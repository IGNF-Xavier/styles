#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/test_sld.py — suite de tests structurels pour styleforge_core.writers.sld.

Même discipline que tests/test_expressions.py et tests/test_qml.py : des
assertions sur la STRUCTURE du XML produit (via xml.etree.ElementTree, pas de
comparaison de chaînes fragiles), plus, en fin de fichier, une section
clairement marquée "VÉRIFICATIONS ORACLE (manuelles)" qui documente les
vérifications déjà faites contre QGIS réel (PyQGIS, QgsVectorLayer.
loadSldStyle()) pendant le développement de ce module, sans les ré-exécuter
ici : ce fichier ne dépend PAS de QGIS pour tourner (PyQGIS reste un ORACLE de
test ponctuel sur la machine connectée de l'utilisateur, jamais une
dépendance des tests automatisés ni du runtime), donc ces vérifications sont
relatées, pas rejouées automatiquement.
"""
from __future__ import annotations

import sys
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from styleforge_core.writers.sld import ExpressionPivotNonEcrite, ecrire_sld

NS = {"sld": "http://www.opengis.net/sld", "ogc": "http://www.opengis.net/ogc"}


def _parse(xml_str: str) -> ET.Element:
    return ET.fromstring(xml_str)


def _rules(racine: ET.Element) -> list[ET.Element]:
    return racine.findall(".//sld:FeatureTypeStyle/sld:Rule", NS)


# --------------------------------------------------------------------------- structure de base
def test_structure_minimale_namedlayer_userstyle_featuretypestyle():
    style = {"name": "MonStyle", "rules": [{"name": "r1", "symbolizers": [
        {"kind": "Fill", "color": "#ff0000"},
    ]}]}
    racine = _parse(ecrire_sld(style, nom_couche="macouche"))
    assert racine.tag == "{http://www.opengis.net/sld}StyledLayerDescriptor"
    assert racine.get("version") == "1.0.0"
    nom = racine.find(".//sld:NamedLayer/sld:Name", NS)
    assert nom is not None and nom.text == "macouche"
    titre = racine.find(".//sld:UserStyle/sld:Title", NS)
    assert titre is not None and titre.text == "MonStyle"
    print("OK: structure minimale StyledLayerDescriptor/NamedLayer/UserStyle/FeatureTypeStyle")


def test_plusieurs_rules_dans_lordre():
    style = {"rules": [
        {"name": "premiere", "symbolizers": [{"kind": "Fill", "color": "#111111"}]},
        {"name": "seconde", "symbolizers": [{"kind": "Fill", "color": "#222222"}]},
    ]}
    racine = _parse(ecrire_sld(style))
    noms = [r.find("sld:Name", NS).text for r in _rules(racine)]
    assert noms == ["premiere", "seconde"]
    print("OK: ordre des Rule préservé")


# --------------------------------------------------------------------------- symbolizers littéraux
def test_symbolizer_fill_polygon_css_parameters():
    style = {"rules": [{"symbolizers": [
        {"kind": "Fill", "color": "#ff0000", "fillOpacity": 0.5,
         "outlineColor": "#000000", "outlineWidth": 1.5, "outlineOpacity": 0.8},
    ]}]}
    racine = _parse(ecrire_sld(style))
    poly = racine.find(".//sld:PolygonSymbolizer", NS)
    assert poly is not None
    fill_params = {p.get("name"): p.text for p in poly.findall("sld:Fill/sld:CssParameter", NS)}
    assert fill_params == {"fill": "#ff0000", "fill-opacity": "0.5"}
    stroke_params = {p.get("name"): p.text for p in poly.findall("sld:Stroke/sld:CssParameter", NS)}
    assert stroke_params == {"stroke": "#000000", "stroke-width": "1.5", "stroke-opacity": "0.8"}
    print("OK: FillSymbolizer -> PolygonSymbolizer, CssParameter fill/stroke corrects")


def test_symbolizer_mark_point_wellknownname_et_size_diametre():
    style = {"rules": [{"symbolizers": [
        {"kind": "Mark", "wellKnownName": "square", "color": "#00ff00", "radius": 5.0},
    ]}]}
    racine = _parse(ecrire_sld(style))
    point = racine.find(".//sld:PointSymbolizer", NS)
    wkn = point.find("sld:Graphic/sld:Mark/sld:WellKnownName", NS)
    assert wkn is not None and wkn.text == "square"
    taille = point.find("sld:Graphic/sld:Size", NS)
    # SLD Size = diamètre ; pivot radius=5.0 -> Size=10.0 (radius*2, convention
    # vérifiée contre l'oracle QGIS, symétrique à radius = QGIS size/2 côté lecteur)
    assert taille is not None and taille.text == "10.0"
    print("OK: MarkSymbolizer -> PointSymbolizer, WellKnownName, Size = radius*2")


def test_symbolizer_line_stroke_dasharray_et_cap_join():
    style = {"rules": [{"symbolizers": [
        {"kind": "Line", "color": "#0000ff", "width": 2.0, "dasharray": [4, 2], "cap": "round", "join": "bevel"},
    ]}]}
    racine = _parse(ecrire_sld(style))
    ligne = racine.find(".//sld:LineSymbolizer", NS)
    params = {p.get("name"): p.text for p in ligne.findall("sld:Stroke/sld:CssParameter", NS)}
    assert params["stroke"] == "#0000ff"
    assert params["stroke-width"] == "2.0"
    assert params["stroke-dasharray"] == "4 2"
    assert params["stroke-linecap"] == "round"
    assert params["stroke-linejoin"] == "bevel"
    print("OK: LineSymbolizer, dasharray/cap/join corrects")


def test_symbolizer_inconnu_leve_exception_nommee():
    # Icon et Text sont désormais écrits (voir test_symbolizer_icon_* et
    # test_text_symbolizer_*) ; Raster reste hors portée (voir
    # test_raster_symbolizer_leve_exception_avec_raison_specifique pour la
    # raison précise — refusé par l'oracle lui-même, pas juste non écrit).
    style = {"rules": [{"symbolizers": [{"kind": "Raster"}]}]}
    try:
        ecrire_sld(style)
        raise AssertionError("aucune exception levée pour un symbolizer 'Raster' hors portée")
    except ExpressionPivotNonEcrite as e:
        assert "Raster" in str(e)
        print(f"OK: symbolizer 'Raster' hors portée -> ExpressionPivotNonEcrite ({e})")


def test_symbolizer_icon_svg_ecrit_avec_size_direct_et_rotation():
    style = {"rules": [{"symbolizers": [
        {"kind": "Icon", "image": "file:///tmp/x.svg", "format": "image/svg+xml", "size": 28, "rotate": 45},
    ]}]}
    avert = []
    racine = _parse(ecrire_sld(style, avertissements=avert))
    point = racine.find(".//sld:PointSymbolizer", NS)
    ext = point.find("sld:Graphic/sld:ExternalGraphic", NS)
    assert ext is not None
    resource = ext.find("sld:OnlineResource", NS)
    assert resource.get("{http://www.w3.org/1999/xlink}href") == "file:///tmp/x.svg"
    assert ext.find("sld:Format", NS).text == "image/svg+xml"
    taille = point.find("sld:Graphic/sld:Size", NS)
    # Contrairement à MarkSymbolizer.radius (Size = radius*2), IconSymbolizer.size
    # correspond DIRECTEMENT à sld:Size, vérifié séparément contre l'oracle.
    assert taille is not None and taille.text == "28"
    rotation = point.find("sld:Graphic/sld:Rotation", NS)
    assert rotation is not None and rotation.text == "45"
    assert avert == []
    print("OK: IconSymbolizer image/svg+xml -> ExternalGraphic, Size direct (pas *2), Rotation")


def test_symbolizer_icon_png_leve_exception_format_non_ecrit():
    """La découverte centrale de cette extension : image/png (syntaxe SLD
    identique à image/svg+xml, fichier par ailleurs valide) échoue
    silencieusement à l'import dans QGIS alors que image/svg+xml fonctionne —
    vérifié par rendu pixel, pas seulement par inspection des propriétés."""
    for fmt in ("image/png", "image/gif", "image/jpeg", "image/jpg"):
        style = {"rules": [{"symbolizers": [{"kind": "Icon", "image": "x", "format": fmt}]}]}
        try:
            ecrire_sld(style)
            raise AssertionError(f"aucune exception levée pour IconSymbolizer.format={fmt!r}")
        except ExpressionPivotNonEcrite as e:
            assert fmt in str(e)
    print("OK: IconSymbolizer.format non-svg (png/gif/jpeg/jpg) -> ExpressionPivotNonEcrite (4/4)")


def test_symbolizer_icon_sprite_leve_exception():
    style = {"rules": [{"symbolizers": [{"kind": "Icon", "image": {"source": "sheet.png", "position": [0, 0]}}]}]}
    try:
        ecrire_sld(style)
        raise AssertionError("aucune exception levée pour IconSymbolizer.image en Sprite (dict)")
    except ExpressionPivotNonEcrite as e:
        print(f"OK: IconSymbolizer.image en Sprite (sheet) -> ExpressionPivotNonEcrite ({e})")


def test_symbolizer_icon_base64_sans_resolveur_leve_exception_nommee():
    """IconSymbolizer.image peut, tel que produit par certains lecteurs QML
    (SLYR/CNIG), être un SVG embarqué en base64 (convention QGIS
    'base64:<données>') plutôt qu'un chemin/URL. Cet écrivain, zéro-E/S, ne
    peut pas matérialiser ce contenu en fichier lui-même : sans callback de
    résolution fourni, il doit lever ExpressionPivotNonEcrite — jamais écrire
    la chaîne 'base64:...' telle quelle dans xlink:href (syntaxiquement
    valide mais inutilisable par GeoServer, échec silencieux évité)."""
    style = {"rules": [{"symbolizers": [
        {"kind": "Icon", "image": "base64:PD94bWwgdmVyc2lvbj0=", "format": "image/svg+xml"},
    ]}]}
    try:
        ecrire_sld(style)
        raise AssertionError("aucune exception levée pour IconSymbolizer.image en base64 sans résolveur")
    except ExpressionPivotNonEcrite as e:
        assert "base64" in str(e)
    print("OK: IconSymbolizer.image en base64 sans resoudre_image_embarquee -> ExpressionPivotNonEcrite")


def test_symbolizer_icon_base64_resolveur_fournit_le_href():
    """Avec un callback 'resoudre_image_embarquee', l'écrivain reste zéro-E/S
    (il ne décode/écrit toujours rien lui-même) mais délègue la résolution :
    le href qu'il écrit est exactement ce que le callback renvoie."""
    appels = []

    def resoudre(valeur: str) -> str:
        appels.append(valeur)
        return "svg/cnig/x_a1b2c3.svg"

    style = {"rules": [{"symbolizers": [
        {"kind": "Icon", "image": "base64:PD94bWwgdmVyc2lvbj0=", "format": "image/svg+xml", "size": 20},
    ]}]}
    racine = _parse(ecrire_sld(style, resoudre_image_embarquee=resoudre))
    resource = racine.find(".//sld:OnlineResource", NS)
    assert resource.get("{http://www.w3.org/1999/xlink}href") == "svg/cnig/x_a1b2c3.svg"
    assert appels == ["base64:PD94bWwgdmVyc2lvbj0="]
    print("OK: IconSymbolizer.image en base64 avec resoudre_image_embarquee -> href = valeur renvoyée par le callback")


