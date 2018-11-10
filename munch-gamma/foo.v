/**
 * PLL configuration
 *
 * This Verilog header file was generated automatically
 * using the icepll tool from the IceStorm project.
 * It is intended for use with FPGA primitives SB_PLL40_CORE,
 * SB_PLL40_PAD, SB_PLL40_2_PAD, SB_PLL40_2F_CORE or SB_PLL40_2F_PAD.
 * Use at your own risk.
 *
 * Given input frequency:        12.000 MHz
 * Requested output frequency:   30.000 MHz
 * Achieved output frequency:    30.000 MHz
 */

.FEEDBACK_PATH("SIMPLE"),
.DIVR(4'b0000),		// DIVR =  0
.DIVF(7'b1001111),	// DIVF = 79
.DIVQ(3'b101),		// DIVQ =  5
.FILTER_RANGE(3'b001)	// FILTER_RANGE = 1
