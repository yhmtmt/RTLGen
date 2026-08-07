# OpenROAD Timing Debug Summary

- design_dir: `runs/designs/npu_blocks/attention_exact_partial_async_fifo_d4_source_domain_physical`
- metrics_path: `runs/designs/npu_blocks/attention_exact_partial_async_fifo_d4_source_domain_physical/metrics.csv`
- rows_considered: 4

## Metrics Rows

| param_hash | tag | status | critical_path_ns | density | result_path |
| --- | --- | --- | ---: | ---: | --- |
| 6e0fc234 | attention_exact_partial_async_fifo_per_domain_v1_6e0fc234 | ok | 0.6249 | 0.4 | `/orfs/flow/reports/nangate45/attention_exact_partial_async_fifo_d4_source_domain_physical/base/6_finish.rpt` |
| 66cddd28 | attention_exact_partial_async_fifo_per_domain_v1_66cddd28 | ok | 0.6300 | 0.4 | `/orfs/flow/reports/nangate45/attention_exact_partial_async_fifo_d4_source_domain_physical/base/6_finish.rpt` |
| 099a0e9e | attention_exact_partial_async_fifo_per_domain_v1_099a0e9e | ok | 0.6337 | 0.4 | `/orfs/flow/reports/nangate45/attention_exact_partial_async_fifo_d4_source_domain_physical/base/6_finish.rpt` |
| 47f786b2 | attention_exact_partial_async_fifo_per_domain_v1_47f786b2 | ok | 0.6351 | 0.4 | `/orfs/flow/reports/nangate45/attention_exact_partial_async_fifo_d4_source_domain_physical/base/6_finish.rpt` |

## Inspected Report Files

- `/orfs/flow/reports/nangate45/attention_exact_partial_async_fifo_d4_source_domain_physical/base/6_finish.rpt`
- `/orfs/flow/reports/nangate45/attention_exact_partial_async_fifo_d4_source_domain_physical/base/5_global_route.rpt`
- `/orfs/flow/reports/nangate45/attention_exact_partial_async_fifo_d4_source_domain_physical/base/5_route_drc.rpt`
- `/orfs/flow/reports/nangate45/attention_exact_partial_async_fifo_d4_source_domain_physical/base/4_cts_final.rpt`
- `/orfs/flow/reports/nangate45/attention_exact_partial_async_fifo_d4_source_domain_physical/base/3_resizer.rpt`
- `/orfs/flow/reports/nangate45/attention_exact_partial_async_fifo_d4_source_domain_physical/base/3_detailed_place.rpt`
- `/orfs/flow/reports/nangate45/attention_exact_partial_async_fifo_d4_source_domain_physical/base/3_global_place.rpt`
- `/orfs/flow/reports/nangate45/attention_exact_partial_async_fifo_d4_source_domain_physical/base/2_floorplan_final.rpt`
- `/orfs/flow/reports/nangate45/attention_exact_partial_async_fifo_d4_source_domain_physical/base/drt_antennas.log`
- `/orfs/flow/reports/nangate45/attention_exact_partial_async_fifo_d4_source_domain_physical/base/grt_antennas.log`
- `/orfs/flow/reports/nangate45/attention_exact_partial_async_fifo_d4_source_domain_physical/base/metadata-generate.log`

## Preferred Final-Stage Timing Paths

- raw_path_block_count: 208
- unique_path_block_count: 33
- preferred_stage: `finish`

### Path 1

- source: `/orfs/flow/reports/nangate45/attention_exact_partial_async_fifo_d4_source_domain_physical/base/6_finish.rpt`
- stage: `finish`
- startpoint: `helper_clk_q$_DFF_PN0_`
- endpoint: `helper_clk_q$_DFF_PN0_`
- path_group: `clk`
- path_type: `min`
- slack: `0.0700`
- data_arrival_time: `0.2200`
- data_required_time: `0.1500`

