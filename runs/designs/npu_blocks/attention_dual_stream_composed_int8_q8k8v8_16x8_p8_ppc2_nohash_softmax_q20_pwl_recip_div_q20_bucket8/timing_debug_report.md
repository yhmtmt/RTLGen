# OpenROAD Timing Debug Summary

- design_dir: `runs/designs/npu_blocks/attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_softmax_q20_pwl_recip_div_q20_bucket8`
- metrics_path: `runs/designs/npu_blocks/attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_softmax_q20_pwl_recip_div_q20_bucket8/metrics.csv`
- rows_considered: 2

## Metrics Rows

| param_hash | tag | status | critical_path_ns | density | result_path |
| --- | --- | --- | ---: | ---: | --- |
| 4696b67c | attention_dual_stream_composed_v1_hier_q20_pwl_recip_div | ok | 50.5545 | 0.3 | `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_softmax_q20_pwl_recip_div_q20_bucket8/attention_dual_stream_composed_v1_hier_q20_pwl_recip_div/6_finish.rpt` |
| add1d6b2 | attention_dual_stream_composed_v1_hier_q20_pwl_recip_div | ok | 50.8085 | 0.4 | `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_softmax_q20_pwl_recip_div_q20_bucket8/attention_dual_stream_composed_v1_hier_q20_pwl_recip_div/6_finish.rpt` |

## Inspected Report Files

- `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_softmax_q20_pwl_recip_div_q20_bucket8/attention_dual_stream_composed_v1_hier_q20_pwl_recip_div/6_finish.rpt`
- `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_softmax_q20_pwl_recip_div_q20_bucket8/attention_dual_stream_composed_v1_hier_q20_pwl_recip_div/5_global_route.rpt`
- `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_softmax_q20_pwl_recip_div_q20_bucket8/attention_dual_stream_composed_v1_hier_q20_pwl_recip_div/5_route_drc.rpt`
- `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_softmax_q20_pwl_recip_div_q20_bucket8/attention_dual_stream_composed_v1_hier_q20_pwl_recip_div/5_route_drc.rpt-5.rpt`
- `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_softmax_q20_pwl_recip_div_q20_bucket8/attention_dual_stream_composed_v1_hier_q20_pwl_recip_div/4_cts_final.rpt`
- `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_softmax_q20_pwl_recip_div_q20_bucket8/attention_dual_stream_composed_v1_hier_q20_pwl_recip_div/3_resizer.rpt`
- `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_softmax_q20_pwl_recip_div_q20_bucket8/attention_dual_stream_composed_v1_hier_q20_pwl_recip_div/3_detailed_place.rpt`
- `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_softmax_q20_pwl_recip_div_q20_bucket8/attention_dual_stream_composed_v1_hier_q20_pwl_recip_div/3_global_place.rpt`
- `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_softmax_q20_pwl_recip_div_q20_bucket8/attention_dual_stream_composed_v1_hier_q20_pwl_recip_div/2_floorplan_final.rpt`
- `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_softmax_q20_pwl_recip_div_q20_bucket8/attention_dual_stream_composed_v1_hier_q20_pwl_recip_div/drt_antennas.log`
- `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_softmax_q20_pwl_recip_div_q20_bucket8/attention_dual_stream_composed_v1_hier_q20_pwl_recip_div/grt_antennas.log`
- `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_softmax_q20_pwl_recip_div_q20_bucket8/attention_dual_stream_composed_v1_hier_q20_pwl_recip_div/metadata-generate.log`

## Preferred Final-Stage Timing Paths

- raw_path_block_count: 104
- unique_path_block_count: 28
- preferred_stage: `finish`

