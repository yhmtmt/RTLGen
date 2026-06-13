# OpenROAD Timing Debug Summary

- design_dir: `runs/designs/npu_blocks/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2`
- metrics_path: `runs/designs/npu_blocks/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2/metrics.csv`
- rows_considered: 2

## Metrics Rows

| param_hash | tag | status | critical_path_ns | density | result_path |
| --- | --- | --- | ---: | ---: | --- |
| 81f459d1 | attention_dual_stream_composed_v1_hier | ok | 23.8349 | 0.3 | `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2/attention_dual_stream_composed_v1_hier/6_finish.rpt` |
| 40317f7f | attention_dual_stream_composed_v1_hier | ok | 24.1263 | 0.4 | `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2/attention_dual_stream_composed_v1_hier/6_finish.rpt` |

## Inspected Report Files

- `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2/attention_dual_stream_composed_v1_hier/6_finish.rpt`
- `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2/attention_dual_stream_composed_v1_hier/3_global_place.rpt`
- `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2/attention_dual_stream_composed_v1_hier/3_detailed_place.rpt`
- `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2/attention_dual_stream_composed_v1_hier/5_route_drc.rpt-5.rpt`
- `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2/attention_dual_stream_composed_v1_hier/3_resizer.rpt`
- `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2/attention_dual_stream_composed_v1_hier/4_cts_final.rpt`
- `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2/attention_dual_stream_composed_v1_hier/2_floorplan_final.rpt`
- `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2/attention_dual_stream_composed_v1_hier/5_global_route.rpt`
- `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2/attention_dual_stream_composed_v1_hier/5_route_drc.rpt`
- `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2/attention_dual_stream_composed_v1_hier/grt_antennas.log`
- `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2/attention_dual_stream_composed_v1_hier/drt_antennas.log`
- `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2/attention_dual_stream_composed_v1_hier/metadata-generate.log`

## Extracted Timing Paths

- path_block_count: 104

### Path 1

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2/attention_dual_stream_composed_v1_hier/2_floorplan_final.rpt`
- startpoint: `seed_state[0]$_DFF_PN1_`
- endpoint: `u_softmax/weight_hash[8]$_DFF_P_`
- path_group: `clk`
- path_type: `max`
- slack: `-19.2200`
- data_arrival_time: `29.1700`
- data_required_time: `9.9500`

```text
Startpoint: seed_state[0]$_DFF_PN1_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: u_softmax/weight_hash[8]$_DFF_P_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                  0.00    0.00    0.00 ^ seed_state[0]$_DFF_PN1_/CK (DFFS_X1)
     5   15.36    0.04    0.12    0.12 ^ seed_state[0]$_DFF_PN1_/Q (DFFS_X1)
                                         seed_state[0] (net)
                  0.04    0.00    0.12 ^ _15428_/A (XOR2_X2)
     2    6.80    0.03    0.06    0.18 ^ _15428_/Z (XOR2_X2)
                                         _06505_ (net)
                  0.03    0.00    0.18 ^ _15429_/A (BUF_X4)
    10   27.39    0.02    0.04    0.22 ^ _15429_/Z (BUF_X4)
                                         _06506_ (net)
                  0.02    0.00    0.22 ^ _15430_/A (BUF_X4)
    10   25.74    0.02    0.04    0.25 ^ _15430_/Z (BUF_X4)
                                         _06507_ (net)
                  0.02    0.00    0.25 ^ _15712_/B (XNOR2_X1)
...
                          0.00   10.00   clock network delay (ideal)
                          0.00   10.00   clock reconvergence pessimism
                                 10.00 ^ u_softmax/weight_hash[8]$_DFF_P_/CK (DFF_X1)
                         -0.05    9.95   library setup time
                                  9.95   data required time
-----------------------------------------------------------------------------
                                  9.95   data required time
                                -29.17   data arrival time
-----------------------------------------------------------------------------
                                -19.22   slack (VIOLATED)



