# OpenROAD Timing Debug Summary

- design_dir: `runs/designs/npu_blocks/attention_decode_score_multivalue_gqa_group_lanes1_int8_m1x8_iterdiv`
- metrics_path: `runs/designs/npu_blocks/attention_decode_score_multivalue_gqa_group_lanes1_int8_m1x8_iterdiv/metrics.csv`
- rows_considered: 2

## Metrics Rows

| param_hash | tag | status | critical_path_ns | density | result_path |
| --- | --- | --- | ---: | ---: | --- |
| 9210cadf | decode_score_multivalue_gqa_lanes1_v1_matched_density_die_2500 | ok | 6.7506 | 0.4 | `/orfs/flow/reports/nangate45/attention_decode_score_multivalue_gqa_group_lanes1_int8_m1x8_iterdiv/decode_score_multivalue_gqa_group_lanes_v1_matched_density_die_2500/6_finish.rpt` |
| 9bd9ae39 | decode_score_multivalue_gqa_lanes1_v1_matched_density_die_2500 | ok | 6.8180 | 0.4 | `/orfs/flow/reports/nangate45/attention_decode_score_multivalue_gqa_group_lanes1_int8_m1x8_iterdiv/decode_score_multivalue_gqa_group_lanes_v1_matched_density_die_2500/6_finish.rpt` |

## Inspected Report Files

- `/orfs/flow/reports/nangate45/attention_decode_score_multivalue_gqa_group_lanes1_int8_m1x8_iterdiv/decode_score_multivalue_gqa_group_lanes_v1_matched_density_die_2500/6_finish.rpt`
- `/orfs/flow/reports/nangate45/attention_decode_score_multivalue_gqa_group_lanes1_int8_m1x8_iterdiv/decode_score_multivalue_gqa_group_lanes_v1_matched_density_die_2500/5_global_route.rpt`
- `/orfs/flow/reports/nangate45/attention_decode_score_multivalue_gqa_group_lanes1_int8_m1x8_iterdiv/decode_score_multivalue_gqa_group_lanes_v1_matched_density_die_2500/5_route_drc.rpt`
- `/orfs/flow/reports/nangate45/attention_decode_score_multivalue_gqa_group_lanes1_int8_m1x8_iterdiv/decode_score_multivalue_gqa_group_lanes_v1_matched_density_die_2500/5_route_drc.rpt-5.rpt`
- `/orfs/flow/reports/nangate45/attention_decode_score_multivalue_gqa_group_lanes1_int8_m1x8_iterdiv/decode_score_multivalue_gqa_group_lanes_v1_matched_density_die_2500/4_cts_final.rpt`
- `/orfs/flow/reports/nangate45/attention_decode_score_multivalue_gqa_group_lanes1_int8_m1x8_iterdiv/decode_score_multivalue_gqa_group_lanes_v1_matched_density_die_2500/3_resizer.rpt`
- `/orfs/flow/reports/nangate45/attention_decode_score_multivalue_gqa_group_lanes1_int8_m1x8_iterdiv/decode_score_multivalue_gqa_group_lanes_v1_matched_density_die_2500/3_detailed_place.rpt`
- `/orfs/flow/reports/nangate45/attention_decode_score_multivalue_gqa_group_lanes1_int8_m1x8_iterdiv/decode_score_multivalue_gqa_group_lanes_v1_matched_density_die_2500/3_global_place.rpt`
- `/orfs/flow/reports/nangate45/attention_decode_score_multivalue_gqa_group_lanes1_int8_m1x8_iterdiv/decode_score_multivalue_gqa_group_lanes_v1_matched_density_die_2500/2_floorplan_final.rpt`
- `/orfs/flow/reports/nangate45/attention_decode_score_multivalue_gqa_group_lanes1_int8_m1x8_iterdiv/decode_score_multivalue_gqa_group_lanes_v1_matched_density_die_2500/drt_antennas.log`
- `/orfs/flow/reports/nangate45/attention_decode_score_multivalue_gqa_group_lanes1_int8_m1x8_iterdiv/decode_score_multivalue_gqa_group_lanes_v1_matched_density_die_2500/grt_antennas.log`
- `/orfs/flow/reports/nangate45/attention_decode_score_multivalue_gqa_group_lanes1_int8_m1x8_iterdiv/decode_score_multivalue_gqa_group_lanes_v1_matched_density_die_2500/metadata-generate.log`

