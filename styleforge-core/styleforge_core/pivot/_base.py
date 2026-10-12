# -*- coding: utf-8 -*-
"""
Classe de base commune à tous les modèles générés du pivot.

C'est ici, et nulle part dans _genere.py (généré, jamais édité à la main),
que se règle le comportement qui fait tout l'intérêt d'un pivot TYPÉ plutôt
qu'un dict libre : une clé inconnue lève une erreur explicite au lieu
d'être silencieusement ignorée. Par défaut, pydantic v2 IGNORE les champs
supplémentaires (extra="ignore") — un lecteur qui écrirait
"graphicFillDistance" au lieu de "graphicFillMargin" (le défaut constaté
chez bridge-style) ne serait jamais averti. extra="forbid" transforme cette
classe d'erreur en échec de validation immédiat, à la construction du
pivot, plutôt qu'en style silencieusement incomplet une fois écrit en SLD.
"""
from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class PivotBaseModel(BaseModel):
    model_config = ConfigDict(extra="forbid")
