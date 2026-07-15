# OpenROAD Timing Debug Summary

- design_dir: `runs/designs/npu_blocks/dense_gemm_tile_stream_int8_1x8`
- metrics_path: `runs/designs/npu_blocks/dense_gemm_tile_stream_int8_1x8/metrics.csv`
- rows_considered: 4

## Metrics Rows

| param_hash | tag | status | critical_path_ns | density | result_path |
| --- | --- | --- | ---: | ---: | --- |
| e34fdc1b | decode_score_tile_m1x8_v1 | ok | 3.3135 | 0.5 | `/orfs/flow/reports/nangate45/dense_gemm_tile_stream_int8_1x8/decode_score_tile_m1x8_v1/6_finish.rpt` |
| 9f5bcd36 | decode_score_tile_m1x8_v1 | ok | 3.3148 | 0.5 | `/orfs/flow/reports/nangate45/dense_gemm_tile_stream_int8_1x8/decode_score_tile_m1x8_v1/6_finish.rpt` |
| 63bed469 | decode_score_tile_m1x8_v1 | ok | 3.3214 | 0.35 | `/orfs/flow/reports/nangate45/dense_gemm_tile_stream_int8_1x8/decode_score_tile_m1x8_v1/6_finish.rpt` |
| c9117972 | decode_score_tile_m1x8_v1 | ok | 3.3319 | 0.35 | `/orfs/flow/reports/nangate45/dense_gemm_tile_stream_int8_1x8/decode_score_tile_m1x8_v1/6_finish.rpt` |

## Inspected Report Files

- `/orfs/flow/reports/nangate45/dense_gemm_tile_stream_int8_1x8/decode_score_tile_m1x8_v1/6_finish.rpt`
- `/orfs/flow/reports/nangate45/dense_gemm_tile_stream_int8_1x8/decode_score_tile_m1x8_v1/5_global_route.rpt`
- `/orfs/flow/reports/nangate45/dense_gemm_tile_stream_int8_1x8/decode_score_tile_m1x8_v1/5_route_drc.rpt`
- `/orfs/flow/reports/nangate45/dense_gemm_tile_stream_int8_1x8/decode_score_tile_m1x8_v1/4_cts_final.rpt`
- `/orfs/flow/reports/nangate45/dense_gemm_tile_stream_int8_1x8/decode_score_tile_m1x8_v1/3_resizer.rpt`
- `/orfs/flow/reports/nangate45/dense_gemm_tile_stream_int8_1x8/decode_score_tile_m1x8_v1/3_detailed_place.rpt`
- `/orfs/flow/reports/nangate45/dense_gemm_tile_stream_int8_1x8/decode_score_tile_m1x8_v1/3_global_place.rpt`
- `/orfs/flow/reports/nangate45/dense_gemm_tile_stream_int8_1x8/decode_score_tile_m1x8_v1/2_floorplan_final.rpt`
- `/orfs/flow/reports/nangate45/dense_gemm_tile_stream_int8_1x8/decode_score_tile_m1x8_v1/drt_antennas.log`
- `/orfs/flow/reports/nangate45/dense_gemm_tile_stream_int8_1x8/decode_score_tile_m1x8_v1/grt_antennas.log`
- `/orfs/flow/reports/nangate45/dense_gemm_tile_stream_int8_1x8/decode_score_tile_m1x8_v1/metadata-generate.log`

## Preferred Final-Stage Timing Paths

- raw_path_block_count: 208
- unique_path_block_count: 33
- preferred_stage: `finish`

### Path 1

- source: `/orfs/flow/reports/nangate45/dense_gemm_tile_stream_int8_1x8/decode_score_tile_m1x8_v1/6_finish.rpt`
- stage: `finish`
- startpoint: `input_a[7] (input port clocked by clk)`
- endpoint: `accum[4][31]$_DFFE_PN0P_`
- path_group: `clk`
- path_type: `max`
- slack: `-1.2000`
- data_arrival_time: `3.3100`
- data_required_time: `2.1200`

