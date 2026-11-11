import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, timezone, date
import io
import os
import utils 
from fpdf import FPDF
from modulos.almacen import insumos, herramientas, recibos, entradas, dinero, pedir, despachar

st.set_page_config(page_title="Almacén Central", page_icon="📦", layout="wide")
utils.aplicar_estilo_movil()
utils.validar_login() 

supabase = utils.supabase 
tz_cdmx = timezone(timedelta(hours=-6))

# ==========================================
# FUNCIONES GENERALES
# ==========================================
def tiene_permiso(permiso):
    if st.session_state.get("es_admin", False): return True
    return permiso in st.session_state.get("permisos", [])

def renderizar_manual(modulo):
    if modulo == "Insumos" or modulo == "Todos":
        st.markdown("## 📦 Módulo: Control de Insumos (Consumibles)")
        st.markdown("Este módulo controla las entradas y salidas de la materia prima del día a día (tornillos, pintura, acero, soldadura, etc.).")
        if modulo != "Todos": return

    if modulo == "Todos": st.divider()

    if modulo == "Herramientas" or modulo == "Todos":
        st.markdown("## 🛠️ Módulo: Control de Herramientas (Activos)")
        st.markdown("Control estricto para evitar pérdidas de maquinaria y equipo pesado.")
        if modulo != "Todos": return

    if modulo == "Todos": st.divider()

    if modulo == "Recibos" or modulo == "Todos":
        st.markdown("## 📑 Módulo: Recibos de Entrega OC (Salidas a Clientes)")
        st.markdown("Generación de comprobantes formales en PDF cuando se envía mobiliario.")
        if modulo != "Todos": return

    if modulo == "Todos": st.divider()

    if modulo == "Entradas" or modulo == "Todos":
        st.markdown("## 📥 Módulo: Entrada de Material")
        st.markdown("Generación de constancias en PDF cuando se recibe materia prima.")
        if modulo != "Todos": return

    if modulo == "Todos": st.divider()

    if modulo == "Dinero" or modulo == "Todos":
        st.markdown("## 💰 Módulo: Entradas y Salidas de Dinero (Caja Chica)")
        st.markdown("Control financiero amparado con tickets impresos.")
        if modulo != "Todos": return

    if modulo == "Todos": st.divider()

    if modulo == "Pedir" or modulo == "Todos":
        st.markdown("## 🛒 Módulo: Solicitar Material o Herramienta")
        st.markdown("Usa este módulo para pedir material a la ventanilla de almacén.")

@st.dialog("📖 Manual de Usuario Completo", width="large")
def modal_manual_completo():
    renderizar_manual("Todos")

@st.dialog("❓ Ayuda del Procedimiento", width="large")
def modal_ayuda_modulo(modulo):
    renderizar_manual(modulo)

def _bloque_folio_fecha(pdf, folio, fecha):
    pdf.set_font('Arial', 'B', 10)
    pdf.set_xy(140, 25); pdf.cell(25, 6, "Folio:", 0, 0, 'R'); pdf.set_font('Arial', '', 10); pdf.cell(30, 6, str(folio), 0, 1, 'L')
    pdf.set_xy(140, 31); pdf.set_font('Arial', 'B', 10); pdf.cell(25, 6, "Fecha:", 0, 0, 'R'); pdf.set_font('Arial', '', 10); pdf.cell(30, 6, str(fecha), 0, 1, 'L')

def _bloque_cajas_prov_cli(pdf, titulo1, texto1, titulo2, texto2):
    pdf.set_y(45)
    pdf.set_fill_color(230, 230, 230); pdf.set_font('Arial', 'B', 9)
    pdf.cell(95, 6, f" {titulo1}", 1, 0, 'L', True)
    pdf.cell(95, 6, f" {titulo2}", 1, 1, 'L', True)
    
    y_cajas = pdf.get_y()
    pdf.set_font('Arial', '', 8)
    
    pdf.set_xy(12, y_cajas + 2)
    pdf.multi_cell(91, 4, str(texto1))
    h1 = pdf.get_y() - y_cajas
    
    pdf.set_xy(107, y_cajas + 2)
    pdf.multi_cell(91, 4, str(texto2))
    h2 = pdf.get_y() - y_cajas
    
    alto_caja = max(h1, h2) + 4
    if alto_caja < 25: alto_caja = 25 
        
    pdf.rect(10, y_cajas, 95, alto_caja)
    pdf.rect(105, y_cajas, 95, alto_caja)
    pdf.set_xy(10, y_cajas + alto_caja + 8)

