import pyaudio
import numpy as np
import rich.traceback

from openwakeword.model import Model

rich.traceback.install(show_locals=True)


class WakeWordDetector:
    def __init__(self) -> None:
        self._detection_threshold = 0.1

        self._WAKE_WORD_MODEL_PATHS: list[str] = [
            # "resources/models/alexa_v0.1.onnx",
            # "resources/models/custom/hey_clock.onnx",
            "resources/models/custom/tic_toc.onnx",
        ]
        self._MELSPEC_MODEL_PATH: str = "resources/models/melspectrogram.onnx"
        self._EMBEDDING_MODEL_PATH = "resources/models/embedding_model.onnx"

        # self._INFERENCE_FRAMEWORK = "tflite"
        self._INFERENCE_FRAMEWORK = "onnx"

        self._SAMPLE_FORMAT = pyaudio.paInt16
        self._CHANNEL_COUNT = 1
        self._SAMPLE_RATE = 16000
        self._SAMPLE_COUNT_PER_CHUNK = (
            1280  # How much audio (in number of samples) to predict on at once
        )
        self._INPUT_DEVICE_INDEX = None  # Set to None to use the default microphone

        self._ENABLE_SPEEX_NOISE_SUPPRESSION = (
            False  # Linux only, requires pyaudio with speex support
        )

        # Get microphone stream
        self._audio = pyaudio.PyAudio()

        for i in range(self._audio.get_device_count()):
            device_info = self._audio.get_device_info_by_index(i)
            print(f"Device {i}: {device_info['name']}")

        self._mic_stream = self._audio.open(
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

        self._wake_word_callback = None

    def register_wake_word_callback(self, callback):
        """Register a callback to be called when a wake word is detected."""
        self._wake_word_callback = callback

    def listen_for_wake_word(self) -> None:
        # Generate output string header
        print("\n\n")
        print("#" * 100)
        print("Listening for wake words...")
        print("#" * 100)
        print("\n" * (self._model_count * 3))

        while True:
            # Get audio
            audio = np.frombuffer(
                self._mic_stream.read(
                    self._SAMPLE_COUNT_PER_CHUNK, exception_on_overflow=False
                ),
                dtype=np.int16,
            )

            # Feed to openWakeWord model
            prediction = self._model.predict(audio)

            # Column titles
            spaces_count = 16
            output_string_header = """
                Model Name         | Score | Wake Word Status
                ---------------------------------------------
                """

            wake_word_detected = False
            for m in self._model.prediction_buffer.keys():
                # Add scores in formatted table
                scores: list = list(self._model.prediction_buffer[m])
                current_score: str = format(scores[-1], ".20f").replace("-", "")

                detected = scores[-1] > self._detection_threshold
                if detected:
                    wake_word_detected = True

                output_string_header += f"""{m}{" "*(spaces_count - len(m))}   | {current_score[0:5]} | {"--"+" "*20 if not detected else "Wake Word Detected!"}
                """

            if wake_word_detected and self._wake_word_callback:
                self._wake_word_callback()

            # Print results table
            print("\033[F" * (4 * self._model_count + 1))
            print(output_string_header, "                             ", end="\r")


if __name__ == "__main__":
    wake_word_detector = WakeWordDetector()

    def wake_word_handler() -> None:
        # print("Wake word callback triggered!")
        pass

    wake_word_detector.register_wake_word_callback(wake_word_handler)

    wake_word_detector.listen_for_wake_word()