```text
Startpoint: input_a[7] (input port clocked by clk)
Endpoint: accum[4][31]$_DFFE_PN0P_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (propagated)
                          2.00    2.00 v input external delay
     1   26.85    0.00    0.00    2.00 v input_a[7] (in)
                                         input_a[7] (net)
                  0.00    0.00    2.00 v input9/A (BUF_X32)
     6   82.08    0.01    0.02    2.03 v input9/Z (BUF_X32)
                                         net9 (net)
                  0.01    0.01    2.03 v place2980/A (BUF_X32)
     8   33.32    0.00    0.02    2.05 v place2980/Z (BUF_X32)
                                         net2980 (net)
                  0.01    0.01    2.06 v _06804_/A1 (AND2_X4)
     2    7.15    0.01    0.03    2.09 v _06804_/ZN (AND2_X4)
                                         _00540_ (net)
                  0.01    0.00    2.09 v _10992_/B (FA_X1)
     1    3.62    0.01    0.12    2.21 ^ _10992_/S (FA_X1)
...
                                         clknet_2_2__leaf_clk (net)
                  0.03    0.00    2.11 ^ clkbuf_leaf_25_clk/A (CLKBUF_X3)
     6   10.93    0.01    0.04    2.15 ^ clkbuf_leaf_25_clk/Z (CLKBUF_X3)
                                         clknet_leaf_25_clk (net)
                  0.01    0.00    2.15 ^ accum[4][31]$_DFFE_PN0P_/CK (DFFR_X1)
                          0.00    2.15   clock reconvergence pessimism
                         -0.04    2.12   library setup time
                                  2.12   data required time
-----------------------------------------------------------------------------
                                  2.12   data required time
                                 -3.31   data arrival time
-----------------------------------------------------------------------------
                                 -1.20   slack (VIOLATED)



```

### Path 2

- source: `/orfs/flow/reports/nangate45/dense_gemm_tile_stream_int8_1x8/decode_score_tile_m1x8_v1/6_finish.rpt`
- stage: `finish`
- startpoint: `rst_n (input port clocked by clk)`
- endpoint: `accum[2][2]$_DFFE_PN0P_ (recovery check against rising-edge clock clk)`
- path_group: `asynchronous`
- path_type: `max`
- slack: `0.0700`
- data_arrival_time: `2.1400`
- data_required_time: `2.2100`

```text
Startpoint: rst_n (input port clocked by clk)
Endpoint: accum[2][2]$_DFFE_PN0P_ (recovery check against rising-edge clock clk)
Path Group: asynchronous
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (propagated)
                          2.00    2.00 ^ input external delay
     1    7.60    0.00    0.00    2.00 ^ rst_n (in)
                                         rst_n (net)
                  0.00    0.00    2.00 ^ input77/A (CLKBUF_X3)
     2   22.20    0.02    0.04    2.04 ^ input77/Z (CLKBUF_X3)
                                         net77 (net)
                  0.02    0.01    2.05 ^ place2996/A (BUF_X16)
    18   99.14    0.01    0.03    2.08 ^ place2996/Z (BUF_X16)
                                         net2996 (net)
                  0.03    0.02    2.10 ^ place3008/A (BUF_X8)
    29   65.30    0.02    0.04    2.13 ^ place3008/Z (BUF_X8)
                                         net3008 (net)
                  0.02    0.01    2.14 ^ accum[2][2]$_DFFE_PN0P_/RN (DFFR_X1)
                                  2.14   data arrival time

...
                                         clknet_0_clk (net)
                  0.02    0.00    2.05 ^ clkbuf_2_1__f_clk/A (CLKBUF_X3)
    11   35.89    0.03    0.06    2.11 ^ clkbuf_2_1__f_clk/Z (CLKBUF_X3)
                                         clknet_2_1__leaf_clk (net)
                  0.03    0.00    2.11 ^ clkbuf_leaf_7_clk/A (CLKBUF_X3)
     6    9.17    0.01    0.04    2.15 ^ clkbuf_leaf_7_clk/Z (CLKBUF_X3)
                                         clknet_leaf_7_clk (net)
                  0.01    0.00    2.15 ^ accum[2][2]$_DFFE_PN0P_/CK (DFFR_X1)
                          0.00    2.15   clock reconvergence pessimism
                          0.06    2.21   library recovery time
                                  2.21   data required time
-----------------------------------------------------------------------------
                                  2.21   data required time
                                 -2.14   data arrival time
-----------------------------------------------------------------------------
                                  0.07   slack (MET)
```

