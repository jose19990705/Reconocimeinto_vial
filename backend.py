"""
Backend para detección de irregularidades en pavimento
Autor: Jose Henao Alzate
"""
"Primera verisón."

#Backend segunda versión

import cv2
import numpy as np
from ultralytics import YOLO
from skimage import img_as_float
from scipy.ndimage import gaussian_filter


# --- Función de preprocesado ---
def imflatfield(image, sigma=40):
    if image.dtype != np.float32:
        image = img_as_float(image)
    corrected = np.zeros_like(image)
    for c in range(3):  # RGB
        fondo = gaussian_filter(image[:, :, c], sigma=sigma)
        corrected[:, :, c] = np.clip((image[:, :, c] - fondo) + np.mean(fondo), 0, 1)
    return (corrected * 255).astype(np.uint8)


class PavementProcessor:
    def __init__(self, model_path=r"C:\Users\jose1\OneDrive\Documentos\interfaz_mejoradas\best.pt"):
        self.model = YOLO(model_path)

    def procesar_video(self, video_path, output_path, inicio_min=0, fin_min=0, todo=True, callback=None):
        """
        Procesa un video con YOLOv8.
        - video_path: ruta del video de entrada
        - output_path: ruta del video de salida
        - inicio_min, fin_min: intervalo de tiempo en minutos
        - todo: si True, procesa todo el video
        - callback: función(frame_inferido, progreso, counts)
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

            # Si hay resultado, se escribe en el video
            if ultimo_frame_inferido is not None:
                out.write(ultimo_frame_inferido)

        cap.release()
        out.release()
        return output_path
