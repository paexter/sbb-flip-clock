from clock import Clock

if __name__ == "__main__":
    clock = Clock(addr_hour=27, addr_min=1, enable_demo_mode=False)
    clock.run()