### Path 3

- source: `/orfs/flow/reports/nangate45/dense_gemm_tile_stream_int8_1x8/decode_score_tile_m1x8_v1/6_finish.rpt`
- stage: `finish`
- startpoint: `accum[7][24]$_DFFE_PN0P_`
- endpoint: `accum[7][24]$_DFFE_PN0P_`
- path_group: `clk`
- path_type: `min`
- slack: `0.1100`
- data_arrival_time: `0.2700`
- data_required_time: `0.1600`

```text
Startpoint: accum[7][24]$_DFFE_PN0P_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: accum[7][24]$_DFFE_PN0P_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   26.39    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.01    0.01    0.01 ^ clkbuf_0_clk/A (CLKBUF_X3)
     4   19.66    0.02    0.04    0.05 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.02    0.00    0.05 ^ clkbuf_2_2__f_clk/A (CLKBUF_X3)
    12   35.01    0.03    0.06    0.11 ^ clkbuf_2_2__f_clk/Z (CLKBUF_X3)
                                         clknet_2_2__leaf_clk (net)
                  0.03    0.00    0.11 ^ clkbuf_leaf_32_clk/A (CLKBUF_X3)
     7   10.83    0.01    0.04    0.15 ^ clkbuf_leaf_32_clk/Z (CLKBUF_X3)
                                         clknet_leaf_32_clk (net)
                  0.01    0.00    0.15 ^ accum[7][24]$_DFFE_PN0P_/CK (DFFR_X1)
     2    5.18    0.01    0.10    0.25 v accum[7][24]$_DFFE_PN0P_/Q (DFFR_X1)
...
                                         clknet_2_2__leaf_clk (net)
                  0.03    0.00    0.11 ^ clkbuf_leaf_32_clk/A (CLKBUF_X3)
     7   10.83    0.01    0.04    0.15 ^ clkbuf_leaf_32_clk/Z (CLKBUF_X3)
                                         clknet_leaf_32_clk (net)
                  0.01    0.00    0.15 ^ accum[7][24]$_DFFE_PN0P_/CK (DFFR_X1)
                          0.00    0.15   clock reconvergence pessimism
                          0.01    0.16   library hold time
                                  0.16   data required time
-----------------------------------------------------------------------------
                                  0.16   data required time
                                 -0.27   data arrival time
-----------------------------------------------------------------------------
                                  0.11   slack (MET)



```

### Path 4

- source: `/orfs/flow/reports/nangate45/dense_gemm_tile_stream_int8_1x8/decode_score_tile_m1x8_v1/6_finish.rpt`
- stage: `finish`
- startpoint: `accum[2][3]$_DFFE_PN0P_`
- endpoint: `accum[2][31]$_DFFE_PN0P_`
- path_group: `clk`
- path_type: `max`
- slack: `1.3100`
- data_arrival_time: `0.8100`
- data_required_time: `2.1200`

```text
Startpoint: accum[2][3]$_DFFE_PN0P_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: accum[2][31]$_DFFE_PN0P_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

  Delay    Time   Description
---------------------------------------------------------
   0.00    0.00   clock clk (rise edge)
   0.00    0.00   clock source latency
   0.00    0.00 ^ clk (in)
   0.05    0.05 ^ clkbuf_0_clk/Z (CLKBUF_X3)
   0.06    0.11 ^ clkbuf_2_0__f_clk/Z (CLKBUF_X3)
   0.04    0.15 ^ clkbuf_leaf_1_clk/Z (CLKBUF_X3)
   0.00    0.16 ^ accum[2][3]$_DFFE_PN0P_/CK (DFFR_X1)
   0.12    0.27 ^ accum[2][3]$_DFFE_PN0P_/Q (DFFR_X1)
   0.08    0.35 ^ _11547_/S (HA_X1)
   0.03    0.38 v _08701_/ZN (NAND3_X1)
   0.06    0.45 ^ _08704_/ZN (OAI221_X2)
   0.03    0.48 v _08713_/ZN (AOI221_X2)
   0.03    0.51 v place1858/Z (BUF_X4)
   0.04    0.55 ^ _08772_/ZN (AOI22_X4)
   0.03    0.59 v _08816_/ZN (AOI221_X2)
...
   0.00    2.00 ^ clk (in)
   0.05    2.05 ^ clkbuf_0_clk/Z (CLKBUF_X3)
   0.06    2.11 ^ clkbuf_2_3__f_clk/Z (CLKBUF_X3)
   0.04    2.15 ^ clkbuf_leaf_19_clk/Z (CLKBUF_X3)
   0.00    2.15 ^ accum[2][31]$_DFFE_PN0P_/CK (DFFR_X1)
   0.00    2.15   clock reconvergence pessimism
  -0.03    2.12   library setup time
           2.12   data required time
---------------------------------------------------------
           2.12   data required time
          -0.81   data arrival time
---------------------------------------------------------
           1.31   slack (MET)



```

