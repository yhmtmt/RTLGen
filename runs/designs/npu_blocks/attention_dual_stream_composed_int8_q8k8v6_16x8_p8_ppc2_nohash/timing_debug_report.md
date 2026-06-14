# OpenROAD Timing Debug Summary

- design_dir: `runs/designs/npu_blocks/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2_nohash`
- metrics_path: `runs/designs/npu_blocks/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2_nohash/metrics.csv`
- rows_considered: 2

## Metrics Rows

| param_hash | tag | status | critical_path_ns | density | result_path |
| --- | --- | --- | ---: | ---: | --- |
| 40317f7f | attention_dual_stream_composed_v1_hier | ok | 23.1995 | 0.4 | `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2_nohash/attention_dual_stream_composed_v1_hier/6_finish.rpt` |
| 81f459d1 | attention_dual_stream_composed_v1_hier | ok | 23.6862 | 0.3 | `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2_nohash/attention_dual_stream_composed_v1_hier/6_finish.rpt` |

## Inspected Report Files

- `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2_nohash/attention_dual_stream_composed_v1_hier/6_finish.rpt`
- `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2_nohash/attention_dual_stream_composed_v1_hier/5_global_route.rpt`
- `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2_nohash/attention_dual_stream_composed_v1_hier/5_route_drc.rpt`
- `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2_nohash/attention_dual_stream_composed_v1_hier/4_cts_final.rpt`
- `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2_nohash/attention_dual_stream_composed_v1_hier/3_resizer.rpt`
- `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2_nohash/attention_dual_stream_composed_v1_hier/3_detailed_place.rpt`
- `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2_nohash/attention_dual_stream_composed_v1_hier/3_global_place.rpt`
- `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2_nohash/attention_dual_stream_composed_v1_hier/2_floorplan_final.rpt`
- `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2_nohash/attention_dual_stream_composed_v1_hier/drt_antennas.log`
- `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2_nohash/attention_dual_stream_composed_v1_hier/grt_antennas.log`
- `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2_nohash/attention_dual_stream_composed_v1_hier/metadata-generate.log`

## Preferred Final-Stage Timing Paths

- raw_path_block_count: 104
- unique_path_block_count: 28
- preferred_stage: `finish`

### Path 1

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2_nohash/attention_dual_stream_composed_v1_hier/6_finish.rpt`
- stage: `finish`
- startpoint: `seed_state[1]$_DFF_PN0_`
- endpoint: `u_softmax/weights[56]$_SDFF_PN1_`
- path_group: `clk`
- path_type: `max`
- slack: `-12.6700`
- data_arrival_time: `23.2000`
- data_required_time: `10.5300`

```text
Startpoint: seed_state[1]$_DFF_PN0_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: u_softmax/weights[56]$_SDFF_PN1_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   48.93    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.02    0.02    0.02 ^ wire79114/A (BUF_X16)
     1   50.07    0.01    0.02    0.04 ^ wire79114/Z (BUF_X16)
                                         net79113 (net)
                  0.02    0.02    0.06 ^ wire79113/A (BUF_X16)
     1   47.51    0.01    0.02    0.09 ^ wire79113/Z (BUF_X16)
                                         net79112 (net)
                  0.02    0.02    0.11 ^ clkbuf_0_clk/A (CLKBUF_X3)
     2   20.44    0.02    0.05    0.15 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.02    0.00    0.16 ^ clkbuf_1_1_0_clk/A (CLKBUF_X3)
     1   33.48    0.03    0.05    0.21 ^ clkbuf_1_1_0_clk/Z (CLKBUF_X3)
...
                                         clknet_5_13__leaf_clk (net)
                  0.04    0.00   10.51 ^ clkbuf_leaf_1_clk/A (CLKBUF_X3)
     3   13.31    0.01    0.05   10.57 ^ clkbuf_leaf_1_clk/Z (CLKBUF_X3)
                                         clknet_leaf_1_clk (net)
                  0.01    0.00   10.57 ^ u_softmax/weights[56]$_SDFF_PN1_/CK (DFF_X1)
                          0.00   10.57   clock reconvergence pessimism
                         -0.03   10.53   library setup time
                                 10.53   data required time
-----------------------------------------------------------------------------
                                 10.53   data required time
                                -23.20   data arrival time
-----------------------------------------------------------------------------
                                -12.67   slack (VIOLATED)



