import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, timezone, date
import utils 

supabase = utils.supabase 
tz_cdmx = timezone(timedelta(hours=-6))

def renderizar(tiene_permiso, generar_pdf_ticket_dinero):
    tab_dinero_new, tab_dinero_hist = st.tabs(["➕ Nuevo Movimiento", "📜 Historial"])
    
    with tab_dinero_new:
        if tiene_permiso("Finanzas: Registrar Movimientos Dinero"):
            with st.container(border=True):
                if "dinero_guardado" not in st.session_state:
                    st.session_state["dinero_guardado"] = False
                    st.session_state["dinero_pdf"] = None
                    st.session_state["dinero_filename"] = ""

                if not st.session_state["dinero_guardado"]:
                    tipo_mov = st.radio("Tipo de Movimiento:", ["Entrada", "Salida"], horizontal=True, key="new_din_tipo")
                    fecha_mov = st.date_input("Fecha", value=datetime.now(tz_cdmx).date(), key="new_din_fecha")
                    
                    c1, c2 = st.columns(2)
                    quien_entrega = c1.text_input("Nombre de quien entrega:", key="new_din_ent")
                    quien_recibe = c2.text_input("Nombre de quien recibe:", key="new_din_rec")
                    
                    monto_mov = st.number_input("Cantidad ($):", min_value=0.00, value=0.00, step=100.0, key="new_din_monto")
                    detalle_mov = st.text_area("Detalle / Descripción del movimiento:", key="new_din_det")
                    
                    if st.button("💾 Guardar y Generar Ticket", type="primary"):
                        errores_dinero = []
                        if not quien_entrega: errores_dinero.append("- Falta la persona que entrega.")
                        if not quien_recibe: errores_dinero.append("- Falta la persona que recibe.")
                        if monto_mov <= 0: errores_dinero.append("- La cantidad debe ser mayor a cero.")
                        if not detalle_mov: errores_dinero.append("- Escribe el detalle del movimiento.")

                        if errores_dinero:
                            st.error("⚠️ **Faltan datos:**\n\n" + "\n".join(errores_dinero))
                        else:
                            data_insert = {"fecha": str(fecha_mov.isoformat()), "tipo": str(tipo_mov), "quien_entrega": str(quien_entrega), "quien_recibe": str(quien_recibe), "monto": float(monto_mov), "descripcion": str(detalle_mov)}
                            supabase.table("Entradas_Salidas_Dinero").insert(data_insert).execute()
                            
                            try: last_id = supabase.table("Entradas_Salidas_Dinero").select("id").order("id", desc=True).limit(1).execute().data[0]['id']
                            except: last_id = 1
                            
                            pdf_bytes_ticket = generar_pdf_ticket_dinero(data_insert, last_id)
                            st.session_state["dinero_pdf"] = pdf_bytes_ticket
                            st.session_state["dinero_filename"] = f"Ticket_{tipo_mov}_{last_id}.pdf"
                            st.session_state["dinero_guardado"] = True
                            st.toast("✅ Movimiento guardado.", icon="💵")
                            st.rerun()
                else:
                    st.success("✅ Movimiento guardado correctamente.")
                    st.download_button("🖨️ Imprimir Ticket PDF", st.session_state["dinero_pdf"], st.session_state["dinero_filename"], "application/pdf")
                    if st.button("🔄 Registrar Nuevo Movimiento"):
                        st.session_state["dinero_guardado"] = False
                        for k in ["new_din_tipo", "new_din_fecha", "new_din_ent", "new_din_rec", "new_din_monto", "new_din_det"]: st.session_state.pop(k, None)
                        st.rerun()
        else:
            st.warning("🔒 No tienes permiso para registrar movimientos de dinero.")

    with tab_dinero_hist:
        @st.dialog("Detalle del Movimiento de Dinero")
        def ver_editar_movimiento(id_mov, df_source):
            row_info = df_source[df_source['id'] == id_mov].iloc[0]
            st.markdown(f"#### 📄 Folio de Movimiento: {id_mov}")
            
            try: fecha_dt = pd.to_datetime(row_info['fecha']).date()
            except: fecha_dt = datetime.now(tz_cdmx).date()
            
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
                    supabase.table("Entradas_Salidas_Dinero").update({"fecha": str(n_fecha.isoformat()), "tipo": str(n_tipo), "quien_entrega": str(n_entrega), "quien_recibe": str(n_recibe), "monto": float(n_monto), "descripcion": str(n_detalle)}).eq("id", id_mov).execute()
                    st.toast("✅ Guardado.", icon="💾"); st.rerun()
            else:
                col_g.warning("🔒 No tienes permiso.")
                
            datos_act = {"fecha": n_fecha.strftime("%d/%m/%Y"), "tipo": n_tipo, "quien_entrega": n_entrega, "quien_recibe": n_recibe, "monto": n_monto, "descripcion": n_detalle}
            try:
                pdf_bytes_upd = generar_pdf_ticket_dinero(datos_act, id_mov)
                col_p.download_button("🖨️ Reimprimir Ticket", pdf_bytes_upd, f"Ticket_{n_tipo}_{id_mov}.pdf", "application/pdf", use_container_width=True)
            except Exception as e: col_p.error("Error PDF")
            
            if tiene_permiso("Finanzas: Editar/Eliminar Movimientos Dinero"):
                st.divider()
                def del_dinero(id_borrar):
                    supabase.table("Entradas_Salidas_Dinero").delete().eq("id", id_borrar).execute()
                    st.toast("Movimiento eliminado.", icon="🗑️")
                st.button("🗑️ ELIMINAR ESTE MOVIMIENTO", type="secondary", use_container_width=True, on_click=del_dinero, args=(id_mov,))

        try:
            res_h = supabase.table("Entradas_Salidas_Dinero").select("*").order("id", desc=True).limit(200).execute()
            df_hist_dinero = pd.DataFrame(res_h.data)
            if not df_hist_dinero.empty:
                c_h1, c_h2, c_h3, c_h4, c_h5 = st.columns([2, 1, 2, 2, 2])
                c_h1.markdown("**Fecha**"); c_h2.markdown("**Folio**"); c_h3.markdown("**Tipo**"); c_h4.markdown("**Monto**"); c_h5.markdown("**Acción**")
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
            st.error("Error cargando historial de dinero.")
