from collections import namedtuple, OrderedDict
import io


class Node(namedtuple('Node', 'name label value type')):

    def predecessors(self, dag):
        return [edge.src for edge in dag.edges if edge.dst == self]


class Edge(namedtuple('Edge', 'src dst')):
    pass


class Dag:

    def __init__(self, name):
        self.name = name
        self.node_count = 0
        self.nodes = OrderedDict()
        self.edges = []
        self.node_map = {}
        self.inputs = set()
        self.outputs = set()
        self.constants = set()
        pass

    def add_node(self, label, value, type):
        new_name = 'node{:03}'.format(self.node_count)
        self.node_count += 1
        new_node = Node(new_name, label, value, type)
        # self.nodes.add(new_node)
        self.nodes[new_node] = None
        self.node_map[value] = new_node

    def add_edge(self, source, dest):
        snode = self.node_map[source]
        dnode = self.node_map[dest]
        self.edges.append(Edge(snode, dnode))

    def is_input(self, value):
        node = self.node_map[value]
        return node in self.inputs

    def is_output(self, value):
        node = self.node_map[value]
        return node in self.outputs

    def is_constant(self, value):
        node = self.node_map[value]
        return node in self.constants

    def tag_input(self, value):
        inode = self.node_map[value]
        self.inputs.add(inode)

    def tag_output(self, value):
        onode = self.node_map[value]
        self.outputs.add(onode)

    def tag_constant(self, value):
        cnode = self.node_map[value]
        self.constants.add(cnode)

    def propagate_constants(self):
        done = False
        while not done:
            done = True
            for node in self.nodes:
                if node in self.constants:
                    continue
                pred = node.predecessors(self)
                if pred and all(p in self.constants for p in pred):
                    self.constants.add(node)
                    done = False

    def to_dot(self):
        f = io.StringIO()
        print('digraph {} {{'.format(self.name), file=f)
        for n in sorted(self.nodes, key=lambda n: n.name):
            i = n in self.inputs
            o = n in self.outputs
            c = n in self.constants
            t = 'is_' in n.label    # XXX better predicate needed

            attrs = 'label="{}"'.format(n.label)

            # custom attributes
            try:
                attrs += ' value="{:.4}"'.format(n.value)
            except (TypeError, ValueError):
                attrs += ' value="{}"'.format(n.value)
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

            # if n in self.inputs:
            #     attrs += ' color=green shape=invhouse input=true'
            # if n in self.outputs:
            #     attrs += ' color=red shape=house output=true'
            # if 'is_' in n.label:
            #     attrs += ' shape=diamond test=true'
            # if n in self.constants and n not in self.outputs:
            #     attrs += ' color=blue shape=box const=true'
            print('    {} [{}];'.format(n.name, attrs), file=f)
        for e in self.edges:
            attrs = 'label="{}"'.format(e.src.type)
            if e.src.type == 'vector':
                attrs += ' penwidth=3'
            elif e.src.type == 'rgbunorm':
                attrs += ' penwidth=2'
            print('    {} -> {} [{}];'.format(e.src.name, e.dst.name, attrs),
                  file=f)
        print('}', file=f)
        return f.getvalue()
        f.close()


def test_me():
    d = Dag('evolution')
    d.add_node('pony', 'red')
    d.add_node('narwhal', 'wet')
    d.add_node('s&times;s', 'mythical')
    d.add_edge('mythical', 'red')
    d.add_edge('mythical', 'wet')
    d.tag_input('red')
    d.tag_output('mythical')
    print(d.to_dot().strip())

    import pydotplus
    pydot_graph = pydotplus.graph_from_dot_data(d.to_dot())
    with open('dumb.png', 'wb') as f:
        f. write(pydot_graph.create_png())


if __name__ == '__main__':
    test_me()