def test_symbolizer_icon_base64_resolveur_renvoie_none_leve_exception():
    """Le callback peut lui-même échouer à résoudre (retourne None) — même
    discipline que son absence : ExpressionPivotNonEcrite, pas un href vide
    ou invalide écrit en silence."""
    style = {"rules": [{"symbolizers": [
        {"kind": "Icon", "image": "base64:XX", "format": "image/svg+xml"},
    ]}]}
    try:
        ecrire_sld(style, resoudre_image_embarquee=lambda v: None)
        raise AssertionError("aucune exception levée quand le résolveur renvoie None")
    except ExpressionPivotNonEcrite as e:
        assert "base64" in str(e)
    print("OK: resoudre_image_embarquee renvoyant None -> ExpressionPivotNonEcrite (comme en son absence)")


def test_fill_graphicfill_icon_base64_resolveur_applique_aussi_au_graphicfill():
    """Le résolveur doit être appliqué de façon uniforme, y compris pour un
    Icon imbriqué dans FillSymbolizer.graphicFill (pas seulement l'Icon
    top-level) — même chemin de code (_construire_graphic_icon), vérifié
    séparément pour ne rien supposer."""
    style = {"rules": [{"symbolizers": [
        {"kind": "Fill", "graphicFill": {
            "kind": "Icon", "image": "base64:PD94bWwgdmVyc2lvbj0=", "format": "image/svg+xml", "size": 10,
        }},
    ]}]}
    racine = _parse(ecrire_sld(style, resoudre_image_embarquee=lambda v: "svg/cnig/motif.svg"))
    resource = racine.find(".//sld:Fill/sld:GraphicFill//sld:OnlineResource", NS)
    assert resource.get("{http://www.w3.org/1999/xlink}href") == "svg/cnig/motif.svg"
    print("OK: FillSymbolizer.graphicFill(Icon base64) -> resoudre_image_embarquee appliqué aussi ici")


