# -*- coding: utf-8 -*-
"""
styleforge_api.auth — Authentification, derrière une interface remplaçable.

Le document de roadmap (plan_bibliotheque_styleforge.docx, section 8.2)
laisse explicitement ouverte la question « service destiné à rester
interne, ou ouvert à d'autres organisations » — elle conditionne le choix
entre une simple clé API et une authentification par jeton/organisation
avec quotas. Cette question n'a pas été tranchée au moment d'écrire ce
module (réponse de l'utilisateur : "pas prioritaire maintenant").

Pour ne pas bloquer la phase 6 sur une décision produit qui n'est pas la
mienne à prendre, ET pour ne pas s'enfermer dans un choix d'architecture
qu'il faudrait ensuite défaire : l'authentification est une INTERFACE
(Authentifieur), jamais codée en dur dans les routes. L'implémentation par
défaut (CleApiStatique) couvre le cas "usage interne" ; le jour où la
réponse devient "ouvert à plusieurs organisations", une nouvelle
implémentation (jetons par organisation + quotas) peut être branchée SANS
toucher aux routes, qui ne connaissent que l'interface.
"""
from __future__ import annotations

import hmac
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import APIKeyHeader

NOM_ENTETE_CLE_API = "X-API-Key"


class Authentifieur(ABC):
    """Interface que toute stratégie d'authentification doit respecter.

    'identifiant_appelant' est délibérément un simple identifiant de
    traçabilité (p. ex. pour la journalisation — section 10 du plan :
    "la journalisation et les métriques d'usage dès le premier
    déploiement"), PAS encore un objet d'organisation/quota : ce
    raffinement est exactement ce que la décision ouverte de la section
    8.2 déterminerait, pas une anticipation à coder sans elle.
    """

    @abstractmethod
    def authentifier(self, cle_presentee: str | None) -> str:
        """Retourne un identifiant d'appelant si `cle_presentee` est
        valide, lève HTTPException(401) sinon. Ne retourne jamais
        silencieusement un succès par défaut sur une clé absente ou
        invalide — l'absence de décision sur le périmètre du service
        (interne/multi-organisations) ne doit JAMAIS se traduire par une
        absence de contrôle."""
        raise NotImplementedError


@dataclass
class CleApiStatique(Authentifieur):
    """Implémentation par défaut : un ensemble fixe de clés valides,
    partagées entre tous les appelants (pas de notion d'organisation ni
    de quota — cohérent avec un usage interne, l'hypothèse par défaut tant
    que la décision de la section 8.2 n'est pas prise).

    Les clés sont comparées en temps constant (hmac.compare_digest) pour
    ne pas introduire une fuite d'information par attaque temporelle sur
    un simple "in" — une précaution normale pour une comparaison de
    secret, même minime ici.
    """

    cles_valides: frozenset[str]

    @classmethod
    def depuis_environnement(
        cls, variable: str = "STYLEFORGE_API_KEYS"
    ) -> "CleApiStatique":
        """Construit l'ensemble des clés valides depuis une variable
        d'environnement (liste séparée par des virgules) — jamais une
        clé écrite en dur dans le code, conformément au principe
        'tout ce qui est un choix est un paramètre' du projet."""
        brut = os.environ.get(variable, "")
        cles = frozenset(c.strip() for c in brut.split(",") if c.strip())
        return cls(cles_valides=cles)

    def authentifier(self, cle_presentee: str | None) -> str:
        if not self.cles_valides:
            # Aucune clé configurée : plutôt que d'ouvrir le service sans
            # contrôle (dangereux et silencieux), on le ferme explicitement
            # — erreur de configuration signalée à CHAQUE appel, jamais un
            # service qui "marche" par accident faute de clé positionnée.
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Authentification non configurée côté serveur "
                       f"(variable d'environnement vide). Voir {__name__}.",
            )
        if cle_presentee is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"En-tête '{NOM_ENTETE_CLE_API}' manquant.",
            )
        for valide in self.cles_valides:
            if hmac.compare_digest(cle_presentee, valide):
                return "appelant-authentifie"
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Clé API invalide.",
        )


# ----------------------------------------------------------------- câblage FastAPI
_cle_api_header = APIKeyHeader(name=NOM_ENTETE_CLE_API, auto_error=False)

#: Instance par défaut, remplaçable via app.dependency_overrides dans les
#: tests (voir tests/conftest.py) ou en redéfinissant obtenir_authentifieur
#: pour brancher une autre implémentation d'Authentifieur en production.
_authentifieur_par_defaut: Authentifieur | None = None


def obtenir_authentifieur() -> Authentifieur:
    global _authentifieur_par_defaut
    if _authentifieur_par_defaut is None:
        _authentifieur_par_defaut = CleApiStatique.depuis_environnement()
    return _authentifieur_par_defaut


def exiger_authentification(
    cle: str | None = Security(_cle_api_header),
    authentifieur: Authentifieur = Depends(obtenir_authentifieur),
) -> str:
    """Dépendance FastAPI à injecter dans chaque route protégée.
    Retourne l'identifiant d'appelant (pour la journalisation) ou lève
    une HTTPException 401/503 — jamais un passage silencieux."""
    return authentifieur.authentifier(cle)
