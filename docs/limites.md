# Limites connues et contournements

Principe du projet, rappelé ici parce qu'il détermine toute la lecture de
ce document : **jamais d'échec silencieux**. Chaque limite ci-dessous est
soit détectée et signalée explicitement (exception nommée, avertissement,
fichier d'index séparé), soit contournée par un mécanisme documenté — rien
n'est tû ni approximé sans le dire.

## 1. Expressions QGIS traduites en Mapbox GL (`strMatches` / `ILIKE`)

Mapbox GL Style n'a pas d'opérateur d'expression regex générique. L'outil
traduit les formes **canoniques** suivantes (vers des opérateurs natifs
`@maplibre/maplibre-gl-style-spec`, pas une approximation) :

| Forme QGIS | Expression Mapbox GL produite |
|---|---|
| égalité exacte | `["==", champ, litteral]` |
| préfixe (`^motif.*$`) | `["==", ["slice", champ, 0, n], litteral]` |
| suffixe (`^.*motif$`) | `["==", ["slice", champ, ["-", ["length", champ], n]], litteral]` |
| contient (substring) | `["in", litteral, champ]` (forme substring native de `in`) |

Exemple réel du corpus (ASSIETTE_SUP_S, règle sur le champ
`CODE_SUP`, motif `(?i)^a1\-.*$`) : traduit en préfixe insensible à la
casse via les 4 formes ci-dessus combinées à une normalisation de casse
amont — voir `cnig_qml2sld_geoserver.py`, PHASE 5.

**Hors champ, lève une exception nommée plutôt que d'approximer** :
motifs multi-segments (plusieurs groupes variables dans le même motif) et
le joker `_` (caractère unique) de `LIKE`/`ILIKE`, qui n'ont pas
d'équivalent composable dans les opérateurs Mapbox GL ci-dessus sans
risque de faux positifs/négatifs. Si votre style utilise l'un de ces
motifs, la conversion MBStyle de la règle concernée échoue explicitement
(`ExpressionPivotNonEcrite`) — contournement : réécrire la règle QGIS
source avec un motif canonique équivalent, ou traiter la couche
séparément pour le SLD (non concerné par cette limite) et accepter
l'absence de MBStyle pour cette règle précise.

## 2. Marques de police (`FontMarker`, ex. `ttf://Wingdings#0x00f1`)

- **SLD** : traduit nativement en `WellKnownName` `ttf://<Police>#0x<hex>`
  — GeoServer sait le tracer si la police est installée côté serveur (voir
  `docs/geoserver.md`, section police). Risque de substitution de glyphe
  silencieuse par GeoServer lui-même si la police est absente côté
  serveur — à vérifier visuellement après déploiement, l'outil ne peut
  pas le détecter à la génération.
- **MBStyle** : Mapbox GL n'a aucune notion de police pour un symbole
  ponctuel. L'outil rasterise donc chaque glyphe en vignette bitmap dans
  la feuille de sprites, à la génération — mais seulement si
  l'environnement de génération dispose d'une plate-forme Qt graphique
  utilisable. Si ce n'est pas le cas (poste serveur sans affichage), les
  glyphes concernés sont **exclus explicitement** (pas rendus
  approximativement) et listés dans `sprite_glyphes_a_generer.json`, avec
  un avertissement — contournement : régénérer la feuille de sprites sur
  un poste où Qt peut créer une fenêtre (y compris hors écran, via
  `QT_QPA_PLATFORM=offscreen`) et où la police voulue est installée.

## 3. Ressources externes (images SVG embarquées, sprites) côté API synchrone et plugin QGIS

La route `POST /v1/convert` de styleforge-api (phase 6) n'a, dans cette
première itération, aucun service de résolution de ressources externes :
un QML dont un symbole référence une image SVG embarquée en base64, ou
dont un `graphicFill`/`graphicStroke` a besoin d'un sprite, produit
l'exception nommée correspondante (`ExpressionPivotNonEcrite`), remontée
en HTTP 422 — jamais un document silencieusement incomplet. Contournement
actuel : utiliser le CLI (`cnig_qml2sld_geoserver.py`), qui résout ces
ressources localement, pour tout style qui en dépend ; lever cette limite
côté API est un chantier séparé (résolveur de ressources par requête, ou
stockage d'assets côté service).

L'extension QGIS (`qgis-plugin/`) couvre un sous-ensemble de ce que
résout le CLI : les SVG **embarqués en base64** (la quasi-totalité du
corpus CNIG réel) SONT décodés et déployés côté SLD — vérifié
empiriquement contre une vraie installation QGIS 3.40, cela fait passer
le taux de réussite SLD du corpus d'exemples de 4/17 à 17/17. Restent
hors de portée du plugin, comme pour l'API : un SVG référencé par un
chemin de fichier (pas embarqué), et tout sprite MBStyle
(pictogramme/motif pour le document Mapbox) — même message d'échec
explicite, même contournement (le CLI).

## 4. `matchCase` sur `PropertyIsLike` — extension GeoServer

Les filtres sensibles/insensibles à la casse sont traduits avec l'attribut
`matchCase`, qui est une extension GeoServer au vocabulaire Filter 1.0
strict (absente du schéma XSD officiel). PHASE 6 de l'outil (audit) le
consigne comme "extension GeoServer présente" plutôt que comme un défaut
— mais un moteur WFS/WMS non-GeoServer strictement conforme Filter 1.0
ignorerait cet attribut. Sans contournement nécessaire sur GeoServer ;
pertinent seulement si le SLD/filtre produit doit être réutilisé en dehors
de GeoServer.

## 5. Pourquoi SLD 1.0.0 et pas SLD/SE 1.1.0

Choix délibéré, pas un oubli : il n'existe pas vraiment de "SLD 1.1.0"
unique à viser. Après SLD 1.0.0 (2005), l'OGC a scindé ce périmètre en
deux spécifications distinctes, toutes deux numérotées 1.1.0 :
**Symbology Encoding (SE) 1.1.0** (les symbolizers) et le **profil SLD de
WMS 1.1.0** (le branchement sur `GetMap`). La documentation GeoServer le
dit explicitement : *"GeoServer implements the SLD 1.0.0 standard, as
well as some parts of the SE 1.1.0 and WMS-SLD 1.1.0 standards."*
(https://docs.geoserver.org/main/en/user/styling/sld/reference/index.html)
— support partiel et non détaillé, et ni l'éditeur de styles GeoServer ni
son API REST n'exposent SE 1.1.0 comme format sélectionnable au même
titre que SLD, CSS, YSLD ou MBStyle.

Deuxième raison, propre à ce projet : l'écrivain SLD est vérifié contre
`QgsVectorLayer.loadSldStyle()`/`saveSldStyle()` de QGIS, qui sert
d'**oracle de test** (voir le docstring de
`styleforge_core/writers/sld.py`) — et qui ne lit/écrit que du SLD 1.0.0.
Viser SE 1.1.0 supprimerait le seul moyen de vérifier objectivement la
sortie produite, contraire au principe du projet (jamais d'approximation
non vérifiée). SLD 1.0.0 reste donc la cible la plus solide des options
disponibles : support GeoServer complet, oracle QGIS disponible, écosystème
réel — contrairement à SE 1.1.0, partiellement supporté et sans moyen de
vérification indépendant.

## 6. Oracle PyQGIS — limite de l'oracle, pas du format cible

Historique utile pour comprendre le tableau de la section 1 ci-dessus :
certaines limites initialement attribuées au format MBStyle lui-même (ex.
`strMatches`) se sont révélées être des limites du convertisseur
`QgsMapBoxGlStyleConverter` de QGIS — utilisé comme **oracle de test**
dans ce projet, jamais comme dépendance d'exécution — et non du format
Mapbox GL Style en lui-même. Quand un tel écart apparaît, la vérification
se fait contre la spécification de référence
(`@maplibre/maplibre-gl-style-spec`), pas contre l'oracle seul, avant de
conclure à une impossibilité structurelle.

## 7. Portée du corpus de test

Testé et validé sur les 17 fichiers `.qml` officiels CNIG GPU
(familles PLU, PSMV, SUP — voir `examples/SOURCES.md`), produits pour
QGIS 3.44 LTR : **17/17 convertis avec succès en SLD 1.0.0 et en Mapbox GL
Style**, 0 échec, audité conforme GeoServer. Un style QGIS en dehors de ce
corpus (version QGIS différente, symbologie non couverte par ces 17
exemples) peut rencontrer une expression ou un type de symbole non géré —
dans ce cas, l'outil lève une exception nommée ou ajoute un avertissement
explicite plutôt que de produire un document approximé ; se référer au
nom de l'exception pour identifier précisément la construction QGIS en
cause.
