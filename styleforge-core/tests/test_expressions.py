#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_expressions.py — Vérifie styleforge_core.readers.expressions en
isolation (niveau 1 de la pyramide : pas de fichier QML, juste le
traducteur d'expressions). test_qml.py vérifie séparément qu'il est bien
câblé bout en bout dans le lecteur QML (_appliquer_expressions,
traduire_filtre_qgis_simple) ; ce fichier couvre la grammaire elle-même, y
compris ses limites délibérées (registre de fonctions borné, round()/
substr() avec des arguments non littéraux ou hors formule vérifiée)."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from styleforge_core.readers.expressions import (
    ExpressionQGISNonTraduite,
    traduire_filtre,
    traduire_valeur,
)


def _root(x):
    return getattr(x, "root", x)


def test_comparaisons_simples_forme_tuple():
    for expr, op_attendu, valeur_attendue in [
        ('"a" = 1', "==", 1), ('"a" <> 1', "!=", 1), ('"a" != 1', "!=", 1),
        ('"a" < 1', "<", 1), ('"a" <= 1', "<=", 1), ('"a" > 1', ">", 1), ('"a" >= 1', ">=", 1),
    ]:
        f = traduire_filtre(expr)
        assert f == [op_attendu, {"name": "property", "args": ["a"]}, valeur_attendue], (expr, f)
    print("OK : les 7 opérateurs de comparaison QGIS -> forme tuple Filter avec la bonne "
          "chaîne ComparisonOperator (== et != normalisés depuis =/<>/!=)")


def test_and_or_not_imbriques():
    f = traduire_filtre('"a" = 1 AND "b" = 2 OR NOT "c" = 3')
    # précédence : OR le plus bas -> ["||", (AND...), (NOT...)]
    assert f[0] == "||"
    assert f[1][0] == "&&"
    assert f[1][1] == ["==", {"name": "property", "args": ["a"]}, 1]
    assert f[1][2] == ["==", {"name": "property", "args": ["b"]}, 2]
    assert f[2] == ["!", ["==", {"name": "property", "args": ["c"]}, 3]]
    print("OK : AND/OR/NOT imbriqués -> précédence correcte (OR < AND < NOT < comparaison)")


def test_parentheses_changent_la_precedence():
    sans = traduire_filtre('"a" = 1 OR "b" = 2 AND "c" = 3')
    avec = traduire_filtre('("a" = 1 OR "b" = 2) AND "c" = 3')
    assert sans[0] == "||" and sans[1] == ["==", {"name": "property", "args": ["a"]}, 1]
    assert avec[0] == "&&" and avec[1][0] == "||"
    print("OK : parenthèses explicites -> arbre différent de la précédence implicite")


def test_in_et_not_in():
    f = traduire_filtre('"a" IN (1, 2, 3)')
    assert f == {"name": "in", "args": [{"name": "property", "args": ["a"]}, 1, 2, 3]}
    f_nie = traduire_filtre('"a" NOT IN (1, 2, 3)')
    assert f_nie == {"name": "not", "args": [f]}
    print("OK : IN (...) -> dict Fin ; NOT IN -> Fnot(Fin(...))")


def test_like_conversion_jokers():
    av = []
    f = traduire_filtre('"a" LIKE \'%abc_d%\'', avertissements=av, contexte="ctx")
    assert f == ["*=", {"name": "property", "args": ["a"]}, "*abc.d*"]
    assert any("_" in a for a in av)  # le joker '_' -> '.' est signalé, pas appliqué en silence
    f_nie = traduire_filtre('"a" NOT LIKE \'%abc%\'')
    assert f_nie == ["!", ["*=", {"name": "property", "args": ["a"]}, "*abc*"]]
    print("OK : LIKE -> \"*=\" avec % -> * et _ -> . (signalé) ; NOT LIKE -> négation")


