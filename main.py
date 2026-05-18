import json
import os

from clock import Clock

if __name__ == "__main__":
    config = {}
    if os.path.exists("config.json"):
        with open("config.json") as f:
            config = json.load(f)

    clock = Clock(
        addr_hour=config.get("addr_hour", 27),
        addr_min=config.get("addr_min", 1),
        enable_demo_mode=config.get("enable_demo_mode", False),
    )
    clock.run()
