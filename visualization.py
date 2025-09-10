import pandas as pd
import numpy as np
import streamlit as st
from bokeh.plotting import figure
from bokeh.models import ColumnDataSource, DataTable, TableColumn, Div
from scipy.stats import norm
from bokeh.transform import dodge
from bokeh.palettes import Category10


# =========================
# Tamaño estándar para gráficos
# =========================
PLOT_WIDTH = 900
PLOT_HEIGHT = 500


# =========================
# Utilidades internas
# =========================
def _ritmo_to_minutos(series):
    """Convierte una Serie de 'Ritmos' a minutos (float). Soporta timedelta64 y numérico."""
    if pd.api.types.is_timedelta64_dtype(series):
        return series.dt.total_seconds() / 60.0
    # Si ya es numérico, asumimos que está en minutos
    if pd.api.types.is_numeric_dtype(series):
        return series.astype(float)
    # Si llega en string u otro, intentamos parsear como mm:ss
    def _parse_one(x):
        if pd.isna(x):
            return np.nan
        s = str(x)
        if ":" in s:
            parts = s.split(":")
            if len(parts) == 2:
                m, sec = parts
                return float(m) + float(sec) / 60.0
        try:
            return float(s)
        except Exception:
            return np.nan
    return series.map(_parse_one)


def _ensure_fecha_datetime(df, col="Fecha"):
    if col in df.columns and not pd.api.types.is_datetime64_any_dtype(df[col]):
        with pd.option_context("mode.chained_assignment", None):
            df[col] = pd.to_datetime(df[col], errors="coerce")
    return df


# =====================================================
def tab_estadisticas(df, nombre, club):

    def formato_mmss(td):
        if isinstance(td, pd.Timedelta):
            total_segundos = int(td.total_seconds())
        else:
            total_segundos = int(float(td) * 60)
        minutos, segundos = divmod(total_segundos, 60)
        return f"{minutos:02d}:{segundos:02d}"

    if df.empty or "Ritmos" not in df.columns:
        st.warning("No hay datos disponibles.")
        return ""

    try:
        entrenamientos_totales = (df['Distancia_km'] == 1).sum()
    except Exception:
        entrenamientos_totales = len(df)

    km_totales = len(df)  # ajusta según cómo calculas

    ritmo_promedio_raw = df["Ritmos"].mean()
    if pd.api.types.is_timedelta64_dtype(df["Ritmos"]):
        ritmo_promedio_td = ritmo_promedio_raw
    else:
        ritmo_promedio_td = pd.to_timedelta(
            float(_ritmo_to_minutos(df["Ritmos"]).mean()), unit="m"
        )

    km_max = df.get("Distancia_km", pd.Series([np.nan])).max()

    mejor_ritmo_raw = df["Ritmos"].min()
    if pd.api.types.is_timedelta64_dtype(df["Ritmos"]):
        mejor_ritmo_td = mejor_ritmo_raw
    else:
        mejor_ritmo_td = pd.to_timedelta(
            float(_ritmo_to_minutos(df["Ritmos"]).min()), unit="m"
        )

    fila_mejor = df.loc[df["Ritmos"] == mejor_ritmo_raw].iloc[0] if not df.empty else None
    mejor_fecha, mejor_lugar = "", ""
    if fila_mejor is not None:
        if "Fecha" in df.columns:
            _ensure_fecha_datetime(df, "Fecha")
            try:
                mejor_fecha = fila_mejor["Fecha"].strftime("%d-%m-%Y")
            except Exception:
                mejor_fecha = str(fila_mejor["Fecha"])
        if "Lugar" in df.columns:
            mejor_lugar = str(fila_mejor["Lugar"])

    # Mostrar en la app con columnas
    col1, col2, col3 = st.columns(3)
    with col1:
        st.subheader("Información personal")
        st.markdown(f"**Nombre:** {nombre}")
        st.markdown(f"**Club:** {club}")

    with col2:
        st.subheader("Estadísticas generales")
        st.markdown(f"**Sesiones totales:** {int(entrenamientos_totales)}")
        st.markdown(f"**Distancia acumulada:** {km_totales} km")
        st.markdown(f"**Ritmo promedio:** {formato_mmss(ritmo_promedio_td)} min/km")

    with col3:
        st.subheader("Destacado")
        st.markdown(f"**Sesión más larga:** {km_max} km")
        st.markdown(f"**Mejor ritmo:** {formato_mmss(mejor_ritmo_td)} min/km")
        st.markdown(f"(Fecha: {mejor_fecha})")
        st.markdown(f"(Lugar: {mejor_lugar})")

    # También retornar HTML para reporte descargable
        # También retornar HTML para reporte descargable (en columnas)
    html = f"""
    <div style="display:flex; justify-content: space-between; gap:20px;">

        <div style="flex:1; border:1px solid #ccc; padding:10px; border-radius:8px;">
            <h2>Información personal</h2>
            <p><b>Nombre:</b> {nombre}</p>
            <p><b>Club:</b> {club}</p>
        </div>

        <div style="flex:1; border:1px solid #ccc; padding:10px; border-radius:8px;">
            <h2>Estadísticas generales</h2>
            <p><b>Sesiones totales:</b> {int(entrenamientos_totales)}</p>
            <p><b>Distancia acumulada:</b> {km_totales} km</p>
            <p><b>Ritmo promedio:</b> {formato_mmss(ritmo_promedio_td)} min/km</p>
        </div>

        <div style="flex:1; border:1px solid #ccc; padding:10px; border-radius:8px;">
            <h2>Destacado</h2>
            <p><b>Sesión más larga:</b> {km_max} km</p>
            <p><b>Mejor ritmo:</b> {formato_mmss(mejor_ritmo_td)} min/km</p>
            <p>(Fecha: {mejor_fecha})</p>
            <p>(Lugar: {mejor_lugar})</p>
        </div>

    </div>
    """

    return html