def test_ilike_via_regex_insensible_a_la_casse():
    # "*=" (l'opérateur de Filter à joker) est sensible à la casse, sans
    # variante insensible documentée : ILIKE passe par la forme dict
    # FstrMatches (regex Java, préfixe (?i)) plutôt que d'être rejeté.
    f = traduire_filtre('"a" ILIKE \'%abc%\'')
    assert f == {"name": "strMatches", "args": [{"name": "property", "args": ["a"]}, "(?i)^.*abc.*$"]}
    f_nie = traduire_filtre('"a" NOT ILIKE \'%abc%\'')
    assert f_nie == {"name": "not", "args": [f]}
    print("OK : ILIKE -> dict FstrMatches avec préfixe (?i) ; NOT ILIKE -> Fnot(...)")


def test_like_ilike_en_position_de_valeur():
    # Hors position de Filter, "*=" n'existe pas : LIKE (sensible à la
    # casse) et ILIKE passent tous les deux par FstrMatches — LIKE sans le
    # préfixe (?i), ILIKE avec.
    assert traduire_valeur('"a" LIKE \'%abc%\'') == {
        "name": "strMatches", "args": [{"name": "property", "args": ["a"]}, "^.*abc.*$"]}
    assert traduire_valeur('"a" ILIKE \'%abc%\'') == {
        "name": "strMatches", "args": [{"name": "property", "args": ["a"]}, "(?i)^.*abc.*$"]}
    print("OK : LIKE/ILIKE en position de valeur -> dict FstrMatches (avec/sans (?i))")


def test_filtre_doit_etre_booleen():
    try:
        traduire_filtre('"a" + 1')
    except ExpressionQGISNonTraduite as e:
        assert "booléenne" in str(e)
        print("OK : une expression non booléenne en position de filtre est rejetée")
        return
    raise AssertionError("\"a\" + 1 aurait dû lever ExpressionQGISNonTraduite en position de filtre")


def test_if_vers_fcase():
    v = traduire_valeur("if(\"a\">1,'x','y')")
    assert v == {
        "name": "case",
        "args": [
            "y",
            {"case": {"name": "greaterThan", "args": [{"name": "property", "args": ["a"]}, 1]},
             "value": "x"},
        ],
    }
    print("OK : if(cond,alors,sinon) -> Fcase(défaut=sinon, [{case,value}])")


def test_arithmetique_et_concat():
    assert traduire_valeur("1 + 2 * 3") == {"name": "add", "args": [1, {"name": "mul", "args": [2, 3]}]}
    assert traduire_valeur("(1 + 2) * 3") == {"name": "mul", "args": [{"name": "add", "args": [1, 2]}, 3]}
    assert traduire_valeur('"a" || \'-\' || "b"') == {
        "name": "strConcat",
        "args": [{"name": "strConcat", "args": [{"name": "property", "args": ["a"]}, "-"]},
                 {"name": "property", "args": ["b"]}],
    }
    assert traduire_valeur("2^10") == {"name": "pow", "args": [2, 10]}
    assert traduire_valeur('-"x"') == {"name": "mul", "args": [{"name": "property", "args": ["x"]}, -1]}
    assert traduire_valeur("-5") == -5  # littéral négatif replié, pas Fmul(5,-1)
    print("OK : arithmétique (+ - * / ^), concaténation ||, unaire -/+ (replié sur un littéral)")


def test_fonctions_math_et_texte_enregistrees():
    assert traduire_valeur("lower(\"nom\")") == {"name": "strToLowerCase",
                                                   "args": [{"name": "property", "args": ["nom"]}]}
    assert traduire_valeur("upper('x')") == {"name": "strToUpperCase", "args": ["x"]}
    assert traduire_valeur("abs(-5)") == {"name": "abs", "args": [-5]}
    assert traduire_valeur("sqrt(4)") == {"name": "sqrt", "args": [4]}
    assert traduire_valeur("min(1,2,3)") == {"name": "min", "args": [1, 2, 3]}
    assert traduire_valeur('concat("a","b",\'-\')') == {
        "name": "strConcat",
        "args": [{"name": "property", "args": ["a"]}, {"name": "property", "args": ["b"]}, "-"],
    }
    print("OK : fonctions du registre borné (math + texte) traduites vers leur Fxxx pivot")


