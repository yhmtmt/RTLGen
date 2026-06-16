# OpenROAD Timing Debug Summary

- design_dir: `runs/designs/npu_blocks/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2_nohash_softmax_pow2sum`
- metrics_path: `runs/designs/npu_blocks/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2_nohash_softmax_pow2sum/metrics.csv`
- rows_considered: 2

## Metrics Rows

| param_hash | tag | status | critical_path_ns | density | result_path |
| --- | --- | --- | ---: | ---: | --- |
| 40317f7f | attention_dual_stream_composed_v1_hier | ok | 6.4411 | 0.4 | `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2_nohash_softmax_pow2sum/attention_dual_stream_composed_v1_hier/6_finish.rpt` |
| 81f459d1 | attention_dual_stream_composed_v1_hier | ok | 6.8017 | 0.3 | `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2_nohash_softmax_pow2sum/attention_dual_stream_composed_v1_hier/6_finish.rpt` |

## Inspected Report Files

- `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2_nohash_softmax_pow2sum/attention_dual_stream_composed_v1_hier/6_finish.rpt`
- `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2_nohash_softmax_pow2sum/attention_dual_stream_composed_v1_hier/5_global_route.rpt`
- `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2_nohash_softmax_pow2sum/attention_dual_stream_composed_v1_hier/5_route_drc.rpt`
- `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2_nohash_softmax_pow2sum/attention_dual_stream_composed_v1_hier/5_route_drc.rpt-5.rpt`
- `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2_nohash_softmax_pow2sum/attention_dual_stream_composed_v1_hier/4_cts_final.rpt`
- `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2_nohash_softmax_pow2sum/attention_dual_stream_composed_v1_hier/3_resizer.rpt`
- `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2_nohash_softmax_pow2sum/attention_dual_stream_composed_v1_hier/3_detailed_place.rpt`
- `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2_nohash_softmax_pow2sum/attention_dual_stream_composed_v1_hier/3_global_place.rpt`
- `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2_nohash_softmax_pow2sum/attention_dual_stream_composed_v1_hier/2_floorplan_final.rpt`
- `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2_nohash_softmax_pow2sum/attention_dual_stream_composed_v1_hier/drt_antennas.log`
- `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2_nohash_softmax_pow2sum/attention_dual_stream_composed_v1_hier/grt_antennas.log`
- `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2_nohash_softmax_pow2sum/attention_dual_stream_composed_v1_hier/metadata-generate.log`

## Preferred Final-Stage Timing Paths

- raw_path_block_count: 104
- unique_path_block_count: 28
- preferred_stage: `finish`

### Path 1

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2_nohash_softmax_pow2sum/attention_dual_stream_composed_v1_hier/6_finish.rpt`
- stage: `finish`
- startpoint: `stream_buf_1_pipe_1[42]$_DFF_PN0_`
- endpoint: `stream_buf_1_pipe_1[74]$_DFF_PN0_`
- path_group: `clk`
- path_type: `min`
- slack: `0.0500`
- data_arrival_time: `0.4800`
- data_required_time: `0.4300`

```text
Startpoint: stream_buf_1_pipe_1[42]$_DFF_PN0_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: stream_buf_1_pipe_1[74]$_DFF_PN0_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   35.58    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.01    0.01    0.01 ^ wire14628/A (BUF_X8)
     1   38.56    0.01    0.03    0.04 ^ wire14628/Z (BUF_X8)
                                         net14627 (net)
                  0.01    0.00    0.04 ^ clkbuf_0_clk/A (CLKBUF_X3)
     2   39.98    0.03    0.06    0.10 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.03    0.00    0.11 ^ clkbuf_1_0_0_clk/A (CLKBUF_X3)
     2   28.08    0.02    0.06    0.16 ^ clkbuf_1_0_0_clk/Z (CLKBUF_X3)
                                         clknet_1_0_0_clk (net)
                  0.02    0.00    0.17 ^ clkbuf_2_0_0_clk/A (CLKBUF_X3)
     4   29.73    0.02    0.06    0.22 ^ clkbuf_2_0_0_clk/Z (CLKBUF_X3)