# ====================================================================
def tab_histograma_ritmos(df):
    
    if df.empty or "Ritmos" not in df.columns:
        return figure(title="No hay datos de ritmos disponibles")

    ritmos_min = _ritmo_to_minutos(df["Ritmos"]).dropna()
    if ritmos_min.empty:
        return figure(title="No hay datos de ritmos disponibles")

    hist, edges = np.histogram(ritmos_min, bins=20)
    p = figure(
        title=None,
        x_axis_label="Ritmo (min/km)",
        y_axis_label="Frecuencia",
        plot_width=PLOT_WIDTH,
        plot_height=PLOT_HEIGHT
    )
    p.quad(top=hist, bottom=0, left=edges[:-1], right=edges[1:], fill_color="navy", line_color="white", alpha=0.7)

    mu, std = norm.fit(ritmos_min)
    x = np.linspace(float(ritmos_min.min()), float(ritmos_min.max()), 100)
    y = norm.pdf(x, mu, std) * len(ritmos_min) * (edges[1] - edges[0])
    p.line(x, y, line_color="red", line_width=2)

    return p


# ====================================================================
def tab_mejores_sesiones_ritmo_distancia(df):
    
    if df.empty or "Ritmos" not in df.columns or "Distancia_km" not in df.columns or "Fecha" not in df.columns:
        return figure(title="No hay datos disponibles")

    df_plot = df.copy()
    _ensure_fecha_datetime(df_plot, "Fecha")
    df_plot["Ritmo_min"] = _ritmo_to_minutos(df_plot["Ritmos"])

    # Calcular el promedio de ritmo por sesión (Fecha)
    sesiones = (
        df_plot.groupby("Fecha")["Ritmo_min"]
        .mean()
        .reset_index()
        .rename(columns={"Ritmo_min": "Ritmo_promedio"})
    )

    # Seleccionar las 5 sesiones más rápidas (menor Ritmo promedio)
    top5_fechas = sesiones.nsmallest(5, "Ritmo_promedio")["Fecha"]

    # Definir rango dinámico en eje X
    max_distancia = df_plot["Distancia_km"].max()
    p = figure(
        title=None,
        x_axis_label="Distancia (km)",
        y_axis_label="Ritmo (min/km)",
        x_range=(0, max_distancia + 1),
        plot_width=PLOT_WIDTH,
        plot_height=PLOT_HEIGHT
    )

    colors = ["red", "green", "blue", "orange", "purple"]

    # Graficar las 5 mejores sesiones (solo líneas)
    for i, fecha in enumerate(top5_fechas):
        sesion = df_plot[df_plot["Fecha"] == fecha].sort_values("Distancia_km")
        source = ColumnDataSource(sesion)
        p.line(
            x="Distancia_km",
            y="Ritmo_min",
            source=source,
            line_width=5,        # más ancho
            color=colors[i % len(colors)],
            alpha=0.6,           # más transparente
            legend_label=fecha.strftime("%d-%m-%Y")
        )

    p.legend.title = "Top 5 Sesiones"
    p.legend.location = "top_right"

    return p


