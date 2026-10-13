#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
 cnig_qml2sld_geoserver.py
 Chaîne de production QML (CNIG / SLYR) -> SLD 1.0.0 « GeoServer-ready »
================================================================================

 Auteur    : chaîne outillée pour les documents d'urbanisme CNIG (PLU / SUP / SCoT)
 Licence   : GPL-3.0-or-later (voir LICENSE à la racine du dépôt)
 Python    : 3.9+   (testé 3.9 / 3.11 / 3.12)
 Plateforme: Windows / PowerShell (chemins gérés via pathlib, aucun appel shell)

--------------------------------------------------------------------------------
 SOURCE DES DONNÉES
--------------------------------------------------------------------------------
 Dépôt officiel de symbolisation du CNIG :
     https://github.com/cnigfr/DDU-SG5-SYMBOLISATION
     branche : SYMBOLISATION     sous-dossier : PLU
     (vue web : .../tree/SYMBOLISATION/PLU)

 Le script NE CODE EN DUR AUCUN NOM DE FICHIER : il interroge l'API Git Trees de
 GitHub en mode `recursive=1`, puis filtre dynamiquement tous les `.qml` et tous
 les `.svg` situés sous le préfixe demandé. Il reste donc valide si le CNIG
 réorganise son arborescence (dossiers QML/, SVG/, PLU/QML/, etc.).

--------------------------------------------------------------------------------
 LES 4 PHASES
