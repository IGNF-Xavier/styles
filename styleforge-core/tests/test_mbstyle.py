#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/test_mbstyle.py — suite de tests structurels pour
styleforge_core.writers.mbstyle.

Même discipline que tests/test_sld.py : des assertions sur la STRUCTURE du
JSON produit (dict Python, pas de comparaison de chaînes fragiles), plus, en
fin de fichier, une section "VÉRIFICATIONS ORACLE" qui documente précisément
CE QUI A ÉTÉ vérifié contre QGIS réel (QgsMapBoxGlStyleConverter) pendant le
développement, et — point important pour ce module en particulier — ce qui
NE L'A PAS ENCORE ÉTÉ parce que la connexion à l'oracle a été interrompue en
cours de chantier (voir la docstring de styleforge_core.writers.mbstyle,
section "AVERTISSEMENT DE COUVERTURE EXPLICITE"). Ce fichier ne dépend pas
de QGIS pour tourner.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from styleforge_core.writers.mbstyle import ExpressionPivotNonEcrite, ecrire_mbstyle

SRC = dict(id_source="src", url_source="http://example.com/tiles.json", nom_couche_source="couche")


def _style(rules):
    return {"name": "MonStyle", "rules": rules}


def _rule(nom, symbolizers, **kw):
    r = {"name": nom, "symbolizers": symbolizers}
    r.update(kw)
    return r


def _doc(rules):
    return json.loads(ecrire_mbstyle(_style(rules), **SRC))


# --------------------------------------------------------------------------- structure de base / document
def test_structure_minimale_version_sources_layers():
    doc = _doc([_rule("r1", [{"kind": "Fill", "color": "#ff0000"}])])
    assert doc["version"] == 8
    assert doc["sources"] == {"src": {"type": "vector", "url": "http://example.com/tiles.json"}}
    assert len(doc["layers"]) == 1


def test_nom_style_ecrit_si_fourni():
    doc = _doc([_rule("r1", [{"kind": "Fill", "color": "#ff0000"}])])
    assert doc["name"] == "MonStyle"


def test_nom_style_absent_si_non_fourni():
    doc = json.loads(ecrire_mbstyle({"rules": [_rule("r1", [{"kind": "Fill", "color": "#ff0000"}])]}, **SRC))
    assert "name" not in doc


def test_une_layer_par_rule_dans_lordre():
    doc = _doc([
        _rule("premiere", [{"kind": "Fill", "color": "#ff0000"}]),
        _rule("deuxieme", [{"kind": "Fill", "color": "#00ff00"}]),
    ])
    assert [l["id"] for l in doc["layers"]] == ["premiere", "deuxieme"]


def test_layer_id_repli_sur_index_si_rule_sans_nom():
    doc = _doc([_rule(None, [{"kind": "Fill", "color": "#ff0000"}])])
    assert doc["layers"][0]["id"] == "layer-0"


def test_layer_source_et_source_layer_depuis_parametres():
    doc = _doc([_rule("r1", [{"kind": "Fill", "color": "#ff0000"}])])
    layer = doc["layers"][0]
    assert layer["source"] == "src"
    assert layer["source-layer"] == "couche"
    assert layer["type"] == "fill"


# --------------------------------------------------------------------------- FillSymbolizer -> paint
def test_fill_color_seul_ecrit_en_hex_litteral():
    doc = _doc([_rule("r1", [{"kind": "Fill", "color": "#ff0000"}])])
    assert doc["layers"][0]["paint"] == {"fill-color": "#ff0000"}


def test_fill_color_avec_fillopacity_egale_1_reste_hex_litteral():
    doc = _doc([_rule("r1", [{"kind": "Fill", "color": "#ff0000", "fillOpacity": 1}])])
    assert doc["layers"][0]["paint"]["fill-color"] == "#ff0000"


def test_fill_color_avec_fillopacity_devient_rgba():
    doc = _doc([_rule("r1", [{"kind": "Fill", "color": "#ff0000", "fillOpacity": 0.5}])])
    assert doc["layers"][0]["paint"]["fill-color"] == "rgba(255,0,0,0.5)"


def test_fill_opacity_pivot_devient_fill_opacity_mapbox():
    doc = _doc([_rule("r1", [{"kind": "Fill", "color": "#ff0000", "opacity": 0.8}])])
    paint = doc["layers"][0]["paint"]
    assert paint["fill-opacity"] == 0.8
    # 'opacity' (pivot) et 'fillOpacity' (pivot) sont deux champs DISTINCTS
    # avec des cibles Mapbox distinctes (fill-opacity vs canal alpha de
    # fill-color) : opacity seul ne doit PAS altérer fill-color.
    assert paint["fill-color"] == "#ff0000"


def test_fill_opacity_et_fillopacity_simultanes_independants():
    doc = _doc([_rule("r1", [
        {"kind": "Fill", "color": "#ff0000", "opacity": 0.8, "fillOpacity": 0.5,
         "outlineColor": "#000000", "outlineOpacity": 0.3},
    ])])
    paint = doc["layers"][0]["paint"]
    assert paint["fill-opacity"] == 0.8
    assert paint["fill-color"] == "rgba(255,0,0,0.5)"
    assert paint["fill-outline-color"] == "rgba(0,0,0,0.3)"


def test_outline_color_seul_ecrit_en_hex_litteral():
    doc = _doc([_rule("r1", [{"kind": "Fill", "color": "#ff0000", "outlineColor": "#0000ff"}])])
    assert doc["layers"][0]["paint"]["fill-outline-color"] == "#0000ff"


def test_fillopacity_sans_color_leve_exception():
    try:
        _doc([_rule("r1", [{"kind": "Fill", "fillOpacity": 0.5}])])
        assert False, "devait lever ExpressionPivotNonEcrite"
    except ExpressionPivotNonEcrite:
        pass


def test_outlineopacity_sans_outlinecolor_leve_exception():
    try:
        _doc([_rule("r1", [{"kind": "Fill", "color": "#ff0000", "outlineOpacity": 0.5}])])
        assert False, "devait lever ExpressionPivotNonEcrite"
    except ExpressionPivotNonEcrite:
        pass


