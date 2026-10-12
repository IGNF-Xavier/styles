#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
styleforge_core.writers.mbstyle — Écrivain GÉNÉRAL (mais délibérément TRÈS
BORNÉ pour cette toute première itération) du pivot geostyler-style vers un
document Mapbox GL "Style Spec" (JSON, version 8). Deux oracles de
vérification pour ce chantier (choix explicite de l'utilisateur, voir la
discussion qui a précédé ce module) :
  1. QgsMapBoxGlStyleConverter (PyQGIS) — convertit une string JSON Mapbox en
     QgsVectorTileBasicRenderer SANS nécessiter de vrai service de tuiles
     vectorielles (TMS) : c'est l'oracle PRINCIPAL, même statut que
     QgsVectorLayer.loadSldStyle() pour l'écrivain SLD — jamais une
     dépendance d'exécution de ce module, seulement un outil de test.
  2. geostyler-cli (npm, wrapper autour de geostyler-mapbox-parser /
     geostyler-style) — oracle SECONDAIRE, utilisé pour corroborer
     indépendamment les conventions mapbox <-> pivot (une implémentation
     tierce, pas QGIS). Risque de décalage de version identifié et accepté :
     geostyler-cli 5.0.4 embarque geostyler-style ^10.5.0, alors que le pivot
     de ce projet est en 13.0.0 — un signal de geostyler-cli n'est retenu que
     lorsqu'il porte sur une convention Mapbox de base (peu susceptible
     d'avoir changé entre 10.5.0 et 13.0.0), jamais sur la forme exacte d'un
     champ pivot récent, et toujours croisé avec l'oracle QGIS avant d'être
     inscrit dans ce module.

