# sbb-flip-clock

## Setup for all

* Install uv: `curl -LsSf https://astral.sh/uv/install.sh | sh`
* Install Python: `uv python install 3.11`
* Run the application: `uv run main.py`

## Setup on Raspberry Pi Zero W

* Install and update Raspberry PI OS
* Install portaudio: `sudo apt-get install portaudio19-dev`
* Install pyaudio:`sudo apt-get install python3-pyaudio`
* Install Waveshare RS485 CAN HAT: www.waveshare.com/wiki/RS485_CAN_HAT
  * `ls -l /dev/serial*` -> No serial device should be listed
  * `sudo raspi-config`
  * Select `Interface Options` -> `Serial`, disable shell access, and enable the hardware serial port, restart
  * `ls -l /dev/serial*` -> A serial device `/dev/ttyS0` should be listed

## Setup on Mac

* Install portaudio with `brew install portaudio`

## Setup autostart
<!-- crontab -e -->
<!-- @reboot uv run /<path-to-script>/sbb-flip-clock/main.py -->

## Dependencies

* https://github.com/adfinis/sbb-fallblatt/tree/master at commit `3097e95061556edef110f86d049867bbf3a20e06`
* Waveshare RS485 CAN HAT: www.waveshare.com/wiki/RS485_CAN_HAT
* Pretrained wake word models: https://github.com/fwartner/home-assistant-wakewords-collection/tree/main/en

## Other related projects

* https://github.com/kahrendt/microWakeWord?tab=readme-ov-file
* https://github.com/esphome/micro-wake-word-models/tree/main/models