```text
Startpoint: helper_clk_q$_DFF_PN0_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: helper_clk_q$_DFF_PN0_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   16.68    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.00    0.00    0.00 ^ clkbuf_0_clk/A (CLKBUF_X3)
     4   16.46    0.02    0.04    0.04 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.02    0.00    0.04 ^ clkbuf_2_1__f_clk/A (CLKBUF_X3)
    13   32.33    0.03    0.06    0.10 ^ clkbuf_2_1__f_clk/Z (CLKBUF_X3)
                                         clknet_2_1__leaf_clk (net)
                  0.03    0.00    0.10 ^ clkbuf_leaf_10_clk/A (CLKBUF_X3)
     7   12.62    0.01    0.04    0.14 ^ clkbuf_leaf_10_clk/Z (CLKBUF_X3)
                                         clknet_leaf_10_clk (net)
                  0.01    0.00    0.14 ^ helper_clk_q$_DFF_PN0_/CK (DFFR_X2)
     1    1.32    0.01    0.08    0.22 ^ helper_clk_q$_DFF_PN0_/QN (DFFR_X2)
...
                                         clknet_2_1__leaf_clk (net)
                  0.03    0.00    0.10 ^ clkbuf_leaf_10_clk/A (CLKBUF_X3)
     7   12.62    0.01    0.04    0.14 ^ clkbuf_leaf_10_clk/Z (CLKBUF_X3)
                                         clknet_leaf_10_clk (net)
                  0.01    0.00    0.14 ^ helper_clk_q$_DFF_PN0_/CK (DFFR_X2)
                          0.00    0.14   clock reconvergence pessimism
                          0.01    0.15   library hold time
                                  0.15   data required time
-----------------------------------------------------------------------------
                                  0.15   data required time
                                 -0.22   data arrival time
-----------------------------------------------------------------------------
                                  0.07   slack (MET)



```

### Path 2

- source: `/orfs/flow/reports/nangate45/attention_exact_partial_async_fifo_d4_source_domain_physical/base/6_finish.rpt`
- stage: `finish`
- startpoint: `rst_n (input port clocked by clk)`
- endpoint: `u_async_fifo.wr_blocked_data_q[387]$_DFFE_PN0P_`
- path_group: `asynchronous`
- path_type: `min`
- slack: `1.6800`
- data_arrival_time: `2.0700`
- data_required_time: `0.3900`

```text
Startpoint: rst_n (input port clocked by clk)
Endpoint: u_async_fifo.wr_blocked_data_q[387]$_DFFE_PN0P_
          (removal check against rising-edge clock clk)
Path Group: asynchronous
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (propagated)
                          2.00    2.00 ^ input external delay
     1    6.96    0.00    0.00    2.00 ^ rst_n (in)
                                         rst_n (net)
                  0.00    0.00    2.00 ^ input59/A (CLKBUF_X3)
    11   40.40    0.03    0.04    2.05 ^ input59/Z (CLKBUF_X3)
                                         net58 (net)
                  0.04    0.02    2.07 ^ u_async_fifo.wr_blocked_data_q[387]$_DFFE_PN0P_/RN (DFFR_X1)
                                  2.07   data arrival time

                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   16.68    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.00    0.00    0.00 ^ clkbuf_0_clk/A (CLKBUF_X3)
     4   16.46    0.02    0.04    0.04 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.02    0.00    0.04 ^ clkbuf_2_3__f_clk/A (CLKBUF_X3)
    10   40.86    0.03    0.06    0.10 ^ clkbuf_2_3__f_clk/Z (CLKBUF_X3)
                                         clknet_2_3__leaf_clk (net)
                  0.03    0.00    0.11 ^ clkbuf_leaf_26_clk/A (CLKBUF_X3)
     9   12.24    0.01    0.05    0.15 ^ clkbuf_leaf_26_clk/Z (CLKBUF_X3)
                                         clknet_leaf_26_clk (net)
                  0.01    0.00    0.15 ^ u_async_fifo.wr_blocked_data_q[387]$_DFFE_PN0P_/CK (DFFR_X1)
                          0.00    0.15   clock reconvergence pessimism
                          0.23    0.39   library removal time
                                  0.39   data required time
-----------------------------------------------------------------------------
                                  0.39   data required time
                                 -2.07   data arrival time
-----------------------------------------------------------------------------
                                  1.68   slack (MET)
```

