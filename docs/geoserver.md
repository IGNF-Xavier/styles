# Ce qu'il faut installer/configurer côté GeoServer

Ce document s'adresse à l'administrateur GeoServer : qu'installer, qu'activer, et
pourquoi — pour que les SLD et MBStyle produits par cet outil se comportent
réellement comme prévu une fois déployés, pas seulement en théorie.

## 1. SLD 1.0.0 — rien à installer

Les fichiers `.sld` produits (`examples/sld/*.sld`) sont du SLD 1.0.0
standard, avec des extensions GeoServer volontaires (`<VendorOption>`,
marques `shape://...`, `ttf://...`) que GeoServer sait lire nativement
depuis sa version historique — **aucune extension à installer** pour le
SLD seul. Un GeoServer "stock" (sans plugin) suffit.

Les `<VendorOption>` injectées par l'outil (voir `AUDIT_VENDOR` dans
`cnig_qml2sld_geoserver.py`) et reconnues par GeoServer sans configuration
supplémentaire :

| Portée | Options |
|---|---|
| `PolygonSymbolizer` + `GraphicFill` (hachures/motifs) | `graphic-margin`, `graphic-resize`, `graphic-margin-top`, `random`, `random-seed`, `random-tile-size`, `random-symbol-count`, `random-rotation`, `composite`, `composite-base`, `sortBy`, `sortByGroup` |
| Étiquetage (`TextSymbolizer`), toutes géométries | `group`, `spaceAround`, `maxDisplacement`, `conflictResolution`, `goodnessOfFit`, `partials`, `autoWrap`, `labelObstacle`, `inclusion`, `labelAllGroup`, `forceLeftToRight`, `allGroup`, `underlineText`, `strikethroughText`, `charSpacing`, `wordSpacing`, `displacementMode`, `fontShrinkSizeMin` |
| Étiquetage le long d'une ligne | `followLine`, `repeat`, `maxAngleDelta` |
| Étiquetage sur surface | `polygonAlign` |

Une `VendorOption` absente de ce tableau est **ignorée silencieusement par
le moteur de rendu de GeoServer lui-même** (ce n'est pas une limite de cet
outil) — PHASE 6 de l'outil (`GeoServerAuditor`) le signale explicitement
dans son rapport avant publication, plutôt que de laisser découvrir le
problème au rendu.

Les marques `shape://...` (hachures, croix, étoiles) sont du vocabulaire
WellKnownName GeoServer natif — pas d'extension requise.

### Marques de police (`ttf://<Police>#0x<hex>`)

GeoServer sait tracer nativement une marque `ttf://<NomPolice>#0x<codepoint>`
en `WellKnownName` d'un `Graphic` **si la police nommée est installée sur
le système qui exécute GeoServer** (ni le SLD, ni GeoServer, n'embarquent la
police — c'est une dépendance système, au même titre qu'une police système
pour du texte). Si la police n'est pas installée côté serveur, GeoServer
retombe sur son glyphe de substitution par défaut sans erreur bloquante —
un risque de rendu silencieusement différent qu'il faut vérifier
manuellement après déploiement (voir `docs/limites.md`, section police).

## 2. MBStyle (Mapbox GL Style JSON) — extension à installer

Les fichiers `.json` produits (`examples/mbstyle/*.json`) utilisent le
module **MBStyle**, une extension GeoServer **non incluse dans
l'installation de base** :

1. Télécharger `geoserver-<version>-mbstyle-plugin.zip` correspondant
   **exactement** à la version de GeoServer installée (un décalage de
   version, même mineur, empêche le chargement du module au démarrage) —
   voir https://docs.geoserver.org/main/en/user/styling/mbstyle/installing.html
