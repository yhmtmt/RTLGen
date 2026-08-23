# OpenROAD Timing Debug Summary

- design_dir: `runs/designs/npu_blocks/attention_shared_sram_read_group_adapter_w256_s1`
- metrics_path: `runs/designs/npu_blocks/attention_shared_sram_read_group_adapter_w256_s1/metrics.csv`
- rows_considered: 4

## Metrics Rows

| param_hash | tag | status | critical_path_ns | density | result_path |
| --- | --- | --- | ---: | ---: | --- |
| 07ed8cb5 | attention_shared_sram_read_group_adapter_ppa_v1_07ed8cb5 | ok | 0.6452 | 0.5 | `/orfs/flow/reports/nangate45/attention_shared_sram_read_group_adapter_w256_s1/base/6_finish.rpt` |
| 77ace606 | attention_shared_sram_read_group_adapter_ppa_v1_77ace606 | ok | 0.6765 | 0.5 | `/orfs/flow/reports/nangate45/attention_shared_sram_read_group_adapter_w256_s1/base/6_finish.rpt` |
| 8574f558 | attention_shared_sram_read_group_adapter_ppa_v1_8574f558 | ok | 0.6799 | 0.5 | `/orfs/flow/reports/nangate45/attention_shared_sram_read_group_adapter_w256_s1/base/6_finish.rpt` |
| 1fd76a90 | attention_shared_sram_read_group_adapter_ppa_v1_1fd76a90 | ok | 0.6835 | 0.5 | `/orfs/flow/reports/nangate45/attention_shared_sram_read_group_adapter_w256_s1/base/6_finish.rpt` |

## Inspected Report Files

- `/orfs/flow/reports/nangate45/attention_shared_sram_read_group_adapter_w256_s1/base/6_finish.rpt`
- `/orfs/flow/reports/nangate45/attention_shared_sram_read_group_adapter_w256_s1/base/5_global_route.rpt`
- `/orfs/flow/reports/nangate45/attention_shared_sram_read_group_adapter_w256_s1/base/5_route_drc.rpt`
- `/orfs/flow/reports/nangate45/attention_shared_sram_read_group_adapter_w256_s1/base/4_cts_final.rpt`
- `/orfs/flow/reports/nangate45/attention_shared_sram_read_group_adapter_w256_s1/base/3_resizer.rpt`
- `/orfs/flow/reports/nangate45/attention_shared_sram_read_group_adapter_w256_s1/base/3_detailed_place.rpt`
- `/orfs/flow/reports/nangate45/attention_shared_sram_read_group_adapter_w256_s1/base/3_global_place.rpt`
- `/orfs/flow/reports/nangate45/attention_shared_sram_read_group_adapter_w256_s1/base/2_floorplan_final.rpt`
- `/orfs/flow/reports/nangate45/attention_shared_sram_read_group_adapter_w256_s1/base/drt_antennas.log`
- `/orfs/flow/reports/nangate45/attention_shared_sram_read_group_adapter_w256_s1/base/grt_antennas.log`
- `/orfs/flow/reports/nangate45/attention_shared_sram_read_group_adapter_w256_s1/base/metadata-generate.log`

## Preferred Final-Stage Timing Paths

- raw_path_block_count: 208
- unique_path_block_count: 33
- preferred_stage: `finish`

### Path 1

- source: `/orfs/flow/reports/nangate45/attention_shared_sram_read_group_adapter_w256_s1/base/6_finish.rpt`
- stage: `finish`
- startpoint: `issued_q[30]$_DFFE_PN0N_`
- endpoint: `issued_q[30]$_DFFE_PN0N_`
- path_group: `clk`
- path_type: `min`
- slack: `0.0900`
- data_arrival_time: `0.2600`
- data_required_time: `0.1700`

