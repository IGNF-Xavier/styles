# -*- coding: utf-8 -*-
"""
styleforge_api.routers.convert — POST /v1/convert (phase 6, API synchrone).

QML -> SLD et/ou MBStyle, dans la même requête HTTP. Toute la logique de
conversion vit dans styleforge_api.conversion (partagée avec le traitement
de lot asynchrone, phase 7) — cette route ne fait que : écrire le fichier
reçu sur disque, appeler convertir_qml(), traduire les exceptions.

Limite explicite de cette première itération, documentée plutôt que
cachée : ni resoudre_image_embarquee (SLD) ni resoudre_sprite (MBStyle) ne
sont câblés sur cette route — l'API, à ce stade, n'a pas de service de
résolution/stockage de ressources (SVG embarqués en base64, sprites). Un
QML dont un IconSymbolizer référence une image embarquée en base64, ou
dont un graphicFill/graphicStroke a besoin d'un sprite, produira donc
l'exception nommée correspondante (ExpressionPivotNonEcrite), remontée en
422 — PAS un document silencieusement incomplet. Lever cette limite est un
chantier séparé (un résolveur de ressources par requête, ou un stockage
d'assets côté service), pas un oubli de câblage.
"""
from __future__ import annotations

import tempfile
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status

from ..auth import exiger_authentification
from ..conversion import ParametresConversion, ParametresSourceManquants, convertir_qml
from ..erreurs import lever_si_connue
from ..models import Cible, PolitiqueExpression, ReponseConversion

router = APIRouter(prefix="/v1", tags=["conversion"])


@router.post(
    "/convert",
    response_model=ReponseConversion,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(exiger_authentification)],
)
async def convertir(
    fichier_qml: UploadFile = File(..., description="Fichier .qml QGIS 3.44 source."),
    cible: Cible = Form(
        "sld_et_mbstyle",
        description="Document(s) à produire : 'sld', 'mbstyle', ou les deux.",
    ),
    nom_style: str | None = Form(
        None, description="Nom du Style produit (défaut : le nom du fichier)."
    ),
    dpi: float = Form(
        90.0,
        description=(
            "Résolution supposée pour convertir MM/Point/Inch en pixels "
            "SLD — 90 est la convention OGC SLD/SE historique, PAS la "
            "résolution écran usuelle de 96 (voir readers.qml)."
        ),
    ),
    sur_expression_non_traduite: PolitiqueExpression = Form(
        "lever",
        description=(
            "'lever' (défaut) : une expression QGIS non traduisible fait "
            "échouer la conversion (422). 'avertir' : la valeur littérale "
            "déjà lue est conservée, avec un avertissement — jamais "
            "silencieux dans les deux cas."
        ),
    ),
    nom_couche: str = Form("layer", description="Nom de couche pour le SLD produit."),
    id_source: str | None = Form(
        None,
        description="Obligatoire si cible inclut 'mbstyle' (paramètre de "
                     "contexte de rendu, jamais déduit du pivot).",
    ),
    url_source: str | None = Form(
        None, description="Obligatoire si cible inclut 'mbstyle'."
    ),
    nom_couche_source: str | None = Form(
        None, description="Obligatoire si cible inclut 'mbstyle'."
    ),
) -> ReponseConversion:
    contenu = await fichier_qml.read()
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

    with tempfile.TemporaryDirectory(prefix="styleforge-api-convert-") as tmp:
        chemin_qml = Path(tmp) / (fichier_qml.filename or "style.qml")
        chemin_qml.write_bytes(contenu)

        try:
            resultat = convertir_qml(chemin_qml, params)
        except ParametresSourceManquants as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail={
                    "type_erreur": "ParametresSourceManquants",
                    "module_erreur": __name__,
                    "message": str(exc),
                },
            ) from exc
        except Exception as exc:  # noqa: BLE001 — traduit ou relevé par lever_si_connue
            lever_si_connue(exc)
            raise  # jamais atteint (lever_si_connue lève toujours) ; pour les linters

    return ReponseConversion(**resultat)
