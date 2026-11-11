import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, timezone, date
import utils 

supabase = utils.supabase 
tz_cdmx = timezone(timedelta(hours=-6))

def renderizar(tiene_permiso):
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
                with st.container(border=True):
                    st.info("📤 Prestar Herramienta")
                    if not df_her.empty:
                        bodega = df_her[df_her["Responsable"] == "Bodega"]
                        if not bodega.empty:
                            sel = st.selectbox("Selecciona Herramienta", bodega["Herramienta"].tolist(), key="prest_herr")
                            resp = st.selectbox("Prestar a:", lista_personal, key="prest_resp")
                            if st.button("Confirmar Préstamo", type="primary"):
                                id_h = int(bodega[bodega["Herramienta"]==sel].iloc[0]["id"])
                                res_check = supabase.table("Herramientas").select("Responsable").eq("id", id_h).execute()
                                if res_check.data and res_check.data[0].get("Responsable", "") == "Bodega":
                                    supabase.table("Herramientas").update({"Responsable": str(resp)}).eq("id", id_h).execute()
                                    try: supabase.table("Historial_Herramientas").insert({"Fecha_Hora": datetime.now(tz_cdmx).strftime('%Y-%m-%d %H:%M:%S'), "Herramienta": str(sel), "Movimiento": "Préstamo", "Responsable": str(resp)}).execute()
                                    except: pass
                                    st.toast("✅ Prestado exitosamente", icon="📤"); st.rerun()
                                else:
                                    st.error("Esta herramienta ya fue prestada.")
                        else:
                            st.warning("No hay herramientas disponibles en BODEGA.")
            with c2:
                with st.container(border=True):
                    st.warning("📥 Devolver Herramienta")
                    if not df_her.empty:
                        prestadas = df_her[df_her["Responsable"] != "Bodega"]
                        if not prestadas.empty:
                            sel_d = st.selectbox("Selecciona Herramienta a devolver", prestadas["Herramienta"].tolist(), key="dev_herr")
                            if st.button("Confirmar Devolución", type="primary"):
                                id_h = int(prestadas[prestadas["Herramienta"]==sel_d].iloc[0]["id"])
                                res_check = supabase.table("Herramientas").select("Responsable").eq("id", id_h).execute()
                                if res_check.data and res_check.data[0].get("Responsable", "") != "Bodega":
                                    supabase.table("Herramientas").update({"Responsable": "Bodega"}).eq("id", id_h).execute()
                                    try: supabase.table("Historial_Herramientas").insert({"Fecha_Hora": datetime.now(tz_cdmx).strftime('%Y-%m-%d %H:%M:%S'), "Herramienta": str(sel_d), "Movimiento": "Devolución", "Responsable": "Bodega"}).execute()
                                    except: pass
                                    st.toast("✅ Devuelto exitosamente a Bodega", icon="📥"); st.rerun()
                                else:
                                    st.error("Esta herramienta ya fue devuelta.")
                        else:
                            st.info("Todas las herramientas están actualmente en bodega.")
        else:
            st.warning("🔒 No tienes permiso para prestar ni devolver herramientas.")

    with tab2:
        if not df_her.empty:
            df_view = df_her.copy()
            df_view.loc[df_view['Responsable'] != 'Bodega', 'ubicacion'] = "En uso - " + df_view['Responsable']
            cols_mostrar = ["codigo", "Herramienta", "Estado", "Responsable", "ubicacion"]
            for col in cols_mostrar:
                if col not in df_view.columns: df_view[col] = ""
            df_display = df_view[cols_mostrar].rename(columns={"codigo": "Código / ID", "ubicacion": "Ubicación"})
            st.dataframe(df_display, use_container_width=True, hide_index=True)
        else:
            st.info("No hay inventario registrado.")

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
                def eliminar_reg_herr(id_borrar):
                    supabase.table("Historial_Herramientas").delete().eq("id", int(id_borrar)).execute()
                    st.toast("Registro eliminado.", icon="🗑️")
                st.button("🗑️ ELIMINAR ESTE REGISTRO", type="secondary", use_container_width=True, on_click=eliminar_reg_herr, args=(mov_id,))
            else:
                st.warning("🔒 No tienes permiso para eliminar registros.")

        try:
            res_h = supabase.table("Historial_Herramientas").select("*").order("id", desc=True).limit(200).execute()
            df_hist_herr = pd.DataFrame(res_h.data)
            if not df_hist_herr.empty:
                c_h1, c_h2, c_h3, c_h4, c_h5 = st.columns([2, 3, 2, 2, 2])
                c_h1.markdown("**Fecha**"); c_h2.markdown("**Herramienta**"); c_h3.markdown("**Movimiento**"); c_h4.markdown("**Responsable**"); c_h5.markdown("**Acción**")
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
