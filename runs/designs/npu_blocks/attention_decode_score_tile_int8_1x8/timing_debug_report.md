# OpenROAD Timing Debug Summary

- design_dir: `runs/designs/npu_blocks/attention_decode_score_tile_int8_1x8`
- metrics_path: `runs/designs/npu_blocks/attention_decode_score_tile_int8_1x8/metrics.csv`
- rows_considered: 4

## Metrics Rows

| param_hash | tag | status | critical_path_ns | density | result_path |
| --- | --- | --- | ---: | ---: | --- |
| 9f5bcd36 | decode_score_tile_m1x8_v1 | ok | 3.3164 | 0.5 | `/orfs/flow/reports/nangate45/attention_decode_score_tile_int8_1x8/decode_score_tile_m1x8_v1/6_finish.rpt` |
| 63bed469 | decode_score_tile_m1x8_v1 | ok | 3.3241 | 0.35 | `/orfs/flow/reports/nangate45/attention_decode_score_tile_int8_1x8/decode_score_tile_m1x8_v1/6_finish.rpt` |
| e34fdc1b | decode_score_tile_m1x8_v1 | ok | 3.3310 | 0.5 | `/orfs/flow/reports/nangate45/attention_decode_score_tile_int8_1x8/decode_score_tile_m1x8_v1/6_finish.rpt` |
| c9117972 | decode_score_tile_m1x8_v1 | ok | 3.3366 | 0.35 | `/orfs/flow/reports/nangate45/attention_decode_score_tile_int8_1x8/decode_score_tile_m1x8_v1/6_finish.rpt` |

## Inspected Report Files

- `/orfs/flow/reports/nangate45/attention_decode_score_tile_int8_1x8/decode_score_tile_m1x8_v1/6_finish.rpt`
- `/orfs/flow/reports/nangate45/attention_decode_score_tile_int8_1x8/decode_score_tile_m1x8_v1/5_global_route.rpt`
- `/orfs/flow/reports/nangate45/attention_decode_score_tile_int8_1x8/decode_score_tile_m1x8_v1/5_route_drc.rpt`
- `/orfs/flow/reports/nangate45/attention_decode_score_tile_int8_1x8/decode_score_tile_m1x8_v1/4_cts_final.rpt`
- `/orfs/flow/reports/nangate45/attention_decode_score_tile_int8_1x8/decode_score_tile_m1x8_v1/3_resizer.rpt`
- `/orfs/flow/reports/nangate45/attention_decode_score_tile_int8_1x8/decode_score_tile_m1x8_v1/3_detailed_place.rpt`
- `/orfs/flow/reports/nangate45/attention_decode_score_tile_int8_1x8/decode_score_tile_m1x8_v1/3_global_place.rpt`
- `/orfs/flow/reports/nangate45/attention_decode_score_tile_int8_1x8/decode_score_tile_m1x8_v1/2_floorplan_final.rpt`
- `/orfs/flow/reports/nangate45/attention_decode_score_tile_int8_1x8/decode_score_tile_m1x8_v1/drt_antennas.log`
- `/orfs/flow/reports/nangate45/attention_decode_score_tile_int8_1x8/decode_score_tile_m1x8_v1/grt_antennas.log`
- `/orfs/flow/reports/nangate45/attention_decode_score_tile_int8_1x8/decode_score_tile_m1x8_v1/metadata-generate.log`

## Preferred Final-Stage Timing Paths

- raw_path_block_count: 208
- unique_path_block_count: 33
- preferred_stage: `finish`

### Path 1

- source: `/orfs/flow/reports/nangate45/attention_decode_score_tile_int8_1x8/decode_score_tile_m1x8_v1/6_finish.rpt`
- stage: `finish`
- startpoint: `input_a[3] (input port clocked by clk)`
- endpoint: `accum[0][31]$_DFFE_PN0N_`
- path_group: `clk`
- path_type: `max`
- slack: `-1.1900`
- data_arrival_time: `3.3200`
- data_required_time: `2.1300`

