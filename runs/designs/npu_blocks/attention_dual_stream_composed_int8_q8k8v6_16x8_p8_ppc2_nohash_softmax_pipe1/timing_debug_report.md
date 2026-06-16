# OpenROAD Timing Debug Summary

- design_dir: `runs/designs/npu_blocks/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2_nohash_softmax_pipe1`
- metrics_path: `runs/designs/npu_blocks/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2_nohash_softmax_pipe1/metrics.csv`
- rows_considered: 2

## Metrics Rows

| param_hash | tag | status | critical_path_ns | density | result_path |
| --- | --- | --- | ---: | ---: | --- |
| 40317f7f | attention_dual_stream_composed_v1_hier | ok | 22.7935 | 0.4 | `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2_nohash_softmax_pipe1/attention_dual_stream_composed_v1_hier/6_finish.rpt` |
| 81f459d1 | attention_dual_stream_composed_v1_hier | ok | 22.8230 | 0.3 | `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2_nohash_softmax_pipe1/attention_dual_stream_composed_v1_hier/6_finish.rpt` |

## Inspected Report Files

- `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2_nohash_softmax_pipe1/attention_dual_stream_composed_v1_hier/6_finish.rpt`
- `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2_nohash_softmax_pipe1/attention_dual_stream_composed_v1_hier/5_global_route.rpt`
- `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2_nohash_softmax_pipe1/attention_dual_stream_composed_v1_hier/5_route_drc.rpt`
- `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2_nohash_softmax_pipe1/attention_dual_stream_composed_v1_hier/5_route_drc.rpt-5.rpt`
- `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2_nohash_softmax_pipe1/attention_dual_stream_composed_v1_hier/4_cts_final.rpt`
- `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2_nohash_softmax_pipe1/attention_dual_stream_composed_v1_hier/3_resizer.rpt`
- `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2_nohash_softmax_pipe1/attention_dual_stream_composed_v1_hier/3_detailed_place.rpt`
- `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2_nohash_softmax_pipe1/attention_dual_stream_composed_v1_hier/3_global_place.rpt`
- `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2_nohash_softmax_pipe1/attention_dual_stream_composed_v1_hier/2_floorplan_final.rpt`
- `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2_nohash_softmax_pipe1/attention_dual_stream_composed_v1_hier/drt_antennas.log`
- `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2_nohash_softmax_pipe1/attention_dual_stream_composed_v1_hier/grt_antennas.log`
- `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2_nohash_softmax_pipe1/attention_dual_stream_composed_v1_hier/metadata-generate.log`

## Preferred Final-Stage Timing Paths

- raw_path_block_count: 104
- unique_path_block_count: 28
- preferred_stage: `finish`

### Path 1

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2_nohash_softmax_pipe1/attention_dual_stream_composed_v1_hier/6_finish.rpt`
- stage: `finish`
- startpoint: `softmax_scores_pipe_0[9]$_DFF_PN0_`
- endpoint: `u_softmax/weights[56]$_SDFF_PN1_`
- path_group: `clk`
- path_type: `max`
- slack: `-12.2000`
- data_arrival_time: `22.7900`
- data_required_time: `10.5900`

```text
Startpoint: softmax_scores_pipe_0[9]$_DFF_PN0_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: u_softmax/weights[56]$_SDFF_PN1_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   12.69    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.00    0.00    0.00 ^ wire46768/A (BUF_X8)
     1   54.48    0.01    0.02    0.02 ^ wire46768/Z (BUF_X8)
                                         net46767 (net)
                  0.03    0.02    0.05 ^ wire46767/A (BUF_X16)
     1   72.24    0.01    0.03    0.07 ^ wire46767/Z (BUF_X16)
                                         net46766 (net)
                  0.04    0.03    0.10 ^ clkbuf_0_clk/A (CLKBUF_X3)
     2   38.71    0.03    0.07    0.17 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.03    0.00    0.18 ^ clkbuf_1_1_0_clk/A (CLKBUF_X3)
     1   26.53    0.02    0.06    0.23 ^ clkbuf_1_1_0_clk/Z (CLKBUF_X3)
