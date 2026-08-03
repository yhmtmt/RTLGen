# OpenROAD Timing Debug Summary

- design_dir: `runs/designs/npu_blocks/attention_score32_exact_local_temporal_reducer_gqa8_physical_harness_p53_source_only_w8`
- metrics_path: `runs/designs/npu_blocks/attention_score32_exact_local_temporal_reducer_gqa8_physical_harness_p53_source_only_w8/metrics.csv`
- rows_considered: 2

## Metrics Rows

| param_hash | tag | status | critical_path_ns | density | result_path |
| --- | --- | --- | ---: | ---: | --- |
| 6a375b03 | attention_score32_local_temporal_reducer_gqa8_physical_harness_boundary_noshare_v1_r2_6a375b03 | ok | 0.8517 | 0.35 | `/orfs/flow/reports/nangate45/attention_score32_exact_local_temporal_reducer_gqa8_physical_harness_p53_source_only_w8/base/6_finish.rpt` |
| 98397138 | attention_score32_local_temporal_reducer_gqa8_physical_harness_boundary_noshare_v1_r2_98397138 | ok | 0.8663 | 0.35 | `/orfs/flow/reports/nangate45/attention_score32_exact_local_temporal_reducer_gqa8_physical_harness_p53_source_only_w8/base/6_finish.rpt` |

## Inspected Report Files

- `/orfs/flow/reports/nangate45/attention_score32_exact_local_temporal_reducer_gqa8_physical_harness_p53_source_only_w8/base/6_finish.rpt`
- `/orfs/flow/reports/nangate45/attention_score32_exact_local_temporal_reducer_gqa8_physical_harness_p53_source_only_w8/base/5_global_route.rpt`
- `/orfs/flow/reports/nangate45/attention_score32_exact_local_temporal_reducer_gqa8_physical_harness_p53_source_only_w8/base/5_route_drc.rpt`
- `/orfs/flow/reports/nangate45/attention_score32_exact_local_temporal_reducer_gqa8_physical_harness_p53_source_only_w8/base/4_cts_final.rpt`
- `/orfs/flow/reports/nangate45/attention_score32_exact_local_temporal_reducer_gqa8_physical_harness_p53_source_only_w8/base/3_resizer.rpt`
- `/orfs/flow/reports/nangate45/attention_score32_exact_local_temporal_reducer_gqa8_physical_harness_p53_source_only_w8/base/3_detailed_place.rpt`
- `/orfs/flow/reports/nangate45/attention_score32_exact_local_temporal_reducer_gqa8_physical_harness_p53_source_only_w8/base/3_global_place.rpt`
- `/orfs/flow/reports/nangate45/attention_score32_exact_local_temporal_reducer_gqa8_physical_harness_p53_source_only_w8/base/2_floorplan_final.rpt`
- `/orfs/flow/reports/nangate45/attention_score32_exact_local_temporal_reducer_gqa8_physical_harness_p53_source_only_w8/base/drt_antennas.log`
- `/orfs/flow/reports/nangate45/attention_score32_exact_local_temporal_reducer_gqa8_physical_harness_p53_source_only_w8/base/grt_antennas.log`
- `/orfs/flow/reports/nangate45/attention_score32_exact_local_temporal_reducer_gqa8_physical_harness_p53_source_only_w8/base/metadata-generate.log`

## Preferred Final-Stage Timing Paths

- raw_path_block_count: 104
- unique_path_block_count: 33
- preferred_stage: `finish`