## Preferred Final-Stage Timing Paths

- raw_path_block_count: 104
- unique_path_block_count: 28
- preferred_stage: `finish`

### Path 1

- source: `/orfs/flow/reports/nangate45/attention_decode_score_multivalue_gqa_group_lanes1_int8_m1x8_iterdiv/decode_score_multivalue_gqa_group_lanes_v1_matched_density_die_2500/6_finish.rpt`
- stage: `finish`
- startpoint: `u_lane_0/reducer/cycle_count[0]$_DFF_PN0_`
- endpoint: `u_lane_0/reducer/cycle_count[0]$_DFF_PN0_`
- path_group: `clk`
- path_type: `min`
- slack: `0.0600`
- data_arrival_time: `0.8600`
- data_required_time: `0.8000`

```text
Startpoint: u_lane_0/reducer/cycle_count[0]$_DFF_PN0_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: u_lane_0/reducer/cycle_count[0]$_DFF_PN0_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   42.88    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.02    0.01    0.01 ^ wire35625/A (BUF_X8)
     1   41.03    0.01    0.03    0.04 ^ wire35625/Z (BUF_X8)
                                         net35624 (net)
                  0.02    0.01    0.05 ^ wire35624/A (BUF_X16)
     1   68.89    0.01    0.02    0.08 ^ wire35624/Z (BUF_X16)
                                         net35623 (net)
                  0.04    0.03    0.11 ^ wire35623/A (BUF_X32)
     1   69.44    0.01    0.03    0.13 ^ wire35623/Z (BUF_X32)
                                         net35622 (net)
                  0.04    0.03    0.16 ^ wire35622/A (BUF_X32)
     2   59.24    0.01    0.03    0.19 ^ wire35622/Z (BUF_X32)
...
                                         clknet_7_117__leaf_clk_regs (net)
                  0.02    0.00    0.76 ^ clkbuf_leaf_1070_clk_regs/A (CLKBUF_X3)
     7    8.66    0.01    0.04    0.79 ^ clkbuf_leaf_1070_clk_regs/Z (CLKBUF_X3)
                                         clknet_leaf_1070_clk_regs (net)
                  0.01    0.00    0.79 ^ u_lane_0/reducer/cycle_count[0]$_DFF_PN0_/CK (DFFR_X1)
                          0.00    0.79   clock reconvergence pessimism
                          0.01    0.80   library hold time
                                  0.80   data required time
-----------------------------------------------------------------------------
                                  0.80   data required time
                                 -0.86   data arrival time
-----------------------------------------------------------------------------
                                  0.06   slack (MET)



```

### Path 2

- source: `/orfs/flow/reports/nangate45/attention_decode_score_multivalue_gqa_group_lanes1_int8_m1x8_iterdiv/decode_score_multivalue_gqa_group_lanes_v1_matched_density_die_2500/6_finish.rpt`
- stage: `finish`
- startpoint: `rst_n (input port clocked by clk)`
- endpoint: `u_lane_0/score_response_data_q[180]$_DFFE_PN0P_`
- path_group: `asynchronous`
- path_type: `min`
- slack: `0.9300`
- data_arrival_time: `2.0800`
- data_required_time: `1.1400`

