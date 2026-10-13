#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/test_sprites.py — suite de tests pour styleforge_core.sprites.SpriteRegistry,
en particulier la détection automatique des SVG « paramétriques »
(fill="param(fill)") et leur rendu en sprite SDF (masque alpha), ajoutés pour
permettre icon-color côté écrivain MBStyle (voir styleforge_core/writers/
mbstyle.py, _ecrire_icon_paint).

Ces tests ont besoin de Qt (PyQt5/PyQt6, ou qgis.PyQt) pour s'exécuter —
exactement le même repli que SpriteRegistry._qt() lui-même. Sans Qt
disponible dans l'environnement, ils sont marqués "skipped" plutôt
qu'échoués (cohérent avec le comportement de build() lui-même, qui se
dégrade proprement — écriture d'un index JSON seul — plutôt que d'échouer).
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

# Doit être positionné AVANT tout import Qt, pour permettre l'exécution dans
# un environnement sans serveur d'affichage (ce bac à sable de développement
# notamment) — cohérent avec la mention de QT_QPA_PLATFORM=offscreen déjà
# documentée dans styleforge_core/sprites.py. setdefault() : ne force rien si
# l'environnement (poste de production avec un vrai affichage) en décide
# autrement.
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest

from styleforge_core.sprites import SpriteRegistry

#: Reproduit la forme RÉELLE rencontrée dans le corpus CNIG (examples/qml,
#: cf. tests/test_sprites.py::test_build_svg_parametrique_rendu_en_masque_blanc)
#: — plusieurs attributs 'param(...)' simultanés sur le même élément, PAS
#: seulement 'fill' : un test qui n'utiliserait que 'fill="param(fill)"' seul
#: ne reproduirait pas le cas réel qui a fait échouer la première version de
#: ce correctif (QSvgRenderer rejette la forme entière dès qu'un AUTRE
#: attribut, ex. stroke="param(outline)", reste une valeur invalide).
SVG_PARAMETRIQUE = """<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 64 64">
  <g fill="param(fill)" fill-opacity="param(fill-opacity)" stroke="param(outline)"
     stroke-opacity="param(outline-opacity) 1" stroke-width="param(outline-width) 0">
    <circle cx="32" cy="32" r="28"/>
  </g>
</svg>
"""

SVG_NON_PARAMETRIQUE = """<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 64 64">
  <circle cx="32" cy="32" r="28" fill="#336699"/>
</svg>
"""


def _qt_disponible() -> bool:
    return SpriteRegistry()._qt() is not None


pytestmark = pytest.mark.skipif(
    not _qt_disponible(), reason="Qt (PyQt5/PyQt6/qgis.PyQt) indisponible dans cet environnement."
)


# --------------------------------------------------------------------------- détection de la convention paramétrique (register_svg)
def test_register_svg_parametrique_marque_sdf(tmp_path: Path):
    """Un SVG contenant littéralement 'fill="param(fill)"' (convention QGIS/
    GeoServer, cf. _MOTIF_SVG_PARAMETRIQUE) est marqué SDF — détection sur le
    CONTENU du fichier, pas sur une liste figée de noms : s'applique donc à
    n'importe quel futur SVG suivant la même convention."""
    svg_dir = tmp_path
    (svg_dir / "picto.svg").write_text(SVG_PARAMETRIQUE, encoding="utf-8")
    registry = SpriteRegistry(64)
    nom = registry.register_svg("picto.svg", svg_dir)
    assert nom is not None
    assert registry.svg_sdf[nom] is True


def test_register_svg_non_parametrique_pas_marque_sdf(tmp_path: Path):
    svg_dir = tmp_path
    (svg_dir / "picto.svg").write_text(SVG_NON_PARAMETRIQUE, encoding="utf-8")
    registry = SpriteRegistry(64)
    nom = registry.register_svg("picto.svg", svg_dir)
    assert nom is not None
    assert registry.svg_sdf[nom] is False


