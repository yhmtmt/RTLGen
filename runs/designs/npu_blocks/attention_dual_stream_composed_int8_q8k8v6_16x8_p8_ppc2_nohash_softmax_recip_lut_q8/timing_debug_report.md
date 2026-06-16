# OpenROAD Timing Debug Summary

- design_dir: `runs/designs/npu_blocks/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2_nohash_softmax_recip_lut_q8`
- metrics_path: `runs/designs/npu_blocks/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2_nohash_softmax_recip_lut_q8/metrics.csv`
- rows_considered: 2

## Metrics Rows

| param_hash | tag | status | critical_path_ns | density | result_path |
| --- | --- | --- | ---: | ---: | --- |
| c6a1179a | attention_dual_stream_composed_v1_hier | ok | 7.7655 | 0.4 | `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2_nohash_softmax_recip_lut_q8/attention_dual_stream_composed_v1_hier/6_finish.rpt` |
| e9e34269 | attention_dual_stream_composed_v1_hier | ok | 8.0334 | 0.3 | `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2_nohash_softmax_recip_lut_q8/attention_dual_stream_composed_v1_hier/6_finish.rpt` |

## Inspected Report Files

- `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2_nohash_softmax_recip_lut_q8/attention_dual_stream_composed_v1_hier/6_finish.rpt`
- `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2_nohash_softmax_recip_lut_q8/attention_dual_stream_composed_v1_hier/5_global_route.rpt`
- `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2_nohash_softmax_recip_lut_q8/attention_dual_stream_composed_v1_hier/5_route_drc.rpt`
- `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2_nohash_softmax_recip_lut_q8/attention_dual_stream_composed_v1_hier/5_route_drc.rpt-5.rpt`
- `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2_nohash_softmax_recip_lut_q8/attention_dual_stream_composed_v1_hier/4_cts_final.rpt`
- `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2_nohash_softmax_recip_lut_q8/attention_dual_stream_composed_v1_hier/3_resizer.rpt`
- `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2_nohash_softmax_recip_lut_q8/attention_dual_stream_composed_v1_hier/3_detailed_place.rpt`
- `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2_nohash_softmax_recip_lut_q8/attention_dual_stream_composed_v1_hier/3_global_place.rpt`
- `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2_nohash_softmax_recip_lut_q8/attention_dual_stream_composed_v1_hier/2_floorplan_final.rpt`
- `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2_nohash_softmax_recip_lut_q8/attention_dual_stream_composed_v1_hier/drt_antennas.log`
- `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2_nohash_softmax_recip_lut_q8/attention_dual_stream_composed_v1_hier/grt_antennas.log`
- `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2_nohash_softmax_recip_lut_q8/attention_dual_stream_composed_v1_hier/metadata-generate.log`

## Preferred Final-Stage Timing Paths

- raw_path_block_count: 104
- unique_path_block_count: 28
- preferred_stage: `finish`

### Path 1

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2_nohash_softmax_recip_lut_q8/attention_dual_stream_composed_v1_hier/6_finish.rpt`
- stage: `finish`
- startpoint: `stream_buf_1[25]$_DFF_PN0_`
- endpoint: `stream_buf_0_pipe_0[25]$_DFF_PN0_`
- path_group: `clk`
- path_type: `min`
- slack: `0.0300`
- data_arrival_time: `0.5700`
- data_required_time: `0.5400`

```text
Startpoint: stream_buf_1[25]$_DFF_PN0_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: stream_buf_0_pipe_0[25]$_DFF_PN0_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   51.04    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.02    0.02    0.02 ^ wire16093/A (BUF_X16)
     1   52.93    0.01    0.02    0.04 ^ wire16093/Z (BUF_X16)
                                         net16092 (net)
                  0.03    0.02    0.07 ^ clkbuf_0_clk/A (CLKBUF_X3)
     2   37.08    0.03    0.06    0.13 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.03    0.01    0.14 ^ clkbuf_1_0_0_clk/A (CLKBUF_X3)
     2   25.04    0.02    0.05    0.19 ^ clkbuf_1_0_0_clk/Z (CLKBUF_X3)
                                         clknet_1_0_0_clk (net)
                  0.02    0.01    0.19 ^ clkbuf_2_0_0_clk/A (CLKBUF_X3)
     2   28.14    0.02    0.05    0.25 ^ clkbuf_2_0_0_clk/Z (CLKBUF_X3)
