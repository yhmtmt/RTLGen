# OpenROAD Timing Debug Summary

- design_dir: `runs/designs/npu_blocks/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2_nohash_softmax_recip_lut_q10`
- metrics_path: `runs/designs/npu_blocks/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2_nohash_softmax_recip_lut_q10/metrics.csv`
- rows_considered: 2

## Metrics Rows

| param_hash | tag | status | critical_path_ns | density | result_path |
| --- | --- | --- | ---: | ---: | --- |
| c6a1179a | attention_dual_stream_composed_v1_hier | ok | 7.9306 | 0.4 | `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2_nohash_softmax_recip_lut_q10/attention_dual_stream_composed_v1_hier/6_finish.rpt` |
| e9e34269 | attention_dual_stream_composed_v1_hier | ok | 7.9981 | 0.3 | `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2_nohash_softmax_recip_lut_q10/attention_dual_stream_composed_v1_hier/6_finish.rpt` |

## Inspected Report Files

- `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2_nohash_softmax_recip_lut_q10/attention_dual_stream_composed_v1_hier/6_finish.rpt`
- `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2_nohash_softmax_recip_lut_q10/attention_dual_stream_composed_v1_hier/5_global_route.rpt`
- `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2_nohash_softmax_recip_lut_q10/attention_dual_stream_composed_v1_hier/5_route_drc.rpt`
- `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2_nohash_softmax_recip_lut_q10/attention_dual_stream_composed_v1_hier/5_route_drc.rpt-5.rpt`
- `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2_nohash_softmax_recip_lut_q10/attention_dual_stream_composed_v1_hier/4_cts_final.rpt`
- `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2_nohash_softmax_recip_lut_q10/attention_dual_stream_composed_v1_hier/3_resizer.rpt`
- `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2_nohash_softmax_recip_lut_q10/attention_dual_stream_composed_v1_hier/3_detailed_place.rpt`
- `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2_nohash_softmax_recip_lut_q10/attention_dual_stream_composed_v1_hier/3_global_place.rpt`
- `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2_nohash_softmax_recip_lut_q10/attention_dual_stream_composed_v1_hier/2_floorplan_final.rpt`
- `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2_nohash_softmax_recip_lut_q10/attention_dual_stream_composed_v1_hier/drt_antennas.log`
- `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2_nohash_softmax_recip_lut_q10/attention_dual_stream_composed_v1_hier/grt_antennas.log`
- `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2_nohash_softmax_recip_lut_q10/attention_dual_stream_composed_v1_hier/metadata-generate.log`

## Preferred Final-Stage Timing Paths

- raw_path_block_count: 104
- unique_path_block_count: 28
- preferred_stage: `finish`

### Path 1

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2_nohash_softmax_recip_lut_q10/attention_dual_stream_composed_v1_hier/6_finish.rpt`
- stage: `finish`
- startpoint: `seed_state[22]$_DFF_PN0_`
- endpoint: `stream_buf_1[22]$_DFF_PN0_`
- path_group: `clk`
- path_type: `min`
- slack: `0.0500`
- data_arrival_time: `0.5300`
- data_required_time: `0.4800`

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
     1   50.40    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.02    0.02    0.02 ^ wire17101/A (BUF_X16)
     1   41.99    0.01    0.02    0.04 ^ wire17101/Z (BUF_X16)
                                         net17100 (net)
                  0.02    0.02    0.06 ^ clkbuf_0_clk/A (CLKBUF_X3)
     2   36.01    0.03    0.06    0.12 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.03    0.01    0.12 ^ clkbuf_1_0_0_clk/A (CLKBUF_X3)
     2   25.28    0.02    0.05    0.18 ^ clkbuf_1_0_0_clk/Z (CLKBUF_X3)
                                         clknet_1_0_0_clk (net)
                  0.02    0.01    0.18 ^ clkbuf_2_0_0_clk/A (CLKBUF_X3)
     2   18.11    0.02    0.05    0.23 ^ clkbuf_2_0_0_clk/Z (CLKBUF_X3)
...
                                         clknet_5_6__leaf_clk (net)
                  0.04    0.01    0.42 ^ clkbuf_leaf_246_clk/A (CLKBUF_X3)
     8   10.90    0.01    0.05    0.47 ^ clkbuf_leaf_246_clk/Z (CLKBUF_X3)
                                         clknet_leaf_246_clk (net)
                  0.01    0.00    0.47 ^ stream_buf_1[22]$_DFF_PN0_/CK (DFFR_X1)
                          0.00    0.47   clock reconvergence pessimism
                          0.01    0.48   library hold time
                                  0.48   data required time
-----------------------------------------------------------------------------
                                  0.48   data required time
                                 -0.53   data arrival time
-----------------------------------------------------------------------------
                                  0.05   slack (MET)



```

