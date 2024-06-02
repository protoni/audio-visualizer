import pyaudio
import numpy as np

# Parameters
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
CHUNK = 1024

# Initialize PyAudio
p = pyaudio.PyAudio()

inputChannel = 1

# Open stream
stream = p.open(format=FORMAT,
                channels=CHANNELS,
                rate=RATE,
                input=True,
                input_device_index=inputChannel,
                frames_per_buffer=CHUNK)

def audio_to_ascii(data, width=50, height=10):
    """Convert audio data to an ASCII graph."""
    # Normalize data
    normalized_data = data / np.max(np.abs(data))
    # Reshape to match desired width
    step = len(normalized_data) // width
    reshaped_data = normalized_data[::step]
    
    # Create graph lines
    lines = []
    for y in range(height, -height-1, -1):
        line = ""
        for x in reshaped_data:
            if x * height > y:
                line += "█"
            else:
                line += " "
        lines.append(line)
    return "\n".join(lines)

print("Recording... Press Ctrl+C to stop.")

try:
    while True:
        # Read data from stream
        data = np.frombuffer(stream.read(CHUNK), dtype=np.int16)
        # Generate ASCII graph
        graph = audio_to_ascii(data)
        # Clear the console
        print("\033[H\033[J", end="")
        print(graph)
except KeyboardInterrupt:
    print("Recording stopped.")

# Stop and close the stream
stream.stop_stream()
stream.close()
p.terminate()
