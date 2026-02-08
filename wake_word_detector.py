import queue
import threading
from dataclasses import dataclass

import miniaudio
import numpy as np
from openwakeword.model import Model


class WakeWordDetector:
    @dataclass
    class Config:
        input_device_name: str | None = None
        enable_speex_noise_suppression: bool = (
            False  # Linux only, requires pyaudio with speex support
        )
        audio_gain: float = 1.0
        detection_threshold: float = 0.1

    def __init__(self, config: Config | None = None) -> None:
        self._config = config or WakeWordDetector.Config()
        self._max_gain: float = 10.0

        # Validate configuration
        if self._config.audio_gain < 0:
            raise ValueError("audio_gain must be non-negative")
        if self._config.audio_gain > self._max_gain:
            print(
                f"Warning: audio_gain {self._config.audio_gain} exceeds "
                f"max_gain {self._max_gain}, will be clamped"
            )
        if (
            self._config.detection_threshold <= 0
            or self._config.detection_threshold > 1
        ):
            raise ValueError("detection_threshold must be between 0 and 1")

        self._detection_threshold: float = self._config.detection_threshold

        self._wake_word_model_paths: list[str] = [
            # "resources/models/alexa_v0.1.onnx",
            # "resources/models/custom/hey_clock.onnx",
            "resources/models/custom/tic_toc.onnx",
        ]
        self._melspec_model_path: str = "resources/models/melspectrogram.onnx"
        self._embedding_model_path: str = "resources/models/embedding_model.onnx"

        # self._inference_framework = "tflite"
        self._inference_framework = "onnx"

        self._model_sample_rate: int = 16000  # Fixed by wake word model
        self._sample_format = miniaudio.SampleFormat.SIGNED16
        self._channel_count: int = 1
        self._sample_count_per_chunk: int = 1280

        # Get microphone stream
        self._devices = miniaudio.Devices()
        self._captures = self._devices.get_captures()

        print("Available audio devices:")
        self._print_audio_devices()

        device_id = None
        if self._config.input_device_name:
            device_id = self._find_device_id_by_name(self._config.input_device_name)

        print(f"Recording at {self._model_sample_rate} Hz")

        self._audio_queue: queue.Queue[bytes] = queue.Queue()
        buffersize_msec = int(
            1000 * self._sample_count_per_chunk / self._model_sample_rate
        )
        self._capture_device = miniaudio.CaptureDevice(
            input_format=self._sample_format,
            nchannels=self._channel_count,
            sample_rate=self._model_sample_rate,
            buffersize_msec=buffersize_msec,
            device_id=device_id,
        )

        self._model = Model(
            wakeword_models=self._wake_word_model_paths,
            melspec_model_path=self._melspec_model_path,
            embedding_model_path=self._embedding_model_path,
            inference_framework=self._inference_framework,
            enable_speex_noise_suppression=self._config.enable_speex_noise_suppression,
            # vad_threshold = 0.3,
        )

        self._model_count: int = len(self._model.models.keys())

        self._wake_word_callback: bool = None
        self._stop_event = threading.Event()

    def _print_audio_devices(self) -> None:
        """Print all available input audio devices."""
        for i, device in enumerate(self._captures):
            print(f"- Audio device {i}: {device['name']}")

    def _find_device_id_by_name(self, name: str):
        """Find audio device index by partial name match (case-insensitive)."""
        matches = []
        for i, device in enumerate(self._captures):
            if name.lower() in device["name"].lower():
                matches.append((i, device["name"], device["id"]))

        print(f"Searching for audio device matching '{name}':")

        if len(matches) == 0:
            raise ValueError(f"No audio device found matching '{name}'")
        if len(matches) > 1:
            match_names = "\n  ".join(f"{i}: {n}" for i, n, _ in matches)
            raise ValueError(f"Multiple audio devices match '{name}':\n  {match_names}")

        print(f"Selected audio device {matches[0][0]}: {matches[0][1]}")
        return matches[0][2]

    def register_wake_word_callback(self, callback):
        """Register a callback to be called when a wake word is detected."""
        self._wake_word_callback = callback

    def stop(self) -> None:
        """Stop the wake word detector and clean up resources."""
        print("Stopping wake word detector...")
        self._stop_event.set()
        self._capture_device.close()

    def _apply_audio_gain(self, audio: np.ndarray) -> np.ndarray:
        """
        Apply software gain to audio signal with clipping protection.

        Args:
            audio: Input audio as int16 numpy array

        Returns:
            Gain-adjusted audio as int16 numpy array
        """
        # Clamp gain to safety limit
        gain = min(self._config.audio_gain, self._max_gain)

        if gain == 1.0:
            return audio

        # Convert to float32 for processing to avoid overflow
        audio_float = audio.astype(np.float32)

        # Apply gain
        audio_float *= gain

        # Clip to prevent distortion (always enabled)
        audio_float = np.clip(audio_float, -32768, 32767)

        # Convert back to int16
        return audio_float.astype(np.int16)

    def _audio_callback_generator(self):
        while True:
            data = yield
            if data:
                self._audio_queue.put(data)

    def listen_for_wake_word(self) -> None:
        print("#" * 100)
        print("Listening for wake words...")
        print("#" * 100)

        callback = self._audio_callback_generator()
        next(callback)
        self._capture_device.start(callback)

        while not self._stop_event.is_set():
            # Get audio at native sample rate with timeout
            try:
                raw_data = self._audio_queue.get(timeout=0.5)
            except queue.Empty:
                continue

            audio = np.frombuffer(raw_data, dtype=np.int16)

            # Apply software gain if configured
            if self._config.audio_gain != 1.0:
                audio = self._apply_audio_gain(audio)

            # Feed to model
            _ = self._model.predict(audio)

            wake_word_detected = False
            for m in self._model.prediction_buffer.keys():
                score: float = list(self._model.prediction_buffer[m])[-1]

                if score > self._detection_threshold:
                    wake_word_detected = True
                    formatted_score: str = format(score, ".20f").replace("-", "")
                    formatted_model: str = f"{m}{' ' * (16 - len(m))}"

                    print(f"{formatted_model} | {formatted_score[0:5]}")

            if wake_word_detected:
                print("-" * 100)
                if self._wake_word_callback:
                    self._wake_word_callback()

        print("Wake word detector stopped")
