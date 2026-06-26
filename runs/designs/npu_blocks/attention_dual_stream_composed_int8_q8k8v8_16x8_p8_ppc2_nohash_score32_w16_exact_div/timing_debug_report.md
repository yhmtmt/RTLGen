# OpenROAD Timing Debug Summary

- design_dir: `runs/designs/npu_blocks/attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_score32_w16_exact_div`
- metrics_path: `runs/designs/npu_blocks/attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_score32_w16_exact_div/metrics.csv`
- rows_considered: 2

## Metrics Rows

| param_hash | tag | status | critical_path_ns | density | result_path |
| --- | --- | --- | ---: | ---: | --- |
| 9981a16f | attention_dual_stream_composed_v1_hier_score32_w16_exact_div | ok | 36.1740 | 0.3 | `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_score32_w16_exact_div/attention_dual_stream_composed_v1_hier_score32_w16_exact_div/6_finish.rpt` |
| 236f0e07 | attention_dual_stream_composed_v1_hier_score32_w16_exact_div | ok | 36.2495 | 0.4 | `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_score32_w16_exact_div/attention_dual_stream_composed_v1_hier_score32_w16_exact_div/6_finish.rpt` |

## Inspected Report Files

- `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_score32_w16_exact_div/attention_dual_stream_composed_v1_hier_score32_w16_exact_div/6_finish.rpt`
- `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_score32_w16_exact_div/attention_dual_stream_composed_v1_hier_score32_w16_exact_div/5_global_route.rpt`
- `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_score32_w16_exact_div/attention_dual_stream_composed_v1_hier_score32_w16_exact_div/5_route_drc.rpt`
- `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_score32_w16_exact_div/attention_dual_stream_composed_v1_hier_score32_w16_exact_div/4_cts_final.rpt`
- `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_score32_w16_exact_div/attention_dual_stream_composed_v1_hier_score32_w16_exact_div/3_resizer.rpt`
- `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_score32_w16_exact_div/attention_dual_stream_composed_v1_hier_score32_w16_exact_div/3_detailed_place.rpt`
- `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_score32_w16_exact_div/attention_dual_stream_composed_v1_hier_score32_w16_exact_div/3_global_place.rpt`
- `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_score32_w16_exact_div/attention_dual_stream_composed_v1_hier_score32_w16_exact_div/2_floorplan_final.rpt`
- `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_score32_w16_exact_div/attention_dual_stream_composed_v1_hier_score32_w16_exact_div/drt_antennas.log`
- `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_score32_w16_exact_div/attention_dual_stream_composed_v1_hier_score32_w16_exact_div/grt_antennas.log`
- `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_score32_w16_exact_div/attention_dual_stream_composed_v1_hier_score32_w16_exact_div/metadata-generate.log`

## Preferred Final-Stage Timing Paths

- raw_path_block_count: 104
- unique_path_block_count: 28
- preferred_stage: `finish`

### Path 1

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_score32_w16_exact_div/attention_dual_stream_composed_v1_hier_score32_w16_exact_div/6_finish.rpt`
- stage: `finish`
- startpoint: `u_softmax/exp_weight_q[1][33]$_DFF_P_`
- endpoint: `u_softmax/weights[16]$_DFF_P_`
- path_group: `clk`
- path_type: `max`
- slack: `-25.6700`
- data_arrival_time: `36.2500`
- data_required_time: `10.5800`

```text
Startpoint: u_softmax/exp_weight_q[1][33]$_DFF_P_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: u_softmax/weights[16]$_DFF_P_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   41.12    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.01    0.01    0.01 ^ wire137603/A (BUF_X8)
     1   43.44    0.01    0.03    0.04 ^ wire137603/Z (BUF_X8)
                                         net137602 (net)
                  0.02    0.02    0.05 ^ wire137602/A (BUF_X16)
     1   48.73    0.01    0.02    0.08 ^ wire137602/Z (BUF_X16)
                                         net137601 (net)
                  0.02    0.02    0.10 ^ clkbuf_0_clk/A (CLKBUF_X3)
     2   30.81    0.03    0.06    0.15 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.03    0.00    0.16 ^ clkbuf_1_0_0_clk/A (CLKBUF_X3)
     1   19.67    0.02    0.05    0.21 ^ clkbuf_1_0_0_clk/Z (CLKBUF_X3)
