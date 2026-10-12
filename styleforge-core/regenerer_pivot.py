#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
regenerer_pivot.py — Régénère le pivot typé (styleforge_core/pivot/_genere.py)
à partir du schéma JSON publié par geostyler-style.

Pourquoi un GÉNÉRATEUR plutôt qu'un module écrit à la main : le pivot du
script CNIG est un dictionnaire Python libre — pratique pour prototyper,
dangereux pour une bibliothèque publiée (rien n'empêche un lecteur d'écrire
une clé que l'écrivain ne lira jamais). geostyler-style publie déjà, à
chaque version, un schema.json exhaustif de son modèle (généré depuis son
propre TypeScript via `typescript-json-schema`). Plutôt que de retranscrire
à la main ces ~100 définitions — source d'erreurs de transcription et
travail à refaire à chaque nouvelle version de geostyler-style — ce script
transforme CE schéma en modèles pydantic. Le schéma est donc un ENTRANT
versionné du projet, pas une donnée qu'on recopie une fois pour toutes.

Évolutivité : tout ce qui peut changer d'une exécution à l'autre est un
paramètre de ligne de commande, jamais une valeur codée en dur :
  --schema   chemin local OU URL d'un schema.json (défaut : la version
             pinnée sous schemas/)
  --version  version geostyler-style à aller chercher sur npm si --schema
             est omis (défaut : "latest")
  --output   fichier de sortie du module généré

Exemples :
    # Régénérer depuis la version actuellement pinnée (schemas/*.schema.json)
    python3 regenerer_pivot.py

    # Passer à une nouvelle version de geostyler-style publiée sur npm
    python3 regenerer_pivot.py --npm-version 14.0.0

    # Utiliser un schéma local (ex. une branche de travail de geostyler-style)
    python3 regenerer_pivot.py --schema /chemin/vers/schema.json --version 13.1.0-dev
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import urllib.request
from pathlib import Path

RACINE = Path(__file__).parent
DIR_SCHEMAS = RACINE / "schemas"
SORTIE_DEFAUT = RACINE / "styleforge_core" / "pivot" / "_genere.py"

NPM_REGISTRY = "https://registry.npmjs.org/geostyler-style"


def resoudre_version_npm(version: str) -> str:
    """'latest' -> le numéro de version réel publié sur npm à cet instant.
    Une version explicite (ex. '13.0.0') est retournée telle quelle."""
    if version != "latest":
        return version
    with urllib.request.urlopen(f"{NPM_REGISTRY}/latest", timeout=30) as r:
        return json.loads(r.read())["version"]


def telecharger_schema_depuis_npm(version: str) -> Path:
    """Télécharge le paquet npm geostyler-style à la version donnée et en
    extrait schema.json — c'est exactement le fichier que geostyler-style
    publie à chaque version via son script `generate-schema`."""
    version_reelle = resoudre_version_npm(version)
    dest = DIR_SCHEMAS / f"geostyler-style.{version_reelle}.schema.json"
    if dest.exists():
        print(f"Schéma déjà pinné localement : {dest}")
        return dest

    print(f"Téléchargement de geostyler-style {version_reelle} depuis npm...")
    import tempfile
    import tarfile

    with urllib.request.urlopen(f"{NPM_REGISTRY}/{version_reelle}", timeout=30) as r:
        meta = json.loads(r.read())
    tarball_url = meta["dist"]["tarball"]

    with tempfile.TemporaryDirectory() as tmp:
        tarball_path = Path(tmp) / "pkg.tgz"
        urllib.request.urlretrieve(tarball_url, tarball_path)
        with tarfile.open(tarball_path) as tf:
            tf.extractall(tmp)
        schema_source = Path(tmp) / "package" / "schema.json"
        if not schema_source.exists():
            raise FileNotFoundError(
                f"Le paquet npm geostyler-style@{version_reelle} ne contient pas de "
                f"schema.json à l'emplacement attendu — le script `generate-schema` du "
                f"paquet source a peut-être changé de sortie ; vérifier "
                f"package.json#scripts de la version visée.")
        DIR_SCHEMAS.mkdir(parents=True, exist_ok=True)
        shutil.copy(schema_source, dest)

    print(f"Schéma pinné : {dest}")
    return dest


