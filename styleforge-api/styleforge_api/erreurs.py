# -*- coding: utf-8 -*-
"""
styleforge_api.erreurs — Traduction des exceptions NOMMÉES de
styleforge-core en réponses HTTP structurées.

Principe du projet, rappelé ici parce qu'il est au cœur de ce module :
jamais d'échec silencieux. styleforge-core lève des exceptions précises
(ErreurLectureQML et ses sous-classes, ExpressionPivotNonEcrite) plutôt que
de produire un document tronqué ou approximé sans le dire. Le rôle de ce
module est de préserver cette précision jusqu'au client HTTP — PAS de la
réduire à un générique "500 Internal Server Error" ni à un vague "400 Bad
Request" sans détail exploitable.

Toute exception qui n'est PAS une de celles reconnues ici n'est PAS
interceptée : elle continue de remonter telle quelle (FastAPI la transforme
en 500 et la journalise). Masquer une erreur inattendue derrière un 422
"propre" serait exactement le genre de silence que ce projet proscrit.
"""
from __future__ import annotations

from fastapi import HTTPException, status

from styleforge_core.readers.qml import ErreurLectureQML
from styleforge_core.writers.mbstyle import (
    ExpressionPivotNonEcrite as ExpressionPivotNonEcriteMBStyle,
)
from styleforge_core.writers.sld import (
    ExpressionPivotNonEcrite as ExpressionPivotNonEcriteSLD,
)

#: Exceptions de styleforge-core dont ce module connaît la nature — toute
#: autre exception reste non interceptée (voir docstring du module).
_EXCEPTIONS_CONNUES = (
    ErreurLectureQML,
    ExpressionPivotNonEcriteSLD,
    ExpressionPivotNonEcriteMBStyle,
)


def mapper_erreur_connue(exc: Exception) -> HTTPException | None:
    """Retourne une HTTPException(422) structurée si `exc` est une des
    exceptions nommées connues de styleforge-core, None sinon (l'appelant
    doit alors laisser `exc` remonter sans la toucher)."""
    if not isinstance(exc, _EXCEPTIONS_CONNUES):
        return None
    return HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        detail={
            "type_erreur": type(exc).__name__,
            "module_erreur": type(exc).__module__,
            "message": str(exc),
        },
    )


def lever_si_connue(exc: Exception) -> None:
    """À appeler dans un `except Exception as exc:` : lève la HTTPException
    structurée si `exc` est reconnue, sinon relève `exc` telle quelle."""
    http = mapper_erreur_connue(exc)
    if http is not None:
        raise http from exc
    raise exc
