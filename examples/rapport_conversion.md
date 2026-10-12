# Rapport de conversion QML CNIG -> SLD GeoServer

- Styles convertis : **17/17**
- Échecs : **0**
- Conversions avec avertissement : **17**
- Pictogrammes SVG déployés : **873**

## Correctifs appliqués en phase 4

| Correctif | Occurrences |
|---|---:|
| onlineresource reecrits | 357 |
| hachures reparees | 260 |
| vendoroptions injectees | 222 |
| elements reordonnes | 214 |
| propertyislike matchcase geoserver | 77 |
| propertyislike completes | 77 |
| wellknownname formes qgis corrigees | 44 |
| tirets personnalises reinjectes | 38 |
| wellknownname inconnus remplaces | 13 |

## Audit de conformité GeoServer

**Conforme** — aucun défaut détecté sur les styles produits.

### Extensions GeoServer assumées

Comprises par GeoServer, nécessaires au rendu, mais refusées par un validateur XSD 1.0 strict.

| Extension | Occurrences |
|---|---:|
| matchCase sur PropertyIsLike (extension GeoServer) | 77 |

## Avertissements

- `plu_inf_l.qml`
  - .cache_cnig/PLU/QGIS/QML/plu_inf_l.qml [SimpleLine].width : unité QML 'Point' convertie en pixels via dpi=90.0 (1.5Point -> 1.875px) — approximation dépendante d'une résolution supposée, pas une conversion exacte.
  - .cache_cnig/PLU/QGIS/QML/plu_inf_l.qml [SimpleLine].dasharray : unité QML 'Point' convertie en pixels via dpi=90.0 (6.0Point -> 7.500px) — approximation dépendante d'une résolution supposée, pas une conversion exacte.
  - .cache_cnig/PLU/QGIS/QML/plu_inf_l.qml [SimpleLine].dasharray : unité QML 'Point' convertie en pixels via dpi=90.0 (10.0Point -> 12.500px) — approximation dépendante d'une résolution supposée, pas une conversion exacte.
  - .cache_cnig/PLU/QGIS/QML/plu_inf_l.qml [SimpleLine].dashOffset : unité QML 'MM' convertie en pixels via dpi=90.0 (0.0MM -> 0.000px) — approximation dépendante d'une résolution supposée, pas une conversion exacte.
  - .cache_cnig/PLU/QGIS/QML/plu_inf_l.qml [MarkerLine] : outline_color/outline_width non représentables par IconSymbolizer (pas de champ de trait séparé) — non traduits.
  - .cache_cnig/PLU/QGIS/QML/plu_inf_l.qml [MarkerLine] [SvgMarker].size : unité QML 'Point' convertie en pixels via dpi=90.0 (6.60156Point -> 8.252px) — approximation dépendante d'une résolution supposée, pas une conversion exacte.
- `plu_inf_p.qml`
  - .cache_cnig/PLU/QGIS/QML/plu_inf_p.qml : outline_color/outline_width non représentables par IconSymbolizer (pas de champ de trait séparé) — non traduits.
  - .cache_cnig/PLU/QGIS/QML/plu_inf_p.qml [SvgMarker].size : unité QML 'Point' convertie en pixels via dpi=90.0 (6.60156Point -> 8.252px) — approximation dépendante d'une résolution supposée, pas une conversion exacte.
  - .cache_cnig/PLU/QGIS/QML/plu_inf_p.qml : outline_color/outline_width non représentables par IconSymbolizer (pas de champ de trait séparé) — non traduits.
  - .cache_cnig/PLU/QGIS/QML/plu_inf_p.qml [SvgMarker].size : unité QML 'Point' convertie en pixels via dpi=90.0 (10.1792Point -> 12.724px) — approximation dépendante d'une résolution supposée, pas une conversion exacte.
  - .cache_cnig/PLU/QGIS/QML/plu_inf_p.qml [SimpleMarker].radius : unité QML 'Point' convertie en pixels via dpi=90.0 (3.0Point -> 3.750px) — approximation dépendante d'une résolution supposée, pas une conversion exacte.
  - .cache_cnig/PLU/QGIS/QML/plu_inf_p.qml [SimpleMarker].strokeWidth : unité QML 'Point' convertie en pixels via dpi=90.0 (0.0Point -> 0.000px) — approximation dépendante d'une résolution supposée, pas une conversion exacte.
