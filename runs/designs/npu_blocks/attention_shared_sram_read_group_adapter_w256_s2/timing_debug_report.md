# OpenROAD Timing Debug Summary

- design_dir: `runs/designs/npu_blocks/attention_shared_sram_read_group_adapter_w256_s2`
- metrics_path: `runs/designs/npu_blocks/attention_shared_sram_read_group_adapter_w256_s2/metrics.csv`
- rows_considered: 4

## Metrics Rows

| param_hash | tag | status | critical_path_ns | density | result_path |
| --- | --- | --- | ---: | ---: | --- |
| 07ed8cb5 | attention_shared_sram_read_group_adapter_ppa_v1_07ed8cb5 | ok | 0.6831 | 0.5 | `/orfs/flow/reports/nangate45/attention_shared_sram_read_group_adapter_w256_s2/base/6_finish.rpt` |
| 1fd76a90 | attention_shared_sram_read_group_adapter_ppa_v1_1fd76a90 | ok | 0.7279 | 0.5 | `/orfs/flow/reports/nangate45/attention_shared_sram_read_group_adapter_w256_s2/base/6_finish.rpt` |
| 8574f558 | attention_shared_sram_read_group_adapter_ppa_v1_8574f558 | ok | 0.7288 | 0.5 | `/orfs/flow/reports/nangate45/attention_shared_sram_read_group_adapter_w256_s2/base/6_finish.rpt` |
| 77ace606 | attention_shared_sram_read_group_adapter_ppa_v1_77ace606 | ok | 0.7343 | 0.5 | `/orfs/flow/reports/nangate45/attention_shared_sram_read_group_adapter_w256_s2/base/6_finish.rpt` |

## Inspected Report Files

- `/orfs/flow/reports/nangate45/attention_shared_sram_read_group_adapter_w256_s2/base/6_finish.rpt`
- `/orfs/flow/reports/nangate45/attention_shared_sram_read_group_adapter_w256_s2/base/5_global_route.rpt`
- `/orfs/flow/reports/nangate45/attention_shared_sram_read_group_adapter_w256_s2/base/5_route_drc.rpt`
- `/orfs/flow/reports/nangate45/attention_shared_sram_read_group_adapter_w256_s2/base/4_cts_final.rpt`
- `/orfs/flow/reports/nangate45/attention_shared_sram_read_group_adapter_w256_s2/base/3_resizer.rpt`
- `/orfs/flow/reports/nangate45/attention_shared_sram_read_group_adapter_w256_s2/base/3_detailed_place.rpt`
- `/orfs/flow/reports/nangate45/attention_shared_sram_read_group_adapter_w256_s2/base/3_global_place.rpt`
- `/orfs/flow/reports/nangate45/attention_shared_sram_read_group_adapter_w256_s2/base/2_floorplan_final.rpt`
- `/orfs/flow/reports/nangate45/attention_shared_sram_read_group_adapter_w256_s2/base/drt_antennas.log`
- `/orfs/flow/reports/nangate45/attention_shared_sram_read_group_adapter_w256_s2/base/grt_antennas.log`
- `/orfs/flow/reports/nangate45/attention_shared_sram_read_group_adapter_w256_s2/base/metadata-generate.log`

## Preferred Final-Stage Timing Paths

- raw_path_block_count: 208
- unique_path_block_count: 33
- preferred_stage: `finish`

### Path 1

- source: `/orfs/flow/reports/nangate45/attention_shared_sram_read_group_adapter_w256_s2/base/6_finish.rpt`
- stage: `finish`
- startpoint: `issued_q[31]$_DFFE_PN0N_`
- endpoint: `issued_q[31]$_DFFE_PN0N_`
- path_group: `clk`
- path_type: `min`
- slack: `0.0900`
- data_arrival_time: `0.2700`
- data_required_time: `0.1900`

