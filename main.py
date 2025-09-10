import streamlit as st
import streamlit.components.v1 as components
from bokeh.embed import file_html
from bokeh.resources import CDN
from bokeh.document import Document
from bokeh.models import LayoutDOM
import pandas as pd

from file_io import leer_url_xlsx
from data_processing import limpiar_datos
from visualization import (
    tab_estadisticas,
    tab_histograma_ritmos,
    tab_mejores_sesiones_ritmo_distancia,
    tab_ritmo_medio_fecha,
    tab_tabla_por_fecha,
    tab_barras_lugares,
    tab_data_completo
)

st.set_page_config(page_title="Reporte de Rendimiento Deportivo", layout="wide")
st.title("🏃‍♂️ Reporte de Rendimiento Deportivo")

def mostrar_bokeh(obj, alto=600):
    if obj is None:
        return ""
    if not isinstance(obj, LayoutDOM):
        st.error("Objeto no es gráfico Bokeh válido")
        return ""
    doc = Document()
    doc.add_root(obj)
    html = file_html(doc, CDN, "Bokeh objeto")
    components.html(html, height=alto, scrolling=True)
    return html

for key in ["datos_cargados", "df", "nombre", "club"]:
    if key not in st.session_state:
        st.session_state[key] = False if key == "datos_cargados" else (None if key == "df" else "")

if not st.session_state.datos_cargados:
    with st.form("formulario_datos"):
        URL = st.text_input("📂 Ingresa la URL del archivo XLSX en Google Drive:")
        nombre = st.text_input("👤 Nombre y Apellidos:")
        club = st.text_input("🏅 Club:")
        enviado = st.form_submit_button("Cargar datos")
        if enviado and URL and nombre and club:
            df_ = leer_url_xlsx(URL)
            if df_ is None:
                st.error("❌ No se pudo obtener el archivo desde Google Drive.")
            elif df_.empty:
                st.warning("⚠️ El archivo está vacío o no tiene registros.")
            else:
                st.session_state.df = limpiar_datos(df_)
                st.session_state.nombre = nombre
                st.session_state.club = club
                st.session_state.datos_cargados = True
                st.success("Datos cargados. Ver reporte debajo.")

if st.session_state.datos_cargados and st.session_state.df is not None:
    df = st.session_state.df
    nombre = st.session_state.nombre
    club = st.session_state.club

    st.write(f"Bienvenido {nombre} del club {club}. Aquí está tu reporte:")

    report_html = """<!DOCTYPE html>
    <html lang="es">
    <head>
    <meta charset="UTF-8">
    <title>Reporte de Rendimiento Deportivo</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 20px;
        }
        h1 {
            font-size: 24px;
            margin-bottom: 12px;
            color: #333;
        }
        h2 {
            font-size: 20px;
            margin-bottom: 10px;
            color: #444;
        }
        h3 {
            font-size: 18px;
            margin-bottom: 8px;
            color: #555;
        }
        p {
            margin: 4px 0;
            font-size: 14px;
        }
        table {
            border-collapse: collapse;
            width: 100%;
            margin-top: 10px;
            font-size: 14px;
        }
        th, td {
            border: 1px solid #ccc;
            padding: 6px;
            text-align: left;
        }
        th {
            background-color: #f2f2f2;
        }
        .section {
            margin-bottom: 20px;
        }
    </style>
    </head><body>
    <h1>Reporte de Rendimiento Deportivo</h1>
    """


    # Nuevo orden de pestañas:
    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
        "📊 Estadística general",
        "⏱ Ritmo Medio por Fecha",
        "📈 Histograma de Ritmos",
        "🔥 Mejores Sesiones",
        "📅 Resumen por Fecha",
        "🌍 Lugares",
        "📋 Datos Completos"
    ])

    # Estadística general
    with tab1:
        html_estadisticas = tab_estadisticas(df, nombre, club)
        report_html += html_estadisticas
        report_html += "<div style='margin:40px 0;'></div>"


    # Ritmo Medio por Fecha
    with tab2:
        st.subheader("⏱ Ritmo Medio por Fecha")
        st.markdown(
        "Muestra cómo ha evolucionado el ritmo promedio de las sesiones "
        "a lo largo del tiempo. Permite identificar mejoras, tendencias y variaciones en el desempeño. "
        )
        medio = tab_ritmo_medio_fecha(df)
        st.bokeh_chart(medio, use_container_width=True)
        report_html += "<h2>Ritmo Medio por Fecha</h2>"
        report_html += file_html(medio, CDN, "")
        report_html += "<div style='margin:40px 0;'></div>"


    # Histograma de Ritmos
    with tab3:
        st.subheader("📈 Histograma de Ritmos")
        st.markdown(
        "Muestra la distribución de los ritmos de entrenamiento registrados. "
        "Permite visualizar con qué frecuencia se presentan diferentes rangos de ritmo. "
        )
        hist = tab_histograma_ritmos(df)
        st.bokeh_chart(hist, use_container_width=True)
        report_html += "<h2>Histograma de Ritmos</h2>"
        report_html += file_html(hist, CDN, "")
        report_html += "<div style='margin:40px 0;'></div>"


    # Mejores Sesiones
    with tab4:
        st.subheader("🔥 Mejores Sesiones")
        st.markdown(
        "Muestra las mejores sesiones de entrenamiento evaluadas por ritmo. "
        )
        mejores = tab_mejores_sesiones_ritmo_distancia(df)
        st.bokeh_chart(mejores, use_container_width=True)
        report_html += "<h2>Mejores Sesiones</h2>"
        report_html += file_html(mejores, CDN, "")
        report_html += "<div style='margin:40px 0;'></div>"


    # Tabla por Fecha
    with tab5:
        st.subheader("📅 Resumen por Fecha")
        st.markdown(
        "Muestra el rendimiento de las sesiones en cada día."
        )
        tabla_obj, tabla_html = tab_tabla_por_fecha(df)
        if isinstance(tabla_obj, LayoutDOM):
            mostrar_bokeh(tabla_obj, alto=600)
        else:
            st.write(tabla_obj)
        report_html += f"<h2>Resumen por Fecha</h2>{tabla_html}"
        report_html += "<div style='margin:40px 0;'></div>"


    # Lugares
    with tab6:
        st.subheader("🌍 Lugares de Entrenamiento")
        st.markdown(
        "Muestra la cantidad total de kilómetros acumulados en cada lugar de entrenamiento, "
        "desglosados por periodos definidos."
        )
        barras = tab_barras_lugares(df)
        st.bokeh_chart(barras, use_container_width=True)
        report_html += "<h2>Lugares de Entrenamiento</h2>"
        report_html += file_html(barras, CDN, "")
        report_html += "<div style='margin:40px 0;'></div>"


    # Datos Completos
    with tab7:
        data_completo = tab_data_completo(df)
        if isinstance(data_completo, LayoutDOM):
            mostrar_bokeh(data_completo, alto=600)
        else:
            st.write(data_completo)
        # Opcional: Para agregar tabla completa al HTML descargado descomentar esto:
        # if isinstance(data_completo, pd.DataFrame):
        #     report_html += "<h2>📋 Datos Completos</h2>" + data_completo.to_html(border=1, index=False)

    report_html += "</body></html>"

    st.download_button(
        label="💾 Guardar reporte en HTML",
        data=report_html.encode("utf-8"),
        file_name=f"reporte_{nombre.replace(' ', '_')}.html",
        mime="text/html"
    )

