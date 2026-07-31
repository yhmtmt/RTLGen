# OpenROAD Timing Debug Summary

- design_dir: `runs/designs/npu_blocks/attention_score32_exact_root_finalizer_l8`
- metrics_path: `runs/designs/npu_blocks/attention_score32_exact_root_finalizer_l8/metrics.csv`
- rows_considered: 2

## Metrics Rows

| param_hash | tag | status | critical_path_ns | density | result_path |
| --- | --- | --- | ---: | ---: | --- |
| 7c17a985 | attention_score32_exact_root_finalizer_lane_firstpass_v1_7c17a985 | ok | 3.4278 | 0.3 | `/orfs/flow/reports/nangate45/attention_score32_exact_root_finalizer_l8/base/6_finish.rpt` |
| 16461852 | attention_score32_exact_root_finalizer_lane_firstpass_v1_16461852 | ok | 3.4350 | 0.5 | `/orfs/flow/reports/nangate45/attention_score32_exact_root_finalizer_l8/base/6_finish.rpt` |

## Inspected Report Files

- `/orfs/flow/reports/nangate45/attention_score32_exact_root_finalizer_l8/base/6_finish.rpt`
- `/orfs/flow/reports/nangate45/attention_score32_exact_root_finalizer_l8/base/5_global_route.rpt`
- `/orfs/flow/reports/nangate45/attention_score32_exact_root_finalizer_l8/base/5_route_drc.rpt`
- `/orfs/flow/reports/nangate45/attention_score32_exact_root_finalizer_l8/base/4_cts_final.rpt`
- `/orfs/flow/reports/nangate45/attention_score32_exact_root_finalizer_l8/base/3_resizer.rpt`
- `/orfs/flow/reports/nangate45/attention_score32_exact_root_finalizer_l8/base/3_detailed_place.rpt`
- `/orfs/flow/reports/nangate45/attention_score32_exact_root_finalizer_l8/base/3_global_place.rpt`
- `/orfs/flow/reports/nangate45/attention_score32_exact_root_finalizer_l8/base/2_floorplan_final.rpt`
- `/orfs/flow/reports/nangate45/attention_score32_exact_root_finalizer_l8/base/drt_antennas.log`
- `/orfs/flow/reports/nangate45/attention_score32_exact_root_finalizer_l8/base/grt_antennas.log`
- `/orfs/flow/reports/nangate45/attention_score32_exact_root_finalizer_l8/base/metadata-generate.log`

## Preferred Final-Stage Timing Paths

- raw_path_block_count: 104
- unique_path_block_count: 33
- preferred_stage: `finish`

### Path 1

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_root_finalizer_l8/base/6_finish.rpt`
- stage: `finish`
- startpoint: `cycle_count[0]$_DFF_PN0_`
- endpoint: `cycle_count[0]$_DFF_PN0_`
- path_group: `clk`
- path_type: `min`
- slack: `0.0600`
- data_arrival_time: `0.3500`
- data_required_time: `0.2900`

```text
Startpoint: cycle_count[0]$_DFF_PN0_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: cycle_count[0]$_DFF_PN0_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   40.84    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.02    0.01    0.01 ^ clkbuf_0_clk/A (CLKBUF_X3)
     2   32.25    0.03    0.06    0.07 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.03    0.00    0.07 ^ clkbuf_1_1_0_clk/A (CLKBUF_X3)
     2   32.27    0.03    0.06    0.13 ^ clkbuf_1_1_0_clk/Z (CLKBUF_X3)
                                         clknet_1_1_0_clk (net)
                  0.03    0.00    0.13 ^ clkbuf_2_3_0_clk/A (CLKBUF_X3)
     4   13.64    0.01    0.05    0.18 ^ clkbuf_2_3_0_clk/Z (CLKBUF_X3)
                                         clknet_2_3_0_clk (net)
                  0.01    0.00    0.18 ^ clkbuf_4_13_0_clk/A (CLKBUF_X3)
    12   31.72    0.03    0.05    0.23 ^ clkbuf_4_13_0_clk/Z (CLKBUF_X3)
