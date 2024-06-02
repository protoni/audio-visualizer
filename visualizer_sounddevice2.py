import sounddevice as sd
import numpy as np

# Parameters
RATE = 44100 / 4
CHUNK = 1024
WIDTH = 100
HEIGHT = 15
NOISE_THRESHOLD = 0.03  # Adjusted threshold for better noise filtering

def audio_to_ascii(data, width=WIDTH, height=HEIGHT):
    """Convert audio data to an ASCII graph."""
    # Normalize data
    max_val = np.max(np.abs(data))
    if max_val == 0:
        max_val = 1  # Prevent division by zero
    normalized_data = data / max_val
    # Reshape to match desired width
    step = len(normalized_data) // width
    reshaped_data = normalized_data[::step]
    
    # Create graph lines
    lines = []
    for y in range(height, -height-1, -1):
        line = ""
        for x in reshaped_data:
            if abs(x) < NOISE_THRESHOLD:
                line += " "
            elif x * height > y:
                line += "█"
            else:
                line += " "
        lines.append(line)
    return "\n".join(lines)

def callback(indata, frames, time, status):
    """This is called (from a separate thread) for each audio block."""
    if status:
        print(status, flush=True)
    data = indata[:, 0]
    graph = audio_to_ascii(data)
    # Clear the console
    print("\033[H\033[J", end="")
    print(graph)

print("Recording... Press Ctrl+C to stop.")

try:
    with sd.InputStream(samplerate=RATE, blocksize=CHUNK, channels=1, callback=callback):
        while True:
            sd.sleep(1000)  # Keep the stream open
except KeyboardInterrupt:
    print("Recording stopped.")
