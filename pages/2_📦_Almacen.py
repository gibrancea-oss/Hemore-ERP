import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, date
import time
import io
import os
import utils 
from fpdf import FPDF

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="Almacén Central", page_icon="📦", layout="wide")

# --- 🔒 SEGURIDAD ---
utils.validar_login() 
# --------------------

supabase = utils.supabase 

# ==========================================
# FUNCIÓN DE PERMISOS (LA MEJORA)
# ==========================================
def tiene_permiso(permiso):
    if st.session_state.get("es_admin", False): return True
    return permiso in st.session_state.get("permisos", [])

# --- HELPER FUNCTIONS ---
def _bloque_folio_fecha(pdf, folio, fecha):
    pdf.set_font('Arial', 'B', 10)
    pdf.set_xy(140, 25); pdf.cell(25, 6, "Folio:", 0, 0, 'R'); pdf.set_font('Arial', '', 10); pdf.cell(30, 6, str(folio), 0, 1, 'L')
    pdf.set_xy(140, 31); pdf.set_font('Arial', 'B', 10); pdf.cell(25, 6, "Fecha:", 0, 0, 'R'); pdf.set_font('Arial', '', 10); pdf.cell(30, 6, str(fecha), 0, 1, 'L')

# ✨ MEJORA: CAJAS DINÁMICAS QUE SE AJUSTAN AL TEXTO ✨
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
    if alto_caja < 25:
        alto_caja = 25 
        
    pdf.rect(10, y_cajas, 95, alto_caja)
    pdf.rect(105, y_cajas, 95, alto_caja)
    
    pdf.set_xy(10, y_cajas + alto_caja + 8)

# ✨ MEJORA: MAYÚSCULAS Y REEMPLAZO POR "CP" ✨
def _formatear_datos_contacto(nombre_principal, dict_datos):
    lineas = [str(nombre_principal).upper()]
    for col, val in dict_datos.items():
        if str(col).lower() not in ['id', 'created_at', 'nombre', 'empresa', 'activo'] and pd.notna(val) and str(val).strip() != "":
            nombre_col = str(col).upper()
            if nombre_col == "CODIGO_POSTAL":
                nombre_col = "CP"
            lineas.append(f"{nombre_col}: {str(val).upper()}")
    return "\n".join(lineas)

# ✨ HELPER: NÚMERO A LETRAS (PARA DINERO) ✨
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

# --- CLASE PDF PERSONALIZADA ---
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

    # ✨ MEJORA: FOOTER DINÁMICO CON NOMBRE Y FIRMAS ACTUALIZADAS ✨
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

# --- GENERADORES DE PDF ---
def generar_pdf_entrega(datos_cabecera, df_productos, folio):
    pdf = PDF()
    pdf.info_reporte = {
        'tipo': 'entrega', 'titulo_doc': 'Recibo de Entrega', 'folio': folio, 'fecha': datos_cabecera['fecha'],
        't1': "Proveedor", 'txt1': datos_cabecera['prov_texto'], 't2': "Cliente", 'txt2': datos_cabecera['cli_texto'],
        'quien_entrega': datos_cabecera.get('quien_entrega', '') 
    }
    pdf.add_page() 
    pdf.set_auto_page_break(auto=True, margin=45)
    _dibujar_filas_productos(pdf, datos_cabecera.get('oc', ''), df_productos)
    _bloque_observaciones(pdf, datos_cabecera.get('observaciones', ''))
    return pdf.output(dest='S').encode('latin-1')

def generar_pdf_entrada(datos_cabecera, df_productos, folio):
    pdf = PDF()
    pdf.info_reporte = {
        'tipo': 'entrada', 'titulo_doc': 'Constancia de Entrada', 'folio': folio, 'fecha': datos_cabecera['fecha'],
        't1': "Proveedor", 'txt1': datos_cabecera['prov_texto'], 't2': "Receptor", 'txt2': datos_cabecera['hemore_texto'],
        'quien_entrega': datos_cabecera.get('quien_entrega', '') 
    }
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=45)
    _dibujar_filas_productos(pdf, datos_cabecera.get('oc', ''), df_productos)
    _bloque_observaciones(pdf, datos_cabecera.get('observaciones', ''))
    return pdf.output(dest='S').encode('latin-1')

# ✨ MEJORA: CELDAS DINÁMICAS (MÁX. 3 LÍNEAS) CON CORTE SEGURO Y SIN ERRORES DE PÁGINA ✨
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
                        
            if current_line:
                lines.append(current_line)
            
            if not lines:
                lines = [""]
                
            if len(lines) > 3:
                lines = lines[:3]
                if len(lines[2]) > 3:
                    lines[2] = lines[2][:-3] + "..."
            
            lineas_por_celda.append(lines)
            if len(lines) > max_lines_in_row:
                max_lines_in_row = len(lines)
        
        altura_fila = max(min_row_height, (max_lines_in_row * line_height) + 2.0)
        
        if pdf.get_y() + altura_fila > 250:
            pdf.add_page()
            
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

# ✨ GENERADOR PDF TICKET PARA DINERO (CUARTO DE CARTA) ✨
def generar_pdf_ticket_dinero(datos, folio):
    pdf = FPDF(orientation='P', unit='mm', format=(108, 140))
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=10)
    
    if os.path.exists("logo.png"):
        pdf.image("logo.png", 10, 8, 25) 
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
# MENÚ LATERAL (CON CANDADOS DE PERMISO)
# ==========================================
st.sidebar.title("🏭 Almacén Central")

opciones_permitidas = []
if tiene_permiso("Almacén: Movimientos Insumos") or tiene_permiso("Almacén: Ver Existencias Insumos") or tiene_permiso("Almacén: Eliminar Historial Insumos"):
    opciones_permitidas.append("Insumos (Consumibles)")