...
                                         clknet_5_4__leaf_clk (net)
                  0.06    0.01    0.37 ^ clkbuf_leaf_334_clk/A (CLKBUF_X3)
     4    9.87    0.01    0.05    0.42 ^ clkbuf_leaf_334_clk/Z (CLKBUF_X3)
                                         clknet_leaf_334_clk (net)
                  0.01    0.00    0.42 ^ stream_buf_1_pipe_1[74]$_DFF_PN0_/CK (DFFR_X2)
                          0.00    0.42   clock reconvergence pessimism
                          0.00    0.43   library hold time
                                  0.43   data required time
-----------------------------------------------------------------------------
                                  0.43   data required time
                                 -0.48   data arrival time
-----------------------------------------------------------------------------
                                  0.05   slack (MET)



```

### Path 2

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2_nohash_softmax_pow2sum/attention_dual_stream_composed_v1_hier/6_finish.rpt`
- stage: `finish`
- startpoint: `rst_n (input port clocked by clk)`
- endpoint: `stream_buf_1_pipe_1[75]$_DFF_PN0_`
- path_group: `asynchronous`
- path_type: `min`
- slack: `1.4300`
- data_arrival_time: `2.0800`
- data_required_time: `0.6500`

```text
Startpoint: rst_n (input port clocked by clk)
Endpoint: stream_buf_1_pipe_1[75]$_DFF_PN0_
          (removal check against rising-edge clock clk)
Path Group: asynchronous
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (propagated)
                          2.00    2.00 ^ input external delay
     1    4.97    0.00    0.00    2.00 ^ rst_n (in)
                                         rst_n (net)
                  0.00    0.00    2.00 ^ input345/A (CLKBUF_X3)
    14   52.89    0.03    0.05    2.05 ^ input345/Z (CLKBUF_X3)
                                         net344 (net)
                  0.05    0.02    2.08 ^ stream_buf_1_pipe_1[75]$_DFF_PN0_/RN (DFFR_X2)
                                  2.08   data arrival time

                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   35.58    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.01    0.01    0.01 ^ wire14628/A (BUF_X8)
...
                                         clknet_4_2_0_clk (net)
                  0.02    0.00    0.28 ^ clkbuf_5_4__f_clk/A (CLKBUF_X3)
    11   78.98    0.06    0.09    0.36 ^ clkbuf_5_4__f_clk/Z (CLKBUF_X3)
                                         clknet_5_4__leaf_clk (net)
                  0.06    0.01    0.37 ^ clkbuf_leaf_333_clk/A (CLKBUF_X3)
     7    9.48    0.01    0.05    0.42 ^ clkbuf_leaf_333_clk/Z (CLKBUF_X3)
                                         clknet_leaf_333_clk (net)
                  0.01    0.00    0.42 ^ stream_buf_1_pipe_1[75]$_DFF_PN0_/CK (DFFR_X2)
                          0.00    0.42   clock reconvergence pessimism
                          0.23    0.65   library removal time
                                  0.65   data required time
-----------------------------------------------------------------------------
                                  0.65   data required time
                                 -2.08   data arrival time
-----------------------------------------------------------------------------
                                  1.43   slack (MET)
```

### Path 3

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2_nohash_softmax_pow2sum/attention_dual_stream_composed_v1_hier/6_finish.rpt`
- stage: `finish`
- startpoint: `softmax_scores_pipe_0[1]$_DFF_PN0_`
- endpoint: `u_softmax/weights[38]$_SDFF_PN1_`
- path_group: `clk`
- path_type: `max`
- slack: `3.9300`
- data_arrival_time: `6.4400`
- data_required_time: `10.3700`

```text
Startpoint: softmax_scores_pipe_0[1]$_DFF_PN0_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: u_softmax/weights[38]$_SDFF_PN1_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   35.58    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.01    0.01    0.01 ^ wire14628/A (BUF_X8)
     1   38.56    0.01    0.03    0.04 ^ wire14628/Z (BUF_X8)
                                         net14627 (net)
                  0.01    0.00    0.04 ^ clkbuf_0_clk/A (CLKBUF_X3)
     2   39.98    0.03    0.06    0.10 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.03    0.00    0.11 ^ clkbuf_1_0_0_clk/A (CLKBUF_X3)
     2   28.08    0.02    0.06    0.16 ^ clkbuf_1_0_0_clk/Z (CLKBUF_X3)
                                         clknet_1_0_0_clk (net)
                  0.02    0.00    0.17 ^ clkbuf_2_1_0_clk/A (CLKBUF_X3)
     4   35.74    0.03    0.06    0.23 ^ clkbuf_2_1_0_clk/Z (CLKBUF_X3)
