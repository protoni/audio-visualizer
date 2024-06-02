# audio-visualizer
Tools for visualizing audio spectrum


#### Setup
```bash

# Create virtual environment
python -m venv venv
.\venv\Scripts\activate

# Install dependencies
pip install numpy pyaudio scipy sounddevice asciimatics
```

#### Run
```bash

# Run horizontal CLI ASCII spectrum analyzer
python .\ascii_horizontal.py

# Run vertical CLI ASCII spectrum analyzer
python .\ascii_vertical.py

# Query available input devices
python .\check.py

# Run different visualizers experiments
python .\visualizer.py
python .\visualizer_pyaudio.py
python .\visualizer_sounddevice.py
python .\visualizer_sounddevice2.py

# Run rust based visualizer
cd audio-visualizer-rust
cargo run

```