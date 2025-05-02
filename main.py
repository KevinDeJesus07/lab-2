# -*- coding: utf-8 -*-
"""
Cine Cultural Barranquilla - Sistema de Gestión y Reservas

Descripción:
Interfaz gráfica (GUI) para la gestión de un cine, usando ttkbootstrap.
Permite visualizar funciones filtradas por fecha/película/sala, seleccionar
asientos de forma interactiva y comprar tiquetes con validación de cliente.
Las reservas se guardan en 'tickets.txt' para persistencia básica.

Desarrollo:
- Python 3.x
- Bibliotecas requeridas:
  pip install Pillow ttkbootstrap tkcalendar
- Archivos necesarios (mismo directorio):
  - movies.txt: Datos de funciones (Formato: DD/MM/YYYY - HH:MM;Película;Género;Sala)
  - tickets.txt: (Se crea automáticamente) Guarda las reservas.
  - seat_available.png: Imagen asiento disponible (40x40, fondo opaco #FFFFFF RECOMENDADO)
  - seat_occupied.png: Imagen asiento ocupado (40x40, fondo opaco #FFFFFF RECOMENDADO)
  - seat_selected.png: Imagen asiento seleccionado (40x40, fondo opaco #FFFFFF RECOMENDADO)

Autores:
    - Kevin De Jesús Romero Incer
    - Mateo
    - Alfredo
    (Adaptado por Asistente AI)

Fecha: 2025-05-01
"""

import tkinter as tk
import ttkbootstrap as ttk # Usar ttkbootstrap para tema y widgets mejorados
from ttkbootstrap.constants import * # Importar constantes si se usan bootstyles específicos
from tkinter import messagebox, simpledialog
from datetime import datetime, timedelta, date
from typing import List, Optional, Dict, Tuple
from PIL import Image, ImageTk  # Necesita Pillow
# Ya no se usa tkcalendar -> from tkcalendar import DateEntry
import copy
import os
import re # Importar re para validación de nombre

# --- Constantes ---
APP_TITLE = "Cine Cultural Barranquilla - Taquilla"
WINDOW_GEOMETRY = "1280x768"
# --- IMPORTANTE: Usar blanco opaco en imágenes y aquí ---
COLOR_FONDO_ASIENTOS = '#FFFFFF' 

# Archivos de datos
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
# Formato consistente para leer/escribir fechas en archivos
DATE_FORMAT_FILE = '%d/%m/%Y - %H:%M' 
# Formato Python strftime para mostrar fechas en GUI (si es diferente)
DATE_FORMAT_DISPLAY_FULL = '%d/%m/%Y %H:%M' 
DATE_FORMAT_DISPLAY_DATE = '%d/%m/%Y' 
DATE_FORMAT_DISPLAY_TIME = '%H:%M' 
# Formato que entiende ttk.DateEntry (usando códigos Python strftime ahora)
DATE_FORMAT_DATEENTRY = DATE_FORMAT_DISPLAY_DATE # Ej: '%d/%m/%Y'

# --- Función Auxiliar para Centrar Ventanas ---
def center_window(window, width, height):
    """Calcula y aplica la geometría para centrar una ventana en la pantalla."""
    try:
        # Obtener dimensiones de la pantalla desde la ventana dada
        screen_width = window.winfo_screenwidth()
        screen_height = window.winfo_screenheight()

        # Calcular coordenadas X, Y para la esquina superior izquierda
        x = (screen_width / 2) - (width / 2)
        y = (screen_height / 2) - (height / 2)

        # Aplicar la geometría (convertir coords a entero)
        window.geometry(f'{width}x{height}+{int(x)}+{int(y)}')
        print(f"Ventana centrada: {width}x{height} en ({int(x)}, {int(y)})")
    except Exception as e:
        print(f"Advertencia: No se pudo centrar la ventana ({e}). Usando tamaño por defecto.")
        # Aplicar solo tamaño si falla el centrado
        window.geometry(f'{width}x{height}')

# --- Clases de Modelo de Datos ---

class Asiento:
    """Representa un único asiento en una sala de cine."""
    def __init__(self, id_asiento: str):
        """Inicializa un asiento con ID y estado disponible."""
        self.id = id_asiento
        self.disponible = True

    def está_disponible(self) -> bool:
        """Verifica si el asiento está disponible."""
        return self.disponible

    def reservar(self) -> None:
        """Marca el asiento como ocupado (no disponible)."""
        if not self.disponible:
            print(f"Advertencia: Intento de reservar asiento {self.id} ya ocupado.")
        self.disponible = False

    def desreservar(self) -> None:
        """Marca el asiento como disponible."""
        self.disponible = True # No necesita verificar estado previo

    def __str__(self) -> str:
        """Representación corta del asiento."""
        return f"Asiento({self.id}, {'Disp' if self.disponible else 'Ocup'})"

    def __repr__(self) -> str:
        """Representación oficial para depuración."""
        return f"Asiento(id='{self.id}')"