```text
Startpoint: rst_n (input port clocked by clk)
Endpoint: u_lane_0/score_response_data_q[180]$_DFFE_PN0P_
          (removal check against rising-edge clock clk)
Path Group: asynchronous
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (propagated)
                          2.00    2.00 ^ input external delay
     1   25.04    0.00    0.00    2.00 ^ rst_n (in)
                                         rst_n (net)
                  0.01    0.01    2.01 ^ input475/A (CLKBUF_X3)
    14   46.20    0.03    0.05    2.05 ^ input475/Z (CLKBUF_X3)
                                         net474 (net)
                  0.04    0.02    2.08 ^ u_lane_0/score_response_data_q[180]$_DFFE_PN0P_/RN (DFFR_X1)
                                  2.08   data arrival time

                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   42.88    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.02    0.01    0.01 ^ wire35625/A (BUF_X8)
...
                                         clknet_6_15_0_clk_regs (net)
                  0.02    0.00    0.74 ^ clkbuf_7_31__f_clk_regs/A (CLKBUF_X3)
    16   88.28    0.07    0.10    0.84 ^ clkbuf_7_31__f_clk_regs/Z (CLKBUF_X3)
                                         clknet_7_31__leaf_clk_regs (net)
                  0.07    0.01    0.85 ^ clkbuf_leaf_843_clk_regs/A (CLKBUF_X3)
     3   14.00    0.02    0.06    0.90 ^ clkbuf_leaf_843_clk_regs/Z (CLKBUF_X3)
                                         clknet_leaf_843_clk_regs (net)
                  0.02    0.00    0.90 ^ u_lane_0/score_response_data_q[180]$_DFFE_PN0P_/CK (DFFR_X1)
                          0.00    0.90   clock reconvergence pessimism
                          0.24    1.14   library removal time
                                  1.14   data required time
-----------------------------------------------------------------------------
                                  1.14   data required time
                                 -2.08   data arrival time
-----------------------------------------------------------------------------
                                  0.93   slack (MET)
```

### Path 3

- source: `/orfs/flow/reports/nangate45/attention_decode_score_multivalue_gqa_group_lanes1_int8_m1x8_iterdiv/decode_score_multivalue_gqa_group_lanes_v1_matched_density_die_2500/6_finish.rpt`
- stage: `finish`
- startpoint: `u_lane_0/scaled_score_row_q[63]$_DFFE_PN0P_`
- endpoint: `u_lane_0/reducer/global_max[14]$_DFF_PN0_`
- path_group: `clk`
- path_type: `max`
- slack: `2.0100`
- data_arrival_time: `6.7500`
- data_required_time: `8.7600`

```text
Startpoint: u_lane_0/scaled_score_row_q[63]$_DFFE_PN0P_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: u_lane_0/reducer/global_max[14]$_DFF_PN0_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   42.88    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.02    0.01    0.01 ^ wire35625/A (BUF_X8)
     1   41.03    0.01    0.03    0.04 ^ wire35625/Z (BUF_X8)
                                         net35624 (net)
                  0.02    0.01    0.05 ^ wire35624/A (BUF_X16)
     1   68.89    0.01    0.02    0.08 ^ wire35624/Z (BUF_X16)
                                         net35623 (net)
                  0.04    0.03    0.11 ^ wire35623/A (BUF_X32)
     1   69.44    0.01    0.03    0.13 ^ wire35623/Z (BUF_X32)
                                         net35622 (net)
                  0.04    0.03    0.16 ^ wire35622/A (BUF_X32)
     2   59.24    0.01    0.03    0.19 ^ wire35622/Z (BUF_X32)
...
                                         clknet_7_87__leaf_clk_regs (net)
                  0.03    0.00    8.75 ^ clkbuf_leaf_1078_clk_regs/A (CLKBUF_X3)
     5    9.99    0.01    0.04    8.80 ^ clkbuf_leaf_1078_clk_regs/Z (CLKBUF_X3)
                                         clknet_leaf_1078_clk_regs (net)
                  0.01    0.00    8.80 ^ u_lane_0/reducer/global_max[14]$_DFF_PN0_/CK (DFFR_X2)
                          0.00    8.80   clock reconvergence pessimism
                         -0.04    8.76   library setup time
                                  8.76   data required time
-----------------------------------------------------------------------------
                                  8.76   data required time
                                 -6.75   data arrival time
-----------------------------------------------------------------------------
                                  2.01   slack (MET)



```

### Path 4

