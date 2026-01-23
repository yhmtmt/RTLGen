// Shared AXI-Lite host tasks for RTL testbenches.

task axi_lite_write(input [31:0] addr, input [31:0] data);
  begin
    @(posedge clk);
    s_axi_awaddr <= addr;
    s_axi_awvalid <= 1'b1;
    s_axi_wdata <= data;
    s_axi_wstrb <= 4'hF;
    s_axi_wvalid <= 1'b1;
    s_axi_bready <= 1'b1;
    wait (s_axi_awready && s_axi_wready);
    @(posedge clk);
    s_axi_awvalid <= 1'b0;
    s_axi_wvalid <= 1'b0;
    wait (s_axi_bvalid);
    @(posedge clk);
    s_axi_bready <= 1'b0;
  end
endtask

task axi_lite_read(input [31:0] addr, output [31:0] data);
  begin
    @(posedge clk);
    s_axi_araddr <= addr;
    s_axi_arvalid <= 1'b1;
    s_axi_rready <= 1'b1;
    wait (s_axi_arready);
    @(posedge clk);
    s_axi_arvalid <= 1'b0;
    wait (s_axi_rvalid);
    data = s_axi_rdata;
    @(posedge clk);
    s_axi_rready <= 1'b0;
  end
endtask

task host_init_mmio(
  input [31:0] cq_base_lo,
  input [31:0] cq_base_hi,
  input [31:0] cq_size,
  input [31:0] irq_enable
);
  begin
    axi_lite_write(OFF_CQ_BASE_LO, cq_base_lo);
    axi_lite_write(OFF_CQ_BASE_HI, cq_base_hi);
    axi_lite_write(OFF_CQ_SIZE, cq_size);
    axi_lite_write(OFF_IRQ_ENABLE, irq_enable);
  end
endtask

task host_submit_cq(input [31:0] tail_bytes);
  begin
    axi_lite_write(OFF_CQ_TAIL, tail_bytes);
    axi_lite_write(OFF_DOORBELL, 32'h0000_0001);
  end
endtask

task host_wait_irq(input integer max_iters, input [31:0] mask, output [31:0] irq_status);
  begin
    irq_status = 0;
    begin : wait_irq
      integer t;
      for (t = 0; t < max_iters; t = t + 1) begin
        axi_lite_read(OFF_IRQ_STATUS, irq_status);
        if ((irq_status & mask) != 0)
          disable wait_irq;
      end
    end
  end
endtask

task host_wait_cq_head(input [31:0] cq_tail, input integer max_iters, output [31:0] cq_head);
  begin
    cq_head = 0;
    begin : wait_head
      integer i;
      for (i = 0; i < max_iters; i = i + 1) begin
        axi_lite_read(OFF_CQ_HEAD, cq_head);
        if (cq_head == cq_tail)
          disable wait_head;
      end
    end
  end
endtask
