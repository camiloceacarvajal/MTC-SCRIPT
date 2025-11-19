# -*- coding: utf-8 -*-
"""
Script principal de cartografía MBN:
- Carga polígono MCT
- Carga variables desde carpeta
- Calcula intersecciones
- Carga plantilla QPT desde URL
- Ajusta layout, grilla, leyenda y variables
- Agrega capas de tiles (Google / NatGeo)
"""

import os
import glob
import requests
from qgis.PyQt.QtGui import QFont, QColor
from qgis.PyQt.QtWidgets import QFileDialog, QDockWidget
from qgis.PyQt.QtXml import QDomDocument
from qgis.PyQt.QtCore import QVariant
from qgis.utils import iface, plugins
from qgis import processing
from qgis.core import (
    QgsLayerTreeGroup,
    QgsLayoutItemMapGrid,
    QgsLayerTreeLayer,
    QgsUnitTypes,
    Qgis,
    QgsLayoutItemScaleBar,
    QgsDistanceArea,
    QgsFillSymbol,
    QgsSingleSymbolRenderer,
    QgsLayoutItemMap,
    QgsLegendStyle,
    QgsLayoutItemLabel,
    QgsCoordinateReferenceSystem,
    QgsLayoutSize,
    QgsProject,
    QgsMapLayer,
    QgsMapLayerLegendUtils,
    QgsVectorLayer,
    QgsPrintLayout,
    QgsReadWriteContext,
    QgsLayoutItemLegend,
    QgsLayoutPoint,
    QgsScaleBarSettings,
    QgsWkbTypes,
    QgsRenderContext,
    QgsInvertedPolygonRenderer,
    QgsField,
    QgsFeature,
    QgsVectorFileWriter,
    QgsRasterLayer,
    QgsCategorizedSymbolRenderer,
    QgsGraduatedSymbolRenderer
)