==========================================================================
floorplan final report_checks -unconstrained
--------------------------------------------------------------------------
```

### Path 2

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2/attention_dual_stream_composed_v1_hier/2_floorplan_final.rpt`
- startpoint: `seed_state[0]$_DFF_PN1_`
- endpoint: `u_softmax/weight_hash[8]$_DFF_P_`
- path_group: `clk`
- path_type: `max`
- slack: `-19.2200`
- data_arrival_time: `29.1700`
- data_required_time: `9.9500`

```text
Startpoint: seed_state[0]$_DFF_PN1_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: u_softmax/weight_hash[8]$_DFF_P_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                  0.00    0.00    0.00 ^ seed_state[0]$_DFF_PN1_/CK (DFFS_X1)
     5   15.36    0.04    0.12    0.12 ^ seed_state[0]$_DFF_PN1_/Q (DFFS_X1)
                                         seed_state[0] (net)
                  0.04    0.00    0.12 ^ _15428_/A (XOR2_X2)
     2    6.80    0.03    0.06    0.18 ^ _15428_/Z (XOR2_X2)
                                         _06505_ (net)
                  0.03    0.00    0.18 ^ _15429_/A (BUF_X4)
    10   27.39    0.02    0.04    0.22 ^ _15429_/Z (BUF_X4)
                                         _06506_ (net)
                  0.02    0.00    0.22 ^ _15430_/A (BUF_X4)
    10   25.74    0.02    0.04    0.25 ^ _15430_/Z (BUF_X4)
                                         _06507_ (net)
                  0.02    0.00    0.25 ^ _15712_/B (XNOR2_X1)
...


==========================================================================
floorplan final report_power
--------------------------------------------------------------------------
Group                  Internal  Switching    Leakage      Total
                          Power      Power      Power      Power (Watts)
----------------------------------------------------------------
Sequential             1.47e-02   7.15e-04   1.15e-04   1.55e-02   0.1%
Combinational          6.31e+00   4.54e+00   6.22e-03   1.09e+01  99.9%
Clock                  0.00e+00   0.00e+00   0.00e+00   0.00e+00   0.0%
Macro                  0.00e+00   0.00e+00   0.00e+00   0.00e+00   0.0%
Pad                    0.00e+00   0.00e+00   0.00e+00   0.00e+00   0.0%
----------------------------------------------------------------
Total                  6.32e+00   4.54e+00   6.34e-03   1.09e+01 100.0%
                          58.2%      41.8%       0.1%
```

### Path 3

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2/attention_dual_stream_composed_v1_hier/2_floorplan_final.rpt`
- startpoint: `seed_state[0]$_DFF_PN1_`
- endpoint: `u_softmax/weight_hash[8]$_DFF_P_`
- path_group: `clk`
- path_type: `max`
- slack: `-19.2200`
- data_arrival_time: `29.1700`
- data_required_time: `9.9500`

```text
Startpoint: seed_state[0]$_DFF_PN1_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: u_softmax/weight_hash[8]$_DFF_P_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                  0.00    0.00    0.00 ^ seed_state[0]$_DFF_PN1_/CK (DFFS_X1)
     5   15.36    0.04    0.12    0.12 ^ seed_state[0]$_DFF_PN1_/Q (DFFS_X1)
                                         seed_state[0] (net)
                  0.04    0.00    0.12 ^ _15428_/A (XOR2_X2)
     2    6.80    0.03    0.06    0.18 ^ _15428_/Z (XOR2_X2)
                                         _06505_ (net)
                  0.03    0.00    0.18 ^ _15429_/A (BUF_X4)
    10   27.39    0.02    0.04    0.22 ^ _15429_/Z (BUF_X4)
                                         _06506_ (net)
                  0.02    0.00    0.22 ^ _15430_/A (BUF_X4)
    10   25.74    0.02    0.04    0.25 ^ _15430_/Z (BUF_X4)
                                         _06507_ (net)
                  0.02    0.00    0.25 ^ _15712_/B (XNOR2_X1)