class Teatro:
    """Representa una plantilla de sala de cine con una lista de asientos."""
    def __init__(self, nombre: str, cantidad_asientos: int = DEFAULT_SEATS_PER_THEATER):
        """Inicializa una sala con nombre y asientos generados."""
        self.nombre = nombre
        self.asientos: List[Asiento] = self._generar_asientos(cantidad_asientos)

    def _generar_asientos(self, cantidad: int) -> List[Asiento]:
        """Genera la lista inicial de objetos Asiento (método privado)."""
        # Nota: IDs generados (A1..J8) son básicos. El layout visual es independiente.
        asientos_generados = []
        filas = "ABCDEFGHIJ"
        if cantidad <= 0: return []
        
        # Cálculo simple, puede no llenar exactamente si no es divisible o hay < 10 asientos
        asientos_por_fila = max(1, cantidad // len(filas)) 

        count = 0
        for fila in filas:
            for num in range(1, asientos_por_fila + 1):
                if count < cantidad:
                    asientos_generados.append(Asiento(f"{fila}{num}"))
                    count += 1
                else: break
            if count >= cantidad: break
        
        # Relleno de seguridad si el cálculo falló
        while len(asientos_generados) < cantidad:
             asientos_generados.append(Asiento(f"Extra{len(asientos_generados) + 1}"))
        return asientos_generados

    def obtener_asiento_por_id(self, id_asiento: str) -> Optional[Asiento]:
        """Busca un asiento por su ID en esta plantilla."""
        for asiento in self.asientos:
            if asiento.id == id_asiento: return asiento
        return None

    def reiniciar(self) -> None:
        """Marca todos los asientos de esta plantilla como disponibles."""
        for asiento in self.asientos: asiento.desreservar()

    def __str__(self) -> str:
        """Representación textual del teatro."""
        return f"Teatro({self.nombre}, Asientos: {len(self.asientos)})"

class Pelicula:
    """Representa una película con su nombre y género."""
    def __init__(self, nombre: str, genero: str):
        """Inicializa la película."""
        self.nombre = nombre
        self.genero = genero

    def obtener_informacion(self) -> str:
        """Devuelve nombre y género."""
        return f"{self.nombre} ({self.genero})"

    def __str__(self) -> str:
        """Representación textual."""
        return self.obtener_informacion()

class Funcion:
    """Representa una proyección específica con estado de asientos independiente."""
    def __init__(self, fecha: datetime, pelicula: Pelicula, teatro_plantilla: Teatro):
        """Inicializa la función, creando copia profunda del teatro."""
        self.pelicula = pelicula
        self.teatro_funcion = copy.deepcopy(teatro_plantilla) # Copia independiente
        self.fecha = fecha
        self.fechaLimite = fecha + timedelta(minutes=30) # Límite para comprar

    def obtener_informacion(self) -> str:
        """Devuelve detalles de la función (película, sala, hora)."""
        return f"{self.pelicula.nombre} en {self.teatro_funcion.nombre} - {self.fecha.strftime(DATE_FORMAT_DISPLAY_TIME)}"

    def fechaLimite_pasada(self) -> bool:
        """Verifica si ya es tarde para comprar (30 min post-inicio)."""
        return datetime.now() > self.fechaLimite

    def obtener_asientos_disponibles(self) -> List[Asiento]:
         """Obtiene asientos disponibles para ESTA función."""
         return [a for a in self.teatro_funcion.asientos if a.está_disponible()]

    def obtener_asiento_por_id(self, id_asiento: str) -> Optional[Asiento]:
         """Busca un asiento por ID DENTRO del estado de esta función."""
         for asiento in self.teatro_funcion.asientos:
              if asiento.id == id_asiento: return asiento
         return None

    def esta_disponible_en_fecha(self, tiempoDeReferencia: datetime) -> bool:
        """Verifica si la función no ha comenzado respecto a un tiempo."""
        return self.fecha >= tiempoDeReferencia

    def __str__(self) -> str:
        """Representación textual corta."""
        return self.obtener_informacion()

class Cliente:
    """Representa a un cliente del cine."""
    def __init__(self, nombre: str, id_cliente: str):
        """Inicializa con nombre e ID."""
        self.nombre = nombre
        self.id = id_cliente

    def __str__(self) -> str:
        """Representación textual."""
        return f"Cliente({self.nombre}, ID: {self.id})"

class Tiquete:
    """Representa un tiquete comprado."""
    # --- CORREGIDO: Acepta objeto Cliente ---
    def __init__(self, precio: float, funcion: Funcion, cliente: Cliente, asiento: Asiento):
        """Inicializa tiquete, guardando referencia al cliente."""
        self.precio = precio
        self.funcion = funcion
        self.cliente = cliente 
        self.asiento = asiento

    def obtener_informacion(self) -> str:
        """Devuelve detalles completos del tiquete."""
        return (
            f"Tiquete para {self.funcion.obtener_informacion()}\n"
            f"Cliente: {self.cliente.nombre} (ID: {self.cliente.id})\n"
            f"Asiento: {self.asiento.id}\n"
            f"Precio: ${self.precio:,.2f} COP"
        )

    def __str__(self) -> str:
        """Representación textual corta."""
        return f"Tiquete({self.funcion.pelicula.nombre}, Asiento: {self.asiento.id}, Cliente: {self.cliente.nombre})"

# --- Clases de Lógica y Control ---

class ControladorDeArchivos:
    """Gestiona lectura/escritura simple en archivos delimitados por ';'."""
    def __init__(self, ruta: str):
        """Inicializa y crea el archivo si no existe."""
        self.ruta = ruta
        if not os.path.exists(self.ruta):
            try:
                with open(self.ruta, "w", encoding='utf-8') as f: f.write("")
                print(f"Archivo '{self.ruta}' creado.")
            except Exception as e: print(f"Error creando archivo '{self.ruta}': {e}")

    def leer(self) -> List[List[str]]:
        """Lee y parsea líneas del archivo."""
        try:
            with open(self.ruta, "r", encoding='utf-8') as archivo:
                return [linea.strip().split(";") for linea in archivo if linea.strip()]
        except FileNotFoundError: return []
        except Exception as e: print(f"Error leyendo '{self.ruta}': {e}"); return []

    def escribir(self, datos: List[str]) -> None:
        """Añade una línea (campos unidos por ';') al archivo."""
        try:
            datos_str = [str(d) for d in datos] # Asegurar strings
            with open(self.ruta, "a", encoding='utf-8') as archivo:
                archivo.write(';'.join(datos_str) + '\n')
        except Exception as e: print(f"Error escribiendo en '{self.ruta}': {e}")

class Admin:
    """Clase principal para lógica de negocio y gestión de datos."""
    def __init__(self, nombre_cine: str):
        """Inicializa el Admin, teatros y controladores."""
        self.nombre = nombre_cine
        self.clientes: List[Cliente] = []
        self.teatros: Dict[str, Teatro] = {n: Teatro(n) for n in DEFAULT_THEATER_NAMES}
        self.funciones_diarias: Dict[str, List[Funcion]] = {n: [] for n in DEFAULT_THEATER_NAMES}
        self.tiquetes: Dict[str, List[Tiquete]] = {} # id_cliente -> Lista Tiquetes (en memoria)

        self.controlador_funciones = ControladorDeArchivos(MOVIE_DATA_FILE)
        self.controlador_tiquetes = ControladorDeArchivos(TICKET_DATA_FILE)

    def add_cliente(self, cliente: Cliente) -> bool:
        """Añade un cliente si no existe. Devuelve True si fue añadido."""
        if not isinstance(cliente, Cliente) or self.get_cliente(cliente.id): return False
        self.clientes.append(cliente)
        if cliente.id not in self.tiquetes: self.tiquetes[cliente.id] = []
        print(f"Cliente '{cliente.nombre}' (ID: {cliente.id}) añadido.")
        return True

    def get_cliente(self, id_cliente: str) -> Optional[Cliente]:
        """Busca cliente por ID."""
        for cliente in self.clientes:
            if cliente.id == id_cliente: return cliente
        return None

    def cargar_funciones_desde_archivo(self) -> int:
        """Carga funciones desde movies.txt, aplicando límite por sala."""
        count = 0
        print(f"Cargando funciones desde '{self.controlador_funciones.ruta}'...")
        registros = self.controlador_funciones.leer()
        if not registros: print("Archivo de funciones vacío."); return 0

        # Limpiar y preparar contadores
        for sala in self.funciones_diarias: self.funciones_diarias[sala] = []
        contador_sala = {sala: 0 for sala in DEFAULT_THEATER_NAMES}

        for i, reg in enumerate(registros):
            if len(reg) >= 4:
                f_str, p_nom, p_gen, s_nom = [campo.strip() for campo in reg[:4]]
                try:
                    fecha = datetime.strptime(f_str, DATE_FORMAT_FILE)
                    teatro_p = self.teatros.get(s_nom)
                    if not teatro_p: raise ValueError(f"Teatro '{s_nom}' inválido")
                    
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
        """Procesa compra, reserva asientos en la copia de la función y guarda tiquete simple."""
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
        
        try: # Reservar y crear/guardar después de validar todos
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

    def get_funciones_disponibles_por_fecha(self, fecha: datetime, incluir_ya_empezadas: bool = True) -> List[Funcion]:
        """
        Obtiene funciones para una fecha específica. Si incluir_ya_empezadas es False,
        filtra las funciones cuya hora de inicio sea anterior a la hora ACTUAL.

        Args:
            fecha (datetime): La fecha para la cual buscar funciones.
            incluir_ya_empezadas (bool): Si es False, se excluyen las funciones
                                         que ya comenzaron según la hora actual.
                                         Si es True (default), se incluyen todas las del día.

        Returns:
            List[Funcion]: Lista ordenada por hora de las funciones encontradas.
        """
        tiempo_referencia: datetime

        # --- LÓGICA DE TIEMPO DE REFERENCIA MODIFICADA ---
        if not incluir_ya_empezadas:
            # Si NO queremos incluir las empezadas, comparamos contra AHORA MISMO
            tiempo_referencia = datetime.now()
        else:
            # Si SÍ queremos incluir empezadas (o es para una fecha diferente),
            # comparamos contra el inicio del día seleccionado para obtener todas.
            tiempo_referencia = fecha.replace(hour=0, minute=0, second=0, microsecond=0)
        # --- Fin lógica modificada ---

        # (Opcional) Prints de depuración si sigues necesitándolos
        # print("-" * 20)
        # print(f"DEBUG (Nueva Lógica): Buscando para fecha: {fecha.date()}")
        # print(f"DEBUG (Nueva Lógica): incluir_ya_empezadas: {incluir_ya_empezadas}")
        # print(f"DEBUG (Nueva Lógica): tiempo_referencia usado: {tiempo_referencia.strftime('%Y-%m-%d %H:%M:%S')}")
        # print("-" * 20)

        funciones_del_dia: List[Funcion] = []
        for lista_funciones in self.funciones_diarias.values():
            for funcion in lista_funciones:
                # Filtrar primero por fecha
                if funcion.fecha.date() == fecha.date():
                    # Luego filtrar por hora usando el tiempo_referencia determinado
                    if funcion.esta_disponible_en_fecha(tiempo_referencia): # func.fecha >= tiempo_referencia
                        funciones_del_dia.append(funcion)

        return sorted(funciones_del_dia, key=lambda f: f.fecha)
    
    # --- CORREGIDO: Versión simple para guardar estado de reserva ---
    def guardar_tiquete_en_archivo(self, tiquete: Tiquete) -> None:
        """Guarda info ESENCIAL (Fecha;Sala;Peli;AsientoID) en tickets.txt."""
        try:
            tiquete_data_simple = [
                tiquete.funcion.fecha.strftime(DATE_FORMAT_FILE),
                tiquete.funcion.teatro_funcion.nombre,
                tiquete.funcion.pelicula.nombre,
                tiquete.asiento.id,
            ]
            self.controlador_tiquetes.escribir(tiquete_data_simple)
        except Exception as e:
            print(f"Error guardando tiquete simple en '{TICKET_DATA_FILE}': {e}")

    # --- CORREGIDO: Nombre y lógica para cargar/aplicar reservas ---
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
            if len(record) >= 4: # Necesita 4 campos guardados por guardar_tiquete...
                fecha_str, nombre_sala, nombre_peli, asiento_id = [r.strip() for r in record[:4]]
                try:
                    fecha_dt = datetime.strptime(fecha_str, DATE_FORMAT_FILE)
                    key_busqueda = (fecha_dt, nombre_sala, nombre_peli)
                    funcion_encontrada = funciones_map.get(key_busqueda)

                    if funcion_encontrada:
                        asiento = funcion_encontrada.obtener_asiento_por_id(asiento_id)
                        if asiento and asiento.está_disponible():
                            asiento.reservar()
                            reservas_aplicadas += 1
                        # else: Asiento no existe o ya ocupado, ignorar
                    # else: Función no encontrada, ignorar
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
        """
        Genera datos de ventas y ganancias para TODAS las funciones cargadas,
        basándose en los asientos marcados como ocupados en cada función.
        """
        reporte_final = []
        print("Generando reporte contando asientos ocupados...") # Log para confirmar

        # Iterar sobre todas las funciones cargadas en memoria
        for lista_funciones_sala in self.funciones_diarias.values():
            for funcion in lista_funciones_sala:
                
                # Contar asientos ocupados para ESTA función específica
                asientos_ocupados = 0
                for asiento in funcion.teatro_funcion.asientos:
                    if not asiento.está_disponible():
                        asientos_ocupados += 1
                        
                # Calcular ganancias basadas en asientos ocupados y precio fijo
                ganancias_totales = asientos_ocupados * PRECIO_TIQUETE
                            
                # Añadir datos al reporte final
                reporte_final.append({
                    # 'funcion_info': str(funcion), # Podemos quitar esto si no se usa en la tabla
                    'fecha': funcion.fecha,
                    'sala': funcion.teatro_funcion.nombre,
                    'pelicula': funcion.pelicula.nombre,
                    'tiquetes_vendidos': asientos_ocupados, # <- Basado en conteo
                    'ganancias_totales': ganancias_totales # <- Basado en conteo * precio
                })
                
        # Ordenar el reporte por fecha y luego sala
        reporte_final.sort(key=lambda item: (item['fecha'], item['sala']))
        
        print(f"Reporte generado para {len(reporte_final)} funciones.")
        return reporte_final

# --- Clase de Interfaz Gráfica (TheaterGUI) ---

class TheaterGUI:
    """Interfaz gráfica principal usando ttkbootstrap."""
    def __init__(self, root: ttk.Window, admin_instance: Admin): # Acepta ttk.Window
        """Inicializa la GUI con ttkbootstrap."""
        self.root = root
        self.admin = admin_instance
        self.funcion_seleccionada: Optional[Funcion] = None
        self.asientos_seleccionados_para_compra: List[Asiento] = []
        self.mapa_widgets_asientos: Dict[str, tk.Button] = {} # Usaremos tk.Button para asientos

        self.root.title(APP_TITLE)
        self.root.geometry(WINDOW_GEOMETRY)

        # Variables para filtros
        self.movie_filter_var = tk.StringVar(value="Todas")
        self.sala_filter_var = tk.StringVar(value="Todas")
        self.include_started_var = tk.BooleanVar(value=False) # True = Incluir empezadas (Default)
        self.show_all_functions_var = tk.BooleanVar(value=False)

        # Carga de imágenes (RECOMENDADO: fondo opaco COLOR_FONDO_ASIENTOS)
        self._cargar_imagenes_asientos()

        # Configuración de layout y widgets
        self._setup_gui_layout()

        # Carga inicial de funciones para hoy
        self._on_filter_apply()

    def _cargar_imagenes_asientos(self) -> None:
        """Carga y prepara las imágenes de los asientos."""
        # (Asumiendo que las imágenes ya tienen fondo opaco blanco #FFFFFF)
        try:
            pil_avail = Image.open(SEAT_IMG_AVAILABLE).resize((SEAT_IMG_WIDTH, SEAT_IMG_HEIGHT), Image.Resampling.LANCZOS)
            pil_occup = Image.open(SEAT_IMG_OCCUPIED).resize((SEAT_IMG_WIDTH, SEAT_IMG_HEIGHT), Image.Resampling.LANCZOS)
            pil_select = Image.open(SEAT_IMG_SELECTED).resize((SEAT_IMG_WIDTH, SEAT_IMG_HEIGHT), Image.Resampling.LANCZOS)
            self.img_available = ImageTk.PhotoImage(pil_avail)
            self.img_occupied = ImageTk.PhotoImage(pil_occup)
            self.img_selected = ImageTk.PhotoImage(pil_select)
            print("Imágenes de asientos cargadas.")
        except FileNotFoundError as e:
            msg = f"ERROR CRÍTICO: Falta archivo de imagen '{e.filename}'.\nLa aplicación podría no funcionar correctamente."
            print(msg)
            messagebox.showerror("Error de Imagen", msg)
            self.img_available = self.img_occupied = self.img_selected = None
        except Exception as e:
            msg = f"Error inesperado cargando imágenes: {e}"
            print(msg)
            messagebox.showerror("Error de Imagen", msg)
            self.img_available = self.img_occupied = self.img_selected = None

    # --- Métodos de Configuración de GUI ---

    def _setup_gui_layout(self) -> None:
        """Configura la estructura principal de widgets de la GUI, incluyendo filtros y bindings."""
        self.root.rowconfigure(1, weight=1)
        self.root.columnconfigure(0, weight=1)

        # --- Frame Superior (Filtros) ---
        filter_frame = ttk.Frame(self.root, padding="10")
        filter_frame.grid(row=0, column=0, sticky='ew')

        # Filtro de Fecha
        ttk.Label(filter_frame, text="Fecha:").pack(side='left', padx=(0, 5))
        date_format_python = DATE_FORMAT_DISPLAY_DATE # Usar formato de display '%d/%m/%Y'
        self.date_entry_widget = ttk.DateEntry(
            filter_frame,
            firstweekday=0,
            dateformat=date_format_python, # Pasar formato Python
            width=12
        )
        self.date_entry_widget.pack(side='left', padx=5)
        
        # --- CORRECCIÓN: Bindings para actualizar al cambiar fecha ---
        # 1. Al seleccionar del calendario popup
        self.date_entry_widget.bind("<<DateEntrySelected>>", lambda event: self._on_filter_apply())
        # 2. Al presionar Enter en la caja de texto
        self.date_entry_widget.entry.bind("<Return>", lambda event: self._on_filter_apply())
        # 3. Al perder el foco la caja de texto (hacer clic fuera)
        self.date_entry_widget.entry.bind("<FocusOut>", lambda event: self._on_filter_apply())


        # Filtro de Película
        ttk.Label(filter_frame, text="Película:").pack(side='left', padx=(15, 5))
        self.movie_combobox = ttk.Combobox(filter_frame, textvariable=self.movie_filter_var,
                                           state='disabled', width=30)
        self.movie_combobox['values'] = ["Todas"]
        self.movie_combobox.current(0)
        self.movie_combobox.pack(side='left', padx=5)
        self.movie_combobox.bind("<<ComboboxSelected>>", lambda event: self._on_filter_apply())

        # Filtro de Sala
        ttk.Label(filter_frame, text="Sala:").pack(side='left', padx=(15, 5))
        self.sala_combobox = ttk.Combobox(filter_frame, textvariable=self.sala_filter_var,
                                          state='readonly', width=15)
        self.sala_combobox['values'] = ["Todas"] + DEFAULT_THEATER_NAMES
        self.sala_combobox.current(0)
        self.sala_combobox.pack(side='left', padx=5)
        self.sala_combobox.bind("<<ComboboxSelected>>", lambda event: self._on_filter_apply())

        # Checkbox "Mostrar Todas"
        show_all_check = ttk.Checkbutton(
            filter_frame, text="Mostrar Todas", variable=self.show_all_functions_var,
            command=self._on_toggle_show_all, bootstyle="round-toggle")
        show_all_check.pack(side='right', padx=15)

        # Checkbox "Incluir Empezadas"
        self.include_started_check = ttk.Checkbutton(
            filter_frame, text="Incluir ya empezadas", variable=self.include_started_var,
            command=self._on_filter_apply, bootstyle="round-toggle")
        self.include_started_check.pack(side='right', padx=5)

        # --- Botón para abrir ventana de reportes ---
        report_button = ttk.Button(
            filter_frame, 
            text="Ver Reporte", 
            command=self._mostrar_ventana_reportes, # Llama a un nuevo método
            bootstyle=SUCCESS # Un estilo diferente (ej. gris)
        )
        # Empaquetarlo, quizás a la izquierda o al final
        report_button.pack(side='left', padx=20) 

        # --- Frame Principal (PanedWindow) ---
        main_pane = ttk.PanedWindow(self.root, orient='horizontal')
        main_pane.grid(row=1, column=0, sticky='nsew', padx=10, pady=5)

        # --- Frame Izquierdo (Funciones) ---
        functions_frame = ttk.Frame(main_pane, padding="5")
        main_pane.add(functions_frame, weight=1)
        ttk.Label(functions_frame, text="Funciones Disponibles", font="-weight bold").pack(pady=5)
        cols = ('pelicula', 'hora', 'sala')
        self.functions_treeview = ttk.Treeview(functions_frame, columns=cols, show='headings', height=15, bootstyle=INFO)
        self.functions_treeview.heading('pelicula', text='Película')
        self.functions_treeview.heading('hora', text='Hora')
        self.functions_treeview.heading('sala', text='Sala')
        self.functions_treeview.column('pelicula', width=200, anchor='w')
        self.functions_treeview.column('hora', width=100, anchor='center')
        self.functions_treeview.column('sala', width=100, anchor='center')
        scrollbar = ttk.Scrollbar(functions_frame, orient='vertical', command=self.functions_treeview.yview, bootstyle=ROUND)
        self.functions_treeview.configure(yscrollcommand=scrollbar.set)
        self.functions_treeview.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        self.functions_treeview.bind('<<TreeviewSelect>>', self._on_function_select)

        # --- Frame Derecho (Asientos) ---
        self.seat_area_frame = ttk.Frame(main_pane, padding="5")
        main_pane.add(self.seat_area_frame, weight=3)

        # --- Frame Inferior (Compra) ---
        purchase_status_frame = ttk.Frame(self.root, padding="5 10 5 10")
        purchase_status_frame.grid(row=2, column=0, sticky='ew')
        self.purchase_info_label = ttk.Label(purchase_status_frame, text="Seleccione función y asientos.", anchor='w')
        self.purchase_info_label.pack(side='left', fill='x', expand=True, padx=5)
        buy_button = ttk.Button(purchase_status_frame, text="Comprar Entradas",
                                command=self._confirm_purchase, bootstyle=SUCCESS)
        buy_button.pack(side='right', padx=5)
        
        # --- Estado Inicial Widgets ---
        if not self.show_all_functions_var.get():
             self._set_filter_widgets_state('enable')

    def _mostrar_ventana_reportes(self) -> None:
        """Crea y muestra una nueva ventana con la tabla de reportes de funciones."""

        print("Generando reporte completo...")
        # 1. Obtener datos del Admin
        try:
            datos_reporte = self.admin.generar_reporte_completo()
        except Exception as e:
            messagebox.showerror("Error Reporte", f"No se pudo generar el reporte:\n{e}")
            return

        # 2. Crear ventana Toplevel (ventana secundaria)
        report_window = tk.Toplevel(self.root)
        report_window.title("Reporte de Funciones - Ventas y Ganancias")
        report_window.geometry("800x500") # Tamaño inicial para la ventana de reporte
        report_window.transient(self.root) # Asociarla a la ventana principal
        report_window.grab_set() # Hacerla modal (opcional, bloquea interacción con principal)

        # --- Centrar Ventana de Reporte ---
        report_width = 800 # Ancho deseado para esta ventana
        report_height = 500 # Alto deseado
        try:
            # Para Toplevels, update_idletasks suele ser suficiente
            report_window.update_idletasks() 
            center_window(report_window, report_width, report_height)
        except Exception as e:
             print(f"Advertencia: No se pudo centrar ventana de reporte: {e}")
             report_window.geometry(f"{report_width}x{report_height}") # Fallback

        # Hacerla modal y asociarla a la principal
        report_window.transient(self.root) 
        report_window.grab_set()

        # 3. Crear Frame principal para la ventana de reporte
        frame = ttk.Frame(report_window, padding="10")
        frame.pack(fill='both', expand=True)

        # 4. Crear Treeview para la tabla de reporte
        cols = ('fecha_hora', 'pelicula', 'sala', 'vendidos', 'ganancias')
        report_tree = ttk.Treeview(frame, columns=cols, show='headings', height=18, bootstyle=INFO)

        # Configurar cabeceras
        report_tree.heading('fecha_hora', text='Fecha y Hora')
        report_tree.heading('pelicula', text='Película')
        report_tree.heading('sala', text='Sala')
        report_tree.heading('vendidos', text='Entradas Vendidas')
        report_tree.heading('ganancias', text='Ganancias ($ COP)')

        # Configurar columnas (ancho y alineación)
        report_tree.column('fecha_hora', width=150, anchor='w')
        report_tree.column('pelicula', width=250, anchor='w')
        report_tree.column('sala', width=80, anchor='center')
        report_tree.column('vendidos', width=100, anchor='e') # Alinear números a la derecha
        report_tree.column('ganancias', width=120, anchor='e') # Alinear números a la derecha

        # 5. Poblar Treeview con los datos
        total_vendidos = 0
        total_ganancias = 0.0
        if datos_reporte:
            for item_reporte in datos_reporte:
                fecha_str = item_reporte['fecha'].strftime(DATE_FORMAT_DISPLAY_FULL)
                ganancia_str = f"{item_reporte['ganancias_totales']:,.0f}" # Formato moneda

                report_tree.insert('', 'end', values=(
                    fecha_str,
                    item_reporte['pelicula'],
                    item_reporte['sala'],
                    item_reporte['tiquetes_vendidos'],
                    ganancia_str
                ))
                total_vendidos += item_reporte['tiquetes_vendidos']
                total_ganancias += item_reporte['ganancias_totales']
        else:
            report_tree.insert('', 'end', values=("No hay datos de funciones", "", "", "", ""))

        # 6. Añadir Scrollbar
        scrollbar = ttk.Scrollbar(frame, orient='vertical', command=report_tree.yview, bootstyle=ROUND)
        report_tree.configure(yscrollcommand=scrollbar.set)

        report_tree.grid(row=0, column=0, sticky='nsew')
        scrollbar.grid(row=0, column=1, sticky='ns')
        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)

        # 7. (Opcional) Mostrar Totales
        total_frame = ttk.Frame(frame, padding="5 0 0 0")
        total_frame.grid(row=1, column=0, columnspan=2, sticky='ew', pady=(10,0))

        ttk.Label(
            total_frame, 
            text=f"Entradas: {total_vendidos}", 
            font="-weight bold",
            bootstyle=(INFO, INVERSE)
            ).pack(side='left', padx=10, ipadx=8, ipady=3)
        ttk.Label(
            total_frame, 
            text=f"Ganancias: ${total_ganancias:,.0f} COP", 
            font="-weight bold",
            bootstyle=(SUCCESS, INVERSE)
            ).pack(side='right', padx=10, ipadx=8, ipady=5)

        # 8. (Opcional) Botón Cerrar
        close_button = ttk.Button(frame, text="Cerrar", command=report_window.destroy, bootstyle=DANGER)
        close_button.grid(row=2, column=0, columnspan=2, pady=10)

    # --- Métodos de Actualización y Eventos ---

    def _on_filter_apply(self, event=None) -> None:
        """Obtiene todos los filtros, busca funciones y actualiza GUI, SI 'Mostrar Todas' está apagado."""
        # No hacer nada si estamos en modo 'Mostrar Todas'
        if self.show_all_functions_var.get():
            return 

        # --- CORRECCIÓN: Inicializar variable antes del try ---
        incluir_empezadas_arg = self.include_started_var.get() # Leer valor actual como default

        try:
            # 1. Obtener Fecha
            date_str = self.date_entry_widget.entry.get()
            date_format_python = DATE_FORMAT_DISPLAY_DATE # Ej: '%d/%m/%Y'
            selected_date_obj = datetime.strptime(date_str, date_format_python).date()
            selected_datetime = datetime.combine(selected_date_obj, datetime.min.time())
            # print(f"Filtrando funciones para: {selected_datetime.strftime('%Y-%m-%d')}") # Log opcional

            # --- Habilitar/Deshabilitar Checkbox "Incluir Empezadas" ---
            # (Esta lógica ahora se ejecuta siempre que se aplica el filtro)
            es_hoy = (selected_date_obj == datetime.now().date())
            estado_checkbox_empezadas = 'normal' if es_hoy else 'disabled' # Solo habilitado si es hoy? O siempre habilitado? Vamos a dejarlo siempre habilitado por ahora, ya que la lógica aplica a cualquier día.
            # --- REVISADO: Mantener habilitado a menos que 'Mostrar Todas' esté activo ---
            # El estado se maneja en _set_filter_widgets_state basado en show_all_var
            # No necesitamos deshabilitarlo aquí basado en 'es_hoy'.
            # try: self.include_started_check.configure(state=estado_checkbox_empezadas) ...

            # --- 2. Obtener otros filtros ---
            movie_filter = self.movie_filter_var.get()
            sala_filter = self.sala_filter_var.get()
            # Leer el estado actual del checkbox (puede haber cambiado desde inicio del método si hubo error antes)
            incluir_empezadas_arg = self.include_started_var.get() 
            print(f"Filtros aplicados: Fecha={date_str}, Peli='{movie_filter}', Sala='{sala_filter}', IncluirEmpezadas={incluir_empezadas_arg}")

            # --- 3. Obtener Funciones del Admin ---
            todas_funciones_dia = self.admin.get_funciones_disponibles_por_fecha(
                selected_datetime, incluir_ya_empezadas=incluir_empezadas_arg)

            # --- 4. Actualizar Combobox Películas ---
            self._actualizar_combobox_peliculas(todas_funciones_dia)
            movie_filter = self.movie_filter_var.get() # Re-leer por si se reseteó

            # --- 5. Filtrar Funciones en GUI ---
            filtered_functions = self._filtrar_funciones_gui(todas_funciones_dia, movie_filter, sala_filter)

            # --- 6. Actualizar Treeview ---
            self._poblar_treeview_funciones(filtered_functions, mostrar_fecha=False)

        except ValueError as e:
            # Error si el formato de fecha en la caja es inválido
            messagebox.showerror("Error de Fecha", f"Formato de fecha inválido: '{date_str}'. Use {date_format_python}.\n({e})")
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
            print(f"Función seleccionada: {self.funcion_seleccionada}")
            self.asientos_seleccionados_para_compra = []
            self._update_seat_display()
            self._update_purchase_info()
        else:
            print(f"Error: No se encontró objeto Funcion para iid {selected_iid}")
            self.funcion_seleccionada = None
            self._clear_seat_display(); self._update_purchase_info()

    def _set_filter_widgets_state(self, state: str) -> None:
        """Habilita ('enable') o deshabilita ('disabled') los filtros normales."""
        disabled_state = 'disabled' if state == 'disabled' else 'normal'
        combo_state = 'disabled' if state == 'disabled' else 'readonly'
        try:
            self.date_entry_widget.configure(state=disabled_state)
            # Habilitar movie combobox solo si tiene opciones cargadas
            if self.movie_combobox['values'] and len(self.movie_combobox['values']) > 1 and state != 'disabled':
                 self.movie_combobox.configure(state=combo_state)
            else:
                 self.movie_combobox.configure(state='disabled') 
            self.sala_combobox.configure(state=combo_state)
            # Usar 'normal' para habilitar Checkbutton
            self.include_started_check.configure(state=disabled_state) 
        except Exception as e: # Captura más genérica por si widget no existe aún
             print(f"Advertencia: Error configurando estado widgets filtro: {e}")

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
            # Actualizar combobox de películas con todas las películas existentes
            self._actualizar_combobox_peliculas(todas_las_funciones)
            # Poblar treeview con todas, mostrando fecha y hora
            self._poblar_treeview_funciones(todas_las_funciones, mostrar_fecha=True)
        except Exception as e:
            messagebox.showerror("Error Cargando Funciones", f"Error: {e}")
            self._limpiar_vista_funciones_y_asientos()

    # --- Métodos Helper de GUI ---

    def _actualizar_combobox_peliculas(self, lista_funciones: List[Funcion]) -> None:
         """Actualiza las opciones del combobox de películas."""
         if lista_funciones:
             nombres = sorted(list(set(f.pelicula.nombre for f in lista_funciones)))
             current_selection = self.movie_filter_var.get()
             self.movie_combobox['values'] = ["Todas"] + nombres
             if current_selection in self.movie_combobox['values']:
                 self.movie_filter_var.set(current_selection)
             else:
                 self.movie_filter_var.set("Todas")
             # Habilitar si no está deshabilitado por 'Mostrar Todas'
             if not self.show_all_functions_var.get():
                  self.movie_combobox.config(state='readonly')
         else:
             self.movie_combobox['values'] = ["Todas"]
             self.movie_combobox.config(state='disabled')
             self.movie_filter_var.set("Todas")

    def _filtrar_funciones_gui(self, funciones: List[Funcion], movie_filter: str, sala_filter: str) -> List[Funcion]:
         """Filtra una lista de funciones basado en los criterios de la GUI."""
         resultado = funciones
         if movie_filter != "Todas":
             resultado = [f for f in resultado if f.pelicula.nombre == movie_filter]
         if sala_filter != "Todas":
             resultado = [f for f in resultado if f.teatro_funcion.nombre == sala_filter]
         return resultado

    def _poblar_treeview_funciones(self, funciones: List[Funcion], mostrar_fecha: bool = False) -> None:
        """Limpia y puebla el Treeview con la lista de funciones dada."""
        for item in self.functions_treeview.get_children(): self.functions_treeview.delete(item)
        self.function_map = {} # Resetear mapa iid -> func
        
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
        self._limpiar_vista_funciones_y_asientos(clear_seats=True) # Limpiar asientos al cambiar lista

    def _limpiar_vista_funciones_y_asientos(self, clear_functions: bool = False, clear_seats: bool = True) -> None:
        """Limpia selectivamente el treeview y/o el área de asientos."""
        if clear_functions:
            for item in self.functions_treeview.get_children(): self.functions_treeview.delete(item)
            self.function_map = {}
        if clear_seats:
            self._clear_seat_display()
            self.funcion_seleccionada = None
            self.asientos_seleccionados_para_compra = []
            self._update_purchase_info()

    def _clear_seat_display(self) -> None:
        """Limpia el área de asientos y muestra mensaje por defecto."""
        for widget in self.seat_area_frame.winfo_children(): widget.destroy()
        ttk.Label(self.seat_area_frame, text="Seleccione una función para ver los asientos.").pack(padx=20, pady=50)

    def _update_seat_display(self) -> None:
        """Limpia y redibuja pantalla y asientos para la función seleccionada."""
        for widget in self.seat_area_frame.winfo_children(): widget.destroy()
        if not self.funcion_seleccionada:
            self._clear_seat_display(); return

        # --- CORREGIDO: Usar tk.Frame/tk.Label para pantalla ---
        screen_frame = tk.Frame(self.seat_area_frame, bg='black', height=25) # Un poco más alta
        screen_frame.pack(side='bottom', fill='x', padx=50, pady=(15, 25))
        screen_frame.pack_propagate(False) 
        screen_label = tk.Label(screen_frame, text="PANTALLA", bg='black', fg='white', font=('Calibri', 11, 'bold')) 
        screen_label.pack(pady=4)

        self.mostrar_asientos(self.seat_area_frame, self.funcion_seleccionada)

    # --- CORREGIDO: Usa tk.Frame y tk.Button ---
    def mostrar_asientos(self, parent_frame: ttk.Frame, funcion: Funcion) -> None:
        """Dibuja la cuadrícula de asientos usando tk.Button y fondo explícito."""
        seats_layout = [11]*2 + [9]*2 + [7]*5 + [5]*1
        num_rows = len(seats_layout)
        max_seats_in_row = 11
        num_grid_cols = 1 + max_seats_in_row + 1
        
        self.mapa_widgets_asientos = {}

        # --- CORREGIDO: Usar tk.Frame para asegurar bg ---
        grid_frame = tk.Frame(parent_frame, bg=COLOR_FONDO_ASIENTOS) 
        grid_frame.pack(side='top', expand=True, pady=(20, 10))

        asiento_index = 0
        asientos_de_la_funcion = funcion.teatro_funcion.asientos

        for i in range(num_rows):
            num_seats_this_row = seats_layout[i]
            indent = (max_seats_in_row - num_seats_this_row) // 2
            start_col = 1 + indent
            end_col = start_col + num_seats_this_row - 1

            for j in range(num_grid_cols):
                widget_to_place = None
                
                # Pasillos / Vacíos (usar tk.Frame)
                is_seat_column = start_col <= j <= end_col
                if j == 0 or j == num_grid_cols - 1 or not is_seat_column:
                    widget_to_place = tk.Frame(grid_frame, width=SEAT_IMG_WIDTH+5, height=SEAT_IMG_HEIGHT+5, bg=COLOR_FONDO_ASIENTOS)
                    if j == 0 or j == num_grid_cols - 1: # Pasillos más angostos
                        widget_to_place.config(width=30)
                
                # Asientos (usar tk.Button)
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
                        if img: # Crear botón con imagen
                            seat_btn = tk.Button(grid_frame, image=img,
                                                 bg=COLOR_FONDO_ASIENTOS, borderwidth=0, 
                                                 highlightthickness=0, relief='flat', 
                                                 activebackground=COLOR_FONDO_ASIENTOS)
                            seat_btn.image = img
                        else: # Fallback con texto
                            fb_text = asiento.id
                            if is_selected: fb_text = f"[{asiento.id}]"
                            color = "red" if not is_available else "green"
                            if is_selected: color = "gold" 
                            seat_btn = tk.Button(grid_frame, text=fb_text, fg="white", bg=color,
                                                 width=5, height=2, borderwidth=0, 
                                                 relief='flat', activebackground=color)

                        if seat_btn:
                            seat_btn.config(command=lambda a=asiento, b=seat_btn: self.on_seat_click(a, b))
                            seat_btn.bind("<Enter>", self._on_seat_enter) 
                            seat_btn.bind("<Leave>", self._on_seat_leave) 
                            self.mapa_widgets_asientos[asiento.id] = seat_btn
                        
                        widget_to_place = seat_btn
                        asiento_index += 1
                    else: # Error Layout
                         print(f"Error Layout: Índice {asiento_index} fuera de rango.")
                         widget_to_place = tk.Frame(grid_frame, width=SEAT_IMG_WIDTH+5, height=SEAT_IMG_HEIGHT+5, bg="magenta")

                # Colocar widget
                if widget_to_place:
                    widget_to_place.grid(row=i, column=j, padx=1, pady=1)
                    if isinstance(widget_to_place, tk.Frame):
                         widget_to_place.pack_propagate(False)

    def _on_seat_enter(self, event):
        """Cambia cursor a mano al entrar."""
        event.widget.config(cursor="hand2")

    def _on_seat_leave(self, event):
        """Restaura cursor al salir."""
        event.widget.config(cursor="")

    # --- CORREGIDO: Type hint a tk.Button ---
    def on_seat_click(self, asiento: Asiento, button: tk.Button) -> None:
        """Manejador de clic en asiento para selección/deselección."""
        if not self.funcion_seleccionada:
            messagebox.showwarning("Selección Requerida", "Seleccione una función primero.")
            return
        if self.funcion_seleccionada.fechaLimite_pasada():
             messagebox.showwarning("Tiempo Excedido", "El tiempo para comprar/seleccionar ha expirado.")
             return

        # Actuar solo si el asiento NO está ya comprado (rojo)
        if asiento.está_disponible():
            if asiento in self.asientos_seleccionados_para_compra: # Deseleccionar
                self.asientos_seleccionados_para_compra.remove(asiento)
                img_actualizar = self.img_available
                fb_text = asiento.id
            else: # Seleccionar
                self.asientos_seleccionados_para_compra.append(asiento)
                img_actualizar = self.img_selected
                fb_text = f"[{asiento.id}]"
            
            # Actualizar apariencia
            if img_actualizar:
                 button.config(image=img_actualizar)
                 button.image = img_actualizar
            else: button.config(text=fb_text)
        
        else: # Asiento ya ocupado permanentemente (rojo)
             if asiento not in self.asientos_seleccionados_para_compra: # Evitar msg si se intenta deseleccionar uno ya ocupado (no debería pasar)
                 messagebox.showinfo("Asiento Ocupado", f"El asiento {asiento.id} ya está ocupado.")

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
        # 1. Validaciones básicas
        if not self.funcion_seleccionada or not self.asientos_seleccionados_para_compra or self.funcion_seleccionada.fechaLimite_pasada():
             # Mostrar mensajes apropiados
             if not self.funcion_seleccionada: msg = "Seleccione una función primero."
             elif not self.asientos_seleccionados_para_compra: msg = "Seleccione al menos un asiento."
             else: msg = "Ya no se pueden comprar entradas para esta función (tiempo excedido)."
             messagebox.showwarning("Acción Requerida", msg)
             return

        # --- 2. Obtener y Validar Datos del Cliente ---
        cliente: Optional[Cliente] = None
        while cliente is None: # Bucle hasta obtener cliente válido o cancelar
            id_cliente = simpledialog.askstring("Identificación Cliente", "Ingrese ID cliente (10 dígitos numéricos):", parent=self.root)
            if id_cliente is None: return # Usuario canceló ID

            # Validación ID
            if not id_cliente.isdigit() or len(id_cliente) != 10:
                messagebox.showerror("ID Inválido", "El ID debe contener exactamente 10 dígitos numéricos.")
                continue # Volver a pedir ID

            cliente_existente = self.admin.get_cliente(id_cliente)
            if cliente_existente:
                cliente = cliente_existente # Usar cliente existente
                break # Salir del bucle de cliente

            else: # Cliente nuevo, pedir nombre
                while True: # Bucle para validar nombre
                     nombre_cliente = simpledialog.askstring("Nombre Cliente Nuevo", f"Cliente ID {id_cliente} no encontrado.\nIngrese el nombre (solo letras y espacios):", parent=self.root)
                     if nombre_cliente is None: return # Usuario canceló nombre
                     
                     # Validación Nombre (solo letras y espacios permitidos)
                     if nombre_cliente.strip() and all(c.isalpha() or c.isspace() for c in nombre_cliente):
                         cliente = Cliente(nombre_cliente.strip(), id_cliente)
                         self.admin.add_cliente(cliente)
                         break # Salir del bucle de nombre
                     else:
                          messagebox.showerror("Nombre Inválido", "El nombre solo debe contener letras y espacios, y no puede estar vacío.")
                          # Continuar bucle de nombre
                break # Salir del bucle de cliente si se creó uno nuevo

        # --- 3. Intentar Compra ---
        if not cliente: # Doble chequeo por si algo falló
             messagebox.showerror("Error", "No se pudo obtener la información del cliente.")
             return
             
        try:
            ids_a_comprar = [a.id for a in self.asientos_seleccionados_para_compra]
            tiquetes = self.admin.comprar_tiquetes(self.funcion_seleccionada, cliente, ids_a_comprar, PRECIO_TIQUETE)
            
            # 4. Éxito
            messagebox.showinfo("Compra Exitosa", f"Compra realizada para {cliente.nombre} (ID: {cliente.id}).\nAsientos: {', '.join(ids_a_comprar)}")
            self.asientos_seleccionados_para_compra = []
            self._update_purchase_info()
            self._update_seat_display() # Refrescar

        except (ValueError, TypeError) as e:
             messagebox.showerror("Error en Compra", f"No se pudo completar:\n{e}")