### Path 1

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_softmax_q20_pwl_recip_div_q20_bucket8/attention_dual_stream_composed_v1_hier_q20_pwl_recip_div/6_finish.rpt`
- stage: `finish`
- startpoint: `softmax_scores_pipe_0[22]$_DFF_PN0_`
- endpoint: `u_softmax/weights[121]$_SDFF_PN1_`
- path_group: `clk`
- path_type: `max`
- slack: `-40.2300`
- data_arrival_time: `50.8100`
- data_required_time: `10.5800`

```text
Startpoint: softmax_scores_pipe_0[22]$_DFF_PN0_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: u_softmax/weights[121]$_SDFF_PN1_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   34.97    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.01    0.01    0.01 ^ wire142020/A (BUF_X8)
     1   49.18    0.01    0.02    0.03 ^ wire142020/Z (BUF_X8)
                                         net142019 (net)
                  0.03    0.02    0.05 ^ wire142019/A (BUF_X16)
     1   69.33    0.01    0.03    0.08 ^ wire142019/Z (BUF_X16)
                                         net142018 (net)
                  0.04    0.03    0.11 ^ clkbuf_0_clk/A (CLKBUF_X3)
     2   17.57    0.02    0.05    0.17 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.02    0.00    0.17 ^ clkbuf_1_1_0_clk/A (CLKBUF_X3)
     1   27.63    0.02    0.05    0.22 ^ clkbuf_1_1_0_clk/Z (CLKBUF_X3)
...
                                         net142022 (net)
                  0.02    0.01   10.58 ^ clkbuf_leaf_1_clk/A (CLKBUF_X3)
     8    9.90    0.01    0.04   10.62 ^ clkbuf_leaf_1_clk/Z (CLKBUF_X3)
                                         clknet_leaf_1_clk (net)
                  0.01    0.00   10.62 ^ u_softmax/weights[121]$_SDFF_PN1_/CK (DFF_X2)
                          0.00   10.62   clock reconvergence pessimism
                         -0.04   10.58   library setup time
                                 10.58   data required time
-----------------------------------------------------------------------------
                                 10.58   data required time
                                -50.81   data arrival time
-----------------------------------------------------------------------------
                                -40.23   slack (VIOLATED)



```

### Path 2

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_softmax_q20_pwl_recip_div_q20_bucket8/attention_dual_stream_composed_v1_hier_q20_pwl_recip_div/6_finish.rpt`
- stage: `finish`
- startpoint: `stream_buf_1_pipe_1[504]$_DFF_PN0_`
- endpoint: `stream_buf_1_pipe_1[536]$_DFF_PN0_`
- path_group: `clk`
- path_type: `min`
- slack: `0.0300`
- data_arrival_time: `0.7300`
- data_required_time: `0.7000`

```text
Startpoint: stream_buf_1_pipe_1[504]$_DFF_PN0_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: stream_buf_1_pipe_1[536]$_DFF_PN0_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   34.97    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.01    0.01    0.01 ^ wire142020/A (BUF_X8)
     1   49.18    0.01    0.02    0.03 ^ wire142020/Z (BUF_X8)
                                         net142019 (net)
                  0.03    0.02    0.05 ^ wire142019/A (BUF_X16)
     1   69.33    0.01    0.03    0.08 ^ wire142019/Z (BUF_X16)
                                         net142018 (net)
                  0.04    0.03    0.11 ^ clkbuf_0_clk/A (CLKBUF_X3)
     2   17.57    0.02    0.05    0.17 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.02    0.00    0.17 ^ clkbuf_1_1_0_clk/A (CLKBUF_X3)
     1   27.63    0.02    0.05    0.22 ^ clkbuf_1_1_0_clk/Z (CLKBUF_X3)
...
                                         clknet_5_22_0_clk (net)
                  0.09    0.02    0.64 ^ clkbuf_leaf_154_clk/A (CLKBUF_X3)
     5    8.96    0.01    0.06    0.70 ^ clkbuf_leaf_154_clk/Z (CLKBUF_X3)
                                         clknet_leaf_154_clk (net)
                  0.01    0.00    0.70 ^ stream_buf_1_pipe_1[536]$_DFF_PN0_/CK (DFFR_X2)
                          0.00    0.70   clock reconvergence pessimism
                          0.00    0.70   library hold time
                                  0.70   data required time
-----------------------------------------------------------------------------
                                  0.70   data required time
                                 -0.73   data arrival time
-----------------------------------------------------------------------------
                                  0.03   slack (MET)



```

