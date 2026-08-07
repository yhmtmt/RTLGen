# OpenROAD Timing Debug Summary

- design_dir: `runs/designs/npu_blocks/attention_exact_partial_async_fifo_d4_destination_domain_physical`
- metrics_path: `runs/designs/npu_blocks/attention_exact_partial_async_fifo_d4_destination_domain_physical/metrics.csv`
- rows_considered: 4

## Metrics Rows

| param_hash | tag | status | critical_path_ns | density | result_path |
| --- | --- | --- | ---: | ---: | --- |
| 66cddd28 | attention_exact_partial_async_fifo_per_domain_v1_66cddd28 | ok | 0.6508 | 0.4 | `/orfs/flow/reports/nangate45/attention_exact_partial_async_fifo_d4_destination_domain_physical/base/6_finish.rpt` |
| 6e0fc234 | attention_exact_partial_async_fifo_per_domain_v1_6e0fc234 | ok | 0.6515 | 0.4 | `/orfs/flow/reports/nangate45/attention_exact_partial_async_fifo_d4_destination_domain_physical/base/6_finish.rpt` |
| 47f786b2 | attention_exact_partial_async_fifo_per_domain_v1_47f786b2 | ok | 0.6516 | 0.4 | `/orfs/flow/reports/nangate45/attention_exact_partial_async_fifo_d4_destination_domain_physical/base/6_finish.rpt` |
| 099a0e9e | attention_exact_partial_async_fifo_per_domain_v1_099a0e9e | ok | 0.6962 | 0.4 | `/orfs/flow/reports/nangate45/attention_exact_partial_async_fifo_d4_destination_domain_physical/base/6_finish.rpt` |

## Inspected Report Files

- `/orfs/flow/reports/nangate45/attention_exact_partial_async_fifo_d4_destination_domain_physical/base/6_finish.rpt`
- `/orfs/flow/reports/nangate45/attention_exact_partial_async_fifo_d4_destination_domain_physical/base/5_global_route.rpt`
- `/orfs/flow/reports/nangate45/attention_exact_partial_async_fifo_d4_destination_domain_physical/base/5_route_drc.rpt`
- `/orfs/flow/reports/nangate45/attention_exact_partial_async_fifo_d4_destination_domain_physical/base/4_cts_final.rpt`
- `/orfs/flow/reports/nangate45/attention_exact_partial_async_fifo_d4_destination_domain_physical/base/3_resizer.rpt`
- `/orfs/flow/reports/nangate45/attention_exact_partial_async_fifo_d4_destination_domain_physical/base/3_detailed_place.rpt`
- `/orfs/flow/reports/nangate45/attention_exact_partial_async_fifo_d4_destination_domain_physical/base/3_global_place.rpt`
- `/orfs/flow/reports/nangate45/attention_exact_partial_async_fifo_d4_destination_domain_physical/base/2_floorplan_final.rpt`
- `/orfs/flow/reports/nangate45/attention_exact_partial_async_fifo_d4_destination_domain_physical/base/drt_antennas.log`
- `/orfs/flow/reports/nangate45/attention_exact_partial_async_fifo_d4_destination_domain_physical/base/grt_antennas.log`
- `/orfs/flow/reports/nangate45/attention_exact_partial_async_fifo_d4_destination_domain_physical/base/metadata-generate.log`

## Preferred Final-Stage Timing Paths

- raw_path_block_count: 208
- unique_path_block_count: 33
- preferred_stage: `finish`

### Path 1

- source: `/orfs/flow/reports/nangate45/attention_exact_partial_async_fifo_d4_destination_domain_physical/base/6_finish.rpt`
- stage: `finish`
- startpoint: `helper_clk_q$_DFF_PN0_`
- endpoint: `helper_clk_q$_DFF_PN0_`
- path_group: `clk`
- path_type: `min`
- slack: `0.0700`
- data_arrival_time: `0.2400`
- data_required_time: `0.1700`

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
     1   16.47    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.00    0.00    0.00 ^ clkbuf_0_clk/A (CLKBUF_X3)
     8   42.21    0.03    0.06    0.06 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.03    0.00    0.06 ^ clkbuf_3_5_0_clk/A (CLKBUF_X3)
     2    8.28    0.01    0.04    0.11 ^ clkbuf_3_5_0_clk/Z (CLKBUF_X3)
                                         clknet_3_5_0_clk (net)
                  0.01    0.00    0.11 ^ clkbuf_4_11__f_clk/A (CLKBUF_X3)
    22   30.38    0.03    0.05    0.16 ^ clkbuf_4_11__f_clk/Z (CLKBUF_X3)
                                         clknet_4_11__leaf_clk (net)
                  0.03    0.00    0.16 ^ helper_clk_q$_DFF_PN0_/CK (DFFR_X2)
     1    1.46    0.01    0.08    0.24 ^ helper_clk_q$_DFF_PN0_/QN (DFFR_X2)
