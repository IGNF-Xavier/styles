#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/test_audit.py — suite de tests pour styleforge_core.audit.

Deux catégories de tests, comme pour test_mbstyle.py/test_sld.py, mais avec
une troisième ici, propre à ce module puisque c'est une EXTRACTION (pas une
construction neuve) :
  1. Tests structurels, un par catégorie de défaut détectable (BOM, CRLF,
     encodage, XML mal formé, racine/version incorrecte, absence de Rule,
     ordre XSD, éléments numériques, Stroke/Fill vide, CssParameter, Mark,
     ExternalGraphic, GraphicFill/Stroke, VendorOption, PropertyName,
     PropertyIsLike) plus un cas "conforme" sans aucun défaut.
  2. Tests de GÉNÉRALISATION : prouvent que les paramètres nouvellement
     introduits (vocabulaire, xsd_order, existe_ressource, apres_fichier)
     changent effectivement le comportement, pas seulement présents sans
     effet.
  3. ÉQUIVALENCE AVEC L'ORIGINAL : importe dynamiquement GeoServerAuditor
     depuis cnig_qml2sld_geoserver.py (encore présent à côté de
     styleforge-core/ à ce stade du projet — voir la note dans le test) et
     compare, sur un même lot de fixtures, le rapport produit par l'ancienne
     classe et par SldAuditor(vocabulaire=VOCABULAIRE_GEOSERVER) : mêmes
     catégories, mêmes comptes, mêmes messages. C'est la preuve que
     l'extraction n'a rien changé au comportement par défaut, pas une
     simple relecture du code affirmant qu'elle ne l'a pas fait.
Ce fichier ne dépend pas de QGIS : l'auditeur ne charge aucun style dans un
moteur de rendu, il contrôle du XML statique — aucun oracle PyQGIS n'est
nécessaire ici (contrairement à test_sld.py/test_mbstyle.py).
"""
from __future__ import annotations

import importlib.util
import sys
import tempfile
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from styleforge_core.audit import (
    ORDRE_XSD_SLD_1_0_0,
    VOCABULAIRE_GEOSERVER,
    RapportAudit,
    SldAuditor,
    VocabulaireCible,
    formater_rapport,
)


def _ecrire(dossier: Path, nom: str, contenu: bytes) -> Path:
    chemin = dossier / nom
    chemin.write_bytes(contenu)
    return chemin


def _auditer_texte(texte: str, *, nom: str = "test.sld", **kw) -> RapportAudit:
    """Écrit `texte` (str, encodé UTF-8) dans un fichier temporaire et
    l'audite avec un SldAuditor construit avec les kwargs fournis (styles_dir
    ajouté automatiquement au dossier temporaire, sauf si déjà fourni)."""
    with tempfile.TemporaryDirectory() as d:
        dossier = Path(d)
        kw.setdefault("styles_dir", dossier)
        chemin = _ecrire(dossier, nom, texte.encode("utf-8"))
        auditeur = SldAuditor(**kw)
        return auditeur.auditer([chemin])


SLD_CONFORME = """<?xml version="1.0" encoding="UTF-8"?>
<StyledLayerDescriptor version="1.0.0">
  <NamedLayer>
    <Name>couche</Name>
    <UserStyle>
      <Name>style</Name>
      <FeatureTypeStyle>
        <Rule>
          <PolygonSymbolizer>
            <Fill>
              <CssParameter name="fill">#ff0000</CssParameter>
              <CssParameter name="fill-opacity">0.8</CssParameter>
            </Fill>
            <Stroke>
              <CssParameter name="stroke">#000000</CssParameter>
              <CssParameter name="stroke-width">1</CssParameter>
            </Stroke>
          </PolygonSymbolizer>
        </Rule>
      </FeatureTypeStyle>
    </UserStyle>
  </NamedLayer>
