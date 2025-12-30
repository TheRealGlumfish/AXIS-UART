# AXIS-UART
AXI4-Stream UART TX/RX for FPGA devices

## Parameters

- `BAUD_RATE` - TX/RX Baud rate
- `CLK_FREQ` - Input clock frequency

Note: The baud rate must be at least 4 times the clock frequency.

## Ports

- `clk_i` - Clock
- `rst_i` - Reset
- `uart_tx_o` - UART TX
- `uart_rx_i` - UART RX

#### AXI4-Stream Master (RX)
- `m_axis_rx_tdata[7:0]`
- `m_axis_rx_tvalid`

#### AXI4-Stream Slave (TX)
- `s_axis_tx_tdata[7:0]`
- `s_axis_tx_tvalid`
- `s_axis_tx_tready`

## Verification

The module has been functionally verified using cocotb and GHDL.
To run the testbench, install the dependencies in the [requirements](requirements.txt) file and run `python tb/main.py`.

## Implementation

On a Gowin GW2A family FPGA this synthesizes to ~58 LUTs at ~297 MHz (C8/I7 grade), the lower the ratio between the clock frequency and baud rate, the lower the utilization and higher max frequency.
Thus, higher baud rates are usually preferred.
For the clock domain crossing a double flop synchronizer has been used with the appropriate synthesis attributes to disable optimizations by Gowin synthesis.

An example UART loopback project is included in the [fpga](fpga) folder.
It is designed to be used with a Sipeed Tang Primer 20k FPGA board but should be easily adaptable to other boards as well.