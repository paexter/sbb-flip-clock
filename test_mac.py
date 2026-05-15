import contextlib
import rich.traceback

from wake_word_detector import WakeWordDetector

rich.traceback.install(show_locals=True)


if __name__ == "__main__":
    config = WakeWordDetector.Config()
    config.enable_speex_noise_suppression = False
    config.input_device_name = "MacBook Pro Microphone"
    config.audio_gain = 0.01  # This makes no sense, but it works the best by far
    config.detection_threshold = 0.3
    config.debug = True

    wake_word_detector = WakeWordDetector(config=config)

    def wake_word_handler() -> None:
        # print("Wake word callback triggered!")
        pass

    wake_word_detector.register_wake_word_callback(wake_word_handler)

    with contextlib.suppress(KeyboardInterrupt):
        wake_word_detector.listen_for_wake_word()
    # wake_word_detector.listen_for_wake_word_in_file("sample.wav")
