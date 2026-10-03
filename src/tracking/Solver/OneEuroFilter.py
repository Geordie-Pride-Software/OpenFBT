import math

import numpy as np


class OneEuroFilter:
    """
    One Euro filter (Casiez et al.) for a vector of values.

    min_cutoff: lower means smoother when the value is still.
    beta: higher means less lag when the value moves quickly.
    """

    def __init__(self, min_cutoff=1.0, beta=0.05, d_cutoff=1.0):
        self.min_cutoff = min_cutoff
        self.beta = beta
        self.d_cutoff = d_cutoff

        self.x_prev = None
        self.dx_prev = None
        self.t_prev = None

    @staticmethod
    def _alpha(cutoff, dt):
        tau = 1.0 / (2.0 * math.pi * cutoff)
        return 1.0 / (1.0 + tau / dt)

    def reset(self):
        self.x_prev = None
        self.dx_prev = None
        self.t_prev = None

    def __call__(self, x, t):
        x = np.asarray(x, dtype=float)

        if self.x_prev is None:
            self.x_prev = x
            self.dx_prev = np.zeros_like(x)
            self.t_prev = t
            return x

        dt = t - self.t_prev

        if dt <= 0.0:
            return self.x_prev

        dx = (x - self.x_prev) / dt
        a_d = self._alpha(self.d_cutoff, dt)
        dx_hat = a_d * dx + (1.0 - a_d) * self.dx_prev

        cutoff = self.min_cutoff + self.beta * np.abs(dx_hat)
        a = self._alpha(cutoff, dt)
        x_hat = a * x + (1.0 - a) * self.x_prev

        self.x_prev = x_hat
        self.dx_prev = dx_hat
        self.t_prev = t

        return x_hat


class QuaternionFilter:
    """One Euro filter on quaternion components, keeping the sign continuous."""

    def __init__(self, min_cutoff=1.0, beta=0.05):
        self.filter = OneEuroFilter(min_cutoff, beta)
        self.last = None

    def reset(self):
        self.filter.reset()
        self.last = None

    def __call__(self, q, t):
        q = np.asarray(q, dtype=float)

        if self.last is not None and np.dot(q, self.last) < 0.0:
            q = -q

        out = self.filter(q, t)
        out = out / np.linalg.norm(out)

        self.last = out

        return out
