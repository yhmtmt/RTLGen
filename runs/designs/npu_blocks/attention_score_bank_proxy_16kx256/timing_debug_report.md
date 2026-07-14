# OpenROAD Timing Debug Summary

- design_dir: `runs/designs/npu_blocks/attention_score_bank_proxy_16kx256`
- metrics_path: `runs/designs/npu_blocks/attention_score_bank_proxy_16kx256/metrics.csv`
- rows_considered: 2

## Metrics Rows

| param_hash | tag | status | critical_path_ns | density | result_path |
| --- | --- | --- | ---: | ---: | --- |
| a17d9d2f | attention_score_bank_proxy_v1_proxy_die_3000 | ok | 2.8162 | 0.4 | `/orfs/flow/reports/nangate45/attention_score_bank_proxy_16kx256/attention_score_bank_proxy_v1_proxy_die_3000/6_finish.rpt` |
| 76029cac | attention_score_bank_proxy_v1_proxy_die_2500 | ok | 5.3857 | 0.4 | `/orfs/flow/reports/nangate45/attention_score_bank_proxy_16kx256/attention_score_bank_proxy_v1_proxy_die_2500/6_finish.rpt` |

## Inspected Report Files

- `/orfs/flow/reports/nangate45/attention_score_bank_proxy_16kx256/attention_score_bank_proxy_v1_proxy_die_2500/6_finish.rpt`
- `/orfs/flow/reports/nangate45/attention_score_bank_proxy_16kx256/attention_score_bank_proxy_v1_proxy_die_3000/6_finish.rpt`
- `/orfs/flow/reports/nangate45/attention_score_bank_proxy_16kx256/attention_score_bank_proxy_v1_proxy_die_2500/5_global_route.rpt`
- `/orfs/flow/reports/nangate45/attention_score_bank_proxy_16kx256/attention_score_bank_proxy_v1_proxy_die_2500/5_route_drc.rpt`
- `/orfs/flow/reports/nangate45/attention_score_bank_proxy_16kx256/attention_score_bank_proxy_v1_proxy_die_3000/5_global_route.rpt`
- `/orfs/flow/reports/nangate45/attention_score_bank_proxy_16kx256/attention_score_bank_proxy_v1_proxy_die_3000/5_route_drc.rpt`
- `/orfs/flow/reports/nangate45/attention_score_bank_proxy_16kx256/attention_score_bank_proxy_v1_proxy_die_2500/4_cts_final.rpt`
- `/orfs/flow/reports/nangate45/attention_score_bank_proxy_16kx256/attention_score_bank_proxy_v1_proxy_die_3000/4_cts_final.rpt`
- `/orfs/flow/reports/nangate45/attention_score_bank_proxy_16kx256/attention_score_bank_proxy_v1_proxy_die_2500/3_resizer.rpt`
- `/orfs/flow/reports/nangate45/attention_score_bank_proxy_16kx256/attention_score_bank_proxy_v1_proxy_die_3000/3_resizer.rpt`
- `/orfs/flow/reports/nangate45/attention_score_bank_proxy_16kx256/attention_score_bank_proxy_v1_proxy_die_2500/3_detailed_place.rpt`
- `/orfs/flow/reports/nangate45/attention_score_bank_proxy_16kx256/attention_score_bank_proxy_v1_proxy_die_3000/3_detailed_place.rpt`
- `/orfs/flow/reports/nangate45/attention_score_bank_proxy_16kx256/attention_score_bank_proxy_v1_proxy_die_2500/3_global_place.rpt`
- `/orfs/flow/reports/nangate45/attention_score_bank_proxy_16kx256/attention_score_bank_proxy_v1_proxy_die_3000/3_global_place.rpt`
- `/orfs/flow/reports/nangate45/attention_score_bank_proxy_16kx256/attention_score_bank_proxy_v1_proxy_die_2500/2_floorplan_final.rpt`
- `/orfs/flow/reports/nangate45/attention_score_bank_proxy_16kx256/attention_score_bank_proxy_v1_proxy_die_3000/2_floorplan_final.rpt`
- `/orfs/flow/reports/nangate45/attention_score_bank_proxy_16kx256/attention_score_bank_proxy_v1_proxy_die_2500/drt_antennas.log`
- `/orfs/flow/reports/nangate45/attention_score_bank_proxy_16kx256/attention_score_bank_proxy_v1_proxy_die_2500/grt_antennas.log`
- `/orfs/flow/reports/nangate45/attention_score_bank_proxy_16kx256/attention_score_bank_proxy_v1_proxy_die_2500/metadata-generate.log`
- `/orfs/flow/reports/nangate45/attention_score_bank_proxy_16kx256/attention_score_bank_proxy_v1_proxy_die_3000/drt_antennas.log`
- `/orfs/flow/reports/nangate45/attention_score_bank_proxy_16kx256/attention_score_bank_proxy_v1_proxy_die_3000/grt_antennas.log`
- `/orfs/flow/reports/nangate45/attention_score_bank_proxy_16kx256/attention_score_bank_proxy_v1_proxy_die_3000/metadata-generate.log`

