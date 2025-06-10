SIM ?= icarus
TOPLEVEL_LANG ?= verilog
VERILOG_SOURCES += $(PWD)/../hdl/dut.v
VERILOG_SOURCES += $(PWD)/../hdl/FIFO1.v
VERILOG_SOURCES += $(PWD)/../hdl/FIFO2.v
TOPLEVEL = dut
MODULE = dut_test

SIM = verilator
include $(shell cocotb-config --makefiles)/Makefile.sim
