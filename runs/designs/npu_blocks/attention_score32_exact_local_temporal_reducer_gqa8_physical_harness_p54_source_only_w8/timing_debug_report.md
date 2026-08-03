# OpenROAD Timing Debug Summary

- design_dir: `runs/designs/npu_blocks/attention_score32_exact_local_temporal_reducer_gqa8_physical_harness_p54_source_only_w8`
- metrics_path: `runs/designs/npu_blocks/attention_score32_exact_local_temporal_reducer_gqa8_physical_harness_p54_source_only_w8/metrics.csv`
- rows_considered: 4

## Metrics Rows

| param_hash | tag | status | critical_path_ns | density | result_path |
| --- | --- | --- | ---: | ---: | --- |
| 6a375b03 | attention_score32_local_temporal_reducer_gqa8_physical_harness_boundary_noshare_v1_r2_6a375b03 | ok | 0.8785 | 0.35 | `/orfs/flow/reports/nangate45/attention_score32_exact_local_temporal_reducer_gqa8_physical_harness_p54_source_only_w8/base/6_finish.rpt` |
| 7a59c40a | attention_score32_local_temporal_reducer_gqa8_physical_harness_boundary_noshare_memguard_v1_r3_7a59c40a | ok | 0.8785 | 0.35 | `/orfs/flow/reports/nangate45/attention_score32_exact_local_temporal_reducer_gqa8_physical_harness_p54_source_only_w8/base/6_finish.rpt` |
| 98397138 | attention_score32_local_temporal_reducer_gqa8_physical_harness_boundary_noshare_v1_r2_98397138 | ok | 0.9874 | 0.35 | `/orfs/flow/reports/nangate45/attention_score32_exact_local_temporal_reducer_gqa8_physical_harness_p54_source_only_w8/base/6_finish.rpt` |
| ef5cc20f | attention_score32_local_temporal_reducer_gqa8_physical_harness_boundary_noshare_memguard_v1_r3_ef5cc20f | ok | 0.9874 | 0.35 | `/orfs/flow/reports/nangate45/attention_score32_exact_local_temporal_reducer_gqa8_physical_harness_p54_source_only_w8/base/6_finish.rpt` |

## Inspected Report Files

- `/orfs/flow/reports/nangate45/attention_score32_exact_local_temporal_reducer_gqa8_physical_harness_p54_source_only_w8/base/6_finish.rpt`
- `/orfs/flow/reports/nangate45/attention_score32_exact_local_temporal_reducer_gqa8_physical_harness_p54_source_only_w8/base/5_global_route.rpt`
- `/orfs/flow/reports/nangate45/attention_score32_exact_local_temporal_reducer_gqa8_physical_harness_p54_source_only_w8/base/5_route_drc.rpt`
- `/orfs/flow/reports/nangate45/attention_score32_exact_local_temporal_reducer_gqa8_physical_harness_p54_source_only_w8/base/4_cts_final.rpt`
- `/orfs/flow/reports/nangate45/attention_score32_exact_local_temporal_reducer_gqa8_physical_harness_p54_source_only_w8/base/3_resizer.rpt`
- `/orfs/flow/reports/nangate45/attention_score32_exact_local_temporal_reducer_gqa8_physical_harness_p54_source_only_w8/base/3_detailed_place.rpt`
- `/orfs/flow/reports/nangate45/attention_score32_exact_local_temporal_reducer_gqa8_physical_harness_p54_source_only_w8/base/3_global_place.rpt`
- `/orfs/flow/reports/nangate45/attention_score32_exact_local_temporal_reducer_gqa8_physical_harness_p54_source_only_w8/base/2_floorplan_final.rpt`
- `/orfs/flow/reports/nangate45/attention_score32_exact_local_temporal_reducer_gqa8_physical_harness_p54_source_only_w8/base/drt_antennas.log`
- `/orfs/flow/reports/nangate45/attention_score32_exact_local_temporal_reducer_gqa8_physical_harness_p54_source_only_w8/base/grt_antennas.log`
- `/orfs/flow/reports/nangate45/attention_score32_exact_local_temporal_reducer_gqa8_physical_harness_p54_source_only_w8/base/metadata-generate.log`

## Preferred Final-Stage Timing Paths