def test_couleur_non_hex_leve_exception():
    try:
        _doc([_rule("r1", [{"kind": "Fill", "color": "red"}])])
        assert False, "devait lever ExpressionPivotNonEcrite"
    except ExpressionPivotNonEcrite:
        pass


def test_graphicfill_sans_resolveur_leve_exception():
    try:
        _doc([_rule("r1", [{"kind": "Fill", "graphicFill": {"kind": "Mark"}}])])
        assert False, "devait lever ExpressionPivotNonEcrite"
    except ExpressionPivotNonEcrite as e:
        assert "resoudre_sprite" in str(e)


def test_graphicfill_mark_ecrit_fill_pattern_via_resolveur():
    """Extension du 2026-10-12 : FillSymbolizer.graphicFill (un Mark — forme
    simple ou motif de hachure shape://...) n'est plus un échec dur — écrit
    en fill-pattern via le résolveur de sprite, le wellKnownName étant passé
    TEL QUEL au résolveur (même convention que SpriteRegistry.register_shape
    côté CLI)."""
    doc = json.loads(ecrire_mbstyle(
        _style([_rule("r1", [{
            "kind": "Fill", "color": "#ff0000",
            "graphicFill": {"kind": "Mark", "wellKnownName": "shape://slash"},
        }])]),
        resoudre_sprite=lambda jeton: f"motif_{jeton.replace('shape://', '')}",
        **SRC,
    ))
    layer = doc["layers"][0]
    assert layer["paint"]["fill-pattern"] == "motif_slash"
    assert layer["paint"]["fill-color"] == "#ff0000"


def test_graphicfill_icon_ecrit_fill_pattern_via_resolveur():
    doc = json.loads(ecrire_mbstyle(
        _style([_rule("r1", [{
            "kind": "Fill", "graphicFill": {"kind": "Icon", "image": "hachure.svg"},
        }])]),
        resoudre_sprite=lambda jeton: f"sprite_{Path(jeton).stem}",
        **SRC,
    ))
    assert doc["layers"][0]["paint"]["fill-pattern"] == "sprite_hachure"


def test_graphicfill_resolveur_renvoie_none_leve_exception():
    try:
        json.loads(ecrire_mbstyle(
            _style([_rule("r1", [{"kind": "Fill", "graphicFill": {"kind": "Mark", "wellKnownName": "x"}}])]),
            resoudre_sprite=lambda jeton: None, **SRC,
        ))
        assert False, "devait lever ExpressionPivotNonEcrite"
    except ExpressionPivotNonEcrite:
        pass


def test_couleur_pilotee_par_expression_leve_exception():
    try:
        _doc([_rule("r1", [{"kind": "Fill", "color": {"name": "property", "args": ["c"]}}])])
        assert False, "devait lever ExpressionPivotNonEcrite"
    except ExpressionPivotNonEcrite:
        pass


# --------------------------------------------------------------------------- propriétés de contour sans équivalent Mapbox (avertissement spécifique)
def test_outlinewidth_avertit_sans_lever_et_nest_pas_ecrit():
    avertissements: list[str] = []
    doc = json.loads(ecrire_mbstyle(
        _style([_rule("r1", [{"kind": "Fill", "color": "#ff0000", "outlineWidth": 2}])]),
        avertissements=avertissements, **SRC,
    ))
    assert "outlineWidth" not in json.dumps(doc["layers"][0]["paint"])
    assert any("outlineWidth" in a and "spec elle-même" in a for a in avertissements)


def test_outlinedasharray_avertit_sans_lever():
    avertissements: list[str] = []
    ecrire_mbstyle(
        _style([_rule("r1", [{"kind": "Fill", "color": "#ff0000", "outlineDasharray": [4, 2]}])]),
        avertissements=avertissements, **SRC,
    )
    assert any("outlineDasharray" in a for a in avertissements)


# --------------------------------------------------------------------------- propriété hors-portée générique (jamais perdue en silence)
def test_avertissement_pour_propriete_hors_portee_non_perdue_en_silence():
    avertissements: list[str] = []
    ecrire_mbstyle(
        _style([_rule("r1", [{"kind": "Fill", "color": "#ff0000", "graphicFillPadding": [1, 1, 1, 1]}])]),
        avertissements=avertissements, **SRC,
    )
    assert any("graphicFillPadding" in a for a in avertissements)


def test_antialias_ecrit_en_litteral():
    doc = _doc([_rule("r1", [{"kind": "Fill", "color": "#ff0000", "antialias": False}])])
    assert doc["layers"][0]["paint"]["fill-antialias"] is False


# --------------------------------------------------------------------------- Rule.filter -> expression Mapbox
def _prop(champ):
    return {"name": "property", "args": [champ]}


def test_filtre_comparaison_tuple_devient_expression_get():
    doc = _doc([_rule("r1", [{"kind": "Fill", "color": "#ff0000"}], filter=["==", _prop("cls"), "A"])])
    assert doc["layers"][0]["filter"] == ["==", ["get", "cls"], "A"]


def test_filtre_and_or_imbriques():
    f = ["&&", ["==", _prop("cls"), "A"], ["||", [">", _prop("pop"), 100], ["<", _prop("pop"), 10]]]
    doc = _doc([_rule("r1", [{"kind": "Fill", "color": "#ff0000"}], filter=f)])
    assert doc["layers"][0]["filter"] == [
        "all", ["==", ["get", "cls"], "A"],
        ["any", [">", ["get", "pop"], 100], ["<", ["get", "pop"], 10]],
    ]


def test_filtre_not_sur_comparaison_leve_exception():
    # Vérifié contre l'oracle QGIS : ["!", ["==",...]] est rejeté par
    # QgsMapBoxGlStyleConverter (avertissement "!==" non supporté) et fait
    # perdre TOUT le filtre (filterExpression vide -> matche tout) — donc
    # cet écrivain refuse de le produire plutôt que de risquer ce silence.
    try:
        _doc([_rule("r1", [{"kind": "Fill", "color": "#ff0000"}], filter=["!", ["==", _prop("cls"), "A"]])])
        assert False, "devait lever ExpressionPivotNonEcrite"
    except ExpressionPivotNonEcrite:
        pass


