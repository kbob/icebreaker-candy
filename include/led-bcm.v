`default_nettype none


module led_main #(
        parameter USE_RESETN_BUTTON =  1,
        parameter FRAME_BITS        = 10,
        parameter DELAY             =  1
    ) (
        input CLK,
        input resetn_btn,
        output pll_clk,
        output reset,
        output [15:0] LED_PANEL);

    // Dimensions
    localparam db = $clog2(DELAY); // delay bits
    localparam fb = FRAME_BITS;    // frame bits
    localparam sb = 8;             // subframe bits
    localparam ab = 5;             // address bits
    localparam rb = 6;             // row bits
    localparam cb = 6;             // column bits
    localparam eb = fb + sb + ab + rb; // extended counter bits

    localparam dh = db - 1;        // delay high bit
    localparam fh = fb - 1;        // frame high bit
    localparam sh = sb - 1;        // subframe high bit
    localparam ah = ab - 1;        // address high bit
    localparam rh = rb - 1;        // row high bit
    localparam ch = cb - 1;        // column high bit
    localparam eh = eb - 1;        // extended counter high bit

    localparam cc = 1 << cb;       // column count

    wire        pll_clk;
    wire        pll_locked;
    wire        resetn;

    wire [13:0] fb_read_addr;
    wire [13:0] fb_write_addr;
    wire        fb_write_enable;
    wire [31:0] fb_data_in;
    wire [31:0] fb_data_out;

    pixel_controller pc (
        .clk(pll_clk),
        .reset(reset),
    );

    frame_buffer fb (
        .clk(pll_clk),
        .reset(reset),
        .frame_toggle(frame[0]),
        .read_addr(fb_read_addr),
        .write_addr(fb_write_addr),
        .write_enable(fb_write_enable),
        .data_in(fb_data_in),
        .data_out(fb_data_out));

    pll_30mhz pll (
        .clk_pin(CLK),
        .locked(pll_locked),
        .pll_clk(pll_clk));

    generate

        if (USE_RESETN_BUTTON) begin
            button_debouncer db (
                .clk(pll_clk),
                .button_pin(resetn_btn),
                .level(resetn));
        end
        else
            assign resetn = 1;

    endgenerate

    reset_logic rl (
        .resetn(resetn),
        .pll_clk(pll_clk),
        .pll_locked(pll_locked),
        .reset(reset));

endmodule // led_main


module pixel_controller (
        input         clk,
        input         reset,
        input         start_frame,
        input         painter_ready,
        input         pixel_ready,
        input  [23:0] pixel_color,
        output        painter_start,
        output  [5:0] x,
        output  [5:0] y,
        output        frame_select,
        output [13:0] write_addr,
    );

endmodule // pixel_controller


// Frame buffer.  Two buffers, each 16384x32.  One half is readable
// and the other is writable, controlled by `frame_toggle`.

module frame_buffer (
    input         clk,
    input         reset,
    input         frame_toggle,
    input  [13:0] read_addr,
    input  [13:0] write_addr,
    input         write_enable,
    input  [31:0] data_in,
    output [31:0] data_out);

    wire wren0 = write_enable && !frame_toggle;
    wire wren1 = write_enable && frame_toggle;

    wire addr0 = wren0 ? write_addr : read_addr;
    wire addr1 = wren1 ? write_addr : read_addr;

    wire [31:0] data_out0;
    wire [31:0] data_out1;

    assign data_out = frame_toggle ? data_out0 : data_out1;

    SPRAM256KA bank0A (     // Frame 0, low word
        .DATAIN(data_in[15:0]),
        .ADDRESS(addr0),
        .MASKWREN(4'b1111),
        .WREN(wren0),
        .CHIPSELECT(~reset),
        .CLOCK(clk),
        .STANDBY(1'b0),
        .SLEEP(1'b0),
        .POWEROFF(1'b1),
        .DATAOUT(data_out0[15:0]));

    SPRAM256KA bank0B (     // Frame 0, high word
        .DATAIN(data_in[31:16]),
        .ADDRESS(addr0),
        .MASKWREN(4'b1111),
        .WREN(wren0),
        .CHIPSELECT(~reset),
        .CLOCK(clk),
        .STANDBY(1'b0),
        .SLEEP(1'b0),
        .POWEROFF(1'b1),
        .DATAOUT(data_out0[31:16]));

    SPRAM256KA bank1A (     // Frame 1, low word
        .DATAIN(data_in[15:0]),
        .ADDRESS(addr1),
        .MASKWREN(4'b1111),
        .WREN(wren1),
        .CHIPSELECT(~reset),
        .CLOCK(clk),
        .STANDBY(1'b0),
        .SLEEP(1'b0),
        .POWEROFF(1'b1),
        .DATAOUT(data_out1[15:0]));

    SPRAM256KA bank1B (     // Frame 1, high word
        .DATAIN(data_in[31:16]),
        .ADDRESS(addr1),
        .MASKWREN(4'b1111),
        .WREN(wren1),
        .CHIPSELECT(~reset),
        .CLOCK(clk),
        .STANDBY(1'b0),
        .SLEEP(1'b0),
        .POWEROFF(1'b1),
        .DATAOUT(data_out1[31:16]));

endmodule // frame_buffer


module button_debouncer (
        input  clk,
        input  button_pin,
        output level,
        output rising_edge,
        output falling_edge);

    localparam COUNT_BITS = 15;

    reg                  is_high;
    reg                  was_high;
    reg                  level_r;
    reg                  rising_edge_r;
    reg                  falling_edge_r;
    reg [COUNT_BITS-1:0] counter = 0;

    assign level        = level_r;
    assign falling_edge = rising_edge_r;
    assign rising_edge  = falling_edge_r;

    always @(posedge clk)
        if (counter) begin
            counter            <= counter + 1;
            rising_edge_r      <= 0;
            falling_edge_r     <= 0;
            was_high           <= is_high;
        end
        else begin
            is_high            <= button_pin;
            level_r            <= is_high;
            if (is_high != was_high) begin
                counter        <= 1;
                rising_edge_r  <= is_high;
                falling_edge_r <= ~is_high;
            end
        end

endmodule // button_debouncer


module pll_30_60mhz (
        input  clk_pin,
        output locked,
        output pll_clk30,
        output pll_clk60);

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
     * Requested output frequency:   60.000 MHz
     * Achieved output frequency:    60.000 MHz
     */

     SB_PLL40_2F_PAD #(
        .FEEDBACK_PATH("SIMPLE"),
        .PLLOUT_SELECT_PORTB("GENCLK_HALF"),
        .DIVR(4'b0000),         // DIVR =  0
        .DIVF(7'b1001111),      // DIVF = 79
        .DIVQ(3'b100),          // DIVQ =  4
        .FILTER_RANGE(3'b001)   // FILTER_RANGE = 1
    ) the_pll (
        .PACKAGEPIN(clk_pin),
        .PLLOUTGLOBALA(pll_clk60),
        .PLLOUTGLOBALB(pll_clk30),
        .LOCK(locked),
        .RESETB(1'b1),
        .BYPASS(1'b0)
    );

endmodule // pll_30_60MHz


module pll_30mhz (
        input clk_pin,
        output locked,
        output pll_clk);

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

    SB_PLL40_PAD #(
        .FEEDBACK_PATH("SIMPLE"),
        .DIVR(4'b0000),         // DIVR =  0
        .DIVF(7'b1001111),      // DIVF = 79
        .DIVQ(3'b101),          // DIVQ =  5
        .FILTER_RANGE(3'b001)   // FILTER_RANGE = 1
    ) the_pll (
        .PACKAGEPIN(clk_pin),
        .PLLOUTCORE(pll_clk),
        .LOCK(locked),
        .RESETB(1'b1),
        .BYPASS(1'b0)
    );

endmodule // pll_30mhz


module reset_logic (
        input pll_clk,
        input pll_locked,
        input resetn,
        output reset);

    localparam MSB = 3;

    reg  [MSB:0] count;
    wire         ext_reset;

    assign ext_reset = ~resetn | ~pll_locked;

    always @(posedge pll_clk or negedge ext_reset)
        if (~ext_reset)
            count <= 0;
        else if  (~count[MSB])
            count <= count + 1;

    SB_GB rst_gb (
        .USER_SIGNAL_TO_GLOBAL_BUFFER(count[MSB]),
        .GLOBAL_BUFFER_OUTPUT(reset));

endmodule // reset_logic
