library ieee;
use ieee.std_logic_1164.all;

entity top is
    port (
       clk     : in  std_logic;
       rst_n   : in  std_logic;
       uart_tx : out std_logic;
       uart_rx : in  std_logic
   );
end top;

architecture rtl of top is
    constant BAUD_RATE : positive := 250000;
    constant CLK_FREQ  : positive := 27000000;
    
    signal tdata  : std_logic_vector(7 downto 0);
    signal tvalid : std_logic;
    signal tready : std_logic;
    signal tx_data  : std_logic_vector(7 downto 0);
    signal rst : std_logic;
    signal buff_tdata : std_logic_vector(7 downto 0);
    signal buff_tvalid : std_logic := '0';
begin
    -- Loopback connection
    tx_data <= tdata when tdata = "00110110" or tdata = "00110111" else "00000111";
    rst <= not rst_n; 

    -- Buffer
    process(clk)
    begin
        if rising_edge(clk) then
            if rst_n = '0' then
                buff_tvalid <= '0';
            else
                if tvalid = '1' then
                    buff_tdata <= tx_data;
                    buff_tvalid <= '1';
                else
                    if tready = '1' then
                        buff_tvalid <= '0';
                    end if;
                end if;
            end if;
        end if;
    end process;

    UART : entity work.uart
        generic map (
            BAUD_RATE => BAUD_RATE,
            CLK_FREQ => CLK_FREQ
        )
        port map (
            clk_i            => clk,
            rst_i            => rst,
            uart_tx_o        => uart_tx,
            uart_rx_i        => uart_rx,
            m_axis_rx_tdata  => tdata,
            m_axis_rx_tvalid => tvalid,
            s_axis_tx_tdata  => buff_tdata,
            s_axis_tx_tvalid => buff_tvalid,
            s_axis_tx_tready => tready
        );
end rtl;