```

### Path 2

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2_nohash/attention_dual_stream_composed_v1_hier/6_finish.rpt`
- stage: `finish`
- startpoint: `seed_state[28]$_DFF_PN0_`
- endpoint: `stream_buf_1[28]$_DFF_PN0_`
- path_group: `clk`
- path_type: `min`
- slack: `0.0600`
- data_arrival_time: `0.6300`
- data_required_time: `0.5700`

```text
Startpoint: seed_state[28]$_DFF_PN0_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: stream_buf_1[28]$_DFF_PN0_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   48.93    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.02    0.02    0.02 ^ wire79114/A (BUF_X16)
     1   50.07    0.01    0.02    0.04 ^ wire79114/Z (BUF_X16)
                                         net79113 (net)
                  0.02    0.02    0.06 ^ wire79113/A (BUF_X16)
     1   47.51    0.01    0.02    0.09 ^ wire79113/Z (BUF_X16)
                                         net79112 (net)
                  0.02    0.02    0.11 ^ clkbuf_0_clk/A (CLKBUF_X3)
     2   20.44    0.02    0.05    0.15 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.02    0.00    0.16 ^ clkbuf_1_1_0_clk/A (CLKBUF_X3)
     1   33.48    0.03    0.05    0.21 ^ clkbuf_1_1_0_clk/Z (CLKBUF_X3)
...
                                         clknet_5_24__leaf_clk (net)
                  0.03    0.00    0.51 ^ clkbuf_leaf_299_clk/A (CLKBUF_X3)
     5   14.49    0.01    0.05    0.56 ^ clkbuf_leaf_299_clk/Z (CLKBUF_X3)
                                         clknet_leaf_299_clk (net)
                  0.01    0.00    0.56 ^ stream_buf_1[28]$_DFF_PN0_/CK (DFFR_X2)
                          0.00    0.56   clock reconvergence pessimism
                          0.01    0.57   library hold time
                                  0.57   data required time
-----------------------------------------------------------------------------
                                  0.57   data required time
                                 -0.63   data arrival time
-----------------------------------------------------------------------------
                                  0.06   slack (MET)



```

### Path 3

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2_nohash/attention_dual_stream_composed_v1_hier/6_finish.rpt`
- stage: `finish`
- startpoint: `rst_n (input port clocked by clk)`
- endpoint: `stream_buf_0[294]$_DFF_PN0_`
- path_group: `asynchronous`
- path_type: `min`
- slack: `1.3400`
- data_arrival_time: `2.2100`
- data_required_time: `0.8700`

```text
Startpoint: rst_n (input port clocked by clk)
Endpoint: stream_buf_0[294]$_DFF_PN0_
          (removal check against rising-edge clock clk)
Path Group: asynchronous
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (propagated)
                          2.00    2.00 ^ input external delay
     1   36.03    0.00    0.00    2.00 ^ rst_n (in)
                                         rst_n (net)
                  0.01    0.01    2.01 ^ wire3839/A (CLKBUF_X3)
     1   17.40    0.02    0.04    2.05 ^ wire3839/Z (CLKBUF_X3)
                                         net3838 (net)
                  0.02    0.01    2.06 ^ place78938/A (BUF_X1)
     1    1.75    0.01    0.03    2.08 ^ place78938/Z (BUF_X1)
                                         net78937 (net)
                  0.01    0.00    2.08 ^ wire79097/A (CLKBUF_X3)
     2   46.34    0.03    0.05    2.13 ^ wire79097/Z (CLKBUF_X3)
                                         net79096 (net)
                  0.04    0.02    2.15 ^ load_slew79096/A (CLKBUF_X3)
     5   24.14    0.02    0.06    2.21 ^ load_slew79096/Z (CLKBUF_X3)
...
                                         clknet_4_11_0_clk (net)
                  0.03    0.00    0.49 ^ clkbuf_5_23__f_clk/A (CLKBUF_X3)
    14   96.78    0.07    0.11    0.60 ^ clkbuf_5_23__f_clk/Z (CLKBUF_X3)
                                         clknet_5_23__leaf_clk (net)
                  0.07    0.01    0.60 ^ clkbuf_leaf_217_clk/A (CLKBUF_X3)
     4   10.31    0.01    0.06    0.66 ^ clkbuf_leaf_217_clk/Z (CLKBUF_X3)
                                         clknet_leaf_217_clk (net)
                  0.01    0.00    0.66 ^ stream_buf_0[294]$_DFF_PN0_/CK (DFFR_X1)
                          0.00    0.66   clock reconvergence pessimism
                          0.21    0.87   library removal time
                                  0.87   data required time
