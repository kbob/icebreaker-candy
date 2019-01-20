import inspect
import io
import math
import os

import trickery


# class Node(namedtuple('Node', 'op ')):
#     pass

class Recorder:
    def __init__(self, title):
        self.title = title
        self.nodes = set()
        self.inputs = set()
        self.outputs = set()
        self.tests = set()
        self.consts = set()
        self.dangling_test = None

    def record(self, op, result, operands, sig=None):
        # print(f'record {op} <= {operands}')
        try:
            print(f'record {op} = {result:.4}')
        except TypeError:
            print(f'record {op} = {result}')
        if sig is None:
            sig = trickery.caller_signature(2, 5)
        for opn in operands:
            if opn not in self.nodes:
                self.record('const', opn, (), sig=getattr(opn, 'name', ''))
        assert not hasattr(result, 'op')
        result.op = op
        result.operands = operands
        result.sig = sig
        result.const = operands and all(opn.const for opn in operands)
        result.index = len(self.nodes)
        result.name = ''
        result.input = False
        result.output = False
        result.test = False
        # Dijkstra: ComesFrom Considered Beneficial
        result.comes_from = self.dangling_test
        self.dangling_test = None
        self.nodes.add(result)
        if result.const:
            self.tag_const(result)

    def tag_input(self, node):
        node.input = True
        self.inputs.add(node)

    def tag_output(self, node):
        node.output = True
        self.outputs.add(node)

    def tag_test(self, node):
        node.test = True
        self.tests.add(node)
        assert self.dangling_test is None
        self.dangling_test = node

    def tag_const(self, node):
        node.const = True
        self.const.add(node)

    def _node_label(self, node):
        label = node.op
        if node.name:
            label += ' ' + node.name
        return label

    def to_dot(self):
        self._check_complete()
        with io.StringIO() as f:
            print(f'digraph {self.title} {{', file=f)
            for node in sorted(self.nodes, key=lambda n: n.index):
                attrs = f'label="{self._node_label(node)}"'

                # shape: I/O override const
                if node.input:
                    attrs += ' shape=invhouse'
                elif node.output:
                    attrs += ' shape=house'
                elif node.test:
                    attrs += ' shape=diamond'
                elif node.const:
                    attrs += ' shape=box'

                # color: const overrides I/O
                if node.const:
                    attrs += ' color=blue'
                elif node.input:
                    attrs += ' color=green'
                elif node.output:
                    attrs += ' color=red'

                if node.input:
                    attrs += ' input=true'
                if node.output:
                    attrs += ' output=true'
                if node.const:
                    attrs += ' const=true'
                if node.test:
                    attrs += ' test=true'

                attrs += f' sig="{node.sig}"'

                print(f'    node{node.index:03} [{attrs}];', file=f)
            def print_ancestor_edges(node):
                if node not in self.inputs:
                    for opn in node.operands:
                        print_ancestor_edges(opn)
                        src = f'node{opn.index:03}'
                        dst = f'node{node.index:03}'
                        node_type_name = type(node).__name__.lower()
                        attrs = f'label={node_type_name}'
                        if node_type_name == 'vec3':
                            attrs += ' penwidth=3'
                        elif node_type_name == 'rgbunorm':
                            attrs += ' penwidth=2'
                        # elif node_type_name == 'boolean':
                        #     attrs += ' style=dashed'
                        print(f'    {src} -> {dst} [{attrs}];', file=f)
                    if node.comes_from:
                        cf = node.comes_from
                        src = f'node{cf.index:03}'
                        dst = f'node{node.index:03}'
                        attrs = 'label="flow" style=dashed'
                        print(f'    {src} -> {dst} [{attrs}];', file=f)
            for out in self.outputs:
                print_ancestor_edges(out)
            print('}', file=f)
            return f.getvalue()

    # def _ancestors_postorder(self, node):
    #     if node not in self.inputs:
    #         for opn in node.operands:
    #             for a in self._ancestors_postorder(opn):
    #                 yield a
    #         if not hasattr(node, 'comes_from'):
    #             print('no copy_from:', node)
    #         if node.comes_from:
    #             for a in self._ancestors_postorder(node.comes_from):
    #                 yield a
    #     yield node
    #
    def nodes_postorder(self):
        seen = set()
        def ancestors_postorder(node):
            if node not in seen:
                if node not in self.inputs:
                    for opn in node.operands:
                        for a in ancestors_postorder(opn):
                            yield a
                    if node.comes_from:
                        for a in ancestors_postorder(node.comes_from):
                            yield a
            seen.add(node)
            yield node

        for out in self.outputs:
            for n in ancestors_postorder(out):
                yield(n)



    def _check_complete(self):
        print('inputs', len(self.inputs))
        print('outputs', len(self.outputs))
        print('tests', len(self.tests))
        print('const', len(self.consts))
        # for n in self.nodes_postorder():
        #     print(n)
        nodes = set(self.nodes_postorder())

        # def ancestors(node):
        #     a = set()
        #     if node not in self.inputs:
        #         for opn in node.operands:
        #             a.add(opn)
        #             a |= ancestors(opn)
        #         if node.comes_from:
        #             a.add(node.comes_from)
        #     print(f'ancestors({node}) => {a}')
        #     return a
        # nodes = set()
        # for node in self.outputs:
        #     nodes.add(node)
        #     nodes |= ancestors(node)
        print(len(nodes))
        print(len(self.nodes))
        for n in nodes:
            try:
                print(f'   {n:.4}')
            except TypeError:
                print(f'   {n}')
        assert nodes == self.nodes

