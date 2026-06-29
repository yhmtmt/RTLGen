# OpenROAD Timing Debug Summary

- design_dir: `runs/designs/npu_blocks/attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_score24_w16_exact_div`
- metrics_path: `runs/designs/npu_blocks/attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_score24_w16_exact_div/metrics.csv`
- rows_considered: 2

## Metrics Rows

| param_hash | tag | status | critical_path_ns | density | result_path |
| --- | --- | --- | ---: | ---: | --- |
| e7038a18 | attention_dual_stream_composed_v1_hier_score24_w16_exact_div | ok | 29.9544 | 0.4 | `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_score24_w16_exact_div/attention_dual_stream_composed_v1_hier_score24_w16_exact_div/6_finish.rpt` |
| edae7987 | attention_dual_stream_composed_v1_hier_score24_w16_exact_div | ok | 30.0970 | 0.3 | `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_score24_w16_exact_div/attention_dual_stream_composed_v1_hier_score24_w16_exact_div/6_finish.rpt` |

## Inspected Report Files

- `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_score24_w16_exact_div/attention_dual_stream_composed_v1_hier_score24_w16_exact_div/6_finish.rpt`
- `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_score24_w16_exact_div/attention_dual_stream_composed_v1_hier_score24_w16_exact_div/5_global_route.rpt`
- `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_score24_w16_exact_div/attention_dual_stream_composed_v1_hier_score24_w16_exact_div/5_route_drc.rpt`
- `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_score24_w16_exact_div/attention_dual_stream_composed_v1_hier_score24_w16_exact_div/5_route_drc.rpt-5.rpt`
- `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_score24_w16_exact_div/attention_dual_stream_composed_v1_hier_score24_w16_exact_div/4_cts_final.rpt`
- `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_score24_w16_exact_div/attention_dual_stream_composed_v1_hier_score24_w16_exact_div/3_resizer.rpt`
- `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_score24_w16_exact_div/attention_dual_stream_composed_v1_hier_score24_w16_exact_div/3_detailed_place.rpt`
- `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_score24_w16_exact_div/attention_dual_stream_composed_v1_hier_score24_w16_exact_div/3_global_place.rpt`
- `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_score24_w16_exact_div/attention_dual_stream_composed_v1_hier_score24_w16_exact_div/2_floorplan_final.rpt`
- `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_score24_w16_exact_div/attention_dual_stream_composed_v1_hier_score24_w16_exact_div/drt_antennas.log`
- `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_score24_w16_exact_div/attention_dual_stream_composed_v1_hier_score24_w16_exact_div/grt_antennas.log`
- `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_score24_w16_exact_div/attention_dual_stream_composed_v1_hier_score24_w16_exact_div/metadata-generate.log`

## Preferred Final-Stage Timing Paths

- raw_path_block_count: 104
- unique_path_block_count: 28
- preferred_stage: `finish`

### Path 1

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_score24_w16_exact_div/attention_dual_stream_composed_v1_hier_score24_w16_exact_div/6_finish.rpt`
- stage: `finish`
- startpoint: `u_softmax/exp_weight_q[0][12]$_DFF_P_`
- endpoint: `u_softmax/weights[0]$_DFF_P_`
- path_group: `clk`
- path_type: `max`
- slack: `-19.4300`
- data_arrival_time: `29.9500`
- data_required_time: `10.5300`

```text
Startpoint: u_softmax/exp_weight_q[0][12]$_DFF_P_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: u_softmax/weights[0]$_DFF_P_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   53.80    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.02    0.02    0.02 ^ wire103935/A (BUF_X16)
     1   59.67    0.01    0.02    0.04 ^ wire103935/Z (BUF_X16)
                                         net103934 (net)
                  0.03    0.02    0.07 ^ wire103934/A (BUF_X16)
     1   59.77    0.01    0.03    0.10 ^ wire103934/Z (BUF_X16)
                                         net103933 (net)
                  0.01    0.01    0.10 ^ clkbuf_0_clk/A (CLKBUF_X3)
     2   27.18    0.02    0.05    0.15 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.02    0.00    0.16 ^ clkbuf_1_1_0_clk/A (CLKBUF_X3)
     1   22.87    0.02    0.05    0.21 ^ clkbuf_1_1_0_clk/Z (CLKBUF_X3)