```text
Startpoint: issued_q[31]$_DFFE_PN0N_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: issued_q[31]$_DFFE_PN0N_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   14.91    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.00    0.00    0.00 ^ clkbuf_0_clk/A (CLKBUF_X3)
     8   48.68    0.04    0.06    0.06 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.04    0.00    0.07 ^ clkbuf_3_4__f_clk/A (CLKBUF_X3)
    15   39.69    0.03    0.07    0.14 ^ clkbuf_3_4__f_clk/Z (CLKBUF_X3)
                                         clknet_3_4__leaf_clk (net)
                  0.03    0.00    0.14 ^ clkbuf_leaf_82_clk/A (CLKBUF_X3)
     7    8.82    0.01    0.04    0.18 ^ clkbuf_leaf_82_clk/Z (CLKBUF_X3)
                                         clknet_leaf_82_clk (net)
                  0.01    0.00    0.18 ^ issued_q[31]$_DFFE_PN0N_/CK (DFFR_X1)
     2    2.73    0.01    0.09    0.27 v issued_q[31]$_DFFE_PN0N_/Q (DFFR_X1)
...
                                         clknet_3_4__leaf_clk (net)
                  0.03    0.00    0.14 ^ clkbuf_leaf_82_clk/A (CLKBUF_X3)
     7    8.82    0.01    0.04    0.18 ^ clkbuf_leaf_82_clk/Z (CLKBUF_X3)
                                         clknet_leaf_82_clk (net)
                  0.01    0.00    0.18 ^ issued_q[31]$_DFFE_PN0N_/CK (DFFR_X1)
                          0.00    0.18   clock reconvergence pessimism
                          0.00    0.19   library hold time
                                  0.19   data required time
-----------------------------------------------------------------------------
                                  0.19   data required time
                                 -0.27   data arrival time
-----------------------------------------------------------------------------
                                  0.09   slack (MET)



```

### Path 2

- source: `/orfs/flow/reports/nangate45/attention_shared_sram_read_group_adapter_w256_s2/base/6_finish.rpt`
- stage: `finish`
- startpoint: `rst_n (input port clocked by clk)`
- endpoint: `fold_q[8]$_DFFE_PN0P_ (removal check against rising-edge clock clk)`
- path_group: `asynchronous`
- path_type: `min`
- slack: `1.6600`
- data_arrival_time: `2.0700`
- data_required_time: `0.4100`

```text
Startpoint: rst_n (input port clocked by clk)
Endpoint: fold_q[8]$_DFFE_PN0P_ (removal check against rising-edge clock clk)
Path Group: asynchronous
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (propagated)
                          2.00    2.00 ^ input external delay
     1    3.51    0.00    0.00    2.00 ^ rst_n (in)
                                         rst_n (net)
                  0.00    0.00    2.00 ^ input6/A (CLKBUF_X3)
    11   40.97    0.03    0.05    2.05 ^ input6/Z (CLKBUF_X3)
                                         net5 (net)
                  0.04    0.02    2.07 ^ fold_q[8]$_DFFE_PN0P_/RN (DFFR_X1)
                                  2.07   data arrival time

                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   14.91    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.00    0.00    0.00 ^ clkbuf_0_clk/A (CLKBUF_X3)
     8   48.68    0.04    0.06    0.06 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.04    0.00    0.07 ^ clkbuf_3_7__f_clk/A (CLKBUF_X3)
     9   35.38    0.03    0.07    0.13 ^ clkbuf_3_7__f_clk/Z (CLKBUF_X3)
                                         clknet_3_7__leaf_clk (net)
                  0.03    0.00    0.14 ^ clkbuf_leaf_42_clk/A (CLKBUF_X3)
     7   10.84    0.01    0.04    0.18 ^ clkbuf_leaf_42_clk/Z (CLKBUF_X3)
                                         clknet_leaf_42_clk (net)
                  0.01    0.00    0.18 ^ fold_q[8]$_DFFE_PN0P_/CK (DFFR_X1)
                          0.00    0.18   clock reconvergence pessimism
                          0.23    0.41   library removal time
                                  0.41   data required time
-----------------------------------------------------------------------------
                                  0.41   data required time
                                 -2.07   data arrival time
-----------------------------------------------------------------------------
                                  1.66   slack (MET)
```

### Path 3

- source: `/orfs/flow/reports/nangate45/attention_shared_sram_read_group_adapter_w256_s2/base/6_finish.rpt`
- stage: `finish`
- startpoint: `adapter.macro_read_count[59]$_DFFE_PN0P_`
- endpoint: `access_reduction_proven (output port clocked by clk)`
- path_group: `clk`
- path_type: `max`
- slack: `7.2700`
- data_arrival_time: `0.7300`
- data_required_time: `8.0000`