### Path 3

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_softmax_q20_pwl_recip_div_q20_bucket8/attention_dual_stream_composed_v1_hier_q20_pwl_recip_div/6_finish.rpt`
- stage: `finish`
- startpoint: `rst_n (input port clocked by clk)`
- endpoint: `stream_buf_0_pipe_1[878]$_DFF_PN0_`
- path_group: `asynchronous`
- path_type: `min`
- slack: `1.0800`
- data_arrival_time: `2.1200`
- data_required_time: `1.0400`

```text
Startpoint: rst_n (input port clocked by clk)
Endpoint: stream_buf_0_pipe_1[878]$_DFF_PN0_
          (removal check against rising-edge clock clk)
Path Group: asynchronous
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (propagated)
                          2.00    2.00 ^ input external delay
     1    7.11    0.00    0.00    2.00 ^ rst_n (in)
                                         rst_n (net)
                  0.00    0.00    2.00 ^ input3673/A (CLKBUF_X3)
     5   75.19    0.02    0.04    2.04 ^ input3673/Z (CLKBUF_X3)
                                         net3672 (net)
                  0.11    0.08    2.12 ^ stream_buf_0_pipe_1[878]$_DFF_PN0_/RN (DFFR_X1)
                                  2.12   data arrival time

                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   34.97    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.01    0.01    0.01 ^ wire142020/A (BUF_X8)
...
                                         clknet_3_5_1_clk (net)
                  0.03    0.00    0.49 ^ clkbuf_5_21_0_clk/A (CLKBUF_X3)
    27  154.67    0.11    0.15    0.64 ^ clkbuf_5_21_0_clk/Z (CLKBUF_X3)
                                         clknet_5_21_0_clk (net)
                  0.12    0.03    0.67 ^ clkbuf_leaf_196_clk/A (CLKBUF_X3)
     5    9.86    0.02    0.06    0.73 ^ clkbuf_leaf_196_clk/Z (CLKBUF_X3)
                                         clknet_leaf_196_clk (net)
                  0.02    0.00    0.73 ^ stream_buf_0_pipe_1[878]$_DFF_PN0_/CK (DFFR_X1)
                          0.00    0.73   clock reconvergence pessimism
                          0.32    1.04   library removal time
                                  1.04   data required time
-----------------------------------------------------------------------------
                                  1.04   data required time
                                 -2.12   data arrival time
-----------------------------------------------------------------------------
                                  1.08   slack (MET)
```

### Path 4

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_softmax_q20_pwl_recip_div_q20_bucket8/attention_dual_stream_composed_v1_hier_q20_pwl_recip_div/6_finish.rpt`
- stage: `finish`
- startpoint: `rst_n (input port clocked by clk)`
- endpoint: `value_accum_0_out[38]$_DFFE_PN0P_`
- path_group: `asynchronous`
- path_type: `max`
- slack: `7.6900`
- data_arrival_time: `2.9200`
- data_required_time: `10.6100`

