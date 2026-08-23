# OpenROAD Timing Debug Summary

- design_dir: `runs/designs/npu_blocks/attention_shared_sram_read_group_adapter_w512_s2`
- metrics_path: `runs/designs/npu_blocks/attention_shared_sram_read_group_adapter_w512_s2/metrics.csv`
- rows_considered: 4

## Metrics Rows

| param_hash | tag | status | critical_path_ns | density | result_path |
| --- | --- | --- | ---: | ---: | --- |
| 07ed8cb5 | attention_shared_sram_read_group_adapter_ppa_v1_07ed8cb5 | ok | 0.6542 | 0.5 | `/orfs/flow/reports/nangate45/attention_shared_sram_read_group_adapter_w512_s2/base/6_finish.rpt` |
| 3b1fff1f | attention_shared_sram_read_group_adapter_ppa_v1_3b1fff1f | ok | 0.7762 | 0.5 | `/orfs/flow/reports/nangate45/attention_shared_sram_read_group_adapter_w512_s2/base/6_finish.rpt` |
| 77ace606 | attention_shared_sram_read_group_adapter_ppa_v1_77ace606 | ok | 0.8057 | 0.5 | `/orfs/flow/reports/nangate45/attention_shared_sram_read_group_adapter_w512_s2/base/6_finish.rpt` |
| ea04ba90 | attention_shared_sram_read_group_adapter_ppa_v1_ea04ba90 | ok | 0.8068 | 0.5 | `/orfs/flow/reports/nangate45/attention_shared_sram_read_group_adapter_w512_s2/base/6_finish.rpt` |

## Inspected Report Files

- `/orfs/flow/reports/nangate45/attention_shared_sram_read_group_adapter_w512_s2/base/6_finish.rpt`
- `/orfs/flow/reports/nangate45/attention_shared_sram_read_group_adapter_w512_s2/base/5_global_route.rpt`
- `/orfs/flow/reports/nangate45/attention_shared_sram_read_group_adapter_w512_s2/base/5_route_drc.rpt`
- `/orfs/flow/reports/nangate45/attention_shared_sram_read_group_adapter_w512_s2/base/4_cts_final.rpt`
- `/orfs/flow/reports/nangate45/attention_shared_sram_read_group_adapter_w512_s2/base/3_resizer.rpt`
- `/orfs/flow/reports/nangate45/attention_shared_sram_read_group_adapter_w512_s2/base/3_detailed_place.rpt`
- `/orfs/flow/reports/nangate45/attention_shared_sram_read_group_adapter_w512_s2/base/3_global_place.rpt`
- `/orfs/flow/reports/nangate45/attention_shared_sram_read_group_adapter_w512_s2/base/2_floorplan_final.rpt`
- `/orfs/flow/reports/nangate45/attention_shared_sram_read_group_adapter_w512_s2/base/drt_antennas.log`
- `/orfs/flow/reports/nangate45/attention_shared_sram_read_group_adapter_w512_s2/base/grt_antennas.log`
- `/orfs/flow/reports/nangate45/attention_shared_sram_read_group_adapter_w512_s2/base/metadata-generate.log`

## Preferred Final-Stage Timing Paths

- raw_path_block_count: 208
- unique_path_block_count: 33
- preferred_stage: `finish`

### Path 1

- source: `/orfs/flow/reports/nangate45/attention_shared_sram_read_group_adapter_w512_s2/base/6_finish.rpt`
- stage: `finish`
- startpoint: `issued_q[27]$_DFFE_PN0N_`
- endpoint: `issued_q[27]$_DFFE_PN0N_`
- path_group: `clk`
- path_type: `min`
- slack: `0.0900`
- data_arrival_time: `0.2500`
- data_required_time: `0.1700`

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
     1   12.81    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.00    0.00    0.00 ^ clkbuf_0_clk/A (CLKBUF_X3)
     8   39.25    0.03    0.05    0.06 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.03    0.00    0.06 ^ clkbuf_3_4__f_clk/A (CLKBUF_X3)
    12   31.66    0.03    0.06    0.12 ^ clkbuf_3_4__f_clk/Z (CLKBUF_X3)
                                         clknet_3_4__leaf_clk (net)
                  0.03    0.00    0.12 ^ clkbuf_leaf_74_clk/A (CLKBUF_X3)
     8    9.41    0.01    0.04    0.16 ^ clkbuf_leaf_74_clk/Z (CLKBUF_X3)
                                         clknet_leaf_74_clk (net)
                  0.01    0.00    0.16 ^ issued_q[27]$_DFFE_PN0N_/CK (DFFR_X1)
     2    2.75    0.01    0.09    0.25 v issued_q[27]$_DFFE_PN0N_/Q (DFFR_X1)
