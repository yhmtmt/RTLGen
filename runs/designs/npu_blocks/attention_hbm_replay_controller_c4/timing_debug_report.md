# OpenROAD Timing Debug Summary

- design_dir: `runs/designs/npu_blocks/attention_hbm_replay_controller_c4`
- metrics_path: `runs/designs/npu_blocks/attention_hbm_replay_controller_c4/metrics.csv`
- rows_considered: 3

## Metrics Rows

| param_hash | tag | status | critical_path_ns | density | result_path |
| --- | --- | --- | ---: | ---: | --- |
| 9422c7e7 | attention_hbm_replay_controller_frontier_9422c7e7 | ok | 2.2087 | 0.45 | `/orfs/flow/reports/nangate45/attention_hbm_replay_controller_c4/base/6_finish.rpt` |
| 855f34cb | attention_hbm_replay_controller_frontier_855f34cb | ok | 2.2238 | 0.45 | `/orfs/flow/reports/nangate45/attention_hbm_replay_controller_c4/base/6_finish.rpt` |
| 5168ba2a | attention_hbm_replay_controller_frontier_5168ba2a | ok | 2.2421 | 0.45 | `/orfs/flow/reports/nangate45/attention_hbm_replay_controller_c4/base/6_finish.rpt` |

## Inspected Report Files

- `/orfs/flow/reports/nangate45/attention_hbm_replay_controller_c4/base/6_finish.rpt`
- `/orfs/flow/reports/nangate45/attention_hbm_replay_controller_c4/base/5_global_route.rpt`
- `/orfs/flow/reports/nangate45/attention_hbm_replay_controller_c4/base/5_route_drc.rpt`
- `/orfs/flow/reports/nangate45/attention_hbm_replay_controller_c4/base/4_cts_final.rpt`
- `/orfs/flow/reports/nangate45/attention_hbm_replay_controller_c4/base/3_resizer.rpt`
- `/orfs/flow/reports/nangate45/attention_hbm_replay_controller_c4/base/3_detailed_place.rpt`
- `/orfs/flow/reports/nangate45/attention_hbm_replay_controller_c4/base/3_global_place.rpt`
- `/orfs/flow/reports/nangate45/attention_hbm_replay_controller_c4/base/2_floorplan_final.rpt`
- `/orfs/flow/reports/nangate45/attention_hbm_replay_controller_c4/base/drt_antennas.log`
- `/orfs/flow/reports/nangate45/attention_hbm_replay_controller_c4/base/grt_antennas.log`
- `/orfs/flow/reports/nangate45/attention_hbm_replay_controller_c4/base/metadata-generate.log`

## Preferred Final-Stage Timing Paths

- raw_path_block_count: 156
- unique_path_block_count: 33
- preferred_stage: `finish`

### Path 1

- source: `/orfs/flow/reports/nangate45/attention_hbm_replay_controller_c4/base/6_finish.rpt`
- stage: `finish`
- startpoint: `request_addr[1] (input port clocked by clk)`
- endpoint: `request_ready (output port clocked by clk)`
- path_group: `clk`
- path_type: `max`
- slack: `-3.2400`
- data_arrival_time: `2.2400`
- data_required_time: `-1.0000`

