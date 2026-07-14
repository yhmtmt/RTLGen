# OpenROAD Timing Debug Summary

- design_dir: `runs/designs/npu_blocks/dense_gemm_tile_stream_int8_16x8`
- metrics_path: `runs/designs/npu_blocks/dense_gemm_tile_stream_int8_16x8/metrics.csv`
- rows_considered: 4

## Metrics Rows

| param_hash | tag | status | critical_path_ns | density | result_path |
| --- | --- | --- | ---: | ---: | --- |
| f670b337 | dense_gemm_tile_stream_int8_v1 | ok | 4.3024 | 0.35 | `/orfs/flow/reports/nangate45/dense_gemm_tile_stream_int8_16x8/dense_gemm_tile_stream_int8_v1/6_finish.rpt` |
| 95d8f5f6 | dense_gemm_tile_stream_int8_v1 | ok | 4.3044 | 0.45 | `/orfs/flow/reports/nangate45/dense_gemm_tile_stream_int8_16x8/dense_gemm_tile_stream_int8_v1/6_finish.rpt` |
| 0b32dd12 | dense_gemm_tile_stream_int8_v1 | ok | 4.3324 | 0.45 | `/orfs/flow/reports/nangate45/dense_gemm_tile_stream_int8_16x8/dense_gemm_tile_stream_int8_v1/6_finish.rpt` |
| 620348b1 | dense_gemm_tile_stream_int8_v1 | ok | 4.3727 | 0.35 | `/orfs/flow/reports/nangate45/dense_gemm_tile_stream_int8_16x8/dense_gemm_tile_stream_int8_v1/6_finish.rpt` |

## Inspected Report Files

- `/orfs/flow/reports/nangate45/dense_gemm_tile_stream_int8_16x8/dense_gemm_tile_stream_int8_v1/6_finish.rpt`
- `/orfs/flow/reports/nangate45/dense_gemm_tile_stream_int8_16x8/dense_gemm_tile_stream_int8_v1/5_global_route.rpt`
- `/orfs/flow/reports/nangate45/dense_gemm_tile_stream_int8_16x8/dense_gemm_tile_stream_int8_v1/5_route_drc.rpt`
- `/orfs/flow/reports/nangate45/dense_gemm_tile_stream_int8_16x8/dense_gemm_tile_stream_int8_v1/5_route_drc.rpt-5.rpt`
- `/orfs/flow/reports/nangate45/dense_gemm_tile_stream_int8_16x8/dense_gemm_tile_stream_int8_v1/4_cts_final.rpt`
- `/orfs/flow/reports/nangate45/dense_gemm_tile_stream_int8_16x8/dense_gemm_tile_stream_int8_v1/3_resizer.rpt`
- `/orfs/flow/reports/nangate45/dense_gemm_tile_stream_int8_16x8/dense_gemm_tile_stream_int8_v1/3_detailed_place.rpt`
- `/orfs/flow/reports/nangate45/dense_gemm_tile_stream_int8_16x8/dense_gemm_tile_stream_int8_v1/3_global_place.rpt`
- `/orfs/flow/reports/nangate45/dense_gemm_tile_stream_int8_16x8/dense_gemm_tile_stream_int8_v1/2_floorplan_final.rpt`
- `/orfs/flow/reports/nangate45/dense_gemm_tile_stream_int8_16x8/dense_gemm_tile_stream_int8_v1/congestion-5.rpt`
- `/orfs/flow/reports/nangate45/dense_gemm_tile_stream_int8_16x8/dense_gemm_tile_stream_int8_v1/drt_antennas.log`
- `/orfs/flow/reports/nangate45/dense_gemm_tile_stream_int8_16x8/dense_gemm_tile_stream_int8_v1/grt_antennas.log`
- `/orfs/flow/reports/nangate45/dense_gemm_tile_stream_int8_16x8/dense_gemm_tile_stream_int8_v1/metadata-generate.log`

## Preferred Final-Stage Timing Paths

- raw_path_block_count: 208
- unique_path_block_count: 33
- preferred_stage: `finish`

### Path 1

