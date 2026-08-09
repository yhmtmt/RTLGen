# OpenROAD Timing Debug Summary

- design_dir: `runs/designs/npu_blocks/attention_score32_exact_partial_temporal_finalizer_physical_l1`
- metrics_path: `runs/designs/npu_blocks/attention_score32_exact_partial_temporal_finalizer_physical_l1/metrics.csv`
- rows_considered: 1

## Metrics Rows

| param_hash | tag | status | critical_path_ns | density | result_path |
| --- | --- | --- | ---: | ---: | --- |
| 7d5d9129 | attention_exact_partial_temporal_finalizer_12ns_v1_7d5d9129 | ok | 11.6827 | 0.4 | `/orfs/flow/reports/nangate45/attention_score32_exact_partial_temporal_finalizer_physical_l1/base/6_finish.rpt` |

## Inspected Report Files

- `/orfs/flow/reports/nangate45/attention_score32_exact_partial_temporal_finalizer_physical_l1/base/6_finish.rpt`
- `/orfs/flow/reports/nangate45/attention_score32_exact_partial_temporal_finalizer_physical_l1/base/5_global_route.rpt`
- `/orfs/flow/reports/nangate45/attention_score32_exact_partial_temporal_finalizer_physical_l1/base/5_route_drc.rpt`
- `/orfs/flow/reports/nangate45/attention_score32_exact_partial_temporal_finalizer_physical_l1/base/5_route_drc.rpt-5.rpt`
- `/orfs/flow/reports/nangate45/attention_score32_exact_partial_temporal_finalizer_physical_l1/base/4_cts_final.rpt`
- `/orfs/flow/reports/nangate45/attention_score32_exact_partial_temporal_finalizer_physical_l1/base/3_resizer.rpt`
- `/orfs/flow/reports/nangate45/attention_score32_exact_partial_temporal_finalizer_physical_l1/base/3_detailed_place.rpt`
- `/orfs/flow/reports/nangate45/attention_score32_exact_partial_temporal_finalizer_physical_l1/base/3_global_place.rpt`
- `/orfs/flow/reports/nangate45/attention_score32_exact_partial_temporal_finalizer_physical_l1/base/2_floorplan_final.rpt`
- `/orfs/flow/reports/nangate45/attention_score32_exact_partial_temporal_finalizer_physical_l1/base/congestion-5.rpt`
- `/orfs/flow/reports/nangate45/attention_score32_exact_partial_temporal_finalizer_physical_l1/base/drt_antennas.log`
- `/orfs/flow/reports/nangate45/attention_score32_exact_partial_temporal_finalizer_physical_l1/base/grt_antennas.log`
- `/orfs/flow/reports/nangate45/attention_score32_exact_partial_temporal_finalizer_physical_l1/base/metadata-generate.log`

## Preferred Final-Stage Timing Paths

- raw_path_block_count: 52
- unique_path_block_count: 28
- preferred_stage: `finish`

### Path 1

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_partial_temporal_finalizer_physical_l1/base/6_finish.rpt`
- stage: `finish`
- startpoint: `u_finalizer/cycle_count[0]$_DFF_PN0_`
- endpoint: `u_finalizer/cycle_count[0]$_DFF_PN0_`
- path_group: `clk`
- path_type: `min`
- slack: `0.0600`
- data_arrival_time: `0.7000`
- data_required_time: `0.6400`

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
     1   36.64    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.01    0.01    0.01 ^ wire27709/A (BUF_X8)
     1   39.86    0.01    0.03    0.03 ^ wire27709/Z (BUF_X8)
                                         net27708 (net)
                  0.02    0.01    0.05 ^ wire27708/A (BUF_X16)
     1   58.89    0.01    0.02    0.07 ^ wire27708/Z (BUF_X16)
                                         net27707 (net)
                  0.03    0.03    0.10 ^ wire27707/A (BUF_X16)
     2   25.55    0.01    0.03    0.12 ^ wire27707/Z (BUF_X16)
                                         net27706 (net)
                  0.01    0.00    0.13 ^ clkbuf_regs_0_clk/A (CLKBUF_X3)
     1    1.52    0.01    0.03    0.15 ^ clkbuf_regs_0_clk/Z (CLKBUF_X3)
...
                                         clknet_7_83__leaf_clk_regs (net)
                  0.03    0.00    0.59 ^ clkbuf_leaf_577_clk_regs/A (CLKBUF_X3)
     7    8.88    0.01    0.04    0.63 ^ clkbuf_leaf_577_clk_regs/Z (CLKBUF_X3)
                                         clknet_leaf_577_clk_regs (net)
                  0.01    0.00    0.63 ^ u_finalizer/cycle_count[0]$_DFF_PN0_/CK (DFFR_X1)
                          0.00    0.63   clock reconvergence pessimism
                          0.01    0.64   library hold time
                                  0.64   data required time
-----------------------------------------------------------------------------
                                  0.64   data required time
                                 -0.70   data arrival time
-----------------------------------------------------------------------------
                                  0.06   slack (MET)



```

