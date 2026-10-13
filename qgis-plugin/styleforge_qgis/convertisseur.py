# -*- coding: utf-8 -*-
"""Pont entre les objets QGIS (QgsVectorLayer, QgsProject, fichiers .qml
sur disque) et styleforge-core.

Principe herite du CLI (cnig_qml2sld_geoserver.py, StyleforgeBackend.
convert()) et de son correctif du 2026-10-12 (voir examples/
rapport_conversion.md et son historique) : chaque avertissement est
prefixe par le document concerne - "Lecture QML :" (pivot, commun
SLD+MBStyle), "SLD :" (ecrivain SLD), "MBStyle :" (ecrivain MBStyle) -
et plus loin, lors de l'affichage, chaque categorie est echantillonnee
SEPAREMENT plutot que de se faire masquer par une autre categorie plus
nombreuse. Reproduire cette convention ici, plutot qu'en inventer une
differente, evite de recreer le meme bug que celui corrige dans le CLI.

DEPUIS LA VERSION 0.2.0, ce module partage trois blocs de code avec le
CLI via styleforge-core (meme principe que styleforge_core.readers.qml/
writers.sld/writers.mbstyle deja partages depuis la 0.1.0) :

  * styleforge_core.writers.sld_posttraitement.post_traiter_sld() -
    PHASE 4 du CLI (nettoyage des balises propriétaires QGIS/ESRI,
    réécriture des références SVG, correction des WellKnownName,
    réparation fidèle des hachures/tirets, injection des VendorOption
    GeoServer, repli des expressions constantes, suppression des
    éléments vides, remise en ordre XSD) - appliquée ici à CHAQUE SLD
    produit, APRES deploiement des SVG (voir le pipeline plus bas).
  * styleforge_core.sprites.SpriteRegistry - fabrication de la feuille
    de sprites Mapbox (sprite.png/@2x + index JSON) pour les documents
    MBStyle, meme logique que le PHASE 5 du CLI (backend styleforge).
  * styleforge_core.writers.sld_posttraitement.{VENDOR_DEFAULTS,
    NOMS_MARQUEURS_QGIS_VERS_WKN} - memes valeurs par defaut que le CLI
    non reconfigure, pour rester coherent avec lui.

RESOLUTION DES SVG (etendue en 0.2.0) : les pictogrammes SVG EMBARQUES
EN BASE64 dans le QML (convention QGIS 'base64:...', cas de la quasi-
totalite du corpus CNIG reel) ET un SVG REFERENCE PAR UN CHEMIN DE
FICHIER (relatif au .qml source, au dossier du projet QGIS, ou absolu)
sont tous deux decodes/copies et materialises dans svg/cnig/ du dossier
de sortie, memes conventions que SVG_SUBDIR du CLI. Un chemin qui ne
mene a aucun fichier reel produit un AVERTISSEMENT EXPLICITE nommant le
chemin essaye, jamais une approximation silencieuse ; le symbolizer
correspondant echoue alors avec ExpressionPivotNonEcrite, comme avant.

Les sprites MBStyle (pictogrammes/motifs/glyphes pour l'ecrivain
MBStyle) sont desormais generes eux aussi (SpriteRegistry, partagee avec
le CLI) - derniere limite "connue" de la 0.1.0 a etre levee. Qt est
TOUJOURS disponible ici (le plugin tourne dans le processus QGIS, qui
EST une application Qt) : aucune sonde de securite par sous-processus
n'est necessaire (voir la docstring de styleforge_core.sprites)."""
from __future__ import annotations

import base64
import hashlib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

from styleforge_core.sprites import SpriteRegistry
from styleforge_core.writers.sld_posttraitement import (
    NOMS_MARQUEURS_QGIS_VERS_WKN,
    VENDOR_DEFAULTS,
    post_traiter_sld,
)

PREFIXES_CONNUS = ("Lecture QML : ", "SLD : ", "MBStyle : ")

#: Meme convention que SVG_SUBDIR dans cnig_qml2sld_geoserver.py (et dans
#: styleforge_core.writers.sld_posttraitement) : les .sld produits par ce
#: plugin et par le CLI referencent leurs pictogrammes sous le meme chemin
#: relatif "svg/cnig/<nom>.svg".
SVG_SUBDIR = Path("svg") / "cnig"

