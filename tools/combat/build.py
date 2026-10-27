#!/usr/bin/env python3
"""Genere SabreLaser_Combat.rbxlx — place Roblox complete, autonome, valide.

    python3 tools/combat/build.py

Toutes les valeurs (enums, noms de proprietes, types XML) sont verifiees
contre le dump API Roblox officiel (Roblox-Client-Tracker/API-Dump.json)
et la specification RobloxAPI/spec/formats/rbxlx.md.
"""

from __future__ import annotations

import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.dirname(HERE)
ROOT = os.path.dirname(TOOLS)
sys.path.insert(0, TOOLS)
sys.path.insert(0, HERE)

from rbxlx import Node, write_place, euler, num, packed, MATERIAL  # noqa: E402
import lua_sources as L  # noqa: E402

OUT = os.path.join(ROOT, "SabreLaser_Combat.rbxlx")

# --- enums verifies dans le dump API ---------------------------------------
MAT = {
    "Plastic": MATERIAL["Plastic"], "SmoothPlastic": MATERIAL["SmoothPlastic"],
    "Neon": MATERIAL["Neon"], "Metal": MATERIAL["Metal"],
    "DiamondPlate": MATERIAL["DiamondPlate"], "Slate": MATERIAL["Slate"],
    "Marble": MATERIAL["Marble"], "Grass": MATERIAL["Grass"],
}
SHAPE = {"Ball": 0, "Block": 1, "Cylinder": 2}
FONT = {"SourceSans": 3, "SourceSansBold": 4, "GothamBold": 19, "GothamBlack": 20}
ALIGN_X = {"Left": 0, "Right": 1, "Center": 2}
ALIGN_Y = {"Top": 0, "Center": 1, "Bottom": 2}
NORMAL = {
    "Plastic": (0.85, 0.86, 0.88), "Steel": (0.42, 0.46, 0.52),
    "Dark": (0.10, 0.12, 0.15), "White": (0.98, 0.99, 1.0),
    "Blue": (0.25, 0.55, 1.0), "Red": (0.95, 0.20, 0.20),
    "Gold": (0.95, 0.76, 0.30), "Cyan": (0.35, 0.85, 1.0),
}

PALETTE = [
    (255, 55, 55), (64, 140, 255), (74, 255, 128), (178, 76, 255),
    (255, 176, 48), (64, 238, 255), (255, 110, 196), (238, 244, 255),
]
SOUNDS = {
    "Hum": "rbxasset://sounds/action_falling.ogg",
    "Ignite": "rbxasset://sounds/action_jump.mp3",
    "Swing": "rbxasset://sounds/action_get_up.mp3",
    "Clash": "rbxasset://sounds/impact_water.mp3",
    "Draw": "rbxasset://sounds/action_jump_land.mp3",
}


# ---------------------------------------------------------------------------
# Helpers de base
# ---------------------------------------------------------------------------
def c3(n, name, rgb):
    return n.c3(name, rgb)


def part(parent, name, pos, size, color, mat="Plastic", shape="Block",
         rot=(0, 0, 0), anchored=True, collide=False, cast=False,
         tr=0.0, refl=0.0, locked=False, massless=True):
    n = parent.add("Part", name)
    n.b("Anchored", anchored).b("CanCollide", collide).b("CastShadow", cast)
    n.b("Locked", locked).b("Massless", massless)
    n.v3("Size", size)
    n.cf("CFrame", pos, rot)
    n.p("Color3uint8", "Color3uint8", str(packed(color)))
    n.tok("Material", MAT.get(mat, MATERIAL["Plastic"]))
    if shape != "Block":
        n.tok("Shape", SHAPE[shape])
    if tr:
        n.f("Transparency", tr)
    if refl:
        n.f("Reflectance", refl)
    n.tok("TopSurface", 0).tok("BottomSurface", 0)
    return n


def script(parent, cls, name, source):
    n = parent.add(cls, name)
    n.ps("Source", source)
    return n


def folder(parent, name, cls="Folder"):
    return parent.add(cls, name)


def ud2(n, name, xs, xo, ys, yo):
    return n.udim2(name, xs, xo, ys, yo)


def vec2(n, name, x, y):
    return n.p("Vector2", name, children=[("X", num(x)), ("Y", num(y))])


def udim(n, name, s, o):
    return n.p("UDim", name, children=[("S", num(s)), ("O", num(o))])


def cseq(n, name, text):
    return n.p("ColorSequence", name, text)


def nseq(n, name, text):
    return n.p("NumberSequence", name, text)


def corner(parent, radius=12):
    c = parent.add("UICorner", "UICorner")
    udim(c, "CornerRadius", 0, radius)
    return c


def stroke(parent, color, thickness=2, transparency=0.35):
    s = parent.add("UIStroke", "UIStroke")
    c3(s, "Color", color)
    s.f("Thickness", thickness).f("Transparency", transparency)
    s.b("Enabled", True)
    return s


def base_gui(n, pos, size, anchor=(0, 0), z=1, visible=True):
    ud2(n, "Position", pos[0], pos[1], pos[2], pos[3])
    ud2(n, "Size", size[0], size[1], size[2], size[3])
    vec2(n, "AnchorPoint", anchor[0], anchor[1])
    n.i("ZIndex", z).b("Visible", visible)
    n.b("Active", True).b("Interactable", True)
    return n


def frame(parent, name, pos, size, color=(0.06, 0.08, 0.11), tr=0.0,
          anchor=(0, 0), z=1, visible=True, clips=False):
    n = parent.add("Frame", name)
    base_gui(n, pos, size, anchor, z, visible)
    c3(n, "BackgroundColor3", color)
    n.f("BackgroundTransparency", tr)
    n.i("BorderSizePixel", 0)
    n.b("ClipsDescendants", clips)
    return n


