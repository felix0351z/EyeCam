import asyncio
import logging
import threading

from bleak import BleakClient, BleakScanner
from bleak.backends.device import BLEDevice
from bleak.backends.scanner import AdvertisementData
from detection.classes import MoveDirection

CHAR_UUID = "12345678-1234-1234-1234-1234567890ac"
TARGET_NAMES = {"OBSTACLE-L": "LEFT", "OBSTACLE-R": "RIGHT"}
MOTOR_ON_MS = 1000  # how long the motor stays on per trigger

SCAN_TIMEOUT = 5.0  # max. seconds per scan (stops earlier once all missing bands are found)
CONNECT_TIMEOUT = 10.0  # seconds to connect to BLE devices
RECONNECT_DELAY = 2.0  # seconds to wait after a disconnect before scanning again
# Pauses between scans while a band is still missing. WLAN and Bluetooth share one
# radio on the Pi, so scanning permanently disturbs the WLAN. The pause grows with
# every unsuccessful scan and is reset once a band connects or disconnects.
SCAN_BACKOFF_S = (5.0, 10.0, 30.0)

DIRECTION_TO_SIDES = {
    MoveDirection.LEFT: ["LEFT"],
    MoveDirection.RIGHT: ["RIGHT"],
    MoveDirection.STOP: ["LEFT", "RIGHT"],
}

class BuzzController:
    """Runs BLE in a background thread."""

    def __init__(self):
        self._loop = asyncio.new_event_loop()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._clients: dict[str, BleakClient] = {}
        self._pulse_locks: dict[str, asyncio.Lock] = {}
        self._wake: asyncio.Event | None = None  # set when a band disconnects
        self._tasks: set[asyncio.Task] = set()

    # ---------------------------------
    # public API
    # ---------------------------------

    def start(self):
        """Start the BLE background thread."""
        self._thread.start()

    def notify(self, direction: MoveDirection):
        """Detection subscriber"""

        logging.info("direction: %s", direction)
        logging.info("clients: %s", self._clients)

        for side in DIRECTION_TO_SIDES.get(direction, []):
            client = self._clients.get(side)
            if client is not None and client.is_connected:
                asyncio.run_coroutine_threadsafe(self._pulse(side), self._loop)


    def stop(self):
        if not self._thread.is_alive():
            return
        try:
            asyncio.run_coroutine_threadsafe(self._shutdown(), self._loop).result(timeout=10)
        except Exception as e:
            logging.exception("BLE shutdown failed: %s", e)
        self._loop.call_soon_threadsafe(self._loop.stop)

    # ---------------------------------
    # background loop
    # ---------------------------------

    def _run(self):
        asyncio.set_event_loop(self._loop)
        self._wake = asyncio.Event()
        self._pulse_locks = {side: asyncio.Lock() for side in TARGET_NAMES.values()}
        self._spawn(self._manage())
        self._loop.run_forever()

    def _spawn(self, coro) -> asyncio.Task:
        task = self._loop.create_task(coro)
        self._tasks.add(task)
        task.add_done_callback(self._tasks.discard)
        return task

    def _missing_names(self) -> set[str]:
        return {name for name, side in TARGET_NAMES.items() if side not in self._clients}

    async def _manage(self):
        """Single loop that scans for all missing bands at once and connects them."""
        backoff_step = 0
        while True:
            missing = self._missing_names()

            if not missing:
                # Both bands connected: no scanning at all until one disconnects
                await self._wake.wait()
            else:
                found = await self._scan(missing)
                # The scan is stopped here, so connecting never overlaps with scanning
                for name, device in found.items():
                    await self._connect(name, device)

                still_missing = self._missing_names()
                if not still_missing:
                    backoff_step = 0
                    continue
                if len(still_missing) < len(missing):
                    backoff_step = 0  # progress was made

                delay = SCAN_BACKOFF_S[min(backoff_step, len(SCAN_BACKOFF_S) - 1)]
                backoff_step += 1
                logging.info("Bands missing: %s, next scan in %.0f s",
                             sorted(TARGET_NAMES[n] for n in still_missing), delay)
                try:
                    await asyncio.wait_for(self._wake.wait(), delay)
                except asyncio.TimeoutError:
                    continue

            # A band disconnected: it is probably still nearby, reconnect quickly
            self._wake.clear()
            backoff_step = 0
            await asyncio.sleep(RECONNECT_DELAY)

    async def _scan(self, names: set[str]) -> dict[str, BLEDevice]:
        """One scan for all given names, stops as soon as all of them are found."""
        found: dict[str, BLEDevice] = {}
        all_found = asyncio.Event()

        def on_detect(device: BLEDevice, adv: AdvertisementData):
            name = adv.local_name or device.name
            if name in names and name not in found:
                found[name] = device
                logging.debug("Found %s (%s)", name, device.address)
                if len(found) == len(names):
                    all_found.set()

        logging.debug("Scanning for %s ...", sorted(names))
        try:
            async with BleakScanner(detection_callback=on_detect):
                try:
                    await asyncio.wait_for(all_found.wait(), SCAN_TIMEOUT)
                except asyncio.TimeoutError:
                    pass
        except Exception:
            logging.exception("BLE scan failed")
        return found

    async def _connect(self, name: str, device: BLEDevice):
        """Connects a found band and starts watching it. Never raises (except cancellation)."""
        side = TARGET_NAMES[name]
        disconnected = asyncio.Event()
        client = BleakClient(
            device,
            disconnected_callback=lambda _c: self._loop.call_soon_threadsafe(disconnected.set),
            timeout=CONNECT_TIMEOUT,
        )
        try:
            await client.connect()
        except Exception:
            logging.exception("[%s] Connect to %s failed", side, name)
            try:
                await client.disconnect()
            except Exception:
                pass
            return

        if not client.is_connected:
            return

        self._clients[side] = client
        logging.info("[CONNECTED] %s <- %s (%s)", side, name, device.address)
        self._spawn(self._watch(side, client, disconnected))

    async def _watch(self, side: str, client: BleakClient, disconnected: asyncio.Event):
        try:
            await disconnected.wait()
        finally:
            self._clients.pop(side, None)
            try:
                await client.disconnect()
            except Exception:
                pass

        logging.warning("[LOST] %s disconnected, trying to reconnect...", side)
        self._wake.set()

    async def _pulse(self, side: str):

        logging.info("Pulsing %s", side)

        client = self._clients.get(side)
        if client is None or not client.is_connected:
            return
        async with self._pulse_locks[side]:  # no overlapping pulses on one motor
            try:
                await client.write_gatt_char(CHAR_UUID, bytes([1]), response=False)
                logging.info("write 1 OK")
                await asyncio.sleep(MOTOR_ON_MS / 1000)
            except Exception:
                logging.exception("BLE write to %s failed: ", side)
            finally:
                try:
                    await client.write_gatt_char(CHAR_UUID, bytes([0]), response=False)
                except Exception:
                    logging.exception("BLE write to %s failed: ", side)

    async def _shutdown(self):
        tasks = list(self._tasks)  # copy: finished tasks remove themselves from the set
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)

# Old keyboard test for testing reasons:
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    buzz = BuzzController()
    buzz.start()
    try:
        while (cmd := input("> ").strip().lower()) != "q":
            if cmd == "l":
                buzz.notify(MoveDirection.LEFT)
            elif cmd == "r":
                buzz.notify(MoveDirection.RIGHT)
            elif cmd == "s":
                buzz.notify(MoveDirection.STOP)
    finally:
        buzz.stop()
