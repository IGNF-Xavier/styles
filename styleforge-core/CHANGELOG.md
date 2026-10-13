# Journal des modifications — styleforge-core

Versionnage sémantique strict (plan de bibliothèque, section 9) : tout
changement de champ du pivot typé (`styleforge_core.pivot`) est une version
MAJEURE, jamais un correctif mineur, parce que des clients de l'API ou de
la bibliothèque en dépendent directement.

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