```text
Startpoint: input_a[3] (input port clocked by clk)
Endpoint: accum[0][31]$_DFFE_PN0N_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (propagated)
                          2.00    2.00 v input external delay
     1   23.42    0.00    0.00    2.00 v input_a[3] (in)
                                         input_a[3] (net)
                  0.00    0.00    2.00 v input5/A (BUF_X16)
     9   32.81    0.01    0.02    2.03 v input5/Z (BUF_X16)
                                         net5 (net)
                  0.01    0.00    2.03 v place3701/A (BUF_X16)
    12   43.65    0.01    0.02    2.05 v place3701/Z (BUF_X16)
                                         net3701 (net)
                  0.01    0.01    2.06 v place3704/A (BUF_X16)
     4   12.09    0.00    0.02    2.08 v place3704/Z (BUF_X16)
                                         net3704 (net)
                  0.00    0.00    2.08 v _07924_/A1 (NAND2_X2)
     1    3.10    0.01    0.01    2.10 ^ _07924_/ZN (NAND2_X2)
...
                                         clknet_3_5_0_clk (net)
                  0.02    0.00    2.12 ^ clkbuf_leaf_42_clk/A (CLKBUF_X3)
     5   13.90    0.01    0.04    2.16 ^ clkbuf_leaf_42_clk/Z (CLKBUF_X3)
                                         clknet_leaf_42_clk (net)
                  0.01    0.00    2.16 ^ accum[0][31]$_DFFE_PN0N_/CK (DFFR_X1)
                          0.00    2.16   clock reconvergence pessimism
                         -0.04    2.13   library setup time
                                  2.13   data required time
-----------------------------------------------------------------------------
                                  2.13   data required time
                                 -3.32   data arrival time
-----------------------------------------------------------------------------
                                 -1.19   slack (VIOLATED)



```

### Path 2

- source: `/orfs/flow/reports/nangate45/attention_decode_score_tile_int8_1x8/decode_score_tile_m1x8_v1/6_finish.rpt`
- stage: `finish`
- startpoint: `rst_n (input port clocked by clk)`
- endpoint: `accum[1][17]$_DFFE_PN0N_`
- path_group: `asynchronous`
- path_type: `max`
- slack: `0.0600`
- data_arrival_time: `2.1700`
- data_required_time: `2.2200`

```text
Startpoint: rst_n (input port clocked by clk)
Endpoint: accum[1][17]$_DFFE_PN0N_
          (recovery check against rising-edge clock clk)
Path Group: asynchronous
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (propagated)
                          2.00    2.00 ^ input external delay
     1    5.12    0.00    0.00    2.00 ^ rst_n (in)
                                         rst_n (net)
                  0.00    0.00    2.00 ^ input77/A (CLKBUF_X3)
     4   33.72    0.03    0.05    2.05 ^ input77/Z (CLKBUF_X3)
                                         net77 (net)
                  0.03    0.01    2.05 ^ place3587/A (BUF_X2)
     2   14.45    0.02    0.04    2.09 ^ place3587/Z (BUF_X2)
                                         net3587 (net)
                  0.02    0.00    2.09 ^ place3588/A (BUF_X16)
    36  100.96    0.01    0.03    2.12 ^ place3588/Z (BUF_X16)
                                         net3588 (net)
                  0.02    0.01    2.13 ^ place3594/A (BUF_X4)
     9   21.80    0.01    0.03    2.16 ^ place3594/Z (BUF_X4)
...
                                         clknet_0_clk (net)
                  0.03    0.00    2.06 ^ clkbuf_3_6_0_clk/A (CLKBUF_X3)
    10   30.60    0.03    0.06    2.12 ^ clkbuf_3_6_0_clk/Z (CLKBUF_X3)
                                         clknet_3_6_0_clk (net)
                  0.03    0.00    2.12 ^ clkbuf_leaf_39_clk/A (CLKBUF_X3)
     8    9.81    0.01    0.04    2.16 ^ clkbuf_leaf_39_clk/Z (CLKBUF_X3)
                                         clknet_leaf_39_clk (net)
                  0.01    0.00    2.16 ^ accum[1][17]$_DFFE_PN0N_/CK (DFFR_X1)
                          0.00    2.16   clock reconvergence pessimism
                          0.06    2.22   library recovery time
                                  2.22   data required time
-----------------------------------------------------------------------------
                                  2.22   data required time
                                 -2.17   data arrival time
-----------------------------------------------------------------------------
                                  0.06   slack (MET)
```

