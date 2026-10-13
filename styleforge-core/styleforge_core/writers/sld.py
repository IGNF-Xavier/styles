#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
styleforge_core.writers.sld — Écrivain GÉNÉRAL (mais délibérément BORNÉ) du
pivot geostyler-style vers un document SLD 1.0.0 (le format OGC historique,
supporté par GeoServer ET par QGIS via QgsVectorLayer.loadSldStyle(), ce qui
en fait l'oracle de vérification de ce module — PyQGIS reste ici, comme pour
le lecteur QML, un ORACLE de test, jamais une dépendance d'exécution : ce
module n'importe QGIS nulle part, il ne fait que produire du XML texte).

Portée assumée, cumulée sur deux itérations (chantier "écrivain", scope
"un format à la fois" puis "cœur minimal d'abord" par défaut, symétrique à
la façon dont le lecteur a grandi couche par couche plutôt que tout d'un
coup) :
  - Style -> NamedLayer/UserStyle/FeatureTypeStyle/Rule(s), avec Name/Title,
    MinScaleDenominator/MaxScaleDenominator (littéraux numériques
    seulement), ElseFilter pour Rule.elseRule ;
  - 4 Symbolizer sur 6 : MarkSymbolizer -> PointSymbolizer (Mark/Fill/
    Stroke/Opacity/Size/Rotation), FillSymbolizer -> PolygonSymbolizer
    (Fill/Stroke), LineSymbolizer -> LineSymbolizer (Stroke), IconSymbolizer
    -> PointSymbolizer (Graphic/ExternalGraphic/Opacity/Size/Rotation,
    format image/svg+xml SEULEMENT — voir plus bas). PAS encore
    TextSymbolizer/RasterSymbolizer, ni les motifs graphicFill/graphicStroke
    (Fill/Line/Mark pilotés par un symbolizer imbriqué plutôt qu'une couleur
    unie — CentroidFill/MarkerLine/HashLine/LinePatternFill/PointPatternFill
    côté lecteur) : chantier de suivi ;
  - Rule.filter : comparaisons (== != < <= > >=) et AND/OR/NOT en forme
    TUPLE, IS [NOT] NULL, IN (...) et BETWEEN (Fbetween, forme DICT
    {"name":"between","args":[valeur,min,max]}) en forme DICT, LIKE sensible
    à la casse ("*=") -> ogc:PropertyIsLike. TOUS ces cas ont été vérifiés
    bout en bout contre l'oracle PyQGIS (QgsVectorLayer.loadSldStyle() +
    inspection de rule.filterExpression()) : AND/OR imbriqués, IS NULL,
    NOT(IS NULL), IN (reconstruit en OR de comparaisons), LIKE, BETWEEN —
    les 6 round-trippent à l'identique (BETWEEN -> "x >= min AND x <= max"
    via ogc:PropertyIsBetween, qui EST un opérateur OGC Filter natif
    standard : une itération précédente de ce module avait supposé, à tort
    et sans vérifier, qu'aucun équivalent natif n'existait et qu'il
    faudrait une forme tuple "<=x<=" inexistante dans le schéma pivot —
    corrigé après consultation de la documentation officielle
    geostyler-style, qui liste bien Fbetween).
    strMatches (LIKE/ILIKE insensible à la casse, ou LIKE/ILIKE hors
    position de Filter) -> ogc:PropertyIsLike AUSSI, désormais : la regex
    Java que strMatches porte est, dans ce projet, TOUJOURS produite par
    readers.expressions._motif_like_vers_regex (seul producteur, vérifié —
    voir _detecter_motif_like_depuis_regex plus bas) à partir d'un motif
    LIKE/ILIKE SQL simple (% et _) — jamais un regexp_match QGIS arbitraire,
    explicitement non traduit par le lecteur. Reconvertible sans perte vers
    wildCard="%"/singleChar="_"/escape="\\"/matchCase="false" (ILIKE) ou
    sans matchCase (LIKE) : vérifié à l'oracle QGIS, à l'écriture
    (saveSldStyle() produit EXACTEMENT ces attributs pour un filtre ILIKE
    natif) ET au rechargement (loadSldStyle() -> filterExpression() ==
    "idass ILIKE 'a1%'" pour le document construit à la main avec ces
    attributs). Une regex strMatches qui ne correspond PAS à cette forme
    canonique garde l'exception nommée — jamais une approximation devinée.
  - Valeurs (couleur, taille...) : UNIQUEMENT des LITTÉRAUX pour cette
    itération (pas de propriété ni d'expression). Ceci n'est PAS le choix
    initial : Fproperty/arithmétique (add/sub/mul/div)/FstrConcat (->
    ogc:Function name="Concatenate") avaient été écrits et produisaient un
    XML syntaxiquement correct selon la norme OGC SE/Filter — mais
    vérifiés contre l'oracle PyQGIS (QgsVectorLayer.loadSldStyle() suivi de
    l'inspection de symbolLayer.dataDefinedProperties()), ils se sont
    révélés NE PAS être repris par l'importeur SLD de QGIS 3.40 : une
    <CssParameter> ou un <Size> contenant un ogc:PropertyName ou un
    ogc:Function, même syntaxiquement valide, retombe silencieusement sur
    la valeur statique par défaut de QGIS (testé sous 3 formes : arbre
    arithmétique complet, ogc:PropertyName nu, XML compact sans espaces —
    même résultat les 3 fois). Ce n'est pas un défaut du XML produit par
    cet écrivain (la même construction _construire_element_valeur EST
    reprise correctement côté FILTRE, chemin de code QGIS différent et
    fiable) : c'est une limite de l'IMPORT SLD de QGIS pour les propriétés
    de symbolizer pilotées par expression, découverte en testant plutôt que
    supposée. Retiré de cette itération plutôt que livré non vérifié —
    signalé ici plutôt que contourné en silence, même discipline que pour
    IS NULL côté lecteur.
  - IconSymbolizer.format : SEUL 'image/svg+xml' est écrit. Vérifié contre
    l'oracle (loadSldStyle() + un VRAI rendu pixel, pas seulement
    l'inspection des propriétés stockées) que 'image/png' — syntaxe
    identique, fichier image valide et existant, testé sous plusieurs
    variantes (avec/sans Opacity-Size-Rotation, avec/sans Format, avec
    xlink:type) — échoue systématiquement à l'import dans QGIS 3.40
    (ok=False, message d'erreur vide, retombe sur un marqueur simple par
    défaut), alors que 'image/svg+xml' avec un fichier par ailleurs
    identique s'importe parfaitement (QgsSvgMarkerSymbolLayer correctement
    peuplé). Les 4 autres valeurs de l'enum pivot (gif/jpeg/jpg/png) sont
    donc exclues, pas seulement png par extrapolation non vérifiée.
  - <Graphic><Opacity> (Mark ET Icon) : ÉCRIT (c'est une construction OGC SE
    1.0 standard, potentiellement utile sous GeoServer) MAIS un avertissement
    explicite accompagne systématiquement son écriture, car vérifié — par
    inspection des propriétés ET par un rendu pixel réel comparant Opacity=1.0
    et Opacity=0.2 du même symbole (pixel de sortie strictement identique
    dans les deux cas) — que QGIS 3.40 n'applique PAS cette opacité de
    Graphic à l'affichage. Ceci corrige une affirmation trop optimiste d'une
    itération précédente de ce module, qui prétendait cette propriété
    "vérifiée" sans avoir testé spécifiquement CETTE balise (le test
    original portait probablement sur fillOpacity/CssParameter, une
    propriété distincte qui, elle, round-trippe correctement).