- source: `/orfs/flow/reports/nangate45/dense_gemm_tile_stream_int8_16x8/dense_gemm_tile_stream_int8_v1/6_finish.rpt`
- stage: `finish`
- startpoint: `accum[126][29]$_DFFE_PN0P_`
- endpoint: `accum[126][29]$_DFFE_PN0P_`
- path_group: `clk`
- path_type: `min`
- slack: `0.1100`
- data_arrival_time: `0.5100`
- data_required_time: `0.4000`

```text
Startpoint: accum[126][29]$_DFFE_PN0P_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: accum[126][29]$_DFFE_PN0P_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   12.24    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.00    0.00    0.00 ^ wire7609/A (BUF_X8)
     1   53.80    0.01    0.02    0.02 ^ wire7609/Z (BUF_X8)
                                         net7609 (net)
                  0.03    0.02    0.05 ^ wire7608/A (BUF_X16)
     1   50.20    0.01    0.03    0.07 ^ wire7608/Z (BUF_X16)
                                         net7608 (net)
                  0.03    0.02    0.09 ^ clkbuf_0_clk/A (CLKBUF_X3)
     4   37.97    0.03    0.06    0.16 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.03    0.01    0.16 ^ clkbuf_2_1_0_clk/A (CLKBUF_X3)
     2   22.29    0.02    0.05    0.21 ^ clkbuf_2_1_0_clk/Z (CLKBUF_X3)
...
                                         clknet_6_21_0_clk (net)
                  0.03    0.00    0.35 ^ clkbuf_leaf_507_clk/A (CLKBUF_X3)
     5   11.52    0.01    0.04    0.40 ^ clkbuf_leaf_507_clk/Z (CLKBUF_X3)
                                         clknet_leaf_507_clk (net)
                  0.01    0.00    0.40 ^ accum[126][29]$_DFFE_PN0P_/CK (DFFR_X1)
                          0.00    0.40   clock reconvergence pessimism
                          0.01    0.40   library hold time
                                  0.40   data required time
-----------------------------------------------------------------------------
                                  0.40   data required time
                                 -0.51   data arrival time
-----------------------------------------------------------------------------
                                  0.11   slack (MET)



```

### Path 2

- source: `/orfs/flow/reports/nangate45/dense_gemm_tile_stream_int8_16x8/dense_gemm_tile_stream_int8_v1/6_finish.rpt`
- stage: `finish`
- startpoint: `input_b[9] (input port clocked by clk)`
- endpoint: `accum[25][31]$_DFFE_PN0P_`
- path_group: `clk`
- path_type: `max`
- slack: `1.0300`
- data_arrival_time: `4.3300`
- data_required_time: `5.3600`

```text
Startpoint: input_b[9] (input port clocked by clk)
Endpoint: accum[25][31]$_DFFE_PN0P_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (propagated)
                          2.00    2.00 ^ input external delay
     1    6.08    0.00    0.00    2.00 ^ input_b[9] (in)
                                         input_b[9] (net)
                  0.00    0.00    2.00 ^ input193/A (CLKBUF_X3)
     3   43.94    0.03    0.05    2.05 ^ input193/Z (CLKBUF_X3)
                                         net193 (net)
                  0.04    0.02    2.07 ^ place6900/A (BUF_X1)
    17   58.07    0.13    0.16    2.23 ^ place6900/Z (BUF_X1)
                                         net6900 (net)
                  0.13    0.02    2.25 ^ place6902/A (BUF_X2)
     7   21.33    0.03    0.05    2.30 ^ place6902/Z (BUF_X2)
                                         net6902 (net)
                  0.03    0.00    2.30 ^ place6903/A (BUF_X2)
    14   58.91    0.07    0.09    2.39 ^ place6903/Z (BUF_X2)
...
                                         clknet_6_63_0_clk (net)
                  0.03    0.00    5.35 ^ clkbuf_leaf_415_clk/A (CLKBUF_X3)
     4    7.12    0.01    0.04    5.40 ^ clkbuf_leaf_415_clk/Z (CLKBUF_X3)
                                         clknet_leaf_415_clk (net)
                  0.01    0.00    5.40 ^ accum[25][31]$_DFFE_PN0P_/CK (DFFR_X1)
                          0.00    5.40   clock reconvergence pessimism
                         -0.04    5.36   library setup time
                                  5.36   data required time
-----------------------------------------------------------------------------
                                  5.36   data required time
                                 -4.33   data arrival time
-----------------------------------------------------------------------------
                                  1.03   slack (MET)



```

