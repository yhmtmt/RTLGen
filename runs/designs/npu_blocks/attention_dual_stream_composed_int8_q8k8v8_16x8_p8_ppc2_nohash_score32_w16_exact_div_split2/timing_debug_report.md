# OpenROAD Timing Debug Summary

- design_dir: `runs/designs/npu_blocks/attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_score32_w16_exact_div_split2`
- metrics_path: `runs/designs/npu_blocks/attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_score32_w16_exact_div_split2/metrics.csv`
- rows_considered: 2

## Metrics Rows

| param_hash | tag | status | critical_path_ns | density | result_path |
| --- | --- | --- | ---: | ---: | --- |
| 85760ad4 | attention_dual_stream_composed_v1_hier_score32_w16_exact_div_split2 | ok | 48.8529 | 0.4 | `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_score32_w16_exact_div_split2/attention_dual_stream_composed_v1_hier_score32_w16_exact_div_split2/6_finish.rpt` |
| 33c094ce | attention_dual_stream_composed_v1_hier_score32_w16_exact_div_split2 | ok | 50.3038 | 0.3 | `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_score32_w16_exact_div_split2/attention_dual_stream_composed_v1_hier_score32_w16_exact_div_split2/6_finish.rpt` |

## Inspected Report Files

- `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_score32_w16_exact_div_split2/attention_dual_stream_composed_v1_hier_score32_w16_exact_div_split2/6_finish.rpt`
- `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_score32_w16_exact_div_split2/attention_dual_stream_composed_v1_hier_score32_w16_exact_div_split2/5_global_route.rpt`
- `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_score32_w16_exact_div_split2/attention_dual_stream_composed_v1_hier_score32_w16_exact_div_split2/5_route_drc.rpt`
- `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_score32_w16_exact_div_split2/attention_dual_stream_composed_v1_hier_score32_w16_exact_div_split2/4_cts_final.rpt`
- `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_score32_w16_exact_div_split2/attention_dual_stream_composed_v1_hier_score32_w16_exact_div_split2/3_resizer.rpt`
- `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_score32_w16_exact_div_split2/attention_dual_stream_composed_v1_hier_score32_w16_exact_div_split2/3_detailed_place.rpt`
- `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_score32_w16_exact_div_split2/attention_dual_stream_composed_v1_hier_score32_w16_exact_div_split2/3_global_place.rpt`
- `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_score32_w16_exact_div_split2/attention_dual_stream_composed_v1_hier_score32_w16_exact_div_split2/2_floorplan_final.rpt`
- `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_score32_w16_exact_div_split2/attention_dual_stream_composed_v1_hier_score32_w16_exact_div_split2/drt_antennas.log`
- `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_score32_w16_exact_div_split2/attention_dual_stream_composed_v1_hier_score32_w16_exact_div_split2/grt_antennas.log`
- `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_score32_w16_exact_div_split2/attention_dual_stream_composed_v1_hier_score32_w16_exact_div_split2/metadata-generate.log`

## Preferred Final-Stage Timing Paths

- raw_path_block_count: 104
- unique_path_block_count: 28
- preferred_stage: `finish`

### Path 1

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_score32_w16_exact_div_split2/attention_dual_stream_composed_v1_hier_score32_w16_exact_div_split2/6_finish.rpt`
- stage: `finish`
- startpoint: `u_softmax/sum_weight_qq[32]$_DFF_P_`
- endpoint: `u_softmax/weights[16]$_DFF_P_`
- path_group: `clk`
- path_type: `max`
- slack: `-38.1700`
- data_arrival_time: `48.8500`
- data_required_time: `10.6800`

```text
Startpoint: u_softmax/sum_weight_qq[32]$_DFF_P_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: u_softmax/weights[16]$_DFF_P_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   49.83    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.02    0.02    0.02 ^ wire154982/A (BUF_X16)
     1   52.71    0.01    0.02    0.04 ^ wire154982/Z (BUF_X16)
                                         net154981 (net)
                  0.03    0.02    0.06 ^ wire154981/A (BUF_X16)
     1   65.35    0.01    0.03    0.09 ^ wire154981/Z (BUF_X16)
                                         net154980 (net)
                  0.04    0.03    0.12 ^ wire154980/A (BUF_X32)
     1   57.15    0.01    0.02    0.14 ^ wire154980/Z (BUF_X32)
                                         net154979 (net)
                  0.03    0.02    0.17 ^ clkbuf_0_clk/A (CLKBUF_X3)
     2   34.07    0.03    0.06    0.23 ^ clkbuf_0_clk/Z (CLKBUF_X3)