## Preferred Final-Stage Timing Paths

- raw_path_block_count: 104
- unique_path_block_count: 66
- preferred_stage: `finish`

### Path 1

- source: `/orfs/flow/reports/nangate45/attention_score_bank_proxy_16kx256/attention_score_bank_proxy_v1_proxy_die_3000/6_finish.rpt`
- stage: `finish`
- startpoint: `read_group_q[0]$_DFFE_PN0P_`
- endpoint: `rsp_group_q[0]$_DFF_PN0_`
- path_group: `clk`
- path_type: `min`
- slack: `0.1000`
- data_arrival_time: `0.8400`
- data_required_time: `0.7400`

```text
Startpoint: read_group_q[0]$_DFFE_PN0P_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: rsp_group_q[0]$_DFF_PN0_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   37.74    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.01    0.01    0.01 ^ wire26188/A (BUF_X8)
     1   55.86    0.01    0.03    0.04 ^ wire26188/Z (BUF_X8)
                                         net26187 (net)
                  0.03    0.02    0.06 ^ wire26187/A (BUF_X16)
     1   66.20    0.01    0.03    0.09 ^ wire26187/Z (BUF_X16)
                                         net26186 (net)
                  0.04    0.03    0.11 ^ wire26186/A (BUF_X32)
     1   64.46    0.01    0.02    0.14 ^ wire26186/Z (BUF_X32)
                                         net26185 (net)
                  0.03    0.03    0.16 ^ wire26185/A (BUF_X32)
     1   64.48    0.01    0.02    0.19 ^ wire26185/Z (BUF_X32)
...
                                         clknet_0_clk_regs (net)
                  0.01    0.00    0.68 ^ clkbuf_1_1__f_clk_regs/A (CLKBUF_X3)
     5   23.27    0.02    0.04    0.73 ^ clkbuf_1_1__f_clk_regs/Z (CLKBUF_X3)
                                         clknet_1_1__leaf_clk_regs (net)
                  0.02    0.01    0.73 ^ rsp_group_q[0]$_DFF_PN0_/CK (DFFR_X2)
                          0.00    0.73   clock reconvergence pessimism
                          0.01    0.74   library hold time
                                  0.74   data required time
-----------------------------------------------------------------------------
                                  0.74   data required time
                                 -0.84   data arrival time
-----------------------------------------------------------------------------
                                  0.10   slack (MET)



```

### Path 2

- source: `/orfs/flow/reports/nangate45/attention_score_bank_proxy_16kx256/attention_score_bank_proxy_v1_proxy_die_2500/6_finish.rpt`
- stage: `finish`
- startpoint: `read_group_q[0]$_DFFE_PN0P_`
- endpoint: `rsp_group_q[0]$_DFF_PN0_`
- path_group: `clk`
- path_type: `min`
- slack: `0.1100`
- data_arrival_time: `0.7200`
- data_required_time: `0.6100`

```text
Startpoint: read_group_q[0]$_DFFE_PN0P_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: rsp_group_q[0]$_DFF_PN0_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   54.13    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.02    0.02    0.02 ^ wire37299/A (BUF_X16)
     1   63.67    0.01    0.02    0.04 ^ wire37299/Z (BUF_X16)
                                         net37298 (net)
                  0.03    0.02    0.07 ^ wire37298/A (BUF_X16)
     1   72.17    0.01    0.03    0.09 ^ wire37298/Z (BUF_X16)
                                         net37297 (net)
                  0.05    0.04    0.13 ^ wire37297/A (BUF_X32)
     1   65.74    0.01    0.03    0.16 ^ wire37297/Z (BUF_X32)
                                         net37296 (net)
                  0.03    0.02    0.18 ^ wire37296/A (BUF_X32)
     2   25.58    0.01    0.02    0.20 ^ wire37296/Z (BUF_X32)
...
                                         clknet_0_clk_regs (net)
                  0.03    0.00    0.52 ^ clkbuf_1_1_0_clk_regs/A (CLKBUF_X3)
     5   45.71    0.03    0.06    0.57 ^ clkbuf_1_1_0_clk_regs/Z (CLKBUF_X3)
                                         clknet_1_1_0_clk_regs (net)
                  0.04    0.02    0.60 ^ rsp_group_q[0]$_DFF_PN0_/CK (DFFR_X2)
                          0.00    0.60   clock reconvergence pessimism
                          0.01    0.61   library hold time
                                  0.61   data required time
-----------------------------------------------------------------------------
                                  0.61   data required time
                                 -0.72   data arrival time
-----------------------------------------------------------------------------
                                  0.11   slack (MET)



```

