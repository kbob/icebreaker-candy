/*
 *  icebreaker examples - gamma pwm demo
 *
 *  Copyright (C) 2018 Piotr Esden-Tempski <piotr@esden.net>
 *
 *  Permission to use, copy, modify, and/or distribute this software for any
 *  purpose with or without fee is hereby granted, provided that the above
 *  copyright notice and this permission notice appear in all copies.
 *
 *  THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 *  WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 *  MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 *  ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 *  WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 *  ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 *  OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 */

// This program generates a gamma correction table. This table is then loaded
// into bram of the FPGA to provide a lookup table.

#include <stdio.h>
#include <math.h>

#define DOMAIN_BITS 11
#define DOMAIN_COUNT (1 << DOMAIN_BITS)
#define DOMAIN_MAX (DOMAIN_COUNT - 1)

#define RANGE_BITS ((DOMAIN_BITS + 1) / 2)
#define RANGE_COUNT (1 << RANGE_BITS)
#define RANGE_MAX (RANGE_COUNT - 1)

int main()
{
	fprintf(stderr, "Generating the square root lookup table.\n");

	for (int i = 0; i < DOMAIN_COUNT; i++) {
		int y = (int)sqrt((double)i);


		if ((i % 8) == 0) {
			printf("@%08X", i);
		}
		printf(" %0*X", (RANGE_BITS + 3) / 4, y);
		if ((i % 8) == 7) {
			printf("\n");
		}
	}

	return 0;
}
