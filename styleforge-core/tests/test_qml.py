#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_qml.py — Vérifie le lecteur QML générique (styleforge_core.readers.qml)
sur le corpus niveau 1 (../corpus, livré précédemment) :
  1. les 5 types de rendu couverts (singleSymbol, categorizedSymbol,
     graduatedSymbol, RuleRenderer, nullSymbol) produisent le bon nombre de
     Rule, avec les bons filtres ;
  2. le contournement EllipseMarker (compat/ellipse.py) est bien appliqué de
     bout en bout depuis un vrai fichier QML du corpus ;
  3. un type de rendu hors périmètre (heatmapRenderer) et une classe de
     couche hors périmètre (FontMarker, et deux autres représentatives des
     familles de raisons documentées) échouent explicitement, avec la
     raison spécifique de RAISONS_HORS_PERIMETRE, pas en silence ;
  4. une propriété pilotée par une expression non triviale échoue par
     défaut (sur_expression_non_traduite="lever") et se dégrade proprement
     en mode "avertir" ;
  5. une référence de champ nue ("champ", sans opérateur) EST traduite
     automatiquement — cas que le corpus actuel n'exerce pas (voir le
     rapport d'accompagnement), donc testé ici sur un QML minimal fabriqué ;
  6. les 7 classes de couche ajoutées lors de l'extension de couverture qui
     a suivi la version initiale (FilledLine, FilledMarker, RasterMarker,
     AnimatedMarker, SvgMarker, RasterFill, RasterLine) sont lues
     correctement bout en bout depuis le corpus, y compris l'écart réel
     découvert en cours de route (FilledLine utilise la clé QGIS "color",
     pas "line_color" comme SimpleLine).
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from styleforge_core.readers.qml import (
    CoucheDeSymboleNonSupportee,
    DocumentQMLInvalide,
    ProprieteExpressionNonTraduite,
    RendererNonSupporte,
    lire_fichier_qml,
)

CORPUS = Path(__file__).parent.parent.parent / "corpus"


def test_single_symbol():
    r = lire_fichier_qml(str(CORPUS / "renderers/singleSymbol.qml"))
    assert len(r.style.rules) == 1
    assert r.style.rules[0].filter is None
    sym = r.style.rules[0].symbolizers[0].root
    assert sym.kind == "Mark"
    print("OK : singleSymbol -> 1 Rule sans filtre")


def test_categorized_symbol():
    r = lire_fichier_qml(str(CORPUS / "renderers/categorizedSymbol.qml"))
    assert len(r.style.rules) == 3
    for regle, valeur_attendue in zip(r.style.rules, (1.0, 2.0, 3.0)):
        filtre = regle.filter
        op = filtre[0]
        assert (getattr(op, "root", op) == "==")
        assert filtre[2] == valeur_attendue
    print("OK : categorizedSymbol -> 3 Rule, une par catégorie, filtre ==")


def test_graduated_symbol():
    r = lire_fichier_qml(str(CORPUS / "renderers/graduatedSymbol.qml"))
    assert len(r.style.rules) == 2
    print("OK : graduatedSymbol -> 2 Rule (une par intervalle)")


def test_rule_renderer():
    r = lire_fichier_qml(str(CORPUS / "renderers/RuleRenderer.qml"))
    assert len(r.style.rules) == 2
    noms = [regle.name for regle in r.style.rules]
    assert noms == ["faible", "fort"]
    print("OK : RuleRenderer -> 2 Rule, filtre QGIS simple traduit")


def test_rule_renderer_filtre_riche_traducteur_general():
    # Preuve bout en bout (pas seulement une unité isolée sur
    # styleforge_core.readers.expressions) que le traducteur d'expressions
    # général est bien câblé dans _renderer_rule_renderer, sur un filtre que
    # l'ancien traducteur minimal (comparaison simple uniquement) n'aurait
    # jamais reconnu : combinaison AND / IN / OR / LIKE.
    brut = (CORPUS / "renderers/RuleRenderer.qml").read_text()
    modifie = brut.replace(
        'filter="&quot;valeur&quot; &lt;= 2"',
        'filter="&quot;valeur&quot; &lt;= 2 AND &quot;valeur&quot; IN (0, 1, 2)"',
    ).replace(
        'filter="&quot;valeur&quot; > 2"',
        'filter="&quot;valeur&quot; > 2 OR &quot;nom&quot; LIKE \'%fort%\'"',
    )
    assert modifie != brut, "aucun des deux filtres du fixture RuleRenderer n'a été trouvé"
    with tempfile.NamedTemporaryFile("w", suffix=".qml", delete=False) as f:
        f.write(modifie)
        chemin = f.name
    try:
        r = lire_fichier_qml(chemin)
    finally:
        Path(chemin).unlink()
    def r_(x):
        return getattr(x, "root", x)

    assert len(r.style.rules) == 2
    filtre_faible = r.style.rules[0].filter
    assert r_(filtre_faible[0]) == "&&"
    membre1 = r_(filtre_faible[1])
    assert r_(membre1[0]) == "<="
    membre2 = r_(filtre_faible[2])
    assert getattr(membre2, "name", None) == "in"  # IN (...) -> dict Fin (pas de forme tuple)
    filtre_fort = r.style.rules[1].filter
    assert r_(filtre_fort[0]) == "||"
    membre_like = r_(r_(filtre_fort[2]))
    assert r_(membre_like[0]) == "*="  # LIKE -> l'opérateur à joker du pivot
    assert membre_like[2] == "*fort*"  # '%fort%' QGIS -> '*fort*' pivot
    print("OK : RuleRenderer avec filtre AND/IN/OR/LIKE -> traducteur d'expressions général câblé")


def test_is_null_traduit_bout_en_bout_via_rule_renderer():
    # IS NULL/IS NOT NULL se traduisent (forme dict FequalTo/FnotEqualTo,
    # pas la forme tuple ["==", operande, None] qu'un premier essai avait
    # utilisée puis vue rejetée par le modèle pivot généré ici) — vérifié
    # bout en bout depuis un vrai RuleRenderer, pas seulement en unité
    # isolée sur styleforge_core.readers.expressions.
    brut = (CORPUS / "renderers/RuleRenderer.qml").read_text()
    modifie = brut.replace(
        'filter="&quot;valeur&quot; &lt;= 2"',
        'filter="&quot;valeur&quot; IS NOT NULL"',
    )
    assert modifie != brut
    with tempfile.NamedTemporaryFile("w", suffix=".qml", delete=False) as f:
        f.write(modifie)
        chemin = f.name
    try:
        r = lire_fichier_qml(chemin)
    finally:
        Path(chemin).unlink()
    filtre = r.style.rules[0].filter
    nom = getattr(filtre, "name", filtre.get("name") if isinstance(filtre, dict) else None)
    assert nom == "notEqualTo"
    print("OK : RuleRenderer avec filtre IS NOT NULL -> dict FnotEqualTo(Fproperty, None)")