### Path 3

- source: `/orfs/flow/reports/nangate45/attention_decode_score_tile_int8_1x8/decode_score_tile_m1x8_v1/6_finish.rpt`
- stage: `finish`
- startpoint: `result_score_row_q[43]$_DFFE_PN0P_`
- endpoint: `result_score_row_q[43]$_DFFE_PN0P_`
- path_group: `clk`
- path_type: `min`
- slack: `0.1100`
- data_arrival_time: `0.2800`
- data_required_time: `0.1700`

```text
Startpoint: result_score_row_q[43]$_DFFE_PN0P_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: result_score_row_q[43]$_DFFE_PN0P_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   13.88    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.00    0.00    0.00 ^ clkbuf_0_clk/A (CLKBUF_X3)
     8   39.62    0.03    0.06    0.06 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.03    0.00    0.06 ^ clkbuf_3_6_0_clk/A (CLKBUF_X3)
    10   30.60    0.03    0.06    0.12 ^ clkbuf_3_6_0_clk/Z (CLKBUF_X3)
                                         clknet_3_6_0_clk (net)
                  0.03    0.00    0.12 ^ clkbuf_leaf_34_clk/A (CLKBUF_X3)
     8   10.43    0.01    0.04    0.17 ^ clkbuf_leaf_34_clk/Z (CLKBUF_X3)
                                         clknet_leaf_34_clk (net)
                  0.01    0.00    0.17 ^ result_score_row_q[43]$_DFFE_PN0P_/CK (DFFR_X1)
     2    2.75    0.01    0.09    0.26 v result_score_row_q[43]$_DFFE_PN0P_/Q (DFFR_X1)
...
                                         clknet_3_6_0_clk (net)
                  0.03    0.00    0.12 ^ clkbuf_leaf_34_clk/A (CLKBUF_X3)
     8   10.43    0.01    0.04    0.17 ^ clkbuf_leaf_34_clk/Z (CLKBUF_X3)
                                         clknet_leaf_34_clk (net)
                  0.01    0.00    0.17 ^ result_score_row_q[43]$_DFFE_PN0P_/CK (DFFR_X1)
                          0.00    0.17   clock reconvergence pessimism
                          0.01    0.17   library hold time
                                  0.17   data required time
-----------------------------------------------------------------------------
                                  0.17   data required time
                                 -0.28   data arrival time
-----------------------------------------------------------------------------
                                  0.11   slack (MET)



```

### Path 4

- source: `/orfs/flow/reports/nangate45/attention_decode_score_tile_int8_1x8/decode_score_tile_m1x8_v1/6_finish.rpt`
- stage: `finish`
- startpoint: `accum[0][0]$_DFFE_PN0N_`
- endpoint: `accum[0][30]$_DFFE_PN0N_`
- path_group: `clk`
- path_type: `max`
- slack: `1.2800`
- data_arrival_time: `0.8400`
- data_required_time: `2.1200`

```text
Startpoint: accum[0][0]$_DFFE_PN0N_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: accum[0][30]$_DFFE_PN0N_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

  Delay    Time   Description
---------------------------------------------------------
   0.00    0.00   clock clk (rise edge)
   0.00    0.00   clock source latency
   0.00    0.00 ^ clk (in)
   0.06    0.06 ^ clkbuf_0_clk/Z (CLKBUF_X3)
   0.07    0.12 ^ clkbuf_3_4_0_clk/Z (CLKBUF_X3)
   0.04    0.17 ^ clkbuf_leaf_16_clk/Z (CLKBUF_X3)
   0.00    0.17 ^ accum[0][0]$_DFFE_PN0N_/CK (DFFR_X1)
   0.11    0.28 ^ accum[0][0]$_DFFE_PN0N_/Q (DFFR_X1)
   0.04    0.32 ^ _12899_/CO (HA_X1)
   0.01    0.33 v _07887_/ZN (INV_X1)
   0.08    0.41 v _12391_/CO (FA_X1)
   0.02    0.42 ^ _08858_/ZN (INV_X1)
   0.02    0.44 v _08859_/ZN (AOI21_X1)
   0.04    0.48 ^ _08862_/ZN (OAI21_X1)
   0.02    0.50 v _08864_/ZN (AOI211_X2)
...
   0.00    2.00 ^ clk (in)
   0.06    2.06 ^ clkbuf_0_clk/Z (CLKBUF_X3)
   0.06    2.12 ^ clkbuf_3_5_0_clk/Z (CLKBUF_X3)
   0.04    2.16 ^ clkbuf_leaf_14_clk/Z (CLKBUF_X3)
   0.00    2.16 ^ accum[0][30]$_DFFE_PN0N_/CK (DFFR_X1)
   0.00    2.16   clock reconvergence pessimism
  -0.03    2.12   library setup time
           2.12   data required time
---------------------------------------------------------
           2.12   data required time
          -0.84   data arrival time
---------------------------------------------------------
           1.28   slack (MET)



```