def test_round_arite_speciale():
    assert traduire_valeur("round(3.456)") == {"name": "round", "args": [3.456]}
    assert traduire_valeur("round(3.456, 0)") == {"name": "round", "args": [3.456]}
    for expr in ("round(3.456, 2)", "round(3.456, 1, 2)"):
        try:
            traduire_valeur(expr)
        except ExpressionQGISNonTraduite:
            continue
        raise AssertionError(f"{expr!r} aurait dû lever ExpressionQGISNonTraduite")
    print("OK : round(x) et round(x,0) traduits ; round(x,n!=0) et arité invalide rejetés "
          "(Fround du pivot n'a pas de paramètre de précision)")


def test_fonction_non_enregistree_levee_avec_son_nom():
    # coalesce() est enregistrée depuis le 3e passage de couverture (voir
    # test_log_coalesce_nullif_ajoutes_apres_troisieme_passage) — remplacée
    # ici par wordwrap(), toujours hors registre (aucune fonction pivot de
    # retour à la ligne).
    for expr in ("regexp_replace(\"a\",'x','y')", "wordwrap(\"a\", 10)", "$area"):
        try:
            traduire_valeur(expr)
        except ExpressionQGISNonTraduite as e:
            assert any(mot in str(e) for mot in ("regexp_replace", "wordwrap", "non reconnu"))
            continue
        raise AssertionError(f"{expr!r} aurait dû lever ExpressionQGISNonTraduite")
    print("OK : fonction non enregistrée (regexp_replace, wordwrap) ou syntaxe hors grammaire "
          "($area) rejetées avec le fragment en cause")


def test_is_null_traduit_forme_dict_validee_contre_le_pivot():
    # Un premier essai traduisait IS [NOT] NULL vers la forme TUPLE
    # ["==", operande, None] et la rejetait car cette forme précise est
    # refusée par le modèle pivot généré ici. Corrigé : la forme DICT
    # (FequalTo/FnotEqualTo, dont les arguments sont sans contrainte de
    # type dans le schéma) n'a pas cette restriction. Ce test valide bout
    # en bout contre styleforge_core.pivot.valider_style(), pas seulement
    # la forme du dict produit, pour que la régression ne puisse pas
    # revenir sans faire échouer un test.
    from styleforge_core.pivot import valider_style

    for expr, nom_attendu in (('"a" IS NULL', "equalTo"), ('"a" IS NOT NULL', "notEqualTo")):
        f = traduire_filtre(expr)
        assert f == {"name": nom_attendu, "args": [{"name": "property", "args": ["a"]}, None]}
        style = {"name": "t", "rules": [{"name": "r", "filter": f,
                 "symbolizers": [{"kind": "Mark", "wellKnownName": "circle"}]}]}
        valider_style(style)  # lève si le pivot rejette encore cette forme
    print("OK : IS [NOT] NULL -> dict FequalTo/FnotEqualTo(operande, None), validé contre le pivot")


def test_fonctions_texte_supplementaires():
    assert traduire_valeur("title('HoW aRe YOU?')") == {"name": "strCapitalize", "args": ["HoW aRe YOU?"]}
    assert traduire_valeur('left("nom", 3)') == {
        "name": "strSubstring", "args": [{"name": "property", "args": ["nom"]}, 0, 3]}
    v = traduire_valeur('right("nom", 3)')
    assert v["name"] == "strSubstring"
    assert v["args"][1] == {"name": "sub", "args": [{"name": "strLength",
             "args": [{"name": "property", "args": ["nom"]}]}, 3]}
    assert traduire_valeur("replace(\"nom\", '.', '-')") == {
        "name": "strReplace", "args": [{"name": "property", "args": ["nom"]}, "\\.", "-", True]}
    try:
        traduire_valeur('replace("nom", "dynamique", \'-\')')
    except ExpressionQGISNonTraduite as e:
        assert "littéral" in str(e)
    else:
        raise AssertionError("replace() avec un 2e argument non littéral aurait dû lever")
    print("OK : title/left/right/replace (constructions vérifiées, pas de simples renommages)")


