from backend import PavementProcessor
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageTk
import cv2

# Primera versión!!
class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Reconocimiento de pavimento")
        self.root.geometry("900x650")  # ventana más compacta
        self.ruta_video = None
        self.ruta_salida = None

        # Atributos adicionales para el control 
        self.var_min_inicio = tk.StringVar(value="0")
        self.var_min_fin = tk.StringVar(value="0")
        self.var_todo = tk.BooleanVar(value=False)
        self.var_estado = tk.StringVar(value="Listo")

        # Tamaño fijo del área de video
        #self.video_ancho = 400
        #self.video_alto = 225
        self.video_ancho = 600
        self.video_alto = 300
        
        
        # Construcción interfaz
        self.crear_interfaz()

    def crear_interfaz(self):
        # --- Parte superior (video de inferencia) ---
        frame_video = tk.Frame(self.root, bg="Green", bd=10, relief="solid")
        frame_video.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=20, pady=20)
        tk.Label(
        frame_video,
        text="Detección de irregularidad",
        font=("Georgi", 14, "bold"),  # Aumenta el tamaño de la fuente y usa negrita
        fg="white", 
        bg="#4CAF50", # Color de fondo del rectangulo en el que esta el label.
        relief="solid",#Borde al rededor del label.
        bd=2,  # Grosor del borde
        padx=20,  
        pady=10,  
        width=30,  
        height=2,  
        anchor="center",  
        justify="center" 
        ).pack(pady=10)
    
        # Contenedor fijo para el área de video
        contenedor_video = tk.Frame(
            frame_video, width=self.video_ancho, height=self.video_alto, bg="white",bd=3,relief="solid"
        )
        contenedor_video.pack(padx=10, pady=10)
        contenedor_video.pack_propagate(False)

        self.label_inferencia = tk.Label(contenedor_video, bg="white")
        self.label_inferencia.pack(fill=tk.BOTH, expand=True)

        # --- Parte inferior (controles + logos) ---
        frame_inferior = tk.Frame(self.root,bg="#4CAF50",padx=10, pady=10,bd=4,relief="solid")
        frame_inferior.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=10)

        # Controles a la izquierda
        frame_controles = tk.Frame(frame_inferior,bg="Green",bd=4,relief="solid")
        frame_controles.pack(side=tk.LEFT, fill=tk.X, expand=True,padx=10,pady=2)

        btn_cargar = tk.Button(
            frame_controles, text="Cargar video", width=15, command=self.cargar_video,bg="white",bd=3
        )
        btn_cargar.grid(row=0, column=2, columnspan=2, pady=5)

        btn_guardar = tk.Button(
            frame_controles, text="Guardar salida", width=15, command=self.guardar_salida,bg="white",bd=3
        )
        btn_guardar.grid(row=1, column=2, columnspan=2, pady=5)
        
        
        tk.Label(frame_controles, text="Min inicio:",bg="white",bd=3).grid(row=2, column=2, sticky="e",pady=2,)
        tk.Entry(frame_controles, textvariable=self.var_min_inicio, width=6,bg="white",bd=3).grid(
            row=2, column=3, sticky="w"
        )

        tk.Label(frame_controles, text="Min fin:",bg="white",bd=3).grid(row=3, column=2, sticky="e",pady=2)
        tk.Entry(frame_controles, textvariable=self.var_min_fin, width=6,bg="white",bd=3).grid(
            row=3, column=3, sticky="w"
        )

        tk.Checkbutton(
            frame_controles, text="Todo el video", variable=self.var_todo,bg="white",bd=3
        ).grid(row=4, column=2, columnspan=2, pady=5)

        btn_iniciar = tk.Button(
            frame_controles, text="Iniciar inferencia", width=18, command=self.iniciar,bg="white",bd=3
        )
        btn_iniciar.grid(row=5, column=2, columnspan=2, pady=2)

        self.label_estado = tk.Label(
            frame_controles, textvariable=self.var_estado, fg="blue", anchor="center",bg="Green",bd=3
        )
        self.label_estado.grid(row=6, column=2, columnspan=2, pady=2, sticky="we",padx=4)

        self.progress = ttk.Progressbar(
            frame_controles, orient="horizontal", length=300, mode="determinate",
        )
        self.progress.grid(row=7, column=2, columnspan=2, pady=7,padx=4)
        
        #Informacion de conteo!!!
        # Simplemente colocar los widgets en columnas más altas para moverlos a la derecha
        tk.Label(frame_controles, text="sdasdad:", bg="white", bd=3).grid(
            row=3, column=32, pady=2, sticky='e', padx=10  # Alineamos a la derecha en la columna 5
        )
        
        tk.Entry(frame_controles, textvariable=self.var_min_fin, width=6, bg="white", bd=3).grid(
            row=3, column=31, pady=2, sticky='e', padx=10  # Alineamos a la derecha en la columna 6
        )




        # Logos a la derecha
        frame_logos = tk.Frame(frame_inferior)
        frame_logos.pack(side=tk.RIGHT, padx=10)
       
        
        
        try:
            img1 = Image.open(r"C:\Users\jose1\OneDrive\Documentos\interfaz_mejoradas\gepar.png")
            img2 = Image.open(r"C:\Users\jose1\OneDrive\Documentos\interfaz_mejoradas\intertelco.png")

            # Reducir al 25% del tamaño original
            w1, h1 = img1.size
            w2, h2 = img2.size
            img1 = img1.resize((w1 // 4, h1 // 4))
            img2 = img2.resize((w2 // 4, h2 // 4))

            self.logo1 = ImageTk.PhotoImage(img1)
            self.logo2 = ImageTk.PhotoImage(img2)

            tk.Label(frame_logos, image=self.logo1).pack(side=tk.LEFT, padx=5)
            tk.Label(frame_logos, image=self.logo2).pack(side=tk.LEFT, padx=5)
        except Exception as e:
            print("Error cargando imágenes:", e)

    def cargar_video(self):
        ruta = filedialog.askopenfilename(
            title="Seleccionar video",
            filetypes=[
                ("Archivos de video", "*.mp4 *.avi *.mov"),
                ("Todos los archivos", "*.*"),
            ],
        )
        if ruta:
            self.ruta_video = ruta
            self.var_estado.set(f"Video cargado: {ruta}")
        else:
            self.var_estado.set("No se seleccionó video")

    def guardar_salida(self):
        ruta = filedialog.asksaveasfilename(
            title="Guardar video procesado",
            defaultextension=".mp4",
            filetypes=[
                ("Video MP4", "*.mp4"),
                ("Video AVI", "*.avi"),
                ("Todos los archivos", "*.*"),
            ],
        )
        if ruta:
            self.ruta_salida = ruta
            self.var_estado.set(f"Salida: {ruta}")
        else:
            self.var_estado.set("No se seleccionó ruta de salida")

    def iniciar(self):
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
                self.var_estado.set(f"✅ Video procesado en: {salida}")
                messagebox.showinfo("Finalizado", f"Video procesado en:\n{salida}")

            self.root.after(0, finalizar)

        threading.Thread(target=worker, daemon=True).start()

    def mostrar_frame(self, frame_inferido, porcentaje):
        def _update():
            frame_rgb = cv2.cvtColor(frame_inferido, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(frame_rgb)

            # Redimensionar siempre al tamaño fijo
            img = img.resize((self.video_ancho, self.video_alto))

            img_tk = ImageTk.PhotoImage(img)
            self.label_inferencia.configure(image=img_tk)
            self.label_inferencia.image = img_tk

            self.progress["value"] = porcentaje
            self.var_estado.set(f"Progreso: {porcentaje:.1f}%")

        self.root.after(0, _update)


if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()





