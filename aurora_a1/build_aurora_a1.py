# AURORA A1 F1 concept - assembly model builder for FreeCAD 1.x
# Axes: X = rearward (front axle at X=0), Y = lateral, Z = up (ground at Z=0). Units: mm.
import math
import FreeCAD as App
import Part
from FreeCAD import Vector as V

DOC_NAME = "AURORA_A1"
FONT = "C:/Windows/Fonts/arialbd.ttf"

# ---- main dimensions (from 三面図 / 主要諸元) ----
WHEELBASE = 3600.0
FRONT_TYRE = dict(D=660.0, W=305.0, track=1620.0)
REAR_TYRE = dict(D=670.0, W=405.0, track=1595.0)   # outer edge = +-1000 -> overall width 2000
RIM_R = 18 * 25.4 / 2                               # R18

# ---- colours ----
C_PURPLE = (0.42, 0.18, 0.78)
C_VIOLET = (0.55, 0.20, 0.72)
C_BLUE = (0.22, 0.30, 0.85)
C_TEAL = (0.10, 0.62, 0.78)
C_CARBON = (0.07, 0.07, 0.08)
C_TYRE = (0.04, 0.04, 0.04)
C_PINK = (1.00, 0.15, 0.65)
C_METAL = (0.55, 0.56, 0.60)
C_TITAN = (0.72, 0.52, 0.30)
C_BRAKE = (0.25, 0.22, 0.22)
C_WHITE = (0.95, 0.95, 0.97)
C_RED = (0.9, 0.05, 0.05)
C_VISOR = (0.15, 0.10, 0.30)


# =============================== helpers ===============================
def sec(x, yc, zb, zt, hw, n=2.8, N=40, flat_bottom=False):
    """Closed superellipse section in the YZ plane at station x."""
    zc, h = (zb + zt) / 2.0, (zt - zb) / 2.0
    pts = []
    for i in range(N):
        t = 2 * math.pi * i / N
        c, s = math.cos(t), math.sin(t)
        e = 2.0 / (n * (1.6 if (flat_bottom and s < 0) else 1.0))
        y = yc + hw * math.copysign(abs(c) ** (2.0 / n), c)
        z = zc + h * math.copysign(abs(s) ** e, s)
        pts.append(V(x, y, z))
    bs = Part.BSplineCurve()
    bs.interpolate(pts, PeriodicFlag=True)
    return Part.Wire(bs.toShape())


def loft(wires, ruled=False):
    return Part.makeLoft(wires, True, ruled)


def mirror_y(shape):
    return shape.mirror(V(0, 0, 0), V(0, 1, 0))


def rod(p1, p2, r):
    d = p2 - p1
    return Part.makeCylinder(r, d.Length, p1, d)


def fair_rod(p1, p2, chord, thick):
    """Aero-faired (elliptical) suspension member between two points."""
    d = p2 - p1
    L = d.Length
    e = Part.Ellipse(V(0, 0, 0), chord / 2.0, thick / 2.0)
    f = Part.Face(Part.Wire(e.toShape())).extrude(V(0, 0, L))
    # orient: local Z -> member axis, local X (chord) -> roughly car X
    rot = App.Rotation(V(0, 0, 1), d)
    f.Placement = App.Placement(p1, rot)
    return f


def box(x0, x1, y0, y1, z0, z1):
    return Part.makeBox(x1 - x0, y1 - y0, z1 - z0, V(x0, y0, z0))


def plate_xz(pts_xz, y, t):
    """Flat plate with outline in XZ plane at y, thickness t along +Y."""
    w = Part.makePolygon([V(px, y, pz) for px, pz in pts_xz] + [V(pts_xz[0][0], y, pts_xz[0][1])])
    return Part.Face(w).extrude(V(0, t, 0))


def plate_xy(pts_xy, z, t):
    w = Part.makePolygon([V(px, py, z) for px, py in pts_xy] + [V(pts_xy[0][0], pts_xy[0][1], z)])
    return Part.Face(w).extrude(V(0, 0, t))