```text
Startpoint: rst_n (input port clocked by clk)
Endpoint: value_accum_0_out[38]$_DFFE_PN0P_
          (recovery check against rising-edge clock clk)
Path Group: asynchronous
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (propagated)
                          2.00    2.00 ^ input external delay
     1    7.11    0.00    0.00    2.00 ^ rst_n (in)
                                         rst_n (net)
                  0.00    0.00    2.00 ^ input3673/A (CLKBUF_X3)
     5   75.19    0.02    0.04    2.04 ^ input3673/Z (CLKBUF_X3)
                                         net3672 (net)
                  0.12    0.09    2.13 ^ place141860/A (BUF_X1)
     2    5.47    0.02    0.04    2.18 ^ place141860/Z (BUF_X1)
                                         net141859 (net)
                  0.02    0.00    2.18 ^ place141866/A (BUF_X1)
     4   52.03    0.11    0.14    2.31 ^ place141866/Z (BUF_X1)
                                         net141865 (net)
                  0.12    0.02    2.33 ^ place141894/A (BUF_X2)
     2   26.09    0.03    0.06    2.39 ^ place141894/Z (BUF_X2)
...
                                         clknet_3_1_1_clk (net)
                  0.03    0.00   10.45 ^ clkbuf_5_5_0_clk/A (CLKBUF_X3)
    13   41.27    0.03    0.07   10.51 ^ clkbuf_5_5_0_clk/Z (CLKBUF_X3)
                                         clknet_5_5_0_clk (net)
                  0.03    0.00   10.52 ^ clkbuf_leaf_378_clk/A (CLKBUF_X3)
     7    9.27    0.01    0.04   10.56 ^ clkbuf_leaf_378_clk/Z (CLKBUF_X3)
                                         clknet_leaf_378_clk (net)
                  0.01    0.00   10.56 ^ value_accum_0_out[38]$_DFFE_PN0P_/CK (DFFR_X1)
                          0.00   10.56   clock reconvergence pessimism
                          0.05   10.61   library recovery time
                                 10.61   data required time
-----------------------------------------------------------------------------
                                 10.61   data required time
                                 -2.92   data arrival time
-----------------------------------------------------------------------------
                                  7.69   slack (MET)
```


## Worst Timing Paths Across All Stages

### Path 1

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_softmax_q20_pwl_recip_div_q20_bucket8/attention_dual_stream_composed_v1_hier_q20_pwl_recip_div/2_floorplan_final.rpt`
- stage: `floorplan`
- startpoint: `softmax_scores_pipe_0[21]$_DFF_PN0_`
- endpoint: `u_softmax/weights[40]$_SDFF_PN1_`
- path_group: `clk`
- path_type: `max`
- slack: `-46.9000`
- data_arrival_time: `56.8600`
- data_required_time: `9.9600`

```text
Startpoint: softmax_scores_pipe_0[21]$_DFF_PN0_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: u_softmax/weights[40]$_SDFF_PN1_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                  0.00    0.00    0.00 ^ softmax_scores_pipe_0[21]$_DFF_PN0_/CK (DFFR_X1)
     4    9.84    0.03    0.12    0.12 ^ softmax_scores_pipe_0[21]$_DFF_PN0_/Q (DFFR_X1)
                                         softmax_scores_pipe_0[21] (net)
                  0.03    0.00    0.12 ^ u_softmax/_313873_/B (HA_X1)
     2    2.58    0.03    0.05    0.17 ^ u_softmax/_313873_/S (HA_X1)
                                         u_softmax/_048401_ (net)
                  0.03    0.00    0.17 ^ u_softmax/_171113_/B2 (AOI21_X1)
     1    1.46    0.01    0.02    0.19 v u_softmax/_171113_/ZN (AOI21_X1)
                                         u_softmax/_113912_ (net)
                  0.01    0.00    0.19 v u_softmax/_171115_/B1 (OAI21_X1)
     1    1.65    0.02    0.03    0.22 ^ u_softmax/_171115_/ZN (OAI21_X1)
                                         u_softmax/_113914_ (net)
                  0.02    0.00    0.22 ^ u_softmax/_171116_/B1 (AOI21_X1)
...
                                 56.86   data arrival time

                  0.00   10.00   10.00   clock clk (rise edge)
                          0.00   10.00   clock network delay (ideal)
                          0.00   10.00   clock reconvergence pessimism
                                 10.00 ^ u_softmax/weights[40]$_SDFF_PN1_/CK (DFF_X1)
                         -0.04    9.96   library setup time
                                  9.96   data required time
-----------------------------------------------------------------------------
                                  9.96   data required time
                                -56.86   data arrival time
-----------------------------------------------------------------------------
                                -46.90   slack (VIOLATED)