...
                                         clknet_4_13_0_clk (net)
                  0.03    0.00    0.24 ^ clkbuf_leaf_100_clk/A (CLKBUF_X3)
     8   10.29    0.01    0.04    0.28 ^ clkbuf_leaf_100_clk/Z (CLKBUF_X3)
                                         clknet_leaf_100_clk (net)
                  0.01    0.00    0.28 ^ cycle_count[0]$_DFF_PN0_/CK (DFFR_X1)
                          0.00    0.28   clock reconvergence pessimism
                          0.01    0.29   library hold time
                                  0.29   data required time
-----------------------------------------------------------------------------
                                  0.29   data required time
                                 -0.35   data arrival time
-----------------------------------------------------------------------------
                                  0.06   slack (MET)



```

### Path 2

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_root_finalizer_l8/base/6_finish.rpt`
- stage: `finish`
- startpoint: `rst_n (input port clocked by clk)`
- endpoint: `completed_count[0]$_DFFE_PN0P_`
- path_group: `asynchronous`
- path_type: `min`
- slack: `1.5000`
- data_arrival_time: `2.0500`
- data_required_time: `0.5500`

```text
Startpoint: rst_n (input port clocked by clk)
Endpoint: completed_count[0]$_DFFE_PN0P_
          (removal check against rising-edge clock clk)
Path Group: asynchronous
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (propagated)
                          2.00    2.00 ^ input external delay
     1    5.45    0.00    0.00    2.00 ^ rst_n (in)
                                         rst_n (net)
                  0.00    0.00    2.00 ^ input390/A (CLKBUF_X3)
     4   37.40    0.02    0.04    2.04 ^ input390/Z (CLKBUF_X3)
                                         net390 (net)
                  0.03    0.01    2.05 ^ completed_count[0]$_DFFE_PN0P_/RN (DFFR_X1)
                                  2.05   data arrival time

                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   40.84    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.02    0.01    0.01 ^ clkbuf_0_clk/A (CLKBUF_X3)
...
                                         clknet_2_2_0_clk (net)
                  0.03    0.00    0.20 ^ clkbuf_4_11_0_clk/A (CLKBUF_X3)
     7   57.54    0.04    0.08    0.27 ^ clkbuf_4_11_0_clk/Z (CLKBUF_X3)
                                         clknet_4_11_0_clk (net)
                  0.05    0.01    0.28 ^ clkbuf_leaf_156_clk/A (CLKBUF_X3)
     8   10.19    0.01    0.05    0.33 ^ clkbuf_leaf_156_clk/Z (CLKBUF_X3)
                                         clknet_leaf_156_clk (net)
                  0.01    0.00    0.33 ^ completed_count[0]$_DFFE_PN0P_/CK (DFFR_X1)
                          0.00    0.33   clock reconvergence pessimism
                          0.22    0.55   library removal time
                                  0.55   data required time
-----------------------------------------------------------------------------
                                  0.55   data required time
                                 -2.05   data arrival time
-----------------------------------------------------------------------------
                                  1.50   slack (MET)
```

### Path 3

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_root_finalizer_l8/base/6_finish.rpt`
- stage: `finish`
- startpoint: `in_value[128] (input port clocked by clk)`
- endpoint: `lane_quotient_q[3][56]$_DFFE_PN0P_`
- path_group: `clk`
- path_type: `max`
- slack: `4.8700`
- data_arrival_time: `3.4400`
- data_required_time: `8.3100`

```text
Startpoint: in_value[128] (input port clocked by clk)
Endpoint: lane_quotient_q[3][56]$_DFFE_PN0P_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (propagated)
                          2.00    2.00 v input external delay
     1    4.70    0.00    0.00    2.00 v in_value[128] (in)
                                         in_value[128] (net)
                  0.00    0.00    2.00 v input92/A (BUF_X1)
     2    3.37    0.01    0.03    2.03 v input92/Z (BUF_X1)
                                         net92 (net)
                  0.01    0.00    2.03 v _16797_/A4 (OR4_X1)
     3    7.24    0.02    0.13    2.16 v _16797_/ZN (OR4_X1)
                                         _10656_ (net)
                  0.02    0.00    2.16 v _16806_/A3 (NOR3_X2)
     4    7.52    0.04    0.07    2.23 ^ _16806_/ZN (NOR3_X2)
                                         _10661_ (net)
                  0.04    0.00    2.23 ^ _16807_/A2 (NAND2_X1)
     4    7.68    0.02    0.04    2.26 v _16807_/ZN (NAND2_X1)
