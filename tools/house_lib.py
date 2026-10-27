"""Bibliotheque de construction : pieces, murs, meubles, vegetation.

Chaque `part()` ajoute aussi une entree dans BOXES pour le rendu d'apercu.
"""

from __future__ import annotations

import math
import random

from rbxlx import MATERIAL, SHAPE, Node, packed

RNG = random.Random(20261027)
BOXES: list[dict] = []

C = {
    "white": (0.94, 0.93, 0.90), "warmwhite": (0.89, 0.86, 0.80),
    "cream": (0.83, 0.79, 0.72), "sand": (0.74, 0.69, 0.60),
    "charcoal": (0.14, 0.15, 0.16), "dark": (0.09, 0.10, 0.11),
    "black": (0.045, 0.048, 0.055),
    "wood": (0.47, 0.32, 0.20), "woodlight": (0.68, 0.51, 0.33),
    "woodmid": (0.58, 0.40, 0.25), "wooddark": (0.29, 0.19, 0.12),
    "walnut": (0.36, 0.24, 0.16),
    "stone": (0.73, 0.72, 0.69), "concrete": (0.67, 0.66, 0.63),
    "marble": (0.93, 0.93, 0.91), "marblegrey": (0.83, 0.84, 0.83),
    "grass": (0.31, 0.43, 0.23), "lawn": (0.34, 0.47, 0.25),
    "leaf": (0.23, 0.37, 0.19), "leaf2": (0.32, 0.47, 0.23),
    "leaf3": (0.41, 0.53, 0.27), "pink": (0.88, 0.66, 0.72),
    "brass": (0.73, 0.56, 0.29), "steel": (0.64, 0.66, 0.68),
    "glass": (0.62, 0.76, 0.81), "water": (0.22, 0.58, 0.70),
    "fabric": (0.57, 0.57, 0.54), "linen": (0.78, 0.75, 0.68),
    "sage": (0.53, 0.59, 0.50), "terracotta": (0.70, 0.39, 0.28),
    "navy": (0.17, 0.23, 0.32), "olive": (0.36, 0.42, 0.28),
    "rust": (0.62, 0.31, 0.20), "bluegrey": (0.44, 0.51, 0.56),
    "tile": (0.88, 0.87, 0.83), "gold": (0.80, 0.65, 0.34),
    "screen": (0.07, 0.08, 0.10), "neon": (1.0, 0.90, 0.70),
}


def tint(rgb, k):
    return tuple(max(0, min(1, c * k)) for c in rgb)


def jitter(rgb, amount=0.04):
    return tuple(max(0, min(1, c + RNG.uniform(-amount, amount))) for c in rgb)


def part(parent, name, pos, size, color, mat="SmoothPlastic", tr=0, rot=(0, 0, 0),
         shape="Block", collide=True, shadow=True, refl=0, tag="", neon=False):
    n = parent.add("Part", name)
    n.b("Anchored", True).b("CanCollide", collide).b("CastShadow", shadow)
    n.v3("Size", size).cf("CFrame", pos, rot)
    n.c3("Color", color).p("Color3uint8", "Color3uint8", str(packed(color)))
    n.tok("Material", MATERIAL.get(mat, 256))
    if shape != "Block":
        n.tok("Shape", SHAPE[shape])
    if tr:
        n.f("Transparency", tr)
    if refl:
        n.f("Reflectance", refl)
    if neon:
        n.tok("Material", MATERIAL["Neon"])
    BOXES.append({
        "name": name, "pos": list(pos), "size": list(size), "rot": list(rot),
        "color": list(color), "tr": tr, "shape": shape, "tag": tag,
    })
    return n


def ball(parent, name, pos, d, color, mat="SmoothPlastic", tr=0, tag=""):
    return part(parent, name, pos, (d, d, d), color, mat, tr, shape="Ball", tag=tag)


def disc(parent, name, center, radius, thick, color, mat="SmoothPlastic",
         segments=18, tr=0, tag="", collide=True):
    """Disque construit en eventail de boites (pas de cylindre ambigu)."""
    holder = parent.add("Model", name)
    chord = 2 * radius * math.sin(math.pi / segments) * 1.25
    for k in range(segments):
        a = 2 * math.pi * k / segments
        px = center[0] + math.cos(a) * radius / 2
        pz = center[2] + math.sin(a) * radius / 2
        part(holder, f"Rayon{k:02d}", (px, center[1], pz),
             (radius, thick, chord), color, mat, tr,
             rot=(0, -math.degrees(a), 0), collide=collide, tag=tag)
    return holder


def light(parent, name, pos, color=(1.0, 0.86, 0.68), brightness=1.2, range_=18,
          kind="PointLight", shadows=False):
    n = parent.add(kind, name)
    n.c3("Color", color).f("Brightness", brightness).f("Range", range_)
    n.b("Enabled", True).b("Shadows", shadows)
    return n


def glowing_bulb(parent, name, pos, size, color=C["neon"], range_=16, brightness=1.0):
    p = part(parent, name, pos, size, color, "Neon", tag="LIGHT")
    light(parent, f"Lumiere_{name}", pos, color, brightness, range_)
    return p


def downlights(parent, x0, x1, z0, z1, y, step=5.0, color=(1.0, 0.90, 0.76)):
    """Plafonniers encastres + vraies lumieres ponctuelles."""
    xs = [x0 + (x1 - x0) * i / max(1, int((x1 - x0) / step))
          for i in range(int((x1 - x0) / step) + 1)]
    zs = [z0 + (z1 - z0) * i / max(1, int((z1 - z0) / step))
          for i in range(int((z1 - z0) / step) + 1)]
    for x in xs:
        for z in zs:
            part(parent, "SpotEncastre", (x, y, z), (0.9, 0.14, 0.9),
                 C["charcoal"], "Metal", tag="CEIL")
            glowing_bulb(parent, "LED", (x, y - 0.1, z), (0.62, 0.08, 0.62),
                         color, range_=17, brightness=0.85)


def pendant(parent, pos, length, color=C["brass"], shade=C["charcoal"], r=0.9):
    part(parent, "Cable", (pos[0], pos[1] - length / 2, pos[2]),
         (0.08, length, 0.08), color, "Metal")
    disc(parent, "AbatJour", (pos[0], pos[1] - length, pos[2]), r, 0.5,
         shade, "Metal", segments=14, tag="LIGHT")
    glowing_bulb(parent, "Ampoule", (pos[0], pos[1] - length - 0.12, pos[2]),
                 (0.34, 0.3, 0.34), C["neon"], range_=14, brightness=0.8)


def switch(parent, pos, room, rot=(0, 0, 0)):
    sw = part(parent, f"Interrupteur_{room}", pos, (0.7, 1.1, 0.16), C["white"],
              "SmoothPlastic", rot=rot)
    cd = sw.add("ClickDetector")
    cd.f("MaxActivationDistance", 12)
    val = sw.add("StringValue", "Room")
    val.s("Value", room)
    return sw


