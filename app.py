import streamlit as st
import pandas as pd
from PIL import Image
import io

# Configuración de la página
st.set_page_config(page_title="Calculadora de Alícuotas - San Martín", page_icon="📊", layout="wide")

# Intentar cargar el logo municipal
try:
    image = Image.open('logo_san_martin.png')
    st.image(image, width=250)
except:
    st.subheader("Municipalidad de General San Martín")

st.title("📊 Calculadora de Alícuotas")
st.markdown("---")

# Nombre de los meses para los selectbox
NOMBRES_MESES = {
    1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril", 5: "Mayo", 6: "Junio",
    7: "Julio", 8: "Agosto", 9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"
}

# 1. FUNCIÓN MATRIZ: DETERMINA EL VALOR DEL MÓDULO FISCAL SEGÚN DECRETO REAL
def obtener_valor_modulo_real(anio, mes):
    if anio == 2026:
        return 89.00  # Desde 01/01/2026 al presente ($89.00)
        
    elif anio == 2025:
        if 1 <= mes <= 6:
            return 64.00  # Del 01/01/2025 al 30/06/2025
        elif 7 <= mes <= 9:
            return 69.00  # Del 01/07/2025 al 30/09/2025
        elif mes == 10:
            return 71.00  # Del 01/10/2025 al 31/10/2025
        elif 11 <= mes <= 12:
            return 74.00  # Del 01/11/2025 al 31/12/2025
            
    elif anio == 2024:
        if 1 <= mes <= 3:
            return 26.00  # Del 01/01/2024 al 31/03/2024
        elif 4 <= mes <= 6:
            return 49.40  # Del 01/04/2024 al 30/06/2024
        elif 7 <= mes <= 8:
            return 52.00  # Del 01/07/2024 al 31/08/2024
        elif 9 <= mes <= 11:
            return 57.00  # Del 01/09/2024 al 30/11/2024
        elif mes == 12:
            return 58.00  # Del 01/12/2024 al 31/12/2024
            
    return 89.00  # Valor por defecto seguro

# 2. ESTRUCTURA DE ESCALAS POR AÑO FISCAL
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

# 3. FUNCIÓN PARA CALCULAR EL MÍNIMO POR EMPLEADOS
def calcular_minimo_empleados(cantidad_empleados, anio, mes):
    if cantidad_empleados <= 0:
        return 0, 0
    elif cantidad_empleados == 1:
        modulos = 170
    elif cantidad_empleados == 2:
        modulos = 260
    elif cantidad_empleados == 3:
        modulos = 350
    else:
        modulos = 350 + (cantidad_empleados - 3) * 100
        
    valor_modulo_especifico = obtener_valor_modulo_real(anio, mes)
    monto_pesos = modulos * valor_modulo_especifico
    return modulos, monto_pesos

# 4. FUNCIÓN DE EVALUACIÓN DE ALÍCUOTA
def evaluar_contribuyente(anio, sector, ingresos):
    if anio not in escalas_por_anio:
        return "Año No Válido", 0
    
    escalas_anio = escalas_por_anio[anio]
    if sector not in escalas_anio:
        return "Sector No Válido", 0
    
    topes = escalas_anio[sector]
    
    if ingresos < topes["limite_5_a_7"]:
        return "Pequeño", 5
    elif ingresos < topes["limite_7_a_8"]:
        return "Pequeño", 7
    elif ingresos < topes["limite_8_to_12"]:
        return "Mediano", 8
    elif ingresos < topes["limite_12_to_15"]:
        return "Grande", 12
    else:
        return "Grande", 15

# Pestañas de la aplicación
tab1, tab2 = st.tabs(["🧮 Calculadora Individual", "📂 Calculadora Masiva (Excel)"])