...
                                         clknet_5_23_0_clk (net)
                  0.06    0.04   10.56 ^ clkbuf_leaf_117_clk/A (CLKBUF_X3)
     3   22.61    0.02    0.06   10.63 ^ clkbuf_leaf_117_clk/Z (CLKBUF_X3)
                                         clknet_leaf_117_clk (net)
                  0.02    0.00   10.63 ^ u_softmax/weights[56]$_SDFF_PN1_/CK (DFF_X2)
                          0.00   10.63   clock reconvergence pessimism
                         -0.04   10.59   library setup time
                                 10.59   data required time
-----------------------------------------------------------------------------
                                 10.59   data required time
                                -22.79   data arrival time
-----------------------------------------------------------------------------
                                -12.20   slack (VIOLATED)



```

### Path 2

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2_nohash_softmax_pipe1/attention_dual_stream_composed_v1_hier/6_finish.rpt`
- stage: `finish`
- startpoint: `stream_buf_0_pipe_1[92]$_DFF_PN0_`
- endpoint: `stream_buf_0_pipe_1[124]$_DFF_PN0_`
- path_group: `clk`
- path_type: `min`
- slack: `0.0100`
- data_arrival_time: `0.7000`
- data_required_time: `0.6900`

```text
Startpoint: stream_buf_0_pipe_1[92]$_DFF_PN0_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: stream_buf_0_pipe_1[124]$_DFF_PN0_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   12.69    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.00    0.00    0.00 ^ wire46768/A (BUF_X8)
     1   54.48    0.01    0.02    0.02 ^ wire46768/Z (BUF_X8)
                                         net46767 (net)
                  0.03    0.02    0.05 ^ wire46767/A (BUF_X16)
     1   72.24    0.01    0.03    0.07 ^ wire46767/Z (BUF_X16)
                                         net46766 (net)
                  0.04    0.03    0.10 ^ clkbuf_0_clk/A (CLKBUF_X3)
     2   38.71    0.03    0.07    0.17 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.03    0.00    0.18 ^ clkbuf_1_0_0_clk/A (CLKBUF_X3)
     1   31.06    0.02    0.06    0.23 ^ clkbuf_1_0_0_clk/Z (CLKBUF_X3)
...
                                         clknet_5_0_0_clk (net)
                  0.08    0.01    0.62 ^ clkbuf_leaf_297_clk/A (CLKBUF_X3)
     7   12.74    0.02    0.06    0.68 ^ clkbuf_leaf_297_clk/Z (CLKBUF_X3)
                                         clknet_leaf_297_clk (net)
                  0.02    0.00    0.68 ^ stream_buf_0_pipe_1[124]$_DFF_PN0_/CK (DFFR_X1)
                          0.00    0.68   clock reconvergence pessimism
                          0.01    0.69   library hold time
                                  0.69   data required time
-----------------------------------------------------------------------------
                                  0.69   data required time
                                 -0.70   data arrival time
-----------------------------------------------------------------------------
                                  0.01   slack (MET)



```

### Path 3

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2_nohash_softmax_pipe1/attention_dual_stream_composed_v1_hier/6_finish.rpt`
- stage: `finish`
- startpoint: `rst_n (input port clocked by clk)`
- endpoint: `score_mix_1_out[2]$_DFFE_PN0P_`
- path_group: `asynchronous`
- path_type: `min`
- slack: `1.2600`
- data_arrival_time: `2.0800`
- data_required_time: `0.8200`

```text
Startpoint: rst_n (input port clocked by clk)
Endpoint: score_mix_1_out[2]$_DFFE_PN0P_
          (removal check against rising-edge clock clk)
Path Group: asynchronous
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (propagated)
                          2.00    2.00 ^ input external delay
     1    4.58    0.00    0.00    2.00 ^ rst_n (in)
                                         rst_n (net)
                  0.00    0.00    2.00 ^ input345/A (CLKBUF_X3)
    12   51.30    0.02    0.04    2.04 ^ input345/Z (CLKBUF_X3)
                                         net344 (net)
                  0.06    0.04    2.08 ^ score_mix_1_out[2]$_DFFE_PN0P_/RN (DFFR_X1)
                                  2.08   data arrival time

                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   12.69    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.00    0.00    0.00 ^ wire46768/A (BUF_X8)
