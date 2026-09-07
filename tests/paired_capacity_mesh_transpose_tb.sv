`timescale 1ns/1ps
module tb;
localparam WITH_STAGE=STAGE_ENABLED;
reg clk=0,rst_n=0; always #1 clk=~clk;
integer cycle=0,progress_fd;
wire [21:0] generated_descriptor_count,completed_descriptor_count;
// Run real layer-0 refill then heads 0 of tiles 0, 1, and 2. Do not pretend
// this bounded fixture completes the full model.
wire enable=generated_descriptor_count < 22'd394;
wire [15:0] source_req_valid,source_req_is_hbm,source_rsp_ready;
wire [16*33-1:0] source_req_byte_address;
reg [15:0] source_req_ready=0,source_rsp_valid=0;
reg [16*256-1:0] source_rsp_data=0;
wire [15:0] resident_write_valid;
reg [15:0] resident_write_ready=0;
wire [16*33-1:0] resident_write_byte_address;
wire [16*256-1:0] resident_write_data;
wire [15:0] canonical_ingress_valid;
wire [15:0] canonical_ingress_ready;
wire [16*5-1:0] canonical_ingress_layer;
wire [16*7-1:0] canonical_ingress_tile;
wire [16*20-1:0] canonical_ingress_tile_byte_address;
wire [16*256-1:0] canonical_ingress_data;
wire protocol_error;
reg [255:0] resident_memory [0:69631];
reg resident_written [0:69631];
reg [15:0] pending=0;
reg [255:0] response [0:15];
integer inputs[0:2],outputs[0:2];
integer refill_count=0,resident_reads=0,hbm_reads=0;
integer lane,init_i,comb_i,index;
reg [32:0] address;
reg [19:0] expected_address;
reg [255:0] expected_output;
integer half_index,token_index;
wire [2:0] key_valid,key_ready,key_error;
wire [3*256-1:0] key_data;
wire [2:0] stage_error,stage_done;

function automatic [7:0] tensor_byte;
 input integer slot,stream,token,dimension;
 begin tensor_byte=(slot*13+stream*71+token*17+dimension*3)&255; end
endfunction
function automatic [255:0] source_payload;
 input [32:0] a;
 integer b;
 begin
  for(b=0;b<32;b=b+1)
   source_payload[b*8+:8]=tensor_byte(a[15:10],a[16],a[9:7],a[6:0]+b);
 end
endfunction

attention_kv_capacity_gather_mesh_ingress #(.PAIRED_K(1)) dut (
 .clk(clk),.rst_n(rst_n),.enable(enable),
 .source_req_valid(source_req_valid),.source_req_ready(source_req_ready),
 .source_req_is_hbm(source_req_is_hbm),.source_req_byte_address(source_req_byte_address),
 .source_rsp_valid(source_rsp_valid),.source_rsp_ready(source_rsp_ready),.source_rsp_data(source_rsp_data),
 .resident_write_valid(resident_write_valid),.resident_write_ready(resident_write_ready),
 .resident_write_byte_address(resident_write_byte_address),.resident_write_data(resident_write_data),
 .canonical_ingress_valid(canonical_ingress_valid),.canonical_ingress_ready(canonical_ingress_ready),
 .canonical_ingress_layer(canonical_ingress_layer),.canonical_ingress_tile(canonical_ingress_tile),
 .canonical_ingress_tile_byte_address(canonical_ingress_tile_byte_address),
 .canonical_ingress_data(canonical_ingress_data),.generated_descriptor_count(generated_descriptor_count),
 .completed_descriptor_count(completed_descriptor_count),.protocol_error(protocol_error));

assign canonical_ingress_ready[15:3]=0;
genvar g;
generate for(g=0;g<3;g=g+1) begin : transposers
 wire allow_key=(cycle%7!=2 && cycle%7!=3);
 wire stage_ready;
 wire [5:0] kp,kpair;wire [1:0] kh;wire kb,kl;
 assign key_ready[g]=allow_key && (!WITH_STAGE || stage_ready);
 attention_score32_exact_kv_key_pingpong_transpose #(.PRODUCERS(PRODUCER_COUNT)) transpose (
  .clk(clk),.rst_n(rst_n),.ingress_valid(canonical_ingress_valid[g]),
  .ingress_ready(canonical_ingress_ready[g]),
  .ingress_tile_byte_addr(canonical_ingress_tile_byte_address[g*20+:20]),
  .ingress_data(canonical_ingress_data[g*256+:256]),.ingress_byte_valid(32'hffffffff),
  .key_valid(key_valid[g]),.key_ready(key_ready[g]),.key_data(key_data[g*256+:256]),
  .key_producer(kp),.key_kv_head(kh),.key_producer_block(kb),.key_dimension_pair(kpair),.key_last(kl),
  .protocol_error(key_error[g]));
 if(WITH_STAGE) begin : staged
  reg fill_sent=0,command_sent=0,finished=0;
  reg [7:0] query_dimension=0;
  wire fill_ready,query_ready,fill_complete,command_ready,command_done;
  wire [PRODUCER_COUNT-1:0] pv,pl;
  reg [PRODUCER_COUNT-1:0] pr=0;
  wire [PRODUCER_COUNT*128-1:0] pq,pk;
  reg [63:0] qdata;
  integer p,b,ready_p,q_lane,accepted[0:PRODUCER_COUNT-1],slot,dim,blocks;
  reg [127:0] expected_k,expected_q;
  function automatic [7:0] query_byte;
   input integer d,l;
   begin query_byte=(d*5+l*7)&255;end
  endfunction
  always @(*) for(q_lane=0;q_lane<8;q_lane=q_lane+1)
   qdata[q_lane*8+:8]=query_byte(query_dimension,q_lane);
  attention_score32_exact_kv_key_stage_wide #(.PRODUCERS(PRODUCER_COUNT)) stage (
   .clk(clk),.rst_n(rst_n),.fill_target_valid(!fill_sent),.fill_target_ready(fill_ready),
   .fill_target_kv_head(2'd0),.query_write_valid(fill_sent && query_dimension<128),
   .query_write_ready(query_ready),.query_write_kv_head(2'd0),
   .query_write_dimension(query_dimension[6:0]),.query_write_data(qdata),.query_write_last(query_dimension==127),
   .key_write_valid(key_valid[g]&&allow_key),.key_write_ready(stage_ready),
   .key_write_kv_head(kh),.key_write_producer(kp),.key_write_producer_block(kb),
   .key_write_dimension_pair(kpair),.key_write_data(key_data[g*256+:256]),.key_write_last(kl),
   .fill_complete(fill_complete),.command_valid(fill_complete&&!command_sent),
   .command_ready(command_ready),.command_kv_head(2'd0),.producer_valid(pv),.producer_ready(pr),
   .producer_last(pl),.producer_query(pq),.producer_key(pk),.command_done(command_done),.protocol_error(stage_error[g]));
  assign stage_done[g]=finished;
  always @(negedge clk) for(ready_p=0;ready_p<PRODUCER_COUNT;ready_p=ready_p+1)
   pr[ready_p]=(cycle+ready_p+g)%11!=2 && (cycle+ready_p+g)%11!=3;
  always @(posedge clk) if(rst_n) begin
   if(!fill_sent&&fill_ready) fill_sent<=1;
   if(fill_sent&&query_dimension<128&&query_ready) query_dimension<=query_dimension+1;
   if(fill_complete&&!command_sent&&command_ready) command_sent<=1;
   for(p=0;p<PRODUCER_COUNT;p=p+1) if(pv[p]&&pr[p]) begin
    blocks=p<(64-PRODUCER_COUNT)?2:1;
    if(accepted[p]>=blocks*128) $fatal(1,"extra staged beat");
    slot=p+(p<(64-PRODUCER_COUNT)?p:(64-PRODUCER_COUNT))+accepted[p]/128;
    dim=accepted[p]%128;
    for(b=0;b<16;b=b+1) begin
     expected_k[b*8+:8]=tensor_byte(slot,b/8,b%8,dim);
     expected_q[b*8+:8]=query_byte(dim,b%8);
    end
    if(pk[p*128+:128]!==expected_k || pq[p*128+:128]!==expected_q || pl[p]!=(dim==127))
     $fatal(1,"staged K/Q mismatch tile=%0d producer=%0d beat=%0d",g,p,accepted[p]);
    accepted[p]=accepted[p]+1;
   end
   if(command_done) begin
    for(p=0;p<PRODUCER_COUNT;p=p+1)
     if(accepted[p]!=(p<(64-PRODUCER_COUNT)?256:128)) $fatal(1,"missing staged beats");
    finished<=1;
   end
  end
  initial for(p=0;p<PRODUCER_COUNT;p=p+1) accepted[p]=0;
 end else begin : unstaged
  assign stage_ready=1;assign stage_error[g]=0;assign stage_done[g]=1;
 end
end endgenerate

always @(*) begin
 source_rsp_valid=pending;
 for(comb_i=0;comb_i<16;comb_i=comb_i+1) begin
  source_req_ready[comb_i]=(!pending[comb_i] || source_rsp_ready[comb_i]) && cycle%5!=1;
  source_rsp_data[comb_i*256+:256]=response[comb_i];
  resident_write_ready[comb_i]=cycle%7!=4;
 end
end

always @(posedge clk) if(rst_n) begin
 cycle<=cycle+1;
 if(cycle%4096==0) begin
  $fdisplay(progress_fd,"cycle=%0d refill=%0d generated=%0d completed=%0d inputs=%0d,%0d,%0d outputs=%0d,%0d,%0d",
    cycle,refill_count,generated_descriptor_count,completed_descriptor_count,
    inputs[0],inputs[1],inputs[2],outputs[0],outputs[1],outputs[2]);
  $fflush(progress_fd);
 end
 if(protocol_error || |key_error || |stage_error) $fatal(1,"protocol error cycle=%0d mesh=%b transpose=%b stage=%b",cycle,protocol_error,key_error,stage_error);
 if(|canonical_ingress_valid[15:3]) $fatal(1,"unexpected consume destination");
 for(lane=0;lane<16;lane=lane+1) begin
  if(pending[lane]&&source_rsp_ready[lane]) pending[lane]<=0;
  if(source_req_valid[lane]&&source_req_ready[lane]) begin
   address=source_req_byte_address[lane*33+:33];
   if(address[4:0]!=0) $fatal(1,"unaligned source");
   pending[lane]<=1;
   if(source_req_is_hbm[lane]) begin
    response[lane]<=source_payload(address);
    hbm_reads=hbm_reads+1;
   end else begin
    index=address/32;
    if(index>=69632 || !resident_written[index]) $fatal(1,"read before refill or wrong source address");
    response[lane]<=resident_memory[index];
    resident_reads=resident_reads+1;
   end
  end
  if(resident_write_valid[lane]&&resident_write_ready[lane]) begin
   address=resident_write_byte_address[lane*33+:33]; index=address/32;
   if(address[4:0]!=0 || index>=69632 || resident_written[index]) $fatal(1,"refill address/duplicate");
   resident_memory[index]=resident_write_data[lane*256+:256];
   resident_written[index]=1; refill_count=refill_count+1;
  end
 end
 for(lane=0;lane<3;lane=lane+1) begin
  if(canonical_ingress_valid[lane]&&canonical_ingress_ready[lane]) begin
   expected_address=((inputs[lane]/32)%2)*65536+(inputs[lane]/64)*1024+(inputs[lane]%32)*32;
   if(canonical_ingress_layer[lane*5+:5]!=0 || canonical_ingress_tile[lane*7+:7]!=lane ||
      canonical_ingress_tile_byte_address[lane*20+:20]!==expected_address ||
      canonical_ingress_data[lane*256+:256]!==source_payload({13'd0,expected_address}))
     $fatal(1,"paired ingress order/data lane=%0d input=%0d",lane,inputs[lane]);
   inputs[lane]=inputs[lane]+1;
  end
  if(key_valid[lane]&&key_ready[lane]) begin
   for(half_index=0;half_index<2;half_index=half_index+1)
    for(token_index=0;token_index<16;token_index=token_index+1)
     expected_output[(half_index*16+token_index)*8+:8]=tensor_byte(
      outputs[lane]/64,token_index/8,token_index%8,(outputs[lane]%64)*2+half_index);
   if(key_data[lane*256+:256]!==expected_output) $fatal(1,"transpose data lane=%0d output=%0d",lane,outputs[lane]);
   outputs[lane]=outputs[lane]+1;
  end
 end
 if(completed_descriptor_count==394 && outputs[0]==4096 && outputs[1]==4096 && outputs[2]==4096 && (&stage_done)) begin
  if(refill_count!=69632 || inputs[0]!=4096 || inputs[1]!=4096 || inputs[2]!=4096 ||
     resident_reads!=8704 || hbm_reads!=73216 || generated_descriptor_count!=394)
    $fatal(1,"coverage counts refill=%0d resident=%0d hbm=%0d",refill_count,resident_reads,hbm_reads);
  if(WITH_STAGE) $display("PASS staged producer beats=24576");
  $display("PASS refill=69632 inputs=12288 outputs=12288 descriptors=394 cycles=%0d",cycle); $finish;
 end
 if(cycle>2000000) $fatal(1,"timeout descriptors=%0d completed=%0d",generated_descriptor_count,completed_descriptor_count);
end
initial begin
 progress_fd=$fopen("progress.log","w");
 if(!progress_fd) $fatal(1,"cannot open progress log");
 for(init_i=0;init_i<69632;init_i=init_i+1) resident_written[init_i]=0;
 for(init_i=0;init_i<3;init_i=init_i+1) begin inputs[init_i]=0;outputs[init_i]=0;end
 for(init_i=0;init_i<16;init_i=init_i+1) response[init_i]=0;
 repeat(3) @(negedge clk);rst_n=1;
end
endmodule