def test_opacity_graphic_ecrite_mais_avertie_non_verifiee_mark_et_icon():
    """Découverte de cette extension : <Graphic><Opacity> EST écrite (c'est
    une construction OGC SE standard) mais un rendu pixel réel (Opacity=1.0
    vs 0.2 sur le même symbole) a confirmé que QGIS 3.40 l'ignore — pour
    Mark ET pour Icon. Écrite avec avertissement explicite, jamais en
    silence, plutôt que retirée : la limite est chez l'oracle QGIS, pas
    dans la norme OGC SE que GeoServer honore probablement."""
    for sym in (
        {"kind": "Mark", "color": "#f00", "opacity": 0.5},
        {"kind": "Icon", "image": "x.svg", "format": "image/svg+xml", "opacity": 0.5},
    ):
        style = {"rules": [{"symbolizers": [sym]}]}
        avert = []
        racine = _parse(ecrire_sld(style, avertissements=avert))
        opacite = racine.find(".//sld:Graphic/sld:Opacity", NS)
        assert opacite is not None and opacite.text == "0.5"
        assert any("Opacity" in a and "QGIS" in a for a in avert)
    print("OK: Graphic/Opacity écrite (Mark et Icon) avec avertissement explicite (non vérifiée par l'oracle)")


# --------------------------------------------------------------------------- graphicFill / graphicStroke
def test_fill_graphicfill_mark_vers_fill_graphicfill_graphic_mark():
    style = {"rules": [{"symbolizers": [
        {"kind": "Fill", "graphicFill": {"kind": "Mark", "wellKnownName": "circle", "color": "#ff0000", "radius": 3}},
    ]}]}
    racine = _parse(ecrire_sld(style))
    gf = racine.find(".//sld:PolygonSymbolizer/sld:Fill/sld:GraphicFill", NS)
    assert gf is not None
    mark = gf.find("sld:Graphic/sld:Mark", NS)
    assert mark is not None and mark.find("sld:WellKnownName", NS).text == "circle"
    taille = gf.find("sld:Graphic/sld:Size", NS)
    assert taille is not None and taille.text == "6.0"  # radius*2, même convention que Mark autonome
    print("OK: FillSymbolizer.graphicFill (Mark) -> Fill/GraphicFill/Graphic/Mark, Size=radius*2")


