# -*- coding: utf-8 -*-
"""
styleforge_api.routers.schema — GET /v1/schema (phase 6, API synchrone).

Publie le schéma JSON du pivot pydantic (styleforge_core.pivot.Style), pour
qu'un client valide un document pivot de son côté sans avoir à deviner sa
forme ni à dépendre de Python/pydantic (table des points de terminaison du
plan de bibliothèque, section 8.1). Volontairement GET et non authentifié
par défaut : c'est un document public et sans effet de bord, au même titre
qu'une spécification OpenAPI — mais la dépendance d'authentification reste
injectée pour que ce choix soit explicite et changeable, pas un oubli.
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, status

from styleforge_core.pivot import Style

router = APIRouter(prefix="/v1", tags=["schema"])


@router.get("/schema", status_code=status.HTTP_200_OK)
async def schema_pivot() -> dict[str, Any]:
    """Schéma JSON (JSON Schema, via pydantic v2) du modèle racine du
    pivot. Le nom de version exposé ('pivot_version') correspond au
    PivotV1 du plan de bibliothèque (section 5.3) : tout changement de
    champ dans styleforge_core.pivot est, par principe du projet, une
    version MAJEURE — jamais un correctif silencieux de ce schéma."""
    return {
        "pivot_version": "v1",
        "schema": Style.model_json_schema(),
    }
