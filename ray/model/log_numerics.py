import inspect
import io
import math
import os

import trickery


class Logger:
    def __init__(self):
        self.prefix = ''
        self.counter = 0
        self._f = None

    def _next_id(self):
        z = f'{self.prefix or "t"}{self.counter:03}'
        self.counter += 1
        return z

    def log_progress(self, str):
        print('#', str, file=self.f)
        # self.f.flush()

    def log_inst(self, op, result, operands, sig=None):
        if sig is None:
            sig = trickery.caller_signature(3, 6)
        if not hasattr(result, 'id'):
            result.id = self._next_id()
        opn_ids = ', '.join(o.id for o in operands)
        print(f'{op:8} {result.id:6} {opn_ids:19} # {sig}', file=self.f)

    @property
    def f(self):
        if not self._f:
            self._f = open('log', 'w')
        return self._f

logger = Logger()

def record(op, result, operands, sig=None):
    logger.log_inst(op, result, operands, sig)



class Scalar:

    def __init__(self, value):
        if isinstance(value, Scalar):
            # Vec3 constructor copies scalar.
            self.value = value.value
            record('copy.s', self, (value, ))
        else:
            self.value = float(value)
            # record('const', self, ())

    def __repr__(self):
        return repr(self.value)

    def __format__(self, format_spec):
        return format(self.value, format_spec)

    def __add__(self, other):
        if isinstance(other, Scalar):
            result = Scalar(self.value + other.value)
            record('add.ss', result, (self, other))
            return result
        elif isinstance(other, Vec3):
            a, b, c = other.values
            result = Vec3(self + a, self + b, self + c)
            assert False # record('add', result, Type.VECTOR, (self, other))
            return result
        else:
            assert False, f'type(other) = {type(other)}'

    def __sub__(self, other):
        assert isinstance(other, Scalar), f'type(other) = {type(other)}'
        result = Scalar(self.value - other.value)
        record('sub.ss', result, (self, other))
        return result

    def __mul__(self, other):
        if isinstance(other, Scalar):
            result = Scalar(self.value * other.value)
            record('mul.ss', result, (self, other))
            return result
        elif isinstance(other, Vec3):
            v = self.value
            a, b, c = other._access_values()
            result = Vec3(v * a, v * b, v * c)
            record('mul.sv', result, (self, other))
            return result
        else:
            assert False, f'type(other) = {type(other)}'

    def __truediv__(self, other):
        assert isinstance(other, Scalar), f'type(other) = {type(other)}'
        result = Scalar(self.value / other.value)
        record('div.s', result, (self, other))
        return result

    def __lt__(self, other):
        assert other == 0, 'must compare to zero'
        result = Boolean(self.value < 0)
        # global cg_test_count
        # label = f'{cg_test_count}\\nis_neg\\n{result}'
        # cg_test_count += 1
        record('is_neg.s', result, (self, ))
        # if current_recorder:
        #     current_recorder.tag_test(result)
        return result

    def abs(self):
        result = Scalar(abs(self.value))
        record('abs.s', result, (self, ))
        return result

    def sqrt(self):
        result = Scalar(math.sqrt(self.value))
        record('sqrt.s', result, (self, ))
        return result

    def to_unorm(self):
        result = min(255, max(0, round(self.value * 255)))
        return result

    def xor4(self, other):
        """Stupid method.  Can't figure out how to decompose it."""
        assert isinstance(other, Scalar)
        a, b = math.floor(self.value), math.floor(other.value)
        result = Scalar((a ^ b) >> 2 & 1)
        record('xor4.ss', result, (self, other))
        return result


