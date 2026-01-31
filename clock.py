import os
import threading
import time
from signal import pause

import rich.traceback
from gpiozero import Button

from sbb_fallblatt import sbb_rs485

# from datetime import datetime

rich.traceback.install(show_locals=True)


class Clock:
    def __init__(self, addr_hour: int, addr_min: int) -> None:
        self._addr_hour = addr_hour
        self._addr_min = addr_min

        self._wake_word_button = Button(6, bounce_time=0.2)
        self._shutdown_button = Button(26, bounce_time=0.2)

        self._wake_word_triggered: bool = False
        self._panel_clock = None

        # Attach the callback to the button press event.
        self._wake_word_button.when_pressed = self._wake_word_button_handler
        self._shutdown_button.when_pressed = self._shutdown_button_handler

    def _wake_word_button_handler(self) -> None:
        print("[Wake Word Button Handler] Wake word mode is turned on!")
        if self._panel_clock is not None:
            self._panel_clock.set_hour(12)
            self._panel_clock.set_minute(34)

    def _shutdown_button_handler(self) -> None:
        for i in range(10, 0, -1):
            print(f"[Shutdown Button Handler] Shutting down in {i} seconds...")
            if self._panel_clock is not None:
                self._panel_clock.set_hour(0)
                self._panel_clock.set_minute(60 - i)

            time.sleep(1)

            if not self._shutdown_button.is_pressed:
                print("[Shutdown Button Handler] Button released, shutdown cancelled.")
                return

        print("[Shutdown Button Handler] Button still pressed, shutting down!")
        if self._panel_clock is not None:
            self._panel_clock.set_hour(0)
            self._panel_clock.set_minute(0)

        # You can allow a specific shutdown command to be executed without a password.
        # For example, add the following line to your sudoers file (using visudo):

        # your_username ALL=(ALL) NOPASSWD: /sbin/shutdown

        # Replace your_username with your actual username. Then you can call shutdown
        # without needing sudo credentials in your script.
        os.system("sudo shutdown -h now")

    def _wake_word_task(self) -> None:
        print("[Wake Word Task] Starting!")

        # TODO: Implement
        # def wake_word_handler() -> None:
        #     print("Wake word callback triggered!")
        #     wake_word_triggered = True

        # wake_word_detector = WakeWordDetector()
        # wake_word_detector.register_wake_word_callback(wake_word_handler)
        # wake_word_detector.listen_for_wake_word()

        pause()

    def _clock_task(self) -> None:
        print("[Clock Task] Starting!")

        self._panel_clock = sbb_rs485.PanelClockControl(
            port="/dev/ttyS0", addr_hour=self._addr_hour, addr_min=self._addr_min
        )
        self._panel_clock.connect()

        # clock.set_zero()

        minutes = 0
        hours = 0
        try:
            while True:
                if self._shutdown_button.is_pressed:
                    time.sleep(1)
                    continue

                if self._wake_word_button.is_pressed and not self._wake_word_triggered:
                    time.sleep(1)
                    continue

                minutes += 1
                minutes %= 60

                hours += 1
                hours %= 24

                print(f"[Clock Task] Setting time to {hours:02d}:{minutes:02d}.")

                self._panel_clock.set_hour(hours)
                self._panel_clock.set_minute(minutes)

                time.sleep(3)

                # clock.set_time_now()
                # ts = datetime.utcnow()
                # sleeptime = 60 - (ts.second + ts.microsecond / 1000000.0)
                # time.sleep(sleeptime)

                self._wake_word_triggered = False
        except KeyboardInterrupt:
            print("[Clock Task] Exiting!")

    def run(self) -> None:
        threading.Thread(target=self._clock_task, daemon=True).start()
        threading.Thread(target=self._wake_word_task, daemon=True).start()

        pause()