...
                                         clknet_5_23_0_clk (net)
                  0.02    0.00   10.48 ^ clkbuf_6_47__f_clk/A (CLKBUF_X3)
     4   53.88    0.04    0.07   10.55 ^ clkbuf_6_47__f_clk/Z (CLKBUF_X3)
                                         clknet_6_47__leaf_clk (net)
                  0.04    0.02   10.56 ^ u_softmax/weights[0]$_DFF_P_/CK (DFF_X2)
                          0.00   10.56   clock reconvergence pessimism
                         -0.03   10.53   library setup time
                                 10.53   data required time
-----------------------------------------------------------------------------
                                 10.53   data required time
                                -29.95   data arrival time
-----------------------------------------------------------------------------
                                -19.43   slack (VIOLATED)



```

### Path 2

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_score24_w16_exact_div/attention_dual_stream_composed_v1_hier_score24_w16_exact_div/6_finish.rpt`
- stage: `finish`
- startpoint: `seed_state[20]$_DFF_PN0_`
- endpoint: `stream_buf_1[20]$_DFF_PN0_`
- path_group: `clk`
- path_type: `min`
- slack: `0.0300`
- data_arrival_time: `0.6600`
- data_required_time: `0.6300`

```text
Startpoint: seed_state[20]$_DFF_PN0_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: stream_buf_1[20]$_DFF_PN0_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   53.80    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.02    0.02    0.02 ^ wire103935/A (BUF_X16)
     1   59.67    0.01    0.02    0.04 ^ wire103935/Z (BUF_X16)
                                         net103934 (net)
                  0.03    0.02    0.07 ^ wire103934/A (BUF_X16)
     1   59.77    0.01    0.03    0.10 ^ wire103934/Z (BUF_X16)
                                         net103933 (net)
                  0.01    0.01    0.10 ^ clkbuf_0_clk/A (CLKBUF_X3)
     2   27.18    0.02    0.05    0.15 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.02    0.00    0.16 ^ clkbuf_1_1_0_clk/A (CLKBUF_X3)
     1   22.87    0.02    0.05    0.21 ^ clkbuf_1_1_0_clk/Z (CLKBUF_X3)
...
                                         clknet_6_51__leaf_clk (net)
                  0.04    0.00    0.57 ^ clkbuf_leaf_162_clk/A (CLKBUF_X3)
     3   11.89    0.01    0.05    0.61 ^ clkbuf_leaf_162_clk/Z (CLKBUF_X3)
                                         clknet_leaf_162_clk (net)
                  0.01    0.00    0.62 ^ stream_buf_1[20]$_DFF_PN0_/CK (DFFR_X1)
                          0.00    0.62   clock reconvergence pessimism
                          0.01    0.63   library hold time
                                  0.63   data required time
-----------------------------------------------------------------------------
                                  0.63   data required time
                                 -0.66   data arrival time
-----------------------------------------------------------------------------
                                  0.03   slack (MET)



```

### Path 3

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_score24_w16_exact_div/attention_dual_stream_composed_v1_hier_score24_w16_exact_div/6_finish.rpt`
- stage: `finish`
- startpoint: `rst_n (input port clocked by clk)`
- endpoint: `stream_buf_0_pipe_1[803]$_DFF_PN0_`
- path_group: `asynchronous`
- path_type: `min`
- slack: `1.6600`
- data_arrival_time: `2.5700`
- data_required_time: `0.9100`

```text
Startpoint: rst_n (input port clocked by clk)
Endpoint: stream_buf_0_pipe_1[803]$_DFF_PN0_
          (removal check against rising-edge clock clk)
Path Group: asynchronous
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (propagated)
                          2.00    2.00 ^ input external delay
     1    6.94    0.00    0.00    2.00 ^ rst_n (in)
                                         rst_n (net)
                  0.00    0.00    2.00 ^ input265/A (CLKBUF_X3)
     1   17.07    0.02    0.04    2.04 ^ input265/Z (CLKBUF_X3)
                                         net264 (net)
                  0.02    0.01    2.04 ^ place103737/A (BUF_X1)
     1   23.93    0.05    0.07    2.12 ^ place103737/Z (BUF_X1)
                                         net103736 (net)
                  0.06    0.01    2.13 ^ place103738/A (BUF_X1)
     1   39.62    0.09    0.12    2.25 ^ place103738/Z (BUF_X1)
                                         net103737 (net)
                  0.09    0.01    2.26 ^ place103739/A (BUF_X1)
     1   29.64    0.07    0.10    2.36 ^ place103739/Z (BUF_X1)
