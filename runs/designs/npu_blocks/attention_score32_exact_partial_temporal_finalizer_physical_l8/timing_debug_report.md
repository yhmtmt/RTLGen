# OpenROAD Timing Debug Summary

- design_dir: `runs/designs/npu_blocks/attention_score32_exact_partial_temporal_finalizer_physical_l8`
- metrics_path: `runs/designs/npu_blocks/attention_score32_exact_partial_temporal_finalizer_physical_l8/metrics.csv`
- rows_considered: 1

## Metrics Rows

| param_hash | tag | status | critical_path_ns | density | result_path |
| --- | --- | --- | ---: | ---: | --- |
| 7d5d9129 | attention_exact_partial_temporal_finalizer_12ns_v1_7d5d9129 | ok | 11.8194 | 0.4 | `/orfs/flow/reports/nangate45/attention_score32_exact_partial_temporal_finalizer_physical_l8/base/6_finish.rpt` |

## Inspected Report Files

- `/orfs/flow/reports/nangate45/attention_score32_exact_partial_temporal_finalizer_physical_l8/base/6_finish.rpt`
- `/orfs/flow/reports/nangate45/attention_score32_exact_partial_temporal_finalizer_physical_l8/base/5_global_route.rpt`
- `/orfs/flow/reports/nangate45/attention_score32_exact_partial_temporal_finalizer_physical_l8/base/5_route_drc.rpt`
- `/orfs/flow/reports/nangate45/attention_score32_exact_partial_temporal_finalizer_physical_l8/base/5_route_drc.rpt-5.rpt`
- `/orfs/flow/reports/nangate45/attention_score32_exact_partial_temporal_finalizer_physical_l8/base/4_cts_final.rpt`
- `/orfs/flow/reports/nangate45/attention_score32_exact_partial_temporal_finalizer_physical_l8/base/3_resizer.rpt`
- `/orfs/flow/reports/nangate45/attention_score32_exact_partial_temporal_finalizer_physical_l8/base/3_detailed_place.rpt`
- `/orfs/flow/reports/nangate45/attention_score32_exact_partial_temporal_finalizer_physical_l8/base/3_global_place.rpt`
- `/orfs/flow/reports/nangate45/attention_score32_exact_partial_temporal_finalizer_physical_l8/base/2_floorplan_final.rpt`
- `/orfs/flow/reports/nangate45/attention_score32_exact_partial_temporal_finalizer_physical_l8/base/drt_antennas.log`
- `/orfs/flow/reports/nangate45/attention_score32_exact_partial_temporal_finalizer_physical_l8/base/grt_antennas.log`
- `/orfs/flow/reports/nangate45/attention_score32_exact_partial_temporal_finalizer_physical_l8/base/metadata-generate.log`

## Preferred Final-Stage Timing Paths

- raw_path_block_count: 52
- unique_path_block_count: 28
- preferred_stage: `finish`

### Path 1

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_partial_temporal_finalizer_physical_l8/base/6_finish.rpt`
- stage: `finish`
- startpoint: `u_finalizer/cycle_count[0]$_DFF_PN0_`
- endpoint: `u_finalizer/cycle_count[0]$_DFF_PN0_`
- path_group: `clk`
- path_type: `min`
- slack: `0.0600`
- data_arrival_time: `0.6600`
- data_required_time: `0.6000`

```text
Startpoint: u_finalizer/cycle_count[0]$_DFF_PN0_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: u_finalizer/cycle_count[0]$_DFF_PN0_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   12.49    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.00    0.00    0.00 ^ wire27892/A (BUF_X8)
     1   52.78    0.01    0.02    0.02 ^ wire27892/Z (BUF_X8)
                                         net27891 (net)
                  0.03    0.02    0.05 ^ wire27891/A (BUF_X16)
     1   55.88    0.01    0.03    0.07 ^ wire27891/Z (BUF_X16)
                                         net27890 (net)
                  0.03    0.02    0.10 ^ wire27890/A (BUF_X16)
     2   18.87    0.01    0.03    0.12 ^ wire27890/Z (BUF_X16)
                                         net27889 (net)
                  0.01    0.00    0.13 ^ clkbuf_regs_0_clk/A (CLKBUF_X3)
     1    1.85    0.01    0.03    0.15 ^ clkbuf_regs_0_clk/Z (CLKBUF_X3)