# ---------------------------------------------------------------------------
# Murs / sols / plafonds
# ---------------------------------------------------------------------------

def wall_box(parent, name, axis, fixed, s0, s1, yb, yt, t, color, mat, tag=""):
    if axis == "x":
        return part(parent, name, ((s0 + s1) / 2, (yb + yt) / 2, fixed),
                    (s1 - s0, yt - yb, t), color, mat, tag=tag)
    return part(parent, name, (fixed, (yb + yt) / 2, (s0 + s1) / 2),
                (t, yt - yb, s1 - s0), color, mat, tag=tag)


def glazing(parent, axis, fixed, opening, t, curtains=False):
    """Remplit une ouverture : chassis aluminium, vitrage, meneaux, seuil."""
    s0, s1, yb, yt, kind = opening
    span, h = s1 - s0, yt - yb
    mid = (s0 + s1) / 2
    frame = C["charcoal"]
    fr, fd = 0.20, 0.24
    # seuil / appui
    wall_box(parent, "Appui", axis, fixed, s0 - 0.25, s1 + 0.25,
             yb - 0.16, yb, t + 0.35, C["stone"], "Marble", tag="WIN")
    # montants
    posts = [s0, s1]
    if span > 9:
        posts.append(mid)
    if span > 17:
        posts += [s0 + span / 3, s0 + 2 * span / 3]
    posts = sorted(set(posts))
    for i, s in enumerate(posts):
        wall_box(parent, f"Montant{i}", axis, fixed, s - fr / 2, s + fr / 2,
                 yb, yt, fd, frame, "Metal", tag="WIN")
    # traverses haute et intermediaire
    rails = [yb, yt]
    if h > 6:
        rails.append(yb + h * 0.62)
    for i, y in enumerate(sorted(set(rails))):
        wall_box(parent, f"Traverse{i}", axis, fixed, s0, s1,
                 y - fr / 2, y + fr / 2, fd, frame, "Metal", tag="WIN")
    # vitres
    for i in range(len(posts) - 1):
        a, b = posts[i] + fr / 2, posts[i + 1] - fr / 2
        for j in range(len(rails) - 1):
            lo, hi = rails[j] + fr / 2, rails[j + 1] - fr / 2
            if b - a < 0.05 or hi - lo < 0.05:
                continue
            solid = kind == "win" and yb > 0.7
            p = wall_box(parent, f"Vitre_{i}_{j}", axis, fixed, a, b, lo, hi,
                         0.10, C["glass"], "Glass", tag="GLASS")
            # transparence + absence d'ombre pour un rendu propre
            p.f("Transparency", 0.72 if kind != "door" else 0.15)
            p.b("CastShadow", False)
            p.b("CanCollide", solid)
            BOXES[-1]["tr"] = 0.72
            BOXES[-1]["color"] = list(C["glass"])
    if kind == "door":
        # porte d'entree en bois, laissee ouverte (pivot a 80 degres)
        wall_box(parent, "PorteEntree", axis, fixed, s0 + 0.25, s0 + 1.5,
                 yb + 0.05, yt - 0.1, 0.25, C["walnut"], "Wood", tag="WIN")
    if curtains:
        for s, side in ((s0 + 0.35, "G"), (s1 - 0.35, "D")):
            wall_box(parent, f"Rideau{side}", axis, fixed + (0.5 if fixed > 0 else -0.5),
                     s - 0.05, s + 0.75, yb + 0.1, yt - 0.15, 0.12,
                     C["linen"], "Fabric", tag="CURTAIN")


def wall(parent, name, axis, fixed, a0, a1, y0, y1, t, color, mat,
         openings=(), tag=""):
    """Mur avec decoupes de fenetres/portes (openings = (s0,s1,yb,yt,kind))."""
    model = parent.add("Model", name)
    bounds = sorted({a0, a1} | {o[0] for o in openings} | {o[1] for o in openings})
    bounds = [v for v in bounds if a0 - 0.001 <= v <= a1 + 0.001]
    for k in range(len(bounds) - 1):
        s0, s1 = bounds[k], bounds[k + 1]
        if s1 - s0 < 0.02:
            continue
        mid = (s0 + s1) / 2
        active = sorted((o for o in openings if o[0] <= mid <= o[1]),
                        key=lambda o: o[2])
        cursor = y0
        for o in active:
            if o[2] > cursor + 0.02:
                wall_box(model, "MurPlein", axis, fixed, s0, s1, cursor, o[2],
                         t, color, mat, tag=tag)
            cursor = max(cursor, o[3])
            glazing(model, axis, fixed, o, t,
                    curtains=o[4] == "win" and y0 > 10)
        if y1 > cursor + 0.02:
            wall_box(model, "MurPlein", axis, fixed, s0, s1, cursor, y1,
                     t, color, mat, tag=tag)
    return model


def floor_planks(parent, name, x0, x1, z0, z1, y, base=None, width=1.15,
                 along="z", tag=""):
    base = base or C["woodlight"]
    m = parent.add("Model", name)
    part(m, "SousCouche", ((x0 + x1) / 2, y - 0.06, (z0 + z1) / 2),
         (x1 - x0, 0.12, z1 - z0), C["wooddark"], "Wood", tag=tag)
    if along == "z":
        n = max(1, int((x1 - x0) / width))
        w = (x1 - x0) / n
        for i in range(n):
            part(m, f"Lame_{i:03d}", (x0 + w * (i + 0.5), y, (z0 + z1) / 2),
                 (w - 0.045, 0.12, z1 - z0 - 0.05), jitter(base), "Wood", tag=tag)
    else:
        n = max(1, int((z1 - z0) / width))
        w = (z1 - z0) / n
        for i in range(n):
            part(m, f"Lame_{i:03d}", ((x0 + x1) / 2, y, z0 + w * (i + 0.5)),
                 (x1 - x0 - 0.05, 0.12, w - 0.045), jitter(base), "Wood", tag=tag)
    return m


def floor_tiles(parent, name, x0, x1, z0, z1, y, tile=2.0, tag=""):
    m = parent.add("Model", name)
    part(m, "Chape", ((x0 + x1) / 2, y - 0.07, (z0 + z1) / 2),
         (x1 - x0, 0.14, z1 - z0), C["stone"], "Marble", tag=tag)
    nx, nz = max(1, round((x1 - x0) / tile)), max(1, round((z1 - z0) / tile))
    sx, sz = (x1 - x0) / nx, (z1 - z0) / nz
    for i in range(nx):
        for j in range(nz):
            c = jitter(C["marble"] if (i + j) % 2 == 0 else C["marblegrey"], 0.025)
            part(m, f"Carreau_{i}_{j}",
                 (x0 + sx * (i + 0.5), y, z0 + sz * (j + 0.5)),
                 (sx - 0.06, 0.12, sz - 0.06), c, "Marble", tag=tag, refl=0.08)
    return m