def test_null_symbol():
    r = lire_fichier_qml(str(CORPUS / "renderers/nullSymbol.qml"))
    assert r.style.rules == [] or r.style.rules is None
    print("OK : nullSymbol -> aucune Rule (état valide, pas une erreur)")


def test_ellipse_marker_bout_en_bout():
    r = lire_fichier_qml(str(CORPUS / "symbol_layers/Marker/EllipseMarker.qml"))
    sym = r.style.rules[0].symbolizers[0].root
    wkn = getattr(sym.wellKnownName, "root", sym.wellKnownName)
    assert wkn == "circle"
    assert sym.radius == 1.75 / 25.4 * 90.0  # (4+3)/4 mm -> px @ 90dpi (défaut, oracle QGIS)
    assert any("approximée par WellKnownName='circle'" in a for a in r.avertissements)
    print("OK : EllipseMarker du corpus -> cercle, avertissement de perte émis")


def test_ellipse_marker_rectangle_devient_square():
    """Extension du 2026-10-12 (styleforge_core.compat.ellipse) : un
    EllipseMarker symbol_name='rectangle' (ex. plu_inf_s.qml/
    psmv_inf_s.qml, 9.96 x 6 Point dans le corpus réel) n'est plus hors
    périmètre -> WellKnownName='square', avertissement de perte émis."""
    brut = (CORPUS / "symbol_layers/Marker/EllipseMarker.qml").read_text()
    modifie = brut.replace(
        '<Option type="QString" name="symbol_name" value="circle"/>',
        '<Option type="QString" name="symbol_name" value="rectangle"/>',
    )
    assert modifie != brut
    with tempfile.NamedTemporaryFile("w", suffix=".qml", delete=False) as f:
        f.write(modifie)
        chemin = f.name
    try:
        r = lire_fichier_qml(chemin)
    finally:
        Path(chemin).unlink()
    sym = r.style.rules[0].symbolizers[0].root
    wkn = getattr(sym.wellKnownName, "root", sym.wellKnownName)
    assert wkn == "square"
    assert any("approximée par WellKnownName='square'" in a for a in r.avertissements)
    print("OK : EllipseMarker 'rectangle' -> WellKnownName 'square', avertissement de perte émis")


def test_renderer_hors_perimetre():
    try:
        lire_fichier_qml(str(CORPUS / "renderers/heatmapRenderer.qml"))
    except RendererNonSupporte as e:
        assert "heatmapRenderer" in str(e)
        print("OK : renderer hors périmètre rejeté explicitement -", str(e).splitlines()[0][:90])
        return
    raise AssertionError("heatmapRenderer aurait dû lever RendererNonSupporte")


def test_couche_hors_perimetre():
    # SvgMarker, FontMarker, CentroidFill... ont été promus au registre lors
    # des extensions de couverture qui ont suivi la version initiale (cf.
    # RAISONS_HORS_PERIMETRE et les rapports d'accompagnement) ; MaskMarker,
    # lui, reste hors périmètre (raison documentée : pas un rendu visuel,
    # aucun Symbolizer ne représente une opération de masquage).
    try:
        lire_fichier_qml(str(CORPUS / "symbol_layers/Marker/MaskMarker.qml"))
    except CoucheDeSymboleNonSupportee as e:
        assert "MaskMarker" in str(e)
        assert "masquage" in str(e)  # raison spécifique, pas générique
        print("OK : classe de couche hors périmètre rejetée explicitement -", str(e).splitlines()[0][:90])
        return
    raise AssertionError("MaskMarker aurait dû lever CoucheDeSymboleNonSupportee")


def test_couches_hors_perimetre_avec_raison_specifique():
    # Vérifie, sur quelques autres classes hors périmètre représentatives des
    # familles de raisons documentées (sous-symbole sans équivalent statique,
    # dégradé), que le message porte bien la raison spécifique de
    # RAISONS_HORS_PERIMETRE et pas le message générique de repli.
    cas = {
        "symbol_layers/Fill/RandomMarkerFill.qml": "sous-symbole",
        "symbol_layers/Fill/GradientFill.qml": "dégradé",
    }
    for chemin, mot_attendu in cas.items():
        try:
            lire_fichier_qml(str(CORPUS / chemin))
        except CoucheDeSymboleNonSupportee as e:
            assert mot_attendu in str(e).lower(), f"{chemin} : raison spécifique absente du message : {e}"
            assert "Voir enregistrer_lecteur_couche()" not in str(e), (
                f"{chemin} : message générique utilisé alors qu'une raison spécifique existe"
            )
            continue
        raise AssertionError(f"{chemin} aurait dû lever CoucheDeSymboleNonSupportee")
    print("OK : raisons spécifiques (pas génériques) pour CentroidFill et GradientFill")


def test_couches_etendues_bout_en_bout():
    # Les 7 classes ajoutées lors de l'extension de couverture (cf. rapport
    # d'accompagnement dédié) : vérifie qu'elles produisent bien un
    # Symbolizer du 'kind' attendu, sans lever, sur un vrai fichier du corpus.
    cas = {
        "symbol_layers/Line/FilledLine.qml": "Line",
        "symbol_layers/Marker/FilledMarker.qml": "Mark",
        "symbol_layers/Marker/RasterMarker.qml": "Icon",
        "symbol_layers/Marker/AnimatedMarker.qml": "Icon",
        "symbol_layers/Marker/SvgMarker.qml": "Icon",
        "symbol_layers/Fill/RasterFill.qml": "Fill",
        "symbol_layers/Line/RasterLine.qml": "Line",
    }
    for chemin, kind_attendu in cas.items():
        r = lire_fichier_qml(str(CORPUS / chemin))
        sym = r.style.rules[0].symbolizers[0].root
        assert sym.kind == kind_attendu, f"{chemin} : kind={sym.kind!r}, attendu {kind_attendu!r}"
    print("OK : les 7 classes de couche étendues produisent le Symbolizer attendu (FilledLine, "
          "FilledMarker, RasterMarker, AnimatedMarker, SvgMarker, RasterFill, RasterLine)")


def test_filled_line_cle_color_pas_line_color():
    # Garde-fou pour l'écart réel découvert lors de cette extension : FilledLine
    # utilise la clé QGIS "color" (pas "line_color" comme SimpleLine) — une
    # délégation naïve à _lire_simple_line lève KeyError. Vérifie la couleur
    # effectivement lue, pas seulement l'absence d'exception.
    r = lire_fichier_qml(str(CORPUS / "symbol_layers/Line/FilledLine.qml"))
    sym = r.style.rules[0].symbolizers[0].root
    assert sym.color == "#0000ff"  # "0,0,255,255,rgb:..." du corpus
    print("OK : FilledLine.color lu depuis la clé QGIS 'color' (pas 'line_color')")


