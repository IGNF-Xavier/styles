# -*- coding: utf-8 -*-
"""
styleforge_api.app — fabrique de l'application FastAPI (phases 6 et 7).

Lancer en développement : uvicorn styleforge_api.app:app --reload
Le worker de lots (phase 7) est un processus SÉPARÉ, jamais démarré ici :
python -m styleforge_api.worker (voir worker.py).
"""
from __future__ import annotations

from fastapi import FastAPI

from .routers import audit, batch, convert, schema

API_VERSION = "0.1.0"


def creer_application() -> FastAPI:
    app = FastAPI(
        title="styleforge-api",
        version=API_VERSION,
        description=(
            "Service de transformation de styles cartographiques "
            "(QML QGIS 3.44 -> SLD 1.0.0 / Mapbox GL Style), construit "
            "sur styleforge-core. PyQGIS n'est JAMAIS une dépendance "
            "d'exécution de ce service — uniquement un oracle de test de "
            "styleforge-core, en amont (voir plan_bibliotheque_"
            "styleforge.docx, section 6.2)."
        ),
    )
    app.include_router(convert.router)
    app.include_router(audit.router)
    app.include_router(schema.router)
    app.include_router(batch.router)

    @app.get("/v1/health", tags=["exploitation"])
    async def sante() -> dict[str, str]:
        """Pas d'authentification : une sonde de vie standard (load
        balancer, orchestrateur de conteneurs) ne porte pas de clé API."""
        return {"statut": "ok", "version": API_VERSION}

    return app


app = creer_application()
