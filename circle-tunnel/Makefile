     PROJ := circle-tunnel
 ADD_DEPS := ../include/led-delay.v sqrt_table.hex
ADD_CLEAN := *.o gen_sqrt_table *.hex
  PIN_DEF := ../icebreaker.pcf
   DEVICE := up5k

include ../main.mk

sqrt_table.hex: gen_sqrt_table
	./gen_sqrt_table > $@

gen_sqrt_table: gen_sqrt_table.c
gen_sqrt_table: LDLIBS += -lm
