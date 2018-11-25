     PROJ := munch1
 ADD_DEPS := ../include/led-pwm-gamma.v gamma8x8z_table.hex
ADD_CLEAN := gamma8x8z_table.hex $(GEN_GAMMA)
  PIN_DEF := ../icebreaker.pcf
   DEVICE := up5k

include ../main.mk

gamma8x8z_table.hex: $(GEN_GAMMA)
	$(GEN_GAMMA) -d 8 -r 8 -z > $@
