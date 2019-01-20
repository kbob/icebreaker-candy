from collections import namedtuple
from trickery import lazy_scalar, lazy_vec3, lazy_angle, define_constants


UGLY_BUT_THOROUGH = True


# Numeric constants are defined lazily.  When the caller passes in an
# implementation of Numerics, we can evaluate these in that numeric
# context.

lazy_scalar('EPSILON', 1.0e-3)
# lazy_scalar('ONE_HALF', 0.5)
lazy_scalar('ONE', 1)
lazy_scalar('TWO', 2)
# lazy_scalar('THREE', 3)
# lazy_scalar('FIVE', 5)
# lazy_scalar('EIGHT', 8)
# lazy_scalar('TEN', 10)
# lazy_scalar('TWENTY_FIVE', 25)

lazy_vec3('X', (1, 0, 0))
lazy_vec3('Y', (0, 1, 0))
lazy_vec3('Z', (0, 0, 1))
lazy_vec3('RED', (1, 0, 0))
lazy_vec3('GREEN', (0, 1, 0))
lazy_vec3('BLUE', (0, 0, 1))

lazy_vec3('BACKGROUND_COLOR', (0, 0, 0.9))

lazy_vec3('LIGHT_DIRECTION', (1, 2, -1))

lazy_vec3('PLANE_COLOR', (0, 0, 0.9))
lazy_vec3('PLANE_ORIGIN', (0, 0, 0))
lazy_vec3('PLANE_NORMAL', (0, 1, 0))

lazy_scalar('CHECKER_X_EXTENT', 18)
lazy_scalar('CHECKER_Z_EXTENT', 26)
lazy_vec3('CHECK0_COLOR', (0, 1, 0))
lazy_vec3('CHECK1_COLOR', (1, 0, 0))

lazy_angle('CAMERA_X_ANGLE', degrees=10)
lazy_angle('CAMERA_Y_ANGLE', units=45)

lazy_scalar('SHADOW_ATTEN', 0.5)

lazy_scalar('SPHERE_RADIUS', 3)
lazy_vec3('SPHERE_COLOR', (0.9, 0.9, 0))
lazy_scalar('SPHERE_ALPHA', 0.3)


def lerp(a, b, frac):
    return (ONE - frac) * a + frac * b


Ray = namedtuple('Ray', 'origin direction')
Camera = namedtuple('Camera', 'position x_angle, y_angle')
Light = namedtuple('Light', 'direction')


class Plane(namedtuple('Plane', 'origin normal')):

    def intersect(self, ray):
        denom = self.normal @ ray.direction
        if denom.abs() - EPSILON < 0:
            return None
        t = (self.origin - ray.origin) @ self.normal / denom
        if t < 0:
            return None
        intersection = ray.origin + t * ray.direction
        return namedtuple('Hit', 't intersection')(t, intersection)


class Sphere(namedtuple('Sphere', 'center radius')):

    def intersect(self, ray):
        L = self.center - ray.origin
        tca = ray.direction @ L
        if tca < 0:
            return None
        d2 = L @ L - tca * tca
        rad2 = self.radius * self.radius
        if rad2 - d2 < 0:
        # if d2 > rad2:
            return None
        thc = (rad2 - d2).sqrt()
        t = tca - thc
        intersection = ray.origin + ray.direction * t
        normal = (intersection - self.center).normalize()
        mirror = normal * (TWO * (ray.direction @ normal))
        reflect_ray = Ray(origin=intersection, direction=ray.direction - mirror)
        return (namedtuple
                ('Hit', 't intersection normal reflect_ray')
                (t, intersection, normal, reflect_ray))