class LayerLoader:
    """
    Clase principal que administra:
      - Carga de polígono MCT
      - Carga de variables desde carpeta
      - Preparación de layout desde QPT
      - Intersecciones, leyenda y estilos
      - Capas de tiles y mapa de esquicio
    """
    # -------------------------------------------------------
    # 1. INICIALIZACIÓN Y UTILIDADES BÁSICAS
    # -------------------------------------------------------
    def __init__(self):
        """Inicializa la configuración base del cargador."""
        self.geopackage_layer = None
        self.selected_file_path = None
        self.target_crs = QgsCoordinateReferenceSystem('EPSG:5361')
        self.current_layout = None
        self.map_scale = 8000
    def add_layer_to_group(self, layer, group_name):
        """
        Agrega una capa a un grupo del árbol de capas.
        Crea el grupo si no existe.
        """
        root = QgsProject.instance().layerTreeRoot()
        group = root.findGroup(group_name)
        if not group:
            group = root.addGroup(group_name)

        QgsProject.instance().addMapLayer(layer, False)
        group.addLayer(layer)
    def find_layer_in_group(self, group_name, layer_name):
        """
        Busca una capa por nombre dentro de un grupo.
        - Primero busca coincidencia exacta
        - Luego, si no encuentra, usa coincidencia parcial (lowercase)
        """
        root = QgsProject.instance().layerTreeRoot()
        group = root.findGroup(group_name)
        if group is not None:
            # Búsqueda exacta
            for layer in group.findLayers():
                if layer.name() == layer_name:
                    return layer.layer()

            # Búsqueda parcial (case-insensitive)
            lname_lower = layer_name.lower()
            for layer in group.findLayers():
                if lname_lower in layer.name().lower():
                    return layer.layer()
        return None
    # -------------------------------------------------------
    # 2. CARGA DE POLÍGONO MCT (GPKG) Y PREPARACIÓN
    # -------------------------------------------------------
    def select_and_load_geopackage(self):
        """
        Selecciona un archivo vectorial (polígono MCT),
        reproyecta, disuelve si tiene más de un feature,
        calcula área para definir escala y prepara capa en memoria.
        """
        file_path = QFileDialog.getOpenFileName(
            None,
            'Seleccionar poligono MCT',
            '',
            'Archivos vectoriales (*.*)'
        )[0]

        if not file_path:
            print('No se seleccionó ningún archivo')
            return
        self.selected_file_path = file_path
        base_name = os.path.splitext(os.path.basename(file_path))[0]

        layer = QgsVectorLayer(file_path, base_name, 'ogr')
        if not layer.isValid():
            print(f'La capa no es válida! Error posible con el driver OGR para {file_path}')
            return

        # Eliminar campo "fid" si existe (para evitar problemas posteriores)
        if 'fid' in [f.name() for f in layer.fields()]:
            try:
                layer.dataProvider().deleteAttributes(
                    [layer.fields().indexFromName('fid')]
                )
                layer.updateFields()
            except Exception:
                pass

        # Reproyección al CRS objetivo
        if layer.crs() != self.target_crs:
            params = {
                'INPUT': layer,
                'TARGET_CRS': self.target_crs,
                'OUTPUT': 'memory:'
            }
            result = processing.run('qgis:reprojectlayer', params)
            layer = result['OUTPUT']
            layer.setName(base_name + "_proj")

        # Dissolve si hay más de un polígono
        if layer.featureCount() > 1:
            params = {
                'INPUT': layer,
                'FIELD': [],
                'OUTPUT': 'memory:'
            }
            result = processing.run('native:dissolve', params)
            layer = result['OUTPUT']
            layer.setName(base_name + "_dissolve")

        # Cálculo de área y definición de escala de mapa
        distance_area = QgsDistanceArea()
        distance_area.setSourceCrs(self.target_crs, QgsProject.instance().transformContext())
        distance_area.setEllipsoid(QgsProject.instance().ellipsoid())

        area_ha = 0
        for feat in layer.getFeatures():
            try:
                area_m2 = distance_area.measureArea(feat.geometry())
            except Exception:
                area_m2 = 0
            area_ha += area_m2 / 10000.0

        if area_ha > 3000:
            self.map_scale = 100000
        elif area_ha > 20:
            self.map_scale = 70000
        else:
            self.map_scale = 8000

        print(f"Área del polígono: {area_ha:.2f} ha (escala {self.map_scale})")

        # Copia a capa de memoria (para tener control total)
        mem_layer = QgsVectorLayer(
            "Polygon?crs={}".format(self.target_crs.authid()),
            base_name + "-",
            "memory"
        )
        prov = mem_layer.dataProvider()
        prov.addAttributes(layer.fields())
        mem_layer.updateFields()

        for feat in layer.getFeatures():
            prov.addFeature(feat)
        mem_layer.updateExtents()

        self.geopackage_layer = mem_layer

        # Simbología invertida (polígono recortado del fondo)
        base_symbol = QgsFillSymbol.createSimple({
            'color': '255,255,255,50',
            'outline_color': '#0059ff',
            'outline_width': '0.99'
        })
        base_renderer = QgsSingleSymbolRenderer(base_symbol)
        renderer = QgsInvertedPolygonRenderer(base_renderer)

        try:
            base_symbol.setColor(QColor.fromRgb(255, 255, 255))
            base_symbol.setOpacity(0.35)
        except Exception:
            pass

        self.geopackage_layer.setRenderer(renderer)
        self.add_layer_to_group(self.geopackage_layer, "Deslinde MCT")

        print("Capa de entrada preparada.")

        # Fuerza el canvas para centrar en el polígono
        iface.mapCanvas().setExtent(self.geopackage_layer.extent())
        iface.mapCanvas().refresh()

    # -------------------------------------------------------
    # 3. CARGA DE CAPAS DESDE CARPETA (VARIABLES)
    # -------------------------------------------------------

    def load_layers_from_selected_folder(self):
        """
        Pide una carpeta y carga todos los .gpkg,
        aplicando estilos qml si existen y ordenando:
        - puntos
        - líneas
        - polígonos
        """
        ruta_capas = QFileDialog.getExistingDirectory(
            None,
            "Seleccionar un directorio donde estan las variables"
        )
        extension_de_busqueda = ".gpkg"

        root = QgsProject.instance().layerTreeRoot()
        lista_archivos = [
            f.name for f in os.scandir(ruta_capas)
            if f.is_file() and f.name.endswith(extension_de_busqueda)
        ]

        for f in lista_archivos:
            file_name, file_ext = os.path.splitext(f)
            abs_path = os.path.join(ruta_capas, f)
            print(f)

            layer = QgsVectorLayer(abs_path, file_name, 'ogr')
            point_layers = []
            line_layers = []
            polygon_layers = []

            if layer.isValid():
                sublayers = layer.dataProvider().subLayers()
                for sublayer in sublayers:
                    name = sublayer.split('!!::!!')[1]
                    uri = f"{abs_path}|layername={name}"
                    sub_vlayer = QgsVectorLayer(uri, name, 'ogr')
                    sub_vlayer.setOpacity(0.9)

                    # Ruta genérica a estilos QML (ajústala a tu entorno)
                    qml_path = f"/ruta/a/los/archivos/qml/{name}.qml"
                    if os.path.exists(qml_path):
                        sub_vlayer.loadNamedStyle(qml_path)

                    geometry_type = sub_vlayer.geometryType()
                    if geometry_type == QgsWkbTypes.PointGeometry:
                        point_layers.append(sub_vlayer)
                    elif geometry_type == QgsWkbTypes.LineGeometry:
                        line_layers.append(sub_vlayer)
                    elif geometry_type == QgsWkbTypes.PolygonGeometry:
                        polygon_layers.append(sub_vlayer)

                # Orden deseado: puntos → líneas → polígonos
                ordered_layers = point_layers + line_layers + polygon_layers
                for lyr in ordered_layers:
                    self.add_layer_to_group(lyr, file_name)

    # -------------------------------------------------------
    # 4. CARGA DE PLANTILLA QPT DESDE URL Y MAPA PRINCIPAL
    # -------------------------------------------------------

    def load_template_from_url(self, template_urls):
        """
        Intenta descargar una plantilla QPT desde una lista de URLs.
        Usa la primera que funcione correctamente.
        """
        for template_url in template_urls:
            try:
                response = requests.get(template_url, verify=False, timeout=15)
            except Exception as e:
                print(f"Error descargando: {e}")
                continue

            if response.status_code == 200:
                try:
                    self.load_template_content(response.text)
                    print("Plantilla cargada OK.")
                    break
                except Exception as e:
                    print(f"Error al cargar contenido: {e}")
            else:
                print(f'Error status: {response.status_code}')

    def load_template_content(self, template_content):
        """
        Carga el contenido de una plantilla QPT (XML) en un QgsPrintLayout,
        reemplaza 'Mapa 3' por un nuevo mapa vinculado a la capa MCT
        y ajusta la escala, grilla, etiquetas y barras de escala.
        """
        myDocument = QDomDocument()
        if not myDocument.setContent(template_content):
            raise RuntimeError("No se pudo parsear QPT.")

        project = QgsProject.instance()
        manager = project.layoutManager()

        # Nombre único para el layout importado
        base_name = "ImportedTemplate"
        name = base_name
        counter = 1
        while manager.layoutByName(name):
            counter += 1
            name = f"{base_name}_{counter}"

        new_layout = QgsPrintLayout(project)
        new_layout.setName(name)

        try:
            ctx = QgsReadWriteContext()
            new_layout.loadFromTemplate(myDocument, ctx)
        except Exception as e:
            raise RuntimeError(f"loadFromTemplate falló: {e}")

        manager.addLayout(new_layout)
        self.current_layout = new_layout

        # Localizar 'Mapa 3' en la plantilla original
        map_item = new_layout.itemById('Mapa 3')
        if not map_item:
            raise RuntimeError("No se encontró 'Mapa 3'")

        # Crear nuevo mapa para tener control total
        new_map = QgsLayoutItemMap(new_layout)
        new_map.attemptMove(map_item.positionWithUnits())
        new_map.attemptResize(map_item.sizeWithUnits())
        new_layout.addLayoutItem(new_map)

        # CRS fijo de trabajo
        new_map.setCrs(self.target_crs)

        # Usar extent de la capa MCT si existe; si no, el del canvas
        if self.geopackage_layer:
            new_map.setExtent(self.geopackage_layer.extent())
        else:
            new_map.setExtent(iface.mapCanvas().extent())

        new_map.attemptResize(map_item.sizeWithUnits())
        new_map.setScale(getattr(self, 'map_scale', new_map.scale()))

        # Fuente base para varios elementos
        font = QFont()
        font.setPointSize(7)

        # Barra de escala principal
        scalebar = QgsLayoutItemScaleBar(new_layout)
        scalebar.setLinkedMap(new_map)

        if getattr(self, 'map_scale', 8000) <= 8900:
            scalebar.setUnits(QgsUnitTypes.DistanceMeters)
            scalebar.setNumberOfSegments(2)
            scalebar.setUnitsPerSegment(100.0)
            scalebar.setUnitLabel('m')
        else:
            scalebar.setUnits(QgsUnitTypes.DistanceKilometers)
            scalebar.setNumberOfSegments(2)
            scalebar.setUnitsPerSegment(1.0)
            scalebar.setUnitLabel('km')

        # Etiqueta numérica de escala
        scale_label = QgsLayoutItemLabel(new_layout)
        scale_label.setText(f"1:{new_map.scale():,.0f}")
        scale_label.setFont(font)
        scale_label.adjustSizeToText()

        # Etiqueta INFO ADMINISTRATIVO
        info_label = QgsLayoutItemLabel(new_layout)
        info_label.setId('INFO ADMINISTRATIVO')
        info_label.setText("Región: \nProvincia: \nComuna: \nLugar: ")

        # Buscar capa "Comunas" en "01. Contexto territorial" y obtener atributos
        root = QgsProject.instance().layerTreeRoot()
        group = root.findGroup("01. Contexto territorial")

        if group:
            layer = None
            for child in group.children():
                if isinstance(child, QgsLayerTreeLayer) and child.name() == "Comunas":
                    layer = child.layer()
                    break

            if layer and self.geopackage_layer:
                try:
                    original_selection = layer.selectedFeatureIds()
                    params = {
                        'INPUT': layer,
                        'PREDICATE': [0],
                        'INTERSECT': self.geopackage_layer,
                        'METHOD': 0
                    }
                    processing.run('native:selectbylocation', params)
                    selected_features = layer.selectedFeatures()

                    if selected_features:
                        feature = selected_features[0]

                        def get_attr(feat, name):
                            idx = feat.fields().indexFromName(name)
                            return feat.attribute(idx) if idx != -1 else ''

                        region = get_attr(feature, "REGION")
                        provincia = get_attr(feature, "PROVINCIA")
                        comuna = get_attr(feature, "COMUNA")

                        info_label.setText(
                            f"Región: {region}\nProvincia: {provincia}\nComuna: {comuna}\nLugar: "
                        )

                    layer.selectByIds(original_selection)
                except Exception:
                    pass

        # Ajustes visuales de la etiqueta de información
        font.setPointSize(10)
        info_label.setFont(font)
        info_label.adjustSizeToText()
        info_label.attemptResize(
            QgsLayoutSize(45.0, 30.0, QgsUnitTypes.LayoutMillimeters)
        )
        info_label.attemptMove(
            QgsLayoutPoint(162.0, 6.4, QgsUnitTypes.LayoutMillimeters)
        )
        new_layout.addLayoutItem(info_label)

        # Configuración visual de la barra de escala principal
        scalebar.setFont(font)
        scalebar.attemptMove(
            QgsLayoutPoint(157.5, 256.0, QgsUnitTypes.LayoutMillimeters)
        )
        scalebar.setSegmentSizeMode(QgsScaleBarSettings.SegmentSizeMode.SegmentSizeFitWidth)
        scalebar.setNumberOfSegmentsLeft(0)
        scalebar.setNumberOfSegments(2)
        scalebar.setMinimumBarWidth(30)
        scalebar.setMaximumBarWidth(40)
        new_layout.addLayoutItem(scalebar)

        # Configuración de la grilla del mapa
        grid = new_map.grid()
        current_scale = getattr(self, 'map_scale', 8000)

        if current_scale >= 100000:
            grid.setIntervalX(5000.0)
            grid.setIntervalY(5000.0)
        elif current_scale >= 70000:
            grid.setIntervalX(2000.0)
            grid.setIntervalY(2000.0)
        elif current_scale == 8000:
            if self.target_crs.isGeographic():
                grid.setIntervalX(0.008)
                grid.setIntervalY(0.008)
            else:
                grid.setIntervalX(800.0)
                grid.setIntervalY(800.0)
        else:
            grid.setIntervalX(1000.0)
            grid.setIntervalY(1000.0)

        grid.setUnits(QgsLayoutItemMapGrid.DynamicPageSizeBased)
        grid.setMinimumIntervalWidth(50)
        grid.setMaximumIntervalWidth(100)
        grid.setStyle(QgsLayoutItemMapGrid.FrameAnnotationsOnly)
        grid.setAnnotationEnabled(True)
        grid.setAnnotationPrecision(0)

        font_grid = QFont()
        font_grid.setPointSize(6)
        grid.setAnnotationFont(font_grid)

        # Anotaciones en los 4 lados
        grid.setAnnotationPosition(QgsLayoutItemMapGrid.OutsideMapFrame, QgsLayoutItemMapGrid.Left)
        grid.setAnnotationDirection(QgsLayoutItemMapGrid.Vertical, QgsLayoutItemMapGrid.Left)
        grid.setAnnotationPosition(QgsLayoutItemMapGrid.OutsideMapFrame, QgsLayoutItemMapGrid.Right)
        grid.setAnnotationDirection(QgsLayoutItemMapGrid.Vertical, QgsLayoutItemMapGrid.Right)
        grid.setAnnotationPosition(QgsLayoutItemMapGrid.OutsideMapFrame, QgsLayoutItemMapGrid.Bottom)
        grid.setAnnotationDirection(QgsLayoutItemMapGrid.Horizontal, QgsLayoutItemMapGrid.Bottom)
        grid.setAnnotationPosition(QgsLayoutItemMapGrid.OutsideMapFrame, QgsLayoutItemMapGrid.Top)
        grid.setAnnotationDirection(QgsLayoutItemMapGrid.Horizontal, QgsLayoutItemMapGrid.Top)

        # Barra de escala numérica (estilo "Numeric")
        scalebar_numerica = QgsLayoutItemScaleBar(new_layout)
        scalebar_numerica.setStyle('Numeric')
        scalebar_numerica.setLinkedMap(new_map)
        scalebar_numerica.setUnits(QgsUnitTypes.DistanceMeters)
        scalebar_numerica.setNumberOfSegments(2)
        scalebar_numerica.setUnitsPerSegment(100.0)
        scalebar_numerica.setUnitLabel('m')
        scalebar_numerica.attemptMove(
            QgsLayoutPoint(178.2, 270.5, QgsUnitTypes.LayoutMillimeters)
        )
        scalebar_numerica.setFont(font_grid)
        new_layout.addLayoutItem(scalebar_numerica)

        # Eliminar el mapa original de la plantilla
        try:
            new_layout.removeLayoutItem(map_item)
        except Exception:
            pass

        # Refrescar mapa nuevo
        try:
            new_map.updateBoundingRect()
            new_map.refresh()
        except Exception:
            pass

        print(f"Plantilla cargada: '{new_layout.name()}'.")

    # -------------------------------------------------------
    # 5. VISIBILIDAD DE GRUPOS Y LEYENDA
    # -------------------------------------------------------

    def hide_complementary_variables_group(self):
        """
        Oculta el grupo "00. Variables complementarias"
        completo en el árbol de capas.
        """
        root = QgsProject.instance().layerTreeRoot()
        for group in root.children():
            if isinstance(group, QgsLayerTreeGroup) and group.name() == "00. Variables complementarias":
                group.setItemVisibilityChecked(False)

    def update_group_visibility(self):
        """
        Recorre todos los grupos y colapsa aquellos que
        no tienen capas visibles.
        """
        root = QgsProject.instance().layerTreeRoot()
        for group in root.children():
            if isinstance(group, QgsLayerTreeGroup):
                visible_layers = [
                    layer for layer in group.children()
                    if layer.isVisible()
                ]
                if not visible_layers:
                    group.setExpanded(False)

    def update_legend(self, intersecting_layers):
        """
        Crea y configura una leyenda en el layout "1",
        mostrando solo las capas listadas en intersecting_layers
        (más la capa MCT al inicio).
        """
        layout_name = '1'
        layout = QgsProject.instance().layoutManager().layoutByName(layout_name)
        if not layout:
            return

        legend_id = 'Leyenda'
        legend = QgsLayoutItemLegend(layout)
        legend.setId(legend_id)
        legend.setTitle('Leyenda')
        layout.addLayoutItem(legend)
        legend.attemptMove(QgsLayoutPoint(44.7, 254.2))
        legend.setColumnCount(2)
        legend.setAutoUpdateModel(False)

        # Asegurar que la capa MCT aparece en la leyenda
        if self.geopackage_layer:
            master_name = self.geopackage_layer.name()
            if master_name not in intersecting_layers:
                intersecting_layers.insert(0, master_name)

        # Ajustes de fuente para leyenda “grande”
        if len(intersecting_layers) > 1:
            group_font = QFont("Arial", 7)
            group_font.setBold(True)
            title_font = QFont("Arial", 12)

            legend.setStyleFont(QgsLegendStyle.Title, title_font)
            legend.setSymbolHeight(5)
            legend.setSymbolWidth(5)
            legend.setStyleFont(QgsLegendStyle.Group, group_font)

            subgroup_font = QFont("Arial", 6)
            legend.setStyleFont(QgsLegendStyle.Subgroup, subgroup_font)

            symbol_label_font = QFont("Arial", 6)
            legend.setStyleFont(QgsLegendStyle.SymbolLabel, symbol_label_font)

        root = QgsProject.instance().layerTreeRoot()
        model = legend.model()
        group = model.rootGroup()
        group.clear()

        # Recorremos todos los grupos del proyecto para armar la leyenda
        for group_node in root.children():
            if not isinstance(group_node, QgsLayerTreeGroup):
                continue

            # Excepción: saltar "Mapa Geológico" en "00. Variables complementarias"
            if group_node.name() == "00. Variables complementarias" and any(
                layer_node.name() == "Mapa Geológico"
                for layer_node in group_node.children()
            ):
                continue

            for layer_node in group_node.findLayers():
                layer_name = layer_node.name()

                # Omitir "Comunas" dentro de "01. Contexto territorial"
                if group_node.name() == "01. Contexto territorial" and layer_name == "Comunas":
                    continue

                if layer_name in intersecting_layers:
                    parent_group = layer_node.parent()
                    legend_group = group.findGroup(parent_group.name())
                    if not legend_group:
                        legend_group = group.addGroup(parent_group.name())
                    legend_group.addLayer(layer_node.layer())

        legend.adjustBoxSize()
        print("Leyenda OK.")

    # -------------------------------------------------------
    # 6. INTERSECCIONES Y ACTIVACIÓN DE CAPAS
    # -------------------------------------------------------

    def find_intersections_v5(self, intersection_types):
        """
        Busca intersecciones entre la capa MCT y todas las capas vectoriales
        del proyecto usando 'selectbylocation'. Devuelve lista de nombres
        de capas que intersectan y las deja visibles en el árbol.
        """
        intersecting_layers = []
        root = QgsProject.instance().layerTreeRoot()

        predicate_map = {
            'intersects': 0,
            'touches': 1,
            'contains': 2,
            'equals': 3,
            'overlaps': 4,
            'within': 5,
            'crosses': 6
        }
        predicates = [predicate_map[t] for t in intersection_types]

        if not self.geopackage_layer:
            return intersecting_layers

        # Limpiar selección de la capa MCT
        try:
            self.geopackage_layer.removeSelection()
        except Exception:
            pass

        # Recorre todas las capas del proyecto
        for layer in QgsProject.instance().mapLayers().values():
            if not isinstance(layer, QgsVectorLayer):
                continue
            if layer.id() == self.geopackage_layer.id():
                continue

            try:
                layer.removeSelection()
            except Exception:
                pass

            intersect_layer_for_select = self.geopackage_layer

            # Reproyectar MCT al CRS de la capa destino si es distinto
            try:
                if self.geopackage_layer.crs() != layer.crs():
                    params = {
                        'INPUT': self.geopackage_layer,
                        'TARGET_CRS': layer.crs(),
                        'OUTPUT': 'memory:'
                    }
                    res = processing.run('qgis:reprojectlayer', params)
                    intersect_layer_for_select = res['OUTPUT']
            except Exception:
                intersect_layer_for_select = self.geopackage_layer

            # Select by location
            try:
                params_sel = {
                    'INPUT': layer,
                    'PREDICATE': predicates,
                    'INTERSECT': intersect_layer_for_select,
                    'METHOD': 0
                }
                processing.run('native:selectbylocation', params_sel)
            except Exception:
                pass

            try:
                sel_count = layer.selectedFeatureCount()
            except Exception:
                sel_count = 0

            layer_node = root.findLayer(layer.id())

            if sel_count > 0:
                intersecting_layers.append(layer.name())
                if layer_node:
                    layer_node.setItemVisibilityChecked(True)
                    parent_group = layer_node.parent()
                    if parent_group:
                        parent_group.setItemVisibilityChecked(True)
            else:
                if layer_node:
                    layer_node.setItemVisibilityChecked(False)

        return intersecting_layers

    # -------------------------------------------------------
    # 7. TILES (GOOGLE / NATGEO) Y MAPA DE ESQUICIO
    # -------------------------------------------------------

    def add_tile_layers_to_project(self):
        """
        Agrega dos capas de tiles (Google Satellite y NatGeo World Map)
        debajo del grupo de variables principales.
        """
        tile_layer_url_1 = (
            "type=xyz&url=https://mt1.google.com/vt/lyrs%3Ds%26x%3D{x}%26y%3D{y}%26z%3D{z}"
            "&zmax=20&zmin=0&crs=EPSG3857"
        )
        tile_layer_url_2 = (
            "https://services.arcgisonline.com/ArcGIS/rest/services/"
            "NatGeo_World_Map/MapServer/tile/{z}/{y}/{x}"
        )

        tile_layer_1 = QgsRasterLayer(
            f"type=xyz&url={tile_layer_url_1}", "Google Satellite", "wms"
        )
        tile_layer_2 = QgsRasterLayer(
            f"type=xyz&url={tile_layer_url_2}", "NatGeo World Map", "wms"
        )

        if tile_layer_1.isValid() and tile_layer_2.isValid():
            root = QgsProject.instance().layerTreeRoot()

            group_names = [
                "09. Variables de energia",
                "08. Variables de minería",
                "07. Variables de turismo y patrimonio",
                "06. Variables de riesgo",
                "05. Variables indígenas",
                "04. Variables de conservación",
                "03. Variables ambientales",
                "02. Instrumentos de Planificación Territorial",
                "01. Contexto territorial"
            ]
            group = None
            for group_name in group_names:
                group = root.findGroup(group_name)
                if group:
                    break

            if group:
                group_index = root.children().index(group)
                QgsProject.instance().addMapLayer(tile_layer_1, False)
                root.insertLayer(group_index + 1, tile_layer_1)
                QgsProject.instance().addMapLayer(tile_layer_2, False)
                root.insertLayer(group_index + 2, tile_layer_2)
            else:
                QgsProject.instance().addMapLayer(tile_layer_1)
                QgsProject.instance().addMapLayer(tile_layer_2)

            tile_layer_node_1 = root.findLayer(tile_layer_1.id())
            tile_layer_node_2 = root.findLayer(tile_layer_2.id())

            if tile_layer_node_2:
                tile_layer_node_2.setItemVisibilityChecked(False)

            return tile_layer_1, tile_layer_2
        else:
            return None, None

    def update_sketch_map(self, tile_layer):
        """
        Reemplaza el ítem 'Mapa esquicio' en el layout '1' con un nuevo mapa,
        centrado en la capa MCT (extent) y opcionalmente mostrando la capa de tiles.
        """
        layout_name = '1'
        layout = QgsProject.instance().layoutManager().layoutByName(layout_name)
        if not layout:
            return

        map_item = layout.itemById('Mapa esquicio')
        if not map_item:
            return

        new_map = QgsLayoutItemMap(layout)
        new_map.attemptMove(map_item.positionWithUnits())
        new_map.attemptResize(map_item.sizeWithUnits())
        layout.addLayoutItem(new_map)
        new_map.setCrs(self.target_crs)

        # Extent basado en MCT (fallback al canvas)
        if self.geopackage_layer:
            new_map.setExtent(self.geopackage_layer.extent())
        else:
            new_map.setExtent(iface.mapCanvas().extent())

        new_map.attemptResize(map_item.sizeWithUnits())
        new_map.setScale(4000000)

        # Capas visibles en el mapa de esquicio
        if tile_layer and tile_layer.isValid():
            new_map.setLayers([self.geopackage_layer, tile_layer])
        else:
            new_map.setLayers([self.geopackage_layer])

        # Centrar el ítem 'POLIGONO DE UBICACION' sobre el nuevo mapa
        polygon_item = layout.itemById('POLIGONO DE UBICACION')
        if polygon_item:
            x = (
                new_map.positionWithUnits().x()
                + new_map.sizeWithUnits().width() / 2
                - polygon_item.sizeWithUnits().width() / 2
            )
            y = (
                new_map.positionWithUnits().y()
                + new_map.sizeWithUnits().height() / 2
                - polygon_item.sizeWithUnits().height() / 2
            )
            polygon_item.attemptMove(QgsLayoutPoint(x, y))

        new_map.setKeepLayerSet(False)

        # Eliminar mapa de esquicio original
        layout.removeLayoutItem(map_item)

    # -------------------------------------------------------
    # 8. FILTRADO DE CATEGORÍAS EN RENDERERS / LEYENDA
    # -------------------------------------------------------

    def check_layer_and_categories(self, layer_name):
        """
        Dada una capa por nombre, retorna la lista de valores
        de categorías cuya propiedad renderState() == False,
        para poder ocultarlas en la leyenda del layout.
        """
        all_layers = QgsProject.instance().mapLayersByName(layer_name)
        if not all_layers:
            return []

        map_layer = all_layers[0]

        if map_layer.renderer().type() == 'categorizedSymbol':
            return [
                cat.value()
                for cat in map_layer.renderer().categories()
                if not cat.renderState()
            ]
        else:
            return []

    def check_layout_and_item(self, layout_name, item_id, layer_name, categories_to_remove):
        """
        Revisa un layout y un ítem de tipo leyenda, y oculta
        las categorías indicadas para la capa dada.
        """
        manager = QgsProject.instance().layoutManager()
        layout = manager.layoutByName(layout_name)
        if not layout:
            return

        legend = layout.itemById(item_id)
        if not legend or not isinstance(legend, QgsLayoutItemLegend):
            return

        target_layer = next(
            (
                layer.layer()
                for layer in legend.model().rootGroup().findLayers()
                if layer.name() == layer_name
            ),
            None
        )

        if target_layer and target_layer.renderer().type() == 'categorizedSymbol':
            root = legend.model().rootGroup().findLayer(target_layer)
            if root is not None:
                nodes = legend.model().layerLegendNodes(root)
                indexes_to_remove = [
                    nodes.index(node)
                    for node in nodes
                    if node.data(0) in categories_to_remove
                ]
                QgsMapLayerLegendUtils.setLegendNodeOrder(
                    root,
                    [i for i in range(len(nodes)) if i not in indexes_to_remove]
                )
                legend.model().refreshLayerLegend(root)

    def process_layers(self, layer_names, layout_name, item_id):
        """
        Aplica check_layout_and_item para una o varias capas,
        escondiendo en la leyenda las categorías con renderState=False.
        """
        if isinstance(layer_names, str):
            layer_names = [layer_names]

        for layer_name in layer_names:
            categories_to_remove = self.check_layer_and_categories(layer_name)
            self.check_layout_and_item(layout_name, item_id, layer_name, categories_to_remove)

    # -------------------------------------------------------
    # 9. ACTUALIZACIÓN DE RENDERERS SEGÚN SELECCIÓN
    # -------------------------------------------------------

    def update_renderer(self, layer_names, attribute_names):
        """
        Para cada capa categorizada/graduada, crea un renderer clonado
        donde sólo se activan (renderState=True) las categorías
        cuyos valores aparecen en las features seleccionadas.
        """
        for layer_name, attribute_name in zip(layer_names, attribute_names):
            layer_categorizada = self.find_layer_in_group("06. Variables de riesgo", layer_name)

            if not layer_categorizada:
                all_matches = [
                    l for l in QgsProject.instance().mapLayers().values()
                    if layer_name.lower() in l.name().lower()
                ]
                if all_matches:
                    layer_categorizada = all_matches[0]
                else:
                    continue
            old_renderer = layer_categorizada.renderer()
            if isinstance(old_renderer, (QgsCategorizedSymbolRenderer, QgsGraduatedSymbolRenderer)):
                new_renderer = old_renderer.clone()
                new_renderer.deleteAllCategories()
                feature_values = set()
                for feat in layer_categorizada.selectedFeatures():
                    idx = feat.fields().indexFromName(attribute_name)
                    if idx != -1:
                        feature_values.add(feat.attribute(idx))
                for cat in old_renderer.categories():
                    cat.setRenderState(cat.value() in feature_values)
                    new_renderer.addCategory(cat)
                layer_categorizada.setRenderer(new_renderer)
                layer_categorizada.triggerRepaint()
    # -------------------------------------------------------
    # 10. UTILIDADES VARIAS (VERSIÓN Y CAPAS CONTEXTO)
    # -------------------------------------------------------
    def obtener_version_qgis(self):
        """Imprime la versión de QGIS en la consola."""
        version = Qgis.QGIS_VERSION
        print(f"QGIS Version: {version}")
    def apagar_comunas(self):
        """
        Apaga la visibilidad de la capa 'Comunas'
        dentro del grupo '01. Contexto territorial'.
        """
        root = QgsProject.instance().layerTreeRoot()
        group = root.findGroup("01. Contexto territorial")
        if group:
            for child in group.children():
                if isinstance(child, QgsLayerTreeLayer) and child.name() == "Comunas":
                    child.setItemVisibilityChecked(False)
                    break
