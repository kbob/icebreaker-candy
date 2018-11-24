#!/usr/bin./env python

from math import pi, sin

F = pi / 500

def f(i):
    return (0.9 * sin(i * F) + 1) / 2
    # return 0.9 * sin(i * F)

foo = open('/tmp/foo', 'w')
for i in range(1000):
    x = f(i)

    print(x, file=foo)

e = 0.0
min_e = max_e = 0.5
for i in range(1000, 3000):
    x = f(i)
    if x >= e:
        y = +1
    else:
        y = 0
    print(y, file=foo)
    e += y - x
    if min_e > e:
        min_e = e
    if max_e < e:
        max_e = e
print('end', file=foo)


print('{} <= e <= {}'.format(min_e, max_e))