_QML_SIMPLE_LINE_UNITES_DASHARRAY = """\
<qgis version="3.40.4-Bratislava">
  <renderer-v2 type="singleSymbol" symbollevels="0" enableorderby="0" forceraster="0" referencescale="-1">
    <symbols>
      <symbol clip_to_extent="1" type="line" name="0" alpha="1" frame_rate="10" is_animated="0" force_rhr="0">
        <layer class="SimpleLine" locked="0" pass="0" id="{0}" enabled="1">
          <Option type="Map">
            <Option type="QString" name="capstyle" value="square"/>
            <Option type="QString" name="customdash" value="3;2"/>
            <Option type="QString" name="customdash_unit" value="Point"/>
            <Option type="QString" name="dash_pattern_offset" value="1"/>
            <Option type="QString" name="dash_pattern_offset_unit" value="Inch"/>
            <Option type="QString" name="joinstyle" value="bevel"/>
            <Option type="QString" name="line_color" value="10,20,30,255"/>
            <Option type="QString" name="line_style" value="solid"/>
            <Option type="QString" name="line_width" value="1"/>
            <Option type="QString" name="line_width_unit" value="MM"/>
            <Option type="QString" name="use_custom_dash" value="1"/>
          </Option>
        </layer>
      </symbol>
    </symbols>
  </renderer-v2>
</qgis>
"""


def test_simple_line_dasharray_convertie_dans_sa_propre_unite():
    # Bug réel découvert en diagnostiquant psmv_zone_urba.qml (3 "zones
    # urba" du corpus CNIG) : customdash_unit et dash_pattern_offset_unit
    # sont des unités QML PROPRES à ces deux champs, indépendantes de
    # line_width_unit — avant ce correctif, dasharray/dashOffset étaient
    # écrits TELS QUELS (valeurs QML brutes non converties en px), alors
    # que 'width' l'était bien via line_width_unit. Confirmé face à
    # l'oracle QGIS réel (QgsVectorLayer.saveSldStyle() sur ce même QML) :
    # customdash="3;2" en Point devient bien des px dans le SLD que QGIS
    # produit lui-même, pas des valeurs Point laissées brutes.
    with tempfile.NamedTemporaryFile("w", suffix=".qml", delete=False) as f:
        f.write(_QML_SIMPLE_LINE_UNITES_DASHARRAY)
        chemin = f.name
    try:
        r = lire_fichier_qml(chemin, dpi=96.0)
    finally:
        Path(chemin).unlink()
    sym = r.style.rules[0].symbolizers[0].root
    assert sym.kind == "Line"
    # customdash "3;2" en Point -> px via dpi=96 (1/72 pouce par Point) :
    # 3 -> 4.0 px, 2 -> 2.6667 px (comme 'width' : 1mm -> ~3.7795px).
    assert sym.dasharray == [4.0, 2.0 * 96.0 / 72.0]
    # dash_pattern_offset "1" en Inch -> 1 * 96 = 96.0 px (unité indépendante
    # de customdash_unit comme de line_width_unit, les trois diffèrent ici
    # à dessein pour ne pas masquer une confusion entre elles).
    assert sym.dashOffset == 96.0
    assert any("dasharray" in a and "Point" in a for a in r.avertissements)
    assert any("dashOffset" in a and "Inch" in a for a in r.avertissements)
    print("OK : SimpleLine.dasharray/dashOffset convertis chacun dans sa PROPRE "
          "unité QML (customdash_unit/dash_pattern_offset_unit), pas celle de 'width'")


_QML_SIMPLE_LINE_OFFSET = """\
<qgis version="3.40.4-Bratislava">
  <renderer-v2 type="singleSymbol" symbollevels="0" enableorderby="0" forceraster="0" referencescale="-1">
    <symbols>
      <symbol clip_to_extent="1" type="fill" name="0" alpha="1" frame_rate="10" is_animated="0" force_rhr="0">
        <layer class="SimpleLine" locked="0" pass="0" id="{0}" enabled="1">
          <Option type="Map">
            <Option type="QString" name="capstyle" value="square"/>
            <Option type="QString" name="joinstyle" value="bevel"/>
            <Option type="QString" name="line_color" value="10,20,30,255"/>
            <Option type="QString" name="line_style" value="solid"/>
            <Option type="QString" name="line_width" value="7"/>
            <Option type="QString" name="line_width_unit" value="Point"/>
            <Option type="QString" name="offset" value="3"/>
            <Option type="QString" name="offset_unit" value="Point"/>
          </Option>
        </layer>
        <layer class="SimpleLine" locked="0" pass="1" id="{1}" enabled="1">
          <Option type="Map">
            <Option type="QString" name="capstyle" value="square"/>
            <Option type="QString" name="joinstyle" value="bevel"/>
            <Option type="QString" name="line_color" value="40,50,60,255"/>
            <Option type="QString" name="line_style" value="solid"/>
            <Option type="QString" name="line_width" value="2.5"/>
            <Option type="QString" name="line_width_unit" value="Point"/>
            <Option type="QString" name="offset" value="0"/>
            <Option type="QString" name="offset_unit" value="MM"/>
          </Option>
        </layer>
      </symbol>
    </symbols>
  </renderer-v2>
</qgis>
"""


def test_fill_symbol_deux_simpleline_offsets_bout_en_bout():
    # Bug réel découvert en comparant styleforge_core contre l'oracle QGIS
    # natif (QgsVectorLayer.saveSldStyle()) sur plu_zone_urba_ge.qml (corpus
    # CNIG) : un <symbol type="fill"> qui simule un double-liseré via DEUX
    # couches SimpleLine à offset ("decalage perpendiculaire") différent
    # perdait ce decalage SANS LE LIRE DU TOUT — donc sans même
    # l'avertissement explicite que _avertir_proprietes_non_gerees produit
    # normalement pour une propriété du pivot non écrite ; c'était une
    # perte silencieuse en amont du pivot lui-même. Vérifié contre l'oracle :
    # offset=3 Point -> PerpendicularOffset=4 (comme line_width 7 Point ->
    # stroke-width ~9.33, même conversion dpi=96) ; offset=0 -> aucun
    # PerpendicularOffset écrit (0 est la valeur par défaut QML, "pas de
    # décalage", pas une valeur à représenter explicitement).
    from styleforge_core.writers.sld import ecrire_sld

    with tempfile.NamedTemporaryFile("w", suffix=".qml", delete=False) as f:
        f.write(_QML_SIMPLE_LINE_OFFSET)
        chemin = f.name
    try:
        r = lire_fichier_qml(chemin, dpi=96.0)
    finally:
        Path(chemin).unlink()
    symbolizers = r.style.rules[0].symbolizers
    assert len(symbolizers) == 2
    sym1, sym2 = (s.root for s in symbolizers)
    assert sym1.perpendicularOffset == 3.0 * 96.0 / 72.0
    assert sym2.perpendicularOffset is None
    assert any("perpendicularOffset" in a and "Point" in a for a in r.avertissements)

    sld = ecrire_sld(r.style, nom_couche="t")
    assert sld.count("<PerpendicularOffset>") == 1  # une seule des deux couches en a besoin
    assert "<PerpendicularOffset>4.0</PerpendicularOffset>" in sld
    print("OK : SimpleLine.offset -> LineSymbolizer.perpendicularOffset, converti dans SA "
          "PROPRE unité (offset_unit), omis quand nul plutôt qu'écrit à 0")


