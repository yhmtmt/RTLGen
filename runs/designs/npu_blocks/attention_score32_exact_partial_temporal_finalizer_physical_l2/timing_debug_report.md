# OpenROAD Timing Debug Summary

- design_dir: `runs/designs/npu_blocks/attention_score32_exact_partial_temporal_finalizer_physical_l2`
- metrics_path: `runs/designs/npu_blocks/attention_score32_exact_partial_temporal_finalizer_physical_l2/metrics.csv`
- rows_considered: 1

## Metrics Rows

| param_hash | tag | status | critical_path_ns | density | result_path |
| --- | --- | --- | ---: | ---: | --- |
| 7d5d9129 | attention_exact_partial_temporal_finalizer_12ns_v1_7d5d9129 | ok | 11.4771 | 0.4 | `/orfs/flow/reports/nangate45/attention_score32_exact_partial_temporal_finalizer_physical_l2/base/6_finish.rpt` |

## Inspected Report Files

- `/orfs/flow/reports/nangate45/attention_score32_exact_partial_temporal_finalizer_physical_l2/base/6_finish.rpt`
- `/orfs/flow/reports/nangate45/attention_score32_exact_partial_temporal_finalizer_physical_l2/base/5_global_route.rpt`
- `/orfs/flow/reports/nangate45/attention_score32_exact_partial_temporal_finalizer_physical_l2/base/5_route_drc.rpt`
- `/orfs/flow/reports/nangate45/attention_score32_exact_partial_temporal_finalizer_physical_l2/base/5_route_drc.rpt-10.rpt`
- `/orfs/flow/reports/nangate45/attention_score32_exact_partial_temporal_finalizer_physical_l2/base/5_route_drc.rpt-5.rpt`
- `/orfs/flow/reports/nangate45/attention_score32_exact_partial_temporal_finalizer_physical_l2/base/4_cts_final.rpt`
- `/orfs/flow/reports/nangate45/attention_score32_exact_partial_temporal_finalizer_physical_l2/base/3_resizer.rpt`
- `/orfs/flow/reports/nangate45/attention_score32_exact_partial_temporal_finalizer_physical_l2/base/3_detailed_place.rpt`
- `/orfs/flow/reports/nangate45/attention_score32_exact_partial_temporal_finalizer_physical_l2/base/3_global_place.rpt`
- `/orfs/flow/reports/nangate45/attention_score32_exact_partial_temporal_finalizer_physical_l2/base/2_floorplan_final.rpt`
- `/orfs/flow/reports/nangate45/attention_score32_exact_partial_temporal_finalizer_physical_l2/base/drt_antennas.log`
- `/orfs/flow/reports/nangate45/attention_score32_exact_partial_temporal_finalizer_physical_l2/base/grt_antennas.log`
- `/orfs/flow/reports/nangate45/attention_score32_exact_partial_temporal_finalizer_physical_l2/base/metadata-generate.log`

## Preferred Final-Stage Timing Paths

- raw_path_block_count: 52
- unique_path_block_count: 28
- preferred_stage: `finish`

### Path 1

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_partial_temporal_finalizer_physical_l2/base/6_finish.rpt`
- stage: `finish`
- startpoint: `u_temporal/cycle_count_q[0]$_DFF_PN0_`
- endpoint: `u_temporal/cycle_count_q[0]$_DFF_PN0_`
- path_group: `clk`
- path_type: `min`
- slack: `0.0600`
- data_arrival_time: `0.6500`
- data_required_time: `0.5900`

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
     1   35.38    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.01    0.01    0.01 ^ wire27678/A (BUF_X8)
     1   38.77    0.01    0.02    0.03 ^ wire27678/Z (BUF_X8)
                                         net27677 (net)
                  0.02    0.01    0.05 ^ wire27677/A (BUF_X16)
     1   56.76    0.01    0.02    0.07 ^ wire27677/Z (BUF_X16)
                                         net27676 (net)
                  0.03    0.03    0.10 ^ wire27676/A (BUF_X16)
     2   18.84    0.01    0.03    0.12 ^ wire27676/Z (BUF_X16)
                                         net27675 (net)
                  0.01    0.00    0.12 ^ clkbuf_regs_0_clk/A (CLKBUF_X3)
     1    1.54    0.01    0.03    0.15 ^ clkbuf_regs_0_clk/Z (CLKBUF_X3)
...
                                         clknet_7_109__leaf_clk_regs (net)
                  0.02    0.00    0.54 ^ clkbuf_leaf_469_clk_regs/A (CLKBUF_X3)
     7    9.66    0.01    0.04    0.58 ^ clkbuf_leaf_469_clk_regs/Z (CLKBUF_X3)
                                         clknet_leaf_469_clk_regs (net)
                  0.01    0.00    0.58 ^ u_temporal/cycle_count_q[0]$_DFF_PN0_/CK (DFFR_X1)
                          0.00    0.58   clock reconvergence pessimism
                          0.01    0.59   library hold time
                                  0.59   data required time
-----------------------------------------------------------------------------
                                  0.59   data required time
                                 -0.65   data arrival time
-----------------------------------------------------------------------------
                                  0.06   slack (MET)



```