def airfoil(chord, t=0.12, m=0.06, p=0.4, N=28):
    """Inverted NACA-4 section, LE at (0,0), chord along +X, returns [(x,z)]."""
    up, lo = [], []
    for i in range(N + 1):
        xc = (1 - math.cos(math.pi * i / N)) / 2
        yt = 5 * t * (0.2969 * math.sqrt(xc) - 0.1260 * xc - 0.3516 * xc ** 2
                      + 0.2843 * xc ** 3 - 0.1036 * xc ** 4)
        if xc < p:
            yc, dy = m / p ** 2 * (2 * p * xc - xc ** 2), 2 * m / p ** 2 * (p - xc)
        else:
            yc = m / (1 - p) ** 2 * ((1 - 2 * p) + 2 * p * xc - xc ** 2)
            dy = 2 * m / (1 - p) ** 2 * (p - xc)
        th = math.atan(dy)
        up.append((xc - yt * math.sin(th), yc + yt * math.cos(th)))
        lo.append((xc + yt * math.sin(th), yc - yt * math.cos(th)))
    pts = list(reversed(up)) + lo[1:-1]
    return [(px * chord, -pz * chord) for px, pz in pts]   # inverted -> downforce


def af_wire(y, x0, z0, chord, aoa, t=0.12, m=0.06):
    a = math.radians(aoa)   # positive = trailing edge up
    vs = []
    for px, pz in airfoil(chord, t, m):
        vs.append(V(x0 + px * math.cos(a) - pz * math.sin(a), y,
                    z0 + px * math.sin(a) + pz * math.cos(a)))
    # one smooth B-spline per section: a polygon loft makes ~56 faces whose edges flood drawings
    bs = Part.BSplineCurve()
    bs.interpolate(vs, PeriodicFlag=True)
    return Part.Wire(bs.toShape())


def wing(stations, t=0.12, m=0.06):
    """stations: [(y, x0, z0, chord, aoa)] lofted spanwise."""
    return loft([af_wire(y, x0, z0, c, a, t, m) for y, x0, z0, c, a in stations])


def text_solid(txt, size, depth):
    """Extruded text lying in XY plane, reading along +X, normal +Z."""
    chars = Part.makeWireString(txt, FONT, size, 0)
    solids = []
    for ch in chars:
        wires = [Part.Wire(e) for e in ch]
        if not wires:
            continue
        face = Part.Face(wires, "Part::FaceMakerBullseye")
        solids.append(face.extrude(V(0, 0, depth)))
    comp = Part.makeCompound(solids)
    bb = comp.BoundBox
    comp.translate(V(-bb.Center.x, -bb.Center.y, 0))
    return comp


def decal(txt, size, host, place, rot, offset=6.0, shift=None):
    """Text projected onto a host body (conforms to curved surfaces)."""
    ts = text_solid(txt, size, 600)
    ts.translate(V(0, 0, -300))
    ts.Placement = App.Placement(place, rot).multiply(ts.Placement)
    try:
        skin = host.makeOffsetShape(offset, 0.05)
    except Exception:   # offset of high-order loft can fail -> nudged copy
        if shift is None:
            return None
        skin = host.copy()
        skin.translate(shift)
    return ts.common(skin)