- `plu_inf_s.qml`
  - .cache_cnig/PLU/QGIS/QML/plu_inf_s.qml [SimpleFill].outlineWidth : unité QML 'MM' convertie en pixels via dpi=90.0 (0.0MM -> 0.000px) — approximation dépendante d'une résolution supposée, pas une conversion exacte.
  - .cache_cnig/PLU/QGIS/QML/plu_inf_s.qml [SimpleLine].width : unité QML 'Point' convertie en pixels via dpi=90.0 (1.0Point -> 1.250px) — approximation dépendante d'une résolution supposée, pas une conversion exacte.
  - .cache_cnig/PLU/QGIS/QML/plu_inf_s.qml [MarkerLine] : outline_color/outline_width non représentables par IconSymbolizer (pas de champ de trait séparé) — non traduits.
  - .cache_cnig/PLU/QGIS/QML/plu_inf_s.qml [MarkerLine] [SvgMarker].size : unité QML 'Point' convertie en pixels via dpi=90.0 (4.83863Point -> 6.048px) — approximation dépendante d'une résolution supposée, pas une conversion exacte.
  - .cache_cnig/PLU/QGIS/QML/plu_inf_s.qml [MarkerLine] [SvgMarker].offset : unité QML 'Point' convertie en pixels via dpi=90.0 (-4.9e-16Point -> -0.000px) — approximation dépendante d'une résolution supposée, pas une conversion exacte.
  - .cache_cnig/PLU/QGIS/QML/plu_inf_s.qml [MarkerLine] [SvgMarker].offset : unité QML 'Point' convertie en pixels via dpi=90.0 (-4.0Point -> -5.000px) — approximation dépendante d'une résolution supposée, pas une conversion exacte.
- `plu_psc_l.qml`
  - .cache_cnig/PLU/QGIS/QML/plu_psc_l.qml [MarkerLine] [SimpleMarker].radius : unité QML 'Point' convertie en pixels via dpi=90.0 (2.5Point -> 3.125px) — approximation dépendante d'une résolution supposée, pas une conversion exacte.
  - .cache_cnig/PLU/QGIS/QML/plu_psc_l.qml [MarkerLine] [SimpleMarker].strokeWidth : unité QML 'MM' convertie en pixels via dpi=90.0 (0.0MM -> 0.000px) — approximation dépendante d'une résolution supposée, pas une conversion exacte.
  - .cache_cnig/PLU/QGIS/QML/plu_psc_l.qml [MarkerLine].spacing : unité QML 'Point' convertie en pixels via dpi=90.0 (11.0Point -> 13.750px) — approximation dépendante d'une résolution supposée, pas une conversion exacte.
  - .cache_cnig/PLU/QGIS/QML/plu_psc_l.qml [MarkerLine] [SimpleMarker].radius : unité QML 'Point' convertie en pixels via dpi=90.0 (2.5Point -> 3.125px) — approximation dépendante d'une résolution supposée, pas une conversion exacte.
  - .cache_cnig/PLU/QGIS/QML/plu_psc_l.qml [MarkerLine] [SimpleMarker].strokeWidth : unité QML 'MM' convertie en pixels via dpi=90.0 (0.0MM -> 0.000px) — approximation dépendante d'une résolution supposée, pas une conversion exacte.
  - .cache_cnig/PLU/QGIS/QML/plu_psc_l.qml [MarkerLine].spacing : unité QML 'Point' convertie en pixels via dpi=90.0 (11.0Point -> 13.750px) — approximation dépendante d'une résolution supposée, pas une conversion exacte.