### Path 1

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_local_temporal_reducer_gqa8_physical_harness_p53_source_only_w8/base/6_finish.rpt`
- stage: `finish`
- startpoint: `shared_beat_count_q[10]$_DFFE_PN0P_`
- endpoint: `shared_beat_count_q[10]$_DFFE_PN0P_`
- path_group: `clk`
- path_type: `min`
- slack: `0.1100`
- data_arrival_time: `0.4300`
- data_required_time: `0.3200`

```text
Startpoint: shared_beat_count_q[10]$_DFFE_PN0P_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: shared_beat_count_q[10]$_DFFE_PN0P_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   36.53    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.01    0.01    0.01 ^ wire2039/A (BUF_X8)
     1   44.48    0.01    0.03    0.04 ^ wire2039/Z (BUF_X8)
                                         net2038 (net)
                  0.02    0.02    0.05 ^ wire2038/A (BUF_X16)
     1   49.87    0.01    0.03    0.08 ^ wire2038/Z (BUF_X16)
                                         net2037 (net)
                  0.02    0.02    0.10 ^ clkbuf_0_clk/A (CLKBUF_X3)
     2   29.95    0.02    0.06    0.15 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.02    0.00    0.16 ^ clkbuf_1_0_0_clk/A (CLKBUF_X3)
     2   10.09    0.01    0.04    0.20 ^ clkbuf_1_0_0_clk/Z (CLKBUF_X3)
...
                                         clknet_2_1__leaf_clk (net)
                  0.03    0.01    0.26 ^ clkbuf_leaf_11_clk/A (CLKBUF_X3)
     9   13.98    0.01    0.05    0.31 ^ clkbuf_leaf_11_clk/Z (CLKBUF_X3)
                                         clknet_leaf_11_clk (net)
                  0.01    0.00    0.31 ^ shared_beat_count_q[10]$_DFFE_PN0P_/CK (DFFR_X1)
                          0.00    0.31   clock reconvergence pessimism
                          0.01    0.32   library hold time
                                  0.32   data required time
-----------------------------------------------------------------------------
                                  0.32   data required time
                                 -0.43   data arrival time
-----------------------------------------------------------------------------
                                  0.11   slack (MET)



```

### Path 2

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_local_temporal_reducer_gqa8_physical_harness_p53_source_only_w8/base/6_finish.rpt`
- stage: `finish`
- startpoint: `rst_n (input port clocked by clk)`
- endpoint: `leaf_fire_count_q[28]$_DFFE_PN0P_`
- path_group: `asynchronous`
- path_type: `min`
- slack: `1.5200`
- data_arrival_time: `2.0700`
- data_required_time: `0.5500`

```text
Startpoint: rst_n (input port clocked by clk)
Endpoint: leaf_fire_count_q[28]$_DFFE_PN0P_
          (removal check against rising-edge clock clk)
Path Group: asynchronous
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (propagated)
                          2.00    2.00 ^ input external delay
     1    7.82    0.00    0.00    2.00 ^ rst_n (in)
                                         rst_n (net)
                  0.00    0.00    2.00 ^ input204/A (CLKBUF_X3)
    19   76.46    0.05    0.07    2.07 ^ input204/Z (CLKBUF_X3)
                                         net203 (net)
                  0.05    0.00    2.07 ^ leaf_fire_count_q[28]$_DFFE_PN0P_/RN (DFFR_X1)
                                  2.07   data arrival time

                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   36.53    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.01    0.01    0.01 ^ wire2039/A (BUF_X8)
...
                                         clknet_1_1_0_clk (net)
                  0.01    0.00    0.20 ^ clkbuf_2_3__f_clk/A (CLKBUF_X3)
     7   30.42    0.02    0.05    0.25 ^ clkbuf_2_3__f_clk/Z (CLKBUF_X3)
                                         clknet_2_3__leaf_clk (net)
                  0.03    0.01    0.26 ^ clkbuf_leaf_21_clk/A (CLKBUF_X3)
    10   13.64    0.01    0.05    0.30 ^ clkbuf_leaf_21_clk/Z (CLKBUF_X3)
                                         clknet_leaf_21_clk (net)
                  0.01    0.00    0.30 ^ leaf_fire_count_q[28]$_DFFE_PN0P_/CK (DFFR_X1)
                          0.00    0.30   clock reconvergence pessimism
                          0.24    0.55   library removal time
                                  0.55   data required time
-----------------------------------------------------------------------------
                                  0.55   data required time
                                 -2.07   data arrival time
-----------------------------------------------------------------------------
                                  1.52   slack (MET)
```