def resoudre_schema(args: argparse.Namespace) -> tuple[Path, str]:
    if args.schema:
        chemin = Path(args.schema)
        if not chemin.exists():
            raise FileNotFoundError(f"Schéma introuvable : {chemin}")
        version = args.version or "personnalisée"
        return chemin, version

    if args.npm_version:
        chemin = telecharger_schema_depuis_npm(args.npm_version)
        return chemin, chemin.stem.split(".", 1)[1].rsplit(".schema", 1)[0]

    # Défaut : la version déjà pinnée sous schemas/ (la plus récente par nom de fichier)
    candidats = sorted(DIR_SCHEMAS.glob("geostyler-style.*.schema.json"))
    if not candidats:
        raise FileNotFoundError(
            "Aucun schéma pinné sous schemas/ et ni --schema ni --npm-version fournis. "
            "Lancer d'abord : python3 regenerer_pivot.py --npm-version latest")
    chemin = candidats[-1]
    version = chemin.stem.split(".", 1)[1].rsplit(".schema", 1)[0]
    return chemin, version


def generer(chemin_schema: Path, sortie: Path) -> None:
    sortie.parent.mkdir(parents=True, exist_ok=True)
    commande = [
        sys.executable, "-m", "datamodel_code_generator",
        "--input", str(chemin_schema),
        "--input-file-type", "jsonschema",
        "--output", str(sortie),
        "--output-model-type", "pydantic_v2.BaseModel",
        "--target-python-version", "3.11",
        "--use-standard-collections",
        # PAS de --use-union-operator : "X | Y | Z | ..." construit un arbre
        # BINAIRE de ForwardRef imbriqués pour les unions à plusieurs dizaines
        # de membres (chaque propriété de symbolizer accepte ~30 types
        # d'expression). typing.Union[X, Y, Z, ...] reste un seul nœud à
        # plat et évite la RecursionError observée à l'import avec l'opérateur.
        "--use-schema-description",
        "--enum-field-as-literal", "all",
        # PAS de --collapse-root-models : le schéma geostyler-style est
        # récursif (une expression peut contenir des expressions ; un
        # Filter peut contenir des Filter). Aplatir les RootModel en unions
        # imbriquées fait exploser la pile d'évaluation de typing._eval_type
        # à l'import (RecursionError constatée en générant contre 13.0.0).
        # Garder chaque RootModel comme une classe à part contourne le problème.
        # extra="forbid" est défini UNE FOIS sur cette classe de base (pivot/_base.py),
        # jamais dans le fichier généré : une clé inconnue doit être une erreur de
        # validation explicite, pas un champ silencieusement ignoré (§ voir _base.py).
        "--base-class", "styleforge_core.pivot._base.PivotBaseModel",
    ]
    print("Commande :", " ".join(commande))
    subprocess.run(commande, check=True)


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--schema", help="Chemin local vers un schema.json (prioritaire sur --npm-version)")
    p.add_argument("--npm-version", help="Version de geostyler-style à télécharger depuis npm "
                                          "('latest' pour la plus récente publiée)")
    p.add_argument("--version", help="Étiquette de version à associer à --schema (facultatif, "
                                      "pour la traçabilité seulement)")
    p.add_argument("--output", default=str(SORTIE_DEFAUT),
                    help=f"Fichier de sortie du module généré (défaut : {SORTIE_DEFAUT})")
    args = p.parse_args()

    chemin_schema, version = resoudre_schema(args)
    print(f"Schéma source : {chemin_schema}  (version : {version})")
    generer(chemin_schema, Path(args.output))

    # Traçabilité : quelle version de quel schéma a produit ce module, et quand.
    marqueur = Path(args.output).parent / "SOURCE.md"
    import datetime
    marqueur.write_text(
        f"# Provenance du pivot généré\n\n"
        f"- Schéma source : `{chemin_schema.name}`\n"
        f"- Version geostyler-style : {version}\n"
        f"- Régénéré le : {datetime.datetime.now().isoformat(timespec='seconds')}\n"
        f"- Commande : `python3 regenerer_pivot.py"
        f"{' --schema ' + str(args.schema) if args.schema else ''}"
        f"{' --npm-version ' + args.npm_version if args.npm_version else ''}`\n\n"
        f"Ne pas éditer _genere.py à la main : toute correction souhaitée doit passer par "
        f"pivot/__init__.py (ré-exports, alias, validateurs additionnels) ou par ce script "
        f"(options de datamodel-codegen), pour rester régénérable.\n",
        encoding="utf-8")
    print(f"Provenance tracée dans {marqueur}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
