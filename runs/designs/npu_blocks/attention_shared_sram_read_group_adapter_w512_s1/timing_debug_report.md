# OpenROAD Timing Debug Summary

- design_dir: `runs/designs/npu_blocks/attention_shared_sram_read_group_adapter_w512_s1`
- metrics_path: `runs/designs/npu_blocks/attention_shared_sram_read_group_adapter_w512_s1/metrics.csv`
- rows_considered: 4

## Metrics Rows

| param_hash | tag | status | critical_path_ns | density | result_path |
| --- | --- | --- | ---: | ---: | --- |
| 07ed8cb5 | attention_shared_sram_read_group_adapter_ppa_v1_07ed8cb5 | ok | 0.6493 | 0.5 | `/orfs/flow/reports/nangate45/attention_shared_sram_read_group_adapter_w512_s1/base/6_finish.rpt` |
| 8574f558 | attention_shared_sram_read_group_adapter_ppa_v1_8574f558 | ok | 0.7476 | 0.5 | `/orfs/flow/reports/nangate45/attention_shared_sram_read_group_adapter_w512_s1/base/6_finish.rpt` |
| ea04ba90 | attention_shared_sram_read_group_adapter_ppa_v1_ea04ba90 | ok | 0.7477 | 0.5 | `/orfs/flow/reports/nangate45/attention_shared_sram_read_group_adapter_w512_s1/base/6_finish.rpt` |
| 77ace606 | attention_shared_sram_read_group_adapter_ppa_v1_77ace606 | ok | 0.7485 | 0.5 | `/orfs/flow/reports/nangate45/attention_shared_sram_read_group_adapter_w512_s1/base/6_finish.rpt` |

## Inspected Report Files

- `/orfs/flow/reports/nangate45/attention_shared_sram_read_group_adapter_w512_s1/base/6_finish.rpt`
- `/orfs/flow/reports/nangate45/attention_shared_sram_read_group_adapter_w512_s1/base/5_global_route.rpt`
- `/orfs/flow/reports/nangate45/attention_shared_sram_read_group_adapter_w512_s1/base/5_route_drc.rpt`
- `/orfs/flow/reports/nangate45/attention_shared_sram_read_group_adapter_w512_s1/base/4_cts_final.rpt`
- `/orfs/flow/reports/nangate45/attention_shared_sram_read_group_adapter_w512_s1/base/3_resizer.rpt`
- `/orfs/flow/reports/nangate45/attention_shared_sram_read_group_adapter_w512_s1/base/3_detailed_place.rpt`
- `/orfs/flow/reports/nangate45/attention_shared_sram_read_group_adapter_w512_s1/base/3_global_place.rpt`
- `/orfs/flow/reports/nangate45/attention_shared_sram_read_group_adapter_w512_s1/base/2_floorplan_final.rpt`
- `/orfs/flow/reports/nangate45/attention_shared_sram_read_group_adapter_w512_s1/base/drt_antennas.log`
- `/orfs/flow/reports/nangate45/attention_shared_sram_read_group_adapter_w512_s1/base/grt_antennas.log`
- `/orfs/flow/reports/nangate45/attention_shared_sram_read_group_adapter_w512_s1/base/metadata-generate.log`

## Preferred Final-Stage Timing Paths

- raw_path_block_count: 208
- unique_path_block_count: 33
- preferred_stage: `finish`

### Path 1

- source: `/orfs/flow/reports/nangate45/attention_shared_sram_read_group_adapter_w512_s1/base/6_finish.rpt`
- stage: `finish`
- startpoint: `issued_q[28]$_DFFE_PN0N_`
- endpoint: `issued_q[28]$_DFFE_PN0N_`
- path_group: `clk`
- path_type: `min`
- slack: `0.0900`
- data_arrival_time: `0.2500`
- data_required_time: `0.1600`

