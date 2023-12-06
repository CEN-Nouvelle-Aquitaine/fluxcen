<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>
<qgis minScale="100000000" version="3.22.5-Białowieża" simplifyLocal="1" readOnly="0" labelsEnabled="0" simplifyAlgorithm="0" maxScale="0" simplifyMaxScale="1" hasScaleBasedVisibilityFlag="0" simplifyDrawingHints="0" styleCategories="AllStyleCategories" symbologyReferenceScale="-1" simplifyDrawingTol="1">
  <flags>
    <Identifiable>1</Identifiable>
    <Removable>1</Removable>
    <Searchable>1</Searchable>
    <Private>0</Private>
  </flags>
  <temporal endExpression="" limitMode="0" durationField="profondeur" durationUnit="min" accumulate="0" fixedDuration="0" enabled="0" endField="" startField="date_installation" mode="0" startExpression="">
    <fixedRange>
      <start></start>
      <end></end>
    </fixedRange>
  </temporal>
  <renderer-v2 forceraster="0" referencescale="-1" symbollevels="0" enableorderby="0" type="singleSymbol">
    <symbols>
      <symbol clip_to_extent="1" alpha="1" force_rhr="0" type="marker" name="0">
        <data_defined_properties>
          <Option type="Map">
            <Option value="" type="QString" name="name"/>
            <Option name="properties"/>
            <Option value="collection" type="QString" name="type"/>
          </Option>
        </data_defined_properties>
        <layer class="SimpleMarker" pass="0" enabled="1" locked="0">
          <Option type="Map">
            <Option value="0" type="QString" name="angle"/>
            <Option value="square" type="QString" name="cap_style"/>
            <Option value="164,113,88,255" type="QString" name="color"/>
            <Option value="1" type="QString" name="horizontal_anchor_point"/>
            <Option value="bevel" type="QString" name="joinstyle"/>
            <Option value="circle" type="QString" name="name"/>
            <Option value="0,0" type="QString" name="offset"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="offset_map_unit_scale"/>
            <Option value="MM" type="QString" name="offset_unit"/>
            <Option value="35,35,35,255" type="QString" name="outline_color"/>
            <Option value="solid" type="QString" name="outline_style"/>
            <Option value="0" type="QString" name="outline_width"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="outline_width_map_unit_scale"/>
            <Option value="MM" type="QString" name="outline_width_unit"/>
            <Option value="diameter" type="QString" name="scale_method"/>
            <Option value="2" type="QString" name="size"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="size_map_unit_scale"/>
            <Option value="MM" type="QString" name="size_unit"/>
            <Option value="1" type="QString" name="vertical_anchor_point"/>
          </Option>
          <prop k="angle" v="0"/>
          <prop k="cap_style" v="square"/>
          <prop k="color" v="164,113,88,255"/>
          <prop k="horizontal_anchor_point" v="1"/>
          <prop k="joinstyle" v="bevel"/>
          <prop k="name" v="circle"/>
          <prop k="offset" v="0,0"/>
          <prop k="offset_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="offset_unit" v="MM"/>
          <prop k="outline_color" v="35,35,35,255"/>
          <prop k="outline_style" v="solid"/>
          <prop k="outline_width" v="0"/>
          <prop k="outline_width_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="outline_width_unit" v="MM"/>
          <prop k="scale_method" v="diameter"/>
          <prop k="size" v="2"/>
          <prop k="size_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="size_unit" v="MM"/>
          <prop k="vertical_anchor_point" v="1"/>
          <data_defined_properties>
            <Option type="Map">
              <Option value="" type="QString" name="name"/>
              <Option name="properties"/>
              <Option value="collection" type="QString" name="type"/>
            </Option>
          </data_defined_properties>
        </layer>
      </symbol>
    </symbols>
    <rotation/>
    <sizescale/>
  </renderer-v2>
  <customproperties>
    <Option type="Map">
      <Option type="List" name="dualview/previewExpressions">
        <Option value="&quot;id_cen&quot;" type="QString"/>
      </Option>
      <Option value="0" type="int" name="embeddedWidgets/count"/>
      <Option name="variableNames"/>
      <Option name="variableValues"/>
    </Option>
  </customproperties>
  <blendMode>0</blendMode>
  <featureBlendMode>0</featureBlendMode>
  <layerOpacity>1</layerOpacity>
  <SingleCategoryDiagramRenderer attributeLegend="1" diagramType="Histogram">
    <DiagramCategory width="15" showAxis="1" minScaleDenominator="0" rotationOffset="270" backgroundColor="#ffffff" minimumSize="0" scaleBasedVisibility="0" barWidth="5" backgroundAlpha="255" sizeScale="3x:0,0,0,0,0,0" lineSizeType="MM" penColor="#000000" opacity="1" diagramOrientation="Up" direction="0" lineSizeScale="3x:0,0,0,0,0,0" scaleDependency="Area" spacing="5" maxScaleDenominator="1e+08" spacingUnit="MM" labelPlacementMethod="XHeight" penWidth="0" spacingUnitScale="3x:0,0,0,0,0,0" penAlpha="255" enabled="0" sizeType="MM" height="15">
      <fontProperties style="" description="MS Shell Dlg 2,8.25,-1,5,50,0,0,0,0,0"/>
      <attribute field="" label="" color="#000000"/>
      <axisSymbol>
        <symbol clip_to_extent="1" alpha="1" force_rhr="0" type="line" name="">
          <data_defined_properties>
            <Option type="Map">
              <Option value="" type="QString" name="name"/>
              <Option name="properties"/>
              <Option value="collection" type="QString" name="type"/>
            </Option>
          </data_defined_properties>
          <layer class="SimpleLine" pass="0" enabled="1" locked="0">
            <Option type="Map">
              <Option value="0" type="QString" name="align_dash_pattern"/>
              <Option value="square" type="QString" name="capstyle"/>
              <Option value="5;2" type="QString" name="customdash"/>
              <Option value="3x:0,0,0,0,0,0" type="QString" name="customdash_map_unit_scale"/>
              <Option value="MM" type="QString" name="customdash_unit"/>
              <Option value="0" type="QString" name="dash_pattern_offset"/>
              <Option value="3x:0,0,0,0,0,0" type="QString" name="dash_pattern_offset_map_unit_scale"/>
              <Option value="MM" type="QString" name="dash_pattern_offset_unit"/>
              <Option value="0" type="QString" name="draw_inside_polygon"/>
              <Option value="bevel" type="QString" name="joinstyle"/>
              <Option value="35,35,35,255" type="QString" name="line_color"/>
              <Option value="solid" type="QString" name="line_style"/>
              <Option value="0.26" type="QString" name="line_width"/>
              <Option value="MM" type="QString" name="line_width_unit"/>
              <Option value="0" type="QString" name="offset"/>
              <Option value="3x:0,0,0,0,0,0" type="QString" name="offset_map_unit_scale"/>
              <Option value="MM" type="QString" name="offset_unit"/>
              <Option value="0" type="QString" name="ring_filter"/>
              <Option value="0" type="QString" name="trim_distance_end"/>
              <Option value="3x:0,0,0,0,0,0" type="QString" name="trim_distance_end_map_unit_scale"/>
              <Option value="MM" type="QString" name="trim_distance_end_unit"/>
              <Option value="0" type="QString" name="trim_distance_start"/>
              <Option value="3x:0,0,0,0,0,0" type="QString" name="trim_distance_start_map_unit_scale"/>
              <Option value="MM" type="QString" name="trim_distance_start_unit"/>
              <Option value="0" type="QString" name="tweak_dash_pattern_on_corners"/>
              <Option value="0" type="QString" name="use_custom_dash"/>
              <Option value="3x:0,0,0,0,0,0" type="QString" name="width_map_unit_scale"/>
            </Option>
            <prop k="align_dash_pattern" v="0"/>
            <prop k="capstyle" v="square"/>
            <prop k="customdash" v="5;2"/>
            <prop k="customdash_map_unit_scale" v="3x:0,0,0,0,0,0"/>
            <prop k="customdash_unit" v="MM"/>
            <prop k="dash_pattern_offset" v="0"/>
            <prop k="dash_pattern_offset_map_unit_scale" v="3x:0,0,0,0,0,0"/>
            <prop k="dash_pattern_offset_unit" v="MM"/>
            <prop k="draw_inside_polygon" v="0"/>
            <prop k="joinstyle" v="bevel"/>
            <prop k="line_color" v="35,35,35,255"/>
            <prop k="line_style" v="solid"/>
            <prop k="line_width" v="0.26"/>
            <prop k="line_width_unit" v="MM"/>
            <prop k="offset" v="0"/>
            <prop k="offset_map_unit_scale" v="3x:0,0,0,0,0,0"/>
            <prop k="offset_unit" v="MM"/>
            <prop k="ring_filter" v="0"/>
            <prop k="trim_distance_end" v="0"/>
            <prop k="trim_distance_end_map_unit_scale" v="3x:0,0,0,0,0,0"/>
            <prop k="trim_distance_end_unit" v="MM"/>
            <prop k="trim_distance_start" v="0"/>
            <prop k="trim_distance_start_map_unit_scale" v="3x:0,0,0,0,0,0"/>
            <prop k="trim_distance_start_unit" v="MM"/>
            <prop k="tweak_dash_pattern_on_corners" v="0"/>
            <prop k="use_custom_dash" v="0"/>
            <prop k="width_map_unit_scale" v="3x:0,0,0,0,0,0"/>
            <data_defined_properties>
              <Option type="Map">
                <Option value="" type="QString" name="name"/>
                <Option name="properties"/>
                <Option value="collection" type="QString" name="type"/>
              </Option>
            </data_defined_properties>
          </layer>
        </symbol>
      </axisSymbol>
    </DiagramCategory>
  </SingleCategoryDiagramRenderer>
  <DiagramLayerSettings dist="0" showAll="1" obstacle="0" zIndex="0" linePlacementFlags="18" priority="0" placement="0">
    <properties>
      <Option type="Map">
        <Option value="" type="QString" name="name"/>
        <Option name="properties"/>
        <Option value="collection" type="QString" name="type"/>
      </Option>
    </properties>
  </DiagramLayerSettings>
  <geometryOptions removeDuplicateNodes="0" geometryPrecision="0">
    <activeChecks/>
    <checkConfiguration/>
  </geometryOptions>
  <legend showLabelLegend="0" type="default-vector"/>
  <referencedLayers/>
  <fieldConfiguration>
    <field configurationFlags="None" name="id_cen">
      <editWidget type="TextEdit">
        <config>
          <Option type="Map">
            <Option value="false" type="bool" name="IsMultiline"/>
            <Option value="false" type="bool" name="UseHtml"/>
          </Option>
        </config>
      </editWidget>
    </field>
    <field configurationFlags="None" name="commune">
      <editWidget type="TextEdit">
        <config>
          <Option type="Map">
            <Option value="false" type="bool" name="IsMultiline"/>
            <Option value="false" type="bool" name="UseHtml"/>
          </Option>
        </config>
      </editWidget>
    </field>
    <field configurationFlags="None" name="dept">
      <editWidget type="TextEdit">
        <config>
          <Option type="Map">
            <Option value="false" type="bool" name="IsMultiline"/>
            <Option value="false" type="bool" name="UseHtml"/>
          </Option>
        </config>
      </editWidget>
    </field>
    <field configurationFlags="None" name="date_installation">
      <editWidget type="DateTime">
        <config>
          <Option type="Map">
            <Option value="true" type="bool" name="allow_null"/>
            <Option value="true" type="bool" name="calendar_popup"/>
            <Option value="dd/MM/yyyy" type="QString" name="display_format"/>
            <Option value="dd/MM/yyyy" type="QString" name="field_format"/>
            <Option value="false" type="bool" name="field_iso_format"/>
          </Option>
        </config>
      </editWidget>
    </field>
    <field configurationFlags="None" name="modele_sonde">
      <editWidget type="TextEdit">
        <config>
          <Option type="Map">
            <Option value="false" type="bool" name="IsMultiline"/>
            <Option value="false" type="bool" name="UseHtml"/>
          </Option>
        </config>
      </editWidget>
    </field>
    <field configurationFlags="None" name="logiciel">
      <editWidget type="TextEdit">
        <config>
          <Option type="Map">
            <Option value="false" type="bool" name="IsMultiline"/>
            <Option value="false" type="bool" name="UseHtml"/>
          </Option>
        </config>
      </editWidget>
    </field>
    <field configurationFlags="None" name="frequence_sauvegarde">
      <editWidget type="TextEdit">
        <config>
          <Option type="Map">
            <Option value="false" type="bool" name="IsMultiline"/>
            <Option value="false" type="bool" name="UseHtml"/>
          </Option>
        </config>
      </editWidget>
    </field>
    <field configurationFlags="None" name="ligero">
      <editWidget type="ValueMap">
        <config>
          <Option type="Map">
            <Option type="List" name="map">
              <Option type="Map">
                <Option value="oui" type="QString" name="oui"/>
              </Option>
              <Option type="Map">
                <Option value="non" type="QString" name="non"/>
              </Option>
            </Option>
          </Option>
        </config>
      </editWidget>
    </field>
    <field configurationFlags="None" name="profondeur">
      <editWidget type="Range">
        <config>
          <Option type="Map">
            <Option value="true" type="bool" name="AllowNull"/>
            <Option value="100" type="double" name="Max"/>
            <Option value="0" type="double" name="Min"/>
            <Option value="0" type="int" name="Precision"/>
            <Option value="10" type="double" name="Step"/>
            <Option value="SpinBox" type="QString" name="Style"/>
          </Option>
        </config>
      </editWidget>
    </field>
    <field configurationFlags="None" name="contexte">
      <editWidget type="ValueMap">
        <config>
          <Option type="Map">
            <Option type="List" name="map">
              <Option type="Map">
                <Option value="Tourbière boisée" type="QString" name="Tourbière boisée"/>
              </Option>
              <Option type="Map">
                <Option value="Autres" type="QString" name="Autres"/>
              </Option>
            </Option>
          </Option>
        </config>
      </editWidget>
    </field>
    <field configurationFlags="None" name="salarie_referent">
      <editWidget type="TextEdit">
        <config>
          <Option type="Map">
            <Option value="false" type="bool" name="IsMultiline"/>
            <Option value="false" type="bool" name="UseHtml"/>
          </Option>
        </config>
      </editWidget>
    </field>
    <field configurationFlags="None" name="commentaires">
      <editWidget type="TextEdit">
        <config>
          <Option type="Map">
            <Option value="false" type="bool" name="IsMultiline"/>
            <Option value="false" type="bool" name="UseHtml"/>
          </Option>
        </config>
      </editWidget>
    </field>
  </fieldConfiguration>
  <aliases>
    <alias field="id_cen" index="0" name=""/>
    <alias field="commune" index="1" name=""/>
    <alias field="dept" index="2" name=""/>
    <alias field="date_installation" index="3" name=""/>
    <alias field="modele_sonde" index="4" name=""/>
    <alias field="logiciel" index="5" name=""/>
    <alias field="frequence_sauvegarde" index="6" name=""/>
    <alias field="ligero" index="7" name=""/>
    <alias field="profondeur" index="8" name=""/>
    <alias field="contexte" index="9" name=""/>
    <alias field="salarie_referent" index="10" name=""/>
    <alias field="commentaires" index="11" name=""/>
  </aliases>
  <defaults>
    <default field="id_cen" applyOnUpdate="1" expression="concat(substr(maximum(&quot;id_cen&quot;),0,-1), format_number(substr(maximum(&quot;id_cen&quot;),7,8),0)+1)"/>
    <default field="commune" applyOnUpdate="0" expression=""/>
    <default field="dept" applyOnUpdate="0" expression=""/>
    <default field="date_installation" applyOnUpdate="0" expression=""/>
    <default field="modele_sonde" applyOnUpdate="0" expression=""/>
    <default field="logiciel" applyOnUpdate="0" expression=""/>
    <default field="frequence_sauvegarde" applyOnUpdate="0" expression=""/>
    <default field="ligero" applyOnUpdate="0" expression=""/>
    <default field="profondeur" applyOnUpdate="0" expression=""/>
    <default field="contexte" applyOnUpdate="0" expression=""/>
    <default field="salarie_referent" applyOnUpdate="0" expression=""/>
    <default field="commentaires" applyOnUpdate="0" expression=""/>
  </defaults>
  <constraints>
    <constraint field="id_cen" exp_strength="0" notnull_strength="1" constraints="3" unique_strength="1"/>
    <constraint field="commune" exp_strength="0" notnull_strength="0" constraints="0" unique_strength="0"/>
    <constraint field="dept" exp_strength="0" notnull_strength="0" constraints="0" unique_strength="0"/>
    <constraint field="date_installation" exp_strength="0" notnull_strength="0" constraints="0" unique_strength="0"/>
    <constraint field="modele_sonde" exp_strength="0" notnull_strength="0" constraints="0" unique_strength="0"/>
    <constraint field="logiciel" exp_strength="0" notnull_strength="0" constraints="0" unique_strength="0"/>
    <constraint field="frequence_sauvegarde" exp_strength="0" notnull_strength="0" constraints="0" unique_strength="0"/>
    <constraint field="ligero" exp_strength="0" notnull_strength="0" constraints="0" unique_strength="0"/>
    <constraint field="profondeur" exp_strength="0" notnull_strength="1" constraints="1" unique_strength="0"/>
    <constraint field="contexte" exp_strength="0" notnull_strength="1" constraints="1" unique_strength="0"/>
    <constraint field="salarie_referent" exp_strength="0" notnull_strength="0" constraints="0" unique_strength="0"/>
    <constraint field="commentaires" exp_strength="0" notnull_strength="0" constraints="0" unique_strength="0"/>
  </constraints>
  <constraintExpressions>
    <constraint field="id_cen" exp="" desc=""/>
    <constraint field="commune" exp="" desc=""/>
    <constraint field="dept" exp="" desc=""/>
    <constraint field="date_installation" exp="" desc=""/>
    <constraint field="modele_sonde" exp="" desc=""/>
    <constraint field="logiciel" exp="" desc=""/>
    <constraint field="frequence_sauvegarde" exp="" desc=""/>
    <constraint field="ligero" exp="" desc=""/>
    <constraint field="profondeur" exp="" desc=""/>
    <constraint field="contexte" exp="" desc=""/>
    <constraint field="salarie_referent" exp="" desc=""/>
    <constraint field="commentaires" exp="" desc=""/>
  </constraintExpressions>
  <expressionfields/>
  <attributeactions>
    <defaultAction key="Canvas" value="{00000000-0000-0000-0000-000000000000}"/>
  </attributeactions>
  <attributetableconfig sortExpression="" actionWidgetStyle="dropDown" sortOrder="0">
    <columns>
      <column hidden="0" width="-1" type="field" name="id_cen"/>
      <column hidden="0" width="-1" type="field" name="commune"/>
      <column hidden="0" width="-1" type="field" name="dept"/>
      <column hidden="0" width="-1" type="field" name="date_installation"/>
      <column hidden="0" width="-1" type="field" name="modele_sonde"/>
      <column hidden="0" width="-1" type="field" name="logiciel"/>
      <column hidden="0" width="-1" type="field" name="frequence_sauvegarde"/>
      <column hidden="0" width="-1" type="field" name="ligero"/>
      <column hidden="0" width="-1" type="field" name="profondeur"/>
      <column hidden="0" width="-1" type="field" name="contexte"/>
      <column hidden="0" width="-1" type="field" name="salarie_referent"/>
      <column hidden="0" width="-1" type="field" name="commentaires"/>
      <column hidden="1" width="-1" type="actions"/>
    </columns>
  </attributetableconfig>
  <conditionalstyles>
    <rowstyles/>
    <fieldstyles/>
  </conditionalstyles>
  <storedexpressions/>
  <editform tolerant="1"></editform>
  <editforminit/>
  <editforminitcodesource>0</editforminitcodesource>
  <editforminitfilepath></editforminitfilepath>
  <editforminitcode><![CDATA[# -*- coding: utf-8 -*-
"""
QGIS forms can have a Python function that is called when the form is
opened.

Use this function to add extra logic to your forms.

Enter the name of the function in the "Python Init function"
field.
An example follows:
"""
from qgis.PyQt.QtWidgets import QWidget

def my_form_open(dialog, layer, feature):
    geom = feature.geometry()
    control = dialog.findChild(QWidget, "MyLineEdit")
]]></editforminitcode>
  <featformsuppress>0</featformsuppress>
  <editorlayout>generatedlayout</editorlayout>
  <editable>
    <field editable="1" name="commentaires"/>
    <field editable="1" name="commune"/>
    <field editable="1" name="contexte"/>
    <field editable="1" name="date_installation"/>
    <field editable="1" name="dept"/>
    <field editable="1" name="frequence_sauvegarde"/>
    <field editable="0" name="id_cen"/>
    <field editable="1" name="ligero"/>
    <field editable="1" name="logiciel"/>
    <field editable="1" name="modele_sonde"/>
    <field editable="1" name="profondeur"/>
    <field editable="1" name="salarie_referent"/>
  </editable>
  <labelOnTop>
    <field labelOnTop="0" name="commentaires"/>
    <field labelOnTop="0" name="commune"/>
    <field labelOnTop="0" name="contexte"/>
    <field labelOnTop="0" name="date_installation"/>
    <field labelOnTop="0" name="dept"/>
    <field labelOnTop="0" name="frequence_sauvegarde"/>
    <field labelOnTop="0" name="id_cen"/>
    <field labelOnTop="0" name="ligero"/>
    <field labelOnTop="0" name="logiciel"/>
    <field labelOnTop="0" name="modele_sonde"/>
    <field labelOnTop="0" name="profondeur"/>
    <field labelOnTop="0" name="salarie_referent"/>
  </labelOnTop>
  <reuseLastValue>
    <field reuseLastValue="0" name="commentaires"/>
    <field reuseLastValue="0" name="commune"/>
    <field reuseLastValue="0" name="contexte"/>
    <field reuseLastValue="0" name="date_installation"/>
    <field reuseLastValue="0" name="dept"/>
    <field reuseLastValue="0" name="frequence_sauvegarde"/>
    <field reuseLastValue="0" name="id_cen"/>
    <field reuseLastValue="0" name="ligero"/>
    <field reuseLastValue="0" name="logiciel"/>
    <field reuseLastValue="0" name="modele_sonde"/>
    <field reuseLastValue="0" name="profondeur"/>
    <field reuseLastValue="0" name="salarie_referent"/>
  </reuseLastValue>
  <dataDefinedFieldProperties/>
  <widgets/>
  <previewExpression>"id_cen"</previewExpression>
  <mapTip></mapTip>
  <layerGeometryType>0</layerGeometryType>
</qgis>