```text
Startpoint: issued_q[30]$_DFFE_PN0N_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: issued_q[30]$_DFFE_PN0N_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   14.55    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.00    0.00    0.00 ^ clkbuf_0_clk/A (CLKBUF_X3)
     8   43.83    0.03    0.06    0.06 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.03    0.00    0.06 ^ clkbuf_3_6_0_clk/A (CLKBUF_X3)
     9   29.48    0.02    0.06    0.12 ^ clkbuf_3_6_0_clk/Z (CLKBUF_X3)
                                         clknet_3_6_0_clk (net)
                  0.02    0.00    0.13 ^ clkbuf_leaf_70_clk/A (CLKBUF_X3)
     7    8.90    0.01    0.04    0.17 ^ clkbuf_leaf_70_clk/Z (CLKBUF_X3)
                                         clknet_leaf_70_clk (net)
                  0.01    0.00    0.17 ^ issued_q[30]$_DFFE_PN0N_/CK (DFFR_X1)
     2    2.94    0.01    0.09    0.26 v issued_q[30]$_DFFE_PN0N_/Q (DFFR_X1)
...
                                         clknet_3_6_0_clk (net)
                  0.02    0.00    0.13 ^ clkbuf_leaf_70_clk/A (CLKBUF_X3)
     7    8.90    0.01    0.04    0.17 ^ clkbuf_leaf_70_clk/Z (CLKBUF_X3)
                                         clknet_leaf_70_clk (net)
                  0.01    0.00    0.17 ^ issued_q[30]$_DFFE_PN0N_/CK (DFFR_X1)
                          0.00    0.17   clock reconvergence pessimism
                          0.00    0.17   library hold time
                                  0.17   data required time
-----------------------------------------------------------------------------
                                  0.17   data required time
                                 -0.26   data arrival time
-----------------------------------------------------------------------------
                                  0.09   slack (MET)



```

### Path 2

- source: `/orfs/flow/reports/nangate45/attention_shared_sram_read_group_adapter_w256_s1/base/6_finish.rpt`
- stage: `finish`
- startpoint: `rst_n (input port clocked by clk)`
- endpoint: `adapter.macro_read_count[27]$_DFFE_PN0P_`
- path_group: `asynchronous`
- path_type: `min`
- slack: `1.6600`
- data_arrival_time: `2.0800`
- data_required_time: `0.4300`

```text
Startpoint: rst_n (input port clocked by clk)
Endpoint: adapter.macro_read_count[27]$_DFFE_PN0P_
          (removal check against rising-edge clock clk)
Path Group: asynchronous
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (propagated)
                          2.00    2.00 ^ input external delay
     1    4.65    0.00    0.00    2.00 ^ rst_n (in)
                                         rst_n (net)
                  0.00    0.00    2.00 ^ input6/A (CLKBUF_X3)
    29   81.13    0.06    0.08    2.08 ^ input6/Z (CLKBUF_X3)
                                         net5 (net)
                  0.06    0.00    2.08 ^ adapter.macro_read_count[27]$_DFFE_PN0P_/RN (DFFR_X1)
                                  2.08   data arrival time

                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   14.55    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.00    0.00    0.00 ^ clkbuf_0_clk/A (CLKBUF_X3)
     8   43.83    0.03    0.06    0.06 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.03    0.00    0.06 ^ clkbuf_3_3_0_clk/A (CLKBUF_X3)
    13   31.23    0.03    0.06    0.13 ^ clkbuf_3_3_0_clk/Z (CLKBUF_X3)
                                         clknet_3_3_0_clk (net)
                  0.03    0.00    0.13 ^ clkbuf_leaf_34_clk/A (CLKBUF_X3)
     7    9.92    0.01    0.04    0.17 ^ clkbuf_leaf_34_clk/Z (CLKBUF_X3)
                                         clknet_leaf_34_clk (net)
                  0.01    0.00    0.17 ^ adapter.macro_read_count[27]$_DFFE_PN0P_/CK (DFFR_X1)
                          0.00    0.17   clock reconvergence pessimism
                          0.26    0.43   library removal time
                                  0.43   data required time
-----------------------------------------------------------------------------
                                  0.43   data required time
                                 -2.08   data arrival time
-----------------------------------------------------------------------------
                                  1.66   slack (MET)
```

### Path 3

- source: `/orfs/flow/reports/nangate45/attention_shared_sram_read_group_adapter_w256_s1/base/6_finish.rpt`
- stage: `finish`
- startpoint: `adapter.beat_request_count[19]$_DFFE_PN0N_`
- endpoint: `access_reduction_proven (output port clocked by clk)`
- path_group: `clk`
- path_type: `max`
- slack: `7.3200`
- data_arrival_time: `0.6800`
- data_required_time: `8.0000`

