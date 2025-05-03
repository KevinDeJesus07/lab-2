# -*- coding: utf-8 -*-
"""
Cine Cultural Barranquilla

Descripción:
Interfaz gráfica (GUI) construida con ttkbootstrap para la gestión de un cine.
Permite visualizar funciones filtradas por fecha, película y sala, con opción
para incluir/excluir funciones ya empezadas. Ofrece selección interactiva de 
asientos y compra de tiquetes con validación de cliente (ID y Nombre). 
Las reservas de asientos se guardan en 'tickets.txt' para persistencia. 
Incluye vista de reporte de ventas por función.

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
    - Mateo Cisneros Galeano
    - Alfredo Badillo Sarmiento

Fecha: 2025-05-02 
"""

import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import messagebox, simpledialog
from datetime import datetime, timedelta, date
from typing import List, Optional, Dict, Tuple
from PIL import Image, ImageTk  
import copy
import os
import re 

# Constantes y Configuración
APP_TITLE = "Cine Cultural Barranquilla"
WINDOW_GEOMETRY = "1400x800"
COLOR_FONDO_ASIENTOS = '#FFFFFF' 

# Archivos
MOVIE_DATA_FILE = 'movies.txt'
TICKET_DATA_FILE = 'tickets.txt'

# Configuración Teatro/Asientos
DEFAULT_SEATS_PER_THEATER = 80
DEFAULT_THEATER_NAMES = ['Sala 1', 'Sala 2', 'Sala 3']

# Imágenes
SEAT_IMG_AVAILABLE = "seat_available.png"
SEAT_IMG_OCCUPIED = "seat_occupied.png"
SEAT_IMG_SELECTED = "seat_selected.png"
SEAT_IMG_WIDTH = 40
SEAT_IMG_HEIGHT = 40

# Otros
PRECIO_TIQUETE = 15000 

# Formatos de Fecha/Hora
DATE_FORMAT_FILE = '%d/%m/%Y - %H:%M'     # Para leer/escribir archivos
DATE_FORMAT_DISPLAY_FULL = '%d/%m/%Y %H:%M' # Para mostrar fecha y hora completa
DATE_FORMAT_DISPLAY_DATE = '%d/%m/%Y'     # Para mostrar/parsear solo fecha en GUI
DATE_FORMAT_DISPLAY_TIME = '%H:%M'     # Para mostrar solo hora en GUI
DATE_FORMAT_DATEENTRY = DATE_FORMAT_DISPLAY_DATE # Formato que usa ttk.DateEntry

def center_window(window: tk.Misc, width: int, height: int) -> None:
    """Calcula y aplica geometría para centrar una ventana Tk o Toplevel."""
    try:
        window.update_idletasks() 
        screen_width = window.winfo_screenwidth()
        screen_height = window.winfo_screenheight()
        x = (screen_width / 2) - (width / 2)
        y = (screen_height / 2) - (height / 2)
        window.geometry(f'{width}x{height}+{int(x)}+{int(y)}')
    except Exception as e:
        print(f"Advertencia: No se pudo centrar ventana ({e}). Usando tamaño {width}x{height}.")
        window.geometry(f'{width}x{height}')

