# -*- coding: utf-8 -*-
"""Classe principale du plugin : cycle de vie QGIS (initGui/unload) et
point d'entree du menu/barre d'outils. Toute la logique de conversion
vit dans convertisseur.py/dependances.py ; toute l'interface vit dans
dialogue.py - ce fichier ne fait que les relier, comme __init__.py."""
from __future__ import annotations

from pathlib import Path

from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction


class StyleforgeQgisPlugin:
    def __init__(self, iface):
        self.iface = iface
        self._action: QAction | None = None
        self._dialogue = None  # créée à la demande, pas au chargement

    # ------------------------------------------------------------------
    # Cycle de vie QGIS
    # ------------------------------------------------------------------
    def initGui(self) -> None:  # noqa: N802 - nom impose par l'API QGIS
        icone = QIcon(str(Path(__file__).resolve().parent / "icon.png"))
        self._action = QAction(icone, "Styleforge — QML vers SLD/MBStyle…", self.iface.mainWindow())
        self._action.triggered.connect(self._ouvrir_dialogue)
        self.iface.addPluginToVectorMenu("&Styleforge", self._action)
        self.iface.addVectorToolBarIcon(self._action)

    def unload(self) -> None:  # noqa: N802 - nom impose par l'API QGIS
        if self._action is not None:
            self.iface.removePluginVectorMenu("&Styleforge", self._action)
            self.iface.removeVectorToolBarIcon(self._action)
            self._action = None
        if self._dialogue is not None:
            self._dialogue.close()
            self._dialogue = None

    # ------------------------------------------------------------------
    def _ouvrir_dialogue(self) -> None:
        # Importee ici (pas en tete de module) : dialogue.py importe
        # qgis.core/qgis.PyQt, et on veut que la moindre erreur
        # d'import a ce niveau s'affiche dans un message explicite
        # plutot que de faire echouer silencieusement le chargement du
        # plugin tout entier au demarrage de QGIS.
        from .dialogue import BoiteDialogueStyleforge

        if self._dialogue is None:
            self._dialogue = BoiteDialogueStyleforge(self.iface, self.iface.mainWindow())
        self._dialogue.show()
        self._dialogue.raise_()
        self._dialogue.activateWindow()
