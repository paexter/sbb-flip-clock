from clock import Clock

SBB_MODULE_ADDR_HOUR = 27  # 12
SBB_MODULE_ADDR_MIN = 1  # TBD

if __name__ == "__main__":
    clock = Clock(addr_hour=SBB_MODULE_ADDR_HOUR, addr_min=SBB_MODULE_ADDR_MIN)
    clock.run()
