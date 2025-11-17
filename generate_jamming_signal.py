#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
generate_jamming_signal.py

Original GNU Radio jamming generator is preserved (if GNU Radio is installed).
Added: a pure-Python LTE/WiFi-like OFDM signal simulator and plotting routines
that produce three cases each (weak / near_drown / full_drown). Use the
command-line flag --mode to choose 'generate' (GNU Radio) or 'simulate' (plots).

This file no longer requires GNU Radio to run the 'simulate' mode.
"""

import time
import json
import os
import argparse
import sys

# Try to import GNU Radio components; make them optional so simulate mode works
try:
    from gnuradio import analog
    from gnuradio import blocks
    from gnuradio import gr
    from gnuradio.filter import firdes
    GNURADIO_AVAILABLE = True
except Exception:
    GNURADIO_AVAILABLE = False

import numpy as np
import matplotlib.pyplot as plt
from scipy import signal as sp_signal


if GNURADIO_AVAILABLE:
    class jamming_signal_generator(gr.top_block):
        def __init__(self, output_file='jamming_signal.dat'):
            gr.top_block.__init__(self, "Jamming Signal Generator")

            ##################################################
            # Variables
            ##################################################
            self.samp_rate = samp_rate = 5e6  # 5 MHz sample rate
            self.noise_amplitude = noise_amplitude = 0.1
            self.center_freq = center_freq = 1874.2e6
            self.num_samples = num_samples = int(2 * samp_rate)  # 2 seconds of data

            ##################################################
            # Blocks
            ##################################################
            self.analog_noise_source = analog.noise_source_c(
                analog.GR_GAUSSIAN,
                noise_amplitude,
                0
            )

            self.blocks_head = blocks.head(gr.sizeof_gr_complex, num_samples)

            self.blocks_file_sink = blocks.file_sink(
                gr.sizeof_gr_complex * 1,
                output_file,
                False
            )
            self.blocks_file_sink.set_unbuffered(False)

            ##################################################
            # Connections
            ##################################################
            self.connect((self.analog_noise_source, 0), (self.blocks_head, 0))
            self.connect((self.blocks_head, 0), (self.blocks_file_sink, 0))

        def get_samp_rate(self):
            return self.samp_rate

        def get_noise_amplitude(self):
            return self.noise_amplitude

        def get_center_freq(self):
            return self.center_freq

        def get_num_samples(self):
            return self.num_samples


def generate_ofdm(num_subcarriers, num_symbols, fft_size, cp_len, mod_order, samp_rate):
    """Generate a simplified OFDM baseband signal (complex) using PSK mapping.

    This is not a standards-accurate implementation. It creates data symbols,
    maps them onto central subcarriers, IFFT, adds cyclic prefix, and
    concatenates symbols.
    """
    num_data = num_subcarriers
    symbols = np.random.randint(0, mod_order, size=(num_symbols, num_data))
    # PSK mapping
    phase = 2 * np.pi * symbols / mod_order
    mapped = np.exp(1j * phase)

    time_domain = []
    for sym in mapped:
        freq_domain = np.zeros(fft_size, dtype=complex)
        start = (fft_size // 2) - (num_data // 2)
        freq_domain[start:start + num_data] = sym
        td = np.fft.ifft(np.fft.ifftshift(freq_domain))
        td_cp = np.concatenate([td[-cp_len:], td])
        time_domain.append(td_cp)
    return np.concatenate(time_domain)


def generate_lte_like(duration_s, samp_rate):
    subcarrier_spacing = 15e3
    fft_size = 2048
    num_subcarriers = 1200
    cp_len = fft_size // 16
    # symbol_time approx (use 1/subcarrier_spacing as OFDM symbol w/o exact LTE framing)
    symbol_time = (fft_size + cp_len) / samp_rate
    num_symbols = max(4, int(duration_s / symbol_time))
    return generate_ofdm(num_subcarriers, num_symbols, fft_size, cp_len, 4, samp_rate)


def generate_wifi_like(duration_s, samp_rate):
    fft_size = 64
    num_subcarriers = 52
    cp_len = 16
    symbol_time = (fft_size + cp_len) / samp_rate
    num_symbols = max(8, int(duration_s / symbol_time))
    return generate_ofdm(num_subcarriers, num_symbols, fft_size, cp_len, 4, samp_rate)


def add_jammer(sig, jammer_amplitude):
    noise = (np.random.normal(size=sig.shape) + 1j * np.random.normal(size=sig.shape)) * (jammer_amplitude / np.sqrt(2))
    return sig + noise


def plot_cases(signal_clean, samp_rate, tech_name, out_dir='plots', jam_multipliers=None):
    """Plot PSD and spectrogram for three jammer levels.

    jam_multipliers: tuple (weak_mult, near_mult, full_mult) relative to signal RMS.
    If None, defaults to (0.2, 1.0, 5.0).
    """
    os.makedirs(out_dir, exist_ok=True)
    rms = np.sqrt(np.mean(np.abs(signal_clean) ** 2))
    if jam_multipliers is None:
        multipliers = (0.2, 1.0, 5.0)
    else:
        multipliers = tuple(jam_multipliers)

    cases = {
        'weak': multipliers[0] * rms,
        'near_drown': multipliers[1] * rms,
        'full_drown': multipliers[2] * rms,
    }

    for case_name, jam_amp in cases.items():
        mixed = add_jammer(signal_clean, jam_amp)

        # PSD using Welch; request two-sided so we can fftshift
        f, Pxx = sp_signal.welch(mixed, fs=samp_rate, nperseg=4096, return_onesided=False)
        # Shift for plotting
        f_shifted = np.fft.fftshift(f) - samp_rate / 2.0
        Pxx_shifted = np.fft.fftshift(Pxx)

        fig, axs = plt.subplots(1, 2, figsize=(12, 4))
        axs[0].plot(f_shifted / 1e6, 10 * np.log10(np.abs(Pxx_shifted) + 1e-12))
        axs[0].set_title(f'{tech_name} PSD - {case_name}')
        axs[0].set_xlabel('Frequency (MHz)')
        axs[0].set_ylabel('Power (dB)')
        axs[0].grid(True)

        axs[1].specgram(mixed, NFFT=1024, Fs=samp_rate, noverlap=512, cmap='plasma')
        axs[1].set_title(f'{tech_name} Spectrogram - {case_name}')
        axs[1].set_xlabel('Time (s)')
        axs[1].set_ylabel('Frequency')

        plt.tight_layout()
        out_path = os.path.join(out_dir, f"{tech_name.lower()}_{case_name}.png")
        fig.savefig(out_path, dpi=150)
        plt.close(fig)
        print(f"Saved {out_path} (jam_amp={jam_amp:.4g}, signal_rms={rms:.4g})")


def run_simulation(args):
    samp_rate = args.samp_rate
    duration = args.duration
    print('Generating LTE-like signal...')
    lte = generate_lte_like(duration, samp_rate)
    print('Generating WiFi-like signal...')
    wifi = generate_wifi_like(duration, samp_rate)
    print('Plotting LTE cases...')
    plot_cases(lte, samp_rate, 'LTE', out_dir=args.out_dir,
               jam_multipliers=(args.jam_weak, args.jam_near, args.jam_full))
    print('Plotting WiFi cases...')
    plot_cases(wifi, samp_rate, 'WiFi', out_dir=args.out_dir,
               jam_multipliers=(args.jam_weak, args.jam_near, args.jam_full))
    print(f'Done. Plots saved in {args.out_dir}')


def run_gnuradio_generate(args):
    if not GNURADIO_AVAILABLE:
        print('GNU Radio not available in this environment. Install gnuradio to use generate mode.')
        return 1

    output_file = args.output_file
    metadata_file = args.metadata_file

    print('=' * 60)
    print('Jamming Signal Generator (GNU Radio)')
    print('=' * 60)

    tb = jamming_signal_generator(output_file)

    samp_rate = tb.get_samp_rate()
    noise_amp = tb.get_noise_amplitude()
    center_freq = tb.get_center_freq()
    num_samples = tb.get_num_samples()
    duration = num_samples / samp_rate if samp_rate > 0 else 0

    print(f'Output file: {output_file}')
    print(f'Sample rate: {samp_rate / 1e6:.1f} MHz' if samp_rate >= 1e6 else f'Sample rate: {samp_rate} Hz')
    print(f'Duration: {duration:.1f} seconds')
    print(f'Center frequency: {center_freq / 1e6:.1f} MHz')
    print(f'Noise amplitude: {noise_amp}')
    print('Noise type: Gaussian (AWGN)')
    print(f'Total samples: {num_samples}')
    print('=' * 60)
    print('\nGenerating signal...')

    metadata = {
        'samp_rate': samp_rate,
        'noise_amplitude': noise_amp,
        'center_freq': center_freq,
        'num_samples': num_samples,
        'duration': duration,
        'noise_type': 'GR_GAUSSIAN'
    }

    with open(metadata_file, 'w') as f:
        json.dump(metadata, f, indent=2)

    start_time = time.time()
    tb.run()
    elapsed_time = time.time() - start_time

    print(f'✓ Signal generated successfully in {elapsed_time:.2f} seconds')
    print(f'✓ Saved to: {output_file}')
    print(f'✓ Metadata saved to: {metadata_file}')
    return 0


def parse_args(argv=None):
    p = argparse.ArgumentParser(description='Generate jamming signal or simulate LTE/WiFi jamming cases')
    p.add_argument('--mode', choices=['simulate', 'generate'], default='simulate', help='Mode: simulate (plots) or generate (GNU Radio file)')
    # simulate options
    p.add_argument('--samp-rate', type=float, default=20e6, help='Sampling rate for simulation (Hz)')
    p.add_argument('--duration', type=float, default=0.05, help='Duration for simulation (s)')
    p.add_argument('--out-dir', type=str, default='plots', help='Output directory for plots')
    # jam level multipliers relative to signal RMS (weak, near, full)
    p.add_argument('--jam-weak', type=float, default=0.2, help='Weak jammer multiplier (times signal RMS)')
    p.add_argument('--jam-near', type=float, default=1.0, help='Near-drown jammer multiplier (times signal RMS)')
    p.add_argument('--jam-full', type=float, default=5.0, help='Full-drown jammer multiplier (times signal RMS)')
    # generate options
    p.add_argument('--output-file', type=str, default='jamming_signal.dat', help='Output file for generated samples')
    p.add_argument('--metadata-file', type=str, default='jamming_signal_metadata.json', help='Metadata JSON filename')
    return p.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    if args.mode == 'simulate':
        run_simulation(args)
    else:
        rc = run_gnuradio_generate(args)
        if rc is not None and rc != 0:
            sys.exit(rc)


if __name__ == '__main__':
    main()