def test_fill_graphicfill_icon_svg_vers_fill_graphicfill_graphic_externalgraphic():
    style = {"rules": [{"symbolizers": [
        {"kind": "Fill", "graphicFill": {"kind": "Icon", "image": "x.svg", "format": "image/svg+xml", "size": 10}},
    ]}]}
    racine = _parse(ecrire_sld(style))
    ext = racine.find(".//sld:Fill/sld:GraphicFill/sld:Graphic/sld:ExternalGraphic", NS)
    assert ext is not None
    assert ext.find("sld:Format", NS).text == "image/svg+xml"
    print("OK: FillSymbolizer.graphicFill (Icon svg) -> Fill/GraphicFill/Graphic/ExternalGraphic")


def test_fill_graphicfill_ecrase_color_ignore_sans_erreur():
    # color/fillOpacity du FillSymbolizer sont ignorés (pas d'erreur) quand
    # graphicFill est présent : le schéma SLD n'autorise qu'un seul des deux
    # (CssParameter OU GraphicFill) dans l'élément Fill.
    style = {"rules": [{"symbolizers": [
        {"kind": "Fill", "color": "#00ff00", "graphicFill": {"kind": "Mark", "color": "#ff0000"}},
    ]}]}
    racine = _parse(ecrire_sld(style))
    fill = racine.find(".//sld:PolygonSymbolizer/sld:Fill", NS)
    assert fill.find("sld:GraphicFill", NS) is not None
    assert fill.find("sld:CssParameter", NS) is None
    print("OK: graphicFill présent -> color/fillOpacity du FillSymbolizer ignorés, pas de conflit XML")


def test_line_graphicstroke_mark_vers_stroke_graphicstroke_avec_gap():
    style = {"rules": [{"symbolizers": [
        {"kind": "Line", "graphicStroke": {"kind": "Mark", "wellKnownName": "circle", "color": "#0000ff"}, "spacing": 15},
    ]}]}
    racine = _parse(ecrire_sld(style))
    gs = racine.find(".//sld:LineSymbolizer/sld:Stroke/sld:GraphicStroke", NS)
    assert gs is not None
    assert gs.find("sld:Graphic/sld:Mark", NS) is not None
    gap = gs.find("sld:Gap", NS)
    assert gap is not None and gap.text == "15"
    print("OK: LineSymbolizer.graphicStroke (Mark) -> Stroke/GraphicStroke, spacing -> Gap")


def test_line_graphicstroke_icon_ecrit_avec_avertissement_non_verifie():
    """Extension du 2026-10-12 : Icon (ExternalGraphic) imbriqué dans
    Stroke/GraphicStroke EST désormais écrit (conforme OGC SE 1.1.0, même
    construction que pour Fill/GraphicFill et PointSymbolizer) — sur
    demande explicite de maximiser la compatibilité du corpus réel plutôt
    que d'échouer. QGIS ne sachant pas relire cet élément, l'oracle habituel
    de ce module ne peut PAS le vérifier : un avertissement explicite le dit
    à chaque occurrence, ce n'est jamais présenté comme vérifié."""
    style = {"rules": [{"symbolizers": [
        {"kind": "Line", "graphicStroke": {"kind": "Icon", "image": "x.svg", "format": "image/svg+xml"}},
    ]}]}
    avert = []
    racine = _parse(ecrire_sld(style, avertissements=avert))
    gs = racine.find(".//sld:LineSymbolizer/sld:Stroke/sld:GraphicStroke", NS)
    assert gs is not None
    ext = gs.find("sld:Graphic/sld:ExternalGraphic", NS)
    assert ext is not None
    resource = ext.find("sld:OnlineResource", NS)
    assert resource.get("{http://www.w3.org/1999/xlink}href") == "x.svg"
    assert any("PAS VÉRIFIÉ PAR L'ORACLE QGIS" in a for a in avert)
    print("OK: LineSymbolizer.graphicStroke(Icon) -> Stroke/GraphicStroke/Graphic/ExternalGraphic écrit, avertissement émis")


def test_line_graphicfill_leve_exception_verifie_casse():
    style = {"rules": [{"symbolizers": [
        {"kind": "Line", "graphicFill": {"kind": "Mark", "color": "#ff0000"}},
    ]}]}
    try:
        ecrire_sld(style)
        raise AssertionError("aucune exception levée pour LineSymbolizer.graphicFill")
    except ExpressionPivotNonEcrite as e:
        print(f"OK: LineSymbolizer.graphicFill -> ExpressionPivotNonEcrite (vérifié cassé, contrairement à Fill) ({e})")


def test_line_graphicfill_et_graphicstroke_simultanes_leve_exception():
    style = {"rules": [{"symbolizers": [
        {"kind": "Line", "graphicFill": {"kind": "Mark"}, "graphicStroke": {"kind": "Mark"}},
    ]}]}
    try:
        ecrire_sld(style)
        raise AssertionError("aucune exception levée pour graphicFill+graphicStroke simultanés")
    except ExpressionPivotNonEcrite as e:
        print(f"OK: graphicFill+graphicStroke simultanés (ambigu) -> ExpressionPivotNonEcrite ({e})")