-----------------------------------------------------------------------------
                                  0.87   data required time
                                 -2.21   data arrival time
-----------------------------------------------------------------------------
                                  1.34   slack (MET)
```

### Path 4

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2_nohash/attention_dual_stream_composed_v1_hier/6_finish.rpt`
- stage: `finish`
- startpoint: `rst_n (input port clocked by clk)`
- endpoint: `stream_buf_0[755]$_DFF_PN0_`
- path_group: `asynchronous`
- path_type: `max`
- slack: `7.6700`
- data_arrival_time: `2.9800`
- data_required_time: `10.6500`

```text
Startpoint: rst_n (input port clocked by clk)
Endpoint: stream_buf_0[755]$_DFF_PN0_
          (recovery check against rising-edge clock clk)
Path Group: asynchronous
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (propagated)
                          2.00    2.00 ^ input external delay
     1   36.03    0.00    0.00    2.00 ^ rst_n (in)
                                         rst_n (net)
                  0.01    0.01    2.01 ^ wire3839/A (CLKBUF_X3)
     1   17.40    0.02    0.04    2.05 ^ wire3839/Z (CLKBUF_X3)
                                         net3838 (net)
                  0.02    0.01    2.06 ^ place78938/A (BUF_X1)
     1    1.75    0.01    0.03    2.08 ^ place78938/Z (BUF_X1)
                                         net78937 (net)
                  0.01    0.00    2.08 ^ wire79097/A (CLKBUF_X3)
     2   46.34    0.03    0.05    2.13 ^ wire79097/Z (CLKBUF_X3)
                                         net79096 (net)
                  0.04    0.02    2.15 ^ load_slew79096/A (CLKBUF_X3)
     5   24.14    0.02    0.06    2.21 ^ load_slew79096/Z (CLKBUF_X3)
...
                                         clknet_4_8_0_clk (net)
                  0.02    0.00   10.48 ^ clkbuf_5_17__f_clk/A (CLKBUF_X3)
    13   57.60    0.04    0.08   10.56 ^ clkbuf_5_17__f_clk/Z (CLKBUF_X3)
                                         clknet_5_17__leaf_clk (net)
                  0.04    0.00   10.56 ^ clkbuf_leaf_150_clk/A (CLKBUF_X3)
     5    7.63    0.01    0.05   10.60 ^ clkbuf_leaf_150_clk/Z (CLKBUF_X3)
                                         clknet_leaf_150_clk (net)
                  0.01    0.00   10.60 ^ stream_buf_0[755]$_DFF_PN0_/CK (DFFR_X1)
                          0.00   10.60   clock reconvergence pessimism
                          0.05   10.65   library recovery time
                                 10.65   data required time
-----------------------------------------------------------------------------
                                 10.65   data required time
                                 -2.98   data arrival time
-----------------------------------------------------------------------------
                                  7.67   slack (MET)
```


## Worst Timing Paths Across All Stages

### Path 1

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2_nohash/attention_dual_stream_composed_v1_hier/2_floorplan_final.rpt`
- stage: `floorplan`
- startpoint: `seed_state[3]$_DFF_PN0_`
- endpoint: `u_softmax/weights[16]$_SDFF_PN1_`
- path_group: `clk`
- path_type: `max`
- slack: `-18.0500`
- data_arrival_time: `28.0100`
- data_required_time: `9.9600`

```text
Startpoint: seed_state[3]$_DFF_PN0_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: u_softmax/weights[16]$_SDFF_PN1_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                  0.00    0.00    0.00 ^ seed_state[3]$_DFF_PN0_/CK (DFFR_X2)
    10   26.52    0.03    0.15    0.15 ^ seed_state[3]$_DFF_PN0_/Q (DFFR_X2)
                                         seed_state[3] (net)
                  0.03    0.00    0.15 ^ _08964_/A (XOR2_X2)
     5   15.32    0.05    0.08    0.23 ^ _08964_/Z (XOR2_X2)
                                         _00285_ (net)
                  0.05    0.00    0.23 ^ _15806_/A (BUF_X8)
    10   35.55    0.01    0.04    0.27 ^ _15806_/Z (BUF_X8)
                                         _06650_ (net)
                  0.01    0.00    0.27 ^ _17335_/A (BUF_X8)
    10   25.74    0.01    0.03    0.30 ^ _17335_/Z (BUF_X8)
                                         _07319_ (net)
                  0.01    0.00    0.30 ^ _17431_/B (XNOR2_X1)