...
                                         clknet_5_3__leaf_clk (net)
                  0.04    0.00   10.36 ^ clkbuf_leaf_295_clk/A (CLKBUF_X3)
     8   11.00    0.01    0.05   10.41 ^ clkbuf_leaf_295_clk/Z (CLKBUF_X3)
                                         clknet_leaf_295_clk (net)
                  0.01    0.00   10.41 ^ u_softmax/weights[38]$_SDFF_PN1_/CK (DFF_X1)
                          0.00   10.41   clock reconvergence pessimism
                         -0.04   10.37   library setup time
                                 10.37   data required time
-----------------------------------------------------------------------------
                                 10.37   data required time
                                 -6.44   data arrival time
-----------------------------------------------------------------------------
                                  3.93   slack (MET)



```

### Path 4

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2_nohash_softmax_pow2sum/attention_dual_stream_composed_v1_hier/6_finish.rpt`
- stage: `finish`
- startpoint: `rst_n (input port clocked by clk)`
- endpoint: `stream_buf_1_pipe_1[163]$_DFF_PN0_`
- path_group: `asynchronous`
- path_type: `max`
- slack: `7.4800`
- data_arrival_time: `2.9800`
- data_required_time: `10.4700`

```text
Startpoint: rst_n (input port clocked by clk)
Endpoint: stream_buf_1_pipe_1[163]$_DFF_PN0_
          (recovery check against rising-edge clock clk)
Path Group: asynchronous
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (propagated)
                          2.00    2.00 ^ input external delay
     1    4.97    0.00    0.00    2.00 ^ rst_n (in)
                                         rst_n (net)
                  0.00    0.00    2.00 ^ input345/A (CLKBUF_X3)
    14   52.89    0.03    0.05    2.05 ^ input345/Z (CLKBUF_X3)
                                         net344 (net)
                  0.05    0.02    2.08 ^ place14499/A (BUF_X2)
     4   29.73    0.03    0.05    2.13 ^ place14499/Z (BUF_X2)
                                         net14498 (net)
                  0.04    0.02    2.14 ^ place14501/A (BUF_X2)
     7   50.71    0.06    0.08    2.22 ^ place14501/Z (BUF_X2)
                                         net14500 (net)
                  0.06    0.02    2.24 ^ place14516/A (BUF_X2)
     4   43.81    0.05    0.07    2.31 ^ place14516/Z (BUF_X2)
...
                                         clknet_4_10_0_clk (net)
                  0.02    0.00   10.30 ^ clkbuf_5_20__f_clk/A (CLKBUF_X3)
    10   48.49    0.04    0.07   10.37 ^ clkbuf_5_20__f_clk/Z (CLKBUF_X3)
                                         clknet_5_20__leaf_clk (net)
                  0.04    0.00   10.38 ^ clkbuf_leaf_50_clk/A (CLKBUF_X3)
     4    7.73    0.01    0.04   10.42 ^ clkbuf_leaf_50_clk/Z (CLKBUF_X3)
                                         clknet_leaf_50_clk (net)
                  0.01    0.00   10.42 ^ stream_buf_1_pipe_1[163]$_DFF_PN0_/CK (DFFR_X1)
                          0.00   10.42   clock reconvergence pessimism
                          0.04   10.47   library recovery time
                                 10.47   data required time
-----------------------------------------------------------------------------
                                 10.47   data required time
                                 -2.98   data arrival time
-----------------------------------------------------------------------------
                                  7.48   slack (MET)
```