```

### Path 2

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_softmax_q20_pwl_recip_div_q20_bucket8/attention_dual_stream_composed_v1_hier_q20_pwl_recip_div/3_global_place.rpt`
- stage: `global_place`
- startpoint: `softmax_scores_pipe_0[2]$_DFF_PN0_`
- endpoint: `u_softmax/weights[73]$_SDFF_PN1_`
- path_group: `clk`
- path_type: `max`
- slack: `-42.3500`
- data_arrival_time: `52.3100`
- data_required_time: `9.9600`

```text
Startpoint: softmax_scores_pipe_0[2]$_DFF_PN0_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: u_softmax/weights[73]$_SDFF_PN1_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                  0.00    0.00    0.00 ^ softmax_scores_pipe_0[2]$_DFF_PN0_/CK (DFFR_X1)
     2    3.66    0.01    0.09    0.09 v softmax_scores_pipe_0[2]$_DFF_PN0_/Q (DFFR_X1)
                                         softmax_scores_pipe_0[2] (net)
                  0.01    0.00    0.09 v u_softmax/_171177_/A (INV_X1)
     2    5.28    0.01    0.02    0.11 ^ u_softmax/_171177_/ZN (INV_X1)
                                         u_softmax/_048396_ (net)
                  0.01    0.00    0.11 ^ u_softmax/_313872_/B (HA_X1)
     2    4.19    0.03    0.06    0.17 ^ u_softmax/_313872_/S (HA_X1)
                                         u_softmax/_048398_ (net)
                  0.03    0.00    0.17 ^ u_softmax/_171114_/A (INV_X1)
     1    2.50    0.01    0.01    0.18 v u_softmax/_171114_/ZN (INV_X1)
                                         u_softmax/_113913_ (net)
                  0.01    0.00    0.18 v u_softmax/_171115_/B2 (OAI21_X1)
...
                                 52.31   data arrival time

                  0.00   10.00   10.00   clock clk (rise edge)
                          0.00   10.00   clock network delay (ideal)
                          0.00   10.00   clock reconvergence pessimism
                                 10.00 ^ u_softmax/weights[73]$_SDFF_PN1_/CK (DFF_X1)
                         -0.04    9.96   library setup time
                                  9.96   data required time
-----------------------------------------------------------------------------
                                  9.96   data required time
                                -52.31   data arrival time
-----------------------------------------------------------------------------
                                -42.35   slack (VIOLATED)



```

### Path 3

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_softmax_q20_pwl_recip_div_q20_bucket8/attention_dual_stream_composed_v1_hier_q20_pwl_recip_div/3_resizer.rpt`
- stage: `resizer`
- startpoint: `softmax_scores_pipe_0[2]$_DFF_PN0_`
- endpoint: `u_softmax/weights[73]$_SDFF_PN1_`
- path_group: `clk`
- path_type: `max`
- slack: `-42.3500`
- data_arrival_time: `52.3100`
- data_required_time: `9.9600`

```text
Startpoint: softmax_scores_pipe_0[2]$_DFF_PN0_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: u_softmax/weights[73]$_SDFF_PN1_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                  0.00    0.00    0.00 ^ softmax_scores_pipe_0[2]$_DFF_PN0_/CK (DFFR_X1)
     2    3.66    0.01    0.09    0.09 v softmax_scores_pipe_0[2]$_DFF_PN0_/Q (DFFR_X1)
                                         softmax_scores_pipe_0[2] (net)
                  0.01    0.00    0.09 v u_softmax/_171177_/A (INV_X1)
     2    5.28    0.01    0.02    0.11 ^ u_softmax/_171177_/ZN (INV_X1)
                                         u_softmax/_048396_ (net)
                  0.01    0.00    0.11 ^ u_softmax/_313872_/B (HA_X1)
     2    4.19    0.03    0.06    0.17 ^ u_softmax/_313872_/S (HA_X1)
                                         u_softmax/_048398_ (net)
                  0.03    0.00    0.17 ^ u_softmax/_171114_/A (INV_X1)
     1    2.50    0.01    0.01    0.18 v u_softmax/_171114_/ZN (INV_X1)
                                         u_softmax/_113913_ (net)
                  0.01    0.00    0.18 v u_softmax/_171115_/B2 (OAI21_X1)