# Memes valeurs par defaut que MbStyleOptions dans le CLI (cnig_qml2sld_
# geoserver.py) : un MBStyle produit par ce plugin sans configuration
# GeoServer explicite (hors de portee de l'UI minimale de cette version)
# reste coherent avec ce que produirait le CLI non reconfigure.
MBSTYLE_BASE_URL_DEFAUT = "http://localhost:8080/geoserver"

#: Taille (px) des vignettes de la feuille de sprites MBStyle - meme valeur
#: par defaut que --sprite-size du CLI.
TAILLE_SPRITE_DEFAUT = 64


@dataclass
class ResultatConversion:
    nom: str
    ok: bool = False
    erreur: Optional[str] = None
    avertissements: List[str] = field(default_factory=list)
    sld: Optional[str] = None
    mbstyle: Optional[str] = None
    #: Usage INTERNE au pipeline (voir executer_pipeline) : SLD tel
    #: qu'ecrit par styleforge_core.writers.sld.ecrire_sld(), AVANT la
    #: PHASE 4 (post_traiter_sld) - celle-ci a besoin que les SVG soient
    #: deja deployes sur disque, ce qui n'est vrai qu'une fois TOUTES les
    #: couches/fichiers de ce lot convertis une premiere fois. `.sld`
    #: reste None jusqu'a ce que la PHASE 4 ait ete appliquee.
    sld_brut: Optional[str] = None
    #: Pivot geostyler-style (styleforge_core.pivot.Style ou dict), garde
    #: pour pouvoir generer le MBStyle et resoudre ses sprites dans une
    #: passe ulterieure du pipeline, sans relire le QML une seconde fois.
    pivot_style: Any = None
    #: Chemin du .qml SOURCE (jamais un fichier de sortie) - necessaire a
    #: la PHASE 4, qui le relit pour les indices de rendu (hachures,
    #: tirets) que le pivot ne porte pas. Reste valide jusqu'a la fin du
    #: pipeline meme pour un export temporaire de couche (voir
    #: executer_pipeline, qui ne nettoie ces temporaires qu'a la fin).
    chemin_qml: Optional[Path] = None


class ErreurExportStyleCouche(Exception):
    """La couche QGIS elle-meme n'a pas pu exporter son style en QML
    (saveNamedStyle a signale un echec) - distinct d'un echec de
    styleforge-core, pour que le message affiche a l'utilisateur pointe
    vers la bonne cause."""


def exporter_style_couche_vers_qml(layer) -> Path:
    """Exporte le style COURANT de la couche QGIS vers un fichier .qml
    temporaire, pour le faire relire ensuite par styleforge_core.
    lire_fichier_qml() - styleforge-core ne sait lire qu'un fichier,
    jamais un objet QgsVectorLayer en memoire (et ne doit jamais
    apprendre a le faire : cela introduirait une dependance PyQGIS dans
    styleforge-core, contraire au principe du projet)."""
    import tempfile

    chemin = Path(tempfile.gettempdir()) / f"styleforge_qgis_{id(layer)}.qml"
    message, succes = layer.saveNamedStyle(str(chemin))
    if not succes:
        raise ErreurExportStyleCouche(
            f"QGIS n'a pas pu exporter le style de la couche "
            f"« {layer.name()} » : {message or 'raison non precisee par QGIS'}."
        )
    return chemin


# SUPPRIME EN 0.2.0 : nouveau_registre_svg() - ne servait qu'a fabriquer le
# dict vide passe aux fonctions ci-dessus, elles-memes supprimees (voir la
# note au-dessus de executer_pipeline) ; executer_pipeline construit
# desormais ce registre lui-meme, en interne.


