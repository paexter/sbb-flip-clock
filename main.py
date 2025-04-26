# /// script
# requires-python = ">=3.11"
# dependencies = ["pyserial==3.5"]
# ///

from sbb_fallblatt import sbb_rs485
import time
from datetime import datetime

SBB_MODULE_ADDR_HOUR = 82
SBB_MODULE_ADDR_MIN = 1


def main() -> None:
    print("Starting clock!")

    clock = sbb_rs485.PanelClockControl(
        port="/dev/ttyS0", addr_hour=SBB_MODULE_ADDR_HOUR, addr_min=SBB_MODULE_ADDR_MIN
    )
    clock.connect()

    while True:
        clock.set_time_now()
        ts = datetime.utcnow()
        sleeptime = 60 - (ts.second + ts.microsecond / 1000000.0)
        time.sleep(sleeptime)


if __name__ == "__main__":
    main()
