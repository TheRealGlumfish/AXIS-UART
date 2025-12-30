//Copyright (C)2014-2025 GOWIN Semiconductor Corporation.
//All rights reserved.
//File Title: Timing Constraints file
//Tool Version: V1.9.12 
//Created Time: 2025-12-29 23:51:00
create_clock -name clk_27 -period 37.037 -waveform {0 18.518} [get_ports {clk}]
set_false_path -from [get_ports {uart_rx}] 
