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

LIMITE DELIBEREE DE CETTE VERSION (voir metadata.txt "about") : les
pictogrammes SVG EMBARQUES EN BASE64 dans le QML (convention QGIS
'base64:...', cas de la quasi-totalite du corpus CNIG reel - verifie
empiriquement : sans ce qui suit, 13 des 17 exemples officiels
echouaient purement et simplement) sont decodes et materialises dans
svg/cnig/ du dossier de sortie, memes conventions que register_svg_
reference()/SVG_SUBDIR du CLI (cnig_qml2sld_geoserver.py), pour que les
.sld produits ici restent coherents avec ceux du CLI. En revanche, un
SVG reference par un CHEMIN DE FICHIER (pas embarque) n'est pas copie
depuis sa source par ce plugin - perimetre different, ouvert (ou est le
fichier reellement sur disque ?), hors de portee de cette version. Les
sprites MBStyle (pictogrammes/motifs pour l'ecrivain MBStyle) restent
eux aussi hors de portee - meme limite, pour la meme raison, que
POST /v1/convert de styleforge-api (voir docs/limites.md section 3).
Dans les deux cas restants : exception nommee explicite
(ExpressionPivotNonEcrite), jamais une approximation silencieuse."""
from __future__ import annotations

import base64
import hashlib
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Dict, List, Optional

PREFIXES_CONNUS = ("Lecture QML : ", "SLD : ", "MBStyle : ")

#: Meme convention que SVG_SUBDIR dans cnig_qml2sld_geoserver.py : les
#: .sld produits par ce plugin et par le CLI referencent leurs
#: pictogrammes sous le meme chemin relatif "svg/cnig/<nom>.svg".
SVG_SUBDIR = Path("svg") / "cnig"

# Memes valeurs par defaut que MbStyleOptions dans le CLI (cnig_qml2sld_
# geoserver.py) : un MBStyle produit par ce plugin sans configuration
# GeoServer explicite (hors de portee de l'UI minimale de cette version)
# reste coherent avec ce que produirait le CLI non reconfigure.
MBSTYLE_BASE_URL_DEFAUT = "http://localhost:8080/geoserver"


@dataclass
class ResultatConversion:
    nom: str
    ok: bool = False
    erreur: Optional[str] = None
    avertissements: List[str] = field(default_factory=list)
    sld: Optional[str] = None
    mbstyle: Optional[str] = None


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
    chemin = Path(tempfile.gettempdir()) / f"styleforge_qgis_{id(layer)}.qml"
    message, succes = layer.saveNamedStyle(str(chemin))
    if not succes:
        raise ErreurExportStyleCouche(
            f"QGIS n'a pas pu exporter le style de la couche "
            f"« {layer.name()} » : {message or 'raison non precisee par QGIS'}."
        )
    return chemin


def nouveau_registre_svg() -> Dict[str, bytes]:
    """Registre partage entre toutes les conversions d'UNE meme execution
    (couche active seule, toutes les couches, ou dossier) : un meme
    pictogramme embarque dans plusieurs couches/fichiers ne produit
    qu'UN seul fichier .svg sur disque (dedoublonnage par empreinte de
    contenu), meme principe que EMBEDDED_SVG cote CLI."""
    return {}


def _fabriquer_resolveur_image_embarquee(
    registre_svg: Dict[str, bytes],
) -> Callable[[str], Optional[str]]:
    """Callback pour ecrire_sld(resoudre_image_embarquee=...) : decode un
    SVG embarque en base64 (convention QGIS 'base64:...') et l'enregistre
    dans registre_svg pour materialisation ulterieure (voir
    deployer_svg_embarque) - jamais ecrit directement ici, pour rester
    appelable plusieurs fois (dedoublonnage) sans connaitre le dossier de
    sortie final a ce stade. Un chemin de fichier classique (pas du
    base64) n'est PAS resolu par ce plugin (voir docstring du module) :
    retourne None, ce qui fait lever ExpressionPivotNonEcrite a
    ecrire_sld() plutot que d'ecrire un href non deploye en silence."""

    def resoudre(image: str) -> Optional[str]:
        if not image:
            return None
        valeur = image.strip()
        if not valeur.lower().startswith("base64:"):
            return None
        try:
            charge_utile = base64.b64decode(valeur[7:], validate=False)
        except Exception:  # noqa: BLE001
            return None
        empreinte = hashlib.sha1(charge_utile).hexdigest()[:10]  # nosec B324
        nom_fichier = f"styleforge_qgis_{empreinte}.svg"
        registre_svg.setdefault(nom_fichier, charge_utile)
        return (SVG_SUBDIR / nom_fichier).as_posix()

    return resoudre