- `plu_psc_p.qml`
  - .cache_cnig/PLU/QGIS/QML/plu_psc_p.qml [SimpleMarker].radius : unité QML 'Point' convertie en pixels via dpi=90.0 (3.5Point -> 4.375px) — approximation dépendante d'une résolution supposée, pas une conversion exacte.
  - .cache_cnig/PLU/QGIS/QML/plu_psc_p.qml [SimpleMarker].strokeWidth : unité QML 'MM' convertie en pixels via dpi=90.0 (0.0MM -> 0.000px) — approximation dépendante d'une résolution supposée, pas une conversion exacte.
  - .cache_cnig/PLU/QGIS/QML/plu_psc_p.qml [SimpleMarker].radius : unité QML 'Point' convertie en pixels via dpi=90.0 (3.5Point -> 4.375px) — approximation dépendante d'une résolution supposée, pas une conversion exacte.
  - .cache_cnig/PLU/QGIS/QML/plu_psc_p.qml [SimpleMarker].strokeWidth : unité QML 'MM' convertie en pixels via dpi=90.0 (0.0MM -> 0.000px) — approximation dépendante d'une résolution supposée, pas une conversion exacte.
  - .cache_cnig/PLU/QGIS/QML/plu_psc_p.qml [SimpleMarker].radius : unité QML 'Point' convertie en pixels via dpi=90.0 (5.2201Point -> 6.525px) — approximation dépendante d'une résolution supposée, pas une conversion exacte.
  - .cache_cnig/PLU/QGIS/QML/plu_psc_p.qml [SimpleMarker].strokeWidth : unité QML 'Point' convertie en pixels via dpi=90.0 (1.5Point -> 1.875px) — approximation dépendante d'une résolution supposée, pas une conversion exacte.
- `plu_psc_s.qml`
  - .cache_cnig/PLU/QGIS/QML/plu_psc_s.qml [PointPatternFill] [SimpleMarker].radius : unité QML 'Point' convertie en pixels via dpi=90.0 (7.0Point -> 8.750px) — approximation dépendante d'une résolution supposée, pas une conversion exacte.
  - .cache_cnig/PLU/QGIS/QML/plu_psc_s.qml [PointPatternFill] [SimpleMarker].strokeWidth : unité QML 'Point' convertie en pixels via dpi=90.0 (0.25Point -> 0.312px) — approximation dépendante d'une résolution supposée, pas une conversion exacte.
  - .cache_cnig/PLU/QGIS/QML/plu_psc_s.qml [PointPatternFill] : distance_x/distance_y approximés via graphicFillPadding (marge autour du motif répété) — pas une correspondance exacte à l'espacement QGIS, dépend du moteur de rendu SLD/MBStyle final (non vérifié sur un rendu réel).
  - .cache_cnig/PLU/QGIS/QML/plu_psc_s.qml [PointPatternFill] [SimpleMarker].radius : unité QML 'Point' convertie en pixels via dpi=90.0 (10.0Point -> 12.500px) — approximation dépendante d'une résolution supposée, pas une conversion exacte.
  - .cache_cnig/PLU/QGIS/QML/plu_psc_s.qml [PointPatternFill] [SimpleMarker].strokeWidth : unité QML 'Point' convertie en pixels via dpi=90.0 (0.25Point -> 0.312px) — approximation dépendante d'une résolution supposée, pas une conversion exacte.
  - .cache_cnig/PLU/QGIS/QML/plu_psc_s.qml [PointPatternFill] : distance_x/distance_y approximés via graphicFillPadding (marge autour du motif répété) — pas une correspondance exacte à l'espacement QGIS, dépend du moteur de rendu SLD/MBStyle final (non vérifié sur un rendu réel).
