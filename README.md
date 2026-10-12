# styles — QML QGIS → SLD GeoServer / Mapbox GL Style

Conversion de styles cartographiques QGIS 3.44 (`.qml`) vers **SLD 1.0.0**
(GeoServer) et **Mapbox GL Style** (`MBStyle`, GeoServer), via :

- **`cnig_qml2sld_geoserver.py`** — l'outil en ligne de commande, point
  d'entrée historique (corpus CNIG GPU) et toujours le chemin le plus
  complet (résolution de ressources locales, publication GeoServer
  optionnelle, repli PyQGIS pour les cas non couverts).
- **`styleforge-core/`** — la bibliothèque Python qui porte la logique de
  conversion (lecteur QML, pivot typé, écrivains SLD/MBStyle, audit),
  **sans jamais dépendre de PyQGIS à l'exécution** — PyQGIS n'intervient
  que comme oracle de test, en amont, jamais en production.
- **`styleforge-api/`** — un service HTTP (FastAPI) construit sur
  `styleforge-core` : conversion synchrone (`POST /v1/convert`) et
  traitement de lot asynchrone (`POST /v1/batch` + worker RQ/Redis).

Ce document a trois entrées indépendantes, chacune autosuffisante — allez
directement à celle qui vous concerne :

1. [Utilisateur CLI](#1-utilisateur-cli--un-dossier-de-qml-vers-sld--mbstyle) — convertir un dossier de `.qml` en un dossier de `.sld`/`.json`.
2. [Déployeur d'API](#2-déployeur-dapi) — installer et lancer le service HTTP (synchrone + asynchrone).
3. [Mainteneur GeoServer](#3-mainteneur-geoserver) — ce qu'il faut installer/configurer côté GeoServer pour que les sorties fonctionnent réellement.

Limites connues et contournements, consolidés : [`docs/limites.md`](docs/limites.md).
Exemples réels (CNIG GPU) avec leurs sorties : [`examples/`](examples/SOURCES.md).

---

## 1. Utilisateur CLI — un dossier de QML vers SLD + MBStyle

### Installation

```bash
git clone <url-de-ce-depot>
cd styles
python3 -m venv .venv && source .venv/bin/activate
pip install ./styleforge-core
```

`cnig_qml2sld_geoserver.py` n'a, avec `--backend styleforge` (recommandé,
voir plus bas), **aucune dépendance autre que `styleforge-core`** —
ni QGIS, ni `bridgestyle`, ni affichage graphique. Les backends `qgis` et
`standalone` existent pour compatibilité/comparaison mais demandent une
installation QGIS complète ; ignorez-les si vous démarrez de zéro.

### Convertir un dossier

```bash
python cnig_qml2sld_geoserver.py \
    --local-source chemin/vers/dossier_qml \
    --backend styleforge \
    --mbstyle \
    --all \
    --out chemin/vers/dossier_sortie \
    --clean
```

- `--local-source` : dossier contenant vos `.qml` (récursif).
- `--backend styleforge` : utilise `styleforge-core` seul (voir ci-dessus) — le choix recommandé pour un usage hors QGIS.
- `--mbstyle` : produit aussi le Mapbox GL Style JSON (sans cette option, seul le SLD est produit).
- `--all` : traite tous les fichiers trouvés (sans filtre d'échantillon).
- `--out` : dossier de sortie (`.sld` et `.json` par fichier source, plus un rapport).
- `--clean` : vide le dossier de sortie avant d'écrire (évite de mélanger une exécution précédente).

Résultat : pour chaque `nom.qml`, un `nom.sld` et (avec `--mbstyle`) un
`nom.json` dans le dossier de sortie, plus un rapport de synthèse
(PHASE 6 : audit de conformité GeoServer — ne conclut jamais "prêt" sans
preuve).

Pour reproduire exactement les exemples fournis (`examples/`), voir la
commande donnée dans [`examples/SOURCES.md`](examples/SOURCES.md).

### Options utiles

| Option | Effet |
|---|---|
| `--mbstyle-base-url URL` | URL de base GeoServer à inscrire dans le champ `"sprite"` du MBStyle produit (voir [section GeoServer](#3-mainteneur-geoserver)) |
| `--mbstyle-workspace NOM` | Workspace GeoServer cible, si le style y sera publié |
| `--analyze-only` | N'écrit rien ; rapporte seulement ce qui serait fait |
| `--no-hatch-fix` | Désactive la correction automatique des hachures `shape://` dégradées |
| `--geoserver-url URL` (+ `--geoserver-user`/`--geoserver-password`/`--geoserver-workspace`) | Publie directement les styles produits sur un GeoServer cible (optionnel — omettez ces options pour ne faire que générer des fichiers) |

`--help` liste l'intégralité des options (configuration réseau/proxy,
cache de dépôt source, écriture d'un fichier de config réutilisable via
`--write-config`, etc.) — tout ce qui constitue un choix dans cet outil
est un paramètre explicite, jamais une valeur devinée en silence.

### Limites

Voir [`docs/limites.md`](docs/limites.md) — notamment les filtres
`LIKE`/`ILIKE` à motif multi-segments (hors champ, lève une exception
nommée plutôt que d'approximer) et les marques de police dont le rendu
dépend de la police installée côté poste de génération et côté serveur.

---

## 2. Déployeur d'API

`styleforge-api` expose `styleforge-core` en service HTTP : une route
**synchrone** pour une conversion immédiate, une route **asynchrone**
(lot + worker séparé) pour un volume de fichiers plus important.

### Installation

```bash
pip install ./styleforge-core ./styleforge-api
```

### Authentification

Toutes les routes (sauf `/v1/health` et `/v1/schema`) exigent un en-tête
`X-API-Key`, validé contre la variable d'environnement
`STYLEFORGE_API_KEYS` (liste de clés valides séparées par des virgules) :

```bash
export STYLEFORGE_API_KEYS="cle-une,cle-deux"
```

**Sans cette variable (ou vide), le service refuse explicitement toute
requête authentifiée (503)** — jamais un service qui "marche" par
accident faute de clé positionnée. L'authentification est une interface
remplaçable (`styleforge_api.auth.Authentifieur`) : l'implémentation par
défaut couvre un usage interne à clé(s) partagée(s) ; un déploiement
ouvert à plusieurs organisations avec quotas demanderait de brancher une
autre implémentation derrière la même interface, sans toucher aux routes.

### Lancer le service synchrone

```bash
uvicorn styleforge_api.app:app --host 0.0.0.0 --port 8000
```

Routes disponibles (toutes sous `/v1`, documentation interactive sur
`/docs`) :

| Route | Rôle |
|---|---|
| `GET /v1/health` | Sonde de vie, non authentifiée |
| `GET /v1/schema` | Schéma JSON du pivot (`styleforge_core.pivot.Style`), non authentifiée |
| `POST /v1/convert` | QML → SLD et/ou MBStyle, dans la requête |
| `POST /v1/audit` | Audit de conformité GeoServer d'un ou plusieurs SLD déjà produits |

**Limite explicite de `/v1/convert`** : aucun résolveur de ressources
externes (SVG embarqué, sprite) n'est câblé dans cette première
itération — un style qui en dépend échoue en 422 avec le détail de
l'exception nommée en cause, jamais un document silencieusement
incomplet. Utilisez le CLI pour ces cas en attendant ce chantier séparé
(voir [`docs/limites.md`](docs/limites.md), section 3).

### Lancer le traitement de lot asynchrone (optionnel)

Nécessite un Redis joignable :

```bash
export STYLEFORGE_API_REDIS_URL="redis://localhost:6379/0"
export STYLEFORGE_API_STOCKAGE_LOTS="/var/lib/styleforge-api/lots"   # défaut : /tmp/styleforge-api-lots
export STYLEFORGE_API_LOT_TTL_SECONDES="86400"                       # défaut : 24h

# Le worker tourne dans un PROCESSUS SÉPARÉ, jamais démarré par uvicorn :
python -m styleforge_api.worker
# (ou, via le point d'entrée installé : styleforge-api-worker)
```

Sans worker actif, un lot créé via `POST /v1/batch` reste indéfiniment
`"en_attente"` — jamais faussement `"terminé"`.

| Route | Rôle |
|---|---|
| `POST /v1/batch` | Dépose un lot de `.qml` (un seul jeu de paramètres pour tout le lot), répond `202 Accepted` avec un identifiant de lot |
| `GET /v1/batch/{id_lot}` | Statut du lot (`en_attente` / `en_cours` / `termine` / `echec`) et résultats une fois terminé |

### Variables d'environnement — récapitulatif

| Variable | Obligatoire | Défaut | Rôle |
|---|---|---|---|
| `STYLEFORGE_API_KEYS` | Oui (sinon 503 sur toute route authentifiée) | — | Clés API valides, séparées par des virgules |
| `STYLEFORGE_API_REDIS_URL` | Seulement pour `/v1/batch` | `redis://localhost:6379/0` | Connexion Redis (file RQ) |
| `STYLEFORGE_API_STOCKAGE_LOTS` | Non | `/tmp/styleforge-api-lots` | Répertoire de stockage des fichiers de lot (expiration automatique) |
| `STYLEFORGE_API_LOT_TTL_SECONDES` | Non | `86400` | Durée de conservation des fichiers d'un lot |

Le stockage des fichiers de lot est, comme l'authentification, une
interface remplaçable (`styleforge_api.storage.StockageObjets`) : le
système de fichiers local est l'implémentation par défaut (purge
automatique sur expiration) ; un déploiement multi-instances a besoin
d'un backend partagé (S3/GCS, volume réseau) branché derrière la même
interface, sans toucher à `routers.batch` ni `jobs`.

### Limites GeoServer applicables aux sorties de l'API

Les documents produits par `/v1/convert` ont les mêmes besoins côté
GeoServer que ceux du CLI — voir la [section mainteneur GeoServer](#3-mainteneur-geoserver)
ci-dessous (module MBStyle, sprites, polices).

---

## 3. Mainteneur GeoServer

Résumé — détail complet dans [`docs/geoserver.md`](docs/geoserver.md).

- **SLD seul (pas de hachures/police)** : rien à installer, SLD 1.0.0
  standard.
- **Marques de police SLD (`ttf://Police#0xHEX`)** : GeoServer les trace
  nativement **si la police est installée côté système GeoServer**.
- **MBStyle (tout fichier `.json` produit)** : extension **non incluse
  par défaut** — télécharger le plugin MBStyle correspondant **exactement**
  à la version de GeoServer installée, extraire les 2 JAR dans
  `WEB-INF/lib`, redémarrer, vérifier que "MBStyle" apparaît dans
  l'éditeur de styles.
- **Sprites référencés par un MBStyle** (`sprite.png`/`sprite@2x.png` +
  index JSON) : déposer les 4 fichiers dans `<data_dir>/styles/`
  et vérifier que l'URL `{base_url}/geoserver/styles/sprite` (sans
  `/rest/`) les sert effectivement — voir `docs/geoserver.md` pour le
  détail et les sources de cette convention.
- **`VendorOption` reconnues** (hachures, étiquetage) : liste complète
  dans `docs/geoserver.md` — une option absente de cette liste est
  ignorée silencieusement par GeoServer lui-même (PHASE 6 de l'outil le
  signale avant publication).
- **`matchCase` sur `PropertyIsLike`** : extension GeoServer au
  vocabulaire Filter 1.0, reconnue nativement, consignée comme telle dans
  l'audit plutôt que tue.

---

## Licence

MIT — voir [`LICENSE`](LICENSE). `styleforge-core` et `styleforge-api`
portent chacun leur propre copie de la licence dans leur dossier
(identique, pour qu'un package publié séparément reste autosuffisant).