...
                                         clknet_5_12__leaf_clk (net)
                  0.07    0.01    0.48 ^ clkbuf_leaf_242_clk/A (CLKBUF_X3)
     4   12.78    0.02    0.06    0.54 ^ clkbuf_leaf_242_clk/Z (CLKBUF_X3)
                                         clknet_leaf_242_clk (net)
                  0.02    0.00    0.54 ^ stream_buf_0_pipe_0[25]$_DFF_PN0_/CK (DFFR_X1)
                          0.00    0.54   clock reconvergence pessimism
                          0.01    0.54   library hold time
                                  0.54   data required time
-----------------------------------------------------------------------------
                                  0.54   data required time
                                 -0.57   data arrival time
-----------------------------------------------------------------------------
                                  0.03   slack (MET)



```

### Path 2

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2_nohash_softmax_recip_lut_q8/attention_dual_stream_composed_v1_hier/6_finish.rpt`
- stage: `finish`
- startpoint: `rst_n (input port clocked by clk)`
- endpoint: `value_accum_0_out[12]$_DFFE_PN0P_`
- path_group: `asynchronous`
- path_type: `min`
- slack: `1.4000`
- data_arrival_time: `2.1500`
- data_required_time: `0.7500`

```text
Startpoint: rst_n (input port clocked by clk)
Endpoint: value_accum_0_out[12]$_DFFE_PN0P_
          (removal check against rising-edge clock clk)
Path Group: asynchronous
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (propagated)
                          2.00    2.00 ^ input external delay
     1    6.80    0.00    0.00    2.00 ^ rst_n (in)
                                         rst_n (net)
                  0.00    0.00    2.00 ^ input1052/A (CLKBUF_X3)
     6   66.64    0.03    0.05    2.05 ^ input1052/Z (CLKBUF_X3)
                                         net1051 (net)
                  0.04    0.01    2.06 ^ place15939/A (BUF_X2)
    25   60.91    0.06    0.08    2.14 ^ place15939/Z (BUF_X2)
                                         net15938 (net)
                  0.07    0.01    2.15 ^ value_accum_0_out[12]$_DFFE_PN0P_/RN (DFFR_X1)
                                  2.15   data arrival time

                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
...
                                         clknet_4_0_0_clk (net)
                  0.02    0.00    0.36 ^ clkbuf_5_0__f_clk/A (CLKBUF_X3)
    18   57.43    0.04    0.07    0.43 ^ clkbuf_5_0__f_clk/Z (CLKBUF_X3)
                                         clknet_5_0__leaf_clk (net)
                  0.04    0.00    0.44 ^ clkbuf_leaf_317_clk/A (CLKBUF_X3)
     5   10.43    0.01    0.05    0.48 ^ clkbuf_leaf_317_clk/Z (CLKBUF_X3)
                                         clknet_leaf_317_clk (net)
                  0.01    0.00    0.48 ^ value_accum_0_out[12]$_DFFE_PN0P_/CK (DFFR_X1)
                          0.00    0.48   clock reconvergence pessimism
                          0.27    0.75   library removal time
                                  0.75   data required time
-----------------------------------------------------------------------------
                                  0.75   data required time
                                 -2.15   data arrival time
-----------------------------------------------------------------------------
                                  1.40   slack (MET)
```