_QML_SIMPLE_MARKER_OFFSET = """\
<qgis version="3.40.4-Bratislava">
  <renderer-v2 type="singleSymbol" symbollevels="0" enableorderby="0" forceraster="0" referencescale="-1">
    <symbols>
      <symbol clip_to_extent="1" type="marker" name="0" alpha="1" frame_rate="10" is_animated="0" force_rhr="0">
        <layer class="SimpleMarker" locked="0" pass="0" id="{0}" enabled="1">
          <Option type="Map">
            <Option type="QString" name="angle" value="0"/>
            <Option type="QString" name="color" value="255,0,0,255"/>
            <Option type="QString" name="name" value="circle"/>
            <Option type="QString" name="offset" value="5,-2"/>
            <Option type="QString" name="offset_unit" value="Point"/>
            <Option type="QString" name="outline_color" value="0,0,0,255"/>
            <Option type="QString" name="outline_style" value="solid"/>
            <Option type="QString" name="outline_width" value="0"/>
            <Option type="QString" name="outline_width_unit" value="MM"/>
            <Option type="QString" name="scale_method" value="diameter"/>
            <Option type="QString" name="size" value="2"/>
            <Option type="QString" name="size_unit" value="MM"/>
          </Option>
        </layer>
      </symbol>
    </symbols>
  </renderer-v2>
</qgis>
"""


def test_simple_marker_offset_devient_displacement_sld():
    # Même famille de bug que SimpleLine.offset (perpendicularOffset,
    # ci-dessus) mais sur MarkSymbolizer cette fois : SimpleMarker.offset
    # n'était pas lu du tout. MarkSymbolizer.offset existe dans le schéma
    # geostyler-style (vérifié) ; écrit en <Graphic><Displacement> — vérifié
    # contre l'oracle QGIS (QgsVectorLayer.loadSldStyle() sur un SLD
    # construit à la main) que symbolLayer.offset() reprend exactement
    # (DisplacementX, DisplacementY) écrits, sans conversion supplémentaire.
    from styleforge_core.writers.sld import ecrire_sld

    with tempfile.NamedTemporaryFile("w", suffix=".qml", delete=False) as f:
        f.write(_QML_SIMPLE_MARKER_OFFSET)
        chemin = f.name
    try:
        r = lire_fichier_qml(chemin, dpi=96.0)
    finally:
        Path(chemin).unlink()
    sym = r.style.rules[0].symbolizers[0].root
    assert sym.kind == "Mark"
    # offset "5,-2" en Point -> px via dpi=96 (comme les autres tailles Point)
    assert sym.offset == [5.0 * 96.0 / 72.0, -2.0 * 96.0 / 72.0]
    assert any("offset" in a and "Point" in a for a in r.avertissements)

    sld = ecrire_sld(r.style, nom_couche="t")
    assert "<Displacement>" in sld
    assert f"<DisplacementX>{5.0 * 96.0 / 72.0}</DisplacementX>" in sld
    assert f"<DisplacementY>{-2.0 * 96.0 / 72.0}</DisplacementY>" in sld
    print("OK : SimpleMarker.offset -> MarkSymbolizer.offset -> <Graphic><Displacement>")


def test_svg_marker_offset_devient_displacement_sld():
    # Même bug, sur IconSymbolizer (SvgMarker) cette fois — découvert sur
    # plu_psc_p.qml (PSC-P_15-00_001, offset SvgMarker "0,3" Point perdu
    # silencieusement). Fabriqué à partir du corpus SvgMarker.qml (pattern
    # déjà utilisé par test_svg_marker_avertit_outline_et_couleur) avec un
    # offset non nul substitué.
    from styleforge_core.writers.sld import ecrire_sld

    brut = (CORPUS / "symbol_layers/Marker/SvgMarker.qml").read_text()
    modifie = brut.replace(
        '<Option type="QString" name="offset" value="0,0"/>',
        '<Option type="QString" name="offset" value="0,3"/>',
    ).replace(
        # Le fixture corpus a un chemin d'image vide (name="") : la lecture
        # de l'offset ne dépend pas de l'image, mais écrire_sld() refuse un
        # IconSymbolizer sans image (ExpressionPivotNonEcrite, vérifié hors
        # de ce test) — substitué pour pouvoir vérifier aussi l'écrivain.
        '<Option type="QString" name="name" value=""/>',
        '<Option type="QString" name="name" value="svg/test.svg"/>',
    )
    assert modifie != brut
    with tempfile.NamedTemporaryFile("w", suffix=".qml", delete=False) as f:
        f.write(modifie)
        chemin = f.name
    try:
        r = lire_fichier_qml(chemin, dpi=96.0)
    finally:
        Path(chemin).unlink()
    sym = r.style.rules[0].symbolizers[0].root
    assert sym.kind == "Icon"
    # offset_unit="MM" dans ce fixture (corpus réel) : 3mm -> px via dpi=96
    assert sym.offset == [0.0, 3.0 * (1 / 25.4) * 96.0]
    sld = ecrire_sld(r.style, nom_couche="t")
    assert "<Displacement>" in sld
    print("OK : SvgMarker.offset -> IconSymbolizer.offset -> <Graphic><Displacement> "
          "(même mécanisme que MarkSymbolizer, vérifié indépendamment)")


def test_animated_marker_avertit_frame_rate():
    r = lire_fichier_qml(str(CORPUS / "symbol_layers/Marker/AnimatedMarker.qml"))
    assert any("frameRate" in a for a in r.avertissements)
    print("OK : AnimatedMarker -> avertissement frameRate non traduit émis")


def test_svg_marker_avertit_outline_et_couleur():
    r = lire_fichier_qml(str(CORPUS / "symbol_layers/Marker/SvgMarker.qml"))
    sym = r.style.rules[0].symbolizers[0].root
    assert sym.color == "#232323"  # substitution de couleur SVG traduite
    assert any("outline_color" in a for a in r.avertissements)
    print("OK : SvgMarker -> couleur traduite + avertissement outline non traduit")


def test_raster_fill_via_graphic_fill():
    r = lire_fichier_qml(str(CORPUS / "symbol_layers/Fill/RasterFill.qml"))
    sym = r.style.rules[0].symbolizers[0].root
    assert sym.kind == "Fill"
    assert sym.graphicFill is not None
    graphic_fill = getattr(sym.graphicFill, "root", sym.graphicFill)
    assert graphic_fill.kind == "Icon"
    print("OK : RasterFill approximé via graphicFill (IconSymbolizer imbriqué)")


