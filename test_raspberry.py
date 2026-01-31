import rich.traceback

from wake_word_detector import WakeWordDetector

rich.traceback.install(show_locals=True)


if __name__ == "__main__":
    config = WakeWordDetector.Config()
    config.enable_speex_noise_suppression = False
    config.input_device_name = "USB PnP Sound Device: Audio"

    wake_word_detector = WakeWordDetector(config=config)

    def wake_word_handler() -> None:
        # print("Wake word callback triggered!")
        pass

    wake_word_detector.register_wake_word_callback(wake_word_handler)

    wake_word_detector.listen_for_wake_word()
