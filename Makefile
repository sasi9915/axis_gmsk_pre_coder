# Minimal cocotb makefile using GHDL backend
TOPLEVEL_LANG ?= vhdl
SIM ?= ghdl

PWD =  /home/sasindu/FPGA_Projects/rtl/axis_peak_detector
VHDL_SOURCES = $(PWD)/axis_peak_detector.vhdl
TOPLEVEL = axis_peak_detector
MODULE = try_01  # test module file name (without .py), cocotb finds tests inside


SIM_ARGS +=  --vcd=wave.vcd


include $(shell cocotb-config --makefiles)/Makefile.sim
