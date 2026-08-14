`timescale 1ns/1ps

module noc_sram_packet_endpoint_tb;
  localparam integer DATA_W = 256;
  localparam integer ADDR_W = 16;

  reg clk = 1'b0;
  reg rst_n = 1'b0;
  integer cycle = 0;

  reg tx_desc_valid = 1'b0;
  wire tx_desc_ready;
  reg [3:0] tx_desc_destination = 0;
  reg [1:0] tx_desc_vc = 0;
  reg [7:0] tx_desc_tag = 0;
  reg [ADDR_W-1:0] tx_desc_base_addr = 0;
  reg [3:0] tx_desc_flit_count = 0;
  wire tx_mem_req_valid;
  reg tx_mem_req_ready = 1'b1;
  wire [ADDR_W-1:0] tx_mem_req_addr;
  reg tx_mem_rsp_valid = 1'b0;
  wire tx_mem_rsp_ready;
  reg [DATA_W-1:0] tx_mem_rsp_data = 0;
  wire tx_flit_valid;
  reg tx_flit_ready = 1'b0;
  wire [3:0] tx_flit_source;
  wire [3:0] tx_flit_destination;
  wire [1:0] tx_flit_vc;
  wire [7:0] tx_flit_tag;
  wire [2:0] tx_flit_fragment;
  wire tx_flit_last;
  wire [DATA_W-1:0] tx_flit_data;

  reg rx_desc_valid = 1'b0;
  wire rx_desc_ready;
  reg [3:0] rx_desc_source = 0;
  reg [1:0] rx_desc_vc = 0;
  reg [7:0] rx_desc_tag = 0;
  reg [ADDR_W-1:0] rx_desc_base_addr = 0;
  reg [3:0] rx_desc_flit_count = 0;
  reg rx_flit_valid = 1'b0;
  wire rx_flit_ready;
  reg [3:0] rx_flit_source = 0;
  reg [1:0] rx_flit_vc = 0;
  reg [7:0] rx_flit_tag = 0;
  reg [2:0] rx_flit_fragment = 0;
  reg rx_flit_last = 1'b0;
  reg [DATA_W-1:0] rx_flit_data = 0;
  wire rx_mem_write_valid;
  reg rx_mem_write_ready = 1'b0;
  wire [ADDR_W-1:0] rx_mem_write_addr;
  wire [DATA_W-1:0] rx_mem_write_data;
  wire rx_completion_valid;
  reg rx_completion_ready = 1'b0;
  wire [3:0] rx_completion_source;
  wire [1:0] rx_completion_vc;
  wire [7:0] rx_completion_tag;
  wire protocol_error;

  reg [ADDR_W-1:0] pending_addr [0:31];
  integer pending_rd = 0;
  integer pending_wr = 0;
  integer pending_count = 0;
  integer request_count = 0;
  integer tx_count = 0;
  integer write_count = 0;
  integer completion_count = 0;
  reg held_valid = 1'b0;
  reg [278:0] held_flit = 0;

  noc_sram_packet_endpoint #(
    .DATA_W(DATA_W),
    .ADDR_W(ADDR_W),
    .TX_DESC_DEPTH(4),
    .TX_OUTSTANDING(8),
    .RX_CONTEXTS(4),
    .LOCAL_ENDPOINT_ID(2)
  ) dut (
    .clk(clk), .rst_n(rst_n),
    .tx_desc_valid(tx_desc_valid), .tx_desc_ready(tx_desc_ready),
    .tx_desc_destination(tx_desc_destination), .tx_desc_vc(tx_desc_vc),
    .tx_desc_tag(tx_desc_tag), .tx_desc_base_addr(tx_desc_base_addr),
    .tx_desc_flit_count(tx_desc_flit_count),
    .tx_mem_req_valid(tx_mem_req_valid), .tx_mem_req_ready(tx_mem_req_ready),
    .tx_mem_req_addr(tx_mem_req_addr), .tx_mem_rsp_valid(tx_mem_rsp_valid),
    .tx_mem_rsp_ready(tx_mem_rsp_ready), .tx_mem_rsp_data(tx_mem_rsp_data),
    .tx_flit_valid(tx_flit_valid), .tx_flit_ready(tx_flit_ready),
    .tx_flit_source(tx_flit_source), .tx_flit_destination(tx_flit_destination),
    .tx_flit_vc(tx_flit_vc), .tx_flit_tag(tx_flit_tag),
    .tx_flit_fragment(tx_flit_fragment), .tx_flit_last(tx_flit_last),
    .tx_flit_data(tx_flit_data),
    .rx_desc_valid(rx_desc_valid), .rx_desc_ready(rx_desc_ready),
    .rx_desc_source(rx_desc_source), .rx_desc_vc(rx_desc_vc),
    .rx_desc_tag(rx_desc_tag), .rx_desc_base_addr(rx_desc_base_addr),
    .rx_desc_flit_count(rx_desc_flit_count),
    .rx_flit_valid(rx_flit_valid), .rx_flit_ready(rx_flit_ready),
    .rx_flit_source(rx_flit_source), .rx_flit_vc(rx_flit_vc),
    .rx_flit_tag(rx_flit_tag), .rx_flit_fragment(rx_flit_fragment),
    .rx_flit_last(rx_flit_last), .rx_flit_data(rx_flit_data),
    .rx_mem_write_valid(rx_mem_write_valid),
    .rx_mem_write_ready(rx_mem_write_ready),
    .rx_mem_write_addr(rx_mem_write_addr), .rx_mem_write_data(rx_mem_write_data),
    .rx_completion_valid(rx_completion_valid),
    .rx_completion_ready(rx_completion_ready),
    .rx_completion_source(rx_completion_source),
    .rx_completion_vc(rx_completion_vc), .rx_completion_tag(rx_completion_tag),
    .protocol_error(protocol_error)
  );

  always #5 clk = ~clk;

  function [DATA_W-1:0] memory_data;
    input [ADDR_W-1:0] addr;
    begin
      memory_data = {{(DATA_W-32){1'b0}}, 16'hcafe, addr};
    end
  endfunction

  task send_tx_descriptor;
    input [3:0] destination;
    input [1:0] vc;
    input [7:0] tag;
    input [ADDR_W-1:0] base_addr;
    input [3:0] flit_count;
    begin
      @(negedge clk);
      tx_desc_valid = 1'b1;
      tx_desc_destination = destination;
      tx_desc_vc = vc;
      tx_desc_tag = tag;
      tx_desc_base_addr = base_addr;
      tx_desc_flit_count = flit_count;
      @(posedge clk);
      while (!tx_desc_ready) @(posedge clk);
      @(negedge clk);
      tx_desc_valid = 1'b0;
    end
  endtask

  task send_rx_descriptor;
    input [3:0] source;
    input [1:0] vc;
    input [7:0] tag;
    input [ADDR_W-1:0] base_addr;
    input [3:0] flit_count;
    begin
      @(negedge clk);
      rx_desc_valid = 1'b1;
      rx_desc_source = source;
      rx_desc_vc = vc;
      rx_desc_tag = tag;
      rx_desc_base_addr = base_addr;
      rx_desc_flit_count = flit_count;
      @(posedge clk);
      while (!rx_desc_ready) @(posedge clk);
      @(negedge clk);
      rx_desc_valid = 1'b0;
    end
  endtask

  task send_rx_flit;
    input [3:0] source;
    input [1:0] vc;
    input [7:0] tag;
    input [2:0] fragment;
    input last;
    input [31:0] data;
    begin
      @(negedge clk);
      rx_flit_valid = 1'b1;
      rx_flit_source = source;
      rx_flit_vc = vc;
      rx_flit_tag = tag;
      rx_flit_fragment = fragment;
      rx_flit_last = last;
      rx_flit_data = {{(DATA_W-32){1'b0}}, data};
      @(posedge clk);
      while (!rx_flit_ready) @(posedge clk);
      @(negedge clk);
      rx_flit_valid = 1'b0;
    end
  endtask

  always @(posedge clk) begin
    if (!rst_n) begin
      cycle <= 0;
      pending_rd <= 0;
      pending_wr <= 0;
      pending_count <= 0;
      tx_mem_rsp_valid <= 1'b0;
      request_count <= 0;
    end else begin
      cycle <= cycle + 1;
      tx_mem_req_ready <= ((cycle % 7) != 3);
      tx_flit_ready <= ((cycle % 5) != 2);
      rx_mem_write_ready <= ((cycle % 4) != 1);

      if (tx_mem_req_valid && tx_mem_req_ready) begin
        pending_addr[pending_wr] <= tx_mem_req_addr;
        pending_wr <= (pending_wr + 1) % 32;
        request_count <= request_count + 1;
      end
      if (tx_mem_rsp_valid && tx_mem_rsp_ready) begin
        tx_mem_rsp_valid <= 1'b0;
      end
      if ((!tx_mem_rsp_valid || tx_mem_rsp_ready) && pending_count != 0) begin
        tx_mem_rsp_valid <= 1'b1;
        tx_mem_rsp_data <= memory_data(pending_addr[pending_rd]);
        pending_rd <= (pending_rd + 1) % 32;
      end
      case ({tx_mem_req_valid && tx_mem_req_ready,
             (!tx_mem_rsp_valid || tx_mem_rsp_ready) && pending_count != 0})
        2'b10: pending_count <= pending_count + 1;
        2'b01: pending_count <= pending_count - 1;
        default: pending_count <= pending_count;
      endcase
    end
  end

  always @(posedge clk) begin
    if (rst_n && tx_flit_valid && !tx_flit_ready) begin
      if (held_valid && held_flit !== {tx_flit_destination, tx_flit_vc, tx_flit_tag,
                                      tx_flit_fragment, tx_flit_last, tx_flit_data}) begin
        $fatal(1, "TX flit changed under backpressure");
      end
      held_valid <= 1'b1;
      held_flit <= {tx_flit_destination, tx_flit_vc, tx_flit_tag,
                    tx_flit_fragment, tx_flit_last, tx_flit_data};
    end else begin
      held_valid <= 1'b0;
    end

    if (rst_n && tx_flit_valid && tx_flit_ready) begin
      $display("TXTRACE %0d %0d %0d %0d %0d %0d",
               tx_flit_source, tx_flit_destination, tx_flit_vc,
               tx_flit_tag, tx_flit_fragment, tx_flit_last);
      if (tx_flit_source !== 2) $fatal(1, "wrong TX source");
      if (tx_count < 8) begin
        if (tx_flit_destination !== 5 || tx_flit_vc !== 1 || tx_flit_tag !== 8'ha1)
          $fatal(1, "wrong first TX packet metadata");
        if (tx_flit_fragment !== tx_count[2:0] || tx_flit_last !== (tx_count == 7))
          $fatal(1, "wrong first TX packet framing");
        if (tx_flit_data !== memory_data(16'h0100 + tx_count * 32))
          $fatal(1, "wrong first TX packet data");
      end else begin
        if (tx_flit_destination !== 9 || tx_flit_vc !== 2 || tx_flit_tag !== 8'hb2)
          $fatal(1, "wrong second TX packet metadata");
        if (tx_flit_fragment !== (tx_count - 8) || tx_flit_last !== (tx_count == 9))
          $fatal(1, "wrong second TX packet framing");
        if (tx_flit_data !== memory_data(16'h0300 + (tx_count - 8) * 32))
          $fatal(1, "wrong second TX packet data");
      end
      tx_count <= tx_count + 1;
    end

    if (rst_n && rx_mem_write_valid && rx_mem_write_ready) begin
      case (write_count)
        0: if (rx_mem_write_addr !== 16'h0500 || rx_mem_write_data[31:0] !== 32'h3000)
             $fatal(1, "wrong RX write 0");
        1: if (rx_mem_write_addr !== 16'h0700 || rx_mem_write_data[31:0] !== 32'h7000)
             $fatal(1, "wrong RX write 1");
        2: if (rx_mem_write_addr !== 16'h0520 || rx_mem_write_data[31:0] !== 32'h3001)
             $fatal(1, "wrong RX write 2");
        3: if (rx_mem_write_addr !== 16'h0720 || rx_mem_write_data[31:0] !== 32'h7001)
             $fatal(1, "wrong RX write 3");
        4: if (rx_mem_write_addr !== 16'h0540 || rx_mem_write_data[31:0] !== 32'h3002)
             $fatal(1, "wrong RX write 4");
        default: $fatal(1, "unexpected RX write");
      endcase
      write_count <= write_count + 1;
    end

    if (rst_n && rx_completion_valid && rx_completion_ready) begin
      if (completion_count == 0) begin
        if (rx_completion_source !== 7 || rx_completion_vc !== 2 || rx_completion_tag !== 8'h22)
          $fatal(1, "wrong first RX completion");
      end else if (completion_count == 1) begin
        if (rx_completion_source !== 3 || rx_completion_vc !== 1 || rx_completion_tag !== 8'h11)
          $fatal(1, "wrong second RX completion");
      end else begin
        $fatal(1, "unexpected RX completion");
      end
      completion_count <= completion_count + 1;
    end
  end

  initial begin
    #200000;
    $fatal(1, "simulation timeout");
  end

  initial begin
    repeat (3) @(negedge clk);
    rst_n = 1'b1;

    fork
      begin
        send_tx_descriptor(5, 1, 8'ha1, 16'h0100, 8);
        send_tx_descriptor(9, 2, 8'hb2, 16'h0300, 2);
      end
      begin
        send_rx_descriptor(3, 1, 8'h11, 16'h0500, 3);
        send_rx_descriptor(7, 2, 8'h22, 16'h0700, 2);
        send_rx_flit(3, 1, 8'h11, 0, 0, 32'h3000);
        send_rx_flit(7, 2, 8'h22, 0, 0, 32'h7000);
        send_rx_flit(3, 1, 8'h11, 1, 0, 32'h3001);
        send_rx_flit(7, 2, 8'h22, 1, 1, 32'h7001);
        while (!rx_completion_valid) @(negedge clk);
        repeat (3) @(negedge clk);
        rx_completion_ready = 1'b1;
        send_rx_flit(3, 1, 8'h11, 2, 1, 32'h3002);
      end
    join

    while (tx_count != 10 || completion_count != 2) @(negedge clk);
    repeat (3) @(negedge clk);
    if (request_count !== 10 || write_count !== 5 || protocol_error)
      $fatal(1, "wrong final counts or protocol_error");

    // An unmatched packet must be consumed to avoid deadlock and reported.
    send_rx_flit(15, 3, 8'hee, 0, 1, 32'hdeadbeef);
    if (!protocol_error)
      $fatal(1, "unmatched RX packet did not set protocol_error");

    $display("PASS noc_sram_packet_endpoint requests=%0d tx=%0d writes=%0d completions=%0d",
             request_count, tx_count, write_count, completion_count);
    $finish;
  end
endmodule