```text
Startpoint: issued_q[28]$_DFFE_PN0N_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: issued_q[28]$_DFFE_PN0N_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   11.76    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.00    0.00    0.00 ^ clkbuf_0_clk/A (CLKBUF_X3)
     8   40.39    0.03    0.06    0.06 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.03    0.00    0.06 ^ clkbuf_3_2__f_clk/A (CLKBUF_X3)
     8   22.46    0.02    0.05    0.11 ^ clkbuf_3_2__f_clk/Z (CLKBUF_X3)
                                         clknet_3_2__leaf_clk (net)
                  0.02    0.00    0.12 ^ clkbuf_leaf_46_clk/A (CLKBUF_X3)
     8   10.24    0.01    0.04    0.16 ^ clkbuf_leaf_46_clk/Z (CLKBUF_X3)
                                         clknet_leaf_46_clk (net)
                  0.01    0.00    0.16 ^ issued_q[28]$_DFFE_PN0N_/CK (DFFR_X1)
     2    2.84    0.01    0.09    0.25 v issued_q[28]$_DFFE_PN0N_/Q (DFFR_X1)
...
                                         clknet_3_2__leaf_clk (net)
                  0.02    0.00    0.12 ^ clkbuf_leaf_46_clk/A (CLKBUF_X3)
     8   10.24    0.01    0.04    0.16 ^ clkbuf_leaf_46_clk/Z (CLKBUF_X3)
                                         clknet_leaf_46_clk (net)
                  0.01    0.00    0.16 ^ issued_q[28]$_DFFE_PN0N_/CK (DFFR_X1)
                          0.00    0.16   clock reconvergence pessimism
                          0.01    0.16   library hold time
                                  0.16   data required time
-----------------------------------------------------------------------------
                                  0.16   data required time
                                 -0.25   data arrival time
-----------------------------------------------------------------------------
                                  0.09   slack (MET)



```

### Path 2

- source: `/orfs/flow/reports/nangate45/attention_shared_sram_read_group_adapter_w512_s1/base/6_finish.rpt`
- stage: `finish`
- startpoint: `rst_n (input port clocked by clk)`
- endpoint: `adapter.protocol_error$_DFFE_PN0P_`
- path_group: `asynchronous`
- path_type: `min`
- slack: `1.6800`
- data_arrival_time: `2.0500`
- data_required_time: `0.3700`

```text
Startpoint: rst_n (input port clocked by clk)
Endpoint: adapter.protocol_error$_DFFE_PN0P_
          (removal check against rising-edge clock clk)
Path Group: asynchronous
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (propagated)
                          2.00    2.00 ^ input external delay
     1    4.52    0.00    0.00    2.00 ^ rst_n (in)
                                         rst_n (net)
                  0.00    0.00    2.00 ^ input7/A (CLKBUF_X3)
     6   29.01    0.02    0.04    2.04 ^ input7/Z (CLKBUF_X3)
                                         net6 (net)
                  0.03    0.01    2.05 ^ adapter.protocol_error$_DFFE_PN0P_/RN (DFFR_X1)
                                  2.05   data arrival time

                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   11.76    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.00    0.00    0.00 ^ clkbuf_0_clk/A (CLKBUF_X3)
     8   40.39    0.03    0.06    0.06 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.03    0.00    0.06 ^ clkbuf_3_2__f_clk/A (CLKBUF_X3)
     8   22.46    0.02    0.05    0.11 ^ clkbuf_3_2__f_clk/Z (CLKBUF_X3)
                                         clknet_3_2__leaf_clk (net)
                  0.02    0.00    0.12 ^ clkbuf_leaf_47_clk/A (CLKBUF_X3)
     8   10.93    0.01    0.04    0.16 ^ clkbuf_leaf_47_clk/Z (CLKBUF_X3)
                                         clknet_leaf_47_clk (net)
                  0.01    0.00    0.16 ^ adapter.protocol_error$_DFFE_PN0P_/CK (DFFR_X1)
                          0.00    0.16   clock reconvergence pessimism
                          0.22    0.37   library removal time
                                  0.37   data required time
-----------------------------------------------------------------------------
                                  0.37   data required time
                                 -2.05   data arrival time
-----------------------------------------------------------------------------
                                  1.68   slack (MET)
```

