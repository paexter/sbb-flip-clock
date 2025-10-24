import pyaudio
import numpy as np
import rich.traceback

from openwakeword.model import Model

rich.traceback.install(show_locals=True)


# TODO: Move to separate wake_word_detector.py file
class WakeWordDetector:
    def __init__(self) -> None:
        self._detection_threshold: float = 0.1

        # TODO: Make all variables lowercase
        self._WAKE_WORD_MODEL_PATHS: list[str] = [
            # "resources/models/alexa_v0.1.onnx",
            # "resources/models/custom/hey_clock.onnx",
            "resources/models/custom/tic_toc.onnx",
        ]
        self._MELSPEC_MODEL_PATH: str = "resources/models/melspectrogram.onnx"
        self._EMBEDDING_MODEL_PATH: str = "resources/models/embedding_model.onnx"

        # self._INFERENCE_FRAMEWORK = "tflite"
        self._INFERENCE_FRAMEWORK = "onnx"

        self._SAMPLE_FORMAT: int = pyaudio.paInt16
        self._CHANNEL_COUNT: int = 1
        self._SAMPLE_RATE: int = 16000
        self._SAMPLE_COUNT_PER_CHUNK: int = 1280
        self._INPUT_DEVICE_INDEX: int | None = (
            None  # Set to None to use the default microphone
        )

        self._ENABLE_SPEEX_NOISE_SUPPRESSION: bool = (
            False  # Linux only, requires pyaudio with speex support
        )

        # Get microphone stream
        self._audio = pyaudio.PyAudio()

        for i in range(self._audio.get_device_count()):
            device_info = self._audio.get_device_info_by_index(i)
            print(f"Device {i}: {device_info['name']}")

        self._mic_stream: pyaudio._Stream = self._audio.open(
            format=self._SAMPLE_FORMAT,
            channels=self._CHANNEL_COUNT,
            rate=self._SAMPLE_RATE,
            input=True,
            frames_per_buffer=self._SAMPLE_COUNT_PER_CHUNK,
            input_device_index=self._INPUT_DEVICE_INDEX,
        )

        self._model = Model(
            wakeword_models=self._WAKE_WORD_MODEL_PATHS,
            melspec_model_path=self._MELSPEC_MODEL_PATH,
            embedding_model_path=self._EMBEDDING_MODEL_PATH,
            inference_framework=self._INFERENCE_FRAMEWORK,
            enable_speex_noise_suppression=self._ENABLE_SPEEX_NOISE_SUPPRESSION,
        )

        self._model_count: int = len(self._model.models.keys())

        self._wake_word_callback: bool = None

    def register_wake_word_callback(self, callback):
        """Register a callback to be called when a wake word is detected."""
        self._wake_word_callback = callback

    def listen_for_wake_word(self) -> None:
        print("#" * 100)
        print("Listening for wake words...")
        print("#" * 100)

        while True:
            # Get audio
            audio = np.frombuffer(
                self._mic_stream.read(
                    self._SAMPLE_COUNT_PER_CHUNK, exception_on_overflow=False
                ),
                dtype=np.int16,
            )

            # Feed to model
            prediction = self._model.predict(audio)

            wake_word_detected = False
            for m in self._model.prediction_buffer.keys():
                score: float = list(self._model.prediction_buffer[m])[-1]

                if score > self._detection_threshold:
                    wake_word_detected = True
                    formatted_score: str = format(score, ".20f").replace("-", "")
                    formatted_model: str = f"{m}{' '*(16 - len(m))}"

                    print(f"{formatted_model} | {formatted_score[0:5]}")

            if wake_word_detected:
                print("-" * 100)
                if self._wake_word_callback:
                    self._wake_word_callback()


if __name__ == "__main__":
    wake_word_detector = WakeWordDetector()

    def wake_word_handler() -> None:
        # print("Wake word callback triggered!")
        pass

    wake_word_detector.register_wake_word_callback(wake_word_handler)

    wake_word_detector.listen_for_wake_word()
