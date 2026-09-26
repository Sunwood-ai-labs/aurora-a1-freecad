# Renders stills for the making-of video (run inside FreeCAD GUI after build_aurora_a1.build()).
import json
import os
import FreeCAD as App
import FreeCADGui as Gui
from PIL import Image
from pivy import coin  # noqa: F401  (getCameraNode needs the SWIG wrapper loaded)

import build_aurora_a1 as A

OUT = "C:/Prj/FreeCAD_Demo_001/videos/aurora-a1-making/assets/renders"
R = App.Rotation
V = App.Vector
CAM_HERO = R(V(0, 0, 1), -125).multiply(R(V(1, 0, 0), 68))
CAM_WING = R(V(0, 0, 1), -140).multiply(R(V(1, 0, 0), 62))
HERO_ZOOM = 1.85  # FreeCAD viewport is portrait; fitAll leaves a landscape frame mostly empty


def _view():
    return Gui.getDocument(A.DOC_NAME).activeView()


def shot(name, rot=None, size=(1920, 1080), zoom=1.0, fit=True, ss=2, persp=True):
    """Supersampled transparent render -> downscaled PNG."""
    v = _view()
    ctype = "Perspective" if persp else "Orthographic"
    if v.getCameraType() != ctype:   # setCameraType rebuilds the camera even for the same type
        v.setCameraType(ctype)
    if rot is not None:
        v.setCameraOrientation(rot)
    if fit:
        v.fitAll()
    if zoom != 1.0:
        cam = v.getCameraNode()
        if persp:
            cam.heightAngle.setValue(cam.heightAngle.getValue() / zoom)
        else:
            cam.height.setValue(cam.height.getValue() / zoom)
    sub, base = os.path.split(name)
    tmp = os.path.join(OUT, sub, "_tmp_" + base)
    v.saveImage(tmp, size[0] * ss, size[1] * ss, "Transparent")
    im = Image.open(tmp).convert("RGBA").resize(size, Image.LANCZOS)
    im.save(os.path.join(OUT, name), optimize=True)
    os.remove(tmp)
    return im


def set_visible(doc, names_visible):
    for o in doc.Objects:
        if o.TypeId == "Part::Feature":
            o.Visibility = any(o.InList and _in_group(o, g) for g in names_visible)


def _in_group(o, gname):
    for p in o.InListRecursive:
        if p.Name == gname:
            return True
    return False


def run():
    os.makedirs(OUT, exist_ok=True)
    doc = App.getDocument(A.DOC_NAME)
    _view().setAnimationEnabled(False)
    A.explode(doc, 0.0)
    meta = {}

    # hero + exploded (same camera)
    shot("hero_front34.png", CAM_HERO, zoom=HERO_ZOOM)
    A.explode(doc, 1.0)
    shot("exploded_front34.png", CAM_HERO, zoom=HERO_ZOOM * 0.8)
    A.explode(doc, 0.0)

    # build-up by assembly group
    stages = [["Chassis"], ["Chassis", "PowerUnit", "Drivetrain"],
              ["Chassis", "PowerUnit", "Drivetrain", "Suspension"],
              ["Chassis", "PowerUnit", "Drivetrain", "Suspension", "Wheels"],
              ["Chassis", "PowerUnit", "Drivetrain", "Suspension", "Wheels", "Aerodynamics"],
              ["Chassis", "PowerUnit", "Drivetrain", "Suspension", "Wheels", "Aerodynamics", "Livery"]]
    v = _view()
    # frame on the complete car once, then keep that camera for every stage
    set_visible(doc, stages[-1])
    v.setCameraType("Perspective")
    v.setCameraOrientation(CAM_HERO)
    v.fitAll()
    cam = v.getCameraNode()
    cam.heightAngle.setValue(cam.heightAngle.getValue() / HERO_ZOOM)
    for i, groups in enumerate(stages, 1):
        set_visible(doc, groups)
        shot("stage_%d.png" % i, None, fit=False)
    set_visible(doc, stages[-1])

    # before/after: edge lines made the wings look black
    for o in doc.Objects:
        if o.TypeId == "Part::Feature":
            o.ViewObject.DisplayMode = "Flat Lines"
    # small scale on purpose: the issue only appeared when the whole car filled a small viewport
    shot("wing_before.png", CAM_WING, size=(1280, 900), zoom=0.9, ss=1)
    for o in doc.Objects:
        if o.TypeId == "Part::Feature":
            o.ViewObject.DisplayMode = "Shaded"
    shot("wing_after.png", CAM_WING, size=(1280, 900), zoom=0.9, ss=1)

    # orthographic side view with an analytic mm -> px mapping for dimension overlays
    W, H, VIS_H, CX, CZ = 1920, 1080, 3700.0, 1710.0, 520.0
    v.setCameraType("Orthographic")
    v.viewFront()
    v.fitAll()   # sets a depth/clip range that contains the car; only pan + zoom afterwards
    cam = v.getCameraNode()
    cam.height.setValue(VIS_H)
    cam.position.setValue(CX, cam.position.getValue()[1], CZ)
    shot("side_ortho.png", None, size=(W, H), fit=False, persp=False, ss=2)
    s = H / VIS_H
    meta["side_ortho"] = {"w": W, "h": H, "px_per_mm": s,
                          "x0_px": W / 2 - CX * s, "z0_px": H / 2 + CZ * s}
    with open(os.path.join(OUT, "render_meta.json"), "w") as f:
        json.dump(meta, f, indent=1)
    return meta


def run_turntable(start=0, stop=48, n=48, folder="turntable", size=(1600, 900)):
    v = _view()
    tdir = os.path.join(OUT, folder)
    os.makedirs(tdir, exist_ok=True)
    v.setCameraType("Perspective")
    v.setCameraOrientation(R(V(0, 0, 1), -125).multiply(R(V(1, 0, 0), 70)))
    v.fitAll()
    cam = v.getCameraNode()
    cam.heightAngle.setValue(cam.heightAngle.getValue() / 1.9)
    for i in range(start, stop):
        rot = R(V(0, 0, 1), -125 + 360.0 * i / n).multiply(R(V(1, 0, 0), 70))
        v.setCameraOrientation(rot)   # orientation only; distance stays fixed
        shot("%s/tt_%03d.png" % (folder, i), None, size=size, fit=False, ss=1)
