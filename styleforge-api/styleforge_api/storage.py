# -*- coding: utf-8 -*-
"""
styleforge_api.storage — Stockage des fichiers de lot, derrière une
interface remplaçable.

Le plan de bibliothèque (section 8.2) tranche explicitement : "Stockage
des fichiers de lot : objet, avec expiration automatique — les styles d'un
client sont potentiellement de la donnée métier sensible, à ne jamais
garder plus que nécessaire." Et la section 11 (sécurité) : "Politique de
conservation minimale, [...] purge automatique après traitement des
lots."

Cette première itération n'a ni compte object storage (S3/GCS/Azure) ni
décision sur lequel utiliser — ce n'est pas une décision de ce module.
L'implémentation par défaut (StockageFichierLocal) respecte néanmoins DÉJÀ
le principe retenu (expiration automatique, purge), sur le système de
fichiers local, derrière la MÊME interface qu'un futur backend S3/GCS :
brancher un véritable stockage objet plus tard ne demandera de changer que
l'implémentation, jamais les appelants (styleforge_api.jobs, routers.batch).
"""
from __future__ import annotations

import json
import os
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path


class CleAbsente(Exception):
    """Levée par lire()/metadonnees() quand `cle` n'existe pas ou a
    expiré — jamais un None silencieux qui masquerait la différence entre
    "jamais écrit" et "purgé après expiration"."""


class StockageObjets(ABC):
    """Interface minimale nécessaire au traitement de lot. Volontairement
    étroite (écrire/lire/existe/purger_expires) plutôt qu'un calque complet
    d'une API S3 — c'est tout ce dont styleforge_api.jobs a besoin ; un
    backend réel (S3/GCS) peut toujours offrir plus, jamais moins, que
    cette interface."""

    @abstractmethod
    def ecrire(self, cle: str, contenu: bytes, *, ttl_secondes: float) -> None: ...

    @abstractmethod
    def lire(self, cle: str) -> bytes: ...

    @abstractmethod
    def existe(self, cle: str) -> bool: ...

    @abstractmethod
    def purger_expires(self) -> int:
        """Supprime les objets dont le TTL est dépassé. Retourne le
        nombre d'objets purgés — jamais appelé implicitement par
        ecrire()/lire() : l'appelant (un job planifié, ou le worker entre
        deux lots) décide explicitement quand purger, pour que le coût et
        le moment de la purge restent visibles et paramétrables."""


@dataclass
class StockageFichierLocal(StockageObjets):
    """Implémentation par défaut : le système de fichiers local, un
    fichier de métadonnées JSON par clé (date d'expiration), une purge qui
    parcourt le répertoire. Convient à un déploiement mono-instance ; un
    déploiement multi-instances a besoin d'un stockage partagé (S3/GCS, ou
    un volume réseau) — brancher cette autre implémentation ne touche à
    rien d'autre que ce fichier, voir la docstring du module."""

    repertoire: Path

    def __post_init__(self) -> None:
        self.repertoire = Path(self.repertoire)
        self.repertoire.mkdir(parents=True, exist_ok=True)

    def _chemin_contenu(self, cle: str) -> Path:
        return self.repertoire / f"{cle}.bin"

    def _chemin_meta(self, cle: str) -> Path:
        return self.repertoire / f"{cle}.meta.json"

    def ecrire(self, cle: str, contenu: bytes, *, ttl_secondes: float) -> None:
        # `cle` peut contenir des "/" (ex. "<id_lot>/<nom_fichier>" côté
        # lots, voir routers.batch) : ce n'est PAS un nom de fichier plat,
        # les répertoires intermédiaires doivent être créés à la volée.
        chemin_contenu = self._chemin_contenu(cle)
        chemin_contenu.parent.mkdir(parents=True, exist_ok=True)
        chemin_contenu.write_bytes(contenu)
        expiration = time.time() + ttl_secondes
        self._chemin_meta(cle).write_text(
            json.dumps({"expire_a": expiration}), encoding="utf-8"
        )

    def _expire(self, cle: str) -> bool:
        meta = self._chemin_meta(cle)
        if not meta.is_file():
            return True
        try:
            donnees = json.loads(meta.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return True
        return time.time() >= donnees.get("expire_a", 0)

    def existe(self, cle: str) -> bool:
        return self._chemin_contenu(cle).is_file() and not self._expire(cle)

    def lire(self, cle: str) -> bytes:
        if not self.existe(cle):
            raise CleAbsente(cle)
        return self._chemin_contenu(cle).read_bytes()

    def purger_expires(self) -> int:
        compte = 0
        # rglob, pas glob : une clé peut contenir des "/" (ex. lots,
        # "<id_lot>/<nom_fichier>"), donc ses fichiers vivent dans des
        # sous-répertoires — glob("*.meta.json") ne les verrait jamais.
        for meta in self.repertoire.rglob("*.meta.json"):
            relatif = meta.relative_to(self.repertoire)
            cle = str(relatif)[: -len(".meta.json")]
            if self._expire(cle):
                self._chemin_contenu(cle).unlink(missing_ok=True)
                meta.unlink(missing_ok=True)
                compte += 1
        return compte


_stockage_par_defaut: StockageObjets | None = None


def obtenir_stockage() -> StockageObjets:
    """Point d'injection unique, utilisé par routers.batch et jobs — une
    dépendance FastAPI (routes) peut le surcharger en test ; jobs.py
    (hors requête HTTP, exécuté par le worker RQ) l'appelle directement."""
    global _stockage_par_defaut
    if _stockage_par_defaut is None:
        repertoire = os.environ.get(
            "STYLEFORGE_API_STOCKAGE_LOTS", "/tmp/styleforge-api-lots"
        )
        _stockage_par_defaut = StockageFichierLocal(Path(repertoire))
    return _stockage_par_defaut
