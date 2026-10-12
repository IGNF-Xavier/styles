#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_ellipse.py — Vérifie le contournement EllipseMarker (compat/ellipse.py) :
  1. chaque stratégie produit le rayon attendu sur les dimensions réelles
     du corpus (symbol_width=4, symbol_height=3, cf.
     corpus/symbol_layers/Marker/EllipseMarker.qml) ;
  2. une forme de base hors périmètre (ex. "triangle") est explicitement
     rejetée, pas approximée en silence ;
  3. approximer() sait signaler qu'il y a bien une perte d'information
     (largeur != hauteur) ou non (cercle déjà parfait).
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from styleforge_core.compat.ellipse import (
    approximer,
    rayon_cercle_equivalent,
    supporte,
)

# Dimensions réelles du corpus niveau 1 (EllipseMarker.qml et variantes) :
# symbol_width=4, symbol_height=3, toutes deux en MM.
LARGEUR, HAUTEUR = 4.0, 3.0


def test_strategie_moyenne():
    assert rayon_cercle_equivalent(LARGEUR, HAUTEUR, "moyenne") == (4.0 + 3.0) / 4
    print("OK : stratégie 'moyenne'")


def test_strategie_aire_egale():
    rayon = rayon_cercle_equivalent(LARGEUR, HAUTEUR, "aire_egale")
    aire_ellipse = math.pi * (LARGEUR / 2) * (HAUTEUR / 2)
    aire_cercle = math.pi * rayon**2
    assert math.isclose(aire_ellipse, aire_cercle, rel_tol=1e-9)
    print("OK : stratégie 'aire_egale' (aires identiques par construction)")


def test_strategie_max_et_min():
    assert rayon_cercle_equivalent(LARGEUR, HAUTEUR, "max") == 2.0
    assert rayon_cercle_equivalent(LARGEUR, HAUTEUR, "min") == 1.5
    print("OK : stratégies 'max' et 'min'")


def test_strategie_inconnue_rejetee():
    try:
        rayon_cercle_equivalent(LARGEUR, HAUTEUR, "bogus")  # type: ignore[arg-type]
    except ValueError as e:
        assert "bogus" in str(e)
        print("OK : stratégie inconnue rejetée -", str(e).splitlines()[0])
        return
    raise AssertionError("Une stratégie inconnue aurait dû être rejetée")


def test_dimensions_negatives_rejetees():
    try:
        rayon_cercle_equivalent(-1.0, HAUTEUR)
    except ValueError:
        print("OK : dimension négative rejetée")
        return
    raise AssertionError("Une dimension négative aurait dû être rejetée")


def test_forme_de_base_circle_supportee():
    assert supporte("circle")
    print("OK : forme de base 'circle' dans le périmètre de la décision")


def test_forme_de_base_hors_perimetre_rejetee():
    assert not supporte("triangle")
    try:
        approximer("triangle", LARGEUR, HAUTEUR)
    except ValueError as e:
        assert "triangle" in str(e)
        print("OK : forme de base hors périmètre rejetée -", str(e).splitlines()[0])
        return
    raise AssertionError("Une forme de base hors périmètre aurait dû être rejetée")


def test_approximer_signale_la_perte():
    resultat_ellipse = approximer("circle", LARGEUR, HAUTEUR)
    assert resultat_ellipse.well_known_name == "circle"
    assert resultat_ellipse.perte is True

    resultat_cercle_parfait = approximer("circle", 4.0, 4.0)
    assert resultat_cercle_parfait.perte is False
    assert resultat_cercle_parfait.radius == 2.0
    print("OK : approximer() distingue perte réelle et cercle déjà parfait")


def test_forme_de_base_rectangle_supportee_vers_square():
    """Extension du 2026-10-12 : rectangle (et square) -> WellKnownName
    'square', motivée par plu_inf_s.qml/psmv_inf_s.qml (EllipseMarker
    symbol_name='rectangle', 9.96 x 6 Point) qui bloquaient sans elle."""
    assert supporte("rectangle") and supporte("square")
    resultat = approximer("rectangle", 9.96, 6.0)
    assert resultat.well_known_name == "square"
    assert resultat.perte is True  # largeur != hauteur
    assert resultat.radius == rayon_cercle_equivalent(9.96, 6.0, "moyenne")
    print("OK : EllipseMarker 'rectangle' -> WellKnownName 'square', perte signalée")


def test_forme_de_base_square_parfait_sans_perte():
    resultat = approximer("square", 5.0, 5.0)
    assert resultat.well_known_name == "square"
    assert resultat.perte is False
    print("OK : EllipseMarker 'square' déjà carré -> pas de perte signalée")


def test_forme_de_base_triangle_toujours_hors_perimetre():
    """triangle/cross/diamond/arrow restent hors périmètre après
    l'extension square/rectangle : seules les formes à angles droits
    (cercle ou carré) ont une approximation honnête."""
    assert not supporte("triangle")
    try:
        approximer("triangle", LARGEUR, HAUTEUR)
    except ValueError:
        print("OK : 'triangle' toujours hors périmètre après l'extension square/rectangle")
        return
    raise AssertionError("'triangle' aurait dû rester hors périmètre")


if __name__ == "__main__":
    test_strategie_moyenne()
    test_strategie_aire_egale()
    test_strategie_max_et_min()
    test_strategie_inconnue_rejetee()
    test_dimensions_negatives_rejetees()
    test_forme_de_base_circle_supportee()
    test_forme_de_base_hors_perimetre_rejetee()
    test_approximer_signale_la_perte()
    print("\nTous les tests EllipseMarker sont passés.")
