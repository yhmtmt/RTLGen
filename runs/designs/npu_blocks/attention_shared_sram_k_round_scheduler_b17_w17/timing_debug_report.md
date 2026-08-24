# OpenROAD Timing Debug Summary

- design_dir: `runs/designs/npu_blocks/attention_shared_sram_k_round_scheduler_b17_w17`
- metrics_path: `runs/designs/npu_blocks/attention_shared_sram_k_round_scheduler_b17_w17/metrics.csv`
- rows_considered: 4

## Metrics Rows

| param_hash | tag | status | critical_path_ns | density | result_path |
| --- | --- | --- | ---: | ---: | --- |
| e820f91b | attention_shared_sram_k_round_scheduler_ppa_v1_e820f91b | ok | 3.8432 | 0.5 | `/orfs/flow/reports/nangate45/attention_shared_sram_k_round_scheduler_b17_w17/base/6_finish.rpt` |
| fd384b8e | attention_shared_sram_k_round_scheduler_ppa_v1_fd384b8e | ok | 3.8605 | 0.5 | `/orfs/flow/reports/nangate45/attention_shared_sram_k_round_scheduler_b17_w17/base/6_finish.rpt` |
| 13bdc83f | attention_shared_sram_k_round_scheduler_ppa_v1_13bdc83f | ok | 3.9061 | 0.5 | `/orfs/flow/reports/nangate45/attention_shared_sram_k_round_scheduler_b17_w17/base/6_finish.rpt` |
| f93ade3a | attention_shared_sram_k_round_scheduler_ppa_v1_f93ade3a | ok | 3.9520 | 0.5 | `/orfs/flow/reports/nangate45/attention_shared_sram_k_round_scheduler_b17_w17/base/6_finish.rpt` |

## Inspected Report Files

- `/orfs/flow/reports/nangate45/attention_shared_sram_k_round_scheduler_b17_w17/base/6_finish.rpt`
- `/orfs/flow/reports/nangate45/attention_shared_sram_k_round_scheduler_b17_w17/base/5_global_route.rpt`
- `/orfs/flow/reports/nangate45/attention_shared_sram_k_round_scheduler_b17_w17/base/5_route_drc.rpt`
- `/orfs/flow/reports/nangate45/attention_shared_sram_k_round_scheduler_b17_w17/base/5_route_drc.rpt-5.rpt`
- `/orfs/flow/reports/nangate45/attention_shared_sram_k_round_scheduler_b17_w17/base/4_cts_final.rpt`
- `/orfs/flow/reports/nangate45/attention_shared_sram_k_round_scheduler_b17_w17/base/3_resizer.rpt`
- `/orfs/flow/reports/nangate45/attention_shared_sram_k_round_scheduler_b17_w17/base/3_detailed_place.rpt`
- `/orfs/flow/reports/nangate45/attention_shared_sram_k_round_scheduler_b17_w17/base/3_global_place.rpt`
- `/orfs/flow/reports/nangate45/attention_shared_sram_k_round_scheduler_b17_w17/base/2_floorplan_final.rpt`
- `/orfs/flow/reports/nangate45/attention_shared_sram_k_round_scheduler_b17_w17/base/drt_antennas.log`
- `/orfs/flow/reports/nangate45/attention_shared_sram_k_round_scheduler_b17_w17/base/grt_antennas.log`
- `/orfs/flow/reports/nangate45/attention_shared_sram_k_round_scheduler_b17_w17/base/metadata-generate.log`

## Preferred Final-Stage Timing Paths

- raw_path_block_count: 208
- unique_path_block_count: 28
- preferred_stage: `finish`

### Path 1

- source: `/orfs/flow/reports/nangate45/attention_shared_sram_k_round_scheduler_b17_w17/base/6_finish.rpt`
- stage: `finish`
- startpoint: `cycle_q[0]$_DFFE_PN0P_`
- endpoint: `cycle_q[0]$_DFFE_PN0P_`
- path_group: `clk`
- path_type: `min`
- slack: `0.0900`
- data_arrival_time: `0.6700`
- data_required_time: `0.5800`