...
                                         clknet_6_26__leaf_clk (net)
                  0.04    0.01   10.57 ^ clkbuf_leaf_14_clk/A (CLKBUF_X3)
     3    9.98    0.01    0.05   10.62 ^ clkbuf_leaf_14_clk/Z (CLKBUF_X3)
                                         clknet_leaf_14_clk (net)
                  0.01    0.00   10.62 ^ u_softmax/weights[16]$_DFF_P_/CK (DFF_X2)
                          0.00   10.62   clock reconvergence pessimism
                         -0.04   10.58   library setup time
                                 10.58   data required time
-----------------------------------------------------------------------------
                                 10.58   data required time
                                -36.25   data arrival time
-----------------------------------------------------------------------------
                                -25.67   slack (VIOLATED)



```

### Path 2

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_score32_w16_exact_div/attention_dual_stream_composed_v1_hier_score32_w16_exact_div/6_finish.rpt`
- stage: `finish`
- startpoint: `stream_buf_0_pipe_1[994]$_DFF_PN0_`
- endpoint: `stream_buf_0_pipe_2[994]$_DFF_PN0_`
- path_group: `clk`
- path_type: `min`
- slack: `0.0500`
- data_arrival_time: `0.7300`
- data_required_time: `0.6900`

```text
Startpoint: stream_buf_0_pipe_1[994]$_DFF_PN0_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: stream_buf_0_pipe_2[994]$_DFF_PN0_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   41.12    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.01    0.01    0.01 ^ wire137603/A (BUF_X8)
     1   43.44    0.01    0.03    0.04 ^ wire137603/Z (BUF_X8)
                                         net137602 (net)
                  0.02    0.02    0.05 ^ wire137602/A (BUF_X16)
     1   48.73    0.01    0.02    0.08 ^ wire137602/Z (BUF_X16)
                                         net137601 (net)
                  0.02    0.02    0.10 ^ clkbuf_0_clk/A (CLKBUF_X3)
     2   30.81    0.03    0.06    0.15 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.03    0.00    0.16 ^ clkbuf_1_1_0_clk/A (CLKBUF_X3)
     1   32.03    0.03    0.06    0.21 ^ clkbuf_1_1_0_clk/Z (CLKBUF_X3)
...
                                         clknet_6_57__leaf_clk (net)
                  0.05    0.00    0.63 ^ clkbuf_leaf_287_clk/A (CLKBUF_X3)
     7   10.50    0.01    0.05    0.68 ^ clkbuf_leaf_287_clk/Z (CLKBUF_X3)
                                         clknet_leaf_287_clk (net)
                  0.01    0.00    0.68 ^ stream_buf_0_pipe_2[994]$_DFF_PN0_/CK (DFFR_X1)
                          0.00    0.68   clock reconvergence pessimism
                          0.01    0.69   library hold time
                                  0.69   data required time
-----------------------------------------------------------------------------
                                  0.69   data required time
                                 -0.73   data arrival time
-----------------------------------------------------------------------------
                                  0.05   slack (MET)



```

### Path 3

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_score32_w16_exact_div/attention_dual_stream_composed_v1_hier_score32_w16_exact_div/6_finish.rpt`
- stage: `finish`
- startpoint: `rst_n (input port clocked by clk)`
- endpoint: `stream_buf_1_pipe_0[864]$_DFF_PN0_`
- path_group: `asynchronous`
- path_type: `min`
- slack: `1.4800`
- data_arrival_time: `2.4700`
- data_required_time: `0.9900`

```text
Startpoint: rst_n (input port clocked by clk)
Endpoint: stream_buf_1_pipe_0[864]$_DFF_PN0_
          (removal check against rising-edge clock clk)
Path Group: asynchronous
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (propagated)
                          2.00    2.00 ^ input external delay
     1    5.89    0.00    0.00    2.00 ^ rst_n (in)
                                         rst_n (net)
                  0.00    0.00    2.00 ^ input393/A (CLKBUF_X3)
     1   14.46    0.01    0.03    2.03 ^ input393/Z (CLKBUF_X3)
                                         net392 (net)
                  0.01    0.01    2.04 ^ place137372/A (BUF_X1)
     1   25.45    0.06    0.08    2.11 ^ place137372/Z (BUF_X1)
                                         net137371 (net)
                  0.06    0.02    2.13 ^ place137373/A (BUF_X1)
     1   24.49    0.05    0.08    2.21 ^ place137373/Z (BUF_X1)
                                         net137372 (net)
                  0.06    0.01    2.23 ^ place137374/A (BUF_X1)
     2   37.85    0.08    0.11    2.34 ^ place137374/Z (BUF_X1)