...
                                 28.01   data arrival time

                  0.00   10.00   10.00   clock clk (rise edge)
                          0.00   10.00   clock network delay (ideal)
                          0.00   10.00   clock reconvergence pessimism
                                 10.00 ^ u_softmax/weights[16]$_SDFF_PN1_/CK (DFF_X1)
                         -0.04    9.96   library setup time
                                  9.96   data required time
-----------------------------------------------------------------------------
                                  9.96   data required time
                                -28.01   data arrival time
-----------------------------------------------------------------------------
                                -18.05   slack (VIOLATED)



```

### Path 2

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2_nohash/attention_dual_stream_composed_v1_hier/3_global_place.rpt`
- stage: `global_place`
- startpoint: `seed_state[9]$_DFF_PN0_`
- endpoint: `u_softmax/weights[48]$_SDFF_PN1_`
- path_group: `clk`
- path_type: `max`
- slack: `-14.0100`
- data_arrival_time: `23.9700`
- data_required_time: `9.9500`

```text
Startpoint: seed_state[9]$_DFF_PN0_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: u_softmax/weights[48]$_SDFF_PN1_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                  0.00    0.00    0.00 ^ seed_state[9]$_DFF_PN0_/CK (DFFR_X2)
     2    6.03    0.01    0.13    0.13 ^ seed_state[9]$_DFF_PN0_/Q (DFFR_X2)
                                         seed_state[9] (net)
                  0.01    0.00    0.13 ^ place78607/A (BUF_X1)
     2    5.83    0.02    0.03    0.17 ^ place78607/Z (BUF_X1)
                                         net78606 (net)
                  0.02    0.00    0.17 ^ _09014_/A (XOR2_X2)
     2   10.26    0.04    0.07    0.23 ^ _09014_/Z (XOR2_X2)
                                         _00325_ (net)
                  0.04    0.00    0.23 ^ place74680/A (BUF_X8)
     3   36.64    0.01    0.03    0.26 ^ place74680/Z (BUF_X8)
                                         net74679 (net)
                  0.02    0.02    0.28 ^ place74681/A (BUF_X4)
...
                                 23.97   data arrival time

                  0.00   10.00   10.00   clock clk (rise edge)
                          0.00   10.00   clock network delay (ideal)
                          0.00   10.00   clock reconvergence pessimism
                                 10.00 ^ u_softmax/weights[48]$_SDFF_PN1_/CK (DFF_X1)
                         -0.05    9.95   library setup time
                                  9.95   data required time
-----------------------------------------------------------------------------
                                  9.95   data required time
                                -23.97   data arrival time
-----------------------------------------------------------------------------
                                -14.01   slack (VIOLATED)



```

### Path 3

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2_nohash/attention_dual_stream_composed_v1_hier/3_resizer.rpt`
- stage: `resizer`
- startpoint: `seed_state[9]$_DFF_PN0_`
- endpoint: `u_softmax/weights[48]$_SDFF_PN1_`
- path_group: `clk`
- path_type: `max`
- slack: `-13.9100`
- data_arrival_time: `23.8600`
- data_required_time: `9.9500`

```text
Startpoint: seed_state[9]$_DFF_PN0_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: u_softmax/weights[48]$_SDFF_PN1_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                  0.00    0.00    0.00 ^ seed_state[9]$_DFF_PN0_/CK (DFFR_X2)
     2    6.03    0.01    0.13    0.13 ^ seed_state[9]$_DFF_PN0_/Q (DFFR_X2)
                                         seed_state[9] (net)
                  0.01    0.00    0.13 ^ place78607/A (BUF_X1)
     2    5.83    0.02    0.03    0.17 ^ place78607/Z (BUF_X1)
                                         net78606 (net)
                  0.02    0.00    0.17 ^ _09014_/A (XOR2_X2)
     2   10.26    0.04    0.07    0.23 ^ _09014_/Z (XOR2_X2)
                                         _00325_ (net)
                  0.04    0.00    0.23 ^ place74680/A (BUF_X8)
     3   36.64    0.01    0.03    0.26 ^ place74680/Z (BUF_X8)
                                         net74679 (net)
                  0.02    0.02    0.28 ^ place74681/A (BUF_X4)
...
                                 23.86   data arrival time

                  0.00   10.00   10.00   clock clk (rise edge)
                          0.00   10.00   clock network delay (ideal)
                          0.00   10.00   clock reconvergence pessimism
                                 10.00 ^ u_softmax/weights[48]$_SDFF_PN1_/CK (DFF_X1)
                         -0.05    9.95   library setup time
                                  9.95   data required time