```text
Startpoint: cycle_q[0]$_DFFE_PN0P_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: cycle_q[0]$_DFFE_PN0P_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   45.34    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.02    0.02    0.02 ^ wire24470/A (BUF_X8)
     1   52.24    0.01    0.03    0.04 ^ wire24470/Z (BUF_X8)
                                         net24470 (net)
                  0.03    0.02    0.07 ^ clkbuf_0_clk/A (CLKBUF_X3)
     2   35.25    0.03    0.06    0.13 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.03    0.00    0.13 ^ clkbuf_1_1_0_clk/A (CLKBUF_X3)
     2   24.34    0.02    0.05    0.19 ^ clkbuf_1_1_0_clk/Z (CLKBUF_X3)
                                         clknet_1_1_0_clk (net)
                  0.02    0.00    0.19 ^ clkbuf_2_2_0_clk/A (CLKBUF_X3)
     2   23.65    0.02    0.05    0.24 ^ clkbuf_2_2_0_clk/Z (CLKBUF_X3)
...
                                         clknet_9_257__leaf_clk (net)
                  0.03    0.01    0.52 ^ clkbuf_leaf_4626_clk/A (CLKBUF_X3)
     7    9.97    0.01    0.05    0.57 ^ clkbuf_leaf_4626_clk/Z (CLKBUF_X3)
                                         clknet_leaf_4626_clk (net)
                  0.01    0.00    0.57 ^ cycle_q[0]$_DFFE_PN0P_/CK (DFFR_X1)
                          0.00    0.57   clock reconvergence pessimism
                          0.01    0.58   library hold time
                                  0.58   data required time
-----------------------------------------------------------------------------
                                  0.58   data required time
                                 -0.67   data arrival time
-----------------------------------------------------------------------------
                                  0.09   slack (MET)



```

### Path 2

- source: `/orfs/flow/reports/nangate45/attention_shared_sram_k_round_scheduler_b17_w17/base/6_finish.rpt`
- stage: `finish`
- startpoint: `rst_n (input port clocked by clk)`
- endpoint: `scheduler.bank_response_count[0]$_DFFE_PN0P_`
- path_group: `asynchronous`
- path_type: `min`
- slack: `1.2600`
- data_arrival_time: `2.0700`
- data_required_time: `0.8100`

```text
Startpoint: rst_n (input port clocked by clk)
Endpoint: scheduler.bank_response_count[0]$_DFFE_PN0P_
          (removal check against rising-edge clock clk)
Path Group: asynchronous
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (propagated)
                          2.00    2.00 ^ input external delay
     1    5.23    0.00    0.00    2.00 ^ rst_n (in)
                                         rst_n (net)
                  0.00    0.00    2.00 ^ input1/A (CLKBUF_X3)
    18   61.57    0.04    0.06    2.06 ^ input1/Z (CLKBUF_X3)
                                         net1 (net)
                  0.04    0.00    2.07 ^ scheduler.bank_response_count[0]$_DFFE_PN0P_/RN (DFFR_X1)
                                  2.07   data arrival time

                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   45.34    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.02    0.02    0.02 ^ wire24470/A (BUF_X8)
...
                                         clknet_8_128_0_clk (net)
                  0.01    0.00    0.45 ^ clkbuf_9_257__f_clk/A (CLKBUF_X3)
    10   43.59    0.03    0.06    0.51 ^ clkbuf_9_257__f_clk/Z (CLKBUF_X3)
                                         clknet_9_257__leaf_clk (net)
                  0.04    0.01    0.52 ^ clkbuf_leaf_4630_clk/A (CLKBUF_X3)
     8   10.45    0.01    0.05    0.57 ^ clkbuf_leaf_4630_clk/Z (CLKBUF_X3)
                                         clknet_leaf_4630_clk (net)
                  0.01    0.00    0.57 ^ scheduler.bank_response_count[0]$_DFFE_PN0P_/CK (DFFR_X1)
                          0.00    0.57   clock reconvergence pessimism
                          0.24    0.81   library removal time
                                  0.81   data required time
-----------------------------------------------------------------------------
                                  0.81   data required time
                                 -2.07   data arrival time
-----------------------------------------------------------------------------
                                  1.26   slack (MET)
```

### Path 3

- source: `/orfs/flow/reports/nangate45/attention_shared_sram_k_round_scheduler_b17_w17/base/6_finish.rpt`
- stage: `finish`
- startpoint: `scheduler.fill_group_q[0]$_DFFE_PN0P_`
- endpoint: `scheduler.bank_request_count[29]$_DFFE_PN0P_`
- path_group: `clk`
- path_type: `max`
- slack: `12.5200`
- data_arrival_time: `3.9600`
- data_required_time: `16.4800`