class Angle:

    def __init__(self, radians=None, degrees=None, units=None):
        assert sum(x is None for x in (radians, degrees, units)) == 2
        if degrees is not None:
            radians = degrees * math.pi / 180
        elif units is not None:
            radians = units * math.tau / 1024
        else:
            # radians is first arg; copy constructor will appear here.
            other = radians
            if isinstance(other, Angle):
                radians = other.radians
                record('copy.a', self, (other, ))
        self.radians = float(radians)

    def __repr__(self):
        return f'{self:.4}'

    def __format__(self, format_spec):
        fa = format(self.radians / math.tau, format_spec)
        # 'angle x.xxx tau'
        # U+2220  ANGLE
        # U+1d70f MATHEMATICAL ITALIC SMALL TAU
        # U+03c4  GREEK SMALL LETTER TAU
        # return '\u2220{}\U0001d70f'.format(fa)
        # return '\u2220{}\u03c4'.format(fa)
        return fa

    def sin(self):
        result = Scalar(math.sin(self.radians))
        record('sin.a', result, (self, ))
        return result

    def cos(self):
        result = Scalar(math.cos(self.radians))
        record('cos.a', result, (self, ))
        return result


class Vec3:

    def __init__(self, *args):
        if len(args) == 1:
            other = args[0]
            assert isinstance(other, Vec3), f'type(other) = {type(other)}'
            self.values = other.values
            record('copy.v', self, (other, ))
        elif len(args) == 3:
            values = ()
            # operands = ()
            for arg in args:
                try:
                    value = float(arg)
                except TypeError:
                    if isinstance(arg, Scalar):
                        # operands += (arg, )
                        value = arg.value
                    else:
                        raise
                values += (value, )

            self.values = values
            # record('vec.sss', self, operands)
        else:
            assert False, f'expected 1 or 3 args, got {len(args)}'

    def __repr__(self):
        a, b, c = self.values
        return f'({a!r} {b!r} {c!r})'

    def __format__(self, format_spec):
        a, b, c = (format(i, format_spec) for i in self.values)
        return f'({a} {b} {c})'

    def __getitem__(self, index):
        assert index in (0, 1, 2)
        result = Scalar(self.values[index])
        record(f'index {index}', result, (self, ))
        return result

    @property
    def x(self):
        return self[0]

    @property
    def y(self):
        return self[1]

    @property
    def z(self):
        return self[2]

    r, g, b = x, y, z

    def _access_values(self):
        return iter(self.values)
        # return [v.value for v in self.values]

    def __add__(self, other):
        assert all(isinstance(v, float) for v in self.values)
        if isinstance(other, Scalar):
            a, b, c = self._access_values()
            s = other.value
            result = Vec3(a + s, b + s, c + s)
            record('add.vs', result, (self, other))
            return result
        elif isinstance(other, Vec3):
            a, b, c = self._access_values()
            d, e, f = other._access_values()
            result = Vec3(a + d, b + e, c + f)
            record('add.vv', result, (self, other))
            return result
        else:
            assert False, f'type(other) = {type(other)}'

    def __sub__(self, other):
        if isinstance(other, Scalar):
            a, b, c = self._access_values()
            s = other.value
            result = Vec3(a - s, b - s, c - s)
            assert False # record('sub', result, Type.VECTOR, (self, other))
            return result
        elif isinstance(other, Vec3):
            a, b, c = self._access_values()
            d, e, f = other._access_values()
            result = Vec3(a - d, b - e, c - f)
            record('sub.vv', result, (self, other))
            return result
        else:
            assert False, f'type(other) = {type(other)}'

    def __mul__(self, other):
        assert isinstance(other, Scalar), f'type(other) = {type(other)}'
        a, b, c = self._access_values()
        s = other.value
        result = Vec3(a * s, b * s, c * s)
        record('mul.vs', result, (self, other))
        return result

    def __matmul__(self, other):
        """dot product"""
        assert isinstance(other, Vec3), f'type(other) = {type(other)}'
        a, b, c = self._access_values()
        d, e, f = other._access_values()
        result = Scalar(a * d + b * e + c * f)
        record('dot.vv', result, (self, other))
        return result

    def normalize(self):
        global ONE
        try:
            ONE
        except NameError:
            ONE = Scalar(1)
            sig = 'ONE = 1.0'
            record('scalar', ONE, (), sig=sig)
        return self * (ONE / (self @ self).sqrt())

    def rotate(self, angle, axis):
        assert isinstance(angle, Angle)
        assert axis == 'X' or axis == 'Y'
        sa, ca = angle.sin(), angle.cos()
        s, c = sa.value, ca.value
        x, y, z = self._access_values()
        if axis == 'X':
            result = Vec3(x, c * y - s * z, s * y + c * z)
            record('rotX', result, (self, sa, ca))
            return result
        elif axis == 'Y':
            result = Vec3(c * x + s * z, y, c * z - s * x)
            record('rotY', result, (self, sa, ca))
            return result

    def to_unorm(self):
        def unorm(x):
            return min(255, max(0, round(x * 255)))
        a, b, c = self._access_values()
        result = RGBUnorm(unorm(a), unorm(b), unorm(c))
        record('unorm.v', result, (self, ))
        return result