### Path 3

- source: `/orfs/flow/reports/nangate45/dense_gemm_tile_stream_int8_16x8/dense_gemm_tile_stream_int8_v1/6_finish.rpt`
- stage: `finish`
- startpoint: `rst_n (input port clocked by clk)`
- endpoint: `accum[38][28]$_DFFE_PN0P_`
- path_group: `asynchronous`
- path_type: `min`
- slack: `1.5100`
- data_arrival_time: `2.2000`
- data_required_time: `0.6900`

```text
Startpoint: rst_n (input port clocked by clk)
Endpoint: accum[38][28]$_DFFE_PN0P_
          (removal check against rising-edge clock clk)
Path Group: asynchronous
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (propagated)
                          2.00    2.00 ^ input external delay
     1   29.53    0.00    0.00    2.00 ^ rst_n (in)
                                         rst_n (net)
                  0.01    0.01    2.01 ^ wire1662/A (CLKBUF_X3)
     2   39.28    0.02    0.04    2.05 ^ wire1662/Z (CLKBUF_X3)
                                         net1662 (net)
                  0.05    0.03    2.08 ^ place6532/A (BUF_X1)
     4   39.37    0.09    0.11    2.20 ^ place6532/Z (BUF_X1)
                                         net6532 (net)
                  0.09    0.00    2.20 ^ accum[38][28]$_DFFE_PN0P_/RN (DFFR_X1)
                                  2.20   data arrival time

                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
...
                                         clknet_3_7_0_clk (net)
                  0.04    0.00    0.29 ^ clkbuf_6_63_0_clk/A (CLKBUF_X3)
    11   36.60    0.03    0.07    0.35 ^ clkbuf_6_63_0_clk/Z (CLKBUF_X3)
                                         clknet_6_63_0_clk (net)
                  0.03    0.00    0.35 ^ clkbuf_leaf_402_clk/A (CLKBUF_X3)
     7   10.72    0.01    0.04    0.40 ^ clkbuf_leaf_402_clk/Z (CLKBUF_X3)
                                         clknet_leaf_402_clk (net)
                  0.01    0.00    0.40 ^ accum[38][28]$_DFFE_PN0P_/CK (DFFR_X1)
                          0.00    0.40   clock reconvergence pessimism
                          0.29    0.69   library removal time
                                  0.69   data required time
-----------------------------------------------------------------------------
                                  0.69   data required time
                                 -2.20   data arrival time
-----------------------------------------------------------------------------
                                  1.51   slack (MET)
```

### Path 4

- source: `/orfs/flow/reports/nangate45/dense_gemm_tile_stream_int8_16x8/dense_gemm_tile_stream_int8_v1/6_finish.rpt`
- stage: `finish`
- startpoint: `rst_n (input port clocked by clk)`
- endpoint: `accum[92][25]$_DFFE_PN0P_`
- path_group: `asynchronous`
- path_type: `max`
- slack: `2.5400`
- data_arrival_time: `2.9000`
- data_required_time: `5.4400`