# =============================== subsystems ===============================
def build_chassis():
    out = {}
    # --- nose cone ---
    nose = loft([
        sec(-1050, 0, 150, 235, 50, n=2.4),
        sec(-800, 0, 158, 285, 85, n=2.5),
        sec(-450, 0, 180, 390, 130, n=2.6),
        sec(-150, 0, 225, 500, 180, n=2.8),
        sec(0, 0, 250, 545, 205, n=3.0),
    ])
    out["NoseCone"] = (nose, C_BLUE)

    # --- monocoque / survival cell ---
    tub = loft([
        sec(0, 0, 250, 545, 205, n=3.0),
        sec(450, 0, 150, 610, 270, n=3.2, flat_bottom=True),
        sec(900, 0, 80, 640, 330, n=3.4, flat_bottom=True),
        sec(1500, 0, 70, 640, 340, n=3.6, flat_bottom=True),
        sec(1900, 0, 75, 620, 320, n=3.4, flat_bottom=True),
        sec(2050, 0, 90, 580, 280, n=3.0, flat_bottom=True),
    ])
    cockpit_cut = loft([
        sec(820, 0, 300, 1000, 150, n=3.0),
        sec(1000, 0, 300, 1000, 225, n=3.0),
        sec(1400, 0, 300, 1000, 235, n=3.0),
        sec(1560, 0, 300, 1000, 180, n=3.0),
    ])
    tub = tub.cut(cockpit_cut)
    out["Monocoque"] = (tub, C_PURPLE)

    # --- cockpit interior / seat ---
    seat = box(1050, 1520, -200, 200, 140, 300)
    out["Seat"] = (seat, C_CARBON)
    wheel = Part.makeCylinder(130, 30, V(1000, 0, 520), V(1, 0, -0.3))
    wheel = wheel.common(box(900, 1100, -150, 150, 440, 620))
    out["SteeringWheel"] = (wheel, C_CARBON)

    # --- driver helmet ---
    helmet = Part.makeSphere(125, V(1420, 0, 690))
    helmet = helmet.fuse(Part.makeCylinder(105, 120, V(1420, 0, 560), V(0, 0, 1)))
    visor = Part.makeSphere(129, V(1420, 0, 690)).common(box(1280, 1360, -95, 95, 665, 725))
    out["DriverHelmet"] = (helmet, C_VIOLET)
    out["HelmetVisor"] = (visor, C_VISOR)

    # --- halo ---
    pts = [V(1500, -245, 640), V(1380, -262, 720), V(1200, -255, 790), V(1000, -215, 825),
           V(880, -130, 838), V(835, 0, 842), V(880, 130, 838), V(1000, 215, 825),
           V(1200, 255, 790), V(1380, 262, 720), V(1500, 245, 640)]
    bs = Part.BSplineCurve()
    bs.interpolate(pts)
    halo = None
    try:
        path = Part.Wire(bs.toShape())
        t0 = bs.tangent(bs.FirstParameter)[0]
        prof = Part.Wire(Part.Circle(pts[0], t0, 24).toShape())
        halo = path.makePipeShell([prof], True, True)
        if not halo.isValid() or halo.Volume <= 0:
            halo = None
    except Exception:
        halo = None
    if halo is None:   # fallback: chained rods
        samples = [bs.value(bs.FirstParameter + (bs.LastParameter - bs.FirstParameter) * i / 40)
                   for i in range(41)]
        halo = rod(samples[0], samples[1], 24)
        for a, b in zip(samples[1:], samples[2:]):
            halo = halo.fuse([rod(a, b, 24), Part.makeSphere(24, a)])
    pillar = rod(V(640, 0, 610), V(845, 0, 842), 30)
    halo = halo.fuse(pillar).removeSplitter()
    out["Halo"] = (halo, C_CARBON)

    # --- mirrors ---
    for side, sgn in (("R", 1), ("L", -1)):
        stalk = rod(V(880, sgn * 300, 600), V(900, sgn * 440, 680), 12)
        stalk = stalk.fuse(rod(V(930, sgn * 320, 590), V(910, sgn * 440, 670), 10))
        housing = loft([
            sec(870, sgn * 450, 655, 720, 85, n=3),
            sec(930, sgn * 450, 645, 725, 95, n=3),
        ])
        glass = box(866, 868, sgn * 450 - 80, sgn * 450 + 80, 660, 715)
        out["Mirror_" + side] = (stalk.fuse(housing), C_PURPLE)
        out["MirrorGlass_" + side] = (glass, C_METAL)
    return out