- raw_path_block_count: 208
- unique_path_block_count: 33
- preferred_stage: `finish`

### Path 1

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_local_temporal_reducer_gqa8_physical_harness_p54_source_only_w8/base/6_finish.rpt`
- stage: `finish`
- startpoint: `shared_lfsr_q[31]$_DFFE_PN0P_`
- endpoint: `final_value_q[326]$_DFFE_PN0P_`
- path_group: `clk`
- path_type: `min`
- slack: `0.0600`
- data_arrival_time: `0.4700`
- data_required_time: `0.4100`

```text
Startpoint: shared_lfsr_q[31]$_DFFE_PN0P_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: final_value_q[326]$_DFFE_PN0P_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   41.05    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.02    0.01    0.01 ^ wire2231/A (BUF_X8)
     1   41.42    0.01    0.03    0.04 ^ wire2231/Z (BUF_X8)
                                         net2230 (net)
                  0.02    0.01    0.05 ^ clkbuf_0_clk/A (CLKBUF_X3)
     2   28.78    0.02    0.05    0.11 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.02    0.00    0.11 ^ clkbuf_1_0_0_clk/A (CLKBUF_X3)
     2   19.62    0.02    0.05    0.16 ^ clkbuf_1_0_0_clk/Z (CLKBUF_X3)
                                         clknet_1_0_0_clk (net)
                  0.02    0.00    0.16 ^ clkbuf_2_0_0_clk/A (CLKBUF_X3)
     1   29.68    0.02    0.05    0.21 ^ clkbuf_2_0_0_clk/Z (CLKBUF_X3)
...
                                         clknet_2_2_0_clk (net)
                  0.15    0.12    0.34 ^ clkbuf_leaf_8_clk/A (CLKBUF_X3)
     7    9.71    0.02    0.07    0.41 ^ clkbuf_leaf_8_clk/Z (CLKBUF_X3)
                                         clknet_leaf_8_clk (net)
                  0.02    0.00    0.41 ^ final_value_q[326]$_DFFE_PN0P_/CK (DFFR_X1)
                          0.00    0.41   clock reconvergence pessimism
                          0.01    0.41   library hold time
                                  0.41   data required time
-----------------------------------------------------------------------------
                                  0.41   data required time
                                 -0.47   data arrival time
-----------------------------------------------------------------------------
                                  0.06   slack (MET)



```

### Path 2

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_local_temporal_reducer_gqa8_physical_harness_p54_source_only_w8/base/6_finish.rpt`
- stage: `finish`
- startpoint: `rst_n (input port clocked by clk)`
- endpoint: `cycle_count_q[9]$_DFFE_PN0P_`
- path_group: `asynchronous`
- path_type: `min`
- slack: `1.5200`
- data_arrival_time: `2.0500`
- data_required_time: `0.5300`

```text
Startpoint: rst_n (input port clocked by clk)
Endpoint: cycle_count_q[9]$_DFFE_PN0P_
          (removal check against rising-edge clock clk)
Path Group: asynchronous
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (propagated)
                          2.00    2.00 ^ input external delay
     1   13.54    0.00    0.00    2.00 ^ rst_n (in)
                                         rst_n (net)
                  0.00    0.00    2.00 ^ input205/A (CLKBUF_X3)
     3   37.27    0.02    0.04    2.05 ^ input205/Z (CLKBUF_X3)
                                         net204 (net)
                  0.02    0.00    2.05 ^ cycle_count_q[9]$_DFFE_PN0P_/RN (DFFR_X1)
                                  2.05   data arrival time

                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   41.05    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.02    0.01    0.01 ^ wire2231/A (BUF_X8)
...
                                         clknet_1_1_0_clk (net)
                  0.02    0.00    0.17 ^ clkbuf_2_3_0_clk/A (CLKBUF_X3)
    10   62.06    0.04    0.06    0.23 ^ clkbuf_2_3_0_clk/Z (CLKBUF_X3)
                                         clknet_2_3_0_clk (net)
                  0.06    0.03    0.27 ^ clkbuf_leaf_23_clk/A (CLKBUF_X3)
     7    9.23    0.01    0.05    0.32 ^ clkbuf_leaf_23_clk/Z (CLKBUF_X3)
                                         clknet_leaf_23_clk (net)
                  0.01    0.00    0.32 ^ cycle_count_q[9]$_DFFE_PN0P_/CK (DFFR_X1)
                          0.00    0.32   clock reconvergence pessimism
                          0.21    0.53   library removal time
                                  0.53   data required time
-----------------------------------------------------------------------------
                                  0.53   data required time
                                 -2.05   data arrival time
-----------------------------------------------------------------------------
                                  1.52   slack (MET)
```

