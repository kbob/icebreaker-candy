import math

class Scalar:

    def __init__(self, value):
        if isinstance(value, Scalar):
            self.value = value.value
        else:
            self.value = float(value)

    def __repr__(self):
        return repr(self.value)

    def __format__(self, format_spec):
        return format(self.value, format_spec)

    def __add__(self, other):
        if isinstance(other, Scalar):
            return Scalar(self.value + other.value)
        elif isinstance(other, Vec3):
            a, b, c = other.values
            return Vec3(self + a, self + b, self + c)
        else:
            assert False, 'type(other) = {}'.format(type(other))

    def __sub__(self, other):
        assert isinstance(other, Scalar), 'type(other) = {}'.format(type(other))
        return Scalar(self.value - other.value)

    def __mul__(self, other):
        if isinstance(other, Scalar):
            return Scalar(self.value * other.value)
        elif isinstance(other, Vec3):
            a, b, c = other.values
            return Vec3(self * a, self * b, self * c)
        else:
            assert False, 'type(other) = {}'.format(type(other))

    def __truediv__(self, other):
        assert isinstance(other, Scalar), 'type(other) = {}'.format(type(other))
        return Scalar(self.value / other.value)

    def __lt__(self, other):
        assert other == 0, 'must compare to zero'
        return self.value < 0

    def abs(self):
        return Scalar(abs(self.value))

    def sqrt(self):
        return Scalar(math.sqrt(self.value))

    def clamp(self):
        if self.value > 1.0:
            return Scalar(1.0)
        return self

    def to_unorm(self):
        return min(255, max(0, round(self.value * 255)))

    def xor4(self, other):
        """Stupid method.  Can't figure out how to decompose it."""
        assert isinstance(other, Scalar)
        a, b = math.floor(self.value), math.floor(other.value)
        return Scalar((a ^ b) >> 2 & 1)


class Angle:

    def __init__(self, radians=None, degrees=None, units=None):
        assert sum(x is None for x in (radians, degrees, units)) == 2
        if degrees is not None:
            radians = degrees * math.pi / 180
        elif units is not None:
            radians = units * math.tau / 1024
        self.radians = radians

    def __repr__(self):
        return '{:.4}'.format(self)

    def __format__(self, format_spec):
        return '∠{}τ'.format(format(self.radians / math.tau, format_spec))

    def sin(self):
        return Scalar(math.sin(self.radians))

    def cos(self):
        return Scalar(math.cos(self.radians))


class Vec3:

    def __init__(self, a, b, c):
        self.values = (Scalar(a), Scalar(b), Scalar(c))

    def __repr__(self):
        a, b, c = self.values
        return '({} {} {})'.format(repr(a), repr(b), repr(c))

    def __format__(self, format_spec):
        a, b, c = (format(i, format_spec) for i in self.values)
        return '({} {} {})'.format(a, b, c)

    def __getitem__(self, index):
        assert index in (0, 1, 2)
        return self.values[index]

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

    def __add__(self, other):
        assert all(isinstance(v, Scalar) for v in self.values)
        if isinstance(other, Scalar):
            a, b, c = self.values
            s = other
            return Vec3(a + s, b + s, c + s)
        elif isinstance(other, Vec3):
            a, b, c = self.values
            d, e, f = other.values
            return Vec3(a + d, b + e, c + f)
        else:
            assert False, 'type(other) = {}'.format(type(other))

    def __sub__(self, other):
        if isinstance(other, Scalar):
            a, b, c = self.values
            s = other
            return Vec3(a - s, b - s, c - s)
        elif isinstance(other, Vec3):
            a, b, c = self.values
            d, e, f = other.values
            return Vec3(a - d, b - e, c - f)
        else:
            assert False, 'type(other) = {}'.format(type(other))

    def __mul__(self, other):
        assert isinstance(other, Scalar), 'type(other) = {}'.format(type(other))
        a, b, c = self.values
        s = other
        return Vec3(a * s, b * s, c * s)

    def __matmul__(self, other):
        """dot product"""
        assert isinstance(other, Vec3), 'type(other) = {}'.format(type(other))
        a, b, c = self.values
        d, e, f = other.values
        return Scalar(a * d + b * e + c * f)

    def normalize(self):
        return self * (Scalar(1) / (self @ self).sqrt())

    def clamp(self):
        a, b, c = self.values
        return Vec3(a.clamp(), b.clamp(), c.clamp())

    def rotate(self, angle, axis):
        assert isinstance(angle, Angle)
        assert axis == 'X' or axis == 'Y'
        s, c = angle.sin(), angle.cos()
        x, y, z = self.values
        if axis == 'X':
            return Vec3(x, c * y - s * z, s * y + c * z)
        elif axis == 'Y':
            return Vec3(c * x + s * z, y, c * z - s * x)

    def to_unorm(self):
        a, b, c = self.values
        return (a.to_unorm(), b.to_unorm(), c.to_unorm())

class Numerics:

    def start_frame(self, *args):
        pass

    def end_frame(self, *args):
        pass

    def start_pixel(self, *args):
        pass

    def end_pixel(self, *args):
        pass

    def scalar(self, value):
        return Scalar(value)

    def vec3(self, a, b, c):
        return Vec3(a, b, c)

    def angle(self, radians=None, degrees=None, units=None):
        """units are 1/1024th of a circle."""
        assert sum(x is None for x in (radians, degrees, units)) == 2
        return Angle(radians=radians, degrees=degrees, units=units)