with tab1:
    st.header("Consulta Individual")
    
    col_a1, col_a2, col_b, col_c, col_d = st.columns([1, 1.2, 2, 2, 1])
    
    with col_a1:
        anio_ind = st.selectbox("📅 Año:", [2026, 2025, 2024], key="anio_individual")
    with col_a2:
        mes_ind = st.selectbox("📆 Mes:", list(NOMBRES_MESES.keys()), format_func=lambda x: NOMBRES_MESES[x], key="mes_individual")
    with col_b:
        sector_sel = st.selectbox("Seleccione la Actividad:", list(escalas_por_anio[anio_ind].keys()))
    with col_c:
        ingresos_num = st.number_input("Ingreso Total gravado del periodo anterior ($):", min_value=0.0, step=10000.0, format="%.2f")
    with col_d:
        empleados_num = st.number_input("👥 Empleados:", min_value=0, step=1, value=1)
        
    if st.button("Calcular Alícuota y Mínimos", type="primary"):
        cat, alic = evaluar_contribuyente(anio_ind, sector_sel, ingresos_num)
        modulos, impuesto_minimo = calcular_minimo_empleados(empleados_num, anio_ind, mes_ind)
        impuesto_por_alicuota = (ingresos_num * alic) / 1000
        monto_final = max(impuesto_por_alicuota, impuesto_minimo)
        
        st.markdown("---")
        
        st.markdown(
            f"""
            <div style="background-color: #f0f4f8; padding: 20px; border-radius: 10px; border-left: 6px solid #1e3d59; margin-bottom: 20px;">
                <h4 style="margin: 0; color: #1e3d59; font-size: 18px;">📋 Veredicto de Auditoría — Período {NOMBRES_MESES[mes_ind]} / {anio_ind}</h4>
                <p style="margin: 8px 0 0 0; font-size: 22px; color: #12232e;">
                    Contribuyente <b>{cat.upper()}</b> — Alícuota Asignada: <span style="color: #1e3d59; font-weight: bold;">{alic} ‰</span>
                </p>
            </div>
            """, 
            unsafe_allow_html=True
        )
        
        col_res1, col_res2, col_res3 = st.columns(3)
        with col_res1:
            st.metric(label="Tasa por Alícuota (Ingresos)", value=f"$ {impuesto_por_alicuota:,.2f}")
        with col_res2:
            st.metric(label=f"Mínimo por Dotación ({NOMBRES_MESES[mes_ind]} {anio_ind})", value=f"$ {impuesto_minimo:,.2f}", delta=f"{modulos} MF", delta_color="off")
        with col_res3:
            st.metric(label="⚡ MONTO DETERMINADO FINAL", value=f"$ {monto_final:,.2f}")
            
        st.markdown("### 🔍 Cuadros de Referencia Fiscal")
        col_tab_a, col_tab_b = st.columns(2)
        
        with col_tab_a:
            t = escalas_por_anio[anio_ind][sector_sel]
            st.markdown(f"**Escala de Alícuotas {anio_ind}: {sector_sel}**")
            
            tabla_escalas_html = f"""
            <table style="width:100%; border-collapse: collapse; margin-top: 10px; font-size: 14px;">
                <tr style="background-color: #1e3d59; color: white; text-align: left;">
                    <th style="padding: 8px; border: 1px solid #ddd;">Rango de Ingresos Brutos Anuales</th>
                    <th style="padding: 8px; border: 1px solid #ddd; text-align: center;">Alícuota</th>
                    <th style="padding: 8px; border: 1px solid #ddd;">Segmento</th>
                </tr>
                <tr>
                    <td style="padding: 8px; border: 1px solid #ddd;">Menos de ${t['limite_5_a_7']:,}</td>
                    <td style="padding: 8px; border: 1px solid #ddd; text-align: center; font-weight: bold;">5 ‰</td>
                    <td style="padding: 8px; border: 1px solid #ddd; color: #2d7f5e;">Pequeño</td>
                </tr>
                <tr style="background-color: #f9f9f9;">
                    <td style="padding: 8px; border: 1px solid #ddd;">Desde ${t['limite_5_a_7']:,} hasta ${t['limite_7_a_8']-1:,}</td>
                    <td style="padding: 8px; border: 1px solid #ddd; text-align: center; font-weight: bold;">7 ‰</td>
                    <td style="padding: 8px; border: 1px solid #ddd; color: #2d7f5e;">Pequeño</td>
                </tr>
                <tr>
                    <td style="padding: 8px; border: 1px solid #ddd;">Desde ${t['limite_7_a_8']:,} hasta ${t['limite_8_to_12']-1:,}</td>
                    <td style="padding: 8px; border: 1px solid #ddd; text-align: center; font-weight: bold;">8 ‰</td>
                    <td style="padding: 8px; border: 1px solid #ddd; color: #b7791f;">Mediano</td>
                </tr>
                <tr style="background-color: #f9f9f9;">
                    <td style="padding: 8px; border: 1px solid #ddd;">Desde ${t['limite_8_to_12']:,} hasta ${t['limite_12_to_15']-1:,}</td>
                    <td style="padding: 8px; border: 1px solid #ddd; text-align: center; font-weight: bold;">12 ‰</td>
                    <td style="padding: 8px; border: 1px solid #ddd; color: #c53030;">Grande</td>
                </tr>
                <tr>
                    <td style="padding: 8px; border: 1px solid #ddd;">${t['limite_12_to_15']:,} o más</td>
                    <td style="padding: 8px; border: 1px solid #ddd; text-align: center; font-weight: bold;">15 ‰</td>
                    <td style="padding: 8px; border: 1px solid #ddd; color: #c53030;">Grande</td>
                </tr>
            </table>
            """
            st.markdown(tabla_escalas_html, unsafe_allow_html=True)
            
        with col_tab_b:
            mod_actual = obtener_valor_modulo_real(anio_ind, mes_ind)
            st.markdown(f"**Mínimos (Módulo Fiscal {NOMBRES_MESES[mes_ind]} {anio_ind}: ${mod_actual:.2f})**")
            
            tabla_minimos_html = f"""
            <table style="width:100%; border-collapse: collapse; margin-top: 10px; font-size: 14px;">
                <tr style="background-color: #1e3d59; color: white; text-align: left;">
                    <th style="padding: 8px; border: 1px solid #ddd;">Dotación de Personal</th>
                    <th style="padding: 8px; border: 1px solid #ddd; text-align: center;">Módulos (MF)</th>
                    <th style="padding: 8px; border: 1px solid #ddd; text-align: right;">Importe en Pesos</th>
                </tr>
                <tr>
                    <td style="padding: 8px; border: 1px solid #ddd;">1 Empleado</td>
                    <td style="padding: 8px; border: 1px solid #ddd; text-align: center;">170 MF</td>
                    <td style="padding: 8px; border: 1px solid #ddd; text-align: right; font-weight: bold;">$ {170 * mod_actual:,.2f}</td>
                </tr>
                <tr style="background-color: #f9f9f9;">
                    <td style="padding: 8px; border: 1px solid #ddd;">2 Empleados</td>
                    <td style="padding: 8px; border: 1px solid #ddd; text-align: center;">260 MF</td>
                    <td style="padding: 8px; border: 1px solid #ddd; text-align: right; font-weight: bold;">$ {260 * mod_actual:,.2f}</td>
                </tr>
                <tr>
                    <td style="padding: 8px; border: 1px solid #ddd;">3 Empleados</td>
                    <td style="padding: 8px; border: 1px solid #ddd; text-align: center;">350 MF</td>
                    <td style="padding: 8px; border: 1px solid #ddd; text-align: right; font-weight: bold;">$ {350 * mod_actual:,.2f}</td>
                </tr>
                <tr style="background-color: #f9f9f9;">
                    <td style="padding: 8px; border: 1px solid #ddd;">4 o más Empleados</td>
                    <td style="padding: 8px; border: 1px solid #ddd; text-align: center;">350 + 100 por adicional</td>
                    <td style="padding: 8px; border: 1px solid #ddd; text-align: right; font-weight: bold;">$ {350 * mod_actual:,.2f} + $ {100 * mod_actual:,.2f} c/u</td>
                </tr>
            </table>
            """
            st.markdown(tabla_minimos_html, unsafe_allow_html=True)