```text
Startpoint: rst_n (input port clocked by clk)
Endpoint: accum[92][25]$_DFFE_PN0P_
          (recovery check against rising-edge clock clk)
Path Group: asynchronous
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (propagated)
                          2.00    2.00 ^ input external delay
     1   29.53    0.00    0.00    2.00 ^ rst_n (in)
                                         rst_n (net)
                  0.01    0.01    2.01 ^ wire1662/A (CLKBUF_X3)
     2   39.28    0.02    0.04    2.05 ^ wire1662/Z (CLKBUF_X3)
                                         net1662 (net)
                  0.05    0.03    2.08 ^ place6578/A (BUF_X2)
     7   46.55    0.05    0.07    2.16 ^ place6578/Z (BUF_X2)
                                         net6578 (net)
                  0.05    0.01    2.17 ^ place6608/A (BUF_X1)
    11   65.28    0.15    0.18    2.35 ^ place6608/Z (BUF_X1)
                                         net6608 (net)
                  0.15    0.00    2.35 ^ place6627/A (BUF_X1)
     4   25.72    0.06    0.09    2.44 ^ place6627/Z (BUF_X1)
...
                                         clknet_3_2_0_clk (net)
                  0.03    0.00    5.28 ^ clkbuf_6_22_0_clk/A (CLKBUF_X3)
    10   40.06    0.03    0.07    5.35 ^ clkbuf_6_22_0_clk/Z (CLKBUF_X3)
                                         clknet_6_22_0_clk (net)
                  0.03    0.00    5.36 ^ clkbuf_leaf_548_clk/A (CLKBUF_X3)
     7    9.95    0.01    0.04    5.40 ^ clkbuf_leaf_548_clk/Z (CLKBUF_X3)
                                         clknet_leaf_548_clk (net)
                  0.01    0.00    5.40 ^ accum[92][25]$_DFFE_PN0P_/CK (DFFR_X1)
                          0.00    5.40   clock reconvergence pessimism
                          0.04    5.44   library recovery time
                                  5.44   data required time
-----------------------------------------------------------------------------
                                  5.44   data required time
                                 -2.90   data arrival time
-----------------------------------------------------------------------------
                                  2.54   slack (MET)
```

### Path 5

- source: `/orfs/flow/reports/nangate45/dense_gemm_tile_stream_int8_16x8/dense_gemm_tile_stream_int8_v1/6_finish.rpt`
- stage: `finish`
- startpoint: `state[0]$_DFF_PN1_ (rising edge-triggered flip-flop clocked by clk)`
- endpoint: `accum[32][3]$_DFFE_PN0P_`
- path_group: `clk`
- path_type: `max`
- slack: `3.6000`
- data_arrival_time: `1.7400`
- data_required_time: `5.3400`

```text
Startpoint: state[0]$_DFF_PN1_ (rising edge-triggered flip-flop clocked by clk)
Endpoint: accum[32][3]$_DFFE_PN0P_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

  Delay    Time   Description
---------------------------------------------------------
   0.00    0.00   clock clk (rise edge)
   0.00    0.00   clock source latency
   0.00    0.00 ^ clk (in)
   0.02    0.02 ^ wire7609/Z (BUF_X8)
   0.05    0.07 ^ wire7608/Z (BUF_X16)
   0.08    0.16 ^ clkbuf_0_clk/Z (CLKBUF_X3)
   0.06    0.21 ^ clkbuf_2_3_0_clk/Z (CLKBUF_X3)
   0.07    0.28 ^ clkbuf_3_6_0_clk/Z (CLKBUF_X3)
   0.07    0.35 ^ clkbuf_6_53_0_clk/Z (CLKBUF_X3)
   0.05    0.40 ^ clkbuf_leaf_429_clk/Z (CLKBUF_X3)
   0.00    0.40 ^ state[0]$_DFF_PN1_/CK (DFFS_X2)
   0.15    0.55 ^ state[0]$_DFF_PN1_/Q (DFFS_X2)
   0.08    0.63 ^ place6086/Z (BUF_X2)
   0.13    0.75 ^ _102264_/ZN (AND2_X2)
   0.13    0.88 ^ place5936/Z (BUF_X2)
   0.14    1.03 ^ place5968/Z (BUF_X2)
...
   0.06    5.21 ^ clkbuf_2_2_0_clk/Z (CLKBUF_X3)
   0.07    5.29 ^ clkbuf_3_5_0_clk/Z (CLKBUF_X3)
   0.06    5.35 ^ clkbuf_6_42_0_clk/Z (CLKBUF_X3)
   0.04    5.39 ^ clkbuf_leaf_221_clk/Z (CLKBUF_X3)
   0.00    5.39 ^ accum[32][3]$_DFFE_PN0P_/CK (DFFR_X1)
   0.00    5.39   clock reconvergence pessimism
  -0.04    5.34   library setup time
           5.34   data required time
---------------------------------------------------------
           5.34   data required time
          -1.74   data arrival time
---------------------------------------------------------
           3.60   slack (MET)



```