def ceiling(parent, name, x0, x1, z0, z1, y, tag="CEIL", hole=None):
    """Plafond, avec eventuelle trappe (hole = (hx0,hx1,hz0,hz1))."""
    m = parent.add("Model", name)
    slabs = [(x0, x1, z0, z1)]
    if hole:
        hx0, hx1, hz0, hz1 = hole
        slabs = [
            (x0, hx0, z0, z1), (hx1, x1, z0, z1),
            (hx0, hx1, z0, hz0), (hx0, hx1, hz1, z1),
        ]
    for i, (a, b, c, d) in enumerate(slabs):
        if b - a < 0.05 or d - c < 0.05:
            continue
        part(m, f"Plafond{i}", ((a + b) / 2, y, (c + d) / 2),
             (b - a, 0.35, d - c), C["white"], "SmoothPlastic", tag=tag)
    # corniche perimetrique avec ruban LED
    for z in (z0 + 0.25, z1 - 0.25):
        part(m, "Corniche", ((x0 + x1) / 2, y - 0.35, z),
             (x1 - x0, 0.35, 0.5), C["warmwhite"], "SmoothPlastic", tag=tag)
        part(m, "RubanLED", ((x0 + x1) / 2, y - 0.54, z + (0.3 if z < 0 else -0.3)),
             (x1 - x0 - 1, 0.08, 0.12), C["neon"], "Neon", tag=tag)
    return m


def rug(parent, name, x, z, y, w, d, color, border=None):
    m = parent.add("Model", name)
    part(m, "Tapis", (x, y, z), (w, 0.09, d), color, "Fabric")
    border = border or tint(color, 0.75)
    for dx in (-w / 2 + 0.28, w / 2 - 0.28):
        part(m, "Bordure", (x + dx, y + 0.06, z), (0.16, 0.03, d - 0.5), border, "Fabric")
    for dz in (-d / 2 + 0.28, d / 2 - 0.28):
        part(m, "Bordure", (x, y + 0.06, z + dz), (w - 0.5, 0.03, 0.16), border, "Fabric")
    return m


def artwork(parent, name, pos, w, h, axis="x", colors=(C["sage"], C["cream"], C["terracotta"])):
    m = parent.add("Model", name)
    if axis == "x":
        part(m, "Cadre", pos, (w + 0.3, h + 0.3, 0.16), C["walnut"], "Wood")
        for i, c in enumerate(colors):
            part(m, f"Touche{i}", (pos[0] - w / 2 + w * (i + 0.5) / len(colors),
                                   pos[1], pos[2] - 0.1),
                 (w / len(colors) - 0.12, h - 0.25, 0.05), c, "SmoothPlastic")
    else:
        part(m, "Cadre", pos, (0.16, h + 0.3, w + 0.3), C["walnut"], "Wood")
        for i, c in enumerate(colors):
            part(m, f"Touche{i}", (pos[0] - 0.1, pos[1],
                                   pos[2] - w / 2 + w * (i + 0.5) / len(colors)),
                 (0.05, h - 0.25, w / len(colors) - 0.12), c, "SmoothPlastic")
    return m


def plant(parent, name, pos, h=2.2, flower=False):
    m = parent.add("Model", name)
    part(m, "Pot", (pos[0], pos[1] + 0.45, pos[2]), (1.0, 0.9, 1.0),
         C["terracotta"], "Sandstone")
    part(m, "Terre", (pos[0], pos[1] + 0.9, pos[2]), (0.9, 0.12, 0.9), C["wooddark"], "Ground")
    part(m, "Tige", (pos[0], pos[1] + 0.9 + h / 2, pos[2]), (0.16, h, 0.16),
         C["leaf"], "Wood")
    for k, (dx, dy, dz, r) in enumerate([
        (-0.6, 0.2, 0.2, 0.95), (0.6, 0.0, -0.2, 0.85),
        (0.15, 0.75, 0.5, 0.8), (-0.25, 0.55, -0.55, 0.75),
        (0.0, 1.25, 0.0, 0.65),
    ]):
        ball(m, f"Feuille{k}", (pos[0] + dx, pos[1] + 1.0 + h / 2 + dy, pos[2] + dz),
             r, C["pink"] if flower else (C["leaf"] if k % 2 else C["leaf2"]),
             "Grass")
    return m


def bookshelf(parent, name, pos, w=4.0, h=6.0, rot=(0, 0, 0)):
    m = parent.add("Model", name)
    part(m, "Dos", pos, (w, h, 0.25), C["wooddark"], "Wood", rot=rot)
    for s in (-1, 1):
        part(m, "Montant", (pos[0] + s * w / 2, pos[1], pos[2] + 0.45),
             (0.22, h, 1.1), C["wooddark"], "Wood", rot=rot)
    for j in range(4):
        y = pos[1] - h / 2 + 0.2 + j * (h - 0.4) / 3
        part(m, "Etagere", (pos[0], y, pos[2] + 0.45), (w, 0.16, 1.1),
             C["woodlight"], "Wood", rot=rot)
        for k in range(9):
            bh = RNG.uniform(0.9, 1.35)
            c = RNG.choice([C["navy"], C["rust"], C["cream"], C["sage"],
                            C["wooddark"], C["terracotta"], C["gold"]])
            part(m, f"Livre{j}_{k}",
                 (pos[0] - w / 2 + 0.35 + k * (w - 0.7) / 9,
                  y + 0.1 + bh / 2, pos[2] + 0.45),
                 ((w - 0.7) / 9 - 0.07, bh, 0.7), c, "SmoothPlastic", rot=rot)
    return m


# ---------------------------------------------------------------------------
# Meubles
# ---------------------------------------------------------------------------

def sofa(parent, name, x, z, y, yaw=0, w=10.0, d=3.6, color=C["fabric"], chaise=False):
    m = parent.add("Model", name)
    rot = (0, yaw, 0)
    part(m, "Pietement", (x, y + 0.55, z), (w, 0.5, d), C["wooddark"], "Wood", rot=rot)
    part(m, "Assise", (x, y + 1.05, z), (w, 0.85, d), color, "Fabric", rot=rot)
    part(m, "Dossier", (x, y + 2.2, z + d / 2 - 0.4), (w, 2.3, 0.8),
         tint(color, 0.95), "Fabric", rot=rot)
    for s in (-1, 1):
        part(m, "Accoudoir", (x + s * (w / 2 - 0.4), y + 1.6, z),
             (0.8, 1.7, d), tint(color, 0.9), "Fabric", rot=rot)
    n = 4 if w > 8 else 3
    for i in range(n):
        cw = (w - 1.8) / n
        part(m, f"Coussin{i}", (x - (w - 1.8) / 2 + cw * (i + 0.5), y + 1.6, z - 0.25),
             (cw - 0.12, 0.5, d - 1.2), tint(color, 1.08), "Fabric", rot=rot)
        part(m, f"CoussinDos{i}",
             (x - (w - 1.8) / 2 + cw * (i + 0.5), y + 2.4, z + d / 2 - 0.85),
             (cw - 0.2, 1.35, 0.45), tint(color, 1.06), "Fabric", rot=rot)
    for i, c in enumerate([C["terracotta"], C["sage"], C["cream"]]):
        part(m, f"CoussinDeco{i}", (x - w / 2 + 1.2 + i * 1.4, y + 2.35, z + 0.85),
             (1.1, 1.1, 0.4), c, "Fabric", rot=rot)
    if chaise:
        part(m, "Méridienne", (x + w / 2 + d / 2, y + 1.05, z - d / 2),
             (d, 0.85, d * 2), color, "Fabric", rot=rot)
    return m


