#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
styleforge_core.writers.sld_posttraitement — PHASE 4 : post-traitement XML et
correctifs GeoServer, appliqués à un document SLD 1.0.0 déjà écrit (par
n'importe quel écrivain : celui de ce paquet, ou bridge-style via le CLI
`cnig_qml2sld_geoserver.py`).

Origine de ce module : migré DEPUIS `cnig_qml2sld_geoserver.py` (où il
vivait sous le nom `SldPostProcessor` + `HintExtractor`, dans la section
« PHASE 4 ») vers `styleforge-core`, pour que le CLI et le plugin QGIS
(`qgis-plugin/`) partagent EXACTEMENT le même code plutôt que deux copies
qui dériveraient l'une de l'autre au fil des correctifs. Le déplacement est
une pure extraction de texte (aucune ligne de logique réécrite) : la preuve
en est la comparaison octet à octet des 17 SLD/MBStyle du corpus d'exemples
avant/après, sur `--backend styleforge` (voir `tests/` et le commit qui
introduit ce fichier).

Pourquoi ce déplacement est sûr — SANS DÉPENDANCE PyQGIS :
  * `QmlDocument` relit le QML brut avec `xml.etree.ElementTree` seul
    (aucun `qgis.core`), exactement comme `styleforge_core.readers.qml`.
  * `SldPostProcessor` ne fait que parser/transformer/sérialiser du texte
    XML SLD — aucun appel à `QgsVectorLayer` ou autre API QGIS.
  * Un commentaire du CLI, au point d'origine de ce code, l'affirmait déjà
    explicitement : « PHASE 4 (SldPostProcessor) s'applique SANS
    MODIFICATION à la sortie de ce backend [styleforge]... Les hachures et
    VendorOption GeoServer restent donc injectées normalement, même en
    --backend styleforge. » — ce module était donc déjà conçu comme
    backend-agnostique avant même d'être déplacé ici.

Utilisation (fonction publique, voir sa docstring plus bas) :

    from styleforge_core.writers.sld_posttraitement import post_traiter_sld

    sld_corrige, stats = post_traiter_sld(
        sld_text, chemin_qml, index_svg=svg_index,
        vendor=VENDOR_DEFAULTS_PAR_DEFAUT,   # ou un dict personnalisé
    )