### Path 2

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_partial_temporal_finalizer_physical_l2/base/6_finish.rpt`
- stage: `finish`
- startpoint: `u_temporal/u_pair_merge/left_global_max_hold_q[31]$_DFFE_PN0P_`
- endpoint: `u_temporal/u_state_memory/protocol_error_q$_DFF_PN0_`
- path_group: `clk`
- path_type: `max`
- slack: `1.0800`
- data_arrival_time: `11.4800`
- data_required_time: `12.5600`

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
     1   35.38    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.01    0.01    0.01 ^ wire27678/A (BUF_X8)
     1   38.77    0.01    0.02    0.03 ^ wire27678/Z (BUF_X8)
                                         net27677 (net)
                  0.02    0.01    0.05 ^ wire27677/A (BUF_X16)
     1   56.76    0.01    0.02    0.07 ^ wire27677/Z (BUF_X16)
                                         net27676 (net)
                  0.03    0.03    0.10 ^ wire27676/A (BUF_X16)
     2   18.84    0.01    0.03    0.12 ^ wire27676/Z (BUF_X16)
                                         net27675 (net)
                  0.01    0.00    0.12 ^ clkbuf_regs_0_clk/A (CLKBUF_X3)
     1    1.54    0.01    0.03    0.15 ^ clkbuf_regs_0_clk/Z (CLKBUF_X3)
...
                                         clknet_7_65__leaf_clk_regs (net)
                  0.02    0.00   12.56 ^ clkbuf_leaf_1028_clk_regs/A (CLKBUF_X3)
     7    9.86    0.01    0.04   12.60 ^ clkbuf_leaf_1028_clk_regs/Z (CLKBUF_X3)
                                         clknet_leaf_1028_clk_regs (net)
                  0.01    0.00   12.60 ^ u_temporal/u_state_memory/protocol_error_q$_DFF_PN0_/CK (DFFR_X1)
                          0.00   12.60   clock reconvergence pessimism
                         -0.04   12.56   library setup time
                                 12.56   data required time
-----------------------------------------------------------------------------
                                 12.56   data required time
                                -11.48   data arrival time
-----------------------------------------------------------------------------
                                  1.08   slack (MET)



```

### Path 3

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_partial_temporal_finalizer_physical_l2/base/6_finish.rpt`
- stage: `finish`
- startpoint: `rst_n (input port clocked by clk)`
- endpoint: `u_temporal/u_state_memory/request_count[24]$_DFFE_PN0P_`
- path_group: `asynchronous`
- path_type: `min`
- slack: `1.2000`
- data_arrival_time: `2.0700`
- data_required_time: `0.8600`

```text
Startpoint: rst_n (input port clocked by clk)
Endpoint: u_temporal/u_state_memory/request_count[24]$_DFFE_PN0P_
          (removal check against rising-edge clock clk)
Path Group: asynchronous
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (propagated)
                          2.00    2.00 ^ input external delay
     1    8.95    0.00    0.00    2.00 ^ rst_n (in)
                                         rst_n (net)
                  0.00    0.00    2.00 ^ input4277/A (CLKBUF_X3)
    12   41.00    0.02    0.04    2.04 ^ input4277/Z (CLKBUF_X3)
                                         net4276 (net)
                  0.04    0.02    2.07 ^ u_temporal/u_state_memory/request_count[24]$_DFFE_PN0P_/RN (DFFR_X1)
                                  2.07   data arrival time

                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   35.38    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.01    0.01    0.01 ^ wire27678/A (BUF_X8)
