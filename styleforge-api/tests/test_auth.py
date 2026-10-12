# -*- coding: utf-8 -*-
from __future__ import annotations


def test_schema_sans_cle_echoue(client):
    # /v1/convert est protégé ; on vérifie le rejet AVANT même de monter un
    # fichier, pour isoler le comportement d'authentification du reste.
    r = client.post("/v1/convert")
    assert r.status_code == 401
    assert "X-API-Key" in r.json()["detail"]


def test_cle_invalide_rejetee(client):
    r = client.post("/v1/convert", headers={"X-API-Key": "mauvaise-cle"})
    assert r.status_code == 401
    assert r.json()["detail"] == "Clé API invalide."


def test_aucune_cle_configuree_ferme_le_service(client, monkeypatch):
    import styleforge_api.auth as auth_mod

    monkeypatch.delenv("STYLEFORGE_API_KEYS", raising=False)
    auth_mod._authentifieur_par_defaut = None
    r = client.post("/v1/convert", headers={"X-API-Key": "peu-importe"})
    assert r.status_code == 503


def test_cle_valide_passe_lauthentification(client, entetes_auth, chemin_qml_valide):
    # Avec une clé valide mais sans fichier joint, on doit dépasser l'étape
    # d'authentification et échouer plus loin (422 de validation FastAPI
    # sur le champ requis), jamais 401.
    r = client.post("/v1/convert", headers=entetes_auth)
    assert r.status_code != 401