### Path 3

- source: `/orfs/flow/reports/nangate45/attention_exact_partial_async_fifo_d4_source_domain_physical/base/6_finish.rpt`
- stage: `finish`
- startpoint: `u_async_fifo.rd_gray_wr_sync2_q[2]$_DFF_PN0_`
- endpoint: `source_occupancy[2] (output port clocked by clk)`
- path_group: `clk`
- path_type: `max`
- slack: `9.3700`
- data_arrival_time: `0.6300`
- data_required_time: `10.0000`

```text
Startpoint: u_async_fifo.rd_gray_wr_sync2_q[2]$_DFF_PN0_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: source_occupancy[2] (output port clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   16.68    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.00    0.00    0.00 ^ clkbuf_0_clk/A (CLKBUF_X3)
     4   16.46    0.02    0.04    0.04 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.02    0.00    0.04 ^ clkbuf_2_0__f_clk/A (CLKBUF_X3)
    12   33.80    0.03    0.06    0.10 ^ clkbuf_2_0__f_clk/Z (CLKBUF_X3)
                                         clknet_2_0__leaf_clk (net)
                  0.03    0.00    0.10 ^ clkbuf_leaf_30_clk/A (CLKBUF_X3)
     9   11.72    0.01    0.04    0.14 ^ clkbuf_leaf_30_clk/Z (CLKBUF_X3)
                                         clknet_leaf_30_clk (net)
                  0.01    0.00    0.14 ^ u_async_fifo.rd_gray_wr_sync2_q[2]$_DFF_PN0_/CK (DFFR_X1)
     4    8.62    0.02    0.12    0.27 ^ u_async_fifo.rd_gray_wr_sync2_q[2]$_DFF_PN0_/Q (DFFR_X1)
                                         u_async_fifo.rd_gray_wr_sync2_q[2] (net)
...
                  0.03    0.01    0.63 ^ source_occupancy[2] (out)
                                  0.63   data arrival time

                         12.00   12.00   clock clk (rise edge)
                          0.00   12.00   clock network delay (propagated)
                          0.00   12.00   clock reconvergence pessimism
                         -2.00   10.00   output external delay
                                 10.00   data required time
-----------------------------------------------------------------------------
                                 10.00   data required time
                                 -0.63   data arrival time
-----------------------------------------------------------------------------
                                  9.37   slack (MET)



```

### Path 4

- source: `/orfs/flow/reports/nangate45/attention_exact_partial_async_fifo_d4_source_domain_physical/base/6_finish.rpt`
- stage: `finish`
- startpoint: `rst_n (input port clocked by clk)`
- endpoint: `source_lfsr_q[18]$_DFFE_PN0P_`
- path_group: `asynchronous`
- path_type: `max`
- slack: `9.8400`
- data_arrival_time: `2.3500`
- data_required_time: `12.1900`