### Path 2

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2_nohash_softmax_recip_lut_q10/attention_dual_stream_composed_v1_hier/6_finish.rpt`
- stage: `finish`
- startpoint: `rst_n (input port clocked by clk)`
- endpoint: `softmax_weights_out[7]$_DFFE_PN0P_`
- path_group: `asynchronous`
- path_type: `min`
- slack: `1.3600`
- data_arrival_time: `2.1000`
- data_required_time: `0.7400`

```text
Startpoint: rst_n (input port clocked by clk)
Endpoint: softmax_weights_out[7]$_DFFE_PN0P_
          (removal check against rising-edge clock clk)
Path Group: asynchronous
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (propagated)
                          2.00    2.00 ^ input external delay
     1    6.02    0.00    0.00    2.00 ^ rst_n (in)
                                         rst_n (net)
                  0.00    0.00    2.00 ^ input1178/A (CLKBUF_X3)
     9   75.46    0.03    0.05    2.05 ^ input1178/Z (CLKBUF_X3)
                                         net1177 (net)
                  0.08    0.05    2.10 ^ softmax_weights_out[7]$_DFFE_PN0P_/RN (DFFR_X1)
                                  2.10   data arrival time

                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   50.40    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.02    0.02    0.02 ^ wire17101/A (BUF_X16)
...
                                         clknet_4_1_0_clk (net)
                  0.02    0.00    0.33 ^ clkbuf_5_3__f_clk/A (CLKBUF_X3)
    12   56.61    0.04    0.08    0.41 ^ clkbuf_5_3__f_clk/Z (CLKBUF_X3)
                                         clknet_5_3__leaf_clk (net)
                  0.04    0.01    0.41 ^ clkbuf_leaf_300_clk/A (CLKBUF_X3)
     5    8.42    0.01    0.05    0.46 ^ clkbuf_leaf_300_clk/Z (CLKBUF_X3)
                                         clknet_leaf_300_clk (net)
                  0.01    0.00    0.46 ^ softmax_weights_out[7]$_DFFE_PN0P_/CK (DFFR_X1)
                          0.00    0.46   clock reconvergence pessimism
                          0.28    0.74   library removal time
                                  0.74   data required time
-----------------------------------------------------------------------------
                                  0.74   data required time
                                 -2.10   data arrival time
-----------------------------------------------------------------------------
                                  1.36   slack (MET)
```

### Path 3

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2_nohash_softmax_recip_lut_q10/attention_dual_stream_composed_v1_hier/6_finish.rpt`
- stage: `finish`
- startpoint: `softmax_scores_pipe_0[2]$_DFF_PN0_`
- endpoint: `u_softmax/weights[0]$_SDFF_PN1_`
- path_group: `clk`
- path_type: `max`
- slack: `2.4700`
- data_arrival_time: `7.9300`
- data_required_time: `10.4000`