## Worst Timing Paths Across All Stages

### Path 1

- source: `/orfs/flow/reports/nangate45/dense_gemm_tile_stream_int8_16x8/dense_gemm_tile_stream_int8_v1/2_floorplan_final.rpt`
- stage: `floorplan`
- startpoint: `accum[125][29]$_DFFE_PN0P_`
- endpoint: `accum[125][29]$_DFFE_PN0P_`
- path_group: `clk`
- path_type: `min`
- slack: `0.1100`
- data_arrival_time: `0.1100`
- data_required_time: `0.0000`

```text
Startpoint: accum[125][29]$_DFFE_PN0P_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: accum[125][29]$_DFFE_PN0P_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                  0.00    0.00    0.00 ^ accum[125][29]$_DFFE_PN0P_/CK (DFFR_X1)
     2    4.61    0.01    0.09    0.09 v accum[125][29]$_DFFE_PN0P_/Q (DFFR_X1)
                                         accum[125][29] (net)
                  0.01    0.00    0.09 v _135158_/A (INV_X1)
     1    1.67    0.01    0.01    0.10 ^ _135158_/ZN (INV_X1)
                                         _068869_ (net)
                  0.01    0.00    0.10 ^ _135166_/A1 (OAI22_X1)
     1    1.05    0.00    0.01    0.11 v _135166_/ZN (OAI22_X1)
                                         _038179_ (net)
                  0.00    0.00    0.11 v accum[125][29]$_DFFE_PN0P_/D (DFFR_X1)
                                  0.11   data arrival time

                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                          0.00    0.00   clock reconvergence pessimism
                                  0.00 ^ accum[125][29]$_DFFE_PN0P_/CK (DFFR_X1)
                          0.00    0.00   library hold time
                                  0.00   data required time
-----------------------------------------------------------------------------
                                  0.00   data required time
                                 -0.11   data arrival time
-----------------------------------------------------------------------------
                                  0.11   slack (MET)



```

### Path 2

- source: `/orfs/flow/reports/nangate45/dense_gemm_tile_stream_int8_16x8/dense_gemm_tile_stream_int8_v1/3_detailed_place.rpt`
- stage: `detailed_place`
- startpoint: `accum[126][29]$_DFFE_PN0P_`
- endpoint: `accum[126][29]$_DFFE_PN0P_`
- path_group: `clk`
- path_type: `min`
- slack: `0.1100`
- data_arrival_time: `0.1100`
- data_required_time: `0.0000`

```text
Startpoint: accum[126][29]$_DFFE_PN0P_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: accum[126][29]$_DFFE_PN0P_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                  0.00    0.00    0.00 ^ accum[126][29]$_DFFE_PN0P_/CK (DFFR_X1)
     2    5.08    0.01    0.09    0.09 v accum[126][29]$_DFFE_PN0P_/Q (DFFR_X1)
                                         accum[126][29] (net)
                  0.01    0.00    0.09 v _135467_/A (INV_X1)
     1    1.72    0.01    0.01    0.10 ^ _135467_/ZN (INV_X1)
                                         _069146_ (net)
                  0.01    0.00    0.10 ^ _135474_/A1 (OAI22_X1)
     1    1.39    0.01    0.01    0.11 v _135474_/ZN (OAI22_X1)
                                         _038211_ (net)
                  0.01    0.00    0.11 v accum[126][29]$_DFFE_PN0P_/D (DFFR_X1)
                                  0.11   data arrival time

                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                          0.00    0.00   clock reconvergence pessimism
                                  0.00 ^ accum[126][29]$_DFFE_PN0P_/CK (DFFR_X1)
                          0.00    0.00   library hold time
                                  0.00   data required time
-----------------------------------------------------------------------------
                                  0.00   data required time
                                 -0.11   data arrival time
-----------------------------------------------------------------------------
                                  0.11   slack (MET)



```

### Path 3

