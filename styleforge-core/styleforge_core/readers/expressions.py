#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
styleforge_core.readers.expressions — Traducteur GÉNÉRAL (mais délibérément
BORNÉ) d'expressions QGIS vers le vocabulaire pivot geostyler-style, pour
remplacer/étendre les deux traducteurs minimaux qui vivaient jusqu'ici dans
qml.py (traduire_reference_champ_nue : référence de champ nue seule ;
traduire_filtre_qgis_simple : comparaison simple "champ" OP littéral seule).

Portée assumée, et pourquoi elle est bornée (pas une régression, un choix
déjà justifié par le diagnostic niveau 3 du projet, mesurer_couverture_
expressions.py) : QGIS expose 387 fonctions (corpus/expressions/
registre_fonctions.json), dont l'immense majorité (GeometryGroup 153,
Aggregates 23, Date and Time 21, Record and Attributes 17, Maps 16, Map
Layers 3...) n'a AUCUN équivalent dans le vocabulaire pivot geostyler-style,
qui ne modélise que des expressions par-entité sur des attributs scalaires
(nombre/texte/booléen), pas des requêtes géométriques, temporelles ou
d'agrégation. Écrire un interpréteur général des 387 fonctions serait donc
非 seulement hors de portée mais produirait un pivot qui prétend représenter
des choses qu'aucun SLD/MBStyle ne peut exprimer. Ce module couvre :
  - la grammaire structurelle complète (littéraux, référence de champ,
    parenthèses, opérateurs unaires -/+, arithmétique + - * / % ^,
    concaténation ||, comparaisons = <> != < <= > >=, IS [NOT] NULL,
    [NOT] LIKE, [NOT] IN (...), AND / OR / NOT, if(cond,alors,sinon)) ;
  - un registre OUVERT et BORNÉ de fonctions QGIS -> fonctions pivot,
    construit uniquement à partir de correspondances 1:1 non ambiguës
    vérifiées contre le schéma geostyler-style (REGISTRE_FONCTIONS_VALEUR
    ci-dessous), pas une tentative d'exhaustivité.
Tout ce qui sort de cette grammaire (regexp_*, agrégats, fonctions
géométriques, CASE WHEN générale à plusieurs branches, round() avec un
nombre de décimales non nul, replace()/LIKE avec un motif non littéral...)
lève ExpressionQGISNonTraduite AVEC LE FRAGMENT PRÉCIS non reconnu — jamais
une approximation silencieuse (même principe que RAISONS_HORS_PERIMETRE
dans qml.py). IS [NOT] NULL et ILIKE sont bien traduits (voir §formes de
sortie ci-dessous) : un premier essai les avait écartés à tort — corrigé
après vérification plus poussée, pas juste réaffirmé.