-----------------------------------------------------------------------------
                                  9.95   data required time
                                -23.86   data arrival time
-----------------------------------------------------------------------------
                                -13.91   slack (VIOLATED)



```

### Path 4

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2_nohash/attention_dual_stream_composed_v1_hier/3_detailed_place.rpt`
- stage: `detailed_place`
- startpoint: `cycle_ctr[9]$_DFF_PN0_`
- endpoint: `u_softmax/weights[40]$_SDFF_PN1_`
- path_group: `clk`
- path_type: `max`
- slack: `-13.6400`
- data_arrival_time: `23.6000`
- data_required_time: `9.9600`

```text
Startpoint: cycle_ctr[9]$_DFF_PN0_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: u_softmax/weights[40]$_SDFF_PN1_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                  0.00    0.00    0.00 ^ cycle_ctr[9]$_DFF_PN0_/CK (DFFR_X2)
     1    4.81    0.02    0.09    0.09 v cycle_ctr[9]$_DFF_PN0_/QN (DFFR_X2)
                                         _00070_ (net)
                  0.02    0.00    0.09 v _17951_/B (XOR2_X2)
     1    6.08    0.01    0.06    0.15 v _17951_/Z (XOR2_X2)
                                         _07381_ (net)
                  0.01    0.00    0.15 v place74159/A (BUF_X8)
     2   18.64    0.01    0.03    0.18 v place74159/Z (BUF_X8)
                                         net74158 (net)
                  0.01    0.00    0.18 v place74160/A (BUF_X2)
     3   19.98    0.01    0.03    0.22 v place74160/Z (BUF_X2)
                                         net74159 (net)
                  0.01    0.00    0.22 v place74162/A (BUF_X4)
...
                                 23.60   data arrival time

                  0.00   10.00   10.00   clock clk (rise edge)
                          0.00   10.00   clock network delay (ideal)
                          0.00   10.00   clock reconvergence pessimism
                                 10.00 ^ u_softmax/weights[40]$_SDFF_PN1_/CK (DFF_X1)
                         -0.04    9.96   library setup time
                                  9.96   data required time
-----------------------------------------------------------------------------
                                  9.96   data required time
                                -23.60   data arrival time
-----------------------------------------------------------------------------
                                -13.64   slack (VIOLATED)



```

### Path 5

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2_nohash/attention_dual_stream_composed_v1_hier/5_global_route.rpt`
- stage: `route`
- startpoint: `seed_state[1]$_DFF_PN0_`
- endpoint: `u_softmax/weights[56]$_SDFF_PN1_`
- path_group: `clk`
- path_type: `max`
- slack: `-12.7700`
- data_arrival_time: `23.3800`
- data_required_time: `10.6200`

```text
Startpoint: seed_state[1]$_DFF_PN0_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: u_softmax/weights[56]$_SDFF_PN1_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   70.38    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.03    0.02    0.02 ^ wire79114/A (BUF_X16)
     1   66.01    0.01    0.03    0.05 ^ wire79114/Z (BUF_X16)
                                         net79113 (net)
                  0.03    0.02    0.08 ^ wire79113/A (BUF_X16)
     1   66.81    0.01    0.03    0.10 ^ wire79113/Z (BUF_X16)
                                         net79112 (net)
                  0.03    0.03    0.13 ^ clkbuf_0_clk/A (CLKBUF_X3)
     2   27.12    0.02    0.06    0.19 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.02    0.01    0.19 ^ clkbuf_1_1_0_clk/A (CLKBUF_X3)
     1   26.28    0.02    0.05    0.24 ^ clkbuf_1_1_0_clk/Z (CLKBUF_X3)
...
                                         clknet_5_13__leaf_clk (net)
                  0.05    0.01   10.60 ^ clkbuf_leaf_1_clk/A (CLKBUF_X3)
     3   12.25    0.01    0.05   10.65 ^ clkbuf_leaf_1_clk/Z (CLKBUF_X3)
                                         clknet_leaf_1_clk (net)
                  0.01    0.00   10.65 ^ u_softmax/weights[56]$_SDFF_PN1_/CK (DFF_X1)
                          0.00   10.65   clock reconvergence pessimism
                         -0.03   10.62   library setup time
                                 10.62   data required time
-----------------------------------------------------------------------------
                                 10.62   data required time
                                -23.38   data arrival time
