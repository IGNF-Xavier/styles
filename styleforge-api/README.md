# styleforge-api

Service HTTP de conversion de styles cartographiques, construit sur
[`styleforge-core`](../styleforge-core) : QML (QGIS 3.44) → SLD 1.0.0 et/ou
Mapbox GL Style, en synchrone (une requête, une réponse) ou en lot
asynchrone (file d'attente + worker séparé).

PyQGIS n'est **jamais** une dépendance d'exécution de ce service — voir
`plan_bibliotheque_styleforge.docx`, section 6.2.

## Installation

```bash
pip install styleforge-api
```

## Configuration (variables d'environnement)

| Variable | Rôle | Défaut |
|---|---|---|
| `STYLEFORGE_API_KEYS` | Clés API valides, séparées par des virgules. **Service fermé si vide** (voir `auth.py`). | *(vide)* |
| `STYLEFORGE_API_REDIS_URL` | Connexion Redis, pour la file de lots (phase asynchrone uniquement). | `redis://localhost:6379/0` |
| `STYLEFORGE_API_STOCKAGE_LOTS` | Répertoire de stockage des fichiers de lot (implémentation filesystem par défaut — voir `storage.py` pour brancher un stockage objet réel). | `/tmp/styleforge-api-lots` |
| `STYLEFORGE_API_LOT_TTL_SECONDES` | Durée de rétention des fichiers d'un lot avant expiration automatique. | `86400` (24h) |

## Lancer le service synchrone

```bash
uvicorn styleforge_api.app:app --host 0.0.0.0 --port 8000
```

Endpoints : `POST /v1/convert`, `POST /v1/audit`, `GET /v1/schema`,
`GET /v1/health` (non authentifié). Documentation interactive générée par
FastAPI : `http://localhost:8000/docs`.

## Lancer le traitement de lot asynchrone (optionnel)

Nécessite un Redis joignable (`STYLEFORGE_API_REDIS_URL`) et un processus
worker **séparé** du service HTTP :

```bash
python -m styleforge_api.worker
```

Endpoints : `POST /v1/batch` (202 Accepted, renvoie un `id_lot`),
`GET /v1/batch/{id_lot}` (statut : `en_attente` / `en_cours` / `termine` /
`echec`, puis le détail par fichier une fois terminé).

Un fichier en échec dans un lot n'invalide jamais les autres — chacun est
rapporté avec son propre statut.

## Authentification

Interface remplaçable (`styleforge_api.auth.Authentifieur`). L'implémentation
par défaut (`CleApiStatique`) vérifie l'en-tête `X-API-Key` contre
`STYLEFORGE_API_KEYS` — adaptée à un usage interne (une seule organisation).
Un déploiement ouvert à plusieurs organisations, avec jetons par organisation
et quotas, demande une nouvelle implémentation de cette interface, jamais une
modification des routes.

## Limite connue de cette version

Ni `resoudre_image_embarquee` (SLD, images SVG embarquées en base64) ni
`resoudre_sprite` (MBStyle, sprites) ne sont câblés sur `/v1/convert` ou
`/v1/batch` : ce service n'a pas encore de résolveur/stockage de ressources
associé à une requête. Un QML qui en a besoin produit l'exception nommée
correspondante (422), jamais un document silencieusement incomplet.

## Tests

```bash
pip install -e ".[test]"
pytest
```

Les tests de lot (`test_batch.py`) démarrent un `redis-server` réel sur un
port libre et sont automatiquement ignorés (`pytest.skip`) si le binaire
est introuvable dans l'environnement d'exécution.

## Licence

MIT — voir `../styleforge-core/LICENSE`.