...
                                         clknet_3_5_0_clk (net)
                  0.01    0.00    0.11 ^ clkbuf_4_11__f_clk/A (CLKBUF_X3)
    22   30.38    0.03    0.05    0.16 ^ clkbuf_4_11__f_clk/Z (CLKBUF_X3)
                                         clknet_4_11__leaf_clk (net)
                  0.03    0.00    0.16 ^ helper_clk_q$_DFF_PN0_/CK (DFFR_X2)
                          0.00    0.16   clock reconvergence pessimism
                          0.01    0.17   library hold time
                                  0.17   data required time
-----------------------------------------------------------------------------
                                  0.17   data required time
                                 -0.24   data arrival time
-----------------------------------------------------------------------------
                                  0.07   slack (MET)



```

### Path 2

- source: `/orfs/flow/reports/nangate45/attention_exact_partial_async_fifo_d4_destination_domain_physical/base/6_finish.rpt`
- stage: `finish`
- startpoint: `rst_n (input port clocked by clk)`
- endpoint: `destination_fold_q[16]$_DFFE_PN0P_`
- path_group: `asynchronous`
- path_type: `min`
- slack: `1.7400`
- data_arrival_time: `2.2000`
- data_required_time: `0.4600`

```text
Startpoint: rst_n (input port clocked by clk)
Endpoint: destination_fold_q[16]$_DFFE_PN0P_
          (removal check against rising-edge clock clk)
Path Group: asynchronous
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (propagated)
                          2.00    2.00 ^ input external delay
     1    3.46    0.00    0.00    2.00 ^ rst_n (in)
                                         rst_n (net)
                  0.00    0.00    2.00 ^ input59/A (CLKBUF_X3)
    10   49.97    0.03    0.05    2.05 ^ input59/Z (CLKBUF_X3)
                                         net58 (net)
                  0.05    0.03    2.08 ^ place379/A (BUF_X2)
    39   82.49    0.09    0.12    2.20 ^ place379/Z (BUF_X2)
                                         net378 (net)
                  0.09    0.00    2.20 ^ destination_fold_q[16]$_DFFE_PN0P_/RN (DFFR_X1)
                                  2.20   data arrival time

                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
...
                                         clknet_0_clk (net)
                  0.03    0.00    0.06 ^ clkbuf_3_5_0_clk/A (CLKBUF_X3)
     2    8.28    0.01    0.04    0.11 ^ clkbuf_3_5_0_clk/Z (CLKBUF_X3)
                                         clknet_3_5_0_clk (net)
                  0.01    0.00    0.11 ^ clkbuf_4_11__f_clk/A (CLKBUF_X3)
    22   30.38    0.03    0.05    0.16 ^ clkbuf_4_11__f_clk/Z (CLKBUF_X3)
                                         clknet_4_11__leaf_clk (net)
                  0.03    0.00    0.16 ^ destination_fold_q[16]$_DFFE_PN0P_/CK (DFFR_X1)
                          0.00    0.16   clock reconvergence pessimism
                          0.30    0.46   library removal time
                                  0.46   data required time
-----------------------------------------------------------------------------
                                  0.46   data required time
                                 -2.20   data arrival time
-----------------------------------------------------------------------------
                                  1.74   slack (MET)