def build_aero():
    out = {}
    # --- front wing: 4 elements, spoon-shaped (dips at centre, rises outboard) ---
    ys = [-985, -800, -600, -400, -200, 0, 200, 400, 600, 800, 985]
    def fw(i, x0, z0, c0, c1, a0, a1, rise):
        st = []
        for y in ys:
            k = abs(y) / 985.0
            st.append((y, x0 + 25 * k, z0 + rise * k ** 1.6, c0 + (c1 - c0) * k, a0 + (a1 - a0) * k))
        return wing(st, t=0.11, m=0.05)
    main = fw(0, -1100, 75, 240, 250, 3, 6, 30)
    f1 = fw(1, -905, 110, 110, 160, 16, 22, 50)
    f2 = fw(2, -800, 150, 90, 130, 26, 32, 80)
    f3 = fw(3, -710, 195, 70, 105, 36, 44, 105)
    out["FrontWing_MainPlane"] = (main, C_TEAL)
    out["FrontWing_Flap1"] = (f1, C_BLUE)
    out["FrontWing_Flap2"] = (f2, C_PURPLE)
    out["FrontWing_Flap3"] = (f3, C_VIOLET)
    ep = [(-1100, 15), (-640, 15), (-575, 110), (-585, 330), (-700, 340), (-1000, 250), (-1100, 150)]
    for side, y in (("R", 990), ("L", -1000)):
        plate = plate_xz(ep, y, 10)
        foot = box(-1120, -660, y - 60, y, 15, 25) if y > 0 else box(-1120, -660, y + 10, y + 70, 15, 25)
        out["FrontWing_Endplate_" + side] = (plate.fuse(foot), C_PURPLE)
    # nose-to-wing pillars
    pil = plate_xz([(-1000, 90), (-870, 90), (-900, 180), (-1010, 170)], -45, 8)
    pil = pil.fuse(plate_xz([(-1000, 90), (-870, 90), (-900, 180), (-1010, 170)], 37, 8))
    out["FrontWing_Pylons"] = (pil, C_CARBON)

    # --- sidepods (coke-bottle, undercut) ---
    def pod(sgn):
        s = loft([
            sec(950, sgn * 540, 250, 540, 170, n=4.2),
            sec(1200, sgn * 560, 190, 560, 205, n=4.2),
            sec(1700, sgn * 540, 150, 530, 210, n=3.8),
            sec(2300, sgn * 440, 120, 430, 180, n=3.3),
            sec(2850, sgn * 320, 110, 330, 120, n=2.8),
            sec(3250, sgn * 220, 120, 270, 60, n=2.4),
        ])
        inlet = loft([
            sec(900, sgn * 560, 310, 510, 125, n=4.0),
            sec(1150, sgn * 565, 310, 500, 105, n=3.6),
        ])
        return s.cut(inlet)
    pod_r, pod_l = pod(1), pod(-1)
    out["Sidepod_R"] = (pod_r, C_BLUE)
    out["Sidepod_L"] = (pod_l, C_BLUE)

    # --- engine cover / airbox / roll hoop / fin ---
    cover = loft([
        sec(1540, 0, 560, 890, 140, n=2.6),
        sec(1750, 0, 330, 935, 200, n=2.8),
        sec(2150, 0, 170, 850, 230, n=3.0),
        sec(2700, 0, 140, 660, 200, n=3.0),
        sec(3300, 0, 200, 480, 120, n=2.8),
        sec(3700, 0, 300, 420, 60, n=2.4),
    ])
    intake = loft([sec(1500, 0, 800, 910, 85, n=2.2), sec(1700, 0, 810, 900, 70, n=2.2)])
    cover = cover.cut(intake)
    hoop = loft([sec(1580, 0, 860, 950, 55, n=2.4), sec(1800, 0, 860, 950, 40, n=2.4)])
    cover = cover.fuse(hoop)
    fin = plate_xz([(1850, 900), (3500, 470), (3500, 420), (1850, 700)], -4, 8)
    cover = cover.fuse(fin).removeSplitter()
    out["EngineCover"] = (cover, C_VIOLET)
    out["TCam"] = (box(1640, 1700, -35, 35, 945, 965), C_CARBON)

    # --- floor + edge wings ---
    fl = [(430, 0), (430, 320), (620, 700), (880, 800), (3080, 800), (3230, 690), (3250, 540),
          (3250, 0)]
    full = fl[:-1] + [(x, -y) for x, y in reversed(fl[1:-1])]
    floor = plate_xy(full, 30, 18)
    for sgn in (1, -1):
        edge = plate_xz([(900, 48), (3060, 48), (3060, 110), (1000, 90)], sgn * 790 - (0 if sgn > 0 else 8), 8)
        fence = plate_xz([(450, 30), (900, 30), (900, 150), (520, 220)], sgn * 260 - 4, 8)
        floor = floor.fuse([edge, fence])
    out["Floor"] = (floor.removeSplitter(), C_CARBON)

    # --- diffuser ---
    ramp = plate_xz([(3250, 30), (4180, 340), (4180, 362), (3250, 52)], -520, 1040)
    dif = ramp
    for y in (-525, -350, -175, 167, 342, 517):
        dif = dif.fuse(plate_xz([(3250, 30), (4180, 345), (4180, 130)], y, 8))
    out["Diffuser"] = (dif.removeSplitter(), C_CARBON)

    # --- rear wing ---
    ys = [-515, -300, -100, 0, 100, 300, 515]
    main = wing([(y, 4150, 775 - 20 * (1 - abs(y) / 515.0), 280, 8) for y in ys], t=0.13, m=0.07)
    flap = wing([(y, 4335, 835 - 10 * (1 - abs(y) / 515.0), 185, 32) for y in ys], t=0.10, m=0.06)
    out["RearWing_MainPlane"] = (main, C_PURPLE)
    out["RearWing_DRSFlap"] = (flap, C_TEAL)
    rep = [(4130, 600), (4470, 600), (4520, 950), (4160, 955), (4120, 880)]
    for side, y in (("R", 515), ("L", -525)):
        out["RearWing_Endplate_" + side] = (plate_xz(rep, y, 10), C_VIOLET)
    pyl = plate_xz([(3980, 380), (4120, 380), (4330, 795), (4230, 800)], -50, 8)
    pyl = pyl.fuse(plate_xz([(3980, 380), (4120, 380), (4330, 795), (4230, 800)], 42, 8))
    act = rod(V(4260, 0, 760), V(4380, 0, 860), 14)
    out["RearWing_Pylons"] = (pyl.fuse(act), C_CARBON)
    # beam wing
    bw = wing([(y, 4180, 400, 170, 12) for y in (-500, 0, 500)], t=0.12, m=0.05)
    out["RearWing_BeamWing"] = (bw, C_CARBON)
    return out, pod_r, pod_l, cover