- `plu_zone_urba_ge.qml`
  - .cache_cnig/PLU/QGIS/QML/plu_zone_urba_ge.qml [SimpleLine].width : unité QML 'Point' convertie en pixels via dpi=90.0 (7.0Point -> 8.750px) — approximation dépendante d'une résolution supposée, pas une conversion exacte.
  - .cache_cnig/PLU/QGIS/QML/plu_zone_urba_ge.qml [SimpleLine].perpendicularOffset : unité QML 'Point' convertie en pixels via dpi=90.0 (3.0Point -> 3.750px) — approximation dépendante d'une résolution supposée, pas une conversion exacte.
  - .cache_cnig/PLU/QGIS/QML/plu_zone_urba_ge.qml [SimpleLine].width : unité QML 'Point' convertie en pixels via dpi=90.0 (2.5Point -> 3.125px) — approximation dépendante d'une résolution supposée, pas une conversion exacte.
  - .cache_cnig/PLU/QGIS/QML/plu_zone_urba_ge.qml [SimpleLine].width : unité QML 'Point' convertie en pixels via dpi=90.0 (7.0Point -> 8.750px) — approximation dépendante d'une résolution supposée, pas une conversion exacte.
  - .cache_cnig/PLU/QGIS/QML/plu_zone_urba_ge.qml [SimpleLine].perpendicularOffset : unité QML 'Point' convertie en pixels via dpi=90.0 (3.0Point -> 3.750px) — approximation dépendante d'une résolution supposée, pas une conversion exacte.
  - .cache_cnig/PLU/QGIS/QML/plu_zone_urba_ge.qml [SimpleLine].width : unité QML 'Point' convertie en pixels via dpi=90.0 (2.5Point -> 3.125px) — approximation dépendante d'une résolution supposée, pas une conversion exacte.
- `plu_zone_urba_pe.qml`
  - .cache_cnig/PLU/QGIS/QML/plu_zone_urba_pe.qml [SimpleFill].outlineWidth : unité QML 'MM' convertie en pixels via dpi=90.0 (0.0MM -> 0.000px) — approximation dépendante d'une résolution supposée, pas une conversion exacte.
  - .cache_cnig/PLU/QGIS/QML/plu_zone_urba_pe.qml [SimpleLine].width : unité QML 'Point' convertie en pixels via dpi=90.0 (0.8Point -> 1.000px) — approximation dépendante d'une résolution supposée, pas une conversion exacte.
  - .cache_cnig/PLU/QGIS/QML/plu_zone_urba_pe.qml [SimpleFill].outlineWidth : unité QML 'MM' convertie en pixels via dpi=90.0 (0.0MM -> 0.000px) — approximation dépendante d'une résolution supposée, pas une conversion exacte.
  - .cache_cnig/PLU/QGIS/QML/plu_zone_urba_pe.qml [SimpleLine].width : unité QML 'Point' convertie en pixels via dpi=90.0 (0.8Point -> 1.000px) — approximation dépendante d'une résolution supposée, pas une conversion exacte.
  - .cache_cnig/PLU/QGIS/QML/plu_zone_urba_pe.qml [SimpleFill].outlineWidth : unité QML 'MM' convertie en pixels via dpi=90.0 (0.0MM -> 0.000px) — approximation dépendante d'une résolution supposée, pas une conversion exacte.
  - .cache_cnig/PLU/QGIS/QML/plu_zone_urba_pe.qml [SimpleLine].width : unité QML 'Point' convertie en pixels via dpi=90.0 (0.8Point -> 1.000px) — approximation dépendante d'une résolution supposée, pas une conversion exacte.
