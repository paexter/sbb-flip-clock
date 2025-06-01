#!/usr/bin/env python3
# filepath: /Users/pascal/git/sbb-flip-clock/shutdown_demo.py

import os
from gpiozero import Button
from signal import pause

# Adjust the pin number based on your wiring.
button = Button(17)


def shutdown_handler():
    print("Shutdown initiated by button press!")
    # You can allow a specific shutdown command to be executed without a password. For example, add the following line to your sudoers file (using visudo):

    # your_username ALL=(ALL) NOPASSWD: /sbin/shutdown

    # Replace your_username with your actual username. Then you can call shutdown without needing sudo credentials in your script.
    os.system("sudo shutdown -h now")


# Attach the callback to the button press event.
button.when_pressed = shutdown_handler

print("Waiting for button press. Press the button to shutdown the system.")
pause()