def _evaluer(expr_qgis, valeurs_champs=None):
    """Petit évaluateur du sous-ensemble de fonctions pivot que
    strpos/substr construisent, pour vérifier le RÉSULTAT NUMÉRIQUE/TEXTE
    produit contre les exemples OFFICIELS de la documentation QGIS —
    pas seulement la forme du dict intermédiaire."""
    valeurs_champs = valeurs_champs or {}
    v = traduire_valeur(expr_qgis)

    def ev(node):
        if isinstance(node, dict) and "name" in node:
            if node["name"] == "property":
                return valeurs_champs[node["args"][0]]
            if node["name"] == "strLength":
                return len(ev(node["args"][0]))
            if node["name"] == "add":
                return ev(node["args"][0]) + ev(node["args"][1])
            if node["name"] == "strSubstring":
                return ev(node["args"][0])[ev(node["args"][1]):ev(node["args"][2])]
            if node["name"] == "strIndexOf":
                return ev(node["args"][0]).find(ev(node["args"][1]))
            if node["name"] == "div":
                return ev(node["args"][0]) / ev(node["args"][1])
            if node["name"] == "log":
                import math
                return math.log(ev(node["args"][0]))
            if node["name"] == "max":
                return max(ev(a) for a in node["args"])
            if node["name"] == "min":
                return min(ev(a) for a in node["args"])
            if node["name"] == "toNumber":
                return float(ev(node["args"][0]))
            if node["name"] == "equalTo":
                return ev(node["args"][0]) == ev(node["args"][1])
            if node["name"] == "notEqualTo":
                return ev(node["args"][0]) != ev(node["args"][1])
            if node["name"] == "case":
                defaut, *branches = node["args"]
                for branche in branches:
                    if ev(branche["case"]):
                        return ev(branche["value"])
                return ev(defaut)
        return node

    return ev(v)


def test_strpos_verifie_contre_les_exemples_officiels_qgis():
    # docs.qgis.org/3.44/.../functions_list.html#strpos, exemples exacts.
    assert _evaluer("strpos('HELLO WORLD','WORLD')") == 7
    assert _evaluer("strpos('HELLO WORLD','GOODBYE')") == 0
    print("OK : strpos -> Fadd(FstrIndexOf(...), 1), vérifié contre les 2 exemples officiels")


def test_substr_verifie_contre_les_exemples_officiels_qgis():
    # docs.qgis.org/3.44/.../functions_list.html#substr, les 6 exemples
    # exacts de la documentation (début positif/négatif, longueur omise/
    # positive/négative) — pas seulement le cas le plus simple.
    cas = [
        ("substr('HELLO WORLD',3,5)", "LLO W"),
        ("substr('HELLO WORLD',6)", " WORLD"),
        ("substr('HELLO WORLD',-5)", "WORLD"),
        ("substr('HELLO',3,-1)", "LL"),
        ("substr('HELLO WORLD',-5,2)", "WO"),
        ("substr('HELLO WORLD',-5,-1)", "WORL"),
    ]
    for expr, attendu in cas:
        resultat = _evaluer(expr)
        assert resultat == attendu, f"{expr} -> {resultat!r}, attendu {attendu!r}"
    for expr in ("substr('HELLO',0,2)", 'substr("champ_dynamique", "autre_champ")'):
        try:
            traduire_valeur(expr)
        except ExpressionQGISNonTraduite:
            continue
        raise AssertionError(f"{expr!r} aurait dû lever ExpressionQGISNonTraduite")
    print("OK : substr -> FstrSubstring(...), vérifié contre les 6 exemples officiels "
          "(début/longueur positifs, négatifs, omis) ; debut=0 et arguments dynamiques rejetés")