...
                                         clknet_5_26_0_clk (net)
                  0.02    0.00    0.52 ^ clkbuf_6_52__f_clk/A (CLKBUF_X3)
    18   88.12    0.07    0.10    0.62 ^ clkbuf_6_52__f_clk/Z (CLKBUF_X3)
                                         clknet_6_52__leaf_clk (net)
                  0.07    0.00    0.63 ^ clkbuf_leaf_232_clk/A (CLKBUF_X3)
     4   18.02    0.02    0.06    0.69 ^ clkbuf_leaf_232_clk/Z (CLKBUF_X3)
                                         clknet_leaf_232_clk (net)
                  0.02    0.00    0.69 ^ stream_buf_1_pipe_0[864]$_DFF_PN0_/CK (DFFR_X1)
                          0.00    0.69   clock reconvergence pessimism
                          0.31    0.99   library removal time
                                  0.99   data required time
-----------------------------------------------------------------------------
                                  0.99   data required time
                                 -2.47   data arrival time
-----------------------------------------------------------------------------
                                  1.48   slack (MET)
```

### Path 4

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_score32_w16_exact_div/attention_dual_stream_composed_v1_hier_score32_w16_exact_div/6_finish.rpt`
- stage: `finish`
- startpoint: `rst_n (input port clocked by clk)`
- endpoint: `value_accum_1_out[1]$_DFFE_PN0P_`
- path_group: `asynchronous`
- path_type: `max`
- slack: `7.3600`
- data_arrival_time: `3.2700`
- data_required_time: `10.6400`

```text
Startpoint: rst_n (input port clocked by clk)
Endpoint: value_accum_1_out[1]$_DFFE_PN0P_
          (recovery check against rising-edge clock clk)
Path Group: asynchronous
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (propagated)
                          2.00    2.00 ^ input external delay
     1    5.89    0.00    0.00    2.00 ^ rst_n (in)
                                         rst_n (net)
                  0.00    0.00    2.00 ^ input393/A (CLKBUF_X3)
     1   14.46    0.01    0.03    2.03 ^ input393/Z (CLKBUF_X3)
                                         net392 (net)
                  0.01    0.01    2.04 ^ place137372/A (BUF_X1)
     1   25.45    0.06    0.08    2.11 ^ place137372/Z (BUF_X1)
                                         net137371 (net)
                  0.06    0.02    2.13 ^ place137373/A (BUF_X1)
     1   24.49    0.05    0.08    2.21 ^ place137373/Z (BUF_X1)
                                         net137372 (net)
                  0.06    0.01    2.23 ^ place137374/A (BUF_X1)
     2   37.85    0.08    0.11    2.34 ^ place137374/Z (BUF_X1)
...
                                         clknet_5_16_0_clk (net)
                  0.02    0.00   10.50 ^ clkbuf_6_33__f_clk/A (CLKBUF_X3)
     6   23.67    0.02    0.05   10.55 ^ clkbuf_6_33__f_clk/Z (CLKBUF_X3)
                                         clknet_6_33__leaf_clk (net)
                  0.02    0.00   10.55 ^ clkbuf_leaf_485_clk/A (CLKBUF_X3)
     6    9.20    0.01    0.04   10.59 ^ clkbuf_leaf_485_clk/Z (CLKBUF_X3)
                                         clknet_leaf_485_clk (net)
                  0.01    0.00   10.59 ^ value_accum_1_out[1]$_DFFE_PN0P_/CK (DFFR_X1)
                          0.00   10.59   clock reconvergence pessimism
                          0.05   10.64   library recovery time
                                 10.64   data required time
-----------------------------------------------------------------------------
                                 10.64   data required time
                                 -3.27   data arrival time
-----------------------------------------------------------------------------
                                  7.36   slack (MET)
```


## Worst Timing Paths Across All Stages

