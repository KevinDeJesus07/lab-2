# -*- coding: utf-8 -*-
"""
Cine Cultural Barranquilla - Sistema de Gestión y Reservas v1.0

Descripción:
Interfaz gráfica (GUI) construida con ttkbootstrap para la gestión de un cine.
Permite visualizar funciones programadas filtradas por fecha, película y sala.
Ofrece selección interactiva de asientos en un layout realista y simula la
compra de tiquetes, validando datos del cliente. Las reservas de asientos
se guardan en 'tickets.txt' para persistencia básica entre sesiones.

Desarrollo:
- Python 3.x
- Bibliotecas requeridas:
  pip install Pillow ttkbootstrap tkcalendar
- Archivos necesarios (mismo directorio):
  - movies.txt: Datos de funciones (Formato: DD/MM/YYYY - HH:MM;Película;Género;Sala)
  - tickets.txt: (Se crea automáticamente) Guarda las reservas.
  - seat_available.png: Imagen asiento disponible (40x40, fondo opaco #FFFFFF RECOMENDADO).
  - seat_occupied.png: Imagen asiento ocupado (40x40, fondo opaco #FFFFFF RECOMENDADO).
  - seat_selected.png: Imagen asiento seleccionado (40x40, fondo opaco #FFFFFF RECOMENDADO).

Autores:
    - Kevin De Jesús Romero Incer
    - Mateo
    - Alfredo
    (Adaptado y Refinado por Asistente AI)

Fecha: 2025-05-02
"""

import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import * # Constantes para bootstyles
from tkinter import messagebox, simpledialog
from datetime import datetime, timedelta, date
from typing import List, Optional, Dict, Tuple
from PIL import Image, ImageTk  # Necesita 'pip install Pillow'
import copy
import os
import re # Para validación de nombre

# --- Constantes Globales ---
APP_TITLE = "Cine Cultural Barranquilla - Taquilla v1.0"
WINDOW_GEOMETRY = "1280x768"
# --- IMPORTANTE: Color de fondo para área de asientos y para fondo de imágenes ---
COLOR_FONDO_ASIENTOS = '#FFFFFF' # Blanco (coincide con tema 'flatly')

# Archivos
MOVIE_DATA_FILE = 'movies.txt'
TICKET_DATA_FILE = 'tickets.txt'

# Configuración Teatro/Asientos
DEFAULT_SEATS_PER_THEATER = 80
DEFAULT_THEATER_NAMES = ['Sala 1', 'Sala 2', 'Sala 3']

# Imágenes (RECOMENDADO: Editar para tener fondo opaco COLOR_FONDO_ASIENTOS)
SEAT_IMG_AVAILABLE = "seat_available.png"
SEAT_IMG_OCCUPIED = "seat_occupied.png"
SEAT_IMG_SELECTED = "seat_selected.png"
SEAT_IMG_WIDTH = 40
SEAT_IMG_HEIGHT = 40

# Otros
PRECIO_TIQUETE = 15000 # Precio base por tiquete (COP)
# Formatos de Fecha/Hora
DATE_FORMAT_FILE = '%d/%m/%Y - %H:%M'     # Formato en archivos movies.txt/tickets.txt
DATE_FORMAT_DISPLAY_FULL = '%d/%m/%Y %H:%M' # Para mostrar fecha y hora completa
DATE_FORMAT_DISPLAY_DATE = '%d/%m/%Y'     # Para mostrar/parsear solo fecha
DATE_FORMAT_DISPLAY_TIME = '%H:%M'     # Para mostrar solo hora
DATE_FORMAT_DATEENTRY = DATE_FORMAT_DISPLAY_DATE # Formato que usa ttk.DateEntry


# --- Función Auxiliar para Centrar Ventanas ---
def center_window(window: tk.Misc, width: int, height: int) -> None:
    """Calcula y aplica geometría para centrar una ventana Tk o Toplevel."""
    try:
        window.update_idletasks() # Asegurar que winfo esté actualizado
        screen_width = window.winfo_screenwidth()
        screen_height = window.winfo_screenheight()
        x = (screen_width / 2) - (width / 2)
        y = (screen_height / 2) - (height / 2)
        window.geometry(f'{width}x{height}+{int(x)}+{int(y)}')
        # print(f"Ventana centrada: {width}x{height} en ({int(x)},{int(y)})") # Log opcional
    except Exception as e:
        print(f"Advertencia: No se pudo centrar ventana ({e}). Usando tamaño {width}x{height}.")
        window.geometry(f'{width}x{height}')


# --- Clases de Modelo de Datos ---

class Asiento:
    """Representa un único asiento con ID y estado de disponibilidad."""
    def __init__(self, id_asiento: str):
        self.id = id_asiento
        self.disponible = True

    def está_disponible(self) -> bool: return self.disponible
    def reservar(self) -> None: self.disponible = False
    def desreservar(self) -> None: self.disponible = True
    def __str__(self) -> str: return f"Asiento({self.id}, {'Disp' if self.disponible else 'Ocup'})"
    def __repr__(self) -> str: return f"Asiento(id='{self.id}')"

