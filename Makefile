# Minimal cocotb makefile using GHDL backend
TOPLEVEL_LANG ?= vhdl
SIM ?= ghdl

PWD =  /home/sasindu/FPGA_Projects/rtl/gmsk_pc/axis_gmsk_pre_coder
VHDL_SOURCES = $(PWD)/gmsk_precoder_axi32.vhdl
TOPLEVEL = pre_coder
MODULE = test_gmsk_precoder  # test module file name (without .py), cocotb finds tests inside


SIM_ARGS +=  --vcd=wave.vcd


include $(shell cocotb-config --makefiles)/Makefile.sim