### Path 2

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_partial_temporal_finalizer_physical_l1/base/6_finish.rpt`
- stage: `finish`
- startpoint: `u_temporal/u_pair_merge/right_global_max_hold_q[19]$_DFFE_PN0P_`
- endpoint: `u_temporal/u_state_memory/protocol_error_q$_DFF_PN0_`
- path_group: `clk`
- path_type: `max`
- slack: `0.9400`
- data_arrival_time: `11.6800`
- data_required_time: `12.6200`

```text
Startpoint: u_temporal/u_pair_merge/right_global_max_hold_q[19]$_DFFE_PN0P_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: u_temporal/u_state_memory/protocol_error_q$_DFF_PN0_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   36.64    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.01    0.01    0.01 ^ wire27709/A (BUF_X8)
     1   39.86    0.01    0.03    0.03 ^ wire27709/Z (BUF_X8)
                                         net27708 (net)
                  0.02    0.01    0.05 ^ wire27708/A (BUF_X16)
     1   58.89    0.01    0.02    0.07 ^ wire27708/Z (BUF_X16)
                                         net27707 (net)
                  0.03    0.03    0.10 ^ wire27707/A (BUF_X16)
     2   25.55    0.01    0.03    0.12 ^ wire27707/Z (BUF_X16)
                                         net27706 (net)
                  0.01    0.00    0.13 ^ clkbuf_regs_0_clk/A (CLKBUF_X3)
     1    1.52    0.01    0.03    0.15 ^ clkbuf_regs_0_clk/Z (CLKBUF_X3)
...
                                         clknet_7_46__leaf_clk_regs (net)
                  0.03    0.00   12.62 ^ clkbuf_leaf_1317_clk_regs/A (CLKBUF_X3)
     6   10.01    0.01    0.04   12.66 ^ clkbuf_leaf_1317_clk_regs/Z (CLKBUF_X3)
                                         clknet_leaf_1317_clk_regs (net)
                  0.01    0.00   12.66 ^ u_temporal/u_state_memory/protocol_error_q$_DFF_PN0_/CK (DFFR_X1)
                          0.00   12.66   clock reconvergence pessimism
                         -0.04   12.62   library setup time
                                 12.62   data required time
-----------------------------------------------------------------------------
                                 12.62   data required time
                                -11.68   data arrival time
-----------------------------------------------------------------------------
                                  0.94   slack (MET)



```

### Path 3

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_partial_temporal_finalizer_physical_l1/base/6_finish.rpt`
- stage: `finish`
- startpoint: `rst_n (input port clocked by clk)`
- endpoint: `u_temporal/u_pair_merge/right_value_hold_q[237]$_DFFE_PN0P_`
- path_group: `asynchronous`
- path_type: `min`
- slack: `1.1500`
- data_arrival_time: `2.1000`
- data_required_time: `0.9400`

```text
Startpoint: rst_n (input port clocked by clk)
Endpoint: u_temporal/u_pair_merge/right_value_hold_q[237]$_DFFE_PN0P_
          (removal check against rising-edge clock clk)
Path Group: asynchronous
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (propagated)
                          2.00    2.00 ^ input external delay
     1    5.46    0.00    0.00    2.00 ^ rst_n (in)
                                         rst_n (net)
                  0.00    0.00    2.00 ^ input4277/A (CLKBUF_X3)
    16   71.24    0.03    0.05    2.05 ^ input4277/Z (CLKBUF_X3)
                                         net4276 (net)
                  0.08    0.05    2.10 ^ u_temporal/u_pair_merge/right_value_hold_q[237]$_DFFE_PN0P_/RN (DFFR_X1)
                                  2.10   data arrival time

                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   36.64    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.01    0.01    0.01 ^ wire27709/A (BUF_X8)
...
                                         clknet_6_0_0_clk_regs (net)
                  0.01    0.00    0.56 ^ clkbuf_7_0__f_clk_regs/A (CLKBUF_X3)
     9   44.61    0.03    0.06    0.62 ^ clkbuf_7_0__f_clk_regs/Z (CLKBUF_X3)
                                         clknet_7_0__leaf_clk_regs (net)
                  0.03    0.00    0.62 ^ clkbuf_leaf_1387_clk_regs/A (CLKBUF_X3)
     7    9.93    0.01    0.04    0.67 ^ clkbuf_leaf_1387_clk_regs/Z (CLKBUF_X3)
                                         clknet_leaf_1387_clk_regs (net)
                  0.01    0.00    0.67 ^ u_temporal/u_pair_merge/right_value_hold_q[237]$_DFFE_PN0P_/CK (DFFR_X1)
                          0.00    0.67   clock reconvergence pessimism
                          0.28    0.94   library removal time
                                  0.94   data required time
-----------------------------------------------------------------------------
                                  0.94   data required time
                                 -2.10   data arrival time
-----------------------------------------------------------------------------
                                  1.15   slack (MET)
```