def label(parent, name, pos, size, text, color=(0.90, 0.94, 1.0),
          size_txt=16, font="SourceSansBold", ax="Center", ay="Center",
          anchor=(0, 0), z=2, tr=1.0, visible=True, scaled=False):
    n = parent.add("TextLabel", name)
    base_gui(n, pos, size, anchor, z, visible)
    c3(n, "BackgroundColor3", (0.06, 0.08, 0.11))
    n.f("BackgroundTransparency", tr)
    n.i("BorderSizePixel", 0)
    n.s("Text", text)
    c3(n, "TextColor3", color)
    n.f("TextSize", size_txt)
    n.tok("Font", FONT[font])
    n.tok("TextXAlignment", ALIGN_X[ax]).tok("TextYAlignment", ALIGN_Y[ay])
    n.b("TextScaled", scaled).b("TextWrapped", True).b("RichText", True)
    n.f("TextTransparency", 0).f("TextStrokeTransparency", 1)
    return n


def button(parent, name, pos, size, text, color=(0.10, 0.30, 0.55),
           txt_color=(1, 1, 1), size_txt=18, font="GothamBold",
           anchor=(0, 0), z=3):
    n = parent.add("TextButton", name)
    base_gui(n, pos, size, anchor, z, True)
    c3(n, "BackgroundColor3", color)
    n.f("BackgroundTransparency", 0)
    n.i("BorderSizePixel", 0)
    n.s("Text", text)
    c3(n, "TextColor3", txt_color)
    n.f("TextSize", size_txt)
    n.tok("Font", FONT[font])
    n.tok("TextXAlignment", ALIGN_X["Center"]).tok("TextYAlignment", ALIGN_Y["Center"])
    n.b("TextScaled", True).b("TextWrapped", True).b("RichText", True)
    n.b("AutoButtonColor", True).b("Modal", False).b("Selected", False)
    return n


def textbox(parent, name, pos, size, text="", placeholder="0-255", z=3):
    n = parent.add("TextBox", name)
    base_gui(n, pos, size, (0, 0), z, True)
    c3(n, "BackgroundColor3", (0.10, 0.13, 0.18))
    n.f("BackgroundTransparency", 0.1)
    n.i("BorderSizePixel", 0)
    n.s("Text", text)
    n.s("PlaceholderText", placeholder)
    c3(n, "TextColor3", (0.95, 0.97, 1.0))
    c3(n, "PlaceholderColor3", (0.45, 0.50, 0.60))
    n.f("TextSize", 17)
    n.tok("Font", FONT["SourceSansBold"])
    n.tok("TextXAlignment", ALIGN_X["Center"]).tok("TextYAlignment", ALIGN_Y["Center"])
    n.b("TextScaled", True).b("ClearTextOnFocus", False)
    n.b("TextEditable", True).b("MultiLine", False).b("RichText", False)
    return n


def screen_gui(parent, name, order, enabled=True):
    n = parent.add("ScreenGui", name)
    n.b("Enabled", enabled).b("ResetOnSpawn", False)
    n.i("DisplayOrder", order)
    n.b("IgnoreGuiInset", True).b("ClipToDeviceSafeArea", False)
    n.tok("ZIndexBehavior", 1)   # Sibling
    return n


def look_at(eye, target):
    """Retourne les 9 composantes R00..R22 d'un CFrame.new(eye, target)."""
    z = [eye[i] - target[i] for i in range(3)]
    ln = math.sqrt(sum(v * v for v in z))
    z = [v / ln for v in z]
    up = (0.0, 1.0, 0.0)
    x = [up[1] * z[2] - up[2] * z[1],
         up[2] * z[0] - up[0] * z[2],
         up[0] * z[1] - up[1] * z[0]]
    ln = math.sqrt(sum(v * v for v in x))
    x = [v / ln for v in x]
    y = [z[1] * x[2] - z[2] * x[1],
         z[2] * x[0] - z[0] * x[2],
         z[0] * x[1] - z[1] * x[0]]
    return [x[0], y[0], z[0], x[1], y[1], z[1], x[2], y[2], z[2]]


# ---------------------------------------------------------------------------
# Tables d'animations (KeyframeSequences instanciees dans le XML)
# ---------------------------------------------------------------------------
ATTACK_JOINTS = [
    "RootJoint", "Waist", "Neck", "RightShoulder", "RightElbow", "RightWrist",
    "LeftShoulder", "LeftElbow", "RightHip", "LeftHip",
]
DEFLECT_JOINTS = [
    "RootJoint", "Waist", "Neck", "RightShoulder", "RightElbow", "RightWrist",
    "LeftShoulder", "LeftElbow",
]


def pose(kf, name, rx=0.0, ry=0.0, rz=0.0, px=0.0, py=0.0, pz=0.0):
    p = kf.add("Pose", name)
    p.cf("CFrame", (px, py, pz), (rx, ry, rz))
    p.f("MaskWeight", 1)
    return p


