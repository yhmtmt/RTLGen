# OpenROAD Timing Debug Summary

- design_dir: `runs/designs/npu_blocks/attention_score32_exact_partial_temporal_finalizer_physical_l4`
- metrics_path: `runs/designs/npu_blocks/attention_score32_exact_partial_temporal_finalizer_physical_l4/metrics.csv`
- rows_considered: 1

## Metrics Rows

| param_hash | tag | status | critical_path_ns | density | result_path |
| --- | --- | --- | ---: | ---: | --- |
| 7d5d9129 | attention_exact_partial_temporal_finalizer_12ns_v1_7d5d9129 | ok | 11.6114 | 0.4 | `/orfs/flow/reports/nangate45/attention_score32_exact_partial_temporal_finalizer_physical_l4/base/6_finish.rpt` |

## Inspected Report Files

- `/orfs/flow/reports/nangate45/attention_score32_exact_partial_temporal_finalizer_physical_l4/base/6_finish.rpt`
- `/orfs/flow/reports/nangate45/attention_score32_exact_partial_temporal_finalizer_physical_l4/base/5_global_route.rpt`
- `/orfs/flow/reports/nangate45/attention_score32_exact_partial_temporal_finalizer_physical_l4/base/5_route_drc.rpt`
- `/orfs/flow/reports/nangate45/attention_score32_exact_partial_temporal_finalizer_physical_l4/base/5_route_drc.rpt-5.rpt`
- `/orfs/flow/reports/nangate45/attention_score32_exact_partial_temporal_finalizer_physical_l4/base/4_cts_final.rpt`
- `/orfs/flow/reports/nangate45/attention_score32_exact_partial_temporal_finalizer_physical_l4/base/3_resizer.rpt`
- `/orfs/flow/reports/nangate45/attention_score32_exact_partial_temporal_finalizer_physical_l4/base/3_detailed_place.rpt`
- `/orfs/flow/reports/nangate45/attention_score32_exact_partial_temporal_finalizer_physical_l4/base/3_global_place.rpt`
- `/orfs/flow/reports/nangate45/attention_score32_exact_partial_temporal_finalizer_physical_l4/base/2_floorplan_final.rpt`
- `/orfs/flow/reports/nangate45/attention_score32_exact_partial_temporal_finalizer_physical_l4/base/drt_antennas.log`
- `/orfs/flow/reports/nangate45/attention_score32_exact_partial_temporal_finalizer_physical_l4/base/grt_antennas.log`
- `/orfs/flow/reports/nangate45/attention_score32_exact_partial_temporal_finalizer_physical_l4/base/metadata-generate.log`

## Preferred Final-Stage Timing Paths

- raw_path_block_count: 52
- unique_path_block_count: 28
- preferred_stage: `finish`

### Path 1

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_partial_temporal_finalizer_physical_l4/base/6_finish.rpt`
- stage: `finish`
- startpoint: `u_finalizer/cycle_count[0]$_DFF_PN0_`
- endpoint: `u_finalizer/cycle_count[0]$_DFF_PN0_`
- path_group: `clk`
- path_type: `min`
- slack: `0.0600`
- data_arrival_time: `0.6800`
- data_required_time: `0.6200`

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
     1   12.57    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.00    0.00    0.00 ^ wire28039/A (BUF_X8)
     1   53.01    0.01    0.02    0.02 ^ wire28039/Z (BUF_X8)
                                         net28038 (net)
                  0.03    0.02    0.05 ^ wire28038/A (BUF_X16)
     1   56.17    0.01    0.03    0.07 ^ wire28038/Z (BUF_X16)
                                         net28037 (net)
                  0.03    0.02    0.10 ^ wire28037/A (BUF_X16)
     2   19.38    0.01    0.03    0.12 ^ wire28037/Z (BUF_X16)
                                         net28036 (net)
                  0.01    0.00    0.13 ^ clkbuf_regs_0_clk/A (CLKBUF_X3)
     1    1.95    0.01    0.03    0.15 ^ clkbuf_regs_0_clk/Z (CLKBUF_X3)
...
                                         clknet_7_77__leaf_clk_regs (net)
                  0.02    0.00    0.57 ^ clkbuf_leaf_818_clk_regs/A (CLKBUF_X3)
     7    8.51    0.01    0.04    0.61 ^ clkbuf_leaf_818_clk_regs/Z (CLKBUF_X3)
                                         clknet_leaf_818_clk_regs (net)
                  0.01    0.00    0.61 ^ u_finalizer/cycle_count[0]$_DFF_PN0_/CK (DFFR_X1)
                          0.00    0.61   clock reconvergence pessimism
                          0.01    0.62   library hold time
                                  0.62   data required time
-----------------------------------------------------------------------------
                                  0.62   data required time
                                 -0.68   data arrival time
-----------------------------------------------------------------------------
                                  0.06   slack (MET)



```

