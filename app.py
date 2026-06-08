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

st.title("📊 Calculadora de Alícuotas e Inconsistencias Fiscales")
st.markdown("Herramienta interna para la Dirección de Inteligencia Fiscal")
st.markdown("---")

# VALOR DEL MÓDULO FISCAL
VALOR_MODULO = 89

# 1. ESTRUCTURA DE ESCALAS POR AÑO FISCAL (2025 y 2026 Corregidas)
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
    }
}

# 2. FUNCIÓN PARA CALCULAR EL MÍNIMO POR EMPLEADOS
def calcular_minimo_empleados(cantidad_empleados):
    if cantidad_empleados <= 0:
        return 0, 0
    elif cantidad_empleados == 1:
        modulos = 170
    elif cantidad_empleados == 2:
        modulos = 260
    elif cantidad_empleados == 3:
        modulos = 350
    else:
        # 350 de base por los primeros 3 + 100 por cada uno adicional
        modulos = 350 + (cantidad_empleados - 3) * 100
        
    monto_pesos = modulos * VALOR_MODULO
    return modulos, monto_pesos

# 3. FUNCIÓN DE EVALUACIÓN DE ALÍCUOTA
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
tab1, tab2 = st.tabs(["🧮 Calculadora Individual", "📂 Procesamiento Masivo (Excel)"])

with tab1:
    st.header("Consulta Individual de Contribuyente")
    
    # Diseño horizontal expandido a 4 columnas
    col_a, col_b, col_c, col_d = st.columns([1, 2, 2, 1])
    
    with col_a:
        anio_ind = st.selectbox("📅 Período:", [2026, 2025], key="anio_individual")
    with col_b:
        sector_sel = st.selectbox("Seleccione el Sector de Actividad:", list(escalas_por_anio[anio_ind].keys()))
    with col_c:
        ingresos_num = st.number_input("Ingresos Brutos Anuales ($):", min_value=0.0, step=10000.0, format="%.2f")
    with col_d:
        empleados_num = st.number_input("👥 Empleados:", min_value=0, step=1, value=1)
        
    if st.button("Calcular Alícuota y Mínimos", type="primary"):
        # Cálculos mecánicos
        cat, alic = evaluar_contribuyente(anio_ind, sector_sel, ingresos_num)
        modulos, impuesto_minimo = calcular_minimo_empleados(empleados_num)
        
        # El impuesto por ingresos brutos tradicional (Ingresos * Alícuota por mil)
        impuesto_por_alicuota = (ingresos_num * alic) / 1000
        
        # El monto final exigible es el mayor entre el mínimo por empleados y lo calculado por alícuota
        monto_final = max(impuesto_por_alicuota, impuesto_minimo)
        
        # Mostramos los resultados detallados
        st.success(f"**Resultado {anio_ind}:** Categoría: **{cat}** | Alícuota Asignada: **{alic} ‰**")
        
        # Panel de desglose de importes
        col_res1, col_res2, col_res3 = st.columns(3)
        with col_res1:
            st.metric(label="Impuesto por Alícuota (Ingresos)", value=f"$ {impuesto_por_alicuota:,.2f}")
        with col_res2:
            st.metric(label=f"Mínimo por Empleados ({modulos} MF)", value=f"$ {impuesto_minimo:,.2f}")
        with col_res3:
            st.warning(f"**Monto Determinado: $ {monto_final:,.2f}**")
            
        # Machete informativo de rangos
        t = escalas_por_anio[anio_ind][sector_sel]
        st.info(f"Rangos aplicados para {sector_sel} en el período {anio_ind}:\n"
                f"- Menos de ${t['limite_5_a_7']:,} ➡️ 5‰ (Pequeño)\n"
                f"- Desde ${t['limite_5_a_7']:,} hasta ${t['limite_7_a_8']-1:,} ➡️ 7‰ (Pequeño)\n"
                f"- Desde ${t['limite_7_a_8']:,} hasta ${t['limite_8_to_12']-1:,} ➡️ 8‰ (Mediano)\n"
                f"- Desde ${t['limite_8_to_12']:,} hasta ${t['limite_12_to_15']-1:,} ➡️ 12‰ (Grande)\n"
                f"- ${t['limite_12_to_15']:,} o más ➡️ 15‰ (Grande)")

