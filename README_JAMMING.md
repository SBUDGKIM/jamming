# Jamming Signal Generator and Visualizer

This project generates a jamming signal using GNU Radio and visualizes it using matplotlib.

## Files

1. **`generate_jamming_signal.py`** - Generates a Gaussian noise jamming signal and saves it to a binary `.dat` file
2. **`visualize_jamming_signal.py`** - Loads the `.dat` file and creates comprehensive visualizations

## Requirements

```bash
# Install GNU Radio
sudo apt-get install gnuradio

# Install Python dependencies
pip3 install numpy matplotlib
```

## Usage

### Generate the Jamming Signal

```bash
python3 generate_jamming_signal.py
```

This will:
- Generate 5 seconds of Gaussian noise at 5 MHz sample rate
- Save the signal to `/tmp/jamming_signal.dat`
- Display generation statistics

### Visualize the Signal

```bash
# Use default settings (50k samples)
python3 visualize_jamming_signal.py

# Specify custom file and sample count
python3 visualize_jamming_signal.py --file /tmp/jamming_signal.dat --samples 100000
```

This will create visualizations showing:
1. **Time Domain (Real/Imag)** - First 10k samples of I and Q components
2. **Frequency Domain (FFT)** - Power spectral density across the bandwidth
3. **Constellation Diagram** - I/Q scatter plot showing signal distribution
4. **Spectrogram** - Time-frequency representation

The visualization is saved as `/tmp/jamming_signal_visualization.png` and displayed in a matplotlib window.

## Signal Parameters

- **Sample Rate**: 5 MHz
- **Center Frequency**: 1874.2 MHz (LTE Band 3)
- **Noise Type**: Gaussian (AWGN - Additive White Gaussian Noise)
- **Amplitude**: 0.5 (adjustable in code)
- **Duration**: 5 seconds (25 million samples)

## Customization

### Change Signal Parameters

Edit `generate_jamming_signal.py`:

```python
self.samp_rate = 10e6  # Change sample rate to 10 MHz
self.noise_amplitude = 1.0  # Increase noise amplitude
self.num_samples = int(10 * samp_rate)  # Generate 10 seconds
```

### Different Noise Types

Replace `analog.GR_GAUSSIAN` with:
- `analog.GR_UNIFORM` - Uniform distribution
- `analog.GR_LAPLACIAN` - Laplacian distribution
- `analog.GR_IMPULSE` - Impulse noise

### Add Filtering

Insert a filter between the noise source and file sink:

```python
from gnuradio import filter as grfilter

# Low-pass filter
self.lpf = grfilter.fir_filter_ccf(1, firdes.low_pass(
    1, samp_rate, 1e6, 500e3, window.WIN_HAMMING, 6.76))

# Update connections
self.connect((self.analog_noise_source, 0), (self.lpf, 0))
self.connect((self.lpf, 0), (self.blocks_head, 0))
```

## Output

- **Signal file**: `/tmp/jamming_signal.dat` (complex64 binary format)
- **Visualization**: `/tmp/jamming_signal_visualization.png`

## Statistics Output

The visualizer prints signal statistics:
- Number of samples
- Duration
- Sample rate
- Mean/std amplitude
- Peak amplitude
- RMS power

## Notes

- The `.dat` file uses `np.complex64` format (8 bytes per sample: 4 bytes I + 4 bytes Q)
- For 5 seconds at 5 MHz: file size ≈ 200 MB
- Visualization downsamples data for performance (default 50k samples)
- Use `--samples` argument to plot more/fewer samples

## Troubleshooting

**Error: "No data found in file!"**
- Ensure `generate_jamming_signal.py` ran successfully
- Check that `/tmp/jamming_signal.dat` exists and is not empty

**Performance issues with visualization**
- Reduce number of samples: `--samples 10000`
- Close the matplotlib window when done

**Memory issues**
- Reduce duration in generator: `self.num_samples = int(1 * samp_rate)`