### Path 3

- source: `/orfs/flow/reports/nangate45/attention_shared_sram_read_group_adapter_w512_s1/base/6_finish.rpt`
- stage: `finish`
- startpoint: `adapter.macro_read_count[11]$_DFFE_PN0P_`
- endpoint: `access_reduction_proven (output port clocked by clk)`
- path_group: `clk`
- path_type: `max`
- slack: `7.2500`
- data_arrival_time: `0.7500`
- data_required_time: `8.0000`

```text
Startpoint: adapter.macro_read_count[11]$_DFFE_PN0P_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: access_reduction_proven (output port clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   11.76    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.00    0.00    0.00 ^ clkbuf_0_clk/A (CLKBUF_X3)
     8   40.39    0.03    0.06    0.06 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.03    0.00    0.06 ^ clkbuf_3_7__f_clk/A (CLKBUF_X3)
     8   25.38    0.02    0.06    0.12 ^ clkbuf_3_7__f_clk/Z (CLKBUF_X3)
                                         clknet_3_7__leaf_clk (net)
                  0.02    0.00    0.12 ^ clkbuf_leaf_20_clk/A (CLKBUF_X3)
     8   10.52    0.01    0.04    0.16 ^ clkbuf_leaf_20_clk/Z (CLKBUF_X3)
                                         clknet_leaf_20_clk (net)
                  0.01    0.00    0.16 ^ adapter.macro_read_count[11]$_DFFE_PN0P_/CK (DFFR_X1)
     7   15.25    0.04    0.14    0.29 ^ adapter.macro_read_count[11]$_DFFE_PN0P_/Q (DFFR_X1)
                                         net166 (net)
...
                  0.01    0.00    0.75 ^ access_reduction_proven (out)
                                  0.75   data arrival time

                         10.00   10.00   clock clk (rise edge)
                          0.00   10.00   clock network delay (propagated)
                          0.00   10.00   clock reconvergence pessimism
                         -2.00    8.00   output external delay
                                  8.00   data required time
-----------------------------------------------------------------------------
                                  8.00   data required time
                                 -0.75   data arrival time
-----------------------------------------------------------------------------
                                  7.25   slack (MET)



```

### Path 4

- source: `/orfs/flow/reports/nangate45/attention_shared_sram_read_group_adapter_w512_s1/base/6_finish.rpt`
- stage: `finish`
- startpoint: `rst_n (input port clocked by clk)`
- endpoint: `seed_q[20]$_DFFE_PN0P_ (recovery check against rising-edge clock clk)`
- path_group: `asynchronous`
- path_type: `max`
- slack: `7.6800`
- data_arrival_time: `2.5200`
- data_required_time: `10.2000`