### Path 1

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_score32_w16_exact_div/attention_dual_stream_composed_v1_hier_score32_w16_exact_div/2_floorplan_final.rpt`
- stage: `floorplan`
- startpoint: `u_softmax/sum_weight_q[8]$_DFF_P_`
- endpoint: `u_softmax/weights[96]$_DFF_P_`
- path_group: `clk`
- path_type: `max`
- slack: `-35.7400`
- data_arrival_time: `45.7000`
- data_required_time: `9.9600`

```text
Startpoint: u_softmax/sum_weight_q[8]$_DFF_P_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: u_softmax/weights[96]$_DFF_P_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                  0.00    0.00    0.00 ^ u_softmax/sum_weight_q[8]$_DFF_P_/CK (DFF_X2)
   392 1251.41    1.42    1.58    1.58 ^ u_softmax/sum_weight_q[8]$_DFF_P_/QN (DFF_X2)
                                         u_softmax/_129447_ (net)
                  1.42    0.00    1.58 ^ u_softmax/_234449_/B (FA_X1)
     1    1.70    0.04    0.22    1.80 ^ u_softmax/_234449_/S (FA_X1)
                                         u_softmax/_001098_ (net)
                  0.04    0.00    1.80 ^ u_softmax/_201210_/A (INV_X1)
     1    3.40    0.01    0.02    1.82 v u_softmax/_201210_/ZN (INV_X1)
                                         u_softmax/_001106_ (net)
                  0.01    0.00    1.82 v u_softmax/_234454_/B (FA_X1)
     1    1.70    0.01    0.12    1.94 ^ u_softmax/_234454_/S (FA_X1)
                                         u_softmax/_001108_ (net)
                  0.01    0.00    1.94 ^ u_softmax/_199625_/A (INV_X1)
...
                                 45.70   data arrival time

                  0.00   10.00   10.00   clock clk (rise edge)
                          0.00   10.00   clock network delay (ideal)
                          0.00   10.00   clock reconvergence pessimism
                                 10.00 ^ u_softmax/weights[96]$_DFF_P_/CK (DFF_X1)
                         -0.04    9.96   library setup time
                                  9.96   data required time
-----------------------------------------------------------------------------
                                  9.96   data required time
                                -45.70   data arrival time
-----------------------------------------------------------------------------
                                -35.74   slack (VIOLATED)



```

### Path 2

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_score32_w16_exact_div/attention_dual_stream_composed_v1_hier_score32_w16_exact_div/3_global_place.rpt`
- stage: `global_place`
- startpoint: `u_softmax/sum_weight_q[39]$_DFF_P_`
- endpoint: `u_softmax/weights[96]$_DFF_P_`
- path_group: `clk`
- path_type: `max`
- slack: `-27.5100`
- data_arrival_time: `37.4700`
- data_required_time: `9.9500`

```text
Startpoint: u_softmax/sum_weight_q[39]$_DFF_P_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: u_softmax/weights[96]$_DFF_P_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                  0.00    0.00    0.00 ^ u_softmax/sum_weight_q[39]$_DFF_P_/CK (DFF_X2)
     2   15.15    0.02    0.09    0.09 ^ u_softmax/sum_weight_q[39]$_DFF_P_/QN (DFF_X2)
                                         u_softmax/_000783_ (net)
                  0.02    0.00    0.09 ^ place131119/A (BUF_X1)
     3   26.87    0.06    0.08    0.17 ^ place131119/Z (BUF_X1)
                                         net131118 (net)
                  0.06    0.00    0.18 ^ place131120/A (BUF_X1)
     4   41.49    0.09    0.12    0.30 ^ place131120/Z (BUF_X1)
                                         net131119 (net)
                  0.09    0.01    0.31 ^ place131134/A (BUF_X2)
     2   12.84    0.02    0.04    0.35 ^ place131134/Z (BUF_X2)
                                         net131133 (net)
                  0.02    0.00    0.35 ^ place131135/A (BUF_X1)
...
                                 37.47   data arrival time

                  0.00   10.00   10.00   clock clk (rise edge)
                          0.00   10.00   clock network delay (ideal)
                          0.00   10.00   clock reconvergence pessimism
                                 10.00 ^ u_softmax/weights[96]$_DFF_P_/CK (DFF_X2)
                         -0.05    9.95   library setup time
                                  9.95   data required time
-----------------------------------------------------------------------------
                                  9.95   data required time
                                -37.47   data arrival time
-----------------------------------------------------------------------------
                                -27.51   slack (VIOLATED)



```

