`timescale 1ns/1ps

// Direct exact roundtrip for the four-bank frontier.  Each source presents
// the 21 packet / 167 flit representation of one 128-beat group.  The test
// keeps only two logical slots per source, lets the fabric arbitrate both
// writes and reads under bank contention, and checks every returned word.
module local_reducer_aggregate_stats_once_exact_shared_root_storage_fabric_b4_tb;
  localparam integer SOURCE_COUNT = 15;
  localparam integer PHYSICAL_BANKS = 4;
  localparam integer DATA_W = 256;
  localparam integer ADDR_W = 4;
  localparam integer PACKET_COUNT = 21;
  localparam integer FLITS_PER_SOURCE = 167;
  localparam integer CANONICAL_BEATS_PER_SOURCE = 128;
  localparam integer TOTAL_CANONICAL_BEATS = SOURCE_COUNT * CANONICAL_BEATS_PER_SOURCE;
  localparam integer TOTAL_FLITS = SOURCE_COUNT * FLITS_PER_SOURCE;
  localparam integer TOTAL_PACKETS = SOURCE_COUNT * PACKET_COUNT;
  localparam integer TIMEOUT = 20000;

  reg clk = 1'b0;
  reg rst_n = 1'b0;
  integer cycle = 0;
  always #5 clk = ~clk;

  reg [SOURCE_COUNT-1:0] write_valid;
  wire [SOURCE_COUNT-1:0] write_ready;
  reg [SOURCE_COUNT*ADDR_W-1:0] write_addr;
  reg [SOURCE_COUNT*DATA_W-1:0] write_data;
  reg [SOURCE_COUNT-1:0] read_req_valid;
  wire [SOURCE_COUNT-1:0] read_req_ready;
  reg [SOURCE_COUNT*ADDR_W-1:0] read_req_addr;
  wire [SOURCE_COUNT-1:0] read_rsp_valid;
  reg [SOURCE_COUNT-1:0] read_rsp_ready;
  wire [SOURCE_COUNT*ADDR_W-1:0] read_rsp_addr;
  wire [SOURCE_COUNT*DATA_W-1:0] read_rsp_data;
  wire protocol_error;

  local_reducer_aggregate_stats_once_exact_shared_root_storage_fabric #(
    .DATA_W(DATA_W), .SOURCE_COUNT(SOURCE_COUNT),
    .PHYSICAL_BANKS(PHYSICAL_BANKS), .ADDR_W(ADDR_W)
  ) fabric (
    .clk(clk), .rst_n(rst_n),
    .write_valid(write_valid), .write_ready(write_ready),
    .write_addr(write_addr), .write_data(write_data),
    .read_req_valid(read_req_valid), .read_req_ready(read_req_ready),
    .read_req_addr(read_req_addr), .read_rsp_valid(read_rsp_valid),
    .read_rsp_ready(read_rsp_ready), .read_rsp_addr(read_rsp_addr),
    .read_rsp_data(read_rsp_data), .protocol_error(protocol_error)
  );

  integer next_write_packet [0:SOURCE_COUNT-1];
  integer write_packet [0:SOURCE_COUNT-1];
  integer write_word [0:SOURCE_COUNT-1];
  integer write_active [0:SOURCE_COUNT-1];
  integer next_read_packet [0:SOURCE_COUNT-1];
  integer read_packet [0:SOURCE_COUNT-1];
  integer read_word [0:SOURCE_COUNT-1];
  integer read_response_count [0:SOURCE_COUNT-1];
  integer read_active [0:SOURCE_COUNT-1];
  integer slot_busy [0:SOURCE_COUNT-1];
  integer slot_packet [0:SOURCE_COUNT-1][0:1];
  integer packet_ready [0:SOURCE_COUNT-1][0:PACKET_COUNT-1];

  integer write_flit_count = 0;
  integer write_packet_count = 0;
  integer read_request_count = 0;
  integer read_flit_count = 0;
  integer read_packet_count = 0;
  integer exact_errors = 0;
  integer overwrite_errors = 0;
  integer timeout_error = 0;
  integer i;
  integer write_fire_now;
  integer write_packet_fire_now;
  integer read_request_fire_now;
  integer read_response_fire_now;
  integer read_packet_fire_now;
  integer count_i;

  always @* begin
    write_fire_now = 0;
    write_packet_fire_now = 0;
    read_request_fire_now = 0;
    read_response_fire_now = 0;
    read_packet_fire_now = 0;
    for (count_i = 0; count_i < SOURCE_COUNT; count_i = count_i + 1) begin
      if (write_valid[count_i] && write_ready[count_i]) begin
        write_fire_now = write_fire_now + 1;
        if (write_word[count_i] + 1 == packet_words(write_packet[count_i]))
          write_packet_fire_now = write_packet_fire_now + 1;
      end
      if (read_req_valid[count_i] && read_req_ready[count_i])
        read_request_fire_now = read_request_fire_now + 1;
      if (read_rsp_valid[count_i] && read_rsp_ready[count_i]) begin
        read_response_fire_now = read_response_fire_now + 1;
        if (read_response_count[count_i] + 1 ==
            packet_words(read_packet[count_i]))
          read_packet_fire_now = read_packet_fire_now + 1;
      end
    end
  end

  function automatic [DATA_W-1:0] make_flit;
    input integer source_id;
    input integer packet_id;
    input integer word_id;
    integer global_flit;
    begin
      global_flit = packet_id * 8 + word_id;
      make_flit = {DATA_W{1'b0}};
      make_flit[15:0] = 16'hb400 + source_id;
      make_flit[20:16] = packet_id[4:0];
      make_flit[28:21] = word_id[7:0];
      make_flit[60:29] = 32'h4100_0000 + source_id * 32'h101 +
        global_flit * 32'h13;
      make_flit[92:61] = 32'h5200_0000 + source_id * 32'h71 +
        packet_id * 32'h17 + word_id;
      make_flit[124:93] = 32'h6300_0000 + global_flit * 32'h1d;
      make_flit[156:125] = 32'h7400_0000 + source_id * 32'h23 + word_id;
      make_flit[188:157] = 32'h8500_0000 + packet_id * 32'h2b;
      make_flit[220:189] = 32'h9600_0000 + source_id * 32'h31 +
        global_flit;
      make_flit[252:221] = 32'ha700_0000 + packet_id * 32'h3d + word_id;
      make_flit[255:253] = 3'b101;
    end
  endfunction

  function automatic integer packet_words;
    input integer packet_id;
    begin
      packet_words = (packet_id == PACKET_COUNT - 1) ? 7 : 8;
    end
  endfunction

  always @* begin
    write_valid = {SOURCE_COUNT{1'b0}};
    write_addr = {SOURCE_COUNT*ADDR_W{1'b0}};
    write_data = {SOURCE_COUNT*DATA_W{1'b0}};
    read_req_valid = {SOURCE_COUNT{1'b0}};
    read_req_addr = {SOURCE_COUNT*ADDR_W{1'b0}};
    read_rsp_ready = {SOURCE_COUNT{1'b0}};
    for (i = 0; i < SOURCE_COUNT; i = i + 1) begin
      write_valid[i] = write_active[i];
      write_addr[i*ADDR_W +: ADDR_W] =
        {write_packet[i][0], write_word[i][2:0]};
      write_data[i*DATA_W +: DATA_W] =
        make_flit(i, write_packet[i], write_word[i]);
      read_req_valid[i] = read_active[i] &&
        (read_word[i] < packet_words(read_packet[i]));
      read_req_addr[i*ADDR_W +: ADDR_W] =
        {read_packet[i][0], read_word[i][2:0]};
      // Deliberate, source-dependent response backpressure.
      read_rsp_ready[i] = ((cycle + i * 5) % 17 != 4) &&
        ((cycle + i * 3) % 11 != 7);
    end
  end

  always @(posedge clk) begin
    if (!rst_n) begin
      cycle <= 0;
      write_flit_count <= 0;
      write_packet_count <= 0;
      read_request_count <= 0;
      read_flit_count <= 0;
      read_packet_count <= 0;
      exact_errors <= 0;
      overwrite_errors <= 0;
      timeout_error <= 0;
      for (i = 0; i < SOURCE_COUNT; i = i + 1) begin
        next_write_packet[i] <= 0;
        write_packet[i] <= 0;
        write_word[i] <= 0;
        write_active[i] <= 0;
        next_read_packet[i] <= 0;
        read_packet[i] <= 0;
        read_word[i] <= 0;
        read_response_count[i] <= 0;
        read_active[i] <= 0;
        slot_busy[i] <= 0;
        slot_packet[i][0] <= -1;
        slot_packet[i][1] <= -1;
        for (integer p = 0; p < PACKET_COUNT; p = p + 1)
          packet_ready[i][p] <= 0;
      end
    end else begin
      cycle <= cycle + 1;
      write_flit_count <= write_flit_count + write_fire_now;
      write_packet_count <= write_packet_count + write_packet_fire_now;
      read_request_count <= read_request_count + read_request_fire_now;
      read_flit_count <= read_flit_count + read_response_fire_now;
      read_packet_count <= read_packet_count + read_packet_fire_now;
      if (cycle >= TIMEOUT)
        timeout_error <= 1;

      for (i = 0; i < SOURCE_COUNT; i = i + 1) begin
        if (!write_active[i] && next_write_packet[i] < PACKET_COUNT &&
            !slot_busy[i][next_write_packet[i][0]]) begin
          write_active[i] <= 1;
          write_packet[i] <= next_write_packet[i];
          write_word[i] <= 0;
          slot_busy[i][next_write_packet[i][0]] <= 1;
          slot_packet[i][next_write_packet[i][0]] <= next_write_packet[i];
        end

        if (!read_active[i] && packet_ready[i][next_read_packet[i]]) begin
          read_active[i] <= 1;
          read_packet[i] <= next_read_packet[i];
          read_word[i] <= 0;
          read_response_count[i] <= 0;
        end

        if (write_valid[i] && write_ready[i]) begin
          if (!slot_busy[i][write_packet[i][0]] ||
              slot_packet[i][write_packet[i][0]] != write_packet[i])
            overwrite_errors <= overwrite_errors + 1;
          if (write_word[i] + 1 == packet_words(write_packet[i])) begin
            packet_ready[i][write_packet[i]] <= 1;
            next_write_packet[i] <= write_packet[i] + 1;
            write_active[i] <= 0;
          end else begin
            write_word[i] <= write_word[i] + 1;
          end
        end

        if (read_req_valid[i] && read_req_ready[i]) begin
          read_word[i] <= read_word[i] + 1;
        end

        if (read_rsp_valid[i] && read_rsp_ready[i]) begin
          if (read_rsp_addr[i*ADDR_W +: ADDR_W] !==
              {read_packet[i][0], read_response_count[i][2:0]})
            exact_errors <= exact_errors + 1;
          if (read_rsp_data[i*DATA_W +: DATA_W] !==
              make_flit(i, read_packet[i], read_response_count[i]))
            exact_errors <= exact_errors + 1;
          if (read_response_count[i] + 1 == packet_words(read_packet[i])) begin
            packet_ready[i][read_packet[i]] <= 0;
            slot_busy[i][read_packet[i][0]] <= 0;
            next_read_packet[i] <= read_packet[i] + 1;
            read_active[i] <= 0;
          end else begin
            read_response_count[i] <= read_response_count[i] + 1;
          end
        end
      end
    end
  end

  integer setup_i;
  integer done_i;
  integer all_done;
  initial begin
    repeat (5) @(posedge clk);
    rst_n = 1'b1;
    @(posedge clk);
    for (setup_i = 0; setup_i < SOURCE_COUNT; setup_i = setup_i + 1)
      write_active[setup_i] = 1;

    while (1) begin
      @(posedge clk);
      all_done = 1;
      for (done_i = 0; done_i < SOURCE_COUNT; done_i = done_i + 1)
        if (next_read_packet[done_i] != PACKET_COUNT)
          all_done = 0;
      if (all_done)
        break;
      if (timeout_error)
        begin
          for (done_i = 0; done_i < SOURCE_COUNT; done_i = done_i + 1)
            $display("TIMEOUT source=%0d next_write=%0d write_active=%0d write_word=%0d next_read=%0d read_active=%0d read_word=%0d responses=%0d slots=%0d ready0=%0d ready1=%0d",
              done_i, next_write_packet[done_i], write_active[done_i],
              write_word[done_i], next_read_packet[done_i],
              read_active[done_i], read_word[done_i],
              read_response_count[done_i], slot_busy[done_i],
              packet_ready[done_i][0], packet_ready[done_i][1]);
          $fatal(1, "B4 storage fabric timeout cycle=%0d writes=%0d reads=%0d",
            cycle, write_flit_count, read_flit_count);
        end
    end
    repeat (5) @(posedge clk);
    if (protocol_error || exact_errors != 0 || overwrite_errors != 0 ||
        write_flit_count != TOTAL_FLITS || read_flit_count != TOTAL_FLITS ||
        write_packet_count != TOTAL_PACKETS || read_packet_count != TOTAL_PACKETS ||
        read_request_count != TOTAL_FLITS) begin
      $fatal(1, "B4 storage failed canonical_beats=%0d/%0d writes=%0d/%0d reads=%0d/%0d packets=%0d/%0d requests=%0d/%0d exact=%0d overwrite=%0d protocol=%b",
        TOTAL_CANONICAL_BEATS, TOTAL_CANONICAL_BEATS,
        write_flit_count, TOTAL_FLITS, read_flit_count, TOTAL_FLITS,
        write_packet_count, TOTAL_PACKETS, read_request_count, TOTAL_FLITS,
        exact_errors, overwrite_errors, protocol_error);
    end
    $display("PASS shared_root_storage_b4 canonical_beats=%0d flits=%0d packets=%0d exact_outputs=%0d overwrite_errors=%0d independent_backpressure=1",
      TOTAL_CANONICAL_BEATS, read_flit_count, read_packet_count,
      read_flit_count, overwrite_errors);
    $finish;
  end
endmodule