- source: `/orfs/flow/reports/nangate45/attention_decode_score_multivalue_gqa_group_lanes1_int8_m1x8_iterdiv/decode_score_multivalue_gqa_group_lanes_v1_matched_density_die_2500/6_finish.rpt`
- stage: `finish`
- startpoint: `rst_n (input port clocked by clk)`
- endpoint: `cycle_count[6]$_DFF_PN0_`
- path_group: `asynchronous`
- path_type: `max`
- slack: `5.0100`
- data_arrival_time: `3.8200`
- data_required_time: `8.8400`

```text
Startpoint: rst_n (input port clocked by clk)
Endpoint: cycle_count[6]$_DFF_PN0_
          (recovery check against rising-edge clock clk)
Path Group: asynchronous
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (propagated)
                          2.00    2.00 ^ input external delay
     1   25.04    0.00    0.00    2.00 ^ rst_n (in)
                                         rst_n (net)
                  0.01    0.01    2.01 ^ input475/A (CLKBUF_X3)
    14   46.20    0.03    0.05    2.05 ^ input475/Z (CLKBUF_X3)
                                         net474 (net)
                  0.04    0.02    2.08 ^ place35450/A (BUF_X2)
     5   39.89    0.04    0.06    2.13 ^ place35450/Z (BUF_X2)
                                         net35449 (net)
                  0.04    0.01    2.15 ^ place35451/A (BUF_X1)
    11   33.54    0.08    0.11    2.25 ^ place35451/Z (BUF_X1)
                                         net35450 (net)
                  0.08    0.00    2.26 ^ place35452/A (BUF_X1)
     1   29.23    0.07    0.10    2.36 ^ place35452/Z (BUF_X1)
...
                                         clknet_4_4_0_clk_regs (net)
                  0.03    0.00    8.65 ^ clkbuf_6_16_0_clk_regs/A (CLKBUF_X3)
     2   13.99    0.01    0.05    8.69 ^ clkbuf_6_16_0_clk_regs/Z (CLKBUF_X3)
                                         clknet_6_16_0_clk_regs (net)
                  0.01    0.00    8.70 ^ clkbuf_7_32__f_clk_regs/A (CLKBUF_X3)
     3   39.95    0.02    0.05    8.75 ^ clkbuf_7_32__f_clk_regs/Z (CLKBUF_X3)
                                         clknet_7_32__leaf_clk_regs (net)
                  0.04    0.03    8.77 ^ cycle_count[6]$_DFF_PN0_/CK (DFFR_X1)
                          0.00    8.77   clock reconvergence pessimism
                          0.06    8.84   library recovery time
                                  8.84   data required time
-----------------------------------------------------------------------------
                                  8.84   data required time
                                 -3.82   data arrival time
-----------------------------------------------------------------------------
                                  5.01   slack (MET)
```


## Worst Timing Paths Across All Stages

### Path 1

- source: `/orfs/flow/reports/nangate45/attention_decode_score_multivalue_gqa_group_lanes1_int8_m1x8_iterdiv/decode_score_multivalue_gqa_group_lanes_v1_matched_density_die_2500/3_global_place.rpt`
- stage: `global_place`
- startpoint: `u_lane_0/state_q[0]$_DFFE_PN0P_`
- endpoint: `u_lane_0/score_bank/u_group_1_slice_1`
- path_group: `clk`
- path_type: `max`
- slack: `-184.7800`
- data_arrival_time: `192.7300`
- data_required_time: `7.9500`