### Path 3

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_local_temporal_reducer_gqa8_physical_harness_p54_source_only_w8/base/6_finish.rpt`
- stage: `finish`
- startpoint: `final_value_q[313]$_DFFE_PN0P_`
- endpoint: `final_value[67] (output port clocked by clk)`
- path_group: `clk`
- path_type: `max`
- slack: `7.0100`
- data_arrival_time: `0.9900`
- data_required_time: `8.0000`

```text
Startpoint: final_value_q[313]$_DFFE_PN0P_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: final_value[67] (output port clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   41.05    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.02    0.01    0.01 ^ wire2231/A (BUF_X8)
     1   41.42    0.01    0.03    0.04 ^ wire2231/Z (BUF_X8)
                                         net2230 (net)
                  0.02    0.01    0.05 ^ clkbuf_0_clk/A (CLKBUF_X3)
     2   28.78    0.02    0.05    0.11 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.02    0.00    0.11 ^ clkbuf_1_1_0_clk/A (CLKBUF_X3)
     2   27.28    0.02    0.05    0.17 ^ clkbuf_1_1_0_clk/Z (CLKBUF_X3)
                                         clknet_1_1_0_clk (net)
                  0.02    0.00    0.17 ^ clkbuf_2_2_0_clk/A (CLKBUF_X3)
    10   85.46    0.03    0.05    0.22 ^ clkbuf_2_2_0_clk/Z (CLKBUF_X3)
                                         clknet_2_2_0_clk (net)
...
                  0.03    0.00    0.99 ^ final_value[67] (out)
                                  0.99   data arrival time

                         10.00   10.00   clock clk (rise edge)
                          0.00   10.00   clock network delay (propagated)
                          0.00   10.00   clock reconvergence pessimism
                         -2.00    8.00   output external delay
                                  8.00   data required time
-----------------------------------------------------------------------------
                                  8.00   data required time
                                 -0.99   data arrival time
-----------------------------------------------------------------------------
                                  7.01   slack (MET)



```

### Path 4

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_local_temporal_reducer_gqa8_physical_harness_p54_source_only_w8/base/6_finish.rpt`
- stage: `finish`
- startpoint: `rst_n (input port clocked by clk)`
- endpoint: `source_fold_q[27]$_DFFE_PN0P_`
- path_group: `asynchronous`
- path_type: `max`
- slack: `7.5100`
- data_arrival_time: `2.8600`
- data_required_time: `10.3600`

```text
Startpoint: rst_n (input port clocked by clk)
Endpoint: source_fold_q[27]$_DFFE_PN0P_
          (recovery check against rising-edge clock clk)
Path Group: asynchronous
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (propagated)
                          2.00    2.00 ^ input external delay
     1   13.54    0.00    0.00    2.00 ^ rst_n (in)
                                         rst_n (net)
                  0.00    0.00    2.00 ^ input205/A (CLKBUF_X3)
     3   37.27    0.02    0.04    2.05 ^ input205/Z (CLKBUF_X3)
                                         net204 (net)
                  0.04    0.02    2.07 ^ place2215/A (BUF_X2)
     1   22.85    0.02    0.04    2.11 ^ place2215/Z (BUF_X2)
                                         net2214 (net)
                  0.03    0.01    2.13 ^ place2216/A (BUF_X2)
     2   40.23    0.04    0.05    2.18 ^ place2216/Z (BUF_X2)
                                         net2215 (net)
                  0.06    0.03    2.21 ^ place2217/A (BUF_X2)
     4   13.44    0.02    0.04    2.25 ^ place2217/Z (BUF_X2)
...
                                         clknet_2_0_0_clk (net)
                  0.03    0.01   10.22 ^ wire2234/A (BUF_X8)
    18   65.99    0.01    0.03   10.25 ^ wire2234/Z (BUF_X8)
                                         net2233 (net)
                  0.03    0.02   10.28 ^ clkbuf_leaf_45_clk/A (CLKBUF_X3)
     8    9.57    0.01    0.04   10.32 ^ clkbuf_leaf_45_clk/Z (CLKBUF_X3)
                                         clknet_leaf_45_clk (net)
                  0.01    0.00   10.32 ^ source_fold_q[27]$_DFFE_PN0P_/CK (DFFR_X1)
                          0.00   10.32   clock reconvergence pessimism
                          0.04   10.36   library recovery time
                                 10.36   data required time
-----------------------------------------------------------------------------
                                 10.36   data required time
                                 -2.86   data arrival time
-----------------------------------------------------------------------------
                                  7.51   slack (MET)
```

### Path 5

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_local_temporal_reducer_gqa8_physical_harness_p54_source_only_w8/base/6_finish.rpt`
- stage: `finish`
- startpoint: `shared_beat_count_q[2]$_DFFE_PN0P_`
- endpoint: `source_fold_q[22]$_DFFE_PN0P_`
- path_group: `clk`
- path_type: `max`
- slack: `8.2700`
- data_arrival_time: `2.0200`
- data_required_time: `10.2900`

```text
Startpoint: shared_beat_count_q[2]$_DFFE_PN0P_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: source_fold_q[22]$_DFFE_PN0P_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

  Delay    Time   Description
---------------------------------------------------------
   0.00    0.00   clock clk (rise edge)
   0.00    0.00   clock source latency
   0.00    0.00 ^ clk (in)
   0.04    0.04 ^ wire2231/Z (BUF_X8)
   0.07    0.11 ^ clkbuf_0_clk/Z (CLKBUF_X3)
   0.05    0.16 ^ clkbuf_1_0_0_clk/Z (CLKBUF_X3)
   0.06    0.21 ^ clkbuf_2_0_0_clk/Z (CLKBUF_X3)
   0.04    0.25 ^ wire2234/Z (BUF_X8)
   0.07    0.32 ^ clkbuf_leaf_4_clk/Z (CLKBUF_X3)
   0.00    0.32 ^ shared_beat_count_q[2]$_DFFE_PN0P_/CK (DFFR_X1)
   0.16    0.49 ^ shared_beat_count_q[2]$_DFFE_PN0P_/Q (DFFR_X1)
   0.13    0.62 ^ _7093_/S (HA_X1)
   0.04    0.66 v _7055_/ZN (NAND3_X1)
   0.11    0.77 ^ _7057_/ZN (AOI21_X2)
   0.06    0.83 v _7060_/ZN (NOR2_X2)
...
   0.05   10.16 ^ clkbuf_1_0_0_clk/Z (CLKBUF_X3)
   0.07   10.23 ^ clkbuf_2_1_0_clk/Z (CLKBUF_X3)
   0.04   10.27 ^ max_length2233/Z (BUF_X8)
   0.06   10.33 ^ clkbuf_leaf_34_clk/Z (CLKBUF_X3)
   0.00   10.33 ^ source_fold_q[22]$_DFFE_PN0P_/CK (DFFR_X1)
   0.00   10.33   clock reconvergence pessimism
  -0.04   10.29   library setup time
          10.29   data required time
---------------------------------------------------------
          10.29   data required time
          -2.02   data arrival time
---------------------------------------------------------
           8.27   slack (MET)



```


## Worst Timing Paths Across All Stages

### Path 1

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_local_temporal_reducer_gqa8_physical_harness_p54_source_only_w8/base/6_finish.rpt`
- stage: `finish`
- startpoint: `shared_lfsr_q[31]$_DFFE_PN0P_`
- endpoint: `final_value_q[326]$_DFFE_PN0P_`
- path_group: `clk`
- path_type: `min`
- slack: `0.0600`
- data_arrival_time: `0.4700`
- data_required_time: `0.4100`

```text
Startpoint: shared_lfsr_q[31]$_DFFE_PN0P_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: final_value_q[326]$_DFFE_PN0P_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   41.05    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.02    0.01    0.01 ^ wire2231/A (BUF_X8)
     1   41.42    0.01    0.03    0.04 ^ wire2231/Z (BUF_X8)
                                         net2230 (net)
                  0.02    0.01    0.05 ^ clkbuf_0_clk/A (CLKBUF_X3)
     2   28.78    0.02    0.05    0.11 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.02    0.00    0.11 ^ clkbuf_1_0_0_clk/A (CLKBUF_X3)
     2   19.62    0.02    0.05    0.16 ^ clkbuf_1_0_0_clk/Z (CLKBUF_X3)
                                         clknet_1_0_0_clk (net)
                  0.02    0.00    0.16 ^ clkbuf_2_0_0_clk/A (CLKBUF_X3)
     1   29.68    0.02    0.05    0.21 ^ clkbuf_2_0_0_clk/Z (CLKBUF_X3)
...
                                         clknet_2_2_0_clk (net)
                  0.15    0.12    0.34 ^ clkbuf_leaf_8_clk/A (CLKBUF_X3)
     7    9.71    0.02    0.07    0.41 ^ clkbuf_leaf_8_clk/Z (CLKBUF_X3)
                                         clknet_leaf_8_clk (net)
                  0.02    0.00    0.41 ^ final_value_q[326]$_DFFE_PN0P_/CK (DFFR_X1)
                          0.00    0.41   clock reconvergence pessimism
                          0.01    0.41   library hold time
                                  0.41   data required time
-----------------------------------------------------------------------------
                                  0.41   data required time
                                 -0.47   data arrival time
-----------------------------------------------------------------------------
                                  0.06   slack (MET)



```

### Path 2

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_local_temporal_reducer_gqa8_physical_harness_p54_source_only_w8/base/2_floorplan_final.rpt`
- stage: `floorplan`
- startpoint: `final_exp_sum_q[14]$_DFFE_PN0P_`
- endpoint: `final_exp_sum_q[14]$_DFFE_PN0P_`
- path_group: `clk`
- path_type: `min`
- slack: `0.1100`
- data_arrival_time: `0.1100`
- data_required_time: `0.0000`

```text
Startpoint: final_exp_sum_q[14]$_DFFE_PN0P_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: final_exp_sum_q[14]$_DFFE_PN0P_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                  0.00    0.00    0.00 ^ final_exp_sum_q[14]$_DFFE_PN0P_/CK (DFFR_X1)
     2    1.58    0.01    0.08    0.08 v final_exp_sum_q[14]$_DFFE_PN0P_/Q (DFFR_X1)
                                         final_exp_sum[14] (net)
                  0.01    0.00    0.08 v _4066_/A1 (NAND2_X1)
     1    1.65    0.01    0.01    0.10 ^ _4066_/ZN (NAND2_X1)
                                         _0488_ (net)
                  0.01    0.00    0.10 ^ _4080_/B1 (AOI21_X1)
     1    1.05    0.01    0.01    0.11 v _4080_/ZN (AOI21_X1)
                                         _0155_ (net)
                  0.01    0.00    0.11 v final_exp_sum_q[14]$_DFFE_PN0P_/D (DFFR_X1)
                                  0.11   data arrival time

                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                          0.00    0.00   clock reconvergence pessimism
                                  0.00 ^ final_exp_sum_q[14]$_DFFE_PN0P_/CK (DFFR_X1)
                          0.00    0.00   library hold time
                                  0.00   data required time
-----------------------------------------------------------------------------
                                  0.00   data required time
                                 -0.11   data arrival time
-----------------------------------------------------------------------------
                                  0.11   slack (MET)



```

### Path 3

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_local_temporal_reducer_gqa8_physical_harness_p54_source_only_w8/base/3_detailed_place.rpt`
- stage: `detailed_place`
- startpoint: `shared_beat_count_q[7]$_DFFE_PN0P_`
- endpoint: `shared_beat_count_q[7]$_DFFE_PN0P_`
- path_group: `clk`
- path_type: `min`
- slack: `0.1100`
- data_arrival_time: `0.1100`
- data_required_time: `0.0000`

```text
Startpoint: shared_beat_count_q[7]$_DFFE_PN0P_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: shared_beat_count_q[7]$_DFFE_PN0P_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                  0.00    0.00    0.00 ^ shared_beat_count_q[7]$_DFFE_PN0P_/CK (DFFR_X1)
     1    2.34    0.01    0.07    0.07 ^ shared_beat_count_q[7]$_DFFE_PN0P_/QN (DFFR_X1)
                                         _0020_ (net)
                  0.01    0.00    0.07 ^ _4825_/A (XOR2_X1)
     1    1.65    0.01    0.01    0.08 v _4825_/Z (XOR2_X1)
                                         _1102_ (net)
                  0.01    0.00    0.08 v _4826_/A2 (NAND2_X1)
     1    1.77    0.01    0.02    0.10 ^ _4826_/ZN (NAND2_X1)
                                         _1103_ (net)
                  0.01    0.00    0.10 ^ _4827_/B2 (AOI21_X1)
     1    1.30    0.01    0.01    0.11 v _4827_/ZN (AOI21_X1)
                                         _0331_ (net)
                  0.01    0.00    0.11 v shared_beat_count_q[7]$_DFFE_PN0P_/D (DFFR_X1)
                                  0.11   data arrival time

                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                          0.00    0.00   clock reconvergence pessimism
                                  0.00 ^ shared_beat_count_q[7]$_DFFE_PN0P_/CK (DFFR_X1)
                          0.00    0.00   library hold time
                                  0.00   data required time
-----------------------------------------------------------------------------
                                  0.00   data required time
                                 -0.11   data arrival time
-----------------------------------------------------------------------------
                                  0.11   slack (MET)



```

### Path 4

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_local_temporal_reducer_gqa8_physical_harness_p54_source_only_w8/base/3_global_place.rpt`
- stage: `global_place`
- startpoint: `shared_beat_count_q[4]$_DFFE_PN0P_`
- endpoint: `shared_beat_count_q[4]$_DFFE_PN0P_`
- path_group: `clk`
- path_type: `min`
- slack: `0.1100`
- data_arrival_time: `0.1100`
- data_required_time: `0.0000`

```text
Startpoint: shared_beat_count_q[4]$_DFFE_PN0P_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: shared_beat_count_q[4]$_DFFE_PN0P_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                  0.00    0.00    0.00 ^ shared_beat_count_q[4]$_DFFE_PN0P_/CK (DFFR_X1)
     1    2.34    0.01    0.07    0.07 ^ shared_beat_count_q[4]$_DFFE_PN0P_/QN (DFFR_X1)
                                         _0017_ (net)
                  0.01    0.00    0.07 ^ _4809_/A (XOR2_X1)
     1    1.54    0.01    0.01    0.08 v _4809_/Z (XOR2_X1)
                                         _1089_ (net)
                  0.01    0.00    0.08 v _4810_/A2 (NAND2_X1)
     1    2.09    0.01    0.02    0.10 ^ _4810_/ZN (NAND2_X1)
                                         _1090_ (net)
                  0.01    0.00    0.10 ^ _4811_/B2 (AOI21_X1)
     1    1.08    0.01    0.01    0.11 v _4811_/ZN (AOI21_X1)
                                         _0328_ (net)
                  0.01    0.00    0.11 v shared_beat_count_q[4]$_DFFE_PN0P_/D (DFFR_X1)
                                  0.11   data arrival time

                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                          0.00    0.00   clock reconvergence pessimism
                                  0.00 ^ shared_beat_count_q[4]$_DFFE_PN0P_/CK (DFFR_X1)
                          0.00    0.00   library hold time
                                  0.00   data required time
-----------------------------------------------------------------------------
                                  0.00   data required time
                                 -0.11   data arrival time
-----------------------------------------------------------------------------
                                  0.11   slack (MET)



```

### Path 5

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_local_temporal_reducer_gqa8_physical_harness_p54_source_only_w8/base/3_resizer.rpt`
- stage: `resizer`
- startpoint: `shared_beat_count_q[4]$_DFFE_PN0P_`
- endpoint: `shared_beat_count_q[4]$_DFFE_PN0P_`
- path_group: `clk`
- path_type: `min`
- slack: `0.1100`
- data_arrival_time: `0.1100`
- data_required_time: `0.0000`

```text
Startpoint: shared_beat_count_q[4]$_DFFE_PN0P_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: shared_beat_count_q[4]$_DFFE_PN0P_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                  0.00    0.00    0.00 ^ shared_beat_count_q[4]$_DFFE_PN0P_/CK (DFFR_X1)
     1    2.34    0.01    0.07    0.07 ^ shared_beat_count_q[4]$_DFFE_PN0P_/QN (DFFR_X1)
                                         _0017_ (net)
                  0.01    0.00    0.07 ^ _4809_/A (XOR2_X1)
     1    1.54    0.01    0.01    0.08 v _4809_/Z (XOR2_X1)
                                         _1089_ (net)
                  0.01    0.00    0.08 v _4810_/A2 (NAND2_X1)
     1    2.09    0.01    0.02    0.10 ^ _4810_/ZN (NAND2_X1)
                                         _1090_ (net)
                  0.01    0.00    0.10 ^ _4811_/B2 (AOI21_X1)
     1    1.08    0.01    0.01    0.11 v _4811_/ZN (AOI21_X1)
                                         _0328_ (net)
                  0.01    0.00    0.11 v shared_beat_count_q[4]$_DFFE_PN0P_/D (DFFR_X1)
                                  0.11   data arrival time

                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                          0.00    0.00   clock reconvergence pessimism
                                  0.00 ^ shared_beat_count_q[4]$_DFFE_PN0P_/CK (DFFR_X1)
                          0.00    0.00   library hold time
                                  0.00   data required time
-----------------------------------------------------------------------------
                                  0.00   data required time
                                 -0.11   data arrival time
-----------------------------------------------------------------------------
                                  0.11   slack (MET)



```

### Path 6

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_local_temporal_reducer_gqa8_physical_harness_p54_source_only_w8/base/4_cts_final.rpt`
- stage: `cts`
- startpoint: `shared_lfsr_q[31]$_DFFE_PN0P_`
- endpoint: `final_value_q[326]$_DFFE_PN0P_`
- path_group: `clk`
- path_type: `min`
- slack: `0.1100`
- data_arrival_time: `0.5200`
- data_required_time: `0.4200`

```text
Startpoint: shared_lfsr_q[31]$_DFFE_PN0P_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: final_value_q[326]$_DFFE_PN0P_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   63.39    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.02    0.02    0.02 ^ wire2231/A (BUF_X8)
     1   52.73    0.01    0.03    0.05 ^ wire2231/Z (BUF_X8)
                                         net2230 (net)
                  0.02    0.02    0.07 ^ clkbuf_0_clk/A (CLKBUF_X3)
     2   40.64    0.03    0.07    0.13 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.03    0.00    0.14 ^ clkbuf_1_0_0_clk/A (CLKBUF_X3)
     2   27.13    0.02    0.06    0.19 ^ clkbuf_1_0_0_clk/Z (CLKBUF_X3)
                                         clknet_1_0_0_clk (net)
                  0.02    0.00    0.20 ^ clkbuf_2_0_0_clk/A (CLKBUF_X3)
     1   39.16    0.03    0.06    0.26 ^ clkbuf_2_0_0_clk/Z (CLKBUF_X3)
...
                                         clknet_2_2_0_clk (net)
                  0.11    0.08    0.35 ^ clkbuf_leaf_8_clk/A (CLKBUF_X3)
     7    9.18    0.01    0.06    0.41 ^ clkbuf_leaf_8_clk/Z (CLKBUF_X3)
                                         clknet_leaf_8_clk (net)
                  0.01    0.00    0.41 ^ final_value_q[326]$_DFFE_PN0P_/CK (DFFR_X1)
                          0.00    0.41   clock reconvergence pessimism
                          0.01    0.42   library hold time
                                  0.42   data required time
-----------------------------------------------------------------------------
                                  0.42   data required time
                                 -0.52   data arrival time
-----------------------------------------------------------------------------
                                  0.11   slack (MET)



```

### Path 7

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_local_temporal_reducer_gqa8_physical_harness_p54_source_only_w8/base/5_global_route.rpt`
- stage: `route`
- startpoint: `shared_beat_count_q[4]$_DFFE_PN0P_`
- endpoint: `shared_beat_count_q[4]$_DFFE_PN0P_`
- path_group: `clk`
- path_type: `min`
- slack: `0.1100`
- data_arrival_time: `0.5000`
- data_required_time: `0.3900`

```text
Startpoint: shared_beat_count_q[4]$_DFFE_PN0P_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: shared_beat_count_q[4]$_DFFE_PN0P_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   61.32    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.02    0.02    0.02 ^ wire2231/A (BUF_X8)
     1   52.56    0.01    0.03    0.05 ^ wire2231/Z (BUF_X8)
                                         net2230 (net)
                  0.03    0.02    0.07 ^ clkbuf_0_clk/A (CLKBUF_X3)
     2   40.41    0.03    0.06    0.13 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.03    0.00    0.14 ^ clkbuf_1_0_0_clk/A (CLKBUF_X3)
     2   26.94    0.02    0.06    0.19 ^ clkbuf_1_0_0_clk/Z (CLKBUF_X3)
                                         clknet_1_0_0_clk (net)
                  0.02    0.01    0.20 ^ clkbuf_2_1_0_clk/A (CLKBUF_X3)
     3   63.67    0.05    0.08    0.27 ^ clkbuf_2_1_0_clk/Z (CLKBUF_X3)
...
                                         net2232 (net)
                  0.03    0.02    0.34 ^ clkbuf_leaf_31_clk/A (CLKBUF_X3)
     7    9.46    0.01    0.04    0.38 ^ clkbuf_leaf_31_clk/Z (CLKBUF_X3)
                                         clknet_leaf_31_clk (net)
                  0.01    0.00    0.38 ^ shared_beat_count_q[4]$_DFFE_PN0P_/CK (DFFR_X1)
                          0.00    0.38   clock reconvergence pessimism
                          0.01    0.39   library hold time
                                  0.39   data required time
-----------------------------------------------------------------------------
                                  0.39   data required time
                                 -0.50   data arrival time
-----------------------------------------------------------------------------
                                  0.11   slack (MET)



```

### Path 8

- source: `/orfs/flow/reports/nangate45/attention_score32_exact_local_temporal_reducer_gqa8_physical_harness_p54_source_only_w8/base/4_cts_final.rpt`
- stage: `cts`
- startpoint: `rst_n (input port clocked by clk)`
- endpoint: `cycle_count_q[9]$_DFFE_PN0P_`
- path_group: `asynchronous`
- path_type: `min`
- slack: `1.4500`
- data_arrival_time: `2.0500`
- data_required_time: `0.6000`

```text
Startpoint: rst_n (input port clocked by clk)
Endpoint: cycle_count_q[9]$_DFFE_PN0P_
          (removal check against rising-edge clock clk)
Path Group: asynchronous
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (propagated)
                          2.00    2.00 ^ input external delay
     1   10.67    0.00    0.00    2.00 ^ rst_n (in)
                                         rst_n (net)
                  0.00    0.00    2.00 ^ input205/A (CLKBUF_X3)
     3   29.74    0.02    0.05    2.05 ^ input205/Z (CLKBUF_X3)
                                         net204 (net)
                  0.02    0.00    2.05 ^ cycle_count_q[9]$_DFFE_PN0P_/RN (DFFR_X1)
                                  2.05   data arrival time

                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   63.39    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.02    0.02    0.02 ^ wire2231/A (BUF_X8)
...
                                         clknet_1_1_0_clk (net)
                  0.03    0.01    0.21 ^ clkbuf_2_3_0_clk/A (CLKBUF_X3)
    10   84.27    0.05    0.08    0.29 ^ clkbuf_2_3_0_clk/Z (CLKBUF_X3)
                                         clknet_2_3_0_clk (net)
                  0.07    0.04    0.33 ^ clkbuf_leaf_23_clk/A (CLKBUF_X3)
     7    9.56    0.01    0.05    0.39 ^ clkbuf_leaf_23_clk/Z (CLKBUF_X3)
                                         clknet_leaf_23_clk (net)
                  0.01    0.00    0.39 ^ cycle_count_q[9]$_DFFE_PN0P_/CK (DFFR_X1)
                          0.00    0.39   clock reconvergence pessimism
                          0.21    0.60   library removal time
                                  0.60   data required time
-----------------------------------------------------------------------------
                                  0.60   data required time
                                 -2.05   data arrival time
-----------------------------------------------------------------------------
                                  1.45   slack (MET)
```