...
                                         clknet_4_5_0_clk (net)
                  0.05    0.01    8.29 ^ clkbuf_leaf_90_clk/A (CLKBUF_X3)
     7    8.42    0.01    0.05    8.34 ^ clkbuf_leaf_90_clk/Z (CLKBUF_X3)
                                         clknet_leaf_90_clk (net)
                  0.01    0.00    8.34 ^ lane_quotient_q[3][56]$_DFFE_PN0P_/CK (DFFR_X1)
                          0.00    8.34   clock reconvergence pessimism
                         -0.03    8.31   library setup time
                                  8.31   data required time
-----------------------------------------------------------------------------
                                  8.31   data required time
                                 -3.44   data arrival time
-----------------------------------------------------------------------------
                                  4.87   slack (MET)



```

### Path 4

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_root_finalizer_l8/base/6_finish.rpt`
- stage: `finish`
- startpoint: `rst_n (input port clocked by clk)`
- endpoint: `lane_quotient_q[5][34]$_DFFE_PN0P_`
- path_group: `asynchronous`
- path_type: `max`
- slack: `5.6200`
- data_arrival_time: `2.7500`
- data_required_time: `8.3800`

```text
Startpoint: rst_n (input port clocked by clk)
Endpoint: lane_quotient_q[5][34]$_DFFE_PN0P_
          (recovery check against rising-edge clock clk)
Path Group: asynchronous
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (propagated)
                          2.00    2.00 ^ input external delay
     1    5.45    0.00    0.00    2.00 ^ rst_n (in)
                                         rst_n (net)
                  0.00    0.00    2.00 ^ input390/A (CLKBUF_X3)
     4   37.40    0.02    0.04    2.04 ^ input390/Z (CLKBUF_X3)
                                         net390 (net)
                  0.04    0.03    2.07 ^ place2146/A (BUF_X1)
     9   41.15    0.09    0.11    2.19 ^ place2146/Z (BUF_X1)
                                         net2146 (net)
                  0.09    0.02    2.21 ^ place2163/A (BUF_X1)
     2   17.69    0.04    0.07    2.27 ^ place2163/Z (BUF_X1)
                                         net2163 (net)
                  0.04    0.01    2.28 ^ place2164/A (BUF_X1)
    14   30.39    0.07    0.10    2.38 ^ place2164/Z (BUF_X1)
...
                                         clknet_2_1_0_clk (net)
                  0.03    0.01    8.20 ^ clkbuf_4_4_0_clk/A (CLKBUF_X3)
    21   60.89    0.05    0.08    8.28 ^ clkbuf_4_4_0_clk/Z (CLKBUF_X3)
                                         clknet_4_4_0_clk (net)
                  0.05    0.01    8.29 ^ clkbuf_leaf_10_clk/A (CLKBUF_X3)
     6    8.12    0.01    0.05    8.34 ^ clkbuf_leaf_10_clk/Z (CLKBUF_X3)
                                         clknet_leaf_10_clk (net)
                  0.01    0.00    8.34 ^ lane_quotient_q[5][34]$_DFFE_PN0P_/CK (DFFR_X1)
                          0.00    8.34   clock reconvergence pessimism
                          0.04    8.38   library recovery time
                                  8.38   data required time
-----------------------------------------------------------------------------
                                  8.38   data required time
                                 -2.75   data arrival time
-----------------------------------------------------------------------------
                                  5.62   slack (MET)
```

### Path 5

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_root_finalizer_l8/base/6_finish.rpt`
- stage: `finish`
- startpoint: `exp_sum_q[0]$_DFFE_PN0P_`
- endpoint: `out_value_q[72]$_DFFE_PN0P_`
- path_group: `clk`
- path_type: `max`
- slack: `6.6000`
- data_arrival_time: `1.6400`
- data_required_time: `8.2400`

```text
Startpoint: exp_sum_q[0]$_DFFE_PN0P_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: out_value_q[72]$_DFFE_PN0P_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

  Delay    Time   Description