### Path 3

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2_nohash_softmax_recip_lut_q8/attention_dual_stream_composed_v1_hier/6_finish.rpt`
- stage: `finish`
- startpoint: `softmax_scores_pipe_0[2]$_DFF_PN0_`
- endpoint: `u_softmax/weights[56]$_SDFF_PN1_`
- path_group: `clk`
- path_type: `max`
- slack: `2.6400`
- data_arrival_time: `7.7700`
- data_required_time: `10.4000`

```text
Startpoint: softmax_scores_pipe_0[2]$_DFF_PN0_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: u_softmax/weights[56]$_SDFF_PN1_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   51.04    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.02    0.02    0.02 ^ wire16093/A (BUF_X16)
     1   52.93    0.01    0.02    0.04 ^ wire16093/Z (BUF_X16)
                                         net16092 (net)
                  0.03    0.02    0.07 ^ clkbuf_0_clk/A (CLKBUF_X3)
     2   37.08    0.03    0.06    0.13 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.03    0.01    0.14 ^ clkbuf_1_1_0_clk/A (CLKBUF_X3)
     2   25.14    0.02    0.05    0.19 ^ clkbuf_1_1_0_clk/Z (CLKBUF_X3)
                                         clknet_1_1_0_clk (net)
                  0.02    0.01    0.20 ^ clkbuf_2_2_0_clk/A (CLKBUF_X3)
     2   24.02    0.02    0.05    0.25 ^ clkbuf_2_2_0_clk/Z (CLKBUF_X3)
...
                                         clknet_5_21__leaf_clk (net)
                  0.02    0.00   10.40 ^ clkbuf_leaf_86_clk/A (CLKBUF_X3)
     8   10.35    0.01    0.04   10.44 ^ clkbuf_leaf_86_clk/Z (CLKBUF_X3)
                                         clknet_leaf_86_clk (net)
                  0.01    0.00   10.44 ^ u_softmax/weights[56]$_SDFF_PN1_/CK (DFF_X2)
                          0.00   10.44   clock reconvergence pessimism
                         -0.04   10.40   library setup time
                                 10.40   data required time
-----------------------------------------------------------------------------
                                 10.40   data required time
                                 -7.77   data arrival time
-----------------------------------------------------------------------------
                                  2.64   slack (MET)



```

### Path 4

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2_nohash_softmax_recip_lut_q8/attention_dual_stream_composed_v1_hier/6_finish.rpt`
- stage: `finish`
- startpoint: `rst_n (input port clocked by clk)`
- endpoint: `stream_buf_0_pipe_1[203]$_DFF_PN0_`
- path_group: `asynchronous`
- path_type: `max`
- slack: `7.6500`
- data_arrival_time: `2.8900`
- data_required_time: `10.5400`

```text
Startpoint: rst_n (input port clocked by clk)
Endpoint: stream_buf_0_pipe_1[203]$_DFF_PN0_
          (recovery check against rising-edge clock clk)
Path Group: asynchronous
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (propagated)
                          2.00    2.00 ^ input external delay
     1    6.80    0.00    0.00    2.00 ^ rst_n (in)
                                         rst_n (net)
                  0.00    0.00    2.00 ^ input1052/A (CLKBUF_X3)
     6   66.64    0.03    0.05    2.05 ^ input1052/Z (CLKBUF_X3)
                                         net1051 (net)
                  0.08    0.06    2.11 ^ place15991/A (BUF_X1)
     4   52.58    0.11    0.15    2.25 ^ place15991/Z (BUF_X1)
                                         net15990 (net)
                  0.12    0.02    2.27 ^ place15995/A (BUF_X1)
     3    9.70    0.02    0.05    2.33 ^ place15995/Z (BUF_X1)
                                         net15994 (net)
                  0.02    0.00    2.33 ^ place15996/A (BUF_X1)
     9   53.34    0.12    0.14    2.47 ^ place15996/Z (BUF_X1)
...
                                         clknet_4_9_0_clk (net)
                  0.02    0.00   10.37 ^ clkbuf_5_19__f_clk/A (CLKBUF_X3)
     9   54.07    0.04    0.07   10.44 ^ clkbuf_5_19__f_clk/Z (CLKBUF_X3)
                                         clknet_5_19__leaf_clk (net)
                  0.04    0.01   10.44 ^ clkbuf_leaf_81_clk/A (CLKBUF_X3)
     4   13.00    0.01    0.05   10.49 ^ clkbuf_leaf_81_clk/Z (CLKBUF_X3)
                                         clknet_leaf_81_clk (net)
                  0.01    0.00   10.50 ^ stream_buf_0_pipe_1[203]$_DFF_PN0_/CK (DFFR_X1)
                          0.00   10.50   clock reconvergence pessimism
                          0.05   10.54   library recovery time
                                 10.54   data required time
-----------------------------------------------------------------------------
                                 10.54   data required time
                                 -2.89   data arrival time
-----------------------------------------------------------------------------
                                  7.65   slack (MET)
```