...
                                         clknet_3_2_0_clk (net)
                  0.03    0.00    0.44 ^ clkbuf_5_8_0_clk/A (CLKBUF_X3)
    19   52.32    0.04    0.08    0.51 ^ clkbuf_5_8_0_clk/Z (CLKBUF_X3)
                                         clknet_5_8_0_clk (net)
                  0.04    0.00    0.52 ^ clkbuf_leaf_341_clk/A (CLKBUF_X3)
     7   11.03    0.01    0.05    0.57 ^ clkbuf_leaf_341_clk/Z (CLKBUF_X3)
                                         clknet_leaf_341_clk (net)
                  0.01    0.00    0.57 ^ score_mix_1_out[2]$_DFFE_PN0P_/CK (DFFR_X1)
                          0.00    0.57   clock reconvergence pessimism
                          0.26    0.82   library removal time
                                  0.82   data required time
-----------------------------------------------------------------------------
                                  0.82   data required time
                                 -2.08   data arrival time
-----------------------------------------------------------------------------
                                  1.26   slack (MET)
```

### Path 4

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2_nohash_softmax_pipe1/attention_dual_stream_composed_v1_hier/6_finish.rpt`
- stage: `finish`
- startpoint: `rst_n (input port clocked by clk)`
- endpoint: `stream_buf_0_pipe_1[925]$_DFF_PN0_`
- path_group: `asynchronous`
- path_type: `max`
- slack: `7.6700`
- data_arrival_time: `2.9600`
- data_required_time: `10.6300`

```text
Startpoint: rst_n (input port clocked by clk)
Endpoint: stream_buf_0_pipe_1[925]$_DFF_PN0_
          (recovery check against rising-edge clock clk)
Path Group: asynchronous
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (propagated)
                          2.00    2.00 ^ input external delay
     1    4.58    0.00    0.00    2.00 ^ rst_n (in)
                                         rst_n (net)
                  0.00    0.00    2.00 ^ input345/A (CLKBUF_X3)
    12   51.30    0.02    0.04    2.04 ^ input345/Z (CLKBUF_X3)
                                         net344 (net)
                  0.06    0.04    2.09 ^ place46588/A (BUF_X1)
     3   15.70    0.04    0.06    2.15 ^ place46588/Z (BUF_X1)
                                         net46587 (net)
                  0.04    0.00    2.15 ^ place46636/A (BUF_X1)
     3   28.48    0.06    0.09    2.24 ^ place46636/Z (BUF_X1)
                                         net46635 (net)
                  0.06    0.01    2.25 ^ place46637/A (BUF_X2)
    17   47.41    0.05    0.08    2.33 ^ place46637/Z (BUF_X2)
...
                                         clknet_3_7_0_clk (net)
                  0.04    0.01   10.47 ^ clkbuf_5_30_0_clk/A (CLKBUF_X3)
    10   44.82    0.04    0.07   10.55 ^ clkbuf_5_30_0_clk/Z (CLKBUF_X3)
                                         clknet_5_30_0_clk (net)
                  0.04    0.00   10.55 ^ clkbuf_leaf_127_clk/A (CLKBUF_X3)
     5    8.94    0.01    0.04   10.59 ^ clkbuf_leaf_127_clk/Z (CLKBUF_X3)
                                         clknet_leaf_127_clk (net)
                  0.01    0.00   10.59 ^ stream_buf_0_pipe_1[925]$_DFF_PN0_/CK (DFFR_X1)
                          0.00   10.59   clock reconvergence pessimism
                          0.04   10.63   library recovery time
                                 10.63   data required time
-----------------------------------------------------------------------------
                                 10.63   data required time
                                 -2.96   data arrival time
-----------------------------------------------------------------------------
                                  7.67   slack (MET)
```


## Worst Timing Paths Across All Stages