def _formatear_datos_contacto(nombre_principal, dict_datos):
    lineas = [str(nombre_principal).upper()]
    for col, val in dict_datos.items():
        if str(col).lower() not in ['id', 'created_at', 'nombre', 'empresa', 'activo'] and pd.notna(val) and str(val).strip() != "":
            nombre_col = str(col).upper()
            if nombre_col == "CODIGO_POSTAL": nombre_col = "CP"
            lineas.append(f"{nombre_col}: {str(val).upper()}")
    return "\n".join(lineas)

def numero_a_letras(numero):
    unidades = ["", "UN ", "DOS ", "TRES ", "CUATRO ", "CINCO ", "SEIS ", "SIETE ", "OCHO ", "NUEVE ", "DIEZ ", "ONCE ", "DOCE ", "TRECE ", "CATORCE ", "QUINCE ", "DIECISEIS ", "DIECISIETE ", "DIECIOCHO ", "DIECINUEVE ", "VEINTE ", "VEINTIUN ", "VEINTIDOS ", "VEINTITRES ", "VEINTICUATRO ", "VEINTICINCO ", "VEINTISEIS ", "VEINTISIETE ", "VEINTIOCHO ", "VEINTINUEVE "]
    decenas = ["", "DIEZ ", "VEINTE ", "TREINTA ", "CUARENTA ", "CINCUENTA ", "SESENTA ", "SETENTA ", "OCHENTA ", "NOVENTA "]
    centenas = ["", "CIENTO ", "DOSCIENTOS ", "TRESCIENTOS ", "CUATROCIENTOS ", "QUINIENTOS ", "SEISCIENTOS ", "SETECIENTOS ", "OCHOCIENTOS ", "NOVECIENTOS "]

    def convertir_grupo(n):
        output = ""
        if n == 100: return "CIEN "
        output += centenas[n // 100]
        n = n % 100
        if n < 30: output += unidades[n]
        else:
            output += decenas[n // 10]
            if n % 10 != 0: output += "Y " + unidades[n % 10]
        return output

    try:
        numero = float(numero)
        entero = int(numero)
        decimal = int(round((numero - entero) * 100))

        if entero == 0: letras = "CERO "
        else:
            letras = ""
            millones = entero // 1000000
            entero = entero % 1000000
            miles = entero // 1000
            resto = entero % 1000

            if millones == 1: letras += "UN MILLON "
            elif millones > 1: letras += convertir_grupo(millones) + "MILLONES "

            if miles == 1: letras += "MIL "
            elif miles > 1: letras += convertir_grupo(miles) + "MIL "

            letras += convertir_grupo(resto)

        return f"{letras.strip()} PESOS {decimal:02d}/100 M.N."
    except:
        return "CANTIDAD NO VALIDA"

class PDF(FPDF):
    def __init__(self, orientation='P', unit='mm', format='A4'):
        super().__init__(orientation, unit, format)
        self.info_reporte = None 

    def header(self):
        if os.path.exists("logo.png"):
            self.image("logo.png", 10, 8, 33) 
        else:
            self.set_font('Arial', 'B', 20)
            self.cell(40, 10, 'HEMORE', 0, 0, 'L')
        self.ln(1)

        if self.info_reporte:
            self.set_xy(0, 10); self.set_font('Arial', 'B', 16)
            self.cell(0, 10, self.info_reporte['titulo_doc'], 0, 1, 'C')
            _bloque_folio_fecha(self, self.info_reporte['folio'], self.info_reporte['fecha'])
            
            if 't1' in self.info_reporte:
                _bloque_cajas_prov_cli(self, self.info_reporte['t1'], self.info_reporte['txt1'], self.info_reporte['t2'], self.info_reporte['txt2'])
            
            if self.info_reporte.get('tipo') != 'dinero':
                self.set_font('Arial', 'B', 9); self.set_fill_color(200, 200, 200)
                self.cell(25, 7, "O.C.", 1, 0, 'C', True)
                self.cell(30, 7, "Codigo", 1, 0, 'C', True)
                self.cell(95, 7, "Descripcion", 1, 0, 'C', True)
                self.cell(20, 7, "Color", 1, 0, 'C', True)
                self.cell(20, 7, "Cant", 1, 1, 'C', True)
                self.ln() 

    def footer(self):
        self.set_y(-40)
        self.set_font('Arial', '', 8)
        nombre_entrega = ""
        if self.info_reporte and 'quien_entrega' in self.info_reporte:
            nombre_entrega = str(self.info_reporte['quien_entrega'])
            
        self.cell(90, 0, '_______________________________', 0, 0, 'C')
        self.cell(10, 0, '', 0, 0)
        self.cell(90, 0, '_______________________________', 0, 1, 'C')
        
        self.ln(2) 
        self.set_font('Arial', 'B', 8)
        self.cell(90, 4, nombre_entrega[:45], 0, 0, 'C')
        self.cell(10, 4, '', 0, 0)
        self.cell(90, 4, '', 0, 1, 'C') 
        
        self.set_font('Arial', '', 8)
        self.cell(90, 4, 'Nombre completo de quien entrega y firma', 0, 0, 'C')
        self.cell(10, 4, '', 0, 0)
        self.cell(90, 4, 'Nombre completo de quien recibe y firma', 0, 1, 'C')
        
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Pagina {self.page_no()}', 0, 0, 'C')

def generar_pdf_entrega(datos_cabecera, df_productos, folio):
    pdf = PDF()
    pdf.info_reporte = {'tipo': 'entrega', 'titulo_doc': 'Recibo de Entrega', 'folio': folio, 'fecha': datos_cabecera['fecha'], 't1': "Proveedor", 'txt1': datos_cabecera['prov_texto'], 't2': "Cliente", 'txt2': datos_cabecera['cli_texto'], 'quien_entrega': datos_cabecera.get('quien_entrega', '')}
    pdf.add_page() 
    pdf.set_auto_page_break(auto=True, margin=45)
    _dibujar_filas_productos(pdf, datos_cabecera.get('oc', ''), df_productos)
    _bloque_observaciones(pdf, datos_cabecera.get('observaciones', ''))
    return pdf.output(dest='S').encode('latin-1')

def generar_pdf_entrada(datos_cabecera, df_productos, folio):
    pdf = PDF()
    pdf.info_reporte = {'tipo': 'entrada', 'titulo_doc': 'Constancia de Entrada', 'folio': folio, 'fecha': datos_cabecera['fecha'], 't1': "Proveedor", 'txt1': datos_cabecera['prov_texto'], 't2': "Receptor", 'txt2': datos_cabecera['hemore_texto'], 'quien_entrega': datos_cabecera.get('quien_entrega', '')}
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=45)
    _dibujar_filas_productos(pdf, datos_cabecera.get('oc', ''), df_productos)
    _bloque_observaciones(pdf, datos_cabecera.get('observaciones', ''))
    return pdf.output(dest='S').encode('latin-1')

def _dibujar_filas_productos(pdf, oc, df_productos):
    pdf.set_font('Arial', '', 8)
    line_height = 3.5
    min_row_height = 7.0
    
    for index, row in df_productos.iterrows():
        textos = [str(oc), str(row['Código']), str(row['Descripción']), str(row['Color']), str(row['Cantidad'])]
        anchos = [25, 30, 95, 20, 20]
        alineaciones = ['C', 'C', 'L', 'C', 'C']
        
        lineas_por_celda = []
        max_lines_in_row = 1
        
        for i, text in enumerate(textos):
            max_w = anchos[i] - 2 
            lines = []
            current_line = ""
            words = str(text).split(" ")
            
            for word in words:
                if pdf.get_string_width(word) > max_w:
                    if current_line:
                        lines.append(current_line)
                        current_line = ""
                    temp_word = ""
                    for char in word:
                        if pdf.get_string_width(temp_word + char) > max_w:
                            lines.append(temp_word)
                            temp_word = char
                        else:
                            temp_word += char
                    current_line = temp_word
                else:
                    test_line = current_line + " " + word if current_line else word
                    if pdf.get_string_width(test_line) > max_w:
                        lines.append(current_line)
                        current_line = word
                    else:
                        current_line = test_line
                        
            if current_line: lines.append(current_line)
            if not lines: lines = [""]
            if len(lines) > 3:
                lines = lines[:3]
                if len(lines[2]) > 3: lines[2] = lines[2][:-3] + "..."
            
            lineas_por_celda.append(lines)
            if len(lines) > max_lines_in_row: max_lines_in_row = len(lines)
        
        altura_fila = max(min_row_height, (max_lines_in_row * line_height) + 2.0)
        if pdf.get_y() + altura_fila > 250: pdf.add_page()
            
        start_x = pdf.get_x()
        start_y = pdf.get_y()
        
        for i in range(5):
            x_celda = start_x + sum(anchos[:i])
            y_celda = start_y
            pdf.rect(x_celda, y_celda, anchos[i], altura_fila)
            espacio_libre_y = altura_fila - (len(lineas_por_celda[i]) * line_height)
            y_texto = y_celda + (espacio_libre_y / 2)
            
            for j, linea in enumerate(lineas_por_celda[i]):
                pdf.set_xy(x_celda, y_texto + (j * line_height))
                pdf.cell(anchos[i], line_height, linea, border=0, ln=0, align=alineaciones[i])
                
        pdf.set_xy(start_x, start_y + altura_fila)

def _bloque_observaciones(pdf, texto):
    pdf.ln(8); pdf.set_font('Arial', 'B', 9); pdf.write(5, "Observaciones: "); pdf.set_font('Arial', '', 9)
    pdf.write(5, str(texto) if texto else "_"*110)

def generar_pdf_ticket_dinero(datos, folio):
    pdf = FPDF(orientation='P', unit='mm', format=(108, 140))
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=10)
    
    if os.path.exists("logo.png"): pdf.image("logo.png", 10, 8, 25) 
    else:
        pdf.set_font('Arial', 'B', 14)
        pdf.cell(0, 10, 'HEMORE', 0, 1, 'L')
    
    pdf.set_xy(10, 30)
    pdf.set_font('Arial', 'B', 11)
    pdf.cell(0, 5, "COMPROBANTE DE MOVIMIENTO", 0, 1, 'C')
    pdf.ln(5)
    
    pdf.set_font('Arial', 'B', 10)
    entrada_check = "[ X ] ENTRADA" if datos['tipo'] == "Entrada" else "[   ] ENTRADA"
    salida_check = "[ X ] SALIDA" if datos['tipo'] == "Salida" else "[   ] SALIDA"
    pdf.cell(0, 5, f"{entrada_check}         {salida_check}", 0, 1, 'C')
    pdf.ln(6)
    
    pdf.set_font('Arial', 'B', 9)
    pdf.cell(15, 5, "Folio:", 0, 0); pdf.set_font('Arial', '', 9); pdf.cell(30, 5, str(folio), 0, 0)
    pdf.set_font('Arial', 'B', 9)
    pdf.cell(15, 5, "Fecha:", 0, 0); pdf.set_font('Arial', '', 9); pdf.cell(0, 5, str(datos['fecha']), 0, 1)
    pdf.ln(6)
    
    pdf.set_font('Arial', 'B', 9); pdf.cell(25, 5, "Entrega:", 0, 0)
    pdf.set_font('Arial', '', 9); pdf.cell(0, 5, str(datos['quien_entrega'])[:45], 0, 1)
    
    pdf.set_font('Arial', 'B', 9); pdf.cell(25, 5, "Recibe:", 0, 0)
    pdf.set_font('Arial', '', 9); pdf.cell(0, 5, str(datos['quien_recibe'])[:45], 0, 1)
    pdf.ln(6)
    
    pdf.set_font('Arial', 'B', 10); pdf.cell(20, 6, "Cantidad:", 0, 0)
    pdf.set_font('Arial', 'B', 12); pdf.cell(0, 6, f"$ {datos['monto']:,.2f} MXN", 0, 1)
    
    pdf.set_font('Arial', '', 7)
    pdf.multi_cell(0, 4, f"({numero_a_letras(datos['monto'])})")
    pdf.ln(6)
    
    pdf.set_font('Arial', 'B', 9); pdf.cell(0, 5, "Detalle / Descripcion:", 0, 1)
    pdf.set_font('Arial', '', 8)
    pdf.multi_cell(0, 4, str(datos['descripcion']))
    
    pdf.set_y(-25)
    pdf.set_font('Arial', '', 7)
    pdf.cell(38, 0, "_"*28, 0, 0, 'C')
    pdf.cell(12, 0, "", 0, 0)
    pdf.cell(38, 0, "_"*28, 0, 1, 'C')
    pdf.ln(4)
    pdf.cell(38, 3, "Firma de quien entrega", 0, 0, 'C')
    pdf.cell(12, 3, "", 0, 0)
    pdf.cell(38, 3, "Firma de quien recibe", 0, 1, 'C')
    return pdf.output(dest='S').encode('latin-1')

