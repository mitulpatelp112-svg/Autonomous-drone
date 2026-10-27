"""Bought parts on each arm, modelled at their real sizes (see the source tags in params.py).

Everything is built in the arm's own frame (root at x = 0, arm underside at z = 0), so
build_frame.place_arm() puts it on any arm. Used by clearance.py, export_viewer.py and render.py.
"""
import math

import cadquery as cq

from params import *  # noqa: F403

ARM_LEN = MOTOR_R - ARM_R0
ESC_X = ESC_R - ARM_R0
h_at = lambda x: ARM_H_ROOT + (ARM_H_TIP - ARM_H_ROOT) * x / ARM_LEN
SEAT_Z = h_at(ESC_X + ESC_SEAT[0] / 2) - ESC_SEAT[1]          # ESC sits on this level seat
MOTOR_Z = ARM_H_TIP                                              # motor base on the pad top
PROP_Z = MOTOR_Z + MOTOR_BODY_H + ADAPTER_COLLAR[1]              # underside of the prop hub


def motor():
    """5010 motor: stationary base + rotating can as one body, shaft, collar and bullet adapter."""
    m = (cq.Workplane("XY").circle(MOTOR_BELL_D / 2).extrude(MOTOR_BODY_H)
         .edges(">Z").chamfer(1.5).translate((ARM_LEN, 0, MOTOR_Z)))
    top = MOTOR_Z + MOTOR_BODY_H
    m = m.union(cq.Workplane("XY").circle(ADAPTER_COLLAR[0] / 2).extrude(ADAPTER_COLLAR[1]).translate((ARM_LEN, 0, top)))
    bd, bh = ADAPTER_BULLET
    bullet = (cq.Workplane("XY").circle(bd / 2).workplane(offset=bh * 0.45).circle(bd / 2)
              .workplane(offset=bh * 0.55).circle(2.5).loft())
    m = m.union(bullet.translate((ARM_LEN, 0, top + ADAPTER_COLLAR[1])))
    # Shaft end + circlip under the base (sits in the pad's centre hole).
    m = m.union(cq.Workplane("XY").circle(MOTOR_SHAFT_D / 2 + 1.5).extrude(-2.5).translate((ARM_LEN, 0, MOTOR_Z)))
    return m


def motor_screw_points():
    """Where the 4 motor screws go: the listed 16 mm pair on one slot axis, the 19 mm pair on the other."""
    a, b = MOTOR_MOUNT[0] / 2, MOTOR_MOUNT[1] / 2
    return [(ARM_LEN + a, 0), (ARM_LEN - a, 0), (ARM_LEN, b), (ARM_LEN, -b)]


def motor_screws():
    """M3 socket-cap screws from under the pad: head in the pocket, thread up into the motor base."""
    s = None
    z0 = ARM_H_TIP - PAD_T
    for x, y in motor_screw_points():
        one = (cq.Workplane("XY").circle(HEAD_D / 2).extrude(-3.0).translate((x, y, z0))
               .union(cq.Workplane("XY").circle(1.5).extrude(MOTOR_SCREW_L).translate((x, y, z0))))
        s = one if s is None else s.union(one)
    return s


def esc():
    """30 A OPTO ESC on its seat: motor end (3 bullets) toward the motor, power + signal toward the body."""
    e = cq.Workplane("XY").box(ESC_L, ESC_W, ESC_T, centered=(True, True, False)).edges("|X").fillet(2.0)
    return e.translate((ESC_X, 0, SEAT_Z))


def esc_bullets():
    """3 x 3.5 mm female bullets on the motor end, joined to the motor leads."""
    b = None
    for y in (-7.0, 0.0, 7.0):
        one = (cq.Workplane("YZ").circle(3.0).extrude(BULLET[1])
               .translate((ESC_X + ESC_L / 2, y, SEAT_Z + ESC_T / 2)))
        b = one if b is None else b.union(one)
    return b


def motor_leads():
    """Motor phase wires from the bullets to where they leave the motor base (straight run on the arm top)."""
    x0 = ESC_X + ESC_L / 2 + BULLET[1]
    x1 = ARM_LEN - MOTOR_BELL_D / 2 + 2
    z = SEAT_Z + ESC_T / 2
    return cq.Workplane("XY").box(x1 - x0, 12, 3.2, centered=(False, True, True)).translate((x0, 0, z))


def esc_leads():
    """Red/black power leads + twisted signal pair down the top wire channel to the body (they go on to the bay)."""
    gw, gd = WIRE_GROOVE
    x0, x1 = -12.0, ESC_X - ESC_L / 2
    floor = lambda x: h_at(x) - gd
    leads = None
    for y, d in ((-3.2, 3.0), (0.0, 3.0), (3.6, 2.0)):           # red, black, signal pair
        p0 = cq.Vector(x0, y, floor(x0) + d / 2 + 0.2)
        p1 = cq.Vector(x1, y, floor(x1) + d / 2 + 0.2)
        L = (p1 - p0).Length
        w = cq.Workplane(cq.Plane(origin=p0.toTuple(), xDir=(0, 1, 0), normal=((p1 - p0) / L).toTuple())).circle(d / 2).extrude(L)
        leads = w if leads is None else leads.union(w)
    return leads


def zip_ties():
    """Two zip ties: through the arm slot, up the arm sides, over the ESC."""
    t = None
    for dx in (-ESC_L / 2 + 8, ESC_L / 2 - 8):
        x = ESC_X + dx
        z_slot = SEAT_Z - ZIP_SLOT[1] / 2 - 2.5
        top = SEAT_Z + ESC_T
        band = cq.Workplane("XY").box(3.6, ARM_W + 2.4, 1.2, centered=(True, True, False)).translate((x, 0, top))
        for sy in (-1, 1):
            band = band.union(cq.Workplane("XY").box(3.6, 1.2, top - z_slot + 1.2, centered=(True, True, False))
                              .translate((x, sy * (ARM_W / 2 + 0.6), z_slot - 0.6)))
        band = band.union(cq.Workplane("XY").box(3.6, ARM_W + 2.4, 1.2).translate((x, 0, z_slot)))
        t = band if t is None else t.union(band)
    return t


def prop_disc():
    return cq.Workplane("XY").circle(PROP_D / 2).extrude(PROP_HUB_T).translate((ARM_LEN, 0, PROP_Z))


PARTS = {   # name: (builder, viewer colour key)
    "motor": (motor, "motor"), "motor_screws": (motor_screws, "steel"), "esc": (esc, "esc"),
    "esc_bullets": (esc_bullets, "gold"), "motor_leads": (motor_leads, "wire"), "esc_leads": (esc_leads, "wire"),
    "zip_ties": (zip_ties, "tie"),
}
