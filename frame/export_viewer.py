"""Export the frame as compact mesh data for the web viewer (frame/viewer/model.json)."""
import base64
import json
import math
from pathlib import Path

import numpy as np

import build_frame as bf
from params import *  # noqa: F403

OUT = Path(__file__).parent / "viewer"


def mesh(shape, tol=0.12):
    verts, faces = shape.val().tessellate(tol, 0.25)
    v = np.array([(p.x, p.y, p.z) for p in verts], dtype=np.float32)
    f = np.array(faces, dtype=np.uint32)
    return {"pos": base64.b64encode(v.tobytes()).decode(), "idx": base64.b64encode(f.tobytes()).decode(),
            "verts": len(v), "tris": len(f)}


def placement(dx, dy, dz, ang):
    """Column-major 4x4 for translate(dx,dy,dz) then rotate about Z by ang degrees (as in build_frame)."""
    c, s = math.cos(math.radians(ang)), math.sin(math.radians(ang))
    return [c, s, 0, 0, -s, c, 0, 0, 0, 0, 1, 0, c * dx - s * dy, s * dx + c * dy, dz, 1]


if __name__ == "__main__":
    geo = {"body": mesh(bf.body()), "arm": mesh(bf.arm()), "leg": mesh(bf.leg()), "mast": mesh(bf.mast())}
    inst = [{"id": "body", "geo": "body", "m": placement(0, 0, 0, 0)}]
    names = {45: "front-left", 135: "rear-left", 225: "rear-right", 315: "front-right"}
    for i, ang in enumerate(bf.ARM_ANGLES):
        inst.append({"id": f"arm_{i + 1}", "geo": "arm", "label": f"Arm {i + 1} ({names[ang]})", "angle": ang,
                     "m": placement(ARM_R0, 0, FLOOR + FIT, ang)})
        inst.append({"id": f"leg_{i + 1}", "geo": "leg", "label": f"Leg {i + 1} ({names[ang]})", "angle": ang,
                     "m": placement(LEG_R, 0, FLOOR + FIT, ang)})
    inst.append({"id": "mast", "geo": "mast", "label": "GPS mast", "m": placement(MAST_X, 0, BODY_H - 20, 0)})
    rep = json.loads((Path(__file__).parent / "out" / "report.json").read_text())
    clear = json.loads((Path(__file__).parent / "out" / "clearance.json").read_text())
    data = {"geometries": geo, "instances": inst, "report": rep, "clearance": clear,
            "motorR": MOTOR_R, "propD": PROP_D, "padTop": FLOOR + FIT + ARM_H_TIP}
    (OUT / "model.json").write_text(json.dumps(data))
    print({k: (g["verts"], g["tris"]) for k, g in geo.items()}, round((OUT / "model.json").stat().st_size / 1e6, 2), "MB")
