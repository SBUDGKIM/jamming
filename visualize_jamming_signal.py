#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Visualize jamming signal from .dat file using matplotlib
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
import json
import os

def load_complex_data(filename, num_samples=None):
    """Load complex IQ data from binary file"""
    data = np.fromfile(filename, dtype=np.complex64)
    if num_samples:
        data = data[:num_samples]
    return data

def plot_jamming_signal(filename='jamming_signal.dat', num_samples=50000, use_fixed_scale=True, target_band='wifi'):
    """
    Visualize the jamming signal in multiple domains
    
    Parameters:
    -----------
    filename : str
        Path to the .dat file containing complex samples
    num_samples : int
        Number of samples to plot (default: 50000 for better performance)
    use_fixed_scale : bool
        Use fixed absolute scales (True) or auto-scale (False)
    target_band : str
        Target communication band: 'wifi', 'lte', or 'generic'
    """
    
    # Try to load metadata
    metadata_file = filename.replace('.dat', '_metadata.json')
    metadata = None
    
    if os.path.exists(metadata_file):
        print(f"Loading metadata from: {metadata_file}")
        with open(metadata_file, 'r') as f:
            metadata = json.load(f)
        samp_rate = metadata['samp_rate']
        center_freq = metadata['center_freq']
        noise_amp = metadata['noise_amplitude']
        total_samples = metadata['num_samples']
        print(f"✓ Metadata loaded: samp_rate={samp_rate/1e6:.1f} MHz, noise_amp={noise_amp}")
    else:
        print(f"Warning: No metadata file found at {metadata_file}")
        print("Using default values (may be incorrect)")
        samp_rate = 5e6
        center_freq = 1874.2e6
        noise_amp = 0.5
        total_samples = None
    
    print(f"Loading signal from: {filename}")
    signal = load_complex_data(filename, num_samples)
    
    if len(signal) == 0:
        print("Error: No data found in file!")
        return
    
    print(f"Loaded {len(signal)} samples")
    
    # Define scale limits based on target band
    scale_configs = {
        'wifi': {
            'time_ylim': (-3.0, 3.0),          # Typical WiFi signal amplitude range
            'freq_ylim': (-80, 10),             # dB scale for WiFi signals
            'constellation_lim': (-3, 3),       # I/Q constellation limits
            'bandwidth': '20 MHz (WiFi)',
            'description': 'WiFi 2.4GHz/5GHz typical levels'
        },
        'lte': {
            'time_ylim': (-2.0, 2.0),          # LTE signal amplitude range
            'freq_ylim': (-100, 0),             # dB scale for LTE
            'constellation_lim': (-2, 2),       # I/Q constellation limits
            'bandwidth': '5-20 MHz (LTE)',
            'description': 'LTE cellular typical levels'
        },
        'generic': {
            'time_ylim': (-5.0, 5.0),          # Generic wider range
            'freq_ylim': (-120, 20),            # Wide dB range
            'constellation_lim': (-5, 5),       # Wide constellation
            'bandwidth': 'Variable',
            'description': 'Generic wide range'
        }
    }
    
    # Select configuration
    if target_band not in scale_configs:
        target_band = 'generic'
    config = scale_configs[target_band]
    
    print(f"Using scale configuration: {target_band.upper()} - {config['description']}")
    print(f"Fixed scale mode: {'ENABLED' if use_fixed_scale else 'DISABLED (auto-scale)'}")
    
    # Time vector
    t = np.arange(len(signal)) / samp_rate
    
    # Calculate frequency domain (FFT)
    fft_signal = np.fft.fftshift(np.fft.fft(signal))
    freqs = np.fft.fftshift(np.fft.fftfreq(len(signal), 1/samp_rate))
    
    # Power spectral density
    psd = 20 * np.log10(np.abs(fft_signal) + 1e-10)
    
    # Create figure with subplots
    fig = plt.figure(figsize=(15, 10))
    gs = GridSpec(3, 2, figure=fig)
    
    # 1. Time domain - Real part
    ax1 = fig.add_subplot(gs[0, 0])
    ax1.plot(t[:10000] * 1e3, np.real(signal[:10000]), 'b-', linewidth=0.5)
    ax1.set_xlabel('Time (ms)')
    ax1.set_ylabel('Amplitude (Real)')
    ax1.set_title('Time Domain - Real Part (first 10k samples)')
    ax1.grid(True, alpha=0.3)
    if use_fixed_scale:
        ax1.set_ylim(config['time_ylim'])
        ax1.axhline(y=0, color='k', linestyle='--', linewidth=0.5, alpha=0.5)
    
    # 2. Time domain - Imaginary part
    ax2 = fig.add_subplot(gs[0, 1])
    ax2.plot(t[:10000] * 1e3, np.imag(signal[:10000]), 'r-', linewidth=0.5)
    ax2.set_xlabel('Time (ms)')
    ax2.set_ylabel('Amplitude (Imag)')
    ax2.set_title('Time Domain - Imaginary Part (first 10k samples)')
    ax2.grid(True, alpha=0.3)
    if use_fixed_scale:
        ax2.set_ylim(config['time_ylim'])
        ax2.axhline(y=0, color='k', linestyle='--', linewidth=0.5, alpha=0.5)
    
    # 3. Frequency domain (FFT)
    ax3 = fig.add_subplot(gs[1, :])
    ax3.plot(freqs / 1e6, psd, 'g-', linewidth=1)
    ax3.set_xlabel('Frequency (MHz)')
    ax3.set_ylabel('Power (dB)')
    title_suffix = f' [{config["bandwidth"]}]' if use_fixed_scale else ''
    ax3.set_title(f'Frequency Domain (Power Spectral Density){title_suffix}')
    ax3.grid(True, alpha=0.3)
    ax3.set_xlim([freqs[0] / 1e6, freqs[-1] / 1e6])
    if use_fixed_scale:
        ax3.set_ylim(config['freq_ylim'])
        # Add reference lines
        ax3.axhline(y=-30, color='orange', linestyle='--', linewidth=0.8, alpha=0.5, label='Typical threshold')
        ax3.axhline(y=-60, color='red', linestyle='--', linewidth=0.8, alpha=0.5, label='Noise floor')
        ax3.legend(loc='upper right', fontsize=8)
    
    # 4. Constellation diagram (I/Q plot)
    ax4 = fig.add_subplot(gs[2, 0])
    ax4.scatter(np.real(signal[::100]), np.imag(signal[::100]), 
                s=1, alpha=0.3, c='blue')
    ax4.set_xlabel('In-phase (I)')
    ax4.set_ylabel('Quadrature (Q)')
    ax4.set_title('Constellation Diagram (I/Q Plot)')
    ax4.grid(True, alpha=0.3)
    if use_fixed_scale:
        lim = config['constellation_lim']
        ax4.set_xlim([lim[0], lim[1]])
        ax4.set_ylim([lim[0], lim[1]])
        # Add reference circles
        circle1 = plt.Circle((0, 0), 0.5, color='green', fill=False, linestyle='--', linewidth=0.8, alpha=0.4, label='Low power')
        circle2 = plt.Circle((0, 0), 1.0, color='orange', fill=False, linestyle='--', linewidth=0.8, alpha=0.4, label='Medium power')
        circle3 = plt.Circle((0, 0), 1.5, color='red', fill=False, linestyle='--', linewidth=0.8, alpha=0.4, label='High power')
        ax4.add_patch(circle1)
        ax4.add_patch(circle2)
        ax4.add_patch(circle3)
        ax4.axhline(y=0, color='k', linestyle='-', linewidth=0.5, alpha=0.3)
        ax4.axvline(x=0, color='k', linestyle='-', linewidth=0.5, alpha=0.3)
        ax4.legend(loc='upper right', fontsize=7)
    ax4.axis('equal')
    
    # 5. Spectrogram (time-frequency)
    ax5 = fig.add_subplot(gs[2, 1])
    NFFT = 1024
    noverlap = 512
    
    powerSpectrum, freqsSpec, time_spec, im = ax5.specgram(
        signal, 
        NFFT=NFFT,
        Fs=samp_rate,
        noverlap=noverlap,
        cmap='viridis'
    )
    
    ax5.set_xlabel('Time (s)')
    ax5.set_ylabel('Frequency (Hz)')
    ax5.set_title('Spectrogram (Time-Frequency)')
    cbar = plt.colorbar(im, ax=ax5)
    cbar.set_label('Power (dB)')
    
    # Overall title with metadata info
    if metadata:
        scale_mode = f'{target_band.upper()} Fixed Scale' if use_fixed_scale else 'Auto-Scale'
        title_text = f'Jamming Signal Analysis - {scale_mode} (SR: {samp_rate/1e6:.1f} MHz, Amp: {noise_amp}, Samples: {len(signal)})'
    else:
        scale_mode = f'{target_band.upper()} Fixed Scale' if use_fixed_scale else 'Auto-Scale'
        title_text = f'Jamming Signal Analysis - {scale_mode} (No Metadata)'
    fig.suptitle(title_text, fontsize=13, fontweight='bold')
    
    plt.tight_layout()
    
    # Save figure
    output_png = filename.replace('.dat', '_visualization.png')
    plt.savefig(output_png, dpi=150, bbox_inches='tight')
    print(f"✓ Visualization saved to: {output_png}")
    
    # Show plot
    plt.show()
    
    # Print statistics
    print("\n" + "=" * 60)
    print("Signal Statistics:")
    print("=" * 60)
    print(f"Target Band: {target_band.upper()}")
    print(f"Scale Mode: {'Fixed (Absolute)' if use_fixed_scale else 'Auto (Relative)'}")
    if metadata:
        print(f"Sample rate (from metadata): {samp_rate / 1e6:.1f} MHz" if samp_rate >= 1e6 else f"Sample rate: {samp_rate} Hz")
        print(f"Noise amplitude (from metadata): {noise_amp}")
        print(f"Center frequency (from metadata): {center_freq / 1e6:.1f} MHz")
        if total_samples:
            print(f"Total samples generated: {total_samples}")
    print(f"Samples loaded: {len(signal)}")
    print(f"Duration: {len(signal) / samp_rate:.3f} seconds")
    print(f"Mean amplitude: {np.mean(np.abs(signal)):.4f}")
    print(f"Std deviation: {np.std(np.abs(signal)):.4f}")
    print(f"Peak amplitude: {np.max(np.abs(signal)):.4f}")
    print(f"RMS power: {np.sqrt(np.mean(np.abs(signal)**2)):.4f}")
    
    # Provide interpretation based on target band
    if use_fixed_scale:
        print(f"\n{target_band.upper()} Scale Interpretation:")
        rms = np.sqrt(np.mean(np.abs(signal)**2))
        if target_band == 'wifi':
            if rms > 1.5:
                print("  ⚠ STRONG jamming - likely to disrupt WiFi (>1.5)")
            elif rms > 0.8:
                print("  ⚡ MEDIUM jamming - may affect WiFi (0.8-1.5)")
            else:
                print("  ✓ WEAK jamming - minimal WiFi impact (<0.8)")
        elif target_band == 'lte':
            if rms > 1.0:
                print("  ⚠ STRONG jamming - likely to disrupt LTE (>1.0)")
            elif rms > 0.5:
                print("  ⚡ MEDIUM jamming - may affect LTE (0.5-1.0)")
            else:
                print("  ✓ WEAK jamming - minimal LTE impact (<0.5)")
    print("=" * 60)


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Visualize jamming signal from .dat file with fixed or auto scaling',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # WiFi analysis with fixed scale
  python3 visualize_jamming_signal.py --band wifi
  
  # LTE analysis with fixed scale
  python3 visualize_jamming_signal.py --band lte
  
  # Auto-scale mode
  python3 visualize_jamming_signal.py --auto-scale
  
  # Custom file with LTE scale
  python3 visualize_jamming_signal.py -f my_signal.dat --band lte --samples 100000
        """)
    
    parser.add_argument('--file', '-f', 
                        default='jamming_signal.dat',
                        help='Input .dat file (default: jamming_signal.dat)')
    parser.add_argument('--samples', '-n', 
                        type=int, 
                        default=50000,
                        help='Number of samples to plot (default: 50000)')
    parser.add_argument('--band', '-b',
                        choices=['wifi', 'lte', 'generic'],
                        default='wifi',
                        help='Target communication band for fixed scale (default: wifi)')
    parser.add_argument('--auto-scale', '-a',
                        action='store_true',
                        help='Use auto-scaling instead of fixed absolute scale')
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("Jamming Signal Visualizer")
    print("=" * 60)
    
    plot_jamming_signal(args.file, args.samples, 
                       use_fixed_scale=not args.auto_scale,
                       target_band=args.band)


if __name__ == '__main__':
    main()