def animation_tables(parent):
    times = [0.00, 0.13, 0.28, 0.38, 0.46]
    dtimes = [0.00, 0.10, 0.22, 0.32, 0.40]
    for kind, joints, tlist in (("Attack", ATTACK_JOINTS, times),
                                ("Deflect", DEFLECT_JOINTS, dtimes)):
        for i in range(1, 11):
            phi = (i - 1) * (math.pi * 2 / 10)
            sn, cs = math.sin(phi), math.cos(phi)
            seq = parent.add("KeyframeSequence", f"{kind}_{i}")
            seq.b("Loop", False)
            seq.tok("Priority", 2)          # AnimationPriority.Action
            seq.f("AuthoredHipHeight", 2.0)
            for k, t in enumerate(tlist):
                kf = seq.add("Keyframe", f"Key{k}")
                kf.f("Time", t)
                if k == 0 or k == len(tlist) - 1:
                    for j in joints:
                        pose(kf, j)
                    continue
                if kind == "Attack":
                    if k == 1:
                        ang = {
                            "RootJoint": (0, -8 * sn, 0),
                            "Waist": (0, -22 * sn, 0),
                            "Neck": (0, 6 * cs, 0),
                            "RightShoulder": (-58 + 12 * cs, 16 * sn, -24 * cs),
                            "RightElbow": (0, 0, -38 - 8 * sn),
                            "RightWrist": (0, 0, -12 * cs),
                            "LeftShoulder": (14 * cs, 0, 22),
                            "LeftElbow": (0, 0, 18),
                            "RightHip": (0, 0, 0), "LeftHip": (0, 0, 0),
                        }
                    elif k == 2:
                        ang = {
                            "RootJoint": (0, 10 * sn, 0),
                            "Waist": (0, 26 * sn, 0),
                            "Neck": (0, -7 * cs, 0),
                            "RightShoulder": (82 if i % 2 == 0 else 68, -20 * cs, 30 * sn),
                            "RightElbow": (0, 0, 14 + 8 * cs),
                            "RightWrist": (0, 0, 16 * sn),
                            "LeftShoulder": (-10 * sn, 0, -20),
                            "LeftElbow": (0, 0, -14),
                            "RightHip": (8 * cs, 0, 0), "LeftHip": (-8 * cs, 0, 0),
                        }
                    else:
                        ang = {
                            "RootJoint": (0, 0, 0),
                            "Waist": (0, 10 * sn, 0),
                            "Neck": (0, 0, 0),
                            "RightShoulder": (38, -8 * cs, 14 * sn),
                            "RightElbow": (0, 0, 8),
                            "RightWrist": (0, 0, 0),
                            "LeftShoulder": (0, 0, -8),
                            "LeftElbow": (0, 0, 0),
                            "RightHip": (0, 0, 0), "LeftHip": (0, 0, 0),
                        }
                else:
                    if k == 1:
                        ang = {
                            "RootJoint": (0, 12 * cs, 0),
                            "Waist": (0, 18 * sn, 0),
                            "Neck": (0, 8 * sn, 0),
                            "RightShoulder": (-30, 12 * cs, 34 * sn),
                            "RightElbow": (0, 0, -46),
                            "RightWrist": (0, 0, -18),
                            "LeftShoulder": (-18, -8 * cs, -20 * sn),
                            "LeftElbow": (0, 0, -26),
                        }
                    elif k == 2:
                        ang = {
                            "RootJoint": (0, 0, 0),
                            "Waist": (0, -14 * sn, 0),
                            "Neck": (0, -8 * cs, 0),
                            "RightShoulder": (-52, -18 * cs, -18 * sn),
                            "RightElbow": (0, 0, -22),
                            "RightWrist": (0, 0, 12 * cs),
                            "LeftShoulder": (-26, 10 * sn, 28 * cs),
                            "LeftElbow": (0, 0, -30),
                        }
                    else:
                        ang = {
                            "RootJoint": (0, 0, 0),
                            "Waist": (0, 6 * sn, 0),
                            "Neck": (0, 0, 0),
                            "RightShoulder": (-14, 0, 0),
                            "RightElbow": (0, 0, -12),
                            "RightWrist": (0, 0, 0),
                            "LeftShoulder": (0, 0, 0),
                            "LeftElbow": (0, 0, 0),
                        }
                for j in joints:
                    rx, ry, rz = ang.get(j, (0, 0, 0))
                    pose(kf, j, rx, ry, rz)
    return parent


# ---------------------------------------------------------------------------
# SabreTemplate (modele physique complet)
# ---------------------------------------------------------------------------
BLADE_ROT = (0, 0, 90)   # axe X du cylindre -> axe Y vertical


