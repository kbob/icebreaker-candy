import copy
from enum import Enum, auto
import math

import dag
import trickery


class Type(Enum):
    SCALAR   = auto()
    ANGLE    = auto()
    VECTOR   = auto()
    RGBUNORM = auto()
    BOOL     = auto()
    UNDEF    = auto()

    @classmethod
    def identify(cls, obj):
        return {
            Scalar: cls.SCALAR,
            Angle: cls.ANGLE,
            Vec3: cls.VECTOR,
            RGBUnorm: cls.RGBUNORM,
        }.get(type(obj), cls.UNDEF)


current_graph = None
cg_test_count = 0

def record(label, op, type, predecessors):
    if current_graph:
        current_graph.add_node(label, op, type.name.lower())
        if type == Type.BOOL and hasattr(current_graph, 'next_test_label'):
            current_graph.annotate_test(op, current_graph.next_test_label)
            del current_graph.next_test_label
        for p in predecessors:
            if p not in current_graph.node_map:
                # (name, value, type_) = trickery.find_constant(p)
                name = getattr(p, 'name', '')
                label = 'const\\n{}\\n{:.3}'.format(name, p)
                type_ = Type.identify(p).name.lower()
                current_graph.add_node(label, p, type_)
                current_graph.tag_constant(p)
            # assert p in current_graph.node_map, str(p)
            if p in current_graph.node_map:
                current_graph.add_edge(p, op)


class NumericBase:          # XXX still needed?
    pass

    # def __init__(self):
    #     self.starts_pixel = False
    #     self.starts_frame = False

    # def components(self):
    #     return iter(range(0))


class Scalar(NumericBase):

    def __new__(cls, *args):
        if not args:
            return super().__new__(cls)
        value = args[0]
        if args and isinstance(value, Scalar):
            return value
        else:
            result = super().__new__(cls)
            result.value = float(value)
            return result

    def __repr__(self):
        return repr(self.value)

    def __format__(self, format_spec):
        return format(self.value, format_spec)

    def __add__(self, other):
        if isinstance(other, Scalar):
            result = Scalar(self.value + other.value)
            record('add', result, Type.SCALAR, (self, other))
            return result
        elif isinstance(other, Vec3):
            print('S + V')
            a, b, c = other.values
            result = Vec3(self + a, self + b, self + c)
            record('add', result, Type.VECTOR, (self, other))
            return result
        else:
            assert False, 'type(other) = {}'.format(type(other))

    def __sub__(self, other):
        assert isinstance(other, Scalar), 'type(other) = {}'.format(type(other))
        result = Scalar(self.value - other.value)
        record('sub', result, Type.SCALAR, (self, other))
        return result

    def __mul__(self, other):
        if isinstance(other, Scalar):
            result = Scalar(self.value * other.value)
            record('mul', result, Type.SCALAR, (self, other))
            return result
        elif isinstance(other, Vec3):
            v = self.value
            a, b, c = other._access_values()
            result = Vec3(v * a, v * b, v * c)
            record('mul', result, Type.VECTOR, (self, other))
            return result
        else:
            assert False, 'type(other) = {}'.format(type(other))

    def __truediv__(self, other):
        assert isinstance(other, Scalar), 'type(other) = {}'.format(type(other))
        result = Scalar(self.value / other.value)
        record('div', result, Type.SCALAR, (self, other))
        return result

    def __lt__(self, other):
        assert other == 0, 'must compare to zero'
        result = self.value < 0
        global cg_test_count
        label = '{}\\nis_neg\\n{}'.format(cg_test_count, result)
        cg_test_count += 1
        record(label, result, Type.BOOL, (self, ))
        return result

    def abs(self):
        result = Scalar(abs(self.value))
        record('abs', result, Type.SCALAR, (self, ))
        return result

    def sqrt(self):
        result = Scalar(math.sqrt(self.value))
        record('sqrt', result, Type.SCALAR, (self, ))
        return result

    def to_unorm(self):
        result = min(255, max(0, round(self.value * 255)))
        return result

    def xor4(self, other):
        """Stupid method.  Can't figure out how to decompose it."""
        assert isinstance(other, Scalar)
        a, b = math.floor(self.value), math.floor(other.value)
        result = Scalar((a ^ b) >> 2 & 1)
        record('xor4', result, Type.SCALAR, (self, other))
        return result


class Angle(NumericBase):

    def __init__(self, radians=None, degrees=None, units=None):
        assert sum(x is None for x in (radians, degrees, units)) == 2
        if degrees is not None:
            radians = degrees * math.pi / 180
        elif units is not None:
            radians = units * math.tau / 1024
        self.radians = radians
        # record('angle', self, Type.ANGLE, ())

    def __repr__(self):
        return '{:.4}'.format(self)

    def __format__(self, format_spec):
        fa = format(self.radians / math.tau, format_spec)
        # 'angle x.xxx tau'
        # return '\u2220{}\U0001d70f'.format(fa)
        return '\u2220{}\u03c4'.format(fa)

    def sin(self):
        result = Scalar(math.sin(self.radians))
        record('sin', result, Type.SCALAR, (self, ))
        return result

    def cos(self):
        result = Scalar(math.cos(self.radians))
        record('cos', result, Type.SCALAR, (self, ))
        return result


