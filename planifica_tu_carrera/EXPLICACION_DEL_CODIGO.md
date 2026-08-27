# Explicación del código — Planificá tu Carrera

Este documento recorre **archivo por archivo** el proyecto, explicando qué
hace cada uno, por qué existe, y qué funciones/clases contiene. Sirve como
guía para la presentación oral (la consigna pide explicar "cómo funciona
la aplicación" y "qué información utiliza").

## Idea general: arquitectura en 3 capas

```
 MySQL  <──────  app/database.py  <──────  app/logica.py  <──────  app/gui.py
(datos)          (acceso a datos)         (reglas de negocio)      (interfaz)
```

Cada capa solo le habla a la de al lado, nunca "salta" a otra:

- **`database.py`** es la única parte del programa que sabe hablar con
  MySQL. No sabe nada de correlatividades ni de Tkinter.
- **`logica.py`** es la única parte que sabe las *reglas* (qué significa
  "puede cursar", cómo calcular el impacto futuro, etc.). No sabe nada de
  MySQL ni de Tkinter — recibe listas y diccionarios de Python comunes.
- **`gui.py`** es la única parte que dibuja ventanas. Le pide los datos a
  `database.py`, se los pasa a `logica.py` para que calcule, y muestra el
  resultado.

Esta separación es a propósito: permite explicar y hasta **probar la
lógica de correlatividades sin necesidad de tener MySQL corriendo**
(ver `tests/test_logica.py`), y si mañana quisieran cambiar Tkinter por
otra interfaz (web, consola, etc.), `logica.py` no se toca.

---

## `db/schema.sql`

Es el script que crea la base de datos en MySQL. Hace tres cosas:

1. **Crea la base** `planifica_tu_carrera` y 4 tablas:
   - `asignatura`: cada materia del plan de estudios (`codigo` — el N°
     oficial del régimen, por ejemplo `'6'` o `'E.1'` —, nombre, nivel
     de 1 a 5, horas, y dos flags: `es_electiva` y `es_integradora`).
     No se guarda modalidad/cuatrimestre (1°, 2°, Anual): se decidió
     omitirla porque no aporta a la lógica de correlatividades.
   - `correlatividad`: qué asignatura (`id_asignatura`) necesita qué otra
     (`id_requisito`), para qué (`tipo`: `'cursar'` o `'rendir'` el
     final), y en qué estado tiene que estar esa otra materia
     (`estado_requerido`: `'regular'` o `'aprobada'`). Esta tabla es el
     corazón del "régimen de correlatividades": es un grafo de
     dependencias entre materias.
   - `estudiante`: quién es el estudiante (nombre).
   - `situacion_academica`: el estado real de CADA estudiante en CADA
     materia (`aprobada`, `regular`, `no_regularizada`, `no_cursada`).
     Si una materia no tiene fila acá para un estudiante, se asume
     `no_cursada` (todavía no la tocó).

2. **Carga el plan de estudios OFICIAL**: las 43 asignaturas (36
   numeradas + el Seminario de Introducción al Idioma Inglés I + 6
   electivas E.1 a E.6) y las ~93 correlatividades del documento
   "Organización Académica Curricular - Régimen de Correlatividades",
   Diseño Curricular 2023 (Ordenanza N° 1878 Cs), Anexo IV - Resolución
   N° 294/25 - C.D. - FRSR, transcriptas directamente de ese póster.

   > **Caso especial — Proyecto Final (N°36):** es una materia
   > integradora sin final tradicional. En el documento, su fila
   > combina ambos requisitos ("Cursada" y "Aprobada") bajo un único
   > encabezado "Para Cursar". Se modela con filas `tipo='cursar'`
   > donde tres materias piden `estado_requerido='regular'`
   > (Ingeniería y Calidad de Software, Redes de Datos, Administración
   > de Sistemas de Información) y otras tres piden `'aprobada'`
   > (Inglés II, Desarrollo de Software, Diseño de Sistemas de
   > Información) — el esquema ya lo soporta sin cambios, porque
   > `tipo` y `estado_requerido` son campos independientes.

3. **Carga el caso de Martín** como estudiante de prueba obligatorio: crea
   la fila en `estudiante`, y en `situacion_academica` carga exactamente
   lo que describe el enunciado (Algoritmos y Estructuras de Datos no
   regularizada, Análisis Matemático I y Física I regulares con final
   pendiente, resto de primer nivel aprobado).

---

## `app/database.py`

Es la capa de **acceso a datos**. Ningún cálculo de correlatividades vive
acá — solo lee y escribe filas de MySQL y las traduce a `dict`/`list` de
Python.

- **`DB_CONFIG`**: diccionario con host, usuario, contraseña y nombre de
  la base. Es lo primero que hay que editar si la conexión a MySQL falla
  (usuario/contraseña distintos a los de por defecto).

- **Clase `ConexionBD`**: envoltorio chico sobre
  `mysql-connector-python`.
  - `conectar()`: abre la conexión si no existe una abierta.
  - `cerrar()`: la cierra.
  - `ejecutar_query(query, params)`: corre un `SELECT` y devuelve una
    lista de diccionarios (una fila = un dict con nombre de columna →
    valor).
  - `ejecutar_update(query, params)`: corre `INSERT`/`UPDATE`/`DELETE` y
    confirma los cambios (`commit`).

- **Funciones de alto nivel** (las que usa `gui.py` directamente):
  - `obtener_plan_de_estudios(bd)`: trae todas las asignaturas (código,
    nombre, nivel, horas, si es electiva/integradora), ordenadas por
    nivel y nombre.
  - `obtener_correlatividades(bd)`: trae todas las filas de la tabla
    `correlatividad` (el grafo de dependencias completo).
  - `obtener_estudiantes(bd)`: lista de estudiantes cargados, para el
    combo de selección en la GUI.
  - `obtener_o_crear_estudiante(bd, nombre)`: busca un estudiante por
    nombre; si no existe, lo crea y devuelve su id. Se usa cuando el
    usuario aprieta "Nuevo estudiante" en la GUI.
  - `obtener_situacion_academica(bd, id_estudiante)`: trae el estado de
    cada materia para un estudiante puntual, como
    `{id_asignatura: estado}`.
  - `guardar_estado_asignatura(bd, id_estudiante, id_asignatura, estado)`:
    inserta o actualiza (`ON DUPLICATE KEY UPDATE`) el estado de una
    materia para un estudiante. Se usa cuando el usuario edita el estado
    de una asignatura desde la pestaña "Situación académica".
  - `cargar_datos_completos(bd, id_estudiante)`: junta las tres consultas
    anteriores en un solo diccionario (`asignaturas`, `correlatividades`,
    `situacion`) — es el "combo" que se le pasa directo a `logica.py`.

---

## `app/logica.py`

Es el **motor de negocio**: acá vive toda la inteligencia que pide la
consigna (qué puede cursar, qué se lo impide, impacto futuro, alternativas
de planificación). Es Python puro — no importa `mysql.connector` ni
`tkinter`, así que se puede testear de forma aislada.

### Clases de datos

- **`Asignatura`**: representa una materia ya combinada con el estado del
  estudiante (`id`, `codigo`, `nombre`, `nivel`, `horas`, `es_electiva`,
  `es_integradora`, `estado`).
- **`Bloqueo`**: explica *por qué* una materia está bloqueada — qué
  materia requisito falta, en qué estado la necesita
  (`regular`/`aprobada`) y en qué estado está realmente. Es lo que
  alimenta la columna "motivo" de la pestaña "Qué no puedo cursar".

### Clase principal: `PlanDeCarrera`

Se construye una vez por estudiante, con los datos que trajo
`database.py`. Internamente arma un diccionario `{id: Asignatura}` con el
estado ya aplicado a cada una.

Métodos, agrupados por qué pregunta de la consigna resuelven:

- **`por_nivel()`**: agrupa las asignaturas por nivel (1 a 5), ordenadas.
  Alimenta la pestaña "Plan de estudios".

- **`puede_cursar(id_asignatura)`** y **`puede_rendir(id_asignatura)`**:
  recorren la tabla de correlatividades buscando los requisitos de tipo
  `'cursar'` (o `'rendir'`) de esa materia, y chequean si el estudiante
  cumple cada uno. Devuelven `(True, [])` si puede, o
  `(False, [lista_de_Bloqueo])` si no, detallando qué falta.

- **`materias_habilitadas()`**: recorre todas las materias que el
  estudiante todavía no tiene aprobadas ni regulares, y se queda con las
  que `puede_cursar()` devuelve `True`. → responde *"¿qué puede cursar
  ahora?"*.

- **`materias_no_habilitadas()`**: lo complementario, junto con la lista
  de `Bloqueo` de cada una. → responde *"¿qué no puede cursar y por
  qué?"*.

- **`materias_con_final_pendiente()`**: filtra las que están en estado
  `'regular'`.

- **`materias_a_recursar()`**: filtra las que están en estado
  `'no_regularizada'`.

- **`avance_general()`**: cuenta cuántas materias están aprobadas sobre
  el total, y calcula el porcentaje. Es lo que se ve arriba a la derecha
  de la ventana ("Avance: X/Y aprobadas").

- **`impacto_futuro(id_asignatura)`**: la función más importante para
  responder *"¿qué materias de niveles posteriores se ven afectadas?"*.
  Arma un grafo invertido (para cada materia, quién depende de ella) y
  hace un recorrido en profundidad (DFS) desde `id_asignatura`, juntando
  **todas** las materias que dependen de ella, directa o
  indirectamente — no solo el nivel inmediato siguiente, sino en cascada
  a través de varios niveles.

- **`generar_alternativas()`**: arma las 3 alternativas que pide la
  consigna, usando `impacto_futuro()` para ordenar qué recursar/rendir
  primero:
  - **Alternativa 1 — Avanzar todo lo posible**: lista directamente
    `materias_habilitadas()`.
  - **Alternativa 2 — Destrabar correlatividades**: prioriza recursar y
    rendir finales, ordenados de mayor a menor según cuántas materias
    futuras destraban (`len(impacto_futuro(...))`).
  - **Alternativa 3 — Planificación equilibrada**: combina un par de
    materias nuevas + todo lo que hay que recursar + los finales de
    mayor impacto, buscando no sobrecargar al estudiante.
  Cada alternativa devuelve título, descripción, lista de acciones
  concretas, ventaja y desventaja — así se explica por sí sola en la
  pestaña "Alternativas".

- **`responder_cuestionario()`**: junta todo lo anterior en un solo
  diccionario que responde, en orden, las 7 preguntas que el PDF de la
  consigna pide poder contestar (qué puede cursar, qué no y por qué,
  consecuencias de no regularizar, qué final priorizar, impacto en
  niveles posteriores, alternativas, avance general). Es lo que arma el
  texto de la pestaña "Resumen del caso".

---

## `app/gui.py`

Es la **interfaz gráfica** (Tkinter). No calcula nada por sí misma: junta
`database.py` (para traer/guardar datos) con `logica.py` (para
calcular), y los muestra en pantalla.

- **Clase `App(tk.Tk)`**: la ventana principal.
  - `_construir_barra_superior()`: arma el combo para elegir estudiante,
    los botones "Nuevo estudiante" / "Cargar caso de Martín" /
    "Actualizar", y la etiqueta de avance general.
  - `_construir_notebook()`: crea las 7 pestañas (`ttk.Notebook`) y llama
    a un método `_construir_tab_...()` por cada una, que arma los
    widgets vacíos (tablas, listas, cajas de texto).
  - `_cargar_lista_estudiantes()`: al arrancar, trae los estudiantes de
    la base (vía `database.py`) y llena el combo. Si falla la conexión a
    MySQL, muestra un mensaje de error explicando qué revisar.
  - `_on_seleccionar_estudiante()`: cuando cambia el combo, guarda el id
    del estudiante elegido y llama a `refrescar_todo()`.
  - `_nuevo_estudiante()`: pide un nombre por diálogo, lo crea en la base
    (`obtener_o_crear_estudiante`) y lo selecciona.
  - `_cargar_caso_martin()`: atajo que selecciona directamente a
    "Martín" (el estudiante de prueba obligatorio) y lleva a la pestaña
    de resumen.
  - **`refrescar_todo()`**: el método central. Trae de `database.py` el
    plan, las correlatividades y la situación del estudiante actual,
    construye un `PlanDeCarrera` (de `logica.py`), y llama a un
    `_refrescar_tab_...()` por cada pestaña para repintarla con los datos
    nuevos. Se llama cada vez que cambia el estudiante o se edita un
    estado.

  Por cada pestaña hay un par de métodos `_construir_tab_X()` (crea los
  widgets, una sola vez, al arrancar) y `_refrescar_tab_X()` (borra y
  vuelve a llenar esos widgets con los datos actuales, cada vez que algo
  cambia):

  - **Plan de estudios**: tabla (`Treeview`) con todas las materias,
    coloreada según estado (verde=aprobada, amarillo=regular,
    rojo=no regularizada, gris=no cursada).
  - **Situación académica**: misma tabla, pero editable — doble clic
    sobre una fila abre una ventanita (`_editar_estado`) para cambiar el
    estado y lo guarda en MySQL con
    `database.guardar_estado_asignatura()`, después refresca todo.
  - **Qué puedo/no puedo cursar**: dos listas lado a lado, alimentadas
    por `materias_habilitadas()` y `materias_no_habilitadas()`.
  - **Finales y recursada**: dos listas con
    `materias_con_final_pendiente()` y `materias_a_recursar()`.
  - **Impacto futuro**: un combo para elegir una materia pendiente
    (recursada o con final) y un botón que muestra, llamando a
    `impacto_futuro()`, todas las materias futuras afectadas.
  - **Alternativas**: un cuadro de texto que vuelca las 3 alternativas de
    `generar_alternativas()`, con sus acciones, ventaja y desventaja.
  - **Resumen del caso**: un cuadro de texto que vuelca
    `responder_cuestionario()`, respondiendo en prosa las 7 preguntas del
    enunciado — pensado para leerlo directo en la presentación oral.

- **`main()`**: crea la `App` y arranca el loop de eventos de Tkinter
  (`app.mainloop()`).

---

## `main.py`

Punto de entrada del programa. Agrega la carpeta `app/` al `sys.path`
(para que los `import database` / `import logica` funcionen sin
configurar nada más) y llama a `gui.main()`. Es el archivo que se
ejecuta con `python main.py`.

---

## `tests/test_logica.py`

Pruebas automáticas del motor de negocio, **sin necesidad de tener MySQL
corriendo**: arma a mano (en listas y diccionarios de Python) una copia
reducida de los datos de `db/schema.sql` con el caso de Martín, y verifica
con `unittest` cosas puntuales, por ejemplo:

- que Martín SÍ puede cursar Análisis Matemático II,
- que NO puede cursar Algoritmos y Estructuras de Datos II (y que el
  motivo detectado es justamente que no regularizó Algoritmos y
  Estructuras de Datos),
- que el impacto futuro de esa materia no regularizada incluye
  correctamente las 3 materias de niveles posteriores que dependen de
  ella,
- que se generan las 3 alternativas de planificación.

Sirve como red de seguridad: si alguien modifica `logica.py` (por
ejemplo, para adaptarlo al plan de estudios real), correr
`python -m unittest tests/test_logica.py -v` avisa enseguida si algo se
rompió, sin tener que abrir la GUI ni tocar la base de datos.

---

## `requirements.txt`

Lista de dependencias externas del proyecto. Hoy tiene una sola:
`mysql-connector-python`, el driver oficial de MySQL para Python que usa
`database.py`. Tkinter no aparece acá porque viene incluido con Python
(salvo en algunas instalaciones de Linux, donde hay que instalar aparte
el paquete `python3-tk` del sistema operativo).