```text
Startpoint: request_addr[1] (input port clocked by clk)
Endpoint: request_ready (output port clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (propagated)
                          2.00    2.00 ^ input external delay
     1    2.11    0.00    0.00    2.00 ^ request_addr[1] (in)
                                         request_addr[1] (net)
                  0.00    0.00    2.00 ^ input21/A (BUF_X2)
     1    7.86    0.01    0.02    2.02 ^ input21/Z (BUF_X2)
                                         net20 (net)
                  0.01    0.00    2.02 ^ place2783/A (BUF_X8)
     6   26.53    0.01    0.03    2.05 ^ place2783/Z (BUF_X8)
                                         net2782 (net)
                  0.01    0.00    2.05 ^ _08045_/A (INV_X8)
     4    9.65    0.00    0.01    2.06 v _08045_/ZN (INV_X8)
                                         _01371_ (net)
                  0.00    0.00    2.06 v _08059_/A1 (NOR3_X4)
     1    6.47    0.03    0.03    2.09 ^ _08059_/ZN (NOR3_X4)
                                         _01385_ (net)
...
                  0.00    0.00    2.24 ^ request_ready (out)
                                  2.24   data arrival time

                          1.00    1.00   clock clk (rise edge)
                          0.00    1.00   clock network delay (propagated)
                          0.00    1.00   clock reconvergence pessimism
                         -2.00   -1.00   output external delay
                                 -1.00   data required time
-----------------------------------------------------------------------------
                                 -1.00   data required time
                                 -2.24   data arrival time
-----------------------------------------------------------------------------
                                 -3.24   slack (VIOLATED)



```

### Path 2

- source: `/orfs/flow/reports/nangate45/attention_hbm_replay_controller_c4/base/6_finish.rpt`
- stage: `finish`
- startpoint: `rst_n (input port clocked by clk)`
- endpoint: `response_addr[13]$_DFFE_PN0P_`
- path_group: `asynchronous`
- path_type: `max`
- slack: `-1.0800`
- data_arrival_time: `2.3100`
- data_required_time: `1.2300`

```text
Startpoint: rst_n (input port clocked by clk)
Endpoint: response_addr[13]$_DFFE_PN0P_
          (recovery check against rising-edge clock clk)
Path Group: asynchronous
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (propagated)
                          2.00    2.00 ^ input external delay
     1    1.85    0.00    0.00    2.00 ^ rst_n (in)
                                         rst_n (net)
                  0.00    0.00    2.00 ^ input51/A (CLKBUF_X3)
     6   24.47    0.02    0.04    2.04 ^ input51/Z (CLKBUF_X3)
                                         net50 (net)
                  0.02    0.01    2.05 ^ place2768/A (BUF_X1)
     3    7.32    0.02    0.04    2.09 ^ place2768/Z (BUF_X1)
                                         net2767 (net)
                  0.02    0.00    2.09 ^ place2769/A (BUF_X4)
    51  121.21    0.06    0.08    2.17 ^ place2769/Z (BUF_X4)
                                         net2768 (net)
                  0.07    0.02    2.18 ^ place2774/A (BUF_X1)
    20   42.43    0.10    0.13    2.31 ^ place2774/Z (BUF_X1)
...
                                         clknet_0_clk (net)
                  0.05    0.00    1.08 ^ clkbuf_4_13_0_clk/A (CLKBUF_X3)
    13   27.86    0.02    0.06    1.14 ^ clkbuf_4_13_0_clk/Z (CLKBUF_X3)
                                         clknet_4_13_0_clk (net)
                  0.02    0.00    1.14 ^ clkbuf_leaf_51_clk/A (CLKBUF_X3)
     8    9.47    0.01    0.04    1.19 ^ clkbuf_leaf_51_clk/Z (CLKBUF_X3)
                                         clknet_leaf_51_clk (net)
                  0.01    0.00    1.19 ^ response_addr[13]$_DFFE_PN0P_/CK (DFFR_X1)
                          0.00    1.19   clock reconvergence pessimism
                          0.04    1.23   library recovery time
                                  1.23   data required time
-----------------------------------------------------------------------------
                                  1.23   data required time
                                 -2.31   data arrival time
-----------------------------------------------------------------------------
                                 -1.08   slack (VIOLATED)
```

### Path 3

- source: `/orfs/flow/reports/nangate45/attention_hbm_replay_controller_c4/base/6_finish.rpt`
- stage: `finish`
- startpoint: `rr_ptr[1]$_DFFE_PN0N_`
- endpoint: `service_row_window[1][12]$_DFFE_PN0N_`
- path_group: `clk`
- path_type: `max`
- slack: `-0.1500`
- data_arrival_time: `1.3100`
- data_required_time: `1.1500`