...
                                         clknet_5_29_0_clk (net)
                  0.02    0.00    0.49 ^ clkbuf_6_58__f_clk/A (CLKBUF_X3)
     6   39.59    0.03    0.06    0.55 ^ clkbuf_6_58__f_clk/Z (CLKBUF_X3)
                                         clknet_6_58__leaf_clk (net)
                  0.03    0.00    0.56 ^ clkbuf_leaf_145_clk/A (CLKBUF_X3)
     5   15.38    0.02    0.05    0.60 ^ clkbuf_leaf_145_clk/Z (CLKBUF_X3)
                                         clknet_leaf_145_clk (net)
                  0.02    0.00    0.61 ^ stream_buf_0_pipe_1[803]$_DFF_PN0_/CK (DFFR_X1)
                          0.00    0.61   clock reconvergence pessimism
                          0.30    0.91   library removal time
                                  0.91   data required time
-----------------------------------------------------------------------------
                                  0.91   data required time
                                 -2.57   data arrival time
-----------------------------------------------------------------------------
                                  1.66   slack (MET)
```

### Path 4

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_score24_w16_exact_div/attention_dual_stream_composed_v1_hier_score24_w16_exact_div/6_finish.rpt`
- stage: `finish`
- startpoint: `rst_n (input port clocked by clk)`
- endpoint: `stream_buf_1[8]$_DFF_PN0_`
- path_group: `asynchronous`
- path_type: `max`
- slack: `7.3800`
- data_arrival_time: `3.2700`
- data_required_time: `10.6500`

```text
Startpoint: rst_n (input port clocked by clk)
Endpoint: stream_buf_1[8]$_DFF_PN0_
          (recovery check against rising-edge clock clk)
Path Group: asynchronous
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (propagated)
                          2.00    2.00 ^ input external delay
     1    6.94    0.00    0.00    2.00 ^ rst_n (in)
                                         rst_n (net)
                  0.00    0.00    2.00 ^ input265/A (CLKBUF_X3)
     1   17.07    0.02    0.04    2.04 ^ input265/Z (CLKBUF_X3)
                                         net264 (net)
                  0.02    0.01    2.04 ^ place103737/A (BUF_X1)
     1   23.93    0.05    0.07    2.12 ^ place103737/Z (BUF_X1)
                                         net103736 (net)
                  0.06    0.01    2.13 ^ place103738/A (BUF_X1)
     1   39.62    0.09    0.12    2.25 ^ place103738/Z (BUF_X1)
                                         net103737 (net)
                  0.09    0.01    2.26 ^ place103739/A (BUF_X1)
     1   29.64    0.07    0.10    2.36 ^ place103739/Z (BUF_X1)
...
                                         clknet_5_2_0_clk (net)
                  0.02    0.00   10.49 ^ clkbuf_6_4__f_clk/A (CLKBUF_X3)
     7   41.19    0.03    0.06   10.56 ^ clkbuf_6_4__f_clk/Z (CLKBUF_X3)
                                         clknet_6_4__leaf_clk (net)
                  0.03    0.00   10.56 ^ clkbuf_leaf_5_clk/A (CLKBUF_X3)
     5    9.96    0.01    0.04   10.60 ^ clkbuf_leaf_5_clk/Z (CLKBUF_X3)
                                         clknet_leaf_5_clk (net)
                  0.01    0.00   10.60 ^ stream_buf_1[8]$_DFF_PN0_/CK (DFFR_X1)
                          0.00   10.60   clock reconvergence pessimism
                          0.05   10.65   library recovery time
                                 10.65   data required time
-----------------------------------------------------------------------------
                                 10.65   data required time
                                 -3.27   data arrival time
-----------------------------------------------------------------------------
                                  7.38   slack (MET)
```


## Worst Timing Paths Across All Stages

