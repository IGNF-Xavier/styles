# -*- coding: utf-8 -*-
"""
styleforge_api.queue — File d'attente pour les lots (phase 7).

Choix du plan de bibliothèque (section 8.2) : "une solution simple (RQ ou
Celery avec Redis) suffit à cette échelle." RQ retenu ici — API Python la
plus simple des deux, suffisante pour ce volume (pas de workflow complexe
multi-étapes, juste "convertir N fichiers").

STYLEFORGE_API_REDIS_URL est le SEUL paramètre : changer de file (Celery,
un Redis managé distant) n'exige de toucher qu'à ce module, jamais aux
routes ni à jobs.py, qui ne connaissent que enfiler_lot()/obtenir_job().
"""
from __future__ import annotations

import os

import redis
from rq import Queue
from rq.job import Job

NOM_FILE = "styleforge-conversions"


def _url_redis() -> str:
    return os.environ.get("STYLEFORGE_API_REDIS_URL", "redis://localhost:6379/0")


_connexion: redis.Redis | None = None
_file: Queue | None = None


def obtenir_connexion() -> redis.Redis:
    global _connexion
    if _connexion is None:
        _connexion = redis.Redis.from_url(_url_redis())
    return _connexion


def obtenir_file() -> Queue:
    global _file
    if _file is None:
        _file = Queue(NOM_FILE, connection=obtenir_connexion())
    return _file


def enfiler_lot(id_lot: str, chemins_relatifs: list[str], params_dict: dict) -> Job:
    """Enfile styleforge_api.jobs.traiter_lot pour exécution par le worker
    (styleforge_api.worker). job_id = id_lot, pour que GET /v1/batch/{id}
    retrouve le job par le même identifiant que celui renvoyé par
    POST /v1/batch — pas de table de correspondance séparée à tenir."""
    from .jobs import traiter_lot  # import tardif : évite que le worker RQ

    # n'ait besoin d'importer app.py (FastAPI) pour résoudre ce module.
    return obtenir_file().enqueue(
        traiter_lot,
        id_lot,
        chemins_relatifs,
        params_dict,
        job_id=id_lot,
        job_timeout="10m",
        result_ttl=86400,
        failure_ttl=86400,
    )


def obtenir_job(id_lot: str) -> Job | None:
    try:
        return Job.fetch(id_lot, connection=obtenir_connexion())
    except Exception:  # noqa: BLE001 — rq lève plusieurs types selon la version
        return None