...
                                         clknet_6_51_0_clk (net)
                  0.04    0.01   10.68 ^ clkbuf_leaf_616_clk/A (CLKBUF_X3)
     5    8.93    0.01    0.04   10.72 ^ clkbuf_leaf_616_clk/Z (CLKBUF_X3)
                                         clknet_leaf_616_clk (net)
                  0.01    0.00   10.72 ^ u_softmax/weights[16]$_DFF_P_/CK (DFF_X1)
                          0.00   10.72   clock reconvergence pessimism
                         -0.04   10.68   library setup time
                                 10.68   data required time
-----------------------------------------------------------------------------
                                 10.68   data required time
                                -48.85   data arrival time
-----------------------------------------------------------------------------
                                -38.17   slack (VIOLATED)



```

### Path 2

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_score32_w16_exact_div_split2/attention_dual_stream_composed_v1_hier_score32_w16_exact_div_split2/6_finish.rpt`
- stage: `finish`
- startpoint: `stream_buf_0_pipe_3[709]$_DFF_PN0_`
- endpoint: `stream_buf_0_pipe_3[741]$_DFF_PN0_`
- path_group: `clk`
- path_type: `min`
- slack: `0.0300`
- data_arrival_time: `0.8500`
- data_required_time: `0.8300`

```text
Startpoint: stream_buf_0_pipe_3[709]$_DFF_PN0_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: stream_buf_0_pipe_3[741]$_DFF_PN0_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   49.83    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.02    0.02    0.02 ^ wire154982/A (BUF_X16)
     1   52.71    0.01    0.02    0.04 ^ wire154982/Z (BUF_X16)
                                         net154981 (net)
                  0.03    0.02    0.06 ^ wire154981/A (BUF_X16)
     1   65.35    0.01    0.03    0.09 ^ wire154981/Z (BUF_X16)
                                         net154980 (net)
                  0.04    0.03    0.12 ^ wire154980/A (BUF_X32)
     1   57.15    0.01    0.02    0.14 ^ wire154980/Z (BUF_X32)
                                         net154979 (net)
                  0.03    0.02    0.17 ^ clkbuf_0_clk/A (CLKBUF_X3)
     2   34.07    0.03    0.06    0.23 ^ clkbuf_0_clk/Z (CLKBUF_X3)
...
                                         clknet_6_34_0_clk (net)
                  0.07    0.00    0.77 ^ clkbuf_leaf_212_clk/A (CLKBUF_X3)
     5    9.63    0.01    0.05    0.82 ^ clkbuf_leaf_212_clk/Z (CLKBUF_X3)
                                         clknet_leaf_212_clk (net)
                  0.01    0.00    0.82 ^ stream_buf_0_pipe_3[741]$_DFF_PN0_/CK (DFFR_X1)
                          0.00    0.82   clock reconvergence pessimism
                          0.00    0.83   library hold time
                                  0.83   data required time
-----------------------------------------------------------------------------
                                  0.83   data required time
                                 -0.85   data arrival time
-----------------------------------------------------------------------------
                                  0.03   slack (MET)



```

