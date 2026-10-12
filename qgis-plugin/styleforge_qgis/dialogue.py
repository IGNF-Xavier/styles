# -*- coding: utf-8 -*-
"""Boite de dialogue du plugin Styleforge.

Ecrite entierement en code (pas de fichier .ui / pyuic) pour rester
simple a maintenir avec une interface volontairement minimale (v1,
choix explicite de l'utilisateur : sortie SLD + case MBStyle, rien de
plus). Imports systematiquement via qgis.PyQt (jamais PyQt5/PyQt6
directement) et appels Qt uniquement par leurs formes compatibles
PyQt6/Qt6 (ex. .exec(), jamais .exec_()) : ce plugin cible QGIS 3.40 au
minimum, et doit rester chargeable sans modification sous QGIS 4.x
(migration PyQt6/Qt6 attendue - voir le README du plugin)."""
from __future__ import annotations

from pathlib import Path
from typing import List, Optional

from qgis.core import QgsProject
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtWidgets import (
    QCheckBox,
    QDialog,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QRadioButton,
    QVBoxLayout,
)

from . import convertisseur, dependances


class BoiteDialogueStyleforge(QDialog):
    def __init__(self, iface, parent=None):
        super().__init__(parent)
        self.iface = iface
        self.setWindowTitle("Styleforge — QML vers SLD / MBStyle")
        self.setMinimumWidth(560)
        self._construire_ui()
        self._rafraichir_etat_dependance()
        self._sur_changement_mode()

    # ------------------------------------------------------------------
    # Construction de l'interface
    # ------------------------------------------------------------------
    def _construire_ui(self) -> None:
        disposition = QVBoxLayout(self)

        self.etiquette_dependance = QLabel()
        self.etiquette_dependance.setWordWrap(True)
        self.bouton_installer = QPushButton("Installer styleforge-core…")
        self.bouton_installer.clicked.connect(self._installer_dependance)
        ligne_dependance = QHBoxLayout()
        ligne_dependance.addWidget(self.etiquette_dependance, 1)
        ligne_dependance.addWidget(self.bouton_installer)
        disposition.addLayout(ligne_dependance)

        disposition.addWidget(QLabel("<b>Source</b>"))
        self.radio_couche_active = QRadioButton("Couche active")
        self.radio_toutes_couches = QRadioButton("Toutes les couches chargées dans le projet")
        self.radio_dossier = QRadioButton("Dossier de fichiers .qml")
        self.radio_couche_active.setChecked(True)
        for bouton in (self.radio_couche_active, self.radio_toutes_couches, self.radio_dossier):
            bouton.toggled.connect(self._sur_changement_mode)
            disposition.addWidget(bouton)

        ligne_dossier_source = QHBoxLayout()
        self.champ_dossier_source = QLineEdit()
        self.champ_dossier_source.setPlaceholderText("Dossier contenant vos .qml…")
        self.bouton_parcourir_source = QPushButton("Parcourir…")
        self.bouton_parcourir_source.clicked.connect(self._choisir_dossier_source)
        ligne_dossier_source.addWidget(self.champ_dossier_source, 1)
        ligne_dossier_source.addWidget(self.bouton_parcourir_source)
        disposition.addLayout(ligne_dossier_source)

        disposition.addWidget(QLabel("<b>Sortie</b>"))
        ligne_dossier_sortie = QHBoxLayout()
        self.champ_dossier_sortie = QLineEdit()
        self.champ_dossier_sortie.setPlaceholderText("Dossier où écrire les .sld/.json…")
        bouton_parcourir_sortie = QPushButton("Parcourir…")
        bouton_parcourir_sortie.clicked.connect(self._choisir_dossier_sortie)
        ligne_dossier_sortie.addWidget(self.champ_dossier_sortie, 1)
        ligne_dossier_sortie.addWidget(bouton_parcourir_sortie)
        disposition.addLayout(ligne_dossier_sortie)

        self.case_mbstyle = QCheckBox("Produire aussi le MBStyle (Mapbox GL Style)")
        disposition.addWidget(self.case_mbstyle)

        avertissement_limite = QLabel(
            "Les pictogrammes SVG embarqués en base64 dans le QML sont "
            "déployés automatiquement (svg/cnig/ du dossier de sortie). "
            "En revanche, un SVG référencé par un chemin de fichier, ou "
            "un sprite MBStyle (pictogramme/motif pour le document "
            "Mapbox), n'est pas résolu par cette version : un style qui "
            "en dépend échoue explicitement pour ce document précis "
            "(voir le journal), plutôt qu'un rendu approximé. Utilisez "
            "le CLI (cnig_qml2sld_geoserver.py) pour ces cas."
        )
        avertissement_limite.setWordWrap(True)
        avertissement_limite.setStyleSheet("color: #7a5c00;")
        disposition.addWidget(avertissement_limite)

        self.journal = QPlainTextEdit()
        self.journal.setReadOnly(True)
        self.journal.setMinimumHeight(180)
        disposition.addWidget(self.journal, 1)

        ligne_boutons = QHBoxLayout()
        self.bouton_convertir = QPushButton("Convertir")
        self.bouton_convertir.clicked.connect(self._lancer_conversion)
        bouton_fermer = QPushButton("Fermer")
        bouton_fermer.clicked.connect(self.close)
        ligne_boutons.addStretch(1)
        ligne_boutons.addWidget(self.bouton_convertir)
        ligne_boutons.addWidget(bouton_fermer)
        disposition.addLayout(ligne_boutons)

    # ------------------------------------------------------------------
    # Etat de la dependance styleforge-core
    # ------------------------------------------------------------------
    def _rafraichir_etat_dependance(self) -> None:
        disponible = dependances.styleforge_core_disponible()
        if disponible:
            self.etiquette_dependance.setText("✓ styleforge-core est disponible.")
            self.bouton_installer.setVisible(False)
        else:
            self.etiquette_dependance.setText(
                "⚠ styleforge-core n'est pas installé dans l'environnement "
                "Python de QGIS."
            )
            self.bouton_installer.setVisible(True)
        self.bouton_convertir.setEnabled(disponible)

    def _installer_dependance(self) -> None:
        source = dependances.chemin_styleforge_core_source()
        if source is None:
            QMessageBox.critical(
                self, "Installation impossible",
                "Le dossier source de styleforge-core n'a pas été trouvé "
                "à côté de ce plugin — il a probablement été installé "
                "séparément du reste du dépôt « styles ».\n\n"
                "Installez-le manuellement depuis un terminal :\n"
                "pip install styleforge-core\n"
                "(ou le chemin vers le dossier styleforge-core/ du dépôt)",
            )
            return

        python_exe = dependances.trouver_python_utilisable()
        if python_exe is None:
            chemin_choisi, _ = QFileDialog.getOpenFileName(
                self, "Localiser l'interpréteur Python de QGIS",
                "", "Exécutable Python (python.exe python3 python)",
            )
            if not chemin_choisi:
                return
            python_exe = Path(chemin_choisi)
            dependances.memoriser_python_choisi(python_exe)

        self._log(f"Installation de styleforge-core depuis {source}…")
        self._log(f"(via {python_exe})")
        self.bouton_installer.setEnabled(False)
        self.setCursor(Qt.CursorShape.WaitCursor)
        try:
            succes, sortie = dependances.installer_styleforge_core(python_exe, source)
        finally:
            self.unsetCursor()
            self.bouton_installer.setEnabled(True)

        self._log(sortie)
        if succes:
            self._log("✓ Installation terminée.")
        else:
            self._log("✗ Installation échouée — voir le détail ci-dessus.")
            QMessageBox.warning(
                self, "Installation échouée",
                "L'installation de styleforge-core a échoué. Le détail "
                "complet est dans le journal de cette fenêtre.",
            )
        self._rafraichir_etat_dependance()

    # ------------------------------------------------------------------
    # Interactions
    # ------------------------------------------------------------------
    def _sur_changement_mode(self) -> None:
        mode_dossier = self.radio_dossier.isChecked()
        self.champ_dossier_source.setEnabled(mode_dossier)
        self.bouton_parcourir_source.setEnabled(mode_dossier)

    def _choisir_dossier_source(self) -> None:
        dossier = QFileDialog.getExistingDirectory(self, "Dossier source (.qml)")
        if dossier:
            self.champ_dossier_source.setText(dossier)

    def _choisir_dossier_sortie(self) -> None:
        dossier = QFileDialog.getExistingDirectory(self, "Dossier de sortie")
        if dossier:
            self.champ_dossier_sortie.setText(dossier)

    def _log(self, texte: str) -> None:
        self.journal.appendPlainText(texte)

    # ------------------------------------------------------------------
    # Conversion
    # ------------------------------------------------------------------
    def _lancer_conversion(self) -> None:
        if not dependances.styleforge_core_disponible():
            QMessageBox.warning(
                self, "Dépendance manquante",
                "styleforge-core n'est pas disponible — installez-le "
                "d'abord (bouton ci-dessus).",
            )
            return

        dossier_sortie_texte = self.champ_dossier_sortie.text().strip()
        if not dossier_sortie_texte:
            QMessageBox.warning(self, "Dossier de sortie manquant",
                                 "Choisissez un dossier de sortie.")
            return
        dossier_sortie = Path(dossier_sortie_texte)
        mbstyle_demande = self.case_mbstyle.isChecked()

        self.journal.clear()
        self.setCursor(Qt.CursorShape.WaitCursor)
        self.bouton_convertir.setEnabled(False)
        registre_svg = convertisseur.nouveau_registre_svg()
        try:
            resultats = self._executer_mode(dossier_sortie, mbstyle_demande, registre_svg)
        except Exception as exc:  # noqa: BLE001 - jamais une exception muette dans l'UI
            self._log(f"✗ Erreur inattendue : {exc}")
            QMessageBox.critical(self, "Erreur", str(exc))
            return
        finally:
            self.unsetCursor()
            self.bouton_convertir.setEnabled(True)

        if resultats is None:
            return

        for resultat in resultats:
            convertisseur.ecrire_fichiers_sortie(resultat, dossier_sortie)
            if resultat.ok:
                suffixe = f" ({len(resultat.avertissements)} avertissement(s))" if resultat.avertissements else ""
                self._log(f"✓ {resultat.nom}{suffixe}")
            else:
                self._log(f"✗ {resultat.nom} : {resultat.erreur}")

        n_svg = convertisseur.deployer_svg_embarque(registre_svg, dossier_sortie)
        if n_svg:
            self._log(f"{n_svg} pictogramme(s) SVG déployé(s) dans "
                       f"{dossier_sortie / convertisseur.SVG_SUBDIR}.")

        chemin_rapport = convertisseur.ecrire_rapport(
            resultats, dossier_sortie, mbstyle_demande=mbstyle_demande,
        )
        n_ok = sum(1 for r in resultats if r.ok)
        self._log("")
        self._log(f"Terminé : {n_ok}/{len(resultats)} converti(s).")
        self._log(f"Rapport : {chemin_rapport}")

    def _executer_mode(
        self, dossier_sortie: Path, mbstyle_demande: bool,
        registre_svg: dict,
    ) -> Optional[List[convertisseur.ResultatConversion]]:
        if self.radio_couche_active.isChecked():
            couche = self.iface.activeLayer() if self.iface else None
            if couche is None:
                QMessageBox.warning(self, "Aucune couche active",
                                     "Sélectionnez une couche dans le panneau avant de convertir.")
                return None
            self._log(f"Conversion de la couche active : {couche.name()}")
            return [convertisseur.convertir_couche(
                couche, mbstyle_demande=mbstyle_demande, registre_svg=registre_svg)]

        if self.radio_toutes_couches.isChecked():
            projet = QgsProject.instance()
            self._log("Conversion de toutes les couches chargées…")
            resultats = convertisseur.convertir_toutes_les_couches(
                projet, mbstyle_demande=mbstyle_demande, registre_svg=registre_svg)
            if not resultats:
                QMessageBox.information(
                    self, "Aucune couche vectorielle",
                    "Aucune couche vectorielle n'est chargée dans ce projet.")
                return None
            return resultats

        # Mode dossier
        dossier_source_texte = self.champ_dossier_source.text().strip()
        if not dossier_source_texte:
            QMessageBox.warning(self, "Dossier source manquant",
                                 "Choisissez un dossier contenant des .qml.")
            return None
        dossier_source = Path(dossier_source_texte)
        if not dossier_source.is_dir():
            QMessageBox.warning(self, "Dossier introuvable",
                                 f"{dossier_source} n'existe pas.")
            return None
        self._log(f"Conversion du dossier : {dossier_source}")
        resultats = convertisseur.convertir_dossier(
            dossier_source, mbstyle_demande=mbstyle_demande, registre_svg=registre_svg)
        if not resultats:
            QMessageBox.information(
                self, "Aucun fichier .qml",
                f"Aucun fichier .qml trouvé dans {dossier_source}.")
            return None
        return resultats