### Path 2

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_partial_temporal_finalizer_physical_l4/base/6_finish.rpt`
- stage: `finish`
- startpoint: `u_temporal/u_pair_merge/right_global_max_hold_q[11]$_DFFE_PN0P_`
- endpoint: `u_temporal/u_state_memory/protocol_error_q$_DFF_PN0_`
- path_group: `clk`
- path_type: `max`
- slack: `0.9800`
- data_arrival_time: `11.6100`
- data_required_time: `12.5900`

```text
Startpoint: u_temporal/u_pair_merge/right_global_max_hold_q[11]$_DFFE_PN0P_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: u_temporal/u_state_memory/protocol_error_q$_DFF_PN0_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   12.57    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.00    0.00    0.00 ^ wire28039/A (BUF_X8)
     1   53.01    0.01    0.02    0.02 ^ wire28039/Z (BUF_X8)
                                         net28038 (net)
                  0.03    0.02    0.05 ^ wire28038/A (BUF_X16)
     1   56.17    0.01    0.03    0.07 ^ wire28038/Z (BUF_X16)
                                         net28037 (net)
                  0.03    0.02    0.10 ^ wire28037/A (BUF_X16)
     2   19.38    0.01    0.03    0.12 ^ wire28037/Z (BUF_X16)
                                         net28036 (net)
                  0.01    0.00    0.13 ^ clkbuf_regs_0_clk/A (CLKBUF_X3)
     1    1.95    0.01    0.03    0.15 ^ clkbuf_regs_0_clk/Z (CLKBUF_X3)
...
                                         clknet_7_62__leaf_clk_regs (net)
                  0.02    0.00   12.59 ^ clkbuf_leaf_1065_clk_regs/A (CLKBUF_X3)
     6    9.48    0.01    0.04   12.63 ^ clkbuf_leaf_1065_clk_regs/Z (CLKBUF_X3)
                                         clknet_leaf_1065_clk_regs (net)
                  0.01    0.00   12.63 ^ u_temporal/u_state_memory/protocol_error_q$_DFF_PN0_/CK (DFFR_X1)
                          0.00   12.63   clock reconvergence pessimism
                         -0.04   12.59   library setup time
                                 12.59   data required time
-----------------------------------------------------------------------------
                                 12.59   data required time
                                -11.61   data arrival time
-----------------------------------------------------------------------------
                                  0.98   slack (MET)



```

### Path 3

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_partial_temporal_finalizer_physical_l4/base/6_finish.rpt`
- stage: `finish`
- startpoint: `rst_n (input port clocked by clk)`
- endpoint: `protocol_error_count_q[25]$_DFFE_PN0P_`
- path_group: `asynchronous`
- path_type: `min`
- slack: `1.2200`
- data_arrival_time: `2.0600`
- data_required_time: `0.8500`

```text
Startpoint: rst_n (input port clocked by clk)
Endpoint: protocol_error_count_q[25]$_DFFE_PN0P_
          (removal check against rising-edge clock clk)
Path Group: asynchronous
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (propagated)
                          2.00    2.00 ^ input external delay
     1    5.78    0.00    0.00    2.00 ^ rst_n (in)
                                         rst_n (net)
                  0.00    0.00    2.00 ^ input4277/A (CLKBUF_X3)
    14   44.15    0.03    0.05    2.05 ^ input4277/Z (CLKBUF_X3)
                                         net4276 (net)
                  0.03    0.01    2.06 ^ protocol_error_count_q[25]$_DFFE_PN0P_/RN (DFFR_X1)
                                  2.06   data arrival time

                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   12.57    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.00    0.00    0.00 ^ wire28039/A (BUF_X8)
...
                                         clknet_5_23_0_clk_regs (net)
                  0.02    0.00    0.51 ^ clkbuf_7_95__f_clk_regs/A (CLKBUF_X3)
     6   37.14    0.03    0.06    0.57 ^ clkbuf_7_95__f_clk_regs/Z (CLKBUF_X3)
                                         clknet_7_95__leaf_clk_regs (net)
                  0.03    0.01    0.58 ^ clkbuf_leaf_832_clk_regs/A (CLKBUF_X3)
     6    8.38    0.01    0.04    0.62 ^ clkbuf_leaf_832_clk_regs/Z (CLKBUF_X3)
                                         clknet_leaf_832_clk_regs (net)
                  0.01    0.00    0.62 ^ protocol_error_count_q[25]$_DFFE_PN0P_/CK (DFFR_X1)
                          0.00    0.62   clock reconvergence pessimism
                          0.23    0.85   library removal time
                                  0.85   data required time
-----------------------------------------------------------------------------
                                  0.85   data required time
                                 -2.06   data arrival time
-----------------------------------------------------------------------------
                                  1.22   slack (MET)
```