Portée de CETTE itération ("cœur minimal d'abord", même discipline que
l'écrivain SLD) — délibérément la plus petite possible pour valider
l'orchestration de bout en bout avant d'élargir :
  - Style -> {"version": 8, "sources": {...UNE source vector...}, "layers":
    [...]}, UNE couche Mapbox PAR Rule du pivot, dans l'ordre. id_source,
    url_source et nom_couche_source (le "source-layer" Mapbox) sont des
    PARAMÈTRES de ecrire_mbstyle() — le pivot lui-même ne contient aucune
    information de source/tuiles (c'est un choix de contexte de rendu, pas
    de style), donc ce ne peut PAS être une valeur supposée (principe
    évolutif : tout ce qui est un choix doit être un paramètre).
  - Rule.filter : PAS ENCORE ÉCRIT. Toute Rule dont 'filter' est renseigné
    (donc non None) lève ExpressionPivotNonEcrite — la syntaxe des
    expressions de filtre Mapbox (["==", ["get","champ"], valeur] ou la
    forme "legacy" ["==","champ",valeur]) n'a pas encore été vérifiée contre
    l'oracle QGIS pour cette itération, donc pas écrite plutôt
    qu'approximée. Rule.elseRule : idem, pas encore traité.
  - UN SEUL symbolizer par Rule, de type Fill uniquement. Une Rule avec 0,
    2+ symbolizers, ou un symbolizer d'un autre kind, lève
    ExpressionPivotNonEcrite (pas d'approximation sur laquelle des couches
    empiler ni sur l'ordre).
  - FillSymbolizer -> Mapbox layer type "fill", propriétés "paint" :
      * color (hex "#rrggbb") -> fill-color, EN LITTÉRAL hex si ni
        fillOpacity ni un canal alpha ne doit être encodé, sinon
        "rgba(r,g,b,fillOpacity)" (fillOpacity comme FLOTTANT 0..1, syntaxe
        CSS rgba() standard prise en charge par la spec Mapbox — PAS besoin
        de la convertir en entier 0..255, cette conversion est faite côté
        QGIS à la LECTURE, pas une convention à reproduire à l'écriture :
        vérifié contre l'oracle avant l'interruption de connexion, voir plus
        bas).
      * opacity (le champ pivot "opacity", PAS "fillOpacity" — les deux sont
        des champs DISTINCTS du schéma FillSymbolizer, cf.
        styleforge_core/pivot/_genere.py) -> fill-opacity. VÉRIFIÉ contre
        l'oracle QGIS (QgsMapBoxGlStyleConverter) : fill-opacity pilote
        symbol.opacity() (l'opacité GLOBALE du symbole QGIS, remplissage ET
        contour), INDÉPENDAMMENT et de façon CUMULATIVE avec un canal alpha
        éventuellement encodé dans fill-color/fill-outline-color (testé
        combiné : fill-color=rgba(255,0,0,0.5) + fill-outline-color=
        rgba(0,0,0,0.3) + fill-opacity=0.8 -> symbol.opacity()==0.8 ET
        color alpha==128 (0.5) ET outline_color alpha==77 (0.3), aucune
        des trois valeurs n'a contaminé les deux autres). C'est cette
        distinction oracle-vérifiée qui justifie fillOpacity -> canal alpha
        de fill-color, MAIS opacity -> fill-opacity (deux mécanismes Mapbox
        différents pour deux champs pivot différents, pas une coïncidence
        de nommage).
      * outlineColor -> fill-outline-color, même logique littéral/rgba()
        selon outlineOpacity. VÉRIFIÉ séparément contre l'oracle (pas
        seulement déduit par symétrie avec color/fillOpacity) : un document
        à deux Rule produit PAR ecrire_mbstyle() lui-même, avec color+
        opacity+fillOpacity+outlineColor+outlineOpacity tous renseignés
        simultanément sur la première Rule et un simple color littéral sur
        la seconde, chargé dans QgsMapBoxGlStyleConverter -> result==0,
        aucune erreur/avertissement, 2 styles produits, et sur la première :
        symbol.opacity()==0.8 (opacity), color alpha==128 (fillOpacity=0.5),
        outline_color alpha==77 (outlineOpacity=0.3) — les trois valeurs
        lues correctement et simultanément, sans contamination croisée.
      * outlineWidth, outlineDasharray, outlineCap, outlineJoin,
        outlineWidthUnit : AUCUN équivalent dans la spec Mapbox GL Style
        pour une couche "fill" — ce n'est pas une limite de conversion
        (QGIS ou geostyler) mais un FAIT de la spec elle-même : les
        propriétés "paint" d'une couche fill sont fill-antialias,
        fill-opacity, fill-color, fill-outline-color, fill-translate,
        fill-translate-anchor, fill-pattern — aucune ne contrôle l'épaisseur,
        le pointillé, ou les extrémités du contour (toujours un trait plein
        de 1px). Signalé par un AVERTISSEMENT SPÉCIFIQUE (pas la formule
        générique "propriété non gérée") dès que l'une de ces propriétés est
        renseignée avec une valeur qui en changerait le rendu, pour ne pas
        laisser croire qu'il s'agit d'un simple report à une itération
        future.
      * antialias : pas encore écrit cette itération (fill-antialias existe
        bien dans la spec Mapbox, mais son effet réel n'a pas été vérifié
        contre l'oracle — reporté avec les autres propriétés hors-portée,
        via le mécanisme générique cette fois, car ce N'EST PAS un cas
        d'impossibilité structurelle comme outlineWidth : juste "pas encore
        vérifié").
      * graphicFill/graphicFillPadding : hors-portée (motif "fill-pattern"
        de Mapbox, chantier de suivi symétrique au graphicFill de l'écrivain
        SLD) — lève ExpressionPivotNonEcrite si renseigné plutôt que
        d'ignorer silencieusement un remplissage texturé.

AVERTISSEMENT DE COUVERTURE EXPLICITE (transparence sur l'état de la
vérification à l'écriture de ce module) : l'orchestration COMPLÈTE a été
vérifiée de bout en bout contre QgsMapBoxGlStyleConverter EN CHARGEANT LE
DOCUMENT PRODUIT PAR ecrire_mbstyle() LUI-MÊME (pas seulement des styles
JSON construits à la main pendant l'exploration préalable) : un Style pivot
à deux Rule (la première avec color+opacity+fillOpacity+outlineColor+
outlineOpacity tous renseignés simultanément, la seconde avec un simple
color littéral) -> deux layers Mapbox -> convert() renvoie result==0, AUCUNE
erreur ni avertissement, 2 QgsVectorTileBasicRendererStyle produits, et les
trois mécanismes d'opacité (symbol.opacity()==0.8, color alpha==128 pour
fillOpacity=0.5, outline_color alpha==77 pour outlineOpacity=0.3) sont lus
correctement et SIMULTANÉMENT sur la première Rule, sans contamination
croisée, tandis que la seconde reste un simple remplissage plein opaque. La
connexion à l'oracle QGIS a ensuite été de nouveau interrompue (plugin QGIS
côté machine utilisateur) avant qu'ait pu être testée, séparément, la seule
affirmation de ce module qui ne repose PAS sur un test oracle mais sur la
lecture de la spec Mapbox GL Style elle-même : que outlineWidth/
outlineDasharray/outlineCap/outlineJoin, une fois écrits dans un document
Mapbox (paint_fill n'a tout simplement pas ces propriétés), sont bien
silencieusement ignorés par QgsMapBoxGlStyleConverter.convert() plutôt que
de le faire échouer — cette affirmation vient de la spec, pas d'un test.
DEPUIS CONFIRMÉ (voir plus loin, section "ÉTAT DE LA VÉRIFICATION POUR
CETTE EXTENSION" mise à jour après rétablissement de l'oracle principal) :
un document combiné chargé dans convert() avec ces clés non standard
présentes ne produit ni erreur ni avertissement (result==0) — ce point est
donc désormais aussi solidement établi que le reste, plus seulement déduit
de la spec.

DÉSACCORD RÉEL ENTRE LES DEUX ORACLES, DÉCOUVERT EN TESTANT (à connaître
avant de faire confiance à geostyler-cli sur ce point précis) : passer le
document produit par ce module (fill-color="rgba(255,0,0,0.5)", fill-
outline-color="rgba(0,0,0,0.3)", fill-opacity=0.8) dans geostyler-cli
(-s mapbox -t sld) ne lève aucune erreur — mais en inspectant directement
le pivot INTERMÉDIAIRE que geostyler-mapbox-parser construit (via
MapboxStyleParser.readStyle(), pas seulement la sortie SLD), son propre
LECTEUR mapbox->pivot DROPPE silencieusement le canal alpha d'un fill-color/
fill-outline-color en rgba() : color devient "#ff0000" (pas "#ff000080" ni
un fillOpacity reconstruit), outlineColor devient "#000000", sans aucune
trace de l'opacité perdue. Autrement dit, geostyler-mapbox-parser ne
reconstruit PAS fillOpacity/outlineOpacity à partir d'un alpha encodé dans
la couleur — SEUL fill-opacity (-> pivot opacity) survit à sa lecture.
QgsMapBoxGlStyleConverter, lui, CONSERVE cet alpha à l'affichage (vérifié :
symbolLayer color/outline_color alpha == valeurs attendues, voir plus haut).
Les deux oracles ne sont donc PAS d'accord sur ce point précis : ce module
suit l'oracle PRINCIPAL (QGIS, choix explicite de l'utilisateur) parce que
c'est lui qui reflète le comportement de RENDU réel (rgba() est une syntaxe
CSS standard que la spec Mapbox GL Style reconnaît explicitement pour
fill-color/fill-outline-color) ; le lecteur mapbox de geostyler semble
simplement lossy sur ce point précis plutôt que représenter une convention
concurrente légitime — mais le désaccord est noté ici plutôt que passé sous
silence, exactement le genre de signal que l'oracle secondaire devait
permettre de détecter (voir la discussion qui a précédé ce module sur le
risque de "faux signal" de geostyler-cli, à vérifier au cas par cas).

EXTENSION DE CETTE ITÉRATION (même session, portée élargie à la demande de
l'utilisateur — "faire tout ce qui reste") : Rule.filter (expressions
Mapbox GL, comparaisons/AND/OR/NOT/IN/IS [NOT] NULL/BETWEEN, PAS LIKE),
LineSymbolizer -> couche "line" (color/opacity/width/dasharray en paint,
cap/join en layout), MarkSymbolizer(wellKnownName="circle" uniquement) ->
couche "circle", TextSymbolizer -> couche "symbol" (cœur minimal :
label/font/size/color/halo/rotate), FillSymbolizer.antialias -> fill-
antialias, et deux exclusions supplémentaires documentées avec leur raison
STRUCTURELLE précise (pas une limite de conversion à vérifier) :
IconSymbolizer (icon-image référence un sprite nommé, pas une URL — voir
_ecrire_layer) et RasterSymbolizer (une couche "raster" a besoin d'une
SOURCE de type "raster", alors que ecrire_mbstyle() de cette itération ne
construit qu'une seule source "vector" partagée — voir _ecrire_layer).

ÉTAT DE LA VÉRIFICATION POUR CETTE EXTENSION — MISE À JOUR APRÈS RÉTABLISSEMENT
DE LA CONNEXION À L'ORACLE PRINCIPAL (la section précédente, qui documentait
un état "pas encore confirmé par QGIS" pendant une panne prolongée du plugin,
est désormais dépassée et remplacée par ce qui suit) :

  - CONFIRMÉ PAR L'ORACLE PRINCIPAL (QGIS, QgsMapBoxGlStyleConverter), via un
    document combiné à 9 couches produit PAR ecrire_mbstyle() lui-même et
    chargé dans un vrai QgsVectorTileBasicRenderer/QgsVectorTileBasicLabeling :
      * Fill : tous les mécanismes d'opacité toujours corrects (voir plus haut).
      * Rule.filter : comparaisons simples, AND/OR ("all"/"any"), IN
        (opérateur natif Mapbox), BETWEEN (reconstruit en AND de deux
        comparaisons) tous lus avec l'expression QGIS exacte attendue.
      * LineSymbolizer : color/opacity/width/cap/join tous corrects ; de plus,
        CONSTAT DE SPEC confirmé par l'oracle (pas un bug) : line-dasharray
        est réinterprété par QGIS comme des multiples de line-width (voir la
        docstring de _ecrire_line_paint) — l'écrivain reste un passage
        littéral, c'est un comportement du moteur de RENDU, pas de l'écriture.
      * MarkSymbolizer(circle) : circle-color/circle-opacity (dérivé de
        fillOpacity, PAS de opacity)/circle-stroke-*/circle-radius tous
        corrects ; radius N'EST PAS doublé dans le JSON Mapbox lui-même, mais
        QGIS le représente en interne comme un marker "size" doublé (diamètre)
        — cohérent avec la convention ×2 déjà établie côté SLD Size, juste
        observée cette fois côté interne QGIS plutôt que dans le JSON.
      * TextSymbolizer : désormais testé (via l'API séparée
        conv.labeling().styles()[0].labelSettings(), distincte de
        conv.renderer() — une couche "symbol" avec texte produit un objet
        QgsVectorTileBasicLabeling séparé, pas une entrée renderer()
        supplémentaire). fieldName/isExpression, color, size, font,
        haloColor, angleOffset tous corrects. CONSTAT DE SPEC confirmé :
        text-halo-width est DOUBLÉ par le buffer QGIS à la lecture (voir la
        docstring de _ecrire_text_paint, même traitement que dasharray/radius
        : passage littéral à l'écriture, le doublement est un comportement du
        moteur de rendu) ; text-rotate correspond 1:1 à angleOffset (AUCUNE
        inversion de signe, contrairement à SLD).
      * outlineWidth/outlineDasharray (et les autres propriétés "fill" hors
        spec Mapbox) : CONFIRMÉ inoffensif — ignoré silencieusement par
        convert() (result==0, aucun avertissement), comme attendu de la
        lecture de la spec seule ; ce point n'est donc plus "à confirmer".
      * antialias : fill-antialias accepté sans erreur ni avertissement par
        convert() dans ce même document combiné.

  - DEUX BUGS RÉELS DÉCOUVERTS PAR CETTE VÉRIFICATION, ET CORRIGÉS DANS CE
    MODULE (exactement le genre de régression que la discipline "toujours
    vérifier contre l'oracle PRINCIPAL avant de livrer" existe pour attraper
    — la corroboration de l'oracle secondaire seule s'est avérée insuffisante
    ici) :
      1. IS NULL/IS NOT NULL : la forme ["==", ["get", champ], null] — pourtant
         corroborée par une lecture indépendante de geostyler-cli — produit un
         AVERTISSEMENT QGIS ("Passe la partie d'expression non supportée") et
         une expression de filtre QGIS TRONQUÉE/INVALIDE ('"champ" IS '), pas
         le filtre attendu. CORRIGÉ : IS NOT NULL s'écrit maintenant
         ["has", champ] et IS NULL ["!", ["has", champ]] (voir
         _construire_filtre_mapbox), les deux vérifiés EXACTS contre l'oracle
         ('"champ" IS NOT NULL' / '"champ" IS NULL').
      2. Négation générale "!" : la traduction 1:1 de toute négation pivot
         (tuple ["!", ...] ou dict {"name":"not",...}) vers Mapbox "!" est
         BRISÉE pour une comparaison directe (["!", ["==",...]] -> avertissement
         "!==" non supporté) et pour AND/OR (["!", ["all"/"any",...]] ->
         "!all"/"!any" non supportés) : dans les deux cas, QGIS ABANDONNE le
         filtre entier en silence (filterExpression devient une chaîne VIDE,
         donc la Rule correspondrait alors à TOUTES les features — un risque
         de correction réel s'il avait été livré tel quel). "!" s'est révélé
         fiable UNIQUEMENT devant ["has", champ] et devant ["in", ...] (les
         deux vérifiés exacts). CORRIGÉ : _construire_filtre_mapbox lève
         maintenant ExpressionPivotNonEcrite pour toute négation qui ne se
         réduit pas à l'une de ces deux formes vérifiées (comparaison directe,
         all/any, double négation "!!" — cette dernière également vérifiée
         cassée), au lieu de produire silencieusement un filtre qui matche
         tout.

  - PAS ENCORE VÉRIFIÉ, à traiter dans une itération ultérieure si demandé :
    le choix ["get", champ] vs l'ancienne forme token "{champ}" pour
    text-field n'a pas été spécifiquement départagé contre l'oracle principal
    au-delà de la confirmation qu'il fonctionne (les deux formes sont
    probablement acceptées par QGIS, seule la forme expression a été testée
    ici puisque c'est celle que cet écrivain produit).

Tout ce qui sort de cette portée (encore plus restreinte qu'une seule
itération de l'écrivain SLD) lève ExpressionPivotNonEcrite avec le fragment
précis en cause — jamais une approximation silencieuse.

EXTENSION "COMPATIBILITÉ MAXIMALE" DU 2026-10-12 (à la demande explicite de
l'utilisateur : "je ne peux pas m'arrêter à un échec", voir la discussion
avant ce chantier) — trois restrictions de la portée initiale, ci-dessus,
sont levées, chacune avec un oracle ou une justification explicite (jamais
une approximation silencieuse) :
  1. Rule à N>1 symbolizers : écrite en N couches Mapbox empilées (même
     filtre/source-layer), PAS une approximation — Mapbox GL Style n'a
     structurellement aucune notion de symbolizers fusionnés d'une même
     règle (contrairement à SLD/QGIS), donc rien à approcher ; coexistence
     des N couches confirmée contre l'oracle principal. Voir _ecrire_layers.
  2. MarkSymbolizer de forme non circulaire : APPROXIMÉ en couche "circle"
     (couleur/taille/contour fidèles, forme perdue), avec avertissement
     explicite plutôt que rejet dur. Voir _ecrire_mark_paint.
  3. IconSymbolizer : désormais écrit en couche "symbol" (icon-image), via
     un résolveur de sprite optionnel ('resoudre_sprite' de ecrire_mbstyle())
     symétrique à 'resoudre_image_embarquee' côté SLD — structure et
     icon-size/icon-opacity/icon-rotate confirmés contre l'oracle principal
     (via un vrai serveur de sprites local + QgsMapBoxGlStyleConversionContext.
     setSprites()) ; icon-offset, lui, vérifié SANS EFFET et donc non écrit.
     Voir _ecrire_icon_paint.
  4. FillSymbolizer.graphicFill et LineSymbolizer.graphicFill/graphicStroke :
     désormais écrits en fill-pattern/line-pattern, via le MÊME résolveur de
     sprite que IconSymbolizer (un Mark imbriqué passe son wellKnownName TEL
     QUEL au résolveur — forme simple ou motif de hachure shape://... — un
     Icon imbriqué passe son image). CONFIRMÉ CONTRE L'ORACLE PRINCIPAL :
     fill-pattern produit une couche RasterFill EN PLUS de la SimpleFill de
     base (symbole à 2 couches, pas un remplacement — d'où fill-color à
     fournir en plus si un repli de couleur est souhaité) ; line-pattern
     produit un RasterLine, cette fois sans couche de base séparée. Voir
     _resoudre_motif_sprite.
  5. Rule.filter avec strMatches (LIKE/ILIKE) : les 4 formes à un SEUL
     segment littéral (exact/préfixe/suffixe/contient, ex. "a1-%"/"%abc%")
     sont désormais écrites, via slice/length/downcase/in — PAS un
     opérateur de motif générique (la spec Mapbox n'en a aucun), mais une
     composition exacte et sans ambiguïté de ces 4 cas précis. VÉRIFIÉ,
     mais pas contre l'oracle principal habituel de ce module (QGIS Desktop
     ne sait pas interpréter slice/downcase, voir le commentaire précédant
     _classifier_motif_like) : vérifié à la place contre
     @maplibre/maplibre-gl-style-spec, la spec de référence elle-même
     (featureFilter(), le même code qui évalue un 'filter' Mapbox dans un
     client réel), y compris sur les cas limites (champ absent, chaîne plus
     courte que le motif). Un motif à plusieurs segments ("a%b%c") ou au
     joker '_' reste hors de portée (lève ExpressionPivotNonEcrite plutôt
     que d'approximer) — voir _construire_motif_like_mapbox.
RasterSymbolizer, Rule.elseRule et un strMatches à plusieurs segments
littéraux ou au joker '_' restent hors de portée (raisons structurelles ou
de périmètre, voir plus haut, _ecrire_layers et _classifier_motif_like).
"""
from __future__ import annotations

import re
from typing import Any, Callable

import json as _json

# Réutilisé tel quel (pas réinventé) : seul producteur canonique de
# strMatches dans ce projet, voir sa docstring côté SLD — le motif SQL-LIKE
# qu'il décode (wildcards '%'/'_') est le MÊME quel que soit l'écrivain
# cible, seule sa TRADUCTION finale diffère (ogc:PropertyIsLike côté SLD,
# slice/downcase/in Mapbox ici, voir _construire_motif_like_mapbox).
from styleforge_core.writers.sld import _detecter_motif_like_depuis_regex


class ExpressionPivotNonEcrite(Exception):
    """Levée quand une valeur, un filtre, un symbolizer ou une propriété du
    pivot sort de la portée BORNÉE de cet écrivain (voir la docstring de
    module). Toujours accompagnée du fragment précis en cause."""


def _normaliser(valeur: Any) -> Any:
    """Même rôle que styleforge_core.writers.sld._normaliser : accepte un
    dict pivot brut OU une instance pydantic du modèle généré, ramène
    toujours à un dict pour n'avoir qu'une seule forme à traiter ici."""
    if hasattr(valeur, "model_dump"):
        return valeur.model_dump(exclude_none=True)
    return valeur


# --------------------------------------------------------------------------- couleur (pivot hex -> Mapbox color)
_MOTIF_HEX_RRGGBB = re.compile(r"^#[0-9a-fA-F]{6}$")


def _hex_vers_rgb(valeur: str, contexte: str, nom_proprietaire: str) -> tuple[int, int, int]:
    """"#rrggbb" -> (r, g, b) entiers 0..255. Seule cette forme (6 chiffres
    hexadécimaux, avec le '#') est acceptée pour cette itération — le schéma
    pivot ne contraint pas le format de 'color' au-delà de "hex-color
    string" (cf. styleforge_core/pivot/_genere.py, FillSymbolizer.color),
    mais c'est la seule forme produite par le lecteur QML de ce projet
    (styleforge_core.readers.qml.couleur_qgis_vers_hex) : pas d'autre forme
    à couvrir tant qu'aucune source pivot n'en produit une autre."""
    if not isinstance(valeur, str) or not _MOTIF_HEX_RRGGBB.match(valeur):
        raise ExpressionPivotNonEcrite(
            f"{contexte} : {nom_proprietaire}={valeur!r} n'est pas de la forme "
            f"\"#rrggbb\" (6 chiffres hexadécimaux) — seule cette forme est "
            f"écrite par cette itération."
        )
    return int(valeur[1:3], 16), int(valeur[3:5], 16), int(valeur[5:7], 16)


def _valeur_symbolizer_litterale(valeur: Any, contexte: str, nom_proprietaire: str) -> Any:
    """Même restriction que côté SLD (styleforge_core.writers.sld) : UNIQUEMENT
    des littéraux pour cette itération, pas de Fproperty ni d'expression pivot
    en position de propriété de symbolizer — pas encore vérifié contre
    l'oracle QGIS pour ce format (les expressions de style Mapbox ont une
    syntaxe complètement différente de celle du filtre OGC, ce serait un
    chantier à part, pas une extrapolation depuis le résultat SLD)."""
    if isinstance(valeur, dict):
        raise ExpressionPivotNonEcrite(
            f"{contexte} : {nom_proprietaire} piloté par une expression pivot "
            f"({valeur.get('name', '?')!r}) — non écrit par cette itération. Les "
            f"expressions de style Mapbox GL ('data-driven styling', syntaxe "
            f"[\"get\", ...] / [\"interpolate\", ...]) ont une syntaxe propre, "
            f"distincte de celle du filtre OGC déjà vérifiée côté écrivain SLD ; "
            f"pas encore vérifiée contre l'oracle QGIS pour ce module."
        )
    return valeur


def _couleur_mapbox(
    hex_couleur: Any, opacite: Any, contexte: str, nom_couleur: str, nom_opacite: str
) -> str:
    """Construit la valeur Mapbox pour une paire (couleur hex, opacité 0..1)
    du pivot : "#rrggbb" tel quel si opacite est None ou vaut 1 (littéralement
    — pas d'arrondi flottant risqué sur une comparaison d'égalité à 1, le cas
    covers 'opacité absente' qui est le cas de très loin le plus courant),
    sinon "rgba(r,g,b,opacite)" avec opacite écrit comme le FLOTTANT pivot
    tel quel (syntaxe CSS rgba() standard de la spec Mapbox GL Style, qui
    attend un alpha 0..1 — PAS de conversion vers un entier 0..255 : cette
    conversion est faite par QGIS à la LECTURE de rgba(), pas une convention
    à reproduire à l'écriture ; vérifié contre l'oracle QgsMapBoxGlStyleConverter
    avant l'interruption de connexion : rgba(255,0,0,0.5) -> symbolLayer
    color alpha==128, rgba(0,0,0,0.3) -> alpha==77, les deux lus correctement
    par QGIS à partir du flottant CSS, sans qu'on ait eu à précalculer
    l'entier nous-mêmes)."""
    opacite = _valeur_symbolizer_litterale(opacite, contexte, nom_opacite)
    r, g, b = _hex_vers_rgb(hex_couleur, contexte, nom_couleur)
    if opacite is None or opacite == 1:
        return hex_couleur
    if not isinstance(opacite, (int, float)) or isinstance(opacite, bool):
        raise ExpressionPivotNonEcrite(
            f"{contexte} : {nom_opacite}={opacite!r} n'est pas un nombre littéral "
            f"— seul ce cas est écrit par cette itération."
        )
    return f"rgba({r},{g},{b},{opacite})"


# --------------------------------------------------------------------------- FillSymbolizer -> Mapbox layer type "fill"
#: propriétés pivot de FillSymbolizer sans AUCUN équivalent dans les
#: propriétés "paint" d'une couche Mapbox "fill" — fait de la spec Mapbox GL
#: Style elle-même (paint_fill : fill-antialias, fill-opacity, fill-color,
#: fill-outline-color, fill-translate, fill-translate-anchor, fill-pattern
#: ; aucune ne contrôle épaisseur/pointillé/extrémités d'un contour, qui est
#: toujours un trait plein de largeur fixe ~1px), PAS une limite de
#: conversion QGIS ou geostyler découverte en testant — donc pas besoin d'un
#: oracle pour l'affirmer, mais signalé explicitement plutôt que noyé dans
#: l'avertissement générique de propriété non gérée.
_PROPRIETES_CONTOUR_SANS_EQUIVALENT_MAPBOX = (
    "outlineWidth", "outlineDasharray", "outlineCap", "outlineJoin", "outlineWidthUnit",
)


def _avertir_proprietes_non_gerees(
    sym: dict, geres: set[str], avertissements: list[str], contexte: str
) -> None:
    ignores_toujours = {"kind", "visibility", "geometry"}
    for cle, val in sym.items():
        if cle in geres or cle in ignores_toujours or val is None:
            continue
        avertissements.append(
            f"{contexte} : propriété de symbolizer {cle!r} (valeur {val!r}) NON "
            f"écrite dans le document Mapbox produit — hors de la portée bornée "
            f"de cet écrivain pour cette itération, PAS silencieusement ignorée."
        )


#: EXTENSION du 2026-10-12 (à la demande explicite de l'utilisateur de
#: maximiser la compatibilité plutôt que d'échouer) : fill-pattern/
#: line-pattern référencent, EXACTEMENT comme icon-image (voir
#: _ecrire_icon_paint), un NOM de vignette déjà enregistrée dans le sprite
#: du style — jamais un motif vectoriel décrit en ligne (contrairement à
#: SLD/GraphicFill, qui PEUT décrire un Mark analytiquement). Ce symbolizer
#: imbriqué (un MarkSymbolizer — forme simple "circle"/"square"... OU motif
#: de hachure "shape://slash"... — OU un IconSymbolizer, même SVG/base64 que
#: pour une image autonome) est donc résolu par le MÊME callback optionnel
#: 'resoudre_sprite' que IconSymbolizer : un Mark passe son wellKnownName
#: TEL QUEL (même convention que SpriteRegistry.register_shape côté CLI,
#: qui sait déjà dessiner un motif de hachure OU une forme simple tuilable),
#: un Icon passe son 'image' (chemin/base64, même convention que pour un
#: IconSymbolizer autonome). CONFIRMÉ CONTRE L'ORACLE PRINCIPAL
#: (QgsMapBoxGlStyleConverter, via le même contexte de sprites pré-rempli
#: que pour IconSymbolizer) : fill-pattern="<nom>" (avec fill-color
#: renseigné en PLUS, sinon le symbole de base reste "no fill" ET le motif
#: n'est qu'une couche DE PLUS, pas un remplacement) -> symbole à 2
#: COUCHES, SimpleFill (color/outline, couche 0) PUIS RasterFill (le motif,
#: couche 1, imageFile correctement résolu) ; line-pattern="<nom>" ->
#: RasterLine (imageFile correctement résolu), confirmé directement, sans
#: couche de base séparée cette fois.
def _resoudre_motif_sprite(
    nested: dict, avertissements: list[str], contexte: str,
    *, resoudre_sprite: Callable[[str], str | None] | None,
) -> str:
    """Résout un symbolizer imbriqué (Mark ou Icon, FillSymbolizer.graphicFill
    ou LineSymbolizer.graphicFill/graphicStroke) en nom de vignette de sprite
    Mapbox. Voir le commentaire précédant cette fonction pour l'état complet
    de la vérification contre l'oracle."""
    nk = nested.get("kind")
    if nk == "Mark":
        jeton = nested.get("wellKnownName") or "circle"
    elif nk == "Icon":
        image = nested.get("image")
        if not isinstance(image, str):
            raise ExpressionPivotNonEcrite(
                f"{contexte} : symbolizer imbriqué Icon sans image exploitable "
                f"(image={image!r}) pour un motif de remplissage/contour."
            )
        jeton = image
    else:
        raise ExpressionPivotNonEcrite(
            f"{contexte} : symbolizer imbriqué de type {nk!r} non écrit par cette "
            f"itération pour un motif de remplissage/contour (seuls Mark et Icon le sont)."
        )
    if resoudre_sprite is None:
        raise ExpressionPivotNonEcrite(
            f"{contexte} : motif de remplissage/contour ({nk}={jeton!r}) non écrit — "
            f"fill-pattern/line-pattern Mapbox référencent TOUJOURS un nom de vignette "
            f"déjà enregistré dans le sprite du style : aucun résolveur 'resoudre_sprite' "
            f"fourni à ecrire_mbstyle()."
        )
    nom = resoudre_sprite(jeton)
    if not nom:
        raise ExpressionPivotNonEcrite(
            f"{contexte} : motif de remplissage/contour ({nk}={jeton!r}) — le résolveur "
            f"de sprite fourni n'a pas su le nommer (a renvoyé None/vide) ; non écrit "
            f"plutôt que de référencer un fill-pattern/line-pattern inexistant."
        )
    return str(nom)


def _ecrire_fill_paint(
    sym: dict, avertissements: list[str], contexte: str,
    *, resoudre_sprite: Callable[[str], str | None] | None = None,
) -> dict:
    """FillSymbolizer (dict pivot normalisé) -> dict "paint" Mapbox pour une
    couche de type "fill". Voir la docstring de module pour le détail
    (couverture vérifiée, distinction opacity/fillOpacity, et l'impossibilité
    structurelle — pas une limite de conversion — des propriétés de contour
    outlineWidth/Dasharray/Cap/Join dans la spec Mapbox "fill"). 'resoudre_sprite'
    (extension du 2026-10-12) : voir _resoudre_motif_sprite pour graphicFill."""
    paint: dict[str, Any] = {}
    if sym.get("graphicFill") is not None:
        nom = _resoudre_motif_sprite(
            _normaliser(sym["graphicFill"]), avertissements, contexte,
            resoudre_sprite=resoudre_sprite,
        )
        paint["fill-pattern"] = nom
    if sym.get("color") is not None:
        paint["fill-color"] = _couleur_mapbox(
            sym["color"], sym.get("fillOpacity"), contexte, "color", "fillOpacity",
        )
    elif sym.get("fillOpacity") is not None:
        raise ExpressionPivotNonEcrite(
            f"{contexte} : fillOpacity={sym['fillOpacity']!r} renseigné sans color — "
            f"aucune couleur par défaut Mapbox sur laquelle appliquer ce canal alpha "
            f"n'est écrite par cette itération (contrairement à SLD, qui a un "
            f"fill-opacity CssParameter indépendant de la couleur)."
        )
    if sym.get("outlineColor") is not None:
        paint["fill-outline-color"] = _couleur_mapbox(
            sym["outlineColor"], sym.get("outlineOpacity"), contexte,
            "outlineColor", "outlineOpacity",
        )
    elif sym.get("outlineOpacity") is not None:
        raise ExpressionPivotNonEcrite(
            f"{contexte} : outlineOpacity={sym['outlineOpacity']!r} renseigné sans "
            f"outlineColor — même raison que pour fillOpacity/color ci-dessus."
        )
    if sym.get("opacity") is not None:
        paint["fill-opacity"] = _valeur_symbolizer_litterale(sym["opacity"], contexte, "opacity")
    if sym.get("antialias") is not None:
        # fill-antialias EST une propriété "paint" réelle de la spec Mapbox
        # (booléenne) — écrite en littéral, même restriction que le reste de
        # ce module pour cette itération (pas d'expression).
        paint["fill-antialias"] = _valeur_symbolizer_litterale(sym["antialias"], contexte, "antialias")
    for cle in _PROPRIETES_CONTOUR_SANS_EQUIVALENT_MAPBOX:
        if sym.get(cle) is not None:
            avertissements.append(
                f"{contexte} : {cle}={sym[cle]!r} NON écrit — la spec Mapbox GL Style "
                f"n'a AUCUNE propriété \"paint\" pour une couche \"fill\" contrôlant "
                f"l'épaisseur, le pointillé, ou les extrémités du contour (paint_fill "
                f"se limite à fill-antialias/fill-opacity/fill-color/"
                f"fill-outline-color/fill-translate*/fill-pattern) : le contour d'une "
                f"couche fill Mapbox est TOUJOURS un simple trait plein de largeur "
                f"fixe. Ceci n'est pas une limite de conversion découverte en testant "
                f"(comme pour l'écrivain SLD) mais un fait de la spec elle-même — "
                f"contourner cela nécessiterait une couche \"line\" séparée, hors de "
                f"la portée de cet écrivain pour cette itération."
            )
    _avertir_proprietes_non_gerees(
        sym,
        {"color", "fillOpacity", "outlineColor", "outlineOpacity", "opacity", "antialias",
         "graphicFill", *_PROPRIETES_CONTOUR_SANS_EQUIVALENT_MAPBOX},
        avertissements, contexte,
    )
    return paint, {}


# --------------------------------------------------------------------------- LineSymbolizer -> Mapbox layer type "line"
def _ecrire_line_paint(
    sym: dict, avertissements: list[str], contexte: str,
    *, resoudre_sprite: Callable[[str], str | None] | None = None,
) -> tuple[dict, dict]:
    """LineSymbolizer -> (paint, layout) Mapbox pour une couche "line".
    Contrairement à FillSymbolizer, LineSymbolizer du pivot n'a QU'UN SEUL
    champ d'opacité (pas de split color/lineOpacity comme fillOpacity/outline
    Opacity) — cf. la docstring de styleforge_core.writers.sld, section sur
    LineSymbolizer.opacity : "aucune ambiguïté, un seul champ d'opacité".
    Donc pas besoin du mécanisme rgba() de _couleur_mapbox ici : line-opacity
    est une propriété "paint" Mapbox à part entière (contrairement à
    FillSymbolizer.fillOpacity, qui elle n'a pas de propriété "paint" dédiée).
    cap/join sont des propriétés "layout" (pas "paint") côté Mapbox — leurs
    valeurs d'énumération pivot ('butt'/'round'/'square' pour cap,
    'bevel'/'miter'/'round' pour join, cf. styleforge_core/pivot/_genere.py,
    LineSymbolizer.cap/.join) sont ORTHOGRAPHIQUEMENT IDENTIQUES aux valeurs
    Mapbox line-cap/line-join : passage littéral, pas de table de
    correspondance à inventer.

    CONSTAT VÉRIFIÉ CONTRE L'ORACLE QGIS (QgsMapBoxGlStyleConverter) : les
    valeurs de line-dasharray sont réinterprétées EN INTERNE par QGIS comme
    des multiples de line-width (dasharray [4,2] + width 2 -> customdash
    QGIS "8;4", soit [4x2, 2x2]) — un fait de la spec Mapbox (les unités du
    tiret sont relatives à la largeur du trait), pas un bug ni une
    approximation de cet écrivain : la liste pivot est écrite ICI de façon
    strictement littérale (aucune division/compensation appliquée), c'est
    QGIS (le moteur de rendu, pas ce module) qui applique la mise à
    l'échelle à la lecture, exactement comme pour MarkSymbolizer.radius x2
    (cf. _ecrire_mark_paint).

    'resoudre_sprite' (extension du 2026-10-12) : LineSymbolizer.graphicFill
    ET .graphicStroke s'écrivent tous deux en line-pattern — Mapbox GL Style
    n'a qu'UNE SEULE propriété de motif pour une couche "line" (contrairement
    à SLD, qui distingue Stroke/GraphicFill de Stroke/GraphicStroke) — voir
    _resoudre_motif_sprite, CONFIRMÉ CONTRE L'ORACLE (RasterLine correctement
    résolu)."""
    paint: dict[str, Any] = {}
    layout: dict[str, Any] = {}
    motif = sym.get("graphicFill") or sym.get("graphicStroke")
    if motif is not None:
        nom = _resoudre_motif_sprite(
            _normaliser(motif), avertissements, contexte, resoudre_sprite=resoudre_sprite,
        )
        paint["line-pattern"] = nom
    if sym.get("color") is not None:
        paint["line-color"] = _valeur_symbolizer_litterale(sym["color"], contexte, "color")
        _hex_vers_rgb(sym["color"], contexte, "color")  # valide le format, valeur déjà écrite littéralement
    if sym.get("opacity") is not None:
        paint["line-opacity"] = _valeur_symbolizer_litterale(sym["opacity"], contexte, "opacity")
    if sym.get("width") is not None:
        paint["line-width"] = _valeur_symbolizer_litterale(sym["width"], contexte, "width")
    if sym.get("dasharray") is not None:
        valeurs = sym["dasharray"]
        if not (isinstance(valeurs, list) and all(isinstance(v, (int, float)) and not isinstance(v, bool) for v in valeurs)):
            raise ExpressionPivotNonEcrite(
                f"{contexte} : dasharray={valeurs!r} n'est pas une liste de nombres "
                f"littéraux — seul ce cas est écrit par cette itération."
            )
        paint["line-dasharray"] = valeurs
    if sym.get("cap") is not None:
        layout["line-cap"] = _valeur_symbolizer_litterale(sym["cap"], contexte, "cap")
    if sym.get("join") is not None:
        layout["line-join"] = _valeur_symbolizer_litterale(sym["join"], contexte, "join")
    _avertir_proprietes_non_gerees(
        sym,
        {"color", "opacity", "width", "dasharray", "cap", "join",
         "graphicFill", "graphicStroke"},
        avertissements, contexte,
    )
    return paint, layout


# --------------------------------------------------------------------------- MarkSymbolizer -> Mapbox layer type "circle"
#: Mapbox GL Style n'a PAS de notion de "well-known name" pour une couche
#: "circle" : c'est TOUJOURS un cercle plein, par construction. wellKnownName
#: du pivot (54 formes dans l'enum : square, triangle, star, ttf://, shape://,
#: brush://...) n'a d'équivalent Mapbox QUE pour "circle" (ou absent, qui
#: équivaut à "circle" par défaut côté pivot comme côté SLD) — toute autre
#: forme nécessiterait une couche "symbol" avec icon-image référençant un
#: sprite, même mécanisme que IconSymbolizer (voir _ecrire_icon_paint).
_FORMES_MARK_ECRITES = {None, "circle"}

#: EXTENSION du 2026-10-12 (à la demande explicite de l'utilisateur de
#: maximiser la compatibilité plutôt que d'échouer) : un MarkSymbolizer avec
#: une forme HORS de _FORMES_MARK_ECRITES n'est plus un échec dur — il est
#: APPROXIMÉ en couche "circle" (couleur/fillOpacity/stroke-*/radius restent
#: fidèles, SEULE la forme réelle est perdue), avec un AVERTISSEMENT EXPLICITE
#: qui le dit (jamais silencieux). Une Rule au corpus réel avec une forme non
#: circulaire pourrait, en alternative plus fidèle mais plus lourde, être
#: réécrite en IconSymbolizer référençant un sprite dédié à cette forme —
#: hors de portée de cette itération, qui se limite à l'approximation la
#: moins coûteuse (même esprit que l'approximation EllipseMarker->circle/
#: square côté SLD, cf. styleforge_core/compat/ellipse.py).


def _ecrire_mark_paint(
    sym: dict, avertissements: list[str], contexte: str,
    *, resoudre_sprite: Callable[[str], str | None] | None = None,
) -> tuple[dict, dict]:
    """MarkSymbolizer(wellKnownName="circle") -> (paint, {}) Mapbox pour une
    couche "circle". fillOpacity (PAS opacity) -> circle-opacity : Mapbox a
    une propriété "paint" DÉDIÉE pour l'opacité du disque (contrairement à
    FillSymbolizer, pas besoin du mécanisme rgba() de _couleur_mapbox) —
    convention CORROBORÉE indépendamment par geostyler-mapbox-parser (oracle
    secondaire, lecture directe du pivot intermédiaire, pas seulement une
    sortie SLD reconstruite) : circle-opacity (Mapbox) -> pivot
    MarkSymbolizer.fillOpacity, jamais MarkSymbolizer.opacity. radius (pivot)
    -> circle-radius SANS doublement (contrairement à SLD Size = radius × 2) :
    circle-radius Mapbox EST déjà un rayon en pixels, pas un diamètre —
    corroboré par la même lecture indépendante (circle-radius=5 (Mapbox) ->
    pivot radius=5, non doublé). MarkSymbolizer.opacity (l'opacité GLOBALE du
    symbolizer, distincte de fillOpacity — voir la découverte centrale côté
    FillSymbolizer) N'A PAS d'équivalent Mapbox pour une couche circle : ni
    circle-opacity (déjà pris par fillOpacity) ni circle-stroke-opacity
    (déjà pris par strokeOpacity) ne représentent une opacité GLOBALE
    combinée — signalé par un avertissement spécifique plutôt que la formule
    générique, même traitement que outlineWidth côté Fill (fait de spec, pas
    une limite de conversion)."""
    forme = sym.get("wellKnownName")
    if forme not in _FORMES_MARK_ECRITES:
        avertissements.append(
            f"{contexte} : MarkSymbolizer.wellKnownName={forme!r} APPROXIMÉ en "
            f"\"circle\" — Mapbox GL Style n'a de couche dédiée que pour un cercle "
            f"plein ; couleur/fillOpacity/stroke-*/radius restent fidèles, mais la "
            f"FORME réelle ({forme!r}) est PERDUE (un rendu fidèle demanderait une "
            f"couche \"symbol\" avec icon-image référençant un sprite dédié à cette "
            f"forme, voir IconSymbolizer/_ecrire_icon_paint — hors de portée de cette "
            f"itération pour une forme Mark). Écrit sur demande explicite de "
            f"maximiser la compatibilité du corpus réel plutôt que d'échouer — à "
            f"confirmer visuellement avant mise en production si la forme exacte importe."
        )
    paint: dict[str, Any] = {}
    if sym.get("color") is not None:
        paint["circle-color"] = _valeur_symbolizer_litterale(sym["color"], contexte, "color")
        _hex_vers_rgb(sym["color"], contexte, "color")
    if sym.get("fillOpacity") is not None:
        paint["circle-opacity"] = _valeur_symbolizer_litterale(sym["fillOpacity"], contexte, "fillOpacity")
    if sym.get("strokeColor") is not None:
        paint["circle-stroke-color"] = _valeur_symbolizer_litterale(sym["strokeColor"], contexte, "strokeColor")
        _hex_vers_rgb(sym["strokeColor"], contexte, "strokeColor")
    if sym.get("strokeWidth") is not None:
        paint["circle-stroke-width"] = _valeur_symbolizer_litterale(sym["strokeWidth"], contexte, "strokeWidth")
    if sym.get("strokeOpacity") is not None:
        paint["circle-stroke-opacity"] = _valeur_symbolizer_litterale(sym["strokeOpacity"], contexte, "strokeOpacity")
    if sym.get("radius") is not None:
        paint["circle-radius"] = _valeur_symbolizer_litterale(sym["radius"], contexte, "radius")
    if sym.get("opacity") is not None:
        avertissements.append(
            f"{contexte} : opacity={sym['opacity']!r} NON écrit — Mapbox GL Style n'a "
            f"AUCUNE propriété \"paint\" d'opacité GLOBALE pour une couche \"circle\" "
            f"(circle-opacity ne couvre que le disque, déjà utilisé pour fillOpacity ; "
            f"circle-stroke-opacity ne couvre que le contour, déjà utilisé pour "
            f"strokeOpacity) : fait de la spec elle-même, pas une limite de conversion "
            f"découverte en testant."
        )
    _avertir_proprietes_non_gerees(
        sym,
        {"wellKnownName", "color", "fillOpacity", "strokeColor", "strokeWidth",
         "strokeOpacity", "radius", "opacity"},
        avertissements, contexte,
    )
    return paint, {}


# --------------------------------------------------------------------------- TextSymbolizer -> Mapbox layer type "symbol"
_MOTIF_LABEL_CHAMP_NU = re.compile(r"^\{\{([A-Za-z_][A-Za-z0-9_]*)\}\}$")


def _extraire_nom_champ_label(label: Any, contexte: str) -> str:
    """Même restriction que styleforge_core.writers.sld._extraire_nom_champ_label
    (voir sa docstring pour le détail des formes cassées côté SLD) — reprise
    ici par prudence plutôt que supposée transposable telle quelle : PAS
    encore vérifiée spécifiquement contre l'oracle QGIS pour le mécanisme
    text-field Mapbox (une syntaxe complètement différente de Label/
    ogc:PropertyName), voir l'avertissement de couverture de la docstring de
    module."""
    if isinstance(label, dict) and label.get("name") == "property":
        args = label.get("args", [])
        if len(args) == 1:
            return str(args[0])
    if isinstance(label, str):
        m = _MOTIF_LABEL_CHAMP_NU.match(label)
        if m:
            return m.group(1)
        raise ExpressionPivotNonEcrite(
            f"{contexte} : label={label!r} n'est pas un template champ-seul "
            f"(\"{{{{champ}}}}\", rien avant/après) — seule cette forme est écrite par "
            f"cette itération (même restriction que l'écrivain SLD, par prudence, pas "
            f"encore reverifiée spécifiquement pour le mécanisme text-field Mapbox)."
        )
    raise ExpressionPivotNonEcrite(
        f"{contexte} : label={label!r} sous une forme Fxxx non écrite par cette "
        f"itération (seul un template \"{{{{champ}}}}\" ou un Fproperty nu l'est)."
    )


def _ecrire_text_paint(
    sym: dict, avertissements: list[str], contexte: str,
    *, resoudre_sprite: Callable[[str], str | None] | None = None,
) -> tuple[dict, dict]:
    """TextSymbolizer -> (paint, layout) Mapbox pour une couche "symbol".
    Cœur minimal délibérément restreint au même périmètre que le
    TextSymbolizer de l'écrivain SLD (label/font/size/color/halo/rotate),
    PAS une tentative de couvrir les ~30 propriétés du schéma Mapbox
    layout_symbol/paint_symbol dès ce premier passage. Contrairement à SLD,
    AUCUNE restriction n'est appliquée sur "une Rule ne doit pas contenir
    QUE du Text" : ce n'était pas une contrainte Mapbox mais un artefact du
    modèle de fusion SLD (un FeatureTypeStyle QGIS fusionne les symbolizers
    d'une même Rule) — en Mapbox, chaque Rule produit sa PROPRE couche
    indépendante ("symbol"), il n'y a rien à fusionner, donc rien à
    craindre d'une couche symbol autonome — CONFIRMÉ contre l'oracle QGIS
    (QgsMapBoxGlStyleConverter.labeling().styles() reconstitue fieldName/
    isExpression, color, size, font, haloColor, angleOffset correctement
    pour une couche "symbol" isolée).

    CONSTAT VÉRIFIÉ CONTRE L'ORACLE : text-halo-width est DOUBLÉ par QGIS à
    la lecture (haloWidth=1 -> label buffer size=2.0 ; haloWidth=2 -> buffer
    size=4.0, confirmé sur deux points). Comme pour line-dasharray/width et
    MarkSymbolizer.radius, cet écrivain écrit la valeur pivot de façon
    strictement littérale (paint["text-halo-width"] = haloWidth, sans
    division par 2) : c'est un comportement du convertisseur/moteur QGIS à
    la LECTURE, pas une correction à appliquer à l'ÉCRITURE — documenté ici
    pour qu'un futur lecteur MBStyle sache qu'il doit diviser par 2 au
    retour, symétriquement, s'il veut retrouver le haloWidth pivot d'origine.

    CONSTAT VÉRIFIÉ CONTRE L'ORACLE : text-rotate correspond 1:1 à QGIS
    angleOffset (AUCUNE inversion de signe, contrairement à la convention
    SLD "(360-rotate)%360" — vérifié, pas supposé)."""
    layout: dict[str, Any] = {}
    paint: dict[str, Any] = {}
    if sym.get("label") is None:
        raise ExpressionPivotNonEcrite(f"{contexte} : TextSymbolizer sans label (label=None).")
    champ = _extraire_nom_champ_label(sym["label"], contexte)
    layout["text-field"] = ["get", champ]
    if sym.get("font") is not None:
        police = sym["font"]
        if not (isinstance(police, list) and police and all(isinstance(p, str) for p in police)):
            raise ExpressionPivotNonEcrite(
                f"{contexte} : font={police!r} n'est pas une liste non vide de noms de "
                f"police — seule cette forme est écrite par cette itération."
            )
        # text-font Mapbox attend DÉJÀ une liste (une pile de polices de
        # repli), contrairement au font-family SLD/CSS où une seule chaîne
        # est attendue : la liste pivot est donc écrite ENTIÈREMENT ici,
        # pas seulement sa première entrée comme le fait l'écrivain SLD.
        layout["text-font"] = police
    if sym.get("size") is not None:
        # text-size EST une propriété "layout" côté Mapbox (pas "paint"),
        # contrairement à ce que son nom pourrait suggérer par analogie avec
        # SLD/CSS font-size — vérifié dans la spec Mapbox GL Style
        # (layout_symbol), pas une supposition.
        layout["text-size"] = _valeur_symbolizer_litterale(sym["size"], contexte, "size")
    if sym.get("rotate") is not None:
        layout["text-rotate"] = _valeur_symbolizer_litterale(sym["rotate"], contexte, "rotate")
    if sym.get("color") is not None:
        paint["text-color"] = _valeur_symbolizer_litterale(sym["color"], contexte, "color")
        _hex_vers_rgb(sym["color"], contexte, "color")
    if sym.get("haloWidth") is not None:
        paint["text-halo-width"] = _valeur_symbolizer_litterale(sym["haloWidth"], contexte, "haloWidth")
    if sym.get("haloColor") is not None:
        # text-halo-opacity n'existe pas dans la spec Mapbox (contrairement à
        # fill-opacity/fillOpacity côté Fill) : même mécanisme rgba() que
        # _couleur_mapbox pour encoder haloOpacity dans le canal alpha de
        # text-halo-color, par cohérence avec le choix déjà fait pour Fill —
        # PAS encore vérifié spécifiquement contre l'oracle pour ce champ.
        paint["text-halo-color"] = _couleur_mapbox(
            sym["haloColor"], sym.get("haloOpacity"), contexte, "haloColor", "haloOpacity",
        )
    elif sym.get("haloOpacity") is not None:
        raise ExpressionPivotNonEcrite(
            f"{contexte} : haloOpacity={sym['haloOpacity']!r} renseigné sans haloColor "
            f"— même raison que fillOpacity/color côté FillSymbolizer."
        )
    if sym.get("opacity") is not None:
        paint["text-opacity"] = _valeur_symbolizer_litterale(sym["opacity"], contexte, "opacity")
    _avertir_proprietes_non_gerees(
        sym,
        {"label", "font", "size", "rotate", "color", "haloWidth", "haloColor",
         "haloOpacity", "opacity"},
        avertissements, contexte,
    )
    return paint, layout


# --------------------------------------------------------------------------- IconSymbolizer -> Mapbox layer type "symbol" (icon-image)
#: EXTENSION du 2026-10-12 (à la demande explicite de l'utilisateur de
#: maximiser la compatibilité plutôt que d'échouer) : IconSymbolizer était
#: jusqu'ici exclu avec une raison STRUCTURELLE (icon-image référence un NOM
#: de vignette déjà enregistré dans le sprite du style, jamais une URL
#: arbitraire comme le fait IconSymbolizer.image côté pivot ou ExternalGraphic
#: côté SLD — voir l'ancienne docstring de module). Cette raison reste VRAIE,
#: mais n'est plus un blocage : exactement comme 'resoudre_image_embarquee'
#: côté écrivain SLD (styleforge_core.writers.sld) permet à l'appelant de
#: matérialiser un SVG base64 embarqué en un fichier puis un href, un
#: paramètre optionnel symétrique 'resoudre_sprite' permet ICI à l'appelant
#: d'enregistrer IconSymbolizer.image dans SA feuille de sprites et de
#: renvoyer le NOM de vignette à écrire dans icon-image. Sans résolveur
#: fourni (ou s'il renvoie None), ExpressionPivotNonEcrite est levée plutôt
#: que d'écrire un icon-image référençant une vignette qui n'existe pas.
#:
#: CONFIRMÉ CONTRE L'ORACLE PRINCIPAL (QgsMapBoxGlStyleConverter), via un
#: serveur HTTP local servant un vrai sprite.png/sprite.json et un
#: QgsMapBoxGlStyleConversionContext.setSprites() pré-rempli (la seule façon
#: de faire aboutir ce test : le convertisseur NE TÉLÉCHARGE PAS lui-même la
#: feuille de sprites depuis l'URL 'sprite' du document — un detail de l'API
#: bas niveau utilisée en test, pas une restriction du FORMAT du document
#: produit ici, qui lui référence bien l'URL 'sprite' comme tout document
#: Mapbox GL Style standard) :
#:   * icon-image="<nom>" -> QgsRasterMarkerSymbolLayer correctement résolu
#:     (layerType "RasterMarker", imageFile pointant vers la vignette décodée).
#:   * icon-size (Mapbox) est un FACTEUR D'ÉCHELLE appliqué à la taille NATIVE
#:     de la vignette dans la feuille de sprites, PAS une taille absolue en
#:     pixels : icon-size=2.0 sur une vignette de 64 px -> symbolLayer
#:     size()==128 (Pixel), soit 64×2 exactement. D'où le paramètre
#:     'taille_sprite_px' (choix de contexte de rendu — la taille des
#:     vignettes de LA feuille de sprites effectivement utilisée — jamais une
#:     information du pivot, principe évolutif) : icon-size écrit ici =
#:     IconSymbolizer.size / taille_sprite_px, pour retrouver une taille
#:     absolue fidèle au pivot plutôt que le défaut Mapbox (1.0 = taille
#:     native de la vignette, probablement fausse pour le corpus réel).
#:   * icon-opacity (paint) -> alpha du symbolLayer, confirmé (0.6 -> 0.6).
#:   * icon-rotate (layout) -> angle du symbolLayer, confirmé 1:1 (30 -> 30),
#:     aucune inversion de signe (même constat que text-rotate, voir
#:     _ecrire_text_paint).
#:   * icon-offset (layout), lui, est VÉRIFIÉ CASSÉ : icon-offset=[5,-3]
#:     n'affecte PAS le symbolLayer résultant (offset() reste "0,0" après
#:     conversion) — un écart RÉEL découvert en testant (pas une limite de
#:     conception de ce module), donc IconSymbolizer.offset n'est PAS écrit,
#:     avec un avertissement explicite plutôt qu'un icon-offset silencieusement
#:     sans effet.
def _ecrire_icon_paint(
    sym: dict, avertissements: list[str], contexte: str,
    *, resoudre_sprite: Callable[[str], str | None] | None = None,
    taille_sprite_px: float = 64.0,
) -> tuple[dict, dict]:
    """IconSymbolizer -> (paint, layout) Mapbox pour une couche "symbol" piloté
    par icon-image. Voir le commentaire précédant cette fonction pour l'état
    complet de la vérification contre l'oracle (icon-image/icon-size/
    icon-opacity/icon-rotate confirmés, icon-offset vérifié cassé)."""
    image = sym.get("image")
    if isinstance(image, dict):
        raise ExpressionPivotNonEcrite(
            f"{contexte} : IconSymbolizer.image sous forme Sprite (sprite sheet) non "
            f"écrit par cette itération — seule une image simple (chemin/URL/base64, "
            f"str) l'est."
        )
    if image is None:
        raise ExpressionPivotNonEcrite(f"{contexte} : IconSymbolizer sans image (image=None).")
    if not isinstance(image, str):
        raise ExpressionPivotNonEcrite(
            f"{contexte} : IconSymbolizer.image={image!r} n'est pas une chaîne — seule "
            f"cette forme est écrite par cette itération."
        )
    if resoudre_sprite is None:
        raise ExpressionPivotNonEcrite(
            f"{contexte} : IconSymbolizer.image={image!r} non écrit — icon-image Mapbox "
            f"référence TOUJOURS un NOM de vignette déjà enregistré dans le sprite du "
            f"style (jamais un chemin/URL/base64 arbitraire, contrairement à "
            f"ExternalGraphic côté SLD) : aucun résolveur 'resoudre_sprite' fourni à "
            f"ecrire_mbstyle() pour nommer et enregistrer cette image dans la feuille "
            f"de sprites."
        )
    nom_sprite = resoudre_sprite(image)
    if not nom_sprite:
        raise ExpressionPivotNonEcrite(
            f"{contexte} : IconSymbolizer.image={image!r} — le résolveur de sprite "
            f"fourni n'a pas su le nommer (a renvoyé None/vide) ; non écrit plutôt que "
            f"de référencer un icon-image inexistant dans la feuille de sprites."
        )
    layout: dict[str, Any] = {"icon-image": str(nom_sprite)}
    paint: dict[str, Any] = {}
    if sym.get("size") is not None:
        taille = _valeur_symbolizer_litterale(sym["size"], contexte, "size")
        if not isinstance(taille, (int, float)) or isinstance(taille, bool):
            raise ExpressionPivotNonEcrite(
                f"{contexte} : size={taille!r} n'est pas un nombre littéral — seul ce "
                f"cas est écrit par cette itération."
            )
        if not taille_sprite_px:
            raise ExpressionPivotNonEcrite(
                f"{contexte} : size={taille!r} renseigné mais taille_sprite_px="
                f"{taille_sprite_px!r} (nul ou absent) — impossible de calculer le "
                f"facteur d'échelle icon-size sans connaître la taille native des "
                f"vignettes de la feuille de sprites effectivement utilisée."
            )
        layout["icon-size"] = taille / float(taille_sprite_px)
    if sym.get("opacity") is not None:
        paint["icon-opacity"] = _valeur_symbolizer_litterale(sym["opacity"], contexte, "opacity")
    if sym.get("rotate") is not None:
        layout["icon-rotate"] = _valeur_symbolizer_litterale(sym["rotate"], contexte, "rotate")
    if sym.get("offset") is not None:
        avertissements.append(
            f"{contexte} : offset={sym['offset']!r} NON écrit — vérifié contre l'oracle "
            f"QGIS (QgsMapBoxGlStyleConverter) qu'icon-offset, bien que syntaxiquement "
            f"accepté par le document, N'AFFECTE PAS le symbolLayer résultant (icon-"
            f"offset=[5,-3] -> offset() reste '0,0' après conversion) : un écart RÉEL "
            f"découvert en testant, pas une limite de conception de ce module."
        )
    _avertir_proprietes_non_gerees(
        sym, {"image", "size", "opacity", "rotate", "offset"}, avertissements, contexte,
    )
    return paint, layout


_ECRIVAINS_SYMBOLIZER_PAINT = {
    "Fill": ("fill", _ecrire_fill_paint),
    "Line": ("line", _ecrire_line_paint),
    "Mark": ("circle", _ecrire_mark_paint),
    "Text": ("symbol", _ecrire_text_paint),
}


# --------------------------------------------------------------------------- filtres (pivot Filter -> expression Mapbox)
#: Ces 6 opérateurs de comparaison pivot (forme TUPLE, ["==", gauche, droite])
#: ont, vérifié contre geostyler-mapbox-parser (lecture indépendante d'un
#: filtre Mapbox écrit à la main vers son propre pivot intermédiaire), des
#: noms d'opérateur Mapbox IDENTIQUES, caractère pour caractère : pas de
#: table de correspondance à inventer, contrairement à SLD (qui traduit vers
#: PropertyIsEqualTo etc). PAS encore contre-vérifié contre l'oracle QGIS
#: (QgsMapBoxGlStyleConverter) au moment d'écrire ce module — voir
#: l'avertissement de couverture de la docstring de module.
_CMP_TUPLE_MAPBOX = {"==", "!=", "<", "<=", ">", ">="}
_CMP_DICT_VERS_MAPBOX = {
    "equalTo": "==", "notEqualTo": "!=", "lessThan": "<",
    "lessThanOrEqualTo": "<=", "greaterThan": ">", "greaterThanOrEqualTo": ">=",
}


def _valeur_filtre_mapbox(valeur: Any, contexte: str) -> Any:
    """Traduit un OPÉRANDE de filtre pivot (littéral, ou Fproperty) vers sa
    forme Mapbox. Fproperty {"name":"property","args":[champ]} -> ["get",
    champ] : "get" est le nom d'opérateur RÉEL de la spec Mapbox GL Style
    Expressions (pas "property", qui n'existe pas côté Mapbox) — confirmé à
    la fois par la spec elle-même et par la lecture indépendante de
    geostyler-mapbox-parser (qui produit aussi ["get", ...] en lisant un
    filtre Mapbox écrit à la main). Rien d'autre qu'un littéral ou Fproperty
    n'est traduit par cette itération (même restriction que
    _construire_element_valeur côté SLD pour les opérandes de FILTRE — la
    restriction sur les VALEURS DE SYMBOLIZER, elle, est distincte et gérée
    par _valeur_symbolizer_litterale)."""
    if isinstance(valeur, dict) and valeur.get("name") == "property":
        args = valeur.get("args", [])
        if len(args) == 1:
            return ["get", str(args[0])]
        raise ExpressionPivotNonEcrite(
            f"{contexte} : property(...) attend exactement 1 argument, {len(args)} reçus."
        )
    if isinstance(valeur, dict):
        raise ExpressionPivotNonEcrite(
            f"{contexte} : opérande de filtre {valeur.get('name', '?')!r} non écrit "
            f"par cette itération (seuls les littéraux et Fproperty le sont)."
        )
    return valeur


def _nom_champ_simple(valeur: Any, contexte: str) -> str:
    """Extrait le nom de champ NU d'un Fproperty pivot (pas la forme
    ["get", champ] de _valeur_filtre_mapbox — "has"/"!has" côté Mapbox
    attendent le nom de propriété en second élément DIRECTEMENT, une chaîne,
    pas une expression ["get", ...] imbriquée, vérifié contre l'oracle :
    ["has", "cls"] fonctionne, un ["get", "cls"] à la place n'a pas été
    testé et n'est de toute façon pas la syntaxe que "has" attend selon la
    spec)."""
    if isinstance(valeur, dict) and valeur.get("name") == "property":
        args = valeur.get("args", [])
        if len(args) == 1:
            return str(args[0])
    raise ExpressionPivotNonEcrite(
        f"{contexte} : IS [NOT] NULL n'est écrit que pour un Fproperty nu en "
        f"opérande gauche — {valeur!r} n'en est pas un."
    )


#: EXTENSION du 2026-10-12 (à la demande explicite de l'utilisateur, reprise
#: après un premier passage qui avait exclu LIKE/ILIKE par prudence — voir
#: ci-dessous pourquoi ce n'est plus nécessaire pour les 4 formes à un seul
#: segment littéral) : la spec Mapbox GL Expressions n'a certes AUCUN
#: opérateur de correspondance par motif générique (pas de wildCard/
#: singleChar comme ogc:PropertyIsLike), mais ELLE A les briques nécessaires
#: pour reconstruire, SANS AUCUNE AMBIGUÏTÉ, les 4 formes LIKE à un seul
#: segment littéral : "slice" (sous-chaîne par position), "length"
#: (longueur), "downcase" (ILIKE) et "in" (recherche de sous-chaîne native,
#: PAS la même forme que l'opérateur "in" déjà écrit par ce module pour
#: Fin — ici le second opérande est une STRING, pas ["literal", [...]]).
#: Portée délibérément bornée à CES 4 formes (exact/préfixe/suffixe/
#: contient un UNIQUE segment littéral) : un motif à plusieurs segments
#: ("a%b%c") ou utilisant le joker '_' (position par position) demanderait
#: de chaîner plusieurs recherches ou de construire caractère par caractère
#: — non construit ni vérifié cette itération, lève ExpressionPivotNonEcrite
#: plutôt que de deviner.
#:
#: VÉRIFIÉ, mais PAS contre l'oracle PRINCIPAL habituel de ce module
#: (QgsMapBoxGlStyleConverter) : celui-ci NE SAIT TOUT SIMPLEMENT PAS
#: interpréter "slice"/"downcase" ("Skipping unsupported expression
#: 'slice'"/'downcase'", testé directement), et produit un filtre QGIS
#: TRONQUÉ/CASSÉ en conséquence (ex. filterExpression() == " IS 'a1-'",
#: opérande gauche silencieusement perdue) — un constat attendu, pas une
#: alerte sur CE module : QGIS Desktop n'est qu'UN client Mapbox GL parmi
#: d'autres et sa propre réimplémentation C++ de la spec est PARTIELLE,
#: alors que la cible réelle de ce document (GeoServer + un client web
#: conforme à la spec, Mapbox GL JS ou MapLibre GL JS) l'interprète
#: nativement. Vérifié à la place contre un oracle SECONDAIRE plus adapté
#: ICI et plus AUTORITATIF pour CETTE question précise — pas un pis-aller :
#: @maplibre/maplibre-gl-style-spec (le paquet npm qui EST la spec de
#: référence, partagée par Mapbox GL JS et MapLibre GL JS), sa fonction
#: featureFilter() — littéralement le même code qui évalue le 'filter'
#: d'une couche dans un client réel — appelée sur les 4 formes produites
#: ici avec des features de test (dont les cas limites : champ absent,
#: chaîne plus courte que le segment recherché) : toutes les 4 renvoient
#: exactement le booléen attendu, y compris sur les limites (ex. slice sur
#: une chaîne plus courte que le motif ne lève jamais, se compare juste
#: comme inégale), et un champ absent (null) retombe sur False sans
#: exception, jamais sur "corresponds à tout".
def _classifier_motif_like(motif: str) -> tuple[str, str] | None:
    """Reconnaît, dans un motif SQL-LIKE déjà décodé par
    _detecter_motif_like_depuis_regex (où '%'/'_' sont TOUJOURS des jokers,
    jamais des caractères littéraux — ce projet ne produit pas de LIKE avec
    caractère d'échappement, voir sa docstring), l'une des 4 formes à un
    SEUL segment littéral que ce module sait traduire : 'exact' (pas de
    joker), 'prefix' ('lit%'), 'suffix' ('%lit'), 'contains' ('%lit%').
    Retourne (forme, littéral), ou None si le motif sort de ce périmètre
    (joker '_', ou '%' ailleurs qu'aux deux bornes, ou plus de 2 '%') —
    l'appelant lève alors ExpressionPivotNonEcrite, jamais une
    approximation sur une forme non reconnue."""
    if "_" in motif:
        return None
    n = motif.count("%")
    if n == 0:
        return ("exact", motif)
    if n == 1:
        if motif.startswith("%"):
            return ("suffix", motif[1:])
        if motif.endswith("%"):
            return ("prefix", motif[:-1])
        return None  # '%' isolé au milieu d'un motif à un seul joker : "a%b"
    if n == 2 and motif.startswith("%") and motif.endswith("%"):
        interieur = motif[1:-1]
        if "%" not in interieur:
            return ("contains", interieur)
    return None


def _construire_motif_like_mapbox(operande: Any, regex: Any, contexte: str) -> Any:
    """strMatches(operande, regex) pivot -> expression booléenne Mapbox GL,
    pour les 4 formes LIKE/ILIKE à un seul segment littéral reconnues par
    _classifier_motif_like (voir le commentaire précédant cette fonction
    pour l'état complet de la vérification). Lève ExpressionPivotNonEcrite
    pour tout le reste (regex non canonique, motif à plusieurs segments ou
    avec '_') plutôt que d'approximer."""
    if not isinstance(regex, str):
        raise ExpressionPivotNonEcrite(
            f"{contexte} : strMatches(..., {regex!r}) non écrit — second argument non textuel."
        )
    detecte = _detecter_motif_like_depuis_regex(regex)
    if detecte is None:
        raise ExpressionPivotNonEcrite(
            f"{contexte} : strMatches(..., {regex!r}) non écrit — cette regex ne correspond "
            f"pas à la forme canonique que produit LIKE/ILIKE dans ce projet "
            f"(styleforge_core.readers.expressions._motif_like_vers_regex), seule "
            f"reconvertible sans supposition vers un motif SQL-LIKE."
        )
    motif, insensible = detecte
    classifie = _classifier_motif_like(motif)
    if classifie is None:
        raise ExpressionPivotNonEcrite(
            f"{contexte} : strMatches(..., motif SQL-LIKE {motif!r}) non écrit — seules les "
            f"formes à UN SEUL segment littéral (exact/préfixe/suffixe/contient, ex. "
            f"\"a1-%\"/\"%abc%\") sont traduites par cette itération ; un motif à joker '_' "
            f"ou à plusieurs segments ('a%b%c') demanderait de chaîner plusieurs recherches, "
            f"non construit ni vérifié ici — voir _classifier_motif_like."
        )
    forme, litteral = classifie
    champ = _valeur_filtre_mapbox(operande, contexte)
    if insensible:
        champ = ["downcase", champ]
        litteral = litteral.lower()
    if forme == "exact":
        return ["==", champ, litteral]
    if forme == "prefix":
        return ["==", ["slice", champ, 0, len(litteral)], litteral]
    if forme == "suffix":
        return ["==", ["slice", champ, ["-", ["length", champ], len(litteral)]], litteral]
    # forme == "contains" : "in" Mapbox cherche nativement une sous-chaîne
    # (second opérande string, PAS ["literal", [...]] comme pour Fin — forme
    # distincte, voir le commentaire précédant cette fonction).
    return ["in", litteral, champ]


def _construire_filtre_mapbox(filtre: Any, avertissements: list[str], contexte: str) -> Any:
    """Traduit un Filter pivot (mêmes formes TUPLE/DICT que
    styleforge_core.writers.sld._construire_filtre, voir sa docstring) vers
    une expression Mapbox GL (liste JSON imbriquée). LIKE/ILIKE : voir
    _construire_motif_like_mapbox (4 formes à un seul segment littéral).

    PAS de négation générale ("!"/"not" pivot sur un sous-filtre arbitraire)
    NON PLUS — DÉCOUVERTE EN TESTANT CONTRE L'ORACLE QGIS, pas supposée :
    QgsMapBoxGlStyleConverter accepte ["!", ["has", champ]] et
    ["!", ["in", ...]] (avertissement aucun, filtre correctement reconstruit
    — "cls" IS NULL / "... NOT IN (...)"), mais ["!", ["==", ...]] ET
    ["!", ["all"/"any", ...]] sont tous les deux EXPLICITEMENT rejetés par
    warnings ('Skipping unsupported expression "!=="' / '"!all"'), avec pour
    conséquence la perte SILENCIEUSE de la Rule entière : filterExpression()
    revient vide, ce qui revient à faire correspondre TOUTES les entités
    plutôt que le sous-ensemble voulu — un vrai risque de correction, pas
    juste une construction manquante. Le support de "!" est donc PARTIEL et
    dépend de ce qu'il enveloppe, un motif trop incohérent pour l'exposer de
    façon générale cette itération : la négation générale lève
    ExpressionPivotNonEcrite, tandis que IS NULL / IS NOT NULL (le seul
    besoin de négation de cette itération) est construit directement avec
    has/!has plutôt que de passer par une négation générique."""
    filtre = _normaliser(filtre)
    if isinstance(filtre, list):
        op = filtre[0]
        if op in _CMP_TUPLE_MAPBOX:
            if len(filtre) != 3:
                raise ExpressionPivotNonEcrite(
                    f"{contexte} : comparaison {filtre!r} attend 3 éléments, {len(filtre)} reçus."
                )
            return [op, _valeur_filtre_mapbox(filtre[1], contexte), _valeur_filtre_mapbox(filtre[2], contexte)]
        if op == "&&":
            return ["all", *(_construire_filtre_mapbox(f, avertissements, contexte) for f in filtre[1:])]
        if op == "||":
            return ["any", *(_construire_filtre_mapbox(f, avertissements, contexte) for f in filtre[1:])]
        if op == "!":
            raise ExpressionPivotNonEcrite(
                f"{contexte} : '!' (négation générale) non écrit par cette itération — "
                f"vérifié contre l'oracle QGIS que ['!', ['==',...]] et ['!', ['all'/'any',...]] "
                f"sont rejetés et font perdre TOUTE la Rule en silence (filtre vide -> "
                f"correspond à tout), voir la docstring de _construire_filtre_mapbox."
            )
        if op == "*=":
            raise ExpressionPivotNonEcrite(
                f"{contexte} : '*=' (LIKE) non écrit par cette itération — aucun "
                f"opérateur de correspondance par motif générique dans la spec Mapbox "
                f"GL Expressions (voir la docstring de _construire_filtre_mapbox)."
            )
        raise ExpressionPivotNonEcrite(f"{contexte} : opérateur de filtre tuple {op!r} non écrit par cette itération.")
    if isinstance(filtre, dict) and "name" in filtre:
        nom = filtre["name"]
        args = filtre.get("args", [])
        if nom in ("equalTo", "notEqualTo") and len(args) == 2 and args[1] is None:
            # IS [NOT] NULL : ["==", ["get",champ], null] — la forme
            # produite par geostyler-mapbox-parser en LECTURE (oracle
            # secondaire) — a été VÉRIFIÉE CASSÉE contre l'oracle PRINCIPAL :
            # QgsMapBoxGlStyleConverter émet "Passe la partie d'expression
            # non supportée" et reconstruit un filtre TRONQUÉ ('"cls" IS ',
            # sans rien après IS, une expression QGIS invalide). La forme
            # QUI FONCTIONNE, vérifiée : ["has", champ] pour IS NOT NULL
            # (-> '"champ" IS NOT NULL' exact) et ["!", ["has", champ]] pour
            # IS NULL (-> '"champ" IS NULL' exact) — un des rares cas où "!"
            # EST accepté par le convertisseur (voir la docstring de
            # _construire_filtre_mapbox pour l'étendue exacte, très partielle,
            # de ce support).
            champ = _nom_champ_simple(args[0], contexte)
            return ["has", champ] if nom == "notEqualTo" else ["!", ["has", champ]]
        if nom in _CMP_DICT_VERS_MAPBOX:
            if len(args) != 2:
                raise ExpressionPivotNonEcrite(f"{contexte} : {nom}(...) attend 2 arguments, {len(args)} reçus.")
            return [_CMP_DICT_VERS_MAPBOX[nom], _valeur_filtre_mapbox(args[0], contexte), _valeur_filtre_mapbox(args[1], contexte)]
        if nom == "all":
            return ["all", *(_construire_filtre_mapbox(f, avertissements, contexte) for f in args)]
        if nom == "any":
            return ["any", *(_construire_filtre_mapbox(f, avertissements, contexte) for f in args)]
        if nom == "not":
            # Miroir du cas tuple "!" (voir plus haut) : vérifié contre l'oracle
            # QGIS que "!" n'est fiable QUE devant ["has", champ] ou ["in", ...]
            # (double négation ["!", ["!", ...]] comprise -> rejetée aussi, car
            # le "!" externe se retrouverait devant un ["!", ...], pas un "has"/"in").
            # Devant une comparaison ou un all/any, QgsMapBoxGlStyleConverter
            # rejette l'expression et le filtre entier disparaît silencieusement
            # (correspond alors à TOUTES les features) — donc on ne traduit QUE
            # les formes vérifiées sûres, et on lève pour tout le reste plutôt
            # que de risquer ce silence.
            if len(args) != 1:
                raise ExpressionPivotNonEcrite(
                    f"{contexte} : not(...) attend exactement 1 argument, {len(args)} reçus."
                )
            interieur = _construire_filtre_mapbox(args[0], avertissements, contexte)
            if isinstance(interieur, list) and interieur and interieur[0] in ("has", "in"):
                return ["!", interieur]
            raise ExpressionPivotNonEcrite(
                f"{contexte} : not(...) non écrit par cette itération pour ce filtre interne — "
                f"vérifié contre l'oracle QGIS que '!' n'est fiable que devant 'has' ou 'in' "
                f"(voir la docstring de _construire_filtre_mapbox) ; toute autre négation "
                f"(comparaison, all, any, double négation) est rejetée par "
                f"QgsMapBoxGlStyleConverter et fait perdre le filtre entier en silence "
                f"(correspond alors à tout)."
            )
        if nom == "between":
            if len(args) != 3:
                raise ExpressionPivotNonEcrite(
                    f"{contexte} : between(...) attend exactement 3 arguments (valeur, min, max), "
                    f"{len(args)} reçus."
                )
            valeur, mini, maxi = (_valeur_filtre_mapbox(a, contexte) for a in args)
            # Pas d'opérateur BETWEEN natif côté Mapbox (comme côté OGC
            # Filter avant la découverte de PropertyIsBetween — mais Mapbox,
            # lui, n'a vraiment aucun équivalent, vérifié dans la spec) :
            # reconstruit en AND de deux comparaisons, même sémantique que
            # documentée pour Fbetween ("min <= valeur <= max").
            return ["all", [">=", valeur, mini], ["<=", valeur, maxi]]
        if nom == "in":
            if len(args) < 2:
                raise ExpressionPivotNonEcrite(f"{contexte} : in(...) attend au moins 2 arguments (propriété, valeur...).")
            operande, *valeurs = args
            # ["in", operande, ["literal", [v1, v2, ...]]] : forme CONFIRMÉE
            # par la lecture indépendante de geostyler-mapbox-parser (un
            # filtre IN écrit à la main produit exactement cette forme dans
            # son pivot). L'opérateur "in" Mapbox est natif (contrairement à
            # OGC Filter, où IN doit être reconstruit en OR).
            return ["in", _valeur_filtre_mapbox(operande, contexte), ["literal", [_valeur_filtre_mapbox(v, contexte) for v in valeurs]]]
        if nom == "strMatches":
            if len(args) != 2:
                raise ExpressionPivotNonEcrite(f"{contexte} : strMatches(...) attend 2 arguments, {len(args)} reçus.")
            operande, regex = args
            return _construire_motif_like_mapbox(operande, regex, contexte)
        raise ExpressionPivotNonEcrite(f"{contexte} : fonction booléenne pivot {nom!r} non écrite par cette itération.")
    raise ExpressionPivotNonEcrite(f"{contexte} : forme de filtre pivot non reconnue : {filtre!r}")


# --------------------------------------------------------------------------- rule -> layer(s)
#: EXTENSION du 2026-10-12 (à la demande explicite de l'utilisateur de
#: maximiser la compatibilité plutôt que d'échouer) : une Rule à N>1
#: symbolizers n'est plus un échec dur — elle écrit N couches Mapbox
#: DISTINCTES (même filtre, même source-layer, un id suffixé "-0".."-N-1"),
#: dans l'ORDRE du pivot. Ce n'est PAS une approximation : contrairement à
#: SLD (où un FeatureTypeStyle QGIS fusionne les symbolizers d'une même Rule
#: en UN SEUL élément de rendu, ce qui forçait déjà l'écrivain SLD à les
#: empiler dans un seul <Rule>), Mapbox GL Style n'a structurellement AUCUNE
#: notion de "symbolizers multiples d'une même règle" : chaque couche
#: ("layer") de la liste est TOUJOURS indépendante, donc rien à fusionner —
#: le pivot standard geostyler-style documente d'ailleurs chaque Rule.
#: symbolizers comme une liste précisément pour ce cas. CONFIRMÉ CONTRE
#: L'ORACLE PRINCIPAL (QgsMapBoxGlStyleConverter) : un document à 2 couches
#: partageant exactement le même filtre et le même source-layer (fill +
#: line) donne convert()==0 (aucune erreur), et renderer().styles() contient
#: bien 2 QgsVectorTileBasicRendererStyle INDÉPENDANTS, tous deux avec le
#: filtre attendu — pas de rejet de doublon, pas de fusion/écrasement. SEUL
#: point non re-vérifié indépendamment : l'ORDRE DE SUPERPOSITION visuel
#: exact (painter's algorithm) au-delà de la simple coexistence des deux
#: styles — à confirmer par un rendu GeoServer réel si cet ordre importe.
def _ecrire_layers(
    rule: dict, index: int, id_source: str, nom_couche_source: str, avertissements: list[str],
    *, resoudre_sprite: Callable[[str], str | None] | None = None,
    taille_sprite_px: float = 64.0,
) -> list[dict]:
    rule = _normaliser(rule)
    contexte_rule = f"Rule[{index}] ({rule.get('name') or 'sans nom'})"
    if rule.get("elseRule"):
        raise ExpressionPivotNonEcrite(
            f"{contexte_rule} : Rule.elseRule non écrit par cette itération — contrairement "
            f"à SLD (ElseFilter, un mécanisme natif du moteur de règles), Mapbox GL "
            f"Style n'a aucune notion d'\"else\" : chaque couche est indépendante et "
            f"évaluée par son propre filtre. Reproduire elseRule demanderait de "
            f"collecter les filtres de TOUTES les Rule sœurs et d'en écrire la "
            f"négation combinée — une transformation à part, non construite ni "
            f"vérifiée par cette itération, pas une simple traduction 1:1."
        )
    symbolizers = rule.get("symbolizers") or []
    if not symbolizers:
        raise ExpressionPivotNonEcrite(f"{contexte_rule} : Rule sans symbolizer (symbolizers vide).")

    filtre_mapbox = None
    if rule.get("filter") is not None:
        filtre_mapbox = _construire_filtre_mapbox(rule["filter"], avertissements, contexte_rule)

    id_base = rule.get("name") or f"layer-{index}"
    couches: list[dict] = []
    for j, symbolizer in enumerate(symbolizers):
        sym = _normaliser(symbolizer)
        kind = sym.get("kind")
        contexte = f"{contexte_rule}.symbolizers[{j}]"
        if kind == "Icon":
            type_layer = "symbol"
            paint, layout = _ecrire_icon_paint(
                sym, avertissements, contexte,
                resoudre_sprite=resoudre_sprite, taille_sprite_px=taille_sprite_px,
            )
        else:
            entree = _ECRIVAINS_SYMBOLIZER_PAINT.get(kind)
            if entree is None:
                raison_supplementaire = ""
                if kind == "Raster":
                    raison_supplementaire = (
                        " (RasterSymbolizer : une couche Mapbox \"raster\" doit référencer une "
                        "SOURCE de type \"raster\" (tuiles image), alors que ecrire_mbstyle() "
                        "de cette itération ne construit qu'UNE seule source, de type "
                        "\"vector\", partagée par toutes les couches — mélanger les deux "
                        "demanderait un paramètre de sources MULTIPLES/typées, une extension "
                        "de conception à part, pas encore construite)"
                    )
                raise ExpressionPivotNonEcrite(
                    f"{contexte} : symbolizer de type {kind!r} non écrit par cette "
                    f"itération de l'écrivain MBStyle (Fill/Line/Mark(circle, ou "
                    f"approximé)/Text/Icon le sont — voir la docstring de "
                    f"styleforge_core.writers.mbstyle){raison_supplementaire}."
                )
            type_layer, ecrivain_paint = entree
            # resoudre_sprite est accepté (et ignoré) par Mark/Text pour une
            # convention d'appel uniforme — seuls Fill (graphicFill) et Line
            # (graphicFill/graphicStroke) s'en servent, voir
            # _resoudre_motif_sprite.
            paint, layout = ecrivain_paint(sym, avertissements, contexte, resoudre_sprite=resoudre_sprite)
        id_layer = f"{id_base}-{j}" if len(symbolizers) > 1 else id_base
        layer: dict[str, Any] = {
            "id": id_layer, "type": type_layer, "source": id_source, "source-layer": nom_couche_source,
        }
        if filtre_mapbox is not None:
            layer["filter"] = filtre_mapbox
        if layout:
            layer["layout"] = layout
        layer["paint"] = paint
        couches.append(layer)

    if len(symbolizers) > 1:
        avertissements.append(
            f"{contexte_rule} : {len(symbolizers)} symbolizers empilés en autant de "
            f"couches Mapbox distinctes (id {id_base}-0..{len(symbolizers) - 1}), même "
            f"filtre et source-layer, dans l'ORDRE du pivot — coexistence confirmée "
            f"contre l'oracle QGIS (QgsMapBoxGlStyleConverter), voir le commentaire "
            f"précédant _ecrire_layers ; l'ordre de superposition visuel exact n'est, "
            f"lui, pas re-vérifié indépendamment — à confirmer par un rendu GeoServer "
            f"réel si cet ordre importe."
        )
    return couches


def ecrire_mbstyle(
    style: Any,
    *,
    id_source: str,
    url_source: str,
    nom_couche_source: str,
    avertissements: list[str] | None = None,
    resoudre_sprite: Callable[[str], str | None] | None = None,
    taille_sprite_px: float = 64.0,
) -> str:
    """Traduit un Style pivot (dict canonique validé par valider_style(), ou
    instance pydantic du modèle généré) en un document Mapbox GL Style Spec
    (JSON, version 8) complet (str). id_source/url_source/nom_couche_source
    sont des PARAMÈTRES OBLIGATOIRES (pas de valeur supposée : le pivot ne
    contient aucune information de source de tuiles, c'est un choix de
    contexte de rendu — principe évolutif du projet) ; le document["name"]
    Mapbox, lui, vient directement de style.name quand il est renseigné —
    même convention que le Title de l'écrivain SLD (ecrire_sld), qui vient
    aussi de style.name plutôt que d'un paramètre séparé : c'est un champ du
    PIVOT (le nom du style lui-même), pas un choix de contexte de rendu.

    Une Rule peut désormais contenir PLUSIEURS symbolizers (empilés en
    autant de couches Mapbox distinctes, voir _ecrire_layers) et un
    MarkSymbolizer de forme non circulaire est APPROXIMÉ en couche "circle"
    plutôt que rejeté (voir _ecrire_mark_paint) — les deux avec un
    avertissement explicite, jamais silencieux (extension du 2026-10-12, à
    la demande explicite de l'utilisateur de maximiser la compatibilité du
    corpus réel plutôt que d'échouer).

    'resoudre_sprite' (optionnel) : callback symétrique de
    'resoudre_image_embarquee' côté écrivain SLD, nécessaire pour écrire tout
    IconSymbolizer — icon-image Mapbox référence TOUJOURS un nom de vignette
    déjà enregistrée dans LA feuille de sprites du style, jamais une URL/
    chemin/base64 arbitraire (voir _ecrire_icon_paint) : appelé avec
    IconSymbolizer.image brut, doit renvoyer le nom de vignette à écrire (ou
    None s'il ne sait pas l'enregistrer). Sans résolveur fourni (ou s'il
    renvoie None), tout IconSymbolizer lève ExpressionPivotNonEcrite plutôt
    que d'écrire un icon-image orphelin. 'taille_sprite_px' : taille native
    (en pixels) des vignettes de CETTE feuille de sprites — un choix de
    contexte de rendu, jamais une information du pivot — utilisée pour
    convertir IconSymbolizer.size (une taille absolue) en icon-size (un
    facteur d'échelle Mapbox, voir _ecrire_icon_paint pour la vérification
    oracle de cette distinction).

    Lève ExpressionPivotNonEcrite si une Rule, un filtre ou un symbolizer
    sort de la portée bornée décrite en tête de module. 'avertissements'
    peut être fourni pour récupérer les propriétés de symbolizer non
    écrites — jamais perdues en silence, seulement omises du document avec
    une trace."""
    style = _normaliser(style)
    avertissements = avertissements if avertissements is not None else []

    document: dict[str, Any] = {
        "version": 8,
        "sources": {
            id_source: {"type": "vector", "url": url_source},
        },
        "layers": [],
    }
    if style.get("name"):
        document["name"] = str(style["name"])

    for i, rule in enumerate(style.get("rules") or []):
        document["layers"].extend(_ecrire_layers(
            rule, i, id_source, nom_couche_source, avertissements,
            resoudre_sprite=resoudre_sprite, taille_sprite_px=taille_sprite_px,
        ))

    return _json.dumps(document, indent=2, ensure_ascii=False) + "\n"
