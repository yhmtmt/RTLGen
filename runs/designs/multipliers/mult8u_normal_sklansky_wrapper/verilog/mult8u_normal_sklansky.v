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
module mult8u_normal_sklansky(
  input [7:0] multiplicand,
  input [7:0] multiplier,
  output [15:0] product
);

  wire pp_0_0;
  wire pp_0_1;
  wire pp_0_2;
  wire pp_0_3;
  wire pp_0_4;
  wire pp_0_5;
  wire pp_0_6;
  wire pp_0_7;
  wire pp_1_1;
  wire pp_1_2;
  wire pp_1_3;
  wire pp_1_4;
  wire pp_1_5;
  wire pp_1_6;
  wire pp_1_7;
  wire pp_1_8;
  wire pp_2_2;
  wire pp_2_3;
  wire pp_2_4;
  wire pp_2_5;
  wire pp_2_6;
  wire pp_2_7;
  wire pp_2_8;
  wire pp_2_9;
  wire pp_3_10;
  wire pp_3_3;
  wire pp_3_4;
  wire pp_3_5;
  wire pp_3_6;
  wire pp_3_7;
  wire pp_3_8;
  wire pp_3_9;
  wire pp_4_10;
  wire pp_4_11;
  wire pp_4_4;
  wire pp_4_5;
  wire pp_4_6;
  wire pp_4_7;
  wire pp_4_8;
  wire pp_4_9;
  wire pp_5_10;
  wire pp_5_11;
  wire pp_5_12;
  wire pp_5_5;
  wire pp_5_6;
  wire pp_5_7;
  wire pp_5_8;
  wire pp_5_9;
  wire pp_6_10;
  wire pp_6_11;
  wire pp_6_12;
  wire pp_6_13;
  wire pp_6_6;
  wire pp_6_7;
  wire pp_6_8;
  wire pp_6_9;
  wire pp_7_10;
  wire pp_7_11;
  wire pp_7_12;
  wire pp_7_13;
  wire pp_7_14;
  wire pp_7_7;
  wire pp_7_8;
  wire pp_7_9;
  assign pp_0_0 = multiplicand[0] & multiplier[0];
  assign pp_0_1 = multiplicand[1] & multiplier[0];
  assign pp_0_2 = multiplicand[2] & multiplier[0];
  assign pp_0_3 = multiplicand[3] & multiplier[0];
  assign pp_0_4 = multiplicand[4] & multiplier[0];
  assign pp_0_5 = multiplicand[5] & multiplier[0];
  assign pp_0_6 = multiplicand[6] & multiplier[0];
  assign pp_0_7 = multiplicand[7] & multiplier[0];
  assign pp_1_1 = multiplicand[0] & multiplier[1];
  assign pp_1_2 = multiplicand[1] & multiplier[1];
  assign pp_1_3 = multiplicand[2] & multiplier[1];
  assign pp_1_4 = multiplicand[3] & multiplier[1];
  assign pp_1_5 = multiplicand[4] & multiplier[1];
  assign pp_1_6 = multiplicand[5] & multiplier[1];
  assign pp_1_7 = multiplicand[6] & multiplier[1];
  assign pp_1_8 = multiplicand[7] & multiplier[1];
  assign pp_2_2 = multiplicand[0] & multiplier[2];
  assign pp_2_3 = multiplicand[1] & multiplier[2];
  assign pp_2_4 = multiplicand[2] & multiplier[2];
  assign pp_2_5 = multiplicand[3] & multiplier[2];
  assign pp_2_6 = multiplicand[4] & multiplier[2];
  assign pp_2_7 = multiplicand[5] & multiplier[2];
  assign pp_2_8 = multiplicand[6] & multiplier[2];
  assign pp_2_9 = multiplicand[7] & multiplier[2];
  assign pp_3_10 = multiplicand[7] & multiplier[3];
  assign pp_3_3 = multiplicand[0] & multiplier[3];
  assign pp_3_4 = multiplicand[1] & multiplier[3];
  assign pp_3_5 = multiplicand[2] & multiplier[3];
  assign pp_3_6 = multiplicand[3] & multiplier[3];
  assign pp_3_7 = multiplicand[4] & multiplier[3];
  assign pp_3_8 = multiplicand[5] & multiplier[3];
  assign pp_3_9 = multiplicand[6] & multiplier[3];
  assign pp_4_10 = multiplicand[6] & multiplier[4];
  assign pp_4_11 = multiplicand[7] & multiplier[4];
  assign pp_4_4 = multiplicand[0] & multiplier[4];
  assign pp_4_5 = multiplicand[1] & multiplier[4];
  assign pp_4_6 = multiplicand[2] & multiplier[4];
  assign pp_4_7 = multiplicand[3] & multiplier[4];
  assign pp_4_8 = multiplicand[4] & multiplier[4];
  assign pp_4_9 = multiplicand[5] & multiplier[4];
  assign pp_5_10 = multiplicand[5] & multiplier[5];
  assign pp_5_11 = multiplicand[6] & multiplier[5];
  assign pp_5_12 = multiplicand[7] & multiplier[5];
  assign pp_5_5 = multiplicand[0] & multiplier[5];
  assign pp_5_6 = multiplicand[1] & multiplier[5];
  assign pp_5_7 = multiplicand[2] & multiplier[5];
  assign pp_5_8 = multiplicand[3] & multiplier[5];
  assign pp_5_9 = multiplicand[4] & multiplier[5];
  assign pp_6_10 = multiplicand[4] & multiplier[6];
  assign pp_6_11 = multiplicand[5] & multiplier[6];
  assign pp_6_12 = multiplicand[6] & multiplier[6];
  assign pp_6_13 = multiplicand[7] & multiplier[6];
  assign pp_6_6 = multiplicand[0] & multiplier[6];
  assign pp_6_7 = multiplicand[1] & multiplier[6];
  assign pp_6_8 = multiplicand[2] & multiplier[6];
  assign pp_6_9 = multiplicand[3] & multiplier[6];
  assign pp_7_10 = multiplicand[3] & multiplier[7];
  assign pp_7_11 = multiplicand[4] & multiplier[7];
  assign pp_7_12 = multiplicand[5] & multiplier[7];
  assign pp_7_13 = multiplicand[6] & multiplier[7];
  assign pp_7_14 = multiplicand[7] & multiplier[7];
  assign pp_7_7 = multiplicand[0] & multiplier[7];
  assign pp_7_8 = multiplicand[1] & multiplier[7];
  assign pp_7_9 = multiplicand[2] & multiplier[7];
  wire pp_0_0_0;
  wire pp_0_1_0;
  wire pp_0_1_1;
  wire pp_0_2_0;
  wire pp_0_2_1;
  wire pp_0_2_2;
  wire pp_0_3_0;
  wire pp_0_3_1;
  wire pp_0_3_2;
  wire pp_0_3_3;
  wire pp_0_4_0;
  wire pp_0_4_1;
  wire pp_0_4_2;
  wire pp_0_4_3;
  wire pp_0_4_4;
  wire pp_0_5_0;
  wire pp_0_5_1;
  wire pp_0_5_2;
  wire pp_0_5_3;
  wire pp_0_5_4;
  wire pp_0_5_5;
  wire pp_0_6_0;
  wire pp_0_6_1;
  wire pp_0_6_2;
  wire pp_0_6_3;
  wire pp_0_6_4;
  wire pp_0_6_5;
  wire pp_0_6_6;
  wire pp_0_7_0;
  wire pp_0_7_1;
  wire pp_0_7_2;
  wire pp_0_7_3;
  wire pp_0_7_4;
  wire pp_0_7_5;
  wire pp_0_7_6;
  wire pp_0_7_7;
  wire pp_0_8_0;
  wire pp_0_8_1;
  wire pp_0_8_2;
  wire pp_0_8_3;
  wire pp_0_8_4;
  wire pp_0_8_5;
  wire pp_0_8_6;
  wire pp_0_9_0;
  wire pp_0_9_1;
  wire pp_0_9_2;
  wire pp_0_9_3;
  wire pp_0_9_4;
  wire pp_0_9_5;
  wire pp_0_10_0;
  wire pp_0_10_1;
  wire pp_0_10_2;
  wire pp_0_10_3;
  wire pp_0_10_4;
  wire pp_0_11_0;
  wire pp_0_11_1;
  wire pp_0_11_2;
  wire pp_0_11_3;
  wire pp_0_12_0;
  wire pp_0_12_1;
  wire pp_0_12_2;
  wire pp_0_13_0;
  wire pp_0_13_1;
  wire pp_0_14_0;
  wire pp_1_0_0;
  wire pp_1_1_0;
  wire pp_1_1_1;
  wire pp_1_2_0;
  wire pp_1_2_1;
  wire pp_1_3_0;
  wire pp_1_3_1;
  wire pp_1_3_2;
  wire pp_1_4_0;
  wire pp_1_4_1;
  wire pp_1_4_2;
  wire pp_1_4_3;
  wire pp_1_5_0;
  wire pp_1_5_1;
  wire pp_1_5_2;
  wire pp_1_6_0;
  wire pp_1_6_1;
  wire pp_1_6_2;
  wire pp_1_6_3;
  wire pp_1_6_4;
  wire pp_1_7_0;
  wire pp_1_7_1;
  wire pp_1_7_2;
  wire pp_1_7_3;
  wire pp_1_7_4;
  wire pp_1_7_5;
  wire pp_1_8_0;
  wire pp_1_8_1;
  wire pp_1_8_2;
  wire pp_1_8_3;
  wire pp_1_8_4;
  wire pp_1_8_5;
  wire pp_1_9_0;
  wire pp_1_9_1;
  wire pp_1_9_2;
  wire pp_1_9_3;
  wire pp_1_9_4;
  wire pp_1_9_5;
  wire pp_1_9_6;
  wire pp_1_9_7;
  wire pp_1_10_0;
  wire pp_1_10_1;
  wire pp_1_10_2;
  wire pp_1_11_0;
  wire pp_1_11_1;
  wire pp_1_11_2;
  wire pp_1_12_0;
  wire pp_1_12_1;
  wire pp_1_13_0;
  wire pp_1_13_1;
  wire pp_1_13_2;
  wire pp_1_14_0;
  wire pp_2_0_0;
  wire pp_2_1_0;
  wire pp_2_1_1;
  wire pp_2_2_0;
  wire pp_2_2_1;
  wire pp_2_3_0;
  wire pp_2_3_1;
  wire pp_2_4_0;
  wire pp_2_4_1;
  wire pp_2_4_2;
  wire pp_2_5_0;
  wire pp_2_5_1;
  wire pp_2_6_0;
  wire pp_2_6_1;
  wire pp_2_6_2;
  wire pp_2_7_0;
  wire pp_2_7_1;
  wire pp_2_7_2;
  wire pp_2_7_3;
  wire pp_2_8_0;
  wire pp_2_8_1;
  wire pp_2_8_2;
  wire pp_2_8_3;
  wire pp_2_9_0;
  wire pp_2_9_1;
  wire pp_2_9_2;
  wire pp_2_9_3;
  wire pp_2_9_4;
  wire pp_2_9_5;
  wire pp_2_10_0;
  wire pp_2_10_1;
  wire pp_2_10_2;
  wire pp_2_11_0;
  wire pp_2_11_1;
  wire pp_2_12_0;
  wire pp_2_12_1;
  wire pp_2_12_2;
  wire pp_2_13_0;
  wire pp_2_14_0;
  wire pp_2_14_1;
  wire pp_3_0_0;
  wire pp_3_1_0;
  wire pp_3_1_1;
  wire pp_3_2_0;
  wire pp_3_2_1;
  wire pp_3_3_0;
  wire pp_3_3_1;
  wire pp_3_4_0;
  wire pp_3_4_1;
  wire pp_3_5_0;
  wire pp_3_5_1;
  wire pp_3_5_2;
  wire pp_3_6_0;
  wire pp_3_6_1;
  wire pp_3_6_2;
  wire pp_3_7_0;
  wire pp_3_7_1;
  wire pp_3_7_2;
  wire pp_3_8_0;
  wire pp_3_8_1;
  wire pp_3_8_2;
  wire pp_3_9_0;
  wire pp_3_9_1;
  wire pp_3_9_2;
  wire pp_3_10_0;
  wire pp_3_10_1;
  wire pp_3_10_2;
  wire pp_3_11_0;
  wire pp_3_11_1;
  wire pp_3_11_2;
  wire pp_3_12_0;
  wire pp_3_13_0;
  wire pp_3_13_1;
  wire pp_3_14_0;
  wire pp_3_14_1;
  wire pp_4_0_0;
  wire pp_4_1_0;
  wire pp_4_1_1;
  wire pp_4_2_0;
  wire pp_4_2_1;
  wire pp_4_3_0;
  wire pp_4_3_1;
  wire pp_4_4_0;
  wire pp_4_4_1;
  wire pp_4_5_0;
  wire pp_4_5_1;
  wire pp_4_6_0;
  wire pp_4_6_1;
  wire pp_4_7_0;
  wire pp_4_7_1;
  wire pp_4_8_0;
  wire pp_4_8_1;
  wire pp_4_9_0;
  wire pp_4_9_1;
  wire pp_4_10_0;
  wire pp_4_10_1;
  wire pp_4_11_0;
  wire pp_4_11_1;
  wire pp_4_12_0;
  wire pp_4_12_1;
  wire pp_4_13_0;
  wire pp_4_13_1;
  wire pp_4_14_0;
  wire pp_4_14_1;
  assign pp_0_0_0 = pp_0_0;
  assign pp_0_1_0 = pp_0_1;
  assign pp_0_1_1 = pp_1_1;
  assign pp_0_2_0 = pp_0_2;
  assign pp_0_2_1 = pp_1_2;
  assign pp_0_2_2 = pp_2_2;
  assign pp_0_3_0 = pp_0_3;
  assign pp_0_3_1 = pp_1_3;
  assign pp_0_3_2 = pp_2_3;
  assign pp_0_3_3 = pp_3_3;
  assign pp_0_4_0 = pp_0_4;
  assign pp_0_4_1 = pp_1_4;
  assign pp_0_4_2 = pp_2_4;
  assign pp_0_4_3 = pp_3_4;
  assign pp_0_4_4 = pp_4_4;
  assign pp_0_5_0 = pp_0_5;
  assign pp_0_5_1 = pp_1_5;
  assign pp_0_5_2 = pp_2_5;
  assign pp_0_5_3 = pp_3_5;
  assign pp_0_5_4 = pp_4_5;
  assign pp_0_5_5 = pp_5_5;
  assign pp_0_6_0 = pp_0_6;
  assign pp_0_6_1 = pp_1_6;
  assign pp_0_6_2 = pp_2_6;
  assign pp_0_6_3 = pp_3_6;
  assign pp_0_6_4 = pp_4_6;
  assign pp_0_6_5 = pp_5_6;
  assign pp_0_6_6 = pp_6_6;
  assign pp_0_7_0 = pp_0_7;
  assign pp_0_7_1 = pp_1_7;
  assign pp_0_7_2 = pp_2_7;
  assign pp_0_7_3 = pp_3_7;
  assign pp_0_7_4 = pp_4_7;
  assign pp_0_7_5 = pp_5_7;
  assign pp_0_7_6 = pp_6_7;
  assign pp_0_7_7 = pp_7_7;
  assign pp_0_8_0 = pp_1_8;
  assign pp_0_8_1 = pp_2_8;
  assign pp_0_8_2 = pp_3_8;
  assign pp_0_8_3 = pp_4_8;
  assign pp_0_8_4 = pp_5_8;
  assign pp_0_8_5 = pp_6_8;
  assign pp_0_8_6 = pp_7_8;
  assign pp_0_9_0 = pp_2_9;
  assign pp_0_9_1 = pp_3_9;
  assign pp_0_9_2 = pp_4_9;
  assign pp_0_9_3 = pp_5_9;
  assign pp_0_9_4 = pp_6_9;
  assign pp_0_9_5 = pp_7_9;
  assign pp_0_10_0 = pp_3_10;
  assign pp_0_10_1 = pp_4_10;
  assign pp_0_10_2 = pp_5_10;
  assign pp_0_10_3 = pp_6_10;
  assign pp_0_10_4 = pp_7_10;
  assign pp_0_11_0 = pp_4_11;
  assign pp_0_11_1 = pp_5_11;
  assign pp_0_11_2 = pp_6_11;
  assign pp_0_11_3 = pp_7_11;
  assign pp_0_12_0 = pp_5_12;
  assign pp_0_12_1 = pp_6_12;
  assign pp_0_12_2 = pp_7_12;
  assign pp_0_13_0 = pp_6_13;
  assign pp_0_13_1 = pp_7_13;
  assign pp_0_14_0 = pp_7_14;

  assign pp_1_0_0 = pp_0_0_0;
  assign pp_1_1_0 = pp_0_1_0;
  assign pp_1_1_1 = pp_0_1_1;
  MG_HA ha_0_2_0(
    .a(pp_0_2_0),
    .b(pp_0_2_1),
    .sum(pp_1_2_0),
    .cout(pp_1_3_0)
  );

  assign pp_1_2_1 = pp_0_2_2;
  MG_FA fa_0_3_0(
    .a(pp_0_3_0),
    .b(pp_0_3_1),
    .cin(pp_0_3_2),
    .sum(pp_1_3_1),
    .cout(pp_1_4_0)
  );

  assign pp_1_3_2 = pp_0_3_3;
  MG_FA fa_0_4_0(
    .a(pp_0_4_0),
    .b(pp_0_4_1),
    .cin(pp_0_4_2),
    .sum(pp_1_4_1),
    .cout(pp_1_5_0)
  );

  assign pp_1_4_2 = pp_0_4_3;
  assign pp_1_4_3 = pp_0_4_4;
  MG_FA fa_0_5_0(
    .a(pp_0_5_0),
    .b(pp_0_5_1),
    .cin(pp_0_5_2),
    .sum(pp_1_5_1),
    .cout(pp_1_6_0)
  );

  MG_FA fa_0_5_1(
    .a(pp_0_5_3),
    .b(pp_0_5_4),
    .cin(pp_0_5_5),
    .sum(pp_1_5_2),
    .cout(pp_1_6_1)
  );

  MG_FA fa_0_6_0(
    .a(pp_0_6_0),
    .b(pp_0_6_1),
    .cin(pp_0_6_2),
    .sum(pp_1_6_2),
    .cout(pp_1_7_0)
  );

  MG_FA fa_0_6_1(
    .a(pp_0_6_3),
    .b(pp_0_6_4),
    .cin(pp_0_6_5),
    .sum(pp_1_6_3),
    .cout(pp_1_7_1)
  );

  assign pp_1_6_4 = pp_0_6_6;
  MG_FA fa_0_7_0(
    .a(pp_0_7_0),
    .b(pp_0_7_1),
    .cin(pp_0_7_2),
    .sum(pp_1_7_2),
    .cout(pp_1_8_0)
  );

  MG_FA fa_0_7_1(
    .a(pp_0_7_3),
    .b(pp_0_7_4),
    .cin(pp_0_7_5),
    .sum(pp_1_7_3),
    .cout(pp_1_8_1)
  );

  assign pp_1_7_4 = pp_0_7_6;
  assign pp_1_7_5 = pp_0_7_7;
  MG_FA fa_0_8_0(
    .a(pp_0_8_0),
    .b(pp_0_8_1),
    .cin(pp_0_8_2),
    .sum(pp_1_8_2),
    .cout(pp_1_9_0)
  );

  MG_HA ha_0_8_1(
    .a(pp_0_8_3),
    .b(pp_0_8_4),
    .sum(pp_1_8_3),
    .cout(pp_1_9_1)
  );

  assign pp_1_8_4 = pp_0_8_5;
  assign pp_1_8_5 = pp_0_8_6;
  assign pp_1_9_2 = pp_0_9_0;
  assign pp_1_9_3 = pp_0_9_1;
  assign pp_1_9_4 = pp_0_9_2;
  assign pp_1_9_5 = pp_0_9_3;
  assign pp_1_9_6 = pp_0_9_4;
  assign pp_1_9_7 = pp_0_9_5;
  MG_FA fa_0_10_0(
    .a(pp_0_10_0),
    .b(pp_0_10_1),
    .cin(pp_0_10_2),
    .sum(pp_1_10_0),
    .cout(pp_1_11_0)
  );

  assign pp_1_10_1 = pp_0_10_3;
  assign pp_1_10_2 = pp_0_10_4;
  MG_FA fa_0_11_0(
    .a(pp_0_11_0),
    .b(pp_0_11_1),
    .cin(pp_0_11_2),
    .sum(pp_1_11_1),
    .cout(pp_1_12_0)
  );

  assign pp_1_11_2 = pp_0_11_3;
  MG_FA fa_0_12_0(
    .a(pp_0_12_0),
    .b(pp_0_12_1),
    .cin(pp_0_12_2),
    .sum(pp_1_12_1),
    .cout(pp_1_13_0)
  );

  assign pp_1_13_1 = pp_0_13_0;
  assign pp_1_13_2 = pp_0_13_1;
  assign pp_1_14_0 = pp_0_14_0;
  assign pp_2_0_0 = pp_1_0_0;
  assign pp_2_1_0 = pp_1_1_0;
  assign pp_2_1_1 = pp_1_1_1;
  assign pp_2_2_0 = pp_1_2_0;
  assign pp_2_2_1 = pp_1_2_1;
  MG_HA ha_1_3_0(
    .a(pp_1_3_0),
    .b(pp_1_3_1),
    .sum(pp_2_3_0),
    .cout(pp_2_4_0)
  );

  assign pp_2_3_1 = pp_1_3_2;
  MG_FA fa_1_4_0(
    .a(pp_1_4_0),
    .b(pp_1_4_1),
    .cin(pp_1_4_2),
    .sum(pp_2_4_1),
    .cout(pp_2_5_0)
  );

  assign pp_2_4_2 = pp_1_4_3;
  MG_FA fa_1_5_0(
    .a(pp_1_5_0),
    .b(pp_1_5_1),
    .cin(pp_1_5_2),
    .sum(pp_2_5_1),
    .cout(pp_2_6_0)
  );

  MG_FA fa_1_6_0(
    .a(pp_1_6_0),
    .b(pp_1_6_1),
    .cin(pp_1_6_2),
    .sum(pp_2_6_1),
    .cout(pp_2_7_0)
  );

  MG_HA ha_1_6_1(
    .a(pp_1_6_3),
    .b(pp_1_6_4),
    .sum(pp_2_6_2),
    .cout(pp_2_7_1)
  );

  MG_FA fa_1_7_0(
    .a(pp_1_7_0),
    .b(pp_1_7_1),
    .cin(pp_1_7_2),
    .sum(pp_2_7_2),
    .cout(pp_2_8_0)
  );

  MG_FA fa_1_7_1(
    .a(pp_1_7_3),
    .b(pp_1_7_4),
    .cin(pp_1_7_5),
    .sum(pp_2_7_3),
    .cout(pp_2_8_1)
  );

  MG_FA fa_1_8_0(
    .a(pp_1_8_0),
    .b(pp_1_8_1),
    .cin(pp_1_8_2),
    .sum(pp_2_8_2),
    .cout(pp_2_9_0)
  );

  MG_FA fa_1_8_1(
    .a(pp_1_8_3),
    .b(pp_1_8_4),
    .cin(pp_1_8_5),
    .sum(pp_2_8_3),
    .cout(pp_2_9_1)
  );

  MG_FA fa_1_9_0(
    .a(pp_1_9_0),
    .b(pp_1_9_1),
    .cin(pp_1_9_2),
    .sum(pp_2_9_2),
    .cout(pp_2_10_0)
  );

  MG_FA fa_1_9_1(
    .a(pp_1_9_3),
    .b(pp_1_9_4),
    .cin(pp_1_9_5),
    .sum(pp_2_9_3),
    .cout(pp_2_10_1)
  );

  assign pp_2_9_4 = pp_1_9_6;
  assign pp_2_9_5 = pp_1_9_7;
  MG_FA fa_1_10_0(
    .a(pp_1_10_2),
    .b(pp_1_10_1),
    .cin(pp_1_10_0),
    .sum(pp_2_10_2),
    .cout(pp_2_11_0)
  );

  MG_FA fa_1_11_0(
    .a(pp_1_11_0),
    .b(pp_1_11_1),
    .cin(pp_1_11_2),
    .sum(pp_2_11_1),
    .cout(pp_2_12_0)
  );

  assign pp_2_12_1 = pp_1_12_0;
  assign pp_2_12_2 = pp_1_12_1;
  MG_FA fa_1_13_0(
    .a(pp_1_13_0),
    .b(pp_1_13_1),
    .cin(pp_1_13_2),
    .sum(pp_2_13_0),
    .cout(pp_2_14_0)
  );

  assign pp_2_14_1 = pp_1_14_0;
  assign pp_3_0_0 = pp_2_0_0;
  assign pp_3_1_0 = pp_2_1_0;
  assign pp_3_1_1 = pp_2_1_1;
  assign pp_3_2_0 = pp_2_2_0;
  assign pp_3_2_1 = pp_2_2_1;
  assign pp_3_3_0 = pp_2_3_0;
  assign pp_3_3_1 = pp_2_3_1;
  MG_HA ha_2_4_0(
    .a(pp_2_4_0),
    .b(pp_2_4_1),
    .sum(pp_3_4_0),
    .cout(pp_3_5_0)
  );

  assign pp_3_4_1 = pp_2_4_2;
  assign pp_3_5_1 = pp_2_5_0;
  assign pp_3_5_2 = pp_2_5_1;
  assign pp_3_6_0 = pp_2_6_0;
  assign pp_3_6_1 = pp_2_6_1;
  assign pp_3_6_2 = pp_2_6_2;
  MG_HA ha_2_7_0(
    .a(pp_2_7_0),
    .b(pp_2_7_1),
    .sum(pp_3_7_0),
    .cout(pp_3_8_0)
  );

  assign pp_3_7_1 = pp_2_7_2;
  assign pp_3_7_2 = pp_2_7_3;
  MG_FA fa_2_8_0(
    .a(pp_2_8_0),
    .b(pp_2_8_1),
    .cin(pp_2_8_2),
    .sum(pp_3_8_1),
    .cout(pp_3_9_0)
  );

  assign pp_3_8_2 = pp_2_8_3;
  MG_FA fa_2_9_0(
    .a(pp_2_9_4),
    .b(pp_2_9_1),
    .cin(pp_2_9_2),
    .sum(pp_3_9_1),
    .cout(pp_3_10_0)
  );

  MG_FA fa_2_9_1(
    .a(pp_2_9_3),
    .b(pp_2_9_0),
    .cin(pp_2_9_5),
    .sum(pp_3_9_2),
    .cout(pp_3_10_1)
  );

  MG_FA fa_2_10_0(
    .a(pp_2_10_0),
    .b(pp_2_10_1),
    .cin(pp_2_10_2),
    .sum(pp_3_10_2),
    .cout(pp_3_11_0)
  );

  assign pp_3_11_1 = pp_2_11_0;
  assign pp_3_11_2 = pp_2_11_1;
  MG_FA fa_2_12_0(
    .a(pp_2_12_0),
    .b(pp_2_12_1),
    .cin(pp_2_12_2),
    .sum(pp_3_12_0),
    .cout(pp_3_13_0)
  );

  assign pp_3_13_1 = pp_2_13_0;
  assign pp_3_14_0 = pp_2_14_0;
  assign pp_3_14_1 = pp_2_14_1;
  assign pp_4_0_0 = pp_3_0_0;
  assign pp_4_1_0 = pp_3_1_0;
  assign pp_4_1_1 = pp_3_1_1;
  assign pp_4_2_0 = pp_3_2_0;
  assign pp_4_2_1 = pp_3_2_1;
  assign pp_4_3_0 = pp_3_3_0;
  assign pp_4_3_1 = pp_3_3_1;
  assign pp_4_4_0 = pp_3_4_0;
  assign pp_4_4_1 = pp_3_4_1;
  MG_HA ha_3_5_0(
    .a(pp_3_5_0),
    .b(pp_3_5_1),
    .sum(pp_4_5_0),
    .cout(pp_4_6_0)
  );

  assign pp_4_5_1 = pp_3_5_2;
  MG_FA fa_3_6_0(
    .a(pp_3_6_0),
    .b(pp_3_6_1),
    .cin(pp_3_6_2),
    .sum(pp_4_6_1),
    .cout(pp_4_7_0)
  );

  MG_FA fa_3_7_0(
    .a(pp_3_7_0),
    .b(pp_3_7_1),
    .cin(pp_3_7_2),
    .sum(pp_4_7_1),
    .cout(pp_4_8_0)
  );

  MG_FA fa_3_8_0(
    .a(pp_3_8_0),
    .b(pp_3_8_2),
    .cin(pp_3_8_1),
    .sum(pp_4_8_1),
    .cout(pp_4_9_0)
  );

  MG_FA fa_3_9_0(
    .a(pp_3_9_0),
    .b(pp_3_9_1),
    .cin(pp_3_9_2),
    .sum(pp_4_9_1),
    .cout(pp_4_10_0)
  );

  MG_FA fa_3_10_0(
    .a(pp_3_10_0),
    .b(pp_3_10_1),
    .cin(pp_3_10_2),
    .sum(pp_4_10_1),
    .cout(pp_4_11_0)
  );

  MG_FA fa_3_11_0(
    .a(pp_3_11_0),
    .b(pp_3_11_1),
    .cin(pp_3_11_2),
    .sum(pp_4_11_1),
    .cout(pp_4_12_0)
  );

  assign pp_4_12_1 = pp_3_12_0;
  assign pp_4_13_0 = pp_3_13_0;
  assign pp_4_13_1 = pp_3_13_1;
  assign pp_4_14_0 = pp_3_14_0;
  assign pp_4_14_1 = pp_3_14_1;
  wire [13:0] cta;
  wire [13:0] ctb;
  wire [13:0] cts;
  wire ctc;

  MG_CPA cpa(
 .a(cta), .b(ctb), .sum(cts), .cout(ctc)
  );

  assign cta[0] = pp_4_1_0;
  assign ctb[0] = pp_4_1_1;
  assign cta[1] = pp_4_2_0;
  assign ctb[1] = pp_4_2_1;
  assign cta[2] = pp_4_3_0;
  assign ctb[2] = pp_4_3_1;
  assign cta[3] = pp_4_4_0;
  assign ctb[3] = pp_4_4_1;
  assign cta[4] = pp_4_5_0;
  assign ctb[4] = pp_4_5_1;
  assign cta[5] = pp_4_6_0;
  assign ctb[5] = pp_4_6_1;
  assign cta[6] = pp_4_7_0;
  assign ctb[6] = pp_4_7_1;
  assign cta[7] = pp_4_8_0;
  assign ctb[7] = pp_4_8_1;
  assign cta[8] = pp_4_9_0;
  assign ctb[8] = pp_4_9_1;
  assign cta[9] = pp_4_10_0;
  assign ctb[9] = pp_4_10_1;
  assign cta[10] = pp_4_11_0;
  assign ctb[10] = pp_4_11_1;
  assign cta[11] = pp_4_12_0;
  assign ctb[11] = pp_4_12_1;
  assign cta[12] = pp_4_13_0;
  assign ctb[12] = pp_4_13_1;
  assign cta[13] = pp_4_14_0;
  assign ctb[13] = pp_4_14_1;
  assign product[0] = pp_4_0_0;
  assign product[14:1] = cts;
  assign product[15] = ctc;
endmodule