### Path 1

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_score24_w16_exact_div/attention_dual_stream_composed_v1_hier_score24_w16_exact_div/2_floorplan_final.rpt`
- stage: `floorplan`
- startpoint: `u_softmax/sum_weight_q[7]$_DFF_P_`
- endpoint: `u_softmax/weights[48]$_DFF_P_`
- path_group: `clk`
- path_type: `max`
- slack: `-26.8100`
- data_arrival_time: `36.7700`
- data_required_time: `9.9600`

```text
Startpoint: u_softmax/sum_weight_q[7]$_DFF_P_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: u_softmax/weights[48]$_DFF_P_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                  0.00    0.00    0.00 ^ u_softmax/sum_weight_q[7]$_DFF_P_/CK (DFF_X2)
   336 1073.08    1.22    1.37    1.37 ^ u_softmax/sum_weight_q[7]$_DFF_P_/QN (DFF_X2)
                                         u_softmax/_096131_ (net)
                  1.22    0.00    1.37 ^ u_softmax/_175473_/B (FA_X1)
     1    1.70    0.04    0.20    1.57 ^ u_softmax/_175473_/S (FA_X1)
                                         u_softmax/_003711_ (net)
                  0.04    0.00    1.57 ^ u_softmax/_152306_/A (INV_X1)
     1    3.40    0.01    0.01    1.58 v u_softmax/_152306_/ZN (INV_X1)
                                         u_softmax/_003725_ (net)
                  0.01    0.00    1.58 v u_softmax/_175478_/B (FA_X1)
     1    1.70    0.01    0.12    1.70 ^ u_softmax/_175478_/S (FA_X1)
                                         u_softmax/_003727_ (net)
                  0.01    0.00    1.70 ^ u_softmax/_150933_/A (INV_X1)
...
                                 36.77   data arrival time

                  0.00   10.00   10.00   clock clk (rise edge)
                          0.00   10.00   clock network delay (ideal)
                          0.00   10.00   clock reconvergence pessimism
                                 10.00 ^ u_softmax/weights[48]$_DFF_P_/CK (DFF_X1)
                         -0.04    9.96   library setup time
                                  9.96   data required time
-----------------------------------------------------------------------------
                                  9.96   data required time
                                -36.77   data arrival time
-----------------------------------------------------------------------------
                                -26.81   slack (VIOLATED)



```

### Path 2

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_score24_w16_exact_div/attention_dual_stream_composed_v1_hier_score24_w16_exact_div/3_global_place.rpt`
- stage: `global_place`
- startpoint: `u_softmax/exp_weight_q[0][12]$_DFF_P_`
- endpoint: `u_softmax/weights[0]$_DFF_P_`
- path_group: `clk`
- path_type: `max`
- slack: `-21.0500`
- data_arrival_time: `31.0000`
- data_required_time: `9.9500`

```text
Startpoint: u_softmax/exp_weight_q[0][12]$_DFF_P_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: u_softmax/weights[0]$_DFF_P_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                  0.00    0.00    0.00 ^ u_softmax/exp_weight_q[0][12]$_DFF_P_/CK (DFF_X1)
     3    9.40    0.01    0.09    0.09 v u_softmax/exp_weight_q[0][12]$_DFF_P_/Q (DFF_X1)
                                         u_softmax/exp_weight_q[0][12] (net)
                  0.01    0.00    0.09 v place100549/A (BUF_X1)
     1    2.96    0.01    0.03    0.12 v place100549/Z (BUF_X1)
                                         net100548 (net)
                  0.01    0.00    0.12 v u_softmax/_176378_/CI (FA_X1)
     3    7.51    0.02    0.12    0.24 ^ u_softmax/_176378_/S (FA_X1)
                                         u_softmax/_005609_ (net)
                  0.02    0.00    0.24 ^ u_softmax/_152851_/A (INV_X1)
     1    4.10    0.01    0.01    0.26 v u_softmax/_152851_/ZN (INV_X1)
                                         u_softmax/_005636_ (net)
                  0.01    0.00    0.26 v u_softmax/_176482_/A (FA_X1)
...
                                 31.00   data arrival time

                  0.00   10.00   10.00   clock clk (rise edge)
                          0.00   10.00   clock network delay (ideal)
                          0.00   10.00   clock reconvergence pessimism
                                 10.00 ^ u_softmax/weights[0]$_DFF_P_/CK (DFF_X2)
                         -0.05    9.95   library setup time
                                  9.95   data required time
-----------------------------------------------------------------------------
                                  9.95   data required time
                                -31.00   data arrival time
-----------------------------------------------------------------------------
                                -21.05   slack (VIOLATED)



```

