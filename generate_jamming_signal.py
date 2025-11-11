#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generate a jamming signal and save to file
Uses GNU Radio without Qt dependencies
"""

from gnuradio import analog
from gnuradio import blocks
from gnuradio import gr
from gnuradio.filter import firdes
import time
import json

class jamming_signal_generator(gr.top_block):
    def __init__(self, output_file='/tmp/jamming_signal.dat'):
        gr.top_block.__init__(self, "Jamming Signal Generator")

        ##################################################
        # Variables
        ##################################################
        self.samp_rate = samp_rate = 5e6  # 1 MHz sample rate (try: 1e6, 5e6, 10e6)
        self.noise_amplitude = noise_amplitude = 0.1  # Noise amplitude (try: 0.1, 0.5, 1.0, 2.0)
        self.center_freq = center_freq = 1874.2e6  # 1.874 GHz
        self.num_samples = num_samples = int(2 * samp_rate)  # 2 seconds of data

        ##################################################
        # Blocks
        ##################################################
        
        # Noise source - Gaussian noise for jamming
        self.analog_noise_source = analog.noise_source_c(
            analog.GR_GAUSSIAN, 
            noise_amplitude, 
            0  # seed
        )
        
        # Head block to limit number of samples
        self.blocks_head = blocks.head(gr.sizeof_gr_complex, num_samples)
        
        # File sink to save the signal
        self.blocks_file_sink = blocks.file_sink(
            gr.sizeof_gr_complex*1, 
            output_file, 
            False  # not append
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


def main():
    output_file = 'jamming_signal.dat'
    metadata_file = 'jamming_signal_metadata.json'
    
    print("=" * 60)
    print("Jamming Signal Generator")
    print("=" * 60)
    
    tb = jamming_signal_generator(output_file)
    
    # Get actual values from the flowgraph
    samp_rate = tb.get_samp_rate()
    noise_amp = tb.get_noise_amplitude()
    center_freq = tb.get_center_freq()
    num_samples = tb.get_num_samples()
    duration = num_samples / samp_rate if samp_rate > 0 else 0
    
    print(f"Output file: {output_file}")
    print(f"Sample rate: {samp_rate / 1e6:.1f} MHz" if samp_rate >= 1e6 else f"Sample rate: {samp_rate} Hz")
    print(f"Duration: {duration:.1f} seconds")
    print(f"Center frequency: {center_freq / 1e6:.1f} MHz")
    print(f"Noise amplitude: {noise_amp}")
    print(f"Noise type: Gaussian (AWGN)")
    print(f"Total samples: {num_samples}")
    print("=" * 60)
    print("\nGenerating signal...")
    
    # Save metadata before running
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
    
    print(f"✓ Signal generated successfully in {elapsed_time:.2f} seconds")
    print(f"✓ Saved to: {output_file}")
    print(f"✓ Metadata saved to: {metadata_file}")
    print(f"\nTo visualize, run: python3 visualize_jamming_signal.py")


if __name__ == '__main__':
    main()
