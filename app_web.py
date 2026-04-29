import streamlit as st
import pandas as pd
from datetime import datetime

# Configuración de la página
st.set_page_config(page_title="IPAM - Gestor de IPs", layout="wide")

# CSS personalizado para tus StatCards de colores
st.markdown("""
    <style>
    .stat-card {
        padding: 20px;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 10px;
    }
    .total-card { background-color: #0066CC; }
    .usada-card { background-color: #DC3545; }
    .libre-card { background-color: #28A745; }
    
    .stat-label { font-size: 16px; font-weight: bold; opacity: 0.9; }
    .stat-value { font-size: 32px; font-weight: bold; margin-top: 5px; }
    </style>
    """, unsafe_allow_html=True)

archivo = "Inventario_servidores_vlans_IPs.xlsx"

# -------------------------------
# LÓGICA DE DATOS
# -------------------------------
def cargar_datos():
    try:
        vlan_df = pd.read_excel(archivo, sheet_name="VLANs")
        servers_df = pd.read_excel(archivo, sheet_name="Servidores")
        ips_df = pd.read_excel(archivo, sheet_name="IPs_VLAN")
        
        for df in [vlan_df, servers_df, ips_df]:
            df.columns = df.columns.str.strip()

        ips_df['VLAN'] = pd.to_numeric(ips_df['VLAN'], errors='coerce').fillna(0).astype(int)
        servers_df['VLAN'] = pd.to_numeric(servers_df['VLAN'], errors='coerce').fillna(0).astype(int)

        data = ips_df.merge(
            servers_df[["IP", "VLAN", "Host", "Ambiente", "Cluster", "Observaciones", "Descripcion"]], 
            on=["IP", "VLAN"], how="left", suffixes=("_ip", "_srv")
        )
        
        if "Descripcion_srv" in data.columns:
            data["Descripcion"] = data["Descripcion_srv"].fillna(data.get("Descripcion_ip", ""))
        
        if 'Estado' in data.columns:
            data['Estado'] = data['Estado'].astype(str).str.strip().str.upper()
        
        return vlan_df, servers_df, ips_df, data
    except Exception as e:
        st.error(f"Error al cargar el Excel: {e}")
        return None, None, None, None

def guardar_excel(vlan_df, servers_df, ips_df):
    with pd.ExcelWriter(archivo, engine="openpyxl", mode="w") as writer:
        vlan_df.to_excel(writer, sheet_name="VLANs", index=False)
        servers_df.to_excel(writer, sheet_name="Servidores", index=False)
        ips_df.to_excel(writer, sheet_name="IPs_VLAN", index=False)

vlan_df, servers_df, ips_df, data = cargar_datos()

# -------------------------------
# INTERFAZ WEB
# -------------------------------
st.title("≡ Gestor de IPs - IPAM")

tab1, tab2, tab3, tab4 = st.tabs(["📋 Consulta VLAN", "🔍 Buscar", "📝 Agregar", "🔓 Liberar"])

# --- TAB 1: CONSULTA POR VLAN CON CARDS DE COLORES ---
with tab1:
    st.subheader("Consulta por VLAN")
    if data is not None:
        vlan_list = sorted(data["VLAN"].unique())
        vlan_sel = st.selectbox("Seleccionar VLAN:", vlan_list, key="vlan_sel_fix")
        
        df_vlan = data[data["VLAN"] == vlan_sel].copy()
        
        # Conteo blindado
        estados_clean = df_vlan['Estado'].astype(str).str.upper().str.strip()
        total = len(df_vlan)
        u = (estados_clean == 'USADA').sum()
        l = (estados_clean == 'LIBRE').sum()
        
        # --- DISEÑO DE TARJETAS DE COLORES ---
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown(f"""<div class="stat-card total-card"><div class="stat-label">Total IPs</div><div class="stat-value">{total}</div></div>""", unsafe_allow_html=True)
        with col2:
            st.markdown(f"""<div class="stat-card usada-card"><div class="stat-label">Usadas</div><div class="stat-value">{u}</div></div>""", unsafe_allow_html=True)
        with col3:
            st.markdown(f"""<div class="stat-card libre-card"><div class="stat-label">Libres</div><div class="stat-value">{l}</div></div>""", unsafe_allow_html=True)
        
        if total > 0:
            cols_mostrar = ["IP", "Estado", "Host", "Cluster", "Descripcion"]
            existentes = [c for c in cols_mostrar if c in df_vlan.columns]
            
            def color_estado(val):
                if val == "LIBRE": return "color: #28A745; font-weight: bold;"
                if val == "USADA": return "color: #DC3545; font-weight: bold;"
                return ""

            st.dataframe(
                df_vlan[existentes].style.map(color_estado, subset=["Estado"]),
                use_container_width=True, hide_index=True
            )

# El resto de las pestañas (Buscar, Agregar, Liberar) se mantienen igual...
with tab2:
    st.subheader("Buscar Host / IP")
    c1, c2 = st.columns([1, 2])
    tipo = c1.selectbox("Buscar por:", ["IP o Host", "IP", "Host"])
    query = c2.text_input("Texto a buscar:")
    if query:
        res = data[data["IP"].astype(str).str.contains(query, case=False) | data["Host"].astype(str).str.contains(query, case=False, na=False)]
        st.dataframe(res, use_container_width=True, hide_index=True)

# Resto de la lógica simplificada para el ejemplo
# ... (Se mantienen las Tabs 3 y 4 del código anterior)