`index_svg` est le même dictionnaire {nom_fichier.lower(): "svg/cnig/..."}
que celui que l'appelant utilise déjà pour déployer les pictogrammes SVG
(voir `GeoServerTreeBuilder.deploy_svg()` côté CLI, ou l'équivalent côté
plugin QGIS) — ce module ne déploie AUCUN fichier lui-même, il ne fait que
réécrire les références déjà présentes dans le SLD pour qu'elles pointent
vers cet index.
"""

from __future__ import annotations

import base64
import hashlib
import re
import xml.etree.ElementTree as ET
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple

#: Sous-dossier imposé par le cahier des charges pour les pictogrammes.
SVG_SUBDIR = Path("svg") / "cnig"

#: Registre des SVG EMBARQUÉS EN BASE64 dans les QML, découverts à la volée
#: par `register_svg_reference()`. {nom_de_fichier: contenu binaire}.
#: Partagé par construction avec tout appelant qui importe ce module : le
#: CLI (PHASE 3b, `GeoServerTreeBuilder.deploy_svg()`) et le plugin QGIS
#: lisent ce MÊME dictionnaire pour matérialiser les fichiers sur disque,
#: après que `register_svg_reference()` les y a déposés. Jamais vidé
#: automatiquement par ce module : c'est à l'appelant de le faire entre deux
#: lots de conversion indépendants, s'il veut éviter qu'un pictogramme d'un
#: lot précédent reste déployé pour un autre.
EMBEDDED_SVG: Dict[str, bytes] = {}


def register_svg_reference(value: Optional[str],
                           hint_name: str = "cnig") -> Optional[str]:
    """
    Normalise une référence SVG issue d'un QML et retourne un NOM DE FICHIER.

    Les QML du CNIG (produits par SLYR à partir des .lyrx ArcGIS) n'utilisent
    PAS de chemins de fichiers pour les pictogrammes : ils EMBARQUENT le SVG
    encodé en base64 directement dans la propriété, sous la forme

        <Option name="name" type="QString"
                value="base64:PD94bWwgdmVyc2lvbj0iMS4wIiBlbmNvZGluZz0i..."/>

    Sur le corpus PLU réel, c'est le cas de la quasi-totalité des SvgMarker.
    Sans traitement, ces valeurs finissent telles quelles dans
    <WellKnownName>, GeoServer ne les reconnaît pas et le symbole disparaît.

    On décode donc le contenu, on lui attribue un nom stable dérivé de son
    empreinte SHA-1 (le même pictogramme utilisé par dix règles ne produit
    qu'UN fichier), et on l'enregistre dans `EMBEDDED_SVG` pour déploiement
    ultérieur par l'appelant.

    Retourne le nom de fichier (ex. « cnig_prescription_a1b2c3d4e5.svg »)
    ou None si la valeur est vide.
    """
    if not value:
        return None
    value = value.strip()

    if value.lower().startswith("base64:"):
        try:
            payload = base64.b64decode(value[7:], validate=False)
        except Exception:                                  # noqa: BLE001
            return None
        digest = hashlib.sha1(payload).hexdigest()[:10]    # nosec B324
        name = f"{safe_stem(hint_name)}_{digest}.svg"
        EMBEDDED_SVG.setdefault(name, payload)
        return name

    # Chemin classique (Windows, POSIX, URL) : on ne garde que le nom.
    name = Path(value.replace("\\", "/")).name
    return name or None


def resoudre_href_svg(raw: str, index: Dict[str, str]) -> Optional[str]:
    """
    Transforme une référence quelconque (chemin Windows absolu, URL, nom nu,
    'file://x.svg', './symboles/x.svg') en chemin relatif `svg/cnig/x.svg`.

    `index` est le dictionnaire {nom_fichier.lower(): chemin_relatif} déjà
    déployé par l'appelant (voir la docstring du module) — cette fonction ne
    touche jamais le disque elle-même.
    """
    if not raw:
        return None
    cleaned = raw.strip()
    for prefix in ("file:///", "file://", "file:"):
        if cleaned.lower().startswith(prefix):
            cleaned = cleaned[len(prefix):]
            break
    # Sépare d'éventuels paramètres GeoServer (?fill=...)
    params = ""
    if "?" in cleaned:
        cleaned, params = cleaned.split("?", 1)
        params = "?" + params
    name = Path(cleaned.replace("\\", "/")).name
    if not name.lower().endswith(".svg"):
        return None
    target = index.get(name.lower())
    if target is None:
        # Pictogramme absent du dépôt : on pointe quand même au bon endroit
        # pour que l'ajout manuel du fichier suffise à réparer le rendu.
        target = (SVG_SUBDIR / name).as_posix()
    return target + params

MM2PIXEL = 1.0 / 0.28
POINT2PIXEL = MM2PIXEL * 0.352777778          # 1 pt = 1/72 in = 0,3528 mm
INCH2PIXEL = MM2PIXEL * 25.4

#: Valeurs par défaut des VendorOption GeoServer injectées en PHASE 4.
#: L'équipe peut ajuster ce dictionnaire sans toucher au reste du code.
VENDOR_DEFAULTS: Dict[str, Dict[str, str]] = {
    # Options applicables aux PolygonSymbolizer comportant un GraphicFill
    # (hachures et motifs) — « graphic-margin » pilote l'espacement du motif.
    "polygon_graphicfill": {
        "graphic-margin": "0",
    },
    # Options d'étiquetage : reproduisent le comportement « QGIS-like » de
    # GeoServer (un label par groupe de features, anti-chevauchement, etc.).
    "text": {
        "group": "yes",
        "spaceAround": "10",
        "maxDisplacement": "40",
        "conflictResolution": "true",
        "goodnessOfFit": "0.3",
        "partials": "false",
        "autoWrap": "60",
    },
    # Options d'étiquetage spécifiques aux géométries linéaires.
    "text_line": {
        "followLine": "true",
        "repeat": "150",
        "maxAngleDelta": "30",
    },
    # Options d'étiquetage spécifiques aux surfaces.
    "text_polygon": {
        "polygonAlign": "mbr",
    },
}

# ------------------------------------------------------------------------------
#  Table de correspondance : styles de brosse Qt (QGIS SimpleFill) -> GeoServer
#  bridge-style ne connaît que horizontal / vertical / cross (cf. PATTERN_NAMES
#  dans bridgestyle/qgis/togeostyler.py). Tous les autres styles ressortent
#  TELS QUELS dans <WellKnownName>, ce que GeoServer rejette (rendu vide).
#  => corrigé en PHASE 4.
# ------------------------------------------------------------------------------
QT_BRUSH_TO_WKN: Dict[str, str] = {
    "horizontal": "shape://horline",
    "vertical": "shape://vertline",
    "cross": "shape://times",
    "b_diagonal": "shape://slash",       # « / »  (bas-gauche -> haut-droite)
    "f_diagonal": "shape://backslash",   # « \ »
    "diagonal_x": "shape://times",
    "dense1": "shape://times",
    "dense2": "shape://times",
    "dense3": "shape://times",
    "dense4": "shape://times",
    "dense5": "shape://plus",
    "dense6": "shape://plus",
    "dense7": "shape://plus",
    "solid": "",                          # traité comme un aplat, pas un motif
    "no": "",
}

#: Noms de FORME QGIS (SimpleMarker.name, p.ex. "equilateral_triangle") ->
#: WellKnownName GeoServer le plus fidèle (vocabulaire à 6 noms, cf.
#: VOCABULAIRE_GEOSERVER.wellknown dans styleforge_core.audit). Table
#: SÉPARÉE de QT_BRUSH_TO_WKN ci-dessus : deux vocabulaires sans rapport
#: (styles de BROSSE Qt pour les hachures de remplissage, vs noms de FORME
#: de marqueur ponctuel) qui aboutissent tous les deux dans un élément
#: <WellKnownName>, d'où la confusion découverte en comparant le SLD produit
#: contre l'oracle QGIS (QgsVectorLayer.saveSldStyle()) sur plu_psc_p.qml :
#: "equilateral_triangle" (une forme de marqueur QGIS native, PAS une dette
#: bridge-style) retombait dans le même fourre-tout "non reconnu -> square"
#: que les styles de brosse vraiment non reconnus, perdant silencieusement
#: un triangle pour un carré alors qu'une correspondance EXACTE existe.
#: Table ouverte : une forme QGIS rencontrée sans entrée ici (ex. "diamond",
#: "line" — vus dans le corpus CNIG mais sans équivalent fidèle parmi les 6
#: noms GeoServer) continue de retomber sur "square" via le comptage
#: wellknownname_inconnus_remplaces, approximation choisie et VISIBLE
#: (comptée), pas silencieuse — à REVOIR au cas par cas plutôt qu'à deviner.
NOMS_MARQUEURS_QGIS_VERS_WKN: Dict[str, str] = {
    "equilateral_triangle": "triangle",
}

#: Marques de hachure GeoServer natives, par angle « canonique ».
HATCH_WKN_BY_ANGLE: Dict[int, str] = {
    0: "shape://horline",
    45: "shape://slash",
    90: "shape://vertline",
    135: "shape://backslash",
}

def safe_stem(name: str) -> str:
    """
    Normalise un nom de fichier pour GeoServer : un nom de style GeoServer ne
    doit contenir ni espace, ni accent, ni caractère spécial (il devient un nom
    de fichier ET une clé REST).
    """
    import unicodedata
    name = unicodedata.normalize("NFKD", name)
    name = name.encode("ascii", "ignore").decode("ascii")
    name = re.sub(r"[^A-Za-z0-9_\-]+", "_", name)
    name = re.sub(r"_{2,}", "_", name).strip("_")
    # La CASSE D'ORIGINE EST PRÉSERVÉE : ce nom devient celui du style dans
    # GeoServer et le contenu des balises <Name> / <Title>. Le mettre en
    # minuscules serait déjà une renommage, gênant pour rapprocher un style
    # livré de sa source CNIG.
    return name or "style"

def qgis_color_to_hex(value: Optional[str]) -> Tuple[Optional[str], float]:
    """
    Convertit une couleur QGIS ('R,G,B,A' ou 'R,G,B,A,rgb:0.1,0.2,...' ou
    '#rrggbb') en couple (#RRGGBB, opacité 0..1).

    Retourne (None, 1.0) si la valeur est vide ou illisible.
    """
    if not value:
        return None, 1.0
    value = value.strip()
    if value.startswith("#"):
        if len(value) == 9:  # #AARRGGBB (rare)
            return "#" + value[3:9], int(value[1:3], 16) / 255.0
        return value[:7], 1.0
    parts = value.split(",")
    try:
        r, g, b = int(float(parts[0])), int(float(parts[1])), int(float(parts[2]))
    except (ValueError, IndexError):
        return None, 1.0
    alpha = 1.0
    if len(parts) > 3:
        try:
            alpha = max(0.0, min(1.0, float(parts[3]) / 255.0))
        except ValueError:
            alpha = 1.0
    return "#{:02x}{:02x}{:02x}".format(r & 255, g & 255, b & 255), alpha

def qgis_size_to_px(value: Any, unit: Optional[str]) -> Optional[float]:
    """Convertit une dimension QGIS vers des pixels OGC selon son unité."""
    try:
        v = float(value)
    except (TypeError, ValueError):
        return None
    unit = (unit or "MM").strip()
    if unit in ("MM", "Millimeter", "RenderMillimeters"):
        return round(v * MM2PIXEL, 4)
    if unit in ("Point", "Points", "RenderPoints"):
        return round(v * POINT2PIXEL, 4)
    if unit in ("Pixel", "Pixels", "RenderPixels"):
        return round(v, 4)
    if unit in ("Inch", "RenderInches"):
        return round(v * INCH2PIXEL, 4)
    if unit in ("Percentage", "RenderPercentage"):
        # CE N'EST PAS UNE LONGUEUR. La valeur exprime une proportion d'une
        # autre grandeur — typiquement le pas d'un semis de points. La traiter
        # comme des pixels transformerait « 50 % » en « 50 pixels ». On renvoie
        # None pour que l'appelant retienne sa valeur par défaut plutôt qu'un
        # nombre faux.
        return None
    # MapUnit / MetersInMapUnits : non convertible sans l'échelle -> on laisse
    # la valeur brute et on préviendra l'utilisateur.
    return round(v, 4)

def hatch_wkn_for_angle(angle: float) -> Tuple[str, float]:
    """
    Choisit la marque de hachure GeoServer la plus proche d'un angle QGIS, et
    retourne la ROTATION RÉSIDUELLE à appliquer pour retrouver l'angle exact.

    C'est la correction n°1 apportée à bridge-style : sa fonction
    `_hatchMarkerForAngle()` arrondit l'angle au quadrant de 45 degrés le plus
    proche et JETTE le reliquat. Une hachure CNIG à 30 deg devenait une hachure
    à 45 deg. Ici on conserve l'écart dans un <Rotation>, que GeoServer
    applique bien aux marques `shape://`.
    """
    a = float(angle) % 180.0
    best = min(HATCH_WKN_BY_ANGLE.keys(), key=lambda k: abs(((a - k + 90) % 180) - 90))
    residual = ((a - best + 90) % 180) - 90
    return HATCH_WKN_BY_ANGLE[best], round(residual, 3)

class QmlDocument:
    """
    Lecture bas niveau d'un fichier .qml QGIS 3.x.

    QGIS a connu deux sérialisations des propriétés de symboles :
      * ancienne (<= 3.16) :  <prop k="color" v="255,0,0,255"/>
      * nouvelle (>= 3.18) :  <Option name="color" type="QString" value="..."/>
    Les deux sont gérées de façon transparente par `layer_props()`.
    """

    def __init__(self, path: Path) -> None:
        self.path = path
        raw = path.read_bytes()
        # Certains QML produits par SLYR sortent en UTF-8 avec BOM.
        if raw.startswith(b"\xef\xbb\xbf"):
            raw = raw[3:]
        self.root = ET.fromstring(raw)

    # ------------------------------------------------------------------ util
    @staticmethod
    def layer_props(layer: ET.Element) -> Dict[str, str]:
        """Retourne le dictionnaire de propriétés d'un <layer> de symbole."""
        props: Dict[str, str] = {}
        for prop in layer.findall("prop"):
            k, v = prop.get("k"), prop.get("v")
            if k is not None:
                props[k] = v or ""
        # Nouvelle forme : <Option type="Map"><Option name=".." value=".."/></Option>
        for opt_map in layer.findall("Option"):
            if opt_map.get("type") != "Map":
                continue
            for opt in opt_map.findall("Option"):
                k, v = opt.get("name"), opt.get("value")
                if k is not None:
                    props[k] = v or ""
        return props

    @property
    def renderer(self) -> Optional[ET.Element]:
        return self.root.find(".//renderer-v2")

    @property
    def renderer_type(self) -> str:
        r = self.renderer
        return (r.get("type") if r is not None else "") or ""

    @property
    def labeling(self) -> Optional[ET.Element]:
        return self.root.find(".//labeling")

    def symbols(self) -> Dict[str, ET.Element]:
        """Index {nom_du_symbole: <symbol>} de tous les symboles du rendu."""
        out: Dict[str, ET.Element] = {}
        r = self.renderer
        if r is None:
            return out
        for container in r.findall("symbols") + r.findall("source-symbol"):
            for sym in container.findall("symbol"):
                name = sym.get("name") or str(len(out))
                out[name] = sym
        return out

    def all_symbol_layers(self) -> List[ET.Element]:
        """Tous les <layer> du document, sous-symboles compris (récursif)."""
        return list(self.root.iter("layer"))

    #: Correspondance <layerGeometryType> de QGIS -> type OGC.
    _QGIS_GEOMETRY_CODES = {"0": "Point", "1": "LineString", "2": "Polygon"}
    _SYMBOL_TO_GEOMETRY = {"fill": "Polygon", "line": "LineString",
                           "marker": "Point"}

    def geometry_type(self) -> str:
        """
        Détermine le type géométrique ('Polygon' | 'LineString' | 'Point').

        C'est une information CRITIQUE : QgsVectorLayer.loadNamedStyle() refuse
        un style dont la symbologie ne correspond pas à la géométrie de la
        couche, avec le message « Impossible d'appliquer un style avec
        symbologie à une couche avec un type de géométrie différent ».

        Deux sources, dans l'ordre de fiabilité :

        1. La balise <layerGeometryType>, écrite par QGIS et sans ambiguïté.

        2. À défaut, les symboles de PREMIER NIVEAU du rendu, et eux seuls.
           Parcourir root.iter("symbol") serait une erreur : cela ramène aussi
           les SOUS-SYMBOLES. Une MarkerLine contient un sous-symbole de type
           « marker », une SVGFill un sous-symbole « fill »… Un style de lignes
           truffé de MarkerLine passerait ainsi pour du ponctuel, et un style
           ponctuel à marqueurs remplis pour du surfacique. On retient donc le
           type MAJORITAIRE parmi les symboles de premier niveau, et non le
           premier trouvé selon un ordre de priorité arbitraire.
        """
        node = self.root.find(".//layerGeometryType")
        if node is not None:
            code = (node.text or "").strip()
            if code in self._QGIS_GEOMETRY_CODES:
                return self._QGIS_GEOMETRY_CODES[code]

        renderer = self.renderer
        top_level: List[ET.Element] = []
        if renderer is not None:
            for container in renderer.findall("symbols"):
                top_level.extend(container.findall("symbol"))
            for container in renderer.findall("source-symbol"):
                top_level.extend(container.findall("symbol"))

        counts = Counter((sym.get("type") or "").lower() for sym in top_level)
        counts.pop("", None)
        if counts:
            dominant = counts.most_common(1)[0][0]
            return self._SYMBOL_TO_GEOMETRY.get(dominant, "Polygon")
        return "Polygon"

    def geometry_candidates(self) -> List[str]:
        """
        Types géométriques à essayer, du plus probable au moins probable.

        Sert de filet : si loadNamedStyle refuse le premier, on tente les
        autres plutôt que de déclarer le style perdu.
        """
        first = self.geometry_type()
        return [first] + [g for g in ("Polygon", "LineString", "Point")
                          if g != first]

    def rules(self) -> List[Dict[str, Any]]:
        """
        Normalise les différents rendus QGIS en une liste de règles homogène :
        {name, filter, symbol, min_scale, max_scale}
        `filter` est une expression QGIS (traduite plus tard en filtre OGC).
        """
        r = self.renderer
        if r is None:
            return []
        rtype = self.renderer_type
        out: List[Dict[str, Any]] = []

        if rtype == "RuleRenderer":
            for rule in r.iter("rule"):
                if rule.find("rule") is not None and rule.get("symbol") is None:
                    continue                   # groupe de règles, pas une règle
                out.append({
                    "name": rule.get("label") or rule.get("key") or "",
                    "filter": rule.get("filter") or None,
                    "symbol": rule.get("symbol"),
                    # QGIS : visible si scalemindenom <= denominateur <= scalemaxdenom
                    # SLD  : visible si MinScaleDenominator <= denom < MaxScaleDenominator
                    # La correspondance est donc directe, sans inversion.
                    "min_scale": rule.get("scalemindenom"),
                    "max_scale": rule.get("scalemaxdenom"),
                })
        elif rtype == "categorizedSymbol":
            attr = r.findtext("attr") or r.get("attr") or ""
            for cat in r.iter("category"):
                if cat.get("render") == "false":
                    continue
                value = cat.get("value")
                if value in (None, "",):
                    flt = "ELSE"
                else:
                    flt = f'"{attr}" = \'{value}\''
                out.append({
                    "name": cat.get("label") or str(value),
                    "filter": flt,
                    "symbol": cat.get("symbol"),
                    "min_scale": None, "max_scale": None,
                })
        elif rtype == "graduatedSymbol":
            attr = r.findtext("attr") or r.get("attr") or ""
            for rng in r.iter("range"):
                if rng.get("render") == "false":
                    continue
                lo, hi = rng.get("lower"), rng.get("upper")
                out.append({
                    "name": rng.get("label") or f"{lo}-{hi}",
                    "filter": f'"{attr}" >= {lo} AND "{attr}" <= {hi}',
                    "symbol": rng.get("symbol"),
                    "min_scale": None, "max_scale": None,
                })
        else:                                   # singleSymbol et assimilés
            syms = self.symbols()
            first = next(iter(syms), None)
            out.append({
                "name": self.path.stem,
                "filter": None,
                "symbol": first,
                "min_scale": None, "max_scale": None,
            })
        return out

@dataclass
class HatchHint:
    """Description exacte d'une hachure QGIS, telle que lue dans le QML."""
    angle: float = 45.0
    distance_px: float = 10.0
    color: str = "#000000"
    opacity: float = 1.0
    width_px: float = 1.0
    offset_px: float = 0.0
    dasharray: Optional[str] = None


@dataclass
class RuleHints:
    """Indices attachés à une règle de rendu (identifiée par son libellé)."""
    rule_name: str
    hatches: List[HatchHint] = field(default_factory=list)
    svg_fills: List[Dict[str, Any]] = field(default_factory=list)
    point_patterns: List[Dict[str, Any]] = field(default_factory=list)
    marker_lines: List[Dict[str, Any]] = field(default_factory=list)
    #: Tirets personnalisés (use_custom_dash) lus dans le QML, dans l'ordre des
    #: SimpleLine de la règle. Le backend QGIS les PERD (voir SECTION 7, point I).
    dashes: List[str] = field(default_factory=list)

class HintExtractor:
    """
    Relit le QML source et produit, règle par règle, la description fidèle des
    constructions que bridge-style dégrade. C'est le « filet de sécurité » qui
    garantit ZÉRO PERTE de rendu en PHASE 4.
    """

    def extract(self, path: Path) -> Tuple[Dict[str, RuleHints], str]:
        doc = QmlDocument(path)
        symbols = doc.symbols()
        hints: Dict[str, RuleHints] = {}

        for rule in doc.rules():
            key = safe_stem(rule["name"] or path.stem)
            rh = hints.setdefault(key, RuleHints(rule_name=rule["name"] or path.stem))
            sym = symbols.get(str(rule.get("symbol")))
            if sym is None:
                continue
            for layer in sym.iter("layer"):
                cls = layer.get("class") or ""
                props = QmlDocument.layer_props(layer)

                if cls == "LinePatternFill":
                    rh.hatches.append(self._hatch_from_linepattern(layer, props))
                elif cls == "SimpleFill":
                    style = (props.get("style") or "solid").lower()
                    if style not in ("solid", "no"):
                        rh.hatches.append(self._hatch_from_qt_brush(props, style))
                elif cls == "SVGFill":
                    rh.svg_fills.append({
                        "svg": register_svg_reference(props.get("svgFile"),
                                                      "cnig_motif"),
                        "width_px": qgis_size_to_px(props.get("width"),
                                                    props.get("width_unit")) or 16.0,
                        "angle": float(props.get("angle") or 0),
                    })
                elif cls in ("PointPatternFill", "RandomMarkerFill"):
                    rh.point_patterns.append({
                        "dx": qgis_size_to_px(props.get("distance_x"),
                                              props.get("distance_x_unit")) or 10.0,
                        "dy": qgis_size_to_px(props.get("distance_y"),
                                              props.get("distance_y_unit")) or 10.0,
                    })
                elif cls == "SimpleLine":
                    dash = _dash_from_props(props, "line")
                    if props.get("use_custom_dash") in ("1", "true") and dash:
                        rh.dashes.append(dash)
                elif cls == "MarkerLine":
                    rh.marker_lines.append({
                        "interval": qgis_size_to_px(props.get("interval"),
                                                    props.get("interval_unit")) or 10.0,
                        "offset": qgis_size_to_px(props.get("offset"),
                                                  props.get("offset_unit")) or 0.0,
                        "placement": props.get("placement", "interval"),
                    })
        return hints, doc.geometry_type()

    # -------------------------------------------------------------- privées
    @staticmethod
    def _hatch_from_linepattern(layer: ET.Element,
                                props: Dict[str, str]) -> HatchHint:
        """
        Une LinePatternFill porte un SOUS-SYMBOLE de type ligne qui définit la
        couleur et l'épaisseur du trait de hachure. bridge-style ne lit que
        `sl.color()` : il perd l'épaisseur réelle et les tirets. On va chercher
        le sous-symbole nous-mêmes.
        """
        angle = float(props.get("angle") or 45)
        dist = qgis_size_to_px(props.get("distance"), props.get("distance_unit")) or 10.0
        off = qgis_size_to_px(props.get("offset"), props.get("offset_unit")) or 0.0

        color, opacity = qgis_color_to_hex(props.get("color") or props.get("line_color"))
        width = qgis_size_to_px(props.get("line_width"), props.get("line_width_unit")) or 1.0
        dash = None

        sub = layer.find("symbol")
        if sub is not None:
            for sublayer in sub.iter("layer"):
                if (sublayer.get("class") or "") != "SimpleLine":
                    continue
                sp = QmlDocument.layer_props(sublayer)
                c, o = qgis_color_to_hex(sp.get("line_color"))
                if c:
                    color, opacity = c, o
                w = qgis_size_to_px(sp.get("line_width"), sp.get("line_width_unit"))
                if w:
                    width = w
                if sp.get("use_custom_dash") in ("1", "true") and sp.get("customdash"):
                    dash = " ".join(
                        str(qgis_size_to_px(v, sp.get("customdash_unit")) or v)
                        for v in sp["customdash"].split(";")
                    )
                break

        return HatchHint(angle=angle, distance_px=dist,
                         color=color or "#000000", opacity=opacity,
                         width_px=width, offset_px=off, dasharray=dash)

    @staticmethod
    def _hatch_from_qt_brush(props: Dict[str, str], style: str) -> HatchHint:
        """Hachure issue d'une brosse Qt classique sur un SimpleFill."""
        color, opacity = qgis_color_to_hex(props.get("color"))
        angle = {"horizontal": 0.0, "vertical": 90.0,
                 "b_diagonal": 45.0, "f_diagonal": 135.0}.get(style, 45.0)
        return HatchHint(angle=angle, distance_px=10.0,
                         color=color or "#000000", opacity=opacity, width_px=1.0)

def _dash_from_props(p: Dict[str, str], prefix: str) -> Optional[str]:
    """
    Reconstitue un stroke-dasharray SLD à partir des propriétés QGIS.

    /!\\ Les valeurs sont ARRONDIES À L'ENTIER, et ce n'est pas un choix
    esthétique. sld/fromgeostyler.py::_lineSymbolizer() contient :

        if cap != "butt":
            tokens = [int(v) + EXTRA_GAP if i % 2 else int(v)
                      for i, v in enumerate(dasharray.split(" "))]

    `int("7.5595")` lève ValueError, ce qui fait échouer la conversion de
    TOUT le style. Sur le corpus PLU réel, 3 fichiers sur 8 tombaient ainsi
    (« invalid literal for int() with base 10: '22.6786' ») — dont le Style
    Étalon. Comme un dasharray SLD s'exprime en pixels, l'arrondi au pixel
    est visuellement neutre. (Défaut remonté en SECTION 7, point G.)
    """
    def fmt(values: Sequence[float]) -> str:
        return " ".join(str(max(1, int(round(v)))) for v in values)

    if p.get("use_custom_dash") in ("1", "true") and p.get("customdash"):
        unit = p.get("customdash_unit", "MM")
        values = [qgis_size_to_px(v, unit) for v in p["customdash"].split(";")]
        clean = [v for v in values if v is not None]
        return fmt(clean) if clean else None

    style = p.get(f"{prefix}_style") or ""
    width = qgis_size_to_px(p.get(f"{prefix}_width"), p.get(f"{prefix}_width_unit")) or 1.0
    patterns = {
        "dash": [4, 2], "dot": [1, 2], "dash dot": [4, 2, 1, 2],
        "dash dot dot": [4, 2, 1, 2, 1, 2],
    }
    if style in patterns:
        return fmt([v * width for v in patterns[style]])
    return None

#: Ordre imposé par l'XSD OGC SLD 1.0.0 (+ extensions GeoServer tolérées).
#: GeoServer valide en mode « Strict XSD » : un élément hors séquence fait
#: échouer l'import du style avec un message peu explicite.
XSD_ORDER: Dict[str, List[str]] = {
    "StyledLayerDescriptor": ["Name", "Title", "Abstract", "NamedLayer", "UserLayer"],
    "NamedLayer": ["Name", "Description", "LayerFeatureConstraints", "UserStyle"],
    "UserStyle": ["Name", "Title", "Abstract", "IsDefault", "FeatureTypeStyle"],
    "FeatureTypeStyle": ["Name", "Title", "Abstract", "FeatureTypeName",
                         "SemanticTypeIdentifier", "Rule", "VendorOption"],
    "Rule": ["Name", "Title", "Abstract", "LegendGraphic",
             "Filter", "ElseFilter",
             "MinScaleDenominator", "MaxScaleDenominator",
             "LineSymbolizer", "PolygonSymbolizer", "PointSymbolizer",
             "TextSymbolizer", "RasterSymbolizer"],
    "PointSymbolizer": ["Geometry", "Graphic", "VendorOption"],
    "LineSymbolizer": ["Geometry", "Stroke", "PerpendicularOffset", "VendorOption"],
    "PolygonSymbolizer": ["Geometry", "Fill", "Stroke", "VendorOption"],
    "TextSymbolizer": ["Geometry", "Label", "Font", "LabelPlacement", "Halo",
                       "Fill", "Graphic", "Priority", "VendorOption"],
    "Graphic": ["ExternalGraphic", "Mark", "Opacity", "Size", "Rotation",
                "AnchorPoint", "Displacement"],
    "Mark": ["WellKnownName", "Fill", "Stroke"],
    "ExternalGraphic": ["OnlineResource", "InlineContent", "Format",
                        "ColorReplacement"],
    "Fill": ["GraphicFill", "CssParameter"],
    "Stroke": ["GraphicFill", "GraphicStroke", "CssParameter"],
    "Halo": ["Radius", "Fill"],
    "LabelPlacement": ["PointPlacement", "LinePlacement"],
    "PointPlacement": ["AnchorPoint", "Displacement", "Rotation"],
    "LinePlacement": ["PerpendicularOffset"],
}

#: Balises et préfixes propriétaires QGIS / ESRI parfois recopiés par les
#: convertisseurs et systématiquement rejetés par la validation stricte.
PROPRIETARY_TAGS: Tuple[str, ...] = (
    "qgis", "renderer-v2", "layerGeometryType", "customproperties",
    "data_defined_properties", "effect", "prop", "Option", "blendMode",
    "featureBlendMode", "labeling", "LayerConfiguration", "esri",
    "CIMSymbolReference", "SymbolLayerReference", "sld:UserStyleExtension",
)

class SldPostProcessor:
    """
    PHASE 4 — le cœur de la garantie « zéro perte de rendu ».

    Enchaînement appliqué à chaque SLD :
      1. Nettoyage des espaces de noms et des balises propriétaires.
      2. Réécriture des OnlineResource / WellKnownName file:// en svg/cnig/*.
      3. Correction des WellKnownName invalides (b_diagonal, dense3, ...).
      4. Réinjection des hachures fidèles à partir de l'index d'indices QML.
      5. Injection des <VendorOption> GeoServer (motifs et étiquetage).
      6. Suppression des éléments vides qui provoquent des rendus parasites
         (<Stroke/> vide = contour noir 1px non désiré dans GeoServer).
      7. Remise en ordre XSD strict de tous les enfants.
      8. Sérialisation UTF-8 SANS BOM avec déclaration XML explicite.
    """

    SLD_NS = "http://www.opengis.net/sld"
    OGC_NS = "http://www.opengis.net/ogc"
    XLINK_NS = "http://www.w3.org/1999/xlink"

    def __init__(self, svg_index: Dict[str, str], vendor: Dict[str, Dict[str, str]],
                 inject_hatches: bool = True,
                 like_match_case_insensible: bool = True) -> None:
        self.svg_index = svg_index
        self.vendor = vendor
        self.inject_hatches = inject_hatches
        #: matchCase="false" sur les PropertyIsLike. Vrai par défaut : sans
        #: lui, les filtres des SUP ne ramènent aucun objet (voir
        #: _fix_property_is_like). À mettre à faux si le style doit passer un
        #: validateur XSD 1.0 sans la moindre extension — au prix du rendu.
        self.like_match_case_insensible = like_match_case_insensible
        self.stats: Counter = Counter()

    # ------------------------------------------------------------------ API
    def process(self, sld_text: str, hints: Dict[str, RuleHints],
                geometry: str) -> str:
        root = self._parse(sld_text)

        self._strip_proprietary(root)
        self._fix_property_is_like(root)
        self._rewrite_svg_references(root)
        self._fix_wellknown_names(root)
        if self.inject_hatches:
            self._repair_hatches(root, hints)
            self._repair_dashes(root, hints)
        self._inject_vendor_options(root, geometry)
        # Le repli passe AVANT la suppression des éléments vides : une
        # expression constante repliée laisse un élément porteur d'une valeur,
        # pas un élément vide qu'il faudrait ensuite jeter.
        self._fold_constant_expressions(root)
        self._drop_empty_elements(root)
        self._reorder(root)

        return self._serialize(root)

    # -------------------------------------------------------------- parsing
    def _parse(self, text: str) -> ET.Element:
        """
        Parse en supprimant les espaces de noms pour simplifier les XPath, puis
        on les rétablit à la sérialisation. C'est la technique la plus robuste
        face aux SLD hétérogènes (avec ou sans préfixe sld:).
        """
        if text.startswith("\ufeff"):
            text = text[1:]
        root = ET.fromstring(text.encode("utf-8"))
        for el in root.iter():
            if isinstance(el.tag, str) and "}" in el.tag:
                el.tag = el.tag.split("}", 1)[1]
            for attr in list(el.attrib):
                if "}" in attr:
                    local = attr.split("}", 1)[1]
                    ns = attr.split("}", 1)[0].lstrip("{")
                    # On conserve xlink:href sous forme préfixée.
                    newname = f"xlink:{local}" if ns == self.XLINK_NS else local
                    el.attrib[newname] = el.attrib.pop(attr)
        return root

    # --------------------------------------------------- 1. nettoyage strict
    def _strip_proprietary(self, root: ET.Element) -> None:
        for parent in list(root.iter()):
            for child in list(parent):
                tag = child.tag if isinstance(child.tag, str) else ""
                if tag in PROPRIETARY_TAGS or tag.startswith(("qgis", "esri", "CIM")):
                    parent.remove(child)
                    self.stats["balises_proprietaires_supprimees"] += 1
        # Attributs propriétaires résiduels
        for el in root.iter():
            for attr in list(el.attrib):
                if attr.startswith(("qgis", "esri", "arcgis")):
                    del el.attrib[attr]
                    self.stats["attributs_proprietaires_supprimes"] += 1

    # ------------------------------------- 2. réécriture des références SVG
    def _rewrite_svg_references(self, root: ET.Element) -> None:
        # (a) ExternalGraphic / OnlineResource
        for online in root.iter("OnlineResource"):
            for key in ("xlink:href", "href"):
                if key not in online.attrib:
                    continue
                new = resoudre_href_svg(online.attrib[key],
                                                        self.svg_index)
                if new:
                    online.attrib.pop("href", None)
                    online.set("xlink:href", new)
                    online.set("xlink:type", "simple")
                    self.stats["onlineresource_reecrits"] += 1
                break

        # (b) <Mark><WellKnownName>file://xxx.svg</WellKnownName></Mark>
        #     -> converti en <ExternalGraphic> conforme.
        for graphic in root.iter("Graphic"):
            for mark in list(graphic.findall("Mark")):
                wkn = mark.find("WellKnownName")
                if wkn is None or not (wkn.text or "").lower().endswith(".svg"):
                    continue
                new_href = resoudre_href_svg(wkn.text, self.svg_index)
                if not new_href:
                    continue
                ext = ET.Element("ExternalGraphic")
                ET.SubElement(ext, "OnlineResource", {
                    "xlink:type": "simple", "xlink:href": new_href})
                fmt = ET.SubElement(ext, "Format")
                fmt.text = "image/svg+xml"
                graphic.remove(mark)
                graphic.insert(0, ext)
                self.stats["marks_svg_convertis_en_externalgraphic"] += 1

    # ------------------- 2-bis. attributs obligatoires de PropertyIsLike
    def _fix_property_is_like(self, root: ET.Element) -> None:
        """
        Complète les attributs obligatoires de <PropertyIsLike>.

        ATTENTION AU NUMÉRO DE VERSION. SLD 1.0.0 s'appuie sur OGC Filter
        Encoding 1.0.0, dont le filter.xsd déclare TROIS attributs requis :

            <xsd:attribute name="wildCard"   type="xsd:string" use="required"/>
            <xsd:attribute name="singleChar" type="xsd:string" use="required"/>
            <xsd:attribute name="escape"     type="xsd:string" use="required"/>

        C'est bien « escape », et non « escapeChar » : ce dernier est
        l'orthographe introduite par Filter 1.1, avec matchCase. Écrire la
        graphie 1.1 dans un document 1.0 laisse l'attribut requis absent et
        ajoute un attribut non déclaré — deux violations pour le prix d'une.
        GeoServer les tolère, un validateur XSD non.

        bridgestyle, lui, ne pose que wildCard :

            if name == OGC_IS_LIKE:
                elem.attrib["wildCard"] = "%"

        (Le parseur SLD de l'écosystème GeoStyler en TypeScript écrit bien les
        trois, avec la bonne graphie : le correctif existe déjà de ce côté-là.)

        matchCase est un cas à part, traité plus bas.
        """
        for noeud in root.iter("PropertyIsLike"):
            # Graphie 1.1 éventuellement héritée d'un traitement antérieur.
            ancien = noeud.attrib.pop("escapeChar", None)
            noeud.attrib.setdefault("wildCard", "%")
            noeud.attrib.setdefault("singleChar", "_")
            noeud.attrib.setdefault("escape", ancien or "\\")

            # matchCase="false" n'appartient PAS au vocabulaire Filter 1.0 :
            # c'est une extension que GeoServer comprend. On la conserve tout
            # de même, parce que la sémantique source l'exige — les filtres
            # QGIS comparent via lower(), et les codes de servitude sont saisis
            # en majuscules dans les données (« AC1-... »). La retirer
            # produirait un style formellement pur qui n'afficherait RIEN.
            #
            # Le choix est donc assumé et, surtout, RENDU VISIBLE : la phase 6
            # le compte et le nomme, au lieu de conclure à une conformité
            # stricte qui serait fausse.
            if self.like_match_case_insensible:
                noeud.attrib.setdefault("matchCase", "false")
                self.stats["propertyislike_matchcase_geoserver"] += 1
            else:
                noeud.attrib.pop("matchCase", None)
            self.stats["propertyislike_completes"] += 1

    # ------------------------- 3. WellKnownName invalides (dette bridge-style)
    def _fix_wellknown_names(self, root: ET.Element) -> None:
        for wkn in root.iter("WellKnownName"):
            value = (wkn.text or "").strip()
            if not value or value.startswith(("shape://", "file://")):
                continue
            if value.lower() in QT_BRUSH_TO_WKN:
                replacement = QT_BRUSH_TO_WKN[value.lower()]
                if replacement:
                    wkn.text = replacement
                    self.stats["wellknownname_qt_corriges"] += 1
                continue
            if value.lower() in NOMS_MARQUEURS_QGIS_VERS_WKN:
                wkn.text = NOMS_MARQUEURS_QGIS_VERS_WKN[value.lower()]
                self.stats["wellknownname_formes_qgis_corrigees"] += 1
                continue
            valid = {"circle", "square", "triangle", "star", "cross", "x",
                     "arrow", "hatch"}
            if value.lower() not in valid:
                wkn.text = "square"
                self.stats["wellknownname_inconnus_remplaces"] += 1

    # -------------------------------------- 4. réparation fidèle des hachures
    def _repair_hatches(self, root: ET.Element, hints: Dict[str, RuleHints]) -> None:
        """
        Pour chaque règle du SLD, on retrouve la règle QML correspondante via
        son libellé normalisé, et l'on remplace/complète le GraphicFill par une
        hachure GeoServer exacte (angle, espacement, épaisseur, couleur).

        Rappel du problème corrigé — bridgestyle/qgis/togeostyler.py :
            def _hatchMarkerForAngle(angle):
                quadrant = math.floor(((angle + 22.5) % 180) / 45.)
                return [...4 valeurs...][quadrant]
        L'angle exact est arrondi au multiple de 45 deg ; l'épaisseur réelle du
        trait (sous-symbole SimpleLine) et le décalage sont purement ignorés.
        """
        for rule in root.iter("Rule"):
            key = self._rule_key(rule)
            rh = hints.get(key)
            if rh is None or not rh.hatches:
                continue
            polys = rule.findall("PolygonSymbolizer")
            if not polys:
                continue
            for poly, hatch in zip(polys, rh.hatches):
                self._apply_hatch(poly, hatch)
                self.stats["hachures_reparees"] += 1

    def _repair_dashes(self, root: ET.Element, hints: Dict[str, RuleHints]) -> None:
        """
        Réinjecte les tirets personnalisés (`use_custom_dash` de QGIS) que le
        backend QGIS perd totalement.

        Défaut corrigé — bridgestyle/qgis/togeostyler.py::_lineSymbolizer() :
        la fonction ne lit QUE la propriété `line_style` et applique une table
        de motifs figés ("8 5", "3 5"...). La propriété `customdash`, qui porte
        le motif réel, n'est jamais consultée. Pire : quand `use_custom_dash`
        vaut 1, QGIS laisse `line_style` à « solid », si bien que la branche
        `elif lineStyle != "solid"` n'est même pas atteinte — la ligne ressort
        PLEINE. Sur le corpus PLU du CNIG, les 8 fichiers utilisent des tirets
        personnalisés. (Défaut remonté en SECTION 7, point I.)
        """
        for rule in root.iter("Rule"):
            rh = hints.get(self._rule_key(rule))
            if rh is None or not rh.dashes:
                continue
            lines = rule.findall("LineSymbolizer")
            for line, dash in zip(lines, rh.dashes):
                stroke = line.find("Stroke")
                if stroke is None:
                    continue
                existing = stroke.find("CssParameter[@name='stroke-dasharray']")
                if existing is not None and (existing.text or "").strip():
                    continue          # bridge-style a déjà produit un motif
                _css(stroke, "stroke-dasharray", dash)
                self.stats["tirets_personnalises_reinjectes"] += 1

    @staticmethod
    def _rule_key(rule: ET.Element) -> str:
        """Clé de rapprochement SLD <-> QML (libellé normalisé)."""
        for tag in ("Title", "Name"):
            el = rule.find(tag)
            if el is not None and (el.text or "").strip():
                return safe_stem(el.text.strip())
        return ""

    def _apply_hatch(self, poly: ET.Element, hatch: HatchHint) -> None:
        wkn, residual = hatch_wkn_for_angle(hatch.angle)

        # Construction du GraphicFill exact
        graphic = ET.Element("Graphic")
        mark = ET.SubElement(graphic, "Mark")
        _sub(mark, "WellKnownName", wkn)
        stroke = ET.SubElement(mark, "Stroke")
        _css(stroke, "stroke", hatch.color)
        _css(stroke, "stroke-width", f"{hatch.width_px:g}")
        _css(stroke, "stroke-opacity", f"{hatch.opacity:g}")
        if hatch.dasharray:
            _css(stroke, "stroke-dasharray", hatch.dasharray)
        # Sous GeoServer, <Size> d'une marque shape:// == l'espacement des traits
        _sub(graphic, "Size", f"{max(1.0, hatch.distance_px):g}")
        if abs(residual) > 0.5:
            _sub(graphic, "Rotation", f"{residual:g}")

        # On remplace le Fill/GraphicFill existant s'il y en a un, sinon on
        # insère un nouveau Fill AVANT le Stroke du polygone (ordre XSD).
        target_fill = None
        for fill in poly.findall("Fill"):
            if fill.find("GraphicFill") is not None:
                target_fill = fill
                break
        if target_fill is None:
            target_fill = ET.Element("Fill")
            stroke_el = poly.find("Stroke")
            idx = list(poly).index(stroke_el) if stroke_el is not None else len(poly)
            poly.insert(idx, target_fill)
        else:
            for child in list(target_fill):
                target_fill.remove(child)

        gfill = ET.SubElement(target_fill, "GraphicFill")
        gfill.append(graphic)

        # graphic-margin = 0 : sans cela GeoServer ajoute un espacement propre
        # et les hachures « respirent » trop par rapport au rendu QGIS.
        self._set_vendor_option(poly, "graphic-margin", "0")
        if abs(hatch.offset_px) > 1e-6:
            # Décalage de hachure (propriété « offset » de LinePatternFill) :
            # SLD 1.0 n'a pas d'équivalent direct. On l'approche par une marge
            # haute, seule forme acceptée par GeoServer (valeurs >= 0, ordre
            # CSS « haut droite bas gauche »).
            self._set_vendor_option(
                poly, "graphic-margin", f"{abs(hatch.offset_px):g} 0 0 0")

    # ------------------------------------ 5. VendorOptions GeoServer généraux
    def _inject_vendor_options(self, root: ET.Element, geometry: str) -> None:
        # --- motifs surfaciques -----------------------------------------
        for poly in root.iter("PolygonSymbolizer"):
            has_graphic_fill = any(f.find("GraphicFill") is not None
                                   for f in poly.findall("Fill"))
            if not has_graphic_fill:
                continue
            for name, value in self.vendor.get("polygon_graphicfill", {}).items():
                if self._get_vendor_option(poly, name) is None:
                    self._set_vendor_option(poly, name, value)
                    self.stats["vendoroptions_injectees"] += 1

        # --- étiquetage ---------------------------------------------------
        options = dict(self.vendor.get("text", {}))
        if geometry == "LineString":
            options.update(self.vendor.get("text_line", {}))
            options.pop("autoWrap", None)          # incompatible avec followLine
        elif geometry == "Polygon":
            options.update(self.vendor.get("text_polygon", {}))

        for text in root.iter("TextSymbolizer"):
            if text.find("VendorOption[@name='followLine']") is not None:
                options.pop("autoWrap", None)
            for name, value in options.items():
                if self._get_vendor_option(text, name) is None:
                    self._set_vendor_option(text, name, value)
                    self.stats["vendoroptions_injectees"] += 1

    @staticmethod
    def _get_vendor_option(parent: ET.Element, name: str) -> Optional[ET.Element]:
        for vo in parent.findall("VendorOption"):
            if vo.get("name") == name:
                return vo
        return None

    def _set_vendor_option(self, parent: ET.Element, name: str, value: str) -> None:
        existing = self._get_vendor_option(parent, name)
        if existing is not None:
            existing.text = value
            return
        vo = ET.SubElement(parent, "VendorOption", {"name": name})
        vo.text = value

    # ------------------------------------------- 6. suppression des vides
    # ------------------------------- 6-bis. repli des expressions constantes
    def _fold_constant_expressions(self, root: ET.Element) -> None:
        """
        Remplace une arithmétique sur littéraux par son résultat.

        Le producteur QGIS de bridgestyle exprime volontiers une taille réduite
        de moitié ainsi :

            <Size><ogc:Div><ogc:Literal>15.0</ogc:Literal>
                           <ogc:Literal>2</ogc:Literal></ogc:Div></Size>

        C'est valide, GeoServer sait l'évaluer. Mais c'est une expression là où
        un nombre suffit : elle alourdit le style, se prête mal à la relecture
        humaine, et tout consommateur SLD un peu juste sur les expressions la
        rendra de travers sans prévenir. Comme les deux opérandes sont connues à
        la génération, autant faire le calcul ici.

        Seules les opérations dont TOUS les opérandes sont des littéraux
        numériques sont repliées : dès qu'un PropertyName ou une Function
        apparaît, l'expression dépend des données et reste intacte.
        """
        operations = {"Add": lambda a, b: a + b, "Sub": lambda a, b: a - b,
                      "Mul": lambda a, b: a * b, "Div": lambda a, b: a / b}

        def valeur_constante(noeud: ET.Element) -> Optional[float]:
            """Retourne la valeur si le sous-arbre est entièrement constant."""
            balise = noeud.tag if isinstance(noeud.tag, str) else ""
            if balise == "Literal":
                if len(noeud):
                    return None
                try:
                    return float((noeud.text or "").strip())
                except ValueError:
                    return None
            operation = operations.get(balise)
            if operation is None or len(noeud) != 2:
                return None
            gauche = valeur_constante(noeud[0])
            droite = valeur_constante(noeud[1])
            if gauche is None or droite is None:
                return None
            if balise == "Div" and droite == 0:
                return None
            try:
                return operation(gauche, droite)
            except (ZeroDivisionError, OverflowError, ValueError):
                return None

        for parent in list(root.iter()):
            balise_parent = parent.tag if isinstance(parent.tag, str) else ""
            if balise_parent not in AUDIT_NUMERIQUES or len(parent) != 1:
                continue
            resultat = valeur_constante(parent[0])
            if resultat is None:
                continue
            parent.remove(parent[0])
            # « %g » évite 7.5000000001 comme 7.500000, et rend « 8 » plutôt
            # que « 8.0 » quand le résultat est entier.
            parent.text = f"{round(resultat, 4):g}"
            self.stats["expressions_constantes_repliees"] += 1

    def _drop_empty_elements(self, root: ET.Element) -> None:
        """
        Deux pièges classiques des SLD générés :
          * <Stroke/> vide  -> GeoServer dessine un contour noir de 1 px.
          * <Size/> / <Rotation/> / <Opacity/> vides -> invalides (type double).
        """
        empties = ("Size", "Rotation", "Opacity", "PerpendicularOffset",
                   "Radius", "DisplacementX", "DisplacementY",
                   "AnchorPointX", "AnchorPointY", "MinScaleDenominator",
                   "MaxScaleDenominator", "Label", "Title", "Name")
        for parent in list(root.iter()):
            for child in list(parent):
                tag = child.tag
                if tag in empties and not (child.text or "").strip() and len(child) == 0:
                    parent.remove(child)
                    self.stats["elements_vides_supprimes"] += 1
                elif tag in ("Stroke", "Fill") and len(child) == 0 \
                        and not (child.text or "").strip():
                    parent.remove(child)
                    self.stats["stroke_fill_vides_supprimes"] += 1
                elif tag == "CssParameter" and (child.text or "").strip() in ("None", ""):
                    if len(child) == 0:
                        parent.remove(child)
                        self.stats["cssparameter_nuls_supprimes"] += 1

    # --------------------------------------------- 7. remise en ordre XSD
    def _reorder(self, root: ET.Element) -> None:
        for el in root.iter():
            order = XSD_ORDER.get(el.tag if isinstance(el.tag, str) else "")
            if not order:
                continue
            index = {tag: i for i, tag in enumerate(order)}
            children = list(el)
            # tri stable : les éléments inconnus gardent leur position relative
            # et sont placés à la fin (GeoServer les ignore plutôt que d'échouer)
            children.sort(key=lambda c: index.get(
                c.tag if isinstance(c.tag, str) else "", len(order)))
            if children != list(el):
                for child in list(el):
                    el.remove(child)
                el.extend(children)
                self.stats["elements_reordonnes"] += 1

    # ----------------------------------- 8. sérialisation UTF-8 sans BOM
    def _serialize(self, root: ET.Element) -> str:
        # Le « déballage » des espaces de noms a transformé xsi:schemaLocation
        # en schemaLocation : on supprime ce doublon avant de le rétablir.
        for stale in ("schemaLocation", "xmlns", "xsi", "ogc", "xlink"):
            root.attrib.pop(stale, None)
        root.set("version", "1.0.0")
        root.set("xmlns", self.SLD_NS)
        root.set("xmlns:ogc", self.OGC_NS)
        root.set("xmlns:xlink", self.XLINK_NS)
        root.set("xmlns:xsi", "http://www.w3.org/2001/XMLSchema-instance")
        root.set("xsi:schemaLocation",
                 "http://www.opengis.net/sld "
                 "http://schemas.opengis.net/sld/1.0.0/StyledLayerDescriptor.xsd")

        # Les balises ogc: doivent retrouver leur préfixe après le « déballage »
        for el in root.iter():
            if isinstance(el.tag, str) and el.tag in OGC_ELEMENTS:
                el.tag = f"ogc:{el.tag}"

        raw = ET.tostring(root, encoding="unicode", method="xml")
        pretty = _pretty_xml(raw)
        # UTF-8 STRICT SANS BOM : la déclaration est écrite à la main car
        # ElementTree ne permet pas de contrôler finement l'en-tête.
        if pretty.startswith("<?xml"):
            pretty = pretty.split("?>", 1)[1].lstrip("\r\n")
        return '<?xml version="1.0" encoding="UTF-8"?>\n' + pretty

#: Éléments appartenant à l'espace de noms OGC Filter (préfixe ogc:).
OGC_ELEMENTS: Set[str] = {
    "Filter", "And", "Or", "Not", "PropertyName", "Literal", "Function",
    "PropertyIsEqualTo", "PropertyIsNotEqualTo", "PropertyIsLessThan",
    "PropertyIsGreaterThan", "PropertyIsLessThanOrEqualTo",
    "PropertyIsGreaterThanOrEqualTo", "PropertyIsLike", "PropertyIsNull",
    "PropertyIsBetween", "LowerBoundary", "UpperBoundary",
    "Add", "Sub", "Mul", "Div",
}

#: Éléments dont le contenu doit être un nombre — copie locale de la
#: constante homonyme du CLI (section PHASE 6, audit), nécessaire à
#: `SldPostProcessor._fold_constant_expressions()`. Dupliquée plutôt que
#: partagée avec le CLI pour ne pas introduire de dépendance dans l'autre
#: sens (styleforge_core -> cnig_qml2sld_geoserver.py) : la migration de
#: l'audit PHASE 6 lui-même n'est pas dans le périmètre de ce chantier.
AUDIT_NUMERIQUES = {
    "Size", "Rotation", "Opacity", "MinScaleDenominator", "MaxScaleDenominator",
    "PerpendicularOffset", "Radius", "DisplacementX", "DisplacementY",
    "AnchorPointX", "AnchorPointY", "Priority",
}

def _sub(parent: ET.Element, tag: str, text: str) -> ET.Element:
    el = ET.SubElement(parent, tag)
    el.text = text
    return el

def _css(parent: ET.Element, name: str, value: str) -> ET.Element:
    el = ET.SubElement(parent, "CssParameter", {"name": name})
    el.text = value
    return el

def _pretty_xml(raw: str) -> str:
    """Indentation lisible, sans lignes vides parasites."""
    from xml.dom import minidom
    dom = minidom.parseString(raw)
    pretty = dom.toprettyxml(indent="  ")
    lines = [line for line in pretty.splitlines() if line.strip()]
    return "\n".join(lines) + "\n"


# ==============================================================================
#  API PUBLIQUE DU MODULE
# ==============================================================================

def post_traiter_sld(sld_text: str, chemin_qml: Any, *,
                     index_svg: Dict[str, str],
                     vendor: Optional[Dict[str, Dict[str, str]]] = None,
                     injecter_hachures: bool = True,
                     like_match_case_insensible: bool = True,
                     avertissements: Optional[List[str]] = None,
                     ) -> Tuple[str, Counter]:
    """
    PHASE 4, en une seule fonction : relit `chemin_qml` pour en extraire les
    indices de rendu que l'écrivain SLD appelant (bridgestyle via le CLI, ou
    `styleforge_core.writers.sld.ecrire_sld`) ne porte pas lui-même — angle et
    épaisseur réelle des hachures, tirets personnalisés (`use_custom_dash`) —
    puis corrige `sld_text` : nettoyage des balises propriétaires QGIS/ESRI,
    réécriture des références SVG vers `index_svg`, correction des
    WellKnownName invalides, réparation fidèle des hachures et tirets,
    injection des VendorOption GeoServer, repli des expressions constantes,
    suppression des éléments vides, remise en ordre XSD stricte.

    Paramètres :
      sld_text               Le document SLD 1.0.0 déjà écrit (texte XML), tel
                             quel — fonctionne quel que soit l'écrivain qui l'a
                             produit, voir la docstring du module.
      chemin_qml             Chemin du fichier .qml SOURCE (pas le SLD) : ce
                             module le relit une seconde fois, indépendamment
                             de l'écrivain, pour les indices non portés par le
                             pivot geostyler-style (voir `HintExtractor`).
      index_svg               {nom_fichier.lower(): "svg/cnig/..."} déjà
                             déployé par l'appelant — jamais construit ici.
      vendor                 VendorOption GeoServer par défaut à injecter
                             (hachures, étiquetage). `None` -> aucune
                             VendorOption injectée (dict vide) plutôt qu'un
                             jeu de valeurs deviné : l'appelant doit fournir
                             ses propres valeurs par défaut, p. ex. en
                             réutilisant celles du CLI
                             (`cnig_qml2sld_geoserver.VENDOR_DEFAULTS`) s'il
                             veut un comportement identique.
      injecter_hachures       Si faux, les hachures/tirets ne sont PAS
                             réinjectés (le reste des correctifs s'applique
                             quand même) — correspond à `--no-hatch-fix` du
                             CLI.
      avertissements          Liste optionnelle dans laquelle un échec de
                             relecture du QML (fichier absent, XML invalide)
                             est consigné comme message EXPLICITE, plutôt que
                             de faire échouer tout le post-traitement : dans
                             ce cas, les hachures/tirets ne sont simplement
                             pas réparés pour ce document (le reste des
                             correctifs — nettoyage, SVG, XSD... —
                             s'applique toujours).

    Retourne (sld_corrige, stats) : `stats` est un `collections.Counter`
    dénombrant chaque correctif appliqué (mêmes clés que
    `SldPostProcessor.stats` historiquement affichées par le CLI en fin de
    PHASE 4 : "hachures_reparees", "vendoroptions_injectees", etc.) — plus
    "relecture_qml_echouee" (0 ou 1) si l'extraction des indices a échoué.
    """
    chemin_qml = Path(chemin_qml)
    extractor = HintExtractor()
    echec_lecture: Optional[Exception] = None
    try:
        hints, geometry = extractor.extract(chemin_qml)
    except Exception as exc:                                   # noqa: BLE001
        hints, geometry = {}, "Polygon"
        echec_lecture = exc

    post = SldPostProcessor(
        index_svg, vendor if vendor is not None else {},
        inject_hatches=injecter_hachures,
        like_match_case_insensible=like_match_case_insensible,
    )
    final_xml = post.process(sld_text or "", hints, geometry)

    if echec_lecture is not None:
        post.stats["relecture_qml_echouee"] += 1
        message = f"Indices QML non extraits ({chemin_qml.name}) : {echec_lecture}"
        if avertissements is not None:
            avertissements.append(message)

    return final_xml, post.stats
