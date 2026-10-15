# Journal des modifications — styleforge-core

Versionnage sémantique strict (plan de bibliothèque, section 9) : tout
changement de champ du pivot typé (`styleforge_core.pivot`) est une version
MAJEURE, jamais un correctif mineur, parce que des clients de l'API ou de
la bibliothèque en dépendent directement.

## 0.2.2 — classification explicite des écarts (`CategorieEcart`)

- Nouvelle énumération `styleforge_core.writers.mbstyle.CategorieEcart`
  (`HORS_PERIMETRE` / `LIMITE_STRUCTURELLE`) et nouveau paramètre optionnel
  `categorie` sur `ExpressionPivotNonEcrite.__init__` — distingue
  explicitement « non écrit parce que hors périmètre actuel de cette
  itération » (un équivalent existe dans le format cible, juste pas encore
  traduit) de « non écrit parce que le format cible ne le permet pas
  structurellement » (aucun développement futur sur cet écrivain ne peut
  lever la limite). Rétrocompatible : `categorie` est optionnel (`None` par
  défaut), aucune des 46 levées existantes de `mbstyle.py` n'est cassée.
- Trois levées représentatives de `mbstyle.py` reclassées avec cette
  nouvelle grille, à la relecture :
  - motif LIKE à plusieurs segments ou au joker `_` (`_classifier_motif_like`) :
    `HORS_PERIMETRE` — reformulation plus précise que ce qui était documenté
    jusqu'ici : ce n'est pas une impossibilité du format, juste une
    traduction non construite/vérifiée cette itération.
  - opérateur `'*='` (LIKE générique) dans `_construire_filtre_mapbox` :
    `LIMITE_STRUCTURELLE` confirmée — aucun opérateur de correspondance par
    motif générique dans la spec Mapbox GL Expressions elle-même.
  - négation générale `'!'` dans `_construire_filtre_mapbox` : `HORS_PERIMETRE`
    (et non `LIMITE_STRUCTURELLE`) malgré le rejet par l'oracle QGIS — la
    spec Mapbox GL legacy filter propose déjà `'!='` et `'none'`, non encore
    vérifiés comme couverture suffisante ; voir le point de vigilance
    méthodologique ajouté à `docs/limites.md` section 0 (ne jamais conclure à
    une limite de format sur la seule foi du comportement de l'oracle, cf.
    section 6 déjà existante).
  Les ~43 autres levées de `mbstyle.py` restent non classées (`categorie=None`)
  en attendant une relecture au cas par cas plutôt qu'un étiquetage hâtif.
