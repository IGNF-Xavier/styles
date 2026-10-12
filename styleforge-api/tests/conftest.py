# -*- coding: utf-8 -*-
from __future__ import annotations

import os
import shutil
import socket
import subprocess
import tempfile
import time
from pathlib import Path

import pytest

CLE_API_TEST = "test-key-123"

_QML_SIMPLE_FILL = """\
<qgis version="3.40.4-Bratislava">
  <renderer-v2 type="singleSymbol" symbollevels="0" enableorderby="0" forceraster="0" referencescale="-1">
    <symbols>
      <symbol clip_to_extent="1" type="fill" name="0" alpha="1" frame_rate="10" is_animated="0" force_rhr="0">
        <layer class="SimpleFill" locked="0" pass="0" id="{0}" enabled="1">
          <Option type="Map">
            <Option type="QString" name="color" value="38,140,0,255"/>
            <Option type="QString" name="outline_color" value="0,0,0,255"/>
            <Option type="QString" name="outline_width" value="0.26"/>
            <Option type="QString" name="outline_width_unit" value="MM"/>
            <Option type="QString" name="style" value="solid"/>
            <Option type="QString" name="outline_style" value="solid"/>
          </Option>
        </layer>
      </symbol>
    </symbols>
  </renderer-v2>
</qgis>
"""

_QML_INVALIDE = "<qgis version=\"3.40.4\"><renderer-v2 type=\"inconnu\"/></qgis>"


def _port_libre() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.fixture(scope="session")
def redis_demarre():
    """Démarre un redis-server réel (pas fakeredis) dédié aux tests, sur un
    port libre — plus fidèle au comportement réel de styleforge_api.queue
    que de simuler le protocole Redis. Nécessite le binaire redis-server,
    déjà présent dans cet environnement (voir Bash: `which redis-server`)."""
    if shutil.which("redis-server") is None:
        pytest.skip("redis-server introuvable dans cet environnement")
    port = _port_libre()
    proc = subprocess.Popen(
        ["redis-server", "--port", str(port), "--daemonize", "no",
         "--save", "", "--appendonly", "no"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    for _ in range(50):
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=0.2):
                break
        except OSError:
            time.sleep(0.1)
    else:
        proc.terminate()
        pytest.skip("redis-server n'a pas démarré à temps")
    os.environ["STYLEFORGE_API_REDIS_URL"] = f"redis://127.0.0.1:{port}/0"
    yield f"redis://127.0.0.1:{port}/0"
    proc.terminate()
    proc.wait(timeout=5)


@pytest.fixture(autouse=True)
def environnement_isole(monkeypatch, tmp_path):
    """Isole chaque test : clé API connue, stockage de lots dans un
    répertoire temporaire propre, caches des singletons (auth, stockage,
    queue) réinitialisés pour relire les variables d'environnement du
    test courant plutôt que celles d'un test précédent."""
    monkeypatch.setenv("STYLEFORGE_API_KEYS", CLE_API_TEST)
    monkeypatch.setenv(
        "STYLEFORGE_API_STOCKAGE_LOTS", str(tmp_path / "lots")
    )

    import styleforge_api.auth as auth_mod
    import styleforge_api.storage as storage_mod
    import styleforge_api.queue as queue_mod

    auth_mod._authentifieur_par_defaut = None
    storage_mod._stockage_par_defaut = None
    queue_mod._connexion = None
    queue_mod._file = None
    yield
    auth_mod._authentifieur_par_defaut = None
    storage_mod._stockage_par_defaut = None
    queue_mod._connexion = None
    queue_mod._file = None


@pytest.fixture
def client():
    from fastapi.testclient import TestClient

    from styleforge_api.app import creer_application

    with TestClient(creer_application()) as c:
        yield c


@pytest.fixture
def entetes_auth():
    return {"X-API-Key": CLE_API_TEST}


@pytest.fixture
def chemin_qml_valide(tmp_path) -> Path:
    chemin = tmp_path / "test_simple.qml"
    chemin.write_text(_QML_SIMPLE_FILL, encoding="utf-8")
    return chemin


@pytest.fixture
def chemin_qml_invalide(tmp_path) -> Path:
    chemin = tmp_path / "invalide.qml"
    chemin.write_text(_QML_INVALIDE, encoding="utf-8")
    return chemin
