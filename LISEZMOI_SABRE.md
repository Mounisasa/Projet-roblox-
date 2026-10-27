# SabreLaser_Combat.rbxlx

Fichier de place Roblox autonome — **ouvrir directement dans Roblox Studio**
(*Fichier → Ouvrir à partir d'un fichier…*), puis **F5 / Play**.

Aucun asset externe, aucun plugin, aucune dépendance. Tout est dans le `.rbxlx`.

## Contrôles (clavier + souris uniquement)

| Touche | Action |
|---|---|
| **Q** | Dégainer / rengainer la poignée |
| **E** | Allumer / éteindre la lame |
| **Clic gauche** | Attaque (combo de 10) |
| **Clic droit (maintenir)** | Garde / parade |

Le menu de départ permet de choisir la couleur de la lame (8 couleurs ou saisie RVB
libre), synchronisée serveur via `RemoteFunction`, puis le bouton **DÉPLOYER**
crée physiquement le personnage.

## Ce qui est dedans

- **Workspace** : uniquement la Baseplate native + Terrain + Camera + SpawnLocation.
- **Rig** : `Players.CharacterAutoLoads = false`. `RigSpawner` force un R15 blocky
  via `HumanoidDescription` (meshes par défaut = 0) et verrouille les échelles
  (`BodyTypeScale`/`ProportionScale` = 0, largeur/hauteur/profondeur/tête = 1),
  sur `PlayerAdded`, `CharacterAdded` et `CharacterAppearanceLoaded`.
- **Sabre** : modèle physique de 11 pièces usinées (Metal / DiamondPlate / Neon),
  10 `Motor6D`, 2 `Attachment` + `Trail`, `PointLight`, 5 `Sound` avec effets
  (Tremolo / Distortion / Equalizer pour le bourdonnement). Trois états stricts :
  `Holstered` → `Drawn` → `Ignited`, avec réassignation du `Motor6D` sur la hanche
  puis sur `RightHand` via le `RightGripAttachment`.
- **Animations** : 20 `KeyframeSequence` (10 attaques + 10 déflexions) déjà
  instanciées dans `ReplicatedStorage/Animations`, doublées d'un lecteur
  procédural qui interpole les `Motor6D` R15.
- **Combat** : 100 d'endurance, combo de 10 avec remise à zéro après 3 s
  (`RunService` + `os.clock`), garde à −5 endurance, parade parfaite dans une
  fenêtre de 0,2 s (0 perte, −20 et recul pour l'attaquant), 3 conditions létales
  (pas de garde, rupture de garde à 0, frappe dorsale par produit scalaire > 0,3).
  Détection par raycast serveur entre les extrémités de la lame.
- **Réseau** : 5 remotes + un bus `BindableEvent` interne pour les statistiques
  (`leaderstats` : Kills, Deaths, Parries, Blocks, Backstabs).
- **UI** : menu principal (caméra fixe + flou), HUD complet (endurance, combo,
  état du sabre, garde, flash, kill feed, overlay de mort).

## Arborescence des scripts

```
ReplicatedStorage/Config/CombatConfig          (ModuleScript)
ReplicatedStorage/Config/BlockyR15Description  (HumanoidDescription)
ReplicatedStorage/Modules/InputPolicy          PC clavier/souris strict
ReplicatedStorage/Modules/SaberStateMachine    3 états
ReplicatedStorage/Modules/AnimationLibrary    20 pistes + lecteur procédural
ReplicatedStorage/Modules/SaberFactory        assemblage, soudure, allumage
ReplicatedStorage/Remotes/*                    5 remotes + protocole documenté
ReplicatedStorage/Assets/SaberTemplate
ReplicatedStorage/Animations/Attack_1..10 / Deflect_1..10
ServerScriptService/ServerState               état autoritaire partagé
ServerScriptService/RigSpawner                spawn + forçage R15 blocky
ServerScriptService/SaberService              machine à états du sabre
ServerScriptService/CombatServer              moteur de combat
ServerScriptService/RemoteHandlers            couleur + déploiement
ServerScriptService/CombatLogger              statistiques
StarterPlayer/StarterPlayerScripts/CombatClient
StarterGui/MainMenu/MenuController
StarterGui/CombatHUD/HUDController
```

## Validation effectuée

- 1 205 instances, 23 services racine, 15 scripts, ~640 Ko.
- Un seul `<Properties>` par `<Item>`, referents uniques, aucune `Ref` orpheline.
- **4 490 propriétés** vérifiées une à une contre le dump API Roblox officiel
  (classes, héritage, noms, types) : 0 inconnue, 0 type incorrect.
- Rotations `CFrame` toutes orthonormales (déterminant = 1).
- Les 15 sources Luau passent le parseur `luau-parser` sans erreur.
- Tous les `Enum.*` et appels d'API utilisés existent dans le dump.

## Régénérer

```bash
python3 tools/combat/build.py
```
