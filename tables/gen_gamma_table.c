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

#include <math.h>
#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>

#define DEFAULT_GAMMA     2.2
#define DEFAULT_DOMAIN_BITS 8
#define DEFAULT_RANGE_BITS 16

const char *prog;

void gen_gamma_table(double   gamma,
					 unsigned domain_bits,
					 unsigned range_bits,
					 bool     zero_adjust)
{
	unsigned d_count = 1 << domain_bits;
	unsigned d_max = d_count - 1;
	unsigned r_count = 1 << range_bits;
	unsigned r_max = r_count - 1;

	int range_digits = (range_bits + 3) / 4;

	double min_x = 0.0;
	double x_scale = 1.0 / d_max;
	if (zero_adjust) {
		min_x = pow(1.0 / r_max, 1.0 / gamma);
		x_scale = (1.0 - min_x) / d_max;
		// printf("min_x = %g\n", min_x);
		// printf("x_scale = %g\n", x_scale);
	}

	for (unsigned i = 0; i < d_count; i++) {
		double x = min_x + x_scale * i;
		double y = pow(x, gamma);
		unsigned g = r_max * y;
		if (zero_adjust && i && !g)
			g = 0x01;

		// printf("%3u: %10g -> %4x %10g\n", i, x, g, y);
		// if (i == 10)
		// 	i = d_max - 1;

		if (i % 8 == 0)
			printf("@%08X", i);
		printf(" %0*x", range_digits, g);
		if (i % 8 == 7 || i == d_count - 1)
			printf("\n");
	}
}

void usage(FILE *out)
{
	fprintf(out, "Use:\n");
	fprintf(out, "   %s -h\n", prog);
	fprintf(out, "   %s [arguments] > FILE.hex\n", prog);
	fprintf(out, "\n");
	fprintf(out, "Generate a gamma correction table.\n");
	fprintf(out, "\n");
	fprintf(out, "Optional arguments:\n");
	fprintf(out, "   -h               show this help message and exit\n");
	fprintf(out, "   -g GAMMA         set the gamma exponent\n");
	fprintf(out, "   -d DOMAIN_BITS   set the size of the table's input ");
	fprintf(out,                      "(default 8)\n");
	fprintf(out, "   -r RANGE_BITS    set the size of the table's output ");
	fprintf(out,                      "(default 16)\n");
	fprintf(out, "   -z               adjust scale so nonzero inputs ");
	fprintf(out,                     "produce nonzero outputs\n");
	fprintf(out, "");
	exit(out == stderr);
}

int main(int argc, char *argv[])
{
	double gamma = DEFAULT_GAMMA;
	int domain_bits = DEFAULT_DOMAIN_BITS;
	int range_bits = DEFAULT_RANGE_BITS;
	bool zero_adjust = false;

	int ch;
	char *endptr;

	prog = argv[0];

	while ((ch = getopt(argc, argv, "hg: d:r:z")) != -1) {
		switch (ch) {

		case 'h':
			usage(stdout);

		case 'g':
			gamma = strtod(optarg, &endptr);
			if (*endptr || gamma != gamma)
				usage(stderr);
			break;

		case 'd':
			domain_bits = strtol(optarg, &endptr, 0);
			if (* endptr)
				usage(stderr);
			break;

		case 'r':
			range_bits = strtol(optarg, &endptr, 0);
			if (*endptr)
				usage(stderr);
			break;

		case 'z':
			zero_adjust = true;
			break;

		default:
			usage(stderr);
		}
	}
	if (optind != argc)
		usage(stderr);

	gen_gamma_table(gamma, domain_bits, range_bits, zero_adjust);

	return 0;
}