### Path 5

- source: `/orfs/flow/reports/nangate45/dense_gemm_tile_stream_int8_1x8/decode_score_tile_m1x8_v1/6_finish.rpt`
- stage: `finish`
- startpoint: `rst_n (input port clocked by clk)`
- endpoint: `accum[4][10]$_DFFE_PN0P_ (removal check against rising-edge clock clk)`
- path_group: `asynchronous`
- path_type: `min`
- slack: `1.7200`
- data_arrival_time: `2.0900`
- data_required_time: `0.3700`

```text
Startpoint: rst_n (input port clocked by clk)
Endpoint: accum[4][10]$_DFFE_PN0P_ (removal check against rising-edge clock clk)
Path Group: asynchronous
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (propagated)
                          2.00    2.00 ^ input external delay
     1    7.60    0.00    0.00    2.00 ^ rst_n (in)
                                         rst_n (net)
                  0.00    0.00    2.00 ^ input77/A (CLKBUF_X3)
     2   22.20    0.02    0.04    2.04 ^ input77/Z (CLKBUF_X3)
                                         net77 (net)
                  0.02    0.01    2.05 ^ place2996/A (BUF_X16)
    18   99.14    0.01    0.03    2.08 ^ place2996/Z (BUF_X16)
                                         net2996 (net)
                  0.03    0.02    2.09 ^ accum[4][10]$_DFFE_PN0P_/RN (DFFR_X1)
                                  2.09   data arrival time

                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   26.39    0.00    0.00    0.00 ^ clk (in)
...
                                         clknet_0_clk (net)
                  0.02    0.00    0.05 ^ clkbuf_2_0__f_clk/A (CLKBUF_X3)
    14   38.46    0.03    0.06    0.11 ^ clkbuf_2_0__f_clk/Z (CLKBUF_X3)
                                         clknet_2_0__leaf_clk (net)
                  0.03    0.00    0.11 ^ clkbuf_leaf_37_clk/A (CLKBUF_X3)
     7    9.95    0.01    0.04    0.15 ^ clkbuf_leaf_37_clk/Z (CLKBUF_X3)
                                         clknet_leaf_37_clk (net)
                  0.01    0.00    0.16 ^ accum[4][10]$_DFFE_PN0P_/CK (DFFR_X1)
                          0.00    0.16   clock reconvergence pessimism
                          0.22    0.37   library removal time
                                  0.37   data required time
-----------------------------------------------------------------------------
                                  0.37   data required time
                                 -2.09   data arrival time
-----------------------------------------------------------------------------
                                  1.72   slack (MET)
```


## Worst Timing Paths Across All Stages

### Path 1

- source: `/orfs/flow/reports/nangate45/dense_gemm_tile_stream_int8_1x8/decode_score_tile_m1x8_v1/2_floorplan_final.rpt`
- stage: `floorplan`
- startpoint: `input_a[3] (input port clocked by clk)`
- endpoint: `accum[7][31]$_DFFE_PN0P_`
- path_group: `clk`
- path_type: `max`
- slack: `-1.4100`
- data_arrival_time: `3.3700`
- data_required_time: `1.9600`