```text
Startpoint: adapter.beat_request_count[19]$_DFFE_PN0N_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: access_reduction_proven (output port clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   14.55    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.00    0.00    0.00 ^ clkbuf_0_clk/A (CLKBUF_X3)
     8   43.83    0.03    0.06    0.06 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.03    0.00    0.06 ^ clkbuf_3_3_0_clk/A (CLKBUF_X3)
    13   31.23    0.03    0.06    0.13 ^ clkbuf_3_3_0_clk/Z (CLKBUF_X3)
                                         clknet_3_3_0_clk (net)
                  0.03    0.00    0.13 ^ clkbuf_leaf_29_clk/A (CLKBUF_X3)
     7   10.58    0.01    0.04    0.17 ^ clkbuf_leaf_29_clk/Z (CLKBUF_X3)
                                         clknet_leaf_29_clk (net)
                  0.01    0.00    0.17 ^ adapter.beat_request_count[19]$_DFFE_PN0N_/CK (DFFR_X1)
     4   17.21    0.04    0.14    0.31 ^ adapter.beat_request_count[19]$_DFFE_PN0N_/Q (DFFR_X1)
                                         net50 (net)
...
                  0.01    0.00    0.68 ^ access_reduction_proven (out)
                                  0.68   data arrival time

                         10.00   10.00   clock clk (rise edge)
                          0.00   10.00   clock network delay (propagated)
                          0.00   10.00   clock reconvergence pessimism
                         -2.00    8.00   output external delay
                                  8.00   data required time
-----------------------------------------------------------------------------
                                  8.00   data required time
                                 -0.68   data arrival time
-----------------------------------------------------------------------------
                                  7.32   slack (MET)



```

### Path 4

- source: `/orfs/flow/reports/nangate45/attention_shared_sram_read_group_adapter_w256_s1/base/6_finish.rpt`
- stage: `finish`
- startpoint: `rst_n (input port clocked by clk)`
- endpoint: `seed_q[16]$_DFFE_PN0P_ (recovery check against rising-edge clock clk)`
- path_group: `asynchronous`
- path_type: `max`
- slack: `7.6200`
- data_arrival_time: `2.5900`
- data_required_time: `10.2100`

```text
Startpoint: rst_n (input port clocked by clk)
Endpoint: seed_q[16]$_DFFE_PN0P_ (recovery check against rising-edge clock clk)
Path Group: asynchronous
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (propagated)
                          2.00    2.00 ^ input external delay
     1    4.65    0.00    0.00    2.00 ^ rst_n (in)
                                         rst_n (net)
                  0.00    0.00    2.00 ^ input6/A (CLKBUF_X3)
    29   81.13    0.06    0.08    2.08 ^ input6/Z (CLKBUF_X3)
                                         net5 (net)
                  0.06    0.00    2.09 ^ place256/A (BUF_X2)
    27   57.84    0.07    0.09    2.18 ^ place256/Z (BUF_X2)
                                         net255 (net)
                  0.07    0.00    2.18 ^ place257/A (BUF_X2)
    24   52.14    0.06    0.09    2.27 ^ place257/Z (BUF_X2)
                                         net256 (net)
                  0.06    0.01    2.28 ^ place258/A (BUF_X2)
    19   49.73    0.06    0.08    2.36 ^ place258/Z (BUF_X2)
                                         net257 (net)
...
                                         clknet_0_clk (net)
                  0.03    0.00   10.06 ^ clkbuf_3_5_0_clk/A (CLKBUF_X3)
    11   25.22    0.02    0.06   10.12 ^ clkbuf_3_5_0_clk/Z (CLKBUF_X3)
                                         clknet_3_5_0_clk (net)
                  0.02    0.00   10.12 ^ clkbuf_leaf_49_clk/A (CLKBUF_X3)
     7    9.28    0.01    0.04   10.16 ^ clkbuf_leaf_49_clk/Z (CLKBUF_X3)
                                         clknet_leaf_49_clk (net)
                  0.01    0.00   10.16 ^ seed_q[16]$_DFFE_PN0P_/CK (DFFR_X1)
                          0.00   10.16   clock reconvergence pessimism
                          0.05   10.21   library recovery time
                                 10.21   data required time
-----------------------------------------------------------------------------
                                 10.21   data required time
                                 -2.59   data arrival time
-----------------------------------------------------------------------------
                                  7.62   slack (MET)
```

### Path 5

