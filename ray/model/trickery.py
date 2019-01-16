# I should not do tricky things in Python.  I know that.
# But I do them anyway.

import inspect
import os

# Hashed signatures make dot files smaller and run faster, but have
# less debugging information.
HASH_SIGNATURES = False

scalars = []
vectors = []
angles = []

# the_namespace = None

def lazy_scalar(name, value):
    scalars.append((name, value))

def lazy_vec3(name, value):
    vectors.append((name, value))

def lazy_angle(name, **kwargs):
    angles.append((name, kwargs))

# lazy_unorm and lazy_bool not needed yet?

def define_constants(namespace, numerics):
    # global the_namespace
    # the_namespace = namespace
    for (name, value) in scalars:
        s = numerics.scalar(value)
        s.name = name
        namespace[name] = s
    for (name, value) in vectors:
        v = numerics.vec3(*value)
        v.name = name
        namespace[name] = v
    for (name, kwargs) in angles:
        a = numerics.angle(**kwargs)
        a.name = name
        namespace[name] = a


def caller_signature(start=None, stop=None):

    """generate a unique signature for this point in program execution."""

    st = inspect.stack()
    fr = None
    try:
        sig = []
        for fr in st[start:stop]:
            file = os.path.basename(fr.filename)
            line = fr.lineno
            func = fr.function
            last = fr.frame.f_lasti
            if HASH_SIGNATURES:
                sig.append((file, line, func, last))
            else:
                # print(f'sig <= {file}:{line}:{func}:{last}')
                sig.append(f'{file}:{line}:{func}:{last}')
        sig = tuple(sig)
        if HASH_SIGNATURES:
            sig = hash(sig)
        return sig
    finally:
        del st
        del fr
