#!/usr/bin/env python3
"""Genere MaisonRealiste.rbxlx : villa contemporaine 2 niveaux, interieur complet.

    python3 tools/build_house.py
"""

from __future__ import annotations

import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from rbxlx import Node, write_place, MATERIAL  # noqa: E402
from house_lib import (  # noqa: E402
    BOXES, C, part, ball, disc, light, glowing_bulb, downlights, pendant, switch,
    wall, wall_box, floor_planks, floor_tiles, ceiling, rug, artwork, plant,
    bookshelf, sofa, armchair, coffee_table, tv_wall, dining_set, kitchen, bed,
    wardrobe, bathroom, office, stairs, tree, hedge, bollard, lounger, parasol,
    car, pool, fence, tint, jitter, RNG,
)

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   "MaisonRealiste.rbxlx")
BOXJSON = os.path.join(os.path.dirname(os.path.abspath(__file__)), "boxes.json")

# --- constantes de la maison ------------------------------------------------
HX, HZ = 24.0, 18.0          # demi-largeur / demi-profondeur
T = 0.8                       # epaisseur des murs
Y_RDC = 0.0                  # sol du RDC
C_RDC = 10.6                 # sous-plafond du RDC
Y_ETG = 11.4                 # sol de l'etage
C_ETG = 21.6                 # sous-plafond de l'etage
ROOF = 22.4                  # toiture

WHITE, CHAR = C["white"], C["charcoal"]