```text
Startpoint: u_lane_0/state_q[0]$_DFFE_PN0P_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: u_lane_0/score_bank/u_group_1_slice_1
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                  0.00    0.00    0.00 ^ u_lane_0/state_q[0]$_DFFE_PN0P_/CK (DFFR_X1)
     2    3.98    0.01    0.09    0.09 v u_lane_0/state_q[0]$_DFFE_PN0P_/Q (DFFR_X1)
                                         u_lane_0/state_q[0] (net)
                  0.01    0.00    0.09 v u_lane_0/_10971_/A (INV_X1)
     2    4.98    0.01    0.02    0.11 ^ u_lane_0/_10971_/ZN (INV_X1)
                                         u_lane_0/_06118_ (net)
                  0.01    0.00    0.11 ^ u_lane_0/_10986_/A2 (NOR3_X2)
     1    5.28    0.01    0.01    0.12 v u_lane_0/_10986_/ZN (NOR3_X2)
                                         u_lane_0/_08921_ (net)
                  0.01    0.00    0.12 v place32583/A (BUF_X4)
     2    7.95    0.01    0.02    0.15 v place32583/Z (BUF_X4)
                                         net32582 (net)
                  0.01    0.00    0.15 v u_lane_0/reducer/_144144_/A2 (AND2_X4)
...
                                192.73   data arrival time

                  0.00    8.00    8.00   clock clk (rise edge)
                          0.00    8.00   clock network delay (ideal)
                          0.00    8.00   clock reconvergence pessimism
                                  8.00 ^ u_lane_0/score_bank/u_group_1_slice_1/clk (fakeram45_2048x39)
                         -0.05    7.95   library setup time
                                  7.95   data required time
-----------------------------------------------------------------------------
                                  7.95   data required time
                               -192.73   data arrival time
-----------------------------------------------------------------------------
                               -184.78   slack (VIOLATED)



```

### Path 2

- source: `/orfs/flow/reports/nangate45/attention_decode_score_multivalue_gqa_group_lanes1_int8_m1x8_iterdiv/decode_score_multivalue_gqa_group_lanes_v1_matched_density_die_2500/3_resizer.rpt`
- stage: `resizer`
- startpoint: `u_lane_0/state_q[0]$_DFFE_PN0P_`
- endpoint: `u_lane_0/score_bank/u_group_1_slice_1`
- path_group: `clk`
- path_type: `max`
- slack: `-184.7800`
- data_arrival_time: `192.7300`
- data_required_time: `7.9500`

```text
Startpoint: u_lane_0/state_q[0]$_DFFE_PN0P_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: u_lane_0/score_bank/u_group_1_slice_1
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                  0.00    0.00    0.00 ^ u_lane_0/state_q[0]$_DFFE_PN0P_/CK (DFFR_X1)
     2    3.98    0.01    0.09    0.09 v u_lane_0/state_q[0]$_DFFE_PN0P_/Q (DFFR_X1)
                                         u_lane_0/state_q[0] (net)
                  0.01    0.00    0.09 v u_lane_0/_10971_/A (INV_X1)
     2    4.98    0.01    0.02    0.11 ^ u_lane_0/_10971_/ZN (INV_X1)
                                         u_lane_0/_06118_ (net)
                  0.01    0.00    0.11 ^ u_lane_0/_10986_/A2 (NOR3_X2)
     1    5.28    0.01    0.01    0.12 v u_lane_0/_10986_/ZN (NOR3_X2)
                                         u_lane_0/_08921_ (net)
                  0.01    0.00    0.12 v place32583/A (BUF_X4)
     2    7.95    0.01    0.02    0.15 v place32583/Z (BUF_X4)
                                         net32582 (net)
                  0.01    0.00    0.15 v u_lane_0/reducer/_144144_/A2 (AND2_X4)
...
                                192.73   data arrival time

                  0.00    8.00    8.00   clock clk (rise edge)
                          0.00    8.00   clock network delay (ideal)
                          0.00    8.00   clock reconvergence pessimism
                                  8.00 ^ u_lane_0/score_bank/u_group_1_slice_1/clk (fakeram45_2048x39)
                         -0.05    7.95   library setup time
                                  7.95   data required time
-----------------------------------------------------------------------------
                                  7.95   data required time
                               -192.73   data arrival time
-----------------------------------------------------------------------------
                               -184.78   slack (VIOLATED)



```

### Path 3