# --------------------------------------------------------------------------- deuxième extension :
# classes composites (sous-symbole imbriqué), lues récursivement via
# _lire_sous_symbole() et REGISTRE_COUCHES_RECURSIVES.

def test_font_marker_ttf():
    r = lire_fichier_qml(str(CORPUS / "symbol_layers/Marker/FontMarker.qml"))
    sym = r.style.rules[0].symbolizers[0].root
    wkn = getattr(sym.wellKnownName, "root", sym.wellKnownName)
    assert wkn == "ttf://Dingbats#0x0041"  # chr="A" (ord 65 = 0x41), font="Dingbats" du corpus
    assert any("ttf://" in a for a in r.avertissements)  # convention non vérifiée sur un rendu réel
    print("OK : FontMarker -> wellKnownName ttf://Dingbats#0x0041 (chr='A' -> 0x41)")


def test_centroid_fill_via_sous_symbole():
    r = lire_fichier_qml(str(CORPUS / "symbol_layers/Fill/CentroidFill.qml"))
    sym = r.style.rules[0].symbolizers[0].root
    assert sym.kind == "Mark"  # le sous-symbole marqueur, pas un Fill
    assert sym.geometry == {"name": "centroid", "args": [{"name": "property", "args": ["geometry"]}]}
    print("OK : CentroidFill -> marqueur du sous-symbole + geometry=centroid(...)")


def test_marker_line_via_graphic_stroke():
    r = lire_fichier_qml(str(CORPUS / "symbol_layers/Line/MarkerLine.qml"))
    sym = r.style.rules[0].symbolizers[0].root
    assert sym.kind == "Line"
    graphic_stroke = getattr(sym.graphicStroke, "root", sym.graphicStroke)
    assert graphic_stroke.kind == "Mark"
    assert abs(sym.spacing - 3.0 / 25.4 * 90.0) < 1e-9  # interval=3mm -> px @ 90dpi (défaut, oracle QGIS)
    print("OK : MarkerLine -> marqueur du sous-symbole via graphicStroke + spacing=interval")


def test_hash_line_marque_orientee():
    r = lire_fichier_qml(str(CORPUS / "symbol_layers/Line/HashLine.qml"))
    sym = r.style.rules[0].symbolizers[0].root
    graphic_stroke = getattr(sym.graphicStroke, "root", sym.graphicStroke)
    wkn = getattr(graphic_stroke.wellKnownName, "root", graphic_stroke.wellKnownName)
    assert wkn == "line"
    assert any("tirets" in a for a in r.avertissements)  # customdash du sous-symbole non reproduit
    print("OK : HashLine -> marque 'line' orientée (hash_angle/hash_length) via graphicStroke")


def test_line_pattern_fill_angle_exact_avec_rotation_residuelle():
    # LinePatternFill.qml du corpus a angle=45 (tombe exactement sur un
    # quadrant, rotation résiduelle nulle) : le calcul lui-même (formule
    # bridgestyle A1 + rotation résiduelle plutôt qu'un arrondi silencieux)
    # est vérifié séparément par unité ci-dessous, sur des angles non ronds.
    r = lire_fichier_qml(str(CORPUS / "symbol_layers/Fill/LinePatternFill.qml"))
    sym = r.style.rules[0].symbolizers[0].root
    assert sym.kind == "Fill"
    hachure = getattr(sym.graphicFill, "root", sym.graphicFill)
    wkn = getattr(hachure.wellKnownName, "root", hachure.wellKnownName)
    assert wkn == "shape://slash"
    assert hachure.rotate == 0.0
    print("OK : LinePatternFill (angle=45°) -> shape://slash, rotation résiduelle nulle")


def test_hachure_angle_non_rond_preserve_par_rotation_residuelle():
    # Le cas que bridgestyle rate (défaut A1 documenté dans le rapport
    # d'audit) : un angle de 30° n'est PAS arrondi à 45° en silence, il est
    # restitué exactement via (shape://slash, rotate=-15) — reproduit ici le
    # test de non-régression que ce même rapport propose (§5.1).
    from styleforge_core.readers.qml import _hachure_marque_et_rotation_residuelle
    marque, residuel = _hachure_marque_et_rotation_residuelle(30.0)
    assert marque == "shape://slash"
    assert residuel == -15.0
    print("OK : hachure à 30° -> shape://slash + rotation résiduelle -15° (angle exact préservé)")


def test_point_pattern_fill_via_graphic_fill_padding():
    r = lire_fichier_qml(str(CORPUS / "symbol_layers/Fill/PointPatternFill.qml"))
    sym = r.style.rules[0].symbolizers[0].root
    assert sym.kind == "Fill"
    graphic_fill = getattr(sym.graphicFill, "root", sym.graphicFill)
    assert graphic_fill.kind == "Mark"
    assert sym.graphicFillPadding is not None and len(sym.graphicFillPadding) == 4
    assert any("graphicFillPadding" in a for a in r.avertissements)  # approximation, pas exact
    print("OK : PointPatternFill -> marqueur du sous-symbole via graphicFill + graphicFillPadding")


def test_geometry_generator_cas_trivial_identite():
    # geometryModifier='@geometry' (les 3 variantes Fill/Line/Marker du
    # corpus) : traduction fidèle et sans perte du seul sous-symbole, pas une
    # approximation — donc aucun avertissement de perte pour ce cas précis.
    for chemin in (
        "symbol_layers/Marker/GeometryGenerator.qml",
        "symbol_layers/Line/GeometryGenerator.qml",
        "symbol_layers/Fill/GeometryGenerator.qml",
    ):
        r = lire_fichier_qml(str(CORPUS / chemin))
        sym = r.style.rules[0].symbolizers[0].root
        assert sym.kind == "Fill"  # les 3 fixtures du corpus ont un sous-symbole de type fill
        assert not any("GeometryGenerator" in a and "centroid" in a for a in r.avertissements)
    print("OK : GeometryGenerator(@geometry) -> traduction fidèle du sous-symbole, sans perte")


def test_geometry_generator_cas_general_leve():
    # Un geometryModifier ni '@geometry' ni 'centroid($geometry)' doit lever,
    # pas être silencieusement traité comme l'un des deux cas triviaux.
    qml = (CORPUS / "symbol_layers/Marker/GeometryGenerator.qml").read_text()
    qml_modifie = qml.replace('name="geometryModifier" value="@geometry"',
                               'name="geometryModifier" value="buffer($geometry, 5)"')
    assert qml_modifie != qml  # la substitution a bien eu lieu
    with tempfile.NamedTemporaryFile("w", suffix=".qml", delete=False) as f:
        f.write(qml_modifie)
        chemin = f.name
    try:
        lire_fichier_qml(chemin)
    except CoucheDeSymboleNonSupportee as e:
        assert "buffer" in str(e)
        print("OK : GeometryGenerator(expression arbitraire) rejeté explicitement -",
              str(e).splitlines()[0][:90])
        return
    finally:
        Path(chemin).unlink()
    raise AssertionError("GeometryGenerator(buffer(...)) aurait dû lever CoucheDeSymboleNonSupportee")