-----------------------------------------------------------------------------
                                -12.77   slack (VIOLATED)



```

### Path 6

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2_nohash/attention_dual_stream_composed_v1_hier/4_cts_final.rpt`
- stage: `cts`
- startpoint: `cycle_ctr[13]$_DFF_PN0_`
- endpoint: `u_softmax/weights[56]$_SDFF_PN1_`
- path_group: `clk`
- path_type: `max`
- slack: `-12.6700`
- data_arrival_time: `23.2800`
- data_required_time: `10.6100`

```text
Startpoint: cycle_ctr[13]$_DFF_PN0_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: u_softmax/weights[56]$_SDFF_PN1_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   72.45    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.03    0.02    0.02 ^ wire79114/A (BUF_X16)
     1   66.20    0.01    0.03    0.05 ^ wire79114/Z (BUF_X16)
                                         net79113 (net)
                  0.03    0.02    0.08 ^ wire79113/A (BUF_X16)
     1   67.10    0.01    0.03    0.10 ^ wire79113/Z (BUF_X16)
                                         net79112 (net)
                  0.03    0.02    0.13 ^ clkbuf_0_clk/A (CLKBUF_X3)
     2   26.70    0.02    0.06    0.18 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.02    0.00    0.19 ^ clkbuf_1_1_0_clk/A (CLKBUF_X3)
     1   27.41    0.02    0.05    0.24 ^ clkbuf_1_1_0_clk/Z (CLKBUF_X3)
...
                                         clknet_5_13__leaf_clk (net)
                  0.05    0.00   10.59 ^ clkbuf_leaf_1_clk/A (CLKBUF_X3)
     3   13.20    0.01    0.05   10.64 ^ clkbuf_leaf_1_clk/Z (CLKBUF_X3)
                                         clknet_leaf_1_clk (net)
                  0.01    0.00   10.64 ^ u_softmax/weights[56]$_SDFF_PN1_/CK (DFF_X1)
                          0.00   10.64   clock reconvergence pessimism
                         -0.03   10.61   library setup time
                                 10.61   data required time
-----------------------------------------------------------------------------
                                 10.61   data required time
                                -23.28   data arrival time
-----------------------------------------------------------------------------
                                -12.67   slack (VIOLATED)



```

### Path 7

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2_nohash/attention_dual_stream_composed_v1_hier/6_finish.rpt`
- stage: `finish`
- startpoint: `seed_state[1]$_DFF_PN0_`
- endpoint: `u_softmax/weights[56]$_SDFF_PN1_`
- path_group: `clk`
- path_type: `max`
- slack: `-12.6700`
- data_arrival_time: `23.2000`
- data_required_time: `10.5300`

```text
Startpoint: seed_state[1]$_DFF_PN0_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: u_softmax/weights[56]$_SDFF_PN1_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   48.93    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.02    0.02    0.02 ^ wire79114/A (BUF_X16)
     1   50.07    0.01    0.02    0.04 ^ wire79114/Z (BUF_X16)
                                         net79113 (net)
                  0.02    0.02    0.06 ^ wire79113/A (BUF_X16)
     1   47.51    0.01    0.02    0.09 ^ wire79113/Z (BUF_X16)
                                         net79112 (net)
                  0.02    0.02    0.11 ^ clkbuf_0_clk/A (CLKBUF_X3)
     2   20.44    0.02    0.05    0.15 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.02    0.00    0.16 ^ clkbuf_1_1_0_clk/A (CLKBUF_X3)
     1   33.48    0.03    0.05    0.21 ^ clkbuf_1_1_0_clk/Z (CLKBUF_X3)
...
                                         clknet_5_13__leaf_clk (net)
                  0.04    0.00   10.51 ^ clkbuf_leaf_1_clk/A (CLKBUF_X3)
     3   13.31    0.01    0.05   10.57 ^ clkbuf_leaf_1_clk/Z (CLKBUF_X3)
                                         clknet_leaf_1_clk (net)
                  0.01    0.00   10.57 ^ u_softmax/weights[56]$_SDFF_PN1_/CK (DFF_X1)
                          0.00   10.57   clock reconvergence pessimism
                         -0.03   10.53   library setup time
                                 10.53   data required time
-----------------------------------------------------------------------------
                                 10.53   data required time
                                -23.20   data arrival time
-----------------------------------------------------------------------------
                                -12.67   slack (VIOLATED)



```

### Path 8

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2_nohash/attention_dual_stream_composed_v1_hier/2_floorplan_final.rpt`
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