- `docs/limites.md` : nouvelle section 0 présentant la grille de lecture
  (trois catégories, dont la « contrainte d'environnement d'exécution » qui
  n'est ni l'une ni l'autre — ex. la rasterisation de glyphes de police
  dépendante d'une plate-forme Qt graphique), et sections 1 à 3 annotées
  avec leur catégorie.
- Aucun changement de champ du pivot typé, aucun changement de
  comportement observable (même document SLD/MBStyle produit pour les
  mêmes entrées) — uniquement une classification diagnostique ajoutée aux
  exceptions déjà levées. Version MINEURE.

## 0.2.1 — correctifs MBStyle (perpendicularOffset, spacing, color) et SLD (color)

- `styleforge_core.writers.mbstyle` : `LineSymbolizer.perpendicularOffset` est
  désormais écrit en `line-offset` (paint), avec **inversion de signe** par
  rapport à la convention SLD/pivot — vérifiée par deux aller-retours oracle
  QGIS indépendants (`QgsVectorLayer.loadSldStyle()` côté SLD,
  `QgsMapBoxGlStyleConverter` côté MBStyle).
- `styleforge_core.writers.mbstyle` : `LineSymbolizer.graphicStroke` avec
  `spacing` (pictogramme répété le long d'une ligne) est désormais écrit en
  couche Mapbox `type: "symbol"` (`symbol-placement: "line"` +
  `symbol-spacing`) au lieu de `type: "line"` — seule construction Mapbox GL
  Style qui répète un motif le long d'une ligne. Vérifié par oracle QGIS
  (round-trip `QgsMapBoxGlStyleConverter` → `QgsMarkerLineSymbolLayer`).
- `styleforge_core.writers.mbstyle` : `IconSymbolizer.color` est désormais
  écrit en `icon-color` (paint), combiné à un sprite marqué `"sdf": true`
  quand le SVG source suit la convention paramétrique QGIS/GeoServer
  (`fill="param(fill)"`). Non vérifiable par l'oracle QGIS habituel
  (`QgsMapBoxGlStyleConverter` n'implémente ni `icon-color` ni le drapeau
  `sdf`, confirmé en lisant son code source C++, versions 3.28 à 3.40) —
  conforme à la spec Mapbox GL Style officielle, avertissement explicite
  émis dans ce sens à chaque occurrence.
- `styleforge_core.writers.sld` : `IconSymbolizer.color` est désormais
  transmis en paramètre de requête sur l'`xlink:href` (`?fill=%23…`),
  convention GeoServer documentée (« Parametric SVG »), pour les mêmes SVG
  paramétriques que ci-dessus.
- Nouveau module `styleforge_core.sprites` : détection automatique (sur le
  contenu du fichier, pas une liste figée) des SVG paramétriques et masquage
  en sprite SDF (blanc opaque, teintable par `icon-color` au rendu) —
  nécessaire pour que le correctif `icon-color` ci-dessus ait un effet réel ;
  sans cette détection, `fill="param(fill)"` n'étant pas une valeur CSS
  valide, le pictogramme s'afficherait vide.
- Limite résiduelle connue : 3 des 127 pictogrammes du corpus de test sont
  des tracés au contour seul (`stroke`, pas de `fill`) — le masquage SDF ne
  neutralise aujourd'hui que le paramètre `fill`, jamais `outline` (même
  limite préexistante côté SLD). Ces 3 pictogrammes précis s'afficheraient
  vides en MBStyle. À traiter séparément si utilisés en pratique.
- Aucun changement de champ du pivot typé (`styleforge_core.pivot`) :
  version MINEURE (correctifs de comportement des écrivains), pas majeure.

## 0.2.0 — partage du post-traitement SLD et des sprites MBStyle avec le plugin QGIS

- Nouveau module `styleforge_core.writers.sld_posttraitement` : migration
  depuis `cnig_qml2sld_geoserver.py` (CLI, section « PHASE 4 ») du
  nettoyage des balises propriétaires QGIS/ESRI, de la réécriture des
  références SVG, de la correction des `WellKnownName`, de la réparation
  fidèle des hachures/tirets et de l'injection des `VendorOption`
  GeoServer — jusqu'ici dupliqué (ou absent) côté `qgis-plugin/`.
  Expose `post_traiter_sld()` (fonction publique) en plus des éléments
  internes migrés tels quels. Migration vérifiée **octet pour octet**
  (manifeste MD5) sur le corpus réel CNIG GPU (17 fichiers), backends
  `styleforge` et `standalone` du CLI.
- Nouveau module `styleforge_core.sprites` (classe `SpriteRegistry`) :
  migration depuis le CLI (section « PHASE 5 ») de la fabrication de la
  feuille de sprites Mapbox GL (`sprite.png`/`sprite.json` + `@2x`) pour
  les pictogrammes SVG, motifs de hachure, marques simples et glyphes de
  police d'un document MBStyle. `build()` accepte désormais un paramètre
  optionnel `pump_ui` (callback sans argument) au lieu d'appeler une
  fonction globale du CLI — seule différence délibérée avec l'original,
  sans impact sur le résultat produit (migration vérifiée octet pour
  octet, même méthode que ci-dessus).
- Aucun changement de champ du pivot typé (`styleforge_core.pivot`) :
  version MINEURE (ajout de modules publics), pas majeure.
- Ces deux migrations permettent au plugin QGIS (`qgis-plugin/`, version
  0.2.0) de lever ses trois limites connues de la 0.1.0 : SVG référencés
  par chemin de fichier, sprites MBStyle, et correctifs PHASE 4 — en
  partageant le même code que le CLI plutôt que deux copies qui
  dériveraient l'une de l'autre.

## 0.1.0 — première publication

- Lecteur QML (QGIS 3.44 LTR) -> pivot typé (`styleforge_core.readers.qml`),
  pivot aligné sur le schéma `geostyler-style` (pydantic v2, `extra="forbid"`).
- Écrivain SLD 1.0.0 (`styleforge_core.writers.sld`), avec post-traitement
  de conformité GeoServer.
- Écrivain Mapbox GL Style (`styleforge_core.writers.mbstyle`), couverture
  étendue : Fill/Line/Mark/Text/Icon, empilement multi-symbolizer par
  Rule, fill-pattern/line-pattern via sprite, et traduction native
  LIKE/ILIKE (formes exact/préfixe/suffixe/contient) en expressions
  Mapbox GL (`slice`/`downcase`/`in`).
- Auditeur de conformité GeoServer généralisé (`styleforge_core.audit`).
- PyQGIS utilisé uniquement comme oracle de test (CI / vérification),
  jamais comme dépendance d'exécution de ce paquet — voir le plan de
  bibliothèque, section 6.2.
- 243 tests (pytest), 0 régression connue sur le corpus réel CNIG GPU
  (17 fichiers, SLD et MBStyle).
