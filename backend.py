'''
-----------------------------------------------------------------------------------------------------------------------------------------------
-------------------------------------------------------- Grupo de investigación Gepar ---------------------------------------------------------
----------------------------------------------------------- Universidad de Antioquia ----------------------------------------------------------
------------------------------------------------------------- Medellín, Colombia --------------------------------------------------------------
---------------------------------------------------------------- Septiembre, 2025 --------------------------------------------------------------
-----------------------------------------------------------------------------------------------------------------------------------------------
-------------------------------------------------------------- Autor: Jose Andres Henao Alzate ------------------------------------------------
-----------------------------------------------------------------------------------------------------------------------------------------------
------------- Proyecto: Detección de imperfecciones en pavimento utilizando técnicas de procesamiento digital de imágenes y --------------------
------------- aprendizaje automático -----------------------------------------------------------------------------------------------------------
-----------------------------------------------------------------------------------------------------------------------------------------------
------------- Descripción: Este software permite detectar imperfecciones en pavimento (grietas, piel de cocodrilo y baches). ------------------
------------- Realiza un conteo de las imperfecciones detectadas y las guarda en un archivo Excel junto con el minuto y segundo ----------------
------------- en el que se presentan dentro de un video vial. Además, genera un video de salida con los resultados de inferencia. ----------------
------------- El backend utiliza como base el modelo YOLOv8 para la detección de objetos. ------------------------------------------------------
-----------------------------------------------------------------------------------------------------------------------------------------------
'''

import os
import pandas as pd
import cv2
import numpy as np
from ultralytics import YOLO
from skimage import img_as_float
from scipy.ndimage import gaussian_filter
import atexit

# --- Función de preprocesado ---
def imflatfield(image, sigma=40):
    '''
    Aplica corrección de campo plano (flat-field correction) para mejorar la uniformidad de la iluminación
    en la imagen, reduciendo la influencia de variaciones de fondo.

    Parámetros:
        image (np.ndarray): Imagen de entrada (BGR).
        sigma (int): Parámetro de suavizado Gaussiano para estimar el fondo.

    Retorna:
        np.ndarray: Imagen corregida con valores en rango [0, 255].
    '''
    if image.dtype != np.float32:
        image = img_as_float(image)
    corrected = np.zeros_like(image)
    for c in range(3):  # RGB
        fondo = gaussian_filter(image[:, :, c], sigma=sigma)
        corrected[:, :, c] = np.clip((image[:, :, c] - fondo) + np.mean(fondo), 0, 1)
    return (corrected * 255).astype(np.uint8)


