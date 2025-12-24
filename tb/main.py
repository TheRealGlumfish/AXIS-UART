import os
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

if __name__ == '__main__':
    uart_tb_runner({'BAUD_RATE': 115200, 'CLK_FREQ': 10_000_000})
    # uart_tb_runner({'BAUD_RATE': 115200, 'CLK_FREQ': 50_000_000})
    # uart_tb_runner({'BAUD_RATE': 115200, 'CLK_FREQ': 400_000_000}) # Slow
    # uart_tb_runner({'BAUD_RATE': 9600, 'CLK_FREQ': 10_000_000})
    # uart_tb_runner({'BAUD_RATE': 9600, 'CLK_FREQ': 50_000_000})
    # uart_tb_runner({'BAUD_RATE': 9600, 'CLK_FREQ': 400_000_000}) # Slow