- source: `/orfs/flow/reports/nangate45/dense_gemm_tile_stream_int8_16x8/dense_gemm_tile_stream_int8_v1/3_global_place.rpt`
- stage: `global_place`
- startpoint: `accum[126][29]$_DFFE_PN0P_`
- endpoint: `accum[126][29]$_DFFE_PN0P_`
- path_group: `clk`
- path_type: `min`
- slack: `0.1100`
- data_arrival_time: `0.1100`
- data_required_time: `0.0000`

```text
Startpoint: accum[126][29]$_DFFE_PN0P_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: accum[126][29]$_DFFE_PN0P_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                  0.00    0.00    0.00 ^ accum[126][29]$_DFFE_PN0P_/CK (DFFR_X1)
     2    4.80    0.01    0.09    0.09 v accum[126][29]$_DFFE_PN0P_/Q (DFFR_X1)
                                         accum[126][29] (net)
                  0.01    0.00    0.09 v _135467_/A (INV_X1)
     1    1.76    0.01    0.01    0.10 ^ _135467_/ZN (INV_X1)
                                         _069146_ (net)
                  0.01    0.00    0.10 ^ _135474_/A1 (OAI22_X1)
     1    1.20    0.01    0.01    0.11 v _135474_/ZN (OAI22_X1)
                                         _038211_ (net)
                  0.01    0.00    0.11 v accum[126][29]$_DFFE_PN0P_/D (DFFR_X1)
                                  0.11   data arrival time

                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                          0.00    0.00   clock reconvergence pessimism
                                  0.00 ^ accum[126][29]$_DFFE_PN0P_/CK (DFFR_X1)
                          0.00    0.00   library hold time
                                  0.00   data required time
-----------------------------------------------------------------------------
                                  0.00   data required time
                                 -0.11   data arrival time
-----------------------------------------------------------------------------
                                  0.11   slack (MET)



```

### Path 4

- source: `/orfs/flow/reports/nangate45/dense_gemm_tile_stream_int8_16x8/dense_gemm_tile_stream_int8_v1/3_resizer.rpt`
- stage: `resizer`
- startpoint: `accum[126][29]$_DFFE_PN0P_`
- endpoint: `accum[126][29]$_DFFE_PN0P_`
- path_group: `clk`
- path_type: `min`
- slack: `0.1100`
- data_arrival_time: `0.1100`
- data_required_time: `0.0000`

```text
Startpoint: accum[126][29]$_DFFE_PN0P_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: accum[126][29]$_DFFE_PN0P_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                  0.00    0.00    0.00 ^ accum[126][29]$_DFFE_PN0P_/CK (DFFR_X1)
     2    4.80    0.01    0.09    0.09 v accum[126][29]$_DFFE_PN0P_/Q (DFFR_X1)
                                         accum[126][29] (net)
                  0.01    0.00    0.09 v _135467_/A (INV_X1)
     1    1.76    0.01    0.01    0.10 ^ _135467_/ZN (INV_X1)
                                         _069146_ (net)
                  0.01    0.00    0.10 ^ _135474_/A1 (OAI22_X1)
     1    1.20    0.01    0.01    0.11 v _135474_/ZN (OAI22_X1)
                                         _038211_ (net)
                  0.01    0.00    0.11 v accum[126][29]$_DFFE_PN0P_/D (DFFR_X1)
                                  0.11   data arrival time

                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                          0.00    0.00   clock reconvergence pessimism
                                  0.00 ^ accum[126][29]$_DFFE_PN0P_/CK (DFFR_X1)
                          0.00    0.00   library hold time
                                  0.00   data required time
-----------------------------------------------------------------------------
                                  0.00   data required time
                                 -0.11   data arrival time
-----------------------------------------------------------------------------
                                  0.11   slack (MET)



```

### Path 5

- source: `/orfs/flow/reports/nangate45/dense_gemm_tile_stream_int8_16x8/dense_gemm_tile_stream_int8_v1/4_cts_final.rpt`
- stage: `cts`
- startpoint: `accum[126][29]$_DFFE_PN0P_`
- endpoint: `accum[126][29]$_DFFE_PN0P_`
- path_group: `clk`
- path_type: `min`
- slack: `0.1100`
- data_arrival_time: `0.5300`
- data_required_time: `0.4200`

