set clock_port "clk"
set clock_period 8.0
set input_delay 2.0
set output_delay 2.0

create_clock [get_ports $clock_port] -period $clock_period

set_input_delay $input_delay -clock $clock_port [all_inputs]
set_output_delay $output_delay -clock $clock_port [all_outputs]

set_load -pin_load 0.05 [all_outputs]
