import cocotb
import random
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer
from cocotbext.axi import AxiStreamSource, AxiStreamMonitor, AxiStreamBus
from cocotbext.uart import UartSource, UartSink

class UARTEnv():
    def __init__(self, dut):
        self.dut = dut
        self.baud_rate = dut.BAUD_RATE
        self.clk_freq = dut.CLK_FREQ
        self.clock = Clock(dut.clk_i, 1 / dut.clk_freq.value.to_unsigned(), unit="sec")
        self.tx_source = AxiStreamSource(AxiStreamBus.from_prefix(dut, "s_axis_tx"), dut.clk_i, byte_size=8) # TODO: Investigate why it doesn't work with rst_i
        self.tx_sink = UartSink(dut.uart_tx_o, baud=dut.baud_rate.value.to_unsigned())
        self.rx_monitor = AxiStreamMonitor(AxiStreamBus.from_prefix(dut, "m_axis_rx"), dut.clk_i, dut.rst_i, byte_size=8)
        self.rx_source = UartSource(dut.uart_rx_i, baud=dut.baud_rate.value.to_unsigned())
        cocotb.log.info(f'UART Environment initialized with baud rate: {self.baud_rate.value.to_unsigned()} and clock frequency: {dut.CLK_FREQ.value.to_unsigned()}')

    async def reset_dut(self):
        self.dut.rst_i.value = 1
        await RisingEdge(self.dut.clk_i)
        self.dut.rst_i.value = 0
        cocotb.log.info('DUT Reset')

    def seconds_per_packet(self):
        bits_per_packet = 1 + 8 + 1  # Start bit + Data bits + Stop bit
        return bits_per_packet / self.baud_rate.value.to_unsigned()

    def clock_period(self):
        return 1 / self.clk_freq.value.to_unsigned()

@cocotb.test()
async def basic_rx(dut):
    env = UARTEnv(dut)
    cocotb.start_soon(env.clock.start())
    await env.reset_dut()

    test_data = b'Hello, UART!'
    await env.rx_source.write(test_data)
    await env.rx_source.wait()
    received_data = bytes(await env.rx_monitor.read())
    assert received_data == test_data, f"Received data {received_data} does not match sent data {test_data}"

@cocotb.test()
@cocotb.parametrize(reset_point=[1 / 1.5, 1 / 2, 1 / 3, 1 / 10])
async def reset_rx(dut, reset_point):
    env = UARTEnv(dut)
    cocotb.start_soon(env.clock.start())
    await env.reset_dut()

    await env.rx_source.write(b'X')
    await Timer(env.seconds_per_packet() * reset_point, unit='sec', round_mode='round')
    await env.reset_dut()
    env.rx_source._restart()
    env.rx_monitor.read_nowait()

    test_data = b'Hello, UART!'
    await env.rx_source.write(test_data)
    await env.rx_source.wait()
    received_data = bytes(await env.rx_monitor.read())
    assert received_data == test_data, f"Received data {received_data} does not match sent data {test_data}"

@cocotb.test()
async def random_delay_rx(dut):
    env = UARTEnv(dut)
    cocotb.start_soon(env.clock.start())
    await env.reset_dut()
    rng = random.Random(cocotb.RANDOM_SEED)

    test_data = b'Hello World! ' * 5
    for byte in test_data:
        await env.rx_source.write(bytes([byte]))
        await env.rx_source.wait()
        await Timer(rng.uniform(0, env.clock_period()), unit='sec', round_mode='round')

    received_data = bytes(await env.rx_monitor.read())
    assert received_data == test_data, f"Received data {received_data} does not match sent data {test_data}"

@cocotb.test()
async def basic_tx(dut):
    env = UARTEnv(dut)
    cocotb.start_soon(env.clock.start())
    await env.reset_dut()

    test_data = b'Hello, UART!'
    await env.tx_source.write(test_data)
    await env.tx_source.wait()
    await Timer(env.seconds_per_packet(), unit='sec', round_mode='round') # Wait for the last byte to be fully transmitted
    received_data = await env.tx_sink.read()
    assert received_data == test_data, f"Received data {received_data} does not match sent data {test_data}"

@cocotb.test()
async def reset_tx(dut):
    env = UARTEnv(dut)
    cocotb.start_soon(env.clock.start())
    await env.reset_dut()

    await env.tx_source.write(b'X')
    await env.reset_dut()
    env.tx_sink._restart()

    test_data = b'Hello, UART!'
    await env.tx_source.write(test_data)
    await env.tx_source.wait()
    await Timer(env.seconds_per_packet(), unit='sec', round_mode='round') # Wait for the last byte to be fully transmitted
    received_data = await env.tx_sink.read()
    assert received_data == test_data, f"Received data {received_data} does not match sent data {test_data}"

@cocotb.test()
async def random_delay_tx(dut):
    env = UARTEnv(dut)
    cocotb.start_soon(env.clock.start())
    await env.reset_dut()
    rng = random.Random(cocotb.RANDOM_SEED)

    test_data = b'Hello World! ' * 5
    for byte in test_data:
        await env.tx_source.write(bytes([byte]))
        await env.tx_source.wait()
        await Timer(rng.uniform(0, 10*env.seconds_per_packet()), unit='sec', round_mode='round')

    await Timer(env.seconds_per_packet(), unit='sec', round_mode='round') # Wait for the last byte to be fully transmitted
    received_data = await env.tx_sink.read()
    assert received_data == test_data, f"Received data {received_data} does not match sent data {test_data}"