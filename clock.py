import os
import threading
import time
from datetime import datetime, timedelta
from signal import pause

import rich.traceback
from gpiozero import Button

from sbb_fallblatt import sbb_rs485
from wake_word_detector import WakeWordDetector

rich.traceback.install(show_locals=True)


class Clock:
    def __init__(
        self, addr_hour: int, addr_min: int, enable_demo_mode: bool = False
    ) -> None:
        self._addr_hour: int = addr_hour
        self._addr_min: int = addr_min
        self._enable_demo_mode: bool = enable_demo_mode

        self._wake_word_button = Button(6, bounce_time=0.2)
        self._shutdown_button = Button(26, bounce_time=0.2)

        self._shutdown_timeout: int = 10  # Seconds
        self._wake_word_timeout: int = 5  # Minutes

        self._wake_word_trigger_time: datetime | None = None
        self._panel_clock = sbb_rs485.PanelClockControl(
            port="/dev/ttyS0", addr_hour=self._addr_hour, addr_min=self._addr_min
        )
        self._panel_clock.connect()

        if self._wake_word_button.is_pressed:
            self._panel_clock.set_hour(12)
            self._panel_clock.set_minute(34)
        elif self._shutdown_button.is_pressed:
            self._panel_clock.set_hour(0)
            self._panel_clock.set_minute(60 - self._shutdown_timeout)
        else:
            self._panel_clock.set_hour(0)
            self._panel_clock.set_minute(0)

        # Attach the callbacks to the button press events
        self._wake_word_button.when_pressed = self._wake_word_button_pressed_handler
        self._shutdown_button.when_pressed = self._shutdown_button_pressed_handler

        self._wake_word_button.when_released = self._wake_word_button_released_handler
        self._shutdown_button.when_released = self._shutdown_button_released_handler

        self._demo_minutes: int = 0
        self._demo_hours: int = 0

    def _wake_word_button_pressed_handler(self) -> None:
        print("[Wake Word Button Pressed Handler] Wake word mode is turned on!")
        self._panel_clock.set_hour(12)
        self._panel_clock.set_minute(34)

    def _wake_word_button_released_handler(self) -> None:
        print("[Wake Word Button Released Handler] Resetting demo clock!")
        self._demo_minutes = 0
        self._demo_hours = 0

    def _shutdown_button_pressed_handler(self) -> None:
        self._panel_clock.set_hour(0)
        self._panel_clock.set_minute(60 - self._shutdown_timeout)

        time.sleep(3)

        for i in range(self._shutdown_timeout, 0, -1):
            print(f"[Shutdown Button Pressed Handler] Shutting down in {i} seconds...")
            self._panel_clock.set_minute(60 - i)

            time.sleep(1)

            if not self._shutdown_button.is_pressed:
                print(
                    "[Shutdown Button Pressed Handler] "
                    "Button released, shutdown cancelled."
                )
                return

        print("[Shutdown Button Pressed Handler] Button still pressed, shutting down!")
        self._panel_clock.set_zero()

        # You can allow a specific shutdown command to be executed without a password.
        # For example, add the following line to your sudoers file (using visudo):

        # your_username ALL=(ALL) NOPASSWD: /sbin/shutdown

        # Replace your_username with your actual username. Then you can call shutdown
        # without needing sudo credentials in your script.
        os.system("sudo shutdown -h now")

    def _shutdown_button_released_handler(self) -> None:
        print("[Shutdown Button Released Handler] Resetting demo clock!")
        self._demo_minutes = 0
        self._demo_hours = 0

    def _wake_word_task(self) -> None:
        print("[Wake Word Task] Starting!")

        def wake_word_handler() -> None:
            if not self._wake_word_button.is_pressed:
                print("[Wake Word Handler] Wake word mode is not active!")
                return

            if self._wake_word_trigger_time is not None:
                print("[Wake Word Handler] Wake word has already been triggered!")
                return

            print("[Wake Word Handler] Wake word callback triggered!")
            self._wake_word_trigger_time = datetime.now()

        config = WakeWordDetector.Config()
        config.enable_speex_noise_suppression = True
        config.input_device_name = "PCM2902 Audio Codec Analog Mono"

        wake_word_detector = WakeWordDetector(config=config)
        wake_word_detector.register_wake_word_callback(wake_word_handler)
        wake_word_detector.listen_for_wake_word()

        pause()

    def _clock_task(self) -> None:
        print("[Clock Task] Starting!")

        try:
            while True:
                if self._shutdown_button.is_pressed:
                    time.sleep(1)
                    continue

                if self._wake_word_button.is_pressed:
                    if self._wake_word_trigger_time is None:
                        time.sleep(1)
                        continue
                    else:
                        elapsed: timedelta = (
                            datetime.now() - self._wake_word_trigger_time
                        )
                        if elapsed.total_seconds() > 60 * self._wake_word_timeout:
                            self._wake_word_trigger_time = None
                            self._panel_clock.set_hour(12)
                            self._panel_clock.set_minute(34)
                            continue
                else:
                    self._wake_word_trigger_time = None

                if self._enable_demo_mode:
                    self._demo_minutes += 1
                    self._demo_minutes %= 60
                    self._demo_hours += 1
                    self._demo_hours %= 24
                    print(
                        f"[Clock Task] Setting time to {self._demo_hours:02d}:"
                        f"{self._demo_minutes:02d}"
                    )
                    self._panel_clock.set_hour(self._demo_hours)
                    self._panel_clock.set_minute(self._demo_minutes)
                    time.sleep(3)
                else:
                    self._panel_clock.set_time_now()
                    ts: datetime = datetime.now()
                    sleeptime: float = 60 - (ts.second + ts.microsecond / 1000000.0)
                    time.sleep(sleeptime)

        except KeyboardInterrupt:
            print("[Clock Task] Exiting!")

    def run(self) -> None:
        threading.Thread(target=self._clock_task, daemon=True).start()
        threading.Thread(target=self._wake_word_task, daemon=True).start()

        pause()
