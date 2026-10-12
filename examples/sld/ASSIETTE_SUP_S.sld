<?xml version="1.0" encoding="UTF-8"?>
<StyledLayerDescriptor xmlns="http://www.opengis.net/sld" xmlns:ogc="http://www.opengis.net/ogc" xmlns:xlink="http://www.w3.org/1999/xlink" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" version="1.0.0" xsi:schemaLocation="http://www.opengis.net/sld http://schemas.opengis.net/sld/1.0.0/StyledLayerDescriptor.xsd">
  <NamedLayer>
    <Name>ASSIETTE_SUP_S</Name>
    <UserStyle>
      <Title>ASSIETTE_SUP_S</Title>
      <FeatureTypeStyle>
        <Rule>
          <Name>Protection des bois et forêts à Mayotte - A1</Name>
          <ogc:Filter>
            <ogc:PropertyIsLike wildCard="%" singleChar="_" escape="\" matchCase="false">
              <ogc:PropertyName>idass</ogc:PropertyName>
              <ogc:Literal>a1-%</ogc:Literal>
            </ogc:PropertyIsLike>
          </ogc:Filter>
          <PolygonSymbolizer>
            <Fill>
              <GraphicFill>
                <Graphic>
                  <Mark>
                    <WellKnownName>square</WellKnownName>
                    <Fill>
                      <CssParameter name="fill">#00ff00</CssParameter>
                      <CssParameter name="fill-opacity">1.0</CssParameter>
                    </Fill>
                    <Stroke>
                      <CssParameter name="stroke">#00ff00</CssParameter>
                      <CssParameter name="stroke-width">1.0</CssParameter>
                      <CssParameter name="stroke-opacity">1.0</CssParameter>
                    </Stroke>
                  </Mark>
                  <Size>15.0</Size>
                  <Rotation>0.0</Rotation>
                </Graphic>
              </GraphicFill>
            </Fill>
            <VendorOption name="graphic-margin">0</VendorOption>
          </PolygonSymbolizer>
          <PolygonSymbolizer>
            <Fill>
              <CssParameter name="fill">#0000ff</CssParameter>
              <CssParameter name="fill-opacity">1.0</CssParameter>
            </Fill>
            <Stroke>
              <CssParameter name="stroke">#00ff00</CssParameter>
              <CssParameter name="stroke-width">0.625</CssParameter>
              <CssParameter name="stroke-opacity">1.0</CssParameter>
            </Stroke>
          </PolygonSymbolizer>
        </Rule>
        <Rule>
          <Name>Conduites d'irrigation - A2</Name>
          <ogc:Filter>
            <ogc:PropertyIsLike wildCard="%" singleChar="_" escape="\" matchCase="false">
              <ogc:PropertyName>idass</ogc:PropertyName>
              <ogc:Literal>a2-%</ogc:Literal>
            </ogc:PropertyIsLike>
          </ogc:Filter>
          <LineSymbolizer>
            <Stroke>
              <CssParameter name="stroke">#00ff00</CssParameter>
              <CssParameter name="stroke-width">3.0</CssParameter>
              <CssParameter name="stroke-opacity">1.0</CssParameter>
              <CssParameter name="stroke-linecap">square</CssParameter>
              <CssParameter name="stroke-linejoin">bevel</CssParameter>
            </Stroke>
          </LineSymbolizer>
        </Rule>
        <Rule>
          <Name>Entretien des canaux d'irigation - A3</Name>
          <ogc:Filter>
            <ogc:PropertyIsLike wildCard="%" singleChar="_" escape="\" matchCase="false">
              <ogc:PropertyName>idass</ogc:PropertyName>
              <ogc:Literal>a3-%</ogc:Literal>
            </ogc:PropertyIsLike>
          </ogc:Filter>
          <LineSymbolizer>
            <Stroke>
              <CssParameter name="stroke">#00ff00</CssParameter>
              <CssParameter name="stroke-width">2.0</CssParameter>
              <CssParameter name="stroke-opacity">1.0</CssParameter>
              <CssParameter name="stroke-linecap">square</CssParameter>
              <CssParameter name="stroke-linejoin">bevel</CssParameter>
              <CssParameter name="stroke-dasharray">18.0 10.0</CssParameter>
            </Stroke>
          </LineSymbolizer>
        </Rule>
        <Rule>
          <Name>Lits et berges des cours d'eau - A4</Name>
          <ogc:Filter>
            <ogc:PropertyIsLike wildCard="%" singleChar="_" escape="\" matchCase="false">
              <ogc:PropertyName>idass</ogc:PropertyName>
              <ogc:Literal>a4-%</ogc:Literal>
            </ogc:PropertyIsLike>
          </ogc:Filter>
          <LineSymbolizer>
            <Stroke>
              <CssParameter name="stroke">#00ff00</CssParameter>
              <CssParameter name="stroke-width">2.0</CssParameter>
              <CssParameter name="stroke-opacity">1.0</CssParameter>
              <CssParameter name="stroke-linecap">square</CssParameter>
              <CssParameter name="stroke-linejoin">bevel</CssParameter>
              <CssParameter name="stroke-dasharray">4.0 5.0</CssParameter>
            </Stroke>
          </LineSymbolizer>
        </Rule>
        <Rule>
          <Name>Canalisations publiques d'eau et assainissement - A5</Name>
          <ogc:Filter>
            <ogc:PropertyIsLike wildCard="%" singleChar="_" escape="\" matchCase="false">
              <ogc:PropertyName>idass</ogc:PropertyName>
              <ogc:Literal>a5-%</ogc:Literal>
            </ogc:PropertyIsLike>
          </ogc:Filter>
          <LineSymbolizer>
            <Stroke>
              <CssParameter name="stroke">#00ff00</CssParameter>
              <CssParameter name="stroke-width">3.0</CssParameter>
              <CssParameter name="stroke-opacity">1.0</CssParameter>
              <CssParameter name="stroke-linecap">square</CssParameter>
              <CssParameter name="stroke-linejoin">bevel</CssParameter>
            </Stroke>
          </LineSymbolizer>
        </Rule>
        <Rule>
          <Name>Ecoulement des eaux nuisibles - A6</Name>
          <ogc:Filter>
            <ogc:PropertyIsLike wildCard="%" singleChar="_" escape="\" matchCase="false">
              <ogc:PropertyName>idass</ogc:PropertyName>
              <ogc:Literal>a6-%</ogc:Literal>
            </ogc:PropertyIsLike>
          </ogc:Filter>
          <LineSymbolizer>
            <Stroke>
              <CssParameter name="stroke">#00ff00</CssParameter>
              <CssParameter name="stroke-width">1.0</CssParameter>
              <CssParameter name="stroke-opacity">1.0</CssParameter>
              <CssParameter name="stroke-linecap">square</CssParameter>
              <CssParameter name="stroke-linejoin">bevel</CssParameter>
            </Stroke>
          </LineSymbolizer>
          <PolygonSymbolizer>
            <Fill>
              <GraphicFill>
                <Graphic>
                  <Mark>
                    <WellKnownName>square</WellKnownName>
                    <Fill>
                      <CssParameter name="fill">#00ff00</CssParameter>
                      <CssParameter name="fill-opacity">1.0</CssParameter>
                    </Fill>
                    <Stroke>
                      <CssParameter name="stroke">#00ff00</CssParameter>
                      <CssParameter name="stroke-width">1.0</CssParameter>
                      <CssParameter name="stroke-opacity">1.0</CssParameter>
                    </Stroke>
                  </Mark>
                  <Size>8.0</Size>
                  <Rotation>0.0</Rotation>
                </Graphic>
              </GraphicFill>
            </Fill>
            <VendorOption name="graphic-margin">0</VendorOption>
          </PolygonSymbolizer>
        </Rule>
        <Rule>
          <Name>Forêts dites de protection - A7</Name>
          <ogc:Filter>
            <ogc:PropertyIsLike wildCard="%" singleChar="_" escape="\" matchCase="false">
              <ogc:PropertyName>idass</ogc:PropertyName>
              <ogc:Literal>a7-%</ogc:Literal>
            </ogc:PropertyIsLike>
          </ogc:Filter>
          <PolygonSymbolizer>
            <Fill>
              <GraphicFill>
                <Graphic>
                  <Mark>
                    <WellKnownName>square</WellKnownName>
                    <Fill>
                      <CssParameter name="fill">#00ff00</CssParameter>
                      <CssParameter name="fill-opacity">1.0</CssParameter>
                    </Fill>
                    <Stroke>
                      <CssParameter name="stroke">#00ff00</CssParameter>
                      <CssParameter name="stroke-width">1.0</CssParameter>
                      <CssParameter name="stroke-opacity">1.0</CssParameter>
                    </Stroke>
                  </Mark>
                  <Size>15.0</Size>
                  <Rotation>0.0</Rotation>
                </Graphic>
              </GraphicFill>
            </Fill>
            <VendorOption name="graphic-margin">0</VendorOption>
          </PolygonSymbolizer>
          <PolygonSymbolizer>
            <Fill>
              <CssParameter name="fill">#0000ff</CssParameter>
              <CssParameter name="fill-opacity">1.0</CssParameter>
            </Fill>
            <Stroke>
              <CssParameter name="stroke">#00ff00</CssParameter>
              <CssParameter name="stroke-width">0.625</CssParameter>
              <CssParameter name="stroke-opacity">1.0</CssParameter>
            </Stroke>
          </PolygonSymbolizer>
        </Rule>
        <Rule>
          <Name>Terrains en montagne et dunes - A8</Name>
          <ogc:Filter>
            <ogc:PropertyIsLike wildCard="%" singleChar="_" escape="\" matchCase="false">
              <ogc:PropertyName>idass</ogc:PropertyName>
              <ogc:Literal>a8-%</ogc:Literal>
            </ogc:PropertyIsLike>
          </ogc:Filter>
          <PolygonSymbolizer>
            <Fill>
              <GraphicFill>
                <Graphic>
                  <Mark>
                    <WellKnownName>square</WellKnownName>
                    <Fill>
                      <CssParameter name="fill">#00ff00</CssParameter>
                      <CssParameter name="fill-opacity">1.0</CssParameter>
                    </Fill>
                    <Stroke>
                      <CssParameter name="stroke">#07c135</CssParameter>
                      <CssParameter name="stroke-width">1.0</CssParameter>
                      <CssParameter name="stroke-opacity">1.0</CssParameter>
                    </Stroke>
                  </Mark>
                  <Size>15.0</Size>
                  <Rotation>0.0</Rotation>
                </Graphic>
              </GraphicFill>
            </Fill>
            <VendorOption name="graphic-margin">0</VendorOption>
          </PolygonSymbolizer>
          <PolygonSymbolizer>
            <Fill>
              <CssParameter name="fill">#0000ff</CssParameter>
              <CssParameter name="fill-opacity">1.0</CssParameter>
            </Fill>
            <Stroke>
              <CssParameter name="stroke">#00ff00</CssParameter>
              <CssParameter name="stroke-width">0.5</CssParameter>
              <CssParameter name="stroke-opacity">1.0</CssParameter>
            </Stroke>
          </PolygonSymbolizer>
        </Rule>
        <Rule>
          <Name>Zones agricoles protégées - A9</Name>
          <ogc:Filter>
            <ogc:PropertyIsLike wildCard="%" singleChar="_" escape="\" matchCase="false">
              <ogc:PropertyName>idass</ogc:PropertyName>
              <ogc:Literal>a9-%</ogc:Literal>
            </ogc:PropertyIsLike>
          </ogc:Filter>
          <LineSymbolizer>
            <Stroke>
              <CssParameter name="stroke">#00ff00</CssParameter>
              <CssParameter name="stroke-width">1.2</CssParameter>
              <CssParameter name="stroke-opacity">1.0</CssParameter>
              <CssParameter name="stroke-linecap">square</CssParameter>
              <CssParameter name="stroke-linejoin">bevel</CssParameter>
            </Stroke>
          </LineSymbolizer>
          <PolygonSymbolizer>
            <Fill>
              <GraphicFill>
                <Graphic>
                  <Mark>
                    <WellKnownName>square</WellKnownName>
                    <Fill>
                      <CssParameter name="fill">#00ff00</CssParameter>
                      <CssParameter name="fill-opacity">1.0</CssParameter>
                    </Fill>
                    <Stroke>
                      <CssParameter name="stroke">#00ff00</CssParameter>
                      <CssParameter name="stroke-width">1.0</CssParameter>
                      <CssParameter name="stroke-opacity">1.0</CssParameter>
                    </Stroke>
                  </Mark>
                  <Size>10.0</Size>
                  <Rotation>0.0</Rotation>
                </Graphic>
              </GraphicFill>
            </Fill>
            <VendorOption name="graphic-margin">0</VendorOption>
          </PolygonSymbolizer>
        </Rule>
        <Rule>
          <Name>Protection naturelle, agricole et forestière du plateau de Saclay - A10</Name>
          <ogc:Filter>
            <ogc:PropertyIsLike wildCard="%" singleChar="_" escape="\" matchCase="false">
              <ogc:PropertyName>idass</ogc:PropertyName>
              <ogc:Literal>a10-%</ogc:Literal>
            </ogc:PropertyIsLike>
          </ogc:Filter>
          <LineSymbolizer>
            <Stroke>
              <CssParameter name="stroke">#00ff00</CssParameter>
              <CssParameter name="stroke-width">1.2</CssParameter>
              <CssParameter name="stroke-opacity">1.0</CssParameter>
              <CssParameter name="stroke-linecap">square</CssParameter>
              <CssParameter name="stroke-linejoin">bevel</CssParameter>
            </Stroke>
          </LineSymbolizer>
          <PolygonSymbolizer>
            <Fill>
              <GraphicFill>
                <Graphic>
                  <Mark>
                    <WellKnownName>square</WellKnownName>
                    <Fill>
                      <CssParameter name="fill">#00ff00</CssParameter>
                      <CssParameter name="fill-opacity">1.0</CssParameter>
                    </Fill>
                    <Stroke>
                      <CssParameter name="stroke">#00ff00</CssParameter>
                      <CssParameter name="stroke-width">1.0</CssParameter>
                      <CssParameter name="stroke-opacity">1.0</CssParameter>
                    </Stroke>
                  </Mark>
                  <Size>10.0</Size>
                  <Rotation>0.0</Rotation>
                </Graphic>
              </GraphicFill>
            </Fill>
            <VendorOption name="graphic-margin">0</VendorOption>
          </PolygonSymbolizer>
        </Rule>
        <Rule>
          <Name>Périmètre des abords - AC1</Name>
          <ogc:Filter>
            <ogc:And>
              <ogc:PropertyIsLike wildCard="%" singleChar="_" escape="\" matchCase="false">
                <ogc:PropertyName>idass</ogc:PropertyName>
                <ogc:Literal>ac1-%</ogc:Literal>
              </ogc:PropertyIsLike>
              <ogc:PropertyIsEqualTo>
                <ogc:PropertyName>typeass</ogc:PropertyName>
                <ogc:Literal>Périmètre des abords</ogc:Literal>
              </ogc:PropertyIsEqualTo>
            </ogc:And>
          </ogc:Filter>
          <LineSymbolizer>
            <Stroke>
              <CssParameter name="stroke">#ff8000</CssParameter>
              <CssParameter name="stroke-width">1.5</CssParameter>
              <CssParameter name="stroke-opacity">1.0</CssParameter>
              <CssParameter name="stroke-linecap">square</CssParameter>
              <CssParameter name="stroke-linejoin">bevel</CssParameter>
            </Stroke>
          </LineSymbolizer>
          <PolygonSymbolizer>
            <Fill>
              <GraphicFill>
                <Graphic>
                  <Mark>
                    <WellKnownName>shape://slash</WellKnownName>
                    <Stroke>
                      <CssParameter name="stroke">#ff8000</CssParameter>
                      <CssParameter name="stroke-width">0.8</CssParameter>
                      <CssParameter name="stroke-opacity">1</CssParameter>
                    </Stroke>
                  </Mark>
                  <Size>5</Size>
                </Graphic>
              </GraphicFill>
            </Fill>
            <VendorOption name="graphic-margin">0</VendorOption>
          </PolygonSymbolizer>
        </Rule>
        <Rule>
          <Name>Monuments historiques - AC1</Name>
          <ogc:Filter>
            <ogc:And>
              <ogc:PropertyIsLike wildCard="%" singleChar="_" escape="\" matchCase="false">
                <ogc:PropertyName>idass</ogc:PropertyName>
                <ogc:Literal>ac1-%</ogc:Literal>
              </ogc:PropertyIsLike>
              <ogc:PropertyIsEqualTo>
                <ogc:PropertyName>typeass</ogc:PropertyName>
                <ogc:Literal>Monument historique</ogc:Literal>
              </ogc:PropertyIsEqualTo>
            </ogc:And>
          </ogc:Filter>
          <LineSymbolizer>
            <Stroke>
              <CssParameter name="stroke">#ff8000</CssParameter>
              <CssParameter name="stroke-width">2.0</CssParameter>
              <CssParameter name="stroke-opacity">1.0</CssParameter>
              <CssParameter name="stroke-linecap">square</CssParameter>
              <CssParameter name="stroke-linejoin">bevel</CssParameter>
            </Stroke>
          </LineSymbolizer>
          <PolygonSymbolizer>
            <Fill>
              <GraphicFill>
                <Graphic>
                  <Mark>
                    <WellKnownName>circle</WellKnownName>
                    <Fill>
                      <CssParameter name="fill">#ff8000</CssParameter>
                      <CssParameter name="fill-opacity">1.0</CssParameter>
                    </Fill>
                    <Stroke>
                      <CssParameter name="stroke">#000000</CssParameter>
                      <CssParameter name="stroke-width">0.0</CssParameter>
                      <CssParameter name="stroke-opacity">0.0</CssParameter>
                    </Stroke>
                  </Mark>
                  <Size>2.0</Size>
                  <Rotation>0.0</Rotation>
                </Graphic>
              </GraphicFill>
            </Fill>
            <VendorOption name="graphic-margin">0</VendorOption>
          </PolygonSymbolizer>
        </Rule>
        <Rule>
          <Name>Sites inscrits - AC2</Name>
          <ogc:Filter>
            <ogc:And>
              <ogc:PropertyIsLike wildCard="%" singleChar="_" escape="\" matchCase="false">
                <ogc:PropertyName>idass</ogc:PropertyName>
                <ogc:Literal>ac2-%</ogc:Literal>
              </ogc:PropertyIsLike>
              <ogc:PropertyIsEqualTo>
                <ogc:PropertyName>type</ogc:PropertyName>
                <ogc:Literal>Inscrit</ogc:Literal>
              </ogc:PropertyIsEqualTo>
            </ogc:And>
          </ogc:Filter>
          <LineSymbolizer>
            <Stroke>
              <CssParameter name="stroke">#ff8000</CssParameter>
              <CssParameter name="stroke-width">1.0</CssParameter>
              <CssParameter name="stroke-opacity">1.0</CssParameter>
              <CssParameter name="stroke-linecap">square</CssParameter>
              <CssParameter name="stroke-linejoin">bevel</CssParameter>
            </Stroke>
          </LineSymbolizer>
          <PolygonSymbolizer>
            <Fill>
              <GraphicFill>
                <Graphic>
                  <Mark>
                    <WellKnownName>shape://horline</WellKnownName>
                    <Stroke>
                      <CssParameter name="stroke">#ff8000</CssParameter>
                      <CssParameter name="stroke-width">1</CssParameter>
                      <CssParameter name="stroke-opacity">1</CssParameter>
                    </Stroke>
                  </Mark>
                  <Size>8</Size>
                </Graphic>
              </GraphicFill>
            </Fill>
            <VendorOption name="graphic-margin">0</VendorOption>
          </PolygonSymbolizer>
          <PolygonSymbolizer>
            <Fill>
              <GraphicFill>
                <Graphic>
                  <Mark>
                    <WellKnownName>shape://vertline</WellKnownName>
                    <Stroke>
                      <CssParameter name="stroke">#ff8000</CssParameter>
                      <CssParameter name="stroke-width">1</CssParameter>
                      <CssParameter name="stroke-opacity">1</CssParameter>
                    </Stroke>
                  </Mark>
                  <Size>8</Size>
                </Graphic>
              </GraphicFill>
            </Fill>
            <VendorOption name="graphic-margin">0</VendorOption>
          </PolygonSymbolizer>
        </Rule>
        <Rule>
          <Name>Sites classés - AC2</Name>
          <ogc:Filter>
            <ogc:And>
              <ogc:PropertyIsLike wildCard="%" singleChar="_" escape="\" matchCase="false">
                <ogc:PropertyName>idass</ogc:PropertyName>
                <ogc:Literal>ac2-%</ogc:Literal>
              </ogc:PropertyIsLike>
              <ogc:PropertyIsEqualTo>
                <ogc:PropertyName>type</ogc:PropertyName>
                <ogc:Literal>Classé</ogc:Literal>
              </ogc:PropertyIsEqualTo>
            </ogc:And>
          </ogc:Filter>
          <LineSymbolizer>
            <Stroke>
              <CssParameter name="stroke">#ff8000</CssParameter>
              <CssParameter name="stroke-width">1.0</CssParameter>
              <CssParameter name="stroke-opacity">1.0</CssParameter>
              <CssParameter name="stroke-linecap">square</CssParameter>
              <CssParameter name="stroke-linejoin">bevel</CssParameter>
            </Stroke>
          </LineSymbolizer>
          <PolygonSymbolizer>
            <Fill>
              <GraphicFill>
                <Graphic>
                  <Mark>
                    <WellKnownName>shape://horline</WellKnownName>
                    <Stroke>
                      <CssParameter name="stroke">#ff8000</CssParameter>
                      <CssParameter name="stroke-width">1</CssParameter>
                      <CssParameter name="stroke-opacity">1</CssParameter>
                    </Stroke>
                  </Mark>
                  <Size>4</Size>
                </Graphic>
              </GraphicFill>
            </Fill>
            <VendorOption name="graphic-margin">0</VendorOption>
          </PolygonSymbolizer>
          <PolygonSymbolizer>
            <Fill>
              <GraphicFill>
                <Graphic>
                  <Mark>
                    <WellKnownName>shape://vertline</WellKnownName>
                    <Stroke>
                      <CssParameter name="stroke">#ff8000</CssParameter>
                      <CssParameter name="stroke-width">1</CssParameter>
                      <CssParameter name="stroke-opacity">1</CssParameter>
                    </Stroke>
                  </Mark>
                  <Size>4</Size>
                </Graphic>
              </GraphicFill>
            </Fill>
            <VendorOption name="graphic-margin">0</VendorOption>
          </PolygonSymbolizer>
        </Rule>
        <Rule>
          <Name>Réserves naturelles - AC3</Name>
          <ogc:Filter>
            <ogc:PropertyIsLike wildCard="%" singleChar="_" escape="\" matchCase="false">
              <ogc:PropertyName>idass</ogc:PropertyName>
              <ogc:Literal>ac3-%</ogc:Literal>
            </ogc:PropertyIsLike>
          </ogc:Filter>
          <LineSymbolizer>
            <Stroke>
              <CssParameter name="stroke">#ff8000</CssParameter>
              <CssParameter name="stroke-width">1.5</CssParameter>
              <CssParameter name="stroke-opacity">1.0</CssParameter>
              <CssParameter name="stroke-linecap">square</CssParameter>
              <CssParameter name="stroke-linejoin">bevel</CssParameter>
            </Stroke>
          </LineSymbolizer>
          <PolygonSymbolizer>
            <Fill>
              <GraphicFill>
                <Graphic>
                  <Mark>
                    <WellKnownName>square</WellKnownName>
                    <Fill>
                      <CssParameter name="fill">#ff8000</CssParameter>
                      <CssParameter name="fill-opacity">1.0</CssParameter>
                    </Fill>
                    <Stroke>
                      <CssParameter name="stroke">#ff8000</CssParameter>
                      <CssParameter name="stroke-width">1.0</CssParameter>
                      <CssParameter name="stroke-opacity">1.0</CssParameter>
                    </Stroke>
                  </Mark>
                  <Size>8.0</Size>
                  <Rotation>0.0</Rotation>
                </Graphic>
              </GraphicFill>
            </Fill>
            <VendorOption name="graphic-margin">0</VendorOption>
          </PolygonSymbolizer>
        </Rule>
        <Rule>
          <Name>Sites patrimoniaux remarquables - AC4</Name>
          <ogc:Filter>
            <ogc:PropertyIsLike wildCard="%" singleChar="_" escape="\" matchCase="false">
              <ogc:PropertyName>idass</ogc:PropertyName>
              <ogc:Literal>ac4-%</ogc:Literal>
            </ogc:PropertyIsLike>
          </ogc:Filter>
          <LineSymbolizer>
            <Stroke>
              <CssParameter name="stroke">#ff8000</CssParameter>
              <CssParameter name="stroke-width">1.5</CssParameter>
              <CssParameter name="stroke-opacity">1.0</CssParameter>
              <CssParameter name="stroke-linecap">square</CssParameter>
              <CssParameter name="stroke-linejoin">bevel</CssParameter>
            </Stroke>
          </LineSymbolizer>
          <PolygonSymbolizer>
            <Fill>
              <GraphicFill>
                <Graphic>
                  <Mark>
                    <WellKnownName>shape://backslash</WellKnownName>
                    <Stroke>
                      <CssParameter name="stroke">#ff8000</CssParameter>
                      <CssParameter name="stroke-width">1</CssParameter>
                      <CssParameter name="stroke-opacity">1</CssParameter>
                    </Stroke>
                  </Mark>
                  <Size>8</Size>
                </Graphic>
              </GraphicFill>
            </Fill>
            <VendorOption name="graphic-margin">0</VendorOption>
          </PolygonSymbolizer>
        </Rule>
        <Rule>
          <Name>Plans de Valorisation de l'Architecture et du Patrimoine - AC4bis</Name>
          <ogc:Filter>
            <ogc:PropertyIsLike wildCard="%" singleChar="_" escape="\" matchCase="false">
              <ogc:PropertyName>idass</ogc:PropertyName>
              <ogc:Literal>ac4bis-%</ogc:Literal>
            </ogc:PropertyIsLike>
          </ogc:Filter>
          <LineSymbolizer>
            <Stroke>
              <CssParameter name="stroke">#ff8000</CssParameter>
              <CssParameter name="stroke-width">1.5</CssParameter>
              <CssParameter name="stroke-opacity">1.0</CssParameter>
              <CssParameter name="stroke-linecap">square</CssParameter>
              <CssParameter name="stroke-linejoin">bevel</CssParameter>
            </Stroke>
          </LineSymbolizer>
          <PolygonSymbolizer>
            <Fill>
              <GraphicFill>
                <Graphic>
                  <Mark>
                    <WellKnownName>shape://backslash</WellKnownName>
                    <Stroke>
                      <CssParameter name="stroke">#ff8000</CssParameter>
                      <CssParameter name="stroke-width">1</CssParameter>
                      <CssParameter name="stroke-opacity">1</CssParameter>
                    </Stroke>
                  </Mark>
                  <Size>8</Size>
                </Graphic>
              </GraphicFill>
            </Fill>
            <VendorOption name="graphic-margin">0</VendorOption>
          </PolygonSymbolizer>
        </Rule>
        <Rule>
          <Name>Champs de vue pour la navigation maritime - AR1</Name>
          <ogc:Filter>
            <ogc:PropertyIsLike wildCard="%" singleChar="_" escape="\" matchCase="false">
              <ogc:PropertyName>idass</ogc:PropertyName>
              <ogc:Literal>ar1-%</ogc:Literal>
            </ogc:PropertyIsLike>
          </ogc:Filter>
          <LineSymbolizer>
            <Stroke>
              <CssParameter name="stroke">#800080</CssParameter>
              <CssParameter name="stroke-width">2.0</CssParameter>
              <CssParameter name="stroke-opacity">1.0</CssParameter>
              <CssParameter name="stroke-linecap">square</CssParameter>
              <CssParameter name="stroke-linejoin">bevel</CssParameter>
            </Stroke>
          </LineSymbolizer>
          <PolygonSymbolizer>
            <Fill>
              <GraphicFill>
                <Graphic>
                  <Mark>
                    <WellKnownName>shape://slash</WellKnownName>
                    <Stroke>
                      <CssParameter name="stroke">#800080</CssParameter>
                      <CssParameter name="stroke-width">1</CssParameter>
                      <CssParameter name="stroke-opacity">1</CssParameter>
                    </Stroke>
                  </Mark>
                  <Size>8</Size>
                </Graphic>
              </GraphicFill>
            </Fill>
            <VendorOption name="graphic-margin">0</VendorOption>
          </PolygonSymbolizer>
        </Rule>
        <Rule>
          <Name>Ouvrages de défense ou de sécurité maritime - AR2</Name>
          <ogc:Filter>
            <ogc:PropertyIsLike wildCard="%" singleChar="_" escape="\" matchCase="false">
              <ogc:PropertyName>idass</ogc:PropertyName>
              <ogc:Literal>ar2-%</ogc:Literal>
            </ogc:PropertyIsLike>
          </ogc:Filter>
          <LineSymbolizer>
            <Stroke>
              <CssParameter name="stroke">#800080</CssParameter>
              <CssParameter name="stroke-width">2.0</CssParameter>
              <CssParameter name="stroke-opacity">1.0</CssParameter>
              <CssParameter name="stroke-linecap">square</CssParameter>
              <CssParameter name="stroke-linejoin">bevel</CssParameter>
            </Stroke>
          </LineSymbolizer>
          <PolygonSymbolizer>
            <Fill>
              <GraphicFill>
                <Graphic>
                  <Mark>
                    <WellKnownName>shape://slash</WellKnownName>
                    <Stroke>
                      <CssParameter name="stroke">#800080</CssParameter>
                      <CssParameter name="stroke-width">1</CssParameter>
                      <CssParameter name="stroke-opacity">1</CssParameter>
                    </Stroke>
                  </Mark>
                  <Size>8</Size>
                </Graphic>
              </GraphicFill>
            </Fill>
            <VendorOption name="graphic-margin">0</VendorOption>
          </PolygonSymbolizer>
        </Rule>
        <Rule>
          <Name>Magasins à poudre - zones de prohibition - AR3</Name>
          <ogc:Filter>
            <ogc:And>
              <ogc:PropertyIsLike wildCard="%" singleChar="_" escape="\" matchCase="false">
                <ogc:PropertyName>idass</ogc:PropertyName>
                <ogc:Literal>ar3-%</ogc:Literal>
              </ogc:PropertyIsLike>
              <ogc:Or>
                <ogc:PropertyIsEqualTo>
                  <ogc:PropertyName>typeass</ogc:PropertyName>
                  <ogc:Literal>Zone de prohibition 1</ogc:Literal>
                </ogc:PropertyIsEqualTo>
                <ogc:PropertyIsEqualTo>
                  <ogc:PropertyName>typeass</ogc:PropertyName>
                  <ogc:Literal>Zone de prohibition 2</ogc:Literal>
                </ogc:PropertyIsEqualTo>
              </ogc:Or>
            </ogc:And>
          </ogc:Filter>
          <LineSymbolizer>
            <Stroke>
              <CssParameter name="stroke">#800080</CssParameter>
              <CssParameter name="stroke-width">2.0</CssParameter>
              <CssParameter name="stroke-opacity">1.0</CssParameter>
              <CssParameter name="stroke-linecap">square</CssParameter>
              <CssParameter name="stroke-linejoin">bevel</CssParameter>
            </Stroke>
          </LineSymbolizer>
          <PolygonSymbolizer>
            <Fill>
              <GraphicFill>
                <Graphic>
                  <Mark>
                    <WellKnownName>shape://slash</WellKnownName>
                    <Stroke>
                      <CssParameter name="stroke">#800080</CssParameter>
                      <CssParameter name="stroke-width">1</CssParameter>
                      <CssParameter name="stroke-opacity">1</CssParameter>
                    </Stroke>
                  </Mark>
                  <Size>4</Size>
                </Graphic>
              </GraphicFill>
            </Fill>
            <VendorOption name="graphic-margin">0</VendorOption>
          </PolygonSymbolizer>
        </Rule>
        <Rule>
          <Name>Magasins à poudre - zones d'isolement - AR3</Name>
          <ogc:Filter>
            <ogc:And>
              <ogc:PropertyIsLike wildCard="%" singleChar="_" escape="\" matchCase="false">
                <ogc:PropertyName>idass</ogc:PropertyName>
                <ogc:Literal>ar3-%</ogc:Literal>
              </ogc:PropertyIsLike>
              <ogc:PropertyIsEqualTo>
                <ogc:PropertyName>typeass</ogc:PropertyName>
                <ogc:Literal>Zone d'isolement</ogc:Literal>
              </ogc:PropertyIsEqualTo>
            </ogc:And>
          </ogc:Filter>
          <LineSymbolizer>
            <Stroke>
              <CssParameter name="stroke">#800080</CssParameter>
              <CssParameter name="stroke-width">2.0</CssParameter>
              <CssParameter name="stroke-opacity">1.0</CssParameter>
              <CssParameter name="stroke-linecap">square</CssParameter>
              <CssParameter name="stroke-linejoin">bevel</CssParameter>
            </Stroke>
          </LineSymbolizer>
          <PolygonSymbolizer>
            <Fill>
              <GraphicFill>
                <Graphic>
                  <Mark>
                    <WellKnownName>shape://slash</WellKnownName>
                    <Stroke>
                      <CssParameter name="stroke">#800080</CssParameter>
                      <CssParameter name="stroke-width">1</CssParameter>
                      <CssParameter name="stroke-opacity">1</CssParameter>
                    </Stroke>
                  </Mark>
                  <Size>12</Size>
                </Graphic>
              </GraphicFill>
            </Fill>
            <VendorOption name="graphic-margin">0</VendorOption>
          </PolygonSymbolizer>
        </Rule>
        <Rule>
          <Name>Terrains d'atterrissage militaires - AR4</Name>
          <ogc:Filter>
            <ogc:PropertyIsLike wildCard="%" singleChar="_" escape="\" matchCase="false">
              <ogc:PropertyName>idass</ogc:PropertyName>
              <ogc:Literal>ar4-%</ogc:Literal>
            </ogc:PropertyIsLike>
          </ogc:Filter>
          <LineSymbolizer>
            <Stroke>
              <CssParameter name="stroke">#800080</CssParameter>
              <CssParameter name="stroke-width">2.0</CssParameter>
              <CssParameter name="stroke-opacity">1.0</CssParameter>
              <CssParameter name="stroke-linecap">square</CssParameter>
              <CssParameter name="stroke-linejoin">bevel</CssParameter>
            </Stroke>
          </LineSymbolizer>
        </Rule>
        <Rule>
          <Name>Fortifications et ouvrages militaires - AR5</Name>
          <ogc:Filter>
            <ogc:PropertyIsLike wildCard="%" singleChar="_" escape="\" matchCase="false">
              <ogc:PropertyName>idass</ogc:PropertyName>
              <ogc:Literal>ar5-%</ogc:Literal>
            </ogc:PropertyIsLike>
          </ogc:Filter>
          <LineSymbolizer>
            <Stroke>
              <CssParameter name="stroke">#800080</CssParameter>
              <CssParameter name="stroke-width">2.0</CssParameter>
              <CssParameter name="stroke-opacity">1.0</CssParameter>
              <CssParameter name="stroke-linecap">square</CssParameter>
              <CssParameter name="stroke-linejoin">bevel</CssParameter>
            </Stroke>
          </LineSymbolizer>
          <PolygonSymbolizer>
            <Fill>
              <GraphicFill>
                <Graphic>
                  <Mark>
                    <WellKnownName>shape://slash</WellKnownName>
                    <Stroke>
                      <CssParameter name="stroke">#800080</CssParameter>
                      <CssParameter name="stroke-width">1</CssParameter>
                      <CssParameter name="stroke-opacity">1</CssParameter>
                    </Stroke>
                  </Mark>
                  <Size>8</Size>
                </Graphic>
              </GraphicFill>
            </Fill>
            <VendorOption name="graphic-margin">0</VendorOption>
          </PolygonSymbolizer>
        </Rule>
        <Rule>
          <Name>Champs de tir - AR6</Name>
          <ogc:Filter>
            <ogc:PropertyIsLike wildCard="%" singleChar="_" escape="\" matchCase="false">
              <ogc:PropertyName>idass</ogc:PropertyName>
              <ogc:Literal>ar6-%</ogc:Literal>
            </ogc:PropertyIsLike>
          </ogc:Filter>
          <LineSymbolizer>
            <Stroke>
              <CssParameter name="stroke">#800080</CssParameter>
              <CssParameter name="stroke-width">2.0</CssParameter>
              <CssParameter name="stroke-opacity">1.0</CssParameter>
              <CssParameter name="stroke-linecap">square</CssParameter>
              <CssParameter name="stroke-linejoin">bevel</CssParameter>
            </Stroke>
          </LineSymbolizer>
          <PolygonSymbolizer>
            <Fill>
              <GraphicFill>
                <Graphic>
                  <Mark>
                    <WellKnownName>shape://backslash</WellKnownName>
                    <Stroke>
                      <CssParameter name="stroke">#800080</CssParameter>
                      <CssParameter name="stroke-width">1</CssParameter>
                      <CssParameter name="stroke-opacity">1</CssParameter>
                    </Stroke>
                  </Mark>
                  <Size>8</Size>
                </Graphic>
              </GraphicFill>
            </Fill>
            <VendorOption name="graphic-margin">0</VendorOption>
          </PolygonSymbolizer>
        </Rule>
        <Rule>
          <Name>Protection des eaux - périmètre de protection immédiate - AS1</Name>
          <ogc:Filter>
            <ogc:And>
              <ogc:PropertyIsLike wildCard="%" singleChar="_" escape="\" matchCase="false">
                <ogc:PropertyName>idass</ogc:PropertyName>
                <ogc:Literal>as1-%</ogc:Literal>
              </ogc:PropertyIsLike>
              <ogc:PropertyIsEqualTo>
                <ogc:PropertyName>typeass</ogc:PropertyName>
                <ogc:Literal>Périmètre de protection immédiate</ogc:Literal>
              </ogc:PropertyIsEqualTo>
            </ogc:And>
          </ogc:Filter>
          <LineSymbolizer>
            <Stroke>
              <CssParameter name="stroke">#00c0c0</CssParameter>
              <CssParameter name="stroke-width">0.5</CssParameter>
              <CssParameter name="stroke-opacity">1.0</CssParameter>
              <CssParameter name="stroke-linecap">square</CssParameter>
              <CssParameter name="stroke-linejoin">bevel</CssParameter>
            </Stroke>
          </LineSymbolizer>
          <PolygonSymbolizer>
            <Fill>
              <GraphicFill>
                <Graphic>
                  <Mark>
                    <WellKnownName>shape://slash</WellKnownName>
                    <Stroke>
                      <CssParameter name="stroke">#00aaff</CssParameter>
                      <CssParameter name="stroke-width">0.7</CssParameter>
                      <CssParameter name="stroke-opacity">1</CssParameter>
                    </Stroke>
                  </Mark>
                  <Size>12</Size>
                </Graphic>
              </GraphicFill>
            </Fill>
            <VendorOption name="graphic-margin">0</VendorOption>
          </PolygonSymbolizer>
        </Rule>
        <Rule>
          <Name>Protection des eaux - périmètre de protection rapprochée - AS1</Name>
          <ogc:Filter>
            <ogc:And>
              <ogc:PropertyIsLike wildCard="%" singleChar="_" escape="\" matchCase="false">
                <ogc:PropertyName>idass</ogc:PropertyName>
                <ogc:Literal>as1-%</ogc:Literal>
              </ogc:PropertyIsLike>
              <ogc:PropertyIsEqualTo>
                <ogc:PropertyName>typeass</ogc:PropertyName>
                <ogc:Literal>Périmètre de protection rapprochée</ogc:Literal>
              </ogc:PropertyIsEqualTo>
            </ogc:And>
          </ogc:Filter>
          <LineSymbolizer>
            <Stroke>
              <CssParameter name="stroke">#00aaff</CssParameter>
              <CssParameter name="stroke-width">0.5</CssParameter>
              <CssParameter name="stroke-opacity">1.0</CssParameter>
              <CssParameter name="stroke-linecap">square</CssParameter>
              <CssParameter name="stroke-linejoin">bevel</CssParameter>
            </Stroke>
          </LineSymbolizer>
          <PolygonSymbolizer>
            <Fill>
              <GraphicFill>
                <Graphic>
                  <Mark>
                    <WellKnownName>shape://slash</WellKnownName>
                    <Stroke>
                      <CssParameter name="stroke">#00aaff</CssParameter>
                      <CssParameter name="stroke-width">0.7</CssParameter>
                      <CssParameter name="stroke-opacity">1</CssParameter>
                    </Stroke>
                  </Mark>
                  <Size>6</Size>
                </Graphic>
              </GraphicFill>
            </Fill>
            <VendorOption name="graphic-margin">0</VendorOption>
          </PolygonSymbolizer>
        </Rule>
        <Rule>
          <Name>Protection des eaux - périmètre de protection éloignée - AS1</Name>
          <ogc:Filter>
            <ogc:And>
              <ogc:PropertyIsLike wildCard="%" singleChar="_" escape="\" matchCase="false">
                <ogc:PropertyName>idass</ogc:PropertyName>
                <ogc:Literal>as1-%</ogc:Literal>
              </ogc:PropertyIsLike>
              <ogc:PropertyIsEqualTo>
                <ogc:PropertyName>typeass</ogc:PropertyName>
                <ogc:Literal>Périmètre de protection éloignée</ogc:Literal>
              </ogc:PropertyIsEqualTo>
            </ogc:And>
          </ogc:Filter>
          <LineSymbolizer>
            <Stroke>
              <CssParameter name="stroke">#00aaff</CssParameter>
              <CssParameter name="stroke-width">0.5</CssParameter>
              <CssParameter name="stroke-opacity">1.0</CssParameter>
              <CssParameter name="stroke-linecap">square</CssParameter>
              <CssParameter name="stroke-linejoin">bevel</CssParameter>
            </Stroke>
          </LineSymbolizer>
          <PolygonSymbolizer>
            <Fill>
              <GraphicFill>
                <Graphic>
                  <Mark>
                    <WellKnownName>shape://slash</WellKnownName>
                    <Stroke>
                      <CssParameter name="stroke">#00aaff</CssParameter>
                      <CssParameter name="stroke-width">0.4</CssParameter>
                      <CssParameter name="stroke-opacity">1</CssParameter>
                    </Stroke>
                  </Mark>
                  <Size>12</Size>
                </Graphic>
              </GraphicFill>
            </Fill>
            <VendorOption name="graphic-margin">0</VendorOption>
          </PolygonSymbolizer>
        </Rule>
        <Rule>
          <Name>Protection des eaux - périmètre de protection eau minérale - AS1</Name>
          <ogc:Filter>
            <ogc:And>
              <ogc:PropertyIsLike wildCard="%" singleChar="_" escape="\" matchCase="false">
                <ogc:PropertyName>idass</ogc:PropertyName>
                <ogc:Literal>as1-%</ogc:Literal>
              </ogc:PropertyIsLike>
              <ogc:PropertyIsEqualTo>
                <ogc:PropertyName>typeass</ogc:PropertyName>
                <ogc:Literal>Périmètre de protection eau minérale</ogc:Literal>
              </ogc:PropertyIsEqualTo>
            </ogc:And>
          </ogc:Filter>
          <LineSymbolizer>
            <Stroke>
              <CssParameter name="stroke">#00aaff</CssParameter>
              <CssParameter name="stroke-width">0.5</CssParameter>
              <CssParameter name="stroke-opacity">1.0</CssParameter>
              <CssParameter name="stroke-linecap">square</CssParameter>
              <CssParameter name="stroke-linejoin">bevel</CssParameter>
            </Stroke>
          </LineSymbolizer>
          <PolygonSymbolizer>
            <Fill>
              <GraphicFill>
                <Graphic>
                  <Mark>
                    <WellKnownName>shape://slash</WellKnownName>
                    <Stroke>
                      <CssParameter name="stroke">#00aaff</CssParameter>
                      <CssParameter name="stroke-width">0.7</CssParameter>
                      <CssParameter name="stroke-opacity">1</CssParameter>
                    </Stroke>
                  </Mark>
                  <Size>12</Size>
                </Graphic>
              </GraphicFill>
            </Fill>
            <VendorOption name="graphic-margin">0</VendorOption>
          </PolygonSymbolizer>
        </Rule>
        <Rule>
          <Name>Établissements conchylicoles - AS2</Name>
          <ogc:Filter>
            <ogc:PropertyIsLike wildCard="%" singleChar="_" escape="\" matchCase="false">
              <ogc:PropertyName>idass</ogc:PropertyName>
              <ogc:Literal>as2-%</ogc:Literal>
            </ogc:PropertyIsLike>
          </ogc:Filter>
          <LineSymbolizer>
            <Stroke>
              <CssParameter name="stroke">#00c0c0</CssParameter>
              <CssParameter name="stroke-width">2.0</CssParameter>
              <CssParameter name="stroke-opacity">1.0</CssParameter>
              <CssParameter name="stroke-linecap">square</CssParameter>
              <CssParameter name="stroke-linejoin">bevel</CssParameter>
            </Stroke>
          </LineSymbolizer>
          <PolygonSymbolizer>
            <Fill>
              <GraphicFill>
                <Graphic>
                  <Mark>
                    <WellKnownName>shape://slash</WellKnownName>
                    <Stroke>
                      <CssParameter name="stroke">#00c0c0</CssParameter>
                      <CssParameter name="stroke-width">1</CssParameter>
                      <CssParameter name="stroke-opacity">1</CssParameter>
                    </Stroke>
                  </Mark>
                  <Size>8</Size>
                </Graphic>
              </GraphicFill>
            </Fill>
            <VendorOption name="graphic-margin">0</VendorOption>
          </PolygonSymbolizer>
        </Rule>
        <Rule>
          <Name>Loire et ses affluents - EL2bis</Name>
          <ogc:Filter>
            <ogc:PropertyIsLike wildCard="%" singleChar="_" escape="\" matchCase="false">
              <ogc:PropertyName>idass</ogc:PropertyName>
              <ogc:Literal>el2bis-%</ogc:Literal>
            </ogc:PropertyIsLike>
          </ogc:Filter>
          <LineSymbolizer>
            <Stroke>
              <CssParameter name="stroke">#000000</CssParameter>
              <CssParameter name="stroke-width">2.0</CssParameter>
              <CssParameter name="stroke-opacity">1.0</CssParameter>
              <CssParameter name="stroke-linecap">square</CssParameter>
              <CssParameter name="stroke-linejoin">bevel</CssParameter>
            </Stroke>
          </LineSymbolizer>
          <PolygonSymbolizer>
            <Fill>
              <GraphicFill>
                <Graphic>
                  <Mark>
                    <WellKnownName>circle</WellKnownName>
                    <Fill>
                      <CssParameter name="fill">#000000</CssParameter>
                      <CssParameter name="fill-opacity">1.0</CssParameter>
                    </Fill>
                    <Stroke>
                      <CssParameter name="stroke">#000000</CssParameter>
                      <CssParameter name="stroke-width">0.0</CssParameter>
                      <CssParameter name="stroke-opacity">0.0</CssParameter>
                    </Stroke>
                  </Mark>
                  <Size>2.0</Size>
                  <Rotation>0.0</Rotation>
                </Graphic>
              </GraphicFill>
            </Fill>
            <VendorOption name="graphic-margin">0</VendorOption>
          </PolygonSymbolizer>
        </Rule>
        <Rule>
          <Name>Cours d’eau - Halage - EL3</Name>
          <ogc:Filter>
            <ogc:And>
              <ogc:PropertyIsLike wildCard="%" singleChar="_" escape="\" matchCase="false">
                <ogc:PropertyName>idass</ogc:PropertyName>
                <ogc:Literal>el3-%</ogc:Literal>
              </ogc:PropertyIsLike>
              <ogc:PropertyIsEqualTo>
                <ogc:PropertyName>typeass</ogc:PropertyName>
                <ogc:Literal>Halage</ogc:Literal>
              </ogc:PropertyIsEqualTo>
            </ogc:And>
          </ogc:Filter>
          <LineSymbolizer>
            <Stroke>
              <CssParameter name="stroke">#000000</CssParameter>
              <CssParameter name="stroke-width">2.0</CssParameter>
              <CssParameter name="stroke-opacity">1.0</CssParameter>
              <CssParameter name="stroke-linecap">square</CssParameter>
              <CssParameter name="stroke-linejoin">bevel</CssParameter>
            </Stroke>
          </LineSymbolizer>
        </Rule>
        <Rule>
          <Name>Cours d’eau - Marchepied - EL3</Name>
          <ogc:Filter>
            <ogc:And>
              <ogc:PropertyIsLike wildCard="%" singleChar="_" escape="\" matchCase="false">
                <ogc:PropertyName>idass</ogc:PropertyName>
                <ogc:Literal>el3-%</ogc:Literal>
              </ogc:PropertyIsLike>
              <ogc:PropertyIsEqualTo>
                <ogc:PropertyName>typeass</ogc:PropertyName>
                <ogc:Literal>Marchepied</ogc:Literal>
              </ogc:PropertyIsEqualTo>
            </ogc:And>
          </ogc:Filter>
          <LineSymbolizer>
            <Stroke>
              <CssParameter name="stroke">#000000</CssParameter>
              <CssParameter name="stroke-width">2.0</CssParameter>
              <CssParameter name="stroke-opacity">1.0</CssParameter>
              <CssParameter name="stroke-linecap">square</CssParameter>
              <CssParameter name="stroke-linejoin">bevel</CssParameter>
            </Stroke>
          </LineSymbolizer>
        </Rule>
        <Rule>
          <Name>Développement et protection des montagnes - EL4</Name>
          <ogc:Filter>
            <ogc:PropertyIsLike wildCard="%" singleChar="_" escape="\" matchCase="false">
              <ogc:PropertyName>idass</ogc:PropertyName>
              <ogc:Literal>el4-%</ogc:Literal>
            </ogc:PropertyIsLike>
          </ogc:Filter>
          <LineSymbolizer>
            <Stroke>
              <CssParameter name="stroke">#000000</CssParameter>
              <CssParameter name="stroke-width">1.0</CssParameter>
              <CssParameter name="stroke-opacity">1.0</CssParameter>
              <CssParameter name="stroke-linecap">square</CssParameter>
              <CssParameter name="stroke-linejoin">bevel</CssParameter>
            </Stroke>
          </LineSymbolizer>
          <PolygonSymbolizer>
            <Fill>
              <GraphicFill>
                <Graphic>
                  <Mark>
                    <WellKnownName>circle</WellKnownName>
                    <Fill>
                      <CssParameter name="fill">#000000</CssParameter>
                      <CssParameter name="fill-opacity">0.0</CssParameter>
                    </Fill>
                    <Stroke>
                      <CssParameter name="stroke">#000000</CssParameter>
                      <CssParameter name="stroke-width">0.0</CssParameter>
                      <CssParameter name="stroke-opacity">0.0</CssParameter>
                    </Stroke>
                  </Mark>
                  <Size>7.0</Size>
                  <Rotation>0.0</Rotation>
                </Graphic>
              </GraphicFill>
            </Fill>
            <VendorOption name="graphic-margin">0</VendorOption>
          </PolygonSymbolizer>
        </Rule>
        <Rule>
          <Name>Visibilité sur les voies publiques - EL5</Name>
          <ogc:Filter>
            <ogc:PropertyIsLike wildCard="%" singleChar="_" escape="\" matchCase="false">
              <ogc:PropertyName>idass</ogc:PropertyName>
              <ogc:Literal>el5-%</ogc:Literal>
            </ogc:PropertyIsLike>
          </ogc:Filter>
          <LineSymbolizer>
            <Stroke>
              <CssParameter name="stroke">#000000</CssParameter>
              <CssParameter name="stroke-width">2.0</CssParameter>
              <CssParameter name="stroke-opacity">1.0</CssParameter>
              <CssParameter name="stroke-linecap">square</CssParameter>
              <CssParameter name="stroke-linejoin">bevel</CssParameter>
            </Stroke>
          </LineSymbolizer>
        </Rule>
        <Rule>
          <Name>Réserve de terrains nécessaires aux routes - EL6</Name>
          <ogc:Filter>
            <ogc:PropertyIsLike wildCard="%" singleChar="_" escape="\" matchCase="false">
              <ogc:PropertyName>idass</ogc:PropertyName>
              <ogc:Literal>el6-%</ogc:Literal>
            </ogc:PropertyIsLike>
          </ogc:Filter>
          <LineSymbolizer>
            <Stroke>
              <CssParameter name="stroke">#000000</CssParameter>
              <CssParameter name="stroke-width">1.0</CssParameter>
              <CssParameter name="stroke-opacity">1.0</CssParameter>
              <CssParameter name="stroke-linecap">square</CssParameter>
              <CssParameter name="stroke-linejoin">bevel</CssParameter>
            </Stroke>
          </LineSymbolizer>
        </Rule>
        <Rule>
          <Name>Alignement des voies publiques - EL7</Name>
          <ogc:Filter>
            <ogc:PropertyIsLike wildCard="%" singleChar="_" escape="\" matchCase="false">
              <ogc:PropertyName>idass</ogc:PropertyName>
              <ogc:Literal>el7-%</ogc:Literal>
            </ogc:PropertyIsLike>
          </ogc:Filter>
          <LineSymbolizer>
            <Stroke>
              <CssParameter name="stroke">#000000</CssParameter>
              <CssParameter name="stroke-width">1.0</CssParameter>
              <CssParameter name="stroke-opacity">1.0</CssParameter>
              <CssParameter name="stroke-linecap">square</CssParameter>
              <CssParameter name="stroke-linejoin">bevel</CssParameter>
            </Stroke>
          </LineSymbolizer>
          <PolygonSymbolizer>
            <Fill>
              <GraphicFill>
                <Graphic>
                  <Mark>
                    <WellKnownName>shape://backslash</WellKnownName>
                    <Stroke>
                      <CssParameter name="stroke">#000000</CssParameter>
                      <CssParameter name="stroke-width">1</CssParameter>
                      <CssParameter name="stroke-opacity">1</CssParameter>
                    </Stroke>
                  </Mark>
                  <Size>3</Size>
                </Graphic>
              </GraphicFill>
            </Fill>
            <VendorOption name="graphic-margin">0</VendorOption>
          </PolygonSymbolizer>
        </Rule>
        <Rule>
          <Name>Champs de vue pour la navigation maritime - EL8</Name>
          <ogc:Filter>
            <ogc:PropertyIsLike wildCard="%" singleChar="_" escape="\" matchCase="false">
              <ogc:PropertyName>idass</ogc:PropertyName>
              <ogc:Literal>el8-%</ogc:Literal>
            </ogc:PropertyIsLike>
          </ogc:Filter>
          <LineSymbolizer>
            <Stroke>
              <CssParameter name="stroke">#000000</CssParameter>
              <CssParameter name="stroke-width">1.5</CssParameter>
              <CssParameter name="stroke-opacity">1.0</CssParameter>
              <CssParameter name="stroke-linecap">square</CssParameter>
              <CssParameter name="stroke-linejoin">bevel</CssParameter>
            </Stroke>
          </LineSymbolizer>
          <PolygonSymbolizer>
            <Fill>
              <GraphicFill>
                <Graphic>
                  <Mark>
                    <WellKnownName>shape://slash</WellKnownName>
                    <Stroke>
                      <CssParameter name="stroke">#000000</CssParameter>
                      <CssParameter name="stroke-width">1</CssParameter>
                      <CssParameter name="stroke-opacity">1</CssParameter>
                    </Stroke>
                  </Mark>
                  <Size>20</Size>
                </Graphic>
              </GraphicFill>
            </Fill>
            <VendorOption name="graphic-margin">0</VendorOption>
          </PolygonSymbolizer>
        </Rule>
        <Rule>
          <Name>Littoral - EL9</Name>
          <ogc:Filter>
            <ogc:PropertyIsLike wildCard="%" singleChar="_" escape="\" matchCase="false">
              <ogc:PropertyName>idass</ogc:PropertyName>
              <ogc:Literal>el9-%</ogc:Literal>
            </ogc:PropertyIsLike>
          </ogc:Filter>
          <LineSymbolizer>
            <Stroke>
              <CssParameter name="stroke">#000000</CssParameter>
              <CssParameter name="stroke-width">2.0</CssParameter>
              <CssParameter name="stroke-opacity">1.0</CssParameter>
              <CssParameter name="stroke-linecap">square</CssParameter>
              <CssParameter name="stroke-linejoin">bevel</CssParameter>
            </Stroke>
          </LineSymbolizer>
          <LineSymbolizer>
            <Stroke>
              <CssParameter name="stroke">#ffff00</CssParameter>
              <CssParameter name="stroke-width">1.0</CssParameter>
              <CssParameter name="stroke-opacity">1.0</CssParameter>
              <CssParameter name="stroke-linecap">square</CssParameter>
              <CssParameter name="stroke-linejoin">bevel</CssParameter>
            </Stroke>
          </LineSymbolizer>
        </Rule>
        <Rule>
          <Name>Parcs nationaux - EL10</Name>
          <ogc:Filter>
            <ogc:PropertyIsLike wildCard="%" singleChar="_" escape="\" matchCase="false">
              <ogc:PropertyName>idass</ogc:PropertyName>
              <ogc:Literal>el10-%</ogc:Literal>
            </ogc:PropertyIsLike>
          </ogc:Filter>
          <LineSymbolizer>
            <Stroke>
              <CssParameter name="stroke">#000000</CssParameter>
              <CssParameter name="stroke-width">1.2</CssParameter>
              <CssParameter name="stroke-opacity">1.0</CssParameter>
              <CssParameter name="stroke-linecap">square</CssParameter>
              <CssParameter name="stroke-linejoin">bevel</CssParameter>
            </Stroke>
          </LineSymbolizer>
          <PolygonSymbolizer>
            <Fill>
              <GraphicFill>
                <Graphic>
                  <Mark>
                    <WellKnownName>square</WellKnownName>
                    <Fill>
                      <CssParameter name="fill">#000000</CssParameter>
                      <CssParameter name="fill-opacity">1.0</CssParameter>
                    </Fill>
                    <Stroke>
                      <CssParameter name="stroke">#000000</CssParameter>
                      <CssParameter name="stroke-width">0.0</CssParameter>
                      <CssParameter name="stroke-opacity">0.0</CssParameter>
                    </Stroke>
                  </Mark>
                  <Size>2.0</Size>
                  <Rotation>0.0</Rotation>
                </Graphic>
              </GraphicFill>
            </Fill>
            <VendorOption name="graphic-margin">0</VendorOption>
          </PolygonSymbolizer>
        </Rule>
        <Rule>
          <Name>Interdictions d'accès en bord de routes - EL11</Name>
          <ogc:Filter>
            <ogc:PropertyIsLike wildCard="%" singleChar="_" escape="\" matchCase="false">
              <ogc:PropertyName>idass</ogc:PropertyName>
              <ogc:Literal>el11-%</ogc:Literal>
            </ogc:PropertyIsLike>
          </ogc:Filter>
          <LineSymbolizer>
            <Stroke>
              <CssParameter name="stroke">#000000</CssParameter>
              <CssParameter name="stroke-width">3.0</CssParameter>
              <CssParameter name="stroke-opacity">1.0</CssParameter>
              <CssParameter name="stroke-linecap">square</CssParameter>
              <CssParameter name="stroke-linejoin">bevel</CssParameter>
            </Stroke>
          </LineSymbolizer>
          <PolygonSymbolizer>
            <Fill>
              <GraphicFill>
                <Graphic>
                  <Mark>
                    <WellKnownName>shape://vertline</WellKnownName>
                    <Stroke>
                      <CssParameter name="stroke">#000000</CssParameter>
                      <CssParameter name="stroke-width">1</CssParameter>
                      <CssParameter name="stroke-opacity">1</CssParameter>
                    </Stroke>
                  </Mark>
                  <Size>5</Size>
                </Graphic>
              </GraphicFill>
            </Fill>
            <VendorOption name="graphic-margin">0</VendorOption>
          </PolygonSymbolizer>
        </Rule>
        <Rule>
          <Name>Maitrise des canalisations de gaz, d’hydrocarbures et de produits chimiques - I1 </Name>
          <ogc:Filter>
            <ogc:PropertyIsLike wildCard="%" singleChar="_" escape="\" matchCase="false">
              <ogc:PropertyName>idass</ogc:PropertyName>
              <ogc:Literal>i1-%</ogc:Literal>
            </ogc:PropertyIsLike>
          </ogc:Filter>
          <LineSymbolizer>
            <Stroke>
              <CssParameter name="stroke">#fa00fa</CssParameter>
              <CssParameter name="stroke-width">1.5</CssParameter>
              <CssParameter name="stroke-opacity">1.0</CssParameter>
              <CssParameter name="stroke-linecap">square</CssParameter>
              <CssParameter name="stroke-linejoin">bevel</CssParameter>
            </Stroke>
          </LineSymbolizer>
        </Rule>
        <Rule>
          <Name>Energie hydraulique - I2</Name>
          <ogc:Filter>
            <ogc:PropertyIsLike wildCard="%" singleChar="_" escape="\" matchCase="false">
              <ogc:PropertyName>idass</ogc:PropertyName>
              <ogc:Literal>i2-%</ogc:Literal>
            </ogc:PropertyIsLike>
          </ogc:Filter>
          <LineSymbolizer>
            <Stroke>
              <CssParameter name="stroke">#fa00fa</CssParameter>
              <CssParameter name="stroke-width">1.5</CssParameter>
              <CssParameter name="stroke-opacity">1.0</CssParameter>
              <CssParameter name="stroke-linecap">square</CssParameter>
              <CssParameter name="stroke-linejoin">bevel</CssParameter>
            </Stroke>
          </LineSymbolizer>
          <PolygonSymbolizer>
            <Fill>
              <GraphicFill>
                <Graphic>
                  <Mark>
                    <WellKnownName>shape://slash</WellKnownName>
                    <Stroke>
                      <CssParameter name="stroke">#fa00fa</CssParameter>
                      <CssParameter name="stroke-width">0.8</CssParameter>
                      <CssParameter name="stroke-opacity">1</CssParameter>
                    </Stroke>
                  </Mark>
                  <Size>5</Size>
                </Graphic>
              </GraphicFill>
            </Fill>
            <VendorOption name="graphic-margin">0</VendorOption>
          </PolygonSymbolizer>
        </Rule>
        <Rule>
          <Name>Canalisations de transport de gaz, hydrocarbures et produits chimiques - I3</Name>
          <ogc:Filter>
            <ogc:And>
              <ogc:PropertyIsLike wildCard="%" singleChar="_" escape="\" matchCase="false">
                <ogc:PropertyName>idass</ogc:PropertyName>
                <ogc:Literal>i3-%</ogc:Literal>
              </ogc:PropertyIsLike>
              <ogc:PropertyIsEqualTo>
                <ogc:PropertyName>typeass</ogc:PropertyName>
                <ogc:Literal>Zone de protection</ogc:Literal>
              </ogc:PropertyIsEqualTo>
            </ogc:And>
          </ogc:Filter>
          <LineSymbolizer>
            <Stroke>
              <CssParameter name="stroke">#fa00fa</CssParameter>
              <CssParameter name="stroke-width">1.5</CssParameter>
              <CssParameter name="stroke-opacity">1.0</CssParameter>
              <CssParameter name="stroke-linecap">square</CssParameter>
              <CssParameter name="stroke-linejoin">bevel</CssParameter>
            </Stroke>
          </LineSymbolizer>
        </Rule>
        <Rule>
          <Name>Canalisations de transport de gaz, hydrocarbures et produits chimiques - I3</Name>
          <ogc:Filter>
            <ogc:And>
              <ogc:PropertyIsLike wildCard="%" singleChar="_" escape="\" matchCase="false">
                <ogc:PropertyName>idass</ogc:PropertyName>
                <ogc:Literal>i3-%</ogc:Literal>
              </ogc:PropertyIsLike>
              <ogc:PropertyIsEqualTo>
                <ogc:PropertyName>typeass</ogc:PropertyName>
                <ogc:Literal>Zone de passage</ogc:Literal>
              </ogc:PropertyIsEqualTo>
            </ogc:And>
          </ogc:Filter>
          <LineSymbolizer>
            <Stroke>
              <CssParameter name="stroke">#fa00fa</CssParameter>
              <CssParameter name="stroke-width">1.5</CssParameter>
              <CssParameter name="stroke-opacity">1.0</CssParameter>
              <CssParameter name="stroke-linecap">square</CssParameter>
              <CssParameter name="stroke-linejoin">bevel</CssParameter>
            </Stroke>
          </LineSymbolizer>
          <PolygonSymbolizer>
            <Fill>
              <GraphicFill>
                <Graphic>
                  <Mark>
                    <WellKnownName>square</WellKnownName>
                    <Fill>
                      <CssParameter name="fill">#fa00fa</CssParameter>
                      <CssParameter name="fill-opacity">1.0</CssParameter>
                    </Fill>
                    <Stroke>
                      <CssParameter name="stroke">#fa00fa</CssParameter>
                      <CssParameter name="stroke-width">1.0</CssParameter>
                      <CssParameter name="stroke-opacity">1.0</CssParameter>
                    </Stroke>
                  </Mark>
                  <Size>8.0</Size>
                  <Rotation>0.0</Rotation>
                </Graphic>
              </GraphicFill>
            </Fill>
            <VendorOption name="graphic-margin">0</VendorOption>
          </PolygonSymbolizer>
        </Rule>
        <Rule>
          <Name>Canalisations électriques - I4</Name>
          <ogc:Filter>
            <ogc:And>
              <ogc:PropertyIsLike wildCard="%" singleChar="_" escape="\" matchCase="false">
                <ogc:PropertyName>idass</ogc:PropertyName>
                <ogc:Literal>i4-%</ogc:Literal>
              </ogc:PropertyIsLike>
              <ogc:PropertyIsEqualTo>
                <ogc:PropertyName>type</ogc:PropertyName>
                <ogc:Literal>Aérien</ogc:Literal>
              </ogc:PropertyIsEqualTo>
            </ogc:And>
          </ogc:Filter>
          <LineSymbolizer>
            <Stroke>
              <CssParameter name="stroke">#fa00fa</CssParameter>
              <CssParameter name="stroke-width">1.5</CssParameter>
              <CssParameter name="stroke-opacity">1.0</CssParameter>
              <CssParameter name="stroke-linecap">square</CssParameter>
              <CssParameter name="stroke-linejoin">bevel</CssParameter>
            </Stroke>
          </LineSymbolizer>
        </Rule>
        <Rule>
          <Name>Canalisation électriques - I4</Name>
          <ogc:Filter>
            <ogc:And>
              <ogc:PropertyIsLike wildCard="%" singleChar="_" escape="\" matchCase="false">
                <ogc:PropertyName>idass</ogc:PropertyName>
                <ogc:Literal>i4-%</ogc:Literal>
              </ogc:PropertyIsLike>
              <ogc:PropertyIsEqualTo>
                <ogc:PropertyName>type</ogc:PropertyName>
                <ogc:Literal>Souterrain</ogc:Literal>
              </ogc:PropertyIsEqualTo>
            </ogc:And>
          </ogc:Filter>
          <LineSymbolizer>
            <Stroke>
              <CssParameter name="stroke">#fa00fa</CssParameter>
              <CssParameter name="stroke-width">1.5</CssParameter>
              <CssParameter name="stroke-opacity">1.0</CssParameter>
              <CssParameter name="stroke-linecap">square</CssParameter>
              <CssParameter name="stroke-linejoin">bevel</CssParameter>
            </Stroke>
          </LineSymbolizer>
        </Rule>
        <Rule>
          <Name>Canalisations de distribution de gaz - I5</Name>
          <ogc:Filter>
            <ogc:PropertyIsLike wildCard="%" singleChar="_" escape="\" matchCase="false">
              <ogc:PropertyName>idass</ogc:PropertyName>
              <ogc:Literal>i5-%</ogc:Literal>
            </ogc:PropertyIsLike>
          </ogc:Filter>
          <LineSymbolizer>
            <Stroke>
              <CssParameter name="stroke">#fa00fa</CssParameter>
              <CssParameter name="stroke-width">1.5</CssParameter>
              <CssParameter name="stroke-opacity">1.0</CssParameter>
              <CssParameter name="stroke-linecap">square</CssParameter>
              <CssParameter name="stroke-linejoin">bevel</CssParameter>
            </Stroke>
          </LineSymbolizer>
          <PolygonSymbolizer>
            <Fill>
              <GraphicFill>
                <Graphic>
                  <Mark>
                    <WellKnownName>square</WellKnownName>
                    <Fill>
                      <CssParameter name="fill">#fa00fa</CssParameter>
                      <CssParameter name="fill-opacity">1.0</CssParameter>
                    </Fill>
                    <Stroke>
                      <CssParameter name="stroke">#fa00fa</CssParameter>
                      <CssParameter name="stroke-width">1.0</CssParameter>
                      <CssParameter name="stroke-opacity">1.0</CssParameter>
                    </Stroke>
                  </Mark>
                  <Size>8.0</Size>
                  <Rotation>0.0</Rotation>
                </Graphic>
              </GraphicFill>
            </Fill>
            <VendorOption name="graphic-margin">0</VendorOption>
          </PolygonSymbolizer>
        </Rule>
        <Rule>
          <Name>Mines et carrières - I6</Name>
          <ogc:Filter>
            <ogc:PropertyIsLike wildCard="%" singleChar="_" escape="\" matchCase="false">
              <ogc:PropertyName>idass</ogc:PropertyName>
              <ogc:Literal>i6-%</ogc:Literal>
            </ogc:PropertyIsLike>
          </ogc:Filter>
          <LineSymbolizer>
            <Stroke>
              <CssParameter name="stroke">#fa00fa</CssParameter>
              <CssParameter name="stroke-width">1.5</CssParameter>
              <CssParameter name="stroke-opacity">1.0</CssParameter>
              <CssParameter name="stroke-linecap">square</CssParameter>
              <CssParameter name="stroke-linejoin">bevel</CssParameter>
            </Stroke>
          </LineSymbolizer>
        </Rule>
        <Rule>
          <Name>Stockage souterrain de gaz, hydrocarbures et produits chimiques - I7</Name>
          <ogc:Filter>
            <ogc:PropertyIsLike wildCard="%" singleChar="_" escape="\" matchCase="false">
              <ogc:PropertyName>idass</ogc:PropertyName>
              <ogc:Literal>i7-%</ogc:Literal>
            </ogc:PropertyIsLike>
          </ogc:Filter>
          <LineSymbolizer>
            <Stroke>
              <CssParameter name="stroke">#fa00fa</CssParameter>
              <CssParameter name="stroke-width">1.5</CssParameter>
              <CssParameter name="stroke-opacity">1.0</CssParameter>
              <CssParameter name="stroke-linecap">square</CssParameter>
              <CssParameter name="stroke-linejoin">bevel</CssParameter>
            </Stroke>
          </LineSymbolizer>
          <PolygonSymbolizer>
            <Fill>
              <GraphicFill>
                <Graphic>
                  <Mark>
                    <WellKnownName>shape://vertline</WellKnownName>
                    <Stroke>
                      <CssParameter name="stroke">#fa00fa</CssParameter>
                      <CssParameter name="stroke-width">1</CssParameter>
                      <CssParameter name="stroke-opacity">1</CssParameter>
                    </Stroke>
                  </Mark>
                  <Size>15</Size>
                </Graphic>
              </GraphicFill>
            </Fill>
            <VendorOption name="graphic-margin">0</VendorOption>
          </PolygonSymbolizer>
          <PolygonSymbolizer>
            <Fill>
              <GraphicFill>
                <Graphic>
                  <Mark>
                    <WellKnownName>shape://horline</WellKnownName>
                    <Stroke>
                      <CssParameter name="stroke">#fa00fa</CssParameter>
                      <CssParameter name="stroke-width">1</CssParameter>
                      <CssParameter name="stroke-opacity">1</CssParameter>
                    </Stroke>
                  </Mark>
                  <Size>15</Size>
                </Graphic>
              </GraphicFill>
            </Fill>
            <VendorOption name="graphic-margin">0</VendorOption>
          </PolygonSymbolizer>
        </Rule>
        <Rule>
          <Name>Canalisation de transport et de distribution de chaleur - I9</Name>
          <ogc:Filter>
            <ogc:PropertyIsLike wildCard="%" singleChar="_" escape="\" matchCase="false">
              <ogc:PropertyName>idass</ogc:PropertyName>
              <ogc:Literal>i9-%</ogc:Literal>
            </ogc:PropertyIsLike>
          </ogc:Filter>
          <LineSymbolizer>
            <Stroke>
              <CssParameter name="stroke">#fa00fa</CssParameter>
              <CssParameter name="stroke-width">1.5</CssParameter>
              <CssParameter name="stroke-opacity">1.0</CssParameter>
              <CssParameter name="stroke-linecap">square</CssParameter>
              <CssParameter name="stroke-linejoin">bevel</CssParameter>
            </Stroke>
          </LineSymbolizer>
        </Rule>
        <Rule>
          <Name>Travaux miniers</Name>
          <ogc:Filter>
            <ogc:PropertyIsLike wildCard="%" singleChar="_" escape="\" matchCase="false">
              <ogc:PropertyName>idass</ogc:PropertyName>
              <ogc:Literal>i10-%</ogc:Literal>
            </ogc:PropertyIsLike>
          </ogc:Filter>
          <LineSymbolizer>
            <Stroke>
              <CssParameter name="stroke">#fa00fa</CssParameter>
              <CssParameter name="stroke-width">1.5</CssParameter>
              <CssParameter name="stroke-opacity">1.0</CssParameter>
              <CssParameter name="stroke-linecap">square</CssParameter>
              <CssParameter name="stroke-linejoin">bevel</CssParameter>
            </Stroke>
          </LineSymbolizer>
          <PolygonSymbolizer>
            <Fill>
              <GraphicFill>
                <Graphic>
                  <Mark>
                    <WellKnownName>shape://backslash</WellKnownName>
                    <Stroke>
                      <CssParameter name="stroke">#0000ff</CssParameter>
                      <CssParameter name="stroke-width">0.8</CssParameter>
                      <CssParameter name="stroke-opacity">1</CssParameter>
                    </Stroke>
                  </Mark>
                  <Size>5</Size>
                </Graphic>
              </GraphicFill>
            </Fill>
            <VendorOption name="graphic-margin">0</VendorOption>
          </PolygonSymbolizer>
        </Rule>
        <Rule>
          <Name>Cimetières - INT1</Name>
          <ogc:Filter>
            <ogc:PropertyIsLike wildCard="%" singleChar="_" escape="\" matchCase="false">
              <ogc:PropertyName>idass</ogc:PropertyName>
              <ogc:Literal>int1-%</ogc:Literal>
            </ogc:PropertyIsLike>
          </ogc:Filter>
          <LineSymbolizer>
            <Stroke>
              <CssParameter name="stroke">#000000</CssParameter>
              <CssParameter name="stroke-width">2.0</CssParameter>
              <CssParameter name="stroke-opacity">1.0</CssParameter>
              <CssParameter name="stroke-linecap">square</CssParameter>
              <CssParameter name="stroke-linejoin">bevel</CssParameter>
            </Stroke>
          </LineSymbolizer>
          <PolygonSymbolizer>
            <Fill>
              <GraphicFill>
                <Graphic>
                  <Mark>
                    <WellKnownName>shape://slash</WellKnownName>
                    <Stroke>
                      <CssParameter name="stroke">#000000</CssParameter>
                      <CssParameter name="stroke-width">1</CssParameter>
                      <CssParameter name="stroke-opacity">1</CssParameter>
                    </Stroke>
                  </Mark>
                  <Size>8</Size>
                </Graphic>
              </GraphicFill>
            </Fill>
            <VendorOption name="graphic-margin">0</VendorOption>
          </PolygonSymbolizer>
        </Rule>
        <Rule>
          <Name>Equipements sportifs - JS1</Name>
          <ogc:Filter>
            <ogc:PropertyIsLike wildCard="%" singleChar="_" escape="\" matchCase="false">
              <ogc:PropertyName>idass</ogc:PropertyName>
              <ogc:Literal>js1-%</ogc:Literal>
            </ogc:PropertyIsLike>
          </ogc:Filter>
          <LineSymbolizer>
            <Stroke>
              <GraphicStroke>
                <Graphic>
                  <Mark>
                    <WellKnownName>triangle</WellKnownName>
                    <Fill>
                      <CssParameter name="fill">#000000</CssParameter>
                      <CssParameter name="fill-opacity">1.0</CssParameter>
                    </Fill>
                    <Stroke>
                      <CssParameter name="stroke">#000000</CssParameter>
                      <CssParameter name="stroke-width">0.5</CssParameter>
                      <CssParameter name="stroke-opacity">1.0</CssParameter>
                    </Stroke>
                  </Mark>
                  <Size>7.0</Size>
                  <Rotation>0.0</Rotation>
                </Graphic>
                <Gap>11.0</Gap>
              </GraphicStroke>
            </Stroke>
          </LineSymbolizer>
        </Rule>
        <Rule>
          <Name>Plans de prévention des risques naturels et miniers - PM1</Name>
          <ogc:Filter>
            <ogc:PropertyIsLike wildCard="%" singleChar="_" escape="\" matchCase="false">
              <ogc:PropertyName>idass</ogc:PropertyName>
              <ogc:Literal>pm1-%</ogc:Literal>
            </ogc:PropertyIsLike>
          </ogc:Filter>
          <LineSymbolizer>
            <Stroke>
              <CssParameter name="stroke">#a81616</CssParameter>
              <CssParameter name="stroke-width">1.5</CssParameter>
              <CssParameter name="stroke-opacity">1.0</CssParameter>
              <CssParameter name="stroke-linecap">square</CssParameter>
              <CssParameter name="stroke-linejoin">bevel</CssParameter>
            </Stroke>
          </LineSymbolizer>
          <PolygonSymbolizer>
            <Fill>
              <GraphicFill>
                <Graphic>
                  <Mark>
                    <WellKnownName>shape://slash</WellKnownName>
                    <Stroke>
                      <CssParameter name="stroke">#a81616</CssParameter>
                      <CssParameter name="stroke-width">1</CssParameter>
                      <CssParameter name="stroke-opacity">1</CssParameter>
                    </Stroke>
                  </Mark>
                  <Size>8</Size>
                </Graphic>
              </GraphicFill>
            </Fill>
            <VendorOption name="graphic-margin">0</VendorOption>
          </PolygonSymbolizer>
        </Rule>
        <Rule>
          <Name>Inondations pour la rétention des crues du Rhin - PM1bis</Name>
          <ogc:Filter>
            <ogc:PropertyIsLike wildCard="%" singleChar="_" escape="\" matchCase="false">
              <ogc:PropertyName>idass</ogc:PropertyName>
              <ogc:Literal>pm1bis-%</ogc:Literal>
            </ogc:PropertyIsLike>
          </ogc:Filter>
          <LineSymbolizer>
            <Stroke>
              <CssParameter name="stroke">#a81616</CssParameter>
              <CssParameter name="stroke-width">1.5</CssParameter>
              <CssParameter name="stroke-opacity">1.0</CssParameter>
              <CssParameter name="stroke-linecap">square</CssParameter>
              <CssParameter name="stroke-linejoin">bevel</CssParameter>
            </Stroke>
          </LineSymbolizer>
          <PolygonSymbolizer>
            <Fill>
              <GraphicFill>
                <Graphic>
                  <Mark>
                    <WellKnownName>shape://slash</WellKnownName>
                    <Stroke>
                      <CssParameter name="stroke">#a81616</CssParameter>
                      <CssParameter name="stroke-width">1</CssParameter>
                      <CssParameter name="stroke-opacity">1</CssParameter>
                    </Stroke>
                  </Mark>
                  <Size>8</Size>
                </Graphic>
              </GraphicFill>
            </Fill>
            <VendorOption name="graphic-margin">0</VendorOption>
          </PolygonSymbolizer>
        </Rule>
        <Rule>
          <Name>Installations classées et sites constituant un risque pour la sécurité et la salubrité publique - PM2</Name>
          <ogc:Filter>
            <ogc:PropertyIsLike wildCard="%" singleChar="_" escape="\" matchCase="false">
              <ogc:PropertyName>idass</ogc:PropertyName>
              <ogc:Literal>pm2-%</ogc:Literal>
            </ogc:PropertyIsLike>
          </ogc:Filter>
          <LineSymbolizer>
            <Stroke>
              <CssParameter name="stroke">#a81616</CssParameter>
              <CssParameter name="stroke-width">1.5</CssParameter>
              <CssParameter name="stroke-opacity">1.0</CssParameter>
              <CssParameter name="stroke-linecap">square</CssParameter>
              <CssParameter name="stroke-linejoin">bevel</CssParameter>
            </Stroke>
          </LineSymbolizer>
          <PolygonSymbolizer>
            <Fill>
              <GraphicFill>
                <Graphic>
                  <Mark>
                    <WellKnownName>shape://backslash</WellKnownName>
                    <Stroke>
                      <CssParameter name="stroke">#a81616</CssParameter>
                      <CssParameter name="stroke-width">1</CssParameter>
                      <CssParameter name="stroke-opacity">1</CssParameter>
                    </Stroke>
                  </Mark>
                  <Size>8</Size>
                </Graphic>
              </GraphicFill>
            </Fill>
            <VendorOption name="graphic-margin">0</VendorOption>
          </PolygonSymbolizer>
        </Rule>
        <Rule>
          <Name>Plans de prévention des risques technologiques - PM3</Name>
          <ogc:Filter>
            <ogc:PropertyIsLike wildCard="%" singleChar="_" escape="\" matchCase="false">
              <ogc:PropertyName>idass</ogc:PropertyName>
              <ogc:Literal>pm3-%</ogc:Literal>
            </ogc:PropertyIsLike>
          </ogc:Filter>
          <LineSymbolizer>
            <Stroke>
              <CssParameter name="stroke">#a81616</CssParameter>
              <CssParameter name="stroke-width">1.5</CssParameter>
              <CssParameter name="stroke-opacity">1.0</CssParameter>
              <CssParameter name="stroke-linecap">square</CssParameter>
              <CssParameter name="stroke-linejoin">bevel</CssParameter>
            </Stroke>
          </LineSymbolizer>
          <PolygonSymbolizer>
            <Fill>
              <GraphicFill>
                <Graphic>
                  <Mark>
                    <WellKnownName>shape://vertline</WellKnownName>
                    <Stroke>
                      <CssParameter name="stroke">#a81616</CssParameter>
                      <CssParameter name="stroke-width">1</CssParameter>
                      <CssParameter name="stroke-opacity">1</CssParameter>
                    </Stroke>
                  </Mark>
                  <Size>6</Size>
                </Graphic>
              </GraphicFill>
            </Fill>
            <VendorOption name="graphic-margin">0</VendorOption>
          </PolygonSymbolizer>
        </Rule>
        <Rule>
          <Name>Zones de rétention d'eau et de mobilité des cours d'eau - PM4</Name>
          <ogc:Filter>
            <ogc:PropertyIsLike wildCard="%" singleChar="_" escape="\" matchCase="false">
              <ogc:PropertyName>idass</ogc:PropertyName>
              <ogc:Literal>pm4-%</ogc:Literal>
            </ogc:PropertyIsLike>
          </ogc:Filter>
          <LineSymbolizer>
            <Stroke>
              <CssParameter name="stroke">#a81616</CssParameter>
              <CssParameter name="stroke-width">1.5</CssParameter>
              <CssParameter name="stroke-opacity">1.0</CssParameter>
              <CssParameter name="stroke-linecap">square</CssParameter>
              <CssParameter name="stroke-linejoin">bevel</CssParameter>
            </Stroke>
          </LineSymbolizer>
          <PolygonSymbolizer>
            <Fill>
              <GraphicFill>
                <Graphic>
                  <Mark>
                    <WellKnownName>square</WellKnownName>
                    <Fill>
                      <CssParameter name="fill">#a81616</CssParameter>
                      <CssParameter name="fill-opacity">1.0</CssParameter>
                    </Fill>
                    <Stroke>
                      <CssParameter name="stroke">#000000</CssParameter>
                      <CssParameter name="stroke-width">0.0</CssParameter>
                      <CssParameter name="stroke-opacity">0.0</CssParameter>
                    </Stroke>
                  </Mark>
                  <Size>8.0</Size>
                  <Rotation>0.0</Rotation>
                </Graphic>
              </GraphicFill>
            </Fill>
            <VendorOption name="graphic-margin">0</VendorOption>
          </PolygonSymbolizer>
        </Rule>
        <Rule>
          <Name>Ouvrages hydrauliques- PM5</Name>
          <ogc:Filter>
            <ogc:PropertyIsLike wildCard="%" singleChar="_" escape="\" matchCase="false">
              <ogc:PropertyName>idass</ogc:PropertyName>
              <ogc:Literal>pm5-%</ogc:Literal>
            </ogc:PropertyIsLike>
          </ogc:Filter>
          <LineSymbolizer>
            <Stroke>
              <CssParameter name="stroke">#a81616</CssParameter>
              <CssParameter name="stroke-width">1.5</CssParameter>
              <CssParameter name="stroke-opacity">1.0</CssParameter>
              <CssParameter name="stroke-linecap">square</CssParameter>
              <CssParameter name="stroke-linejoin">bevel</CssParameter>
            </Stroke>
          </LineSymbolizer>
          <PolygonSymbolizer>
            <Fill>
              <GraphicFill>
                <Graphic>
                  <Mark>
                    <WellKnownName>shape://horline</WellKnownName>
                    <Stroke>
                      <CssParameter name="stroke">#a81616</CssParameter>
                      <CssParameter name="stroke-width">1.2599</CssParameter>
                      <CssParameter name="stroke-opacity">1</CssParameter>
                    </Stroke>
                  </Mark>
                  <Size>6</Size>
                </Graphic>
              </GraphicFill>
            </Fill>
            <VendorOption name="graphic-margin">0</VendorOption>
          </PolygonSymbolizer>
        </Rule>
        <Rule>
          <Name>Installations nucléaires de base - PM6</Name>
          <ogc:Filter>
            <ogc:PropertyIsLike wildCard="%" singleChar="_" escape="\" matchCase="false">
              <ogc:PropertyName>idass</ogc:PropertyName>
              <ogc:Literal>pm6-%</ogc:Literal>
            </ogc:PropertyIsLike>
          </ogc:Filter>
          <LineSymbolizer>
            <Stroke>
              <CssParameter name="stroke">#a81616</CssParameter>
              <CssParameter name="stroke-width">1.5</CssParameter>
              <CssParameter name="stroke-opacity">1.0</CssParameter>
              <CssParameter name="stroke-linecap">square</CssParameter>
              <CssParameter name="stroke-linejoin">bevel</CssParameter>
            </Stroke>
          </LineSymbolizer>
          <PolygonSymbolizer>
            <Fill>
              <GraphicFill>
                <Graphic>
                  <Mark>
                    <WellKnownName>circle</WellKnownName>
                    <Fill>
                      <CssParameter name="fill">#a81616</CssParameter>
                      <CssParameter name="fill-opacity">1.0</CssParameter>
                    </Fill>
                    <Stroke>
                      <CssParameter name="stroke">#000000</CssParameter>
                      <CssParameter name="stroke-width">0.0</CssParameter>
                      <CssParameter name="stroke-opacity">0.0</CssParameter>
                    </Stroke>
                  </Mark>
                  <Size>2.0</Size>
                  <Rotation>0.0</Rotation>
                </Graphic>
              </GraphicFill>
            </Fill>
            <VendorOption name="graphic-margin">0</VendorOption>
          </PolygonSymbolizer>
        </Rule>
        <Rule>
          <Name>Ouvrage anti inondation et submersion - PM7</Name>
          <ogc:Filter>
            <ogc:PropertyIsLike wildCard="%" singleChar="_" escape="\" matchCase="false">
              <ogc:PropertyName>idass</ogc:PropertyName>
              <ogc:Literal>pm7-%</ogc:Literal>
            </ogc:PropertyIsLike>
          </ogc:Filter>
          <LineSymbolizer>
            <Stroke>
              <CssParameter name="stroke">#a81616</CssParameter>
              <CssParameter name="stroke-width">1.5</CssParameter>
              <CssParameter name="stroke-opacity">1.0</CssParameter>
              <CssParameter name="stroke-linecap">square</CssParameter>
              <CssParameter name="stroke-linejoin">bevel</CssParameter>
            </Stroke>
          </LineSymbolizer>
          <PolygonSymbolizer>
            <Fill>
              <GraphicFill>
                <Graphic>
                  <Mark>
                    <WellKnownName>square</WellKnownName>
                    <Fill>
                      <CssParameter name="fill">#a81616</CssParameter>
                      <CssParameter name="fill-opacity">1.0</CssParameter>
                    </Fill>
                    <Stroke>
                      <CssParameter name="stroke">#000000</CssParameter>
                      <CssParameter name="stroke-width">0.0</CssParameter>
                      <CssParameter name="stroke-opacity">0.0</CssParameter>
                    </Stroke>
                  </Mark>
                  <Size>8.0</Size>
                  <Rotation>0.0</Rotation>
                </Graphic>
              </GraphicFill>
            </Fill>
            <VendorOption name="graphic-margin">0</VendorOption>
          </PolygonSymbolizer>
        </Rule>
        <Rule>
          <Name>Point d'eau, piste DFCI, zone de coupure de combustible - PM8</Name>
          <ogc:Filter>
            <ogc:PropertyIsLike wildCard="%" singleChar="_" escape="\" matchCase="false">
              <ogc:PropertyName>idass</ogc:PropertyName>
              <ogc:Literal>pm8-%</ogc:Literal>
            </ogc:PropertyIsLike>
          </ogc:Filter>
          <LineSymbolizer>
            <Stroke>
              <CssParameter name="stroke">#a81616</CssParameter>
              <CssParameter name="stroke-width">1.5</CssParameter>
              <CssParameter name="stroke-opacity">1.0</CssParameter>
              <CssParameter name="stroke-linecap">square</CssParameter>
              <CssParameter name="stroke-linejoin">bevel</CssParameter>
            </Stroke>
          </LineSymbolizer>
          <PolygonSymbolizer>
            <Fill>
              <GraphicFill>
                <Graphic>
                  <Mark>
                    <WellKnownName>circle</WellKnownName>
                    <Fill>
                      <CssParameter name="fill">#a81616</CssParameter>
                      <CssParameter name="fill-opacity">1.0</CssParameter>
                    </Fill>
                    <Stroke>
                      <CssParameter name="stroke">#000000</CssParameter>
                      <CssParameter name="stroke-width">0.0</CssParameter>
                      <CssParameter name="stroke-opacity">0.0</CssParameter>
                    </Stroke>
                  </Mark>
                  <Size>2.0</Size>
                  <Rotation>0.0</Rotation>
                </Graphic>
              </GraphicFill>
            </Fill>
            <VendorOption name="graphic-margin">0</VendorOption>
          </PolygonSymbolizer>
        </Rule>
        <Rule>
          <Name>Communications électroniques - Zone de protection - PT1 </Name>
          <ogc:Filter>
            <ogc:And>
              <ogc:PropertyIsLike wildCard="%" singleChar="_" escape="\" matchCase="false">
                <ogc:PropertyName>idass</ogc:PropertyName>
                <ogc:Literal>pt1-%</ogc:Literal>
              </ogc:PropertyIsLike>
              <ogc:PropertyIsEqualTo>
                <ogc:PropertyName>typeass</ogc:PropertyName>
                <ogc:Literal>Zone de protection</ogc:Literal>
              </ogc:PropertyIsEqualTo>
            </ogc:And>
          </ogc:Filter>
          <LineSymbolizer>
            <Stroke>
              <CssParameter name="stroke">#807dff</CssParameter>
              <CssParameter name="stroke-width">2.0</CssParameter>
              <CssParameter name="stroke-opacity">1.0</CssParameter>
              <CssParameter name="stroke-linecap">square</CssParameter>
              <CssParameter name="stroke-linejoin">bevel</CssParameter>
            </Stroke>
          </LineSymbolizer>
          <PolygonSymbolizer>
            <Fill>
              <GraphicFill>
                <Graphic>
                  <Mark>
                    <WellKnownName>shape://slash</WellKnownName>
                    <Stroke>
                      <CssParameter name="stroke">#807dff</CssParameter>
                      <CssParameter name="stroke-width">1.8</CssParameter>
                      <CssParameter name="stroke-opacity">1</CssParameter>
                    </Stroke>
                  </Mark>
                  <Size>8</Size>
                </Graphic>
              </GraphicFill>
            </Fill>
            <VendorOption name="graphic-margin">0</VendorOption>
          </PolygonSymbolizer>
        </Rule>
        <Rule>
          <Name>Communications électroniques - Zone de garde - PT1 </Name>
          <ogc:Filter>
            <ogc:And>
              <ogc:PropertyIsLike wildCard="%" singleChar="_" escape="\" matchCase="false">
                <ogc:PropertyName>idass</ogc:PropertyName>
                <ogc:Literal>pt1-%</ogc:Literal>
              </ogc:PropertyIsLike>
              <ogc:PropertyIsEqualTo>
                <ogc:PropertyName>typeass</ogc:PropertyName>
                <ogc:Literal>Zone de garde</ogc:Literal>
              </ogc:PropertyIsEqualTo>
            </ogc:And>
          </ogc:Filter>
          <LineSymbolizer>
            <Stroke>
              <CssParameter name="stroke">#807dff</CssParameter>
              <CssParameter name="stroke-width">2.0</CssParameter>
              <CssParameter name="stroke-opacity">1.0</CssParameter>
              <CssParameter name="stroke-linecap">square</CssParameter>
              <CssParameter name="stroke-linejoin">bevel</CssParameter>
            </Stroke>
          </LineSymbolizer>
          <PolygonSymbolizer>
            <Fill>
              <GraphicFill>
                <Graphic>
                  <Mark>
                    <WellKnownName>shape://slash</WellKnownName>
                    <Stroke>
                      <CssParameter name="stroke">#807dff</CssParameter>
                      <CssParameter name="stroke-width">1.8</CssParameter>
                      <CssParameter name="stroke-opacity">1</CssParameter>
                    </Stroke>
                  </Mark>
                  <Size>16</Size>
                </Graphic>
              </GraphicFill>
            </Fill>
            <VendorOption name="graphic-margin">0</VendorOption>
          </PolygonSymbolizer>
        </Rule>
        <Rule>
          <Name>Communications électroniques - Zone primaire de dégagement - PT2</Name>
          <ogc:Filter>
            <ogc:And>
              <ogc:PropertyIsLike wildCard="%" singleChar="_" escape="\" matchCase="false">
                <ogc:PropertyName>idass</ogc:PropertyName>
                <ogc:Literal>pt2-%</ogc:Literal>
              </ogc:PropertyIsLike>
              <ogc:PropertyIsEqualTo>
                <ogc:PropertyName>typeass</ogc:PropertyName>
                <ogc:Literal>Zone primaire de dégagement</ogc:Literal>
              </ogc:PropertyIsEqualTo>
            </ogc:And>
          </ogc:Filter>
          <LineSymbolizer>
            <Stroke>
              <CssParameter name="stroke">#807dff</CssParameter>
              <CssParameter name="stroke-width">2.0</CssParameter>
              <CssParameter name="stroke-opacity">1.0</CssParameter>
              <CssParameter name="stroke-linecap">square</CssParameter>
              <CssParameter name="stroke-linejoin">bevel</CssParameter>
            </Stroke>
          </LineSymbolizer>
          <PolygonSymbolizer>
            <Fill>
              <GraphicFill>
                <Graphic>
                  <Mark>
                    <WellKnownName>shape://backslash</WellKnownName>
                    <Stroke>
                      <CssParameter name="stroke">#807dff</CssParameter>
                      <CssParameter name="stroke-width">1.8</CssParameter>
                      <CssParameter name="stroke-opacity">1</CssParameter>
                    </Stroke>
                  </Mark>
                  <Size>8</Size>
                </Graphic>
              </GraphicFill>
            </Fill>
            <VendorOption name="graphic-margin">0</VendorOption>
          </PolygonSymbolizer>
        </Rule>
        <Rule>
          <Name>Communications électroniques - Zone secondaire, spéciale et secteur de dégagement -  PT2</Name>
          <ogc:Filter>
            <ogc:And>
              <ogc:PropertyIsLike wildCard="%" singleChar="_" escape="\" matchCase="false">
                <ogc:PropertyName>idass</ogc:PropertyName>
                <ogc:Literal>pt2-%</ogc:Literal>
              </ogc:PropertyIsLike>
              <ogc:Or>
                <ogc:PropertyIsEqualTo>
                  <ogc:PropertyName>typeass</ogc:PropertyName>
                  <ogc:Literal>Zone secondaire de dégagement</ogc:Literal>
                </ogc:PropertyIsEqualTo>
                <ogc:PropertyIsEqualTo>
                  <ogc:PropertyName>typeass</ogc:PropertyName>
                  <ogc:Literal>Zone spéciale de dégagement</ogc:Literal>
                </ogc:PropertyIsEqualTo>
                <ogc:PropertyIsEqualTo>
                  <ogc:PropertyName>typeass</ogc:PropertyName>
                  <ogc:Literal>Secteur de dégagement</ogc:Literal>
                </ogc:PropertyIsEqualTo>
              </ogc:Or>
            </ogc:And>
          </ogc:Filter>
          <LineSymbolizer>
            <Stroke>
              <CssParameter name="stroke">#807dff</CssParameter>
              <CssParameter name="stroke-width">2.0</CssParameter>
              <CssParameter name="stroke-opacity">1.0</CssParameter>
              <CssParameter name="stroke-linecap">square</CssParameter>
              <CssParameter name="stroke-linejoin">bevel</CssParameter>
            </Stroke>
          </LineSymbolizer>
          <PolygonSymbolizer>
            <Fill>
              <GraphicFill>
                <Graphic>
                  <Mark>
                    <WellKnownName>shape://backslash</WellKnownName>
                    <Stroke>
                      <CssParameter name="stroke">#807dff</CssParameter>
                      <CssParameter name="stroke-width">1.8</CssParameter>
                      <CssParameter name="stroke-opacity">1</CssParameter>
                    </Stroke>
                  </Mark>
                  <Size>16</Size>
                </Graphic>
              </GraphicFill>
            </Fill>
            <VendorOption name="graphic-margin">0</VendorOption>
          </PolygonSymbolizer>
        </Rule>
        <Rule>
          <Name>Réseaux de télécommunication - PT3</Name>
          <ogc:Filter>
            <ogc:PropertyIsLike wildCard="%" singleChar="_" escape="\" matchCase="false">
              <ogc:PropertyName>idass</ogc:PropertyName>
              <ogc:Literal>pt3-%</ogc:Literal>
            </ogc:PropertyIsLike>
          </ogc:Filter>
          <LineSymbolizer>
            <Stroke>
              <CssParameter name="stroke">#807dff</CssParameter>
              <CssParameter name="stroke-width">1.5</CssParameter>
              <CssParameter name="stroke-opacity">1.0</CssParameter>
              <CssParameter name="stroke-linecap">square</CssParameter>
              <CssParameter name="stroke-linejoin">bevel</CssParameter>
            </Stroke>
          </LineSymbolizer>
        </Rule>
        <Rule>
          <Name>Voies ferrées et visibilité sur les voies publiques - T1</Name>
          <ogc:Filter>
            <ogc:PropertyIsLike wildCard="%" singleChar="_" escape="\" matchCase="false">
              <ogc:PropertyName>idass</ogc:PropertyName>
              <ogc:Literal>t1-%</ogc:Literal>
            </ogc:PropertyIsLike>
          </ogc:Filter>
          <LineSymbolizer>
            <Stroke>
              <CssParameter name="stroke">#000000</CssParameter>
              <CssParameter name="stroke-width">1.5</CssParameter>
              <CssParameter name="stroke-opacity">1.0</CssParameter>
              <CssParameter name="stroke-linecap">square</CssParameter>
              <CssParameter name="stroke-linejoin">bevel</CssParameter>
            </Stroke>
          </LineSymbolizer>
          <PolygonSymbolizer>
            <Fill>
              <GraphicFill>
                <Graphic>
                  <Mark>
                    <WellKnownName>shape://slash</WellKnownName>
                    <Stroke>
                      <CssParameter name="stroke">#000000</CssParameter>
                      <CssParameter name="stroke-width">1</CssParameter>
                      <CssParameter name="stroke-opacity">1</CssParameter>
                    </Stroke>
                  </Mark>
                  <Size>8</Size>
                </Graphic>
              </GraphicFill>
            </Fill>
            <VendorOption name="graphic-margin">0</VendorOption>
          </PolygonSymbolizer>
        </Rule>
        <Rule>
          <Name>Survol au profit des téléphériques - T2</Name>
          <ogc:Filter>
            <ogc:PropertyIsLike wildCard="%" singleChar="_" escape="\" matchCase="false">
              <ogc:PropertyName>idass</ogc:PropertyName>
              <ogc:Literal>t2-%</ogc:Literal>
            </ogc:PropertyIsLike>
          </ogc:Filter>
          <LineSymbolizer>
            <Stroke>
              <CssParameter name="stroke">#000000</CssParameter>
              <CssParameter name="stroke-width">1.5</CssParameter>
              <CssParameter name="stroke-opacity">1.0</CssParameter>
              <CssParameter name="stroke-linecap">square</CssParameter>
              <CssParameter name="stroke-linejoin">bevel</CssParameter>
            </Stroke>
          </LineSymbolizer>
        </Rule>
        <Rule>
          <Name>Tréfonds - T3</Name>
          <ogc:Filter>
            <ogc:PropertyIsLike wildCard="%" singleChar="_" escape="\" matchCase="false">
              <ogc:PropertyName>idass</ogc:PropertyName>
              <ogc:Literal>t3-%</ogc:Literal>
            </ogc:PropertyIsLike>
          </ogc:Filter>
          <LineSymbolizer>
            <Stroke>
              <CssParameter name="stroke">#000000</CssParameter>
              <CssParameter name="stroke-width">1.5</CssParameter>
              <CssParameter name="stroke-opacity">1.0</CssParameter>
              <CssParameter name="stroke-linecap">square</CssParameter>
              <CssParameter name="stroke-linejoin">bevel</CssParameter>
            </Stroke>
          </LineSymbolizer>
          <PolygonSymbolizer>
            <Fill>
              <GraphicFill>
                <Graphic>
                  <Mark>
                    <WellKnownName>shape://backslash</WellKnownName>
                    <Stroke>
                      <CssParameter name="stroke">#000000</CssParameter>
                      <CssParameter name="stroke-width">1</CssParameter>
                      <CssParameter name="stroke-opacity">1</CssParameter>
                    </Stroke>
                  </Mark>
                  <Size>8</Size>
                </Graphic>
              </GraphicFill>
            </Fill>
            <VendorOption name="graphic-margin">0</VendorOption>
          </PolygonSymbolizer>
        </Rule>
        <Rule>
          <Name>Aéronautique de balisage - T4</Name>
          <ogc:Filter>
            <ogc:PropertyIsLike wildCard="%" singleChar="_" escape="\" matchCase="false">
              <ogc:PropertyName>idass</ogc:PropertyName>
              <ogc:Literal>t4-%</ogc:Literal>
            </ogc:PropertyIsLike>
          </ogc:Filter>
          <LineSymbolizer>
            <Stroke>
              <CssParameter name="stroke">#000000</CssParameter>
              <CssParameter name="stroke-width">1.5</CssParameter>
              <CssParameter name="stroke-opacity">1.0</CssParameter>
              <CssParameter name="stroke-linecap">square</CssParameter>
              <CssParameter name="stroke-linejoin">bevel</CssParameter>
            </Stroke>
          </LineSymbolizer>
        </Rule>
        <Rule>
          <Name>Circulation aérienne - T5</Name>
          <ogc:Filter>
            <ogc:PropertyIsLike wildCard="%" singleChar="_" escape="\" matchCase="false">
              <ogc:PropertyName>idass</ogc:PropertyName>
              <ogc:Literal>t5-%</ogc:Literal>
            </ogc:PropertyIsLike>
          </ogc:Filter>
          <LineSymbolizer>
            <Stroke>
              <CssParameter name="stroke">#000000</CssParameter>
              <CssParameter name="stroke-width">1.5</CssParameter>
              <CssParameter name="stroke-opacity">1.0</CssParameter>
              <CssParameter name="stroke-linecap">square</CssParameter>
              <CssParameter name="stroke-linejoin">bevel</CssParameter>
            </Stroke>
          </LineSymbolizer>
          <PolygonSymbolizer>
            <Fill>
              <GraphicFill>
                <Graphic>
                  <Mark>
                    <WellKnownName>square</WellKnownName>
                    <Fill>
                      <CssParameter name="fill">#000000</CssParameter>
                      <CssParameter name="fill-opacity">1.0</CssParameter>
                    </Fill>
                    <Stroke>
                      <CssParameter name="stroke">#000000</CssParameter>
                      <CssParameter name="stroke-width">0.0</CssParameter>
                      <CssParameter name="stroke-opacity">1.0</CssParameter>
                    </Stroke>
                  </Mark>
                  <Size>7.0</Size>
                  <Rotation>0.0</Rotation>
                </Graphic>
              </GraphicFill>
            </Fill>
            <VendorOption name="graphic-margin">0</VendorOption>
          </PolygonSymbolizer>
        </Rule>
        <Rule>
          <Name>Terrains nécessaires à la navigation aérienne - T6</Name>
          <ogc:Filter>
            <ogc:PropertyIsLike wildCard="%" singleChar="_" escape="\" matchCase="false">
              <ogc:PropertyName>idass</ogc:PropertyName>
              <ogc:Literal>t6-%</ogc:Literal>
            </ogc:PropertyIsLike>
          </ogc:Filter>
          <LineSymbolizer>
            <Stroke>
              <CssParameter name="stroke">#000000</CssParameter>
              <CssParameter name="stroke-width">1.0</CssParameter>
              <CssParameter name="stroke-opacity">1.0</CssParameter>
              <CssParameter name="stroke-linecap">square</CssParameter>
              <CssParameter name="stroke-linejoin">bevel</CssParameter>
            </Stroke>
          </LineSymbolizer>
          <PolygonSymbolizer>
            <Fill>
              <GraphicFill>
                <Graphic>
                  <Mark>
                    <WellKnownName>square</WellKnownName>
                    <Fill>
                      <CssParameter name="fill">#000000</CssParameter>
                      <CssParameter name="fill-opacity">1.0</CssParameter>
                    </Fill>
                    <Stroke>
                      <CssParameter name="stroke">#000000</CssParameter>
                      <CssParameter name="stroke-width">0.0</CssParameter>
                      <CssParameter name="stroke-opacity">0.0</CssParameter>
                    </Stroke>
                  </Mark>
                  <Size>6.0</Size>
                  <Rotation>0.0</Rotation>
                </Graphic>
              </GraphicFill>
            </Fill>
            <VendorOption name="graphic-margin">0</VendorOption>
          </PolygonSymbolizer>
        </Rule>
        <Rule>
          <Name>Extérieur des zones de dégagament - T7</Name>
          <ogc:Filter>
            <ogc:PropertyIsLike wildCard="%" singleChar="_" escape="\" matchCase="false">
              <ogc:PropertyName>idass</ogc:PropertyName>
              <ogc:Literal>t7-%</ogc:Literal>
            </ogc:PropertyIsLike>
          </ogc:Filter>
          <LineSymbolizer>
            <Stroke>
              <CssParameter name="stroke">#000000</CssParameter>
              <CssParameter name="stroke-width">1.5</CssParameter>
              <CssParameter name="stroke-opacity">1.0</CssParameter>
              <CssParameter name="stroke-linecap">square</CssParameter>
              <CssParameter name="stroke-linejoin">bevel</CssParameter>
            </Stroke>
          </LineSymbolizer>
        </Rule>
        <Rule>
          <Name>Installations de navigation et d'atterrissage - Zone primaire de dégagement - T8 </Name>
          <ogc:Filter>
            <ogc:And>
              <ogc:PropertyIsLike wildCard="%" singleChar="_" escape="\" matchCase="false">
                <ogc:PropertyName>idass</ogc:PropertyName>
                <ogc:Literal>t8-%</ogc:Literal>
              </ogc:PropertyIsLike>
              <ogc:PropertyIsEqualTo>
                <ogc:PropertyName>typeass</ogc:PropertyName>
                <ogc:Literal>Zone primaire de dégagement</ogc:Literal>
              </ogc:PropertyIsEqualTo>
            </ogc:And>
          </ogc:Filter>
          <LineSymbolizer>
            <Stroke>
              <CssParameter name="stroke">#000000</CssParameter>
              <CssParameter name="stroke-width">2.0</CssParameter>
              <CssParameter name="stroke-opacity">1.0</CssParameter>
              <CssParameter name="stroke-linecap">square</CssParameter>
              <CssParameter name="stroke-linejoin">bevel</CssParameter>
            </Stroke>
          </LineSymbolizer>
          <PolygonSymbolizer>
            <Fill>
              <GraphicFill>
                <Graphic>
                  <Mark>
                    <WellKnownName>shape://backslash</WellKnownName>
                    <Stroke>
                      <CssParameter name="stroke">#000000</CssParameter>
                      <CssParameter name="stroke-width">1.8</CssParameter>
                      <CssParameter name="stroke-opacity">1</CssParameter>
                    </Stroke>
                  </Mark>
                  <Size>8</Size>
                </Graphic>
              </GraphicFill>
            </Fill>
            <VendorOption name="graphic-margin">0</VendorOption>
          </PolygonSymbolizer>
        </Rule>
        <Rule>
          <Name>Installations de navigation et d'atterrissage  -Zone secondaire, spéciale et secteur de dégagement - T8 </Name>
          <ogc:Filter>
            <ogc:And>
              <ogc:PropertyIsLike wildCard="%" singleChar="_" escape="\" matchCase="false">
                <ogc:PropertyName>idass</ogc:PropertyName>
                <ogc:Literal>t8-%</ogc:Literal>
              </ogc:PropertyIsLike>
              <ogc:Or>
                <ogc:PropertyIsEqualTo>
                  <ogc:PropertyName>typeass</ogc:PropertyName>
                  <ogc:Literal>Zone secondaire de dégagement</ogc:Literal>
                </ogc:PropertyIsEqualTo>
                <ogc:PropertyIsEqualTo>
                  <ogc:PropertyName>typeass</ogc:PropertyName>
                  <ogc:Literal>Zone spéciale de dégagement</ogc:Literal>
                </ogc:PropertyIsEqualTo>
                <ogc:PropertyIsEqualTo>
                  <ogc:PropertyName>typeass</ogc:PropertyName>
                  <ogc:Literal>Secteur de dégagement</ogc:Literal>
                </ogc:PropertyIsEqualTo>
              </ogc:Or>
            </ogc:And>
          </ogc:Filter>
          <LineSymbolizer>
            <Stroke>
              <CssParameter name="stroke">#000000</CssParameter>
              <CssParameter name="stroke-width">2.0</CssParameter>
              <CssParameter name="stroke-opacity">1.0</CssParameter>
              <CssParameter name="stroke-linecap">square</CssParameter>
              <CssParameter name="stroke-linejoin">bevel</CssParameter>
            </Stroke>
          </LineSymbolizer>
          <PolygonSymbolizer>
            <Fill>
              <GraphicFill>
                <Graphic>
                  <Mark>
                    <WellKnownName>shape://backslash</WellKnownName>
                    <Stroke>
                      <CssParameter name="stroke">#000000</CssParameter>
                      <CssParameter name="stroke-width">1.8</CssParameter>
                      <CssParameter name="stroke-opacity">1</CssParameter>
                    </Stroke>
                  </Mark>
                  <Size>16</Size>
                </Graphic>
              </GraphicFill>
            </Fill>
            <VendorOption name="graphic-margin">0</VendorOption>
          </PolygonSymbolizer>
        </Rule>
        <Rule>
          <Name>Transport par câble - T9</Name>
          <ogc:Filter>
            <ogc:PropertyIsLike wildCard="%" singleChar="_" escape="\" matchCase="false">
              <ogc:PropertyName>idass</ogc:PropertyName>
              <ogc:Literal>t9-%</ogc:Literal>
            </ogc:PropertyIsLike>
          </ogc:Filter>
          <LineSymbolizer>
            <Stroke>
              <CssParameter name="stroke">#000000</CssParameter>
              <CssParameter name="stroke-width">1.5</CssParameter>
              <CssParameter name="stroke-opacity">1.0</CssParameter>
              <CssParameter name="stroke-linecap">square</CssParameter>
              <CssParameter name="stroke-linejoin">bevel</CssParameter>
            </Stroke>
          </LineSymbolizer>
        </Rule>
      </FeatureTypeStyle>
    </UserStyle>
  </NamedLayer>
</StyledLayerDescriptor>