---------------------------------------------------------
   0.00    0.00   clock clk (rise edge)
   0.00    0.00   clock source latency
   0.00    0.00 ^ clk (in)
   0.07    0.07 ^ clkbuf_0_clk/Z (CLKBUF_X3)
   0.06    0.13 ^ clkbuf_1_0_0_clk/Z (CLKBUF_X3)
   0.07    0.20 ^ clkbuf_2_0_0_clk/Z (CLKBUF_X3)
   0.10    0.30 ^ clkbuf_4_2_0_clk/Z (CLKBUF_X3)
   0.06    0.36 ^ clkbuf_leaf_28_clk/Z (CLKBUF_X3)
   0.00    0.36 ^ exp_sum_q[0]$_DFFE_PN0P_/CK (DFFR_X1)
   0.15    0.51 ^ exp_sum_q[0]$_DFFE_PN0P_/Q (DFFR_X1)
   0.11    0.62 ^ place2070/Z (BUF_X1)
   0.07    0.69 ^ _27828_/CO (HA_X1)
   0.05    0.74 ^ _27656_/CO (FA_X1)
   0.01    0.75 v _15549_/ZN (INV_X1)
   0.03    0.78 ^ _15550_/ZN (AOI21_X1)
...
   0.06    8.13 ^ clkbuf_1_1_0_clk/Z (CLKBUF_X3)
   0.05    8.18 ^ clkbuf_2_3_0_clk/Z (CLKBUF_X3)
   0.05    8.23 ^ clkbuf_4_12_0_clk/Z (CLKBUF_X3)
   0.04    8.27 ^ clkbuf_leaf_114_clk/Z (CLKBUF_X3)
   0.00    8.27 ^ out_value_q[72]$_DFFE_PN0P_/CK (DFFR_X1)
   0.00    8.27   clock reconvergence pessimism
  -0.04    8.24   library setup time
           8.24   data required time
---------------------------------------------------------
           8.24   data required time
          -1.64   data arrival time
---------------------------------------------------------
           6.60   slack (MET)



```


## Worst Timing Paths Across All Stages

### Path 1

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_root_finalizer_l8/base/2_floorplan_final.rpt`
- stage: `floorplan`
- startpoint: `cycle_count[0]$_DFF_PN0_`
- endpoint: `cycle_count[0]$_DFF_PN0_`
- path_group: `clk`
- path_type: `min`
- slack: `0.0600`
- data_arrival_time: `0.0600`
- data_required_time: `0.0100`

```text
Startpoint: cycle_count[0]$_DFF_PN0_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: cycle_count[0]$_DFF_PN0_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                  0.00    0.00    0.00 ^ cycle_count[0]$_DFF_PN0_/CK (DFFR_X1)
     1    1.13    0.01    0.06    0.06 ^ cycle_count[0]$_DFF_PN0_/QN (DFFR_X1)
                                         _13660_ (net)
                  0.01    0.00    0.06 ^ cycle_count[0]$_DFF_PN0_/D (DFFR_X1)
                                  0.06   data arrival time

                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                          0.00    0.00   clock reconvergence pessimism
                                  0.00 ^ cycle_count[0]$_DFF_PN0_/CK (DFFR_X1)
                          0.01    0.01   library hold time
                                  0.01   data required time
-----------------------------------------------------------------------------
                                  0.01   data required time
                                 -0.06   data arrival time
-----------------------------------------------------------------------------
                                  0.06   slack (MET)



```

### Path 2

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_root_finalizer_l8/base/3_detailed_place.rpt`
- stage: `detailed_place`
- startpoint: `cycle_count[0]$_DFF_PN0_`
- endpoint: `cycle_count[0]$_DFF_PN0_`
- path_group: `clk`
- path_type: `min`
- slack: `0.0600`
- data_arrival_time: `0.0600`
- data_required_time: `0.0100`

```text
Startpoint: cycle_count[0]$_DFF_PN0_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: cycle_count[0]$_DFF_PN0_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                  0.00    0.00    0.00 ^ cycle_count[0]$_DFF_PN0_/CK (DFFR_X1)
     1    1.38    0.01    0.06    0.06 ^ cycle_count[0]$_DFF_PN0_/QN (DFFR_X1)
                                         _13660_ (net)
                  0.01    0.00    0.06 ^ cycle_count[0]$_DFF_PN0_/D (DFFR_X1)
                                  0.06   data arrival time

                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                          0.00    0.00   clock reconvergence pessimism
                                  0.00 ^ cycle_count[0]$_DFF_PN0_/CK (DFFR_X1)
                          0.01    0.01   library hold time
                                  0.01   data required time