```text
Startpoint: rr_ptr[1]$_DFFE_PN0N_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: service_row_window[1][12]$_DFFE_PN0N_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

  Delay    Time   Description
---------------------------------------------------------
   0.00    0.00   clock clk (rise edge)
   0.00    0.00   clock source latency
   0.00    0.00 ^ clk (in)
   0.08    0.08 ^ clkbuf_0_clk/Z (CLKBUF_X3)
   0.07    0.15 ^ clkbuf_4_4_0_clk/Z (CLKBUF_X3)
   0.04    0.19 ^ clkbuf_leaf_6_clk/Z (CLKBUF_X3)
   0.00    0.19 ^ rr_ptr[1]$_DFFE_PN0N_/CK (DFFR_X2)
   0.14    0.33 ^ rr_ptr[1]$_DFFE_PN0N_/Q (DFFR_X2)
   0.02    0.35 ^ place2739/Z (BUF_X4)
   0.02    0.37 ^ rebuffer2869/Z (BUF_X4)
   0.02    0.39 ^ rebuffer3348/Z (BUF_X1)
   0.02    0.41 ^ rebuffer2807/Z (BUF_X2)
   0.05    0.47 ^ _14697_/CO (HA_X1)
   0.03    0.49 ^ rebuffer3243/Z (BUF_X4)
   0.01    0.50 v _07911_/ZN (INV_X4)
...
   0.00    1.00 ^ clk (in)
   0.08    1.08 ^ clkbuf_0_clk/Z (CLKBUF_X3)
   0.07    1.14 ^ clkbuf_4_6_0_clk/Z (CLKBUF_X3)
   0.04    1.19 ^ clkbuf_leaf_46_clk/Z (CLKBUF_X3)
   0.00    1.19 ^ service_row_window[1][12]$_DFFE_PN0N_/CK (DFFR_X1)
   0.00    1.19   clock reconvergence pessimism
  -0.03    1.15   library setup time
           1.15   data required time
---------------------------------------------------------
           1.15   data required time
          -1.31   data arrival time
---------------------------------------------------------
          -0.15   slack (VIOLATED)



```

### Path 4

- source: `/orfs/flow/reports/nangate45/attention_hbm_replay_controller_c4/base/6_finish.rpt`
- stage: `finish`
- startpoint: `q_count[2][0]$_DFFE_PN0P_`
- endpoint: `q_count[2][0]$_DFFE_PN0P_`
- path_group: `clk`
- path_type: `min`
- slack: `0.1100`
- data_arrival_time: `0.3100`
- data_required_time: `0.2000`

```text
Startpoint: q_count[2][0]$_DFFE_PN0P_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: q_count[2][0]$_DFFE_PN0P_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   14.33    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.00    0.00    0.00 ^ clkbuf_0_clk/A (CLKBUF_X3)
    16   64.48    0.05    0.07    0.08 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.05    0.00    0.08 ^ clkbuf_4_4_0_clk/A (CLKBUF_X3)
     9   30.94    0.03    0.07    0.15 ^ clkbuf_4_4_0_clk/Z (CLKBUF_X3)
                                         clknet_4_4_0_clk (net)
                  0.03    0.00    0.15 ^ clkbuf_leaf_11_clk/A (CLKBUF_X3)
     7    9.69    0.01    0.04    0.19 ^ clkbuf_leaf_11_clk/Z (CLKBUF_X3)
                                         clknet_leaf_11_clk (net)
                  0.01    0.00    0.19 ^ q_count[2][0]$_DFFE_PN0P_/CK (DFFR_X1)
     2    5.18    0.02    0.08    0.27 ^ q_count[2][0]$_DFFE_PN0P_/QN (DFFR_X1)
...
                                         clknet_4_4_0_clk (net)
                  0.03    0.00    0.15 ^ clkbuf_leaf_11_clk/A (CLKBUF_X3)
     7    9.69    0.01    0.04    0.19 ^ clkbuf_leaf_11_clk/Z (CLKBUF_X3)
                                         clknet_leaf_11_clk (net)
                  0.01    0.00    0.19 ^ q_count[2][0]$_DFFE_PN0P_/CK (DFFR_X1)
                          0.00    0.19   clock reconvergence pessimism
                          0.01    0.20   library hold time
                                  0.20   data required time
-----------------------------------------------------------------------------
                                  0.20   data required time
                                 -0.31   data arrival time
-----------------------------------------------------------------------------
                                  0.11   slack (MET)



```