## Worst Timing Paths Across All Stages

### Path 1

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2_nohash_softmax_pow2sum/attention_dual_stream_composed_v1_hier/4_cts_final.rpt`
- stage: `cts`
- startpoint: `stream_buf_1_pipe_1[42]$_DFF_PN0_`
- endpoint: `stream_buf_1_pipe_1[74]$_DFF_PN0_`
- path_group: `clk`
- path_type: `min`
- slack: `0.0400`
- data_arrival_time: `0.5200`
- data_required_time: `0.4800`

```text
Startpoint: stream_buf_1_pipe_1[42]$_DFF_PN0_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: stream_buf_1_pipe_1[74]$_DFF_PN0_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   54.53    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.02    0.01    0.01 ^ wire14628/A (BUF_X8)
     1   44.48    0.01    0.03    0.04 ^ wire14628/Z (BUF_X8)
                                         net14627 (net)
                  0.02    0.01    0.06 ^ clkbuf_0_clk/A (CLKBUF_X3)
     2   42.41    0.03    0.07    0.12 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.03    0.00    0.12 ^ clkbuf_1_0_0_clk/A (CLKBUF_X3)
     2   37.00    0.03    0.07    0.19 ^ clkbuf_1_0_0_clk/Z (CLKBUF_X3)
                                         clknet_1_0_0_clk (net)
                  0.03    0.00    0.19 ^ clkbuf_2_0_0_clk/A (CLKBUF_X3)
     4   36.31    0.03    0.06    0.26 ^ clkbuf_2_0_0_clk/Z (CLKBUF_X3)
...
                                         clknet_5_4__leaf_clk (net)
                  0.06    0.01    0.42 ^ clkbuf_leaf_334_clk/A (CLKBUF_X3)
     4    9.95    0.01    0.05    0.47 ^ clkbuf_leaf_334_clk/Z (CLKBUF_X3)
                                         clknet_leaf_334_clk (net)
                  0.01    0.00    0.47 ^ stream_buf_1_pipe_1[74]$_DFF_PN0_/CK (DFFR_X2)
                          0.00    0.47   clock reconvergence pessimism
                          0.00    0.48   library hold time
                                  0.48   data required time
-----------------------------------------------------------------------------
                                  0.48   data required time
                                 -0.52   data arrival time
-----------------------------------------------------------------------------
                                  0.04   slack (MET)



```

### Path 2

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2_nohash_softmax_pow2sum/attention_dual_stream_composed_v1_hier/5_global_route.rpt`
- stage: `route`
- startpoint: `stream_buf_1_pipe_1[42]$_DFF_PN0_`
- endpoint: `stream_buf_1_pipe_1[74]$_DFF_PN0_`
- path_group: `clk`
- path_type: `min`
- slack: `0.0400`
- data_arrival_time: `0.5100`
- data_required_time: `0.4600`

```text
Startpoint: stream_buf_1_pipe_1[42]$_DFF_PN0_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: stream_buf_1_pipe_1[74]$_DFF_PN0_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   52.38    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.02    0.01    0.01 ^ wire14628/A (BUF_X8)
     1   36.44    0.01    0.03    0.04 ^ wire14628/Z (BUF_X8)
                                         net14627 (net)
                  0.01    0.00    0.05 ^ clkbuf_0_clk/A (CLKBUF_X3)
     2   41.75    0.03    0.06    0.11 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.03    0.00    0.11 ^ clkbuf_1_0_0_clk/A (CLKBUF_X3)
     2   37.02    0.03    0.06    0.18 ^ clkbuf_1_0_0_clk/Z (CLKBUF_X3)
                                         clknet_1_0_0_clk (net)
                  0.03    0.01    0.18 ^ clkbuf_2_0_0_clk/A (CLKBUF_X3)
     4   36.37    0.03    0.06    0.25 ^ clkbuf_2_0_0_clk/Z (CLKBUF_X3)
...
                                         clknet_5_4__leaf_clk (net)
                  0.06    0.01    0.41 ^ clkbuf_leaf_334_clk/A (CLKBUF_X3)
     4    9.59    0.01    0.05    0.46 ^ clkbuf_leaf_334_clk/Z (CLKBUF_X3)
                                         clknet_leaf_334_clk (net)
                  0.01    0.00    0.46 ^ stream_buf_1_pipe_1[74]$_DFF_PN0_/CK (DFFR_X2)
                          0.00    0.46   clock reconvergence pessimism
                          0.00    0.46   library hold time
                                  0.46   data required time
-----------------------------------------------------------------------------
                                  0.46   data required time
                                 -0.51   data arrival time
-----------------------------------------------------------------------------
                                  0.04   slack (MET)



```

