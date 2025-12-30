-- AXI4-Stream UART TX/RX

-- Copyright (c) 2025, Dimitrios Alexopoulos All rights reserved.
library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;
use ieee.math_real.all;

entity uart is
    generic (
        BAUD_RATE : positive;
        CLK_FREQ  : positive
    );
    port (
        clk_i            : in  std_logic;
        rst_i            : in  std_logic;
        uart_tx_o        : out std_logic;
        uart_rx_i        : in  std_logic;
        m_axis_rx_tdata  : out std_logic_vector(7 downto 0);
        m_axis_rx_tvalid : out std_logic;
        s_axis_tx_tdata  : in  std_logic_vector(7 downto 0);
        s_axis_tx_tvalid : in  std_logic;
        s_axis_tx_tready : out std_logic
    );
end uart;

architecture rtl of uart is
    constant CLK_PER_BIT       : positive := CLK_FREQ / BAUD_RATE; -- Clock cycles per bit of the packet
    constant CLK_PER_BIT_WIDTH : positive := integer(ceil(log2(real(CLK_PER_BIT))));
    constant NUM_BITS          : positive := 10; -- Number of bits in packet

    type uart_state_t is (IDLE, START_B, DATA, STOP_B);

    signal uart_rx_q1 : std_logic := '1';
    signal uart_rx_q2 : std_logic := '1';

    signal rx_valid    : std_logic := '0';
    signal rx_sr_en    : boolean;
    signal rx_sr       : std_logic_vector(7 downto 0);
    signal rx_state    : uart_state_t := IDLE;
    signal rx_clk_cnt  : unsigned(CLK_PER_BIT_WIDTH-1 downto 0) := to_unsigned(0, CLK_PER_BIT_WIDTH);
    signal rx_data_cnt : unsigned(2 downto 0) := to_unsigned(0, 3);

    signal tx_ready    : std_logic := '1';
    signal tx_sr_en    : boolean;
    signal tx_sr       : std_logic_vector(7 downto 0);
    signal tx_state    : uart_state_t := IDLE;
    signal tx_clk_cnt  : unsigned(CLK_PER_BIT_WIDTH-1 downto 0) := to_unsigned(0, CLK_PER_BIT_WIDTH);
    signal tx_data_cnt : unsigned(2 downto 0) := to_unsigned(0, 3);

    attribute syn_preserve : integer;
    attribute syn_preserve of uart_rx_q1 : signal is 1;
    attribute syn_preserve of uart_rx_q2 : signal is 1;
