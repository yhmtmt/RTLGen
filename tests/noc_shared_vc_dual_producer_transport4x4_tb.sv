`timescale 1ns/1ps

module noc_shared_vc_dual_producer_transport4x4_tb;
  localparam integer DATA_W = 32;
  localparam integer ENDPOINT_W = 4;
  localparam integer VC_W = 2;
  localparam integer TAG_W = 8;
  localparam integer FRAGMENT_W = 3;
  localparam integer EP5_DEST_LSB = 20;
  localparam integer EP5_TAG_LSB = 40;
  localparam integer EP5_FRAGMENT_LSB = 15;
  localparam integer EP5_VC_LSB = 10;
  localparam integer EP5_DATA_LSB = 160;
  localparam integer EP6_DEST_LSB = 24;
  localparam integer EP6_TAG_LSB = 48;
  localparam integer EP6_FRAGMENT_LSB = 18;
  localparam integer EP6_VC_LSB = 12;
  localparam integer EP6_DATA_LSB = 192;

  reg clk = 1'b0;
  reg rst_n = 1'b0;
  always #5 clk = ~clk;

  reg [15:0] producer0_in_valid = 16'b0;
  wire [15:0] producer0_in_ready;
  reg [16*ENDPOINT_W-1:0] producer0_in_destination = 0;
  reg [16*ENDPOINT_W-1:0] producer0_in_source = 0;
  reg [16*TAG_W-1:0] producer0_in_tag = 0;
  reg [16*FRAGMENT_W-1:0] producer0_in_fragment = 0;
  reg [15:0] producer0_in_last = 16'b0;
  reg [16*VC_W-1:0] producer0_in_vc = 0;
  reg [16*DATA_W-1:0] producer0_in_data = 0;

  reg [15:0] producer1_in_valid = 16'b0;
  wire [15:0] producer1_in_ready;
  reg [16*ENDPOINT_W-1:0] producer1_in_destination = 0;
  reg [16*ENDPOINT_W-1:0] producer1_in_source = 0;
  reg [16*TAG_W-1:0] producer1_in_tag = 0;
  reg [16*FRAGMENT_W-1:0] producer1_in_fragment = 0;
  reg [15:0] producer1_in_last = 16'b0;
  reg [16*VC_W-1:0] producer1_in_vc = 0;
  reg [16*DATA_W-1:0] producer1_in_data = 0;

  wire [15:0] producer0_out_valid;
  reg [15:0] producer0_out_ready = 16'hffff;
  wire [16*ENDPOINT_W-1:0] producer0_out_destination;
  wire [16*ENDPOINT_W-1:0] producer0_out_source;
  wire [16*TAG_W-1:0] producer0_out_tag;
  wire [16*FRAGMENT_W-1:0] producer0_out_fragment;
  wire [15:0] producer0_out_last;
  wire [16*VC_W-1:0] producer0_out_vc;
  wire [16*DATA_W-1:0] producer0_out_data;

  wire [15:0] producer1_out_valid;
  reg [15:0] producer1_out_ready = 16'hffff;
  wire [16*ENDPOINT_W-1:0] producer1_out_destination;
  wire [16*ENDPOINT_W-1:0] producer1_out_source;
  wire [16*TAG_W-1:0] producer1_out_tag;
  wire [16*FRAGMENT_W-1:0] producer1_out_fragment;
  wire [15:0] producer1_out_last;
  wire [16*VC_W-1:0] producer1_out_vc;
  wire [16*DATA_W-1:0] producer1_out_data;

  wire [15:0] injection_protocol_error;
  wire [15:0] ejection_protocol_error;
  wire protocol_error;

  integer cycle_count = 0;
  integer delivered_p0 = 0;
  integer delivered_p1 = 0;
  reg seen_p0_a = 1'b0;
  reg seen_p1_b = 1'b0;

  noc_shared_vc_dual_producer_transport4x4 #(
    .DATA_W(DATA_W),
    .ENDPOINT_W(ENDPOINT_W),
    .VC_W(VC_W),
    .TAG_W(TAG_W),
    .FRAGMENT_W(FRAGMENT_W),
    .VC_COUNT(2),
    .FIFO_DEPTH(1),
    .ENABLE_DEBUG_COUNTERS(0)
  ) dut (
    .clk(clk),
    .rst_n(rst_n),
    .producer0_in_valid(producer0_in_valid),
    .producer0_in_ready(producer0_in_ready),
    .producer0_in_destination(producer0_in_destination),
    .producer0_in_source(producer0_in_source),
    .producer0_in_tag(producer0_in_tag),
    .producer0_in_fragment(producer0_in_fragment),
    .producer0_in_last(producer0_in_last),
    .producer0_in_vc(producer0_in_vc),
    .producer0_in_data(producer0_in_data),
    .producer1_in_valid(producer1_in_valid),
    .producer1_in_ready(producer1_in_ready),
    .producer1_in_destination(producer1_in_destination),
    .producer1_in_source(producer1_in_source),
    .producer1_in_tag(producer1_in_tag),
    .producer1_in_fragment(producer1_in_fragment),
    .producer1_in_last(producer1_in_last),
    .producer1_in_vc(producer1_in_vc),
    .producer1_in_data(producer1_in_data),
    .producer0_out_valid(producer0_out_valid),
    .producer0_out_ready(producer0_out_ready),
    .producer0_out_destination(producer0_out_destination),
    .producer0_out_source(producer0_out_source),
    .producer0_out_tag(producer0_out_tag),
    .producer0_out_fragment(producer0_out_fragment),
    .producer0_out_last(producer0_out_last),
    .producer0_out_vc(producer0_out_vc),
    .producer0_out_data(producer0_out_data),
    .producer1_out_valid(producer1_out_valid),
    .producer1_out_ready(producer1_out_ready),
    .producer1_out_destination(producer1_out_destination),
    .producer1_out_source(producer1_out_source),
    .producer1_out_tag(producer1_out_tag),
    .producer1_out_fragment(producer1_out_fragment),
    .producer1_out_last(producer1_out_last),
    .producer1_out_vc(producer1_out_vc),
    .producer1_out_data(producer1_out_data),
    .injection_protocol_error(injection_protocol_error),
    .ejection_protocol_error(ejection_protocol_error),
    .protocol_error(protocol_error)
  );

  task clear_inputs;
    begin
      producer0_in_valid = 16'b0;
      producer0_in_destination = 0;
      producer0_in_source = 0;
      producer0_in_tag = 0;
      producer0_in_fragment = 0;
      producer0_in_last = 16'b0;
      producer0_in_vc = 0;
      producer0_in_data = 0;
      producer1_in_valid = 16'b0;
      producer1_in_destination = 0;
      producer1_in_source = 0;
      producer1_in_tag = 0;
      producer1_in_fragment = 0;
      producer1_in_last = 16'b0;
      producer1_in_vc = 0;
      producer1_in_data = 0;
    end
  endtask

  task drive_p0;
    input integer endpoint;
    input [3:0] destination;
    input [3:0] source;
    input [7:0] tag;
    input [2:0] fragment;
    input last;
    input [1:0] vc;
    input [31:0] data;
    begin
      producer0_in_valid[endpoint] = 1'b1;
      producer0_in_destination[(endpoint * ENDPOINT_W) +: ENDPOINT_W] = destination;
      producer0_in_source[(endpoint * ENDPOINT_W) +: ENDPOINT_W] = source;
      producer0_in_tag[(endpoint * TAG_W) +: TAG_W] = tag;
      producer0_in_fragment[(endpoint * FRAGMENT_W) +: FRAGMENT_W] = fragment;
      producer0_in_last[endpoint] = last;
      producer0_in_vc[(endpoint * VC_W) +: VC_W] = vc;
      producer0_in_data[(endpoint * DATA_W) +: DATA_W] = data;
    end
  endtask

  task drive_p1;
    input integer endpoint;
    input [3:0] destination;
    input [3:0] source;
    input [7:0] tag;
    input [2:0] fragment;
    input last;
    input [1:0] vc;
    input [31:0] data;
    begin
      producer1_in_valid[endpoint] = 1'b1;
      producer1_in_destination[(endpoint * ENDPOINT_W) +: ENDPOINT_W] = destination;
      producer1_in_source[(endpoint * ENDPOINT_W) +: ENDPOINT_W] = source;
      producer1_in_tag[(endpoint * TAG_W) +: TAG_W] = tag;
      producer1_in_fragment[(endpoint * FRAGMENT_W) +: FRAGMENT_W] = fragment;
      producer1_in_last[endpoint] = last;
      producer1_in_vc[(endpoint * VC_W) +: VC_W] = vc;
      producer1_in_data[(endpoint * DATA_W) +: DATA_W] = data;
    end
  endtask

  task wait_idle;
    input integer cycles;
    integer idx;
    begin
      for (idx = 0; idx < cycles; idx = idx + 1)
        @(posedge clk);
    end
  endtask

  always @(posedge clk) begin
    integer endpoint;
    if (rst_n) begin
      cycle_count = cycle_count + 1;
      for (endpoint = 0; endpoint < 16; endpoint = endpoint + 1) begin
        if (producer0_out_valid[endpoint] && producer0_out_ready[endpoint]) begin
          delivered_p0 = delivered_p0 + 1;
          if (producer0_out_vc[(endpoint * VC_W) +: VC_W] !== 2'b00)
            $fatal(1, "producer0 observed wrong VC at endpoint %0d", endpoint);
          if (producer0_out_data[(endpoint * DATA_W) +: DATA_W] == 32'h0bad_c0de)
            seen_p0_a <= 1'b1;
          if (producer0_out_data[(endpoint * DATA_W) +: DATA_W] == 32'h1bad_b002)
            $fatal(1, "producer1 flit crossed into producer0 at endpoint %0d", endpoint);
        end
        if (producer1_out_valid[endpoint] && producer1_out_ready[endpoint]) begin
          delivered_p1 = delivered_p1 + 1;
          if (producer1_out_vc[(endpoint * VC_W) +: VC_W] !== 2'b01)
            $fatal(1, "producer1 observed wrong VC at endpoint %0d", endpoint);
          if (producer1_out_data[(endpoint * DATA_W) +: DATA_W] == 32'h1bad_b002)
            seen_p1_b <= 1'b1;
          if (producer1_out_data[(endpoint * DATA_W) +: DATA_W] == 32'h0bad_c0de)
            $fatal(1, "producer0 flit crossed into producer1 at endpoint %0d", endpoint);
        end
      end
    end
  end

  initial begin
    clear_inputs();
    repeat (3) @(posedge clk);
    @(negedge clk);
    rst_n = 1'b1;

    // Held grant: producer1 wins while stalled, producer0 arrives later, and
    // producer1 is still granted first once the endpoint is unstalled.
    force dut.mesh_endpoint_in_ready_w[0] = 1'b0;
    @(negedge clk);
    clear_inputs();
    drive_p1(0, 4'h5, 4'h0, 8'h11, 3'h0, 1'b1, 2'b01, 32'h1111_0001);
    #1;
    if (producer0_in_ready[0] !== 1'b0 || producer1_in_ready[0] !== 1'b0)
      $fatal(1, "stalled grant advertised ready");
    @(posedge clk);
    @(negedge clk);
    clear_inputs();
    drive_p0(0, 4'h5, 4'h0, 8'h12, 3'h0, 1'b1, 2'b00, 32'h0000_0002);
    drive_p1(0, 4'h5, 4'h0, 8'h11, 3'h0, 1'b1, 2'b01, 32'h1111_0001);
    #1;
    if (producer0_in_ready[0] !== 1'b0 || producer1_in_ready[0] !== 1'b0)
      $fatal(1, "held grant changed while stalled");
    release dut.mesh_endpoint_in_ready_w[0];
    @(posedge clk);
    @(negedge clk);
    clear_inputs();
    drive_p0(0, 4'h5, 4'h0, 8'h12, 3'h0, 1'b1, 2'b00, 32'h0000_0002);
    drive_p1(0, 4'h5, 4'h0, 8'h11, 3'h0, 1'b1, 2'b01, 32'h1111_0001);
    #1;
    if (producer1_in_ready[0] !== 1'b1 || producer0_in_ready[0] !== 1'b0)
      $fatal(1, "held grant did not preserve producer1 ownership");
    @(posedge clk);
    @(negedge clk);
    clear_inputs();
    drive_p0(0, 4'h5, 4'h0, 8'h12, 3'h0, 1'b1, 2'b00, 32'h0000_0002);
    #1;
    if (producer0_in_ready[0] !== 1'b1)
      $fatal(1, "producer0 did not receive the next grant");
    @(posedge clk);
    clear_inputs();
    wait_idle(20);

    // Demux + ready backpressure for VC0.
    producer0_out_ready[5] = 1'b0;
    producer1_out_ready[5] = 1'b1;
    force dut.mesh_endpoint_out_valid_w[5] = 1'b1;
    force dut.mesh_endpoint_out_destination_w[EP5_DEST_LSB +: ENDPOINT_W] = 4'h5;
    force dut.mesh_endpoint_out_source_w[EP5_DEST_LSB +: ENDPOINT_W] = 4'h2;
    force dut.mesh_endpoint_out_tag_w[EP5_TAG_LSB +: TAG_W] = 8'h55;
    force dut.mesh_endpoint_out_fragment_w[EP5_FRAGMENT_LSB +: FRAGMENT_W] = 3'h3;
    force dut.mesh_endpoint_out_last_w[5] = 1'b1;
    force dut.mesh_endpoint_out_vc_w[EP5_VC_LSB +: VC_W] = 2'b00;
    force dut.mesh_endpoint_out_data_w[EP5_DATA_LSB +: DATA_W] = 32'h00c0_ffee;
    #1;
    if (producer0_out_valid[5] !== 1'b1 || producer1_out_valid[5] !== 1'b0)
      $fatal(1, "VC0 ejection demuxed to the wrong producer");
    if (dut.mesh_endpoint_out_ready_w[5] !== 1'b0)
      $fatal(1, "VC0 backpressure did not propagate");
    producer0_out_ready[5] = 1'b1;
    #1;
    if (dut.mesh_endpoint_out_ready_w[5] !== 1'b1)
      $fatal(1, "VC0 path did not release when producer0 became ready");
    release dut.mesh_endpoint_out_valid_w[5];
    release dut.mesh_endpoint_out_destination_w[EP5_DEST_LSB +: ENDPOINT_W];
    release dut.mesh_endpoint_out_source_w[EP5_DEST_LSB +: ENDPOINT_W];
    release dut.mesh_endpoint_out_tag_w[EP5_TAG_LSB +: TAG_W];
    release dut.mesh_endpoint_out_fragment_w[EP5_FRAGMENT_LSB +: FRAGMENT_W];
    release dut.mesh_endpoint_out_last_w[5];
    release dut.mesh_endpoint_out_vc_w[EP5_VC_LSB +: VC_W];
    release dut.mesh_endpoint_out_data_w[EP5_DATA_LSB +: DATA_W];
    wait_idle(2);

    // Demux + ready backpressure for VC1.
    producer0_out_ready[5] = 1'b1;
    producer1_out_ready[5] = 1'b0;
    force dut.mesh_endpoint_out_valid_w[5] = 1'b1;
    force dut.mesh_endpoint_out_destination_w[EP5_DEST_LSB +: ENDPOINT_W] = 4'h5;
    force dut.mesh_endpoint_out_source_w[EP5_DEST_LSB +: ENDPOINT_W] = 4'h3;
    force dut.mesh_endpoint_out_tag_w[EP5_TAG_LSB +: TAG_W] = 8'h56;
    force dut.mesh_endpoint_out_fragment_w[EP5_FRAGMENT_LSB +: FRAGMENT_W] = 3'h4;
    force dut.mesh_endpoint_out_last_w[5] = 1'b1;
    force dut.mesh_endpoint_out_vc_w[EP5_VC_LSB +: VC_W] = 2'b01;
    force dut.mesh_endpoint_out_data_w[EP5_DATA_LSB +: DATA_W] = 32'h0dd0_0dd0;
    #1;
    if (producer0_out_valid[5] !== 1'b0 || producer1_out_valid[5] !== 1'b1)
      $fatal(1, "VC1 ejection demuxed to the wrong producer");
    if (dut.mesh_endpoint_out_ready_w[5] !== 1'b0)
      $fatal(1, "VC1 backpressure did not propagate");
    producer1_out_ready[5] = 1'b1;
    #1;
    if (dut.mesh_endpoint_out_ready_w[5] !== 1'b1)
      $fatal(1, "VC1 path did not release when producer1 became ready");
    release dut.mesh_endpoint_out_valid_w[5];
    release dut.mesh_endpoint_out_destination_w[EP5_DEST_LSB +: ENDPOINT_W];
    release dut.mesh_endpoint_out_source_w[EP5_DEST_LSB +: ENDPOINT_W];
    release dut.mesh_endpoint_out_tag_w[EP5_TAG_LSB +: TAG_W];
    release dut.mesh_endpoint_out_fragment_w[EP5_FRAGMENT_LSB +: FRAGMENT_W];
    release dut.mesh_endpoint_out_last_w[5];
    release dut.mesh_endpoint_out_vc_w[EP5_VC_LSB +: VC_W];
    release dut.mesh_endpoint_out_data_w[EP5_DATA_LSB +: DATA_W];
    producer0_out_ready = 16'hffff;
    producer1_out_ready = 16'hffff;
    wait_idle(20);

    // Real mesh traffic: one VC0 flit and one VC1 flit must both survive and
    // must never cross-deliver.
    delivered_p0 = 0;
    delivered_p1 = 0;
    seen_p0_a = 1'b0;
    seen_p1_b = 1'b0;
    @(negedge clk);
    clear_inputs();
    drive_p0(2, 4'hb, 4'h2, 8'h31, 3'h1, 1'b1, 2'b00, 32'h0bad_c0de);
    drive_p1(3, 4'ha, 4'h3, 8'h32, 3'h2, 1'b1, 2'b01, 32'h1bad_b002);
    #1;
    if (producer0_in_ready[2] !== 1'b1 || producer1_in_ready[3] !== 1'b1)
      $fatal(1, "mesh did not accept independent producer flits");
    @(posedge clk);
    clear_inputs();
    while ((!seen_p0_a || !seen_p1_b) && cycle_count < 200) begin
      @(posedge clk);
    end
    if (!seen_p0_a || !seen_p1_b)
      $fatal(1, "timed out waiting for conserved mesh deliveries");
    if (delivered_p0 != 1 || delivered_p1 != 1)
      $fatal(1, "unexpected delivered counts p0=%0d p1=%0d", delivered_p0, delivered_p1);
    wait_idle(10);

    // Bad producer VC is dropped, acknowledged, and sticks an injection error.
    @(negedge clk);
    clear_inputs();
    drive_p0(1, 4'h6, 4'h1, 8'h41, 3'h0, 1'b1, 2'b10, 32'hdead_0000);
    #1;
    if (producer0_in_ready[1] !== 1'b1)
      $fatal(1, "bad producer VC did not fail closed");
    @(posedge clk);
    @(negedge clk);
    if (injection_protocol_error[1] !== 1'b1 || protocol_error !== 1'b1)
      $fatal(1, "bad producer VC did not stick protocol_error");
    clear_inputs();

    // Bad ejected VC is dropped, never cross-delivered, and sticks an error.
    force dut.mesh_endpoint_out_valid_w[6] = 1'b1;
    force dut.mesh_endpoint_out_destination_w[EP6_DEST_LSB +: ENDPOINT_W] = 4'h6;
    force dut.mesh_endpoint_out_source_w[EP6_DEST_LSB +: ENDPOINT_W] = 4'h4;
    force dut.mesh_endpoint_out_tag_w[EP6_TAG_LSB +: TAG_W] = 8'h61;
    force dut.mesh_endpoint_out_fragment_w[EP6_FRAGMENT_LSB +: FRAGMENT_W] = 3'h1;
    force dut.mesh_endpoint_out_last_w[6] = 1'b1;
    force dut.mesh_endpoint_out_vc_w[EP6_VC_LSB +: VC_W] = 2'b10;
    force dut.mesh_endpoint_out_data_w[EP6_DATA_LSB +: DATA_W] = 32'hfeed_6000;
    #1;
    if (producer0_out_valid[6] !== 1'b0 || producer1_out_valid[6] !== 1'b0)
      $fatal(1, "unexpected ejected VC reached a producer");
    if (dut.mesh_endpoint_out_ready_w[6] !== 1'b1)
      $fatal(1, "unexpected ejected VC did not drain fail-closed");
    @(posedge clk);
    @(negedge clk);
    if (ejection_protocol_error[6] !== 1'b1)
      $fatal(1, "unexpected ejected VC did not stick ejection error");
    release dut.mesh_endpoint_out_valid_w[6];
    release dut.mesh_endpoint_out_destination_w[EP6_DEST_LSB +: ENDPOINT_W];
    release dut.mesh_endpoint_out_source_w[EP6_DEST_LSB +: ENDPOINT_W];
    release dut.mesh_endpoint_out_tag_w[EP6_TAG_LSB +: TAG_W];
    release dut.mesh_endpoint_out_fragment_w[EP6_FRAGMENT_LSB +: FRAGMENT_W];
    release dut.mesh_endpoint_out_last_w[6];
    release dut.mesh_endpoint_out_vc_w[EP6_VC_LSB +: VC_W];
    release dut.mesh_endpoint_out_data_w[EP6_DATA_LSB +: DATA_W];

    $display("PASS shared transport arbitration, demux, conservation, and failure handling");
    $finish;
  end
endmodule