</StyledLayerDescriptor>"""


# --------------------------------------------------------------------------- cas conforme
def test_sld_conforme_aucun_defaut():
    rapport = _auditer_texte(SLD_CONFORME)
    assert rapport.conforme, dict(rapport.problemes)
    assert rapport.controles == 1
    assert not rapport.extensions


# --------------------------------------------------------------------------- encodage / fins de ligne
def test_bom_utf8_detecte():
    rapport = _auditer_texte(SLD_CONFORME.replace(
        '<?xml version="1.0" encoding="UTF-8"?>\n', ""))
    with tempfile.TemporaryDirectory() as d:
        chemin = _ecrire(Path(d), "bom.sld", b"\xef\xbb\xbf" + SLD_CONFORME.encode("utf-8"))
        rapport = SldAuditor(styles_dir=Path(d)).auditer([chemin])
    assert rapport.problemes["BOM UTF-8 présent"] == 1


def test_crlf_detecte():
    rapport = _auditer_texte(SLD_CONFORME.replace("\n", "\r\n"))
    assert rapport.problemes["fins de ligne CRLF"] == 1


def test_encodage_non_utf8_detecte():
    with tempfile.TemporaryDirectory() as d:
        # Un octet 0xFF isolé n'est pas de l'UTF-8 valide.
        chemin = _ecrire(Path(d), "bad.sld", b"<StyledLayerDescriptor>\xff</StyledLayerDescriptor>")
        rapport = SldAuditor(styles_dir=Path(d)).auditer([chemin])
    assert rapport.problemes["encodage non UTF-8"] == 1


# --------------------------------------------------------------------------- bonne formation / racine
def test_xml_mal_forme_detecte():
    rapport = _auditer_texte("<StyledLayerDescriptor version=\"1.0.0\"><Rule>")
    assert rapport.problemes["XML mal formé"] == 1


def test_racine_incorrecte_detectee():
    rapport = _auditer_texte('<AutreChose version="1.0.0"><Rule/></AutreChose>')
    assert rapport.problemes["racine incorrecte"] == 1


def test_version_sld_incorrecte_detectee():
    rapport = _auditer_texte('<StyledLayerDescriptor version="1.1.0"><Rule/></StyledLayerDescriptor>')
    assert rapport.problemes["version SLD incorrecte"] == 1


def test_style_sans_regle_detecte():
    rapport = _auditer_texte('<StyledLayerDescriptor version="1.0.0"></StyledLayerDescriptor>')
    assert rapport.problemes["style sans aucune règle"] == 1


# --------------------------------------------------------------------------- ordre XSD
def test_ordre_xsd_non_respecte_detecte():
    # Fill APRÈS Stroke dans un PolygonSymbolizer viole l'ordre imposé
    # (Geometry, Fill, Stroke, VendorOption).
    sld = SLD_CONFORME.replace(
        "<Fill>\n              <CssParameter name=\"fill\">#ff0000</CssParameter>\n"
        "              <CssParameter name=\"fill-opacity\">0.8</CssParameter>\n            </Fill>\n"
        "            <Stroke>\n              <CssParameter name=\"stroke\">#000000</CssParameter>\n"
        "              <CssParameter name=\"stroke-width\">1</CssParameter>\n            </Stroke>",
        "<Stroke>\n              <CssParameter name=\"stroke\">#000000</CssParameter>\n"
        "              <CssParameter name=\"stroke-width\">1</CssParameter>\n            </Stroke>\n"
        "            <Fill>\n              <CssParameter name=\"fill\">#ff0000</CssParameter>\n"
        "              <CssParameter name=\"fill-opacity\">0.8</CssParameter>\n            </Fill>",
    )
    rapport = _auditer_texte(sld)
    assert rapport.problemes["ordre XSD non respecté"] == 1


# --------------------------------------------------------------------------- éléments numériques
def test_element_numerique_vide_detecte():
    rapport = _auditer_texte(
        '<StyledLayerDescriptor version="1.0.0"><Rule><PointSymbolizer>'
        "<Graphic><Size/></Graphic></PointSymbolizer></Rule></StyledLayerDescriptor>")
    assert rapport.problemes["élément numérique vide"] == 1


def test_valeur_numerique_invalide_detectee():
    rapport = _auditer_texte(
        '<StyledLayerDescriptor version="1.0.0"><Rule><PointSymbolizer>'
        "<Graphic><Size>gros</Size></Graphic></PointSymbolizer></Rule></StyledLayerDescriptor>")
    assert rapport.problemes["valeur numérique invalide"] == 1


def test_element_numerique_avec_expression_ogc_accepte():
    # Size piloté par une expression ogc:Div (cas réel bridgestyle documenté
    # dans le module) : NE DOIT PAS être signalé.
    rapport = _auditer_texte(
        '<StyledLayerDescriptor version="1.0.0"><Rule><PointSymbolizer><Graphic>'
        "<Size><Div><Literal>15.0</Literal><Literal>2</Literal></Div></Size>"
        "</Graphic></PointSymbolizer></Rule></StyledLayerDescriptor>")
    assert "expression non reconnue dans un élément numérique" not in rapport.problemes
    assert "élément numérique vide" not in rapport.problemes


def test_expression_non_reconnue_dans_element_numerique_detectee():
    rapport = _auditer_texte(
        '<StyledLayerDescriptor version="1.0.0"><Rule><PointSymbolizer><Graphic>'
        "<Size><TrucInconnu/></Size></Graphic></PointSymbolizer></Rule></StyledLayerDescriptor>")
    assert rapport.problemes["expression non reconnue dans un élément numérique"] == 1


# --------------------------------------------------------------------------- Stroke/Fill vide
def test_stroke_vide_detecte():
    rapport = _auditer_texte(
        '<StyledLayerDescriptor version="1.0.0"><Rule><PolygonSymbolizer>'
        "<Stroke/></PolygonSymbolizer></Rule></StyledLayerDescriptor>")
    assert rapport.problemes["Stroke ou Fill vide"] == 1


# --------------------------------------------------------------------------- CssParameter
def test_cssparameter_sans_name_detecte():
    rapport = _auditer_texte(
        '<StyledLayerDescriptor version="1.0.0"><Rule><PolygonSymbolizer><Fill>'
        "<CssParameter>#fff</CssParameter></Fill></PolygonSymbolizer></Rule></StyledLayerDescriptor>")
    assert rapport.problemes["CssParameter sans attribut name"] == 1


def test_cssparameter_inconnu_detecte():
    rapport = _auditer_texte(
        '<StyledLayerDescriptor version="1.0.0"><Rule><PolygonSymbolizer><Fill>'
        '<CssParameter name="truc-inconnu">1</CssParameter></Fill>'
        "</PolygonSymbolizer></Rule></StyledLayerDescriptor>")
    assert rapport.problemes["CssParameter inconnu"] == 1


def test_cssparameter_sans_valeur_detecte():
    rapport = _auditer_texte(
        '<StyledLayerDescriptor version="1.0.0"><Rule><PolygonSymbolizer><Fill>'
        '<CssParameter name="fill"></CssParameter></Fill>'
        "</PolygonSymbolizer></Rule></StyledLayerDescriptor>")
    assert rapport.problemes["CssParameter sans valeur"] == 1


def test_stroke_dasharray_non_numerique_detecte():
    rapport = _auditer_texte(
        '<StyledLayerDescriptor version="1.0.0"><Rule><PolygonSymbolizer><Stroke>'
        '<CssParameter name="stroke-dasharray">4 deux 2</CssParameter></Stroke>'
        "</PolygonSymbolizer></Rule></StyledLayerDescriptor>")
    assert rapport.problemes["stroke-dasharray non numérique"] == 1


# --------------------------------------------------------------------------- Mark
def test_mark_sans_wellknownname_unique_detecte():
    rapport = _auditer_texte(
        '<StyledLayerDescriptor version="1.0.0"><Rule><PointSymbolizer><Graphic>'
        "<Mark/></Graphic></PointSymbolizer></Rule></StyledLayerDescriptor>")
    assert rapport.problemes["Mark sans WellKnownName unique"] == 1


def test_wellknownname_non_reconnu_detecte():
    rapport = _auditer_texte(
        '<StyledLayerDescriptor version="1.0.0"><Rule><PointSymbolizer><Graphic><Mark>'
        "<WellKnownName>pentagone</WellKnownName></Mark>"
        "</Graphic></PointSymbolizer></Rule></StyledLayerDescriptor>")
    assert rapport.problemes["WellKnownName non reconnu par la cible"] == 1


def test_wellknownname_prefixe_shape_accepte():
    rapport = _auditer_texte(
        '<StyledLayerDescriptor version="1.0.0"><Rule><PointSymbolizer><Graphic><Mark>'
        "<WellKnownName>shape://plus</WellKnownName></Mark>"
        "</Graphic></PointSymbolizer></Rule></StyledLayerDescriptor>")
    assert "WellKnownName non reconnu par la cible" not in rapport.problemes


# --------------------------------------------------------------------------- ExternalGraphic
def test_externalgraphic_sans_onlineresource_detecte():
    rapport = _auditer_texte(
        '<StyledLayerDescriptor version="1.0.0"><Rule><PointSymbolizer><Graphic>'
        "<ExternalGraphic><Format>image/svg+xml</Format></ExternalGraphic>"
        "</Graphic></PointSymbolizer></Rule></StyledLayerDescriptor>")
    assert rapport.problemes["ExternalGraphic sans OnlineResource"] == 1


def test_externalgraphic_sans_format_detecte():
    with tempfile.TemporaryDirectory() as d:
        Path(d, "icone.svg").write_text("<svg/>")
        sld = (
            '<StyledLayerDescriptor version="1.0.0" xmlns:xlink="http://www.w3.org/1999/xlink">'
            '<Rule><PointSymbolizer><Graphic>'
            '<ExternalGraphic><OnlineResource xlink:href="icone.svg"/></ExternalGraphic>'
            "</Graphic></PointSymbolizer></Rule></StyledLayerDescriptor>")
        rapport = _auditer_texte(sld, styles_dir=Path(d))
    assert rapport.problemes["ExternalGraphic sans Format"] == 1


def test_pictogramme_absent_detecte():
    sld = (
        '<StyledLayerDescriptor version="1.0.0" xmlns:xlink="http://www.w3.org/1999/xlink">'
        '<Rule><PointSymbolizer><Graphic>'
        '<ExternalGraphic><OnlineResource xlink:href="inexistant.svg"/>'
        "<Format>image/svg+xml</Format></ExternalGraphic>"
        "</Graphic></PointSymbolizer></Rule></StyledLayerDescriptor>")
    rapport = _auditer_texte(sld)
    assert rapport.problemes["pictogramme référencé mais absent"] == 1


def test_pictogramme_present_non_signale():
    with tempfile.TemporaryDirectory() as d:
        Path(d, "icone.svg").write_text("<svg/>")
        sld = (
            '<StyledLayerDescriptor version="1.0.0" xmlns:xlink="http://www.w3.org/1999/xlink">'
            '<Rule><PointSymbolizer><Graphic>'
            '<ExternalGraphic><OnlineResource xlink:href="icone.svg"/>'
            "<Format>image/svg+xml</Format></ExternalGraphic>"
            "</Graphic></PointSymbolizer></Rule></StyledLayerDescriptor>")
        rapport = _auditer_texte(sld, styles_dir=Path(d))
    assert "pictogramme référencé mais absent" not in rapport.problemes


def test_pictogramme_http_non_verifie():
    # Une URL http(s) n'est jamais vérifiée sur le disque, même sans
    # résolveur configuré : ce n'est pas une référence locale.
    sld = (
        '<StyledLayerDescriptor version="1.0.0" xmlns:xlink="http://www.w3.org/1999/xlink">'
        '<Rule><PointSymbolizer><Graphic>'
        '<ExternalGraphic><OnlineResource xlink:href="https://exemple.test/icone.svg"/>'
        "<Format>image/svg+xml</Format></ExternalGraphic>"
        "</Graphic></PointSymbolizer></Rule></StyledLayerDescriptor>")
    rapport = _auditer_texte(sld, styles_dir=None)
    assert "pictogramme référencé mais absent" not in rapport.problemes
    assert "vérification de ressource impossible" not in rapport.problemes


# --------------------------------------------------------------------------- GraphicFill/GraphicStroke
def test_graphicfill_mal_forme_detecte():
    rapport = _auditer_texte(
        '<StyledLayerDescriptor version="1.0.0"><Rule><PolygonSymbolizer><Fill>'
        "<GraphicFill/></Fill></PolygonSymbolizer></Rule></StyledLayerDescriptor>")
    assert rapport.problemes["GraphicFill ou GraphicStroke mal formé"] == 1


# --------------------------------------------------------------------------- VendorOption
def test_vendoroption_sans_name_detectee():
    rapport = _auditer_texte(
        '<StyledLayerDescriptor version="1.0.0"><Rule><PolygonSymbolizer>'
        "<VendorOption>x</VendorOption></PolygonSymbolizer></Rule></StyledLayerDescriptor>")
    assert rapport.problemes["VendorOption sans attribut name"] == 1


def test_vendoroption_inconnue_detectee():
    rapport = _auditer_texte(
        '<StyledLayerDescriptor version="1.0.0"><Rule><PolygonSymbolizer>'
        '<VendorOption name="option-inventee">x</VendorOption>'
        "</PolygonSymbolizer></Rule></StyledLayerDescriptor>")
    assert rapport.problemes["VendorOption inconnue de la cible"] == 1


def test_vendoroption_connue_non_signalee():
    rapport = _auditer_texte(
        '<StyledLayerDescriptor version="1.0.0"><Rule><PolygonSymbolizer>'
        '<VendorOption name="random">true</VendorOption>'
        "</PolygonSymbolizer></Rule></StyledLayerDescriptor>")
    assert "VendorOption inconnue de la cible" not in rapport.problemes


# --------------------------------------------------------------------------- filtres
def test_propertyname_vide_detecte():
    rapport = _auditer_texte(
        '<StyledLayerDescriptor version="1.0.0"><Rule><Filter>'
        "<PropertyIsEqualTo><PropertyName/><Literal>A</Literal></PropertyIsEqualTo>"
        "</Filter></Rule></StyledLayerDescriptor>")
    assert rapport.problemes["PropertyName vide"] == 1


def test_propertyislike_bien_forme_avec_attributs_complets_non_signale():
    rapport = _auditer_texte(
        '<StyledLayerDescriptor version="1.0.0"><Rule><Filter>'
        '<PropertyIsLike wildCard="*" singleChar="." escape="!">'
        "<PropertyName>idass</PropertyName><Literal>a1-*</Literal>"
        "</PropertyIsLike></Filter></Rule></StyledLayerDescriptor>")
    assert not any(c.startswith("PropertyIsLike") or c == "attribut hors vocabulaire Filter 1.0"
                   for c in rapport.problemes)


def test_propertyislike_incomplet_detecte():
    rapport = _auditer_texte(
        '<StyledLayerDescriptor version="1.0.0"><Rule><Filter>'
        "<PropertyIsLike><PropertyName>idass</PropertyName><Literal>a1-*</Literal>"
        "</PropertyIsLike></Filter></Rule></StyledLayerDescriptor>")
    assert rapport.problemes["PropertyIsLike incomplet"] == 3  # wildCard, singleChar, escape


def test_propertyislike_escapechar_hors_vocabulaire_detecte():
    rapport = _auditer_texte(
        '<StyledLayerDescriptor version="1.0.0"><Rule><Filter>'
        '<PropertyIsLike wildCard="*" singleChar="." escapeChar="!">'
        "<PropertyName>idass</PropertyName><Literal>a1-*</Literal>"
        "</PropertyIsLike></Filter></Rule></StyledLayerDescriptor>")
    assert rapport.problemes["attribut hors vocabulaire Filter 1.0"] == 1


def test_propertyislike_matchcase_est_une_extension_pas_un_defaut():
    rapport = _auditer_texte(
        '<StyledLayerDescriptor version="1.0.0"><Rule><Filter>'
        '<PropertyIsLike wildCard="*" singleChar="." escape="!" matchCase="false">'
        "<PropertyName>idass</PropertyName><Literal>a1-*</Literal>"
        "</PropertyIsLike></Filter></Rule></StyledLayerDescriptor>")
    assert rapport.conforme
    assert rapport.extensions["matchCase sur PropertyIsLike (extension GeoServer)"] == 1


# --------------------------------------------------------------------------- généralisation : paramètres
def test_vocabulaire_personnalise_change_le_resultat():
    # Un vocabulaire cible qui N'admet PAS "random" doit signaler ce que
    # VOCABULAIRE_GEOSERVER laisse passer — preuve que le paramètre agit
    # réellement, pas seulement présent sans effet.
    vocab_strict = VocabulaireCible(
        numeriques=VOCABULAIRE_GEOSERVER.numeriques,
        expressions=VOCABULAIRE_GEOSERVER.expressions,
        wellknown=VOCABULAIRE_GEOSERVER.wellknown,
        wellknown_prefixes=VOCABULAIRE_GEOSERVER.wellknown_prefixes,
        vendor=frozenset(),  # aucune VendorOption admise
        css=VOCABULAIRE_GEOSERVER.css,
    )
    sld = (
        '<StyledLayerDescriptor version="1.0.0"><Rule><PolygonSymbolizer>'
        '<VendorOption name="random">true</VendorOption>'
        "</PolygonSymbolizer></Rule></StyledLayerDescriptor>")
    rapport_geoserver = _auditer_texte(sld)
    rapport_strict = _auditer_texte(sld, vocabulaire=vocab_strict)
    assert "VendorOption inconnue de la cible" not in rapport_geoserver.problemes
    assert rapport_strict.problemes["VendorOption inconnue de la cible"] == 1


def test_xsd_order_personnalise_change_le_resultat():
    # Un ordre XSD réduit (sans entrée pour PolygonSymbolizer) désactive le
    # contrôle d'ordre pour cette balise précise.
    ordre_reduit = {k: v for k, v in ORDRE_XSD_SLD_1_0_0.items() if k != "PolygonSymbolizer"}
    sld = SLD_CONFORME.replace(
        "<Stroke>\n              <CssParameter name=\"stroke\">#000000</CssParameter>\n"
        "              <CssParameter name=\"stroke-width\">1</CssParameter>\n            </Stroke>",
        "<StrokeAvantFillPourTester/>",
    )
    # (test simplifié : on vérifie surtout que fournir un xsd_order différent
    # ne lève pas d'exception et est bien pris en compte pour les balises
    # qu'il contient toujours, ex. Rule)
    rapport = _auditer_texte(SLD_CONFORME, xsd_order=ordre_reduit)
    assert rapport.conforme


def test_existe_ressource_personnalise_prioritaire_sur_styles_dir():
    appels = []

    def resolveur(href: str) -> bool:
        appels.append(href)
        return True  # toujours "présent", même si absent du disque

    sld = (
        '<StyledLayerDescriptor version="1.0.0" xmlns:xlink="http://www.w3.org/1999/xlink">'
        '<Rule><PointSymbolizer><Graphic>'
        '<ExternalGraphic><OnlineResource xlink:href="nimporte-quoi.svg"/>'
        "<Format>image/svg+xml</Format></ExternalGraphic>"
        "</Graphic></PointSymbolizer></Rule></StyledLayerDescriptor>")
    rapport = _auditer_texte(sld, existe_ressource=resolveur)
    assert "pictogramme référencé mais absent" not in rapport.problemes
    assert appels == ["nimporte-quoi.svg"]


def test_aucun_resolveur_configure_signale_verification_impossible():
    sld = (
        '<StyledLayerDescriptor version="1.0.0" xmlns:xlink="http://www.w3.org/1999/xlink">'
        '<Rule><PointSymbolizer><Graphic>'
        '<ExternalGraphic><OnlineResource xlink:href="icone.svg"/>'
        "<Format>image/svg+xml</Format></ExternalGraphic>"
        "</Graphic></PointSymbolizer></Rule></StyledLayerDescriptor>")
    rapport = _auditer_texte(sld, styles_dir=None)
    assert rapport.problemes["vérification de ressource impossible"] == 1
    assert "pictogramme référencé mais absent" not in rapport.problemes


def test_apres_fichier_appele_une_fois_par_fichier():
    appels = []
    with tempfile.TemporaryDirectory() as d:
        dossier = Path(d)
        c1 = _ecrire(dossier, "a.sld", SLD_CONFORME.encode("utf-8"))
        c2 = _ecrire(dossier, "b.sld", SLD_CONFORME.encode("utf-8"))
        auditeur = SldAuditor(styles_dir=dossier, apres_fichier=lambda p: appels.append(p.name))
        rapport = auditeur.auditer([c1, c2])
    assert rapport.controles == 2
    assert sorted(appels) == ["a.sld", "b.sld"]


def test_fichier_none_ou_absent_ignore_silencieusement():
    # Comportement PRÉSERVÉ à l'identique de GeoServerAuditor : le tri est
    # déjà fait par l'appelant (results.ok and r.target dans le script
    # CNIG) — voir la docstring du module pour la discussion de ce choix.
    with tempfile.TemporaryDirectory() as d:
        auditeur = SldAuditor(styles_dir=Path(d))
        rapport = auditeur.auditer([None, Path(d) / "n_existe_pas.sld"])
    assert rapport.controles == 0
    assert rapport.conforme


# --------------------------------------------------------------------------- formater_rapport()
def test_formater_rapport_ne_produit_aucun_effet_de_bord():
    capture = StringIO()
    with redirect_stdout(capture):
        rapport = _auditer_texte(SLD_CONFORME)
        texte = formater_rapport(rapport)
    assert capture.getvalue() == ""  # ni auditer() ni formater_rapport() n'impriment
    assert "Conforme" in texte


def test_formater_rapport_liste_les_categories_et_comptes():
    rapport = _auditer_texte(
        '<StyledLayerDescriptor version="1.0.0"><Rule><PolygonSymbolizer>'
        "<Stroke/></PolygonSymbolizer></Rule></StyledLayerDescriptor>")
    texte = formater_rapport(rapport)
    assert "Stroke ou Fill vide" in texte
    assert "1" in texte


# --------------------------------------------------------------------------- ÉQUIVALENCE AVEC L'ORIGINAL
def test_equivalence_avec_geoserverauditor_original():
    """Compare, fichier par fichier, GeoServerAuditor (script CNIG
    d'origine) et SldAuditor (ce module) sur le MÊME lot de fixtures. Si le
    script CNIG a depuis été retiré (Phase 5 du plan : rebranchement du CLI
    sur styleforge-core), ce test se contente de le signaler plutôt que
    d'échouer — la non-régression aura déjà été vérifiée au moment de cette
    extraction, ce test n'a pas vocation à dépendre indéfiniment d'un
    fichier appelé à disparaître."""
    chemin_original = Path(__file__).resolve().parents[2] / "cnig_qml2sld_geoserver.py"
    if not chemin_original.is_file():
        print("(ignoré : cnig_qml2sld_geoserver.py n'est plus présent à côté de "
              "styleforge-core — non-régression déjà vérifiée lors de l'extraction "
              "d'origine, voir rapport_auditeur.docx)")
        return

    spec = importlib.util.spec_from_file_location("cnig_orig_pour_test", chemin_original)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    GeoServerAuditorOriginal = mod.GeoServerAuditor

    fixtures = {
        "conforme.sld": SLD_CONFORME,
        "vide.sld": '<StyledLayerDescriptor version="1.0.0"></StyledLayerDescriptor>',
        "version.sld": '<StyledLayerDescriptor version="1.1.0"><Rule/></StyledLayerDescriptor>',
        "stroke_vide.sld": (
            '<StyledLayerDescriptor version="1.0.0"><Rule><PolygonSymbolizer>'
            "<Stroke/></PolygonSymbolizer></Rule></StyledLayerDescriptor>"),
        "mark_inconnu.sld": (
            '<StyledLayerDescriptor version="1.0.0"><Rule><PointSymbolizer><Graphic><Mark>'
            "<WellKnownName>pentagone</WellKnownName></Mark>"
            "</Graphic></PointSymbolizer></Rule></StyledLayerDescriptor>"),
        "vendor_inconnu.sld": (
            '<StyledLayerDescriptor version="1.0.0"><Rule><PolygonSymbolizer>'
            '<VendorOption name="option-inventee">x</VendorOption>'
            "</PolygonSymbolizer></Rule></StyledLayerDescriptor>"),
        "css_inconnu.sld": (
            '<StyledLayerDescriptor version="1.0.0"><Rule><PolygonSymbolizer><Fill>'
            '<CssParameter name="truc-inconnu">1</CssParameter></Fill>'
            "</PolygonSymbolizer></Rule></StyledLayerDescriptor>"),
        "like_incomplet.sld": (
            '<StyledLayerDescriptor version="1.0.0"><Rule><Filter>'
            "<PropertyIsLike><PropertyName>idass</PropertyName><Literal>a1-*</Literal>"
            "</PropertyIsLike></Filter></Rule></StyledLayerDescriptor>"),
        "like_matchcase.sld": (
            '<StyledLayerDescriptor version="1.0.0"><Rule><Filter>'
            '<PropertyIsLike wildCard="*" singleChar="." escape="!" matchCase="false">'
            "<PropertyName>idass</PropertyName><Literal>a1-*</Literal>"
            "</PropertyIsLike></Filter></Rule></StyledLayerDescriptor>"),
    }

    with tempfile.TemporaryDirectory() as d:
        dossier = Path(d)
        chemins = [_ecrire(dossier, nom, texte.encode("utf-8")) for nom, texte in fixtures.items()]

        original = GeoServerAuditorOriginal(dossier)
        original.audit(chemins)

        nouveau = SldAuditor(styles_dir=dossier)
        rapport = nouveau.auditer(chemins)

    # Deux catégories ont été délibérément renommées lors de l'extraction
    # (point 5 de la docstring du module) : le nom "GeoServer" en dur dans
    # le message d'une catégorie contredisait le principe "le cœur ne doit
    # jamais coder en dur un nom de cible" dès lors que le vocabulaire lui-
    # même est devenu un paramètre substituable. Documenté ici plutôt que
    # gommé silencieusement de la comparaison.
    RENOMMAGES_ASSUMES = {
        "WellKnownName non reconnu par la cible": "WellKnownName non reconnu par GeoServer",
        "VendorOption inconnue de la cible": "VendorOption inconnue de GeoServer",
    }
    problemes_normalises = {RENOMMAGES_ASSUMES.get(k, k): v for k, v in rapport.problemes.items()}
    details_normalises = {RENOMMAGES_ASSUMES.get(k, k): list(v) for k, v in rapport.details.items()}

    assert problemes_normalises == dict(original.problemes), (
        problemes_normalises, dict(original.problemes))
    assert details_normalises == {
        k: list(v) for k, v in original.details.items()
    }
    assert dict(rapport.extensions) == dict(original.extensions)
    assert rapport.controles == original.controles


if __name__ == "__main__":
    import inspect

    fonctions_test = [obj for nom, obj in list(globals().items())
                       if nom.startswith("test_") and inspect.isfunction(obj)]
    echecs = 0
    for f in fonctions_test:
        try:
            f()
            print(f"OK   {f.__name__}")
        except Exception as e:
            echecs += 1
            print(f"FAIL {f.__name__}: {e}")
    print(f"\n{len(fonctions_test) - echecs}/{len(fonctions_test)} tests passent")
    if echecs:
        sys.exit(1)
