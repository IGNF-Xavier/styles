# -*- coding: utf-8 -*-
"""Point d'entree QGIS du plugin Styleforge.

Convention standard des plugins QGIS : au chargement, QGIS importe CE
module (jamais plugin.py directement) et appelle classFactory(iface)
pour obtenir l'instance du plugin. Aucune logique metier ici -
uniquement l'aiguillage attendu par QGIS, pour que ce fichier reste
valide meme si le reste du plugin evolue.
"""


def classFactory(iface):  # noqa: N802 - nom impose par l'API QGIS
    from .plugin import StyleforgeQgisPlugin

    return StyleforgeQgisPlugin(iface)