```text
Startpoint: adapter.macro_read_count[59]$_DFFE_PN0P_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: access_reduction_proven (output port clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   14.91    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.00    0.00    0.00 ^ clkbuf_0_clk/A (CLKBUF_X3)
     8   48.68    0.04    0.06    0.06 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.04    0.00    0.07 ^ clkbuf_3_3__f_clk/A (CLKBUF_X3)
    12   31.90    0.03    0.06    0.13 ^ clkbuf_3_3__f_clk/Z (CLKBUF_X3)
                                         clknet_3_3__leaf_clk (net)
                  0.03    0.00    0.13 ^ clkbuf_leaf_20_clk/A (CLKBUF_X3)
     8   10.05    0.01    0.04    0.18 ^ clkbuf_leaf_20_clk/Z (CLKBUF_X3)
                                         clknet_leaf_20_clk (net)
                  0.01    0.00    0.18 ^ adapter.macro_read_count[59]$_DFFE_PN0P_/CK (DFFR_X1)
     6   12.13    0.03    0.13    0.30 ^ adapter.macro_read_count[59]$_DFFE_PN0P_/Q (DFFR_X1)
                                         adapter.macro_read_count[59] (net)
...
                  0.02    0.00    0.73 ^ access_reduction_proven (out)
                                  0.73   data arrival time

                         10.00   10.00   clock clk (rise edge)
                          0.00   10.00   clock network delay (propagated)
                          0.00   10.00   clock reconvergence pessimism
                         -2.00    8.00   output external delay
                                  8.00   data required time
-----------------------------------------------------------------------------
                                  8.00   data required time
                                 -0.73   data arrival time
-----------------------------------------------------------------------------
                                  7.27   slack (MET)



```

### Path 4

- source: `/orfs/flow/reports/nangate45/attention_shared_sram_read_group_adapter_w256_s2/base/6_finish.rpt`
- stage: `finish`
- startpoint: `rst_n (input port clocked by clk)`
- endpoint: `adapter.macro_read_count[60]$_DFFE_PN0P_`
- path_group: `asynchronous`
- path_type: `max`
- slack: `7.6900`
- data_arrival_time: `2.5300`
- data_required_time: `10.2200`

```text
Startpoint: rst_n (input port clocked by clk)
Endpoint: adapter.macro_read_count[60]$_DFFE_PN0P_
          (recovery check against rising-edge clock clk)
Path Group: asynchronous
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (propagated)
                          2.00    2.00 ^ input external delay
     1    3.51    0.00    0.00    2.00 ^ rst_n (in)
                                         rst_n (net)
                  0.00    0.00    2.00 ^ input6/A (CLKBUF_X3)
    11   40.97    0.03    0.05    2.05 ^ input6/Z (CLKBUF_X3)
                                         net5 (net)
                  0.03    0.00    2.05 ^ place300/A (BUF_X2)
    35   76.74    0.09    0.11    2.16 ^ place300/Z (BUF_X2)
                                         net299 (net)
                  0.09    0.00    2.17 ^ place301/A (BUF_X2)
    32   68.80    0.08    0.11    2.27 ^ place301/Z (BUF_X2)
                                         net300 (net)
                  0.08    0.01    2.28 ^ place303/A (BUF_X1)
    19   39.28    0.09    0.12    2.40 ^ place303/Z (BUF_X1)
...
                                         clknet_0_clk (net)
                  0.04    0.00   10.07 ^ clkbuf_3_3__f_clk/A (CLKBUF_X3)
    12   31.90    0.03    0.06   10.13 ^ clkbuf_3_3__f_clk/Z (CLKBUF_X3)
                                         clknet_3_3__leaf_clk (net)
                  0.03    0.00   10.13 ^ clkbuf_leaf_22_clk/A (CLKBUF_X3)
     7    9.35    0.01    0.04   10.17 ^ clkbuf_leaf_22_clk/Z (CLKBUF_X3)
                                         clknet_leaf_22_clk (net)
                  0.01    0.00   10.17 ^ adapter.macro_read_count[60]$_DFFE_PN0P_/CK (DFFR_X1)
                          0.00   10.17   clock reconvergence pessimism
                          0.04   10.22   library recovery time
                                 10.22   data required time
-----------------------------------------------------------------------------
                                 10.22   data required time
                                 -2.53   data arrival time
-----------------------------------------------------------------------------
                                  7.69   slack (MET)
```