### Path 3

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2_nohash_softmax_pow2sum/attention_dual_stream_composed_v1_hier/6_finish.rpt`
- stage: `finish`
- startpoint: `stream_buf_1_pipe_1[42]$_DFF_PN0_`
- endpoint: `stream_buf_1_pipe_1[74]$_DFF_PN0_`
- path_group: `clk`
- path_type: `min`
- slack: `0.0500`
- data_arrival_time: `0.4800`
- data_required_time: `0.4300`

```text
Startpoint: stream_buf_1_pipe_1[42]$_DFF_PN0_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: stream_buf_1_pipe_1[74]$_DFF_PN0_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   35.58    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.01    0.01    0.01 ^ wire14628/A (BUF_X8)
     1   38.56    0.01    0.03    0.04 ^ wire14628/Z (BUF_X8)
                                         net14627 (net)
                  0.01    0.00    0.04 ^ clkbuf_0_clk/A (CLKBUF_X3)
     2   39.98    0.03    0.06    0.10 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.03    0.00    0.11 ^ clkbuf_1_0_0_clk/A (CLKBUF_X3)
     2   28.08    0.02    0.06    0.16 ^ clkbuf_1_0_0_clk/Z (CLKBUF_X3)
                                         clknet_1_0_0_clk (net)
                  0.02    0.00    0.17 ^ clkbuf_2_0_0_clk/A (CLKBUF_X3)
     4   29.73    0.02    0.06    0.22 ^ clkbuf_2_0_0_clk/Z (CLKBUF_X3)
...
                                         clknet_5_4__leaf_clk (net)
                  0.06    0.01    0.37 ^ clkbuf_leaf_334_clk/A (CLKBUF_X3)
     4    9.87    0.01    0.05    0.42 ^ clkbuf_leaf_334_clk/Z (CLKBUF_X3)
                                         clknet_leaf_334_clk (net)
                  0.01    0.00    0.42 ^ stream_buf_1_pipe_1[74]$_DFF_PN0_/CK (DFFR_X2)
                          0.00    0.42   clock reconvergence pessimism
                          0.00    0.43   library hold time
                                  0.43   data required time
-----------------------------------------------------------------------------
                                  0.43   data required time
                                 -0.48   data arrival time
-----------------------------------------------------------------------------
                                  0.05   slack (MET)



```

### Path 4

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2_nohash_softmax_pow2sum/attention_dual_stream_composed_v1_hier/2_floorplan_final.rpt`
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

### Path 5

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2_nohash_softmax_pow2sum/attention_dual_stream_composed_v1_hier/3_detailed_place.rpt`
- stage: `detailed_place`
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
     1    1.40    0.01    0.06    0.06 ^ seed_state[22]$_DFF_PN0_/QN (DFFR_X1)
                                         _00044_ (net)
                  0.01    0.00    0.06 ^ stream_buf_1[22]$_DFF_PN0_/D (DFFR_X1)
                                  0.06   data arrival time

                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                          0.00    0.00   clock reconvergence pessimism
                                  0.00 ^ stream_buf_1[22]$_DFF_PN0_/CK (DFFR_X1)
                          0.01    0.01   library hold time
                                  0.01   data required time
-----------------------------------------------------------------------------
                                  0.01   data required time
                                 -0.06   data arrival time
-----------------------------------------------------------------------------
                                  0.06   slack (MET)



```

