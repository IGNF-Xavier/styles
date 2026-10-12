#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
mesurer_couverture_expressions_generales.py — Niveau 3 de la pyramide de
test, appliqué au NOUVEAU traducteur d'expressions général
(styleforge_core.readers.expressions), PAS à l'ancien StandaloneBackend._filter
du prototype monolithique (déjà mesuré séparément par
mesurer_couverture_expressions.py, à la racine du dépôt — laissé tel quel,
c'est une mesure historique d'un autre composant).

Contrairement à ce script historique (qui devait EXTRAIRE par regex les noms
de fonctions reconnus depuis le code source, faute d'un registre explicite),
le nouveau traducteur MAINTIENT un registre explicite
(REGISTRE_FONCTIONS_VALEUR) : ce script l'importe directement plutôt que de
le re-parser, et le confronte au même oracle
(corpus/expressions/registre_fonctions.json, 387 fonctions QGIS réelles).

Ce script mesure aussi, séparément, les GROUPES de fonctions QGIS qui sont
HORS PÉRIMÈTRE PAR CONCEPTION (pas des lacunes à combler) : GeometryGroup,
Aggregates, Date and Time, Record and Attributes, Maps, Map Layers — cf. la
docstring de styleforge_core/readers/expressions.py. Le chiffre qui compte
n'est pas "387 - couvertes" mais "fonctions du sous-ensemble RÉALISTE
(scalaire, par-entité) - couvertes".
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

RACINE = Path(__file__).parent.parent
CHEMIN_REGISTRE = RACINE / "corpus" / "expressions" / "registre_fonctions.json"

sys.path.insert(0, str(Path(__file__).parent))
from styleforge_core.readers.expressions import REGISTRE_FONCTIONS_VALEUR  # noqa: E402

#: groupes de la nomenclature QGIS qui n'ont structurellement AUCUN
#: équivalent dans le pivot geostyler-style (requêtes géométriques,
#: temporelles, d'agrégation, de couche...) — voir la docstring de
#: styleforge_core/readers/expressions.py. Ne pas les compter comme des
#: lacunes du traducteur : elles ne peuvent pas être couvertes par CE pivot,
#: quel que soit l'effort mis dans ce traducteur.
#:
#: Neuf groupes supplémentaires ajoutés après un second passage (déclenché
#: par le constat "la couverture n'est pas fameuse") : vérifiés en scannant
#: EXHAUSTIVEMENT les $defs du schéma geostyler-style (97 définitions) pour
#: toute fonction dont le nom évoquerait tableaux/fichiers/rasters/formulaire/
#: mise en page/capteur/traitement — aucune trouvée. Ce n'est donc pas une
#: supposition : le pivot ne modélise, à ce jour, QUE des expressions
#: scalaires (nombre/texte/booléen) par-entité, jamais un tableau, un accès
#: fichier, un pixel raster, un contexte de formulaire de saisie, un élément
#: de mise en page, un capteur, ou un paramètre de traitement.
GROUPES_HORS_PERIMETRE_PAR_CONCEPTION = {
    "GeometryGroup", "Aggregates", "Date and Time", "Record and Attributes",
    "Maps", "Map Layers", "Color", "Variables and Functions", "General",
    "Arrays",           # aucun type/valeur "tableau" dans le pivot (vérifié : pas de Farray*)
    "Files and Paths",  # accès au système de fichiers, hors du modèle attribut/valeur
    "Fuzzy Matching",   # similarité entre deux chaînes (levenshtein...), aucune Fxxx correspondante
    "Rasters",          # échantillonnage de pixel raster, hors du modèle par-entité vectoriel
    "Form",             # contexte d'un formulaire de saisie QGIS, pas une valeur d'attribut
    "Layout",           # éléments de mise en page/impression, hors du modèle de style
    "Processing",       # paramètre d'un algorithme de traitement, pas une expression de style
    "Sensors",          # capteur matériel (GPS...), hors du modèle attribut/valeur
    "deprecated",       # $scale (variable d'environnement de rendu), même famille que "General"
}
#: "if" est couvert (traduit en Fcase), mais PAS via REGISTRE_FONCTIONS_VALEUR
#: (cas spécial de construction, voir _traduire_appel_valeur) : à additionner
#: à part pour ne pas fausser la mesure du registre lui-même.
FONCTIONS_COUVERTES_HORS_REGISTRE = {"if"}


def main() -> int:
    if not CHEMIN_REGISTRE.exists():
        print(f"Registre absent : {CHEMIN_REGISTRE}")
        return 2
    registre = json.loads(CHEMIN_REGISTRE.read_text(encoding="utf-8"))
    toutes = {f["nom"]: (f.get("groupes") or ["(sans groupe)"]) for f in registre["fonctions"]}

    couvertes = set(REGISTRE_FONCTIONS_VALEUR) | FONCTIONS_COUVERTES_HORS_REGISTRE
    couvertes_dans_registre = couvertes & toutes.keys()

    par_groupe: dict[str, dict] = {}
    for nom, groupes in toutes.items():
        for g in groupes:
            d = par_groupe.setdefault(g, {"total": 0, "couvertes": [], "hors_perimetre": False})
            d["total"] += 1
            d["hors_perimetre"] = g in GROUPES_HORS_PERIMETRE_PAR_CONCEPTION
            if nom in couvertes_dans_registre:
                d["couvertes"].append(nom)

    total_toutes = len(toutes)
    total_realiste = sum(
        1 for nom, groupes in toutes.items()
        if not all(g in GROUPES_HORS_PERIMETRE_PAR_CONCEPTION for g in groupes)
    )
    total_couvertes = len(couvertes_dans_registre)

    print(f"Registre QGIS complet : {total_toutes} fonctions.")
    print(f"Sous-ensemble RÉALISTE (au moins un groupe hors de la liste "
          f"structurellement hors périmètre) : {total_realiste} fonctions.")
    print(f"Couvertes par le traducteur général (REGISTRE_FONCTIONS_VALEUR + if->Fcase) : "
          f"{total_couvertes} fonctions.")
    print()
    for g in sorted(par_groupe, key=lambda g: (-par_groupe[g]["total"])):
        d = par_groupe[g]
        marqueur = " [hors périmètre par conception]" if d["hors_perimetre"] else ""
        print(f"  {g:28s} {len(d['couvertes']):3d}/{d['total']:3d}{marqueur}")
        if d["couvertes"] and not d["hors_perimetre"]:
            print(f"      -> {sorted(d['couvertes'])}")

    resultat = {
        "total_registre_qgis": total_toutes,
        "total_sous_ensemble_realiste": total_realiste,
        "total_couvertes": total_couvertes,
        "par_groupe": {
            g: {"total": d["total"], "couvertes": sorted(d["couvertes"]),
                "hors_perimetre_par_conception": d["hors_perimetre"]}
            for g, d in par_groupe.items()
        },
    }
    chemin_sortie = RACINE / "corpus" / "rapport_couverture_expressions_generales.json"
    chemin_sortie.write_text(json.dumps(resultat, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nRapport détaillé écrit dans {chemin_sortie}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