...
                                         clknet_3_4__leaf_clk (net)
                  0.03    0.00    0.12 ^ clkbuf_leaf_74_clk/A (CLKBUF_X3)
     8    9.41    0.01    0.04    0.16 ^ clkbuf_leaf_74_clk/Z (CLKBUF_X3)
                                         clknet_leaf_74_clk (net)
                  0.01    0.00    0.16 ^ issued_q[27]$_DFFE_PN0N_/CK (DFFR_X1)
                          0.00    0.16   clock reconvergence pessimism
                          0.01    0.17   library hold time
                                  0.17   data required time
-----------------------------------------------------------------------------
                                  0.17   data required time
                                 -0.25   data arrival time
-----------------------------------------------------------------------------
                                  0.09   slack (MET)



```

### Path 2

- source: `/orfs/flow/reports/nangate45/attention_shared_sram_read_group_adapter_w512_s2/base/6_finish.rpt`
- stage: `finish`
- startpoint: `rst_n (input port clocked by clk)`
- endpoint: `cycle_q[24]$_DFFE_PN0P_ (removal check against rising-edge clock clk)`
- path_group: `asynchronous`
- path_type: `min`
- slack: `1.6600`
- data_arrival_time: `2.0500`
- data_required_time: `0.3900`

```text
Startpoint: rst_n (input port clocked by clk)
Endpoint: cycle_q[24]$_DFFE_PN0P_ (removal check against rising-edge clock clk)
Path Group: asynchronous
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (propagated)
                          2.00    2.00 ^ input external delay
     1    3.30    0.00    0.00    2.00 ^ rst_n (in)
                                         rst_n (net)
                  0.00    0.00    2.00 ^ input7/A (CLKBUF_X3)
    11   34.17    0.03    0.05    2.05 ^ input7/Z (CLKBUF_X3)
                                         net6 (net)
                  0.03    0.00    2.05 ^ cycle_q[24]$_DFFE_PN0P_/RN (DFFR_X1)
                                  2.05   data arrival time

                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   12.81    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.00    0.00    0.00 ^ clkbuf_0_clk/A (CLKBUF_X3)
     8   39.25    0.03    0.05    0.06 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.03    0.00    0.06 ^ clkbuf_3_3__f_clk/A (CLKBUF_X3)
    10   37.56    0.03    0.07    0.12 ^ clkbuf_3_3__f_clk/Z (CLKBUF_X3)
                                         clknet_3_3__leaf_clk (net)
                  0.03    0.00    0.13 ^ clkbuf_leaf_26_clk/A (CLKBUF_X3)
     7    9.34    0.01    0.04    0.17 ^ clkbuf_leaf_26_clk/Z (CLKBUF_X3)
                                         clknet_leaf_26_clk (net)
                  0.01    0.00    0.17 ^ cycle_q[24]$_DFFE_PN0P_/CK (DFFR_X1)
                          0.00    0.17   clock reconvergence pessimism
                          0.22    0.39   library removal time
                                  0.39   data required time
-----------------------------------------------------------------------------
                                  0.39   data required time
                                 -2.05   data arrival time
-----------------------------------------------------------------------------
                                  1.66   slack (MET)
