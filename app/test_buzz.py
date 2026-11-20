import logging
import time

from detection.buzz_motors import BuzzController
from detection.classes import MoveDirection

WAIT_FOR_BANDS_S = 60   # maximum time to wait for the connections
PAUSE_S = 3             # longer than the 1 s motor pulse, so pulses don't overlap


def main():
    logging.basicConfig(level=logging.INFO)

    buzz = BuzzController()
    buzz.start()

    try:
        # 1. Wait until both bands are connected
        print("Waiting for the bands to connect ...")
        for _ in range(WAIT_FOR_BANDS_S):
            if {"LEFT", "RIGHT"} <= set(buzz._clients):
                break
            time.sleep(1)

        connected = sorted(buzz._clients)
        if not connected:
            print("No band connected, nothing to test.")
            return
        print(f"Connected: {connected}")

        # 2. Send every direction once
        for direction in (MoveDirection.LEFT, MoveDirection.RIGHT, MoveDirection.STOP):
            print(f"\n--> {direction}")
            buzz.notify(direction)
            time.sleep(PAUSE_S)

        print("\nDone.")
    finally:
        buzz.stop()


if __name__ == "__main__":
    main()