if tiene_permiso("Almacén: Prestar/Devolver Herramientas") or tiene_permiso("Almacén: Eliminar Historial Herramientas"):
    opciones_permitidas.append("Herramientas (Activos)")
if tiene_permiso("Almacén: Generar Recibos OC") or tiene_permiso("Almacén: Editar/Eliminar Recibos OC"):
    opciones_permitidas.append("Recibos de Entrega OC")
if tiene_permiso("Almacén: Registrar Entrada Material") or tiene_permiso("Almacén: Editar/Eliminar Entrada Material"):
    opciones_permitidas.append("Entrada de Material")
if tiene_permiso("Finanzas: Registrar Movimientos Dinero") or tiene_permiso("Finanzas: Editar/Eliminar Movimientos Dinero"):
    opciones_permitidas.append("Entradas y Salidas de Dinero")

if not opciones_permitidas:
    st.warning("🔒 No tienes permisos asignados para operar en ningún módulo del Almacén.")
    st.stop()

opcion_almacen = st.sidebar.radio(
    "Selecciona Operación:",
    opciones_permitidas
)

st.title(f"Control de {opcion_almacen.split(' (')[0]}")

# ==================================================
# 🧱 OPCIÓN 1: INSUMOS
# ==================================================
if opcion_almacen == "Insumos (Consumibles)":
    try:
        response_ins = supabase.table("Insumos").select("*").order("id").execute()
        df_ins = pd.DataFrame(response_ins.data)
        if not df_ins.empty:
            df_ins.columns = df_ins.columns.str.lower()
            if "descripcion" not in df_ins.columns: df_ins["descripcion"] = "Sin Nombre"
            if "cantidad" not in df_ins.columns: df_ins["cantidad"] = 0
            if "unidad" not in df_ins.columns: df_ins["unidad"] = "Pzas"
            if "ubicacion" not in df_ins.columns: df_ins["ubicacion"] = "S/U"

        df_personal = pd.DataFrame(supabase.table("Personal").select("nombre").eq("activo", True).execute().data)
        lista_personal = df_personal['nombre'].tolist() if not df_personal.empty else []
    except Exception as e: 
        st.error(f"Error cargando base de datos: {e}")
        df_ins = pd.DataFrame()
        lista_personal = []

    tab_op, tab_exist, tab_hist = st.tabs(["📝 Registrar Movimientos", "📊 Existencias", "📜 Historial"])
    
    with tab_op:
        if tiene_permiso("Almacén: Movimientos Insumos"):
            if df_ins.empty: st.warning("No hay insumos registrados.")
            else:
                tipo_operacion = st.radio("Acción:", ["📤 Entrega (Salida)", "📥 Re-Stock (Entrada)"], horizontal=True)
                c_form, c_info = st.columns([2, 1])
                with c_form:
                    lista_busqueda = [f"{row['codigo']} | {row['descripcion']}" for i, row in df_ins.iterrows()]
                    seleccion = st.selectbox("Buscar:", lista_busqueda)
                    
                    if seleccion:
                        codigo_sel = seleccion.split(" | ")[0]
                        item_actual = df_ins[df_ins["codigo"] == codigo_sel].iloc[0]
                        cant_mov = st.number_input("Cantidad", min_value=1.0, value=1.0)
                        
                        if "Entrega" in tipo_operacion:
                            responsable = st.selectbox("Entregar a:", lista_personal)
                            if st.button("Confirmar Salida", type="primary"):
                                if item_actual['cantidad'] >= cant_mov:
                                    new_st = float(item_actual['cantidad'] - cant_mov)
                                    supabase.table("Insumos").update({"Cantidad": new_st}).eq("id", int(item_actual['id'])).execute()
                                    try: supabase.table("Historial_Insumos").insert({"fecha": datetime.now().strftime('%Y-%m-%d %H:%M'), "codigo": str(item_actual['codigo']), "descripcion": str(item_actual['descripcion']), "tipo_movimiento": "Salida", "cantidad": float(cant_mov), "responsable": str(responsable)}).execute()
                                    except: pass
                                    st.success("✅ Salida registrada"); time.sleep(1); st.rerun()
                                else: st.error("Stock insuficiente")
                        else:
                            if st.button("Confirmar Entrada"):
                                new_st = float(item_actual['cantidad'] + cant_mov)
                                supabase.table("Insumos").update({"Cantidad": new_st}).eq("id", int(item_actual['id'])).execute()
                                try: supabase.table("Historial_Insumos").insert({"fecha": datetime.now().strftime('%Y-%m-%d %H:%M'), "codigo": str(item_actual['codigo']), "descripcion": str(item_actual['descripcion']), "tipo_movimiento": "Re-stock", "cantidad": float(cant_mov), "responsable": "Almacén"}).execute()
                                except: pass
                                st.success("✅ Entrada registrada"); time.sleep(1); st.rerun()
                
                with c_info: 
                    if seleccion: 
                        st.metric("Stock Actual", item_actual['cantidad'])
                        st.write(f"📍 Ubicación: {item_actual['ubicacion']}")
        else:
            st.warning("🔒 No tienes permiso para registrar movimientos de insumos.")

    with tab_exist:
        if tiene_permiso("Almacén: Ver Existencias Insumos"):
            if not df_ins.empty:
                df_view = df_ins[["codigo", "descripcion", "cantidad", "unidad", "ubicacion"]].rename(columns={"codigo": "Código", "descripcion": "Descripción", "cantidad": "Stock", "unidad": "Unidad", "ubicacion": "Ubicación"})
                st.download_button("📥 Descargar Existencias", convertir_df_a_excel(df_view), "Existencias.xlsx")
                st.dataframe(df_view, use_container_width=True)
        else:
            st.warning("🔒 No tienes permiso para ver el stock de existencias.")

    with tab_hist:
        @st.dialog("Detalles del Movimiento - Insumos")
        def ver_detalle_insumo(mov_id, df_source):
            row_info = df_source[df_source['id'] == mov_id].iloc[0]
            st.markdown("#### 📄 Información del Registro")
            st.write(f"**Fecha y Hora:** {row_info.get('fecha', '')}")
            st.write(f"**Código:** {row_info.get('codigo', '')}")
            st.write(f"**Descripción:** {row_info.get('descripcion', '')}")
            st.write(f"**Tipo de Movimiento:** {row_info.get('tipo_movimiento', '')}")
            st.write(f"**Cantidad:** {row_info.get('cantidad', '')}")
            st.write(f"**Responsable:** {row_info.get('responsable', '')}")
            
            st.divider()
            
            if tiene_permiso("Almacén: Eliminar Historial Insumos"):
                if st.button("🗑️ ELIMINAR ESTE REGISTRO", type="secondary", use_container_width=True):
                    supabase.table("Historial_Insumos").delete().eq("id", int(mov_id)).execute()
                    st.warning("Registro eliminado exitosamente."); time.sleep(1); st.rerun()
            else:
                st.warning("🔒 No tienes permiso para eliminar registros.")

        try:
            res_h = supabase.table("Historial_Insumos").select("*").order("id", desc=True).limit(200).execute()
            df_hist_ins = pd.DataFrame(res_h.data)
            
            if not df_hist_ins.empty:
                c_h1, c_h2, c_h3, c_h4, c_h5 = st.columns([2, 2, 3, 1, 2])
                c_h1.markdown("**Fecha**")
                c_h2.markdown("**Código**")
                c_h3.markdown("**Movimiento**")
                c_h4.markdown("**Cant**")
                c_h5.markdown("**Acción**")
                
                for idx, row in df_hist_ins.iterrows():
                    c1, c2, c3, c4, c5 = st.columns([2, 2, 3, 1, 2])
                    c1.write(row.get('fecha', ''))
                    c2.write(row.get('codigo', ''))
                    c3.write(row.get('tipo_movimiento', ''))
                    c4.write(row.get('cantidad', ''))
                    if c5.button("Ver Detalle", key=f"btn_ins_{row['id']}"):
                        ver_detalle_insumo(row['id'], df_hist_ins)
            else:
                st.info("No hay movimientos registrados.")
        except Exception as e: 
            st.error(f"Error cargando historial: {e}")