--------------------------------------------------------------------------------
 PHASE 1 : Analyse de complexité cartographique et désignation du « Style Étalon »
           (benchmark) + calcul de la COMBINAISON COUVRANTE MINIMALE de 2-3
           styles qui totalise l'ensemble des cas de figure du corpus.
 PHASE 2 : Conversion par lot QML -> SLD 1.0.0 via `bridgestyle` (implémentation
           Python officielle de GeoStyler, dépôt GeoCat/bridge-style),
           tolérante aux pannes (un échec n'interrompt jamais le lot).
 PHASE 3 : Construction de l'arborescence GEOSERVER_DATA_DIR et gestion stricte
           des SVG + réécriture systématique des <OnlineResource> en chemins
           relatifs `svg/cnig/<fichier>.svg`.
 PHASE 4 : Post-traitement XML : réinjection des <VendorOption> GeoServer,
           correction des hachures dégradées (shape://slash, backslash...),
           remise en ordre XSD strict, nettoyage des reliquats QGIS/ESRI,
           écriture UTF-8 SANS BOM.

--------------------------------------------------------------------------------
 INSTALLATION DES DÉPENDANCES
--------------------------------------------------------------------------------
     pip install bridgestyle lxml requests

 /!\ ATTENTION - PIÈGE CLASSIQUE /!\
 Le dépôt GitHub s'appelle « bridge-style », mais le paquet publié sur PyPI et
 le module importable s'appellent « bridgestyle » (sans tiret). La commande
 `pip install bridge-style` échoue avec « No matching distribution found ».
 Depuis les sources :
     pip install git+https://github.com/GeoCat/bridge-style.git

 `lxml` est optionnel (repli automatique sur xml.etree.ElementTree) mais
 fortement recommandé : il préserve les commentaires et sérialise proprement.

--------------------------------------------------------------------------------
 LES DEUX BACKENDS DE CONVERSION (point d'architecture ESSENTIEL)
--------------------------------------------------------------------------------
 `bridgestyle.qgis.togeostyler.convert()` prend en argument un OBJET
 QgsVectorLayer, PAS un fichier .qml. Autrement dit, la conversion QML -> SLD
 « pleine fidélité » de bridge-style N'EST PAS UTILISABLE sans PyQGIS : le
 module lit l'arbre d'objets QgsSymbolLayer en mémoire (QgsLinePatternFill-
 SymbolLayer, QgsSVGFillSymbolLayer, QgsMarkerLineSymbolLayer...).
 De plus le CLI `style2style` fourni par bridgestyle ne gère que
 sld / geostyler / mapbox / lyrx : « qml » n'est pas dans sa table `_exts`.

 Ce script propose donc DEUX backends, auto-détectés :

   [A] BACKEND « qgis »  (RECOMMANDÉ - pleine fidélité)
       Nécessite que le script tourne dans l'interpréteur Python de QGIS.
       Sous Windows, dans le « OSGeo4W Shell » ou via python-qgis.bat :
           C:\\Program Files\\QGIS 3.34\\bin\\python-qgis.bat cnig_qml2sld_geoserver.py --all
       Le script instancie QgsApplication en mode headless, crée une couche
       mémoire du bon type géométrique (déduit du QML), applique
       `layer.loadNamedStyle(qml)` puis appelle `bridgestyle.qgis.layerStyleAsSld`.

   [B] BACKEND « standalone » (repli - Python « nu »)
       Aucune dépendance QGIS. Le script parse lui-même le XML du QML et
       fabrique le dictionnaire GeoStyler attendu par
       `bridgestyle.sld.fromgeostyler.convert()`. La couverture est volontai-
       rement ciblée sur les cas de figure réellement utilisés par le CNIG
       (SimpleFill, SimpleLine, SimpleMarker, SvgMarker, LinePatternFill,
       SVGFill, PointPatternFill, CentroidFill, MarkerLine, étiquetage simple).
       Les cas non couverts sont signalés comme AVERTISSEMENTS, jamais ignorés
       silencieusement.

 Dans les deux cas, les PHASES 3 et 4 s'appliquent de façon identique : elles
 travaillent sur le XML produit, et sur un « index d'indices » (hints) extrait
 directement du QML source. C'est ce qui permet de RÉPARER les dégradations de
 bridge-style même quand c'est bridge-style lui-même qui a produit le SLD.

--------------------------------------------------------------------------------
 CONFIGURATION (recommandé en équipe)
--------------------------------------------------------------------------------
 Plutôt que d'empiler les arguments, on décrit une bonne fois les paramètres
 dans un fichier .ini :

   python .\\cnig_qml2sld_geoserver.py --write-config
   # -> écrit cnig_qml2sld.ini, commenté ; on l'ajuste, puis :
   python .\\cnig_qml2sld_geoserver.py

 Le fichier « cnig_qml2sld.ini » est cherché automatiquement à côté du script
 puis dans le répertoire courant ; --config pointe un autre fichier,
 --no-config ignore tout fichier détecté.

 PRIORITÉ : argument de ligne de commande > fichier .ini > valeur par défaut.
 Le fichier fixe les habitudes de l'équipe (dépôt, dossier de sortie, backend,
 VendorOptions, identifiants GeoServer) et la ligne de commande permet de s'en
 écarter ponctuellement sans le modifier.

 Il pilote notamment [source] mode = github | local : en mode « local », on
 travaille sur un clone ou un export déjà présent sur le disque, sans aucun
 accès réseau (utile derrière un proxy d'entreprise).

--------------------------------------------------------------------------------
 EXEMPLES D'UTILISATION (PowerShell)
--------------------------------------------------------------------------------
   # Chaîne complète : téléchargement + 4 phases, sortie dans .\\build
   python .\\cnig_qml2sld_geoserver.py --all --out .\\build

   # Phase 1 seule : quel est le style le plus complexe ? (aucune écriture)
   python .\\cnig_qml2sld_geoserver.py --analyze-only

   # Travailler sur un clone local déjà présent (aucun accès réseau)
   python .\\cnig_qml2sld_geoserver.py --all --local-source "D:\\git\\DDU-SG5-SYMBOLISATION\\PLU"

   # Forcer le backend pleine fidélité dans le shell OSGeo4W
   python-qgis.bat .\\cnig_qml2sld_geoserver.py --all --backend qgis

   # Ne convertir que le style étalon identifié en phase 1 (tests GeoServer)
   python .\\cnig_qml2sld_geoserver.py --all --benchmark-only

   # Publier dans la foulée sur une instance GeoServer de recette
   python .\\cnig_qml2sld_geoserver.py --all ^
          --geoserver-url http://localhost:8080/geoserver ^
          --geoserver-user admin --geoserver-password geoserver ^
          --geoserver-workspace cnig
================================================================================
"""

# NOTE : surtout NE PAS ajouter « from __future__ import annotations » ici.
# Cette directive transforme toutes les annotations en CHAÎNES. Le module
# dataclasses doit alors les résoudre via sys.modules[cls.__module__].__dict__,
# ce qui échoue avec
#     AttributeError: 'NoneType' object has no attribute '__dict__'
# dès que le script est exécuté hors d'un module enregistré dans sys.modules —
# c'est-à-dire précisément dans la console Python de QGIS, avec
#     exec(compile(Path(...).read_text(), ..., 'exec'))
# Sans la directive, les annotations sont évaluées à la définition et
# dataclasses n'a plus besoin de retrouver l'espace de noms du module.
# Toutes les annotations utilisent donc les formes typing (Dict, List, Optional)
# et non les génériques natifs (dict, list), pour rester compatibles Python 3.9.

import argparse
import base64
import io
import json
import math
import os
import re
import subprocess
import sys
import time
import traceback
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Set, Tuple

# ------------------------------------------------------------------------------
# Dépendances optionnelles / obligatoires
# ------------------------------------------------------------------------------
try:
    import requests  # type: ignore
    _HAS_REQUESTS = True
except ImportError:                                    # pragma: no cover
    requests = None                                    # type: ignore
    _HAS_REQUESTS = False

try:
    from lxml import etree as LET                      # type: ignore
    _HAS_LXML = True
except ImportError:                                    # pragma: no cover
    LET = None                                         # type: ignore
    _HAS_LXML = False

import xml.etree.ElementTree as ET

# ------------------------------------------------------------------------------
# PHASE 4 (post-traitement XML / correctifs GeoServer) : code PARTAGÉ avec le
# plugin QGIS (qgis-plugin/), migré depuis ce script vers styleforge-core pour
# que les deux consommateurs appellent EXACTEMENT le même code plutôt que deux
# copies qui dériveraient l'une de l'autre (voir styleforge_core.writers.
# sld_posttraitement pour le détail et la justification de ce déplacement).
#
# styleforge_core devient donc ici une dépendance du script lui-même, pas
# seulement de l'optionnel --backend styleforge : PHASE 4 (comme PHASE 2 du
# backend standalone, qui réutilise plusieurs des mêmes utilitaires) s'applique
# QUEL QUE SOIT le backend choisi. Repli identique à celui déjà utilisé par
# StyleforgeBackend.available() : paquet installé (pip), sinon dossier frère
# styleforge-core/ à côté de ce script — jamais une troisième tentative
# silencieuse, jamais une approximation si les deux échouent.
# ------------------------------------------------------------------------------
def _rendre_styleforge_core_importable() -> None:
    try:
        import styleforge_core  # type: ignore  # noqa: F401
        return
    except ImportError:
        pass
    candidat = Path(__file__).resolve().parent / "styleforge-core"
    if candidat.is_dir() and str(candidat) not in sys.path:
        sys.path.insert(0, str(candidat))
    try:
        import styleforge_core  # type: ignore  # noqa: F401
    except ImportError as exc:
        raise RuntimeError(
            "styleforge_core est introuvable (ni installé via pip, ni présent "
            "dans un dossier styleforge-core/ à côté de ce script). Depuis "
            "0.2.0, ce module est nécessaire quel que soit le --backend choisi "
            "(PHASE 4 — post-traitement SLD — en dépend désormais, partagé "
            "avec le plugin QGIS). Installez-le avec : "
            "pip install ./styleforge-core (depuis la racine du dépôt), ou "
            "vérifiez que le dépôt a été cloné en entier plutôt que ce seul "
            f"fichier. Détail : {exc}"
        ) from exc


_rendre_styleforge_core_importable()

from styleforge_core.writers.sld_posttraitement import (          # noqa: E402
    SVG_SUBDIR,
    VENDOR_DEFAULTS,
    QT_BRUSH_TO_WKN,
    NOMS_MARQUEURS_QGIS_VERS_WKN,
    HATCH_WKN_BY_ANGLE,
    XSD_ORDER,
    PROPRIETARY_TAGS,
    OGC_ELEMENTS,
    safe_stem,
    qgis_color_to_hex,
    qgis_size_to_px,
    hatch_wkn_for_angle,
    register_svg_reference,
    resoudre_href_svg,
    EMBEDDED_SVG,
    _dash_from_props,
    QmlDocument,
    HatchHint,
    RuleHints,
    HintExtractor,
    SldPostProcessor,
    post_traiter_sld,
)
from styleforge_core.sprites import SpriteRegistry                # noqa: E402


# ==============================================================================
#  SECTION 0-bis — CONTOURNEMENT D'UN DÉFAUT D'IMPORT DE bridgestyle 0.1.9
# ==============================================================================
#
#  SYMPTÔME OBSERVÉ (reproductible sur une installation pip « nue ») :
#      >>> import bridgestyle.sld.fromgeostyler
#      bridgestyle.qgis.expressions.CompatibilityException:
#          Your QGIS version is not compatible with bridgestyle
#
#  CAUSE : chaîne d'imports circulaire et non conditionnelle.
#      bridgestyle/sld/__init__.py
#        -> sld/fromgeostyler.py     ligne 7 : from ..qgis.expressions import ...
#          -> bridgestyle/qgis/__init__.py   ligne 5 : from .. import mapboxgl
#            -> mapboxgl/fromgeostyler.py    ligne 6 : from ..qgis import togeostyler
#              -> qgis/togeostyler.py        ligne 6 : from .expressions import ...
#                -> qgis/expressions.py      ligne 37 : raise CompatibilityException
#
#  Autrement dit, le module SLD — qui est du pur XML et n'a AUCUN besoin de
#  QGIS — devient inutilisable sans QGIS. Il n'importe de `qgis.expressions`
#  que QUATRE CONSTANTES DE TYPE CHAÎNE (OGC_PROPERTYNAME, OGC_IS_EQUAL_TO,
#  OGC_IS_NULL, OGC_IS_LIKE). Le CLI `style2style` est atteint par le même
#  défaut : « sld -> mapbox » échoue sans QGIS installé.
#
#  SOLUTION APPLIQUÉE ICI : on pré-enregistre dans sys.modules un module
#  `bridgestyle.qgis.expressions` minimal AVANT le premier import de
#  `bridgestyle.sld`. Python trouve le module déjà chargé et ne rejoue pas la
#  chaîne fautive. C'est strictement non intrusif : aucun fichier de la
#  bibliothèque n'est modifié, et si un vrai QGIS est présent, la fonction
#  se retire d'elle-même (voir le test `_has_real_qgis`).
#
#  => Voir la SECTION 7 (guide de Pull Request), correctif « priorité 0 ».
# ------------------------------------------------------------------------------

#: True lorsque le shim a dû être imposé alors que PyQGIS était présent :
#: cela signifie que bridgestyle.qgis est inutilisable et que seul le backend
#: autonome peut fonctionner.
SLD_SHIM_FORCED = False


def install_bridgestyle_sld_shim(force: bool = False) -> bool:
    """
    Rend `bridgestyle.sld.fromgeostyler` importable sans PyQGIS.

    `force=True` pose le shim MÊME SI PyQGIS est présent. C'est le cas de
    secours lorsque bridgestyle refuse de s'initialiser avec la version de QGIS
    installée : qgis/expressions.py lève alors CompatibilityException dès
    l'import, ce qui rend le module SLD inutilisable alors même que QGIS
    fonctionne. Mieux vaut basculer sur le backend autonome que tout perdre.

    Retourne True si le shim a été posé, False s'il était inutile ou impossible.
    """
    if not force and "bridgestyle.sld.fromgeostyler" in sys.modules:
        return False
    if not force:
        try:
            import qgis.core  # type: ignore  # noqa: F401
            return False                  # vrai QGIS : surtout ne rien fausser
        except Exception:                 # noqa: BLE001
            pass
    try:
        import bridgestyle                # type: ignore
    except Exception:                     # noqa: BLE001
        return False

    import types
    pkg_dir = os.path.dirname(bridgestyle.__file__)

    qgis_pkg = types.ModuleType("bridgestyle.qgis")
    qgis_pkg.__path__ = [os.path.join(pkg_dir, "qgis")]   # type: ignore[attr-defined]

    expressions = types.ModuleType("bridgestyle.qgis.expressions")
    # Les seules constantes réellement consommées par sld/fromgeostyler.py
    expressions.OGC_PROPERTYNAME = "PropertyName"          # type: ignore[attr-defined]
    expressions.OGC_IS_EQUAL_TO = "PropertyIsEqualTo"      # type: ignore[attr-defined]
    expressions.OGC_IS_NULL = "PropertyIsNull"             # type: ignore[attr-defined]
    expressions.OGC_IS_NOT_NULL = "PropertyIsNotNull"      # type: ignore[attr-defined]
    expressions.OGC_IS_LIKE = "PropertyIsLike"             # type: ignore[attr-defined]
    expressions.OGC_CONCAT = "Concatenate"                 # type: ignore[attr-defined]
    expressions.OGC_SUB = "Sub"                            # type: ignore[attr-defined]

    class UnsupportedExpressionException(Exception):
        """Copie locale : l'originale vit dans qgis/expressions.py."""

    class CompatibilityException(Exception):
        """Copie locale : l'originale vit dans qgis/expressions.py."""

    expressions.UnsupportedExpressionException = UnsupportedExpressionException   # type: ignore[attr-defined]
    expressions.CompatibilityException = CompatibilityException                   # type: ignore[attr-defined]

    class ExpressionConverter:                             # pragma: no cover
        """Substitut inerte : la traduction d'expressions exige PyQGIS."""

        def __init__(self, *args: Any, **kwargs: Any) -> None:
            raise UnsupportedExpressionException(
                "La conversion d'expressions QGIS nécessite PyQGIS.")

    expressions.ExpressionConverter = ExpressionConverter  # type: ignore[attr-defined]
    qgis_pkg.expressions = expressions                     # type: ignore[attr-defined]

    # Le module mapboxgl importe « ..qgis.togeostyler » dès son chargement, pour
    # la seule constante SPRITE_SIZE et les fonctions de feuille de sprites, qui
    # reposent sur QImage / QPainter. Sans substitut, l'export MBStyle est lui
    # aussi inaccessible sans QGIS — même couplage dur que pour le module SLD.
    togeostyler = types.ModuleType("bridgestyle.qgis.togeostyler")
    togeostyler.SPRITE_SIZE = 64                           # type: ignore[attr-defined]
    togeostyler.NO_ICON = "no_icon"                        # type: ignore[attr-defined]

    def _needs_qgis(*args: Any, **kwargs: Any) -> Any:      # pragma: no cover
        raise RuntimeError(
            "Cette fonction de bridgestyle.qgis.togeostyler exige PyQGIS. "
            "La feuille de sprites est produite par ce script, pas par "
            "bridgestyle.")

    for _name in ("convert", "initSpriteSheet", "drawSpriteSheet"):
        setattr(togeostyler, _name, _needs_qgis)
    qgis_pkg.togeostyler = togeostyler                     # type: ignore[attr-defined]

    if force:
        sys.modules["bridgestyle.qgis"] = qgis_pkg
        sys.modules["bridgestyle.qgis.expressions"] = expressions
        sys.modules["bridgestyle.qgis.togeostyler"] = togeostyler
    else:
        sys.modules.setdefault("bridgestyle.qgis", qgis_pkg)
        sys.modules.setdefault("bridgestyle.qgis.expressions", expressions)
        sys.modules.setdefault("bridgestyle.qgis.togeostyler", togeostyler)
    return True


# ==============================================================================
#  SECTION 0 — CONFIGURATION GLOBALE
# ==============================================================================

#: Dépôt CNIG de référence (modifiable par --repo / --branch / --subpath)
DEFAULT_REPO = "cnigfr/DDU-SG5-SYMBOLISATION"
DEFAULT_BRANCH = "SYMBOLISATION"
#: Sous-dossiers balayés par défaut : les trois familles de documents
#: d'urbanisme publiées par le CNIG. « Archives » contient d'anciennes versions
#: et est écarté par défaut (voir EXCLUDED_PREFIXES).
DEFAULT_SUBPATH = "PLU,PSMV,SUP,__Ressources"

#: Préfixes systématiquement ignorés, même lorsqu'on balaye tout le dépôt.
#: Archives/ rassemble des QML obsolètes, dont des homonymes des versions
#: courantes : les convertir produirait des styles en double et trompeurs.
EXCLUDED_PREFIXES = ("Archives/", ".github/", "__outils")

#: Branches de repli testées si la branche demandée est introuvable.
FALLBACK_BRANCHES = ("SYMBOLISATION", "main", "master", "develop")


#: Classes de symboles QGIS considérées comme « coûteuses » pour le score
#: de complexité cartographique (PHASE 1). Le poids traduit l'effort de
#: portage vers SLD/GeoServer, pas la beauté du rendu.
COMPLEXITY_WEIGHTS: Dict[str, int] = {
    "rules": 1,                       # par règle de rendu
    "categories": 1,                  # par catégorie / classe
    "LinePatternFill": 12,            # hachures : cas le plus délicat
    "SVGFill": 10,                    # motif SVG répété
    "PointPatternFill": 9,            # semis de points
    "RandomMarkerFill": 9,
    "CentroidFill": 6,
    "MarkerLine": 10,                 # ligne à symboles répétés
    "ArrowLine": 8,
    "HashLine": 8,
    "SvgMarker": 5,
    "FontMarker": 7,                  # police ESRI : dégradation quasi certaine
    "RasterFill": 7,
    "GradientFill": 6,
    "ShapeburstFill": 8,
    "GeometryGenerator": 14,          # aucun équivalent SLD
    "LinePatternFill.offset": 6,      # décalage de hachure
    "offset": 3,                      # décalage de symbole / ligne
    "customdash": 4,                  # tirets personnalisés
    "labeling": 6,                    # présence d'étiquetage
    "labeling_rules": 4,              # étiquetage par règles
    "labeling_callout": 5,            # lignes de rappel
    "data_defined": 5,                # propriétés pilotées par expression
    "scale_dependent": 2,             # visibilité par échelle
    "blend_mode": 4,                  # modes de fusion
    "symbol_levels": 3,               # niveaux de symboles
}

#: Nom du fichier de configuration cherché automatiquement (à côté du script,
#: puis dans le répertoire courant). Surchargé par --config.
DEFAULT_CONFIG_NAME = "cnig_qml2sld.ini"

#: Gabarit de configuration produit par --write-config.
#: Format INI (module configparser de la bibliothèque standard) : pas de
#: dépendance supplémentaire, commentaires autorisés, lisible sous Windows.
CONFIG_TEMPLATE = """\
# ==============================================================================
#  Configuration de la chaîne CNIG QML -> SLD GeoServer
#  Fichier lu automatiquement s'il s'appelle « cnig_qml2sld.ini » et se trouve
#  à côté du script ou dans le répertoire courant. Sinon : --config chemin.ini
#
#  PRIORITÉ : argument de ligne de commande  >  fichier .ini  >  valeur par défaut
#  Autrement dit, ce fichier fixe les habitudes de l'équipe, et la ligne de
#  commande permet de s'en écarter ponctuellement sans le modifier.
#
#  Les lignes commençant par # ou ; sont des commentaires.
#  Une valeur laissée vide est ignorée (la valeur par défaut s'applique).
# ==============================================================================

[execution]
# Action lancée quand le script est appelé SANS argument :
#   all       -> les 4 phases
#   analyze   -> phase 1 seule (analyse de complexité, aucune écriture)
#   benchmark -> les 4 phases, mais sur le style étalon et la combinaison
#                couvrante minimale uniquement
#   none      -> ne rien faire, afficher l'aide
action = all

# Nombre de styles affichés dans le classement de la phase 1.
top = 12


[source]
# D'où viennent les QML et les SVG.
#   github -> téléchargement depuis le dépôt CNIG (API Git Trees, récursive)
#   local  -> dossier déjà présent sur le disque (aucun accès réseau)
mode = github

# --- mode « github » ---------------------------------------------------------
repo = cnigfr/DDU-SG5-SYMBOLISATION
branch = SYMBOLISATION
# Sous-dossiers balayés, séparés par des virgules. Vide = tout le dépôt.
# Le CNIG publie trois familles de documents d'urbanisme :
#   PLU    plan local d'urbanisme                 8 QML, 333 pictogrammes
#   PSMV   plan de sauvegarde et de mise en valeur 7 QML, 744 pictogrammes
#   SUP    servitudes d'utilité publique           2 QML
# __Ressources contient des pictogrammes communs.
# Le dossier Archives (anciennes versions) est toujours écarté.
subpath = PLU,PSMV,SUP,__Ressources
# Dossier de cache des téléchargements. Réutilisé d'une exécution à l'autre :
# le second lancement ne retélécharge rien.
# Comme « out », un chemin relatif est ancré sur le dossier du script.
cache = .cache_cnig
# Jeton GitHub, pour dépasser la limite de 60 requêtes/heure en anonyme.
# Peut aussi être fourni par la variable d'environnement GITHUB_TOKEN.
github_token =

# --- mode « local » ----------------------------------------------------------
# Dossier contenant les .qml (et éventuellement les .svg), exploré récursivement.
# Exemple : D:\\git\\DDU-SG5-SYMBOLISATION\\PLU
local_source =


[sortie]
# Dossier de sortie. Il contiendra styles/ , styles/svg/cnig/ et les rapports.
# L'arborescence est créée automatiquement.
#
# UN CHEMIN RELATIF EST RÉSOLU PAR RAPPORT AU DOSSIER DU SCRIPT, jamais par
# rapport au répertoire courant : depuis la console QGIS, celui-ci vaut souvent
# « C:\\Program Files\\QGIS 3.xx\\bin », où l'écriture est refusée.
# « out = build » place donc la sortie à côté du .py, et l'ensemble reste
# portable si vous déplacez le dossier.
# Un chemin absolu est utilisé tel quel.
out = build
# Vider les *.sld existants avant génération (true / false).
clean = false


[conversion]
# Backend de conversion :
#   auto       -> qgis si PyQGIS est disponible, sinon standalone
#   qgis       -> impose la chaîne bridge-style complète (nécessite PyQGIS)
#   standalone -> parseur QML intégré, aucune dépendance QGIS
backend = auto

# Réinjection des hachures exactes lues dans le QML (phase 4).
# Ne passer à false que pour diagnostiquer ce que produit bridge-style seul.
hatch_fix = true

# Installer automatiquement bridgestyle s'il manque dans l'interpréteur Python
# utilisé (celui de QGIS lorsque le script tourne dans la console QGIS).
# Si l'installation réussit mais que le paquet ne peut pas être chargé dans la
# session en cours, le script demande explicitement de redémarrer QGIS.
auto_install = true


[svg]
# Sous-dossier des pictogrammes, relatif à styles/.
# Les <OnlineResource> des SLD pointent vers ce chemin : le modifier ici suffit,
# les SLD sont réécrits en conséquence.
subdir = svg/cnig


[reseau]
# Proxy d'entreprise. Laisser vide pour une détection automatique, qui examine
# dans l'ordre : les variables d'environnement HTTPS_PROXY / HTTP_PROXY, la
# configuration réseau de QGIS (Préférences > Options > Réseau), puis les
# paramètres proxy de Windows.
# proxy = http://utilisateur:motdepasse@serveur:8080
proxy =

# Roue .whl (ou dossier de roues) pour une installation hors ligne de
# bridgestyle, sur un poste sans accès à PyPI. Préparation depuis un poste
# connecté :   pip download bridgestyle lxml requests -d paquets
# bridgestyle_wheel = C:\\chemin\\paquets
bridgestyle_wheel =


[mbstyle]
# Export supplémentaire au format MBStyle (Mapbox GL Style JSON), publiable par
# l'extension « mbstyle » de GeoServer sur des couches vectorielles tuilées.
# Un fichier .json est écrit à côté de chaque .sld, plus une feuille de sprites
# (sprite.png, sprite.json et leurs équivalents @2x) contenant les pictogrammes
# CNIG et les motifs de hachure rendus en images.
enabled = false

# Racine de l'instance GeoServer, utilisée pour construire les URL de tuiles,
# de sprites et de glyphes inscrites dans le JSON.
base_url = http://localhost:8080/geoserver

# Espace de travail des couches vectorielles tuilées.
workspace =

# URL explicites, si votre déploiement ne suit pas les chemins par défaut.
# sprite_url = http://mon-serveur/ressources/sprite
# glyphs_url = http://mon-serveur/fonts/{fontstack}/{range}.pbf
sprite_url =
glyphs_url =

# Côté des vignettes de la feuille de sprites, en pixels.
sprite_size = 64

# Génération effective des images. Nécessite Qt, toujours présent dans QGIS.
build_sprites = true


[geoserver]
# Publication REST automatique en fin de chaîne (optionnelle).
# Laisser « url » vide pour ne rien publier.
url =
# url = http://localhost:8080/geoserver
user = admin
password = geoserver
# Espace de travail cible. Vide = styles globaux.
workspace =


# ==============================================================================
#  VendorOptions GeoServer injectées en phase 4.
#  Chaque clé = un nom de VendorOption, chaque valeur = sa valeur.
#  Supprimer une ligne désactive l'injection de cette option.
# ==============================================================================

# Motifs et hachures surfaciques.
[vendor.polygon_graphicfill]
graphic-margin = 0

# Étiquetage, toutes géométries.
[vendor.text]
group = yes
spaceAround = 10
maxDisplacement = 40
conflictResolution = true
goodnessOfFit = 0.3
partials = false
autoWrap = 60

# Étiquetage, géométries linéaires uniquement.
[vendor.text_line]
followLine = true
repeat = 150
maxAngleDelta = 30

# Étiquetage, géométries surfaciques uniquement.
[vendor.text_polygon]
polygonAlign = mbr
"""

#: Catégories de « cas de figure cartographiques » utilisées pour le calcul de
#: la combinaison couvrante minimale (PHASE 1).
FEATURE_FLAGS: Tuple[str, ...] = (
    "LinePatternFill", "SVGFill", "PointPatternFill", "CentroidFill",
    "MarkerLine", "ArrowLine", "HashLine", "SvgMarker", "FontMarker",
    "RasterFill", "GradientFill", "ShapeburstFill", "GeometryGenerator",
    "offset", "customdash", "labeling", "labeling_rules", "labeling_callout",
    "data_defined", "scale_dependent", "blend_mode", "symbol_levels",
    "multi_rule", "multi_symbollayer",
)


# ==============================================================================
#  SECTION 1 — UTILITAIRES GÉNÉRIQUES
# ==============================================================================

#: Horodatage du dernier rafraîchissement d'interface, pour l'étranglement.
_LAST_PUMP = [0.0]

#: Intervalle minimal entre deux rafraîchissements, en secondes.
PUMP_INTERVAL = 0.20


def pump_ui(force: bool = False) -> None:
    """
    Laisse l'interface de QGIS se repeindre pendant un traitement long.

    La console Python de QGIS s'exécute dans le thread de l'interface : tant
    qu'un traitement synchrone tourne, la boucle d'événements Qt est bloquée,
    les print() partent dans le tampon et rien ne s'affiche avant la fin.
    processEvents() rend brièvement la main à Qt pour repeindre.

    DEUX PRÉCAUTIONS, apprises à l'usage :

    1. ÉTRANGLEMENT. Appeler processEvents() à CHAQUE écriture coûte plus cher
       que le traitement lui-même sur un corpus volumineux : des centaines de
       lignes de journal deviennent des centaines de cycles complets de boucle
       d'événements. On se limite donc à un rafraîchissement toutes les 200 ms,
       ce qui suffit largement à l'œil.

    2. EXCLUSION DES ÉVÉNEMENTS D'ENTRÉE. Sans ExcludeUserInputEvents, Qt
       distribue aussi les clics et les touches pendant le traitement :
       l'utilisateur peut relancer le script, fermer le projet ou modifier une
       couche en pleine conversion. C'est une source classique de plantage par
       réentrance. On ne laisse donc passer que les événements de rendu.

    À n'appeler QUE depuis le thread principal.
    """
    try:
        import time
        now = time.monotonic()
        if not force and now - _LAST_PUMP[0] < PUMP_INTERVAL:
            return
        _LAST_PUMP[0] = now
        from qgis.PyQt.QtCore import QCoreApplication, QEventLoop  # type: ignore
        app = QCoreApplication.instance()
        if app is not None:
            app.processEvents(QEventLoop.ExcludeUserInputEvents)
    except Exception:                                          # noqa: BLE001
        pass


class Console:
    """
    Affichage console lisible, compatible PowerShell (pas d'emoji exotique)
    et console Python de QGIS.

    Chaque écriture force le vidage du tampon et rend la main à Qt : c'est ce
    qui permet de suivre l'avancement en direct depuis QGIS.
    """

    #: Désactivé automatiquement si la sortie n'est pas un terminal.
    ENABLED = sys.stdout.isatty()

    @staticmethod
    def raw(msg: str = "", stream=None) -> None:
        print(msg, file=stream or sys.stdout, flush=True)
        pump_ui()

    @staticmethod
    def rule(title: str = "", char: str = "=", width: int = 78) -> None:
        if title:
            pad = max(0, width - len(title) - 4)
            Console.raw(f"{char * 2} {title} {char * pad}")
        else:
            Console.raw(char * width)

    @staticmethod
    def info(msg: str) -> None:
        Console.raw(f"[INFO ] {msg}")

    @staticmethod
    def ok(msg: str) -> None:
        Console.raw(f"[ OK  ] {msg}")

    @staticmethod
    def warn(msg: str) -> None:
        Console.raw(f"[WARN ] {msg}")

    @staticmethod
    def err(msg: str) -> None:
        Console.raw(f"[ERREUR] {msg}", stream=sys.stderr)

    @staticmethod
    def step(msg: str) -> None:
        Console.raw(f"\n>>> {msg}")


# ------------------------------------------------------------------------------
#  Détection du proxy d'entreprise
# ------------------------------------------------------------------------------
#
#  Sur un poste d'entreprise, l'accès direct à pypi.org et à github.com est
#  généralement bloqué : pip échoue sur « ConnectTimeoutError ... Connection to
#  pypi.org timed out » après quatre tentatives, puis conclut à tort
#  « No matching distribution found for bridgestyle ».
#
#  QGIS, lui, fonctionne souvent : il possède SA PROPRE configuration de proxy
#  (Préférences > Options > Réseau), indépendante des variables d'environnement.
#  On va donc la chercher là où elle est, plutôt que de demander à
#  l'utilisateur de la ressaisir.
#
#  Ordre de recherche, du plus explicite au plus implicite :
#    1. l'option --proxy ou la section [reseau] du fichier de configuration
#    2. les variables d'environnement HTTPS_PROXY / HTTP_PROXY / ALL_PROXY
#    3. la configuration réseau de QGIS (QSettings)
#    4. les paramètres proxy de Windows (base de registre WinINET)
# ------------------------------------------------------------------------------

#: Proxy retenu pour toute la session (None = accès direct).
PROXY_URL: Optional[str] = None


def detect_proxy(explicit: Optional[str] = None) -> Optional[str]:
    """Retourne l'URL de proxy à utiliser, ou None pour un accès direct."""
    if explicit:
        return explicit

    # --- 2. variables d'environnement --------------------------------
    for var in ("HTTPS_PROXY", "https_proxy", "HTTP_PROXY", "http_proxy",
                "ALL_PROXY", "all_proxy"):
        value = os.environ.get(var)
        if value:
            return value.strip()

    # --- 3. configuration réseau de QGIS ------------------------------
    try:
        from qgis.PyQt.QtCore import QSettings                 # type: ignore
        settings = QSettings()
        enabled = settings.value("proxy/proxyEnabled", False, type=bool)
        if enabled:
            host = str(settings.value("proxy/proxyHost", "") or "").strip()
            port = str(settings.value("proxy/proxyPort", "") or "").strip()
            user = str(settings.value("proxy/proxyUser", "") or "").strip()
            password = str(settings.value("proxy/proxyPassword", "") or "")
            if host:
                auth = ""
                if user:
                    auth = (f"{urllib.parse.quote(user, safe='')}:"
                            f"{urllib.parse.quote(password, safe='')}@")
                port_part = f":{port}" if port else ""
                return f"http://{auth}{host}{port_part}"
    except Exception:                                          # noqa: BLE001
        pass

    # --- 4. paramètres proxy de Windows -------------------------------
    if os.name == "nt":
        try:
            import winreg                                      # type: ignore
            path = (r"Software\Microsoft\Windows\CurrentVersion"
                    r"\Internet Settings")
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, path) as key:
                enable, _ = winreg.QueryValueEx(key, "ProxyEnable")
                if enable:
                    server, _ = winreg.QueryValueEx(key, "ProxyServer")
                    server = str(server or "").strip()
                    if server:
                        # Deux formes possibles : « hote:port » ou
                        # « http=hote:port;https=autre:port »
                        if "=" in server:
                            mapping = {}
                            for part in server.split(";"):
                                if "=" in part:
                                    scheme, value = part.split("=", 1)
                                    mapping[scheme.strip().lower()] = value.strip()
                            server = (mapping.get("https") or mapping.get("http")
                                      or next(iter(mapping.values()), ""))
                        if server:
                            if "://" not in server:
                                server = "http://" + server
                            return server
        except Exception:                                      # noqa: BLE001
            pass

    return None


def apply_proxy(proxy: Optional[str]) -> None:
    """
    Installe le proxy pour les requêtes du script lui-même.

    urllib n'utilise les variables d'environnement qu'au premier appel : on
    installe donc explicitement un ProxyHandler. On renseigne aussi les
    variables d'environnement, ce qui couvre requests et les sous-processus pip.
    """
    global PROXY_URL
    PROXY_URL = proxy
    if not proxy:
        return
    os.environ.setdefault("HTTP_PROXY", proxy)
    os.environ.setdefault("HTTPS_PROXY", proxy)
    handler = urllib.request.ProxyHandler({"http": proxy, "https": proxy})
    urllib.request.install_opener(urllib.request.build_opener(handler))


def describe_proxy(proxy: Optional[str]) -> str:
    """Masque le mot de passe avant tout affichage."""
    if not proxy:
        return "accès direct (aucun proxy)"
    return re.sub(r"://([^:/@]+):([^@]*)@", r"://\1:***@", proxy)


def http_get(url: str, timeout: int = 60, binary: bool = False,
             token: Optional[str] = None) -> Any:
    """
    GET HTTP unifié : utilise `requests` s'il est installé, sinon `urllib`.
    Ajoute un User-Agent (GitHub refuse les requêtes anonymes sans UA) et,
    si fourni, un jeton d'API GitHub (utile pour dépasser les 60 req/h).
    """
    headers = {"User-Agent": "cnig-qml2sld/1.0 (+GeoServer pipeline)"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if _HAS_REQUESTS:
        resp = requests.get(url, headers=headers, timeout=timeout)
        resp.raise_for_status()
        return resp.content if binary else resp.text
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=timeout) as fh:   # nosec B310
        data = fh.read()
    return data if binary else data.decode("utf-8", errors="replace")


# ------------------------------------------------------------------------------
#  Vérification et installation automatique de bridgestyle
# ------------------------------------------------------------------------------
#
#  QGIS embarque SON PROPRE interpréteur Python, distinct du Python système.
#  Un « pip install bridgestyle » lancé depuis une invite de commandes ordinaire
#  installe donc le paquet là où QGIS ne le verra jamais. C'est la cause n°1
#  d'échec au premier lancement depuis la console Python de QGIS.
#
#  Difficulté supplémentaire : dans la console QGIS, sys.executable ne vaut PAS
#  python.exe mais qgis-bin.exe. On ne peut donc pas écrire naïvement
#  [sys.executable, "-m", "pip", ...] ; il faut retrouver le python.exe voisin.
# ------------------------------------------------------------------------------

def _import_bridgestyle() -> Optional[str]:
    """Retourne la version de bridgestyle s'il est importable, sinon None."""
    try:
        import bridgestyle                                     # type: ignore
        return getattr(bridgestyle, "__version__", "?")
    except Exception:                                          # noqa: BLE001
        return None


def _bridgestyle_usable() -> Tuple[Optional[str], Optional[str]]:
    """
    Vérifie que bridgestyle est non seulement INSTALLÉ, mais UTILISABLE.

    La distinction n'est pas théorique. « import bridgestyle » réussit toujours
    dès que le paquet est présent : son __init__.py se réduit à
    « from .version import __version__ ». Le module réellement employé par le
    backend autonome est bridgestyle.sld.fromgeostyler, et c'est LUI qui casse
    sans PyQGIS, à cause de la chaîne d'imports circulaire décrite en
    SECTION 0-bis. Se contenter du premier import annoncerait donc « présent,
    on continue » sur une installation inexploitable.

    On pose le shim au passage, ce qui rend le module SLD importable sans QGIS.

    Retourne (version, raison_d_echec) :
      (None, None)          -> paquet absent
      ("0.1.9", None)       -> installé ET utilisable
      ("0.1.9", "message")  -> installé mais module SLD inutilisable
    """
    global SLD_SHIM_FORCED
    version = _import_bridgestyle()
    if version is None:
        return (None, None)

    install_bridgestyle_sld_shim()
    try:
        import bridgestyle.sld.fromgeostyler                   # type: ignore  # noqa
        return (version, None)
    except Exception as first:                                 # noqa: BLE001
        reason = f"{type(first).__name__}: {first}"

    # Seconde tentative, shim imposé. Cas typique : PyQGIS est présent mais sa
    # version ne convient pas à bridgestyle, qui lève CompatibilityException
    # dès l'import. Sans cette reprise, le script s'arrêterait là alors que le
    # backend autonome, lui, aurait parfaitement fonctionné.
    for name in [k for k in list(sys.modules)
                 if k.startswith(("bridgestyle.qgis", "bridgestyle.sld",
                                  "bridgestyle.mapboxgl"))]:
        del sys.modules[name]
    install_bridgestyle_sld_shim(force=True)
    try:
        import bridgestyle.sld.fromgeostyler                   # type: ignore  # noqa
        SLD_SHIM_FORCED = True
        Console.warn("bridgestyle refuse de s'initialiser avec cette version "
                     "de QGIS : " + reason)
        Console.info("Bascule automatique sur le backend autonome, qui produit "
                     "le même résultat sur le corpus CNIG.")
        return (version, None)
    except Exception as second:                                # noqa: BLE001
        return (version, f"{reason} | après contournement : {second}")


def find_python_executable() -> Optional[str]:
    """
    Localise l'exécutable python de l'environnement COURANT.

    Dans la console QGIS, sys.executable vaut qgis-bin.exe : le python.exe
    recherché se trouve dans le même dossier bin/. On teste plusieurs
    emplacements, du plus probable au plus général.
    """
    candidates: List[str] = []
    exe = Path(sys.executable)

    # 1. sys.executable est déjà un python (ligne de commande, python-qgis.bat)
    if exe.name.lower().startswith("python"):
        candidates.append(str(exe))
    # 2. python.exe voisin de qgis-bin.exe (console QGIS sous Windows)
    for name in ("python.exe", "python3.exe", "python", "python3"):
        candidates.append(str(exe.parent / name))
    # 3. Répertoire des scripts de l'installation Python courante
    try:
        import sysconfig
        for key in ("scripts", "purelib"):
            base = sysconfig.get_paths().get(key)
            if base:
                root = Path(base).parent
                for name in ("python.exe", "python3.exe", "python", "python3"):
                    candidates.append(str(root / name))
    except Exception:                                          # noqa: BLE001
        pass
    # 4. sys.prefix
    for sub in ("", "bin", "Scripts"):
        for name in ("python.exe", "python3.exe", "python", "python3"):
            candidates.append(str(Path(sys.prefix) / sub / name))

    seen: Set[str] = set()
    for candidate in candidates:
        if candidate in seen:
            continue
        seen.add(candidate)
        if Path(candidate).is_file():
            return candidate
    return None


def _refresh_optional_dependencies() -> None:
    """
    Recharge lxml et requests après une installation à chaud.

    _HAS_LXML et _HAS_REQUESTS sont évalués une fois pour toutes au chargement
    du module. Si l'installation automatique vient de les ajouter, ces drapeaux
    resteraient à False et le script continuerait sur ses implémentations de
    repli alors que les bibliothèques sont désormais disponibles.
    """
    global LET, _HAS_LXML, requests, _HAS_REQUESTS
    if not _HAS_LXML:
        try:
            from lxml import etree as _lxml_etree              # type: ignore
            LET, _HAS_LXML = _lxml_etree, True
        except Exception:                                      # noqa: BLE001
            pass
    if not _HAS_REQUESTS:
        try:
            import requests as _requests                       # type: ignore
            requests, _HAS_REQUESTS = _requests, True
        except Exception:                                      # noqa: BLE001
            pass


def ensure_bridgestyle(auto_install: bool = True,
                       quiet: bool = False,
                       wheel: Optional[Path] = None) -> Tuple[str, str]:
    """
    Garantit que bridgestyle est importable dans l'interpréteur courant.

    Retourne un couple (état, détail) où l'état vaut :
      « present »  -> déjà installé, rien à faire, on continue
      « installed »-> installé à l'instant ET immédiatement utilisable
      « restart »  -> installé, mais un REDÉMARRAGE DE QGIS est nécessaire
      « absent »   -> manquant, installation non tentée (auto_install=False)
      « failed »   -> tentative d'installation en échec (détail = message)

    L'installation vise l'interpréteur courant, donc celui de QGIS lorsque le
    script tourne dans la console QGIS : c'est exactement ce qu'il faut.
    """
    version, reason = _bridgestyle_usable()
    if version and reason is None:
        return ("present", version)
    if version and reason:
        # Paquet présent mais module SLD inutilisable : réinstaller n'y
        # changerait rien, c'est un défaut de la bibliothèque elle-même.
        return ("broken", reason)
    if not auto_install:
        return ("absent", "")

    python = find_python_executable()
    if python is None:
        return ("failed", "interpréteur python introuvable "
                          f"(sys.executable = {sys.executable})")

    # On profite de l'installation pour combler les dépendances optionnelles.
    packages = ["bridgestyle"]
    if not _HAS_LXML:
        packages.append("lxml")
    if not _HAS_REQUESTS:
        packages.append("requests")

    if not quiet:
        Console.warn("bridgestyle est absent de cet interpréteur Python.")
        Console.info(f"Installation automatique via {python}")
        Console.info(f"Paquets : {', '.join(packages)} — patientez...")

    import subprocess                                          # nosec B404
    proxy = PROXY_URL or detect_proxy()
    base = [python, "-m", "pip", "install", "--disable-pip-version-check",
            "--timeout", "30", "--retries", "2"]
    if proxy:
        base += ["--proxy", proxy]
        if not quiet:
            Console.info(f"Proxy utilisé : {describe_proxy(proxy)}")

    def run(cmd: List[str], verbose: bool = True) -> Tuple[int, str]:
        """
        Exécute pip en affichant son avancement EN DIRECT.

        Deux pièges évités ici.

        1. LA FENÊTRE NOIRE. Sous Windows, lancer un sous-processus depuis une
           application graphique ouvre une console qui vole le focus et masque
           QGIS. CREATE_NO_WINDOW la supprime.

        2. LA CONSOLE FIGÉE. subprocess.run(capture_output=True) ne rend la
           main qu'à la fin : pendant une à deux minutes, l'utilisateur n'a
           aucun retour. On lit donc la sortie au fil de l'eau, dans un thread
           dédié, pendant que le thread principal affiche l'avancement, émet un
           battement régulier quand pip reste silencieux, et laisse Qt
           rafraîchir la console.
        """
        import queue
        import threading
        import time

        kwargs: Dict[str, Any] = {}
        if os.name == "nt":
            # 0x08000000 = CREATE_NO_WINDOW, absent des vieux Python
            kwargs["creationflags"] = getattr(subprocess, "CREATE_NO_WINDOW",
                                              0x08000000)
        try:
            proc = subprocess.Popen(                           # nosec B603
                cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, encoding="utf-8", errors="replace", bufsize=1,
                **kwargs)
        except Exception as exc:                               # noqa: BLE001
            return -1, str(exc)

        channel: "queue.Queue[Optional[str]]" = queue.Queue()

        def reader() -> None:
            try:
                assert proc.stdout is not None
                for raw_line in proc.stdout:
                    channel.put(raw_line)
            except Exception:                                  # noqa: BLE001
                pass
            channel.put(None)

        threading.Thread(target=reader, daemon=True).start()

        # Étapes de pip dignes d'être affichées ; le reste part dans le journal.
        keep = ("collecting", "downloading", "using cached", "installing",
                "building", "preparing", "successfully", "requirement already",
                "error", "erreur", "warning: ")

        collected: List[str] = []
        started = time.time()
        last_news = started
        finished = False

        while not finished:
            try:
                item = channel.get(timeout=0.25)
            except queue.Empty:
                item = ""
            if item is None:
                finished = True
            elif item:
                line = item.rstrip()
                collected.append(line)
                if verbose and line and line.lower().startswith(keep):
                    Console.raw(f"         {line[:104]}")
                last_news = time.time()

            now = time.time()
            if verbose and not finished and now - last_news > 6:
                Console.raw(f"         ... toujours en cours "
                            f"({int(now - started)} s écoulées)")
                last_news = now
            pump_ui()

            if now - started > 900:
                proc.kill()
                return -1, "délai dépassé (15 minutes)"

        try:
            proc.wait(timeout=30)
        except Exception:                                      # noqa: BLE001
            proc.kill()
        if verbose:
            Console.info(f"      terminé en {int(time.time() - started)} s")
        return proc.returncode or 0, "\n".join(collected)

    if wheel is not None:
        # Installation HORS LIGNE : la roue (ou le dossier de roues) a été
        # récupérée depuis un poste connecté. --no-index interdit tout accès
        # réseau, ce qui évite de repartir dans un délai d'attente de 15 s x 4.
        source = Path(wheel).expanduser()
        if not source.exists():
            return ("failed", f"fichier introuvable : {source}")
        if not quiet:
            Console.info(f"Installation hors ligne depuis {source}")
        if source.is_dir():
            code, output = run([python, "-m", "pip", "install", "--no-index",
                                "--find-links", str(source)] + packages)
        else:
            code, output = run([python, "-m", "pip", "install", "--no-index",
                                str(source)])
    else:
        code, output = run(base + packages)

    # pip absent de l'installation QGIS : on l'amorce puis on réessaie.
    if code != 0 and "No module named pip" in output:
        if not quiet:
            Console.info("pip absent, amorçage via ensurepip...")
        run([python, "-m", "ensurepip", "--upgrade"], verbose=False)
        code, output = run(base + packages)

    # Dossier système non accessible en écriture (Program Files sans droits
    # administrateur) : on bascule sur une installation utilisateur.
    if code != 0 and any(marker in output for marker in
                         ("Permission denied", "Access is denied", "EnvironmentError",
                          "Could not install packages due to an OSError", "WinError 5")):
        if not quiet:
            Console.info("Droits insuffisants sur le dossier système, "
                         "bascule sur une installation utilisateur (--user)...")
        code, output = run(base + ["--user"] + packages)

    if code != 0:
        # Seconde chance : si aucun proxy n'avait été trouvé mais que l'échec
        # est clairement réseau, on retente en laissant pip utiliser la
        # configuration système (certains environnements l'exposent autrement).
        kind = _classify_pip_failure(output)
        if kind == "network" and not proxy:
            detected = detect_proxy()
            if detected:
                if not quiet:
                    Console.info(f"Nouvelle tentative via le proxy détecté : "
                                 f"{describe_proxy(detected)}")
                code, output = run(base + ["--proxy", detected] + packages)
                kind = _classify_pip_failure(output) if code else ""
        if code != 0:
            tail = "\n".join(l for l in output.strip().splitlines()[-8:])
            return (kind or "failed", tail or f"code de retour {code}")

    # --- L'installation a réussi : le paquet est-il utilisable TOUT DE SUITE ?
    # Un paquet installé pendant que l'interpréteur tourne n'est pas
    # automatiquement visible : les caches d'import doivent être invalidés, et
    # le dossier « user site » peut ne pas figurer dans sys.path s'il n'existait
    # pas au démarrage de QGIS.
    import importlib
    importlib.invalidate_caches()
    try:
        import site
        for extra in (site.getusersitepackages(), *site.getsitepackages()):
            if extra and extra not in sys.path and Path(extra).is_dir():
                sys.path.append(extra)
    except Exception:                                          # noqa: BLE001
        pass

    _refresh_optional_dependencies()

    version, reason = _bridgestyle_usable()
    if version and reason is None:
        return ("installed", version)
    if version and reason:
        return ("broken", reason)

    # Dernier recours : demander à l'interpréteur cible où il a installé le
    # paquet, et ajouter ce chemin à sys.path.
    code, output = run([python, "-c",
                        "import bridgestyle, os; print(os.path.dirname("
                        "os.path.dirname(bridgestyle.__file__)))"], verbose=False)
    if code == 0 and output.strip():
        candidate = output.strip().splitlines()[-1]
        if Path(candidate).is_dir() and candidate not in sys.path:
            sys.path.append(candidate)
            importlib.invalidate_caches()
            version, reason = _bridgestyle_usable()
            if version and reason is None:
                return ("installed", version)

    return ("restart", "")


#: Signatures d'échec de pip, pour distinguer un problème de réseau d'un vrai
#: problème de paquet et donner un diagnostic utile plutôt qu'un message générique.
_PIP_NETWORK_MARKERS = (
    "connecttimeouterror", "read timed out", "timed out", "proxyerror",
    "failed to establish a new connection", "temporary failure in name resolution",
    "getaddrinfo failed", "network is unreachable", "no matching distribution",
    "could not find a version that satisfies", "connection broken",
    "connection refused", "retrying (retry",
)
_PIP_SSL_MARKERS = (
    "certificate verify failed", "sslcertverificationerror", "ssl: certificate",
    "sslerror", "self signed certificate", "unable to get local issuer",
)


def _classify_pip_failure(output: str) -> str:
    """Retourne « ssl », « network » ou « failed » selon la sortie de pip."""
    low = (output or "").lower()
    if any(m in low for m in _PIP_SSL_MARKERS):
        return "ssl"
    if any(m in low for m in _PIP_NETWORK_MARKERS):
        return "network"
    return "failed"


def _explain_offline_install(python_hint: str = "<python de QGIS>") -> None:
    """Marche à suivre quand le poste n'a pas accès à PyPI."""
    Console.info("")
    Console.info("SOLUTION DE REPLI — installation hors ligne :")
    Console.info("  1. Depuis un poste ayant accès à Internet :")
    Console.info("       pip download bridgestyle lxml requests -d paquets")
    Console.info("  2. Copiez le dossier « paquets » sur ce poste, puis :")
    Console.info(f"       {python_hint} -m pip install --no-index "
                 "--find-links paquets bridgestyle lxml requests")
    Console.info("")
    Console.info("Ou récupérez la roue directement et relancez avec :")
    Console.info("       --bridgestyle-wheel C:\\chemin\\bridgestyle-0.1.9-py3-none-any.whl")


def report_bridgestyle_state(state: str, detail: str) -> bool:
    """
    Affiche le résultat de ensure_bridgestyle() et indique si l'on peut
    poursuivre le traitement (True) ou s'il faut s'arrêter (False).
    """
    if state == "present":
        Console.ok(f"bridgestyle {detail} déjà installé — poursuite du traitement.")
        return True
    if state == "installed":
        Console.ok(f"bridgestyle {detail} installé et chargé — "
                   f"poursuite du traitement, aucun redémarrage nécessaire.")
        return True
    if state == "restart":
        print()
        Console.rule("REDÉMARRAGE DE QGIS NÉCESSAIRE", "!")
        Console.ok("bridgestyle a bien été installé.")
        Console.warn("Il ne peut pas être chargé dans la session en cours : "
                     "Python avait déjà exploré ses chemins de modules au "
                     "démarrage de QGIS.")
        Console.info("FERMEZ ET ROUVREZ QGIS, puis relancez le script.")
        Console.rule("", "!")
        return False
    if state == "broken":
        Console.err("bridgestyle est installé mais son module SLD ne peut pas "
                    "être chargé.")
        Console.info(f"   {detail}")
        Console.info("Le contournement intégré (SECTION 0-bis) n'a pas suffi. "
                     "Causes possibles : version de bridgestyle très différente "
                     "de 0.1.9, ou installation partielle.")
        Console.info("Piste : réinstaller proprement avec")
        Console.info("   <python> -m pip install --force-reinstall bridgestyle")
        return False
    if state == "absent":
        Console.err("bridgestyle est absent et l'installation automatique est "
                    "désactivée (--no-auto-install).")
        Console.info("Installation manuelle : "
                     "<python de QGIS> -m pip install bridgestyle lxml requests")
        return False
    if state == "network":
        Console.rule("ACCES A PyPI IMPOSSIBLE DEPUIS CE POSTE", "!")
        Console.err("pip n'a pas pu joindre pypi.org.")
        Console.info(f"Proxy essayé : {describe_proxy(PROXY_URL or detect_proxy())}")
        Console.info("")
        Console.info("Le message « No matching distribution found » de pip est")
        Console.info("trompeur : le paquet existe, c'est la connexion qui échoue.")
        Console.info("")
        Console.info("À vérifier, dans cet ordre :")
        Console.info("  - QGIS a-t-il un proxy configuré ?")
        Console.info("      Préférences > Options > Réseau > Utiliser un proxy.")
        Console.info("      Le script le réutilise automatiquement s'il est renseigné.")
        Console.info("  - Sinon, indiquez-le explicitement :")
        Console.info("      --proxy http://utilisateur:motdepasse@serveur:port")
        Console.info("      ou la section [reseau] du fichier cnig_qml2sld.ini")
        Console.info("  - Si votre réseau autorise seulement certains sites,")
        Console.info("    demandez l'ouverture de pypi.org et files.pythonhosted.org,")
        Console.info("    ou utilisez la solution de repli ci-dessous.")
        _explain_offline_install()
        Console.rule("", "!")
        return False
    if state == "ssl":
        Console.rule("CERTIFICAT TLS REFUSE", "!")
        Console.err("La connexion à PyPI est interceptée par un équipement "
                    "d'entreprise dont le certificat n'est pas reconnu.")
        Console.info("")
        Console.info("Solution propre — déclarer le certificat racine de votre")
        Console.info("entreprise (demandez le fichier .pem au service informatique) :")
        Console.info("      setx REQUESTS_CA_BUNDLE C:\\chemin\\entreprise.pem")
        Console.info("      setx SSL_CERT_FILE      C:\\chemin\\entreprise.pem")
        Console.info("")
        Console.info("Solution de contournement, à n'employer qu'en connaissance")
        Console.info("de cause car elle désactive la vérification du certificat :")
        Console.info("      <python de QGIS> -m pip install bridgestyle \\")
        Console.info("          --trusted-host pypi.org --trusted-host files.pythonhosted.org")
        _explain_offline_install()
        Console.rule("", "!")
        return False
    Console.err(f"L'installation automatique de bridgestyle a échoué : {detail}")
    Console.info("Installation manuelle depuis la console Python de QGIS :")
    Console.info('   import os, sys, subprocess')
    Console.info('   py = os.path.join(os.path.dirname(sys.executable), "python.exe")')
    Console.info('   subprocess.check_call([py, "-m", "pip", "install", "bridgestyle"])')
    Console.info("   puis redémarrer QGIS.")
    return False


# ==============================================================================
#  SECTION 2 — ACQUISITION DES SOURCES (dépôt CNIG)
# ==============================================================================

@dataclass
class SourceFiles:
    """Inventaire des fichiers sources récupérés."""
    qml: List[Path] = field(default_factory=list)
    svg: List[Path] = field(default_factory=list)
    root: Optional[Path] = None

    def summary(self) -> str:
        return f"{len(self.qml)} fichier(s) .qml, {len(self.svg)} pictogramme(s) .svg"


class CnigRepository:
    """
    Récupération des QML et SVG du dépôt CNIG.

    Deux modes :
      * `--local-source` : on pointe un clone git ou un dossier déjà téléchargé
        (aucun accès réseau, idéal en environnement fermé / proxy d'entreprise).
      * mode réseau : API Git Trees de GitHub en `recursive=1`, puis
        téléchargement via raw.githubusercontent.com.
    """

    API_TREE = "https://api.github.com/repos/{repo}/git/trees/{branch}?recursive=1"
    RAW = "https://raw.githubusercontent.com/{repo}/{branch}/{path}"

    def __init__(self, repo: str, branch: str, subpath: str,
                 cache_dir: Path, token: Optional[str] = None) -> None:
        self.repo = repo
        self.branch = branch
        # Plusieurs sous-dossiers séparés par des virgules : « PLU,PSMV,SUP ».
        # Une chaîne vide signifie « tout le dépôt ».
        self.subpaths = [s.strip().strip("/") for s in str(subpath).split(",")
                         if s.strip().strip("/")]
        self.subpath = ", ".join(self.subpaths) or "(tout le dépôt)"
        self.cache_dir = cache_dir
        self.token = token or os.environ.get("GITHUB_TOKEN")

    # ---------------------------------------------------------------- réseau
    def _resolve_branch(self) -> str:
        """Teste la branche demandée puis les branches de repli."""
        candidates = [self.branch] + [b for b in FALLBACK_BRANCHES if b != self.branch]
        last_error: Optional[Exception] = None
        for branch in candidates:
            url = self.API_TREE.format(repo=self.repo,
                                       branch=urllib.parse.quote(branch, safe=""))
            try:
                payload = json.loads(http_get(url, token=self.token))
                if "tree" in payload:
                    if branch != self.branch:
                        Console.warn(f"Branche '{self.branch}' introuvable, "
                                     f"bascule automatique sur '{branch}'.")
                    self.branch = branch
                    self._tree = payload["tree"]
                    if payload.get("truncated"):
                        Console.warn("L'arbre Git renvoyé par GitHub est TRONQUÉ "
                                     "(dépôt volumineux). Préférez --local-source "
                                     "sur un clone complet.")
                    return branch
            except Exception as exc:                          # noqa: BLE001
                last_error = exc
        raise RuntimeError(
            f"Impossible de lire l'arborescence du dépôt {self.repo}. "
            f"Dernière erreur : {last_error}\n"
            f"Contournement : cloner le dépôt puis utiliser --local-source."
        )

    def fetch_remote(self) -> SourceFiles:
        Console.step(f"Lecture de l'arborescence GitHub : {self.repo} "
                     f"(branche '{self.branch}', dossier '{self.subpath or '/'}')")
        self._resolve_branch()

        prefixes = tuple(f"{s}/" for s in self.subpaths)

        def retenu(chemin: str) -> bool:
            if chemin.startswith(EXCLUDED_PREFIXES):
                return False
            return chemin.startswith(prefixes) if prefixes else True

        wanted = [
            node for node in self._tree
            if node.get("type") == "blob"
            and retenu(node["path"])
            and node["path"].lower().endswith((".qml", ".svg"))
        ]
        if not wanted:
            raise RuntimeError(
                f"Aucun .qml/.svg trouvé sous '{self.subpath}'. "
                f"Vérifiez --subpath (essayez '' pour balayer tout le dépôt)."
            )

        # Compte rendu par famille de documents : utile pour vérifier d'un
        # coup d'œil qu'aucun type n'a été oublié.
        par_famille: Dict[str, List[int]] = {}
        for node in wanted:
            famille = node["path"].split("/", 1)[0]
            compte = par_famille.setdefault(famille, [0, 0])
            compte[0 if node["path"].lower().endswith(".qml") else 1] += 1
        for famille in sorted(par_famille):
            qml_n, svg_n = par_famille[famille]
            Console.info(f"   {famille:<16} {qml_n:>3} QML   {svg_n:>5} SVG")

        qml_dir = self.cache_dir / "qml"
        svg_dir = self.cache_dir / "svg"
        qml_dir.mkdir(parents=True, exist_ok=True)
        svg_dir.mkdir(parents=True, exist_ok=True)

        out = SourceFiles(root=self.cache_dir)
        total = len(wanted)
        started = time.time()
        Console.info(f"{total} fichiers à récupérer "
                     f"({sum(1 for n in wanted if n['path'].lower().endswith('.qml'))} QML, "
                     f"{sum(1 for n in wanted if n['path'].lower().endswith('.svg'))} SVG). "
                     f"Le cache évite de recommencer au prochain lancement.")
        # TÉLÉCHARGEMENT PARALLÈLE. Le corpus complet (PLU + PSMV + SUP)
        # compte près de 1 100 fichiers : en séquentiel, c'est une dizaine de
        # minutes, dominées par la latence réseau et non par la bande passante.
        # Huit requêtes simultanées ramènent cela à environ une minute, sans
        # solliciter GitHub de façon déraisonnable. Le cache rend l'opération
        # ponctuelle de toute façon.
        import concurrent.futures
        import threading
        verrou = threading.Lock()
        avancement = {"fait": 0}

        def recuperer(node: Dict[str, Any]) -> Optional[Tuple[Path, bool]]:
            rel = node["path"]
            est_qml = rel.lower().endswith(".qml")
            cible = self.cache_dir / rel
            if not cible.exists():
                cible.parent.mkdir(parents=True, exist_ok=True)
                url = self.RAW.format(
                    repo=self.repo,
                    branch=urllib.parse.quote(self.branch, safe=""),
                    path=urllib.parse.quote(rel))
                try:
                    cible.write_bytes(http_get(url, binary=True,
                                               token=self.token))
                except Exception as exc:                   # noqa: BLE001
                    with verrou:
                        Console.warn(f"Téléchargement échoué : {rel} ({exc})")
                    return None
            with verrou:
                avancement["fait"] += 1
                fait = avancement["fait"]
                if fait % 25 == 0 or fait == total:
                    passe = time.time() - started
                    cadence = fait / passe if passe > 0.1 else 0
                    restant = (total - fait) / cadence if cadence else 0
                    barre = "#" * int(24 * fait / total)
                    Console.raw(f"         [{barre:<24}] {fait:>4}/{total}  "
                                f"{int(passe)} s écoulées, "
                                f"~{int(restant)} s restantes")
            return cible, est_qml

        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
            for resultat in pool.map(recuperer, wanted):
                if resultat is None:
                    continue
                cible, est_qml = resultat
                (out.qml if est_qml else out.svg).append(cible)

        Console.ok(f"Sources en cache dans {self.cache_dir} : {out.summary()}")
        return out

    def _sequentiel_obsolete(self, wanted, out, total, started):   # noqa: D401
        """Ancienne boucle séquentielle, conservée pour référence."""
        for idx, node in enumerate(wanted, start=1):
            rel = node["path"]
            is_qml = rel.lower().endswith(".qml")
            # L'ARBORESCENCE DU DÉPÔT EST PRÉSERVÉE TELLE QUELLE dans le cache.
            # Surtout ne pas aplatir en préfixant les homonymes par leur dossier
            # parent : le nom du fichier devient le nom du style GeoServer et le
            # contenu des balises <Name> / <Title> du SLD. Un préfixe technique
            # comme « qml__ » se propagerait jusque dans la configuration de
            # GeoServer et dans les requêtes WMS. En conservant les sous-dossiers
            # du dépôt, les homonymes cohabitent sans être renommés et
            # Path(...).stem reste exactement le nom d'origine.
            target = self.cache_dir / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            if target.exists():                       # déjà en cache
                (out.qml if is_qml else out.svg).append(target)
                continue
            url = self.RAW.format(
                repo=self.repo,
                branch=urllib.parse.quote(self.branch, safe=""),
                path=urllib.parse.quote(rel),
            )
            try:
                data = http_get(url, binary=True, token=self.token)
                target.write_bytes(data)
                (out.qml if is_qml else out.svg).append(target)
            except Exception as exc:                          # noqa: BLE001
                Console.warn(f"Téléchargement échoué : {rel} ({exc})")
            if idx % 10 == 0 or idx == total:
                elapsed = time.time() - started
                rate = idx / elapsed if elapsed > 0.1 else 0
                remaining = (total - idx) / rate if rate > 0 else 0
                bar = "#" * int(24 * idx / total)
                Console.raw(f"         [{bar:<24}] {idx:>4}/{total}  "
                            f"{int(elapsed)} s écoulées, "
                            f"~{int(remaining)} s restantes")

        Console.ok(f"Sources en cache dans {self.cache_dir} : {out.summary()}")
        return out

    # ------------------------------------------------------------ hors ligne
    @staticmethod
    def fetch_local(folder: Path) -> SourceFiles:
        Console.step(f"Lecture d'un dossier local : {folder}")
        if not folder.is_dir():
            raise RuntimeError(f"Dossier introuvable : {folder}")
        out = SourceFiles(root=folder)
        ecartes = 0
        for path in sorted(folder.rglob("*")):
            if not path.is_file():
                continue
            # Même filtrage qu'en mode GitHub : le dépôt CNIG conserve sous
            # « Archives/ » des styles OBSOLÈTES qui portent parfois le même
            # nom que les styles courants. Les convertir reviendrait à livrer
            # côte à côte deux versions d'une même symbologie — et, pire, à
            # voir apparaître des suffixes « _2 » pour départager les doublons.
            rel = path.relative_to(folder).as_posix()
            if rel.startswith(EXCLUDED_PREFIXES):
                if path.suffix.lower() == ".qml":
                    ecartes += 1
                continue
            if path.suffix.lower() == ".qml":
                out.qml.append(path)
            elif path.suffix.lower() == ".svg":
                out.svg.append(path)
        if not out.qml:
            raise RuntimeError(f"Aucun fichier .qml sous {folder}")
        Console.ok(f"Sources locales : {out.summary()}")
        if ecartes:
            Console.info(f"   {ecartes} style(s) obsolète(s) écarté(s) "
                         f"({', '.join(EXCLUDED_PREFIXES)}).")
        return out


# (SECTION 3 — PARSEUR QML : `QmlDocument` a été déplacée dans
#  styleforge_core.writers.sld_posttraitement, importée en tête de ce
#  fichier, pour être partagée avec le plugin QGIS. Voir la docstring de ce
#  module pour le détail.)


# ==============================================================================
#  PHASE 1 — ANALYSE DE COMPLEXITÉ ET STYLE ÉTALON
# ==============================================================================

@dataclass
class ComplexityReport:
    """Résultat de l'analyse d'un fichier QML."""
    path: Path
    score: int = 0
    n_rules: int = 0
    n_symbol_layers: int = 0
    geometry: str = ""
    renderer: str = ""
    flags: Set[str] = field(default_factory=set)
    details: Counter = field(default_factory=Counter)
    error: Optional[str] = None

    @property
    def name(self) -> str:
        return self.path.name

    def flag_list(self) -> str:
        return ", ".join(sorted(self.flags)) or "(aucun cas particulier)"


class ComplexityAnalyzer:
    """
    PHASE 1 — calcule un score de complexité cartographique par fichier QML.

    Le score n'est pas une note esthétique : il mesure la DIFFICULTÉ DE PORTAGE
    vers SLD/GeoServer. Un fichier à score élevé concentre les constructions que
    bridge-style dégrade (hachures, motifs SVG, lignes à symboles, décalages) :
    c'est donc le meilleur candidat comme « Style Étalon » de recette.
    """

    def analyze_file(self, path: Path) -> ComplexityReport:
        rep = ComplexityReport(path=path)
        try:
            doc = QmlDocument(path)
        except Exception as exc:                              # noqa: BLE001
            rep.error = f"QML illisible : {exc}"
            return rep

        rep.renderer = doc.renderer_type or "(aucun renderer-v2)"
        rep.geometry = doc.geometry_type()
        rules = doc.rules()
        rep.n_rules = len(rules)

        score = 0
        # --- volumétrie -------------------------------------------------
        score += rep.n_rules * COMPLEXITY_WEIGHTS["rules"]
        if rep.n_rules > 1:
            rep.flags.add("multi_rule")

        layers = doc.all_symbol_layers()
        rep.n_symbol_layers = len(layers)
        if rep.n_symbol_layers > 1:
            rep.flags.add("multi_symbollayer")

        # --- classes de symboles ---------------------------------------
        for layer in layers:
            cls = layer.get("class") or ""
            props = QmlDocument.layer_props(layer)

            if cls in COMPLEXITY_WEIGHTS:
                score += COMPLEXITY_WEIGHTS[cls]
                rep.flags.add(cls)
                rep.details[cls] += 1
            elif cls.startswith("GeometryGenerator"):
                score += COMPLEXITY_WEIGHTS["GeometryGenerator"]
                rep.flags.add("GeometryGenerator")
                rep.details["GeometryGenerator"] += 1

            # décalage de hachure : cas particulièrement pénible en SLD
            if cls == "LinePatternFill" and _nonzero(props.get("offset")):
                score += COMPLEXITY_WEIGHTS["LinePatternFill.offset"]
                rep.flags.add("offset")
                rep.details["hachure_decalee"] += 1

            # décalages génériques
            for key in ("offset", "offset_x", "offset_y", "offset_along_line"):
                if _nonzero(props.get(key)):
                    score += COMPLEXITY_WEIGHTS["offset"]
                    rep.flags.add("offset")
                    rep.details["offset"] += 1
                    break

            # tirets personnalisés
            if props.get("use_custom_dash") in ("1", "true") or props.get("customdash"):
                score += COMPLEXITY_WEIGHTS["customdash"]
                rep.flags.add("customdash")
                rep.details["customdash"] += 1

            # brosse Qt non pleine sur un SimpleFill (hachure « native » Qt)
            if cls == "SimpleFill":
                style = (props.get("style") or "solid").lower()
                if style not in ("solid", "no"):
                    score += COMPLEXITY_WEIGHTS["LinePatternFill"] // 2
                    rep.flags.add("LinePatternFill")
                    rep.details[f"brosse_qt_{style}"] += 1

            # propriétés pilotées par des expressions
            ddp = layer.find("data_defined_properties")
            if ddp is not None and _has_active_dd(ddp):
                score += COMPLEXITY_WEIGHTS["data_defined"]
                rep.flags.add("data_defined")
                rep.details["data_defined"] += 1

        # --- étiquetage --------------------------------------------------
        lab = doc.labeling
        if lab is not None and len(list(lab.iter("settings"))):
            score += COMPLEXITY_WEIGHTS["labeling"]
            rep.flags.add("labeling")
            if (lab.get("type") or "") == "rule-based":
                score += COMPLEXITY_WEIGHTS["labeling_rules"]
                rep.flags.add("labeling_rules")
            if lab.find(".//callout") is not None:
                score += COMPLEXITY_WEIGHTS["labeling_callout"]
                rep.flags.add("labeling_callout")
            rep.details["etiquetage"] += len(list(lab.iter("settings")))

        # --- rendu par échelle, fusion, niveaux de symboles --------------
        if any(r.get("min_scale") or r.get("max_scale") for r in rules) \
           or doc.root.find(".//scaledependentvisibility") is not None \
           or doc.root.get("hasScaleBasedVisibilityFlag") == "1":
            score += COMPLEXITY_WEIGHTS["scale_dependent"]
            rep.flags.add("scale_dependent")

        for sym in doc.root.iter("symbol"):
            if (sym.get("alpha") or "1") not in ("1", "1.0"):
                rep.details["alpha_symbole"] += 1
        if doc.root.find(".//blendMode") is not None or \
           any((e.get("v") or "") not in ("", "0") for e in doc.root.iter("blendMode")):
            score += COMPLEXITY_WEIGHTS["blend_mode"]
            rep.flags.add("blend_mode")

        r = doc.renderer
        if r is not None and (r.get("symbollevels") or "0") == "1":
            score += COMPLEXITY_WEIGHTS["symbol_levels"]
            rep.flags.add("symbol_levels")

        rep.score = score
        return rep

    # ------------------------------------------------------------------ lot
    def analyze_all(self, files: Sequence[Path]) -> List[ComplexityReport]:
        reports: List[ComplexityReport] = []
        for path in files:
            reports.append(self.analyze_file(path))
        reports.sort(key=lambda r: (-r.score, r.name))
        return reports

    # ------------------------------------------- combinaison couvrante min.
    @staticmethod
    def minimal_cover(reports: Sequence[ComplexityReport],
                      max_size: int = 3) -> Tuple[List[ComplexityReport], Set[str], Set[str]]:
        """
        Algorithme glouton de couverture d'ensemble : sélectionne au plus
        `max_size` styles qui, réunis, contiennent le maximum de cas de figure
        distincts du corpus.

        Retourne (styles_choisis, cas_couverts, cas_non_couverts).
        """
        universe: Set[str] = set()
        for rep in reports:
            universe |= (rep.flags & set(FEATURE_FLAGS))

        chosen: List[ComplexityReport] = []
        covered: Set[str] = set()
        pool = [r for r in reports if not r.error]

        while len(chosen) < max_size and covered != universe:
            # meilleur apport marginal ; en cas d'égalité, le score le plus élevé
            best = max(
                pool,
                key=lambda r: (len((r.flags & universe) - covered), r.score),
                default=None,
            )
            if best is None or not ((best.flags & universe) - covered):
                break
            chosen.append(best)
            covered |= (best.flags & universe)
            pool.remove(best)

        return chosen, covered, (universe - covered)

    # ------------------------------------------------------------- affichage
    @classmethod
    def print_report(cls, reports: Sequence[ComplexityReport], top: int = 12) -> None:
        ok = [r for r in reports if not r.error]
        ko = [r for r in reports if r.error]

        Console.rule("PHASE 1 — STYLE ETALON (BENCHMARK)", "#")
        if not ok:
            Console.err("Aucun QML analysable.")
            return

        etalon = ok[0]
        print()
        print("  +" + "-" * 72 + "+")
        print("  |  STYLE ETALON RETENU — cible prioritaire des tests GeoServer".ljust(75) + "|")
        print("  +" + "-" * 72 + "+")
        print(f"  |  Fichier   : {etalon.name}".ljust(75) + "|")
        print(f"  |  Score     : {etalon.score}".ljust(75) + "|")
        print(f"  |  Rendu     : {etalon.renderer}  ({etalon.geometry})".ljust(75) + "|")
        print(f"  |  Règles    : {etalon.n_rules}   "
              f"Couches de symboles : {etalon.n_symbol_layers}".ljust(75) + "|")
        print("  +" + "-" * 72 + "+")
        for line in _wrap(f"Cas de figure : {etalon.flag_list()}", 68):
            print(f"  |  {line}".ljust(75) + "|")
        print("  +" + "-" * 72 + "+")

        # --- combinaison couvrante minimale ------------------------------
        chosen, covered, missing = cls.minimal_cover(reports, max_size=3)
        print()
        Console.rule("COMBINAISON COUVRANTE MINIMALE (2-3 styles)", "-")
        for i, rep in enumerate(chosen, 1):
            print(f"   {i}. {rep.name}  (score {rep.score})")
            for line in _wrap("apporte : " + ", ".join(sorted(rep.flags & set(FEATURE_FLAGS))), 66):
                print(f"        {line}")
        print(f"\n   -> {len(covered)} cas de figure couverts sur "
              f"{len(covered) + len(missing)} présents dans le corpus.")
        if missing:
            for line in _wrap("NON couverts : " + ", ".join(sorted(missing)), 70):
                print(f"      {line}")

        # --- classement --------------------------------------------------
        print()
        Console.rule(f"CLASSEMENT DES {min(top, len(ok))} STYLES LES PLUS COMPLEXES", "-")
        print(f"   {'#':>3}  {'SCORE':>6}  {'RÈG':>4}  {'CCH':>4}  {'GÉOM':<10}  FICHIER")
        for i, rep in enumerate(ok[:top], 1):
            print(f"   {i:>3}  {rep.score:>6}  {rep.n_rules:>4}  "
                  f"{rep.n_symbol_layers:>4}  {rep.geometry:<10}  {rep.name}")

        # --- panorama du corpus ------------------------------------------
        print()
        Console.rule("PANORAMA DU CORPUS", "-")
        agg: Counter = Counter()
        for rep in ok:
            for flag in rep.flags:
                agg[flag] += 1
        for flag, count in agg.most_common():
            pct = 100.0 * count / len(ok)
            bar = "#" * int(pct / 4)
            print(f"   {flag:<22} {count:>4} fichiers ({pct:5.1f}%)  {bar}")

        if ko:
            print()
            Console.warn(f"{len(ko)} fichier(s) illisible(s) :")
            for rep in ko[:10]:
                print(f"      - {rep.name} : {rep.error}")
        print()


def _wrap(text: str, width: int) -> List[str]:
    """Découpage simple pour l'affichage encadré."""
    import textwrap
    return textwrap.wrap(text, width) or [""]


def _nonzero(value: Optional[str]) -> bool:
    """True si la propriété QGIS représente un décalage non nul."""
    if not value:
        return False
    try:
        return any(abs(float(part)) > 1e-9 for part in str(value).split(","))
    except ValueError:
        return False


def _has_active_dd(ddp: ET.Element) -> bool:
    """Détecte une propriété pilotée par expression réellement active."""
    for opt in ddp.iter("Option"):
        if opt.get("name") == "active" and (opt.get("value") or "").lower() == "true":
            return True
    for prop in ddp.iter("prop"):
        if prop.get("k") == "active" and (prop.get("v") or "").lower() == "true":
            return True
    return False


# (SECTION 4 — INDEX D'INDICES (« hints ») EXTRAIT DU QML : `HatchHint`,
#  `RuleHints` et `HintExtractor` ont été déplacées dans styleforge_core.
#  writers.sld_posttraitement, importées en tête de ce fichier, pour être
#  partagées avec le plugin QGIS.)


# ==============================================================================
#  PHASE 2 — CONVERSION QML -> SLD (deux backends)
# ==============================================================================

def _valeur_python(valeur: Any) -> Any:
    """
    Ramène une valeur Qt à son équivalent Python.

    PyQt enveloppe les attributs lus dans une couche vectorielle : un champ
    texte devient un QVariant, une couleur un QColor. Ces objets se comportent
    correctement tant qu'on se contente de les mettre en forme, d'où le fait
    qu'ils traversent la génération SLD sans se signaler. Mais ils ne sont ni
    sérialisables en JSON ni copiables par copy.deepcopy — ce dernier échoue
    sur « cannot pickle 'QVariant' object ». On les déballe donc au plus tôt.
    """
    if valeur is None or isinstance(valeur, (str, int, float, bool)):
        return valeur
    # QVariant nul : QVariant().value() retourne None, mais isNull() est le
    # test explicite et évite de dépendre du type interne.
    controle = getattr(valeur, "isNull", None)
    if callable(controle):
        try:
            if controle():
                return None
        except Exception:                                  # noqa: BLE001
            pass
    # QVariant, QJsonValue… exposent value() ; QColor expose name().
    for accesseur in ("value", "name", "toPyObject"):
        methode = getattr(valeur, accesseur, None)
        if callable(methode):
            try:
                obtenu = methode()
            except Exception:                              # noqa: BLE001
                continue
            if obtenu is not valeur:
                return _valeur_python(obtenu)
    return str(valeur)


def purger_types_qt(noeud: Any) -> int:
    """
    Remplace SUR PLACE toute valeur Qt du dictionnaire GeoStyler par son
    équivalent Python. Retourne le nombre de valeurs converties.

    La conversion est faite en place plutôt que par recopie : le pivot est
    partagé avec l'appelant, qui le réutilise pour l'export MBStyle.
    """
    compteur = 0
    if isinstance(noeud, dict):
        for cle in list(noeud):
            enfant = noeud[cle]
            if isinstance(enfant, (dict, list)):
                compteur += purger_types_qt(enfant)
            else:
                remplacant = _valeur_python(enfant)
                if remplacant is not enfant:
                    noeud[cle] = remplacant
                    compteur += 1
    elif isinstance(noeud, list):
        for indice, enfant in enumerate(noeud):
            if isinstance(enfant, (dict, list)):
                compteur += purger_types_qt(enfant)
            else:
                remplacant = _valeur_python(enfant)
                if remplacant is not enfant:
                    noeud[indice] = remplacant
                    compteur += 1
    return compteur


def inject_missing_filters(geostyler: Dict[str, Any], doc: "QmlDocument",
                           warnings: List[str]) -> int:
    """
    Complète les filtres de règle absents du pivot, à partir du QML source.

    bridgestyle.qgis abandonne les expressions qu'il ne sait pas traduire
    (`string_to_array`, `lower`, comparaisons imbriquées…) : la règle part alors
    SANS filtre et s'applique à tous les objets. Sur ASSIETTE_SUP_S, ce sont 77
    symbologies de servitudes superposées sur le même polygone.

    L'appariement se fait d'abord PAR POSITION — bridgestyle conserve l'ordre
    des règles — mais uniquement lorsque le nom concorde aussi : si le
    producteur a écarté une règle en cours de route, les rangs se décalent et
    la vérification de nom le détecte. À défaut, on retombe sur une recherche
    par nom, abandonnée si plusieurs règles homonymes portent des filtres
    différents. Mieux vaut un filtre manquant, visible dans le rapport, qu'un
    filtre faux, invisible à la lecture.
    """
    regles_qml = doc.rules()
    par_nom: Dict[str, List[str]] = defaultdict(list)
    for regle in regles_qml:
        expression = regle.get("filter")
        if expression:
            par_nom[str(regle.get("name") or "")].append(expression)

    if not par_nom:
        return 0

    rattrapes = 0
    for rang, regle in enumerate(geostyler.get("rules") or []):
        if not isinstance(regle, dict) or regle.get("filter") is not None:
            continue
        nom = str(regle.get("name") or "")

        source: Optional[str] = None
        if rang < len(regles_qml) \
                and str(regles_qml[rang].get("name") or "") == nom:
            source = regles_qml[rang].get("filter")
        if not source:
            candidats = par_nom.get(nom)
            if candidats and len(set(candidats)) == 1:
                source = candidats[0]
        if not source:
            continue

        traduit = StandaloneBackend._filter(source, warnings)
        if traduit not in (None, "ELSE"):
            regle["filter"] = traduit
            rattrapes += 1
    return rattrapes


def normalize_geostyler(geostyler: Dict[str, Any]) -> Counter:
    """
    Passe de normalisation appliquée au dictionnaire GeoStyler AVANT sa
    sérialisation en SLD, quel que soit le backend qui l'a produit.

    C'est le point d'insertion qui permet au backend « qgis » de bénéficier des
    mêmes correctifs que le backend autonome. Trois défauts de bridgestyle
    0.1.9 sont neutralisés ici :

    1. SVG EMBARQUÉS EN BASE64 (points E et H de la SECTION 7)
       `qgis/togeostyler.py::_markGraphic()` fait
       `name = os.path.basename(sl.path())`. Pour un pictogramme embarqué,
       `sl.path()` vaut « base64:PD94bWwg... ». L'alphabet base64 contenant le
       caractère « / », basename() renvoie un fragment arbitraire de la chaîne
       encodée, qui atterrit dans <WellKnownName>. GeoServer n'affiche rien.
       On décode, on matérialise le fichier et on référence son nom.

    2. DASHARRAY DÉCIMAL (point G)
       `sld/fromgeostyler.py::_lineSymbolizer()` applique `int(v)` sur chaque
       valeur quand cap != "butt" ; « 22.6786 » lève ValueError et fait échouer
       tout le style. On arrondit au pixel, visuellement neutre.

    3. ESPACEMENT DES MOTIFS PERDU (point B)
       `qgis/togeostyler.py::_simpleFillSymbolizer()` écrit
       « graphicFillDistanceX/Y » alors que `sld/fromgeostyler.py` lit
       « graphicFillMarginX/Y » : la valeur n'arrive jamais. On renomme.

    Retourne un compteur des corrections appliquées.
    """
    stats: Counter = Counter()

    def fix_dash(value: Any) -> Any:
        if not isinstance(value, str) or not value.strip():
            return value
        try:
            tokens = [max(1, int(round(float(v)))) for v in value.split()]
        except ValueError:
            return value
        fixed = " ".join(str(t) for t in tokens)
        if fixed != value:
            stats["dasharray_arrondis"] += 1
        return fixed

    def walk(symbolizer: Dict[str, Any]) -> None:
        # --- 1. pictogrammes base64 -----------------------------------
        for key in ("wellKnownName", "image"):
            value = symbolizer.get(key)
            if isinstance(value, str) and "base64:" in value:
                # Le préfixe peut avoir été tronqué par un basename() malheureux
                raw = value[value.index("base64:"):]
                name = register_svg_reference(raw, "cnig_picto")
                if name:
                    symbolizer[key] = name
                    stats["svg_base64_extraits"] += 1

        # --- 2. tirets ------------------------------------------------
        for key in ("dasharray", "outlineDasharray"):
            if key in symbolizer:
                symbolizer[key] = fix_dash(symbolizer[key])

        # --- 3. clés d'espacement incohérentes -------------------------
        for src, dst in (("graphicFillDistanceX", "graphicFillMarginX"),
                         ("graphicFillDistanceY", "graphicFillMarginY")):
            if src in symbolizer and dst not in symbolizer:
                symbolizer[dst] = symbolizer.pop(src)
                stats["cles_espacement_corrigees"] += 1

        # --- 4. bruit inutile en SLD ----------------------------------
        symbolizer.pop("spriteName", None)

        # --- récursion dans les sous-symboles --------------------------
        for container in ("graphicFill", "graphicStroke"):
            for sub in symbolizer.get(container) or []:
                if isinstance(sub, dict):
                    walk(sub)

    for rule in geostyler.get("rules", []):
        for symbolizer in rule.get("symbolizers", []):
            if isinstance(symbolizer, dict):
                walk(symbolizer)
    return stats


@dataclass
class ConversionResult:
    source: Path
    target: Optional[Path] = None
    sld: Optional[str] = None
    #: Dictionnaire GeoStyler intermédiaire, conservé pour la PHASE 5 (MBStyle).
    #: C'est tout l'intérêt du format pivot : une seule lecture du QML alimente
    #: autant de formats cibles que nécessaire.
    geostyler: Optional[Dict[str, Any]] = None
    #: Pivot styleforge_core (styleforge_core.pivot.Style), peuplé uniquement
    #: par StyleforgeBackend — c'est SON format pivot, distinct du dict
    #: GeoStyler de bridgestyle ci-dessus (schéma différent, jamais réutilisé
    #: comme alias) : nécessaire ici pour que la PHASE 5 (export MBStyle)
    #: puisse appeler styleforge_core.writers.mbstyle.ecrire_mbstyle() sans
    #: relire le QML une seconde fois.
    pivot_style: Optional[Any] = None
    mbstyle: Optional[Path] = None
    icons: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    error: Optional[str] = None
    backend: str = ""

    @property
    def ok(self) -> bool:
        return self.error is None and bool(self.sld)


class BaseBackend:
    name = "base"

    def available(self) -> bool:                               # pragma: no cover
        raise NotImplementedError

    def convert(self, qml: Path) -> ConversionResult:          # pragma: no cover
        raise NotImplementedError


# ------------------------------------------------------------------------------
#  [A] BACKEND QGIS — pleine fidélité (bridgestyle.qgis)
# ------------------------------------------------------------------------------
class QgisBackend(BaseBackend):
    """
    Utilise la vraie chaîne bridge-style : QgsVectorLayer -> GeoStyler -> SLD.

    Doit impérativement tourner dans l'interpréteur Python de QGIS.
    Sous Windows :
        "C:\\Program Files\\QGIS 3.34\\bin\\python-qgis.bat" script.py --all
    Sous Linux/conda :
        conda activate qgis && python script.py --all
    """

    name = "qgis"

    def __init__(self, sprites_bridgestyle: bool = False) -> None:
        #: False = on neutralise le rendu de vignettes de bridgestyle.
        self.sprites_bridgestyle = sprites_bridgestyle
        self._app = None          # QgsApplication créée PAR NOUS (mode headless)
        self._borrowed = False    # True si l'on réutilise le QGIS de l'utilisateur
        self._ok = False

    def available(self) -> bool:
        if self._ok:
            return True
        if SLD_SHIM_FORCED:
            # bridgestyle.qgis a été remplacé par un module de substitution
            # pour sauver le module SLD : ce backend n'est plus utilisable.
            return False
        try:
            from qgis.core import QgsApplication          # type: ignore  # noqa
            import bridgestyle.qgis                        # type: ignore  # noqa
        except Exception:                                  # noqa: BLE001
            return False
        try:
            from qgis.core import QgsApplication          # type: ignore

            # CAS 1 — le script tourne DANS QGIS (console Python, script de
            # traitement, plugin) : une QgsApplication existe déjà. En créer
            # une seconde plante l'application. On emprunte l'existante et on
            # s'interdit tout initQgis()/exitQgis(), qui fermeraient QGIS.
            if QgsApplication.instance() is not None:
                self._borrowed = True
                self._ok = True
                if self.sprites_bridgestyle is False and self._disable_sprite_rendering():
                    Console.info("Rendu de vignettes de bridgestyle neutralisé "
                                 "(inutilisé ici, et très coûteux).")
                Console.info("QgsApplication existante réutilisée "
                             "(exécution depuis QGIS) — QGIS ne sera pas fermé.")
                return True

            # CAS 2 — interpréteur QGIS lancé en ligne de commande
            # (python-qgis.bat, OSGeo4W Shell) : on initialise nous-mêmes,
            # en mode headless (2e argument = False, pas d'interface).
            prefix = os.environ.get("QGIS_PREFIX_PATH", "")
            if prefix:
                QgsApplication.setPrefixPath(prefix, True)
            self._app = QgsApplication([], False)
            self._app.initQgis()
            self._ok = True
            if self.sprites_bridgestyle is False:
                self._disable_sprite_rendering()
            return True
        except Exception as exc:                           # noqa: BLE001
            Console.warn(f"PyQGIS présent mais non initialisable : {exc}")
            return False

    def shutdown(self) -> None:
        # On ne ferme que ce que l'on a ouvert : appeler exitQgis() sur
        # l'instance empruntée fermerait le QGIS de l'utilisateur.
        if self._app is not None and not self._borrowed:
            try:
                self._app.exitQgis()
            except Exception:                              # noqa: BLE001
                pass

    #: Géométrie factice minimale par type, pour peupler la couche porteuse.
    _SAMPLE_WKT = {
        "Polygon": "POLYGON((0 0, 0 1, 1 1, 1 0, 0 0))",
        "LineString": "LINESTRING(0 0, 1 1)",
        "Point": "POINT(0 0)",
    }

    @classmethod
    def _seed_feature(cls, layer: Any, geometry: str) -> None:
        """
        Ajoute UNE entité factice à la couche mémoire.

        Ce n'est pas un détail : sans entité, bridgestyle échoue sur
            TypeError: 'NoneType' object is not iterable
        Le mécanisme, vérifié sur QGIS 3.40.4 et bridgestyle 0.1.9 :

          * qgis/expressions.py::ExpressionConverter.__init__() ÉCHANTILLONNE
            la première entité de la couche pour en déduire la liste des
            champs. Sur une couche vide, _get_feature() renvoie None, la
            fonction sort par « return » et self.fields conserve sa valeur de
            classe, None.
          * plus tard, _handle_column_ref() fait
                if self.layer is not None:
                    for field in self.fields:
            Le garde-fou teste self.LAYER alors que c'est self.FIELDS qui peut
            valoir None. Toute expression citant un champ — donc tout rendu
            catégorisé ou par règles — provoque l'exception.

        Autrement dit, bridgestyle exige des DONNÉES pour convertir un STYLE.
        Une entité suffit : seuls les NOMS de champs sont lus, jamais les
        valeurs. (Défaut remonté en SECTION 7, point J.)
        """
        from qgis.core import QgsFeature, QgsGeometry       # type: ignore
        try:
            feature = QgsFeature(layer.fields())
            wkt = cls._SAMPLE_WKT.get(geometry)
            if wkt:
                feature.setGeometry(QgsGeometry.fromWkt(wkt))
            layer.dataProvider().addFeatures([feature])
            layer.updateExtents()
        except Exception:                                  # noqa: BLE001
            pass

    @staticmethod
    def _disable_sprite_rendering() -> bool:
        """
        Neutralise la fabrication des vignettes par bridgestyle.

        C'EST LE PRINCIPAL LEVIER DE PERFORMANCE DU BACKEND QGIS.

        qgis/togeostyler.py::_createSprite() est appelé pour CHAQUE marqueur et
        CHAQUE motif de remplissage — lignes 789, 826 et 837 — et rend à chaque
        fois DEUX images :

            img   = newSymbol.asImage(QSize(64, 64))
            img2x = newSymbol.asImage(QSize(128, 128))

        Sur plu_psc_s.qml et ses 438 couches de symboles, cela représente près
        de 900 rendus d'images, dont beaucoup de pictogrammes SVG à décoder
        depuis leur base64. C'est là que part l'essentiel du temps.

        Or ces vignettes ne servent QU'À mapboxgl.convertGroup() et
        toSpriteSheet(), que cette chaîne n'appelle jamais : la feuille de
        sprites MBStyle est construite par la PHASE 5, directement depuis les
        fichiers SVG du dépôt et des motifs dessinés — plus fidèle, et en
        disposition grille. Les noms de vignettes (« spriteName »), eux, sont
        calculés indépendamment et restent donc corrects.

        Effet de bord heureux : _createSprite() laisse img et img2x NON
        DÉFINIES lorsque la couche de symbole n'a ni setSize ni
        toTiledPatternImage, ce qui lève UnboundLocalError. Le substitut
        supprime aussi ce risque.
        """
        try:
            from bridgestyle.qgis import togeostyler        # type: ignore
        except Exception:                                  # noqa: BLE001
            return False
        if getattr(togeostyler, "_cnig_sprites_neutralises", False):
            return True
        togeostyler._cnig_createSprite_origine = togeostyler._createSprite
        togeostyler._createSprite = lambda sl: {"image": None, "image2x": None}
        togeostyler._cnig_sprites_neutralises = True
        return True

    def convert(self, qml: Path) -> ConversionResult:
        from qgis.core import QgsVectorLayer               # type: ignore
        import bridgestyle.qgis                             # type: ignore

        res = ConversionResult(source=qml, backend=self.name)
        doc = QmlDocument(qml)

        # Couche mémoire « porteuse » : le style QML sera appliqué dessus.
        # Les champs sont créés à la volée à partir des attributs référencés
        # par les filtres du QML, sinon `loadNamedStyle` perd les catégories.
        fields = self._fields_referenced(doc)

        # On essaie les types géométriques du plus probable au moins probable :
        # loadNamedStyle refuse un style dont la symbologie ne correspond pas à
        # la géométrie de la couche, et l'entête du QML n'est pas toujours
        # renseignée. Plutôt que d'abandonner sur le premier refus, on tente les
        # autres — le coût est négligeable, une couche mémoire vide.
        layer = None
        refusals: List[str] = []
        for geom in doc.geometry_candidates():
            uri = (f"{geom}?crs=EPSG:2154"
                   + "".join(f"&field={f}:string" for f in fields))
            candidate = QgsVectorLayer(uri, qml.stem, "memory")
            if not candidate.isValid():
                refusals.append(f"{geom} : couche mémoire invalide")
                continue
            self._seed_feature(candidate, geom)

            result = candidate.loadNamedStyle(str(qml))
            message, ok = "", True
            if isinstance(result, bool):
                ok = result
            elif isinstance(result, (tuple, list)):
                for item in result:
                    if isinstance(item, bool):
                        ok = item
                    elif isinstance(item, str):
                        message = item
            if ok:
                layer = candidate
                if geom != doc.geometry_candidates()[0]:
                    res.warnings.append(
                        f"Type géométrique déduit corrigé en « {geom} » "
                        f"après refus de « {doc.geometry_candidates()[0]} ».")
                if message:
                    res.warnings.append(f"loadNamedStyle : {message}")
                break
            refusals.append(f"{geom} : {message or 'refusé sans message'}")

        if layer is None:
            res.error = ("loadNamedStyle a refusé le QML pour tous les types "
                         "géométriques essayés — " + " | ".join(refusals))
            return res

        # On N'APPELLE PAS bridgestyle.qgis.layerStyleAsSld() directement :
        # cette fonction enchaîne togeostyler puis fromgeostyler sans laisser de
        # point d'accès au dictionnaire GeoStyler intermédiaire. Or c'est
        # précisément là qu'il faut intervenir pour neutraliser les défauts
        # connus (SVG base64, dasharray décimal, clés d'espacement). On refait
        # donc l'enchaînement à la main, à l'identique, avec une passe de
        # normalisation au milieu.
        from bridgestyle.qgis import togeostyler                  # type: ignore
        from bridgestyle.sld import fromgeostyler                 # type: ignore
        try:
            geostyler, icons, _sprites, warnings = togeostyler.convert(layer)
        except Exception as exc:                           # noqa: BLE001
            # On consigne l'endroit exact du défaut dans bridgestyle : c'est ce
            # qui permet d'ouvrir une issue utile en amont plutôt que de se
            # contenter d'un message d'erreur sans contexte.
            frames = traceback.extract_tb(exc.__traceback__)
            trace = " <- ".join(
                f"{Path(f.filename).name}:{f.lineno} ({f.name})"
                for f in frames[-3:])
            res.error = (f"bridgestyle.qgis.togeostyler a échoué : "
                         f"{type(exc).__name__}: {exc}")
            res.warnings.append(f"Localisation du défaut : {trace}")
            return res

        # bridgestyle.qgis recopie parfois des valeurs Qt brutes (QVariant,
        # QColor…) dans le pivot. Elles traversent la génération SLD sans
        # broncher, puis font échouer tout ce qui sérialise ou copie le
        # dictionnaire — json.dumps, et surtout le copy.deepcopy de la phase 5
        # (« cannot pickle 'QVariant' object »). On les ramène donc à des types
        # Python simples dès la sortie du producteur.
        converties = purger_types_qt(geostyler)
        if converties:
            res.warnings.append(
                f"normalisation GeoStyler : valeurs Qt converties x{converties}")

        # bridgestyle.qgis ne sait pas traduire les expressions QGIS un peu
        # riches (string_to_array, lower…) : il émet un avertissement et
        # abandonne le filtre, ce qui applique la règle à TOUS les objets. Le
        # traducteur du backend autonome, lui, les couvre : on l'appelle en
        # rattrapage, règle par règle, sur celles restées sans filtre.
        try:
            rattrapes = inject_missing_filters(geostyler, QmlDocument(qml),
                                               res.warnings)
        except Exception as exc:                           # noqa: BLE001
            rattrapes = 0
            res.warnings.append(f"Rattrapage des filtres impossible : {exc}")
        if rattrapes:
            res.warnings.append(
                f"{rattrapes} filtre(s) de règle rattrapé(s) par le "
                f"traducteur d'expressions maison.")

        stats = normalize_geostyler(geostyler)
        for key, value in stats.items():
            res.warnings.append(f"normalisation GeoStyler : {key} x{value}")

        if not geostyler.get("rules"):
            res.error = ("Résultat GeoStyler vide (style composé uniquement "
                         "d'éléments non supportés par bridge-style).")
            res.warnings.extend(warnings or [])
            return res

        try:
            sld, sld_warnings = fromgeostyler.convert(geostyler)
        except Exception as exc:                           # noqa: BLE001
            res.error = f"bridgestyle.sld.fromgeostyler a échoué : {exc}"
            res.warnings.extend(warnings or [])
            return res

        res.sld = sld if isinstance(sld, str) else sld.decode("utf-8")
        res.geostyler = geostyler
        res.icons = [i for i in (icons or {}) if i and i != "no_icon"
                     and not str(i).startswith("base64:")]
        res.warnings.extend(list(warnings or []) + list(sld_warnings or []))
        return res

    @staticmethod
    def _fields_referenced(doc: QmlDocument) -> List[str]:
        """Extrait les noms de champs cités dans les filtres / expressions."""
        names: Set[str] = set()
        r = doc.renderer
        if r is not None:
            if r.findtext("attr"):
                names.add(r.findtext("attr").strip())
            for rule in r.iter("rule"):
                for m in re.finditer(r'"([^"]+)"', rule.get("filter") or ""):
                    names.add(m.group(1))
        lab = doc.labeling
        if lab is not None:
            for st in lab.iter("text-style"):
                if st.get("fieldName"):
                    names.add(st.get("fieldName"))
        return [re.sub(r"\W", "_", n) for n in sorted(names) if n]


# ------------------------------------------------------------------------------
#  [B] BACKEND AUTONOME — QML -> GeoStyler -> bridgestyle.sld
# ------------------------------------------------------------------------------
class StandaloneBackend(BaseBackend):
    """
    Parse le QML directement et fabrique le dictionnaire GeoStyler attendu par
    `bridgestyle.sld.fromgeostyler.convert()`.

    Schéma GeoStyler produit (conforme à ce qu'attend bridgestyle) :
        {"name": ..., "rules": [
            {"name":..., "filter":[...], "scaleDenominator":{"min":..,"max":..},
             "symbolizers":[ {...}, ... ]}
        ]}
    Symbolizers supportés : Fill / Line / Mark / Icon / Text.
    """

    name = "standalone"

    def __init__(self) -> None:
        #: Semis en quinconce rencontrés, signalés en fin de conversion.
        self.quinconces: List[str] = []

    def available(self) -> bool:
        # Le shim neutralise le défaut d'import de bridgestyle 0.1.9
        # (cf. SECTION 0-bis) : sans lui, l'import ci-dessous lève
        # CompatibilityException dès que PyQGIS est absent.
        if install_bridgestyle_sld_shim():
            Console.info("Shim d'import bridgestyle activé "
                         "(module SLD utilisable sans PyQGIS).")
        try:
            import bridgestyle.sld.fromgeostyler           # type: ignore  # noqa
            return True
        except Exception as exc:                           # noqa: BLE001
            Console.warn(f"bridgestyle.sld inutilisable : {exc}")
            return False

    def convert(self, qml: Path) -> ConversionResult:
        from bridgestyle.sld import fromgeostyler          # type: ignore

        res = ConversionResult(source=qml, backend=self.name)
        doc = QmlDocument(qml)
        symbols = doc.symbols()
        warnings: List[str] = []
        self.quinconces = []

        rules_out: List[Dict[str, Any]] = []
        for rule in doc.rules():
            sym = symbols.get(str(rule.get("symbol")))
            symbolizers: List[Dict[str, Any]] = []
            if sym is not None:
                alpha = _safe_float(sym.get("alpha"), 1.0)
                for layer in sym.findall("layer"):
                    if layer.get("enabled") == "0":
                        continue
                    sl = self._symbol_layer(layer, alpha, warnings, qml)
                    if sl:
                        symbolizers.extend(sl)
            if not symbolizers:
                warnings.append(f"Règle '{rule['name']}' sans symbolizer exploitable.")
                continue

            gs_rule: Dict[str, Any] = {
                "name": rule["name"] or qml.stem,
                "symbolizers": symbolizers,
            }
            flt = self._filter(rule.get("filter"), warnings)
            if flt is not None:
                gs_rule["filter"] = flt
            scale = {}
            if rule.get("min_scale") and _safe_float(rule["min_scale"], 0) > 0:
                scale["min"] = int(float(rule["min_scale"]))
            if rule.get("max_scale") and _safe_float(rule["max_scale"], 0) > 0:
                scale["max"] = int(float(rule["max_scale"]))
            if scale:
                gs_rule["scaleDenominator"] = scale
            rules_out.append(gs_rule)

        # --- étiquetage : une règle supplémentaire par jeu de paramètres ---
        for text_sym, label_name in self._labels(doc, warnings):
            rules_out.append({"name": f"{qml.stem}_label_{label_name}",
                              "symbolizers": [text_sym]})

        if not rules_out:
            res.error = "Aucune règle convertible (QML vide ou 100% non supporté)."
            res.warnings = warnings
            return res

        geostyler = {"name": safe_stem(qml.stem), "rules": rules_out}
        normalize_geostyler(geostyler)      # ceinture et bretelles
        try:
            sld, sld_warnings = fromgeostyler.convert(geostyler)
        except Exception as exc:                           # noqa: BLE001
            res.error = f"bridgestyle.sld.fromgeostyler a échoué : {exc}"
            res.warnings = warnings
            return res

        if self.quinconces:
            warnings.append(
                f"{len(self.quinconces)} semis de points en quinconce "
                f"(displacement non nul) : le décalage d'une rangée sur deux "
                f"n'a pas d'équivalent en SLD 1.0, le motif sera rendu en "
                f"grille régulière. Détail : "
                + " ; ".join(self.quinconces[:3]))

        res.sld = sld if isinstance(sld, str) else sld.decode("utf-8")
        res.geostyler = geostyler
        res.warnings = warnings + list(sld_warnings or [])
        return res

    # -------------------------------------------------- couches de symboles
    def _symbol_layer(self, layer: ET.Element, alpha: float,
                      warnings: List[str], qml: Path) -> List[Dict[str, Any]]:
        cls = layer.get("class") or ""
        p = QmlDocument.layer_props(layer)
        handler = {
            "SimpleFill": self._simple_fill,
            "SimpleLine": self._simple_line,
            "SimpleMarker": self._simple_marker,
            "SvgMarker": self._svg_marker,
            "FilledMarker": self._simple_marker,
            "EllipseMarker": self._simple_marker,   # approché par un cercle
            "LinePatternFill": self._line_pattern_fill,
            "SVGFill": self._svg_fill,
            "PointPatternFill": self._point_pattern_fill,
            "RandomMarkerFill": self._point_pattern_fill,
            "CentroidFill": self._centroid_fill,
            "MarkerLine": self._marker_line,
        }.get(cls)

        if handler is None:
            warnings.append(
                f"[{qml.name}] Classe de symbole non supportée par le backend "
                f"autonome : '{cls}' -> utilisez --backend qgis pour ce style."
            )
            return []
        try:
            out = handler(layer, p, alpha)
        except Exception as exc:                           # noqa: BLE001
            warnings.append(f"[{qml.name}] Échec sur '{cls}' : {exc}")
            return []
        return [o for o in (out or []) if o]

    # ---- surfaces ------------------------------------------------------
    def _simple_fill(self, layer, p, alpha) -> List[Dict[str, Any]]:
        sym: Dict[str, Any] = {"kind": "Fill", "opacity": alpha}
        style = (p.get("style") or "solid").lower()
        color, fop = qgis_color_to_hex(p.get("color"))
        if style == "solid" and color:
            sym["color"] = color
            sym["fillOpacity"] = fop
        elif style not in ("no", "solid"):
            # brosse Qt -> GraphicFill avec une marque shape://
            wkn = QT_BRUSH_TO_WKN.get(style, "shape://slash")
            sym["graphicFill"] = [{
                "kind": "Mark", "wellKnownName": wkn,
                "color": color or "#000000", "strokeColor": color or "#000000",
                "strokeWidth": 1, "size": 10,
                "fillOpacity": 0, "strokeOpacity": fop,
            }]
            sym["graphicFillMargin"] = [0, 0, 0, 0]
        self._outline(sym, p, alpha)
        return [sym]

    def _line_pattern_fill(self, layer, p, alpha) -> List[Dict[str, Any]]:
        """Hachures : le cas décisif pour le PLU."""
        hint = HintExtractor._hatch_from_linepattern(layer, p)
        wkn, residual = hatch_wkn_for_angle(hint.angle)
        mark: Dict[str, Any] = {
            "kind": "Mark", "wellKnownName": wkn,
            "color": hint.color, "strokeColor": hint.color,
            "strokeWidth": hint.width_px, "strokeOpacity": hint.opacity,
            "fillOpacity": 0,
            "size": max(1.0, hint.distance_px),
        }
        if abs(residual) > 0.5:
            mark["rotate"] = residual
        if hint.dasharray:
            mark["outlineDasharray"] = hint.dasharray
        sym: Dict[str, Any] = {
            "kind": "Fill", "opacity": alpha,
            "graphicFill": [mark],
            "graphicFillMargin": [0, 0, 0, 0],
        }
        self._outline(sym, p, alpha)
        return [sym]

    def _svg_fill(self, layer, p, alpha) -> List[Dict[str, Any]]:
        svg = register_svg_reference(p.get("svgFile"), "cnig_motif")
        if not svg:
            return []
        size = qgis_size_to_px(p.get("width"), p.get("width_unit")) or 16.0
        sym: Dict[str, Any] = {
            "kind": "Fill", "opacity": alpha,
            "graphicFill": [_svg_mark(svg, size, _safe_float(p.get("angle"), 0.0))],
            "graphicFillMargin": [0, 0, 0, 0],
        }
        self._outline(sym, p, alpha)
        return [sym]

    def _point_pattern_fill(self, layer, p, alpha) -> List[Dict[str, Any]]:
        sub = layer.find("symbol")
        marks: List[Dict[str, Any]] = []
        if sub is not None:
            for sublayer in sub.findall("layer"):
                marks.extend(self._symbol_layer(sublayer, 1.0, [], Path("sub")))
        if not marks:
            return []

        # SEMIS EN QUINCONCE — ne pas confondre deux propriétés distinctes :
        #
        #   offset_x / offset_y        décalent le motif ENTIER. Sur une trame
        #                              qui se répète à l'infini, un décalage
        #                              global ne change rien à l'aspect : il
        #                              translate la trame, c'est tout. Un
        #                              « 50 % » très répandu dans le corpus CNIG
        #                              est donc SANS CONSÉQUENCE visuelle.
        #
        #   displacement_x / _y        décalent UNE RANGÉE SUR DEUX. C'est le
        #                              vrai quinconce, et lui n'a pas
        #                              d'équivalent en SLD 1.0 : un GraphicFill
        #                              ne connaît qu'une grille régulière.
        #
        # Seul le second mérite un avertissement. Confondre les deux revient à
        # alarmer sur des dizaines de motifs parfaitement rendus.
        if _safe_float(p.get("displacement_x"), 0.0) or \
                _safe_float(p.get("displacement_y"), 0.0):
            self.quinconces.append(
                f"displacement_x={p.get('displacement_x')} "
                f"displacement_y={p.get('displacement_y')} "
                f"{p.get('displacement_x_unit')}")
        dx = qgis_size_to_px(p.get("distance_x"), p.get("distance_x_unit")) or 10.0
        dy = qgis_size_to_px(p.get("distance_y"), p.get("distance_y_unit")) or 10.0
        return [{
            "kind": "Fill", "opacity": alpha,
            "graphicFill": marks[:1],
            # GeoServer attend « top right bottom left » en pixels.
            "graphicFillMargin": [dy / 2.0, dx / 2.0, dy / 2.0, dx / 2.0],
        }]

    def _centroid_fill(self, layer, p, alpha) -> List[Dict[str, Any]]:
        sub = layer.find("symbol")
        out: List[Dict[str, Any]] = []
        if sub is not None:
            for sublayer in sub.findall("layer"):
                out.extend(self._symbol_layer(sublayer, alpha, [], Path("sub")))
        return out

    @staticmethod
    def _outline(sym: Dict[str, Any], p: Dict[str, str], alpha: float) -> None:
        """
        Contour commun à tous les remplissages.

        NE PAS pré-multiplier les opacités par `alpha` : sld/fromgeostyler.py
        applique lui-même `fillOpacity * opacity` et `outlineOpacity * opacity`
        (cf. _fillSymbolizer). Une pré-multiplication donnerait alpha au carré
        et des contours anormalement translucides.
        """
        if (p.get("outline_style") or "solid") == "no":
            return
        color, op = qgis_color_to_hex(p.get("outline_color") or p.get("border_color"))
        if not color:
            return
        sym["outlineColor"] = color
        sym["outlineOpacity"] = op
        sym["outlineWidth"] = qgis_size_to_px(
            p.get("outline_width") or p.get("border_width"),
            p.get("outline_width_unit")) or 1.0
        dash = _dash_from_props(p, "outline")
        if dash:
            sym["outlineDasharray"] = dash

    # ---- lignes --------------------------------------------------------
    def _simple_line(self, layer, p, alpha) -> List[Dict[str, Any]]:
        if (p.get("line_style") or "solid") == "no":
            return []
        color, op = qgis_color_to_hex(p.get("line_color"))
        sym: Dict[str, Any] = {
            "kind": "Line",
            "color": color or "#000000",
            "opacity": op * alpha,
            "width": qgis_size_to_px(p.get("line_width"), p.get("line_width_unit")) or 1.0,
            "cap": {"square": "square", "flat": "butt",
                    "round": "round"}.get(p.get("capstyle", "square"), "butt"),
            "join": {"bevel": "bevel", "miter": "mitre",
                     "round": "round"}.get(p.get("joinstyle", "bevel"), "mitre"),
        }
        dash = _dash_from_props(p, "line")
        if dash:
            sym["dasharray"] = dash
        off = qgis_size_to_px(p.get("offset"), p.get("offset_unit"))
        if off:
            sym["perpendicularOffset"] = off
        return [sym]

    def _marker_line(self, layer, p, alpha) -> List[Dict[str, Any]]:
        """Ligne à symboles répétés -> Stroke/GraphicStroke."""
        sub = layer.find("symbol")
        marks: List[Dict[str, Any]] = []
        if sub is not None:
            for sublayer in sub.findall("layer"):
                marks.extend(self._symbol_layer(sublayer, 1.0, [], Path("sub")))
        if not marks:
            return []
        interval = qgis_size_to_px(p.get("interval"), p.get("interval_unit")) or 10.0
        sym: Dict[str, Any] = {
            "kind": "Line",
            "graphicStroke": marks,
            "graphicStrokeInterval": interval,
            "graphicStrokeOffset": qgis_size_to_px(p.get("offset_along_line"),
                                                   p.get("offset_along_line_unit")) or 0,
            "width": marks[0].get("size", 4),
            "opacity": alpha,
        }
        off = qgis_size_to_px(p.get("offset"), p.get("offset_unit"))
        if off:
            sym["perpendicularOffset"] = off
        return [sym]

    # ---- ponctuels -----------------------------------------------------
    def _simple_marker(self, layer, p, alpha) -> List[Dict[str, Any]]:
        shape = (p.get("name") or "circle").lower()
        wkn = {
            "circle": "circle", "square": "square", "rectangle": "square",
            "triangle": "triangle", "equilateral_triangle": "triangle",
            "star": "star", "regular_star": "star",
            "diamond": "square", "pentagon": "circle", "hexagon": "circle",
            "cross": "shape://plus", "cross2": "shape://times",
            "cross_fill": "shape://plus", "line": "shape://vertline",
            "arrow": "shape://oarrow", "arrowhead": "shape://oarrow",
            "filled_arrowhead": "shape://coarrow",
        }.get(shape, "circle")
        color, fop = qgis_color_to_hex(p.get("color"))
        scolor, sop = qgis_color_to_hex(p.get("outline_color"))
        sym: Dict[str, Any] = {
            "kind": "Mark", "wellKnownName": wkn,
            "color": color or "#000000", "fillOpacity": fop,
            "strokeColor": scolor or "#000000", "strokeOpacity": sop,
            "strokeWidth": qgis_size_to_px(p.get("outline_width"),
                                           p.get("outline_width_unit")) or 0.0,
            "size": qgis_size_to_px(p.get("size"), p.get("size_unit")) or 8.0,
            "opacity": alpha,
        }
        if _safe_float(p.get("angle"), 0.0):
            sym["rotate"] = _safe_float(p.get("angle"), 0.0)
        ox = qgis_size_to_px((p.get("offset") or "0,0").split(",")[0], p.get("offset_unit"))
        oy = qgis_size_to_px((p.get("offset") or "0,0").split(",")[-1], p.get("offset_unit"))
        if ox or oy:
            sym["offset"] = [ox or 0, -(oy or 0)]   # l'axe Y est inversé en SLD
        return [sym]

    def _svg_marker(self, layer, p, alpha) -> List[Dict[str, Any]]:
        svg = register_svg_reference(p.get("name"), "cnig_picto")
        if not svg:
            return []
        sym = _svg_mark(svg,
                        qgis_size_to_px(p.get("size"), p.get("size_unit")) or 12.0,
                        _safe_float(p.get("angle"), 0.0))
        sym["opacity"] = alpha
        ox = qgis_size_to_px((p.get("offset") or "0,0").split(",")[0], p.get("offset_unit"))
        oy = qgis_size_to_px((p.get("offset") or "0,0").split(",")[-1], p.get("offset_unit"))
        if ox or oy:
            sym["offset"] = [ox or 0, -(oy or 0)]
        return [sym]

    # ---- étiquetage ----------------------------------------------------
    @staticmethod
    def _labels(doc: QmlDocument, warnings: List[str]) -> List[Tuple[Dict[str, Any], str]]:
        lab = doc.labeling
        out: List[Tuple[Dict[str, Any], str]] = []
        if lab is None:
            return out
        for idx, settings in enumerate(lab.iter("settings")):
            style = settings.find("text-style")
            if style is None:
                continue
            field_name = style.get("fieldName") or ""
            if not field_name:
                continue
            color, _ = qgis_color_to_hex(style.get("textColor"))
            sym: Dict[str, Any] = {
                "kind": "Text",
                # GeoStyler attend une expression : ["PropertyName", champ]
                "label": ["PropertyName", field_name],
                "font": style.get("fontFamily") or "Arial",
                "size": qgis_size_to_px(style.get("fontSize"),
                                        style.get("fontSizeUnit")) or 12.0,
                "color": color or "#000000",
                "group": True,
            }
            buf = settings.find(".//text-buffer")
            if buf is not None and buf.get("bufferDraw") in ("1", "true"):
                hcolor, hop = qgis_color_to_hex(buf.get("bufferColor"))
                sym["haloColor"] = hcolor or "#ffffff"
                sym["haloSize"] = qgis_size_to_px(buf.get("bufferSize"),
                                                  buf.get("bufferSizeUnits")) or 1.0
                sym["haloOpacity"] = hop
            placement = settings.find("placement")
            if placement is not None:
                dist = qgis_size_to_px(placement.get("dist"),
                                       placement.get("distUnits"))
                if dist:
                    sym["perpendicularOffset"] = dist
                if (placement.get("placement") or "") in ("2", "3"):  # le long de la ligne
                    sym["followLine"] = True
            out.append((sym, str(idx)))
        return out

    # ---- filtres -------------------------------------------------------
    @staticmethod
    def _filter(expr: Optional[str], warnings: List[str]) -> Optional[Any]:
        """
        Traduit une expression QGIS simple en expression GeoStyler.
        Couvre : ELSE, "champ" = 'valeur', IN, AND/OR, comparaisons numériques.
        Les expressions complexes sont signalées et ignorées (la règle reste
        appliquée à tous les objets, ce qui est visible et donc corrigeable).
        """
        if expr is None:
            return None
        expr = expr.strip()
        if expr.upper() == "ELSE":
            return "ELSE"

        def denuder(token: str) -> str:
            """
            Retire les parenthèses ENGLOBANTES, et elles seules.

            Un simple str.strip("()") est piégeux : sur
                (typeass IN ('a','b','c'))
            il mange la parenthèse de tête ET les DEUX de queue, laissant une
            expression déséquilibrée que plus aucun motif ne reconnaît. On
            vérifie donc que la parenthèse ouvrante se referme bien tout à la
            fin avant de dépouiller, et on recommence tant que c'est le cas.
            """
            token = token.strip()
            while token.startswith("(") and token.endswith(")"):
                profondeur, dans_chaine, apparie = 0, False, True
                for position, caractere in enumerate(token):
                    if caractere == "'":
                        dans_chaine = not dans_chaine
                    elif dans_chaine:
                        continue
                    elif caractere == "(":
                        profondeur += 1
                    elif caractere == ")":
                        profondeur -= 1
                        # Retour à zéro avant la fin : la parenthèse de tête
                        # n'est pas celle qui se referme à la fin.
                        if profondeur == 0 and position != len(token) - 1:
                            apparie = False
                            break
                if not apparie:
                    break
                token = token[1:-1].strip()
            return token

        def deliterer(valeur: str) -> str:
            """
            Dépouille un littéral de ses quotes et rétablit les apostrophes
            échappées à la mode SQL : 'Zone d''isolement' → Zone d'isolement.
            """
            valeur = valeur.strip()
            if len(valeur) >= 2 and valeur[0] == valeur[-1] and valeur[0] in "'\"":
                interieur = valeur[1:-1]
                return interieur.replace(valeur[0] * 2, valeur[0])
            return valeur.strip("'\"")

        def _decouper_liste(contenu: str) -> List[str]:
            """
            Découpe le contenu d'un IN (...) sur les virgules de premier niveau,
            en ignorant celles qui se trouvent à l'intérieur d'une chaîne.
            """
            morceaux, courant, dans_chaine = [], [], False
            for caractere in contenu:
                if caractere == "'":
                    dans_chaine = not dans_chaine
                    courant.append(caractere)
                elif caractere == "," and not dans_chaine:
                    morceaux.append("".join(courant))
                    courant = []
                else:
                    courant.append(caractere)
            morceaux.append("".join(courant))
            return [m for m in (x.strip() for x in morceaux) if m]

        def atom(token: str) -> Optional[List[Any]]:
            token = denuder(token)
            m = re.match(r'^"?([\w\-. ]+)"?\s*(=|<>|!=|>=|<=|>|<)\s*(.+)$', token)
            if m:
                fieldname, op, value = m.group(1).strip(), m.group(2), m.group(3).strip()
                value = deliterer(value)
                ops = {"=": "PropertyIsEqualTo", "<>": "PropertyIsNotEqualTo",
                       "!=": "PropertyIsNotEqualTo",
                       ">=": "PropertyIsGreaterThanOrEqualTo",
                       "<=": "PropertyIsLessThanOrEqualTo",
                       ">": "PropertyIsGreaterThan", "<": "PropertyIsLessThan"}
                return [ops[op], ["PropertyName", fieldname], value]
            m = re.match(r'^"?([\w\-. ]+)"?\s+IS\s+NULL$', token, re.I)
            if m:
                return ["PropertyIsNull", ["PropertyName", m.group(1).strip()]]
            m = re.match(r'^"?([\w\-. ]+)"?\s+IN\s*\((.+)\)$', token, re.I)
            if m:
                fieldname = m.group(1).strip()
                values = [deliterer(v) for v in _decouper_liste(m.group(2))]
                terms = [["PropertyIsEqualTo", ["PropertyName", fieldname], v]
                         for v in values]
                out: Any = terms[0]
                for t in terms[1:]:
                    out = ["Or", out, t]
                return out
            m = re.match(r'^"?([\w\-. ]+)"?\s+LIKE\s+(.+)$', token, re.I)
            if m:
                return ["PropertyIsLike", ["PropertyName", m.group(1).strip()],
                        deliterer(m.group(2))]

            # Motif propre aux servitudes d'utilité publique :
            #     lower(string_to_array(idass, '-')[0]) = 'a1'
            # soit « le premier segment de idass, découpé sur le tiret, vaut
            # a1 ». C'est exactement « idass commence par a1- », sans
            # distinction de casse — ce qu'un PropertyIsLike exprime
            # nativement en OGC Filter, sans fonction propre à GeoServer.
            m = re.match(
                r"^lower\(\s*string_to_array\(\s*\"?([\w\-. ]+)\"?\s*,"
                r"\s*'([^']+)'\s*\)\s*\[\s*0\s*\]\s*\)\s*=\s*'([^']*)'$",
                token, re.I)
            if m:
                champ, separateur, valeur = m.group(1), m.group(2), m.group(3)
                return ["PropertyIsLike", ["PropertyName", champ.strip()],
                        f"{valeur}{separateur}%"]
            return None

        # On dépouille AVANT le découpage : « (a OR b) » doit se découper sur
        # son OR, ce qui n'arrive pas tant que celui-ci est enfermé dans une
        # parenthèse de premier niveau.
        expr = denuder(expr)

        # Découpage AND/OR de premier niveau (hors parenthèses et hors chaînes)
        for keyword, gs_op in ((" AND ", "And"), (" OR ", "Or")):
            depth, in_str, parts, start = 0, False, [], 0
            for i, ch in enumerate(expr):
                if ch == "'":
                    in_str = not in_str
                elif not in_str and ch == "(":
                    depth += 1
                elif not in_str and ch == ")":
                    depth -= 1
                elif not in_str and depth == 0 and \
                        expr[i:i + len(keyword)].upper() == keyword:
                    parts.append(expr[start:i])
                    start = i + len(keyword)
            if parts:
                parts.append(expr[start:])
                subs = [StandaloneBackend._filter(p, warnings) for p in parts]
                subs = [s for s in subs if s not in (None, "ELSE")]
                if len(subs) < 2:
                    return subs[0] if subs else None
                out = subs[0]
                for s in subs[1:]:
                    out = [gs_op, out, s]
                return out

        result = atom(expr)
        if result is None:
            warnings.append(f"Filtre QGIS non traduit (règle appliquée à tout) : {expr}")
        return result


def _svg_mark(svg_name: str, size: float, angle: float = 0.0) -> Dict[str, Any]:
    """
    Fabrique le symbolizer GeoStyler d'un pictogramme SVG.

    ATTENTION — piège de bridgestyle 0.1.9 : on pourrait croire qu'il faut
    émettre {"kind": "Icon", "image": "x.svg"}. C'est faux. Dans
    sld/fromgeostyler.py, `_iconSymbolizer()` teste l'extension puis délègue
    à `_markSymbolizer()`, lequel lit la clé "wellKnownName" et JAMAIS "image" :

        def _iconSymbolizer(sl):
            path = sl["image"]
            if path.lower().endswith(".svg"):
                return _markSymbolizer(sl)      # <- "image" est abandonné ici
        ...
        def _markGraphic(sl):
            shape = _symbolProperty(sl, "wellKnownName")
            if shape.lower().endswith(".svg") ...   # <- AttributeError si absent

    Un Icon SVG sans "wellKnownName" provoque donc systématiquement
    « 'NoneType' object has no attribute 'lower' ». On émet par conséquent un
    Mark portant le nom du SVG : bridgestyle le sérialise en
    <WellKnownName>file://x.svg</WellKnownName>, forme que la PHASE 4 normalise
    ensuite en <ExternalGraphic><OnlineResource xlink:href="svg/cnig/x.svg"/>.
    (Défaut remonté en SECTION 7, point E.)
    """
    sym: Dict[str, Any] = {
        "kind": "Mark",
        "wellKnownName": svg_name,
        "size": size,
        "fillOpacity": 1.0,
        "strokeOpacity": 0.0,
    }
    if angle:
        sym["rotate"] = angle
    return sym


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


# ------------------------------------------------------------------------------
#  [C] BACKEND STYLEFORGE — styleforge_core (Phase 5 du plan de bibliothèque)
# ------------------------------------------------------------------------------
class StyleforgeBackend(BaseBackend):
    """
    Utilise styleforge_core (styleforge_core.readers.qml + writers.sld) à la
    place de bridgestyle — début du rebranchement du CLI sur la bibliothèque
    générique (Phase 5 du plan_bibliotheque_styleforge.docx).

    Différences volontaires avec les deux backends ci-dessus :

    * NI PyQGIS NI bridgestyle ne sont requis (contrairement à 'qgis' ET
      'standalone', qui dépendent tous deux de bridgestyle.sld). C'est un
      backend pur Python, disponible partout où styleforge_core est installé.
    * Le filtre de règle est traduit directement et correctement par
      styleforge_core.readers.expressions (y compris l'idiome
      string_to_array(...)[0] et les noms de champ non guillemetés) : la
      fonction inject_missing_filters() ci-dessus, qui compense a posteriori
      les filtres abandonnés en silence par bridgestyle.qgis, n'a plus lieu
      d'être pour ce backend — aucun rattrapage n'est nécessaire.
    * res.geostyler est intentionnellement laissé à None : ce backend ne
      produit PAS le dictionnaire GeoStyler de bridgestyle, donc la PHASE 5
      (export MBStyle, qui lit res.geostyler) n'a rien à traiter pour ces
      résultats — elle les saute proprement (cf. la garde déjà présente dans
      main(), `res.geostyler is None`), sans erreur. styleforge_core a SA
      PROPRE écriture MBStyle (writers/mbstyle.py, déjà vérifiée à l'oracle
      QGIS), mais la brancher sur la PHASE 5 de ce script n'a pas encore été
      fait — chantier explicitement suivant, pas silencieusement abandonné
      (cf. rapport d'accompagnement de cette étape).
    * res.icons reste vide, comme pour StandaloneBackend (qui ne le peuple
      pas non plus) : le déploiement SVG (PHASE 3b) s'appuie sur sources.svg,
      pas sur cette liste complémentaire spécifique au backend QGIS.
    * PHASE 4 (SldPostProcessor) s'applique SANS MODIFICATION à la sortie de
      ce backend : c'est un post-traitement XML générique qui opère sur le
      texte SLD et sur le QML source (via HintExtractor), pas sur des
      structures internes à bridgestyle — vérifié en relisant son code avant
      d'écrire ce backend, pas supposé. Les hachures et VendorOption GeoServer
      restent donc injectées normalement, même en --backend styleforge.
    * SVG embarqués en base64 (IconSymbolizer.image = 'base64:...', cas
      dominant sur le corpus CNIG réel — QML produits par SLYR à partir des
      .lyrx ArcGIS) : DÉFAUT DÉCOUVERT au premier test de bout en bout de ce
      backend, PAS anticipé à l'écriture initiale — la PHASE 6 (audit)
      plantait (OSError: File name too long) en tentant de vérifier
      l'existence, en tant que CHEMIN DE FICHIER local, d'une valeur
      xlink:href qui était en réalité la chaîne base64 intégrale. Cause
      racine : styleforge_core.readers.qml transmet la propriété QML 'name'
      telle quelle dans le pivot (comportement correct pour un CHEMIN, faux
      pour du contenu embarqué) et styleforge_core.writers.sld — délibérément
      zéro-E/S — ne peut matérialiser ce contenu en fichier lui-même. Corrigé
      SANS dupliquer de logique : ecrire_sld() accepte maintenant un callback
      optionnel 'resoudre_image_embarquee' (voir sa docstring), branché ici
      (_resoudre_image_embarquee ci-dessous) sur la machinerie déjà existante
      et déjà testée pour les backends 'qgis'/'standalone'
      (register_svg_reference() + EMBEDDED_SVG + PHASE 3b deploy_svg()).
      styleforge_core lui-même lève ExpressionPivotNonEcrite s'il rencontre
      un tel SVG SANS ce callback — jamais un href cassé écrit en silence.
    """

    name = "styleforge"

    def __init__(self) -> None:
        self._ok = False

    def available(self) -> bool:
        if self._ok:
            return True
        try:
            import styleforge_core  # type: ignore  # noqa: F401
        except ImportError:
            # Installation « à plat » à côté du script (pas encore publiée
            # sur PyPI, cf. Phase 8 du plan) : le paquet vit dans un dossier
            # frère styleforge-core/ — ajouté à sys.path seulement s'il existe
            # réellement, jamais supposé.
            candidat = Path(__file__).resolve().parent / "styleforge-core"
            if candidat.is_dir() and str(candidat) not in sys.path:
                sys.path.insert(0, str(candidat))
            try:
                import styleforge_core  # type: ignore  # noqa: F401
            except ImportError as exc:
                Console.warn(f"styleforge_core introuvable : {exc}")
                return False
        self._ok = True
        return True

    @staticmethod
    def _resoudre_image_embarquee(image: str) -> Optional[str]:
        """
        Callback passé à styleforge_core.writers.sld.ecrire_sld() (paramètre
        'resoudre_image_embarquee', zéro-E/S côté écrivain — voir sa
        docstring). styleforge_core.readers.qml transmet la propriété QML
        'name'/'imageFile' TELLE QUELLE dans le pivot (IconSymbolizer.image) ;
        pour les QML SLYR/CNIG, c'est très majoritairement un SVG embarqué en
        base64 (convention QGIS 'base64:...'), jamais un chemin de fichier.

        On réutilise ICI la machinerie déjà construite et déjà testée pour les
        backends 'qgis'/'standalone' (register_svg_reference() décode,
        hache et enregistre dans EMBEDDED_SVG — matérialisé sur disque plus
        tard par GeoServerTreeBuilder.deploy_svg() en PHASE 3b) plutôt que
        d'écrire un second mécanisme d'extraction redondant. Le nom d'indice
        "cnig_picto" reprend celui déjà utilisé au même point pour
        StandaloneBackend (ligne ~3222), pour que les deux backends produisent
        des noms de fichiers stables et comparables sur le même corpus.

        Retourne le chemin relatif 'svg/cnig/<nom>.svg' (même convention que
        deploy_svg()/resolve_href() en PHASE 3-4), ou None si la valeur n'est
        ni du base64 reconnu ni un nom de fichier exploitable — auquel cas
        ecrire_sld() lève ExpressionPivotNonEcrite plutôt que d'écrire un href
        cassé en silence.
        """
        name = register_svg_reference(image, "cnig_picto")
        if name is None:
            return None
        return (SVG_SUBDIR / name).as_posix()

    def convert(self, qml: Path) -> ConversionResult:
        from styleforge_core.readers.qml import lire_fichier_qml
        from styleforge_core.writers.sld import ecrire_sld

        res = ConversionResult(source=qml, backend=self.name)
        try:
            lecture = lire_fichier_qml(str(qml))
        except Exception as exc:                            # noqa: BLE001
            res.error = f"styleforge_core (lecture QML) a échoué : {exc}"
            return res
        # Préfixe "Lecture QML :" : ces avertissements viennent de la
        # construction du pivot (lire_fichier_qml), PARTAGÉ par le SLD et le
        # MBStyle écrits ensuite depuis ce même pivot — ils concernent donc
        # les DEUX documents produits, pas seulement le SLD.
        res.warnings = [f"Lecture QML : {w}" for w in lecture.avertissements]
        sld_avertissements: List[str] = []
        try:
            sld_xml = ecrire_sld(
                lecture.style, nom_couche=safe_stem(qml.stem),
                resoudre_image_embarquee=self._resoudre_image_embarquee,
                avertissements=sld_avertissements,
            )
        except Exception as exc:                            # noqa: BLE001
            res.error = f"styleforge_core (écriture SLD) a échoué : {exc}"
            return res
        # AVANT ce correctif, ecrire_sld() recevait son paramètre
        # avertissements=... jamais câblé ici : chaque propriété de
        # symbolizer non écrite dans le SLD (voir _avertir_proprietes_non_
        # gerees dans styleforge_core.writers.sld) était donc perdue en
        # silence côté CLI — 1838 avertissements de ce type rien que sur le
        # corpus des 17 exemples du dépôt, découvert en vérifiant pourquoi
        # un avertissement "sans préfixe" du rapport ne disait pas à quel
        # document (SLD/MBStyle/les deux) il se rapportait. Préfixe "SLD :"
        # : spécifique à l'écrivain SLD, ne concerne PAS le MBStyle produit
        # à partir du même pivot (voir docstring de ecrire_sld).
        res.warnings += [f"SLD : {w}" for w in sld_avertissements]
        res.sld = sld_xml
        res.pivot_style = lecture.style
        return res


# ------------------------------------------------------------------------------
#  Orchestrateur de la PHASE 2
# ------------------------------------------------------------------------------
class BatchConverter:
    """
    Conversion par lot, tolérante aux pannes (un try/except par fichier).

    En plus du try/except, un REPLI PAR FICHIER : si le backend QGIS échoue sur
    un style — défaut interne de bridgestyle, cas de symbologie non géré — le
    backend autonome reprend ce style-là. Un style converti avec une fidélité
    légèrement moindre vaut mieux qu'un style perdu, et le rapport indique quel
    backend a produit chaque fichier.
    """

    def __init__(self, backend: BaseBackend,
                 fallback: Optional[BaseBackend] = None) -> None:
        self.backend = backend
        self.fallback = fallback

    def run(self, qml_files: Sequence[Path], styles_dir: Path) -> List[ConversionResult]:
        styles_dir.mkdir(parents=True, exist_ok=True)
        results: List[ConversionResult] = []
        total = len(qml_files)

        Console.step(f"PHASE 2 — Conversion de {total} style(s) "
                     f"via le backend '{self.backend.name}'")

        used_names: Set[str] = set()
        self.fallbacks = 0
        import time
        debut_lot = time.monotonic()
        for idx, qml in enumerate(qml_files, start=1):
            import time
            depart = time.monotonic()
            try:
                res = self.backend.convert(qml)
            except Exception as exc:                       # noqa: BLE001
                res = ConversionResult(source=qml, backend=self.backend.name)
                res.error = f"Exception non rattrapée : {exc}"
                res.warnings.append(traceback.format_exc(limit=3))

            # Repli : on retente avec l'autre backend plutôt que d'abandonner.
            if not res.ok and self.fallback is not None:
                echec = res.error
                try:
                    secours = self.fallback.convert(qml)
                except Exception as exc:                   # noqa: BLE001
                    secours = ConversionResult(source=qml,
                                               backend=self.fallback.name)
                    secours.error = f"Exception non rattrapée : {exc}"
                if secours.ok:
                    secours.warnings.insert(
                        0, f"Repli sur le backend « {self.fallback.name} » — "
                           f"le backend « {self.backend.name} » a échoué : {echec}")
                    secours.warnings.extend(res.warnings)
                    res = secours
                    self.fallbacks += 1

            if res.ok:
                # Le nom du style est celui du fichier QML d'origine, sans
                # préfixe technique ni changement de casse. La comparaison
                # d'unicité est insensible à la casse car les systèmes de
                # fichiers Windows le sont.
                stem = safe_stem(qml.stem)
                candidate, n = stem, 1
                while candidate.lower() in used_names:
                    n += 1
                    candidate = f"{stem}_{n}"
                used_names.add(candidate.lower())
                res.target = styles_dir / f"{candidate}.sld"
                # Écriture provisoire : la PHASE 4 réécrira le fichier corrigé.
                res.target.write_text(res.sld, encoding="utf-8")
                status = "OK  "
            else:
                status = "ECHEC"

            results.append(res)
            if res.ok and res.backend != self.backend.name:
                status = "REPLI"
            duree = time.monotonic() - depart
            ecoule = time.monotonic() - debut_lot
            reste = (ecoule / idx) * (total - idx) if idx else 0
            suffix = f" ({len(res.warnings)} avert.)" if res.warnings else ""
            suffix += f"  {duree:.1f} s"
            if idx < total:
                suffix += f"  |  ~{int(reste)} s restantes"
            Console.raw(f"   [{idx:>4}/{total}] {status} {qml.name}{suffix}")
            if res.error:
                Console.raw(f"            -> {res.error}")

        n_ok = sum(1 for r in results if r.ok)
        message = (f"PHASE 2 terminée : {n_ok}/{total} conversions réussies, "
                   f"{total - n_ok} échec(s).")
        if self.fallbacks:
            message += (f" Dont {self.fallbacks} via le backend de repli "
                        f"« {self.fallback.name} ».")
        message += f" En {int(time.monotonic() - debut_lot)} s."
        Console.ok(message)
        return results


# ==============================================================================
#  PHASE 3 — ARBORESCENCE GEOSERVER_DATA_DIR + GESTION STRICTE DES SVG
# ==============================================================================

class GeoServerTreeBuilder:
    """
    Construit :

        <out>/styles/
          |- *.sld
          `- svg/
             `- cnig/
                `- *.svg

    et réécrit TOUTES les références aux pictogrammes en chemins relatifs
    `svg/cnig/<fichier>.svg`.

    Deux formes de référence sont traitées :
      1. <ExternalGraphic><OnlineResource xlink:href="..."/></ExternalGraphic>
      2. <Mark><WellKnownName>file://xxx.svg</WellKnownName></Mark>
         (forme produite par bridgestyle/sld/fromgeostyler.py::_markGraphic,
          spécifique GeoServer). Elle est NORMALISÉE en ExternalGraphic, ce qui
          est à la fois conforme à l'XSD OGC et exigé par le cahier des charges.
    """

    def __init__(self, out_dir: Path) -> None:
        self.out_dir = out_dir
        self.styles_dir = out_dir / "styles"
        self.svg_dir = self.styles_dir / SVG_SUBDIR

    def prepare(self) -> None:
        self.styles_dir.mkdir(parents=True, exist_ok=True)
        self.svg_dir.mkdir(parents=True, exist_ok=True)
        Console.step(f"PHASE 3 — Arborescence GEOSERVER_DATA_DIR sous {self.out_dir}")
        Console.info(f"  styles/          -> {self.styles_dir}")
        Console.info(f"  styles/svg/cnig/ -> {self.svg_dir}")

    def deploy_svg(self, svg_files: Sequence[Path],
                   extra_icons: Iterable[str] = ()) -> Dict[str, str]:
        """
        Copie tous les SVG dans styles/svg/cnig/ et retourne l'index
        {nom_de_fichier_en_minuscules: chemin_relatif}.
        """
        index: Dict[str, str] = {}
        sources = list(svg_files) + [Path(p) for p in extra_icons if p]
        copied = 0
        # Le cache reflétant l'arborescence du dépôt, deux pictogrammes de
        # dossiers différents peuvent porter le même nom. On les départage par
        # leur CONTENU : contenu identique -> un seul fichier ; contenu
        # différent -> le premier est conservé sous son nom d'origine (c'est lui
        # que les SLD référencent, qui ne transportent que le nom de base) et la
        # collision est signalée.
        import hashlib
        seen: Dict[str, str] = {}          # nom -> empreinte du contenu retenu
        collisions = 0
        for src in sources:
            if not src.is_file() or src.suffix.lower() != ".svg":
                continue
            payload = src.read_bytes()
            digest = hashlib.sha1(payload).hexdigest()         # nosec B324
            key = src.name.lower()
            if key in seen:
                if seen[key] != digest:
                    collisions += 1
                continue
            seen[key] = digest
            dest = self.svg_dir / src.name
            if not dest.exists() or dest.read_bytes() != payload:
                dest.write_bytes(payload)
                copied += 1
            index[key] = (SVG_SUBDIR / src.name).as_posix()
        if collisions:
            Console.warn(f"{collisions} pictogramme(s) homonyme(s) de contenu "
                         f"différent dans le dépôt : la première version "
                         f"rencontrée est conservée.")

        # Pictogrammes EMBARQUÉS EN BASE64 dans les QML (cas dominant du CNIG) :
        # ils n'existent nulle part sous forme de fichier, on les matérialise.
        extracted = 0
        for name, payload in EMBEDDED_SVG.items():
            dest = self.svg_dir / name
            if not dest.exists() or dest.stat().st_size != len(payload):
                dest.write_bytes(payload)
                extracted += 1
            index[name.lower()] = (SVG_SUBDIR / name).as_posix()

        Console.ok(f"{copied} pictogramme(s) copié(s) depuis le dépôt, "
                   f"{extracted} extrait(s) du base64 des QML, "
                   f"{len(index)} SVG disponibles dans svg/cnig/.")
        return index

    @staticmethod
    def resolve_href(raw: str, index: Dict[str, str]) -> Optional[str]:
        """
        Transforme une référence quelconque (chemin Windows absolu, URL, nom nu,
        'file://x.svg', './symboles/x.svg') en chemin relatif `svg/cnig/x.svg`.

        Fine couche de compatibilité : la logique elle-même vit désormais dans
        styleforge_core.writers.sld_posttraitement.resoudre_href_svg(), pour
        être partagée avec le plugin QGIS — voir la docstring de ce module.
        """
        return resoudre_href_svg(raw, index)


# ==============================================================================
#  PHASE 4 — POST-TRAITEMENT XML ET CORRECTIFS GEOSERVER
# ==============================================================================
#
#  `XSD_ORDER`, `PROPRIETARY_TAGS`, `OGC_ELEMENTS`, `SldPostProcessor` et les
#  petits utilitaires `_sub`/`_css`/`_pretty_xml` ont été déplacés dans
#  styleforge_core.writers.sld_posttraitement (importés en tête de ce
#  fichier), pour être partagés avec le plugin QGIS (qgis-plugin/) plutôt que
#  dupliqués. L'appel, plus bas dans main(), est resté inchangé — ces noms
#  désignent maintenant le code importé, pas une redéfinition locale. Voir la
#  docstring de ce module pour la justification complète du déplacement.
# ==============================================================================


# ==============================================================================
#  PHASE 5 — EXPORT MBSTYLE (Mapbox GL Style JSON) POUR GEOSERVER
# ==============================================================================
#
#  GeoServer sait publier une couche vectorielle tuilée avec un style MBStyle
#  (extension « mbstyle »), au format JSON de la spécification Mapbox GL Style.
#  Le format pivot GeoStyler rend cet export presque gratuit : le QML n'est lu
#  qu'une fois, et le même dictionnaire alimente le SLD ET le MBStyle.
#
#  « Presque » : le module bridgestyle/mapboxgl/fromgeostyler.py est nettement
#  moins abouti que son homologue SLD. Les défauts constatés sur le corpus CNIG
#  sont détaillés dans le rapport Word (famille D) ; en voici les conséquences
#  pratiques, toutes neutralisées ici :
#
#    * KeyError 'spriteName' dès qu'un remplissage porte un graphicFill,
#      c'est-à-dire sur TOUTES les hachures du PLU. La clé n'est renseignée que
#      par le chemin QGIS ; on l'injecte donc nous-mêmes en amont.
#    * icon-image produit par _iconSymbolizer vaut ["p", ""] à cause d'une
#      parenthèse mal placée : os.path.basename(image)[0] prend la PREMIÈRE
#      LETTRE du nom de fichier. Corrigé en post-traitement.
#    * les propriétés icon-* sont écrites dans « paint » alors que la
#      spécification Mapbox les place dans « layout ». Déplacées.
#    * l'URL des tuiles vaut littéralement « URL to tiles - <nom> » et le
#      sprite « spriteSheet », deux valeurs de remplissage. Reconstruites à
#      partir de la configuration.
#    * les marques shape:// ressortent telles quelles dans icon-image ; on les
#      matérialise en motifs raster dans la feuille de sprites.
# ------------------------------------------------------------------------------


@dataclass
class MbStyleOptions:
    """Paramètres de l'export MBStyle, alimentés par [mbstyle] du .ini."""
    enabled: bool = False
    base_url: str = "http://localhost:8080/geoserver"
    workspace: str = ""
    #: URL du sprite ; déduite de base_url/workspace si laissée vide.
    sprite_url: Optional[str] = None
    #: URL des polices ; GeoServer sait servir des glyphes PBF.
    glyphs_url: Optional[str] = None
    #: Côté des vignettes de la feuille de sprites, en pixels.
    sprite_size: int = 64
    #: Génération effective des images de sprites (nécessite Qt).
    build_sprites: bool = True

    def resolved_sprite_url(self) -> str:
        if self.sprite_url:
            return self.sprite_url
        prefix = f"{self.base_url.rstrip('/')}"
        if self.workspace:
            return f"{prefix}/styles/{self.workspace}/sprite"
        return f"{prefix}/styles/sprite"

    def resolved_glyphs_url(self) -> str:
        if self.glyphs_url:
            return self.glyphs_url
        return (f"{self.base_url.rstrip('/')}/styles/"
                "{fontstack}/{range}.pbf")

    def tiles_url(self, layer: str) -> str:
        workspace = self.workspace or "workspace"
        return (f"{self.base_url.rstrip('/')}/gwc/service/wmts"
                f"?REQUEST=GetTile&SERVICE=WMTS&VERSION=1.0.0"
                f"&LAYER={workspace}:{layer}&STYLE="
                f"&TILEMATRIX=EPSG:900913:{{z}}&TILEMATRIXSET=EPSG:900913"
                f"&FORMAT=application/x-protobuf;type=mapbox-vector"
                f"&TILECOL={{x}}&TILEROW={{y}}")


# (`SpriteRegistry` a été déplacée dans styleforge_core.sprites, importée en
#  tête de ce fichier, pour être partagée avec le plugin QGIS. Voir la
#  docstring de ce module pour la justification complète du déplacement.)


class MbStyleExporter:
    """
    PHASE 5 — produit un fichier MBStyle JSON par style, à partir du même
    dictionnaire GeoStyler que celui utilisé pour le SLD.
    """

    def __init__(self, options: MbStyleOptions, svg_dir: Path) -> None:
        self.options = options
        self.sprites = SpriteRegistry(options.sprite_size)
        self.svg_dir = svg_dir
        self.stats: Counter = Counter()

    # ------------------------------------------------------------- préparation
    def _prepare(self, geostyler: Dict[str, Any]) -> None:
        """
        Injecte la clé « spriteName » attendue par bridgestyle et convertit les
        références de pictogrammes en noms de vignettes.

        Sans cette passe, _fillSymbolizer lève KeyError: 'spriteName' sur le
        premier remplissage hachuré — donc sur la quasi-totalité du corpus PLU.
        """
        def walk(symbolizer: Dict[str, Any], hint: Dict[str, Any]) -> None:
            kind = symbolizer.get("kind")
            if kind in ("Mark", "Icon"):
                reference = (symbolizer.get("wellKnownName")
                             or symbolizer.get("image") or "")
                name = None
                if str(reference).startswith("shape://"):
                    name = self.sprites.register_shape(
                        reference,
                        color=symbolizer.get("strokeColor")
                        or symbolizer.get("color") or "#000000",
                        stroke_width=symbolizer.get("strokeWidth") or 1.0,
                        spacing=symbolizer.get("size") or 8.0,
                        rotation=symbolizer.get("rotate") or 0.0)
                elif str(reference).lower().endswith(".svg"):
                    name = self.sprites.register_svg(reference, self.svg_dir)
                elif str(reference).lower() in SpriteRegistry.SIMPLE_SHAPES \
                        and str(reference).lower() != "circle":
                    # Marque simple utilisée telle quelle : _markSymbolizer la
                    # recopie dans icon-image, où elle ne correspond à aucune
                    # vignette. On l'inscrit au registre ET on réécrit
                    # wellKnownName, pour que la référence émise existe. Le
                    # cercle fait exception : Mapbox sait le dessiner nativement
                    # via une couche « circle », sans passer par le sprite.
                    name = self.sprites.register_shape(
                        reference,
                        color=symbolizer.get("strokeColor") or "#000000",
                        stroke_width=symbolizer.get("strokeWidth") or 1.0,
                        spacing=symbolizer.get("size") or 8.0,
                        fill_color=symbolizer.get("color"))
                    if name:
                        symbolizer["wellKnownName"] = name
                if name:
                    symbolizer["spriteName"] = name
                    self.stats["vignettes_referencees"] += 1

            for container in ("graphicFill", "graphicStroke"):
                for sub in symbolizer.get(container) or []:
                    if not isinstance(sub, dict):
                        continue
                    walk(sub, hint)
                    # Filet de sécurité : bridgestyle lit sub["spriteName"]
                    # SANS valeur par défaut. Toute vignette manquante fait
                    # échouer la conversion du style entier.
                    if "spriteName" not in sub:
                        fallback = self.sprites.register_shape(
                            sub.get("wellKnownName") or "square",
                            color=sub.get("strokeColor") or sub.get("color")
                            or "#000000",
                            stroke_width=sub.get("strokeWidth") or 1.0,
                            spacing=sub.get("size") or 8.0,
                            fill_color=sub.get("color"))
                        if fallback:
                            sub["spriteName"] = fallback
                            self.stats["vignettes_de_secours"] += 1
                        else:
                            # Dernier recours : une vignette générique, inscrite
                            # au registre pour que la référence existe bel et
                            # bien dans sprite.json.
                            sub["spriteName"] = self.sprites.register_shape(
                                "square", color="#000000") or "square"
                            self.stats["vignettes_generiques"] += 1

        for rule in geostyler.get("rules", []):
            symbolizers = [s for s in rule.get("symbolizers", [])
                           if isinstance(s, dict)]
            rule["symbolizers"] = self._split_patterned_fills(symbolizers)
            for symbolizer in rule["symbolizers"]:
                walk(symbolizer, rule)

    def _split_patterned_fills(
            self, symbolizers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Sépare « remplissage à motif » et « contour » en deux symbolizers.

        Contournement d'un défaut de mapboxgl/fromgeostyler.py::_fillSymbolizer :
        lorsqu'un remplissage porte à la fois un graphicFill et un contour, la
        fonction construit `fill` comme une LISTE puis retourne `[fill, line]`,
        soit une liste imbriquée. processSymbolizer() fait ensuite `s["Z"] = 0`
        sur cette liste et lève
            TypeError: list indices must be integers or slices, not str
        La conversion du style entier échoue. Or c'est la forme de toutes les
        prescriptions surfaciques hachurées du PLU : une hachure et un liseré.

        En scindant en amont, chaque symbolizer emprunte une branche saine, et
        le rendu final est identique puisque Mapbox superpose les couches.
        """
        result: List[Dict[str, Any]] = []
        for symbolizer in symbolizers:
            has_pattern = bool(symbolizer.get("graphicFill"))
            has_outline = symbolizer.get("outlineColor") is not None
            if symbolizer.get("kind") == "Fill" and has_pattern and has_outline:
                pattern = dict(symbolizer)
                outline = dict(symbolizer)
                for key in ("outlineColor", "outlineWidth", "outlineOpacity",
                            "outlineDasharray"):
                    pattern.pop(key, None)
                outline.pop("graphicFill", None)
                outline.pop("graphicFillMargin", None)
                outline.pop("color", None)
                result.extend([pattern, outline])
                self.stats["remplissages_scindes"] += 1
            else:
                result.append(symbolizer)
        return result

    # ------------------------------------------------------------- conversion
    def export(self, geostyler: Dict[str, Any], name: str,
               target: Path) -> Tuple[bool, List[str]]:
        import copy
        from bridgestyle.mapboxgl import fromgeostyler as mb   # type: ignore

        # Ceinture et bretelles : le backend QGIS purge déjà les valeurs Qt,
        # mais un pivot venu d'ailleurs (relecture d'un .json, futur backend)
        # pourrait en contenir. copy.deepcopy échouerait alors sur
        # « cannot pickle 'QVariant' object », en plein milieu du lot.
        purger_types_qt(geostyler)
        try:
            pivot = copy.deepcopy(geostyler)
        except Exception:                                  # noqa: BLE001
            # Dernier recours : une copie par aller-retour JSON, qui ne
            # conserve que des types simples — exactement ce dont MBStyle a
            # besoin.
            pivot = json.loads(json.dumps(geostyler, default=str))
        pivot["name"] = name
        self._prepare(pivot)

        try:
            raw, warnings = mb.convert(pivot)
        except Exception as exc:                               # noqa: BLE001
            return False, [f"bridgestyle.mapboxgl a échoué : "
                           f"{type(exc).__name__}: {exc}"]

        try:
            obj = json.loads(raw)
        except Exception as exc:                               # noqa: BLE001
            return False, [f"JSON MBStyle illisible : {exc}"]

        self._postprocess(obj, name)
        reparations = self._repair_filters(obj, pivot)
        target.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n",
                          encoding="utf-8", newline="\n")
        restantes = [w for w in (warnings or [])
                     if "wildcards are supported in LIKE" not in str(w)] \
            if reparations else list(warnings or [])
        return True, restantes

    # --------------------------------------------------------- post-traitement
    def _postprocess(self, obj: Dict[str, Any], name: str) -> None:
        """Corrige les valeurs de remplissage et les erreurs de bridgestyle."""
        options = self.options

        obj["name"] = name
        obj["sprite"] = options.resolved_sprite_url()
        obj["glyphs"] = options.resolved_glyphs_url()
        for source in (obj.get("sources") or {}).values():
            if isinstance(source, dict) and "tiles" in source:
                source["tiles"] = [options.tiles_url(name)]
                self.stats["url_tuiles_corrigees"] += 1

        for layer in obj.get("layers", []):
            if not isinstance(layer, dict):
                continue
            paint = layer.get("paint") or {}
            layout = layer.get("layout") or {}

            # icon-* appartient à « layout » selon la spécification Mapbox ;
            # _iconSymbolizer les écrit à tort dans « paint ».
            for key in [k for k in list(paint) if k.startswith("icon-")]:
                layout[key] = paint.pop(key)
                self.stats["proprietes_icon_deplacees"] += 1

            # icon-image mutilé par os.path.basename(image)[0]
            value = layout.get("icon-image")
            if isinstance(value, (list, tuple)) and value and all(
                    isinstance(v, str) for v in value):
                repaired = self._repair_icon_name("".join(value))
                if repaired:
                    layout["icon-image"] = repaired
                    self.stats["icon_image_reparees"] += 1
            elif isinstance(value, str) and value not in self.sprites.svg:
                # _markSymbolizer de mapboxgl recopie wellKnownName tel quel
                # dans icon-image : « shape://slash », « triangle », « square »…
                # Aucune de ces valeurs n'est un nom de vignette. On inscrit la
                # marque dans la feuille de sprites et on référence son nom.
                repaired = self.sprites.register_shape(
                    value,
                    color=paint.get("icon-color") or "#000000")
                if repaired:
                    layout["icon-image"] = repaired
                    self.stats["icon_image_reparees"] += 1

            # Même traitement pour les motifs de remplissage
            pattern = paint.get("fill-pattern")
            if isinstance(pattern, str) and pattern not in self.sprites.svg \
                    and pattern not in self.sprites.shapes:
                repaired = self.sprites.register_shape(pattern)
                if repaired:
                    paint["fill-pattern"] = repaired
                    self.stats["icon_image_reparees"] += 1

            # fill-opacity nulle sur une couche à motif : la vignette
            # deviendrait invisible. La valeur vient de la clé fillOpacity du
            # sous-symbole, qui en SLD signifie « ne pas remplir l'intérieur de
            # la marque » — une sémantique sans équivalent ici, où fill-opacity
            # pilote l'opacité de TOUT le motif.
            if paint.get("fill-pattern") is not None:
                if not paint.get("fill-opacity"):
                    paint["fill-opacity"] = 1
                    self.stats["opacites_de_motif_corrigees"] += 1

            # Valeurs nulles : Mapbox rejette null là où il attend un nombre
            for holder in (paint, layout):
                for key in [k for k, v in holder.items() if v is None]:
                    del holder[key]
                    self.stats["valeurs_nulles_supprimees"] += 1

            if paint:
                layer["paint"] = paint
            else:
                layer.pop("paint", None)
            if layout:
                layer["layout"] = layout
            else:
                layer.pop("layout", None)

    # ------------------------------------------------------------- filtres
    #
    #  DÉFAUT bridgestyle (mapboxgl/fromgeostyler.py, fonction convertExpression)
    #  ------------------------------------------------------------------------
    #  Un PropertyIsLike dont le « % » n'est pas des DEUX côtés déclenche
    #      « Only enclosing % wildcards are supported in LIKE »
    #  et la fonction retourne None. Conséquences, toutes silencieuses :
    #    * filtre composé  -> ["all", null, ...]  : expression INVALIDE, la
    #      feuille de style entière est refusée au chargement par Mapbox GL /
    #      MapLibre ;
    #    * filtre simple   -> aucune clé "filter" : la règle s'applique à TOUS
    #      les objets, ce qui superpose 77 symbologies sur le même polygone.
    #
    #  Les servitudes d'utilité publique n'utilisent QUE des préfixes
    #  (« idass commence par a1- »). On retraduit donc nous-mêmes, à partir du
    #  pivot GeoStyler, en expression Mapbox GL :
    #      ["==", ["slice", ["downcase", ["to-string", ["get","idass"]]], 0, 3],
    #             "a1-"]
    #  « slice », « downcase » et « index-of » font partie de la spécification
    #  d'expressions v8 et sont interprétés par MapLibre GL comme par Mapbox GL.
    # ------------------------------------------------------------------------

    _RULE_ID = re.compile(r"\(rule#(\d+)\)")

    def _repair_filters(self, obj: Dict[str, Any],
                        pivot: Dict[str, Any]) -> int:
        """Réécrit les filtres que bridgestyle a laissés nuls ou absents."""
        regles = pivot.get("rules") or []
        reparations = 0

        for layer in obj.get("layers", []):
            if not isinstance(layer, dict):
                continue
            actuel = layer.get("filter")
            # Un filtre complet et sans « null » est laissé tel quel.
            if actuel is not None and not self._contient_null(actuel):
                continue

            marqueur = self._RULE_ID.search(str(layer.get("id") or ""))
            if not marqueur:
                continue
            indice = int(marqueur.group(1))
            if indice >= len(regles):
                continue
            source = (regles[indice] or {}).get("filter")
            if source in (None, "ELSE"):
                continue

            traduit = self._mb_filter(source)
            if traduit is None:
                continue
            if actuel is None or traduit != actuel:
                layer["filter"] = traduit
                reparations += 1
                self.stats["filtres_mbstyle_reparés"] += 1
        return reparations

    @staticmethod
    def _contient_null(noeud: Any) -> bool:
        """Cherche un None dans une expression Mapbox GL, à n'importe quel étage."""
        if noeud is None:
            return True
        if isinstance(noeud, (list, tuple)):
            return any(MbStyleExporter._contient_null(x) for x in noeud)
        return False

    @staticmethod
    def _mb_filter(noeud: Any) -> Optional[Any]:
        """
        Traduit un filtre GeoStyler en expression Mapbox GL (spécification v8).
        Retourne None si l'opérateur n'a pas d'équivalent — l'appelant laisse
        alors le filtre en l'état plutôt que d'en fabriquer un faux.
        """
        if not isinstance(noeud, (list, tuple)) or not noeud:
            return None
        operateur = str(noeud[0])

        # --- combinaisons ------------------------------------------------
        if operateur in ("And", "Or"):
            enfants = [MbStyleExporter._mb_filter(x) for x in noeud[1:]]
            if any(e is None for e in enfants):
                return None
            return ["all" if operateur == "And" else "any"] + enfants
        if operateur == "Not":
            enfant = MbStyleExporter._mb_filter(noeud[1])
            return None if enfant is None else ["!", enfant]

        # --- accès au champ ----------------------------------------------
        def champ(reference: Any) -> Any:
            if isinstance(reference, (list, tuple)) and len(reference) == 2 \
                    and str(reference[0]) == "PropertyName":
                return ["get", str(reference[1])]
            return reference

        if operateur == "PropertyIsNull":
            return ["!", ["has", str(noeud[1][1])]]

        comparaisons = {
            "PropertyIsEqualTo": "==", "PropertyIsNotEqualTo": "!=",
            "PropertyIsLessThan": "<", "PropertyIsLessThanOrEqualTo": "<=",
            "PropertyIsGreaterThan": ">", "PropertyIsGreaterThanOrEqualTo": ">=",
        }
        if operateur in comparaisons and len(noeud) >= 3:
            return [comparaisons[operateur], champ(noeud[1]), noeud[2]]

        # --- LIKE ---------------------------------------------------------
        if operateur == "PropertyIsLike" and len(noeud) >= 3:
            cible = champ(noeud[1])
            motif = str(noeud[2])
            # La source QGIS compare en minuscules (fonction lower) : on
            # reproduit exactement cette sémantique.
            texte = ["downcase", ["to-string", cible]]
            debut, fin = motif.startswith("%"), motif.endswith("%")
            noyau = motif.strip("%").lower()
            if not noyau:
                return None
            if debut and fin:                                # %milieu%
                return ["!=", ["index-of", noyau, texte], -1]
            if fin:                                          # préfixe%
                return ["==", ["slice", texte, 0, len(noyau)], noyau]
            if debut:                                        # %suffixe
                return ["==", ["slice", texte, -len(noyau)], noyau]
            return ["==", texte, noyau]                      # aucun joker
        return None

    def _repair_icon_name(self, mutilated: str) -> Optional[str]:
        """
        Retrouve le nom de vignette à partir du fragment laissé par
        bridgestyle. Le fragment vaut la première lettre du nom de fichier :
        on cherche donc l'unique vignette qui commence par cette lettre.
        """
        candidates = [n for n in sorted(self.sprites.svg)
                      if n.startswith(mutilated.lower())]
        if len(candidates) == 1:
            return candidates[0]
        return None

# ==============================================================================
#  PHASE 6 — AUDIT DE CONFORMITÉ GEOSERVER
# ==============================================================================
#
#  Objectif : ne livrer aucun SLD dont on ne sache pas s'il fonctionnera.
#
#  GeoServer refuse un style en validation stricte, ou pire le rend de travers
#  sans rien signaler. Le schéma XSD officiel n'étant pas toujours accessible
#  (réseau d'entreprise, proxy), l'audit reproduit ici les règles qui comptent :
#  le modèle de contenu de SLD 1.0.0, les extensions admises par GeoServer, et
#  les pièges de rendu que l'XSD ne voit pas — un <Stroke/> vide qui fabrique un
#  contour noir, un pictogramme référencé mais absent du dossier.
#
#  L'audit tourne sur les fichiers ÉCRITS, pas sur des structures en mémoire :
#  c'est bien le livrable qui est contrôlé.
# ------------------------------------------------------------------------------

#: Éléments dont le contenu doit être un nombre.
AUDIT_NUMERIQUES = {
    "Size", "Rotation", "Opacity", "MinScaleDenominator", "MaxScaleDenominator",
    "PerpendicularOffset", "Radius", "DisplacementX", "DisplacementY",
    "AnchorPointX", "AnchorPointY", "Priority",
}

#: Éléments d'expression OGC admis à l'intérieur d'un ParameterValueType.
#: Leur présence rend l'élément parent valide même sans texte.
AUDIT_EXPRESSIONS = {
    "Literal", "PropertyName", "Function", "Add", "Sub", "Mul", "Div",
}

#: Marques admises par GeoServer, hors préfixe « shape:// ».
AUDIT_WELLKNOWN = {"circle", "square", "triangle", "star", "cross", "x"}

#: VendorOption reconnues par GeoServer. Une option inconnue est ignorée
#: silencieusement par le moteur de rendu : autant la repérer ici.
AUDIT_VENDOR = {
    "graphic-margin", "graphic-resize", "random", "random-seed",
    "random-tile-size", "random-symbol-count", "random-rotation",
    "composite", "composite-base", "sortBy", "sortByGroup",
    "group", "spaceAround", "maxDisplacement", "conflictResolution",
    "goodnessOfFit", "partials", "autoWrap", "followLine", "repeat",
    "maxAngleDelta", "polygonAlign", "labelObstacle", "inclusion",
    "labelAllGroup", "forceLeftToRight", "allGroup", "underlineText",
    "strikethroughText", "charSpacing", "wordSpacing", "displacementMode",
    "fontShrinkSizeMin", "graphic-margin-top",
}

#: Noms de CssParameter valides en SLD 1.0.
AUDIT_CSS = {
    "fill", "fill-opacity", "stroke", "stroke-width", "stroke-opacity",
    "stroke-linejoin", "stroke-linecap", "stroke-dasharray", "stroke-dashoffset",
    "font-family", "font-size", "font-style", "font-weight",
}


class GeoServerAuditor:
    """
    PHASE 6 — contrôle chaque SLD produit et refuse de conclure « prêt » sans
    preuve. Retourne un compte rendu par catégorie de problème.
    """

    XLINK = "{http://www.w3.org/1999/xlink}"

    def __init__(self, styles_dir: Path) -> None:
        self.styles_dir = styles_dir
        self.problemes: Counter = Counter()
        self.details: Dict[str, List[str]] = defaultdict(list)
        #: Extensions GeoServer volontairement présentes : elles ne sont pas des
        #: défauts, mais elles interdisent d'affirmer une conformité XSD stricte.
        #: Les taire serait le vrai défaut.
        self.extensions: Counter = Counter()
        self.controles = 0

    # ------------------------------------------------------------------ util
    def _ko(self, categorie: str, message: str) -> None:
        self.problemes[categorie] += 1
        if len(self.details[categorie]) < 5:
            self.details[categorie].append(message)

    def _extension(self, categorie: str) -> None:
        self.extensions[categorie] += 1

    @staticmethod
    def _nom(element: Any) -> str:
        tag = element.tag
        if not isinstance(tag, str):
            return ""
        return tag.split("}", 1)[1] if "}" in tag else tag

    # ------------------------------------------------------------------- API
    def audit(self, fichiers: Sequence[Path]) -> Counter:
        for chemin in fichiers:
            if chemin is None or not chemin.is_file():
                continue
            self.controles += 1
            self._audit_fichier(chemin)
            pump_ui()
        return self.problemes

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
        ordre = XSD_ORDER.get(balise)
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
        if balise in AUDIT_NUMERIQUES:
            if len(element):
                # Le contrôle descend TOUT le sous-arbre : une balise étrangère
                # nichée sous un <ogc:Mul> est aussi fautive qu'à la racine de
                # l'expression, et un contrôle limité au premier niveau ne la
                # verrait jamais.
                inconnus = sorted({self._nom(e) for e in element.iter()
                                   if e is not element
                                   and self._nom(e) not in AUDIT_EXPRESSIONS})
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
            elif cle not in AUDIT_CSS:
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
                if not (valeur in AUDIT_WELLKNOWN
                        or valeur.startswith(("shape://", "file://",
                                              "wkt://", "ttf://"))):
                    self._ko("WellKnownName non reconnu par GeoServer",
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
                    cible = self.styles_dir / href.split("?", 1)[0]
                    if not cible.is_file():
                        self._ko("pictogramme référencé mais absent",
                                 f"{nom} : {href}")
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
            elif cle not in AUDIT_VENDOR:
                self._ko("VendorOption inconnue de GeoServer",
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

    # -------------------------------------------------------------- rapport
    def afficher(self) -> bool:
        """Affiche le compte rendu. Retourne True si tout est conforme."""
        Console.step(f"PHASE 6 — Audit de conformité GeoServer "
                     f"({self.controles} fichier(s))")
        if not self.problemes:
            Console.ok("Conforme : aucun défaut détecté.")
            Console.info("   encodage UTF-8 sans BOM, XML bien formé,")
            Console.info("   ordre des éléments conforme au modèle SLD 1.0.0,")
            Console.info("   valeurs numériques valides, aucun élément vide,")
            Console.info("   marques et VendorOption reconnues par GeoServer,")
            Console.info("   tous les pictogrammes référencés sont présents.")
            self._afficher_extensions()
            return True

        total = sum(self.problemes.values())
        Console.err(f"{total} défaut(s) de conformité répartis en "
                    f"{len(self.problemes)} catégorie(s) :")
        for categorie, nombre in self.problemes.most_common():
            Console.raw(f"   {categorie:<44} {nombre:>5}")
            for detail in self.details[categorie]:
                Console.raw(f"        {detail[:100]}")
        Console.info("Ces styles risquent d'être refusés à l'import ou de "
                     "rendre de travers.")
        self._afficher_extensions()
        return False

    def _afficher_extensions(self) -> None:
        """
        Déclare les extensions GeoServer présentes dans les styles produits.

        Une extension n'est pas un défaut : c'est une construction que
        GeoServer comprend et qu'un validateur XSD strict refusera. Les passer
        sous silence reviendrait à laisser croire à une portabilité que les
        styles n'ont pas — c'est précisément le genre de dégradation
        silencieuse que ce document reproche à bridge-style.
        """
        if not self.extensions:
            return
        Console.info("")
        Console.info("Extensions GeoServer assumées (hors XSD strict) :")
        for categorie, nombre in self.extensions.most_common():
            Console.raw(f"   {categorie:<52} {nombre:>5}")
        Console.info("   Elles sont nécessaires au rendu et comprises par "
                     "GeoServer,")
        Console.info("   mais un validateur XSD 1.0 strict les refusera.")

# ==============================================================================
#  SECTION 5 — PUBLICATION OPTIONNELLE SUR GEOSERVER (REST)
# ==============================================================================

class GeoServerPublisher:
    """
    Dépôt direct des SLD via l'API REST de GeoServer (pratique pour la recette
    « grandeur nature » du Style Étalon). Totalement optionnel.

    Équivalent curl :
      curl -u admin:geoserver -XPOST -H "Content-type: text/xml" \\
           -d "<style><name>plu_zonage</name><filename>plu_zonage.sld</filename></style>" \\
           http://localhost:8080/geoserver/rest/workspaces/cnig/styles
      curl -u admin:geoserver -XPUT -H "Content-type: application/vnd.ogc.sld+xml" \\
           -d @plu_zonage.sld \\
           http://localhost:8080/geoserver/rest/workspaces/cnig/styles/plu_zonage
    """

    def __init__(self, url: str, user: str, password: str,
                 workspace: Optional[str] = None) -> None:
        self.base = url.rstrip("/")
        self.auth = base64.b64encode(f"{user}:{password}".encode()).decode()
        self.workspace = workspace

    def _endpoint(self, suffix: str = "") -> str:
        if self.workspace:
            return f"{self.base}/rest/workspaces/{self.workspace}/styles{suffix}"
        return f"{self.base}/rest/styles{suffix}"

    def _request(self, method: str, url: str, body: bytes,
                 content_type: str) -> Tuple[int, str]:
        req = urllib.request.Request(url, data=body, method=method)
        req.add_header("Authorization", f"Basic {self.auth}")
        req.add_header("Content-type", content_type)
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:   # nosec B310
                return resp.status, resp.read().decode("utf-8", "replace")
        except urllib.error.HTTPError as exc:
            return exc.code, exc.read().decode("utf-8", "replace")
        except Exception as exc:                                # noqa: BLE001
            return -1, str(exc)

    def publish(self, sld_path: Path) -> Tuple[bool, str]:
        name = sld_path.stem
        meta = (f"<style><name>{name}</name>"
                f"<filename>{sld_path.name}</filename></style>").encode("utf-8")
        self._request("POST", self._endpoint(), meta, "text/xml")  # 409 si existe
        status, body = self._request(
            "PUT", self._endpoint(f"/{name}?raw=true"),
            sld_path.read_bytes(), "application/vnd.ogc.sld+xml")
        return (200 <= status < 300), f"HTTP {status} {body[:200]}"


# ==============================================================================
#  SECTION 6 — RAPPORT FINAL ET NOTICE DE DÉPLOIEMENT
# ==============================================================================

def _raison_echec_mbstyle(r: "ConversionResult") -> str:
    """Best-effort : remonte la raison d'un échec MBStyle (r.mbstyle is
    None alors que r.ok est vrai, donc le SLD a réussi et seule la PHASE 5
    a échoué) depuis les avertissements du résultat — il n'existe pas de
    champ structuré dédié (voir ConversionResult, PHASE 5). Ne retourne
    jamais une chaîne vide : l'absence de raison capturée est elle-même
    signalée, pas masquée."""
    for w in r.warnings:
        if w.startswith("MBStyle"):
            return w
    return "raison non capturée dans les avertissements (voir la console au moment de la génération)."


def write_reports(out_dir: Path,
                  reports: Sequence[ComplexityReport],
                  results: Sequence[ConversionResult],
                  post_stats: Counter,
                  svg_index: Dict[str, str],
                  audit_stats: Optional[Counter] = None,
                  audit_extensions: Optional[Counter] = None,
                  mbstyle_demande: bool = False) -> None:
    """Produit rapport_conversion.json + rapport_conversion.md + README.

    `mbstyle_demande` (nouveau) : indique si --mbstyle était actif pour
    cette exécution. SANS ce paramètre, le rapport Markdown ne comportait
    AUCUN compteur de succès/échec propre au MBStyle (seul le JSON gardait
    la liste des fichiers produits, sous `phase5_mbstyle`) : un rapport
    pouvait afficher "Styles convertis : 17/17" en ne parlant que du SLD,
    sans jamais dire si les 17 MBStyle correspondants avaient réellement
    été produits — une omission silencieuse contraire au principe du
    projet, découverte à l'usage réel plutôt qu'en test unitaire."""
    ok = [r for r in results if r.ok]
    ko = [r for r in results if not r.ok]
    warned = [r for r in ok if r.warnings]
    mbstyle_ok = [r for r in ok if r.mbstyle] if mbstyle_demande else []
    mbstyle_ko = [r for r in ok if mbstyle_demande and not r.mbstyle]

    payload = {
        "phase1_complexite": [
            {"fichier": r.name, "score": r.score, "regles": r.n_rules,
             "couches_symboles": r.n_symbol_layers, "geometrie": r.geometry,
             "renderer": r.renderer, "cas_de_figure": sorted(r.flags),
             "detail": dict(r.details), "erreur": r.error}
            for r in reports
        ],
        "phase2_conversion": [
            {"source": r.source.name,
             "cible": r.target.name if r.target else None,
             "backend": r.backend, "ok": r.ok, "erreur": r.error,
             "avertissements": r.warnings}
            for r in results
        ],
        "phase3_svg": {"nombre": len(svg_index),
                       "dossier": str(SVG_SUBDIR.as_posix())},
        "phase5_mbstyle": {
            "demande": mbstyle_demande,
            "produits": [
                {"source": r.source.name, "cible": r.mbstyle.name}
                for r in mbstyle_ok
            ],
            "echecs": [
                {"source": r.source.name, "raison": _raison_echec_mbstyle(r)}
                for r in mbstyle_ko
            ],
        },
        "phase4_posttraitement": dict(post_stats),
        "phase6_audit_geoserver": dict(audit_stats or {}),
        "phase6_extensions_geoserver": dict(audit_extensions or {}),
    }
    (out_dir / "rapport_conversion.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    audit_lines: List[str] = []
    if audit_stats is not None:
        audit_lines = ["", "## Audit de conformité GeoServer", ""]
        if not audit_stats:
            audit_lines.append("**Conforme** — aucun défaut détecté sur les "
                               "styles produits.")
        else:
            audit_lines += ["| Défaut | Occurrences |", "|---|---:|"]
            for cle, valeur in sorted(audit_stats.items(),
                                      key=lambda kv: -kv[1]):
                audit_lines.append(f"| {cle} | {valeur} |")
        if audit_extensions:
            # Une extension n'est pas un défaut, mais la taire reviendrait à
            # laisser croire à une portabilité que les styles n'ont pas.
            audit_lines += [
                "", "### Extensions GeoServer assumées", "",
                "Comprises par GeoServer, nécessaires au rendu, mais refusées "
                "par un validateur XSD 1.0 strict.", "",
                "| Extension | Occurrences |", "|---|---:|"]
            for cle, valeur in sorted(audit_extensions.items(),
                                      key=lambda kv: -kv[1]):
                audit_lines.append(f"| {cle} | {valeur} |")

    titre = "# Rapport de conversion QML CNIG -> SLD"
    if mbstyle_demande:
        titre += " / MBStyle"
    titre += " GeoServer"

    lines: List[str] = [
        titre, "",
        f"- Styles SLD convertis : **{len(ok)}/{len(results)}**",
        f"- Échecs SLD : **{len(ko)}**",
        f"- Conversions SLD avec avertissement : **{len(warned)}**",
    ]
    if mbstyle_demande:
        # Compteur dédié, absent avant ce correctif (voir docstring de
        # write_reports) : sans lui, rien dans ce rapport ne disait si les
        # MBStyle demandés avaient réellement été produits.
        lines += [
            f"- MBStyle produits : **{len(mbstyle_ok)}/{len(ok)}**",
            f"- MBStyle en échec : **{len(mbstyle_ko)}**",
        ]
    lines += [
        f"- Pictogrammes SVG déployés : **{len(svg_index)}**", "",
        "## Correctifs appliqués en phase 4", "",
        "| Correctif | Occurrences |", "|---|---:|",
    ]
    for key, value in sorted(post_stats.items(), key=lambda kv: -kv[1]):
        lines.append(f"| {key.replace('_', ' ')} | {value} |")

    lines += audit_lines

    if mbstyle_demande:
        lines += ["", "## MBStyle", ""]
        if not mbstyle_ok and not mbstyle_ko:
            lines.append("Aucun fichier SLD produit avec succès : aucun MBStyle "
                          "n'a pu être tenté.")
        else:
            lines.append(f"**{len(mbstyle_ok)}/{len(ok)}** fichier(s) SLD "
                         f"produit(s) avec succès ont également donné lieu à "
                         f"un MBStyle.")
            if mbstyle_ko:
                lines += ["", "### Échecs MBStyle", ""]
                for r in mbstyle_ko:
                    lines.append(f"- `{r.source.name}` : "
                                 f"{_raison_echec_mbstyle(r)}")
            else:
                lines.append("Aucun échec.")

    if ko:
        lines += ["", "## Échecs de conversion SLD", ""]
        for r in ko:
            lines.append(f"- `{r.source.name}` : {r.error}")
    if warned:
        lines += ["", "## Avertissements", ""]
        PAR_CATEGORIE = 6
        if mbstyle_demande:
            # Explicite plutôt qu'à déduire du préfixe : clarifie à quel(s)
            # document(s) produit(s) chaque avertissement se rapporte.
            #
            # CORRECTIF : avant, l'échantillonnage par fichier prenait les 6
            # premiers avertissements TOUTES CATÉGORIES CONFONDUES, dans
            # l'ordre d'ajout (Lecture QML d'abord, puis SLD, puis MBStyle).
            # Un fichier avec >=6 avertissements "Lecture QML :" masquait donc
            # TOUJOURS ses avertissements "SLD :"/"MBStyle :" dans ce rapport
            # — silencieusement, sans même dire qu'il manquait quelque chose.
            # Vérifié concrètement : sur les 17 exemples de ce dépôt, 16/17
            # fichiers avaient au moins 6 avertissements "Lecture QML :", donc
            # 16/17 ne montraient JAMAIS leurs avertissements "SLD :" ici, même
            # après avoir câblé ecrire_sld(..., avertissements=...) plus haut
            # dans ce fichier — le correctif précédent restait sans effet
            # visible dans ce rapport pour la quasi-totalité du corpus.
            # Chaque catégorie présente est donc désormais échantillonnée
            # SÉPARÉMENT, et toute troncature est dite explicitement plutôt
            # que tue.
            lines += [
                "Chaque avertissement précise le document concerné par son "
                "préfixe : **`Lecture QML :`** (construction du pivot, "
                "commun au SLD ET au MBStyle, puisque les deux en sont "
                "dérivés), **`SLD :`** (spécifique à l'écrivain SLD) ou "
                "**`MBStyle :`** (spécifique à l'écrivain MBStyle). Par "
                f"fichier, chaque catégorie présente est échantillonnée "
                f"séparément (jusqu'à {PAR_CATEGORIE} avertissements) : une "
                "catégorie nombreuse (typiquement « Lecture QML ») ne masque "
                "donc pas les avertissements d'une autre catégorie moins "
                "nombreuse. Liste exhaustive, non tronquée : "
                "`rapport_conversion.json` (`phase2_conversion`).", "",
            ]
        PREFIXES = ("Lecture QML : ", "SLD : ", "MBStyle : ")
        for r in warned[:60]:
            lines.append(f"- `{r.source.name}`")
            if not mbstyle_demande:
                # Pas de distinction SLD/MBStyle à faire (MBStyle non
                # demandé) : un seul échantillon, mais la troncature reste
                # explicite plutôt que silencieuse.
                for w in r.warnings[:PAR_CATEGORIE]:
                    lines.append(f"  - {w}")
                reste = len(r.warnings) - PAR_CATEGORIE
                if reste > 0:
                    lines.append(
                        f"  - … et {reste} autre(s) avertissement(s) non "
                        f"affiché(s) ici — voir rapport_conversion.json.")
                continue
            groupes: Dict[str, List[str]] = {}
            for w in r.warnings:
                for p in PREFIXES:
                    if w.startswith(p):
                        groupes.setdefault(p[:-3], []).append(w[len(p):])
                        break
                else:
                    groupes.setdefault("Autre", []).append(w)
            for cle, items in groupes.items():
                prefixe = f"{cle} : " if cle != "Autre" else ""
                for w in items[:PAR_CATEGORIE]:
                    lines.append(f"  - {prefixe}{w}")
                reste = len(items) - PAR_CATEGORIE
                if reste > 0:
                    lines.append(
                        f"  - … et {reste} autre(s) avertissement(s) "
                        f"« {cle} » non affiché(s) ici — voir "
                        f"rapport_conversion.json.")
    (out_dir / "rapport_conversion.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8")
    Console.ok(f"Rapports écrits : rapport_conversion.json / .md")


DEPLOY_NOTICE = """\
================================================================================
 NOTICE DE DÉPLOIEMENT DANS LE GEOSERVER_DATA_DIR
================================================================================

1. LOCALISER LE RÉPERTOIRE DE DONNÉES
   Interface d'admin GeoServer : « À propos & état » > « Répertoire de données ».
   Valeurs usuelles :
     - Windows (installeur) : C:\\ProgramData\\GeoServer\\data_dir
     - Windows (binaire)    : C:\\GeoServer\\data_dir
     - Linux / Docker       : /var/lib/geoserver_data  ou  /opt/geoserver_data
   En ligne de commande, la variable d'environnement GEOSERVER_DATA_DIR fait foi.

2. COPIER L'ARBORESCENCE PRODUITE
   Le dossier <sortie>/styles reproduit exactement la structure attendue :

       styles/
         |- plu_zonage.sld
         |- plu_prescriptions.sld
         |- ...
         `- svg/
            `- cnig/
               |- prescription_surfacique.svg
               `- ...

   PowerShell (fusion sans écraser les styles existants) :
       Copy-Item -Path ".\\build\\styles\\*" `
                 -Destination "$env:GEOSERVER_DATA_DIR\\styles" `
                 -Recurse -Force

   /!\\ Ne PAS renommer le dossier svg/cnig : les chemins relatifs inscrits dans
   les balises <OnlineResource> en dépendent (ils sont résolus par GeoServer
   depuis la racine du dossier styles/).

3. PRENDRE EN COMPTE LES STYLES
   Deux options :
     a) « Rechargement de la configuration » : interface d'admin >
        « Paramètres du serveur » > bouton « Recharger », ou
            curl -u admin:geoserver -XPOST http://<host>/geoserver/rest/reload
     b) Redémarrage du service GeoServer (Tomcat / service Windows).

   Les fichiers .sld déposés à la main n'apparaissent dans la liste des styles
   qu'après ce rechargement. Pour un référencement immédiat et propre, utiliser
   l'option --geoserver-url du script, qui passe par l'API REST.

4. AFFECTER UN STYLE À UNE COUCHE
   Couches > <votre couche> > onglet « Publication » > « Style par défaut ».
   Pour les documents d'urbanisme, associer typiquement :
     - zone_urba            -> plu_zonage
     - prescription_surf    -> plu_prescription_surfacique
     - prescription_lin     -> plu_prescription_lineaire
     - prescription_pct     -> plu_prescription_ponctuelle
     - info_surf / lin / pct-> plu_information_*

5. VÉRIFIER LE RENDU (recette « grandeur nature »)
   - Aperçu de couche > « OpenLayers » : contrôler les hachures et les SVG.
   - Requête WMS de contrôle (GetMap) sur une emprise connue :
       http://<host>/geoserver/wms?service=WMS&version=1.1.0&request=GetMap
         &layers=cnig:zone_urba&styles=plu_zonage&bbox=...&width=1024&height=1024
         &srs=EPSG:2154&format=image/png
   - Journal : <GEOSERVER_DATA_DIR>/logs/geoserver.log
     Un SVG manquant s'y signale par « Failed to load external graphic ».
   - Comparer côte à côte avec QGIS sur le « Style Étalon » identifié en phase 1.

6. DÉPLOYER LES STYLES MBSTYLE (si l'export a été demandé)
   Le dossier styles/ contient alors, à côté des .sld :
       <nom>.json          le style MBStyle (spécification Mapbox GL, version 8)
       sprite.png          la feuille de sprites : pictogrammes CNIG et
       sprite.json         motifs de hachure rasterisés
       sprite@2x.png       variante haute densité
       sprite@2x.json

   PRÉREQUIS : l'extension « mbstyle » de GeoServer, et des couches publiées en
   tuiles vectorielles (GeoWebCache, format application/vnd.mapbox-vector-tile).
   MBStyle ne s'applique PAS à une couche WMS classique : c'est là sa différence
   majeure avec le SLD, qui lui fonctionne sur toute couche.

   a) Copier les fichiers comme les .sld :
        Copy-Item ".\build\styles\*.json" "$env:GEOSERVER_DATA_DIR\styles" -Force
        Copy-Item ".\build\styles\sprite*" "$env:GEOSERVER_DATA_DIR\styles" -Force

   b) Déclarer chaque style avec le bon type de média :
        curl -u admin:geoserver -XPOST ^
             -H "Content-type: application/vnd.geoserver.mbstyle+json" ^
             -d @plu_psc_s.json ^
             "http://<hote>/geoserver/rest/workspaces/cnig/styles?name=plu_psc_s"

      Pour METTRE À JOUR un style déjà déclaré, utiliser PUT sur
      .../styles/plu_psc_s au lieu de POST.

   c) Associer le style à la couche tuilée, onglet « Publication », puis
      contrôler dans un client vectoriel (aperçu OpenLayers vector tiles,
      MapLibre, Mapbox GL JS).

   /!\ LES URL SONT ÉCRITES EN DUR DANS LE JSON — celles des tuiles, du sprite
   et des glyphes. Elles proviennent de base_url et workspace de la section
   [mbstyle] du fichier de configuration. Renseignez-les AVANT la génération :
   les modifier ensuite impose de régénérer, ou de reprendre chaque JSON à la
   main. Vérification rapide :
        Select-String -Path .\build\styles\plu_psc_s.json -Pattern '"sprite"|"tiles"'

   /!\ Les glyphes (polices des étiquettes) ne sont pas fournis par GeoServer
   par défaut. Si vos étiquettes n'apparaissent pas, renseignez glyphs_url vers
   un service de glyphes PBF existant.

7. POINTS DE VIGILANCE CONNUS
   - Encodage : tous les SLD sont écrits en UTF-8 SANS BOM. Un BOM fait échouer
     le parseur XML de GeoServer avec « Content is not allowed in prolog ».
   - Validation : si l'import REST échoue, ajouter ?raw=true à l'URL PUT pour
     court-circuiter la validation stricte, puis corriger le SLD.
   - Espacement des hachures : piloté par <Size> de la marque shape:// et par
     la VendorOption « graphic-margin ». Ajuster VENDOR_DEFAULTS si le rendu
     paraît trop dense ou trop aéré par rapport à QGIS.
   - Unités : QGIS raisonne en millimètres, SLD en pixels (1 px = 0,28 mm).
     Les styles en « unités carte » (MapUnit) ne sont pas convertibles sans
     échelle fixe : ils sont signalés dans rapport_conversion.md.
================================================================================
"""


# ==============================================================================
#  SECTION 7 — GUIDE DE CONTRIBUTION AMONT (Pull Request bridge-style)
# ==============================================================================
#
#  Ce script répare les dégradations EN AVAL (post-traitement XML). C'est le
#  choix pragmatique : aucune dépendance à une version patchée de bridge-style,
#  donc aucune régression lors d'un `pip install --upgrade`.
#
#  Si l'équipe souhaite au contraire corriger le problème À LA SOURCE et
#  soumettre une Pull Request sur https://github.com/GeoCat/bridge-style,
#  voici la cartographie précise des points d'intervention. Les numéros de
#  ligne correspondent à bridgestyle 0.1.9 ; ils sont donnés à titre indicatif.
#
#  ---------------------------------------------------------------------------
#  0. LE MODULE SLD EST INIMPORTABLE SANS PYQGIS   [priorité 0 — bug bloquant]
#  ---------------------------------------------------------------------------
#  Fichiers concernés :
#      bridge_style/bridgestyle/sld/fromgeostyler.py     ligne 7
#      bridge_style/bridgestyle/qgis/__init__.py         ligne 5
#      bridge_style/bridgestyle/mapboxgl/fromgeostyler.py ligne 6
#      bridge_style/bridgestyle/qgis/expressions.py      ligne 37
#
#  Reproduction sur une machine SANS QGIS, bridgestyle 0.1.9 fraîchement
#  installé depuis PyPI :
#      >>> import bridgestyle.sld.fromgeostyler
#      bridgestyle.qgis.expressions.CompatibilityException:
#          Your QGIS version is not compatible with bridgestyle
#
#  La chaîne fautive :
#      sld/fromgeostyler.py   : from ..qgis.expressions import (OGC_PROPERTYNAME,
#                                     OGC_IS_EQUAL_TO, OGC_IS_NULL, OGC_IS_LIKE)
#        -> déclenche qgis/__init__.py   : from .. import mapboxgl
#          -> mapboxgl/fromgeostyler.py  : from ..qgis import togeostyler
#            -> qgis/togeostyler.py      : from .expressions import ...
#              -> qgis/expressions.py    : raise CompatibilityException  (l. 37)
#
#  Conséquences : le module SLD (pur XML, zéro dépendance QGIS) est inutilisable
#  sans QGIS ; le CLI `style2style` l'est aussi pour toutes les conversions qui
#  touchent mapbox ou sld. Or les quatre symboles importés sont de SIMPLES
#  CONSTANTES DE TYPE CHAÎNE.
#
#  Correctifs possibles, du plus simple au plus propre :
#    1. Déplacer les constantes OGC_* dans un nouveau module neutre
#       `bridgestyle/ogc_constants.py`, importé par sld/ ET par qgis/.
#       C'est la PR la plus facile à faire accepter : purement mécanique,
#       aucun changement de comportement, aucun test à réécrire.
#    2. Rendre l'import de mapboxgl paresseux dans qgis/__init__.py
#       (le déplacer dans le corps des fonctions qui l'utilisent).
#    3. Transformer le `raise CompatibilityException` de la ligne 37 en
#       dégradation silencieuse : laisser BINOPS_MAP vide et ne lever
#       l'exception qu'à l'APPEL d'ExpressionConverter, pas à l'import.
#
#  Le présent script contourne le problème sans patcher la bibliothèque, via
#  install_bridgestyle_sld_shim() (SECTION 0-bis) : le code de ce shim liste
#  exactement les symboles à déplacer, il constitue donc la spécification de
#  la PR n°1.
#
#  ---------------------------------------------------------------------------
#  A. HACHURES : ANGLE ARRONDI AU QUADRANT      [priorité 1 — impact PLU majeur]
#  ---------------------------------------------------------------------------
#  Fichier : bridge_style/bridgestyle/qgis/togeostyler.py
#  Fonctions : _linePatternFillSymbolizer()  (~ligne 894)
#              _hatchMarkerForAngle()        (~ligne 907)
#
#      def _hatchMarkerForAngle(angle):
#          quadrant = math.floor(((angle + 22.5) % 180) / 45.)
#          return ["shape://vertline", "shape://slash",
#                  "shape://horline", "shape://backslash"][quadrant]
#
#  Problème : toute hachure CNIG à 30, 60 ou 120 degrés est ramenée au multiple
#  de 45 le plus proche, sans trace de l'écart. Une prescription hachurée à
#  30 deg devient visuellement identique à une hachure à 45 deg.
#
#  Correction proposée : retourner le couple (marque, rotation résiduelle) et
#  propager la rotation dans le symbolizer GeoStyler sous la clé "rotate",
#  déjà prise en charge par sld/fromgeostyler.py::_basePointSymbolizer().
#  Voir dans le présent script la fonction hatch_wkn_for_angle(), directement
#  transposable.
#
#  À corriger dans le même mouvement : _linePatternFillSymbolizer() lit
#  `sl.color()` et « line_width » au niveau de la couche de motif, alors que la
#  couleur et l'épaisseur réelles vivent dans le SOUS-SYMBOLE de type ligne
#  (`sl.subSymbol().symbolLayers()`), qui peut en outre porter des tirets.
#  Enfin, les propriétés « offset » / « offset_unit » sont purement ignorées.
#
#  ---------------------------------------------------------------------------
#  B. ESPACEMENT DES MOTIFS PERDU : INCOHÉRENCE DE CLÉ  [priorité 1 — bug franc]
#  ---------------------------------------------------------------------------
#  Fichier producteur : bridge_style/bridgestyle/qgis/togeostyler.py
#                       _simpleFillSymbolizer()          (~ligne 935)
#      symbolizer["graphicFillDistanceX"] = FIXED_PATTERN_SIZE / 2.0
#      symbolizer["graphicFillDistanceY"] = FIXED_PATTERN_SIZE / 2.0
#
#  Fichier consommateur : bridge_style/bridgestyle/sld/fromgeostyler.py
#                         _fillSymbolizer()               (~ligne 470)
#      elif _symbolProperty(sl, "graphicFillMarginY") and \
#           _symbolProperty(sl, "graphicFillMarginX"):
#
#  Le producteur écrit « ...DistanceX/Y », le consommateur lit
#  « ...MarginX/Y » : la valeur n'est JAMAIS transmise et GeoServer applique son
#  espacement par défaut. Correctif d'une ligne, mais il faut trancher le nom
#  canonique (« graphicFillMargin* » est cohérent avec la VendorOption
#  GeoServer « graphic-margin ») et garder une rétrocompatibilité de lecture.
#
#  ---------------------------------------------------------------------------
#  C. BROSSES QT NON MAPPÉES                    [priorité 2 — rendu vide sous GS]
#  ---------------------------------------------------------------------------
#  Fichier : bridge_style/bridgestyle/qgis/togeostyler.py
#  Constante : PATTERN_NAMES                      (~ligne 36)
#
#      PATTERN_NAMES = {
#          "horizontal": "shape://horline",
#          "vertical":   "shape://vertline",
#          "cross":      "shape://times"
#          # TODO
#      }
#
#  Les styles Qt « b_diagonal », « f_diagonal », « diagonal_x » et « dense1 »
#  à « dense7 » ne sont pas mappés : _simpleFillSymbolizer() les recopie tels
#  quels dans <WellKnownName>, valeur que GeoServer ne reconnaît pas (polygone
#  rendu vide, sans message d'erreur). Le « # TODO » présent dans le code est
#  une invitation explicite à contribuer. Voir QT_BRUSH_TO_WKN dans ce script
#  pour une table complète, directement réutilisable.
#
#  ---------------------------------------------------------------------------
#  D. <Stroke/> VIDE = CONTOUR NOIR FANTÔME                      [priorité 2]
#  ---------------------------------------------------------------------------
#  Fichier : bridge_style/bridgestyle/sld/fromgeostyler.py
#  Fonction : _markGraphic()                        (~ligne 409)
#      stroke = _addSubElement(mark, "Stroke")
#      if strokeOpacity:
#          ...
#
#  L'élément <Stroke> est créé AVANT le test d'opacité : si l'opacité est nulle,
#  un <Stroke/> vide subsiste, et GeoServer le rend comme un contour noir de
#  1 px. Correctif : ne créer l'élément que dans la branche utile.
#  Même schéma à vérifier pour <Fill> et pour <Size/> laissé vide quand la
#  taille est None (_basePointSymbolizer(), ~ligne 380).
#
#  ---------------------------------------------------------------------------
#  E. SVG : WellKnownName file:// AU LIEU D'ExternalGraphic        [priorité 3]
#  ---------------------------------------------------------------------------
#  Fichier : bridge_style/bridgestyle/sld/fromgeostyler.py
#  Fonction : _markGraphic()                        (~ligne 415)
#      if shape.lower().endswith(".svg") and "://" not in shape:
#          shape = f"file://{os.path.basename(shape)}"
#
#  Cette écriture est une extension GeoServer, hors XSD OGC, et elle aplatit le
#  chemin (impossible de ranger les pictogrammes dans un sous-dossier). Une PR
#  pourrait produire un <ExternalGraphic><OnlineResource xlink:href="..."/>
#  avec un préfixe de dossier paramétrable via `options` (le dictionnaire
#  d'options est déjà propagé jusqu'ici par convert()).
#
#  ---------------------------------------------------------------------------
#  F. ABSENCE D'ENTRÉE « QML » DANS LE CLI                          [priorité 3]
#  ---------------------------------------------------------------------------
#  Fichier : bridge_style/bridgestyle/style2style.py
#      _exts = {"sld": sld, "geostyler": geostyler,
#               "mapbox": mapboxgl, "lyrx": arcgis}
#
#  Le module `qgis` n'y figure pas car il exige PyQGIS. Une PR utile consisterait
#  à enregistrer conditionnellement une entrée "qml" qui tente l'import de
#  qgis.core et affiche un message d'aide explicite en cas d'absence, plutôt que
#  le laconique « Unsupported style type: 'qml' ».
#
#  ---------------------------------------------------------------------------
#  G. DASHARRAY DÉCIMAL : ValueError QUI FAIT ÉCHOUER TOUT LE STYLE
#                                             [priorité 1 — constaté sur le PLU]
#  ---------------------------------------------------------------------------
#  Fichier : bridge_style/bridgestyle/sld/fromgeostyler.py
#  Fonction : _lineSymbolizer()                     (~ligne 330)
#
#      if dasharray is not None:
#          if cap != "butt":
#              try:
#                  EXTRA_GAP = 2 * width
#                  tokens = [int(v) + EXTRA_GAP if i % 2 else int(v)
#                            for i, v in enumerate(dasharray.split(" "))]
#              except:                      # <- n'attrape PAS le cas utile
#                  GAP_FACTOR = 2
#                  tokens = [int(v) * GAP_FACTOR if i % 2 else int(v)
#                            for i, v in enumerate(dasharray.split(" "))]
#
#  `int("22.6786")` lève ValueError. Le `except:` nu est censé rattraper le cas
#  où `width` est une expression, mais la BRANCHE DE SECOURS refait exactement
#  le même `int(v)` sur les mêmes valeurs : l'exception se propage et la
#  conversion du style entier échoue.
#
#  Or un dasharray issu d'une conversion millimètres -> pixels est presque
#  toujours décimal (0,5 mm = 1,7857 px). Sur le corpus PLU du CNIG, 3 styles
#  sur 8 échouaient ainsi, dont le Style Étalon qml__plu_psc_s.qml :
#      « bridgestyle.sld.fromgeostyler a échoué :
#        invalid literal for int() with base 10: '6.2996' »
#
#  Correctif : utiliser float() puis arrondir à la sérialisation, et remplacer
#  le `except:` nu par `except (TypeError, ValueError):` autour du seul calcul
#  de EXTRA_GAP. C'est un cas de test de non-régression idéal : un QML avec
#  une ligne à tirets de 0,5 mm et un capstyle « square ».
#
#  ---------------------------------------------------------------------------
#  H. SVG EMBARQUÉS EN BASE64 NON RECONNUS          [priorité 2 — cas CNIG/SLYR]
#  ---------------------------------------------------------------------------
#  Fichier : bridge_style/bridgestyle/qgis/togeostyler.py
#  Fonction : _svgMarkerSymbolizer()                (~ligne 716)
#
#  Les QML produits par SLYR à partir de .lyrx ArcGIS n'utilisent pas de
#  chemins de fichiers : ils embarquent le pictogramme directement, sous la
#  forme  name="base64:PD94bWwgdmVyc2lvbj0iMS4wIi..." .
#  bridge-style traite cette valeur comme un chemin ; elle ressort telle quelle
#  dans <WellKnownName> et GeoServer n'affiche rien. Sur le corpus PLU du CNIG,
#  70 occurrences de symboles étaient ainsi perdues.
#
#  Correctif : détecter le préfixe « base64: », décoder le contenu, l'écrire
#  dans le dossier d'icônes que convert() renseigne déjà (`icons`), et
#  référencer le fichier produit. La mécanique de collecte des icônes existe
#  déjà (_usedIcons / NO_ICON) : il s'agit de l'alimenter. Voir
#  register_svg_reference() dans le présent script pour une implémentation de
#  référence (nommage par empreinte SHA-1, donc déduplication automatique).
#
#  ---------------------------------------------------------------------------
#  I. TIRETS PERSONNALISÉS IGNORÉS         [priorité 1 — 100% du corpus CNIG]
#  ---------------------------------------------------------------------------
#  Fichier : bridge_style/bridgestyle/qgis/togeostyler.py
#  Fonction : _lineSymbolizer()                     (~ligne 651)
#
#      lineStyle = _symbolProperty(sl, "line_style", ...PropertyStrokeStyle)
#      ...
#      if   lineStyle == 'dot':           symbolizer["dasharray"] = "3 5"
#      elif lineStyle == 'dash':          symbolizer["dasharray"] = "8 5"
#      elif lineStyle == 'dash dot':      symbolizer["dasharray"] = "8 5 3 5"
#      elif lineStyle == 'dash dot dot':  symbolizer["dasharray"] = "8 5 3 5 3 5"
#      elif lineStyle != "solid":         symbolizer["dasharray"] = "5 2"
#
#  Deux problèmes cumulés :
#    1. les motifs sont FIGÉS : un tiret QGIS de 4 mm suivi d'un blanc de 1 mm
#       devient « 8 5 » quelle que soit la géométrie réelle du motif ;
#    2. la propriété `customdash` (le motif réellement défini par l'auteur du
#       style) n'est JAMAIS lue. Et comme QGIS laisse `line_style` à « solid »
#       lorsque `use_custom_dash` vaut 1, aucune branche n'est atteinte : la
#       ligne ressort PLEINE, sans le moindre avertissement.
#
#  Le même schéma affecte `outlineDasharray` dans _markGraphic() (~ligne 850).
#
#  Impact mesuré : sur le corpus PLU du CNIG, les 8 fichiers utilisent
#  `use_custom_dash` (100 % — voir le panorama de la PHASE 1). Tous les tirets
#  des prescriptions linéaires seraient perdus en mode « qgis » pur.
#
#  Correctif : lire `use_custom_dash` / `customdash` / `customdash_unit`,
#  convertir en pixels via _handleUnits() et produire le dasharray exact ;
#  ne retomber sur la table figée qu'en dernier recours. Dans le présent script,
#  la réparation est faite en aval par SldPostProcessor._repair_dashes(), à
#  partir des valeurs relues dans le QML — utilisable comme oracle de test.
#
#  ---------------------------------------------------------------------------
#  MODE OPÉRATOIRE DE LA CONTRIBUTION
#  ---------------------------------------------------------------------------
#    git clone https://github.com/GeoCat/bridge-style.git
#    cd bridge-style
#    python -m venv .venv ; .\\.venv\\Scripts\\Activate.ps1      # PowerShell
#    pip install -e .
#    git checkout -b fix/qgis-hatch-angle-fidelity
#    # ... modifications ...
#    python -m pytest test/                      # suite de tests du dépôt
#    git commit -am "fix(qgis): preserve exact hatch angle via residual rotation"
#    git push origin fix/qgis-hatch-angle-fidelity
#
#  Recommandations pour maximiser les chances d'acceptation :
#    - une PR = un correctif (A, B, C... séparément) ;
#    - joindre un QML minimal de non-régression dans test/data/ et le SLD
#      attendu, en s'alignant sur les tests existants ;
#    - mentionner que les fichiers proviennent du CNIG (documents d'urbanisme
#      français), ce qui donne un cas d'usage public et vérifiable ;
#    - le projet est sous l'ombrelle GeoStyler : ouvrir d'abord une issue
#      décrivant le défaut avec captures QGIS / GeoServer côte à côte.
# ==============================================================================


# ==============================================================================
#  SECTION 8 — ORCHESTRATION / CLI
# ==============================================================================

# ------------------------------------------------------------------------------
#  Chargement du fichier de configuration
# ------------------------------------------------------------------------------

def script_dir() -> Optional[Path]:
    """
    Retourne le dossier où se trouve ce script, y compris sous exec().

    Sous « exec(compile(source, chemin, "exec")) » — la forme employée depuis la
    console Python de QGIS — la variable __file__ n'est PAS définie. En
    revanche, le chemin passé à compile() survit dans co_filename du code en
    cours d'exécution : on le récupère par introspection.
    """
    candidate = globals().get("__file__")
    if candidate:
        try:
            return Path(candidate).resolve().parent
        except Exception:                                      # noqa: BLE001
            pass
    try:
        import inspect
        frame = inspect.currentframe()
        if frame is not None:
            path = Path(frame.f_code.co_filename)
            if path.is_file():
                return path.resolve().parent
    except Exception:                                          # noqa: BLE001
        pass
    return None


def resolve_near_script(path: Path) -> Path:
    """
    Résout un chemin RELATIF par rapport au dossier du script, pas au
    répertoire courant.

    C'est indispensable depuis la console Python de QGIS : le répertoire
    courant y est imprévisible — souvent « C:\\Program Files\\QGIS 3.xx\\bin » —
    si bien qu'un « out = build » atterrirait dans les fichiers programme, ou
    échouerait faute de droits d'écriture. En ancrant les chemins relatifs sur
    l'emplacement du .py, l'ensemble reste portable : on déplace le dossier, et
    la configuration continue de fonctionner.

    Un chemin absolu est renvoyé tel quel.
    """
    candidate = Path(path).expanduser()
    if candidate.is_absolute():
        return candidate
    base = script_dir() or Path.cwd()
    return (base / candidate).resolve()


def default_output_dir() -> Path:
    """Dossier de sortie par défaut : « build » à côté du script."""
    return resolve_near_script(Path("build"))


#: Caractères interdits dans un chemin Windows (hors lettre de lecteur).
_WINDOWS_FORBIDDEN = '<>:"|?*'


def validate_output_dir(path: Path) -> Path:
    """
    Vérifie qu'un chemin de sortie est utilisable, AVANT tout téléchargement.

    Sans ce contrôle, un chemin invalide ne se manifeste qu'à la création de
    l'arborescence, après une à deux minutes de téléchargement, et sous la forme
    d'une trace Python peu parlante :
        OSError: [WinError 123] La syntaxe du nom de fichier, de répertoire ou
        de volume est incorrecte

    Le cas le plus fréquent : un exemple de la documentation recopié tel quel,
    avec son emplacement à remplacer encore entre chevrons.
    """
    raw = str(path)

    placeholder = re.search(r"[<{]\s*[^<>{}]{1,30}\s*[>}]", raw)
    if placeholder:
        raise RuntimeError(
            f"Le chemin de sortie contient encore un emplacement à remplacer : "
            f"« {placeholder.group(0)} »\n"
            f"         Chemin fourni : {raw}\n"
            f"         Remplacez-le par un vrai dossier, ou n'indiquez rien :\n"
            f"         le script utilisera alors {default_output_dir()}"
        )

    if os.name == "nt":
        tail = raw[2:] if re.match(r"^[A-Za-z]:", raw) else raw
        bad = sorted({c for c in _WINDOWS_FORBIDDEN if c in tail})
        if bad:
            raise RuntimeError(
                f"Le chemin de sortie contient des caractères interdits sous "
                f"Windows : {' '.join(bad)}\n"
                f"         Chemin fourni : {raw}"
            )

    try:
        path.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise RuntimeError(
            f"Impossible de créer le dossier de sortie.\n"
            f"         Chemin fourni : {raw}\n"
            f"         Cause : {exc}"
        ) from exc
    return path


def find_config(explicit: Optional[Path]) -> Optional[Path]:
    """
    Localise le fichier de configuration : d'abord --config, puis
    « cnig_qml2sld.ini » à côté du script, puis dans le répertoire courant.
    """
    if explicit:
        path = Path(explicit).expanduser()
        if not path.is_file():
            raise RuntimeError(f"Fichier de configuration introuvable : {path}")
        return path
    candidates = []
    here = script_dir()
    if here is not None:
        candidates.append(here / DEFAULT_CONFIG_NAME)
    candidates.append(Path.cwd() / DEFAULT_CONFIG_NAME)
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    return None


def load_config(path: Path) -> Dict[str, Any]:
    """
    Lit le .ini et retourne un dictionnaire de valeurs par défaut au format
    attendu par argparse (clés = noms de `dest`).

    Effet de bord assumé : les sections [vendor.*] et [svg] modifient
    directement les constantes globales VENDOR_DEFAULTS et SVG_SUBDIR, qui ne
    transitent pas par argparse.
    """
    import configparser
    global SVG_SUBDIR

    parser = configparser.ConfigParser(inline_comment_prefixes=(";", "#"))
    parser.optionxform = str               # préserve la casse des VendorOption
    parser.read(path, encoding="utf-8")

    defaults: Dict[str, Any] = {}

    def text(section: str, key: str) -> Optional[str]:
        value = parser.get(section, key, fallback="").strip()
        return value or None

    def flag(section: str, key: str) -> Optional[bool]:
        raw = parser.get(section, key, fallback="").strip()
        if not raw:
            return None
        return raw.lower() in ("1", "true", "yes", "on", "oui", "vrai")

    # --- [execution] --------------------------------------------------
    action = (text("execution", "action") or "").lower()
    if action == "all":
        defaults["all"] = True
    elif action == "analyze":
        defaults["analyze_only"] = True
    elif action == "benchmark":
        defaults["all"] = True
        defaults["benchmark_only"] = True
    if text("execution", "top"):
        defaults["top"] = parser.getint("execution", "top")

    # --- [source] -----------------------------------------------------
    mode = (text("source", "mode") or "github").lower()
    for key in ("repo", "branch", "github_token"):
        if text("source", key):
            defaults[key] = text("source", key)
    # subpath peut légitimement valoir "" (balayer tout le dépôt) : on ne le
    # reprend que s'il est explicitement présent dans le fichier.
    if parser.has_option("source", "subpath"):
        defaults["subpath"] = parser.get("source", "subpath").strip()
    if text("source", "cache"):
        defaults["cache"] = Path(text("source", "cache")).expanduser()
    if mode == "local":
        local = text("source", "local_source")
        if not local:
            raise RuntimeError(
                f"[source] mode = local mais « local_source » est vide "
                f"dans {path.name}."
            )
        defaults["local_source"] = Path(local).expanduser()

    # --- [sortie] -----------------------------------------------------
    if text("sortie", "out"):
        defaults["out"] = Path(text("sortie", "out")).expanduser()
    if flag("sortie", "clean") is not None:
        defaults["clean"] = flag("sortie", "clean")

    # --- [conversion] -------------------------------------------------
    backend = text("conversion", "backend")
    if backend in ("auto", "qgis", "standalone"):
        defaults["backend"] = backend
    hatch = flag("conversion", "hatch_fix")
    if hatch is not None:
        defaults["no_hatch_fix"] = not hatch
    auto = flag("conversion", "auto_install")
    if auto is not None:
        defaults["no_auto_install"] = not auto

    # --- [mbstyle] ----------------------------------------------------
    if flag("mbstyle", "enabled"):
        defaults["mbstyle"] = True
    if text("mbstyle", "base_url"):
        defaults["mbstyle_base_url"] = text("mbstyle", "base_url")
    if text("mbstyle", "workspace"):
        defaults["mbstyle_workspace"] = text("mbstyle", "workspace")

    # --- [reseau] -----------------------------------------------------
    if text("reseau", "proxy"):
        defaults["proxy"] = text("reseau", "proxy")
    if text("reseau", "bridgestyle_wheel"):
        defaults["bridgestyle_wheel"] = Path(
            text("reseau", "bridgestyle_wheel")).expanduser()

    # --- [svg] --------------------------------------------------------
    subdir = text("svg", "subdir")
    if subdir:
        SVG_SUBDIR = Path(*subdir.replace("\\", "/").strip("/").split("/"))

    # --- [geoserver] --------------------------------------------------
    if text("geoserver", "url"):
        defaults["geoserver_url"] = text("geoserver", "url")
        for key, dest in (("user", "geoserver_user"),
                          ("password", "geoserver_password"),
                          ("workspace", "geoserver_workspace")):
            if text("geoserver", key):
                defaults[dest] = text("geoserver", key)

    # --- [vendor.*] ---------------------------------------------------
    for section in parser.sections():
        if not section.startswith("vendor."):
            continue
        group = section.split(".", 1)[1]
        VENDOR_DEFAULTS[group] = {k: v.strip()
                                  for k, v in parser.items(section) if v.strip()}

    return defaults


def _refine_mbstyle_options(options: "MbStyleOptions", config_path: Path) -> None:
    """Complète les options MBStyle à partir des champs propres au fichier .ini."""
    import configparser
    parser = configparser.ConfigParser(inline_comment_prefixes=(";", "#"))
    parser.optionxform = str
    try:
        parser.read(config_path, encoding="utf-8")
    except Exception:                                          # noqa: BLE001
        return
    if not parser.has_section("mbstyle"):
        return
    get = lambda key: (parser.get("mbstyle", key, fallback="") or "").strip()   # noqa: E731
    if get("sprite_url"):
        options.sprite_url = get("sprite_url")
    if get("glyphs_url"):
        options.glyphs_url = get("glyphs_url")
    if get("sprite_size").isdigit():
        options.sprite_size = int(get("sprite_size"))
    if get("build_sprites"):
        options.build_sprites = get("build_sprites").lower() in (
            "1", "true", "yes", "on", "oui", "vrai")


def build_argparser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="cnig_qml2sld_geoserver.py",
        description="Chaîne QML CNIG -> SLD 1.0.0 GeoServer "
                    "(analyse, conversion, SVG, correctifs VendorOption).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=DEPLOY_NOTICE,
    )
    cfg = p.add_argument_group("Configuration")
    cfg.add_argument("--config", type=Path, default=None,
                     help=f"Fichier .ini de configuration. Par défaut, "
                          f"'{DEFAULT_CONFIG_NAME}' est cherché à côté du "
                          f"script puis dans le répertoire courant.")
    cfg.add_argument("--write-config", type=Path, nargs="?",
                     const=Path(DEFAULT_CONFIG_NAME), default=None,
                     metavar="FICHIER",
                     help="Écrit un fichier de configuration commenté puis "
                          "quitte. Sans valeur : "
                          f"./{DEFAULT_CONFIG_NAME}")
    cfg.add_argument("--no-config", action="store_true",
                     help="Ignore tout fichier de configuration détecté.")

    src = p.add_argument_group("Source des styles")
    src.add_argument("--repo", default=DEFAULT_REPO,
                     help=f"Dépôt GitHub (défaut : {DEFAULT_REPO})")
    src.add_argument("--branch", default=DEFAULT_BRANCH,
                     help=f"Branche (défaut : {DEFAULT_BRANCH})")
    src.add_argument("--subpath", default=DEFAULT_SUBPATH,
                     help="Sous-dossiers à balayer, séparés par des virgules. "
                          "'' balaye tout le dépôt. Le dossier Archives est "
                          f"toujours écarté. Défaut : {DEFAULT_SUBPATH}")
    src.add_argument("--local-source", type=Path, default=None,
                     help="Dossier local déjà cloné : aucun accès réseau.")
    src.add_argument("--cache", type=Path, default=Path(".cache_cnig"),
                     help="Dossier de cache des téléchargements.")
    src.add_argument("--github-token", default=None,
                     help="Jeton GitHub (ou variable GITHUB_TOKEN) pour "
                          "dépasser la limite de 60 requêtes/heure.")

    out = p.add_argument_group("Sortie")
    out.add_argument("--out", type=Path, default=None,
                     help="Dossier de sortie (contiendra styles/). "
                          "Par défaut : « build » à côté du script.")
    out.add_argument("--clean", action="store_true",
                     help="Vide le dossier styles/ avant génération.")

    run = p.add_argument_group("Exécution")
    run.add_argument("--all", action="store_true",
                     help="Exécute les 4 phases.")
    run.add_argument("--analyze-only", action="store_true",
                     help="PHASE 1 seule (aucune écriture de style).")
    run.add_argument("--benchmark-only", action="store_true",
                     help="Ne convertit que le Style Étalon et la combinaison "
                          "couvrante minimale.")
    run.add_argument("--backend", choices=("auto", "qgis", "standalone", "styleforge"),
                     default="auto",
                     help="Backend de conversion (défaut : auto). 'styleforge' "
                          "utilise styleforge_core (ni PyQGIS ni bridgestyle "
                          "requis) ; encore incomplet (pas de MBStyle, cf. "
                          "--help sur le README), donc jamais choisi par "
                          "'auto' — seulement sur demande explicite.")
    run.add_argument("--no-hatch-fix", action="store_true",
                     help="Désactive la réinjection des hachures (phase 4).")
    run.add_argument("--sprites-bridgestyle", action="store_true",
                     help="Conserve le rendu de vignettes de bridgestyle "
                          "(inutilisé par cette chaîne, et très lent).")
    run.add_argument("--no-auto-install", action="store_true",
                     help="N'installe pas bridgestyle automatiquement s'il "
                          "manque ; se contente de le signaler.")
    run.add_argument("--bridgestyle-wheel", type=Path, default=None,
                     metavar="CHEMIN",
                     help="Installe bridgestyle hors ligne depuis une roue "
                          ".whl ou un dossier de roues, sans accès à PyPI.")

    mb = p.add_argument_group("Export MBStyle (Mapbox GL Style JSON)")
    mb.add_argument("--mbstyle", action="store_true",
                    help="Produit aussi un fichier .json MBStyle par style, "
                         "et la feuille de sprites associée.")
    mb.add_argument("--no-mbstyle", action="store_true",
                    help="Désactive l'export MBStyle même si le fichier de "
                         "configuration l'active.")
    mb.add_argument("--mbstyle-base-url", default=None, metavar="URL",
                    help="Racine GeoServer pour les URL de tuiles, de sprites "
                         "et de glyphes (défaut : http://localhost:8080/geoserver).")
    mb.add_argument("--mbstyle-workspace", default=None,
                    help="Espace de travail GeoServer des couches tuilées.")

    net = p.add_argument_group("Réseau")
    net.add_argument("--proxy", default=None, metavar="URL",
                     help="Proxy d'entreprise, ex. "
                          "http://utilisateur:motdepasse@serveur:8080. "
                          "À défaut, le script lit les variables "
                          "d'environnement, la configuration réseau de QGIS "
                          "puis les paramètres proxy de Windows.")
    net.add_argument("--no-proxy", action="store_true",
                     help="Force l'accès direct, sans proxy.")
    run.add_argument("--top", type=int, default=12,
                     help="Taille du classement affiché en phase 1.")

    gs = p.add_argument_group("Publication GeoServer (optionnelle)")
    gs.add_argument("--geoserver-url", default=None,
                    help="ex. http://localhost:8080/geoserver")
    gs.add_argument("--geoserver-user", default="admin")
    gs.add_argument("--geoserver-password", default="geoserver")
    gs.add_argument("--geoserver-workspace", default=None)
    return p


def select_backend(choice: str, sprites: bool = False) -> BaseBackend:
    """Choisit le backend de conversion, avec repli automatique et explicite."""
    qgis_backend = QgisBackend(sprites_bridgestyle=sprites)
    standalone = StandaloneBackend()
    styleforge = StyleforgeBackend()

    if choice == "styleforge":
        if not styleforge.available():
            raise RuntimeError(
                "Backend 'styleforge' demandé mais styleforge_core est "
                "introuvable (ni installé, ni présent dans un dossier "
                "styleforge-core/ à côté de ce script)."
            )
        return styleforge
    if choice == "qgis":
        if not qgis_backend.available():
            raise RuntimeError(
                "Backend 'qgis' demandé mais PyQGIS est introuvable.\n"
                "Lancez le script depuis l'interpréteur QGIS, par exemple :\n"
                '  & "C:\\Program Files\\QGIS 3.34\\bin\\python-qgis.bat" '
                "cnig_qml2sld_geoserver.py --all --backend qgis"
            )
        return qgis_backend
    if choice == "standalone":
        if not standalone.available():
            raise RuntimeError("bridgestyle est introuvable : "
                               "pip install bridgestyle lxml requests")
        return standalone

    # auto
    if qgis_backend.available():
        Console.ok("Backend 'qgis' détecté (bridge-style pleine fidélité).")
        return qgis_backend
    if standalone.available():
        Console.warn(
            "PyQGIS indisponible -> bascule sur le backend 'standalone'.\n"
            "         Pour une fidélité maximale, relancez depuis le shell "
            "OSGeo4W :\n"
            '         & "C:\\Program Files\\QGIS 3.34\\bin\\python-qgis.bat" '
            "cnig_qml2sld_geoserver.py --all")
        return standalone
    raise RuntimeError("Ni PyQGIS ni bridgestyle ne sont disponibles. "
                       "Exécutez : pip install bridgestyle lxml requests")


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_argparser()

    # --- Passe 1 : on ne lit que les options liées à la configuration -----
    prelim, _ = parser.parse_known_args(argv)

    if prelim.write_config is not None:
        target = Path(prelim.write_config).expanduser()
        if target.exists():
            Console.err(f"{target} existe déjà — supprimez-le ou changez de nom.")
            return 4
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(CONFIG_TEMPLATE, encoding="utf-8", newline="\n")
        Console.ok(f"Configuration écrite : {target.resolve()}")
        Console.info("Ajustez-la, puis lancez simplement le script sans argument.")
        return 0

    config_path: Optional[Path] = None
    if not prelim.no_config:
        try:
            config_path = find_config(prelim.config)
        except Exception as exc:                           # noqa: BLE001
            Console.err(str(exc))
            return 4

    # --- Passe 2 : le fichier alimente les valeurs par défaut, puis la ----
    #     ligne de commande repasse par-dessus (précédence CLI > .ini).
    if config_path is not None:
        try:
            parser.set_defaults(**load_config(config_path))
        except Exception as exc:                           # noqa: BLE001
            Console.err(f"Configuration illisible ({config_path}) : {exc}")
            return 4

    args = parser.parse_args(argv)

    if not (args.all or args.analyze_only or args.benchmark_only):
        Console.warn("Aucune action demandée.")
        if config_path is None:
            Console.info("Deux possibilités :")
            Console.info("  1. créer un fichier de configuration :  "
                         "--write-config")
            Console.info("  2. passer par la ligne de commande :    "
                         "--all  ou  --analyze-only")
        else:
            Console.info(f"Renseignez [execution] action dans "
                         f"{config_path.name} (all | analyze | benchmark).")
        return 1

    Console.rule("CNIG / PLU — QML -> SLD 1.0.0 GeoServer", "=")
    Console.info(f"Python {sys.version.split()[0]} | lxml={_HAS_LXML} | "
                 f"requests={_HAS_REQUESTS}")
    if config_path is not None:
        Console.info(f"Configuration : {config_path}")
    else:
        Console.info("Configuration : aucune (valeurs par défaut + ligne de "
                     "commande). Créez-en une avec --write-config.")

    # ----------------------------------------- validation du dossier de sortie
    # Contrôlé AVANT le téléchargement : mieux vaut échouer en une seconde
    # qu'après deux minutes de récupération des fichiers du dépôt.
    args.out = (resolve_near_script(args.out) if args.out
                else default_output_dir())
    args.cache = resolve_near_script(args.cache)
    try:
        validate_output_dir(args.out)
    except RuntimeError as exc:
        Console.err(str(exc))
        return 6
    Console.info(f"Dossier du script  : {script_dir() or Path.cwd()}")
    Console.info(f"Dossier de sortie  : {args.out}")
    Console.info(f"Cache des sources  : {args.cache}")

    # ------------------------------------------------------ réseau / proxy
    proxy = None if args.no_proxy else detect_proxy(args.proxy)
    apply_proxy(proxy)
    Console.info(f"Réseau : {describe_proxy(proxy)}")

    # ------------------------------- bridgestyle : présent ? sinon installer
    # Le backend 'styleforge' (styleforge_core) n'a besoin ni de bridgestyle
    # ni de PyQGIS : lui imposer cette vérification (et une éventuelle
    # installation réseau) serait un obstacle inutile, pas une prudence.
    if args.backend != "styleforge":
        state, detail = ensure_bridgestyle(auto_install=not args.no_auto_install,
                                           wheel=args.bridgestyle_wheel)
        if not report_bridgestyle_state(state, detail):
            return 5

    # ------------------------------------------------ acquisition des sources
    try:
        if args.local_source:
            sources = CnigRepository.fetch_local(args.local_source)
        else:
            repo = CnigRepository(args.repo, args.branch, args.subpath,
                                  args.cache, args.github_token)
            sources = repo.fetch_remote()
    except Exception as exc:                                   # noqa: BLE001
        Console.err(str(exc))
        return 2

    # ------------------------------------------------------------- PHASE 1
    analyzer = ComplexityAnalyzer()
    reports = analyzer.analyze_all(sources.qml)
    ComplexityAnalyzer.print_report(reports, top=args.top)

    if args.analyze_only:
        args.out.mkdir(parents=True, exist_ok=True)
        write_reports(args.out, reports, [], Counter(), {})
        return 0

    # Restriction éventuelle au style étalon + combinaison couvrante
    if args.benchmark_only:
        chosen, _, _ = ComplexityAnalyzer.minimal_cover(reports, 3)
        keep = {reports[0].path} | {r.path for r in chosen}
        qml_files = [p for p in sources.qml if p in keep]
        Console.info(f"Mode --benchmark-only : {len(qml_files)} style(s) retenu(s).")
    else:
        qml_files = sources.qml

    # ------------------------------------------------------------- PHASE 3a
    tree = GeoServerTreeBuilder(args.out)
    if args.clean and tree.styles_dir.exists():
        for old in tree.styles_dir.glob("*.sld"):
            old.unlink()
        Console.info("Dossier styles/ nettoyé (*.sld supprimés).")
    tree.prepare()

    # ------------------------------------------------------------- PHASE 2
    try:
        backend = select_backend(args.backend, args.sprites_bridgestyle)
    except Exception as exc:                                   # noqa: BLE001
        Console.err(str(exc))
        return 3

    # Le backend autonome sert de filet au backend QGIS, et réciproquement.
    secours: Optional[BaseBackend] = None
    if isinstance(backend, QgisBackend):
        candidate = StandaloneBackend()
        if candidate.available():
            secours = candidate
    converter = BatchConverter(backend, secours)
    results = converter.run(qml_files, tree.styles_dir)

    # ------------------------------------------------------------- PHASE 3b
    extra_icons: List[str] = []
    for res in results:
        extra_icons.extend(res.icons)
    svg_index = tree.deploy_svg(sources.svg, extra_icons)

    # ------------------------------------------------------------- PHASE 4
    Console.step("PHASE 4 — Post-traitement XML et correctifs GeoServer")
    extractor = HintExtractor()
    post = SldPostProcessor(svg_index, VENDOR_DEFAULTS,
                            inject_hatches=not args.no_hatch_fix)

    fixed, failed = 0, 0
    for res in results:
        if not res.ok or res.target is None:
            continue
        try:
            hints, geometry = extractor.extract(res.source)
        except Exception as exc:                               # noqa: BLE001
            hints, geometry = {}, "Polygon"
            # PHASE 4 post-traite le XML SLD déjà écrit (res.sld) : ces
            # avertissements sont par construction spécifiques au SLD, pas
            # au MBStyle (voir le correctif de StyleforgeBackend.convert()
            # pour la même logique de préfixage).
            res.warnings.append(f"SLD : Indices QML non extraits : {exc}")
        try:
            final_xml = post.process(res.sld or "", hints, geometry)
            # Écriture UTF-8 SANS BOM et fins de ligne normalisées.
            with open(res.target, "w", encoding="utf-8", newline="\n") as fh:
                fh.write(final_xml)
            fixed += 1
        except Exception as exc:                               # noqa: BLE001
            failed += 1
            res.warnings.append(f"SLD : Post-traitement échoué : {exc}")
            Console.warn(f"{res.target.name} : post-traitement échoué ({exc})")

    Console.ok(f"PHASE 4 terminée : {fixed} SLD corrigés, {failed} en échec.")
    for key, value in sorted(post.stats.items(), key=lambda kv: -kv[1]):
        Console.info(f"   {key.replace('_', ' '):<45} {value:>5}")

    # ------------------------------------------------------------- PHASE 5
    mb_options = MbStyleOptions(
        enabled=bool(args.mbstyle) and not args.no_mbstyle)
    if args.mbstyle_base_url:
        mb_options.base_url = args.mbstyle_base_url
    if args.mbstyle_workspace:
        mb_options.workspace = args.mbstyle_workspace
    if config_path is not None:
        _refine_mbstyle_options(mb_options, config_path)

    if mb_options.enabled and isinstance(backend, StyleforgeBackend):
        Console.step("PHASE 5 — Export MBStyle (Mapbox GL Style JSON, styleforge_core)")
        from styleforge_core.writers.mbstyle import ecrire_mbstyle, ExpressionPivotNonEcrite

        # Résolveur de sprite pour IconSymbolizer (paramètre 'resoudre_sprite'
        # de ecrire_mbstyle(), voir sa docstring — extension du 2026-10-12) :
        # même machinerie de décodage/déduplication base64 que
        # StyleforgeBackend._resoudre_image_embarquee côté SLD
        # (register_svg_reference(), déjà matérialisée sur disque dans
        # tree.svg_dir par PHASE 3b au moment où PHASE 5 s'exécute), mais
        # enregistrée en PLUS dans SA PROPRE feuille de sprites MBStyle
        # (styleforge_sprites, une instance DÉDIÉE de la même SpriteRegistry
        # que le backend bridgestyle utilise pour --backend qgis/standalone —
        # pas un second mécanisme réinventé), puisque icon-image Mapbox
        # référence un NOM de vignette, jamais un chemin SLD.
        styleforge_sprites = SpriteRegistry(mb_options.sprite_size)

        def _resoudre_sprite_mbstyle(jeton: str) -> Optional[str]:
            # 'jeton' est soit une IMAGE (IconSymbolizer.image : chemin/URL/
            # base64, résolue comme côté SLD), soit un WELLKNOWNNAME de Mark
            # (forme simple "circle"/"square"... ou motif de hachure
            # "shape://slash"... — graphicFill/graphicStroke, voir
            # styleforge_core.writers.mbstyle._resoudre_motif_sprite) : on
            # tente d'abord en SVG, puis — SEULEMENT si ça échoue (register_svg
            # exige une extension ".svg", qu'un wellKnownName nu n'a jamais) —
            # en motif/forme simple via la MÊME SpriteRegistry que le backend
            # bridgestyle (register_shape, déjà testée et utilisée par
            # --backend qgis/standalone).
            name = register_svg_reference(jeton, "cnig_picto")
            if name is not None:
                resolu = styleforge_sprites.register_svg(name, tree.svg_dir)
                if resolu is not None:
                    return resolu
            # NOMS_MARQUEURS_QGIS_VERS_WKN (déjà utilisée en PHASE 2 pour la
            # même confusion côté SLD, cf. sa docstring ci-dessus) : un
            # wellKnownName QGIS natif comme "equilateral_triangle" a une
            # correspondance WKN EXACTE, à ne pas laisser retomber sur
            # l'approximation MarkSymbolizer->circle de _ecrire_mark_paint
            # faute d'une forme SpriteRegistry.SIMPLE_SHAPES reconnue.
            resolu = styleforge_sprites.register_shape(
                NOMS_MARQUEURS_QGIS_VERS_WKN.get(jeton, jeton)
            )
            if resolu is not None:
                return resolu
            # "ttf://<Police>#0x<hex>" (FontMarker, voir
            # styleforge_core.readers.qml._lire_font_marker) : ni un SVG, ni
            # une forme SIMPLE_SHAPES/shape://, donc toujours None à ce
            # point pour un jeton de cette famille. GeoServer sait tracer
            # cette chaîne nativement en SLD (wellknown_prefixes inclut
            # "ttf://"), mais Mapbox GL n'a aucune notion de police : on la
            # matérialise en vignette rasterisée (SpriteRegistry.
            # register_font_glyph/_draw_font_glyph), seule façon de
            # produire un PointPatternFill MBStyle sans la laisser en échec.
            return styleforge_sprites.register_font_glyph(jeton)

        produced, failed_mb = 0, 0
        for res in results:
            if not res.ok or res.pivot_style is None or res.target is None:
                continue
            target = res.target.with_suffix(".json")
            layer_name = res.target.stem
            mb_warnings: List[str] = []
            try:
                document_json = ecrire_mbstyle(
                    res.pivot_style,
                    id_source=mb_options.workspace or "cnig",
                    url_source=mb_options.tiles_url(layer_name),
                    nom_couche_source=layer_name,
                    avertissements=mb_warnings,
                    resoudre_sprite=_resoudre_sprite_mbstyle,
                    taille_sprite_px=float(mb_options.sprite_size),
                )
            except ExpressionPivotNonEcrite as exc:
                failed_mb += 1
                # Préfixe "MBStyle :" uniforme (voir _raison_echec_mbstyle,
                # qui le recherche littéralement) — avant ce correctif, cette
                # branche d'échec utilisait un préfixe différent de celui de
                # la branche succès-avec-avertissements juste en dessous
                # ("MBStyle (styleforge_core.writers.mbstyle) : ..."), ce qui
                # aurait pu faire manquer cet échec à toute recherche/analyse
                # du texte par préfixe.
                res.warnings.append(f"MBStyle : {exc}")
                Console.warn(f"{res.source.name} : MBStyle non produit ({exc})")
                continue
            # Alignement avec la convention déjà utilisée par les backends
            # qgis/standalone (PHASE 5 ci-dessous) : une source vectorielle
            # tuilée s'exprime ici via "tiles" (gabarit {z}/{x}/{y} déjà
            # produit par mb_options.tiles_url), pas via "url" (endpoint
            # TileJSON) — ecrire_mbstyle() est volontairement agnostique de
            # cette convention (paramètre url_source, voir sa docstring), on
            # la fixe donc ici plutôt que dans styleforge_core.
            obj = json.loads(document_json)
            source = obj.get("sources", {}).get(mb_options.workspace or "cnig")
            if isinstance(source, dict) and "url" in source:
                source["tiles"] = [source.pop("url")]
            obj["sprite"] = mb_options.resolved_sprite_url()
            obj["glyphs"] = mb_options.resolved_glyphs_url()
            target.write_text(
                json.dumps(obj, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8", newline="\n",
            )
            res.warnings.extend(f"MBStyle : {w}" for w in mb_warnings)
            res.mbstyle = target
            produced += 1
        Console.ok(f"{produced} fichier(s) MBStyle écrit(s), {failed_mb} échec(s).")
        if failed_mb:
            Console.info(
                "   (voir la docstring de styleforge_core.writers.mbstyle, section "
                "\"EXTENSION COMPATIBILITÉ MAXIMALE\", pour la portée précise — "
                "Fill/Line/Mark(circle ou approximé)/Text/Icon et Rule.filter sont "
                "couverts ; RasterSymbolizer et Rule.elseRule restent hors de portée "
                "pour des raisons structurelles, pas un oubli de câblage.)"
            )
        if mb_options.build_sprites:
            report = styleforge_sprites.build(tree.styles_dir, pump_ui=pump_ui)
            if report.get("images"):
                Console.ok(f"Feuille de sprites styleforge générée : "
                           f"{report['vignettes']} vignette(s) "
                           f"(sprite.png, sprite@2x.png et leurs index).")
            elif report.get("vignettes"):
                Console.warn("Feuille de sprites styleforge non générée (Qt indisponible).")
            for warning in styleforge_sprites.warnings[:5]:
                Console.warn(f"   {warning}")
    if mb_options.enabled and not isinstance(backend, StyleforgeBackend):
        Console.step("PHASE 5 — Export MBStyle (Mapbox GL Style JSON)")
        exporter = MbStyleExporter(mb_options, tree.svg_dir)
        produced, failed_mb = 0, 0
        for res in results:
            if not res.ok or res.geostyler is None or res.target is None:
                continue
            target = res.target.with_suffix(".json")
            ok, warnings = exporter.export(res.geostyler, res.target.stem,
                                           target)
            res.warnings.extend(f"MBStyle : {w}" for w in warnings)
            if ok:
                res.mbstyle = target
                produced += 1
            else:
                failed_mb += 1
                Console.warn(f"{res.source.name} : {warnings[0] if warnings else 'échec'}")
        Console.ok(f"{produced} fichier(s) MBStyle écrit(s), {failed_mb} échec(s).")

        if mb_options.build_sprites:
            report = exporter.sprites.build(tree.styles_dir, pump_ui=pump_ui)
            if report.get("images"):
                Console.ok(f"Feuille de sprites générée : "
                           f"{report['vignettes']} vignettes "
                           f"(sprite.png, sprite@2x.png et leurs index).")
            elif report.get("vignettes"):
                Console.warn("Feuille de sprites non générée (Qt indisponible).")
            for warning in exporter.sprites.warnings[:5]:
                Console.info(f"   {warning}")
        for key, value in sorted(exporter.stats.items(), key=lambda kv: -kv[1]):
            Console.info(f"   {key.replace('_', ' '):<45} {value:>5}")
        if produced:
            Console.raw("")
            Console.rule("TROIS URL A VERIFIER DANS LES .json PRODUITS", "-")
            Console.info("Elles sont écrites en dur et pointent par défaut vers "
                         "une instance locale.")
            Console.info("Adaptez-les à votre GeoServer, dans le .ini avant "
                         "génération ou dans les JSON ensuite :")
            Console.raw("")
            Console.raw(f'   "tiles"  : {mb_options.tiles_url("<couche>")[:74]}...')
            Console.raw(f'   "sprite" : {mb_options.resolved_sprite_url()}')
            Console.raw(f'   "glyphs" : {mb_options.resolved_glyphs_url()}')
            Console.raw("")
            Console.info("Section [mbstyle] du fichier .ini : base_url, "
                         "workspace, sprite_url, glyphs_url.")
            Console.rule("", "-")

    # ------------------------------------------------------------- PHASE 6
    auditeur = GeoServerAuditor(tree.styles_dir)
    auditeur.audit([r.target for r in results if r.ok and r.target])
    conforme = auditeur.afficher()

    # --------------------------------------------------------- publication
    if args.geoserver_url:
        Console.step(f"Publication REST vers {args.geoserver_url}")
        publisher = GeoServerPublisher(args.geoserver_url, args.geoserver_user,
                                       args.geoserver_password,
                                       args.geoserver_workspace)
        for res in results:
            if res.ok and res.target:
                ok, msg = publisher.publish(res.target)
                Console.raw(f"   {'OK  ' if ok else 'ECHEC'} {res.target.name} : {msg}")

    # ------------------------------------------------------------- rapports
    write_reports(args.out, reports, results, post.stats, svg_index,
                  auditeur.problemes, auditeur.extensions, mb_options.enabled)
    (args.out / "NOTICE_DEPLOIEMENT.txt").write_text(DEPLOY_NOTICE,
                                                     encoding="utf-8")

    if isinstance(backend, QgisBackend):
        backend.shutdown()

    Console.rule("TERMINÉ", "=")
    Console.ok(f"Arborescence prête : {tree.styles_dir}")
    Console.info("Étape suivante : voir NOTICE_DEPLOIEMENT.txt")
    # Code 7 : les fichiers sont écrits, mais l'audit a relevé des défauts.
    # Utile en intégration continue pour bloquer une livraison non conforme.
    return 0 if conforme else 7


# ------------------------------------------------------------------------------
#  LANCEMENT DEPUIS LA CONSOLE PYTHON DE QGIS
# ------------------------------------------------------------------------------
#  Dans QGIS : Extensions > Console Python, puis (chemins à adapter) :
#
#      import importlib.util, sys
#      chemin = r"C:\Users\xthauvin\Documents\Styles\cnig_qml2sld_geoserver.py"
#      spec = importlib.util.spec_from_file_location("cnig_qml2sld", chemin)
#      cnig = importlib.util.module_from_spec(spec)
#      sys.modules[spec.name] = cnig      # <-- INDISPENSABLE, voir ci-dessous
#      spec.loader.exec_module(cnig)
#
#  La ligne sys.modules[...] n'est pas facultative : sans elle, le module
#  @dataclass ne retrouve pas son espace de noms et l'exécution s'arrête sur
#      AttributeError: 'NoneType' object has no attribute '__dict__'
#
#      cnig.main(["--all",
#                 "--backend", "qgis",
#                 "--out", r"C:\Users\xthauvin\Documents\Styles\build"])
#
#  PRÉALABLE : bridgestyle doit être installé DANS le Python de QGIS.
#  Depuis la console Python de QGIS, une seule fois :
#
#      import os, sys, subprocess
#      py = os.path.join(os.path.dirname(sys.executable), "python.exe")
#      subprocess.check_call([py, "-m", "pip", "install",
#                             "bridgestyle", "lxml", "requests"])
#
#  ATTENTION : dans la console QGIS, sys.executable vaut « qgis-bin.exe » et non
#  « python.exe » — d'où la reconstruction du chemin ci-dessus. Redémarrer QGIS
#  après l'installation pour que l'import soit pris en compte.
#  (lxml et requests sont généralement déjà fournis avec QGIS.)
#
#  Le script détecte automatiquement la QgsApplication déjà en cours et ne
#  ferme JAMAIS votre QGIS ; le backend « qgis » (pleine fidélité) est alors
#  sélectionné d'office.
# ------------------------------------------------------------------------------

def run_in_qgis_console(out_dir: Optional[str] = None,
                        local_source: Optional[str] = None,
                        extra_args: Optional[Sequence[str]] = None,
                        proxy: Optional[str] = None,
                        wheel: Optional[str] = None,
                        mbstyle: bool = True,
                        workspace: Optional[str] = None) -> int:
    """
    Raccourci pour la console Python de QGIS.

        cnig.run_in_qgis_console()                       # SLD + MBStyle
        cnig.run_in_qgis_console(workspace="cnig")       # espace GeoServer
        cnig.run_in_qgis_console(mbstyle=False)          # SLD uniquement
        cnig.run_in_qgis_console(r"D:\\sorties\\cnig")      # dossier choisi

    Vérifie d'abord que bridgestyle est disponible dans le Python de QGIS et
    l'installe au besoin. Retourne 5 si un redémarrage de QGIS est requis.
    """
    Console.rule("QGIS VA PARAITRE FIGE PENDANT LE TRAITEMENT", "-")
    Console.info("C'est normal : la console Python s'exécute dans le thread de "
                 "l'interface,")
    Console.info("donc QGIS ne répond plus tant que la conversion tourne "
                 "(quelques minutes")
    Console.info("sur le corpus complet). L'avancement continue de s'afficher.")
    Console.info("")
    Console.info("Pour NE PAS bloquer QGIS, lancez plutôt depuis le shell "
                 "OSGeo4W :")
    Console.info('   & "C:\\Program Files\\QGIS 3.40.4\\bin\\python-qgis.bat" ^')
    Console.info("       cnig_qml2sld_geoserver.py --all --mbstyle")
    Console.info("Même interpréteur, même fidélité, mais hors de l'interface.")
    Console.info("")
    Console.info("Essai rapide depuis la console : "
                 "run_in_qgis_console(extra_args=[\"--benchmark-only\"])")
    Console.rule("", "-")

    apply_proxy(detect_proxy(proxy))
    state, detail = ensure_bridgestyle(auto_install=True,
                                       wheel=Path(wheel) if wheel else None)
    if not report_bridgestyle_state(state, detail):
        return 5

    # Sans argument, on NE FORCE PAS --out : le fichier de configuration garde
    # la main, et à défaut main() retombe sur « build » à côté du script.
    argv: List[str] = ["--all", "--backend", "qgis"]
    # L'export MBStyle est actif par défaut depuis la console : il ne coûte
    # qu'une réutilisation du pivot GeoStyler déjà calculé pour le SLD.
    # mbstyle=False pour ne produire que les SLD.
    argv.append("--mbstyle" if mbstyle else "--no-mbstyle")
    if workspace:
        argv += ["--mbstyle-workspace", workspace]
    if out_dir:
        target = Path(out_dir).expanduser()
        try:
            validate_output_dir(target)
        except RuntimeError as exc:
            Console.err(str(exc))
            return 6
        argv += ["--out", str(target)]
    if proxy:
        argv += ["--proxy", proxy]
    if wheel:
        argv += ["--bridgestyle-wheel", str(wheel)]
    if local_source:
        argv += ["--local-source", local_source]
    argv += list(extra_args or [])

    # Curseur d'attente : le seul retour visuel possible tant que la boucle
    # d'événements est monopolisée par le traitement.
    restore = None
    try:
        from qgis.PyQt.QtWidgets import QApplication          # type: ignore
        from qgis.PyQt.QtCore import Qt                       # type: ignore
        QApplication.setOverrideCursor(Qt.WaitCursor)
        restore = QApplication.restoreOverrideCursor
    except Exception:                                          # noqa: BLE001
        pass
    try:
        return main(argv)
    finally:
        if restore is not None:
            try:
                restore()
            except Exception:                                  # noqa: BLE001
                pass


def _inside_interactive_qgis() -> bool:
    """Vrai si l'on tourne dans une session QGIS avec interface (console Python)."""
    try:
        from qgis.core import QgsApplication                     # type: ignore
        return QgsApplication.instance() is not None
    except Exception:                                            # noqa: BLE001
        return False


def _print_console_banner() -> None:
    """
    Accusé de réception affiché lors d'un chargement dans la console QGIS.

    Il confirme que le script est chargé — sans cela, un exec() réussi ne produit
    AUCUNE sortie et rien ne distingue le succès d'un échec silencieux — et il
    fait le point sur les dépendances, au moment précis où c'est utile.
    """
    print("=" * 78)
    print(" Chaîne CNIG QML -> SLD 1.0.0 GeoServer — script CHARGÉ.")
    print("=" * 78)

    # --- réseau : réutiliser le proxy de QGIS s'il est configuré ------
    proxy = detect_proxy()
    apply_proxy(proxy)
    print(f"   Réseau      : {describe_proxy(proxy)}", flush=True)

    # --- bridgestyle : vérification, et installation si nécessaire ----
    state, detail = ensure_bridgestyle(auto_install=True)
    ready = report_bridgestyle_state(state, detail)

    print(f"   lxml        : {'OK' if _HAS_LXML else 'absent (repli xml.etree)'}")
    print(f"   requests    : {'OK' if _HAS_REQUESTS else 'absent (repli urllib)'}")
    if SLD_SHIM_FORCED:
        print("   PyQGIS      : présent, mais incompatible avec bridgestyle "
              "-> backend « standalone »", flush=True)
    else:
        print("   PyQGIS      : OK — backend « qgis » (pleine fidélité) sélectionné",
              flush=True)

    if not ready:
        print("=" * 78)
        return

    # --- configuration détectée -------------------------------------
    try:
        found = find_config(None)
    except Exception:                                          # noqa: BLE001
        found = None
    print(f"\n   Configuration : {found if found else 'aucune (--write-config pour en créer une)'}")

    print("\n Lancer la chaîne complète — sans argument, la sortie va dans :")
    print(f"   {default_output_dir()}\n")
    print("     run_in_qgis_console()        # SLD + MBStyle + sprites")
    print("\n Variantes :\n")
    print('     # en précisant l\'espace de travail GeoServer (URL du MBStyle)')
    print('     run_in_qgis_console(workspace="cnig")')
    print()
    print('     # SLD uniquement, sans export MBStyle')
    print('     run_in_qgis_console(mbstyle=False)')
    print()
    print('     # dossier de sortie choisi')
    print('     run_in_qgis_console(r"D:\\sorties\\cnig")')
    print()
    print('     # uniquement le style étalon et la combinaison couvrante minimale')
    print('     run_in_qgis_console(extra_args=["--benchmark-only"])')
    print()
    print('     # à partir d\'un clone local, sans accès réseau')
    print('     run_in_qgis_console(local_source=r"D:\\git\\DDU-SG5-SYMBOLISATION\\PLU")')
    print()
    print('     # poste derrière un proxy d\'entreprise')
    print('     run_in_qgis_console(proxy="http://utilisateur:motdepasse@serveur:8080")')
    print()
    print('     # poste sans accès à PyPI : roues récupérées au préalable')
    print('     run_in_qgis_console(wheel=r"D:\\paquets")')
    print()
    print('     # en désignant explicitement un fichier de configuration')
    print('     run_in_qgis_console(extra_args=["--config", r"D:\\cnig_qml2sld.ini"])')
    print("=" * 78)


# ATTENTION — ne PAS conditionner ce bloc au seul `__name__ == "__main__"`.
# La console Python de QGIS exécute le code dans un espace de noms dont le
# __name__ n'est pas « __main__ » : un exec(compile(...)) réussi ne produisait
# alors STRICTEMENT AUCUNE sortie, et rien ne permettait de distinguer un
# chargement réussi d'un échec silencieux. On teste donc d'abord la présence
# d'une session QGIS interactive, indépendamment de __name__.
if _inside_interactive_qgis():
    _print_console_banner()
elif __name__ == "__main__":
    sys.exit(main())