...
                                         clknet_6_47_0_clk_regs (net)
                  0.01    0.00    0.52 ^ clkbuf_7_94__f_clk_regs/A (CLKBUF_X3)
     8   37.57    0.03    0.06    0.58 ^ clkbuf_7_94__f_clk_regs/Z (CLKBUF_X3)
                                         clknet_7_94__leaf_clk_regs (net)
                  0.03    0.01    0.58 ^ clkbuf_leaf_769_clk_regs/A (CLKBUF_X3)
     7    9.25    0.01    0.04    0.63 ^ clkbuf_leaf_769_clk_regs/Z (CLKBUF_X3)
                                         clknet_leaf_769_clk_regs (net)
                  0.01    0.00    0.63 ^ u_temporal/u_state_memory/request_count[24]$_DFFE_PN0P_/CK (DFFR_X1)
                          0.00    0.63   clock reconvergence pessimism
                          0.24    0.86   library removal time
                                  0.86   data required time
-----------------------------------------------------------------------------
                                  0.86   data required time
                                 -2.07   data arrival time
-----------------------------------------------------------------------------
                                  1.20   slack (MET)
```

### Path 4

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_partial_temporal_finalizer_physical_l2/base/6_finish.rpt`
- stage: `finish`
- startpoint: `rst_n (input port clocked by clk)`
- endpoint: `u_temporal/completed_head_count_q[17]$_DFFE_PN0P_`
- path_group: `asynchronous`
- path_type: `max`
- slack: `9.1500`
- data_arrival_time: `3.5100`
- data_required_time: `12.6500`

```text
Startpoint: rst_n (input port clocked by clk)
Endpoint: u_temporal/completed_head_count_q[17]$_DFFE_PN0P_
          (recovery check against rising-edge clock clk)
Path Group: asynchronous
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (propagated)
                          2.00    2.00 ^ input external delay
     1    8.95    0.00    0.00    2.00 ^ rst_n (in)
                                         rst_n (net)
                  0.00    0.00    2.00 ^ input4277/A (CLKBUF_X3)
    12   41.00    0.02    0.04    2.04 ^ input4277/Z (CLKBUF_X3)
                                         net4276 (net)
                  0.04    0.02    2.07 ^ load_slew27675/A (BUF_X4)
     5   39.73    0.02    0.04    2.11 ^ load_slew27675/Z (BUF_X4)
                                         net27674 (net)
                  0.03    0.01    2.12 ^ wire27674/A (CLKBUF_X3)
     2   41.58    0.02    0.05    2.17 ^ wire27674/Z (CLKBUF_X3)
                                         net27673 (net)
                  0.05    0.03    2.20 ^ place27149/A (BUF_X2)
     1    2.37    0.01    0.03    2.23 ^ place27149/Z (BUF_X2)
...
                                         clknet_6_31_0_clk_regs (net)
                  0.01    0.00   12.50 ^ clkbuf_7_62__f_clk_regs/A (CLKBUF_X3)
    16   40.09    0.03    0.06   12.56 ^ clkbuf_7_62__f_clk_regs/Z (CLKBUF_X3)
                                         clknet_7_62__leaf_clk_regs (net)
                  0.03    0.00   12.56 ^ clkbuf_leaf_512_clk_regs/A (CLKBUF_X3)
     7   10.51    0.01    0.04   12.61 ^ clkbuf_leaf_512_clk_regs/Z (CLKBUF_X3)
                                         clknet_leaf_512_clk_regs (net)
                  0.01    0.00   12.61 ^ u_temporal/completed_head_count_q[17]$_DFFE_PN0P_/CK (DFFR_X1)
                          0.00   12.61   clock reconvergence pessimism
                          0.05   12.65   library recovery time
                                 12.65   data required time
-----------------------------------------------------------------------------
                                 12.65   data required time
                                 -3.51   data arrival time
-----------------------------------------------------------------------------
                                  9.15   slack (MET)
```


## Worst Timing Paths Across All Stages