class Teatro:
    """Representa una plantilla de sala con una lista de asientos base."""
    def __init__(self, nombre: str, cantidad_asientos: int = DEFAULT_SEATS_PER_THEATER):
        self.nombre = nombre
        self.asientos: List[Asiento] = self._generar_asientos(cantidad_asientos)

    def _generar_asientos(self, cantidad: int) -> List[Asiento]:
        """Genera IDs básicos A1..J8 (privado)."""
        asientos_generados = []
        filas = "ABCDEFGHIJ"
        if cantidad <= 0 or not filas: return []
        asientos_por_fila = max(1, cantidad // len(filas))
        count = 0
        for fila in filas:
            for num in range(1, asientos_por_fila + 1):
                if count < cantidad:
                    asientos_generados.append(Asiento(f"{fila}{num}")); count += 1
                else: break
            if count >= cantidad: break
        while len(asientos_generados) < cantidad:
             asientos_generados.append(Asiento(f"Extra{len(asientos_generados)+1}"))
        return asientos_generados

    def obtener_asiento_por_id(self, id_asiento: str) -> Optional[Asiento]:
        for asiento in self.asientos:
            if asiento.id == id_asiento: return asiento
        return None

    def __str__(self) -> str: return f"Teatro({self.nombre})"

class Pelicula:
    """Representa una película."""
    def __init__(self, nombre: str, genero: str):
        self.nombre = nombre; self.genero = genero
    def __str__(self) -> str: return f"{self.nombre} ({self.genero})"

class Funcion:
    """Representa una proyección con estado de asientos independiente."""
    def __init__(self, fecha: datetime, pelicula: Pelicula, teatro_plantilla: Teatro):
        self.pelicula = pelicula
        self.teatro_funcion = copy.deepcopy(teatro_plantilla) # Copia independiente
        self.fecha = fecha
        self.fechaLimite = fecha + timedelta(minutes=30)

    def obtener_informacion(self) -> str:
        """Devuelve nombre, sala y hora."""
        return f"{self.pelicula.nombre} en {self.teatro_funcion.nombre} - {self.fecha.strftime(DATE_FORMAT_DISPLAY_TIME)}"

    def fechaLimite_pasada(self) -> bool:
        return datetime.now() > self.fechaLimite

    def obtener_asientos_disponibles(self) -> List[Asiento]:
         return [a for a in self.teatro_funcion.asientos if a.está_disponible()]

    def obtener_asiento_por_id(self, id_asiento: str) -> Optional[Asiento]:
         for asiento in self.teatro_funcion.asientos:
              if asiento.id == id_asiento: return asiento
         return None

    def esta_disponible_en_fecha(self, tiempoDeReferencia: datetime) -> bool:
        return self.fecha >= tiempoDeReferencia

    def __str__(self) -> str: return self.obtener_informacion()

class Cliente:
    """Representa a un cliente."""
    def __init__(self, nombre: str, id_cliente: str):
        self.nombre = nombre; self.id = id_cliente
    def __str__(self) -> str: return f"Cliente({self.nombre}, ID: {self.id})"

# --- CORREGIDO: Tiquete guarda objeto Cliente ---
class Tiquete:
    """Representa un tiquete comprado."""
    def __init__(self, precio: float, funcion: Funcion, cliente: Cliente, asiento: Asiento):
        self.precio = precio; self.funcion = funcion
        self.cliente = cliente; self.asiento = asiento

    def obtener_informacion(self) -> str:
        return (f"Tiquete para {self.funcion.obtener_informacion()}\n"
                f"Cliente: {self.cliente.nombre} (ID: {self.cliente.id})\n"
                f"Asiento: {self.asiento.id}\n"
                f"Precio: ${self.precio:,.2f} COP")

    def __str__(self) -> str:
        return f"Tiquete({self.funcion.pelicula.nombre}, Asiento: {self.asiento.id}, Cliente: {self.cliente.nombre})"

# --- Clases de Lógica y Control ---

class ControladorDeArchivos:
    """Gestiona lectura/escritura en archivos delimitados por ';'."""
    def __init__(self, ruta: str):
        self.ruta = ruta
        if not os.path.exists(self.ruta):
            try: # Crear archivo si no existe
                with open(self.ruta, "w", encoding='utf-8') as f: f.write("")
                print(f"Archivo '{self.ruta}' creado.")
            except Exception as e: print(f"Error creando archivo '{self.ruta}': {e}")

    def leer(self) -> List[List[str]]:
        try:
            with open(self.ruta, "r", encoding='utf-8') as f:
                return [line.strip().split(";") for line in f if line.strip()]
        except Exception as e: print(f"Error leyendo '{self.ruta}': {e}"); return []

    def escribir(self, datos: List[str]) -> None:
        try:
            datos_str = [str(d) for d in datos] # Asegurar strings
            with open(self.ruta, "a", encoding='utf-8') as f:
                f.write(';'.join(datos_str) + '\n')
        except Exception as e: print(f"Error escribiendo en '{self.ruta}': {e}")

class Admin:
    """Clase principal para lógica de negocio y gestión de datos."""
    def __init__(self, nombre_cine: str):
        self.nombre = nombre_cine
        self.clientes: List[Cliente] = []
        self.teatros: Dict[str, Teatro] = {n: Teatro(n) for n in DEFAULT_THEATER_NAMES}
        self.funciones_diarias: Dict[str, List[Funcion]] = {n: [] for n in DEFAULT_THEATER_NAMES}
        self.tiquetes: Dict[str, List[Tiquete]] = {}

        self.controlador_funciones = ControladorDeArchivos(MOVIE_DATA_FILE)
        self.controlador_tiquetes = ControladorDeArchivos(TICKET_DATA_FILE)

    def add_cliente(self, cliente: Cliente) -> bool:
        """Añade cliente si ID no existe. Inicializa lista de tiquetes."""
        if not isinstance(cliente, Cliente) or self.get_cliente(cliente.id): return False
        self.clientes.append(cliente)
        self.tiquetes[cliente.id] = [] # Asegurar entrada en dict de tiquetes
        print(f"Cliente '{cliente.nombre}' (ID: {cliente.id}) añadido.")
        return True

    def get_cliente(self, id_cliente: str) -> Optional[Cliente]:
        for c in self.clientes:
            if c.id == id_cliente: return c
        return None

    def cargar_funciones_desde_archivo(self) -> int:
        """Carga funciones desde movies.txt, aplicando límite de 2 por sala."""
        count = 0
        print(f"Cargando funciones desde '{self.controlador_funciones.ruta}'...")
        registros = self.controlador_funciones.leer()
        if not registros: print("Archivo de funciones vacío."); return 0

        for sala in self.funciones_diarias: self.funciones_diarias[sala] = []
        contador_sala = {sala: 0 for sala in DEFAULT_THEATER_NAMES}

        for i, reg in enumerate(registros):
            if len(reg) >= 4:
                f_str, p_nom, p_gen, s_nom = [campo.strip() for campo in reg[:4]]
                try:
                    fecha = datetime.strptime(f_str, DATE_FORMAT_FILE)
                    teatro_p = self.teatros.get(s_nom)
                    if not teatro_p: raise ValueError(f"Teatro '{s_nom}' inválido")
                    
                    if s_nom not in contador_sala: # Seguridad por si acaso
                         print(f"Error L.{i+1}: Sala '{s_nom}' no está inicializada.")
                         continue

                    if contador_sala[s_nom] >= 2:
                        print(f"Adv L.{i+1}: Límite 2 func. para {s_nom}. Ignorando '{p_nom}'.")
                        continue
                        
                    pelicula = Pelicula(p_nom, p_gen)
                    funcion = Funcion(fecha, pelicula, teatro_p)
                    self.funciones_diarias[s_nom].append(funcion)
                    contador_sala[s_nom] += 1
                    count += 1
                except (ValueError, KeyError) as e: print(f"Error L.{i+1} func: {reg} -> {e}")
                except Exception as e: print(f"Error inesperado L.{i+1} func: {reg} -> {e}")
            else: print(f"Adv L.{i+1} func: Formato incorrecto: {reg}")
            
        print(f"Se cargaron {count} funciones.")
        return count

    # --- CORREGIDO: Acepta y pasa objeto Cliente ---
    def comprar_tiquetes(self, funcion: Funcion, cliente: Cliente, ids_asientos: List[str], precio_unitario: float) -> List[Tiquete]:
        """Procesa compra, reserva asientos y guarda registro simple del tiquete."""
        if not isinstance(funcion, Funcion) or not isinstance(cliente, Cliente):
            raise TypeError("Args 'funcion'/'cliente' inválidos.")
        if not ids_asientos: raise ValueError("Seleccione al menos un asiento.")

        tiquetes_comprados = []
        asientos_a_reservar = []
        for id_a in ids_asientos: # Validar primero
            asiento = funcion.obtener_asiento_por_id(id_a)
            if not asiento: raise ValueError(f"Asiento ID '{id_a}' no existe.")
            if not asiento.está_disponible(): raise ValueError(f"Asiento {id_a} no disponible.")
            asientos_a_reservar.append(asiento)
        
        try: # Reservar y crear/guardar después
            for asiento in asientos_a_reservar:
                asiento.reservar() # Modifica la copia en 'funcion'
                # --- CORREGIDO: Pasar objeto cliente ---
                tiquete = Tiquete(precio_unitario, funcion, cliente, asiento) 
                tiquetes_comprados.append(tiquete)
                if cliente.id not in self.tiquetes: self.tiquetes[cliente.id] = []
                self.tiquetes[cliente.id].append(tiquete) # Guardar en memoria
                self.guardar_tiquete_en_archivo(tiquete) # Guardar para persistencia
            print(f"Compra OK para {cliente.nombre}: {len(tiquetes_comprados)} tiquetes.")
            return tiquetes_comprados
        except Exception as e:
            print(f"Error en compra, revirtiendo reservas: {e}")
            for asiento in asientos_a_reservar:
                 if not asiento.está_disponible(): asiento.desreservar()
            raise ValueError(f"Error procesando compra: {e}")

    # --- CORREGIDO: Nombre del argumento y lógica simplificada ---
    def get_funciones_disponibles_por_fecha(self, fecha_consulta: datetime, incluir_ya_empezadas: bool = True) -> List[Funcion]:
        """Obtiene funciones para una fecha, filtrando opcionalmente las ya empezadas."""
        tiempo_referencia = datetime.now() if not incluir_ya_empezadas else fecha_consulta.replace(hour=0, minute=0, second=0, microsecond=0)
        
        # (Opcional) Prints de depuración
        # print(f"DEBUG: get_funciones_... FechaConsulta: {fecha_consulta.date()}, IncluirEmpezadas: {incluir_ya_empezadas}, Ref: {tiempo_referencia}")

        funciones_del_dia: List[Funcion] = []
        for lista_funciones in self.funciones_diarias.values():
            for funcion in lista_funciones:
                if funcion.fecha.date() == fecha_consulta.date():
                    # Comparar hora de inicio de la función con el tiempo de referencia
                    if funcion.fecha >= tiempo_referencia:
                        funciones_del_dia.append(funcion)
                        
        return sorted(funciones_del_dia, key=lambda f: f.fecha)

    # --- CORREGIDO: Versión simple correcta para guardar estado ---
    def guardar_tiquete_en_archivo(self, tiquete: Tiquete) -> None:
        """Guarda info ESENCIAL (Fecha;Sala;Peli;AsientoID) en tickets.txt."""
        try:
            tiquete_data_simple = [
                tiquete.funcion.fecha.strftime(DATE_FORMAT_FILE), # Fecha y hora completas
                tiquete.funcion.teatro_funcion.nombre,
                tiquete.funcion.pelicula.nombre,
                tiquete.asiento.id,
            ]
            self.controlador_tiquetes.escribir(tiquete_data_simple)
        except Exception as e:
            print(f"Error guardando tiquete simple en '{TICKET_DATA_FILE}': {e}")

    # --- CORREGIDO: Nombre y lógica para cargar/aplicar ---
    def _cargar_y_aplicar_reservas(self) -> None:
        """Lee tickets.txt y marca asientos como ocupados en funciones en memoria."""
        print(f"Cargando y aplicando reservas desde '{TICKET_DATA_FILE}'...")
        reservas_guardadas = self.controlador_tiquetes.leer()
        reservas_aplicadas = 0
        funciones_map = {} # Cache: (fecha_dt, sala_str, peli_str) -> Funcion

        # Crear mapa para búsqueda rápida
        for lista_funciones in self.funciones_diarias.values():
            for func in lista_funciones:
                key = (func.fecha, func.teatro_funcion.nombre, func.pelicula.nombre)
                funciones_map[key] = func

        if not reservas_guardadas: print("No hay reservas guardadas."); return

        for i, record in enumerate(reservas_guardadas):
            if len(record) >= 4:
                fecha_str, nombre_sala, nombre_peli, asiento_id = [r.strip() for r in record[:4]]
                try:
                    fecha_dt = datetime.strptime(fecha_str, DATE_FORMAT_FILE) # Usar formato completo
                    key_busqueda = (fecha_dt, nombre_sala, nombre_peli)
                    funcion_encontrada = funciones_map.get(key_busqueda)

                    if funcion_encontrada:
                        asiento = funcion_encontrada.obtener_asiento_por_id(asiento_id)
                        if asiento and asiento.está_disponible():
                            asiento.reservar()
                            reservas_aplicadas += 1
                except ValueError as e: print(f"Error parse Tkt L.{i+1}: {record} -> {e}")
                except Exception as e: print(f"Error inesperado Tkt L.{i+1}: {record} -> {e}")
            else: print(f"Adv Tkt L.{i+1}: Formato incorrecto: {record}")
            
        print(f"Se aplicaron {reservas_aplicadas} reservas desde archivo.")

    def get_todas_las_funciones(self) -> List[Funcion]:
        """Devuelve lista plana de todas las funciones cargadas, ordenada."""
        lista_completa = [func for lista in self.funciones_diarias.values() for func in lista]
        lista_completa.sort(key=lambda f: (f.fecha, f.teatro_funcion.nombre))
        return lista_completa
        
    def generar_reporte_completo(self) -> List[Dict]:
        """Genera datos de ventas/ganancias para TODAS las funciones, contando asientos ocupados."""
        reporte_final = []
        print("Generando reporte contando asientos ocupados...")

        for lista_funciones_sala in self.funciones_diarias.values():
            for funcion in lista_funciones_sala:
                # Contar asientos ocupados para ESTA función
                asientos_ocupados = sum(1 for a in funcion.teatro_funcion.asientos if not a.está_disponible())
                ganancias_totales = asientos_ocupados * PRECIO_TIQUETE
                            
                reporte_final.append({
                    'fecha': funcion.fecha, 'sala': funcion.teatro_funcion.nombre,
                    'pelicula': funcion.pelicula.nombre,
                    'tiquetes_vendidos': asientos_ocupados,
                    'ganancias_totales': ganancias_totales
                })
        reporte_final.sort(key=lambda item: (item['fecha'], item['sala']))
        print(f"Reporte generado para {len(reporte_final)} funciones.")
        return reporte_final

# --- Clase de Interfaz Gráfica (TheaterGUI) ---

class TheaterGUI:
    """Interfaz gráfica principal usando ttkbootstrap."""
    def __init__(self, root: ttk.Window, admin_instance: Admin):
        """Inicializa la GUI, variables, carga imágenes y configura layout."""
        self.root = root
        self.admin = admin_instance
        self.funcion_seleccionada: Optional[Funcion] = None
        self.asientos_seleccionados_para_compra: List[Asiento] = []
        self.mapa_widgets_asientos: Dict[str, tk.Button] = {} # Usar tk.Button

        self.root.title(APP_TITLE)
        # No llamar a geometry aquí, se hace en main después de centrar

        # Variables para filtros
        self.movie_filter_var = tk.StringVar(value="Todas")
        self.sala_filter_var = tk.StringVar(value="Todas")
        # --- CORREGIDO: Checkbox inicia desmarcado ---
        self.include_started_var = tk.BooleanVar(value=False) 
        self.show_all_functions_var = tk.BooleanVar(value=False)

        self._cargar_imagenes_asientos()
        self._setup_gui_layout()
        self._on_filter_apply() # Carga inicial

    def _cargar_imagenes_asientos(self) -> None:
        """Carga y prepara las imágenes de los asientos."""
        print("Cargando imágenes de asientos...")
        # --- RECOMENDACIÓN FUERTE: Usar imágenes con fondo opaco COLOR_FONDO_ASIENTOS ---
        try:
            pil_avail = Image.open(SEAT_IMG_AVAILABLE).resize((SEAT_IMG_WIDTH, SEAT_IMG_HEIGHT), Image.Resampling.LANCZOS)
            pil_occup = Image.open(SEAT_IMG_OCCUPIED).resize((SEAT_IMG_WIDTH, SEAT_IMG_HEIGHT), Image.Resampling.LANCZOS)
            pil_select = Image.open(SEAT_IMG_SELECTED).resize((SEAT_IMG_WIDTH, SEAT_IMG_HEIGHT), Image.Resampling.LANCZOS)
            self.img_available = ImageTk.PhotoImage(pil_avail)
            self.img_occupied = ImageTk.PhotoImage(pil_occup)
            self.img_selected = ImageTk.PhotoImage(pil_select)
            print("Imágenes de asientos OK.")
        except FileNotFoundError as e:
            msg = f"ERROR CRÍTICO: Falta archivo '{e.filename}'. Se usará fallback de texto/color."
            print(msg)
            messagebox.showerror("Error Imagen", msg)
            self.img_available = self.img_occupied = self.img_selected = None
        except Exception as e:
            msg = f"Error inesperado cargando imágenes: {e}"
            print(msg)
            messagebox.showerror("Error Imagen", msg)
            self.img_available = self.img_occupied = self.img_selected = None

    # --- Métodos de Configuración de GUI ---

    def _setup_gui_layout(self) -> None:
        """Configura la estructura principal de widgets y bindings."""
        self.root.rowconfigure(1, weight=1)
        self.root.columnconfigure(0, weight=1)

        # --- Frame Superior (Filtros) ---
        filter_frame = ttk.Frame(self.root, padding="10")
        filter_frame.grid(row=0, column=0, sticky='ew')

        # Filtro Fecha
        ttk.Label(filter_frame, text="Fecha:").pack(side='left', padx=(0, 5))
        self.date_entry_widget = ttk.DateEntry(filter_frame, firstweekday=0, 
                                               dateformat=DATE_FORMAT_DATEENTRY, width=12)
        self.date_entry_widget.pack(side='left', padx=5)
        self.date_entry_widget.bind("<<DateEntrySelected>>", self._on_filter_apply)
        self.date_entry_widget.entry.bind("<Return>", self._on_filter_apply)
        self.date_entry_widget.entry.bind("<FocusOut>", self._on_filter_apply)

        # Filtro Película
        ttk.Label(filter_frame, text="Película:").pack(side='left', padx=(15, 5))
        self.movie_combobox = ttk.Combobox(filter_frame, textvariable=self.movie_filter_var, 
                                           state='disabled', width=30)
        self.movie_combobox['values'] = ["Todas"]; self.movie_combobox.current(0)
        self.movie_combobox.pack(side='left', padx=5)
        self.movie_combobox.bind("<<ComboboxSelected>>", self._on_filter_apply)

        # Filtro Sala
        ttk.Label(filter_frame, text="Sala:").pack(side='left', padx=(15, 5))
        self.sala_combobox = ttk.Combobox(filter_frame, textvariable=self.sala_filter_var, 
                                          state='readonly', width=15)
        self.sala_combobox['values'] = ["Todas"] + DEFAULT_THEATER_NAMES; self.sala_combobox.current(0)
        self.sala_combobox.pack(side='left', padx=5)
        self.sala_combobox.bind("<<ComboboxSelected>>", self._on_filter_apply)

        # Checkbox "Mostrar Todas"
        show_all_check = ttk.Checkbutton(filter_frame, text="Mostrar Todas", 
                                         variable=self.show_all_functions_var,
                                         command=self._on_toggle_show_all, bootstyle="round-toggle")
        show_all_check.pack(side='right', padx=15)

        # Checkbox "Incluir Empezadas"
        # --- CORREGIDO: Guardar referencia en self. ---
        self.include_started_check = ttk.Checkbutton(
            filter_frame, text="Incluir ya empezadas", variable=self.include_started_var,
            command=self._on_filter_apply, bootstyle="round-toggle")
        self.include_started_check.pack(side='right', padx=5)

        # Botón Reporte
        report_button = ttk.Button(filter_frame, text="Ver Reporte", 
                                   command=self._mostrar_ventana_reportes, bootstyle=SUCCESS)
        report_button.pack(side='left', padx=20)

        # --- Frame Principal (PanedWindow) ---
        main_pane = ttk.PanedWindow(self.root, orient='horizontal')
        main_pane.grid(row=1, column=0, sticky='nsew', padx=10, pady=5)

        # Frame Izquierdo (Funciones)
        functions_frame = ttk.Frame(main_pane, padding="5")
        main_pane.add(functions_frame, weight=1)
        ttk.Label(functions_frame, text="Funciones Disponibles", font="-weight bold").pack(pady=5)
        cols = ('pelicula', 'hora', 'sala')
        self.functions_treeview = ttk.Treeview(functions_frame, columns=cols, show='headings', height=15, bootstyle=INFO)
        self.functions_treeview.heading('pelicula', text='Película'); self.functions_treeview.column('pelicula', width=200, anchor='w')
        self.functions_treeview.heading('hora', text='Hora'); self.functions_treeview.column('hora', width=100, anchor='center')
        self.functions_treeview.heading('sala', text='Sala'); self.functions_treeview.column('sala', width=100, anchor='center')
        scrollbar = ttk.Scrollbar(functions_frame, orient='vertical', command=self.functions_treeview.yview, bootstyle=ROUND)
        self.functions_treeview.configure(yscrollcommand=scrollbar.set)
        self.functions_treeview.pack(side='left', fill='both', expand=True); scrollbar.pack(side='right', fill='y')
        self.functions_treeview.bind('<<TreeviewSelect>>', self._on_function_select)

        # Frame Derecho (Asientos)
        self.seat_area_frame = ttk.Frame(main_pane, padding="5")
        main_pane.add(self.seat_area_frame, weight=3)

        # --- Frame Inferior (Compra) ---
        purchase_status_frame = ttk.Frame(self.root, padding="5 10 5 10")
        purchase_status_frame.grid(row=2, column=0, sticky='ew')
        self.purchase_info_label = ttk.Label(purchase_status_frame, text="Seleccione función y asientos.", anchor='w')
        self.purchase_info_label.pack(side='left', fill='x', expand=True, padx=5)
        buy_button = ttk.Button(purchase_status_frame, text="Comprar Entradas", command=self._confirm_purchase, bootstyle=SUCCESS)
        buy_button.pack(side='right', padx=5)
        
        # Estado Inicial Widgets
        if not self.show_all_functions_var.get():
             self._set_filter_widgets_state('enable') # Habilitar filtros normales

    # --- Métodos de Actualización y Eventos ---

    def _on_filter_apply(self, event=None) -> None:
        """Obtiene filtros normales, busca funciones y actualiza GUI, SI 'Mostrar Todas' está apagado."""
        if self.show_all_functions_var.get(): return # No hacer nada si se muestran todas
        
        incluir_empezadas_arg = self.include_started_var.get() # Leer estado actual
        try:
            date_str = self.date_entry_widget.entry.get()
            selected_date_obj = datetime.strptime(date_str, DATE_FORMAT_DISPLAY_DATE).date()
            selected_datetime = datetime.combine(selected_date_obj, datetime.min.time())

            movie_filter = self.movie_filter_var.get()
            sala_filter = self.sala_filter_var.get()
            # print(f"Filtros: {date_str}, Peli='{movie_filter}', Sala='{sala_filter}', IncluirEmpezadas={incluir_empezadas_arg}") # Log

            todas_funciones_dia = self.admin.get_funciones_disponibles_por_fecha(
                selected_datetime, incluir_ya_empezadas=incluir_empezadas_arg)

            self._actualizar_combobox_peliculas(todas_funciones_dia)
            movie_filter = self.movie_filter_var.get() # Re-leer por si cambió

            filtered_functions = self._filtrar_funciones_gui(todas_funciones_dia, movie_filter, sala_filter)
            self._poblar_treeview_funciones(filtered_functions, mostrar_fecha=False)

        except ValueError as e:
            messagebox.showerror("Error de Fecha", f"Formato de fecha inválido: '{date_str}'. Use {DATE_FORMAT_DISPLAY_DATE}.\n({e})")
            self._limpiar_vista_funciones_y_asientos(clear_functions=True, clear_seats=True)
        except Exception as e:
            messagebox.showerror("Error Aplicando Filtros", f"Ocurrió un error: {e}")
            self._limpiar_vista_funciones_y_asientos(clear_functions=True, clear_seats=True)

    def _on_function_select(self, event=None) -> None:
        """Manejador cuando se selecciona una función en el Treeview."""
        selected_items = self.functions_treeview.selection()
        if not selected_items:
            self.funcion_seleccionada = None
            self._clear_seat_display(); self._update_purchase_info(); return
        
        selected_iid = selected_items[0]
        selected_function = self.function_map.get(selected_iid)

        if selected_function:
            self.funcion_seleccionada = selected_function
            self.asientos_seleccionados_para_compra = []
            self._update_seat_display()
            self._update_purchase_info()
        else: # No debería ocurrir si map está sincronizado
            self.funcion_seleccionada = None
            self._clear_seat_display(); self._update_purchase_info()

    # --- CORREGIDO: Habilita/Deshabilita todos los filtros normales ---
    def _set_filter_widgets_state(self, state: str) -> None:
        """Habilita ('enable') o deshabilita ('disabled') los filtros normales."""
        widget_state = 'disabled' if state == 'disabled' else 'normal'
        combo_state = 'disabled' if state == 'disabled' else 'readonly'
        try:
            self.date_entry_widget.configure(state=widget_state)
            # Habilitar movie combobox solo si tiene opciones y no estamos deshabilitando
            if self.movie_combobox.cget('values') and len(self.movie_combobox.cget('values')) > 1 and state != 'disabled':
                 self.movie_combobox.configure(state=combo_state)
            else:
                 self.movie_combobox.configure(state='disabled') 
            self.sala_combobox.configure(state=combo_state)
            # El checkbutton usa 'normal'/'disabled'
            self.include_started_check.configure(state=widget_state) 
        except Exception as e: 
             print(f"Advertencia: Error config. estado widgets filtro: {e}")

    def _on_toggle_show_all(self) -> None:
        """Manejador para el checkbox 'Mostrar Todas'."""
        if self.show_all_functions_var.get():
            self._set_filter_widgets_state('disabled')
            self._load_all_functions_to_view()
        else:
            self._set_filter_widgets_state('enable')
            self._on_filter_apply() # Reaplicar filtros normales

    def _load_all_functions_to_view(self) -> None:
        """Obtiene TODAS las funciones del Admin y las muestra."""
        print("Cargando todas las funciones...")
        try:
            todas_las_funciones = self.admin.get_todas_las_funciones()
            self._actualizar_combobox_peliculas(todas_las_funciones)
            self._poblar_treeview_funciones(todas_las_funciones, mostrar_fecha=True) # Mostrar fecha completa
        except Exception as e:
            messagebox.showerror("Error Cargando Funciones", f"Error: {e}")
            self._limpiar_vista_funciones_y_asientos(clear_functions=True, clear_seats=True)

    # --- Métodos Helper de GUI ---

    def _actualizar_combobox_peliculas(self, lista_funciones: List[Funcion]) -> None:
         """Actualiza las opciones del combobox de películas."""
         nombres = ["Todas"]
         if lista_funciones:
             nombres.extend(sorted(list(set(f.pelicula.nombre for f in lista_funciones))))
         
         current_selection = self.movie_filter_var.get()
         self.movie_combobox['values'] = nombres
         
         if current_selection in nombres:
             self.movie_filter_var.set(current_selection)
         else:
             self.movie_filter_var.set("Todas")

         # Habilitar/Deshabilitar basado en opciones y modo 'Mostrar Todas'
         new_state = 'readonly' if len(nombres) > 1 and not self.show_all_functions_var.get() else 'disabled'
         self.movie_combobox.config(state=new_state)


    def _filtrar_funciones_gui(self, funciones: List[Funcion], movie_filter: str, sala_filter: str) -> List[Funcion]:
         """Filtra lista de funciones según comboboxes."""
         resultado = funciones
         if movie_filter != "Todas":
             resultado = [f for f in resultado if f.pelicula.nombre == movie_filter]
         if sala_filter != "Todas":
             resultado = [f for f in resultado if f.teatro_funcion.nombre == sala_filter]
         return resultado

    def _poblar_treeview_funciones(self, funciones: List[Funcion], mostrar_fecha: bool = False) -> None:
        """Limpia y puebla el Treeview con funciones."""
        for item in self.functions_treeview.get_children(): self.functions_treeview.delete(item)
        self.function_map = {}
        
        if funciones:
            for func in funciones:
                hora_o_fecha_hora = func.fecha.strftime(DATE_FORMAT_DISPLAY_FULL if mostrar_fecha else DATE_FORMAT_DISPLAY_TIME)
                iid = self.functions_treeview.insert('', 'end', values=(
                    func.pelicula.nombre, hora_o_fecha_hora, func.teatro_funcion.nombre))
                self.function_map[iid] = func
            msg = f"Mostrando {len(funciones)} funciones."
        else:
             msg = "No hay funciones para mostrar con los filtros actuales."
             self.functions_treeview.insert('', 'end', values=(msg, "", ""))
        
        print(msg)
        # Limpiar SIEMPRE asientos al cambiar la lista de funciones mostrada
        self._limpiar_vista_funciones_y_asientos(clear_functions=False, clear_seats=True) 

    def _limpiar_vista_funciones_y_asientos(self, clear_functions: bool = False, clear_seats: bool = True) -> None:
        """Limpia selectivamente treeview y/o área de asientos."""
        if clear_functions:
            for item in self.functions_treeview.get_children(): self.functions_treeview.delete(item)
            self.function_map = {}
            # También limpiar combobox de películas si se limpia el treeview
            self._actualizar_combobox_peliculas([]) 
        if clear_seats:
            self._clear_seat_display()
            self.funcion_seleccionada = None
            self.asientos_seleccionados_para_compra = []
            self._update_purchase_info()
            # Resetear texto de etiquetas de reporte si existen
            if hasattr(self, 'report_vendidos_label'): self.report_vendidos_label.config(text="Vendidos: -")
            if hasattr(self, 'report_ganancias_label'): self.report_ganancias_label.config(text="Ganancias: -")


    def _clear_seat_display(self) -> None:
        """Limpia área de asientos y muestra mensaje."""
        for widget in self.seat_area_frame.winfo_children(): widget.destroy()
        ttk.Label(self.seat_area_frame, text="Seleccione una función para ver los asientos.").pack(padx=20, pady=50)

    def _update_seat_display(self) -> None:
        """Limpia y redibuja pantalla y asientos."""
        for widget in self.seat_area_frame.winfo_children(): widget.destroy()
        if not self.funcion_seleccionada:
            self._clear_seat_display(); return

        # --- CORREGIDO: Usar tk.Frame/tk.Label para pantalla ---
        screen_frame = tk.Frame(self.seat_area_frame, bg='black', height=25) 
        screen_frame.pack(side='bottom', fill='x', padx=50, pady=(15, 25))
        screen_frame.pack_propagate(False) 
        screen_label = tk.Label(screen_frame, text="PANTALLA", bg='black', fg='white', font=('Calibri', 11, 'bold')) 
        screen_label.pack(pady=4)

        self.mostrar_asientos(self.seat_area_frame, self.funcion_seleccionada)

    # --- CORREGIDO: Usa tk.Frame y tk.Button ---
    def mostrar_asientos(self, parent_frame: ttk.Frame, funcion: Funcion) -> None:
        """Dibuja cuadrícula de asientos usando tk.Button y fondo explícito."""
        # --- RECOMENDACIÓN FUERTE: Asegurar que las imágenes PNG tengan fondo opaco COLOR_FONDO_ASIENTOS ---
        seats_layout = [11]*2 + [9]*2 + [7]*5 + [5]*1
        num_rows = len(seats_layout)
        max_seats_in_row = 11
        num_grid_cols = 1 + max_seats_in_row + 1
        
        self.mapa_widgets_asientos = {}

        grid_frame = tk.Frame(parent_frame, bg=COLOR_FONDO_ASIENTOS) 
        grid_frame.pack(side='top', expand=True, pady=(20, 10))

        asiento_index = 0
        asientos_de_la_funcion = funcion.teatro_funcion.asientos # Usa la copia

        for i in range(num_rows):
            num_seats_this_row = seats_layout[i]
            indent = (max_seats_in_row - num_seats_this_row) // 2
            start_col = 1 + indent
            end_col = start_col + num_seats_this_row - 1

            for j in range(num_grid_cols):
                widget_to_place = None
                is_seat_column = start_col <= j <= end_col
                
                # Pasillos / Vacíos
                if j == 0 or j == num_grid_cols - 1 or not is_seat_column:
                    width = 30 if (j == 0 or j == num_grid_cols - 1) else SEAT_IMG_WIDTH + 5
                    widget_to_place = tk.Frame(grid_frame, width=width, height=SEAT_IMG_HEIGHT+5, bg=COLOR_FONDO_ASIENTOS)
                
                # Asientos
                elif is_seat_column:
                    if asiento_index < len(asientos_de_la_funcion):
                        asiento = asientos_de_la_funcion[asiento_index]
                        is_available = asiento.está_disponible()
                        is_selected = asiento in self.asientos_seleccionados_para_compra

                        img = None
                        if is_selected and self.img_selected: img = self.img_selected
                        elif not is_available and self.img_occupied: img = self.img_occupied
                        elif is_available and self.img_available: img = self.img_available

                        seat_btn = None # Inicializar
                        if img: # Usar tk.Button con imagen
                            seat_btn = tk.Button(grid_frame, image=img,
                                                 bg=COLOR_FONDO_ASIENTOS, borderwidth=0, 
                                                 highlightthickness=0, relief='flat', 
                                                 activebackground=COLOR_FONDO_ASIENTOS)
                            seat_btn.image = img
                        else: # Fallback con texto
                            fb_text = asiento.id; color = "gray" # Default fallback
                            if not is_available: color = "red"
                            elif is_selected: color = "gold"; fb_text = f"[{asiento.id}]"
                            elif is_available: color = "green"
                            seat_btn = tk.Button(grid_frame, text=fb_text, fg="white", bg=color,
                                                 width=5, height=2, borderwidth=0, relief='flat', activebackground=color)

                        if seat_btn:
                            seat_btn.config(command=lambda a=asiento, b=seat_btn: self.on_seat_click(a, b))
                            seat_btn.bind("<Enter>", self._on_seat_enter) 
                            seat_btn.bind("<Leave>", self._on_seat_leave) 
                            self.mapa_widgets_asientos[asiento.id] = seat_btn
                        
                        widget_to_place = seat_btn
                        asiento_index += 1
                    else: # Error de Layout/Índice
                         print(f"Error Layout: Índice {asiento_index} fuera de rango.")
                         widget_to_place = tk.Frame(grid_frame, width=SEAT_IMG_WIDTH+5, height=SEAT_IMG_HEIGHT+5, bg="magenta")

                # Colocar widget en grid
                if widget_to_place:
                    widget_to_place.grid(row=i, column=j, padx=1, pady=1)
                    if isinstance(widget_to_place, tk.Frame):
                         widget_to_place.pack_propagate(False) # Evitar que Frames se encojan

    def _on_seat_enter(self, event):
        """Cambia cursor a mano al entrar."""
        event.widget.config(cursor="hand2")

    def _on_seat_leave(self, event):
        """Restaura cursor al salir."""
        event.widget.config(cursor="")

    def on_seat_click(self, asiento: Asiento, button: tk.Button) -> None:
        """Manejador de clic en asiento para selección/deselección."""
        if not self.funcion_seleccionada: messagebox.showwarning("Selección Requerida", "Seleccione una función primero."); return
        if self.funcion_seleccionada.fechaLimite_pasada(): messagebox.showwarning("Tiempo Excedido", "El tiempo para comprar/seleccionar ha expirado."); return

        # Solo permitir interactuar si el asiento está disponible (verde)
        if asiento.está_disponible():
            img_actualizar = None
            if asiento in self.asientos_seleccionados_para_compra: # Deseleccionar
                self.asientos_seleccionados_para_compra.remove(asiento)
                img_actualizar = self.img_available
                fb_text = asiento.id
            else: # Seleccionar
                self.asientos_seleccionados_para_compra.append(asiento)
                img_actualizar = self.img_selected
                fb_text = f"[{asiento.id}]"
            
            # Actualizar apariencia
            if img_actualizar and hasattr(button,'image'): # Asegurar que el botón usa imagen
                 button.config(image=img_actualizar)
                 button.image = img_actualizar
            elif not hasattr(button,'image'): # Fallback texto
                 button.config(text=fb_text)
                 # Reajustar color de fallback si es necesario (ej. a verde o amarillo)
                 new_color = "green" if asiento in self.asientos_seleccionados_para_compra else "gold" # Ejemplo
                 button.config(bg=new_color, activebackground=new_color)
        
        elif asiento not in self.asientos_seleccionados_para_compra: # Ocupado (rojo) y no seleccionado -> Mostrar info
             messagebox.showinfo("Asiento Ocupado", f"El asiento {asiento.id} ya está ocupado.")
        # Si está ocupado Y seleccionado (no debería pasar si se carga bien), no hacer nada al click

        self._update_purchase_info()

    def _update_purchase_info(self) -> None:
        """Actualiza etiqueta de información de compra."""
        num = len(self.asientos_seleccionados_para_compra)
        if num > 0:
            costo = num * PRECIO_TIQUETE
            ids = ", ".join(sorted([a.id for a in self.asientos_seleccionados_para_compra]))
            self.purchase_info_label.config(text=f"Sel: {num} ({ids}) - Total: ${costo:,.0f} COP")
        else:
            self.purchase_info_label.config(text="Seleccione asientos haciendo clic.")

    def _confirm_purchase(self) -> None:
        """Inicia proceso de compra con validación de cliente."""
        # 1. Validaciones previas
        if not self.funcion_seleccionada or not self.asientos_seleccionados_para_compra or self.funcion_seleccionada.fechaLimite_pasada():
             if not self.funcion_seleccionada: msg = "Seleccione una función primero."
             elif not self.asientos_seleccionados_para_compra: msg = "Seleccione al menos un asiento."
             else: msg = "Ya no se pueden comprar entradas (tiempo excedido)."
             messagebox.showwarning("Acción Requerida", msg); return

        # --- 2. Obtener y Validar Datos del Cliente ---
        cliente: Optional[Cliente] = None
        while cliente is None: 
            id_cliente = simpledialog.askstring("Identificación Cliente", "Ingrese ID cliente (10 dígitos numéricos):", parent=self.root)
            if id_cliente is None: return # Canceló

            # Validación ID
            id_cliente = id_cliente.strip() # Quitar espacios extra
            if not id_cliente.isdigit() or len(id_cliente) != 10:
                messagebox.showerror("ID Inválido", "El ID debe contener exactamente 10 dígitos numéricos."); continue

            cliente_existente = self.admin.get_cliente(id_cliente)
            if cliente_existente: cliente = cliente_existente; break

            else: # Cliente nuevo
                while True: 
                     nombre_cliente = simpledialog.askstring("Nombre Cliente Nuevo", f"Cliente ID {id_cliente} no encontrado.\nIngrese nombre (solo letras/espacios):", parent=self.root)
                     if nombre_cliente is None: return # Canceló
                     
                     nombre_cliente = nombre_cliente.strip()
                     # Validación Nombre (permite letras y espacios internos)
                     if nombre_cliente and re.fullmatch(r"[A-Za-zÁÉÍÓÚáéíóúÑñ\s]+", nombre_cliente):
                         cliente = Cliente(nombre_cliente, id_cliente)
                         self.admin.add_cliente(cliente)
                         break # Sale del bucle de nombre
                     else:
                          messagebox.showerror("Nombre Inválido", "El nombre solo debe contener letras y espacios, y no puede estar vacío.")
                break # Sale del bucle de cliente

        if not cliente: messagebox.showerror("Error", "No se pudo obtener info del cliente."); return
             
        # --- 3. Intentar Compra ---
        try:
            ids_a_comprar = [a.id for a in self.asientos_seleccionados_para_compra]
            tiquetes = self.admin.comprar_tiquetes(self.funcion_seleccionada, cliente, ids_a_comprar, PRECIO_TIQUETE)
            
            messagebox.showinfo("Compra Exitosa", f"Compra para {cliente.nombre} (ID: {cliente.id}).\nAsientos: {', '.join(ids_a_comprar)}")
            self.asientos_seleccionados_para_compra = []
            self._update_purchase_info()
            self._update_seat_display() # Refrescar asientos

        except (ValueError, TypeError) as e:
             messagebox.showerror("Error en Compra", f"No se pudo completar:\n{e}")

    # --- Reporte ---
    def _mostrar_ventana_reportes(self) -> None:
        """Crea y muestra ventana modal con tabla de reportes."""
        print("Generando reporte completo...")
        try:
            datos_reporte = self.admin.generar_reporte_completo()
        except Exception as e:
            messagebox.showerror("Error Reporte", f"No se pudo generar:\n{e}"); return

        report_window = tk.Toplevel(self.root)
        report_window.title("Reporte Funciones - Ventas y Ganancias")
        
        report_width, report_height = 800, 500
        center_window(report_window, report_width, report_height) # Centrar
        report_window.transient(self.root); report_window.grab_set() 

        frame = ttk.Frame(report_window, padding="10")
        frame.pack(fill='both', expand=True)

        cols = ('fecha_hora', 'pelicula', 'sala', 'vendidos', 'ganancias')
        report_tree = ttk.Treeview(frame, columns=cols, show='headings', height=18, bootstyle=INFO)
        
        report_tree.heading('fecha_hora', text='Fecha y Hora'); report_tree.column('fecha_hora', width=150, anchor='w')
        report_tree.heading('pelicula', text='Película'); report_tree.column('pelicula', width=250, anchor='w')
        report_tree.heading('sala', text='Sala'); report_tree.column('sala', width=80, anchor='center')
        report_tree.heading('vendidos', text='Entradas Vendidas'); report_tree.column('vendidos', width=100, anchor='e')
        report_tree.heading('ganancias', text='Ganancias (COP)'); report_tree.column('ganancias', width=120, anchor='e')

        total_vendidos, total_ganancias = 0, 0.0
        if datos_reporte:
            for item in datos_reporte:
                fecha_str = item['fecha'].strftime(DATE_FORMAT_DISPLAY_FULL)
                # --- CORREGIDO: Usar :.2f para dos decimales ---
                ganancia_str = f"{item['ganancias_totales']:,.0f}" 
                report_tree.insert('', 'end', values=(fecha_str, item['pelicula'], item['sala'], item['tiquetes_vendidos'], ganancia_str))
                total_vendidos += item['tiquetes_vendidos']
                total_ganancias += item['ganancias_totales']
        else:
            report_tree.insert('', 'end', values=("No hay datos", "", "", "", ""))

        scrollbar = ttk.Scrollbar(frame, orient='vertical', command=report_tree.yview, bootstyle=ROUND)
        report_tree.configure(yscrollcommand=scrollbar.set)
        
        report_tree.grid(row=0, column=0, sticky='nsew')
        scrollbar.grid(row=0, column=1, sticky='ns')
        frame.rowconfigure(0, weight=1); frame.columnconfigure(0, weight=1)

        total_frame = ttk.Frame(frame, padding="5 0 0 0")
        total_frame.grid(row=1, column=0, columnspan=2, sticky='ew', pady=(10,0))
        
        # --- CORREGIDO: Totales con .2f ---
        ttk.Label(total_frame, text=f"Entradas: {total_vendidos}", font="-weight bold", bootstyle=(INFO, INVERSE)).pack(side='left', padx=10, ipadx=8, ipady=5)
        ttk.Label(total_frame, text=f"Ganancias: ${total_ganancias:,.0f} COP", font="-weight bold", bootstyle=(SUCCESS, INVERSE)).pack(side='right', padx=10, ipadx=8, ipady=5)
        
        close_button = ttk.Button(frame, text="Cerrar", command=report_window.destroy, bootstyle=DANGER)
        close_button.grid(row=2, column=0, columnspan=2, pady=10)

# --- Función Principal ---

def main() -> None:
    """Inicializa Admin, carga datos, aplica tema, centra y ejecuta la GUI."""
    print("Iniciando aplicación Cine...")
    admin = Admin("Cine Cultural Barranquilla")
    admin.cargar_funciones_desde_archivo()
    # --- CORREGIDO: Llamada al método renombrado ---
    admin._cargar_y_aplicar_reservas() 

    root = ttk.Window(themename="flatly") 
    # Quitar la configuración de estilo redundante aquí, se hace en GUI.__init__ si es necesario
    # style = ttk.Style(root) ... 

    # --- Centrar Ventana Principal ---
    try:
        main_width, main_height = map(int, WINDOW_GEOMETRY.split('x'))
        root.withdraw()         
        # El título se puede poner antes o después de centrar
        root.title(APP_TITLE) 
        root.update_idletasks() 
        center_window(root, main_width, main_height) 
        root.deiconify()        
    except Exception as e:
        print(f"Advertencia: No se pudo parsear/centrar ventana principal: {e}")
        root.title(APP_TITLE) # Asegurar título
        root.geometry(WINDOW_GEOMETRY) 

    app = TheaterGUI(root, admin)
    root.mainloop()
    print("Aplicación Cine cerrada.")

# --- Punto de Entrada ---
if __name__ == "__main__":
    main()