def deployer_svg_embarque(registre_svg: Dict[str, bytes], dossier_sortie: Path) -> int:
    """Materialise sur disque, sous dossier_sortie/svg/cnig/, tous les
    SVG decodes par _fabriquer_resolveur_image_embarquee() au cours
    d'une execution. A appeler UNE fois, apres toutes les conversions
    (pas par fichier/couche) : c'est ce qui permet le dedoublonnage.
    Retourne le nombre de fichiers ecrits."""
    if not registre_svg:
        return 0
    dossier_svg = dossier_sortie / SVG_SUBDIR
    dossier_svg.mkdir(parents=True, exist_ok=True)
    for nom_fichier, contenu in registre_svg.items():
        (dossier_svg / nom_fichier).write_bytes(contenu)
    return len(registre_svg)


def convertir_depuis_fichier_qml(
    chemin_qml: Path, *, nom: str, mbstyle_demande: bool,
    workspace_mbstyle: str = "", registre_svg: Optional[Dict[str, bytes]] = None,
) -> ResultatConversion:
    """Conversion d'UN fichier .qml (deja sur disque, qu'il vienne d'un
    dossier ou d'un export temporaire de couche) vers SLD et,
    optionnellement, MBStyle - meme sequence que StyleforgeBackend.
    convert() + la branche PHASE 5 du CLI, sans PHASE 4 (post-traitement
    GeoServer : hachures, VendorOption - hors de portee de ce plugin,
    voir metadata.txt)."""
    from styleforge_core.readers.qml import lire_fichier_qml
    from styleforge_core.writers.sld import ecrire_sld

    resultat = ResultatConversion(nom=nom)
    try:
        lecture = lire_fichier_qml(str(chemin_qml))
    except Exception as exc:  # noqa: BLE001
        resultat.erreur = f"Lecture QML a echoue : {exc}"
        return resultat

    resultat.avertissements = [f"Lecture QML : {w}" for w in lecture.avertissements]

    resolveur_svg = (
        _fabriquer_resolveur_image_embarquee(registre_svg)
        if registre_svg is not None else None
    )
    avert_sld: List[str] = []
    try:
        resultat.sld = ecrire_sld(
            lecture.style, nom_couche=nom, avertissements=avert_sld,
            resoudre_image_embarquee=resolveur_svg,
        )
    except Exception as exc:  # noqa: BLE001
        resultat.erreur = f"Ecriture SLD a echoue : {exc}"
        return resultat
    resultat.avertissements += [f"SLD : {w}" for w in avert_sld]

    if mbstyle_demande:
        from styleforge_core.writers.mbstyle import ecrire_mbstyle

        avert_mb: List[str] = []
        id_source = workspace_mbstyle or "cnig"
        workspace_tiles = workspace_mbstyle or "workspace"
        url_source = (
            f"{MBSTYLE_BASE_URL_DEFAUT}/gwc/service/wmts"
            f"?REQUEST=GetTile&SERVICE=WMTS&VERSION=1.0.0"
            f"&LAYER={workspace_tiles}:{nom}&STYLE="
            f"&TILEMATRIX=EPSG:900913:{{z}}&TILEMATRIXSET=EPSG:900913"
            f"&FORMAT=application/x-protobuf;type=mapbox-vector"
            f"&TILECOL={{x}}&TILEROW={{y}}"
        )
        try:
            resultat.mbstyle = ecrire_mbstyle(
                lecture.style,
                id_source=id_source, url_source=url_source,
                nom_couche_source=nom, avertissements=avert_mb,
            )
        except Exception as exc:  # noqa: BLE001
            # Pas un echec de resultat.ok : le SLD a reussi, seul le
            # MBStyle manque - meme convention que le CLI
            # (_raison_echec_mbstyle cherche aussi le prefixe "MBStyle").
            resultat.avertissements.append(f"MBStyle : {exc}")
        else:
            resultat.avertissements += [f"MBStyle : {w}" for w in avert_mb]

    resultat.ok = True
    return resultat