### Path 5

- source: `/orfs/flow/reports/nangate45/attention_hbm_replay_controller_c4/base/6_finish.rpt`
- stage: `finish`
- startpoint: `rst_n (input port clocked by clk)`
- endpoint: `q_tail[1][0]$_DFFE_PN0N_ (removal check against rising-edge clock clk)`
- path_group: `asynchronous`
- path_type: `min`
- slack: `1.6800`
- data_arrival_time: `2.0900`
- data_required_time: `0.4100`

```text
Startpoint: rst_n (input port clocked by clk)
Endpoint: q_tail[1][0]$_DFFE_PN0N_ (removal check against rising-edge clock clk)
Path Group: asynchronous
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (propagated)
                          2.00    2.00 ^ input external delay
     1    1.85    0.00    0.00    2.00 ^ rst_n (in)
                                         rst_n (net)
                  0.00    0.00    2.00 ^ input51/A (CLKBUF_X3)
     6   24.47    0.02    0.04    2.04 ^ input51/Z (CLKBUF_X3)
                                         net50 (net)
                  0.02    0.00    2.05 ^ place2765/A (BUF_X1)
     6   11.12    0.03    0.05    2.09 ^ place2765/Z (BUF_X1)
                                         net2764 (net)
                  0.03    0.00    2.09 ^ q_tail[1][0]$_DFFE_PN0N_/RN (DFFR_X1)
                                  2.09   data arrival time

                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   14.33    0.00    0.00    0.00 ^ clk (in)
...
                                         clknet_0_clk (net)
                  0.05    0.00    0.08 ^ clkbuf_4_8_0_clk/A (CLKBUF_X3)
    13   32.89    0.03    0.07    0.15 ^ clkbuf_4_8_0_clk/Z (CLKBUF_X3)
                                         clknet_4_8_0_clk (net)
                  0.03    0.00    0.15 ^ clkbuf_leaf_124_clk/A (CLKBUF_X3)
     6   10.55    0.01    0.04    0.19 ^ clkbuf_leaf_124_clk/Z (CLKBUF_X3)
                                         clknet_leaf_124_clk (net)
                  0.01    0.00    0.19 ^ q_tail[1][0]$_DFFE_PN0N_/CK (DFFR_X1)
                          0.00    0.19   clock reconvergence pessimism
                          0.22    0.41   library removal time
                                  0.41   data required time
-----------------------------------------------------------------------------
                                  0.41   data required time
                                 -2.09   data arrival time
-----------------------------------------------------------------------------
                                  1.68   slack (MET)
```


## Worst Timing Paths Across All Stages

### Path 1

- source: `/orfs/flow/reports/nangate45/attention_hbm_replay_controller_c4/base/3_detailed_place.rpt`
- stage: `detailed_place`
- startpoint: `request_addr[1] (input port clocked by clk)`
- endpoint: `request_ready (output port clocked by clk)`
- path_group: `clk`
- path_type: `max`
- slack: `-3.2600`
- data_arrival_time: `2.2600`
- data_required_time: `-1.0000`

