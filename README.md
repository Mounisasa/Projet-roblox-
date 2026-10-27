# Projet Roblox — Maison réaliste

Ce dépôt contient **`MaisonRealiste.rbxlx`** : une villa contemporaine de deux
niveaux, entièrement meublée, générée directement au format XML officiel de
Roblox (`.rbxlx`, version 4).

> Le fichier `SakuraKatana_FreeCombat.rbxlx` présent dans le dépôt est l'ancien
> brouillon. Il n'est **pas** un vrai fichier Roblox valide (plusieurs blocs
> `<Properties>` par objet, CFrame en JSON, etc.) — Studio refusera de l'ouvrir.
> Utilise `MaisonRealiste.rbxlx`.

---

## Installer / ouvrir

1. Télécharge **`MaisonRealiste.rbxlx`**.
2. Ouvre **Roblox Studio** → *File / Fichier* → **Open from File… / Ouvrir à partir d'un fichier…**
3. Sélectionne le fichier. La villa apparaît dans l'Explorer sous
   `Workspace > MaisonRealiste`.
4. Pour jouer : **Play (F5)**. Pour la publier sur ton compte :
   *File → Publish to Roblox*.

Aucun asset externe, aucun plugin, aucune dépendance : tout est fait avec des
`Part`, des matériaux Roblox natifs et des lumières.

---

## Ce qu'il y a dedans

**3 806 instances — 3 465 pièces.**

### Rez-de-chaussée
- **Salon** : canapé 4 places + coussins, 2 fauteuils, table basse (livres, vase,
  fleurs), grand écran + meuble TV + barre de son, cheminée avec feu, tapis,
  bibliothèque garnie, coin lecture, plantes, tableaux, lustre.
- **Cuisine** : caissons hauts et bas, plan de travail en marbre, crédence
  carrelée, évier + robinetterie, plaque 4 foyers, four, hotte, réfrigérateur
  américain, îlot central avec 4 tabourets, 3 suspensions, épices, fruits.
- **Salle à manger** : table 8 personnes, 8 chaises, sets de table, assiettes,
  verres, centre de table fleuri, lustre.
- **Entrée** : console, miroir doré, vide-poches, plante, 3 suspensions.
- **WC invités**, **escalier** en bois de 22 marches avec rampe et balustres.

### Étage
- **Chambre principale** : lit king size (tête de lit capitonnée, couette,
  oreillers, plaid), 2 chevets + lampes, dressing 4 portes, fauteuil, tapis.
- **Chambre d'enfant** : lit, armoire, étagère, peluches, tableau.
- **Salle de bain spa** : baignoire îlot, douche à l'italienne avec parois en
  verre et pomme de pluie, double vasque + miroirs rétroéclairés, WC, faïence,
  serviettes.
- **Bureau / bibliothèque** : bureau, écran, clavier, souris, fauteuil,
  bibliothèque remplie de livres, canapé, tapis.
- **Couloir** en croix, **balcon** filant avec garde-corps en verre, salon de
  jardin et jardinières.

### Extérieur
- Piscine carrelée avec eau translucide, margelles, échelle et éclairages
  immergés, grande terrasse en platelage bois, 2 transats, 2 parasols,
  cuisine d'été / barbecue.
- Garage fermé avec voiture, étagères et éclairage néon, allée béton.
- Porche à colonnes, marches, auvent bois, appliques, jardinières.
- Allée pavée, bornes lumineuses, massifs fleuris, 10 arbres (dont cerisiers),
  haies, clôture en lames de bois.
- Toiture terrasse : verrière, 6 panneaux solaires, groupes de climatisation,
  souche de cheminée, jardinières, acrotères et LED de contour.
- Éclairage cinématique : lumière dorée de fin de journée, atmosphère, bloom,
  rayons de soleil, étalonnage des couleurs, 143 sources lumineuses.

### Interactions
Des **interrupteurs cliquables** (dans `MaisonRealiste > Interrupteurs`)
allument ou éteignent les lumières de la pièce correspondante : Salon, Cuisine,
SalleAManger, ChambrePrincipale, ChambreEnfant, SalleDeBain, Bureau, Jardin.
Le script se trouve dans `ServerScriptService > ControlesMaison`.

---

## Aperçus

- `apercu.png` — vue extérieure + coupe de l'intérieur.
- `apercu_piscine.png` — façade arrière, piscine et terrasse.

Ces images sont des rendus isométriques générés à partir de la géométrie du
`.rbxlx` (pas des captures de Studio).

---

## Régénérer / modifier

```bash
python3 tools/build_house.py              # reconstruit MaisonRealiste.rbxlx
python3 -m pip install Pillow
python3 tools/preview.py                  # régénère les aperçus
```

- `tools/rbxlx.py` — sérialiseur XML Roblox v4 (types, enums, CFrame, couleurs).
- `tools/house_lib.py` — bibliothèque de construction (murs à ouvertures,
  parquets, carrelages, meubles, végétation, piscine…).
- `tools/build_house.py` — assemblage de la villa, du jardin et des scripts.
- `tools/preview.py` — rendu d'aperçu sans Roblox Studio.

Toute la géométrie est décrite en Python : changer une cote ou une couleur
puis relancer `build_house.py` suffit.
