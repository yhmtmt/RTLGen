IVERILOG=iverilog
VVP=vvp

TOP=npu_top
OUT=build_npu_shell.vvp
OUT_AXI=build_npu_axi.vvp
OUT_AXI_MULTI=build_npu_axi_multi.vvp
BYTES?=

RTL=npu/rtlgen/out/top.v
RTL_AXI=npu/rtlgen/out/top_axi.v npu/rtlgen/out/axi_lite_mmio_bridge.sv
MODEL=npu/sim/rtl/axi_mem_model.sv
TB=npu/sim/rtl/tb_npu_shell.sv
TB_AXI=npu/sim/rtl/tb_axi_lite_mmio.sv
TB_AXI_MULTI=npu/sim/rtl/tb_axi_lite_multi.sv

.PHONY: gen build run run-axi run-axi-multi status clean

gen:
	python3 npu/rtlgen/gen.py --config npu/rtlgen/examples/minimal.json --out npu/rtlgen/out

build: gen
	$(IVERILOG) -g2012 -s tb_npu_shell -o $(OUT) $(RTL) $(TB) $(MODEL)

run: build
	$(VVP) $(OUT) $(if $(BYTES),+bytes=$(BYTES),)

run-axi: gen
	$(IVERILOG) -g2012 -s tb_axi_lite_mmio -o $(OUT_AXI) $(RTL) $(RTL_AXI) $(TB_AXI) $(MODEL)
	$(VVP) $(OUT_AXI)

run-axi-multi: gen
	$(IVERILOG) -g2012 -s tb_axi_lite_multi -o $(OUT_AXI_MULTI) $(RTL) $(RTL_AXI) $(TB_AXI_MULTI) $(MODEL)
	$(VVP) $(OUT_AXI_MULTI)

status:
	python3 npu/docs/update_status.py

clean:
	rm -f $(OUT)