def _resoudre_chemin_svg(
    valeur: str, dossiers_recherche: Sequence[Path],
) -> Tuple[Optional[Path], List[str]]:
    """Tente de localiser sur disque un SVG reference par un CHEMIN DE
    FICHIER (pas du base64) : chemin absolu tel quel, sinon relatif a
    chacun de `dossiers_recherche`, DANS L'ORDRE (le premier dossier est
    le plus probable - typiquement le dossier du .qml source). Retourne
    (chemin_trouve_ou_None, liste_des_chemins_essayes) - la liste permet
    au niveau au-dessus de produire un avertissement PRECIS plutot qu'un
    "fichier introuvable" generique."""
    cleaned = valeur.strip()
    for prefix in ("file:///", "file://", "file:"):
        if cleaned.lower().startswith(prefix):
            cleaned = cleaned[len(prefix):]
            break
    cleaned = cleaned.replace("\\", "/")
    # Parametres GeoServer eventuels (?fill=...) : jamais un nom de fichier.
    if "?" in cleaned:
        cleaned = cleaned.split("?", 1)[0]
    candidat = Path(cleaned)

    essais: List[Path] = []
    if candidat.is_absolute():
        essais.append(candidat)
    else:
        essais.extend(d / candidat for d in dossiers_recherche)

    chemins_essayes = [str(c) for c in essais]
    for c in essais:
        if c.is_file():
            return c, chemins_essayes
    return None, chemins_essayes


def _predeployer_svg_par_chemin(
    pivot: Any,
    registre_svg: Dict[str, bytes],
    index_valeur_vers_nom: Dict[str, str],
    dossiers_recherche: Sequence[Path],
    avertissements: List[str],
) -> None:
    """Parcourt le pivot geostyler-style (instance pydantic ou dict - voir
    lire_fichier_qml) a la recherche de references SVG PAR CHEMIN DE
    FICHIER, et les copie sur disque PROACTIVEMENT, avant l'ecriture du
    SLD.

    NECESSAIRE, et PAS redondant avec le resolveur passe a ecrire_sld (voir
    _fabriquer_resolveur_svg) : styleforge_core.writers.sld.
    _construire_graphic_icon n'appelle ce resolveur QUE pour une valeur
    'image' commencant par 'base64:' (verifie dans le code source de ce
    module - voir sa docstring "cet écrivain est zéro-E/S") ; un chemin de
    fichier est ecrit TEL QUEL (verbatim) dans le SLD, sans jamais passer
    par un callback. La PHASE 4 (post_traiter_sld, partagee avec le CLI)
    reecrit ensuite N'IMPORTE QUEL href vers svg/cnig/<nom_de_base> PAR SON
    SEUL NOM DE FICHIER, QU'UN FICHIER DE CE NOM EXISTE REELLEMENT A CET
    ENDROIT OU NON (cf. styleforge_core.writers.sld_posttraitement.
    resoudre_href_svg - "absent du dépôt : on pointe quand même au bon
    endroit"). Sans ce pre-deploiement, un SLD produit par ce plugin
    pointerait donc vers un fichier jamais copie, SANS LE DIRE. Ce parcours
    rend l'absence EXPLICITE (avertissement nommant le chemin essaye)
    plutot que silencieuse, et deploie reellement le fichier quand il est
    trouve, pour que la PHASE 4 pointe vers un fichier qui existe vraiment.

    Parcours GENERIQUE (recursif sur tout dict/liste imbrique) plutot que
    cible sur un type de symbolizer precis : IconSymbolizer.image ET les
    graphicFill/graphicStroke de motifs (SVGFill) partagent la MEME cle
    pivot "image" (voir styleforge_core.writers.sld, _construire_graphic_
    icon, reutilisee par les deux) - un parcours generique couvre les deux
    sans dependre de la forme exacte du pivot, qui reste un detail
    d'implementation de styleforge-core."""
    brut = pivot.model_dump() if hasattr(pivot, "model_dump") else pivot

    def _traiter(valeur: str) -> None:
        valeur = valeur.strip()
        if not valeur or valeur.lower().startswith("base64:"):
            return
        if not valeur.split("?", 1)[0].lower().endswith(".svg"):
            return
        if valeur in index_valeur_vers_nom:
            return
        trouve, chemins_essayes = _resoudre_chemin_svg(valeur, dossiers_recherche)
        if trouve is None:
            avertissements.append(
                f"SVG référencé par chemin de fichier introuvable : « {valeur} » "
                f"(essayé : {', '.join(chemins_essayes) or 'aucun dossier de recherche'})."
            )
            return
        try:
            charge_utile = trouve.read_bytes()
        except OSError as exc:
            avertissements.append(f"SVG illisible ({trouve}) : {exc}")
            return
        nom_fichier = trouve.name
        existant = registre_svg.get(nom_fichier)
        if existant is not None and existant != charge_utile:
            avertissements.append(
                f"Pictogrammes homonymes de contenu différent : « {nom_fichier} » "
                f"— la première version rencontrée est conservée."
            )
        else:
            registre_svg.setdefault(nom_fichier, charge_utile)
        index_valeur_vers_nom[valeur] = nom_fichier

    def _parcourir(noeud: Any) -> None:
        if isinstance(noeud, dict):
            valeur = noeud.get("image")
            if isinstance(valeur, str):
                _traiter(valeur)
            for v in noeud.values():
                _parcourir(v)
        elif isinstance(noeud, (list, tuple)):
            for item in noeud:
                _parcourir(item)

    _parcourir(brut)


