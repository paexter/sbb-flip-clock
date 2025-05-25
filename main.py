# /// script
# requires-python = ">=3.11"
# dependencies = ["pyserial==3.5", "gpiozero==2.0.1", "RPi.GPIO==0.7.1"]
# ///

from sbb_fallblatt import sbb_rs485
import time
from datetime import datetime
import threading
from signal import pause

SBB_MODULE_ADDR_HOUR = 12
SBB_MODULE_ADDR_MIN = 1


def main() -> None:

    threading.Thread(target=clock_task, daemon=True).start()

    pause()


def clock_task() -> None:
    print("Starting clock task!")

    clock = sbb_rs485.PanelClockControl(
        port="/dev/ttyS0", addr_hour=SBB_MODULE_ADDR_HOUR, addr_min=SBB_MODULE_ADDR_MIN
    )
    clock.connect()

    # clock.set_zero()

    minutes = 0
    hours = 0
    try:
        while True:

            minutes += 1
            minutes %= 60

            hours += 1
            hours %= 24

            print(f"Setting clock to {hours:02d} hours and {minutes:02d} minutes")

            clock.set_hour(hours)
            clock.set_minute(minutes)

            time.sleep(3)

            # clock.set_time_now()
            # ts = datetime.utcnow()
            # sleeptime = 60 - (ts.second + ts.microsecond / 1000000.0)
            # time.sleep(sleeptime)
    except KeyboardInterrupt:
        print("Exiting clock task")
    finally:
        pass
        # GPIO.cleanup()


if __name__ == "__main__":
    main()
