import numpy as np
import pyaudio
import struct
import scipy.fftpack as scp
import os
import math

# get window's dimensions
#rows = 40
#columns = 80

columns, rows = os.get_terminal_size()


buff_size = 0.1            # window size in seconds
wanted_num_of_bins = rows-4  # number of frequency bins to display
max_bar_length = columns-4   # Max length for the bars to prevent exceeding screen width

# initialize soundcard for recording:
fs = 24000
pa = pyaudio.PyAudio()
stream = pa.open(format=pyaudio.paInt16, channels=1, rate=fs,
                 input=True, frames_per_buffer=int(fs * buff_size))

def nonlinear_multiply_log(a, b):
    return math.exp(math.log(a) + math.log(b))

def colorize(text, color_code):
    return f"\033[{color_code}m{text}\033[0m"

def get_color_code(segment, total_segments):
    proportion = segment / total_segments
    if proportion > 0.75:
        return 91  # Red
    elif proportion > 0.5:
        return 93  # Yellow
    elif proportion > 0.25:
        return 92  # Green
    else:
        return 94  # Blue

def clear_screen():
    # Hide cursor
    print('\033[?25l', end='')

    # Clear screen
    print("\033[H\033[J", end="")

def apply_smoothing(data, window_size=3):
    """Applies a simple moving average smoothing to the data."""
    return np.convolve(data, np.ones(window_size)/window_size, mode='valid')

while True:  # for each recorded window (until ctrl+c is pressed)
    columns, rows = os.get_terminal_size()
    columns -= 2
    #rows += 2
    clear_screen()
    buffer = []
    #buffer.append("\033[H")  # Move cursor to the top left corner
    block = stream.read(int(fs * buff_size))
    format = "%dh" % (len(block) / 2)
    shorts = struct.unpack(format, block)

    # Amplify short ints
    shorts = [s * 90 for s in shorts]

    # then normalize and convert to numpy array:
    x = np.double(list(shorts)) / (2**15)
    seg_len = len(x)

    # get total energy of the current window and compute a normalization
    # factor (to be used for visualizing the maximum spectrogram value)
    energy = np.mean(x ** 2)
    max_energy = 0.005  # energy for which the bars are set to max
    max_width_from_energy = int((energy / max_energy) * max_bar_length) + 1
    if max_width_from_energy > max_bar_length:
        max_width_from_energy = max_bar_length

    # get the magnitude of the FFT and the corresponding frequencies
    X = np.abs(scp.fft(x))[0:int(seg_len/2)]
    freqs = (np.arange(0, 1 + 1.0/len(X), 1.0 / len(X)) * fs / 2)

    # resample to a fixed number of frequency bins (to visualize)
    wanted_step = X.size // wanted_num_of_bins#(int(freqs.shape[0] / wanted_num_of_bins))
    
    if X.size % wanted_step != 0:
    # If not, decrease wanted_step until it is a divisor of X.size
        while X.size % wanted_step != 0:
            wanted_step -= 1
    
    freqs2 = freqs[0::wanted_step].astype('int')
    X2 = np.mean(X.reshape(-1, wanted_step), axis=1)

    

    # Apply smoothing to the FFT values
    X2_smoothed = apply_smoothing(X2)

    # plot (freqs, fft) as horizontal histogram:
    for i, value in enumerate(X2_smoothed):
        max_bar_length = columns - 2 - len(f"{int(freqs2[i])} Hz".ljust(10))
        bar_length = int(value * max_width_from_energy)
        bar_length = min(bar_length, max_bar_length)  # Ensure the bar does not exceed the screen width
        bar = ""
        for segment in range(bar_length):
            color_code = get_color_code(segment, bar_length)
            bar += colorize("#", color_code)
        freq_label = f"{int(freqs2[i])} Hz".ljust(10)
        buffer.append((freq_label + bar).ljust(columns))  # Ensure the bar line clears the old bars
        
    # add exactly as many new lines as they are needed to
    # fill clear the screen in the next iteration:
    buffer.append("\n" * (int(rows) - freqs2.shape[0] - 1))

    # Print the buffer all at once
    print("\n".join(buffer))
