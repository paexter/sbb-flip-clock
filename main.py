# /// script
# requires-python = ">=3.11"
# dependencies = ["pyserial==3.5"]
# ///

from sbb_fallblatt import sbb_rs485
import time
from datetime import datetime
import RPi.GPIO as GPIO

PIR_SENSOR_PIN = 23  # Pin 16 on the board
GPIO.setmode(GPIO.BCM)  # Use Broadcom (BCM) pin numbering
GPIO.setup(PIR_SENSOR_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

SBB_MODULE_ADDR_HOUR = 12
SBB_MODULE_ADDR_MIN = 1


def main() -> None:
    print("Starting clock!")

    clock = sbb_rs485.PanelClockControl(
        port="/dev/ttyS0", addr_hour=SBB_MODULE_ADDR_HOUR, addr_min=SBB_MODULE_ADDR_MIN
    )
    clock.connect()

    # clock.set_zero()

    minutes = 0
    hours = 0
    try:
        while True:
            # Read the binary signal. Returns 1 if HIGH, 0 if LOW.
            signal = GPIO.input(pin)
            if signal:
                print("Signal is HIGH")
            else:
                print("Signal is LOW")

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
        print("Exiting program")
    finally:
        GPIO.cleanup()


if __name__ == "__main__":
    main()
