#!/usr/bin/env python

from itertools import chain
import os
import sys

import PIL.Image

import numerics
import scene
from trickery import lazy_scalar, define_constants


WIDTH, HEIGHT = 64, 64
# WIDTH, HEIGHT = 256, 256
FRAME_COUNT = 2


def make_image():

    numz = numerics.Numerics()
    my_scene = scene.Scene(WIDTH, HEIGHT, numerics=numz)
    pixels = my_scene.render_scene()

    img = PIL.Image.new(mode='RGB', size=(WIDTH, HEIGHT))
    img.putdata(list(chain(*pixels)))
    img.save('scene.png')


def make_animation():
    numz = numerics.Numerics()
    my_scene = scene.Scene(WIDTH, HEIGHT, numerics=numz)
    imgs = []

    for (frame, pixels) in enumerate(my_scene.render_anim(FRAME_COUNT)):
        img = PIL.Image.new(mode='RGB', size=(WIDTH, HEIGHT))
        img.putdata(list(chain(*pixels)))
        if frame == 0:
            seq = img
        else:
            imgs.append(img)
        print('Frame {}'.format(frame))

    seq.save('scene.gif',
             include_color_table=True,
             save_all=True,
             append_images=imgs,
             duration=20,
             loop=100)


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

    # Deprecated
    # # print('begin s components')
    # # for c in s.components():
    # #     print('   s component {}'.format(c))
    # # print('end s components')
    #
    # print(s + s)
    # print(s - s)
    # print(s * s)
    # print(s / s)
    # print(s.clamp(), numz.scalar(0.9).clamp())
    # print(s < 0)
    # print(s - s - s < 0)
    # try:
    #     s >= 0
    #     print('fail')
    # except TypeError:
    #     print('scalar >= not supported')
    # try:
    #     s > 0
    #     print('fail')
    # except TypeError:
    #     print('scalar > not supported')
    # print()
    #
    # Deprecated
    # # for c in v.components():
    # #     print('   v component {}', c)
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
    print('60° =', a)
    print('sin 60° = {:.4}'.format(a.sin()))
    print('cos 60° = {:.4}'.format(a.cos()))
    print('1 radian =', numz.angle(radians=1))
    print('64 units =', numz.angle(units=64))
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


def derandomize_hash():
    if 'PYTHONHASHSEED' not in os.environ:
        environ = dict(os.environ)
        environ['PYTHONHASHSEED'] = '3'
        argv = [sys.executable] + sys.argv
        os.execve(sys.executable, argv, environ)


if __name__ == '__main__':
    derandomize_hash()
    if '-t' in sys.argv:
        test_numerics()
    elif '-a' in sys.argv:
        make_animation()
    else:
        make_image()