- source: `/orfs/flow/reports/nangate45/attention_shared_sram_read_group_adapter_w256_s1/base/6_finish.rpt`
- stage: `finish`
- startpoint: `adapter.slot_base_addr[0][8]$_DFFE_PN0P_`
- endpoint: `adapter.slot_state[0][0]$_DFF_PN0_`
- path_group: `clk`
- path_type: `max`
- slack: `9.1900`
- data_arrival_time: `0.9400`
- data_required_time: `10.1300`

```text
Startpoint: adapter.slot_base_addr[0][8]$_DFFE_PN0P_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: adapter.slot_state[0][0]$_DFF_PN0_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

  Delay    Time   Description
---------------------------------------------------------
   0.00    0.00   clock clk (rise edge)
   0.00    0.00   clock source latency
   0.00    0.00 ^ clk (in)
   0.06    0.06 ^ clkbuf_0_clk/Z (CLKBUF_X3)
   0.06    0.12 ^ clkbuf_3_4_0_clk/Z (CLKBUF_X3)
   0.04    0.17 ^ clkbuf_leaf_57_clk/Z (CLKBUF_X3)
   0.00    0.17 ^ adapter.slot_base_addr[0][8]$_DFFE_PN0P_/CK (DFFR_X1)
   0.13    0.30 ^ adapter.slot_base_addr[0][8]$_DFFE_PN0P_/Q (DFFR_X1)
   0.06    0.36 ^ _4377_/CO (HA_X1)
   0.03    0.38 v _2701_/ZN (NAND2_X1)
   0.13    0.51 v _2710_/ZN (OR4_X2)
   0.05    0.56 v _2883_/ZN (XNOR2_X1)
   0.04    0.60 ^ _2884_/ZN (XNOR2_X1)
   0.03    0.63 v _2888_/ZN (OAI221_X1)
   0.13    0.76 v _2889_/ZN (OR4_X1)
...
   0.00   10.00 ^ clk (in)
   0.06   10.06 ^ clkbuf_0_clk/Z (CLKBUF_X3)
   0.06   10.12 ^ clkbuf_3_6_0_clk/Z (CLKBUF_X3)
   0.04   10.17 ^ clkbuf_leaf_69_clk/Z (CLKBUF_X3)
   0.00   10.17 ^ adapter.slot_state[0][0]$_DFF_PN0_/CK (DFFR_X1)
   0.00   10.17   clock reconvergence pessimism
  -0.04   10.13   library setup time
          10.13   data required time
---------------------------------------------------------
          10.13   data required time
          -0.94   data arrival time
---------------------------------------------------------
           9.19   slack (MET)



```


## Worst Timing Paths Across All Stages

### Path 1

- source: `/orfs/flow/reports/nangate45/attention_shared_sram_read_group_adapter_w256_s1/base/3_detailed_place.rpt`
- stage: `detailed_place`
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
     2    2.85    0.01    0.09    0.09 v issued_q[31]$_DFFE_PN0N_/Q (DFFR_X1)
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

### Path 2

- source: `/orfs/flow/reports/nangate45/attention_shared_sram_read_group_adapter_w256_s1/base/3_global_place.rpt`
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
     2    2.86    0.01    0.09    0.09 v issued_q[30]$_DFFE_PN0N_/Q (DFFR_X1)
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

- source: `/orfs/flow/reports/nangate45/attention_shared_sram_read_group_adapter_w256_s1/base/3_resizer.rpt`
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
     2    2.86    0.01    0.09    0.09 v issued_q[30]$_DFFE_PN0N_/Q (DFFR_X1)
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

- source: `/orfs/flow/reports/nangate45/attention_shared_sram_read_group_adapter_w256_s1/base/2_floorplan_final.rpt`
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
                                         _0006_ (net)
                  0.02    0.00    0.07 ^ _2569_/B2 (AOI21_X1)
     1    1.05    0.01    0.02    0.09 v _2569_/ZN (AOI21_X1)
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

- source: `/orfs/flow/reports/nangate45/attention_shared_sram_read_group_adapter_w256_s1/base/4_cts_final.rpt`
- stage: `cts`
- startpoint: `issued_q[30]$_DFFE_PN0N_`
- endpoint: `issued_q[30]$_DFFE_PN0N_`
- path_group: `clk`
- path_type: `min`
- slack: `0.0900`
- data_arrival_time: `0.2700`
- data_required_time: `0.1900`

