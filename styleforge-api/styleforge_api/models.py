# -*- coding: utf-8 -*-
"""
styleforge_api.models — Modèles pydantic de la couche HTTP.

À NE PAS confondre avec styleforge_core.pivot : ceux-ci décrivent la forme
des requêtes/réponses JSON de l'API, pas le pivot cartographique lui-même.
Le pivot a son propre contrat, versionné séparément (PivotV1, voir le plan
de bibliothèque section 5.3) ; ces modèles-ci peuvent évoluer avec l'API
sans que ça n'engage le pivot.
"""
from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

Cible = Literal["sld", "mbstyle", "sld_et_mbstyle"]
PolitiqueExpression = Literal["lever", "avertir"]


class ReponseConversion(BaseModel):
    """Réponse de POST /v1/convert."""

    nom_style: str
    avertissements: list[str] = Field(
        default_factory=list,
        description=(
            "TOUJOURS présents s'il y en a — un pivot ou un document "
            "syntaxiquement valide mais qui a perdu de l'information en "
            "silence est exactement le défaut que ce projet corrige "
            "(voir styleforge_core.readers.qml.LectureResultat)."
        ),
    )
    sld: str | None = Field(
        default=None, description="Document SLD 1.0.0 complet, si demandé."
    )
    mbstyle: dict[str, Any] | None = Field(
        default=None,
        description="Document Mapbox GL Style (JSON), si demandé.",
    )


class DetailProbleme(BaseModel):
    categorie: str
    occurrences: int
    exemples: list[str] = Field(default_factory=list)


class ReponseAudit(BaseModel):
    """Réponse de POST /v1/audit — reflète styleforge_core.audit.RapportAudit,
    sans en exposer directement les types internes (Counter/defaultdict)."""

    conforme: bool
    fichiers_controles: int
    problemes: list[DetailProbleme] = Field(default_factory=list)
    extensions: dict[str, int] = Field(
        default_factory=dict,
        description=(
            "Extensions GeoServer assumées (hors XSD 1.0.0 strict), p. ex. "
            "matchCase sur PropertyIsLike — nécessaires au rendu, "
            "comprises par GeoServer, mais qu'un validateur XSD strict "
            "refuserait. Jamais comptées comme un problème."
        ),
    )
    rapport_texte: str = Field(
        description="Même contenu, mis en forme lisible (styleforge_core."
                     "audit.formater_rapport)."
    )


class ErreurStructuree(BaseModel):
    """Corps d'une réponse 422 pour une exception nommée de styleforge-core
    (voir styleforge_api.erreurs) — jamais un message générique."""

    type_erreur: str
    module_erreur: str
    message: str


StatutLot = Literal["en_attente", "en_cours", "termine", "echec", "introuvable"]


class ReponseLotCree(BaseModel):
    """Réponse de POST /v1/batch — 202 Accepted, le traitement n'a pas
    encore eu lieu (phase 7, asynchrone par nature)."""

    id_lot: str
    statut: StatutLot
    nombre_fichiers: int


class DetailFichierLot(BaseModel):
    nom: str
    statut: Literal["ok", "echec"]
    resultat: ReponseConversion | None = None
    erreur: ErreurStructuree | None = None


class ReponseStatutLot(BaseModel):
    """Réponse de GET /v1/batch/{id_lot}."""

    id_lot: str
    statut: StatutLot
    fichiers_traites: int = 0
    reussites: int = 0
    echecs: int = 0
    resultats: list[DetailFichierLot] = Field(default_factory=list)
    erreur_infrastructure: str | None = Field(
        default=None,
        description=(
            "Rempli uniquement si le JOB LUI-MÊME a échoué (bug du "
            "worker, Redis indisponible...) — à distinguer d'un fichier "
            "individuel en échec, qui apparaît dans `resultats` avec son "
            "propre statut sans faire échouer le lot entier."
        ),
    )