```text
Startpoint: input_a[3] (input port clocked by clk)
Endpoint: accum[7][31]$_DFFE_PN0P_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                          2.00    2.00 v input external delay
     1   23.57    0.00    0.00    2.00 v input_a[3] (in)
                                         input_a[3] (net)
                  0.00    0.00    2.00 v _06502_/A (BUF_X32)
    10   41.01    0.01    0.02    2.02 v _06502_/Z (BUF_X32)
                                         _02638_ (net)
                  0.01    0.00    2.02 v _06535_/A (BUF_X16)
    10   15.21    0.00    0.02    2.04 v _06535_/Z (BUF_X16)
                                         _02654_ (net)
                  0.00    0.00    2.04 v _06536_/A1 (AND2_X4)
     1    3.40    0.01    0.02    2.07 v _06536_/ZN (AND2_X4)
                                         _00062_ (net)
                  0.01    0.00    2.07 v _10811_/B (FA_X1)
     1    3.25    0.01    0.12    2.19 ^ _10811_/S (FA_X1)
...
                                  3.37   data arrival time

                  0.00    2.00    2.00   clock clk (rise edge)
                          0.00    2.00   clock network delay (ideal)
                          0.00    2.00   clock reconvergence pessimism
                                  2.00 ^ accum[7][31]$_DFFE_PN0P_/CK (DFFR_X1)
                         -0.04    1.96   library setup time
                                  1.96   data required time
-----------------------------------------------------------------------------
                                  1.96   data required time
                                 -3.37   data arrival time
-----------------------------------------------------------------------------
                                 -1.41   slack (VIOLATED)



```

### Path 2

- source: `/orfs/flow/reports/nangate45/dense_gemm_tile_stream_int8_1x8/decode_score_tile_m1x8_v1/3_detailed_place.rpt`
- stage: `detailed_place`
- startpoint: `input_a[6] (input port clocked by clk)`
- endpoint: `accum[5][31]$_DFFE_PN0P_`
- path_group: `clk`
- path_type: `max`
- slack: `-1.3800`
- data_arrival_time: `3.3400`
- data_required_time: `1.9600`

```text
Startpoint: input_a[6] (input port clocked by clk)
Endpoint: accum[5][31]$_DFFE_PN0P_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                          2.00    2.00 ^ input external delay
     1    5.64    0.00    0.00    2.00 ^ input_a[6] (in)
                                         input_a[6] (net)
                  0.00    0.00    2.00 ^ input8/A (BUF_X2)
    12   42.29    0.05    0.06    2.06 ^ input8/Z (BUF_X2)
                                         net8 (net)
                  0.05    0.01    2.07 ^ place2993/A (BUF_X2)
     4    9.06    0.01    0.04    2.11 ^ place2993/Z (BUF_X2)
                                         net2993 (net)
                  0.01    0.00    2.11 ^ place2994/A (BUF_X2)
     6    9.35    0.01    0.03    2.14 ^ place2994/Z (BUF_X2)
                                         net2994 (net)
                  0.01    0.00    2.14 ^ _06691_/A1 (NAND2_X1)
     1    2.93    0.01    0.02    2.15 v _06691_/ZN (NAND2_X1)
...
                                  3.34   data arrival time

                  0.00    2.00    2.00   clock clk (rise edge)
                          0.00    2.00   clock network delay (ideal)
                          0.00    2.00   clock reconvergence pessimism
                                  2.00 ^ accum[5][31]$_DFFE_PN0P_/CK (DFFR_X1)
                         -0.04    1.96   library setup time
                                  1.96   data required time
-----------------------------------------------------------------------------
                                  1.96   data required time
                                 -3.34   data arrival time
-----------------------------------------------------------------------------
                                 -1.38   slack (VIOLATED)



```

### Path 3

- source: `/orfs/flow/reports/nangate45/dense_gemm_tile_stream_int8_1x8/decode_score_tile_m1x8_v1/3_global_place.rpt`
- stage: `global_place`
- startpoint: `input_a[6] (input port clocked by clk)`
- endpoint: `accum[5][31]$_DFFE_PN0P_`
- path_group: `clk`
- path_type: `max`
- slack: `-1.3800`
- data_arrival_time: `3.3400`
- data_required_time: `1.9600`