```text
Startpoint: softmax_scores_pipe_0[2]$_DFF_PN0_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: u_softmax/weights[0]$_SDFF_PN1_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   50.40    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.02    0.02    0.02 ^ wire17101/A (BUF_X16)
     1   41.99    0.01    0.02    0.04 ^ wire17101/Z (BUF_X16)
                                         net17100 (net)
                  0.02    0.02    0.06 ^ clkbuf_0_clk/A (CLKBUF_X3)
     2   36.01    0.03    0.06    0.12 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.03    0.01    0.12 ^ clkbuf_1_1_0_clk/A (CLKBUF_X3)
     2   25.83    0.02    0.05    0.18 ^ clkbuf_1_1_0_clk/Z (CLKBUF_X3)
                                         clknet_1_1_0_clk (net)
                  0.02    0.01    0.18 ^ clkbuf_2_2_0_clk/A (CLKBUF_X3)
     2   19.31    0.02    0.05    0.23 ^ clkbuf_2_2_0_clk/Z (CLKBUF_X3)
...
                                         clknet_5_20__leaf_clk (net)
                  0.03    0.00   10.40 ^ clkbuf_leaf_95_clk/A (CLKBUF_X3)
     5   13.02    0.01    0.04   10.44 ^ clkbuf_leaf_95_clk/Z (CLKBUF_X3)
                                         clknet_leaf_95_clk (net)
                  0.01    0.00   10.44 ^ u_softmax/weights[0]$_SDFF_PN1_/CK (DFF_X2)
                          0.00   10.44   clock reconvergence pessimism
                         -0.04   10.40   library setup time
                                 10.40   data required time
-----------------------------------------------------------------------------
                                 10.40   data required time
                                 -7.93   data arrival time
-----------------------------------------------------------------------------
                                  2.47   slack (MET)



```

### Path 4

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2_nohash_softmax_recip_lut_q10/attention_dual_stream_composed_v1_hier/6_finish.rpt`
- stage: `finish`
- startpoint: `rst_n (input port clocked by clk)`
- endpoint: `stream_buf_0_pipe_1[439]$_DFF_PN0_`
- path_group: `asynchronous`
- path_type: `max`
- slack: `7.5300`
- data_arrival_time: `2.9600`
- data_required_time: `10.4900`

```text
Startpoint: rst_n (input port clocked by clk)
Endpoint: stream_buf_0_pipe_1[439]$_DFF_PN0_
          (recovery check against rising-edge clock clk)
Path Group: asynchronous
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (propagated)
                          2.00    2.00 ^ input external delay
     1    6.02    0.00    0.00    2.00 ^ rst_n (in)
                                         rst_n (net)
                  0.00    0.00    2.00 ^ input1178/A (CLKBUF_X3)
     9   75.46    0.03    0.05    2.05 ^ input1178/Z (CLKBUF_X3)
                                         net1177 (net)
                  0.09    0.06    2.11 ^ place17005/A (BUF_X2)
     8   59.22    0.06    0.08    2.19 ^ place17005/Z (BUF_X2)
                                         net17004 (net)
                  0.08    0.04    2.22 ^ place17017/A (BUF_X1)
     2    2.59    0.01    0.04    2.26 ^ place17017/Z (BUF_X1)
                                         net17016 (net)
                  0.01    0.00    2.26 ^ place17040/A (BUF_X1)
     9   44.10    0.10    0.12    2.38 ^ place17040/Z (BUF_X1)
...
                                         clknet_4_15_0_clk (net)
                  0.02    0.00   10.34 ^ clkbuf_5_30__f_clk/A (CLKBUF_X3)
     7   37.28    0.03    0.06   10.40 ^ clkbuf_5_30__f_clk/Z (CLKBUF_X3)
                                         clknet_5_30__leaf_clk (net)
                  0.03    0.00   10.40 ^ clkbuf_leaf_157_clk/A (CLKBUF_X3)
     5    9.79    0.01    0.04   10.45 ^ clkbuf_leaf_157_clk/Z (CLKBUF_X3)
                                         clknet_leaf_157_clk (net)
                  0.01    0.00   10.45 ^ stream_buf_0_pipe_1[439]$_DFF_PN0_/CK (DFFR_X1)
                          0.00   10.45   clock reconvergence pessimism
                          0.04   10.49   library recovery time
                                 10.49   data required time
-----------------------------------------------------------------------------
                                 10.49   data required time
                                 -2.96   data arrival time
-----------------------------------------------------------------------------
                                  7.53   slack (MET)
