#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_pivot.py — Vérifie que le pivot typé (styleforge_core.pivot) :
  1. valide un pivot minimal réaliste (une règle, un MarkSymbolizer, un
     filtre simple) — la forme que produira le futur lecteur QML ;
  2. REJETTE une clé mal orthographiée au lieu de l'ignorer silencieusement
     — c'est la raison d'être du typage (cf. pivot/_base.py) ;
  3. accepte une propriété pilotée par une expression (Fcase) au lieu d'une
     valeur littérale — le cas des variantes "expression" du corpus niveau 1 ;
  4. survit à un aller-retour valider -> sérialiser -> revalider sans perte.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from pydantic import ValidationError

from styleforge_core.pivot import Style, valider_style, dumper_style


def test_pivot_minimal_valide():
    brut = {
        "name": "exemple",
        "rules": [{
            "name": "regle 1",
            "filter": ["==", {"name": "property", "args": ["typeass"]}, "A1"],
            "symbolizers": [{
                "kind": "Mark",
                "wellKnownName": "circle",
                "color": "#ff0000",
                "radius": 4,
            }],
        }],
    }
    style = valider_style(brut)
    assert isinstance(style, Style)
    wkn = style.rules[0].symbolizers[0].root.wellKnownName
    # wellKnownName est lui-même un RootModel (généré depuis un $ref partagé
    # du schéma) : la valeur texte est sous .root, pas directement comparable.
    assert getattr(wkn, "root", wkn) == "circle"
    print("OK : pivot minimal validé")


def test_cle_inconnue_rejetee():
    brut = {
        "name": "exemple",
        "rules": [{
            "name": "regle 1",
            "symbolizers": [{
                "kind": "Fill",
                # Faute volontaire, calquée sur le défaut réel constaté chez
                # bridge-style (graphicFillDistance écrit, jamais lu) :
                "graphicFillDistanceXXX": 10,
            }],
        }],
    }
    try:
        valider_style(brut)
    except ValidationError as e:
        assert "graphicFillDistanceXXX" in str(e) or "extra" in str(e).lower()
        print("OK : clé inconnue rejetée explicitement -", str(e).splitlines()[0])
        return
    raise AssertionError("Une clé inconnue aurait dû être rejetée (extra='forbid')")


def test_propriete_pilotee_par_expression():
    # Équivalent geostyler-style d'une propriété "size" pilotée par une
    # expression QGIS (cf. corpus/symbol_layers/**/*__expression.qml) :
    # ici un Fcase qui choisit entre deux couleurs selon un attribut.
    brut = {
        "name": "exemple",
        "rules": [{
            "name": "regle 1",
            "symbolizers": [{
                "kind": "Mark",
                "wellKnownName": "circle",
                "color": {
                    "name": "case",
                    "args": [
                        [{"name": "greaterThan", "args": [
                            {"name": "property", "args": ["valeur"]}, 1]},
                         "#ff0000"],
                        "#0000ff",
                    ],
                },
            }],
        }],
    }
    style = valider_style(brut)
    assert style.rules[0].symbolizers[0].root.color is not None
    print("OK : propriété pilotée par une expression (Fcase) validée")


def test_aller_retour_sans_perte():
    brut = {
        "name": "exemple",
        "rules": [{
            "name": "regle 1",
            "symbolizers": [{"kind": "Mark", "wellKnownName": "circle", "radius": 4}],
        }],
    }
    style1 = valider_style(brut)
    dump = dumper_style(style1)
    style2 = valider_style(dump)
    assert dumper_style(style2) == dump
    print("OK : aller-retour valider -> sérialiser -> revalider stable")


if __name__ == "__main__":
    test_pivot_minimal_valide()
    test_cle_inconnue_rejetee()
    test_propriete_pilotee_par_expression()
    test_aller_retour_sans_perte()
    print("\nTous les tests du pivot sont passés.")
