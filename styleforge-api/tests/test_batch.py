# -*- coding: utf-8 -*-
from __future__ import annotations

import pytest


def _traiter_la_file(redis_demarre) -> None:
    """Traite tout ce qu'il y a dans la file en mode 'burst' (s'arrête une
    fois la file vide) avec SimpleWorker — exécute le job dans CE
    processus, sans fork, pour rester déterministe dans un bac à sable de
    test. worker.py (production) utilise rq.Worker, pas SimpleWorker —
    voir sa docstring."""
    from rq.worker import SimpleWorker

    from styleforge_api.queue import NOM_FILE, obtenir_connexion

    worker = SimpleWorker([NOM_FILE], connection=obtenir_connexion())
    worker.work(burst=True)


def test_batch_id_inconnu_404(client, entetes_auth, redis_demarre):
    r = client.get("/v1/batch/id-qui-nexiste-pas", headers=entetes_auth)
    assert r.status_code == 404


def test_batch_cree_puis_traite_avec_succes(
    client, entetes_auth, chemin_qml_valide, redis_demarre
):
    with open(chemin_qml_valide, "rb") as f:
        r = client.post(
            "/v1/batch",
            headers=entetes_auth,
            files={"fichiers_qml": ("test_simple.qml", f, "application/xml")},
            data={"cible": "sld"},
        )
    assert r.status_code == 202, r.text
    corps = r.json()
    id_lot = corps["id_lot"]
    assert corps["statut"] == "en_attente"
    assert corps["nombre_fichiers"] == 1

    _traiter_la_file(redis_demarre)

    r2 = client.get(f"/v1/batch/{id_lot}", headers=entetes_auth)
    assert r2.status_code == 200, r2.text
    corps2 = r2.json()
    assert corps2["statut"] == "termine"
    assert corps2["fichiers_traites"] == 1
    assert corps2["reussites"] == 1
    assert corps2["echecs"] == 0
    assert corps2["resultats"][0]["statut"] == "ok"
    assert corps2["resultats"][0]["resultat"]["sld"] is not None


def test_batch_fichier_en_echec_nimpacte_pas_les_autres(
    client, entetes_auth, chemin_qml_valide, chemin_qml_invalide, redis_demarre
):
    with open(chemin_qml_valide, "rb") as f1, open(chemin_qml_invalide, "rb") as f2:
        r = client.post(
            "/v1/batch",
            headers=entetes_auth,
            files=[
                ("fichiers_qml", ("valide.qml", f1, "application/xml")),
                ("fichiers_qml", ("invalide.qml", f2, "application/xml")),
            ],
            data={"cible": "sld"},
        )
    assert r.status_code == 202, r.text
    id_lot = r.json()["id_lot"]

    _traiter_la_file(redis_demarre)

    r2 = client.get(f"/v1/batch/{id_lot}", headers=entetes_auth)
    corps2 = r2.json()
    assert corps2["statut"] == "termine"
    assert corps2["fichiers_traites"] == 2
    assert corps2["reussites"] == 1
    assert corps2["echecs"] == 1
    statuts = {r["nom"]: r["statut"] for r in corps2["resultats"]}
    assert statuts["valide.qml"] == "ok"
    assert statuts["invalide.qml"] == "echec"
    erreur = next(r for r in corps2["resultats"] if r["nom"] == "invalide.qml")["erreur"]
    assert erreur is not None
    assert erreur["module_erreur"] == "styleforge_core.readers.qml"