Tout ce qui sort de cette portée lève ExpressionPivotNonEcrite AVEC le
fragment précis en cause — jamais une approximation silencieuse, même
principe que le lecteur QML (RAISONS_HORS_PERIMETRE, ExpressionQGISNonTraduite).
"""
from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from typing import Any, Callable
from urllib.parse import quote
from xml.dom import minidom

NS_SLD = "http://www.opengis.net/sld"
NS_OGC = "http://www.opengis.net/ogc"
NS_XLINK = "http://www.w3.org/1999/xlink"
NS_XSI = "http://www.w3.org/2001/XMLSchema-instance"

ET.register_namespace("", NS_SLD)
ET.register_namespace("ogc", NS_OGC)
ET.register_namespace("xlink", NS_XLINK)
ET.register_namespace("xsi", NS_XSI)


class ExpressionPivotNonEcrite(Exception):
    """Levée quand une valeur, un filtre ou une propriété de symbolizer du
    pivot sort de la portée BORNÉE de cet écrivain (voir la docstring de
    module). Toujours accompagnée du fragment précis en cause."""


def _q_sld(tag: str) -> str:
    return f"{{{NS_SLD}}}{tag}"


def _q_ogc(tag: str) -> str:
    return f"{{{NS_OGC}}}{tag}"


def _normaliser(valeur: Any) -> Any:
    """Accepte soit un dict pivot brut (la forme canonique produite par le
    lecteur et validée par valider_style()), soit une instance pydantic du
    modèle généré — dans ce 2e cas, la convertit en dict via model_dump()
    pour n'avoir qu'UNE seule forme à traiter dans tout ce module."""
    if hasattr(valeur, "model_dump"):
        return valeur.model_dump(exclude_none=True)
    return valeur


# --------------------------------------------------------------------------- registre des fonctions de VALEUR (Fxxx -> expression OGC)
#: nom de fonction pivot (le "name" d'un dict Fxxx) -> constructeur
#: OGC Filter/SE. Registre OUVERT et délibérément PETIT, même discipline que
#: REGISTRE_FONCTIONS_VALEUR côté lecteur : chaque entrée correspond à une
#: fonction du vocabulaire OGC Filter Encoding standard (Add/Sub/Mul/Div) ou
#: à une fonction d'extension GeoServer au nom IDENTIQUE à celui du pivot
#: (Concatenate) — jamais une supposition sur ce qu'un moteur de rendu
#: pourrait comprendre.
_ARITH_PIVOT_VERS_OGC = {"add": "Add", "sub": "Sub", "mul": "Mul", "div": "Div"}


def _construire_element_valeur(valeur: Any) -> ET.Element:
    """Traduit une valeur pivot (littéral, Fproperty, ou fonction du
    registre borné ci-dessus) en un unique élément OGC (ogc:Literal,
    ogc:PropertyName, ogc:Add/Sub/Mul/Div, ogc:Function). Lève
    ExpressionPivotNonEcrite pour tout le reste (Fcase, Finterpolate,
    Fstep, les fonctions de texte non listées...) plutôt que d'approximer."""
    if isinstance(valeur, dict) and "name" in valeur:
        nom = valeur["name"]
        args = valeur.get("args", [])
        if nom == "property":
            el = ET.Element(_q_ogc("PropertyName"))
            el.text = str(args[0])
            return el
        if nom in _ARITH_PIVOT_VERS_OGC:
            if len(args) != 2:
                raise ExpressionPivotNonEcrite(
                    f"{nom}(...) : {len(args)} argument(s), 2 attendus pour un "
                    f"opérateur arithmétique OGC Filter (Add/Sub/Mul/Div)."
                )
            el = ET.Element(_q_ogc(_ARITH_PIVOT_VERS_OGC[nom]))
            el.append(_construire_element_valeur(args[0]))
            el.append(_construire_element_valeur(args[1]))
            return el
        if nom == "strConcat":
            # FstrConcat pivot <-> la fonction d'extension GeoServer
            # "Concatenate" (même nom que dans le vocabulaire OGC Filter
            # Function de GeoServer, ce n'est pas une coïncidence : le
            # pivot geostyler-style a été conçu pour coller à ce
            # vocabulaire). Variadique, comme FstrConcat lui-même.
            el = ET.Element(_q_ogc("Function"))
            el.set("name", "Concatenate")
            for a in args:
                el.append(_construire_element_valeur(a))
            return el
        raise ExpressionPivotNonEcrite(
            f"fonction pivot {nom!r} non enregistrée dans l'écrivain SLD "
            f"(registre volontairement borné à cette itération — voir la "
            f"docstring de styleforge_core.writers.sld)."
        )
    if valeur is None:
        raise ExpressionPivotNonEcrite(
            "valeur littérale None hors position de filtre (IS [NOT] NULL) : "
            "aucune représentation OGC Filter standard vérifiée pour cette "
            "itération."
        )
    if isinstance(valeur, bool):
        el = ET.Element(_q_ogc("Literal"))
        el.text = "true" if valeur else "false"
        return el
    el = ET.Element(_q_ogc("Literal"))
    el.text = str(valeur)
    return el


def _valeur_symbolizer_litterale(valeur: Any, contexte: str, nom_proprietaire: str) -> str:
    """Convertit une valeur de PROPRIÉTÉ DE SYMBOLIZER (couleur, taille...)
    en texte littéral pour un CssParameter/Size/Rotation/Opacity — UNIQUEMENT
    des littéraux pour cette itération (pas de Fproperty ni d'expression) :
    voir la docstring de module pour la limite d'import SLD de QGIS vérifiée
    qui justifie cette restriction, distincte du côté FILTRE (qui, lui,
    accepte pleinement _construire_element_valeur — chemin QGIS différent
    et fiable)."""
    if isinstance(valeur, dict):
        raise ExpressionPivotNonEcrite(
            f"{contexte} : {nom_proprietaire} piloté par une expression pivot "
            f"({valeur.get('name', '?')!r}) — retiré de cette itération : "
            f"vérifié contre l'oracle PyQGIS (QgsVectorLayer.loadSldStyle()), "
            f"une propriété de symbolizer pilotée par ogc:PropertyName ou "
            f"ogc:Function n'est PAS reprise par l'import SLD de QGIS 3.40 "
            f"(retombe silencieusement sur la valeur statique par défaut), "
            f"voir la docstring de styleforge_core.writers.sld. Seuls les "
            f"littéraux sont écrits pour cette itération."
        )
    if isinstance(valeur, bool):
        return "true" if valeur else "false"
    return str(valeur)


def _definir_parametre(parent: ET.Element, nom_css: str, valeur: Any, contexte: str = "") -> None:
    """Ajoute un <CssParameter name="nom_css"> en texte littéral à 'parent'
    (voir _valeur_symbolizer_litterale : pas d'expression pour cette
    itération, seulement des littéraux, chemin QGIS vérifié fiable)."""
    if valeur is None:
        return
    param = ET.SubElement(parent, _q_sld("CssParameter"))
    param.set("name", nom_css)
    param.text = _valeur_symbolizer_litterale(valeur, contexte, f"CssParameter {nom_css!r}")


def _avertir_proprietes_non_gerees(
    sym: dict, geres: set[str], avertissements: list[str], contexte: str
) -> None:
    ignores_toujours = {"kind", "visibility", "geometry"}
    for cle, val in sym.items():
        if cle in geres or cle in ignores_toujours or val is None:
            continue
        avertissements.append(
            f"{contexte} : propriété de symbolizer {cle!r} (valeur {val!r}) NON "
            f"écrite dans le SLD produit — hors de la portée bornée de cet "
            f"écrivain pour cette itération, PAS silencieusement ignorée."
        )


# --------------------------------------------------------------------------- symbolizers
def _avertir_opacity_graphic_non_verifiee(sym: dict, avertissements: list[str], contexte: str, nom_symbolizer: str) -> None:
    avertissements.append(
        f"{contexte} : Opacity={sym['opacity']!r} écrit dans le SLD (construction OGC SE 1.0 "
        f"standard) mais NON vérifié comme appliqué par l'oracle QGIS pour {nom_symbolizer} — "
        f"testé par introspection des propriétés ET par rendu pixel réel (Opacity=0.2 vs 1.0 "
        f"du même symbole produisent un pixel de sortie strictement identique), QGIS 3.40 "
        f"ignore ce <Graphic><Opacity>. Peut fonctionner sous GeoServer (non vérifiable ici, "
        f"aucun oracle GeoServer disponible)."
    )


def _ajouter_displacement(graphic: ET.Element, sym: dict, contexte: str) -> None:
    """Ajoute <Displacement><DisplacementX/><DisplacementY/></Displacement>
    à un <Graphic> (Mark OU ExternalGraphic, factorisé entre
    _construire_graphic_mark et _construire_graphic_icon) quand le pivot
    porte un 'offset' [x, y] — MarkSymbolizer.offset et IconSymbolizer.offset
    existent tous deux dans le schéma geostyler-style. Vérifié contre
    l'oracle QGIS (QgsVectorLayer.loadSldStyle() sur un SLD construit à la
    main, Mark ET ExternalGraphic) que symbolLayer.offset() reprend
    exactement (DisplacementX, DisplacementY) sans conversion supplémentaire."""
    valeurs = sym.get("offset")
    if valeurs is None:
        return
    if not (isinstance(valeurs, list) and len(valeurs) == 2
            and all(isinstance(v, (int, float)) for v in valeurs)):
        raise ExpressionPivotNonEcrite(
            f"{contexte} : offset={valeurs!r} n'est pas une paire [x, y] de nombres "
            f"littéraux — seul ce cas est écrit par cette itération."
        )
    deplacement = ET.SubElement(graphic, _q_sld("Displacement"))
    dx = ET.SubElement(deplacement, _q_sld("DisplacementX"))
    dx.text = str(valeurs[0])
    dy = ET.SubElement(deplacement, _q_sld("DisplacementY"))
    dy.text = str(valeurs[1])