### Path 1

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2_nohash_softmax_pipe1/attention_dual_stream_composed_v1_hier/2_floorplan_final.rpt`
- stage: `floorplan`
- startpoint: `softmax_scores_pipe_0[9]$_DFF_PN0_`
- endpoint: `u_softmax/weights[40]$_SDFF_PN1_`
- path_group: `clk`
- path_type: `max`
- slack: `-17.5700`
- data_arrival_time: `27.5300`
- data_required_time: `9.9600`

```text
Startpoint: softmax_scores_pipe_0[9]$_DFF_PN0_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: u_softmax/weights[40]$_SDFF_PN1_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                  0.00    0.00    0.00 ^ softmax_scores_pipe_0[9]$_DFF_PN0_/CK (DFFR_X1)
     2    5.15    0.02    0.11    0.11 ^ softmax_scores_pipe_0[9]$_DFF_PN0_/Q (DFFR_X1)
                                         softmax_scores_pipe_0[9] (net)
                  0.02    0.00    0.11 ^ u_softmax/_77546_/B (HA_X1)
     2    3.31    0.03    0.06    0.16 ^ u_softmax/_77546_/S (HA_X1)
                                         u_softmax/_01975_ (net)
                  0.03    0.00    0.16 ^ u_softmax/_43708_/B2 (AOI21_X1)
     1    1.46    0.01    0.02    0.18 v u_softmax/_43708_/ZN (AOI21_X1)
                                         u_softmax/_14979_ (net)
                  0.01    0.00    0.18 v u_softmax/_43710_/B1 (OAI21_X1)
     1    1.65    0.02    0.03    0.21 ^ u_softmax/_43710_/ZN (OAI21_X1)
                                         u_softmax/_14981_ (net)
                  0.02    0.00    0.21 ^ u_softmax/_43711_/B1 (AOI21_X1)
...
                                 27.53   data arrival time

                  0.00   10.00   10.00   clock clk (rise edge)
                          0.00   10.00   clock network delay (ideal)
                          0.00   10.00   clock reconvergence pessimism
                                 10.00 ^ u_softmax/weights[40]$_SDFF_PN1_/CK (DFF_X1)
                         -0.04    9.96   library setup time
                                  9.96   data required time
-----------------------------------------------------------------------------
                                  9.96   data required time
                                -27.53   data arrival time
-----------------------------------------------------------------------------
                                -17.57   slack (VIOLATED)



```

### Path 2

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2_nohash_softmax_pipe1/attention_dual_stream_composed_v1_hier/3_global_place.rpt`
- stage: `global_place`
- startpoint: `softmax_scores_pipe_0[1]$_DFF_PN0_`
- endpoint: `u_softmax/weights[40]$_SDFF_PN1_`
- path_group: `clk`
- path_type: `max`
- slack: `-13.4900`
- data_arrival_time: `23.4400`
- data_required_time: `9.9500`

```text
Startpoint: softmax_scores_pipe_0[1]$_DFF_PN0_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: u_softmax/weights[40]$_SDFF_PN1_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                  0.00    0.00    0.00 ^ softmax_scores_pipe_0[1]$_DFF_PN0_/CK (DFFR_X1)
     2    3.69    0.01    0.09    0.09 v softmax_scores_pipe_0[1]$_DFF_PN0_/Q (DFFR_X1)
                                         softmax_scores_pipe_0[1] (net)
                  0.01    0.00    0.09 v u_softmax/_43734_/A (INV_X1)
     2    5.29    0.01    0.02    0.11 ^ u_softmax/_43734_/ZN (INV_X1)
                                         u_softmax/_01973_ (net)
                  0.01    0.00    0.11 ^ u_softmax/_77546_/A (HA_X1)
     2    4.59    0.03    0.06    0.17 ^ u_softmax/_77546_/S (HA_X1)
                                         u_softmax/_01975_ (net)
                  0.03    0.00    0.17 ^ u_softmax/_43708_/B2 (AOI21_X1)
     1    1.98    0.01    0.02    0.19 v u_softmax/_43708_/ZN (AOI21_X1)
                                         u_softmax/_14979_ (net)
                  0.01    0.00    0.19 v u_softmax/_43710_/B1 (OAI21_X1)
...
                                 23.44   data arrival time

                  0.00   10.00   10.00   clock clk (rise edge)
                          0.00   10.00   clock network delay (ideal)
                          0.00   10.00   clock reconvergence pessimism
                                 10.00 ^ u_softmax/weights[40]$_SDFF_PN1_/CK (DFF_X1)
                         -0.05    9.95   library setup time
                                  9.95   data required time
-----------------------------------------------------------------------------
                                  9.95   data required time
                                -23.44   data arrival time
-----------------------------------------------------------------------------
                                -13.49   slack (VIOLATED)



```