```text
Startpoint: scheduler.fill_group_q[0]$_DFFE_PN0P_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: scheduler.bank_request_count[29]$_DFFE_PN0P_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   45.34    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.02    0.02    0.02 ^ wire24470/A (BUF_X8)
     1   52.24    0.01    0.03    0.04 ^ wire24470/Z (BUF_X8)
                                         net24470 (net)
                  0.03    0.02    0.07 ^ clkbuf_0_clk/A (CLKBUF_X3)
     2   35.25    0.03    0.06    0.13 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.03    0.00    0.13 ^ clkbuf_1_1_0_clk/A (CLKBUF_X3)
     2   24.34    0.02    0.05    0.19 ^ clkbuf_1_1_0_clk/Z (CLKBUF_X3)
                                         clknet_1_1_0_clk (net)
                  0.02    0.00    0.19 ^ clkbuf_2_2_0_clk/A (CLKBUF_X3)
     2   23.65    0.02    0.05    0.24 ^ clkbuf_2_2_0_clk/Z (CLKBUF_X3)
...
                                         clknet_9_341__leaf_clk (net)
                  0.02    0.00   16.48 ^ clkbuf_leaf_4319_clk/A (CLKBUF_X3)
     8   10.11    0.01    0.04   16.52 ^ clkbuf_leaf_4319_clk/Z (CLKBUF_X3)
                                         clknet_leaf_4319_clk (net)
                  0.01    0.00   16.52 ^ scheduler.bank_request_count[29]$_DFFE_PN0P_/CK (DFFR_X1)
                          0.00   16.52   clock reconvergence pessimism
                         -0.04   16.48   library setup time
                                 16.48   data required time
-----------------------------------------------------------------------------
                                 16.48   data required time
                                 -3.96   data arrival time
-----------------------------------------------------------------------------
                                 12.52   slack (MET)



```

### Path 4

- source: `/orfs/flow/reports/nangate45/attention_shared_sram_k_round_scheduler_b17_w17/base/6_finish.rpt`
- stage: `finish`
- startpoint: `rst_n (input port clocked by clk)`
- endpoint: `cycle_q[25]$_DFFE_PN0P_ (recovery check against rising-edge clock clk)`
- path_group: `asynchronous`
- path_type: `max`
- slack: `13.8300`
- data_arrival_time: `2.7400`
- data_required_time: `16.5700`

```text
Startpoint: rst_n (input port clocked by clk)
Endpoint: cycle_q[25]$_DFFE_PN0P_ (recovery check against rising-edge clock clk)
Path Group: asynchronous
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (propagated)
                          2.00    2.00 ^ input external delay
     1    5.23    0.00    0.00    2.00 ^ rst_n (in)
                                         rst_n (net)
                  0.00    0.00    2.00 ^ input1/A (CLKBUF_X3)
    18   61.57    0.04    0.06    2.06 ^ input1/Z (CLKBUF_X3)
                                         net1 (net)
                  0.05    0.02    2.08 ^ place24419/A (BUF_X2)
    10   40.27    0.04    0.07    2.14 ^ place24419/Z (BUF_X2)
                                         net24419 (net)
                  0.05    0.02    2.16 ^ place24430/A (BUF_X2)
    22   57.35    0.06    0.09    2.25 ^ place24430/Z (BUF_X2)
                                         net24430 (net)
                  0.06    0.01    2.26 ^ place24432/A (BUF_X2)
    28   79.49    0.09    0.11    2.37 ^ place24432/Z (BUF_X2)
                                         net24432 (net)
...
                                         clknet_8_171_0_clk (net)
                  0.01    0.00   16.44 ^ clkbuf_9_343__f_clk/A (CLKBUF_X3)
    11   26.21    0.02    0.05   16.49 ^ clkbuf_9_343__f_clk/Z (CLKBUF_X3)
                                         clknet_9_343__leaf_clk (net)
                  0.02    0.00   16.49 ^ clkbuf_leaf_4295_clk/A (CLKBUF_X3)
     8    9.32    0.01    0.04   16.53 ^ clkbuf_leaf_4295_clk/Z (CLKBUF_X3)
                                         clknet_leaf_4295_clk (net)
                  0.01    0.00   16.53 ^ cycle_q[25]$_DFFE_PN0P_/CK (DFFR_X1)
                          0.00   16.53   clock reconvergence pessimism
                          0.04   16.57   library recovery time
                                 16.57   data required time
-----------------------------------------------------------------------------
                                 16.57   data required time
                                 -2.74   data arrival time
-----------------------------------------------------------------------------
                                 13.83   slack (MET)
```


