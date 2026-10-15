# Registre des écarts connus — QGIS ↔ GeoServer ↔ MBStyle

Ce registre répond au constat central du retex « interopérabilité des
styles QGIS / GeoServer » (recommandation n°2) : sans mémoire partagée des
écarts déjà rencontrés, chaque projet IGN qui touche à l'export de styles
QGIS vers SLD/MBStyle/GeoServer redécouvre les mêmes limites. Ce document
est ce registre. Il vit dans ce dépôt mais n'est pas spécifique à
styleforge-core : la section A couvre l'écosystème en général, la section
B isole ce qui est propre à ce projet.

**Mise à jour** : quand un projet IGN rencontre un nouvel écart QGIS,
GeoServer ou MBStyle non listé ici, l'ajouter (même sans solution), avec
sa source. Ne jamais retirer une ligne parce qu'elle semble ancienne —
noter son statut à jour plutôt.

## Comment lire ce registre

**Catégorie** (voir `docs/limites.md` section 0 pour la grille complète
avec exemples de code) :

- **Hors périmètre actuel** — un équivalent existe en principe dans le
  format cible, ce n'est juste pas (encore) implémenté/exporté.
- **Limite structurelle** — le format cible n'a, dans sa spécification,
  aucun moyen de représenter la construction.
- **Contrainte d'environnement** — ni le format ni l'outil ne sont en
  cause, c'est la plate-forme d'exécution qui manque d'une capacité.
- **Choix produit / organisationnel** — pas un bug, une décision
  (ex. GeoServer qui propose 4 langages de style sans trancher).

**Statut** : Ouvert (ticket amont existant) · Ouvert (sans ticket amont,
à déposer) · Fermé / corrigé · Statut incertain (à revérifier) · Contourné
dans styleforge-core.

## A. Écarts génériques de l'écosystème