### Path 5

- source: `/orfs/flow/reports/nangate45/attention_decode_score_tile_int8_1x8/decode_score_tile_m1x8_v1/6_finish.rpt`
- stage: `finish`
- startpoint: `rst_n (input port clocked by clk)`
- endpoint: `result_score_row_q[43]$_DFFE_PN0P_`
- path_group: `asynchronous`
- path_type: `min`
- slack: `1.7200`
- data_arrival_time: `2.0900`
- data_required_time: `0.3700`

```text
Startpoint: rst_n (input port clocked by clk)
Endpoint: result_score_row_q[43]$_DFFE_PN0P_
          (removal check against rising-edge clock clk)
Path Group: asynchronous
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (propagated)
                          2.00    2.00 ^ input external delay
     1    5.12    0.00    0.00    2.00 ^ rst_n (in)
                                         rst_n (net)
                  0.00    0.00    2.00 ^ input77/A (CLKBUF_X3)
     4   33.72    0.03    0.05    2.05 ^ input77/Z (CLKBUF_X3)
                                         net77 (net)
                  0.03    0.01    2.05 ^ place3587/A (BUF_X2)
     2   14.45    0.02    0.04    2.09 ^ place3587/Z (BUF_X2)
                                         net3587 (net)
                  0.02    0.00    2.09 ^ result_score_row_q[43]$_DFFE_PN0P_/RN (DFFR_X1)
                                  2.09   data arrival time

                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
...
                                         clknet_0_clk (net)
                  0.03    0.00    0.06 ^ clkbuf_3_6_0_clk/A (CLKBUF_X3)
    10   30.60    0.03    0.06    0.12 ^ clkbuf_3_6_0_clk/Z (CLKBUF_X3)
                                         clknet_3_6_0_clk (net)
                  0.03    0.00    0.12 ^ clkbuf_leaf_34_clk/A (CLKBUF_X3)
     8   10.43    0.01    0.04    0.17 ^ clkbuf_leaf_34_clk/Z (CLKBUF_X3)
                                         clknet_leaf_34_clk (net)
                  0.01    0.00    0.17 ^ result_score_row_q[43]$_DFFE_PN0P_/CK (DFFR_X1)
                          0.00    0.17   clock reconvergence pessimism
                          0.21    0.37   library removal time
                                  0.37   data required time
-----------------------------------------------------------------------------
                                  0.37   data required time
                                 -2.09   data arrival time
-----------------------------------------------------------------------------
                                  1.72   slack (MET)
```


## Worst Timing Paths Across All Stages

### Path 1

- source: `/orfs/flow/reports/nangate45/attention_decode_score_tile_int8_1x8/decode_score_tile_m1x8_v1/2_floorplan_final.rpt`
- stage: `floorplan`
- startpoint: `input_a[7] (input port clocked by clk)`
- endpoint: `accum[0][31]$_DFFE_PN0N_`
- path_group: `clk`
- path_type: `max`
- slack: `-1.4800`
- data_arrival_time: `3.4400`
- data_required_time: `1.9600`

