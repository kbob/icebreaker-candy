`default_nettype none

module led_driver (
        input         CLK,
        input         reset_pin,
        output        pll_clk,
        output        reset,
        output [15:0] LED_PANEL);

    localparam S_BLANK  = 4'b0001;
    localparam S_SHIFT0 = 4'b0010;
    localparam S_SHIFT  = 4'b0100;
    localparam S_SHIFTN = 4'b1000;

    wire        P1A1, P1A2, P1A3, P1A4, P1A7, P1A8, P1A9, P1A10;
    wire        P1B1, P1B2, P1B3, P1B4, P1B7, P1B8, P1B9, P1B10;

    wire        pll_locked;
    wire  [4:0] addr;
    wire  [7:0] subframe;
    wire [12:0] frame;
    wire  [5:0] y0, y1;
    wire  [2:0] rgb0, rgb1;

    reg   [2:0] led_rgb0;
    reg   [2:0] led_rgb1;
    reg   [4:0] led_addr;
    wire        led_blank;
    wire        led_latch;
    wire        led_sclk;

    reg   [6:0] x;
    reg  [25:0] row_cnt;
    reg   [4:0] state;
    reg   [1:0] blank;
    reg   [1:0] latch;
    reg         sclk_ena;
    reg   [4:0] state;

    // LED panel pins
    assign LED_PANEL = {P1B10, P1B9, P1B8, P1B7,  P1B4, P1B3, P1B2, P1B1,
                        P1A10, P1A9, P1A8, P1A7,  P1A4, P1A3, P1A2, P1A1};
    assign {P1A3, P1A2, P1A1}              = led_rgb0;
    assign {P1A9, P1A8, P1A7}              = led_rgb1;
    assign {P1B10, P1B4, P1B3, P1B2, P1B1} = led_addr;
    assign P1B7                            = led_blank;
    assign P1B8                            = led_latch;
    assign P1B9                            = led_sclk;

    assign P1A4 = pll_clk;  // XXX debug
    // assign P1A10 = reset;

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
            sclk_ena              <= 0;
            state                 <= S_SHIFT;
        end
        else
            case (state)

                S_BLANK:
                    begin
                        led_addr  <= addr;
                        row_cnt   <= row_cnt + 1;
                        x         <= 0;
                        sclk_ena  <= 0;
                        blank     <= 2'b10;
                        latch     <= 2'b00;
                        state     <= S_SHIFT0;
                    end

                S_SHIFT0:
                    begin
                        blank     <= 2'b00;
                        led_rgb0  <= rgb0;
                        led_rgb1  <= rgb1;
                        x         <= x + 1;
                        sclk_ena  <= 1;
                        state     <= S_SHIFT;
                    end

                S_SHIFT:
                    begin
                        led_rgb0  <= rgb0;
                        led_rgb1  <= rgb1;
                        x         <= x + 1;
                        sclk_ena  <= 1;
                        if (x == 62)
                            state <= S_SHIFTN;
                    end

                S_SHIFTN:
                    begin
                        blank     <= 2'b11;
                        latch     <= 2'b11;
                        led_rgb0  <= rgb0;
                        led_rgb1  <= rgb1;
                        x         <= x + 1;
                        state     <= S_BLANK;
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

    ddr led_sclk_ddr(
        .clk(pll_clk),
        .ena(sclk_ena),
        .ddr_pin(led_sclk));

    // ddr led_latch_ddr(
    //     .clk(pll_clk),
    //     .ena(latch),
    //     .ddr_pin(led_latch));

    // assign led_latch = latch;

    SB_IO #(
        .PIN_TYPE(6'b010001)
    ) blank_ddr (
        .PACKAGE_PIN(led_blank),
        .LATCH_INPUT_VALUE(1'b0),
        // .CLOCK_ENABLE(1'b1),
        .INPUT_CLK(pll_clk),
        .OUTPUT_CLK(pll_clk),
        .OUTPUT_ENABLE(1'b1),
        .D_OUT_0(blank[0]),
        .D_OUT_1(blank[1]));

        SB_IO #(
            .PIN_TYPE(6'b010001)
        ) latch_ddr (
            .PACKAGE_PIN(led_latch),
            .LATCH_INPUT_VALUE(1'b0),
            // .CLOCK_ENABLE(1'b1),
            .INPUT_CLK(pll_clk),
            .OUTPUT_CLK(pll_clk),
            .OUTPUT_ENABLE(1'b1),
            .D_OUT_0(latch[0]),
            .D_OUT_1(latch[1]));

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
        output ddr_pin);

    SB_IO #(
        .PIN_TYPE(6'b010001)
    ) it (
        .PACKAGE_PIN(ddr_pin),
        .LATCH_INPUT_VALUE(1'b0),
        // .CLOCK_ENABLE(1'b1),
        .INPUT_CLK(clk),
        .OUTPUT_CLK(clk),
        .OUTPUT_ENABLE(1'b1),
        .D_OUT_0(1'b0),
        .D_OUT_1(ena));

endmodule // ddr
