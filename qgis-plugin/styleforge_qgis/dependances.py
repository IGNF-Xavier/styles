# -*- coding: utf-8 -*-
"""Detection et installation de styleforge-core dans l'environnement
Python de QGIS.

Piege verifie empiriquement (QGIS 3.40.4, Windows) : sys.executable
dans l'interpreteur Python embarque de QGIS pointe vers le binaire
GRAPHIQUE (ex. "qgis-ltr-bin.exe"), pas vers un executable Python
utilisable en sous-processus - un appel
subprocess.run([sys.executable, "-m", "pip", ...]) s'y bloque
indefiniment (timeout) plutot que d'echouer proprement, au lieu
d'executer pip. Ce module cherche donc l'executable Python "nu" livre
a cote de QGIS (ex. "<install QGIS>/apps/Python312/python.exe" sur
Windows) plutot que de supposer que sys.executable convient - jamais
une hypothese non verifiee.

Rien dans ce module n'installe quoi que ce soit sans un geste explicite
de l'utilisateur dans le dialogue (bouton "Installer") : la detection
seule (trouver_python_utilisable, styleforge_core_disponible) ne fait
aucune ecriture sur le systeme.
"""
from __future__ import annotations

import importlib
import importlib.util
import subprocess
import sys
from pathlib import Path
from typing import Optional, Tuple

from qgis.PyQt.QtCore import QSettings

CLE_PYTHON_SETTINGS = "styleforge_qgis/chemin_python"
DELAI_VERIFICATION_S = 8
DELAI_INSTALLATION_S = 300


def styleforge_core_disponible() -> bool:
    """True si styleforge_core est importable MAINTENANT. Invalide le
    cache d'imports avant de tester : apres une installation reussie
    dans la meme session QGIS, sans ca, importlib continuerait a
    croire le module absent (cache negatif) et redemanderait une
    installation deja faite - une forme d'echec silencieux qu'il faut
    eviter."""
    importlib.invalidate_caches()
    return importlib.util.find_spec("styleforge_core") is not None


def chemin_styleforge_core_source() -> Optional[Path]:
    """Localise le dossier source styleforge-core/ dans le depot
    "styles" dont ce plugin fait partie (qgis-plugin/ et
    styleforge-core/ sont des dossiers freres a la racine du depot).
    Retourne None si ce plugin a ete deplace/installe separement du
    reste du depot - jamais un chemin devine sans verification."""
    ici = Path(__file__).resolve()
    # ici = <depot>/qgis-plugin/styleforge_qgis/dependances.py
    for ancetre in ici.parents:
        candidat = ancetre / "styleforge-core"
        if (candidat / "pyproject.toml").is_file() and \
                (candidat / "styleforge_core" / "__init__.py").is_file():
            return candidat
    return None


def _executable_utilisable(chemin: Path, delai: int = DELAI_VERIFICATION_S) -> bool:
    """Verifie, avec un timeout borne, qu'un executable repond a
    "--version" sans se bloquer - plutot que de supposer qu'un chemin
    qui existe sur le disque est forcement un vrai interpreteur Python
    utilisable en sous-processus (voir le piege documente en tete de
    module)."""
    try:
        res = subprocess.run(
            [str(chemin), "--version"],
            capture_output=True, text=True, timeout=delai,
        )
        return res.returncode == 0 and "python" in (res.stdout + res.stderr).lower()
    except Exception:  # noqa: BLE001 - tout echec = inutilisable, jamais une exception qui remonte ici
        return False


