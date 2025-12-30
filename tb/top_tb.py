import cocotb
import random
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer
from cocotbext.uart import UartSource, UartSink

class TopEnv():
    def __init__(self, dut):
        self.dut = dut
        self.clk_freq = 27_000_000
        self.baud_rate = 250_000
        self.clock = Clock(dut.clk, round(1e9 / self.clk_freq), unit="ns")
        self.tx_sink = UartSink(dut.uart_tx, baud=self.baud_rate)
        self.rx_source = UartSource(dut.uart_rx, baud=self.baud_rate)
        cocotb.log.info(f'UART Environment initialized with baud rate: {self.baud_rate} and clock frequency: {self.clk_freq}')
    
    async def reset_dut(self):
        self.dut.rst_n.value = 0
        await RisingEdge(self.dut.clk)
        self.dut.rst_n.value = 1
        cocotb.log.info('DUT Reset')
    
    def seconds_per_packet(self):
        bits_per_packet = 1 + 8 + 1  # Start bit + Data bits + Stop bit
        return bits_per_packet / self.baud_rate
    
    def clock_period(self):
        return 1 / self.clk_freq
    
@cocotb.test()
async def basic_loopback(dut):
    env = TopEnv(dut)
    cocotb.start_soon(env.clock.start())
    await env.reset_dut()

    test_data = b'5678'
    expected_data = b'\x0767\x07'
    await env.rx_source.write(test_data)
    await env.rx_source.wait()
    await Timer(env.seconds_per_packet(), unit='sec', round_mode='round') # Wait for the last byte to be fully transmitted
    received_data = bytes(await env.tx_sink.read())
    assert received_data == expected_data, f"Received data {received_data} does not match expected data {expected_data}"

@cocotb.test()
@cocotb.parametrize(reset_point=[1 / 1.5, 1 / 2, 1 / 3, 1 / 10])
async def reset_loopback(dut, reset_point):
    env = TopEnv(dut)
    cocotb.start_soon(env.clock.start())
    await env.reset_dut()

    await env.rx_source.write(b'7')
    await Timer(env.seconds_per_packet() * reset_point, unit='sec', round_mode='round')
    await env.reset_dut()
    env.rx_source._restart()
    env.tx_sink._restart()

    test_data = b'67'
    await env.rx_source.write(test_data)
    await env.rx_source.wait()
    await Timer(env.seconds_per_packet(), unit='sec', round_mode='round') # Wait for the last byte to be fully transmitted
    received_data = bytes(await env.tx_sink.read())
    assert received_data == test_data, f"Received data {received_data} does not match sent data {test_data}"