...
                                         clknet_7_110__leaf_clk_regs (net)
                  0.02    0.00    0.55 ^ clkbuf_leaf_732_clk_regs/A (CLKBUF_X3)
     6    8.05    0.01    0.04    0.59 ^ clkbuf_leaf_732_clk_regs/Z (CLKBUF_X3)
                                         clknet_leaf_732_clk_regs (net)
                  0.01    0.00    0.59 ^ u_finalizer/cycle_count[0]$_DFF_PN0_/CK (DFFR_X1)
                          0.00    0.59   clock reconvergence pessimism
                          0.01    0.60   library hold time
                                  0.60   data required time
-----------------------------------------------------------------------------
                                  0.60   data required time
                                 -0.66   data arrival time
-----------------------------------------------------------------------------
                                  0.06   slack (MET)



```

### Path 2

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_partial_temporal_finalizer_physical_l8/base/6_finish.rpt`
- stage: `finish`
- startpoint: `u_temporal/u_pair_merge/left_global_max_hold_q[31]$_DFFE_PN0P_`
- endpoint: `u_temporal/u_state_memory/protocol_error_q$_DFF_PN0_`
- path_group: `clk`
- path_type: `max`
- slack: `0.7900`
- data_arrival_time: `11.8200`
- data_required_time: `12.6100`

```text
Startpoint: u_temporal/u_pair_merge/left_global_max_hold_q[31]$_DFFE_PN0P_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: u_temporal/u_state_memory/protocol_error_q$_DFF_PN0_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   12.49    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.00    0.00    0.00 ^ wire27892/A (BUF_X8)
     1   52.78    0.01    0.02    0.02 ^ wire27892/Z (BUF_X8)
                                         net27891 (net)
                  0.03    0.02    0.05 ^ wire27891/A (BUF_X16)
     1   55.88    0.01    0.03    0.07 ^ wire27891/Z (BUF_X16)
                                         net27890 (net)
                  0.03    0.02    0.10 ^ wire27890/A (BUF_X16)
     2   18.87    0.01    0.03    0.12 ^ wire27890/Z (BUF_X16)
                                         net27889 (net)
                  0.01    0.00    0.13 ^ clkbuf_regs_0_clk/A (CLKBUF_X3)
     1    1.85    0.01    0.03    0.15 ^ clkbuf_regs_0_clk/Z (CLKBUF_X3)
...
                                         clknet_7_65__leaf_clk_regs (net)
                  0.04    0.00   12.61 ^ clkbuf_leaf_1232_clk_regs/A (CLKBUF_X3)
     8   10.65    0.01    0.05   12.65 ^ clkbuf_leaf_1232_clk_regs/Z (CLKBUF_X3)
                                         clknet_leaf_1232_clk_regs (net)
                  0.01    0.00   12.65 ^ u_temporal/u_state_memory/protocol_error_q$_DFF_PN0_/CK (DFFR_X2)
                          0.00   12.65   clock reconvergence pessimism
                         -0.04   12.61   library setup time
                                 12.61   data required time
-----------------------------------------------------------------------------
                                 12.61   data required time
                                -11.82   data arrival time
-----------------------------------------------------------------------------
                                  0.79   slack (MET)



```

### Path 3

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_partial_temporal_finalizer_physical_l8/base/6_finish.rpt`
- stage: `finish`
- startpoint: `rst_n (input port clocked by clk)`
- endpoint: `u_finalizer/cycle_count[29]$_DFF_PN0_`
- path_group: `asynchronous`
- path_type: `min`
- slack: `1.3200`
- data_arrival_time: `2.1300`
- data_required_time: `0.8100`

```text
Startpoint: rst_n (input port clocked by clk)
Endpoint: u_finalizer/cycle_count[29]$_DFF_PN0_
          (removal check against rising-edge clock clk)