def build_saber_template(assets, sound_group):
    model = assets.add("Model", "SaberTemplate")

    # --- pieces de la poignee (Parts geometriques usinees) ---
    handle = part(model, "Handle", (0, 0, 0), (0.34, 1.70, 0.34),
                  NORMAL["Steel"], "Metal")
    model.refprop("PrimaryPart", handle)

    grip = part(model, "Grip", (0, -0.10, 0), (0.38, 0.95, 0.38),
                NORMAL["Dark"], "DiamondPlate", refl=0.15)
    pommel = part(model, "Pommel", (0, -0.92, 0), (0.40, 0.22, 0.40),
                  NORMAL["Steel"], "Metal", refl=0.35)
    emitter = part(model, "EmitterHousing", (0, 0.95, 0), (0.40, 0.30, 0.40),
                   NORMAL["Steel"], "Metal", refl=0.30)
    ring = part(model, "EmitterRing", (0, 1.12, 0), (0.42, 0.08, 0.42),
                NORMAL["Blue"], "Neon")
    guard = part(model, "GuardRing", (0, 1.20, 0), (0.56, 0.12, 0.56),
                 NORMAL["Dark"], "DiamondPlate", refl=0.20)
    switch = part(model, "SwitchBox", (0.20, 0.35, 0), (0.16, 0.34, 0.22),
                  NORMAL["Dark"], "Metal")
    switch_led = part(model, "SwitchLED", (0.29, 0.35, 0), (0.08, 0.16, 0.14),
                      NORMAL["Red"], "Neon")

    # --- lame : noyau blanc + gaine coloree + pointe ---
    core = part(model, "BladeCore", (0, 3.55, 0), (4.60, 0.16, 0.16),
                (1.0, 1.0, 1.0), "Neon", shape="Cylinder", rot=BLADE_ROT)
    glow = part(model, "BladeGlow", (0, 3.55, 0), (4.58, 0.34, 0.34),
                NORMAL["Blue"], "Neon", shape="Cylinder", rot=BLADE_ROT, tr=0.55)
    tip = part(model, "BladeTip", (0, 5.88, 0), (0.34, 0.34, 0.34),
               NORMAL["Blue"], "Neon", shape="Ball")

    # --- Motor6D : joints physiques reassignes dynamiquement ---
    offsets = {
        "Grip": ((0, -0.10, 0), (0, 0, 0)),
        "Pommel": ((0, -0.92, 0), (0, 0, 0)),
        "EmitterHousing": ((0, 0.95, 0), (0, 0, 0)),
        "EmitterRing": ((0, 1.12, 0), (0, 0, 0)),
        "GuardRing": ((0, 1.20, 0), (0, 0, 0)),
        "SwitchBox": ((0.20, 0.35, 0), (0, 0, 0)),
        "SwitchLED": ((0.29, 0.35, 0), (0, 0, 0)),
        "BladeCore": ((0, 3.55, 0), BLADE_ROT),
        "BladeGlow": ((0, 3.55, 0), BLADE_ROT),
        "BladeTip": ((0, 5.88, 0), (0, 0, 0)),
    }
    parts = {
        "Grip": grip, "Pommel": pommel, "EmitterHousing": emitter,
        "EmitterRing": ring, "GuardRing": guard, "SwitchBox": switch,
        "SwitchLED": switch_led, "BladeCore": core,
        "BladeGlow": glow, "BladeTip": tip,
    }
    for name, (pos, rot) in offsets.items():
        m = handle.add("Motor6D", f"Joint_{name}")
        m.refprop("Part0", handle)
        m.refprop("Part1", parts[name])
        m.cf("C0", pos, rot)
        m.cf("C1", (0, 0, 0))
        m.b("Enabled", True)

    sabermotor = model.add("Motor6D", "SaberMotor")
    sabermotor.cf("C0", (0.62, -0.35, 0.18), (0, 0, 18))
    sabermotor.cf("C1", (0, 0, 0))
    sabermotor.b("Enabled", True)

    # --- Attachements pour la trainee haute fidelite ---
    a0 = core.add("Attachment", "Attach0")
    a0.v3("Position", (-2.30, 0, 0))
    a0.v3("Orientation", (0, 0, 0))
    a0.b("Visible", False)
    a1 = core.add("Attachment", "Attach1")
    a1.v3("Position", (2.30, 0, 0))
    a1.v3("Orientation", (0, 0, 0))
    a1.b("Visible", False)

    trail = core.add("Trail", "BladeTrail")
    trail.refprop("Attachment0", a0)
    trail.refprop("Attachment1", a1)
    cseq(trail, "Color", "0 0.25 0.55 1 0 1 0.25 0.55 1 0 ")
    nseq(trail, "Transparency", "0 0 0 1 1 0 ")
    nseq(trail, "WidthScale", "0 1 0 1 0.2 0 ")
    trail.f("Lifetime", 0.18).f("MinLength", 0.05).f("MaxLength", 0)
    trail.f("LightEmission", 1).f("LightInfluence", 0).f("Brightness", 2)
    trail.b("FaceCamera", True).b("Enabled", False)
    trail.content("Texture", None)

    light = core.add("PointLight", "BladeLight")
    c3(light, "Color", NORMAL["Blue"])
    light.f("Brightness", 2.4).f("Range", 14)
    light.b("Enabled", False).b("Shadows", False)

    # --- Sons (effets de bourdonnement inclus) ---
    for name, sid in SOUNDS.items():
        snd = emitter.add("Sound", name)
        snd.content("SoundId", sid)
        snd.refprop("SoundGroup", sound_group)
        snd.f("Volume", 0.55 if name == "Hum" else 0.8)
        snd.f("PlaybackSpeed", 1.35 if name == "Hum" else 1.0)
        snd.f("RollOffMaxDistance", 60).f("RollOffMinDistance", 4)
        snd.f("EmitterSize", 3)
        snd.b("Looped", name == "Hum").b("PlayOnRemove", False)
        if name == "Hum":
            tr = snd.add("TremoloSoundEffect", "BuzzTremolo")
            tr.b("Enabled", True).i("Priority", 0)
            tr.f("Depth", 0.9).f("Duty", 0.5).f("Frequency", 14)
            di = snd.add("DistortionSoundEffect", "BuzzDrive")
            di.b("Enabled", True).i("Priority", 1)
            di.f("Level", 0.35)
            eq = snd.add("EqualizerSoundEffect", "BuzzEQ")
            eq.b("Enabled", True).i("Priority", 2)
            eq.f("LowGain", -6).f("MidGain", 5).f("HighGain", -3)

    return model


