import tkinter as tk
from tkinter import ttk
from datetime import datetime, timedelta
from typing import List, Optional, Dict

class Asiento:
    def __init__(self, id: str):
        self.id = id
        self.disponible = True

    def está_disponible(self) -> bool:
        return self.disponible

    def reservar(self) -> None:
        if not self.disponible:
            raise ValueError(f"El asiento {self.id} no está disponible")
        self.disponible = False

    def desreservar(self) -> None:
        self.disponible = True

class Teatro:
    def __init__(self, nombre: str, cantidad_asientos: int = 80) -> None:
        self.nombre = nombre
        self.asientos: List[Asiento] = []

        # Asientos con ID: A1, A2, ..., J8
        filas = "ABCDEFGHIJ"
        asientos_por_fila = cantidad_asientos // len(filas)
        for fila in filas:
            for num in range(1, asientos_por_fila + 1):
                asiento_id = f"{fila}{num}"
                self.asientos.append(Asiento(asiento_id))

    def obtener_asientos_disponibles(self) -> List[Asiento]:
        return [asiento for asiento in self.asientos if asiento.está_disponible()]

    def reiniciar(self) -> None:
        for asiento in self.asientos:
            asiento.desreservar()

class Película:
    def __init__(self, nombre: str, género: str) -> None:
        self.nombre = nombre
        self.género = género

    def obtener_información(self) -> str:
        return f"{self.nombre} ({self.género})"

class Función:
    def __init__(self, fecha: datetime, película: Película, teatro: Teatro):
        self.película = película
        self.teatro = teatro
        self.fecha = fecha
        self.fechaLimite = fecha + timedelta(minutes=30)

    def obtener_información(self) -> str:
        return f"{self.película.nombre} en {self.teatro.nombre} - {self.fecha.strftime('%Y-%m-%d %H:%M')}"

    def reiniciar(self) -> None:
        self.teatro.reiniciar()

    def fechaLimite_pasada(self) -> bool:
        return datetime.now() > self.fechaLimite

    def obtener_asientos_disponibles(self):
        return self.teatro.obtener_asientos_disponibles()

    def está_disponible(self, tiempoDeReferencia: datetime) -> bool:
        return self.fecha >= tiempoDeReferencia

class Tiquete:
    def __init__(self, precio: float, función: Función, nombre_cliente: str, asiento: Asiento):
        self.precio = precio
        self.función = función
        self.nombre_cliente = nombre_cliente
        self.asiento = asiento

    def obtener_información(self) -> str:
        return (
            f"Tiquete para {self.función.obtener_información()}\n"
            f"Nombre del cliente: {self.nombre_cliente}\n"
            f"Asiento: {self.asiento.id}\n"
            f"Precio: ${self.precio:.2f}"
        )

class Cliente:
    def __init__(self, nombre: str, id: str):
        self.nombre = nombre
        self.id = id

class ControladorDeArchivos:
    def __init__(self, ruta: str):
        self.ruta = ruta

    def leer(self) -> list[list[str]]:
        try:
            with open(self.ruta, "r", encoding='utf-8') as archivo:
                return [linea.strip().split(",") for linea in archivo if linea.strip()]
        except FileNotFoundError:
            return []

    def escribir(self, datos: list[str]) -> None:
        with open(self.ruta, "a", encoding='utf-8') as archivo:
            linea = ';'.join(datos) + '\n'
            archivo.write(linea)

    def filtrar(self, criterio: str) -> list[list[str]]:
        return [registro for registro in self.leer() if any(criterio in campo for campo in registro)]

