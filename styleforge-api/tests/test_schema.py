# -*- coding: utf-8 -*-
from __future__ import annotations


def test_schema_pivot_public_et_bien_forme(client):
    r = client.get("/v1/schema")
    assert r.status_code == 200
    corps = r.json()
    assert corps["pivot_version"] == "v1"
    assert corps["schema"]["title"] or corps["schema"].get("$defs")
    # Les trois champs du pivot racine (voir Style.model_fields) doivent
    # apparaître dans le schéma JSON publié.
    proprietes = corps["schema"].get("properties", {})
    assert "rules" in proprietes


def test_health_sans_authentification(client):
    r = client.get("/v1/health")
    assert r.status_code == 200
    assert r.json()["statut"] == "ok"