def armchair(parent, name, x, z, y, yaw=0, color=C["sage"]):
    m = parent.add("Model", name)
    r = (0, yaw, 0)
    part(m, "Assise", (x, y + 0.9, z), (3.0, 0.8, 3.0), color, "Fabric", rot=r)
    part(m, "Dossier", (x, y + 1.9, z + 1.25), (3.0, 2.0, 0.6), color, "Fabric", rot=r)
    for s in (-1, 1):
        part(m, "Accoudoir", (x + s * 1.25, y + 1.35, z), (0.5, 1.1, 3.0),
             tint(color, 0.9), "Fabric", rot=r)
    for dx in (-1, 1):
        for dz in (-1, 1):
            part(m, "Pied", (x + dx * 1.2, y + 0.25, z + dz * 1.2),
                 (0.2, 0.5, 0.2), C["wooddark"], "Wood", rot=r)
    return m


def coffee_table(parent, name, x, z, y, w=6.0, d=3.2):
    m = parent.add("Model", name)
    part(m, "Plateau", (x, y + 1.5, z), (w, 0.28, d), C["walnut"], "Wood", refl=0.15)
    part(m, "Tablette", (x, y + 0.55, z), (w - 0.8, 0.16, d - 0.6), C["wooddark"], "Wood")
    for dx in (-1, 1):
        for dz in (-1, 1):
            part(m, "Pied", (x + dx * (w / 2 - 0.35), y + 0.75, z + dz * (d / 2 - 0.3)),
                 (0.22, 1.5, 0.22), C["charcoal"], "Metal")
    for i, c in enumerate([C["cream"], C["navy"], C["terracotta"]]):
        part(m, f"Livre{i}", (x - 1.7 + i * 0.12, y + 1.72 + i * 0.13, z - 0.6),
             (1.5, 0.13, 1.0), c, "SmoothPlastic")
    part(m, "Vase", (x + 1.6, y + 1.95, z + 0.6), (0.55, 0.85, 0.55),
         C["steel"], "Marble")
    for k in range(3):
        ball(m, f"Fleur{k}", (x + 1.6 + (k - 1) * 0.35, y + 2.7, z + 0.6 + (k % 2) * 0.3),
             0.45, C["pink"], "Fabric")
    return m


def tv_wall(parent, name, x, z, y, axis="x"):
    """Meuble TV + ecran. axis='x' -> ecran face +Z, 'z' -> face -X."""
    m = parent.add("Model", name)
    r = (0, 90, 0) if axis == "z" else (0, 0, 0)

    def pos(d=0.0, lat=0.0, h=0.0):
        # d = avancement vers le spectateur, lat = decalage lateral, h = hauteur
        if axis == "z":
            return (x - d, y + h, z + lat)
        return (x + lat, y + h, z + d)

    part(m, "MeubleTV", pos(0, 0, 1.2), (9.0, 2.4, 1.6),
         C["walnut"], "Wood", rot=r)
    for i in range(3):
        part(m, f"Tiroir{i}", pos(0.85, (-1 + i) * 2.9, 1.2),
             (2.7, 1.6, 0.08), C["wooddark"], "Wood", rot=r)
    part(m, "CadreTV", pos(0.95, 0, 6.2), (11.0, 6.3, 0.3),
         C["black"], "SmoothPlastic", rot=r)
    part(m, "Ecran", pos(1.13, 0, 6.2), (10.6, 5.9, 0.08),
         C["screen"], "Glass", rot=r, refl=0.35)
    part(m, "Reflet", pos(1.19, -2.5, 6.4), (2.6, 4.4, 0.03),
         C["bluegrey"], "Glass", tr=0.78, rot=r)
    part(m, "BarreDeSon", pos(0.6, 0, 2.7), (5.0, 0.5, 0.7),
         C["charcoal"], "Metal", rot=r)
    for i in range(4):
        part(m, f"Enceinte{i}", pos(0.6, (i - 1.5) * 2.6, 0.5),
             (0.35, 0.35, 0.35), C["dark"], "Metal", rot=r)
    return m

