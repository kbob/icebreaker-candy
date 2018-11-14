     PROJ := gamma-roll
 ADD_DEPS := ../include/led-pwm.v gamma_table.hex
ADD_CLEAN := *.o gen_gamma_table *.hex
  PIN_DEF := ../icebreaker.pcf
   DEVICE := up5k

include ../main.mk

gamma_table.hex: gen_gamma_table
	./gen_gamma_table > $@

gen_gamma_table: gen_gamma_table.c
gen_gamma_table: LDLIBS += -lm