def _fabriquer_resolveur_svg(
    registre_svg: Dict[str, bytes],
    index_valeur_vers_nom: Dict[str, str],
) -> Callable[[str], Optional[str]]:
    """Callback pour ecrire_sld(resoudre_image_embarquee=...) : decode un
    SVG EMBARQUE EN BASE64 (convention QGIS 'base64:...', cas de la quasi-
    totalite du corpus CNIG reel) et l'enregistre dans registre_svg pour
    materialisation ulterieure (voir deployer_svg_embarque). SEULE forme
    pour laquelle ce callback est sollicite par ecrire_sld (voir la
    docstring de _predeployer_svg_par_chemin, appelee elle AVANT ecrire_sld
    pour le cas "chemin de fichier").

    `index_valeur_vers_nom` retient {valeur_brute: nom_de_fichier_deploye}
    (deja rempli pour les chemins de fichier trouves par _predeployer_svg_
    par_chemin), pour que generer_mbstyle_et_sprites() puisse retrouver
    EXACTEMENT le meme fichier sans re-decoder quoi que ce soit (le jeton
    que recoit resoudre_sprite() est la MEME valeur brute que celle recue
    ici).

    Un base64 illisible retourne None : ecrire_sld() leve alors
    ExpressionPivotNonEcrite pour le symbolizer concerne, plutot que
    d'ecrire un href casse en silence."""

    def resoudre(image: str) -> Optional[str]:
        if not image:
            return None
        valeur = image.strip()

        if valeur in index_valeur_vers_nom:
            return (SVG_SUBDIR / index_valeur_vers_nom[valeur]).as_posix()

        if not valeur.lower().startswith("base64:"):
            return None
        try:
            charge_utile = base64.b64decode(valeur[7:], validate=False)
        except Exception:  # noqa: BLE001
            return None
        empreinte = hashlib.sha1(charge_utile).hexdigest()[:10]  # nosec B324
        nom_fichier = f"styleforge_qgis_{empreinte}.svg"
        registre_svg.setdefault(nom_fichier, charge_utile)
        index_valeur_vers_nom[valeur] = nom_fichier
        return (SVG_SUBDIR / nom_fichier).as_posix()

    return resoudre


def deployer_svg_embarque(registre_svg: Dict[str, bytes], dossier_sortie: Path) -> int:
    """Materialise sur disque, sous dossier_sortie/svg/cnig/, tous les SVG
    enregistres par _fabriquer_resolveur_svg() au cours d'une execution
    (base64 decode OU chemin de fichier copie). A appeler UNE fois, apres
    toutes les conversions de ce lot (pas par fichier/couche) : c'est ce
    qui permet le dedoublonnage ET ce que la PHASE 4/les sprites MBStyle
    exigent (voir executer_pipeline) - ils ont besoin des fichiers reels
    sur disque, pas seulement de leur contenu en memoire. Retourne le
    nombre de fichiers ecrits."""
    if not registre_svg:
        return 0
    dossier_svg = dossier_sortie / SVG_SUBDIR
    dossier_svg.mkdir(parents=True, exist_ok=True)
    for nom_fichier, contenu in registre_svg.items():
        (dossier_svg / nom_fichier).write_bytes(contenu)
    return len(registre_svg)