- `psmv_inf_l.qml`
  - .cache_cnig/PSMV/QGIS/QML/psmv_inf_l.qml [SimpleLine].width : unité QML 'Point' convertie en pixels via dpi=90.0 (1.5Point -> 1.875px) — approximation dépendante d'une résolution supposée, pas une conversion exacte.
  - .cache_cnig/PSMV/QGIS/QML/psmv_inf_l.qml [SimpleLine].dasharray : unité QML 'Point' convertie en pixels via dpi=90.0 (6.0Point -> 7.500px) — approximation dépendante d'une résolution supposée, pas une conversion exacte.
  - .cache_cnig/PSMV/QGIS/QML/psmv_inf_l.qml [SimpleLine].dasharray : unité QML 'Point' convertie en pixels via dpi=90.0 (10.0Point -> 12.500px) — approximation dépendante d'une résolution supposée, pas une conversion exacte.
  - .cache_cnig/PSMV/QGIS/QML/psmv_inf_l.qml [SimpleLine].dashOffset : unité QML 'MM' convertie en pixels via dpi=90.0 (0.0MM -> 0.000px) — approximation dépendante d'une résolution supposée, pas une conversion exacte.
  - .cache_cnig/PSMV/QGIS/QML/psmv_inf_l.qml [MarkerLine] : outline_color/outline_width non représentables par IconSymbolizer (pas de champ de trait séparé) — non traduits.
  - .cache_cnig/PSMV/QGIS/QML/psmv_inf_l.qml [MarkerLine] [SvgMarker].size : unité QML 'Point' convertie en pixels via dpi=90.0 (6.60156Point -> 8.252px) — approximation dépendante d'une résolution supposée, pas une conversion exacte.
- `psmv_inf_p.qml`
  - .cache_cnig/PSMV/QGIS/QML/psmv_inf_p.qml : outline_color/outline_width non représentables par IconSymbolizer (pas de champ de trait séparé) — non traduits.
  - .cache_cnig/PSMV/QGIS/QML/psmv_inf_p.qml [SvgMarker].size : unité QML 'Point' convertie en pixels via dpi=90.0 (6.60156Point -> 8.252px) — approximation dépendante d'une résolution supposée, pas une conversion exacte.
  - .cache_cnig/PSMV/QGIS/QML/psmv_inf_p.qml : outline_color/outline_width non représentables par IconSymbolizer (pas de champ de trait séparé) — non traduits.
  - .cache_cnig/PSMV/QGIS/QML/psmv_inf_p.qml [SvgMarker].size : unité QML 'Point' convertie en pixels via dpi=90.0 (10.1792Point -> 12.724px) — approximation dépendante d'une résolution supposée, pas une conversion exacte.
  - .cache_cnig/PSMV/QGIS/QML/psmv_inf_p.qml : outline_color/outline_width non représentables par IconSymbolizer (pas de champ de trait séparé) — non traduits.
  - .cache_cnig/PSMV/QGIS/QML/psmv_inf_p.qml [SvgMarker].size : unité QML 'Point' convertie en pixels via dpi=90.0 (20.0Point -> 25.000px) — approximation dépendante d'une résolution supposée, pas une conversion exacte.
- `psmv_inf_s.qml`
  - .cache_cnig/PSMV/QGIS/QML/psmv_inf_s.qml [SimpleLine].width : unité QML 'Point' convertie en pixels via dpi=90.0 (3.0Point -> 3.750px) — approximation dépendante d'une résolution supposée, pas une conversion exacte.
  - .cache_cnig/PSMV/QGIS/QML/psmv_inf_s.qml [SimpleLine].dasharray : unité QML 'Point' convertie en pixels via dpi=90.0 (6.0Point -> 7.500px) — approximation dépendante d'une résolution supposée, pas une conversion exacte.
  - .cache_cnig/PSMV/QGIS/QML/psmv_inf_s.qml [SimpleLine].dasharray : unité QML 'Point' convertie en pixels via dpi=90.0 (2.0Point -> 2.500px) — approximation dépendante d'une résolution supposée, pas une conversion exacte.
  - .cache_cnig/PSMV/QGIS/QML/psmv_inf_s.qml [SimpleLine].dasharray : unité QML 'Point' convertie en pixels via dpi=90.0 (3.0Point -> 3.750px) — approximation dépendante d'une résolution supposée, pas une conversion exacte.
  - .cache_cnig/PSMV/QGIS/QML/psmv_inf_s.qml [SimpleLine].dasharray : unité QML 'Point' convertie en pixels via dpi=90.0 (2.0Point -> 2.500px) — approximation dépendante d'une résolution supposée, pas une conversion exacte.
  - .cache_cnig/PSMV/QGIS/QML/psmv_inf_s.qml [SimpleLine].dashOffset : unité QML 'MM' convertie en pixels via dpi=90.0 (0.0MM -> 0.000px) — approximation dépendante d'une résolution supposée, pas une conversion exacte.