## Worst Timing Paths Across All Stages

### Path 1

- source: `/orfs/flow/reports/nangate45/attention_shared_sram_k_round_scheduler_b17_w17/base/2_floorplan_final.rpt`
- stage: `floorplan`
- startpoint: `scheduler.done$_DFF_PN0_`
- endpoint: `running_q$_DFFE_PN0P_ (rising edge-triggered flip-flop clocked by clk)`
- path_group: `clk`
- path_type: `min`
- slack: `0.0900`
- data_arrival_time: `0.0900`
- data_required_time: `0.0100`

```text
Startpoint: scheduler.done$_DFF_PN0_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: running_q$_DFFE_PN0P_ (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                  0.00    0.00    0.00 ^ scheduler.done$_DFF_PN0_/CK (DFFR_X1)
     1    1.67    0.01    0.06    0.06 ^ scheduler.done$_DFF_PN0_/QN (DFFR_X1)
                                         _00000_ (net)
                  0.01    0.00    0.06 ^ _95016_/A (OAI21_X1)
     1    1.52    0.01    0.01    0.08 v _95016_/ZN (OAI21_X1)
                                         _41983_ (net)
                  0.01    0.00    0.08 v _95018_/A (OAI21_X1)
     1    1.13    0.01    0.02    0.09 ^ _95018_/ZN (OAI21_X1)
                                         _02350_ (net)
                  0.01    0.00    0.09 ^ running_q$_DFFE_PN0P_/D (DFFR_X1)
                                  0.09   data arrival time

                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                          0.00    0.00   clock reconvergence pessimism
                                  0.00 ^ running_q$_DFFE_PN0P_/CK (DFFR_X1)
                          0.01    0.01   library hold time
                                  0.01   data required time
-----------------------------------------------------------------------------
                                  0.01   data required time
                                 -0.09   data arrival time
-----------------------------------------------------------------------------
                                  0.09   slack (MET)



```

### Path 2

- source: `/orfs/flow/reports/nangate45/attention_shared_sram_k_round_scheduler_b17_w17/base/3_detailed_place.rpt`
- stage: `detailed_place`
- startpoint: `scheduler.done$_DFF_PN0_`
- endpoint: `running_q$_DFFE_PN0P_ (rising edge-triggered flip-flop clocked by clk)`
- path_group: `clk`
- path_type: `min`
- slack: `0.0900`
- data_arrival_time: `0.1000`
- data_required_time: `0.0100`

```text
Startpoint: scheduler.done$_DFF_PN0_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: running_q$_DFFE_PN0P_ (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                  0.00    0.00    0.00 ^ scheduler.done$_DFF_PN0_/CK (DFFR_X1)
     1    1.76    0.01    0.07    0.07 ^ scheduler.done$_DFF_PN0_/QN (DFFR_X1)
                                         _00000_ (net)
                  0.01    0.00    0.07 ^ _95016_/A (OAI21_X1)
     1    1.81    0.01    0.01    0.08 v _95016_/ZN (OAI21_X1)
                                         _41983_ (net)
                  0.01    0.00    0.08 v _95018_/A (OAI21_X1)
     1    1.45    0.01    0.02    0.10 ^ _95018_/ZN (OAI21_X1)
                                         _02350_ (net)
                  0.01    0.00    0.10 ^ running_q$_DFFE_PN0P_/D (DFFR_X1)
                                  0.10   data arrival time

                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                          0.00    0.00   clock reconvergence pessimism
                                  0.00 ^ running_q$_DFFE_PN0P_/CK (DFFR_X1)
                          0.01    0.01   library hold time
                                  0.01   data required time
-----------------------------------------------------------------------------
                                  0.01   data required time
                                 -0.10   data arrival time
-----------------------------------------------------------------------------
                                  0.09   slack (MET)



```

### Path 3