def test_length_to_real_log10_clamp_ajoutes_apres_second_passage():
    """Quatre fonctions ajoutées après le constat que la couverture restait
    trop faible même à 31/129 : length (correspondance 1:1 triviale,
    manquée au premier passage), to_real (via FtoNumber — to_int et
    to_decimal ont été EXAMINÉS et délibérément écartés, voir le registre),
    log10 et clamp (constructions vérifiées contre les exemples OFFICIELS
    exacts de docs.qgis.org/3.44, pas des suppositions par ressemblance de
    formule)."""
    assert traduire_valeur('length("nom")') == {
        "name": "strLength", "args": [{"name": "property", "args": ["nom"]}]}
    assert traduire_valeur('to_real("brut")') == {
        "name": "toNumber", "args": [{"name": "property", "args": ["brut"]}]}
    assert _evaluer("to_real('123.45')") == 123.45

    # log10(1) -> 0, log10(100) -> 2 : les deux exemples officiels exacts.
    assert abs(_evaluer("log10(1)") - 0) < 1e-9
    assert abs(_evaluer("log10(100)") - 2) < 1e-9

    # clamp(minimum, input, maximum) : les 3 exemples officiels exacts.
    assert _evaluer("clamp(1,5,10)") == 5    # inchangé (dans la plage)
    assert _evaluer("clamp(1,0,10)") == 1    # ramené au plancher
    assert _evaluer("clamp(1,11,10)") == 10  # ramené au plafond
    print("OK : length/to_real/log10/clamp, vérifiés contre les exemples officiels QGIS "
          "(to_int et to_decimal examinés et délibérément écartés, voir le registre)")


def test_format_number_et_scale_linear_approximes_avec_avertissement():
    """format_number et scale_linear ont un écart de sémantique RÉEL et
    signalé explicitement (troncature QGIS vs arrondi Java DecimalFormat ;
    comportement hors-domaine non documenté) — traduits quand même sur
    décision explicite de l'utilisateur, mais JAMAIS sans avertissement
    (même principe que le motif LIKE non vérifié par un rendu réel)."""
    avert: list[str] = []
    v = traduire_valeur("format_number(10000000.332, 2)", avertissements=avert)
    assert v == {"name": "numberFormat", "args": ["#,##0.00", 10000000.332, "en"]}
    assert any("tronque" in a.lower() or "arrondi" in a.lower() for a in avert)
    assert any("locale" in a.lower() for a in avert)

    avert2: list[str] = []
    v2 = traduire_valeur("format_number(3, 0)", avertissements=avert2)
    assert v2 == {"name": "numberFormat", "args": ["#,##0", 3, "en"]}

    try:
        traduire_valeur('format_number(3, "champ_dynamique")')
    except ExpressionQGISNonTraduite:
        pass
    else:
        raise AssertionError("format_number() avec des décimales non littérales aurait dû lever")

    # scale_linear(5,0,10,0,100) -> 50 ; scale_linear(0.2,0,1,0,360) -> 72 ;
    # scale_linear(1500,1000,10000,9,20) -> 9.6111111 — exemples officiels.
    avert3: list[str] = []
    v3 = traduire_valeur("scale_linear(5,0,10,0,100)", avertissements=avert3)
    assert v3 == {"name": "interpolate", "args": [
        {"name": "linear"}, 5, {"stop": 0, "value": 0}, {"stop": 10, "value": 100}]}
    assert any("domaine" in a.lower() for a in avert3)

    # Validation directe contre les modèles pydantic générés du pivot (pas
    # seulement la forme du dict) : FnumberFormat exige EXACTEMENT 3
    # arguments (locale non optionnelle, contrairement à la description
    # QGIS) — découvert en vérifiant contre le modèle réel, pas supposé.
    from styleforge_core.pivot._genere import FnumberFormat, Finterpolate
    FnumberFormat.model_validate(v)
    Finterpolate.model_validate(v3)
    print("OK : format_number/scale_linear approximés (Java DecimalFormat/Finterpolate), "
          "validés contre les modèles pivot réels, avec avertissement explicite systématique "
          "— décision de l'utilisateur, jamais silencieux")