# ==================================================
# 🔧 OPCIÓN 2: HERRAMIENTAS
# ==================================================
elif opcion_almacen == "Herramientas (Activos)":
    try:
        df_her = pd.DataFrame(supabase.table("Herramientas").select("*").order("id").execute().data)
        df_personal = pd.DataFrame(supabase.table("Personal").select("nombre").eq("activo", True).execute().data)
        lista_personal = df_personal['nombre'].tolist() if not df_personal.empty else []
    except: df_her = pd.DataFrame(); lista_personal = []

    if not df_her.empty:
        if "Responsable" not in df_her.columns: df_her["Responsable"] = "Bodega"
        df_her["Responsable"].fillna("Bodega", inplace=True)

    tab1, tab2, tab3 = st.tabs(["Movimientos", "Inventario", "Historial"])
    
    with tab1:
        if tiene_permiso("Almacén: Prestar/Devolver Herramientas"):
            c1, c2 = st.columns(2)
            with c1:
                st.info("Prestar")
                if not df_her.empty:
                    bodega = df_her[df_her["Responsable"]=="Bodega"]
                    if not bodega.empty:
                        sel = st.selectbox("Herramienta", bodega["Herramienta"].tolist())
                        resp = st.selectbox("A quien", lista_personal)
                        if st.button("Prestar"):
                            id_h = bodega[bodega["Herramienta"]==sel].iloc[0]["id"]
                            supabase.table("Herramientas").update({"Responsable": str(resp)}).eq("id", int(id_h)).execute()
                            try: supabase.table("Historial_Herramientas").insert({"Fecha_Hora": datetime.now().strftime('%Y-%m-%d %H:%M'), "Herramienta": str(sel), "Movimiento": "Préstamo", "Responsable": str(resp)}).execute()
                            except: pass
                            st.success("Prestado"); time.sleep(1); st.rerun()
            with c2:
                st.warning("Devolver")
                if not df_her.empty:
                    prestadas = df_her[df_her["Responsable"]!="Bodega"]
                    if not prestadas.empty:
                        sel_d = st.selectbox("Devolver", prestadas["Herramienta"].tolist())
                        if st.button("Devolver"):
                            id_h = prestadas[prestadas["Herramienta"]==sel_d].iloc[0]["id"]
                            supabase.table("Herramientas").update({"Responsable": "Bodega"}).eq("id", int(id_h)).execute()
                            try: supabase.table("Historial_Herramientas").insert({"Fecha_Hora": datetime.now().strftime('%Y-%m-%d %H:%M'), "Herramienta": str(sel_d), "Movimiento": "Devolución", "Responsable": "Bodega"}).execute()
                            except: pass
                            st.success("Devuelto"); time.sleep(1); st.rerun()
        else:
            st.warning("🔒 No tienes permiso para prestar ni devolver herramientas.")

    with tab2: st.dataframe(df_her, use_container_width=True)

    with tab3:
        @st.dialog("Detalles del Movimiento - Herramientas")
        def ver_detalle_herramienta(mov_id, df_source):
            row_info = df_source[df_source['id'] == mov_id].iloc[0]
            st.markdown("#### 📄 Información del Registro")
            st.write(f"**Fecha y Hora:** {row_info.get('Fecha_Hora', '')}")
            st.write(f"**Herramienta:** {row_info.get('Herramienta', '')}")
            st.write(f"**Tipo de Movimiento:** {row_info.get('Movimiento', '')}")
            st.write(f"**Responsable:** {row_info.get('Responsable', '')}")
            
            st.divider()
            
            if tiene_permiso("Almacén: Eliminar Historial Herramientas"):
                if st.button("🗑️ ELIMINAR ESTE REGISTRO", type="secondary", use_container_width=True):
                    supabase.table("Historial_Herramientas").delete().eq("id", int(mov_id)).execute()
                    st.warning("Registro eliminado exitosamente."); time.sleep(1); st.rerun()
            else:
                st.warning("🔒 No tienes permiso para eliminar registros.")

        try:
            res_h = supabase.table("Historial_Herramientas").select("*").order("id", desc=True).limit(200).execute()
            df_hist_herr = pd.DataFrame(res_h.data)
            
            if not df_hist_herr.empty:
                c_h1, c_h2, c_h3, c_h4, c_h5 = st.columns([2, 3, 2, 2, 2])
                c_h1.markdown("**Fecha**")
                c_h2.markdown("**Herramienta**")
                c_h3.markdown("**Movimiento**")
                c_h4.markdown("**Responsable**")
                c_h5.markdown("**Acción**")
                
                for idx, row in df_hist_herr.iterrows():
                    c1, c2, c3, c4, c5 = st.columns([2, 3, 2, 2, 2])
                    c1.write(row.get('Fecha_Hora', ''))
                    c2.write(row.get('Herramienta', ''))
                    c3.write(row.get('Movimiento', ''))
                    c4.write(row.get('Responsable', ''))
                    if c5.button("Ver Detalle", key=f"btn_herr_{row['id']}"):
                        ver_detalle_herramienta(row['id'], df_hist_herr)
            else:
                st.info("No hay movimientos registrados.")
        except Exception as e: 
            st.error(f"Error cargando historial: {e}")

