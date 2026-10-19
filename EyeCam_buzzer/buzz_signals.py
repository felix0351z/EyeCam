import asyncio
from bleak import BleakClient, BleakScanner

CHAR_UUID = "12345678-1234-1234-1234-1234567890ac"
TARGET_NAMES = {"OBSTACLE-L": "LEFT", "OBSTACLE-R": "RIGHT"}
MOTOR_ON_MS = 1000  # how long the motor stays on per trigger

async def find_and_connect():
    print("Scanning for ESP32 boards...")
    devices = await BleakScanner.discover(timeout=6.0)
    clients = {}

    for d in devices:
        if d.name in TARGET_NAMES:
            side = TARGET_NAMES[d.name]
            client = BleakClient(d.address)
            await client.connect()
            if client.is_connected:
                clients[side] = client
                print(f"[CONNECTED] {side} <- {d.name} ({d.address})")

    missing = set(TARGET_NAMES.values()) - set(clients.keys())
    if missing:
        print(f"[WARNING] Could not find/connect: {missing}. Check power/advertising.")

    return clients

async def pulse_motor(client, side):
    print(f"[SIGNAL] -> {side}: motor ON")
    await client.write_gatt_char(CHAR_UUID, bytes([1]), response=False)
    await asyncio.sleep(MOTOR_ON_MS / 1000)
    await client.write_gatt_char(CHAR_UUID, bytes([0]), response=False)
    print(f"[SIGNAL] -> {side}: motor OFF")

async def main():
    clients = await find_and_connect()

    if not clients:
        print("No boards connected. Exiting.")
        return

    print("\nReady. Press 'l' + Enter for LEFT, 'r' + Enter for RIGHT, 'q' + Enter to quit.\n")

    loop = asyncio.get_event_loop()
    while True:
        cmd = await loop.run_in_executor(None, input, "> ")
        cmd = cmd.strip().lower()

        if cmd == "q":
            break
        elif cmd == "l" and "LEFT" in clients:
            await pulse_motor(clients["LEFT"], "LEFT")
        elif cmd == "r" and "RIGHT" in clients:
            await pulse_motor(clients["RIGHT"], "RIGHT")
        else:
            print(f"[IGNORED] Unknown or unconnected command: '{cmd}'")

    for side, client in clients.items():
        await client.disconnect()
        print(f"[DISCONNECTED] {side}")

asyncio.run(main())