-----------------------------------------------------------------------------
                                  0.01   data required time
                                 -0.06   data arrival time
-----------------------------------------------------------------------------
                                  0.06   slack (MET)



```

### Path 3

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_root_finalizer_l8/base/3_global_place.rpt`
- stage: `global_place`
- startpoint: `cycle_count[0]$_DFF_PN0_`
- endpoint: `cycle_count[0]$_DFF_PN0_`
- path_group: `clk`
- path_type: `min`
- slack: `0.0600`
- data_arrival_time: `0.0600`
- data_required_time: `0.0100`

```text
Startpoint: cycle_count[0]$_DFF_PN0_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: cycle_count[0]$_DFF_PN0_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                  0.00    0.00    0.00 ^ cycle_count[0]$_DFF_PN0_/CK (DFFR_X1)
     1    1.38    0.01    0.06    0.06 ^ cycle_count[0]$_DFF_PN0_/QN (DFFR_X1)
                                         _13660_ (net)
                  0.01    0.00    0.06 ^ cycle_count[0]$_DFF_PN0_/D (DFFR_X1)
                                  0.06   data arrival time

                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                          0.00    0.00   clock reconvergence pessimism
                                  0.00 ^ cycle_count[0]$_DFF_PN0_/CK (DFFR_X1)
                          0.01    0.01   library hold time
                                  0.01   data required time
-----------------------------------------------------------------------------
                                  0.01   data required time
                                 -0.06   data arrival time
-----------------------------------------------------------------------------
                                  0.06   slack (MET)



```

### Path 4

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_root_finalizer_l8/base/3_resizer.rpt`
- stage: `resizer`
- startpoint: `cycle_count[0]$_DFF_PN0_`
- endpoint: `cycle_count[0]$_DFF_PN0_`
- path_group: `clk`
- path_type: `min`
- slack: `0.0600`
- data_arrival_time: `0.0600`
- data_required_time: `0.0100`

```text
Startpoint: cycle_count[0]$_DFF_PN0_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: cycle_count[0]$_DFF_PN0_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                  0.00    0.00    0.00 ^ cycle_count[0]$_DFF_PN0_/CK (DFFR_X1)
     1    1.38    0.01    0.06    0.06 ^ cycle_count[0]$_DFF_PN0_/QN (DFFR_X1)
                                         _13660_ (net)
                  0.01    0.00    0.06 ^ cycle_count[0]$_DFF_PN0_/D (DFFR_X1)
                                  0.06   data arrival time

                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                          0.00    0.00   clock reconvergence pessimism
                                  0.00 ^ cycle_count[0]$_DFF_PN0_/CK (DFFR_X1)
                          0.01    0.01   library hold time
                                  0.01   data required time
-----------------------------------------------------------------------------
                                  0.01   data required time
                                 -0.06   data arrival time
-----------------------------------------------------------------------------
                                  0.06   slack (MET)



```

### Path 5

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_root_finalizer_l8/base/4_cts_final.rpt`
- stage: `cts`
- startpoint: `cycle_count[0]$_DFF_PN0_`
- endpoint: `cycle_count[0]$_DFF_PN0_`
- path_group: `clk`
- path_type: `min`
- slack: `0.0600`
- data_arrival_time: `0.3900`
- data_required_time: `0.3300`