Deux FORMES DE SORTIE, choisies par le contexte d'usage, PAS un détail
d'implémentation arbitraire — vérifiées contre le schéma geostyler-style
13.0.0 (Filter.anyOf, FCaseParameter.case) :
  - traduire_filtre(expr) -> une valeur de type Filter. Pour les
    connecteurs booléens usuels (comparaison =/<>/</<=/>/>=, AND/OR/NOT,
    LIKE sensible à la casse), produit la forme TUPLE "raccourcie"
    (["==", gauche, droite], ["&&", f1, f2], ["!", f], ["*=", gauche,
    motif]) : cette forme est explicitement documentée dans le schéma
    (ComparisonFilter, CombinationFilter, NegationFilter) ET c'est déjà la
    forme produite par _renderer_categorized_symbol/_renderer_graduated_
    symbol dans qml.py — la généraliser ici garde tout le pivot interne à
    un seul style plutôt que d'en introduire un second. Pour IN, IS [NOT]
    NULL et ILIKE, PAS de forme tuple adaptée (absente du schéma pour IN ;
    rejetée par le modèle pivot généré pour IS NULL — voir la note plus
    bas ; pas de variante insensible à la casse pour "*=") : ces trois cas
    produisent directement une forme DICT (Fin, FequalTo/FnotEqualTo,
    FstrMatches) — valide en tête de Filter parce qu'un dict de fonction
    booléenne EST lui-même une Filter valide (vérifié dans le paquet
    geostyler-style local, dist/typeguards.js : isFilter() accepte
    isGeoStylerBooleanFunction() directement, pas seulement une liste).
  - traduire_valeur(expr) -> une Expression<T> générale (valeur pilotée par
    une propriété pilotée par expression d'un Symbolizer, argument de
    fonction, branche d'un Fcase...). Utilise TOUJOURS la forme dict Fxxx
    (Fproperty pour un champ, FequalTo/Fall/Fany/Fnot pour les connecteurs
    booléens, FstrMatches pour LIKE/ILIKE...), car c'est la SEULE forme
    valide à ces positions du schéma (FCaseParameter.case en particulier
    référence Expression<boolean>, pas Filter — vérifié, pas supposé).

Note vérifiée sur IS [NOT] NULL (une correction, pas une supposition
initiale) : la forme TUPLE ["==", operande, None] est REJETÉE par le
modèle pydantic généré de ce projet (styleforge_core/pivot/_genere.py,
classe Filter — aucune branche de l'union pour l'opérande d'un
ComparisonFilter tuple n'inclut None, vérifié contre valider_style()). La
forme DICT équivalente {"name": "equalTo", "args": [operande, None]} n'a
PAS cette restriction (FequalTo.args est sans contrainte de type dans le
schéma, "items": [{}, {}]) — donc IS [NOT] NULL se traduit bien, seulement
jamais via la forme tuple pour cette comparaison précise.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Literal


#: CORRECTIF (après vérification plus poussée que le premier essai) : IS
#: [NOT] NULL EST traduisible. Le premier essai utilisait la forme TUPLE
#: raccourcie ["==", operande, None] pour le comparer à None — cette forme
#: précise est bien rejetée par le modèle pydantic généré ici
#: (styleforge_core/pivot/_genere.py, classe Filter : aucune des branches de
#: l'union générée pour l'opérande d'un ComparisonFilter TUPLE n'inclut
#: None ; str/float/bool oui, None non — vérifié contre valider_style()).
#: MAIS la forme DICT équivalente {"name": "equalTo", "args": [operande,
#: None]} (FequalTo) n'a PAS cette restriction : ses deux arguments sont
#: déclarés sans aucune contrainte de type dans le schéma ("args": {"items":
#: [{}, {}]} — un schéma JSON vide {} accepte n'importe quelle valeur, null
#: inclus), et un dict de fonction booléenne EST lui-même un Filter valide
#: en position de tête (vérifié directement contre valider_style(), pas
#: seulement contre le schéma JSON) — donc IS NULL / IS NOT NULL se
#: traduisent bien, juste jamais via la forme tuple pour cette comparaison
#: précise. Voir _traduire_valeur/_traduire_filtre_noeud, cas "est_null".


class ExpressionQGISNonTraduite(Exception):
    """Un fragment de l'expression QGIS dépasse la grammaire bornée que ce
    module reconnaît (voir la docstring du module pour le périmètre exact).
    Toujours levée avec le fragment précis en cause — jamais un message
    générique. qml.py capture cette exception et la relève comme
    FiltreQGISNonTraduit ou ProprieteExpressionNonTraduite selon le
    contexte d'appel (filtre de règle, ou propriété pilotée par expression),
    pour préserver la taxonomie d'exceptions publique déjà établie."""


# --------------------------------------------------------------------------- lexer
_JETON = re.compile(r"""
      (?P<ESPACE>\s+)
    | (?P<CHAINE>'(?:[^']|'')*')
    | (?P<CHAMP>"(?:[^"]|"")*")
    | (?P<NOMBRE>\d+(?:\.\d+)?)
    | (?P<IDENT>[A-Za-z_][A-Za-z0-9_]*)
    | (?P<NE><>|!=)
    | (?P<LE><=)
    | (?P<GE>>=)
    | (?P<CONCAT>\|\|)
    | (?P<PONCT>[()\[\]+\-*/%^,=<>])
""", re.VERBOSE)

_MOTS_CLES = {
    "and", "or", "not", "is", "null", "like", "ilike", "in", "true", "false",
}


@dataclass
class _Jeton:
    type: str
    valeur: str


def _tokeniser(expression: str) -> list[_Jeton]:
    jetons: list[_Jeton] = []
    pos = 0
    while pos < len(expression):
        m = _JETON.match(expression, pos)
        if not m:
            raise ExpressionQGISNonTraduite(
                f"caractère non reconnu par le lexeur d'expression QGIS à la "
                f"position {pos} : {expression[pos:pos + 20]!r}"
            )
        pos = m.end()
        genre = m.lastgroup
        if genre == "ESPACE":
            continue
        texte = m.group()
        if genre == "IDENT" and texte.lower() in _MOTS_CLES:
            jetons.append(_Jeton(texte.lower(), texte))
        else:
            jetons.append(_Jeton(genre, texte))
    jetons.append(_Jeton("FIN", ""))
    return jetons


def _decoder_chaine(brut: str) -> str:
    # 'texte' -> texte ; '' à l'intérieur -> un seul ' littéral (échappement
    # QGIS, comme SQL) — vérifié sur la syntaxe QGIS documentée.
    return brut[1:-1].replace("''", "'")


def _decoder_champ(brut: str) -> str:
    return brut[1:-1].replace('""', '"')


# --------------------------------------------------------------------------- AST
# Nœuds : tuples simples (pas de classes dédiées — cohérent avec le reste du
# lecteur, qui manipule des dicts/tuples bruts plutôt que des classes ad hoc
# pour des structures internes temporaires).
#   ("lit", valeur)
#   ("champ", nom)
#   ("unaire", "-"|"+", noeud)
#   ("arith", "+"|"-"|"*"|"/"|"%"|"^"|"||", gauche, droite)
#   ("cmp", "="|"<>"|"!="|"<"|"<="|">"|">=", gauche, droite)
#   ("et", gauche, droite) / ("ou", gauche, droite) / ("non", noeud)
#   ("est_null", noeud, nie)
#   ("like", noeud, motif_noeud, nie, insensible_casse)
#   ("in", noeud, [valeurs...], nie)
#   ("appel", nom_fonction, [args...])
#   ("index", noeud, indice_entier)   -- noeud[indice] ; voir _postfixe() et
#       _reconnaitre_idiome_prefixe_tableau : l'INDEXATION elle-même n'a PAS
#       d'équivalent générique dans le pivot geostyler-style (aucune notion
#       de valeur "liste"/"tableau" dans son langage d'expression, vérifié
#       par introspection du schéma — voir la docstring du module readers.qml
#       sur les 90+ nœuds d'expression disponibles) : un ("index", ...) qui
#       n'est PAS reconnu comme faisant partie de l'idiome borné ci-dessous
#       lève donc naturellement (fallback de _traduire_valeur), jamais une
#       approximation silencieuse.


class _Analyseur:
    """Descente récursive classique, sans dépendance externe (pyparsing est
    disponible dans l'environnement mais un analyseur à la main reste plus
    simple à faire correspondre EXACTEMENT à la grammaire bornée voulue, et
    évite une dépendance de plus pour ~150 lignes de grammaire)."""

    def __init__(self, jetons: list[_Jeton]):
        self._jetons = jetons
        self._i = 0

    def _courant(self) -> _Jeton:
        return self._jetons[self._i]

    def _consommer(self, type_attendu: str | None = None) -> _Jeton:
        jeton = self._courant()
        if type_attendu is not None and jeton.type != type_attendu:
            raise ExpressionQGISNonTraduite(
                f"jeton {jeton.valeur!r} inattendu (type {jeton.type!r}), "
                f"{type_attendu!r} attendu"
            )
        self._i += 1
        return jeton

    def analyser_complet(self) -> tuple:
        noeud = self._ou()
        if self._courant().type != "FIN":
            raise ExpressionQGISNonTraduite(
                f"jeton(s) résiduel(s) après une expression complète, à "
                f"partir de {self._courant().valeur!r} — expression non "
                f"entièrement reconnue par la grammaire bornée de ce module."
            )
        return noeud

    def _ou(self) -> tuple:
        gauche = self._et()
        while self._courant().type == "or":
            self._consommer("or")
            gauche = ("ou", gauche, self._et())
        return gauche

    def _et(self) -> tuple:
        gauche = self._non()
        while self._courant().type == "and":
            self._consommer("and")
            gauche = ("et", gauche, self._non())
        return gauche

    def _non(self) -> tuple:
        if self._courant().type == "not":
            self._consommer("not")
            return ("non", self._non())
        return self._comparaison()

    _OPS_CMP = {"=": "=", "<>": "<>", "!=": "<>", "<": "<", "<=": "<=", ">": ">", ">=": ">="}

    def _comparaison(self) -> tuple:
        gauche = self._concat()
        t = self._courant()
        if t.type == "PONCT" and t.valeur in ("=", "<", ">"):
            self._consommer()
            return ("cmp", self._OPS_CMP[t.valeur], gauche, self._concat())
        if t.type in ("NE", "LE", "GE"):
            self._consommer()
            return ("cmp", self._OPS_CMP[t.valeur], gauche, self._concat())
        if t.type == "is":
            self._consommer("is")
            nie = False
            if self._courant().type == "not":
                self._consommer("not")
                nie = True
            self._consommer("null")
            return ("est_null", gauche, nie)
        if t.type == "not" and self._jetons[self._i + 1].type in ("like", "ilike", "in"):
            self._consommer("not")
            return self._suite_comparaison_niee(gauche, nie=True)
        if t.type in ("like", "ilike", "in"):
            return self._suite_comparaison_niee(gauche, nie=False)
        return gauche

    def _suite_comparaison_niee(self, gauche: tuple, *, nie: bool) -> tuple:
        t = self._courant()
        if t.type in ("like", "ilike"):
            self._consommer()
            insensible = t.type == "ilike"
            return ("like", gauche, self._concat(), nie, insensible)
        if t.type == "in":
            self._consommer("in")
            self._consommer("PONCT")  # "("
            valeurs = [self._concat()]
            while self._courant().type == "PONCT" and self._courant().valeur == ",":
                self._consommer()
                valeurs.append(self._concat())
            self._consommer("PONCT")  # ")"
            return ("in", gauche, valeurs, nie)
        raise ExpressionQGISNonTraduite(f"NOT inattendu avant {t.valeur!r}")

    def _concat(self) -> tuple:
        gauche = self._additif()
        while self._courant().type == "CONCAT":
            self._consommer()
            gauche = ("arith", "||", gauche, self._additif())
        return gauche

    def _additif(self) -> tuple:
        gauche = self._multiplicatif()
        while self._courant().type == "PONCT" and self._courant().valeur in ("+", "-"):
            op = self._consommer().valeur
            gauche = ("arith", op, gauche, self._multiplicatif())
        return gauche

    def _multiplicatif(self) -> tuple:
        gauche = self._puissance()
        while self._courant().type == "PONCT" and self._courant().valeur in ("*", "/", "%"):
            op = self._consommer().valeur
            gauche = ("arith", op, gauche, self._puissance())
        return gauche

    def _puissance(self) -> tuple:
        gauche = self._unaire()
        if self._courant().type == "PONCT" and self._courant().valeur == "^":
            self._consommer()
            return ("arith", "^", gauche, self._puissance())  # associe à droite
        return gauche

    def _unaire(self) -> tuple:
        if self._courant().type == "PONCT" and self._courant().valeur in ("+", "-"):
            op = self._consommer().valeur
            return ("unaire", op, self._unaire())
        return self._postfixe()

    def _postfixe(self) -> tuple:
        """primaire, suivi de zéro ou plusieurs indexations [n] postfixées
        (ex. string_to_array(champ,'-')[0]) — seule la forme [ENTIER LITTÉRAL]
        est reconnue : QGIS autorise en principe un indice quelconque
        (expression, négatif depuis la fin), mais l'idiome borné que ce
        module traduit (_reconnaitre_idiome_prefixe_tableau) n'a jamais
        besoin de plus, et une forme non littérale ne pourrait de toute
        façon pas être résolue à la traduction (pas d'exécution QGIS ici)."""
        noeud = self._primaire()
        while self._courant().type == "PONCT" and self._courant().valeur == "[":
            self._consommer()  # "["
            t = self._courant()
            if t.type != "NOMBRE" or "." in t.valeur:
                raise ExpressionQGISNonTraduite(
                    f"indexation [...] attend un indice entier littéral, "
                    f"{t.valeur!r} reçu — seule cette forme (par exemple "
                    f"string_to_array(champ,'-')[0]) est reconnue par ce module."
                )
            indice = int(self._consommer().valeur)
            fermante = self._consommer("PONCT")
            if fermante.valeur != "]":
                raise ExpressionQGISNonTraduite(
                    f"indexation [...] non refermée par ']', {fermante.valeur!r} reçu"
                )
            noeud = ("index", noeud, indice)
        return noeud

    def _primaire(self) -> tuple:
        t = self._courant()
        if t.type == "NOMBRE":
            self._consommer()
            valeur = float(t.valeur) if "." in t.valeur else int(t.valeur)
            return ("lit", valeur)
        if t.type == "CHAINE":
            self._consommer()
            return ("lit", _decoder_chaine(t.valeur))
        if t.type == "CHAMP":
            self._consommer()
            return ("champ", _decoder_champ(t.valeur))
        if t.type == "true":
            self._consommer()
            return ("lit", True)
        if t.type == "false":
            self._consommer()
            return ("lit", False)
        if t.type == "null":
            self._consommer()
            return ("lit", None)
        if t.type == "PONCT" and t.valeur == "(":
            self._consommer()
            noeud = self._ou()
            self._consommer("PONCT")  # ")"
            return noeud
        if t.type == "IDENT" and self._jetons[self._i + 1].type == "PONCT" \
                and self._jetons[self._i + 1].valeur == "(":
            nom = self._consommer().valeur
            self._consommer("PONCT")  # "("
            args = []
            if not (self._courant().type == "PONCT" and self._courant().valeur == ")"):
                args.append(self._ou())
                while self._courant().type == "PONCT" and self._courant().valeur == ",":
                    self._consommer()
                    args.append(self._ou())
            self._consommer("PONCT")  # ")"
            return ("appel", nom.lower(), args)
        if t.type == "IDENT":
            # Référence de champ NON quotée : syntaxe QGIS standard tant que
            # le nom ne heurte pas un mot-clé/nom de fonction (documenté —
            # "field names ... may be used without quoting if unambiguous").
            # Même nœud AST ("champ", nom) qu'une référence quotée ("CHAMP"
            # ci-dessus) : aucune distinction de traduction en aval entre les
            # deux formes, seule la syntaxe d'origine diffère.
            self._consommer()
            return ("champ", t.valeur)
        raise ExpressionQGISNonTraduite(
            f"fragment d'expression QGIS non reconnu à partir de {t.valeur!r} "
            f"(type de jeton {t.type!r})"
        )


def _analyser(expression: str) -> tuple:
    return _Analyseur(_tokeniser(expression)).analyser_complet()


# --------------------------------------------------------------------------- registre de fonctions
#: nom de fonction QGIS (en minuscules) -> spécification de traduction vers
#: le vocabulaire pivot geostyler-style. Registre OUVERT (voir
#: enregistrer_fonction_expression) et délibérément PETIT : chaque entrée a
#: été vérifiée une par une contre le nom ET l'arité déclarés dans le schéma
#: geostyler-style (Fxxx correspondantes), PAS une supposition de
#: correspondance par similarité de nom. "if" n'est pas ici : traité à part
#: (voir _traduire_appel), parce qu'il ne se traduit pas par un simple appel
#: à 1 fonction pivot du même nom mais par la construction d'un Fcase.
REGISTRE_FONCTIONS_VALEUR: dict[str, dict[str, Any]] = {
    # --- mathématiques, correspondance 1:1 vérifiée (même arité, même sens) ---
    "abs": {"nom": "abs", "arite": 1},
    "acos": {"nom": "acos", "arite": 1},
    "asin": {"nom": "asin", "arite": 1},
    "atan": {"nom": "atan", "arite": 1},
    "atan2": {"nom": "atan2", "arite": 2},
    "ceil": {"nom": "ceil", "arite": 1},
    "cos": {"nom": "cos", "arite": 1},
    "exp": {"nom": "exp", "arite": 1},
    "floor": {"nom": "floor", "arite": 1},
    "ln": {"nom": "log", "arite": 1},  # QGIS ln = logarithme népérien = Flog (1 arg, vérifié schéma)
    "pi": {"nom": "pi", "arite": 0},
    "sin": {"nom": "sin", "arite": 1},
    "sqrt": {"nom": "sqrt", "arite": 1},
    "tan": {"nom": "tan", "arite": 1},
    "degrees": {"nom": "toDegrees", "arite": 1},
    "radians": {"nom": "toRadians", "arite": 1},
    "max": {"nom": "max", "arite": None},  # Fmax variadic (schéma : pas de min/maxItems)
    "min": {"nom": "min", "arite": None},
    # round : cas spécial (arité 1 OU 2, voir _traduire_appel_valeur) — pas
    # une simple entrée arite=1, donc pas vérifiée ici par le chemin générique.
    "round": {"nom": "round", "arite": None},
    # --- texte, correspondance 1:1 vérifiée ---
    "lower": {"nom": "strToLowerCase", "arite": 1},
    "upper": {"nom": "strToUpperCase", "arite": 1},
    "trim": {"nom": "strTrim", "arite": 1},
    "to_string": {"nom": "toString", "arite": 1},
    "concat": {"nom": "strConcat", "arite": None},  # QGIS concat variadic ; FstrConcat aussi
    # title : "Fully capitalizes the sentence" chez FstrCapitalize, exemple
    # donné par le schéma ("HoW aRe YOU?" -> "How Are You?") — même
    # comportement (majuscule initiale + minuscules ensuite, par mot) que
    # QGIS title() documente ; correspondance de SENS vérifiée via cet
    # exemple, pas seulement de nom.
    "title": {"nom": "strCapitalize", "arite": 1},
    # left, right, replace : cas spéciaux de construction (pas un simple
    # renommage 1 fonction QGIS -> 1 fonction pivot), voir
    # _traduire_appel_valeur pour la justification vérifiée de chacun.
    "left": {"nom": None, "arite": 2},
    "right": {"nom": None, "arite": 2},
    "replace": {"nom": None, "arite": 3},
    # strpos, substr : cas spéciaux vérifiés contre la documentation QGIS
    # officielle EXACTE (docs.qgis.org/3.44, functions_list.html#substr et
    # #strpos — citations exactes relevées avant d'écrire ce code, pas une
    # supposition sur la convention d'indexation), voir _traduire_appel_valeur.
    "strpos": {"nom": None, "arite": 2},
    "substr": {"nom": None, "arite": None},  # 2 ou 3 args
    # length : QGIS "Returns the character count of a string" (groupe
    # String) -> FstrLength, "Returns the string length" — correspondance
    # 1:1 de nom ET de sens, arité 1 des deux côtés.
    "length": {"nom": "strLength", "arite": 1},
    # to_real : QGIS "Converts a string to a real number" -> FtoNumber,
    # "Converts an unknown value into a number" — correspondance vérifiée
    # contre les deux descriptions officielles, arité 1. to_int et
    # to_decimal ont été EXAMINÉS et délibérément PAS ajoutés ici malgré la
    # ressemblance de nom : voir le bloc de commentaires plus bas.
    "to_real": {"nom": "toNumber", "arite": 1},
    # log10, clamp : cas spéciaux de construction (aucune fonction pivot
    # "log10" ni "clamp" nommée ainsi), voir _traduire_appel_valeur pour la
    # formule vérifiée de chacun.
    "log10": {"nom": None, "arite": 1},
    "clamp": {"nom": None, "arite": 3},
    # format_number, scale_linear : ÉCART DE SÉMANTIQUE CONNU ET NON RÉSOLU
    # (troncature QGIS vs arrondi Java DecimalFormat pour l'un, comportement
    # hors-domaine non documenté pour l'autre) — traduits quand même, sur
    # décision explicite de l'utilisateur, mais TOUJOURS accompagnés d'un
    # avertissement signalant précisément le risque à chaque usage (jamais
    # une approximation silencieuse). Voir _traduire_appel_valeur.
    "format_number": {"nom": None, "arite": None},  # 2 args (nombre, décimales)
    "scale_linear": {"nom": None, "arite": 5},
    # log(base, valeur) : QGIS registre officiel (oracle PyQGIS,
    # corpus/expressions/registre_fonctions.json) confirme la signature
    # EXACTE — 2 paramètres nommés ['base', 'value'], dans cet ordre.
    # Aucune fonction pivot "log" à 2 arguments (Flog du pivot est le
    # logarithme népérien à 1 argument, déjà utilisé pour ln/log10) :
    # construit via l'identité log_base(valeur) = ln(valeur) / ln(base),
    # même technique que log10 — voir _traduire_appel_valeur.
    "log": {"nom": None, "arite": 2},
    # coalesce, nullif : groupe Conditionals, constructibles via Fcase
    # (déjà utilisé pour if()) plutôt que par une fonction pivot dédiée —
    # vérifiés contre les exemples OFFICIELS EXACTS de docs.qgis.org/3.44,
    # voir _traduire_appel_valeur.
    "coalesce": {"nom": None, "arite": None},  # variadique, >= 1 argument
    "nullif": {"nom": None, "arite": 2},
}

#: fonctions QGIS des groupes String/Math/Conversions EXAMINÉES mais
#: délibérément NON ajoutées ci-dessus (registre ouvert : à ajouter si l'une
#: de ces incertitudes est un jour levée, pas ici par une supposition) :
#:   lpad/rpad/ltrim/rtrim : FstrTrim ne rogne QUE les deux côtés (pas de
#:     variante asymétrique dans le pivot) ; pas de fonction de remplissage
#:     (pad) du tout côté pivot — non traduisibles sans perte de sens.
#:   ascii/char/format/format_date/wordwrap : aucune fonction pivot de
#:     sémantique équivalente (conversion code↔caractère, formatage libre,
#:     retour à la ligne) — vérifié dans la liste complète des fonctions du
#:     pivot, pas juste absent par inattention.
#:   regexp_match/regexp_replace/regexp_substr : FstrMatches/FstrReplace
#:     acceptent bien un motif au sens Java Pattern, mais le DIALECTE regex
#:     de QGIS (Qt QRegularExpression, proche de PCRE) et celui de Java ne
#:     sont PAS garantis identiques sur tous les cas (groupes nommés,
#:     quantificateurs possessifs, classes POSIX...) — faire passer le
#:     motif QGIS tel quel serait une approximation non vérifiée, pas une
#:     correspondance ; non traduits par prudence.
#:   to_int : EXAMINÉ contre la doc officielle (docs.qgis.org/3.44) — celle-
#:     ci ne précise PAS si un nombre fractionnaire est tronqué, arrondi, ou
#:     rejeté (seul exemple donné : to_int('123') -> 123). FtoNumber
#:     ("convertit en nombre") ne documente pas non plus de troncature :
#:     mapper l'un sur l'autre risquerait de changer silencieusement le
#:     résultat pour une chaîne comme '3.7'. Non ajouté par prudence.
#:   to_decimal : EXAMINÉ et volontairement écarté pour une raison plus
#:     profonde qu'une simple incertitude — ce n'est PAS un convertisseur
#:     texte->nombre comme to_int/to_real (contrairement à ce que son nom
#:     suggère) : la doc officielle confirme que to_decimal() convertit une
#:     coordonnée degrés-minutes-secondes en degrés décimaux
#:     (to_decimal('6°21'16.445') -> 6.3545680555), un domaine (angles/
#:     coordonnées) sans équivalent dans le pivot, même famille que to_dm/
#:     to_dms. Erreur évitée en vérifiant plutôt qu'en supposant par
#:     ressemblance de nom.
#:   scale_exponential/scale_polynomial (mais PAS scale_linear, voir plus
#:     bas) : ont un paramètre "exponent" sans équivalent pivot (Finterpolate
#:     n'a qu'un type "linear") — non ajoutés, structurellement.
#:   rand/randf : Frandom existe mais SANS paramètre de plage (son schéma
#:     n'a même pas de propriété "args" — toujours [0.0, 1.0[), alors que
#:     QGIS rand(min,max)/randf(min,max) prennent une plage arbitraire :
#:     aucune correspondance générale possible sans la reconstruire par
#:     une formule non vérifiée. Non ajoutés.
#:
#: format_number et scale_linear ont un écart de sémantique réel (troncature
#: QGIS vs arrondi Java DecimalFormat pour l'un, comportement hors-domaine
#: non documenté pour l'autre) — CE POINT A ÉTÉ SIGNALÉ EXPLICITEMENT à
#: l'utilisateur avant d'être tranché (jamais en silence), qui a choisi de
#: les traduire quand même, avec un avertissement systématique à l'usage
#: plutôt qu'une exclusion : voir leur entrée dans REGISTRE_FONCTIONS_VALEUR
#: ci-dessus et leur traduction dans _traduire_appel_valeur.


def enregistrer_fonction_expression(nom_qgis: str, nom_geostyler: str, arite: int | None) -> None:
    """Point d'extension : ajoute une correspondance fonction QGIS -> fonction
    pivot, sans modifier la logique de traduction. `arite=None` signifie
    variadique (aucune vérification de nombre d'arguments)."""
    REGISTRE_FONCTIONS_VALEUR[nom_qgis.lower()] = {"nom": nom_geostyler, "arite": arite}


# --------------------------------------------------------------------------- conversion des littéraux de motif LIKE
def _traduire_motif_like(champ_texte: str, avertissements: list[str], contexte: str) -> str:
    """QGIS LIKE utilise les jokers SQL % (0..n caractères) et _ (1
    caractère), avec \\ comme échappement. Le seul opérateur de filtre du
    pivot ayant une sémantique de joker est "*=" (vérifié dans le paquet
    geostyler-style local, examples/filter.ts : ['*=', 'TEST2', '*York*']) —
    dont la convention observée est '*' pour un nombre quelconque de
    caractères (comme le joker OGC PropertyIsLike par défaut). La
    correspondance % -> * est donc directe ; _ -> '.' suit la convention
    OGC PropertyIsLike par défaut (singleChar='.') mais n'a pas pu être
    vérifiée par un rendu réel dans ce projet — signalée explicitement
    plutôt qu'appliquée en silence, même principe que la convention ttf://
    pour FontMarker."""
    if "_" in champ_texte or "\\" in champ_texte:
        avertissements.append(
            f"{contexte} : motif LIKE {champ_texte!r} contient '_' et/ou une "
            f"séquence d'échappement '\\\\' — convertis respectivement en "
            f"'.' (convention OGC PropertyIsLike par défaut) et laissés tels "
            f"quels, PAS VÉRIFIÉS PAR UN RENDU RÉEL dans ce projet."
        )
    return champ_texte.replace("%", "*").replace("_", ".")


def _motif_like_vers_regex(champ_texte: str, avertissements: list[str], contexte: str) -> str:
    """Conversion ALTERNATIVE du motif LIKE, vers une expression régulière
    Java (syntaxe attendue par FstrMatches, "voir Java Pattern javadocs" —
    la même que celle documentée pour FstrReplace). Utilisée pour ILIKE (et
    pour LIKE hors position de filtre), qui n'ont pas d'équivalent via
    l'opérateur "*=" (réservé au Filter, et sensible à la casse) : chaque
    caractère hors joker est échappé (re.escape — le même jeu de
    métacaractères que Java Pattern pour la ponctuation ASCII visée ici),
    puis % -> '.*' et _ -> '.', le tout ancré (^...$) pour un comportement
    de correspondance TOTALE équivalent à LIKE (pas une simple recherche de
    sous-chaîne)."""
    if "\\" in champ_texte:
        avertissements.append(
            f"{contexte} : motif LIKE/ILIKE {champ_texte!r} contient une "
            f"séquence d'échappement '\\\\' — traduite en regex littéralement "
            f"(pas d'échappement LIKE dédié reconnu), PAS VÉRIFIÉE PAR UN "
            f"RENDU RÉEL dans ce projet."
        )
    morceaux = []
    for caractere in champ_texte:
        if caractere == "%":
            morceaux.append(".*")
        elif caractere == "_":
            morceaux.append(".")
        else:
            morceaux.append(re.escape(caractere))
    return "^" + "".join(morceaux) + "$"


# --------------------------------------------------------------------------- traduction : forme "valeur" (dict Fxxx partout)
_ARITH_VERS_FONCTION = {
    "+": "add", "-": "sub", "*": "mul", "/": "div", "%": "modulo", "^": "pow", "||": "strConcat",
}
_CMP_VERS_FONCTION_BOOLEENNE = {
    "=": "equalTo", "<>": "notEqualTo", "<": "lessThan",
    "<=": "lessThanOrEqualTo", ">": "greaterThan", ">=": "greaterThanOrEqualTo",
}
#: opérateur interne ("=", "<>", "<", "<=", ">", ">=") -> chaîne EXACTE de
#: l'enum ComparisonOperator du schéma geostyler-style (vérifié : "==" et
#: "!=", PAS "=" ni "<>" — seuls "<", "<=", ">", ">=" coïncident déjà).
_CMP_VERS_OPERATEUR_FILTRE = {
    "=": "==", "<>": "!=", "<": "<", "<=": "<=", ">": ">", ">=": ">=",
}


def _fonction(nom: str, args: list[Any]) -> dict[str, Any]:
    return {"name": nom, "args": args}


def _litteral_numerique(noeud: tuple) -> float | int | None:
    """('lit', 5) -> 5 ; ('unaire', '-', ('lit', 5)) -> -5 (le nœud brut
    pour un littéral négatif N'EST PAS replié par l'analyseur syntaxique
    lui-même, seulement par _traduire_valeur — les traducteurs spéciaux qui
    doivent connaître le SIGNE d'un argument à la traduction, comme
    substr(), doivent donc dérouler ce cas explicitement plutôt que de
    rejeter à tort tout littéral négatif faute de l'avoir prévu) ; sinon
    None (pas un littéral numérique connu à la traduction)."""
    if noeud[0] == "lit" and isinstance(noeud[1], (int, float)) and not isinstance(noeud[1], bool):
        return noeud[1]
    if noeud[0] == "unaire" and noeud[1] in ("-", "+"):
        interieur = _litteral_numerique(noeud[2])
        if interieur is not None:
            return -interieur if noeud[1] == "-" else interieur
    return None


def _traduire_substr(args: list[tuple], avertissements: list[str], contexte: str) -> Any:
    """QGIS substr(chaine, debut, [longueur]) -> FstrSubstring(chaine,
    debutIndex0, finIndex0) (0-indexé, fin EXCLUSIVE — vérifié dans le
    schéma pivot). Formule vérifiée une par une contre les 6 exemples
    OFFICIELS de la documentation QGIS (docs.qgis.org/3.44/.../
    functions_list.html#substr, citée exactement avant d'écrire ce code) :
      substr('HELLO WORLD',3,5)   -> 'LLO W'   (debut positif, longueur positive)
      substr('HELLO WORLD',6)     -> ' WORLD'  (longueur omise -> jusqu'à la fin)
      substr('HELLO WORLD',-5)    -> 'WORLD'   (debut négatif -> depuis la fin)
      substr('HELLO',3,-1)        -> 'LL'      (longueur négative -> omet depuis la fin)
      substr('HELLO WORLD',-5,2)  -> 'WO'      (debut négatif + longueur positive)
      substr('HELLO WORLD',-5,-1) -> 'WORL'    (debut négatif + longueur négative)
    'debut' (et 'longueur' si fourni) doivent être des littéraux numériques
    connus à la traduction : le SIGNE détermine quelle formule appliquer
    (depuis le début ou depuis la fin), et ce choix ne peut pas être fait
    sans connaître le signe au moment de traduire (pas de branchement
    conditionnel construit ici) — sinon ExpressionQGISNonTraduite plutôt
    qu'une formule appliquée au hasard."""
    if len(args) not in (2, 3):
        raise ExpressionQGISNonTraduite(f"substr() appelée avec {len(args)} argument(s), 2 ou 3 attendu(s)")
    chaine_noeud, debut_noeud = args[0], args[1]
    longueur_noeud = args[2] if len(args) == 3 else None
    debut = _litteral_numerique(debut_noeud)
    if debut is None:
        raise ExpressionQGISNonTraduite(
            "substr() : 'debut' doit être un littéral numérique constant pour ce "
            "traducteur (son signe détermine la formule à appliquer — depuis le "
            "début ou depuis la fin de la chaîne — et ne peut pas être déduit "
            "d'une expression dynamique à la traduction)."
        )
    if debut == 0:
        raise ExpressionQGISNonTraduite(
            "substr() avec debut=0 : comportement non documenté explicitement "
            "par QGIS (les exemples officiels ne couvrent que debut>0 et "
            "debut<0) — non traduit par prudence plutôt que supposé."
        )
    chaine = _traduire_valeur(chaine_noeud, avertissements, contexte)
    longueur_dyn = _fonction("strLength", [chaine])
    debut0 = int(debut) - 1 if debut > 0 else _fonction("add", [longueur_dyn, int(debut)])
    if longueur_noeud is None:
        fin0 = longueur_dyn
    else:
        longueur = _litteral_numerique(longueur_noeud)
        if longueur is None:
            raise ExpressionQGISNonTraduite(
                "substr() : 'longueur' doit être un littéral numérique constant "
                "pour ce traducteur, pour la même raison que 'debut' (son signe "
                "détermine la formule)."
            )
        if longueur >= 0:
            fin0 = _fonction("add", [debut0, int(longueur)]) if isinstance(debut0, dict) else debut0 + int(longueur)
        else:
            fin0 = _fonction("add", [longueur_dyn, int(longueur)])
    return _fonction("strSubstring", [chaine, debut0, fin0])


def _traduire_appel_valeur(nom: str, args: list[tuple], avertissements: list[str], contexte: str) -> Any:
    if nom == "if":
        if len(args) != 3:
            raise ExpressionQGISNonTraduite(
                f"if(...) attend exactement 3 arguments (condition, alors, "
                f"sinon) — {len(args)} reçu(s)"
            )
        condition, alors, sinon = args
        return _fonction("case", [
            _traduire_valeur(sinon, avertissements, contexte),
            {"case": _traduire_valeur(condition, avertissements, contexte),
             "value": _traduire_valeur(alors, avertissements, contexte)},
        ])
    spec = REGISTRE_FONCTIONS_VALEUR.get(nom)
    if spec is None:
        raise ExpressionQGISNonTraduite(
            f"fonction QGIS {nom!r} non enregistrée dans le traducteur "
            f"d'expressions (registre volontairement borné — voir "
            f"enregistrer_fonction_expression pour l'étendre)"
        )
    if nom == "left":
        # QGIS left(chaine, n) = les n premiers caractères. FstrSubstring
        # est 0-indexé, borne de fin EXCLUSIVE (vérifié dans le schéma) :
        # substring(chaine, 0, n) donne EXACTEMENT les n premiers
        # caractères — correspondance exacte, pas une approximation.
        if len(args) != 2:
            raise ExpressionQGISNonTraduite(f"left() appelée avec {len(args)} argument(s), 2 attendu(s)")
        chaine, n = (_traduire_valeur(a, avertissements, contexte) for a in args)
        return _fonction("strSubstring", [chaine, 0, n])
    if nom == "right":
        # QGIS right(chaine, n) = les n derniers caractères. FstrSubstring
        # n'accepte pas d'index négatif (non documenté comme tel) : construit
        # dynamiquement le début à partir de la longueur réelle de la
        # chaîne (strLength(chaine) - n), calculée à l'évaluation, pas
        # supposée ici — correspondance exacte pour toute longueur.
        if len(args) != 2:
            raise ExpressionQGISNonTraduite(f"right() appelée avec {len(args)} argument(s), 2 attendu(s)")
        chaine, n = (_traduire_valeur(a, avertissements, contexte) for a in args)
        longueur = _fonction("strLength", [chaine])
        return _fonction("strSubstring", [chaine, _fonction("sub", [longueur, n]), longueur])
    if nom == "replace":
        # QGIS replace(chaine, avant, apres) remplace TOUTES les occurrences
        # LITTÉRALES de 'avant' (pas une regex) — vérifié dans la doc QGIS.
        # FstrReplace attend un PATRON REGEX (Java Pattern) : n'est fidèle à
        # la sémantique littérale de QGIS que si 'avant' est un littéral
        # texte CONNU à la traduction, pour pouvoir l'échapper (re.escape)
        # avant de le poser comme patron — sinon un caractère spécial regex
        # dans 'avant' changerait le sens en silence. global=true (4e
        # argument de FstrReplace) car QGIS replace() remplace TOUTES les
        # occurrences, jamais seulement la première.
        if len(args) != 3:
            raise ExpressionQGISNonTraduite(f"replace() appelée avec {len(args)} argument(s), 3 attendu(s)")
        chaine_noeud, avant_noeud, apres_noeud = args
        if avant_noeud[0] != "lit" or not isinstance(avant_noeud[1], str):
            raise ExpressionQGISNonTraduite(
                "replace(chaine, avant, apres) : 'avant' doit être un littéral texte "
                "constant pour ce traducteur (FstrReplace attend un patron regex Java, "
                "pas une sous-chaîne littérale comme QGIS replace() — 'avant' doit être "
                "connu à la traduction pour pouvoir l'échapper correctement, sans quoi "
                "un caractère spécial regex changerait le sens en silence)."
            )
        chaine = _traduire_valeur(chaine_noeud, avertissements, contexte)
        apres = _traduire_valeur(apres_noeud, avertissements, contexte)
        motif_echappe = re.escape(avant_noeud[1])
        return _fonction("strReplace", [chaine, motif_echappe, apres, True])
    if nom == "strpos":
        # QGIS strpos(pile, aiguille) : position 1-indexée, 0 si absent
        # (docs.qgis.org/3.44/.../functions_list.html#strpos, cité
        # exactement : "Return the first matching position... or 0 if the
        # substring is not found" ; exemples strpos('HELLO WORLD','WORLD')
        # -> 7, strpos('HELLO WORLD','GOODBYE') -> 0). FstrIndexOf est
        # 0-indexé, -1 si absent. strpos = FstrIndexOf + 1 est correct dans
        # LES DEUX cas (trouvé : décalage d'indexation ; absent : -1+1=0) —
        # vérifié sur les deux exemples officiels avant d'être écrit ici.
        pile, aiguille = (_traduire_valeur(a, avertissements, contexte) for a in args)
        return _fonction("add", [_fonction("strIndexOf", [pile, aiguille]), 1])
    if nom == "substr":
        return _traduire_substr(args, avertissements, contexte)
    if nom == "log10":
        # QGIS log10(x) = logarithme base 10 (docs.qgis.org/3.44 : "Returns
        # the value of the base 10 logarithm of the passed expression",
        # exemples log10(1)->0, log10(100)->2). Aucune fonction pivot
        # "log10" ; construit via l'identité mathématique
        # log10(x) = ln(x) / ln(10), avec Flog (népérien, déjà utilisé pour
        # ln) et Fdiv — le ln(10) est calculé PAR le style au rendu
        # (log(10) imbriqué), pas figé ici comme constante approchée.
        # Vérifié sur les deux exemples officiels : log10(1) = 0/ln(10) = 0 ;
        # log10(100) = ln(100)/ln(10) = 2 exactement (identité mathématique,
        # pas un arrondi).
        if len(args) != 1:
            raise ExpressionQGISNonTraduite(f"log10() appelée avec {len(args)} argument(s), 1 attendu")
        x = _traduire_valeur(args[0], avertissements, contexte)
        return _fonction("div", [_fonction("log", [x]), _fonction("log", [10])])
    if nom == "format_number":
        # QGIS format_number(nombre, decimales) : "Returns a number formatted
        # with the locale separator for thousands... truncates the decimal
        # places to the number of supplied places" (docs.qgis.org/3.44).
        # FnumberFormat attend un PATRON Java DecimalFormat, qui ARRONDIT
        # plutôt que de tronquer — écart signalé explicitement à
        # l'utilisateur, qui a choisi l'approximation avec avertissement
        # plutôt que l'exclusion (voir le rapport). 'decimales' doit être un
        # littéral entier connu à la traduction (il façonne le PATRON, pas
        # une valeur passée à l'évaluation) ; seule la forme à 2 arguments
        # est traduite (la forme à langue/séparateurs explicites de QGIS
        # n'est pas vérifiée).
        if len(args) != 2:
            raise ExpressionQGISNonTraduite(
                "format_number() : seule la forme à 2 arguments (nombre, décimales) est "
                f"traduite par ce traducteur — {len(args)} argument(s) reçu(s)."
            )
        decimales = _litteral_numerique(args[1])
        if decimales is None or decimales < 0 or int(decimales) != decimales:
            raise ExpressionQGISNonTraduite(
                "format_number() : 'decimales' doit être un littéral entier non négatif connu "
                "à la traduction (il façonne le patron Java DecimalFormat, pas une valeur "
                "évaluée au rendu)."
            )
        decimales = int(decimales)
        patron = "#,##0" + ("." + "0" * decimales if decimales > 0 else "")
        avertissements.append(
            f"{contexte} : format_number(...) approximé via FnumberFormat (patron {patron!r}, "
            f"locale fixée à 'en') — DEUX écarts non vérifiés par un rendu réel dans ce projet : "
            f"(1) QGIS TRONQUE les décimales excédentaires, cette fonction pivot (Java "
            f"DecimalFormat) les ARRONDIT (résultat potentiellement différent pour une valeur "
            f"proche d'une frontière de troncature, ex. 1.999 avec 2 décimales) ; (2) le schéma "
            f"pivot exige un 3e argument de locale (contrairement à la description QGIS qui le "
            f"présente comme optionnel) — fixé ici à 'en' (séparateur de milliers ',', décimal "
            f"'.'), qui peut différer du séparateur régional que QGIS aurait utilisé par défaut. "
            f"APPROXIMATION ACCEPTÉE EXPLICITEMENT par l'utilisateur plutôt qu'exclue."
        )
        nombre = _traduire_valeur(args[0], avertissements, contexte)
        return _fonction("numberFormat", [patron, nombre, "en"])
    if nom == "scale_linear":
        # QGIS scale_linear(valeur, domaine_min, domaine_max, plage_min,
        # plage_max) : "Transforms a given value from an input domain to an
        # output range using linear interpolation" (docs.qgis.org/3.44) —
        # construit via Finterpolate("linear", valeur, {stop:domaine_min,
        # value:plage_min}, {stop:domaine_max, value:plage_max}), vérifié
        # sur les 3 exemples officiels EN DOMAINE (scale_linear(5,0,10,0,100)
        # -> 50, etc.). La doc QGIS ne précise PAS le comportement HORS du
        # domaine [domaine_min, domaine_max] (clampé ou extrapolé) ; ce
        # point a été signalé explicitement à l'utilisateur, qui a choisi
        # l'approximation avec avertissement plutôt que l'exclusion.
        if len(args) != 5:
            raise ExpressionQGISNonTraduite(f"scale_linear() appelée avec {len(args)} argument(s), 5 attendus")
        valeur, dmin, dmax, rmin, rmax = (_traduire_valeur(a, avertissements, contexte) for a in args)
        avertissements.append(
            f"{contexte} : scale_linear(...) approximé via Finterpolate (type linear, 2 points) — "
            f"le comportement HORS du domaine [domaine_min, domaine_max] n'est PAS documenté côté "
            f"QGIS (clampé aux bornes ou extrapolé ?) et n'a pas pu être vérifié comme identique à "
            f"celui de Finterpolate, APPROXIMATION ACCEPTÉE EXPLICITEMENT plutôt qu'exclue, PAS "
            f"VÉRIFIÉE PAR UN RENDU RÉEL dans ce projet."
        )
        return _fonction("interpolate", [
            {"name": "linear"}, valeur,
            {"stop": dmin, "value": rmin},
            {"stop": dmax, "value": rmax},
        ])
    if nom == "log":
        # QGIS log(base, valeur) : signature confirmée par l'oracle PyQGIS
        # (registre_fonctions.json : noms_parametres=['base','value']).
        # log_base(valeur) = ln(valeur) / ln(base) — identité mathématique,
        # même construction que log10, vérifiable par exemple exact :
        # log(2,8) = ln(8)/ln(2) = 3 (2^3 = 8).
        if len(args) != 2:
            raise ExpressionQGISNonTraduite(f"log() appelée avec {len(args)} argument(s), 2 attendus (base, valeur)")
        base, valeur = (_traduire_valeur(a, avertissements, contexte) for a in args)
        return _fonction("div", [_fonction("log", [valeur]), _fonction("log", [base])])
    if nom == "coalesce":
        # QGIS coalesce(e1, e2, ..., en) : "Returns the first non-NULL value
        # from the expression list" (docs.qgis.org/3.44), évaluée dans
        # l'ORDRE des arguments. Construit via Fcase : chaque argument sauf
        # le dernier devient une branche {case: notEqualTo(ei, None), value:
        # ei}, le DERNIER argument devient le default — reproduit
        # exactement la sémantique "premier non-NULL, sinon le dernier"
        # (le cas limite où même le dernier serait NULL n'est pas non plus
        # géré par QGIS autrement qu'en renvoyant NULL, donc pas une perte
        # de sens ici). Vérifié contre les exemples officiels exacts :
        # coalesce(NULL,2)->2 ; coalesce(NULL,2,3)->2 ; coalesce(7,NULL,3*2)->7.
        if len(args) < 1:
            raise ExpressionQGISNonTraduite("coalesce() appelée sans argument")
        traduits = [_traduire_valeur(a, avertissements, contexte) for a in args]
        if len(traduits) == 1:
            return traduits[0]
        *branches, defaut = traduits
        return _fonction("case", [defaut] + [
            {"case": _fonction("notEqualTo", [v, None]), "value": v} for v in branches
        ])
    if nom == "nullif":
        # QGIS nullif(valeur1, valeur2) : "Returns a NULL value if value1
        # equals value2; otherwise it returns value1" (docs.qgis.org/3.44).
        # Construit via Fcase : default=valeur1, une branche {case:
        # equalTo(valeur1,valeur2), value: None}. Vérifié contre les
        # exemples officiels exacts : nullif('(none)','(none)')->NULL ;
        # nullif('text','(none)')->'text'.
        if len(args) != 2:
            raise ExpressionQGISNonTraduite(f"nullif() appelée avec {len(args)} argument(s), 2 attendus")
        v1, v2 = (_traduire_valeur(a, avertissements, contexte) for a in args)
        return _fonction("case", [v1, {"case": _fonction("equalTo", [v1, v2]), "value": None}])
    if nom == "clamp":
        # QGIS clamp(minimum, input, maximum) : "Restricts an input value to
        # a specified range" (docs.qgis.org/3.44). Aucune fonction pivot
        # "clamp" ; construit via Fmax(Fmin_val, Fmin(input, Fmax_val)) —
        # Fmin/Fmax du pivot sont déjà enregistrées (variadiques). Formule
        # vérifiée sur les 3 exemples officiels :
        #   clamp(1,5,10)  -> max(1, min(5,10))  = max(1,5)  = 5   (inchangé)
        #   clamp(1,0,10)  -> max(1, min(0,10))  = max(1,0)  = 1   (plancher)
        #   clamp(1,11,10) -> max(1, min(11,10)) = max(1,10) = 10  (plafond)
        if len(args) != 3:
            raise ExpressionQGISNonTraduite(f"clamp() appelée avec {len(args)} argument(s), 3 attendus")
        minimum, entree, maximum = (_traduire_valeur(a, avertissements, contexte) for a in args)
        return _fonction("max", [minimum, _fonction("min", [entree, maximum])])
    if nom == "round":
        # round(valeur) OU round(valeur, decimales) chez QGIS, mais Fround
        # du pivot n'a qu'1 argument (vérifié dans le schéma, pas de
        # paramètre de précision) : seul round(valeur) ou round(valeur, 0)
        # (0 décimale = équivalent exact) se traduit sans perte silencieuse.
        if len(args) not in (1, 2):
            raise ExpressionQGISNonTraduite(
                f"round() appelée avec {len(args)} argument(s), 1 ou 2 attendu(s)"
            )
        if len(args) == 2 and args[1] != ("lit", 0):
            raise ExpressionQGISNonTraduite(
                "round(valeur, decimales) avec decimales != 0 : la fonction "
                "pivot 'round' (Fround) n'a pas de paramètre de précision "
                "(vérifié dans le schéma geostyler-style, 1 seul argument) "
                "— non traduit plutôt qu'arrondi à un nombre de décimales "
                "différent en silence."
            )
        args = args[:1]
    elif spec["arite"] is not None and len(args) != spec["arite"]:
        raise ExpressionQGISNonTraduite(
            f"fonction QGIS {nom}() appelée avec {len(args)} argument(s), "
            f"{spec['arite']} attendu(s) par la correspondance pivot "
            f"{spec['nom']!r} enregistrée — pas de traduction partielle."
        )
    return _fonction(spec["nom"], [_traduire_valeur(a, avertissements, contexte) for a in args])


def _traduire_valeur(noeud: tuple, avertissements: list[str], contexte: str) -> Any:
    genre = noeud[0]
    if genre == "lit":
        return noeud[1]
    if genre == "champ":
        return {"name": "property", "args": [noeud[1]]}
    if genre == "unaire":
        op, operande = noeud[1], noeud[2]
        if operande[0] == "lit" and isinstance(operande[1], (int, float)):
            return -operande[1] if op == "-" else operande[1]
        valeur = _traduire_valeur(operande, avertissements, contexte)
        return valeur if op == "+" else _fonction("mul", [valeur, -1])
    if genre == "arith":
        _, op, gauche, droite = noeud
        return _fonction(_ARITH_VERS_FONCTION[op], [
            _traduire_valeur(gauche, avertissements, contexte),
            _traduire_valeur(droite, avertissements, contexte),
        ])
    if genre == "cmp":
        _, op, gauche, droite = noeud
        return _fonction(_CMP_VERS_FONCTION_BOOLEENNE[op], [
            _traduire_valeur(gauche, avertissements, contexte),
            _traduire_valeur(droite, avertissements, contexte),
        ])
    if genre == "et":
        return _fonction("all", [_traduire_valeur(noeud[1], avertissements, contexte),
                                  _traduire_valeur(noeud[2], avertissements, contexte)])
    if genre == "ou":
        return _fonction("any", [_traduire_valeur(noeud[1], avertissements, contexte),
                                  _traduire_valeur(noeud[2], avertissements, contexte)])
    if genre == "non":
        return _fonction("not", [_traduire_valeur(noeud[1], avertissements, contexte)])
    if genre == "est_null":
        # Forme DICT (pas tuple) — voir la note en tête de module : FequalTo/
        # FnotEqualTo n'imposent aucune contrainte de type à leurs arguments
        # (schéma : "args": {"items": [{}, {}]}), donc acceptent None.
        _, operande, nie = noeud
        fn = "notEqualTo" if nie else "equalTo"
        return _fonction(fn, [_traduire_valeur(operande, avertissements, contexte), None])
    if genre == "in":
        _, operande, valeurs, nie = noeud
        base = _fonction("in", [_traduire_valeur(operande, avertissements, contexte)]
                          + [_traduire_valeur(v, avertissements, contexte) for v in valeurs])
        return _fonction("not", [base]) if nie else base
    if genre == "like":
        # Hors position de Filter, "*=" n'existe pas : LIKE et ILIKE passent
        # tous les deux par FstrMatches (regex Java), avec (?i) en préfixe
        # pour ILIKE seulement — voir _motif_like_vers_regex.
        _, operande, motif_noeud, nie, insensible = noeud
        if motif_noeud[0] != "lit" or not isinstance(motif_noeud[1], str):
            raise ExpressionQGISNonTraduite(
                "LIKE/ILIKE avec un motif qui n'est pas un littéral texte constant "
                "— non traduit (le motif doit être connu pour convertir ses jokers "
                "SQL vers une expression régulière)."
            )
        regex = _motif_like_vers_regex(motif_noeud[1], avertissements, contexte)
        if insensible:
            regex = "(?i)" + regex
        base = _fonction("strMatches", [_traduire_valeur(operande, avertissements, contexte), regex])
        return _fonction("not", [base]) if nie else base
    if genre == "appel":
        return _traduire_appel_valeur(noeud[1], noeud[2], avertissements, contexte)
    raise ExpressionQGISNonTraduite(f"nœud d'expression interne non géré : {noeud!r}")


# --------------------------------------------------------------------------- traduction : forme "filtre" (tuple raccourci en tête, dict Fxxx sinon)
#: idiome REPÉRÉ dans le corpus réel (les 77 filtres SUP, cf. rapport
#: bridge-style/CNIG : "lower(string_to_array(idass,'-')[0]) = 'a1'", c'est-
#: à-dire « le code de servitude commence par a1- »). Ni le pivot ni son
#: langage d'expression ne modélisent un type "tableau"/"liste" (vérifié :
#: aucun nœud F* de ce genre dans le schéma) — cet idiome PRÉCIS est donc
#: reconnu au niveau du FILTRE (pas de la valeur) et reconstruit en LIKE
#: préfixe, exactement la traduction déjà établie pour ce projet (voir
#: styleforge_core/pivot/__init__.py, commentaire sur StandaloneBackend._filter
#: du script CNIG d'origine : "idass LIKE 'a1-%'"). Bornes volontaires,
#: chacune vérifiée nécessaire et suffisante sur le corpus réel plutôt que
#: généralisée par précaution :
#:   - séparateur : un littéral texte QUELCONQUE (pas seulement '-') ;
#:   - indice : UNIQUEMENT 0 (préfixe, avant le premier séparateur) — un
#:     indice différent (milieu/fin de chaîne découpée) n'a pas d'équivalent
#:     LIKE général sans connaître le nombre de parties, non traduit ;
#:   - lower(...) optionnel autour de l'indexation entière (pas autour du
#:     littéral comparé) — bascule vers la forme insensible à la casse déjà
#:     établie pour ILIKE (FstrMatches + préfixe regex (?i)), PAS vers "*="
#:     (qui n'a pas de variante insensible, voir _traduire_motif_like) ;
#:   - comparateur : "=" (positif) ou "<>" (négatif, LIKE nié) uniquement.
def _reconnaitre_idiome_prefixe_tableau(gauche: tuple, droite: tuple) -> tuple | None:
    """Renvoie (champ_noeud, separateur, valeur_litterale, insensible) si
    (gauche, droite) — dans un ordre ou l'autre — correspond exactement à
    l'idiome ci-dessus, sinon None (et la comparaison suit alors son chemin
    de traduction générique habituel, qui échouera honnêtement sur le nœud
    "index" s'il en reste un — voir _traduire_valeur)."""
    for cote_idiome, cote_litteral in ((gauche, droite), (droite, gauche)):
        insensible = False
        noeud = cote_idiome
        if noeud[0] == "appel" and noeud[1] == "lower" and len(noeud[2]) == 1:
            insensible = True
            noeud = noeud[2][0]
        if noeud[0] != "index" or noeud[2] != 0:
            continue
        appel = noeud[1]
        if appel[0] != "appel" or appel[1] != "string_to_array" or len(appel[2]) != 2:
            continue
        champ_noeud, sep_noeud = appel[2]
        if champ_noeud[0] != "champ" or sep_noeud[0] != "lit" or not isinstance(sep_noeud[1], str):
            continue
        if cote_litteral[0] != "lit" or not isinstance(cote_litteral[1], str):
            continue
        return champ_noeud, sep_noeud[1], cote_litteral[1], insensible
    return None


def _traduire_filtre_noeud(noeud: tuple, avertissements: list[str], contexte: str) -> Any:
    genre = noeud[0]
    if genre == "cmp":
        _, op, gauche, droite = noeud
        if op in ("=", "<>"):
            idiome = _reconnaitre_idiome_prefixe_tableau(gauche, droite)
            if idiome is not None:
                champ_noeud, separateur, valeur, insensible = idiome
                avertissements.append(
                    f"{contexte} : idiome QGIS "
                    f"string_to_array(champ,{separateur!r})[0] "
                    f"{'<>' if op == '<>' else '='} {valeur!r} reconnu et traduit en "
                    f"LIKE préfixe ({'insensible' if insensible else 'sensible'} à la "
                    f"casse) 'champ {'NOT ' if op == '<>' else ''}LIKE "
                    f"{valeur}{separateur}%' — équivalent au comportement, pas une "
                    f"reconstruction d'un opérateur tableau générique (le pivot n'en "
                    f"a pas, voir _reconnaitre_idiome_prefixe_tableau)."
                )
                motif_noeud = ("lit", f"{valeur}{separateur}%")
                return _traduire_filtre_noeud(
                    ("like", champ_noeud, motif_noeud, op == "<>", insensible),
                    avertissements, contexte,
                )
        return [_CMP_VERS_OPERATEUR_FILTRE[op],
                _traduire_valeur(gauche, avertissements, contexte),
                _traduire_valeur(droite, avertissements, contexte)]
    if genre == "et":
        return ["&&", _traduire_filtre_noeud(noeud[1], avertissements, contexte),
                _traduire_filtre_noeud(noeud[2], avertissements, contexte)]
    if genre == "ou":
        return ["||", _traduire_filtre_noeud(noeud[1], avertissements, contexte),
                _traduire_filtre_noeud(noeud[2], avertissements, contexte)]
    if genre == "non":
        return ["!", _traduire_filtre_noeud(noeud[1], avertissements, contexte)]
    if genre == "est_null":
        # Forme DICT, pas tuple — la comparaison à None via la forme tuple
        # ["==", operande, None] est rejetée par le modèle pivot généré ici
        # (vérifié contre valider_style()) ; la forme dict FequalTo/
        # FnotEqualTo ne l'est pas (ses arguments sont sans contrainte de
        # type dans le schéma), ET un dict de fonction booléenne est
        # lui-même un Filter valide en tête — voir la note en haut de
        # module et _traduire_valeur, même cas.
        _, operande, nie = noeud
        fn = "notEqualTo" if nie else "equalTo"
        return _fonction(fn, [_traduire_valeur(operande, avertissements, contexte), None])
    if genre == "like":
        _, operande, motif_noeud, nie, insensible = noeud
        if motif_noeud[0] != "lit" or not isinstance(motif_noeud[1], str):
            raise ExpressionQGISNonTraduite(
                "LIKE/ILIKE avec un motif qui n'est pas un littéral texte constant "
                "— non traduit (le motif doit être connu pour convertir ses "
                "jokers SQL vers la convention du pivot)."
            )
        if insensible:
            # "*=" (l'opérateur de Filter à joker) est sensible à la casse,
            # sans variante insensible documentée : ILIKE passe par la
            # forme dict FstrMatches (regex Java, préfixe (?i)) — valide en
            # tête de Filter (dict de fonction booléenne), pas seulement
            # comme opérande d'un tuple.
            regex = "(?i)" + _motif_like_vers_regex(motif_noeud[1], avertissements, contexte)
            base = _fonction("strMatches", [_traduire_valeur(operande, avertissements, contexte), regex])
            return _fonction("not", [base]) if nie else base
        motif = _traduire_motif_like(motif_noeud[1], avertissements, contexte)
        base = ["*=", _traduire_valeur(operande, avertissements, contexte), motif]
        return ["!", base] if nie else base
    if genre == "in":
        _, operande, valeurs, nie = noeud
        base = _fonction("in", [_traduire_valeur(operande, avertissements, contexte)]
                          + [_traduire_valeur(v, avertissements, contexte) for v in valeurs])
        return _fonction("not", [base]) if nie else base
    if genre in ("lit", "champ", "unaire", "arith", "appel"):
        raise ExpressionQGISNonTraduite(
            f"expression de filtre qui ne se réduit pas à un connecteur "
            f"booléen (comparaison/AND/OR/NOT/IS NULL/LIKE/IN) en tête : "
            f"{noeud!r} — un filtre de Rule doit être une expression "
            f"booléenne, pas une valeur numérique/texte."
        )
    raise ExpressionQGISNonTraduite(f"nœud de filtre interne non géré : {noeud!r}")


# --------------------------------------------------------------------------- API publique
def traduire_valeur(
    expression: str, *, avertissements: list[str] | None = None, contexte: str = "",
) -> Any:
    """Traduit une expression QGIS quelconque (dans la grammaire bornée
    décrite en tête de module) vers une Expression<T> pivot en forme dict
    Fxxx. Lève ExpressionQGISNonTraduite si l'expression dépasse cette
    grammaire (fonction non enregistrée, syntaxe non reconnue...)."""
    avertissements = avertissements if avertissements is not None else []
    return _traduire_valeur(_analyser(expression), avertissements, contexte)


def traduire_filtre(
    expression: str, *, avertissements: list[str] | None = None, contexte: str = "",
) -> Any:
    """Traduit une expression QGIS de filtre (dans la grammaire bornée
    décrite en tête de module) vers une valeur de type Filter pivot, en
    tuple raccourci pour les connecteurs booléens (cohérent avec le reste du
    lecteur) et en dict Fxxx pour IN. Lève ExpressionQGISNonTraduite si
    l'expression dépasse cette grammaire, ou ne se réduit pas à une
    expression booléenne."""
    avertissements = avertissements if avertissements is not None else []
    return _traduire_filtre_noeud(_analyser(expression), avertissements, contexte)