def convertir_df_a_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output) as writer: df.to_excel(writer, index=False, sheet_name='Reporte')
    return output.getvalue()

# ==========================================
# MENÚ LATERAL 
# ==========================================
st.sidebar.title("🏭 Almacén Central")
opciones_permitidas = []

if tiene_permiso("Almacén: Solicitar Material"): opciones_permitidas.append("🛒 Pedir Material")
if tiene_permiso("Almacén: Movimientos Insumos") or tiene_permiso("Almacén: Ver Existencias Insumos") or tiene_permiso("Almacén: Eliminar Historial Insumos"): opciones_permitidas.append("Insumos (Consumibles)")
if tiene_permiso("Almacén: Prestar/Devolver Herramientas") or tiene_permiso("Almacén: Eliminar Historial Herramientas"): opciones_permitidas.append("Herramientas (Activos)")
if tiene_permiso("Almacén: Generar Recibos OC") or tiene_permiso("Almacén: Editar/Eliminar Recibos OC"): opciones_permitidas.append("Recibos de Entrega OC")
if tiene_permiso("Almacén: Registrar Entrada Material") or tiene_permiso("Almacén: Editar/Eliminar Entrada Material"): opciones_permitidas.append("Entrada de Material")
if tiene_permiso("Finanzas: Registrar Movimientos Dinero") or tiene_permiso("Finanzas: Editar/Eliminar Movimientos Dinero"): opciones_permitidas.append("Entradas y Salidas de Dinero")
if tiene_permiso("Almacén: Despachar Pedidos"): opciones_permitidas.append("🔔 Despachar Pedidos")