### Path 3

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_score32_w16_exact_div_split2/attention_dual_stream_composed_v1_hier_score32_w16_exact_div_split2/6_finish.rpt`
- stage: `finish`
- startpoint: `rst_n (input port clocked by clk)`
- endpoint: `score_mix_1_out[15]$_DFFE_PN0P_`
- path_group: `asynchronous`
- path_type: `min`
- slack: `1.0600`
- data_arrival_time: `2.0600`
- data_required_time: `0.9900`

```text
Startpoint: rst_n (input port clocked by clk)
Endpoint: score_mix_1_out[15]$_DFFE_PN0P_
          (removal check against rising-edge clock clk)
Path Group: asynchronous
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (propagated)
                          2.00    2.00 ^ input external delay
     1    4.55    0.00    0.00    2.00 ^ rst_n (in)
                                         rst_n (net)
                  0.00    0.00    2.00 ^ input393/A (CLKBUF_X3)
    13   49.07    0.03    0.05    2.05 ^ input393/Z (CLKBUF_X3)
                                         net392 (net)
                  0.03    0.00    2.06 ^ score_mix_1_out[15]$_DFFE_PN0P_/RN (DFFR_X1)
                                  2.06   data arrival time

                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   49.83    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.02    0.02    0.02 ^ wire154982/A (BUF_X16)
...
                                         clknet_5_21_0_clk (net)
                  0.02    0.00    0.64 ^ clkbuf_6_42_0_clk/A (CLKBUF_X3)
    10   46.37    0.03    0.06    0.70 ^ clkbuf_6_42_0_clk/Z (CLKBUF_X3)
                                         clknet_6_42_0_clk (net)
                  0.04    0.02    0.72 ^ clkbuf_leaf_300_clk/A (CLKBUF_X3)
     7    9.13    0.01    0.05    0.77 ^ clkbuf_leaf_300_clk/Z (CLKBUF_X3)
                                         clknet_leaf_300_clk (net)
                  0.01    0.00    0.77 ^ score_mix_1_out[15]$_DFFE_PN0P_/CK (DFFR_X1)
                          0.00    0.77   clock reconvergence pessimism
                          0.23    0.99   library removal time
                                  0.99   data required time
-----------------------------------------------------------------------------
                                  0.99   data required time
                                 -2.06   data arrival time
-----------------------------------------------------------------------------
                                  1.06   slack (MET)
```

### Path 4

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_score32_w16_exact_div_split2/attention_dual_stream_composed_v1_hier_score32_w16_exact_div_split2/6_finish.rpt`
- stage: `finish`
- startpoint: `rst_n (input port clocked by clk)`
- endpoint: `softmax_weights_out[36]$_DFFE_PN0P_`
- path_group: `asynchronous`
- path_type: `max`
- slack: `7.7100`
- data_arrival_time: `3.0300`
- data_required_time: `10.7500`

```text
Startpoint: rst_n (input port clocked by clk)
Endpoint: softmax_weights_out[36]$_DFFE_PN0P_
          (recovery check against rising-edge clock clk)
Path Group: asynchronous
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (propagated)
                          2.00    2.00 ^ input external delay
     1    4.55    0.00    0.00    2.00 ^ rst_n (in)
                                         rst_n (net)
                  0.00    0.00    2.00 ^ input393/A (CLKBUF_X3)
    13   49.07    0.03    0.05    2.05 ^ input393/Z (CLKBUF_X3)
                                         net392 (net)
                  0.04    0.02    2.08 ^ place154734/A (BUF_X2)
     2   37.57    0.04    0.06    2.14 ^ place154734/Z (BUF_X2)
                                         net154733 (net)
                  0.04    0.01    2.15 ^ place154809/A (BUF_X2)
     2   44.64    0.05    0.07    2.22 ^ place154809/Z (BUF_X2)
                                         net154808 (net)
                  0.05    0.02    2.24 ^ place154810/A (BUF_X2)
     4   49.12    0.05    0.07    2.30 ^ place154810/Z (BUF_X2)
...
                                         clknet_5_26_0_clk (net)
                  0.02    0.00   10.60 ^ clkbuf_6_53_0_clk/A (CLKBUF_X3)
    11   35.56    0.03    0.06   10.66 ^ clkbuf_6_53_0_clk/Z (CLKBUF_X3)
                                         clknet_6_53_0_clk (net)
                  0.03    0.00   10.66 ^ clkbuf_leaf_630_clk/A (CLKBUF_X3)
     6    8.36    0.01    0.04   10.71 ^ clkbuf_leaf_630_clk/Z (CLKBUF_X3)
                                         clknet_leaf_630_clk (net)
                  0.01    0.00   10.71 ^ softmax_weights_out[36]$_DFFE_PN0P_/CK (DFFR_X1)
                          0.00   10.71   clock reconvergence pessimism
                          0.04   10.75   library recovery time
                                 10.75   data required time
-----------------------------------------------------------------------------
                                 10.75   data required time
                                 -3.03   data arrival time
-----------------------------------------------------------------------------
                                  7.71   slack (MET)
```