class Admin:
    def __init__(self, nombre: str):
        self.nombre = nombre
        self.clientes: List[Cliente] = []
        self.teatros: Dict[str, Teatro] = {
            'Sala 1': Teatro('Sala 1'),
            'Sala 2': Teatro('Sala 2'),
            'Sala 3': Teatro('Sala 3')
        }
        self.funciones_diarias: Dict[str, List[Función]] = {
            'Sala 1': [],
            'Sala 2': [],
            'Sala 3': []
        }
        self.tiquetes: Dict[int, List[Tiquete]] = {}
        self.controlador_de_archivos = ControladorDeArchivos('data/movies.txt')

    def add_cliente(self, cliente: Cliente) -> None:
        self.clientes.append(cliente)
        self.tiquetes[cliente.id] = []

    def get_cliente(self, id_cliente: str) -> Optional[Cliente]:
        for cliente in self.clientes:
            if cliente.id == id_cliente:
                return cliente
        return None

    def asignar_función(self, función: Función) -> None:
        funciones_de_sala = self.funciones_diarias[función.teatro.nombre]
        if len(funciones_de_sala) >= 2:
            raise ValueError(f"El teatro {función.teatro.nombre} ya tiene dos funciones programadas")
        funciones_de_sala.append(función)

    def comprar_tiquetes(self, función: Función, cliente: Cliente, id_asientos: List[str], precio: float) -> List[Tiquete]:
        tiquetes = []
        asientos_disponibles = [asiento for asiento in función.obtener_asientos_disponibles() if asiento.id in id_asientos]
        if len(asientos_disponibles) != len(id_asientos):
            raise ValueError("Algunos asientos no están disponibles")
        for asiento in asientos_disponibles:
            asiento.reservar()
            tiquete = Tiquete(precio, función, cliente.nombre, asiento)
            tiquetes.append(tiquete)
            self.tiquetes[cliente.id].append(tiquete)
            self.guardar_tiquete_en_archivo(tiquete)
        return tiquetes

    def get_tiquetes_por_cliente(self, id_cliente: str) -> List[Tiquete]:
        return self.tiquetes.get(id_cliente, [])

    def cargar_funciones_desde_archivo(self) -> None:
        funciones = []
        for registro in self.controlador_de_archivos.leer():
            if len(registro) >= 4:
                try:
                    fecha = datetime.strptime(registro[0], '%d%m%Y - %H:%M')
                    película = Película(registro[1], registro[2])
                    teatro = self.teatros.get(registro[3])
                    if teatro is None:
                        raise ValueError(f"Teatro {registro[3]} inválido")
                    función = Función(fecha, película, teatro)
                    funciones.append(función)
                    self.asignar_función(función)
                except ValueError as e:
                    print(f"Error al cargar la función: {e}")
        return funciones

    def get_funciones_por_fecha(self, fecha: datetime, incluir_desde_ahora: bool = False) -> List[Función]:
        tiempoDeReferencia = datetime.now() if incluir_desde_ahora and fecha.date() == datetime.now().date() else fecha.replace(hour=0, minute=0)
        todas_las_funciones = []
        for funciones in self.funciones_diarias.values():
            funciones_coincidentes = [
                función for función in funciones
                if función.fecha.date() == fecha.date() and función.está_disponible(tiempoDeReferencia)
            ]
            todas_las_funciones.extend(funciones_coincidentes)
        return sorted(todas_las_funciones, key=lambda x: x.fecha)

    def guardar_tiquete_en_archivo(self, tiquete: Tiquete) -> None:
        tiquete_data = [
            tiquete.función.fecha.strftime('%Y-%m-%d %H:%M'),
            tiquete.función.película.nombre,
            tiquete.función.teatro.nombre,
            tiquete.asiento.id,
            tiquete.nombre_cliente,
            f"{tiquete.precio:.2f}"
        ]
        self.controlador_de_archivos.escribir(tiquete_data)

    def mostrar_tablero(self, teatro: Teatro) -> None:
        filas = "ABCDEFGHIJ"
        asientos_por_fila = len(teatro.asientos) // len(filas)

        print("\nEstado de los asientos:\n")

        for i, fila in enumerate(filas):
            fila_asientos = teatro.asientos[i * asientos_por_fila:(i + 1) * asientos_por_fila]
            linea = ""
            for asiento in fila_asientos:
                estado = "[ ]" if asiento.está_disponible() else "[X]"
                linea += f"{asiento.id} {estado}  "
            print(linea)

class TheaterGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Cine Cultural Barranquilla")
        self.root.geometry("900x600")

        # Crear 3 salas (Theater) con 80 asientos cada una
        self.salas = [Teatro(f"Sala {i+1}") for i in range(3)]
        self.sala_actual = 0

        # Configurar layout principal
        self.root.rowconfigure(1, weight=1)
        self.root.columnconfigure(0, weight=1)

        # Barra de menú superior
        self.menu_frame = tk.Frame(self.root, bg='#e0e0e0', height=40)
        self.menu_frame.grid(row=0, column=0, sticky='ew')
        self.menu_frame.grid_propagate(False)
        for idx, sala in enumerate(self.salas):
            btn = tk.Button(self.menu_frame, text=sala.nombre, command=lambda i=idx: self.mostrar_sala(i))
            btn.pack(side='left', padx=10, pady=5)

        # Zona dinámica central
        self.content_frame = tk.Frame(self.root, bg='#f8f8f8')
        self.content_frame.grid(row=1, column=0, sticky='nsew')
        self.content_frame.grid_propagate(True)

        # Barra de estado inferior
        self.status_frame = tk.Frame(self.root, bg='#e0e0e0', height=30)
        self.status_frame.grid(row=2, column=0, sticky='ew')
        self.status_frame.grid_propagate(False)
        self.status_label = tk.Label(self.status_frame, text="Listo", anchor='w', bg='#e0e0e0')
        self.status_label.pack(fill='both', padx=10)

        self.mostrar_sala(self.sala_actual)

    def mostrar_sala(self, idx):
        # Limpiar contenido anterior
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        sala = self.salas[idx]
        self.sala_actual = idx
        self.status_label.config(text=f"Mostrando {sala.nombre}")
        self.mostrar_asientos(self.content_frame, sala)

    def mostrar_asientos(self, parent, sala):
        filas = 10
        columnas = 8
        grid_frame = tk.Frame(parent, bg='#f8f8f8')
        grid_frame.pack(expand=True, pady=30, padx=30)
        for fila_idx in range(filas):
            for col_idx in range(columnas):
                asiento = sala.asientos[fila_idx * columnas + col_idx]
                color = 'green' if asiento.está_disponible() else 'red'
                btn = tk.Button(grid_frame, width=2, height=1, bg=color, state='disabled', relief='ridge')
                btn.grid(row=fila_idx, column=col_idx, padx=8, pady=8)

def main():
    root = tk.Tk()
    app = TheaterGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main() 