# -*- coding: utf-8 -*-
import os, re, unicodedata, tempfile, webbrowser, datetime, textwrap
from collections import OrderedDict
from qgis.utils import iface
from qgis.core import Qgis, QgsProject, QgsLayerTreeGroup, QgsLayerTreeLayer, QgsMapLayer
from qgis import processing

# ==========================================
# 1. CONFIGURACIÓN Y DATOS
# ==========================================
TITULO_ID = "UC-2025-B10.0" # Versión 10
PARAMS_TECNICOS = {
    "fecha_datos": "Noviembre 2025",
    "fuente_geo": "Catastro MBN, IDE Chile, MMA, IDE Minvu, IDE ENERGIA, Sitio Conadi, Portal Geomin y otras IDES y Portales Oficiales.",
}
PERSONAL_CATASTRO = [
    {"nombre": "Álvaro Cortez Lozano", "cargo": "Encargado de Catastro", "region": "Arica y Parinacota"},
    {"nombre": "Roberto Barraza Valdivia", "cargo": "Analista de Catastro", "region": "Arica y Parinacota"},
    {"nombre": "Giorgio Escarate Parra", "cargo": "Analista de Catastro", "region": "Arica y Parinacota"},
    {"nombre": "Jorge Farfán Farfán", "cargo": "Encargado de Catastro", "region": "Tarapacá"},
    {"nombre": "Cristóbal Loayza Herrera", "cargo": "Analista de Catastro", "region": "Tarapacá"},
    {"nombre": "Daniel Cabezas Monsalves", "cargo": "Analista de Catastro", "region": "Tarapacá"},
    {"nombre": "Kiang Lau Gajardo", "cargo": "Analista de Catastro", "region": "Tarapacá"},
    {"nombre": "Rodrigo Godoy Rodriguez", "cargo": "Analista de Catastro", "region": "Tarapacá"},
    {"nombre": "Aldo Contreras Zarate", "cargo": "Analista de Catastro", "region": "Tarapacá"},
    {"nombre": "Vianca Estay Páez", "cargo": "Encargada de Catastro", "region": "Antofagasta"},
    {"nombre": "Marcela Carvajal Irarrazabal", "cargo": "Analista de Catastro", "region": "Antofagasta"},
    {"nombre": "Marta Cabello Trujillo", "cargo": "Analista de Catastro", "region": "Antofagasta"},
    {"nombre": "Gerson Saul Quezada Araya", "cargo": "Analista de Catastro", "region": "Antofagasta"},
    {"nombre": "Soledad Zuleta Cruz", "cargo": "Analista de Catastro", "region": "Antofagasta"},
    {"nombre": "José Andrés Jara Salas", "cargo": "Analista de Catastro", "region": "Antofagasta"},
    {"nombre": "Natalia Carolina Henriquez Muñoz", "cargo": "Analista de Catastro", "region": "Antofagasta"},
    {"nombre": "Nicolas Hernan Lara Cortes", "cargo": "Analista de Catastro", "region": "Antofagasta"},
    {"nombre": "Jeannette Zamora Gonzalez", "cargo": "Encargada de Catastro", "region": "Atacama"},
    {"nombre": "Dominique Seguich Albarracin", "cargo": "Analista de Catastro", "region": "Atacama"},
    {"nombre": "Ignacio Juárez Picón", "cargo": "Analista de Catastro", "region": "Atacama"},
    {"nombre": "Rene Toro Barrera", "cargo": "Analista de Catastro", "region": "Atacama"},
    {"nombre": "Jessica Castillo Diaz", "cargo": "Analista de Catastro", "region": "Atacama"},
    {"nombre": "Paula Sabrina Mondaca Fritis", "cargo": "Analista de Catastro", "region": "Atacama"},
    {"nombre": "Claudia Luisa Villacorta López", "cargo": "Analista de Catastro", "region": "Atacama"},
    {"nombre": "Marcelo Fuenzalida Gonzalez", "cargo": "Encargado de Catastro", "region": "Coquimbo"},
    {"nombre": "Patricia Olivares Tejada", "cargo": "Analista de Catastro", "region": "Coquimbo"},
    {"nombre": "Miguel Alvarez Jofre", "cargo": "Analista de Catastro", "region": "Coquimbo"},
    {"nombre": "Jose Jirón Encina", "cargo": "Encargado de Catastro", "region": "Valparaíso"},
    {"nombre": "Gustavo Gutiérrez Pinto", "cargo": "Analista de Catastro", "region": "Valparaíso"},
    {"nombre": "Pablo Arevalo", "cargo": "Analista de Catastro", "region": "Valparaíso"},
    {"nombre": "Isaias Barraza Ramos", "cargo": "Analista de Catastro", "region": "Valparaíso"},
    {"nombre": "Eliana Aranda Alzamora", "cargo": "Analista de Catastro", "region": "Valparaíso"},
    {"nombre": "Luis Guillermo Álvarez Guzman", "cargo": "Encargado de Catastro", "region": "Metropolitana"},
    {"nombre": "Ximena Patricia Salas Salas", "cargo": "Analista de Catastro", "region": "Metropolitana"},
    {"nombre": "Cristina Acevedo Meléndez", "cargo": "Analista de Catastro", "region": "Metropolitana"},
    {"nombre": "Cristóbal Mena Muñoz", "cargo": "Encargado de Catastro", "region": "O'Higgins"},
    {"nombre": "Celeste Angelina Escobar Avila", "cargo": "Encargada de Catastro", "region": "Maule"},
    {"nombre": "Rocio Pilar Rojas Gonzalez", "cargo": "Analista de Catastro", "region": "Maule"},
    {"nombre": "Rodolfo Araya Gonzalez", "cargo": "Analista de Catastro", "region": "Maule"},
    {"nombre": "Valeria Bastias Huaiquil", "cargo": "Encargada de Catastro", "region": "Ñuble"},
    {"nombre": "Gonzalo Llanos Plaza", "cargo": "Analista de Catastro", "region": "Ñuble"},
    {"nombre": "Carlos Alfredo Martinez Catalán", "cargo": "Encargado de Catastro", "region": "Biobío"},
    {"nombre": "Julio Carvajal Vásquez", "cargo": "Analista de Catastro", "region": "Biobío"},
    {"nombre": "Verónica Sepúlveda Fernández", "cargo": "Analista de Catastro", "region": "Biobío"},
    {"nombre": "Loreto Pérez Fernández", "cargo": "Analista de Catastro", "region": "Biobío"},
    {"nombre": "Oscar Godoy Reyes", "cargo": "Encargado de Catastro", "region": "Araucanía"},
    {"nombre": "Moises Aaron Quilodran Antipil", "cargo": "Analista de Catastro", "region": "Araucanía"},
    {"nombre": "Luis Alejandro Ortega Jerez", "cargo": "Analista de Catastro", "region": "Araucanía"},
    {"nombre": "Luis Felipe Fernandez Sinning", "cargo": "Analista de Catastro", "region": "Araucanía"},
    {"nombre": "Diego Enrique Sanchez Fuentes", "cargo": "Analista de Catastro", "region": "Araucanía"},
    {"nombre": "Ricardo Rioseco Gutiérrez", "cargo": "Encargado de Catastro", "region": "Los Ríos"},
    {"nombre": "Arnaldo Vergara Ferrada", "cargo": "Analista de Catastro", "region": "Los Ríos"},
    {"nombre": "Egar Aguilera Vejar", "cargo": "Analista de Catastro", "region": "Los Ríos"},
    {"nombre": "Jorge Calvo Walters", "cargo": "Analista de Catastro", "region": "Los Lagos"},
    {"nombre": "Erwin Alarcon Monge", "cargo": "Analista de Catastro", "region": "Los Lagos"},
    {"nombre": "Danilo Andrés Soto Gonzalez", "cargo": "Analista de Catastro", "region": "Los Lagos"},
    {"nombre": "Matías Wood Osses", "cargo": "Analista de Catastro", "region": "Los Lagos"},
    {"nombre": "Cristian Araya Tapia", "cargo": "Analista de Catastro", "region": "Los Lagos"},
    {"nombre": "Raúl Morell Carreño", "cargo": "Analista de Catastro", "region": "Los Lagos"},
    {"nombre": "Julio Vejar Vejar", "cargo": "Analista de Catastro", "region": "Los Lagos"},
    {"nombre": "Jaime Alvarado Guzman", "cargo": "Analista de Catastro", "region": "Los Lagos"},
    {"nombre": "Fernando Andrade Vilaro", "cargo": "Analista de Catastro", "region": "Los Lagos"},
    {"nombre": "Sandra Martinez Parra", "cargo": "Encargada de Catastro", "region": "Los Lagos"},
    {"nombre": "Mauro Echeverría Huaquer", "cargo": "Encargado de Catastro", "region": "Aysén"},
    {"nombre": "Rodolfo Alexis Rojas Landaeta", "cargo": "Analista de Catastro", "region": "Aysén"},
    {"nombre": "Gabriel Rozas Poblete", "cargo": "Analista de Catastro", "region": "Aysén"},
    {"nombre": "Ivan Sasso Godoy", "cargo": "Encargado de Catastro", "region": "Magallanes"},
    {"nombre": "Ricardo Vivar Navarro", "cargo": "Analista de Catastro", "region": "Magallanes"},
    {"nombre": "Samuel Isaac Huentecol Cheuquepan", "cargo": "Analista de Catastro", "region": "Magallanes"},
    {"nombre": "Marco Villegas Salas", "cargo": "Analista de Estudios Territoriales", "region": "Nivel Central"},
    {"nombre": "Camilo Cea Carvajal", "cargo": "Analista de Estudios Territoriales", "region": "Nivel Central"},
    {"nombre": "Gloria Inzunza Rivera", "cargo": "Encargada de Estudios Territoriales", "region": "Nivel Central"},
]
# ==========================================
# 2. UTILIDADES
# ==========================================
def norm(s):
    return re.sub(
        r"\s+"," ",
        "".join(
            c for c in unicodedata.normalize("NFKD", str(s).lower())
            if not unicodedata.combining(c)
        )
    ).strip()
