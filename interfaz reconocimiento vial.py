'''
-----------------------------------------------------------------------------------------------------------------------------------------------
-------------------------------------------------------- Grupo de investigación GEPAR ---------------------------------------------------------
------------------------------------------------------------- Universidad de Antioquia ---------------------------------------------------------
------------------------------------------------------------- Medellín, Colombia --------------------------------------------------------------
---------------------------------------------------------------- Septiembre, 2025 --------------------------------------------------------------
-----------------------------------------------------------------------------------------------------------------------------------------------
---------------------------------------------- Autor: * Jose Andres Henao Alzate --------------------------------------------------------------
-----------------------------------------------------------------------------------------------------------------------------------------------
--------- Proyecto: Detección de imperfecciones en pavimento utilizando técnicas de procesamiento digital de imágenes -------------------------
--------- y aprendizaje automático. -----------------------------------------------------------------------------------------------------------
-----------------------------------------------------------------------------------------------------------------------------------------------
--------- Descripción: ----------------------------------------------------------------------------------- ------------------------------------
Este módulo implementa la interfaz gráfica de usuario (GUI) desarrollada en Tkinter para el software de 
detección de imperfecciones en pavimento (grietas, piel de cocodrilo y baches). 

La interfaz permite:
    - Cargar videos.
    - Seleccionar intervalos de análisis o procesar el video completo.
    - Ejecutar el procesamiento mediante el backend con el modelo YOLOv8.
    - Mostrar resultados de conteo en tiempo real de cada categoría.
    - Guardar la salida procesada en un archivo de video.
    - Visualizar logos del grupo de investigación.

El backend genera un archivo Excel con los resultados detallados.
-----------------------------------------------------------------------------------------------------------------------------------------------
'''

from backend import PavementProcessor
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageTk
import cv2
#import pandas as pd