### Path 3

- source: `/orfs/flow/reports/nangate45/attention_score_bank_proxy_16kx256/attention_score_bank_proxy_v1_proxy_die_3000/6_finish.rpt`
- stage: `finish`
- startpoint: `rst_n (input port clocked by clk)`
- endpoint: `rsp_valid_q$_DFF_PN0_ (removal check against rising-edge clock clk)`
- path_group: `asynchronous`
- path_type: `min`
- slack: `1.1500`
- data_arrival_time: `2.1400`
- data_required_time: `0.9900`

```text
Startpoint: rst_n (input port clocked by clk)
Endpoint: rsp_valid_q$_DFF_PN0_ (removal check against rising-edge clock clk)
Path Group: asynchronous
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (propagated)
                          2.00    2.00 ^ input external delay
     1   40.65    0.00    0.00    2.00 ^ rst_n (in)
                                         rst_n (net)
                  0.01    0.01    2.01 ^ wire17223/A (CLKBUF_X3)
     1   35.65    0.03    0.05    2.06 ^ wire17223/Z (CLKBUF_X3)
                                         net17222 (net)
                  0.03    0.01    2.08 ^ place22342/A (BUF_X1)
     3   18.61    0.04    0.07    2.14 ^ place22342/Z (BUF_X1)
                                         net22341 (net)
                  0.04    0.00    2.14 ^ rsp_valid_q$_DFF_PN0_/RN (DFFR_X1)
                                  2.14   data arrival time

                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   37.74    0.00    0.00    0.00 ^ clk (in)
...
                                         clk_regs (net)
                  0.01    0.00    0.65 ^ clkbuf_0_clk_regs/A (CLKBUF_X3)
     2   11.08    0.01    0.03    0.68 ^ clkbuf_0_clk_regs/Z (CLKBUF_X3)
                                         clknet_0_clk_regs (net)
                  0.01    0.00    0.68 ^ clkbuf_1_0__f_clk_regs/A (CLKBUF_X3)
     4   38.35    0.03    0.06    0.74 ^ clkbuf_1_0__f_clk_regs/Z (CLKBUF_X3)
                                         clknet_1_0__leaf_clk_regs (net)
                  0.03    0.01    0.75 ^ rsp_valid_q$_DFF_PN0_/CK (DFFR_X1)
                          0.00    0.75   clock reconvergence pessimism
                          0.24    0.99   library removal time
                                  0.99   data required time
-----------------------------------------------------------------------------
                                  0.99   data required time
                                 -2.14   data arrival time
-----------------------------------------------------------------------------
                                  1.15   slack (MET)
```

### Path 4

- source: `/orfs/flow/reports/nangate45/attention_score_bank_proxy_16kx256/attention_score_bank_proxy_v1_proxy_die_2500/6_finish.rpt`
- stage: `finish`
- startpoint: `rst_n (input port clocked by clk)`
- endpoint: `read_group_q[0]$_DFFE_PN0P_`
- path_group: `asynchronous`
- path_type: `min`
- slack: `1.3600`
- data_arrival_time: `2.2100`
- data_required_time: `0.8600`

