# styleforge-core

Lit un style QGIS (`.qml`, QGIS 3.44 LTR) et produit un document SLD 1.0.0
ou Mapbox GL Style (MBStyle) — sans jamais dépendre de QGIS/PyQGIS à
l'exécution. PyQGIS n'intervient que comme **oracle de test** (CI), jamais
comme dépendance d'exécution de ce paquet.

## Installation

```bash
pip install styleforge-core
```

## Usage minimal

```python
from styleforge_core.readers.qml import lire_fichier_qml
from styleforge_core.writers.sld import ecrire_sld
from styleforge_core.writers.mbstyle import ecrire_mbstyle

resultat = lire_fichier_qml("mon_style.qml")
print(resultat.avertissements)  # jamais à ignorer — voir ci-dessous

sld = ecrire_sld(resultat.style, nom_couche="ma_couche")

mbstyle = ecrire_mbstyle(
    resultat.style,
    id_source="ma_source",
    url_source="https://tuiles.example.org/{z}/{x}/{y}.pbf",
    nom_couche_source="ma_couche",
)
```

## Principes

- **Jamais d'échec silencieux.** Un cas non géré lève une exception nommée
  (`ErreurLectureQML` et ses sous-classes côté lecteur,
  `ExpressionPivotNonEcrite` côté écrivain) plutôt que de produire un
  document tronqué ou une approximation non signalée. Une approximation
  délibérée (ex. une forme non circulaire rendue en cercle) est toujours
  accompagnée d'un avertissement explicite dans
  `LectureResultat.avertissements` ou la liste `avertissements` passée aux
  écrivains.
- **Tout ce qui est un choix est un paramètre.** dpi, politique sur les
  expressions non traduites, résolveurs de ressources (images embarquées,
  sprites) : jamais une valeur figée en dur.
- **Pivot typé, pas un dict libre.** `styleforge_core.pivot` est aligné sur
  le schéma publié par [geostyler-style](https://github.com/geostyler/geostyler-style)
  (pydantic v2, `extra="forbid"` : une clé inconnue lève une erreur de
  validation immédiate plutôt que d'être silencieusement ignorée).

## Portée

Une seule version QGIS formellement supportée : **3.44 (LTR)**. Voir
`CHANGELOG.md` pour l'historique des versions et la politique de
versionnage (tout changement de champ du pivot = version majeure).

## Licence

GPL-3.0-or-later — voir `LICENSE`.
