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
module mult4u_normal_brentkung(
  input [3:0] multiplicand,
  input [3:0] multiplier,
  output [7:0] product
);

  wire pp_0_0;
  wire pp_0_1;
  wire pp_0_2;
  wire pp_0_3;
  wire pp_1_1;
  wire pp_1_2;
  wire pp_1_3;
  wire pp_1_4;
  wire pp_2_2;
  wire pp_2_3;
  wire pp_2_4;
  wire pp_2_5;
  wire pp_3_3;
  wire pp_3_4;
  wire pp_3_5;
  wire pp_3_6;
  assign pp_0_0 = multiplicand[0] & multiplier[0];
  assign pp_0_1 = multiplicand[1] & multiplier[0];
  assign pp_0_2 = multiplicand[2] & multiplier[0];
  assign pp_0_3 = multiplicand[3] & multiplier[0];
  assign pp_1_1 = multiplicand[0] & multiplier[1];
  assign pp_1_2 = multiplicand[1] & multiplier[1];
  assign pp_1_3 = multiplicand[2] & multiplier[1];
  assign pp_1_4 = multiplicand[3] & multiplier[1];
  assign pp_2_2 = multiplicand[0] & multiplier[2];
  assign pp_2_3 = multiplicand[1] & multiplier[2];
  assign pp_2_4 = multiplicand[2] & multiplier[2];
  assign pp_2_5 = multiplicand[3] & multiplier[2];
  assign pp_3_3 = multiplicand[0] & multiplier[3];
  assign pp_3_4 = multiplicand[1] & multiplier[3];
  assign pp_3_5 = multiplicand[2] & multiplier[3];
  assign pp_3_6 = multiplicand[3] & multiplier[3];
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
  wire pp_0_5_0;
  wire pp_0_5_1;
  wire pp_0_6_0;
  wire pp_1_0_0;
  wire pp_1_1_0;
  wire pp_1_1_1;
  wire pp_1_2_0;
  wire pp_1_2_1;
  wire pp_1_3_0;
  wire pp_1_3_1;
  wire pp_1_3_2;
  wire pp_1_3_3;
  wire pp_1_4_0;
  wire pp_1_4_1;
  wire pp_1_5_0;
  wire pp_1_5_1;
  wire pp_1_5_2;
  wire pp_1_6_0;
  wire pp_2_0_0;
  wire pp_2_1_0;
  wire pp_2_1_1;
  wire pp_2_2_0;
  wire pp_2_2_1;
  wire pp_2_3_0;
  wire pp_2_3_1;
  wire pp_2_4_0;
  wire pp_2_4_1;
  wire pp_2_5_0;
  wire pp_2_5_1;
  wire pp_2_6_0;
  wire pp_2_6_1;
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
  assign pp_0_4_0 = pp_1_4;
  assign pp_0_4_1 = pp_2_4;
  assign pp_0_4_2 = pp_3_4;
  assign pp_0_5_0 = pp_2_5;
  assign pp_0_5_1 = pp_3_5;
  assign pp_0_6_0 = pp_3_6;

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
  MG_HA ha_0_3_0(
    .a(pp_0_3_0),
    .b(pp_0_3_1),
    .sum(pp_1_3_1),
    .cout(pp_1_4_0)
  );

  assign pp_1_3_2 = pp_0_3_2;
  assign pp_1_3_3 = pp_0_3_3;
  MG_FA fa_0_4_0(
    .a(pp_0_4_0),
    .b(pp_0_4_1),
    .cin(pp_0_4_2),
    .sum(pp_1_4_1),
    .cout(pp_1_5_0)
  );

  assign pp_1_5_1 = pp_0_5_0;
  assign pp_1_5_2 = pp_0_5_1;
  assign pp_1_6_0 = pp_0_6_0;
  assign pp_2_0_0 = pp_1_0_0;
  assign pp_2_1_0 = pp_1_1_0;
  assign pp_2_1_1 = pp_1_1_1;
  assign pp_2_2_0 = pp_1_2_0;
  assign pp_2_2_1 = pp_1_2_1;
  MG_FA fa_1_3_0(
    .a(pp_1_3_3),
    .b(pp_1_3_1),
    .cin(pp_1_3_2),
    .sum(pp_2_3_0),
    .cout(pp_2_4_0)
  );

  assign pp_2_3_1 = pp_1_3_0;
  MG_HA ha_1_4_0(
    .a(pp_1_4_0),
    .b(pp_1_4_1),
    .sum(pp_2_4_1),
    .cout(pp_2_5_0)
  );

  MG_FA fa_1_5_0(
    .a(pp_1_5_0),
    .b(pp_1_5_1),
    .cin(pp_1_5_2),
    .sum(pp_2_5_1),
    .cout(pp_2_6_0)
  );

  assign pp_2_6_1 = pp_1_6_0;
  wire [5:0] cta;
  wire [5:0] ctb;
  wire [5:0] cts;
  wire ctc;

  MG_CPA cpa(
 .a(cta), .b(ctb), .sum(cts), .cout(ctc)
  );

  assign cta[0] = pp_2_1_0;
  assign ctb[0] = pp_2_1_1;
  assign cta[1] = pp_2_2_0;
  assign ctb[1] = pp_2_2_1;
  assign cta[2] = pp_2_3_0;
  assign ctb[2] = pp_2_3_1;
  assign cta[3] = pp_2_4_0;
  assign ctb[3] = pp_2_4_1;
  assign cta[4] = pp_2_5_0;
  assign ctb[4] = pp_2_5_1;
  assign cta[5] = pp_2_6_0;
  assign ctb[5] = pp_2_6_1;
  assign product[0] = pp_2_0_0;
  assign product[6:1] = cts;
  assign product[7] = ctc;
endmodule
