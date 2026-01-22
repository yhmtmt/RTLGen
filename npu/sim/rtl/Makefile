IVERILOG=iverilog
VVP=vvp

TOP=npu_top
OUT=build_npu_shell.vvp
OUT_AXI=build_npu_axi.vvp
BYTES?=

RTL=npu/rtlgen/out/top.v
RTL_AXI=npu/rtlgen/out/top_axi.v npu/rtlgen/out/axi_lite_mmio_bridge.sv
MODEL=npu/sim/rtl/axi_mem_model.sv
TB=npu/sim/rtl/tb_npu_shell.sv
TB_AXI=npu/sim/rtl/tb_axi_lite_mmio.sv

.PHONY: gen build run run-axi status clean

gen:
	python3 npu/rtlgen/gen.py --config npu/rtlgen/examples/minimal.json --out npu/rtlgen/out

build: gen
	$(IVERILOG) -g2012 -s tb_npu_shell -o $(OUT) $(RTL) $(TB) $(MODEL)

run: build
	$(VVP) $(OUT) $(if $(BYTES),+bytes=$(BYTES),)

run-axi: gen
	$(IVERILOG) -g2012 -s tb_axi_lite_mmio -o $(OUT_AXI) $(RTL) $(RTL_AXI) $(TB_AXI) $(MODEL)
	$(VVP) $(OUT_AXI)

status:
	python3 npu/docs/update_status.py

clean:
	rm -f $(OUT)
