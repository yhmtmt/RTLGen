IVERILOG=iverilog
IVERILOGFLAGS=-g2012 -I npu/rtlgen/out
VVP=vvp

TOP=npu_top
OUT=build_npu_shell.vvp
OUT_AXI=build_npu_axi.vvp
OUT_AXI_MULTI=build_npu_axi_multi.vvp
BYTES?=
BIN?=
VVPFLAGS?=

ARCH?=npu/arch/examples/minimal.yml
CONFIG?=npu/rtlgen/examples/minimal.json
RTL=npu/rtlgen/out/top.v
RTL_AXI=npu/rtlgen/out/top_axi.v npu/rtlgen/out/axi_lite_mmio_bridge.sv
SRAM_MODELS=$(wildcard npu/rtlgen/out/sram_models.sv)
ROUTER=npu/sim/rtl/axi_mem_router.sv
MODEL=npu/sim/rtl/axi_mem_model.sv
TB=npu/sim/rtl/tb_npu_shell.sv
TB_AXI=npu/sim/rtl/tb_axi_lite_mmio.sv
TB_AXI_MULTI=npu/sim/rtl/tb_axi_lite_multi.sv
NOC_FIFO=npu/sim/rtl/noc_ready_valid_fifo.sv
NOC_ROUTER=npu/sim/rtl/noc_ready_valid_router.sv
VALUE_SERVICE=npu/sim/rtl/banked_value_memory_service.sv
TB_NOC_ROUTER=npu/sim/rtl/tb_noc_ready_valid_router.sv
TB_VALUE_SERVICE=npu/sim/rtl/tb_banked_value_memory_service.sv
OUT_NOC_ROUTER=build_noc_router.vvp
OUT_VALUE_SERVICE=build_value_service.vvp

.PHONY: gen gen-arch build run run-axi run-axi-multi run-arch run-axi-arch run-axi-multi-arch run-arch-sram run-axi-arch-sram run-axi-multi-arch-sram run-arch-event run-axi-arch-event run-axi-multi-arch-event run-noc-router-rr-128 run-noc-router-local-128 run-noc-router-local-256 run-value-service-128 run-value-service-256 status clean

gen:
	python3 npu/rtlgen/gen.py --config $(CONFIG) --out npu/rtlgen/out

gen-arch:
	python3 npu/arch/to_rtlgen.py $(ARCH) --out $(CONFIG)
	python3 npu/rtlgen/gen.py --config $(CONFIG) --out npu/rtlgen/out

build: gen
	$(IVERILOG) $(IVERILOGFLAGS) -s tb_npu_shell -o $(OUT) $(RTL) $(TB) $(ROUTER) $(MODEL) $(SRAM_MODELS)

run: build
	$(VVP) $(OUT) $(if $(BYTES),+bytes=$(BYTES),) $(if $(BIN),+bin=$(BIN),) $(VVPFLAGS)

run-arch: gen-arch
	$(IVERILOG) $(IVERILOGFLAGS) -s tb_npu_shell -o $(OUT) $(RTL) $(TB) $(ROUTER) $(MODEL) $(SRAM_MODELS)
	$(VVP) $(OUT) $(if $(BYTES),+bytes=$(BYTES),)

run-arch-sram: gen-arch
	$(IVERILOG) $(IVERILOGFLAGS) -s tb_npu_shell -o $(OUT) $(RTL) $(TB) $(ROUTER) $(MODEL) $(SRAM_MODELS)
	$(VVP) $(OUT) +sram_test=1

run-arch-event: gen-arch
	$(IVERILOG) $(IVERILOGFLAGS) -s tb_npu_shell -o $(OUT) $(RTL) $(TB) $(ROUTER) $(MODEL) $(SRAM_MODELS)
	$(VVP) $(OUT) +event_test=1

run-axi: gen
	$(IVERILOG) $(IVERILOGFLAGS) -s tb_axi_lite_mmio -o $(OUT_AXI) $(RTL) $(RTL_AXI) $(TB_AXI) $(ROUTER) $(MODEL) $(SRAM_MODELS)
	$(VVP) $(OUT_AXI)

run-axi-arch: gen-arch
	$(IVERILOG) $(IVERILOGFLAGS) -s tb_axi_lite_mmio -o $(OUT_AXI) $(RTL) $(RTL_AXI) $(TB_AXI) $(ROUTER) $(MODEL) $(SRAM_MODELS)
	$(VVP) $(OUT_AXI)