### Path 4

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_partial_temporal_finalizer_physical_l4/base/6_finish.rpt`
- stage: `finish`
- startpoint: `rst_n (input port clocked by clk)`
- endpoint: `u_temporal/emit_value_q[250]$_DFFE_PN0P_`
- path_group: `asynchronous`
- path_type: `max`
- slack: `9.4800`
- data_arrival_time: `3.2100`
- data_required_time: `12.6900`

```text
Startpoint: rst_n (input port clocked by clk)
Endpoint: u_temporal/emit_value_q[250]$_DFFE_PN0P_
          (recovery check against rising-edge clock clk)
Path Group: asynchronous
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (propagated)
                          2.00    2.00 ^ input external delay
     1    5.78    0.00    0.00    2.00 ^ rst_n (in)
                                         rst_n (net)
                  0.00    0.00    2.00 ^ input4277/A (CLKBUF_X3)
    14   44.15    0.03    0.05    2.05 ^ input4277/Z (CLKBUF_X3)
                                         net4276 (net)
                  0.04    0.02    2.07 ^ place27408/A (BUF_X1)
     1    1.07    0.01    0.03    2.10 ^ place27408/Z (BUF_X1)
                                         net27407 (net)
                  0.01    0.00    2.10 ^ place27409/A (BUF_X1)
     1    1.60    0.01    0.02    2.12 ^ place27409/Z (BUF_X1)
                                         net27408 (net)
                  0.01    0.00    2.12 ^ wire28030/A (CLKBUF_X3)
     4   39.43    0.02    0.05    2.16 ^ wire28030/Z (CLKBUF_X3)
...
                                         clknet_5_1_0_clk_regs (net)
                  0.02    0.00   12.53 ^ clkbuf_7_6__f_clk_regs/A (CLKBUF_X3)
    15   45.35    0.04    0.07   12.59 ^ clkbuf_7_6__f_clk_regs/Z (CLKBUF_X3)
                                         clknet_7_6__leaf_clk_regs (net)
                  0.04    0.00   12.60 ^ clkbuf_leaf_1334_clk_regs/A (CLKBUF_X3)
     7    9.72    0.01    0.05   12.64 ^ clkbuf_leaf_1334_clk_regs/Z (CLKBUF_X3)
                                         clknet_leaf_1334_clk_regs (net)
                  0.01    0.00   12.64 ^ u_temporal/emit_value_q[250]$_DFFE_PN0P_/CK (DFFR_X1)
                          0.00   12.64   clock reconvergence pessimism
                          0.05   12.69   library recovery time
                                 12.69   data required time
-----------------------------------------------------------------------------
                                 12.69   data required time
                                 -3.21   data arrival time
-----------------------------------------------------------------------------
                                  9.48   slack (MET)