def _construire_graphic_mark(sym: dict, avertissements: list[str], contexte: str) -> ET.Element:
    """Construit un <Graphic><Mark>...</Mark><Opacity/><Size/><Rotation/></Graphic>
    complet à partir d'un MarkSymbolizer du pivot — factorisé pour être
    réutilisé tel quel par _ecrire_mark (PointSymbolizer) ET par le
    graphicFill/graphicStroke de _ecrire_fill/_ecrire_line (même construction,
    vérifiée séparément dans chacun des deux contextes contre l'oracle)."""
    graphic = ET.Element(_q_sld("Graphic"))
    mark = ET.SubElement(graphic, _q_sld("Mark"))
    nom_forme = ET.SubElement(mark, _q_sld("WellKnownName"))
    nom_forme.text = str(sym.get("wellKnownName") or "circle")
    if sym.get("color") is not None or sym.get("fillOpacity") is not None:
        remplissage = ET.SubElement(mark, _q_sld("Fill"))
        _definir_parametre(remplissage, "fill", sym.get("color"), contexte)
        _definir_parametre(remplissage, "fill-opacity", sym.get("fillOpacity"), contexte)
    if sym.get("strokeColor") is not None or sym.get("strokeWidth") is not None:
        contour = ET.SubElement(mark, _q_sld("Stroke"))
        _definir_parametre(contour, "stroke", sym.get("strokeColor"), contexte)
        _definir_parametre(contour, "stroke-width", sym.get("strokeWidth"), contexte)
        _definir_parametre(contour, "stroke-opacity", sym.get("strokeOpacity"), contexte)
    if sym.get("opacity") is not None:
        el = ET.SubElement(graphic, _q_sld("Opacity"))
        el.text = _valeur_symbolizer_litterale(sym["opacity"], contexte, "Opacity")
        # Vérifié par introspection ET par rendu pixel réel (Opacity=1.0 vs
        # 0.2 sur le même Mark produisent un pixel identique) que QGIS 3.40
        # n'applique PAS ce <Graphic><Opacity> à l'affichage. Écrit malgré
        # tout (construction OGC SE standard) mais avec avertissement.
        _avertir_opacity_graphic_non_verifiee(sym, avertissements, contexte, "MarkSymbolizer")
    if sym.get("radius") is not None:
        el = ET.SubElement(graphic, _q_sld("Size"))
        # SLD Size = diamètre ; pivot 'radius' = QGIS size/2 (convention
        # déjà établie et vérifiée côté lecteur, styleforge_core/readers/
        # qml.py : "radius": float(props["size"]) / 2) — inversée ici à
        # l'identique (radius * 2), pas une nouvelle supposition. Littéral
        # uniquement pour cette itération (voir _valeur_symbolizer_litterale).
        rayon = _valeur_symbolizer_litterale(sym["radius"], contexte, "Size/radius")
        el.text = str(float(rayon) * 2)
    if sym.get("rotate") is not None:
        el = ET.SubElement(graphic, _q_sld("Rotation"))
        el.text = _valeur_symbolizer_litterale(sym["rotate"], contexte, "Rotation")
    _ajouter_displacement(graphic, sym, contexte)
    return graphic


def _ecrire_mark(
    sym: dict, avertissements: list[str], contexte: str,
    *, resoudre_image_embarquee: Callable[[str], str | None] | None = None,
) -> ET.Element:
    # 'resoudre_image_embarquee' fait partie de l'interface commune des
    # écrivains de symbolizer (voir _ecrire_symbolizer/_ECRIVAINS_SYMBOLIZER)
    # mais n'est pertinent que pour Icon/Fill(graphicFill) — MarkSymbolizer
    # n'a pas de propriété 'image', ignoré ici sans effet.
    point = ET.Element(_q_sld("PointSymbolizer"))
    point.append(_construire_graphic_mark(sym, avertissements, contexte))
    _avertir_proprietes_non_gerees(
        sym,
        {"wellKnownName", "color", "fillOpacity", "strokeColor", "strokeWidth",
         "strokeOpacity", "opacity", "radius", "rotate", "offset"},
        avertissements, contexte,
    )
    return point


def _ecrire_fill(
    sym: dict, avertissements: list[str], contexte: str,
    *, resoudre_image_embarquee: Callable[[str], str | None] | None = None,
) -> ET.Element:
    poly = ET.Element(_q_sld("PolygonSymbolizer"))
    if sym.get("graphicFill") is not None:
        # FillSymbolizer.graphicFill (Mark ou Icon imbriqué) -> Fill/GraphicFill.
        # Vérifié contre l'oracle : Mark -> QgsPointPatternFillSymbolLayer
        # (couleur/taille du motif confirmées), Icon(svg) -> QgsSVGFillSymbolLayer
        # (chemin/largeur confirmés) — les deux round-trippent. color/fillOpacity
        # du FillSymbolizer lui-même sont ignorés dans ce cas (le motif remplace
        # la couleur unie, pas une superposition — cohérent avec le choix XOR de
        # Fill dans le schéma SLD : CssParameter OU GraphicFill, pas les deux).
        remplissage = ET.SubElement(poly, _q_sld("Fill"))
        graphic_fill = ET.SubElement(remplissage, _q_sld("GraphicFill"))
        graphic_fill.append(_construire_graphic_imbrique(
            sym["graphicFill"], avertissements, f"{contexte}.graphicFill",
            resoudre_image_embarquee=resoudre_image_embarquee,
        ))
        if sym.get("graphicFillPadding") is not None:
            avertissements.append(
                f"{contexte} : graphicFillPadding={sym['graphicFillPadding']!r} NON écrit — pas "
                f"encore vérifié contre l'oracle pour cette itération (l'espacement du motif "
                f"reste déterminé par Size seul, motif jointif par défaut)."
            )
    elif sym.get("color") is not None or sym.get("fillOpacity") is not None:
        remplissage = ET.SubElement(poly, _q_sld("Fill"))
        _definir_parametre(remplissage, "fill", sym.get("color"), contexte)
        _definir_parametre(remplissage, "fill-opacity", sym.get("fillOpacity"), contexte)
    if sym.get("outlineColor") is not None or sym.get("outlineWidth") is not None:
        contour = ET.SubElement(poly, _q_sld("Stroke"))
        _definir_parametre(contour, "stroke", sym.get("outlineColor"), contexte)
        _definir_parametre(contour, "stroke-width", sym.get("outlineWidth"), contexte)
        _definir_parametre(contour, "stroke-opacity", sym.get("outlineOpacity"), contexte)
        if sym.get("outlineDasharray") is not None:
            valeurs = sym["outlineDasharray"]
            if not (isinstance(valeurs, list) and all(isinstance(v, (int, float)) for v in valeurs)):
                raise ExpressionPivotNonEcrite(
                    f"{contexte} : outlineDasharray={valeurs!r} n'est pas une liste "
                    f"de nombres littéraux — seul ce cas est écrit par cette itération."
                )
            param = ET.SubElement(contour, _q_sld("CssParameter"))
            param.set("name", "stroke-dasharray")
            param.text = " ".join(str(v) for v in valeurs)
    _avertir_proprietes_non_gerees(
        sym,
        {"color", "fillOpacity", "outlineColor", "outlineWidth", "outlineOpacity",
         "outlineDasharray", "graphicFill", "graphicFillPadding"},
        avertissements, contexte,
    )
    return poly


