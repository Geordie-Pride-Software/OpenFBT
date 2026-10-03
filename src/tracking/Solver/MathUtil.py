import math

import numpy as np


EPSILON = 1e-8


def normalize(v):
    length = np.linalg.norm(v)

    if length < EPSILON:
        return None

    return v / length


def basis_rotation(right, up):
    """
    Quaternion (x, y, z, w) for a body part whose local X axis points
    along `right` and whose local Y axis points roughly along `up`.

    Frame used everywhere in the solver: right-handed, X right, Y up,
    Z towards the back of the person (so forward is -Z, like OpenVR).
    Returns None if the two vectors are degenerate.
    """
    x = normalize(right)

    if x is None:
        return None

    z = normalize(np.cross(x, up))

    if z is None:
        return None

    y = np.cross(z, x)

    return matrix_to_quaternion(np.column_stack((x, y, z)))


def look_rotation(forward, up):
    """
    Quaternion for a body part facing `forward` with `up` as a hint.
    """
    f = normalize(forward)

    if f is None:
        return None

    x = normalize(np.cross(up, -f))

    if x is None:
        return None

    z = -f
    y = np.cross(z, x)

    return matrix_to_quaternion(np.column_stack((x, y, z)))


def remove_component(v, axis):
    """Remove the part of v that lies along axis (axis is normalized first)."""
    a = normalize(axis)

    if a is None:
        return v

    return v - a * np.dot(v, a)


def matrix_to_quaternion(m):
    trace = m[0][0] + m[1][1] + m[2][2]

    if trace > 0.0:
        s = math.sqrt(trace + 1.0) * 2.0
        w = 0.25 * s
        x = (m[2][1] - m[1][2]) / s
        y = (m[0][2] - m[2][0]) / s
        z = (m[1][0] - m[0][1]) / s
    elif m[0][0] > m[1][1] and m[0][0] > m[2][2]:
        s = math.sqrt(1.0 + m[0][0] - m[1][1] - m[2][2]) * 2.0
        w = (m[2][1] - m[1][2]) / s
        x = 0.25 * s
        y = (m[0][1] + m[1][0]) / s
        z = (m[0][2] + m[2][0]) / s
    elif m[1][1] > m[2][2]:
        s = math.sqrt(1.0 + m[1][1] - m[0][0] - m[2][2]) * 2.0
        w = (m[0][2] - m[2][0]) / s
        x = (m[0][1] + m[1][0]) / s
        y = 0.25 * s
        z = (m[1][2] + m[2][1]) / s
    else:
        s = math.sqrt(1.0 + m[2][2] - m[0][0] - m[1][1]) * 2.0
        w = (m[1][0] - m[0][1]) / s
        x = (m[0][2] + m[2][0]) / s
        y = (m[1][2] + m[2][1]) / s
        z = 0.25 * s

    q = np.array([x, y, z, w], dtype=float)

    return q / np.linalg.norm(q)


def quaternion_to_matrix(q):
    x, y, z, w = q

    return np.array([
        [1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
        [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
        [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)],
    ])


def quaternion_from_axis_angle(axis, degrees):
    a = normalize(np.asarray(axis, dtype=float))
    half = math.radians(degrees) / 2.0

    return np.array([
        a[0] * math.sin(half),
        a[1] * math.sin(half),
        a[2] * math.sin(half),
        math.cos(half),
    ])


def rotate_vector(q, v):
    return quaternion_to_matrix(q) @ np.asarray(v, dtype=float)


def to_unity_position(p):
    """Right-handed (Z back) to Unity / VRChat left-handed (Z forward)."""
    return np.array([p[0], p[1], -p[2]])


def to_unity_euler_degrees(q):
    """
    Convert a right-handed quaternion (x, y, z, w) from the solver frame
    into the Euler angles VRChat expects (Unity left-handed, ZXY order,
    same result as Unity's Quaternion.eulerAngles).
    """
    x, y, z, w = q

    # Right-handed to left-handed quaternion.
    ux, uy, uz, uw = x, y, -z, -w

    r = quaternion_to_matrix(np.array([ux, uy, uz, uw]))

    sin_x = -r[1][2]
    sin_x = max(-1.0, min(1.0, sin_x))
    pitch = math.asin(sin_x)

    if abs(sin_x) < 0.9999999:
        yaw = math.atan2(r[0][2], r[2][2])
        roll = math.atan2(r[1][0], r[1][1])
    else:
        yaw = math.atan2(-r[2][0], r[0][0])
        roll = 0.0

    return np.array([
        math.degrees(pitch) % 360.0,
        math.degrees(yaw) % 360.0,
        math.degrees(roll) % 360.0,
    ])