```text
Startpoint: input_a[7] (input port clocked by clk)
Endpoint: accum[0][31]$_DFFE_PN0N_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                          2.00    2.00 ^ input external delay
     1   26.70    0.00    0.00    2.00 ^ input_a[7] (in)
                                         input_a[7] (net)
                  0.00    0.00    2.00 ^ _07309_/A (BUF_X32)
     7   51.92    0.01    0.02    2.02 ^ _07309_/Z (BUF_X32)
                                         _02890_ (net)
                  0.01    0.00    2.02 ^ _07322_/A (BUF_X32)
    10   24.28    0.01    0.02    2.04 ^ _07322_/Z (BUF_X32)
                                         _02895_ (net)
                  0.01    0.00    2.04 ^ _07813_/A1 (AND2_X4)
     3   11.78    0.01    0.03    2.07 ^ _07813_/ZN (AND2_X4)
                                         _01042_ (net)
                  0.01    0.00    2.07 ^ _07814_/A (INV_X4)
     2    6.06    0.00    0.01    2.08 v _07814_/ZN (INV_X4)
...
                                  3.44   data arrival time

                  0.00    2.00    2.00   clock clk (rise edge)
                          0.00    2.00   clock network delay (ideal)
                          0.00    2.00   clock reconvergence pessimism
                                  2.00 ^ accum[0][31]$_DFFE_PN0N_/CK (DFFR_X1)
                         -0.04    1.96   library setup time
                                  1.96   data required time
-----------------------------------------------------------------------------
                                  1.96   data required time
                                 -3.44   data arrival time
-----------------------------------------------------------------------------
                                 -1.48   slack (VIOLATED)



```

### Path 2

- source: `/orfs/flow/reports/nangate45/attention_decode_score_tile_int8_1x8/decode_score_tile_m1x8_v1/3_detailed_place.rpt`
- stage: `detailed_place`
- startpoint: `input_b[41] (input port clocked by clk)`
- endpoint: `accum[5][30]$_DFFE_PN0N_`
- path_group: `clk`
- path_type: `max`
- slack: `-1.4000`
- data_arrival_time: `3.3600`
- data_required_time: `1.9600`

```text
Startpoint: input_b[41] (input port clocked by clk)
Endpoint: accum[5][30]$_DFFE_PN0N_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                          2.00    2.00 ^ input external delay
     1   10.96    0.00    0.00    2.00 ^ input_b[41] (in)
                                         input_b[41] (net)
                  0.00    0.00    2.00 ^ input45/A (BUF_X1)
     6   16.03    0.04    0.05    2.05 ^ input45/Z (BUF_X1)
                                         net45 (net)
                  0.04    0.00    2.06 ^ _07435_/A2 (NAND2_X1)
     1    3.71    0.01    0.02    2.08 v _07435_/ZN (NAND2_X1)
                                         _00297_ (net)
                  0.01    0.00    2.08 v _12135_/B (FA_X1)
     1    3.08    0.01    0.12    2.20 ^ _12135_/S (FA_X1)
                                         _06685_ (net)
                  0.01    0.00    2.20 ^ _12137_/CI (FA_X1)
     1    2.90    0.02    0.09    2.30 v _12137_/S (FA_X1)
...
                                  3.36   data arrival time

                  0.00    2.00    2.00   clock clk (rise edge)
                          0.00    2.00   clock network delay (ideal)
                          0.00    2.00   clock reconvergence pessimism
                                  2.00 ^ accum[5][30]$_DFFE_PN0N_/CK (DFFR_X1)
                         -0.04    1.96   library setup time
                                  1.96   data required time
-----------------------------------------------------------------------------
                                  1.96   data required time
                                 -3.36   data arrival time
-----------------------------------------------------------------------------
                                 -1.40   slack (VIOLATED)



```

### Path 3

- source: `/orfs/flow/reports/nangate45/attention_decode_score_tile_int8_1x8/decode_score_tile_m1x8_v1/3_global_place.rpt`
- stage: `global_place`
- startpoint: `input_b[41] (input port clocked by clk)`
- endpoint: `accum[5][30]$_DFFE_PN0N_`
- path_group: `clk`
- path_type: `max`
- slack: `-1.4000`
- data_arrival_time: `3.3600`
- data_required_time: `1.9600`