def _ecrire_line(
    sym: dict, avertissements: list[str], contexte: str,
    *, resoudre_image_embarquee: Callable[[str], str | None] | None = None,
) -> ET.Element:
    ligne = ET.Element(_q_sld("LineSymbolizer"))
    if sym.get("graphicFill") is not None and sym.get("graphicStroke") is not None:
        raise ExpressionPivotNonEcrite(
            f"{contexte} : graphicFill ET graphicStroke tous deux définis — le schéma SLD "
            f"n'autorise qu'un seul enfant (GraphicFill OU GraphicStroke, pas les deux) dans "
            f"l'élément Stroke d'un LineSymbolizer, ambigu à écrire."
        )
    if sym.get("graphicFill") is not None:
        # Vérifié contre l'oracle : contrairement à FillSymbolizer.graphicFill
        # (qui fonctionne, voir _ecrire_fill), LineSymbolizer.graphicFill —
        # Stroke/GraphicFill — retombe silencieusement sur un QgsSimpleLineSymbolLayer
        # noir par défaut (color/width par défaut, motif totalement ignoré) :
        # écart réel entre deux emplois syntaxiquement permis du même élément
        # GraphicFill selon le symbolizer parent, découvert en testant.
        raise ExpressionPivotNonEcrite(
            f"{contexte} : LineSymbolizer.graphicFill non écrit — vérifié contre l'oracle QGIS "
            f"que Stroke/GraphicFill (contrairement à Fill/GraphicFill sur un FillSymbolizer) "
            f"retombe silencieusement sur une ligne unie noire par défaut, le motif étant "
            f"entièrement ignoré à l'import."
        )
    if sym.get("graphicStroke") is not None:
        # Mark imbriqué -> QgsMarkerLineSymbolLayer : vérifié contre l'oracle
        # QGIS de bout en bout (écrit, relu par loadSldStyle(), propriétés
        # couleur/taille confirmées ; spacing -> Gap -> interval confirmé,
        # Gap=15 -> layer 'interval'==15).
        #
        # Icon imbriqué (ExternalGraphic) : la structure XML elle-même est
        # IDENTIQUE à celle déjà vérifiée pour Fill/GraphicFill et
        # PointSymbolizer (_construire_graphic_imbrique est le MÊME code pour
        # les trois), et conforme à OGC SE 1.1.0 (Graphic = ExternalGraphic |
        # Mark, sans restriction selon le parent Fill/Stroke). MAIS : QGIS
        # lui-même ne sait PAS relire un ExternalGraphic dans un
        # Stroke/GraphicStroke (vérifié : round-trip loadSldStyle() retombe
        # silencieusement sur une ligne unie par défaut, information perdue à
        # LA LECTURE côté QGIS) — ce qui rend l'oracle QGIS, utilisé partout
        # ailleurs dans ce module pour vérifier un écrivain, structurellement
        # INUTILISABLE ici : il ne peut confirmer QUE ce qu'il sait relire.
        # Écrit quand même (sur demande explicite de maximiser la
        # compatibilité du corpus réel plutôt que d'échouer), avec un
        # avertissement qui le dit EXPLICITEMENT à chaque occurrence — jamais
        # présenté comme vérifié au même titre que le reste de ce module.
        imbrique = _normaliser(sym["graphicStroke"])
        if imbrique.get("kind") not in ("Mark", "Icon"):
            raise ExpressionPivotNonEcrite(
                f"{contexte} : LineSymbolizer.graphicStroke avec un symbolizer imbriqué de type "
                f"{imbrique.get('kind')!r} non écrit — seuls Mark et Icon le sont dans ce contexte."
            )
        if imbrique.get("kind") == "Icon":
            avertissements.append(
                f"{contexte} : LineSymbolizer.graphicStroke avec un Icon (ExternalGraphic) "
                f"imbriqué — écrit conformément à OGC SE 1.1.0 (Graphic = ExternalGraphic | "
                f"Mark), mais PAS VÉRIFIÉ PAR L'ORACLE QGIS : QGIS lui-même ne sait pas relire "
                f"cet élément (round-trip loadSldStyle() retombe sur une ligne unie par défaut), "
                f"ce qui rend la vérification habituelle de ce module impossible ici. Écrit sur "
                f"demande explicite de maximiser la compatibilité plutôt que d'échouer — à "
                f"confirmer par un test de rendu GeoServer réel avant mise en production."
            )
        contour = ET.SubElement(ligne, _q_sld("Stroke"))
        graphic_stroke = ET.SubElement(contour, _q_sld("GraphicStroke"))
        graphic_stroke.append(_construire_graphic_imbrique(
            sym["graphicStroke"], avertissements, f"{contexte}.graphicStroke",
            resoudre_image_embarquee=resoudre_image_embarquee,
        ))
        if sym.get("spacing") is not None:
            gap = ET.SubElement(graphic_stroke, _q_sld("Gap"))
            gap.text = _valeur_symbolizer_litterale(sym["spacing"], contexte, "Gap/spacing")
    elif any(sym.get(c) is not None for c in ("color", "width", "opacity", "dasharray", "cap", "join")):
        contour = ET.SubElement(ligne, _q_sld("Stroke"))
        _definir_parametre(contour, "stroke", sym.get("color"), contexte)
        _definir_parametre(contour, "stroke-width", sym.get("width"), contexte)
        _definir_parametre(contour, "stroke-opacity", sym.get("opacity"), contexte)
        _definir_parametre(contour, "stroke-linecap", sym.get("cap"), contexte)
        _definir_parametre(contour, "stroke-linejoin", sym.get("join"), contexte)
        if sym.get("dasharray") is not None:
            valeurs = sym["dasharray"]
            if not (isinstance(valeurs, list) and all(isinstance(v, (int, float)) for v in valeurs)):
                raise ExpressionPivotNonEcrite(
                    f"{contexte} : dasharray={valeurs!r} n'est pas une liste de "
                    f"nombres littéraux — seul ce cas est écrit par cette itération."
                )
            param = ET.SubElement(contour, _q_sld("CssParameter"))
            param.set("name", "stroke-dasharray")
            param.text = " ".join(str(v) for v in valeurs)
    if sym.get("perpendicularOffset") is not None:
        # Sibling de Stroke/GraphicStroke dans LineSymbolizer (pas un
        # paramètre de Stroke) — vérifié contre l'oracle QGIS
        # (QgsVectorLayer.saveSldStyle() natif sur plu_zone_urba_ge.qml,
        # dont le double-liseré par deux SimpleLine à offsets différents
        # produit exactement <se:PerpendicularOffset>4</se:PerpendicularOffset>
        # pour la couche à offset=3pt, et aucun élément pour celle à offset=0).
        decalage = ET.SubElement(ligne, _q_sld("PerpendicularOffset"))
        decalage.text = _valeur_symbolizer_litterale(
            sym["perpendicularOffset"], contexte, "PerpendicularOffset")
    _avertir_proprietes_non_gerees(
        sym,
        {"color", "width", "opacity", "dasharray", "cap", "join", "graphicFill",
         "graphicStroke", "spacing", "perpendicularOffset"},
        avertissements, contexte,
    )
    return ligne


#: formats MIME acceptés par IconSymbolizer.format côté pivot (5 valeurs de
#: l'enum du schéma). Un seul, image/svg+xml, est écrit par cette itération :
#: vérifié précisément contre l'oracle PyQGIS (QgsVectorLayer.loadSldStyle()
#: PUIS un rendu pixel réel, pas seulement l'inspection des propriétés) que
#: <ExternalGraphic><Format>image/svg+xml</Format> produit un QgsSvgMarkerSymbolLayer
#: correctement peuplé (size, angle confirmés), TANDIS QUE la forme
#: syntaxiquement identique avec image/png (fichier existant, valide, testé
#: sous 3 variantes : avec/sans Opacity-Size-Rotation, sans Format, avec
#: xlink:type) échoue systématiquement au chargement (loadSldStyle renvoie
#: ok=False, message d'erreur vide, retombe sur un QgsSimpleMarkerSymbolLayer
#: par défaut) — un écart réel entre deux MIME types syntaxiquement
#: équivalents pour QGIS 3.40, découvert en testant, pas supposé par
#: analogie avec le comportement habituel de GeoServer.
_FORMATS_ICON_ECRITS = {"image/svg+xml"}


def _href_svg_parametrique(href: str, color: str | None) -> str:
    """Ajoute, le cas échéant, le paramètre de requête 'fill' documenté par
    GeoServer pour les SVG PARAMÉTRIQUES (convention QGIS/GeoServer partagée
    'fill="param(fill)"' dans le SVG lui-même) — voir la documentation
    GeoServer, Graphic symbology / "Parametric SVG"
    (https://docs.geoserver.org/main/en/user/styling/sld/extensions/pointsymbols.html) :
    la couleur se transmet en paramètre de requête ajouté à xlink:href, ex.
    'poi_peak.svg?fill=%23ff0000' (le '#' est url-encodé en '%23').

    'color' vient du pivot IconSymbolizer.color (lecteur QML, SvgMarker
    uniquement — voir styleforge_core.readers.qml._lire_icone_image,
    avec_couleur=True) : la couleur de substitution que QGIS applique à un
    pictogramme SVG générique au moment du rendu. Jusqu'ici ce champ était
    silencieusement abandonné par cet écrivain (ni SLD ni MBStyle ne le
    consommaient) : le SVG déployé reste le même quelle que soit la couche,
    mais son attribut 'fill="param(fill)"' (sans repli) est syntaxiquement
    invalide pour un moteur de rendu qui ne le résout pas — GeoServer retombe
    alors très probablement sur du noir plutôt que la teinte configurée dans
    QGIS, une perte visuelle réelle, pas cosmétique (voir l'analyse du
    2026-10-13, rapport_conversion.md du corpus CNIG : 871 des 873 SVG
    déployés par le CLI utilisent cette convention paramétrique).

    Ne s'applique qu'à un href SANS requête préexistante (cas de ce module,
    qui ne produit que des chemins relatifs 'svg/cnig/<nom>.svg' ou des hrefs
    déjà résolus par l'appelant) : si un '?' est déjà présent, le paramètre
    est ajouté avec '&' plutôt que d'écraser une requête existante."""
    if not color:
        return href
    separateur = "&" if "?" in href else "?"
    return f"{href}{separateur}fill={quote(color, safe='')}"


