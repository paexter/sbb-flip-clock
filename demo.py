# Imports
import rich.traceback

rich.traceback.install(show_locals=True)

import pyaudio
import numpy as np
from openwakeword.model import Model

# WAKE_WORD_MODEL_PATHS = ["resources/models/embedding_model.tflite"]
WAKE_WORD_MODEL_PATHS = [
    "resources/models/alexa_v0.1.onnx",
    "resources/models/custom/hey_clock.onnx",
    "resources/models/custom/tic_toc.onnx",
]
melspec_model_path = "resources/models/melspectrogram.onnx"
embedding_model_path = "resources/models/embedding_model.onnx"

# The inference framework to use (either 'onnx' or 'tflite')
# INFERENCE_FRAMEWORK = "tflite"
INFERENCE_FRAMEWORK = "onnx"

FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
CHUNK = 1280  # How much audio (in number of samples) to predict on at once
INPUT_DEVICE_INDEX = None  # Set to None to use the default microphone

ENABLE_SPEEX_NOISE_SUPPRESSION = (
    False  # Linux only, requires pyaudio with speex support
)

# Get microphone stream
audio = pyaudio.PyAudio()

for i in range(audio.get_device_count()):
    device_info = audio.get_device_info_by_index(i)
    print(f"Device {i}: {device_info['name']}")

mic_stream = audio.open(
    format=FORMAT,
    channels=CHANNELS,
    rate=RATE,
    input=True,
    frames_per_buffer=CHUNK,
    input_device_index=INPUT_DEVICE_INDEX,
)

owwModel = Model(
    wakeword_models=WAKE_WORD_MODEL_PATHS,
    melspec_model_path=melspec_model_path,
    embedding_model_path=embedding_model_path,
    inference_framework=INFERENCE_FRAMEWORK,
    enable_speex_noise_suppression=ENABLE_SPEEX_NOISE_SUPPRESSION,
)

model_count = len(owwModel.models.keys())

# Run capture loop continuosly, checking for wakewords
if __name__ == "__main__":
    # Generate output string header
    print("\n\n")
    print("#" * 100)
    print("Listening for wakewords...")
    print("#" * 100)
    print("\n" * (model_count * 3))

    while True:
        # Get audio
        audio = np.frombuffer(
            mic_stream.read(CHUNK, exception_on_overflow=False), dtype=np.int16
        )

        # Feed to openWakeWord model
        prediction = owwModel.predict(audio)

        # Column titles
        n_spaces = 16
        output_string_header = """
            Model Name         | Score | Wakeword Status
            --------------------------------------
            """

        for mdl in owwModel.prediction_buffer.keys():
            # Add scores in formatted table
            scores = list(owwModel.prediction_buffer[mdl])
            curr_score = format(scores[-1], ".20f").replace("-", "")

            output_string_header += f"""{mdl}{" "*(n_spaces - len(mdl))}   | {curr_score[0:5]} | {"--"+" "*20 if scores[-1] <= 0.1 else "Wakeword Detected!"}
            """

        # Print results table
        print("\033[F" * (4 * model_count + 1))
        print(output_string_header, "                             ", end="\r")