def _candidats_python_embarque_windows(executable_qgis: Path) -> list[Path]:
    """QGIS pour Windows (installeur officiel/OSGeo4W) place l'interpreteur
    Python "nu" sous <racine_install>/apps/PythonXYZ/python.exe, a cote du
    binaire qgis-*.exe (verifie sur une installation reelle 3.40.4,
    "C:/Program Files/QGIS 3.40.4"). On remonte depuis le binaire plutot
    que de deviner un chemin absolu fige - chaque version de QGIS peut
    changer le numero de version Python embarquee."""
    candidats: list[Path] = []
    racine = executable_qgis.parent.parent  # .../bin/qgis-x.exe -> racine install
    dossier_apps = racine / "apps"
    if dossier_apps.is_dir():
        for sous in sorted(dossier_apps.glob("Python*")):
            exe = sous / "python.exe"
            if exe.is_file():
                candidats.append(exe)
    return candidats


def trouver_python_utilisable(forcer_nouvelle_recherche: bool = False) -> Optional[Path]:
    """Trouve un interpreteur Python capable d'executer pip en
    sous-processus depuis CET environnement QGIS. Ordre d'essai :
    1. chemin memorise (QSettings) d'une detection/saisie precedente ;
    2. sys.executable, SEULEMENT s'il ne ressemble pas au binaire
       graphique de QGIS (sinon : piege documente en tete de module) ;
    3. recherche du Python embarque a cote de l'executable QGIS
       (Windows uniquement pour l'instant - sur Linux/macOS,
       sys.executable est deja l'interpreteur reel dans les
       distributions QGIS connues).
    Retourne None si rien n'a fonctionne - laisse l'appelant demander
    le chemin a l'utilisateur plutot que d'echouer en silence."""
    parametres = QSettings()
    if not forcer_nouvelle_recherche:
        memorise = parametres.value(CLE_PYTHON_SETTINGS, "", type=str)
        if memorise and _executable_utilisable(Path(memorise)):
            return Path(memorise)

    executable_qgis = Path(sys.executable)
    ressemble_binaire_gui = "qgis" in executable_qgis.name.lower()

    if not ressemble_binaire_gui and _executable_utilisable(executable_qgis):
        parametres.setValue(CLE_PYTHON_SETTINGS, str(executable_qgis))
        return executable_qgis

    if sys.platform == "win32":
        for candidat in _candidats_python_embarque_windows(executable_qgis):
            if _executable_utilisable(candidat):
                parametres.setValue(CLE_PYTHON_SETTINGS, str(candidat))
                return candidat

    return None


def memoriser_python_choisi(chemin: Path) -> None:
    """Enregistre un chemin Python choisi manuellement par l'utilisateur
    (voir dialogue.py, bouton "Parcourir...") pour ne plus le redemander
    dans cette installation de QGIS."""
    QSettings().setValue(CLE_PYTHON_SETTINGS, str(chemin))


def installer_styleforge_core(python_exe: Path, source_dir: Path) -> Tuple[bool, str]:
    """Installe styleforge-core depuis sa source locale (sibling de ce
    plugin dans le depot "styles") via "pip install <chemin>". Retourne
    TOUJOURS la sortie combinee stdout+stderr, succes ou echec - jamais
    un succes/echec muet sans texte exploitable, puisque c'est
    precisement ce que l'utilisateur devra lire si pip echoue
    (dependance manquante, permissions, etc.)."""
    try:
        res = subprocess.run(
            [str(python_exe), "-m", "pip", "install", str(source_dir)],
            capture_output=True, text=True, timeout=DELAI_INSTALLATION_S,
        )
    except subprocess.TimeoutExpired as exc:
        return False, (
            f"Installation interrompue apres {DELAI_INSTALLATION_S}s sans "
            f"reponse de pip.\n\nSortie partielle :\n{exc.stdout or ''}"
            f"\n{exc.stderr or ''}"
        )
    except Exception as exc:  # noqa: BLE001
        return False, f"Impossible de lancer pip ({python_exe}) : {exc}"

    sortie = (res.stdout or "") + ("\n" + res.stderr if res.stderr else "")
    if res.returncode != 0:
        return False, sortie or f"pip a renvoye le code {res.returncode} sans sortie."
    importlib.invalidate_caches()
    return True, sortie