# ==================================================
# 📑 OPCIÓN 3: RECIBOS DE ENTREGA OC 
# ==================================================
elif opcion_almacen == "Recibos de Entrega OC":
    st.markdown("### 📑 Recibos de Entrega (Salidas a Clientes)")
    try:
        res_cli = supabase.table("Clientes").select("*").execute(); df_clientes = pd.DataFrame(res_cli.data)
        lista_nombres_cli = df_clientes['nombre'].tolist() if not df_clientes.empty else []
        res_prov = supabase.table("Proveedores").select("*").execute(); df_proveedores = pd.DataFrame(res_prov.data)
        col_p_name = 'empresa' if 'empresa' in df_proveedores.columns else 'nombre'
        lista_nombres_prov = df_proveedores[col_p_name].tolist() if not df_proveedores.empty else []
        df_personal = pd.DataFrame(supabase.table("Personal").select("nombre").eq("activo", True).execute().data)
        lista_personal = df_personal['nombre'].tolist() if not df_personal.empty else []
    except: lista_nombres_cli = []; lista_nombres_prov = []; lista_personal = []; df_clientes = pd.DataFrame(); df_proveedores = pd.DataFrame()

    tab_nuevo, tab_historial = st.tabs(["➕ Nuevo Recibo", "📜 Historial"])
    
    with tab_nuevo:
        if tiene_permiso("Almacén: Generar Recibos OC"):
            with st.container(border=True):
                st.subheader("Datos de la Entrega")
                c1, c2, c3 = st.columns([1, 1, 1])
                oc_input = c1.text_input("Orden de Compra (O.C.)", placeholder="Ej. 2183")
                fecha_input = c2.date_input("Fecha", value=datetime.now().date())
                prov_input = c3.selectbox("Proveedor (Origen):", lista_nombres_prov, index=None, placeholder="Hemore...")
                cliente_input = st.selectbox("Cliente (Destino):", lista_nombres_cli, index=None)
                
                if "data_recibo" not in st.session_state: st.session_state["data_recibo"] = pd.DataFrame([{"Código": "", "Descripción": "", "Color": "", "Cantidad": 0}], columns=["Código", "Descripción", "Color", "Cantidad"])
                edited_df = st.data_editor(st.session_state["data_recibo"], num_rows="dynamic", use_container_width=True)
                observaciones = st.text_area("Observaciones:")
                quien_entrega_input = st.selectbox("Quien entrega:", lista_personal)
                
                if st.button("💾 Guardar y PDF", type="primary"):
                    items = edited_df[edited_df["Código"].astype(str).str.strip() != ""]

                    errores = []
                    if not oc_input: errores.append("- **Falta O.C.**")
                    if not prov_input: errores.append("- **Falta Proveedor**")
                    if not cliente_input: errores.append("- **Falta Cliente**")
                    if items.empty: errores.append("- **Tabla vacía**")

                    if errores:
                        st.error("⚠️ **No se pudo guardar el recibo debido a los siguientes errores:**\n\n" + "\n".join(errores))
                    else:
                        for _, row in items.iterrows():
                            val_cant = row.get("Cantidad", 0)
                            try: cant_f = float(val_cant) if val_cant is not None else 0.0
                            except: cant_f = 0.0

                            data_to_insert = {
                                "fecha": str(fecha_input.isoformat()), "oc": str(oc_input), 
                                "cliente": str(cliente_input), "proveedor": str(prov_input), 
                                "codigo": str(row["Código"]), "descripcion": str(row["Descripción"]), 
                                "color": str(row["Color"]), "cantidad": cant_f, 
                                "usuario": str(quien_entrega_input), "observaciones": str(observaciones)
                            }
                            supabase.table("Recibos_OC").insert(data_to_insert).execute()
                        
                        try:
                            cli_data = df_clientes[df_clientes['nombre'] == cliente_input].iloc[0]
                            prov_data = df_proveedores[df_proveedores[col_p_name] == prov_input].iloc[0]
                            last_id = supabase.table("Recibos_OC").select("id").order("id", desc=True).limit(1).execute().data[0]['id']
                            prov_text = _formatear_datos_contacto(prov_input, prov_data)
                            cli_text = _formatear_datos_contacto(cliente_input, cli_data)
                            datos_pdf = {"oc": oc_input, "fecha": fecha_input.strftime("%d/%m/%Y"), "observaciones": observaciones, "prov_texto": prov_text, "cli_texto": cli_text, "quien_entrega": quien_entrega_input}
                            pdf_bytes = generar_pdf_entrega(datos_pdf, items, last_id)
                            st.success("✅ Guardado correctamente.")
                            st.download_button("🖨️ Imprimir PDF", pdf_bytes, f"Recibo_{oc_input}.pdf", "application/pdf")
                        except Exception as e: 
                            st.error(f"Error interno al generar el archivo PDF: {e}")
        else:
            st.warning("🔒 No tienes permiso para generar nuevos recibos OC.")

    with tab_historial:
        @st.dialog("Detalles de Orden de Compra", width="large")
        def ver_editar_oc(oc_seleccionada, df_source):
            df_oc = df_source[df_source['oc'] == oc_seleccionada].copy()
            if not df_oc.empty:
                row_info = df_oc.iloc[0]
                
                st.markdown(f"#### 📄 Gestionar O.C. {oc_seleccionada}")
                
                try: fecha_dt = pd.to_datetime(row_info['fecha']).date()
                except: fecha_dt = datetime.now().date()
                
                idx_cli = lista_nombres_cli.index(row_info['cliente']) if row_info['cliente'] in lista_nombres_cli else None
                idx_prov = lista_nombres_prov.index(row_info['proveedor']) if row_info['proveedor'] in lista_nombres_prov else None
                idx_usr = lista_personal.index(row_info.get('usuario', '')) if row_info.get('usuario', '') in lista_personal else None
                
                c1, c2, c3, c4 = st.columns(4)
                n_fecha = c1.date_input("Fecha", value=fecha_dt, key="d_fecha")
                n_cli = c2.selectbox("Cliente", lista_nombres_cli, index=idx_cli, key="d_cli")
                n_prov = c3.selectbox("Proveedor", lista_nombres_prov, index=idx_prov, key="d_prov")
                n_entrega = c4.selectbox("Quien entrega", lista_personal, index=idx_usr, key="d_usr")
                
                n_obs = st.text_area("Observaciones", value=row_info.get('observaciones', ''), key="d_obs")
                
                st.divider()
                st.write("**Productos:**")
                df_edit_prod = df_oc[['id', 'codigo', 'descripcion', 'color', 'cantidad']].copy()
                df_edit_prod.rename(columns={'codigo':'Código', 'descripcion':'Descripción', 'color':'Color', 'cantidad':'Cantidad'}, inplace=True)
                
                # ✨ MEJORA: AÑADIDO NUM_ROWS="DYNAMIC" PARA PODER AGREGAR FILAS ✨
                edited_prods = st.data_editor(df_edit_prod, use_container_width=True, hide_index=True, disabled=['id'], num_rows="dynamic", key="d_editor")
                
                col_g, col_p = st.columns(2)
                
                if tiene_permiso("Almacén: Editar/Eliminar Recibos OC"):
                    if col_g.button("💾 Guardar Cambios", type="primary", use_container_width=True):
                        for _, r in edited_prods.iterrows():
                            val_cant = r.get("Cantidad", 0)
                            try: cant_f = float(val_cant) if pd.notna(val_cant) else 0.0
                            except: cant_f = 0.0
                            
                            datos_update = {
                                "fecha": str(n_fecha.isoformat()), "cliente": str(n_cli), "proveedor": str(n_prov),
                                "observaciones": str(n_obs), "codigo": str(r.get("Código", "")), "descripcion": str(r.get("Descripción", "")),
                                "color": str(r.get("Color", "")), "cantidad": cant_f, "usuario": str(n_entrega),
                                "oc": str(oc_seleccionada) # IMPORTANTE PARA VINCULAR FILAS NUEVAS
                            }
                            
                            # Si tiene ID, actualiza; Si NO tiene ID, inserta como fila nueva
                            if pd.notna(r.get("id")) and str(r.get("id")).strip() != "":
                                supabase.table("Recibos_OC").update(datos_update).eq("id", r["id"]).execute()
                            else:
                                if str(r.get("Código", "")).strip() != "": # Valida que la fila no esté vacía
                                    supabase.table("Recibos_OC").insert(datos_update).execute()
                                    
                        st.success("Guardado."); time.sleep(0.5); st.rerun()
                else:
                    col_g.warning("🔒 No tienes permiso para guardar cambios.")

                if n_cli in lista_nombres_cli and n_prov in lista_nombres_prov:
                    try:
                        cli_data = df_clientes[df_clientes['nombre'] == n_cli].iloc[0]
                        prov_data = df_proveedores[df_proveedores[col_p_name] == n_prov].iloc[0]
                        prov_text = _formatear_datos_contacto(n_prov, prov_data)
                        cli_text = _formatear_datos_contacto(n_cli, cli_data)
                        
                        datos_pdf = {"oc": oc_seleccionada, "fecha": n_fecha.strftime("%d/%m/%Y"), "observaciones": n_obs, "prov_texto": prov_text, "cli_texto": cli_text, "quien_entrega": n_entrega}
                        pdf_bytes = generar_pdf_entrega(datos_pdf, edited_prods, row_info['id'])
                        col_p.download_button("🖨️ PDF", pdf_bytes, f"Recibo_{oc_seleccionada}.pdf", "application/pdf", use_container_width=True)
                    except: col_p.error("Error PDF")
                
                st.divider()
                if tiene_permiso("Almacén: Editar/Eliminar Recibos OC"):
                    if st.button("🗑️ ELIMINAR ESTA ORDEN DE COMPRA", type="secondary", use_container_width=True):
                        supabase.table("Recibos_OC").delete().eq("oc", oc_seleccionada).execute()
                        st.warning("Orden eliminada. Actualizando..."); time.sleep(1); st.rerun()

        try:
            res_h = supabase.table("Recibos_OC").select("*").order("id", desc=True).limit(500).execute()
            df_hist = pd.DataFrame(res_h.data)
            
            if not df_hist.empty:
                df_resumen = df_hist.drop_duplicates(subset=['oc'])[['fecha', 'oc', 'cliente']].reset_index(drop=True)
                df_resumen.columns = ['Fecha', 'Orden de Compra', 'Cliente']
                
                c_h1, c_h2, c_h3, c_h4 = st.columns([2, 2, 3, 2])
                c_h1.markdown("**Fecha**")
                c_h2.markdown("**Orden de Compra**")
                c_h3.markdown("**Cliente**")
                c_h4.markdown("**Acción**")
                
                for idx, row in df_resumen.iterrows():
                    c1, c2, c3, c4 = st.columns([2, 2, 3, 2])
                    c1.write(row['Fecha'])
                    c2.write(row['Orden de Compra'])
                    c3.write(row['Cliente'])
                    if c4.button("Ver Detalle", key=f"btn_oc_{row['Orden de Compra']}"):
                        ver_editar_oc(row['Orden de Compra'], df_hist)
            
            else:
                st.info("No hay recibos registrados.")
        except Exception as e: 
            st.error(f"Error cargando historial: {e}")