```


## Worst Timing Paths Across All Stages

### Path 1

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2_nohash_softmax_recip_lut_q10/attention_dual_stream_composed_v1_hier/6_finish.rpt`
- stage: `finish`
- startpoint: `seed_state[22]$_DFF_PN0_`
- endpoint: `stream_buf_1[22]$_DFF_PN0_`
- path_group: `clk`
- path_type: `min`
- slack: `0.0500`
- data_arrival_time: `0.5300`
- data_required_time: `0.4800`

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
     1   50.40    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.02    0.02    0.02 ^ wire17101/A (BUF_X16)
     1   41.99    0.01    0.02    0.04 ^ wire17101/Z (BUF_X16)
                                         net17100 (net)
                  0.02    0.02    0.06 ^ clkbuf_0_clk/A (CLKBUF_X3)
     2   36.01    0.03    0.06    0.12 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.03    0.01    0.12 ^ clkbuf_1_0_0_clk/A (CLKBUF_X3)
     2   25.28    0.02    0.05    0.18 ^ clkbuf_1_0_0_clk/Z (CLKBUF_X3)
                                         clknet_1_0_0_clk (net)
                  0.02    0.01    0.18 ^ clkbuf_2_0_0_clk/A (CLKBUF_X3)
     2   18.11    0.02    0.05    0.23 ^ clkbuf_2_0_0_clk/Z (CLKBUF_X3)
...
                                         clknet_5_6__leaf_clk (net)
                  0.04    0.01    0.42 ^ clkbuf_leaf_246_clk/A (CLKBUF_X3)
     8   10.90    0.01    0.05    0.47 ^ clkbuf_leaf_246_clk/Z (CLKBUF_X3)
                                         clknet_leaf_246_clk (net)
                  0.01    0.00    0.47 ^ stream_buf_1[22]$_DFF_PN0_/CK (DFFR_X1)
                          0.00    0.47   clock reconvergence pessimism
                          0.01    0.48   library hold time
                                  0.48   data required time
-----------------------------------------------------------------------------
                                  0.48   data required time
                                 -0.53   data arrival time
-----------------------------------------------------------------------------
                                  0.05   slack (MET)



```

### Path 2

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2_nohash_softmax_recip_lut_q10/attention_dual_stream_composed_v1_hier/2_floorplan_final.rpt`
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

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2_nohash_softmax_recip_lut_q10/attention_dual_stream_composed_v1_hier/3_detailed_place.rpt`
- stage: `detailed_place`
- startpoint: `seed_state[20]$_DFF_PN0_`
- endpoint: `stream_buf_1[20]$_DFF_PN0_`
- path_group: `clk`
- path_type: `min`
- slack: `0.0600`
- data_arrival_time: `0.0600`
- data_required_time: `0.0100`

```text
Startpoint: seed_state[20]$_DFF_PN0_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: stream_buf_1[20]$_DFF_PN0_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                  0.00    0.00    0.00 ^ seed_state[20]$_DFF_PN0_/CK (DFFR_X1)
     1    1.30    0.01    0.06    0.06 ^ seed_state[20]$_DFF_PN0_/QN (DFFR_X1)
                                         _00043_ (net)
                  0.01    0.00    0.06 ^ stream_buf_1[20]$_DFF_PN0_/D (DFFR_X1)
                                  0.06   data arrival time

                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                          0.00    0.00   clock reconvergence pessimism
                                  0.00 ^ stream_buf_1[20]$_DFF_PN0_/CK (DFFR_X1)
                          0.01    0.01   library hold time
                                  0.01   data required time
-----------------------------------------------------------------------------
                                  0.01   data required time
                                 -0.06   data arrival time
-----------------------------------------------------------------------------
                                  0.06   slack (MET)



```

### Path 4

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2_nohash_softmax_recip_lut_q10/attention_dual_stream_composed_v1_hier/3_global_place.rpt`
- stage: `global_place`
- startpoint: `seed_state[18]$_DFF_PN0_`
- endpoint: `stream_buf_1[18]$_DFF_PN0_`
- path_group: `clk`
- path_type: `min`
- slack: `0.0600`
- data_arrival_time: `0.0600`
- data_required_time: `0.0100`

```text
Startpoint: seed_state[18]$_DFF_PN0_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: stream_buf_1[18]$_DFF_PN0_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                  0.00    0.00    0.00 ^ seed_state[18]$_DFF_PN0_/CK (DFFR_X1)
     1    1.25    0.01    0.06    0.06 ^ seed_state[18]$_DFF_PN0_/QN (DFFR_X1)
                                         _00041_ (net)
                  0.01    0.00    0.06 ^ stream_buf_1[18]$_DFF_PN0_/D (DFFR_X1)
                                  0.06   data arrival time

                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                          0.00    0.00   clock reconvergence pessimism
                                  0.00 ^ stream_buf_1[18]$_DFF_PN0_/CK (DFFR_X1)
                          0.01    0.01   library hold time
                                  0.01   data required time
-----------------------------------------------------------------------------
                                  0.01   data required time
                                 -0.06   data arrival time
-----------------------------------------------------------------------------
                                  0.06   slack (MET)



```