def test_filtre_not_sur_and_or_leve_exception():
    # Même constat oracle que ci-dessus, pour "!" devant "all"/"any"
    # (["!", ["all"/"any", ...]] -> "!all"/"!any" non supportés côté QGIS).
    f = {"name": "not", "args": [{"name": "and", "args": [
        {"name": "equalTo", "args": [_prop("cls"), "A"]},
        {"name": "equalTo", "args": [_prop("pop"), 10]},
    ]}]}
    try:
        _doc([_rule("r1", [{"kind": "Fill", "color": "#ff0000"}], filter=f)])
        assert False, "devait lever ExpressionPivotNonEcrite"
    except ExpressionPivotNonEcrite:
        pass


def test_filtre_is_null_devient_egalite_a_null():
    # equalTo(champ, null) == IS NULL. L'ancienne forme
    # ["==", ["get", champ], None] — pourtant corroborée par une lecture
    # indépendante de geostyler-cli — s'est avérée BRISÉE contre l'oracle
    # QGIS (filtre tronqué/invalide) : cet écrivain produit désormais
    # ["!", ["has", champ]], vérifié exact contre QGIS ('"champ" IS NULL').
    f = {"name": "equalTo", "args": [_prop("cls"), None]}
    doc = _doc([_rule("r1", [{"kind": "Fill", "color": "#ff0000"}], filter=f)])
    assert doc["layers"][0]["filter"] == ["!", ["has", "cls"]]


def test_filtre_not_is_null():
    # notEqualTo(champ, null) == IS NOT NULL : ["has", champ] (pas
    # ["==", ..., None]), vérifié exact contre QGIS ('"champ" IS NOT NULL').
    f = {"name": "notEqualTo", "args": [_prop("cls"), None]}
    doc = _doc([_rule("r1", [{"kind": "Fill", "color": "#ff0000"}], filter=f)])
    assert doc["layers"][0]["filter"] == ["has", "cls"]


def test_filtre_not_devant_has_fonctionne():
    # "!" EST fiable devant ["has", champ] — un des deux seuls cas vérifiés
    # sûrs (l'autre étant "in", couvert par test_filtre_not_devant_in_fonctionne).
    # not(notEqualTo(champ, null)) = not(IS NOT NULL) = IS NULL, et
    # structurellement not(["has", champ]) = ["!", ["has", champ]] (PAS une
    # double négation : l'intérieur ["has", champ] n'est déjà pas un "!").
    f = {"name": "not", "args": [{"name": "notEqualTo", "args": [_prop("cls"), None]}]}
    doc = _doc([_rule("r1", [{"kind": "Fill", "color": "#ff0000"}], filter=f)])
    assert doc["layers"][0]["filter"] == ["!", ["has", "cls"]]


def test_filtre_not_devant_in_fonctionne():
    f = {"name": "not", "args": [{"name": "in", "args": [_prop("cls"), "A", "B"]}]}
    doc = _doc([_rule("r1", [{"kind": "Fill", "color": "#ff0000"}], filter=f)])
    assert doc["layers"][0]["filter"] == ["!", ["in", ["get", "cls"], ["literal", ["A", "B"]]]]


def test_filtre_double_negation_leve_exception():
    # Double négation (["!", ["!", ["has", ...]]]) : vérifié cassée aussi
    # contre l'oracle ("!!" non supporté) — le "!" externe se retrouve devant
    # un ["!", ...], pas un "has"/"in" direct, donc rejeté.
    f = {"name": "not", "args": [{"name": "not", "args": [{"name": "equalTo", "args": [_prop("cls"), None]}]}]}
    try:
        _doc([_rule("r1", [{"kind": "Fill", "color": "#ff0000"}], filter=f)])
        assert False, "devait lever ExpressionPivotNonEcrite"
    except ExpressionPivotNonEcrite:
        pass


def test_filtre_between_devient_and_de_deux_comparaisons():
    f = {"name": "between", "args": [_prop("x"), 10, 20]}
    doc = _doc([_rule("r1", [{"kind": "Fill", "color": "#ff0000"}], filter=f)])
    assert doc["layers"][0]["filter"] == ["all", [">=", ["get", "x"], 10], ["<=", ["get", "x"], 20]]


def test_filtre_in_devient_operateur_in_natif():
    f = {"name": "in", "args": [_prop("cls"), "A", "B", "C"]}
    doc = _doc([_rule("r1", [{"kind": "Fill", "color": "#ff0000"}], filter=f)])
    assert doc["layers"][0]["filter"] == ["in", ["get", "cls"], ["literal", ["A", "B", "C"]]]


def test_filtre_like_leve_exception():
    try:
        _doc([_rule("r1", [{"kind": "Fill", "color": "#ff0000"}], filter=["*=", _prop("cls"), "A*"])])
        assert False, "devait lever ExpressionPivotNonEcrite"
    except ExpressionPivotNonEcrite:
        pass


def test_filtre_dict_comparaison_simple():
    f = {"name": "greaterThan", "args": [_prop("pop"), 100]}
    doc = _doc([_rule("r1", [{"kind": "Fill", "color": "#ff0000"}], filter=f)])
    assert doc["layers"][0]["filter"] == [">", ["get", "pop"], 100]


# --------------------------------------------------------------------------- strMatches (LIKE/ILIKE) : 4 formes à un seul segment
def _strmatches(champ, regex):
    return {"name": "strMatches", "args": [_prop(champ), regex]}


def test_strmatches_prefixe_ilike_devient_slice_downcase():
    """Cas réel du corpus (ASSIETTE_SUP_S.qml) : idass ILIKE 'a1-%'."""
    f = _strmatches("idass", r"(?i)^a1\-.*$")
    doc = _doc([_rule("r1", [{"kind": "Fill", "color": "#ff0000"}], filter=f)])
    assert doc["layers"][0]["filter"] == ["==", ["slice", ["downcase", ["get", "idass"]], 0, 3], "a1-"]


def test_strmatches_suffixe_like_sensible_casse_pas_de_downcase():
    f = _strmatches("cls", r"^.*xyz$")
    doc = _doc([_rule("r1", [{"kind": "Fill", "color": "#ff0000"}], filter=f)])
    layer_filter = doc["layers"][0]["filter"]
    assert layer_filter == ["==", ["slice", ["get", "cls"], ["-", ["length", ["get", "cls"]], 3]], "xyz"]