Path Group: asynchronous
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (propagated)
                          2.00    2.00 ^ input external delay
     1    6.53    0.00    0.00    2.00 ^ rst_n (in)
                                         rst_n (net)
                  0.00    0.00    2.00 ^ input4277/A (CLKBUF_X3)
     2   35.17    0.02    0.04    2.04 ^ input4277/Z (CLKBUF_X3)
                                         net4276 (net)
                  0.04    0.03    2.07 ^ place27322/A (BUF_X2)
     3   22.54    0.02    0.05    2.11 ^ place27322/Z (BUF_X2)
                                         net27321 (net)
                  0.03    0.01    2.13 ^ u_finalizer/cycle_count[29]$_DFF_PN0_/RN (DFFR_X1)
                                  2.13   data arrival time

                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
...
                                         clknet_5_27_0_clk_regs (net)
                  0.02    0.00    0.51 ^ clkbuf_7_109__f_clk_regs/A (CLKBUF_X3)
     5   13.52    0.01    0.04    0.55 ^ clkbuf_7_109__f_clk_regs/Z (CLKBUF_X3)
                                         clknet_7_109__leaf_clk_regs (net)
                  0.01    0.00    0.55 ^ clkbuf_leaf_720_clk_regs/A (CLKBUF_X3)
     4    7.55    0.01    0.04    0.59 ^ clkbuf_leaf_720_clk_regs/Z (CLKBUF_X3)
                                         clknet_leaf_720_clk_regs (net)
                  0.01    0.00    0.59 ^ u_finalizer/cycle_count[29]$_DFF_PN0_/CK (DFFR_X1)
                          0.00    0.59   clock reconvergence pessimism
                          0.22    0.81   library removal time
                                  0.81   data required time
-----------------------------------------------------------------------------
                                  0.81   data required time
                                 -2.13   data arrival time
-----------------------------------------------------------------------------
                                  1.32   slack (MET)
```

### Path 4

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_partial_temporal_finalizer_physical_l8/base/6_finish.rpt`
- stage: `finish`
- startpoint: `rst_n (input port clocked by clk)`
- endpoint: `u_finalizer/lane_remainder_q[5][26]$_DFFE_PN0P_`
- path_group: `asynchronous`
- path_type: `max`
- slack: `9.2700`
- data_arrival_time: `3.4000`
- data_required_time: `12.6700`

```text
Startpoint: rst_n (input port clocked by clk)
Endpoint: u_finalizer/lane_remainder_q[5][26]$_DFFE_PN0P_
          (recovery check against rising-edge clock clk)
Path Group: asynchronous
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (propagated)
                          2.00    2.00 ^ input external delay
     1    6.53    0.00    0.00    2.00 ^ rst_n (in)
                                         rst_n (net)
                  0.00    0.00    2.00 ^ input4277/A (CLKBUF_X3)
     2   35.17    0.02    0.04    2.04 ^ input4277/Z (CLKBUF_X3)
                                         net4276 (net)
                  0.04    0.03    2.07 ^ place27151/A (BUF_X1)
     1   26.43    0.06    0.09    2.15 ^ place27151/Z (BUF_X1)
                                         net27150 (net)
                  0.06    0.01    2.16 ^ place27152/A (BUF_X2)
     2   36.17    0.04    0.06    2.22 ^ place27152/Z (BUF_X2)
                                         net27151 (net)
                  0.04    0.01    2.24 ^ place27180/A (BUF_X1)
     5   36.78    0.08    0.11    2.34 ^ place27180/Z (BUF_X1)
...
                                         clknet_5_0_0_clk_regs (net)
                  0.02    0.00   12.52 ^ clkbuf_7_3__f_clk_regs/A (CLKBUF_X3)
    13   38.88    0.03    0.06   12.59 ^ clkbuf_7_3__f_clk_regs/Z (CLKBUF_X3)
                                         clknet_7_3__leaf_clk_regs (net)
                  0.03    0.00   12.59 ^ clkbuf_leaf_1334_clk_regs/A (CLKBUF_X3)
     5    8.47    0.01    0.04   12.63 ^ clkbuf_leaf_1334_clk_regs/Z (CLKBUF_X3)
                                         clknet_leaf_1334_clk_regs (net)
                  0.01    0.00   12.63 ^ u_finalizer/lane_remainder_q[5][26]$_DFFE_PN0P_/CK (DFFR_X1)
                          0.00   12.63   clock reconvergence pessimism
                          0.04   12.67   library recovery time
                                 12.67   data required time
-----------------------------------------------------------------------------
                                 12.67   data required time
                                 -3.40   data arrival time
-----------------------------------------------------------------------------
                                  9.27   slack (MET)
```