### Path 3

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2_nohash_softmax_pipe1/attention_dual_stream_composed_v1_hier/3_resizer.rpt`
- stage: `resizer`
- startpoint: `softmax_scores_pipe_0[1]$_DFF_PN0_`
- endpoint: `u_softmax/weights[40]$_SDFF_PN1_`
- path_group: `clk`
- path_type: `max`
- slack: `-13.4900`
- data_arrival_time: `23.4400`
- data_required_time: `9.9500`

```text
Startpoint: softmax_scores_pipe_0[1]$_DFF_PN0_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: u_softmax/weights[40]$_SDFF_PN1_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                  0.00    0.00    0.00 ^ softmax_scores_pipe_0[1]$_DFF_PN0_/CK (DFFR_X1)
     2    3.69    0.01    0.09    0.09 v softmax_scores_pipe_0[1]$_DFF_PN0_/Q (DFFR_X1)
                                         softmax_scores_pipe_0[1] (net)
                  0.01    0.00    0.09 v u_softmax/_43734_/A (INV_X1)
     2    5.29    0.01    0.02    0.11 ^ u_softmax/_43734_/ZN (INV_X1)
                                         u_softmax/_01973_ (net)
                  0.01    0.00    0.11 ^ u_softmax/_77546_/A (HA_X1)
     2    4.59    0.03    0.06    0.17 ^ u_softmax/_77546_/S (HA_X1)
                                         u_softmax/_01975_ (net)
                  0.03    0.00    0.17 ^ u_softmax/_43708_/B2 (AOI21_X1)
     1    1.98    0.01    0.02    0.19 v u_softmax/_43708_/ZN (AOI21_X1)
                                         u_softmax/_14979_ (net)
                  0.01    0.00    0.19 v u_softmax/_43710_/B1 (OAI21_X1)
...
                                 23.44   data arrival time

                  0.00   10.00   10.00   clock clk (rise edge)
                          0.00   10.00   clock network delay (ideal)
                          0.00   10.00   clock reconvergence pessimism
                                 10.00 ^ u_softmax/weights[40]$_SDFF_PN1_/CK (DFF_X1)
                         -0.05    9.95   library setup time
                                  9.95   data required time
-----------------------------------------------------------------------------
                                  9.95   data required time
                                -23.44   data arrival time
-----------------------------------------------------------------------------
                                -13.49   slack (VIOLATED)



```

### Path 4

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2_nohash_softmax_pipe1/attention_dual_stream_composed_v1_hier/3_detailed_place.rpt`
- stage: `detailed_place`
- startpoint: `softmax_scores_pipe_0[1]$_DFF_PN0_`
- endpoint: `u_softmax/weights[40]$_SDFF_PN1_`
- path_group: `clk`
- path_type: `max`
- slack: `-12.9400`
- data_arrival_time: `22.8900`
- data_required_time: `9.9500`

```text
Startpoint: softmax_scores_pipe_0[1]$_DFF_PN0_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: u_softmax/weights[40]$_SDFF_PN1_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                  0.00    0.00    0.00 ^ softmax_scores_pipe_0[1]$_DFF_PN0_/CK (DFFR_X1)
     2    2.92    0.01    0.09    0.09 v softmax_scores_pipe_0[1]$_DFF_PN0_/Q (DFFR_X1)
                                         softmax_scores_pipe_0[1] (net)
                  0.01    0.00    0.09 v u_softmax/_43734_/A (INV_X1)
     2    5.13    0.01    0.02    0.11 ^ u_softmax/_43734_/ZN (INV_X1)
                                         u_softmax/_01973_ (net)
                  0.01    0.00    0.11 ^ u_softmax/_77546_/A (HA_X1)
     2    4.03    0.03    0.06    0.17 ^ u_softmax/_77546_/S (HA_X1)
                                         u_softmax/_01975_ (net)
                  0.03    0.00    0.17 ^ u_softmax/_43708_/B2 (AOI21_X1)
     1    2.03    0.01    0.02    0.19 v u_softmax/_43708_/ZN (AOI21_X1)
                                         u_softmax/_14979_ (net)
                  0.01    0.00    0.19 v u_softmax/_43710_/B1 (OAI21_X1)
...
                                 22.89   data arrival time

                  0.00   10.00   10.00   clock clk (rise edge)
                          0.00   10.00   clock network delay (ideal)
                          0.00   10.00   clock reconvergence pessimism
                                 10.00 ^ u_softmax/weights[40]$_SDFF_PN1_/CK (DFF_X1)
                         -0.05    9.95   library setup time
                                  9.95   data required time
-----------------------------------------------------------------------------
                                  9.95   data required time
                                -22.89   data arrival time
-----------------------------------------------------------------------------
                                -12.94   slack (VIOLATED)



```