def test_strmatches_contient_devient_in_sous_chaine():
    f = _strmatches("cls", r"(?i)^.*abc.*$")
    doc = _doc([_rule("r1", [{"kind": "Fill", "color": "#ff0000"}], filter=f)])
    assert doc["layers"][0]["filter"] == ["in", "abc", ["downcase", ["get", "cls"]]]


def test_strmatches_exact_sans_joker_devient_egalite():
    f = _strmatches("cls", r"^abc$")
    doc = _doc([_rule("r1", [{"kind": "Fill", "color": "#ff0000"}], filter=f)])
    assert doc["layers"][0]["filter"] == ["==", ["get", "cls"], "abc"]


def test_strmatches_plusieurs_segments_leve_exception():
    """'a%b' (joker au milieu, pas aux bornes) : hors du périmètre à un
    seul segment littéral — lève plutôt que d'approximer en chaînant des
    recherches non vérifiées."""
    try:
        _doc([_rule("r1", [{"kind": "Fill", "color": "#ff0000"}], filter=_strmatches("cls", r"^a.*b$"))])
        assert False, "devait lever ExpressionPivotNonEcrite"
    except ExpressionPivotNonEcrite as e:
        assert "segment littéral" in str(e)


def test_strmatches_joker_souligne_leve_exception():
    try:
        _doc([_rule("r1", [{"kind": "Fill", "color": "#ff0000"}], filter=_strmatches("cls", r"^a.$"))])
        assert False, "devait lever ExpressionPivotNonEcrite"
    except ExpressionPivotNonEcrite:
        pass


def test_strmatches_regex_non_canonique_leve_exception():
    try:
        _doc([_rule("r1", [{"kind": "Fill", "color": "#ff0000"}], filter=_strmatches("cls", r"[a-z]+"))])
        assert False, "devait lever ExpressionPivotNonEcrite"
    except ExpressionPivotNonEcrite as e:
        assert "forme canonique" in str(e)


# --------------------------------------------------------------------------- LineSymbolizer -> couche "line"
def test_line_paint_et_layout_complets():
    doc = _doc([_rule("r1", [{
        "kind": "Line", "color": "#0000ff", "width": 2, "opacity": 0.8,
        "dasharray": [4, 2], "cap": "round", "join": "bevel",
    }])])
    layer = doc["layers"][0]
    assert layer["type"] == "line"
    assert layer["paint"] == {
        "line-color": "#0000ff", "line-opacity": 0.8, "line-width": 2, "line-dasharray": [4, 2],
    }
    assert layer["layout"] == {"line-cap": "round", "line-join": "bevel"}


def test_line_sans_cap_join_omet_layout():
    doc = _doc([_rule("r1", [{"kind": "Line", "color": "#0000ff"}])])
    assert "layout" not in doc["layers"][0]


def test_line_dasharray_non_numerique_leve_exception():
    try:
        _doc([_rule("r1", [{"kind": "Line", "color": "#000000", "dasharray": ["a", "b"]}])])
        assert False, "devait lever ExpressionPivotNonEcrite"
    except ExpressionPivotNonEcrite:
        pass


def test_line_graphicstroke_sans_resolveur_leve_exception():
    try:
        _doc([_rule("r1", [{"kind": "Line", "graphicStroke": {"kind": "Mark"}}])])
        assert False, "devait lever ExpressionPivotNonEcrite"
    except ExpressionPivotNonEcrite as e:
        assert "resoudre_sprite" in str(e)


def test_line_graphicstroke_ecrit_line_pattern_via_resolveur():
    """Extension du 2026-10-12 : LineSymbolizer.graphicFill ET .graphicStroke
    s'écrivent tous deux en line-pattern (Mapbox n'a qu'UNE propriété de
    motif pour une couche "line", contrairement à SLD) — voir
    _resoudre_motif_sprite, confirmé contre l'oracle (RasterLine)."""
    for champ in ("graphicFill", "graphicStroke"):
        doc = json.loads(ecrire_mbstyle(
            _style([_rule("r1", [{
                "kind": "Line", "width": 2,
                champ: {"kind": "Mark", "wellKnownName": "shape://horline"},
            }])]),
            resoudre_sprite=lambda jeton: "motif_horline",
            **SRC,
        ))
        layer = doc["layers"][0]
        assert layer["paint"]["line-pattern"] == "motif_horline"
        assert layer["paint"]["line-width"] == 2


def test_line_perpendicularoffset_ecrit_line_offset_signe_inverse():
    """perpendicularOffset (pivot, convention SLD/QGIS "offset direct") ->
    line-offset Mapbox, avec INVERSION DE SIGNE — vérifié contre l'oracle QGIS
    par DEUX round-trips indépendants via le même moteur de lecture :
    SLD <se:PerpendicularOffset>5</se:PerpendicularOffset> charge en
    offset()==+5 (QgsVectorLayer.loadSldStyle()), alors qu'un style Mapbox
    {"line-offset": 5} charge en offset()==-5 (QgsMapBoxGlStyleConverter) —
    même grandeur, signe opposé selon le format source. Le pivot suit la
    convention SLD (perpendicularOffset=3.75 écrit tel quel côté SLD), donc
    line-offset doit être le pivot NÉGÉ."""
    doc = _doc([_rule("r1", [{"kind": "Line", "color": "#000000", "perpendicularOffset": 3.75}])])
    assert doc["layers"][0]["paint"]["line-offset"] == -3.75


def test_line_perpendicularoffset_zero_ecrit_zero():
    doc = _doc([_rule("r1", [{"kind": "Line", "color": "#000000", "perpendicularOffset": 0}])])
    assert doc["layers"][0]["paint"]["line-offset"] == 0


def test_line_sans_perpendicularoffset_omet_line_offset():
    doc = _doc([_rule("r1", [{"kind": "Line", "color": "#000000"}])])
    assert "line-offset" not in doc["layers"][0]["paint"]


def test_line_perpendicularoffset_non_numerique_leve_exception():
    try:
        _doc([_rule("r1", [{"kind": "Line", "color": "#000000", "perpendicularOffset": "3.75"}])])
        assert False, "devait lever ExpressionPivotNonEcrite"
    except ExpressionPivotNonEcrite as e:
        assert "perpendicularOffset" in str(e)


