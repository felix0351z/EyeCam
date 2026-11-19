import asyncio
import logging
import threading

from bleak import BleakClient, BleakScanner
from detection.classes import MoveDirection

CHAR_UUID = "12345678-1234-1234-1234-1234567890ac"
TARGET_NAMES = {"OBSTACLE-L": "LEFT", "OBSTACLE-R": "RIGHT"}
MOTOR_ON_MS = 1000  # how long the motor stays on per trigger

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
        self._ready = threading.Event()
        self._clients: dict[str, BleakClient] = {}
        self._locks: dict[str, asyncio.Lock] = {}

    # ---------------------------------
    # public API
    # ---------------------------------

    def start(self, timeout: float = 30.0):
        self._thread.start()
        self._ready.wait(timeout)

    def notify(self, direction: MoveDirection):
        """Detection subscriber"""
        for side in DIRECTION_TO_SIDES.get(direction, []):
            if side in self._clients:
                asyncio.run_coroutine_threadsafe(self._pulse(side), self._loop)

    def stop(self):
        if not self._thread.is_alive():
            return
        try:
            asyncio.run_coroutine_threadsafe(self._disconnect_all(), self._loop).result(timeout=5)
        except Exception as e:
            logging.warning("BLE disconnect failed: %s", e)
        self._loop.call_soon_threadsafe(self._loop.stop)

    def _run(self):
        asyncio.set_event_loop(self._loop)
        try:
            self._loop.run_until_complete(self._connect_all())
        except Exception as e:
            #logging.error("BLE setup failed: %s", e)
            logging.exception("BLE setup failed")
        finally:
            self._ready.set()
        self._loop.run_forever()

    async def _connect_all(self):
        logging.info("Scanning for ESP32 boards...")
        devices = await BleakScanner.discover(timeout=6.0)

        for d in devices:
            if d.name in TARGET_NAMES:
                side = TARGET_NAMES[d.name]
                client = BleakClient(d.address)
                await client.connect()
                if client.is_connected:
                    self._clients[side] = client
                    self._locks[side] = asyncio.Lock()
                    logging.info("[CONNECTED] %s <- %s (%s)", side, d.name, d.address)

        missing = set(TARGET_NAMES.values()) - set(self._clients)
        if missing:
            logging.warning("Could not find/connect: %s", missing)

    async def _pulse(self, side: str):
        client = self._clients[side]
        async with self._locks[side]:  # no overlapping pulses on one motor
            try:
                await client.write_gatt_char(CHAR_UUID, bytes([1]), response=False)
                await asyncio.sleep(MOTOR_ON_MS / 1000)
            except Exception as e:
                logging.error("BLE write to %s failed: %s", side, e)
            finally:
                try:
                    await client.write_gatt_char(CHAR_UUID, bytes([0]), response=False)
                except Exception:
                    pass

    async def _disconnect_all(self):
        for side, client in self._clients.items():
            await client.disconnect()
            logging.info("[DISCONNECTED] %s", side)

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