## Worst Timing Paths Across All Stages

### Path 1

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_partial_temporal_finalizer_physical_l8/base/2_floorplan_final.rpt`
- stage: `floorplan`
- startpoint: `u_finalizer/cycle_count[0]$_DFF_PN0_`
- endpoint: `u_finalizer/cycle_count[0]$_DFF_PN0_`
- path_group: `clk`
- path_type: `min`
- slack: `0.0600`
- data_arrival_time: `0.0600`
- data_required_time: `0.0100`

```text
Startpoint: u_finalizer/cycle_count[0]$_DFF_PN0_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: u_finalizer/cycle_count[0]$_DFF_PN0_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                  0.00    0.00    0.00 ^ u_finalizer/cycle_count[0]$_DFF_PN0_/CK (DFFR_X1)
     1    1.13    0.01    0.06    0.06 ^ u_finalizer/cycle_count[0]$_DFF_PN0_/QN (DFFR_X1)
                                         u_finalizer/_13834_ (net)
                  0.01    0.00    0.06 ^ u_finalizer/cycle_count[0]$_DFF_PN0_/D (DFFR_X1)
                                  0.06   data arrival time

                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                          0.00    0.00   clock reconvergence pessimism
                                  0.00 ^ u_finalizer/cycle_count[0]$_DFF_PN0_/CK (DFFR_X1)
                          0.01    0.01   library hold time
                                  0.01   data required time
-----------------------------------------------------------------------------
                                  0.01   data required time
                                 -0.06   data arrival time
-----------------------------------------------------------------------------
                                  0.06   slack (MET)



```

### Path 2

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_partial_temporal_finalizer_physical_l8/base/3_detailed_place.rpt`
- stage: `detailed_place`
- startpoint: `u_finalizer/cycle_count[0]$_DFF_PN0_`
- endpoint: `u_finalizer/cycle_count[0]$_DFF_PN0_`
- path_group: `clk`
- path_type: `min`
- slack: `0.0600`
- data_arrival_time: `0.0600`
- data_required_time: `0.0100`

```text
Startpoint: u_finalizer/cycle_count[0]$_DFF_PN0_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: u_finalizer/cycle_count[0]$_DFF_PN0_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                  0.00    0.00    0.00 ^ u_finalizer/cycle_count[0]$_DFF_PN0_/CK (DFFR_X1)
     1    1.38    0.01    0.06    0.06 ^ u_finalizer/cycle_count[0]$_DFF_PN0_/QN (DFFR_X1)
                                         u_finalizer/_13834_ (net)
                  0.01    0.00    0.06 ^ u_finalizer/cycle_count[0]$_DFF_PN0_/D (DFFR_X1)
                                  0.06   data arrival time

                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                          0.00    0.00   clock reconvergence pessimism
                                  0.00 ^ u_finalizer/cycle_count[0]$_DFF_PN0_/CK (DFFR_X1)
                          0.01    0.01   library hold time
                                  0.01   data required time
-----------------------------------------------------------------------------
                                  0.01   data required time
                                 -0.06   data arrival time
-----------------------------------------------------------------------------
                                  0.06   slack (MET)



```