def convertir_depuis_fichier_qml(
    chemin_qml: Path, *, nom: str,
    registre_svg: Dict[str, bytes],
    index_valeur_vers_nom: Dict[str, str],
    dossiers_recherche_svg: Optional[Sequence[Path]] = None,
) -> ResultatConversion:
    """Conversion d'UN fichier .qml (deja sur disque, qu'il vienne d'un
    dossier ou d'un export temporaire de couche) vers un SLD BRUT (pas
    encore PHASE 4 - voir ResultatConversion.sld_brut et
    executer_pipeline) - meme sequence que StyleforgeBackend.convert()
    cote CLI. Le MBStyle n'est PAS produit ici : il depend des sprites,
    generes dans une passe ulterieure commune a tout le lot (voir
    generer_mbstyle_et_sprites) - produire le pivot ici suffit, il est
    conserve dans resultat.pivot_style."""
    from styleforge_core.readers.qml import lire_fichier_qml
    from styleforge_core.writers.sld import ecrire_sld

    resultat = ResultatConversion(nom=nom, chemin_qml=chemin_qml)
    try:
        lecture = lire_fichier_qml(str(chemin_qml))
    except Exception as exc:  # noqa: BLE001
        resultat.erreur = f"Lecture QML a echoue : {exc}"
        return resultat

    resultat.avertissements = [f"Lecture QML : {w}" for w in lecture.avertissements]
    resultat.pivot_style = lecture.style

    dossiers = list(dossiers_recherche_svg) if dossiers_recherche_svg else []
    if chemin_qml.parent not in dossiers:
        dossiers.insert(0, chemin_qml.parent)
    avert_svg: List[str] = []
    _predeployer_svg_par_chemin(
        lecture.style, registre_svg, index_valeur_vers_nom, dossiers, avert_svg)
    resolveur_svg = _fabriquer_resolveur_svg(registre_svg, index_valeur_vers_nom)

    avert_sld: List[str] = []
    try:
        resultat.sld_brut = ecrire_sld(
            lecture.style, nom_couche=nom, avertissements=avert_sld,
            resoudre_image_embarquee=resolveur_svg,
        )
    except Exception as exc:  # noqa: BLE001
        resultat.erreur = f"Ecriture SLD a echoue : {exc}"
        resultat.avertissements += [f"SLD : {w}" for w in avert_svg]
        return resultat
    resultat.avertissements += [f"SLD : {w}" for w in (avert_sld + avert_svg)]
    resultat.ok = True
    return resultat


# SUPPRIME EN 0.2.0 : convertir_couche() / convertir_toutes_les_couches() /
# convertir_dossier() - chacune ne produisait qu'un SLD BRUT (registre_svg/
# index_valeur_vers_nom en parametres directs), sans jamais appeler la
# PHASE 4 (post_traiter_sld) ni generer le MBStyle/les sprites : correct en
# 0.1.0 (qui n'avait ni l'un ni l'autre), mais les garder telles quelles en
# 0.2.0 aurait cree un second chemin d'appel, silencieusement incomplet
# (SLD jamais nettoye des balises proprietaires, SVG par chemin de fichier
# jamais deploye), a cote du pipeline desormais correct (executer_pipeline,
# plus bas). Plutot que du code mort potentiellement trompeur, dialogue.py
# construit directement la liste d'elements (nom, chemin_qml, nettoyer)
# attendue par executer_pipeline - voir BoiteDialogueStyleforge._construire_
# elements().