def test_line_graphicstroke_avec_spacing_ecrit_couche_symbol_placement_line():
    """MarkerLine/HashLine (graphicStroke + spacing du pivot) : Mapbox n'a
    AUCUNE notion d'espacement pour une couche "line" (line-pattern tuile en
    continu) — VÉRIFIÉ CONTRE L'ORACLE QGIS (QgsMapBoxGlStyleConverter) que la
    seule construction qui porte 'spacing' est une couche "symbol" avec
    symbol-placement:"line" + symbol-spacing, round-trip confirmé vers
    QgsMarkerLineSymbolLayer(interval==16, rotate==1) avec icon-rotation-
    alignment="map". Ce test confirme le type de couche ET les champs clés."""
    doc = json.loads(ecrire_mbstyle(
        _style([_rule("r1", [{
            "kind": "Line",
            "graphicStroke": {"kind": "Icon", "image": "svg/cnig/x.svg", "format": "image/svg+xml"},
            "spacing": 16,
        }])]),
        resoudre_sprite=lambda jeton: "motif_x",
        **SRC,
    ))
    layer = doc["layers"][0]
    assert layer["type"] == "symbol"
    assert layer["layout"]["symbol-placement"] == "line"
    assert layer["layout"]["symbol-spacing"] == 16
    assert layer["layout"]["icon-image"] == "motif_x"
    assert layer["layout"]["icon-rotation-alignment"] == "map"
    assert layer["layout"]["icon-allow-overlap"] is True
    assert layer["layout"]["icon-ignore-placement"] is True


def test_line_graphicstroke_sans_spacing_reste_couche_line():
    """Non-régression explicite : SANS 'spacing' renseigné (motif continu,
    ex. RasterLine), le symbolizer continue de passer par _ecrire_line_paint
    -> couche "line" + line-pattern, inchangé par l'ajout du cas symbol."""
    doc = json.loads(ecrire_mbstyle(
        _style([_rule("r1", [{
            "kind": "Line",
            "graphicStroke": {"kind": "Mark", "wellKnownName": "shape://horline"},
        }])]),
        resoudre_sprite=lambda jeton: "motif_x",
        **SRC,
    ))
    layer = doc["layers"][0]
    assert layer["type"] == "line"
    assert layer["paint"]["line-pattern"] == "motif_x"


def test_line_graphicstroke_spacing_non_numerique_leve_exception():
    try:
        json.loads(ecrire_mbstyle(
            _style([_rule("r1", [{
                "kind": "Line",
                "graphicStroke": {"kind": "Icon", "image": "svg/cnig/x.svg", "format": "image/svg+xml"},
                "spacing": "16",
            }])]),
            resoudre_sprite=lambda jeton: "motif_x",
            **SRC,
        ))
        assert False, "devait lever ExpressionPivotNonEcrite"
    except ExpressionPivotNonEcrite as e:
        assert "spacing" in str(e)


def test_line_spacing_sans_resolveur_leve_exception():
    try:
        json.loads(ecrire_mbstyle(
            _style([_rule("r1", [{
                "kind": "Line",
                "graphicStroke": {"kind": "Icon", "image": "svg/cnig/x.svg", "format": "image/svg+xml"},
                "spacing": 16,
            }])]),
            **SRC,
        ))
        assert False, "devait lever ExpressionPivotNonEcrite"
    except ExpressionPivotNonEcrite as e:
        assert "resoudre_sprite" in str(e)


# --------------------------------------------------------------------------- MarkSymbolizer(circle) -> couche "circle"
def test_mark_circle_paint_complet():
    doc = _doc([_rule("r1", [{
        "kind": "Mark", "wellKnownName": "circle", "color": "#00ff00", "fillOpacity": 0.9,
        "radius": 5, "strokeColor": "#000000", "strokeWidth": 1, "strokeOpacity": 0.5,
    }])])
    layer = doc["layers"][0]
    assert layer["type"] == "circle"
    assert layer["paint"] == {
        "circle-color": "#00ff00", "circle-opacity": 0.9, "circle-stroke-color": "#000000",
        "circle-stroke-width": 1, "circle-stroke-opacity": 0.5, "circle-radius": 5,
    }


def test_mark_wellknownname_absent_equivaut_a_circle():
    doc = _doc([_rule("r1", [{"kind": "Mark", "color": "#00ff00", "radius": 5}])])
    assert doc["layers"][0]["type"] == "circle"


def test_mark_forme_non_circle_approximee_en_circle_avec_avertissement():
    """Extension du 2026-10-12 : une forme Mark non circulaire n'est plus un
    échec dur — approximée en couche "circle", couleur/radius préservés,
    la forme réelle signalée PERDUE par un avertissement explicite."""
    avertissements: list[str] = []
    doc = json.loads(ecrire_mbstyle(
        _style([_rule("r1", [{"kind": "Mark", "wellKnownName": "star", "color": "#00ff00", "radius": 5}])]),
        avertissements=avertissements, **SRC,
    ))
    layer = doc["layers"][0]
    assert layer["type"] == "circle"
    assert layer["paint"]["circle-color"] == "#00ff00"
    assert layer["paint"]["circle-radius"] == 5
    assert any("star" in a and "APPROXIMÉ" in a for a in avertissements)


def test_mark_opacity_globale_avertit_sans_lever():
    avertissements: list[str] = []
    ecrire_mbstyle(
        _style([_rule("r1", [{"kind": "Mark", "color": "#00ff00", "radius": 5, "opacity": 0.5}])]),
        avertissements=avertissements, **SRC,
    )
    assert any("opacity" in a and "circle" in a for a in avertissements)


# --------------------------------------------------------------------------- TextSymbolizer -> couche "symbol"
def test_text_label_champ_nu_devient_text_field_get():
    doc = _doc([_rule("r1", [{"kind": "Text", "label": "{{nom}}"}])])
    layer = doc["layers"][0]
    assert layer["type"] == "symbol"
    assert layer["layout"]["text-field"] == ["get", "nom"]


def test_text_label_fproperty_equivalent_au_template():
    doc = _doc([_rule("r1", [{"kind": "Text", "label": _prop("nom")}])])
    assert doc["layers"][0]["layout"]["text-field"] == ["get", "nom"]