...
                          0.00   10.00   clock network delay (ideal)
                          0.00   10.00   clock reconvergence pessimism
                                 10.00 ^ u_softmax/weight_hash[8]$_DFF_P_/CK (DFF_X1)
                         -0.05    9.95   library setup time
                                  9.95   data required time
-----------------------------------------------------------------------------
                                  9.95   data required time
                                -29.17   data arrival time
-----------------------------------------------------------------------------
                                -19.22   slack (VIOLATED)



==========================================================================
floorplan final report_checks -unconstrained
--------------------------------------------------------------------------
```

### Path 4

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2/attention_dual_stream_composed_v1_hier/2_floorplan_final.rpt`
- startpoint: `seed_state[0]$_DFF_PN1_`
- endpoint: `u_softmax/weight_hash[8]$_DFF_P_`
- path_group: `clk`
- path_type: `max`
- slack: `-19.2200`
- data_arrival_time: `29.1700`
- data_required_time: `9.9500`

```text
Startpoint: seed_state[0]$_DFF_PN1_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: u_softmax/weight_hash[8]$_DFF_P_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                  0.00    0.00    0.00 ^ seed_state[0]$_DFF_PN1_/CK (DFFS_X1)
     5   15.36    0.04    0.12    0.12 ^ seed_state[0]$_DFF_PN1_/Q (DFFS_X1)
                                         seed_state[0] (net)
                  0.04    0.00    0.12 ^ _15428_/A (XOR2_X2)
     2    6.80    0.03    0.06    0.18 ^ _15428_/Z (XOR2_X2)
                                         _06505_ (net)
                  0.03    0.00    0.18 ^ _15429_/A (BUF_X4)
    10   27.39    0.02    0.04    0.22 ^ _15429_/Z (BUF_X4)
                                         _06506_ (net)
                  0.02    0.00    0.22 ^ _15430_/A (BUF_X4)
    10   25.74    0.02    0.04    0.25 ^ _15430_/Z (BUF_X4)
                                         _06507_ (net)
                  0.02    0.00    0.25 ^ _15712_/B (XNOR2_X1)
...


==========================================================================
floorplan final report_power
--------------------------------------------------------------------------
Group                  Internal  Switching    Leakage      Total
                          Power      Power      Power      Power (Watts)
----------------------------------------------------------------
Sequential             1.47e-02   7.15e-04   1.15e-04   1.55e-02   0.1%
Combinational          6.31e+00   4.54e+00   6.22e-03   1.09e+01  99.9%
Clock                  0.00e+00   0.00e+00   0.00e+00   0.00e+00   0.0%
Macro                  0.00e+00   0.00e+00   0.00e+00   0.00e+00   0.0%
Pad                    0.00e+00   0.00e+00   0.00e+00   0.00e+00   0.0%
----------------------------------------------------------------
Total                  6.32e+00   4.54e+00   6.34e-03   1.09e+01 100.0%
                          58.2%      41.8%       0.1%
```

### Path 5

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2/attention_dual_stream_composed_v1_hier/3_global_place.rpt`
- startpoint: `seed_state[9]$_DFF_PN0_`
- endpoint: `u_softmax/weight_hash[24]$_DFF_P_`
- path_group: `clk`
- path_type: `max`
- slack: `-14.8700`
- data_arrival_time: `24.8300`
- data_required_time: `9.9600`

```text
Startpoint: seed_state[9]$_DFF_PN0_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: u_softmax/weight_hash[24]$_DFF_P_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                  0.00    0.00    0.00 ^ seed_state[9]$_DFF_PN0_/CK (DFFR_X1)
     3    9.77    0.01    0.10    0.10 v seed_state[9]$_DFF_PN0_/Q (DFFR_X1)
                                         seed_state[9] (net)
                  0.01    0.00    0.10 v _17974_/A (XOR2_X2)
     3   19.20    0.02    0.06    0.16 v _17974_/Z (XOR2_X2)
                                         _07482_ (net)
                  0.02    0.01    0.17 v place72761/A (BUF_X4)
     3   40.11    0.01    0.04    0.20 v place72761/Z (BUF_X4)
                                         net72760 (net)
                  0.03    0.02    0.23 v place72765/A (BUF_X4)
     2    5.51    0.01    0.03    0.26 v place72765/Z (BUF_X4)
                                         net72764 (net)
                  0.01    0.00    0.26 v _18908_/B (XNOR2_X1)