run-axi-arch-sram: gen-arch
	$(IVERILOG) $(IVERILOGFLAGS) -s tb_axi_lite_mmio -o $(OUT_AXI) $(RTL) $(RTL_AXI) $(TB_AXI) $(ROUTER) $(MODEL) $(SRAM_MODELS)
	$(VVP) $(OUT_AXI) +sram_test=1

run-axi-arch-event: gen-arch
	$(IVERILOG) $(IVERILOGFLAGS) -s tb_axi_lite_mmio -o $(OUT_AXI) $(RTL) $(RTL_AXI) $(TB_AXI) $(ROUTER) $(MODEL) $(SRAM_MODELS)
	$(VVP) $(OUT_AXI) +event_test=1

run-axi-multi: gen
	$(IVERILOG) $(IVERILOGFLAGS) -s tb_axi_lite_multi -o $(OUT_AXI_MULTI) $(RTL) $(RTL_AXI) $(TB_AXI_MULTI) $(ROUTER) $(MODEL) $(SRAM_MODELS)
	$(VVP) $(OUT_AXI_MULTI)

run-axi-multi-arch: gen-arch
	$(IVERILOG) $(IVERILOGFLAGS) -s tb_axi_lite_multi -o $(OUT_AXI_MULTI) $(RTL) $(RTL_AXI) $(TB_AXI_MULTI) $(ROUTER) $(MODEL) $(SRAM_MODELS)
	$(VVP) $(OUT_AXI_MULTI)

run-axi-multi-arch-sram: gen-arch
	$(IVERILOG) $(IVERILOGFLAGS) -s tb_axi_lite_multi -o $(OUT_AXI_MULTI) $(RTL) $(RTL_AXI) $(TB_AXI_MULTI) $(ROUTER) $(MODEL) $(SRAM_MODELS)
	$(VVP) $(OUT_AXI_MULTI) +sram_test=1

run-axi-multi-arch-event: gen-arch
	$(IVERILOG) $(IVERILOGFLAGS) -s tb_axi_lite_multi -o $(OUT_AXI_MULTI) $(RTL) $(RTL_AXI) $(TB_AXI_MULTI) $(ROUTER) $(MODEL) $(SRAM_MODELS)
	$(VVP) $(OUT_AXI_MULTI) +event_test=1

run-noc-router-rr-128:
	$(IVERILOG) $(IVERILOGFLAGS) -P tb_noc_ready_valid_router.PACKET_W=128 -P tb_noc_ready_valid_router.ARB_MODE=0 -s tb_noc_ready_valid_router -o $(OUT_NOC_ROUTER) $(NOC_FIFO) $(NOC_ROUTER) $(TB_NOC_ROUTER)
	$(VVP) $(OUT_NOC_ROUTER)

run-noc-router-local-128:
	$(IVERILOG) $(IVERILOGFLAGS) -P tb_noc_ready_valid_router.PACKET_W=128 -P tb_noc_ready_valid_router.ARB_MODE=1 -s tb_noc_ready_valid_router -o $(OUT_NOC_ROUTER) $(NOC_FIFO) $(NOC_ROUTER) $(TB_NOC_ROUTER)
	$(VVP) $(OUT_NOC_ROUTER)

run-noc-router-local-256:
	$(IVERILOG) $(IVERILOGFLAGS) -P tb_noc_ready_valid_router.PACKET_W=256 -P tb_noc_ready_valid_router.ARB_MODE=1 -s tb_noc_ready_valid_router -o $(OUT_NOC_ROUTER) $(NOC_FIFO) $(NOC_ROUTER) $(TB_NOC_ROUTER)
	$(VVP) $(OUT_NOC_ROUTER)

run-value-service-128:
	$(IVERILOG) $(IVERILOGFLAGS) -P tb_banked_value_memory_service.PACKET_W=128 -s tb_banked_value_memory_service -o $(OUT_VALUE_SERVICE) $(NOC_FIFO) $(NOC_ROUTER) $(VALUE_SERVICE) $(TB_VALUE_SERVICE)
	$(VVP) $(OUT_VALUE_SERVICE)

run-value-service-256:
	$(IVERILOG) $(IVERILOGFLAGS) -P tb_banked_value_memory_service.PACKET_W=256 -s tb_banked_value_memory_service -o $(OUT_VALUE_SERVICE) $(NOC_FIFO) $(NOC_ROUTER) $(VALUE_SERVICE) $(TB_VALUE_SERVICE)
	$(VVP) $(OUT_VALUE_SERVICE)

status:
	python3 npu/docs/update_status.py

clean:
	rm -f $(OUT)
