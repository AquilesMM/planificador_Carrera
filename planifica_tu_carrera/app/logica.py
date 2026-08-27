"""
logica.py
---------
Motor de negocio de "Planificá tu Carrera".

Este módulo NO sabe nada de MySQL ni de Tkinter: trabaja únicamente
sobre estructuras Python (listas de dicts) que le entrega
`database.py`. Esto permite testearlo de forma aislada y reutilizarlo
desde cualquier interfaz (GUI, consola, tests).

Estados posibles de una asignatura para un estudiante:
    'aprobada'         -> rindió el final y aprobó
    'regular'          -> cursó y quedó regularizada, final pendiente
    'no_regularizada'  -> cursó pero no logró regularizarla (debe recursar)
    'no_cursada'       -> todavía no la cursó (estado por defecto)

Régimen de correlatividades (según el Diseño Curricular 2023 - FRSR):
    tipo='cursar' + estado_requerido='regular'   -> columna "Cursada":
        para CURSAR esta asignatura, la requisito debe estar regularizada
        (o aprobada, que también habilita).
    tipo='rendir' + estado_requerido='aprobada'  -> columna "Aprobada":
        para RENDIR el final de esta asignatura, la requisito debe
        estar aprobada.
    Caso especial "Proyecto Final": no tiene columna "Aprobada" propia
    (es Integradora, sin final tradicional). Sus filas son todas
    tipo='cursar', pero algunas piden estado_requerido='regular' y
    otras 'aprobada' — el modelo ya lo soporta porque ambos campos son
    independientes.
"""

from __future__ import annotations
from dataclasses import dataclass

ESTADOS_QUE_HABILITAN_CURSAR = {"regular", "aprobada"}


@dataclass
class Asignatura:
    id: int
    codigo: str
    nombre: str
    nivel: int
    horas: int | None
    es_electiva: bool
    es_integradora: bool
    estado: str = "no_cursada"


@dataclass
class Bloqueo:
    """Explica por qué una asignatura no puede cursarse todavía."""
    id_requisito: int
    nombre_requisito: str
    estado_requerido: str   # 'regular' | 'aprobada'
    estado_actual: str