### Path 5

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2_nohash_softmax_recip_lut_q10/attention_dual_stream_composed_v1_hier/3_resizer.rpt`
- stage: `resizer`
- startpoint: `seed_state[18]$_DFF_PN0_`
- endpoint: `stream_buf_1[18]$_DFF_PN0_`
- path_group: `clk`
- path_type: `min`
- slack: `0.0600`
- data_arrival_time: `0.0600`
- data_required_time: `0.0100`

```text
Startpoint: seed_state[18]$_DFF_PN0_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: stream_buf_1[18]$_DFF_PN0_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                  0.00    0.00    0.00 ^ seed_state[18]$_DFF_PN0_/CK (DFFR_X1)
     1    1.25    0.01    0.06    0.06 ^ seed_state[18]$_DFF_PN0_/QN (DFFR_X1)
                                         _00041_ (net)
                  0.01    0.00    0.06 ^ stream_buf_1[18]$_DFF_PN0_/D (DFFR_X1)
                                  0.06   data arrival time

                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                          0.00    0.00   clock reconvergence pessimism
                                  0.00 ^ stream_buf_1[18]$_DFF_PN0_/CK (DFFR_X1)
                          0.01    0.01   library hold time
                                  0.01   data required time
-----------------------------------------------------------------------------
                                  0.01   data required time
                                 -0.06   data arrival time
-----------------------------------------------------------------------------
                                  0.06   slack (MET)



```

### Path 6

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2_nohash_softmax_recip_lut_q10/attention_dual_stream_composed_v1_hier/4_cts_final.rpt`
- stage: `cts`
- startpoint: `seed_state[18]$_DFF_PN0_`
- endpoint: `stream_buf_1[18]$_DFF_PN0_`
- path_group: `clk`
- path_type: `min`
- slack: `0.0600`
- data_arrival_time: `0.5800`
- data_required_time: `0.5200`

```text
Startpoint: seed_state[18]$_DFF_PN0_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: stream_buf_1[18]$_DFF_PN0_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   74.41    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.03    0.03    0.03 ^ wire17101/A (BUF_X16)
     1   56.82    0.01    0.03    0.05 ^ wire17101/Z (BUF_X16)
                                         net17100 (net)
                  0.02    0.02    0.07 ^ clkbuf_0_clk/A (CLKBUF_X3)
     2   37.69    0.03    0.06    0.13 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.03    0.00    0.14 ^ clkbuf_1_0_0_clk/A (CLKBUF_X3)
     2   27.26    0.02    0.06    0.19 ^ clkbuf_1_0_0_clk/Z (CLKBUF_X3)
                                         clknet_1_0_0_clk (net)
                  0.02    0.00    0.20 ^ clkbuf_2_0_0_clk/A (CLKBUF_X3)
     2   22.91    0.02    0.05    0.25 ^ clkbuf_2_0_0_clk/Z (CLKBUF_X3)
...
                                         clknet_5_3__leaf_clk (net)
                  0.06    0.01    0.46 ^ clkbuf_leaf_239_clk/A (CLKBUF_X3)
     5    8.59    0.01    0.05    0.51 ^ clkbuf_leaf_239_clk/Z (CLKBUF_X3)
                                         clknet_leaf_239_clk (net)
                  0.01    0.00    0.51 ^ stream_buf_1[18]$_DFF_PN0_/CK (DFFR_X1)
                          0.00    0.51   clock reconvergence pessimism
                          0.01    0.52   library hold time
                                  0.52   data required time
-----------------------------------------------------------------------------
                                  0.52   data required time
                                 -0.58   data arrival time
-----------------------------------------------------------------------------
                                  0.06   slack (MET)



```

