import os
import threading
import time
from signal import pause

import rich.traceback
from gpiozero import Button

from sbb_fallblatt import sbb_rs485

# from datetime import datetime

rich.traceback.install(show_locals=True)

SBB_MODULE_ADDR_HOUR = 27  # 12
SBB_MODULE_ADDR_MIN = 1  # TBD

wake_word_button = Button(6, bounce_time=0.2)
shutdown_button = Button(26, bounce_time=0.2)

wake_word_triggered: bool = False
clock = None


def wake_word_button_handler() -> None:
    print("[Wake Word Button Handler] Wake word mode is turned on!")


def shutdown_button_handler() -> None:
    global clock
    print("[Shutdown Button Handler] Shutdown initiated by shutdown button press!")

    if clock is not None:
        clock.set_hour(0)
        clock.set_minute(30)

    for i in range(5, 0, -1):
        print(f"[Shutdown Button Handler] Shutting down in {i} seconds...")
        time.sleep(1)

    if shutdown_button.is_pressed:
        print("[Shutdown Button Handler] Button still pressed, shutting down!")
        if clock is not None:
            clock.set_hour(0)
            clock.set_minute(0)
        # You can allow a specific shutdown command to be executed without a password.
        # For example, add the following line to your sudoers file (using visudo):

        # your_username ALL=(ALL) NOPASSWD: /sbin/shutdown

        # Replace your_username with your actual username. Then you can call shutdown
        # without needing sudo credentials in your script.
        os.system("sudo shutdown -h now")
    else:
        print("[Shutdown Button Handler] Button released, shutdown cancelled.")


# Attach the callback to the button press event.
wake_word_button.when_pressed = wake_word_button_handler
shutdown_button.when_pressed = shutdown_button_handler


def main() -> None:
    threading.Thread(target=clock_task, daemon=True).start()
    threading.Thread(target=wake_word_task, daemon=True).start()

    pause()


def wake_word_task() -> None:
    print("[Wake Word Task] Starting!")

    # TODO: Implement
    # def wake_word_handler() -> None:
    #     print("Wake word callback triggered!")
    #     wake_word_triggered = True

    # wake_word_detector = WakeWordDetector()
    # wake_word_detector.register_wake_word_callback(wake_word_handler)
    # wake_word_detector.listen_for_wake_word()

    pause()


def clock_task() -> None:
    global wake_word_triggered, clock
    print("[Clock Task] Starting!")

    clock = sbb_rs485.PanelClockControl(
        port="/dev/ttyS0", addr_hour=SBB_MODULE_ADDR_HOUR, addr_min=SBB_MODULE_ADDR_MIN
    )
    clock.connect()

    # clock.set_zero()

    minutes = 0
    hours = 0
    try:
        while True:
            if shutdown_button.is_pressed:
                time.sleep(1)
                continue

            if wake_word_button.is_pressed and not wake_word_triggered:
                time.sleep(1)
                continue

            minutes += 1
            minutes %= 60

            hours += 1
            hours %= 24

            print(f"[Clock Task] Setting time to {hours:02d}:{minutes:02d}.")

            clock.set_hour(hours)
            clock.set_minute(minutes)

            time.sleep(3)

            # clock.set_time_now()
            # ts = datetime.utcnow()
            # sleeptime = 60 - (ts.second + ts.microsecond / 1000000.0)
            # time.sleep(sleeptime)

            wake_word_triggered = False
    except KeyboardInterrupt:
        print("[Clock Task] Exiting!")


if __name__ == "__main__":
    main()