### Path 3

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_score32_w16_exact_div/attention_dual_stream_composed_v1_hier_score32_w16_exact_div/3_resizer.rpt`
- stage: `resizer`
- startpoint: `u_softmax/sum_weight_q[39]$_DFF_P_`
- endpoint: `u_softmax/weights[96]$_DFF_P_`
- path_group: `clk`
- path_type: `max`
- slack: `-27.5100`
- data_arrival_time: `37.4700`
- data_required_time: `9.9500`

```text
Startpoint: u_softmax/sum_weight_q[39]$_DFF_P_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: u_softmax/weights[96]$_DFF_P_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                  0.00    0.00    0.00 ^ u_softmax/sum_weight_q[39]$_DFF_P_/CK (DFF_X2)
     2   15.15    0.02    0.09    0.09 ^ u_softmax/sum_weight_q[39]$_DFF_P_/QN (DFF_X2)
                                         u_softmax/_000783_ (net)
                  0.02    0.00    0.09 ^ place131119/A (BUF_X1)
     3   26.87    0.06    0.08    0.17 ^ place131119/Z (BUF_X1)
                                         net131118 (net)
                  0.06    0.00    0.18 ^ place131120/A (BUF_X1)
     4   41.49    0.09    0.12    0.30 ^ place131120/Z (BUF_X1)
                                         net131119 (net)
                  0.09    0.01    0.31 ^ place131134/A (BUF_X2)
     2   12.84    0.02    0.04    0.35 ^ place131134/Z (BUF_X2)
                                         net131133 (net)
                  0.02    0.00    0.35 ^ place131135/A (BUF_X1)
...
                                 37.47   data arrival time

                  0.00   10.00   10.00   clock clk (rise edge)
                          0.00   10.00   clock network delay (ideal)
                          0.00   10.00   clock reconvergence pessimism
                                 10.00 ^ u_softmax/weights[96]$_DFF_P_/CK (DFF_X2)
                         -0.05    9.95   library setup time
                                  9.95   data required time
-----------------------------------------------------------------------------
                                  9.95   data required time
                                -37.47   data arrival time
-----------------------------------------------------------------------------
                                -27.51   slack (VIOLATED)



```

### Path 4

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_score32_w16_exact_div/attention_dual_stream_composed_v1_hier_score32_w16_exact_div/3_detailed_place.rpt`
- stage: `detailed_place`
- startpoint: `u_softmax/sum_weight_q[30]$_DFF_P_`
- endpoint: `u_softmax/weights[64]$_DFF_P_`
- path_group: `clk`
- path_type: `max`
- slack: `-27.0800`
- data_arrival_time: `37.0200`
- data_required_time: `9.9500`

```text
Startpoint: u_softmax/sum_weight_q[30]$_DFF_P_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: u_softmax/weights[64]$_DFF_P_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                  0.00    0.00    0.00 ^ u_softmax/sum_weight_q[30]$_DFF_P_/CK (DFF_X2)
     2    4.84    0.01    0.08    0.08 ^ u_softmax/sum_weight_q[30]$_DFF_P_/QN (DFF_X2)
                                         u_softmax/_129519_ (net)
                  0.01    0.00    0.08 ^ place131387/A (BUF_X1)
     3   33.44    0.07    0.09    0.17 ^ place131387/Z (BUF_X1)
                                         net131386 (net)
                  0.07    0.00    0.17 ^ place131388/A (BUF_X2)
     2   25.83    0.03    0.05    0.22 ^ place131388/Z (BUF_X2)
                                         net131387 (net)
                  0.03    0.01    0.23 ^ place131389/A (BUF_X1)
     3   28.07    0.06    0.09    0.32 ^ place131389/Z (BUF_X1)
                                         net131388 (net)
                  0.06    0.00    0.32 ^ place131390/A (BUF_X2)
...
                                 37.02   data arrival time

                  0.00   10.00   10.00   clock clk (rise edge)
                          0.00   10.00   clock network delay (ideal)
                          0.00   10.00   clock reconvergence pessimism
                                 10.00 ^ u_softmax/weights[64]$_DFF_P_/CK (DFF_X2)
                         -0.05    9.95   library setup time
                                  9.95   data required time
-----------------------------------------------------------------------------
                                  9.95   data required time
                                -37.02   data arrival time
-----------------------------------------------------------------------------
                                -27.08   slack (VIOLATED)



```