### Path 4

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_partial_temporal_finalizer_physical_l1/base/6_finish.rpt`
- stage: `finish`
- startpoint: `rst_n (input port clocked by clk)`
- endpoint: `u_temporal/head_sequence_q[2][12]$_DFFE_PN0P_`
- path_group: `asynchronous`
- path_type: `max`
- slack: `9.1000`
- data_arrival_time: `3.5700`
- data_required_time: `12.6700`

```text
Startpoint: rst_n (input port clocked by clk)
Endpoint: u_temporal/head_sequence_q[2][12]$_DFFE_PN0P_
          (recovery check against rising-edge clock clk)
Path Group: asynchronous
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (propagated)
                          2.00    2.00 ^ input external delay
     1    5.46    0.00    0.00    2.00 ^ rst_n (in)
                                         rst_n (net)
                  0.00    0.00    2.00 ^ input4277/A (CLKBUF_X3)
    16   71.24    0.03    0.05    2.05 ^ input4277/Z (CLKBUF_X3)
                                         net4276 (net)
                  0.08    0.06    2.11 ^ place27119/A (BUF_X2)
     4   47.39    0.05    0.07    2.18 ^ place27119/Z (BUF_X2)
                                         net27118 (net)
                  0.06    0.02    2.20 ^ place27248/A (BUF_X1)
     3   13.04    0.03    0.06    2.26 ^ place27248/Z (BUF_X1)
                                         net27247 (net)
                  0.03    0.00    2.26 ^ place27262/A (BUF_X2)
    11   84.43    0.08    0.09    2.35 ^ place27262/Z (BUF_X2)
...
                                         clknet_6_39_0_clk_regs (net)
                  0.01    0.00   12.52 ^ clkbuf_7_78__f_clk_regs/A (CLKBUF_X3)
    11   33.47    0.03    0.06   12.58 ^ clkbuf_7_78__f_clk_regs/Z (CLKBUF_X3)
                                         clknet_7_78__leaf_clk_regs (net)
                  0.03    0.00   12.58 ^ clkbuf_leaf_928_clk_regs/A (CLKBUF_X3)
     7    9.54    0.01    0.04   12.62 ^ clkbuf_leaf_928_clk_regs/Z (CLKBUF_X3)
                                         clknet_leaf_928_clk_regs (net)
                  0.01    0.00   12.62 ^ u_temporal/head_sequence_q[2][12]$_DFFE_PN0P_/CK (DFFR_X1)
                          0.00   12.62   clock reconvergence pessimism
                          0.05   12.67   library recovery time
                                 12.67   data required time
-----------------------------------------------------------------------------
                                 12.67   data required time
                                 -3.57   data arrival time
-----------------------------------------------------------------------------
                                  9.10   slack (MET)