current_recorder = None

# def record(op, result, operands, sig=None):
#     print(f'record {op} <= {operands}')
#     if sig is None:
#         sig = trickery.caller_signature(1, 4)
#
#     if current_recorder:
#         for opn in operands:
#             if opn not in current_recorder.nodes:
#                 current_recorder.nodes.add(opn)
#                 current_recorder.tag_const(opn)
#     assert not hasattr(result, 'op')
#     result.op = op
#     result.operands = operands
#     result.sig = sig
#     result.const = operands and all(opn.const for opn in operands)
#     result.index = len(current_recorder.nodes) if current_recorder else 0
#     result.name = ''
#     result.input = False
#     result.output = False
#     result.test = False
#     # Dijkstra: ComesFrom Considered Beneficial
#     if current_recorder:
#         result.comes_from = self.dangling_test
#         self.dangling_test = None
#     self.nodes.add(result)
#
#     def _record(self, op, result, operands, sig=None):
#         for opn in operands:
#             if opn not in self.nodes:
#                 self.nodes.add(opn)
#                 self.tag_const(opn)


def record(op, result, operands, sig=None):
    if current_recorder:
        current_recorder.record(op, result, operands, sig)


class Scalar:

    # def __new__(cls, *args):
    #     if len(args) != 1:
    #         print(f'{len(args)} args')
    #     if not args:
    #         print('no args')
    #         return super().__new__(cls)
    #     value = args[0]
    #     if args and isinstance(value, Scalar):
    #         return value
    #     else:
    #         result = super().__new__(cls)
    #         result.value = float(value)
    #         return result

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
        if current_recorder:
            current_recorder.tag_test(result)
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
            a, b, c = args
            # if (a, b, c) == (0, 0, 0.9):
            #     raise RuntimeError()
            self.values = (Scalar(a), Scalar(b), Scalar(c))
            # record('vec.sss', self, self.values)
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
        result = self.values[index]
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
        return [v.value for v in self.values]

    def __add__(self, other):
        assert all(isinstance(v, Scalar) for v in self.values)
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
        return self * (Numerics().scalar(1) / (self @ self).sqrt())

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
        a, b, c = self.values
        result = RGBUnorm(a.to_unorm(), b.to_unorm(), c.to_unorm())
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
        record('scalar', result, (), sig=sig)
        return result

    def vec3(self, a, b, c, sig=None):
        result = Vec3(a, b, c)
        record('vec.sss', result, result.values, sig=sig)
        return result

    def angle(self, radians=None, degrees=None, units=None, sig=None):
        "units are 1/1024th of a circle."
        assert sum(x is None for x in (radians, degrees, units)) == 2
        result = Angle(radians=radians, degrees=degrees, units=units)
        record('angle', result, (), sig=sig)
        return result


    def start_frame(self, *input_tuples):
        self.frame_counter += 1
        # self._start_graph('Frame', *input_tuples)

    def end_frame(self, *output_tuples):
        self.pixel_counter = 0
        fnum = f'{self.frame_counter:03}'
        dotfile = f'frame-{fnum}.dot'
        dotfile = os.path.join('dot', fnum, dotfile)
        # self._end_graph(dotfile, *output_tuples)

    def start_pixel(self, *input_tuples):
        self._start_graph('Pixel', *input_tuples)

    def end_pixel(self, *output_tuples):
        fnum = '{:03}'.format(self.frame_counter)
        dotfile = 'pixel-{}-{:04}.dot'.format(fnum, self.pixel_counter)
        dotfile = os.path.join('dot', fnum, dotfile)
        self.pixel_counter += 1
        self._end_graph(dotfile, *output_tuples)


    def _start_graph(self, title, *input_tuples):
        global current_recorder
        assert current_recorder is None
        current_recorder = Recorder(title)
        for tup in input_tuples:
            tup_name = tup.__class__.__name__
            for f in tup._fields:
                v = getattr(tup, f)
                label = f'{tup_name}.{f}'
                record(label, v, ())
                current_recorder.tag_input(v)

    def _end_graph(self, dotfile, *output_tuples):
        global current_recorder
        assert current_recorder
        # sinks = []
        for tup in output_tuples:
            tup_name = tup.__class__.__name__
            for f in tup._fields:
                v = getattr(tup, f)
                try:
                    out = type(v)(v)
                except:
                    print('v', v)
                    print('type(v)', type(v))
                    raise
                # label = f'{tup_name}.{f}'
                # record(label, out, (v, ), sig=label)
                out.label = f'{tup_name}.{f}'
                # out.output = True
                current_recorder.tag_output(out)
                # sinks.append((v, out))
        # current_graph.propagate_constants()
        # for (v, out) in sinks:
        #     if current_graph.is_constant(out):
        #         v.constant = True
        os.makedirs(os.path.dirname(dotfile), exist_ok=True)
        with open(dotfile, 'w') as out:
            out.write(current_recorder.to_dot())
        current_recorder = None