### Path 6

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2_nohash_softmax_pow2sum/attention_dual_stream_composed_v1_hier/3_global_place.rpt`
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
     1    1.30    0.01    0.06    0.06 ^ seed_state[22]$_DFF_PN0_/QN (DFFR_X1)
                                         _00044_ (net)
                  0.01    0.00    0.06 ^ stream_buf_1[22]$_DFF_PN0_/D (DFFR_X1)
                                  0.06   data arrival time

                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                          0.00    0.00   clock reconvergence pessimism
                                  0.00 ^ stream_buf_1[22]$_DFF_PN0_/CK (DFFR_X1)
                          0.01    0.01   library hold time
                                  0.01   data required time
-----------------------------------------------------------------------------
                                  0.01   data required time
                                 -0.06   data arrival time
-----------------------------------------------------------------------------
                                  0.06   slack (MET)



```

### Path 7

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2_nohash_softmax_pow2sum/attention_dual_stream_composed_v1_hier/3_resizer.rpt`
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
     1    1.30    0.01    0.06    0.06 ^ seed_state[22]$_DFF_PN0_/QN (DFFR_X1)
                                         _00044_ (net)
                  0.01    0.00    0.06 ^ stream_buf_1[22]$_DFF_PN0_/D (DFFR_X1)
                                  0.06   data arrival time

                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                          0.00    0.00   clock reconvergence pessimism
                                  0.00 ^ stream_buf_1[22]$_DFF_PN0_/CK (DFFR_X1)
                          0.01    0.01   library hold time
                                  0.01   data required time
-----------------------------------------------------------------------------
                                  0.01   data required time
                                 -0.06   data arrival time
-----------------------------------------------------------------------------
                                  0.06   slack (MET)



```

### Path 8

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2_nohash_softmax_pow2sum/attention_dual_stream_composed_v1_hier/4_cts_final.rpt`
- stage: `cts`
- startpoint: `rst_n (input port clocked by clk)`
- endpoint: `stream_buf_1_pipe_1[75]$_DFF_PN0_`
- path_group: `asynchronous`
- path_type: `min`
- slack: `1.3800`
- data_arrival_time: `2.0800`
- data_required_time: `0.7000`

```text
Startpoint: rst_n (input port clocked by clk)
Endpoint: stream_buf_1_pipe_1[75]$_DFF_PN0_
          (removal check against rising-edge clock clk)
Path Group: asynchronous
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (propagated)
                          2.00    2.00 ^ input external delay
     1    6.40    0.00    0.00    2.00 ^ rst_n (in)
                                         rst_n (net)
                  0.00    0.00    2.00 ^ input345/A (CLKBUF_X3)
    14   51.73    0.04    0.05    2.05 ^ input345/Z (CLKBUF_X3)
                                         net344 (net)
                  0.05    0.02    2.08 ^ stream_buf_1_pipe_1[75]$_DFF_PN0_/RN (DFFR_X2)
                                  2.08   data arrival time

                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   54.53    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.02    0.01    0.01 ^ wire14628/A (BUF_X8)
...
                                         clknet_4_2_0_clk (net)
                  0.02    0.00    0.32 ^ clkbuf_5_4__f_clk/A (CLKBUF_X3)
    11   85.03    0.06    0.10    0.41 ^ clkbuf_5_4__f_clk/Z (CLKBUF_X3)
                                         clknet_5_4__leaf_clk (net)
                  0.06    0.01    0.42 ^ clkbuf_leaf_333_clk/A (CLKBUF_X3)
     7    9.83    0.01    0.05    0.47 ^ clkbuf_leaf_333_clk/Z (CLKBUF_X3)
                                         clknet_leaf_333_clk (net)
                  0.01    0.00    0.47 ^ stream_buf_1_pipe_1[75]$_DFF_PN0_/CK (DFFR_X2)
                          0.00    0.47   clock reconvergence pessimism
                          0.22    0.70   library removal time
                                  0.70   data required time
-----------------------------------------------------------------------------
                                  0.70   data required time
                                 -2.08   data arrival time
-----------------------------------------------------------------------------
                                  1.38   slack (MET)
```