if not opciones_permitidas:
    st.warning("🔒 No tienes permisos asignados en el sistema.")
    st.stop()

opcion_almacen = st.sidebar.radio("Selecciona Operación:", opciones_permitidas)

st.sidebar.divider()
if st.sidebar.button("📖 Leer Manual Completo", use_container_width=True): modal_manual_completo()

c_tit, c_ayu = st.columns([9, 1])
with c_tit:
    if opcion_almacen == "Insumos (Consumibles)": st.title("📦 CONTROL DE INSUMOS")
    elif opcion_almacen == "Herramientas (Activos)": st.title("🛠️ CONTROL DE HERRAMIENTAS")
    elif opcion_almacen == "Recibos de Entrega OC": st.title("📑 CONTROL DE RECIBOS DE ENTREGA OC")
    elif opcion_almacen == "Entrada de Material": st.title("📥 CONTROL DE ENTRADA DE MATERIAL")
    elif opcion_almacen == "Entradas y Salidas de Dinero": st.title("💰 CONTROL DE ENTRADAS Y SALIDAS DE DINERO")
    elif opcion_almacen == "🛒 Pedir Material": st.title("🛒 SOLICITAR MATERIAL O HERRAMIENTA")
    elif opcion_almacen == "🔔 Despachar Pedidos": st.title("🔔 REQUERIMIENTOS PENDIENTES")
    else: st.title(f"{opcion_almacen}")
    