# --------------------------------------------------------------------------- TextSymbolizer
def test_text_symbolizer_complet_avec_champ_seul_font_halo_rotation():
    style = {"rules": [{"symbolizers": [
        {"kind": "Fill", "color": "#eee"},
        {"kind": "Text", "label": "{{nom}}", "font": ["Arial"], "size": 14, "fontWeight": "bold",
         "fontStyle": "italic", "color": "#222222", "haloWidth": 2, "haloColor": "#ffffff", "rotate": 30},
    ]}]}
    racine = _parse(ecrire_sld(style))
    texte = racine.find(".//sld:TextSymbolizer", NS)
    assert texte is not None
    label = texte.find("sld:Label/ogc:PropertyName", NS)
    assert label is not None and label.text == "nom"
    font_params = {p.get("name"): p.text for p in texte.findall("sld:Font/sld:CssParameter", NS)}
    assert font_params == {"font-family": "Arial", "font-size": "14", "font-weight": "bold", "font-style": "italic"}
    fill_params = {p.get("name"): p.text for p in texte.findall("sld:Fill/sld:CssParameter", NS)}
    assert fill_params == {"fill": "#222222"}
    halo = texte.find("sld:Halo", NS)
    assert halo.find("sld:Radius", NS).text == "2"
    assert halo.find("sld:Fill/sld:CssParameter", NS).text == "#ffffff"
    rotation = texte.find("sld:LabelPlacement/sld:PointPlacement/sld:Rotation", NS)
    # Rotation SLD = (360 - rotate pivot) % 360, vérifié contre l'oracle sur 5 points.
    assert rotation is not None and rotation.text == "330.0"
    print("OK: TextSymbolizer complet (label champ seul, font, halo, rotation inversée) correctement écrit")


def test_text_symbolizer_label_fproperty_nu_equivalent_au_template():
    style = {"rules": [{"symbolizers": [
        {"kind": "Fill", "color": "#eee"},
        {"kind": "Text", "label": {"name": "property", "args": ["nom"]}},
    ]}]}
    racine = _parse(ecrire_sld(style))
    label = racine.find(".//sld:TextSymbolizer/sld:Label/ogc:PropertyName", NS)
    assert label is not None and label.text == "nom"
    print("OK: TextSymbolizer.label en Fproperty nu -> même résultat que le template \"{{champ}}\"")


def test_text_symbolizer_label_litteral_ou_mixte_leve_exception():
    """La découverte centrale de cette extension pour Text : un label
    littéral pur échoue à produire un labeling QGIS (silencieusement), et un
    label mixte texte+champ importe le champ mais PERD le texte littéral
    sans avertissement — les deux sont donc rejetés explicitement ici plutôt
    que silencieusement produits puis silencieusement dégradés par QGIS."""
    for label in ("texte fixe", "Nom: {{nom}}", "{{nom}} (valeur)"):
        style = {"rules": [{"symbolizers": [
            {"kind": "Fill", "color": "#eee"},
            {"kind": "Text", "label": label},
        ]}]}
        try:
            ecrire_sld(style)
            raise AssertionError(f"aucune exception levée pour label={label!r}")
        except ExpressionPivotNonEcrite:
            pass
    print("OK: label littéral pur ou mixte texte+champ (3 cas) -> ExpressionPivotNonEcrite (3/3)")


def test_text_symbolizer_seul_dans_une_rule_leve_exception():
    """Vérifié contre l'oracle : une Rule ne contenant QU'un TextSymbolizer
    échoue ENTIÈREMENT au chargement SLD dans QGIS (pas seulement le texte)."""
    style = {"rules": [{"symbolizers": [{"kind": "Text", "label": "{{nom}}"}]}]}
    try:
        ecrire_sld(style)
        raise AssertionError("aucune exception levée pour une Rule ne contenant qu'un TextSymbolizer")
    except ExpressionPivotNonEcrite as e:
        print(f"OK: Rule avec Text seul (aucun autre symbolizer) -> ExpressionPivotNonEcrite ({e})")


def test_raster_symbolizer_leve_exception_avec_raison_specifique():
    style = {"rules": [{"symbolizers": [{"kind": "Raster"}]}]}
    try:
        ecrire_sld(style)
        raise AssertionError("aucune exception levée pour RasterSymbolizer")
    except ExpressionPivotNonEcrite as e:
        assert "Layer type 1 not supported" in str(e)
        print(f"OK: RasterSymbolizer -> ExpressionPivotNonEcrite, raison précise (oracle refuse de charger) ({e})")


def test_dasharray_non_numerique_leve_exception():
    style = {"rules": [{"symbolizers": [{"kind": "Line", "color": "#000", "dasharray": "4,2"}]}]}
    try:
        ecrire_sld(style)
        raise AssertionError("aucune exception levée pour dasharray non-liste-de-nombres")
    except ExpressionPivotNonEcrite as e:
        print(f"OK: dasharray littéral non conforme -> ExpressionPivotNonEcrite ({e})")


# --------------------------------------------------------------------------- restriction littéral-only (résultat de la découverte oracle)
def test_valeur_symbolizer_pilotee_par_expression_leve_exception():
    """La découverte centrale de ce chantier : une propriété de symbolizer
    pilotée par une expression pivot (Fproperty ici) N'est PAS écrite — elle
    lève ExpressionPivotNonEcrite avec le motif vérifié contre l'oracle PyQGIS
    (voir la docstring de styleforge_core.writers.sld)."""
    for prop, sym in (
        ("color", {"kind": "Mark", "color": {"name": "property", "args": ["c"]}}),
        ("radius", {"kind": "Mark", "radius": {"name": "property", "args": ["r"]}}),
        ("rotate", {"kind": "Mark", "rotate": {"name": "property", "args": ["rot"]}}),
        ("opacity", {"kind": "Mark", "opacity": {"name": "property", "args": ["op"]}}),
    ):
        style = {"rules": [{"symbolizers": [sym]}]}
        try:
            ecrire_sld(style)
            raise AssertionError(f"aucune exception levée pour {prop} piloté par expression")
        except ExpressionPivotNonEcrite as e:
            assert "expression" in str(e) or "oracle" in str(e)
    print("OK: color/radius/rotate/opacity pilotés par expression -> ExpressionPivotNonEcrite (4/4)")


