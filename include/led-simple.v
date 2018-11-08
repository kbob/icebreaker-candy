`default_nettype none

module led_driver (
        input  CLK,
        input  reset_pin,
        output pll_clk,
        output reset,
        output [15:0] LED_PANEL);

    localparam  S_BLANK   = 8'b00001;
    localparam  S_LATCH   = 8'b00010;
    localparam  S_UNLATCH = 8'b00100;
    localparam  S_UNBLANK = 8'b01000;
    localparam  S_SHIFT   = 8'b10000;

    wire        P1A1, P1A2, P1A3, P1A4, P1A7, P1A8, P1A9, P1A10;
    wire        P1B1, P1B2, P1B3, P1B4, P1B7, P1B8, P1B9, P1B10;

    wire        pll_locked;
    wire  [7:0] subframe;
    wire [12:0] frame;
    wire  [5:0] y0, y1;
    wire [23:0] rgb0, rgb1;

    reg   [2:0] led_rgb0;
    reg   [2:0] led_rgb1;
    reg   [4:0] led_addr;
    reg         led_blank;
    reg         led_latch;
    wire        led_sclk;

    reg   [6:0] x;
    reg   [4:0] addr;
    reg  [19:0] frame_counter;
    reg   [4:0] state;
    reg         sclk_ena;

    // LED panel pins
    assign LED_PANEL = {P1B10, P1B9, P1B8, P1B7,  P1B4, P1B3, P1B2, P1B1,
                        P1A10, P1A9, P1A8, P1A7,  P1A4, P1A3, P1A2, P1A1};
    assign {P1A3, P1A2, P1A1}              = led_rgb0;
    assign {P1A9, P1A8, P1A7}              = led_rgb1;
    assign {P1B10, P1B4, P1B3, P1B2, P1B1} = led_addr;
    assign P1B7                            = led_blank;
    assign P1B8                            = led_latch;
    assign P1B9                            = led_sclk;

    assign {frame, subframe} = frame_counter;
    assign y0 = {1'b0, addr};
    assign y1 = {1'b1, addr};

    always @(posedge pll_clk)
        if (reset) begin
            led_rgb0              <= 0;
            led_rgb1              <= 0;
            led_addr              <= 0;
            led_blank             <= 0;
            led_latch             <= 0;
            addr                  <= 0;
            frame_counter         <= 0;
            x                     <= 0;
            state                 <= S_BLANK;
            sclk_ena              <= 0;
        end
        else
            case (state)

                S_BLANK:
                    begin
                        led_blank <= 1;
                        led_addr  <= addr;
                        state     <= S_LATCH;
                    end

                S_LATCH:
                    begin
                        led_latch <= 1;
                        state     <= S_UNLATCH;
                    end

                S_UNLATCH:
                    begin
                        led_latch <= 0;
                        state     <= S_UNBLANK;
                    end

                S_UNBLANK:
                    begin
                        led_blank <= 0;
                        x         <= 0;
                        addr      <= addr + 1;
                        if (addr == 31)
                            frame_counter <= frame_counter + 1;
                        state     <= S_SHIFT;
                    end

                S_SHIFT:
                    if (x[6]) begin
                        sclk_ena  <= 0;
                        state     <= S_BLANK;
                    end
                    else begin
                        led_rgb0  <= rgb0;
                        led_rgb1  <= rgb1;
                        x         <= x + 1;
                        sclk_ena  <= 1;
                        state     <= S_SHIFT;
                    end

            endcase

    painter paint0(
        .clk(pll_clk),
        .reset(reset),
        .frame(frame),
        .x(x),
        .y(y0),
        .rgb(rgb0));

    painter paint1(
        .clk(pll_clk),
        .reset(reset),
        .frame(frame),
        .x(x),
        .y(y1),
        .rgb(rgb1));

    pll_30mhz pll(
        .clk_pin(CLK),
        .reset_pin(reset_pin),
        .locked(pll_locked),
        .pll_clk(pll_clk));

    reset_logic rl(
        .pll_clk(pll_clk),
        .pll_locked(pll_locked),
        .reset(reset));

    ddr led_sclk_ddr(
        .clk(pll_clk),
        .ena(sclk_ena),
        .sclk(led_sclk));

endmodule // top


module pll_30mhz (
        input clk_pin,
        input reset_pin,
        output locked,
        output pll_clk);

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
        .RESETB(~reset_pin),
        .BYPASS(1'b0)
    );

endmodule // pll30mhz


module reset_logic (
        input pll_clk,
        input pll_locked,
        output reset);

    reg [3:0] count;
    wire reset_i;

    assign reset = ~count[3];

    always @(posedge pll_clk or negedge pll_locked)
        if (~pll_locked)
            count <= 0;
        else if  (~count[3])
            count <= count + 1;

    SB_GB rst_gb (
        .USER_SIGNAL_TO_GLOBAL_BUFFER(reset_i),
        .GLOBAL_BUFFER_OUTPUT(reset));

endmodule // reset_logic


module ddr (
        input clk,
        input ena,
        output sclk);

    SB_IO #(
        .PIN_TYPE(6'b010001)
    ) it (
        .PACKAGE_PIN(sclk),
        .LATCH_INPUT_VALUE(1'b0),
        .CLOCK_ENABLE(1'b1),
        .INPUT_CLK(clk),
        .OUTPUT_CLK(clk),
        .OUTPUT_ENABLE(1'b1),
        .D_OUT_0(1'b0),
        .D_OUT_1(ena));

endmodule // ddr