- source: `/orfs/flow/reports/nangate45/attention_decode_score_multivalue_gqa_group_lanes1_int8_m1x8_iterdiv/decode_score_multivalue_gqa_group_lanes_v1_matched_density_die_2500/3_detailed_place.rpt`
- stage: `detailed_place`
- startpoint: `u_lane_0/state_q[0]$_DFFE_PN0P_`
- endpoint: `u_lane_0/score_bank/u_group_0_slice_0`
- path_group: `clk`
- path_type: `max`
- slack: `-5.3900`
- data_arrival_time: `13.3400`
- data_required_time: `7.9500`

```text
Startpoint: u_lane_0/state_q[0]$_DFFE_PN0P_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: u_lane_0/score_bank/u_group_0_slice_0
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                  0.00    0.00    0.00 ^ u_lane_0/state_q[0]$_DFFE_PN0P_/CK (DFFR_X1)
     2    3.19    0.01    0.09    0.09 v u_lane_0/state_q[0]$_DFFE_PN0P_/Q (DFFR_X1)
                                         u_lane_0/state_q[0] (net)
                  0.01    0.00    0.09 v u_lane_0/_10971_/A (INV_X1)
     2    5.02    0.01    0.02    0.11 ^ u_lane_0/_10971_/ZN (INV_X1)
                                         u_lane_0/_06118_ (net)
                  0.01    0.00    0.11 ^ u_lane_0/_10986_/A2 (NOR3_X2)
     1    5.38    0.01    0.01    0.12 v u_lane_0/_10986_/ZN (NOR3_X2)
                                         u_lane_0/_08921_ (net)
                  0.01    0.00    0.12 v place32583/A (BUF_X4)
     2    7.08    0.01    0.02    0.15 v place32583/Z (BUF_X4)
                                         net32582 (net)
                  0.01    0.00    0.15 v u_lane_0/reducer/_144144_/A2 (AND2_X4)
...
                                 13.34   data arrival time

                  0.00    8.00    8.00   clock clk (rise edge)
                          0.00    8.00   clock network delay (ideal)
                          0.00    8.00   clock reconvergence pessimism
                                  8.00 ^ u_lane_0/score_bank/u_group_0_slice_0/clk (fakeram45_2048x39)
                         -0.05    7.95   library setup time
                                  7.95   data required time
-----------------------------------------------------------------------------
                                  7.95   data required time
                                -13.34   data arrival time
-----------------------------------------------------------------------------
                                 -5.39   slack (VIOLATED)



```

### Path 4

- source: `/orfs/flow/reports/nangate45/attention_decode_score_multivalue_gqa_group_lanes1_int8_m1x8_iterdiv/decode_score_multivalue_gqa_group_lanes_v1_matched_density_die_2500/2_floorplan_final.rpt`
- stage: `floorplan`
- startpoint: `u_lane_0/reducer/state[6]$_DFF_PN0_`
- endpoint: `u_lane_0/score_bank/u_group_1_slice_0`
- path_group: `clk`
- path_type: `min`
- slack: `-0.0500`
- data_arrival_time: `0.0000`
- data_required_time: `0.0500`

```text
Startpoint: u_lane_0/reducer/state[6]$_DFF_PN0_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: u_lane_0/score_bank/u_group_1_slice_0
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                  0.00    0.00    0.00 ^ u_lane_0/reducer/state[6]$_DFF_PN0_/CK (DFFR_X1)
     4    7.29    0.02    0.11    0.11 ^ u_lane_0/reducer/state[6]$_DFF_PN0_/Q (DFFR_X1)
                                         u_lane_0/reducer/state[6] (net)
                  0.02    0.00    0.11 ^ u_lane_0/reducer/_144144_/A1 (AND2_X4)
  2055 10250.42    5.86    6.20    6.31 ^ u_lane_0/reducer/_144144_/ZN (AND2_X4)
                                         u_lane_0/bank_req_write (net)
                   INF   -6.31    0.00 ^ u_lane_0/score_bank/u_group_1_slice_0/w_mask_in[10] (fakeram45_2048x39)
                                  0.00   data arrival time

                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                          0.00    0.00   clock reconvergence pessimism
                                  0.00 ^ u_lane_0/score_bank/u_group_1_slice_0/clk (fakeram45_2048x39)
                          0.05    0.05   library hold time
                                  0.05   data required time
-----------------------------------------------------------------------------
                                  0.05   data required time
                                 -0.00   data arrival time
-----------------------------------------------------------------------------
                                 -0.05   slack (VIOLATED)



```