class Scene:

    def __init__(self, width, height, numerics):
        self.width = width
        self.height = height
        self.numerics = numerics
        define_constants(globals(), numerics)
        self.plane = Plane(origin=PLANE_ORIGIN, normal=PLANE_NORMAL)
        self.light = Light(direction=LIGHT_DIRECTION.normalize())

    def render_scene(self):
        cam_pos = self.numerics.vec3(0, 10, -10)
        # cam_x_angle = self.numerics.angle(degrees=20)
        # cam_y_angle = self.numerics.angle(degrees=10)
        sphere_pos = self.numerics.vec3(3, 10, 10)
        self.camera = Camera(position=cam_pos,
                             x_angle=CAMERA_X_ANGLE,
                             y_angle=CAMERA_Y_ANGLE)
        self.sphere = Sphere(center=sphere_pos, radius=SPHERE_RADIUS)
        return self.collect_pixels()

    def render_anim(self, frame_count):
        self.cam_pos_u = 0
        self.cam_pos_v = 0
        self.sphere_pos_x = 0
        self.sphere_pos_z = 0
        if UGLY_BUT_THOROUGH:
            self.sphere_pos_z = -16
        self.sphere_inc_x = +7 / 2**5
        self.sphere_inc_z = +4 / 2**5

        for frame in range(frame_count):
            yield self.render_frame(frame)

    def precalc_camera(self):
        """Precalculate the camera parameters that don't require DSP.
           Return a record of DSP pipeline inputs.
        """
        v_inc = 3
        if UGLY_BUT_THOROUGH:
            v_inc = 513
        self.cam_pos_u = (self.cam_pos_u + 2) % 1024
        self.cam_pos_v = (self.cam_pos_v + v_inc) % 1024
        pos_u = self.numerics.angle(units=self.cam_pos_u)
        pos_v = self.numerics.angle(units=self.cam_pos_v)
        PreCam = namedtuple('PreCam', 'pos_u pos_v')
        return PreCam(pos_u, pos_v)

    def calc_camera(self, pre_cam):
        """Finish calculating camera using DSP operations."""
        S = self.numerics.scalar
        pos_sin = pre_cam.pos_u.sin()
        pos_cos = pre_cam.pos_v.cos()
        # print('sin {:.4} => {:.4}'.format(precalc.cam_pos_u, pos_sin))
        # print('cos {:.4} => {:.4}'.format(precalc.cam_pos_v, pos_cos))
        pos_x = pos_sin * S(8) - S(3)
        pos_y = pos_cos * S(8) + S(10)
        pos_z = pos_cos * S(5) - S(25)
        pos = self.numerics.vec3(pos_x, pos_y, pos_z)
        x_angle = self.numerics.angle(degrees=10)
        y_angle = self.numerics.angle(units=45)
        return Camera(position=pos, x_angle=x_angle, y_angle=y_angle)

    def precalc_sphere(self, frame):
        """Precalculate the sphere parameters that don't require DSP.
           Return a record of DSP pipeline inputs.
        """
        S = self.numerics.scalar

        # For Y calc, just need frame number.
        frame64 = S(frame % 64)
        frame64m = S(63 - frame % 64)

        # Can precalc X and Z coordinates.
        SPHERE_MIN_X = SPHERE_MIN_Z = -16
        SPHERE_MAX_X = SPHERE_MAX_Z = +16
        x = self.sphere_pos_x + self.sphere_inc_x
        self.sphere_pos_x = x
        if x > SPHERE_MAX_X:
            x = SPHERE_MAX_X
            self.sphere_inc_x = -self.sphere_inc_x
        elif x < SPHERE_MIN_X:
            x = SPHERE_MIN_X
            self.sphere_inc_x = -self.sphere_inc_x
        z = self.sphere_pos_z + self.sphere_inc_z
        self.sphere_pos_z = z
        if z > SPHERE_MAX_Z:
            z = SPHERE_MAX_Z
            self.sphere_inc_z = -self.sphere_inc_z
        elif z < SPHERE_MIN_Z:
            z = SPHERE_MIN_Z
            self.sphere_inc_z = -self.sphere_inc_z
        center_x = self.numerics.scalar(x)
        center_z = self.numerics.scalar(z)
        PreSphere = namedtuple('PreSphere',
                               'frame64 frame64m center_x center_z')
        return PreSphere(frame64, frame64m, center_x, center_z)

    def calc_sphere(self, pre_sphere):
        """Finish calculating sphere using DSP operations."""
        y_accel = self.numerics.scalar(7 / 1024)
        q = pre_sphere.frame64 * pre_sphere.frame64m
        center_x = pre_sphere.center_x
        center_y = q * y_accel + SPHERE_RADIUS
        center_z = pre_sphere.center_z
        pos = self.numerics.vec3(center_x, center_y, center_z)
        return Sphere(center=pos, radius=SPHERE_RADIUS)

    def render_frame(self, frame):
        pre_cam = self.precalc_camera()
        pre_sphere = self.precalc_sphere(frame)
        # print('pre_cam', pre_cam)
        # print('pre_sphere', pre_sphere)

        # Record the per-frame calculations.
        self.numerics.start_frame(pre_cam, pre_sphere)
        self.camera = self.calc_camera(pre_cam)
        self.sphere = self.calc_sphere(pre_sphere)
        # print('camera', self.camera)
        # print('sphere', self.sphere)
        self.numerics.end_frame(self.camera, self.sphere)

        pixels = self.collect_pixels()
        return pixels

    def collect_pixels(self):
        # return [[self.render_pixel(2, 47)]]
        return [
            [
                self.render_pixel(ix, iy)
                for ix in range(self.width)
            ]
            for iy in range(self.height)
        ]

    def render_pixel(self, ix, iy):
        x = self.numerics.scalar(ix)
        y = self.numerics.scalar(iy)
        pixel = namedtuple('Pixel', 'x y')(x, y)
        # print('render_pixel({}, {})'.format(ix, iy))
        self.numerics.start_pixel(pixel,
                                  self.camera,
                                  self.sphere)
        x_start = self.numerics.scalar(-1 / 2)
        y_start = self.numerics.scalar(+1 / 2)
        x_step = self.numerics.scalar(+1 / min(self.width, self.height))
        y_step = self.numerics.scalar(-1 / min(self.width, self.height))
        # FOV is implicitly 60 degrees.
        px = x_start + x * x_step
        py = y_start + y * y_step
        pz = self.numerics.scalar(1)
        primary = Ray(origin=self.camera.position,
                      direction=self.numerics.vec3(px, py, pz)
                          .rotate(self.camera.x_angle, 'X')
                          .rotate(self.camera.y_angle, 'Y')
                          .normalize())
        # print(ix, iy, primary)
        color = self.trace(primary).to_unorm()
        pixel_color = namedtuple('Pixel', 'color')(color)
        self.numerics.end_pixel(pixel_color)
        return color.as_tuple()

    def trace(self, ray, primary=True):
        if primary:
            hit = self.sphere.intersect(ray)
            if hit:
                C = self.trace(hit.reflect_ray, primary=False)
                C = lerp(SPHERE_COLOR, C, SPHERE_ALPHA)
                spot_light = hit.reflect_ray.direction @ self.light.direction
                if not spot_light < 0:
                    spot_light_e2 = spot_light * spot_light
                    spot_light_e4 = spot_light_e2 * spot_light_e2
                    spot_light_e8 = spot_light_e4 * spot_light_e4
                    C = C + SHADOW_ATTEN * spot_light_e8
                    # Clamp not needed.  to_unorm clamps later.
                    # C = C.clamp()
                return C
        hit = self.plane.intersect(ray)
        if not hit:
            return BACKGROUND_COLOR
        pisect = hit.intersection
        if (not pisect.z.abs() - CHECKER_Z_EXTENT < 0 or
            not pisect.x.abs() - CHECKER_X_EXTENT < 0):
            return PLANE_COLOR
        reverse_light_ray = Ray(pisect, self.light.direction)
        light_intersects = self.sphere.intersect(reverse_light_ray)
        checker = pisect.x.xor4(pisect.z)
        C = lerp(CHECK0_COLOR, CHECK1_COLOR, checker)
        if light_intersects:
            C = SHADOW_ATTEN * C
        return C