## Worst Timing Paths Across All Stages

### Path 1

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2_nohash_softmax_recip_lut_q8/attention_dual_stream_composed_v1_hier/6_finish.rpt`
- stage: `finish`
- startpoint: `stream_buf_1[25]$_DFF_PN0_`
- endpoint: `stream_buf_0_pipe_0[25]$_DFF_PN0_`
- path_group: `clk`
- path_type: `min`
- slack: `0.0300`
- data_arrival_time: `0.5700`
- data_required_time: `0.5400`

```text
Startpoint: stream_buf_1[25]$_DFF_PN0_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: stream_buf_0_pipe_0[25]$_DFF_PN0_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   51.04    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.02    0.02    0.02 ^ wire16093/A (BUF_X16)
     1   52.93    0.01    0.02    0.04 ^ wire16093/Z (BUF_X16)
                                         net16092 (net)
                  0.03    0.02    0.07 ^ clkbuf_0_clk/A (CLKBUF_X3)
     2   37.08    0.03    0.06    0.13 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.03    0.01    0.14 ^ clkbuf_1_0_0_clk/A (CLKBUF_X3)
     2   25.04    0.02    0.05    0.19 ^ clkbuf_1_0_0_clk/Z (CLKBUF_X3)
                                         clknet_1_0_0_clk (net)
                  0.02    0.01    0.19 ^ clkbuf_2_0_0_clk/A (CLKBUF_X3)
     2   28.14    0.02    0.05    0.25 ^ clkbuf_2_0_0_clk/Z (CLKBUF_X3)
...
                                         clknet_5_12__leaf_clk (net)
                  0.07    0.01    0.48 ^ clkbuf_leaf_242_clk/A (CLKBUF_X3)
     4   12.78    0.02    0.06    0.54 ^ clkbuf_leaf_242_clk/Z (CLKBUF_X3)
                                         clknet_leaf_242_clk (net)
                  0.02    0.00    0.54 ^ stream_buf_0_pipe_0[25]$_DFF_PN0_/CK (DFFR_X1)
                          0.00    0.54   clock reconvergence pessimism
                          0.01    0.54   library hold time
                                  0.54   data required time
-----------------------------------------------------------------------------
                                  0.54   data required time
                                 -0.57   data arrival time
-----------------------------------------------------------------------------
                                  0.03   slack (MET)



```

### Path 2

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2_nohash_softmax_recip_lut_q8/attention_dual_stream_composed_v1_hier/2_floorplan_final.rpt`
- stage: `floorplan`
- startpoint: `seed_state[16]$_DFF_PN0_`
- endpoint: `stream_buf_1[16]$_DFF_PN0_`
- path_group: `clk`
- path_type: `min`
- slack: `0.0600`
- data_arrival_time: `0.0600`
- data_required_time: `0.0100`