def build_power_unit():
    out = {}
    crank = box(2080, 2640, -150, 150, 110, 310)
    out["ICE_Crankcase"] = (crank, C_METAL)
    banks = None
    covers = None
    for ang in (45, -45):
        b = box(2100, 2620, -80, 80, 290, 500)
        c = Part.makeCylinder(45, 520, V(2100, 0, 500), V(1, 0, 0))
        rot_c = V(0, 0, 290)
        b.rotate(rot_c, V(1, 0, 0), ang)
        c.rotate(rot_c, V(1, 0, 0), ang)
        banks = b if banks is None else banks.fuse(b)
        covers = c if covers is None else covers.fuse(c)
    out["ICE_CylinderBanks_V6"] = (banks, C_METAL)
    out["ICE_CamCovers"] = (covers, C_RED)
    out["Turbo_Compressor"] = (Part.makeCylinder(110, 110, V(1960, 0, 420), V(1, 0, 0)), C_METAL)
    out["Turbo_Turbine"] = (Part.makeCylinder(105, 110, V(2650, 0, 420), V(1, 0, 0)), C_TITAN)
    out["MGU_H"] = (Part.makeCylinder(55, 580, V(2070, 0, 420), V(1, 0, 0)), C_TEAL)
    mguk = Part.makeCylinder(60, 110, V(2200, -150, 210), V(0, -1, 0))
    out["MGU_K"] = (mguk, C_TEAL)
    out["EnergyStore"] = (box(1520, 1950, -210, 210, 90, 230), C_TEAL)
    ce = box(1250, 1650, 420, 560, 220, 380)
    out["ControlElectronics"] = (ce, C_CARBON)
    # radiators inside sidepods (inclined)
    rads = None
    for sgn in (1, -1):
        r = box(1200, 1260, -150, 150, 200, 500)
        r.rotate(V(1230, 0, 350), V(0, 0, 1), -25 * sgn)
        r.translate(V(0, sgn * 590, 0))
        rads = r if rads is None else rads.fuse(r)
    out["Radiators"] = (rads, C_METAL)
    # exhaust: 3 primaries per bank into turbine, tailpipe out the rear
    ex = None
    for sgn in (1, -1):
        for x in (2170, 2350, 2530):
            p1 = V(x, sgn * 185, 445)
            pipe = rod(p1, V(2670, sgn * 45, 420), 22).fuse(Part.makeSphere(22, p1))
            ex = pipe if ex is None else ex.fuse(pipe)
    tail = loft([sec(2760, 0, 380, 460, 40, n=2), sec(3500, 0, 360, 440, 42, n=2),
                 sec(3760, 0, 375, 455, 48, n=2)])
    out["Exhaust"] = (ex.fuse(tail).fuse(rod(V(2700, 0, 420), V(2770, 0, 420), 40)), C_TITAN)
    return out


