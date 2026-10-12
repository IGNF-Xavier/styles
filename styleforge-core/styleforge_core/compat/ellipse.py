# -*- coding: utf-8 -*-
"""
styleforge_core.compat.ellipse — Décision EllipseMarker.

Le problème
-----------
QGIS a un type de couche de symbole marqueur nommé "EllipseMarker" : un
marqueur défini par une LARGEUR et une HAUTEUR indépendantes
(``symbol_width`` / ``symbol_height`` dans le QML — cf.
corpus/symbol_layers/Marker/EllipseMarker*.qml), au-dessus d'une forme de
base (``symbol_name`` : circle, square, rectangle, triangle, diamond,
cross, arrow...). Quand largeur != hauteur sur la forme "circle", le
résultat est une véritable ellipse.

Le vocabulaire WellKnownName de la norme OGC Symbology Encoding (et donc de
SLD, et donc de GeoServer qui l'implémente) est limité à :
square, circle, triangle, star, cross, x — il n'existe PAS de primitive
"ellipse". Un futur écrivain SLD/MBStyle ne peut donc pas restituer une
EllipseMarker QGIS à l'identique : c'est une limite de la norme cible, pas
un défaut de ce projet.

La décision (proposée par l'utilisateur, retenue)
--------------------------------------------------
Approximer toute EllipseMarker par un MarkSymbolizer WellKnownName="circle"
(forme de base circle/semi_circle) ou "square" (forme de base square/
rectangle, ajouté le 2026-10-12 — voir "Extension" ci-dessous) dont le
rayon est dérivé de symbol_width/symbol_height. On calcule ce rayon à
partir de ces deux propriétés plutôt que de la propriété QGIS "size",
parce que le niveau 2 (rapport rapport_niveaux_2_3_4.docx, §4) a mesuré que
"size" est incohérente sur les variantes EllipseMarker du corpus (une valeur
lue par pivot_properties.py différente de la valeur sérialisée par l'oracle
PyQGIS sur 3 fixtures/4) : symbol_width et symbol_height, eux, sont fiables
et toujours présents.

Portée de la décision
----------------------
Cette approximation couvre les cas symbol_name in {circle, semi_circle,
square, rectangle}. Une EllipseMarker dont la forme de base est différente
(triangle, cross, diamond, arrow...) combine DEUX écarts avec le
vocabulaire WellKnownName standard (la forme de base ET l'ellipticité) ;
ce cas est signalé comme hors périmètre par ``supporte()`` plutôt que
traité silencieusement — mieux vaut un signal explicite qu'une
approximation trompeuse.

Extension square/rectangle (2026-10-12)
-----------------------------------------
Motivée par deux fichiers réels du corpus (plu_inf_s.qml, psmv_inf_s.qml :
EllipseMarker symbol_name="rectangle", 9.96 x 6 Point) bloquant leur
conversion complète, et par une consigne explicite de maximiser la
compatibilité du corpus plutôt que de laisser un échec dur quand une
approximation raisonnable existe. square/rectangle partagent le
WellKnownName "square" (aucun "rectangle" dans le vocabulaire OGC SE à 6
noms) : la perte d'ellipticité (largeur != hauteur) reste signalée via
``ApproximationEllipse.perte``, exactement comme pour circle/semi_circle —
ce n'est pas un traitement silencieux, juste un périmètre élargi à une
seconde paire de formes où l'approximation reste honnête (un seul écart,
la forme de base étant déjà celle d'un quadrilatère à angles droits,
contrairement à triangle/cross/diamond/arrow qui restent hors périmètre).

Évolutivité
-----------
La stratégie de calcul du rayon équivalent est un PARAMÈTRE
(``StrategieApproximation``), pas une formule figée : un projet qui
préfère préserver l'aire, ou la plus grande dimension (rendu plus visible),
ou la plus petite (rendu plus prudent), choisit sans toucher au code.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Literal

#: Les stratégies de réduction (largeur, hauteur) -> rayon disponibles.
#: "moyenne"    : rayon = (largeur + hauteur) / 4  (diamètre moyen / 2)
#: "aire_egale" : rayon du cercle de même aire que l'ellipse
#: "max"        : rayon = max(largeur, hauteur) / 2  (l'ellipse tient DANS le cercle)
#: "min"        : rayon = min(largeur, hauteur) / 2  (le cercle tient DANS l'ellipse)
#: "largeur"    : rayon = largeur / 2
#: "hauteur"    : rayon = hauteur / 2
StrategieApproximation = Literal[
    "moyenne", "aire_egale", "max", "min", "largeur", "hauteur"
]

STRATEGIE_PAR_DEFAUT: StrategieApproximation = "moyenne"

#: Formes de base QGIS pour lesquelles une approximation directe a un sens :
#: circle/semi_circle -> cercle (décision d'origine, cf. docstring du
#: module), square/rectangle -> carré (ajouté le 2026-10-12, sur demande
#: explicite de maximiser la couverture du corpus réel plutôt que de
#: laisser échouer la conversion — cf. rapport d'accompagnement). Les
#: autres (triangle, cross, diamond, arrow, ...) restent hors périmètre :
#: pas de WellKnownName OGC assez proche pour que l'approximation reste
#: honnête plutôt que trompeuse.
FORMES_BASE_SUPPORTEES = frozenset({"circle", "semi_circle", "square", "rectangle"})

#: forme de base QGIS -> WellKnownName OGC le plus proche. square/rectangle
#: partagent "square" (un rectangle QGIS largeur != hauteur reste approximé
#: par un carré : AUCUN WellKnownName "rectangle" n'existe dans le
#: vocabulaire OGC SE à 6 noms — square/circle/triangle/star/cross/x — donc
#: la perte d'ellipticité déjà actée pour circle/semi_circle se retrouve
#: identique ici pour square/rectangle, signalée de la même façon).
_FORME_VERS_WKN: dict[str, Literal["circle", "square"]] = {
    "circle": "circle", "semi_circle": "circle",
    "square": "square", "rectangle": "square",
}


@dataclass(frozen=True)
class ApproximationEllipse:
    """Résultat de l'approximation : ce que le futur écrivain SLD/MBStyle
    posera comme WellKnownName + radius sur le MarkSymbolizer du pivot."""

    well_known_name: Literal["circle", "square"]
    radius: float
    strategie: StrategieApproximation
    perte: bool  # True si largeur != hauteur (approximation avec perte réelle)


def supporte(symbol_name: str) -> bool:
    """Indique si `symbol_name` (la forme de base QGIS de l'EllipseMarker)
    entre dans le périmètre d'une de ces décisions d'approximation.
    Voir "Portée de la décision" dans la docstring du module."""
    return symbol_name in FORMES_BASE_SUPPORTEES


def rayon_cercle_equivalent(
    largeur: float,
    hauteur: float,
    strategie: StrategieApproximation = STRATEGIE_PAR_DEFAUT,
) -> float:
    """Calcule le rayon du cercle approximant une ellipse largeur x hauteur,
    selon la stratégie choisie (paramètre, jamais figée en dur — voir
    "Évolutivité" dans la docstring du module).

    largeur et hauteur sont dans la même unité (celle du QML source,
    typiquement symbol_width_unit == symbol_height_unit chez QGIS) ; le
    rayon retourné est dans cette même unité, à convertir si besoin par
    l'appelant."""
    if largeur < 0 or hauteur < 0:
        raise ValueError(
            f"largeur et hauteur doivent être positives ou nulles "
            f"(reçu largeur={largeur!r}, hauteur={hauteur!r})"
        )

    if strategie == "moyenne":
        return (largeur + hauteur) / 4
    if strategie == "aire_egale":
        # aire ellipse = pi * (largeur/2) * (hauteur/2)
        # aire cercle  = pi * rayon^2
        # => rayon = sqrt((largeur/2) * (hauteur/2))
        return math.sqrt((largeur / 2) * (hauteur / 2))
    if strategie == "max":
        return max(largeur, hauteur) / 2
    if strategie == "min":
        return min(largeur, hauteur) / 2
    if strategie == "largeur":
        return largeur / 2
    if strategie == "hauteur":
        return hauteur / 2

    raise ValueError(
        f"Stratégie d'approximation EllipseMarker inconnue : {strategie!r} "
        f"(valeurs valides : moyenne, aire_egale, max, min, largeur, hauteur)"
    )


def approximer(
    symbol_name: str,
    largeur: float,
    hauteur: float,
    strategie: StrategieApproximation = STRATEGIE_PAR_DEFAUT,
) -> ApproximationEllipse:
    """Point d'entrée destiné au futur lecteur QML (styleforge_core.readers.qml) :
    à partir des propriétés brutes d'une couche de symbole EllipseMarker,
    produit ce qu'il faut poser sur le MarkSymbolizer du pivot.

    Lève ValueError si `symbol_name` est une forme de base hors périmètre
    (cf. `supporte`) — le lecteur doit alors le traiter comme un cas non
    couvert plutôt que produire un cercle ou un carré trompeur."""
    if not supporte(symbol_name):
        raise ValueError(
            f"EllipseMarker de forme de base {symbol_name!r} hors périmètre des "
            f"décisions d'approximation retenues (formes supportées : "
            f"{sorted(FORMES_BASE_SUPPORTEES)}). Ce cas combine un écart de "
            f"forme ET d'ellipticité avec le vocabulaire WellKnownName standard "
            f"— à traiter séparément plutôt que par une approximation trompeuse."
        )
    # rayon_cercle_equivalent() calcule un demi-côté tout aussi valide pour
    # un carré que pour un cercle : c'est la même grandeur pivot (radius,
    # demi-taille de la boîte englobante du marqueur) quel que soit le
    # WellKnownName final — le nom de la fonction (hérité de la décision
    # d'origine, circle/semi_circle) ne limite pas son usage ici.
    rayon = rayon_cercle_equivalent(largeur, hauteur, strategie)
    return ApproximationEllipse(
        well_known_name=_FORME_VERS_WKN[symbol_name],
        radius=rayon,
        strategie=strategie,
        perte=(largeur != hauteur),
    )