```text
Startpoint: request_addr[1] (input port clocked by clk)
Endpoint: request_ready (output port clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                          2.00    2.00 ^ input external delay
     1    1.33    0.00    0.00    2.00 ^ request_addr[1] (in)
                                         request_addr[1] (net)
                  0.00    0.00    2.00 ^ input21/A (BUF_X1)
     1    7.89    0.02    0.03    2.03 ^ input21/Z (BUF_X1)
                                         net20 (net)
                  0.02    0.00    2.03 ^ place2783/A (BUF_X8)
     6   26.42    0.01    0.03    2.06 ^ place2783/Z (BUF_X8)
                                         net2782 (net)
                  0.01    0.00    2.06 ^ _08045_/A (INV_X8)
     4    9.76    0.00    0.01    2.07 v _08045_/ZN (INV_X8)
                                         _01371_ (net)
                  0.00    0.00    2.07 v _08059_/A1 (NOR3_X4)
     1    6.47    0.03    0.03    2.10 ^ _08059_/ZN (NOR3_X4)
                                         _01385_ (net)
...
                  0.00    0.00    2.26 ^ request_ready (out)
                                  2.26   data arrival time

                  0.00    1.00    1.00   clock clk (rise edge)
                          0.00    1.00   clock network delay (ideal)
                          0.00    1.00   clock reconvergence pessimism
                         -2.00   -1.00   output external delay
                                 -1.00   data required time
-----------------------------------------------------------------------------
                                 -1.00   data required time
                                 -2.26   data arrival time
-----------------------------------------------------------------------------
                                 -3.26   slack (VIOLATED)



```

### Path 2

- source: `/orfs/flow/reports/nangate45/attention_hbm_replay_controller_c4/base/3_resizer.rpt`
- stage: `resizer`
- startpoint: `request_addr[1] (input port clocked by clk)`
- endpoint: `request_ready (output port clocked by clk)`
- path_group: `clk`
- path_type: `max`
- slack: `-3.2600`
- data_arrival_time: `2.2600`
- data_required_time: `-1.0000`

```text
Startpoint: request_addr[1] (input port clocked by clk)
Endpoint: request_ready (output port clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                          2.00    2.00 ^ input external delay
     1    1.32    0.00    0.00    2.00 ^ request_addr[1] (in)
                                         request_addr[1] (net)
                  0.00    0.00    2.00 ^ input21/A (BUF_X1)
     1    7.80    0.02    0.03    2.03 ^ input21/Z (BUF_X1)
                                         net20 (net)
                  0.02    0.00    2.03 ^ place2783/A (BUF_X8)
     6   26.29    0.01    0.03    2.06 ^ place2783/Z (BUF_X8)
                                         net2782 (net)
                  0.01    0.00    2.06 ^ _08045_/A (INV_X8)
     4    9.72    0.00    0.01    2.07 v _08045_/ZN (INV_X8)
                                         _01371_ (net)
                  0.00    0.00    2.07 v _08059_/A1 (NOR3_X4)
     1    6.46    0.03    0.03    2.10 ^ _08059_/ZN (NOR3_X4)
                                         _01385_ (net)
...
                  0.00    0.00    2.26 ^ request_ready (out)
                                  2.26   data arrival time

                  0.00    1.00    1.00   clock clk (rise edge)
                          0.00    1.00   clock network delay (ideal)
                          0.00    1.00   clock reconvergence pessimism
                         -2.00   -1.00   output external delay
                                 -1.00   data required time
-----------------------------------------------------------------------------
                                 -1.00   data required time
                                 -2.26   data arrival time
-----------------------------------------------------------------------------
                                 -3.26   slack (VIOLATED)



```

### Path 3

- source: `/orfs/flow/reports/nangate45/attention_hbm_replay_controller_c4/base/4_cts_final.rpt`
- stage: `cts`
- startpoint: `request_addr[1] (input port clocked by clk)`
- endpoint: `request_ready (output port clocked by clk)`
- path_group: `clk`
- path_type: `max`
- slack: `-3.2400`
- data_arrival_time: `2.2400`
- data_required_time: `-1.0000`