### Path 5

- source: `/orfs/flow/reports/nangate45/attention_shared_sram_read_group_adapter_w256_s2/base/6_finish.rpt`
- stage: `finish`
- startpoint: `adapter.collect_slot_q$_DFFE_PN0P_`
- endpoint: `adapter.slot_base_addr[0][11]$_DFFE_PN0P_`
- path_group: `clk`
- path_type: `max`
- slack: `8.8100`
- data_arrival_time: `1.3300`
- data_required_time: `10.1400`

```text
Startpoint: adapter.collect_slot_q$_DFFE_PN0P_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: adapter.slot_base_addr[0][11]$_DFFE_PN0P_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

  Delay    Time   Description
---------------------------------------------------------
   0.00    0.00   clock clk (rise edge)
   0.00    0.00   clock source latency
   0.00    0.00 ^ clk (in)
   0.06    0.06 ^ clkbuf_0_clk/Z (CLKBUF_X3)
   0.07    0.14 ^ clkbuf_3_4__f_clk/Z (CLKBUF_X3)
   0.05    0.18 ^ clkbuf_leaf_80_clk/Z (CLKBUF_X3)
   0.00    0.18 ^ adapter.collect_slot_q$_DFFE_PN0P_/CK (DFFR_X2)
   0.20    0.39 ^ adapter.collect_slot_q$_DFFE_PN0P_/Q (DFFR_X2)
   0.13    0.52 ^ place297/Z (BUF_X1)
   0.08    0.60 v _3162_/Z (MUX2_X1)
   0.04    0.63 ^ _3432_/ZN (XNOR2_X1)
   0.05    0.68 v _3437_/ZN (NAND4_X1)
   0.08    0.76 ^ _3438_/ZN (NOR4_X2)
   0.05    0.81 v _3471_/ZN (NAND4_X1)
   0.09    0.90 ^ _3505_/ZN (OAI33_X1)
...
   0.00   10.00 ^ clk (in)
   0.06   10.06 ^ clkbuf_0_clk/Z (CLKBUF_X3)
   0.07   10.13 ^ clkbuf_3_6__f_clk/Z (CLKBUF_X3)
   0.04   10.18 ^ clkbuf_leaf_72_clk/Z (CLKBUF_X3)
   0.00   10.18 ^ adapter.slot_base_addr[0][11]$_DFFE_PN0P_/CK (DFFR_X1)
   0.00   10.18   clock reconvergence pessimism
  -0.04   10.14   library setup time
          10.14   data required time
---------------------------------------------------------
          10.14   data required time
          -1.33   data arrival time
---------------------------------------------------------
           8.81   slack (MET)



```


## Worst Timing Paths Across All Stages

### Path 1

- source: `/orfs/flow/reports/nangate45/attention_shared_sram_read_group_adapter_w256_s2/base/3_detailed_place.rpt`
- stage: `detailed_place`
- startpoint: `issued_q[27]$_DFFE_PN0N_`
- endpoint: `issued_q[27]$_DFFE_PN0N_`
- path_group: `clk`
- path_type: `min`
- slack: `0.0800`
- data_arrival_time: `0.0900`
- data_required_time: `0.0000`

```text
Startpoint: issued_q[27]$_DFFE_PN0N_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: issued_q[27]$_DFFE_PN0N_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                  0.00    0.00    0.00 ^ issued_q[27]$_DFFE_PN0N_/CK (DFFR_X1)
     2    2.70    0.01    0.09    0.09 v issued_q[27]$_DFFE_PN0N_/Q (DFFR_X1)
                                         issued_q[27] (net)
                  0.01    0.00    0.09 v issued_q[27]$_DFFE_PN0N_/D (DFFR_X1)
                                  0.09   data arrival time

                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                          0.00    0.00   clock reconvergence pessimism
                                  0.00 ^ issued_q[27]$_DFFE_PN0N_/CK (DFFR_X1)
                          0.00    0.00   library hold time
                                  0.00   data required time
-----------------------------------------------------------------------------
                                  0.00   data required time
                                 -0.09   data arrival time
-----------------------------------------------------------------------------
                                  0.08   slack (MET)



```

### Path 2

