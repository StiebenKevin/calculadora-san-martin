import streamlit as st
import pandas as pd
import plotly.express as px  # Librería para gráficos interactivos estilo Power BI
import io
from PIL import Image

# ==============================================================================
# 1. CONFIGURACIÓN DE LA PÁGINA E INTERFAZ
# ==============================================================================
st.set_page_config(page_title="Calculadora de Alícuotas - San Martín", page_icon="📊", layout="wide")

# Intentar cargar el logo municipal
try:
    image = Image.open('logo_san_martin.png')
    st.image(image, width=250)
except:
    st.subheader("Municipalidad de General San Martín")

st.title("📊 Calculadora de Alícuotas e Inteligencia Fiscal")
st.markdown("---")

NOMBRES_MESES = {
    1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril", 5: "Mayo", 6: "Junio",
    7: "Julio", 8: "Agosto", 9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"
}

# ==============================================================================
# 2. MOTOR FISCAL (LÓGICA NORMATIVA DE SAN MARTÍN)
# ==============================================================================
def obtener_valor_modulo_real(anio, mes):
    if anio == 2026: return 89.00
    elif anio == 2025:
        if 1 <= mes <= 6: return 64.00
        elif 7 <= mes <= 9: return 69.00
        elif mes == 10: return 71.00
        elif 11 <= mes <= 12: return 74.00
    elif anio == 2024:
        if 1 <= mes <= 3: return 26.00
        elif 4 <= mes <= 6: return 49.40
        elif 7 <= mes <= 8: return 52.00
        elif 9 <= mes <= 11: return 57.00
        elif mes == 12: return 58.00
    return 89.00

escalas_por_anio = {
    2026: {
        "Agropecuario": {"limite_5_a_7": 244789000, "limite_7_a_8": 368103000, "limite_8_to_12": 1187425000, "limite_12_to_15": 3492431000},
        "Industria y Minería": {"limite_5_a_7": 723725000, "limite_7_a_8": 1088308000, "limite_8_to_12": 3510670000, "limite_12_to_15": 10325497000},
        "Comercio": {"limite_5_a_7": 966148000, "limite_7_a_8": 1453321000, "limite_8_to_12": 4686623000, "limite_12_to_15": 13784189000},
        "Servicios": {"limite_5_a_7": 236512000, "limite_7_a_8": 355658000, "limite_8_to_12": 1147282000, "limite_12_to_15": 3374357000},
        "Construcción": {"limite_5_a_7": 289552000, "limite_7_a_8": 458798000, "limite_8_to_12": 1479990000, "limite_12_to_15": 4352914000}
    },
    2025: {
        "Agropecuario": {"limite_5_a_7": 188939000, "limite_7_a_8": 284118000, "limite_8_to_12": 916506000, "limite_12_to_15": 2695609000},
        "Industria y Minería": {"limite_5_a_7": 558602000, "limite_7_a_8": 840003000, "limite_8_to_12": 2709687000, "limite_12_to_15": 7969664000},
        "Comercio": {"limite_5_a_7": 745715000, "limite_7_a_8": 1121376000, "limite_8_to_12": 3617338000, "limite_12_to_15": 10639232000},
        "Servicios": {"limite_5_a_7": 182550000, "limite_7_a_8": 274512000, "limite_8_to_12": 885522000, "limite_12_to_15": 2604474000},
        "Construcción": {"limite_5_a_7": 223489000, "limite_7_a_8": 354120000, "limite_8_to_12": 1142320000, "limite_12_to_15": 3359767000}
    },
    2024: {
        "Agropecuario": {"limite_5_a_7": 87975000, "limite_7_a_8": 132293000, "limite_8_to_12": 426750000, "limite_12_to_15": 1255148000},
        "Industria y Minería": {"limite_5_a_7": 260100000, "limite_7_a_8": 391128000, "limite_8_to_12": 1261703000, "limite_12_to_15": 3710890000},
        "Comercio": {"limite_5_a_7": 347225000, "limite_7_a_8": 522143000, "limite_8_to_12": 1684330000, "limite_12_to_15": 4953913000},
        "Servicios": {"limite_5_a_7": 85000000, "limite_7_a_8": 127820000, "limite_8_to_12": 412323000, "limite_12_to_15": 1212713000},
        "Construcción": {"limite_5_a_7": 109650000, "limite_7_a_8": 164888000, "limite_8_to_12": 531895000, "limite_12_to_15": 1564398000}
    }
}

MAPEO_RUBROS = {
    "C": "Comercio", "COMERCIO": "Comercio",
    "I": "Industria y Minería", "INDUSTRIA": "Industria y Minería",
    "S": "Servicios", "SERVICIOS": "Servicios",
    "A": "Agropecuario", "AGROPECUARIO": "Agropecuario",
    "CONSTRUCCION": "Construcción", "CO": "Construcción"
}