### Path 5

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2_nohash_softmax_pipe1/attention_dual_stream_composed_v1_hier/5_global_route.rpt`
- stage: `route`
- startpoint: `softmax_scores_pipe_0[9]$_DFF_PN0_`
- endpoint: `u_softmax/weights[56]$_SDFF_PN1_`
- path_group: `clk`
- path_type: `max`
- slack: `-12.4200`
- data_arrival_time: `23.0300`
- data_required_time: `10.6100`

```text
Startpoint: softmax_scores_pipe_0[9]$_DFF_PN0_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: u_softmax/weights[56]$_SDFF_PN1_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   16.72    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.00    0.00    0.00 ^ wire46768/A (BUF_X8)
     1   69.70    0.01    0.03    0.03 ^ wire46768/Z (BUF_X8)
                                         net46767 (net)
                  0.04    0.03    0.06 ^ wire46767/A (BUF_X16)
     1   58.42    0.01    0.03    0.08 ^ wire46767/Z (BUF_X16)
                                         net46766 (net)
                  0.03    0.02    0.10 ^ clkbuf_0_clk/A (CLKBUF_X3)
     2   42.31    0.03    0.07    0.17 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.03    0.00    0.18 ^ clkbuf_1_1_0_clk/A (CLKBUF_X3)
     1   27.23    0.02    0.06    0.23 ^ clkbuf_1_1_0_clk/Z (CLKBUF_X3)
...
                                         clknet_5_23_0_clk (net)
                  0.06    0.04   10.58 ^ clkbuf_leaf_117_clk/A (CLKBUF_X3)
     3   24.77    0.02    0.07   10.65 ^ clkbuf_leaf_117_clk/Z (CLKBUF_X3)
                                         clknet_leaf_117_clk (net)
                  0.02    0.00   10.65 ^ u_softmax/weights[56]$_SDFF_PN1_/CK (DFF_X2)
                          0.00   10.65   clock reconvergence pessimism
                         -0.04   10.61   library setup time
                                 10.61   data required time
-----------------------------------------------------------------------------
                                 10.61   data required time
                                -23.03   data arrival time
-----------------------------------------------------------------------------
                                -12.42   slack (VIOLATED)



```

### Path 6

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2_nohash_softmax_pipe1/attention_dual_stream_composed_v1_hier/4_cts_final.rpt`
- stage: `cts`
- startpoint: `softmax_scores_pipe_0[9]$_DFF_PN0_`
- endpoint: `u_softmax/weights[56]$_SDFF_PN1_`
- path_group: `clk`
- path_type: `max`
- slack: `-12.2400`
- data_arrival_time: `22.8600`
- data_required_time: `10.6200`

```text
Startpoint: softmax_scores_pipe_0[9]$_DFF_PN0_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: u_softmax/weights[56]$_SDFF_PN1_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   16.73    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.00    0.00    0.00 ^ wire46768/A (BUF_X8)
     1   70.22    0.02    0.03    0.03 ^ wire46768/Z (BUF_X8)
                                         net46767 (net)
                  0.04    0.03    0.06 ^ wire46767/A (BUF_X16)
     1   62.60    0.01    0.03    0.09 ^ wire46767/Z (BUF_X16)
                                         net46766 (net)
                  0.03    0.02    0.11 ^ clkbuf_0_clk/A (CLKBUF_X3)
     2   42.50    0.03    0.07    0.18 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.03    0.00    0.18 ^ clkbuf_1_1_0_clk/A (CLKBUF_X3)
     1   27.32    0.02    0.06    0.24 ^ clkbuf_1_1_0_clk/Z (CLKBUF_X3)
...
                                         clknet_5_23_0_clk (net)
                  0.07    0.04   10.59 ^ clkbuf_leaf_117_clk/A (CLKBUF_X3)
     3   22.84    0.02    0.06   10.66 ^ clkbuf_leaf_117_clk/Z (CLKBUF_X3)
                                         clknet_leaf_117_clk (net)
                  0.02    0.00   10.66 ^ u_softmax/weights[56]$_SDFF_PN1_/CK (DFF_X2)
                          0.00   10.66   clock reconvergence pessimism
                         -0.04   10.62   library setup time
                                 10.62   data required time
-----------------------------------------------------------------------------
                                 10.62   data required time
                                -22.86   data arrival time
-----------------------------------------------------------------------------
                                -12.24   slack (VIOLATED)



```