- source: `/orfs/flow/reports/nangate45/attention_shared_sram_read_group_adapter_w256_s2/base/3_global_place.rpt`
- stage: `global_place`
- startpoint: `issued_q[31]$_DFFE_PN0N_`
- endpoint: `issued_q[31]$_DFFE_PN0N_`
- path_group: `clk`
- path_type: `min`
- slack: `0.0800`
- data_arrival_time: `0.0900`
- data_required_time: `0.0000`

```text
Startpoint: issued_q[31]$_DFFE_PN0N_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: issued_q[31]$_DFFE_PN0N_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                  0.00    0.00    0.00 ^ issued_q[31]$_DFFE_PN0N_/CK (DFFR_X1)
     2    2.73    0.01    0.09    0.09 v issued_q[31]$_DFFE_PN0N_/Q (DFFR_X1)
                                         issued_q[31] (net)
                  0.01    0.00    0.09 v issued_q[31]$_DFFE_PN0N_/D (DFFR_X1)
                                  0.09   data arrival time

                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                          0.00    0.00   clock reconvergence pessimism
                                  0.00 ^ issued_q[31]$_DFFE_PN0N_/CK (DFFR_X1)
                          0.00    0.00   library hold time
                                  0.00   data required time
-----------------------------------------------------------------------------
                                  0.00   data required time
                                 -0.09   data arrival time
-----------------------------------------------------------------------------
                                  0.08   slack (MET)



```

### Path 3

- source: `/orfs/flow/reports/nangate45/attention_shared_sram_read_group_adapter_w256_s2/base/3_resizer.rpt`
- stage: `resizer`
- startpoint: `issued_q[31]$_DFFE_PN0N_`
- endpoint: `issued_q[31]$_DFFE_PN0N_`
- path_group: `clk`
- path_type: `min`
- slack: `0.0800`
- data_arrival_time: `0.0900`
- data_required_time: `0.0000`

```text
Startpoint: issued_q[31]$_DFFE_PN0N_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: issued_q[31]$_DFFE_PN0N_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                  0.00    0.00    0.00 ^ issued_q[31]$_DFFE_PN0N_/CK (DFFR_X1)
     2    2.73    0.01    0.09    0.09 v issued_q[31]$_DFFE_PN0N_/Q (DFFR_X1)
                                         issued_q[31] (net)
                  0.01    0.00    0.09 v issued_q[31]$_DFFE_PN0N_/D (DFFR_X1)
                                  0.09   data arrival time

                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                          0.00    0.00   clock reconvergence pessimism
                                  0.00 ^ issued_q[31]$_DFFE_PN0N_/CK (DFFR_X1)
                          0.00    0.00   library hold time
                                  0.00   data required time
-----------------------------------------------------------------------------
                                  0.00   data required time
                                 -0.09   data arrival time
-----------------------------------------------------------------------------
                                  0.08   slack (MET)



```

### Path 4

- source: `/orfs/flow/reports/nangate45/attention_shared_sram_read_group_adapter_w256_s2/base/2_floorplan_final.rpt`
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
     3    5.08    0.02    0.07    0.07 ^ running_q$_DFF_PN0_/QN (DFFR_X1)
                                         _0010_ (net)
                  0.02    0.00    0.07 ^ _3308_/B2 (AOI21_X1)
     1    1.05    0.01    0.02    0.09 v _3308_/ZN (AOI21_X1)
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

- source: `/orfs/flow/reports/nangate45/attention_shared_sram_read_group_adapter_w256_s2/base/4_cts_final.rpt`
- stage: `cts`
- startpoint: `issued_q[27]$_DFFE_PN0N_`
- endpoint: `issued_q[27]$_DFFE_PN0N_`
- path_group: `clk`
- path_type: `min`
- slack: `0.0900`
- data_arrival_time: `0.2900`
- data_required_time: `0.2100`