def generer_mbstyle_et_sprites(
    resultats: List[ResultatConversion], *,
    index_valeur_vers_nom: Dict[str, str],
    dossier_sortie: Path,
    workspace_mbstyle: str = "",
    taille_sprite_px: int = TAILLE_SPRITE_DEFAUT,
) -> Dict[str, Any]:
    """Produit le MBStyle de chaque resultat reussi (resultat.mbstyle),
    PUIS la feuille de sprites Mapbox correspondante (sprite.png/@2x +
    index JSON, ecrits directement dans dossier_sortie) - meme sequence
    que le CLI (PHASE 5, backend styleforge) : les sprites SVG exigent
    que les fichiers soient DEJA SUR DISQUE (voir styleforge_core.
    sprites), donc deployer_svg_embarque() doit avoir ete appelee AVANT
    cette fonction (voir executer_pipeline).

    Retourne le rapport de SpriteRegistry.build() (memes cles que le
    CLI : "vignettes", "images"), avec en plus "warnings" (liste des
    avertissements de SpriteRegistry, ex. pictogramme absent pour le
    sprite)."""
    from styleforge_core.writers.mbstyle import ecrire_mbstyle

    sprites = SpriteRegistry(taille_sprite_px)
    dossier_svg = dossier_sortie / SVG_SUBDIR

    def resoudre_sprite(jeton: str) -> Optional[str]:
        # 'jeton' est soit une IMAGE (chemin/base64, deja vue par le
        # resolveur SLD - voir _fabriquer_resolveur_svg - et donc deja
        # dans index_valeur_vers_nom), soit un WELLKNOWNNAME de Mark
        # (forme simple "circle"/"square"... ou motif de hachure
        # "shape://slash"...).
        nom_fichier = index_valeur_vers_nom.get(jeton)
        if nom_fichier is not None:
            resolu = sprites.register_svg(nom_fichier, dossier_svg)
            if resolu is not None:
                return resolu
        resolu = sprites.register_shape(
            NOMS_MARQUEURS_QGIS_VERS_WKN.get(jeton, jeton)
        )
        if resolu is not None:
            return resolu
        # "ttf://<Police>#0x<hex>" (FontMarker) : Mapbox GL n'a aucune
        # notion de police, on le rasterise en vignette - meme logique
        # que le CLI (voir styleforge_core.sprites docstring).
        return sprites.register_font_glyph(jeton)

    id_source = workspace_mbstyle or "cnig"
    workspace_tiles = workspace_mbstyle or "workspace"

    for resultat in resultats:
        if not resultat.ok or resultat.pivot_style is None:
            continue
        url_source = (
            f"{MBSTYLE_BASE_URL_DEFAUT}/gwc/service/wmts"
            f"?REQUEST=GetTile&SERVICE=WMTS&VERSION=1.0.0"
            f"&LAYER={workspace_tiles}:{resultat.nom}&STYLE="
            f"&TILEMATRIX=EPSG:900913:{{z}}&TILEMATRIXSET=EPSG:900913"
            f"&FORMAT=application/x-protobuf;type=mapbox-vector"
            f"&TILECOL={{x}}&TILEROW={{y}}"
        )
        avert_mb: List[str] = []
        try:
            resultat.mbstyle = ecrire_mbstyle(
                resultat.pivot_style,
                id_source=id_source, url_source=url_source,
                nom_couche_source=resultat.nom, avertissements=avert_mb,
                resoudre_sprite=resoudre_sprite,
                taille_sprite_px=float(taille_sprite_px),
            )
        except Exception as exc:  # noqa: BLE001
            # Pas un echec de resultat.ok : le SLD a reussi, seul le
            # MBStyle manque - meme convention que le CLI
            # (_raison_echec_mbstyle cherche aussi le prefixe "MBStyle").
            resultat.avertissements.append(f"MBStyle : {exc}")
        else:
            resultat.avertissements += [f"MBStyle : {w}" for w in avert_mb]

    rapport = sprites.build(dossier_sortie)
    rapport["warnings"] = list(sprites.warnings)
    return rapport


