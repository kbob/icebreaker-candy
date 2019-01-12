from collections import namedtuple
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
        self.nodes = set()
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
        self.nodes.add(new_node)
        self.node_map[value] = new_node

    def add_edge(self, source, dest):
        snode = self.node_map[source]
        dnode = self.node_map[dest]
        self.edges.append(Edge(snode, dnode))

    def tag_input(self, value):
        snode = self.node_map[value]
        self.inputs.add(snode)

    def tag_output(self, value):
        snode = self.node_map[value]
        self.outputs.add(snode)

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
            attrs = 'label="{}"'.format(n.label)
            try:
                attrs += ' value="{:.4}"'.format(n.value)
            except (TypeError, ValueError):
                attrs += ' value="{}"'.format(n.value)
            if n in self.inputs:
                attrs += ' color=green shape=invhouse input=true'
            if n in self.outputs:
                attrs += ' color=red shape=house output=true'
            if 'is_' in n.label:
                attrs += ' shape=diamond test=true'
            if n in self.constants and n not in self.outputs:
                attrs += ' color=blue shape=box const=true'
            print('    {} [{}];'.format(n.name, attrs), file=f)
        for e in self.edges:
            attrs = 'label="{}"'.format(e.src.type)
            if e.src.type =='vector':
                attrs += ' penwidth=3'
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
