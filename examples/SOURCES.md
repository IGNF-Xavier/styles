# Origine des exemples

Les 17 fichiers `.qml` sous `qml/` proviennent du dépôt officiel du CNIG
(Conseil National de l'Information Géolocalisée) pour la symbolisation des
documents d'urbanisme numérisés diffusés sur le **Géoportail de
l'Urbanisme (GPU)** :

- Dépôt source : https://github.com/cnigfr/DDU-SG5-SYMBOLISATION
- Branche utilisée par le CLI : voir `DEFAULT_REPO` dans
  `cnig_qml2sld_geoserver.py` (`cnigfr/DDU-SG5-SYMBOLISATION`).
- Trois familles de documents, chacune avec ses propres couches :
  **PLU** (Plan Local d'Urbanisme), **PSMV** (Plan de Sauvegarde et de Mise
  en Valeur), **SUP** (Servitudes d'Utilité Publique).

Ces fichiers sont la propriété du CNIG et restent soumis à leurs conditions
de réutilisation propres (voir leur dépôt) — ils sont inclus ici à titre
d'exemples de référence pour ce convertisseur, pas republiés comme un
produit indépendant.

## Correspondance qml -> sld -> mbstyle

Chaque fichier `qml/<famille>/<nom>.qml` correspond exactement à
`sld/<nom>.sld` et `mbstyle/<nom>.json`, produits par :

```bash
python cnig_qml2sld_geoserver.py --local-source <dossier_qml> --backend styleforge \
    --mbstyle --all --out <dossier_sortie> --clean
```

État au moment de la génération de ces exemples : **17/17 fichiers
convertis avec succès en SLD 1.0.0 et en Mapbox GL Style**, 0 échec,
audité conforme GeoServer (PHASE 6 du CLI). Voir `docs/limites.md` pour le
détail des contournements appliqués (approximations signalées,
réécritures de filtre, etc.) et `docs/geoserver.md` pour ce qu'il faut
installer côté GeoServer pour que ces sorties fonctionnent réellement
(sprites, vendor options).

## sprites/

`sprite.png` / `sprite@2x.png` et leurs index JSON sont la feuille de
sprites styleforge produite pour l'ensemble du corpus (pictogrammes et
motifs référencés par les documents MBStyle de `mbstyle/`).
`sprite_glyphes_a_generer.json` liste les glyphes de police (FontMarker,
ex. `ASSIETTE_SUP_S`) qui n'ont PAS pu être rasterisés dans cet
environnement de génération (pas de plate-forme Qt graphique disponible —
voir docs/limites.md) et doivent être régénérés sur un poste où QFont
fonctionne (p. ex. le poste de production, où la police concernée est
installée nativement).