| # | Lacune | Côté | Catégorie | Ticket amont | Statut | Référence |
|---|---|---|---|---|---|---|
| A1 | L'export SLD ne reporte pas les propriétés pilotées par attribut/expression (couleur, taille… calculées en QML) | QGIS | Hors périmètre | [QGIS #23356](https://github.com/qgis/QGIS/issues/23356) | Ouvert | tracker QGIS |
| A2 | Aucun support de la labellisation par règles (« rule-based labeling ») dans l'export SLD | QGIS | Hors périmètre | [QGIS #27752](https://github.com/qgis/QGIS/issues/27752) | Ouvert (demande de fonctionnalité) | tracker QGIS |
| A3 | L'export d'une expression de label utilisant `concat` vers SLD échoue | QGIS | Limite structurelle (le `TextSymbolizer` SLD n'a pas de mécanisme pour des fonctions d'expression arbitraires) | [QGIS #64778](https://github.com/qgis/qgis/issues/64778) | Fermé « not planned » — confirme qu'aucune correction n'est prévue | tracker QGIS |
| A4 | Des styles SLD ne peuvent pas être chargés pour des couches raster (reliquat, malgré l'ajout d'un support raster SLD en 3.6) | QGIS | Hors périmètre / régression partielle | [QGIS #36347](https://github.com/qgis/QGIS/issues/36347) (ouvert) ; contexte : [QGIS #18136](https://github.com/qgis/QGIS/issues/18136) (fermé, implémenté en 3.6) | Ouvert malgré #18136 | tracker QGIS |
| A5 | L'export SLD omet `Displacement` dans `PointPlacement` pour un label décalé | QGIS | Hors périmètre, correctif partiel déjà livré | [QGIS #36466](https://github.com/qgis/QGIS/issues/36466) | Ouvert ; un commentaire de 2024 indique un correctif partiel déjà intégré — à revérifier sur la version QGIS cible avant de considérer l'écart clos | tracker QGIS |
| A6 | La règle « ELSE » (règle par défaut) ne s'exporte pas en SLD, rendant le style inutilisable au rechargement | QGIS | Hors périmètre | [QGIS #25689](https://github.com/qgis/QGIS/issues/25689) | Statut incertain (signalé comme possible doublon de #22172 par un mainteneur, non confirmé) | tracker QGIS |
| A7 | **Mode de fusion de couche (« Blend mode » / « Feature blend mode ») et opacité de couche silencieusement absents de l'export SLD** | QGIS | Limite structurelle probable côté SLD officiel (pas de notion de compositing dans SLD/SE), contournable via le VendorOption GeoServer `composite`/`composite-base` | **Aucun ticket trouvé** | **Ouvert, sans ticket — vérifié empiriquement le 2026-10-15 sur QGIS 3.40.4-Bratislava (voir section C) — à déposer** | voir section C |
| A8 | VendorOptions de labellisation GeoServer incomplètes par rapport aux capacités QGIS (halos, callouts avancés) | GeoServer | Choix produit / limite structurelle de l'implémentation GeoServer | — (tracker GeoServer, hors périmètre de la demande « tickets QGIS ») | Ouvert, non suivi par un ticket précis identifié | [doc GeoServer labelling](https://docs.geoserver.org/main/en/user/styling/sld/reference/labeling.html) |
| A9 | GeoServer propose 4 langages de style (SLD/CSS/YSLD/MBStyle) sans politique officielle sur lequel privilégier | GeoServer | Choix produit / organisationnel | n/a | Constat durable, pas un bug | retex, recommandation n°3 |
| A10 | Absence (avant ce document) de registre neutre des écarts QGIS↔GeoServer | Écosystème | — | n/a | Résolu par ce document, à l'échelle IGN ; seul équivalent externe identifié : la matrice commerciale GeoCat Bridge | [GeoCat Bridge — symbologie supportée](https://docs.geocat.net/bridge/qgis/v4.2/supported_symbology.html) |

Note sur A4/A5 : plusieurs de ces tickets portent des commentaires
indiquant un correctif partiel déjà intégré (parfois en 2024). Avant de
les citer comme preuve d'un écart actuel dans un document destiné à un
tiers, revérifier sur la version QGIS réellement utilisée — un ticket
« ouvert » sur le tracker ne garantit pas que le comportement observé
initialement persiste intégralement.

## B. Écarts spécifiques à styleforge-core

Détail technique complet dans `docs/limites.md` — résumé ici pour la vue
d'ensemble :

| # | Lacune | Catégorie (docs/limites.md) | Statut |
|---|---|---|---|
| B1 | `strMatches`/`ILIKE` à plusieurs segments ou au joker `_` non traduit en MBStyle | Hors périmètre actuel (§1) | Contourné : exception nommée explicite, pas d'approximation |
| B2 | Opérateur `'*='` (LIKE générique) non traduit en MBStyle | Limite structurelle confirmée (§1) | Permanent, sauf évolution de la spec Mapbox GL |
| B3 | Négation générale `'!'` non traduite en MBStyle | Hors périmètre, classification provisoire — à revérifier contre la spec (§1) | Ouvert (chantier interne) |
| B4 | `FontMarker` : aucune notion de police dans Mapbox GL Style | Limite structurelle (§2) | Contourné par rasterisation en sprite (changement de mécanisme) |
| B5 | Rasterisation de glyphe de police impossible sans plate-forme Qt graphique | Contrainte d'environnement (§2) | Contourné : exclusion explicite + avertissement, régénération sur poste adéquat |
| B6 | `styleforge-api` (`POST /v1/convert`) sans résolveur de ressources externes (SVG/sprites) | Hors périmètre actuel (§3) | Contourné via le CLI/plugin QGIS, qui en disposent |

## C. Ticket QGIS à déposer — mode de fusion / opacité de couche absents de l'export SLD

Aucun ticket existant ne couvre ce point (recherche du 2026-10-15 sur le
tracker QGIS, y compris le label « SLD support » — 11 tickets ouverts,
aucun ne mentionne blend/composite/opacity). Vérifié empiriquement avant
rédaction, sur QGIS 3.40.4-Bratislava (Windows), via l'API Python :

```python
from qgis.core import QgsVectorLayer, QgsSingleSymbolRenderer, QgsFillSymbol
from qgis.PyQt.QtGui import QPainter

layer = QgsVectorLayer("Polygon?crs=EPSG:4326", "test", "memory")
layer.setRenderer(QgsSingleSymbolRenderer(QgsFillSymbol.createSimple({'color': '255,0,0,255'})))
layer.setBlendMode(QPainter.CompositionMode_Multiply)
layer.setFeatureBlendMode(QPainter.CompositionMode_Multiply)
layer.setOpacity(0.5)
layer.saveSldStyle("test.sld")
```

Résultat observé : le SLD 1.1.0 produit ne contient ni `VendorOption`, ni
aucun attribut d'opacité — le réglage est perdu silencieusement,
`saveSldStyle()` ne signale aucun avertissement et rapporte un succès
plein. Confirmé en relisant intégralement le fichier produit (1144
caractères, aucune occurrence de « blend », « composit » ou « opacity »
en dehors du nom de couche choisi pour le test).

### Texte de ticket prêt à déposer (anglais, convention du tracker QGIS)

> **Title:** SLD export silently drops layer Blend mode / Feature blend mode (and layer opacity)
>
> **QGIS version:** 3.40.4-Bratislava (Windows) — likely affects other 3.x versions; not checked against 4.0.
>
> **Description:**
> When a vector layer has a non-default "Blend mode" and/or "Feature blend mode" set (Layer Properties → Symbology → Layer rendering), and/or a layer opacity below 100%, exporting the layer's style to SLD (`QgsVectorLayer.saveSldStyle()`, or Export → Save as → SLD) produces a document with no trace of any of these settings: no `VendorOption` (GeoServer's SLD `composite`/`composite-base` extension would be the natural target: https://docs-archive.geoserver.org/stable/en/user/styling/sld/extensions/composite-blend/syntax.html), and no opacity attribute either. The export silently succeeds with no warning.
>
> **Steps to reproduce:**
> 1. Create any vector layer with a simple single-symbol renderer.
> 2. Set Blend mode and/or Feature blend mode to e.g. "Multiply", and/or set layer Opacity to 50%.
> 3. Export the style to SLD (Layer → Export → Save as... → SLD Style, or `layer.saveSldStyle(path)`).
> 4. Inspect the resulting .sld file.
>
> **Expected behavior:** the exported SLD reflects the compositing/opacity settings — e.g. via the GeoServer `composite`/`composite-base` VendorOption for blend mode, and an opacity attribute for layer opacity — or, failing that, QGIS warns that these settings cannot be preserved in SLD.
>
> **Actual behavior:** the settings are dropped with no trace and no warning.
>
> **Note:** this is distinct from #7926 (an unrelated, long-fixed print-composer rasterization bug at high DPI). Searched the "SLD support" label and the other open SLD-export tickets (#23356, #23355, #27752, #36347, #36466) without finding an existing report of this specific gap.

**Avant dépôt** : vérifier si le comportement est identique sur QGIS 4.0
(en préparation, voir le retex) une fois disponible, et joindre le
fichier `.sld` produit par le script ci-dessus comme pièce justificative.