```text
Startpoint: rst_n (input port clocked by clk)
Endpoint: source_lfsr_q[18]$_DFFE_PN0P_
          (recovery check against rising-edge clock clk)
Path Group: asynchronous
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (propagated)
                          2.00    2.00 ^ input external delay
     1    6.96    0.00    0.00    2.00 ^ rst_n (in)
                                         rst_n (net)
                  0.00    0.00    2.00 ^ input59/A (CLKBUF_X3)
    11   40.40    0.03    0.04    2.05 ^ input59/Z (CLKBUF_X3)
                                         net58 (net)
                  0.03    0.01    2.05 ^ place371/A (BUF_X4)
    65  142.88    0.07    0.09    2.14 ^ place371/Z (BUF_X4)
                                         net370 (net)
                  0.07    0.00    2.14 ^ place372/A (BUF_X2)
    15   42.18    0.04    0.06    2.20 ^ place372/Z (BUF_X2)
                                         net371 (net)
                  0.05    0.02    2.22 ^ place373/A (BUF_X2)
    37   79.63    0.09    0.12    2.34 ^ place373/Z (BUF_X2)
...
                                         clknet_0_clk (net)
                  0.02    0.00   12.04 ^ clkbuf_2_0__f_clk/A (CLKBUF_X3)
    12   33.80    0.03    0.06   12.10 ^ clkbuf_2_0__f_clk/Z (CLKBUF_X3)
                                         clknet_2_0__leaf_clk (net)
                  0.03    0.00   12.10 ^ clkbuf_leaf_37_clk/A (CLKBUF_X3)
     9   11.47    0.01    0.04   12.14 ^ clkbuf_leaf_37_clk/Z (CLKBUF_X3)
                                         clknet_leaf_37_clk (net)
                  0.01    0.00   12.14 ^ source_lfsr_q[18]$_DFFE_PN0P_/CK (DFFR_X1)
                          0.00   12.14   clock reconvergence pessimism
                          0.04   12.19   library recovery time
                                 12.19   data required time
-----------------------------------------------------------------------------
                                 12.19   data required time
                                 -2.35   data arrival time
-----------------------------------------------------------------------------
                                  9.84   slack (MET)
```

### Path 5

- source: `/orfs/flow/reports/nangate45/attention_exact_partial_async_fifo_d4_source_domain_physical/base/6_finish.rpt`
- stage: `finish`
- startpoint: `source_running_q$_DFF_PN0_`
- endpoint: `u_async_fifo.wr_full_q$_DFF_PN0_`
- path_group: `clk`
- path_type: `max`
- slack: `11.3100`
- data_arrival_time: `0.8000`
- data_required_time: `12.1100`

```text
Startpoint: source_running_q$_DFF_PN0_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: u_async_fifo.wr_full_q$_DFF_PN0_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

  Delay    Time   Description
---------------------------------------------------------
   0.00    0.00   clock clk (rise edge)
   0.00    0.00   clock source latency
   0.00    0.00 ^ clk (in)
   0.04    0.04 ^ clkbuf_0_clk/Z (CLKBUF_X3)
   0.06    0.10 ^ clkbuf_2_2__f_clk/Z (CLKBUF_X3)
   0.05    0.15 ^ clkbuf_leaf_34_clk/Z (CLKBUF_X3)
   0.00    0.15 ^ source_running_q$_DFF_PN0_/CK (DFFR_X1)
   0.11    0.26 ^ source_running_q$_DFF_PN0_/Q (DFFR_X1)
   0.02    0.28 v _1900_/ZN (INV_X1)
   0.07    0.36 v _1905_/ZN (OR3_X4)
   0.07    0.43 ^ _1906_/ZN (INV_X2)
   0.12    0.54 ^ place359/Z (BUF_X1)
   0.08    0.62 ^ _3288_/S (HA_X1)
   0.06    0.68 ^ _3274_/Z (XOR2_X1)
   0.02    0.70 v _3275_/ZN (NOR2_X1)
...
   0.00   12.00 ^ clk (in)
   0.04   12.04 ^ clkbuf_0_clk/Z (CLKBUF_X3)
   0.06   12.10 ^ clkbuf_2_0__f_clk/Z (CLKBUF_X3)
   0.05   12.14 ^ clkbuf_leaf_32_clk/Z (CLKBUF_X3)
   0.00   12.14 ^ u_async_fifo.wr_full_q$_DFF_PN0_/CK (DFFR_X1)
   0.00   12.14   clock reconvergence pessimism
  -0.04   12.11   library setup time
          12.11   data required time
---------------------------------------------------------
          12.11   data required time
          -0.80   data arrival time
---------------------------------------------------------
          11.31   slack (MET)



```