```text
Startpoint: issued_q[27]$_DFFE_PN0N_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: issued_q[27]$_DFFE_PN0N_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   23.92    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.00    0.00    0.00 ^ clkbuf_0_clk/A (CLKBUF_X3)
     8   61.48    0.05    0.07    0.08 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.05    0.00    0.08 ^ clkbuf_3_4__f_clk/A (CLKBUF_X3)
    15   44.17    0.04    0.08    0.16 ^ clkbuf_3_4__f_clk/Z (CLKBUF_X3)
                                         clknet_3_4__leaf_clk (net)
                  0.04    0.00    0.16 ^ clkbuf_leaf_83_clk/A (CLKBUF_X3)
     8    9.63    0.01    0.05    0.20 ^ clkbuf_leaf_83_clk/Z (CLKBUF_X3)
                                         clknet_leaf_83_clk (net)
                  0.01    0.00    0.20 ^ issued_q[27]$_DFFE_PN0N_/CK (DFFR_X1)
     2    2.75    0.01    0.09    0.29 v issued_q[27]$_DFFE_PN0N_/Q (DFFR_X1)
...
                                         clknet_3_4__leaf_clk (net)
                  0.04    0.00    0.16 ^ clkbuf_leaf_83_clk/A (CLKBUF_X3)
     8    9.63    0.01    0.05    0.20 ^ clkbuf_leaf_83_clk/Z (CLKBUF_X3)
                                         clknet_leaf_83_clk (net)
                  0.01    0.00    0.20 ^ issued_q[27]$_DFFE_PN0N_/CK (DFFR_X1)
                          0.00    0.20   clock reconvergence pessimism
                          0.01    0.21   library hold time
                                  0.21   data required time
-----------------------------------------------------------------------------
                                  0.21   data required time
                                 -0.29   data arrival time
-----------------------------------------------------------------------------
                                  0.09   slack (MET)



```

### Path 6

- source: `/orfs/flow/reports/nangate45/attention_shared_sram_read_group_adapter_w256_s2/base/5_global_route.rpt`
- stage: `route`
- startpoint: `issued_q[31]$_DFFE_PN0N_`
- endpoint: `issued_q[31]$_DFFE_PN0N_`
- path_group: `clk`
- path_type: `min`
- slack: `0.0900`
- data_arrival_time: `0.2900`
- data_required_time: `0.2100`

```text
Startpoint: issued_q[31]$_DFFE_PN0N_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: issued_q[31]$_DFFE_PN0N_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   22.82    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.00    0.00    0.00 ^ clkbuf_0_clk/A (CLKBUF_X3)
     8   61.19    0.05    0.07    0.07 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.05    0.00    0.08 ^ clkbuf_3_4__f_clk/A (CLKBUF_X3)
    15   43.76    0.04    0.08    0.15 ^ clkbuf_3_4__f_clk/Z (CLKBUF_X3)
                                         clknet_3_4__leaf_clk (net)
                  0.04    0.00    0.16 ^ clkbuf_leaf_82_clk/A (CLKBUF_X3)
     7    9.14    0.01    0.04    0.20 ^ clkbuf_leaf_82_clk/Z (CLKBUF_X3)
                                         clknet_leaf_82_clk (net)
                  0.01    0.00    0.20 ^ issued_q[31]$_DFFE_PN0N_/CK (DFFR_X1)
     2    2.94    0.01    0.09    0.29 v issued_q[31]$_DFFE_PN0N_/Q (DFFR_X1)
...
                                         clknet_3_4__leaf_clk (net)
                  0.04    0.00    0.16 ^ clkbuf_leaf_82_clk/A (CLKBUF_X3)
     7    9.14    0.01    0.04    0.20 ^ clkbuf_leaf_82_clk/Z (CLKBUF_X3)
                                         clknet_leaf_82_clk (net)
                  0.01    0.00    0.20 ^ issued_q[31]$_DFFE_PN0N_/CK (DFFR_X1)
                          0.00    0.20   clock reconvergence pessimism
                          0.01    0.21   library hold time
                                  0.21   data required time
-----------------------------------------------------------------------------
                                  0.21   data required time
                                 -0.29   data arrival time
-----------------------------------------------------------------------------
                                  0.09   slack (MET)



```

### Path 7

- source: `/orfs/flow/reports/nangate45/attention_shared_sram_read_group_adapter_w256_s2/base/6_finish.rpt`
- stage: `finish`
- startpoint: `issued_q[31]$_DFFE_PN0N_`
- endpoint: `issued_q[31]$_DFFE_PN0N_`
- path_group: `clk`
- path_type: `min`
- slack: `0.0900`
- data_arrival_time: `0.2700`
- data_required_time: `0.1900`

