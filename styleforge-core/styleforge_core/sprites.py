#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
styleforge_core.sprites — fabrication de la feuille de sprites Mapbox GL
(sprite.png + sprite.json, et leurs équivalents @2x) à partir des vignettes
nécessaires à un document MBStyle : pictogrammes SVG, motifs de hachure
« shape://... », marques simples, glyphes de police (FontMarker).

Origine : migré DEPUIS `cnig_qml2sld_geoserver.py` (où il vivait sous le nom
`SpriteRegistry`, section PHASE 5) vers `styleforge-core`, pour la MÊME
raison que `styleforge_core.writers.sld_posttraitement` (PHASE 4) : partager
exactement le même code entre le CLI et le plugin QGIS (`qgis-plugin/`)
plutôt que deux copies qui dériveraient l'une de l'autre.

Ce module reste SANS DÉPENDANCE PyQGIS au sens du projet : il importe
`qgis.PyQt` (ou, à défaut, `PyQt5`/`PyQt6` nus) uniquement pour piloter Qt —
jamais `qgis.core` ni aucune API QGIS. Le repli `PyQt5`/`PyQt6` permet de
l'utiliser et de le tester hors de QGIS (cas du CLI, exécuté par un
interpréteur Python « nu » dans son backend 'styleforge'/'standalone').

DIFFÉRENCE DÉLIBÉRÉE avec l'original ligne pour ligne, pour rester utilisable
tel quel DANS QGIS, sans rien retirer de la sûreté côté CLI :

  * `build()` accepte désormais un paramètre optionnel `pump_ui` (un rappel
    sans argument) plutôt que d'appeler une fonction `pump_ui()` du CLI
    directement — ce module ne connaît pas (et ne doit pas connaître)
    l'infrastructure console du CLI. Le CLI continue de passer SA fonction
    `pump_ui` existante ; le plugin QGIS peut en passer une équivalente, ou
    omettre le paramètre (aucun rafraîchissement forcé de l'interface —
    acceptable pour un lot de quelques dizaines de couches).

  * La sonde par sous-processus (`_qguiapp_disponible`) qui protège le CLI
    contre un SIGABRT en tentant de créer une QGuiApplication sur une
    plate-forme Qt inutilisable N'EST JAMAIS SOLLICITÉE à l'intérieur de
    QGIS : `QGuiApplication.instance()` y est TOUJOURS déjà non None (QGIS
    est lui-même une application Qt), donc `build()` prend directement la
    branche « application déjà instanciée » sans jamais construire ni sonder
    quoi que ce soit — ce comportement existait déjà dans le code original,
    il n'a pas été modifié ici, seulement confirmé pertinent pour le plugin.