## Worst Timing Paths Across All Stages

### Path 1

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_score32_w16_exact_div_split2/attention_dual_stream_composed_v1_hier_score32_w16_exact_div_split2/2_floorplan_final.rpt`
- stage: `floorplan`
- startpoint: `u_softmax/sum_weight_qq[0]$_DFF_P_`
- endpoint: `u_softmax/weights[80]$_DFF_P_`
- path_group: `clk`
- path_type: `max`
- slack: `-51.9100`
- data_arrival_time: `61.8700`
- data_required_time: `9.9600`

```text
Startpoint: u_softmax/sum_weight_qq[0]$_DFF_P_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: u_softmax/weights[80]$_DFF_P_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                  0.00    0.00    0.00 ^ u_softmax/sum_weight_qq[0]$_DFF_P_/CK (DFF_X2)
   440 1408.32    1.60    1.77    1.77 ^ u_softmax/sum_weight_qq[0]$_DFF_P_/QN (DFF_X2)
                                         u_softmax/_159287_ (net)
                  1.60    0.00    1.77 ^ u_softmax/_291933_/A (HA_X1)
     1    1.60    0.06    0.11    1.88 ^ u_softmax/_291933_/CO (HA_X1)
                                         u_softmax/_015888_ (net)
                  0.06    0.00    1.88 ^ u_softmax/_188272_/A1 (NAND2_X1)
     1    2.93    0.02    0.02    1.90 v u_softmax/_188272_/ZN (NAND2_X1)
                                         u_softmax/_130834_ (net)
                  0.02    0.00    1.90 v u_softmax/_188273_/B1 (AOI22_X2)
     2    5.07    0.06    0.05    1.95 ^ u_softmax/_188273_/ZN (AOI22_X2)
                                         u_softmax/_015890_ (net)
                  0.06    0.00    1.95 ^ u_softmax/_291934_/B (HA_X1)
...
                                 61.87   data arrival time

                  0.00   10.00   10.00   clock clk (rise edge)
                          0.00   10.00   clock network delay (ideal)
                          0.00   10.00   clock reconvergence pessimism
                                 10.00 ^ u_softmax/weights[80]$_DFF_P_/CK (DFF_X1)
                         -0.04    9.96   library setup time
                                  9.96   data required time
-----------------------------------------------------------------------------
                                  9.96   data required time
                                -61.87   data arrival time
-----------------------------------------------------------------------------
                                -51.91   slack (VIOLATED)



```

### Path 2

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_score32_w16_exact_div_split2/attention_dual_stream_composed_v1_hier_score32_w16_exact_div_split2/3_global_place.rpt`
- stage: `global_place`
- startpoint: `u_softmax/sum_weight_qq[12]$_DFF_P_`
- endpoint: `u_softmax/weights[80]$_DFF_P_`
- path_group: `clk`
- path_type: `max`
- slack: `-42.0600`
- data_arrival_time: `52.0200`
- data_required_time: `9.9600`

