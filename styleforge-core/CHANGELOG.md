# Journal des modifications — styleforge-core

Versionnage sémantique strict (plan de bibliothèque, section 9) : tout
changement de champ du pivot typé (`styleforge_core.pivot`) est une version
MAJEURE, jamais un correctif mineur, parce que des clients de l'API ou de
la bibliothèque en dépendent directement.

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