```

### Path 3

- source: `/orfs/flow/reports/nangate45/attention_exact_partial_async_fifo_d4_destination_domain_physical/base/6_finish.rpt`
- stage: `finish`
- startpoint: `u_async_fifo.wr_gray_rd_sync2_q[2]$_DFF_PN0_`
- endpoint: `destination_occupancy[2] (output port clocked by clk)`
- path_group: `clk`
- path_type: `max`
- slack: `9.3500`
- data_arrival_time: `0.6500`
- data_required_time: `10.0000`

```text
Startpoint: u_async_fifo.wr_gray_rd_sync2_q[2]$_DFF_PN0_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: destination_occupancy[2] (output port clocked by clk)
Path Group: clk
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
     1   16.47    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.00    0.00    0.00 ^ clkbuf_0_clk/A (CLKBUF_X3)
     8   42.21    0.03    0.06    0.06 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.03    0.00    0.06 ^ clkbuf_3_1_0_clk/A (CLKBUF_X3)
     2    7.18    0.01    0.04    0.10 ^ clkbuf_3_1_0_clk/Z (CLKBUF_X3)
                                         clknet_3_1_0_clk (net)
                  0.01    0.00    0.11 ^ clkbuf_4_2__f_clk/A (CLKBUF_X3)
     9   13.68    0.01    0.04    0.14 ^ clkbuf_4_2__f_clk/Z (CLKBUF_X3)
                                         clknet_4_2__leaf_clk (net)
                  0.01    0.00    0.15 ^ u_async_fifo.wr_gray_rd_sync2_q[2]$_DFF_PN0_/CK (DFFR_X1)
     4    7.87    0.02    0.12    0.26 ^ u_async_fifo.wr_gray_rd_sync2_q[2]$_DFF_PN0_/Q (DFFR_X1)
                                         u_async_fifo.wr_gray_rd_sync2_q[2] (net)
...
                  0.03    0.00    0.65 ^ destination_occupancy[2] (out)
                                  0.65   data arrival time

                         12.00   12.00   clock clk (rise edge)
                          0.00   12.00   clock network delay (propagated)
                          0.00   12.00   clock reconvergence pessimism
                         -2.00   10.00   output external delay
                                 10.00   data required time
-----------------------------------------------------------------------------
                                 10.00   data required time
                                 -0.65   data arrival time
-----------------------------------------------------------------------------
                                  9.35   slack (MET)



```

### Path 4

- source: `/orfs/flow/reports/nangate45/attention_exact_partial_async_fifo_d4_destination_domain_physical/base/6_finish.rpt`
- stage: `finish`
- startpoint: `rst_n (input port clocked by clk)`
- endpoint: `u_async_fifo.empty_cycles[2]$_DFFE_PN0P_`
- path_group: `asynchronous`
- path_type: `max`
- slack: `9.8300`
- data_arrival_time: `2.3600`
- data_required_time: `12.1900`

```text
Startpoint: rst_n (input port clocked by clk)
Endpoint: u_async_fifo.empty_cycles[2]$_DFFE_PN0P_
          (recovery check against rising-edge clock clk)
Path Group: asynchronous
Path Type: max

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (propagated)
                          2.00    2.00 ^ input external delay
     1    3.46    0.00    0.00    2.00 ^ rst_n (in)
                                         rst_n (net)
                  0.00    0.00    2.00 ^ input59/A (CLKBUF_X3)
    10   49.97    0.03    0.05    2.05 ^ input59/Z (CLKBUF_X3)
                                         net58 (net)
                  0.05    0.03    2.08 ^ place382/A (BUF_X2)
    28   58.32    0.07    0.09    2.17 ^ place382/Z (BUF_X2)
                                         net381 (net)
                  0.07    0.01    2.18 ^ place384/A (BUF_X1)
     6   21.81    0.05    0.08    2.26 ^ place384/Z (BUF_X1)
                                         net383 (net)
                  0.05    0.01    2.26 ^ place385/A (BUF_X2)
    28   59.13    0.07    0.09    2.36 ^ place385/Z (BUF_X2)
...
                                         clknet_0_clk (net)
                  0.03    0.00   12.06 ^ clkbuf_3_0_0_clk/A (CLKBUF_X3)
     2    7.71    0.01    0.04   12.11 ^ clkbuf_3_0_0_clk/Z (CLKBUF_X3)
                                         clknet_3_0_0_clk (net)
                  0.01    0.00   12.11 ^ clkbuf_4_1__f_clk/A (CLKBUF_X3)
     7   12.46    0.01    0.04   12.14 ^ clkbuf_4_1__f_clk/Z (CLKBUF_X3)
                                         clknet_4_1__leaf_clk (net)
                  0.01    0.00   12.15 ^ u_async_fifo.empty_cycles[2]$_DFFE_PN0P_/CK (DFFR_X1)
                          0.00   12.15   clock reconvergence pessimism
                          0.05   12.19   library recovery time
                                 12.19   data required time