```text
Startpoint: rst_n (input port clocked by clk)
Endpoint: seed_q[20]$_DFFE_PN0P_ (recovery check against rising-edge clock clk)
Path Group: asynchronous
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (propagated)
                          2.00    2.00 ^ input external delay
     1    4.52    0.00    0.00    2.00 ^ rst_n (in)
                                         rst_n (net)
                  0.00    0.00    2.00 ^ input7/A (CLKBUF_X3)
     6   29.01    0.02    0.04    2.04 ^ input7/Z (CLKBUF_X3)
                                         net6 (net)
                  0.03    0.01    2.05 ^ place263/A (BUF_X2)
    29   64.37    0.07    0.09    2.15 ^ place263/Z (BUF_X2)
                                         net262 (net)
                  0.07    0.01    2.16 ^ place264/A (BUF_X2)
    34   72.26    0.08    0.11    2.27 ^ place264/Z (BUF_X2)
                                         net263 (net)
                  0.08    0.01    2.27 ^ place265/A (BUF_X2)
    34   69.55    0.08    0.11    2.38 ^ place265/Z (BUF_X2)
                                         net264 (net)
...
                                         clknet_0_clk (net)
                  0.03    0.00   10.06 ^ clkbuf_3_0__f_clk/A (CLKBUF_X3)
    10   23.30    0.02    0.06   10.12 ^ clkbuf_3_0__f_clk/Z (CLKBUF_X3)
                                         clknet_3_0__leaf_clk (net)
                  0.02    0.00   10.12 ^ clkbuf_leaf_39_clk/A (CLKBUF_X3)
     6   11.52    0.01    0.04   10.16 ^ clkbuf_leaf_39_clk/Z (CLKBUF_X3)
                                         clknet_leaf_39_clk (net)
                  0.01    0.00   10.16 ^ seed_q[20]$_DFFE_PN0P_/CK (DFFR_X1)
                          0.00   10.16   clock reconvergence pessimism
                          0.04   10.20   library recovery time
                                 10.20   data required time
-----------------------------------------------------------------------------
                                 10.20   data required time
                                 -2.52   data arrival time
-----------------------------------------------------------------------------
                                  7.68   slack (MET)
```

### Path 5

- source: `/orfs/flow/reports/nangate45/attention_shared_sram_read_group_adapter_w512_s1/base/6_finish.rpt`
- stage: `finish`
- startpoint: `issued_q[14]$_DFFE_PN0N_`
- endpoint: `adapter.beat_request_count[40]$_DFFE_PN0N_`
- path_group: `clk`
- path_type: `max`
- slack: `9.1500`
- data_arrival_time: `0.9900`
- data_required_time: `10.1300`

```text
Startpoint: issued_q[14]$_DFFE_PN0N_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: adapter.beat_request_count[40]$_DFFE_PN0N_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

  Delay    Time   Description
---------------------------------------------------------
   0.00    0.00   clock clk (rise edge)
   0.00    0.00   clock source latency
   0.00    0.00 ^ clk (in)
   0.06    0.06 ^ clkbuf_0_clk/Z (CLKBUF_X3)
   0.06    0.12 ^ clkbuf_3_1__f_clk/Z (CLKBUF_X3)
   0.04    0.16 ^ clkbuf_leaf_48_clk/Z (CLKBUF_X3)
   0.00    0.16 ^ issued_q[14]$_DFFE_PN0N_/CK (DFFR_X1)
   0.14    0.30 ^ issued_q[14]$_DFFE_PN0N_/Q (DFFR_X1)
   0.08    0.38 ^ _4285_/CO (HA_X1)
   0.06    0.44 v _2557_/ZN (NAND4_X1)
   0.05    0.50 v _2605_/ZN (XNOR2_X1)
   0.12    0.62 v _2606_/ZN (OR4_X1)
   0.03    0.65 ^ _2616_/ZN (OAI211_X2)
   0.04    0.69 v _2853_/ZN (NAND4_X2)
   0.10    0.79 ^ _2854_/ZN (AOI21_X4)
...
   0.00   10.00 ^ clk (in)
   0.06   10.06 ^ clkbuf_0_clk/Z (CLKBUF_X3)
   0.06   10.12 ^ clkbuf_3_5__f_clk/Z (CLKBUF_X3)
   0.04   10.17 ^ clkbuf_leaf_16_clk/Z (CLKBUF_X3)
   0.00   10.17 ^ adapter.beat_request_count[40]$_DFFE_PN0N_/CK (DFFR_X1)
   0.00   10.17   clock reconvergence pessimism
  -0.03   10.13   library setup time
          10.13   data required time
---------------------------------------------------------
          10.13   data required time
          -0.99   data arrival time
---------------------------------------------------------
           9.15   slack (MET)



```


## Worst Timing Paths Across All Stages

