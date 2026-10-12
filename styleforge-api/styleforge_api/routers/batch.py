# -*- coding: utf-8 -*-
"""
styleforge_api.routers.batch — POST /v1/batch, GET /v1/batch/{id} (phase 7,
API asynchrone).

Un lot : plusieurs fichiers .qml déposés en une requête, convertis en
arrière-plan par un worker RQ séparé (styleforge_api.worker), avec UN SEUL
jeu de paramètres de conversion pour tout le lot — pas de traitement
pendant la requête HTTP elle-même, qui répond 202 Accepted avec un
identifiant à interroger via GET /v1/batch/{id}.

Dépendance explicite, pas cachée : cette route a besoin d'un worker RQ
démarré séparément (`python -m styleforge_api.worker`) et d'un Redis
joignable (STYLEFORGE_API_REDIS_URL) — sans worker actif, un lot reste
indéfiniment "en_attente", jamais silencieusement "terminé" à tort.
"""
from __future__ import annotations

import os
import uuid

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status

from ..auth import exiger_authentification
from ..conversion import ParametresConversion
from ..models import Cible, PolitiqueExpression, ReponseLotCree, ReponseStatutLot
from ..queue import obtenir_job
from ..storage import obtenir_stockage

router = APIRouter(prefix="/v1", tags=["lots"])

_TTL_LOT_SECONDES = float(os.environ.get("STYLEFORGE_API_LOT_TTL_SECONDES", "86400"))


@router.post(
    "/batch",
    response_model=ReponseLotCree,
    status_code=status.HTTP_202_ACCEPTED,
    dependencies=[Depends(exiger_authentification)],
)
async def creer_lot(
    fichiers_qml: list[UploadFile] = File(
        ..., description="Un ou plusieurs fichiers .qml — un seul jeu de "
                          "paramètres de conversion s'applique à tous."
    ),
    cible: Cible = Form("sld_et_mbstyle"),
    nom_style: str | None = Form(None),
    dpi: float = Form(90.0),
    sur_expression_non_traduite: PolitiqueExpression = Form("lever"),
    nom_couche: str = Form("layer"),
    id_source: str | None = Form(None),
    url_source: str | None = Form(None),
    nom_couche_source: str | None = Form(None),
) -> ReponseLotCree:
    if not fichiers_qml:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Au moins un fichier .qml est requis.",
        )

    # Import tardif : la file (et donc rq/redis) n'est nécessaire qu'à cet
    # instant, jamais au chargement du module (une installation qui ne
    # sert QUE la phase 6 n'a pas besoin de Redis disponible pour démarrer).
    from ..queue import enfiler_lot

    id_lot = uuid.uuid4().hex
    stockage = obtenir_stockage()
    cles: list[str] = []
    for fichier in fichiers_qml:
        contenu = await fichier.read()
        nom = fichier.filename or f"{uuid.uuid4().hex}.qml"
        cle = f"{id_lot}/{nom}"
        stockage.ecrire(cle, contenu, ttl_secondes=_TTL_LOT_SECONDES)
        cles.append(cle)

    params = ParametresConversion(
        cible=cible,
        nom_style=nom_style,
        dpi=dpi,
        sur_expression_non_traduite=sur_expression_non_traduite,
        nom_couche=nom_couche,
        id_source=id_source,
        url_source=url_source,
        nom_couche_source=nom_couche_source,
    )
    enfiler_lot(id_lot, cles, params.__dict__)

    return ReponseLotCree(
        id_lot=id_lot, statut="en_attente", nombre_fichiers=len(cles)
    )


_RQ_VERS_STATUT = {
    "queued": "en_attente",
    "deferred": "en_attente",
    "scheduled": "en_attente",
    "started": "en_cours",
    "finished": "termine",
    "failed": "echec",
    "stopped": "echec",
    "canceled": "echec",
}


@router.get(
    "/batch/{id_lot}",
    response_model=ReponseStatutLot,
    dependencies=[Depends(exiger_authentification)],
)
async def statut_lot(id_lot: str) -> ReponseStatutLot:
    job = obtenir_job(id_lot)
    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Aucun lot {id_lot!r} — identifiant inconnu, expiré, "
                   "ou Redis indisponible.",
        )

    statut_rq = job.get_status(refresh=True)
    statut = _RQ_VERS_STATUT.get(statut_rq, "en_attente")

    resultat_job = job.return_value(refresh=True)
    if statut == "termine" and isinstance(resultat_job, dict):
        return ReponseStatutLot(id_lot=id_lot, statut=statut, **{
            k: resultat_job[k]
            for k in ("fichiers_traites", "reussites", "echecs", "resultats")
            if k in resultat_job
        })
    if statut == "echec":
        return ReponseStatutLot(
            id_lot=id_lot,
            statut=statut,
            erreur_infrastructure=str(job.exc_info) if job.exc_info else
            "Le job a échoué sans trace d'exception disponible.",
        )
    return ReponseStatutLot(id_lot=id_lot, statut=statut)
