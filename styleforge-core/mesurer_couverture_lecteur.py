#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
mesurer_couverture_lecteur.py — Mesure, sur l'ENSEMBLE du corpus niveau 1
(../corpus), ce que le lecteur QML générique (styleforge_core.readers.qml)
sait effectivement traiter aujourd'hui, plutôt que de l'affirmer. Même
démarche que mesurer_couverture_expressions.py (niveau 3) : un chiffre
mesuré, pas estimé.

Produit corpus/rapport_couverture_lecteur_qml.json.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from styleforge_core.readers.qml import (
    CoucheDeSymboleNonSupportee,
    DocumentQMLInvalide,
    ErreurLectureQML,
    ProprieteExpressionNonTraduite,
    RendererNonSupporte,
    lire_fichier_qml,
)

CORPUS = Path(__file__).parent.parent / "corpus"


def classer(chemin: Path) -> dict:
    try:
        resultat = lire_fichier_qml(str(chemin), sur_expression_non_traduite="avertir")
        return {
            "fichier": str(chemin.relative_to(CORPUS)),
            "statut": "lu",
            "nb_rules": len(resultat.style.rules or []),
            "nb_avertissements": len(resultat.avertissements),
        }
    except RendererNonSupporte as e:
        return {"fichier": str(chemin.relative_to(CORPUS)), "statut": "renderer_non_supporte", "detail": str(e)}
    except CoucheDeSymboleNonSupportee as e:
        return {"fichier": str(chemin.relative_to(CORPUS)), "statut": "couche_non_supportee", "detail": str(e)}
    except ProprieteExpressionNonTraduite as e:
        return {"fichier": str(chemin.relative_to(CORPUS)), "statut": "expression_non_traduite", "detail": str(e)}
    except DocumentQMLInvalide as e:
        return {"fichier": str(chemin.relative_to(CORPUS)), "statut": "document_invalide", "detail": str(e)}
    except ErreurLectureQML as e:
        return {"fichier": str(chemin.relative_to(CORPUS)), "statut": "autre_erreur_lecture", "detail": str(e)}


def main() -> None:
    fichiers = sorted(CORPUS.glob("symbol_layers/**/*.qml")) + sorted(CORPUS.glob("renderers/**/*.qml"))
    resultats = [classer(f) for f in fichiers]

    par_statut: dict[str, int] = {}
    for r in resultats:
        par_statut[r["statut"]] = par_statut.get(r["statut"], 0) + 1

    rapport = {
        "total_fichiers": len(resultats),
        "par_statut": par_statut,
        "resultats": resultats,
    }
    sortie = CORPUS / "rapport_couverture_lecteur_qml.json"
    sortie.write_text(json.dumps(rapport, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"{len(resultats)} fichiers analysés")
    for statut, n in sorted(par_statut.items(), key=lambda kv: -kv[1]):
        print(f"  {statut:28s} {n:4d}")
    print(f"\nRapport détaillé : {sortie}")


if __name__ == "__main__":
    main()