### Path 5

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_score32_w16_exact_div/attention_dual_stream_composed_v1_hier_score32_w16_exact_div/5_global_route.rpt`
- stage: `route`
- startpoint: `u_softmax/sum_weight_q[16]$_DFF_P_`
- endpoint: `u_softmax/weights[0]$_DFF_P_`
- path_group: `clk`
- path_type: `max`
- slack: `-25.8100`
- data_arrival_time: `36.4100`
- data_required_time: `10.5900`

```text
Startpoint: u_softmax/sum_weight_q[16]$_DFF_P_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: u_softmax/weights[0]$_DFF_P_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   55.22    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.02    0.01    0.01 ^ wire137603/A (BUF_X8)
     1   56.47    0.01    0.03    0.04 ^ wire137603/Z (BUF_X8)
                                         net137602 (net)
                  0.03    0.02    0.06 ^ wire137602/A (BUF_X16)
     1   67.03    0.01    0.03    0.09 ^ wire137602/Z (BUF_X16)
                                         net137601 (net)
                  0.03    0.03    0.12 ^ clkbuf_0_clk/A (CLKBUF_X3)
     2   43.19    0.03    0.07    0.19 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.03    0.00    0.19 ^ clkbuf_1_0_0_clk/A (CLKBUF_X3)
     1   27.42    0.02    0.06    0.25 ^ clkbuf_1_0_0_clk/Z (CLKBUF_X3)
...
                                         clknet_5_13_0_clk (net)
                  0.02    0.00   10.56 ^ clkbuf_6_27__f_clk/A (CLKBUF_X3)
     5   34.26    0.02    0.05   10.62 ^ clkbuf_6_27__f_clk/Z (CLKBUF_X3)
                                         clknet_6_27__leaf_clk (net)
                  0.03    0.01   10.63 ^ u_softmax/weights[0]$_DFF_P_/CK (DFF_X2)
                          0.00   10.63   clock reconvergence pessimism
                         -0.04   10.59   library setup time
                                 10.59   data required time
-----------------------------------------------------------------------------
                                 10.59   data required time
                                -36.41   data arrival time
-----------------------------------------------------------------------------
                                -25.81   slack (VIOLATED)



```

### Path 6

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_score32_w16_exact_div/attention_dual_stream_composed_v1_hier_score32_w16_exact_div/6_finish.rpt`
- stage: `finish`
- startpoint: `u_softmax/exp_weight_q[1][33]$_DFF_P_`
- endpoint: `u_softmax/weights[16]$_DFF_P_`
- path_group: `clk`
- path_type: `max`
- slack: `-25.6700`
- data_arrival_time: `36.2500`
- data_required_time: `10.5800`

```text
Startpoint: u_softmax/exp_weight_q[1][33]$_DFF_P_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: u_softmax/weights[16]$_DFF_P_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   41.12    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.01    0.01    0.01 ^ wire137603/A (BUF_X8)
     1   43.44    0.01    0.03    0.04 ^ wire137603/Z (BUF_X8)
                                         net137602 (net)
                  0.02    0.02    0.05 ^ wire137602/A (BUF_X16)
     1   48.73    0.01    0.02    0.08 ^ wire137602/Z (BUF_X16)
                                         net137601 (net)
                  0.02    0.02    0.10 ^ clkbuf_0_clk/A (CLKBUF_X3)
     2   30.81    0.03    0.06    0.15 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.03    0.00    0.16 ^ clkbuf_1_0_0_clk/A (CLKBUF_X3)
     1   19.67    0.02    0.05    0.21 ^ clkbuf_1_0_0_clk/Z (CLKBUF_X3)
...
                                         clknet_6_26__leaf_clk (net)
                  0.04    0.01   10.57 ^ clkbuf_leaf_14_clk/A (CLKBUF_X3)
     3    9.98    0.01    0.05   10.62 ^ clkbuf_leaf_14_clk/Z (CLKBUF_X3)
                                         clknet_leaf_14_clk (net)
                  0.01    0.00   10.62 ^ u_softmax/weights[16]$_DFF_P_/CK (DFF_X2)
                          0.00   10.62   clock reconvergence pessimism
                         -0.04   10.58   library setup time
                                 10.58   data required time
-----------------------------------------------------------------------------
                                 10.58   data required time
                                -36.25   data arrival time
-----------------------------------------------------------------------------
                                -25.67   slack (VIOLATED)



```