### Path 1

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_partial_temporal_finalizer_physical_l2/base/2_floorplan_final.rpt`
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
                                         u_finalizer/_08144_ (net)
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

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_partial_temporal_finalizer_physical_l2/base/3_detailed_place.rpt`
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
                                         u_finalizer/_08144_ (net)
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

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_partial_temporal_finalizer_physical_l2/base/3_global_place.rpt`
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
                                         u_finalizer/_08144_ (net)
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

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_partial_temporal_finalizer_physical_l2/base/3_resizer.rpt`
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
                                         u_finalizer/_08144_ (net)
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

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_partial_temporal_finalizer_physical_l2/base/4_cts_final.rpt`
- stage: `cts`
- startpoint: `u_temporal/u_pair_merge/cycle_count[0]$_DFF_PN0_`
- endpoint: `u_temporal/u_pair_merge/cycle_count[0]$_DFF_PN0_`
- path_group: `clk`
- path_type: `min`
- slack: `0.0600`
- data_arrival_time: `0.7300`
- data_required_time: `0.6700`

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
     1   48.41    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.01    0.01    0.01 ^ wire27678/A (BUF_X8)
     1   50.61    0.01    0.03    0.04 ^ wire27678/Z (BUF_X8)
                                         net27677 (net)
                  0.02    0.01    0.05 ^ wire27677/A (BUF_X16)
     1   73.06    0.01    0.03    0.08 ^ wire27677/Z (BUF_X16)
                                         net27676 (net)
                  0.03    0.03    0.11 ^ wire27676/A (BUF_X16)
     2   22.21    0.01    0.03    0.14 ^ wire27676/Z (BUF_X16)
                                         net27675 (net)
                  0.01    0.00    0.14 ^ clkbuf_regs_0_clk/A (CLKBUF_X3)
     1    1.65    0.01    0.03    0.16 ^ clkbuf_regs_0_clk/Z (CLKBUF_X3)
...
                                         clknet_7_111__leaf_clk_regs (net)
                  0.02    0.00    0.62 ^ clkbuf_leaf_759_clk_regs/A (CLKBUF_X3)
     7    8.69    0.01    0.04    0.66 ^ clkbuf_leaf_759_clk_regs/Z (CLKBUF_X3)
                                         clknet_leaf_759_clk_regs (net)
                  0.01    0.00    0.66 ^ u_temporal/u_pair_merge/cycle_count[0]$_DFF_PN0_/CK (DFFR_X1)
                          0.00    0.66   clock reconvergence pessimism
                          0.01    0.67   library hold time
                                  0.67   data required time
-----------------------------------------------------------------------------
                                  0.67   data required time
                                 -0.73   data arrival time
-----------------------------------------------------------------------------
                                  0.06   slack (MET)



```

### Path 6

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_partial_temporal_finalizer_physical_l2/base/5_global_route.rpt`
- stage: `route`
- startpoint: `u_temporal/cycle_count_q[0]$_DFF_PN0_`
- endpoint: `u_temporal/cycle_count_q[0]$_DFF_PN0_`
- path_group: `clk`
- path_type: `min`
- slack: `0.0600`
- data_arrival_time: `0.7200`
- data_required_time: `0.6600`

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
     1   48.29    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.01    0.01    0.01 ^ wire27678/A (BUF_X8)
     1   50.22    0.01    0.03    0.04 ^ wire27678/Z (BUF_X8)
                                         net27677 (net)
                  0.02    0.02    0.05 ^ wire27677/A (BUF_X16)
     1   72.65    0.01    0.03    0.08 ^ wire27677/Z (BUF_X16)
                                         net27676 (net)
                  0.04    0.03    0.11 ^ wire27676/A (BUF_X16)
     2   21.93    0.01    0.03    0.14 ^ wire27676/Z (BUF_X16)
                                         net27675 (net)
                  0.01    0.00    0.14 ^ clkbuf_regs_0_clk/A (CLKBUF_X3)
     1    1.76    0.01    0.03    0.17 ^ clkbuf_regs_0_clk/Z (CLKBUF_X3)
...
                                         clknet_7_109__leaf_clk_regs (net)
                  0.02    0.00    0.61 ^ clkbuf_leaf_469_clk_regs/A (CLKBUF_X3)
     7    9.88    0.01    0.04    0.65 ^ clkbuf_leaf_469_clk_regs/Z (CLKBUF_X3)
                                         clknet_leaf_469_clk_regs (net)
                  0.01    0.00    0.65 ^ u_temporal/cycle_count_q[0]$_DFF_PN0_/CK (DFFR_X1)
                          0.00    0.65   clock reconvergence pessimism
                          0.01    0.66   library hold time
                                  0.66   data required time
-----------------------------------------------------------------------------
                                  0.66   data required time
                                 -0.72   data arrival time
-----------------------------------------------------------------------------
                                  0.06   slack (MET)



```