```text
Startpoint: input_b[41] (input port clocked by clk)
Endpoint: accum[5][30]$_DFFE_PN0N_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                          2.00    2.00 ^ input external delay
     1   10.98    0.00    0.00    2.00 ^ input_b[41] (in)
                                         input_b[41] (net)
                  0.00    0.00    2.00 ^ input45/A (BUF_X1)
     6   16.14    0.04    0.05    2.05 ^ input45/Z (BUF_X1)
                                         net45 (net)
                  0.04    0.00    2.06 ^ _07435_/A2 (NAND2_X1)
     1    3.89    0.01    0.02    2.08 v _07435_/ZN (NAND2_X1)
                                         _00297_ (net)
                  0.01    0.00    2.08 v _12135_/B (FA_X1)
     1    2.82    0.02    0.10    2.18 v _12135_/S (FA_X1)
                                         _06685_ (net)
                  0.02    0.00    2.18 v _12137_/CI (FA_X1)
     1    3.05    0.01    0.12    2.30 ^ _12137_/S (FA_X1)
...
                                  3.36   data arrival time

                  0.00    2.00    2.00   clock clk (rise edge)
                          0.00    2.00   clock network delay (ideal)
                          0.00    2.00   clock reconvergence pessimism
                                  2.00 ^ accum[5][30]$_DFFE_PN0N_/CK (DFFR_X1)
                         -0.04    1.96   library setup time
                                  1.96   data required time
-----------------------------------------------------------------------------
                                  1.96   data required time
                                 -3.36   data arrival time
-----------------------------------------------------------------------------
                                 -1.40   slack (VIOLATED)



```

### Path 4

- source: `/orfs/flow/reports/nangate45/attention_decode_score_tile_int8_1x8/decode_score_tile_m1x8_v1/3_resizer.rpt`
- stage: `resizer`
- startpoint: `input_b[41] (input port clocked by clk)`
- endpoint: `accum[5][30]$_DFFE_PN0N_`
- path_group: `clk`
- path_type: `max`
- slack: `-1.4000`
- data_arrival_time: `3.3600`
- data_required_time: `1.9600`

```text
Startpoint: input_b[41] (input port clocked by clk)
Endpoint: accum[5][30]$_DFFE_PN0N_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                          2.00    2.00 ^ input external delay
     1   10.98    0.00    0.00    2.00 ^ input_b[41] (in)
                                         input_b[41] (net)
                  0.00    0.00    2.00 ^ input45/A (BUF_X1)
     6   16.14    0.04    0.05    2.05 ^ input45/Z (BUF_X1)
                                         net45 (net)
                  0.04    0.00    2.06 ^ _07435_/A2 (NAND2_X1)
     1    3.89    0.01    0.02    2.08 v _07435_/ZN (NAND2_X1)
                                         _00297_ (net)
                  0.01    0.00    2.08 v _12135_/B (FA_X1)
     1    2.82    0.02    0.10    2.18 v _12135_/S (FA_X1)
                                         _06685_ (net)
                  0.02    0.00    2.18 v _12137_/CI (FA_X1)
     1    3.05    0.01    0.12    2.30 ^ _12137_/S (FA_X1)
...
                                  3.36   data arrival time

                  0.00    2.00    2.00   clock clk (rise edge)
                          0.00    2.00   clock network delay (ideal)
                          0.00    2.00   clock reconvergence pessimism
                                  2.00 ^ accum[5][30]$_DFFE_PN0N_/CK (DFFR_X1)
                         -0.04    1.96   library setup time
                                  1.96   data required time
-----------------------------------------------------------------------------
                                  1.96   data required time
                                 -3.36   data arrival time
-----------------------------------------------------------------------------
                                 -1.40   slack (VIOLATED)



```

### Path 5

- source: `/orfs/flow/reports/nangate45/attention_decode_score_tile_int8_1x8/decode_score_tile_m1x8_v1/4_cts_final.rpt`
- stage: `cts`
- startpoint: `input_a[6] (input port clocked by clk)`
- endpoint: `accum[0][30]$_DFFE_PN0N_`
- path_group: `clk`
- path_type: `max`
- slack: `-1.1900`
- data_arrival_time: `3.3200`
- data_required_time: `2.1400`

