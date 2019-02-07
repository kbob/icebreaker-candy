#!/usr/bin/env python3

from collections import Counter, defaultdict, namedtuple
import copy
from itertools import count
import os
from pprint import pprint
import re

import dag


match_inst = re.compile(r'''
    \s*
    (?P<op> [\.\w]+ )
    \s+
    (?P<id> t \d+ )
    \s+
    (?P<operands>
        (?:
            t \d+ (?: \s* , \s* t \d+ )*
        )?
    )
    \s*
    \#
    \s*
    " (?P<value> .*? ) "
    \s*
    (?P<sig> .*? )
    \s*
    \Z
    ''', re.VERBOSE).match

find_operands = re.compile(r'''
    t \d+
    ''', re.VERBOSE).findall

match_begin_frame = re.compile(r'''
    \s* \# \s* BEGIN \s+
    frame \s+ (?P<frame> \d+ ) \s*
    \Z
    ''', re.VERBOSE).match

match_end_frame = re.compile(r'''
    \s* \# \s* END \s+
    frame \s+ (?P<frame> \d+ ) \s*
    \Z
    ''', re.VERBOSE).match

match_begin_pixel = re.compile(r'''
    \s* \# \s* BEGIN \s+
    frame \s+ (?P<frame> \d+ ) \s+
    pixel \s+ (?P<pixel> \d+ ) \s*
    \Z
    ''', re.VERBOSE).match

match_end_pixel = re.compile(r'''
    \s* \# \s* END \s+
    frame \s+ (?P<frame> \d+ ) \s+
    pixel \s+ (?P<pixel> \d+ ) \s*
    \Z
    ''', re.VERBOSE).match


class Inst(namedtuple('Inst', 'id op operands sig value')):

    @classmethod
    def from_str(cls, str):
        m = match_inst(str)
        if m:
            d = dict(m.groupdict())
            d['operands'] = tuple(find_operands(d['operands']))
            return cls(**d)

    def __repr__(self):
        op = self.op
        id = self.id
        operands = ', '.join(str(o) for o in self.operands)
        value = self.value
        sig = self.sig
        # if len(sig) > 30:
        #     sig = sig[:27] + "..."
        return f'{op:8} {id:6} {operands:19} # "{value}" {sig}'

    @property
    def is_test(self):
        return self.op in {'is_neg.s', 'bneg.s', 'bnneg.s'}
        # return self.op.startswith('is_') or self.op.startswith('b')

    @property
    def is_const(self):
        if self.op not in {'scalar', 'vec.sss', 'angle'}:
            return False
        return not self.sig.startswith('(')


class Trace(list):

    def __init__(self, iterable=(), name=''):
        super().__init__(iterable)
        self.name = name

    def __repr__(self):
        try:
            return self.path
        except AttributeError:
            return repr(super())


class Traces(namedtuple('Sections', 'extern frames pixels')):
    pass


class Maps(namedtuple('Maps', 'id2sig sig2id')):
    pass

class Label:
    """A label names a code location.  A label's name is not defined
       until the label is placed.
    """

    counter = 0

    def __init__(self):
        self.traces = []
        self._name = None

    def __repr__(self):
        return self.name

    @property
    def placed(self):
        return self._name is not None

    @property
    def name(self):
        if self.placed:
            return self._name
        return f'<unplaced Label {id(self)}>'

    def place(self):
        assert not self.placed
        self._name = f'L{type(self).counter}'
        type(self).counter += 1


def read_log(file_name='log'):
    extern = Trace()
    frames = []
    pixels = defaultdict(Trace)
    current = extern
    with open(file_name) as log:
        for line in log:
            line = line.rstrip('\n')
            inst = Inst.from_str(line)
            if inst:
                current.append(inst)
                continue

            m = match_begin_frame(line)
            if m:
                frame = int(m.group('frame'))
                while frame >= len(frames):
                    frames.append(Trace(name=f'frame {frame}'))
                current = frames[frame]
                continue

            m = match_end_frame(line)
            if m:
                current = extern
                continue

            m = match_begin_pixel(line)
            if m:
                frame = int(m.group('frame'))
                pixel = int(m.group('pixel'))
                current = pixels[(frame, pixel)]
                current.name = f'frame {frame} pixel {pixel}'
                continue

            m = match_end_pixel(line)
            if m:
                current = extern
                continue

            print('WARNING: unrecognized')
            print('   ', line)
            print()
    return Traces(extern, frames, pixels)

def group_traces_by_path(traces):
    by_path = defaultdict(list)
    for trace in traces:
        path = ''
        for i in trace:
            if i.is_test:
                path += i.value[0]
        trace.path = path
        by_path[path].append(trace)
    return by_path


def collect_insts(traces):
    insts = defaultdict(list)
    for trace in traces:
        for i in trace:
            insts[i.sig].append(i)
    return list(insts.values())


def trace_exemplars(traces_by_path):
    return sorted((traces[0] for traces in traces_by_path.values()),
                  key=lambda t: t.path)


def make_maps(traces):
    id2sig = {}
    sig2ids = defaultdict(list)
    def map_trace(trace):
        for inst in trace:
            sig = inst.sig
            id_ = inst.id
            if id_ not in sig:
                id2sig[id_] = sig
            sig2ids[sig].append(id_)
    map_trace(traces.extern)
    for trace in traces.frames:
        map_trace(trace)
    for trace in traces.pixels.values():
        map_trace(trace)
    sig2id = {sig: min(ids) for (sig, ids) in sig2ids.items()}
    return Maps(id2sig=id2sig, sig2id=sig2id)