```text
Startpoint: seed_state[16]$_DFF_PN0_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: stream_buf_1[16]$_DFF_PN0_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                  0.00    0.00    0.00 ^ seed_state[16]$_DFF_PN0_/CK (DFFR_X1)
     1    1.13    0.01    0.06    0.06 ^ seed_state[16]$_DFF_PN0_/QN (DFFR_X1)
                                         _00039_ (net)
                  0.01    0.00    0.06 ^ stream_buf_1[16]$_DFF_PN0_/D (DFFR_X1)
                                  0.06   data arrival time

                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                          0.00    0.00   clock reconvergence pessimism
                                  0.00 ^ stream_buf_1[16]$_DFF_PN0_/CK (DFFR_X1)
                          0.01    0.01   library hold time
                                  0.01   data required time
-----------------------------------------------------------------------------
                                  0.01   data required time
                                 -0.06   data arrival time
-----------------------------------------------------------------------------
                                  0.06   slack (MET)



```

### Path 3

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2_nohash_softmax_recip_lut_q8/attention_dual_stream_composed_v1_hier/3_detailed_place.rpt`
- stage: `detailed_place`
- startpoint: `seed_state[28]$_DFF_PN0_`
- endpoint: `stream_buf_1[28]$_DFF_PN0_`
- path_group: `clk`
- path_type: `min`
- slack: `0.0600`
- data_arrival_time: `0.0600`
- data_required_time: `0.0100`

```text
Startpoint: seed_state[28]$_DFF_PN0_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: stream_buf_1[28]$_DFF_PN0_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                  0.00    0.00    0.00 ^ seed_state[28]$_DFF_PN0_/CK (DFFR_X1)
     1    1.36    0.01    0.06    0.06 ^ seed_state[28]$_DFF_PN0_/QN (DFFR_X1)
                                         _00047_ (net)
                  0.01    0.00    0.06 ^ stream_buf_1[28]$_DFF_PN0_/D (DFFR_X1)
                                  0.06   data arrival time

                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                          0.00    0.00   clock reconvergence pessimism
                                  0.00 ^ stream_buf_1[28]$_DFF_PN0_/CK (DFFR_X1)
                          0.01    0.01   library hold time
                                  0.01   data required time
-----------------------------------------------------------------------------
                                  0.01   data required time
                                 -0.06   data arrival time
-----------------------------------------------------------------------------
                                  0.06   slack (MET)



```

### Path 4

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2_nohash_softmax_recip_lut_q8/attention_dual_stream_composed_v1_hier/3_global_place.rpt`
- stage: `global_place`
- startpoint: `seed_state[22]$_DFF_PN0_`
- endpoint: `stream_buf_1[22]$_DFF_PN0_`
- path_group: `clk`
- path_type: `min`
- slack: `0.0600`
- data_arrival_time: `0.0600`
- data_required_time: `0.0100`

```text
Startpoint: seed_state[22]$_DFF_PN0_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: stream_buf_1[22]$_DFF_PN0_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                  0.00    0.00    0.00 ^ seed_state[22]$_DFF_PN0_/CK (DFFR_X1)
     1    1.38    0.01    0.06    0.06 ^ seed_state[22]$_DFF_PN0_/QN (DFFR_X1)
                                         _00044_ (net)
                  0.01    0.00    0.06 ^ stream_buf_1[22]$_DFF_PN0_/D (DFFR_X2)
                                  0.06   data arrival time

                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                          0.00    0.00   clock reconvergence pessimism
                                  0.00 ^ stream_buf_1[22]$_DFF_PN0_/CK (DFFR_X2)
                          0.01    0.01   library hold time
                                  0.01   data required time
-----------------------------------------------------------------------------
                                  0.01   data required time
                                 -0.06   data arrival time
-----------------------------------------------------------------------------
                                  0.06   slack (MET)



```