- `psmv_psc_l.qml`
  - .cache_cnig/PSMV/QGIS/QML/psmv_psc_l.qml [MarkerLine] [SimpleMarker].radius : unité QML 'Point' convertie en pixels via dpi=90.0 (2.5Point -> 3.125px) — approximation dépendante d'une résolution supposée, pas une conversion exacte.
  - .cache_cnig/PSMV/QGIS/QML/psmv_psc_l.qml [MarkerLine] [SimpleMarker].strokeWidth : unité QML 'MM' convertie en pixels via dpi=90.0 (0.0MM -> 0.000px) — approximation dépendante d'une résolution supposée, pas une conversion exacte.
  - .cache_cnig/PSMV/QGIS/QML/psmv_psc_l.qml [MarkerLine].spacing : unité QML 'Point' convertie en pixels via dpi=90.0 (11.0Point -> 13.750px) — approximation dépendante d'une résolution supposée, pas une conversion exacte.
  - .cache_cnig/PSMV/QGIS/QML/psmv_psc_l.qml [MarkerLine] [SimpleMarker].radius : unité QML 'Point' convertie en pixels via dpi=90.0 (2.5Point -> 3.125px) — approximation dépendante d'une résolution supposée, pas une conversion exacte.
  - .cache_cnig/PSMV/QGIS/QML/psmv_psc_l.qml [MarkerLine] [SimpleMarker].strokeWidth : unité QML 'MM' convertie en pixels via dpi=90.0 (0.0MM -> 0.000px) — approximation dépendante d'une résolution supposée, pas une conversion exacte.
  - .cache_cnig/PSMV/QGIS/QML/psmv_psc_l.qml [MarkerLine].spacing : unité QML 'Point' convertie en pixels via dpi=90.0 (11.0Point -> 13.750px) — approximation dépendante d'une résolution supposée, pas une conversion exacte.
- `psmv_psc_p.qml`
  - .cache_cnig/PSMV/QGIS/QML/psmv_psc_p.qml [SimpleMarker].radius : unité QML 'Point' convertie en pixels via dpi=90.0 (3.5Point -> 4.375px) — approximation dépendante d'une résolution supposée, pas une conversion exacte.
  - .cache_cnig/PSMV/QGIS/QML/psmv_psc_p.qml [SimpleMarker].strokeWidth : unité QML 'MM' convertie en pixels via dpi=90.0 (0.0MM -> 0.000px) — approximation dépendante d'une résolution supposée, pas une conversion exacte.
  - .cache_cnig/PSMV/QGIS/QML/psmv_psc_p.qml [SimpleMarker].radius : unité QML 'Point' convertie en pixels via dpi=90.0 (3.5Point -> 4.375px) — approximation dépendante d'une résolution supposée, pas une conversion exacte.
  - .cache_cnig/PSMV/QGIS/QML/psmv_psc_p.qml [SimpleMarker].strokeWidth : unité QML 'MM' convertie en pixels via dpi=90.0 (0.0MM -> 0.000px) — approximation dépendante d'une résolution supposée, pas une conversion exacte.
  - .cache_cnig/PSMV/QGIS/QML/psmv_psc_p.qml [SimpleMarker].radius : unité QML 'Point' convertie en pixels via dpi=90.0 (5.2201Point -> 6.525px) — approximation dépendante d'une résolution supposée, pas une conversion exacte.
  - .cache_cnig/PSMV/QGIS/QML/psmv_psc_p.qml [SimpleMarker].strokeWidth : unité QML 'Point' convertie en pixels via dpi=90.0 (1.5Point -> 1.875px) — approximation dépendante d'une résolution supposée, pas une conversion exacte.