### Path 7

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_partial_temporal_finalizer_physical_l2/base/6_finish.rpt`
- stage: `finish`
- startpoint: `u_temporal/cycle_count_q[0]$_DFF_PN0_`
- endpoint: `u_temporal/cycle_count_q[0]$_DFF_PN0_`
- path_group: `clk`
- path_type: `min`
- slack: `0.0600`
- data_arrival_time: `0.6500`
- data_required_time: `0.5900`

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
     1   35.38    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.01    0.01    0.01 ^ wire27678/A (BUF_X8)
     1   38.77    0.01    0.02    0.03 ^ wire27678/Z (BUF_X8)
                                         net27677 (net)
                  0.02    0.01    0.05 ^ wire27677/A (BUF_X16)
     1   56.76    0.01    0.02    0.07 ^ wire27677/Z (BUF_X16)
                                         net27676 (net)
                  0.03    0.03    0.10 ^ wire27676/A (BUF_X16)
     2   18.84    0.01    0.03    0.12 ^ wire27676/Z (BUF_X16)
                                         net27675 (net)
                  0.01    0.00    0.12 ^ clkbuf_regs_0_clk/A (CLKBUF_X3)
     1    1.54    0.01    0.03    0.15 ^ clkbuf_regs_0_clk/Z (CLKBUF_X3)
...
                                         clknet_7_109__leaf_clk_regs (net)
                  0.02    0.00    0.54 ^ clkbuf_leaf_469_clk_regs/A (CLKBUF_X3)
     7    9.66    0.01    0.04    0.58 ^ clkbuf_leaf_469_clk_regs/Z (CLKBUF_X3)
                                         clknet_leaf_469_clk_regs (net)
                  0.01    0.00    0.58 ^ u_temporal/cycle_count_q[0]$_DFF_PN0_/CK (DFFR_X1)
                          0.00    0.58   clock reconvergence pessimism
                          0.01    0.59   library hold time
                                  0.59   data required time
-----------------------------------------------------------------------------
                                  0.59   data required time
                                 -0.65   data arrival time
-----------------------------------------------------------------------------
                                  0.06   slack (MET)



```

### Path 8

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_partial_temporal_finalizer_physical_l2/base/6_finish.rpt`
- stage: `finish`
- startpoint: `u_temporal/u_pair_merge/left_global_max_hold_q[31]$_DFFE_PN0P_`
- endpoint: `u_temporal/u_state_memory/protocol_error_q$_DFF_PN0_`
- path_group: `clk`
- path_type: `max`
- slack: `1.0800`
- data_arrival_time: `11.4800`
- data_required_time: `12.5600`

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
     1   35.38    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.01    0.01    0.01 ^ wire27678/A (BUF_X8)
     1   38.77    0.01    0.02    0.03 ^ wire27678/Z (BUF_X8)
                                         net27677 (net)
                  0.02    0.01    0.05 ^ wire27677/A (BUF_X16)
     1   56.76    0.01    0.02    0.07 ^ wire27677/Z (BUF_X16)
                                         net27676 (net)
                  0.03    0.03    0.10 ^ wire27676/A (BUF_X16)
     2   18.84    0.01    0.03    0.12 ^ wire27676/Z (BUF_X16)
                                         net27675 (net)
                  0.01    0.00    0.12 ^ clkbuf_regs_0_clk/A (CLKBUF_X3)
     1    1.54    0.01    0.03    0.15 ^ clkbuf_regs_0_clk/Z (CLKBUF_X3)
...
                                         clknet_7_65__leaf_clk_regs (net)
                  0.02    0.00   12.56 ^ clkbuf_leaf_1028_clk_regs/A (CLKBUF_X3)
     7    9.86    0.01    0.04   12.60 ^ clkbuf_leaf_1028_clk_regs/Z (CLKBUF_X3)
                                         clknet_leaf_1028_clk_regs (net)
                  0.01    0.00   12.60 ^ u_temporal/u_state_memory/protocol_error_q$_DFF_PN0_/CK (DFFR_X1)
                          0.00   12.60   clock reconvergence pessimism
                         -0.04   12.56   library setup time
                                 12.56   data required time
-----------------------------------------------------------------------------
                                 12.56   data required time
                                -11.48   data arrival time
-----------------------------------------------------------------------------
                                  1.08   slack (MET)



```
