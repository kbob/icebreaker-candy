# icebreaker-candy
Eye candy from an iCEBreaker FPGA and a 64×64 LED panel

**Disclaimer: I am an FPGA n00b.  I do stupid things unintentionally.**


# Ideas

Want some cool demo-ware for the iCEBreaker.

* I want to try blurring/depth of field stuff.

* 2D transforms: translate, scale, rotate.

* Maybe 3D transforms?

* Ray tracing?  I would love to recreate one of Turner Whitted's first
  published images in real time.

* I want to implement a better-than-average Munching Square.  (See below)

* It would be an interesting challenge to implement Smoking Clover without
a frame buffer.  (See below)

* Glitchy stuff.  Perturb the H clock to make the display jump sideways.
  Other effects are undoubtedly possible.

* There is talk of making a cube of six panels and a single iCEBreaker.

* Mandelbrot sets.


# Hardware

The iCEBreaker is a new dev board based on the Lattice iCE40 UltraPlus 5K FPGA.
The UltraPlus 5K is near the top of the iCE40 line, but it's still
a pretty small FPGA.

* only 40-ish I/O pins
* only 5K LUTs
* only one PLL
* only 8 DSP slices.

It does have a decent amount of embedded RAM.  120 kbits of DPRAM and 1
mbit of SPRAM.

The LED panel of choice is 64×64 RGB.  It uses the HUB75 protocol with
one of 32 pixels latched at any time.  It is rated at 30 MHz.


# Thoughts

There is only one PLL.  So everything has to run on the same clock.
(The external 12 MHz clock is also available, though it's not a
very useful speed.)

I'm thinking that PDM is not common on video displays.  It's feasible (barely)
here because the LED panel has very low resolution, and the FPGA has very
high bandwidth.  I can pump nearly 180 Mbit/sec to 4K pixels.
40 Kbit/sec/pixel.

One thing to do with all that bandwidth is to supersample.  If you
supersample, you can antialias or blur.  Or motion blur.

8×8 multiply is possible in one clock (30 MHz).  16×16 requires two.

There is enough single ported RAM for 256bpp.  But there's only bandwidth
to access 32bpp at 30 MHz, 64bpp at 60 MHz.  Hard mode: the SPRAM
could be clocked at 60 MHz, doubling its bandwidth, but that speed
seriously restricts what the rest of the logic can do.  And there
is only one PLL clock.

The dual ported RAM is smaller but much faster.  30 bpp.


# Smoking Clover

Smoking Clover is traditionally done with a frame buffer and a color
lookup table (CLUT).  The frame buffer is initialized by summing a
bunch of diagonal lines at startup.  Then the CLUT cycles through
interesting colors, and the frame buffer is read-only.  Works great on
circa-1985 workstation displays.

I'm thinking it might be possible, on an FPGA, to calculate 64 or 128
lines simultaneously and update them on every pixel using something
related to Bresenham's algorithm.  Then there is no need for a frame
buffer, just a vast number of gates.

The classic algorithm would calculate 64 lines top-to-bottom and 64
lines left-to-right for a 64×64 display.  It may be possible to
reduce that by a factor of 2 or 4 because of symmetries.


# Munching Square

If I can make 2D transforms work, that's a good way to spice up Munch.  Also,
blurring would be fun.