```text
Startpoint: input_a[6] (input port clocked by clk)
Endpoint: accum[5][31]$_DFFE_PN0P_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                          2.00    2.00 ^ input external delay
     1    5.70    0.00    0.00    2.00 ^ input_a[6] (in)
                                         input_a[6] (net)
                  0.00    0.00    2.00 ^ input8/A (BUF_X2)
    12   42.15    0.05    0.06    2.06 ^ input8/Z (BUF_X2)
                                         net8 (net)
                  0.05    0.01    2.07 ^ place2993/A (BUF_X2)
     4    8.67    0.01    0.04    2.11 ^ place2993/Z (BUF_X2)
                                         net2993 (net)
                  0.01    0.00    2.11 ^ place2994/A (BUF_X2)
     6    9.26    0.01    0.03    2.14 ^ place2994/Z (BUF_X2)
                                         net2994 (net)
                  0.01    0.00    2.14 ^ _06691_/A1 (NAND2_X1)
     1    2.82    0.01    0.02    2.15 v _06691_/ZN (NAND2_X1)
...
                                  3.34   data arrival time

                  0.00    2.00    2.00   clock clk (rise edge)
                          0.00    2.00   clock network delay (ideal)
                          0.00    2.00   clock reconvergence pessimism
                                  2.00 ^ accum[5][31]$_DFFE_PN0P_/CK (DFFR_X1)
                         -0.04    1.96   library setup time
                                  1.96   data required time
-----------------------------------------------------------------------------
                                  1.96   data required time
                                 -3.34   data arrival time
-----------------------------------------------------------------------------
                                 -1.38   slack (VIOLATED)



```

### Path 4

- source: `/orfs/flow/reports/nangate45/dense_gemm_tile_stream_int8_1x8/decode_score_tile_m1x8_v1/3_resizer.rpt`
- stage: `resizer`
- startpoint: `input_a[6] (input port clocked by clk)`
- endpoint: `accum[5][31]$_DFFE_PN0P_`
- path_group: `clk`
- path_type: `max`
- slack: `-1.3800`
- data_arrival_time: `3.3400`
- data_required_time: `1.9600`

```text
Startpoint: input_a[6] (input port clocked by clk)
Endpoint: accum[5][31]$_DFFE_PN0P_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                          2.00    2.00 ^ input external delay
     1    5.70    0.00    0.00    2.00 ^ input_a[6] (in)
                                         input_a[6] (net)
                  0.00    0.00    2.00 ^ input8/A (BUF_X2)
    12   42.15    0.05    0.06    2.06 ^ input8/Z (BUF_X2)
                                         net8 (net)
                  0.05    0.01    2.07 ^ place2993/A (BUF_X2)
     4    8.67    0.01    0.04    2.11 ^ place2993/Z (BUF_X2)
                                         net2993 (net)
                  0.01    0.00    2.11 ^ place2994/A (BUF_X2)
     6    9.26    0.01    0.03    2.14 ^ place2994/Z (BUF_X2)
                                         net2994 (net)
                  0.01    0.00    2.14 ^ _06691_/A1 (NAND2_X1)
     1    2.82    0.01    0.02    2.15 v _06691_/ZN (NAND2_X1)
...
                                  3.34   data arrival time

                  0.00    2.00    2.00   clock clk (rise edge)
                          0.00    2.00   clock network delay (ideal)
                          0.00    2.00   clock reconvergence pessimism
                                  2.00 ^ accum[5][31]$_DFFE_PN0P_/CK (DFFR_X1)
                         -0.04    1.96   library setup time
                                  1.96   data required time
-----------------------------------------------------------------------------
                                  1.96   data required time
                                 -3.34   data arrival time
-----------------------------------------------------------------------------
                                 -1.38   slack (VIOLATED)



```

### Path 5

- source: `/orfs/flow/reports/nangate45/dense_gemm_tile_stream_int8_1x8/decode_score_tile_m1x8_v1/5_global_route.rpt`
- stage: `route`
- startpoint: `input_a[7] (input port clocked by clk)`
- endpoint: `accum[4][31]$_DFFE_PN0P_`
- path_group: `clk`
- path_type: `max`
- slack: `-1.2000`
- data_arrival_time: `3.3200`
- data_required_time: `2.1300`

