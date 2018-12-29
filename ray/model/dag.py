from collections import namedtuple
import io


class Node(namedtuple('Node', 'name label value type')):
    pass


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

    def to_dot(self):
        f = io.StringIO()
        print('digraph {} {{'.format(self.name), file=f)
        for n in sorted(self.nodes, key=lambda n: n.name):
            extra = ''
            if n in self.inputs:
                extra += ' color=green shape=invhouse'
            if n in self.outputs:
                extra += ' color=red shape=house'
            if n.label.startswith('is_'):
                extra += ' shape=diamond'
            if n.label.startswith('const'):
                extra += ' color=blue shape=box'
            print('    {} [label="{}"{}];'.format(n.name, n.label, extra),
                  file=f)
        for e in self.edges:
            print('    {} -> {} [label={}];'.format(e.src.name, e.dst.name, e.src.type), file=f)
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