def _construire_graphic_icon(
    sym: dict, avertissements: list[str], contexte: str,
    *, resoudre_image_embarquee: Callable[[str], str | None] | None = None,
) -> ET.Element:
    """Construit un <Graphic><ExternalGraphic>...</ExternalGraphic><Opacity/>
    <Size/><Rotation/></Graphic> complet à partir d'un IconSymbolizer du
    pivot — factorisé, même principe que _construire_graphic_mark, pour être
    réutilisé par _ecrire_icon ET par le graphicFill de _ecrire_fill.

    'resoudre_image_embarquee' : IconSymbolizer.image (str) est censé être un
    chemin/URL — mais certains lecteurs QML (SLYR/CNIG notamment) peuvent y
    faire passer, TEL QUEL depuis la propriété QML source, un SVG EMBARQUÉ en
    base64 (convention QGIS "base64:<données>", pas un chemin). Cet écrivain
    est zéro-E/S (voir la docstring de module) : il ne peut ni décoder, ni
    matérialiser ce contenu en fichier lui-même, et ÉCRIRE la chaîne
    "base64:..." telle quelle dans xlink:href produirait un SLD syntaxiquement
    valide mais sémantiquement cassé (GeoServer traite l'href comme un chemin
    de fichier ou une URL, jamais comme des données embarquées). Le CHOIX de
    savoir où/comment matérialiser cette image (nom de fichier, répertoire de
    sortie, déduplication...) appartient à l'appelant — d'où ce callback
    optionnel : si fourni, il est appelé avec la valeur 'image' brute et doit
    renvoyer le href de remplacement (ou None s'il ne sait pas résoudre) ;
    s'il est absent (ou renvoie None), ExpressionPivotNonEcrite est levée
    plutôt que d'écrire un href silencieusement inutilisable."""
    image = sym.get("image")
    if isinstance(image, dict):
        raise ExpressionPivotNonEcrite(
            f"{contexte} : IconSymbolizer.image sous forme Sprite (sprite sheet) non écrit "
            f"par cette itération — seule une image simple (chemin/URL, str) l'est."
        )
    if image is None:
        raise ExpressionPivotNonEcrite(f"{contexte} : IconSymbolizer sans image (image=None).")
    if isinstance(image, str) and image.lower().startswith("base64:"):
        resolu = resoudre_image_embarquee(image) if resoudre_image_embarquee is not None else None
        if not resolu:
            raise ExpressionPivotNonEcrite(
                f"{contexte} : IconSymbolizer.image est un SVG embarqué en base64 "
                f"(convention QGIS 'base64:...', pas un chemin/URL) — cet écrivain, zéro-E/S, "
                f"ne peut pas le matérialiser en fichier lui-même. Fournir "
                f"resoudre_image_embarquee=... à ecrire_sld() (callback str -> href) pour "
                f"extraire l'image et renvoyer son chemin/URL de destination ; sans ce callback, "
                f"la chaîne base64 n'est PAS écrite telle quelle (elle produirait un href "
                f"syntaxiquement valide mais inutilisable par GeoServer)."
            )
        image = resolu
    fmt = sym.get("format") or "image/svg+xml"
    if fmt not in _FORMATS_ICON_ECRITS:
        raise ExpressionPivotNonEcrite(
            f"{contexte} : IconSymbolizer.format={fmt!r} non écrit par cette itération — "
            f"vérifié contre l'oracle PyQGIS (QgsVectorLayer.loadSldStyle() + rendu pixel) que "
            f"seul 'image/svg+xml' est correctement importé par QGIS 3.40 ; 'image/png' "
            f"(syntaxe identique, fichier valide) échoue silencieusement au chargement — voir "
            f"le registre _FORMATS_ICON_ECRITS dans le module."
        )
    couleur = sym.get("color")
    if couleur is not None and not isinstance(couleur, str):
        # Jamais produit par le lecteur QML actuel (toujours un hex litteral
        # via couleur_qgis_vers_hex — voir readers.qml._lire_icone_image),
        # mais ce module ne doit pas construire un href invalide pour un cas
        # pivot inattendu : avertissement explicite plutot qu'un crash ou une
        # substitution silencieusement ignoree.
        avertissements.append(
            f"{contexte} : IconSymbolizer.color={couleur!r} n'est pas une chaîne "
            f"hexadécimale littérale — paramètre SVG 'fill' (GeoServer, Parametric "
            f"SVG) NON ajouté à l'href, le pictogramme restera dans sa couleur "
            f"par défaut du fichier SVG."
        )
        couleur = None
    graphic = ET.Element(_q_sld("Graphic"))
    ext = ET.SubElement(graphic, _q_sld("ExternalGraphic"))
    resource = ET.SubElement(ext, _q_sld("OnlineResource"))
    href = _href_svg_parametrique(image, couleur)
    resource.set(f"{{{NS_XLINK}}}href", _valeur_symbolizer_litterale(href, contexte, "image"))
    fmt_el = ET.SubElement(ext, _q_sld("Format"))
    fmt_el.text = fmt
    if sym.get("opacity") is not None:
        el = ET.SubElement(graphic, _q_sld("Opacity"))
        el.text = _valeur_symbolizer_litterale(sym["opacity"], contexte, "Opacity")
        _avertir_opacity_graphic_non_verifiee(sym, avertissements, contexte, "IconSymbolizer")
    if sym.get("size") is not None:
        el = ET.SubElement(graphic, _q_sld("Size"))
        # PAS de x2 ici : IconSymbolizer.size (pivot) correspond directement,
        # de bout en bout via l'oracle (Size=28 -> layer.size()==28.0), à
        # sld:Size — contrairement à MarkSymbolizer.radius (voir _ecrire_mark) ;
        # deux propriétés pivot différentes, deux conventions vérifiées
        # séparément, pas une extrapolation de l'une à l'autre.
        el.text = _valeur_symbolizer_litterale(sym["size"], contexte, "Size")
    if sym.get("rotate") is not None:
        el = ET.SubElement(graphic, _q_sld("Rotation"))
        el.text = _valeur_symbolizer_litterale(sym["rotate"], contexte, "Rotation")
    _ajouter_displacement(graphic, sym, contexte)
    return graphic


def _ecrire_icon(
    sym: dict, avertissements: list[str], contexte: str,
    *, resoudre_image_embarquee: Callable[[str], str | None] | None = None,
) -> ET.Element:
    point = ET.Element(_q_sld("PointSymbolizer"))
    point.append(_construire_graphic_icon(
        sym, avertissements, contexte, resoudre_image_embarquee=resoudre_image_embarquee,
    ))
    _avertir_proprietes_non_gerees(
        sym,
        {"image", "format", "opacity", "size", "rotate", "offset", "color"},
        avertissements, contexte,
    )
    return point


def _construire_graphic_imbrique(
    sym_imbrique: Any, avertissements: list[str], contexte: str,
    *, resoudre_image_embarquee: Callable[[str], str | None] | None = None,
) -> ET.Element:
    """Construit un <Graphic> pour un symbolizer IMBRIQUÉ (graphicFill /
    graphicStroke du pivot, qui référencent un MarkSymbolizer, un
    IconSymbolizer ou un TextSymbolizer nu). Text n'est pas encore écrit
    comme symbolizer autonome (voir _ecrire_text) et n'est donc pas non plus
    écrit ici — pas d'incohérence entre les deux contextes."""
    sym_imbrique = _normaliser(sym_imbrique)
    kind = sym_imbrique.get("kind")
    if kind == "Mark":
        return _construire_graphic_mark(sym_imbrique, avertissements, contexte)
    if kind == "Icon":
        return _construire_graphic_icon(
            sym_imbrique, avertissements, contexte,
            resoudre_image_embarquee=resoudre_image_embarquee,
        )
    raise ExpressionPivotNonEcrite(
        f"{contexte} : symbolizer imbriqué de type {kind!r} non écrit par cette itération "
        f"(seuls Mark et Icon le sont pour graphicFill/graphicStroke — Text n'est pas non plus "
        f"écrit comme symbolizer autonome, voir la docstring de module)."
    )


#: TextSymbolizer.label (pivot) est un STRING TEMPLATE ("Nom : {{champ}}",
#: doc officielle du schéma) ou une Fxxx. Vérifié contre l'oracle (4
#: constructions distinctes testées : ogc:PropertyName nu, littéral texte nu,
#: littéral texte + PropertyName en contenu mixte, ogc:Function Concatenate) :
#: SEULE la référence de champ NUE (rien d'autre dans <Label>) produit un
#: labeling QGIS correctement peuplé (fieldName confirmé). Les 3 autres
#: échouent silencieusement : soit lyr.labeling() reste None (littéral seul,
#: Concatenate), soit — plus grave — le texte littéral entourant le champ est
#: PERDU SANS AVERTISSEMENT (contenu mixte "Nom: <PropertyName>nom</PropertyName>"
#: importé avec fieldName="nom" mais le préfixe "Nom: " disparaît). D'où une
#: restriction stricte : seul un template EXACTEMENT égal à "{{champ}}" (rien
#: avant, rien après) est écrit ; tout le reste lève ExpressionPivotNonEcrite
#: plutôt que produire un SLD qui perd silencieusement de l'information au
#: prochain import QGIS.
_MOTIF_LABEL_CHAMP_NU = re.compile(r"^\{\{([A-Za-z_][A-Za-z0-9_]*)\}\}$")