```text
Startpoint: rst_n (input port clocked by clk)
Endpoint: read_group_q[0]$_DFFE_PN0P_
          (removal check against rising-edge clock clk)
Path Group: asynchronous
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (propagated)
                          2.00    2.00 ^ input external delay
     1   59.73    0.00    0.00    2.00 ^ rst_n (in)
                                         rst_n (net)
                  0.04    0.03    2.03 ^ wire20819/A (CLKBUF_X3)
     1   17.04    0.02    0.05    2.08 ^ wire20819/Z (CLKBUF_X3)
                                         net20818 (net)
                  0.02    0.01    2.09 ^ place28482/A (BUF_X2)
     2   22.31    0.03    0.04    2.13 ^ place28482/Z (BUF_X2)
                                         net28481 (net)
                  0.03    0.01    2.13 ^ place28486/A (BUF_X1)
     3   23.33    0.05    0.08    2.21 ^ place28486/Z (BUF_X1)
                                         net28485 (net)
                  0.05    0.00    2.21 ^ read_group_q[0]$_DFFE_PN0P_/RN (DFFR_X1)
                                  2.21   data arrival time
...
                                         clk_regs (net)
                  0.01    0.00    0.46 ^ clkbuf_0_clk_regs/A (CLKBUF_X3)
     2   32.57    0.03    0.05    0.51 ^ clkbuf_0_clk_regs/Z (CLKBUF_X3)
                                         clknet_0_clk_regs (net)
                  0.03    0.00    0.52 ^ clkbuf_1_1_0_clk_regs/A (CLKBUF_X3)
     5   45.71    0.03    0.06    0.57 ^ clkbuf_1_1_0_clk_regs/Z (CLKBUF_X3)
                                         clknet_1_1_0_clk_regs (net)
                  0.05    0.03    0.60 ^ read_group_q[0]$_DFFE_PN0P_/CK (DFFR_X1)
                          0.00    0.60   clock reconvergence pessimism
                          0.26    0.86   library removal time
                                  0.86   data required time
-----------------------------------------------------------------------------
                                  0.86   data required time
                                 -2.21   data arrival time
-----------------------------------------------------------------------------
                                  1.36   slack (MET)
```

### Path 5

- source: `/orfs/flow/reports/nangate45/attention_score_bank_proxy_16kx256/attention_score_bank_proxy_v1_proxy_die_2500/6_finish.rpt`
- stage: `finish`
- startpoint: `u_group_0_slice_2 (rising edge-triggered flip-flop clocked by clk)`
- endpoint: `rsp_rdata[98] (output port clocked by clk)`
- path_group: `clk`
- path_type: `max`
- slack: `2.6100`
- data_arrival_time: `5.3900`
- data_required_time: `8.0000`

```text
Startpoint: u_group_0_slice_2 (rising edge-triggered flip-flop clocked by clk)
Endpoint: rsp_rdata[98] (output port clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   54.13    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.02    0.02    0.02 ^ wire37299/A (BUF_X16)
     1   63.67    0.01    0.02    0.04 ^ wire37299/Z (BUF_X16)
                                         net37298 (net)
                  0.03    0.02    0.07 ^ wire37298/A (BUF_X16)
     1   72.17    0.01    0.03    0.09 ^ wire37298/Z (BUF_X16)
                                         net37297 (net)
                  0.05    0.04    0.13 ^ wire37297/A (BUF_X32)
     1   65.74    0.01    0.03    0.16 ^ wire37297/Z (BUF_X32)
                                         net37296 (net)
                  0.03    0.02    0.18 ^ wire37296/A (BUF_X32)
     2   25.58    0.01    0.02    0.20 ^ wire37296/Z (BUF_X32)
                                         net37295 (net)
                  0.01    0.00    0.21 ^ clkbuf_0_clk/A (CLKBUF_X3)
...
                  0.37    0.30    5.39 v rsp_rdata[98] (out)
                                  5.39   data arrival time

                         10.00   10.00   clock clk (rise edge)
                          0.00   10.00   clock network delay (propagated)
                          0.00   10.00   clock reconvergence pessimism
                         -2.00    8.00   output external delay
                                  8.00   data required time
-----------------------------------------------------------------------------
                                  8.00   data required time
                                 -5.39   data arrival time
-----------------------------------------------------------------------------
                                  2.61   slack (MET)



```

### Path 6

- source: `/orfs/flow/reports/nangate45/attention_score_bank_proxy_16kx256/attention_score_bank_proxy_v1_proxy_die_3000/6_finish.rpt`
- stage: `finish`
- startpoint: `rsp_group_q[2]$_DFF_PN0_`
- endpoint: `rsp_rdata[93] (output port clocked by clk)`
- path_group: `clk`
- path_type: `max`
- slack: `5.1800`
- data_arrival_time: `2.8200`
- data_required_time: `8.0000`