...
                                 52.31   data arrival time

                  0.00   10.00   10.00   clock clk (rise edge)
                          0.00   10.00   clock network delay (ideal)
                          0.00   10.00   clock reconvergence pessimism
                                 10.00 ^ u_softmax/weights[73]$_SDFF_PN1_/CK (DFF_X1)
                         -0.04    9.96   library setup time
                                  9.96   data required time
-----------------------------------------------------------------------------
                                  9.96   data required time
                                -52.31   data arrival time
-----------------------------------------------------------------------------
                                -42.35   slack (VIOLATED)



```

### Path 4

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_softmax_q20_pwl_recip_div_q20_bucket8/attention_dual_stream_composed_v1_hier_q20_pwl_recip_div/3_detailed_place.rpt`
- stage: `detailed_place`
- startpoint: `softmax_scores_pipe_0[22]$_DFF_PN0_`
- endpoint: `u_softmax/weights[73]$_SDFF_PN1_`
- path_group: `clk`
- path_type: `max`
- slack: `-41.8500`
- data_arrival_time: `51.8000`
- data_required_time: `9.9600`

```text
Startpoint: softmax_scores_pipe_0[22]$_DFF_PN0_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: u_softmax/weights[73]$_SDFF_PN1_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                  0.00    0.00    0.00 ^ softmax_scores_pipe_0[22]$_DFF_PN0_/CK (DFFR_X1)
     2    4.90    0.02    0.11    0.11 ^ softmax_scores_pipe_0[22]$_DFF_PN0_/Q (DFFR_X1)
                                         softmax_scores_pipe_0[22] (net)
                  0.02    0.00    0.11 ^ u_softmax/_313872_/A (HA_X1)
     2    3.72    0.03    0.06    0.17 ^ u_softmax/_313872_/S (HA_X1)
                                         u_softmax/_048398_ (net)
                  0.03    0.00    0.17 ^ u_softmax/_171114_/A (INV_X1)
     1    2.12    0.01    0.01    0.18 v u_softmax/_171114_/ZN (INV_X1)
                                         u_softmax/_113913_ (net)
                  0.01    0.00    0.18 v u_softmax/_171115_/B2 (OAI21_X1)
     1    1.83    0.02    0.03    0.21 ^ u_softmax/_171115_/ZN (OAI21_X1)
                                         u_softmax/_113914_ (net)
                  0.02    0.00    0.21 ^ u_softmax/_171116_/B1 (AOI21_X1)
...
                                 51.80   data arrival time

                  0.00   10.00   10.00   clock clk (rise edge)
                          0.00   10.00   clock network delay (ideal)
                          0.00   10.00   clock reconvergence pessimism
                                 10.00 ^ u_softmax/weights[73]$_SDFF_PN1_/CK (DFF_X1)
                         -0.04    9.96   library setup time
                                  9.96   data required time
-----------------------------------------------------------------------------
                                  9.96   data required time
                                -51.80   data arrival time
-----------------------------------------------------------------------------
                                -41.85   slack (VIOLATED)



```

### Path 5

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_softmax_q20_pwl_recip_div_q20_bucket8/attention_dual_stream_composed_v1_hier_q20_pwl_recip_div/5_global_route.rpt`
- stage: `route`
- startpoint: `softmax_scores_pipe_0[21]$_DFF_PN0_`
- endpoint: `u_softmax/weights[121]$_SDFF_PN1_`
- path_group: `clk`
- path_type: `max`
- slack: `-40.5500`
- data_arrival_time: `51.1600`
- data_required_time: `10.6200`

```text
Startpoint: softmax_scores_pipe_0[21]$_DFF_PN0_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: u_softmax/weights[121]$_SDFF_PN1_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   50.62    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.01    0.01    0.01 ^ wire142020/A (BUF_X8)
     1   52.36    0.01    0.03    0.04 ^ wire142020/Z (BUF_X8)
                                         net142019 (net)
                  0.02    0.02    0.06 ^ wire142019/A (BUF_X16)
     1   67.90    0.01    0.03    0.08 ^ wire142019/Z (BUF_X16)
                                         net142018 (net)
                  0.03    0.03    0.11 ^ clkbuf_0_clk/A (CLKBUF_X3)
     2   22.97    0.02    0.05    0.17 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.02    0.00    0.17 ^ clkbuf_1_1_0_clk/A (CLKBUF_X3)
     1   27.88    0.02    0.05    0.22 ^ clkbuf_1_1_0_clk/Z (CLKBUF_X3)
