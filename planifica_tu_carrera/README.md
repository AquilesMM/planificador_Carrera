# Planificá tu Carrera

Aplicación de escritorio (Python + Tkinter + MySQL) para la actividad
**"Planifica tu carrera"** de Ingeniería y Sociedad — Ingeniería en
Sistemas de Información, UTN San Rafael (2026).

Permite cargar la situación académica de un estudiante, ver qué
materias puede cursar según el régimen de correlatividades, qué se lo
impide, qué finales tiene pendientes, qué debe recursar, cómo eso
afecta niveles futuros, el avance general de la carrera, y propone
alternativas de planificación (avanzar / destrabar / equilibrado).
Incluye el caso de Martín precargado como estudiante de prueba.

## Arquitectura

```
planifica_tu_carrera/
├── db/
│   └── schema.sql        # Tablas MySQL + plan de estudios + caso de Martín
├── app/
│   ├── database.py       # Acceso a datos (MySQL) — no tiene lógica de negocio
│   ├── logica.py         # Motor de negocio (correlatividades, alternativas) — no sabe de MySQL ni de Tkinter
│   └── gui.py             # Interfaz gráfica (Tkinter)
├── tests/
│   └── test_logica.py    # Tests del motor de negocio con el caso de Martín (no requieren MySQL)
├── main.py                # Punto de entrada
└── requirements.txt
```

La separación en tres capas (datos / lógica / interfaz) es intencional:
`logica.py` es 100% Python puro (sin imports de MySQL ni de Tkinter),
así que se puede probar y revisar en la presentación oral sin
necesidad de tener el motor gráfico corriendo.

## Sobre el plan de estudios cargado

`db/schema.sql` carga el plan de estudios **oficial**: "Organización
Académica Curricular - Régimen de Correlatividades", Diseño Curricular
2023 (Ordenanza N° 1878 Cs), Anexo IV - Resolución N° 294/25 - C.D. -
FRSR, Ciclo Lectivo 2026|2027. Las 43 asignaturas (36 numeradas +
Seminario de Introducción al Idioma Inglés I + 6 electivas) y sus ~93
correlatividades para cursar y para rendir están transcriptas
directamente de ese documento.

No se incluye la columna de modalidad/cuatrimestre (1°, 2°, Anual) del
documento original — el esquema solo guarda nivel, nombre, código
oficial (N°) y carga horaria.

**Caso especial — Proyecto Final (N°36):** es una materia integradora
sin final tradicional, así que en el documento su fila combina ambos
requisitos ("Cursada" y "Aprobada") bajo un único encabezado "Para
Cursar". Esto se modela con filas `tipo='cursar'` donde unas piden
`estado_requerido='regular'` y otras `'aprobada'` — el esquema ya lo
soporta porque ambos campos son independientes.

## Instalación

1. Tener MySQL corriendo localmente.
2. Crear la base y cargar los datos:
   ```bash
   mysql -u root -p < db/schema.sql
   ```
3. Instalar dependencias:
   ```bash
   pip install -r requirements.txt
   ```
4. Ajustar la conexión si hace falta en `app/database.py` (`DB_CONFIG`):
   ```python
   DB_CONFIG = {
       "host": "localhost",
       "user": "root",
       "password": "",
       "database": "planifica_tu_carrera",
   }
   ```
5. Ejecutar:
   ```bash
   python main.py
   ```

Tkinter viene incluido con Python en Windows/Mac. En Linux, si falta,
se instala con `sudo apt install python3-tk`.

## Probar la lógica sin MySQL

```bash
python -m unittest tests/test_logica.py -v
```

Estos tests reproducen el caso de Martín en memoria y verifican, por
ejemplo, que no puede cursar "Algoritmos y Estructuras de Datos II"
porque no regularizó "Algoritmos y Estructuras de Datos", y que esa
materia condiciona el cursado de "Arquitectura de Computadores" y
"Base de Datos" más adelante.

## Estados de una asignatura

| Estado             | Significado                                  |
|---------------------|-----------------------------------------------|
| `aprobada`          | Rindió el final y aprobó                      |
| `regular`           | Cursó y regularizó, final pendiente           |
| `no_regularizada`   | Cursó pero no regularizó, debe recursar       |
| `no_cursada`        | Todavía no la cursó (estado por defecto)      |

## Qué resuelve cada pestaña de la GUI

1. **Plan de estudios**: todas las materias por nivel, coloreadas según estado.
2. **Situación académica**: cargar/editar el estado de cada materia para el estudiante seleccionado (doble clic).
3. **Qué puedo / no puedo cursar**: dos listas, la segunda con el motivo puntual (qué correlatividad falla).
4. **Finales y recursada**: materias regularizadas con final pendiente, y materias a recursar.
5. **Impacto futuro**: elegís una materia pendiente y ves qué asignaturas de niveles posteriores dependen de ella.
6. **Alternativas**: las 3 estrategias de planificación (avanzar todo lo posible / destrabar correlatividades / equilibrada), generadas dinámicamente según el ranking de impacto de cada final/recursada.
7. **Resumen del caso**: responde en texto corrido las 7 preguntas del cuestionario de la consigna, para usar en la presentación oral.

## Reflexión final (pregunta de la consigna)

> ¿De qué manera un sistema de información puede transformar datos
> académicos en información útil para tomar mejores decisiones?

Cada estado de asignatura es un dato aislado; el valor lo agrega el
**motor de correlatividades** (`logica.py`), que cruza esos datos con
el régimen de la carrera para producir información accionable: qué se
puede hacer hoy, qué lo bloquea, y qué conviene priorizar según cuánto
impacto tiene a futuro. Eso es lo que un estudiante no puede ver a
simple vista revisando el plan de estudios en papel.