# ====================================================================
def tab_ritmo_medio_fecha(df):
    
    if df.empty or "Fecha" not in df.columns or "Ritmos" not in df.columns:
        return figure(title="No hay datos disponibles")

    df2 = df.copy()
    _ensure_fecha_datetime(df2, "Fecha")
    grp = df2.groupby("Fecha")["Ritmos"].mean().reset_index()
    grp["Ritmo_min"] = _ritmo_to_minutos(grp["Ritmos"])

    source = ColumnDataSource(grp)
    # Cálculo del límite inferior del eje Y: 15 segundos (0.25 min) por debajo del menor ritmo
    y_min = grp["Ritmo_min"].min() - 0.25
    y_max = grp["Ritmo_min"].max() + 0.25

    p = figure(
        title=None,
        x_axis_type="datetime",
        x_axis_label="Fecha",
        y_axis_label="Ritmo (min/km)",
        y_range=(y_min, y_max),
        plot_width=PLOT_WIDTH,
        plot_height=PLOT_HEIGHT
    )
    p.varea(
        x="Fecha",
        y1=y_min,
        y2="Ritmo_min",
        source=source,
        fill_color="green",
        fill_alpha=0.25
    )
    p.line("Fecha", "Ritmo_min", source=source, line_width=2, color="green")
    p.circle("Fecha", "Ritmo_min", source=source, size=6, color="green", alpha=0.7)
    return p


# ====================================================================
def tab_tabla_por_fecha(df):
    
    if df.empty:
        st.warning("No hay datos disponibles.")
        return Div(text="<p><b>No hay datos disponibles.</b></p>"), "<p><b>No hay datos disponibles.</b></p>"

    df2 = df.copy()
    _ensure_fecha_datetime(df2, "Fecha")
    agg = df2.groupby("Fecha").agg({
        "Distancia_km": "max",
        "Ritmos": "mean"
    }).reset_index()

    def minutos_a_mmss(valor_min):
        total_sec = int(round(valor_min * 60))
        minutos, segundos = divmod(total_sec, 60)
        return f"{minutos:02d}:{segundos:02d}"

    agg["Ritmo_min_decimal"] = _ritmo_to_minutos(agg["Ritmos"])
    agg["Ritmo_mmss"] = agg["Ritmo_min_decimal"].apply(minutos_a_mmss)
    agg["Fecha_str"] = agg["Fecha"].dt.strftime("%d-%m-%Y")

    # Calcular Tiempo total en minutos decimales
    agg["Tiempo_min_decimal"] = agg["Distancia_km"] * agg["Ritmo_min_decimal"]
    agg["Tiempo_mmss"] = agg["Tiempo_min_decimal"].apply(minutos_a_mmss)

    source = ColumnDataSource(agg)
    columns = [
        TableColumn(field="Fecha_str", title="Fecha"),
        TableColumn(field="Distancia_km", title="Distancia total (km)"),
        TableColumn(field="Ritmo_mmss", title="Ritmo Promedio (mm:ss)"),
        TableColumn(field="Tiempo_mmss", title="Tiempo (mm:ss)"),
    ]
    data_table = DataTable(source=source, columns=columns, width=680, height=360, index_position=None)

    agg_html = agg[["Fecha_str", "Distancia_km", "Ritmo_mmss", "Tiempo_mmss"]].rename(
        columns={
            "Fecha_str": "Fecha",
            "Distancia_km": "Distancia total (km)",
            "Ritmo_mmss": "Ritmo Promedio (mm:ss)",
            "Tiempo_mmss": "Tiempo (mm:ss)"
        }
    )

    html_str = agg_html.to_html(index=False, border=1)
    html_str = html_str.replace("<table", f'<table style="width:{PLOT_WIDTH}px;min-width:{PLOT_WIDTH}px;max-width:{PLOT_WIDTH}px"')

    return data_table, html_str