def test_valeur_symbolizer_litterale_bool_et_none():
    style = {"rules": [{"symbolizers": [
        {"kind": "Fill", "color": "#fff", "fillOpacity": True},
    ]}]}
    racine = _parse(ecrire_sld(style))
    params = {p.get("name"): p.text for p in racine.findall(".//sld:Fill/sld:CssParameter", NS)}
    assert params["fill-opacity"] == "true"
    style_none = {"rules": [{"symbolizers": [{"kind": "Fill", "color": "#fff", "fillOpacity": None}]}]}
    racine2 = _parse(ecrire_sld(style_none))
    params2 = {p.get("name"): p.text for p in racine2.findall(".//sld:Fill/sld:CssParameter", NS)}
    assert "fill-opacity" not in params2
    print("OK: bool littéral -> 'true'/'false', None -> CssParameter omis (pas d'élément vide)")


def test_avertissement_pour_propriete_hors_portee_non_perdue_en_silence():
    # antialias : propriété FillSymbolizer réelle, jamais gérée par cette
    # itération de l'écrivain, doit produire un avertissement explicite et
    # non être silencieusement ignorée.
    style = {"rules": [{"symbolizers": [
        {"kind": "Fill", "color": "#fff", "antialias": True},
    ]}]}
    avert = []
    ecrire_sld(style, avertissements=avert)
    assert any("antialias" in a for a in avert)
    print(f"OK: antialias hors portée -> avertissement explicite, pas silencieux : {avert}")


def test_graphicfillpadding_hors_portee_avertit_sans_lever():
    style = {"rules": [{"symbolizers": [
        {"kind": "Fill", "graphicFill": {"kind": "Mark", "wellKnownName": "circle", "color": "#ff0000"},
         "graphicFillPadding": [2, 2, 2, 2]},
    ]}]}
    avert = []
    ecrire_sld(style, avertissements=avert)
    assert any("graphicFillPadding" in a for a in avert)
    print(f"OK: graphicFillPadding non géré -> avertissement explicite (pas une exception) : {avert}")


# --------------------------------------------------------------------------- filtres
def test_filtre_comparaison_simple_tuple():
    style = {"rules": [{"filter": ["==", {"name": "property", "args": ["type"]}, "A"],
                         "symbolizers": [{"kind": "Fill", "color": "#fff"}]}]}
    racine = _parse(ecrire_sld(style))
    cmp = racine.find(".//ogc:Filter/ogc:PropertyIsEqualTo", NS)
    assert cmp is not None
    assert cmp.find("ogc:PropertyName", NS).text == "type"
    assert cmp.find("ogc:Literal", NS).text == "A"
    print("OK: comparaison tuple '==' -> ogc:PropertyIsEqualTo")


def test_filtre_and_or_not_imbriques():
    filtre = ["&&",
              ["==", {"name": "property", "args": ["a"]}, "1"],
              ["!", ["||", ["==", {"name": "property", "args": ["b"]}, "2"],
                     ["==", {"name": "property", "args": ["c"]}, "3"]]]]
    style = {"rules": [{"filter": filtre, "symbolizers": [{"kind": "Fill", "color": "#fff"}]}]}
    racine = _parse(ecrire_sld(style))
    et = racine.find(".//ogc:Filter/ogc:And", NS)
    assert et is not None
    non = et.find("ogc:Not", NS)
    assert non is not None
    ou = non.find("ogc:Or", NS)
    assert ou is not None and len(ou.findall("ogc:PropertyIsEqualTo", NS)) == 2
    print("OK: AND(Not(OR(...))) imbriqué correctement traduit")


def test_filtre_is_null_et_not_is_null():
    style_null = {"rules": [{"filter": {"name": "equalTo", "args": [{"name": "property", "args": ["x"]}, None]},
                              "symbolizers": [{"kind": "Fill", "color": "#fff"}]}]}
    racine = _parse(ecrire_sld(style_null))
    assert racine.find(".//ogc:Filter/ogc:PropertyIsNull", NS) is not None

    style_not_null = {"rules": [{"filter": {"name": "notEqualTo", "args": [{"name": "property", "args": ["x"]}, None]},
                                  "symbolizers": [{"kind": "Fill", "color": "#fff"}]}]}
    racine2 = _parse(ecrire_sld(style_not_null))
    non = racine2.find(".//ogc:Filter/ogc:Not", NS)
    assert non is not None and non.find("ogc:PropertyIsNull", NS) is not None
    print("OK: IS NULL -> ogc:PropertyIsNull, IS NOT NULL -> ogc:Not/ogc:PropertyIsNull")


def test_filtre_in_reconstruit_en_or_de_equalto():
    style = {"rules": [{"filter": {"name": "in", "args": [{"name": "property", "args": ["cat"]}, "a", "b", "c"]},
                         "symbolizers": [{"kind": "Fill", "color": "#fff"}]}]}
    racine = _parse(ecrire_sld(style))
    ou = racine.find(".//ogc:Filter/ogc:Or", NS)
    assert ou is not None
    cmps = ou.findall("ogc:PropertyIsEqualTo", NS)
    assert len(cmps) == 3
    valeurs = [c.find("ogc:Literal", NS).text for c in cmps]
    assert valeurs == ["a", "b", "c"]
    print("OK: IN(cat, a,b,c) -> Or(PropertyIsEqualTo x 3), reconstruction fidèle")


