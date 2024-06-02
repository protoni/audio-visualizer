import numpy as np
import pyaudio
import struct
import scipy.fftpack as scp
import os
import math
import time

# get window's dimensions
#rows = 40
#columns = 160

columns, rows = os.get_terminal_size()

buff_size = 0.02          # window size in seconds
wanted_num_of_bins = columns # number of frequency bins to display
max_bar_height = rows   # Max height for the bars to prevent exceeding screen height

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
    
    #print('\n' * rows)
    #os.system('cls')

    # Clear screen
    print("\033[H\033[J", end="")

def apply_smoothing(data, window_size=3):
    """Applies a simple moving average smoothing to the data."""
    return np.convolve(data, np.ones(window_size)/window_size, mode='valid')

# Initialize the terminal size
old_columns, old_rows = os.get_terminal_size()

# Initialize the frequency information
freq_info_str = ""

# Initialize the old graph
old_graph = []

while True:  # for each recorded window (until ctrl+c is pressed)
    #os.system('cls')
    columns, rows = os.get_terminal_size()
    rows -= 2
    clear_screen()
    
    buffer = [[" "] * columns for _ in range(rows)]
    #buffer.append("\033[H")
    block = stream.read(int(fs * buff_size))
    format = "%dh" % (len(block) / 2)
    shorts = struct.unpack(format, block)

    # Amplify short ints
    shorts = [s * 100 for s in shorts]
    #shorts = [s * (10 - (i * 0.1)) for i, s in enumerate(shorts)]
    #shorts = [s * (150 - (s * 0.1)) for s in shorts]
    #shorts = [s * 100 if s < 5.0 else s for s in shorts]
    #shorts = [s * (100 / (math.sqrt(abs(s)) + 1)) if s != 0 else 0 for s in shorts]

    # then normalize and convert to numpy array:
    x = np.double(list(shorts)) / (2**15)
    seg_len = len(x)

    # get total energy of the current window and compute a normalization
    # factor (to be used for visualizing the maximum spectrogram value)
    energy = np.mean(x ** 2)
    max_energy = 0.01  # energy for which the bars are set to max
    max_height_from_energy = int((energy / max_energy) * max_bar_height) + 1
    if max_height_from_energy > max_bar_height:
        max_height_from_energy = max_bar_height

    # get the magnitude of the FFT and the corresponding frequencies
    X = np.abs(scp.fft(x))[0:int(seg_len/2)]
    freqs = (np.arange(0, 1 + 1.0/len(X), 1.0 / len(X)) * fs / 2)

    # resample to a fixed number of frequency bins (to visualize)
    wanted_step = X.size // columns #(int(freqs.shape[0] / wanted_num_of_bins))
    if X.size % wanted_step != 0:
    # If not, decrease wanted_step until it is a divisor of X.size
        while X.size % wanted_step != 0:
            wanted_step -= 1
    freqs2 = freqs[0::wanted_step].astype('int')
    X2 = np.mean(X.reshape(-1, wanted_step), axis=1)

    # Apply smoothing to the FFT values
    X2_smoothed = apply_smoothing(X2)

    # Initialize the list to store frequency information
    freq_info = [[" " for _ in range(columns)] for _ in range(2)]  # Create two rows for frequency information

    # Calculate the spacing between the frequency information
    spacing = columns // 4

    # Create the vertical bars
    for i, value in enumerate(X2_smoothed):
        bar_height = int(value * max_height_from_energy)
        bar_height = min(bar_height, max_bar_height)  # Ensure the bar does not exceed the screen height
        for j in range(bar_height):
            color_code = get_color_code(j, bar_height)
            index = min(rows - 2 - j, rows - 1)
            i = min(i, columns - 1)
            #buffer[rows - 2 - j][i] = colorize("#", color_code)
            buffer[index][i] = colorize("#", color_code)

        # Print frequency information for every 25% of the graph
        if i % spacing == 0 and i // spacing < 4:
            freq = freqs2[i]
            freq_str = f"{freq} Hz"
            start_index = i if i < columns - len(freq_str) else columns - len(freq_str)  # Ensure the frequency information fits within the terminal width
            for j in range(len(freq_str)):
                freq_info[0][start_index + j] = freq_str[j]

    # Store the last frequency value
    freq = freqs2[-1]
    freq_str = f"{freq} Hz"
    start_index = columns - len(freq_str)  # Ensure the frequency information fits within the terminal width
    for j in range(len(freq_str)):
        freq_info[0][start_index + j] = freq_str[j]

    # Add frequency labels at the bottom
    #label_row = rows - 1
    #for i, freq in enumerate(freqs2):
    #    freq_label = f"{int(freq)}Hz".center(4)
    #    for j, char in enumerate(freq_label):
    #        if i * 2 + j < columns:  # Ensuring we stay within buffer bounds
    #            buffer[label_row][i * 2 + j] = char


    # Print the graph
    #for i, row in enumerate(buffer):
    #    if i < rows + 1:  # Leave one row empty at the bottom
    #        print("".join(row))

    # Calculate the number of empty lines needed above the graph
    #empty_lines = rows - len(buffer)

    # Print the empty lines
    #for _ in range(empty_lines):
    #    print()

    #for row in buffer:
    #    print("".join(row))

    for i, row in enumerate(freq_info):
        if i + len(buffer) < rows + 1:  # Leave one row empty at the bottom
            print("".join(row))

    # Print the parts of the graph that have changed
    for i, row in enumerate(reversed(buffer)):
        if i >= len(old_graph) or row != old_graph[i]:
            print("".join(row))

    # Print the frequency information below the graph
    

    #print('\033[{};{}H'.format(rows, 1), end='')
    #flat_list = [item for sublist in freq_info for item in sublist]
    #print("".join(flat_list))

    # Only redraw the frequency information if the terminal size has changed
    #if columns != old_columns or rows != old_rows:
    #    # Print the frequency information below the graph
    #    for i, row in enumerate(freq_info):
    #        if i + len(buffer) < rows + 1:  # Leave one row empty at the bottom
    #            print("".join(row))

    # Update the old graph
    old_graph = buffer

    # Update the old terminal size
    old_columns, old_rows = columns, rows

    #time.sleep(0.05)
#