```text
Startpoint: issued_q[31]$_DFFE_PN0N_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: issued_q[31]$_DFFE_PN0N_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   14.91    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.00    0.00    0.00 ^ clkbuf_0_clk/A (CLKBUF_X3)
     8   48.68    0.04    0.06    0.06 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.04    0.00    0.07 ^ clkbuf_3_4__f_clk/A (CLKBUF_X3)
    15   39.69    0.03    0.07    0.14 ^ clkbuf_3_4__f_clk/Z (CLKBUF_X3)
                                         clknet_3_4__leaf_clk (net)
                  0.03    0.00    0.14 ^ clkbuf_leaf_82_clk/A (CLKBUF_X3)
     7    8.82    0.01    0.04    0.18 ^ clkbuf_leaf_82_clk/Z (CLKBUF_X3)
                                         clknet_leaf_82_clk (net)
                  0.01    0.00    0.18 ^ issued_q[31]$_DFFE_PN0N_/CK (DFFR_X1)
     2    2.73    0.01    0.09    0.27 v issued_q[31]$_DFFE_PN0N_/Q (DFFR_X1)
...
                                         clknet_3_4__leaf_clk (net)
                  0.03    0.00    0.14 ^ clkbuf_leaf_82_clk/A (CLKBUF_X3)
     7    8.82    0.01    0.04    0.18 ^ clkbuf_leaf_82_clk/Z (CLKBUF_X3)
                                         clknet_leaf_82_clk (net)
                  0.01    0.00    0.18 ^ issued_q[31]$_DFFE_PN0N_/CK (DFFR_X1)
                          0.00    0.18   clock reconvergence pessimism
                          0.00    0.19   library hold time
                                  0.19   data required time
-----------------------------------------------------------------------------
                                  0.19   data required time
                                 -0.27   data arrival time
-----------------------------------------------------------------------------
                                  0.09   slack (MET)



```

### Path 8

- source: `/orfs/flow/reports/nangate45/attention_shared_sram_read_group_adapter_w256_s2/base/4_cts_final.rpt`
- stage: `cts`
- startpoint: `rst_n (input port clocked by clk)`
- endpoint: `fold_q[8]$_DFFE_PN0P_ (removal check against rising-edge clock clk)`
- path_group: `asynchronous`
- path_type: `min`
- slack: `1.6400`
- data_arrival_time: `2.0700`
- data_required_time: `0.4300`

```text
Startpoint: rst_n (input port clocked by clk)
Endpoint: fold_q[8]$_DFFE_PN0P_ (removal check against rising-edge clock clk)
Path Group: asynchronous
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (propagated)
                          2.00    2.00 ^ input external delay
     1    4.28    0.00    0.00    2.00 ^ rst_n (in)
                                         rst_n (net)
                  0.00    0.00    2.00 ^ input6/A (CLKBUF_X3)
    11   44.29    0.03    0.05    2.05 ^ input6/Z (CLKBUF_X3)
                                         net5 (net)
                  0.04    0.02    2.07 ^ fold_q[8]$_DFFE_PN0P_/RN (DFFR_X1)
                                  2.07   data arrival time

                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   23.92    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.00    0.00    0.00 ^ clkbuf_0_clk/A (CLKBUF_X3)
     8   61.48    0.05    0.07    0.08 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.05    0.00    0.08 ^ clkbuf_3_7__f_clk/A (CLKBUF_X3)
     9   39.63    0.03    0.07    0.15 ^ clkbuf_3_7__f_clk/Z (CLKBUF_X3)
                                         clknet_3_7__leaf_clk (net)
                  0.03    0.00    0.15 ^ clkbuf_leaf_42_clk/A (CLKBUF_X3)
     7   10.60    0.01    0.05    0.20 ^ clkbuf_leaf_42_clk/Z (CLKBUF_X3)
                                         clknet_leaf_42_clk (net)
                  0.01    0.00    0.20 ^ fold_q[8]$_DFFE_PN0P_/CK (DFFR_X1)
                          0.00    0.20   clock reconvergence pessimism
                          0.23    0.43   library removal time
                                  0.43   data required time
-----------------------------------------------------------------------------
                                  0.43   data required time
                                 -2.07   data arrival time
-----------------------------------------------------------------------------
                                  1.64   slack (MET)
```