```text
Startpoint: u_softmax/sum_weight_qq[12]$_DFF_P_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: u_softmax/weights[80]$_DFF_P_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                  0.00    0.00    0.00 ^ u_softmax/sum_weight_qq[12]$_DFF_P_/CK (DFF_X2)
     2    3.04    0.01    0.09    0.09 v u_softmax/sum_weight_qq[12]$_DFF_P_/Q (DFF_X2)
                                         u_softmax/sum_weight_qq[12] (net)
                  0.01    0.00    0.09 v u_softmax/_164607_/A4 (NOR4_X1)
     1    2.24    0.05    0.08    0.17 ^ u_softmax/_164607_/ZN (NOR4_X1)
                                         u_softmax/_108448_ (net)
                  0.05    0.00    0.17 ^ place146192/A (BUF_X1)
     1    3.09    0.01    0.03    0.21 ^ place146192/Z (BUF_X1)
                                         net146191 (net)
                  0.01    0.00    0.21 ^ u_softmax/_164611_/A1 (NAND4_X2)
     2    8.20    0.02    0.03    0.24 v u_softmax/_164611_/ZN (NAND4_X2)
                                         u_softmax/_108452_ (net)
                  0.02    0.00    0.24 v u_softmax/_164612_/A4 (NOR4_X4)
...
                                 52.02   data arrival time

                  0.00   10.00   10.00   clock clk (rise edge)
                          0.00   10.00   clock network delay (ideal)
                          0.00   10.00   clock reconvergence pessimism
                                 10.00 ^ u_softmax/weights[80]$_DFF_P_/CK (DFF_X2)
                         -0.04    9.96   library setup time
                                  9.96   data required time
-----------------------------------------------------------------------------
                                  9.96   data required time
                                -52.02   data arrival time
-----------------------------------------------------------------------------
                                -42.06   slack (VIOLATED)



```

### Path 3

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_score32_w16_exact_div_split2/attention_dual_stream_composed_v1_hier_score32_w16_exact_div_split2/3_resizer.rpt`
- stage: `resizer`
- startpoint: `u_softmax/sum_weight_qq[12]$_DFF_P_`
- endpoint: `u_softmax/weights[80]$_DFF_P_`
- path_group: `clk`
- path_type: `max`
- slack: `-42.0600`
- data_arrival_time: `52.0200`
- data_required_time: `9.9600`

```text
Startpoint: u_softmax/sum_weight_qq[12]$_DFF_P_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: u_softmax/weights[80]$_DFF_P_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                  0.00    0.00    0.00 ^ u_softmax/sum_weight_qq[12]$_DFF_P_/CK (DFF_X2)
     2    3.04    0.01    0.09    0.09 v u_softmax/sum_weight_qq[12]$_DFF_P_/Q (DFF_X2)
                                         u_softmax/sum_weight_qq[12] (net)
                  0.01    0.00    0.09 v u_softmax/_164607_/A4 (NOR4_X1)
     1    2.24    0.05    0.08    0.17 ^ u_softmax/_164607_/ZN (NOR4_X1)
                                         u_softmax/_108448_ (net)
                  0.05    0.00    0.17 ^ place146192/A (BUF_X1)
     1    3.09    0.01    0.03    0.21 ^ place146192/Z (BUF_X1)
                                         net146191 (net)
                  0.01    0.00    0.21 ^ u_softmax/_164611_/A1 (NAND4_X2)
     2    8.20    0.02    0.03    0.24 v u_softmax/_164611_/ZN (NAND4_X2)
                                         u_softmax/_108452_ (net)
                  0.02    0.00    0.24 v u_softmax/_164612_/A4 (NOR4_X4)
...
                                 52.02   data arrival time

                  0.00   10.00   10.00   clock clk (rise edge)
                          0.00   10.00   clock network delay (ideal)
                          0.00   10.00   clock reconvergence pessimism
                                 10.00 ^ u_softmax/weights[80]$_DFF_P_/CK (DFF_X2)
                         -0.04    9.96   library setup time
                                  9.96   data required time
