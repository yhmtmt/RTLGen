module MG_FA(
  input a,
  input b,
  input cin,
  output sum,
  output cout
);

  assign sum = (a ^ b) ^ cin;
  assign cout = (a & b) | (b & cin) | (a & cin);
endmodule
module MG_HA(
  input a,
  input b,
  output sum,
  output cout
);

  assign sum = a ^ b;
  assign cout = a & b;
endmodule
module mult4u_booth4_sklansky(
  input [3:0] multiplicand,
  input [3:0] multiplier,
  output [7:0] product
);

  wire be_2x_0_0;
  wire be_2x_0_1;
  wire be_2x_0_2;
  wire be_2x_0_3;
  wire be_2x_0_4;
  wire be_2x_0_5;
  wire be_2x_1_0;
  wire be_2x_1_1;
  wire be_2x_1_2;
  wire be_2x_1_3;
  wire be_2x_1_4;
  wire be_2x_1_5;
  wire be_2x_2_0;
  wire be_2x_2_1;
  wire be_2x_2_2;
  wire be_2x_2_3;
  wire be_c_0;
  wire be_c_1;
  wire be_c_2;
  wire be_d_0;
  wire be_d_1;
  wire be_d_2;
  wire be_neg_0;
  wire be_neg_1;
  wire be_neg_2;
  wire be_s1_0;
  wire be_s1_1;
  wire be_s1_2;
  wire be_s2_0;
  wire be_s2_1;
  wire be_s2_2;
  wire be_s2_a_0;
  wire be_s2_a_1;
  wire be_s2_a_2;
  wire be_s2_b_0;
  wire be_s2_b_1;
  wire be_s2_b_2;
  wire be_x_0_0;
  wire be_x_0_1;
  wire be_x_0_2;
  wire be_x_0_3;
  wire be_x_0_4;
  wire be_x_0_5;
  wire be_x_1_0;
  wire be_x_1_1;
  wire be_x_1_2;
  wire be_x_1_3;
  wire be_x_1_4;
  wire be_x_1_5;
  wire be_x_2_0;
  wire be_x_2_1;
  wire be_x_2_2;
  wire be_x_2_3;
  wire not_pp_0_7;
  wire not_pp_1_7;
  wire ny_0;
  wire ny_1;
  wire ny_2;
  wire ny_3;
  wire one;
  wire pp_0_0;
  wire pp_0_1;
  wire pp_0_2;
  wire pp_0_3;
  wire pp_0_4;
  wire pp_0_5;
  wire pp_1_2;
  wire pp_1_3;
  wire pp_1_4;
  wire pp_1_5;
  wire pp_1_6;
  wire pp_1_7;
  wire pp_2_4;
  wire pp_2_5;
  wire pp_2_6;
  wire pp_2_7;
  wire px_0_0;
  wire px_0_1;
  wire px_0_2;
  wire px_0_3;
  wire px_0_4;
  wire px_0_5;
  wire px_0_6;
  wire px_1_0;
  wire px_1_1;
  wire px_1_2;
  wire px_1_3;
  wire px_1_4;
  wire px_1_5;
  wire px_1_6;
  wire px_2_0;
  wire px_2_1;
  wire px_2_2;
  wire px_2_3;
  wire px_2_4;
  wire px_2_5;
  wire px_2_6;
  wire x_0;
  wire x_1;
  wire x_2;
  wire x_3;
  wire y_0;
  wire y_1;
  wire y_2;
  wire y_3;
  wire zero;
  assign be_2x_0_0 = ~(px_0_0 & be_s2_0);
  assign be_2x_0_1 = ~(px_0_1 & be_s2_0);
  assign be_2x_0_2 = ~(px_0_2 & be_s2_0);
  assign be_2x_0_3 = ~(px_0_3 & be_s2_0);
  assign be_2x_0_4 = ~(px_0_4 & be_s2_0);
  assign be_2x_0_5 = ~(px_0_5 & be_s2_0);
  assign be_2x_1_0 = ~(px_1_0 & be_s2_1);
  assign be_2x_1_1 = ~(px_1_1 & be_s2_1);
  assign be_2x_1_2 = ~(px_1_2 & be_s2_1);
  assign be_2x_1_3 = ~(px_1_3 & be_s2_1);
  assign be_2x_1_4 = ~(px_1_4 & be_s2_1);
  assign be_2x_1_5 = ~(px_1_5 & be_s2_1);
  assign be_2x_2_0 = ~(px_2_0 & be_s2_2);
  assign be_2x_2_1 = ~(px_2_1 & be_s2_2);
  assign be_2x_2_2 = ~(px_2_2 & be_s2_2);
  assign be_2x_2_3 = ~(px_2_3 & be_s2_2);
  assign be_c_0 = be_d_0 & be_neg_0;
  assign be_c_1 = be_d_1 & be_neg_1;
  assign be_c_2 = be_d_2 & be_neg_2;
  assign be_d_0 = ny_0 | one;
  assign be_d_1 = ny_2 | ny_1;
  assign be_d_2 = one | ny_3;
  assign be_neg_0 = y_1;
  assign be_neg_1 = y_3;
  assign be_neg_2 = zero;
  assign be_s1_0 = y_0 ^ zero;
  assign be_s1_1 = y_2 ^ y_1;
  assign be_s1_2 = zero ^ y_3;
  assign be_s2_0 = be_s2_a_0 | be_s2_b_0;
  assign be_s2_1 = be_s2_a_1 | be_s2_b_1;
  assign be_s2_2 = be_s2_a_2 | be_s2_b_2;
  assign be_s2_a_0 = ny_1 & y_0 & zero;
  assign be_s2_a_1 = ny_3 & y_2 & y_1;
  assign be_s2_a_2 = one & zero & y_3;
  assign be_s2_b_0 = y_1 & ny_0 & one;
  assign be_s2_b_1 = y_3 & ny_2 & ny_1;
  assign be_s2_b_2 = zero & one & ny_3;
  assign be_x_0_0 = ~(px_0_1 & be_s1_0);
  assign be_x_0_1 = ~(px_0_2 & be_s1_0);
  assign be_x_0_2 = ~(px_0_3 & be_s1_0);
  assign be_x_0_3 = ~(px_0_4 & be_s1_0);
  assign be_x_0_4 = ~(px_0_5 & be_s1_0);
  assign be_x_0_5 = ~(px_0_6 & be_s1_0);
  assign be_x_1_0 = ~(px_1_1 & be_s1_1);
  assign be_x_1_1 = ~(px_1_2 & be_s1_1);
  assign be_x_1_2 = ~(px_1_3 & be_s1_1);
  assign be_x_1_3 = ~(px_1_4 & be_s1_1);
  assign be_x_1_4 = ~(px_1_5 & be_s1_1);
  assign be_x_1_5 = ~(px_1_6 & be_s1_1);
  assign be_x_2_0 = ~(px_2_1 & be_s1_2);
  assign be_x_2_1 = ~(px_2_2 & be_s1_2);
  assign be_x_2_2 = ~(px_2_3 & be_s1_2);
  assign be_x_2_3 = ~(px_2_4 & be_s1_2);
  assign not_pp_0_7 = ~pp_0_5;
  assign not_pp_1_7 = ~pp_1_7;
  assign ny_0 = ~multiplier[0];
  assign ny_1 = ~multiplier[1];
  assign ny_2 = ~multiplier[2];
  assign ny_3 = ~multiplier[3];
  assign one = 1'b1;
  assign pp_0_0 = ~(be_2x_0_0 & be_x_0_0);
  assign pp_0_1 = ~(be_2x_0_1 & be_x_0_1);
  assign pp_0_2 = ~(be_2x_0_2 & be_x_0_2);
  assign pp_0_3 = ~(be_2x_0_3 & be_x_0_3);
  assign pp_0_4 = ~(be_2x_0_4 & be_x_0_4);
  assign pp_0_5 = ~(be_2x_0_5 & be_x_0_5);
  assign pp_1_2 = ~(be_2x_1_0 & be_x_1_0);
  assign pp_1_3 = ~(be_2x_1_1 & be_x_1_1);
  assign pp_1_4 = ~(be_2x_1_2 & be_x_1_2);
  assign pp_1_5 = ~(be_2x_1_3 & be_x_1_3);
  assign pp_1_6 = ~(be_2x_1_4 & be_x_1_4);
  assign pp_1_7 = ~(be_2x_1_5 & be_x_1_5);
  assign pp_2_4 = ~(be_2x_2_0 & be_x_2_0);
  assign pp_2_5 = ~(be_2x_2_1 & be_x_2_1);
  assign pp_2_6 = ~(be_2x_2_2 & be_x_2_2);
  assign pp_2_7 = ~(be_2x_2_3 & be_x_2_3);
  assign px_0_0 = be_neg_0;
  assign px_0_1 = be_neg_0 ^ x_0;
  assign px_0_2 = be_neg_0 ^ x_1;
  assign px_0_3 = be_neg_0 ^ x_2;
  assign px_0_4 = be_neg_0 ^ x_3;
  assign px_0_5 = be_neg_0 ^ zero;
  assign px_0_6 = be_neg_0 ^ zero;
  assign px_1_0 = be_neg_1;
  assign px_1_1 = be_neg_1 ^ x_0;
  assign px_1_2 = be_neg_1 ^ x_1;
  assign px_1_3 = be_neg_1 ^ x_2;
  assign px_1_4 = be_neg_1 ^ x_3;
  assign px_1_5 = be_neg_1 ^ zero;
  assign px_1_6 = be_neg_1 ^ zero;
  assign px_2_0 = be_neg_2;
  assign px_2_1 = be_neg_2 ^ x_0;
  assign px_2_2 = be_neg_2 ^ x_1;
  assign px_2_3 = be_neg_2 ^ x_2;
  assign px_2_4 = be_neg_2 ^ x_3;
  assign px_2_5 = be_neg_2 ^ zero;
  assign px_2_6 = be_neg_2 ^ zero;
  assign x_0 = multiplicand[0];
  assign x_1 = multiplicand[1];
  assign x_2 = multiplicand[2];
  assign x_3 = multiplicand[3];
  assign y_0 = multiplier[0];
  assign y_1 = multiplier[1];
  assign y_2 = multiplier[2];
  assign y_3 = multiplier[3];
  assign zero = 1'b0;
  wire pp_0_0_0;
  wire pp_0_0_1;
  wire pp_0_1_0;
  wire pp_0_2_0;
  wire pp_0_2_1;
  wire pp_0_2_2;
  wire pp_0_3_0;
  wire pp_0_3_1;
  wire pp_0_4_0;
  wire pp_0_4_1;
  wire pp_0_4_2;
  wire pp_0_5_0;
  wire pp_0_5_1;
  wire pp_0_5_2;
  wire pp_0_6_0;
  wire pp_0_6_1;
  wire pp_0_6_2;
  wire pp_0_7_0;
  wire pp_0_7_1;
  wire pp_0_7_2;
  wire pp_1_0_0;
  wire pp_1_0_1;
  wire pp_1_1_0;
  wire pp_1_2_0;
  wire pp_1_2_1;
  wire pp_1_3_0;
  wire pp_1_3_1;
  wire pp_1_4_0;
  wire pp_1_4_1;
  wire pp_1_5_0;
  wire pp_1_5_1;
  wire pp_1_6_0;
  wire pp_1_6_1;
  wire pp_1_7_0;
  wire pp_1_7_1;
  assign pp_0_0_0 = pp_0_0;
  assign pp_0_0_1 = be_c_0;
  assign pp_0_1_0 = pp_0_1;
  assign pp_0_2_0 = pp_0_2;
  assign pp_0_2_1 = pp_1_2;
  assign pp_0_2_2 = be_c_1;
  assign pp_0_3_0 = pp_0_3;
  assign pp_0_3_1 = pp_1_3;
  assign pp_0_4_0 = pp_0_4;
  assign pp_0_4_1 = pp_1_4;
  assign pp_0_4_2 = pp_2_4;
  assign pp_0_5_0 = pp_0_5;
  assign pp_0_5_1 = pp_1_5;
  assign pp_0_5_2 = pp_2_5;
  assign pp_0_6_0 = pp_0_5;
  assign pp_0_6_1 = pp_1_6;
  assign pp_0_6_2 = pp_2_6;
  assign pp_0_7_0 = not_pp_0_7;
  assign pp_0_7_1 = not_pp_1_7;
  assign pp_0_7_2 = pp_2_7;

  assign pp_1_0_0 = pp_0_0_0;
  assign pp_1_0_1 = pp_0_0_1;
  assign pp_1_1_0 = pp_0_1_0;
  MG_HA ha_0_2_0(
    .a(pp_0_2_0),
    .b(pp_0_2_1),
    .sum(pp_1_2_0),
    .cout(pp_1_3_0)
  );

  assign pp_1_2_1 = pp_0_2_2;
  MG_HA ha_0_3_0(
    .a(pp_0_3_0),
    .b(pp_0_3_1),
    .sum(pp_1_3_1),
    .cout(pp_1_4_0)
  );

  MG_FA fa_0_4_0(
    .a(pp_0_4_0),
    .b(pp_0_4_1),
    .cin(pp_0_4_2),
    .sum(pp_1_4_1),
    .cout(pp_1_5_0)
  );

  MG_FA fa_0_5_0(
    .a(pp_0_5_0),
    .b(pp_0_5_1),
    .cin(pp_0_5_2),
    .sum(pp_1_5_1),
    .cout(pp_1_6_0)
  );

  MG_FA fa_0_6_0(
    .a(pp_0_6_0),
    .b(pp_0_6_1),
    .cin(pp_0_6_2),
    .sum(pp_1_6_1),
    .cout(pp_1_7_0)
  );

  MG_FA fa_0_7_0(
    .a(pp_0_7_0),
    .b(pp_0_7_1),
    .cin(pp_0_7_2),
    .sum(pp_1_7_1),
    .cout()
  );

  wire [7:0] cta;
  wire [7:0] ctb;
  wire [7:0] cts;
  wire ctc;

  MG_CPA cpa(
 .a(cta), .b(ctb), .sum(cts), .cout(ctc)
  );

  assign cta[0] = pp_1_0_0;
  assign ctb[0] = pp_1_0_1;
  assign cta[1] = pp_1_1_0;
  assign ctb[1] = 1'b0;
  assign cta[2] = pp_1_2_0;
  assign ctb[2] = pp_1_2_1;
  assign cta[3] = pp_1_3_0;
  assign ctb[3] = pp_1_3_1;
  assign cta[4] = pp_1_4_0;
  assign ctb[4] = pp_1_4_1;
  assign cta[5] = pp_1_5_0;
  assign ctb[5] = pp_1_5_1;
  assign cta[6] = pp_1_6_0;
  assign ctb[6] = pp_1_6_1;
  assign cta[7] = pp_1_7_0;
  assign ctb[7] = pp_1_7_1;
  assign product[7:0] = cts;
endmodule