# =======================================================
# FLUJO PRINCIPAL
# =======================================================
layer_loader = LayerLoader()
# 1) Carga polígono MCT y variables desde carpeta
layer_loader.select_and_load_geopackage()
layer_loader.load_layers_from_selected_folder()
# 2) Busca intersecciones (por defecto 'intersects')
intersecting_layers = layer_loader.find_intersections_v5(['intersects'])
# 3) Carga plantilla desde URLs (orden de prioridad)
template_urls = [
    "https://gitlab.com/camiloceacarvajal1/plantilla_MBN/-/raw/main/22.qpt?ref_type=heads",
    "https://raw.githubusercontent.com/camiloceacarvajal/PLANTILLA-MBN/main/21.qpt"
]
layer_loader.load_template_from_url(template_urls)
# 4) Actualiza leyenda en layout "1" según capas intersectadas
layer_loader.update_legend(intersecting_layers)
# 5) Agrega capas de tiles y actualiza mapa de esquicio
tile_layer_1, tile_layer_2 = layer_loader.add_tile_layers_to_project()
layer_loader.update_sketch_map(tile_layer_2)
# 6) Abrir el diseñador de layouts al final (refresco visual)
try:
    designer = iface.openLayoutDesigner(
        QgsProject.instance().layoutManager().layoutByName('1')
    )
    designer.view().setZoomLevel(0.7)
    designer.view().refresh()
except Exception:
    pass
# 7) Aplicar filtros de renderer a capas de riesgo
layer_names = [
    "Riesgo de incendios forestales",
    "Cartas de inundación por tsunami",
    "Áreas de peligro por actividad volcánica: áreas de peligro"
]
attribute_names = [
    "Riesgo ",
    "Name",
    "peligro"
]
layer_loader.update_renderer(layer_names, attribute_names)
# 8) Ajustar visibilidad de grupos y procesar leyenda por categorías
layer_loader.update_group_visibility()
layer_loader.process_layers(layer_names, "1", "Leyenda")
layer_loader.hide_complementary_variables_group()
# 9) Info de versión y apagar "Comunas"
layer_loader.obtener_version_qgis()
layer_loader.apagar_comunas()
# 10) Cerrar consola de Python para limpiar la interfaz
try:
    iface.mainWindow().findChild(QDockWidget, 'PythonConsole').close()
except Exception:
    pass
# Version C (Definitiva - Extent Fijo) - 30-12-2025