# ---------------------------------------------------------------------------
# Interfaces utilisateur
# ---------------------------------------------------------------------------
def build_main_menu(starter_gui):
    menu = screen_gui(starter_gui, "MainMenu", 20)

    frame(menu, "Shade", (0, 0, 0, 0), (1, 0, 1, 0),
          color=(0.02, 0.03, 0.05), tr=0.55, z=1)

    panel = frame(menu, "Panel", (0.5, 0, 0.5, 0), (0, 590, 0, 500),
                  color=(0.055, 0.075, 0.105), tr=0.04,
                  anchor=(0.5, 0.5), z=2, clips=True)
    corner(panel, 18)
    stroke(panel, (0.20, 0.55, 0.95), 2, 0.45)

    frame(panel, "Accent", (0, 0, 0, 0), (1, 0, 0, 4),
          color=(0.20, 0.60, 1.0), tr=0.0, z=3)

    label(panel, "Title", (0, 0, 0, 16), (1, 0, 0, 62),
          "SABRE  DE  LUMIERE", (0.92, 0.97, 1.0), 34, "GothamBlack", z=4)
    label(panel, "Subtitle", (0, 0, 0, 80), (1, 0, 0, 28),
          "ARENE DE COMBAT   |   R15 BLOCKY   |   CLAVIER + SOURIS",
          (0.45, 0.68, 0.92), 14, "SourceSansBold", z=4)
    frame(panel, "Separator", (0, 30, 0, 116), (1, -60, 0, 2),
          color=(0.22, 0.34, 0.48), tr=0, z=4)
    label(panel, "ColorLabel", (0, 30, 0, 126), (1, -60, 0, 28),
          "COULEUR DE LA LAME", (0.80, 0.86, 0.95), 16,
          "GothamBold", ax="Left", z=4)

    preview = frame(panel, "Preview", (0.5, 0, 0, 160), (0, 200, 0, 42),
                    color=NORMAL["Blue"], tr=0, anchor=(0.5, 0), z=4)
    corner(preview, 10)
    stroke(preview, (0.85, 0.92, 1.0), 2, 0.55)

    palette = frame(panel, "Palette", (0, 30, 0, 216), (1, -60, 0, 62),
                    color=(0, 0, 0), tr=1, z=4)
    for i, (r, g, b) in enumerate(PALETTE):
        x = 8 + i * 65
        btn = button(palette, f"P{i+1}", (0, x, 0, 2), (0, 56, 0, 56),
                     "", (r / 255, g / 255, b / 255), (1, 1, 1), 14,
                     "SourceSans", z=5)
        corner(btn, 10)
        stroke(btn, (0.10, 0.12, 0.16), 2, 0.25)

    rgbrow = frame(panel, "RGBRow", (0, 30, 0, 290), (1, -60, 0, 50),
                   color=(0, 0, 0), tr=1, z=4)
    for idx, (ch, default) in enumerate((("R", "64"), ("G", "140"), ("B", "255"))):
        x = 8 + idx * 172
        label(rgbrow, f"{ch}Label", (0, x, 0, 8), (0, 30, 0, 34),
              ch, (0.55, 0.70, 0.90), 18, "GothamBold", z=5)
        box = textbox(rgbrow, f"{ch}Box", (0, x + 36, 0, 8),
                      (0, 120, 0, 34), default, "0-255", z=5)
        corner(box, 8)
    label(rgbrow, "RGBHint", (0, 8, 0, 44), (1, -16, 0, 6),
          "Saisie RVB libre ou palette", (0.40, 0.50, 0.62), 10,
          "SourceSans", ax="Right", z=5, tr=1)

    deploy = button(panel, "DeployButton", (0.5, 0, 0, 356), (0, 320, 0, 60),
                    "DEPLOYER", (0.10, 0.42, 0.85), (1, 1, 1), 26,
                    "GothamBlack", anchor=(0.5, 0), z=5)
    corner(deploy, 12)
    stroke(deploy, (0.55, 0.80, 1.0), 2, 0.35)

    label(panel, "Status", (0, 30, 0, 424), (1, -60, 0, 24),
          "", (0.60, 0.85, 0.98), 14, "SourceSansBold", z=5, tr=1)
    label(panel, "Hint", (0, 30, 0, 452), (1, -60, 0, 40),
          "Q degainer   |   E allumer   |   Clic gauche attaque   |   Clic droit garde",
          (0.46, 0.56, 0.68), 12, "SourceSans", z=5, tr=1)

    script(menu, "LocalScript", "MenuController", L.MENU_CONTROLLER)
    return menu


def build_hud(starter_gui):
    hud = screen_gui(starter_gui, "CombatHUD", 10)

    stam = frame(hud, "StaminaFrame", (0, 24, 1, -126), (0, 360, 0, 82),
                 color=(0.04, 0.06, 0.09), tr=0.30, z=2, clips=True)
    corner(stam, 12)
    stroke(stam, (0.20, 0.50, 0.75), 2, 0.55)
    label(stam, "StaminaLabel", (0, 14, 0, 8), (1, -28, 0, 26),
          "ENDURANCE   100 / 100", (0.88, 0.94, 1.0), 15,
          "GothamBold", ax="Left", z=3, tr=1)
    bar = frame(stam, "BarBack", (0, 14, 0, 42), (1, -28, 0, 26),
                color=(0.10, 0.13, 0.18), tr=0, z=3, clips=True)
    corner(bar, 8)
    fill = frame(bar, "BarFill", (0, 0, 0, 0), (1, 0, 1, 0),
                 color=(0.35, 0.86, 0.65), tr=0, z=4)
    corner(fill, 8)

    combo = frame(hud, "ComboFrame", (1, -24, 1, -126), (0, 300, 0, 82),
                  color=(0.04, 0.06, 0.09), tr=0.30,
                  anchor=(1, 0), z=2, clips=True)
    corner(combo, 12)
    label(combo, "ComboLabel", (0, 12, 0, 8), (1, -24, 0, 30),
          "COMBO   1 / 10", (0.95, 0.88, 0.65), 19,
          "GothamBlack", ax="Right", z=3, tr=1)
    label(combo, "ComboHint", (0, 12, 0, 44), (1, -24, 0, 26),
          "3 s sans frappe = reset", (0.48, 0.56, 0.66), 11,
          "SourceSans", ax="Right", z=3, tr=1)

    label(hud, "StateLabel", (0.5, 0, 1, -48), (0, 460, 0, 30),
          "SABRE  -  RANGE", (0.70, 0.86, 1.0), 17,
          "GothamBold", anchor=(0.5, 0), z=3, tr=1)
    label(hud, "GuardLabel", (0.5, 0, 0, 96), (0, 320, 0, 28),
          "", (0.35, 0.92, 1.0), 20, "GothamBlack",
          anchor=(0.5, 0), z=3, tr=1)
    label(hud, "Flash", (0.5, 0, 0.32, 0), (0, 520, 0, 76),
          "", (1.0, 0.92, 0.62), 40, "GothamBlack",
          anchor=(0.5, 0), z=5, tr=1, visible=False, scaled=True)
    label(hud, "KillFeed", (0.5, 0, 0, 44), (0, 560, 0, 32),
          "", (0.95, 0.78, 0.45), 16, "GothamBold",
          anchor=(0.5, 0), z=4, tr=1, visible=False)

    death = frame(hud, "DeathOverlay", (0, 0, 0, 0), (1, 0, 1, 0),
                  color=(0.35, 0.02, 0.03), tr=0.55, z=7, visible=False)
    label(death, "DeathLabel", (0.5, 0, 0.42, 0), (0, 520, 0, 90),
          "ELIMINE", (1.0, 0.45, 0.42), 52, "GothamBlack",
          anchor=(0.5, 0), z=8, tr=1, scaled=True)

    label(hud, "Controls", (0.5, 0, 1, -32), (0, 900, 0, 24),
          "", (0.62, 0.72, 0.84), 12, "SourceSansBold",
          anchor=(0.5, 0), z=3, tr=1)
    label(hud, "Crosshair", (0.5, -12, 0.5, -12), (0, 24, 0, 24),
          "+", (0.75, 0.88, 1.0), 22, "SourceSans",
          anchor=(0, 0), z=3, tr=1)

    script(hud, "LocalScript", "HUDController", L.HUD_CONTROLLER)
    return hud