## Worst Timing Paths Across All Stages

### Path 1

- source: `/orfs/flow/reports/nangate45/attention_exact_partial_async_fifo_d4_source_domain_physical/base/2_floorplan_final.rpt`
- stage: `floorplan`
- startpoint: `helper_clk_q$_DFF_PN0_`
- endpoint: `helper_clk_q$_DFF_PN0_`
- path_group: `clk`
- path_type: `min`
- slack: `0.0600`
- data_arrival_time: `0.0600`
- data_required_time: `0.0100`

```text
Startpoint: helper_clk_q$_DFF_PN0_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: helper_clk_q$_DFF_PN0_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                  0.00    0.00    0.00 ^ helper_clk_q$_DFF_PN0_/CK (DFFR_X1)
     1    1.13    0.01    0.06    0.06 ^ helper_clk_q$_DFF_PN0_/QN (DFFR_X1)
                                         _0001_ (net)
                  0.01    0.00    0.06 ^ helper_clk_q$_DFF_PN0_/D (DFFR_X1)
                                  0.06   data arrival time

                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                          0.00    0.00   clock reconvergence pessimism
                                  0.00 ^ helper_clk_q$_DFF_PN0_/CK (DFFR_X1)
                          0.01    0.01   library hold time
                                  0.01   data required time
-----------------------------------------------------------------------------
                                  0.01   data required time
                                 -0.06   data arrival time
-----------------------------------------------------------------------------
                                  0.06   slack (MET)



```

### Path 2

- source: `/orfs/flow/reports/nangate45/attention_exact_partial_async_fifo_d4_source_domain_physical/base/3_detailed_place.rpt`
- stage: `detailed_place`
- startpoint: `helper_clk_q$_DFF_PN0_`
- endpoint: `helper_clk_q$_DFF_PN0_`
- path_group: `clk`
- path_type: `min`
- slack: `0.0700`
- data_arrival_time: `0.0700`
- data_required_time: `0.0100`

```text
Startpoint: helper_clk_q$_DFF_PN0_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: helper_clk_q$_DFF_PN0_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                  0.00    0.00    0.00 ^ helper_clk_q$_DFF_PN0_/CK (DFFR_X2)
     1    1.38    0.01    0.07    0.07 ^ helper_clk_q$_DFF_PN0_/QN (DFFR_X2)
                                         _0001_ (net)
                  0.01    0.00    0.07 ^ helper_clk_q$_DFF_PN0_/D (DFFR_X2)
                                  0.07   data arrival time

                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                          0.00    0.00   clock reconvergence pessimism
                                  0.00 ^ helper_clk_q$_DFF_PN0_/CK (DFFR_X2)
                          0.01    0.01   library hold time
                                  0.01   data required time
-----------------------------------------------------------------------------
                                  0.01   data required time
                                 -0.07   data arrival time
-----------------------------------------------------------------------------
                                  0.07   slack (MET)



```

### Path 3

- source: `/orfs/flow/reports/nangate45/attention_exact_partial_async_fifo_d4_source_domain_physical/base/3_global_place.rpt`
- stage: `global_place`
- startpoint: `helper_clk_q$_DFF_PN0_`
- endpoint: `helper_clk_q$_DFF_PN0_`
- path_group: `clk`
- path_type: `min`
- slack: `0.0700`
- data_arrival_time: `0.0700`
- data_required_time: `0.0100`