```text
Startpoint: request_addr[1] (input port clocked by clk)
Endpoint: request_ready (output port clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (propagated)
                          2.00    2.00 ^ input external delay
     1    2.14    0.00    0.00    2.00 ^ request_addr[1] (in)
                                         request_addr[1] (net)
                  0.00    0.00    2.00 ^ input21/A (BUF_X2)
     1    7.89    0.01    0.02    2.02 ^ input21/Z (BUF_X2)
                                         net20 (net)
                  0.01    0.00    2.02 ^ place2783/A (BUF_X8)
     6   26.38    0.01    0.03    2.05 ^ place2783/Z (BUF_X8)
                                         net2782 (net)
                  0.01    0.00    2.05 ^ _08045_/A (INV_X8)
     4    9.61    0.00    0.01    2.06 v _08045_/ZN (INV_X8)
                                         _01371_ (net)
                  0.00    0.00    2.06 v _08059_/A1 (NOR3_X4)
     1    6.56    0.03    0.03    2.09 ^ _08059_/ZN (NOR3_X4)
                                         _01385_ (net)
...
                  0.00    0.00    2.24 ^ request_ready (out)
                                  2.24   data arrival time

                          1.00    1.00   clock clk (rise edge)
                          0.00    1.00   clock network delay (propagated)
                          0.00    1.00   clock reconvergence pessimism
                         -2.00   -1.00   output external delay
                                 -1.00   data required time
-----------------------------------------------------------------------------
                                 -1.00   data required time
                                 -2.24   data arrival time
-----------------------------------------------------------------------------
                                 -3.24   slack (VIOLATED)



```

### Path 4

- source: `/orfs/flow/reports/nangate45/attention_hbm_replay_controller_c4/base/5_global_route.rpt`
- stage: `route`
- startpoint: `request_addr[1] (input port clocked by clk)`
- endpoint: `request_ready (output port clocked by clk)`
- path_group: `clk`
- path_type: `max`
- slack: `-3.2400`
- data_arrival_time: `2.2400`
- data_required_time: `-1.0000`

```text
Startpoint: request_addr[1] (input port clocked by clk)
Endpoint: request_ready (output port clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (propagated)
                          2.00    2.00 ^ input external delay
     1    2.39    0.00    0.00    2.00 ^ request_addr[1] (in)
                                         request_addr[1] (net)
                  0.00    0.00    2.00 ^ input21/A (BUF_X2)
     1    7.71    0.01    0.02    2.02 ^ input21/Z (BUF_X2)
                                         net20 (net)
                  0.01    0.00    2.02 ^ place2783/A (BUF_X8)
     6   26.37    0.01    0.03    2.05 ^ place2783/Z (BUF_X8)
                                         net2782 (net)
                  0.01    0.00    2.05 ^ _08045_/A (INV_X8)
     4    9.94    0.00    0.01    2.06 v _08045_/ZN (INV_X8)
                                         _01371_ (net)
                  0.00    0.00    2.06 v _08059_/A1 (NOR3_X4)
     1    6.56    0.03    0.03    2.09 ^ _08059_/ZN (NOR3_X4)
                                         _01385_ (net)
...
                  0.00    0.00    2.24 ^ request_ready (out)
                                  2.24   data arrival time

                          1.00    1.00   clock clk (rise edge)
                          0.00    1.00   clock network delay (propagated)
                          0.00    1.00   clock reconvergence pessimism
                         -2.00   -1.00   output external delay
                                 -1.00   data required time
-----------------------------------------------------------------------------
                                 -1.00   data required time
                                 -2.24   data arrival time
-----------------------------------------------------------------------------
                                 -3.24   slack (VIOLATED)



```

### Path 5

- source: `/orfs/flow/reports/nangate45/attention_hbm_replay_controller_c4/base/6_finish.rpt`
- stage: `finish`
- startpoint: `request_addr[1] (input port clocked by clk)`
- endpoint: `request_ready (output port clocked by clk)`
- path_group: `clk`
- path_type: `max`
- slack: `-3.2400`
- data_arrival_time: `2.2400`
- data_required_time: `-1.0000`

