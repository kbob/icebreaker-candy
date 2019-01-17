from collections import namedtuple
import io


class Node(namedtuple('Node', 'name label obj type attrs')):
    # Use a subclass so clients can add attributes.
    def __hash__(self):
        # attrs is mutable; does not hash.
        return hash(self[:-1])

    def predecessors(self, dag):
        return [edge.src for edge in dag.edges if edge.dst == self]


class Edge(namedtuple('Edge', 'src dst')):
    # Use a subclass so clients can add attributes.
    pass


class Dag:

    def __init__(self, name):
        self.name = name
        self.node_count = 0
        self._nodes = set()
        self.edges = []
        self.node_map = {}
        self.inputs = set()
        self.outputs = set()
        self.constants = set()
        self.tests = set()
        pass

    def add_node(self, label, obj, type):
        if obj not in self.node_map:
            new_name = 'node{:03}'.format(self.node_count)
            self.node_count += 1
            new_node = Node(new_name, label, obj, type, {})
            self._nodes.add(new_node)
            self.node_map[obj] = new_node

    def add_edge(self, source, dest):
        snode = self.node_map[source]
        dnode = self.node_map[dest]
        self.edges.append(Edge(snode, dnode))

    def add_node_attr(self, obj, key, value):
        node = self.node_map[obj]
        node.attrs[key] = value

    def is_input(self, obj):
        node = self.node_map[obj]
        return node in self.inputs

    def is_output(self, obj):
        node = self.node_map[obj]
        return node in self.outputs

    def is_constant(self, obj):
        node = self.node_map[obj]
        return node in self.constants

    def is_test(self, obj):
        node = self.node_map[obj]
        return node in self.tests

    def tag_input(self, obj):
        inode = self.node_map[obj]
        self.inputs.add(inode)

    def tag_output(self, obj):
        onode = self.node_map[obj]
        self.outputs.add(onode)

    def tag_constant(self, obj):
        cnode = self.node_map[obj]
        self.constants.add(cnode)

    def tag_test(self, obj):
        tnode = self.node_map[obj]
        self.tests.add(tnode)

    def propagate_constants(self):
        done = False
        while not done:
            done = True
            for node in self._nodes:
                if node in self.constants:
                    continue
                pred = node.predecessors(self)
                if pred and all(p in self.constants for p in pred):
                    self.constants.add(node)
                    done = False

    def to_dot(self):
        with io.StringIO() as f:
            print('digraph {} {{'.format(self.name), file=f)
            for n in sorted(self._nodes, key=lambda n: n.name):
                i = n in self.inputs
                o = n in self.outputs
                c = n in self.constants
                t = 'is_' in n.label    # XXX better predicate needed

                attrs = 'label="{}"'.format(asciify(n.label))

                if i:
                    attrs += ' input=true'
                if o:
                    attrs += ' output=true'
                if c:
                    attrs += ' const=true'
                if t:
                    attrs += ' test=true'

                # shape: I/O override const
                if i:
                    attrs += ' shape=invhouse'
                elif o:
                    attrs += ' shape=house'
                elif t:
                    attrs += ' shape=diamond'
                elif c:
                    attrs += ' shape=box'

                # color: const overrides I/O
                if c:
                    attrs += ' color=blue'
                elif i:
                    attrs += ' color=green'
                elif o:
                    attrs += ' color=red'

                # custom attributes
                attrs += f' type={n.type}'
                for (k, v) in sorted(n.attrs.items()):
                    attrs += f' {k}="{asciify(v)}"'

                print('    {} [{}];'.format(n.name, attrs), file=f)
            for e in self.edges:
                attrs = 'label="{}"'.format(e.src.type)
                if e.src.type == 'vector':
                    attrs += ' penwidth=3'
                elif e.src.type == 'rgbunorm':
                    attrs += ' penwidth=2'
                elif e.src.type == 'bool':
                    attrs += ' style=dashed'
                print(f'    {e.src.name} -> {e.dst.name} [{attrs}];', file=f)
            print('}', file=f)
            return f.getvalue()


def asciify(s):
    return s.encode('ascii', 'xmlcharrefreplace').decode('ascii')