-----------------------------------------------------------------------------
                                  9.96   data required time
                                -52.02   data arrival time
-----------------------------------------------------------------------------
                                -42.06   slack (VIOLATED)



```

### Path 4

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_score32_w16_exact_div_split2/attention_dual_stream_composed_v1_hier_score32_w16_exact_div_split2/3_detailed_place.rpt`
- stage: `detailed_place`
- startpoint: `u_softmax/sum_weight_qq[12]$_DFF_P_`
- endpoint: `u_softmax/weights[16]$_DFF_P_`
- path_group: `clk`
- path_type: `max`
- slack: `-40.8200`
- data_arrival_time: `50.7800`
- data_required_time: `9.9600`

```text
Startpoint: u_softmax/sum_weight_qq[12]$_DFF_P_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: u_softmax/weights[16]$_DFF_P_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                  0.00    0.00    0.00 ^ u_softmax/sum_weight_qq[12]$_DFF_P_/CK (DFF_X2)
     2    2.91    0.01    0.09    0.09 v u_softmax/sum_weight_qq[12]$_DFF_P_/Q (DFF_X2)
                                         u_softmax/sum_weight_qq[12] (net)
                  0.01    0.00    0.09 v u_softmax/_164607_/A4 (NOR4_X1)
     1    1.73    0.04    0.08    0.17 ^ u_softmax/_164607_/ZN (NOR4_X1)
                                         u_softmax/_108448_ (net)
                  0.04    0.00    0.17 ^ place146192/A (BUF_X1)
     1    3.45    0.01    0.03    0.20 ^ place146192/Z (BUF_X1)
                                         net146191 (net)
                  0.01    0.00    0.20 ^ u_softmax/_164611_/A1 (NAND4_X2)
     2    8.17    0.02    0.03    0.24 v u_softmax/_164611_/ZN (NAND4_X2)
                                         u_softmax/_108452_ (net)
                  0.02    0.00    0.24 v u_softmax/_164612_/A4 (NOR4_X4)
...
                                 50.78   data arrival time

                  0.00   10.00   10.00   clock clk (rise edge)
                          0.00   10.00   clock network delay (ideal)
                          0.00   10.00   clock reconvergence pessimism
                                 10.00 ^ u_softmax/weights[16]$_DFF_P_/CK (DFF_X1)
                         -0.04    9.96   library setup time
                                  9.96   data required time
-----------------------------------------------------------------------------
                                  9.96   data required time
                                -50.78   data arrival time
-----------------------------------------------------------------------------
                                -40.82   slack (VIOLATED)



```

### Path 5

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_score32_w16_exact_div_split2/attention_dual_stream_composed_v1_hier_score32_w16_exact_div_split2/4_cts_final.rpt`
- stage: `cts`
- startpoint: `u_softmax/sum_weight_qq[12]$_DFF_P_`
- endpoint: `u_softmax/weights[48]$_DFF_P_`
- path_group: `clk`
- path_type: `max`
- slack: `-38.9800`
- data_arrival_time: `49.7500`
- data_required_time: `10.7700`

```text
Startpoint: u_softmax/sum_weight_qq[12]$_DFF_P_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: u_softmax/weights[48]$_DFF_P_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   74.44    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.03    0.03    0.03 ^ wire154982/A (BUF_X16)
     1   67.99    0.01    0.03    0.05 ^ wire154982/Z (BUF_X16)
                                         net154981 (net)
                  0.03    0.02    0.08 ^ wire154981/A (BUF_X16)
     1   79.50    0.01    0.03    0.11 ^ wire154981/Z (BUF_X16)
                                         net154980 (net)
                  0.04    0.03    0.14 ^ wire154980/A (BUF_X32)
     1   66.88    0.01    0.03    0.16 ^ wire154980/Z (BUF_X32)
                                         net154979 (net)
                  0.03    0.02    0.19 ^ clkbuf_0_clk/A (CLKBUF_X3)
     2   42.49    0.03    0.07    0.26 ^ clkbuf_0_clk/Z (CLKBUF_X3)