class App:
    '''
    Clase principal que gestiona la interfaz gráfica de usuario para la detección de imperfecciones 
    en pavimento.

    Atributos:
        root (tk.Tk): Ventana principal de Tkinter.
        ruta_video (str): Ruta al archivo de video cargado.
        ruta_salida (str): Ruta al archivo de salida del video procesado.
        var_min_inicio (tk.StringVar): Minuto de inicio del análisis.
        var_min_fin (tk.StringVar): Minuto de finalización del análisis.
        var_todo (tk.BooleanVar): Indica si se procesa todo el video.
        var_estado (tk.StringVar): Estado actual de la aplicación.
        video_ancho (int): Ancho del área de visualización de video.
        video_alto (int): Alto del área de visualización de video.
        cant_huecos (tk.StringVar): Conteo de baches detectados.
        cant_grietas (tk.StringVar): Conteo de grietas detectadas.
        cant_Pcocodrilo (tk.StringVar): Conteo de piel de cocodrilo detectada.
    '''
    def __init__(self, root):
        '''
        Constructor de la clase App. Inicializa la ventana principal y configura variables de estado.
        
        Args:
            root (tk.Tk): Objeto de la ventana principal de Tkinter.
        '''
        self.root = root
        self.root.title("CRACKFINDER 	Detección Inteligente de irregularidades en pavimento")
        self.root.geometry("1100x750")
        self.root.resizable(False, False)
        self.root.maxsize(1100, 750)
        self.root.minsize(1100, 750)

        self.ruta_video = None
        self.ruta_salida = None

        self.var_min_inicio = tk.StringVar(value="0")
        self.var_min_fin = tk.StringVar(value="0")
        self.var_todo = tk.BooleanVar(value=False)
        self.var_estado = tk.StringVar(value="Listo")

        self.video_ancho = 600
        self.video_alto = 300
        
        self.cant_huecos = tk.StringVar(value="0")
        self.cant_grietas = tk.StringVar(value="0")
        self.cant_Pcocodrilo = tk.StringVar(value="0")

        self.crear_interfaz()

    def crear_interfaz(self):
        '''
        Construye todos los elementos gráficos de la interfaz:
            - Área de visualización del video.
            - Botones de control (cargar, guardar, iniciar).
            - Parámetros de tiempo de análisis.
            - Barra de progreso.
            - Área de conteo de resultados.
            - Logos institucionales.
        '''
        frame_video = tk.Frame(self.root, bg="Green", bd=10, relief="solid")
        frame_video.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=20, pady=20)
        tk.Label(
            frame_video,
            text="CRACKFINDER Detección Inteligente de irregularidades en pavimento",
            font=("Georgi", 14, "bold"),
            fg="white",
            bg="#4CAF50",
            relief="solid",
            bd=2,
            padx=20,
            pady=10,
            width=60,
            height=2,
            anchor="center",
            justify="center"
        ).pack(pady=10)


        
        
        contenedor_video_normal = tk.Frame(
            frame_video, width=self.video_ancho-90, height=self.video_alto, bg="white", bd=3, relief="solid"
        )
        contenedor_video_normal.pack(side=tk.LEFT, padx=10, pady=10)
        contenedor_video_normal.pack_propagate(False)
        
        self.label_imagen_normal = tk.Label(contenedor_video_normal, bg="white")
        self.label_imagen_normal.pack(fill=tk.BOTH, expand=True)
        
        
        contenedor_video_inferencia = tk.Frame(
            frame_video, width=self.video_ancho, height=self.video_alto, bg="white", bd=3, relief="solid"
        )
        contenedor_video_inferencia.pack(side=tk.LEFT, padx=10, pady=10)
        contenedor_video_inferencia.pack_propagate(False)
        
        self.label_inferencia = tk.Label(contenedor_video_inferencia, bg="white")
        self.label_inferencia.pack(fill=tk.BOTH, expand=True)
        
        
                
                        
        
        

        frame_inferior = tk.Frame(self.root, bg="#4CAF50", padx=10, pady=10, bd=4, relief="solid")
        frame_inferior.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=10)

        frame_controles = tk.Frame(frame_inferior, bg="Green", bd=4, relief="solid")
        frame_controles.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10, pady=2)

        frame_botones = tk.Frame(frame_controles, bg="Green")
        frame_botones.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        frame_informacion = tk.Frame(frame_controles, bg="Green", bd=3, relief="solid")
        frame_informacion.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Botones principales
        btn_cargar = tk.Button(
            frame_botones, text="Cargar video", width=15, command=self.cargar_video, bg="white", bd=3
        )
        btn_cargar.grid(row=0, column=3, columnspan=2, pady=5)

        btn_guardar = tk.Button(
            frame_botones, text="Guardar salida", width=15, command=self.guardar_salida, bg="white", bd=3
        )
        btn_guardar.grid(row=1, column=3, columnspan=2, pady=5)

        # Parámetros de tiempo
        tk.Label(frame_botones, text="Min inicio:", bg="white", bd=3).grid(row=2, column=3, sticky="e", pady=2)
        tk.Entry(frame_botones, textvariable=self.var_min_inicio, width=6, bg="white", bd=3).grid(
            row=2, column=4, sticky="w"
        )

        tk.Label(frame_botones, text="Min fin:", bg="white", bd=3).grid(row=3, column=3, sticky="e", pady=2)
        tk.Entry(frame_botones, textvariable=self.var_min_fin, width=6, bg="white", bd=3).grid(
            row=3, column=4, sticky="w"
        )

        tk.Checkbutton(
            frame_botones, text="Todo el video", variable=self.var_todo, bg="white", bd=3
        ).grid(row=4, column=3, columnspan=2, pady=5)

        btn_iniciar = tk.Button(
            frame_botones, text="Iniciar inferencia", width=18, command=self.iniciar, bg="white", bd=3
        )
        btn_iniciar.grid(row=5, column=3, columnspan=2, pady=2)

        # Barra de progreso
        self.progress = ttk.Progressbar(
            frame_botones, orient="horizontal", length=300, mode="determinate",
        )
        self.progress.grid(row=7, column=3, columnspan=2, pady=2, padx=4)

        # Panel de información de resultados
        frame_informacion.grid_columnconfigure(0, weight=1)
        frame_informacion.grid_columnconfigure(1, weight=1)

        tk.Label(frame_informacion, text="Informacion", bg="white", anchor="center").grid(
            row=0, column=0, columnspan=2, pady=10, sticky="we"
        )

        tk.Label(frame_informacion, text="Cant huecos:", bg="white", bd=3).grid(
            row=1, column=0, sticky="e", pady=5, padx=10
        )
        tk.Entry(frame_informacion, textvariable=self.cant_huecos, width=6, bg="white", bd=3).grid(
            row=1, column=1, sticky="w", pady=5, padx=10
        )

        tk.Label(frame_informacion, text="Cant grietas:", bg="white", bd=3).grid(
            row=3, column=0, sticky="e", pady=5, padx=10
        )
        tk.Entry(frame_informacion, textvariable=self.cant_grietas, width=6, bg="white", bd=3).grid(
            row=3, column=1, sticky="w", pady=5, padx=10
        )

        tk.Label(frame_informacion, text="Cant P.cocodr:", bg="white", bd=3).grid(
            row=4, column=0, sticky="e", pady=5, padx=10
        )
        tk.Entry(frame_informacion, textvariable=self.cant_Pcocodrilo, width=6, bg="white", bd=3).grid(
            row=4, column=1, sticky="w", pady=5, padx=10
        )

        tk.Label(frame_informacion, text="  ", bg="white", anchor="center").grid(
            row=5, column=0, columnspan=2, pady=10, sticky="we"
        )

        self.label_estado = tk.Label(
            frame_informacion, textvariable=self.var_estado, fg="white", anchor="center", bg="Green", bd=3
        )
        self.label_estado.grid(row=7, column=0, columnspan=2, pady=2, sticky="we", padx=4)

        # Logos institucionales
        frame_logos = tk.Frame(frame_inferior)
        frame_logos.pack(side=tk.RIGHT, padx=10)

        try:
            img1 = Image.open(r"C:\Users\jose1\OneDrive\Documentos\interfaz_mejoradas\gepar.png")
            img2 = Image.open(r"C:\Users\jose1\OneDrive\Documentos\interfaz_mejoradas\intertelco.png")

            img1 = img1.resize((img1.size[0] // 4, img1.size[1] // 4))
            img2 = img2.resize((img2.size[0] // 4, img2.size[1] // 4))

            self.logo1 = ImageTk.PhotoImage(img1)
            self.logo2 = ImageTk.PhotoImage(img2)

            tk.Label(frame_logos, image=self.logo1).pack(side=tk.LEFT, padx=5)
            tk.Label(frame_logos, image=self.logo2).pack(side=tk.LEFT, padx=5)
        except Exception as e:
            print("Error cargando imágenes:", e)

    def cargar_video(self):
        '''
        Abre un cuadro de diálogo para seleccionar un archivo de video 
        y actualiza la variable de estado.
        '''
        ruta = filedialog.askopenfilename(
            title="Seleccionar video",
            filetypes=[("Archivos de video", "*.mp4 *.avi *.mov"), ("Todos los archivos", "*.*")]
        )
        if ruta:
            self.ruta_video = ruta
            self.var_estado.set(f"Video cargado: {ruta}")
        else:
            self.var_estado.set("No se seleccionó video")

    def guardar_salida(self):
        '''
        Abre un cuadro de diálogo para seleccionar la ruta de guardado 
        del video procesado.
        '''
        ruta = filedialog.asksaveasfilename(
            title="Guardar video procesado",
            defaultextension=".mp4",
            filetypes=[("Video MP4", "*.mp4"), ("Video AVI", "*.avi"), ("Todos los archivos", "*.*")]
        )
        if ruta:
            self.ruta_salida = ruta
            self.var_estado.set(f"Salida: {ruta}")
        else:
            self.var_estado.set("No se seleccionó ruta de salida")

    def iniciar(self):
        '''
        Inicia el procesamiento del video cargado en un hilo separado.
        Verifica parámetros de entrada, ejecuta el backend y muestra el progreso en la interfaz.
        '''
        if not self.ruta_video:
            messagebox.showwarning("Aviso", "Primero carga un video.")
            return
        if not self.ruta_salida:
            messagebox.showwarning("Aviso", "Selecciona la ruta de salida.")
            return

        ini = int(self.var_min_inicio.get())
        fin = int(self.var_min_fin.get())
        todo = self.var_todo.get()

        self.var_estado.set("Ejecutando inferencia...")
        self.progress["value"] = 0
        self.root.update_idletasks()

        def worker():
            procesador = PavementProcessor()
            salida = procesador.procesar_video(
                video_path=self.ruta_video,
                output_path=self.ruta_salida,
                inicio_min=ini,
                fin_min=fin,
                todo=todo,
                callback=self.mostrar_frame,
            )

            def finalizar():
                self.var_estado.set(f" Video procesado en: {salida}")
                messagebox.showinfo("Finalizado", f"Video procesado en:\n{salida}")

                # Guardar los resultados en un archivo Excel al finalizar el procesamiento.
                self.guardar_resultados_excel()

            self.root.after(0, finalizar)

        threading.Thread(target=worker, daemon=True).start()
    
    def mostrar_frame(self, frame_inferido, frame_normal, porcentaje, counts):
        '''
        Actualiza el área de video y las métricas de detección en la interfaz.
    
        Args:
            frame_inferido (ndarray): Frame del video procesado.
            frame_normal (ndarray): Frame del video normal (sin inferencias).
            porcentaje (float): Progreso del procesamiento (%).
            counts (dict): Conteo de objetos detectados por clase.
        '''
        def _update():
            # Mostrar el frame normal
            frame_rgb_normal = cv2.cvtColor(frame_normal, cv2.COLOR_BGR2RGB)
            img_normal = Image.fromarray(frame_rgb_normal)
            img_normal = img_normal.resize((self.video_ancho, self.video_alto))
            img_tk_normal = ImageTk.PhotoImage(img_normal)
            self.label_imagen_normal.configure(image=img_tk_normal)
            self.label_imagen_normal.image = img_tk_normal  # Asegúrate de mantener la referencia
    
            # Mostrar el frame inferido (con detecciones)
            frame_rgb_inferido = cv2.cvtColor(frame_inferido, cv2.COLOR_BGR2RGB)
            img_inferido = Image.fromarray(frame_rgb_inferido)
            img_inferido = img_inferido.resize((self.video_ancho, self.video_alto))
            img_tk_inferido = ImageTk.PhotoImage(img_inferido)
            self.label_inferencia.configure(image=img_tk_inferido)
            self.label_inferencia.image = img_tk_inferido  # Asegúrate de mantener la referencia
    
            # Actualización de progreso
            self.progress["value"] = porcentaje
            self.var_estado.set(f"Progreso: {porcentaje:.1f}%")
    
            # Actualización de conteos
            self.cant_huecos.set(str(counts.get(0, 0)))       # Pothole
            self.cant_Pcocodrilo.set(str(counts.get(1, 0)))   # Cocodrile skin
            self.cant_grietas.set(str(counts.get(2, 0)))      # Crack
    
        self.root.after(0, _update)
    

    def on_closing(self):
        '''
        Evento ejecutado cuando el usuario cierra la ventana manualmente.
        '''
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)  # Guardar resultados al cerrar
    root.mainloop()