```


## Worst Timing Paths Across All Stages

### Path 1

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_partial_temporal_finalizer_physical_l4/base/2_floorplan_final.rpt`
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
                                         u_finalizer/_12087_ (net)
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

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_partial_temporal_finalizer_physical_l4/base/3_detailed_place.rpt`
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
                                         u_finalizer/_12087_ (net)
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

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_partial_temporal_finalizer_physical_l4/base/3_global_place.rpt`
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
                                         u_finalizer/_12087_ (net)
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

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_partial_temporal_finalizer_physical_l4/base/3_resizer.rpt`
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
                                         u_finalizer/_12087_ (net)
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

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_partial_temporal_finalizer_physical_l4/base/4_cts_final.rpt`
- stage: `cts`
- startpoint: `u_finalizer/cycle_count[0]$_DFF_PN0_`
- endpoint: `u_finalizer/cycle_count[0]$_DFF_PN0_`
- path_group: `clk`
- path_type: `min`
- slack: `0.0600`
- data_arrival_time: `0.7600`
- data_required_time: `0.7000`

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
     1   16.57    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.00    0.00    0.00 ^ wire28039/A (BUF_X8)
     1   70.67    0.02    0.03    0.03 ^ wire28039/Z (BUF_X8)
                                         net28038 (net)
                  0.04    0.03    0.06 ^ wire28038/A (BUF_X16)
     1   72.88    0.01    0.03    0.09 ^ wire28038/Z (BUF_X16)
                                         net28037 (net)
                  0.03    0.03    0.11 ^ wire28037/A (BUF_X16)
     2   23.35    0.01    0.03    0.14 ^ wire28037/Z (BUF_X16)
                                         net28036 (net)
                  0.01    0.00    0.14 ^ clkbuf_regs_0_clk/A (CLKBUF_X3)
     1    2.03    0.01    0.03    0.17 ^ clkbuf_regs_0_clk/Z (CLKBUF_X3)
...
                                         clknet_7_77__leaf_clk_regs (net)
                  0.03    0.00    0.65 ^ clkbuf_leaf_818_clk_regs/A (CLKBUF_X3)
     7    8.77    0.01    0.04    0.69 ^ clkbuf_leaf_818_clk_regs/Z (CLKBUF_X3)
                                         clknet_leaf_818_clk_regs (net)
                  0.01    0.00    0.69 ^ u_finalizer/cycle_count[0]$_DFF_PN0_/CK (DFFR_X1)
                          0.00    0.69   clock reconvergence pessimism
                          0.01    0.70   library hold time
                                  0.70   data required time
-----------------------------------------------------------------------------
                                  0.70   data required time
                                 -0.76   data arrival time
-----------------------------------------------------------------------------
                                  0.06   slack (MET)



```

### Path 6

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_partial_temporal_finalizer_physical_l4/base/5_global_route.rpt`
- stage: `route`
- startpoint: `u_temporal/u_pair_merge/cycle_count[0]$_DFF_PN0_`
- endpoint: `u_temporal/u_pair_merge/cycle_count[0]$_DFF_PN0_`
- path_group: `clk`
- path_type: `min`
- slack: `0.0600`
- data_arrival_time: `0.7700`
- data_required_time: `0.7000`

```text
Startpoint: u_temporal/u_pair_merge/cycle_count[0]$_DFF_PN0_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: u_temporal/u_pair_merge/cycle_count[0]$_DFF_PN0_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   16.26    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.00    0.00    0.00 ^ wire28039/A (BUF_X8)
     1   70.15    0.01    0.02    0.03 ^ wire28039/Z (BUF_X8)
                                         net28038 (net)
                  0.04    0.03    0.06 ^ wire28038/A (BUF_X16)
     1   72.10    0.01    0.03    0.08 ^ wire28038/Z (BUF_X16)
                                         net28037 (net)
                  0.04    0.03    0.11 ^ wire28037/A (BUF_X16)
     2   23.46    0.01    0.03    0.14 ^ wire28037/Z (BUF_X16)
                                         net28036 (net)
                  0.01    0.00    0.14 ^ clkbuf_regs_0_clk/A (CLKBUF_X3)
     1    2.50    0.01    0.03    0.17 ^ clkbuf_regs_0_clk/Z (CLKBUF_X3)
...
                                         clknet_7_78__leaf_clk_regs (net)
                  0.03    0.00    0.65 ^ clkbuf_leaf_826_clk_regs/A (CLKBUF_X3)
     7    9.06    0.01    0.04    0.70 ^ clkbuf_leaf_826_clk_regs/Z (CLKBUF_X3)
                                         clknet_leaf_826_clk_regs (net)
                  0.01    0.00    0.70 ^ u_temporal/u_pair_merge/cycle_count[0]$_DFF_PN0_/CK (DFFR_X1)
                          0.00    0.70   clock reconvergence pessimism
                          0.01    0.70   library hold time
                                  0.70   data required time
-----------------------------------------------------------------------------
                                  0.70   data required time
                                 -0.77   data arrival time
-----------------------------------------------------------------------------
                                  0.06   slack (MET)



```