class Boolean:

    def __init__(self, value):
        assert isinstance(value, bool), f'type(value) = {type(value)}'
        self.value = value

    def __bool__(self):
        return self.value

    def __repr__(self):
        return ['false', 'true'][self.value]


class RGBUnorm:

    def __init__(self, *args):
        if len(args) == 1:
            other = args[0]
            assert isinstance(other, RGBUnorm), f'type(other) = {type(other)}'
            self.values = other.values
            record('copy.u', self, (other, ))
        elif len(args) == 3:
            assert all(isinstance(c, int)
                       for c in args), f'type(other) = {type(other)}'
            r, g, b = args
            self.values = r, g, b
        else:
            assert False, f'expected 1 or 3 args, got {len(args)}'

    def __repr__(self):
        return '#{:02x}{:02x}{:02x}'.format(*self.values)

    def as_tuple(self):
        return self.values


class Numerics:

    def __init__(self):
        self.frame_counter = -1
        self.pixel_counter = 0

    def scalar(self, value, sig=None):
        result = Scalar(value)
        if sig is None:
            sig = f'const {result.value}'
        record('scalar', result, (), sig=sig)
        return result

    def vec3(self, a, b, c, sig=None):
        result = Vec3(a, b, c)
        operands = tuple(arg for arg in (a, b, c) if isinstance(arg, Scalar))
        record('vec.sss', result, operands, sig=sig)
        return result

    def angle(self, radians=None, degrees=None, units=None, sig=None):
        "units are 1/1024th of a circle."
        assert sum(x is None for x in (radians, degrees, units)) == 2
        result = Angle(radians=radians, degrees=degrees, units=units)
        record('angle', result, (), sig=sig)
        return result


    def start_frame(self, *input_tuples):
        self.frame_counter += 1
        self._begin_segment(f'frame {self.frame_counter}', *input_tuples)

    def end_frame(self, *output_tuples):
        self.pixel_counter = 0
        self._end_segment(f'frame {self.frame_counter}', *output_tuples)

    def start_pixel(self, *input_tuples):
        f = self.frame_counter
        p = self.pixel_counter
        self._begin_segment(f'frame {f} pixel {p}', *input_tuples)

    def end_pixel(self, *output_tuples):
        f = self.frame_counter
        p = self.pixel_counter
        self._end_segment(f'frame {f} pixel {p}', *output_tuples)
        self.pixel_counter += 1


    def _begin_segment(self, msg, *input_tuples):
        logger.log_progress(f'BEGIN {msg}')
        for tup in input_tuples:
            tup_name = tup.__class__.__name__
            for f in tup._fields:
                obj = getattr(tup, f)
                try:
                    fobj = format(obj, '.4')
                except TypeError:
                    fobj = format(obj)
                record('input', obj, (), sig=f'{tup_name}.{f} = {fobj}')


    def _end_segment(self, msg, *output_tuples):
        for tup in output_tuples:
            tup_name = tup.__class__.__name__
            for f in tup._fields:
                obj = getattr(tup, f)
                try:
                    fobj = format(obj, '.4')
                except TypeError:
                    fobj = format(obj)
                record('output', obj, (), sig=f'{tup_name}.{f} = {fobj}')
        logger.log_progress(f'END {msg}')