...
                                         net142022 (net)
                  0.02    0.01   10.61 ^ clkbuf_leaf_1_clk/A (CLKBUF_X3)
     8   10.28    0.01    0.04   10.66 ^ clkbuf_leaf_1_clk/Z (CLKBUF_X3)
                                         clknet_leaf_1_clk (net)
                  0.01    0.00   10.66 ^ u_softmax/weights[121]$_SDFF_PN1_/CK (DFF_X2)
                          0.00   10.66   clock reconvergence pessimism
                         -0.04   10.62   library setup time
                                 10.62   data required time
-----------------------------------------------------------------------------
                                 10.62   data required time
                                -51.16   data arrival time
-----------------------------------------------------------------------------
                                -40.55   slack (VIOLATED)



```

### Path 6

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_softmax_q20_pwl_recip_div_q20_bucket8/attention_dual_stream_composed_v1_hier_q20_pwl_recip_div/6_finish.rpt`
- stage: `finish`
- startpoint: `softmax_scores_pipe_0[22]$_DFF_PN0_`
- endpoint: `u_softmax/weights[121]$_SDFF_PN1_`
- path_group: `clk`
- path_type: `max`
- slack: `-40.2300`
- data_arrival_time: `50.8100`
- data_required_time: `10.5800`

```text
Startpoint: softmax_scores_pipe_0[22]$_DFF_PN0_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: u_softmax/weights[121]$_SDFF_PN1_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   34.97    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.01    0.01    0.01 ^ wire142020/A (BUF_X8)
     1   49.18    0.01    0.02    0.03 ^ wire142020/Z (BUF_X8)
                                         net142019 (net)
                  0.03    0.02    0.05 ^ wire142019/A (BUF_X16)
     1   69.33    0.01    0.03    0.08 ^ wire142019/Z (BUF_X16)
                                         net142018 (net)
                  0.04    0.03    0.11 ^ clkbuf_0_clk/A (CLKBUF_X3)
     2   17.57    0.02    0.05    0.17 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.02    0.00    0.17 ^ clkbuf_1_1_0_clk/A (CLKBUF_X3)
     1   27.63    0.02    0.05    0.22 ^ clkbuf_1_1_0_clk/Z (CLKBUF_X3)
...
                                         net142022 (net)
                  0.02    0.01   10.58 ^ clkbuf_leaf_1_clk/A (CLKBUF_X3)
     8    9.90    0.01    0.04   10.62 ^ clkbuf_leaf_1_clk/Z (CLKBUF_X3)
                                         clknet_leaf_1_clk (net)
                  0.01    0.00   10.62 ^ u_softmax/weights[121]$_SDFF_PN1_/CK (DFF_X2)
                          0.00   10.62   clock reconvergence pessimism
                         -0.04   10.58   library setup time
                                 10.58   data required time
-----------------------------------------------------------------------------
                                 10.58   data required time
                                -50.81   data arrival time
-----------------------------------------------------------------------------
                                -40.23   slack (VIOLATED)



```