# ====================================================================
def tab_barras_lugares(df):
    if df.empty or "Lugar" not in df.columns or "Periodo" not in df.columns:
        return figure(title="No hay datos de lugares o periodos", plot_width=900, plot_height=500)

    df_group = df.groupby(["Lugar", "Periodo"]).size().reset_index(name="Conteo")

    periodos = sorted(df_group["Periodo"].unique())
    pivot = df_group.pivot(index="Lugar", columns="Periodo", values="Conteo").fillna(0)

    pivot["Total"] = pivot.sum(axis=1)
    pivot = pivot.sort_values("Total", ascending=True)
    lugares_ordenados = list(pivot.index)
    pivot = pivot.drop(columns="Total")

    colores = Category10[max(3, len(periodos))]

    # Calcular el máximo total de km de cualquier lugar (no suma de todos)
    max_km_lugar = pivot.sum(axis=1).max()
    x_range_max = max_km_lugar + 5  # Siempre 5 más

    # Usar altura dinámica con mínimo 500px
    height_px = max(500, 90 + 35 * len(lugares_ordenados))

    
    p = figure(
        y_range=lugares_ordenados,
        x_range=(0, x_range_max),
        x_axis_label="Kilómetros",
        y_axis_label="Lugar",
        title=None,
        plot_height=height_px,
        plot_width=PLOT_WIDTH,
        toolbar_location=None,
        tools=""
    )

    source_data = {"Lugar": lugares_ordenados}
    left_vals = [0] * len(lugares_ordenados)

    for i, periodo in enumerate(periodos):
        counts = list(pivot[periodo].values)
        right_vals = [left_vals[j] + counts[j] for j in range(len(counts))]

        source_data[f"left_{i}"] = left_vals
        source_data[f"right_{i}"] = right_vals

        left_vals = right_vals

    source = ColumnDataSource(source_data)

    for i, periodo in enumerate(periodos):
        p.hbar(
            y="Lugar", height=0.8,
            left=f"left_{i}", right=f"right_{i}",
            color=colores[i % len(colores)],
            legend_label=str(periodo),
            source=source
        )

    p.ygrid.grid_line_color = None
    p.legend.title = "Periodo"
    p.legend.location = "right"
    p.legend.orientation = "vertical"
    p.legend.background_fill_alpha = 0.0
    p.legend.border_line_alpha = 0.0
    p.legend.label_text_font_size = "10pt"
    p.min_border_right = 110

    return p


# ====================================================================
def tab_data_completo(df):
    
    if df.empty:
        return Div(text="<p><b>No hay datos disponibles.</b></p>")

    df_all = df.copy()
    _ensure_fecha_datetime(df_all, "Fecha")

    if "Fecha" in df_all.columns and pd.api.types.is_datetime64_any_dtype(df_all["Fecha"]):
        df_all["Fecha"] = df_all["Fecha"].dt.strftime("%d-%m-%Y")

    def formato_mmss(td):
        total_segundos = int(td.total_seconds())
        minutos, segundos = divmod(total_segundos, 60)
        return f"{minutos:02d}:{segundos:02d}"

    df_all["Ritmos_formateado"] = df_all["Ritmos"].apply(formato_mmss)

    columnas_mostrar = ["ID", "Lugar", "Fecha", "Distancia_km", "Ritmos_formateado", "Periodo"]
    columnas_validas = [col for col in columnas_mostrar if col in df_all.columns]

    columns = []
    for col in columnas_validas:
        if col == "Lugar":
            width = 200   # más ancho
        elif col == "ID":
            width = 40    # más angosto
        elif col == "Ritmos_formateado":
            width = 90
        elif col == "Distancia_km":
            width = 120
        else:
            width = 100
        title = "Ritmos (mm:ss)" if col == "Ritmos_formateado" else col
        if col == "Distancia_km":
            title = "Distancia (km)"
        columns.append(TableColumn(field=col, title=title, width=width))

    source = ColumnDataSource(df_all)
    return DataTable(source=source, columns=columns, width=950, height=500, index_position=None)