### Path 7

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2_nohash_softmax_pipe1/attention_dual_stream_composed_v1_hier/6_finish.rpt`
- stage: `finish`
- startpoint: `softmax_scores_pipe_0[9]$_DFF_PN0_`
- endpoint: `u_softmax/weights[56]$_SDFF_PN1_`
- path_group: `clk`
- path_type: `max`
- slack: `-12.2000`
- data_arrival_time: `22.7900`
- data_required_time: `10.5900`

```text
Startpoint: softmax_scores_pipe_0[9]$_DFF_PN0_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: u_softmax/weights[56]$_SDFF_PN1_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   12.69    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.00    0.00    0.00 ^ wire46768/A (BUF_X8)
     1   54.48    0.01    0.02    0.02 ^ wire46768/Z (BUF_X8)
                                         net46767 (net)
                  0.03    0.02    0.05 ^ wire46767/A (BUF_X16)
     1   72.24    0.01    0.03    0.07 ^ wire46767/Z (BUF_X16)
                                         net46766 (net)
                  0.04    0.03    0.10 ^ clkbuf_0_clk/A (CLKBUF_X3)
     2   38.71    0.03    0.07    0.17 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.03    0.00    0.18 ^ clkbuf_1_1_0_clk/A (CLKBUF_X3)
     1   26.53    0.02    0.06    0.23 ^ clkbuf_1_1_0_clk/Z (CLKBUF_X3)
...
                                         clknet_5_23_0_clk (net)
                  0.06    0.04   10.56 ^ clkbuf_leaf_117_clk/A (CLKBUF_X3)
     3   22.61    0.02    0.06   10.63 ^ clkbuf_leaf_117_clk/Z (CLKBUF_X3)
                                         clknet_leaf_117_clk (net)
                  0.02    0.00   10.63 ^ u_softmax/weights[56]$_SDFF_PN1_/CK (DFF_X2)
                          0.00   10.63   clock reconvergence pessimism
                         -0.04   10.59   library setup time
                                 10.59   data required time
-----------------------------------------------------------------------------
                                 10.59   data required time
                                -22.79   data arrival time
-----------------------------------------------------------------------------
                                -12.20   slack (VIOLATED)



```

### Path 8

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2_nohash_softmax_pipe1/attention_dual_stream_composed_v1_hier/6_finish.rpt`
- stage: `finish`
- startpoint: `stream_buf_0_pipe_1[92]$_DFF_PN0_`
- endpoint: `stream_buf_0_pipe_1[124]$_DFF_PN0_`
- path_group: `clk`
- path_type: `min`
- slack: `0.0100`
- data_arrival_time: `0.7000`
- data_required_time: `0.6900`

```text
Startpoint: stream_buf_0_pipe_1[92]$_DFF_PN0_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: stream_buf_0_pipe_1[124]$_DFF_PN0_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   12.69    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.00    0.00    0.00 ^ wire46768/A (BUF_X8)
     1   54.48    0.01    0.02    0.02 ^ wire46768/Z (BUF_X8)
                                         net46767 (net)
                  0.03    0.02    0.05 ^ wire46767/A (BUF_X16)
     1   72.24    0.01    0.03    0.07 ^ wire46767/Z (BUF_X16)
                                         net46766 (net)
                  0.04    0.03    0.10 ^ clkbuf_0_clk/A (CLKBUF_X3)
     2   38.71    0.03    0.07    0.17 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.03    0.00    0.18 ^ clkbuf_1_0_0_clk/A (CLKBUF_X3)
     1   31.06    0.02    0.06    0.23 ^ clkbuf_1_0_0_clk/Z (CLKBUF_X3)
...
                                         clknet_5_0_0_clk (net)
                  0.08    0.01    0.62 ^ clkbuf_leaf_297_clk/A (CLKBUF_X3)
     7   12.74    0.02    0.06    0.68 ^ clkbuf_leaf_297_clk/Z (CLKBUF_X3)
                                         clknet_leaf_297_clk (net)
                  0.02    0.00    0.68 ^ stream_buf_0_pipe_1[124]$_DFF_PN0_/CK (DFFR_X1)
                          0.00    0.68   clock reconvergence pessimism
                          0.01    0.69   library hold time
                                  0.69   data required time
-----------------------------------------------------------------------------
                                  0.69   data required time
                                 -0.70   data arrival time
-----------------------------------------------------------------------------
                                  0.01   slack (MET)



```