### Path 5

- source: `/orfs/flow/reports/nangate45/attention_decode_score_multivalue_gqa_group_lanes1_int8_m1x8_iterdiv/decode_score_multivalue_gqa_group_lanes_v1_matched_density_die_2500/4_cts_final.rpt`
- stage: `cts`
- startpoint: `u_lane_0/reducer/state[6]$_DFF_PN0_`
- endpoint: `u_lane_0/score_bank/u_group_2_slice_5`
- path_group: `clk`
- path_type: `min`
- slack: `-0.0300`
- data_arrival_time: `0.9000`
- data_required_time: `0.9300`

```text
Startpoint: u_lane_0/reducer/state[6]$_DFF_PN0_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: u_lane_0/score_bank/u_group_2_slice_5
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   57.98    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.02    0.02    0.02 ^ wire35625/A (BUF_X8)
     1   49.20    0.01    0.03    0.05 ^ wire35625/Z (BUF_X8)
                                         net35624 (net)
                  0.02    0.01    0.06 ^ wire35624/A (BUF_X16)
     1   81.20    0.01    0.03    0.09 ^ wire35624/Z (BUF_X16)
                                         net35623 (net)
                  0.04    0.03    0.12 ^ wire35623/A (BUF_X32)
     1   82.84    0.01    0.03    0.15 ^ wire35623/Z (BUF_X32)
                                         net35622 (net)
                  0.04    0.03    0.18 ^ wire35622/A (BUF_X32)
     2   54.22    0.01    0.03    0.20 ^ wire35622/Z (BUF_X32)
...
                                         net35631 (net)
                  0.02    0.01    0.77 ^ clkbuf_leaf_1_clk/A (CLKBUF_X3)
     3   99.19    0.08    0.11    0.88 ^ clkbuf_leaf_1_clk/Z (CLKBUF_X3)
                                         clknet_leaf_1_clk (net)
                  0.12    0.00    0.88 ^ u_lane_0/score_bank/u_group_2_slice_5/clk (fakeram45_2048x39)
                          0.00    0.88   clock reconvergence pessimism
                          0.05    0.93   library hold time
                                  0.93   data required time
-----------------------------------------------------------------------------
                                  0.93   data required time
                                 -0.90   data arrival time
-----------------------------------------------------------------------------
                                 -0.03   slack (VIOLATED)



```

### Path 6

- source: `/orfs/flow/reports/nangate45/attention_decode_score_multivalue_gqa_group_lanes1_int8_m1x8_iterdiv/decode_score_multivalue_gqa_group_lanes_v1_matched_density_die_2500/4_cts_final.rpt`
- stage: `cts`
- startpoint: `u_lane_0/state_q[1]$_DFFE_PN0P_`
- endpoint: `u_lane_0/score_bank/u_group_0_slice_5`
- path_group: `clk`
- path_type: `max`
- slack: `0.0200`
- data_arrival_time: `8.8000`
- data_required_time: `8.8200`

