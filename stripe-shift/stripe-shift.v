`default_nettype none

`include "../include/led-pwm-gamma.v"

module top (
        input         CLK,
        input         BTN_N,
        output [15:0] LED_PANEL);

        led_main #(
            .FRAME_BITS(16),
            .DELAY(1)
        ) main (
            .CLK(CLK),
            .resetn_btn(BTN_N),
            .LED_PANEL(LED_PANEL));

endmodule

module painter24(
        input         clk,
        input         reset,
        input  [15:0] frame,
        input   [7:0] subframe,
        input   [5:0] x,
        input   [5:0] y,
        output [23:0] rgb24);

    wire [7:0] hue = frame[2+:8];
    wire [5:0] yy = y + frame[0+:6] + x;
    wire [4:0] dim = yy[5] ? 31 - yy[4:0] : yy[4:0];

    reg  [2:0] schan, gchan;     // color channels that are solid, gradient.
    reg  [4:0] sdist, gdist;
    reg        in_stripe;
    always @(posedge clk) begin
        in_stripe <= x[1:0] == 0;
        sdist <= 5'b11111;
        case (hue[7:5])

            0: begin
                schan <= 3'b000;
                gchan <= 3'b001;
                gdist <= hue[4:0];
            end

            1: begin
                schan <= 3'b001;
                gchan <= 3'b010;
                gdist <= hue[4:0];
            end

            2: begin
                schan <= 3'b010;
                gchan <= 3'b001;
                gdist <= 31 - hue[4:0];
            end

            3: begin
                schan <= 3'b010;
                gchan <= 3'b100;
                gdist <= hue[4:0];
            end

            4: begin
                schan <= 3'b110;
                gchan <= 3'b001;
                gdist <= hue[4:0];
            end

            5: begin
                schan <= 3'b101;
                gchan <= 3'b010;
                gdist <= 31 - hue[4:0];
            end

            6: begin
                schan <= 3'b100;
                gchan <= 3'b001;
                gdist <= 31 - hue[4:0];
            end

            7: begin
                schan <= 3'b000;
                gchan <= 3'b100;
                gdist <= 31 - hue[4:0];
            end

        endcase
    end

    wire [4:0] ssdist = sdist < dim ? 0 : sdist - dim;
    wire [4:0] ggdist = gdist < dim ? 0 : gdist - dim;

    wire [7:0] solid, grad;
    assign solid = {ssdist[4:0], ssdist[4:2]};
    assign grad  = {ggdist[4:0], ggdist[4:2]};
    // assign solid = {3'b0, sdist[4:0]};
    // assign grad  = {3'b0, gdist[4:0]};
    wire [7:0] red, green, blue;
    assign red   = in_stripe ? gchan[0] ? grad : (schan[0] ? solid : 0) : 0;
    assign green = in_stripe ? gchan[1] ? grad : (schan[1] ? solid : 0) : 0;
    assign blue  = in_stripe ? gchan[2] ? grad : (schan[2] ? solid : 0) : 0;

    assign rgb24 = {blue, green, red};

endmodule