### Path 5

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2_nohash_softmax_recip_lut_q8/attention_dual_stream_composed_v1_hier/3_resizer.rpt`
- stage: `resizer`
- startpoint: `seed_state[22]$_DFF_PN0_`
- endpoint: `stream_buf_1[22]$_DFF_PN0_`
- path_group: `clk`
- path_type: `min`
- slack: `0.0600`
- data_arrival_time: `0.0600`
- data_required_time: `0.0100`

```text
Startpoint: seed_state[22]$_DFF_PN0_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: stream_buf_1[22]$_DFF_PN0_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                  0.00    0.00    0.00 ^ seed_state[22]$_DFF_PN0_/CK (DFFR_X1)
     1    1.38    0.01    0.06    0.06 ^ seed_state[22]$_DFF_PN0_/QN (DFFR_X1)
                                         _00044_ (net)
                  0.01    0.00    0.06 ^ stream_buf_1[22]$_DFF_PN0_/D (DFFR_X2)
                                  0.06   data arrival time

                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                          0.00    0.00   clock reconvergence pessimism
                                  0.00 ^ stream_buf_1[22]$_DFF_PN0_/CK (DFFR_X2)
                          0.01    0.01   library hold time
                                  0.01   data required time
-----------------------------------------------------------------------------
                                  0.01   data required time
                                 -0.06   data arrival time
-----------------------------------------------------------------------------
                                  0.06   slack (MET)



```

### Path 6

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2_nohash_softmax_recip_lut_q8/attention_dual_stream_composed_v1_hier/4_cts_final.rpt`
- stage: `cts`
- startpoint: `seed_state[22]$_DFF_PN0_`
- endpoint: `stream_buf_1[22]$_DFF_PN0_`
- path_group: `clk`
- path_type: `min`
- slack: `0.0600`
- data_arrival_time: `0.5600`
- data_required_time: `0.5000`

```text
Startpoint: seed_state[22]$_DFF_PN0_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: stream_buf_1[22]$_DFF_PN0_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   75.40    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.03    0.03    0.03 ^ wire16093/A (BUF_X16)
     1   57.89    0.01    0.03    0.06 ^ wire16093/Z (BUF_X16)
                                         net16092 (net)
                  0.02    0.02    0.07 ^ clkbuf_0_clk/A (CLKBUF_X3)
     2   38.49    0.03    0.06    0.14 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.03    0.00    0.14 ^ clkbuf_1_0_0_clk/A (CLKBUF_X3)
     2   27.24    0.02    0.06    0.20 ^ clkbuf_1_0_0_clk/Z (CLKBUF_X3)
                                         clknet_1_0_0_clk (net)
                  0.02    0.00    0.20 ^ clkbuf_2_0_0_clk/A (CLKBUF_X3)
     2   33.49    0.03    0.06    0.26 ^ clkbuf_2_0_0_clk/Z (CLKBUF_X3)
...
                                         clknet_5_3__leaf_clk (net)
                  0.03    0.00    0.45 ^ clkbuf_leaf_239_clk/A (CLKBUF_X3)
     8   11.30    0.01    0.05    0.49 ^ clkbuf_leaf_239_clk/Z (CLKBUF_X3)
                                         clknet_leaf_239_clk (net)
                  0.01    0.00    0.49 ^ stream_buf_1[22]$_DFF_PN0_/CK (DFFR_X2)
                          0.00    0.49   clock reconvergence pessimism
                          0.01    0.50   library hold time
                                  0.50   data required time
-----------------------------------------------------------------------------
                                  0.50   data required time
                                 -0.56   data arrival time
-----------------------------------------------------------------------------
                                  0.06   slack (MET)



```

### Path 7

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2_nohash_softmax_recip_lut_q8/attention_dual_stream_composed_v1_hier/5_global_route.rpt`
- stage: `route`
- startpoint: `seed_state[22]$_DFF_PN0_`
- endpoint: `stream_buf_1[22]$_DFF_PN0_`
- path_group: `clk`
- path_type: `min`
- slack: `0.0600`
- data_arrival_time: `0.5600`
- data_required_time: `0.5000`

```text
Startpoint: seed_state[22]$_DFF_PN0_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: stream_buf_1[22]$_DFF_PN0_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   72.74    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.03    0.03    0.03 ^ wire16093/A (BUF_X16)
     1   55.51    0.01    0.03    0.05 ^ wire16093/Z (BUF_X16)
                                         net16092 (net)
                  0.02    0.02    0.07 ^ clkbuf_0_clk/A (CLKBUF_X3)
     2   38.22    0.03    0.06    0.13 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.03    0.00    0.14 ^ clkbuf_1_0_0_clk/A (CLKBUF_X3)
     2   27.14    0.02    0.06    0.20 ^ clkbuf_1_0_0_clk/Z (CLKBUF_X3)
                                         clknet_1_0_0_clk (net)
                  0.02    0.01    0.20 ^ clkbuf_2_0_0_clk/A (CLKBUF_X3)
     2   33.30    0.03    0.06    0.26 ^ clkbuf_2_0_0_clk/Z (CLKBUF_X3)
