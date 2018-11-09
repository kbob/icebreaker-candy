`default_nettype none

// TODO:
//
//    split led_driver into two modules.  One that manipulates the
//    output pins and one that instantiates all the other modules.
//
//    parameterize for delay.
//
//    combine frame and subframe.



module led_driver (
        input         CLK,
        input         reset_pin,
        output        pll_clk,
        output        reset,
        output [15:0] LED_PANEL);

    // State machine.
    localparam S_START   = 6'b000001;
    localparam S_SHIFT0  = 6'b000010;
    localparam S_SHIFT   = 6'b000100;
    localparam S_SHIFTN  = 6'b001000;
    localparam S_BLANK   = 6'b010000;
    localparam S_UNBLANK = 6'b100000;

    // Route outputs to LED panel with registers as needed.
    reg   [2:0] led_rgb0;
    reg   [2:0] led_rgb1;
    reg   [4:0] led_addr;
    wire        led_blank;
    wire        led_latch;
    wire        led_sclk;
    wire        P1A1, P1A2, P1A3, P1A4, P1A7, P1A8, P1A9, P1A10;
    wire        P1B1, P1B2, P1B3, P1B4, P1B7, P1B8, P1B9, P1B10;

    assign {P1A3, P1A2, P1A1}              = led_rgb0;
    assign {P1A9, P1A8, P1A7}              = led_rgb1;
    assign {P1B10, P1B4, P1B3, P1B2, P1B1} = led_addr;
    assign P1B7                            = led_blank;
    assign P1B8                            = led_latch;
    assign P1B9                            = led_sclk;
    assign {P1A4, P1A10}                   = 0;
    assign LED_PANEL = {P1B10, P1B9, P1B8, P1B7,  P1B4, P1B3, P1B2, P1B1,
                        P1A10, P1A9, P1A8, P1A7,  P1A4, P1A3, P1A2, P1A1};

    wire        pll_locked;
    wire  [4:0] addr;
    wire  [7:0] subframe;
    wire [12:0] frame;
    wire  [5:0] y0, y1;
    wire  [2:0] rgb0, rgb1;

    reg   [6:0] x;
    reg  [25:0] row_cnt;
    reg   [4:0] state;
    reg   [1:0] blank;
    reg   [1:0] latch;
    reg   [1:0] sclk;
    reg   [4:0] state;

    assign {frame, subframe, addr} = row_cnt;
    assign y0 = {1'b0, addr};
    assign y1 = {1'b1, addr};

    always @(posedge pll_clk)
        if (reset) begin
            led_rgb0              <= 0;
            led_rgb1              <= 0;
            led_addr              <= 0;
            x                     <= 0;
            row_cnt               <= 0;
            blank                 <= 2'b11;
            latch                 <= 2'b00;
            sclk                  <= 2'b10;
            state                 <= S_START;
        end
        else
            case (state)

                S_START:          // Exit reset; start shifting column data.
                    begin
                        blank     <= 2'b11; // blank until first row is latched
                        state     <= S_SHIFT;
                    end

                S_SHIFT0:         // Shift first column.
                    begin
                        led_rgb0  <= rgb0;
                        led_rgb1  <= rgb1;
                        x         <= x + 1;
                        blank     <= 2'b00;
                        sclk      <= 2'b10;
                        state     <= S_SHIFT;
                    end

                S_SHIFT:          // Shift a column.
                    begin
                        led_rgb0  <= rgb0;
                        led_rgb1  <= rgb1;
                        x         <= x + 1;
                        sclk      <= 2'b10;
                        if (x == 62) // next column will be the last.
                            state <= S_SHIFTN;
                    end

                S_SHIFTN:         // Shift out the last column; start LATCH.
                    begin
                        latch     <= 2'b01;
                        led_rgb0  <= rgb0;
                        led_rgb1  <= rgb1;
                        x         <= x + 1;
                        state     <= S_BLANK;
                    end

                S_BLANK:          // Drain shift register; start BLANK.
                    begin
                        blank     <= 2'b11;
                        latch     <= 2'b10;
                        sclk      <= 2'b00;
                        state     <= S_UNBLANK;
                    end

                S_UNBLANK:        // End BLANK; start next row.
                    begin
                        led_addr  <= addr;
                        row_cnt   <= row_cnt + 1;
                        x         <= 0;
                        blank     <= 2'b10;
                        latch     <= 2'b00;
                        state     <= S_SHIFT0;
                    end

            endcase

    painter paint0(
        .clk(pll_clk),
        .reset(reset),
        .frame(frame),
        .x(x[5:0]),
        .y(y0),
        .rgb(rgb0));

    painter paint1(
        .clk(pll_clk),
        .reset(reset),
        .frame(frame),
        .x(x[5:0]),
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

    ddr led_blank_ddr(
        .clk(pll_clk),
        .data(blank),
        .ddr_pin(led_blank));

    ddr led_latch_ddr(
        .clk(pll_clk),
        .data(latch),
        .ddr_pin(led_latch));

    ddr led_sclk_ddr(
        .clk(pll_clk),
        .data(sclk),
        .ddr_pin(led_sclk));

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
        input       clk,
        input [1:0] data,
        output      ddr_pin);

    SB_IO #(
        .PIN_TYPE(6'b010001)
    ) it (
        .PACKAGE_PIN(ddr_pin),
        .LATCH_INPUT_VALUE(1'b0),
        .INPUT_CLK(clk),
        .OUTPUT_CLK(clk),
        .OUTPUT_ENABLE(1'b1),
        .D_OUT_0(data[0]),
        .D_OUT_1(data[1]));

endmodule // ddr
