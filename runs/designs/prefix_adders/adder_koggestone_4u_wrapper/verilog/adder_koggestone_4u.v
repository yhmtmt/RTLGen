module adder_koggestone_4u(
  input [3:0] a,
  input [3:0] b,
  output [3:0] sum,
  output cout
);

  wire p_0_0;
  wire g_0_0;
 assign p_0_0 = a[0] ^ b[0];
 assign g_0_0 = a[0] & b[0];
  wire p_1_1;
  wire g_1_1;
 assign p_1_1 = a[1] ^ b[1];
 assign g_1_1 = a[1] & b[1];
  wire p_1_0;
  wire g_1_0;
  wire p_2_2;
  wire g_2_2;
 assign p_2_2 = a[2] ^ b[2];
 assign g_2_2 = a[2] & b[2];
  wire p_2_0;
  wire g_2_0;
  wire p_2_1;
  wire g_2_1;
  wire p_3_3;
  wire g_3_3;
 assign p_3_3 = a[3] ^ b[3];
 assign g_3_3 = a[3] & b[3];
  wire p_3_0;
  wire g_3_0;
  wire p_3_1;
  wire g_3_1;
  wire p_3_2;
  wire g_3_2;
 assign sum[0] = p_0_0;
 assign p_1_0 = p_1_1 & p_0_0;
 assign g_1_0 = g_1_1 | (p_1_1 & g_0_0);
 assign sum[1] = p_1_1^ g_0_0;
 assign p_2_0 = p_2_1 & p_0_0;
 assign g_2_0 = g_2_1 | (p_2_1 & g_0_0);
 assign p_2_1 = p_2_2 & p_1_1;
 assign g_2_1 = g_2_2 | (p_2_2 & g_1_1);
 assign sum[2] = p_2_2^ g_1_0;
 assign p_3_0 = p_3_2 & p_1_0;
 assign g_3_0 = g_3_2 | (p_3_2 & g_1_0);
 assign p_3_1 = p_3_2 & p_1_1;
 assign g_3_1 = g_3_2 | (p_3_2 & g_1_1);
 assign p_3_2 = p_3_3 & p_2_2;
 assign g_3_2 = g_3_3 | (p_3_3 & g_2_2);
 assign sum[3] = p_3_3^ g_2_0;
 assign cout = g_3_0;
endmodule
