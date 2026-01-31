import rich.traceback

from wake_word_detector import WakeWordDetector

rich.traceback.install(show_locals=True)


if __name__ == "__main__":
    wake_word_detector = WakeWordDetector()

    def wake_word_handler() -> None:
        # print("Wake word callback triggered!")
        pass

    wake_word_detector.register_wake_word_callback(wake_word_handler)

    wake_word_detector.listen_for_wake_word()