# Old version.  No numerics.

'''

import PIL.Image
from collections import namedtuple
from math import sqrt, sin, cos, pi, floor

class Vec3(tuple):

    def __str__(self):
        return 'V[{} {} {}]'.format(*self)

    __repr__ = __str__

    def __add__(self, other):
        if isinstance(other, tuple):
            return Vec3((self[0] + other[0],
                         self[1] + other[1],
                         self[2] + other[2]))
        else:
            return Vec3((self[0] + other,
                         self[1] + other,
                         self[2] + other))

    def __radd__(self, other):
        return Vec3((other + self[0],
                     other + self[1],
                     other + self[2]))

    def __sub__(self, other):
        if isinstance(other, Vec3):
            return Vec3((self[0] - other[0],
                         self[1] - other[1],
                         self[2] - other[2]))
        else:
            return Vec3((self[0] - other,
                         self[1] - other,
                         self[2] - other))

    def __mul__(self, other):
        assert not isinstance(other, tuple)
        return Vec3((self[0] * other, self[1] * other, self[2] * other))

    def __matmul__(self, other):
        """dot product"""
        assert isinstance(other, tuple)
        return self[0] * other[0] + self[1] * other[1] + self[2] * other[2]

    def __rmul__(self, other):
        return Vec3((other * self[0],
                     other * self[1],
                     other * self[2]))

    def normalize(self):
        return self * (1/sqrt(self @ self))

    def rotate(self, angle, axis):
        x, y, z = self
        s, c = sin(angle), cos(angle)
        if axis == X:
            return Vec3((x, c * y - s * z, s * y + c * z))
        elif axis == Y:
            return Vec3((c * x + s * z, y, c * z - s * x))
        else:
            assert False

    def clamp(self, max):
        return Vec3((min(self[0], max),
                     min(self[1], max),
                     min(self[2], max)))

def r2(v):  # for debugging
    return Vec3((round(c, 2) for c in v))


class Ray(namedtuple('Ray', 'origin direction')):
    pass

def dot(a, b):
    # return sum(i * j for (i, j) in zip(a, b))
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]

X = Vec3((1, 0, 0))
Y = Vec3((0, 1, 0))
Z = Vec3((0, 0, 1))
RED = Vec3((1, 0, 0))
GREEN = Vec3((0, 1, 0))
BLUE = Vec3((0, 0, 0.9))      # Why 0.9?
YELLOW = Vec3(0.9, 0.9, 0)
deg = pi / 180

# print('rotate x => {}'.format(Z.rotate(20*deg, X)))
# print('rotate y => {}'.format(Z.rotate(10*deg, Y)))
# exit()

camera = namedtuple('Camera', 'origin direction')(Vec3((0, 10, -10)),
                                                  Vec3((0, 0, 0)))

plane = namedtuple('Plane', 'origin normal')(Vec3((0, 0, 0)), Vec3((0, 1, 0)))

sphere = namedtuple('Sphere', 'center radius')(Vec3((3, 10, 10)), 3)

light = namedtuple('Light', 'direction')(Vec3((1, 2, -1)).normalize())

epsilon = 1.0e-3

# print(camera)
# print(plane)
# print(sphere)
# print(light)


def plane_intersect(plane, ray):
    denom = dot(plane.normal, ray.direction)
    if abs(denom) < epsilon:
        return None
    t = dot(plane.origin - ray.origin, plane.normal) / denom
    if t < 0:
        return None
    intersection = ray.origin + t * ray.direction
    return namedtuple('Hit', 't intersection')(t, intersection)

def sphere_intersect(sphere, ray):
    # print('sphere', sphere)
    # print('ray', ray)
    L = sphere.center - ray.origin
    tca = dot(ray.direction, L)
    if tca < 0:
        return None
    d2 = dot(L, L) - tca * tca
    rad2 = sphere.radius * sphere.radius
    if d2 > rad2:
        return None
    # d = sqrt(d2)
    # t = tca - d
    thc = sqrt(rad2 - d2)
    t = tca - thc
    intersection = ray.origin + ray.direction * t
    normal = (intersection - sphere.center).normalize()
    mirror = normal * (2 * dot(ray.direction, normal))
    reflect_ray = Ray(origin=intersection, direction=ray.direction - mirror)
    return (namedtuple
            ('Hit', 't intersection normal reflect_ray')
            (t, intersection, normal, reflect_ray))

def trace(ray, iteration=0):
    if iteration == 0:
        hit = sphere_intersect(sphere, ray)
        if hit:
            C = trace(hit.reflect_ray, 1)
            alpha = 0.3
            C = C * alpha + YELLOW * (1 - alpha)
            spot_light = dot(hit.reflect_ray.direction, light.direction)
            if spot_light > 0:
                spot_light_e2 = spot_light * spot_light
                spot_light_e4 = spot_light_e2 * spot_light_e2
                spot_light_e8 = spot_light_e4 * spot_light_e4
                C = C + 0.5 * spot_light_e8
                C = C.clamp(1)
            return C
    hit = plane_intersect(plane, ray)
    if not hit:
        return BLUE
    pisect = hit.intersection
    if abs(pisect[2]) >= 28 or abs(pisect[0]) >= 16:
        return BLUE
    reverse_light_ray = Ray(pisect, light.direction)
    light_intersects = sphere_intersect(sphere, reverse_light_ray)
    pisect_x = floor(pisect[0])
    pisect_z = floor(pisect[2])
    checker = (pisect_x ^ pisect_z) & 4

    C = RED if checker else GREEN
    if light_intersects:
        C = 0.5 * C
    return C


def Unorm(c):
    return tuple(round(i * 255) for i in c)


def render_scene():
    width, height = 64, 64
    x_step, y_step = 1 / width, -1 / width
    x_left, y_top = -width / 2 * x_step, -height / 2 * y_step

    img = PIL.Image.new(mode='RGB', size=(width, height), color=0)
    pix = img.load()

    y_dir = y_top
    for y in range(height):
        x_dir = x_left
        for x in range(width):
            if True or (x == 128 and y == 128):
                ray = Ray(origin=camera.origin,
                          direction=Vec3((x_dir, y_dir, 1))
                            .rotate(20*deg, X)
                            .rotate(10*deg, Y)
                            .normalize()
                            )
                color = trace(ray)
                pix[x, y] = Unorm(color)
            x_dir += x_step
        y_dir += y_step

    img.save('scene.png')


if __name__ == '__main__':
    render_scene()
'''