# ==================================================
# 📥 OPCIÓN 4: ENTRADA DE MATERIAL
# ==================================================
elif opcion_almacen == "Entrada de Material":
    st.markdown("### 📥 Registro de Entrada de Material")
    try:
        res_prov = supabase.table("Proveedores").select("*").execute(); df_provs = pd.DataFrame(res_prov.data)
        col_p_name = 'empresa' if 'empresa' in df_provs.columns else 'nombre'
        lista_provs = df_provs[col_p_name].tolist() if not df_provs.empty else []
        df_pers = pd.DataFrame(supabase.table("Personal").select("nombre").eq("activo", True).execute().data)
        lista_pers = df_pers['nombre'].tolist() if not df_pers.empty else []
    except: lista_provs = []; lista_pers = []; df_provs = pd.DataFrame()

    tab_ent_new, tab_ent_hist = st.tabs(["➕ Nueva Entrada", "📜 Historial"])
    
    with tab_ent_new:
        if tiene_permiso("Almacén: Registrar Entrada Material"):
            with st.container(border=True):
                oc_in = st.text_input("Orden de Compra / Remisión")
                fecha_in = st.date_input("Fecha de Llegada", value=datetime.now().date())
                prov_in = st.selectbox("Proveedor (Origen):", lista_provs, index=None)
                
                if "data_entrada" not in st.session_state: st.session_state["data_entrada"] = pd.DataFrame([{"Código": "", "Descripción": "", "Color": "", "Cantidad": 0}], columns=["Código", "Descripción", "Color", "Cantidad"])
                edited_df_in = st.data_editor(st.session_state["data_entrada"], num_rows="dynamic", use_container_width=True)
                observaciones_in = st.text_area("Observaciones:", key="obs_in")
                quien_entrega_in = st.selectbox("Quien entrega:", lista_pers, key="user_in")
                
                if st.button("💾 Registrar Entrada", type="primary"):
                    if oc_in and prov_in and not edited_df_in.empty:
                        items_in = edited_df_in[edited_df_in["Código"].notna() & (edited_df_in["Código"] != "")]
                        for _, row in items_in.iterrows():
                            val_cant_in = row.get("Cantidad", 0)
                            try: cant_f_in = float(val_cant_in) if val_cant_in is not None else 0.0
                            except: cant_f_in = 0.0

                            data_in = {
                                "fecha": str(fecha_in.isoformat()), "oc": str(oc_in), "proveedor": str(prov_in), 
                                "codigo": str(row["Código"]), "descripcion": str(row["Descripción"]), 
                                "color": str(row["Color"]), "cantidad": cant_f_in, 
                                "usuario": str(quien_entrega_in), "observaciones": str(observaciones_in)
                            }
                            supabase.table("Entradas_Material").insert(data_in).execute()
                        
                        st.success("✅ Registrado."); st.rerun()
        else:
            st.warning("🔒 No tienes permiso para registrar nuevas entradas de material.")

    with tab_ent_hist:
        @st.dialog("Detalles de Entrada de Material", width="large")
        def ver_editar_entrada(oc_seleccionada, df_source):
            df_oc = df_source[df_source['oc'] == oc_seleccionada].copy()
            if not df_oc.empty:
                row_info = df_oc.iloc[0]
                
                st.markdown(f"#### 📥 Gestionar Entrada O.C. / Remisión {oc_seleccionada}")
                
                try: fecha_dt = pd.to_datetime(row_info['fecha']).date()
                except: fecha_dt = datetime.now().date()
                
                idx_prov = lista_provs.index(row_info['proveedor']) if row_info['proveedor'] in lista_provs else None
                idx_usr = lista_pers.index(row_info.get('usuario', '')) if row_info.get('usuario', '') in lista_pers else None

                c1, c2, c3 = st.columns(3)
                n_fecha = c1.date_input("Fecha", value=fecha_dt, key="e_fecha")
                n_prov = c2.selectbox("Proveedor", lista_provs, index=idx_prov, key="e_prov")
                n_entrega = c3.selectbox("Quien entrega", lista_pers, index=idx_usr, key="e_usr")
                
                n_obs = st.text_area("Observaciones", value=row_info.get('observaciones', ''), key="e_obs")
                
                st.divider()
                st.write("**Productos:**")
                df_edit_prod = df_oc[['id', 'codigo', 'descripcion', 'color', 'cantidad']].copy()
                df_edit_prod.rename(columns={'codigo':'Código', 'descripcion':'Descripción', 'color':'Color', 'cantidad':'Cantidad'}, inplace=True)
                
                # ✨ MEJORA: AÑADIDO NUM_ROWS="DYNAMIC" PARA PODER AGREGAR FILAS ✨
                edited_prods = st.data_editor(df_edit_prod, use_container_width=True, hide_index=True, disabled=['id'], num_rows="dynamic", key="e_editor")
                
                col_g, col_p = st.columns(2)
                
                if tiene_permiso("Almacén: Editar/Eliminar Entrada Material"):
                    if col_g.button("💾 Guardar Cambios", type="primary", use_container_width=True):
                        for _, r in edited_prods.iterrows():
                            val_cant = r.get("Cantidad", 0)
                            try: cant_f = float(val_cant) if pd.notna(val_cant) else 0.0
                            except: cant_f = 0.0
                            
                            datos_update = {
                                "fecha": str(n_fecha.isoformat()), "proveedor": str(n_prov),
                                "observaciones": str(n_obs), "usuario": str(n_entrega),
                                "codigo": str(r.get("Código", "")), "descripcion": str(r.get("Descripción", "")),
                                "color": str(r.get("Color", "")), "cantidad": cant_f,
                                "oc": str(oc_seleccionada) # IMPORTANTE PARA VINCULAR FILAS NUEVAS
                            }
                            
                            # Si tiene ID, actualiza; Si NO tiene ID, inserta como fila nueva
                            if pd.notna(r.get("id")) and str(r.get("id")).strip() != "":
                                supabase.table("Entradas_Material").update(datos_update).eq("id", r["id"]).execute()
                            else:
                                if str(r.get("Código", "")).strip() != "":
                                    supabase.table("Entradas_Material").insert(datos_update).execute()
                                    
                        st.success("Guardado."); time.sleep(0.5); st.rerun()
                else:
                    col_g.warning("🔒 No tienes permiso para editar.")

                if n_prov in lista_provs:
                    try:
                        prov_data = df_provs[df_provs[col_p_name] == n_prov].iloc[0]
                        prov_text = _formatear_datos_contacto(n_prov, prov_data)
                        hemore_text = "HEMORE INDUSTRIAS\nAlmacén Central" 
                        
                        datos_pdf = {"oc": oc_seleccionada, "fecha": n_fecha.strftime("%d/%m/%Y"), "observaciones": n_obs, "prov_texto": prov_text, "hemore_texto": hemore_text, "quien_entrega": n_entrega}
                        pdf_bytes = generar_pdf_entrada(datos_pdf, edited_prods, row_info['id'])
                        col_p.download_button("🖨️ Reimprimir PDF", pdf_bytes, f"Entrada_{oc_seleccionada}.pdf", "application/pdf", use_container_width=True)
                    except: col_p.error("Error PDF")
                
                st.divider()
                if tiene_permiso("Almacén: Editar/Eliminar Entrada Material"):
                    if st.button("🗑️ ELIMINAR ESTA ENTRADA", type="secondary", use_container_width=True):
                        supabase.table("Entradas_Material").delete().eq("oc", oc_seleccionada).execute()
                        st.warning("Entrada eliminada. Actualizando..."); time.sleep(1); st.rerun()

        try:
            res_h = supabase.table("Entradas_Material").select("*").order("id", desc=True).limit(500).execute()
            df_hist_ent = pd.DataFrame(res_h.data)
            
            if not df_hist_ent.empty:
                df_resumen_ent = df_hist_ent.drop_duplicates(subset=['oc'])[['fecha', 'oc', 'proveedor']].reset_index(drop=True)
                df_resumen_ent.columns = ['Fecha', 'OC / Remisión', 'Proveedor']
                
                c_h1, c_h2, c_h3, c_h4 = st.columns([2, 2, 3, 2])
                c_h1.markdown("**Fecha**")
                c_h2.markdown("**OC / Remisión**")
                c_h3.markdown("**Proveedor**")
                c_h4.markdown("**Acción**")
                
                for idx, row in df_resumen_ent.iterrows():
                    c1, c2, c3, c4 = st.columns([2, 2, 3, 2])
                    c1.write(row['Fecha'])
                    c2.write(row['OC / Remisión'])
                    c3.write(row['Proveedor'])
                    if c4.button("Ver Detalle", key=f"btn_ent_{row['OC / Remisión']}"):
                        ver_editar_entrada(row['OC / Remisión'], df_hist_ent)
            
            else:
                st.info("No hay entradas registradas.")
        except Exception as e: 
            st.error(f"Error cargando historial: {e}")