def check_signatures(traces):
    """check that signatures are unique within a trace."""
    for (fno, frame) in enumerate(traces.frames):
        frm = Counter(i.sig for i in frame)
        assert frm.most_common(1)[0][1] == 1
        for pixels in traces.pixels.values():
            pxl = Counter(i.sig for i in pixels)
            assert pxl.most_common(1)[0][1] == 1


def check_isomorphism(traces_by_path):
    def index_ids(trace):
        id_index = {}
        for (i, inst) in enumerate(trace):
            id_index[inst.id] = i
        return id_index
    for (path, traces) in traces_by_path.items():
        trace0 = traces[0]
        idx0 = index_ids(trace0)
        for trace in traces:
            idx = index_ids(trace)
            assert len(trace) == len(trace0)
            for (i, i0) in zip(trace, trace0):
                assert i.op == i0.op
                assert i.sig == i0.sig
                assert len(i.operands) == len(i0.operands)
                for (opn, opn0) in zip(i.operands, i0.operands):
                    # print(f'opn = {opn} => {idx.get(opn, opn)}, '
                    #       f'opn0 = {opn0} => {idx0.get(opn0, opn0)}')
                    assert idx.get(opn, opn) == idx0.get(opn0, opn0)


def check_constants(inst_lists):
    for insts in inst_lists:
        i0 = insts[0]
        if i0.is_const:
            assert all(i.value == i0.value for i in insts)


def partition(traces):
    d = defaultdict(list)
    for t in traces:
        value = t[t.pc].value
        succ_sig = t[t.pc + 1].sig
        d[(value, succ_sig)].append(t)
    assert len(d) <= 2
    if len(d) == 1:             # no split.
        return traces, []
    a, b = d.items()
    ((a_value, a_sig), a_traces) = a
    ((b_value, b_sig), b_traces) = b
    if a_sig in {i.sig for t in b_traces for i in t}:
        return b_traces, a_traces
    else:
        return a_traces, b_traces


def merge_paths(exemplars):
    code = []
    Reactivation = namedtuple('Reactivation', 'label traces')
    reactivations = {}
    active_traces = [copy.copy(x) for x in exemplars]
    for t in active_traces:
        t.pc = 0
    while active_traces:
        a0 = active_traces[0]
        inst0 = a0[a0.pc]
        sig0 = inst0.sig
        if sig0 in reactivations:
            ra = reactivations[sig0]
            if not ra.label.placed:
                ra.label.place()
            code.append(ra.label)
            active_traces.extend(ra.traces)
            ra.traces.clear()
        assert all(a[a.pc].sig == sig0 for a in active_traces)
        if inst0.is_test:
            active_traces, b = partition(active_traces)
            for t in sorted(b, key=lambda t: t.path):
                t.pc += 1
                s = t[t.pc].sig
                if s not in reactivations:
                    reactivations[s] = Reactivation(Label(), [])
                reactivations[s].traces.append(t)
                label = reactivations[s].label
            a0 = active_traces[0]
            t0 = a0[a0.pc]
            op = {'false': 'bneg.s', 'true': 'bnneg.s'}[t0.value]
            branch = t0._replace(op=op, operands=tuple((label, *t0.operands)))
            code.append(branch)
            code.append('')
        else:
            code.append(inst0)
        for a in active_traces:
            a.pc += 1
            if a.pc >= len(a):
                active_traces.remove(a)
        if not active_traces:
            code.append('done')
            if reactivations:
                def ra_score(item):
                    (sig, ra) = item
                    if ra.traces:
                        return max(len(t) for t in ra.traces)
                    return 0
                sig0, ra = max(reactivations.items(), key=ra_score)
                active_traces.extend(ra.traces)
                ra.traces.clear()

    assert not active_traces
    assert not any(ra.traces for ra in reactivations.values())
    return code


def canon_ids(code, maps):
    def canon_id(id_):
        return maps.sig2id[maps.id2sig[id_]]
    def try_canon_id(id_):
        try:
            return canon_id(id_)
        except KeyError:
            return id_          # Some operands, e.g. labels, are not mapped.
    new_code = type(code)()
    for inst in code:
        if isinstance(inst, Inst):
            id_ = canon_id(inst.id)
            operands = tuple(try_canon_id(opn) for opn in inst.operands)
            inst = inst._replace(id=id_, operands=operands)
        new_code.append(inst)
    return new_code


def analyze():
    traces = read_log()
    frame_traces_by_path = group_traces_by_path(traces.frames)
    pixel_traces_by_path = group_traces_by_path(traces.pixels.values())
    frame_trace_insts = collect_insts(traces.frames)
    pixel_trace_insts = collect_insts(traces.pixels.values())
    frame_trace_exemplars = trace_exemplars(frame_traces_by_path)
    pixel_trace_exemplars = trace_exemplars(pixel_traces_by_path)
    maps = make_maps(traces)

    check_signatures(traces)
    check_isomorphism(frame_traces_by_path)
    check_isomorphism(pixel_traces_by_path)
    check_constants(frame_trace_insts)
    check_constants(pixel_trace_insts)

    frame_code = merge_paths(frame_trace_exemplars)
    pixel_code = merge_paths(pixel_trace_exemplars)

    frame_code = canon_ids(frame_code, maps)
    pixel_code = canon_ids(pixel_code, maps)

    print()
    print('Frame Code')
    print()
    for i in frame_code:
        print('       ', i)
    print()

    print()
    print('Pixel Code')
    print()
    for i in pixel_code:
        if isinstance(i, Label):
            print(f'{i}:')
        else:
            print('       ', i)
    print()


if __name__ == '__main__':
    analyze()