def convertir_couche(
    layer, *, mbstyle_demande: bool, workspace_mbstyle: str = "",
    registre_svg: Optional[Dict[str, bytes]] = None,
) -> ResultatConversion:
    """Convertit le style COURANT d'une couche QGIS (celui affiche dans
    le panneau Styles, modifications non enregistrees comprises - on lit
    l'etat en memoire, pas un .qml sur disque)."""
    try:
        chemin_qml = exporter_style_couche_vers_qml(layer)
    except ErreurExportStyleCouche as exc:
        resultat = ResultatConversion(nom=layer.name())
        resultat.erreur = str(exc)
        return resultat
    try:
        return convertir_depuis_fichier_qml(
            chemin_qml, nom=layer.name(), mbstyle_demande=mbstyle_demande,
            workspace_mbstyle=workspace_mbstyle, registre_svg=registre_svg,
        )
    finally:
        chemin_qml.unlink(missing_ok=True)


def convertir_toutes_les_couches(
    project, *, mbstyle_demande: bool, workspace_mbstyle: str = "",
    registre_svg: Optional[Dict[str, bytes]] = None,
) -> List[ResultatConversion]:
    """Convertit TOUTES les couches vectorielles chargees dans le projet
    QGIS courant, une par une - tolerant aux pannes (une couche en echec
    n'empeche pas les autres), meme discipline que BatchConverter cote
    CLI."""
    from qgis.core import QgsVectorLayer

    resultats: List[ResultatConversion] = []
    for layer in project.mapLayers().values():
        if not isinstance(layer, QgsVectorLayer):
            continue
        resultats.append(
            convertir_couche(
                layer, mbstyle_demande=mbstyle_demande,
                workspace_mbstyle=workspace_mbstyle, registre_svg=registre_svg,
            )
        )
    return resultats


def convertir_dossier(
    dossier: Path, *, mbstyle_demande: bool, workspace_mbstyle: str = "",
    registre_svg: Optional[Dict[str, bytes]] = None,
) -> List[ResultatConversion]:
    """Convertit tous les fichiers .qml trouves recursivement dans un
    dossier - equivalent de --local-source/--all du CLI, sans PHASE 4
    (voir docstring du module)."""
    resultats: List[ResultatConversion] = []
    for chemin in sorted(dossier.rglob("*.qml")):
        resultats.append(
            convertir_depuis_fichier_qml(
                chemin, nom=chemin.stem, mbstyle_demande=mbstyle_demande,
                workspace_mbstyle=workspace_mbstyle, registre_svg=registre_svg,
            )
        )
    return resultats


def ecrire_fichiers_sortie(resultat: ResultatConversion, dossier_sortie: Path) -> None:
    """Ecrit <nom>.sld et, si produit, <nom>.json dans le dossier de
    sortie. N'ecrit rien pour une conversion en echec (resultat.ok est
    False) : il n'y a alors rien a ecrire que du vide, ce serait
    trompeur de produire un fichier vide a cote du nom du style."""
    if not resultat.ok:
        return
    dossier_sortie.mkdir(parents=True, exist_ok=True)
    (dossier_sortie / f"{resultat.nom}.sld").write_text(
        resultat.sld or "", encoding="utf-8")
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
                "MBStyle), **`SLD :`** (ecrivain SLD) ou **`MBStyle :`** "
                "(ecrivain MBStyle). Chaque categorie presente est "
                f"echantillonnee separement (jusqu'a {par_categorie} "
                "avertissements) pour qu'une categorie nombreuse n'en "
                "masque pas une autre.", "",
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