def build_drivetrain():
    out = {}
    gb = loft([
        sec(2640, 0, 150, 430, 170, n=3.4),
        sec(3200, 0, 190, 430, 140, n=3.2),
        sec(3700, 0, 260, 430, 105, n=3.0),
    ])
    out["Gearbox_8speed"] = (gb, C_CARBON)
    crash = loft([sec(3700, 0, 280, 430, 90, n=3), sec(4200, 0, 330, 420, 55, n=2.6)])
    out["RearCrashStructure"] = (crash, C_CARBON)
    out["RainLight"] = (box(4200, 4215, -40, 40, 340, 400), C_RED)
    for sgn in (1, -1):
        ds = rod(V(WHEELBASE, sgn * 120, REAR_TYRE["D"] / 2), V(WHEELBASE, sgn * 640, REAR_TYRE["D"] / 2), 26)
        out["Driveshaft_" + ("R" if sgn > 0 else "L")] = (ds, C_METAL)
    return out


def build_suspension():
    out = {}
    fz = FRONT_TYRE["D"] / 2
    rz = REAR_TYRE["D"] / 2
    for side, s in (("R", 1), ("L", -1)):
        # front: double wishbone + pushrod + track rod
        up = V(0, s * 700, fz + 180)
        lo = V(0, s * 715, fz - 175)
        f = fair_rod(V(-230, s * 150, 500), up, 40, 14)
        f = f.fuse(fair_rod(V(240, s * 170, 520), up, 40, 14))
        f = f.fuse(fair_rod(V(-280, s * 120, 270), lo, 40, 14))
        f = f.fuse(fair_rod(V(290, s * 190, 240), lo, 40, 14))
        f = f.fuse(fair_rod(V(20, s * 690, fz - 150), V(80, s * 200, 560), 30, 12))
        f = f.fuse(fair_rod(V(90, s * 190, 380), V(95, s * 700, fz - 20), 30, 12))
        upright = box(-40, 40, s * 680 - 20, s * 680 + 20, fz - 190, fz + 200)
        out["FrontSuspension_" + side] = (f, C_CARBON)
        out["FrontUpright_" + side] = (upright, C_METAL)
        # rear: double wishbone + pullrod + toe link
        up = V(WHEELBASE, s * 650, rz + 190)
        lo = V(WHEELBASE, s * 660, rz - 190)
        r = fair_rod(V(3330, s * 150, 440), up, 40, 14)
        r = r.fuse(fair_rod(V(3820, s * 110, 430), up, 40, 14))
        r = r.fuse(fair_rod(V(3250, s * 160, 190), lo, 40, 14))
        r = r.fuse(fair_rod(V(3760, s * 100, 270), lo, 40, 14))
        r = r.fuse(fair_rod(up, V(3420, s * 130, 230), 30, 12))
        r = r.fuse(fair_rod(V(3820, s * 100, 330), V(3720, s * 650, rz), 30, 12))
        upr = box(WHEELBASE - 50, WHEELBASE + 50, s * 640 - 22, s * 640 + 22, rz - 200, rz + 210)
        out["RearSuspension_" + side] = (r, C_CARBON)
        out["RearUpright_" + side] = (upr, C_METAL)
    return out


def build_wheel(D, W, disc_r):
    """Wheel with outer face towards +Y, centred at origin, axis = Y."""
    R = D / 2
    parts = {}
    tyre = Part.makeCylinder(R, W, V(0, -W / 2, 0), V(0, 1, 0))
    edges = [e for e in tyre.Edges if isinstance(e.Curve, Part.Circle) and abs(e.Curve.Radius - R) < 1]
    tyre = tyre.makeFillet(min(55, W * 0.18), edges)
    tyre = tyre.cut(Part.makeCylinder(RIM_R, W + 20, V(0, -W / 2 - 10, 0), V(0, 1, 0)))
    parts["Tyre"] = (tyre, C_TYRE)
    stripe = None
    for yy in (W / 2 - 1.0, -W / 2 - 1.0):
        ring = Part.makeCylinder(RIM_R + 50, 2.2, V(0, yy, 0), V(0, 1, 0)).cut(
            Part.makeCylinder(RIM_R + 30, 3, V(0, yy - 0.4, 0), V(0, 1, 0)))
        stripe = ring if stripe is None else stripe.fuse(ring)
    parts["TyreStripe"] = (stripe, C_PINK)
    rim = Part.makeCylinder(RIM_R, W - 30, V(0, -W / 2 + 15, 0), V(0, 1, 0))
    rim = rim.cut(Part.makeCylinder(RIM_R - 14, W, V(0, -W / 2 - 5, 0), V(0, 1, 0)))
    cover = Part.makeCylinder(RIM_R - 6, 6, V(0, W / 2 - 30, 0), V(0, 1, 0))
    hub = Part.makeCylinder(42, 30, V(0, W / 2 - 30, 0), V(0, 1, 0))
    parts["Rim"] = (rim.fuse(cover), C_CARBON)
    parts["WheelNut"] = (hub, C_PINK)
    disc = Part.makeCylinder(disc_r, 32, V(0, -W / 2 + 25, 0), V(0, 1, 0)).cut(
        Part.makeCylinder(disc_r - 55, 40, V(0, -W / 2 + 20, 0), V(0, 1, 0)))
    parts["BrakeDisc"] = (disc, C_BRAKE)
    cal = box(-60, 60, -W / 2 + 10, -W / 2 + 72, disc_r - 40, disc_r + 30)
    cal.rotate(V(0, 0, 0), V(0, 1, 0), -40)
    parts["BrakeCaliper"] = (cal, C_PINK)
    return parts