```text
Startpoint: cycle_count[0]$_DFF_PN0_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: cycle_count[0]$_DFF_PN0_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   61.49    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.02    0.02    0.02 ^ clkbuf_0_clk/A (CLKBUF_X3)
     2   42.44    0.03    0.07    0.08 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.03    0.00    0.09 ^ clkbuf_1_1_0_clk/A (CLKBUF_X3)
     2   42.60    0.03    0.07    0.16 ^ clkbuf_1_1_0_clk/Z (CLKBUF_X3)
                                         clknet_1_1_0_clk (net)
                  0.03    0.00    0.16 ^ clkbuf_2_3_0_clk/A (CLKBUF_X3)
     4   13.55    0.01    0.05    0.21 ^ clkbuf_2_3_0_clk/Z (CLKBUF_X3)
                                         clknet_2_3_0_clk (net)
                  0.01    0.00    0.21 ^ clkbuf_4_13_0_clk/A (CLKBUF_X3)
    12   36.67    0.03    0.06    0.27 ^ clkbuf_4_13_0_clk/Z (CLKBUF_X3)
...
                                         clknet_4_13_0_clk (net)
                  0.03    0.00    0.27 ^ clkbuf_leaf_100_clk/A (CLKBUF_X3)
     8   10.10    0.01    0.04    0.32 ^ clkbuf_leaf_100_clk/Z (CLKBUF_X3)
                                         clknet_leaf_100_clk (net)
                  0.01    0.00    0.32 ^ cycle_count[0]$_DFF_PN0_/CK (DFFR_X1)
                          0.00    0.32   clock reconvergence pessimism
                          0.01    0.33   library hold time
                                  0.33   data required time
-----------------------------------------------------------------------------
                                  0.33   data required time
                                 -0.39   data arrival time
-----------------------------------------------------------------------------
                                  0.06   slack (MET)



```

### Path 6

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_root_finalizer_l8/base/5_global_route.rpt`
- stage: `route`
- startpoint: `cycle_count[0]$_DFF_PN0_`
- endpoint: `cycle_count[0]$_DFF_PN0_`
- path_group: `clk`
- path_type: `min`
- slack: `0.0600`
- data_arrival_time: `0.3800`
- data_required_time: `0.3200`

```text
Startpoint: cycle_count[0]$_DFF_PN0_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: cycle_count[0]$_DFF_PN0_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   61.54    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.02    0.02    0.02 ^ clkbuf_0_clk/A (CLKBUF_X3)
     2   42.16    0.03    0.07    0.08 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.03    0.00    0.09 ^ clkbuf_1_1_0_clk/A (CLKBUF_X3)
     2   42.23    0.03    0.07    0.16 ^ clkbuf_1_1_0_clk/Z (CLKBUF_X3)
                                         clknet_1_1_0_clk (net)
                  0.03    0.01    0.16 ^ clkbuf_2_3_0_clk/A (CLKBUF_X3)
     4   13.77    0.01    0.05    0.21 ^ clkbuf_2_3_0_clk/Z (CLKBUF_X3)
                                         clknet_2_3_0_clk (net)
                  0.01    0.00    0.21 ^ clkbuf_4_13_0_clk/A (CLKBUF_X3)
    12   35.56    0.03    0.06    0.27 ^ clkbuf_4_13_0_clk/Z (CLKBUF_X3)
...
                                         clknet_4_13_0_clk (net)
                  0.03    0.00    0.27 ^ clkbuf_leaf_100_clk/A (CLKBUF_X3)
     8   10.44    0.01    0.04    0.32 ^ clkbuf_leaf_100_clk/Z (CLKBUF_X3)
                                         clknet_leaf_100_clk (net)
                  0.01    0.00    0.32 ^ cycle_count[0]$_DFF_PN0_/CK (DFFR_X1)
                          0.00    0.32   clock reconvergence pessimism
                          0.01    0.32   library hold time
                                  0.32   data required time
-----------------------------------------------------------------------------
                                  0.32   data required time
                                 -0.38   data arrival time
-----------------------------------------------------------------------------
                                  0.06   slack (MET)



```

### Path 7

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_root_finalizer_l8/base/6_finish.rpt`
- stage: `finish`
- startpoint: `cycle_count[0]$_DFF_PN0_`
- endpoint: `cycle_count[0]$_DFF_PN0_`
- path_group: `clk`
- path_type: `min`
- slack: `0.0600`
- data_arrival_time: `0.3500`
- data_required_time: `0.2900`