...
                                         clknet_5_3__leaf_clk (net)
                  0.03    0.00    0.45 ^ clkbuf_leaf_239_clk/A (CLKBUF_X3)
     8   11.56    0.01    0.05    0.49 ^ clkbuf_leaf_239_clk/Z (CLKBUF_X3)
                                         clknet_leaf_239_clk (net)
                  0.01    0.00    0.49 ^ stream_buf_1[22]$_DFF_PN0_/CK (DFFR_X2)
                          0.00    0.49   clock reconvergence pessimism
                          0.01    0.50   library hold time
                                  0.50   data required time
-----------------------------------------------------------------------------
                                  0.50   data required time
                                 -0.56   data arrival time
-----------------------------------------------------------------------------
                                  0.06   slack (MET)



```

### Path 8

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2_nohash_softmax_recip_lut_q8/attention_dual_stream_composed_v1_hier/4_cts_final.rpt`
- stage: `cts`
- startpoint: `rst_n (input port clocked by clk)`
- endpoint: `softmax_weights_out[41]$_DFFE_PN0P_`
- path_group: `asynchronous`
- path_type: `min`
- slack: `1.3700`
- data_arrival_time: `2.1900`
- data_required_time: `0.8200`

```text
Startpoint: rst_n (input port clocked by clk)
Endpoint: softmax_weights_out[41]$_DFFE_PN0P_
          (removal check against rising-edge clock clk)
Path Group: asynchronous
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (propagated)
                          2.00    2.00 ^ input external delay
     1    8.83    0.00    0.00    2.00 ^ rst_n (in)
                                         rst_n (net)
                  0.00    0.00    2.00 ^ input1052/A (CLKBUF_X3)
     6   58.58    0.03    0.05    2.05 ^ input1052/Z (CLKBUF_X3)
                                         net1051 (net)
                  0.04    0.01    2.06 ^ place15943/A (BUF_X1)
    19   42.10    0.10    0.12    2.19 ^ place15943/Z (BUF_X1)
                                         net15942 (net)
                  0.10    0.00    2.19 ^ softmax_weights_out[41]$_DFFE_PN0P_/RN (DFFR_X1)
                                  2.19   data arrival time

                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
...
                                         clknet_4_0_0_clk (net)
                  0.02    0.00    0.38 ^ clkbuf_5_0__f_clk/A (CLKBUF_X3)
    18   64.98    0.05    0.08    0.46 ^ clkbuf_5_0__f_clk/Z (CLKBUF_X3)
                                         clknet_5_0__leaf_clk (net)
                  0.05    0.00    0.46 ^ clkbuf_leaf_325_clk/A (CLKBUF_X3)
     8   11.81    0.01    0.05    0.52 ^ clkbuf_leaf_325_clk/Z (CLKBUF_X3)
                                         clknet_leaf_325_clk (net)
                  0.01    0.00    0.52 ^ softmax_weights_out[41]$_DFFE_PN0P_/CK (DFFR_X1)
                          0.00    0.52   clock reconvergence pessimism
                          0.30    0.82   library removal time
                                  0.82   data required time
-----------------------------------------------------------------------------
                                  0.82   data required time
                                 -2.19   data arrival time
-----------------------------------------------------------------------------
                                  1.37   slack (MET)
```