- source: `/orfs/flow/reports/nangate45/attention_shared_sram_k_round_scheduler_b17_w17/base/3_global_place.rpt`
- stage: `global_place`
- startpoint: `scheduler.done$_DFF_PN0_`
- endpoint: `running_q$_DFFE_PN0P_ (rising edge-triggered flip-flop clocked by clk)`
- path_group: `clk`
- path_type: `min`
- slack: `0.0900`
- data_arrival_time: `0.1000`
- data_required_time: `0.0100`

```text
Startpoint: scheduler.done$_DFF_PN0_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: running_q$_DFFE_PN0P_ (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                  0.00    0.00    0.00 ^ scheduler.done$_DFF_PN0_/CK (DFFR_X1)
     1    1.81    0.01    0.07    0.07 ^ scheduler.done$_DFF_PN0_/QN (DFFR_X1)
                                         _00000_ (net)
                  0.01    0.00    0.07 ^ _95016_/A (OAI21_X1)
     1    1.84    0.01    0.01    0.08 v _95016_/ZN (OAI21_X1)
                                         _41983_ (net)
                  0.01    0.00    0.08 v _95018_/A (OAI21_X1)
     1    1.22    0.01    0.02    0.10 ^ _95018_/ZN (OAI21_X1)
                                         _02350_ (net)
                  0.01    0.00    0.10 ^ running_q$_DFFE_PN0P_/D (DFFR_X1)
                                  0.10   data arrival time

                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                          0.00    0.00   clock reconvergence pessimism
                                  0.00 ^ running_q$_DFFE_PN0P_/CK (DFFR_X1)
                          0.01    0.01   library hold time
                                  0.01   data required time
-----------------------------------------------------------------------------
                                  0.01   data required time
                                 -0.10   data arrival time
-----------------------------------------------------------------------------
                                  0.09   slack (MET)



```

### Path 4

- source: `/orfs/flow/reports/nangate45/attention_shared_sram_k_round_scheduler_b17_w17/base/3_resizer.rpt`
- stage: `resizer`
- startpoint: `scheduler.done$_DFF_PN0_`
- endpoint: `running_q$_DFFE_PN0P_ (rising edge-triggered flip-flop clocked by clk)`
- path_group: `clk`
- path_type: `min`
- slack: `0.0900`
- data_arrival_time: `0.1000`
- data_required_time: `0.0100`

```text
Startpoint: scheduler.done$_DFF_PN0_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: running_q$_DFFE_PN0P_ (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                  0.00    0.00    0.00 ^ scheduler.done$_DFF_PN0_/CK (DFFR_X1)
     1    1.81    0.01    0.07    0.07 ^ scheduler.done$_DFF_PN0_/QN (DFFR_X1)
                                         _00000_ (net)
                  0.01    0.00    0.07 ^ _95016_/A (OAI21_X1)
     1    1.84    0.01    0.01    0.08 v _95016_/ZN (OAI21_X1)
                                         _41983_ (net)
                  0.01    0.00    0.08 v _95018_/A (OAI21_X1)
     1    1.22    0.01    0.02    0.10 ^ _95018_/ZN (OAI21_X1)
                                         _02350_ (net)
                  0.01    0.00    0.10 ^ running_q$_DFFE_PN0P_/D (DFFR_X1)
                                  0.10   data arrival time

                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                          0.00    0.00   clock reconvergence pessimism
                                  0.00 ^ running_q$_DFFE_PN0P_/CK (DFFR_X1)
                          0.01    0.01   library hold time
                                  0.01   data required time
-----------------------------------------------------------------------------
                                  0.01   data required time
                                 -0.10   data arrival time
-----------------------------------------------------------------------------
                                  0.09   slack (MET)



```

### Path 5

- source: `/orfs/flow/reports/nangate45/attention_shared_sram_k_round_scheduler_b17_w17/base/4_cts_final.rpt`
- stage: `cts`
- startpoint: `cycle_q[0]$_DFFE_PN0P_`
- endpoint: `cycle_q[0]$_DFFE_PN0P_`
- path_group: `clk`
- path_type: `min`
- slack: `0.0900`
- data_arrival_time: `0.7000`
- data_required_time: `0.6000`