### Path 1

- source: `/orfs/flow/reports/nangate45/attention_shared_sram_read_group_adapter_w512_s1/base/3_detailed_place.rpt`
- stage: `detailed_place`
- startpoint: `issued_q[28]$_DFFE_PN0N_`
- endpoint: `issued_q[28]$_DFFE_PN0N_`
- path_group: `clk`
- path_type: `min`
- slack: `0.0800`
- data_arrival_time: `0.0900`
- data_required_time: `0.0000`

```text
Startpoint: issued_q[28]$_DFFE_PN0N_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: issued_q[28]$_DFFE_PN0N_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                  0.00    0.00    0.00 ^ issued_q[28]$_DFFE_PN0N_/CK (DFFR_X1)
     2    2.85    0.01    0.09    0.09 v issued_q[28]$_DFFE_PN0N_/Q (DFFR_X1)
                                         issued_q[28] (net)
                  0.01    0.00    0.09 v issued_q[28]$_DFFE_PN0N_/D (DFFR_X1)
                                  0.09   data arrival time

                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                          0.00    0.00   clock reconvergence pessimism
                                  0.00 ^ issued_q[28]$_DFFE_PN0N_/CK (DFFR_X1)
                          0.00    0.00   library hold time
                                  0.00   data required time
-----------------------------------------------------------------------------
                                  0.00   data required time
                                 -0.09   data arrival time
-----------------------------------------------------------------------------
                                  0.08   slack (MET)



```

### Path 2

- source: `/orfs/flow/reports/nangate45/attention_shared_sram_read_group_adapter_w512_s1/base/3_global_place.rpt`
- stage: `global_place`
- startpoint: `issued_q[30]$_DFFE_PN0N_`
- endpoint: `issued_q[30]$_DFFE_PN0N_`
- path_group: `clk`
- path_type: `min`
- slack: `0.0800`
- data_arrival_time: `0.0900`
- data_required_time: `0.0000`

```text
Startpoint: issued_q[30]$_DFFE_PN0N_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: issued_q[30]$_DFFE_PN0N_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                  0.00    0.00    0.00 ^ issued_q[30]$_DFFE_PN0N_/CK (DFFR_X1)
     2    2.78    0.01    0.09    0.09 v issued_q[30]$_DFFE_PN0N_/Q (DFFR_X1)
                                         issued_q[30] (net)
                  0.01    0.00    0.09 v issued_q[30]$_DFFE_PN0N_/D (DFFR_X1)
                                  0.09   data arrival time

                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                          0.00    0.00   clock reconvergence pessimism
                                  0.00 ^ issued_q[30]$_DFFE_PN0N_/CK (DFFR_X1)
                          0.00    0.00   library hold time
                                  0.00   data required time
-----------------------------------------------------------------------------
                                  0.00   data required time
                                 -0.09   data arrival time
-----------------------------------------------------------------------------
                                  0.08   slack (MET)



```

### Path 3

- source: `/orfs/flow/reports/nangate45/attention_shared_sram_read_group_adapter_w512_s1/base/3_resizer.rpt`
- stage: `resizer`
- startpoint: `issued_q[30]$_DFFE_PN0N_`
- endpoint: `issued_q[30]$_DFFE_PN0N_`
- path_group: `clk`
- path_type: `min`
- slack: `0.0800`
- data_arrival_time: `0.0900`
- data_required_time: `0.0000`

```text
Startpoint: issued_q[30]$_DFFE_PN0N_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: issued_q[30]$_DFFE_PN0N_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                  0.00    0.00    0.00 ^ issued_q[30]$_DFFE_PN0N_/CK (DFFR_X1)
     2    2.78    0.01    0.09    0.09 v issued_q[30]$_DFFE_PN0N_/Q (DFFR_X1)
                                         issued_q[30] (net)
                  0.01    0.00    0.09 v issued_q[30]$_DFFE_PN0N_/D (DFFR_X1)
                                  0.09   data arrival time

                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                          0.00    0.00   clock reconvergence pessimism
                                  0.00 ^ issued_q[30]$_DFFE_PN0N_/CK (DFFR_X1)
                          0.00    0.00   library hold time
                                  0.00   data required time
-----------------------------------------------------------------------------
                                  0.00   data required time
                                 -0.09   data arrival time
-----------------------------------------------------------------------------
                                  0.08   slack (MET)



```

