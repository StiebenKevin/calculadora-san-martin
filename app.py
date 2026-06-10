import streamlit as st
import pandas as pd
from PIL import Image
import io

# Configuración de la página
st.set_page_config(page_title="Calculadora de Alícuotas - San Martín", page_icon="📊", layout="wide")

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

tab1, tab2 = st.tabs(["🧮 Calculadora Individual", "📂 Matriz de Inconsistencias Masiva"])

# --- PESTAÑA 1: CONSULTA INDIVIDUAL ---
with tab1:
    st.header("Consulta Individual")
    col_a1, col_a2, col_b, col_c1, col_c2, col_d = st.columns([0.8, 1, 1.8, 1.8, 1.8, 0.8])
    
    with col_a1: anio_ind = st.selectbox("📅 Año Fiscal a Liquidar:", [2026, 2025, 2024], key="anio_individual")
    with col_a2: mes_ind = st.selectbox("📆 Mes a Liquidar:", list(NOMBRES_MESES.keys()), format_func=lambda x: NOMBRES_MESES[x], key="mes_individual")
    with col_b: sector_sel = st.selectbox("Seleccione la Actividad:", ["Comercio", "Industria y Minería", "Servicios", "Agropecuario", "Construcción"])
    with col_c1: ingresos_globales_num = st.number_input("Ingresos Totales del Año Anterior ($):", min_value=0.0, format="%.2f", help="Determina la alícuota anual del contribuyente.")
    with col_c2: ingresos_sm_num = st.number_input("Facturación o Base Imponible Mensual ($):", min_value=0.0, format="%.2f", help="Monto del mes bajo análisis (aplicando convenios o directo).")
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
                    Contribuyente <b>{cat.upper()}</b> — Alícuota Asignada (vía año anterior): <span style="color: #1e3d59; font-weight: bold;">{alic} ‰</span>
                </p>
            </div>
            """, unsafe_allow_html=True
        )
        
        col_res1, col_res2, col_res3 = st.columns(3)
        with col_res1: st.metric(label=f"Tasa por Alícuota (Sobre base del mes)", value=f"$ {impuesto_por_alicuota:,.2f}")
        with col_res2: st.metric(label=f"Mínimo por Empleados (Mes Actual)", value=f"$ {impuesto_minimo:,.2f}", delta=f"{modulos} MF", delta_color="off")
        with col_res3: st.metric(label="MONTO DETERMINADO FINAL", value=f"$ {monto_final:,.2f}")

# --- PESTAÑA 2: CONTROL DE INCONSISTENCIAS MASIVO ---
with tab2:
    st.header("Análisis de Inconsistencias Mensual por Convenio Multilateral")
    st.markdown("Cargá el padrón. El sistema determinará la alícuota con los ingresos anuales previos y liquidará la cascada territorial con los datos de facturación del mes.")
    
    archivo = st.file_uploader("Cargar Padrón Excel (.xlsx)", type=["xlsx"])
    
    columnas = ["Subí un archivo para mapear"]
    deshabilitado = True
    df = None
    
    if archivo is not None:
        try:
            df = pd.read_excel(archivo)
            columnas = df.columns.tolist()
            deshabilitado = False
        except Exception as e:
            st.error(f"Error al abrir archivo: {e}")
            
    st.markdown("### ⚙️ Mapeo de Parámetros del Circuito de Fiscalización")
    
    col1, col2, col3, col4 = st.columns(4)
    col5, col6, col7, col8 = st.columns(4)
    
    with col1:
        c_rubro = st.selectbox("Rubro/Actividad (Col. T):", columnas, disabled=deshabilitado, index=columnas.index("RUBRO") if "RUBRO" in columnas else 0)
    with col2:
        c_ing_totales_ant = st.selectbox("Ingresos Anuales Año Anterior (Col. Y):", columnas, disabled=deshabilitado, index=columnas.index("INGRESOS SEGÚN IIBB 2023") if "INGRESOS SEGÚN IIBB 2023" in columnas else 0, help="Sirve estrictamente para fijar la alícuota anual.")
    with col3:
        c_ing_mes = st.selectbox("Facturación / Ingresos del MES:", columnas, disabled=deshabilitado, help="La materia base sobre la cual se liquida el período bajo análisis.")
    with col4:
        c_coef_arba = st.selectbox("Coeficiente ARBA (Col. Z):", columnas, disabled=deshabilitado, index=columnas.index("COEF IIBB 2023 BS AS") if "COEF IIBB 2023 BS AS" in columnas else 0)
        
    with col5:
        c_imp_det_arba = st.selectbox("Imp. Det. ARBA (Col. AC):", columnas, disabled=deshabilitado, index=columnas.index("IMP DET IIBB") if "IMP DET IIBB" in columnas else 0)
    with col6:
        c_coef_sm = st.selectbox("Coeficiente San Martín (Col. AE):", columnas, disabled=deshabilitado, index=columnas.index("COEF SAN MARTIN 2023") if "COEF SAN MARTIN 2023" in columnas else 0)
    with col7:
        c_empleados = st.selectbox("👥 Cantidad Empleados:", columnas, disabled=deshabilitado, index=columnas.index("EMPLEADOS") if "EMPLEADOS" in columnas else 0)
    with col8:
        c_pagos = st.selectbox("💰 Pagos / DDJJ del MES (Col. AL):", columnas, disabled=deshabilitado, index=columnas.index("PAGOS 2023") if "PAGOS 2023" in columnas else 0)

    st.markdown("---")
    col_p1, col_p2 = st.columns([1, 5])
    with col_p1: anio_m = st.selectbox("Año a Liquidar:", [2026, 2025, 2024], key="am")
    with col_p2: mes_m = st.selectbox("Mes a Liquidar:", list(NOMBRES_MESES.keys()), format_func=lambda x: NOMBRES_MESES[x], key="mm")

    if df is not None:
        st.markdown("---")
        if st.button("Correr Auditoría Mensual de Oficio y Buscar Desvíos 🚀", type="primary", use_container_width=True):
            try:
                # Asegurar parseo numérico correcto
                df[c_ing_totales_ant] = pd.to_numeric(df[c_ing_totales_ant], errors='coerce').fillna(0)
                df[c_ing_mes] = pd.to_numeric(df[c_ing_mes], errors='coerce').fillna(0)
                df[c_coef_arba] = pd.to_numeric(df[c_coef_arba], errors='coerce').fillna(0)
                df[c_imp_det_arba] = pd.to_numeric(df[c_imp_det_arba], errors='coerce').fillna(0)
                df[c_coef_sm] = pd.to_numeric(df[c_coef_sm], errors='coerce').fillna(0)
                df[c_empleados] = pd.to_numeric(df[c_empleados], errors='coerce').fillna(0).astype(int)
                df[c_pagos] = pd.to_numeric(df[c_pagos], errors='coerce').fillna(0)
                
                # --- PASO 1: Determinar Alícuota por Ingresos del Año Anterior (Fijo Anual) ---
                res_eval = df.apply(lambda r: evaluar_contribuyente(anio_m, r[c_rubro], r[c_ing_totales_ant]), axis=1)
                df['Fisca_Tamaño'] = [r[0] for r in res_eval]
                df['Fisca_Alícuota_‰'] = [r[1] for r in res_eval]
                
                # --- PASO 2: Liquidar el Período usando la Facturación Mensual ---
                # Facturación del mes * Coeficiente ARBA
                df['Fisca_Base_Imponible_PBA'] = df[c_ing_mes] * df[c_coef_arba]
                
                # Base PBA Menos Impuesto Determinado ARBA
                df['Fisca_Base_PBA_Final'] = df['Fisca_Base_Imponible_PBA'] - df[c_imp_det_arba]
                
                # Si es contribuyente directo (no intermunicipal), la base PBA Final pasa entera para San Martín.
                # Si tiene coeficiente San Martín, se multiplica por el mismo.
                df['Fisca_Base_San_Martín'] = df.apply(
                    lambda r: r['Fisca_Base_PBA_Final'] * r[c_coef_sm] if r[c_coef_sm] > 0 else r['Fisca_Base_PBA_Final'], 
                    axis=1
                )
                
                # --- PASO 3: Cálculo del Impuesto Teórico por Alícuota vs Mínimos ---
                df['Fisca_Tasa_por_Ingresos'] = (df['Fisca_Base_San_Martín'] * df['Fisca_Alícuota_‰']) / 1000
                
                res_minimos = df[c_empleados].apply(lambda x: calcular_minimo_empleados(x, anio_m, mes_m))
                df['Fisca_Mínimo_Empleados'] = [r[1] for r in res_minimos]
                
                # El impuesto determinado teórico es el mayor valor
                df['Fisca_Impuesto_Determinado'] = df[['Fisca_Tasa_por_Ingresos', 'Fisca_Mínimo_Empleados']].max(axis=1)
                
                # --- PASO 4: Contraste con lo Declarado/Pagado en el Mes ---
                df['Fisca_Diferencia_Desvío'] = df['Fisca_Impuesto_Determinado'] - df[c_pagos]
                
                def definir_estado(dif):
                    if dif > 10: return "🔴 BAJO PAGO / INCONSISTENTE"
                    elif dif < -10: return "🟢 SALDO A FAVOR"
                    return "⚪ CORRECTO / NETEADO"
                    
                df['Fisca_Estado_Auditoría'] = df['Fisca_Diferencia_Desvío'].apply(definir_estado)
                
                st.success(f"¡Auditoría de Oficio finalizada para el período {NOMBRES_MESES[mes_m]} / {anio_m}!")
                
                inconsistentes = df[df['Fisca_Diferencia_Desvío'] > 10]
                m_tot_inconsistencias = inconsistentes['Fisca_Diferencia_Desvío'].sum()
                
                m1, m2, m3 = st.columns(3)
                with m1: st.metric("Contribuyentes Fiscalizados", f"{len(df)}")
                with m2: st.metric("Casos Inconsistentes", f"{len(inconsistentes)}", delta=f"{len(inconsistentes)/len(df)*100:.1f}%", delta_color="inverse")
                with m3: st.metric("Monto Total Omitido en el Mes", f"$ {m_tot_inconsistencias:,.2f}")
                
                st.markdown("### 📋 Resultados del Período (Ordenado por Gravedad)")
                df_mostrar = df.sort_values(by='Fisca_Diferencia_Desvío', ascending=False)
                st.dataframe(df_mostrar, use_container_width=True)
                
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    df_mostrar.to_excel(writer, index=False, sheet_name=f'Fisca_Mes_{mes_m}')
                processed_data = output.getvalue()
                
                st.download_button(
                    label=f"📥 Descargar Reporte Mensual {NOMBRES_MESES[mes_m]}_{anio_m}",
                    data=processed_data,
                    file_name=f"auditoria_fiscal_{NOMBRES_MESES[mes_m]}_{anio_m}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
                
            except Exception as e:
                st.error(f"Error al computar las bases con la facturación mensual: {e}")