with c_ayu:
    if opcion_almacen == "Insumos (Consumibles)":
        if st.button("❓ Ayuda", key="ayu_ins"): modal_ayuda_modulo("Insumos")
    elif opcion_almacen == "Herramientas (Activos)":
        if st.button("❓ Ayuda", key="ayu_herr"): modal_ayuda_modulo("Herramientas")
    elif opcion_almacen == "Recibos de Entrega OC":
        if st.button("❓ Ayuda", key="ayu_rec"): modal_ayuda_modulo("Recibos")
    elif opcion_almacen == "Entrada de Material":
        if st.button("❓ Ayuda", key="ayu_ent"): modal_ayuda_modulo("Entradas")
    elif opcion_almacen == "Entradas y Salidas de Dinero":
        if st.button("❓ Ayuda", key="ayu_din"): modal_ayuda_modulo("Dinero")
    elif opcion_almacen == "🛒 Pedir Material": 
        if st.button("❓ Ayuda", key="ayu_pedir"): modal_ayuda_modulo("Pedir")

# ==================================================
# 🚦 ENRUTADOR DE MÓDULOS DE ALMACÉN
# ==================================================
if opcion_almacen == "Insumos (Consumibles)":
    insumos.renderizar(tiene_permiso)

elif opcion_almacen == "Herramientas (Activos)":
    herramientas.renderizar(tiene_permiso)

elif opcion_almacen == "Recibos de Entrega OC":
    recibos.renderizar(tiene_permiso, _formatear_datos_contacto, generar_pdf_entrega)

elif opcion_almacen == "Entrada de Material":
    entradas.renderizar(tiene_permiso, _formatear_datos_contacto, generar_pdf_entrada)

elif opcion_almacen == "Entradas y Salidas de Dinero":
    dinero.renderizar(tiene_permiso, generar_pdf_ticket_dinero)

elif opcion_almacen == "🛒 Pedir Material":
    pedir.renderizar()

elif opcion_almacen == "🔔 Despachar Pedidos":
    despachar.renderizar()
