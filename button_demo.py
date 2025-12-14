#!/usr/bin/env python3
# filepath: /Users/pascal/git/sbb-flip-clock/button_demo.py

from gpiozero import Button
from signal import pause

# Adjust the pin number based on your wiring.
button_1 = Button(6, pull_up=True)
button_2 = Button(26, pull_up=True)


def on_button_1_pressed() -> None:
    print("Button 1 pressed!")


def on_button_2_pressed() -> None:
    print("Button 2 pressed!")


# Attach the callback to the button press event.
button_1.when_pressed = on_button_1_pressed
button_2.when_pressed = on_button_2_pressed

print("Waiting for button presses. Press Ctrl+C to exit.")
pause()