```text
Startpoint: u_lane_0/state_q[1]$_DFFE_PN0P_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: u_lane_0/score_bank/u_group_0_slice_5
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   57.98    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.02    0.02    0.02 ^ wire35625/A (BUF_X8)
     1   49.20    0.01    0.03    0.05 ^ wire35625/Z (BUF_X8)
                                         net35624 (net)
                  0.02    0.01    0.06 ^ wire35624/A (BUF_X16)
     1   81.20    0.01    0.03    0.09 ^ wire35624/Z (BUF_X16)
                                         net35623 (net)
                  0.04    0.03    0.12 ^ wire35623/A (BUF_X32)
     1   82.84    0.01    0.03    0.15 ^ wire35623/Z (BUF_X32)
                                         net35622 (net)
                  0.04    0.03    0.18 ^ wire35622/A (BUF_X32)
     2   54.22    0.01    0.03    0.20 ^ wire35622/Z (BUF_X32)
...
                                         net35636 (net)
                  0.03    0.02    8.80 ^ clkbuf_leaf_6_clk/A (CLKBUF_X3)
     2   50.00    0.04    0.08    8.87 ^ clkbuf_leaf_6_clk/Z (CLKBUF_X3)
                                         clknet_leaf_6_clk (net)
                  0.06    0.00    8.87 ^ u_lane_0/score_bank/u_group_0_slice_5/clk (fakeram45_2048x39)
                          0.00    8.87   clock reconvergence pessimism
                         -0.05    8.82   library setup time
                                  8.82   data required time
-----------------------------------------------------------------------------
                                  8.82   data required time
                                 -8.80   data arrival time
-----------------------------------------------------------------------------
                                  0.02   slack (MET)



```

### Path 7

- source: `/orfs/flow/reports/nangate45/attention_decode_score_multivalue_gqa_group_lanes1_int8_m1x8_iterdiv/decode_score_multivalue_gqa_group_lanes_v1_matched_density_die_2500/3_detailed_place.rpt`
- stage: `detailed_place`
- startpoint: `cycle_count[0]$_DFF_PN0_`
- endpoint: `cycle_count[0]$_DFF_PN0_`
- path_group: `clk`
- path_type: `min`
- slack: `0.0600`
- data_arrival_time: `0.0600`
- data_required_time: `0.0100`

```text
Startpoint: cycle_count[0]$_DFF_PN0_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: cycle_count[0]$_DFF_PN0_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                  0.00    0.00    0.00 ^ cycle_count[0]$_DFF_PN0_/CK (DFFR_X1)
     1    1.38    0.01    0.06    0.06 ^ cycle_count[0]$_DFF_PN0_/QN (DFFR_X1)
                                         _0555_ (net)
                  0.01    0.00    0.06 ^ cycle_count[0]$_DFF_PN0_/D (DFFR_X1)
                                  0.06   data arrival time

                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                          0.00    0.00   clock reconvergence pessimism
                                  0.00 ^ cycle_count[0]$_DFF_PN0_/CK (DFFR_X1)
                          0.01    0.01   library hold time
                                  0.01   data required time
-----------------------------------------------------------------------------
                                  0.01   data required time
                                 -0.06   data arrival time
-----------------------------------------------------------------------------
                                  0.06   slack (MET)



```

### Path 8

- source: `/orfs/flow/reports/nangate45/attention_decode_score_multivalue_gqa_group_lanes1_int8_m1x8_iterdiv/decode_score_multivalue_gqa_group_lanes_v1_matched_density_die_2500/3_global_place.rpt`
- stage: `global_place`
- startpoint: `cycle_count[0]$_DFF_PN0_`
- endpoint: `cycle_count[0]$_DFF_PN0_`
- path_group: `clk`
- path_type: `min`
- slack: `0.0600`
- data_arrival_time: `0.0600`
- data_required_time: `0.0100`

```text
Startpoint: cycle_count[0]$_DFF_PN0_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: cycle_count[0]$_DFF_PN0_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                  0.00    0.00    0.00 ^ cycle_count[0]$_DFF_PN0_/CK (DFFR_X1)
     1    1.38    0.01    0.06    0.06 ^ cycle_count[0]$_DFF_PN0_/QN (DFFR_X1)
                                         _0555_ (net)
                  0.01    0.00    0.06 ^ cycle_count[0]$_DFF_PN0_/D (DFFR_X1)
                                  0.06   data arrival time

                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                          0.00    0.00   clock reconvergence pessimism
                                  0.00 ^ cycle_count[0]$_DFF_PN0_/CK (DFFR_X1)
                          0.01    0.01   library hold time
                                  0.01   data required time
-----------------------------------------------------------------------------
                                  0.01   data required time
                                 -0.06   data arrival time
-----------------------------------------------------------------------------
                                  0.06   slack (MET)



```