def build():
    # ------------------------------------------------------------------ roots
    ws = Node("Workspace", "Workspace")
    ws.b("StreamingEnabled", True).f("Gravity", 196.2)
    ws.add("Terrain", "Terrain")

    spawn = ws.add("SpawnLocation", "Arrivee")
    spawn.b("Anchored", True).b("Neutral", True).b("Enabled", True)
    spawn.v3("Size", (8, 1, 8))
    spawn.cf("CFrame", (0, 1.2, 38))
    spawn.c3("Color", C["stone"]).tok("Material", MATERIAL["Marble"])

    lighting = Node("Lighting", "Lighting")
    lighting.tok("Technology", 4)
    lighting.f("Brightness", 2.1).f("ClockTime", 17.4)
    lighting.f("ExposureCompensation", 0.15)
    lighting.c3("Ambient", (0.32, 0.29, 0.26))
    lighting.c3("OutdoorAmbient", (0.46, 0.40, 0.34))
    lighting.c3("FogColor", (0.62, 0.58, 0.52))
    lighting.f("FogStart", 120).f("FogEnd", 420)
    lighting.b("GlobalShadows", True)
    lighting.f("EnvironmentDiffuseScale", 0.85)
    lighting.f("EnvironmentSpecularScale", 0.9)

    atmo = lighting.add("Atmosphere", "BrumeDoree")
    atmo.f("Density", 0.24).f("Offset", 0.3).f("Haze", 1.4).f("Glare", 0.16)
    atmo.c3("Color", (0.78, 0.72, 0.63)).c3("Decay", (0.55, 0.42, 0.34))

    bloom = lighting.add("BloomEffect", "Bloom")
    bloom.f("Intensity", 0.35).f("Size", 22).f("Threshold", 1.3)
    cc = lighting.add("ColorCorrectionEffect", "Etalonnage")
    cc.f("Brightness", 0.02).f("Contrast", 0.12).f("Saturation", 0.08)
    cc.c3("TintColor", (1.0, 0.97, 0.92))
    rays = lighting.add("SunRaysEffect", "Rayons")
    rays.f("Intensity", 0.035).f("Spread", 0.22)
    dof = lighting.add("DepthOfFieldEffect", "Profondeur")
    dof.f("FarIntensity", 0.06).f("FocusDistance", 45)
    dof.f("InFocusRadius", 35).f("NearIntensity", 0.0)

    sss = Node("ServerScriptService", "ServerScriptService")
    script = sss.add("Script", "ControlesMaison")
    script.ps("Source", SCRIPT_SOURCE)

    house = ws.add("Model", "MaisonRealiste")
    ext = house.add("Model", "Exterieur")
    rdc = house.add("Model", "RezDeChaussee")
    etg = house.add("Model", "Etage")
    toit = house.add("Model", "Toiture")
    inter = house.add("Model", "Interrupteurs")

    # ==================================================================
    # EXTERIEUR : terrain, cloture, allee, terrasse, piscine, garage
    # ==================================================================
    jardin = ext.add("Model", "Jardin")
    part(jardin, "Pelouse", (0, -0.5, 0), (140, 1, 130), C["lawn"], "Grass", tag="GROUND")
    part(jardin, "DalleFondation", (0, -0.75, 0), (49.5, 1.1, 37.5),
         C["concrete"], "Concrete", tag="SLAB")
    fence(ext, "Cloture", -64, 64, -58, 58)

    # allee principale et dallage d'entree
    allee = ext.add("Model", "AlleePrincipale")
    part(allee, "Allee", (0, 0.06, 37), (7.0, 0.2, 38), C["stone"], "Sandstone")
    for i in range(19):
        part(allee, f"Dalle{i:02d}", (0, 0.2, 19 + i * 2),
             (6.4, 0.12, 1.75), jitter(C["stone"], 0.03), "Sandstone")
    # pelouses laterales + massifs
    for s in (-1, 1):
        part(allee, f"BandeGazon{s}", (s * 5.0, 0.12, 37), (2.6, 0.14, 38),
             C["grass"], "Grass")
        for k in range(9):
            ball(allee, f"Massif{s}_{k}",
                 (s * (8 + (k % 3) * 1.2), 0.55, 21 + k * 3.8),
                 1.6, C["leaf2"] if k % 2 else C["pink"], "Grass")
            part(allee, f"Tige{s}_{k}",
                 (s * (8 + (k % 3) * 1.2), 0.35, 21 + k * 3.8),
                 (0.14, 0.7, 0.14), C["leaf"], "Wood")
    for i, (x, z) in enumerate([(x, z) for z in (21, 28, 35, 42, 49)
                                for x in (-3.9, 3.9)]):
        bollard(jardin, f"Borne{i:02d}", x, z)
        light(jardin, f"LumiereAllee{i}", (x, 2.5, z), C["neon"], 0.55, 10)

    # porche d'entree
    porche = ext.add("Model", "Porche")
    part(porche, "DallePorche", (0, 0.35, 21.5), (22, 0.7, 8),
         C["stone"], "Marble")
    for i in range(3):
        part(porche, f"Marche{i}", (0, 0.7 + i * 0.22, 25.6 - i * 0.8),
             (14 - i * 1.2, 0.24, 1.0), C["stone"], "Marble")
    for x in (-9.5, -3.2, 3.2, 9.5):
        part(porche, f"Colonne{x}", (x, 4.6, 24.2), (1.0, 8.6, 1.0),
             C["warmwhite"], "Concrete")
        part(porche, f"Chapiteau{x}", (x, 8.9, 24.2), (1.5, 0.4, 1.5),
             C["white"], "Marble")
    part(porche, "Auvent", (0, 9.3, 21.5), (23, 0.7, 9),
         C["warmwhite"], "Concrete")
    part(porche, "SousFaceBois", (0, 8.92, 21.5), (22, 0.12, 8.4),
         C["woodlight"], "Wood")
    for x in (-7, -3.5, 0, 3.5, 7):
        glowing_bulb(porche, f"SpotPorche{x}", (x, 8.8, 21.5),
                     (0.7, 0.09, 0.7), C["neon"], range_=12, brightness=0.7)
    for s in (-1, 1):
        part(porche, f"Jardiniere{s}", (s * 7.5, 1.1, 25.0), (3.0, 1.4, 1.6),
             C["terracotta"], "Sandstone")
        for k in range(4):
            ball(porche, f"Buisson{s}_{k}",
                 (s * 7.5 + (k - 1.5) * 0.7, 2.0, 25.0), 1.3,
                 C["pink"] if k % 2 else C["leaf2"], "Grass")
    # lampe de facade
    for s in (-1, 1):
        part(porche, f"Applique{s}", (s * 3.2, 5.6, 18.55), (0.5, 1.6, 0.45),
             C["charcoal"], "Metal")
        glowing_bulb(porche, f"AmpouleFacade{s}", (s * 3.2, 5.6, 18.85),
                     (0.3, 1.1, 0.2), C["neon"], range_=13, brightness=0.8)

    # terrasse arriere + piscine
    terrasse = ext.add("Model", "TerrasseArriere")
    floor_planks(terrasse, "Platelage", -26, 26, -53, -18, 0.55,
                 base=C["woodmid"], width=1.4, along="z")
    part(terrasse, "MargelleArriere", (0, 0.65, -18.6), (48, 0.9, 1.0),
         C["stone"], "Marble")
    pool(terrasse, "Piscine", -14, 14, -46, -28)
    for s in (-1, 1):
        lounger(terrasse, f"Transat{s}", s * 19.5, -34, yaw=0)
        part(terrasse, f"TableBasse{s}", (s * 16.5, 1.2, -34),
             (2.2, 0.3, 2.2), C["steel"], "Metal")
    parasol(terrasse, "ParasolGauche", -19.5, -34, 5.0)
    parasol(terrasse, "ParasolDroite", 19.5, -34, 5.0)
    # cuisine d'ete / barbecue
    part(terrasse, "Barbecue", (-24, 1.7, -22), (4.0, 2.6, 3.0), C["steel"], "Metal")
    part(terrasse, "Grille", (-24, 3.1, -22), (3.6, 0.15, 2.6), C["charcoal"], "Metal")
    part(terrasse, "PlanBarbecue", (-24, 3.3, -19.5), (4.4, 0.25, 3.0),
         C["stone"], "Marble")
    for k in range(6):
        part(terrasse, f"LumierePiscine{k}", (-12 + k * 4.8, 0.5, -26.9),
             (0.7, 0.2, 0.25), C["neon"], "Neon")
    for k in range(4):
        light(jardin, f"LumierePiscine{k}", (-12 + k * 9, 0.8, -37),
              C["water"], 0.5, 15)

    # garage + voiture
    garage = ext.add("Model", "Garage")
    part(garage, "DalleGarage", (-36, 0.1, 21), (20.5, 0.6, 22.5),
         C["concrete"], "Concrete")
    part(garage, "GarageMurNord", (-36, 4.5, 9.9), (20.5, 9.0, 0.6),
         C["warmwhite"], "Concrete")
    for s in (-1, 1):
        part(garage, f"GarageMur{s}", (-36 + s * 10.0, 4.5, 21),
             (0.6, 9.0, 22), C["warmwhite"], "Concrete")
    part(garage, "ToitGarage", (-36, 9.3, 21), (21.5, 0.7, 23.0),
         C["charcoal"], "Slate")
    for k in range(7):
        part(garage, f"LamePorte{k}", (-36, 1.0 + k * 1.15, 32.2),
             (19.0, 1.05, 0.25), tint(C["warmwhite"], 0.9), "Wood")
    part(garage, "PorteService", (-26.3, 3.0, 28), (0.4, 5.0, 2.2),
         C["walnut"], "Wood")
    for x in (-41, -31):
        part(garage, f"Etagere{x}", (x, 3.0, 12), (4.0, 0.25, 1.5),
             C["steel"], "Metal")
        for k in range(4):
            part(garage, f"Boite{x}_{k}", (x - 1.4 + k * 0.9, 3.7, 12),
                 (0.7, 1.1, 1.0), RNG.choice([C["navy"], C["rust"], C["cream"]]),
                 "SmoothPlastic")
    glowing_bulb(garage, "NeonGarage", (-36, 8.6, 21), (8.0, 0.2, 1.0),
                 (0.95, 0.97, 1.0), range_=22, brightness=1.0)
    car(garage, "Voiture", -36, 21, yaw=0)
    # allee vers le garage
    part(allee, "AccesGarage", (-36, 0.08, 44), (13, 0.2, 25),
         C["concrete"], "Concrete")
    for i in range(12):
        part(allee, f"Joint{i}", (-36, 0.2, 33 + i * 2), (12.6, 0.06, 0.12),
             C["stone"], "Sandstone")

    # arbres et haies
    for k, (x, z, h, bl) in enumerate([
        (-52, 38, 13, False), (-48, -38, 15, False), (52, 40, 12, True),
        (55, -34, 14, False), (-20, -55, 11, True), (20, -55, 12, False),
        (-58, 5, 13, False), (58, 6, 12, False), (38, 50, 10, True),
        (-10, 50, 12, False),
    ]):
        tree(jardin, f"Arbre{k:02d}", x, z, h, blossom=bl)
    for k in range(12):
        hedge(jardin, f"HaieN{k}", -58 + k * 10, -54, 9.5)
        hedge(jardin, f"HaieS{k}", -58 + k * 10, 54, 9.5)
    for x in (-30, -26, 26, 30):
        for z in (26, 30, 34):
            part(jardin, f"Fleur{x}_{z}", (x, 0.35, z), (0.25, 0.7, 0.25),
                 C["leaf"], "Wood")
            ball(jardin, f"Corolle{x}_{z}", (x, 0.85, z), 1.0,
                 RNG.choice([C["pink"], C["terracotta"], C["cream"]]), "Fabric")

    # ==================================================================
    # REZ-DE-CHAUSSEE
    # ==================================================================
    part(rdc, "DalleRDC", (0, -0.2, 0), (48.8, 0.4, 36.8),
         C["concrete"], "Concrete", tag="SLAB")
    salon = rdc.add("Model", "Salon")
    cuisine_m = rdc.add("Model", "Cuisine")
    sam = rdc.add("Model", "SalleAManger")
    entree = rdc.add("Model", "Entree")
    wc = rdc.add("Model", "WC")

    floor_planks(salon, "ParquetSalon", -23.7, -4.2, -17.7, 17.7, 0.06,
                 base=C["woodlight"], width=1.25)
    floor_tiles(cuisine_m, "CarrelageCuisine", -4.2, 23.7, -17.7, 5.8, 0.06, 2.0)
    floor_tiles(sam, "CarrelageSalleAManger", -4.2, 23.7, 5.8, 17.7, 0.06, 2.0)
    floor_tiles(entree, "MarbreEntree", -4.2, 4.2, 8.0, 17.7, 0.09, 1.8)

    # murs exterieurs RDC
    front = [
        (-22.5, -3.2, 1.0, 9.5, "win"),
        (-2.3, 2.3, 0.0, 7.8, "door"),
        (3.2, 22.5, 1.0, 9.5, "win"),
    ]
    back = [
        (-22.5, -12.0, 1.0, 9.5, "win"),
        (-10.5, 10.5, 0.0, 9.5, "slide"),
        (12.0, 22.5, 1.0, 9.5, "win"),
    ]
    left = [(-15.5, -5.0, 1.0, 9.5, "win"), (5.0, 15.5, 1.0, 9.5, "win")]
    right = [(-15.5, -5.0, 1.0, 9.5, "win"), (5.0, 15.5, 1.0, 9.5, "win")]
    wall(rdc, "FacadeAvantRDC", "x", HZ, -HX, HX, Y_RDC, C_RDC, T,
         C["warmwhite"], "Concrete", front, tag="EXT")
    wall(rdc, "FacadeArriereRDC", "x", -HZ, -HX, HX, Y_RDC, C_RDC, T,
         C["warmwhite"], "Concrete", back, tag="EXT")
    wall(rdc, "MurOuestRDC", "z", -HX, -HZ, HZ, Y_RDC, C_RDC, T,
         C["warmwhite"], "Concrete", left, tag="EXT")
    wall(rdc, "MurEstRDC", "z", HX, -HZ, HZ, Y_RDC, C_RDC, T,
         C["warmwhite"], "Concrete", right, tag="EXT")

    # habillage : bardage bois + bandeaux de pierre
    for k in range(14):
        part(rdc, f"BardageAvant{k}", (-22.5 + k * 1.15, 5.2, 18.48),
             (1.05, 9.0, 0.14), jitter(C["woodmid"], 0.03), "Wood")
    for s in (-1, 1):
        part(rdc, f"Soubassement{s}", (s * HX * 0.99, 0.55, 0),
             (0.25, 1.1, 2 * HZ), C["stone"], "Marble")

    # cloisons interieures RDC
    wall_box(rdc, "MurTV", "x", -8.6, -23.2, -5.0, 0, C_RDC, 0.55,
             C["white"], "SmoothPlastic", tag="PARTITION")
    # cloison de l'escalier / WC
    for z in (-16.6, -8.0):
        wall_box(wc, f"CloisonWC_Z{z}", "x", z, 4.0, 11.0, 0, 9.6, 0.4,
                 C["white"], "SmoothPlastic", tag="PARTITION")
    wall_box(wc, "CloisonWC_X4", "z", 4.0, -16.6, -8.0, 0, 9.6, 0.4,
             C["white"], "SmoothPlastic", tag="PARTITION")
    wall_box(wc, "CloisonWC_X11", "z", 11.0, -16.6, -11.0, 0, 9.6, 0.4,
             C["white"], "SmoothPlastic", tag="PARTITION")
    wall_box(wc, "CloisonWC_X11b", "z", 11.0, -8.5, -8.0, 0, 9.6, 0.4,
             C["white"], "SmoothPlastic", tag="PARTITION")
    # meubles WC
    part(wc, "VasqueWC", (6.2, 2.6, -9.7), (2.4, 0.4, 1.6), C["white"], "Marble")
    part(wc, "MeubleWC", (6.2, 1.4, -9.7), (2.2, 2.4, 1.4), C["walnut"], "Wood")
    part(wc, "MiroirWC", (6.2, 6.0, -16.3), (2.4, 3.0, 0.12),
         C["bluegrey"], "Glass", refl=0.5)
    part(wc, "ToiletteWC", (9.4, 1.2, -14.0), (2.0, 2.4, 2.6), C["white"], "Marble")
    part(wc, "ReservoirWC", (9.4, 2.7, -15.1), (1.9, 2.6, 0.6), C["white"], "Marble")

    # plafond RDC
    ceiling(rdc, "PlafondRDC", -23.9, 23.9, -17.9, 17.9, C_RDC + 0.18,
            hole=(-3.6, 3.6, -17.9, 0.6))
    downlights(salon, -21, -6, -15, 15, C_RDC - 0.15, step=6.0)
    downlights(cuisine_m, -2, 22, -15, 4, C_RDC - 0.15, step=6.0)
    downlights(sam, -2, 22, 7, 16, C_RDC - 0.15, step=5.5)
    downlights(entree, -3, 3, 9, 17, C_RDC - 0.15, step=5.0)
    light(wc, "LumiereWC", (7.5, 9.0, -12.0), C["neon"], 1.0, 14)

    # --- salon -----------------------------------------------------------
    rug(salon, "TapisSalon", -14.0, 1.0, 0.16, 15.0, 11.0, C["cream"], C["sand"])
    tv_wall(salon, "MurMedia", -14.0, -8.0, 0.1, axis="x")
    # cheminee avec feu
    part(salon, "Cheminee", (-21.0, 4.0, 3.0), (2.6, 8.0, 7.0), C["stone"], "Marble")
    part(salon, "Foyer", (-19.6, 2.6, 3.0), (0.4, 3.6, 4.6), C["black"], "Slate")
    for k in range(5):
        part(salon, f"Buche{k}", (-19.4, 1.0, 1.5 + k * 0.75),
             (0.7, 0.5, 1.8), C["wooddark"], "Wood")
    fire = salon.add("Fire", "Feu")
    fire.c3("Color", (1.0, 0.48, 0.12)).c3("SecondaryColor", (1.0, 0.85, 0.35))
    fire.f("Heat", 9).f("Size", 3.2).b("Enabled", True)
    light(salon, "LueurCheminee", (-19.0, 2.5, 3.0), (1.0, 0.55, 0.22), 1.3, 16)
    sofa(salon, "Canape", -14.0, 5.2, 0.2, yaw=0, w=11.0, d=3.8, color=C["fabric"])
    coffee_table(salon, "TableBasse", -14.0, -1.2, 0.2, w=6.4, d=3.4)
    armchair(salon, "FauteuilA", -21.0, -3.5, 0.2, color=C["sage"])
    armchair(salon, "FauteuilB", -7.5, -3.5, 0.2, color=C["terracotta"])
    # coin lecture arriere
    bookshelf(salon, "BibliothequeSalon", (-14.0, 4.5, -16.9), w=11.0, h=8.0)
    rug(salon, "TapisLecture", -14.0, -13.0, 0.16, 9.0, 6.0, C["navy"])
    armchair(salon, "FauteuilLecture", -17.0, -13.0, 0.2, color=C["linen"])
    part(salon, "TableLecture", (-11.5, 1.5, -13.0), (2.2, 0.22, 2.2),
         C["walnut"], "Wood")
    plant(salon, "PlanteSalon", (-5.6, 0.2, 13.5), 2.6)
    artwork(salon, "TableauSalon", (-14.0, 6.5, -8.15), 5.0, 3.2,
            colors=(C["sage"], C["terracotta"], C["cream"], C["navy"]))
    pendant(salon, (-14.0, 10.2, -13.0), 3.6, shade=C["brass"], r=1.1)

    # --- cuisine + salle a manger ---------------------------------------
    kitchen(cuisine_m, "CuisineEquipee", 5.0, 23.0, -7.0, 6.0, 0.1)
    dining_set(sam, "TableSalleAManger", 12.0, 12.5, 0.1, seats=8)
    pendant(sam, (12.0, 10.2, 12.5), 2.8, shade=C["brass"], r=1.3)
    artwork(sam, "TableauSalleAManger", (12.0, 6.0, 17.3), 6.0, 3.0,
            colors=(C["terracotta"], C["cream"], C["rust"]))
    plant(sam, "PlanteSalleAManger", (21.0, 0.2, 8.0), 2.8)

    # --- entree ----------------------------------------------------------
    part(entree, "Console", (0, 2.0, 16.6), (5.0, 0.28, 1.2), C["walnut"], "Wood")
    for s in (-1, 1):
        part(entree, f"PiedConsole{s}", (s * 2.1, 1.0, 16.6), (0.2, 2.0, 1.0),
             C["brass"], "Metal")
    part(entree, "MiroirEntree", (0, 6.5, 17.5), (4.0, 5.0, 0.15),
         C["bluegrey"], "Glass", refl=0.55)
    part(entree, "CadreMiroir", (0, 6.5, 17.4), (4.4, 5.4, 0.1),
         C["brass"], "Metal")
    part(entree, "VidePoches", (-1.2, 2.3, 16.6), (0.9, 0.3, 0.9),
         C["steel"], "Marble")
    plant(entree, "PlanteEntree", (1.5, 0.2, 16.6), 2.0)
    for k in range(3):
        pendant(entree, (-2.0 + k * 2.0, 10.2, 14.0), 3.2,
                shade=C["brass"], r=0.55)

    # --- escalier ---------------------------------------------------------
    escalier = rdc.add("Model", "Escalier")
    stairs(escalier, "Volee", 0.0, -16.8, 0.0, width=6.2,
           length=16.8, height=Y_ETG, steps=22)
    part(escalier, "Palier", (0, Y_ETG - 0.2, -0.5), (7.0, 0.4, 3.5),
         C["woodlight"], "Wood", tag="SLAB")

    # ==================================================================
    # ETAGE
    # ==================================================================
    # dalle de l'etage avec trappe pour l'escalier
    for i, (a, b, c, d) in enumerate([
        (-24.4, -3.6, -18.4, 18.4), (3.6, 24.4, -18.4, 18.4),
        (-3.6, 3.6, 0.6, 18.4),
    ]):
        part(etg, f"DalleEtage{i}", ((a + b) / 2, Y_ETG - 0.25, (c + d) / 2),
             (b - a, 0.5, d - c), C["concrete"], "Concrete", tag="SLAB")
    # contour de la trappe de l'escalier
    for s in (-1, 1):
        part(etg, f"ContourTrappe{s}", (s * 3.6, Y_ETG + 0.15, -7.0),
             (0.3, 0.5, 17.0), C["walnut"], "Wood")

    cp = etg.add("Model", "ChambrePrincipale")
    ce = etg.add("Model", "ChambreEnfant")
    sdb = etg.add("Model", "SalleDeBain")
    bur = etg.add("Model", "Bureau")
    hall = etg.add("Model", "Couloir")
    balcon = etg.add("Model", "Balcon")

    floor_planks(cp, "ParquetChambre", -23.7, -2.2, -17.7, -2.2,
                 Y_ETG + 0.05, base=C["woodmid"], width=1.1)
    floor_planks(ce, "ParquetEnfant", 2.2, 23.7, -17.7, -2.2,
                 Y_ETG + 0.05, base=C["woodlight"], width=1.1)
    floor_tiles(sdb, "CarrelageSDB", -23.7, -2.2, 2.2, 17.7,
                Y_ETG + 0.05, 1.8)
    floor_planks(bur, "ParquetBureau", 2.2, 23.7, 2.2, 17.7,
                 Y_ETG + 0.05, base=C["walnut"], width=1.1)
    floor_tiles(hall, "SolCouloir", -2.2, 2.2, -17.7, 17.7,
                Y_ETG + 0.05, 1.5)

    # murs exterieurs etage
    f1 = [(-22.5, -12.0, Y_ETG + 1.0, 20.4, "win"),
          (-10.0, -3.0, Y_ETG + 0.0, 20.4, "slide"),
          (-1.5, 1.5, Y_ETG + 0.0, 20.4, "slide"),
          (3.0, 10.0, Y_ETG + 0.0, 20.4, "slide"),
          (12.0, 22.5, Y_ETG + 1.0, 20.4, "win")]
    b1 = [(-22.5, -12.0, Y_ETG + 1.0, 20.4, "win"),
          (-9.0, 9.0, Y_ETG + 1.0, 20.4, "win"),
          (12.0, 22.5, Y_ETG + 1.0, 20.4, "win")]
    l1 = [(-15.5, -5.0, Y_ETG + 1.0, 20.4, "win"),
          (5.0, 15.5, Y_ETG + 1.0, 20.4, "win")]
    r1 = l1
    wall(etg, "FacadeAvantEtage", "x", HZ, -HX, HX, Y_ETG, C_ETG, T,
         C["white"], "Concrete", f1, tag="EXT")
    wall(etg, "FacadeArriereEtage", "x", -HZ, -HX, HX, Y_ETG, C_ETG, T,
         C["white"], "Concrete", b1, tag="EXT")
    wall(etg, "MurOuestEtage", "z", -HX, -HZ, HZ, Y_ETG, C_ETG, T,
         C["white"], "Concrete", l1, tag="EXT")
    wall(etg, "MurEstEtage", "z", HX, -HZ, HZ, Y_ETG, C_ETG, T,
         C["white"], "Concrete", r1, tag="EXT")
    # bandeau bois de l'etage
    for k in range(20):
        part(etg, f"BardageEtage{k}", (-23.0 + k * 2.35, 16.5, 18.48),
             (2.2, 0.55, 0.14), jitter(C["woodmid"], 0.03), "Wood")

    # cloisons interieures de l'etage (croix centrale avec passages)
    for z0, z1 in ((-17.9, -12.0), (-8.0, -2.2), (2.2, 8.0), (12.0, 17.9)):
        for x in (-2.2, 2.2):
            wall_box(etg, f"CloisonX{x}_{z0}", "z", x, z0, z1,
                     Y_ETG, C_ETG, 0.35, C["white"], "SmoothPlastic", tag="PARTITION")
    for x0, x1 in ((-23.7, -13.0), (-9.0, -2.2), (2.2, 9.0), (13.0, 23.7)):
        for z in (-2.2, 2.2):
            wall_box(etg, f"CloisonZ{z}_{x0}", "x", z, x0, x1,
                     Y_ETG, C_ETG, 0.35, C["white"], "SmoothPlastic", tag="PARTITION")
    # encadrements de portes
    for x, z in ((-2.2, -10), (2.2, -10), (-2.2, 10), (2.2, 10),
                 (-11, -2.2), (11, -2.2), (-11, 2.2), (11, 2.2)):
        part(etg, f"Chambranle{x}_{z}", (x, Y_ETG + 4.0, z),
             (0.9, 8.0, 0.9), C["walnut"], "Wood", tag="PARTITION")

    ceiling(etg, "PlafondEtage", -23.9, 23.9, -17.9, 17.9, C_ETG + 0.18,
            hole=(-4.2, 4.2, -9.2, 5.2))
    downlights(cp, -21, -4, -15, -4, C_ETG - 0.15, step=6.0)
    downlights(ce, 4, 21, -15, -4, C_ETG - 0.15, step=6.0)
    downlights(sdb, -21, -4, 4, 15, C_ETG - 0.15, step=6.0)
    downlights(bur, 4, 21, 4, 15, C_ETG - 0.15, step=6.0)
    downlights(hall, -1, 1, -15, 15, C_ETG - 0.15, step=6.0)

    # --- chambre principale ----------------------------------------------
    rug(cp, "TapisChambre", -13.0, -9.0, Y_ETG + 0.14, 14.0, 10.0, C["cream"])
    bed(cp, "LitPrincipal", -13.0, -9.0, Y_ETG + 0.1, w=8.0, d=9.0,
        color=C["linen"], accent=C["bluegrey"])
    wardrobe(cp, "Dressing", -13.0, -17.0, Y_ETG + 0.05, w=12.0, h=8.6)
    artwork(cp, "TableauChambre", (-13.0, Y_ETG + 6.0, -17.2), 5.0, 2.6,
            colors=(C["sage"], C["cream"], C["bluegrey"], C["sand"]))
    armchair(cp, "FauteuilChambre", -6.0, -14.0, Y_ETG + 0.1, color=C["sage"])
    plant(cp, "PlanteChambre", (-21.0, Y_ETG + 0.1, -4.0), 2.4)
    part(cp, "ConsoleChambre", (-22.0, Y_ETG + 2.5, -9.0),
         (1.4, 0.25, 6.0), C["walnut"], "Wood")
    for k in range(3):
        part(cp, f"Objet{k}", (-22.0, Y_ETG + 2.8, -11 + k * 1.8),
             (0.8, 0.5, 0.8), RNG.choice([C["brass"], C["cream"], C["sage"]]),
             "Marble")

    # --- chambre enfant ---------------------------------------------------
    rug(ce, "TapisEnfant", 13.0, -9.0, Y_ETG + 0.14, 13.0, 9.0, C["sage"])
    bed(ce, "LitEnfant", 13.0, -9.0, Y_ETG + 0.1, w=6.6, d=8.0,
        color=C["white"], accent=C["terracotta"])
    wardrobe(ce, "ArmoireEnfant", 13.0, -17.0, Y_ETG + 0.05, w=9.0, h=8.0)
    bookshelf(ce, "EtagereEnfant", (22.0, Y_ETG + 3.5, -8.0), w=6.0, h=6.0)
    for k in range(4):
        ball(ce, f"Peluche{k}",
             (7.0 + k * 1.4, Y_ETG + 1.0, -4.0 + (k % 2) * 1.2), 1.2,
             RNG.choice([C["pink"], C["cream"], C["sage"], C["terracotta"]]),
             "Fabric")
    artwork(ce, "TableauEnfant", (13.0, Y_ETG + 6.0, -17.2), 4.0, 2.4,
            colors=(C["pink"], C["cream"], C["gold"]))

    # --- salle de bain ----------------------------------------------------
    bathroom(sdb, "SalleDeBainSpa", -23.0, -3.0, 3.0, 17.0, Y_ETG + 0.1)
    wardrobe(sdb, "MeubleLinge", -21.0, 15.8, Y_ETG + 0.05, w=5.0, h=7.0)
    rug(sdb, "TapisSDB", -13.0, 10.0, Y_ETG + 0.18, 6.0, 8.0, C["bluegrey"])

    # --- bureau / bibliotheque -------------------------------------------
    office(bur, "BureauMaison", 12.0, 10.0, Y_ETG + 0.1)
    bookshelf(bur, "Bibliotheque", (22.2, Y_ETG + 3.6, 10.0), w=9.0, h=7.5)
    sofa(bur, "CanapeBureau", 8.0, 15.5, Y_ETG + 0.1, w=7.0, d=3.2,
         color=C["navy"])
    rug(bur, "TapisBureau", 12.0, 10.0, Y_ETG + 0.14, 12.0, 10.0, C["sand"])
    plant(bur, "PlanteBureau", (4.0, Y_ETG + 0.1, 5.0), 2.6)
    artwork(bur, "TableauBureau", (12.0, Y_ETG + 6.0, 17.2), 5.0, 2.8,
            colors=(C["navy"], C["brass"], C["cream"]))

    # --- couloir ----------------------------------------------------------
    part(hall, "ConsoleCouloir", (0, Y_ETG + 2.4, -14.5), (3.0, 0.25, 1.2),
         C["walnut"], "Wood")
    plant(hall, "PlanteCouloir", (0.0, Y_ETG + 0.1, 14.0), 2.2)
    for k in range(3):
        pendant(hall, (0, C_ETG, -8.0 + k * 8.0), 3.0,
                shade=C["brass"], r=0.7)

    # --- balcon -----------------------------------------------------------
    part(balcon, "DalleBalcon", (0, Y_ETG - 0.1, 20.5), (47.0, 0.6, 5.5),
         C["stone"], "Marble", tag="SLAB")
    floor_planks(balcon, "PlatelageBalcon", -23, 23, 18.2, 23.0,
                 Y_ETG + 0.25, base=C["woodmid"], width=1.0)
    for k in range(24):
        x = -23 + k * 2
        part(balcon, f"GardeCorps{k}", (x, Y_ETG + 2.2, 23.1),
             (0.1, 3.6, 0.1), C["steel"], "Metal")
        p = part(balcon, f"VerreGarde{k}", (x + 1.0, Y_ETG + 2.2, 23.1),
                 (2.0, 3.4, 0.12), C["glass"], "Glass", tr=0.75,
                 collide=False, tag="GLASS")
    part(balcon, "LisseHaute", (0, Y_ETG + 4.0, 23.1), (47, 0.18, 0.25),
         C["steel"], "Metal")
    for s in (-1, 1):
        part(balcon, f"VerreCote{s}", (s * 23.2, Y_ETG + 2.2, 20.5),
             (0.12, 3.4, 5.0), C["glass"], "Glass", tr=0.75, collide=False,
             tag="GLASS")
    for x in (-15, 15):
        part(balcon, f"TableBalcon{x}", (x, Y_ETG + 1.8, 20.5),
             (2.6, 0.25, 2.6), C["steel"], "Metal")
        for s in (-1, 1):
            part(balcon, f"ChaiseBalcon{x}_{s}", (x + s * 2.2, Y_ETG + 1.4, 20.5),
                 (1.6, 0.28, 1.6), C["cream"], "Fabric")
            part(balcon, f"Dossier{x}_{s}", (x + s * 3.0, Y_ETG + 2.4, 20.5),
                 (0.22, 1.8, 1.6), C["cream"], "Fabric")
        plant(balcon, f"PlanteBalcon{x}", (x, Y_ETG + 0.3, 22.4), 1.8)

    # ==================================================================
    # TOITURE
    # ==================================================================
    for i, (a, b, c, d) in enumerate([
        (-25, -4.1, -19, 19), (4.1, 25, -19, 19),
        (-4.1, 4.1, -19, -9.1), (-4.1, 4.1, 5.1, 19),
    ]):
        part(toit, f"DalleToit{i}", ((a + b) / 2, ROOF - 0.4, (c + d) / 2),
             (b - a, 0.8, d - c), C["charcoal"], "Slate", tag="ROOF")
    for s in (-1, 1):
        part(toit, f"AcrotereX{s}", (s * 25.0, ROOF + 0.6, 0),
             (0.7, 2.0, 38.0), C["white"], "Concrete", tag="ROOF")
        part(toit, f"AcrotereZ{s}", (0, ROOF + 0.6, s * 19.0),
             (50.0, 2.0, 0.7), C["white"], "Concrete", tag="ROOF")
    # verriere
    part(toit, "Verriere", (0, ROOF + 0.15, -2.0), (8.0, 0.2, 14.0),
         C["glass"], "Glass", tr=0.7, collide=False, tag="ROOF")
    for k in range(6):
        part(toit, f"MontantVerriere{k}", (0, ROOF + 0.35, -8.0 + k * 2.4),
             (8.4, 0.2, 0.18), C["steel"], "Metal", tag="ROOF")
    # panneaux solaires
    for k in range(6):
        part(toit, f"PanneauSolaire{k}", (-18 + k * 6, ROOF + 0.4, 10.0),
             (5.4, 0.2, 7.0), C["navy"], "Glass", rot=(0, 0, 8), tag="ROOF")
        part(toit, f"CadreSolaire{k}", (-18 + k * 6, ROOF + 0.25, 10.0),
             (5.7, 0.12, 7.3), C["steel"], "Metal", tag="ROOF")
    # groupes de climatisation + cheminees
    for k in range(2):
        part(toit, f"Clim{k}", (14 + k * 4, ROOF + 1.0, -12.0),
             (3.0, 2.0, 2.4), C["warmwhite"], "Metal", tag="ROOF")
        for j in range(5):
            part(toit, f"Grille{k}_{j}", (12.6 + k * 4 + j * 0.6, ROOF + 1.0, -10.7),
                 (0.12, 1.4, 0.1), C["charcoal"], "Metal", tag="ROOF")
    part(toit, "SoucheCheminee", (-19.5, ROOF + 2.0, 3.0), (2.6, 4.0, 2.6),
         C["stone"], "Marble", tag="ROOF")
    # jardinieres de toiture
    for k, (x, z) in enumerate([(-20, 14), (-10, 15), (0, 15), (10, 15), (20, 14)]):
        part(toit, f"JardiniereToit{k}", (x, ROOF + 0.6, z), (4.0, 1.2, 3.0),
             C["terracotta"], "Sandstone", tag="ROOF")
        for j in range(3):
            ball(toit, f"BuissonToit{k}_{j}", (x - 1.2 + j * 1.2, ROOF + 1.6, z),
                 1.8, C["leaf"] if j % 2 else C["leaf2"], "Grass", tag="ROOF")
    for x in (-24.2, 24.2):
        for z in (-18, -9, 0, 9, 18):
            glowing_bulb(toit, f"LEDToit{x}_{z}", (x, ROOF - 0.1, z),
                         (0.3, 0.12, 1.2), C["neon"], range_=8, brightness=0.4)

    # ==================================================================
    # INTERRUPTEURS (cliquables en jeu)
    # ==================================================================
    for name, pos, rot in [
        ("Salon", (-4.6, 5.4, 7.0), (0, 90, 0)),
        ("Cuisine", (4.6, 5.4, 5.0), (0, 90, 0)),
        ("SalleAManger", (4.6, 5.4, 11.0), (0, 90, 0)),
        ("ChambrePrincipale", (-2.6, 16.0, -6.0), (0, 90, 0)),
        ("ChambreEnfant", (2.6, 16.0, -6.0), (0, 90, 0)),
        ("SalleDeBain", (-2.6, 16.0, 8.0), (0, 90, 0)),
        ("Bureau", (2.6, 16.0, 8.0), (0, 90, 0)),
        ("Jardin", (-3.4, 5.4, 18.9), (0, 0, 0)),
    ]:
        switch(inter, pos, name, rot)

    roots = [ws, lighting, Node("ReplicatedStorage", "ReplicatedStorage"), sss,
             Node("StarterPlayer", "StarterPlayer"), Node("StarterGui", "StarterGui")]
    return roots


