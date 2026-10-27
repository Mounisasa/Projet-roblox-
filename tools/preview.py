#!/usr/bin/env python3
"""Rendu d'apercu (isometrique) de MaisonRealiste.rbxlx.

Deux vues : exterieure et coupe de l'interieur.
    python3 tools/preview.py
"""

from __future__ import annotations

import json
import math
import os
import sys

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from rbxlx import euler  # noqa: E402

BOXES = json.load(open(os.path.join(HERE, "boxes.json"), encoding="utf-8"))
OUT = os.path.join(ROOT, "apercu.png")

PANEL_W, PANEL_H = 1240, 860
COS, SIN = math.cos(math.radians(30)), math.sin(math.radians(30))
VIEW = (0.62, 0.52, 0.62)          # direction de la camera (normalisee plus bas)
LIGHT = (-0.35, 0.88, 0.32)

HIDE_CUT = {"EXT", "WIN", "GLASS", "CURTAIN", "ROOF", "CEIL",
            "SLAB", "PARTITION"}
FOCUS_SKIP = {"GROUND", "FENCE"}

FACES = [
    (0, 1, 3, 2), (4, 5, 7, 6),      # x-, x+
    (0, 1, 5, 4), (2, 3, 7, 6),      # y-, y+
    (0, 2, 6, 4), (1, 3, 7, 5),      # z-, z+
]


def norm(v):
    n = math.sqrt(sum(c * c for c in v))
    return tuple(c / n for c in v) if n else (0, 1, 0)


VIEW = norm(VIEW)
LIGHT = norm(LIGHT)


def dot(a, b):
    return sum(x * y for x, y in zip(a, b))


def apply(m, v):
    return (
        m[0] * v[0] + m[1] * v[1] + m[2] * v[2],
        m[3] * v[0] + m[4] * v[1] + m[5] * v[2],
        m[6] * v[0] + m[7] * v[1] + m[8] * v[2],
    )


def project(p):
    x, y, z = p
    return ((x - z) * COS, (x + z) * 0.44 - y * 1.20, x + z + y * 1.6)


def shade(color, k):
    return tuple(max(0, min(255, int(round(c * 255 * k)))) for c in color)


def collect(cutaway: bool, flip: bool = False):
    ops = []
    all_pts = []
    focus_pts = []
    for b in BOXES:
        if b["tr"] >= 0.58:
            continue
        if cutaway and b["tag"] in HIDE_CUT:
            continue
        pos = b["pos"]
        sx, sy, sz = b["size"]
        m = euler(*b["rot"])
        local = []
        for ix in (-1, 1):
            for iy in (-1, 1):
                for iz in (-1, 1):
                    local.append((ix * sx / 2, iy * sy / 2, iz * sz / 2))
        world = [tuple(pos[i] + apply(m, l)[i] for i in range(3)) for l in local]
        if flip:
            world = [(-p[0], p[1], -p[2]) for p in world]
        projected = [project(p) for p in world]
        all_pts.extend(projected)
        if (b["tag"] not in FOCUS_SKIP and abs(pos[0]) < 42 and abs(pos[2]) < 54):
            focus_pts.extend(projected)

        if b["shape"] == "Ball":
            c = project((-pos[0], pos[1], -pos[2]) if flip else tuple(pos))
            d = (sx + sy + sz) / 3
            k = 0.55 + 0.45 * max(0, dot(norm((0.3, 1.0, 0.4)), LIGHT))
            ops.append((c[2] + d * 0.2, "ball", c, d, shade(b["color"], k),
                        shade(b["color"], min(1, k + 0.25))))
            continue

        for f in FACES:
            pts = [world[i] for i in f]
            center = tuple(sum(p[j] for p in pts) / 4 for j in range(3))
            pc = (-pos[0], pos[1], -pos[2]) if flip else pos
            n = norm(tuple(center[j] - pc[j] for j in range(3)))
            if dot(n, VIEW) <= 0.02:
                continue
            k = 0.40 + 0.66 * max(0.0, dot(n, LIGHT))
            if b["tag"] == "LIGHT":
                k = min(1.35, k + 0.45)
            depth = sum(projected[i][2] for i in f) / 4
            ops.append((depth, "face", [projected[i] for i in f],
                        shade(b["color"], k), b))
    return ops, (focus_pts or all_pts)


