# -*- coding: utf-8 -*-
"""
styleforge_api.routers.audit — POST /v1/audit (phase 6, API synchrone).

Contrôle de conformité GeoServer d'un ou plusieurs documents SLD déjà
produits (par cette API ou ailleurs) — s'appuie exclusivement sur
styleforge_core.audit.SldAuditor, à l'identique du comportement de la
PHASE 6 du script CNIG (voir sa docstring).

Limite explicite : le résolveur de ressources (existe_ressource /
styles_dir de SldAuditor, pour vérifier qu'un onlineResource référencé
existe réellement) n'est pas câblé ici — cette route audite un SLD hors
contexte de dépôt de fichiers, elle ne sait donc pas si une ressource
externe existe. SldAuditor le gère déjà proprement : un résolveur absent
produit son propre problème nommé (voir _ressource_existe), jamais une
approximation silencieuse "présent" ou "absent".
"""
from __future__ import annotations

import tempfile
from pathlib import Path

from fastapi import APIRouter, Depends, File, UploadFile, status

from styleforge_core.audit import SldAuditor, formater_rapport

from ..auth import exiger_authentification
from ..models import DetailProbleme, ReponseAudit

router = APIRouter(prefix="/v1", tags=["audit"])


@router.post(
    "/audit",
    response_model=ReponseAudit,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(exiger_authentification)],
)
async def auditer(
    fichiers_sld: list[UploadFile] = File(
        ..., description="Un ou plusieurs documents .sld à contrôler."
    ),
) -> ReponseAudit:
    with tempfile.TemporaryDirectory(prefix="styleforge-api-audit-") as tmp:
        chemins: list[Path] = []
        for fichier in fichiers_sld:
            contenu = await fichier.read()
            chemin = Path(tmp) / (fichier.filename or "style.sld")
            chemin.write_bytes(contenu)
            chemins.append(chemin)

        auditeur = SldAuditor()
        rapport = auditeur.auditer(chemins)

    problemes = [
        DetailProbleme(
            categorie=categorie,
            occurrences=rapport.problemes[categorie],
            exemples=rapport.details.get(categorie, [])[:5],
        )
        for categorie in rapport.problemes
    ]

    return ReponseAudit(
        conforme=rapport.conforme,
        fichiers_controles=rapport.controles,
        problemes=problemes,
        extensions=dict(rapport.extensions),
        rapport_texte=formater_rapport(rapport),
    )