with tab2:
    st.header("Control de Inconsistencias Masivo")
    st.markdown("Subí el Excel con el padrón para cruzar los datos y calcular diferencias automáticamente.")
    
    archivo = st.file_uploader("Cargar archivo Excel (.xlsx)", type=["xlsx"])
    
    if archivo is not None:
        try:
            df = pd.read_excel(archivo)
            st.write("📋 Vista previa de los datos cargados:")
            st.dataframe(df.head(3))
            
            columnas = df.columns.tolist()
            
            # Columnas de mapeo ahora agregando la de empleados
            col_x, col_y, col_w, col_z = st.columns(4)
            with col_x:
                col_sec = st.selectbox("Columna SECTOR / ACTIVIDAD:", columnas)
            with col_y:
                col_ing = st.selectbox("Columna INGRESOS / EMISIÓN:", columnas)
            with col_w:
                col_emp = st.selectbox("Columna CANTIDAD EMPLEADOS:", columnas)
            with col_z:
                anio_mas = st.selectbox("📅 Año Fiscal a Auditar:", [2026, 2025], key="anio_masivo")
            
            if st.button("Procesar y Buscar Inconsistencias", type="primary"):
                # 1. Calcular alícuotas e ingresos fila por fila
                res_alicuotas = df.apply(lambda r: evaluar_contribuyente(anio_mas, r[col_sec], r[col_ing]), axis=1)
                
                df['Año_Fiscal_Auditado'] = anio_mas
                df['Categoría_Calculada'] = [res[0] for res in res_alicuotas]
                df['Alícuota_Calculada_‰'] = [res[1] for res in res_alicuotas]
                
                # Impuesto calculado puramente por ingresos
                df['Impuesto_por_Ingresos_$'] = (df[col_ing] * df['Alícuota_Calculada_‰']) / 1000
                
                # 2. Calcular los mínimos por empleados fila por fila
                res_empleados = df[col_emp].apply(calcular_minimo_empleados)
                df['Módulos_Fiscales'] = [res[0] for res in res_empleados]
                df['Impuesto_Mínimo_Empleados_$'] = [res[1] for res in res_empleados]
                
                # 3. Cruzar para ver cuál es el mayor (Monto Determinado Oficial)
                df['Impuesto_Determinado_Oficial_$'] = df[['Impuesto_por_Ingresos_$', 'Impuesto_Mínimo_Empleados_$']].max(axis=1)
                
                st.success(f"¡Procesamiento masivo completado! Se calcularon alícuotas e impuestos mínimos.")
                
                # Configuramos la vista para formatear todas las columnas monetarias con "$"
                st.dataframe(df, column_config={
                    col_ing: st.column_config.NumberColumn(col_ing, format="$ %.2f"),
                    'Impuesto_por_Ingresos_$': st.column_config.NumberColumn('Impuesto por Ingresos', format="$ %.2f"),
                    'Impuesto_Mínimo_Empleados_$': st.column_config.NumberColumn('Mínimo Empleados', format="$ %.2f"),
                    'Impuesto_Determinado_Oficial_$': st.column_config.NumberColumn('Impuesto Determinado', format="$ %.2f")
                })
                
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    df.to_excel(writer, index=False, sheet_name=f'Control_Completo_{anio_mas}')
                processed_data = output.getvalue()
                
                st.download_button(
                    label=f"📥 Descargar Excel con Mínimos Calculados {anio_mas}",
                    data=processed_data,
                    file_name=f"control_fiscal_completo_{anio_mas}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
        except Exception as e:
            st.error(f"Error al procesar el archivo: {e}")
