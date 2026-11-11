import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, timezone, date
import utils 

supabase = utils.supabase 
tz_cdmx = timezone(timedelta(hours=-6))

def renderizar():
    st.markdown("Busca lo que necesitas y envía la solicitud a almacén para que te lo preparen.")
    usuario_actual = st.session_state.get("usuario_actual", "Usuario No Identificado") 

    tab_pedir_insumo, tab_pedir_herr = st.tabs(["📦 Pedir Insumos", "🛠️ Pedir Herramientas"])

    with tab_pedir_insumo:
        if st.session_state.get("pedido_ins_exito", False):
            st.success("✅ Pedido enviado correctamente a ventanilla.")
            if st.button("🔄 Hacer otro pedido de Insumo"):
                st.session_state["pedido_ins_exito"] = False
                st.rerun()
        else:
            try:
                df_ins = pd.DataFrame(supabase.table("Insumos").select("*").execute().data)
                if not df_ins.empty:
                    df_ins.columns = df_ins.columns.str.lower()
                    lista_busqueda = [f"{row.get('codigo', 'S/C')} | {row.get('descripcion', 'Sin nombre')} (Stock: {row.get('cantidad', 0)})" for i, row in df_ins.iterrows()]
                    seleccion_ins = st.selectbox("🔍 Buscar Insumo:", lista_busqueda, index=None, placeholder="Escribe para buscar...")
                    
                    if seleccion_ins:
                        codigo_sel = seleccion_ins.split(" | ")[0]
                        item_actual = df_ins[df_ins["codigo"] == codigo_sel].iloc[0]
                        st.info(f"📍 **Ubicación en almacén:** {item_actual.get('ubicacion', 'S/U')}")
                        st.metric("Stock Disponible", item_actual.get('cantidad', 0))
                        
                        cant_pedir = st.number_input("Cantidad a solicitar:", min_value=1.0, max_value=float(item_actual.get('cantidad', 1)), value=1.0)
                        
                        if st.button("🚀 Enviar Pedido a Almacén", type="primary"):
                            datos_solicitud = {"fecha": datetime.now(tz_cdmx).strftime('%Y-%m-%d %H:%M:%S'), "usuario_solicita": str(usuario_actual), "tipo_item": "Insumo", "codigo_item": str(item_actual.get('codigo', '')), "nombre_item": str(item_actual.get('descripcion', '')), "cantidad": float(cant_pedir), "estado": "Pendiente"}
                            supabase.table("solicitudes_almacen").insert(datos_solicitud).execute()
                            st.session_state["pedido_ins_exito"] = True
                            st.toast("✅ Pedido enviado.", icon="🚀"); st.rerun()
                else:
                    st.warning("No hay insumos registrados en la base de datos.")
            except Exception as e:
                st.error(f"Error cargando insumos: {e}")

    with tab_pedir_herr:
        if st.session_state.get("pedido_herr_exito", False):
            st.success("✅ Solicitud enviada correctamente a ventanilla.")
            if st.button("🔄 Hacer otro pedido de Herramienta"):
                st.session_state["pedido_herr_exito"] = False
                st.rerun()
        else:
            try:
                df_her = pd.DataFrame(supabase.table("Herramientas").select("*").execute().data)
                if not df_her.empty:
                    bodega = df_her[df_her.get("Responsable", df_her.get("responsable")) == "Bodega"]
                    if not bodega.empty:
                        lista_herr = [f"{row.get('codigo', 'S/C')} | {row.get('Herramienta', row.get('herramienta', 'Sin nombre'))}" for i, row in bodega.iterrows()]
                        seleccion_herr = st.selectbox("🔍 Buscar Herramienta Disponible:", lista_herr, index=None, placeholder="Escribe para buscar...")
                        
                        if seleccion_herr:
                            cod_herr = seleccion_herr.split(" | ")[0]
                            herr_actual = bodega[bodega["codigo"] == cod_herr].iloc[0]
                            
                            st.info("🟢 Disponible para préstamo inmediato.")
                            if st.button("🚀 Solicitar Préstamo", type="primary"):
                                datos_solicitud = {"fecha": datetime.now(tz_cdmx).strftime('%Y-%m-%d %H:%M:%S'), "usuario_solicita": str(usuario_actual), "tipo_item": "Herramienta", "codigo_item": str(herr_actual.get('codigo', '')), "nombre_item": str(herr_actual.get('Herramienta', herr_actual.get('herramienta', ''))), "cantidad": 1.0, "estado": "Pendiente"}
                                supabase.table("solicitudes_almacen").insert(datos_solicitud).execute()
                                st.session_state["pedido_herr_exito"] = True
                                st.toast("✅ Préstamo solicitado.", icon="🚀"); st.rerun()
                    else:
                        st.warning("No hay herramientas en bodega en este momento.")
            except Exception as e:
                st.error(f"Error cargando herramientas: {e}")