- `psmv_psc_s.qml`
  - .cache_cnig/PSMV/QGIS/QML/psmv_psc_s.qml [SimpleLine].width : unité QML 'Point' convertie en pixels via dpi=90.0 (0.8Point -> 1.000px) — approximation dépendante d'une résolution supposée, pas une conversion exacte.
  - .cache_cnig/PSMV/QGIS/QML/psmv_psc_s.qml [PointPatternFill] [SimpleMarker].radius : unité QML 'Point' convertie en pixels via dpi=90.0 (5.0Point -> 6.250px) — approximation dépendante d'une résolution supposée, pas une conversion exacte.
  - .cache_cnig/PSMV/QGIS/QML/psmv_psc_s.qml [PointPatternFill] [SimpleMarker].strokeWidth : unité QML 'Point' convertie en pixels via dpi=90.0 (0.4Point -> 0.500px) — approximation dépendante d'une résolution supposée, pas une conversion exacte.
  - .cache_cnig/PSMV/QGIS/QML/psmv_psc_s.qml [PointPatternFill] : distance_x/distance_y approximés via graphicFillPadding (marge autour du motif répété) — pas une correspondance exacte à l'espacement QGIS, dépend du moteur de rendu SLD/MBStyle final (non vérifié sur un rendu réel).
  - .cache_cnig/PSMV/QGIS/QML/psmv_psc_s.qml [PointPatternFill] [SimpleMarker].radius : unité QML 'Point' convertie en pixels via dpi=90.0 (2.5Point -> 3.125px) — approximation dépendante d'une résolution supposée, pas une conversion exacte.
  - .cache_cnig/PSMV/QGIS/QML/psmv_psc_s.qml [PointPatternFill] [SimpleMarker].strokeWidth : unité QML 'Point' convertie en pixels via dpi=90.0 (0.0Point -> 0.000px) — approximation dépendante d'une résolution supposée, pas une conversion exacte.
- `psmv_zone_urba.qml`
  - .cache_cnig/PSMV/QGIS/QML/psmv_zone_urba.qml [SimpleLine].width : unité QML 'Point' convertie en pixels via dpi=90.0 (3.0Point -> 3.750px) — approximation dépendante d'une résolution supposée, pas une conversion exacte.
  - .cache_cnig/PSMV/QGIS/QML/psmv_zone_urba.qml [SimpleLine].dasharray : unité QML 'Point' convertie en pixels via dpi=90.0 (3.0Point -> 3.750px) — approximation dépendante d'une résolution supposée, pas une conversion exacte.
  - .cache_cnig/PSMV/QGIS/QML/psmv_zone_urba.qml [SimpleLine].dasharray : unité QML 'Point' convertie en pixels via dpi=90.0 (2.0Point -> 2.500px) — approximation dépendante d'une résolution supposée, pas une conversion exacte.
  - .cache_cnig/PSMV/QGIS/QML/psmv_zone_urba.qml [SimpleLine].dashOffset : unité QML 'MM' convertie en pixels via dpi=90.0 (0.0MM -> 0.000px) — approximation dépendante d'une résolution supposée, pas une conversion exacte.
  - MBStyle : Rule[0] (ZONE_U_001).symbolizers[0] : propriété de symbolizer 'dashOffset' (valeur 0.0) NON écrite dans le document Mapbox produit — hors de la portée bornée de cet écrivain pour cette itération, PAS silencieusement ignorée.
  - MBStyle : Rule[0] (ZONE_U_001).symbolizers[0] : propriété de symbolizer 'widthUnit' (valeur 'px') NON écrite dans le document Mapbox produit — hors de la portée bornée de cet écrivain pour cette itération, PAS silencieusement ignorée.