Utilisation (identique au CLI, voir son PHASE 5 pour l'exemple complet) :

    from styleforge_core.sprites import SpriteRegistry

    sprites = SpriteRegistry(taille_px)

    def resoudre_sprite(jeton: str) -> str | None:
        ... # voir register_svg / register_shape / register_font_glyph
        return sprites.register_svg(jeton, dossier_svg_deja_deploye)

    document_json = ecrire_mbstyle(pivot, resoudre_sprite=resoudre_sprite, ...)
    rapport = sprites.build(dossier_sortie)   # sprite.png/@2x + .json

IMPORTANT — ORDRE D'APPEL : `register_svg(reference, svg_dir)` vérifie
IMMÉDIATEMENT que le fichier existe dans `svg_dir` (`candidate.is_file()`) :
les SVG embarqués/copiés doivent donc déjà être DÉPLOYÉS SUR DISQUE avant de
générer le MBStyle (donc avant d'appeler `resoudre_sprite`), pas seulement
enregistrés en mémoire — même séquence que le CLI (PHASE 3b déploie les SVG
avant que PHASE 5 construise les sprites).
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from styleforge_core.writers.sld_posttraitement import safe_stem

#: Reconnaît toute occurrence restante de la convention GeoServer "Parametric
#: SVG" ('param(nom)', avec ou sans valeur de repli séparée par un espace,
#: ex. 'param(outline-width) 0') — utilisé par _neutraliser_svg_parametrique
#: UNIQUEMENT pour neutraliser ce qui reste APRÈS le remplacement explicite
#: de 'fill="param(fill)"' (le seul cas qui pilote réellement le masque
#: blanc). Confirmé exhaustif sur le corpus CNIG (examples/qml) : les seules
#: variantes observées sont fill, fill-opacity, stroke(=outline),
#: stroke-opacity(=outline-opacity, repli "1") et stroke-width(=outline-
#: width, repli "0", parfois sans repli).
_MOTIF_FALLBACK_PARAM = re.compile(r"param\([\w-]+\)(?:\s+([^\"]+))?")


def _neutraliser_svg_parametrique(contenu: str) -> str:
    """Transforme un SVG « paramétrique » QGIS/GeoServer (voir
    SpriteRegistry._MOTIF_SVG_PARAMETRIQUE) en un masque opaque BLANC
    exploitable comme sprite Mapbox GL "sdf" (teinté au rendu par
    icon-color) :

      1. fill="param(fill)" (forme EXACTE, sans repli — la seule confirmée
         pour cet attribut) -> fill="#ffffff" : c'est elle qui pilote la
         silhouette du masque, peu importe la couleur réellement voulue
         (transmise séparément via icon-color, pas figée dans le sprite).
      2. fill-opacity="param(fill-opacity)" (sans repli observé) -> "1" :
         le masque doit rester PLEINEMENT opaque pour que icon-color le
         teinte uniformément (l'opacité réelle, si besoin, reste portée par
         icon-opacity côté MBStyle, indépendamment du sprite).
      3. stroke="param(outline)" (sans repli observé) -> "none" : le
         contour n'est PAS reproduit dans le masque — cohérent avec le
         correctif SLD (task #46 de ce projet), qui ne transmet lui non
         plus que 'fill' via le mécanisme GeoServer Parametric SVG, jamais
         'outline', et avec stroke-width replié à 0 dans l'écrasante
         majorité des occurrences du corpus (contour invisible par défaut).
      4. Tout 'param(nom) repli' restant (stroke-opacity, stroke-width, ou
         toute variante future AVEC repli documenté) -> repli pris
         LITTÉRALEMENT : exactement la sémantique GeoServer "Parametric
         SVG" (paramètre non fourni -> valeur de repli), pas une
         approximation inventée ici.

    Portée délibérément bornée aux variantes confirmées sur le corpus CNIG
    (examples/qml) : fill, fill-opacity, stroke, stroke-opacity,
    stroke-width — voir _MOTIF_FALLBACK_PARAM."""
    contenu = contenu.replace(SpriteRegistry._MOTIF_SVG_PARAMETRIQUE, 'fill="#ffffff"')
    contenu = contenu.replace('fill-opacity="param(fill-opacity)"', 'fill-opacity="1"')
    contenu = contenu.replace('stroke="param(outline)"', 'stroke="none"')
    contenu = _MOTIF_FALLBACK_PARAM.sub(lambda m: m.group(1) or "0", contenu)
    return contenu


class SpriteRegistry:
    """
    Inventaire des vignettes nécessaires au MBStyle, et fabrication de la
    feuille de sprites au format Mapbox (sprite.png + sprite.json, et leurs
    équivalents @2x).

    Deux natures de vignettes :
      * un pictogramme SVG du dépôt CNIG, rendu tel quel ;
      * un motif de hachure « shape://… », dessiné à la volée et TUILABLE,
        pour servir de fill-pattern.
    """

    #: Convention QGIS/GeoServer des SVG dits « paramétriques » : l'attribut
    #: fill d'un (ou plusieurs) élément du SVG vaut LITTÉRALEMENT
    #: 'fill="param(fill)"' (sans repli), QGIS substituant la vraie couleur à
    #: l'affichage depuis IconSymbolizer.color (cf. styleforge_core/readers/
    #: qml.py, _lire_icone_image(avec_couleur=True) pour SvgMarker) — MÊME
    #: convention et MÊME constat chiffré (871 SVG sur 873 dans le dépôt CNIG)
    #: que documenté dans styleforge_core/writers/sld.py pour le correctif
    #: SLD (paramètre de requête 'fill' sur xlink:href, mécanisme GeoServer
    #: "Parametric SVG"). Côté MBStyle, aucun moteur de rendu de tuiles
    #: vectorielles ne sait interpréter 'param(fill)' à l'affichage : la
    #: seule façon de transmettre une couleur par-couche (et non figée dans
    #: le fichier source) est le mécanisme Mapbox GL "SDF" (sprite enregistré
    #: comme masque alpha, teinté au rendu par la propriété paint icon-color)
    #: — voir register_svg/_draw_svg ci-dessous et
    #: styleforge_core.writers.mbstyle._ecrire_icon_paint.
    _MOTIF_SVG_PARAMETRIQUE = 'fill="param(fill)"'

    def __init__(self, size: int = 64) -> None:
        self.size = size
        self.svg: Dict[str, Path] = {}          # nom -> fichier SVG
        self.svg_sdf: Dict[str, bool] = {}      # nom -> SVG paramétrique (sprite SDF)
        self.shapes: Dict[str, Dict[str, Any]] = {}   # nom -> description
        self.glyphs: Dict[str, Dict[str, Any]] = {}   # nom -> description
        self.warnings: List[str] = []

    # ------------------------------------------------------------- inscription
    def register_svg(self, reference: str, svg_dir: Path) -> Optional[str]:
        """Inscrit un pictogramme SVG et retourne son nom de sprite.

        Détecte, au CONTENU du fichier (pas sur une liste figée de noms), la
        convention SVG paramétrique 'fill="param(fill)"' (voir
        _MOTIF_SVG_PARAMETRIQUE) : si elle est présente, le sprite est marqué
        SDF (self.svg_sdf[name] = True) et sera rendu comme un masque alpha
        par _draw_svg, pour être teinté par-couche via icon-color côté
        MBStyle — AUTOMATIQUE et GÉNÉRAL, s'applique à tout futur QML/SVG
        suivant la même convention, pas seulement au corpus CNIG déjà vu."""
        if not reference:
            return None
        base = Path(str(reference).replace("\\", "/")).name
        if not base.lower().endswith(".svg"):
            return None
        name = safe_stem(Path(base).stem)
        if name not in self.svg:
            candidate = svg_dir / base
            if not candidate.is_file():
                self.warnings.append(
                    f"Pictogramme absent pour le sprite : {base}")
                return None
            self.svg[name] = candidate
            try:
                contenu = candidate.read_text(encoding="utf-8", errors="replace")
            except OSError:
                contenu = ""
            self.svg_sdf[name] = self._MOTIF_SVG_PARAMETRIQUE in contenu
        return name

    #: Marques simples dessinées centrées dans la vignette, par opposition aux
    #: motifs « shape:// » qui pavent toute sa surface.
    SIMPLE_SHAPES = ("circle", "square", "triangle", "star", "cross", "x",
                     "diamond", "pentagon", "hexagon", "line")

    def register_shape(self, well_known_name: str, color: str = "#000000",
                       stroke_width: float = 1.0, spacing: float = 8.0,
                       rotation: float = 0.0,
                       fill_color: Optional[str] = None) -> Optional[str]:
        """
        Inscrit une marque et retourne son nom de vignette.

        Deux familles sont acceptées :
          * « shape://slash », « shape://horline »… : motifs de hachure, pavant
            toute la vignette pour servir de fill-pattern ;
          * « circle », « square », « triangle »… : marques simples, dessinées
            centrées. Il faut les traiter aussi, car un semis de points
            (PointPatternFill) les utilise en graphicFill, et bridgestyle lève
            KeyError: 'spriteName' pour toute vignette non inscrite.
        """
        if not well_known_name:
            return None
        name = str(well_known_name)
        if name.startswith("shape://"):
            shape, family = name.split("//", 1)[1], "motif"
        elif name.lower() in self.SIMPLE_SHAPES:
            shape, family = name.lower(), "marque"
        else:
            return None
        key = safe_stem(f"{family}_{shape}_{color}_{fill_color or 'none'}"
                        f"_{stroke_width:g}_{spacing:g}_{rotation:g}")
        self.shapes.setdefault(key, {
            "shape": shape, "family": family, "color": color or "#000000",
            "fill": fill_color,
            "width": max(1.0, float(stroke_width or 1.0)),
            "spacing": max(2.0, float(spacing or 8.0)),
            "rotation": float(rotation or 0.0),
        })
        return key

    def register_font_glyph(self, well_known_name: str,
                            color: str = "#000000") -> Optional[str]:
        """
        Inscrit un glyphe de police et retourne son nom de vignette.

        Reconnaît la convention « ttf://<Police>#0x<hex> » produite par
        styleforge_core.readers.qml._lire_font_marker pour un FontMarker QGIS
        (point-de-code UTF-16, 4 chiffres hexadécimaux, préfixés "0x" :
        p. ex. "ttf://Wingdings#0x00f1"). GeoServer sait nativement tracer
        cette même chaîne comme WellKnownName SLD (wellknown_prefixes inclut
        déjà "ttf://" dans audit.py) ; côté MBStyle en revanche il n'existe
        aucune notion de police dans la spécification Mapbox GL — un
        FontMarker utilisé en graphicFill/graphicStroke (PointPatternFill)
        n'a donc PAS d'équivalent direct et doit être matérialisé en
        vignette, comme les autres marques.

        Le glyphe est dessiné CENTRÉ dans la vignette (cf. _draw_font_glyph),
        à la manière des « marques simples » de register_shape : une
        approximation visuelle du semis de points d'origine (la vignette,
        pavée en mosaïque par fill-pattern/line-pattern, reproduit l'effet
        d'un semis à intervalle régulier), pas un rendu point par point
        identique — mais sans substitution arbitraire de forme ni silence.
        """
        if not well_known_name:
            return None
        name = str(well_known_name)
        if not name.startswith("ttf://") or "#" not in name:
            return None
        reste = name[len("ttf://"):]
        police, _, code = reste.rpartition("#")
        if not police or not code.lower().startswith("0x"):
            return None
        try:
            point_de_code = int(code, 16)
        except ValueError:
            return None
        key = safe_stem(f"glyphe_{police}_{code}_{color or '#000000'}")
        self.glyphs.setdefault(key, {
            "police": police, "point_de_code": point_de_code,
            "color": color or "#000000",
        })
        return key

    # ------------------------------------------------------------- fabrication
    def _qt(self):
        """
        Retourne les classes Qt nécessaires, ou None.

        On privilégie « qgis.PyQt », qui pointe vers la version de Qt embarquée
        par QGIS ; sinon on tente PyQt5 puis PyQt6, ce qui permet d'utiliser la
        fonction hors de QGIS et de la tester.
        """
        for module in ("qgis.PyQt", "PyQt5", "PyQt6"):
            try:
                gui = __import__(f"{module}.QtGui", fromlist=["QtGui"])
                core = __import__(f"{module}.QtCore", fromlist=["QtCore"])
                svg = __import__(f"{module}.QtSvg", fromlist=["QtSvg"])
                return gui, core, svg
            except Exception:                              # noqa: BLE001
                continue
        return None

    @staticmethod
    def _qguiapp_disponible(gui) -> bool:
        """
        Vérifie, dans un SOUS-PROCESSUS jetable, qu'une QGuiApplication peut
        être instanciée dans cet environnement sans provoquer l'abandon
        (SIGABRT) du processus.

        Nécessaire car QGuiApplication() avec un greffon de plate-forme Qt
        inutilisable (p. ex. "xcb" sans serveur d'affichage) appelle
        qFatal() -> abort() — une erreur FATALE, non interceptable par un
        except Python, qui tue tout le processus (confirmé : code de sortie
        134/SIGABRT). On ne peut donc pas se contenter d'un try/except
        autour de la construction réelle dans CE processus : seule une
        sonde dans un sous-processus séparé, dont la mort éventuelle n'affecte
        pas le processus appelant, permet de savoir sans risque si la
        plate-forme est utilisable.
        """
        prefixe = gui.__name__.rsplit(".", 1)[0]          # "PyQt5" / "qgis.PyQt"...
        sonde = (
            "import sys\n"
            f"from {prefixe}.QtGui import QGuiApplication\n"
            "QGuiApplication(sys.argv[:1] or ['sonde'])\n"
        )
        try:
            resultat = subprocess.run(
                [sys.executable, "-c", sonde],
                capture_output=True, timeout=15)
            return resultat.returncode == 0
        except Exception:                                  # noqa: BLE001
            return False

    def build(self, out_dir: Path,
             pump_ui: Optional[Callable[[], None]] = None) -> Dict[str, Any]:
        """
        Écrit sprite.png, sprite.json, sprite@2x.png et sprite@2x.json.

        Retourne un dictionnaire de compte rendu. Sans Qt, aucune image n'est
        produite : on écrit seulement l'index des vignettes attendues, pour que
        l'équipe puisse les fabriquer autrement, et on le signale.
        """
        noms_glyphes = sorted(self.glyphs)
        names = sorted(self.svg) + sorted(self.shapes) + noms_glyphes
        report: Dict[str, Any] = {"vignettes": len(names), "images": False}
        if not names:
            return report

        qt = self._qt()
        if qt is None:
            (out_dir / "sprite_a_generer.json").write_text(
                json.dumps({"vignettes_attendues": names}, indent=2,
                           ensure_ascii=False), encoding="utf-8")
            self.warnings.append(
                "Qt indisponible : la feuille de sprites n'a pas été générée. "
                "L'index des vignettes attendues est écrit dans "
                "sprite_a_generer.json.")
            return report

        gui, core, svgmod = qt
        QImage, QPainter, QColor = gui.QImage, gui.QPainter, gui.QColor
        QRectF = core.QRectF
        QSvgRenderer = svgmod.QSvgRenderer

        # QFont (glyphes de police, cf. _draw_font_glyph) a besoin d'une
        # QGuiApplication déjà instanciée pour résoudre sa base de polices —
        # sans elle, PyQt segfault (confirmé : "QGuiApplication::font(): no
        # QGuiApplication instance..." suivi d'un SIGSEGV). QImage/QPainter
        # pour les SVG et les formes simples n'en ont pas besoin : on ne crée
        # donc cette instance que si des glyphes sont réellement inscrits, et
        # on réutilise celle de QGIS si le script tourne dans ce contexte
        # (instance() non None) plutôt que d'en créer une seconde. La
        # référence est conservée sur self pour ne pas être détruite par le
        # ramasse-miettes avant la fin de build().
        #
        # MAIS construire une QGuiApplication avec un greffon de plate-forme
        # Qt inutilisable (p. ex. "xcb" sans serveur d'affichage disponible,
        # le cas de ce bac à sable de développement) appelle qFatal() ->
        # abort() : une erreur FATALE qu'aucun except Python ne peut
        # intercepter (confirmé : code de sortie 134/SIGABRT, qui emporte
        # TOUT le processus — y compris les phases suivantes déjà en file).
        # On sonde donc la faisabilité dans un SOUS-PROCESSUS jetable
        # (_qguiapp_disponible) avant de risquer la construction réelle :
        # seul ce sous-processus meurt en cas d'échec. Si la plate-forme
        # n'est pas utilisable, on ne tente PAS un rendu dégradé des
        # glyphes (ce serait reconstruire une police au hasard) : on les
        # retire du jeu de vignettes à produire ICI — exactement comme le
        # mécanisme préexistant « Qt indisponible » ci-dessus, mais restreint
        # aux seuls glyphes — et on écrit leur liste dans un index séparé
        # pour que l'équipe les fabrique sur un poste où QFont fonctionne
        # (p. ex. le poste Windows de production, où le greffon de plate-
        # forme natif n'a pas cette dépendance à un serveur X11 ; ou ce
        # même environnement avec QT_QPA_PLATFORM=offscreen positionné).
        # Les SVG et formes simples, qui n'ont pas besoin de QFont, sont
        # tout de même produits normalement.
        if noms_glyphes:
            QGuiApplication = gui.QGuiApplication
            if QGuiApplication.instance() is not None:
                app_utilisable = True
            else:
                app_utilisable = self._qguiapp_disponible(gui)
            if not app_utilisable:
                (out_dir / "sprite_glyphes_a_generer.json").write_text(
                    json.dumps({"glyphes_attendus": noms_glyphes}, indent=2,
                               ensure_ascii=False), encoding="utf-8")
                self.warnings.append(
                    f"{len(noms_glyphes)} glyphe(s) de police (FontMarker) "
                    "non rendu(s) dans la feuille de sprites : aucune "
                    "plate-forme Qt utilisable dans cet environnement pour "
                    "QFont (pas de serveur d'affichage, ni "
                    "QT_QPA_PLATFORM=offscreen positionné). Les documents "
                    "MBStyle référencent déjà ces noms de vignette ; "
                    "régénérer la feuille de sprites sur un poste où QFont "
                    "fonctionne (p. ex. le poste de production, ou ce même "
                    "environnement avec QT_QPA_PLATFORM=offscreen). Liste "
                    "dans sprite_glyphes_a_generer.json.")
                names = sorted(self.svg) + sorted(self.shapes)
                report["vignettes"] = len(names)
                noms_glyphes = []
                if not names:
                    return report
            elif QGuiApplication.instance() is None:
                self._qt_app = QGuiApplication(sys.argv[:1] or ["styleforge"])

        # DISPOSITION EN GRILLE, ET NON EN BANDE HORIZONTALE.
        # Une bande de 224 vignettes de 64 px fait 14 336 px de large, et le
        # double en @2x : au-delà de la taille de texture maximale de la plupart
        # des implémentations WebGL (souvent 4 096 ou 8 192 px). La feuille ne
        # se chargerait tout simplement pas côté client. Une grille carrée
        # garde les deux dimensions modestes : 224 vignettes tiennent dans
        # 15 x 15, soit 960 px de côté en @1x.
        import math as _math
        columns = max(1, int(_math.ceil(_math.sqrt(len(names)))))
        rows_count = int(_math.ceil(len(names) / columns))

        for ratio in (1, 2):
            tile = self.size * ratio
            sheet = QImage(tile * columns, tile * rows_count,
                           QImage.Format_ARGB32)
            sheet.fill(0)
            painter = QPainter(sheet)
            try:
                painter.setRenderHint(QPainter.Antialiasing, True)
                index: Dict[str, Any] = {}
                for position, name in enumerate(names):
                    x = (position % columns) * tile
                    y = (position // columns) * tile
                    est_sdf = False
                    if name in self.svg:
                        est_sdf = self.svg_sdf.get(name, False)
                        self._draw_svg(painter, QSvgRenderer, core, QRectF,
                                       self.svg[name], x, y, tile, sdf=est_sdf)
                    elif name in self.shapes:
                        self._draw_shape(painter, gui, core,
                                         self.shapes[name], x, y, tile, ratio)
                    else:
                        self._draw_font_glyph(painter, gui, core,
                                              self.glyphs[name], x, y, tile,
                                              ratio)
                    index[name] = {"x": x, "y": y, "width": tile,
                                   "height": tile, "pixelRatio": ratio}
                    if est_sdf:
                        # Indicateur Mapbox GL Style ("sdf": true dans
                        # sprite.json) : un sprite marqué ainsi est un masque
                        # alpha teinté au rendu par icon-color (paint), voir
                        # _draw_svg et styleforge_core.writers.mbstyle.
                        # _ecrire_icon_paint. NON vérifié contre l'oracle
                        # QGIS habituel de ce module (QgsMapBoxGlStyleConverter
                        # n'implémente ni icon-color ni "sdf" — confirmé en
                        # lisant son code source C++, versions 3.28 à 3.40 —
                        # ce n'est donc pas une limite de conception de cet
                        # écrivain mais de l'oracle lui-même), mais repose sur
                        # la spec Mapbox GL Style officielle et stable, prise
                        # en charge nativement par Mapbox GL JS/MapLibre GL JS
                        # et le rendu vecteur-tuiles de GeoServer.
                        index[name]["sdf"] = True
                    if pump_ui is not None:
                        pump_ui()
            finally:
                painter.end()

            suffix = "" if ratio == 1 else "@2x"
            sheet.save(str(out_dir / f"sprite{suffix}.png"), "PNG")
            (out_dir / f"sprite{suffix}.json").write_text(
                json.dumps(index, indent=2), encoding="utf-8")

        report["images"] = True
        return report

    @staticmethod
    def _draw_svg(painter, QSvgRenderer, core, QRectF, path: Path,
                  x: int, y: int, tile: int, *, sdf: bool = False) -> None:
        """Dessine un pictogramme SVG dans la vignette.

        Cas normal (sdf=False) : rendu TEL QUEL, inchangé par rapport au
        comportement préexistant.

        Cas SDF (sdf=True, SVG paramétrique 'fill="param(fill)"' — voir
        _MOTIF_SVG_PARAMETRIQUE) : AUCUNE valeur 'param(...)' (fill,
        fill-opacity, stroke, stroke-opacity, stroke-width — confirmées sur
        le corpus CNIG examples/qml) n'est une valeur CSS valide —
        QSvgRenderer ne sait interpréter aucune d'elles (constaté : un SVG
        réel du corpus, avec plusieurs attributs param() simultanés sur le
        même élément, ne produit AUCUN pixel opaque une fois rendu tel quel
        — pas seulement une couleur par défaut, le renderer rejette la forme
        entière). _neutraliser_svg_parametrique() neutralise TOUTES les
        occurrences confirmées avant rendu (voir sa docstring pour le détail
        par attribut), pas seulement 'fill'."""
        if not sdf:
            renderer = QSvgRenderer(str(path))
            if renderer.isValid():
                renderer.render(painter, QRectF(x, y, tile, tile))
            return
        try:
            contenu = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            return
        contenu_masque = _neutraliser_svg_parametrique(contenu)
        renderer = QSvgRenderer(core.QByteArray(contenu_masque.encode("utf-8")))
        if renderer.isValid():
            renderer.render(painter, QRectF(x, y, tile, tile))

    @staticmethod
    def _draw_shape(painter, gui, core, spec: Dict[str, Any],
                    x: int, y: int, tile: int, ratio: int) -> None:
        """
        Dessine un motif de hachure TUILABLE dans une vignette.

        Le motif doit se raccorder à lui-même : Mapbox répète l'image en
        mosaïque via fill-pattern. Les lignes sont donc tracées au-delà des
        bords et l'espacement divise la taille de la vignette.
        """
        QColor, QPen, QBrush = gui.QColor, gui.QPen, gui.QBrush
        QPointF, QRectF = core.QPointF, core.QRectF
        color = QColor(spec["color"])
        pen = QPen(color)
        pen.setWidthF(max(1.0, spec["width"] * ratio))
        pen.setCapStyle(core.Qt.FlatCap)
        painter.setPen(pen)

        step = max(4.0, spec["spacing"] * ratio)
        shape = spec["shape"]

        # --- marques simples : dessinées centrées, pas en pavage -------
        if spec.get("family") == "marque":
            painter.setBrush(QBrush(QColor(spec["fill"]))
                             if spec.get("fill") else core.Qt.NoBrush)
            margin = tile * 0.15
            box = QRectF(x + margin, y + margin,
                         tile - 2 * margin, tile - 2 * margin)
            if shape in ("circle", "pentagon", "hexagon"):
                painter.drawEllipse(box)
            elif shape in ("square", "diamond"):
                painter.drawRect(box)
            elif shape == "triangle":
                gui_poly = gui.QPolygonF([
                    QPointF(box.center().x(), box.top()),
                    QPointF(box.left(), box.bottom()),
                    QPointF(box.right(), box.bottom())])
                painter.drawPolygon(gui_poly)
            elif shape in ("cross", "x"):
                painter.drawLine(QPointF(box.left(), box.top()),
                                 QPointF(box.right(), box.bottom()))
                painter.drawLine(QPointF(box.left(), box.bottom()),
                                 QPointF(box.right(), box.top()))
            elif shape == "line":
                # Qgis::MarkerShape::Line (QGIS) : un simple segment vertical,
                # ni pivoté ni mis à l'échelle ici (comme les autres marques
                # de cette branche, "rotation" n'est pas encore exploité —
                # limite préexistante, pas introduite par cet ajout).
                painter.drawLine(QPointF(box.center().x(), box.top()),
                                 QPointF(box.center().x(), box.bottom()))
            else:                                    # star et divers
                painter.drawEllipse(box)
            painter.setBrush(core.Qt.NoBrush)
            return

        def line(x1, y1, x2, y2):
            painter.drawLine(QPointF(x + x1, y + y1), QPointF(x + x2, y + y2))

        if shape in ("horline", "times", "plus"):
            offset = 0.0
            while offset <= tile:
                line(0, offset, tile, offset)
                offset += step
        if shape in ("vertline", "times", "plus"):
            offset = 0.0
            while offset <= tile:
                line(offset, 0, offset, tile)
                offset += step
        if shape == "slash":
            offset = -tile
            while offset <= tile * 2:
                line(offset, tile, offset + tile, 0)
                offset += step
        if shape == "backslash":
            offset = -tile
            while offset <= tile * 2:
                line(offset, 0, offset + tile, tile)
                offset += step

    @staticmethod
    def _draw_font_glyph(painter, gui, core, spec: Dict[str, Any],
                         x: int, y: int, tile: int, ratio: int) -> None:
        """
        Dessine un glyphe de police (FontMarker) centré dans la vignette.

        Même logique que les « marques simples » de _draw_shape : le glyphe
        est centré et dimensionné pour occuper l'essentiel de la vignette
        sans la déborder, afin de rester visuellement cohérent une fois pavé
        en mosaïque par fill-pattern/line-pattern. QFont est résolue par son
        seul nom de famille (spec["police"]) : si la police n'est pas
        installée sur la machine qui fabrique la feuille de sprites, Qt lui
        substitue une police par défaut — ceci n'est PAS vérifié ici (aucune
        exception QFont ne permet de le détecter de façon fiable), et reste
        documenté comme une limite connue plutôt que silencieusement ignoré.
        """
        QColor, QFont = gui.QColor, gui.QFont
        QRectF = core.QRectF
        painter.setPen(QColor(spec["color"]))
        font = QFont(spec["police"])
        font.setPixelSize(max(1, int(tile * 0.8)))
        painter.setFont(font)
        caractere = chr(spec["point_de_code"])
        box = QRectF(x, y, tile, tile)
        painter.drawText(box, core.Qt.AlignCenter, caractere)

