module MG_CPA(
  input [6:0] a,
  input [6:0] b,
  output [6:0] sum,
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
  wire p_3_3;
  wire g_3_3;
 assign p_3_3 = a[3] ^ b[3];
 assign g_3_3 = a[3] & b[3];
  wire p_3_0;
  wire g_3_0;
  wire p_4_4;
  wire g_4_4;
 assign p_4_4 = a[4] ^ b[4];
 assign g_4_4 = a[4] & b[4];
  wire p_4_0;
  wire g_4_0;
  wire p_5_5;
  wire g_5_5;
 assign p_5_5 = a[5] ^ b[5];
 assign g_5_5 = a[5] & b[5];
  wire p_5_0;
  wire g_5_0;
  wire p_6_6;
  wire g_6_6;
 assign p_6_6 = a[6] ^ b[6];
 assign g_6_6 = a[6] & b[6];
  wire p_6_0;
  wire g_6_0;
 assign sum[0] = p_0_0;
 assign p_1_0 = p_1_1 & p_0_0;
 assign g_1_0 = g_1_1 | (p_1_1 & g_0_0);
 assign sum[1] = p_1_1^ g_0_0;
 assign p_2_0 = p_2_2 & p_1_0;
 assign g_2_0 = g_2_2 | (p_2_2 & g_1_0);
 assign sum[2] = p_2_2^ g_1_0;
 assign p_3_0 = p_3_3 & p_2_0;
 assign g_3_0 = g_3_3 | (p_3_3 & g_2_0);
 assign sum[3] = p_3_3^ g_2_0;
 assign p_4_0 = p_4_4 & p_3_0;
 assign g_4_0 = g_4_4 | (p_4_4 & g_3_0);
 assign sum[4] = p_4_4^ g_3_0;
 assign p_5_0 = p_5_5 & p_4_0;
 assign g_5_0 = g_5_5 | (p_5_5 & g_4_0);
 assign sum[5] = p_5_5^ g_4_0;
 assign p_6_0 = p_6_6 & p_5_0;
 assign g_6_0 = g_6_6 | (p_6_6 & g_5_0);
 assign sum[6] = p_6_6^ g_5_0;
 assign cout = g_6_0;
endmodule