### Path 4

- source: `/orfs/flow/reports/nangate45/attention_shared_sram_read_group_adapter_w512_s1/base/2_floorplan_final.rpt`
- stage: `floorplan`
- startpoint: `running_q$_DFF_PN0_ (rising edge-triggered flip-flop clocked by clk)`
- endpoint: `running_q$_DFF_PN0_ (rising edge-triggered flip-flop clocked by clk)`
- path_group: `clk`
- path_type: `min`
- slack: `0.0900`
- data_arrival_time: `0.0900`
- data_required_time: `0.0000`

```text
Startpoint: running_q$_DFF_PN0_ (rising edge-triggered flip-flop clocked by clk)
Endpoint: running_q$_DFF_PN0_ (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                  0.00    0.00    0.00 ^ running_q$_DFF_PN0_/CK (DFFR_X1)
     3    5.07    0.02    0.07    0.07 ^ running_q$_DFF_PN0_/QN (DFFR_X1)
                                         _0007_ (net)
                  0.02    0.00    0.07 ^ _2503_/B2 (AOI21_X1)
     1    1.05    0.01    0.02    0.09 v _2503_/ZN (AOI21_X1)
                                         _0000_ (net)
                  0.01    0.00    0.09 v running_q$_DFF_PN0_/D (DFFR_X1)
                                  0.09   data arrival time

                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                          0.00    0.00   clock reconvergence pessimism
                                  0.00 ^ running_q$_DFF_PN0_/CK (DFFR_X1)
                          0.00    0.00   library hold time
                                  0.00   data required time
-----------------------------------------------------------------------------
                                  0.00   data required time
                                 -0.09   data arrival time
-----------------------------------------------------------------------------
                                  0.09   slack (MET)



```

### Path 5

- source: `/orfs/flow/reports/nangate45/attention_shared_sram_read_group_adapter_w512_s1/base/4_cts_final.rpt`
- stage: `cts`
- startpoint: `issued_q[28]$_DFFE_PN0N_`
- endpoint: `issued_q[28]$_DFFE_PN0N_`
- path_group: `clk`
- path_type: `min`
- slack: `0.0900`
- data_arrival_time: `0.2600`
- data_required_time: `0.1700`

```text
Startpoint: issued_q[28]$_DFFE_PN0N_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: issued_q[28]$_DFFE_PN0N_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   19.09    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.00    0.00    0.00 ^ clkbuf_0_clk/A (CLKBUF_X3)
     8   50.80    0.04    0.06    0.07 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.04    0.00    0.07 ^ clkbuf_3_2__f_clk/A (CLKBUF_X3)
     8   23.75    0.02    0.06    0.13 ^ clkbuf_3_2__f_clk/Z (CLKBUF_X3)
                                         clknet_3_2__leaf_clk (net)
                  0.02    0.00    0.13 ^ clkbuf_leaf_46_clk/A (CLKBUF_X3)
     8   10.17    0.01    0.04    0.17 ^ clkbuf_leaf_46_clk/Z (CLKBUF_X3)
                                         clknet_leaf_46_clk (net)
                  0.01    0.00    0.17 ^ issued_q[28]$_DFFE_PN0N_/CK (DFFR_X1)
     2    2.90    0.01    0.09    0.26 v issued_q[28]$_DFFE_PN0N_/Q (DFFR_X1)
...
                                         clknet_3_2__leaf_clk (net)
                  0.02    0.00    0.13 ^ clkbuf_leaf_46_clk/A (CLKBUF_X3)
     8   10.17    0.01    0.04    0.17 ^ clkbuf_leaf_46_clk/Z (CLKBUF_X3)
                                         clknet_leaf_46_clk (net)
                  0.01    0.00    0.17 ^ issued_q[28]$_DFFE_PN0N_/CK (DFFR_X1)
                          0.00    0.17   clock reconvergence pessimism
                          0.01    0.17   library hold time
                                  0.17   data required time
-----------------------------------------------------------------------------
                                  0.17   data required time
                                 -0.26   data arrival time
-----------------------------------------------------------------------------
                                  0.09   slack (MET)



```