def test_log_coalesce_nullif_ajoutes_apres_troisieme_passage():
    """Troisième passage de couverture, déclenché par un troisième retour
    ('37/70 c'est pas encore top') : trois fonctions manquées jusqu'ici
    parce qu'elles ressemblaient à des cas déjà tranchés (log10, if) sans
    l'être — vérifiées contre l'oracle PyQGIS (registre_fonctions.json,
    signature exacte de log) et les exemples OFFICIELS EXACTS de
    docs.qgis.org/3.44 pour coalesce/nullif."""
    # log(base, valeur) = ln(valeur)/ln(base) ; log(2,8) = 3 (2**3 = 8).
    assert abs(_evaluer("log(2,8)") - 3) < 1e-9
    assert abs(_evaluer("log(10,1000)") - 3) < 1e-9

    # coalesce : les 3 exemples officiels numériques exacts (le 4e exemple
    # officiel mélange champs et littéral 'ERROR', non vérifiable ici sans
    # champ réel, couvert par la structure Fcase elle-même).
    assert _evaluer("coalesce(NULL, 2)") == 2
    assert _evaluer("coalesce(NULL, 2, 3)") == 2
    assert _evaluer("coalesce(7, NULL, 3*2)") == 7

    # nullif : les 2 premiers exemples officiels exacts (littéraux).
    assert _evaluer("nullif('(none)', '(none)')") is None
    assert _evaluer("nullif('text', '(none)')") == "text"

    from styleforge_core.pivot._genere import Fcase
    Fcase.model_validate(traduire_valeur("coalesce(7, NULL, 3*2)"))
    Fcase.model_validate(traduire_valeur("nullif('text', '(none)')"))
    print("OK : log(base,valeur)/coalesce/nullif, vérifiés contre l'oracle PyQGIS et les "
          "exemples officiels QGIS exacts, validés contre le modèle pivot Fcase réel")


def test_champ_avec_guillemet_echappe():
    assert traduire_valeur('"champ ""spécial"""') == {"name": "property", "args": ['champ "spécial"']}
    assert traduire_valeur("'texte avec '' quote'") == "texte avec ' quote"
    print("OK : échappement QGIS des guillemets doublés (\"\" dans un champ, '' dans une chaîne)")


def test_reference_de_champ_nue_sans_guillemets():
    # Syntaxe QGIS standard (nom de champ non ambigu, sans guillemets) — pas
    # seulement une convention du corpus CNIG : "idass" doit être reconnu au
    # même titre que "idass" avec guillemets ('"idass"').
    assert traduire_valeur("idass") == {"name": "property", "args": ["idass"]}
    assert traduire_filtre("idass = 'a1'") == ["==", {"name": "property", "args": ["idass"]}, "a1"]
    print("OK : référence de champ nue sans guillemets (idass) reconnue, comme \"idass\"")


def test_indexation_postfixe_tableau():
    # Nouveau nœud AST ("index", ...) : indexation postfixe [N] sur un appel
    # de fonction — seul consommateur actuel : l'idiome string_to_array(...)
    # [0] (cf. test_idiome_string_to_array_prefixe ci-dessous). Hors de cet
    # idiome précis, un index non nul doit échouer honnêtement (le pivot n'a
    # pas de type tableau/liste), pas être silencieusement ignoré.
    from styleforge_core.readers.expressions import _analyser
    assert _analyser("string_to_array(idass,'-')[0]") == (
        "index", ("appel", "string_to_array", [("champ", "idass"), ("lit", "-")]), 0)
    try:
        traduire_valeur("string_to_array(idass,'-')[1]")
    except ExpressionQGISNonTraduite as e:
        assert "index" in str(e)
        print("OK : indexation postfixe [N] parsée (AST 'index') ; un index hors de "
              "l'idiome string_to_array(...)[0] échoue honnêtement, pas silencieusement -",
              str(e)[:80])
        return
    raise AssertionError("string_to_array(...)[1] (hors idiome) aurait dû lever ExpressionQGISNonTraduite")


