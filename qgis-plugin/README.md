# Plugin QGIS Styleforge — QML vers SLD / MBStyle

Convertit, directement depuis QGIS, le style de la couche active, de
toutes les couches chargées dans le projet, ou d'un dossier de fichiers
`.qml`, vers **SLD 1.0.0** et (optionnellement) **Mapbox GL Style**
(MBStyle) pour GeoServer — sans quitter QGIS, pour un usage
d'aperçu/itération rapide.

Testé avec **QGIS 3.40.4** (LTR) ; écrit pour rester chargeable sans
modification sous **QGIS 4.x** (imports via `qgis.PyQt`, jamais
`PyQt5`/`PyQt6` directement ; appels `.exec()`, jamais `.exec_()` ;
aucune API dépréciée connue). `qgisMinimumVersion=3.40` dans
`metadata.txt`.

## Limites de cette version (volontaires, voir `metadata.txt`)

- Aucun correctif de post-traitement GeoServer (hachures, `VendorOption`
  — PHASE 4 du CLI) : ce plugin couvre l'aperçu rapide, pas le pipeline
  de production complet. Pour un déploiement réel, utilisez
  `cnig_qml2sld_geoserver.py` (le CLI, à la racine du dépôt).
- Les pictogrammes SVG **embarqués en base64** dans le QML (convention
  QGIS — la quasi-totalité du corpus CNIG réel) sont décodés et déployés
  dans `svg/cnig/` du dossier de sortie, mêmes conventions que le CLI.
- Un SVG référencé par un **chemin de fichier** (pas embarqué), ou un
  **sprite MBStyle** (pictogramme/motif pour le document Mapbox),
  n'est pas résolu par cette version — même limite, pour la même
  raison, que `POST /v1/convert` de `styleforge-api` (voir
  `docs/limites.md` section 3 à la racine du dépôt). Un style qui en
  dépend échoue avec un message explicite pour ce document précis,
  jamais un rendu approximé.

## Installation

Le plugin dépend de **`styleforge-core`**, qui vit comme dossier frère
de `qgis-plugin/` dans ce même dépôt (`<dépôt>/styleforge-core/`) — ne
déplacez pas ce plugin hors du dépôt cloné, sinon le bouton
« Installer styleforge-core… » du plugin ne retrouvera pas sa source.

### 1. Indiquer à QGIS où trouver le plugin

Deux façons, au choix :

**A. Chemin de plugin additionnel (recommandé — rien à copier)**

QGIS → *Préférences* (ou *Settings*) → *Options* → onglet *Système* →
section « Chemins des extensions » (*Plugin Paths*) → ajouter le
chemin complet vers **`<dépôt>/qgis-plugin`** (le dossier qui contient
`styleforge_qgis/`, pas `styleforge_qgis/` lui-même). Redémarrer QGIS.

**B. Lien/copie dans le dossier de profil QGIS**

Placez (ou créez un lien symbolique vers) `styleforge_qgis/` dans le
dossier des plugins du profil QGIS actif :

- **Windows** :
  `%APPDATA%\QGIS\QGIS3\profiles\<profil>\python\plugins\`
  (profil par défaut : `default` — trouvez le vôtre via *Paramètres
  utilisateur* dans QGIS, ou `QGIS 3.40.4` → *Aide* → *Infos système*).
- **Linux** :
  `~/.local/share/QGIS/QGIS3/profiles/<profil>/python/plugins/`
- **macOS** :
  `~/Library/Application Support/QGIS/QGIS3/profiles/<profil>/python/plugins/`

Avec cette option, chaque mise à jour du dépôt nécessite de recopier
(ou de refaire le lien vers) `styleforge_qgis/`.

### 2. Activer le plugin

QGIS → *Extensions* (*Plugins*) → *Gérer et installer les extensions*
→ onglet *Installées* → cocher **Styleforge — QML vers SLD/MBStyle**.

### 3. Installer la dépendance styleforge-core

À la première utilisation (menu *Vecteur* → *Styleforge* → convertir…),
le plugin détecte si `styleforge-core` est disponible dans
l'environnement Python de QGIS. S'il ne l'est pas, un bouton
**« Installer styleforge-core… »** lance `pip install` depuis la source
du dépôt (voir ci-dessus) — aucune action manuelle en ligne de commande
n'est nécessaire dans le cas courant.

Si l'installation automatique échoue (environnement verrouillé,
permissions), le message d'erreur complet de `pip` est affiché dans le
journal de la fenêtre — installez alors manuellement, avec
l'interpréteur Python **de QGIS** (pas celui du système) :

```bash
# Linux/macOS : généralement l'interpréteur système utilisé par QGIS
python3 -m pip install /chemin/vers/<dépôt>/styleforge-core

# Windows : l'exécutable Python livré à côté de QGIS, PAS qgis-bin.exe
# (ex. "C:\Program Files\QGIS 3.40.4\apps\Python312\python.exe" —
# le numéro de version Python peut différer selon votre installation)
"C:\Program Files\QGIS 3.40.4\apps\Python312\python.exe" -m pip install C:\chemin\vers\<dépôt>\styleforge-core
```

## Utilisation

Menu *Vecteur* → *Styleforge* → *Styleforge — QML vers SLD/MBStyle…*
(ou l'icône correspondante dans la barre d'outils Vecteur).

1. Choisir la source : couche active, toutes les couches chargées, ou
   un dossier de fichiers `.qml`.
2. Choisir le dossier de sortie.
3. Cocher « Produire aussi le MBStyle » si besoin.
4. *Convertir*. Le journal affiche le résultat par couche/fichier
   (succès, nombre d'avertissements, ou message d'échec explicite) ;
   `rapport_conversion.md` est écrit dans le dossier de sortie, avec la
   même convention de préfixes (`Lecture QML :` / `SLD :` /
   `MBStyle :`) que le rapport du CLI.

## Développement

Pas de fichier `.ui` : l'interface est construite en code
(`dialogue.py`) pour rester simple à relire sans Qt Designer. La
logique de conversion (`convertisseur.py`) et la détection/installation
de la dépendance (`dependances.py`) n'importent `qgis.core`/
`qgis.PyQt` que là où c'est strictement nécessaire (export du style
d'une couche, interface) — `styleforge-core` lui-même reste **sans
aucune dépendance PyQGIS**, y compris quand il est appelé depuis ce
plugin.