def test_register_svg_meme_reference_deux_fois_ne_relit_pas_le_fichier(tmp_path: Path):
    """Non-régression : enregistrer deux fois la même référence doit renvoyer
    le même nom sans erreur (chemin déjà existant dans self.svg, cf. 'if name
    not in self.svg')."""
    svg_dir = tmp_path
    (svg_dir / "picto.svg").write_text(SVG_PARAMETRIQUE, encoding="utf-8")
    registry = SpriteRegistry(64)
    nom1 = registry.register_svg("picto.svg", svg_dir)
    nom2 = registry.register_svg("picto.svg", svg_dir)
    assert nom1 == nom2
    assert registry.svg_sdf[nom1] is True


# --------------------------------------------------------------------------- fabrication de la feuille de sprites (build())
def test_build_sprite_json_marque_sdf_true_pour_svg_parametrique(tmp_path: Path):
    svg_dir = tmp_path / "svg"
    svg_dir.mkdir()
    (svg_dir / "param.svg").write_text(SVG_PARAMETRIQUE, encoding="utf-8")
    (svg_dir / "fixe.svg").write_text(SVG_NON_PARAMETRIQUE, encoding="utf-8")

    registry = SpriteRegistry(64)
    nom_param = registry.register_svg("param.svg", svg_dir)
    nom_fixe = registry.register_svg("fixe.svg", svg_dir)

    out_dir = tmp_path / "out"
    out_dir.mkdir()
    report = registry.build(out_dir)
    assert report["images"] is True

    import json
    index = json.loads((out_dir / "sprite.json").read_text(encoding="utf-8"))
    assert index[nom_param].get("sdf") is True
    assert "sdf" not in index[nom_fixe]


def test_build_svg_parametrique_rendu_en_masque_blanc(tmp_path: Path):
    """Vérifie le résultat VISUEL, pas seulement le drapeau JSON : un SVG
    paramétrique doit être rendu comme un masque BLANC opaque (teintable par
    icon-color au rendu), alors qu'un SVG non paramétrique garde sa couleur
    d'origine telle quelle (comportement préexistant, inchangé)."""
    from PyQt5.QtGui import QImage

    svg_dir = tmp_path / "svg"
    svg_dir.mkdir()
    (svg_dir / "param.svg").write_text(SVG_PARAMETRIQUE, encoding="utf-8")
    (svg_dir / "fixe.svg").write_text(SVG_NON_PARAMETRIQUE, encoding="utf-8")

    registry = SpriteRegistry(64)
    registry.register_svg("param.svg", svg_dir)
    registry.register_svg("fixe.svg", svg_dir)

    out_dir = tmp_path / "out"
    out_dir.mkdir()
    registry.build(out_dir)

    sheet = QImage(str(out_dir / "sprite.png"))
    assert not sheet.isNull()

    import json
    index = json.loads((out_dir / "sprite.json").read_text(encoding="utf-8"))

    def pixel_centre(nom):
        entry = index[nom]
        cx = entry["x"] + entry["width"] // 2
        cy = entry["y"] + entry["height"] // 2
        return sheet.pixelColor(cx, cy)

    # Repère les deux noms par le contenu de self.svg (chemin source).
    nom_param = next(n for n, p in registry.svg.items() if p.name == "param.svg")
    nom_fixe = next(n for n, p in registry.svg.items() if p.name == "fixe.svg")

    couleur_param = pixel_centre(nom_param)
    couleur_fixe = pixel_centre(nom_fixe)

    assert couleur_param.alpha() > 0, "le masque SDF doit rester opaque (sinon rien a teindre)"
    assert (couleur_param.red(), couleur_param.green(), couleur_param.blue()) == (255, 255, 255), (
        "un SVG parametrique doit etre rendu en masque BLANC, pas dans sa "
        "couleur d'origine invalide (param(fill) n'est pas interpretable par Qt)"
    )
    assert (couleur_fixe.red(), couleur_fixe.green(), couleur_fixe.blue()) == (0x33, 0x66, 0x99), (
        "un SVG non parametrique doit garder sa couleur d'origine, rendu inchange"
    )