# ---------------------------------------------------------------------------
# Description R15 blocky
# ---------------------------------------------------------------------------
def build_description(config):
    d = config.add("HumanoidDescription", "BlockyR15Description")
    # identifiants de maillage par defaut : 0 = R15 cubique natif
    for key in ("Head", "Torso", "LeftArm", "RightArm", "LeftLeg", "RightLeg",
                "Face", "Shirt", "Pants", "GraphicTShirt", "WalkAnimation",
                "RunAnimation", "IdleAnimation", "JumpAnimation",
                "FallAnimation", "SwimAnimation", "ClimbAnimation",
                "MoodAnimation"):
        d.p("int64", key, "0")
    d.f("BodyTypeScale", 0)
    d.f("ProportionScale", 0)
    d.f("WidthScale", 1).f("HeightScale", 1)
    d.f("DepthScale", 1).f("HeadScale", 1)
    for key in ("HeadColor", "TorsoColor", "LeftArmColor", "RightArmColor",
                "LeftLegColor", "RightLegColor"):
        c3(d, key, (0.86, 0.87, 0.90))
    for key in ("HatAccessory", "HairAccessory", "FaceAccessory",
                "NeckAccessory", "ShouldersAccessory", "FrontAccessory",
                "BackAccessory", "WaistAccessory"):
        d.s(key, "")
    d.b("ResetIncludesBodyParts", True)
    return d