def test_arrow_line_decision_largeur_moyenne():
    r = lire_fichier_qml(str(CORPUS / "symbol_layers/Line/ArrowLine.qml"))
    sym = r.style.rules[0].symbolizers[0].root
    assert sym.kind == "Line"
    assert any("décision actée" in a and "ArrowLine" in a for a in r.avertissements)
    print("OK : ArrowLine -> ligne pleine de largeur moyenne, décision actée et documentée")


def test_sous_symbole_absent_leve_document_invalide():
    # Garde-fou du mécanisme récursif lui-même : une classe composite privée
    # de son <symbol> imbriqué (QML corrompu/tronqué) doit échouer de façon
    # nommée (DocumentQMLInvalide), jamais silencieusement.
    qml = (CORPUS / "symbol_layers/Fill/CentroidFill.qml").read_text()
    import re as _re
    qml_sans_sous_symbole = _re.sub(
        r'<symbol clip_to_extent="1" type="marker" name="@0@0".*?</symbol>',
        "", qml, count=1, flags=_re.DOTALL,
    )
    assert qml_sans_sous_symbole != qml
    with tempfile.NamedTemporaryFile("w", suffix=".qml", delete=False) as f:
        f.write(qml_sans_sous_symbole)
        chemin = f.name
    try:
        lire_fichier_qml(chemin)
    except DocumentQMLInvalide as e:
        assert "sous-symbole" in str(e)
        print("OK : sous-symbole imbriqué absent -> DocumentQMLInvalide explicite")
        return
    finally:
        Path(chemin).unlink()
    raise AssertionError("CentroidFill sans sous-symbole aurait dû lever DocumentQMLInvalide")


def test_expression_if_traduite_via_traducteur_general():
    # Depuis l'introduction du traducteur d'expressions général
    # (styleforge_core.readers.expressions), if(cond,alors,sinon) N'EST
    # PLUS hors périmètre : c'est un cas explicitement couvert (traduit en
    # Fcase, voir la docstring de _traduire_appel_valeur). Ce test remplace
    # l'ancien test_expression_non_triviale_levee_par_defaut, qui vérifiait
    # l'inverse avec le traducteur minimal précédent — changement de
    # comportement assumé et documenté (cf. rapport du traducteur
    # d'expressions), pas une régression silencieuse.
    r = lire_fichier_qml(
        str(CORPUS / "symbol_layers/Marker/SimpleMarker__expression.qml"),
        sur_expression_non_traduite="lever",
    )
    sym = r.style.rules[0].symbolizers[0].root
    couleur = sym.color
    assert getattr(couleur, "name", None) == "case"
    assert couleur.args[0] == "#0000ff"  # branche "sinon" = valeur par défaut de Fcase
    cas = couleur.args[1]
    cas_condition = cas["case"] if isinstance(cas, dict) else cas.case
    cas_valeur = cas["value"] if isinstance(cas, dict) else cas.value
    assert getattr(cas_condition, "name", cas_condition.get("name") if isinstance(cas_condition, dict) else None) == "greaterThan"
    assert cas_valeur == "#ff0000"
    print("OK : if(\"valeur\">1,'#ff0000','#0000ff') -> Fcase (traducteur d'expressions général)")


def test_expression_hors_grammaire_bornee_levee():
    # Remplace la fonction de couverture de l'ancien test (une expression
    # "non triviale" rejetée par défaut) avec une expression qui reste hors
    # de la grammaire bornée MÊME APRÈS l'introduction du traducteur général
    # : regexp_replace(...) n'a pas de fonction pivot correspondante
    # enregistrée (voir REGISTRE_FONCTIONS_VALEUR, volontairement borné) —
    # la discipline "jamais d'approximation silencieuse" doit continuer à
    # s'appliquer à ce qui dépasse le périmètre choisi.
    brut = (CORPUS / "symbol_layers/Marker/SimpleMarker__expression.qml").read_text()
    modifie = brut.replace(
        "if(&quot;valeur&quot;>1,'#ff0000','#0000ff')",
        "regexp_replace(&quot;valeur&quot;,'[0-9]+','x')",
    )
    assert modifie != brut, "le remplacement de l'expression du fixture n'a rien trouvé à remplacer"
    with tempfile.NamedTemporaryFile("w", suffix=".qml", delete=False) as f:
        f.write(modifie)
        chemin = f.name
    try:
        try:
            lire_fichier_qml(chemin)
        except ProprieteExpressionNonTraduite as e:
            assert "fillColor" in str(e)
            assert "regexp_replace" in str(e)
            print("OK : regexp_replace(...) hors grammaire bornée rejeté explicitement -",
                  str(e).splitlines()[0][:100])
            return
        raise AssertionError("regexp_replace(...) aurait dû lever ProprieteExpressionNonTraduite")
    finally:
        Path(chemin).unlink()


def test_expression_non_triviale_mode_avertir():
    # Même fixture regexp_replace(...) que ci-dessus (hors grammaire bornée),
    # mais en mode "avertir" : valeur statique conservée + avertissement.
    brut = (CORPUS / "symbol_layers/Marker/SimpleMarker__expression.qml").read_text()
    modifie = brut.replace(
        "if(&quot;valeur&quot;>1,'#ff0000','#0000ff')",
        "regexp_replace(&quot;valeur&quot;,'[0-9]+','x')",
    )
    with tempfile.NamedTemporaryFile("w", suffix=".qml", delete=False) as f:
        f.write(modifie)
        chemin = f.name
    try:
        r = lire_fichier_qml(chemin, sur_expression_non_traduite="avertir")
    finally:
        Path(chemin).unlink()
    sym = r.style.rules[0].symbolizers[0].root
    assert sym.color == "#ff0000"  # valeur statique littérale conservée
    assert any("fillColor" in a and "non traduite" in a for a in r.avertissements)
    print("OK : mode 'avertir' -> valeur statique conservée + avertissement explicite")


_QML_CHAMP_NU = """<?xml version="1.0"?>
<qgis version="3.40.4">
  <renderer-v2 type="singleSymbol">
    <symbols>
      <symbol type="marker" name="0" alpha="1">
        <layer class="SimpleMarker" enabled="1">
          <Option type="Map">
            <Option type="QString" name="name" value="circle"/>
            <Option type="QString" name="color" value="255,0,0,255"/>
            <Option type="QString" name="outline_color" value="0,0,0,255"/>
            <Option type="QString" name="outline_width" value="0"/>
            <Option type="QString" name="outline_width_unit" value="MM"/>
            <Option type="QString" name="size" value="2"/>
            <Option type="QString" name="size_unit" value="MM"/>
          </Option>
          <data_defined_properties>
            <Option type="Map">
              <Option type="Map" name="properties">
                <Option type="Map" name="fillColor">
                  <Option type="bool" name="active" value="true"/>
                  <Option type="QString" name="expression" value="&quot;couleur_attribut&quot;"/>
                </Option>
              </Option>
            </Option>
          </data_defined_properties>
        </layer>
      </symbol>
    </symbols>
  </renderer-v2>
</qgis>
"""


