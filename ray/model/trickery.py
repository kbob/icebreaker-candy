# I should not do tricky things in Python.  I know that.
# But I do them anyway.


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

# def find_constant(obj):
#     print('find_constant(id={} obj={})'.format(id(obj), obj))
#     for (name, value) in scalars:
#         if the_namespace[name] == obj:
#             return (name, value, 'SCALAR')
#     for (name, value) in vectors:
#         print('vec namespace[{}] = (id={} obj={})'.format(name, id(the_namespace[name]), the_namespace[name]))
#         if the_namespace[name] == obj:
#             return (name, value, 'VECTOR')
#     for (name, value) in angles:
#         if the_namespace[name] == obj:
#             return (name, value, 'ANGLE')