```text
Startpoint: helper_clk_q$_DFF_PN0_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: helper_clk_q$_DFF_PN0_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                  0.00    0.00    0.00 ^ helper_clk_q$_DFF_PN0_/CK (DFFR_X2)
     1    1.38    0.01    0.07    0.07 ^ helper_clk_q$_DFF_PN0_/QN (DFFR_X2)
                                         _0001_ (net)
                  0.01    0.00    0.07 ^ helper_clk_q$_DFF_PN0_/D (DFFR_X2)
                                  0.07   data arrival time

                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                          0.00    0.00   clock reconvergence pessimism
                                  0.00 ^ helper_clk_q$_DFF_PN0_/CK (DFFR_X2)
                          0.01    0.01   library hold time
                                  0.01   data required time
-----------------------------------------------------------------------------
                                  0.01   data required time
                                 -0.07   data arrival time
-----------------------------------------------------------------------------
                                  0.07   slack (MET)



```

### Path 4

- source: `/orfs/flow/reports/nangate45/attention_exact_partial_async_fifo_d4_source_domain_physical/base/3_resizer.rpt`
- stage: `resizer`
- startpoint: `helper_clk_q$_DFF_PN0_`
- endpoint: `helper_clk_q$_DFF_PN0_`
- path_group: `clk`
- path_type: `min`
- slack: `0.0700`
- data_arrival_time: `0.0700`
- data_required_time: `0.0100`

```text
Startpoint: helper_clk_q$_DFF_PN0_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: helper_clk_q$_DFF_PN0_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                  0.00    0.00    0.00 ^ helper_clk_q$_DFF_PN0_/CK (DFFR_X2)
     1    1.38    0.01    0.07    0.07 ^ helper_clk_q$_DFF_PN0_/QN (DFFR_X2)
                                         _0001_ (net)
                  0.01    0.00    0.07 ^ helper_clk_q$_DFF_PN0_/D (DFFR_X2)
                                  0.07   data arrival time

                  0.00    0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (ideal)
                          0.00    0.00   clock reconvergence pessimism
                                  0.00 ^ helper_clk_q$_DFF_PN0_/CK (DFFR_X2)
                          0.01    0.01   library hold time
                                  0.01   data required time
-----------------------------------------------------------------------------
                                  0.01   data required time
                                 -0.07   data arrival time
-----------------------------------------------------------------------------
                                  0.07   slack (MET)



```

### Path 5

- source: `/orfs/flow/reports/nangate45/attention_exact_partial_async_fifo_d4_source_domain_physical/base/4_cts_final.rpt`
- stage: `cts`
- startpoint: `helper_clk_q$_DFF_PN0_`
- endpoint: `helper_clk_q$_DFF_PN0_`
- path_group: `clk`
- path_type: `min`
- slack: `0.0700`
- data_arrival_time: `0.2300`
- data_required_time: `0.1600`

```text
Startpoint: helper_clk_q$_DFF_PN0_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: helper_clk_q$_DFF_PN0_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   21.49    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.00    0.00    0.00 ^ clkbuf_0_clk/A (CLKBUF_X3)
     4   19.92    0.02    0.04    0.04 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.02    0.00    0.04 ^ clkbuf_2_1__f_clk/A (CLKBUF_X3)
    13   35.75    0.03    0.06    0.10 ^ clkbuf_2_1__f_clk/Z (CLKBUF_X3)
                                         clknet_2_1__leaf_clk (net)
                  0.03    0.00    0.10 ^ clkbuf_leaf_10_clk/A (CLKBUF_X3)
     7   12.19    0.01    0.05    0.15 ^ clkbuf_leaf_10_clk/Z (CLKBUF_X3)
                                         clknet_leaf_10_clk (net)
                  0.01    0.00    0.15 ^ helper_clk_q$_DFF_PN0_/CK (DFFR_X2)
     1    1.38    0.01    0.08    0.23 ^ helper_clk_q$_DFF_PN0_/QN (DFFR_X2)
...
                                         clknet_2_1__leaf_clk (net)
                  0.03    0.00    0.10 ^ clkbuf_leaf_10_clk/A (CLKBUF_X3)
     7   12.19    0.01    0.05    0.15 ^ clkbuf_leaf_10_clk/Z (CLKBUF_X3)
                                         clknet_leaf_10_clk (net)
                  0.01    0.00    0.15 ^ helper_clk_q$_DFF_PN0_/CK (DFFR_X2)
                          0.00    0.15   clock reconvergence pessimism
                          0.01    0.16   library hold time
                                  0.16   data required time
-----------------------------------------------------------------------------
                                  0.16   data required time
                                 -0.23   data arrival time
-----------------------------------------------------------------------------
                                  0.07   slack (MET)



```