```text
Startpoint: issued_q[30]$_DFFE_PN0N_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: issued_q[30]$_DFFE_PN0N_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   23.20    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.00    0.00    0.00 ^ clkbuf_0_clk/A (CLKBUF_X3)
     8   53.29    0.04    0.07    0.07 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.04    0.00    0.07 ^ clkbuf_3_6_0_clk/A (CLKBUF_X3)
     9   33.04    0.03    0.07    0.14 ^ clkbuf_3_6_0_clk/Z (CLKBUF_X3)
                                         clknet_3_6_0_clk (net)
                  0.03    0.00    0.14 ^ clkbuf_leaf_70_clk/A (CLKBUF_X3)
     7    9.12    0.01    0.04    0.18 ^ clkbuf_leaf_70_clk/Z (CLKBUF_X3)
                                         clknet_leaf_70_clk (net)
                  0.01    0.00    0.18 ^ issued_q[30]$_DFFE_PN0N_/CK (DFFR_X1)
     2    2.86    0.01    0.09    0.27 v issued_q[30]$_DFFE_PN0N_/Q (DFFR_X1)
...
                                         clknet_3_6_0_clk (net)
                  0.03    0.00    0.14 ^ clkbuf_leaf_70_clk/A (CLKBUF_X3)
     7    9.12    0.01    0.04    0.18 ^ clkbuf_leaf_70_clk/Z (CLKBUF_X3)
                                         clknet_leaf_70_clk (net)
                  0.01    0.00    0.18 ^ issued_q[30]$_DFFE_PN0N_/CK (DFFR_X1)
                          0.00    0.18   clock reconvergence pessimism
                          0.00    0.19   library hold time
                                  0.19   data required time
-----------------------------------------------------------------------------
                                  0.19   data required time
                                 -0.27   data arrival time
-----------------------------------------------------------------------------
                                  0.09   slack (MET)



```

### Path 6

- source: `/orfs/flow/reports/nangate45/attention_shared_sram_read_group_adapter_w256_s1/base/5_global_route.rpt`
- stage: `route`
- startpoint: `issued_q[30]$_DFFE_PN0N_`
- endpoint: `issued_q[30]$_DFFE_PN0N_`
- path_group: `clk`
- path_type: `min`
- slack: `0.0900`
- data_arrival_time: `0.2700`
- data_required_time: `0.1900`

```text
Startpoint: issued_q[30]$_DFFE_PN0N_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: issued_q[30]$_DFFE_PN0N_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   22.13    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.00    0.00    0.00 ^ clkbuf_0_clk/A (CLKBUF_X3)
     8   54.41    0.04    0.07    0.07 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.04    0.00    0.07 ^ clkbuf_3_6_0_clk/A (CLKBUF_X3)
     9   33.16    0.03    0.07    0.14 ^ clkbuf_3_6_0_clk/Z (CLKBUF_X3)
                                         clknet_3_6_0_clk (net)
                  0.03    0.00    0.14 ^ clkbuf_leaf_70_clk/A (CLKBUF_X3)
     7    9.29    0.01    0.04    0.18 ^ clkbuf_leaf_70_clk/Z (CLKBUF_X3)
                                         clknet_leaf_70_clk (net)
                  0.01    0.00    0.18 ^ issued_q[30]$_DFFE_PN0N_/CK (DFFR_X1)
     2    3.08    0.01    0.09    0.27 v issued_q[30]$_DFFE_PN0N_/Q (DFFR_X1)
...
                                         clknet_3_6_0_clk (net)
                  0.03    0.00    0.14 ^ clkbuf_leaf_70_clk/A (CLKBUF_X3)
     7    9.29    0.01    0.04    0.18 ^ clkbuf_leaf_70_clk/Z (CLKBUF_X3)
                                         clknet_leaf_70_clk (net)
                  0.01    0.00    0.18 ^ issued_q[30]$_DFFE_PN0N_/CK (DFFR_X1)
                          0.00    0.18   clock reconvergence pessimism
                          0.00    0.19   library hold time
                                  0.19   data required time
-----------------------------------------------------------------------------
                                  0.19   data required time
                                 -0.27   data arrival time
-----------------------------------------------------------------------------
                                  0.09   slack (MET)



```

### Path 7

- source: `/orfs/flow/reports/nangate45/attention_shared_sram_read_group_adapter_w256_s1/base/6_finish.rpt`
- stage: `finish`
- startpoint: `issued_q[30]$_DFFE_PN0N_`
- endpoint: `issued_q[30]$_DFFE_PN0N_`
- path_group: `clk`
- path_type: `min`
- slack: `0.0900`
- data_arrival_time: `0.2600`
- data_required_time: `0.1700`