```text
Startpoint: accum[126][29]$_DFFE_PN0P_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: accum[126][29]$_DFFE_PN0P_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   14.74    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.00    0.00    0.00 ^ wire7609/A (BUF_X8)
     1   70.57    0.02    0.03    0.03 ^ wire7609/Z (BUF_X8)
                                         net7609 (net)
                  0.04    0.03    0.06 ^ wire7608/A (BUF_X16)
     1   61.71    0.01    0.03    0.09 ^ wire7608/Z (BUF_X16)
                                         net7608 (net)
                  0.03    0.02    0.11 ^ clkbuf_0_clk/A (CLKBUF_X3)
     4   39.20    0.03    0.06    0.17 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.03    0.00    0.17 ^ clkbuf_2_1_0_clk/A (CLKBUF_X3)
     2   24.47    0.02    0.06    0.23 ^ clkbuf_2_1_0_clk/Z (CLKBUF_X3)
...
                                         clknet_6_21_0_clk (net)
                  0.03    0.00    0.37 ^ clkbuf_leaf_507_clk/A (CLKBUF_X3)
     5   11.98    0.01    0.05    0.42 ^ clkbuf_leaf_507_clk/Z (CLKBUF_X3)
                                         clknet_leaf_507_clk (net)
                  0.01    0.00    0.42 ^ accum[126][29]$_DFFE_PN0P_/CK (DFFR_X1)
                          0.00    0.42   clock reconvergence pessimism
                          0.01    0.42   library hold time
                                  0.42   data required time
-----------------------------------------------------------------------------
                                  0.42   data required time
                                 -0.53   data arrival time
-----------------------------------------------------------------------------
                                  0.11   slack (MET)



```

### Path 6

- source: `/orfs/flow/reports/nangate45/dense_gemm_tile_stream_int8_16x8/dense_gemm_tile_stream_int8_v1/6_finish.rpt`
- stage: `finish`
- startpoint: `accum[126][29]$_DFFE_PN0P_`
- endpoint: `accum[126][29]$_DFFE_PN0P_`
- path_group: `clk`
- path_type: `min`
- slack: `0.1100`
- data_arrival_time: `0.5100`
- data_required_time: `0.4000`

```text
Startpoint: accum[126][29]$_DFFE_PN0P_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: accum[126][29]$_DFFE_PN0P_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   12.24    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.00    0.00    0.00 ^ wire7609/A (BUF_X8)
     1   53.80    0.01    0.02    0.02 ^ wire7609/Z (BUF_X8)
                                         net7609 (net)
                  0.03    0.02    0.05 ^ wire7608/A (BUF_X16)
     1   50.20    0.01    0.03    0.07 ^ wire7608/Z (BUF_X16)
                                         net7608 (net)
                  0.03    0.02    0.09 ^ clkbuf_0_clk/A (CLKBUF_X3)
     4   37.97    0.03    0.06    0.16 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.03    0.01    0.16 ^ clkbuf_2_1_0_clk/A (CLKBUF_X3)
     2   22.29    0.02    0.05    0.21 ^ clkbuf_2_1_0_clk/Z (CLKBUF_X3)
...
                                         clknet_6_21_0_clk (net)
                  0.03    0.00    0.35 ^ clkbuf_leaf_507_clk/A (CLKBUF_X3)
     5   11.52    0.01    0.04    0.40 ^ clkbuf_leaf_507_clk/Z (CLKBUF_X3)
                                         clknet_leaf_507_clk (net)
                  0.01    0.00    0.40 ^ accum[126][29]$_DFFE_PN0P_/CK (DFFR_X1)
                          0.00    0.40   clock reconvergence pessimism
                          0.01    0.40   library hold time
                                  0.40   data required time
-----------------------------------------------------------------------------
                                  0.40   data required time
                                 -0.51   data arrival time
-----------------------------------------------------------------------------
                                  0.11   slack (MET)



```

### Path 7