def draw_panel(ops, all_pts, bounds, title, subtitle):
    img = Image.new("RGB", (PANEL_W, PANEL_H))
    px = img.load()
    # ciel + sol en degrade
    for y in range(PANEL_H):
        t = y / PANEL_H
        if t < 0.62:
            u = t / 0.62
            col = (int(38 + 92 * u), int(58 + 88 * u), int(86 + 62 * u))
        else:
            u = (t - 0.62) / 0.38
            col = (int(130 - 38 * u), int(146 - 42 * u), int(148 - 52 * u))
        for x in range(PANEL_W):
            px[x, y] = col
    draw = ImageDraw.Draw(img)

    minx, maxx, miny, maxy = bounds
    scale = min((PANEL_W - 90) / (maxx - minx), (PANEL_H - 150) / (maxy - miny))
    ox = PANEL_W / 2 - (minx + maxx) / 2 * scale
    oy = PANEL_H / 2 + 30 - (miny + maxy) / 2 * scale

    def scr(p):
        return (p[0] * scale + ox, p[1] * scale + oy)

    ops.sort(key=lambda o: o[0])
    for op in ops:
        if op[1] == "ball":
            _, _, c, d, col, hi = op
            x, y = scr(c)
            r = max(1.0, d * scale / 2)
            draw.ellipse((x - r, y - r, x + r, y + r), fill=col)
            draw.ellipse((x - r * 0.55, y - r * 0.6, x - r * 0.05, y - r * 0.1),
                         fill=hi)
        else:
            _, _, pts, col, b = op
            poly = [scr(p) for p in pts]
            # aire approximee pour eviter de dessiner les micro-polygones
            area = abs(sum(poly[i][0] * poly[(i + 1) % 4][1] -
                           poly[(i + 1) % 4][0] * poly[i][1]
                           for i in range(4))) / 2
            if area < 0.7:
                continue
            draw.polygon(poly, fill=col)
            if area > 26:
                draw.line(poly + [poly[0]],
                          fill=tuple(max(0, int(c * 0.68)) for c in col), width=1)

    # titre
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 25)
        small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 15)
    except OSError:
        font = small = ImageFont.load_default()
    draw.rounded_rectangle((22, 20, 22 + 640, 94), radius=12,
                           fill=(16, 20, 28), outline=(190, 165, 115), width=2)
    draw.text((40, 30), title, fill=(245, 235, 214), font=font)
    draw.text((40, 66), subtitle, fill=(186, 181, 170), font=small)
    return img


def main():
    ext_ops, ext_pts = collect(False)
    cut_ops, _ = collect(True)
    minx = min(p[0] for p in ext_pts)
    maxx = max(p[0] for p in ext_pts)
    miny = min(p[1] for p in ext_pts)
    maxy = max(p[1] for p in ext_pts)
    bounds = (minx, maxx, miny, maxy)

    a = draw_panel(ext_ops, ext_pts, bounds, "MAISON REALISTE  ·  VUE EXTERIEURE",
                   f"{len(BOXES):,} pieces  |  villa 2 niveaux, piscine, garage, jardin")
    b = draw_panel(cut_ops, ext_pts, bounds, "COUPE  ·  INTERIEUR COMPLET",
                   "salon, cuisine, salle a manger, 2 chambres, SDB, bureau, escalier")

    out = Image.new("RGB", (PANEL_W * 2 + 16, PANEL_H), (18, 22, 30))
    out.paste(a, (0, 0))
    out.paste(b, (PANEL_W + 16, 0))
    d = ImageDraw.Draw(out)
    d.rectangle((PANEL_W + 4, 0, PANEL_W + 12, PANEL_H), fill=(18, 22, 30))
    out.save(OUT, optimize=True)

    # troisieme image : vue depuis le fond du jardin (piscine / terrasse)
    back_ops, back_pts = collect(False, flip=True)
    bminx = min(p[0] for p in back_pts); bmaxx = max(p[0] for p in back_pts)
    bminy = min(p[1] for p in back_pts); bmaxy = max(p[1] for p in back_pts)
    c = draw_panel(back_ops, back_pts, (bminx, bmaxx, bminy, bmaxy),
                   "FACE ARRIERE  ·  PISCINE & TERRASSE",
                   "platelage bois, bassin, transats, parasols, cuisine d'ete, eclairages")
    OUT2 = os.path.join(ROOT, "apercu_piscine.png")
    c.save(OUT2, optimize=True)
    print(f"OK -> {os.path.basename(OUT)} ({out.width}x{out.height})")
    print(f"OK -> {os.path.basename(OUT2)} ({c.width}x{c.height})")


if __name__ == "__main__":
    main()