```text
Startpoint: input_a[6] (input port clocked by clk)
Endpoint: accum[0][30]$_DFFE_PN0N_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (propagated)
                          2.00    2.00 ^ input external delay
     1   40.24    0.00    0.00    2.00 ^ input_a[6] (in)
                                         input_a[6] (net)
                  0.02    0.01    2.01 ^ input8/A (BUF_X32)
     7   42.19    0.01    0.02    2.03 ^ input8/Z (BUF_X32)
                                         net8 (net)
                  0.01    0.00    2.04 ^ place3576/A (BUF_X32)
     8   25.88    0.01    0.02    2.06 ^ place3576/Z (BUF_X32)
                                         net3576 (net)
                  0.01    0.00    2.06 ^ _07815_/A1 (NAND2_X4)
     1    3.77    0.01    0.01    2.07 v _07815_/ZN (NAND2_X4)
                                         _01028_ (net)
                  0.01    0.00    2.07 v _12407_/A (FA_X1)
     1    3.90    0.02    0.10    2.17 v _12407_/S (FA_X1)
...
                                         clknet_3_5_0_clk (net)
                  0.02    0.00    2.13 ^ clkbuf_leaf_14_clk/A (CLKBUF_X3)
     5    9.88    0.01    0.04    2.17 ^ clkbuf_leaf_14_clk/Z (CLKBUF_X3)
                                         clknet_leaf_14_clk (net)
                  0.01    0.00    2.17 ^ accum[0][30]$_DFFE_PN0N_/CK (DFFR_X1)
                          0.00    2.17   clock reconvergence pessimism
                         -0.03    2.14   library setup time
                                  2.14   data required time
-----------------------------------------------------------------------------
                                  2.14   data required time
                                 -3.32   data arrival time
-----------------------------------------------------------------------------
                                 -1.19   slack (VIOLATED)



```

### Path 6

- source: `/orfs/flow/reports/nangate45/attention_decode_score_tile_int8_1x8/decode_score_tile_m1x8_v1/5_global_route.rpt`
- stage: `route`
- startpoint: `input_a[3] (input port clocked by clk)`
- endpoint: `accum[0][31]$_DFFE_PN0N_`
- path_group: `clk`
- path_type: `max`
- slack: `-1.1900`
- data_arrival_time: `3.3300`
- data_required_time: `2.1400`

```text
Startpoint: input_a[3] (input port clocked by clk)
Endpoint: accum[0][31]$_DFFE_PN0N_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (propagated)
                          2.00    2.00 v input external delay
     1   27.67    0.00    0.00    2.00 v input_a[3] (in)
                                         input_a[3] (net)
                  0.00    0.00    2.00 v input5/A (BUF_X16)
     9   32.64    0.01    0.02    2.03 v input5/Z (BUF_X16)
                                         net5 (net)
                  0.01    0.00    2.03 v place3701/A (BUF_X16)
    12   43.13    0.01    0.02    2.05 v place3701/Z (BUF_X16)
                                         net3701 (net)
                  0.01    0.01    2.06 v place3704/A (BUF_X16)
     4   11.80    0.00    0.02    2.08 v place3704/Z (BUF_X16)
                                         net3704 (net)
                  0.00    0.00    2.08 v _07924_/A1 (NAND2_X2)
     1    3.16    0.01    0.01    2.10 ^ _07924_/ZN (NAND2_X2)
...
                                         clknet_3_5_0_clk (net)
                  0.02    0.00    2.13 ^ clkbuf_leaf_42_clk/A (CLKBUF_X3)
     5   13.12    0.01    0.04    2.17 ^ clkbuf_leaf_42_clk/Z (CLKBUF_X3)
                                         clknet_leaf_42_clk (net)
                  0.01    0.00    2.17 ^ accum[0][31]$_DFFE_PN0N_/CK (DFFR_X1)
                          0.00    2.17   clock reconvergence pessimism
                         -0.04    2.14   library setup time
                                  2.14   data required time
-----------------------------------------------------------------------------
                                  2.14   data required time
                                 -3.33   data arrival time
-----------------------------------------------------------------------------
                                 -1.19   slack (VIOLATED)



```

### Path 7

- source: `/orfs/flow/reports/nangate45/attention_decode_score_tile_int8_1x8/decode_score_tile_m1x8_v1/6_finish.rpt`
- stage: `finish`
- startpoint: `input_a[3] (input port clocked by clk)`
- endpoint: `accum[0][31]$_DFFE_PN0N_`
- path_group: `clk`
- path_type: `max`
- slack: `-1.1900`
- data_arrival_time: `3.3200`
- data_required_time: `2.1300`