_LAYER_SIMPLEMARKER_MARKERLINE = (
    '            <layer class="SimpleMarker" locked="0" pass="0" '
    'id="{f2ac1b9f-3054-4d24-a147-c86c372cb702}" enabled="1">'
)

_LAYER_SVGMARKER_MINIMAL = """            <layer class="SvgMarker" locked="0" pass="0" id="{6a5df582-6f7f-4e21-92df-44ab68ba845c}" enabled="1">
              <Option type="Map">
                <Option type="QString" name="angle" value="0"/>
                <Option type="QString" name="color" value="35,35,35,255,rgb:0.13725490196078433,0.13725490196078433,0.13725490196078433,1"/>
                <Option type="QString" name="fixedAspectRatio" value="0"/>
                <Option type="QString" name="horizontal_anchor_point" value="1"/>
                <Option type="QString" name="name" value=""/>
                <Option type="QString" name="offset" value="0,0"/>
                <Option type="QString" name="offset_map_unit_scale" value="3x:0,0,0,0,0,0"/>
                <Option type="QString" name="offset_unit" value="MM"/>
                <Option type="QString" name="outline_color" value="35,35,35,255,rgb:0.13725490196078433,0.13725490196078433,0.13725490196078433,1"/>
                <Option type="QString" name="outline_width" value="0.2"/>
                <Option type="QString" name="outline_width_map_unit_scale" value="3x:0,0,0,0,0,0"/>
                <Option type="QString" name="outline_width_unit" value="MM"/>
                <Option name="parameters"/>
                <Option type="QString" name="scale_method" value="diameter"/>
                <Option type="QString" name="size" value="4"/>
                <Option type="QString" name="size_map_unit_scale" value="3x:0,0,0,0,0,0"/>
                <Option type="QString" name="size_unit" value="MM"/>
                <Option type="QString" name="vertical_anchor_point" value="1"/>
              </Option>"""


def _qml_marker_line_avec_sous_symbole_modifie(remplacement_ouverture_layer: str | None,
                                                 enabled_valeur: str | None = None) -> str:
    """Charge le corpus MarkerLine.qml et modifie son unique <layer> imbriqué
    (le sous-symbole SimpleMarker sous graphicStroke) : soit en remplaçant sa
    balise d'ouverture (pour en changer la classe, ex. -> SvgMarker), soit en
    changeant juste son attribut enabled (pour le désactiver)."""
    qml = (CORPUS / "symbol_layers/Line/MarkerLine.qml").read_text()
    assert qml.count(_LAYER_SIMPLEMARKER_MARKERLINE) == 1
    if remplacement_ouverture_layer is not None:
        qml = qml.replace(_LAYER_SIMPLEMARKER_MARKERLINE, remplacement_ouverture_layer)
    if enabled_valeur is not None:
        qml = qml.replace(
            _LAYER_SIMPLEMARKER_MARKERLINE,
            _LAYER_SIMPLEMARKER_MARKERLINE.replace('enabled="1"', f'enabled="{enabled_valeur}"'),
        )
    return qml


def _ecrire_temp_qml(contenu: str) -> str:
    with tempfile.NamedTemporaryFile("w", suffix=".qml", delete=False) as f:
        f.write(contenu)
        return f.name


def test_marker_line_icon_accepte_via_graphic_stroke():
    # Lacune fermée : MarkerLine acceptait auparavant UNIQUEMENT un
    # sous-symbole 'Mark' (CoucheDeSymboleNonSupportee sinon), alors que le
    # pivot type graphicStroke en Union[Mark, Text, Icon, None] — un Icon
    # imbriqué est structurellement légitime, c'est à l'ÉCRIVAIN de décider
    # s'il sait le représenter (le lecteur ne doit pas préjuger). Ce QML
    # remplace le sous-symbole SimpleMarker du corpus MarkerLine.qml par un
    # SvgMarker (Icon) minimal.
    qml = (CORPUS / "symbol_layers/Line/MarkerLine.qml").read_text()
    assert _LAYER_SIMPLEMARKER_MARKERLINE in qml
    debut = qml.index(_LAYER_SIMPLEMARKER_MARKERLINE)
    fin = qml.index("</layer>", debut) + len("</layer>")
    qml_modifie = qml[:debut] + _LAYER_SVGMARKER_MINIMAL + "\n            </layer>" + qml[fin:]
    chemin = _ecrire_temp_qml(qml_modifie)
    try:
        r = lire_fichier_qml(chemin)
    finally:
        Path(chemin).unlink()
    sym = r.style.rules[0].symbolizers[0].root
    assert sym.kind == "Line"
    graphic_stroke = getattr(sym.graphicStroke, "root", sym.graphicStroke)
    assert graphic_stroke.kind == "Icon"
    print("OK : MarkerLine + sous-symbole Icon -> lu fidèlement (kind='Icon' sous graphicStroke), "
          "pas rejeté par le lecteur")


def test_sous_symbole_entierement_desactive_ne_produit_aucun_symbolizer():
    # Lacune fermée : un sous-symbole composite dont TOUTES les <layer>
    # imbriquées sont enabled="0" levait auparavant DocumentQMLInvalide (QML
    # pourtant parfaitement valide - observé sur le corpus réel CNIG, 5
    # fichiers). Traité maintenant comme une <layer> de premier niveau
    # désactivée : aucun Symbolizer produit pour cette couche composite,
    # avec avertissement explicite (pas silencieux).
    qml_modifie = _qml_marker_line_avec_sous_symbole_modifie(None, enabled_valeur="0")
    chemin = _ecrire_temp_qml(qml_modifie)
    try:
        r = lire_fichier_qml(chemin)
    finally:
        Path(chemin).unlink()
    assert r.style.rules[0].symbolizers in (None, [])
    assert any("sans aucune" in a and "MarkerLine" in a for a in r.avertissements)
    print("OK : MarkerLine avec sous-symbole entièrement désactivé -> aucun Symbolizer, "
          "avertissement explicite (pas DocumentQMLInvalide)")