```


## Worst Timing Paths Across All Stages

### Path 1

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_partial_temporal_finalizer_physical_l1/base/2_floorplan_final.rpt`
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
                                         u_finalizer/_05274_ (net)
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

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_partial_temporal_finalizer_physical_l1/base/3_detailed_place.rpt`
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
                                         u_finalizer/_05274_ (net)
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

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_partial_temporal_finalizer_physical_l1/base/3_global_place.rpt`
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
                                         u_finalizer/_05274_ (net)
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

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_partial_temporal_finalizer_physical_l1/base/3_resizer.rpt`
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
                                         u_finalizer/_05274_ (net)
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

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_partial_temporal_finalizer_physical_l1/base/4_cts_final.rpt`
- stage: `cts`
- startpoint: `u_finalizer/cycle_count[0]$_DFF_PN0_`
- endpoint: `u_finalizer/cycle_count[0]$_DFF_PN0_`
- path_group: `clk`
- path_type: `min`
- slack: `0.0600`
- data_arrival_time: `0.7800`
- data_required_time: `0.7200`

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
     1   50.35    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.01    0.01    0.01 ^ wire27709/A (BUF_X8)
     1   51.88    0.01    0.03    0.04 ^ wire27709/Z (BUF_X8)
                                         net27708 (net)
                  0.02    0.02    0.06 ^ wire27708/A (BUF_X16)
     1   72.27    0.01    0.03    0.08 ^ wire27708/Z (BUF_X16)
                                         net27707 (net)
                  0.03    0.03    0.11 ^ wire27707/A (BUF_X16)
     2   30.10    0.01    0.03    0.14 ^ wire27707/Z (BUF_X16)
                                         net27706 (net)
                  0.01    0.00    0.14 ^ clkbuf_regs_0_clk/A (CLKBUF_X3)
     1    1.59    0.01    0.03    0.17 ^ clkbuf_regs_0_clk/Z (CLKBUF_X3)
...
                                         clknet_7_83__leaf_clk_regs (net)
                  0.03    0.00    0.67 ^ clkbuf_leaf_577_clk_regs/A (CLKBUF_X3)
     7    8.82    0.01    0.04    0.71 ^ clkbuf_leaf_577_clk_regs/Z (CLKBUF_X3)
                                         clknet_leaf_577_clk_regs (net)
                  0.01    0.00    0.71 ^ u_finalizer/cycle_count[0]$_DFF_PN0_/CK (DFFR_X1)
                          0.00    0.71   clock reconvergence pessimism
                          0.01    0.72   library hold time
                                  0.72   data required time
-----------------------------------------------------------------------------
                                  0.72   data required time
                                 -0.78   data arrival time
-----------------------------------------------------------------------------
                                  0.06   slack (MET)



```

### Path 6

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_partial_temporal_finalizer_physical_l1/base/5_global_route.rpt`
- stage: `route`
- startpoint: `u_temporal/cycle_count_q[0]$_DFF_PN0_`
- endpoint: `u_temporal/cycle_count_q[0]$_DFF_PN0_`
- path_group: `clk`
- path_type: `min`
- slack: `0.0600`
- data_arrival_time: `0.7800`
- data_required_time: `0.7200`

```text
Startpoint: u_temporal/cycle_count_q[0]$_DFF_PN0_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: u_temporal/cycle_count_q[0]$_DFF_PN0_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   50.12    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.01    0.01    0.01 ^ wire27709/A (BUF_X8)
     1   51.91    0.01    0.03    0.04 ^ wire27709/Z (BUF_X8)
                                         net27708 (net)
                  0.02    0.02    0.06 ^ wire27708/A (BUF_X16)
     1   72.05    0.01    0.03    0.08 ^ wire27708/Z (BUF_X16)
                                         net27707 (net)
                  0.04    0.03    0.11 ^ wire27707/A (BUF_X16)
     2   30.31    0.01    0.03    0.14 ^ wire27707/Z (BUF_X16)
                                         net27706 (net)
                  0.01    0.01    0.15 ^ clkbuf_regs_0_clk/A (CLKBUF_X3)
     1    1.70    0.01    0.03    0.17 ^ clkbuf_regs_0_clk/Z (CLKBUF_X3)
...
                                         clknet_7_81__leaf_clk_regs (net)
                  0.02    0.00    0.67 ^ clkbuf_leaf_551_clk_regs/A (CLKBUF_X3)
     7   10.38    0.01    0.04    0.71 ^ clkbuf_leaf_551_clk_regs/Z (CLKBUF_X3)
                                         clknet_leaf_551_clk_regs (net)
                  0.01    0.00    0.71 ^ u_temporal/cycle_count_q[0]$_DFF_PN0_/CK (DFFR_X1)
                          0.00    0.71   clock reconvergence pessimism
                          0.01    0.72   library hold time
                                  0.72   data required time
-----------------------------------------------------------------------------
                                  0.72   data required time
                                 -0.78   data arrival time
-----------------------------------------------------------------------------
                                  0.06   slack (MET)



```