def es_basemap(layer):
    n = norm(layer.name())
    if layer.type() != QgsMapLayer.VectorLayer:
        return True
    return any(k in n for k in ["google","satellite","natgeo","xyz","wms","osm","world map","basemap"])
def get_layer_dir(layer):
    try:
        src = layer.dataProvider().dataSourceUri()
    except:
        src = getattr(layer,"source",lambda:"")()
    if "|layername=" in src: src = src.split("|layername=")[0]
    if os.path.isfile(src): return os.path.dirname(src)
    m = re.search(r"([A-Za-z]:[\\/].+?\.(gpkg|shp|geojson|sqlite))", src)
    if m and os.path.isfile(m.group(1)): return os.path.dirname(m.group(1))
    return None
# ==========================================
# 3. DETECCIÓN DE CAPA BASE
# ==========================================
def detectar_capa_base():
    root = QgsProject.instance().layerTreeRoot()
    grupo = root.findGroup("Deslinde MCT")
    if not grupo: 
        iface.messageBar().pushMessage("Error", "No se encontró el grupo 'Deslinde MCT'", level=Qgis.Critical)
        return None
    candidatos=[]
    for node in grupo.children():
        if isinstance(node, QgsLayerTreeLayer):
            lyr=node.layer()
            if lyr and lyr.isValid() and lyr.type()==QgsMapLayer.VectorLayer and lyr.geometryType()==2:
                try:
                    fc=lyr.featureCount()
                except:
                    fc=9999
                candidatos.append((fc,lyr))
    if not candidatos:
        iface.messageBar().pushMessage("Error", "No se encontraron capas de polígono válidas en 'Deslinde MCT'", level=Qgis.Critical)
        return None
    candidatos.sort(key=lambda x:x[0])
    return candidatos[0][1]
def obtener_identificacion(capa_base):
    region=provincia=comuna="(No identificado)"
    root = QgsProject.instance().layerTreeRoot()
    grupo_ctx = root.findGroup("01. Contexto territorial")
    if grupo_ctx and capa_base and capa_base.isValid():
        for node in grupo_ctx.children():
            if isinstance(node, QgsLayerTreeLayer) and "comunas" in norm(node.name()):
                comunas_layer=node.layer()
                if comunas_layer and comunas_layer.isValid():
                    try:
                        processing.run("native:selectbylocation",
                            {'INPUT':comunas_layer,'PREDICATE':[0],'INTERSECT':capa_base,'METHOD':0})
                        sel=comunas_layer.selectedFeatures()
                        if sel:
                            f=sel[0]
                            fn=[fld.name().upper() for fld in comunas_layer.fields()]
                            region=f["REGION"] if "REGION" in fn else region
                            provincia=f["PROVINCIA"] if "PROVINCIA" in fn else provincia
                            comuna=f["COMUNA"] if "COMUNA" in fn else comuna
                    except:
                        pass
    return region, provincia, comuna

# 4. CONSTRUIR TABLAS

# --- FUNCIÓN MODIFICADA (1) ---
def clasificar_capas(capa_base):
    root = QgsProject.instance().layerTreeRoot()
    clasificados = OrderedDict()
    
    capa_base_dissolved = None
    if capa_base and capa_base.isValid():
        try:
            result = processing.run("native:dissolve", {
                'INPUT': capa_base,
                'OUTPUT': 'memory:'
            })
            capa_base_dissolved = result['OUTPUT']
        except Exception as e:
            print(f"Advertencia: No se pudo disolver la capa base. El chequeo espacial para G.00 puede fallar. {e}")
            pass

    for group in root.children():
        if not isinstance(group, QgsLayerTreeGroup): 
            continue
        if not re.match(r"^\s*\d{2}\.", group.name()):
            continue
            
        gname = group.name()
        clasificados[gname] = []
        
        for node in group.children():
            if not isinstance(node, QgsLayerTreeLayer): 
                continue
            lyr=node.layer()
            if not lyr or not lyr.isValid() or es_basemap(lyr): 
                continue
            
            condicion = "No superpone" # Default

            # --- NUEVA LÓGICA DE INTERSECCIÓN ---
            if gname.startswith("00.") and capa_base_dissolved:
                # Para el grupo 00, hacer chequeo espacial real
                try:
                    extract = processing.run("native:extractbylocation", {
                        'INPUT': lyr,
                        'INTERSECT': capa_base_dissolved,
                        'PREDICATE': [0], # 0 = intersects
                        'OUTPUT': 'memory:'
                    })
                    if extract['OUTPUT'].featureCount() > 0:
                        condicion = "Superpone"
                    else:
                        condicion = "No superpone"
                except Exception as e:
                    print(f"Error chequeando intersección para {lyr.name()}: {e}")
                    condicion = "No superpone" # Fallback
            else:
                # Para todos los demás grupos, usar la visibilidad
                condicion = "Superpone" if node.isVisible() else "No superpone"
            # --- FIN DE LA LÓGICA ---
            
            clasificados[gname].append((lyr.name(),condicion))
    return clasificados

def construir_tabla_resumen(clasificados):
    rows=[]
    for g,items in clasificados.items():
        tot=len(items)
        sup=sum(1 for _,c in items if c=="Superpone")
        rows.append(f"<tr><td>{g}</td><td>{tot}</td><td>{sup}</td><td>{tot-sup}</td></tr>")
    return "\n".join(rows) if rows else "<tr><td colspan='4'><em>Sin datos</em></td></tr>"

def build_data(capa_base):
    region, provincia, comuna = obtener_identificacion(capa_base)
    DATA = {
        "id": TITULO_ID,
        "fecha": datetime.date.today().strftime("%Y-%m-%d"),
        "region": region,
        "provincia": provincia,
        "comuna": comuna,
        "fecha_datos": PARAMS_TECNICOS.get("fecha_datos", ""),
        "fuente_geo": PARAMS_TECNICOS.get("fuente_geo", "")
    }
    return DATA