def dining_set(parent, name, x, z, y, seats=8):
    m = parent.add("Model", name)
    part(m, "Plateau", (x, y + 2.9, z), (13.0, 0.35, 5.0), C["walnut"], "Wood", refl=0.15)
    for dx in (-5.3, 5.3):
        for dz in (-1.7, 1.7):
            part(m, "PiedTable", (x + dx, y + 1.45, z + dz), (0.5, 2.9, 0.5),
                 C["charcoal"], "Metal")
    for k in range(seats):
        side = -1 if k < seats // 2 else 1
        idx = k % (seats // 2)
        cx = x - 4.6 + idx * (9.2 / max(1, seats // 2 - 1))
        cz = z + side * 3.6
        part(m, f"Assise{k}", (cx, y + 1.75, cz), (1.9, 0.3, 1.9), C["fabric"], "Fabric")
        part(m, f"Dossier{k}", (cx, y + 3.0, cz + side * 0.85), (1.9, 2.4, 0.22),
             C["wooddark"], "Wood")
        for ddx in (-0.75, 0.75):
            for ddz in (-0.75, 0.75):
                part(m, f"Pied{k}_{ddx}_{ddz}", (cx + ddx, y + 0.85, cz + ddz),
                     (0.16, 1.7, 0.16), C["charcoal"], "Metal")
    for i in range(4):
        px = x - 3.6 + i * 2.4
        for side in (-1, 1):
            part(m, f"SetDeTable{i}_{side}", (px, y + 3.12, z + side * 1.2),
                 (1.9, 0.05, 1.3), C["linen"], "Fabric")
            disc(m, f"Assiette{i}_{side}", (px, y + 3.22, z + side * 1.2),
                 0.55, 0.08, C["white"], "Marble", segments=10)
            part(m, f"Verre{i}_{side}", (px + 0.65, y + 3.5, z + side * 1.2),
                 (0.32, 0.55, 0.32), C["glass"], "Glass", tr=0.5)
    part(m, "CentreDeTable", (x, y + 3.35, z), (2.6, 0.35, 1.0), C["steel"], "Marble")
    for k in range(5):
        ball(m, f"Fleur{k}", (x - 1 + k * 0.5, y + 3.9, z + (k % 2) * 0.3 - 0.15),
             0.42, C["cream"] if k % 2 else C["pink"], "Fabric")
    return m


def kitchen(parent, name, x0, x1, z0, z1, y):
    m = parent.add("Model", name)
    # meubles bas le long du mur est et du mur nord
    part(m, "PlanEst", (x1 - 1.2, y + 3.3, (z0 + z1) / 2),
         (2.4, 0.3, z1 - z0 - 1.0), C["marble"], "Marble", refl=0.12)
    part(m, "CaissonsEst", (x1 - 1.2, y + 1.6, (z0 + z1) / 2),
         (2.4, 3.2, z1 - z0 - 1.0), C["warmwhite"], "SmoothPlastic")
    for i in range(7):
        zz = z0 + 1.2 + i * (z1 - z0 - 2.4) / 6
        part(m, f"PorteEst{i}", (x1 - 2.45, y + 1.7, zz),
             (0.12, 2.6, (z1 - z0) / 7 - 0.18), C["sage"], "Wood")
        part(m, f"PoigneeEst{i}", (x1 - 2.55, y + 2.8, zz),
             (0.1, 0.7, 0.1), C["brass"], "Metal")
    # credence en carrelage
    for i in range(12):
        zz = z0 + 0.9 + i * (z1 - z0 - 1.8) / 11
        for j in range(3):
            part(m, f"Credence{i}_{j}", (x1 - 2.48, y + 4.0 + j * 0.9, zz),
                 (0.08, 0.85, (z1 - z0 - 1.8) / 11 - 0.06),
                 jitter(C["tile"], 0.02), "Marble")
    # meubles hauts
    part(m, "MeublesHauts", (x1 - 0.9, y + 7.1, (z0 + z1) / 2),
         (1.8, 2.6, z1 - z0 - 2.5), C["warmwhite"], "SmoothPlastic")
    for i in range(6):
        zz = z0 + 2.0 + i * (z1 - z0 - 4) / 5
        part(m, f"PorteHaute{i}", (x1 - 1.85, y + 7.1, zz),
             (0.1, 2.3, (z1 - z0 - 4) / 5 - 0.16), C["cream"], "Wood")
    # evier + robinetterie
    part(m, "Evier", (x1 - 1.4, y + 3.2, z0 + 4.0), (1.7, 0.35, 2.6),
         C["steel"], "Metal", refl=0.3)
    part(m, "Robinet", (x1 - 2.0, y + 4.0, z0 + 4.0), (0.18, 1.5, 0.18),
         C["steel"], "Metal", refl=0.4)
    part(m, "BecRobinet", (x1 - 1.7, y + 4.7, z0 + 4.0), (0.8, 0.16, 0.18),
         C["steel"], "Metal", refl=0.4)
    # plaque de cuisson + four + hotte
    part(m, "Plaque", (x1 - 1.3, y + 3.52, z1 - 5.0), (2.0, 0.12, 3.0), C["black"], "Glass")
    for dx in (-0.55, 0.55):
        for dz in (-0.75, 0.75):
            disc(m, f"Foyer{dx}_{dz}", (x1 - 1.3 + dx, y + 3.62, z1 - 5.0 + dz),
                 0.42, 0.06, C["charcoal"], "Metal", segments=10)
    part(m, "Four", (x1 - 2.5, y + 1.7, z1 - 5.0), (0.14, 2.5, 2.7), C["black"], "Glass")
    part(m, "FourPoignee", (x1 - 2.6, y + 2.6, z1 - 5.0), (0.12, 0.16, 2.2), C["steel"], "Metal")
    part(m, "Hotte", (x1 - 1.3, y + 7.6, z1 - 5.0), (2.4, 1.2, 3.4), C["steel"], "Metal")
    part(m, "ConduitHotte", (x1 - 1.3, y + 8.9, z1 - 5.0), (1.4, 1.6, 1.4), C["steel"], "Metal")
    # refrigerateur americain
    part(m, "Frigo", (x1 - 1.6, y + 4.0, z0 + 1.4), (2.8, 8.0, 3.4), C["steel"], "Metal", refl=0.22)
    for s in (-1, 1):
        part(m, f"PorteFrigo{s}", (x1 - 3.05, y + 4.0, z0 + 1.4 + s * 0.86),
             (0.1, 7.6, 1.65), tint(C["steel"], 1.06), "Metal")
        part(m, f"PoigneeFrigo{s}", (x1 - 3.2, y + 4.2, z0 + 1.4 + s * 1.35),
             (0.12, 2.6, 0.12), C["charcoal"], "Metal")
    part(m, "Distributeur", (x1 - 3.12, y + 5.2, z0 + 0.9), (0.1, 1.2, 0.6), C["black"], "Glass")
    # ilot central
    ix = (x0 + x1) / 2 + 1.0
    iz = (z0 + z1) / 2 + 2.0
    part(m, "Ilot", (ix, y + 1.7, iz), (4.4, 3.4, 10.0), C["sage"], "Wood")
    part(m, "PlanIlot", (ix, y + 3.55, iz), (6.0, 0.35, 11.4), C["marble"], "Marble", refl=0.12)
    for k in range(4):
        part(m, f"TiroirIlot{k}", (ix - 2.25, y + 1.8, iz - 3.8 + k * 2.5),
             (0.1, 2.6, 2.2), tint(C["sage"], 0.9), "Wood")
    # tabourets
    for k in range(4):
        sz = iz - 3.6 + k * 2.4
        sx = ix - 3.9
        disc(m, f"AssiseTabouret{k}", (sx, y + 2.6, sz), 0.75, 0.25,
             C["walnut"], "Wood", segments=12)
        part(m, f"PiedTabouret{k}", (sx, y + 1.3, sz), (0.18, 2.6, 0.18),
             C["charcoal"], "Metal")
    # suspensions
    for k in range(3):
        pendant(m, (ix, y + 10.0, iz - 3.5 + k * 3.5), 3.4,
                shade=C["brass"], r=0.75)
    # petits details
    part(m, "Planche", (ix + 1.4, y + 3.85, iz + 3.5), (1.4, 0.18, 2.4), C["woodlight"], "Wood")
    for k in range(5):
        ball(m, f"Fruit{k}", (ix + 1.4 + (k - 2) * 0.24, y + 4.1, iz + 3.5 + (k % 2) * 0.3),
             0.42, RNG.choice([C["terracotta"], C["gold"], C["leaf3"]]), "SmoothPlastic")
    for k in range(4):
        part(m, f"PotEpice{k}", (x1 - 3.0, y + 3.9, z0 + 7 + k * 0.8),
             (0.45, 0.8, 0.45), RNG.choice([C["cream"], C["terracotta"], C["sage"]]), "Marble")
    return m


def bed(parent, name, x, z, y, yaw=0, w=7.5, d=8.5, color=C["linen"], accent=C["sage"]):
    m = parent.add("Model", name)
    r = (0, yaw, 0)
    part(m, "Sommier", (x, y + 1.2, z), (w, 1.6, d), C["wooddark"], "Wood", rot=r)
    part(m, "Matelas", (x, y + 2.35, z), (w + 0.2, 0.9, d + 0.2), C["white"], "Fabric", rot=r)
    part(m, "TeteDeLit", (x, y + 3.8, z + d / 2 + 0.25), (w + 1.2, 5.2, 0.7),
         accent, "Fabric", rot=r)
    for i in range(5):
        for j in range(3):
            ball(m, f"Capiton{i}_{j}",
                 (x - w / 2 + 1.0 + i * (w - 2) / 4, y + 2.3 + j * 1.5, z + d / 2 + 0.62),
                 0.16, C["brass"], "Metal")
    part(m, "Couette", (x, y + 2.95, z - 0.9), (w + 0.3, 0.55, d - 2.0),
         color, "Fabric", rot=r)
    part(m, "RetourCouette", (x, y + 2.65, z + d / 2 - 1.1), (w + 0.3, 0.6, 1.6),
         tint(color, 1.05), "Fabric", rot=r)
    for i in range(2):
        part(m, f"Oreiller{i}", (x + (i - 0.5) * (w / 2), y + 3.0, z + d / 2 - 2.0),
             (w / 2 - 0.5, 0.65, 1.8), C["white"], "Fabric", rot=r)
    for i, c in enumerate([C["terracotta"], C["navy"], C["cream"]]):
        part(m, f"Coussin{i}", (x - 1.6 + i * 1.6, y + 3.15, z + d / 2 - 3.0),
             (1.3, 1.3, 0.45), c, "Fabric", rot=r)
    part(m, "Plaid", (x, y + 3.3, z - d / 2 + 0.8), (w + 0.35, 0.2, 3.0),
         accent, "Fabric", rot=r)
    for s in (-1, 1):
        # tables de chevet
        nx = x + s * (w / 2 + 1.7)
        part(m, f"Chevet{s}", (nx, y + 1.4, z + d / 2 - 1.5), (2.2, 2.2, 2.2),
             C["walnut"], "Wood")
        part(m, f"Tiroir{s}", (nx - s * 1.15, y + 1.4, z + d / 2 - 1.5),
             (0.1, 1.4, 1.8), C["wooddark"], "Wood")
        part(m, f"PiedLampe{s}", (nx, y + 2.9, z + d / 2 - 1.5), (0.16, 1.2, 0.16), C["brass"], "Metal")
        part(m, f"AbatJour{s}", (nx, y + 3.7, z + d / 2 - 1.5), (1.3, 1.1, 1.3), C["cream"], "Fabric")
        glowing_bulb(m, f"AmpouleChevet{s}", (nx, y + 3.1, z + d / 2 - 1.5),
                     (0.3, 0.3, 0.3), C["neon"], range_=9, brightness=0.6)
    return m


def wardrobe(parent, name, x, z, y, w=8.0, h=9.0, axis="x"):
    m = parent.add("Model", name)
    r = (0, 0, 0) if axis == "x" else (0, 90, 0)
    part(m, "Corps", (x, y + h / 2, z), (w, h, 2.2), C["warmwhite"], "Wood", rot=r)
    for k in range(4):
        part(m, f"Porte{k}", (x - w / 2 + w * (k + 0.5) / 4, y + h / 2, z + (1.18 if axis == "x" else 0)),
             (w / 4 - 0.12, h - 0.3, 0.12), C["cream"], "Wood", rot=r)
    for k in range(3):
        part(m, f"Poignee{k}",
             (x - w / 2 + w * (k + 1) / 4, y + h / 2, z + (1.32 if axis == "x" else 0)),
             (0.1, 1.6, 0.1), C["brass"], "Metal", rot=r)
    part(m, "Miroir", (x + w / 2 - 1.5, y + h / 2, z + 1.32),
         (2.2, h - 1.0, 0.1), C["bluegrey"], "Glass", refl=0.5)
    return m


def bathroom(parent, name, x0, x1, z0, z1, y):
    m = parent.add("Model", name)
    cx, cz = (x0 + x1) / 2, (z0 + z1) / 2
    # faience murale
    for i in range(6):
        part(m, f"FaienceNord{i}", (x0 + (x1 - x0) * (i + 0.5) / 6, y + 5.0, z0 + 0.15),
             ((x1 - x0) / 6 - 0.08, 9.6, 0.12), jitter(C["tile"], 0.02), "Marble")
    # baignoire ilot
    bx, bz = x0 + 3.4, z1 - 3.6
    part(m, "Baignoire", (bx, y + 1.4, bz), (4.0, 2.6, 7.2), C["white"], "Marble", refl=0.18)
    part(m, "EauBaignoire", (bx, y + 2.6, bz), (3.3, 0.12, 6.4),
         C["water"], "Glass", tr=0.35, collide=False)
    part(m, "RobinetBain", (bx - 1.4, y + 3.4, bz - 2.4), (0.2, 1.5, 0.2), C["steel"], "Metal")
    # douche a l'italienne
    dx, dz = x1 - 2.8, z1 - 3.6
    part(m, "Receveur", (dx, y + 0.2, dz), (4.6, 0.3, 5.2), C["marble"], "Marble")
    for s in (-1, 1):
        part(m, f"ParoiDouche{s}", (dx + s * 2.2, y + 4.6, dz),
             (0.14, 9.0, 5.2), C["glass"], "Glass", tr=0.78, collide=False)
    part(m, "ParoiDoucheFond", (dx, y + 4.6, dz - 2.6),
         (4.5, 9.0, 0.14), C["glass"], "Glass", tr=0.78, collide=False)
    part(m, "ColonneDouche", (dx, y + 5.4, dz - 2.2), (0.35, 5.2, 0.35), C["steel"], "Metal")
    disc(m, "PommeDePluie", (dx, y + 8.0, dz - 1.2), 1.0, 0.16, C["steel"], "Metal", segments=12)
    # double vasque
    vx, vz = x0 + 2.4, z0 + 2.0
    part(m, "MeubleVasque", (vx, y + 1.6, vz), (12.0, 3.0, 2.4), C["walnut"], "Wood")
    part(m, "PlanVasque", (vx, y + 3.25, vz), (12.4, 0.3, 2.7), C["marble"], "Marble", refl=0.15)
    for s in (-1, 1):
        part(m, f"Vasque{s}", (vx + s * 3.0, y + 3.55, vz), (2.6, 0.5, 1.9), C["white"], "Marble")
        part(m, f"Robinet{s}", (vx + s * 3.0, y + 4.3, vz - 0.8), (0.2, 1.1, 0.2), C["steel"], "Metal")
        part(m, f"Miroir{s}", (vx + s * 3.0, y + 7.0, z0 + 0.28),
             (3.2, 4.2, 0.12), C["bluegrey"], "Glass", refl=0.55)
        part(m, f"CadreMiroir{s}", (vx + s * 3.0, y + 7.0, z0 + 0.2),
             (3.5, 4.5, 0.08), C["brass"], "Metal")
        glowing_bulb(m, f"Applique{s}", (vx + s * 3.0, y + 9.4, z0 + 0.45),
                     (2.2, 0.22, 0.22), C["neon"], range_=10, brightness=0.6)
    # WC
    wx, wz = x1 - 2.0, z0 + 2.2
    part(m, "WC", (wx, y + 1.0, wz), (2.2, 2.0, 2.8), C["white"], "Marble")
    part(m, "CuveWC", (wx, y + 2.2, wz), (2.1, 0.4, 2.6), tint(C["white"], 0.96), "Marble")
    part(m, "Reservoir", (wx, y + 2.6, wz - 1.2), (2.0, 2.8, 0.7), C["white"], "Marble")
    # serviettes et accessoires
    part(m, "PorteServiettes", (x0 + 0.4, y + 4.4, cz), (0.2, 0.2, 4.0), C["steel"], "Metal")
    for k in range(3):
        part(m, f"Serviette{k}", (x0 + 0.7, y + 3.7, cz - 1.2 + k * 1.1),
             (0.5, 1.5, 0.9), C["linen"] if k % 2 else C["bluegrey"], "Fabric")
    plant(m, "PlanteSDB", (x1 - 1.2, y, z0 + 1.2), 1.8)
    rug(m, "TapisDeBain", cx, cz, y + 0.12, 4.0, 2.4, C["cream"])
    return m


def office(parent, name, x, z, y, yaw=0):
    m = parent.add("Model", name)
    r = (0, yaw, 0)
    part(m, "Bureau", (x, y + 2.8, z), (8.0, 0.35, 3.6), C["walnut"], "Wood", rot=r, refl=0.12)
    for dx in (-3.4, 3.4):
        part(m, "PiedBureau", (x + dx, y + 1.4, z), (0.4, 2.8, 3.0), C["charcoal"], "Metal", rot=r)
    part(m, "Ecran", (x, y + 5.2, z - 0.9), (5.0, 3.0, 0.2), C["black"], "SmoothPlastic", rot=r)
    part(m, "EcranImage", (x, y + 5.2, z - 0.78), (4.7, 2.7, 0.05), C["screen"], "Glass", rot=r)
    part(m, "PiedEcran", (x, y + 3.5, z - 0.9), (0.5, 0.7, 0.5), C["charcoal"], "Metal", rot=r)
    part(m, "Clavier", (x, y + 3.1, z + 0.7), (2.6, 0.12, 0.9), C["charcoal"], "Metal", rot=r)
    part(m, "Souris", (x + 1.8, y + 3.1, z + 0.7), (0.35, 0.16, 0.5), C["charcoal"], "Metal", rot=r)
    part(m, "LampeBureau", (x - 3.0, y + 3.8, z - 0.6), (0.15, 2.0, 0.15), C["brass"], "Metal", rot=r)
    part(m, "AbatJourLampe", (x - 3.0, y + 4.9, z - 0.3), (1.2, 0.5, 1.2), C["charcoal"], "Metal", rot=r)
    # fauteuil de bureau
    part(m, "Fauteuil", (x, y + 1.6, z + 3.2), (2.6, 0.5, 2.6), C["charcoal"], "Fabric")
    part(m, "DossierFauteuil", (x, y + 3.1, z + 4.3), (2.6, 3.0, 0.5), C["charcoal"], "Fabric")
    part(m, "PiedFauteuil", (x, y + 0.7, z + 3.2), (0.3, 1.4, 0.3), C["steel"], "Metal")
    for k in range(5):
        a = 2 * math.pi * k / 5
        part(m, f"Roulette{k}", (x + math.cos(a) * 0.9, y + 0.15, z + 3.2 + math.sin(a) * 0.9),
             (0.3, 0.3, 0.3), C["dark"], "Metal")
    return m


def stairs(parent, name, x, z0, y, width=6.0, length=16.0, height=11.0, steps=20):
    m = parent.add("Model", name)
    run, rise = length / steps, height / steps
    for k in range(steps):
        yk = y + rise * (k + 1)
        zk = z0 + run * (k + 0.5)
        part(m, f"Marche{k:02d}", (x, yk - rise / 2, zk),
             (width, rise, run + 0.05), C["woodlight"], "Wood")
        part(m, f"Contremarche{k:02d}", (x, yk - rise - 0.15, zk - run / 2),
             (width, rise + 0.3, 0.12), C["white"], "SmoothPlastic")
        part(m, f"Nez{k:02d}", (x, yk - 0.06, zk + run / 2),
             (width, 0.1, 0.22), C["walnut"], "Wood")
    # rampes
    for s in (-1, 1):
        for k in range(steps + 1):
            zk = z0 + run * k
            yk = y + rise * k
            part(m, f"Balustre{s}_{k}", (x + s * (width / 2 - 0.15), yk + 1.6, zk),
                 (0.12, 3.2, 0.12), C["steel"], "Metal")
        for k in range(steps):
            zk = z0 + run * (k + 0.5)
            yk = y + rise * (k + 0.5) + 3.2
            part(m, f"MainCourante{s}_{k}", (x + s * (width / 2 - 0.15), yk, zk),
                 (0.24, 0.2, run * 1.02), C["walnut"], "Wood",
                 rot=(-math.degrees(math.atan2(rise, run)), 0, 0))
    return m


# ---------------------------------------------------------------------------
# Exterieur
# ---------------------------------------------------------------------------

def tree(parent, name, x, z, h=12.0, blossom=False):
    m = parent.add("Model", name)
    part(m, "Tronc", (x, h / 2, z), (1.5, h, 1.5), C["wooddark"], "Wood")
    for k, (dx, dy, dz, r) in enumerate([
        (0, 0, 0, 6.5), (-3.4, 1.2, 1.0, 4.6), (3.2, 0.4, -1.4, 4.8),
        (-1.0, 3.4, -2.6, 4.2), (2.0, 3.0, 2.8, 4.0), (0, 5.0, 0.2, 3.6),
    ]):
        ball(m, f"Feuillage{k}", (x + dx, h + dy, z + dz), r,
             C["pink"] if blossom else (C["leaf"] if k % 3 == 0 else
                                         C["leaf2"] if k % 3 == 1 else C["leaf3"]),
             "Grass")
    return m


def hedge(parent, name, x, z, length, axis="x", h=2.4):
    m = parent.add("Model", name)
    n = max(1, int(length / 2.2))
    for k in range(n):
        s = -length / 2 + length * (k + 0.5) / n
        px = x + s if axis == "x" else x
        pz = z if axis == "x" else z + s
        ball(m, f"Buis{k}", (px, h + 0.3, pz), 2.6,
             C["leaf"] if k % 2 else C["leaf2"], "Grass")
        part(m, f"Base{k}", (px, h / 2, pz), (2.3, h, 1.5), C["leaf"], "Grass")
    return m


def bollard(parent, name, x, z):
    m = parent.add("Model", name)
    part(m, "Poteau", (x, 1.1, z), (0.5, 2.2, 0.5), C["charcoal"], "Metal")
    part(m, "Tete", (x, 2.35, z), (0.8, 0.35, 0.8), C["neon"], "Neon")
    light(m, "Halo", (x, 2.4, z), C["neon"], 0.7, 11)
    return m


def lounger(parent, name, x, z, yaw=0):
    m = parent.add("Model", name)
    r = (0, yaw, 0)
    part(m, "Chassis", (x, 1.0, z), (3.0, 0.35, 7.0), C["white"], "Metal", rot=r)
    part(m, "Matelas", (x, 1.25, z - 0.4), (2.7, 0.35, 5.4), C["cream"], "Fabric", rot=r)
    part(m, "Dossier", (x, 2.2, z - 3.0), (2.7, 0.35, 3.0), C["cream"], "Fabric",
         rot=(-35, yaw, 0))
    return m


def parasol(parent, name, x, z, r=5.5):
    m = parent.add("Model", name)
    part(m, "Mat", (x, 5.0, z), (0.25, 10.0, 0.25), C["steel"], "Metal")
    disc(m, "Toile", (x, 9.6, z), r, 0.22, C["cream"], "Fabric", segments=16)
    ball(m, "Pommeau", (x, 10.2, z), 0.6, C["brass"], "Metal")
    return m


def car(parent, name, x, z, yaw=0):
    m = parent.add("Model", name)
    r = (0, yaw, 0)
    part(m, "Chassis", (x, 1.8, z), (8.0, 2.0, 17.0), C["navy"], "Metal", rot=r, refl=0.25)
    part(m, "Habitacle", (x, 3.6, z - 0.6), (7.2, 2.2, 9.0), tint(C["navy"], 1.1), "Metal", rot=r)
    part(m, "PareBrise", (x, 4.0, z + 3.4), (6.6, 1.8, 0.18), C["glass"], "Glass", tr=0.55, rot=r)
    for s in (-1, 1):
        part(m, f"VitreLaterale{s}", (x + s * 3.65, 4.0, z - 0.6),
             (0.16, 1.7, 7.6), C["glass"], "Glass", tr=0.6, rot=r)
    for dx in (-3.9, 3.9):
        for dz in (-5.6, 5.6):
            ball(m, f"Roue{dx}_{dz}", (x + dx, 1.2, z + dz), 2.6, C["black"], "SmoothPlastic")
            ball(m, f"Jante{dx}_{dz}", (x + dx * 1.02, 1.2, z + dz), 1.4, C["steel"], "Metal")
    for s in (-1, 1):
        part(m, f"Phare{s}", (x + s * 2.9, 2.0, z + 8.6), (1.5, 0.7, 0.2), C["neon"], "Neon", rot=r)
        part(m, f"Feu{s}", (x + s * 2.9, 2.0, z - 8.6), (1.5, 0.7, 0.2), C["rust"], "Neon", rot=r)
    part(m, "Calandre", (x, 1.6, z + 8.6), (4.0, 0.9, 0.2), C["charcoal"], "Metal", rot=r)
    return m


def pool(parent, name, x0, x1, z0, z1):
    m = parent.add("Model", name)
    cx, cz = (x0 + x1) / 2, (z0 + z1) / 2
    part(m, "Fond", (cx, -1.6, cz), (x1 - x0 + 2, 0.5, z1 - z0 + 2),
         C["bluegrey"], "Marble")
    for s in (-1, 1):
        part(m, f"ParoiX{s}", (cx + s * (x1 - x0) / 2, -0.6, cz),
             (0.7, 3.2, z1 - z0 + 2), C["tile"], "Marble")
        part(m, f"ParoiZ{s}", (cx, -0.6, cz + s * (z1 - z0) / 2),
             (x1 - x0 + 2, 3.2, 0.7), C["tile"], "Marble")
    part(m, "Eau", (cx, 0.15, cz), (x1 - x0 - 0.2, 0.3, z1 - z0 - 0.2),
         C["water"], "Glass", tr=0.32, collide=False)
    part(m, "LigneEau", (cx, 0.35, cz), (x1 - x0 - 0.4, 0.06, z1 - z0 - 0.4),
         C["water"], "Neon", tr=0.7, collide=False)
    # margelles
    for k in range(int((x1 - x0) / 2)):
        xx = x0 + 1 + k * 2
        for s in (-1, 1):
            part(m, f"Margelle{k}_{s}", (xx, 0.35, cz + s * ((z1 - z0) / 2 + 1.2)),
                 (1.9, 0.25, 2.2), jitter(C["stone"], 0.03), "Sandstone")
    # echelle
    for s in (-1, 1):
        part(m, f"Barre{s}", (cx + s * 1.2, 1.2, z1 - 0.6), (0.18, 2.6, 0.18), C["steel"], "Metal")
    for k in range(4):
        part(m, f"Echelon{k}", (cx, -0.4 + k * 0.7, z1 - 0.6), (2.6, 0.14, 0.14), C["steel"], "Metal")
    return m


def fence(parent, name, x0, x1, z0, z1):
    m = parent.add("Model", name)
    for side, a, b, fixed, axis in (
        ("Nord", x0, x1, z0, "x"), ("Sud", x0, x1, z1, "x"),
        ("Ouest", z0, z1, x0, "z"), ("Est", z0, z1, x1, "z"),
    ):
        n = max(1, int((b - a) / 6))
        for k in range(n + 1):
            s = a + (b - a) * k / n
            px, pz = (s, fixed) if axis == "x" else (fixed, s)
            part(m, f"Poteau{side}{k}", (px, 2.6, pz), (0.6, 5.2, 0.6),
                 C["charcoal"], "Metal", tag="FENCE")
        for k in range(n):
            s = a + (b - a) * (k + 0.5) / n
            px, pz = (s, fixed) if axis == "x" else (fixed, s)
            for j in range(4):
                part(m, f"Lame{side}{k}_{j}", (px, 1.2 + j * 0.95, pz),
                     ((b - a) / n - 0.1, 0.42, 0.16) if axis == "x"
                     else (0.16, 0.42, (b - a) / n - 0.1),
                     C["wooddark"], "Wood", tag="FENCE")
    return m
