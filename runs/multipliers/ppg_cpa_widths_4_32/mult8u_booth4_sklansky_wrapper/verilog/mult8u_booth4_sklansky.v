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
module mult8u_booth4_sklansky(
  input [7:0] multiplicand,
  input [7:0] multiplier,
  output [15:0] product
);

  wire be_2x_0_0;
  wire be_2x_0_1;
  wire be_2x_0_2;
  wire be_2x_0_3;
  wire be_2x_0_4;
  wire be_2x_0_5;
  wire be_2x_0_6;
  wire be_2x_0_7;
  wire be_2x_0_8;
  wire be_2x_0_9;
  wire be_2x_1_0;
  wire be_2x_1_1;
  wire be_2x_1_2;
  wire be_2x_1_3;
  wire be_2x_1_4;
  wire be_2x_1_5;
  wire be_2x_1_6;
  wire be_2x_1_7;
  wire be_2x_1_8;
  wire be_2x_1_9;
  wire be_2x_2_0;
  wire be_2x_2_1;
  wire be_2x_2_2;
  wire be_2x_2_3;
  wire be_2x_2_4;
  wire be_2x_2_5;
  wire be_2x_2_6;
  wire be_2x_2_7;
  wire be_2x_2_8;
  wire be_2x_2_9;
  wire be_2x_3_0;
  wire be_2x_3_1;
  wire be_2x_3_2;
  wire be_2x_3_3;
  wire be_2x_3_4;
  wire be_2x_3_5;
  wire be_2x_3_6;
  wire be_2x_3_7;
  wire be_2x_3_8;
  wire be_2x_3_9;
  wire be_2x_4_0;
  wire be_2x_4_1;
  wire be_2x_4_2;
  wire be_2x_4_3;
  wire be_2x_4_4;
  wire be_2x_4_5;
  wire be_2x_4_6;
  wire be_2x_4_7;
  wire be_c_0;
  wire be_c_1;
  wire be_c_2;
  wire be_c_3;
  wire be_c_4;
  wire be_d_0;
  wire be_d_1;
  wire be_d_2;
  wire be_d_3;
  wire be_d_4;
  wire be_neg_0;
  wire be_neg_1;
  wire be_neg_2;
  wire be_neg_3;
  wire be_neg_4;
  wire be_s1_0;
  wire be_s1_1;
  wire be_s1_2;
  wire be_s1_3;
  wire be_s1_4;
  wire be_s2_0;
  wire be_s2_1;
  wire be_s2_2;
  wire be_s2_3;
  wire be_s2_4;
  wire be_s2_a_0;
  wire be_s2_a_1;
  wire be_s2_a_2;
  wire be_s2_a_3;
  wire be_s2_a_4;
  wire be_s2_b_0;
  wire be_s2_b_1;
  wire be_s2_b_2;
  wire be_s2_b_3;
  wire be_s2_b_4;
  wire be_x_0_0;
  wire be_x_0_1;
  wire be_x_0_2;
  wire be_x_0_3;
  wire be_x_0_4;
  wire be_x_0_5;
  wire be_x_0_6;
  wire be_x_0_7;
  wire be_x_0_8;
  wire be_x_0_9;
  wire be_x_1_0;
  wire be_x_1_1;
  wire be_x_1_2;
  wire be_x_1_3;
  wire be_x_1_4;
  wire be_x_1_5;
  wire be_x_1_6;
  wire be_x_1_7;
  wire be_x_1_8;
  wire be_x_1_9;
  wire be_x_2_0;
  wire be_x_2_1;
  wire be_x_2_2;
  wire be_x_2_3;
  wire be_x_2_4;
  wire be_x_2_5;
  wire be_x_2_6;
  wire be_x_2_7;
  wire be_x_2_8;
  wire be_x_2_9;
  wire be_x_3_0;
  wire be_x_3_1;
  wire be_x_3_2;
  wire be_x_3_3;
  wire be_x_3_4;
  wire be_x_3_5;
  wire be_x_3_6;
  wire be_x_3_7;
  wire be_x_3_8;
  wire be_x_3_9;
  wire be_x_4_0;
  wire be_x_4_1;
  wire be_x_4_2;
  wire be_x_4_3;
  wire be_x_4_4;
  wire be_x_4_5;
  wire be_x_4_6;
  wire be_x_4_7;
  wire not_pp_0_11;
  wire not_pp_1_11;
  wire not_pp_2_13;
  wire not_pp_3_15;
  wire ny_0;
  wire ny_1;
  wire ny_2;
  wire ny_3;
  wire ny_4;
  wire ny_5;
  wire ny_6;
  wire ny_7;
  wire one;
  wire pp_0_0;
  wire pp_0_1;
  wire pp_0_2;
  wire pp_0_3;
  wire pp_0_4;
  wire pp_0_5;
  wire pp_0_6;
  wire pp_0_7;
  wire pp_0_8;
  wire pp_0_9;
  wire pp_1_10;
  wire pp_1_11;
  wire pp_1_2;
  wire pp_1_3;
  wire pp_1_4;
  wire pp_1_5;
  wire pp_1_6;
  wire pp_1_7;
  wire pp_1_8;
  wire pp_1_9;
  wire pp_2_10;
  wire pp_2_11;
  wire pp_2_12;
  wire pp_2_13;
  wire pp_2_4;
  wire pp_2_5;
  wire pp_2_6;
  wire pp_2_7;
  wire pp_2_8;
  wire pp_2_9;
  wire pp_3_10;
  wire pp_3_11;
  wire pp_3_12;
  wire pp_3_13;
  wire pp_3_14;
  wire pp_3_15;
  wire pp_3_6;
  wire pp_3_7;
  wire pp_3_8;
  wire pp_3_9;
  wire pp_4_10;
  wire pp_4_11;
  wire pp_4_12;
  wire pp_4_13;
  wire pp_4_14;
  wire pp_4_15;
  wire pp_4_8;
  wire pp_4_9;
  wire px_0_0;
  wire px_0_1;
  wire px_0_10;
  wire px_0_2;
  wire px_0_3;
  wire px_0_4;
  wire px_0_5;
  wire px_0_6;
  wire px_0_7;
  wire px_0_8;
  wire px_0_9;
  wire px_1_0;
  wire px_1_1;
  wire px_1_10;
  wire px_1_2;
  wire px_1_3;
  wire px_1_4;
  wire px_1_5;
  wire px_1_6;
  wire px_1_7;
  wire px_1_8;
  wire px_1_9;
  wire px_2_0;
  wire px_2_1;
  wire px_2_10;
  wire px_2_2;
  wire px_2_3;
  wire px_2_4;
  wire px_2_5;
  wire px_2_6;
  wire px_2_7;
  wire px_2_8;
  wire px_2_9;
  wire px_3_0;
  wire px_3_1;
  wire px_3_10;
  wire px_3_2;
  wire px_3_3;
  wire px_3_4;
  wire px_3_5;
  wire px_3_6;
  wire px_3_7;
  wire px_3_8;
  wire px_3_9;
  wire px_4_0;
  wire px_4_1;
  wire px_4_10;
  wire px_4_2;
  wire px_4_3;
  wire px_4_4;
  wire px_4_5;
  wire px_4_6;
  wire px_4_7;
  wire px_4_8;
  wire px_4_9;
  wire x_0;
  wire x_1;
  wire x_2;
  wire x_3;
  wire x_4;
  wire x_5;
  wire x_6;
  wire x_7;
  wire y_0;
  wire y_1;
  wire y_2;
  wire y_3;
  wire y_4;
  wire y_5;
  wire y_6;
  wire y_7;
  wire zero;
  assign be_2x_0_0 = ~(px_0_0 & be_s2_0);
  assign be_2x_0_1 = ~(px_0_1 & be_s2_0);
  assign be_2x_0_2 = ~(px_0_2 & be_s2_0);
  assign be_2x_0_3 = ~(px_0_3 & be_s2_0);
  assign be_2x_0_4 = ~(px_0_4 & be_s2_0);
  assign be_2x_0_5 = ~(px_0_5 & be_s2_0);
  assign be_2x_0_6 = ~(px_0_6 & be_s2_0);
  assign be_2x_0_7 = ~(px_0_7 & be_s2_0);
  assign be_2x_0_8 = ~(px_0_8 & be_s2_0);
  assign be_2x_0_9 = ~(px_0_9 & be_s2_0);
  assign be_2x_1_0 = ~(px_1_0 & be_s2_1);
  assign be_2x_1_1 = ~(px_1_1 & be_s2_1);
  assign be_2x_1_2 = ~(px_1_2 & be_s2_1);
  assign be_2x_1_3 = ~(px_1_3 & be_s2_1);
  assign be_2x_1_4 = ~(px_1_4 & be_s2_1);
  assign be_2x_1_5 = ~(px_1_5 & be_s2_1);
  assign be_2x_1_6 = ~(px_1_6 & be_s2_1);
  assign be_2x_1_7 = ~(px_1_7 & be_s2_1);
  assign be_2x_1_8 = ~(px_1_8 & be_s2_1);
  assign be_2x_1_9 = ~(px_1_9 & be_s2_1);
  assign be_2x_2_0 = ~(px_2_0 & be_s2_2);
  assign be_2x_2_1 = ~(px_2_1 & be_s2_2);
  assign be_2x_2_2 = ~(px_2_2 & be_s2_2);
  assign be_2x_2_3 = ~(px_2_3 & be_s2_2);
  assign be_2x_2_4 = ~(px_2_4 & be_s2_2);
  assign be_2x_2_5 = ~(px_2_5 & be_s2_2);
  assign be_2x_2_6 = ~(px_2_6 & be_s2_2);
  assign be_2x_2_7 = ~(px_2_7 & be_s2_2);
  assign be_2x_2_8 = ~(px_2_8 & be_s2_2);
  assign be_2x_2_9 = ~(px_2_9 & be_s2_2);
  assign be_2x_3_0 = ~(px_3_0 & be_s2_3);
  assign be_2x_3_1 = ~(px_3_1 & be_s2_3);
  assign be_2x_3_2 = ~(px_3_2 & be_s2_3);
  assign be_2x_3_3 = ~(px_3_3 & be_s2_3);
  assign be_2x_3_4 = ~(px_3_4 & be_s2_3);
  assign be_2x_3_5 = ~(px_3_5 & be_s2_3);
  assign be_2x_3_6 = ~(px_3_6 & be_s2_3);
  assign be_2x_3_7 = ~(px_3_7 & be_s2_3);
  assign be_2x_3_8 = ~(px_3_8 & be_s2_3);
  assign be_2x_3_9 = ~(px_3_9 & be_s2_3);
  assign be_2x_4_0 = ~(px_4_0 & be_s2_4);
  assign be_2x_4_1 = ~(px_4_1 & be_s2_4);
  assign be_2x_4_2 = ~(px_4_2 & be_s2_4);
  assign be_2x_4_3 = ~(px_4_3 & be_s2_4);
  assign be_2x_4_4 = ~(px_4_4 & be_s2_4);
  assign be_2x_4_5 = ~(px_4_5 & be_s2_4);
  assign be_2x_4_6 = ~(px_4_6 & be_s2_4);
  assign be_2x_4_7 = ~(px_4_7 & be_s2_4);
  assign be_c_0 = be_d_0 & be_neg_0;
  assign be_c_1 = be_d_1 & be_neg_1;
  assign be_c_2 = be_d_2 & be_neg_2;
  assign be_c_3 = be_d_3 & be_neg_3;
  assign be_c_4 = be_d_4 & be_neg_4;
  assign be_d_0 = ny_0 | one;
  assign be_d_1 = ny_2 | ny_1;
  assign be_d_2 = ny_4 | ny_3;
  assign be_d_3 = ny_6 | ny_5;
  assign be_d_4 = one | ny_7;
  assign be_neg_0 = y_1;
  assign be_neg_1 = y_3;
  assign be_neg_2 = y_5;
  assign be_neg_3 = y_7;
  assign be_neg_4 = zero;
  assign be_s1_0 = y_0 ^ zero;
  assign be_s1_1 = y_2 ^ y_1;
  assign be_s1_2 = y_4 ^ y_3;
  assign be_s1_3 = y_6 ^ y_5;
  assign be_s1_4 = zero ^ y_7;
  assign be_s2_0 = be_s2_a_0 | be_s2_b_0;
  assign be_s2_1 = be_s2_a_1 | be_s2_b_1;
  assign be_s2_2 = be_s2_a_2 | be_s2_b_2;
  assign be_s2_3 = be_s2_a_3 | be_s2_b_3;
  assign be_s2_4 = be_s2_a_4 | be_s2_b_4;
  assign be_s2_a_0 = ny_1 & y_0 & zero;
  assign be_s2_a_1 = ny_3 & y_2 & y_1;
  assign be_s2_a_2 = ny_5 & y_4 & y_3;
  assign be_s2_a_3 = ny_7 & y_6 & y_5;
  assign be_s2_a_4 = one & zero & y_7;
  assign be_s2_b_0 = y_1 & ny_0 & one;
  assign be_s2_b_1 = y_3 & ny_2 & ny_1;
  assign be_s2_b_2 = y_5 & ny_4 & ny_3;
  assign be_s2_b_3 = y_7 & ny_6 & ny_5;
  assign be_s2_b_4 = zero & one & ny_7;
  assign be_x_0_0 = ~(px_0_1 & be_s1_0);
  assign be_x_0_1 = ~(px_0_2 & be_s1_0);
  assign be_x_0_2 = ~(px_0_3 & be_s1_0);
  assign be_x_0_3 = ~(px_0_4 & be_s1_0);
  assign be_x_0_4 = ~(px_0_5 & be_s1_0);
  assign be_x_0_5 = ~(px_0_6 & be_s1_0);
  assign be_x_0_6 = ~(px_0_7 & be_s1_0);
  assign be_x_0_7 = ~(px_0_8 & be_s1_0);
  assign be_x_0_8 = ~(px_0_9 & be_s1_0);
  assign be_x_0_9 = ~(px_0_10 & be_s1_0);
  assign be_x_1_0 = ~(px_1_1 & be_s1_1);
  assign be_x_1_1 = ~(px_1_2 & be_s1_1);
  assign be_x_1_2 = ~(px_1_3 & be_s1_1);
  assign be_x_1_3 = ~(px_1_4 & be_s1_1);
  assign be_x_1_4 = ~(px_1_5 & be_s1_1);
  assign be_x_1_5 = ~(px_1_6 & be_s1_1);
  assign be_x_1_6 = ~(px_1_7 & be_s1_1);
  assign be_x_1_7 = ~(px_1_8 & be_s1_1);
  assign be_x_1_8 = ~(px_1_9 & be_s1_1);
  assign be_x_1_9 = ~(px_1_10 & be_s1_1);
  assign be_x_2_0 = ~(px_2_1 & be_s1_2);
  assign be_x_2_1 = ~(px_2_2 & be_s1_2);
  assign be_x_2_2 = ~(px_2_3 & be_s1_2);
  assign be_x_2_3 = ~(px_2_4 & be_s1_2);
  assign be_x_2_4 = ~(px_2_5 & be_s1_2);
  assign be_x_2_5 = ~(px_2_6 & be_s1_2);
  assign be_x_2_6 = ~(px_2_7 & be_s1_2);
  assign be_x_2_7 = ~(px_2_8 & be_s1_2);
  assign be_x_2_8 = ~(px_2_9 & be_s1_2);
  assign be_x_2_9 = ~(px_2_10 & be_s1_2);
  assign be_x_3_0 = ~(px_3_1 & be_s1_3);
  assign be_x_3_1 = ~(px_3_2 & be_s1_3);
  assign be_x_3_2 = ~(px_3_3 & be_s1_3);
  assign be_x_3_3 = ~(px_3_4 & be_s1_3);
  assign be_x_3_4 = ~(px_3_5 & be_s1_3);
  assign be_x_3_5 = ~(px_3_6 & be_s1_3);
  assign be_x_3_6 = ~(px_3_7 & be_s1_3);
  assign be_x_3_7 = ~(px_3_8 & be_s1_3);
  assign be_x_3_8 = ~(px_3_9 & be_s1_3);
  assign be_x_3_9 = ~(px_3_10 & be_s1_3);
  assign be_x_4_0 = ~(px_4_1 & be_s1_4);
  assign be_x_4_1 = ~(px_4_2 & be_s1_4);
  assign be_x_4_2 = ~(px_4_3 & be_s1_4);
  assign be_x_4_3 = ~(px_4_4 & be_s1_4);
  assign be_x_4_4 = ~(px_4_5 & be_s1_4);
  assign be_x_4_5 = ~(px_4_6 & be_s1_4);
  assign be_x_4_6 = ~(px_4_7 & be_s1_4);
  assign be_x_4_7 = ~(px_4_8 & be_s1_4);
  assign not_pp_0_11 = ~pp_0_9;
  assign not_pp_1_11 = ~pp_1_11;
  assign not_pp_2_13 = ~pp_2_13;
  assign not_pp_3_15 = ~pp_3_15;
  assign ny_0 = ~multiplier[0];
  assign ny_1 = ~multiplier[1];
  assign ny_2 = ~multiplier[2];
  assign ny_3 = ~multiplier[3];
  assign ny_4 = ~multiplier[4];
  assign ny_5 = ~multiplier[5];
  assign ny_6 = ~multiplier[6];
  assign ny_7 = ~multiplier[7];
  assign one = 1'b1;
  assign pp_0_0 = ~(be_2x_0_0 & be_x_0_0);
  assign pp_0_1 = ~(be_2x_0_1 & be_x_0_1);
  assign pp_0_2 = ~(be_2x_0_2 & be_x_0_2);
  assign pp_0_3 = ~(be_2x_0_3 & be_x_0_3);
  assign pp_0_4 = ~(be_2x_0_4 & be_x_0_4);
  assign pp_0_5 = ~(be_2x_0_5 & be_x_0_5);
  assign pp_0_6 = ~(be_2x_0_6 & be_x_0_6);
  assign pp_0_7 = ~(be_2x_0_7 & be_x_0_7);
  assign pp_0_8 = ~(be_2x_0_8 & be_x_0_8);
  assign pp_0_9 = ~(be_2x_0_9 & be_x_0_9);
  assign pp_1_10 = ~(be_2x_1_8 & be_x_1_8);
  assign pp_1_11 = ~(be_2x_1_9 & be_x_1_9);
  assign pp_1_2 = ~(be_2x_1_0 & be_x_1_0);
  assign pp_1_3 = ~(be_2x_1_1 & be_x_1_1);
  assign pp_1_4 = ~(be_2x_1_2 & be_x_1_2);
  assign pp_1_5 = ~(be_2x_1_3 & be_x_1_3);
  assign pp_1_6 = ~(be_2x_1_4 & be_x_1_4);
  assign pp_1_7 = ~(be_2x_1_5 & be_x_1_5);
  assign pp_1_8 = ~(be_2x_1_6 & be_x_1_6);
  assign pp_1_9 = ~(be_2x_1_7 & be_x_1_7);
  assign pp_2_10 = ~(be_2x_2_6 & be_x_2_6);
  assign pp_2_11 = ~(be_2x_2_7 & be_x_2_7);
  assign pp_2_12 = ~(be_2x_2_8 & be_x_2_8);
  assign pp_2_13 = ~(be_2x_2_9 & be_x_2_9);
  assign pp_2_4 = ~(be_2x_2_0 & be_x_2_0);
  assign pp_2_5 = ~(be_2x_2_1 & be_x_2_1);
  assign pp_2_6 = ~(be_2x_2_2 & be_x_2_2);
  assign pp_2_7 = ~(be_2x_2_3 & be_x_2_3);
  assign pp_2_8 = ~(be_2x_2_4 & be_x_2_4);
  assign pp_2_9 = ~(be_2x_2_5 & be_x_2_5);
  assign pp_3_10 = ~(be_2x_3_4 & be_x_3_4);
  assign pp_3_11 = ~(be_2x_3_5 & be_x_3_5);
  assign pp_3_12 = ~(be_2x_3_6 & be_x_3_6);
  assign pp_3_13 = ~(be_2x_3_7 & be_x_3_7);
  assign pp_3_14 = ~(be_2x_3_8 & be_x_3_8);
  assign pp_3_15 = ~(be_2x_3_9 & be_x_3_9);
  assign pp_3_6 = ~(be_2x_3_0 & be_x_3_0);
  assign pp_3_7 = ~(be_2x_3_1 & be_x_3_1);
  assign pp_3_8 = ~(be_2x_3_2 & be_x_3_2);
  assign pp_3_9 = ~(be_2x_3_3 & be_x_3_3);
  assign pp_4_10 = ~(be_2x_4_2 & be_x_4_2);
  assign pp_4_11 = ~(be_2x_4_3 & be_x_4_3);
  assign pp_4_12 = ~(be_2x_4_4 & be_x_4_4);
  assign pp_4_13 = ~(be_2x_4_5 & be_x_4_5);
  assign pp_4_14 = ~(be_2x_4_6 & be_x_4_6);
  assign pp_4_15 = ~(be_2x_4_7 & be_x_4_7);
  assign pp_4_8 = ~(be_2x_4_0 & be_x_4_0);
  assign pp_4_9 = ~(be_2x_4_1 & be_x_4_1);
  assign px_0_0 = be_neg_0;
  assign px_0_1 = be_neg_0 ^ x_0;
  assign px_0_10 = be_neg_0 ^ zero;
  assign px_0_2 = be_neg_0 ^ x_1;
  assign px_0_3 = be_neg_0 ^ x_2;
  assign px_0_4 = be_neg_0 ^ x_3;
  assign px_0_5 = be_neg_0 ^ x_4;
  assign px_0_6 = be_neg_0 ^ x_5;
  assign px_0_7 = be_neg_0 ^ x_6;
  assign px_0_8 = be_neg_0 ^ x_7;
  assign px_0_9 = be_neg_0 ^ zero;
  assign px_1_0 = be_neg_1;
  assign px_1_1 = be_neg_1 ^ x_0;
  assign px_1_10 = be_neg_1 ^ zero;
  assign px_1_2 = be_neg_1 ^ x_1;
  assign px_1_3 = be_neg_1 ^ x_2;
  assign px_1_4 = be_neg_1 ^ x_3;
  assign px_1_5 = be_neg_1 ^ x_4;
  assign px_1_6 = be_neg_1 ^ x_5;
  assign px_1_7 = be_neg_1 ^ x_6;
  assign px_1_8 = be_neg_1 ^ x_7;
  assign px_1_9 = be_neg_1 ^ zero;
  assign px_2_0 = be_neg_2;
  assign px_2_1 = be_neg_2 ^ x_0;
  assign px_2_10 = be_neg_2 ^ zero;
  assign px_2_2 = be_neg_2 ^ x_1;
  assign px_2_3 = be_neg_2 ^ x_2;
  assign px_2_4 = be_neg_2 ^ x_3;
  assign px_2_5 = be_neg_2 ^ x_4;
  assign px_2_6 = be_neg_2 ^ x_5;
  assign px_2_7 = be_neg_2 ^ x_6;
  assign px_2_8 = be_neg_2 ^ x_7;
  assign px_2_9 = be_neg_2 ^ zero;
  assign px_3_0 = be_neg_3;
  assign px_3_1 = be_neg_3 ^ x_0;
  assign px_3_10 = be_neg_3 ^ zero;
  assign px_3_2 = be_neg_3 ^ x_1;
  assign px_3_3 = be_neg_3 ^ x_2;
  assign px_3_4 = be_neg_3 ^ x_3;
  assign px_3_5 = be_neg_3 ^ x_4;
  assign px_3_6 = be_neg_3 ^ x_5;
  assign px_3_7 = be_neg_3 ^ x_6;
  assign px_3_8 = be_neg_3 ^ x_7;
  assign px_3_9 = be_neg_3 ^ zero;
  assign px_4_0 = be_neg_4;
  assign px_4_1 = be_neg_4 ^ x_0;
  assign px_4_10 = be_neg_4 ^ zero;
  assign px_4_2 = be_neg_4 ^ x_1;
  assign px_4_3 = be_neg_4 ^ x_2;
  assign px_4_4 = be_neg_4 ^ x_3;
  assign px_4_5 = be_neg_4 ^ x_4;
  assign px_4_6 = be_neg_4 ^ x_5;
  assign px_4_7 = be_neg_4 ^ x_6;
  assign px_4_8 = be_neg_4 ^ x_7;
  assign px_4_9 = be_neg_4 ^ zero;
  assign x_0 = multiplicand[0];
  assign x_1 = multiplicand[1];
  assign x_2 = multiplicand[2];
  assign x_3 = multiplicand[3];
  assign x_4 = multiplicand[4];
  assign x_5 = multiplicand[5];
  assign x_6 = multiplicand[6];
  assign x_7 = multiplicand[7];
  assign y_0 = multiplier[0];
  assign y_1 = multiplier[1];
  assign y_2 = multiplier[2];
  assign y_3 = multiplier[3];
  assign y_4 = multiplier[4];
  assign y_5 = multiplier[5];
  assign y_6 = multiplier[6];
  assign y_7 = multiplier[7];
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
  wire pp_0_4_3;
  wire pp_0_5_0;
  wire pp_0_5_1;
  wire pp_0_5_2;
  wire pp_0_6_0;
  wire pp_0_6_1;
  wire pp_0_6_2;
  wire pp_0_6_3;
  wire pp_0_6_4;
  wire pp_0_7_0;
  wire pp_0_7_1;
  wire pp_0_7_2;
  wire pp_0_7_3;
  wire pp_0_8_0;
  wire pp_0_8_1;
  wire pp_0_8_2;
  wire pp_0_8_3;
  wire pp_0_8_4;
  wire pp_0_9_0;
  wire pp_0_9_1;
  wire pp_0_9_2;
  wire pp_0_9_3;
  wire pp_0_9_4;
  wire pp_0_10_0;
  wire pp_0_10_1;
  wire pp_0_10_2;
  wire pp_0_10_3;
  wire pp_0_10_4;
  wire pp_0_11_0;
  wire pp_0_11_1;
  wire pp_0_11_2;
  wire pp_0_11_3;
  wire pp_0_11_4;
  wire pp_0_12_0;
  wire pp_0_12_1;
  wire pp_0_12_2;
  wire pp_0_12_3;
  wire pp_0_13_0;
  wire pp_0_13_1;
  wire pp_0_13_2;
  wire pp_0_14_0;
  wire pp_0_14_1;
  wire pp_0_14_2;
  wire pp_0_15_0;
  wire pp_0_15_1;
  wire pp_1_0_0;
  wire pp_1_0_1;
  wire pp_1_1_0;
  wire pp_1_2_0;
  wire pp_1_2_1;
  wire pp_1_2_2;
  wire pp_1_3_0;
  wire pp_1_3_1;
  wire pp_1_4_0;
  wire pp_1_4_1;
  wire pp_1_5_0;
  wire pp_1_5_1;
  wire pp_1_5_2;
  wire pp_1_5_3;
  wire pp_1_6_0;
  wire pp_1_6_1;
  wire pp_1_6_2;
  wire pp_1_7_0;
  wire pp_1_7_1;
  wire pp_1_7_2;
  wire pp_1_8_0;
  wire pp_1_8_1;
  wire pp_1_8_2;
  wire pp_1_8_3;
  wire pp_1_8_4;
  wire pp_1_8_5;
  wire pp_1_9_0;
  wire pp_1_9_1;
  wire pp_1_9_2;
  wire pp_1_10_0;
  wire pp_1_10_1;
  wire pp_1_10_2;
  wire pp_1_10_3;
  wire pp_1_11_0;
  wire pp_1_11_1;
  wire pp_1_11_2;
  wire pp_1_11_3;
  wire pp_1_12_0;
  wire pp_1_12_1;
  wire pp_1_12_2;
  wire pp_1_12_3;
  wire pp_1_13_0;
  wire pp_1_13_1;
  wire pp_1_13_2;
  wire pp_1_13_3;
  wire pp_1_14_0;
  wire pp_1_15_0;
  wire pp_1_15_1;
  wire pp_1_15_2;
  wire pp_2_0_0;
  wire pp_2_0_1;
  wire pp_2_1_0;
  wire pp_2_2_0;
  wire pp_2_2_1;
  wire pp_2_2_2;
  wire pp_2_3_0;
  wire pp_2_3_1;
  wire pp_2_4_0;
  wire pp_2_4_1;
  wire pp_2_5_0;
  wire pp_2_5_1;
  wire pp_2_5_2;
  wire pp_2_6_0;
  wire pp_2_6_1;
  wire pp_2_7_0;
  wire pp_2_7_1;
  wire pp_2_7_2;
  wire pp_2_8_0;
  wire pp_2_8_1;
  wire pp_2_8_2;
  wire pp_2_9_0;
  wire pp_2_9_1;
  wire pp_2_9_2;
  wire pp_2_10_0;
  wire pp_2_10_1;
  wire pp_2_10_2;
  wire pp_2_11_0;
  wire pp_2_11_1;
  wire pp_2_11_2;
  wire pp_2_12_0;
  wire pp_2_12_1;
  wire pp_2_12_2;
  wire pp_2_13_0;
  wire pp_2_13_1;
  wire pp_2_13_2;
  wire pp_2_14_0;
  wire pp_2_14_1;
  wire pp_2_15_0;
  wire pp_2_15_1;
  wire pp_2_15_2;
  wire pp_3_0_0;
  wire pp_3_0_1;
  wire pp_3_1_0;
  wire pp_3_2_0;
  wire pp_3_2_1;
  wire pp_3_3_0;
  wire pp_3_3_1;
  wire pp_3_4_0;
  wire pp_3_4_1;
  wire pp_3_5_0;
  wire pp_3_5_1;
  wire pp_3_6_0;
  wire pp_3_6_1;
  wire pp_3_7_0;
  wire pp_3_7_1;
  wire pp_3_8_0;
  wire pp_3_8_1;
  wire pp_3_9_0;
  wire pp_3_9_1;
  wire pp_3_10_0;
  wire pp_3_10_1;
  wire pp_3_11_0;
  wire pp_3_11_1;
  wire pp_3_12_0;
  wire pp_3_12_1;
  wire pp_3_13_0;
  wire pp_3_13_1;
  wire pp_3_14_0;
  wire pp_3_14_1;
  wire pp_3_15_0;
  wire pp_3_15_1;
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
  assign pp_0_4_3 = be_c_2;
  assign pp_0_5_0 = pp_0_5;
  assign pp_0_5_1 = pp_1_5;
  assign pp_0_5_2 = pp_2_5;
  assign pp_0_6_0 = pp_0_6;
  assign pp_0_6_1 = pp_1_6;
  assign pp_0_6_2 = pp_2_6;
  assign pp_0_6_3 = pp_3_6;
  assign pp_0_6_4 = be_c_3;
  assign pp_0_7_0 = pp_0_7;
  assign pp_0_7_1 = pp_1_7;
  assign pp_0_7_2 = pp_2_7;
  assign pp_0_7_3 = pp_3_7;
  assign pp_0_8_0 = pp_0_8;
  assign pp_0_8_1 = pp_1_8;
  assign pp_0_8_2 = pp_2_8;
  assign pp_0_8_3 = pp_3_8;
  assign pp_0_8_4 = pp_4_8;
  assign pp_0_9_0 = pp_0_9;
  assign pp_0_9_1 = pp_1_9;
  assign pp_0_9_2 = pp_2_9;
  assign pp_0_9_3 = pp_3_9;
  assign pp_0_9_4 = pp_4_9;
  assign pp_0_10_0 = pp_0_9;
  assign pp_0_10_1 = pp_1_10;
  assign pp_0_10_2 = pp_2_10;
  assign pp_0_10_3 = pp_3_10;
  assign pp_0_10_4 = pp_4_10;
  assign pp_0_11_0 = not_pp_0_11;
  assign pp_0_11_1 = not_pp_1_11;
  assign pp_0_11_2 = pp_2_11;
  assign pp_0_11_3 = pp_3_11;
  assign pp_0_11_4 = pp_4_11;
  assign pp_0_12_0 = one;
  assign pp_0_12_1 = pp_2_12;
  assign pp_0_12_2 = pp_3_12;
  assign pp_0_12_3 = pp_4_12;
  assign pp_0_13_0 = not_pp_2_13;
  assign pp_0_13_1 = pp_3_13;
  assign pp_0_13_2 = pp_4_13;
  assign pp_0_14_0 = one;
  assign pp_0_14_1 = pp_3_14;
  assign pp_0_14_2 = pp_4_14;
  assign pp_0_15_0 = not_pp_3_15;
  assign pp_0_15_1 = pp_4_15;

  assign pp_1_0_0 = pp_0_0_0;
  assign pp_1_0_1 = pp_0_0_1;
  assign pp_1_1_0 = pp_0_1_0;
  assign pp_1_2_0 = pp_0_2_0;
  assign pp_1_2_1 = pp_0_2_1;
  assign pp_1_2_2 = pp_0_2_2;
  assign pp_1_3_0 = pp_0_3_0;
  assign pp_1_3_1 = pp_0_3_1;
  MG_FA fa_0_4_0(
    .a(pp_0_4_0),
    .b(pp_0_4_1),
    .cin(pp_0_4_2),
    .sum(pp_1_4_0),
    .cout(pp_1_5_0)
  );

  assign pp_1_4_1 = pp_0_4_3;
  assign pp_1_5_1 = pp_0_5_0;
  assign pp_1_5_2 = pp_0_5_1;
  assign pp_1_5_3 = pp_0_5_2;
  MG_FA fa_0_6_0(
    .a(pp_0_6_0),
    .b(pp_0_6_1),
    .cin(pp_0_6_2),
    .sum(pp_1_6_0),
    .cout(pp_1_7_0)
  );

  assign pp_1_6_1 = pp_0_6_3;
  assign pp_1_6_2 = pp_0_6_4;
  MG_FA fa_0_7_0(
    .a(pp_0_7_0),
    .b(pp_0_7_1),
    .cin(pp_0_7_2),
    .sum(pp_1_7_1),
    .cout(pp_1_8_0)
  );

  assign pp_1_7_2 = pp_0_7_3;
  assign pp_1_8_1 = pp_0_8_0;
  assign pp_1_8_2 = pp_0_8_1;
  assign pp_1_8_3 = pp_0_8_2;
  assign pp_1_8_4 = pp_0_8_3;
  assign pp_1_8_5 = pp_0_8_4;
  MG_FA fa_0_9_0(
    .a(pp_0_9_0),
    .b(pp_0_9_1),
    .cin(pp_0_9_2),
    .sum(pp_1_9_0),
    .cout(pp_1_10_0)
  );

  assign pp_1_9_1 = pp_0_9_3;
  assign pp_1_9_2 = pp_0_9_4;
  MG_FA fa_0_10_0(
    .a(pp_0_10_0),
    .b(pp_0_10_1),
    .cin(pp_0_10_2),
    .sum(pp_1_10_1),
    .cout(pp_1_11_0)
  );

  assign pp_1_10_2 = pp_0_10_3;
  assign pp_1_10_3 = pp_0_10_4;
  MG_FA fa_0_11_0(
    .a(pp_0_11_0),
    .b(pp_0_11_1),
    .cin(pp_0_11_2),
    .sum(pp_1_11_1),
    .cout(pp_1_12_0)
  );

  assign pp_1_11_2 = pp_0_11_3;
  assign pp_1_11_3 = pp_0_11_4;
  MG_HA ha_0_12_0(
    .a(pp_0_12_0),
    .b(pp_0_12_1),
    .sum(pp_1_12_1),
    .cout(pp_1_13_0)
  );

  assign pp_1_12_2 = pp_0_12_2;
  assign pp_1_12_3 = pp_0_12_3;
  assign pp_1_13_1 = pp_0_13_0;
  assign pp_1_13_2 = pp_0_13_1;
  assign pp_1_13_3 = pp_0_13_2;
  MG_FA fa_0_14_0(
    .a(pp_0_14_0),
    .b(pp_0_14_1),
    .cin(pp_0_14_2),
    .sum(pp_1_14_0),
    .cout(pp_1_15_0)
  );

  assign pp_1_15_1 = pp_0_15_0;
  assign pp_1_15_2 = pp_0_15_1;
  assign pp_2_0_0 = pp_1_0_0;
  assign pp_2_0_1 = pp_1_0_1;
  assign pp_2_1_0 = pp_1_1_0;
  assign pp_2_2_0 = pp_1_2_0;
  assign pp_2_2_1 = pp_1_2_1;
  assign pp_2_2_2 = pp_1_2_2;
  assign pp_2_3_0 = pp_1_3_0;
  assign pp_2_3_1 = pp_1_3_1;
  assign pp_2_4_0 = pp_1_4_0;
  assign pp_2_4_1 = pp_1_4_1;
  MG_HA ha_1_5_0(
    .a(pp_1_5_0),
    .b(pp_1_5_1),
    .sum(pp_2_5_0),
    .cout(pp_2_6_0)
  );

  assign pp_2_5_1 = pp_1_5_2;
  assign pp_2_5_2 = pp_1_5_3;
  MG_FA fa_1_6_0(
    .a(pp_1_6_0),
    .b(pp_1_6_1),
    .cin(pp_1_6_2),
    .sum(pp_2_6_1),
    .cout(pp_2_7_0)
  );

  MG_HA ha_1_7_0(
    .a(pp_1_7_0),
    .b(pp_1_7_1),
    .sum(pp_2_7_1),
    .cout(pp_2_8_0)
  );

  assign pp_2_7_2 = pp_1_7_2;
  MG_FA fa_1_8_0(
    .a(pp_1_8_0),
    .b(pp_1_8_1),
    .cin(pp_1_8_2),
    .sum(pp_2_8_1),
    .cout(pp_2_9_0)
  );

  MG_FA fa_1_8_1(
    .a(pp_1_8_3),
    .b(pp_1_8_4),
    .cin(pp_1_8_5),
    .sum(pp_2_8_2),
    .cout(pp_2_9_1)
  );

  MG_FA fa_1_9_0(
    .a(pp_1_9_0),
    .b(pp_1_9_1),
    .cin(pp_1_9_2),
    .sum(pp_2_9_2),
    .cout(pp_2_10_0)
  );

  MG_FA fa_1_10_0(
    .a(pp_1_10_0),
    .b(pp_1_10_1),
    .cin(pp_1_10_2),
    .sum(pp_2_10_1),
    .cout(pp_2_11_0)
  );

  assign pp_2_10_2 = pp_1_10_3;
  MG_FA fa_1_11_0(
    .a(pp_1_11_0),
    .b(pp_1_11_1),
    .cin(pp_1_11_2),
    .sum(pp_2_11_1),
    .cout(pp_2_12_0)
  );

  assign pp_2_11_2 = pp_1_11_3;
  MG_FA fa_1_12_0(
    .a(pp_1_12_0),
    .b(pp_1_12_1),
    .cin(pp_1_12_2),
    .sum(pp_2_12_1),
    .cout(pp_2_13_0)
  );

  assign pp_2_12_2 = pp_1_12_3;
  MG_FA fa_1_13_0(
    .a(pp_1_13_0),
    .b(pp_1_13_1),
    .cin(pp_1_13_2),
    .sum(pp_2_13_1),
    .cout(pp_2_14_0)
  );

  assign pp_2_13_2 = pp_1_13_3;
  assign pp_2_14_1 = pp_1_14_0;
  assign pp_2_15_0 = pp_1_15_0;
  assign pp_2_15_1 = pp_1_15_1;
  assign pp_2_15_2 = pp_1_15_2;
  assign pp_3_0_0 = pp_2_0_0;
  assign pp_3_0_1 = pp_2_0_1;
  assign pp_3_1_0 = pp_2_1_0;
  MG_HA ha_2_2_0(
    .a(pp_2_2_0),
    .b(pp_2_2_1),
    .sum(pp_3_2_0),
    .cout(pp_3_3_0)
  );

  assign pp_3_2_1 = pp_2_2_2;
  MG_HA ha_2_3_0(
    .a(pp_2_3_0),
    .b(pp_2_3_1),
    .sum(pp_3_3_1),
    .cout(pp_3_4_0)
  );

  MG_HA ha_2_4_0(
    .a(pp_2_4_0),
    .b(pp_2_4_1),
    .sum(pp_3_4_1),
    .cout(pp_3_5_0)
  );

  MG_FA fa_2_5_0(
    .a(pp_2_5_0),
    .b(pp_2_5_1),
    .cin(pp_2_5_2),
    .sum(pp_3_5_1),
    .cout(pp_3_6_0)
  );

  MG_HA ha_2_6_0(
    .a(pp_2_6_0),
    .b(pp_2_6_1),
    .sum(pp_3_6_1),
    .cout(pp_3_7_0)
  );

  MG_FA fa_2_7_0(
    .a(pp_2_7_0),
    .b(pp_2_7_1),
    .cin(pp_2_7_2),
    .sum(pp_3_7_1),
    .cout(pp_3_8_0)
  );

  MG_FA fa_2_8_0(
    .a(pp_2_8_0),
    .b(pp_2_8_1),
    .cin(pp_2_8_2),
    .sum(pp_3_8_1),
    .cout(pp_3_9_0)
  );

  MG_FA fa_2_9_0(
    .a(pp_2_9_0),
    .b(pp_2_9_1),
    .cin(pp_2_9_2),
    .sum(pp_3_9_1),
    .cout(pp_3_10_0)
  );

  MG_FA fa_2_10_0(
    .a(pp_2_10_0),
    .b(pp_2_10_2),
    .cin(pp_2_10_1),
    .sum(pp_3_10_1),
    .cout(pp_3_11_0)
  );

  MG_FA fa_2_11_0(
    .a(pp_2_11_0),
    .b(pp_2_11_2),
    .cin(pp_2_11_1),
    .sum(pp_3_11_1),
    .cout(pp_3_12_0)
  );

  MG_FA fa_2_12_0(
    .a(pp_2_12_0),
    .b(pp_2_12_1),
    .cin(pp_2_12_2),
    .sum(pp_3_12_1),
    .cout(pp_3_13_0)
  );

  MG_FA fa_2_13_0(
    .a(pp_2_13_0),
    .b(pp_2_13_1),
    .cin(pp_2_13_2),
    .sum(pp_3_13_1),
    .cout(pp_3_14_0)
  );

  MG_HA ha_2_14_0(
    .a(pp_2_14_0),
    .b(pp_2_14_1),
    .sum(pp_3_14_1),
    .cout(pp_3_15_0)
  );

  MG_FA fa_2_15_0(
    .a(pp_2_15_0),
    .b(pp_2_15_1),
    .cin(pp_2_15_2),
    .sum(pp_3_15_1),
    .cout()
  );

  wire [15:0] cta;
  wire [15:0] ctb;
  wire [15:0] cts;
  wire ctc;

  MG_CPA cpa(
 .a(cta), .b(ctb), .sum(cts), .cout(ctc)
  );

  assign cta[0] = pp_3_0_0;
  assign ctb[0] = pp_3_0_1;
  assign cta[1] = pp_3_1_0;
  assign ctb[1] = 1'b0;
  assign cta[2] = pp_3_2_0;
  assign ctb[2] = pp_3_2_1;
  assign cta[3] = pp_3_3_0;
  assign ctb[3] = pp_3_3_1;
  assign cta[4] = pp_3_4_0;
  assign ctb[4] = pp_3_4_1;
  assign cta[5] = pp_3_5_0;
  assign ctb[5] = pp_3_5_1;
  assign cta[6] = pp_3_6_0;
  assign ctb[6] = pp_3_6_1;
  assign cta[7] = pp_3_7_0;
  assign ctb[7] = pp_3_7_1;
  assign cta[8] = pp_3_8_0;
  assign ctb[8] = pp_3_8_1;
  assign cta[9] = pp_3_9_0;
  assign ctb[9] = pp_3_9_1;
  assign cta[10] = pp_3_10_0;
  assign ctb[10] = pp_3_10_1;
  assign cta[11] = pp_3_11_0;
  assign ctb[11] = pp_3_11_1;
  assign cta[12] = pp_3_12_0;
  assign ctb[12] = pp_3_12_1;
  assign cta[13] = pp_3_13_0;
  assign ctb[13] = pp_3_13_1;
  assign cta[14] = pp_3_14_0;
  assign ctb[14] = pp_3_14_1;
  assign cta[15] = pp_3_15_0;
  assign ctb[15] = pp_3_15_1;
  assign product[15:0] = cts;
endmodule
