# -*- coding: utf-8 -*-
"""
styleforge_api.jobs — le travail exécuté par le worker RQ (phase 7).

traiter_lot() est la fonction enfilée par styleforge_api.queue.enfiler_lot
et exécutée par `python -m styleforge_api.worker`, jamais par le processus
API lui-même (c'est tout l'intérêt de la file : une requête POST /v1/batch
répond immédiatement avec un identifiant, le travail se fait ailleurs).

Un fichier en échec dans un lot n'invalide PAS les autres : chacun est
traité indépendamment, avec son propre statut et, en cas d'échec, le nom
et le message de l'exception NOMMÉE de styleforge-core qui l'a provoqué —
jamais un lot entier qui échoue pour un seul fichier fautif, et jamais un
échec individuel réduit à "quelque chose s'est mal passé".
"""
from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Any

from .conversion import ParametresConversion, ParametresSourceManquants, convertir_qml
from .storage import CleAbsente, obtenir_stockage


def traiter_lot(
    id_lot: str, chemins_entree: list[str], params_dict: dict[str, Any]
) -> dict[str, Any]:
    """`chemins_entree` : clés de styleforge_api.storage sous lesquelles
    POST /v1/batch a déposé chaque fichier .qml reçu. `params_dict` :
    ParametresConversion sérialisé en dict (un seul jeu de paramètres
    s'applique à tous les fichiers du lot — cohérent avec "un lot" comme
    une seule opération de conversion appliquée à plusieurs fichiers)."""
    stockage = obtenir_stockage()
    params = ParametresConversion(**params_dict)

    resultats: list[dict[str, Any]] = []
    for cle in chemins_entree:
        nom = cle.rsplit("/", 1)[-1]
        entree = {"nom": nom, "statut": "echec", "resultat": None, "erreur": None}
        try:
            contenu = stockage.lire(cle)
        except CleAbsente as exc:
            entree["erreur"] = {
                "type_erreur": "CleAbsente",
                "module_erreur": "styleforge_api.storage",
                "message": str(exc),
            }
            resultats.append(entree)
            continue

        with tempfile.TemporaryDirectory(prefix="styleforge-api-batch-") as tmp:
            chemin = Path(tmp) / nom
            chemin.write_bytes(contenu)
            try:
                resultat = convertir_qml(chemin, params)
                entree["statut"] = "ok"
                entree["resultat"] = resultat
            except ParametresSourceManquants as exc:
                entree["erreur"] = {
                    "type_erreur": "ParametresSourceManquants",
                    "module_erreur": "styleforge_api.conversion",
                    "message": str(exc),
                }
            except Exception as exc:  # noqa: BLE001 — voir docstring : jamais masqué
                entree["erreur"] = {
                    "type_erreur": type(exc).__name__,
                    "module_erreur": type(exc).__module__,
                    "message": str(exc),
                }
        resultats.append(entree)

    reussites = sum(1 for r in resultats if r["statut"] == "ok")
    return {
        "id_lot": id_lot,
        "fichiers_traites": len(resultats),
        "reussites": reussites,
        "echecs": len(resultats) - reussites,
        "resultats": resultats,
    }