class Asiento:
    """Representa un único asiento con ID y estado de disponibilidad."""
    def __init__(self, id_asiento: str):
        self.id = id_asiento; self.disponible = True
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
        filas = "ABCDEFGHIJ"; count = 0
        if cantidad <= 0 or not filas: return []
        asientos_por_fila = max(1, cantidad // len(filas))
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
        for a in self.asientos:
            if a.id == id_asiento: return a
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

    def fechaLimite_pasada(self) -> bool: return datetime.now() > self.fechaLimite
    def obtener_asientos_disponibles(self) -> List[Asiento]: return [a for a in self.teatro_funcion.asientos if a.está_disponible()]
    def obtener_asiento_por_id(self, id_asiento: str) -> Optional[Asiento]: return self.teatro_funcion.obtener_asiento_por_id(id_asiento)
    def esta_disponible_en_fecha(self, t: datetime) -> bool: return self.fecha >= t
    def __str__(self) -> str: return self.obtener_informacion()

class Cliente:
    """Representa a un cliente."""
    def __init__(self, nombre: str, id_cliente: str):
        self.nombre = nombre; self.id = id_cliente
    def __str__(self) -> str: return f"Cliente({self.nombre}, ID: {self.id})"

class Tiquete:
    """Representa un tiquete comprado."""
    def __init__(self, precio: float, funcion: Funcion, cliente: Cliente, asiento: Asiento):
        self.precio = precio; self.funcion = funcion
        self.cliente = cliente; self.asiento = asiento # Guarda objeto Cliente
    def obtener_informacion(self) -> str:
        return (f"Tiquete para {self.funcion.obtener_informacion()}\n"
                f"Cliente: {self.cliente.nombre} (ID: {self.cliente.id})\n"
                f"Asiento: {self.asiento.id}\n"
                f"Precio: ${self.precio:,.0f} COP")
    def __str__(self) -> str:
        return f"Tiquete({self.funcion.pelicula.nombre}, Asiento: {self.asiento.id}, Cliente: {self.cliente.nombre})"

class ControladorDeArchivos:
    """Gestiona lectura/escritura simple en archivos delimitados por ';'."""
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
    def escribir(self, datos: List[str]) -> None: # Appends
        try:
            datos_str = [str(d) for d in datos]
            with open(self.ruta, "a", encoding='utf-8') as f:
                f.write(';'.join(datos_str) + '\n')
        except Exception as e: print(f"Error escribiendo en '{self.ruta}': {e}")

    def sobrescribir(self, lista_lineas: List[str]) -> None:
        """Sobrescribe el archivo completo con las líneas proporcionadas."""
        try:
            with open(self.ruta, "w", encoding='utf-8') as f:
                for linea in lista_lineas:
                    f.write(linea + '\n')
            print(f"Archivo '{self.ruta}' sobrescrito.")
        except Exception as e:
            print(f"ERROR FATAL al sobrescribir '{self.ruta}': {e}")
            # Re-lanzar para que Admin lo maneje o mostrar messagebox
            raise IOError(f"No se pudo guardar en {self.ruta}") from e

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
        if not isinstance(cliente, Cliente) or self.get_cliente(cliente.id): return False
        self.clientes.append(cliente); self.tiquetes[cliente.id] = []
        print(f"Cliente '{cliente.nombre}' (ID: {cliente.id}) añadido.")
        return True
    def get_cliente(self, id_cliente: str) -> Optional[Cliente]:
        for c in self.clientes:
            if c.id == id_cliente: return c
        return None

    def cargar_funciones_desde_archivo(self) -> int:
        """Carga funciones desde MOVIE_DATA_FILE, aplicando límite de 2 por sala POR DÍA."""
        funciones_cargadas_count = 0
        print(f"Cargando funciones desde '{self.controlador_funciones.ruta}'...")
        registros = self.controlador_funciones.leer()
        if not registros: print("Archivo de funciones vacío."); return 0

        # Limpiar programación anterior
        for sala in self.funciones_diarias: self.funciones_diarias[sala] = []
        
        contador_sala_dia: Dict[Tuple[str, date], int] = {} 

        for i, reg in enumerate(registros):
            if len(reg) >= 4:
                f_str, p_nom, p_gen, s_nom = [campo.strip() for campo in reg[:4]]
                try:
                    fecha_dt = datetime.strptime(f_str, DATE_FORMAT_FILE)
                    fecha_obj = fecha_dt.date() # Obtener solo la fecha (sin hora) para contar
                    
                    teatro_p = self.teatros.get(s_nom)
                    if not teatro_p: raise ValueError(f"Teatro '{s_nom}' inválido")
                    if s_nom not in DEFAULT_THEATER_NAMES: raise KeyError(f"Sala '{s_nom}' no reconocida")

                    key_contador = (s_nom, fecha_obj)

                    contador_sala_dia.setdefault(key_contador, 0) 
                    
                    if contador_sala_dia[key_contador] >= 2:
                        continue # Saltar si ya hay 2 para esta sala/día

                    # Si no se ha alcanzado el límite, procesar y añadir
                    pelicula = Pelicula(p_nom, p_gen)
                    funcion = Funcion(fecha_dt, pelicula, teatro_p)
                    self.funciones_diarias[s_nom].append(funcion)
                    contador_sala_dia[key_contador] += 1 # Incrementar contador para esta sala/día
                    funciones_cargadas_count += 1
                    
                except (ValueError, KeyError) as e: print(f"Error L.{i+1} func: {reg} -> {e}")
                except Exception as e: print(f"Error inesperado L.{i+1} func: {reg} -> {e}")
            else: print(f"Adv L.{i+1} func: Formato incorrecto: {reg}")
            
        print(f"Se cargaron {funciones_cargadas_count} funciones.") 
        return funciones_cargadas_count

    def _cargar_y_aplicar_reservas(self) -> None:
        """Lee tickets.txt y marca asientos como ocupados en funciones en memoria."""
        print(f"Cargando y aplicando reservas desde '{TICKET_DATA_FILE}'...")
        reservas_guardadas = self.controlador_tiquetes.leer()
        reservas_aplicadas = 0
        funciones_map = { (f.fecha, f.teatro_funcion.nombre, f.pelicula.nombre): f 
                          for lista in self.funciones_diarias.values() for f in lista }
        if not reservas_guardadas: print("No hay reservas guardadas."); return
        for i, record in enumerate(reservas_guardadas):
            if len(record) >= 4: # Necesita 4 campos guardados
                fecha_str, nombre_sala, nombre_peli, asiento_id = [r.strip() for r in record[:4]]
                try:
                    fecha_dt = datetime.strptime(fecha_str, DATE_FORMAT_FILE)
                    key = (fecha_dt, nombre_sala, nombre_peli)
                    funcion = funciones_map.get(key)
                    if funcion:
                        asiento = funcion.obtener_asiento_por_id(asiento_id)
                        if asiento and asiento.está_disponible():
                            asiento.reservar(); reservas_aplicadas += 1
                except ValueError as e: print(f"Error parse Tkt L.{i+1}: {record} -> {e}")
                except Exception as e: print(f"Error inesperado Tkt L.{i+1}: {record} -> {e}")
            else: print(f"Adv Tkt L.{i+1}: Formato incorrecto: {record}")
        print(f"Se aplicaron {reservas_aplicadas} reservas desde archivo.")

    def guardar_funciones_a_archivo(self) -> bool:
        """Sobrescribe movies.txt con las funciones actuales en memoria."""
        print(f"Guardando horario en '{MOVIE_DATA_FILE}'...")
        lineas = []
        try:
            for funcion in self.get_todas_las_funciones(): # Obtener lista ordenada
                linea = ";".join([
                    funcion.fecha.strftime(DATE_FORMAT_FILE),
                    funcion.pelicula.nombre,
                    funcion.pelicula.genero,
                    funcion.teatro_funcion.nombre
                ])
                lineas.append(linea)
            self.controlador_funciones.sobrescribir(lineas)
            return True
        except Exception as e:
            print(f"ERROR FATAL al guardar funciones: {e}")
            messagebox.showerror("Error Guardando", f"No se pudo guardar horario:\n{e}")
            return False

    def add_new_funcion(self, fecha: datetime, pelicula: Pelicula, sala_nombre: str) -> Tuple[bool, str]:
        """Añade una nueva función a la memoria si es válida."""
        if sala_nombre not in self.teatros:
            return False, f"Sala '{sala_nombre}' no existe."
        teatro_plantilla = self.teatros[sala_nombre]
        
        # Validar límite de 2 por día/sala
        count_dia = sum(1 for f in self.funciones_diarias[sala_nombre] if f.fecha.date() == fecha.date())
        if count_dia >= 2:
            return False, f"Ya existen 2 funciones para '{sala_nombre}' en {fecha.strftime('%d/%m/%Y')}."
        
        nueva_funcion = Funcion(fecha, pelicula, teatro_plantilla)
        self.funciones_diarias[sala_nombre].append(nueva_funcion)
        print(f"Nueva función añadida a memoria: {nueva_funcion}")
        return True, "Función añadida (Guarde el horario para persistir)."

    def delete_funcion(self, funcion_a_eliminar: Funcion) -> Tuple[bool, str]:
        """Elimina una función de memoria si no tiene tickets vendidos en archivo."""
        # Verificar si hay tickets en archivo para esta función
        print(f"Verificando tickets antes de eliminar: {funcion_a_eliminar}...")
        formato_fecha_hora = funcion_a_eliminar.fecha.strftime(DATE_FORMAT_FILE)
        sala = funcion_a_eliminar.teatro_funcion.nombre
        peli = funcion_a_eliminar.pelicula.nombre
        try:
            reservas = self.controlador_tiquetes.leer()
            for record in reservas:
                 if len(record) >= 4:
                     f_str, s_str, p_str, _ = [r.strip() for r in record[:4]]
                     if f_str == formato_fecha_hora and s_str == sala and p_str == peli:
                          msg = "No se puede eliminar: existen tickets registrados."
                          print(msg); return False, msg
        except Exception as e:
            msg = f"Error leyendo archivo de tickets para validación: {e}"
            print(msg); return False, msg

        # Si no hay tickets, eliminar de memoria
        if sala in self.funciones_diarias:
            try:
                self.funciones_diarias[sala].remove(funcion_a_eliminar)
                print(f"Función eliminada de memoria: {funcion_a_eliminar}")
                return True, "Función eliminada (Guarde el horario para persistir)."
            except ValueError:
                 msg = "Error: Función no encontrada en lista interna."; print(msg); return False, msg
        else:
             msg = f"Error: Sala '{sala}' no encontrada."; print(msg); return False, msg

    def comprar_tiquetes(self, funcion: Funcion, cliente: Cliente, ids_asientos: List[str], precio: float) -> List[Tiquete]:
        """Procesa compra, reserva asientos y guarda registro simple."""
        if not isinstance(funcion, Funcion) or not isinstance(cliente, Cliente): raise TypeError("Args inválidos.")
        if not ids_asientos: raise ValueError("Seleccione asiento(s).")
        asientos_obj = []
        for id_a in ids_asientos:
            a = funcion.obtener_asiento_por_id(id_a)
            if not a: raise ValueError(f"Asiento '{id_a}' no existe.")
            if not a.está_disponible(): raise ValueError(f"Asiento {id_a} no disponible.")
            asientos_obj.append(a)
        tiquetes = []
        try:
            for asiento in asientos_obj:
                asiento.reservar()
                tiquete = Tiquete(precio, funcion, cliente, asiento) 
                tiquetes.append(tiquete)
                if cliente.id not in self.tiquetes: self.tiquetes[cliente.id] = []
                self.tiquetes[cliente.id].append(tiquete)
                self.guardar_tiquete_en_archivo(tiquete) 
            print(f"Compra OK: {len(tiquetes)} tiquetes para {cliente.nombre}.")
            return tiquetes
        except Exception as e:
            print(f"Error compra, revirtiendo: {e}")
            for a in asientos_obj:
                 if not a.está_disponible(): a.desreservar()
            raise ValueError(f"Error procesando compra: {e}")

    def get_funciones_disponibles_por_fecha(self, fecha_consulta: datetime, incluir_ya_empezadas: bool = True) -> List[Funcion]:
        """Obtiene funciones para fecha, filtrando opcionalmente las ya empezadas vs AHORA."""
        tiempo_referencia = datetime.now() if not incluir_ya_empezadas else fecha_consulta.replace(hour=0, minute=0, second=0, microsecond=0)
        
        funciones_del_dia = []
        for lista_f in self.funciones_diarias.values():
            for f in lista_f:
                if f.fecha.date() == fecha_consulta.date() and f.fecha >= tiempo_referencia:
                    funciones_del_dia.append(f)
        return sorted(funciones_del_dia, key=lambda f: f.fecha)

    def get_todas_las_funciones(self) -> List[Funcion]:
        """Devuelve lista plana de todas las funciones cargadas, ordenada."""
        lista = [f for lista in self.funciones_diarias.values() for f in lista]
        lista.sort(key=lambda f: (f.fecha, f.teatro_funcion.nombre))
        print(f"DEBUG Admin: get_todas_las_funciones - Devolviendo {len(lista)} funciones.")
        return lista
        
    def generar_reporte_completo(self) -> List[Dict]:
        """Genera reporte contando asientos ocupados por función."""
        reporte = []
        print("Generando reporte contando asientos ocupados...")
        for lista_func in self.funciones_diarias.values():
            for func in lista_func:
                ocupados = sum(1 for a in func.teatro_funcion.asientos if not a.está_disponible())
                ganancias = ocupados * PRECIO_TIQUETE
                reporte.append({'fecha': func.fecha, 'sala': func.teatro_funcion.nombre,
                                'pelicula': func.pelicula.nombre, 'tiquetes_vendidos': ocupados,
                                'ganancias_totales': ganancias })
        reporte.sort(key=lambda item: (item['fecha'], item['sala']))
        print(f"Reporte generado para {len(reporte)} funciones.")
        return reporte

    def guardar_tiquete_en_archivo(self, tiquete: Tiquete) -> None:
        """Guarda info ESENCIAL (Fecha;Sala;Peli;AsientoID) en tickets.txt."""
        try:
            t_data = [ tiquete.funcion.fecha.strftime(DATE_FORMAT_FILE),
                       tiquete.funcion.teatro_funcion.nombre,
                       tiquete.funcion.pelicula.nombre, tiquete.asiento.id ]
            self.controlador_tiquetes.escribir(t_data)
        except Exception as e: print(f"Error guardando tiquete: {e}")

class TheaterGUI:
    """Interfaz gráfica principal usando ttkbootstrap."""
    def __init__(self, root: ttk.Window, admin_instance: Admin):
        self.root = root; self.admin = admin_instance
        self.funcion_seleccionada: Optional[Funcion] = None
        self.asientos_seleccionados_para_compra: List[Asiento] = []
        self.mapa_widgets_asientos: Dict[str, tk.Button] = {}

        self.root.title(APP_TITLE)

        # Variables Filtro
        self.movie_filter_var = tk.StringVar(value="Todas")
        self.sala_filter_var = tk.StringVar(value="Todas")
        self.include_started_var = tk.BooleanVar(value=False) 
        self.show_all_functions_var = tk.BooleanVar(value=False)

        self._cargar_imagenes_asientos()
        self._setup_gui_layout() # Configura widgets y layout
        self._on_filter_apply() # Carga inicial para hoy

    def _cargar_imagenes_asientos(self):
        """Carga imágenes (fondo opaco blanco #FFFFFF recomendado)."""
        print("Cargando imágenes...")
        try:
            pil_avail = Image.open(SEAT_IMG_AVAILABLE).resize((SEAT_IMG_WIDTH, SEAT_IMG_HEIGHT), Image.Resampling.LANCZOS)
            pil_occup = Image.open(SEAT_IMG_OCCUPIED).resize((SEAT_IMG_WIDTH, SEAT_IMG_HEIGHT), Image.Resampling.LANCZOS)
            pil_select = Image.open(SEAT_IMG_SELECTED).resize((SEAT_IMG_WIDTH, SEAT_IMG_HEIGHT), Image.Resampling.LANCZOS)
            self.img_available = ImageTk.PhotoImage(pil_avail)
            self.img_occupied = ImageTk.PhotoImage(pil_occup)
            self.img_selected = ImageTk.PhotoImage(pil_select)
            print("Imágenes OK.")
        except FileNotFoundError as e:
            msg = f"ERROR CRÍTICO: Falta '{e.filename}'. Fallback texto/color."
            print(msg); messagebox.showerror("Error Imagen", msg); self.img_available=self.img_occupied=self.img_selected=None
        except Exception as e:
            msg = f"Error cargando imágenes: {e}"; print(msg); messagebox.showerror("Error Imagen", msg); self.img_available=self.img_occupied=self.img_selected=None

    def _setup_gui_layout(self) -> None:
        """Configura estructura de widgets y bindings."""
        self.root.rowconfigure(1, weight=1); self.root.columnconfigure(0, weight=1)

        # Frame Superior (Filtros y Acciones)
        filter_frame = ttk.Frame(self.root, padding="10")
        filter_frame.grid(row=0, column=0, sticky='ew')

        # Filtros a la izquierda
        ttk.Label(filter_frame, text="Fecha:").pack(side='left', padx=(0, 5))
        self.date_entry_widget = ttk.DateEntry(filter_frame, firstweekday=0, dateformat=DATE_FORMAT_DATEENTRY, width=12)
        self.date_entry_widget.pack(side='left', padx=5)
        self.date_entry_widget.bind("<<DateEntrySelected>>", self._on_filter_apply)
        self.date_entry_widget.entry.bind("<Return>", self._on_filter_apply)
        self.date_entry_widget.entry.bind("<FocusOut>", self._on_filter_apply)

        ttk.Label(filter_frame, text="Película:").pack(side='left', padx=(10, 5))
        self.movie_combobox = ttk.Combobox(filter_frame, textvariable=self.movie_filter_var, state='disabled', width=25)
        self.movie_combobox['values'] = ["Todas"]; self.movie_combobox.current(0)
        self.movie_combobox.pack(side='left', padx=5)
        self.movie_combobox.bind("<<ComboboxSelected>>", self._on_filter_apply)

        ttk.Label(filter_frame, text="Sala:").pack(side='left', padx=(10, 5))
        self.sala_combobox = ttk.Combobox(filter_frame, textvariable=self.sala_filter_var, state='readonly', width=10)
        self.sala_combobox['values'] = ["Todas"] + DEFAULT_THEATER_NAMES; self.sala_combobox.current(0)
        self.sala_combobox.pack(side='left', padx=5)
        self.sala_combobox.bind("<<ComboboxSelected>>", self._on_filter_apply)
        
        # Espacio flexible para empujar botones a la derecha
        spacer = ttk.Frame(filter_frame)
        spacer.pack(side='left', expand=True, fill='x')

        # Botones Admin y Checkboxes a la derecha
        save_button = ttk.Button(filter_frame, text="Guardar Horario", command=self._guardar_cambios_horario, bootstyle=(WARNING, OUTLINE))
        save_button.pack(side='right', padx=5)

        self.delete_button = ttk.Button(filter_frame, text="Eliminar Función", command=self._eliminar_funcion_seleccionada, state='disabled', bootstyle=(DANGER, OUTLINE))
        self.delete_button.pack(side='right', padx=5)

        add_button = ttk.Button(filter_frame, text="Añadir Función", command=self._abrir_ventana_anadir_funcion, bootstyle=(INFO, OUTLINE))
        add_button.pack(side='right', padx=5)
        
        report_button = ttk.Button(filter_frame, text="Ver Reporte", command=self._mostrar_ventana_reportes, bootstyle=SUCCESS)
        report_button.pack(side='right', padx=5)
        
        show_all_check = ttk.Checkbutton(filter_frame, text="Mostrar Todas", variable=self.show_all_functions_var, command=self._on_toggle_show_all, bootstyle="round-toggle")
        show_all_check.pack(side='right', padx=5)

        self.include_started_check = ttk.Checkbutton(filter_frame, text="Incluir ya empezadas", variable=self.include_started_var, command=self._on_filter_apply, bootstyle="round-toggle")
        self.include_started_check.pack(side='right', padx=5)

        # Frame Principal (PanedWindow)
        main_pane = ttk.PanedWindow(self.root, orient='horizontal'); main_pane.grid(row=1, column=0, sticky='nsew', padx=10, pady=5)
        functions_frame = ttk.Frame(main_pane, padding="5"); main_pane.add(functions_frame, weight=1)
        self.seat_area_frame = ttk.Frame(main_pane, padding="5"); main_pane.add(self.seat_area_frame, weight=3)

        # Treeview en Frame Izquierdo
        ttk.Label(functions_frame, text="Funciones Disponibles", font="-weight bold").pack(pady=5)
        cols = ('pelicula', 'hora', 'sala'); self.functions_treeview = ttk.Treeview(functions_frame, columns=cols, show='headings', height=15, bootstyle=INFO)
        for col, head, wid, anc in [('pelicula','Película',200,'w'), ('hora','Hora',100,'center'), ('sala','Sala',100,'center')]:
            self.functions_treeview.heading(col, text=head); self.functions_treeview.column(col, width=wid, anchor=anc)
        scrollbar = ttk.Scrollbar(functions_frame, orient='vertical', command=self.functions_treeview.yview, bootstyle=ROUND)
        self.functions_treeview.configure(yscrollcommand=scrollbar.set); self.functions_treeview.pack(side='left', fill='both', expand=True); scrollbar.pack(side='right', fill='y')
        self.functions_treeview.bind('<<TreeviewSelect>>', self._on_function_select)

        # Frame Inferior (Compra)
        purchase_status_frame = ttk.Frame(self.root, padding="5 10 5 10"); purchase_status_frame.grid(row=2, column=0, sticky='ew')
        self.purchase_info_label = ttk.Label(purchase_status_frame, text="Seleccione función y asientos.", anchor='w'); self.purchase_info_label.pack(side='left', fill='x', expand=True, padx=5)
        buy_button = ttk.Button(purchase_status_frame, text="Comprar Entradas", command=self._confirm_purchase, bootstyle=SUCCESS); buy_button.pack(side='right', padx=5)
        
        # Estado Inicial Widgets
        if not self.show_all_functions_var.get(): self._set_filter_widgets_state('enable')

    def _on_filter_apply(self, event=None) -> None:
        """Obtiene filtros normales, busca funciones y actualiza GUI, SI 'Mostrar Todas' está apagado."""
        if self.show_all_functions_var.get(): return 
        
        # Leer estado actual del checkbox como valor por defecto
        incluir_empezadas_arg = self.include_started_var.get() 
        try:
            date_str = self.date_entry_widget.entry.get()
            selected_date_obj = datetime.strptime(date_str, DATE_FORMAT_DISPLAY_DATE).date()
            selected_datetime = datetime.combine(selected_date_obj, datetime.min.time())

            movie_filter = self.movie_filter_var.get()
            sala_filter = self.sala_filter_var.get()
            # Leer de nuevo por si cambió durante el parseo de fecha (raro, pero seguro)
            incluir_empezadas_arg = self.include_started_var.get() 

            todas_funciones_dia = self.admin.get_funciones_disponibles_por_fecha(
                selected_datetime, incluir_ya_empezadas=incluir_empezadas_arg)

            self._actualizar_combobox_peliculas(todas_funciones_dia)
            movie_filter = self.movie_filter_var.get() # Re-leer por si cambió

            filtered_functions = self._filtrar_funciones_gui(todas_funciones_dia, movie_filter, sala_filter)
            self._poblar_treeview_funciones(filtered_functions, mostrar_fecha=False)

        except ValueError as e:
            messagebox.showerror("Error de Fecha", f"Formato inválido: '{date_str}'. Use {DATE_FORMAT_DISPLAY_DATE}.\n({e})")
            self._limpiar_vista_funciones_y_asientos(True, True)
        except Exception as e:
            messagebox.showerror("Error Aplicando Filtros", f"Ocurrió un error: {e}")
            self._limpiar_vista_funciones_y_asientos(True, True)

    def _on_function_select(self, event=None) -> None:
        """Manejador para selección en Treeview. Habilita/deshabilita botón Eliminar."""
        selected_items = self.functions_treeview.selection()
        if not selected_items:
            self.funcion_seleccionada = None
            if hasattr(self, 'delete_button'): self.delete_button.config(state='disabled') 
            self._clear_seat_display(); self._update_purchase_info(); return
        
        selected_iid = selected_items[0]
        selected_function = self.function_map.get(selected_iid)
        if selected_function:
            self.funcion_seleccionada = selected_function
            self.asientos_seleccionados_para_compra = []
            if hasattr(self, 'delete_button'): self.delete_button.config(state='normal')
            self._update_seat_display(); self._update_purchase_info()
        else: # Error
            self.funcion_seleccionada = None
            if hasattr(self, 'delete_button'): self.delete_button.config(state='disabled')
            self._clear_seat_display(); self._update_purchase_info()

    def _set_filter_widgets_state(self, state: str) -> None:
        """Habilita/deshabilita filtros normales (DateEntry, Combos, Checkbox Empezadas)."""
        widget_state = 'disabled' if state == 'disabled' else 'normal'
        combo_state = 'disabled' if state == 'disabled' else 'readonly'
        try:
            self.date_entry_widget.configure(state=widget_state)
            can_enable_movie = self.movie_combobox.cget('values') and len(self.movie_combobox.cget('values')) > 1 and state != 'disabled'
            self.movie_combobox.configure(state=combo_state if can_enable_movie else 'disabled')
            self.sala_combobox.configure(state=combo_state)
            self.include_started_check.configure(state=widget_state) 
        except Exception as e: print(f"Adv: Error config. estado filtros: {e}")

    def _on_toggle_show_all(self) -> None:
        """Manejador para checkbox 'Mostrar Todas'."""
        if self.show_all_functions_var.get():
            self._set_filter_widgets_state('disabled'); self._load_all_functions_to_view()
        else:
            self._set_filter_widgets_state('enable'); self._on_filter_apply()

    def _load_all_functions_to_view(self) -> None:
        """Obtiene TODAS las funciones y las muestra."""
        print("Cargando todas las funciones...")
        try:
            todas_las_funciones = self.admin.get_todas_las_funciones()
            self._actualizar_combobox_peliculas(todas_las_funciones)
            print(f"DEBUG GUI: _load_all_functions_to_view - Recibidas {len(todas_las_funciones)} funciones del Admin.")
            self._poblar_treeview_funciones(todas_las_funciones, mostrar_fecha=True)
        except Exception as e: messagebox.showerror("Error", f"Error cargando funciones: {e}"); self._limpiar_vista_funciones_y_asientos(True, True)

    # --- Métodos Helper de GUI ---
    def _actualizar_combobox_peliculas(self, f_list: List[Funcion]) -> None:
        """Actualiza opciones del combobox películas."""
        nombres = ["Todas"]; state_if_options = 'readonly'
        if f_list: nombres.extend(sorted(list(set(f.pelicula.nombre for f in f_list))))
        else: state_if_options = 'disabled'
        
        current = self.movie_filter_var.get()
        self.movie_combobox['values'] = nombres
        self.movie_filter_var.set(current if current in nombres else "Todas")
        # Habilitar/Deshabilitar según opciones Y modo 'Mostrar Todas'
        final_state = state_if_options if not self.show_all_functions_var.get() else 'disabled'
        self.movie_combobox.config(state=final_state)

    def _filtrar_funciones_gui(self, f_list: List[Funcion], mov_f: str, sal_f: str) -> List[Funcion]:
        """Filtra lista según comboboxes."""
        res = f_list
        if mov_f != "Todas": res = [f for f in res if f.pelicula.nombre == mov_f]
        if sal_f != "Todas": res = [f for f in res if f.teatro_funcion.nombre == sal_f]
        return res

    def _poblar_treeview_funciones(self, funciones: List[Funcion], mostrar_fecha: bool = False) -> None:
        """Limpia y puebla el Treeview con la lista de funciones dada."""
        for item in self.functions_treeview.get_children(): 
            self.functions_treeview.delete(item)
        
        self.function_map = {}
        if funciones:
            for i, func in enumerate(funciones): # Usar enumerate para contar
                # Determinar formato de fecha/hora a mostrar
                fmt = DATE_FORMAT_DISPLAY_FULL if mostrar_fecha else DATE_FORMAT_DISPLAY_TIME
                fecha_hora_str = func.fecha.strftime(fmt)
                
                # Preparar valores para la fila
                valores_fila = (func.pelicula.nombre, fecha_hora_str, func.teatro_funcion.nombre) 
                
                try:
                    iid = self.functions_treeview.insert('', 'end', values=valores_fila)
                    # Guardar mapeo para selección posterior
                    self.function_map[iid] = func
                except Exception as e:
                    print(f"  ERROR: Falló inserción fila {i+1} ({valores_fila}): {e}") 
            
            msg = f"Mostrando {len(self.functions_treeview.get_children())} funciones en tabla." # Contar items reales en treeview
        else:
             msg = "No hay funciones para mostrar con los filtros actuales."
             self.functions_treeview.insert('', 'end', values=(msg, "", ""))
        
        print(msg)
        self._limpiar_vista_funciones_y_asientos(clear_functions=False, clear_seats=True) 

    def _limpiar_vista_funciones_y_asientos(self, clear_functions: bool = False, clear_seats: bool = True) -> None:
        """Limpia selectivamente treeview y/o área de asientos."""
        if clear_functions:
            for item in self.functions_treeview.get_children(): self.functions_treeview.delete(item)
            self.function_map = {}; self._actualizar_combobox_peliculas([])
        if clear_seats:
            self._clear_seat_display(); self.funcion_seleccionada = None
            self.asientos_seleccionados_para_compra = []
            self._update_purchase_info()
            if hasattr(self, 'delete_button'): self.delete_button.config(state='disabled')
            if hasattr(self, 'report_vendidos_label'): self.report_vendidos_label.config(text="Vendidos: -")
            if hasattr(self, 'report_ganancias_label'): self.report_ganancias_label.config(text="Ganancias: -")

    def _clear_seat_display(self) -> None:
        """Limpia área de asientos y muestra mensaje."""
        for widget in self.seat_area_frame.winfo_children(): widget.destroy()
        ttk.Label(self.seat_area_frame, text="Seleccione función para ver asientos.").pack(padx=20, pady=50)

    def _update_seat_display(self) -> None:
        """Limpia y redibuja pantalla y asientos."""
        for widget in self.seat_area_frame.winfo_children(): widget.destroy()
        if not self.funcion_seleccionada: self._clear_seat_display(); return

        screen_frame = tk.Frame(self.seat_area_frame, bg='black', height=25)
        screen_frame.pack(side='bottom', fill='x', padx=50, pady=(15, 25))
        screen_frame.pack_propagate(False)
        screen_label = tk.Label(screen_frame, text="PANTALLA", bg='black', fg='white', font=('Calibri', 11, 'bold'))
        screen_label.pack(pady=4)

        self.mostrar_asientos(self.seat_area_frame, self.funcion_seleccionada)

    def mostrar_asientos(self, parent_frame: ttk.Frame, funcion: Funcion) -> None:
        """Dibuja cuadrícula de asientos usando tk.Button y fondo explícito."""
        seats_layout=[11]*2 + [9]*2 + [7]*5 + [5]*1; num_rows=len(seats_layout)
        max_seats=11; num_cols=1+max_seats+1; self.mapa_widgets_asientos={}
        grid_frame = tk.Frame(parent_frame, bg=COLOR_FONDO_ASIENTOS)
        grid_frame.pack(side='top', expand=True, pady=(20, 10))
        idx = 0; asientos_func = funcion.teatro_funcion.asientos
        for r in range(num_rows):
            seats_row = seats_layout[r]; indent = (max_seats - seats_row) // 2
            start_col = 1 + indent; end_col = start_col + seats_row - 1
            for c in range(num_cols):
                widget = None; is_seat_col = start_col <= c <= end_col
                if c == 0 or c == num_cols - 1 or not is_seat_col: # Pasillo o vacío
                    w = 30 if (c == 0 or c == num_cols - 1) else SEAT_IMG_WIDTH + 5
                    widget = tk.Frame(grid_frame, width=w, height=SEAT_IMG_HEIGHT+5, bg=COLOR_FONDO_ASIENTOS)
                elif is_seat_col: # Asiento
                    if idx < len(asientos_func):
                        a=asientos_func[idx]; sel=a in self.asientos_seleccionados_para_compra; disp=a.está_disponible()
                        img=self.img_selected if sel and self.img_selected else self.img_occupied if not disp and self.img_occupied else self.img_available if disp and self.img_available else None
                        btn = None
                        if img:
                            btn = tk.Button(grid_frame, image=img, bg=COLOR_FONDO_ASIENTOS, borderwidth=0, highlightthickness=0, relief='flat', activebackground=COLOR_FONDO_ASIENTOS)
                            btn.image = img
                        else: # Fallback
                            txt=f"[{a.id}]" if sel else a.id; clr="gold" if sel else "red" if not disp else "green"
                            btn = tk.Button(grid_frame, text=txt, fg="white", bg=clr, width=5, height=2, borderwidth=0, relief='flat', activebackground=clr)
                        if btn:
                            btn.config(command=lambda asiento=a, button=btn: self.on_seat_click(asiento, button))
                            btn.bind("<Enter>", self._on_seat_enter); btn.bind("<Leave>", self._on_seat_leave)
                            self.mapa_widgets_asientos[a.id] = btn
                        widget = btn; idx += 1
                    else: widget = tk.Frame(grid_frame, width=SEAT_IMG_WIDTH+5, height=SEAT_IMG_HEIGHT+5, bg="magenta") # Error
                if widget:
                    widget.grid(row=r, column=c, padx=1, pady=1)
                    if isinstance(widget, tk.Frame): widget.pack_propagate(False)

    def _on_seat_enter(self, event): event.widget.config(cursor="hand2")
    def _on_seat_leave(self, event): event.widget.config(cursor="")

    def on_seat_click(self, asiento: Asiento, button: tk.Button) -> None:
        """Manejador de clic en asiento para selección/deselección."""
        if not self.funcion_seleccionada: messagebox.showwarning("Selección Requerida", "Seleccione función."); return
        if self.funcion_seleccionada.fechaLimite_pasada(): messagebox.showwarning("Tiempo Excedido", "Tiempo expiró."); return
        if asiento.está_disponible():
            img_upd = None; txt_upd = None
            if asiento in self.asientos_seleccionados_para_compra: # Deseleccionar
                self.asientos_seleccionados_para_compra.remove(asiento); img_upd = self.img_available; txt_upd = asiento.id
            else: # Seleccionar
                self.asientos_seleccionados_para_compra.append(asiento); img_upd = self.img_selected; txt_upd = f"[{asiento.id}]"
            if img_upd and hasattr(button,'image'): button.config(image=img_upd); button.image = img_upd
            elif not hasattr(button, 'image'): button.config(text=txt_upd) # Fallback texto
        elif asiento not in self.asientos_seleccionados_para_compra: messagebox.showinfo("Asiento Ocupado", f"Asiento {asiento.id} ya ocupado.")
        self._update_purchase_info()

    def _update_purchase_info(self) -> None:
        """Actualiza etiqueta de info de compra."""
        num = len(self.asientos_seleccionados_para_compra)
        if num > 0:
            costo = num * PRECIO_TIQUETE; ids = ", ".join(sorted([a.id for a in self.asientos_seleccionados_para_compra]))
            self.purchase_info_label.config(text=f"Sel: {num} ({ids}) - Total: ${costo:,.0f} COP")
        else: self.purchase_info_label.config(text="Seleccione asientos.")

    def _confirm_purchase(self) -> None:
        """Inicia proceso de compra con validación de cliente."""
        if not self.funcion_seleccionada or not self.asientos_seleccionados_para_compra or self.funcion_seleccionada.fechaLimite_pasada():
             msg = "Seleccione función." if not self.funcion_seleccionada else "Seleccione asientos." if not self.asientos_seleccionados_para_compra else "Tiempo excedido."
             messagebox.showwarning("Acción Requerida", msg); return

        cliente: Optional[Cliente] = None

        # Bucle para obtener/validar ID cliente
        while cliente is None:
            id_cliente = simpledialog.askstring("ID Cliente", "Ingrese ID cliente (10 dígitos numéricos):", parent=self.root)
            if id_cliente is None: return # Canceló
            id_cliente = id_cliente.strip()
            if not (id_cliente.isdigit() and len(id_cliente) == 10): # Validación ID
                messagebox.showerror("ID Inválido", "ID debe ser 10 dígitos numéricos.", parent=self.root); continue
            
            cliente_existente = self.admin.get_cliente(id_cliente)
            if cliente_existente: cliente = cliente_existente; break # Cliente encontrado
            else: # Cliente nuevo, pedir nombre
                while True: 
                     nombre_cliente = simpledialog.askstring("Nombre Nuevo Cliente", f"Cliente ID {id_cliente} no existe.\nIngrese nombre (solo letras/espacios):", parent=self.root)
                     if nombre_cliente is None: return # Canceló
                     nombre_cliente = nombre_cliente.strip()
                     # Validación Nombre (permite unicode y espacios)
                     if nombre_cliente and re.fullmatch(r"[\w\s]+", nombre_cliente, re.UNICODE) and not any(c.isdigit() for c in nombre_cliente):
                         cliente = Cliente(nombre_cliente, id_cliente)
                         self.admin.add_cliente(cliente); break # Sale bucle nombre
                     else: messagebox.showerror("Nombre Inválido", "Nombre solo debe contener letras y espacios.", parent=self.root)
                break # Sale bucle cliente
        if not cliente: return # Si algo falló en el proceso
             
        # Intentar Compra
        try:
            ids_a_comprar = [a.id for a in self.asientos_seleccionados_para_compra]
            self.admin.comprar_tiquetes(self.funcion_seleccionada, cliente, ids_a_comprar, PRECIO_TIQUETE)
            messagebox.showinfo("Compra Exitosa", f"Compra para {cliente.nombre}.\nAsientos: {', '.join(ids_a_comprar)}", parent=self.root)
            self.asientos_seleccionados_para_compra = []
            self._update_purchase_info(); self._update_seat_display() # Limpiar y refrescar
        except (ValueError, TypeError) as e: messagebox.showerror("Error Compra", f"No se pudo completar:\n{e}", parent=self.root)

    def _abrir_ventana_anadir_funcion(self) -> None:
        """Abre una ventana Toplevel para añadir una nueva función."""
        
        add_window = tk.Toplevel(self.root)
        add_window.title("Añadir Nueva Función")
        add_window.transient(self.root); add_window.grab_set()
        center_window(add_window, 400, 280); add_window.resizable(False, False)

        form_frame = ttk.Frame(add_window, padding="15")
        form_frame.pack(expand=True, fill='both')

        # Diccionario para guardar referencias a los widgets de entrada
        fields = {}
        # Definir etiquetas y claves para el diccionario fields
        labels_and_keys = [
            ("Fecha:", "Fecha"), 
            ("Hora (HH:MM):", "Hora"), 
            ("Película:", "Película"), 
            ("Género:", "Género"), 
            ("Sala:", "Sala")
        ]
        
        # Crear etiquetas y campos de entrada
        for i, (label_text, key) in enumerate(labels_and_keys):
            lbl = ttk.Label(form_frame, text=label_text)
            lbl.grid(row=i, column=0, padx=5, pady=6, sticky='w')
            
            entry_widget = None 
            if key == "Fecha":
                entry_widget = ttk.DateEntry(form_frame, width=18, 
                                             dateformat=DATE_FORMAT_DISPLAY_DATE, 
                                             firstweekday=0)
            elif key == "Sala":
                entry_widget = ttk.Combobox(form_frame, values=DEFAULT_THEATER_NAMES, 
                                            state='readonly', width=16)
                if DEFAULT_THEATER_NAMES: entry_widget.current(0) 
            else: # Para Hora, Película, Género
                entry_widget = ttk.Entry(form_frame, width=20)
                
            if entry_widget: # Asegurarse que se creó
                entry_widget.grid(row=i, column=1, padx=5, pady=6, sticky='ew')
                fields[key] = entry_widget # Guardar referencia usando la clave

        def on_save() -> None:
            """Handler interno para guardar desde el formulario."""
            try:
                date_entry_widget = fields['Fecha'] # Obtener el widget DateEntry
                date_str = date_entry_widget.entry.get() # Obtener el texto
                # Parsear usando el formato de display
                fecha_obj = datetime.strptime(date_str, DATE_FORMAT_DISPLAY_DATE).date()
                
                # Obtener y validar hora
                hora_str = fields['Hora'].get().strip()
                # Validar formato HH:MM y parsear
                hora_obj = datetime.strptime(hora_str, "%H:%M").time() 
                
                # Combinar fecha y hora
                fecha_hora_dt = datetime.combine(fecha_obj, hora_obj)

                # Obtener otros campos
                pelicula_nombre = fields['Película'].get().strip()
                pelicula_genero = fields['Género'].get().strip()
                sala_nombre = fields['Sala'].get()

                # Validación básica de campos no vacíos
                if not all([pelicula_nombre, pelicula_genero, sala_nombre, hora_str]):
                     raise ValueError("Todos los campos son requeridos.")
                     
                # Crear objeto Pelicula
                pelicula = Pelicula(pelicula_nombre, pelicula_genero)
                
                # Llamar al método del Admin para añadir (que ya tiene validaciones)
                success, message = self.admin.add_new_funcion(fecha_hora_dt, pelicula, sala_nombre)
                
                if success:
                    messagebox.showinfo("Éxito", message, parent=add_window)
                    add_window.destroy() # Cerrar ventana de añadir
                    # Actualizar la vista principal
                    if self.show_all_functions_var.get():
                        self._load_all_functions_to_view() # Recargar todas si esa vista está activa
                    else:
                        self._on_filter_apply() # Reaplicar filtros normales
                else:
                    messagebox.showerror("Error al Añadir", message, parent=add_window)

            except ValueError as ve: 
                messagebox.showerror("Error de Validación", f"Datos inválidos:\n{ve}", parent=add_window)
            except Exception as ex:
                messagebox.showerror("Error Inesperado", f"Ocurrió un error: {ex}", parent=add_window)

        # Botones de acción en el Toplevel
        button_frame = ttk.Frame(form_frame)
        button_frame.grid(row=len(labels_and_keys), column=0, columnspan=2, pady=(20, 5)) # Aumentar pady superior

        save_btn = ttk.Button(button_frame, text="Guardar Función", command=on_save, bootstyle=SUCCESS)
        cancel_btn = ttk.Button(button_frame, text="Cancelar", command=add_window.destroy, bootstyle=SECONDARY)
        save_btn.pack(side='left', padx=10); cancel_btn.pack(side='right', padx=10)
        
        # Hacer que la ventana espere hasta que se cierre
        add_window.wait_window()

    def _eliminar_funcion_seleccionada(self) -> None:
        """Elimina la función seleccionada (con confirmación y validación)."""
        if not self.funcion_seleccionada: messagebox.showwarning("Sin Selección", "Seleccione función a eliminar."); return
        confirm = messagebox.askyesno("Confirmar", f"¿Eliminar función:\n{self.funcion_seleccionada}?", parent=self.root)
        if confirm:
            success, message = self.admin.delete_funcion(self.funcion_seleccionada)
            if success:
                messagebox.showinfo("Éxito", message); self._on_filter_apply(None) # Refrescar vista actual
            else: messagebox.showerror("Error", message)

    def _guardar_cambios_horario(self) -> None:
        """Guarda el horario actual de memoria a movies.txt."""
        if messagebox.askyesno("Guardar Horario", f"¿Sobrescribir '{MOVIE_DATA_FILE}' con el horario actual?", parent=self.root):
            self.admin.guardar_funciones_a_archivo()

    def _mostrar_ventana_reportes(self) -> None:
        """Crea y muestra ventana modal con tabla de reportes."""
        print("Generando reporte completo...")
        try: datos_reporte = self.admin.generar_reporte_completo()
        except Exception as e: messagebox.showerror("Error Reporte", f"No se pudo generar:\n{e}"); return

        report_window = tk.Toplevel(self.root); report_window.title("Reporte Funciones - Ventas y Ganancias")
        report_width, report_height = 800, 500; center_window(report_window, report_width, report_height)
        report_window.transient(self.root); report_window.grab_set() 

        frame = ttk.Frame(report_window, padding="10"); frame.pack(fill='both', expand=True)
        cols = ('fecha_hora', 'pelicula', 'sala', 'vendidos', 'ganancias')
        report_tree = ttk.Treeview(frame, columns=cols, show='headings', height=18, bootstyle=INFO)
        h = {'fecha_hora':'Fecha/Hora','pelicula':'Película','sala':'Sala','vendidos':'Entradas','ganancias':'Ganancias($COP)'}
        w = {'fecha_hora':150,'pelicula':250,'sala':80,'vendidos':100,'ganancias':120}
        a = {'fecha_hora':'w','pelicula':'w','sala':'center','vendidos':'e','ganancias':'e'}
        for c in cols: report_tree.heading(c, text=h[c]); report_tree.column(c, width=w[c], anchor=a[c])

        total_v, total_g = 0, 0.0
        if datos_reporte:
            for item in datos_reporte:
                f_str = item['fecha'].strftime(DATE_FORMAT_DISPLAY_FULL)
                g_str = f"{item['ganancias_totales']:,.0f}" # Usar .2f
                report_tree.insert('', 'end', values=(f_str, item['pelicula'], item['sala'], item['tiquetes_vendidos'], g_str))
                total_v += item['tiquetes_vendidos']; total_g += item['ganancias_totales']
        else: report_tree.insert('', 'end', values=("No hay datos", "", "", "", ""))

        sbar = ttk.Scrollbar(frame, orient='vertical', command=report_tree.yview, bootstyle=ROUND)
        report_tree.configure(yscrollcommand=sbar.set)
        report_tree.grid(row=0, column=0, sticky='nsew'); sbar.grid(row=0, column=1, sticky='ns')
        frame.rowconfigure(0, weight=1); frame.columnconfigure(0, weight=1)

        total_frame = ttk.Frame(frame, padding="5 0 0 0"); total_frame.grid(row=1, column=0, columnspan=2, sticky='ew', pady=(10,0))
        ttk.Label(total_frame, text=f"Total Vendidas: {total_v}", font="-weight bold", bootstyle=(INFO, INVERSE)).pack(side='left', padx=10, ipadx=8, ipady=5)
        ttk.Label(total_frame, text=f"Ganancias Totales: ${total_g:,.0f} COP", font="-weight bold", bootstyle=(SUCCESS, INVERSE)).pack(side='right', padx=10, ipadx=8, ipady=5) # Usar .2f
        
        ttk.Button(frame, text="Cerrar", command=report_window.destroy, bootstyle=(DANGER, OUTLINE)).grid(row=2, column=0, columnspan=2, pady=10)

def main() -> None:
    """Inicializa Admin, carga datos, aplica tema, centra y ejecuta la GUI."""
    print("Iniciando aplicación Cine...")
    admin = Admin("Cine Cultural Barranquilla")
    admin.cargar_funciones_desde_archivo()
    admin._cargar_y_aplicar_reservas() # Cargar estado persistente

    root = ttk.Window(themename="flatly") 

    try:
        main_width, main_height = map(int, WINDOW_GEOMETRY.split('x'))
        root.withdraw()
        root.title(APP_TITLE) 
        root.update_idletasks() 
        center_window(root, main_width, main_height) 
        root.deiconify()
    except Exception as e:
        print(f"Advertencia: No se pudo parsear/centrar ventana principal: {e}")
        root.title(APP_TITLE)
        root.geometry(WINDOW_GEOMETRY) 

    app = TheaterGUI(root, admin)
    root.mainloop()
    print("Aplicación Cine cerrada.")

if __name__ == "__main__":
    main()