def calcular_minimo_empleados(cantidad_empleados, anio, mes):
    if cantidad_empleados <= 0: return 0, 0
    elif cantidad_empleados == 1: modulos = 170
    elif cantidad_empleados == 2: modulos = 260
    elif cantidad_empleados == 3: modulos = 350
    else: modulos = 350 + (cantidad_empleados - 3) * 100
    
    valor_modulo_especifico = obtener_valor_modulo_real(anio, mes)
    return modulos, modulos * valor_modulo_especifico

def evaluar_contribuyente(anio, sector_raw, ingresos_globales_anio_anterior):
    sector = MAPEO_RUBROS.get(str(sector_raw).strip().upper(), "Comercio")
    if anio not in escalas_por_anio: return "Año No Válido", 0
    escalas_anio = escalas_por_anio[anio]
    if sector not in escalas_anio: return "Sector No Válido", 0
    
    topes = escalas_anio[sector]
    if ingresos_globales_anio_anterior < topes["limite_5_a_7"]: return "Pequeño", 5
    elif ingresos_globales_anio_anterior < topes["limite_7_a_8"]: return "Pequeño", 7
    elif ingresos_globales_anio_anterior < topes["limite_8_to_12"]: return "Mediano", 8
    elif ingresos_globales_anio_anterior < topes["limite_12_to_15"]: return "Grande", 12
    else: return "Grande", 15

# ==============================================================================
# 3. CREACIÓN DE LAS PESTAÑAS (ACÁ SE DEFINE TAB1 Y TAB2)
# ==============================================================================
tab1, tab2 = st.tabs(["🧮 Calculadora Individual", "📂 Matriz de Inconsistencias Masiva"])

# ------------------------------------------------------------------------------
# PESTAÑA 1: CONSULTA INDIVIDUAL
# ------------------------------------------------------------------------------
with tab1:
    st.header("Consulta Individual de Contribuyentes")
    col_a1, col_a2, col_b, col_c1, col_c2, col_d = st.columns([0.8, 1, 1.8, 1.8, 1.8, 0.8])
    
    with col_a1: anio_ind = st.selectbox("📅 Año Fiscal:", [2026, 2025, 2024], key="anio_individual")
    with col_a2: mes_ind = st.selectbox("📆 Mes Fiscal:", list(NOMBRES_MESES.keys()), format_func=lambda x: NOMBRES_MESES[x], key="mes_individual")
    with col_b: sector_sel = st.selectbox("Seleccione la Actividad:", ["Comercio", "Industria y Minería", "Servicios", "Agropecuario", "Construcción"])
    with col_c1: ingresos_globales_num = st.number_input("Ingresos Totales del Año Anterior ($):", min_value=0.0, format="%.2f", help="Determina la alícuota anual.")
    with col_c2: ingresos_sm_num = st.number_input("Facturación o Base Imponible Mensual ($):", min_value=0.0, format="%.2f", help="Monto neto asignado a San Martín.")
    with col_d: empleados_num = st.number_input("👥 Empleados:", min_value=0, step=1, value=1)
        
    if st.button("Calcular Alícuota y Mínimos", type="primary"):
        cat, alic = evaluar_contribuyente(anio_ind, sector_sel, ingresos_globales_num)
        modulos, impuesto_minimo = calcular_minimo_empleados(empleados_num, anio_ind, mes_ind)
        
        impuesto_por_alicuota = (ingresos_sm_num * alic) / 1000
        monto_final = max(impuesto_por_alicuota, impuesto_minimo)
        
        st.markdown("---")
        st.markdown(
            f"""
            <div style="background-color: #f0f4f8; padding: 20px; border-radius: 10px; border-left: 6px solid #1e3d59; margin-bottom: 20px;">
                <h4 style="margin: 0; color: #1e3d59; font-size: 18px;">Resultado — Período {NOMBRES_MESES[mes_ind]} / {anio_ind}</h4>
                <p style="margin: 8px 0 0 0; font-size: 22px; color: #12232e;">
                    Contribuyente <b>{cat.upper()}</b> — Alícuota Asignada (año anterior): <span style="color: #1e3d59; font-weight: bold;">{alic} ‰</span>
                </p>
            </div>
            """, unsafe_allow_html=True
        )
        
        col_res1, col_res2, col_res3 = st.columns(3)
        with col_res1: st.metric(label="Tasa por Alícuota (Mes)", value=f"$ {impuesto_por_alicuota:,.2f}")
        with col_res2: st.metric(label="Mínimo por Empleados", value=f"$ {impuesto_minimo:,.2f}", delta=f"{modulos} MF", delta_color="off")
        with col_res3: st.metric(label="MONTO DETERMINADO FINAL", value=f"$ {monto_final:,.2f}")

