import re
import requests
import pandas as pd
from io import BytesIO
import streamlit as st

def leer_url_xlsx(url):
    # Extrae el ID del archivo desde la URL de Google Drive
    patron = r"/d/([a-zA-Z0-9_-]+)"
    coincidencia = re.search(patron, url)

    if coincidencia:
        id_archivo = coincidencia.group(1)
        # Construye URL de descarga directa
        url_descarga = f"https://drive.google.com/uc?export=download&id={id_archivo}"

        try:
            respuesta = requests.get(url_descarga)
            respuesta.raise_for_status()  # Para errores HTTP

            archivo_binario = BytesIO(respuesta.content)
            df_inicial = pd.read_excel(archivo_binario, engine='openpyxl')
            return df_inicial

        except Exception as e:
            st.error(f"❌ Error al leer el archivo XLSX desde la URL: {e}")
            st.stop()
    else:
        st.error("❌ La URL proporcionada no es válida o no contiene un ID de archivo de Google Drive.")
        st.stop()


