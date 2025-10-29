# --------------------------------------------------------

# ///--MAKE SURE ALL THE FILES ARE IN THE SAME FOLDER
# ///--gmsk_precoder_axi32.vhd
# ///--pre_coder.py
# ///--vectors_gen.py
# ///--MakeFile

# ------------------------------------------------------------


import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer
from cocotbext.axi import (AxiStreamBus,AxiStreamSource,AxiStreamSink,AxiStreamFrame,AxiStreamMonitor,)
from cocotb.regression import TestFactory
import csv
import itertools
import random


# ------------------------------
# BACKPRESSURE / PAUSE
# ------------------------------

def random_cycle():
    lst = [1] * 4
    while not 0 in lst:
        lst = [random.randint(0, 1) for _ in range(16)]
    return itertools.cycle(lst)


def fec_cycle():
    pattern = [0] + [1] * 32
    return itertools.cycle(pattern)

# -------------------------------
# TEST BENCH
# -------------------------------

class TB:
    def __init__(self, dut):
        self.dut = dut
        self.source = AxiStreamSource(
            AxiStreamBus.from_prefix(dut, "s_axis"),
            dut.clk,
            dut.rst_n,
            reset_active_level=False,
        )
        self.sink = AxiStreamSink(
            AxiStreamBus.from_prefix(dut, "m_axis"),
            dut.clk,
            dut.rst_n,
            reset_active_level=False,
        )
        
        self.monitor = AxiStreamMonitor(
            AxiStreamBus.from_prefix(dut, "m_axis"),
            dut.clk,
            dut.rst_n,
            reset_active_level=False,
        )

        # ----------------------------------
        # GENERATE THE CLOCK
        # ----------------------------------

        cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
        self.dut._log.setLevel("INFO")

        # ----------------------------------
        # INITIALIZE THE DUT INPUTS
        # ----------------------------------

        dut.s_axis_tdata.value = 0
        dut.s_axis_tvalid.value = 0
        dut.m_axis_tready.value = 0
        dut.s_axis_tlast.value = 0


    # -------------------------------------
    # RESET FUNCTION
    # -------------------------------------

    async def reset(self):
    
        self.dut.rst_n.value = 0  
        for _ in range(5):
            await RisingEdge(self.dut.clk)
        self.dut.rst_n.value = 1
        await RisingEdge(self.dut.clk)

    # ------------------------------------------------------------------
    # Create pause generators for the Source and the Sink correspondly
    # ------------------------------------------------------------------

    def set_idle_generator(self, generator=None):
        if generator:
            self.source.set_pause_generator(generator())

    def set_backpressure_generator(self, generator=None):
        if generator:
            self.sink.set_pause_generator(generator())


# -----------------------------------------------
# LOAD THE CSV FILE
# -----------------------------------------------

def load_vectors(csv_file="vectors_gen.csv"):
    vectors = []
    with open(csv_file, "r") as f:
        reader = csv.DictReader(f)
        for r in reader:
            inp = int(r["input_bin"], 2)
            out = int(r["output_bin"], 2)
            vectors.append((inp, out))
    return vectors
   

    
# --------------------------
# TESTING VIA CSV FILE
# --------------------------

async def run_csv_test(dut, idle_inserter=None, backpressure_inserter=None):
    tb = TB(dut)
    await tb.reset()
    tb.set_idle_generator(idle_inserter)  
    tb.set_backpressure_generator(backpressure_inserter)

    vectors = load_vectors()
    total_vectors = len(vectors)
    dut._log.info(f"Total vectors: {total_vectors}, sending in 1 frame")

    # ------------------------------------------
    # I/P All 20 words as a burst
    # ------------------------------------------

    all_bytes = b''.join(inp.to_bytes(4, "little") for inp, _ in vectors)
    frame = AxiStreamFrame(tdata=all_bytes)
    frame.tlast = True  # asserted only at the end of the whole frame


    
    dut._log.info(f"Sending {total_vectors} words as a single AXI frame")
    await tb.source.send(frame)

    # --------------------------------------
    # Receving Rx Frame
    # --------------------------------------
    
    rx_frame = await tb.sink.recv()
    rx_bytes = rx_frame.tdata
    n_words = len(rx_bytes) // 4

    if n_words != total_vectors:
        dut._log.warning(f"RX frame contains {n_words} words, expected {total_vectors}")

    # --------------------------------------------
    # Compare each O/p with Expected o/p
    # --------------------------------------------

    for i in range(total_vectors):
        got = int.from_bytes(rx_bytes[i*4:(i+1)*4], "little")
        expected = vectors[i][1]
        dut._log.info(f"[{i+1}] GOT: 0x{got:08X}  EXPECTED: 0x{expected:08X}")
        assert got == expected, f"Mismatch at word {i+1}: got=0x{got:08X}, expected=0x{expected:08X}"

    dut._log.info(" All vectors processed successfully.")
    await Timer(100, units="ns")

# --------------------------------------
# FACTORY TEST
# --------------------------------------

factory_csv = TestFactory(run_csv_test)
factory_csv.add_option("idle_inserter", [None, fec_cycle])
factory_csv.add_option("backpressure_inserter", [None, random_cycle])
factory_csv.generate_tests()
