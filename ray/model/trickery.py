# I should not to tricky things in Python.  I know that.
# But I do them anyway.

scalars = []
vectors = []
angles = []

def lazy_scalar(name, value):
    scalars.append((name, value))

def lazy_vec3(name, value):
    vectors.append((name, value))

def lazy_angle(name, value):
    angles.append((name, value))

def define_constants(namespace, numerics):
    for (name, value) in scalars:
        namespace[name] = numerics.scalar(value)
    for (name, value) in vectors:
        namespace[name] = numerics.vec3(*value)
    for (name, value) in angles:
        namespace[name] = numerics.angle(value)