def test_indexation_index_non_entier_ou_non_fermee_levee():
    for expr in ("string_to_array(idass,'-')[x]", "string_to_array(idass,'-')[0"):
        try:
            traduire_valeur(expr)
        except ExpressionQGISNonTraduite:
            continue
        raise AssertionError(f"{expr!r} aurait dû lever ExpressionQGISNonTraduite")
    print("OK : indice non littéral entier, ou crochet non fermé -> ExpressionQGISNonTraduite")


def test_idiome_string_to_array_prefixe():
    # Idiome QGIS observé tel quel sur le corpus réel CNIG (famille SUP,
    # ASSIETTE_SUP_S.qml/sup_ass.qml, 77 occurrences) : filtre par préfixe
    # via string_to_array(champ, séparateur)[0]. Le pivot n'a pas de type
    # tableau : reconnu et délégué à la machinerie LIKE/ILIKE déjà établie
    # (pas une nouvelle traduction inventée), avec avertissement explicite
    # documentant ce qui a été reconnu.
    av = []
    f = traduire_filtre("lower(string_to_array(idass,'-')[0]) = 'a1'", avertissements=av, contexte="ctx")
    assert f == {"name": "strMatches",
                 "args": [{"name": "property", "args": ["idass"]}, "(?i)^a1\\-.*$"]}
    assert any("string_to_array" in a and "idiome" in a for a in av)

    # Sensible à la casse (sans lower()) : "*=" comme un LIKE normal.
    f_cs = traduire_filtre("string_to_array(idass,'-')[0] = 'a1'")
    assert f_cs == ["*=", {"name": "property", "args": ["idass"]}, "a1-*"]

    # <> : négation (ILIKE nié -> Fnot(FstrMatches...)).
    f_ne = traduire_filtre("lower(string_to_array(idass,'-')[0]) <> 'a1'")
    assert f_ne == {"name": "not", "args": [f]}

    # Espace parasite autour du séparateur, et champ entre guillemets : la
    # reconnaissance de l'idiome ne dépend pas de ces détails de formatage
    # (variantes observées telles quelles sur le corpus réel).
    f_espace = traduire_filtre("lower(string_to_array(idass ,'-')[0]) = 'a1'")
    assert f_espace == f
    f_guillemets = traduire_filtre('lower(string_to_array( "idass",\'-\')[0]) = \'a1\'')
    assert f_guillemets == f

    print("OK : idiome string_to_array(champ,'-')[0] {=|<>} 'val' -> délégué à LIKE/ILIKE "
          "préfixe, avec avertissement documentant la reconnaissance")


if __name__ == "__main__":
    test_comparaisons_simples_forme_tuple()
    test_and_or_not_imbriques()
    test_parentheses_changent_la_precedence()
    test_in_et_not_in()
    test_like_conversion_jokers()
    test_ilike_via_regex_insensible_a_la_casse()
    test_like_ilike_en_position_de_valeur()
    test_filtre_doit_etre_booleen()
    test_if_vers_fcase()
    test_arithmetique_et_concat()
    test_fonctions_math_et_texte_enregistrees()
    test_fonctions_texte_supplementaires()
    test_strpos_verifie_contre_les_exemples_officiels_qgis()
    test_substr_verifie_contre_les_exemples_officiels_qgis()
    test_round_arite_speciale()
    test_fonction_non_enregistree_levee_avec_son_nom()
    test_is_null_traduit_forme_dict_validee_contre_le_pivot()
    test_length_to_real_log10_clamp_ajoutes_apres_second_passage()
    test_format_number_et_scale_linear_approximes_avec_avertissement()
    test_log_coalesce_nullif_ajoutes_apres_troisieme_passage()
    test_champ_avec_guillemet_echappe()
    test_reference_de_champ_nue_sans_guillemets()
    test_indexation_postfixe_tableau()
    test_indexation_index_non_entier_ou_non_fermee_levee()
    test_idiome_string_to_array_prefixe()
    print("\nTous les tests du traducteur d'expressions sont passés.")