### Path 7

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_partial_temporal_finalizer_physical_l4/base/6_finish.rpt`
- stage: `finish`
- startpoint: `u_finalizer/cycle_count[0]$_DFF_PN0_`
- endpoint: `u_finalizer/cycle_count[0]$_DFF_PN0_`
- path_group: `clk`
- path_type: `min`
- slack: `0.0600`
- data_arrival_time: `0.6800`
- data_required_time: `0.6200`

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
     1   12.57    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.00    0.00    0.00 ^ wire28039/A (BUF_X8)
     1   53.01    0.01    0.02    0.02 ^ wire28039/Z (BUF_X8)
                                         net28038 (net)
                  0.03    0.02    0.05 ^ wire28038/A (BUF_X16)
     1   56.17    0.01    0.03    0.07 ^ wire28038/Z (BUF_X16)
                                         net28037 (net)
                  0.03    0.02    0.10 ^ wire28037/A (BUF_X16)
     2   19.38    0.01    0.03    0.12 ^ wire28037/Z (BUF_X16)
                                         net28036 (net)
                  0.01    0.00    0.13 ^ clkbuf_regs_0_clk/A (CLKBUF_X3)
     1    1.95    0.01    0.03    0.15 ^ clkbuf_regs_0_clk/Z (CLKBUF_X3)
...
                                         clknet_7_77__leaf_clk_regs (net)
                  0.02    0.00    0.57 ^ clkbuf_leaf_818_clk_regs/A (CLKBUF_X3)
     7    8.51    0.01    0.04    0.61 ^ clkbuf_leaf_818_clk_regs/Z (CLKBUF_X3)
                                         clknet_leaf_818_clk_regs (net)
                  0.01    0.00    0.61 ^ u_finalizer/cycle_count[0]$_DFF_PN0_/CK (DFFR_X1)
                          0.00    0.61   clock reconvergence pessimism
                          0.01    0.62   library hold time
                                  0.62   data required time
-----------------------------------------------------------------------------
                                  0.62   data required time
                                 -0.68   data arrival time
-----------------------------------------------------------------------------
                                  0.06   slack (MET)



```

### Path 8

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_partial_temporal_finalizer_physical_l4/base/3_global_place.rpt`
- stage: `global_place`
- startpoint: `u_temporal/u_pair_merge/left_global_max_hold_q[31]$_DFFE_PN0P_`
- endpoint: `u_temporal/u_state_memory/protocol_error_q$_DFF_PN0_`
- path_group: `clk`
- path_type: `max`
- slack: `0.9400`
- data_arrival_time: `11.0200`
- data_required_time: `11.9600`

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
     2    4.75    0.02    0.11    0.11 ^ u_temporal/u_pair_merge/left_global_max_hold_q[31]$_DFFE_PN0P_/Q (DFFR_X1)
                                         u_temporal/u_pair_merge/left_global_max_hold_q[31] (net)
                  0.02    0.00    0.11 ^ u_temporal/u_pair_merge/_208404_/A (HA_X1)
     1    3.09    0.03    0.06    0.16 ^ u_temporal/u_pair_merge/_208404_/S (HA_X1)
                                         u_temporal/u_pair_merge/_050953_ (net)
                  0.03    0.00    0.16 ^ place26651/A (BUF_X1)
    10   18.49    0.04    0.07    0.23 ^ place26651/Z (BUF_X1)
                                         net26650 (net)
                  0.04    0.00    0.23 ^ u_temporal/u_pair_merge/_119334_/A1 (NAND2_X1)
     2    4.16    0.02    0.03    0.26 v u_temporal/u_pair_merge/_119334_/ZN (NAND2_X1)
                                         u_temporal/u_pair_merge/_072721_ (net)
                  0.02    0.00    0.26 v u_temporal/u_pair_merge/_119349_/A2 (OR2_X1)
...
                                 11.02   data arrival time

                  0.00   12.00   12.00   clock clk (rise edge)
                          0.00   12.00   clock network delay (ideal)
                          0.00   12.00   clock reconvergence pessimism
                                 12.00 ^ u_temporal/u_state_memory/protocol_error_q$_DFF_PN0_/CK (DFFR_X1)
                         -0.04   11.96   library setup time
                                 11.96   data required time
-----------------------------------------------------------------------------
                                 11.96   data required time
                                -11.02   data arrival time
-----------------------------------------------------------------------------
                                  0.94   slack (MET)



```
