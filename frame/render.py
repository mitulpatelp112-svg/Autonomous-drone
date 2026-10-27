"""Render preview images of the assembly and each part (matplotlib, no GUI)."""
import math
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


if __name__ == "__main__" and "--mount" not in sys.argv:
    parts = {"body": bf.body(), "arm": bf.arm(), "leg": bf.leg(), "mast": bf.mast()}
    body_c, arm_c, grey = (0.25, 0.27, 0.3), (0.1, 0.5, 0.56), (0.62, 0.64, 0.67)
    items = [(parts["body"], body_c)]
    for ang in bf.ARM_ANGLES:
        items.append((bf.place_arm(parts["arm"], ang), arm_c))
        items.append((bf.place_leg(parts["leg"], ang), grey))
    items.append((bf.place_mast(parts["mast"]), grey))

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


def mount_drawing(path):
    """Side elevation of one arm end with the motor and ESC at their real sizes, plus an exploded 3D view."""
    import hardware as hw
    from matplotlib.patches import Rectangle, Polygon as Poly
    L = hw.ARM_LEN
    fig = plt.figure(figsize=(15, 9), dpi=110)
    ax = fig.add_axes([0.03, 0.46, 0.94, 0.49])
    xs = np.linspace(95, L + bf.PAD_D / 2, 200)
    top = [min(hw.h_at(x), bf.ARM_H_TIP) if x > L - bf.MOTOR_BELL_D / 2 - 4 else hw.h_at(x) for x in xs]
    seat0, seat1 = hw.ESC_X - bf.ESC_SEAT[0] / 2, hw.ESC_X + bf.ESC_SEAT[0] / 2
    top = [hw.SEAT_Z if seat0 <= x <= seat1 else t for x, t in zip(xs, top)]
    arm_c, esc_c, mot_c, gold = (0.1, 0.5, 0.56), (0.15, 0.16, 0.18), (0.72, 0.75, 0.78), (0.78, 0.62, 0.17)
    ax.add_patch(Poly(list(zip(xs, top)) + [(xs[-1], 0), (xs[0], 0)], closed=True, fc=arm_c, alpha=0.85, ec="none"))
    ax.add_patch(Rectangle((L - bf.PAD_POCKET_D / 2, 0), bf.PAD_POCKET_D, bf.ARM_H_TIP - bf.PAD_T, fc="white", ec=arm_c, ls="--"))
    for x, y in hw.motor_screw_points():
        if abs(y) < 1:
            ax.add_patch(Rectangle((x - 1.5, bf.ARM_H_TIP - bf.PAD_T), 3, bf.MOTOR_SCREW_L, fc="0.25"))
            ax.add_patch(Rectangle((x - bf.HEAD_D / 2, bf.ARM_H_TIP - bf.PAD_T - 3), bf.HEAD_D, 3, fc="0.25"))
    # motor, collar, bullet, prop hub
    z0 = bf.ARM_H_TIP
    ax.add_patch(Rectangle((L - bf.MOTOR_BELL_D / 2, z0), bf.MOTOR_BELL_D, bf.MOTOR_BODY_H, fc=mot_c, ec="0.4"))
    zc = z0 + bf.MOTOR_BODY_H
    cd, ch = bf.ADAPTER_COLLAR; bd, bh = bf.ADAPTER_BULLET
    ax.add_patch(Rectangle((L - cd / 2, zc), cd, ch, fc="0.8", ec="0.4"))
    ax.add_patch(Poly([(L - bd / 2, zc + ch), (L + bd / 2, zc + ch), (L + bd / 2, zc + ch + bh * 0.45), (L + 2.5, zc + ch + bh), (L - 2.5, zc + ch + bh), (L - bd / 2, zc + ch + bh * 0.45)], fc="0.85", ec="0.4"))
    ax.add_patch(Rectangle((L - 18, hw.PROP_Z), 36, bf.PROP_HUB_T, fc="0.15", alpha=0.8))
    ax.plot([L - 160, L - 18], [hw.PROP_Z + bf.PROP_HUB_T / 2] * 2, color="0.15", lw=2.5, alpha=0.45)
    ax.text(L - 105, hw.PROP_Z + bf.PROP_HUB_T / 2 + 2.5, "prop blade (sweeps over the ESC: cooling air)", fontsize=8, color="0.35")
    ax.add_patch(Rectangle((hw.ESC_X - bf.ESC_L / 2, hw.SEAT_Z), bf.ESC_L, bf.ESC_T, fc=esc_c, ec="0.2"))
    ax.add_patch(Rectangle((hw.ESC_X + bf.ESC_L / 2, hw.SEAT_Z + bf.ESC_T / 2 - 3), bf.BULLET[1], 6, fc=gold))
    ax.plot([hw.ESC_X + bf.ESC_L / 2 + bf.BULLET[1], L - bf.MOTOR_BELL_D / 2 + 2], [hw.SEAT_Z + bf.ESC_T / 2] * 2, color=(0.7, 0.2, 0.15), lw=3)
    gfloor = lambda x: hw.h_at(x) - bf.WIRE_GROOVE[1] + 1.5
    ax.plot([95, hw.ESC_X - bf.ESC_L / 2], [gfloor(95), gfloor(hw.ESC_X - bf.ESC_L / 2)], color=(0.7, 0.2, 0.15), lw=3)
    for dx in (-bf.ESC_L / 2 + 8, bf.ESC_L / 2 - 8):
        x = hw.ESC_X + dx; zs = hw.SEAT_Z - bf.ZIP_SLOT[1] / 2 - 2.5
        ax.add_patch(Rectangle((x - 1.8, zs - 1.2), 3.6, hw.SEAT_Z + bf.ESC_T - zs + 2.4, fc="none", ec="0.55", lw=1.5))
    def note(xy, txt, xyt):
        ax.annotate(txt, xy=xy, xytext=xyt, fontsize=9, arrowprops=dict(arrowstyle="-", color="0.4", lw=0.8), va="center")
    note((L, zc + ch + bh), f"bullet prop adapter, tip ~{bf.MOTOR_BODY_H + ch + bh:.0f} above the pad [photo]", (L + 40, zc + ch + bh + 6))
    note((L + 16, hw.PROP_Z + 5), f"prop hub on the collar (16 x 5.5 prop)", (L + 40, hw.PROP_Z + 14))
    note((L + bf.MOTOR_BELL_D / 2, z0 + 9), f"5010-14 360KV: can ~Ø{bf.MOTOR_BELL_D:.0f} x {bf.MOTOR_BODY_H:.0f} [photo], stator 50 x 10, Ø4 shaft [listing]", (L + 40, z0 + 2))
    note((L + 8, bf.ARM_H_TIP - bf.PAD_T - 3), f"4 x M3 x {bf.MOTOR_SCREW_L:.0f} up through the {bf.PAD_T:.0f} mm pad (~3 mm into the motor)", (L + 40, -12))
    note((L - 12, 6), "open pocket: driver access + cooling air", (L - 60, -24))
    note((hw.ESC_X - 10, hw.SEAT_Z + bf.ESC_T), f"30 A OPTO ESC {bf.ESC_L:.0f} x {bf.ESC_W:.0f} x {bf.ESC_T} [retailer], on a flat {bf.ESC_SEAT[0]:.0f} mm seat", (hw.ESC_X - 70, 60))
    note((hw.ESC_X + bf.ESC_L / 2 - 8, hw.SEAT_Z + bf.ESC_T + 1), "2 zip ties through the arm (<= 3.6 mm)", (hw.ESC_X - 5, 74))
    note((hw.ESC_X + bf.ESC_L / 2 + 8, hw.SEAT_Z + bf.ESC_T / 2 - 3), "3 x 3.5 mm bullets -> motor leads", (hw.ESC_X + 5, -10))
    note((105, gfloor(105)), f"power + signal leads in the\n{bf.WIRE_GROOVE[0]:.0f} x {bf.WIRE_GROOVE[1]:.0f} channel -> body", (92, -14))
    ax.set_xlim(90, L + 175); ax.set_ylim(-30, 95); ax.set_aspect("equal"); ax.axis("off")
    ax.set_title("Arm end, side view (mm): motor and ESC at their real sizes", loc="left", fontsize=12)
    # exploded 3D view of the same parts
    ax3 = fig.add_axes([0.0, -0.05, 0.5, 0.46], projection="3d")
    arm = bf.arm().intersect(cq.Workplane('XY').box(200, 80, 80, centered=(False, True, True)).translate((110, 0, 0)))
    items = [(arm, arm_c), (hw.motor().translate((0, 0, 45)), mot_c), (hw.motor_screws().translate((0, 0, -25)), (0.25, 0.25, 0.25)),
             (hw.esc().translate((0, 0, 25)), esc_c), (hw.esc_bullets().translate((0, 0, 25)), gold), (hw.zip_ties().translate((0, 0, 40)), (0.8, 0.8, 0.8))]
    draw(ax3, items, 22, -60); ax3.set_title("Exploded: motor up, screws below, ESC and ties lifted", fontsize=10)
    ax4 = fig.add_axes([0.52, 0.0, 0.45, 0.4])
    # top view of the pad: slots, vents, listed holes
    th = np.linspace(0, 2 * np.pi, 200)
    ax4.plot(bf.PAD_D / 2 * np.cos(th), bf.PAD_D / 2 * np.sin(th), color=arm_c, lw=2)
    ax4.plot(bf.MOTOR_BELL_D / 2 * np.cos(th), bf.MOTOR_BELL_D / 2 * np.sin(th), color="0.6", ls="--", lw=1)
    ax4.plot(bf.PAD_POCKET_D / 2 * np.cos(th), bf.PAD_POCKET_D / 2 * np.sin(th), color=arm_c, ls=":", lw=1)
    r1, r2 = bf.MOTOR_SLOT_R
    for a in bf.MOTOR_SLOT_ANGLES:
        c, s = math.cos(math.radians(a)), math.sin(math.radians(a))
        ax4.plot([r1 * c, r2 * c], [r1 * s, r2 * s], color=arm_c, lw=7, alpha=0.5, solid_capstyle="round")
    vr, vd = bf.MOTOR_VENTS
    for a in (45, 135, 225, 315):
        cx, cy = vr * math.cos(math.radians(a)), vr * math.sin(math.radians(a))
        ax4.plot(cx + vd / 2 * np.cos(th), cy + vd / 2 * np.sin(th), color=arm_c)
    for x, y in hw.motor_screw_points():
        ax4.plot(x - L, y, "o", color="0.2", ms=7)
    ax4.plot(bf.MOTOR_CENTER_HOLE_D / 2 * np.cos(th), bf.MOTOR_CENTER_HOLE_D / 2 * np.sin(th), color=arm_c)
    ax4.annotate("", xy=(-36, 0), xytext=(-28, 0), arrowprops=dict(arrowstyle="->", color="0.3"))
    ax4.text(-36, 3, "to body", fontsize=8, color="0.3")
    ax4.text(-36, -40, f"pad Ø{bf.PAD_D:.0f}; dashed: motor can Ø{bf.MOTOR_BELL_D:.0f}; dotted: pocket below Ø{bf.PAD_POCKET_D:.0f}\n"
             f"slots r {r1:g}-{r2:g} (any 12-31 mm pattern); dots: listed 16 mm + 19 mm holes; 4 x Ø{vd:g} vents", fontsize=8)
    ax4.set_aspect("equal"); ax4.set_xlim(-38, 38); ax4.set_ylim(-42, 31); ax4.axis("off")
    ax4.set_title("Motor pad from above", fontsize=10)
    fig.savefig(path); plt.close(fig)


if __name__ == "__main__" and "--mount" in sys.argv:
    mount_drawing(OUT / "motor_mount.png")