def test_filtre_like_wildcard_convention_reutilisee_du_lecteur():
    style = {"rules": [{"filter": ["*=", {"name": "property", "args": ["nom"]}, "*abc*"],
                         "symbolizers": [{"kind": "Fill", "color": "#fff"}]}]}
    racine = _parse(ecrire_sld(style))
    like = racine.find(".//ogc:Filter/ogc:PropertyIsLike", NS)
    assert like is not None
    assert like.get("wildCard") == "*" and like.get("singleChar") == "."
    assert like.find("ogc:Literal", NS).text == "*abc*"
    print("OK: LIKE '*=' -> ogc:PropertyIsLike, convention wildCard='*'/singleChar='.' identique au lecteur")


def test_filtre_between_fbetween_dict_vers_propertyisbetween():
    """Fbetween EST désormais écrit : ogc:PropertyIsBetween est un opérateur
    OGC Filter natif (une itération précédente supposait, à tort, qu'aucun
    n'existait) — vérifié contre l'oracle PyQGIS : rule.filterExpression()
    reconstruit exactement 'x >= 10 AND x <= 20'."""
    style = {"rules": [{
        "filter": {"name": "between", "args": [{"name": "property", "args": ["x"]}, 10, 20]},
        "symbolizers": [{"kind": "Fill", "color": "#fff"}],
    }]}
    racine = _parse(ecrire_sld(style))
    between = racine.find(".//ogc:Filter/ogc:PropertyIsBetween", NS)
    assert between is not None
    assert between.find("ogc:PropertyName", NS).text == "x"
    assert between.find("ogc:LowerBoundary/ogc:Literal", NS).text == "10"
    assert between.find("ogc:UpperBoundary/ogc:Literal", NS).text == "20"
    print("OK: Fbetween (dict) -> ogc:PropertyIsBetween, LowerBoundary/UpperBoundary corrects")


def test_filtre_between_arite_invalide_leve_exception():
    style = {"rules": [{
        "filter": {"name": "between", "args": [{"name": "property", "args": ["x"]}, 10]},
        "symbolizers": [{"kind": "Fill", "color": "#fff"}],
    }]}
    try:
        ecrire_sld(style)
        raise AssertionError("aucune exception levée pour between(...) à 2 arguments")
    except ExpressionPivotNonEcrite as e:
        print(f"OK: between(...) arité invalide -> ExpressionPivotNonEcrite ({e})")


def test_filtre_between_tuple_forme_inexistante_leve_exception():
    # Aucune forme tuple pour BETWEEN dans le schéma pivot (seule Fbetween en
    # dict existe) : une hypothèse d'itération précédente à corriger, pas un
    # cas réel à écrire.
    style = {"rules": [{"filter": ["<=", 1, {"name": "property", "args": ["x"]}, 10],
                         "symbolizers": [{"kind": "Fill", "color": "#fff"}]}]}
    try:
        ecrire_sld(style)
        raise AssertionError("aucune exception levée pour la forme tuple '<=x<=' (inexistante)")
    except ExpressionPivotNonEcrite as e:
        print(f"OK: forme tuple BETWEEN inexistante -> ExpressionPivotNonEcrite ({e})")


def test_filtre_strmatches_forme_non_canonique_leve_exception():
    """"^a.*" n'est PAS la forme canonique produite par
    _motif_like_vers_regex (pas de "$" final) : ne peut provenir ni de LIKE
    ni de ILIKE dans ce projet (regexp_match QGIS, seule autre source
    possible d'une regex arbitraire, n'est explicitement pas traduit par le
    lecteur) — reste non écrit, par prudence plutôt que par supposition."""
    style = {"rules": [{"filter": {"name": "strMatches", "args": [{"name": "property", "args": ["x"]}, "^a.*"]},
                         "symbolizers": [{"kind": "Fill", "color": "#fff"}]}]}
    try:
        ecrire_sld(style)
        raise AssertionError("aucune exception levée pour strMatches (forme non canonique)")
    except ExpressionPivotNonEcrite as e:
        print(f"OK: strMatches forme non canonique -> ExpressionPivotNonEcrite ({e})")


def test_filtre_strmatches_ilike_canonique_vers_propertyislike():
    """La forme canonique ("(?i)" + "^...$" avec .*/./re.escape()) EST
    désormais écrite : vérifié à l'oracle QGIS (saveSldStyle() sur un
    filtre ILIKE natif produit exactement wildCard="%"/singleChar="_"/
    escape="\\\\"/matchCase="false" ; le document reconstruit à la main
    avec ces attributs round-trippe par loadSldStyle() vers
    filterExpression() == "idass ILIKE 'a1%'")."""
    style = {"rules": [{
        "filter": {"name": "strMatches", "args": [{"name": "property", "args": ["idass"]}, r"(?i)^a1\-.*$"]},
        "symbolizers": [{"kind": "Fill", "color": "#fff"}],
    }]}
    racine = _parse(ecrire_sld(style))
    like = racine.find(".//ogc:Filter/ogc:PropertyIsLike", NS)
    assert like is not None
    assert like.get("wildCard") == "%" and like.get("singleChar") == "_" and like.get("escape") == "\\"
    assert like.get("matchCase") == "false"
    assert like.find("ogc:PropertyName", NS).text == "idass"
    assert like.find("ogc:Literal", NS).text == "a1-%"
    print("OK: strMatches (ILIKE canonique) -> ogc:PropertyIsLike wildCard=%/singleChar=_/escape=\\/matchCase=false")


