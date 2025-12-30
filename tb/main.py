import os
import argparse
from pathlib import Path
from cocotb_tools.runner import get_runner

rtl_dir = Path('./rtl')
fpga_dir = Path('./fpga')

def uart_tb_runner(parameters):
    sim = os.getenv('SIM', 'ghdl')
    runner = get_runner(sim)
    runner.build(
        hdl_toplevel='uart',
        sources = [rtl_dir / 'uart.vhd'],
        parameters=parameters,
        waves=True
    )

    runner.test(
        test_module='uart_tb',
        hdl_toplevel='uart',
        waves=True
    )

def top_tb_runner():
    sim = os.getenv('SIM', 'ghdl')
    runner = get_runner(sim)
    runner.build(
        hdl_toplevel='top',
        sources = [rtl_dir / 'uart.vhd', fpga_dir / 'src/top.vhd'],
        waves=True
    )

    runner.test(
        test_module='top_tb',
        hdl_toplevel='top',
        waves=True
    )

def main():
    parser = argparse.ArgumentParser()
    # Make top and (clk freq, baud rate) mutually exclusive
    parser.add_argument('--top', action='store_true', help='Run top_tb')
    parser.add_argument('--baud_rate', type=int, default=115200, help='Baud rate')
    parser.add_argument('--clk_freq', type=int, default=10_000_000, help='Clock frequency')
    args = parser.parse_args()
    if args.top:
        top_tb_runner()
    else:
        uart_tb_runner({'BAUD_RATE': args.baud_rate, 'CLK_FREQ': args.clk_freq})

if __name__ == '__main__':
    main()