```text
Startpoint: cycle_q[0]$_DFFE_PN0P_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: cycle_q[0]$_DFFE_PN0P_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   63.85    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.02    0.02    0.02 ^ wire24470/A (BUF_X8)
     1   53.41    0.02    0.03    0.05 ^ wire24470/Z (BUF_X8)
                                         net24470 (net)
                  0.02    0.02    0.07 ^ clkbuf_0_clk/A (CLKBUF_X3)
     2   42.51    0.03    0.07    0.14 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.03    0.00    0.14 ^ clkbuf_1_1_0_clk/A (CLKBUF_X3)
     2   29.86    0.02    0.06    0.20 ^ clkbuf_1_1_0_clk/Z (CLKBUF_X3)
                                         clknet_1_1_0_clk (net)
                  0.02    0.00    0.20 ^ clkbuf_2_2_0_clk/A (CLKBUF_X3)
     2   30.22    0.02    0.06    0.26 ^ clkbuf_2_2_0_clk/Z (CLKBUF_X3)
...
                                         clknet_9_257__leaf_clk (net)
                  0.04    0.01    0.55 ^ clkbuf_leaf_4626_clk/A (CLKBUF_X3)
     7    9.85    0.01    0.05    0.59 ^ clkbuf_leaf_4626_clk/Z (CLKBUF_X3)
                                         clknet_leaf_4626_clk (net)
                  0.01    0.00    0.59 ^ cycle_q[0]$_DFFE_PN0P_/CK (DFFR_X1)
                          0.00    0.59   clock reconvergence pessimism
                          0.01    0.60   library hold time
                                  0.60   data required time
-----------------------------------------------------------------------------
                                  0.60   data required time
                                 -0.70   data arrival time
-----------------------------------------------------------------------------
                                  0.09   slack (MET)



```

### Path 6

- source: `/orfs/flow/reports/nangate45/attention_shared_sram_k_round_scheduler_b17_w17/base/6_finish.rpt`
- stage: `finish`
- startpoint: `cycle_q[0]$_DFFE_PN0P_`
- endpoint: `cycle_q[0]$_DFFE_PN0P_`
- path_group: `clk`
- path_type: `min`
- slack: `0.0900`
- data_arrival_time: `0.6700`
- data_required_time: `0.5800`

```text
Startpoint: cycle_q[0]$_DFFE_PN0P_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: cycle_q[0]$_DFFE_PN0P_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   45.34    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.02    0.02    0.02 ^ wire24470/A (BUF_X8)
     1   52.24    0.01    0.03    0.04 ^ wire24470/Z (BUF_X8)
                                         net24470 (net)
                  0.03    0.02    0.07 ^ clkbuf_0_clk/A (CLKBUF_X3)
     2   35.25    0.03    0.06    0.13 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.03    0.00    0.13 ^ clkbuf_1_1_0_clk/A (CLKBUF_X3)
     2   24.34    0.02    0.05    0.19 ^ clkbuf_1_1_0_clk/Z (CLKBUF_X3)
                                         clknet_1_1_0_clk (net)
                  0.02    0.00    0.19 ^ clkbuf_2_2_0_clk/A (CLKBUF_X3)
     2   23.65    0.02    0.05    0.24 ^ clkbuf_2_2_0_clk/Z (CLKBUF_X3)
...
                                         clknet_9_257__leaf_clk (net)
                  0.03    0.01    0.52 ^ clkbuf_leaf_4626_clk/A (CLKBUF_X3)
     7    9.97    0.01    0.05    0.57 ^ clkbuf_leaf_4626_clk/Z (CLKBUF_X3)
                                         clknet_leaf_4626_clk (net)
                  0.01    0.00    0.57 ^ cycle_q[0]$_DFFE_PN0P_/CK (DFFR_X1)
                          0.00    0.57   clock reconvergence pessimism
                          0.01    0.58   library hold time
                                  0.58   data required time
-----------------------------------------------------------------------------
                                  0.58   data required time
                                 -0.67   data arrival time
-----------------------------------------------------------------------------
                                  0.09   slack (MET)



```

### Path 7

- source: `/orfs/flow/reports/nangate45/attention_shared_sram_k_round_scheduler_b17_w17/base/5_global_route.rpt`
- stage: `route`
- startpoint: `scheduler.compute_beat_count[0]$_DFFE_PN0P_`
- endpoint: `scheduler.compute_beat_count[0]$_DFFE_PN0P_`
- path_group: `clk`
- path_type: `min`
- slack: `0.1000`
- data_arrival_time: `0.7000`
- data_required_time: `0.6100`