# ==================================================
# 💰 OPCIÓN 5: ENTRADAS Y SALIDAS DE DINERO
# ==================================================
elif opcion_almacen == "Entradas y Salidas de Dinero":
    st.markdown("### 💰 Entradas y Salidas de Dinero")
    
    tab_dinero_new, tab_dinero_hist = st.tabs(["➕ Nuevo Movimiento", "📜 Historial"])
    
    with tab_dinero_new:
        if tiene_permiso("Finanzas: Registrar Movimientos Dinero"):
            with st.container(border=True):
                tipo_mov = st.radio("Tipo de Movimiento:", ["Entrada", "Salida"], horizontal=True)
                fecha_mov = st.date_input("Fecha", value=datetime.now().date())
                
                c1, c2 = st.columns(2)
                quien_entrega = c1.text_input("Nombre de quien entrega:")
                quien_recibe = c2.text_input("Nombre de quien recibe:")
                
                monto_mov = st.number_input("Cantidad ($):", min_value=0.00, value=0.00, step=100.0)
                detalle_mov = st.text_area("Detalle / Descripción del movimiento:")
                
                if st.button("💾 Guardar y Generar Ticket", type="primary"):
                    errores_dinero = []
                    if not quien_entrega: errores_dinero.append("- Falta la persona que entrega.")
                    if not quien_recibe: errores_dinero.append("- Falta la persona que recibe.")
                    if monto_mov <= 0: errores_dinero.append("- La cantidad debe ser mayor a cero.")
                    if not detalle_mov: errores_dinero.append("- Escribe el detalle del movimiento.")

                    if errores_dinero:
                        st.error("⚠️ **Faltan datos:**\n\n" + "\n".join(errores_dinero))
                    else:
                        data_insert = {
                            "fecha": str(fecha_mov.isoformat()),
                            "tipo": str(tipo_mov),
                            "quien_entrega": str(quien_entrega),
                            "quien_recibe": str(quien_recibe),
                            "monto": float(monto_mov),
                            "descripcion": str(detalle_mov)
                        }
                        
                        supabase.table("Entradas_Salidas_Dinero").insert(data_insert).execute()
                        
                        try: last_id = supabase.table("Entradas_Salidas_Dinero").select("id").order("id", desc=True).limit(1).execute().data[0]['id']
                        except: last_id = 1
                        
                        pdf_bytes_ticket = generar_pdf_ticket_dinero(data_insert, last_id)
                        st.success("✅ Movimiento guardado correctamente.")
                        st.download_button("🖨️ Imprimir Ticket PDF", pdf_bytes_ticket, f"Ticket_{tipo_mov}_{last_id}.pdf", "application/pdf")
        else:
            st.warning("🔒 No tienes permiso para registrar movimientos de dinero.")

    with tab_dinero_hist:
        @st.dialog("Detalle del Movimiento de Dinero")
        def ver_editar_movimiento(id_mov, df_source):
            row_info = df_source[df_source['id'] == id_mov].iloc[0]
            st.markdown(f"#### 📄 Folio de Movimiento: {id_mov}")
            
            try: fecha_dt = pd.to_datetime(row_info['fecha']).date()
            except: fecha_dt = datetime.now().date()
            
            n_tipo = st.radio("Tipo:", ["Entrada", "Salida"], index=0 if row_info['tipo'] == "Entrada" else 1, horizontal=True)
            n_fecha = st.date_input("Fecha", value=fecha_dt, key="d_f")
            
            c1, c2 = st.columns(2)
            n_entrega = c1.text_input("Quien entrega:", value=row_info.get('quien_entrega', ''), key="d_ent")
            n_recibe = c2.text_input("Quien recibe:", value=row_info.get('quien_recibe', ''), key="d_rec")
            
            n_monto = st.number_input("Cantidad ($):", value=float(row_info.get('monto', 0)), step=100.0, key="d_mon")
            n_detalle = st.text_area("Detalle:", value=row_info.get('descripcion', ''), key="d_desc")
            
            st.divider()
            col_g, col_p = st.columns(2)
            
            if tiene_permiso("Finanzas: Editar/Eliminar Movimientos Dinero"):
                if col_g.button("💾 Guardar Cambios", type="primary", use_container_width=True):
                    supabase.table("Entradas_Salidas_Dinero").update({
                        "fecha": str(n_fecha.isoformat()), "tipo": str(n_tipo),
                        "quien_entrega": str(n_entrega), "quien_recibe": str(n_recibe),
                        "monto": float(n_monto), "descripcion": str(n_detalle)
                    }).eq("id", id_mov).execute()
                    st.success("Guardado."); time.sleep(0.5); st.rerun()
            else:
                col_g.warning("🔒 No tienes permiso para editar.")
                
            datos_act = {
                "fecha": n_fecha.strftime("%d/%m/%Y"), "tipo": n_tipo,
                "quien_entrega": n_entrega, "quien_recibe": n_recibe,
                "monto": n_monto, "descripcion": n_detalle
            }
            try:
                pdf_bytes_upd = generar_pdf_ticket_dinero(datos_act, id_mov)
                col_p.download_button("🖨️ Reimprimir Ticket", pdf_bytes_upd, f"Ticket_{n_tipo}_{id_mov}.pdf", "application/pdf", use_container_width=True)
            except Exception as e:
                col_p.error("Error PDF")
            
            if tiene_permiso("Finanzas: Editar/Eliminar Movimientos Dinero"):
                st.divider()
                if st.button("🗑️ ELIMINAR ESTE MOVIMIENTO", type="secondary", use_container_width=True):
                    supabase.table("Entradas_Salidas_Dinero").delete().eq("id", id_mov).execute()
                    st.warning("Movimiento eliminado."); time.sleep(1); st.rerun()

        try:
            res_h = supabase.table("Entradas_Salidas_Dinero").select("*").order("id", desc=True).limit(200).execute()
            df_hist_dinero = pd.DataFrame(res_h.data)
            
            if not df_hist_dinero.empty:
                c_h1, c_h2, c_h3, c_h4, c_h5 = st.columns([2, 1, 2, 2, 2])
                c_h1.markdown("**Fecha**")
                c_h2.markdown("**Folio**")
                c_h3.markdown("**Tipo**")
                c_h4.markdown("**Monto**")
                c_h5.markdown("**Acción**")
                
                for idx, row in df_hist_dinero.iterrows():
                    c1, c2, c3, c4, c5 = st.columns([2, 1, 2, 2, 2])
                    c1.write(row.get('fecha', ''))
                    c2.write(str(row.get('id', '')))
                    color = "🟢" if row.get('tipo', '') == "Entrada" else "🔴"
                    c3.write(f"{color} {row.get('tipo', '')}")
                    c4.write(f"$ {float(row.get('monto', 0)):,.2f}")
                    if c5.button("Ver Detalle", key=f"btn_mov_{row['id']}"):
                        ver_editar_movimiento(row['id'], df_hist_dinero)
            else:
                st.info("No hay movimientos registrados.")
        except Exception as e: 
            st.error(f"Error cargando historial: Asegúrate de crear la tabla 'Entradas_Salidas_Dinero' en Supabase.")
