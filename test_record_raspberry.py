import queue
import time
import wave

import miniaudio

DEVICE_NAME = "PCM2902 Audio Codec Analog Mono"
DURATION = 10
SAMPLE_RATE = 16000
CHANNELS = 1
SAMPLE_FORMAT = miniaudio.SampleFormat.SIGNED16
CHUNK_SIZE = 1280
BUFFERSIZE_MSEC = int(1000 * CHUNK_SIZE / SAMPLE_RATE)


def find_device_id(name: str) -> object:
    devices = miniaudio.Devices()
    captures = devices.get_captures()
    matches = [
        (d["id"], d["name"]) for d in captures if name.lower() in d["name"].lower()
    ]
    if not matches:
        raise ValueError(f"No audio device matching '{name}'")
    if len(matches) > 1:
        raise ValueError(f"Multiple devices match '{name}': {[n for _, n in matches]}")
    print(f"Using device: {matches[0][1]}")
    return matches[0][0]


def next_filename() -> str:
    i = 1
    while True:
        name = f"sample_{i:04d}.wav"
        try:
            open(name, "x").close()
            import os

            os.remove(name)
        except FileExistsError:
            i += 1
            continue
        return name


def audio_callback_generator(q: queue.Queue):
    while True:
        data = yield
        if data:
            q.put(data)


def main():
    filename = next_filename()
    device_id = find_device_id(DEVICE_NAME)

    audio_queue: queue.Queue[bytes] = queue.Queue()
    capture = miniaudio.CaptureDevice(
        input_format=SAMPLE_FORMAT,
        nchannels=CHANNELS,
        sample_rate=SAMPLE_RATE,
        buffersize_msec=BUFFERSIZE_MSEC,
        device_id=device_id,
    )

    callback = audio_callback_generator(audio_queue)
    next(callback)

    chunks = []
    print(f"Recording for {DURATION}s...")
    capture.start(callback)
    deadline = time.monotonic() + DURATION
    while time.monotonic() < deadline:
        try:
            chunks.append(audio_queue.get(timeout=0.1))
        except queue.Empty:
            pass
    capture.close()

    raw = b"".join(chunks)
    with wave.open(filename, "wb") as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(raw)

    print(f"Saved {filename} ({len(raw) // 2 // SAMPLE_RATE:.1f}s)")


if __name__ == "__main__":
    main()
