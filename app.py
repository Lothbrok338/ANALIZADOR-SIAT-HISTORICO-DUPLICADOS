import streamlit as st
import pandas as pd
from urllib.parse import urlparse, parse_qs
from io import BytesIO, StringIO
import os
import re

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Gestión Contable | UNIVALLE", page_icon="🎓", layout="wide")

# --- NOMBRES DE BASES DE DATOS LOCALES ---
FILE_SIAT = "DB_SIAT_MAESTRO.csv"
FILE_HISTORICO = "DB_HISTORICO_FACTURAS.csv"

# --- FUNCIONES DE BASE DE DATOS LOCAL ---
def cargar_historico():
    if os.path.exists(FILE_HISTORICO):
        return pd.read_csv(FILE_HISTORICO)
    return pd.DataFrame(columns=["Fecha", "Razón Social", "NIT", "Nro Factura", "Monto (Bs)", "CUF / Autorización"])

def cargar_siat_maestro():
    if os.path.exists(FILE_SIAT):
        return pd.read_csv(FILE_SIAT)
    return None

def guardar_historico(df_nuevo):
    df_actual = cargar_historico()
    df_actual = pd.concat([df_actual, df_nuevo], ignore_index=True)
    df_actual.to_csv(FILE_HISTORICO, index=False)

def guardar_siat_maestro(df_nuevo):
    df_actual = cargar_siat_maestro()
    if df_actual is not None:
        # Unir y eliminar duplicados por si suben la misma base varias veces
        df_combinado = pd.concat([df_actual, df_nuevo], ignore_index=True)
        df_combinado = df_combinado.drop_duplicates(subset=['CODIGO DE AUTORIZACION'], keep='last')
        df_combinado.to_csv(FILE_SIAT, index=False)
    else:
        df_nuevo.to_csv(FILE_SIAT, index=False)

# --- ESTILOS CSS PROFESIONALES ---
st.markdown("""
<style>
    .stApp { background-color: #fdf5e6; }
    [data-testid="stSidebar"] { background-color: #741b28 !important; border-right: 2px solid #b8860b; }
    [data-testid="stSidebar"] div, [data-testid="stSidebar"] span, 
    [data-testid="stSidebar"] label, [data-testid="stSidebar"] p { color: #ffffff !important; font-weight: 500 !important; }
    [data-testid="stFileUploader"] section { background-color: #1a1a1a !important; border: 1px dashed #b8860b !important; border-radius: 8px !important; }
    [data-testid="stFileUploaderFileName"], [data-testid="stFileUploaderFileData"], 
    [data-testid="stFileUploader"] small { color: #b8860b !important; opacity: 1 !important; }
    [data-testid="stFileUploader"] button { background-color: #741b28 !important; color: white !important; border: 1px solid #b8860b !important; }
    .stButton > button { border-radius: 4px; font-weight: 600; text-transform: uppercase; }
    div.stButton > button:first-child:not([kind="primary"]) { background-color: #741b28 !important; color: #ffffff !important; border: 1px solid #b8860b !important; }
    .stButton > button[kind="primary"] { background-color: #741b28 !important; color: #ffffff !important; border: 1px solid #b8860b !important; height: 3em; }
    h1, h2, h3 { color: #741b28; font-family: 'Times New Roman', serif; }
    .factura-card { background-color: #ffffff; padding: 15px; border-left: 5px solid #741b28; border-radius: 4px; margin-bottom: 12px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    .cuf-text { color: #b8860b; font-family: monospace; font-weight: bold; }
    .alerta-duplicado { color: #d32f2f; font-weight: bold; background-color: #ffebee; padding: 10px; border-radius: 5px; margin-bottom: 10px; border-left: 4px solid #d32f2f;}
</style>
""", unsafe_allow_html=True)

# --- LÓGICA DE SESIÓN ---
if 'registros_sesion' not in st.session_state:
    st.session_state.registros_sesion = []

# --- PANEL LATERAL ---
with st.sidebar:
    logo_path = "UNIVALLE LOGO.webp"
    if os.path.exists(logo_path):
        st.image(logo_path, use_container_width=True)
    else:
        st.markdown("<h2 style='color:white; text-align:center;'>UNIVALLE</h2>", unsafe_allow_html=True)
    
    st.markdown("<h4 style='text-align: center;'>INSTRUMENTO DE CONTROL CONTABLE</h4>", unsafe_allow_html=True)
    st.divider()
    
    archivo_csv = st.file_uploader("Vincular Base SIAT Diaria (.csv)", type=['csv'], help="Sube la base del día. Se acumulará al histórico automáticamente.")
    
    if archivo_csv:
        try:
            content = archivo_csv.read()
            try:
                decoded_content = content.decode('utf-8')
            except UnicodeDecodeError:
                decoded_content = content.decode('latin1')
            
            df_diario = pd.read_csv(StringIO(decoded_content), sep=',', on_bad_lines='skip')
            df_diario.columns = [c.strip() for c in df_diario.columns]
            
            # Limpieza y mapeo (Versión compatible con Pandas modernos)
            df_diario = df_diario.map(lambda x: x.strip() if isinstance(x, str) else x)
            
            # Guardar en la base maestra
            guardar_siat_maestro(df_diario)
            st.success("✅ Base diaria añadida al maestro con éxito")
        except Exception as e:
            st.error(f"Error en la lectura: {e}")
    
    st.divider()
    
    # --- ESTADÍSTICAS DEL SISTEMA ---
    df_historico_actual = cargar_historico()
    df_siat_actual = cargar_siat_maestro()
    
    st.write("📊 **Estadísticas del Sistema:**")
    st.write(f"- Facturas en SIAT (Maestro): {len(df_siat_actual) if df_siat_actual is not None else 0}")
    st.write(f"- Facturas Procesadas (Histórico): {len(df_historico_actual)}")
    
    st.divider()
    if st.button("🔄 Limpiar Pantalla", use_container_width=True, help="Limpia la vista actual, pero NO borra el historial guardado."):
        st.session_state.registros_sesion = []
        st.rerun()