### Path 3

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_partial_temporal_finalizer_physical_l8/base/3_global_place.rpt`
- stage: `global_place`
- startpoint: `u_finalizer/cycle_count[0]$_DFF_PN0_`
- endpoint: `u_finalizer/cycle_count[0]$_DFF_PN0_`
- path_group: `clk`
- path_type: `min`
- slack: `0.0600`
- data_arrival_time: `0.0600`
- data_required_time: `0.0100`

```text
Startpoint: u_finalizer/cycle_count[0]$_DFF_PN0_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: u_finalizer/cycle_count[0]$_DFF_PN0_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                  0.00    0.00    0.00 ^ u_finalizer/cycle_count[0]$_DFF_PN0_/CK (DFFR_X1)
     1    1.38    0.01    0.06    0.06 ^ u_finalizer/cycle_count[0]$_DFF_PN0_/QN (DFFR_X1)
                                         u_finalizer/_13834_ (net)
                  0.01    0.00    0.06 ^ u_finalizer/cycle_count[0]$_DFF_PN0_/D (DFFR_X1)
                                  0.06   data arrival time

                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                          0.00    0.00   clock reconvergence pessimism
                                  0.00 ^ u_finalizer/cycle_count[0]$_DFF_PN0_/CK (DFFR_X1)
                          0.01    0.01   library hold time
                                  0.01   data required time
-----------------------------------------------------------------------------
                                  0.01   data required time
                                 -0.06   data arrival time
-----------------------------------------------------------------------------
                                  0.06   slack (MET)



```

### Path 4

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_partial_temporal_finalizer_physical_l8/base/3_resizer.rpt`
- stage: `resizer`
- startpoint: `u_finalizer/cycle_count[0]$_DFF_PN0_`
- endpoint: `u_finalizer/cycle_count[0]$_DFF_PN0_`
- path_group: `clk`
- path_type: `min`
- slack: `0.0600`
- data_arrival_time: `0.0600`
- data_required_time: `0.0100`

```text
Startpoint: u_finalizer/cycle_count[0]$_DFF_PN0_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: u_finalizer/cycle_count[0]$_DFF_PN0_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                  0.00    0.00    0.00 ^ u_finalizer/cycle_count[0]$_DFF_PN0_/CK (DFFR_X1)
     1    1.38    0.01    0.06    0.06 ^ u_finalizer/cycle_count[0]$_DFF_PN0_/QN (DFFR_X1)
                                         u_finalizer/_13834_ (net)
                  0.01    0.00    0.06 ^ u_finalizer/cycle_count[0]$_DFF_PN0_/D (DFFR_X1)
                                  0.06   data arrival time

                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                          0.00    0.00   clock reconvergence pessimism
                                  0.00 ^ u_finalizer/cycle_count[0]$_DFF_PN0_/CK (DFFR_X1)
                          0.01    0.01   library hold time
                                  0.01   data required time
-----------------------------------------------------------------------------
                                  0.01   data required time
                                 -0.06   data arrival time
-----------------------------------------------------------------------------
                                  0.06   slack (MET)



```

### Path 5

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_partial_temporal_finalizer_physical_l8/base/4_cts_final.rpt`
- stage: `cts`
- startpoint: `u_finalizer/cycle_count[0]$_DFF_PN0_`
- endpoint: `u_finalizer/cycle_count[0]$_DFF_PN0_`
- path_group: `clk`
- path_type: `min`
- slack: `0.0600`
- data_arrival_time: `0.7200`
- data_required_time: `0.6600`

```text
Startpoint: u_finalizer/cycle_count[0]$_DFF_PN0_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: u_finalizer/cycle_count[0]$_DFF_PN0_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   16.39    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.00    0.00    0.00 ^ wire27892/A (BUF_X8)
     1   70.59    0.02    0.03    0.03 ^ wire27892/Z (BUF_X8)
                                         net27891 (net)
                  0.04    0.03    0.06 ^ wire27891/A (BUF_X16)
     1   73.14    0.01    0.03    0.09 ^ wire27891/Z (BUF_X16)
                                         net27890 (net)
                  0.03    0.03    0.11 ^ wire27890/A (BUF_X16)
     2   20.79    0.01    0.03    0.14 ^ wire27890/Z (BUF_X16)
                                         net27889 (net)
                  0.01    0.00    0.14 ^ clkbuf_regs_0_clk/A (CLKBUF_X3)
     1    1.91    0.01    0.03    0.17 ^ clkbuf_regs_0_clk/Z (CLKBUF_X3)