```text
Startpoint: rsp_group_q[2]$_DFF_PN0_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: rsp_rdata[93] (output port clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   37.74    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.01    0.01    0.01 ^ wire26188/A (BUF_X8)
     1   55.86    0.01    0.03    0.04 ^ wire26188/Z (BUF_X8)
                                         net26187 (net)
                  0.03    0.02    0.06 ^ wire26187/A (BUF_X16)
     1   66.20    0.01    0.03    0.09 ^ wire26187/Z (BUF_X16)
                                         net26186 (net)
                  0.04    0.03    0.11 ^ wire26186/A (BUF_X32)
     1   64.46    0.01    0.02    0.14 ^ wire26186/Z (BUF_X32)
                                         net26185 (net)
                  0.03    0.03    0.16 ^ wire26185/A (BUF_X32)
     1   64.48    0.01    0.02    0.19 ^ wire26185/Z (BUF_X32)
                                         net26184 (net)
...
                  0.07    0.01    2.82 ^ rsp_rdata[93] (out)
                                  2.82   data arrival time

                         10.00   10.00   clock clk (rise edge)
                          0.00   10.00   clock network delay (propagated)
                          0.00   10.00   clock reconvergence pessimism
                         -2.00    8.00   output external delay
                                  8.00   data required time
-----------------------------------------------------------------------------
                                  8.00   data required time
                                 -2.82   data arrival time
-----------------------------------------------------------------------------
                                  5.18   slack (MET)



```

### Path 7

- source: `/orfs/flow/reports/nangate45/attention_score_bank_proxy_16kx256/attention_score_bank_proxy_v1_proxy_die_2500/6_finish.rpt`
- stage: `finish`
- startpoint: `rst_n (input port clocked by clk)`
- endpoint: `read_pending_q$_DFF_PN0_`
- path_group: `asynchronous`
- path_type: `max`
- slack: `8.2500`
- data_arrival_time: `2.4300`
- data_required_time: `10.6800`

```text
Startpoint: rst_n (input port clocked by clk)
Endpoint: read_pending_q$_DFF_PN0_
          (recovery check against rising-edge clock clk)
Path Group: asynchronous
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (propagated)
                          2.00    2.00 ^ input external delay
     1   59.73    0.00    0.00    2.00 ^ rst_n (in)
                                         rst_n (net)
                  0.04    0.03    2.03 ^ wire20819/A (CLKBUF_X3)
     1   17.04    0.02    0.05    2.08 ^ wire20819/Z (CLKBUF_X3)
                                         net20818 (net)
                  0.02    0.01    2.09 ^ place28482/A (BUF_X2)
     2   22.31    0.03    0.04    2.13 ^ place28482/Z (BUF_X2)
                                         net28481 (net)
                  0.03    0.01    2.14 ^ place28483/A (BUF_X1)
     1   24.96    0.05    0.07    2.21 ^ place28483/Z (BUF_X1)
                                         net28482 (net)
                  0.06    0.02    2.23 ^ place28484/A (BUF_X1)
     2   44.75    0.09    0.11    2.34 ^ place28484/Z (BUF_X1)
...
                                         clk_regs (net)
                  0.01    0.00   10.46 ^ clkbuf_0_clk_regs/A (CLKBUF_X3)
     2   32.57    0.03    0.05   10.51 ^ clkbuf_0_clk_regs/Z (CLKBUF_X3)
                                         clknet_0_clk_regs (net)
                  0.03    0.00   10.52 ^ clkbuf_1_0_0_clk_regs/A (CLKBUF_X3)
     4   62.71    0.04    0.07   10.59 ^ clkbuf_1_0_0_clk_regs/Z (CLKBUF_X3)
                                         clknet_1_0_0_clk_regs (net)
                  0.05    0.03   10.61 ^ read_pending_q$_DFF_PN0_/CK (DFFR_X1)
                          0.00   10.61   clock reconvergence pessimism
                          0.07   10.68   library recovery time
                                 10.68   data required time
-----------------------------------------------------------------------------
                                 10.68   data required time
                                 -2.43   data arrival time
-----------------------------------------------------------------------------
                                  8.25   slack (MET)
```

### Path 8

- source: `/orfs/flow/reports/nangate45/attention_score_bank_proxy_16kx256/attention_score_bank_proxy_v1_proxy_die_3000/6_finish.rpt`
- stage: `finish`
- startpoint: `rst_n (input port clocked by clk)`
- endpoint: `read_group_q[1]$_DFFE_PN0P_`
- path_group: `asynchronous`
- path_type: `max`
- slack: `8.5600`
- data_arrival_time: `2.2400`
- data_required_time: `10.7900`