### Path 3

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_score24_w16_exact_div/attention_dual_stream_composed_v1_hier_score24_w16_exact_div/3_resizer.rpt`
- stage: `resizer`
- startpoint: `u_softmax/exp_weight_q[0][12]$_DFF_P_`
- endpoint: `u_softmax/weights[0]$_DFF_P_`
- path_group: `clk`
- path_type: `max`
- slack: `-21.0500`
- data_arrival_time: `31.0000`
- data_required_time: `9.9500`

```text
Startpoint: u_softmax/exp_weight_q[0][12]$_DFF_P_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: u_softmax/weights[0]$_DFF_P_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                  0.00    0.00    0.00 ^ u_softmax/exp_weight_q[0][12]$_DFF_P_/CK (DFF_X1)
     3    9.40    0.01    0.09    0.09 v u_softmax/exp_weight_q[0][12]$_DFF_P_/Q (DFF_X1)
                                         u_softmax/exp_weight_q[0][12] (net)
                  0.01    0.00    0.09 v place100549/A (BUF_X1)
     1    2.96    0.01    0.03    0.12 v place100549/Z (BUF_X1)
                                         net100548 (net)
                  0.01    0.00    0.12 v u_softmax/_176378_/CI (FA_X1)
     3    7.51    0.02    0.12    0.24 ^ u_softmax/_176378_/S (FA_X1)
                                         u_softmax/_005609_ (net)
                  0.02    0.00    0.24 ^ u_softmax/_152851_/A (INV_X1)
     1    4.10    0.01    0.01    0.26 v u_softmax/_152851_/ZN (INV_X1)
                                         u_softmax/_005636_ (net)
                  0.01    0.00    0.26 v u_softmax/_176482_/A (FA_X1)
...
                                 31.00   data arrival time

                  0.00   10.00   10.00   clock clk (rise edge)
                          0.00   10.00   clock network delay (ideal)
                          0.00   10.00   clock reconvergence pessimism
                                 10.00 ^ u_softmax/weights[0]$_DFF_P_/CK (DFF_X2)
                         -0.05    9.95   library setup time
                                  9.95   data required time
-----------------------------------------------------------------------------
                                  9.95   data required time
                                -31.00   data arrival time
-----------------------------------------------------------------------------
                                -21.05   slack (VIOLATED)



```

### Path 4

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_score24_w16_exact_div/attention_dual_stream_composed_v1_hier_score24_w16_exact_div/3_detailed_place.rpt`
- stage: `detailed_place`
- startpoint: `u_softmax/sum_weight_q[19]$_DFF_P_`
- endpoint: `u_softmax/weights[96]$_DFF_P_`
- path_group: `clk`
- path_type: `max`
- slack: `-20.5900`
- data_arrival_time: `30.5500`
- data_required_time: `9.9500`

```text
Startpoint: u_softmax/sum_weight_q[19]$_DFF_P_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: u_softmax/weights[96]$_DFF_P_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                  0.00    0.00    0.00 ^ u_softmax/sum_weight_q[19]$_DFF_P_/CK (DFF_X2)
     2    6.23    0.01    0.08    0.08 ^ u_softmax/sum_weight_q[19]$_DFF_P_/QN (DFF_X2)
                                         u_softmax/_095965_ (net)
                  0.01    0.00    0.08 ^ place99638/A (BUF_X1)
     8   47.50    0.10    0.13    0.21 ^ place99638/Z (BUF_X1)
                                         net99637 (net)
                  0.11    0.01    0.22 ^ place99649/A (BUF_X1)
     3   22.27    0.05    0.08    0.30 ^ place99649/Z (BUF_X1)
                                         net99648 (net)
                  0.05    0.01    0.31 ^ place99650/A (BUF_X2)
     7   58.06    0.06    0.09    0.39 ^ place99650/Z (BUF_X2)
                                         net99649 (net)
                  0.07    0.02    0.41 ^ place99659/A (BUF_X1)
...
                                 30.55   data arrival time

                  0.00   10.00   10.00   clock clk (rise edge)
                          0.00   10.00   clock network delay (ideal)
                          0.00   10.00   clock reconvergence pessimism
                                 10.00 ^ u_softmax/weights[96]$_DFF_P_/CK (DFF_X2)
                         -0.05    9.95   library setup time
                                  9.95   data required time
-----------------------------------------------------------------------------
                                  9.95   data required time
                                -30.55   data arrival time
-----------------------------------------------------------------------------
                                -20.59   slack (VIOLATED)



```