class PlanDeCarrera:
    """
    Representa el plan de estudios + correlatividades + situación
    académica de UN estudiante, ya cargados en memoria, y ofrece toda
    la lógica de negocio pedida por la consigna.
    """

    def __init__(self, asignaturas: list[dict], correlatividades: list[dict],
                 situacion: dict[int, str]):
        self.asignaturas: dict[int, Asignatura] = {}
        for a in asignaturas:
            estado = situacion.get(a["id_asignatura"], "no_cursada")
            self.asignaturas[a["id_asignatura"]] = Asignatura(
                id=a["id_asignatura"],
                codigo=a["codigo"],
                nombre=a["nombre"],
                nivel=a["nivel"],
                horas=a.get("horas"),
                es_electiva=bool(a.get("es_electiva", False)),
                es_integradora=bool(a.get("es_integradora", False)),
                estado=estado,
            )
        self.correlatividades = correlatividades

    # -----------------------------------------------------------------
    # Consultas básicas
    # -----------------------------------------------------------------
    def por_nivel(self) -> dict[int, list[Asignatura]]:
        niveles: dict[int, list[Asignatura]] = {}
        for a in self.asignaturas.values():
            niveles.setdefault(a.nivel, []).append(a)
        for nivel in niveles:
            niveles[nivel].sort(key=lambda x: x.nombre)
        return dict(sorted(niveles.items()))

    def _requisitos(self, id_asignatura: int, tipo: str) -> list[dict]:
        return [c for c in self.correlatividades
                if c["id_asignatura"] == id_asignatura and c["tipo"] == tipo]

    def _cumple_requisito(self, req: dict) -> bool:
        requisito = self.asignaturas[req["id_requisito"]]
        if req["estado_requerido"] == "aprobada":
            return requisito.estado == "aprobada"
        # 'regular' se satisface con 'regular' o con 'aprobada'
        return requisito.estado in ESTADOS_QUE_HABILITAN_CURSAR

    # -----------------------------------------------------------------
    # ¿Puede cursar? / ¿Puede rendir?
    # -----------------------------------------------------------------
    def puede_cursar(self, id_asignatura: int) -> tuple[bool, list[Bloqueo]]:
        bloqueos = []
        for req in self._requisitos(id_asignatura, "cursar"):
            if not self._cumple_requisito(req):
                requisito = self.asignaturas[req["id_requisito"]]
                bloqueos.append(Bloqueo(
                    id_requisito=requisito.id,
                    nombre_requisito=requisito.nombre,
                    estado_requerido=req["estado_requerido"],
                    estado_actual=requisito.estado,
                ))
        return (len(bloqueos) == 0, bloqueos)

    def puede_rendir(self, id_asignatura: int) -> tuple[bool, list[Bloqueo]]:
        bloqueos = []
        for req in self._requisitos(id_asignatura, "rendir"):
            if not self._cumple_requisito(req):
                requisito = self.asignaturas[req["id_requisito"]]
                bloqueos.append(Bloqueo(
                    id_requisito=requisito.id,
                    nombre_requisito=requisito.nombre,
                    estado_requerido=req["estado_requerido"],
                    estado_actual=requisito.estado,
                ))
        return (len(bloqueos) == 0, bloqueos)

    # -----------------------------------------------------------------
    # Listados pedidos por la consigna
    # -----------------------------------------------------------------
    def materias_habilitadas(self) -> list[Asignatura]:
        """Asignaturas que el estudiante puede cursar AHORA (no
        aprobadas ni regulares todavía) y que cumplen correlatividades."""
        resultado = []
        for a in self.asignaturas.values():
            if a.estado in ("aprobada", "regular"):
                continue
            puede, _ = self.puede_cursar(a.id)
            if puede:
                resultado.append(a)
        return sorted(resultado, key=lambda x: (x.nivel, x.nombre))

    def materias_no_habilitadas(self) -> list[tuple[Asignatura, list[Bloqueo]]]:
        """Asignaturas que NO puede cursar todavía, junto con el motivo."""
        resultado = []
        for a in self.asignaturas.values():
            if a.estado in ("aprobada", "regular"):
                continue
            puede, bloqueos = self.puede_cursar(a.id)
            if not puede:
                resultado.append((a, bloqueos))
        return sorted(resultado, key=lambda x: (x[0].nivel, x[0].nombre))

    def materias_con_final_pendiente(self) -> list[Asignatura]:
        return sorted(
            [a for a in self.asignaturas.values() if a.estado == "regular"],
            key=lambda x: (x.nivel, x.nombre),
        )

    def materias_a_recursar(self) -> list[Asignatura]:
        return sorted(
            [a for a in self.asignaturas.values() if a.estado == "no_regularizada"],
            key=lambda x: (x.nivel, x.nombre),
        )

    def avance_general(self) -> dict:
        total = len(self.asignaturas)
        aprobadas = sum(1 for a in self.asignaturas.values() if a.estado == "aprobada")
        regulares = sum(1 for a in self.asignaturas.values() if a.estado == "regular")
        pct = round(100 * aprobadas / total, 1) if total else 0.0
        return {
            "total_materias": total,
            "aprobadas": aprobadas,
            "regulares_con_final_pendiente": regulares,
            "porcentaje_aprobado": pct,
        }

    # -----------------------------------------------------------------
    # Impacto futuro de una materia pendiente / no regularizada
    # -----------------------------------------------------------------
    def impacto_futuro(self, id_asignatura: int) -> list[Asignatura]:
        """
        Devuelve, recorriendo el grafo de correlatividades hacia
        adelante, TODAS las asignaturas (de cualquier nivel posterior)
        cuyo cursado o final dependen -directa o indirectamente- de
        que `id_asignatura` esté regular/aprobada.
        """
        dependientes_directos: dict[int, set[int]] = {}
        for c in self.correlatividades:
            dependientes_directos.setdefault(c["id_requisito"], set()).add(c["id_asignatura"])

        visitados: set[int] = set()
        pendientes = [id_asignatura]
        while pendientes:
            actual = pendientes.pop()
            for dependiente in dependientes_directos.get(actual, ()):
                if dependiente not in visitados:
                    visitados.add(dependiente)
                    pendientes.append(dependiente)

        afectadas = [self.asignaturas[i] for i in visitados]
        return sorted(afectadas, key=lambda x: (x.nivel, x.nombre))

    # -----------------------------------------------------------------
    # Alternativas de planificación
    # -----------------------------------------------------------------
    def generar_alternativas(self) -> list[dict]:
        habilitadas = self.materias_habilitadas()
        a_recursar = self.materias_a_recursar()
        finales_pendientes = self.materias_con_final_pendiente()

        # Priorizar finales según cuántas materias futuras destraban
        finales_priorizados = sorted(
            finales_pendientes,
            key=lambda a: -len(self.impacto_futuro(a.id)),
        )

        alternativas = []

        # --- Alternativa 1: Avanzar todo lo posible ---
        alternativas.append({
            "titulo": "Alternativa 1 — Avanzar todo lo posible",
            "descripcion": (
                "Priorizar el cursado de las asignaturas del próximo nivel "
                "que ya están habilitadas, para no perder el cuatrimestre."
            ),
            "acciones": [f"Cursar: {a.nombre} (Nivel {a.nivel})" for a in habilitadas]
                        or ["No hay asignaturas nuevas habilitadas todavía."],
            "ventaja": "Mantiene el ritmo de avance en la carrera.",
            "desventaja": "No resuelve las materias adeudadas, que pueden "
                           "seguir frenando niveles más adelante.",
        })

        # --- Alternativa 2: Destrabar correlatividades ---
        acciones_destrabar = []
        for a in a_recursar:
            impacto = self.impacto_futuro(a.id)
            acciones_destrabar.append(
                f"Recursar: {a.nombre} (destraba {len(impacto)} asignatura/s futura/s)"
            )
        for a in finales_priorizados:
            impacto = self.impacto_futuro(a.id)
            acciones_destrabar.append(
                f"Rendir final: {a.nombre} (destraba {len(impacto)} asignatura/s futura/s)"
            )
        alternativas.append({
            "titulo": "Alternativa 2 — Destrabar correlatividades",
            "descripcion": (
                "Priorizar el recursado de materias no regularizadas y los "
                "finales pendientes que más asignaturas futuras condicionan, "
                "para evitar que se conviertan en cuellos de botella."
            ),
            "acciones": acciones_destrabar or ["No hay materias a recursar ni finales pendientes."],
            "ventaja": "Reduce el riesgo de atraso en niveles posteriores.",
            "desventaja": "Puede significar avanzar más lento en materias nuevas este cuatrimestre.",
        })

        # --- Alternativa 3: Planificación equilibrada ---
        acciones_equilibrada = []
        acciones_equilibrada += [f"Cursar: {a.nombre}" for a in habilitadas[:2]]
        acciones_equilibrada += [f"Recursar: {a.nombre}" for a in a_recursar]
        acciones_equilibrada += [f"Preparar y rendir final: {a.nombre}"
                                  for a in finales_priorizados[:2]]
        alternativas.append({
            "titulo": "Alternativa 3 — Planificación equilibrada",
            "descripcion": (
                "Combinar materias nuevas, recursado y preparación de "
                "finales, para mantener una carga académica razonable sin "
                "descuidar lo adeudado."
            ),
            "acciones": acciones_equilibrada or ["No hay acciones pendientes: la situación está al día."],
            "ventaja": "Equilibra avance y regularización de deudas.",
            "desventaja": "Requiere más organización personal (varios frentes a la vez).",
        })

        return alternativas

    # -----------------------------------------------------------------
    # Respuestas puntuales al cuestionario del caso de Martín
    # (reutilizable para cualquier estudiante, no solo Martín)
    # -----------------------------------------------------------------
    def responder_cuestionario(self) -> dict:
        habilitadas = self.materias_habilitadas()
        no_habilitadas = self.materias_no_habilitadas()
        a_recursar = self.materias_a_recursar()
        finales = self.materias_con_final_pendiente()

        finales_priorizados = sorted(finales, key=lambda a: -len(self.impacto_futuro(a.id)))

        consecuencias_recursado = []
        for a in a_recursar:
            consecuencias_recursado.extend(self.impacto_futuro(a.id))

        respuestas = {
            "1_puede_cursar": habilitadas,
            "2_no_puede_cursar": no_habilitadas,
            "3_consecuencias_no_regularizada": {
                "materias": a_recursar,
                "impacto": consecuencias_recursado,
            },
            "4_final_a_priorizar": finales_priorizados[0] if finales_priorizados else None,
            "4_ranking_finales": finales_priorizados,
            "5_materias_futuras_afectadas": {
                a.nombre: self.impacto_futuro(a.id)
                for a in (a_recursar + finales)
            },
            "6_alternativas": self.generar_alternativas(),
            "7_avance_general": self.avance_general(),
        }
        return respuestas
