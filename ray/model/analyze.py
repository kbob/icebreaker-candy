#!/usr/bin/env python3

# Read all the dotfiles.
# Generate each graph's signature.
# Check for missing signatures.

from collections import Counter, defaultdict
import os
from pprint import pprint
import re
import sys

import dag

match_node = re.compile(r'''
    (?P<name> node\d+ )
    [ ]
    \[
        (?P<attrs> .* )
    \];
    \Z
    ''', re.VERBOSE).match

match_edge = re.compile(r'''
    (?P<src>node\d+)
    [ ] -> [ ]
    (?P<dst>node\d+)
    [ ]
    \[
        (?P<attrs>.*)
    \];
    \Z
    ''', re.VERBOSE).match

find_attrs = re.compile(r'''
    (?P<name> \w+ )
    =
    (?:
        (?P<v0> \w+ )   # unquoted word
     |
        "
        (?P<v1> .*? )   # quoted string
        "
    )
    ''', re.VERBOSE).findall

class HashSnowflake:
    def __init__(self, value):
        self.value = value
    def __hash__(self):
        return id(self)
    def __repr__(self):
        return repr(self.value)

def read_dotfiles():
    i = 0
    for (dir, subdirs, files) in os.walk('dot'):
        files.sort()
        for f in files:
            if f.endswith('.dot'):
                g= read_dotfile(os.path.join(dir, f))
                yield g
                i += 1
                if i == 100:
                    return


def read_dotfile(path):
    # print(f'reading {path}')
    with open(path) as f:
        title = os.path.splitext(os.path.basename(path))[0]
        g = dag.Dag(title)
        node_map = {}
        for line in f:
            line = line.strip()
            if line.startswith('digraph'):
                continue
            if line == '}':
                continue
            m = match_node(line)
            if m:
                # print('node', m.groupdict())
                name, attrs = m.groups()
                attrs = {key: v0 + v1 for (key, v0, v1) in find_attrs(attrs)}
                # print(name)
                # for a in attrs:
                #     print('   {}: {!a}'.format(a, attrs[a]))
                # print('attrs', attrs)
                node_value = HashSnowflake(attrs['value'])
                node_map[name] = node_value
                g.add_node(attrs['label'], node_value, attrs['type'])
                # print(attrs)
                if attrs.get('input', False):
                    g.tag_input(node_value)
                if attrs.get('output', False):
                    g.tag_output(node_value)
                if attrs.get('const', False):
                    g.tag_constant(node_value)
                if attrs.get('test', False):
                    g.tag_test(node_value)
            else:
                m = match_edge(line)
                if m:
                    # print('edge', m.groupdict())
                    src, dst, attrs = m.groups()
                    src = node_map[src]
                    dst = node_map[dst]
                    attrs = {k: v0 + v1 for (k, v0, v1) in find_attrs(attrs)}
                    g.add_edge(src, dst)
                    # discard edge attributes
                else:
                    print('no match', repr(line), file=sys.stderr)
                    raise RuntimeError(path)
    return g


def branch_signature(g):
    sig = ''
    for n in sorted(g.nodes):
        if n in g.tests:
            sig += {'true': 'T', 'false': 'F'}[n.obj.value]
    return sig


def collect_constants(g):
    return [(node.label, node.obj.value)
            for node in sorted(g.nodes)
            if g.is_constant(node.obj)]

def check_constants(dags):
    dag0 = dags[0]
    const0 = collect_constants(dag0)
    for g in dags[1:]:
        const = collect_constants(g)
        if const != const0:
            print('constant mismatch')
            print(f'expected ({dag0.name}):')
            pprint(const0)
            print(f'found ({g.name}):')
            pprint(const)
            print()
            for (a, b) in zip(const, const0):
                if a != b:
                    print('diff')
                    print('  ', a)
                    print('  ', b)
        assert const == const0


def check_isomorphism(dags):
    dag0 = dags[0]
    for g in dags[1:]:
        for (n0, n1) in zip(sorted(dag0.nodes), sorted(g.nodes)):
            assert n0.name == n1.name
            assert n0.label == n1.label
            assert n0.type == n1.type
        for (e0, e1) in zip(dag0.edges, g.edges):
            assert e0.src.name == e1.src.name
            assert e0.dst.name == e1.dst.name


def print_values(dags):
    d = defaultdict(Counter)
    for g in dags:
        for node in sorted(g.nodes):
            if not g.is_constant(node.obj):
                d[node.name][node.obj.value] += 1
    # print(len(d))
    # pprint(d)
    # exit()


def analyze():
    frame_dags = []
    pixel_dags = defaultdict(list)
    for g in read_dotfiles():
        if g.name.startswith('frame'):
            frame_dags.append(g)
        else:
            assert g.name.startswith('pixel')
            sig = branch_signature(g)
            pixel_dags[sig].append(g)
    for sig in sorted(pixel_dags):
        dags = pixel_dags[sig]
        node_count = len(dags[0].nodes)
        for g in pixel_dags[sig]:
            assert len(g.nodes) == node_count
        print(f'sig {sig}: {len(dags)} pixels, {node_count} nodes')
        # print('sig {}: {} pixels, {} nodes'.format(sig, len(dags), node_count))
        check_constants(dags)
        check_isomorphism(dags)
        print_values(dags)

if __name__ == '__main__':
    analyze()