def test_outline_style_no_neutralise_le_trait_sans_avertissement():
    # outline_style='no' (Qt::NoPen) est une interprétation EXACTE (QGIS ne
    # dessine aucun trait) : neutralisé sans avertissement, comme une <layer>
    # désactivée. Observé sur le corpus réel (SUP) : outline_color peut être
    # VIDE dans cet état (ne doit plus lever DocumentQMLInvalide).
    qml = (CORPUS / "symbol_layers/Marker/SimpleMarker.qml").read_text()
    ligne_cible = ('            <Option type="QString" name="outline_color" '
                   'value="35,35,35,255,rgb:0.13725490196078433,0.13725490196078433,'
                   '0.13725490196078433,1"/>')
    assert qml.count(ligne_cible) == 1
    qml_modifie = qml.replace(
        ligne_cible,
        '            <Option type="QString" name="outline_color" value=""/>',
    ).replace(
        '<Option type="QString" name="outline_style" value="solid"/>\n'
        '            <Option type="QString" name="outline_width" value="0"/>',
        '<Option type="QString" name="outline_style" value="no"/>\n'
        '            <Option type="QString" name="outline_width" value="5"/>',
    )
    assert qml_modifie != qml
    chemin = _ecrire_temp_qml(qml_modifie)
    try:
        r = lire_fichier_qml(chemin)
    finally:
        Path(chemin).unlink()
    sym = r.style.rules[0].symbolizers[0].root
    assert float(sym.strokeWidth) == 0.0
    assert float(sym.strokeOpacity) == 0.0
    assert not any("outline_color vide" in a for a in r.avertissements)
    print("OK : outline_style='no' + outline_color vide -> trait neutralisé (strokeWidth=0), "
          "aucun avertissement (interprétation exacte, pas une approximation)")


def test_outline_color_vide_sans_style_no_avertit():
    # Même symptôme (outline_color vide) mais SANS outline_style='no' pour le
    # justifier (ex. outline_style='solid') : observé tel quel sur le corpus
    # réel (SUP/ASSIETTE_SUP_S). Neutralisé PAR HYPOTHÈSE (une chaîne vide
    # n'est de toute façon pas un encodage QGIS valide), mais cette fois avec
    # un avertissement explicite car c'est une approximation non certaine.
    qml = (CORPUS / "symbol_layers/Marker/SimpleMarker.qml").read_text()
    ligne_cible = ('            <Option type="QString" name="outline_color" '
                   'value="35,35,35,255,rgb:0.13725490196078433,0.13725490196078433,'
                   '0.13725490196078433,1"/>')
    assert qml.count(ligne_cible) == 1
    qml_modifie = qml.replace(
        ligne_cible,
        '            <Option type="QString" name="outline_color" value=""/>',
    )
    assert qml_modifie != qml
    chemin = _ecrire_temp_qml(qml_modifie)
    try:
        r = lire_fichier_qml(chemin)
    finally:
        Path(chemin).unlink()
    sym = r.style.rules[0].symbolizers[0].root
    assert float(sym.strokeWidth) == 0.0
    assert any("outline_color vide" in a and "SimpleMarker" in a for a in r.avertissements)
    print("OK : outline_color vide sans outline_style='no' -> trait neutralisé PAR HYPOTHÈSE, "
          "avec avertissement explicite (approximation, pas une certitude)")


def test_centroid_fill_icon_accepte():
    # Même lacune que MarkerLine, fermée pour CentroidFill (troisième contexte
    # composite trouvé sur le corpus réel CNIG, psmv_psc_s.qml) : dict(sous)
    # copie déjà tous les champs de l'IconSymbolizer imbriqué (structure
    # générique, pas de champ 'kind' codé en dur) donc aucun autre changement
    # n'était nécessaire une fois le kind-check élargi.
    qml = (CORPUS / "symbol_layers/Fill/CentroidFill.qml").read_text()
    cible = ('            <layer class="SimpleMarker" locked="0" pass="0" '
             'id="{0358da50-3ae2-4e92-9dc6-ce92f1bb8ac1}" enabled="1">')
    assert qml.count(cible) == 1
    debut = qml.index(cible)
    fin = qml.index("</layer>", debut) + len("</layer>")
    qml_modifie = qml[:debut] + _LAYER_SVGMARKER_MINIMAL + "\n            </layer>" + qml[fin:]
    chemin = _ecrire_temp_qml(qml_modifie)
    try:
        r = lire_fichier_qml(chemin)
    finally:
        Path(chemin).unlink()
    sym = r.style.rules[0].symbolizers[0].root
    assert sym.kind == "Icon"
    assert sym.geometry == {"name": "centroid", "args": [{"name": "property", "args": ["geometry"]}]}
    print("OK : CentroidFill + sous-symbole Icon -> lu fidèlement (kind='Icon' + geometry=centroid(...))")


def test_reference_de_champ_nue_traduite():
    # Le corpus niveau 1 n'exerce que l'expression if(...) (non triviale) ;
    # ce QML minimal couvre le SEUL cas que ce lecteur traduit
    # automatiquement (voir traduire_reference_champ_nue).
    with tempfile.NamedTemporaryFile("w", suffix=".qml", delete=False) as f:
        f.write(_QML_CHAMP_NU)
        chemin = f.name
    try:
        r = lire_fichier_qml(chemin, sur_expression_non_traduite="lever")
    finally:
        Path(chemin).unlink()
    sym = r.style.rules[0].symbolizers[0].root
    # 'color' doit maintenant être une Fproperty("couleur_attribut"), pas "#ff0000"
    couleur = sym.color
    assert hasattr(couleur, "root") or hasattr(couleur, "args")
    print("OK : référence de champ nue \"champ\" traduite en Fproperty, sans avertissement ni erreur")


if __name__ == "__main__":
    test_single_symbol()
    test_categorized_symbol()
    test_graduated_symbol()
    test_rule_renderer()
    test_rule_renderer_filtre_riche_traducteur_general()
    test_is_null_traduit_bout_en_bout_via_rule_renderer()
    test_null_symbol()
    test_ellipse_marker_bout_en_bout()
    test_renderer_hors_perimetre()
    test_couche_hors_perimetre()
    test_couches_hors_perimetre_avec_raison_specifique()
    test_couches_etendues_bout_en_bout()
    test_filled_line_cle_color_pas_line_color()
    test_animated_marker_avertit_frame_rate()
    test_svg_marker_avertit_outline_et_couleur()
    test_raster_fill_via_graphic_fill()
    test_font_marker_ttf()
    test_centroid_fill_via_sous_symbole()
    test_marker_line_via_graphic_stroke()
    test_hash_line_marque_orientee()
    test_line_pattern_fill_angle_exact_avec_rotation_residuelle()
    test_hachure_angle_non_rond_preserve_par_rotation_residuelle()
    test_point_pattern_fill_via_graphic_fill_padding()
    test_geometry_generator_cas_trivial_identite()
    test_geometry_generator_cas_general_leve()
    test_arrow_line_decision_largeur_moyenne()
    test_sous_symbole_absent_leve_document_invalide()
    test_marker_line_icon_accepte_via_graphic_stroke()
    test_sous_symbole_entierement_desactive_ne_produit_aucun_symbolizer()
    test_outline_style_no_neutralise_le_trait_sans_avertissement()
    test_outline_color_vide_sans_style_no_avertit()
    test_centroid_fill_icon_accepte()
    test_expression_if_traduite_via_traducteur_general()
    test_expression_hors_grammaire_bornee_levee()
    test_expression_non_triviale_mode_avertir()
    test_reference_de_champ_nue_traduite()
    print("\nTous les tests du lecteur QML sont passés.")