### Path 7

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_score32_w16_exact_div/attention_dual_stream_composed_v1_hier_score32_w16_exact_div/4_cts_final.rpt`
- stage: `cts`
- startpoint: `u_softmax/sum_weight_q[27]$_DFF_P_`
- endpoint: `u_softmax/weights[64]$_DFF_P_`
- path_group: `clk`
- path_type: `max`
- slack: `-25.5100`
- data_arrival_time: `36.1500`
- data_required_time: `10.6300`

```text
Startpoint: u_softmax/sum_weight_q[27]$_DFF_P_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: u_softmax/weights[64]$_DFF_P_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   55.74    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.02    0.01    0.01 ^ wire137603/A (BUF_X8)
     1   56.48    0.01    0.03    0.05 ^ wire137603/Z (BUF_X8)
                                         net137602 (net)
                  0.03    0.02    0.06 ^ wire137602/A (BUF_X16)
     1   67.30    0.01    0.03    0.09 ^ wire137602/Z (BUF_X16)
                                         net137601 (net)
                  0.03    0.02    0.12 ^ clkbuf_0_clk/A (CLKBUF_X3)
     2   42.51    0.03    0.07    0.19 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.03    0.00    0.19 ^ clkbuf_1_0_0_clk/A (CLKBUF_X3)
     1   27.45    0.02    0.06    0.25 ^ clkbuf_1_0_0_clk/Z (CLKBUF_X3)
...
                                         clknet_6_1__leaf_clk (net)
                  0.03    0.00   10.63 ^ clkbuf_leaf_516_clk/A (CLKBUF_X3)
     5   11.49    0.01    0.05   10.68 ^ clkbuf_leaf_516_clk/Z (CLKBUF_X3)
                                         clknet_leaf_516_clk (net)
                  0.01    0.00   10.68 ^ u_softmax/weights[64]$_DFF_P_/CK (DFF_X2)
                          0.00   10.68   clock reconvergence pessimism
                         -0.04   10.63   library setup time
                                 10.63   data required time
-----------------------------------------------------------------------------
                                 10.63   data required time
                                -36.15   data arrival time
-----------------------------------------------------------------------------
                                -25.51   slack (VIOLATED)



```

### Path 8

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_score32_w16_exact_div/attention_dual_stream_composed_v1_hier_score32_w16_exact_div/6_finish.rpt`
- stage: `finish`
- startpoint: `stream_buf_0_pipe_1[994]$_DFF_PN0_`
- endpoint: `stream_buf_0_pipe_2[994]$_DFF_PN0_`
- path_group: `clk`
- path_type: `min`
- slack: `0.0500`
- data_arrival_time: `0.7300`
- data_required_time: `0.6900`

```text
Startpoint: stream_buf_0_pipe_1[994]$_DFF_PN0_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: stream_buf_0_pipe_2[994]$_DFF_PN0_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   41.12    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.01    0.01    0.01 ^ wire137603/A (BUF_X8)
     1   43.44    0.01    0.03    0.04 ^ wire137603/Z (BUF_X8)
                                         net137602 (net)
                  0.02    0.02    0.05 ^ wire137602/A (BUF_X16)
     1   48.73    0.01    0.02    0.08 ^ wire137602/Z (BUF_X16)
                                         net137601 (net)
                  0.02    0.02    0.10 ^ clkbuf_0_clk/A (CLKBUF_X3)
     2   30.81    0.03    0.06    0.15 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.03    0.00    0.16 ^ clkbuf_1_1_0_clk/A (CLKBUF_X3)
     1   32.03    0.03    0.06    0.21 ^ clkbuf_1_1_0_clk/Z (CLKBUF_X3)
...
                                         clknet_6_57__leaf_clk (net)
                  0.05    0.00    0.63 ^ clkbuf_leaf_287_clk/A (CLKBUF_X3)
     7   10.50    0.01    0.05    0.68 ^ clkbuf_leaf_287_clk/Z (CLKBUF_X3)
                                         clknet_leaf_287_clk (net)
                  0.01    0.00    0.68 ^ stream_buf_0_pipe_2[994]$_DFF_PN0_/CK (DFFR_X1)
                          0.00    0.68   clock reconvergence pessimism
                          0.01    0.69   library hold time
                                  0.69   data required time
-----------------------------------------------------------------------------
                                  0.69   data required time
                                 -0.73   data arrival time
-----------------------------------------------------------------------------
                                  0.05   slack (MET)



```