...
                                         clknet_6_49_0_clk (net)
                  0.05    0.01   10.76 ^ clkbuf_leaf_625_clk/A (CLKBUF_X3)
     3   11.84    0.01    0.05   10.81 ^ clkbuf_leaf_625_clk/Z (CLKBUF_X3)
                                         clknet_leaf_625_clk (net)
                  0.01    0.00   10.81 ^ u_softmax/weights[48]$_DFF_P_/CK (DFF_X1)
                          0.00   10.81   clock reconvergence pessimism
                         -0.04   10.77   library setup time
                                 10.77   data required time
-----------------------------------------------------------------------------
                                 10.77   data required time
                                -49.75   data arrival time
-----------------------------------------------------------------------------
                                -38.98   slack (VIOLATED)



```

### Path 6

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_score32_w16_exact_div_split2/attention_dual_stream_composed_v1_hier_score32_w16_exact_div_split2/5_global_route.rpt`
- stage: `route`
- startpoint: `u_softmax/sum_weight_qq[24]$_DFF_P_`
- endpoint: `u_softmax/weights[16]$_DFF_P_`
- path_group: `clk`
- path_type: `max`
- slack: `-38.5400`
- data_arrival_time: `49.2900`
- data_required_time: `10.7500`

```text
Startpoint: u_softmax/sum_weight_qq[24]$_DFF_P_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: u_softmax/weights[16]$_DFF_P_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   72.01    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.03    0.03    0.03 ^ wire154982/A (BUF_X16)
     1   67.73    0.01    0.03    0.05 ^ wire154982/Z (BUF_X16)
                                         net154981 (net)
                  0.03    0.03    0.08 ^ wire154981/A (BUF_X16)
     1   79.07    0.01    0.03    0.11 ^ wire154981/Z (BUF_X16)
                                         net154980 (net)
                  0.04    0.03    0.14 ^ wire154980/A (BUF_X32)
     1   66.53    0.01    0.03    0.17 ^ wire154980/Z (BUF_X32)
                                         net154979 (net)
                  0.03    0.02    0.19 ^ clkbuf_0_clk/A (CLKBUF_X3)
     2   42.97    0.03    0.07    0.26 ^ clkbuf_0_clk/Z (CLKBUF_X3)
...
                                         clknet_6_51_0_clk (net)
                  0.03    0.01   10.75 ^ clkbuf_leaf_616_clk/A (CLKBUF_X3)
     5    9.28    0.01    0.04   10.79 ^ clkbuf_leaf_616_clk/Z (CLKBUF_X3)
                                         clknet_leaf_616_clk (net)
                  0.01    0.00   10.79 ^ u_softmax/weights[16]$_DFF_P_/CK (DFF_X1)
                          0.00   10.79   clock reconvergence pessimism
                         -0.04   10.75   library setup time
                                 10.75   data required time
-----------------------------------------------------------------------------
                                 10.75   data required time
                                -49.29   data arrival time
-----------------------------------------------------------------------------
                                -38.54   slack (VIOLATED)



```