# --- Función Principal ---

def main() -> None:
    """Inicializa Admin, carga datos, aplica tema y ejecuta la GUI."""
    print("Iniciando aplicación Cine...")
    admin = Admin("Cine Cultural Barranquilla")
    admin.cargar_funciones_desde_archivo()
    admin._cargar_y_aplicar_reservas() # Cargar estado persistente

    # Inicializar con ttkbootstrap y tema 'flatly'
    root = ttk.Window(themename="flatly") 

    # --- Centrar Ventana Principal ---
    try:
        # Parsear dimensiones desde la constante WINDOW_GEOMETRY
        main_width, main_height = map(int, WINDOW_GEOMETRY.split('x'))
        # Técnica para centrar antes de mostrar y evitar parpadeo
        root.withdraw()         # Ocultar temporalmente
        root.update_idletasks() # Asegurar que winfo_ esté listo
        center_window(root, main_width, main_height) # Llamar a la función auxiliar
        root.deiconify()        # Mostrar la ventana ya centrada
    except Exception as e:
        print(f"Advertencia: No se pudo parsear/centrar ventana principal: {e}")
        root.geometry(WINDOW_GEOMETRY) # Usar geometría por defecto si falla

    app = TheaterGUI(root, admin)
    root.mainloop()
    print("Aplicación Cine cerrada.")

# --- Punto de Entrada ---
if __name__ == "__main__":
    main()