...
                          0.00   10.00   clock network delay (ideal)
                          0.00   10.00   clock reconvergence pessimism
                                 10.00 ^ u_softmax/weight_hash[24]$_DFF_P_/CK (DFF_X1)
                         -0.04    9.96   library setup time
                                  9.96   data required time
-----------------------------------------------------------------------------
                                  9.96   data required time
                                -24.83   data arrival time
-----------------------------------------------------------------------------
                                -14.87   slack (VIOLATED)



==========================================================================
global place report_checks -unconstrained
--------------------------------------------------------------------------
```

### Path 6

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2/attention_dual_stream_composed_v1_hier/3_global_place.rpt`
- startpoint: `seed_state[9]$_DFF_PN0_`
- endpoint: `u_softmax/weight_hash[24]$_DFF_P_`
- path_group: `clk`
- path_type: `max`
- slack: `-14.8700`
- data_arrival_time: `24.8300`
- data_required_time: `9.9600`

```text
Startpoint: seed_state[9]$_DFF_PN0_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: u_softmax/weight_hash[24]$_DFF_P_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                  0.00    0.00    0.00 ^ seed_state[9]$_DFF_PN0_/CK (DFFR_X1)
     3    9.77    0.01    0.10    0.10 v seed_state[9]$_DFF_PN0_/Q (DFFR_X1)
                                         seed_state[9] (net)
                  0.01    0.00    0.10 v _17974_/A (XOR2_X2)
     3   19.20    0.02    0.06    0.16 v _17974_/Z (XOR2_X2)
                                         _07482_ (net)
                  0.02    0.01    0.17 v place72761/A (BUF_X4)
     3   40.11    0.01    0.04    0.20 v place72761/Z (BUF_X4)
                                         net72760 (net)
                  0.03    0.02    0.23 v place72765/A (BUF_X4)
     2    5.51    0.01    0.03    0.26 v place72765/Z (BUF_X4)
                                         net72764 (net)
                  0.01    0.00    0.26 v _18908_/B (XNOR2_X1)
...


==========================================================================
global place report_power
--------------------------------------------------------------------------
Group                  Internal  Switching    Leakage      Total
                          Power      Power      Power      Power (Watts)
----------------------------------------------------------------
Sequential             1.04e-02   8.97e-04   1.21e-04   1.14e-02   0.1%
Combinational          8.01e+00   7.74e+00   7.12e-03   1.58e+01  99.9%
Clock                  0.00e+00   0.00e+00   0.00e+00   0.00e+00   0.0%
Macro                  0.00e+00   0.00e+00   0.00e+00   0.00e+00   0.0%
Pad                    0.00e+00   0.00e+00   0.00e+00   0.00e+00   0.0%
----------------------------------------------------------------
Total                  8.02e+00   7.74e+00   7.24e-03   1.58e+01 100.0%
                          50.9%      49.1%       0.0%
```

