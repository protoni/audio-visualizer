import numpy as np
import sounddevice as sd
from asciimatics.screen import Screen
from asciimatics.scene import Scene
from asciimatics.effects import Effect

# Parameters for sounddevice
SAMPLE_RATE = 44100  # Sampling rate (samples per second)
CHUNK = 1024  # Number of audio samples per frame

sd.default.device = 'YOUR_DEVICE_NAME_OR_INDEX'

class AudioVisualizerEffect(Effect):
    def __init__(self, screen):
        super().__init__(screen)
        self._screen = screen

    def _update(self, frame_no):
        # Capture audio data
        data = sd.rec(CHUNK, samplerate=SAMPLE_RATE, channels=1, dtype='float32')
        sd.wait()
        # Normalize the audio data
        data = data.flatten()
        max_amplitude = np.max(np.abs(data))
        if max_amplitude == 0:
            levels = np.zeros_like(data)
        else:
            levels = np.abs(data) / max_amplitude
        
        bar_length = self._screen.width - 2
        
        # Clear screen
        self._screen.clear_buffer(7, 0, 0)
        
        for i in range(0, CHUNK, CHUNK // self._screen.height):
            level = levels[i]
            length = int(level * bar_length)
            self._screen.print_at('|' * length, 0, i // (CHUNK // self._screen.height), colour=7)
        
        self._screen.refresh()

    def reset(self):
        pass

    @property
    def stop_frame(self):
        return 0

def visualize_audio(screen):
    scenes = [Scene([AudioVisualizerEffect(screen)], -1)]
    screen.play(scenes)

if __name__ == "__main__":
    Screen.wrapper(visualize_audio)