def test_text_label_litteral_leve_exception():
    try:
        _doc([_rule("r1", [{"kind": "Text", "label": "Nom fixe"}])])
        assert False, "devait lever ExpressionPivotNonEcrite"
    except ExpressionPivotNonEcrite:
        pass


def test_text_font_liste_complete_ecrite_pas_seulement_premiere():
    doc = _doc([_rule("r1", [{"kind": "Text", "label": "{{n}}", "font": ["Open Sans Bold", "Arial Unicode MS Bold"]}])])
    assert doc["layers"][0]["layout"]["text-font"] == ["Open Sans Bold", "Arial Unicode MS Bold"]


def test_text_size_et_rotate_dans_layout_pas_paint():
    doc = _doc([_rule("r1", [{"kind": "Text", "label": "{{n}}", "size": 14, "rotate": 45}])])
    layout = doc["layers"][0]["layout"]
    assert layout["text-size"] == 14
    assert layout["text-rotate"] == 45
    assert "paint" not in doc["layers"][0] or "text-size" not in doc["layers"][0]["paint"]


def test_text_color_et_halo_dans_paint():
    doc = _doc([_rule("r1", [{"kind": "Text", "label": "{{n}}", "color": "#ffffff", "haloColor": "#000000", "haloWidth": 2}])])
    paint = doc["layers"][0]["paint"]
    assert paint["text-color"] == "#ffffff"
    assert paint["text-halo-color"] == "#000000"
    assert paint["text-halo-width"] == 2


def test_text_halo_color_avec_haloopacity_devient_rgba():
    doc = _doc([_rule("r1", [{"kind": "Text", "label": "{{n}}", "haloColor": "#000000", "haloOpacity": 0.4}])])
    assert doc["layers"][0]["paint"]["text-halo-color"] == "rgba(0,0,0,0.4)"


def test_text_sans_label_leve_exception():
    try:
        _doc([_rule("r1", [{"kind": "Text"}])])
        assert False, "devait lever ExpressionPivotNonEcrite"
    except ExpressionPivotNonEcrite:
        pass


# --------------------------------------------------------------------------- exclusions structurelles (Icon, Raster)
def test_icon_leve_exception_avec_raison_sprite():
    try:
        _doc([_rule("r1", [{"kind": "Icon", "image": "http://x/icon.svg"}])])
        assert False, "devait lever ExpressionPivotNonEcrite"
    except ExpressionPivotNonEcrite as e:
        assert "sprite" in str(e)


def test_raster_leve_exception_avec_raison_source():
    try:
        _doc([_rule("r1", [{"kind": "Raster", "opacity": 0.5}])])
        assert False, "devait lever ExpressionPivotNonEcrite"
    except ExpressionPivotNonEcrite as e:
        assert "source" in str(e)


# --------------------------------------------------------------------------- portée : elseRule, multi-symbolizer, kind non écrit
def test_rule_elserule_leve_exception():
    try:
        _doc([_rule("r1", [{"kind": "Fill", "color": "#ff0000"}], elseRule=True)])
        assert False, "devait lever ExpressionPivotNonEcrite"
    except ExpressionPivotNonEcrite:
        pass


def test_rule_sans_symbolizer_leve_exception():
    try:
        _doc([_rule("r1", [])])
        assert False, "devait lever ExpressionPivotNonEcrite"
    except ExpressionPivotNonEcrite:
        pass


def test_rule_avec_deux_symbolizers_empile_deux_couches():
    """Extension du 2026-10-12 : une Rule à N>1 symbolizers n'est plus un
    échec dur — écrite en N couches Mapbox distinctes, même filtre/
    source-layer, id suffixé "-0"/"-1", avec un avertissement informatif
    (pas une erreur)."""
    avertissements: list[str] = []
    doc = json.loads(ecrire_mbstyle(
        _style([_rule(
            "r1",
            [{"kind": "Fill", "color": "#ff0000"}, {"kind": "Line", "color": "#000000", "width": 2}],
            filter=["==", {"name": "property", "args": ["cls"]}, "A"],
        )]),
        avertissements=avertissements, **SRC,
    ))
    assert len(doc["layers"]) == 2
    l0, l1 = doc["layers"]
    assert l0["id"] == "r1-0" and l0["type"] == "fill"
    assert l1["id"] == "r1-1" and l1["type"] == "line"
    assert l0["filter"] == l1["filter"] == ["==", ["get", "cls"], "A"]
    assert l0["source-layer"] == l1["source-layer"] == "couche"
    assert any("2 symbolizers" in a for a in avertissements)


def test_rule_un_seul_symbolizer_id_sans_suffixe():
    """Pas de suffixe -0 quand il n'y a qu'un seul symbolizer (pas de
    changement d'id pour le cas déjà existant, rétrocompatible)."""
    doc = _doc([_rule("r1", [{"kind": "Fill", "color": "#ff0000"}])])
    assert doc["layers"][0]["id"] == "r1"


def test_rule_sans_symbolizer_leve_exception():
    try:
        _doc([_rule("r1", [])])
        assert False, "devait lever ExpressionPivotNonEcrite"
    except ExpressionPivotNonEcrite as e:
        assert "sans symbolizer" in str(e)


# --------------------------------------------------------------------------- IconSymbolizer -> couche "symbol"
def test_icon_sans_resolveur_leve_exception():
    try:
        _doc([_rule("r1", [{"kind": "Icon", "image": "picto.svg"}])])
        assert False, "devait lever ExpressionPivotNonEcrite"
    except ExpressionPivotNonEcrite as e:
        assert "resoudre_sprite" in str(e)


def test_icon_resolveur_renvoie_none_leve_exception():
    try:
        json.loads(ecrire_mbstyle(
            _style([_rule("r1", [{"kind": "Icon", "image": "inconnu.svg"}])]),
            resoudre_sprite=lambda image: None, **SRC,
        ))
        assert False, "devait lever ExpressionPivotNonEcrite"
    except ExpressionPivotNonEcrite as e:
        assert "inconnu.svg" in str(e)


