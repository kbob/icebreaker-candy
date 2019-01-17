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


# Collect regular expressions here to make them easy to find.
# Names are "verb_object" where verb is an re method name.
# Verbose syntax might be more readable; IDK.

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

split_on_entities = re.compile(r'''
    & .*? ;
    ''', re.VERBOSE).split

match_branch_label = re.compile(r'''
    (?P<index> \d+ )
    \\n
    is_neg
    \\n
    ''', re.VERBOSE).match


class HashSnowflake:
    """Each one is a special snowflake.
       Wrap a non-unique object in an object that has a unique hash value.

       This should probably be in trickery.
    """
    def __init__(self, obj):
        self.obj = obj

    def __hash__(self):
        return id(self)

    def __repr__(self):
        return repr(self.obj)


def numeric_value(node):
    str_value = node.attrs['value']
    if node.type == 'scalar':
        return float(str_value)
    elif node.type == 'vector':
        return tuple(float(i) for i in str_value[1:-1].split())
    elif node.type == 'angle':
        return float(split_on_entities(str_value)[1])
    elif node.type == 'bool':
        return bool(str_value.title())
    elif node.type == 'rgbunorm':
        return int(str_value.lstrip('#'), 0x10)
    else:
        assert False, f'unknown node type {node.type}'


def short_label(node):
    label = node.label
    m = match_branch_label(label)
    if m:
        label = f'branch {m.group("index")}'
    label = label.replace(r'\n', ' ')
    return label


def read_dotfiles():
    i = 0
    for (dir, subdirs, files) in os.walk('dot'):
        files.sort()
        for f in files:
            if f.endswith('.dot'):
                g= read_dotfile(os.path.join(dir, f))
                yield g
                i += 1
                # if i % 100 == 0:
                #     break


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
                name, attrs = m.groups()
                attrs = {key: v0 + v1 for (key, v0, v1) in find_attrs(attrs)}
                node_obj = HashSnowflake(attrs['label'])
                node_map[name] = node_obj
                g.add_node(attrs['label'], node_obj, attrs['type'])
                g.add_node_attr(node_obj, 'value', attrs['value'])
                g.add_node_attr(node_obj, 'sig', attrs['sig'])
                if attrs.get('input', False):
                    g.tag_input(node_obj)
                if attrs.get('output', False):
                    g.tag_output(node_obj)
                if attrs.get('const', False):
                    g.tag_constant(node_obj)
                    g.add_node_attr(node_obj, 'const', True)
                if attrs.get('test', False):
                    g.tag_test(node_obj)
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


def read_dags():
    frame_dags = []
    pixel_dags = []
    for g in read_dotfiles():
        if g.name.startswith('frame'):
            frame_dags.append(g)
        else:
            assert g.name.startswith('pixel')
            pixel_dags.append(g)
    return (frame_dags, pixel_dags)


def branch_signature(g):
    sig = ''
    for n in sorted(g._nodes):
        if n in g.tests:
            sig += {True: 'T', False: 'F'}[numeric_value(n)]
    return sig

def group_dags_by_path(dags):
    by_path = defaultdict(list)
    for g in dags:
        by_path[branch_signature(g)].append(g)
    return by_path

def collect_nodes(dags):
    by_sig = defaultdict(list)
    for g in dags:
        for n in g._nodes:
            by_sig[n.attrs['sig']].append(n)
    return sorted(by_sig.values(), key=lambda nl: nl[0].name)


def check_isomorphism(dags_by_path):
    for (path, dags) in dags_by_path.items():
        dag0 = dags[0]
        for g in dags[1:]:
            for (n0, n1) in zip(sorted(dag0._nodes), sorted(g._nodes)):
                assert n0.name == n1.name
                assert n0.label == n1.label
                assert n0.type == n1.type
            for (e0, e1) in zip(dag0.edges, g.edges):
                assert e0.src.name == e1.src.name
                assert e0.dst.name == e1.dst.name

def check_constants(node_lists):
    for nodes in node_lists:
        are_const = ['const' in n.attrs for n in nodes]
        if any(are_const):
            if not all(are_const):
                label = short_label(nodes[0])
                print(f'ERROR: node {label} is sometimes const')
            values = {n.attrs['value'] for n in nodes}
            if len(values) > 1:
                label = short_label(nodes[0])
                print(f'ERROR: const node {label} has multiple values {values}')

def print_value_ranges(node_lists, heading):
    print(heading)
    print()
    for node_list in node_lists:
        n0 = node_list[0]
        if n0.attrs.get('const', False):
            continue
        values = [numeric_value(n) for n in node_list]
        label = short_label(n0)
        if n0.type == 'vector':
            v0 = [v[0] for v in values]
            v1 = [v[1] for v in values]
            v2 = [v[2] for v in values]
            minv = str((min(v0), min(v1), min(v2)))
            maxv = str((max(v0), max(v1), max(v2)))
        else:
            minv = min(values)
            maxv = max(values)
        print(f'{label:20} {minv:>28} {maxv:>28}')
    print()


def analyze():
    frame_dags, pixel_dags = read_dags()
    frame_dags_by_path = group_dags_by_path(frame_dags)
    pixel_dags_by_path = group_dags_by_path(pixel_dags)
    frame_dag_nodes = collect_nodes(frame_dags)
    pixel_dag_nodes = collect_nodes(pixel_dags)

    check_isomorphism(frame_dags_by_path)
    check_isomorphism(pixel_dags_by_path)
    check_constants(frame_dag_nodes)
    check_constants(pixel_dag_nodes)

    print_value_ranges(frame_dag_nodes, 'FRAME NODE RANGES')
    print_value_ranges(pixel_dag_nodes, 'PIXEL NODE RANGES')


if __name__ == '__main__':
    analyze()