- source: `/orfs/flow/reports/nangate45/dense_gemm_tile_stream_int8_16x8/dense_gemm_tile_stream_int8_v1/5_global_route.rpt`
- stage: `route`
- startpoint: `accum[125][29]$_DFFE_PN0P_`
- endpoint: `accum[125][29]$_DFFE_PN0P_`
- path_group: `clk`
- path_type: `min`
- slack: `0.1200`
- data_arrival_time: `0.5400`
- data_required_time: `0.4200`

```text
Startpoint: accum[125][29]$_DFFE_PN0P_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: accum[125][29]$_DFFE_PN0P_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   14.82    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.00    0.00    0.00 ^ wire7609/A (BUF_X8)
     1   69.91    0.01    0.02    0.03 ^ wire7609/Z (BUF_X8)
                                         net7609 (net)
                  0.04    0.03    0.06 ^ wire7608/A (BUF_X16)
     1   59.19    0.01    0.03    0.08 ^ wire7608/Z (BUF_X16)
                                         net7608 (net)
                  0.03    0.02    0.11 ^ clkbuf_0_clk/A (CLKBUF_X3)
     4   39.98    0.03    0.06    0.17 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.03    0.01    0.18 ^ clkbuf_2_1_0_clk/A (CLKBUF_X3)
     2   24.34    0.02    0.06    0.23 ^ clkbuf_2_1_0_clk/Z (CLKBUF_X3)
...
                                         clknet_6_21_0_clk (net)
                  0.03    0.00    0.37 ^ clkbuf_leaf_510_clk/A (CLKBUF_X3)
     6    8.76    0.01    0.04    0.42 ^ clkbuf_leaf_510_clk/Z (CLKBUF_X3)
                                         clknet_leaf_510_clk (net)
                  0.01    0.00    0.42 ^ accum[125][29]$_DFFE_PN0P_/CK (DFFR_X1)
                          0.00    0.42   clock reconvergence pessimism
                          0.01    0.42   library hold time
                                  0.42   data required time
-----------------------------------------------------------------------------
                                  0.42   data required time
                                 -0.54   data arrival time
-----------------------------------------------------------------------------
                                  0.12   slack (MET)



```

### Path 8

- source: `/orfs/flow/reports/nangate45/dense_gemm_tile_stream_int8_16x8/dense_gemm_tile_stream_int8_v1/3_global_place.rpt`
- stage: `global_place`
- startpoint: `input_b[9] (input port clocked by clk)`
- endpoint: `accum[25][31]$_DFFE_PN0P_`
- path_group: `clk`
- path_type: `max`
- slack: `0.6300`
- data_arrival_time: `4.3300`
- data_required_time: `4.9600`

```text
Startpoint: input_b[9] (input port clocked by clk)
Endpoint: accum[25][31]$_DFFE_PN0P_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                          2.00    2.00 ^ input external delay
     1    7.11    0.00    0.00    2.00 ^ input_b[9] (in)
                                         input_b[9] (net)
                  0.00    0.00    2.00 ^ input193/A (CLKBUF_X3)
     3   45.62    0.03    0.05    2.05 ^ input193/Z (CLKBUF_X3)
                                         net193 (net)
                  0.05    0.04    2.08 ^ place6900/A (BUF_X1)
    17   49.94    0.11    0.14    2.23 ^ place6900/Z (BUF_X1)
                                         net6900 (net)
                  0.11    0.01    2.24 ^ place6902/A (BUF_X2)
     7   18.12    0.02    0.05    2.29 ^ place6902/Z (BUF_X2)
                                         net6902 (net)
                  0.02    0.00    2.29 ^ place6903/A (BUF_X2)
    14   51.70    0.06    0.08    2.37 ^ place6903/Z (BUF_X2)
...
                                  4.33   data arrival time

                  0.00    5.00    5.00   clock clk (rise edge)
                          0.00    5.00   clock network delay (ideal)
                          0.00    5.00   clock reconvergence pessimism
                                  5.00 ^ accum[25][31]$_DFFE_PN0P_/CK (DFFR_X1)
                         -0.04    4.96   library setup time
                                  4.96   data required time
-----------------------------------------------------------------------------
                                  4.96   data required time
                                 -4.33   data arrival time
-----------------------------------------------------------------------------
                                  0.63   slack (MET)



```