### Path 5

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_score24_w16_exact_div/attention_dual_stream_composed_v1_hier_score24_w16_exact_div/5_global_route.rpt`
- stage: `route`
- startpoint: `u_softmax/exp_weight_q[0][12]$_DFF_P_`
- endpoint: `u_softmax/weights[0]$_DFF_P_`
- path_group: `clk`
- path_type: `max`
- slack: `-19.5700`
- data_arrival_time: `30.1600`
- data_required_time: `10.5900`

```text
Startpoint: u_softmax/exp_weight_q[0][12]$_DFF_P_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: u_softmax/weights[0]$_DFF_P_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   71.04    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.03    0.02    0.02 ^ wire103935/A (BUF_X16)
     1   64.85    0.01    0.03    0.05 ^ wire103935/Z (BUF_X16)
                                         net103934 (net)
                  0.03    0.02    0.08 ^ wire103934/A (BUF_X16)
     1   60.39    0.01    0.03    0.11 ^ wire103934/Z (BUF_X16)
                                         net103933 (net)
                  0.01    0.01    0.11 ^ clkbuf_0_clk/A (CLKBUF_X3)
     2   32.17    0.03    0.05    0.16 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.03    0.01    0.17 ^ clkbuf_1_1_0_clk/A (CLKBUF_X3)
     1   27.43    0.02    0.05    0.22 ^ clkbuf_1_1_0_clk/Z (CLKBUF_X3)
...
                                         clknet_5_23_0_clk (net)
                  0.02    0.00   10.52 ^ clkbuf_6_47__f_clk/A (CLKBUF_X3)
     4   62.69    0.05    0.08   10.60 ^ clkbuf_6_47__f_clk/Z (CLKBUF_X3)
                                         clknet_6_47__leaf_clk (net)
                  0.05    0.02   10.62 ^ u_softmax/weights[0]$_DFF_P_/CK (DFF_X2)
                          0.00   10.62   clock reconvergence pessimism
                         -0.03   10.59   library setup time
                                 10.59   data required time
-----------------------------------------------------------------------------
                                 10.59   data required time
                                -30.16   data arrival time
-----------------------------------------------------------------------------
                                -19.57   slack (VIOLATED)



```

### Path 6

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_score24_w16_exact_div/attention_dual_stream_composed_v1_hier_score24_w16_exact_div/6_finish.rpt`
- stage: `finish`
- startpoint: `u_softmax/exp_weight_q[0][12]$_DFF_P_`
- endpoint: `u_softmax/weights[0]$_DFF_P_`
- path_group: `clk`
- path_type: `max`
- slack: `-19.4300`
- data_arrival_time: `29.9500`
- data_required_time: `10.5300`

```text
Startpoint: u_softmax/exp_weight_q[0][12]$_DFF_P_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: u_softmax/weights[0]$_DFF_P_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   53.80    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.02    0.02    0.02 ^ wire103935/A (BUF_X16)
     1   59.67    0.01    0.02    0.04 ^ wire103935/Z (BUF_X16)
                                         net103934 (net)
                  0.03    0.02    0.07 ^ wire103934/A (BUF_X16)
     1   59.77    0.01    0.03    0.10 ^ wire103934/Z (BUF_X16)
                                         net103933 (net)
                  0.01    0.01    0.10 ^ clkbuf_0_clk/A (CLKBUF_X3)
     2   27.18    0.02    0.05    0.15 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.02    0.00    0.16 ^ clkbuf_1_1_0_clk/A (CLKBUF_X3)
     1   22.87    0.02    0.05    0.21 ^ clkbuf_1_1_0_clk/Z (CLKBUF_X3)
...
                                         clknet_5_23_0_clk (net)
                  0.02    0.00   10.48 ^ clkbuf_6_47__f_clk/A (CLKBUF_X3)
     4   53.88    0.04    0.07   10.55 ^ clkbuf_6_47__f_clk/Z (CLKBUF_X3)
                                         clknet_6_47__leaf_clk (net)
                  0.04    0.02   10.56 ^ u_softmax/weights[0]$_DFF_P_/CK (DFF_X2)
                          0.00   10.56   clock reconvergence pessimism
                         -0.03   10.53   library setup time
                                 10.53   data required time
-----------------------------------------------------------------------------
                                 10.53   data required time
                                -29.95   data arrival time
-----------------------------------------------------------------------------
                                -19.43   slack (VIOLATED)



```

