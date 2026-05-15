import queue
import threading
import time
from dataclasses import dataclass

import miniaudio
import numpy as np
from livekit.wakeword import WakeWordModel


class WakeWordDetector:
    @dataclass
    class Config:
        input_device_name: str | None = None
        audio_gain: float = 1.0
        detection_threshold: float = 0.3
        debounce: float = 2.0
        # With a smaller stride the CPU on the Raspberry Pi is too slow
        inference_stride: int = 8
        debug: bool = False

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
        if self._config.inference_stride < 1:
            raise ValueError("inference_stride must be >= 1")

        self._detection_threshold: float = self._config.detection_threshold

        self._wake_word_model_paths: list[str] = [
            # "resources/models/alexa_v0.1.onnx",
            # "resources/models/custom/hey_clock.onnx",
            # "resources/models/custom/tic_toc.onnx",
            # "resources/models/custom/tick_tock_v3.onnx",
            # "resources/models/custom/hey_livekit.onnx",
            # "resources/models/custom/hey_clock_v1.onnx",
            "resources/models/custom/hey_clock_small_v1.onnx",
        ]

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

        self._model = WakeWordModel(models=self._wake_word_model_paths)

        self._model_count: int = len(self._wake_word_model_paths)
        self._audio_buffer: np.ndarray = np.array([], dtype=np.int16)
        self._audio_buffer_size: int = 2 * self._model_sample_rate  # 2s sliding window

        self._wake_word_callback: bool = None
        self._last_detection_time: float = 0.0
        self._chunk_counter: int = 0
        self._stop_event = threading.Event()
        self._pause_event = threading.Event()
        self._pause_event.set()  # running by default

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

    def pause(self) -> None:
        """Pause wake word detection (audio is still captured but not processed)."""
        print("Wake word detector paused.")
        self._pause_event.clear()

    def resume(self) -> None:
        """Resume wake word detection."""
        print("Wake word detector resumed.")
        self._audio_queue.queue.clear()
        self._pause_event.set()

    def stop(self) -> None:
        """Stop the wake word detector and clean up resources."""
        print("Stopping wake word detector...")
        self._stop_event.set()
        self._pause_event.set()  # unblock if paused so the loop can exit
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
        print(
            f"Listening for wake words...{'(Paused)' if not self._pause_event.is_set else ''}"
        )
        print("#" * 100)

        callback = self._audio_callback_generator()
        next(callback)
        self._capture_device.start(callback)

        wake_word_detected_in_previous_chunk = False

        while not self._stop_event.is_set():
            # Get audio at native sample rate with timeout
            try:
                raw_data = self._audio_queue.get(timeout=0.5)
            except queue.Empty:
                continue

            if not self._pause_event.is_set():
                self._pause_event.wait()
                self._audio_queue.queue.clear()
                continue

            audio = np.frombuffer(raw_data, dtype=np.int16)

            # Apply software gain if configured
            if self._config.audio_gain != 1.0:
                audio = self._apply_audio_gain(audio)

            # Append to rolling buffer and trim to 2s
            self._audio_buffer = np.concatenate([self._audio_buffer, audio])
            if len(self._audio_buffer) > self._audio_buffer_size:
                self._audio_buffer = self._audio_buffer[-self._audio_buffer_size :]

            self._chunk_counter += 1
            if self._chunk_counter % self._config.inference_stride != 0:
                continue

            scores = self._model.predict(self._audio_buffer)

            wake_word_detected = False
            for m, score in scores.items():

                if score > self._detection_threshold:
                    # Add a newline if we didn't detect a wake word in the chunk before
                    if not wake_word_detected_in_previous_chunk:
                        print("")

                    wake_word_detected_in_previous_chunk = True
                    wake_word_detected = True
                    formatted_score: str = format(score, ".20f").replace("-", "")
                    formatted_model: str = f"{m}{' ' * (16 - len(m))}"

                    print(f"{formatted_model} | {formatted_score[0:5]}")
                else:
                    wake_word_detected_in_previous_chunk = False

                    if self._config.debug:
                        print("-", end="", flush=True)

            if wake_word_detected:
                now = time.monotonic()
                if now - self._last_detection_time >= self._config.debounce:
                    self._last_detection_time = now
                    self._audio_buffer = np.array([], dtype=np.int16)
                    if self._wake_word_callback:
                        self._wake_word_callback()

        print("Wake word detector stopped")

    def listen_for_wake_word_in_file(self, file_path: str) -> None:
        import wave

        print("#" * 100)
        print(f"Processing wake word detection from file: {file_path}")
        print("#" * 100)

        with wave.open(file_path, "rb") as wf:
            n_channels = wf.getnchannels()
            orig_sample_rate = wf.getframerate()
            n_frames = wf.getnframes()
            raw_data = wf.readframes(n_frames)

        # Convert to mono 16kHz int16 using miniaudio
        converted = miniaudio.convert_frames(
            from_fmt=miniaudio.SampleFormat.SIGNED16,
            from_numchannels=n_channels,
            from_samplerate=orig_sample_rate,
            sourcedata=raw_data,
            to_fmt=miniaudio.SampleFormat.SIGNED16,
            to_numchannels=1,
            to_samplerate=16000,
        )
        audio = np.frombuffer(converted, dtype=np.int16)

        # Apply software gain if configured
        if self._config.audio_gain != 1.0:
            audio = self._apply_audio_gain(audio)

        chunk_size = 1280
        wake_word_detected_in_previous_chunk = False
        wake_word_detected = False

        file_buffer: np.ndarray = np.array([], dtype=np.int16)
        file_chunk_counter = 0

        for i in range(0, len(audio) - chunk_size + 1, chunk_size):
            chunk = audio[i : i + chunk_size]
            file_buffer = np.concatenate([file_buffer, chunk])
            if len(file_buffer) > self._audio_buffer_size:
                file_buffer = file_buffer[-self._audio_buffer_size :]

            file_chunk_counter += 1
            if file_chunk_counter % self._config.inference_stride != 0:
                continue

            scores = self._model.predict(file_buffer)

            for m, score in scores.items():

                if score > self._detection_threshold:
                    # Add a newline if we didn't detect a wake word in the chunk before
                    if not wake_word_detected_in_previous_chunk:
                        print("")

                    wake_word_detected_in_previous_chunk = True
                    wake_word_detected = True
                    formatted_score: str = format(score, ".20f").replace("-", "")
                    formatted_model: str = f"{m}{' ' * (16 - len(m))}"
                    print(f"{formatted_model} | {formatted_score[0:5]}")
                else:
                    wake_word_detected_in_previous_chunk = False

                    print("-", end="", flush=True)

        if not wake_word_detected:
            print("\nNo wake word detected in file.")
