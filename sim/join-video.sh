#!/bin/sh

ffmpeg -i scene.png -pix_fmt rgb565 -f rawvideo scene.raw
cat scene.raw{,,,,} > s5.raw
cat scene.raw{,,,,,,} > s30.raw
dd if=s30.raw of=top-data.bin seek=256 bs=1024
# iceprog top-data.bin
