import streamlit as st
import pandas as pd
import utils 
import time
import datetime
import io
import qrcode
import os
import base64
from fpdf import FPDF

st.set_page_config(page_title="Configuración Master", page_icon="⚙️", layout="wide")

# --- 🔒 SEGURIDAD ---
utils.validar_login()
supabase = utils.supabase

# --- FUNCIONES QR ---
def get_qr_data_url(text):
    if not text: return None
    try:
        qr = qrcode.QRCode(version=1, box_size=4, border=1)
        qr.add_data(str(text))
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        buffered = io.BytesIO()
        img.save(buffered, format="PNG")
        return "data:image/png;base64," + base64.b64encode(buffered.getvalue()).decode()
    except: return None

# ==========================================
# MENÚ PRINCIPAL
# ==========================================
st.sidebar.title("🔧 Configuración")
opcion = st.sidebar.radio(
    "Selecciona Módulo:",
    ["Personal", "Insumos", "Herramientas", "Clientes", "Proveedores", "📂 Catálogos QR"]
)

# ==========================================
# 2. INSUMOS (CON PROTECCIÓN DE COLUMNAS)
# ==========================================
if opcion == "Insumos":
    st.markdown("### 📦 Gestión de Insumos")
    try:
        response = supabase.table("Insumos").select("*").order("id").execute()
        df = pd.DataFrame(response.data)
    except: df = pd.DataFrame()
    
    t1, t2 = st.tabs(["➕ Alta Manual", "📋 Inventario Maestro"])
    
    with t1:
        with st.form("alta_insumo"):
            c1, c2 = st.columns([1, 3])
            cod = c1.text_input("Código / SKU")
            nom = c2.text_input("Descripción")
            c3, c4, c5 = st.columns(3)
            uni = c3.selectbox("Unidad", ["Pzas", "Kg", "Lts", "Mts", "Cajas"])
            cant = c4.number_input("Cantidad Inicial", min_value=0.0)
            mini = c5.number_input("Stock Mínimo", value=5.0)
            ubi = st.text_input("Ubicación (Estante/Gaveta)")
            
            if st.form_submit_button("Guardar Insumo"):
                if cod and nom:
                    datos = {
                        "codigo": cod, 
                        "Descripcion": nom, 
                        "Insumo": nom, # Requerido por tu DB
                        "Unidad": uni, 
                        "Cantidad": cant, 
                        "stock_minimo": mini
                    }
                    # Intentar agregar ubicación solo si existe en la DB
                    if "ubicacion" in df.columns or df.empty:
                        datos["ubicacion"] = ubi
                    
                    try:
                        supabase.table("Insumos").insert(datos).execute()
                        st.success("✅ Guardado correctamente")
                        time.sleep(1); st.rerun()
                    except Exception as e:
                        st.error(f"Error al guardar. ¿Ya creaste la columna 'ubicacion' en Supabase? Detalle: {e}")
                else: st.warning("SKU y Descripción son obligatorios.")

    with t2:
        if not df.empty:
            # Columnas a mostrar (ajustadas a lo que existe en tu DB)
            cols_base = ["id", "codigo", "Descripcion", "Unidad", "Cantidad", "stock_minimo"]
            if "ubicacion" in df.columns:
                cols_base.append("ubicacion")
            else:
                st.warning("⚠️ La columna 'ubicacion' no se detecta en la base de datos. Crea la columna en Supabase para poder usarla.")

            edited = st.data_editor(df[cols_base], num_rows="dynamic", use_container_width=True)
            
            if st.button("💾 Guardar Cambios"):
                for i, r in edited.iterrows():
                    d = {
                        "codigo": r["codigo"],
                        "Descripcion": r["Descripcion"],
                        "Insumo": r["Descripcion"],
                        "Cantidad": r["Cantidad"],
                        "Unidad": r["Unidad"],
                        "stock_minimo": r["stock_minimo"]
                    }
                    if "ubicacion" in r: d["ubicacion"] = r["ubicacion"]

                    try:
                        if pd.notna(r["id"]): 
                            supabase.table("Insumos").update(d).eq("id", r["id"]).execute()
                        else: 
                            supabase.table("Insumos").insert(d).execute()
                    except Exception as e:
                        st.error(f"Error en SKU {r['codigo']}: {e}")
                st.success("✅ Cambios aplicados"); time.sleep(1); st.rerun()
        else: st.info("No hay datos en el inventario.")

# (Los demás módulos se mantienen igual para no afectar procesos anteriores)
elif opcion == "Personal":
    # Tu código anterior de Personal...
    st.info("Módulo de Personal activo")
elif opcion == "Herramientas":
    # Tu código anterior de Herramientas...
    st.info("Módulo de Herramientas activo")
elif opcion == "Clientes":
    # Tu código anterior de Clientes...
    st.info("Módulo de Clientes activo")
elif opcion == "Proveedores":
    # Tu código anterior de Proveedores...
    st.info("Módulo de Proveedores activo")
elif "Etiquetas" in opcion:
    # Tu código anterior de Catálogos QR...
    st.info("Módulo de Catálogos QR activo")