```text
Startpoint: request_addr[1] (input port clocked by clk)
Endpoint: request_ready (output port clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (propagated)
                          2.00    2.00 ^ input external delay
     1    2.11    0.00    0.00    2.00 ^ request_addr[1] (in)
                                         request_addr[1] (net)
                  0.00    0.00    2.00 ^ input21/A (BUF_X2)
     1    7.86    0.01    0.02    2.02 ^ input21/Z (BUF_X2)
                                         net20 (net)
                  0.01    0.00    2.02 ^ place2783/A (BUF_X8)
     6   26.53    0.01    0.03    2.05 ^ place2783/Z (BUF_X8)
                                         net2782 (net)
                  0.01    0.00    2.05 ^ _08045_/A (INV_X8)
     4    9.65    0.00    0.01    2.06 v _08045_/ZN (INV_X8)
                                         _01371_ (net)
                  0.00    0.00    2.06 v _08059_/A1 (NOR3_X4)
     1    6.47    0.03    0.03    2.09 ^ _08059_/ZN (NOR3_X4)
                                         _01385_ (net)
...
                  0.00    0.00    2.24 ^ request_ready (out)
                                  2.24   data arrival time

                          1.00    1.00   clock clk (rise edge)
                          0.00    1.00   clock network delay (propagated)
                          0.00    1.00   clock reconvergence pessimism
                         -2.00   -1.00   output external delay
                                 -1.00   data required time
-----------------------------------------------------------------------------
                                 -1.00   data required time
                                 -2.24   data arrival time
-----------------------------------------------------------------------------
                                 -3.24   slack (VIOLATED)



```

### Path 6

- source: `/orfs/flow/reports/nangate45/attention_hbm_replay_controller_c4/base/2_floorplan_final.rpt`
- stage: `floorplan`
- startpoint: `request_addr[1] (input port clocked by clk)`
- endpoint: `request_ready (output port clocked by clk)`
- path_group: `clk`
- path_type: `max`
- slack: `-3.1700`
- data_arrival_time: `2.1700`
- data_required_time: `-1.0000`

```text
Startpoint: request_addr[1] (input port clocked by clk)
Endpoint: request_ready (output port clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                          2.00    2.00 ^ input external delay
     1   26.70    0.00    0.00    2.00 ^ request_addr[1] (in)
                                         request_addr[1] (net)
                  0.00    0.00    2.00 ^ _08044_/A (BUF_X32)
     6   24.92    0.01    0.02    2.02 ^ _08044_/Z (BUF_X32)
                                         _01370_ (net)
                  0.01    0.00    2.02 ^ _08045_/A (INV_X8)
     5   11.42    0.00    0.01    2.02 v _08045_/ZN (INV_X8)
                                         _01371_ (net)
                  0.00    0.00    2.02 v _08059_/A1 (NOR3_X4)
     1    6.35    0.03    0.03    2.05 ^ _08059_/ZN (NOR3_X4)
                                         _01385_ (net)
                  0.03    0.00    2.05 ^ _08060_/B1 (OAI21_X4)
     1    5.77    0.01    0.02    2.07 v _08060_/ZN (OAI21_X4)
                                         _01386_ (net)
...
                  0.01    0.00    2.17 ^ request_ready (out)
                                  2.17   data arrival time

                  0.00    1.00    1.00   clock clk (rise edge)
                          0.00    1.00   clock network delay (ideal)
                          0.00    1.00   clock reconvergence pessimism
                         -2.00   -1.00   output external delay
                                 -1.00   data required time
-----------------------------------------------------------------------------
                                 -1.00   data required time
                                 -2.17   data arrival time
-----------------------------------------------------------------------------
                                 -3.17   slack (VIOLATED)



```

### Path 7

- source: `/orfs/flow/reports/nangate45/attention_hbm_replay_controller_c4/base/3_global_place.rpt`
- stage: `global_place`
- startpoint: `request_addr[1] (input port clocked by clk)`
- endpoint: `q_count[2][2]$_DFFE_PN0P_`
- path_group: `clk`
- path_type: `max`
- slack: `-1.5500`
- data_arrival_time: `2.5100`
- data_required_time: `0.9600`