def _extraire_nom_champ_label(label: Any, contexte: str) -> str:
    if isinstance(label, dict) and label.get("name") == "property":
        args = label.get("args", [])
        if len(args) == 1:
            return str(args[0])
    if isinstance(label, str):
        m = _MOTIF_LABEL_CHAMP_NU.match(label)
        if m:
            return m.group(1)
        raise ExpressionPivotNonEcrite(
            f"{contexte} : label={label!r} n'est pas un template champ-seul (\"{{{{champ}}}}\", "
            f"rien avant/après) — vérifié contre l'oracle QGIS que tout le reste (texte littéral "
            f"seul, ou texte mélangé à un champ) échoue à produire un labeling, dans un cas en "
            f"perdant silencieusement le texte littéral entourant le champ. Voir la docstring de "
            f"_MOTIF_LABEL_CHAMP_NU."
        )
    raise ExpressionPivotNonEcrite(
        f"{contexte} : label={label!r} sous une forme Fxxx non écrite par cette itération (seul "
        f"un template \"{{{{champ}}}}\" ou un Fproperty nu l'est ; ogc:Function Concatenate, "
        f"testé contre l'oracle, échoue silencieusement à produire un labeling)."
    )


def _ecrire_text(
    sym: dict, avertissements: list[str], contexte: str,
    *, resoudre_image_embarquee: Callable[[str], str | None] | None = None,
) -> ET.Element:
    # Idem _ecrire_mark : TextSymbolizer n'a pas de propriété 'image', ignoré
    # ici sans effet — présent seulement pour l'interface commune des
    # écrivains de symbolizer.
    """TextSymbolizer -> sld:TextSymbolizer. Ne peut être écrit QUE dans une
    Rule qui contient aussi au moins un AUTRE symbolizer (Mark/Fill/Line/Icon) :
    vérifié contre l'oracle qu'une Rule ne contenant QU'un TextSymbolizer
    échoue entièrement au chargement (loadSldStyle renvoie ok=False, message
    vide) — appliqué par _ecrire_rule, pas ici (cette fonction ne voit pas
    les autres symbolizers de la Rule)."""
    texte = ET.Element(_q_sld("TextSymbolizer"))
    if sym.get("label") is None:
        raise ExpressionPivotNonEcrite(f"{contexte} : TextSymbolizer sans label (label=None).")
    champ = _extraire_nom_champ_label(sym["label"], contexte)
    label_el = ET.SubElement(texte, _q_sld("Label"))
    prop_el = ET.SubElement(label_el, _q_ogc("PropertyName"))
    prop_el.text = champ

    police = sym.get("font")
    tailles_polices_geres = ["font"]
    if any(sym.get(c) is not None for c in ("font", "size", "fontStyle", "fontWeight")):
        font_el = ET.SubElement(texte, _q_sld("Font"))
        if police is not None:
            if isinstance(police, list) and police:
                if len(police) > 1:
                    avertissements.append(
                        f"{contexte} : font={police!r} contient plusieurs familles de repli — "
                        f"seule la première ({police[0]!r}) est écrite, le mécanisme de repli "
                        f"CSS/SLD sur police manquante n'est pas vérifié pour cette itération."
                    )
                param = ET.SubElement(font_el, _q_sld("CssParameter"))
                param.set("name", "font-family")
                param.text = _valeur_symbolizer_litterale(police[0], contexte, "font-family")
            else:
                raise ExpressionPivotNonEcrite(
                    f"{contexte} : font={police!r} n'est pas une liste non vide de noms de "
                    f"police — seule cette forme est écrite par cette itération."
                )
        _definir_parametre(font_el, "font-size", sym.get("size"), contexte)
        # fontStyle/fontWeight (pivot) sont des chaînes libres, écrites telles
        # quelles : vérifié contre l'oracle pour "italic"/"bold" précisément
        # (font_italic/font_bold confirmés True) — pas vérifié pour d'autres
        # valeurs, aucune validation de vocabulaire faite ici.
        _definir_parametre(font_el, "font-style", sym.get("fontStyle"), contexte)
        _definir_parametre(font_el, "font-weight", sym.get("fontWeight"), contexte)

    if sym.get("rotate") is not None:
        rotate = _valeur_symbolizer_litterale(sym["rotate"], contexte, "rotate")
        placement = ET.SubElement(texte, _q_sld("LabelPlacement"))
        point_placement = ET.SubElement(placement, _q_sld("PointPlacement"))
        rot_el = ET.SubElement(point_placement, _q_sld("Rotation"))
        # SLD Rotation et QGIS angleOffset ont un sens opposé : vérifié sur 5
        # points (0/30/90/180/270 -> angleOffset 360/330/270/180/90, soit
        # exactement (360 - rotation) % 360 à chaque fois) — pas une
        # extrapolation d'un seul point.
        rot_el.text = str((360.0 - float(rotate)) % 360.0)

    if sym.get("color") is not None:
        remplissage = ET.SubElement(texte, _q_sld("Fill"))
        _definir_parametre(remplissage, "fill", sym.get("color"), contexte)

    if sym.get("haloWidth") is not None:
        # Halo/Radius -> buffer(enabled,size) confirmé 1:1 (Radius=3 ->
        # buffer_size=3.0). Halo/Fill/CssParameter fill -> buffer_color
        # confirmé également (#ffffff -> #ffffff).
        halo = ET.SubElement(texte, _q_sld("Halo"))
        rayon_el = ET.SubElement(halo, _q_sld("Radius"))
        rayon_el.text = _valeur_symbolizer_litterale(sym["haloWidth"], contexte, "Halo/Radius")
        if sym.get("haloColor") is not None:
            halo_fill = ET.SubElement(halo, _q_sld("Fill"))
            _definir_parametre(halo_fill, "fill", sym.get("haloColor"), contexte)

    _avertir_proprietes_non_gerees(
        sym,
        {"label", "font", "size", "fontStyle", "fontWeight", "rotate", "color",
         "haloWidth", "haloColor"},
        avertissements, contexte,
    )
    return texte


_ECRIVAINS_SYMBOLIZER = {
    "Mark": _ecrire_mark, "Fill": _ecrire_fill, "Line": _ecrire_line, "Icon": _ecrire_icon,
    "Text": _ecrire_text,
}


def _ecrire_symbolizer(
    sym: dict, avertissements: list[str], contexte: str,
    *, resoudre_image_embarquee: Callable[[str], str | None] | None = None,
) -> ET.Element:
    sym = _normaliser(sym)
    kind = sym.get("kind")
    ecrivain = _ECRIVAINS_SYMBOLIZER.get(kind)
    if ecrivain is None:
        raison_supplementaire = ""
        if kind == "Raster":
            # Pas une limite d'IMPORT SLD comme les autres exclusions de ce
            # module : QgsRasterLayer.loadSldStyle() lève lui-même une erreur
            # EXPLICITE ("Layer type 1 not supported") — l'API générique de
            # chargement SLD utilisée comme oracle dans tout ce module ne
            # prend simplement pas en charge les couches raster sur cette
            # version de QGIS. Rien à écrire de vérifiable ici.
            raison_supplementaire = (
                " (RasterSymbolizer : QgsRasterLayer.loadSldStyle() lève explicitement "
                "\"Layer type 1 not supported\" sur cette version de QGIS — pas une limite "
                "d'import silencieuse comme les autres exclusions, l'oracle refuse categoriquement "
                "de charger un SLD sur une couche raster, rien à vérifier de ce côté)"
            )
        raise ExpressionPivotNonEcrite(
            f"{contexte} : symbolizer de type {kind!r} non écrit par cette itération "
            f"de l'écrivain SLD (seuls Mark/Fill/Line/Icon/Text le sont — voir la docstring de "
            f"styleforge_core.writers.sld){raison_supplementaire}."
        )
    return ecrivain(sym, avertissements, contexte, resoudre_image_embarquee=resoudre_image_embarquee)