```text
Startpoint: input_a[7] (input port clocked by clk)
Endpoint: accum[4][31]$_DFFE_PN0P_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (propagated)
                          2.00    2.00 v input external delay
     1   28.11    0.00    0.00    2.00 v input_a[7] (in)
                                         input_a[7] (net)
                  0.00    0.00    2.00 v input9/A (BUF_X32)
     6   82.78    0.01    0.02    2.03 v input9/Z (BUF_X32)
                                         net9 (net)
                  0.01    0.01    2.03 v place2980/A (BUF_X32)
     8   33.17    0.00    0.02    2.06 v place2980/Z (BUF_X32)
                                         net2980 (net)
                  0.01    0.01    2.06 v _06804_/A1 (AND2_X4)
     2    7.31    0.01    0.03    2.09 v _06804_/ZN (AND2_X4)
                                         _00540_ (net)
                  0.01    0.00    2.09 v _10992_/B (FA_X1)
     1    3.74    0.02    0.12    2.21 ^ _10992_/S (FA_X1)
...
                                         clknet_2_2__leaf_clk (net)
                  0.03    0.00    2.12 ^ clkbuf_leaf_25_clk/A (CLKBUF_X3)
     6   10.93    0.01    0.04    2.16 ^ clkbuf_leaf_25_clk/Z (CLKBUF_X3)
                                         clknet_leaf_25_clk (net)
                  0.01    0.00    2.16 ^ accum[4][31]$_DFFE_PN0P_/CK (DFFR_X1)
                          0.00    2.16   clock reconvergence pessimism
                         -0.04    2.13   library setup time
                                  2.13   data required time
-----------------------------------------------------------------------------
                                  2.13   data required time
                                 -3.32   data arrival time
-----------------------------------------------------------------------------
                                 -1.20   slack (VIOLATED)



```

### Path 6

- source: `/orfs/flow/reports/nangate45/dense_gemm_tile_stream_int8_1x8/decode_score_tile_m1x8_v1/6_finish.rpt`
- stage: `finish`
- startpoint: `input_a[7] (input port clocked by clk)`
- endpoint: `accum[4][31]$_DFFE_PN0P_`
- path_group: `clk`
- path_type: `max`
- slack: `-1.2000`
- data_arrival_time: `3.3100`
- data_required_time: `2.1200`

```text
Startpoint: input_a[7] (input port clocked by clk)
Endpoint: accum[4][31]$_DFFE_PN0P_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (propagated)
                          2.00    2.00 v input external delay
     1   26.85    0.00    0.00    2.00 v input_a[7] (in)
                                         input_a[7] (net)
                  0.00    0.00    2.00 v input9/A (BUF_X32)
     6   82.08    0.01    0.02    2.03 v input9/Z (BUF_X32)
                                         net9 (net)
                  0.01    0.01    2.03 v place2980/A (BUF_X32)
     8   33.32    0.00    0.02    2.05 v place2980/Z (BUF_X32)
                                         net2980 (net)
                  0.01    0.01    2.06 v _06804_/A1 (AND2_X4)
     2    7.15    0.01    0.03    2.09 v _06804_/ZN (AND2_X4)
                                         _00540_ (net)
                  0.01    0.00    2.09 v _10992_/B (FA_X1)
     1    3.62    0.01    0.12    2.21 ^ _10992_/S (FA_X1)
...
                                         clknet_2_2__leaf_clk (net)
                  0.03    0.00    2.11 ^ clkbuf_leaf_25_clk/A (CLKBUF_X3)
     6   10.93    0.01    0.04    2.15 ^ clkbuf_leaf_25_clk/Z (CLKBUF_X3)
                                         clknet_leaf_25_clk (net)
                  0.01    0.00    2.15 ^ accum[4][31]$_DFFE_PN0P_/CK (DFFR_X1)
                          0.00    2.15   clock reconvergence pessimism
                         -0.04    2.12   library setup time
                                  2.12   data required time
-----------------------------------------------------------------------------
                                  2.12   data required time
                                 -3.31   data arrival time
-----------------------------------------------------------------------------
                                 -1.20   slack (VIOLATED)



```

### Path 7

- source: `/orfs/flow/reports/nangate45/dense_gemm_tile_stream_int8_1x8/decode_score_tile_m1x8_v1/4_cts_final.rpt`
- stage: `cts`
- startpoint: `input_a[7] (input port clocked by clk)`
- endpoint: `accum[2][28]$_DFFE_PN0P_`
- path_group: `clk`
- path_type: `max`
- slack: `-1.1900`
- data_arrival_time: `3.3100`
- data_required_time: `2.1200`

