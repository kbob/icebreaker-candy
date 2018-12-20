#!/usr/bin/env python

import sys

import PIL.Image

import numerics
import scene
from trickery import lazy_scalar, define_constants


WIDTH, HEIGHT = 64, 64
# WIDTH, HEIGHT = 256, 256

def make_image():

    numz = numerics.Numerics()
    my_scene = scene.Scene(WIDTH, HEIGHT, numerics=numz)
    pixels = my_scene.render_scene()

    img = PIL.Image.new(mode='RGB', size=(WIDTH, HEIGHT), color=0)
    pix = img.load()

    for y in range(HEIGHT):
        for x in range(WIDTH):
            pix[x, y] = pixels[y][x]

    img.save('scene.png')

def test_numerics():
    numz = numerics.Numerics()

    s = numz.scalar(3)
    v = numz.vec3(1, 2, 3)
    a = numz.angle(degrees=60)

    print('s', s)
    print('v', v)
    print('a', a)
    # print('s = {:.2}'.format(numerics.scalar(2/3)))
    # vv = numerics.vec3(1/3, 1/7, 1/9)
    # print('vv = {:.2}'.format(vv))
    #
    # print(v[0], v.x, v.r)
    # print(v[1], v.y, v.g)
    # print(v[2], v.z, v.b)
    # print()
    #
    print(s + s)
    print(s - s)
    print(s * s)
    print(s / s)
    print(s.clamp(), numz.scalar(0.9).clamp())
    print(s < 0)
    print(s - s - s < 0)
    try:
        s >= 0
        print('fail')
    except TypeError:
        print('scalar >= not supported')
    try:
        s > 0
        print('fail')
    except TypeError:
        print('scalar > not supported')
    print()
    #
    # print(v + v)
    # print(v - v)
    # print(v @ v)
    # print((v * numz.scalar(0.7)).clamp())
    # print('{:.2}'.format(v.normalize()))
    # print()
    #
    # print(s + v)
    # print(s * v)
    # print(v + s)
    # print(v - s)
    # print(v * s)
    #
    # print(a)
    # print(a.sin())
    # print(a.cos())
    #
    # print(v.rotate(a, 'X'))
    # print(v.rotate(numerics.angle(degrees=90), 'X'))

    #
    # lazy_scalar('MY_VAR', 0.01)
    #
    # def f():
    #     define_constants(globals(), numerics)
    #     print(locals())
    #     print('MY_VAR = {}'.format(MY_VAR))
    #     print('type(MY_VAR) = {}'.format(type(MY_VAR)))
    #
    # f()
    #
    # print('MY_VAR = {}'.format(MY_VAR))

if __name__ == '__main__':
    if '-t' in sys.argv:
        test_numerics()
    else:
        make_image()