# --------------------------------------------------------------------------- filtres (pivot Filter -> ogc:Filter)
_CMP_TUPLE_VERS_OGC = {
    "==": "PropertyIsEqualTo", "!=": "PropertyIsNotEqualTo",
    "<": "PropertyIsLessThan", "<=": "PropertyIsLessThanOrEqualTo",
    ">": "PropertyIsGreaterThan", ">=": "PropertyIsGreaterThanOrEqualTo",
}
#: dict de fonction booléenne pivot (son "name") -> même table, pour les cas
#: (plus rares) où le filtre est produit en forme dict plutôt que tuple.
_CMP_DICT_VERS_OGC = {
    "equalTo": "PropertyIsEqualTo", "notEqualTo": "PropertyIsNotEqualTo",
    "lessThan": "PropertyIsLessThan", "lessThanOrEqualTo": "PropertyIsLessThanOrEqualTo",
    "greaterThan": "PropertyIsGreaterThan", "greaterThanOrEqualTo": "PropertyIsGreaterThanOrEqualTo",
}


def _motif_ogc_vers_wildcard(motif: str) -> tuple[str, str, str]:
    """Le motif produit par le lecteur pour '*=' utilise déjà la convention
    wildCard='*'/singleChar='.' (styleforge_core.readers.expressions,
    _traduire_motif_like) : on la réutilise à l'identique plutôt que d'en
    inventer une seconde, avec escapeChar='!' (valeur par défaut usuelle,
    absente du motif lecteur donc sans conflit)."""
    return motif, "*", "."


#: Caractères regex "spéciaux" au sens de re.escape() (Python >= 3.7 :
#: ponctuation ASCII seulement, plus l'espace n'est PLUS échappé depuis
#: 3.7). Tout caractère de cet ensemble rencontré NU (ni dans la paire
#: ".*", ni précédé d'un backslash) dans le corps d'une regex signale une
#: chaîne qui ne peut PAS provenir de _motif_like_vers_regex (qui échappe
#: systématiquement tout caractère de cet ensemble) : prudence, abandon.
_REGEX_SPECIAUX = frozenset("()[]{}?*+-|^$\\.&~#")


def _detecter_motif_like_depuis_regex(regex: str) -> tuple[str, bool] | None:
    """Tente de reconnaître, dans `regex`, la forme EXACTE produite par
    styleforge_core.readers.expressions._motif_like_vers_regex — seul
    producteur de strMatches dans ce projet (LIKE/ILIKE, vérifié : aucun
    autre site n'appelle _fonction("strMatches", ...) dans expressions.py ;
    regexp_match/regexp_replace/regexp_substr QGIS, qui pourraient produire
    une regex arbitraire, sont explicitement NON traduits par le lecteur —
    voir sa docstring — donc jamais une source de strMatches ici).

    Cette forme canonique est : "(?i)"? "^" (".*" | "." | caractère
    re.escape()-é)* "$" — où ".*" vient d'un joker SQL '%', "." d'un '_',
    et tout le reste d'un caractère littéral échappé par re.escape().

    Retourne (motif_sql_like, insensible_a_la_casse) si `regex` correspond
    EXACTEMENT à cette forme, sinon None (jamais une approximation sur une
    forme non reconnue — l'appelant doit alors garder l'exception nommée
    existante plutôt que deviner)."""
    insensible = regex.startswith("(?i)")
    corps = regex[4:] if insensible else regex
    if not (corps.startswith("^") and corps.endswith("$") and len(corps) >= 2):
        return None
    corps = corps[1:-1]
    motif: list[str] = []
    i, n = 0, len(corps)
    while i < n:
        c = corps[i]
        if c == "\\":
            if i + 1 >= n:
                return None  # backslash isolé en fin de chaîne : pas notre forme
            motif.append(corps[i + 1])
            i += 2
        elif corps[i:i + 2] == ".*":
            motif.append("%")
            i += 2
        elif c == ".":
            motif.append("_")
            i += 1
        elif c in _REGEX_SPECIAUX:
            return None  # métacaractère nu hors des trois cas gérés ci-dessus
        else:
            motif.append(c)
            i += 1
    return "".join(motif), insensible


def _construire_filtre(filtre: Any, avertissements: list[str], contexte: str) -> ET.Element:
    filtre = _normaliser(filtre)
    if isinstance(filtre, list):
        op = filtre[0]
        if op in _CMP_TUPLE_VERS_OGC:
            if len(filtre) != 3:
                raise ExpressionPivotNonEcrite(
                    f"{contexte} : comparaison {filtre!r} attend 3 éléments (opérateur, "
                    f"gauche, droite), {len(filtre)} reçus."
                )
            el = ET.Element(_q_ogc(_CMP_TUPLE_VERS_OGC[op]))
            el.append(_construire_element_valeur(filtre[1]))
            el.append(_construire_element_valeur(filtre[2]))
            return el
        if op == "&&":
            el = ET.Element(_q_ogc("And"))
            for f in filtre[1:]:
                el.append(_construire_filtre(f, avertissements, contexte))
            return el
        if op == "||":
            el = ET.Element(_q_ogc("Or"))
            for f in filtre[1:]:
                el.append(_construire_filtre(f, avertissements, contexte))
            return el
        if op == "!":
            el = ET.Element(_q_ogc("Not"))
            el.append(_construire_filtre(filtre[1], avertissements, contexte))
            return el
        if op == "*=":
            if len(filtre) != 3:
                raise ExpressionPivotNonEcrite(f"{contexte} : '*=' attend 3 éléments, {len(filtre)} reçus.")
            motif, joker, car_unique = _motif_ogc_vers_wildcard(filtre[2])
            el = ET.Element(_q_ogc("PropertyIsLike"))
            el.set("wildCard", joker)
            el.set("singleChar", car_unique)
            el.set("escapeChar", "!")
            el.append(_construire_element_valeur(filtre[1]))
            lit = ET.SubElement(el, _q_ogc("Literal"))
            lit.text = motif
            return el
        raise ExpressionPivotNonEcrite(
            f"{contexte} : opérateur de filtre tuple {op!r} non écrit par cette itération de "
            f"l'écrivain SLD. Note : BETWEEN n'a PAS de forme tuple dans le schéma "
            f"geostyler-style (seule Fbetween en forme dict {{'name':'between',...}} existe, "
            f"gérée plus bas) ; une correction d'une hypothèse d'itération précédente, qui "
            f"supposait à tort une forme tuple 'min<=x<=max' inexistante."
        )
    if isinstance(filtre, dict) and "name" in filtre:
        nom = filtre["name"]
        args = filtre.get("args", [])
        if nom in ("equalTo", "notEqualTo") and len(args) == 2 and args[1] is None:
            base = ET.Element(_q_ogc("PropertyIsNull"))
            base.append(_construire_element_valeur(args[0]))
            if nom == "notEqualTo":
                non = ET.Element(_q_ogc("Not"))
                non.append(base)
                return non
            return base
        if nom in _CMP_DICT_VERS_OGC:
            if len(args) != 2:
                raise ExpressionPivotNonEcrite(f"{contexte} : {nom}(...) attend 2 arguments, {len(args)} reçus.")
            el = ET.Element(_q_ogc(_CMP_DICT_VERS_OGC[nom]))
            el.append(_construire_element_valeur(args[0]))
            el.append(_construire_element_valeur(args[1]))
            return el
        if nom == "all":
            el = ET.Element(_q_ogc("And"))
            for f in args:
                el.append(_construire_filtre(f, avertissements, contexte))
            return el
        if nom == "any":
            el = ET.Element(_q_ogc("Or"))
            for f in args:
                el.append(_construire_filtre(f, avertissements, contexte))
            return el
        if nom == "not":
            el = ET.Element(_q_ogc("Not"))
            el.append(_construire_filtre(args[0], avertissements, contexte))
            return el
        if nom == "between":
            # Fbetween pivot = {"name": "between", "args": [valeur, min, max]},
            # exactement 3 arguments (schéma : minItems=maxItems=3), sémantique
            # "min <= valeur <= max" (docstring officielle geostyler-style).
            # ogc:PropertyIsBetween EST un opérateur OGC Filter natif standard
            # (contrairement à ce qu'une itération précédente de ce module
            # supposait par erreur, voir la docstring de module) — vérifié
            # contre l'oracle PyQGIS : rule.filterExpression() reconstruit
            # exactement "x >= 10 AND x <= 20" pour PropertyIsBetween(x,10,20).
            if len(args) != 3:
                raise ExpressionPivotNonEcrite(
                    f"{contexte} : between(...) attend exactement 3 arguments "
                    f"(valeur, min, max), {len(args)} reçus."
                )
            valeur, mini, maxi = args
            el = ET.Element(_q_ogc("PropertyIsBetween"))
            el.append(_construire_element_valeur(valeur))
            borne_min = ET.SubElement(el, _q_ogc("LowerBoundary"))
            borne_min.append(_construire_element_valeur(mini))
            borne_max = ET.SubElement(el, _q_ogc("UpperBoundary"))
            borne_max.append(_construire_element_valeur(maxi))
            return el
        if nom == "in":
            if len(args) < 2:
                raise ExpressionPivotNonEcrite(f"{contexte} : in(...) attend au moins 2 arguments (propriété, valeur...).")
            operande, *valeurs = args
            # Aucun opérateur OGC Filter natif pour IN : reconstruit comme
            # Or(PropertyIsEqualTo(operande, v1), PropertyIsEqualTo(operande, v2), ...)
            # — équivalent logique exact, pas une approximation.
            el = ET.Element(_q_ogc("Or"))
            for v in valeurs:
                cmp_el = ET.SubElement(el, _q_ogc("PropertyIsEqualTo"))
                cmp_el.append(_construire_element_valeur(operande))
                cmp_el.append(_construire_element_valeur(v))
            return el
        if nom == "strMatches":
            if len(args) != 2:
                raise ExpressionPivotNonEcrite(f"{contexte} : strMatches(...) attend 2 arguments, {len(args)} reçus.")
            operande, regex = args
            detecte = _detecter_motif_like_depuis_regex(regex) if isinstance(regex, str) else None
            if detecte is None:
                raise ExpressionPivotNonEcrite(
                    f"{contexte} : strMatches(..., {regex!r}) non écrit — cette regex ne "
                    f"correspond pas à la forme canonique que produit LIKE/ILIKE dans ce "
                    f"projet (styleforge_core.readers.expressions._motif_like_vers_regex), "
                    f"seule reconvertible sans supposition vers ogc:PropertyIsLike. Un "
                    f"strMatches construit autrement (ex. regexp_match QGIS, non traduit "
                    f"par le lecteur) n'a pas de correspondance OGC Filter standard pour "
                    f"une sémantique regex générale."
                )
            motif, insensible = detecte
            # wildCard="%"/singleChar="_"/escape="\" : vérifié à l'oracle QGIS,
            # PAS supposé — QgsVectorLayer.saveSldStyle() sur une couche avec un
            # filtre ILIKE natif produit EXACTEMENT ces trois attributs (et
            # matchCase="false" pour ILIKE, absent pour LIKE), et le document
            # SLD construit à la main avec ces attributs round-trippe par
            # loadSldStyle() vers filterExpression() == "idass ILIKE 'a1%'"
            # (vérifié le 2026-10-12, voir le rapport d'accompagnement).
            el = ET.Element(_q_ogc("PropertyIsLike"))
            el.set("wildCard", "%")
            el.set("singleChar", "_")
            el.set("escape", "\\")
            if insensible:
                el.set("matchCase", "false")
            el.append(_construire_element_valeur(operande))
            lit = ET.SubElement(el, _q_ogc("Literal"))
            lit.text = motif
            return el
        raise ExpressionPivotNonEcrite(
            f"{contexte} : fonction booléenne pivot {nom!r} non écrite par cette "
            f"itération de l'écrivain SLD (strMatches/ILIKE notamment : aucune "
            f"correspondance OGC Filter standard vérifiée pour une sémantique "
            f"regex — voir la docstring de styleforge_core.writers.sld)."
        )
    raise ExpressionPivotNonEcrite(f"{contexte} : forme de filtre pivot non reconnue : {filtre!r}")