### Path 7

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2_nohash_softmax_recip_lut_q10/attention_dual_stream_composed_v1_hier/5_global_route.rpt`
- stage: `route`
- startpoint: `seed_state[18]$_DFF_PN0_`
- endpoint: `stream_buf_1[18]$_DFF_PN0_`
- path_group: `clk`
- path_type: `min`
- slack: `0.0600`
- data_arrival_time: `0.5800`
- data_required_time: `0.5200`

```text
Startpoint: seed_state[18]$_DFF_PN0_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: stream_buf_1[18]$_DFF_PN0_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   71.68    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.03    0.03    0.03 ^ wire17101/A (BUF_X16)
     1   54.77    0.01    0.03    0.05 ^ wire17101/Z (BUF_X16)
                                         net17100 (net)
                  0.02    0.02    0.07 ^ clkbuf_0_clk/A (CLKBUF_X3)
     2   37.37    0.03    0.06    0.13 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.03    0.00    0.14 ^ clkbuf_1_0_0_clk/A (CLKBUF_X3)
     2   26.89    0.02    0.06    0.19 ^ clkbuf_1_0_0_clk/Z (CLKBUF_X3)
                                         clknet_1_0_0_clk (net)
                  0.02    0.01    0.20 ^ clkbuf_2_0_0_clk/A (CLKBUF_X3)
     2   22.89    0.02    0.05    0.25 ^ clkbuf_2_0_0_clk/Z (CLKBUF_X3)
...
                                         clknet_5_3__leaf_clk (net)
                  0.06    0.01    0.46 ^ clkbuf_leaf_239_clk/A (CLKBUF_X3)
     5    8.86    0.01    0.05    0.51 ^ clkbuf_leaf_239_clk/Z (CLKBUF_X3)
                                         clknet_leaf_239_clk (net)
                  0.01    0.00    0.51 ^ stream_buf_1[18]$_DFF_PN0_/CK (DFFR_X1)
                          0.00    0.51   clock reconvergence pessimism
                          0.01    0.52   library hold time
                                  0.52   data required time
-----------------------------------------------------------------------------
                                  0.52   data required time
                                 -0.58   data arrival time
-----------------------------------------------------------------------------
                                  0.06   slack (MET)



```

### Path 8

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2_nohash_softmax_recip_lut_q10/attention_dual_stream_composed_v1_hier/4_cts_final.rpt`
- stage: `cts`
- startpoint: `rst_n (input port clocked by clk)`
- endpoint: `softmax_weights_out[7]$_DFFE_PN0P_`
- path_group: `asynchronous`
- path_type: `min`
- slack: `1.3100`
- data_arrival_time: `2.0900`
- data_required_time: `0.7800`

```text
Startpoint: rst_n (input port clocked by clk)
Endpoint: softmax_weights_out[7]$_DFFE_PN0P_
          (removal check against rising-edge clock clk)
Path Group: asynchronous
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (propagated)
                          2.00    2.00 ^ input external delay
     1    6.50    0.00    0.00    2.00 ^ rst_n (in)
                                         rst_n (net)
                  0.00    0.00    2.00 ^ input1178/A (CLKBUF_X3)
     9   70.86    0.03    0.05    2.05 ^ input1178/Z (CLKBUF_X3)
                                         net1177 (net)
                  0.07    0.04    2.09 ^ softmax_weights_out[7]$_DFFE_PN0P_/RN (DFFR_X1)
                                  2.09   data arrival time

                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   74.41    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.03    0.03    0.03 ^ wire17101/A (BUF_X16)
...
                                         clknet_4_1_0_clk (net)
                  0.02    0.00    0.37 ^ clkbuf_5_3__f_clk/A (CLKBUF_X3)
    12   72.24    0.05    0.09    0.46 ^ clkbuf_5_3__f_clk/Z (CLKBUF_X3)
                                         clknet_5_3__leaf_clk (net)
                  0.06    0.01    0.46 ^ clkbuf_leaf_300_clk/A (CLKBUF_X3)
     5    8.46    0.01    0.05    0.51 ^ clkbuf_leaf_300_clk/Z (CLKBUF_X3)
                                         clknet_leaf_300_clk (net)
                  0.01    0.00    0.51 ^ softmax_weights_out[7]$_DFFE_PN0P_/CK (DFFR_X1)
                          0.00    0.51   clock reconvergence pessimism
                          0.27    0.78   library removal time
                                  0.78   data required time
-----------------------------------------------------------------------------
                                  0.78   data required time
                                 -2.09   data arrival time
-----------------------------------------------------------------------------
                                  1.31   slack (MET)
```
