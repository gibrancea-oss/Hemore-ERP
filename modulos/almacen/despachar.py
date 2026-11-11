import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, timezone, date
import utils 

supabase = utils.supabase 
tz_cdmx = timezone(timedelta(hours=-6))

def renderizar():
    st.markdown("Pedidos realizados por los trabajadores que están esperando en ventanilla.")
    
    # 🌟 FRAGMENTO EN TIEMPO REAL 🌟
    @st.fragment(run_every="5s")
    def vista_pedidos_tiempo_real():
        try:
            res_pendientes = supabase.table("solicitudes_almacen").select("*").eq("estado", "Pendiente").execute()
            df_pendientes = pd.DataFrame(res_pendientes.data)
            
            if not df_pendientes.empty:
                st.warning(f"🚨 ¡ATENCIÓN! Tienes {len(df_pendientes)} pedido(s) pendiente(s) en ventanilla.", icon="🚨")
                
                # --- CALLBACKS DIRECTOS A BASE DE DATOS (Anti Doble Clic) ---
                def accion_despachar(id_pedido, tipo_item, cod_item, cant, usr_sol, nom_item):
                    if tipo_item == "Insumo":
                        item_ins = supabase.table("Insumos").select("id, cantidad").eq("codigo", cod_item).execute().data[0]
                        stock_real = float(item_ins.get('cantidad', 0))
                        if stock_real >= float(cant):
                            nuevo_stock = stock_real - float(cant)
                            supabase.table("Insumos").update({"cantidad": nuevo_stock}).eq("id", item_ins['id']).execute()
                            supabase.table("Historial_Insumos").insert({"fecha": datetime.now(tz_cdmx).strftime('%Y-%m-%d %H:%M:%S'), "codigo": cod_item, "descripcion": nom_item, "tipo_movimiento": "Salida (Despacho)", "cantidad": float(cant), "responsable": usr_sol}).execute()
                            supabase.table("solicitudes_almacen").update({"estado": "Despachado"}).eq("id", id_pedido).execute()
                            st.toast("✅ Despachado y descontado del stock.", icon="✅")
                        else:
                            st.toast(f"❌ Stock insuficiente. Quedan {stock_real} unidades.", icon="❌")
                    elif tipo_item == "Herramienta":
                        item_herr = supabase.table("Herramientas").select("id, Responsable").eq("codigo", cod_item).execute().data[0]
                        if item_herr.get("Responsable", "") == "Bodega":
                            supabase.table("Herramientas").update({"Responsable": usr_sol}).eq("id", item_herr['id']).execute()
                            supabase.table("Historial_Herramientas").insert({"Fecha_Hora": datetime.now(tz_cdmx).strftime('%Y-%m-%d %H:%M:%S'), "Herramienta": nom_item, "Movimiento": "Préstamo", "Responsable": usr_sol}).execute()
                            supabase.table("solicitudes_almacen").update({"estado": "Despachado"}).eq("id", id_pedido).execute()
                            st.toast("✅ Herramienta prestada.", icon="✅")
                        else:
                            st.toast(f"❌ La herramienta ya fue prestada a: {item_herr.get('Responsable', 'Otro usuario')}", icon="❌")

                def accion_rechazar(id_pedido):
                    supabase.table("solicitudes_almacen").update({"estado": "Rechazado"}).eq("id", id_pedido).execute()
                    st.toast("⚠️ Solicitud rechazada.", icon="❌")

                # --- RENDERIZADO DE LA LISTA ---
                for i, row in df_pendientes.iterrows():
                    with st.container(border=True):
                        c1, c2, c3 = st.columns([3, 1, 1])
                        c1.markdown(f"**{row['usuario_solicita']}** solicita:")
                        c1.markdown(f"### {row['cantidad']}x {row['nombre_item']} ({row['tipo_item']})")
                        c1.caption(f"📅 {row['fecha']} | Código: {row['codigo_item']}")
                        
                        # Los botones usan on_click para no recargar toda la página y evitar doble clic
                        c2.button("✅ Despachar", key=f"ok_{row['id']}", type="primary", use_container_width=True, on_click=accion_despachar, args=(row['id'], row['tipo_item'], row['codigo_item'], row['cantidad'], row['usuario_solicita'], row['nombre_item']))
                        c3.button("❌ Rechazar", key=f"no_{row['id']}", use_container_width=True, on_click=accion_rechazar, args=(row['id'],))
            else:
                st.success("🎉 No hay pedidos pendientes. Todo en orden.")
        except Exception as e:
            st.error(f"Asegúrate de haber creado la tabla 'solicitudes_almacen'. Detalles: {e}")
            
    # Ejecuta el fragmento
    vista_pedidos_tiempo_real()
