#!/usr/bin/env python3
# filepath: /Users/pascal/git/sbb-flip-clock/button_demo.py

from gpiozero import Button
from signal import pause

# Adjust the pin number based on your wiring.
button = Button(17)


def on_button_pressed() -> None:
    print("Button pressed!")


# Attach the callback to the button press event.
button.when_pressed = on_button_pressed

print("Waiting for button presses. Press Ctrl+C to exit.")
pause()