### Path 7

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_score24_w16_exact_div/attention_dual_stream_composed_v1_hier_score24_w16_exact_div/4_cts_final.rpt`
- stage: `cts`
- startpoint: `u_softmax/sum_weight_q[19]$_DFF_P_`
- endpoint: `u_softmax/weights[96]$_DFF_P_`
- path_group: `clk`
- path_type: `max`
- slack: `-19.3700`
- data_arrival_time: `29.9500`
- data_required_time: `10.5700`

```text
Startpoint: u_softmax/sum_weight_q[19]$_DFF_P_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: u_softmax/weights[96]$_DFF_P_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   71.44    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.03    0.02    0.02 ^ wire103935/A (BUF_X16)
     1   65.37    0.01    0.03    0.05 ^ wire103935/Z (BUF_X16)
                                         net103934 (net)
                  0.03    0.02    0.07 ^ wire103934/A (BUF_X16)
     1   67.12    0.01    0.03    0.10 ^ wire103934/Z (BUF_X16)
                                         net103933 (net)
                  0.03    0.02    0.13 ^ clkbuf_0_clk/A (CLKBUF_X3)
     2   32.06    0.03    0.06    0.19 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.03    0.00    0.19 ^ clkbuf_1_1_0_clk/A (CLKBUF_X3)
     1   27.51    0.02    0.06    0.25 ^ clkbuf_1_1_0_clk/Z (CLKBUF_X3)
...
                                         clknet_5_19_0_clk (net)
                  0.02    0.00   10.56 ^ clkbuf_6_38__f_clk/A (CLKBUF_X3)
     3   29.91    0.02    0.06   10.61 ^ clkbuf_6_38__f_clk/Z (CLKBUF_X3)
                                         clknet_6_38__leaf_clk (net)
                  0.02    0.00   10.61 ^ u_softmax/weights[96]$_DFF_P_/CK (DFF_X2)
                          0.00   10.61   clock reconvergence pessimism
                         -0.04   10.57   library setup time
                                 10.57   data required time
-----------------------------------------------------------------------------
                                 10.57   data required time
                                -29.95   data arrival time
-----------------------------------------------------------------------------
                                -19.37   slack (VIOLATED)



```

### Path 8

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_score24_w16_exact_div/attention_dual_stream_composed_v1_hier_score24_w16_exact_div/6_finish.rpt`
- stage: `finish`
- startpoint: `seed_state[20]$_DFF_PN0_`
- endpoint: `stream_buf_1[20]$_DFF_PN0_`
- path_group: `clk`
- path_type: `min`
- slack: `0.0300`
- data_arrival_time: `0.6600`
- data_required_time: `0.6300`

```text
Startpoint: seed_state[20]$_DFF_PN0_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: stream_buf_1[20]$_DFF_PN0_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   53.80    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.02    0.02    0.02 ^ wire103935/A (BUF_X16)
     1   59.67    0.01    0.02    0.04 ^ wire103935/Z (BUF_X16)
                                         net103934 (net)
                  0.03    0.02    0.07 ^ wire103934/A (BUF_X16)
     1   59.77    0.01    0.03    0.10 ^ wire103934/Z (BUF_X16)
                                         net103933 (net)
                  0.01    0.01    0.10 ^ clkbuf_0_clk/A (CLKBUF_X3)
     2   27.18    0.02    0.05    0.15 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.02    0.00    0.16 ^ clkbuf_1_1_0_clk/A (CLKBUF_X3)
     1   22.87    0.02    0.05    0.21 ^ clkbuf_1_1_0_clk/Z (CLKBUF_X3)
...
                                         clknet_6_51__leaf_clk (net)
                  0.04    0.00    0.57 ^ clkbuf_leaf_162_clk/A (CLKBUF_X3)
     3   11.89    0.01    0.05    0.61 ^ clkbuf_leaf_162_clk/Z (CLKBUF_X3)
                                         clknet_leaf_162_clk (net)
                  0.01    0.00    0.62 ^ stream_buf_1[20]$_DFF_PN0_/CK (DFFR_X1)
                          0.00    0.62   clock reconvergence pessimism
                          0.01    0.63   library hold time
                                  0.63   data required time
-----------------------------------------------------------------------------
                                  0.63   data required time
                                 -0.66   data arrival time
-----------------------------------------------------------------------------
                                  0.03   slack (MET)



```