- `ASSIETTE_SUP_S.qml`
  - .cache_cnig/SUP/QGIS/QML/ASSIETTE_SUP_S.qml : idiome QGIS string_to_array(champ,'-')[0] = 'a1' reconnu et traduit en LIKE préfixe (insensible à la casse) 'champ LIKE a1-%' — équivalent au comportement, pas une reconstruction d'un opérateur tableau générique (le pivot n'en a pas, voir _reconnaitre_idiome_prefixe_tableau).
  - .cache_cnig/SUP/QGIS/QML/ASSIETTE_SUP_S.qml [PointPatternFill] [FontMarker] : traduit en wellKnownName 'ttf://Wingdings#0x00f1' — construction correcte (le point de code vient de chr, pas deviné), mais la convention exacte de padding hexadécimal attendue par un moteur SLD donné n'a pas été vérifiée sur un rendu réel (aucun accès GeoServer depuis cet environnement) ; radius = size/2 par analogie avec les autres marqueurs, alors que la sémantique exacte de 'size' pour un glyphe de police (FontMarker n'a pas de scale_method, à la différence de SimpleMarker) n'est pas confirmée non plus.
  - .cache_cnig/SUP/QGIS/QML/ASSIETTE_SUP_S.qml [PointPatternFill] : distance_x/distance_y approximés via graphicFillPadding (marge autour du motif répété) — pas une correspondance exacte à l'espacement QGIS, dépend du moteur de rendu SLD/MBStyle final (non vérifié sur un rendu réel).
  - .cache_cnig/SUP/QGIS/QML/ASSIETTE_SUP_S.qml [SimpleFill].outlineWidth : unité QML 'Point' convertie en pixels via dpi=90.0 (0.5Point -> 0.625px) — approximation dépendante d'une résolution supposée, pas une conversion exacte.
  - .cache_cnig/SUP/QGIS/QML/ASSIETTE_SUP_S.qml : idiome QGIS string_to_array(champ,'-')[0] = 'a2' reconnu et traduit en LIKE préfixe (insensible à la casse) 'champ LIKE a2-%' — équivalent au comportement, pas une reconstruction d'un opérateur tableau générique (le pivot n'en a pas, voir _reconnaitre_idiome_prefixe_tableau).
  - .cache_cnig/SUP/QGIS/QML/ASSIETTE_SUP_S.qml : idiome QGIS string_to_array(champ,'-')[0] = 'a3' reconnu et traduit en LIKE préfixe (insensible à la casse) 'champ LIKE a3-%' — équivalent au comportement, pas une reconstruction d'un opérateur tableau générique (le pivot n'en a pas, voir _reconnaitre_idiome_prefixe_tableau).
- `sup_ass.qml`
  - .cache_cnig/SUP/QGIS/QML/sup_ass.qml [SimpleLine].width : unité QML 'Point' convertie en pixels via dpi=90.0 (0.5Point -> 0.625px) — approximation dépendante d'une résolution supposée, pas une conversion exacte.
  - .cache_cnig/SUP/QGIS/QML/sup_ass.qml [PointPatternFill] : outline_color/outline_width non représentables par IconSymbolizer (pas de champ de trait séparé) — non traduits.
  - .cache_cnig/SUP/QGIS/QML/sup_ass.qml [PointPatternFill] [SvgMarker].size : unité QML 'Point' convertie en pixels via dpi=90.0 (7.06992Point -> 8.837px) — approximation dépendante d'une résolution supposée, pas une conversion exacte.
  - .cache_cnig/SUP/QGIS/QML/sup_ass.qml [PointPatternFill] : distance_x/distance_y approximés via graphicFillPadding (marge autour du motif répété) — pas une correspondance exacte à l'espacement QGIS, dépend du moteur de rendu SLD/MBStyle final (non vérifié sur un rendu réel).
  - .cache_cnig/SUP/QGIS/QML/sup_ass.qml [SimpleLine].width : unité QML 'Point' convertie en pixels via dpi=90.0 (1.2Point -> 1.500px) — approximation dépendante d'une résolution supposée, pas une conversion exacte.
  - .cache_cnig/SUP/QGIS/QML/sup_ass.qml [PointPatternFill] : outline_color/outline_width non représentables par IconSymbolizer (pas de champ de trait séparé) — non traduits.