```text
Startpoint: input_a[3] (input port clocked by clk)
Endpoint: accum[0][31]$_DFFE_PN0N_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (propagated)
                          2.00    2.00 v input external delay
     1   23.42    0.00    0.00    2.00 v input_a[3] (in)
                                         input_a[3] (net)
                  0.00    0.00    2.00 v input5/A (BUF_X16)
     9   32.81    0.01    0.02    2.03 v input5/Z (BUF_X16)
                                         net5 (net)
                  0.01    0.00    2.03 v place3701/A (BUF_X16)
    12   43.65    0.01    0.02    2.05 v place3701/Z (BUF_X16)
                                         net3701 (net)
                  0.01    0.01    2.06 v place3704/A (BUF_X16)
     4   12.09    0.00    0.02    2.08 v place3704/Z (BUF_X16)
                                         net3704 (net)
                  0.00    0.00    2.08 v _07924_/A1 (NAND2_X2)
     1    3.10    0.01    0.01    2.10 ^ _07924_/ZN (NAND2_X2)
...
                                         clknet_3_5_0_clk (net)
                  0.02    0.00    2.12 ^ clkbuf_leaf_42_clk/A (CLKBUF_X3)
     5   13.90    0.01    0.04    2.16 ^ clkbuf_leaf_42_clk/Z (CLKBUF_X3)
                                         clknet_leaf_42_clk (net)
                  0.01    0.00    2.16 ^ accum[0][31]$_DFFE_PN0N_/CK (DFFR_X1)
                          0.00    2.16   clock reconvergence pessimism
                         -0.04    2.13   library setup time
                                  2.13   data required time
-----------------------------------------------------------------------------
                                  2.13   data required time
                                 -3.32   data arrival time
-----------------------------------------------------------------------------
                                 -1.19   slack (VIOLATED)



```

### Path 8

- source: `/orfs/flow/reports/nangate45/attention_decode_score_tile_int8_1x8/decode_score_tile_m1x8_v1/3_detailed_place.rpt`
- stage: `detailed_place`
- startpoint: `rst_n (input port clocked by clk)`
- endpoint: `accum[1][14]$_DFFE_PN0N_`
- path_group: `asynchronous`
- path_type: `max`
- slack: `-0.1100`
- data_arrival_time: `2.1600`
- data_required_time: `2.0500`

```text
Startpoint: rst_n (input port clocked by clk)
Endpoint: accum[1][14]$_DFFE_PN0N_
          (recovery check against rising-edge clock clk)
Path Group: asynchronous
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                          2.00    2.00 ^ input external delay
     1    5.56    0.00    0.00    2.00 ^ rst_n (in)
                                         rst_n (net)
                  0.00    0.00    2.00 ^ input77/A (CLKBUF_X3)
     4   33.95    0.02    0.04    2.04 ^ input77/Z (CLKBUF_X3)
                                         net77 (net)
                  0.03    0.01    2.05 ^ place3587/A (BUF_X2)
     2   14.43    0.02    0.04    2.09 ^ place3587/Z (BUF_X2)
                                         net3587 (net)
                  0.02    0.00    2.09 ^ place3588/A (BUF_X16)
    36  101.47    0.01    0.03    2.12 ^ place3588/Z (BUF_X16)
                                         net3588 (net)
                  0.02    0.01    2.13 ^ place3594/A (BUF_X4)
     9   21.26    0.01    0.03    2.16 ^ place3594/Z (BUF_X4)
                                         net3594 (net)
                  0.01    0.00    2.16 ^ accum[1][14]$_DFFE_PN0N_/RN (DFFR_X1)
                                  2.16   data arrival time

                  0.00    2.00    2.00   clock clk (rise edge)
                          0.00    2.00   clock network delay (ideal)
                          0.00    2.00   clock reconvergence pessimism
                                  2.00 ^ accum[1][14]$_DFFE_PN0N_/CK (DFFR_X1)
                          0.05    2.05   library recovery time
                                  2.05   data required time
-----------------------------------------------------------------------------
                                  2.05   data required time
                                 -2.16   data arrival time
-----------------------------------------------------------------------------
                                 -0.11   slack (VIOLATED)
```
