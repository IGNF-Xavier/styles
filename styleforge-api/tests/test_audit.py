# -*- coding: utf-8 -*-
from __future__ import annotations


def _produire_sld(client, entetes_auth, chemin_qml) -> str:
    with open(chemin_qml, "rb") as f:
        r = client.post(
            "/v1/convert",
            headers=entetes_auth,
            files={"fichier_qml": ("test_simple.qml", f, "application/xml")},
            data={"cible": "sld"},
        )
    assert r.status_code == 200, r.text
    return r.json()["sld"]


def test_audit_sld_conforme(client, entetes_auth, chemin_qml_valide):
    sld = _produire_sld(client, entetes_auth, chemin_qml_valide)
    r = client.post(
        "/v1/audit",
        headers=entetes_auth,
        files={"fichiers_sld": ("test_simple.sld", sld.encode("utf-8"), "application/xml")},
    )
    assert r.status_code == 200, r.text
    corps = r.json()
    assert corps["fichiers_controles"] == 1
    assert corps["conforme"] is True
    assert corps["problemes"] == []


def test_audit_sld_malforme_non_conforme(client, entetes_auth):
    r = client.post(
        "/v1/audit",
        headers=entetes_auth,
        files={"fichiers_sld": ("casse.sld", b"<ceci-n-est-pas-un-sld/>", "application/xml")},
    )
    assert r.status_code == 200, r.text
    corps = r.json()
    assert corps["conforme"] is False
    assert corps["problemes"]
