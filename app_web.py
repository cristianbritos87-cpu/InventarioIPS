import streamlit as st
import pandas as pd

# CONFIGURACIÓN
# Reemplazá este ID por el de tu Google Sheet
SHEET_ID = "11aAvK0LcZo-6jL3UcUPoao5AFSuQ2NANHpHqcAhwz-w"
PASS_SISTEMA = "inventarioipot" # Cambiá esto por la clave que quieras

st.set_page_config(page_title="IPAM - Gestor de IPs", layout="wide")

# --- CONTROL DE ACCESO ---
def check_password():
    if "password_correct" not in st.session_state:
        st.title("Acceso al IPAM")
        pass_input = st.text_input("Ingresá la contraseña", type="password")
        if st.button("Entrar"):
            if pass_input == PASS_SISTEMA:
                st.session_state["password_correct"] = True
                st.rerun()
            else:
                st.error("Contraseña incorrecta")
        return False
    return True

if not check_password():
    st.stop()

# --- ESTILOS ---
st.markdown("""
    <style>
    .stat-card { padding: 20px; border-radius: 10px; color: white; text-align: center; margin-bottom: 15px; }
    .total-card { background-color: #0066CC; }
    .usada-card { background-color: #DC3545; }
    .libre-card { background-color: #28A745; }
    .stat-label { font-size: 18px; font-weight: bold; opacity: 0.9; }
    .stat-value { font-size: 36px; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- FUNCIONES DE DATOS (GOOGLE SHEETS) ---
def get_sheet_url(sheet_name):
    return f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={sheet_name}"

def cargar_datos():
    try:
        vlan_df = pd.read_csv(get_sheet_url("VLANs"))
        servers_df = pd.read_csv(get_sheet_url("Servidores"))
        ips_df = pd.read_csv(get_sheet_url("IPs_VLAN"))
        
        for df in [vlan_df, servers_df, ips_df]:
            df.columns = df.columns.str.strip()
            
        data = ips_df.merge(
            servers_df[["IP", "VLAN", "Host", "Ambiente", "Cluster", "Descripcion"]], 
            on=["IP", "VLAN"], how="left"
        )
        data['Estado'] = data['Estado'].astype(str).str.strip().str.upper()
        return vlan_df, servers_df, ips_df, data
    except Exception as e:
        st.error(f"Error cargando datos desde Google Sheets: {e}")
        return None, None, None, None

vlan_df, servers_df, ips_df, data = cargar_datos()

# --- INTERFAZ ---
st.title("≡ Gestor de IPs - IPAM (Cloud)")

tab1, tab2, tab3 = st.tabs(["📋 Consulta VLAN", "🔍 Buscar", "📝 Gestionar"])

with tab1:
    if data is not None:
        vlan_sel = st.selectbox("VLAN:", sorted(data["VLAN"].unique()))
        df_vlan = data[data["VLAN"] == vlan_sel].copy()
        
        total = len(df_vlan)
        u = (df_vlan['Estado'] == 'USADA').sum()
        l = (df_vlan['Estado'] == 'LIBRE').sum()
        
        c1, c2, c3 = st.columns(3)
        c1.markdown(f'<div class="stat-card total-card"><div class="stat-label">Total</div><div class="stat-value">{total}</div></div>', unsafe_allow_html=True)
        c2.markdown(f'<div class="stat-card usada-card"><div class="stat-label">Usadas</div><div class="stat-value">{u}</div></div>', unsafe_allow_html=True)
        c3.markdown(f'<div class="stat-card libre-card"><div class="stat-label">Libres</div><div class="stat-value">{l}</div></div>', unsafe_allow_html=True)
        
        st.dataframe(df_vlan[["IP", "Estado", "Host", "Cluster", "Descripcion"]], use_container_width=True, hide_index=True, height=None)

with tab2:
    query = st.text_input("Buscar IP o Host:")
    if query:
        res = data[data["IP"].astype(str).str.contains(query, case=False) | data["Host"].astype(str).str.contains(query, case=False, na=False)]
        st.dataframe(res, use_container_width=True, hide_index=True)

with tab3:
    st.info("Para editar, agregar o liberar IPs, hacé los cambios directamente en el Google Sheet. La App se actualizará automáticamente al recargar.")
    st.link_button("Ir al Google Sheet ↗", f"https://docs.google.com/spreadsheets/d/{SHEET_ID}")