```text
Startpoint: scheduler.compute_beat_count[0]$_DFFE_PN0P_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: scheduler.compute_beat_count[0]$_DFFE_PN0P_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   62.74    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.02    0.02    0.02 ^ wire24470/A (BUF_X8)
     1   52.02    0.01    0.03    0.05 ^ wire24470/Z (BUF_X8)
                                         net24470 (net)
                  0.03    0.02    0.07 ^ clkbuf_0_clk/A (CLKBUF_X3)
     2   43.96    0.03    0.07    0.14 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.03    0.00    0.14 ^ clkbuf_1_1_0_clk/A (CLKBUF_X3)
     2   29.85    0.02    0.06    0.20 ^ clkbuf_1_1_0_clk/Z (CLKBUF_X3)
                                         clknet_1_1_0_clk (net)
                  0.02    0.00    0.21 ^ clkbuf_2_2_0_clk/A (CLKBUF_X3)
     2   30.24    0.02    0.06    0.26 ^ clkbuf_2_2_0_clk/Z (CLKBUF_X3)
...
                                         clknet_9_256__leaf_clk (net)
                  0.04    0.01    0.55 ^ clkbuf_leaf_4620_clk/A (CLKBUF_X3)
     7    8.96    0.01    0.05    0.60 ^ clkbuf_leaf_4620_clk/Z (CLKBUF_X3)
                                         clknet_leaf_4620_clk (net)
                  0.01    0.00    0.60 ^ scheduler.compute_beat_count[0]$_DFFE_PN0P_/CK (DFFR_X1)
                          0.00    0.60   clock reconvergence pessimism
                          0.01    0.61   library hold time
                                  0.61   data required time
-----------------------------------------------------------------------------
                                  0.61   data required time
                                 -0.70   data arrival time
-----------------------------------------------------------------------------
                                  0.10   slack (MET)



```

### Path 8

- source: `/orfs/flow/reports/nangate45/attention_shared_sram_k_round_scheduler_b17_w17/base/5_global_route.rpt`
- stage: `route`
- startpoint: `rst_n (input port clocked by clk)`
- endpoint: `scheduler.bank_response_count[0]$_DFFE_PN0P_`
- path_group: `asynchronous`
- path_type: `min`
- slack: `1.2300`
- data_arrival_time: `2.0700`
- data_required_time: `0.8400`

```text
Startpoint: rst_n (input port clocked by clk)
Endpoint: scheduler.bank_response_count[0]$_DFFE_PN0P_
          (removal check against rising-edge clock clk)
Path Group: asynchronous
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (propagated)
                          2.00    2.00 ^ input external delay
     1    7.44    0.00    0.00    2.00 ^ rst_n (in)
                                         rst_n (net)
                  0.00    0.00    2.00 ^ input1/A (CLKBUF_X3)
    18   57.27    0.04    0.06    2.06 ^ input1/Z (CLKBUF_X3)
                                         net1 (net)
                  0.04    0.00    2.07 ^ scheduler.bank_response_count[0]$_DFFE_PN0P_/RN (DFFR_X1)
                                  2.07   data arrival time

                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   62.74    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.02    0.02    0.02 ^ wire24470/A (BUF_X8)
...
                                         clknet_8_128_0_clk (net)
                  0.01    0.00    0.48 ^ clkbuf_9_257__f_clk/A (CLKBUF_X3)
    10   44.92    0.03    0.06    0.54 ^ clkbuf_9_257__f_clk/Z (CLKBUF_X3)
                                         clknet_9_257__leaf_clk (net)
                  0.04    0.01    0.55 ^ clkbuf_leaf_4630_clk/A (CLKBUF_X3)
     8    9.97    0.01    0.05    0.60 ^ clkbuf_leaf_4630_clk/Z (CLKBUF_X3)
                                         clknet_leaf_4630_clk (net)
                  0.01    0.00    0.60 ^ scheduler.bank_response_count[0]$_DFFE_PN0P_/CK (DFFR_X1)
                          0.00    0.60   clock reconvergence pessimism
                          0.24    0.84   library removal time
                                  0.84   data required time
-----------------------------------------------------------------------------
                                  0.84   data required time
                                 -2.07   data arrival time
-----------------------------------------------------------------------------
                                  1.23   slack (MET)
```