def build_wheels():
    out = {}
    for axle, x, T, disc_r in (("Front", 0.0, FRONT_TYRE, 150), ("Rear", WHEELBASE, REAR_TYRE, 145)):
        base = build_wheel(T["D"], T["W"], disc_r)
        for side, s in (("R", 1), ("L", -1)):
            key = "%s%s" % (axle[0], side)
            grp = {}
            for n, (shp, col) in base.items():
                sh = shp.copy()
                if s < 0:
                    sh = mirror_y(sh)
                sh.translate(V(x, s * T["track"] / 2, T["D"] / 2))
                grp["%s_%s" % (n, key)] = (sh, col)
            out["Wheel_" + key] = grp
    return out


# =============================== assembly ===============================
def add(doc, container, name, shape, color):
    o = doc.addObject("Part::Feature", name)
    o.Shape = shape
    container.addObject(o)
    if App.GuiUp:
        vo = o.ViewObject
        vo.ShapeColor = color
        vo.DisplayMode = "Shaded"
        try:
            mat = App.Material()
            mat.DiffuseColor = color
            mat.SpecularColor = (0.8, 0.8, 0.9)
            mat.Shininess = 0.85 if color not in (C_TYRE, C_CARBON) else 0.3
            vo.ShapeAppearance = (mat,)
        except Exception:
            pass
    return o


def group(doc, parent, name):
    p = doc.addObject("App::Part", name)
    if parent is not None:
        parent.addObject(p)
    return p


EXPLODE = [   # (name prefix, offset) - first match wins
    ("FrontWing", V(-650, 0, -50)), ("NoseCone", V(-350, 0, 200)), ("Decal_77", V(-350, 0, 200)),
    ("Halo", V(0, 0, 550)), ("DriverHelmet", V(0, 0, 350)), ("HelmetVisor", V(0, 0, 350)),
    ("SteeringWheel", V(0, 0, 250)),
    ("Mirror_R", V(0, 350, 450)), ("Mirror_L", V(0, -350, 450)),
    ("MirrorGlass_R", V(0, 350, 450)), ("MirrorGlass_L", V(0, -350, 450)),
    ("EngineCover", V(0, 0, 900)), ("TCam", V(0, 0, 900)), ("Decal_AURORA_EngineCover", V(0, 0, 900)),
    ("Sidepod_R", V(0, 750, 250)), ("Decal_AURORA_SidepodR", V(0, 750, 250)),
    ("Sidepod_L", V(0, -750, 250)), ("Decal_AURORA_SidepodL", V(0, -750, 250)),
    ("Radiators", V(0, 0, 450)), ("ControlElectronics", V(0, 450, 450)),
    ("Floor", V(0, 0, -450)), ("Diffuser", V(450, 0, -450)),
    ("RearWing", V(750, 0, 450)), ("Decal_AURORA_RearEndplate", V(750, 0, 450)),
    ("Gearbox", V(350, 0, 150)), ("RearCrash", V(700, 0, 150)), ("RainLight", V(700, 0, 150)),
    ("Driveshaft_R", V(0, 250, 0)), ("Driveshaft_L", V(0, -250, 0)),
    ("FrontSuspension_R", V(0, 300, 0)), ("FrontSuspension_L", V(0, -300, 0)),
    ("FrontUpright_R", V(0, 450, 0)), ("FrontUpright_L", V(0, -450, 0)),
    ("RearSuspension_R", V(0, 300, 0)), ("RearSuspension_L", V(0, -300, 0)),
    ("RearUpright_R", V(0, 450, 0)), ("RearUpright_L", V(0, -450, 0)),
    ("Wheel_FR", V(0, 800, 0)), ("Wheel_FL", V(0, -800, 0)),
    ("Wheel_RR", V(0, 800, 0)), ("Wheel_RL", V(0, -800, 0)),
    ("ICE", V(0, 0, 450)), ("Turbo", V(0, 0, 450)), ("MGU", V(0, 0, 450)), ("Exhaust", V(0, 0, 450)),
]