...
                                         clknet_7_110__leaf_clk_regs (net)
                  0.02    0.00    0.62 ^ clkbuf_leaf_732_clk_regs/A (CLKBUF_X3)
     6    7.84    0.01    0.04    0.66 ^ clkbuf_leaf_732_clk_regs/Z (CLKBUF_X3)
                                         clknet_leaf_732_clk_regs (net)
                  0.01    0.00    0.66 ^ u_finalizer/cycle_count[0]$_DFF_PN0_/CK (DFFR_X1)
                          0.00    0.66   clock reconvergence pessimism
                          0.01    0.66   library hold time
                                  0.66   data required time
-----------------------------------------------------------------------------
                                  0.66   data required time
                                 -0.72   data arrival time
-----------------------------------------------------------------------------
                                  0.06   slack (MET)



```

### Path 6

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_partial_temporal_finalizer_physical_l8/base/5_global_route.rpt`
- stage: `route`
- startpoint: `u_finalizer/cycle_count[0]$_DFF_PN0_`
- endpoint: `u_finalizer/cycle_count[0]$_DFF_PN0_`
- path_group: `clk`
- path_type: `min`
- slack: `0.0600`
- data_arrival_time: `0.7300`
- data_required_time: `0.6700`

```text
Startpoint: u_finalizer/cycle_count[0]$_DFF_PN0_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: u_finalizer/cycle_count[0]$_DFF_PN0_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   16.23    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.00    0.00    0.00 ^ wire27892/A (BUF_X8)
     1   70.15    0.01    0.02    0.03 ^ wire27892/Z (BUF_X8)
                                         net27891 (net)
                  0.04    0.03    0.06 ^ wire27891/A (BUF_X16)
     1   72.37    0.01    0.03    0.08 ^ wire27891/Z (BUF_X16)
                                         net27890 (net)
                  0.04    0.03    0.11 ^ wire27890/A (BUF_X16)
     2   20.77    0.01    0.03    0.14 ^ wire27890/Z (BUF_X16)
                                         net27889 (net)
                  0.01    0.00    0.14 ^ clkbuf_regs_0_clk/A (CLKBUF_X3)
     1    2.21    0.01    0.03    0.17 ^ clkbuf_regs_0_clk/Z (CLKBUF_X3)
...
                                         clknet_7_110__leaf_clk_regs (net)
                  0.02    0.00    0.62 ^ clkbuf_leaf_732_clk_regs/A (CLKBUF_X3)
     6    8.29    0.01    0.04    0.66 ^ clkbuf_leaf_732_clk_regs/Z (CLKBUF_X3)
                                         clknet_leaf_732_clk_regs (net)
                  0.01    0.00    0.66 ^ u_finalizer/cycle_count[0]$_DFF_PN0_/CK (DFFR_X1)
                          0.00    0.66   clock reconvergence pessimism
                          0.01    0.67   library hold time
                                  0.67   data required time
-----------------------------------------------------------------------------
                                  0.67   data required time
                                 -0.73   data arrival time
-----------------------------------------------------------------------------
                                  0.06   slack (MET)



```

### Path 7

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_partial_temporal_finalizer_physical_l8/base/6_finish.rpt`
- stage: `finish`
- startpoint: `u_finalizer/cycle_count[0]$_DFF_PN0_`
- endpoint: `u_finalizer/cycle_count[0]$_DFF_PN0_`
- path_group: `clk`
- path_type: `min`
- slack: `0.0600`
- data_arrival_time: `0.6600`
- data_required_time: `0.6000`

```text
Startpoint: u_finalizer/cycle_count[0]$_DFF_PN0_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: u_finalizer/cycle_count[0]$_DFF_PN0_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   12.49    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.00    0.00    0.00 ^ wire27892/A (BUF_X8)
     1   52.78    0.01    0.02    0.02 ^ wire27892/Z (BUF_X8)
                                         net27891 (net)
                  0.03    0.02    0.05 ^ wire27891/A (BUF_X16)
     1   55.88    0.01    0.03    0.07 ^ wire27891/Z (BUF_X16)
                                         net27890 (net)
                  0.03    0.02    0.10 ^ wire27890/A (BUF_X16)
     2   18.87    0.01    0.03    0.12 ^ wire27890/Z (BUF_X16)
                                         net27889 (net)
                  0.01    0.00    0.13 ^ clkbuf_regs_0_clk/A (CLKBUF_X3)
     1    1.85    0.01    0.03    0.15 ^ clkbuf_regs_0_clk/Z (CLKBUF_X3)