```text
Startpoint: rst_n (input port clocked by clk)
Endpoint: read_group_q[1]$_DFFE_PN0P_
          (recovery check against rising-edge clock clk)
Path Group: asynchronous
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (propagated)
                          2.00    2.00 ^ input external delay
     1   40.65    0.00    0.00    2.00 ^ rst_n (in)
                                         rst_n (net)
                  0.01    0.01    2.01 ^ wire17223/A (CLKBUF_X3)
     1   35.65    0.03    0.05    2.06 ^ wire17223/Z (CLKBUF_X3)
                                         net17222 (net)
                  0.03    0.01    2.08 ^ place22342/A (BUF_X1)
     3   18.61    0.04    0.07    2.14 ^ place22342/Z (BUF_X1)
                                         net22341 (net)
                  0.04    0.01    2.15 ^ place22343/A (BUF_X2)
     6   40.51    0.04    0.06    2.21 ^ place22343/Z (BUF_X2)
                                         net22342 (net)
                  0.05    0.03    2.24 ^ read_group_q[1]$_DFFE_PN0P_/RN (DFFR_X1)
                                  2.24   data arrival time
...
                                         clk_regs (net)
                  0.01    0.00   10.65 ^ clkbuf_0_clk_regs/A (CLKBUF_X3)
     2   11.08    0.01    0.03   10.68 ^ clkbuf_0_clk_regs/Z (CLKBUF_X3)
                                         clknet_0_clk_regs (net)
                  0.01    0.00   10.68 ^ clkbuf_1_1__f_clk_regs/A (CLKBUF_X3)
     5   23.27    0.02    0.04   10.73 ^ clkbuf_1_1__f_clk_regs/Z (CLKBUF_X3)
                                         clknet_1_1__leaf_clk_regs (net)
                  0.02    0.01   10.74 ^ read_group_q[1]$_DFFE_PN0P_/CK (DFFR_X1)
                          0.00   10.74   clock reconvergence pessimism
                          0.06   10.79   library recovery time
                                 10.79   data required time
-----------------------------------------------------------------------------
                                 10.79   data required time
                                 -2.24   data arrival time
-----------------------------------------------------------------------------
                                  8.56   slack (MET)
```


## Worst Timing Paths Across All Stages

### Path 1

- source: `/orfs/flow/reports/nangate45/attention_score_bank_proxy_16kx256/attention_score_bank_proxy_v1_proxy_die_2500/2_floorplan_final.rpt`
- stage: `floorplan`
- startpoint: `read_pending_q$_DFF_PN0_`
- endpoint: `rsp_valid_q$_DFF_PN0_ (rising edge-triggered flip-flop clocked by clk)`
- path_group: `clk`
- path_type: `min`
- slack: `0.0800`
- data_arrival_time: `0.0800`
- data_required_time: `0.0000`

```text
Startpoint: read_pending_q$_DFF_PN0_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: rsp_valid_q$_DFF_PN0_ (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                  0.00    0.00    0.00 ^ read_pending_q$_DFF_PN0_/CK (DFFR_X1)
     1    1.05    0.01    0.08    0.08 v read_pending_q$_DFF_PN0_/Q (DFFR_X1)
                                         read_pending_q (net)
                  0.01    0.00    0.08 v rsp_valid_q$_DFF_PN0_/D (DFFR_X1)
                                  0.08   data arrival time

                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                          0.00    0.00   clock reconvergence pessimism
                                  0.00 ^ rsp_valid_q$_DFF_PN0_/CK (DFFR_X1)
                          0.00    0.00   library hold time
                                  0.00   data required time
-----------------------------------------------------------------------------
                                  0.00   data required time
                                 -0.08   data arrival time
-----------------------------------------------------------------------------
                                  0.08   slack (MET)



```

### Path 2

- source: `/orfs/flow/reports/nangate45/attention_score_bank_proxy_16kx256/attention_score_bank_proxy_v1_proxy_die_3000/2_floorplan_final.rpt`
- stage: `floorplan`
- startpoint: `read_pending_q$_DFF_PN0_`
- endpoint: `rsp_valid_q$_DFF_PN0_ (rising edge-triggered flip-flop clocked by clk)`
- path_group: `clk`
- path_type: `min`
- slack: `0.0800`
- data_arrival_time: `0.0800`
- data_required_time: `0.0000`

```text
Startpoint: read_pending_q$_DFF_PN0_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: rsp_valid_q$_DFF_PN0_ (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                  0.00    0.00    0.00 ^ read_pending_q$_DFF_PN0_/CK (DFFR_X1)
     1    1.05    0.01    0.08    0.08 v read_pending_q$_DFF_PN0_/Q (DFFR_X1)
                                         read_pending_q (net)
                  0.01    0.00    0.08 v rsp_valid_q$_DFF_PN0_/D (DFFR_X1)
                                  0.08   data arrival time

                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                          0.00    0.00   clock reconvergence pessimism
                                  0.00 ^ rsp_valid_q$_DFF_PN0_/CK (DFFR_X1)
                          0.00    0.00   library hold time
                                  0.00   data required time
-----------------------------------------------------------------------------
                                  0.00   data required time
                                 -0.08   data arrival time
-----------------------------------------------------------------------------
                                  0.08   slack (MET)



```

