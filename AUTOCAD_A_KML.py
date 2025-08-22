import os,logging
from osgeo import ogr, osr
from qgis.PyQt.QtWidgets import QFileDialog, QMessageBox, QDialog, QVBoxLayout, QComboBox, QLabel, QPushButton
from pathlib import Path

class DXFtoKMLConverter:
    def __init__(self):
        # Definir el sistema de referencia espacial por defecto
        self.srs = osr.SpatialReference()
        self.srs.ImportFromEPSG(32719)
    def seleccionar_crs(self):
        dialog = QDialog()
        dialog.setWindowTitle("Seleccionar CRS")
        layout = QVBoxLayout()
        label = QLabel("Seleccione el EPSG del CRS:")
        layout.addWidget(label)
        self.crs_combo = QComboBox()
        # Añadir los códigos EPSG 32719 y 32718 (ya no es necesario editar ojo-ojo 😊)
        self.crs_combo.addItem("EPSG:32719 (WGS 84 / UTM zone 19S)", 32719)
        self.crs_combo.addItem("EPSG:32718 (WGS 84 / UTM zone 18S)", 32718)
        layout.addWidget(self.crs_combo)
        button = QPushButton("Aceptar")
        button.clicked.connect(dialog.accept)
        layout.addWidget(button)
        dialog.setLayout(layout)
        if dialog.exec_() == QDialog.Accepted:
            epsg_code = self.crs_combo.currentData()
            try:
                self.srs = osr.SpatialReference()
                self.srs.ImportFromEPSG(epsg_code)
                print(f"CRS seleccionado: EPSG:{epsg_code}")  # Añadir esta línea para depuración
            except Exception as e:
                logging.error(f'Error al importar el EPSG {epsg_code}: {str(e)}')
                QMessageBox.critical(None, "Error", f'Error al importar el EPSG {epsg_code}: {str(e)}')
    def validar_archivo(self, dwg_file):
        if not dwg_file.lower().endswith('.dxf'):
            raise ValueError(f"El archivo {dwg_file} no es un archivo DXF válido.")
    def abrir_archivo_dxf(self, dwg_file):
        dxf_ds = ogr.Open(dwg_file)
        if dxf_ds is None:
            raise Exception(f"No se pudo abrir el archivo {dwg_file}")
        print(f"Archivo DXF abierto: {dwg_file}")  # Añadir esta línea para depuración
        return dxf_ds
    def crear_archivo_kml(self, dwg_file):
        try:
            dwg_path = Path(dwg_file)
            base_name = dwg_path.stem  # Obtener el nombre base del archivo sin extensión
            print(f"Nombre base del archivo: {base_name}")  # Añadir esta línea para depuración
            kml_file = dwg_path.with_suffix('.kml')  # Cambiar la extensión a .kml
            print(f"Ruta del archivo KML: {kml_file}")  # Añadir esta línea para depuración
            kml_driver = ogr.GetDriverByName("KML")
            if kml_file.exists():
                kml_driver.DeleteDataSource(str(kml_file))
            kml_ds = kml_driver.CreateDataSource(str(kml_file))
            if kml_ds is None:
                raise Exception(f"No se pudo crear el archivo KML {kml_file}")
            return kml_ds, str(kml_file)
        except Exception as e:
            logging.error(f'Error creando el archivo KML: {str(e)}')
            raise
    def copiar_capas(self, dxf_ds, kml_ds):
        for i in range(dxf_ds.GetLayerCount()):
            dxf_layer = dxf_ds.GetLayerByIndex(i)
            print(f"Copiando capa: {dxf_layer.GetName()}")  # Añadir esta línea para depuración
            kml_layer = kml_ds.CreateLayer(dxf_layer.GetName(), self.srs, geom_type=dxf_layer.GetGeomType())
            kml_layer.CreateFields(dxf_layer.schema)
            for feature in dxf_layer:
                kml_layer.CreateFeature(feature)
    def procesar_archivo(self, dwg_file):
        try:
            self.validar_archivo(dwg_file)
            dxf_ds = self.abrir_archivo_dxf(dwg_file)
            kml_ds, kml_file = self.crear_archivo_kml(dwg_file)
            self.copiar_capas(dxf_ds, kml_ds)
            return f'<a href="file:///{kml_file}">El archivo {dwg_file} se ha convertido a {kml_file} exitosamente.</a>'
        except ValueError as ve:
            logging.error(f'Error de validación en el archivo {dwg_file}: {str(ve)}')
            return f'Error de validación en el archivo {dwg_file}: {str(ve)}'
        except Exception as e:
            logging.error(f'Error procesando el archivo {dwg_file}: {str(e)}')
            return f'Ocurrió un error procesando el archivo {dwg_file}: {str(e)}'
    def cargar_dxf_como_kml(self):
        try:
            # Seleccionar CRS
            self.seleccionar_crs()
            # Crear un diálogo para seleccionar los archivos
            file_dialog = QFileDialog()
            file_dialog.setFileMode(QFileDialog.ExistingFiles)
            file_dialog.setNameFilter("AutoCAD Files (*.dxf)")
            if file_dialog.exec_():
                dwg_files = file_dialog.selectedFiles()
                resultados = [self.procesar_archivo(dwg_file) for dwg_file in dwg_files]
                # Mostrar todos los mensajes juntos
                QMessageBox.information(None, "Resultados", "\n".join(resultados), QMessageBox.Ok, QMessageBox.Ok)
        except Exception as e:
            logging.error(f'Ocurrió un error inesperado: {str(e)}')
            QMessageBox.critical(None, "Error", f'Ocurrió un error inesperado: {str(e)}')
# Instanciar y usar la clase directamente
converter = DXFtoKMLConverter()
converter.cargar_dxf_como_kml()
#v4🌍🗺️