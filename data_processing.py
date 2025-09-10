import pandas as pd
from PIL import Image
import streamlit as st

def mostrar_imagen_error(ruta_imagen):
    try:
        img = Image.open(ruta_imagen)
        st.image(img, caption="Formato esperado del archivo XLSX")
    except Exception as e:
        st.error(f"No se pudo mostrar la imagen de referencia: {e}")

def limpiar_datos(df_input):
    try:
        # Forzar nombres de columnas por posición
        columnas_forzadas = ["ID", "Lugar", "Fecha", "Distancia_km", "Ritmos", "Periodo"]

        # Verificar que el archivo tenga al menos 6 columnas
        if df_input.shape[1] != len(columnas_forzadas):
            raise ValueError(
                f"El archivo debe tener exactamente {len(columnas_forzadas)} columnas: "
                f"{', '.join(columnas_forzadas)}. "
                f"Se detectaron {df_input.shape[1]} columnas."
            )

        df = df_input.copy()
        df.columns = columnas_forzadas

        # Validar distancia (entero > 0)
        try:
            df["Distancia_km"] = df["Distancia_km"].astype(int)
            df = df[df["Distancia_km"] > 0]
        except Exception as e:
            raise ValueError(f"Error en columna 'Distancia_km'. Verifica que todas las filas sean números enteros positivos. Detalle: {e}")

        # Validar fecha
        errores_fecha = []
        for idx, valor in df["Fecha"].items():
            try:
                pd.to_datetime(valor, dayfirst=True, errors="raise")
            except Exception:
                errores_fecha.append((idx + 2, "Fecha", valor))  # +2 por encabezado en Excel
        if errores_fecha:
            fila, col, val = errores_fecha[0]
            raise ValueError(f"Error en fila {fila}, columna '{col}': valor inválido '{val}'. Formato esperado: dd\\/mm\\/yyyy (ej: 09/07/2025).")
        df["Fecha"] = pd.to_datetime(df["Fecha"], dayfirst=True)

        # Validar ritmos (mm:ss)
        errores_ritmos = []
        for idx, valor in df["Ritmos"].astype(str).items():
            try:
                pd.to_timedelta("00:" + valor)
            except Exception:
                errores_ritmos.append((idx + 2, "Ritmos", valor))
        if errores_ritmos:
            fila, col, val = errores_ritmos[0]
            raise ValueError(f"Error en fila {fila}, columna '{col}': valor inválido '{val}'. Formato esperado: mm\\:ss (ej: 04:32).")
        df["Ritmos"] = pd.to_timedelta("00:" + df["Ritmos"].astype(str))

        return df

    except Exception as e:
        st.error(f"⚠️ {e}")
        st.info("ℹ️ Corrige el archivo en Excel según el formato esperado y vuelve a cargar en Google Drive o corrige el archivo directamente en Google Drive.")
        mostrar_imagen_error("Referencia.png")
        st.stop()


