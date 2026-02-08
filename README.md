# sbb-flip-clock

## Setup on Raspberry Pi Zero W

* Install and update Raspberry PI OS (64-bit)
  * Use user `sbb`
  * Use `raspberrypi-clock.local`
* Install portaudio: `sudo apt-get install portaudio19-dev`
* Install pyaudio:`sudo apt-get install python3-pyaudio`
* Install Waveshare RS485 CAN HAT: www.waveshare.com/wiki/RS485_CAN_HAT
  * `ls -l /dev/serial*` -> No serial device should be listed
  * `sudo raspi-config`
  * Select `Interface Options` -> `Serial Port`, disable shell access, and enable the hardware serial port, restart
  * `ls -l /dev/serial*` -> A serial device `/dev/ttyS0` should be listed
* Change directory: `cd /home/sbb/Desktop`
* Clone: `git clone https://github.com/paexter/sbb-flip-clock.git`
* Install uv: `curl -LsSf https://astral.sh/uv/install.sh | sh`
* Check that `python --version` returns `3.11.2`.
* Create venv including system packages: `uv venv -p /usr/bin/python --system-site-packages`. The system version of `lgpio` is required for the buttons to work.
* Activate environment: `source .venv/bin/activate` or `source .venv/bin/activate.fish`
* Install dependencies: `uv sync`
* Verify that `lgpio` package is present even though not explicitly installed with `uv sync`: `uv run python -m pip list | grep lgpio`
* To enable clock shutdown use `visudo` a set `<your_username> ALL=(ALL) NOPASSWD: /sbin/shutdown`. Replace `<your_username>` with your actual username.
* Run script with system Python without activating the environment `uv run python main.py`  or `uv run python test_raspberry.py`

### Run the application at startup

* Create a new systemd service: `sudo cp sbb-flip-clock.service /etc/systemd/system/sbb-flip-clock.service`
* `sudo systemctl daemon-reload`
* `sudo systemctl enable sbb-flip-clock`
* `sudo systemctl start sbb-flip-clock`
* `sudo systemctl restart sbb-flip-clock`
* `sudo systemctl status sbb-flip-clock`
* `journalctl -u sbb-flip-clock`

## Setup on Mac

* Install portaudio with `brew install portaudio`
* Install uv: `curl -LsSf https://astral.sh/uv/install.sh | sh`
* Install Python: `uv python install 3.11`
* Clone: `git clone https://github.com/paexter/sbb-flip-clock.git`
* `uv sync`
* `uv run demo.py` or `uv run main.py`
* Run the linter: `clear && uvx ruff check --fix`

# Dependencies
* https://github.com/dscripka/openWakeWord/tree/main
* https://github.com/adfinis/sbb-fallblatt/tree/master at commit `3097e95061556edef110f86d049867bbf3a20e06`
* Waveshare RS485 CAN HAT: www.waveshare.com/wiki/RS485_CAN_HAT
* Pretrained wake word models: https://github.com/fwartner/home-assistant-wakewords-collection/tree/main/en

## Other related projects

* https://github.com/kahrendt/microWakeWord?tab=readme-ov-file
* https://github.com/esphome/micro-wake-word-models/tree/main/models