```text
Startpoint: request_addr[1] (input port clocked by clk)
Endpoint: q_count[2][2]$_DFFE_PN0P_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                          2.00    2.00 v input external delay
     1    1.22    0.00    0.00    2.00 v request_addr[1] (in)
                                         request_addr[1] (net)
                  0.00    0.00    2.00 v input21/A (BUF_X1)
     1    7.02    0.01    0.03    2.03 v input21/Z (BUF_X1)
                                         net20 (net)
                  0.01    0.00    2.03 v place2783/A (BUF_X8)
     6   23.30    0.01    0.03    2.06 v place2783/Z (BUF_X8)
                                         net2782 (net)
                  0.01    0.00    2.06 v _08045_/A (INV_X8)
     4   11.58    0.01    0.01    2.07 ^ _08045_/ZN (INV_X8)
                                         _01371_ (net)
                  0.01    0.00    2.07 ^ _08059_/A1 (NOR3_X4)
     1    5.66    0.01    0.01    2.08 v _08059_/ZN (NOR3_X4)
...
                                  2.51   data arrival time

                  0.00    1.00    1.00   clock clk (rise edge)
                          0.00    1.00   clock network delay (ideal)
                          0.00    1.00   clock reconvergence pessimism
                                  1.00 ^ q_count[2][2]$_DFFE_PN0P_/CK (DFFR_X1)
                         -0.04    0.96   library setup time
                                  0.96   data required time
-----------------------------------------------------------------------------
                                  0.96   data required time
                                 -2.51   data arrival time
-----------------------------------------------------------------------------
                                 -1.55   slack (VIOLATED)



```

### Path 8

- source: `/orfs/flow/reports/nangate45/attention_hbm_replay_controller_c4/base/3_detailed_place.rpt`
- stage: `detailed_place`
- startpoint: `rst_n (input port clocked by clk)`
- endpoint: `service_row_window[1][12]$_DFFE_PN0N_`
- path_group: `asynchronous`
- path_type: `max`
- slack: `-1.2700`
- data_arrival_time: `2.3100`
- data_required_time: `1.0400`

```text
Startpoint: rst_n (input port clocked by clk)
Endpoint: service_row_window[1][12]$_DFFE_PN0N_
          (recovery check against rising-edge clock clk)
Path Group: asynchronous
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                          2.00    2.00 ^ input external delay
     1    1.82    0.00    0.00    2.00 ^ rst_n (in)
                                         rst_n (net)
                  0.00    0.00    2.00 ^ input51/A (CLKBUF_X3)
     6   20.61    0.02    0.04    2.04 ^ input51/Z (CLKBUF_X3)
                                         net50 (net)
                  0.02    0.01    2.04 ^ place2768/A (BUF_X1)
     3    7.40    0.02    0.04    2.08 ^ place2768/Z (BUF_X1)
                                         net2767 (net)
                  0.02    0.00    2.08 ^ place2769/A (BUF_X4)
    51  120.30    0.07    0.08    2.17 ^ place2769/Z (BUF_X4)
                                         net2768 (net)
                  0.07    0.01    2.18 ^ place2774/A (BUF_X1)
    20   42.06    0.10    0.13    2.31 ^ place2774/Z (BUF_X1)
                                         net2773 (net)
                  0.10    0.00    2.31 ^ service_row_window[1][12]$_DFFE_PN0N_/RN (DFFR_X1)
                                  2.31   data arrival time

                  0.00    1.00    1.00   clock clk (rise edge)
                          0.00    1.00   clock network delay (ideal)
                          0.00    1.00   clock reconvergence pessimism
                                  1.00 ^ service_row_window[1][12]$_DFFE_PN0N_/CK (DFFR_X1)
                          0.04    1.04   library recovery time
                                  1.04   data required time
-----------------------------------------------------------------------------
                                  1.04   data required time
                                 -2.31   data arrival time
-----------------------------------------------------------------------------
                                 -1.27   slack (VIOLATED)
```
