import streamlit as st
import extra_streamlit_components as stx
import utils
import os
import uuid
import datetime

# ==========================================
# 1. CONFIGURACIÓN INICIAL · HEMORE EXECUTIVE UI
#    Rediseño visual: la lógica operativa se conserva.
# ==========================================
st.set_page_config(page_title="Inicio | ERP Hemore", page_icon="", layout="wide")
utils.aplicar_estilo_movil()

# Sistema visual: acabado editorial corporativo, superficies precisas,
# jerarquía tipográfica y controles nativos de Streamlit estilizados.
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@400;500;600;700;800&display=swap');

    :root {
        --hm-ink: #142038;
        --hm-navy: #0B1830;
        --hm-royal: #2D62D9;
        --hm-muted: #758198;
        --hm-line: #E4EAF2;
        --hm-surface: #FFFFFF;
        --hm-bg: #F4F7FB;
        --hm-success: #12A67B;
        --hm-danger: #CE4252;
        --hm-shadow: 0 25px 75px rgba(18, 36, 70, .08);
    }

    html, body, .stApp, [data-testid="stAppViewContainer"] {
        font-family: 'DM Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        color: var(--hm-ink);
        background: var(--hm-bg);
    }
    [data-testid="stAppViewContainer"] {
        background-image:
            radial-gradient(ellipse 48% 38% at 96% 4%, rgba(214,225,247,.43), transparent 76%),
            radial-gradient(ellipse 37% 37% at 0% 94%, rgba(229,236,248,.47), transparent 77%);
    }
    #MainMenu, footer, [data-testid="stToolbar"] {visibility: hidden;}
    header[data-testid="stHeader"] {background: transparent !important;}
    [data-testid="stDecoration"] {display: none;}
    [data-testid="stMainBlockContainer"], .block-container {
        max-width: 1310px;
        padding-top: 3.3rem;
        padding-bottom: 4rem;
    }
    h1, h2, h3, h4, h5 {
        font-family: 'Manrope', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        letter-spacing: -.045em;
        color: var(--hm-ink);
    }
    h1 {font-weight: 800 !important;}
    h3 {font-weight: 750 !important;}
    p {line-height: 1.65;}
    hr {
        margin: 1.8rem 0 !important;
        border: none !important;
        border-top: 1px solid var(--hm-line) !important;
    }

    /* ===================================================
       ACCESO: marco de dos cuerpos. La tarjeta incluye
       widgets Streamlit reales (no superposiciones HTML).
       =================================================== */
    [data-testid="stHorizontalBlock"]:has(.hm-brand-surface) {
        max-width: 1130px;
        margin: 2.25rem auto 0;
        gap: 0 !important;
        overflow: hidden;
        border: 1px solid rgba(226,234,245,.95);
        border-radius: 30px;
        background: #FFFFFF;
        box-shadow: 0 35px 100px rgba(17,35,65,.11), 0 4px 16px rgba(17,35,65,.025);
        align-items: stretch;
    }
    [data-testid="stHorizontalBlock"]:has(.hm-brand-surface) > [data-testid="column"] {
        min-height: 598px;
    }
    [data-testid="column"]:has(.hm-brand-surface) {
        position: relative;
        isolation: isolate;
        overflow: hidden;
        background:
            radial-gradient(circle at 93% 12%, rgba(101,148,237,.19), transparent 28%),
            radial-gradient(circle at 6% 98%, rgba(45,98,217,.20), transparent 41%),
            linear-gradient(143deg, #0B1933 3%, #10264B 65%, #0A1932 100%);
        padding: 49px 48px 42px;
    }
    [data-testid="column"]:has(.hm-brand-surface)::before {
        content: '';
        position: absolute;
        z-index: -1;
        width: 480px;
        height: 480px;
        right: -290px;
        top: 160px;
        border-radius: 50%;
        border: 1px solid rgba(197,214,246,.16);
        box-shadow:
            0 0 0 62px rgba(197,214,246,.035),
            0 0 0 123px rgba(197,214,246,.025),
            0 0 0 185px rgba(197,214,246,.014);
        pointer-events: none;
    }
    [data-testid="column"]:has(.hm-brand-surface)::after {
        content: '';
        position: absolute;
        inset: 0;
        z-index: -1;
        background-image: linear-gradient(rgba(255,255,255,.025) 1px, transparent 1px),
                          linear-gradient(90deg, rgba(255,255,255,.025) 1px, transparent 1px);
        background-size: 38px 38px;
        mask-image: linear-gradient(120deg, transparent 3%, #000 100%);
        pointer-events: none;
    }
    .hm-brand-surface {
        display: flex;
        align-items: center;
        gap: 12px;
        margin-bottom: 116px;
    }
    .hm-brand-mark {
        display: inline-flex;
        justify-content: center;
        align-items: center;
        width: 39px;
        height: 39px;
        border: 1px solid rgba(255,255,255,.25);
        border-radius: 12px;
        background: linear-gradient(135deg, rgba(255,255,255,.18), rgba(255,255,255,.04));
        color: #fff;
        font-family: 'Manrope', sans-serif;
        font-weight: 800;
        font-size: 19px;
        letter-spacing: -.07em;
        box-shadow: inset 0 1px 0 rgba(255,255,255,.15);
    }
    .hm-brand-id {
        color: rgba(245,249,255,.96);
        font-size: 11px;
        font-weight: 800;
        letter-spacing: .16em;
        line-height: 1.5;
    }
    .hm-brand-edition {
        color: rgba(201,218,246,.59);
        font-size: 9px;
        letter-spacing: .16em;
        margin-top: 1px;
    }
    .hm-brand-name {
        margin: 0 0 10px !important;
        color: #FFFFFF !important;
        font-family: 'Manrope', sans-serif;
        font-size: clamp(43px, 4vw, 62px) !important;
        font-weight: 800;
        letter-spacing: -.065em !important;
        line-height: 1.1;
    }
    .hm-brand-subtitle {
        margin: 0;
        color: #B4C6E0;
        font-size: 17px;
        font-weight: 400;
        letter-spacing: -.015em;
    }
    .hm-brand-footer {
        margin-top: 115px;
        padding-top: 24px;
        border-top: 1px solid rgba(226,238,255,.17);
        display: flex;
        align-items: center;
        gap: 10px;
        font-size: 10px;
        font-weight: 700;
        letter-spacing: .16em;
        color: #AFC5E2;
    }
    .hm-brand-footer-dot {
        width: 7px;
        height: 7px;
        flex: 0 0 7px;
        background: #75D5BC;
        border-radius: 50%;
        box-shadow: 0 0 0 4px rgba(117,213,188,.1);
    }
    [data-testid="column"]:has(.hm-brand-surface) [data-testid="stImage"] {
        max-width: 300px;
    }
    [data-testid="column"]:has(.hm-brand-surface) [data-testid="stImage"] img {
        max-height: 158px;
        object-fit: contain;
        object-position: left center;
    }

    [data-testid="column"]:has(.hm-login-heading) {
        background: #FFFFFF;
        padding: 87px clamp(30px, 4vw, 67px) 52px;
    }
    .hm-login-heading {margin-bottom: 29px;}
    .hm-kicker {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        border: 1px solid #E5ECF7;
        background: #F4F7FD;
        border-radius: 7px;
        padding: 7px 10px;
        color: #3662B0;
        font-size: 10px;
        font-weight: 800;
        letter-spacing: .12em;
        text-transform: uppercase;
    }
    .hm-kicker::before {
        content: '';
        width: 5px;
        height: 5px;
        border-radius: 50%;
        background: #4174DC;
    }
    .hm-login-heading h2 {
        font-family: 'Manrope', sans-serif;
        margin: 21px 0 8px;
        color: #142038;
        font-size: clamp(29px, 3vw, 38px);
        line-height: 1.16;
        font-weight: 800;
        letter-spacing: -.055em;
    }
    .hm-login-heading p {
        color: #7D889A;
        font-size: 13.5px;
        margin: 0;
        line-height: 1.7;
    }
    .hm-login-footnote {
        margin-top: 24px;
        padding-top: 18px;
        border-top: 1px solid #EEF2F7;
        color: #A1ADBD;
        font-size: 10px;
        font-weight: 700;
        letter-spacing: .12em;
        text-align: center;
    }

    /* ===================================================
       CONTROLES: estados, espaciado y accesibilidad
       =================================================== */
    [data-testid="stTextInput"] {margin-bottom: 3px;}
    [data-testid="stTextInput"] label p {
        color: #344258 !important;
        font-size: 12px !important;
        font-weight: 700 !important;
        letter-spacing: .005em;
    }
    [data-testid="stTextInput"] [data-baseweb="input"] {
        background: #FAFBFD;
        border: 1px solid #DCE4EE;
        border-radius: 11px;
        box-shadow: 0 1px 2px rgba(23,43,77,.02);
        transition: border-color .2s ease, background .2s ease, box-shadow .2s ease;
    }
    [data-testid="stTextInput"] [data-baseweb="input"]:focus-within {
        border-color: #4174DF !important;
        background: #FFF;
        box-shadow: 0 0 0 4px rgba(65,116,223,.11);
    }
    [data-testid="stTextInput"] input {
        min-height: 48px;
        background: transparent !important;
        color: #1A2942 !important;
        font-family: 'DM Sans', sans-serif;
        font-size: 13.5px !important;
        padding: 0 14px !important;
    }
    [data-testid="stTextInput"] input::placeholder {color: #A8B3C2 !important;}
    [data-testid="stButton"] > button {
        min-height: 49px;
        background: #2D62D9;
        color: #FFFFFF;
        border: 1px solid #2D62D9;
        border-radius: 11px;
        font-family: 'DM Sans', sans-serif;
        font-size: 13px;
        font-weight: 700;
        letter-spacing: .008em;
        box-shadow: 0 6px 18px rgba(42,95,207,.16);
        transition: background .2s ease, border-color .2s ease, box-shadow .2s ease, transform .2s ease;
    }
    [data-testid="stButton"] > button:hover {
        background: #2455C7;
        color: #FFFFFF;
        border-color: #2455C7;
        box-shadow: 0 10px 25px rgba(42,95,207,.23);
        transform: translateY(-1px);
    }
    [data-testid="stButton"] > button:active {transform: translateY(0);}
    [data-testid="stButton"] > button:focus-visible {
        outline: 3px solid rgba(45,98,217,.25);
        outline-offset: 3px;
    }
    [data-testid="stAlert"] {border-radius: 11px;}

    /* ===================================================
       EQUIPO NO AUTORIZADO: alerta y vinculación
       =================================================== */
    [data-testid="stHorizontalBlock"]:has(.hm-device-heading) {
        max-width: 1150px;
        margin: 4rem auto 0;
        align-items: stretch;
    }
    [data-testid="column"]:has(.hm-device-heading) {
        padding: clamp(26px, 3.5vw, 49px);
        background: #fff;
        border: 1px solid #E2E9F3;
        border-radius: 23px;
        box-shadow: var(--hm-shadow);
    }
    .hm-device-heading {margin-bottom: 30px;}
    .hm-device-heading .hm-device-icon {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 52px;
        height: 52px;
        margin-bottom: 19px;
        border: 1px solid #F7DADD;
        background: #FFF3F4;
        color: #C63B4B;
        border-radius: 15px;
        font-size: 22px;
    }
    .hm-device-heading h2 {
        color: #17243B;
        font-size: 26px;
        line-height: 1.25;
        margin: 0 0 12px;
        font-weight: 800;
    }
    .hm-device-heading p {
        color: #7D899B;
        font-size: 13px;
        line-height: 1.75;
        margin: 0;
    }
    [data-testid="stExpander"] {
        background: #FAFBFD;
        border: 1px solid #E2E8F1;
        border-radius: 12px;
        overflow: hidden;
    }
    [data-testid="stExpander"] summary {
        padding-top: 12px;
        padding-bottom: 12px;
        color: #273950;
        font-weight: 700;
        font-size: 13px;
    }

    /* ===================================================
       PANEL: cabecera ejecutiva, estado y accesos
       =================================================== */
    .hm-dashboard-kicker {
        margin: 2px 0 9px;
        font-size: 10px;
        font-weight: 800;
        text-transform: uppercase;
        letter-spacing: .18em;
        color: #5675AE;
    }
    [data-testid="stHorizontalBlock"]:has(.hm-dashboard-kicker) {
        align-items: center;
        padding-bottom: 12px;
    }
    [data-testid="stHorizontalBlock"]:has(.hm-dashboard-kicker) h1 {
        margin: 0 !important;
        font-size: clamp(33px, 3.5vw, 46px);
        line-height: 1.18;
    }
    [data-testid="stHorizontalBlock"]:has(.hm-dashboard-kicker) [data-testid="stButton"] button {
        background: #FFFFFF;
        color: #34435B;
        border: 1px solid #DDE5F0;
        box-shadow: 0 2px 9px rgba(26,44,74,.035);
    }
    [data-testid="stHorizontalBlock"]:has(.hm-dashboard-kicker) [data-testid="stButton"] button:hover {
        background: #F8FAFD;
        border-color: #B9C9DF;
        color: #142038;
    }
    .hm-dashboard-description {
        margin: 6px 0 0;
        font-size: 13.5px;
        color: #7E8CA1;
        line-height: 1.6;
    }
    .hm-session-card {
        position: relative;
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 18px;
        padding: 24px 28px;
        margin: 5px 0 24px;
        border: 1px solid #E3E9F2;
        border-radius: 17px;
        background: #fff;
        box-shadow: 0 8px 30px rgba(25,45,77,.035);
    }
    .hm-session-card::before {
        position: absolute;
        content: '';
        top: 22px;
        bottom: 22px;
        left: 0;
        width: 3px;
        background: #3E71DF;
        border-radius: 0 3px 3px 0;
    }
    .hm-session-card--limited::before {background: #22B78B;}
    .hm-session-label {
        display: flex;
        align-items: center;
        gap: 9px;
        margin-bottom: 7px;
        color: #7C899D;
        text-transform: uppercase;
        font-size: 10px;
        font-weight: 800;
        letter-spacing: .13em;
    }
    .apple-dot {
        width: 7px;
        height: 7px;
        display: inline-block;
        border-radius: 50%;
        background: #23BD8B;
        box-shadow: 0 0 0 4px rgba(35,189,139,.12);
    }
    .hm-session-user {
        color: #19273E;
        font-family: 'Manrope', sans-serif;
        font-size: 18px;
        font-weight: 800;
        letter-spacing: -.025em;
        overflow-wrap: anywhere;
    }
    .hm-access-badge {
        flex-shrink: 0;
        padding: 9px 13px;
        border-radius: 8px;
        background: #EFF4FF;
        color: #315DC4;
        font-size: 11px;
        font-weight: 800;
        letter-spacing: .006em;
        border: 1px solid #DFE9FD;
    }
    .hm-access-badge--limited {
        background: #F0F4F7;
        color: #44546A;
        border-color: #E3E9F0;
    }
    [data-testid="stHorizontalBlock"]:has(.hm-feature-card) {margin-top: 10px;}
    [data-testid="stHorizontalBlock"]:has(.hm-feature-card) h3,
    [data-testid="stHorizontalBlock"]:has(.hm-access-level) h3 {
        margin-bottom: 8px;
        font-size: 17px;
        letter-spacing: -.03em;
    }
    .hm-section-description {
        color: #7D899B;
        font-size: 12.5px;
        margin: 0 0 18px;
    }
    .hm-feature-card {
        display: flex;
        align-items: flex-start;
        gap: 15px;
        padding: 21px;
        margin-bottom: 13px;
        background: #FFFFFF;
        border: 1px solid #E1E8F1;
        border-radius: 15px;
        box-shadow: 0 5px 20px rgba(27,47,76,.025);
        transition: transform .2s ease, box-shadow .2s ease, border-color .2s ease;
    }
    .hm-feature-card:hover {
        transform: translateY(-2px);
        border-color: #C4D2E6;
        box-shadow: 0 12px 24px rgba(27,47,76,.055);
    }
    .hm-feature-icon {
        flex: 0 0 42px;
        width: 42px;
        height: 42px;
        display: flex;
        align-items: center;
        justify-content: center;
        border: 1px solid #E4EBF9;
        border-radius: 11px;
        background: #F3F7FF;
        font-size: 20px;
    }
    .hm-feature-icon--neutral {
        border-color: #E7E9F0;
        background: #F5F6F9;
    }
    .hm-feature-title {
        margin: 1px 0 5px;
        font-family: 'Manrope', sans-serif;
        font-size: 13.5px;
        color: #23314B;
        font-weight: 800;
    }
    .hm-feature-description {
        font-size: 12px;
        line-height: 1.65;
        margin: 0;
        color: #7A8799;
    }
    .hm-access-level {
        padding: 24px;
        border: 1px solid #DCEAE6;
        background: #fff;
        border-radius: 15px;
        box-shadow: 0 5px 20px rgba(27,47,76,.025);
    }
    .hm-access-level--empty {
        border-color: #F1DADD;
    }
    .hm-access-level-title {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        color: #148D6F;
        font-size: 12.5px;
        font-weight: 800;
        margin-bottom: 8px;
    }
    .hm-access-level-title--empty {color: #C44757;}
    .hm-access-level p {
        color: #7C899B;
        font-size: 12px;
        margin: 0;
        line-height: 1.75;
    }
    .hm-permission {
        display: inline-block;
        padding: 7px 11px;
        margin: 4px 5px 4px 0;
        background: #F2F6FC;
        border: 1px solid #E0E9F4;
        border-radius: 8px;
        font-size: 11px;
        font-weight: 700;
        color: #32517A;
    }

    /* Menú lateral: conserva la navegación del ERP. */
    [data-testid="stSidebar"] {
        background: #101E36;
        border-right: 1px solid #1D2D4B;
    }
    [data-testid="stSidebar"] * {color: #D5E0F1;}
    [data-testid="stSidebar"] [data-testid="stSidebarNav"] a {
        border-radius: 9px;
        margin: 2px 8px;
        transition: background .2s ease;
    }
    [data-testid="stSidebar"] [data-testid="stSidebarNav"] a:hover {
        background: rgba(255,255,255,.075);
    }
    [data-testid="stSidebar"] [data-testid="stSidebarNav"] a[aria-current="page"] {
        background: rgba(72,119,213,.24);
        color: #fff;
    }

    /* Ajustes de tamaño para tablets y móviles. */
    @media (max-width: 1050px) {
        [data-testid="column"]:has(.hm-brand-surface) {padding: 40px 31px;}
        [data-testid="column"]:has(.hm-login-heading) {padding: 65px 30px 42px;}
        .hm-brand-surface {margin-bottom: 90px;}
        .hm-brand-footer {margin-top: 92px;}
    }
    @media (max-width: 767px) {
        [data-testid="stMainBlockContainer"], .block-container {
            padding-top: 1.1rem;
            padding-left: 1rem;
            padding-right: 1rem;
        }
        [data-testid="stHorizontalBlock"]:has(.hm-brand-surface) {
            margin-top: 1rem;
            border-radius: 22px;
            flex-direction: column !important;
        }
        [data-testid="stHorizontalBlock"]:has(.hm-brand-surface) > [data-testid="column"] {
            min-height: 0;
            width: 100% !important;
            flex: unset !important;
        }
        [data-testid="column"]:has(.hm-brand-surface) {padding: 26px 26px 30px;}
        .hm-brand-surface {margin-bottom: 33px;}
        .hm-brand-name {font-size: 40px !important;}
        .hm-brand-subtitle {font-size: 14px;}
        .hm-brand-footer {margin-top: 36px; padding-top: 17px;}
        [data-testid="column"]:has(.hm-login-heading) {padding: 32px 26px 36px;}
        .hm-login-heading h2 {font-size: 31px;}
        [data-testid="stHorizontalBlock"]:has(.hm-device-heading) {margin-top: 1.5rem;}
        [data-testid="column"]:has(.hm-device-heading) {padding: 25px;}
        .hm-session-card {flex-wrap: wrap; padding: 22px;}
        .hm-access-badge {max-width: 100%;}
    }
    @media (prefers-reduced-motion: reduce) {
        *, *::before, *::after {
            scroll-behavior: auto !important;
            transition-duration: .01ms !important;
            animation-duration: .01ms !important;
        }
    }
</style>
""", unsafe_allow_html=True)

if "bypass_device" not in st.session_state:
    st.session_state["bypass_device"] = False

# ==========================================
# 🛡️ BARRERA 1: DISPOSITIVO DE CONFIANZA
# ==========================================
cookie_manager = stx.CookieManager(key="cookie_manager_hemore")

device_token = cookie_manager.get(cookie="hemore_device_token")
dispositivo_valido = False

if device_token:
    try:
        res_device = utils.supabase.table("Dispositivos_Autorizados").select("*").eq("token", device_token).execute()
        if len(res_device.data) > 0:
            dispositivo_valido = True
    except Exception as e:
        pass

if st.session_state["bypass_device"]:
    dispositivo_valido = True

if not dispositivo_valido:
    col1, col2, col3 = st.columns([1, 1.8, 1])

    with col2:
        st.markdown("""
            <div class="hm-device-heading">
                <span class="hm-device-icon">🔒</span>
                <div class="hm-kicker" style="margin-bottom: 15px;">Autenticación</div>
                <h2>Terminal No Autorizada</h2>
                <p>Este equipo no está vinculado a la red central de la fábrica. Por protocolos de seguridad, el sistema permanece bloqueado para esta terminal.</p>
            </div>
        """, unsafe_allow_html=True)

        with st.expander("⚙️ Vincular este equipo (Solo Administrador)"):
            admin_pass_link = st.text_input("Contraseña Maestra", type="password", key="auth_pass")
            nombre_equipo = st.text_input("Nombre de este equipo (Ej. Computadora Almacén)", key="auth_name")

            st.write("<br>", unsafe_allow_html=True)
            if st.button("Vincular Equipo Físico", type="primary", use_container_width=True):
                if admin_pass_link == st.secrets["admin_password"]:
                    if nombre_equipo:
                        nuevo_token = str(uuid.uuid4())
                        try:
                            utils.supabase.table("Dispositivos_Autorizados").insert({"token": nuevo_token, "descripcion": nombre_equipo}).execute()
                            vencimiento = datetime.datetime.now() + datetime.timedelta(days=1825)
                            cookie_manager.set("hemore_device_token", nuevo_token, expires_at=vencimiento)
                            st.session_state["bypass_device"] = True
                            st.toast("✅ Equipo vinculado exitosamente", icon="✅")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error al conectar: {e}")
                    else:
                        st.warning("Escribe un nombre para identificar este equipo.")
                else:
                    st.error("Contraseña incorrecta.")
    st.stop()

# ==========================================
# 🛡️ BARRERA 2: SISTEMA DE LOGIN Y SESIONES
# ==========================================
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False
if "usuario_actual" not in st.session_state:
    st.session_state["usuario_actual"] = ""
if "es_admin" not in st.session_state:
    st.session_state["es_admin"] = False
if "permisos" not in st.session_state:
    st.session_state["permisos"] = []

if not st.session_state["authenticated"]:
    col_logo, col_login = st.columns([1.2, 1.5], gap="large")

    with col_logo:
        st.markdown("""
            <div class="hm-brand-surface">
                <span class="hm-brand-mark">H</span>
                <span>
                    <span class="hm-brand-id">INDUSTRIAS HEMORE</span>
                    <span class="hm-brand-edition" style="display: block;">ENTERPRISE SYSTEMS</span>
                </span>
            </div>
        """, unsafe_allow_html=True)
        if os.path.exists("logo.png"):
            st.image("logo.png", use_container_width=True)
        else:
            st.markdown("""
                <h1 class="hm-brand-name">HEMORE</h1>
                <p class="hm-brand-subtitle">Enterprise Resource Planning</p>
            """, unsafe_allow_html=True)
        st.markdown("""
            <div class="hm-brand-footer">
                <span class="hm-brand-footer-dot"></span>
                <span>SISTEMA CENTRALIZADO DE OPERACIONES</span>
            </div>
        """, unsafe_allow_html=True)

    with col_login:
        st.markdown("""
            <div class="hm-login-heading">
                <span class="hm-kicker">Autenticación</span>
                <h2>Iniciar Sesión</h2>
                <p>Introduce tus credenciales operativas autorizadas.</p>
            </div>
        """, unsafe_allow_html=True)

        usuario_input = st.text_input("Usuario", placeholder="ej. jPerez")
        password_input = st.text_input("Contraseña", type="password", placeholder="••••••••")

        st.write("<br>", unsafe_allow_html=True)

        if st.button("Ingresar al Sistema", type="primary", use_container_width=True):
            if not usuario_input or not password_input:
                st.warning("⚠️ Ingresa usuario y contraseña.")
            else:
                if usuario_input == st.secrets["admin_user"] and password_input == st.secrets["admin_password"]:
                    st.session_state["authenticated"] = True
                    st.session_state["usuario_actual"] = "Administrador Master"
                    st.session_state["es_admin"] = True
                    st.session_state["permisos"] = ["TODO"]
                    st.toast("✅ Acceso Concedido", icon="🔓")
                    st.rerun()
                else:
                    try:
                        res = utils.supabase.table("Personal").select("*").eq("usuario", usuario_input).eq("pin", password_input).eq("activo", True).execute()
                        if len(res.data) > 0:
                            usuario_db = res.data[0]
                            st.session_state["authenticated"] = True
                            st.session_state["usuario_actual"] = usuario_db["nombre"]
                            st.session_state["es_admin"] = False
                            permisos_str = usuario_db.get("permisos", "")
                            st.session_state["permisos"] = [p.strip() for p in permisos_str.split(",")] if permisos_str else []
                            st.toast(f"✅ Bienvenido {usuario_db['nombre']}", icon="🔓")
                            st.rerun()
                        else:
                            st.error("⛔ Usuario o contraseña incorrectos")
                    except Exception as e:
                        st.error(f"Error de conexión: {e}")

        st.markdown('<div class="hm-login-footnote">HEMORE · ENTERPRISE RESOURCE PLANNING</div>', unsafe_allow_html=True)

    st.stop()

# ==========================================
# 🏠 PANTALLA PRINCIPAL · EXECUTIVE DASHBOARD
# ==========================================
if os.path.exists("logo.png"):
    st.sidebar.image("logo.png", use_container_width=True)

col_t1, col_t2 = st.columns([8, 2])
with col_t1:
    st.markdown('<div class="hm-dashboard-kicker">INDUSTRIAS HEMORE / ERP</div>', unsafe_allow_html=True)
    st.title("Panel de Control")
    st.markdown("<p class='hm-dashboard-description'>Sistema Centralizado de Operaciones y Manufactura — Industrias Hemore</p>", unsafe_allow_html=True)

with col_t2:
    st.write("")

    def cerrar_sesion():
        st.session_state["authenticated"] = False
        st.session_state["usuario_actual"] = ""
        st.session_state["es_admin"] = False
        st.session_state["permisos"] = []

    st.button("🚪 Cerrar Sesión", use_container_width=True, on_click=cerrar_sesion)

st.write("<br>", unsafe_allow_html=True)

# Estado de sesión (la autorización y el usuario se toman de la misma sesión).
if st.session_state["es_admin"]:
    st.markdown(f"""
        <div class="hm-session-card hm-session-card--admin">
            <div>
                <div class="hm-session-label"><span class="apple-dot"></span>Sesión Activa</div>
                <strong class="hm-session-user">{st.session_state['usuario_actual']}</strong>
            </div>
            <span class="hm-access-badge">👑 Acceso Total Habilitado</span>
        </div>
    """, unsafe_allow_html=True)
else:
    st.markdown(f"""
        <div class="hm-session-card hm-session-card--limited">
            <div>
                <div class="hm-session-label"><span class="apple-dot"></span>Sesión Activa</div>
                <strong class="hm-session-user">{st.session_state['usuario_actual']}</strong>
            </div>
            <span class="hm-access-badge hm-access-badge--limited">🔒 Accesos Restringidos</span>
        </div>
    """, unsafe_allow_html=True)

st.divider()

col_info1, col_info2 = st.columns(2, gap="large")

with col_info1:
    st.markdown("### 🚀 Accesos Directos")
    st.markdown("<p class='hm-section-description'>Selecciona una opción en el menú lateral izquierdo:</p>", unsafe_allow_html=True)

    st.markdown("""
        <div class="hm-feature-card">
            <div class="hm-feature-icon">📦</div>
            <div>
                <div class="hm-feature-title">Almacén Central</div>
                <p class="hm-feature-description">Control de inventarios, entradas, salidas, recibos y préstamos.</p>
            </div>
        </div>
        <div class="hm-feature-card">
            <div class="hm-feature-icon hm-feature-icon--neutral">⚙️</div>
            <div>
                <div class="hm-feature-title">Configuración Master</div>
                <p class="hm-feature-description">Alta de productos, clientes, proveedores, personal y catálogos QR.</p>
            </div>
        </div>
    """, unsafe_allow_html=True)

with col_info2:
    if st.session_state["es_admin"]:
        st.markdown("### 🛡️ Nivel de Acceso")
        st.markdown("""
            <div class="hm-access-level">
                <div class="hm-access-level-title"><span class="apple-dot"></span>Administrador del Sistema</div>
                <p>Tienes control total y absoluto sobre los submódulos de Almacén y Configuración de Industrias Hemore.</p>
            </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("### 🛡️ Tus permisos habilitados:")
        if st.session_state["permisos"]:
            permisos_html = "".join([f"<span class='hm-permission'>✅ {p}</span>" for p in st.session_state["permisos"]])
            st.markdown(f"""
                <div class="hm-access-level">
                    {permisos_html}
                </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
                <div class="hm-access-level hm-access-level--empty">
                    <div class="hm-access-level-title hm-access-level-title--empty">Sin privilegios activos</div>
                    <p>No tienes permisos asignados actualmente en el sistema.</p>
                </div>
            """, unsafe_allow_html=True)