def appliquer_post_traitement_sld(
    resultats: List[ResultatConversion], *, index_svg: Dict[str, str],
) -> None:
    """PHASE 4 (post_traiter_sld, styleforge_core.writers.
    sld_posttraitement) - appliquee APRES deploiement des SVG (index_svg
    doit deja refleter les fichiers reellement sur disque, voir
    executer_pipeline). Remplit resultat.sld a partir de resultat.
    sld_brut ; en cas d'echec du post-traitement (improbable - XML
    invalide uniquement), conserve le SLD brut tel quel plutot que de
    perdre une conversion qui avait reussi, avec un avertissement
    explicite plutot qu'un silence."""
    for resultat in resultats:
        if not resultat.ok or not resultat.sld_brut:
            continue
        avert_phase4: List[str] = []
        try:
            resultat.sld, _stats = post_traiter_sld(
                resultat.sld_brut, resultat.chemin_qml,
                index_svg=index_svg, vendor=VENDOR_DEFAULTS,
                avertissements=avert_phase4,
            )
        except Exception as exc:  # noqa: BLE001
            resultat.sld = resultat.sld_brut
            resultat.avertissements.append(
                f"SLD : Post-traitement (PHASE 4) échoué, SLD non corrigé "
                f"conservé : {exc}")
        else:
            resultat.avertissements += [f"SLD : {w}" for w in avert_phase4]


def executer_pipeline(
    elements: List[Tuple[str, Path, bool]], *,
    mbstyle_demande: bool,
    dossier_sortie: Path,
    workspace_mbstyle: str = "",
    dossiers_recherche_svg_additionnels: Optional[Sequence[Path]] = None,
    taille_sprite_px: int = TAILLE_SPRITE_DEFAUT,
) -> Tuple[List[ResultatConversion], int, Dict[str, Any]]:
    """Pipeline complet d'un lot de conversions : chaque element est un
    triplet (nom, chemin_qml, nettoyer) - `nettoyer=True` pour un .qml
    TEMPORAIRE exporte d'une couche QGIS (supprime a la fin du pipeline,
    jamais avant : la PHASE 4 doit encore pouvoir le relire).

    Sequence (memes dependances d'ordre que le CLI, voir les docstrings
    des fonctions appelees) :
      1. Conversion de chaque element -> SLD BRUT + pivot (resultat.ok,
         .sld_brut, .pivot_style), SVG collectes dans un registre commun.
      2. Deploiement des SVG sur disque (svg/cnig/) - CONDITION PREALABLE
         aux etapes 3 et 4, qui verifient l'existence reelle des fichiers.
      3. MBStyle + sprites (si mbstyle_demande), a partir des pivots
         conserves a l'etape 1.
      4. PHASE 4 (post-traitement SLD) sur chaque SLD brut, avec l'index
         SVG complet issu de l'etape 2.
      5. Nettoyage des .qml temporaires marques `nettoyer=True`.

    Retourne (resultats, nombre_de_svg_deployes, rapport_sprites) -
    rapport_sprites est un dict vide si mbstyle_demande est faux."""
    registre_svg: Dict[str, bytes] = {}
    index_valeur_vers_nom: Dict[str, str] = {}
    extra = list(dossiers_recherche_svg_additionnels or [])

    resultats: List[ResultatConversion] = []
    for nom, chemin_qml, _nettoyer in elements:
        resultats.append(convertir_depuis_fichier_qml(
            chemin_qml, nom=nom, registre_svg=registre_svg,
            index_valeur_vers_nom=index_valeur_vers_nom,
            dossiers_recherche_svg=extra,
        ))

    n_svg = deployer_svg_embarque(registre_svg, dossier_sortie)
    index_svg = {
        nom_fichier.lower(): (SVG_SUBDIR / nom_fichier).as_posix()
        for nom_fichier in registre_svg
    }

    rapport_sprites: Dict[str, Any] = {}
    if mbstyle_demande:
        rapport_sprites = generer_mbstyle_et_sprites(
            resultats, index_valeur_vers_nom=index_valeur_vers_nom,
            dossier_sortie=dossier_sortie, workspace_mbstyle=workspace_mbstyle,
            taille_sprite_px=taille_sprite_px,
        )

    appliquer_post_traitement_sld(resultats, index_svg=index_svg)

    for _nom, chemin_qml, nettoyer in elements:
        if nettoyer:
            chemin_qml.unlink(missing_ok=True)

    return resultats, n_svg, rapport_sprites


