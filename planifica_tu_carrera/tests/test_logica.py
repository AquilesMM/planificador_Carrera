"""
Test del motor de lógica (logica.py) usando el plan de estudios OFICIAL
(Diseño Curricular 2023 - FRSR) y el caso de Martín, reproducidos en
memoria (sin necesidad de una base MySQL levantada).

Ejecutar con:  python -m unittest tests/test_logica.py -v
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))
from logica import PlanDeCarrera  # noqa: E402


def _a(id_, codigo, nombre, nivel, horas=4, electiva=False, integradora=False):
    return {
        "id_asignatura": id_, "codigo": codigo, "nombre": nombre,
        "nivel": nivel, "horas": horas, "es_electiva": electiva,
        "es_integradora": integradora,
    }


# Subconjunto del plan oficial suficiente para probar el caso de Martín
# (Primer, Segundo y parte de Tercer Nivel).
ASIGNATURAS = [
    _a(1, "1", "Análisis Matemático I", 1, 10),
    _a(2, "2", "Álgebra y Geometría Analítica", 1, 10),
    _a(3, "3", "Física I", 1, 10),
    _a(5, "5", "Lógica y Estructuras Discretas", 1, 6),
    _a(6, "6", "Algoritmo y Estructura de Datos", 1, 5),
    _a(7, "7", "Arquitectura de Computadoras", 1, 8),
    _a(8, "8", "Sistemas y Procesos de Negocios", 1, 3),
    _a(80, "O.1", "Seminario de Introducción al Idioma Inglés I", 1, 2),
    _a(9, "9", "Análisis Matemático II", 2, 5),
    _a(10, "10", "Física II", 2, 10),
    _a(13, "13", "Sintaxis y Semántica de los Lenguajes", 2, 4),
    _a(14, "14", "Paradigmas de Programación", 2, 4),
    _a(15, "15", "Sistemas Operativos", 2, 4),
    _a(16, "16", "Análisis de Sistemas de Información", 2, 5, integradora=True),
    _a(19, "19", "Base de Datos", 3, 4),
    _a(20, "20", "Desarrollo de Software", 3, 4),
]

CORRELATIVIDADES = [
    {"id_asignatura": 9, "id_requisito": 1, "tipo": "cursar", "estado_requerido": "regular"},
    {"id_asignatura": 9, "id_requisito": 2, "tipo": "cursar", "estado_requerido": "regular"},
    {"id_asignatura": 10, "id_requisito": 1, "tipo": "cursar", "estado_requerido": "regular"},
    {"id_asignatura": 10, "id_requisito": 3, "tipo": "cursar", "estado_requerido": "regular"},
    {"id_asignatura": 13, "id_requisito": 5, "tipo": "cursar", "estado_requerido": "regular"},
    {"id_asignatura": 13, "id_requisito": 6, "tipo": "cursar", "estado_requerido": "regular"},
    {"id_asignatura": 14, "id_requisito": 5, "tipo": "cursar", "estado_requerido": "regular"},
    {"id_asignatura": 14, "id_requisito": 6, "tipo": "cursar", "estado_requerido": "regular"},
    {"id_asignatura": 15, "id_requisito": 7, "tipo": "cursar", "estado_requerido": "regular"},
    {"id_asignatura": 16, "id_requisito": 6, "tipo": "cursar", "estado_requerido": "regular"},
    {"id_asignatura": 16, "id_requisito": 8, "tipo": "cursar", "estado_requerido": "regular"},
    {"id_asignatura": 19, "id_requisito": 13, "tipo": "cursar", "estado_requerido": "regular"},
    {"id_asignatura": 19, "id_requisito": 16, "tipo": "cursar", "estado_requerido": "regular"},
    {"id_asignatura": 19, "id_requisito": 5, "tipo": "rendir", "estado_requerido": "aprobada"},
    {"id_asignatura": 19, "id_requisito": 6, "tipo": "rendir", "estado_requerido": "aprobada"},
    {"id_asignatura": 20, "id_requisito": 14, "tipo": "cursar", "estado_requerido": "regular"},
    {"id_asignatura": 20, "id_requisito": 16, "tipo": "cursar", "estado_requerido": "regular"},
]

# Caso de Martín (según el enunciado de la actividad)
SITUACION_MARTIN = {
    6: "no_regularizada",  # Algoritmo y Estructura de Datos
    1: "regular",          # Análisis Matemático I
    3: "regular",          # Física I
    2: "aprobada",
    5: "aprobada",
    7: "aprobada",
    8: "aprobada",
    80: "aprobada",
}


class TestCasoMartin(unittest.TestCase):
    def setUp(self):
        self.plan = PlanDeCarrera(ASIGNATURAS, CORRELATIVIDADES, SITUACION_MARTIN)

    def test_puede_cursar_analisis_matematico_ii(self):
        # AM II requiere AM I y AyGA regularizadas -> Martín cumple
        puede, _ = self.plan.puede_cursar(9)
        self.assertTrue(puede)

    def test_puede_cursar_fisica_ii(self):
        # Física II requiere AM I y Física I regularizadas -> cumple
        puede, _ = self.plan.puede_cursar(10)
        self.assertTrue(puede)

    def test_no_puede_cursar_sintaxis_y_semantica(self):
        # Requiere Algoritmo y Estructura de Datos regularizada -> Martín NO la tiene
        puede, bloqueos = self.plan.puede_cursar(13)
        self.assertFalse(puede)
        self.assertEqual(bloqueos[0].nombre_requisito, "Algoritmo y Estructura de Datos")

    def test_puede_cursar_sistemas_operativos(self):
        # Requiere Arquitectura de Computadoras regularizada -> Martín la tiene APROBADA
        # (aprobada también habilita cursar)
        puede, _ = self.plan.puede_cursar(15)
        self.assertTrue(puede)

    def test_debe_recursar_algoritmo_y_estructura_de_datos(self):
        recursar = [a.nombre for a in self.plan.materias_a_recursar()]
        self.assertIn("Algoritmo y Estructura de Datos", recursar)

    def test_finales_pendientes(self):
        finales = {a.nombre for a in self.plan.materias_con_final_pendiente()}
        self.assertEqual(finales, {"Análisis Matemático I", "Física I"})

    def test_impacto_futuro_algoritmo_y_estructura_de_datos(self):
        # AED (no regularizada) condiciona: Sintaxis y Semántica, Paradigmas
        # de Programación (cursar) y Análisis de Sistemas de Información
        # (cursar), y transitivamente Base de Datos y Desarrollo de Software.
        afectadas = {a.nombre for a in self.plan.impacto_futuro(6)}
        esperado = {
            "Sintaxis y Semántica de los Lenguajes",
            "Paradigmas de Programación",
            "Análisis de Sistemas de Información",
            "Base de Datos",
            "Desarrollo de Software",
        }
        self.assertEqual(afectadas, esperado)

    def test_avance_general(self):
        avance = self.plan.avance_general()
        self.assertEqual(avance["aprobadas"], 5)  # 2,5,7,8,O.1
        self.assertEqual(avance["total_materias"], len(ASIGNATURAS))

    def test_genera_tres_alternativas(self):
        alternativas = self.plan.generar_alternativas()
        self.assertEqual(len(alternativas), 3)


if __name__ == "__main__":
    unittest.main()