# --- INTERFAZ PRINCIPAL ---
st.title("UNIVERSIDAD DEL VALLE S.A.")
st.subheader("Módulo Centralizado de Procesamiento de Datos Fiscales")
st.divider()

base_siat = cargar_siat_maestro()

if base_siat is not None:
    st.markdown("### 📥 Consolidación de Registros")
    urls_raw = st.text_area("Depósito de URLs para procesamiento masivo:", height=150, placeholder="Pegue los enlaces aquí...")
    
    if st.button("🚀 EJECUTAR PROCESAMIENTO DE DATOS", type="primary", use_container_width=True):
        links = re.findall(r'https?://[^\s]+?(?=https?://|$)', urls_raw)
        
        # Cargar historial justo en este momento para validación
        historico_db = cargar_historico()
        cufs_historicos = historico_db['CUF / Autorización'].tolist()
        
        agregados = 0
        duplicados = 0
        nuevos_registros_df = []
        
        for link in links:
            try:
                link_clean = link.strip().rstrip(',').rstrip(';')
                params = parse_qs(urlparse(link_clean).query)
                cuf_extraido = params.get('cuf', [''])[0].strip()
                
                if not cuf_extraido:
                    continue

                # 1. VALIDACIÓN ANTI-DUPLICADOS
                if cuf_extraido in cufs_historicos or any(d['CUF / Autorización'] == cuf_extraido for d in st.session_state.registros_sesion):
                    duplicados += 1
                    continue

                # 2. BÚSQUEDA EN SIAT
                match = base_siat[base_siat['CODIGO DE AUTORIZACION'] == cuf_extraido]
                
                if not match.empty:
                    item = match.iloc[0]
                    
                    # Corrección robusta de caracteres (ej. "Ã")
                    rs_raw = str(item['RAZON SOCIAL PROVEEDOR'])
                    try:
                        razon_social = rs_raw.encode('latin1').decode('utf-8') if "Ã" in rs_raw else rs_raw
                    except:
                        razon_social = rs_raw
                    
                    nuevo_registro = {
                        "Fecha": item['FECHA DE FACTURA/DUI/DIM'],
                        "Razón Social": razon_social,
                        "NIT": item['NIT PROVEEDOR'],
                        "Nro Factura": item['NUMERO FACTURA'],
                        "Monto (Bs)": item['IMPORTE TOTAL COMPRA'],
                        "CUF / Autorización": cuf_extraido
                    }
                    
                    st.session_state.registros_sesion.append(nuevo_registro)
                    nuevos_registros_df.append(nuevo_registro)
                    agregados += 1
            except:
                continue
        
        # 3. GUARDADO DE NUEVOS REGISTROS
        if nuevos_registros_df:
            guardar_historico(pd.DataFrame(nuevos_registros_df))
            st.success(f"Operación exitosa: {agregados} registros nuevos validados y guardados en la base de datos.")
        
        # 4. ADVERTENCIA DE DUPLICADOS
        if duplicados > 0:
            st.markdown(f"<div class='alerta-duplicado'>⚠️ ALERTA DE SISTEMA: Se bloquearon {duplicados} facturas repetidas (Ya se encontraban procesadas en el historial).</div>", unsafe_allow_html=True)

# --- REPORTES Y EXPORTACIÓN ---
if st.session_state.registros_sesion:
    st.divider()
    st.write("### 📊 Registros Procesados en esta sesión")
    
    for i, reg in enumerate(st.session_state.registros_sesion):
        st.markdown(f"""
        <div class='factura-card'>
            <span style='color: #741b28; font-weight: bold; font-size: 1.1em;'>{reg['Razón Social']}</span><br>
            <small>Factura: {reg['Nro Factura']} | Monto: {reg['Monto (Bs)']} Bs.</small><br>
            <span class='cuf-text'>CUF: {reg['CUF / Autorización']}</span>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("#### 📥 Descargar Historial Completo del Mes")
    df_historico_completo = cargar_historico()
    st.dataframe(df_historico_completo, use_container_width=True)
    
    buff = BytesIO()
    with pd.ExcelWriter(buff, engine='openpyxl') as w:
        df_historico_completo.to_excel(w, index=False)
    
    st.download_button(
        label="DESCARGAR INFORME TÉCNICO COMPLETO (EXCEL)",
        data=buff.getvalue(),
        file_name="Procesamiento_Datos_Mensual_UNIVALLE.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True
    )
else:
    if base_siat is None:
        st.info("📌 Sistema operativo. Por favor, vincule la base de datos diaria en el panel izquierdo para iniciar.")
    else:
        st.info("📌 Base de datos operativa. Deposite los enlaces para iniciar el procesamiento.")

st.markdown("<br><p style='text-align: center; color: #741b28; opacity: 0.6;'>DEPARTAMENTO DE CONTABILIDAD | UNIVALLE S.A. © 2026</p>", unsafe_allow_html=True)
