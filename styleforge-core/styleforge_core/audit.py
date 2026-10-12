#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
styleforge_core.audit — Auditeur de conformité SLD 1.0.0, extrait de la
PHASE 6 du script cnig_qml2sld_geoserver.py (classe GeoServerAuditor
d'origine) et GÉNÉRALISÉ pour la bibliothèque, conformément à la Phase 4 de
plan_bibliotheque_styleforge.docx ("audit.py : auditeur de conformité,
généralisé et paramétrable").

Objectif inchangé depuis le script CNIG : ne livrer aucun SLD dont on ne
sache pas s'il fonctionnera. GeoServer (ou tout autre consommateur SLD 1.0)
refuse un style en validation stricte, ou pire le rend de travers sans rien
signaler. Le schéma XSD officiel n'étant pas toujours accessible (réseau
d'entreprise, proxy), cet auditeur reproduit EN PYTHON les règles qui
comptent : le modèle de contenu SLD 1.0.0, les extensions admises par la
cible visée, et les pièges de rendu que l'XSD ne voit pas (un <Stroke/> vide
qui fabrique un contour noir, un pictogramme référencé mais absent).

L'audit tourne sur des fichiers ÉCRITS (des chemins), pas sur des structures
Python en mémoire : c'est bien le livrable qui est contrôlé, exactement
comme dans le script d'origine.

CE QUI A CHANGÉ PAR RAPPORT À GeoServerAuditor (le principe évolutif du
projet : tout ce qui est un CHOIX devient un PARAMÈTRE, rien n'est codé en
dur au nom d'un déploiement particulier) :

  1. Les cinq vocabulaires (AUDIT_NUMERIQUES, AUDIT_EXPRESSIONS,
     AUDIT_WELLKNOWN, AUDIT_VENDOR, AUDIT_CSS de l'original) sont regroupés
     dans une seule dataclass `VocabulaireCible`, passée en PARAMÈTRE au
     constructeur de SldAuditor plutôt que codée en dur dans la classe. Le
     jeu de valeurs GeoServer d'origine reste disponible tel quel comme
     `VOCABULAIRE_GEOSERVER` (comportement identique par défaut) — mais rien
     n'empêche désormais un appelant de fournir le vocabulaire d'une autre
     version de GeoServer, ou d'un autre serveur WMS/SLD 1.0 entièrement,
     sans toucher à la logique d'audit elle-même.

  2. Le modèle de contenu XSD_ORDER de l'original devient
     `ORDRE_XSD_SLD_1_0_0` : c'est un FAIT du schéma OGC SLD 1.0.0 lui-même
     (l'ordre des enfants qu'impose le XSD), pas une convention GeoServer —
     il reste donc SÉPARÉ du VocabulaireCible, mais suit la même discipline
     de nommage versionné que le pivot (cf. styleforge_core.pivot,
     "PivotV1") : un futur SLD 1.1 ajouterait ORDRE_XSD_SLD_1_1_0 à côté,
     jamais une modification silencieuse de celui-ci.

  3. La résolution "un pictogramme référencé existe-t-il ?" n'est plus
     câblée en dur sur `styles_dir / href` : c'est désormais un paramètre
     `existe_ressource` (Callable[[str], bool]) optionnel. Quand il est
     fourni, il est utilisé tel quel. Sinon, si `styles_dir` est fourni, un
     résolveur Path équivalent à l'original est construit automatiquement
     (comportement inchangé). Si NI L'UN NI L'AUTRE n'est fourni et qu'une
     référence locale doit être vérifiée, ce module NE SUPPOSE PAS qu'elle
     est présente ET NE LA REJETTE PAS non plus silencieusement : il lève un
     problème d'une catégorie dédiée ("vérification de ressource impossible
     — aucun résolveur configuré"), conformément à la discipline du projet
     de ne jamais avaler silencieusement un cas non couvert. C'est une
     préfiguration délibérée, à cet échelon minimal, du "résolveur de
     ressources" prévu pour registry.py (section 4.2 du plan) — sans
     attendre que ce module existe pour rendre l'auditeur réutilisable hors
     du contexte fichier CNIG.

  4. Les dépendances UI/CNIG de l'original sont retirées du cœur : plus
     d'appel à Console.step/ok/err/info/raw (présentation, propre à la
     console du script CNIG) ni à pump_ui() (spécifique à l'éventuelle
     interface graphique du script CNIG). auditer() renvoie une
     `RapportAudit`, une structure de données pure ; `formater_rapport()`
     produit une représentation texte de ce rapport SANS l'imprimer — libre
     à chaque appelant (CLI, API, notebook, test) de l'afficher, l'écrire
     dans un fichier ou l'ignorer. Un unique point d'extension,
     `apres_fichier` (Callable[[Path], None]), remplace pump_ui() : un
     appelant qui a besoin de faire respirer une boucle d'événements Qt (ou
     toute autre chose après chaque fichier contrôlé) le fournit lui-même.

  5. La classe est renommée `SldAuditor` (au lieu de `GeoServerAuditor`) :
     son comportement par défaut reste 100% GeoServer (VOCABULAIRE_GEOSERVER
     en valeur par défaut du paramètre `vocabulaire`), mais la classe elle-
     même n'est plus nommée d'après UNE cible particulière, cohérent avec le
     principe (section 4.1 du plan) que le cœur ne doit jamais coder en dur
     un nom de cible — tout ce qui en dépend est injecté.

Rien d'autre n'a changé : les catégories de problème, leurs messages, et
l'ordre des contrôles par élément sont repris À L'IDENTIQUE de
GeoServerAuditor — une non-régression vérifiable par comparaison directe
(voir tests/test_audit.py, section "ÉQUIVALENCE AVEC L'ORIGINAL"), pas
seulement par lecture du code.
"""
from __future__ import annotations

import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, FrozenSet, List, Optional, Sequence, Tuple


# ============================================================================
# Modèle de contenu SLD 1.0.0 — fait du schéma OGC, pas une convention
# GeoServer. Nommé par version, comme le pivot (voir docstring du module).
# ============================================================================
ORDRE_XSD_SLD_1_0_0: Dict[str, Tuple[str, ...]] = {
    "StyledLayerDescriptor": ("Name", "Title", "Abstract", "NamedLayer", "UserLayer"),
    "NamedLayer": ("Name", "Description", "LayerFeatureConstraints", "UserStyle"),
    "UserStyle": ("Name", "Title", "Abstract", "IsDefault", "FeatureTypeStyle"),
    "FeatureTypeStyle": ("Name", "Title", "Abstract", "FeatureTypeName",
                         "SemanticTypeIdentifier", "Rule", "VendorOption"),
    "Rule": ("Name", "Title", "Abstract", "LegendGraphic",
             "Filter", "ElseFilter",
             "MinScaleDenominator", "MaxScaleDenominator",
             "LineSymbolizer", "PolygonSymbolizer", "PointSymbolizer",
             "TextSymbolizer", "RasterSymbolizer"),
    "PointSymbolizer": ("Geometry", "Graphic", "VendorOption"),
    "LineSymbolizer": ("Geometry", "Stroke", "PerpendicularOffset", "VendorOption"),
    "PolygonSymbolizer": ("Geometry", "Fill", "Stroke", "VendorOption"),
    "TextSymbolizer": ("Geometry", "Label", "Font", "LabelPlacement", "Halo",
                       "Fill", "Graphic", "Priority", "VendorOption"),
    "Graphic": ("ExternalGraphic", "Mark", "Opacity", "Size", "Rotation",
                "AnchorPoint", "Displacement"),
    "Mark": ("WellKnownName", "Fill", "Stroke"),
    "ExternalGraphic": ("OnlineResource", "InlineContent", "Format",
                        "ColorReplacement"),
    "Fill": ("GraphicFill", "CssParameter"),
    "Stroke": ("GraphicFill", "GraphicStroke", "CssParameter"),
    "Halo": ("Radius", "Fill"),
    "LabelPlacement": ("PointPlacement", "LinePlacement"),
    "PointPlacement": ("AnchorPoint", "Displacement", "Rotation"),
    "LinePlacement": ("PerpendicularOffset",),
}


# ============================================================================
# Vocabulaire d'une CIBLE (un serveur SLD 1.0 particulier, GeoServer par
# défaut) — un CHOIX de déploiement, donc un paramètre, jamais codé en dur.
# ============================================================================
@dataclass(frozen=True)
class VocabulaireCible:
    """Les cinq vocabulaires que GeoServerAuditor codait en dur, regroupés
    et rendus substituables. Chaque champ reprend, sans changement de
    valeurs, l'un des ensembles AUDIT_* du script CNIG d'origine."""

    #: Éléments dont le contenu doit être un nombre (ou une expression OGC
    #: reconnue, voir `expressions`).
    numeriques: FrozenSet[str]
    #: Éléments d'expression OGC admis à l'intérieur d'un ParameterValueType
    #: — leur présence rend l'élément parent valide même sans texte.
    expressions: FrozenSet[str]
    #: Noms de WellKnownName reconnus tels quels (hors préfixes, voir
    #: `wellknown_prefixes`).
    wellknown: FrozenSet[str]
    #: Préfixes de WellKnownName reconnus (shape://, ttf://, ...).
    wellknown_prefixes: Tuple[str, ...]
    #: VendorOption reconnues par la cible. Une option inconnue est ignorée
    #: silencieusement par la plupart des moteurs de rendu SLD : autant la
    #: repérer ici plutôt que de laisser le style mentir sur ce qu'il fait.
    vendor: FrozenSet[str]
    #: Noms de CssParameter valides pour cette cible en SLD 1.0.
    css: FrozenSet[str]


#: Vocabulaire GeoServer — reprise EXACTE des cinq ensembles AUDIT_* du
#: script CNIG (cnig_qml2sld_geoserver.py, PHASE 6), sans aucune valeur
#: ajoutée ni retirée. C'est le vocabulaire par défaut de SldAuditor : le
#: comportement de ce module, sans arguments supplémentaires, est identique
#: à celui de GeoServerAuditor.
VOCABULAIRE_GEOSERVER = VocabulaireCible(
    numeriques=frozenset({
        "Size", "Rotation", "Opacity", "MinScaleDenominator", "MaxScaleDenominator",
        "PerpendicularOffset", "Radius", "DisplacementX", "DisplacementY",
        "AnchorPointX", "AnchorPointY", "Priority",
    }),
    expressions=frozenset({
        "Literal", "PropertyName", "Function", "Add", "Sub", "Mul", "Div",
    }),
    wellknown=frozenset({"circle", "square", "triangle", "star", "cross", "x"}),
    wellknown_prefixes=("shape://", "file://", "wkt://", "ttf://"),
    vendor=frozenset({
        "graphic-margin", "graphic-resize", "random", "random-seed",
        "random-tile-size", "random-symbol-count", "random-rotation",
        "composite", "composite-base", "sortBy", "sortByGroup",
        "group", "spaceAround", "maxDisplacement", "conflictResolution",
        "goodnessOfFit", "partials", "autoWrap", "followLine", "repeat",
        "maxAngleDelta", "polygonAlign", "labelObstacle", "inclusion",
        "labelAllGroup", "forceLeftToRight", "allGroup", "underlineText",
        "strikethroughText", "charSpacing", "wordSpacing", "displacementMode",
        "fontShrinkSizeMin", "graphic-margin-top",
    }),
    css=frozenset({
        "fill", "fill-opacity", "stroke", "stroke-width", "stroke-opacity",
        "stroke-linejoin", "stroke-linecap", "stroke-dasharray", "stroke-dashoffset",
        "font-family", "font-size", "font-style", "font-weight",
    }),
)


@dataclass
class RapportAudit:
    """Structure de données pure (aucune impression) renvoyée par
    SldAuditor.auditer(). Même contenu que les attributs de GeoServerAuditor
    (problemes/details/extensions/controles), regroupés."""

    controles: int = 0
    problemes: "Counter[str]" = field(default_factory=Counter)
    details: Dict[str, List[str]] = field(default_factory=lambda: defaultdict(list))
    extensions: "Counter[str]" = field(default_factory=Counter)

    @property
    def conforme(self) -> bool:
        """True si aucun défaut détecté — même définition que le booléen
        renvoyé par GeoServerAuditor.afficher() dans le script d'origine."""
        return not self.problemes


class SldAuditor:
    """
    Contrôle chaque SLD produit et permet de ne conclure « prêt » qu'avec
    preuve. Reprend le comportement de GeoServerAuditor (script CNIG, PHASE
    6) à l'identique par défaut — voir la docstring du module pour ce qui a
    été généralisé et pourquoi.
    """

    XLINK = "{http://www.w3.org/1999/xlink}"

    def __init__(
        self,
        *,
        xsd_order: Dict[str, Sequence[str]] = ORDRE_XSD_SLD_1_0_0,
        vocabulaire: VocabulaireCible = VOCABULAIRE_GEOSERVER,
        styles_dir: Optional[Path] = None,
        existe_ressource: Optional[Callable[[str], bool]] = None,
        apres_fichier: Optional[Callable[[Path], None]] = None,
    ) -> None:
        self.xsd_order = xsd_order
        self.vocabulaire = vocabulaire
        self.styles_dir = styles_dir
        self._existe_ressource = existe_ressource
        self._apres_fichier = apres_fichier
        self.rapport = RapportAudit()

    # ------------------------------------------------------------------ util
    def _ko(self, categorie: str, message: str) -> None:
        self.rapport.problemes[categorie] += 1
        if len(self.rapport.details[categorie]) < 5:
            self.rapport.details[categorie].append(message)

    def _extension(self, categorie: str) -> None:
        self.rapport.extensions[categorie] += 1

    @staticmethod
    def _nom(element: Any) -> str:
        tag = element.tag
        if not isinstance(tag, str):
            return ""
        return tag.split("}", 1)[1] if "}" in tag else tag

    def _ressource_existe(self, href: str) -> Optional[bool]:
        """True/False si vérifiable, None si aucun résolveur n'est
        configuré — voir point 3 de la docstring du module : un None
        n'est JAMAIS interprété comme "présent" ni comme "absent" par
        l'appelant (_audit_element), il produit son propre problème
        nommé plutôt qu'une approximation silencieuse."""
        if self._existe_ressource is not None:
            return self._existe_ressource(href)
        if self.styles_dir is not None:
            cible = self.styles_dir / href.split("?", 1)[0]
            return cible.is_file()
        return None

    # ------------------------------------------------------------------- API
    def auditer(self, fichiers: Sequence[Optional[Path]]) -> RapportAudit:
        for chemin in fichiers:
            if chemin is None or not chemin.is_file():
                continue
            self.rapport.controles += 1
            self._audit_fichier(chemin)
            if self._apres_fichier is not None:
                self._apres_fichier(chemin)
        return self.rapport

    def _audit_fichier(self, chemin: Path) -> None:
        nom = chemin.name
        brut = chemin.read_bytes()

        # --- encodage et fins de ligne --------------------------------
        if brut.startswith(b"\xef\xbb\xbf"):
            self._ko("BOM UTF-8 présent",
                     f"{nom} — GeoServer rejette avec « Content is not allowed "
                     f"in prolog »")
        if b"\r\n" in brut:
            self._ko("fins de ligne CRLF", nom)
        try:
            brut.decode("utf-8")
        except UnicodeDecodeError as exc:
            self._ko("encodage non UTF-8", f"{nom} : {exc}")
            return

        # --- bonne formation ------------------------------------------
        try:
            racine = ET.fromstring(brut)
        except Exception as exc:                               # noqa: BLE001
            self._ko("XML mal formé", f"{nom} : {exc}")
            return

        if self._nom(racine) != "StyledLayerDescriptor":
            self._ko("racine incorrecte", f"{nom} : <{self._nom(racine)}>")
        if racine.get("version") != "1.0.0":
            self._ko("version SLD incorrecte",
                     f"{nom} : {racine.get('version')}")
        if not racine.findall(".//{*}Rule") and not racine.findall(".//Rule"):
            self._ko("style sans aucune règle", nom)

        for element in racine.iter():
            if not isinstance(element.tag, str):
                continue
            self._audit_element(nom, element)

    # -------------------------------------------------------- par élément
    def _audit_element(self, nom: str, element: Any) -> None:
        balise = self._nom(element)
        texte = (element.text or "").strip()

        # --- ordre imposé par le modèle de contenu --------------------
        ordre = self.xsd_order.get(balise)
        if ordre:
            positions = [ordre.index(self._nom(enfant)) for enfant in element
                         if self._nom(enfant) in ordre]
            if positions != sorted(positions):
                self._ko("ordre XSD non respecté",
                         f"{nom} : <{balise}> contient "
                         f"{[self._nom(e) for e in element]}")

        # --- valeurs numériques ---------------------------------------
        #
        #  Size, Rotation, Opacity et consorts sont de type ParameterValueType :
        #  leur contenu n'est PAS forcément un nombre littéral, ce peut être une
        #  expression OGC. bridgestyle produit par exemple, pour une taille
        #  divisée par deux :
        #
        #      <Size><ogc:Div><ogc:Literal>15.0</ogc:Literal>
        #                     <ogc:Literal>2</ogc:Literal></ogc:Div></Size>
        #
        #  C'est parfaitement valide. Un contrôle qui ne regarde que le texte y
        #  voit un élément vide et crie au défaut — faux positif d'autant plus
        #  nuisible qu'il décrédibilise les vrais.
        if balise in self.vocabulaire.numeriques:
            if len(element):
                # Le contrôle descend TOUT le sous-arbre : une balise étrangère
                # nichée sous un <ogc:Mul> est aussi fautive qu'à la racine de
                # l'expression, et un contrôle limité au premier niveau ne la
                # verrait jamais.
                inconnus = sorted({self._nom(e) for e in element.iter()
                                   if e is not element
                                   and self._nom(e) not in self.vocabulaire.expressions})
                if inconnus:
                    self._ko("expression non reconnue dans un élément numérique",
                             f"{nom} : <{balise}> contient {inconnus}")
            elif not texte:
                self._ko("élément numérique vide", f"{nom} : <{balise}/>")
            else:
                try:
                    float(texte)
                except ValueError:
                    self._ko("valeur numérique invalide",
                             f"{nom} : <{balise}>{texte[:30]}")

        # --- éléments vides au rendu néfaste --------------------------
        if balise in ("Stroke", "Fill") and len(element) == 0 and not texte:
            self._ko("Stroke ou Fill vide",
                     f"{nom} : <{balise}/> — GeoServer dessine un contour noir "
                     f"de 1 px")

        # --- CssParameter ---------------------------------------------
        if balise == "CssParameter":
            cle = element.get("name")
            if not cle:
                self._ko("CssParameter sans attribut name", nom)
            elif cle not in self.vocabulaire.css:
                self._ko("CssParameter inconnu", f"{nom} : {cle}")
            if not texte:
                self._ko("CssParameter sans valeur", f"{nom} : {cle}")
            elif cle == "stroke-dasharray":
                for jeton in texte.split():
                    try:
                        float(jeton)
                    except ValueError:
                        self._ko("stroke-dasharray non numérique",
                                 f"{nom} : {texte[:40]}")
                        break

        # --- marques --------------------------------------------------
        if balise == "Mark":
            noms = [e for e in element if self._nom(e) == "WellKnownName"]
            if len(noms) != 1:
                self._ko("Mark sans WellKnownName unique",
                         f"{nom} : {len(noms)} trouvés")
            else:
                valeur = (noms[0].text or "").strip()
                if not (valeur in self.vocabulaire.wellknown
                        or valeur.startswith(self.vocabulaire.wellknown_prefixes)):
                    self._ko("WellKnownName non reconnu par la cible",
                             f"{nom} : {valeur[:40]}")

        # --- pictogrammes externes ------------------------------------
        if balise == "ExternalGraphic":
            ressources = [e for e in element if self._nom(e) == "OnlineResource"]
            formats = [e for e in element if self._nom(e) == "Format"]
            if not ressources:
                self._ko("ExternalGraphic sans OnlineResource", nom)
            else:
                href = (ressources[0].get(self.XLINK + "href")
                        or ressources[0].get("xlink:href")
                        or ressources[0].get("href"))
                if not href:
                    self._ko("OnlineResource sans xlink:href", nom)
                elif not href.startswith(("http://", "https://")):
                    existe = self._ressource_existe(href)
                    if existe is False:
                        self._ko("pictogramme référencé mais absent",
                                 f"{nom} : {href}")
                    elif existe is None:
                        self._ko("vérification de ressource impossible",
                                 f"{nom} : {href} — aucun résolveur configuré "
                                 f"(ni styles_dir, ni existe_ressource)")
            if not formats:
                self._ko("ExternalGraphic sans Format", nom)

        # --- motifs ----------------------------------------------------
        if balise in ("GraphicFill", "GraphicStroke"):
            graphiques = [e for e in element if self._nom(e) == "Graphic"]
            if len(graphiques) != 1:
                self._ko("GraphicFill ou GraphicStroke mal formé",
                         f"{nom} : {len(graphiques)} <Graphic>")

        # --- VendorOption ----------------------------------------------
        if balise == "VendorOption":
            cle = element.get("name")
            if not cle:
                self._ko("VendorOption sans attribut name", nom)
            elif cle not in self.vocabulaire.vendor:
                self._ko("VendorOption inconnue de la cible",
                         f"{nom} : {cle}")

        # --- filtres ---------------------------------------------------
        if balise == "PropertyName" and not texte:
            self._ko("PropertyName vide", nom)

        if balise == "PropertyIsLike":
            # Le contenu compte autant que les attributs : le modèle Filter 1.0
            # impose exactement <PropertyName> puis <Literal>, dans cet ordre.
            enfants = [self._nom(e) for e in element]
            if enfants[:2] != ["PropertyName", "Literal"]:
                self._ko("PropertyIsLike mal formé", f"{nom} : {enfants}")

            # filter.xsd 1.0.0 : wildCard, singleChar et escape, tous requis.
            for attendu in ("wildCard", "singleChar", "escape"):
                if attendu not in element.attrib:
                    self._ko("PropertyIsLike incomplet",
                             f"{nom} : attribut {attendu} manquant "
                             f"(requis par filter.xsd 1.0.0)")
            # escapeChar est la graphie de Filter 1.1 : dans un document 1.0,
            # c'est un attribut non déclaré.
            if "escapeChar" in element.attrib:
                self._ko("attribut hors vocabulaire Filter 1.0",
                         f"{nom} : escapeChar — la graphie 1.0 est « escape »")
            # matchCase n'existe qu'à partir de Filter 1.1. GeoServer le
            # comprend ; on le signale sans le compter comme défaut.
            if "matchCase" in element.attrib:
                self._extension("matchCase sur PropertyIsLike "
                                "(extension GeoServer)")


def formater_rapport(rapport: RapportAudit) -> str:
    """Représentation texte pure du rapport (aucun print ici) — même
    contenu informatif que GeoServerAuditor.afficher() dans le script
    d'origine, mais RENVOYÉ plutôt qu'imprimé sur une Console CNIG : à
    l'appelant (CLI, API, test) de l'afficher, le journaliser, ou l'ignorer.
    """
    lignes: List[str] = []
    lignes.append(f"Audit de conformité SLD ({rapport.controles} fichier(s) contrôlé(s))")
    if rapport.conforme:
        lignes.append("Conforme : aucun défaut détecté.")
        lignes.append("  encodage UTF-8 sans BOM, XML bien formé,")
        lignes.append("  ordre des éléments conforme au modèle SLD 1.0.0,")
        lignes.append("  valeurs numériques valides, aucun élément vide,")
        lignes.append("  marques et VendorOption reconnues par la cible,")
        lignes.append("  tous les pictogrammes référencés sont présents.")
    else:
        total = sum(rapport.problemes.values())
        lignes.append(f"{total} défaut(s) de conformité répartis en "
                      f"{len(rapport.problemes)} catégorie(s) :")
        for categorie, nombre in rapport.problemes.most_common():
            lignes.append(f"  {categorie:<44} {nombre:>5}")
            for detail in rapport.details[categorie]:
                lignes.append(f"       {detail[:100]}")
        lignes.append("Ces styles risquent d'être refusés à l'import ou de "
                      "rendre de travers.")

    if rapport.extensions:
        lignes.append("")
        lignes.append("Extensions assumées (hors XSD strict) :")
        for categorie, nombre in rapport.extensions.most_common():
            lignes.append(f"  {categorie:<52} {nombre:>5}")
        lignes.append("  Elles sont nécessaires au rendu et comprises par la "
                      "cible visée,")
        lignes.append("  mais un validateur XSD 1.0 strict les refusera.")

    return "\n".join(lignes)


__all__ = [
    "ORDRE_XSD_SLD_1_0_0",
    "VocabulaireCible",
    "VOCABULAIRE_GEOSERVER",
    "RapportAudit",
    "SldAuditor",
    "formater_rapport",
]
