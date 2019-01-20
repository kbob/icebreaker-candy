#!/usr/bin/env python

import argparse
from itertools import chain
import math
import os
import sys

import PIL.Image

import simple_numerics
import dag_numerics
import sexpr_numerics
import log_numerics
import scene


WIDTH, HEIGHT = 64, 64
# WIDTH, HEIGHT = 256, 256
# FRAME_COUNT = 2


def make_image(numz_module):

    numz = numz_module.Numerics()
    my_scene = scene.Scene(WIDTH, HEIGHT, numerics=numz)
    pixels = my_scene.render_scene()

    img = PIL.Image.new(mode='RGB', size=(WIDTH, HEIGHT))
    img.putdata(list(chain(*pixels)))
    img.save('scene.png')


def make_animation(frame_count, numz_module):
    numz = numz_module.Numerics()
    my_scene = scene.Scene(WIDTH, HEIGHT, numerics=numz)
    imgs = []

    for (frame, pixels) in enumerate(my_scene.render_anim(frame_count)):
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


def test_numerics(numz_module):
    numz = numz_module.Numerics()

    s = numz.scalar(3)
    v = numz.vec3(1, 2, 3)
    a = numz.angle(degrees=60)

    print('s', s)
    print('v', v)
    print('a', a)
    assert s.value == 3
    assert v._access_values() == [1, 2, 3]
    assert a.radians == math.pi / 3
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


def main(argv):
    derandomize_hash()
    parser = argparse.ArgumentParser(description='Annotated Ray Tracer')
    action = parser.add_mutually_exclusive_group()
    action.add_argument('-t', '--test',
        action='store_true',
        help='run self-test')
    action.add_argument('-i', '--image',
        action='store_true',
        help='generate static image')
    action.add_argument('-a', '--animate',
        action='store_true',
        help='generate animation')
    parser.add_argument('-n', '--numerics',
        choices=('simple', 'dag', 'sexpr', 'log'),
        default='simple',
        help='choose numeric implementation')
    parser.add_argument('-f', '--frames',
        type=int,
        default=2,
        metavar='N',
        help='number of animation frames')
    args = parser.parse_args(argv[1:])

    numz = {
        'simple': simple_numerics,
        'dag': dag_numerics,
        'sexpr': sexpr_numerics,
        'log': log_numerics,
    }[args.numerics]
    if args.test:
        test_numerics(numz)
    elif args.animate:
        make_animation(args.frames, numz)
    else:
        make_image(numz)


if __name__ == '__main__':
    main(sys.argv)
