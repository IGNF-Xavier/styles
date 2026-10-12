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
python cnig_qml2sld_geoserver.py --local-source <dossier_source> --backend styleforge \
    --mbstyle --all --out <dossier_sortie> --clean
```

**Attention à `<dossier_source>`** : il doit pointer vers une copie du
dépôt CNIG qui conserve les fichiers `.svg` à côté des `.qml` (un clone
git de la branche `SYMBOLISATION`, ou le dossier `.cache_cnig` déjà
rempli par une exécution précédente en mode `github`) — **pas** le
dossier `qml/` de ce répertoire d'exemples, qui ne contient QUE les 17
`.qml` extraits, sans les pictogrammes qui les accompagnent dans le
dépôt source. Lancer la commande sur `qml/` seul reste possible et
produit bien des SLD/MBStyle valides, mais avec beaucoup moins de
pictogrammes résolus (environ 127 contre 873 ici) — le compteur
"Pictogrammes SVG déployés" de `rapport_conversion.md` en dépend
directement, ce n'est pas une variation aléatoire.

État au moment de la génération de ces exemples : **17/17 fichiers
convertis avec succès en SLD 1.0.0 et en Mapbox GL Style**, 0 échec,
audité conforme GeoServer (PHASE 6 du CLI). Voir `docs/limites.md` pour le
détail des contournements appliqués (approximations signalées,
réécritures de filtre, etc.) et `docs/geoserver.md` pour ce qu'il faut
installer côté GeoServer pour que ces sorties fonctionnent réellement
(sprites, vendor options).

## rapport_conversion.md

Le rapport de synthèse produit par CETTE exécution exacte (celle qui a
généré les fichiers de `sld/` et `mbstyle/` ci-contre) : décompte par
correctif appliqué en phase 4 (réécritures d'`onlineResource`, hachures
réparées, `VendorOption` injectées, etc.), résultat de l'audit PHASE 6
("Conforme — aucun défaut détecté"), et le détail exhaustif,
**fichier par fichier**, de chaque avertissement émis pendant la
conversion — jamais une approximation silencieuse, toujours tracée.
C'est la meilleure illustration concrète de ce que `docs/limites.md`
décrit en théorie : chaque ligne y renvoie au fichier QML, au
symbolizer et à la propriété concernés.

Le rapport existe aussi en JSON (`rapport_conversion.json`, même contenu,
exploitable par script) — non inclus ici pour limiter la taille du dépôt
(environ 1,5 Mo sur ce corpus) ; régénérez-le en relançant la commande
ci-dessus, il est produit automatiquement à côté du dossier de sortie.

## NOTICE_DEPLOIEMENT.txt

Notice générée par le CLI à chaque exécution : comment déployer le
dossier `styles/` produit dans le `GEOSERVER_DATA_DIR`, recharger la
configuration GeoServer, associer un style à une couche, vérifier le
rendu, et les points de vigilance connus (encodage UTF-8 sans BOM,
espacement des hachures, glyphes de police non fournis par GeoServer par
défaut, unités QGIS/SLD). Un complément pratique à `docs/geoserver.md`,
du point de vue de l'opération de déploiement plutôt que de
l'installation du serveur.

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