def test_icon_ecrit_couche_symbol_avec_icon_image():
    avertissements: list[str] = []
    doc = json.loads(ecrire_mbstyle(
        _style([_rule("r1", [{
            "kind": "Icon", "image": "picto.svg", "size": 32, "opacity": 0.5, "rotate": 45,
        }])]),
        resoudre_sprite=lambda image: f"sprite_{Path(image).stem}",
        taille_sprite_px=64.0,
        avertissements=avertissements, **SRC,
    ))
    layer = doc["layers"][0]
    assert layer["type"] == "symbol"
    assert layer["layout"]["icon-image"] == "sprite_picto"
    assert layer["layout"]["icon-size"] == 32 / 64.0
    assert layer["layout"]["icon-rotate"] == 45
    assert layer["paint"]["icon-opacity"] == 0.5


def test_icon_offset_non_ecrit_avec_avertissement():
    avertissements: list[str] = []
    doc = json.loads(ecrire_mbstyle(
        _style([_rule("r1", [{"kind": "Icon", "image": "picto.svg", "offset": [5, -3]}])]),
        resoudre_sprite=lambda image: "sprite_picto",
        avertissements=avertissements, **SRC,
    ))
    layer = doc["layers"][0]
    assert "icon-offset" not in layer.get("layout", {})
    assert any("offset" in a and "icon-offset" in a for a in avertissements)


def test_icon_color_ecrit_icon_color_avec_avertissement_non_oracle():
    """IconSymbolizer.color -> icon-color (paint) : VOIR sprites.py pour le
    mécanisme SDF correspondant. Ce point n'est PAS vérifié contre l'oracle
    QGIS habituel (QgsMapBoxGlStyleConverter n'implémente ni icon-color ni le
    drapeau 'sdf' — confirmé en lisant son code source C++, versions 3.28 à
    3.40), ce qui doit être dit EXPLICITEMENT dans l'avertissement produit,
    pas seulement dans un commentaire de code."""
    avertissements: list[str] = []
    doc = json.loads(ecrire_mbstyle(
        _style([_rule("r1", [{"kind": "Icon", "image": "picto.svg", "color": "#d7b09e"}])]),
        resoudre_sprite=lambda image: "sprite_picto",
        avertissements=avertissements, **SRC,
    ))
    layer = doc["layers"][0]
    assert layer["paint"]["icon-color"] == "#d7b09e"
    assert any("icon-color" in a and "oracle" in a.lower() for a in avertissements)


def test_icon_sans_color_omet_icon_color():
    doc = json.loads(ecrire_mbstyle(
        _style([_rule("r1", [{"kind": "Icon", "image": "picto.svg"}])]),
        resoudre_sprite=lambda image: "sprite_picto",
        **SRC,
    ))
    assert "icon-color" not in doc["layers"][0]["paint"]


def test_icon_color_non_hex_leve_exception():
    try:
        json.loads(ecrire_mbstyle(
            _style([_rule("r1", [{"kind": "Icon", "image": "picto.svg", "color": "rouge"}])]),
            resoudre_sprite=lambda image: "sprite_picto",
            **SRC,
        ))
        assert False, "devait lever ExpressionPivotNonEcrite"
    except ExpressionPivotNonEcrite:
        pass


def test_symbolizer_kind_inconnu_leve_exception_nommee():
    try:
        _doc([_rule("r1", [{"kind": "Bogus", "color": "#ff0000"}])])
        assert False, "devait lever ExpressionPivotNonEcrite"
    except ExpressionPivotNonEcrite as e:
        assert "Bogus" in str(e)


# --------------------------------------------------------------------------- pivot pydantic (model_dump) accepté au même titre que le dict brut
def test_accepte_une_instance_pydantic_du_style():
    from styleforge_core.pivot import Style, Rule, FillSymbolizer

    style = Style(name="MonStyle", rules=[
        Rule(name="r1", symbolizers=[FillSymbolizer(kind="Fill", color="#ff0000")]),
    ])
    doc = json.loads(ecrire_mbstyle(style, **SRC))
    assert doc["layers"][0]["paint"] == {"fill-color": "#ff0000"}


if __name__ == "__main__":
    import inspect

    fonctions_test = [obj for nom, obj in list(globals().items())
                       if nom.startswith("test_") and inspect.isfunction(obj)]
    echecs = 0
    for f in fonctions_test:
        try:
            f()
            print(f"OK   {f.__name__}")
        except Exception as e:
            echecs += 1
            print(f"FAIL {f.__name__}: {e}")
    print(f"\n{len(fonctions_test) - echecs}/{len(fonctions_test)} tests passent")
    if echecs:
        sys.exit(1)