```text
Startpoint: issued_q[30]$_DFFE_PN0N_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: issued_q[30]$_DFFE_PN0N_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   14.55    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.00    0.00    0.00 ^ clkbuf_0_clk/A (CLKBUF_X3)
     8   43.83    0.03    0.06    0.06 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.03    0.00    0.06 ^ clkbuf_3_6_0_clk/A (CLKBUF_X3)
     9   29.48    0.02    0.06    0.12 ^ clkbuf_3_6_0_clk/Z (CLKBUF_X3)
                                         clknet_3_6_0_clk (net)
                  0.02    0.00    0.13 ^ clkbuf_leaf_70_clk/A (CLKBUF_X3)
     7    8.90    0.01    0.04    0.17 ^ clkbuf_leaf_70_clk/Z (CLKBUF_X3)
                                         clknet_leaf_70_clk (net)
                  0.01    0.00    0.17 ^ issued_q[30]$_DFFE_PN0N_/CK (DFFR_X1)
     2    2.94    0.01    0.09    0.26 v issued_q[30]$_DFFE_PN0N_/Q (DFFR_X1)
...
                                         clknet_3_6_0_clk (net)
                  0.02    0.00    0.13 ^ clkbuf_leaf_70_clk/A (CLKBUF_X3)
     7    8.90    0.01    0.04    0.17 ^ clkbuf_leaf_70_clk/Z (CLKBUF_X3)
                                         clknet_leaf_70_clk (net)
                  0.01    0.00    0.17 ^ issued_q[30]$_DFFE_PN0N_/CK (DFFR_X1)
                          0.00    0.17   clock reconvergence pessimism
                          0.00    0.17   library hold time
                                  0.17   data required time
-----------------------------------------------------------------------------
                                  0.17   data required time
                                 -0.26   data arrival time
-----------------------------------------------------------------------------
                                  0.09   slack (MET)



```

### Path 8

- source: `/orfs/flow/reports/nangate45/attention_shared_sram_read_group_adapter_w256_s1/base/4_cts_final.rpt`
- stage: `cts`
- startpoint: `rst_n (input port clocked by clk)`
- endpoint: `adapter.macro_read_count[27]$_DFFE_PN0P_`
- path_group: `asynchronous`
- path_type: `min`
- slack: `1.6400`
- data_arrival_time: `2.0900`
- data_required_time: `0.4400`

```text
Startpoint: rst_n (input port clocked by clk)
Endpoint: adapter.macro_read_count[27]$_DFFE_PN0P_
          (removal check against rising-edge clock clk)
Path Group: asynchronous
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (propagated)
                          2.00    2.00 ^ input external delay
     1    5.03    0.00    0.00    2.00 ^ rst_n (in)
                                         rst_n (net)
                  0.00    0.00    2.00 ^ input6/A (CLKBUF_X3)
    29   80.48    0.06    0.08    2.08 ^ input6/Z (CLKBUF_X3)
                                         net5 (net)
                  0.06    0.00    2.09 ^ adapter.macro_read_count[27]$_DFFE_PN0P_/RN (DFFR_X1)
                                  2.09   data arrival time

                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   23.20    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.00    0.00    0.00 ^ clkbuf_0_clk/A (CLKBUF_X3)
     8   53.29    0.04    0.07    0.07 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.04    0.00    0.07 ^ clkbuf_3_3_0_clk/A (CLKBUF_X3)
    13   33.55    0.03    0.07    0.14 ^ clkbuf_3_3_0_clk/Z (CLKBUF_X3)
                                         clknet_3_3_0_clk (net)
                  0.03    0.00    0.14 ^ clkbuf_leaf_34_clk/A (CLKBUF_X3)
     7    9.76    0.01    0.04    0.18 ^ clkbuf_leaf_34_clk/Z (CLKBUF_X3)
                                         clknet_leaf_34_clk (net)
                  0.01    0.00    0.18 ^ adapter.macro_read_count[27]$_DFFE_PN0P_/CK (DFFR_X1)
                          0.00    0.18   clock reconvergence pessimism
                          0.26    0.44   library removal time
                                  0.44   data required time
-----------------------------------------------------------------------------
                                  0.44   data required time
                                 -2.09   data arrival time
-----------------------------------------------------------------------------
                                  1.64   slack (MET)
```