# ---------------------------------------------------------------------------
# Services / arborescence
# ---------------------------------------------------------------------------
def build():
    roots = []

    # ---------------- Workspace : uniquement la Baseplate native -----------
    ws = Node("Workspace", "Workspace")
    ws.f("Gravity", 196.2).b("FilteringEnabled", True)
    ws.b("StreamingEnabled", False).f("FallenPartsDestroyHeight", -500)
    roots.append(ws)

    cam = ws.add("Camera", "Camera")
    eye, target = (0, 20, 46), (0, 3, 0)
    rot = look_at(eye, target)
    tags = ["X", "Y", "Z", "R00", "R01", "R02", "R10", "R11", "R12",
            "R20", "R21", "R22"]
    vals = [num(v) for v in (*eye, *rot)]
    cam.p("CoordinateFrame", "CFrame", children=list(zip(tags, vals)))
    cam.f("FieldOfView", 70)
    cam.tok("CameraType", 6)  # Scriptable (menu)
    ws.refprop("CurrentCamera", cam)

    terr = ws.add("Terrain", "Terrain")
    terr.b("Decoration", False)

    base = part(ws, "Baseplate", (0, -10, 0), (512, 20, 512),
                (0.36, 0.38, 0.40), "Plastic",
                anchored=True, collide=True, cast=True, locked=True,
                massless=False)
    base.p("Color3uint8", "Color3uint8", "4284177243")

    spawn = ws.add("SpawnLocation", "SpawnLocation")
    spawn.v3("Size", (12, 1, 12))
    spawn.cf("CFrame", (0, 0.5, 0))
    spawn.p("Color3uint8", "Color3uint8", "4288914085")
    spawn.tok("Material", MATERIAL["Plastic"])
    spawn.tok("TopSurface", 0).tok("BottomSurface", 0)
    spawn.b("Anchored", True).b("CanCollide", True).b("Locked", True)
    spawn.b("CastShadow", False)
    spawn.b("Neutral", True).b("Enabled", True)
    spawn.i("Duration", 0).b("AllowTeamChangeOnTouch", False)

    # ---------------- Players ----------------------------------------------
    players = Node("Players", "Players")
    players.b("CharacterAutoLoads", False)
    players.i("MaxPlayers", 20).f("RespawnTime", 0)
    players.b("UseStrafingAnimations", True)
    roots.append(players)

    # ---------------- Lighting + effets ------------------------------------
    lighting = Node("Lighting", "Lighting")
    lighting.f("Brightness", 2.0).f("ClockTime", 14.5)
    lighting.f("ExposureCompensation", 0.12)
    c3(lighting, "Ambient", (0.28, 0.31, 0.36))
    c3(lighting, "OutdoorAmbient", (0.42, 0.46, 0.52))
    c3(lighting, "ColorShift_Top", (0.85, 0.90, 1.0))
    c3(lighting, "ColorShift_Bottom", (0.40, 0.45, 0.55))
    c3(lighting, "FogColor", (0.62, 0.68, 0.76))
    lighting.f("FogStart", 350).f("FogEnd", 900)
    lighting.f("EnvironmentDiffuseScale", 0.9).f("EnvironmentSpecularScale", 0.9)
    lighting.f("ShadowSoftness", 0.35)
    lighting.b("GlobalShadows", True)
    lighting.tok("Technology", 4)  # Future
    roots.append(lighting)

    blur = lighting.add("BlurEffect", "MenuBlur")
    blur.f("Size", 22).b("Enabled", True)
    bloom = lighting.add("BloomEffect", "BladeBloom")
    bloom.f("Intensity", 0.55).f("Size", 26).f("Threshold", 1.05)
    bloom.b("Enabled", True)
    cc = lighting.add("ColorCorrectionEffect", "CombatGrade")
    cc.f("Brightness", 0.02).f("Contrast", 0.14).f("Saturation", 0.10)
    c3(cc, "TintColor", (1.0, 0.98, 0.96))
    cc.b("Enabled", True)
    rays = lighting.add("SunRaysEffect", "SunRays")
    rays.f("Intensity", 0.025).f("Spread", 0.22).b("Enabled", True)
    dof = lighting.add("DepthOfFieldEffect", "MenuDOF")
    dof.f("FarIntensity", 0.10).f("FocusDistance", 44)
    dof.f("InFocusRadius", 32).f("NearIntensity", 0.0)
    dof.b("Enabled", False)
    atmo = lighting.add("Atmosphere", "ArenaAir")
    atmo.f("Density", 0.18).f("Offset", 0.2).f("Haze", 1.2).f("Glare", 0.10)
    c3(atmo, "Color", (0.78, 0.84, 0.92))
    c3(atmo, "Decay", (0.50, 0.56, 0.66))

    # ---------------- SoundService -----------------------------------------
    sound_service = Node("SoundService", "SoundService")
    sound_group = sound_service.add("SoundGroup", "Combat")
    sound_group.f("Volume", 0.85)
    roots.append(sound_service)

    # ---------------- ReplicatedFirst --------------------------------------
    rep_first = Node("ReplicatedFirst", "ReplicatedFirst")
    roots.append(rep_first)

    # ---------------- ReplicatedStorage ------------------------------------
    rep = Node("ReplicatedStorage", "ReplicatedStorage")
    roots.append(rep)

    config = folder(rep, "Config")
    script(config, "ModuleScript", "CombatConfig", L.CONFIG)
    build_description(config)

    modules = folder(rep, "Modules")
    for name, src in (
        ("InputPolicy", L.INPUT_POLICY),
        ("SaberStateMachine", L.SABER_STATE_MACHINE),
        ("AnimationLibrary", L.ANIMATION_LIBRARY),
        ("SaberFactory", L.SABER_FACTORY),
    ):
        script(modules, "ModuleScript", name, src)

    remotes = folder(rep, "Remotes")
    for name in ("CombatAction", "CombatState", "CombatEvent"):
        remotes.add("RemoteEvent", name)
    for name in ("SetBladeColor", "DeployCharacter"):
        remotes.add("RemoteFunction", name)

    protocol = folder(remotes, "Protocol", "Configuration")
    docs = {
        "CombatAction": "client -> serveur : Draw, Ignite, Extinguish, Holster, Attack, BlockBegin, BlockEnd",
        "CombatState": "serveur -> client : Deployed, Stamina, Combo, SaberState, Guard, PerfectParry, Parried, Blocked, Hit, Kill, Died",
        "CombatEvent": "serveur -> tous : SaberState, BladeColor, Swing, Clash, Backstab, Kill, Deploy, Trail",
        "SetBladeColor": "RemoteFunction : {r,g,b} 0-255 -> true, normalized",
        "DeployCharacter": "RemoteFunction : {pc=true, platform='PC'} -> true, 'deploye'",
    }
    for key, value in docs.items():
        v = protocol.add("StringValue", key)
        v.s("Value", value)

    assets = folder(rep, "Assets")
    build_saber_template(assets, sound_group)

    effects = folder(assets, "Effects")
    anchor = part(effects, "SparkAnchor", (0, 0, 0), (0.2, 0.2, 0.2),
                  (1, 1, 1), "Neon", tr=1)
    anchor.f("Transparency", 1)
    pe = anchor.add("ParticleEmitter", "SparkEmitter")
    cseq(pe, "Color", "0 1 0.92 0.55 0 1 1 0.45 0.15 0 ")
    nseq(pe, "Size", "0 0.35 0 1 0 0 ")
    nseq(pe, "Transparency", "0 0 0 1 1 0 ")
    pe.p("NumberRange", "Lifetime", "0.15 0.42 ")
    pe.p("NumberRange", "Speed", "5 13 ")
    vec2(pe, "SpreadAngle", 70, 70)
    pe.f("Rate", 0).f("LightEmission", 1).f("LightInfluence", 0)
    pe.b("Enabled", True).b("LockedToPart", True)
    pe.content("Texture", None)
    clash = effects.add("PointLight", "ClashLight")
    c3(clash, "Color", (1.0, 0.82, 0.45))
    clash.f("Brightness", 3).f("Range", 18)
    clash.b("Enabled", False).b("Shadows", False)

    anims = folder(rep, "Animations")
    animation_tables(anims)

    # ---------------- ServerStorage ----------------------------------------
    server_storage = Node("ServerStorage", "ServerStorage")
    bus = folder(server_storage, "CombatBus")
    bus.add("BindableEvent", "CombatLog")
    bus.add("BindableEvent", "DeploySignal")
    roots.append(server_storage)

    # ---------------- ServerScriptService ----------------------------------
    sss = Node("ServerScriptService", "ServerScriptService")
    roots.append(sss)
    script(sss, "ModuleScript", "ServerState", L.SERVER_STATE)
    for name, src in (
        ("RigSpawner", L.RIG_SPAWNER),
        ("SaberService", L.SABER_SERVICE),
        ("CombatServer", L.COMBAT_SERVER),
        ("RemoteHandlers", L.REMOTE_HANDLERS),
        ("CombatLogger", L.COMBAT_LOGGER),
    ):
        script(sss, "Script", name, src)

    # ---------------- StarterPlayer ----------------------------------------
    starter_player = Node("StarterPlayer", "StarterPlayer")
    starter_player.b("LoadCharacterAppearance", False)
    starter_player.tok("GameSettingsAvatar", 1)          # R15
    starter_player.tok("GameSettingsR15Collision", 0)    # OuterBox
    starter_player.f("CharacterWalkSpeed", 16)
    starter_player.f("CharacterJumpHeight", 7.2)
    starter_player.f("CameraMaxZoomDistance", 40)
    starter_player.f("CameraMinZoomDistance", 5)
    starter_player.b("AutoJumpEnabled", False)
    starter_player.b("EnableMouseLockOption", True)
    starter_player.b("AllowCustomAnimations", True)
    starter_player.b("CharacterBreakJointsOnDeath", True)
    starter_player.f("HealthDisplayDistance", 0)
    starter_player.f("NameDisplayDistance", 0)
    sps = starter_player.add("StarterPlayerScripts", "StarterPlayerScripts")
    script(sps, "LocalScript", "CombatClient", L.COMBAT_CLIENT)
    scs = starter_player.add("StarterCharacterScripts", "StarterCharacterScripts")
    script(scs, "LocalScript", "Animate", L.ANIMATE_PLACEHOLDER)
    roots.append(starter_player)

    # ---------------- StarterGui -------------------------------------------
    starter_gui = Node("StarterGui", "StarterGui")
    starter_gui.b("ResetPlayerGuiOnSpawn", False)
    roots.append(starter_gui)
    build_main_menu(starter_gui)
    build_hud(starter_gui)

    # ---------------- autres services --------------------------------------
    for name in ("StarterPack", "Teams", "Chat", "LocalizationService",
                 "MaterialService", "CollectionService", "Debris",
                 "HttpService", "InsertService", "RunService",
                 "TweenService", "ContextActionService", "UserInputService"):
        roots.append(Node(name, name))

    return roots


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------
def validate(path):
    import xml.etree.ElementTree as ET
    import math as _m
    tree = ET.parse(path)
    root = tree.getroot()
    assert root.tag == "roblox" and root.get("version") == "4"

    items = root.findall(".//Item")
    props = root.findall(".//Properties")
    assert len(items) == len(props), "un <Properties> exactement par <Item>"
    for it in items:
        ps = it.findall("Properties")
        assert len(ps) == 1
        assert list(it)[0].tag == "Properties"
        assert not ps[0].findall("Item")
        names = [p.get("name") for p in ps[0]]
        assert all(names), f"propriete sans nom dans {it.get('class')}"
        assert len(names) == len(set(names)), f"doublon dans {it.get('class')}: {names}"
    refs = [it.get("referent") for it in items]
    assert len(refs) == len(set(refs)), "referents dupliques"
    refset = set(refs)

    known_refs = []
    for e in root.iter():
        if e.tag == "Ref" and e.text:
            assert e.text in refset, f"Ref orpheline: {e.text}"
        if e.tag == "ProtectedString" and e.get("name") == "Source":
            assert e.text and len(e.text) > 40, "Source vide/tronque"
        if e.tag in ("X", "Y", "Z", "R00", "R01", "R02", "R10", "R11",
                     "R12", "R20", "R21", "R22", "S", "O", "XS", "XO",
                     "YS", "YO", "float", "double", "int", "int64", "token",
                     "Time", "MaskWeight", "Thickness", "Volume"):
            try:
                v = float(e.text)
                assert _m.isfinite(v), f"valeur non finie: {e.tag}={e.text}"
            except (TypeError, ValueError):
                raise AssertionError(f"nombre invalide: {e.tag}={e.text!r}")

    for cf in root.iter("CoordinateFrame"):
        v = [float(cf.findtext(k)) for k in
             ("R00", "R01", "R02", "R10", "R11", "R12", "R20", "R21", "R22")]
        det = (v[0] * (v[4] * v[8] - v[5] * v[7])
               - v[1] * (v[3] * v[8] - v[5] * v[6])
               + v[2] * (v[3] * v[7] - v[4] * v[6]))
        assert abs(det - 1) < 0.02, f"rotation invalide det={det}"

    scripts = [it for it in items if it.get("class") in
               ("Script", "LocalScript", "ModuleScript")]
    return {
        "instances": len(items), "scripts": len(scripts),
        "bytes": os.path.getsize(path),
        "top_services": [i.get("class") for i in items[:0]] or
                        [c.get("class") for c in root.findall("Item")],
        "ref_count": len(refs),
    }


def main():
    write_place(OUT, build())
    info = validate(OUT)
    print(f"OK -> {os.path.basename(OUT)}")
    print(f"    {info['instances']:,} instances | {info['scripts']} scripts | "
          f"{info['ref_count']} referents | {info['bytes'] / 1024:.0f} Ko")
    print(f"    {len(info['top_services'])} services racine")


if __name__ == "__main__":
    main()
