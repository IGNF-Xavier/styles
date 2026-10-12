# -*- coding: utf-8 -*-
"""
styleforge_api.worker — processus séparé exécutant les lots (phase 7).

Lancer avec : python -m styleforge_api.worker
Jamais importé par app.py ni par les routes : le worker est un PROCESSUS
séparé du serveur API (section 10 du plan : "un worker pour les lots"),
pour qu'un lot volumineux ne bloque jamais une requête HTTP synchrone.
"""
from __future__ import annotations

from rq import Worker

from .queue import NOM_FILE, obtenir_connexion


def main() -> None:
    connexion = obtenir_connexion()
    worker = Worker([NOM_FILE], connection=connexion)
    worker.work()


if __name__ == "__main__":
    main()