# --- FUNCIÓN MODIFICADA (2) ---
def construir_tabla_matriz(clasificados):
    rows = []
    for g, items in clasificados.items():
        if not items:
            continue
            
        has_superpone = any(cond == "Superpone" for _, cond in items)
        is_open = (g.startswith("01.") or g.startswith("00.")) or has_superpone
        
        data_g_norm = norm(g)
        indicator = "[-]" if is_open else "[+]"
        sorted_items = sorted(items, key=lambda x: (x[1] != "Superpone", norm(x[0])))
        rowspan = len(sorted_items)
        
        rowspan_actual = rowspan if is_open else 1
        style_filas_ocultas = "" if is_open else "style='display:none;'"
        style_celdas_fila1_ocultas = "" if is_open else "style='display:none;'"
        
        for i, (nombre, cond) in enumerate(sorted_items, 1):
            icon = "✅" if cond == "Superpone" else ""
            color = "#e8f5e9" if cond == "Superpone" else "#f9f9f9"
            texto_condicion = f"{icon} {cond}" if icon else cond

            if i == 1:
                # Modificación: El onclick se mueve al span y se añade event.stopPropagation()
                gcell = f"<td rowspan='{rowspan_actual}' class='cat' id='cat-{data_g_norm}' " \
                        f"data-full-rowspan='{rowspan}'>" \
                        f"{g} <span class='toggle-indicator' id='toggle-{data_g_norm}' " \
                        f"onclick='event.stopPropagation(); toggleGroup(\"{data_g_norm}\")'>{indicator}</span></td>"
                
                # Las celdas de datos de la fila 1 (se ocultan si está cerrado)
                data_cells = f"<td {style_celdas_fila1_ocultas}>{i}</td>" \
                             f"<td {style_celdas_fila1_ocultas}>{nombre}</td>" \
                             f"<td {style_celdas_fila1_ocultas} style='background:{color}; white-space:nowrap;'>{texto_condicion}</td>"
                
                rows.append(
                    f"<tr data-grupo='{data_g_norm}'>"
                    f"{gcell}"
                    f"{data_cells}"
                    f"</tr>"
                )
            else:
                # Filas 2 en adelante
                gcell = ""
                data_cells = f"<td>{i}</td>" \
                             f"<td>{nombre}</td>" \
                             f"<td style='background:{color}; white-space:nowrap;'>{texto_condicion}</td>"
                
                rows.append(
                    f"<tr data-grupo='{data_g_norm}' {style_filas_ocultas}>"
                    f"{gcell}"
                    f"{data_cells}"
                    f"</tr>"
                )
    return "".join(rows)