SCRIPT_SOURCE = r"""-- MaisonRealiste - interactions
-- Clique sur un interrupteur pour allumer/eteindre les lumieres de la piece.
local house = workspace:WaitForChild("MaisonRealiste")
local switches = house:FindFirstChild("Interrupteurs")
if not switches then return end

local function lightsIn(root)
    local found = {}
    for _, d in ipairs(root:GetDescendants()) do
        if d:IsA("Light") then table.insert(found, d) end
    end
    return found
end

for _, sw in ipairs(switches:GetChildren()) do
    local cd = sw:FindFirstChildOfClass("ClickDetector")
    local tag = sw:FindFirstChild("Room")
    if cd and tag then
        local room = house:FindFirstChild(tag.Value, true)
        if room then
            local bulbs = lightsIn(room)
            local on = true
            cd.MouseClick:Connect(function()
                on = not on
                for _, l in ipairs(bulbs) do l.Enabled = on end
                if sw:IsA("BasePart") then
                    sw.Color = on and Color3.fromRGB(240, 236, 225)
                                  or Color3.fromRGB(58, 60, 62)
                end
            end)
        end
    end
end
"""


def main():
    roots = build()
    write_place(OUT, roots)
    with open(BOXJSON, "w", encoding="utf-8") as fh:
        json.dump(BOXES, fh)
    import xml.etree.ElementTree as ET
    tree = ET.parse(OUT)
    items = tree.findall(".//Item")
    props = tree.findall(".//Properties")
    assert tree.getroot().tag == "roblox"
    assert len(items) == len(props), "un <Properties> par <Item> requis"
    print(f"OK -> {os.path.basename(OUT)}")
    print(f"    {len(items):,} instances | {len(BOXES):,} parties | "
          f"{os.path.getsize(OUT) / 1024:.0f} Ko")


if __name__ == "__main__":
    main()