...
                                         clknet_7_110__leaf_clk_regs (net)
                  0.02    0.00    0.55 ^ clkbuf_leaf_732_clk_regs/A (CLKBUF_X3)
     6    8.05    0.01    0.04    0.59 ^ clkbuf_leaf_732_clk_regs/Z (CLKBUF_X3)
                                         clknet_leaf_732_clk_regs (net)
                  0.01    0.00    0.59 ^ u_finalizer/cycle_count[0]$_DFF_PN0_/CK (DFFR_X1)
                          0.00    0.59   clock reconvergence pessimism
                          0.01    0.60   library hold time
                                  0.60   data required time
-----------------------------------------------------------------------------
                                  0.60   data required time
                                 -0.66   data arrival time
-----------------------------------------------------------------------------
                                  0.06   slack (MET)



```

### Path 8

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_partial_temporal_finalizer_physical_l8/base/3_global_place.rpt`
- stage: `global_place`
- startpoint: `u_temporal/u_pair_merge/left_global_max_hold_q[31]$_DFFE_PN0P_`
- endpoint: `u_temporal/u_state_memory/protocol_error_q$_DFF_PN0_`
- path_group: `clk`
- path_type: `max`
- slack: `0.6300`
- data_arrival_time: `11.3300`
- data_required_time: `11.9500`

```text
Startpoint: u_temporal/u_pair_merge/left_global_max_hold_q[31]$_DFFE_PN0P_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: u_temporal/u_state_memory/protocol_error_q$_DFF_PN0_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                  0.00    0.00    0.00 ^ u_temporal/u_pair_merge/left_global_max_hold_q[31]$_DFFE_PN0P_/CK (DFFR_X1)
     2    5.14    0.02    0.11    0.11 ^ u_temporal/u_pair_merge/left_global_max_hold_q[31]$_DFFE_PN0P_/Q (DFFR_X1)
                                         u_temporal/u_pair_merge/left_global_max_hold_q[31] (net)
                  0.02    0.00    0.11 ^ u_temporal/u_pair_merge/_210538_/A (HA_X1)
     3    9.68    0.06    0.09    0.20 ^ u_temporal/u_pair_merge/_210538_/S (HA_X1)
                                         u_temporal/u_pair_merge/_050951_ (net)
                  0.06    0.00    0.20 ^ u_temporal/u_pair_merge/_120417_/A1 (NAND4_X2)
     3    9.68    0.03    0.05    0.25 v u_temporal/u_pair_merge/_120417_/ZN (NAND4_X2)
                                         u_temporal/u_pair_merge/_073221_ (net)
                  0.03    0.00    0.25 v u_temporal/u_pair_merge/_120420_/A2 (NOR4_X2)
     2    5.10    0.05    0.08    0.33 ^ u_temporal/u_pair_merge/_120420_/ZN (NOR4_X2)
                                         u_temporal/u_pair_merge/_073224_ (net)
                  0.05    0.00    0.33 ^ u_temporal/u_pair_merge/_120462_/A1 (NAND2_X1)
...
                                 11.33   data arrival time

                  0.00   12.00   12.00   clock clk (rise edge)
                          0.00   12.00   clock network delay (ideal)
                          0.00   12.00   clock reconvergence pessimism
                                 12.00 ^ u_temporal/u_state_memory/protocol_error_q$_DFF_PN0_/CK (DFFR_X2)
                         -0.05   11.95   library setup time
                                 11.95   data required time
-----------------------------------------------------------------------------
                                 11.95   data required time
                                -11.33   data arrival time
-----------------------------------------------------------------------------
                                  0.63   slack (MET)



```