class PavementProcessor:
    '''
    Clase para procesar videos de pavimento, detectar imperfecciones con YOLOv8
    y guardar los resultados en un archivo Excel y un video de salida.

    Atributos:
        model (YOLO): Modelo cargado de YOLOv8.
        resultados_inferencia (list): Lista que almacena resultados detectados (minuto, segundo, conteo).
        ruta_excel (str): Ruta del archivo Excel donde se guardarán los resultados.
        df_writer (pd.DataFrame): DataFrame que mantiene resultados acumulados en memoria.
        excel_writer: Escritor de Excel (pandas) para exportar datos.
    '''

    def __init__(self, model_path=r"C:\Users\jose1\OneDrive\Documentos\interfaz_mejoradas\best.pt"):
        '''
        Constructor de la clase PavementProcessor.

        Parámetros:
            model_path (str): Ruta al archivo del modelo YOLO entrenado.
        '''
        self.model = YOLO(model_path)
        self.resultados_inferencia = []  # Mantener los resultados en memoria
        self.ruta_excel = os.path.join(os.getcwd(), "resultados_de_inferencia.xlsx")  # Usar el directorio actual
        self.df_writer = None  # El escritor de pandas para Excel
        self.excel_writer = None  # El writer para pandas, que se mantiene abierto
        # Registrar función de cierre para guardar los resultados si el programa se cierra inesperadamente
        atexit.register(self.guardar_resultados_excel)

    def procesar_video(self, video_path, output_path, inicio_min=0, fin_min=0, todo=True, callback=None):
        """
        Procesa un video con YOLOv8 y guarda los resultados en video y Excel.

        Parámetros:
            video_path (str): Ruta del video de entrada.
            output_path (str): Ruta del video de salida con inferencias dibujadas.
            inicio_min (int): Minuto de inicio de análisis.
            fin_min (int): Minuto final de análisis.
            todo (bool): Si True, procesa todo el video. Si False, procesa solo el intervalo.
            callback (function): Función de retorno para actualizar interfaz (frame, progreso, conteos).

        Retorna:
            str: Ruta del video de salida generado.
        """
        cap = cv2.VideoCapture(video_path)
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        # Salida del video
        out = cv2.VideoWriter(
            output_path, cv2.VideoWriter_fourcc(*'mp4v'), fps, (width, height)
        )

        # Intervalo de tiempo
        if todo:
            inicio = 0
            fin = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        else:
            inicio = int(inicio_min * 60 * fps)
            fin = int(fin_min * 60 * fps)
        cap.set(cv2.CAP_PROP_POS_FRAMES, inicio)

        procesados = 0
        total_frames = max(1, fin - inicio)
        frame_count = 0
        ultimo_frame_inferido = None
        counts = {0: 0, 1: 0, 2: 0}  # Inicial para callback en caso de que no infiera aún

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret or cap.get(cv2.CAP_PROP_POS_FRAMES) > fin:
                break

            frame_count += 1

            # Inferencia cada 20 frames
            if frame_count % 20 == 0:
                frame_proc = imflatfield(frame)
                results = self.model(frame_proc)
                result = results[0]

                # --- Contar clases ---
                counts = {0: 0, 1: 0, 2: 0}  # Pothole, cocodrile skin, crack
                if result.boxes is not None:
                    for cls_id in result.boxes.cls:
                        cls_int = int(cls_id)
                        if cls_int in counts:
                            counts[cls_int] += 1

                # Dibujar resultados
                ultimo_frame_inferido = result.plot()

                # Actualizar interfaz
                procesados += 1
                progreso = (procesados / total_frames) * 100
                if callback:
                    callback(ultimo_frame_inferido, progreso, counts)

                # Si hay resultado, agregarlo a la lista de resultados de inferencia
                if sum(counts.values()) > 0:  # Solo guardar si hay alguna detección
                    tiempo_seg = int(cap.get(cv2.CAP_PROP_POS_MSEC) / 1000)
                    minuto = tiempo_seg // 60
                    segundo = tiempo_seg % 60
                    self.resultados_inferencia.append({
                        "Minuto": minuto,
                        "Segundo": segundo,
                        "Huecos": counts[0],
                        "Grietas": counts[2],
                        "Piel de cocodrilo": counts[1],
                    })

                    # Escribir los resultados directamente en el archivo Excel
                    self.escribir_resultado_excel(minuto, segundo, counts)

            # Si hay resultado, se escribe en el video
            if ultimo_frame_inferido is not None:
                out.write(ultimo_frame_inferido)

        cap.release()
        out.release()

        # Al finalizar, guardar los resultados si no se ha cerrado el programa inesperadamente
        if self.resultados_inferencia:
            self.guardar_resultados_excel()

        return output_path

    def escribir_resultado_excel(self, minuto, segundo, counts):
        """
        Escribe un nuevo resultado en el archivo Excel de manera eficiente,
        sin cerrar el archivo repetidamente.

        Parámetros:
            minuto (int): Minuto en el que ocurre la detección.
            segundo (int): Segundo en el que ocurre la detección.
            counts (dict): Diccionario con los conteos de cada clase detectada.
        """
        # Si el DataFrame no está inicializado, crearlo
        if self.df_writer is None:
            self.iniciar_excel_writer()

        # Crear un DataFrame para la nueva fila
        nueva_fila = pd.DataFrame([{
            "Minuto": minuto,
            "Segundo": segundo,
            "Huecos": counts[0],
            "Grietas": counts[2],
            "Piel de cocodrilo": counts[1]
        }])

        # Usar pd.concat() para agregar la nueva fila al DataFrame
        self.df_writer = pd.concat([self.df_writer, nueva_fila], ignore_index=True)

        # Usar ExcelWriter para escribir el DataFrame al archivo sin sobreescribir
        with pd.ExcelWriter(self.ruta_excel, engine="openpyxl", mode="a", if_sheet_exists="overlay") as writer:
            self.df_writer.to_excel(writer, index=False, header=False, startrow=self.df_writer.shape[0])

    def iniciar_excel_writer(self):
        """
        Inicializa el archivo Excel si no existe y configura el escritor de pandas.
        También crea el DataFrame inicial en memoria.
        """
        # Asegurarse de que el directorio de la ruta del archivo existe
        os.makedirs(os.path.dirname(self.ruta_excel), exist_ok=True)

        # Si el archivo no existe, crear uno nuevo con los encabezados
        if not os.path.exists(self.ruta_excel):
            df = pd.DataFrame(columns=["Minuto", "Segundo", "Huecos", "Grietas", "Piel de cocodrilo"])
            df.to_excel(self.ruta_excel, index=False)

        # Inicializar el DataFrame en memoria
        self.df_writer = pd.read_excel(self.ruta_excel)

    def guardar_resultados_excel(self):
        """
        Guarda los resultados acumulados en el archivo Excel.
        Si el archivo ya existe, sobreescribe los datos con los nuevos resultados.
        """
        if not self.resultados_inferencia:
            return  # No hay resultados que guardar

        # Al finalizar, guardar los resultados en el archivo Excel
        self.df_writer.to_excel(self.ruta_excel, index=False)