### Path 7

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2/attention_dual_stream_composed_v1_hier/3_global_place.rpt`
- startpoint: `seed_state[9]$_DFF_PN0_`
- endpoint: `u_softmax/weight_hash[24]$_DFF_P_`
- path_group: `clk`
- path_type: `max`
- slack: `-14.8700`
- data_arrival_time: `24.8300`
- data_required_time: `9.9600`

```text
Startpoint: seed_state[9]$_DFF_PN0_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: u_softmax/weight_hash[24]$_DFF_P_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                  0.00    0.00    0.00 ^ seed_state[9]$_DFF_PN0_/CK (DFFR_X1)
     3    9.77    0.01    0.10    0.10 v seed_state[9]$_DFF_PN0_/Q (DFFR_X1)
                                         seed_state[9] (net)
                  0.01    0.00    0.10 v _17974_/A (XOR2_X2)
     3   19.20    0.02    0.06    0.16 v _17974_/Z (XOR2_X2)
                                         _07482_ (net)
                  0.02    0.01    0.17 v place72761/A (BUF_X4)
     3   40.11    0.01    0.04    0.20 v place72761/Z (BUF_X4)
                                         net72760 (net)
                  0.03    0.02    0.23 v place72765/A (BUF_X4)
     2    5.51    0.01    0.03    0.26 v place72765/Z (BUF_X4)
                                         net72764 (net)
                  0.01    0.00    0.26 v _18908_/B (XNOR2_X1)
...
                          0.00   10.00   clock network delay (ideal)
                          0.00   10.00   clock reconvergence pessimism
                                 10.00 ^ u_softmax/weight_hash[24]$_DFF_P_/CK (DFF_X1)
                         -0.04    9.96   library setup time
                                  9.96   data required time
-----------------------------------------------------------------------------
                                  9.96   data required time
                                -24.83   data arrival time
-----------------------------------------------------------------------------
                                -14.87   slack (VIOLATED)



==========================================================================
global place report_checks -unconstrained
--------------------------------------------------------------------------
```

### Path 8

- source: `/orfs/flow/reports/nangate45/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2/attention_dual_stream_composed_v1_hier/3_global_place.rpt`
- startpoint: `seed_state[9]$_DFF_PN0_`
- endpoint: `u_softmax/weight_hash[24]$_DFF_P_`
- path_group: `clk`
- path_type: `max`
- slack: `-14.8700`
- data_arrival_time: `24.8300`
- data_required_time: `9.9600`

```text
Startpoint: seed_state[9]$_DFF_PN0_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: u_softmax/weight_hash[24]$_DFF_P_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                  0.00    0.00    0.00 ^ seed_state[9]$_DFF_PN0_/CK (DFFR_X1)
     3    9.77    0.01    0.10    0.10 v seed_state[9]$_DFF_PN0_/Q (DFFR_X1)
                                         seed_state[9] (net)
                  0.01    0.00    0.10 v _17974_/A (XOR2_X2)
     3   19.20    0.02    0.06    0.16 v _17974_/Z (XOR2_X2)
                                         _07482_ (net)
                  0.02    0.01    0.17 v place72761/A (BUF_X4)
     3   40.11    0.01    0.04    0.20 v place72761/Z (BUF_X4)
                                         net72760 (net)
                  0.03    0.02    0.23 v place72765/A (BUF_X4)
     2    5.51    0.01    0.03    0.26 v place72765/Z (BUF_X4)
                                         net72764 (net)
                  0.01    0.00    0.26 v _18908_/B (XNOR2_X1)
...


==========================================================================
global place report_power
--------------------------------------------------------------------------
Group                  Internal  Switching    Leakage      Total
                          Power      Power      Power      Power (Watts)
----------------------------------------------------------------
Sequential             1.04e-02   8.97e-04   1.21e-04   1.14e-02   0.1%
Combinational          8.01e+00   7.74e+00   7.12e-03   1.58e+01  99.9%
Clock                  0.00e+00   0.00e+00   0.00e+00   0.00e+00   0.0%
Macro                  0.00e+00   0.00e+00   0.00e+00   0.00e+00   0.0%
Pad                    0.00e+00   0.00e+00   0.00e+00   0.00e+00   0.0%
----------------------------------------------------------------
Total                  8.02e+00   7.74e+00   7.24e-03   1.58e+01 100.0%
                          50.9%      49.1%       0.0%
```