### Path 6

- source: `/orfs/flow/reports/nangate45/attention_shared_sram_read_group_adapter_w512_s1/base/5_global_route.rpt`
- stage: `route`
- startpoint: `issued_q[26]$_DFFE_PN0N_`
- endpoint: `issued_q[26]$_DFFE_PN0N_`
- path_group: `clk`
- path_type: `min`
- slack: `0.0900`
- data_arrival_time: `0.2600`
- data_required_time: `0.1700`

```text
Startpoint: issued_q[26]$_DFFE_PN0N_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: issued_q[26]$_DFFE_PN0N_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   17.96    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.00    0.00    0.00 ^ clkbuf_0_clk/A (CLKBUF_X3)
     8   51.10    0.04    0.06    0.07 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.04    0.00    0.07 ^ clkbuf_3_2__f_clk/A (CLKBUF_X3)
     8   23.54    0.02    0.06    0.13 ^ clkbuf_3_2__f_clk/Z (CLKBUF_X3)
                                         clknet_3_2__leaf_clk (net)
                  0.02    0.00    0.13 ^ clkbuf_leaf_47_clk/A (CLKBUF_X3)
     8   10.68    0.01    0.04    0.17 ^ clkbuf_leaf_47_clk/Z (CLKBUF_X3)
                                         clknet_leaf_47_clk (net)
                  0.01    0.00    0.17 ^ issued_q[26]$_DFFE_PN0N_/CK (DFFR_X1)
     2    2.90    0.01    0.09    0.26 v issued_q[26]$_DFFE_PN0N_/Q (DFFR_X1)
...
                                         clknet_3_2__leaf_clk (net)
                  0.02    0.00    0.13 ^ clkbuf_leaf_47_clk/A (CLKBUF_X3)
     8   10.68    0.01    0.04    0.17 ^ clkbuf_leaf_47_clk/Z (CLKBUF_X3)
                                         clknet_leaf_47_clk (net)
                  0.01    0.00    0.17 ^ issued_q[26]$_DFFE_PN0N_/CK (DFFR_X1)
                          0.00    0.17   clock reconvergence pessimism
                          0.01    0.17   library hold time
                                  0.17   data required time
-----------------------------------------------------------------------------
                                  0.17   data required time
                                 -0.26   data arrival time
-----------------------------------------------------------------------------
                                  0.09   slack (MET)



```

### Path 7

- source: `/orfs/flow/reports/nangate45/attention_shared_sram_read_group_adapter_w512_s1/base/6_finish.rpt`
- stage: `finish`
- startpoint: `issued_q[28]$_DFFE_PN0N_`
- endpoint: `issued_q[28]$_DFFE_PN0N_`
- path_group: `clk`
- path_type: `min`
- slack: `0.0900`
- data_arrival_time: `0.2500`
- data_required_time: `0.1600`