### Path 3

- source: `/orfs/flow/reports/nangate45/attention_score_bank_proxy_16kx256/attention_score_bank_proxy_v1_proxy_die_3000/3_detailed_place.rpt`
- stage: `detailed_place`
- startpoint: `read_group_q[0]$_DFFE_PN0P_`
- endpoint: `rsp_group_q[0]$_DFF_PN0_`
- path_group: `clk`
- path_type: `min`
- slack: `0.0900`
- data_arrival_time: `0.1000`
- data_required_time: `0.0000`

```text
Startpoint: read_group_q[0]$_DFFE_PN0P_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: rsp_group_q[0]$_DFF_PN0_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                  0.00    0.00    0.00 ^ read_group_q[0]$_DFFE_PN0P_/CK (DFFR_X1)
     2    9.22    0.01    0.10    0.10 v read_group_q[0]$_DFFE_PN0P_/Q (DFFR_X1)
                                         read_group_q[0] (net)
                  0.01    0.00    0.10 v rsp_group_q[0]$_DFF_PN0_/D (DFFR_X2)
                                  0.10   data arrival time

                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                          0.00    0.00   clock reconvergence pessimism
                                  0.00 ^ rsp_group_q[0]$_DFF_PN0_/CK (DFFR_X2)
                          0.00    0.00   library hold time
                                  0.00   data required time
-----------------------------------------------------------------------------
                                  0.00   data required time
                                 -0.10   data arrival time
-----------------------------------------------------------------------------
                                  0.09   slack (MET)



```

### Path 4

- source: `/orfs/flow/reports/nangate45/attention_score_bank_proxy_16kx256/attention_score_bank_proxy_v1_proxy_die_2500/3_detailed_place.rpt`
- stage: `detailed_place`
- startpoint: `read_group_q[0]$_DFFE_PN0P_`
- endpoint: `rsp_group_q[0]$_DFF_PN0_`
- path_group: `clk`
- path_type: `min`
- slack: `0.1000`
- data_arrival_time: `0.1000`
- data_required_time: `0.0000`

```text
Startpoint: read_group_q[0]$_DFFE_PN0P_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: rsp_group_q[0]$_DFF_PN0_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                  0.00    0.00    0.00 ^ read_group_q[0]$_DFFE_PN0P_/CK (DFFR_X1)
     2   14.81    0.02    0.10    0.10 v read_group_q[0]$_DFFE_PN0P_/Q (DFFR_X1)
                                         read_group_q[0] (net)
                  0.02    0.00    0.10 v rsp_group_q[0]$_DFF_PN0_/D (DFFR_X2)
                                  0.10   data arrival time

                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                          0.00    0.00   clock reconvergence pessimism
                                  0.00 ^ rsp_group_q[0]$_DFF_PN0_/CK (DFFR_X2)
                          0.00    0.00   library hold time
                                  0.00   data required time
-----------------------------------------------------------------------------
                                  0.00   data required time
                                 -0.10   data arrival time
-----------------------------------------------------------------------------
                                  0.10   slack (MET)



```

### Path 5

- source: `/orfs/flow/reports/nangate45/attention_score_bank_proxy_16kx256/attention_score_bank_proxy_v1_proxy_die_2500/3_global_place.rpt`
- stage: `global_place`
- startpoint: `read_group_q[0]$_DFFE_PN0P_`
- endpoint: `rsp_group_q[0]$_DFF_PN0_`
- path_group: `clk`
- path_type: `min`
- slack: `0.1000`
- data_arrival_time: `0.1100`
- data_required_time: `0.0000`

```text
Startpoint: read_group_q[0]$_DFFE_PN0P_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: rsp_group_q[0]$_DFF_PN0_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                  0.00    0.00    0.00 ^ read_group_q[0]$_DFFE_PN0P_/CK (DFFR_X1)
     2   15.36    0.02    0.10    0.10 v read_group_q[0]$_DFFE_PN0P_/Q (DFFR_X1)
                                         read_group_q[0] (net)
                  0.02    0.00    0.11 v rsp_group_q[0]$_DFF_PN0_/D (DFFR_X2)
                                  0.11   data arrival time

                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                          0.00    0.00   clock reconvergence pessimism
                                  0.00 ^ rsp_group_q[0]$_DFF_PN0_/CK (DFFR_X2)
                          0.00    0.00   library hold time
                                  0.00   data required time
-----------------------------------------------------------------------------
                                  0.00   data required time
                                 -0.11   data arrival time
-----------------------------------------------------------------------------
                                  0.10   slack (MET)



```