class Vec3(NumericBase):

    def __init__(self, a, b, c):
        self.values = (Scalar(a), Scalar(b), Scalar(c))
        # record('vec', self, Type.VECTOR, self.values)

    def __repr__(self):
        a, b, c = self.values
        return '({} {} {})'.format(repr(a), repr(b), repr(c))

    def __format__(self, format_spec):
        a, b, c = (format(i, format_spec) for i in self.values)
        return '({} {} {})'.format(a, b, c)

    def __getitem__(self, index):
        assert index in (0, 1, 2)
        result = self.values[index]
        record('index', result, Type.SCALAR, (self, ))
        return result

    # def components(self):
    #     return iter(self.values)

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
        return [v.value for v in self.values]

    def __add__(self, other):
        assert all(isinstance(v, Scalar) for v in self.values)
        if isinstance(other, Scalar):
            a, b, c = self._access_values()
            s = other.value
            result = Vec3(a + s, b + s, c + s)
            record('add', result, Type.VECTOR, (self, other))
            return result
        elif isinstance(other, Vec3):
            a, b, c = self._access_values()
            d, e, f = other._access_values()
            result = Vec3(a + d, b + e, c + f)
            record('add', result, Type.VECTOR, (self, other))
            return result
        else:
            assert False, 'type(other) = {}'.format(type(other))

    def __sub__(self, other):
        if isinstance(other, Scalar):
            a, b, c = self._access_values()
            s = other.value
            result = Vec3(a - s, b - s, c - s)
            record('sub', result, Type.VECTOR, (self, other))
            return result
        elif isinstance(other, Vec3):
            a, b, c = self._access_values()
            d, e, f = other._access_values()
            result = Vec3(a - d, b - e, c - f)
            record('sub', result, Type.VECTOR, (self, other))
            return result
        else:
            assert False, 'type(other) = {}'.format(type(other))

    def __mul__(self, other):
        assert isinstance(other, Scalar), 'type(other) = {}'.format(type(other))
        a, b, c = self._access_values()
        s = other.value
        result = Vec3(a * s, b * s, c * s)
        record('mul', result, Type.VECTOR, (self, other))
        return result

    def __matmul__(self, other):
        """dot product"""
        assert isinstance(other, Vec3), 'type(other) = {}'.format(type(other))
        a, b, c = self._access_values()
        d, e, f = other._access_values()
        result = Scalar(a * d + b * e + c * f)
        record('dot', result, Type.SCALAR, (self, other))
        return result

    def normalize(self):
        return self * (Numerics().scalar(1) / (self @ self).sqrt())

    def rotate(self, angle, axis):
        assert isinstance(angle, Angle)
        assert axis == 'X' or axis == 'Y'
        sa, ca = angle.sin(), angle.cos()
        s, c = sa.value, ca.value
        x, y, z = self._access_values()
        if axis == 'X':
            result = Vec3(x, c * y - s * z, s * y + c * z)
            record('rotX', result, Type.VECTOR, (self, sa, ca))
            return result
        elif axis == 'Y':
            result = Vec3(c * x + s * z, y, c * z - s * x)
            record('rotY', result, Type.VECTOR, (self, sa, ca))
            return result

    def to_unorm(self):
        a, b, c = self.values
        result = RGBUnorm(a.to_unorm(), b.to_unorm(), c.to_unorm())
        record('unorm', result, Type.RGBUNORM, (self, ))
        return result

class RGBUnorm(NumericBase):

    def __init__(self, r, g, b):
        self.values = r, g, b

    def __repr__(self):
        return '#{:02x}{:02x}{:02x}'.format(*self.values)

    def as_tuple(self):
        return self.values


class Numerics:

    def __init__(self):
        self.frame_counter = -1
        self.pixel_counter = 0

    def scalar(self, value):
        result = Scalar(value)
        record('scalar\\n{}'.format(result), result, Type.SCALAR, ())
        return result

    def vec3(self, a, b, c):
        result = Vec3(a, b, c)
        record('vec', result, Type.VECTOR, result.values)
        return result

    def angle(self, radians=None, degrees=None, units=None):
        """units are 1/1024th of a circle."""
        assert sum(x is None for x in (radians, degrees, units)) == 2
        result = Angle(radians=radians, degrees=degrees, units=units)
        record('angle\\n{:.4}'.format(result), result, Type.ANGLE, ())
        return result


    def start_frame(self, *input_tuples):
        self.frame_counter += 1
        self._start_graph('Frame', *input_tuples)

    def end_frame(self, *output_tuples):
        self.pixel_counter = 0
        dotfile = 'frame-{:03}.dot'.format(self.frame_counter)
        self._end_graph(dotfile, *output_tuples)

    def start_pixel(self, *input_tuples):
        self._start_graph('Pixel', *input_tuples)

    def end_pixel(self, *output_tuples):
        dotfile = 'pixel-{:03}-{:04}.dot'.format(self.frame_counter,
                                                 self.pixel_counter)
        self.pixel_counter += 1
        self._end_graph(dotfile, *output_tuples)


    def _start_graph(self, title, *input_tuples):
        global current_graph, cg_test_count
        assert current_graph is None
        current_graph = dag.Dag(title)
        cg_test_count = 0
        for tup in input_tuples:
            for f in tup._fields:
                v = getattr(tup, f)
                label = '{}.{}'.format(tup.__class__.__name__, f)
                type_ = Type.identify(v).name.lower()
                current_graph.add_node(label, v, type_)
                current_graph.tag_input(v)

    def _end_graph(self, dotfile, *output_tuples):
        global current_graph
        assert current_graph
        for tup in output_tuples:
            for f in tup._fields:
                v = getattr(tup, f)
                out = copy.copy(v)
                label = '{}.{}'.format(tup.__class__.__name__, f)
                type_ = Type.identify(v)
                record(label, out, type_, (v, ))
                current_graph.tag_output(out)
        current_graph.propagate_constants()
        with open(dotfile, 'w') as out:
            out.write(current_graph.to_dot())
        current_graph = None


    def annotate_test(label):
        global next_test_label
        next_test_label = label