-----------------------------------------------------------------------------
                                 12.19   data required time
                                 -2.36   data arrival time
-----------------------------------------------------------------------------
                                  9.83   slack (MET)
```

### Path 5

- source: `/orfs/flow/reports/nangate45/attention_exact_partial_async_fifo_d4_destination_domain_physical/base/6_finish.rpt`
- stage: `finish`
- startpoint: `u_async_fifo.rd_bin_q[1]$_DFF_PN0_`
- endpoint: `u_async_fifo.rd_protocol_error$_DFFE_PN0P_`
- path_group: `clk`
- path_type: `max`
- slack: `11.2400`
- data_arrival_time: `0.8700`
- data_required_time: `12.1100`

```text
Startpoint: u_async_fifo.rd_bin_q[1]$_DFF_PN0_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: u_async_fifo.rd_protocol_error$_DFFE_PN0P_
          (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

  Delay    Time   Description
---------------------------------------------------------
   0.00    0.00   clock clk (rise edge)
   0.00    0.00   clock source latency
   0.00    0.00 ^ clk (in)
   0.06    0.06 ^ clkbuf_0_clk/Z (CLKBUF_X3)
   0.05    0.10 ^ clkbuf_3_1_0_clk/Z (CLKBUF_X3)
   0.04    0.14 ^ clkbuf_4_2__f_clk/Z (CLKBUF_X3)
   0.00    0.15 ^ u_async_fifo.rd_bin_q[1]$_DFF_PN0_/CK (DFFR_X1)
   0.09    0.24 v u_async_fifo.rd_bin_q[1]$_DFF_PN0_/Q (DFFR_X1)
   0.04    0.28 v place369/Z (BUF_X4)
   0.11    0.39 ^ _1965_/ZN (INV_X2)
   0.11    0.50 ^ place368/Z (BUF_X2)
   0.08    0.58 v _1966_/Z (MUX2_X1)
   0.06    0.64 v _3083_/Z (XOR2_X1)
   0.05    0.69 ^ _3084_/ZN (NOR3_X2)
   0.02    0.71 v _3088_/ZN (AOI21_X1)
...
   0.00   12.00 ^ clk (in)
   0.06   12.06 ^ clkbuf_0_clk/Z (CLKBUF_X3)
   0.05   12.11 ^ clkbuf_3_4_0_clk/Z (CLKBUF_X3)
   0.05   12.15 ^ clkbuf_4_9__f_clk/Z (CLKBUF_X3)
   0.00   12.15 ^ u_async_fifo.rd_protocol_error$_DFFE_PN0P_/CK (DFFR_X1)
   0.00   12.15   clock reconvergence pessimism
  -0.04   12.11   library setup time
          12.11   data required time
---------------------------------------------------------
          12.11   data required time
          -0.87   data arrival time
---------------------------------------------------------
          11.24   slack (MET)



```


## Worst Timing Paths Across All Stages

### Path 1

- source: `/orfs/flow/reports/nangate45/attention_exact_partial_async_fifo_d4_destination_domain_physical/base/2_floorplan_final.rpt`
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

- source: `/orfs/flow/reports/nangate45/attention_exact_partial_async_fifo_d4_destination_domain_physical/base/3_detailed_place.rpt`
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

- source: `/orfs/flow/reports/nangate45/attention_exact_partial_async_fifo_d4_destination_domain_physical/base/3_global_place.rpt`
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

- source: `/orfs/flow/reports/nangate45/attention_exact_partial_async_fifo_d4_destination_domain_physical/base/3_resizer.rpt`
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

- source: `/orfs/flow/reports/nangate45/attention_exact_partial_async_fifo_d4_destination_domain_physical/base/4_cts_final.rpt`
- stage: `cts`
- startpoint: `helper_clk_q$_DFF_PN0_`
- endpoint: `helper_clk_q$_DFF_PN0_`
- path_group: `clk`
- path_type: `min`
- slack: `0.0700`
- data_arrival_time: `0.2500`
- data_required_time: `0.1900`

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
     1   23.51    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.00    0.00    0.00 ^ clkbuf_0_clk/A (CLKBUF_X3)
     8   53.99    0.04    0.07    0.07 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.04    0.00    0.07 ^ clkbuf_3_5_0_clk/A (CLKBUF_X3)
     2    9.26    0.01    0.05    0.12 ^ clkbuf_3_5_0_clk/Z (CLKBUF_X3)
                                         clknet_3_5_0_clk (net)
                  0.01    0.00    0.12 ^ clkbuf_4_11__f_clk/A (CLKBUF_X3)
    22   29.75    0.03    0.05    0.17 ^ clkbuf_4_11__f_clk/Z (CLKBUF_X3)
                                         clknet_4_11__leaf_clk (net)
                  0.03    0.00    0.17 ^ helper_clk_q$_DFF_PN0_/CK (DFFR_X2)
     1    1.38    0.01    0.08    0.25 ^ helper_clk_q$_DFF_PN0_/QN (DFFR_X2)
...
                                         clknet_3_5_0_clk (net)
                  0.01    0.00    0.12 ^ clkbuf_4_11__f_clk/A (CLKBUF_X3)
    22   29.75    0.03    0.05    0.17 ^ clkbuf_4_11__f_clk/Z (CLKBUF_X3)
                                         clknet_4_11__leaf_clk (net)
                  0.03    0.00    0.17 ^ helper_clk_q$_DFF_PN0_/CK (DFFR_X2)
                          0.00    0.17   clock reconvergence pessimism
                          0.01    0.19   library hold time
                                  0.19   data required time
-----------------------------------------------------------------------------
                                  0.19   data required time
                                 -0.25   data arrival time
-----------------------------------------------------------------------------
                                  0.07   slack (MET)



```

### Path 6

- source: `/orfs/flow/reports/nangate45/attention_exact_partial_async_fifo_d4_destination_domain_physical/base/5_global_route.rpt`
- stage: `route`
- startpoint: `helper_clk_q$_DFF_PN0_`
- endpoint: `helper_clk_q$_DFF_PN0_`
- path_group: `clk`
- path_type: `min`
- slack: `0.0700`
- data_arrival_time: `0.2600`
- data_required_time: `0.1900`

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
     1   23.45    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.00    0.00    0.00 ^ clkbuf_0_clk/A (CLKBUF_X3)
     8   54.08    0.04    0.07    0.07 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.04    0.00    0.07 ^ clkbuf_3_5_0_clk/A (CLKBUF_X3)
     2    9.74    0.01    0.05    0.12 ^ clkbuf_3_5_0_clk/Z (CLKBUF_X3)
                                         clknet_3_5_0_clk (net)
                  0.01    0.00    0.12 ^ clkbuf_4_11__f_clk/A (CLKBUF_X3)
    22   29.88    0.03    0.05    0.17 ^ clkbuf_4_11__f_clk/Z (CLKBUF_X3)
                                         clknet_4_11__leaf_clk (net)
                  0.03    0.00    0.18 ^ helper_clk_q$_DFF_PN0_/CK (DFFR_X2)
     1    1.46    0.01    0.08    0.26 ^ helper_clk_q$_DFF_PN0_/QN (DFFR_X2)
...
                                         clknet_3_5_0_clk (net)
                  0.01    0.00    0.12 ^ clkbuf_4_11__f_clk/A (CLKBUF_X3)
    22   29.88    0.03    0.05    0.17 ^ clkbuf_4_11__f_clk/Z (CLKBUF_X3)
                                         clknet_4_11__leaf_clk (net)
                  0.03    0.00    0.18 ^ helper_clk_q$_DFF_PN0_/CK (DFFR_X2)
                          0.00    0.18   clock reconvergence pessimism
                          0.01    0.19   library hold time
                                  0.19   data required time
-----------------------------------------------------------------------------
                                  0.19   data required time
                                 -0.26   data arrival time
-----------------------------------------------------------------------------
                                  0.07   slack (MET)



```

### Path 7

- source: `/orfs/flow/reports/nangate45/attention_exact_partial_async_fifo_d4_destination_domain_physical/base/6_finish.rpt`
- stage: `finish`
- startpoint: `helper_clk_q$_DFF_PN0_`
- endpoint: `helper_clk_q$_DFF_PN0_`
- path_group: `clk`
- path_type: `min`
- slack: `0.0700`
- data_arrival_time: `0.2400`
- data_required_time: `0.1700`

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
     1   16.47    0.00    0.00    0.00 ^ clk (in)
                                         clk (net)
                  0.00    0.00    0.00 ^ clkbuf_0_clk/A (CLKBUF_X3)
     8   42.21    0.03    0.06    0.06 ^ clkbuf_0_clk/Z (CLKBUF_X3)
                                         clknet_0_clk (net)
                  0.03    0.00    0.06 ^ clkbuf_3_5_0_clk/A (CLKBUF_X3)
     2    8.28    0.01    0.04    0.11 ^ clkbuf_3_5_0_clk/Z (CLKBUF_X3)
                                         clknet_3_5_0_clk (net)
                  0.01    0.00    0.11 ^ clkbuf_4_11__f_clk/A (CLKBUF_X3)
    22   30.38    0.03    0.05    0.16 ^ clkbuf_4_11__f_clk/Z (CLKBUF_X3)
                                         clknet_4_11__leaf_clk (net)
                  0.03    0.00    0.16 ^ helper_clk_q$_DFF_PN0_/CK (DFFR_X2)
     1    1.46    0.01    0.08    0.24 ^ helper_clk_q$_DFF_PN0_/QN (DFFR_X2)
...
                                         clknet_3_5_0_clk (net)
                  0.01    0.00    0.11 ^ clkbuf_4_11__f_clk/A (CLKBUF_X3)
    22   30.38    0.03    0.05    0.16 ^ clkbuf_4_11__f_clk/Z (CLKBUF_X3)
                                         clknet_4_11__leaf_clk (net)
                  0.03    0.00    0.16 ^ helper_clk_q$_DFF_PN0_/CK (DFFR_X2)
                          0.00    0.16   clock reconvergence pessimism
                          0.01    0.17   library hold time
                                  0.17   data required time
-----------------------------------------------------------------------------
                                  0.17   data required time
                                 -0.24   data arrival time
-----------------------------------------------------------------------------
                                  0.07   slack (MET)



```

### Path 8

- source: `/orfs/flow/reports/nangate45/attention_exact_partial_async_fifo_d4_destination_domain_physical/base/5_global_route.rpt`
- stage: `route`
- startpoint: `rst_n (input port clocked by clk)`
- endpoint: `destination_fold_q[22]$_DFFE_PN0P_`
- path_group: `asynchronous`
- path_type: `min`
- slack: `1.7200`
- data_arrival_time: `2.2000`
- data_required_time: `0.4800`

```text
Startpoint: rst_n (input port clocked by clk)
Endpoint: destination_fold_q[22]$_DFFE_PN0P_
          (removal check against rising-edge clock clk)
Path Group: asynchronous
Path Type: min

Fanout     Cap    Slew   Delay    Time   Description
-----------------------------------------------------------------------------
                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock network delay (propagated)
                          2.00    2.00 ^ input external delay
     1    4.15    0.00    0.00    2.00 ^ rst_n (in)
                                         rst_n (net)
                  0.00    0.00    2.00 ^ input59/A (CLKBUF_X3)
    10   51.78    0.03    0.05    2.05 ^ input59/Z (CLKBUF_X3)
                                         net58 (net)
                  0.05    0.03    2.08 ^ place379/A (BUF_X2)
    39   84.63    0.09    0.12    2.20 ^ place379/Z (BUF_X2)
                                         net378 (net)
                  0.09    0.00    2.20 ^ destination_fold_q[22]$_DFFE_PN0P_/RN (DFFR_X1)
                                  2.20   data arrival time

                          0.00    0.00   clock clk (rise edge)
                          0.00    0.00   clock source latency
...
                                         clknet_0_clk (net)
                  0.04    0.00    0.07 ^ clkbuf_3_5_0_clk/A (CLKBUF_X3)
     2    9.74    0.01    0.05    0.12 ^ clkbuf_3_5_0_clk/Z (CLKBUF_X3)
                                         clknet_3_5_0_clk (net)
                  0.01    0.00    0.12 ^ clkbuf_4_11__f_clk/A (CLKBUF_X3)
    22   29.88    0.03    0.05    0.17 ^ clkbuf_4_11__f_clk/Z (CLKBUF_X3)
                                         clknet_4_11__leaf_clk (net)
                  0.03    0.00    0.18 ^ destination_fold_q[22]$_DFFE_PN0P_/CK (DFFR_X1)
                          0.00    0.18   clock reconvergence pessimism
                          0.31    0.48   library removal time
                                  0.48   data required time
-----------------------------------------------------------------------------
                                  0.48   data required time
                                 -2.20   data arrival time
-----------------------------------------------------------------------------
                                  1.72   slack (MET)
```