def explode(doc, k=1.0):
    """Exploded view (k=0 restores the assembled state)."""
    for o in doc.Objects:
        for prefix, off in EXPLODE:
            if o.Name.startswith(prefix) and (o.TypeId == "Part::Feature" or o.Name.startswith("Wheel_")):
                o.Placement = App.Placement(off * k, App.Rotation())
                break
    doc.recompute()


def build(save_path=None):
    if DOC_NAME in App.listDocuments():
        App.closeDocument(DOC_NAME)
    doc = App.newDocument(DOC_NAME)
    root = group(doc, None, "AURORA_A1_Assembly")

    g = group(doc, root, "Chassis")
    chassis = build_chassis()
    for n, (s, c) in chassis.items():
        add(doc, g, n, s, c)

    aero, pod_r, pod_l, cover = build_aero()
    g = group(doc, root, "Aerodynamics")
    for n, (s, c) in aero.items():
        add(doc, g, n, s, c)

    g = group(doc, root, "PowerUnit")
    for n, (s, c) in build_power_unit().items():
        add(doc, g, n, s, c)

    g = group(doc, root, "Drivetrain")
    for n, (s, c) in build_drivetrain().items():
        add(doc, g, n, s, c)

    g = group(doc, root, "Suspension")
    for n, (s, c) in build_suspension().items():
        add(doc, g, n, s, c)

    g = group(doc, root, "Wheels")
    for wn, parts in build_wheels().items():
        wg = group(doc, g, wn)
        for n, (s, c) in parts.items():
            add(doc, wg, n, s, c)

    # livery decals
    g = group(doc, root, "Livery")
    decals = [
        ("Decal_AURORA_SidepodR", "AURORA", 105, pod_r, V(1520, 800, 390),
         App.Rotation(V(1, 0, 0), -90).multiply(App.Rotation(V(0, 0, 1), 180))),
        ("Decal_AURORA_SidepodL", "AURORA", 105, pod_l, V(1520, -800, 390),
         App.Rotation(V(1, 0, 0), 90)),
        ("Decal_77_Nose", "77", 150, chassis["NoseCone"][0], V(-430, 0, 500),
         App.Rotation(V(0, 0, 1), -90)),
        ("Decal_AURORA_EngineCover", "AURORA", 70, cover, V(2350, 0, 900),
         App.Rotation(V(0, 0, 1), 0)),
    ]
    for n, txt, size, host, pl, rot in decals:
        shift = V(0, 6 if pl.y > 0 else -6, 0) if "Sidepod" in n else V(0, 0, 6)
        d = decal(txt, size, host, pl, rot, shift=shift)
        if d is not None and d.Volume > 1:
            add(doc, g, n, d, C_WHITE)
    for side, y, rot in (("R", 530, App.Rotation(V(1, 0, 0), -90).multiply(App.Rotation(V(0, 0, 1), 180))),
                         ("L", -530, App.Rotation(V(1, 0, 0), 90))):
        ts = text_solid("AURORA", 60, 3)
        ts.Placement = App.Placement(V(4310, y, 640), rot).multiply(ts.Placement)
        add(doc, g, "Decal_AURORA_RearEndplate_" + side, ts, C_WHITE)

    doc.recompute()
    if App.GuiUp:
        import FreeCADGui as Gui
        v = Gui.getDocument(DOC_NAME).activeView()
        v.viewIsometric()
        v.fitAll()
    if save_path:
        doc.saveAs(save_path)
    return doc
