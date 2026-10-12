#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
styleforge_core.readers.qml — Lecteur QML générique : transforme un fichier
.qml QGIS en pivot TYPÉ (styleforge_core.pivot.Style), sans dépendre de
PyQGIS (§ principe directeur du projet : QGIS = oracle de test, jamais
dépendance d'exécution — plan §6.2).

Ce module succède au prototype pivot_properties.py (racine du dépôt, outil
du niveau 2 de la pyramide de test) : il en reprend le bas niveau (analyse
XML, contournement du piège des couches <layer> de secours du profil
altimétrique — voir la docstring de pivot_properties.py) mais va plus loin
sur trois points que le prototype ne traitait pas :

  1. il couvre plusieurs TYPES DE RENDU (pas seulement singleSymbol) ;
  2. il produit directement un pivot TYPÉ et VALIDÉ (styleforge_core.pivot.Style),
     pas un dict libre ;
  3. il traite explicitement (jamais en silence) les propriétés pilotées par
     une expression QGIS (data_defined_properties).

Portée assumée de cette version (voir REGISTRE_RENDERERS, REGISTRE_COUCHES et
REGISTRE_COUCHES_RECURSIVES ci-dessous, et les rapports d'accompagnement — la
couverture des couches de symbole a été étendue deux fois après la version
initiale, cf. rapports dédiés) :
  - types de rendu couverts : singleSymbol, categorizedSymbol, graduatedSymbol,
    RuleRenderer, nullSymbol (les 5 dont le modèle "liste de Rule" de
    geostyler-style peut restituer le sens exactement) ;
  - classes de couche de symbole couvertes (19) : SimpleMarker, SimpleLine,
    SimpleFill, EllipseMarker (cf. styleforge_core.compat.ellipse) pour le
    noyau "couleur plate" d'origine ; FilledLine, FilledMarker, RasterMarker,
    AnimatedMarker, SvgMarker, RasterFill, RasterLine, FontMarker pour les
    couches image/icône/glyphe (IconSymbolizer, graphicFill/graphicStroke,
    ou wellKnownName='ttf://...') — ces 12 dans REGISTRE_COUCHES ; et
    CentroidFill, MarkerLine, HashLine, LinePatternFill, PointPatternFill,
    GeometryGenerator (cas triviaux), ArrowLine (approximation actée) dans
    REGISTRE_COUCHES_RECURSIVES, pour les classes COMPOSITES dont l'apparence
    réelle vient d'un <symbol> imbriqué (sous-symbole), lu récursivement par
    _lire_sous_symbole() en rappelant ce même pipeline. Les classes hors des
    deux registres ne sont pas simplement omises : RAISONS_HORS_PERIMETRE
    documente, pour chacune, la raison précise de son exclusion — vérifiée
    contre le schéma geostyler-style et le corpus réel, pas supposée
    (sous-symbole sans équivalent statique, dégradé qui ne peut pas être
    précalculé indépendamment de la géométrie, concept sans fonction
    correspondante dans le vocabulaire du pivot...) ;
  - expressions QGIS (propriétés pilotées par expression ET filtres de
    RuleRenderer) traduites via styleforge_core.readers.expressions : un
    traducteur GÉNÉRAL mais délibérément BORNÉ (grammaire complète —
    arithmétique, comparaisons, AND/OR/NOT, IS [NOT] NULL, [NOT] LIKE,
    [NOT] ILIKE, [NOT] IN, if(...) —, mais un registre de FONCTIONS
    nommées volontairement petit : 35 fonctions QGIS/387 au total, mesurées
    par mesurer_couverture_expressions_generales.py contre le même oracle
    que le niveau 3 historique ; la comparaison honnête n'est pas /387 mais
    /70, le sous-ensemble qui a une chance d'avoir un équivalent pivot
    scalaire une fois retirés TOUS les groupes structurellement hors
    périmètre (géométrie, agrégats, dates, tableaux, fichiers, rasters,
    formulaires, mise en page, capteurs... — 59 fonctions supplémentaires
    reclassées après un second passage motivé par le constat que le
    dénominateur /129 gonflait artificiellement les groupes Arrays/Files/
    Rasters/etc., jamais couvrables par CE pivot ; cf. la docstring de ce
    module et de mesurer_couverture_expressions_generales.py pour le détail
    vérifié de chaque groupe). Remplace les deux traducteurs minimaux d'une version
    antérieure (référence de champ nue seule ; comparaison simple seule),
    conservés uniquement comme chemin rapide pour le cas le plus fréquent.
    IS [NOT] NULL et ILIKE, écartés à tort lors d'un premier essai (la
    forme TUPLE d'une comparaison à None est bien rejetée par le modèle
    pivot généré ici, vérifié contre valider_style()), sont couverts via
    la forme DICT équivalente (FequalTo/FnotEqualTo pour NULL, FstrMatches
    avec préfixe (?i) pour ILIKE) — voir expressions.py pour la
    vérification détaillée.

Chacune de ces limites est un registre extensible (dict au niveau module,
avec une fonction enregistrer_*), pas une liste fermée codée en dur :
ajouter une classe de couche ou un type de rendu ne demande pas de modifier
la logique d'orchestration, seulement d'enregistrer un nouveau traducteur.
Ce qui n'est pas dans un registre échoue de façon explicite et nommée
(RendererNonSupporte, CoucheDeSymboleNonSupportee) plutôt que de produire un
pivot silencieusement incomplet — exactement le défaut que le typage du
pivot (extra="forbid", cf. pivot/_base.py) a été construit pour intercepter
côté écriture ; ce lecteur applique la même discipline côté lecture.
"""
from __future__ import annotations

import math
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from typing import Any, Callable, Literal

from styleforge_core.compat import ellipse as _ellipse
from styleforge_core.pivot import Style, valider_style
from styleforge_core.readers.expressions import ExpressionQGISNonTraduite
from styleforge_core.readers.expressions import traduire_filtre as _traduire_filtre_general
from styleforge_core.readers.expressions import traduire_valeur as _traduire_valeur_general


# --------------------------------------------------------------------------- exceptions
class ErreurLectureQML(Exception):
    """Racine commune des erreurs de lecture QML. Jamais levée telle quelle :
    toujours une des sous-classes ci-dessous, pour que l'appelant puisse
    distinguer un document mal formé d'un cas simplement hors périmètre."""


class DocumentQMLInvalide(ErreurLectureQML):
    """XML mal formé, ou structure de base (renderer-v2, symbols) absente."""


class RendererNonSupporte(ErreurLectureQML):
    """Le type de rendu (attribut type= de renderer-v2) n'a pas de traducteur
    enregistré dans REGISTRE_RENDERERS."""


class CoucheDeSymboleNonSupportee(ErreurLectureQML):
    """La classe de couche de symbole (attribut class= de <layer>) n'a pas de
    traducteur enregistré dans REGISTRE_COUCHES."""


class ProprieteExpressionNonTraduite(ErreurLectureQML):
    """Une propriété pilotée par une expression QGIS n'a pas pu être traduite
    automatiquement (seule la référence de champ nue l'est — voir la
    docstring du module). Levée uniquement quand
    sur_expression_non_traduite="lever" (le défaut) ; sinon, un avertissement
    est ajouté à LectureResultat.avertissements et la valeur littérale
    statique déjà lue est conservée."""


class FiltreQGISNonTraduit(ErreurLectureQML):
    """L'expression de filtre d'une RuleRenderer (ou une expression de
    catégorie/plage complexe) dépasse ce que le traducteur minimal de ce
    module sait reconnaître (comparaison simple champ/littéral)."""


class UniteNonConvertible(ErreurLectureQML):
    """L'unité QML (ex. Percentage) ne peut pas être convertie vers les deux
    seules unités que geostyler-style connaît (m, px) sans information de
    contexte supplémentaire (voir convertir_taille)."""


# --------------------------------------------------------------------------- résultat
@dataclass
class LectureResultat:
    """Ce que retourne lire_fichier_qml : le pivot validé, PLUS tout ce qui a
    dû être simplifié, approximé ou dégradé pour y arriver. Ne jamais jeter
    ces avertissements : un pivot syntaxiquement valide mais qui a perdu de
    l'information en silence reproduirait exactement le défaut que ce projet
    a été lancé pour corriger (cf. bridge-style, graphicFillDistance/Margin)."""

    style: Style
    avertissements: list[str] = field(default_factory=list)


# --------------------------------------------------------------------------- XML bas niveau
# Ces trois fonctions sont volontairement dupliquées, pas importées, depuis
# pivot_properties.py (racine du dépôt) : ce dernier est l'outil du niveau 2
# de la pyramide de test, livré et vérifié indépendamment — styleforge_core
# (le paquet distribué) ne doit pas dépendre au runtime d'un script qui vit
# hors du paquet. Les deux copies restent petites et stables (analyse d'un
# format XML figé, celui que QGIS écrit) ; en cas de divergence future,
# n'ajuster qu'ici.

def _defaire_espace_de_noms(racine: ET.Element) -> None:
    """Voir pivot_properties.py::_defaire_espace_de_noms — même correctif
    (un xmlns par défaut sur la racine qualifie chaque balise et casse les
    recherches par nom nu), même justification (niveau 4, robustesse XML)."""
    for el in racine.iter():
        if isinstance(el.tag, str) and el.tag.startswith("{"):
            el.tag = el.tag.split("}", 1)[1]


def _parse_option_map(el: ET.Element) -> dict[str, Any]:
    """Voir pivot_properties.py::_parse_option_map — restitue un <Option
    type="Map"> comme un dict plat {nom: valeur}, tel que QGIS le ferait via
    QgsSymbolLayer.properties()."""
    resultat: dict[str, Any] = {}
    for enfant in el:
        if enfant.tag != "Option":
            continue
        nom = enfant.get("name")
        type_ = enfant.get("type")
        if nom is None:
            continue
        if type_ == "Map":
            resultat[nom] = _parse_option_map(enfant)
        elif type_ == "List":
            resultat[nom] = [c.get("value") for c in enfant if c.tag == "Option"]
        elif "value" in enfant.attrib:
            resultat[nom] = enfant.get("value")
    return resultat


def _lire_proprietes_dd(layer_el: ET.Element) -> dict[str, dict[str, str]]:
    """Lit le <data_defined_properties> propre à une <layer> (frère de son
    <Option type="Map">, distinct du <data-defined-properties> — avec
    tiret — porté par le <symbol> englobant, qui pilote des propriétés du
    renderer, pas de la couche). Retourne {cle_dd: {"active", "expression",
    "type"}} uniquement pour les propriétés réellement actives."""
    ddp_el = layer_el.find("data_defined_properties")
    if ddp_el is None:
        return {}
    props_el = ddp_el.find("./Option[@type='Map']/Option[@name='properties']")
    if props_el is None or props_el.get("type") != "Map":
        return {}
    resultat: dict[str, dict[str, str]] = {}
    for enfant in props_el:
        if enfant.tag != "Option" or enfant.get("type") != "Map":
            continue
        cle = enfant.get("name")
        if cle is None:
            continue
        detail = {c.get("name"): c.get("value") for c in enfant if c.tag == "Option"}
        if detail.get("active") in ("true", "1"):
            resultat[cle] = detail
    return resultat


# --------------------------------------------------------------------------- couleur / unité
def couleur_qgis_vers_hex(valeur: str) -> tuple[str, float]:
    """"r,g,b,a[,rgb:...]" (format QgsSymbolLayerUtils::encodeColor) ->
    ("#rrggbb", opacite 0..1). La composante rgb: (fractions 0..1, présente
    depuis QGIS 3.x pour la précision) est ignorée : les 4 premiers entiers
    0..255 sont la représentation faisant autorité pour un export vers un
    format tiers (SLD/MBStyle n'ont pas de notion de précision étendue)."""
    parties = valeur.split(",")
    if len(parties) < 3:
        raise DocumentQMLInvalide(f"couleur QML non reconnue : {valeur!r}")
    try:
        r, g, b = (int(parties[i]) for i in range(3))
        a = int(parties[3]) if len(parties) > 3 and parties[3].strip().isdigit() else 255
    except ValueError as e:
        raise DocumentQMLInvalide(f"couleur QML non reconnue : {valeur!r}") from e
    return f"#{r:02x}{g:02x}{b:02x}", round(a / 255, 4)


def _lire_trait_qgis(
    props: dict[str, str], *, cle_couleur: str, cle_largeur: str,
    classe: str, chemin_source: str, avertissements: list[str],
    cle_style: str = "outline_style", largeur_defaut: float | None = None,
) -> tuple[str, float, float]:
    """Lit un trait/contour QGIS (couleur hex, opacité 0..1, largeur) pour une
    classe de couche donnée. Deux cas neutralisent le trait (couleur noire,
    opacité 0, largeur 0) plutôt que de parser littéralement <cle_couleur> :

    (1) <cle_style> == 'no' (Qt::NoPen, cf. QgsSymbolLayerUtils::
    decodePenStyle) : QGIS ne dessine alors AUCUN trait quelle que soit sa
    couleur — interprétation EXACTE, pas une approximation (convention
    Qt::PenStyle bien établie, mais non re-vérifiée contre un rendu QGIS réel
    dans cette session, oracle injoignable ici), donc PAS d'avertissement
    (au même titre qu'une <layer> désactivée, déjà filtrée sans avertissement
    ailleurs dans ce module).

    (2) <cle_couleur> est une chaîne vide alors que <cle_style> ne vaut PAS
    'no' (soit un autre style, soit absent — ex. FontMarker qui n'a pas de
    outline_style du tout). Observé sur le corpus réel (SUP/ASSIETTE_SUP_S) :
    ni Qt::NoPen ni une couleur RGBA valide ne l'expliquent avec certitude
    (un cas a même outline_style='solid' avec outline_color='' — donnée
    QGIS dégénérée, pas une convention documentée) ; une chaîne vide n'est de
    toute façon jamais un encodage QGIS valide (couleur_qgis_vers_hex
    lèverait). Traité comme trait absent PAR HYPOTHÈSE, avec avertissement
    explicite car c'est une approximation non certaine, non vérifiée contre
    un rendu QGIS réel."""
    style = props.get(cle_style)
    couleur_brute = props.get(cle_couleur, "0,0,0,255")
    if style == "no":
        return "#000000", 0.0, 0.0
    if not couleur_brute.strip():
        avertissements.append(
            f"{chemin_source} [{classe}] : {cle_couleur} vide alors que "
            f"{cle_style}={style!r} — trait neutralisé par hypothèse (couleur "
            f"noire, opacité 0, largeur 0) plutôt que d'interpréter "
            f"littéralement une valeur vide ; hypothèse non vérifiée contre "
            f"un rendu QGIS réel (oracle injoignable dans cette session)."
        )
        return "#000000", 0.0, 0.0
    hex_, opacite = couleur_qgis_vers_hex(couleur_brute)
    largeur = (
        float(props[cle_largeur]) if largeur_defaut is None
        else float(props.get(cle_largeur, largeur_defaut))
    )
    return hex_, opacite, largeur


#: geostyler-style 13.0.0 ne connaît que deux unités de taille : le mètre-sol
#: ("m") et le pixel-écran ("px") — cf. schemas/geostyler-style.13.0.0.schema.json,
#: MarkSymbolizer.radiusUnit / LineSymbolizer.widthUnit. Les unités QML
#: physiques (MM, Point, Inch) n'ont pas d'équivalent direct : ce ne sont pas
#: des unités-sol ni des unités-écran mais des unités "papier à une échelle
#: d'impression donnée". Les convertir vers "px" suppose une résolution
#: (DPI) : un PARAMÈTRE (dpi=...), jamais une valeur supposée, avec
#: avertissement explicite plutôt que conversion silencieuse.
UNITES_DIRECTES: dict[str, Literal["m", "px"]] = {
    "Pixel": "px",
    "MapUnit": "m",
}
#: Facteur de conversion vers le pouce (base commune) pour les unités
#: physiques dont on ne sait produire un équivalent px qu'en supposant un DPI.
POUCES_PAR_UNITE_PHYSIQUE = {
    "MM": 1 / 25.4,
    "Point": 1 / 72.0,
    "Inch": 1.0,
}


def convertir_taille(
    valeur: float,
    unite_qml: str,
    avertissements: list[str],
    *,
    contexte: str,
    dpi: float = 90.0,
) -> tuple[float, Literal["m", "px"]]:
    """Convertit une taille QML (valeur + unité) vers ce que geostyler-style
    accepte. `dpi` est un PARAMÈTRE (évolutif — voir docstring du module) :
    sa valeur par défaut (90) est celle que QGIS lui-même utilise pour cette
    conversion dans son propre export SLD natif (QgsVectorLayer.saveSldStyle),
    vérifiée empiriquement contre l'oracle QGIS le 2026-10-12 (ex. : un
    SimpleMarker size=7 Point -> <se:Size>9</se:Size>, soit ×1.25 = 90/72 ;
    un SimpleLine width=2 MM -> stroke-width=7, soit ×(90/25.4)). C'est la
    convention historique OGC SLD/SE ("pixel standard" = 1/90 pouce), pas la
    résolution écran usuelle (96) — ne pas la reconfondre. Toute conversion
    MM/Point/Inch -> px qui en dépend est signalée dans `avertissements` :
    ce n'est jamais une conversion sans perte."""
    if unite_qml in UNITES_DIRECTES:
        return valeur, UNITES_DIRECTES[unite_qml]
    if unite_qml in POUCES_PAR_UNITE_PHYSIQUE:
        pouces = valeur * POUCES_PAR_UNITE_PHYSIQUE[unite_qml]
        px = pouces * dpi
        avertissements.append(
            f"{contexte} : unité QML {unite_qml!r} convertie en pixels via "
            f"dpi={dpi} ({valeur}{unite_qml} -> {px:.3f}px) — approximation "
            f"dépendante d'une résolution supposée, pas une conversion exacte."
        )
        return px, "px"
    raise UniteNonConvertible(
        f"{contexte} : unité QML {unite_qml!r} non convertible vers les "
        f"unités geostyler-style (m, px) — ni une unité-sol/écran directe, "
        f"ni une unité physique à DPI fixe (Percentage, par ex., dépend de "
        f"la taille d'un autre symbole et n'a pas de conversion générale)."
    )


# --------------------------------------------------------------------------- expressions
_RE_CHAMP_NU = re.compile(r'^\s*"([^"]+)"\s*$')
# _RE_COMPARAISON_SIMPLE / _OPERATEURS_QGIS_VERS_GEOSTYLER (le traducteur de
# filtre minimal d'une version antérieure) ont été retirés : remplacés par
# styleforge_core.readers.expressions.traduire_filtre, appelé depuis
# traduire_filtre_qgis_simple() ci-dessous. _valeur_litterale ci-dessous
# reste utilisée séparément, par les renderers categorized/graduated (qui ne
# passent pas par une expression QGIS mais par un attribut value=/lower=/
# upper= déjà littéral).


def _valeur_litterale(brut: str) -> Any:
    """"2" -> 2 (int/float) ; "'texte'" -> "texte" ; sinon la chaîne telle
    quelle. Utilisé pour le second opérande d'une comparaison simple."""
    brut = brut.strip()
    if (brut.startswith("'") and brut.endswith("'")) or (
        brut.startswith('"') and brut.endswith('"')
    ):
        return brut[1:-1]
    try:
        return int(brut)
    except ValueError:
        pass
    try:
        return float(brut)
    except ValueError:
        return brut


def traduire_reference_champ_nue(expression: str) -> str | None:
    """"champ" -> "champ" ; toute autre expression -> None (pas de tentative
    de traduction partielle : mieux vaut ne rien traduire qu'approximer un
    if()/CASE/concaténation en une seule Fproperty trompeuse). Conservée
    telle quelle comme chemin rapide (0 analyse syntaxique) pour le cas de
    très loin le plus fréquent ; _appliquer_expressions() ne retombe sur le
    traducteur général (styleforge_core.readers.expressions) que si celle-ci
    renvoie None."""
    m = _RE_CHAMP_NU.match(expression)
    return m.group(1) if m else None


def traduire_filtre_qgis_simple(expression: str, avertissements: list[str] | None = None,
                                 chemin_source: str = "") -> list:
    """Traduit une expression de filtre QGIS (attribut filter= d'une <rule>
    de RuleRenderer) vers une valeur de type Filter geostyler-style, via le
    traducteur d'expressions général (styleforge_core.readers.expressions :
    comparaisons, AND/OR/NOT, IS [NOT] NULL, [NOT] LIKE, [NOT] IN, et les
    fonctions bornées qu'il reconnaît). Toute expression hors de cette
    grammaire (bornée délibérément, voir la docstring de ce module-là) lève
    FiltreQGISNonTraduit avec le fragment précis en cause, plutôt que d'être
    mal interprétée."""
    av = avertissements if avertissements is not None else []
    try:
        return _traduire_filtre_general(expression, avertissements=av, contexte=chemin_source)
    except ExpressionQGISNonTraduite as e:
        raise FiltreQGISNonTraduit(
            f"{chemin_source} : expression de filtre QGIS {expression!r} non "
            f"traduite — {e}"
        ) from e


# --------------------------------------------------------------------------- couches de symbole
#: DD-key QGIS (data_defined_properties) -> champ du Symbolizer geostyler-style
#: qu'elle pilote, PAR CLASSE de couche. Table volontairement petite et
#: ouverte (enregistrer_cle_dd) : construite depuis les clés effectivement
#: observées dans le corpus niveau 1 (toutes les variantes __expression
#: utilisent la clé QGIS "fillColor" — un choix du générateur de corpus, pas
#: une liste exhaustive des clés DD que QGIS peut produire).
CLES_DD_VERS_CHAMP_SYMBOLIZER: dict[str, dict[str, str]] = {
    "SimpleMarker": {"fillColor": "color", "outlineColor": "strokeColor",
                      "outlineWidth": "strokeWidth", "size": "radius", "angle": "rotate"},
    "EllipseMarker": {"fillColor": "color", "outlineColor": "strokeColor",
                       "outlineWidth": "strokeWidth", "angle": "rotate"},
    "SimpleLine": {"fillColor": "color", "strokeColor": "color",
                   "lineColor": "color", "strokeWidth": "width", "width": "width"},
    "SimpleFill": {"fillColor": "color", "outlineColor": "outlineColor",
                   "outlineWidth": "outlineWidth"},
}


def enregistrer_cle_dd(classe_couche: str, cle_dd: str, champ_symbolizer: str) -> None:
    """Point d'extension : déclare qu'une clé de propriété pilotée par
    expression (QGIS) correspond à tel champ du Symbolizer geostyler-style
    pour telle classe de couche, sans toucher au reste du lecteur."""
    CLES_DD_VERS_CHAMP_SYMBOLIZER.setdefault(classe_couche, {})[cle_dd] = champ_symbolizer


def _appliquer_expressions(
    classe: str,
    proprietes_dd: dict[str, dict[str, str]],
    champ_geostyler: dict[str, Any],
    avertissements: list[str],
    *,
    chemin_source: str,
    sur_expression_non_traduite: Literal["lever", "avertir"],
) -> None:
    """Modifie champ_geostyler en place : pour chaque propriété pilotée par
    une expression, tente la traduction "référence de champ nue" (le seul
    cas non ambigu) ; sinon lève ou avertit selon le paramètre — jamais
    d'ignorance silencieuse (voir docstring du module)."""
    table = CLES_DD_VERS_CHAMP_SYMBOLIZER.get(classe, {})
    for cle_dd, detail in proprietes_dd.items():
        expression = detail.get("expression", "")
        cible = table.get(cle_dd)
        if cible is None:
            message = (
                f"{chemin_source} [{classe}] : propriété pilotée par expression "
                f"'{cle_dd}' = {expression!r} non traduite automatiquement "
                f"(aucun champ Symbolizer connu pour cette clé DD) — valeur "
                f"statique conservée pour {cle_dd!r}."
            )
            if sur_expression_non_traduite == "lever":
                raise ProprieteExpressionNonTraduite(message)
            avertissements.append(message)
            continue
        champ_nu = traduire_reference_champ_nue(expression)
        if champ_nu is not None:
            champ_geostyler[cible] = {"name": "property", "args": [champ_nu]}
            continue
        try:
            champ_geostyler[cible] = _traduire_valeur_general(
                expression, avertissements=avertissements,
                contexte=f"{chemin_source} [{classe}].{cle_dd}",
            )
            continue
        except ExpressionQGISNonTraduite as e:
            message = (
                f"{chemin_source} [{classe}] : propriété pilotée par expression "
                f"'{cle_dd}' = {expression!r} non traduite automatiquement "
                f"(expression hors de la grammaire bornée du traducteur — {e}) "
                f"— valeur statique conservée pour {cible!r}."
            )
            if sur_expression_non_traduite == "lever":
                raise ProprieteExpressionNonTraduite(message) from e
            avertissements.append(message)


def _lire_decalage_qgis(props: dict[str, str]) -> dict[str, Any]:
    """Lit la propriété QML "offset" (paire "x,y", ex. "0,3" ou "0,-3.7798"),
    commune aux couches marqueur (SimpleMarker, EllipseMarker, RasterMarker/
    AnimatedMarker/SvgMarker) — MarkSymbolizer.offset et IconSymbolizer.offset
    existent tous deux dans le schéma geostyler-style (vérifié), donc
    factorisé ici plutôt que dupliqué par couche. Découvert manquant (comme
    LineSymbolizer.perpendicularOffset, voir _lire_simple_line) en comparant
    contre l'oracle QGIS sur plu_psc_p.qml (PSC-P_15-00_001, offset SvgMarker
    "0,3" Point silencieusement perdu). Omis si (0,0) : c'est la valeur par
    défaut QML (aucun décalage), l'écrire ajouterait un élément SLD inutile.
    Retourne {} si absent/nul, sinon {"offset": [x, y], "_unite_decalage": ...}
    à fusionner dans le dict Symbolizer (converti ensuite par
    _convertir_tailles_symbolizer, pas ici — pas de dpi disponible à ce
    point de l'appel). Clé "_unite_decalage" (pas "_unite_offset") pour ne
    PAS entrer en collision avec celle, homonyme en apparence mais distincte,
    de LineSymbolizer.perpendicularOffset (_lire_simple_line) — un champ
    scalaire différent, sur un kind différent ("Line"), jamais présent sur
    le même dict que ce champ "offset" en liste (kind "Mark"/"Icon")."""
    brut = props.get("offset")
    if not brut:
        return {}
    parties = brut.split(",")
    if len(parties) != 2:
        return {}
    x, y = float(parties[0]), float(parties[1])
    if x == 0 and y == 0:
        return {}
    return {"offset": [x, y], "_unite_decalage": props.get("offset_unit", "MM")}


def _lire_simple_marker(
    props: dict[str, str], avertissements: list[str], chemin_source: str,
) -> dict[str, Any]:
    hex_, opacite = couleur_qgis_vers_hex(props["color"])
    hex_ol, opacite_ol, largeur_ol = _lire_trait_qgis(
        props, cle_couleur="outline_color", cle_largeur="outline_width",
        classe="SimpleMarker", chemin_source=chemin_source, avertissements=avertissements,
    )
    return {
        "kind": "Mark",
        "wellKnownName": props["name"],  # validé par le pivot (enum WellKnownName)
        "color": hex_,
        "fillOpacity": opacite,
        "radius": float(props["size"]) / 2,  # scale_method=diameter chez QGIS
        "strokeColor": hex_ol,
        "strokeOpacity": opacite_ol,
        "strokeWidth": largeur_ol,
        "rotate": float(props.get("angle", 0)),
        "_unite_taille": props.get("size_unit", "MM"),
        "_unite_trait": props.get("outline_width_unit", "MM"),
        **_lire_decalage_qgis(props),
    }


def _lire_ellipse_marker(props: dict[str, str], avertissements: list[str], chemin_source: str) -> dict[str, Any]:
    symbol_name = props.get("symbol_name", "circle")
    largeur = float(props["symbol_width"])
    hauteur = float(props["symbol_height"])
    try:
        approx = _ellipse.approximer(symbol_name, largeur, hauteur)
    except ValueError as e:
        raise CoucheDeSymboleNonSupportee(f"{chemin_source} : {e}") from e
    if approx.perte:
        avertissements.append(
            f"{chemin_source} [EllipseMarker] : forme approximée par "
            f"WellKnownName={approx.well_known_name!r} (décision retenue, cf. "
            f"styleforge_core.compat.ellipse) — symbol_width={largeur}, "
            f"symbol_height={hauteur} -> radius={approx.radius} "
            f"(stratégie {approx.strategie!r}). Information de forme réelle perdue."
        )
    hex_, opacite = couleur_qgis_vers_hex(props["color"])
    hex_ol, opacite_ol, largeur_ol = _lire_trait_qgis(
        props, cle_couleur="outline_color", cle_largeur="outline_width",
        classe="EllipseMarker", chemin_source=chemin_source, avertissements=avertissements,
    )
    return {
        "kind": "Mark",
        "wellKnownName": approx.well_known_name,
        "color": hex_,
        "fillOpacity": opacite,
        "radius": approx.radius,
        "strokeColor": hex_ol,
        "strokeOpacity": opacite_ol,
        "strokeWidth": largeur_ol,
        "rotate": float(props.get("angle", 0)),
        "_unite_taille": props.get("symbol_width_unit", "MM"),
        "_unite_trait": props.get("outline_width_unit", "MM"),
        **_lire_decalage_qgis(props),
    }


_CAPSTYLE_QGIS_VERS_GEOSTYLER = {"square": "square", "round": "round", "flat": "butt"}


def _lire_simple_line(props: dict[str, str]) -> dict[str, Any]:
    hex_, opacite = couleur_qgis_vers_hex(props["line_color"])
    resultat: dict[str, Any] = {
        "kind": "Line",
        "color": hex_,
        "opacity": opacite,
        "width": float(props["line_width"]),
        "cap": _CAPSTYLE_QGIS_VERS_GEOSTYLER.get(props.get("capstyle", "square"), "square"),
        "join": props.get("joinstyle", "bevel"),
        "_unite_taille": props.get("line_width_unit", "MM"),
    }
    if props.get("use_custom_dash") == "1" and props.get("customdash"):
        resultat["dasharray"] = [float(x) for x in props["customdash"].split(";") if x]
        resultat["dashOffset"] = float(props.get("dash_pattern_offset", 0))
        # customdash_unit / dash_pattern_offset_unit sont des unités QML
        # PROPRES à ces deux champs, indépendantes de line_width_unit même
        # si elles coïncident le plus souvent dans le corpus (vérifié sur
        # psmv_zone_urba.qml : customdash_unit="Point" mais
        # dash_pattern_offset_unit="MM") — les lire par convenance depuis
        # line_width_unit serait une approximation silencieuse si elles
        # diffèrent. Converties par _convertir_tailles_symbolizer, pas ici
        # (pas de dpi disponible à ce point de l'appel).
        resultat["_unite_dasharray"] = props.get("customdash_unit", "MM")
        resultat["_unite_dash_offset"] = props.get("dash_pattern_offset_unit", "MM")
    # offset QML ("decalage perpendiculaire a la ligne, cote gauche si >0")
    # -> LineSymbolizer.perpendicularOffset du pivot (présent dans le schéma
    # geostyler-style, vérifié) — découvert manquant en comparant contre
    # l'oracle QGIS (QgsVectorLayer.saveSldStyle() natif) sur
    # plu_zone_urba_ge.qml : un symbole Fill à deux couches SimpleLine y
    # simule un double-liseré via deux offsets différents (3pt et 0), perdu
    # jusqu'ici sans même un avertissement puisque cette propriété n'était
    # pas lue du tout (donc jamais vue par _avertir_proprietes_non_gerees
    # côté écrivain). Omis si nul : 0 est la valeur par défaut QML (aucun
    # décalage), l'écrire ajouterait un élément SLD inutile sans rien
    # représenter de plus.
    if float(props.get("offset", 0)) != 0:
        resultat["perpendicularOffset"] = float(props["offset"])
        resultat["_unite_offset"] = props.get("offset_unit", "MM")
    return resultat


def _lire_simple_fill(
    props: dict[str, str], avertissements: list[str], chemin_source: str,
) -> dict[str, Any]:
    hex_, opacite = couleur_qgis_vers_hex(props["color"])
    hex_ol, opacite_ol, largeur_ol = _lire_trait_qgis(
        props, cle_couleur="outline_color", cle_largeur="outline_width",
        classe="SimpleFill", chemin_source=chemin_source, avertissements=avertissements,
    )
    return {
        "kind": "Fill",
        "color": hex_,
        "fillOpacity": opacite,
        "outlineColor": hex_ol,
        "outlineOpacity": opacite_ol,
        "outlineWidth": largeur_ol,
        "_unite_taille": props.get("outline_width_unit", "MM"),
    }


#: classe de couche QGIS -> fonction(props) -> dict Symbolizer geostyler-style
#: (avant conversion d'unité et application des expressions, faites par
#: l'appelant). Registre ouvert : enregistrer_lecteur_couche() pour étendre
#: sans modifier ce module. Les classes composites (sous-symbole imbriqué)
#: sont dans REGISTRE_COUCHES_RECURSIVES, pas ici. Les classes hors des deux
#: registres sont un échec explicite (CoucheDeSymboleNonSupportee), jamais un
#: symbolizer par défaut trompeur. Cette version en couvre 12 ici (les 4
#: couches "couleur plate" d'origine, plus 7 couches image/icône, plus
#: FontMarker) et 7 dans REGISTRE_COUCHES_RECURSIVES — cf. rapport
#: d'accompagnement de la deuxième extension de couverture pour le détail.
#: Les classes restantes du corpus, examinées et sciemment laissées hors
#: registre pour une raison précise, sont documentées dans
#: RAISONS_HORS_PERIMETRE ci-dessous plutôt que simplement omises.
REGISTRE_COUCHES: dict[str, Callable[..., dict[str, Any]]] = {
    "SimpleMarker": lambda props, av, src: _lire_simple_marker(props, av, src),
    "EllipseMarker": lambda props, av, src: _lire_ellipse_marker(props, av, src),
    "SimpleLine": lambda props, av, src: _lire_simple_line(props),
    "SimpleFill": lambda props, av, src: _lire_simple_fill(props, av, src),
    "FilledLine": lambda props, av, src: _lire_filled_line(props),
    "FilledMarker": lambda props, av, src: _lire_filled_marker(props),
    "RasterMarker": lambda props, av, src: _lire_icone_image(
        props, av, src, cle_image="imageFile"),
    "AnimatedMarker": lambda props, av, src: _lire_icone_image(
        props, av, src, cle_image="imageFile", avertir_frame_rate=True),
    "SvgMarker": lambda props, av, src: _lire_icone_image(
        props, av, src, cle_image="name", avec_couleur=True),
    "RasterFill": lambda props, av, src: _lire_raster_fill(props, av, src),
    "RasterLine": lambda props, av, src: _lire_raster_line(props, av, src),
    "FontMarker": lambda props, av, src: _lire_font_marker(props, av, src),
}


def enregistrer_lecteur_couche(classe: str, fonction: Callable[..., dict[str, Any]]) -> None:
    """Point d'extension : ajoute (ou remplace) le traducteur d'une classe de
    couche de symbole QGIS, sans modifier la logique d'orchestration de ce
    module. `fonction(proprietes, avertissements, chemin_source) -> dict`
    doit renvoyer un dict prêt à valider contre le Symbolizer geostyler-style
    correspondant (clés '_unite_taille'/'_unite_trait' facultatives, retirées
    après conversion par le lecteur)."""
    REGISTRE_COUCHES[classe] = fonction


_CHAMPS_TAILLE_PAR_KIND = {
    "Mark": [("radius", "radiusUnit", "_unite_taille"),
             ("strokeWidth", "strokeWidthUnit", "_unite_trait")],
    "Line": [("width", "widthUnit", "_unite_taille"),
             ("spacing", "spacingUnit", "_unite_espacement")],
    "Fill": [("outlineWidth", "outlineWidthUnit", "_unite_taille")],
    "Icon": [("size", "sizeUnit", "_unite_taille")],
}

#: classe de couche -> raison SPÉCIFIQUE de son exclusion, quand elle est
#: connue et vaut la peine d'être dite (plutôt que le message générique
#: "non couverte par ce lecteur"). Une couche listée ici a été EXAMINÉE,
#: pas simplement oubliée — voir la docstring de chaque cas pour le détail.
RAISONS_HORS_PERIMETRE: dict[str, str] = {
    "MaskMarker": (
        "MaskMarker ne dessine rien par lui-même : c'est une couche de "
        "masquage (elle découpe/masque les couches sous-jacentes selon une "
        "forme de marqueur). Aucun Symbolizer geostyler-style ne représente "
        "cette opération — ce n'est pas un cas non traité, c'est un concept "
        "sans équivalent dans le pivot."
    ),
    "RandomMarkerFill": (
        "Un sous-symbole imbriqué porte la couleur/forme réelle (comme pour "
        "CentroidFill/PointPatternFill, couverts), mais le PLACEMENT ici est "
        "un nombre de points aléatoires par polygone : ni le pivot geostyler-"
        "style (Frandom n'est qu'un scalaire, pas un générateur de points "
        "aléatoires dans une géométrie) ni SLD/MBStyle standard n'ont de "
        "primitif pour ça — vérifié dans le schéma du pivot, pas supposé."
    ),
    "GradientFill": (
        "Remplissage en dégradé continu (color1/color2/rampType) : "
        "geostyler-style n'a pas de FillSymbolizer à dégradé. Une "
        "rasterisation en image statique ne résout PAS le problème (piste "
        "initialement envisagée puis écartée) : graphicFill RÉPÈTE une "
        "tuile de taille fixe sur toute la surface (comme pour "
        "RasterFill/PointPatternFill) plutôt que d'étirer une image sur "
        "l'étendue du polygone — un dégradé rasterisé y apparaîtrait comme "
        "un motif de bandes répété, pas comme un dégradé continu unique. "
        "Voir le document de consignes utilisateur QGIS pour l'alternative "
        "recommandée."
    ),
    "ShapeburstFill": (
        "Même famille que GradientFill, avec une limite supplémentaire : le "
        "dégradé dépend de la distance au bord DU POLYGONE (max_distance), "
        "donc de sa forme et sa taille propres — même une rasterisation "
        "hypothétique ne pourrait pas être précalculée une fois pour toutes "
        "les géométries, à la différence d'un dégradé directionnel simple."
    ),
    "Lineburst": (
        "Même famille que GradientFill, appliquée à une ligne plutôt qu'un "
        "remplissage."
    ),
    "GeometryGenerator": (
        "Couche composite (sous-symbole imbriqué) *partiellement* couverte : "
        "REGISTRE_COUCHES_RECURSIVES traduit les deux cas triviaux reconnus "
        "dans le corpus, geometryModifier='@geometry' (identité) et "
        "'centroid($geometry)' (comme CentroidFill) — cf. "
        "_lire_geometry_generator(). Cette entrée ne s'applique qu'au CAS "
        "GÉNÉRAL, une expression QGIS arbitraire, qui demanderait un "
        "traducteur d'expressions généraliste explicitement hors périmètre "
        "de ce lecteur (cf. docstring du module) ; _lire_geometry_generator() "
        "lève elle-même CoucheDeSymboleNonSupportee avec le modificateur "
        "concerné dans ce cas, ce message générique ne devrait donc "
        "normalement pas être vu pour cette classe."
    ),
    "VectorField": (
        "Dessine, pour chaque entité, un SEGMENT DE LONGUEUR ET DIRECTION "
        "VARIABLES (calculées depuis x_attribute/y_attribute) — vérifié sur "
        "le corpus : son sous-symbole est une LIGNE, pas un marqueur "
        "orientable. Ni le pivot geostyler-style ni SLD/MBStyle standard "
        "n'ont de fonction de construction de géométrie (aucune fonction du "
        "type 'segment depuis un point, une direction et une magnitude' "
        "dans le vocabulaire de fonctions du pivot, vérifié dans le "
        "schéma) : contrairement à une hypothèse initialement avancée pour "
        "cette classe, l'approximer par un MarkSymbolizer orienté (rotate/"
        "size calculés) changerait la nature même du rendu (icône statique "
        "au lieu d'un vecteur dessiné), pas une simple perte de fidélité."
    ),
    "LinearReferencing": (
        "Combine un habillage numérique (numeric_format) et textuel "
        "(text_format, un QgsTextFormat complet) le long d'une ligne — plus "
        "proche d'un TextSymbolizer avec repères géométriques que d'un "
        "LineSymbolizer simple ; hors périmètre de cette version."
    ),
    "InterpolatedLine": (
        "À RECONSIDÉRER (moins fermé qu'initialement estimé) : les "
        "fonctions Finterpolate/Fstep du pivot (vérifiées dans le schéma) "
        "peuvent piloter directement 'color'/'width' depuis un attribut, "
        "sans passer par plusieurs Rule comme envisagé au premier passage — "
        "reste néanmoins hors registre pour l'instant, faute d'avoir "
        "construit et vérifié cette traduction contre le corpus."
    ),
}


def _convertir_tailles_symbolizer(
    dico: dict[str, Any], chemin_source: str, etiquette: str,
    avertissements: list[str], dpi: float,
) -> None:
    """Convertit en place les champs de taille d'UN dict Symbolizer (top-
    niveau ou imbriqué, ex. le IconSymbolizer d'un graphicFill/graphicStroke)
    selon son 'kind', via _CHAMPS_TAILLE_PAR_KIND — factorisé pour être
    appliqué aussi bien au symbolizer principal qu'à un symbolizer imbriqué
    sans dupliquer la logique de conversion elle-même."""
    for nom_champ, nom_champ_unite, cle_unite in _CHAMPS_TAILLE_PAR_KIND.get(dico.get("kind"), []):
        unite_brute = dico.pop(cle_unite, None)
        if unite_brute is None or nom_champ not in dico:
            continue
        valeur_convertie, unite_geostyler = convertir_taille(
            dico[nom_champ], unite_brute, avertissements,
            contexte=f"{chemin_source} [{etiquette}].{nom_champ}", dpi=dpi,
        )
        dico[nom_champ] = valeur_convertie
        dico[nom_champ_unite] = unite_geostyler

    # dasharray : liste de longueurs (ex. SimpleLine.customdash), convertie
    # ÉLÉMENT PAR ÉLÉMENT dans SA PROPRE unité QML (_unite_dasharray), et
    # dashOffset dans LA SIENNE (_unite_dash_offset) — toutes deux
    # indépendantes de celle de 'width' même si elles coïncident le plus
    # souvent dans le corpus (cf. commentaire dans _lire_simple_line). Pas
    # dans _CHAMPS_TAILLE_PAR_KIND car ce dict suppose un champ SCALAIRE
    # avec UNE seule unité par kind ; dasharray est une liste et peut porter
    # une unité différente de 'width' sur le MÊME symbolizer "Line".
    unite_dasharray = dico.pop("_unite_dasharray", None)
    if unite_dasharray is not None and dico.get("dasharray"):
        dico["dasharray"] = [
            convertir_taille(
                valeur, unite_dasharray, avertissements,
                contexte=f"{chemin_source} [{etiquette}].dasharray", dpi=dpi,
            )[0]
            for valeur in dico["dasharray"]
        ]
    unite_dash_offset = dico.pop("_unite_dash_offset", None)
    if unite_dash_offset is not None and "dashOffset" in dico:
        dico["dashOffset"], _ = convertir_taille(
            dico["dashOffset"], unite_dash_offset, avertissements,
            contexte=f"{chemin_source} [{etiquette}].dashOffset", dpi=dpi,
        )

    # perpendicularOffset (LineSymbolizer, SimpleLine.offset) : champ
    # scalaire SANS variante "...Unit" dans le schéma geostyler-style
    # (vérifié : perpendicularOffset y est juste "number", contrairement à
    # width/widthUnit) — valeur convertie en px mais pas de second champ
    # d'unité à écrire, donc pas dans _CHAMPS_TAILLE_PAR_KIND (qui suppose
    # toujours une paire valeur/unité).
    unite_offset = dico.pop("_unite_offset", None)
    if unite_offset is not None and "perpendicularOffset" in dico:
        dico["perpendicularOffset"], _ = convertir_taille(
            dico["perpendicularOffset"], unite_offset, avertissements,
            contexte=f"{chemin_source} [{etiquette}].perpendicularOffset", dpi=dpi,
        )

    # offset (MarkSymbolizer/IconSymbolizer, QGIS "x,y" sur une couche
    # marqueur) : liste [x, y] convertie COMPOSANTE PAR COMPOSANTE dans sa
    # PROPRE unité QML (offset_unit) — même famille de bug que dasharray/
    # perpendicularOffset ci-dessus, découverte sur IconSymbolizer (SvgMarker
    # de plu_psc_p.qml) mais la lecture (_lire_decalage_qgis) est partagée
    # avec MarkSymbolizer (SimpleMarker/EllipseMarker). Vérifié contre
    # l'oracle QGIS (QgsVectorLayer.loadSldStyle() sur un SLD construit à la
    # main) que <Graphic><Displacement><DisplacementX/><DisplacementY/></Displacement></Graphic>
    # est bien repris, sur un Mark COMME sur un ExternalGraphic, en
    # symbolLayer.offset() — pas de second champ d'unité à écrire (comme
    # perpendicularOffset), d'où la clé "_unite_decalage" distincte au lieu
    # d'être dans _CHAMPS_TAILLE_PAR_KIND.
    unite_decalage = dico.pop("_unite_decalage", None)
    if unite_decalage is not None and dico.get("offset"):
        dico["offset"] = [
            convertir_taille(
                valeur, unite_decalage, avertissements,
                contexte=f"{chemin_source} [{etiquette}].offset", dpi=dpi,
            )[0]
            for valeur in dico["offset"]
        ]

    for cle_residuelle in [k for k in dico if k.startswith("_")]:
        del dico[cle_residuelle]


def _lire_filled_line(props: dict[str, str]) -> dict[str, Any]:
    # FilledLine a le même ÉVENTAIL de notions que SimpleLine (couleur,
    # largeur, styles de coin) mais PAS le même nom de clé pour la couleur :
    # "color" (vérifié sur le corpus, symbol_layers/Line/FilledLine.qml),
    # pas "line_color" comme SimpleLine — une délégation directe à
    # _lire_simple_line lèverait KeyError. Pas de use_custom_dash/customdash
    # dans ses propriétés QGIS (vérifié sur le corpus) : pas de motif de
    # tirets pour cette classe. Son remplissage réel (l'intérieur du ruban)
    # passe par un sous-symbole de remplissage imbriqué non lu par cette
    # version (cf. RAISONS_HORS_PERIMETRE pour les couches comparables).
    hex_, opacite = couleur_qgis_vers_hex(props["color"])
    return {
        "kind": "Line",
        "color": hex_,
        "opacity": opacite,
        "width": float(props["line_width"]),
        "cap": _CAPSTYLE_QGIS_VERS_GEOSTYLER.get(props.get("capstyle", "square"), "square"),
        "join": props.get("joinstyle", "bevel"),
        "_unite_taille": props.get("line_width_unit", "MM"),
    }


def _lire_filled_marker(props: dict[str, str]) -> dict[str, Any]:
    # FilledMarker n'a pas de outline_color/outline_width propres (son
    # contour vient d'un sous-symbole de remplissage imbriqué, non lu) :
    # à la différence de _lire_simple_marker, aucun champ de trait n'est
    # produit plutôt que d'en inventer un par défaut trompeur.
    hex_, opacite = couleur_qgis_vers_hex(props["color"])
    return {
        "kind": "Mark",
        "wellKnownName": props["name"],
        "color": hex_,
        "fillOpacity": opacite,
        "radius": float(props["size"]) / 2,
        "rotate": float(props.get("angle", 0)),
        "_unite_taille": props.get("size_unit", "MM"),
    }


def _lire_icone_image(
    props: dict[str, str], avertissements: list[str], chemin_source: str,
    *, cle_image: str, avec_couleur: bool = False, avertir_frame_rate: bool = False,
) -> dict[str, Any]:
    """Traducteur commun pour les couches marqueur pilotées par une image
    externe (RasterMarker, AnimatedMarker) ou un fichier SVG (SvgMarker) :
    toutes trois partagent le même squelette IconSymbolizer (image, taille,
    rotation, opacité), et diffèrent seulement par la clé du chemin d'image
    et la présence ou non d'une couleur de substitution."""
    resultat: dict[str, Any] = {
        "kind": "Icon",
        "rotate": float(props.get("angle", 0)),
        "opacity": float(props.get("alpha", 1)),
        "_unite_taille": props.get("size_unit", "MM"),
        **_lire_decalage_qgis(props),
    }
    image = props.get(cle_image)
    if image:
        resultat["image"] = image
    if props.get("size"):
        resultat["size"] = float(props["size"])
    if avec_couleur and props.get("color"):
        hex_, _ = couleur_qgis_vers_hex(props["color"])
        resultat["color"] = hex_
    if avec_couleur and (props.get("outline_color") or props.get("outline_width")):
        avertissements.append(
            f"{chemin_source} : outline_color/outline_width non représentables "
            f"par IconSymbolizer (pas de champ de trait séparé) — non traduits."
        )
    if avec_couleur and props.get("parameters") not in (None, "", "{}"):
        avertissements.append(
            f"{chemin_source} : substitution de paramètres SVG (parameters) "
            f"non traduite."
        )
    if avertir_frame_rate and props.get("frameRate") not in (None, ""):
        avertissements.append(
            f"{chemin_source} : frameRate (fréquence d'animation) non "
            f"représentable par IconSymbolizer — non traduit (image statique)."
        )
    return resultat


def _lire_raster_fill(props: dict[str, str], avertissements: list[str], chemin_source: str) -> dict[str, Any]:
    # RasterFill n'a pas d'équivalent FillSymbolizer direct (remplissage par
    # texture) : approximé via graphicFill, le mécanisme geostyler-style
    # dédié aux remplissages par motif répété (accepte un IconSymbolizer).
    icone: dict[str, Any] = {"kind": "Icon", "opacity": float(props.get("alpha", 1))}
    if props.get("imageFile"):
        icone["image"] = props["imageFile"]
    largeur, hauteur = props.get("width"), props.get("height")
    if largeur:
        icone["size"] = float(largeur)
        icone["_unite_taille"] = props.get("width_unit", "MM")
    if largeur and hauteur and float(largeur) != float(hauteur):
        avertissements.append(
            f"{chemin_source} [RasterFill] : largeur ({largeur}) et hauteur "
            f"({hauteur}) différentes — IconSymbolizer n'a qu'une seule "
            f"taille (carrée) ; largeur retenue, hauteur ignorée."
        )
    return {"kind": "Fill", "graphicFill": icone}


def _lire_raster_line(props: dict[str, str], avertissements: list[str], chemin_source: str) -> dict[str, Any]:
    # Même approximation que RasterFill, via graphicStroke (motif répété
    # le long de la ligne) plutôt qu'une texture continue.
    icone: dict[str, Any] = {"kind": "Icon", "opacity": float(props.get("alpha", 1))}
    if props.get("imageFile"):
        icone["image"] = props["imageFile"]
    resultat: dict[str, Any] = {
        "kind": "Line",
        "graphicStroke": icone,
        "cap": _CAPSTYLE_QGIS_VERS_GEOSTYLER.get(props.get("capstyle", "square"), "square"),
        "join": props.get("joinstyle", "bevel"),
    }
    if props.get("line_width"):
        resultat["width"] = float(props["line_width"])
        resultat["_unite_taille"] = props.get("line_width_unit", "MM")
    return resultat


#: classe de couche QGIS composite -> fonction(props, avertissements,
#: chemin_source, layer_el, dpi, sur_expression_non_traduite) -> dict
#: Symbolizer. Registre séparé de REGISTRE_COUCHES parce que ces classes ont
#: besoin de bien plus que leurs propres propriétés : elles portent un
#: <symbol> imbriqué (un "sous-symbole") qui gouverne l'apparence réelle
#: (couleur/forme du marqueur ou de la ligne répétée), qu'il faut lire en
#: rappelant le même pipeline (_lire_couche, donc REGISTRE_COUCHES, la
#: conversion d'unité et les expressions) plutôt que de dupliquer cette
#: logique. Voir _lire_sous_symbole() et enregistrer_lecteur_couche_recursive().
REGISTRE_COUCHES_RECURSIVES: dict[str, Callable[..., dict[str, Any]]] = {}


def enregistrer_lecteur_couche_recursive(classe: str, fonction: Callable[..., dict[str, Any]]) -> None:
    """Point d'extension pour une classe de couche composite (sous-symbole
    imbriqué) : `fonction(proprietes, avertissements, chemin_source, layer_el,
    dpi, sur_expression_non_traduite) -> dict`. À la différence de
    enregistrer_lecteur_couche(), la fonction reçoit l'élément XML <layer>
    complet (pas seulement ses propriétés à plat) pour pouvoir en extraire le
    <symbol> imbriqué via _lire_sous_symbole()."""
    REGISTRE_COUCHES_RECURSIVES[classe] = fonction


def _lire_sous_symbole(
    layer_el: ET.Element,
    *,
    chemin_source: str,
    contexte: str,
    avertissements: list[str],
    dpi: float,
    sur_expression_non_traduite: Literal["lever", "avertir"],
) -> list[dict[str, Any]]:
    """Lit récursivement le <symbol> imbriqué directement enfant de layer_el
    (le sous-symbole d'une couche composite : CentroidFill, MarkerLine,
    HashLine, LinePatternFill, PointPatternFill, ArrowLine, GeometryGenerator),
    en rappelant _lire_couche() sur chacune de ses propres <layer> actives —
    REGISTRE_COUCHES, la conversion d'unité et les expressions s'appliquent
    donc identiquement à un sous-symbole et à une couche de premier niveau,
    sans dupliquer cette logique. Renvoie la liste des dicts Symbolizer déjà
    entièrement traités (un par <layer> active du sous-symbole)."""
    sous_symbole_el = layer_el.find("symbol")
    if sous_symbole_el is None:
        raise DocumentQMLInvalide(
            f"{chemin_source} [{contexte}] : sous-symbole imbriqué attendu, absent du QML"
        )
    couches_el = [l for l in sous_symbole_el.findall("layer") if l.get("enabled", "1") == "1"]
    if not couches_el:
        # Aucune <layer> active dans le sous-symbole imbriqué : le QML est
        # parfaitement valide (l'auteur a désactivé le contenu du sous-symbole
        # tout en laissant la couche composite elle-même active), et au même
        # titre qu'une <layer> de premier niveau désactivée (cf.
        # _lire_symbolizers, qui les filtre silencieusement — QGIS ne les
        # rend pas non plus), cette couche composite ne produit visuellement
        # rien. Averti, pas silencieux : le motif MarkerLine/HashLine/
        # LinePatternFill/PointPatternFill/ArrowLine/CentroidFill correspondant
        # disparaît du pivot, fidèlement à ce que QGIS afficherait — ce n'est
        # PAS traité comme un document invalide.
        avertissements.append(
            f"{chemin_source} [{contexte}] : sous-symbole imbriqué sans aucune "
            f"<layer> active — comme une <layer> de premier niveau désactivée, "
            f"cette couche composite ne rend rien chez QGIS ; aucun Symbolizer "
            f"produit pour elle."
        )
        return []
    resultats_bruts = [
        _lire_couche(
            l, chemin_source=f"{chemin_source} [{contexte}]",
            avertissements=avertissements, dpi=dpi,
            sur_expression_non_traduite=sur_expression_non_traduite,
        )
        for l in couches_el
    ]
    resultats = [r for r in resultats_bruts if r is not None]
    if len(resultats) < len(resultats_bruts):
        avertissements.append(
            f"{chemin_source} [{contexte}] : {len(resultats_bruts) - len(resultats)} "
            f"couche(s) imbriquée(s) active(s) mais elle(s)-même(s) sans effet visuel "
            f"(sous-symbole composite interne entièrement désactivé) ignorée(s)."
        )
    if len(resultats) > 1:
        avertissements.append(
            f"{chemin_source} [{contexte}] : sous-symbole imbriqué à {len(resultats)} "
            f"couches empilées — un Symbolizer geostyler-style n'en porte qu'une "
            f"(graphicFill/graphicStroke est singulier) : seule la première est "
            f"retenue, les {len(resultats) - 1} autres sont perdues."
        )
    return resultats


def _premier_sous_symbole(
    layer_el: ET.Element,
    *,
    chemin_source: str,
    contexte: str,
    avertissements: list[str],
    dpi: float,
    sur_expression_non_traduite: Literal["lever", "avertir"],
) -> dict[str, Any] | None:
    """Wrapper de _lire_sous_symbole() pour les 7 lecteurs de couche composite
    (CentroidFill, MarkerLine, HashLine, LinePatternFill, PointPatternFill,
    ArrowLine, GeometryGenerator) : une couche composite ne porte qu'UN seul
    sous-symbole (le premier, cf. avertissement 'couches empilées' ci-dessus),
    ou None si le sous-symbole n'a produit aucun Symbolizer (toutes ses
    <layer> désactivées, directement ou via un composite interne lui-même
    vide) — auquel cas l'appelant doit lui aussi ne produire aucun
    Symbolizer pour rester fidèle à ce que QGIS rend."""
    resultats = _lire_sous_symbole(
        layer_el, chemin_source=chemin_source, contexte=contexte,
        avertissements=avertissements, dpi=dpi,
        sur_expression_non_traduite=sur_expression_non_traduite,
    )
    return resultats[0] if resultats else None


def _lire_font_marker(props: dict[str, str], avertissements: list[str], chemin_source: str) -> dict[str, Any]:
    # FontMarker n'a pas de wellKnownName standard, mais le pivot modélise
    # déjà la convention GeoServer 'ttf://<police>#0x<point de code>' dans
    # son enum WellKnownName (vérifié dans le schéma) : construite ici depuis
    # chr (le caractère) et font (la police), pas devinée.
    caractere = props.get("chr") or ""
    police = props.get("font") or ""
    if not caractere or not police:
        raise DocumentQMLInvalide(f"{chemin_source} [FontMarker] : chr ou font absent/vide")
    point_de_code = f"0x{ord(caractere[0]):04x}"
    hex_, opacite = couleur_qgis_vers_hex(props["color"])
    # FontMarker n'a PAS de propriété outline_style (Qt::PenStyle) contrairement
    # à SimpleMarker/EllipseMarker/SimpleFill (vérifié sur le corpus réel,
    # ASSIETTE_SUP_S.qml : aucune Option name="outline_style" dans aucune de
    # ses <layer class="FontMarker">) : _lire_trait_qgis() y voit donc
    # toujours style=None (jamais 'no'), et une outline_color VIDE ('')
    # observée sur ce même corpus (avec outline_width non nul) tombe dans son
    # deuxième cas (hypothèse, avertie) plutôt que le premier (certitude,
    # silencieux).
    hex_ol, opacite_ol, largeur_ol = _lire_trait_qgis(
        props, cle_couleur="outline_color", cle_largeur="outline_width",
        classe="FontMarker", chemin_source=chemin_source, avertissements=avertissements,
        largeur_defaut=0.0,
    )
    avertissements.append(
        f"{chemin_source} [FontMarker] : traduit en wellKnownName "
        f"'ttf://{police}#{point_de_code}' — construction correcte (le point de "
        f"code vient de chr, pas deviné), mais la convention exacte de padding "
        f"hexadécimal attendue par un moteur SLD donné n'a pas été vérifiée sur un "
        f"rendu réel (aucun accès GeoServer depuis cet environnement) ; radius = "
        f"size/2 par analogie avec les autres marqueurs, alors que la sémantique "
        f"exacte de 'size' pour un glyphe de police (FontMarker n'a pas de "
        f"scale_method, à la différence de SimpleMarker) n'est pas confirmée non plus."
    )
    return {
        "kind": "Mark",
        "wellKnownName": f"ttf://{police}#{point_de_code}",
        "color": hex_,
        "fillOpacity": opacite,
        "strokeColor": hex_ol,
        "strokeOpacity": opacite_ol,
        "strokeWidth": largeur_ol,
        "radius": float(props["size"]) / 2,
        "rotate": float(props.get("angle", 0)),
        "_unite_taille": props.get("size_unit", "MM"),
        "_unite_trait": props.get("outline_width_unit", "MM"),
    }


def _lire_centroid_fill(
    props: dict[str, str], avertissements: list[str], chemin_source: str,
    layer_el: ET.Element, dpi: float, sur_expression_non_traduite: Literal["lever", "avertir"],
) -> dict[str, Any] | None:
    sous = _premier_sous_symbole(
        layer_el, chemin_source=chemin_source, contexte="CentroidFill",
        avertissements=avertissements, dpi=dpi,
        sur_expression_non_traduite=sur_expression_non_traduite,
    )
    if sous is None:
        return None
    _verifier_sous_symbole_kind(sous, "CentroidFill", chemin_source)
    resultat = dict(sous)
    resultat["geometry"] = {"name": "centroid", "args": [{"name": "property", "args": ["geometry"]}]}
    details = []
    if props.get("point_on_all_parts") not in (None, "0"):
        details.append("point_on_all_parts (un centroïde par partie de géométrie "
                        "multi-parties) non restitué — Fcentroid n'a qu'un résultat")
    if props.get("point_on_surface") not in (None, "0"):
        details.append("point_on_surface (forcer le point à l'intérieur du polygone) "
                        "non restitué — Fcentroid calcule le centroïde mathématique")
    avertissements.append(
        f"{chemin_source} [CentroidFill] : approximé par le marqueur du sous-symbole "
        f"avec geometry=centroid(...) ; le nom de colonne géométrie ('geometry') est "
        f"un espace réservé à substituer par un écrivain SLD/MBStyle, pas le nom réel "
        f"de la couche (non connu à la lecture du QML)."
        + ("".join(f" {d}." for d in details))
    )
    return resultat


_SOUS_SYMBOLE_ATTENDU_PAR_COMPOSITE = {
    # MarkerLine et PointPatternFill acceptent aussi 'Icon' : le pivot type
    # graphicStroke/graphicFill en Union[MarkSymbolizer, TextSymbolizer,
    # IconSymbolizer, None] (voir pivot/__init__.py), donc un sous-symbole
    # Icon y est structurellement légitime. C'est au lecteur de construire un
    # pivot fidèle, pas de pré-juger des limites d'un écrivain particulier :
    # l'écrivain SLD sait déjà représenter Icon sous graphicFill (via
    # QgsSVGFillSymbolLayer, vérifié à l'oracle) et refuse déjà, lui,
    # explicitement (ExpressionPivotNonEcrite, également vérifié à l'oracle :
    # QGIS retombe silencieusement sur une ligne unie) Icon sous
    # graphicStroke — ce refus doit rester au niveau de l'écrivain, pas
    # remonter artificiellement au lecteur.
    "MarkerLine": ("Mark", "Icon"), "HashLine": ("Line",), "LinePatternFill": ("Line",),
    "PointPatternFill": ("Mark", "Icon"), "ArrowLine": ("Fill",), "CentroidFill": ("Mark", "Icon"),
}


def _verifier_sous_symbole_kind(sous: dict[str, Any], contexte: str, chemin_source: str) -> None:
    attendus = _SOUS_SYMBOLE_ATTENDU_PAR_COMPOSITE[contexte]
    if sous.get("kind") not in attendus:
        attendu_txt = " ou ".join(repr(a) for a in attendus)
        raise CoucheDeSymboleNonSupportee(
            f"{chemin_source} [{contexte}] : sous-symbole de type {sous.get('kind')!r} "
            f"inattendu (un symbolizer {attendu_txt} était attendu) — non traduit."
        )


def _lire_marker_line(
    props: dict[str, str], avertissements: list[str], chemin_source: str,
    layer_el: ET.Element, dpi: float, sur_expression_non_traduite: Literal["lever", "avertir"],
) -> dict[str, Any] | None:
    sous = _premier_sous_symbole(
        layer_el, chemin_source=chemin_source, contexte="MarkerLine",
        avertissements=avertissements, dpi=dpi,
        sur_expression_non_traduite=sur_expression_non_traduite,
    )
    if sous is None:
        return None
    _verifier_sous_symbole_kind(sous, "MarkerLine", chemin_source)
    placements = props.get("placements", "Interval")
    if placements != "Interval":
        avertissements.append(
            f"{chemin_source} [MarkerLine] : placements={placements!r} approximé par "
            f"un espacement régulier — graphicStroke ne connaît que l'espacement "
            f"régulier (spacing), pas les placements QGIS aux sommets/extrémités."
        )
    resultat: dict[str, Any] = {"kind": "Line", "graphicStroke": sous}
    if props.get("interval"):
        resultat["spacing"] = float(props["interval"])
        resultat["_unite_espacement"] = props.get("interval_unit", "MM")
    return resultat


def _lire_hash_line(
    props: dict[str, str], avertissements: list[str], chemin_source: str,
    layer_el: ET.Element, dpi: float, sur_expression_non_traduite: Literal["lever", "avertir"],
) -> dict[str, Any] | None:
    sous = _premier_sous_symbole(
        layer_el, chemin_source=chemin_source, contexte="HashLine",
        avertissements=avertissements, dpi=dpi,
        sur_expression_non_traduite=sur_expression_non_traduite,
    )
    if sous is None:
        return None
    _verifier_sous_symbole_kind(sous, "HashLine", chemin_source)
    marque_hash: dict[str, Any] = {
        "kind": "Mark",
        "wellKnownName": "line",  # marque WKN "ligne" du pivot, pas la classe QGIS SimpleLine
        "strokeColor": sous.get("color", "#000000"),
        "strokeOpacity": sous.get("opacity", 1),
        "strokeWidth": sous.get("width", 1),  # déjà converti par _lire_couche sur le sous-symbole
        "rotate": float(props.get("hash_angle", 0)),
    }
    if props.get("hash_length"):
        marque_hash["radius"] = float(props["hash_length"]) / 2
        marque_hash["_unite_taille"] = props.get("hash_length_unit", "MM")
    avertissements.append(
        f"{chemin_source} [HashLine] : approximé par une marque 'line' orientée "
        f"(hash_angle/hash_length) répétée à intervalle régulier — le motif de "
        f"tirets éventuel du sous-symbole de ligne n'est pas reproduit sur le trait "
        f"perpendiculaire (customdash ignoré pour ce tiret court)."
    )
    placements = props.get("placements", "Interval")
    if placements != "Interval":
        avertissements.append(
            f"{chemin_source} [HashLine] : placements={placements!r} approximé par "
            f"un espacement régulier, comme pour MarkerLine."
        )
    resultat: dict[str, Any] = {"kind": "Line", "graphicStroke": marque_hash}
    if props.get("interval"):
        resultat["spacing"] = float(props["interval"])
        resultat["_unite_espacement"] = props.get("interval_unit", "MM")
    return resultat


#: quadrant (0..3) -> marque WKN de hachure GeoServer correspondante, et angle
#: de base de ce quadrant. Formule et correspondance reprises littéralement de
#: bridgestyle/qgis/togeostyler.py::_hatchMarkerForAngle() (cf. rapport
#: d'audit "bridge-style — Recommandations d'évolution", défaut A1) : la
#: CORRECTION apportée ici par rapport à ce code est de conserver l'écart à ce
#: quadrant comme rotation résiduelle plutôt que de l'arrondir en silence —
#: exactement le correctif que ce même rapport propose (§5.1).
_MARQUES_HACHURE = ["shape://vertline", "shape://slash", "shape://horline", "shape://backslash"]


def _hachure_marque_et_rotation_residuelle(angle: float) -> tuple[str, float]:
    quadrant = math.floor(((angle + 22.5) % 180) / 45.0)
    residuel = angle - quadrant * 45.0
    return _MARQUES_HACHURE[quadrant], residuel


def _lire_line_pattern_fill(
    props: dict[str, str], avertissements: list[str], chemin_source: str,
    layer_el: ET.Element, dpi: float, sur_expression_non_traduite: Literal["lever", "avertir"],
) -> dict[str, Any] | None:
    sous = _premier_sous_symbole(
        layer_el, chemin_source=chemin_source, contexte="LinePatternFill",
        avertissements=avertissements, dpi=dpi,
        sur_expression_non_traduite=sur_expression_non_traduite,
    )
    if sous is None:
        return None
    _verifier_sous_symbole_kind(sous, "LinePatternFill", chemin_source)
    angle = float(props.get("angle", 0))
    marque_wkn, residuel = _hachure_marque_et_rotation_residuelle(angle)
    hachure: dict[str, Any] = {
        "kind": "Mark",
        "wellKnownName": marque_wkn,
        "strokeColor": sous.get("color", "#000000"),
        "strokeOpacity": sous.get("opacity", 1),
        "strokeWidth": sous.get("width", 1),
        "rotate": residuel,
    }
    if props.get("distance"):
        # Convention GeoServer pour les marques de hachure shape://... : Size
        # contrôle l'ESPACEMENT entre hachures, pas une taille visuelle (une
        # ligne n'a pas de taille propre) — distance s'y transpose donc
        # directement via radius=size/2, sans passer par graphicFillPadding.
        hachure["radius"] = float(props["distance"]) / 2
        hachure["_unite_taille"] = props.get("distance_unit", "MM")
    if sous.get("dasharray"):
        avertissements.append(
            f"{chemin_source} [LinePatternFill] : motif de tirets du sous-symbole "
            f"non reproduit sur la hachure (une marque shape://... n'a pas de "
            f"dasharray propre)."
        )
    if props.get("offset") not in (None, "0"):
        avertissements.append(
            f"{chemin_source} [LinePatternFill] : offset={props['offset']} (décalage "
            f"du réseau de hachures) non représentable, non traduit."
        )
    return {"kind": "Fill", "graphicFill": hachure}


def _lire_point_pattern_fill(
    props: dict[str, str], avertissements: list[str], chemin_source: str,
    layer_el: ET.Element, dpi: float, sur_expression_non_traduite: Literal["lever", "avertir"],
) -> dict[str, Any] | None:
    sous = _premier_sous_symbole(
        layer_el, chemin_source=chemin_source, contexte="PointPatternFill",
        avertissements=avertissements, dpi=dpi,
        sur_expression_non_traduite=sur_expression_non_traduite,
    )
    if sous is None:
        return None
    _verifier_sous_symbole_kind(sous, "PointPatternFill", chemin_source)
    resultat: dict[str, Any] = {"kind": "Fill", "graphicFill": sous}
    dx, dy = props.get("distance_x"), props.get("distance_y")
    if dx and dy:
        # graphicFillPadding est une marge autour de chaque motif répété, pas
        # littéralement la distance QGIS entre centres — approximation
        # explicitement signalée, pas une correspondance vérifiée au pixel.
        marge_x, marge_y = max(0.0, float(dx)), max(0.0, float(dy))
        resultat["graphicFillPadding"] = [marge_y / 2, marge_x / 2, marge_y / 2, marge_x / 2]
        avertissements.append(
            f"{chemin_source} [PointPatternFill] : distance_x/distance_y approximés "
            f"via graphicFillPadding (marge autour du motif répété) — pas une "
            f"correspondance exacte à l'espacement QGIS, dépend du moteur de rendu "
            f"SLD/MBStyle final (non vérifié sur un rendu réel)."
        )
    decalage_perdu = any(props.get(k) not in (None, "0", "0.0") for k in
                         ("displacement_x", "displacement_y", "random_deviation_x", "random_deviation_y"))
    if decalage_perdu:
        avertissements.append(
            f"{chemin_source} [PointPatternFill] : décalage en quinconce ou "
            f"dispersion aléatoire (displacement_x/y, random_deviation_x/y) non "
            f"représentable par graphicFill (grille strictement régulière) — décision "
            f"actée : grille réalignée sans décalage plutôt qu'un rejet, perte assumée "
            f"et documentée ici (cf. rapport d'accompagnement)."
        )
    return resultat


_RE_GEOMETRIE_CENTROIDE = re.compile(r"^centroid\(\s*\$geometry\s*\)$", re.IGNORECASE)


def _lire_geometry_generator(
    props: dict[str, str], avertissements: list[str], chemin_source: str,
    layer_el: ET.Element, dpi: float, sur_expression_non_traduite: Literal["lever", "avertir"],
) -> dict[str, Any] | None:
    modificateur = (props.get("geometryModifier") or "").strip()
    contexte = f"GeometryGenerator({props.get('SymbolType', '?')})"
    if modificateur == "@geometry":
        # Cas trivial : la géométrie n'est PAS modifiée (@geometry référence
        # la géométrie de l'entité elle-même, inchangée) — traduction fidèle,
        # sans perte, du seul sous-symbole. Vérifié sur le corpus : les 3
        # variantes Fill/Line/Marker de GeometryGenerator n'exercent que ce cas.
        return _premier_sous_symbole(
            layer_el, chemin_source=chemin_source, contexte=contexte,
            avertissements=avertissements, dpi=dpi,
            sur_expression_non_traduite=sur_expression_non_traduite,
        )
    if _RE_GEOMETRIE_CENTROIDE.match(modificateur):
        sous = _premier_sous_symbole(
            layer_el, chemin_source=chemin_source, contexte=contexte,
            avertissements=avertissements, dpi=dpi,
            sur_expression_non_traduite=sur_expression_non_traduite,
        )
        if sous is None:
            return None
        resultat = dict(sous)
        resultat["geometry"] = {"name": "centroid", "args": [{"name": "property", "args": ["geometry"]}]}
        avertissements.append(
            f"{chemin_source} [{contexte}] : geometryModifier='centroid($geometry)' "
            f"reconnu et traduit comme CentroidFill (même réserve sur le nom de "
            f"colonne géométrie, cf. CentroidFill)."
        )
        return resultat
    raise CoucheDeSymboleNonSupportee(
        f"{chemin_source} : GeometryGenerator avec geometryModifier={modificateur!r} "
        f"non traduit — seuls les cas triviaux reconnus sont '@geometry' (identité) "
        f"et 'centroid($geometry)' ; une expression QGIS arbitraire demanderait un "
        f"traducteur d'expressions généraliste, explicitement hors périmètre de ce "
        f"lecteur (cf. docstring du module, et le rapport niveau 3 sur la couverture "
        f"de StandaloneBackend._filter)."
    )


def _lire_arrow_line(
    props: dict[str, str], avertissements: list[str], chemin_source: str,
    layer_el: ET.Element, dpi: float, sur_expression_non_traduite: Literal["lever", "avertir"],
) -> dict[str, Any] | None:
    sous = _premier_sous_symbole(
        layer_el, chemin_source=chemin_source, contexte="ArrowLine",
        avertissements=avertissements, dpi=dpi,
        sur_expression_non_traduite=sur_expression_non_traduite,
    )
    if sous is None:
        return None
    _verifier_sous_symbole_kind(sous, "ArrowLine", chemin_source)
    largeurs = [float(props[k]) for k in ("arrow_width", "arrow_start_width") if props.get(k)]
    largeur_moyenne = sum(largeurs) / len(largeurs) if largeurs else 1.0
    avertissements.append(
        f"{chemin_source} [ArrowLine] : décision actée — approximé par une ligne "
        f"pleine de largeur moyenne (arrow_width/arrow_start_width), couleur du "
        f"remplissage du sous-symbole ; la forme réelle (fuseau effilé, tête de "
        f"flèche, tracé courbe) est perdue, perte assumée et documentée ici."
    )
    return {
        "kind": "Line",
        "color": sous.get("color", "#000000"),
        "opacity": sous.get("fillOpacity", 1),
        "width": largeur_moyenne,
        "_unite_taille": props.get("arrow_width_unit", "MM"),
    }


REGISTRE_COUCHES_RECURSIVES.update({
    "CentroidFill": _lire_centroid_fill,
    "MarkerLine": _lire_marker_line,
    "HashLine": _lire_hash_line,
    "LinePatternFill": _lire_line_pattern_fill,
    "PointPatternFill": _lire_point_pattern_fill,
    "GeometryGenerator": _lire_geometry_generator,
    "ArrowLine": _lire_arrow_line,
})


def _lire_couche(
    layer_el: ET.Element,
    *,
    chemin_source: str,
    avertissements: list[str],
    dpi: float,
    sur_expression_non_traduite: Literal["lever", "avertir"],
) -> dict[str, Any] | None:
    classe = layer_el.get("class")
    if not classe:
        raise DocumentQMLInvalide(f"{chemin_source} : <layer> sans attribut class")
    traducteur = REGISTRE_COUCHES.get(classe)
    traducteur_recursif = None if traducteur is not None else REGISTRE_COUCHES_RECURSIVES.get(classe)
    if traducteur is None and traducteur_recursif is None:
        raison_connue = RAISONS_HORS_PERIMETRE.get(classe)
        raise CoucheDeSymboleNonSupportee(
            f"{chemin_source} : classe de couche de symbole {classe!r} non "
            f"couverte par ce lecteur"
            + (f" — {raison_connue}" if raison_connue else
               f" (registre : {sorted(set(REGISTRE_COUCHES) | set(REGISTRE_COUCHES_RECURSIVES))}). "
               f"Voir enregistrer_lecteur_couche() pour l'ajouter.")
        )
    option_map = layer_el.find("./Option[@type='Map']")
    proprietes = _parse_option_map(option_map) if option_map is not None else {}
    try:
        if traducteur_recursif is not None:
            champ_geostyler = traducteur_recursif(
                proprietes, avertissements, chemin_source, layer_el, dpi, sur_expression_non_traduite,
            )
        else:
            champ_geostyler = traducteur(proprietes, avertissements, chemin_source)
    except KeyError as e:
        raise DocumentQMLInvalide(
            f"{chemin_source} [{classe}] : propriété attendue absente : {e}"
        ) from e

    if champ_geostyler is None:
        # Couche composite (traducteur récursif) dont le sous-symbole imbriqué
        # ne produit visuellement rien (cf. _lire_sous_symbole/
        # _premier_sous_symbole) : aucun Symbolizer à produire pour cette
        # <layer> non plus, y compris ses éventuelles propriétés pilotées par
        # expression (moot si la couche elle-même ne rend rien).
        return None

    _convertir_tailles_symbolizer(champ_geostyler, chemin_source, classe, avertissements, dpi)
    for cle_imbriquee in ("graphicFill", "graphicStroke"):
        if isinstance(champ_geostyler.get(cle_imbriquee), dict):
            _convertir_tailles_symbolizer(
                champ_geostyler[cle_imbriquee], chemin_source,
                f"{classe}.{cle_imbriquee}", avertissements, dpi)

    proprietes_dd = _lire_proprietes_dd(layer_el)
    if proprietes_dd:
        _appliquer_expressions(
            classe, proprietes_dd, champ_geostyler, avertissements,
            chemin_source=chemin_source,
            sur_expression_non_traduite=sur_expression_non_traduite,
        )
    return champ_geostyler


def _lire_symbolizers(
    symbol_el: ET.Element,
    *,
    chemin_source: str,
    avertissements: list[str],
    dpi: float,
    sur_expression_non_traduite: Literal["lever", "avertir"],
) -> list[dict[str, Any]]:
    couches_el = symbol_el.findall("layer")
    if not couches_el:
        raise DocumentQMLInvalide(f"{chemin_source} : <symbol> sans <layer>")
    resultats = [
        _lire_couche(
            layer_el, chemin_source=chemin_source, avertissements=avertissements,
            dpi=dpi, sur_expression_non_traduite=sur_expression_non_traduite,
        )
        for layer_el in couches_el
        if layer_el.get("enabled", "1") == "1"
    ]
    # Une <layer> composite active (MarkerLine, PointPatternFill, ...) dont le
    # sous-symbole imbriqué ne rend visuellement rien (toutes ses propres
    # <layer> désactivées) revient à _lire_couche() = None : filtrée ici, pas
    # différemment d'une <layer> désactivée au premier niveau (déjà exclue
    # ci-dessus par le filtre enabled="1").
    return [r for r in resultats if r is not None]


# --------------------------------------------------------------------------- renderers
def _index_symboles(renderer_el: ET.Element) -> dict[str, ET.Element]:
    return {s.get("name"): s for s in renderer_el.findall("symbols/symbol")}


def _rule_depuis_symbole(
    symbole_el: ET.Element, nom: str, filtre: list | None,
    *, chemin_source: str, avertissements: list[str], dpi: float,
    sur_expression_non_traduite: Literal["lever", "avertir"],
) -> dict[str, Any]:
    rule: dict[str, Any] = {
        "name": nom,
        "symbolizers": _lire_symbolizers(
            symbole_el, chemin_source=chemin_source, avertissements=avertissements,
            dpi=dpi, sur_expression_non_traduite=sur_expression_non_traduite,
        ),
    }
    if filtre is not None:
        rule["filter"] = filtre
    return rule


def _renderer_single_symbol(renderer_el: ET.Element, ctx: dict) -> list[dict]:
    symboles = renderer_el.findall("symbols/symbol")
    if not symboles:
        raise DocumentQMLInvalide(f"{ctx['chemin_source']} : aucun <symbol> sous renderer-v2/symbols")
    return [_rule_depuis_symbole(symboles[0], "règle unique", None, **ctx)]


def _renderer_categorized_symbol(renderer_el: ET.Element, ctx: dict) -> list[dict]:
    attr = renderer_el.get("attr")
    if not attr:
        raise DocumentQMLInvalide(f"{ctx['chemin_source']} : categorizedSymbol sans attribut attr=")
    index = _index_symboles(renderer_el)
    rules = []
    for cat in renderer_el.findall("categories/category"):
        if cat.get("render") == "false":
            continue
        symbole_el = index.get(cat.get("symbol"))
        if symbole_el is None:
            raise DocumentQMLInvalide(
                f"{ctx['chemin_source']} : category référence le symbole "
                f"{cat.get('symbol')!r}, absent de <symbols>")
        valeur = _valeur_litterale(cat.get("value", ""))
        filtre = ["==", {"name": "property", "args": [attr]}, valeur]
        rules.append(_rule_depuis_symbole(
            symbole_el, cat.get("label") or f"{attr}={valeur}", filtre, **ctx))
    return rules


def _renderer_graduated_symbol(renderer_el: ET.Element, ctx: dict) -> list[dict]:
    attr = renderer_el.get("attr")
    if not attr:
        raise DocumentQMLInvalide(f"{ctx['chemin_source']} : graduatedSymbol sans attribut attr=")
    index = _index_symboles(renderer_el)
    rules = []
    for rng in renderer_el.findall("ranges/range"):
        if rng.get("render") == "false":
            continue
        symbole_el = index.get(rng.get("symbol"))
        if symbole_el is None:
            raise DocumentQMLInvalide(
                f"{ctx['chemin_source']} : range référence le symbole "
                f"{rng.get('symbol')!r}, absent de <symbols>")
        borne_inf, borne_sup = float(rng.get("lower")), float(rng.get("upper"))
        filtre = [
            "&&",
            [">=", {"name": "property", "args": [attr]}, borne_inf],
            ["<=" if rng is renderer_el.findall("ranges/range")[-1] else "<",
             {"name": "property", "args": [attr]}, borne_sup],
        ]
        rules.append(_rule_depuis_symbole(
            symbole_el, rng.get("label") or f"{borne_inf}-{borne_sup}", filtre, **ctx))
    return rules


def _renderer_rule_renderer(renderer_el: ET.Element, ctx: dict) -> list[dict]:
    index = _index_symboles(renderer_el)
    rules_el = renderer_el.find("rules")
    if rules_el is None:
        raise DocumentQMLInvalide(f"{ctx['chemin_source']} : RuleRenderer sans <rules>")
    rules = []
    for rule_el in rules_el.findall("rule"):
        symbole_el = index.get(rule_el.get("symbol"))
        if symbole_el is None:
            # Une <rule> sans symbole (groupe de règles imbriquées) n'a pas
            # d'équivalent Rule geostyler-style à plat : hors périmètre,
            # signalé nommément plutôt qu'ignoré.
            raise FiltreQGISNonTraduit(
                f"{ctx['chemin_source']} : <rule label={rule_el.get('label')!r}> "
                f"sans symbole propre (règle groupe/imbriquée) — non aplatissable "
                f"vers une Rule geostyler-style unique.")
        expr = rule_el.get("filter")
        filtre = traduire_filtre_qgis_simple(
            expr, avertissements=ctx["avertissements"], chemin_source=ctx["chemin_source"],
        ) if expr else None
        rules.append(_rule_depuis_symbole(
            symbole_el, rule_el.get("label") or "règle", filtre, **ctx))
    return rules


def _renderer_null_symbol(renderer_el: ET.Element, ctx: dict) -> list[dict]:
    return []  # aucune règle : "ne rien dessiner" est un état valide, pas une erreur.


#: type de renderer QGIS (attribut type= de renderer-v2) -> fonction(el, ctx)
#: -> list[dict Rule]. Registre ouvert (enregistrer_lecteur_renderer). Les 6
#: renderers du corpus niveau 1 qui n'y figurent pas (embeddedSymbol,
#: heatmapRenderer, invertedPolygonRenderer, mergedFeatureRenderer,
#: pointCluster, pointDisplacement, 25dRenderer) combinent des données
#: par-entité ou une logique de rendu procédurale sans équivalent dans le
#: modèle "liste de Rule" de geostyler-style — ce n'est pas une lacune de ce
#: lecteur mais une limite du pivot lui-même, à documenter, pas à contourner
#: par une approximation trompeuse.
REGISTRE_RENDERERS: dict[str, Callable[[ET.Element, dict], list[dict]]] = {
    "singleSymbol": _renderer_single_symbol,
    "categorizedSymbol": _renderer_categorized_symbol,
    "graduatedSymbol": _renderer_graduated_symbol,
    "RuleRenderer": _renderer_rule_renderer,
    "nullSymbol": _renderer_null_symbol,
}


def enregistrer_lecteur_renderer(type_renderer: str, fonction: Callable[[ET.Element, dict], list[dict]]) -> None:
    """Point d'extension : ajoute (ou remplace) le traducteur d'un type de
    rendu QGIS, sans modifier la logique d'orchestration de ce module."""
    REGISTRE_RENDERERS[type_renderer] = fonction


# --------------------------------------------------------------------------- point d'entrée
def lire_fichier_qml(
    chemin_qml: str,
    *,
    nom_style: str | None = None,
    dpi: float = 90.0,
    sur_expression_non_traduite: Literal["lever", "avertir"] = "lever",
) -> LectureResultat:
    """Lit un fichier .qml QGIS et produit un pivot geostyler-style typé et
    validé (styleforge_core.pivot.Style).

    Paramètres (tous évolutifs — jamais de valeur figée en dur dans la
    logique de traduction) :
      nom_style                   : nom du Style produit (défaut : le nom de
                                     fichier sans extension).
      dpi                         : résolution supposée pour convertir les
                                     tailles en unité physique (MM/Point/Inch)
                                     vers des pixels (voir convertir_taille).
                                     Défaut 90 : convention OGC SLD/SE
                                     ("pixel standard" = 1/90 pouce), celle
                                     qu'utilise QGIS lui-même dans
                                     saveSldStyle() — vérifié contre l'oracle
                                     QGIS, pas 96 (résolution écran).
      sur_expression_non_traduite : "lever" (défaut, sûr) pour arrêter sur la
                                     première propriété pilotée par une
                                     expression QGIS non traduisible
                                     automatiquement, ou "avertir" pour
                                     conserver la valeur statique et
                                     poursuivre (voir LectureResultat.avertissements).

    Lève une sous-classe d'ErreurLectureQML nommée et explicite pour tout ce
    qui sort du périmètre couvert plutôt que de produire un pivot
    silencieusement incomplet.
    """
    try:
        arbre = ET.parse(chemin_qml)
    except ET.ParseError as e:
        raise DocumentQMLInvalide(f"{chemin_qml} : XML non valide : {e}") from e
    racine = arbre.getroot()
    _defaire_espace_de_noms(racine)

    renderer_el = racine.find("renderer-v2")
    if renderer_el is None:
        raise DocumentQMLInvalide(f"{chemin_qml} : pas d'élément renderer-v2")
    type_renderer = renderer_el.get("type")
    traducteur = REGISTRE_RENDERERS.get(type_renderer)
    if traducteur is None:
        raise RendererNonSupporte(
            f"{chemin_qml} : type de rendu {type_renderer!r} non couvert par ce "
            f"lecteur (registre : {sorted(REGISTRE_RENDERERS)}) — cf. la note "
            f"du registre REGISTRE_RENDERERS sur les renderers hors périmètre "
            f"du modèle Rule de geostyler-style."
        )

    avertissements: list[str] = []
    ctx = dict(chemin_source=chemin_qml, avertissements=avertissements,
               dpi=dpi, sur_expression_non_traduite=sur_expression_non_traduite)
    rules = traducteur(renderer_el, ctx)

    import os
    nom = nom_style or os.path.splitext(os.path.basename(chemin_qml))[0]
    style_brut = {"name": nom, "rules": rules}
    style = valider_style(style_brut)
    return LectureResultat(style=style, avertissements=avertissements)


if __name__ == "__main__":
    import json
    import sys

    if len(sys.argv) < 2:
        print("usage : qml.py chemin/vers/style.qml [--avertir-expressions]", file=sys.stderr)
        raise SystemExit(2)
    mode = "avertir" if "--avertir-expressions" in sys.argv[2:] else "lever"
    resultat = lire_fichier_qml(sys.argv[1], sur_expression_non_traduite=mode)
    print(json.dumps(
        {"style": resultat.style.model_dump(mode="json", exclude_none=True, by_alias=True),
         "avertissements": resultat.avertissements},
        indent=2, ensure_ascii=False))