```

### Path 3

- source: `/orfs/flow/reports/nangate45/attention_shared_sram_read_group_adapter_w512_s2/base/6_finish.rpt`
- stage: `finish`
- startpoint: `adapter.beat_request_count[45]$_DFFE_PN0N_`
- endpoint: `access_reduction_proven (output port clocked by clk)`
- path_group: `clk`
- path_type: `max`
- slack: `7.1900`
- data_arrival_time: `0.8100`
- data_required_time: `8.0000`

```text
Startpoint: adapter.beat_request_count[45]$_DFFE_PN0N_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: access_reduction_proven (output port clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   12.81    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.00    0.00    0.00 ^ clkbuf_0_clk/A (CLKBUF_X3)
     8   39.25    0.03    0.05    0.06 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.03    0.00    0.06 ^ clkbuf_3_2__f_clk/A (CLKBUF_X3)
    15   39.17    0.03    0.07    0.13 ^ clkbuf_3_2__f_clk/Z (CLKBUF_X3)
                                         clknet_3_2__leaf_clk (net)
                  0.03    0.00    0.13 ^ clkbuf_leaf_12_clk/A (CLKBUF_X3)
     8    9.82    0.01    0.04    0.17 ^ clkbuf_leaf_12_clk/Z (CLKBUF_X3)
                                         clknet_leaf_12_clk (net)
                  0.01    0.00    0.17 ^ adapter.beat_request_count[45]$_DFFE_PN0N_/CK (DFFR_X1)
     6   13.39    0.03    0.13    0.30 ^ adapter.beat_request_count[45]$_DFFE_PN0N_/Q (DFFR_X1)
                                         adapter.beat_request_count[45] (net)
...
                  0.01    0.00    0.81 ^ access_reduction_proven (out)
                                  0.81   data arrival time

                         10.00   10.00   clock clk (rise edge)
                          0.00   10.00   clock network delay (propagated)
                          0.00   10.00   clock reconvergence pessimism
                         -2.00    8.00   output external delay
                                  8.00   data required time
-----------------------------------------------------------------------------
                                  8.00   data required time
                                 -0.81   data arrival time
-----------------------------------------------------------------------------
                                  7.19   slack (MET)



```

### Path 4

- source: `/orfs/flow/reports/nangate45/attention_shared_sram_read_group_adapter_w512_s2/base/6_finish.rpt`
- stage: `finish`
- startpoint: `rst_n (input port clocked by clk)`
- endpoint: `adapter.slot_base_addr[1][18]$_DFFE_PN0P_`
- path_group: `asynchronous`
- path_type: `max`
- slack: `7.5900`
- data_arrival_time: `2.6200`
- data_required_time: `10.2100`

```text
Startpoint: rst_n (input port clocked by clk)
Endpoint: adapter.slot_base_addr[1][18]$_DFFE_PN0P_
          (recovery check against rising-edge clock clk)
Path Group: asynchronous
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (propagated)
                          2.00    2.00 ^ input external delay
     1    3.30    0.00    0.00    2.00 ^ rst_n (in)
                                         rst_n (net)
                  0.00    0.00    2.00 ^ input7/A (CLKBUF_X3)
    11   34.17    0.03    0.05    2.05 ^ input7/Z (CLKBUF_X3)
                                         net6 (net)
                  0.03    0.01    2.06 ^ place291/A (BUF_X2)
    34   71.90    0.08    0.10    2.16 ^ place291/Z (BUF_X2)
                                         net290 (net)
                  0.08    0.01    2.17 ^ place292/A (BUF_X2)
    30   65.06    0.07    0.10    2.27 ^ place292/Z (BUF_X2)
                                         net291 (net)
                  0.07    0.01    2.28 ^ place293/A (BUF_X2)
    33   74.05    0.08    0.11    2.39 ^ place293/Z (BUF_X2)
...
                                         clknet_0_clk (net)
                  0.03    0.00   10.06 ^ clkbuf_3_5__f_clk/A (CLKBUF_X3)
     9   32.89    0.03    0.06   10.12 ^ clkbuf_3_5__f_clk/Z (CLKBUF_X3)
                                         clknet_3_5__leaf_clk (net)
                  0.03    0.00   10.12 ^ clkbuf_leaf_66_clk/A (CLKBUF_X3)
     8   10.13    0.01    0.04   10.17 ^ clkbuf_leaf_66_clk/Z (CLKBUF_X3)
                                         clknet_leaf_66_clk (net)
                  0.01    0.00   10.17 ^ adapter.slot_base_addr[1][18]$_DFFE_PN0P_/CK (DFFR_X1)
                          0.00   10.17   clock reconvergence pessimism
                          0.05   10.21   library recovery time
                                 10.21   data required time
-----------------------------------------------------------------------------
                                 10.21   data required time
                                 -2.62   data arrival time
-----------------------------------------------------------------------------
                                  7.59   slack (MET)
```

### Path 5

- source: `/orfs/flow/reports/nangate45/attention_shared_sram_read_group_adapter_w512_s2/base/6_finish.rpt`
- stage: `finish`
- startpoint: `adapter.collect_slot_q$_DFFE_PN0P_`
- endpoint: `adapter.beat_request_count[46]$_DFFE_PN0N_`
- path_group: `clk`
- path_type: `max`
- slack: `8.8500`
- data_arrival_time: `1.2800`
- data_required_time: `10.1300`

```text
Startpoint: adapter.collect_slot_q$_DFFE_PN0P_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: adapter.beat_request_count[46]$_DFFE_PN0N_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

  Delay    Time   Description
---------------------------------------------------------
   0.00    0.00   clock clk (rise edge)
   0.00    0.00   clock source latency
   0.00    0.00 ^ clk (in)
   0.06    0.06 ^ clkbuf_0_clk/Z (CLKBUF_X3)
   0.07    0.12 ^ clkbuf_3_4__f_clk/Z (CLKBUF_X3)
   0.04    0.16 ^ clkbuf_leaf_80_clk/Z (CLKBUF_X3)
   0.00    0.17 ^ adapter.collect_slot_q$_DFFE_PN0P_/CK (DFFR_X2)
   0.20    0.37 ^ adapter.collect_slot_q$_DFFE_PN0P_/Q (DFFR_X2)
   0.13    0.50 ^ place280/Z (BUF_X2)
   0.09    0.58 v _3292_/Z (MUX2_X1)
   0.12    0.70 v _3293_/ZN (OR4_X1)
   0.06    0.76 v _3296_/Z (MUX2_X1)
   0.04    0.81 ^ _3299_/ZN (OAI22_X1)
   0.05    0.86 v _3375_/ZN (NAND4_X2)
   0.12    0.98 ^ _3376_/ZN (OAI21_X4)
...
   0.00   10.00 ^ clk (in)
   0.06   10.06 ^ clkbuf_0_clk/Z (CLKBUF_X3)
   0.06   10.12 ^ clkbuf_3_0__f_clk/Z (CLKBUF_X3)
   0.04   10.16 ^ clkbuf_leaf_18_clk/Z (CLKBUF_X3)
   0.00   10.16 ^ adapter.beat_request_count[46]$_DFFE_PN0N_/CK (DFFR_X1)
   0.00   10.16   clock reconvergence pessimism
  -0.03   10.13   library setup time
          10.13   data required time
---------------------------------------------------------
          10.13   data required time
          -1.28   data arrival time
---------------------------------------------------------
           8.85   slack (MET)



```


## Worst Timing Paths Across All Stages

### Path 1

- source: `/orfs/flow/reports/nangate45/attention_shared_sram_read_group_adapter_w512_s2/base/3_detailed_place.rpt`
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
     2    2.71    0.01    0.09    0.09 v issued_q[27]$_DFFE_PN0N_/Q (DFFR_X1)
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

- source: `/orfs/flow/reports/nangate45/attention_shared_sram_read_group_adapter_w512_s2/base/3_global_place.rpt`
- stage: `global_place`
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
     2    2.83    0.01    0.09    0.09 v issued_q[27]$_DFFE_PN0N_/Q (DFFR_X1)
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

### Path 3

- source: `/orfs/flow/reports/nangate45/attention_shared_sram_read_group_adapter_w512_s2/base/3_resizer.rpt`
- stage: `resizer`
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
     2    2.83    0.01    0.09    0.09 v issued_q[27]$_DFFE_PN0N_/Q (DFFR_X1)
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

### Path 4

- source: `/orfs/flow/reports/nangate45/attention_shared_sram_read_group_adapter_w512_s2/base/2_floorplan_final.rpt`
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
                                         _0011_ (net)
                  0.02    0.00    0.07 ^ _3213_/B2 (AOI21_X1)
     1    1.05    0.01    0.02    0.09 v _3213_/ZN (AOI21_X1)
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

- source: `/orfs/flow/reports/nangate45/attention_shared_sram_read_group_adapter_w512_s2/base/4_cts_final.rpt`
- stage: `cts`
- startpoint: `issued_q[27]$_DFFE_PN0N_`
- endpoint: `issued_q[27]$_DFFE_PN0N_`
- path_group: `clk`
- path_type: `min`
- slack: `0.0900`
- data_arrival_time: `0.2700`
- data_required_time: `0.1800`

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
     1   16.99    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.00    0.00    0.00 ^ clkbuf_0_clk/A (CLKBUF_X3)
     8   48.35    0.04    0.06    0.06 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.04    0.00    0.07 ^ clkbuf_3_4__f_clk/A (CLKBUF_X3)
    12   33.99    0.03    0.07    0.13 ^ clkbuf_3_4__f_clk/Z (CLKBUF_X3)
                                         clknet_3_4__leaf_clk (net)
                  0.03    0.00    0.13 ^ clkbuf_leaf_74_clk/A (CLKBUF_X3)
     8    9.34    0.01    0.04    0.18 ^ clkbuf_leaf_74_clk/Z (CLKBUF_X3)
                                         clknet_leaf_74_clk (net)
                  0.01    0.00    0.18 ^ issued_q[27]$_DFFE_PN0N_/CK (DFFR_X1)
     2    2.78    0.01    0.09    0.27 v issued_q[27]$_DFFE_PN0N_/Q (DFFR_X1)
...
                                         clknet_3_4__leaf_clk (net)
                  0.03    0.00    0.13 ^ clkbuf_leaf_74_clk/A (CLKBUF_X3)
     8    9.34    0.01    0.04    0.18 ^ clkbuf_leaf_74_clk/Z (CLKBUF_X3)
                                         clknet_leaf_74_clk (net)
                  0.01    0.00    0.18 ^ issued_q[27]$_DFFE_PN0N_/CK (DFFR_X1)
                          0.00    0.18   clock reconvergence pessimism
                          0.01    0.18   library hold time
                                  0.18   data required time
-----------------------------------------------------------------------------
                                  0.18   data required time
                                 -0.27   data arrival time
-----------------------------------------------------------------------------
                                  0.09   slack (MET)



```

### Path 6

- source: `/orfs/flow/reports/nangate45/attention_shared_sram_read_group_adapter_w512_s2/base/5_global_route.rpt`
- stage: `route`
- startpoint: `issued_q[27]$_DFFE_PN0N_`
- endpoint: `issued_q[27]$_DFFE_PN0N_`
- path_group: `clk`
- path_type: `min`
- slack: `0.0900`
- data_arrival_time: `0.2700`
- data_required_time: `0.1800`

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
     1   16.76    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.00    0.00    0.00 ^ clkbuf_0_clk/A (CLKBUF_X3)
     8   48.62    0.04    0.06    0.06 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.04    0.00    0.07 ^ clkbuf_3_4__f_clk/A (CLKBUF_X3)
    12   34.20    0.03    0.07    0.13 ^ clkbuf_3_4__f_clk/Z (CLKBUF_X3)
                                         clknet_3_4__leaf_clk (net)
                  0.03    0.00    0.13 ^ clkbuf_leaf_74_clk/A (CLKBUF_X3)
     8    9.81    0.01    0.04    0.18 ^ clkbuf_leaf_74_clk/Z (CLKBUF_X3)
                                         clknet_leaf_74_clk (net)
                  0.01    0.00    0.18 ^ issued_q[27]$_DFFE_PN0N_/CK (DFFR_X1)
     2    2.91    0.01    0.09    0.27 v issued_q[27]$_DFFE_PN0N_/Q (DFFR_X1)
...
                                         clknet_3_4__leaf_clk (net)
                  0.03    0.00    0.13 ^ clkbuf_leaf_74_clk/A (CLKBUF_X3)
     8    9.81    0.01    0.04    0.18 ^ clkbuf_leaf_74_clk/Z (CLKBUF_X3)
                                         clknet_leaf_74_clk (net)
                  0.01    0.00    0.18 ^ issued_q[27]$_DFFE_PN0N_/CK (DFFR_X1)
                          0.00    0.18   clock reconvergence pessimism
                          0.01    0.18   library hold time
                                  0.18   data required time
-----------------------------------------------------------------------------
                                  0.18   data required time
                                 -0.27   data arrival time
-----------------------------------------------------------------------------
                                  0.09   slack (MET)



```

### Path 7

- source: `/orfs/flow/reports/nangate45/attention_shared_sram_read_group_adapter_w512_s2/base/6_finish.rpt`
- stage: `finish`
- startpoint: `issued_q[27]$_DFFE_PN0N_`
- endpoint: `issued_q[27]$_DFFE_PN0N_`
- path_group: `clk`
- path_type: `min`
- slack: `0.0900`
- data_arrival_time: `0.2500`
- data_required_time: `0.1700`

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
     1   12.81    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.00    0.00    0.00 ^ clkbuf_0_clk/A (CLKBUF_X3)
     8   39.25    0.03    0.05    0.06 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.03    0.00    0.06 ^ clkbuf_3_4__f_clk/A (CLKBUF_X3)
    12   31.66    0.03    0.06    0.12 ^ clkbuf_3_4__f_clk/Z (CLKBUF_X3)
                                         clknet_3_4__leaf_clk (net)
                  0.03    0.00    0.12 ^ clkbuf_leaf_74_clk/A (CLKBUF_X3)
     8    9.41    0.01    0.04    0.16 ^ clkbuf_leaf_74_clk/Z (CLKBUF_X3)
                                         clknet_leaf_74_clk (net)
                  0.01    0.00    0.16 ^ issued_q[27]$_DFFE_PN0N_/CK (DFFR_X1)
     2    2.75    0.01    0.09    0.25 v issued_q[27]$_DFFE_PN0N_/Q (DFFR_X1)
...
                                         clknet_3_4__leaf_clk (net)
                  0.03    0.00    0.12 ^ clkbuf_leaf_74_clk/A (CLKBUF_X3)
     8    9.41    0.01    0.04    0.16 ^ clkbuf_leaf_74_clk/Z (CLKBUF_X3)
                                         clknet_leaf_74_clk (net)
                  0.01    0.00    0.16 ^ issued_q[27]$_DFFE_PN0N_/CK (DFFR_X1)
                          0.00    0.16   clock reconvergence pessimism
                          0.01    0.17   library hold time
                                  0.17   data required time
-----------------------------------------------------------------------------
                                  0.17   data required time
                                 -0.25   data arrival time
-----------------------------------------------------------------------------
                                  0.09   slack (MET)



```

### Path 8

- source: `/orfs/flow/reports/nangate45/attention_shared_sram_read_group_adapter_w512_s2/base/4_cts_final.rpt`
- stage: `cts`
- startpoint: `rst_n (input port clocked by clk)`
- endpoint: `cycle_q[24]$_DFFE_PN0P_ (removal check against rising-edge clock clk)`
- path_group: `asynchronous`
- path_type: `min`
- slack: `1.6500`
- data_arrival_time: `2.0500`
- data_required_time: `0.4000`

```text
Startpoint: rst_n (input port clocked by clk)
Endpoint: cycle_q[24]$_DFFE_PN0P_ (removal check against rising-edge clock clk)
Path Group: asynchronous
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (propagated)
                          2.00    2.00 ^ input external delay
     1    4.17    0.00    0.00    2.00 ^ rst_n (in)
                                         rst_n (net)
                  0.00    0.00    2.00 ^ input7/A (CLKBUF_X3)
    11   37.78    0.03    0.05    2.05 ^ input7/Z (CLKBUF_X3)
                                         net6 (net)
                  0.03    0.00    2.05 ^ cycle_q[24]$_DFFE_PN0P_/RN (DFFR_X1)
                                  2.05   data arrival time

                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   16.99    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.00    0.00    0.00 ^ clkbuf_0_clk/A (CLKBUF_X3)
     8   48.35    0.04    0.06    0.06 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.04    0.00    0.07 ^ clkbuf_3_3__f_clk/A (CLKBUF_X3)
    10   41.18    0.03    0.07    0.14 ^ clkbuf_3_3__f_clk/Z (CLKBUF_X3)
                                         clknet_3_3__leaf_clk (net)
                  0.03    0.00    0.14 ^ clkbuf_leaf_26_clk/A (CLKBUF_X3)
     7    9.23    0.01    0.04    0.18 ^ clkbuf_leaf_26_clk/Z (CLKBUF_X3)
                                         clknet_leaf_26_clk (net)
                  0.01    0.00    0.18 ^ cycle_q[24]$_DFFE_PN0P_/CK (DFFR_X1)
                          0.00    0.18   clock reconvergence pessimism
                          0.22    0.40   library removal time
                                  0.40   data required time
-----------------------------------------------------------------------------
                                  0.40   data required time
                                 -2.05   data arrival time
-----------------------------------------------------------------------------
                                  1.65   slack (MET)
```
