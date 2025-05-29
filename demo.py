# Copyright 2022 David Scripka. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Imports
import rich.traceback

rich.traceback.install(show_locals=True)

import pyaudio
import numpy as np
from openwakeword.model import Model

# The path of a specific model to load
# model_paths = []
# model_paths = ["resources/models/embedding_model.tflite"]
model_paths = [
    # "resources/models/alexa_v0.1.onnx",
    "resources/models/custom/hey_clock.onnx",
    "resources/models/custom/tic_toc.onnx",
]
melspec_model_path = "resources/models/melspectrogram.onnx"
embedding_model_path = "resources/models/embedding_model.onnx"

# The inference framework to use (either 'onnx' or 'tflite')
# inference_framework = "tflite"
inference_framework = "onnx"

# How much audio (in number of samples) to predict on at once
chunk_size = 1280

# Get microphone stream
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
CHUNK = chunk_size
audio = pyaudio.PyAudio()
mic_stream = audio.open(
    format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK
)

if model_paths is not None and len(model_paths) > 0:
    owwModel = Model(
        wakeword_models=model_paths,
        melspec_model_path=melspec_model_path,
        embedding_model_path=embedding_model_path,
        inference_framework=inference_framework,
    )
else:
    # Load pre-trained openwakeword models (broken in 0.6.0 and works in 0.5.1 since it ships with the models)
    owwModel = Model(inference_framework=inference_framework)

n_models = len(owwModel.models.keys())

# Run capture loop continuosly, checking for wakewords
if __name__ == "__main__":
    # Generate output string header
    print("\n\n")
    print("#" * 100)
    print("Listening for wakewords...")
    print("#" * 100)
    print("\n" * (n_models * 3))

    while True:
        # Get audio
        audio = np.frombuffer(mic_stream.read(CHUNK), dtype=np.int16)

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
        print("\033[F" * (4 * n_models + 1))
        print(output_string_header, "                             ", end="\r")