2. Extraire les deux JAR de l'archive dans `WEB-INF/lib` de l'instance
   GeoServer (webapp déployée, ou répertoire `webapps/geoserver/WEB-INF/lib`
   selon le mode d'installation).
3. Redémarrer GeoServer.
4. Vérifier : dans l'éditeur de styles GeoServer, le format "MBStyle"
   doit apparaître comme option à la création/import d'un style — c'est la
   seule preuve fiable que le module a bien été chargé (une absence
   silencieuse dans la liste des formats, sans message d'erreur explicite
   au démarrage, est le symptôme le plus courant d'un décalage de version).

### Sprites (pictogrammes et motifs référencés par `"sprite"`)

Un document MBStyle qui référence des pictogrammes (`sprite.png` /
`sprite@2x.png` + leurs index `sprite.json` / `sprite@2x.json`, produits
dans `examples/sprites/`) a besoin que ces 4 fichiers soient déposés dans
le répertoire de données GeoServer et servis par l'URL que le champ
`"sprite"` du document désigne — convention observée (et reprise par cet
outil, voir `MbStyleOptions.resolved_sprite_url()`) :

```
{base_url}/geoserver/styles/sprite        (ou /styles/{workspace}/sprite)
```

c'est-à-dire **sans** le segment `/rest/` (ce segment n'existe que pour
l'API REST de gestion des styles, pas pour le service statique des
ressources d'un style). Cette convention est corroborée par l'exemple
officiel GeoCat (`"sprite": "http://localhost:8080/geoserver/styles/sprites"`,
https://docs.geocat.net/map/2024/styling/workshop/mbstyle/mbstyle.html) ;
elle n'est en revanche pas explicitement documentée dans la page REST API
de GeoServer elle-même (qui ne couvre que le pattern différent
`/rest/styles/{name}.{format}`) — à vérifier concrètement sur votre
instance (requête `GET` directe sur l'URL du sprite) avant mise en
production, plutôt que de la tenir pour acquise sans contrôle.

Concrètement : déposer les 4 fichiers de `examples/sprites/` (en
remplaçant par ceux produits pour votre propre corpus) au même niveau que
les fichiers de style dans le répertoire de données GeoServer
(`<data_dir>/styles/`), puis renseigner `--mbstyle-base-url` (et
`--mbstyle-workspace` si le style est publié dans un workspace) lors de la
conversion pour que le champ `"sprite"` du JSON produit pointe vers la
bonne URL dès la génération — voir le README, section « Utilisateur CLI »,
tableau des options utiles.

### Glyphes de police non rasterisés (`sprite_glyphes_a_generer.json`)

Mapbox GL Style n'a pas de notion de police native pour un symbole ponctuel
(contrairement à SLD/`ttf://`) : l'outil rasterise donc chaque glyphe de
police (`FontMarker` QGIS) comme une vignette bitmap dans la feuille de
sprites, à la génération. Si l'environnement qui génère les sprites n'a
pas de plate-forme Qt graphique disponible (poste serveur sans affichage),
l'outil **n'invente pas un rendu approximatif** : il exclut ces glyphes de
la feuille de sprites produite et les liste explicitement dans
`sprite_glyphes_a_generer.json` (voir `examples/sprites/`), avec un
avertissement. Ces glyphes doivent être régénérés sur un poste où la
police concernée est réellement installée et où Qt peut créer une fenêtre
(même hors écran, via `QT_QPA_PLATFORM=offscreen`) — typiquement le poste
de production/bureau du cartographe, pas nécessairement le serveur
GeoServer lui-même.

## 3. `PropertyIsLike` et `matchCase`

Les filtres littéraux QGIS sensibles à la casse (ex. `strMatches` avec un
indicateur insensible à la casse, `ILIKE`) sont traduits en
`<PropertyIsLike matchCase="false" .../>` — `matchCase` est une extension
GeoServer au vocabulaire Filter 1.0 (absente du schéma XSD strict). Un
moteur WFS/WMS strictement conforme à Filter 1.0 et non-GeoServer
ignorerait cet attribut ; GeoServer le respecte nativement, aucune
installation supplémentaire requise. PHASE 6 de l'outil (`GeoServerAuditor`)
consigne cette extension dans son rapport (catégorie "extensions GeoServer
présentes") pour qu'elle reste visible, plutôt que tue, même si elle n'est
pas un défaut.

## 4. Récapitulatif pour une mise en production

| Besoin | Obligatoire pour | Action |
|---|---|---|
| Rien (SLD "nu", pas de hachures/police) | SLD basique | — |
| Police installée côté OS serveur | `WellKnownName` `ttf://...` en SLD | Installer la police système concernée |
| Module MBStyle | Tout fichier `.json` produit | JAR du plugin version-matchée + redémarrage |
| 4 fichiers sprite déposés + URL correcte | MBStyle avec pictogrammes/motifs | Copier dans `<data_dir>/styles/`, vérifier l'URL servie |
| Glyphes régénérés sur poste avec Qt+police | Glyphes listés dans `sprite_glyphes_a_generer.json` | Relancer la génération sprite sur un tel poste |
