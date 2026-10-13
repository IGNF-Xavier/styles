<?xml version="1.0" encoding="UTF-8"?>
<StyledLayerDescriptor xmlns="http://www.opengis.net/sld" xmlns:ogc="http://www.opengis.net/ogc" xmlns:xlink="http://www.w3.org/1999/xlink" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" version="1.0.0" xsi:schemaLocation="http://www.opengis.net/sld http://schemas.opengis.net/sld/1.0.0/StyledLayerDescriptor.xsd">
  <NamedLayer>
    <Name>plu_inf_p</Name>
    <UserStyle>
      <Title>plu_inf_p</Title>
      <FeatureTypeStyle>
        <Rule>
          <Name>INF-P_16-00_001</Name>
          <ogc:Filter>
            <ogc:PropertyIsEqualTo>
              <ogc:PropertyName>SYMBOLE</ogc:PropertyName>
              <ogc:Literal>INF-P_16-00_001</ogc:Literal>
            </ogc:PropertyIsEqualTo>
          </ogc:Filter>
          <PointSymbolizer>
            <Graphic>
              <ExternalGraphic>
                <OnlineResource xlink:href="svg/cnig/cnig_picto_bdc49c9371.svg?fill=%23d7b09e" xlink:type="simple"/>
                <Format>image/svg+xml</Format>
              </ExternalGraphic>
              <Opacity>1.0</Opacity>
              <Size>8.251949999999999</Size>
              <Rotation>0.0</Rotation>
            </Graphic>
          </PointSymbolizer>
        </Rule>
        <Rule>
          <Name>INF-P_19-01_001</Name>
          <ogc:Filter>
            <ogc:PropertyIsEqualTo>
              <ogc:PropertyName>SYMBOLE</ogc:PropertyName>
              <ogc:Literal>INF-P_19-01_001</ogc:Literal>
            </ogc:PropertyIsEqualTo>
          </ogc:Filter>
          <PointSymbolizer>
            <Graphic>
              <ExternalGraphic>
                <OnlineResource xlink:href="svg/cnig/cnig_picto_f26ef2b329.svg?fill=%2300734c" xlink:type="simple"/>
                <Format>image/svg+xml</Format>
              </ExternalGraphic>
              <Opacity>1.0</Opacity>
              <Size>12.723999999999998</Size>
              <Rotation>0.0</Rotation>
            </Graphic>
          </PointSymbolizer>
        </Rule>
        <Rule>
          <Name>INF-P_99-00_001</Name>
          <ogc:Filter>
            <ogc:PropertyIsEqualTo>
              <ogc:PropertyName>SYMBOLE</ogc:PropertyName>
              <ogc:Literal>INF-P_99-00_001</ogc:Literal>
            </ogc:PropertyIsEqualTo>
          </ogc:Filter>
          <PointSymbolizer>
            <Graphic>
              <Mark>
                <WellKnownName>circle</WellKnownName>
                <Fill>
                  <CssParameter name="fill">#9c9c9c</CssParameter>
                  <CssParameter name="fill-opacity">1.0</CssParameter>
                </Fill>
                <Stroke>
                  <CssParameter name="stroke">#000000</CssParameter>
                  <CssParameter name="stroke-width">0.0</CssParameter>
                  <CssParameter name="stroke-opacity">0.0</CssParameter>
                </Stroke>
              </Mark>
              <Size>7.5</Size>
              <Rotation>0.0</Rotation>
            </Graphic>
          </PointSymbolizer>
        </Rule>
      </FeatureTypeStyle>
    </UserStyle>
  </NamedLayer>
</StyledLayerDescriptor>