with tab2:
    st.header("Control de Inconsistencias Masivo")
    st.markdown("Subí el Excel con el padrón en el área central. Luego, configurá los campos en la **barra lateral izquierda**.")
    
    archivo = st.file_uploader("Cargar archivo Excel (.xlsx)", type=["xlsx"])
    
    if archivo is not None:
        try:
            df = pd.read_excel(archivo)
            st.write("📋 Vista previa de los datos cargados:")
            st.dataframe(df.head(3), use_container_width=True)
            
            columnas = df.columns.tolist()
            
            # PASO 1: SECTORES Y SELECTORES LLEVADOS EXCLUSIVAMENTE AL SIDEBAR
            st.sidebar.markdown("### ⚙️ Configuración del Padrón")
            col_sec = st.sidebar.selectbox("Columna SECTOR / ACTIVIDAD:", columnas)
            col_ing = st.sidebar.selectbox("Columna INGRESOS / EMISIÓN:", columnas)
            col_emp = st.sidebar.selectbox("Columna CANTIDAD EMPLEADOS:", columnas)
            
            st.sidebar.markdown("### 📅 Período Normativo")
            anio_mas = st.sidebar.selectbox("📅 Año Fiscal:", [2026, 2025, 2024], key="anio_masivo")
            mes_mas = st.sidebar.selectbox("📆 Mes Fiscal:", list(NOMBRES_MESES.keys()), format_func=lambda x: NOMBRES_MESES[x], key="mes_masivo")
            
            # Botón de ejecución en el sidebar para liberar espacio en pantalla principal
            if st.sidebar.button("Procesar y Buscar Inconsistencias", type="primary", use_container_width=True):
                res_alicuotas = df.apply(lambda r: evaluar_contribuyente(anio_mas, r[col_sec], r[col_ing]), axis=1)
                
                df['Año_Fiscal_Auditado'] = anio_mas
                df['Mes_Fiscal_Auditado'] = NOMBRES_MESES[mes_mas]
                df['Valor_Módulo_Aplicado'] = obtener_valor_modulo_real(anio_mas, mes_mas)
                df['Categoría_Calculada'] = [res[0] for res in res_alicuotas]
                df['Alícuota_Calculada_‰'] = [res[1] for res in res_alicuotas]
                df['Impuesto_por_Ingresos_$'] = (df[col_ing] * df['Alícuota_Calculada_‰']) / 1000
                
                res_empleados = df[col_emp].apply(lambda x: calcular_minimo_empleados(x, anio_mas, mes_mas))
                df['Mínimo_Empleados_MF'] = [res[0] for res in res_empleados]
                df['Mínimo_Empleados_$'] = [res[1] for res in res_empleados]
                
                df['Impuesto_Determinado_Oficial_$'] = df[['Impuesto_por_Ingresos_$', 'Mínimo_Empleados_$']].max(axis=1)
                
                st.success(f"¡Procesamiento masivo completado para {NOMBRES_MESES[mes_mas]} / {anio_mas}!")
                
                st.dataframe(df, use_container_width=True, column_config={
                    col_ing: st.column_config.NumberColumn(col_ing, format="$ %.2f"),
                    'Valor_Módulo_Aplicado': st.column_config.NumberColumn('Módulo ($)', format="$ %.2f"),
                    'Impuesto_por_Ingresos_$': st.column_config.NumberColumn('Impuesto por Ingresos', format="$ %.2f"),
                    'Mínimo_Empleados_$': st.column_config.NumberColumn('Mínimo por Empleados ($)', format="$ %.2f"),
                    'Impuesto_Determinado_Oficial_$': st.column_config.NumberColumn('Monto Determinado Final', format="$ %.2f")
                })
                
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    df.to_excel(writer, index=False, sheet_name=f'Auditoria_{mes_mas}_{anio_mas}')
                processed_data = output.getvalue()
                
                st.download_button(
                    label=f"📥 Descargar Excel {NOMBRES_MESES[mes_mas]}_{anio_mas}",
                    data=processed_data,
                    file_name=f"control_fiscal_{mes_mas}_{anio_mas}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
        except Exception as e:
            st.error(f"Error al procesar el archivo: {e}")