begin
    assert CLK_FREQ > (BAUD_RATE * 4) -- TODO: Check if this constraint should be tightened, i.e. a higher multiple of the
    -- CLK_FREQUENCY, we should add some constraint about multiples and such as well as how much "gap" we can have
        report "The clock frequency must be at least four times the baud rate"
        severity failure;

    -- UART TX
    process(clk_i)
    begin
        if rising_edge(clk_i) then
            if rst_i = '1' then
                tx_state <= IDLE;
                tx_ready <= '1';
                tx_clk_cnt <= to_unsigned(0, CLK_PER_BIT_WIDTH);
                tx_data_cnt <= to_unsigned(0, 3);
            else
                case(tx_state) is
                    when IDLE =>
                        if s_axis_tx_tvalid = '1' then
                            tx_state <= START_B;
                            tx_ready <= '0';
                        end if;
                    when START_B =>
                        if tx_clk_cnt = CLK_PER_BIT-1 then
                            tx_state <= DATA;
                            tx_clk_cnt <= to_unsigned(0, CLK_PER_BIT_WIDTH);
                        else
                            tx_clk_cnt <= tx_clk_cnt + 1;
                        end if;
                    when DATA =>
                        if tx_data_cnt = 7 and tx_clk_cnt = CLK_PER_BIT-1 then
                            tx_state <= STOP_B;
                            tx_clk_cnt <= to_unsigned(0, CLK_PER_BIT_WIDTH);
                            tx_data_cnt <= to_unsigned(0, 3);
                        elsif tx_clk_cnt = CLK_PER_BIT-1 then
                            tx_clk_cnt <= to_unsigned(0, CLK_PER_BIT_WIDTH);
                            tx_data_cnt <= tx_data_cnt + 1;
                        else
                            tx_clk_cnt <= tx_clk_cnt + 1;
                        end if;
                    when STOP_B =>
                        if tx_clk_cnt = CLK_PER_BIT-1 then
                            tx_state <= IDLE;
                            tx_ready <= '1';
                            tx_clk_cnt <= to_unsigned(0, CLK_PER_BIT_WIDTH);
                        else
                            tx_clk_cnt <= tx_clk_cnt + 1;
                        end if;
                end case;
            end if;
        end if;
    end process;

    process(tx_state, tx_sr)
    begin
        case(tx_state) is
            when START_B =>
                uart_tx_o <= '0';
            when DATA =>
                uart_tx_o <= tx_sr(0);
            when STOP_B =>
                uart_tx_o <= '1';
            when others =>
                uart_tx_o <= '1';
        end case;
    end process;

    s_axis_tx_tready <= tx_ready;

    -- UART RX
    -- INFO: In the current scheme if we are slower (thus less CLK per bit its mostly okay, but if we are slower, it's not)
    -- we should write some constraints to characterize this and emit a warning
    process(clk_i)
    begin
        if rising_edge(clk_i) then
            uart_rx_q1 <= uart_rx_i;
            uart_rx_q2 <= uart_rx_q1;
        end if;
    end process;

    process(clk_i)
    begin
        if rising_edge(clk_i) then
            if rst_i = '1' then
                rx_state <= IDLE;
                rx_valid <= '0';
                rx_clk_cnt <= to_unsigned(0, CLK_PER_BIT_WIDTH);
                rx_data_cnt <= to_unsigned(0, 3);
            else
                case(rx_state) is
                    when IDLE =>
                        if uart_rx_q2 = '0' then
                            rx_state <= START_B;
                        end if;
                        rx_valid <= '0';
                    when START_B =>
                        if rx_clk_cnt = CLK_PER_BIT-1 then
                            rx_state <= DATA;
                            rx_clk_cnt <= to_unsigned(0, CLK_PER_BIT_WIDTH);
                        else
                            rx_clk_cnt <= rx_clk_cnt + 1;
                        end if;
                    when DATA =>
                        if rx_data_cnt = 7 and rx_clk_cnt = CLK_PER_BIT-1 then
                            rx_state <= STOP_B;
                            rx_clk_cnt <= to_unsigned(0, CLK_PER_BIT_WIDTH);
                            rx_data_cnt <= to_unsigned(0, 3);
                        elsif rx_clk_cnt = CLK_PER_BIT-1 then
                            rx_clk_cnt <= to_unsigned(0, CLK_PER_BIT_WIDTH);
                            rx_data_cnt <= rx_data_cnt + 1;
                        else
                            rx_clk_cnt <= rx_clk_cnt + 1;
                        end if;
                    when STOP_B => -- TODO: Add a proper stop bit check (sample in the middle)
                        if uart_rx_q2 = '1' then
                            rx_valid <= '1';
                            rx_state <= IDLE;
                        end if;
                end case;
            end if;
        end if;
    end process;

    tx_sr_en <= tx_clk_cnt = CLK_PER_BIT-1 and tx_state = DATA;
    rx_sr_en <= rx_clk_cnt = CLK_PER_BIT/2 and rx_state = DATA;

    process(clk_i)
    begin
        if rising_edge(clk_i) then
            if tx_sr_en then
                for i in 7 downto 1 loop
                    tx_sr(i - 1) <= tx_sr(i);
                end loop;
            elsif tx_state = IDLE and s_axis_tx_tvalid = '1' then
                tx_sr <= s_axis_tx_tdata;
            end if;
            if rx_sr_en then
                rx_sr(7) <= uart_rx_q2;
                for i in 7 downto 1 loop
                    rx_sr(i - 1) <= rx_sr(i);
                end loop;
            end if;
        end if;
    end process;

    m_axis_rx_tdata <= rx_sr;
    m_axis_rx_tvalid <= rx_valid;

end rtl;
