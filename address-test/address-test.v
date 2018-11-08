`default_nettype none

`include "../include/led-simple.v"

module top (
        input         CLK,
        input         BTN1_N,
        output [15:0] LED_PANEL);

    led_driver ld(
        .CLK(CLK),
        .reset_pin(BTN1_N),
        .LED_PANEL(LED_PANEL));

endmodule

module painter(
        input        clk,
        input        reset,
        input [12:0] frame,
        input  [5:0] x,
        input  [5:0] y,
        output [2:0] rgb);

    wire x_single_bit, y_single_bit;

    assign x_single_bit = (| x) & (~|(x & (x - 1)));
    assign y_single_bit = (| y) & (~|(y & (y - 1)));

    //             BLUE GREEN RED
    assign rgb = {0, y_single_bit, x_single_bit};

endmodule