# ==========================================
# 5. HTML (plantilla + ensamblado)
# ==========================================
def build_html(DATA, tabla_resumen, tabla_matriz):
    region_detectada = DATA.get("region", "(No identificado)")
    
    # Obtener Comuna y Provincia con valores por defecto
    comuna_detectada = DATA.get("comuna", "[comuna]")
    provincia_detectada = DATA.get("provincia", "[provincia]")

    if comuna_detectada != "[comuna]" and comuna_detectada != "(No identificado)":
        comuna_detectada = comuna_detectada.title()
    if provincia_detectada != "[provincia]" and provincia_detectada != "(No identificado)":
        provincia_detectada = provincia_detectada.title()

    fecha_raw = DATA.get("fecha", "")
    try:
        f_obj = datetime.datetime.strptime(fecha_raw, "%Y-%m-%d")
        fecha_display = f_obj.strftime("%d-%m-%Y")
        fecha_filename = f_obj.strftime("%Y%m%d")
    except:
        fecha_display = fecha_raw
        fecha_filename = "SinFecha"

    fecha_datos = PARAMS_TECNICOS.get("fecha_datos", "")
    fuente_geo = PARAMS_TECNICOS.get("fuente_geo", "")
    
    lista_filtrada = [p for p in PERSONAL_CATASTRO if p["region"] in region_detectada or p["region"] == "Nivel Central"]

    opciones_html = ""
    mapa_cargos_js = ""
    for resp in lista_filtrada:
        nombre_js = resp["nombre"].replace('"', '\\"')
        cargo_js = resp["cargo"].replace('"', '\\"')
        opciones_html += f'<option value="{nombre_js}">'
        mapa_cargos_js += f'"{nombre_js}": "{cargo_js}",\n'

    html_content = fr"""
        <!doctype html>
        <html lang='es'>
        <head>
        <meta charset='utf-8'>
        <title>Minuta {DATA.get('id', '')}</title>
        <style>
            body{{font-family:Calibri,Arial,sans-serif;font-size:9pt;margin:30px;color:#111;}}
            h1{{margin:0;font-size:16pt;color:#003366;font-weight:bold;}}
            h2{{color:#003366;margin-top:20px;font-size:14pt;}}
            .panel{{border:1px solid #ddd;padding:8px;border-radius:6px;margin-bottom:12px;}}
            #parrafo_analisis, #antecedentes_panel, #intro_analisis, #conclusiones_panel {{ text-align: justify; }}
            .panel p {{ margin-top: 0; margin-bottom: 0; }}
            .panel p + p {{ margin-top: 10px; }}
            .panel ul {{ margin-top: 10px; margin-bottom: 10px; padding-left: 30px; }}
            .panel li {{ margin-bottom: 5px; }}

            /* Inputs modernos */
            #encabezado_identificacion [contenteditable='true'] {{
                color: #111; border: none; background: transparent;
                padding: 0; border-radius: 0; display: inline; min-width: 50px; 
            }}
            [contenteditable='true'] {{
                color: #666; border: 1px solid #ccc; background: #fff;
                padding: 2px 4px; border-radius: 3px; display: inline-block; min-width: 150px; 
            }}
            [contenteditable='true']:focus {{ color: #111; border: 1px solid #003366; outline: none; background: #fff; }}
            
            #input_responsable {{
                font-family: Calibri, Arial, sans-serif; font-size: 9pt;
                border: 1px solid #ccc; background: #fff; padding: 2px 4px; border-radius: 3px;
            }}
            
            button.main-btn {{background:#003366;color:#fff;border:none;padding:6px 12px;margin:8px 0;border-radius:4px;cursor:pointer;font-size:9pt;}}
            button.main-btn:hover {{background:#0059b3;}}
            
            /* --- DROP ZONE & IMAGENES --- */
            .image-block {{ margin-bottom: 20px; text-align: center; }}
            
            .drop-zone {{
                display: block !important; 
                width: 100%; 
                min-height: 200px !important; 
                height: auto;     
                background: #fafafa;
                border: 2px dashed #999; 
                border-radius: 6px;
                margin: 10px 0;
                position: relative; 
                cursor: pointer;
                box-sizing: border-box;
                padding: 10px;
                text-align: center;
            }}
            
            .drop-zone span.drop-text {{ 
                display: inline-block; 
                margin-top: 80px; 
                color: #666; 
                font-style: italic;
                pointer-events: none; 
            }}
            
            .drop-zone:hover {{ background: #f0f0f0; border-color: #666; }}
            .drop-zone.dragover {{ background: #e8f5e9; border-color: #4caf50; }}
            
            .drop-zone canvas {{ 
                max-width: 100%; 
                height: auto; 
                display: none; 
                margin: 0 auto;
            }}
            
            .drop-zone.has-image span.drop-text {{ display: none; }}
            .drop-zone.has-image canvas {{ display: block; }}
            .drop-zone.has-image {{ padding: 0; border-style: solid; }}

            .editor-toolbar {{ margin-top: 5px; text-align: center; display: none; }}
            .editor-btn {{
                background: #fff; border: 1px solid #ccc; color: #444;
                padding: 4px 10px; border-radius: 4px; cursor: pointer; margin: 0 5px; font-size: 12pt;
                line-height: 1;
            }}

            /* TABLAS */
            table#tabla1, table#resumen, table#matriz {{ width: 100%; border-collapse:collapse; font-size:9pt; }}
            th,td{{border:1px solid #ccc;padding:4px 6px;text-align:left;vertical-align:middle;}}
            thead th{{background:#003366;color:#fff;text-align:center;}}
            
            /* Ancho de columnas Tabla 1 */
            #tabla1 td input, #tabla1 td select {{ width: 95%; box-sizing: border-box; font-family: Calibri, sans-serif; font-size: 9pt; }}
            
            /* INTERACTIVIDAD MATRIZ */
            .cat {{ background:#f0f0f0; font-weight:bold; user-select: text; }}
            .toggle-indicator {{ 
                font-family: monospace; font-weight: bold; float: right; margin-right: 5px; 
                cursor: pointer; padding: 0 5px; background: #e0e0e0; border-radius: 3px; user-select: none; 
            }}
            .toggle-indicator:hover {{ background: #c0c0c0; }}

            #matriz th:nth-child(1), #matriz td:nth-child(1){{ width:18%; }}
            #matriz th:nth-child(2), #matriz td:nth-child(2){{ width:6%; }}
            #matriz th:nth-child(3), #matriz td:nth-child(3){{ width:53%; }} 
            #matriz th:nth-child(4), #matriz td:nth-child(4){{ width:23%; }} 

            .footer{{border-top:1px solid #ccc;margin-top:25px;padding-top:8px;font-size:8pt;color:#555;text-align:center;line-height:1.5;}}
            .fuente {{ font-style: italic; font-size: 9pt; color: #666; text-align: center; }}
            
            /* Encabezado MBN */
            .mbn-main-header-table {{ border: 1px solid #ccc; margin-bottom: 0; font-family: Calibri, sans-serif; }}
            .mbn-main-header-table tr, .mbn-main-header-table td {{ padding: 0 !important; border: none !important; vertical-align: top; }}
            .mbn-bar-cell {{ width: 2.4cm; min-width: 2.4cm; border-right: 1px solid #ccc !important; padding-right: 8px !important; }}
            .mbn-text-line-1 {{ font-family:Calibri;font-size:9pt;color:#444;margin-top:2px; line-height: normal; white-space:nowrap; }}
            .mbn-text-line-2 {{ font-family:Calibri;font-size:9pt;color:#555;margin-top:0px; line-height: normal; white-space:nowrap; font-weight: bold;}}
            .title-cell {{ padding-left: 8px !important; padding-top: 2px !important; padding-bottom: 4px !important; font-weight: bold; color:#003366; }}
            .mbn-bar-table {{ width: 2.4cm; border-collapse: collapse; table-layout: fixed; mso-table-lspace:0pt; mso-table-rspace:0pt; mso-padding-alt:0 0 0 0; margin: 0; }}
            .mbn-bar-table td {{ padding: 0 !important; border: none !important; line-height:0; font-size:1px; height: 0.23cm; }}
            
            /* Anexo Láminas */
            .lamina-item {{ 
                margin-bottom: 30px; 
                border-bottom: 1px dashed #ccc; 
                padding-bottom: 20px; 
            }}
            .lamina-item:last-child {{ border-bottom: none; }}
            .lamina-title {{ font-weight: bold; margin-bottom: 10px; text-align: center; }}
            .btn-del-lamina {{ 
                background: #ffdddd; border: 1px solid #ffaaaa; color: #aa0000; 
                cursor: pointer; font-size: 8pt; padding: 2px 6px; margin-left: 10px; border-radius: 3px;
            }}
            
            @media print {{
                .actions, .editor-toolbar, .drop-text, button {{ display: none !important; }}
                .drop-zone {{ border: none !important; min-height: 0 !important; }}
            }}
        </style>
        </head>
        <body>

        <div id="encabezado_mbn">
            <table width="100%" border="0" cellspacing="0" cellpadding="0" class="mbn-main-header-table">
                <tr>
                    <td class="mbn-bar-cell">
                        <table class="mbn-bar-table" width="2.4cm" border="0" cellspacing="0" cellpadding="0" style="width:2.4cm; height:0.23cm;">
                            <tr style="height:0.23cm; line-height:0; font-size:0;">
                                <td width="1.2cm" bgcolor="#A7BED3" style="background:#A7BED3; width:1.2cm; border-right:1px solid #FFFFFF;">&nbsp;</td>
                                <td width="1.2cm" bgcolor="#E8A3A3" style="background:#E8A3A3; width:1.2cm;">&nbsp;</td>
                            </tr>
                        </table>
                        <div class="mbn-text-line-1">Ministerio de Bienes Nacionales</div>
                        <div class="mbn-text-line-2">División de Catastro</div>
                    </td>
                    <td width="*" style="vertical-align: top;">
                        <div class="title-cell" style="font-size:14pt;">MINUTA CATASTRAL TERRITORIAL</div>
                        <div id='identificacion-content' style="padding-left: 8px; font-size: 9pt; margin-top: 8px;">
                            <table style="width:100%; border:none;">
                                <tr style="border:none;">
                                    <td style="width:50%; border:none; padding:0; vertical-align:top;">
                                        <b>Materia:</b> <span contenteditable='true'>[Señalar la materia del análisis – naturaleza de la solicitud]</span><br><br>
                                        <b>Fecha de creación de la Minuta:</b> {fecha_display}
                                    </td>
                                    <td style="width:50%; border:none; padding:0; vertical-align:top;">
                                        <b>ID catastral:</b> <span id="id_catastral_input" contenteditable='true' oninput="actualizarTablaPorID(this)">[Indicar ID]</span><br>
                                        <b>Región:</b> {DATA.get("region")}<br>
                                        <b>Responsable:</b> 
                                        <input id="input_responsable" list="lista-responsables-data" onchange="actualizarFirma(this)" placeholder="[Escriba o seleccione un analista]">
                                        <datalist id="lista-responsables-data">{opciones_html}</datalist>
                                    </td>
                                </tr>
                            </table>
                        </div>
                    </td>
                </tr>
            </table>
        </div>

        <div id='parrafo_analisis'>
            <p>Por medio de la presente minuta se remite análisis territorial <span contenteditable='true'>[N° de expediente / materia de la solicitud]</span>.</p>
            <p>El análisis territorial se efectuó sobre la espacialización del <span contenteditable='true'>[predio/inmueble]</span> de acuerdo con los antecedentes remitidos, realizando una superposición geográfica entre la propiedad fiscal y la información disponible, para obtener el resultado de variables que pudiesen constituir alguna incompatibilidad de orden territorial para el Ministerio de Bienes Nacionales.</p>
        </div>
        
        <h2>1. Antecedentes e identificación catastral territorial</h2>
        <div id='antecedentes_panel' class='panel'>
            <p>De acuerdo con los antecedentes, la solicitud corresponde a <span contenteditable='true'>[Detalle de la solicitud -]</span> <span contenteditable='true'>[otorgada a favor de …]</span> cuyo destino buscado es <span contenteditable='true'>[completar destino]</span>.</p>
            <p>El inmueble solicitado se encuentra inscrito a favor del Fisco de Chile a <span contenteditable='true'>[Fojas xxx Número xxxx año xxxx del Conservador de Bienes Raíces de xxxx]</span> y localizado en <span contenteditable='true'>[dirección/sector]</span> comuna de <span contenteditable='true'>{comuna_detectada}</span>, provincia de <span contenteditable='true'>{provincia_detectada}</span>, Región de {DATA.get("region")}.</p>
            <p>En la tabla N°1 se mostrará los detalles de la propiedad fiscal analizada.</p>
        </div>
        
        <div style='text-align:center;font-style:italic;margin:6px 0;'>Tabla N°1: Detalle Propiedad Fiscal en análisis.</div>
        <div class='actions'><button class="main-btn" id="btn_addrow" onclick="agregarFilaTabla1()">➕ Agregar fila</button></div>
        
        <table id='tabla1' style="width:100%;">
            <thead>
                <tr>
                    <th>ID UC</th>
                    <th>Nombre</th>
                    <th>Sector</th>
                    <th>Plano</th>
                    <th>Inscripción de dominio fiscal</th>
                    <th>Tenencia</th>
                    <th>Administración</th>
                    <th id="th-superficie">
                        Superficie UC (<span id="unidad-display">m²</span>)
                        <button class="editor-btn" id="btn-toggle-unidad" onclick="toggleUnidadSuperficie(event)">🔄</button>
                    </th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td><input type='text' placeholder='XXXX'></td>
                    <td><input type='text' placeholder='Nombre de la UC'></td>
                    <td><select><option>URBANO</option><option>RURAL</option><option>AMBOS</option></select></td>
                    <td><input type='text' placeholder='XXXXX-XXXX-CU'></td>
                    <td><input type='text' placeholder='Fojas / Nº / Año - CBR'></td>
                    <td><select><option>Con administración</option><option>Con administración y ocupante</option><option>Parcialmente Administrada</option><option>Parcialmente Administrada y con ocupante</option><option>En Administración MBN D.L. 1939</option><option>En Administración MBN D.L. 1939 y con ocupante</option><option>Con autorización de enajenación</option><option>Con enajenación</option><option>Sin tuición de administración del MBN</option></select></td>
                    <td><input type='text' placeholder='MBN / Otro'></td>
                    <td><input type='number' step='0.1' placeholder='0,0' data-unidad-base='0.0' oninput="updateUnidadBase(this)"></td>
                </tr>
            </tbody>
        </table>
        <div class='fuente'>Fuente: Sistema de Catastro, MBN.</div>

        <div id="bloque_imagen_1" class="image-block" style="margin-top:25px; margin-bottom:25px;">
            <div style="text-align:center; font-style:italic; font-weight:normal; margin-bottom:8px; color:#444;">Imagen N°1. Localización general de área analizada</div>
            
            <div class="img-editor-container" id="img-editor-1">
                <div class="drop-zone">
                    <span class="drop-text">Arrastra una imagen aquí (JPG/PNG) o pégala (Ctrl+V)</span>
                    <canvas></canvas>
                    <input type="file" accept="image/*" style="display:none;">
                </div>
                <div class="editor-toolbar">
                    <button class="editor-btn btn-rot-l">↺</button>
                    <button class="editor-btn btn-rot-r">↻</button>
                    <button class="editor-btn btn-del" style="color:red;">✖</button>
                </div>
            </div>

            <div id="fuente_imagen_1" style="text-align:center; font-size:9pt; font-style:italic; margin-top:5px; color:#666;">Fuente: Unidad de Catastro SEREMI {DATA.get("region")}</div>
        </div>

        <h2>2. Análisis Territorial</h2>
        <p id='intro_analisis'>Según los resultados del análisis realizado, se presenta una tabla de las variables territoriales consideradas para el análisis territorial en la cual se señala la presencia o ausencia de estas con respecto al inmueble analizado o al área de estudio.</p>
        
        <h2>Resumen numérico</h2>
        <table id='resumen' style="width:100%;"><thead><tr><th>Grupo</th><th>Total</th><th>Superpone</th><th>No superpone</th></tr></thead><tbody>{tabla_resumen}</tbody></table>
        <div style='text-align:center;font-style:italic;margin:12px 0 6px 0;'>Tabla N° 2. Variables consideradas para el análisis territorial.</div>
        <table id='matriz' style="width:100%;"><thead><tr><th>Categoría</th><th>N°</th><th>Variable</th><th>Condición</th></tr></thead><tbody>{tabla_matriz}</tbody></table>
        <div id="fuente_unidad_catastro" style='margin-top:6px; font-size:9pt; color:#666; text-align:center; font-style:italic;'>Fuente: Unidad de Catastro SEREMI Region de {DATA.get("region")}</div>

        <h2>3. CONCLUSIONES</h2>
        <div id="conclusiones_panel" class="panel">
            <p>En vista de los antecedentes anteriormente expuestos y del análisis territorial realizado en este informe, se establece lo siguiente:</p>
            <ul id="lista_conclusiones">
                <li><span contenteditable="true">[Conclusión 1]</span></li>
                <li><span contenteditable="true">[Conclusión 2]</span></li>
            </ul>
            <div class="actions" style="margin-bottom: 10px;">
                <button class="main-btn" onclick="agregarConclusion()">➕ Agregar conclusión</button>
            </div>
            
            <p>Desde el punto de vista de esta Unidad, <select id="conclusion_existencia"><option value="existen">existen</option><option value="no_existen">no existen</option></select> variables territoriales contenidas en la base de información que señalen inconvenientes o conflictos para realizar gestiones en el uso de la propiedad fiscal, salvo mejor parecer de la autoridad.</p>
        </div>

        <h2>FIRMA</h2>
        <div id="firma_panel" class="panel" style="text-align:center; margin-top:20px;">
            <div style="margin-bottom:25px; font-style:italic;">[INSERTAR FIRMA]</div>
            <div>____________________________</div>
            <div id="firma_nombre" contenteditable="true">[Nombre profesional a cargo]</div>
            <div id="firma_cargo" contenteditable="true">[Asistente de Catastro / Encargado de Catastro]</div>
            <div id="firma_unidad_catastro">Unidad de Catastro SEREMI {DATA.get("region")}</div>
            <div>Ministerio de Bienes Nacionales</div>
        </div>
        
        <div id="word_footer" style="margin-top:25px;font-size:8pt;color:#555;">
            <hr style="border:0;border-top:1px solid #999;margin-bottom:6px;">
            <div>Fuente de información catastral: Sistema de Catastro, MBN.</div>
            <div>Fecha actualización de variables: {fecha_datos}</div>
            <div>Fuentes geoespaciales: {fuente_geo}</div>
            <div style="margin-top:5px; text-align: justify;">
                El presente material cartográfico está destinado al uso interno del Ministerio de Bienes Nacionales y su propósito es exclusivamente
                referencial. Se advierte que no debe ser utilizado para trabajos que impliquen la interpretación de límites o que requieran precisión
                geodésica.
            </div>
        </div>

        <h2 style='text-align:center;'>ANEXO</h2>
        <div id="anexo_panel" class="panel" style='text-align:center;'>
            <div id="contenedor_laminas">
                </div>
            <div class="actions" style="margin-top:15px;">
                <button class="main-btn" onclick="agregarLamina()">➕ Agregar Lámina</button>
            </div>
        </div>

        <div style="text-align:center; margin-top:25px;"><button class="main-btn" id="btn_export" onclick="exportarTablaWord()">📄 Exportar a Word (.doc)</button></div>
        <div class='footer'>Ministerio de Bienes Nacionales — Departamento de Estudios Territoriales</div>
        
        <script>
        window.EXPORT_FILENAME_DATE = "{fecha_filename}";
        window.QGIS_DATA = {{
            region: "{DATA.get('region')}",
            cargos: {{ {mapa_cargos_js} }}
        }};
        </script>
    """
    
    js_logic = r"""
    <script>
    (function(){

        class ImageControl {
            constructor(container) {
                this.container = container;
                this.dropZone = container.querySelector('.drop-zone');
                this.fileInput = container.querySelector('input[type="file"]');
                this.canvas = container.querySelector('canvas');
                this.ctx = this.canvas.getContext('2d');
                this.dropText = container.querySelector('.drop-text');
                this.toolbar = container.querySelector('.editor-toolbar');
                this.imgObject = new Image();
                this.currentRotation = 0;
                this.initEvents();
            }
            initEvents() {
                // Click event
                this.dropZone.onclick = (e) => { 
                    if(e.target !== this.toolbar && !this.toolbar.contains(e.target)) { 
                        this.fileInput.click(); 
                    } 
                };

                // Drag events
                this.dropZone.ondragover = (e) => { e.preventDefault(); this.dropZone.classList.add('dragover'); };
                this.dropZone.ondragleave = () => { this.dropZone.classList.remove('dragover'); };
                this.dropZone.ondrop = (e) => { 
                    e.preventDefault(); 
                    this.dropZone.classList.remove('dragover'); 
                    if(e.dataTransfer.files && e.dataTransfer.files[0]) this.processFile(e.dataTransfer.files[0]); 
                };

                // Paste event (Ctrl+V)
                this.container.addEventListener('paste', (e) => {
                    const items = (e.clipboardData || e.originalEvent.clipboardData).items;
                    for (let i = 0; i < items.length; i++) {
                        if (items[i].kind === 'file' && items[i].type.startsWith('image/')) {
                            const file = items[i].getAsFile();
                            this.processFile(file);
                            e.preventDefault(); 
                            return; 
                        }
                    }
                });

                // File input event
                this.fileInput.onchange = () => { 
                    if(this.fileInput.files[0]) this.processFile(this.fileInput.files[0]); 
                };

                // Button events
                this.container.querySelector('.btn-rot-l').onclick = (e) => { e.stopPropagation(); this.rotate(-90); };
                this.container.querySelector('.btn-rot-r').onclick = (e) => { e.stopPropagation(); this.rotate(90); };
                this.container.querySelector('.btn-del').onclick = (e) => { e.stopPropagation(); this.clear(); };
                
                new ResizeObserver(() => { 
                    if(this.imgObject.src && this.canvas.style.display !== 'none') this.render(); 
                }).observe(this.dropZone);
            }

            processFile(file) {
                if(!file.type.startsWith('image/')) return;
                const reader = new FileReader();
                reader.onload = (e) => { 
                    this.imgObject.onload = () => { 
                        this.currentRotation = 0; 
                        this.dropZone.classList.add('has-image'); 
                        this.render(); 
                        this.toolbar.style.display = 'block'; 
                    }; 
                    this.imgObject.src = e.target.result; 
                };
                reader.readAsDataURL(file);
            }
            rotate(deg) { this.currentRotation = (this.currentRotation + deg) % 360; this.render(); }
            clear() {
                this.imgObject.src = ""; 
                this.ctx.clearRect(0,0,this.canvas.width, this.canvas.height); 
                this.canvas.width = 0; this.canvas.height = 0;
                this.dropZone.classList.remove('has-image'); 
                this.toolbar.style.display = 'none'; 
                this.fileInput.value = '';
                this.dropZone.style.height = 'auto'; 
                this.dropZone.style.minHeight = '200px';
            }
            render() {
                if(!this.imgObject.src) return;
                const dropZoneWidth = this.dropZone.clientWidth; 
                const dropZoneMaxHeight = 800; 
                let newWidth, newHeight;
                if (this.currentRotation % 180 === 0) { newWidth = this.imgObject.width; newHeight = this.imgObject.height; } 
                else { newWidth = this.imgObject.height; newHeight = this.imgObject.width; }
                const scaleWidth = dropZoneWidth / newWidth; 
                const scaleHeight = dropZoneMaxHeight / newHeight; 
                const scale = Math.min(scaleWidth, scaleHeight, 1); 
                this.canvas.width = newWidth * scale; 
                this.canvas.height = newHeight * scale;
                this.ctx.clearRect(0,0,this.canvas.width,this.canvas.height); 
                this.ctx.save();
                this.ctx.translate(this.canvas.width/2, this.canvas.height/2); 
                this.ctx.rotate(this.currentRotation * Math.PI/180);
                this.ctx.drawImage(this.imgObject, -newWidth * scale / 2, -newHeight * scale / 2, newWidth * scale, newHeight * scale);
                this.ctx.restore();
                this.dropZone.style.height = (this.canvas.offsetHeight + 20) + 'px'; 
            }
        }

        function norm(t) { return (t || "").normalize("NFD").replace(/[\u0300-\u036f]/g,"").toLowerCase().replace(/[^a-z0-9\s]/g,"").replace(/\s+/g," ").trim(); }

        window.agregarLamina = function() {
            const container = document.getElementById('contenedor_laminas');
            const index = container.children.length + 1;
            const div = document.createElement('div'); 
            div.className = 'lamina-item';
            div.innerHTML = `
                <div class="lamina-title">Lámina ${index}: <span contenteditable="true">[Tema de la lámina]</span>${index > 1 ? '<button class="btn-del-lamina" onclick="eliminarLamina(this)">Eliminar</button>' : ''}</div>
                <div class="img-editor-container"><div class="drop-zone"><span class="drop-text">Arrastra mapa aquí (JPG/PNG) o pégala (Ctrl+V)</span><canvas></canvas><input type="file" accept="image/*" style="display:none;"></div><div class="editor-toolbar"><button class="editor-btn btn-rot-l">↺</button><button class="editor-btn btn-rot-r">↻</button><button class="editor-btn btn-del" style="color:red;">✖</button></div></div>
            `;
            container.appendChild(div); 
            new ImageControl(div.querySelector('.img-editor-container'));
        };

        window.eliminarLamina = function(btn) { if(confirm('¿Eliminar esta lámina?')) { btn.closest('.lamina-item').remove(); renumerarLaminas(); } };

        function renumerarLaminas() {
            const laminas = document.querySelectorAll('#contenedor_laminas .lamina-item');
            laminas.forEach((div, i) => {
                const titleDiv = div.querySelector('.lamina-title'); 
                const span = titleDiv.querySelector('span[contenteditable]'); 
                const btn = titleDiv.querySelector('.btn-del-lamina');
                titleDiv.innerHTML = `Lámina ${i+1}: `; 
                titleDiv.appendChild(span);
                if(i > 0) { 
                    if(!btn) { 
                        const newBtn = document.createElement('button'); 
                        newBtn.className = 'btn-del-lamina'; 
                        newBtn.onclick = function(){eliminarLamina(this)}; 
                        newBtn.innerText = 'Eliminar'; 
                        titleDiv.appendChild(newBtn); 
                    } else { titleDiv.appendChild(btn); } 
                }
            });
        }

        // FIX: FUNCION AGREGAR CONCLUSION
        window.agregarConclusion = function() {
            var ul = document.getElementById("lista_conclusiones");
            if(!ul) return;
            var li = document.createElement("li");
            var span = document.createElement("span");
            span.setAttribute("contenteditable", "true");
            span.textContent = "[Nueva conclusión]";
            li.appendChild(span);
            ul.appendChild(li);
        };

        function init() {
            new ImageControl(document.getElementById('img-editor-1'));
            agregarLamina();
        }
        
        if(document.readyState==='complete') init(); else window.onload = init;

        // ===============================================
        // FUNCIONES DE UNIDAD Y SUPERFICIE 
        // ===============================================
        
        let currentUnit = 'm2'; 

        window.updateUnidadBase = function(input) {
            var val = parseFloat(input.value) || 0;
            var unidadActual = document.getElementById("unidad-display").textContent.trim().toLowerCase().replace('²', '2');
            var valM2 = (unidadActual === 'ha') ? val * 10000 : val;
            input.setAttribute('data-unidad-base', valM2.toFixed(4));
        }
        
        window.toggleUnidadSuperficie = function(e) {
            if (e) e.stopPropagation();
            var inputs = document.querySelectorAll("#tabla1 tbody input[type='number']");
            var unidadDisplay = document.getElementById("unidad-display");
            
            if (currentUnit === 'm2') {
                currentUnit = 'ha';
                unidadDisplay.textContent = 'ha';
                inputs.forEach(function(input) {
                    var valM2 = parseFloat(input.getAttribute('data-unidad-base')) || 0;
                    var valHa = valM2 / 10000;
                    input.value = (valM2 === 0) ? "0" : (valM2 < 10000 ? valHa.toFixed(4) : valHa.toFixed(2));
                });
            } else {
                currentUnit = 'm2';
                unidadDisplay.textContent = 'm²';
                inputs.forEach(function(input) {
                    var valM2 = parseFloat(input.getAttribute('data-unidad-base')) || 0;
                    input.value = valM2.toFixed(2);
                });
            }
        };
        
        window.agregarFilaTabla1 = function() {
            var tb = document.querySelector("#tabla1 tbody");
            var cl = tb.lastElementChild.cloneNode(true);
            cl.querySelectorAll("input").forEach(function(i){
                i.value="";
                if (i.hasAttribute('data-unidad-base')) {
                    i.setAttribute('data-unidad-base', '0.00'); 
                    i.setAttribute('oninput', 'updateUnidadBase(this)'); 
                }
            });
            cl.querySelectorAll("select").forEach(function(s){s.selectedIndex=0});
            tb.appendChild(cl);
            toggleUnidadSuperficie(null); toggleUnidadSuperficie(null); 
        };
        
        window.actualizarTablaPorID = function(el) {
            var txt = (el.textContent || el.innerText).trim();
            var ids = txt.split('-').map(function(s){return s.trim()}).filter(function(s){return s.match(/^\d+$/)});
            var tb = document.querySelector("#tabla1 tbody");
            if(!tb) return;
            var curr = tb.rows.length;
            var need = ids.length || 1;
            
            if(need > curr) {
                for(var i=0; i<(need-curr); i++) {
                    var cl = tb.lastElementChild.cloneNode(true);
                    cl.querySelectorAll("input").forEach(function(inp){inp.value=""});
                    tb.appendChild(cl);
                }
            }
            while(tb.rows.length > need) tb.removeChild(tb.lastElementChild);
            for(var i=0; i<tb.rows.length; i++) {
                var inp = tb.rows[i].querySelector("td:first-child input");
                if(inp) inp.value = ids[i]||"";
            }
            toggleUnidadSuperficie(null); toggleUnidadSuperficie(null);
        };

        window.actualizarFirma = function(el) {
            var val = el.value;
            var c = window.QGIS_DATA.cargos[val];
            var dU = "Fuente: Unidad de Catastro SEREMI Region de " + window.QGIS_DATA.region;
            var dF = "Unidad de Catastro SEREMI " + window.QGIS_DATA.region;
            var cU = "Fuente: Departamento de Estudios Territoriales – División de Catastro";
            var cF = "Departamento de Estudios Territoriales – División de Catastro";
            
            var targetU = (c && c.indexOf("Estudios Territoriales") !== -1) ? cU : dU;
            var targetF = (c && c.indexOf("Estudios Territoriales") !== -1) ? cF : dF;

            document.getElementById("firma_nombre").innerText = val || "[Nombre profesional a cargo]";
            document.getElementById("firma_cargo").innerText = c || "[Asistente de Catastro / Encargado de Catastro]";
            document.getElementById("fuente_unidad_catastro").innerText = targetU;
            document.getElementById("firma_unidad_catastro").innerText = targetF;
            document.getElementById("fuente_imagen_1").innerText = targetU;
        };

        // --- INTERACTIVIDAD MATRIZ ---
        window.toggleGroup = function(gName) {
            var cat = document.getElementById("cat-" + gName);
            if(!cat) return;
            var full = parseInt(cat.getAttribute("data-full-rowspan"), 10);
            var rows = document.querySelectorAll("tr[data-grupo='" + gName + "']");
            var ind = document.getElementById("toggle-" + gName);
            
            var isCurrentlyHidden = rows.length > 1 && rows[1].style.display === 'none';

            if (isCurrentlyHidden) {
                for(var i=1; i<rows.length; i++) rows[i].style.display = '';
                if(rows.length > 0) {
                      var tds = rows[0].querySelectorAll("td:not(.cat)");
                      for(var k=0; k<tds.length; k++) tds[k].style.display = '';
                }
                if(ind) ind.textContent = "[-]";
                cat.rowSpan = full;
            } else {
                for(var i=1; i<rows.length; i++) rows[i].style.display = 'none';
                if(rows.length > 0) {
                      var tds = rows[0].querySelectorAll("td:not(.cat)");
                      for(var k=0; k<tds.length; k++) tds[k].style.display = 'none';
                }
                if(ind) ind.textContent = "[+]";
                cat.rowSpan = 1;
            }
        };

        // =====================================================
        // HELPER: CLONAR PRESERVANDO VALORES
        // =====================================================
        function cloneWithValues(originalNode) {
            var clone = originalNode.cloneNode(true);
            
            // Sincronizar Inputs (saltando file inputs)
            var originalInputs = originalNode.querySelectorAll("input");
            var clonedInputs = clone.querySelectorAll("input");
            originalInputs.forEach((inp, i) => {
                if (inp.type !== 'file') {
                    clonedInputs[i].value = inp.value; 
                }
            });

            // Sincronizar Selects
            var originalSelects = originalNode.querySelectorAll("select");
            var clonedSelects = clone.querySelectorAll("select");
            originalSelects.forEach((sel, i) => {
                clonedSelects[i].selectedIndex = sel.selectedIndex; 
            });
            
            return clone;
        }

        function flatten(el) {
            el.querySelectorAll("input").forEach(function(i){
                if(i.type === 'file') { i.remove(); return; }
                if (i.hasAttribute('data-unidad-base')) {
                    var valM2 = parseFloat(i.getAttribute('data-unidad-base')) || 0;
                    var unidadTexto = document.getElementById("unidad-display").textContent.trim().toLowerCase().replace('²', '2');
                    var displayText = valM2.toFixed(2); 
                    if (unidadTexto === 'ha') {
                        var valHa = valM2 / 10000;
                        displayText = (valM2 === 0) ? "0" : (valM2 < 10000 ? valHa.toFixed(4) : valHa.toFixed(2));
                    } else { displayText = valM2.toFixed(2); }
                    var s=document.createElement("span"); s.textContent=displayText; i.replaceWith(s);
                } else {
                    var s=document.createElement("span"); s.textContent=i.value.trim(); i.replaceWith(s);
                }
            });
            el.querySelectorAll("select").forEach(function(s){
                var text = s.options[s.selectedIndex] ? s.options[s.selectedIndex].text : "";
                var sp=document.createElement("span"); sp.textContent = text; s.replaceWith(sp);
            });
            el.querySelectorAll("[contenteditable]").forEach(function(e){
                var t = e.textContent.trim();
                if(t.startsWith("[")) t = " ";
                e.textContent = t; e.removeAttribute("contenteditable");
                e.style.border = "none"; e.style.background = "transparent"; e.style.padding = "0";
            });
            el.querySelectorAll("button").forEach(b => b.remove());
            el.querySelectorAll(".toggle-indicator").forEach(t => t.remove());
            return el;
        }
        
        function cleanMatrizRows(matClone) {
            const desiredKeywords = ["difrol", "dl 1939", "dl1939", "1939"];
            const tbody = matClone.querySelector("tbody");
            if(!tbody) return;
            const rows = Array.from(tbody.querySelectorAll("tr"));
            const groups = new Map();
            rows.forEach(tr => {
                tr.style.display = '';
                Array.from(tr.children).forEach(td => td.style.display = '');
                const g = tr.getAttribute("data-grupo");
                if(g) {
                    if(!groups.has(g)) groups.set(g, []);
                    groups.get(g).push(tr);
                }
            });
            tbody.innerHTML = ''; 
            groups.forEach((list, gname) => {
                if (gname.startsWith('00.')) return;
                let filteredList = list;
                if (gname.startsWith('01.')) {
                    filteredList = list.filter(tr => {
                        const cell = tr.querySelector('td:last-child').previousElementSibling; 
                        const txt = cell ? norm(cell.textContent) : "";
                        return desiredKeywords.some(k => txt.includes(norm(k)));
                    });
                }
                if(filteredList.length > 0) {
                    const catTd = document.createElement("td");
                    catTd.className = "cat"; catTd.setAttribute("rowspan", filteredList.length); catTd.textContent = gname;
                    filteredList.forEach((tr, idx) => {
                        tr.querySelector('td.cat')?.remove();
                        if(tr.children[0]) tr.children[0].textContent = (idx + 1);
                        if(idx === 0) tr.insertBefore(catTd, tr.firstChild);
                        tbody.appendChild(tr);
                    });
                }
            });
        }

        window.exportarTablaWord = function() {
            var isExporting = false;
            if(isExporting) return; isExporting=true;
            setTimeout(function(){isExporting=false}, 1500);

            try {
                var wrapper = document.createElement("div");
                
                // USO DE cloneWithValues
                var enc = flatten(cloneWithValues(document.getElementById("encabezado_mbn"))); wrapper.append(enc);
                var p = flatten(cloneWithValues(document.getElementById("parrafo_analisis"))); p.style.marginTop = "10px"; wrapper.append(p);
                var t3 = document.createElement("h2"); t3.textContent="1. Antecedentes e identificación catastral territorial"; t3.style.color="#003366"; wrapper.append(t3);
                wrapper.append(flatten(cloneWithValues(document.getElementById("antecedentes_panel"))));
                var cap1 = document.createElement("div"); cap1.innerHTML="<i>Tabla N°1: Detalle Propiedad Fiscal en análisis.</i>"; cap1.style.cssText = "text-align:center;font-style:italic;margin:6px 0;"; wrapper.append(cap1);
                
                // Tabla 1 con valores
                var t1 = cloneWithValues(document.getElementById("tabla1"));
                var thS = t1.querySelector('#th-superficie');
                if(thS) thS.innerHTML = 'Superficie UC (' + document.getElementById("unidad-display").textContent.trim() + ')';
                wrapper.append(flatten(t1));
                var f1 = document.createElement("div"); f1.innerText="Fuente: Sistema de Catastro, MBN."; f1.style.cssText="font-size:9pt; font-style:italic; color:#666; text-align:center;"; wrapper.append(f1);

                // IMAGENES (FAKE URLS)
                var mhtmlImages = [];

                // Imagen 1
                var img1Div = document.getElementById("bloque_imagen_1").cloneNode(true);
                var canvas1 = document.querySelector("#bloque_imagen_1 canvas");
                if(canvas1 && canvas1.width > 0 && canvas1.style.display !== 'none') {
                    var fakeUrl = "http://localhost/img_loc_" + Date.now() + ".jpg";
                    var b64 = canvas1.toDataURL("image/jpeg", 0.7).split(",")[1];
                    mhtmlImages.push({ url: fakeUrl, data: b64 });
                    var imgTag = document.createElement("img"); imgTag.src = fakeUrl; imgTag.width = Math.min(650, canvas1.width); imgTag.style.cssText = "width:" + Math.min(650, canvas1.width) + "px; height:auto; max-width:100%; display:block; margin:0 auto;";
                    var dz = img1Div.querySelector(".drop-zone"); if(dz) dz.replaceWith(imgTag);
                } else {
                    var ph = document.createElement("div"); ph.innerText="[SIN IMAGEN]"; ph.style.cssText="color:#999; border:1px dashed #ccc; padding:20px; text-align:center;";
                    var dz = img1Div.querySelector(".drop-zone"); if(dz) dz.replaceWith(ph);
                }
                img1Div.querySelectorAll(".editor-toolbar").forEach(e => e.remove());
                wrapper.append(flatten(img1Div));

                // Resto
                var t2 = document.createElement("h2"); t2.textContent="2. Análisis Territorial"; t2.style.color="#003366"; t2.style.marginTop="15px"; wrapper.append(t2);
                wrapper.append(flatten(document.getElementById("intro_analisis").cloneNode(true)));
                var cap2 = document.createElement("div"); cap2.innerHTML="<i>Tabla N° 2. Variables consideradas para el análisis territorial.</i>"; cap2.style.cssText = "text-align:center;font-style:italic;margin:12px 0 6px 0;"; wrapper.append(cap2);
                var mat = document.getElementById("matriz").cloneNode(true);
                cleanMatrizRows(mat);
                wrapper.append(flatten(mat));
                wrapper.append(flatten(document.getElementById("fuente_unidad_catastro").cloneNode(true)));
                
                var tC = document.createElement("h2"); tC.textContent="3. CONCLUSIONES"; tC.style.color="#003366"; wrapper.append(tC);
                
                // Conclusiones con cloneWithValues
                wrapper.append(flatten(cloneWithValues(document.getElementById("conclusiones_panel"))));
                
                wrapper.append(flatten(cloneWithValues(document.getElementById("firma_panel"))));
                wrapper.append(flatten(document.getElementById("word_footer").cloneNode(true)));

                // Anexo con cloneWithValues
                var tA = document.createElement("h2"); tA.textContent="ANEXO"; tA.style.color="#003366"; tA.style.textAlign="center"; wrapper.append(tA);
                var anexoPanel = document.getElementById("anexo_panel").cloneNode(false); 
                anexoPanel.style.textAlign = "center";
                
                var laminasReales = document.querySelectorAll("#contenedor_laminas .lamina-item");
                laminasReales.forEach((laminaReal, idx) => {
                    var laminaClon = cloneWithValues(laminaReal);
                    var canvasL = laminaReal.querySelector("canvas");
                    var dz = laminaClon.querySelector(".drop-zone");
                    if(canvasL && canvasL.width > 0 && canvasL.style.display !== 'none') {
                        var fakeUrl = "http://localhost/img_anexo_" + idx + "_" + Date.now() + ".jpg";
                        var b64 = canvasL.toDataURL("image/jpeg", 0.7).split(",")[1];
                        mhtmlImages.push({ url: fakeUrl, data: b64 });
                        var imgTag = document.createElement("img"); imgTag.src = fakeUrl; imgTag.width = Math.min(650, canvasL.width); imgTag.style.cssText = "width:" + Math.min(650, canvasL.width) + "px; height:auto; max-width:100%; display:block; margin:0 auto;";
                        if(dz) dz.replaceWith(imgTag);
                    } else {
                         var ph = document.createElement("div"); ph.innerText="[SIN IMAGEN]"; ph.style.cssText="color:#999; border:1px dashed #ccc; padding:20px; text-align:center;"; if(dz) dz.replaceWith(ph);
                    }
                    laminaClon.querySelectorAll(".editor-toolbar, .btn-del-lamina").forEach(e => e.remove());
                    anexoPanel.appendChild(flatten(laminaClon));
                });
                wrapper.append(anexoPanel);

                // GENERAR MHTML
                var css = "<style>body{font-family:Calibri,sans-serif;font-size:9pt;} h2{color:#003366;font-size:14pt;margin-top:20px;} p{text-align:justify; margin:0; margin-bottom:10px;} table{border-collapse:collapse;width:100%;} td,th{border:1px solid #ccc;padding:4px;} thead th{background:#003366;color:#fff;} .mbn-bar-table{width:2.4cm;border-collapse:collapse; table-layout:fixed;} .mbn-bar-table td{padding:0;border:none; line-height:normal;} .mbn-main-header-table{border:1px solid #ccc;margin-bottom:0;} .mbn-main-header-table tr, .mbn-main-header-table td{padding:0!important;border:none!important;vertical-align:top;} .mbn-bar-cell{width:2.4cm;min-width:2.4cm;border-right:1px solid #ccc!important;padding-right:8px!important;} .title-cell{padding-left:8px!important;padding-bottom:4px!important;font-weight:bold;color:#003366; padding-top: 2px !important;} #identificacion-content{padding-left:8px;font-size:9pt;} #identificacion-content table td{padding-top:4px!important; padding-bottom:4px!important;} .mbn-text-line-1, .mbn-text-line-2{font-size:9pt;} #parrafo_analisis{margin-top:10px;} @page Section1{margin:2cm 2.5cm; mso-header-margin:1.0cm; mso-footer-margin:1.0cm; mso-footer:f1;} div.Section1{page:Section1;} p.MsoFooter{text-align:right;font-size:9pt;} .lamina-item{page-break-inside: avoid; margin-bottom:20px;}</style>";
                
                var boundary = "----=_NextPart_000_0000";
                var mhtml = "MIME-Version: 1.0\r\nContent-Type: multipart/related; boundary=\"" + boundary + "\"\r\n\r\n";
                mhtml += "--" + boundary + "\r\nContent-Type: text/html; charset=\"utf-8\"\r\nContent-Transfer-Encoding: quoted-printable\r\n\r\n";
                var htmlBody = '<html xmlns:o="urn:schemas-microsoft-com:office:office" xmlns:w="urn:schemas-microsoft-com:office:word" xmlns="http://www.w3.org/TR/REC-html40"><head><meta charset="utf-8">' + css + '</head><body lang="ES-CL"><div class="Section1">' + wrapper.innerHTML + '</div><div style="mso-element:footer" id="f1"><p class="MsoFooter"><span style="mso-field-code:\' PAGE \'"></span></p></div></body></html>';
                
                mhtml += htmlBody.replace(/=/g, "=3D") + "\r\n\r\n";
                
                mhtmlImages.forEach(function(imgObj) {
                    mhtml += "--" + boundary + "\r\nContent-Type: image/jpeg\r\nContent-Transfer-Encoding: base64\r\nContent-Location: " + imgObj.url + "\r\n\r\n";
                    mhtml += imgObj.data + "\r\n\r\n";
                });
                mhtml += "--" + boundary + "--";

                var blob = new Blob([mhtml], { type: "application/msword" });
                var url = URL.createObjectURL(blob);
                var a = document.createElement("a");
                a.href = url;
                a.download = "Minuta_Territorial_" + window.EXPORT_FILENAME_DATE + ".doc";
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                
            } catch(e) {
                alert("Error exportando: " + e.name + ": " + e.message);
                console.error("Export Error:", e);
            }
        };

    })();
    </script>
    """
    
    return textwrap.dedent(html_content) + textwrap.dedent(js_logic)

# ===== MAIN (MODIFICADO) =====
try:
    capa_base = detectar_capa_base()
    
    # Detener ejecución si no hay capa base
    if not capa_base:
        raise Exception("No se pudo detectar la capa base en 'Deslinde MCT'. El script se detendrá.")

    DATA = build_data(capa_base)
    
    # Pasar la capa base a la función de clasificación
    clasificados = clasificar_capas(capa_base) 
    
    tabla_resumen = construir_tabla_resumen(clasificados)
    tabla_matriz = construir_tabla_matriz(clasificados)
    html = build_html(DATA, tabla_resumen, tabla_matriz)
    
    ruta = os.path.join(get_save_dir(capa_base), f"Minuta_{TITULO_ID}.html")
    with open(ruta, "w", encoding="utf-8") as f:
        f.write(html)
    
    iface.messageBar().pushMessage("✅ Minuta Generada", f"Versión {TITULO_ID} guardada en: " + ruta, level=Qgis.Info, duration=7)
    webbrowser.open(ruta)
    print(f"[INFO] HTML abierto: {ruta}")

except Exception as e:
    iface.messageBar().pushMessage("Error al generar Minuta", str(e), level=Qgis.Critical, duration=10)
    print(f"[ERROR] {e}")