```text
Startpoint: issued_q[28]$_DFFE_PN0N_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: issued_q[28]$_DFFE_PN0N_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   11.76    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.00    0.00    0.00 ^ clkbuf_0_clk/A (CLKBUF_X3)
     8   40.39    0.03    0.06    0.06 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.03    0.00    0.06 ^ clkbuf_3_2__f_clk/A (CLKBUF_X3)
     8   22.46    0.02    0.05    0.11 ^ clkbuf_3_2__f_clk/Z (CLKBUF_X3)
                                         clknet_3_2__leaf_clk (net)
                  0.02    0.00    0.12 ^ clkbuf_leaf_46_clk/A (CLKBUF_X3)
     8   10.24    0.01    0.04    0.16 ^ clkbuf_leaf_46_clk/Z (CLKBUF_X3)
                                         clknet_leaf_46_clk (net)
                  0.01    0.00    0.16 ^ issued_q[28]$_DFFE_PN0N_/CK (DFFR_X1)
     2    2.84    0.01    0.09    0.25 v issued_q[28]$_DFFE_PN0N_/Q (DFFR_X1)
...
                                         clknet_3_2__leaf_clk (net)
                  0.02    0.00    0.12 ^ clkbuf_leaf_46_clk/A (CLKBUF_X3)
     8   10.24    0.01    0.04    0.16 ^ clkbuf_leaf_46_clk/Z (CLKBUF_X3)
                                         clknet_leaf_46_clk (net)
                  0.01    0.00    0.16 ^ issued_q[28]$_DFFE_PN0N_/CK (DFFR_X1)
                          0.00    0.16   clock reconvergence pessimism
                          0.01    0.16   library hold time
                                  0.16   data required time
-----------------------------------------------------------------------------
                                  0.16   data required time
                                 -0.25   data arrival time
-----------------------------------------------------------------------------
                                  0.09   slack (MET)



```

### Path 8

- source: `/orfs/flow/reports/nangate45/attention_shared_sram_read_group_adapter_w512_s1/base/4_cts_final.rpt`
- stage: `cts`
- startpoint: `rst_n (input port clocked by clk)`
- endpoint: `adapter.protocol_error$_DFFE_PN0P_`
- path_group: `asynchronous`
- path_type: `min`
- slack: `1.6700`
- data_arrival_time: `2.0600`
- data_required_time: `0.3900`

```text
Startpoint: rst_n (input port clocked by clk)
Endpoint: adapter.protocol_error$_DFFE_PN0P_
          (removal check against rising-edge clock clk)
Path Group: asynchronous
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (propagated)
                          2.00    2.00 ^ input external delay
     1    4.85    0.00    0.00    2.00 ^ rst_n (in)
                                         rst_n (net)
                  0.00    0.00    2.00 ^ input7/A (CLKBUF_X3)
     6   32.29    0.02    0.04    2.04 ^ input7/Z (CLKBUF_X3)
                                         net6 (net)
                  0.03    0.01    2.06 ^ adapter.protocol_error$_DFFE_PN0P_/RN (DFFR_X1)
                                  2.06   data arrival time

                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   19.09    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.00    0.00    0.00 ^ clkbuf_0_clk/A (CLKBUF_X3)
     8   50.80    0.04    0.06    0.07 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.04    0.00    0.07 ^ clkbuf_3_2__f_clk/A (CLKBUF_X3)
     8   23.75    0.02    0.06    0.13 ^ clkbuf_3_2__f_clk/Z (CLKBUF_X3)
                                         clknet_3_2__leaf_clk (net)
                  0.02    0.00    0.13 ^ clkbuf_leaf_47_clk/A (CLKBUF_X3)
     8   10.85    0.01    0.04    0.17 ^ clkbuf_leaf_47_clk/Z (CLKBUF_X3)
                                         clknet_leaf_47_clk (net)
                  0.01    0.00    0.17 ^ adapter.protocol_error$_DFFE_PN0P_/CK (DFFR_X1)
                          0.00    0.17   clock reconvergence pessimism
                          0.22    0.39   library removal time
                                  0.39   data required time
-----------------------------------------------------------------------------
                                  0.39   data required time
                                 -2.06   data arrival time
-----------------------------------------------------------------------------
                                  1.67   slack (MET)
```