### Path 6

- source: `/orfs/flow/reports/nangate45/attention_score_bank_proxy_16kx256/attention_score_bank_proxy_v1_proxy_die_2500/3_resizer.rpt`
- stage: `resizer`
- startpoint: `read_group_q[0]$_DFFE_PN0P_`
- endpoint: `rsp_group_q[0]$_DFF_PN0_`
- path_group: `clk`
- path_type: `min`
- slack: `0.1000`
- data_arrival_time: `0.1100`
- data_required_time: `0.0000`

```text
Startpoint: read_group_q[0]$_DFFE_PN0P_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: rsp_group_q[0]$_DFF_PN0_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                  0.00    0.00    0.00 ^ read_group_q[0]$_DFFE_PN0P_/CK (DFFR_X1)
     2   15.36    0.02    0.10    0.10 v read_group_q[0]$_DFFE_PN0P_/Q (DFFR_X1)
                                         read_group_q[0] (net)
                  0.02    0.00    0.11 v rsp_group_q[0]$_DFF_PN0_/D (DFFR_X2)
                                  0.11   data arrival time

                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                          0.00    0.00   clock reconvergence pessimism
                                  0.00 ^ rsp_group_q[0]$_DFF_PN0_/CK (DFFR_X2)
                          0.00    0.00   library hold time
                                  0.00   data required time
-----------------------------------------------------------------------------
                                  0.00   data required time
                                 -0.11   data arrival time
-----------------------------------------------------------------------------
                                  0.10   slack (MET)



```

### Path 7

- source: `/orfs/flow/reports/nangate45/attention_score_bank_proxy_16kx256/attention_score_bank_proxy_v1_proxy_die_3000/3_global_place.rpt`
- stage: `global_place`
- startpoint: `read_group_q[0]$_DFFE_PN0P_`
- endpoint: `rsp_group_q[0]$_DFF_PN0_`
- path_group: `clk`
- path_type: `min`
- slack: `0.1000`
- data_arrival_time: `0.1000`
- data_required_time: `0.0000`

```text
Startpoint: read_group_q[0]$_DFFE_PN0P_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: rsp_group_q[0]$_DFF_PN0_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                  0.00    0.00    0.00 ^ read_group_q[0]$_DFFE_PN0P_/CK (DFFR_X1)
     2   10.72    0.01    0.10    0.10 v read_group_q[0]$_DFFE_PN0P_/Q (DFFR_X1)
                                         read_group_q[0] (net)
                  0.01    0.00    0.10 v rsp_group_q[0]$_DFF_PN0_/D (DFFR_X2)
                                  0.10   data arrival time

                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                          0.00    0.00   clock reconvergence pessimism
                                  0.00 ^ rsp_group_q[0]$_DFF_PN0_/CK (DFFR_X2)
                          0.00    0.00   library hold time
                                  0.00   data required time
-----------------------------------------------------------------------------
                                  0.00   data required time
                                 -0.10   data arrival time
-----------------------------------------------------------------------------
                                  0.10   slack (MET)



```

### Path 8

- source: `/orfs/flow/reports/nangate45/attention_score_bank_proxy_16kx256/attention_score_bank_proxy_v1_proxy_die_3000/3_resizer.rpt`
- stage: `resizer`
- startpoint: `read_group_q[0]$_DFFE_PN0P_`
- endpoint: `rsp_group_q[0]$_DFF_PN0_`
- path_group: `clk`
- path_type: `min`
- slack: `0.1000`
- data_arrival_time: `0.1000`
- data_required_time: `0.0000`

```text
Startpoint: read_group_q[0]$_DFFE_PN0P_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: rsp_group_q[0]$_DFF_PN0_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                  0.00    0.00    0.00 ^ read_group_q[0]$_DFFE_PN0P_/CK (DFFR_X1)
     2   10.72    0.01    0.10    0.10 v read_group_q[0]$_DFFE_PN0P_/Q (DFFR_X1)
                                         read_group_q[0] (net)
                  0.01    0.00    0.10 v rsp_group_q[0]$_DFF_PN0_/D (DFFR_X2)
                                  0.10   data arrival time

                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                          0.00    0.00   clock reconvergence pessimism
                                  0.00 ^ rsp_group_q[0]$_DFF_PN0_/CK (DFFR_X2)
                          0.00    0.00   library hold time
                                  0.00   data required time
-----------------------------------------------------------------------------
                                  0.00   data required time
                                 -0.10   data arrival time
-----------------------------------------------------------------------------
                                  0.10   slack (MET)



```