def test_filtre_strmatches_like_sensible_casse_pas_de_matchcase():
    """LIKE (sensible à la casse, pas de préfixe "(?i)") : pas d'attribut
    matchCase écrit (comportement par défaut OGC = sensible à la casse)."""
    style = {"rules": [{
        "filter": {"name": "strMatches", "args": [{"name": "property", "args": ["idass"]}, r"^a2\-.*$"]},
        "symbolizers": [{"kind": "Fill", "color": "#fff"}],
    }]}
    racine = _parse(ecrire_sld(style))
    like = racine.find(".//ogc:Filter/ogc:PropertyIsLike", NS)
    assert like is not None
    assert like.get("matchCase") is None
    assert like.find("ogc:Literal", NS).text == "a2-%"
    print("OK: strMatches (LIKE sensible à la casse) -> pas d'attribut matchCase")


def test_else_rule():
    style = {"rules": [{"elseRule": True, "symbolizers": [{"kind": "Fill", "color": "#fff"}]}]}
    racine = _parse(ecrire_sld(style))
    assert racine.find(".//sld:Rule/sld:ElseFilter", NS) is not None
    print("OK: elseRule -> sld:ElseFilter")


def test_scale_denominator_min_max():
    style = {"rules": [{"scaleDenominator": {"min": 1000, "max": 50000},
                         "symbolizers": [{"kind": "Fill", "color": "#fff"}]}]}
    racine = _parse(ecrire_sld(style))
    mn = racine.find(".//sld:Rule/sld:MinScaleDenominator", NS)
    mx = racine.find(".//sld:Rule/sld:MaxScaleDenominator", NS)
    assert mn is not None and mn.text == "1000"
    assert mx is not None and mx.text == "50000"
    print("OK: scaleDenominator.min/max -> MinScaleDenominator/MaxScaleDenominator")


def test_scale_denominator_expression_leve_exception():
    style = {"rules": [{"scaleDenominator": {"min": {"name": "property", "args": ["seuil"]}},
                         "symbolizers": [{"kind": "Fill", "color": "#fff"}]}]}
    try:
        ecrire_sld(style)
        raise AssertionError("aucune exception levée pour scaleDenominator piloté par expression")
    except ExpressionPivotNonEcrite as e:
        print(f"OK: scaleDenominator par expression -> ExpressionPivotNonEcrite ({e})")


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    echecs = 0
    for t in tests:
        try:
            t()
        except Exception as e:
            echecs += 1
            print(f"ECHEC {t.__name__}: {e}")
    print(f"\n{len(tests) - echecs}/{len(tests)} tests réussis.")
    if echecs:
        raise SystemExit(1)

# ------------------------------------------------------------------------- VÉRIFICATIONS ORACLE (manuelles, déjà faites — non ré-exécutées ici)
#
# Les assertions ci-dessus sont structurelles (elles vérifient le XML que ce
# module produit, pas ce qu'un moteur de rendu en ferait). Les vérifications
# suivantes ont été faites PENDANT le développement contre un vrai QGIS
# (3.40.4-Bratislava, via QgsVectorLayer.loadSldStyle() + inspection de
# rule.filterExpression() / symbolLayer.dataDefinedProperties()), machine
# connectée de l'utilisateur, PyQGIS utilisé UNIQUEMENT comme oracle de test
# (jamais importé par ce module ni par ces tests) :
#
#   1. FillSymbolizer/MarkSymbolizer/LineSymbolizer avec propriétés
#      LITTÉRALES (couleur, largeur, opacité, taille) : round-trip parfait,
#      valeurs relues identiques à celles écrites, y compris Size = radius*2.
#   2. Rule.filter : comparaisons, AND/OR imbriqués, IS NULL, NOT(IS NULL),
#      IN (reconstruit en OR), LIKE ('*=' -> wildCard='*') : les 5 formes
#      round-trippent à l'identique via rule.filterExpression().
#   3. DÉCOUVERTE CENTRALE (justifiant la restriction littéral-only ci-
#      dessus) : une propriété de symbolizer pilotée par une expression
#      (ogc:PropertyName ou ogc:Function dans un CssParameter/Size/Rotation/
#      Opacity) N'est PAS reprise par QgsVectorLayer.loadSldStyle() —
#      testé sous 3 formulations XML différentes (arbre arithmétique complet,
#      PropertyName nu, XML compact sans indentation), même résultat les 3
#      fois : symbolLayer.dataDefinedProperties().isActive(...) == False,
#      valeur statique par défaut de QGIS utilisée à la place. Vérifié comme
#      spécifique au chemin de code symbolizer-value (le chemin filtre, lui,
#      utilisant la même fonction _construire_element_valeur, fonctionne).
#
# Pour rejouer ces vérifications : écrire le SLD produit par ecrire_sld() sur
# la machine connectée (device_commit_files), puis, via
# mcp__remote-devices__qgis__execute_code, charger avec
# QgsVectorLayer(...).loadSldStyle(chemin) et inspecter le renderer obtenu.
