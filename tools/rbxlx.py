"""
Mini-bibliotheque de generation de fichiers .rbxlx (format XML Roblox v4).

Reference : https://github.com/RobloxAPI/spec/blob/master/formats/rbxlx.md
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field


# ---------------------------------------------------------------------------
# Enums Roblox (valeurs numeriques officielles)
# ---------------------------------------------------------------------------
MATERIAL = {
    "Plastic": 256, "SmoothPlastic": 272, "Neon": 288,
    "Wood": 512, "WoodPlanks": 528,
    "Marble": 784, "Slate": 800, "Concrete": 816, "Granite": 832,
    "Brick": 848, "Pebble": 864, "Cobblestone": 880, "Rock": 896,
    "Sandstone": 912,
    "CorrodedMetal": 1040, "DiamondPlate": 1056, "Foil": 1072, "Metal": 1088,
    "Grass": 1280, "LeafyGrass": 1284, "Sand": 1296, "Fabric": 1312,
    "Snow": 1328, "Mud": 1344, "Ground": 1360, "Asphalt": 1376,
    "Ice": 1536, "Glacier": 1552, "Glass": 1568, "ForceField": 1584,
    "Air": 1792, "Water": 2048,
}
SHAPE = {"Ball": 0, "Block": 1, "Cylinder": 2, "Wedge": 3}
TECHNOLOGY = {"ShadowMap": 3, "Future": 4}
NORMAL_ID = {"Right": 0, "Top": 1, "Back": 2, "Left": 3, "Bottom": 4, "Front": 5}

_counter = [0]


def new_ref() -> str:
    _counter[0] += 1
    return f"RBX{_counter[0]:08X}"


def esc(t: str) -> str:
    return (
        str(t).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def num(v: float) -> str:
    f = float(v)
    if f == 0:
        return "0"
    if abs(f - round(f)) < 1e-9:
        return str(int(round(f)))
    return f"{f:.7g}"


def packed(rgb) -> int:
    r, g, b = (max(0, min(255, round(c * 255))) for c in rgb)
    return 0xFF000000 | (r << 16) | (g << 8) | b


@dataclass
class Prop:
    tag: str
    name: str
    text: str | None = None
    children: list[tuple[str, str]] = field(default_factory=list)

    def render(self, indent: str) -> str:
        if self.children:
            inner = "".join(
                f"\n{indent}\t<{t}>{v}</{t}>" for t, v in self.children
            )
            return f"{indent}<{self.tag} name=\"{self.name}\">{inner}\n{indent}</{self.tag}>"
        return f"{indent}<{self.tag} name=\"{self.name}\">{esc(self.text or '')}</{self.tag}>"


@dataclass
class Node:
    cls: str
    name: str = ""
    ref: str = field(default_factory=new_ref)
    props: dict[str, Prop] = field(default_factory=dict)
    children: list["Node"] = field(default_factory=list)

    def __post_init__(self):
        if self.name:
            self.s("Name", self.name)

    def p(self, tag: str, name: str, text=None, children=None) -> "Node":
        self.props[name] = Prop(tag, name, text, children or [])
        return self

    # raccourcis types
    def s(self, n, v): return self.p("string", n, v)
    def b(self, n, v): return self.p("bool", n, "true" if v else "false")
    def f(self, n, v): return self.p("float", n, num(v))
    def i(self, n, v): return self.p("int", n, str(int(v)))
    def tok(self, n, v): return self.p("token", n, str(v))
    def ps(self, n, v): return self.p("ProtectedString", n, v)
    def refprop(self, n, node): return self.p("Ref", n, node.ref)
    def v3(self, n, v):
        return self.p("Vector3", n, children=[
            ("X", num(v[0])), ("Y", num(v[1])), ("Z", num(v[2]))])
    def c3(self, n, v):
        return self.p("Color3", n, children=[
            ("R", num(v[0])), ("G", num(v[1])), ("B", num(v[2]))])
    def cf(self, n, pos, rot=None):
        rot = rot or (0, 0, 0)
        m = euler(*rot)
        comps = ["X", "Y", "Z", "R00", "R01", "R02", "R10", "R11", "R12",
                 "R20", "R21", "R22"]
        vals = [num(v) for v in (*pos, *m)]
        return self.p("CoordinateFrame", n, children=list(zip(comps, vals)))
    def udim2(self, n, xs, xo, ys, yo):
        return self.p("UDim2", n, children=[
            ("XS", num(xs)), ("XO", num(xo)), ("YS", num(ys)), ("YO", num(yo))])
    def content(self, n, url=None):
        return self.p("Content", n, children=[("url", url) if url else ("null", "")])

    def add(self, cls: str, name: str = "") -> "Node":
        child = Node(cls, name)
        self.children.append(child)
        return child

    def render(self, depth: int = 1) -> str:
        ind = "\t" * depth
        out = [f"{ind}<Item class=\"{self.cls}\" referent=\"{self.ref}\">",
               f"{ind}\t<Properties>"]
        for key in sorted(self.props):
            out.append(self.props[key].render(f"{ind}\t\t"))
        out.append(f"{ind}\t</Properties>")
        for c in self.children:
            out.append(c.render(depth + 1))
        out.append(f"{ind}</Item>")
        return "\n".join(out)


def euler(rx: float = 0, ry: float = 0, rz: float = 0) -> list[float]:
    """Angles en degres -> matrice 3x3 (ligne par ligne) pour CoordinateFrame."""
    x, y, z = map(math.radians, (rx, ry, rz))
    cx, sx, cy, sy, cz, sz = math.cos(x), math.sin(x), math.cos(y), math.sin(y), math.cos(z), math.sin(z)
    return [
        cy * cz, sx * sy * cz - cx * sz, cx * sy * cz + sx * sz,
        cy * sz, sx * sy * sz + cx * cz, cx * sy * sz - sx * cz,
        -sy, sx * cy, cx * cy,
    ]


def write_place(path: str, roots: list[Node]) -> None:
    parts = [
        '<?xml version="1.0" encoding="utf-8" standalone="yes"?>',
        '<roblox xmlns:xmime="http://www.w3.org/2005/05/xmlmime" '
        'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
        'xsi:noNamespaceSchemaLocation="http://www.roblox.com/roblox.xsd" version="4">',
        "\t<External>null</External>",
        "\t<External>nil</External>",
    ]
    parts.extend(n.render(1) for n in roots)
    parts.append("</roblox>")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(parts) + "\n")