### Path 7

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_score32_w16_exact_div_split2/attention_dual_stream_composed_v1_hier_score32_w16_exact_div_split2/6_finish.rpt`
- stage: `finish`
- startpoint: `u_softmax/sum_weight_qq[32]$_DFF_P_`
- endpoint: `u_softmax/weights[16]$_DFF_P_`
- path_group: `clk`
- path_type: `max`
- slack: `-38.1700`
- data_arrival_time: `48.8500`
- data_required_time: `10.6800`

```text
Startpoint: u_softmax/sum_weight_qq[32]$_DFF_P_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: u_softmax/weights[16]$_DFF_P_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   49.83    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.02    0.02    0.02 ^ wire154982/A (BUF_X16)
     1   52.71    0.01    0.02    0.04 ^ wire154982/Z (BUF_X16)
                                         net154981 (net)
                  0.03    0.02    0.06 ^ wire154981/A (BUF_X16)
     1   65.35    0.01    0.03    0.09 ^ wire154981/Z (BUF_X16)
                                         net154980 (net)
                  0.04    0.03    0.12 ^ wire154980/A (BUF_X32)
     1   57.15    0.01    0.02    0.14 ^ wire154980/Z (BUF_X32)
                                         net154979 (net)
                  0.03    0.02    0.17 ^ clkbuf_0_clk/A (CLKBUF_X3)
     2   34.07    0.03    0.06    0.23 ^ clkbuf_0_clk/Z (CLKBUF_X3)
...
                                         clknet_6_51_0_clk (net)
                  0.04    0.01   10.68 ^ clkbuf_leaf_616_clk/A (CLKBUF_X3)
     5    8.93    0.01    0.04   10.72 ^ clkbuf_leaf_616_clk/Z (CLKBUF_X3)
                                         clknet_leaf_616_clk (net)
                  0.01    0.00   10.72 ^ u_softmax/weights[16]$_DFF_P_/CK (DFF_X1)
                          0.00   10.72   clock reconvergence pessimism
                         -0.04   10.68   library setup time
                                 10.68   data required time
-----------------------------------------------------------------------------
                                 10.68   data required time
                                -48.85   data arrival time
-----------------------------------------------------------------------------
                                -38.17   slack (VIOLATED)



```

### Path 8

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_score32_w16_exact_div_split2/attention_dual_stream_composed_v1_hier_score32_w16_exact_div_split2/6_finish.rpt`
- stage: `finish`
- startpoint: `stream_buf_0_pipe_3[709]$_DFF_PN0_`
- endpoint: `stream_buf_0_pipe_3[741]$_DFF_PN0_`
- path_group: `clk`
- path_type: `min`
- slack: `0.0300`
- data_arrival_time: `0.8500`
- data_required_time: `0.8300`

```text
Startpoint: stream_buf_0_pipe_3[709]$_DFF_PN0_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: stream_buf_0_pipe_3[741]$_DFF_PN0_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   49.83    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.02    0.02    0.02 ^ wire154982/A (BUF_X16)
     1   52.71    0.01    0.02    0.04 ^ wire154982/Z (BUF_X16)
                                         net154981 (net)
                  0.03    0.02    0.06 ^ wire154981/A (BUF_X16)
     1   65.35    0.01    0.03    0.09 ^ wire154981/Z (BUF_X16)
                                         net154980 (net)
                  0.04    0.03    0.12 ^ wire154980/A (BUF_X32)
     1   57.15    0.01    0.02    0.14 ^ wire154980/Z (BUF_X32)
                                         net154979 (net)
                  0.03    0.02    0.17 ^ clkbuf_0_clk/A (CLKBUF_X3)
     2   34.07    0.03    0.06    0.23 ^ clkbuf_0_clk/Z (CLKBUF_X3)
...
                                         clknet_6_34_0_clk (net)
                  0.07    0.00    0.77 ^ clkbuf_leaf_212_clk/A (CLKBUF_X3)
     5    9.63    0.01    0.05    0.82 ^ clkbuf_leaf_212_clk/Z (CLKBUF_X3)
                                         clknet_leaf_212_clk (net)
                  0.01    0.00    0.82 ^ stream_buf_0_pipe_3[741]$_DFF_PN0_/CK (DFFR_X1)
                          0.00    0.82   clock reconvergence pessimism
                          0.00    0.83   library hold time
                                  0.83   data required time
-----------------------------------------------------------------------------
                                  0.83   data required time
                                 -0.85   data arrival time
-----------------------------------------------------------------------------
                                  0.03   slack (MET)



```