# --------------------------------------------------------------------------- rule / style
def _ecrire_scale(el_rule: ET.Element, scale: dict | None, contexte: str) -> None:
    if not scale:
        return
    for cle, tag in (("min", "MinScaleDenominator"), ("max", "MaxScaleDenominator")):
        v = scale.get(cle)
        if v is None:
            continue
        if isinstance(v, dict):
            raise ExpressionPivotNonEcrite(
                f"{contexte} : scaleDenominator.{cle} piloté par expression, non "
                f"écrit par cette itération (seul un littéral numérique l'est)."
            )
        el = ET.SubElement(el_rule, _q_sld(tag))
        el.text = str(v)


def _ecrire_rule(
    rule: dict, index: int, avertissements: list[str],
    *, resoudre_image_embarquee: Callable[[str], str | None] | None = None,
) -> ET.Element:
    rule = _normaliser(rule)
    contexte = f"Rule[{index}] ({rule.get('name') or 'sans nom'})"
    el = ET.Element(_q_sld("Rule"))
    if rule.get("name"):
        nom = ET.SubElement(el, _q_sld("Name"))
        nom.text = str(rule["name"])
    if rule.get("elseRule"):
        ET.SubElement(el, _q_sld("ElseFilter"))
    elif rule.get("filter") is not None:
        filtre_el = ET.SubElement(el, _q_ogc("Filter"))
        filtre_el.append(_construire_filtre(rule["filter"], avertissements, contexte))
    _ecrire_scale(el, rule.get("scaleDenominator"), contexte)
    symbolizers = rule.get("symbolizers") or []
    kinds = [_normaliser(s).get("kind") for s in symbolizers]
    if "Text" in kinds and all(k == "Text" for k in kinds):
        # Vérifié contre l'oracle : une Rule qui ne contient QU'un ou des
        # TextSymbolizer échoue ENTIÈREMENT au chargement (loadSldStyle
        # renvoie ok=False, message vide) — pas seulement le TextSymbolizer
        # qui serait ignoré, toute la Rule. Ajouter un Mark/Fill/Line/Icon
        # dans la même Rule suffit à la faire réussir (vérifié également).
        raise ExpressionPivotNonEcrite(
            f"{contexte} : ne contient que des TextSymbolizer, aucun autre symbolizer — vérifié "
            f"contre l'oracle QGIS qu'une Rule composée uniquement de TextSymbolizer échoue "
            f"ENTIÈREMENT au chargement SLD (pas seulement le texte : toute la Rule). Il faut au "
            f"moins un symbolizer Mark/Fill/Line/Icon en plus dans la même Rule."
        )
    for i, sym in enumerate(symbolizers):
        el.append(_ecrire_symbolizer(
            sym, avertissements, f"{contexte}.symbolizers[{i}]",
            resoudre_image_embarquee=resoudre_image_embarquee,
        ))
    return el


def ecrire_sld(
    style: Any, *, nom_couche: str = "layer", avertissements: list[str] | None = None,
    resoudre_image_embarquee: Callable[[str], str | None] | None = None,
) -> str:
    """Traduit un Style pivot (dict canonique validé par valider_style(), ou
    instance pydantic du modèle généré) en un document SLD 1.0.0 complet
    (str). Lève ExpressionPivotNonEcrite si une Rule, un filtre ou une
    propriété de symbolizer sort de la portée bornée décrite en tête de
    module. 'avertissements' peut être fourni pour récupérer les propriétés
    de symbolizer non écrites (voir _avertir_proprietes_non_gerees) — jamais
    perdues en silence, seulement omises du document avec une trace.

    'resoudre_image_embarquee' : callback optionnel (str -> str | None) pour
    résoudre un IconSymbolizer.image qui est un SVG embarqué en base64
    (convention QGIS 'base64:...' — cas du lecteur QML SLYR/CNIG notamment)
    plutôt qu'un chemin/URL. Cet écrivain reste zéro-E/S : il NE décode NI
    n'écrit ce contenu lui-même. S'il rencontre une telle valeur SANS que ce
    callback soit fourni (ou si le callback renvoie None), ExpressionPivotNonEcrite
    est levée — voir _construire_graphic_icon — plutôt que d'écrire un href
    'base64:...' syntaxiquement valide mais inutilisable par GeoServer."""
    style = _normaliser(style)
    avertissements = avertissements if avertissements is not None else []

    racine = ET.Element(_q_sld("StyledLayerDescriptor"))
    racine.set("version", "1.0.0")
    racine.set(f"{{{NS_XSI}}}schemaLocation",
               f"{NS_SLD} http://schemas.opengis.net/sld/1.0.0/StyledLayerDescriptor.xsd")

    named_layer = ET.SubElement(racine, _q_sld("NamedLayer"))
    nom_el = ET.SubElement(named_layer, _q_sld("Name"))
    nom_el.text = nom_couche

    user_style = ET.SubElement(named_layer, _q_sld("UserStyle"))
    if style.get("name"):
        titre = ET.SubElement(user_style, _q_sld("Title"))
        titre.text = str(style["name"])

    fts = ET.SubElement(user_style, _q_sld("FeatureTypeStyle"))
    for i, rule in enumerate(style.get("rules") or []):
        fts.append(_ecrire_rule(
            rule, i, avertissements, resoudre_image_embarquee=resoudre_image_embarquee,
        ))

    brut = ET.tostring(racine, encoding="unicode")
    joli = minidom.parseString(brut).toprettyxml(indent="  ")
    # minidom insère une ligne XML-declaration par défaut ; on la remplace
    # par une version UTF-8 explicite et on retire les lignes blanches
    # superflues qu'il ajoute entre les éléments.
    lignes = [l for l in joli.splitlines() if l.strip()]
    lignes[0] = '<?xml version="1.0" encoding="UTF-8"?>'
    return "\n".join(lignes) + "\n"