# ------------------------------------------------------------------------- VÉRIFICATIONS ORACLE (manuelles, PARTIELLEMENT faites — voir ci-dessous)
#
# Les assertions ci-dessus sont structurelles (elles vérifient le JSON que ce
# module produit, PAS ce qu'un moteur de rendu Mapbox en ferait). État exact
# à la livraison de ce fichier :
#
#   VÉRIFIÉ contre QgsMapBoxGlStyleConverter (oracle PRINCIPAL) EN CHARGEANT
#   LE DOCUMENT PRODUIT PAR ecrire_mbstyle() LUI-MÊME (pas seulement des
#   styles construits à la main pendant l'exploration préalable) :
#     - Un Style pivot à deux Rule (la première avec color+opacity+
#       fillOpacity+outlineColor+outlineOpacity tous renseignés
#       simultanément, la seconde avec un simple color littéral) ->
#       convert() renvoie result==0, AUCUNE erreur ni avertissement, 2
#       QgsVectorTileBasicRendererStyle produits.
#     - Sur la première Rule : symbol.opacity()==0.8 (pivot opacity ->
#       fill-opacity), symbolLayer color alpha==128 (pivot fillOpacity=0.5
#       -> canal alpha de fill-color en rgba()), outline_color alpha==77
#       (pivot outlineOpacity=0.3 -> canal alpha de fill-outline-color) —
#       les trois mécanismes lus SIMULTANÉMENT et sans contamination
#       croisée. C'est cette vérification qui justifie directement
#       opacity->fill-opacity et fillOpacity/outlineOpacity->canal alpha
#       rgba() dans _ecrire_fill_paint, testée sur le document réel, pas
#       seulement déduite par symétrie.
#     - Sur la seconde Rule : un fill-color hex littéral seul (sans
#       opacité) reste un remplissage plein opaque, comme attendu.
#
#   VÉRIFIÉ contre geostyler-cli (oracle SECONDAIRE) — avec un DÉSACCORD
#   RÉEL DÉCOUVERT, documenté en détail dans la docstring de
#   styleforge_core.writers.mbstyle ("DÉSACCORD RÉEL ENTRE LES DEUX
#   ORACLES") : passer notre document produit dans
#   `geostyler-cli -s mapbox -t sld` ne lève aucune erreur/avertissement
#   inattendu, MAIS en inspectant directement le pivot que construit
#   geostyler-mapbox-parser (MapboxStyleParser.readStyle(), pas seulement la
#   sortie SLD), son lecteur mapbox->pivot DROPPE silencieusement le canal
#   alpha d'un fill-color/fill-outline-color en rgba() (color devient
#   "#ff0000" sans fillOpacity reconstruit, au lieu de préserver l'opacité
#   quelque part) — contrairement à QgsMapBoxGlStyleConverter qui la
#   conserve à l'affichage. Les deux oracles ne sont PAS d'accord sur ce
#   point ; ce module suit l'oracle PRINCIPAL (QGIS, choix explicite de
#   l'utilisateur), le comportement de geostyler semblant simplement lossy
#   sur ce point précis plutôt que représenter une convention concurrente
#   légitime. Signalé ici plutôt que passé sous silence — exactement le
#   type de signal que l'oracle secondaire devait permettre de détecter.
#
#   MISE À JOUR — CONNEXION À L'ORACLE PRINCIPAL RÉTABLIE, EXTENSION ENTIÈREMENT
#   VÉRIFIÉE (remplace la section "PAS ENCORE VÉRIFIÉ" précédente, écrite
#   pendant une panne prolongée du plugin QGIS) :
#
#     Un document combiné à 9 couches, produit PAR ecrire_mbstyle() lui-même,
#     a été chargé dans un vrai QgsMapBoxGlStyleConverter.convert() :
#       - Rule.filter : comparaisons, AND/OR ("all"/"any"), IN, BETWEEN tous
#         lus avec l'expression QGIS EXACTE attendue.
#       - LineSymbolizer : color/opacity/width/cap/join corrects ; de plus,
#         CONSTAT DE SPEC confirmé (pas un bug) : line-dasharray est
#         réinterprété par QGIS comme des multiples de line-width — voir la
#         docstring de _ecrire_line_paint, l'écrivain reste un passage
#         littéral, la mise à l'échelle est un comportement du RENDU.
#       - MarkSymbolizer(circle) : circle-color/opacity(dérivé de
#         fillOpacity)/stroke-*/radius tous corrects ; radius N'EST PAS
#         doublé dans le JSON Mapbox, mais QGIS le représente en interne
#         comme un marker "size" doublé — cohérent avec le ×2 déjà établi
#         côté SLD Size.
#       - TextSymbolizer : désormais testé, via l'API séparée
#         conv.labeling().styles()[0].labelSettings() (distincte de
#         conv.renderer() — une couche "symbol" avec texte produit un objet
#         QgsVectorTileBasicLabeling séparé). fieldName/isExpression, color,
#         size, font, haloColor, angleOffset tous corrects. CONSTAT DE SPEC
#         confirmé : text-halo-width est DOUBLÉ par le buffer QGIS à la
#         lecture (voir _ecrire_text_paint, même traitement que
#         dasharray/radius : littéral à l'écriture) ; text-rotate
#         correspond 1:1 à angleOffset (aucune inversion de signe,
#         contrairement à SLD). Le plantage de geostyler-mapbox-parser
#         6.2.0 sur text-field en forme expression (["get","nom"]),
#         documenté précédemment, est donc confirmé n'être qu'un problème de
#         CETTE version tierce : QGIS, l'oracle PRINCIPAL, accepte cette
#         forme sans réserve.
#       - outlineWidth/outlineDasharray (propriétés "fill" hors spec
#         Mapbox) : CONFIRMÉ inoffensif — ignoré silencieusement par
#         convert() (result==0, aucun avertissement).
#       - antialias : fill-antialias accepté sans erreur ni avertissement.
#
#     DEUX BUGS RÉELS DÉCOUVERTS PAR CETTE VÉRIFICATION, CORRIGÉS DANS LE
#     MODULE ET REFLÉTÉS DANS LES TESTS CI-DESSUS (une vindication concrète
#     de la discipline "toujours vérifier contre l'oracle PRINCIPAL avant de
#     livrer" — la corroboration de l'oracle secondaire seule s'est avérée
#     insuffisante ici) :
#       1. IS NULL/IS NOT NULL : ["==", ["get", champ], null] — pourtant
#          corroboré par geostyler-cli — produit un AVERTISSEMENT QGIS et un
#          filtre TRONQUÉ/INVALIDE. Corrigé : ["has", champ] / ["!", ["has",
#          champ]], vérifiés EXACTS (voir test_filtre_is_null_devient_
#          egalite_a_null / test_filtre_not_is_null).
#       2. Négation générale "!" : traduction 1:1 vers Mapbox "!" brisée
#          devant une comparaison directe et devant AND/OR — QGIS abandonne
#          alors le filtre ENTIER en silence (filterExpression vide, la Rule
#          matcherait TOUTES les features). "!" fiable UNIQUEMENT devant
#          ["has", ...] et ["in", ...] (double négation "!!" également
#          vérifiée cassée). Corrigé : _construire_filtre_mapbox lève
#          maintenant ExpressionPivotNonEcrite pour toute négation qui ne se
#          réduit pas à l'une de ces deux formes vérifiées (voir
#          test_filtre_not_sur_comparaison_leve_exception,
#          test_filtre_not_sur_and_or_leve_exception,
#          test_filtre_double_negation_leve_exception,
#          test_filtre_not_devant_has_fonctionne,
#          test_filtre_not_devant_in_fonctionne).
#
#     PAS ENCORE VÉRIFIÉ, à traiter dans une itération ultérieure si
#     demandé : le choix ["get", champ] vs l'ancienne forme token "{champ}"
#     pour text-field n'a pas été spécifiquement départagé contre l'oracle
#     au-delà de la confirmation que la forme expression fonctionne — seule
#     celle-ci a été testée puisque c'est celle que cet écrivain produit.