def ecrire_fichiers_sortie(resultat: ResultatConversion, dossier_sortie: Path) -> None:
    """Ecrit <nom>.sld et, si produit, <nom>.json dans le dossier de
    sortie. N'ecrit rien pour une conversion en echec (resultat.ok est
    False) : il n'y a alors rien a ecrire que du vide, ce serait
    trompeur de produire un fichier vide a cote du nom du style."""
    if not resultat.ok:
        return
    dossier_sortie.mkdir(parents=True, exist_ok=True)
    (dossier_sortie / f"{resultat.nom}.sld").write_text(
        resultat.sld or resultat.sld_brut or "", encoding="utf-8")
    if resultat.mbstyle is not None:
        (dossier_sortie / f"{resultat.nom}.json").write_text(
            resultat.mbstyle, encoding="utf-8")


def _grouper_par_categorie(avertissements: List[str]) -> "dict[str, list[str]]":
    groupes: "dict[str, list[str]]" = {}
    for avert in avertissements:
        for prefixe in PREFIXES_CONNUS:
            if avert.startswith(prefixe):
                groupes.setdefault(prefixe[:-3], []).append(avert[len(prefixe):])
                break
        else:
            groupes.setdefault("Autre", []).append(avert)
    return groupes


def ecrire_rapport(
    resultats: List[ResultatConversion], dossier_sortie: Path, *,
    mbstyle_demande: bool, par_categorie: int = 6,
) -> Path:
    """Ecrit rapport_conversion.md dans le dossier de sortie, avec la
    MEME discipline d'echantillonnage par categorie que le correctif du
    CLI du 2026-10-12 : un echantillon global (plutot que par categorie)
    masquait de fait les avertissements SLD/MBStyle des qu'un fichier
    avait plusieurs dizaines d'avertissements "Lecture QML" - toute
    troncature ici reste donc dite explicitement, jamais silencieuse."""
    ok = [r for r in resultats if r.ok]
    ko = [r for r in resultats if not r.ok]
    avec_mbstyle = [r for r in ok if r.mbstyle] if mbstyle_demande else []

    lignes: List[str] = ["# Rapport de conversion Styleforge (plugin QGIS)", ""]
    lignes.append(f"- Styles SLD convertis : **{len(ok)}/{len(resultats)}**")
    lignes.append(f"- Echecs SLD : **{len(ko)}**")
    if mbstyle_demande:
        lignes.append(f"- MBStyle produits : **{len(avec_mbstyle)}/{len(ok)}**")
    lignes.append("")

    if ko:
        lignes += ["## Echecs", ""]
        for r in ko:
            lignes.append(f"- `{r.nom}` : {r.erreur}")
        lignes.append("")

    avertis = [r for r in ok if r.avertissements]
    if avertis:
        lignes += ["## Avertissements", ""]
        if mbstyle_demande:
            lignes += [
                "Chaque avertissement precise le document concerne par son "
                "prefixe : **`Lecture QML :`** (pivot, commun au SLD ET au "
                "MBStyle), **`SLD :`** (ecrivain SLD ou PHASE 4) ou "
                "**`MBStyle :`** (ecrivain MBStyle ou sprites). Chaque "
                "categorie presente est echantillonnee separement (jusqu'a "
                f"{par_categorie} avertissements) pour qu'une categorie "
                "nombreuse n'en masque pas une autre.", "",
            ]
        for r in avertis:
            lignes.append(f"- `{r.nom}`")
            if not mbstyle_demande:
                for w in r.avertissements[:par_categorie]:
                    lignes.append(f"  - {w}")
                reste = len(r.avertissements) - par_categorie
                if reste > 0:
                    lignes.append(
                        f"  - ... et {reste} autre(s) avertissement(s) non "
                        f"affiche(s) ici.")
                continue
            for categorie, items in _grouper_par_categorie(r.avertissements).items():
                prefixe = f"{categorie} : " if categorie != "Autre" else ""
                for w in items[:par_categorie]:
                    lignes.append(f"  - {prefixe}{w}")
                reste = len(items) - par_categorie
                if reste > 0:
                    lignes.append(
                        f"  - ... et {reste} autre(s) avertissement(s) "
                        f"« {categorie} » non affiche(s) ici.")

    dossier_sortie.mkdir(parents=True, exist_ok=True)
    chemin_rapport = dossier_sortie / "rapport_conversion.md"
    chemin_rapport.write_text("\n".join(lignes) + "\n", encoding="utf-8")
    return chemin_rapport
