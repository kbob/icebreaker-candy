# Munch Cheesy Gamma

Quick hack to demo low-precision multiplication for gamma correction.

A cheesy way to gamma correct is to square the
pixel value.  That gives a gamma of 2.0, which is sort of close
to a good gamma value.

On the iCEBreaker FPGA, squaring by doing an 8-bit multiply
requires at least one extra clock cycle and a lot of LUTs.
So you can square by multiplying just the high-order bits.

But doing that loses fine detail.  So instead, this design
multiplies the high bits by the low bits.  Look at the line
that says

    wire [7:0] z8g = z6[5:2] * z6[3:0];

That's the gamma correction with extra cheese.
