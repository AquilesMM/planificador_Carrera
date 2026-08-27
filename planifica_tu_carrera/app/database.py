"""
database.py
-----------
Capa de acceso a datos. Se encarga exclusivamente de hablar con MySQL
y de traducir las filas de las tablas en estructuras Python simples
(dicts / listas) que después usa `logica.py`.

Ningún cálculo de correlatividades ni de recomendaciones vive acá:
este módulo solo LEE y ESCRIBE datos.
"""

from __future__ import annotations
import mysql.connector
from mysql.connector import Error as MySQLError

# ---------------------------------------------------------------------
# Configuración de conexión.
# Ajustar estos valores según el entorno (o exportarlos como variables
# de entorno si se prefiere).
# ---------------------------------------------------------------------
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "root",
    "database": "planifica_tu_carrera",
}


class ConexionBD:
    """Wrapper chico sobre mysql-connector-python."""

    def __init__(self, config: dict | None = None):
        self.config = config or DB_CONFIG
        self.conn = None

    def conectar(self):
        if self.conn is None or not self.conn.is_connected():
            self.conn = mysql.connector.connect(**self.config)
        return self.conn

    def cerrar(self):
        if self.conn is not None and self.conn.is_connected():
            self.conn.close()
            self.conn = None

    def ejecutar_query(self, query: str, params: tuple = ()) -> list[dict]:
        """SELECT que devuelve una lista de dicts."""
        conn = self.conectar()
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute(query, params)
            return cursor.fetchall()
        finally:
            cursor.close()

    def ejecutar_update(self, query: str, params: tuple = ()) -> int:
        """INSERT/UPDATE/DELETE. Devuelve el id autogenerado (si aplica)."""
        conn = self.conectar()
        cursor = conn.cursor()
        try:
            cursor.execute(query, params)
            conn.commit()
            return cursor.lastrowid
        finally:
            cursor.close()


# ---------------------------------------------------------------------
# Funciones de acceso a datos de alto nivel
# ---------------------------------------------------------------------

def obtener_plan_de_estudios(bd: ConexionBD) -> list[dict]:
    """Devuelve todas las asignaturas ordenadas por nivel y nombre."""
    query = """
        SELECT id_asignatura, codigo, nombre, nivel, horas, es_electiva, es_integradora
        FROM asignatura
        ORDER BY nivel, nombre
    """
    return bd.ejecutar_query(query)


def obtener_correlatividades(bd: ConexionBD) -> list[dict]:
    query = """
        SELECT id_correlatividad, id_asignatura, id_requisito, tipo, estado_requerido
        FROM correlatividad
    """
    return bd.ejecutar_query(query)


def obtener_estudiantes(bd: ConexionBD) -> list[dict]:
    return bd.ejecutar_query("SELECT id_estudiante, nombre FROM estudiante ORDER BY nombre")


def obtener_o_crear_estudiante(bd: ConexionBD, nombre: str) -> int:
    filas = bd.ejecutar_query(
        "SELECT id_estudiante FROM estudiante WHERE nombre = %s", (nombre,)
    )
    if filas:
        return filas[0]["id_estudiante"]
    return bd.ejecutar_update(
        "INSERT INTO estudiante (nombre) VALUES (%s)", (nombre,)
    )


def obtener_situacion_academica(bd: ConexionBD, id_estudiante: int) -> dict[int, str]:
    """Devuelve {id_asignatura: estado}. Lo que no está en la tabla
    se interpreta como 'no_cursada' (se resuelve en logica.py)."""
    filas = bd.ejecutar_query(
        "SELECT id_asignatura, estado FROM situacion_academica WHERE id_estudiante = %s",
        (id_estudiante,),
    )
    return {f["id_asignatura"]: f["estado"] for f in filas}


def guardar_estado_asignatura(bd: ConexionBD, id_estudiante: int, id_asignatura: int, estado: str):
    """Inserta o actualiza el estado de una asignatura para un estudiante."""
    query = """
        INSERT INTO situacion_academica (id_estudiante, id_asignatura, estado)
        VALUES (%s, %s, %s)
        ON DUPLICATE KEY UPDATE estado = VALUES(estado)
    """
    bd.ejecutar_update(query, (id_estudiante, id_asignatura, estado))


def cargar_datos_completos(bd: ConexionBD, id_estudiante: int) -> dict:
    """Punto de entrada único: trae todo lo que necesita `logica.py`
    para un estudiante dado."""
    return {
        "asignaturas": obtener_plan_de_estudios(bd),
        "correlatividades": obtener_correlatividades(bd),
        "situacion": obtener_situacion_academica(bd, id_estudiante),
    }