```text
Startpoint: input_a[7] (input port clocked by clk)
Endpoint: accum[2][28]$_DFFE_PN0P_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (propagated)
                          2.00    2.00 v input external delay
     1   28.07    0.00    0.00    2.00 v input_a[7] (in)
                                         input_a[7] (net)
                  0.00    0.00    2.00 v input9/A (BUF_X32)
     5   34.15    0.00    0.02    2.02 v input9/Z (BUF_X32)
                                         net9 (net)
                  0.00    0.00    2.03 v rebuffer3415/A (BUF_X16)
     1   24.04    0.01    0.02    2.05 v rebuffer3415/Z (BUF_X16)
                                         net3415 (net)
                  0.01    0.00    2.05 v place2974/A (BUF_X32)
     7   31.44    0.00    0.02    2.07 v place2974/Z (BUF_X32)
                                         net2974 (net)
                  0.01    0.00    2.07 v _06954_/A1 (AND2_X4)
     2    6.77    0.01    0.03    2.10 v _06954_/ZN (AND2_X4)
...
                                         clknet_2_3__leaf_clk (net)
                  0.03    0.00    2.12 ^ clkbuf_leaf_18_clk/A (CLKBUF_X3)
     6    9.94    0.01    0.04    2.16 ^ clkbuf_leaf_18_clk/Z (CLKBUF_X3)
                                         clknet_leaf_18_clk (net)
                  0.01    0.00    2.16 ^ accum[2][28]$_DFFE_PN0P_/CK (DFFR_X1)
                          0.00    2.16   clock reconvergence pessimism
                         -0.04    2.12   library setup time
                                  2.12   data required time
-----------------------------------------------------------------------------
                                  2.12   data required time
                                 -3.31   data arrival time
-----------------------------------------------------------------------------
                                 -1.19   slack (VIOLATED)



```

### Path 8

- source: `/orfs/flow/reports/nangate45/dense_gemm_tile_stream_int8_1x8/decode_score_tile_m1x8_v1/3_detailed_place.rpt`
- stage: `detailed_place`
- startpoint: `rst_n (input port clocked by clk)`
- endpoint: `accum[3][3]$_DFFE_PN0P_ (recovery check against rising-edge clock clk)`
- path_group: `asynchronous`
- path_type: `max`
- slack: `-0.0900`
- data_arrival_time: `2.1400`
- data_required_time: `2.0500`

```text
Startpoint: rst_n (input port clocked by clk)
Endpoint: accum[3][3]$_DFFE_PN0P_ (recovery check against rising-edge clock clk)
Path Group: asynchronous
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                          2.00    2.00 ^ input external delay
     1    9.44    0.00    0.00    2.00 ^ rst_n (in)
                                         rst_n (net)
                  0.00    0.00    2.00 ^ input77/A (CLKBUF_X3)
     2   25.56    0.02    0.04    2.04 ^ input77/Z (CLKBUF_X3)
                                         net77 (net)
                  0.02    0.01    2.05 ^ place2996/A (BUF_X16)
    18   97.51    0.01    0.03    2.08 ^ place2996/Z (BUF_X16)
                                         net2996 (net)
                  0.02    0.02    2.10 ^ place3008/A (BUF_X8)
    29   65.36    0.02    0.04    2.14 ^ place3008/Z (BUF_X8)
                                         net3008 (net)
                  0.02    0.00    2.14 ^ accum[3][3]$_DFFE_PN0P_/RN (DFFR_X1)
                                  2.14   data arrival time

                  0.00    2.00    2.00   clock clk (rise edge)
                          0.00    2.00   clock network delay (ideal)
                          0.00    2.00   clock reconvergence pessimism
                                  2.00 ^ accum[3][3]$_DFFE_PN0P_/CK (DFFR_X1)
                          0.05    2.05   library recovery time
                                  2.05   data required time
-----------------------------------------------------------------------------
                                  2.05   data required time
                                 -2.14   data arrival time
-----------------------------------------------------------------------------
                                 -0.09   slack (VIOLATED)
```
