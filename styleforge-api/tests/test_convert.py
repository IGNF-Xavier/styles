# -*- coding: utf-8 -*-
from __future__ import annotations


def test_convert_sld_seul(client, entetes_auth, chemin_qml_valide):
    with open(chemin_qml_valide, "rb") as f:
        r = client.post(
            "/v1/convert",
            headers=entetes_auth,
            files={"fichier_qml": ("test_simple.qml", f, "application/xml")},
            data={"cible": "sld"},
        )
    assert r.status_code == 200, r.text
    corps = r.json()
    assert corps["sld"] is not None
    assert "<FeatureTypeStyle" in corps["sld"] or "FeatureTypeStyle" in corps["sld"]
    assert corps["mbstyle"] is None
    assert corps["nom_style"] == "test_simple"


def test_convert_mbstyle_sans_parametres_source_422(client, entetes_auth, chemin_qml_valide):
    with open(chemin_qml_valide, "rb") as f:
        r = client.post(
            "/v1/convert",
            headers=entetes_auth,
            files={"fichier_qml": ("test_simple.qml", f, "application/xml")},
            data={"cible": "mbstyle"},
        )
    assert r.status_code == 422
    detail = r.json()["detail"]
    assert detail["type_erreur"] == "ParametresSourceManquants"


def test_convert_sld_et_mbstyle_avec_parametres_source(client, entetes_auth, chemin_qml_valide):
    with open(chemin_qml_valide, "rb") as f:
        r = client.post(
            "/v1/convert",
            headers=entetes_auth,
            files={"fichier_qml": ("test_simple.qml", f, "application/xml")},
            data={
                "cible": "sld_et_mbstyle",
                "id_source": "ma_source",
                "url_source": "https://tuiles.example.org/{z}/{x}/{y}.pbf",
                "nom_couche_source": "test_simple",
            },
        )
    assert r.status_code == 200, r.text
    corps = r.json()
    assert corps["sld"] is not None
    assert corps["mbstyle"] is not None
    assert corps["mbstyle"]["layers"]


def test_convert_qml_invalide_422_nomme(client, entetes_auth, chemin_qml_invalide):
    with open(chemin_qml_invalide, "rb") as f:
        r = client.post(
            "/v1/convert",
            headers=entetes_auth,
            files={"fichier_qml": ("invalide.qml", f, "application/xml")},
            data={"cible": "sld"},
        )
    assert r.status_code == 422
    detail = r.json()["detail"]
    # Une exception NOMMÉE de styleforge_core.readers.qml (ErreurLectureQML
    # ou une sous-classe), jamais un message générique.
    assert detail["module_erreur"] == "styleforge_core.readers.qml"
    assert detail["type_erreur"] in (
        "DocumentQMLInvalide", "RendererNonSupporte",
        "CoucheDeSymboleNonSupportee",
    )
