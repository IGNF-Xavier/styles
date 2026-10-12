# -*- coding: utf-8 -*-
"""
styleforge_core.pivot — Le pivot typé de la bibliothèque, aligné sur le
schéma JSON publié par geostyler-style (actuellement 13.0.0 — voir
pivot/SOURCE.md pour la provenance exacte et regenerer_pivot.py pour changer
de version).

Ce paquet est volontairement scindé en deux :
  - _genere.py     : ENTIÈREMENT généré par datamodel-codegen depuis le
                      schema.json de geostyler-style. Ne JAMAIS l'éditer à
                      la main — toute correction s'y perdrait à la
                      prochaine régénération. 97 classes pydantic.
  - __init__.py     (ce fichier) : la surface publique, stable, que le
                      reste de la bibliothèque importe. C'est ICI que
                      vivent les alias (Style plutôt que le nom générique
                      "Model" que datamodel-codegen a donné au modèle
                      racine, faute de titre dans le schéma), les
                      validateurs additionnels, et les fonctions de
                      confort — jamais dans le fichier généré.

Pourquoi un pivot TYPÉ plutôt que le dict Python libre du script CNIG :
rien n'empêchait un lecteur d'écrire une clé qu'aucun écrivain ne lira
jamais (le défaut constaté chez bridge-style : graphicFillDistance écrit,
graphicFillMargin lu). Un modèle pydantic rend cette classe d'erreur
détectable à l'exécution, avant même d'atteindre l'écrivain SLD/MBStyle.
"""
from __future__ import annotations

import os
import sys

# Le schéma geostyler-style est génuinement récursif (une expression peut
# contenir des expressions ; un Filter peut contenir des Filter ; §voir
# regenerer_pivot.py). En résoudre les annotations différées (PEP 563)
# demande à typing._eval_type une profondeur d'appel bien supérieure à la
# limite par défaut de CPython (1000) : la construction des modèles pydantic
# lève RecursionError à l'import sans cette augmentation. La valeur est un
# paramètre (variable d'environnement), pas une constante close en dur, pour
# rester ajustable si le schéma continue de se complexifier sans avoir à
# modifier ce fichier.
_LIMITE_RECURSION = int(os.environ.get("STYLEFORGE_PIVOT_RECURSION_LIMIT", "10000"))
if sys.getrecursionlimit() < _LIMITE_RECURSION:
    sys.setrecursionlimit(_LIMITE_RECURSION)

from . import _genere as _g

# --------------------------------------------------------------- surface publique
#: La racine d'un style GeoStyler. Nommée "Model" par le générateur faute de
#: titre explicite dans le schéma JSON racine — "Style" est le nom qui a un
#: sens pour qui lit le code appelant.
Style = _g.Model

Rule = _g.Rule
Symbolizer = _g.Symbolizer

MarkSymbolizer = _g.MarkSymbolizer
IconSymbolizer = _g.IconSymbolizer
TextSymbolizer = _g.TextSymbolizer
FillSymbolizer = _g.FillSymbolizer
LineSymbolizer = _g.LineSymbolizer
RasterSymbolizer = _g.RasterSymbolizer

#: Un Filter geostyler-style 13.x EST une expression (Fproperty, Fcase, "==", "&&"...),
#: pas un type séparé : c'est le même langage d'expression que celui qui pilote une
#: propriété de symbolizer (cf. les variantes "expression" du corpus, niveau 1/§6.3).
Filter = _g.Filter

#: Sous-espace de confort pour les nœuds d'expression les plus utilisés par le
#: lecteur QML (StandaloneBackend._filter du script CNIG n'en couvre aujourd'hui
#: que deux : lower/string_to_array — cf. rapport niveau 3). Les 90+ autres
#: définitions du schéma restent accessibles via `_genere` pour qui en a besoin.
class expressions:  # noqa: N801 — regroupement délibéré, pas une classe métier
    Fproperty = _g.Fproperty
    Fcase = _g.Fcase
    Fall = _g.Fall
    Fany = _g.Fany
    Fnot = _g.Fnot
    FequalTo = _g.FequalTo
    FnotEqualTo = _g.FnotEqualTo
    FgreaterThan = _g.FgreaterThan
    FgreaterThanOrEqualTo = _g.FgreaterThanOrEqualTo
    FlessThan = _g.FlessThan
    FlessThanOrEqualTo = _g.FlessThanOrEqualTo
    Fin = _g.Fin


def valider_style(donnees: dict) -> Style:
    """
    Point d'entrée unique de validation d'un pivot brut (dict, tel que produit
    par un lecteur ou par bridgestyle) contre le pivot typé. Lève
    pydantic.ValidationError avec un message précis (chemin de la clé fautive
    inclus) plutôt que de laisser une clé erronée voyager silencieusement
    jusqu'à l'écrivain SLD/MBStyle.
    """
    return Style.model_validate(donnees)


def dumper_style(style: Style) -> dict:
    """Sérialise un Style typé vers le dict JSON geostyler-style standard
    (clés omises quand leur valeur est None, pour rester un pivot minimal
    et lisible plutôt que rempli de null)."""
    return style.model_dump(mode="json", exclude_none=True, by_alias=True)


__all__ = [
    "Style", "Rule", "Symbolizer",
    "MarkSymbolizer", "IconSymbolizer", "TextSymbolizer",
    "FillSymbolizer", "LineSymbolizer", "RasterSymbolizer",
    "Filter", "expressions",
    "valider_style", "dumper_style",
]
