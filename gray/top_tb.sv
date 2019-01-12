`default_nettype none

module top_tb();

    reg  clk;
    integer i;

    reg [3:0] binary;
    wire [3:0] gray;
    wire [3:0] binary_again;

    to_gray uut (
        .clk(clk),
        .enable(1'b1),
        .binary(binary),
        .gray(gray)
        );

    to_binary uut2 (
        .clk(clk),
        .enable(1'b1),
        .gray(gray),
        .binary(binary_again)
    );

    initial begin
        $dumpfile("queue.vcd");
        $dumpvars(0, top_tb);
    end

    initial begin
        clk = 0;
        binary = 4'b0000;
        for (i = 0; i < 40; i++)
            #1 clk = ~clk;
    end

    always @(posedge clk) begin
        binary <= binary + 1;
        // assert(binary_again + 2 == binary);
    end


endmodule // top_tb
