"""Render preview images of the assembly and each part (matplotlib, no GUI)."""
import sys
from pathlib import Path

import cadquery as cq
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

import build_frame as bf

OUT = Path(__file__).parent / "out"


def tris(shape, tol=0.4):
    verts, faces = shape.val().tessellate(tol, 0.3)
    v = np.array([(p.x, p.y, p.z) for p in verts])
    return v[np.array(faces)]


def draw(ax, items, elev, azim):
    allpts = []
    light = np.array([0.4, -0.5, 0.8]); light /= np.linalg.norm(light)
    for shape, rgb in items:
        t = tris(shape)
        n = np.cross(t[:, 1] - t[:, 0], t[:, 2] - t[:, 0])
        n /= np.linalg.norm(n, axis=1, keepdims=True) + 1e-9
        shade = 0.45 + 0.55 * np.clip(np.abs(n @ light), 0, 1)
        cols = np.clip(np.outer(shade, rgb), 0, 1)
        ax.add_collection3d(Poly3DCollection(t, facecolors=cols, edgecolors="none"))
        allpts.append(t.reshape(-1, 3))
    p = np.vstack(allpts)
    mid = (p.max(0) + p.min(0)) / 2
    r = (p.max(0) - p.min(0)).max() / 2
    ax.set_xlim(mid[0] - r, mid[0] + r); ax.set_ylim(mid[1] - r, mid[1] + r); ax.set_zlim(mid[2] - r, mid[2] + r)
    ax.set_box_aspect((1, 1, 1)); ax.view_init(elev=elev, azim=azim); ax.set_axis_off()


if __name__ == "__main__":
    parts = {"body": bf.body(), "arm": bf.arm(), "leg": bf.leg(), "mast": bf.mast()}
    body_c, arm_c, grey = (0.25, 0.27, 0.3), (0.1, 0.5, 0.56), (0.62, 0.64, 0.67)
    items = [(parts["body"], body_c)]
    for ang in bf.ARM_ANGLES:
        items.append((bf.place_arm(parts["arm"], ang), arm_c))
        items.append((bf.place_leg(parts["leg"], ang), grey))
    mx = -(bf.CORE / 2 - bf.WALL - bf.MAST_BOSS_D / 2)
    items.append((parts["mast"].translate((mx, 0, bf.BODY_H - 20)), grey))

    fig = plt.figure(figsize=(14, 7), dpi=110)
    for i, (el, az, title) in enumerate([(28, -55, "Assembly"), (90, -90, "Top view")]):
        ax = fig.add_subplot(1, 2, i + 1, projection="3d")
        draw(ax, items, el, az); ax.set_title(title)
    fig.tight_layout(); fig.savefig(OUT / "assembly.png"); plt.close(fig)

    fig = plt.figure(figsize=(14, 10), dpi=100)
    for i, (name, el, az) in enumerate([("body", 40, -60), ("arm", 30, -60), ("leg", 15, -80), ("mast", 25, -60)]):
        ax = fig.add_subplot(2, 2, i + 1, projection="3d")
        draw(ax, [(parts[name], body_c if name == "body" else arm_c if name == "arm" else grey)], el, az)
        ax.set_title(name)
    fig.tight_layout(); fig.savefig(OUT / "parts.png"); plt.close(fig)
    print("ok")