### Path 3

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_local_temporal_reducer_gqa8_physical_harness_p53_source_only_w8/base/6_finish.rpt`
- stage: `finish`
- startpoint: `final_value_q[313]$_DFFE_PN0P_`
- endpoint: `final_value[313] (output port clocked by clk)`
- path_group: `clk`
- path_type: `max`
- slack: `7.1300`
- data_arrival_time: `0.8700`
- data_required_time: `8.0000`

```text
Startpoint: final_value_q[313]$_DFFE_PN0P_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: final_value[313] (output port clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   36.53    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.01    0.01    0.01 ^ wire2039/A (BUF_X8)
     1   44.48    0.01    0.03    0.04 ^ wire2039/Z (BUF_X8)
                                         net2038 (net)
                  0.02    0.02    0.05 ^ wire2038/A (BUF_X16)
     1   49.87    0.01    0.03    0.08 ^ wire2038/Z (BUF_X16)
                                         net2037 (net)
                  0.02    0.02    0.10 ^ clkbuf_0_clk/A (CLKBUF_X3)
     2   29.95    0.02    0.06    0.15 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.02    0.00    0.16 ^ clkbuf_1_0_0_clk/A (CLKBUF_X3)
     2   10.09    0.01    0.04    0.20 ^ clkbuf_1_0_0_clk/Z (CLKBUF_X3)
                                         clknet_1_0_0_clk (net)
...
                  0.02    0.00    0.87 ^ final_value[313] (out)
                                  0.87   data arrival time

                         10.00   10.00   clock clk (rise edge)
                          0.00   10.00   clock network delay (propagated)
                          0.00   10.00   clock reconvergence pessimism
                         -2.00    8.00   output external delay
                                  8.00   data required time
-----------------------------------------------------------------------------
                                  8.00   data required time
                                 -0.87   data arrival time
-----------------------------------------------------------------------------
                                  7.13   slack (MET)



```

### Path 4

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_local_temporal_reducer_gqa8_physical_harness_p53_source_only_w8/base/6_finish.rpt`
- stage: `finish`
- startpoint: `rst_n (input port clocked by clk)`
- endpoint: `final_global_max_q[17]$_DFFE_PN0P_`
- path_group: `asynchronous`
- path_type: `max`
- slack: `7.5800`
- data_arrival_time: `2.7900`
- data_required_time: `10.3600`

```text
Startpoint: rst_n (input port clocked by clk)
Endpoint: final_global_max_q[17]$_DFFE_PN0P_
          (recovery check against rising-edge clock clk)
Path Group: asynchronous
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (propagated)
                          2.00    2.00 ^ input external delay
     1    7.82    0.00    0.00    2.00 ^ rst_n (in)
                                         rst_n (net)
                  0.00    0.00    2.00 ^ input204/A (CLKBUF_X3)
    19   76.46    0.05    0.07    2.07 ^ input204/Z (CLKBUF_X3)
                                         net203 (net)
                  0.07    0.04    2.11 ^ place2028/A (BUF_X2)
     1   12.50    0.02    0.04    2.15 ^ place2028/Z (BUF_X2)
                                         net2027 (net)
                  0.02    0.00    2.16 ^ place2029/A (BUF_X2)
     3   48.46    0.03    0.05    2.21 ^ place2029/Z (BUF_X2)
                                         net2028 (net)
                  0.08    0.05    2.26 ^ place2030/A (BUF_X2)
    23   56.34    0.06    0.09    2.34 ^ place2030/Z (BUF_X2)
...
                                         clknet_1_0_0_clk (net)
                  0.01    0.00   10.20 ^ clkbuf_2_1__f_clk/A (CLKBUF_X3)
    11   38.42    0.03    0.06   10.26 ^ clkbuf_2_1__f_clk/Z (CLKBUF_X3)
                                         clknet_2_1__leaf_clk (net)
                  0.03    0.01   10.27 ^ clkbuf_leaf_8_clk/A (CLKBUF_X3)
     9   18.10    0.02    0.05   10.32 ^ clkbuf_leaf_8_clk/Z (CLKBUF_X3)
                                         clknet_leaf_8_clk (net)
                  0.02    0.00   10.32 ^ final_global_max_q[17]$_DFFE_PN0P_/CK (DFFR_X1)
                          0.00   10.32   clock reconvergence pessimism
                          0.05   10.36   library recovery time
                                 10.36   data required time
-----------------------------------------------------------------------------
                                 10.36   data required time
                                 -2.79   data arrival time
-----------------------------------------------------------------------------
                                  7.58   slack (MET)
```

### Path 5

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_local_temporal_reducer_gqa8_physical_harness_p53_source_only_w8/base/6_finish.rpt`
- stage: `finish`
- startpoint: `shared_beat_count_q[2]$_DFFE_PN0P_`
- endpoint: `source_fold_q[31]$_DFFE_PN0P_`
- path_group: `clk`
- path_type: `max`
- slack: `8.3400`
- data_arrival_time: `1.9600`
- data_required_time: `10.2900`

```text
Startpoint: shared_beat_count_q[2]$_DFFE_PN0P_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: source_fold_q[31]$_DFFE_PN0P_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

  Delay    Time   Description
---------------------------------------------------------
   0.00    0.00   clock clk (rise edge)
   0.00    0.00   clock source latency
   0.00    0.00 ^ clk (in)
   0.04    0.04 ^ wire2039/Z (BUF_X8)
   0.04    0.08 ^ wire2038/Z (BUF_X16)
   0.08    0.15 ^ clkbuf_0_clk/Z (CLKBUF_X3)
   0.04    0.20 ^ clkbuf_1_0_0_clk/Z (CLKBUF_X3)
   0.06    0.26 ^ clkbuf_2_1__f_clk/Z (CLKBUF_X3)
   0.06    0.31 ^ clkbuf_leaf_12_clk/Z (CLKBUF_X3)
   0.00    0.31 ^ shared_beat_count_q[2]$_DFFE_PN0P_/CK (DFFR_X1)
   0.18    0.49 ^ shared_beat_count_q[2]$_DFFE_PN0P_/Q (DFFR_X1)
   0.13    0.62 ^ _7601_/S (HA_X1)
   0.03    0.65 v _5964_/ZN (NAND3_X1)
   0.05    0.70 ^ _5966_/ZN (OAI221_X1)
   0.09    0.79 ^ place1665/Z (BUF_X1)
...
   0.08   10.15 ^ clkbuf_0_clk/Z (CLKBUF_X3)
   0.04   10.20 ^ clkbuf_1_0_0_clk/Z (CLKBUF_X3)
   0.06   10.26 ^ clkbuf_2_0__f_clk/Z (CLKBUF_X3)
   0.06   10.33 ^ clkbuf_leaf_2_clk/Z (CLKBUF_X3)
   0.00   10.33 ^ source_fold_q[31]$_DFFE_PN0P_/CK (DFFR_X1)
   0.00   10.33   clock reconvergence pessimism
  -0.04   10.29   library setup time
          10.29   data required time
---------------------------------------------------------
          10.29   data required time
          -1.96   data arrival time
---------------------------------------------------------
           8.34   slack (MET)



```


## Worst Timing Paths Across All Stages

### Path 1

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_local_temporal_reducer_gqa8_physical_harness_p53_source_only_w8/base/2_floorplan_final.rpt`
- stage: `floorplan`
- startpoint: `final_exp_sum_q[16]$_DFFE_PN0P_`
- endpoint: `final_exp_sum_q[16]$_DFFE_PN0P_`
- path_group: `clk`
- path_type: `min`
- slack: `0.1100`
- data_arrival_time: `0.1100`
- data_required_time: `0.0000`

```text
Startpoint: final_exp_sum_q[16]$_DFFE_PN0P_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: final_exp_sum_q[16]$_DFFE_PN0P_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                  0.00    0.00    0.00 ^ final_exp_sum_q[16]$_DFFE_PN0P_/CK (DFFR_X1)
     2    1.58    0.01    0.08    0.08 v final_exp_sum_q[16]$_DFFE_PN0P_/Q (DFFR_X1)
                                         final_exp_sum[16] (net)
                  0.01    0.00    0.08 v _6344_/A1 (NAND2_X1)
     1    1.65    0.01    0.01    0.10 ^ _6344_/ZN (NAND2_X1)
                                         _0525_ (net)
                  0.01    0.00    0.10 ^ _6361_/B1 (AOI21_X1)
     1    1.05    0.01    0.01    0.11 v _6361_/ZN (AOI21_X1)
                                         _0155_ (net)
                  0.01    0.00    0.11 v final_exp_sum_q[16]$_DFFE_PN0P_/D (DFFR_X1)
                                  0.11   data arrival time

                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                          0.00    0.00   clock reconvergence pessimism
                                  0.00 ^ final_exp_sum_q[16]$_DFFE_PN0P_/CK (DFFR_X1)
                          0.00    0.00   library hold time
                                  0.00   data required time
-----------------------------------------------------------------------------
                                  0.00   data required time
                                 -0.11   data arrival time
-----------------------------------------------------------------------------
                                  0.11   slack (MET)



```

### Path 2

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_local_temporal_reducer_gqa8_physical_harness_p53_source_only_w8/base/3_detailed_place.rpt`
- stage: `detailed_place`
- startpoint: `shared_beat_count_q[10]$_DFFE_PN0P_`
- endpoint: `shared_beat_count_q[10]$_DFFE_PN0P_`
- path_group: `clk`
- path_type: `min`
- slack: `0.1100`
- data_arrival_time: `0.1100`
- data_required_time: `0.0000`

```text
Startpoint: shared_beat_count_q[10]$_DFFE_PN0P_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: shared_beat_count_q[10]$_DFFE_PN0P_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                  0.00    0.00    0.00 ^ shared_beat_count_q[10]$_DFFE_PN0P_/CK (DFFR_X1)
     1    2.33    0.01    0.07    0.07 ^ shared_beat_count_q[10]$_DFFE_PN0P_/QN (DFFR_X1)
                                         _0023_ (net)
                  0.01    0.00    0.07 ^ _7166_/A (XOR2_X1)
     1    1.66    0.01    0.01    0.08 v _7166_/Z (XOR2_X1)
                                         _1180_ (net)
                  0.01    0.00    0.08 v _7167_/A2 (NAND2_X1)
     1    2.02    0.01    0.02    0.10 ^ _7167_/ZN (NAND2_X1)
                                         _1181_ (net)
                  0.01    0.00    0.10 ^ _7168_/B2 (AOI21_X1)
     1    1.18    0.01    0.01    0.11 v _7168_/ZN (AOI21_X1)
                                         _0322_ (net)
                  0.01    0.00    0.11 v shared_beat_count_q[10]$_DFFE_PN0P_/D (DFFR_X1)
                                  0.11   data arrival time

                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                          0.00    0.00   clock reconvergence pessimism
                                  0.00 ^ shared_beat_count_q[10]$_DFFE_PN0P_/CK (DFFR_X1)
                          0.00    0.00   library hold time
                                  0.00   data required time
-----------------------------------------------------------------------------
                                  0.00   data required time
                                 -0.11   data arrival time
-----------------------------------------------------------------------------
                                  0.11   slack (MET)



```

### Path 3

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_local_temporal_reducer_gqa8_physical_harness_p53_source_only_w8/base/3_global_place.rpt`
- stage: `global_place`
- startpoint: `shared_beat_count_q[10]$_DFFE_PN0P_`
- endpoint: `shared_beat_count_q[10]$_DFFE_PN0P_`
- path_group: `clk`
- path_type: `min`
- slack: `0.1100`
- data_arrival_time: `0.1100`
- data_required_time: `0.0000`

```text
Startpoint: shared_beat_count_q[10]$_DFFE_PN0P_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: shared_beat_count_q[10]$_DFFE_PN0P_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                  0.00    0.00    0.00 ^ shared_beat_count_q[10]$_DFFE_PN0P_/CK (DFFR_X1)
     1    2.38    0.01    0.07    0.07 ^ shared_beat_count_q[10]$_DFFE_PN0P_/QN (DFFR_X1)
                                         _0023_ (net)
                  0.01    0.00    0.07 ^ _7166_/A (XOR2_X1)
     1    1.57    0.01    0.01    0.08 v _7166_/Z (XOR2_X1)
                                         _1180_ (net)
                  0.01    0.00    0.08 v _7167_/A2 (NAND2_X1)
     1    2.10    0.01    0.02    0.10 ^ _7167_/ZN (NAND2_X1)
                                         _1181_ (net)
                  0.01    0.00    0.10 ^ _7168_/B2 (AOI21_X1)
     1    1.08    0.01    0.01    0.11 v _7168_/ZN (AOI21_X1)
                                         _0322_ (net)
                  0.01    0.00    0.11 v shared_beat_count_q[10]$_DFFE_PN0P_/D (DFFR_X1)
                                  0.11   data arrival time

                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                          0.00    0.00   clock reconvergence pessimism
                                  0.00 ^ shared_beat_count_q[10]$_DFFE_PN0P_/CK (DFFR_X1)
                          0.00    0.00   library hold time
                                  0.00   data required time
-----------------------------------------------------------------------------
                                  0.00   data required time
                                 -0.11   data arrival time
-----------------------------------------------------------------------------
                                  0.11   slack (MET)



```

### Path 4

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_local_temporal_reducer_gqa8_physical_harness_p53_source_only_w8/base/3_resizer.rpt`
- stage: `resizer`
- startpoint: `shared_beat_count_q[10]$_DFFE_PN0P_`
- endpoint: `shared_beat_count_q[10]$_DFFE_PN0P_`
- path_group: `clk`
- path_type: `min`
- slack: `0.1100`
- data_arrival_time: `0.1100`
- data_required_time: `0.0000`

```text
Startpoint: shared_beat_count_q[10]$_DFFE_PN0P_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: shared_beat_count_q[10]$_DFFE_PN0P_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                  0.00    0.00    0.00 ^ shared_beat_count_q[10]$_DFFE_PN0P_/CK (DFFR_X1)
     1    2.38    0.01    0.07    0.07 ^ shared_beat_count_q[10]$_DFFE_PN0P_/QN (DFFR_X1)
                                         _0023_ (net)
                  0.01    0.00    0.07 ^ _7166_/A (XOR2_X1)
     1    1.57    0.01    0.01    0.08 v _7166_/Z (XOR2_X1)
                                         _1180_ (net)
                  0.01    0.00    0.08 v _7167_/A2 (NAND2_X1)
     1    2.10    0.01    0.02    0.10 ^ _7167_/ZN (NAND2_X1)
                                         _1181_ (net)
                  0.01    0.00    0.10 ^ _7168_/B2 (AOI21_X1)
     1    1.08    0.01    0.01    0.11 v _7168_/ZN (AOI21_X1)
                                         _0322_ (net)
                  0.01    0.00    0.11 v shared_beat_count_q[10]$_DFFE_PN0P_/D (DFFR_X1)
                                  0.11   data arrival time

                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                          0.00    0.00   clock reconvergence pessimism
                                  0.00 ^ shared_beat_count_q[10]$_DFFE_PN0P_/CK (DFFR_X1)
                          0.00    0.00   library hold time
                                  0.00   data required time
-----------------------------------------------------------------------------
                                  0.00   data required time
                                 -0.11   data arrival time
-----------------------------------------------------------------------------
                                  0.11   slack (MET)



```

### Path 5

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_local_temporal_reducer_gqa8_physical_harness_p53_source_only_w8/base/4_cts_final.rpt`
- stage: `cts`
- startpoint: `shared_beat_count_q[10]$_DFFE_PN0P_`
- endpoint: `shared_beat_count_q[10]$_DFFE_PN0P_`
- path_group: `clk`
- path_type: `min`
- slack: `0.1100`
- data_arrival_time: `0.4800`
- data_required_time: `0.3700`

```text
Startpoint: shared_beat_count_q[10]$_DFFE_PN0P_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: shared_beat_count_q[10]$_DFFE_PN0P_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   56.66    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.02    0.02    0.02 ^ wire2039/A (BUF_X8)
     1   57.60    0.01    0.03    0.05 ^ wire2039/Z (BUF_X8)
                                         net2038 (net)
                  0.03    0.02    0.07 ^ wire2038/A (BUF_X16)
     1   67.37    0.01    0.03    0.09 ^ wire2038/Z (BUF_X16)
                                         net2037 (net)
                  0.03    0.02    0.12 ^ clkbuf_0_clk/A (CLKBUF_X3)
     2   42.49    0.03    0.07    0.19 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.03    0.00    0.19 ^ clkbuf_1_0_0_clk/A (CLKBUF_X3)
     2   13.64    0.01    0.05    0.24 ^ clkbuf_1_0_0_clk/Z (CLKBUF_X3)
...
                                         clknet_2_1__leaf_clk (net)
                  0.04    0.01    0.31 ^ clkbuf_leaf_11_clk/A (CLKBUF_X3)
     9   13.86    0.01    0.05    0.36 ^ clkbuf_leaf_11_clk/Z (CLKBUF_X3)
                                         clknet_leaf_11_clk (net)
                  0.01    0.00    0.36 ^ shared_beat_count_q[10]$_DFFE_PN0P_/CK (DFFR_X1)
                          0.00    0.36   clock reconvergence pessimism
                          0.01    0.37   library hold time
                                  0.37   data required time
-----------------------------------------------------------------------------
                                  0.37   data required time
                                 -0.48   data arrival time
-----------------------------------------------------------------------------
                                  0.11   slack (MET)



```

### Path 6

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_local_temporal_reducer_gqa8_physical_harness_p53_source_only_w8/base/6_finish.rpt`
- stage: `finish`
- startpoint: `shared_beat_count_q[10]$_DFFE_PN0P_`
- endpoint: `shared_beat_count_q[10]$_DFFE_PN0P_`
- path_group: `clk`
- path_type: `min`
- slack: `0.1100`
- data_arrival_time: `0.4300`
- data_required_time: `0.3200`

```text
Startpoint: shared_beat_count_q[10]$_DFFE_PN0P_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: shared_beat_count_q[10]$_DFFE_PN0P_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   36.53    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.01    0.01    0.01 ^ wire2039/A (BUF_X8)
     1   44.48    0.01    0.03    0.04 ^ wire2039/Z (BUF_X8)
                                         net2038 (net)
                  0.02    0.02    0.05 ^ wire2038/A (BUF_X16)
     1   49.87    0.01    0.03    0.08 ^ wire2038/Z (BUF_X16)
                                         net2037 (net)
                  0.02    0.02    0.10 ^ clkbuf_0_clk/A (CLKBUF_X3)
     2   29.95    0.02    0.06    0.15 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.02    0.00    0.16 ^ clkbuf_1_0_0_clk/A (CLKBUF_X3)
     2   10.09    0.01    0.04    0.20 ^ clkbuf_1_0_0_clk/Z (CLKBUF_X3)
...
                                         clknet_2_1__leaf_clk (net)
                  0.03    0.01    0.26 ^ clkbuf_leaf_11_clk/A (CLKBUF_X3)
     9   13.98    0.01    0.05    0.31 ^ clkbuf_leaf_11_clk/Z (CLKBUF_X3)
                                         clknet_leaf_11_clk (net)
                  0.01    0.00    0.31 ^ shared_beat_count_q[10]$_DFFE_PN0P_/CK (DFFR_X1)
                          0.00    0.31   clock reconvergence pessimism
                          0.01    0.32   library hold time
                                  0.32   data required time
-----------------------------------------------------------------------------
                                  0.32   data required time
                                 -0.43   data arrival time
-----------------------------------------------------------------------------
                                  0.11   slack (MET)



```

### Path 7

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_local_temporal_reducer_gqa8_physical_harness_p53_source_only_w8/base/5_global_route.rpt`
- stage: `route`
- startpoint: `shared_beat_count_q[10]$_DFFE_PN0P_`
- endpoint: `shared_beat_count_q[10]$_DFFE_PN0P_`
- path_group: `clk`
- path_type: `min`
- slack: `0.1200`
- data_arrival_time: `0.4800`
- data_required_time: `0.3700`

```text
Startpoint: shared_beat_count_q[10]$_DFFE_PN0P_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: shared_beat_count_q[10]$_DFFE_PN0P_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   54.62    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.02    0.01    0.01 ^ wire2039/A (BUF_X8)
     1   57.05    0.01    0.03    0.05 ^ wire2039/Z (BUF_X8)
                                         net2038 (net)
                  0.03    0.02    0.06 ^ wire2038/A (BUF_X16)
     1   66.88    0.01    0.03    0.09 ^ wire2038/Z (BUF_X16)
                                         net2037 (net)
                  0.03    0.03    0.12 ^ clkbuf_0_clk/A (CLKBUF_X3)
     2   42.60    0.03    0.07    0.19 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.03    0.00    0.19 ^ clkbuf_1_0_0_clk/A (CLKBUF_X3)
     2   13.79    0.01    0.05    0.24 ^ clkbuf_1_0_0_clk/Z (CLKBUF_X3)
...
                                         clknet_2_1__leaf_clk (net)
                  0.04    0.01    0.31 ^ clkbuf_leaf_11_clk/A (CLKBUF_X3)
     9   14.27    0.01    0.05    0.36 ^ clkbuf_leaf_11_clk/Z (CLKBUF_X3)
                                         clknet_leaf_11_clk (net)
                  0.01    0.00    0.36 ^ shared_beat_count_q[10]$_DFFE_PN0P_/CK (DFFR_X1)
                          0.00    0.36   clock reconvergence pessimism
                          0.01    0.37   library hold time
                                  0.37   data required time
-----------------------------------------------------------------------------
                                  0.37   data required time
                                 -0.48   data arrival time
-----------------------------------------------------------------------------
                                  0.12   slack (MET)



```

### Path 8

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_local_temporal_reducer_gqa8_physical_harness_p53_source_only_w8/base/4_cts_final.rpt`
- stage: `cts`
- startpoint: `rst_n (input port clocked by clk)`
- endpoint: `leaf_fire_count_q[28]$_DFFE_PN0P_`
- path_group: `asynchronous`
- path_type: `min`
- slack: `1.4700`
- data_arrival_time: `2.0800`
- data_required_time: `0.6100`

```text
Startpoint: rst_n (input port clocked by clk)
Endpoint: leaf_fire_count_q[28]$_DFFE_PN0P_
          (removal check against rising-edge clock clk)
Path Group: asynchronous
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (propagated)
                          2.00    2.00 ^ input external delay
     1    8.72    0.00    0.00    2.00 ^ rst_n (in)
                                         rst_n (net)
                  0.00    0.00    2.00 ^ input204/A (CLKBUF_X3)
    19   71.72    0.05    0.08    2.08 ^ input204/Z (CLKBUF_X3)
                                         net203 (net)
                  0.05    0.00    2.08 ^ leaf_fire_count_q[28]$_DFFE_PN0P_/RN (DFFR_X1)
                                  2.08   data arrival time

                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   56.66    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.02    0.02    0.02 ^ wire2039/A (BUF_X8)
...
                                         clknet_1_1_0_clk (net)
                  0.01    0.00    0.24 ^ clkbuf_2_3__f_clk/A (CLKBUF_X3)
     7   39.48    0.03    0.06    0.30 ^ clkbuf_2_3__f_clk/Z (CLKBUF_X3)
                                         clknet_2_3__leaf_clk (net)
                  0.03    0.01    0.31 ^ clkbuf_leaf_21_clk/A (CLKBUF_X3)
    10   13.72    0.01    0.05    0.35 ^ clkbuf_leaf_21_clk/Z (CLKBUF_X3)
                                         clknet_leaf_21_clk (net)
                  0.01    0.00    0.36 ^ leaf_fire_count_q[28]$_DFFE_PN0P_/CK (DFFR_X1)
                          0.00    0.36   clock reconvergence pessimism
                          0.25    0.61   library removal time
                                  0.61   data required time
-----------------------------------------------------------------------------
                                  0.61   data required time
                                 -2.08   data arrival time
-----------------------------------------------------------------------------
                                  1.47   slack (MET)
```