### Path 7

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_softmax_q20_pwl_recip_div_q20_bucket8/attention_dual_stream_composed_v1_hier_q20_pwl_recip_div/4_cts_final.rpt`
- stage: `cts`
- startpoint: `softmax_scores_pipe_0[22]$_DFF_PN0_`
- endpoint: `u_softmax/weights[0]$_SDFF_PN1_`
- path_group: `clk`
- path_type: `max`
- slack: `-40.2100`
- data_arrival_time: `50.7400`
- data_required_time: `10.5300`

```text
Startpoint: softmax_scores_pipe_0[22]$_DFF_PN0_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: u_softmax/weights[0]$_SDFF_PN1_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   50.54    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.01    0.01    0.01 ^ wire142020/A (BUF_X8)
     1   52.13    0.01    0.03    0.04 ^ wire142020/Z (BUF_X8)
                                         net142019 (net)
                  0.02    0.02    0.06 ^ wire142019/A (BUF_X16)
     1   67.88    0.01    0.03    0.09 ^ wire142019/Z (BUF_X16)
                                         net142018 (net)
                  0.03    0.02    0.11 ^ clkbuf_0_clk/A (CLKBUF_X3)
     2   22.79    0.02    0.05    0.16 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.02    0.00    0.17 ^ clkbuf_1_1_0_clk/A (CLKBUF_X3)
     1   27.66    0.02    0.05    0.22 ^ clkbuf_1_1_0_clk/Z (CLKBUF_X3)
...
                                         clknet_3_6_1_clk (net)
                  0.03    0.00   10.48 ^ clkbuf_5_27_0_clk/A (CLKBUF_X3)
     9   55.87    0.04    0.08   10.55 ^ clkbuf_5_27_0_clk/Z (CLKBUF_X3)
                                         clknet_5_27_0_clk (net)
                  0.04    0.00   10.56 ^ u_softmax/weights[0]$_SDFF_PN1_/CK (DFF_X2)
                          0.00   10.56   clock reconvergence pessimism
                         -0.03   10.53   library setup time
                                 10.53   data required time
-----------------------------------------------------------------------------
                                 10.53   data required time
                                -50.74   data arrival time
-----------------------------------------------------------------------------
                                -40.21   slack (VIOLATED)



```

### Path 8

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_softmax_q20_pwl_recip_div_q20_bucket8/attention_dual_stream_composed_v1_hier_q20_pwl_recip_div/4_cts_final.rpt`
- stage: `cts`
- startpoint: `stream_buf_1_pipe_1[504]$_DFF_PN0_`
- endpoint: `stream_buf_1_pipe_1[536]$_DFF_PN0_`
- path_group: `clk`
- path_type: `min`
- slack: `0.0300`
- data_arrival_time: `0.7000`
- data_required_time: `0.6700`

```text
Startpoint: stream_buf_1_pipe_1[504]$_DFF_PN0_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: stream_buf_1_pipe_1[536]$_DFF_PN0_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   50.54    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.01    0.01    0.01 ^ wire142020/A (BUF_X8)
     1   52.13    0.01    0.03    0.04 ^ wire142020/Z (BUF_X8)
                                         net142019 (net)
                  0.02    0.02    0.06 ^ wire142019/A (BUF_X16)
     1   67.88    0.01    0.03    0.09 ^ wire142019/Z (BUF_X16)
                                         net142018 (net)
                  0.03    0.02    0.11 ^ clkbuf_0_clk/A (CLKBUF_X3)
     2   22.79    0.02    0.05    0.16 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.02    0.00    0.17 ^ clkbuf_1_1_0_clk/A (CLKBUF_X3)
     1   27.66    0.02    0.05    0.22 ^ clkbuf_1_1_0_clk/Z (CLKBUF_X3)
...
                                         clknet_5_22_0_clk (net)
                  0.08    0.01    0.61 ^ clkbuf_leaf_154_clk/A (CLKBUF_X3)
     5    8.80    0.01    0.06    0.67 ^ clkbuf_leaf_154_clk/Z (CLKBUF_X3)
                                         clknet_leaf_154_clk (net)
                  0.01    0.00    0.67 ^ stream_buf_1_pipe_1[536]$_DFF_PN0_/CK (DFFR_X2)
                          0.00    0.67   clock reconvergence pessimism
                          0.00    0.67   library hold time
                                  0.67   data required time
-----------------------------------------------------------------------------
                                  0.67   data required time
                                 -0.70   data arrival time
-----------------------------------------------------------------------------
                                  0.03   slack (MET)



```