```text
Startpoint: cycle_count[0]$_DFF_PN0_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: cycle_count[0]$_DFF_PN0_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   40.84    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.02    0.01    0.01 ^ clkbuf_0_clk/A (CLKBUF_X3)
     2   32.25    0.03    0.06    0.07 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.03    0.00    0.07 ^ clkbuf_1_1_0_clk/A (CLKBUF_X3)
     2   32.27    0.03    0.06    0.13 ^ clkbuf_1_1_0_clk/Z (CLKBUF_X3)
                                         clknet_1_1_0_clk (net)
                  0.03    0.00    0.13 ^ clkbuf_2_3_0_clk/A (CLKBUF_X3)
     4   13.64    0.01    0.05    0.18 ^ clkbuf_2_3_0_clk/Z (CLKBUF_X3)
                                         clknet_2_3_0_clk (net)
                  0.01    0.00    0.18 ^ clkbuf_4_13_0_clk/A (CLKBUF_X3)
    12   31.72    0.03    0.05    0.23 ^ clkbuf_4_13_0_clk/Z (CLKBUF_X3)
...
                                         clknet_4_13_0_clk (net)
                  0.03    0.00    0.24 ^ clkbuf_leaf_100_clk/A (CLKBUF_X3)
     8   10.29    0.01    0.04    0.28 ^ clkbuf_leaf_100_clk/Z (CLKBUF_X3)
                                         clknet_leaf_100_clk (net)
                  0.01    0.00    0.28 ^ cycle_count[0]$_DFF_PN0_/CK (DFFR_X1)
                          0.00    0.28   clock reconvergence pessimism
                          0.01    0.29   library hold time
                                  0.29   data required time
-----------------------------------------------------------------------------
                                  0.29   data required time
                                 -0.35   data arrival time
-----------------------------------------------------------------------------
                                  0.06   slack (MET)



```

### Path 8

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_root_finalizer_l8/base/4_cts_final.rpt`
- stage: `cts`
- startpoint: `rst_n (input port clocked by clk)`
- endpoint: `completed_count[0]$_DFFE_PN0P_`
- path_group: `asynchronous`
- path_type: `min`
- slack: `1.4400`
- data_arrival_time: `2.0600`
- data_required_time: `0.6100`

```text
Startpoint: rst_n (input port clocked by clk)
Endpoint: completed_count[0]$_DFFE_PN0P_
          (removal check against rising-edge clock clk)
Path Group: asynchronous
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (propagated)
                          2.00    2.00 ^ input external delay
     1    6.96    0.00    0.00    2.00 ^ rst_n (in)
                                         rst_n (net)
                  0.00    0.00    2.00 ^ input390/A (CLKBUF_X3)
     4   47.68    0.03    0.05    2.05 ^ input390/Z (CLKBUF_X3)
                                         net390 (net)
                  0.03    0.01    2.06 ^ completed_count[0]$_DFFE_PN0P_/RN (DFFR_X1)
                                  2.06   data arrival time

                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   61.49    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.02    0.02    0.02 ^ clkbuf_0_clk/A (CLKBUF_X3)
...
                                         clknet_2_2_0_clk (net)
                  0.04    0.00    0.24 ^ clkbuf_4_11_0_clk/A (CLKBUF_X3)
     7   72.34    0.05    0.09    0.33 ^ clkbuf_4_11_0_clk/Z (CLKBUF_X3)
                                         clknet_4_11_0_clk (net)
                  0.06    0.01    0.34 ^ clkbuf_leaf_156_clk/A (CLKBUF_X3)
     8   10.30    0.01    0.05    0.39 ^ clkbuf_leaf_156_clk/Z (CLKBUF_X3)
                                         clknet_leaf_156_clk (net)
                  0.01    0.00    0.39 ^ completed_count[0]$_DFFE_PN0P_/CK (DFFR_X1)
                          0.00    0.39   clock reconvergence pessimism
                          0.22    0.61   library removal time
                                  0.61   data required time
-----------------------------------------------------------------------------
                                  0.61   data required time
                                 -2.06   data arrival time
-----------------------------------------------------------------------------
                                  1.44   slack (MET)
```