### Path 6

- source: `/orfs/flow/reports/nangate45/attention_exact_partial_async_fifo_d4_source_domain_physical/base/5_global_route.rpt`
- stage: `route`
- startpoint: `helper_clk_q$_DFF_PN0_`
- endpoint: `helper_clk_q$_DFF_PN0_`
- path_group: `clk`
- path_type: `min`
- slack: `0.0700`
- data_arrival_time: `0.2300`
- data_required_time: `0.1600`

```text
Startpoint: helper_clk_q$_DFF_PN0_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: helper_clk_q$_DFF_PN0_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   21.28    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.00    0.00    0.00 ^ clkbuf_0_clk/A (CLKBUF_X3)
     4   19.81    0.02    0.04    0.04 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.02    0.00    0.04 ^ clkbuf_2_1__f_clk/A (CLKBUF_X3)
    13   36.70    0.03    0.06    0.10 ^ clkbuf_2_1__f_clk/Z (CLKBUF_X3)
                                         clknet_2_1__leaf_clk (net)
                  0.03    0.00    0.11 ^ clkbuf_leaf_10_clk/A (CLKBUF_X3)
     7   12.90    0.01    0.05    0.15 ^ clkbuf_leaf_10_clk/Z (CLKBUF_X3)
                                         clknet_leaf_10_clk (net)
                  0.01    0.00    0.15 ^ helper_clk_q$_DFF_PN0_/CK (DFFR_X2)
     1    1.46    0.01    0.08    0.23 ^ helper_clk_q$_DFF_PN0_/QN (DFFR_X2)
...
                                         clknet_2_1__leaf_clk (net)
                  0.03    0.00    0.11 ^ clkbuf_leaf_10_clk/A (CLKBUF_X3)
     7   12.90    0.01    0.05    0.15 ^ clkbuf_leaf_10_clk/Z (CLKBUF_X3)
                                         clknet_leaf_10_clk (net)
                  0.01    0.00    0.15 ^ helper_clk_q$_DFF_PN0_/CK (DFFR_X2)
                          0.00    0.15   clock reconvergence pessimism
                          0.01    0.16   library hold time
                                  0.16   data required time
-----------------------------------------------------------------------------
                                  0.16   data required time
                                 -0.23   data arrival time
-----------------------------------------------------------------------------
                                  0.07   slack (MET)



```

### Path 7

- source: `/orfs/flow/reports/nangate45/attention_exact_partial_async_fifo_d4_source_domain_physical/base/6_finish.rpt`
- stage: `finish`
- startpoint: `helper_clk_q$_DFF_PN0_`
- endpoint: `helper_clk_q$_DFF_PN0_`
- path_group: `clk`
- path_type: `min`
- slack: `0.0700`
- data_arrival_time: `0.2200`
- data_required_time: `0.1500`

