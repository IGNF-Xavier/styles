# -*- coding: utf-8 -*-
"""
styleforge_api.conversion — logique de conversion partagée entre la route
synchrone (POST /v1/convert, phase 6) et le traitement de lot asynchrone
(phase 7, styleforge_api.jobs). Factorisée ici pour que les deux chemins ne
puissent PAS diverger silencieusement sur le même fichier QML — un bug
corrigé une fois profite aux deux.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from styleforge_core.readers.qml import lire_fichier_qml
from styleforge_core.writers.mbstyle import ecrire_mbstyle
from styleforge_core.writers.sld import ecrire_sld

from .models import Cible, PolitiqueExpression


class ParametresSourceManquants(Exception):
    """id_source/url_source/nom_couche_source manquants alors que `cible`
    demande un document MBStyle — styleforge_core.writers.mbstyle.
    ecrire_mbstyle() ne suppose jamais de source de tuiles par défaut
    (paramètres obligatoires, voir sa docstring) ; cette couche API
    applique la même règle plutôt que d'inventer une valeur."""


@dataclass
class ParametresConversion:
    cible: Cible = "sld_et_mbstyle"
    nom_style: str | None = None
    dpi: float = 90.0
    sur_expression_non_traduite: PolitiqueExpression = "lever"
    nom_couche: str = "layer"
    id_source: str | None = None
    url_source: str | None = None
    nom_couche_source: str | None = None


def convertir_qml(chemin_qml: Path, params: ParametresConversion) -> dict:
    """Lit `chemin_qml` et produit le(s) document(s) demandé(s) par
    `params.cible`. Lève les exceptions NOMMÉES de styleforge_core telles
    quelles (ErreurLectureQML, ExpressionPivotNonEcrite) — c'est à
    l'appelant (route HTTP ou job de lot) de les traduire dans son propre
    vocabulaire de réponse, jamais à cette fonction de les avaler."""
    if params.cible in ("mbstyle", "sld_et_mbstyle") and not (
        params.id_source and params.url_source and params.nom_couche_source
    ):
        raise ParametresSourceManquants(
            "id_source, url_source et nom_couche_source sont obligatoires "
            "pour produire un document MBStyle — ecrire_mbstyle() ne "
            "suppose jamais de source de tuiles par défaut."
        )

    resultat = lire_fichier_qml(
        str(chemin_qml),
        nom_style=params.nom_style,
        dpi=params.dpi,
        sur_expression_non_traduite=params.sur_expression_non_traduite,
    )
    avertissements: list[str] = list(resultat.avertissements)

    sld_texte: str | None = None
    mbstyle_doc: dict | None = None

    if params.cible in ("sld", "sld_et_mbstyle"):
        sld_texte = ecrire_sld(
            resultat.style,
            nom_couche=params.nom_couche,
            avertissements=avertissements,
        )
    if params.cible in ("mbstyle", "sld_et_mbstyle"):
        mbstyle_texte = ecrire_mbstyle(
            resultat.style,
            id_source=params.id_source,  # type: ignore[arg-type] — validé ci-dessus
            url_source=params.url_source,  # type: ignore[arg-type]
            nom_couche_source=params.nom_couche_source,  # type: ignore[arg-type]
            avertissements=avertissements,
        )
        mbstyle_doc = json.loads(mbstyle_texte)

    return {
        "nom_style": resultat.style.name or (params.nom_style or chemin_qml.stem),
        "avertissements": avertissements,
        "sld": sld_texte,
        "mbstyle": mbstyle_doc,
    }
