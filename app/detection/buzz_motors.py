import asyncio
import logging
import threading

from bleak import BleakClient, BleakScanner
from detection.classes import MoveDirection

CHAR_UUID = "12345678-1234-1234-1234-1234567890ac"
TARGET_NAMES = {"OBSTACLE-L": "LEFT", "OBSTACLE-R": "RIGHT"}
MOTOR_ON_MS = 1000  # how long the motor stays on per trigger

SCAN_TIMEOUT = 5.0  # seconds to scan for BLE devices
CONNECT_TIMEOUT = 10.0  # seconds to connect to BLE devices
RETRY_DELAY = 2.0  # seconds to wait before retrying a failed connection

DIRECTION_TO_SIDES = {
    MoveDirection.LEFT: ["LEFT"],
    MoveDirection.RIGHT: ["RIGHT"],
    MoveDirection.STOP: ["LEFT", "RIGHT"],
}

class BuzzController:
    """Runs BLE in a background."""

    def __init__(self):
        self._loop = asyncio.new_event_loop()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._clients: dict[str, BleakClient] = {}
        self._pulse_locks: dict[str, asyncio.Lock] = {}
        self._scan_lock: asyncio.Lock | None = None
        self._tasks: list[asyncio.Task] = []

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

    def _run(self):
        asyncio.set_event_loop(self._loop)
        self._scan_lock = asyncio.Lock()
        self._pulse_locks = {side: asyncio.Lock() for side in TARGET_NAMES.values()}
        self._tasks = [
            self._loop.create_task(self._supervise(name, side))
            for name, side in TARGET_NAMES.items()
        ]
        self._loop.run_forever()

    # async def _connect_all(self):
    #     logging.info("Scanning for ESP32 boards...")
    #     devices = await BleakScanner.discover(timeout=6.0)

    #     for d in devices:
    #         if d.name in TARGET_NAMES:
    #             side = TARGET_NAMES[d.name]
    #             client = BleakClient(d.address)
    #             await client.connect()
    #             if client.is_connected:
    #                 self._clients[side] = client
    #                 self._pulse_locks[side] = asyncio.Lock()
    #                 logging.info("[CONNECTED] %s <- %s (%s)", side, d.name, d.address)

    #     missing = set(TARGET_NAMES.values()) - set(self._clients)
    #     if missing:
    #         logging.warning("Could not find/connect: %s", missing)

    async def _supervise(self, name: str, side: str):
        while True:
            disconnected = asyncio.Event()
            client = await self._try_connect(name, side, disconnected)

            if client is None:
                await asyncio.sleep(RETRY_DELAY)
                continue

            self._clients[side] = client
            logging.info("[CONNECTED] %s <- %s", side, name)

            try:
                await disconnected.wait()
            finally:
                self._clients.pop(side, None)
                try:
                    await client.disconnect()
                except Exception:
                    pass

            logging.warning("[LOST] %s disconnected, trying to reconnect...", side)
            await asyncio.sleep(RETRY_DELAY)

    async def _try_connect(self, name: str, side: str, disconnected: asyncio.Event):
        """Returns a connected client or None. Never raises (except cancellation)."""
        client = None
        try:
            # Only one band scans/connects at a time (BlueZ allows one scan)
            async with self._scan_lock:
                logging.debug("[%s] Searching for %s ...", side, name)
                device = await BleakScanner.find_device_by_name(name, timeout=SCAN_TIMEOUT)
                if device is None:
                    logging.debug("[%s] %s not found", side, name)
                    return None

                client = BleakClient(
                    device,
                    disconnected_callback=lambda _c: self._loop.call_soon_threadsafe(disconnected.set),
                    timeout=CONNECT_TIMEOUT,
                )
                await client.connect()

            return client if client.is_connected else None
        except Exception:
            logging.exception("[%s] Connect to %s failed", side, name)
            if client is not None:
                try:
                    await client.disconnect()
                except Exception:
                    pass
            return None

    async def _pulse(self, side: str):

        logging.info("Pulsing %s", side)

        client = self._clients.get(side)
        if client is None or not client.is_connected:
            return
        async with self._pulse_locks[side]:  # no overlapping pulses on one motor
            try:
                await client.write_gatt_char(CHAR_UUID, bytes([1]), response=False)
                logging.info("write 1 OK")
                logging.info("write 1 OK")
                await asyncio.sleep(MOTOR_ON_MS / 1000)
            except Exception:
                logging.exception("BLE write to %s failed: ", side)
                logging.exception("BLE write to %s failed: ", side)
            finally:
                try:
                    await client.write_gatt_char(CHAR_UUID, bytes([0]), response=False)
                except Exception:
                    logging.exception("BLE write to %s failed: ", side)
                    logging.exception("BLE write to %s failed: ", side)

    async def _shutdown(self):
        for task in self._tasks:
                task.cancel()
        await asyncio.gather(*self._tasks, return_exceptions=True)

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
