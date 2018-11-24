     PROJ := address-test-pdm
 ADD_DEPS := ../include/led-pdm-gamma.v gamma8x10z_table.hex
ADD_CLEAN := gamma8x10z_table.hex $(GEN_GAMMA)
  PIN_DEF := ../icebreaker.pcf
   DEVICE := up5k

include ../main.mk

gamma8x10z_table.hex: $(GEN_GAMMA)
	$(GEN_GAMMA) -d 8 -r 10 -z > $@