```text
Startpoint: helper_clk_q$_DFF_PN0_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: helper_clk_q$_DFF_PN0_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   16.68    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.00    0.00    0.00 ^ clkbuf_0_clk/A (CLKBUF_X3)
     4   16.46    0.02    0.04    0.04 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.02    0.00    0.04 ^ clkbuf_2_1__f_clk/A (CLKBUF_X3)
    13   32.33    0.03    0.06    0.10 ^ clkbuf_2_1__f_clk/Z (CLKBUF_X3)
                                         clknet_2_1__leaf_clk (net)
                  0.03    0.00    0.10 ^ clkbuf_leaf_10_clk/A (CLKBUF_X3)
     7   12.62    0.01    0.04    0.14 ^ clkbuf_leaf_10_clk/Z (CLKBUF_X3)
                                         clknet_leaf_10_clk (net)
                  0.01    0.00    0.14 ^ helper_clk_q$_DFF_PN0_/CK (DFFR_X2)
     1    1.32    0.01    0.08    0.22 ^ helper_clk_q$_DFF_PN0_/QN (DFFR_X2)
...
                                         clknet_2_1__leaf_clk (net)
                  0.03    0.00    0.10 ^ clkbuf_leaf_10_clk/A (CLKBUF_X3)
     7   12.62    0.01    0.04    0.14 ^ clkbuf_leaf_10_clk/Z (CLKBUF_X3)
                                         clknet_leaf_10_clk (net)
                  0.01    0.00    0.14 ^ helper_clk_q$_DFF_PN0_/CK (DFFR_X2)
                          0.00    0.14   clock reconvergence pessimism
                          0.01    0.15   library hold time
                                  0.15   data required time
-----------------------------------------------------------------------------
                                  0.15   data required time
                                 -0.22   data arrival time
-----------------------------------------------------------------------------
                                  0.07   slack (MET)



```

### Path 8

- source: `/orfs/flow/reports/nangate45/attention_exact_partial_async_fifo_d4_source_domain_physical/base/4_cts_final.rpt`
- stage: `cts`
- startpoint: `rst_n (input port clocked by clk)`
- endpoint: `u_async_fifo.wr_blocked_data_q[387]$_DFFE_PN0P_`
- path_group: `asynchronous`
- path_type: `min`
- slack: `1.6700`
- data_arrival_time: `2.0700`
- data_required_time: `0.4000`

```text
Startpoint: rst_n (input port clocked by clk)
Endpoint: u_async_fifo.wr_blocked_data_q[387]$_DFFE_PN0P_
          (removal check against rising-edge clock clk)
Path Group: asynchronous
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (propagated)
                          2.00    2.00 ^ input external delay
     1    8.23    0.00    0.00    2.00 ^ rst_n (in)
                                         rst_n (net)
                  0.00    0.00    2.00 ^ input59/A (CLKBUF_X3)
    11   43.73    0.03    0.05    2.05 ^ input59/Z (CLKBUF_X3)
                                         net58 (net)
                  0.04    0.02    2.07 ^ u_async_fifo.wr_blocked_data_q[387]$_DFFE_PN0P_/RN (DFFR_X1)
                                  2.07   data arrival time

                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   21.49    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.00    0.00    0.00 ^ clkbuf_0_clk/A (CLKBUF_X3)
     4   19.92    0.02    0.04    0.04 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.02    0.00    0.04 ^ clkbuf_2_3__f_clk/A (CLKBUF_X3)
    10   47.73    0.04    0.07    0.11 ^ clkbuf_2_3__f_clk/Z (CLKBUF_X3)
                                         clknet_2_3__leaf_clk (net)
                  0.04    0.00    0.12 ^ clkbuf_leaf_26_clk/A (CLKBUF_X3)
     9   12.19    0.01    0.05    0.16 ^ clkbuf_leaf_26_clk/Z (CLKBUF_X3)
                                         clknet_leaf_26_clk (net)
                  0.01    0.00    0.16 ^ u_async_fifo.wr_blocked_data_q[387]$_DFFE_PN0P_/CK (DFFR_X1)
                          0.00    0.16   clock reconvergence pessimism
                          0.23    0.40   library removal time
                                  0.40   data required time
-----------------------------------------------------------------------------
                                  0.40   data required time
                                 -2.07   data arrival time
-----------------------------------------------------------------------------
                                  1.67   slack (MET)
```