### Path 7

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_partial_temporal_finalizer_physical_l1/base/6_finish.rpt`
- stage: `finish`
- startpoint: `u_finalizer/cycle_count[0]$_DFF_PN0_`
- endpoint: `u_finalizer/cycle_count[0]$_DFF_PN0_`
- path_group: `clk`
- path_type: `min`
- slack: `0.0600`
- data_arrival_time: `0.7000`
- data_required_time: `0.6400`

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
     1   36.64    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.01    0.01    0.01 ^ wire27709/A (BUF_X8)
     1   39.86    0.01    0.03    0.03 ^ wire27709/Z (BUF_X8)
                                         net27708 (net)
                  0.02    0.01    0.05 ^ wire27708/A (BUF_X16)
     1   58.89    0.01    0.02    0.07 ^ wire27708/Z (BUF_X16)
                                         net27707 (net)
                  0.03    0.03    0.10 ^ wire27707/A (BUF_X16)
     2   25.55    0.01    0.03    0.12 ^ wire27707/Z (BUF_X16)
                                         net27706 (net)
                  0.01    0.00    0.13 ^ clkbuf_regs_0_clk/A (CLKBUF_X3)
     1    1.52    0.01    0.03    0.15 ^ clkbuf_regs_0_clk/Z (CLKBUF_X3)
...
                                         clknet_7_83__leaf_clk_regs (net)
                  0.03    0.00    0.59 ^ clkbuf_leaf_577_clk_regs/A (CLKBUF_X3)
     7    8.88    0.01    0.04    0.63 ^ clkbuf_leaf_577_clk_regs/Z (CLKBUF_X3)
                                         clknet_leaf_577_clk_regs (net)
                  0.01    0.00    0.63 ^ u_finalizer/cycle_count[0]$_DFF_PN0_/CK (DFFR_X1)
                          0.00    0.63   clock reconvergence pessimism
                          0.01    0.64   library hold time
                                  0.64   data required time
-----------------------------------------------------------------------------
                                  0.64   data required time
                                 -0.70   data arrival time
-----------------------------------------------------------------------------
                                  0.06   slack (MET)



```

### Path 8

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_partial_temporal_finalizer_physical_l1/base/3_global_place.rpt`
- stage: `global_place`
- startpoint: `u_temporal/u_pair_merge/right_global_max_hold_q[19]$_DFFE_PN0P_`
- endpoint: `u_temporal/u_state_memory/protocol_error_q$_DFF_PN0_`
- path_group: `clk`
- path_type: `max`
- slack: `0.9200`
- data_arrival_time: `11.0400`
- data_required_time: `11.9600`

```text
Startpoint: u_temporal/u_pair_merge/right_global_max_hold_q[19]$_DFFE_PN0P_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: u_temporal/u_state_memory/protocol_error_q$_DFF_PN0_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                  0.00    0.00    0.00 ^ u_temporal/u_pair_merge/right_global_max_hold_q[19]$_DFFE_PN0P_/CK (DFFR_X1)
     3   11.34    0.02    0.08    0.08 v u_temporal/u_pair_merge/right_global_max_hold_q[19]$_DFFE_PN0P_/QN (DFFR_X1)
                                         u_temporal/u_pair_merge/_059214_ (net)
                  0.02    0.00    0.08 v u_temporal/u_pair_merge/_213478_/B (HA_X1)
     3    7.31    0.02    0.07    0.15 v u_temporal/u_pair_merge/_213478_/S (HA_X1)
                                         u_temporal/u_pair_merge/_059216_ (net)
                  0.02    0.00    0.16 v u_temporal/u_pair_merge/_119877_/B2 (AOI21_X1)
     1    3.96    0.03    0.05    0.20 ^ u_temporal/u_pair_merge/_119877_/ZN (AOI21_X1)
                                         u_temporal/u_pair_merge/_073314_ (net)
                  0.03    0.00    0.20 ^ u_temporal/u_pair_merge/_119880_/A (OAI21_X1)
     4    9.22    0.02    0.04    0.24 v u_temporal/u_pair_merge/_119880_/ZN (OAI21_X1)
                                         u_temporal/u_pair_merge/_073317_ (net)
                  0.02    0.00    0.24 v u_temporal/u_pair_merge/_119987_/A2 (NOR4_X1)
...
                                 11.04   data arrival time

                  0.00   12.00   12.00   clock clk (rise edge)
                          0.00   12.00   clock network delay (ideal)
                          0.00   12.00   clock reconvergence pessimism
                                 12.00 ^ u_temporal/u_state_memory/protocol_error_q$_DFF_PN0_/CK (DFFR_X1)
                         -0.04   11.96   library setup time
                                 11.96   data required time
-----------------------------------------------------------------------------
                                 11.96   data required time
                                -11.04   data arrival time
-----------------------------------------------------------------------------
                                  0.92   slack (MET)



```