# ------------------------------------------------------------------------------
# PESTAÑA 2: CONTROL MASIVO + DASHBOARD ANALÍTICO
# ------------------------------------------------------------------------------
with tab2:
    st.header("🔬 Centro de Inteligencia y Dashboard Fiscal")
    st.markdown("""
    Cargá tu archivo vertical en crudo utilizando la plantilla estándar. El sistema procesará las diferencias de oficio
    y consolidará de forma automática un tablero gráfico interactivo.
    """)
    
    with st.expander("📋 Ver estructura requerida de la plantilla estándar (9 Columnas)"):
        st.code("CUIT | RAZON_SOCIAL | RUBRO | ING_ANUAL_PAIS | ANIO_FISCAL | MES_FISCAL | FACTURACION_MES | COEF_SM | PAGOS_MES")
        st.caption("Nota: Para contribuyentes directos locales, el COEF_SM debe completarse con 1.")

    archivo = st.file_uploader("📂 Cargar Archivo de Fiscalización (.xlsx)", type=["xlsx"], key="uploader_dashboard")
    
    if archivo is not None:
        try:
            df_raw = pd.read_excel(archivo)
            
            columnas_requeridas = ['RUBRO', 'ING_ANUAL_PAIS', 'ANIO_FISCAL', 'MES_FISCAL', 'FACTURACION_MES', 'COEF_SM', 'PAGOS_MES']
            if not all(col in df_raw.columns for col in columnas_requeridas):
                st.error("❌ El archivo no cumple con la estructura requerida de encabezados.")
            else:
                st.success("¡Datos cargados con éxito!")
                
                df = df_raw.copy()
                df['ING_ANUAL_PAIS'] = pd.to_numeric(df['ING_ANUAL_PAIS'], errors='coerce').fillna(0)
                df['ANIO_FISCAL'] = pd.to_numeric(df['ANIO_FISCAL'], errors='coerce').fillna(2026).astype(int)
                df['MES_FISCAL'] = pd.to_numeric(df['MES_FISCAL'], errors='coerce').fillna(1).astype(int)
                df['FACTURACION_MES'] = pd.to_numeric(df['FACTURACION_MES'], errors='coerce').fillna(0)
                df['COEF_SM'] = pd.to_numeric(df['COEF_SM'], errors='coerce').fillna(1)
                df['PAGOS_MES'] = pd.to_numeric(df['PAGOS_MES'], errors='coerce').fillna(0)
                
                # Procesamiento por fila en Pandas
                res_eval = df.apply(lambda r: evaluar_contribuyente(r['ANIO_FISCAL'], r['RUBRO'], r['ING_ANUAL_PAIS']), axis=1)
                df['Fisca_Tamaño'] = [r[0] for r in res_eval]
                df['Fisca_Alícuota_‰'] = [r[1] for r in res_eval]
                
                df['Fisca_Base_San_Martín'] = df['FACTURACION_MES'] * df['COEF_SM']
                df['Fisca_Tasa_por_Ingresos'] = (df['Fisca_Base_San_Martín'] * df['Fisca_Alícuota_‰']) / 1000
                
                res_minimos = df.apply(lambda r: calcular_minimo_empleados(1, r['ANIO_FISCAL'], r['MES_FISCAL']), axis=1)
                df['Fisca_Mínimo_Fijo'] = [r[1] for r in res_minimos]
                
                df['Fisca_Impuesto_Determinado'] = df[['Fisca_Tasa_por_Ingresos', 'Fisca_Mínimo_Fijo']].max(axis=1)
                df['Fisca_Diferencia_Desvío'] = df['Fisca_Impuesto_Determinado'] - df['PAGOS_MES']
                
                def definir_estado(x):
                    if x > 10: return "Inconsistente (Bajo Pago)"
                    elif x < -10: return "Saldo a Favor (Contribuyente)"
                    return "Correcto / Neteado"
                df['Fisca_Estado'] = df['Fisca_Diferencia_Desvío'].apply(definir_estado)

                # --- FILTROS DINÁMICOS EN SIDEBAR ---
                st.sidebar.header("🎯 Filtros del Dashboard")
                anios_disponibles = sorted(df['ANIO_FISCAL'].unique())
                anio_sel = st.sidebar.multiselect("Filtrar por Año Fiscal:", anios_disponibles, default=anios_disponibles)
                
                meses_disponibles = sorted(df['MES_FISCAL'].unique())
                mes_sel = st.sidebar.multiselect("Filtrar por Mes:", meses_disponibles, format_func=lambda x: NOMBRES_MESES.get(x, x), default=meses_disponibles)
                
                rubros_disponibles = df['RUBRO'].unique()
                rubro_sel = st.sidebar.multiselect("Filtrar por Rubro/Actividad:", rubros_disponibles, default=rubros_disponibles)
                
                df_filtrado = df[
                    (df['ANIO_FISCAL'].isin(anio_sel)) & 
                    (df['MES_FISCAL'].isin(mes_sel)) & 
                    (df['RUBRO'].isin(rubro_sel))
                ]
                
                st.markdown("---")
                st.subheader("📊 Tablero de Control de Gestión de Inteligencia Fiscal")
                
                total_contribuyentes = len(df_filtrado)
                df_inconsistentes = df_filtrado[df_filtrado['Fisca_Diferencia_Desvío'] > 10]
                cant_inconsistentes = len(df_inconsistentes)
                monto_total_evadido = df_inconsistentes['Fisca_Diferencia_Desvío'].sum()
                porcentaje_desvio = (cant_inconsistentes / total_contribuyentes * 100) if total_contribuyentes > 0 else 0
                
                kpi1, kpi2, kpi3 = st.columns(3)
                with kpi1: st.metric(label="👥 Contribuyentes Auditados", value=f"{total_contribuyentes:,}")
                with kpi2: st.metric(label="🔴 Casos con Inconsistencia", value=f"{cant_inconsistentes:,}", delta=f"{porcentaje_desvio:.1f}% del padrón", delta_color="inverse")
                with kpi3: st.metric(label="💰 Monto Total Omitido Recuperable", value=f"$ {monto_total_evadido:,.2f}")
                
                st.markdown("---")
                
                col_graf1, col_graf2 = st.columns(2)
                with col_graf1:
                    st.markdown("##### 🍕 Distribución del Padrón por Estado de Auditoría")
                    fig_torta = px.pie(
                        df_filtrado, names='Fisca_Estado', color='Fisca_Estado',
                        color_discrete_map={
                            "Inconsistente (Bajo Pago)": "#e63946",
                            "Correcto / Neteado": "#a8dadc",
                            "Saldo a Favor (Contribuyente)": "#457b9d"
                        }, hole=0.4
                    )
                    fig_torta.update_layout(margin=dict(t=20, b=20, l=20, r=20), height=300)
                    st.plotly_chart(fig_torta, use_container_width=True)
                    
                with col_graf2:
                    st.markdown("##### 🏢 Monto Omitido ($) por Rubro / Actividad")
                    df_rubro_monto = df_inconsistentes.groupby('RUBRO')['Fisca_Diferencia_Desvío'].sum().reset_index()
                    fig_barras = px.bar(
                        df_rubro_monto, x='RUBRO', y='Fisca_Diferencia_Desvío',
                        labels={'Fisca_Diferencia_Desvío': 'Monto Omitido ($)', 'RUBRO': 'Actividad'},
                        color='RUBRO', color_discrete_sequence=px.colors.qualitative.Safe
                    )
                    fig_barras.update_layout(showlegend=False, margin=dict(t=20, b=20, l=20, r=20), height=300)
                    st.plotly_chart(fig_barras, use_container_width=True)
                
                st.markdown("---")
                
                if len(df_filtrado['MES_FISCAL'].unique()) > 1:
                    st.markdown("##### 📈 Evolución Mensual del Monto Total Omitido Detectado")
                    df_linea = df_inconsistentes.groupby(['ANIO_FISCAL', 'MES_FISCAL'])['Fisca_Diferencia_Desvío'].sum().reset_index()
                    df_linea['Periodo'] = df_linea['ANIO_FISCAL'].astype(str) + "-" + df_linea['MES_FISCAL'].astype(str).str.zfill(2)
                    df_linea = df_linea.sort_values('Periodo')
                    
                    fig_linea = px.line(df_linea, x='Periodo', y='Fisca_Diferencia_Desvío', markers=True)
                    st.plotly_chart(fig_linea, use_container_width=True)
                    st.markdown("---")

                st.markdown("### 📋 Detalle de Contribuyentes Filtrados (Ordenado por Gravedad)")
                df_mostrar = df_filtrado.sort_values(by='Fisca_Diferencia_Desvío', ascending=False)
                st.dataframe(df_mostrar, use_container_width=True)
                
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    df_mostrar.to_excel(writer, index=False, sheet_name='Auditoria_Filtrada')
                processed_data = output.getvalue()
                
                st.download_button(
                    label="📥 Descargar esta Vista Filtrada en Excel",
                    data=processed_data,
                    file_name="auditoria_dashboard_filtrado.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
        except Exception as e:
            st.error(f"Error general en el sistema analítico: {e}")
