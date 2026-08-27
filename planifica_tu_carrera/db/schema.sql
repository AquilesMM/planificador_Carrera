-- =====================================================================
-- Planificá tu Carrera - Ingeniería en Sistemas de Información
-- Ingeniería y Sociedad - UTN San Rafael - 2026
-- =====================================================================
-- Esquema de base de datos MySQL + datos OFICIALES del plan de estudios.
--
-- Fuente: "Organización Académica Curricular - Régimen de
-- Correlatividades" - Diseño Curricular 2023 - Ordenanza N° 1878 Cs -
-- Anexo IV - Resolución N° 294/25 - C.D. - FRSR - Ciclo Lectivo
-- 2026|2027 (documento provisto por la cátedra).
--
-- No se incluye información de modalidad/cuatrimestre (1°, 2°, Anual):
-- solo nivel, nombre, carga horaria y correlatividades.
-- =====================================================================

DROP DATABASE IF EXISTS planifica_tu_carrera;
CREATE DATABASE planifica_tu_carrera CHARACTER SET utf8mb4;
USE planifica_tu_carrera;

-- ---------------------------------------------------------------------
-- Tabla: asignatura
-- `codigo` conserva el N° oficial del régimen (1, 2, 3... 36, o el
-- código de electiva E.1...E.6), para poder cruzar fácilmente con el
-- documento fuente.
-- ---------------------------------------------------------------------
CREATE TABLE asignatura (
    id_asignatura   INT AUTO_INCREMENT PRIMARY KEY,
    codigo          VARCHAR(6)   NOT NULL,   -- N° oficial: '1'..'36', 'O.1', 'E.1'..'E.6'
    nombre          VARCHAR(120) NOT NULL,
    nivel           TINYINT      NOT NULL,   -- 1..5
    horas           SMALLINT     NULL,
    es_electiva     BOOLEAN      NOT NULL DEFAULT FALSE,
    es_integradora  BOOLEAN      NOT NULL DEFAULT FALSE,
    UNIQUE KEY uq_asignatura_codigo (codigo),
    UNIQUE KEY uq_asignatura_nombre (nombre)
);

-- ---------------------------------------------------------------------
-- Tabla: correlatividad
-- Modela el régimen tal cual está en el documento: cada asignatura
-- tiene una columna "Cursada" (materias que deben estar REGULARIZADAS
-- para poder CURSAR esta asignatura) y una columna "Aprobada"
-- (materias que deben estar APROBADAS para poder RENDIR el final de
-- esta asignatura).
--   tipo='cursar' + estado_requerido='regular'  -> columna "Cursada"
--   tipo='rendir' + estado_requerido='aprobada' -> columna "Aprobada"
-- Excepción: Proyecto Final (36) no tiene columna "Aprobada" propia
-- (no rinde final tradicional); su fila combina, ambas bajo
-- tipo='cursar': unas materias piden 'regular' y otras 'aprobada'
-- para poder CURSAR el Proyecto Final. El modelo ya lo soporta sin
-- cambios porque `estado_requerido` es independiente de `tipo`.
-- ---------------------------------------------------------------------
CREATE TABLE correlatividad (
    id_correlatividad   INT AUTO_INCREMENT PRIMARY KEY,
    id_asignatura       INT NOT NULL,
    id_requisito        INT NOT NULL,
    tipo                ENUM('cursar', 'rendir') NOT NULL,
    estado_requerido    ENUM('regular', 'aprobada') NOT NULL,
    CONSTRAINT fk_corr_asignatura FOREIGN KEY (id_asignatura)
        REFERENCES asignatura(id_asignatura) ON DELETE CASCADE,
    CONSTRAINT fk_corr_requisito FOREIGN KEY (id_requisito)
        REFERENCES asignatura(id_asignatura) ON DELETE CASCADE,
    UNIQUE KEY uq_corr (id_asignatura, id_requisito, tipo, estado_requerido)
);

-- ---------------------------------------------------------------------
-- Tabla: estudiante
-- ---------------------------------------------------------------------
CREATE TABLE estudiante (
    id_estudiante   INT AUTO_INCREMENT PRIMARY KEY,
    nombre          VARCHAR(120) NOT NULL
);

-- ---------------------------------------------------------------------
-- Tabla: situacion_academica
-- Estado real de cada estudiante en cada asignatura. Si no hay fila
-- para una asignatura, se asume 'no_cursada'.
-- ---------------------------------------------------------------------
CREATE TABLE situacion_academica (
    id_situacion    INT AUTO_INCREMENT PRIMARY KEY,
    id_estudiante   INT NOT NULL,
    id_asignatura   INT NOT NULL,
    estado          ENUM('aprobada', 'regular', 'no_regularizada', 'no_cursada')
                    NOT NULL DEFAULT 'no_cursada',
    CONSTRAINT fk_sit_estudiante FOREIGN KEY (id_estudiante)
        REFERENCES estudiante(id_estudiante) ON DELETE CASCADE,
    CONSTRAINT fk_sit_asignatura FOREIGN KEY (id_asignatura)
        REFERENCES asignatura(id_asignatura) ON DELETE CASCADE,
    UNIQUE KEY uq_situacion (id_estudiante, id_asignatura)
);

-- =====================================================================
-- DATOS: Plan de estudios OFICIAL (Diseño Curricular 2023 - FRSR)
-- =====================================================================

-- ---- Primer Nivel ----
INSERT INTO asignatura (codigo, nombre, nivel, horas) VALUES
('1',   'Análisis Matemático I',                          1, 10),
('2',   'Álgebra y Geometría Analítica',                  1, 10),
('3',   'Física I',                                       1, 10),
('5',   'Lógica y Estructuras Discretas',                 1, 6),
('6',   'Algoritmo y Estructura de Datos',                1, 5),
('7',   'Arquitectura de Computadoras',                   1, 8),
('8',   'Sistemas y Procesos de Negocios',                1, 3),
('O.1', 'Seminario de Introducción al Idioma Inglés I',   1, 2);

-- ---- Segundo Nivel ----
INSERT INTO asignatura (codigo, nombre, nivel, horas, es_integradora) VALUES
('9',   'Análisis Matemático II',                    2, 5,  FALSE),
('10',  'Física II',                                 2, 10, FALSE),
('11',  'Ingeniería y Sociedad',                      2, 4,  FALSE),
('13',  'Sintaxis y Semántica de los Lenguajes',      2, 4,  FALSE),
('14',  'Paradigmas de Programación',                 2, 4,  FALSE),
('15',  'Sistemas Operativos',                        2, 4,  FALSE),
('16',  'Análisis de Sistemas de Información',        2, 5,  TRUE),
('4',   'Inglés I',                                   2, 2,  FALSE);

-- ---- Tercer Nivel ----
INSERT INTO asignatura (codigo, nombre, nivel, horas, es_integradora) VALUES
('17',  'Probabilidad y Estadística',                 3, 6, FALSE),
('18',  'Economía',                                   3, 6, FALSE),
('19',  'Base de Datos',                               3, 4, FALSE),
('20',  'Desarrollo de Software',                     3, 4, FALSE),
('21',  'Comunicación de Datos',                       3, 4, FALSE),
('22',  'Análisis Numérico',                           3, 6, FALSE),
('23',  'Diseño de Sistemas de Información',          3, 6, TRUE),
('12',  'Inglés II',                                   3, 2, FALSE);

-- ---- Cuarto Nivel ----
INSERT INTO asignatura (codigo, nombre, nivel, horas, es_electiva, es_integradora) VALUES
('24',  'Legislación',                                4, 2, FALSE, FALSE),
('25',  'Ingeniería y Calidad de Software',            4, 6, FALSE, FALSE),
('26',  'Redes de Datos',                              4, 8, FALSE, FALSE),
('27',  'Investigación Operativa',                     4, 4, FALSE, FALSE),
('28',  'Simulación',                                  4, 6, FALSE, FALSE),
('29',  'Tecnología para la Automatización',           4, 6, FALSE, FALSE),
('30',  'Administración de Sistemas de Información',   4, 6, FALSE, TRUE),
('E.1', 'Arduino',                                     4, 8, TRUE,  FALSE),
('E.2', 'Auditoría en Sistemas de Información',        4, 8, TRUE,  FALSE),
('E.3', 'Seguridad en Redes',                          4, 8, TRUE,  FALSE),
('E.4', 'Base de Datos Avanzada',                      4, 8, TRUE,  FALSE);

-- ---- Quinto Nivel ----
INSERT INTO asignatura (codigo, nombre, nivel, horas, es_electiva, es_integradora) VALUES
('31',  'Inteligencia Artificial',                    5, 3, FALSE, FALSE),
('32',  'Ciencia de Datos',                            5, 6, FALSE, FALSE),
('33',  'Sistemas de Gestión',                         5, 8, FALSE, FALSE),
('34',  'Gestión Gerencial',                           5, 6, FALSE, FALSE),
('35',  'Seguridad en los Sistemas de Información',    5, 6, FALSE, FALSE),
('E.5', 'Visión por Computadora',                      5, 8, TRUE,  FALSE),
('E.6', 'Inglés para Profesionales',                   5, 4, TRUE,  FALSE),
('36',  'Proyecto Final',                              5, 6, FALSE, TRUE);

-- =====================================================================
-- DATOS: Correlatividades OFICIALES
-- =====================================================================

-- --- Segundo Nivel ---
INSERT INTO correlatividad (id_asignatura, id_requisito, tipo, estado_requerido) VALUES
((SELECT id_asignatura FROM asignatura WHERE codigo='9'),  (SELECT id_asignatura FROM asignatura WHERE codigo='1'), 'cursar', 'regular'),
((SELECT id_asignatura FROM asignatura WHERE codigo='9'),  (SELECT id_asignatura FROM asignatura WHERE codigo='2'), 'cursar', 'regular'),
((SELECT id_asignatura FROM asignatura WHERE codigo='10'), (SELECT id_asignatura FROM asignatura WHERE codigo='1'), 'cursar', 'regular'),
((SELECT id_asignatura FROM asignatura WHERE codigo='10'), (SELECT id_asignatura FROM asignatura WHERE codigo='3'), 'cursar', 'regular'),
((SELECT id_asignatura FROM asignatura WHERE codigo='13'), (SELECT id_asignatura FROM asignatura WHERE codigo='5'), 'cursar', 'regular'),
((SELECT id_asignatura FROM asignatura WHERE codigo='13'), (SELECT id_asignatura FROM asignatura WHERE codigo='6'), 'cursar', 'regular'),
((SELECT id_asignatura FROM asignatura WHERE codigo='14'), (SELECT id_asignatura FROM asignatura WHERE codigo='5'), 'cursar', 'regular'),
((SELECT id_asignatura FROM asignatura WHERE codigo='14'), (SELECT id_asignatura FROM asignatura WHERE codigo='6'), 'cursar', 'regular'),
((SELECT id_asignatura FROM asignatura WHERE codigo='15'), (SELECT id_asignatura FROM asignatura WHERE codigo='7'), 'cursar', 'regular'),
((SELECT id_asignatura FROM asignatura WHERE codigo='16'), (SELECT id_asignatura FROM asignatura WHERE codigo='6'), 'cursar', 'regular'),
((SELECT id_asignatura FROM asignatura WHERE codigo='16'), (SELECT id_asignatura FROM asignatura WHERE codigo='8'), 'cursar', 'regular');

-- --- Tercer Nivel ---
INSERT INTO correlatividad (id_asignatura, id_requisito, tipo, estado_requerido) VALUES
((SELECT id_asignatura FROM asignatura WHERE codigo='17'), (SELECT id_asignatura FROM asignatura WHERE codigo='1'),  'cursar', 'regular'),
((SELECT id_asignatura FROM asignatura WHERE codigo='17'), (SELECT id_asignatura FROM asignatura WHERE codigo='2'),  'cursar', 'regular'),
((SELECT id_asignatura FROM asignatura WHERE codigo='18'), (SELECT id_asignatura FROM asignatura WHERE codigo='1'),  'rendir', 'aprobada'),
((SELECT id_asignatura FROM asignatura WHERE codigo='18'), (SELECT id_asignatura FROM asignatura WHERE codigo='2'),  'rendir', 'aprobada'),
((SELECT id_asignatura FROM asignatura WHERE codigo='19'), (SELECT id_asignatura FROM asignatura WHERE codigo='13'), 'cursar', 'regular'),
((SELECT id_asignatura FROM asignatura WHERE codigo='19'), (SELECT id_asignatura FROM asignatura WHERE codigo='16'), 'cursar', 'regular'),
((SELECT id_asignatura FROM asignatura WHERE codigo='19'), (SELECT id_asignatura FROM asignatura WHERE codigo='5'),  'rendir', 'aprobada'),
((SELECT id_asignatura FROM asignatura WHERE codigo='19'), (SELECT id_asignatura FROM asignatura WHERE codigo='6'),  'rendir', 'aprobada'),
((SELECT id_asignatura FROM asignatura WHERE codigo='20'), (SELECT id_asignatura FROM asignatura WHERE codigo='14'), 'cursar', 'regular'),
((SELECT id_asignatura FROM asignatura WHERE codigo='20'), (SELECT id_asignatura FROM asignatura WHERE codigo='16'), 'cursar', 'regular'),
((SELECT id_asignatura FROM asignatura WHERE codigo='20'), (SELECT id_asignatura FROM asignatura WHERE codigo='5'),  'rendir', 'aprobada'),
((SELECT id_asignatura FROM asignatura WHERE codigo='20'), (SELECT id_asignatura FROM asignatura WHERE codigo='6'),  'rendir', 'aprobada'),
((SELECT id_asignatura FROM asignatura WHERE codigo='21'), (SELECT id_asignatura FROM asignatura WHERE codigo='3'),  'rendir', 'aprobada'),
((SELECT id_asignatura FROM asignatura WHERE codigo='21'), (SELECT id_asignatura FROM asignatura WHERE codigo='7'),  'rendir', 'aprobada'),
((SELECT id_asignatura FROM asignatura WHERE codigo='22'), (SELECT id_asignatura FROM asignatura WHERE codigo='9'),  'cursar', 'regular'),
((SELECT id_asignatura FROM asignatura WHERE codigo='22'), (SELECT id_asignatura FROM asignatura WHERE codigo='1'),  'rendir', 'aprobada'),
((SELECT id_asignatura FROM asignatura WHERE codigo='22'), (SELECT id_asignatura FROM asignatura WHERE codigo='2'),  'rendir', 'aprobada'),
((SELECT id_asignatura FROM asignatura WHERE codigo='23'), (SELECT id_asignatura FROM asignatura WHERE codigo='14'), 'cursar', 'regular'),
((SELECT id_asignatura FROM asignatura WHERE codigo='23'), (SELECT id_asignatura FROM asignatura WHERE codigo='16'), 'cursar', 'regular'),
((SELECT id_asignatura FROM asignatura WHERE codigo='23'), (SELECT id_asignatura FROM asignatura WHERE codigo='4'),  'rendir', 'aprobada'),
((SELECT id_asignatura FROM asignatura WHERE codigo='23'), (SELECT id_asignatura FROM asignatura WHERE codigo='6'),  'rendir', 'aprobada'),
((SELECT id_asignatura FROM asignatura WHERE codigo='23'), (SELECT id_asignatura FROM asignatura WHERE codigo='8'),  'rendir', 'aprobada'),
((SELECT id_asignatura FROM asignatura WHERE codigo='12'), (SELECT id_asignatura FROM asignatura WHERE codigo='4'),  'cursar', 'regular');

-- --- Cuarto Nivel ---
INSERT INTO correlatividad (id_asignatura, id_requisito, tipo, estado_requerido) VALUES
((SELECT id_asignatura FROM asignatura WHERE codigo='24'),  (SELECT id_asignatura FROM asignatura WHERE codigo='11'), 'cursar', 'regular'),
((SELECT id_asignatura FROM asignatura WHERE codigo='25'),  (SELECT id_asignatura FROM asignatura WHERE codigo='19'), 'cursar', 'regular'),
((SELECT id_asignatura FROM asignatura WHERE codigo='25'),  (SELECT id_asignatura FROM asignatura WHERE codigo='20'), 'cursar', 'regular'),
((SELECT id_asignatura FROM asignatura WHERE codigo='25'),  (SELECT id_asignatura FROM asignatura WHERE codigo='23'), 'cursar', 'regular'),
((SELECT id_asignatura FROM asignatura WHERE codigo='25'),  (SELECT id_asignatura FROM asignatura WHERE codigo='13'), 'rendir', 'aprobada'),
((SELECT id_asignatura FROM asignatura WHERE codigo='25'),  (SELECT id_asignatura FROM asignatura WHERE codigo='14'), 'rendir', 'aprobada'),
((SELECT id_asignatura FROM asignatura WHERE codigo='26'),  (SELECT id_asignatura FROM asignatura WHERE codigo='15'), 'cursar', 'regular'),
((SELECT id_asignatura FROM asignatura WHERE codigo='26'),  (SELECT id_asignatura FROM asignatura WHERE codigo='21'), 'cursar', 'regular'),
((SELECT id_asignatura FROM asignatura WHERE codigo='27'),  (SELECT id_asignatura FROM asignatura WHERE codigo='17'), 'cursar', 'regular'),
((SELECT id_asignatura FROM asignatura WHERE codigo='27'),  (SELECT id_asignatura FROM asignatura WHERE codigo='22'), 'cursar', 'regular'),
((SELECT id_asignatura FROM asignatura WHERE codigo='28'),  (SELECT id_asignatura FROM asignatura WHERE codigo='17'), 'cursar', 'regular'),
((SELECT id_asignatura FROM asignatura WHERE codigo='28'),  (SELECT id_asignatura FROM asignatura WHERE codigo='9'),  'rendir', 'aprobada'),
((SELECT id_asignatura FROM asignatura WHERE codigo='29'),  (SELECT id_asignatura FROM asignatura WHERE codigo='10'), 'cursar', 'regular'),
((SELECT id_asignatura FROM asignatura WHERE codigo='29'),  (SELECT id_asignatura FROM asignatura WHERE codigo='22'), 'cursar', 'regular'),
((SELECT id_asignatura FROM asignatura WHERE codigo='29'),  (SELECT id_asignatura FROM asignatura WHERE codigo='9'),  'rendir', 'aprobada'),
((SELECT id_asignatura FROM asignatura WHERE codigo='30'),  (SELECT id_asignatura FROM asignatura WHERE codigo='18'), 'cursar', 'regular'),
((SELECT id_asignatura FROM asignatura WHERE codigo='30'),  (SELECT id_asignatura FROM asignatura WHERE codigo='23'), 'cursar', 'regular'),
((SELECT id_asignatura FROM asignatura WHERE codigo='30'),  (SELECT id_asignatura FROM asignatura WHERE codigo='16'), 'rendir', 'aprobada'),
((SELECT id_asignatura FROM asignatura WHERE codigo='E.1'), (SELECT id_asignatura FROM asignatura WHERE codigo='23'), 'cursar', 'regular'),
((SELECT id_asignatura FROM asignatura WHERE codigo='E.1'), (SELECT id_asignatura FROM asignatura WHERE codigo='6'),  'rendir', 'aprobada'),
((SELECT id_asignatura FROM asignatura WHERE codigo='E.1'), (SELECT id_asignatura FROM asignatura WHERE codigo='7'),  'rendir', 'aprobada'),
((SELECT id_asignatura FROM asignatura WHERE codigo='E.1'), (SELECT id_asignatura FROM asignatura WHERE codigo='14'), 'rendir', 'aprobada'),
((SELECT id_asignatura FROM asignatura WHERE codigo='E.2'), (SELECT id_asignatura FROM asignatura WHERE codigo='11'), 'cursar', 'regular'),
((SELECT id_asignatura FROM asignatura WHERE codigo='E.2'), (SELECT id_asignatura FROM asignatura WHERE codigo='19'), 'cursar', 'regular'),
((SELECT id_asignatura FROM asignatura WHERE codigo='E.2'), (SELECT id_asignatura FROM asignatura WHERE codigo='16'), 'rendir', 'aprobada'),
((SELECT id_asignatura FROM asignatura WHERE codigo='E.3'), (SELECT id_asignatura FROM asignatura WHERE codigo='20'), 'cursar', 'regular'),
((SELECT id_asignatura FROM asignatura WHERE codigo='E.3'), (SELECT id_asignatura FROM asignatura WHERE codigo='21'), 'cursar', 'regular'),
((SELECT id_asignatura FROM asignatura WHERE codigo='E.3'), (SELECT id_asignatura FROM asignatura WHERE codigo='16'), 'rendir', 'aprobada'),
((SELECT id_asignatura FROM asignatura WHERE codigo='E.4'), (SELECT id_asignatura FROM asignatura WHERE codigo='19'), 'cursar', 'regular'),
((SELECT id_asignatura FROM asignatura WHERE codigo='E.4'), (SELECT id_asignatura FROM asignatura WHERE codigo='15'), 'cursar', 'regular');

-- --- Quinto Nivel ---
INSERT INTO correlatividad (id_asignatura, id_requisito, tipo, estado_requerido) VALUES
((SELECT id_asignatura FROM asignatura WHERE codigo='31'),  (SELECT id_asignatura FROM asignatura WHERE codigo='28'), 'cursar', 'regular'),
((SELECT id_asignatura FROM asignatura WHERE codigo='31'),  (SELECT id_asignatura FROM asignatura WHERE codigo='17'), 'rendir', 'aprobada'),
((SELECT id_asignatura FROM asignatura WHERE codigo='31'),  (SELECT id_asignatura FROM asignatura WHERE codigo='22'), 'rendir', 'aprobada'),
((SELECT id_asignatura FROM asignatura WHERE codigo='32'),  (SELECT id_asignatura FROM asignatura WHERE codigo='28'), 'cursar', 'regular'),
((SELECT id_asignatura FROM asignatura WHERE codigo='32'),  (SELECT id_asignatura FROM asignatura WHERE codigo='17'), 'rendir', 'aprobada'),
((SELECT id_asignatura FROM asignatura WHERE codigo='32'),  (SELECT id_asignatura FROM asignatura WHERE codigo='19'), 'rendir', 'aprobada'),
((SELECT id_asignatura FROM asignatura WHERE codigo='33'),  (SELECT id_asignatura FROM asignatura WHERE codigo='18'), 'cursar', 'regular'),
((SELECT id_asignatura FROM asignatura WHERE codigo='33'),  (SELECT id_asignatura FROM asignatura WHERE codigo='27'), 'cursar', 'regular'),
((SELECT id_asignatura FROM asignatura WHERE codigo='33'),  (SELECT id_asignatura FROM asignatura WHERE codigo='23'), 'rendir', 'aprobada'),
((SELECT id_asignatura FROM asignatura WHERE codigo='34'),  (SELECT id_asignatura FROM asignatura WHERE codigo='24'), 'cursar', 'regular'),
((SELECT id_asignatura FROM asignatura WHERE codigo='34'),  (SELECT id_asignatura FROM asignatura WHERE codigo='30'), 'cursar', 'regular'),
((SELECT id_asignatura FROM asignatura WHERE codigo='34'),  (SELECT id_asignatura FROM asignatura WHERE codigo='18'), 'rendir', 'aprobada'),
((SELECT id_asignatura FROM asignatura WHERE codigo='35'),  (SELECT id_asignatura FROM asignatura WHERE codigo='26'), 'cursar', 'regular'),
((SELECT id_asignatura FROM asignatura WHERE codigo='35'),  (SELECT id_asignatura FROM asignatura WHERE codigo='30'), 'cursar', 'regular'),
((SELECT id_asignatura FROM asignatura WHERE codigo='35'),  (SELECT id_asignatura FROM asignatura WHERE codigo='20'), 'rendir', 'aprobada'),
((SELECT id_asignatura FROM asignatura WHERE codigo='35'),  (SELECT id_asignatura FROM asignatura WHERE codigo='21'), 'rendir', 'aprobada'),
((SELECT id_asignatura FROM asignatura WHERE codigo='E.5'), (SELECT id_asignatura FROM asignatura WHERE codigo='28'), 'cursar', 'regular'),
((SELECT id_asignatura FROM asignatura WHERE codigo='E.5'), (SELECT id_asignatura FROM asignatura WHERE codigo='30'), 'cursar', 'regular'),
((SELECT id_asignatura FROM asignatura WHERE codigo='E.5'), (SELECT id_asignatura FROM asignatura WHERE codigo='17'), 'rendir', 'aprobada'),
((SELECT id_asignatura FROM asignatura WHERE codigo='E.5'), (SELECT id_asignatura FROM asignatura WHERE codigo='22'), 'rendir', 'aprobada'),
((SELECT id_asignatura FROM asignatura WHERE codigo='E.5'), (SELECT id_asignatura FROM asignatura WHERE codigo='19'), 'rendir', 'aprobada'),
((SELECT id_asignatura FROM asignatura WHERE codigo='E.6'), (SELECT id_asignatura FROM asignatura WHERE codigo='12'), 'cursar', 'regular'),
((SELECT id_asignatura FROM asignatura WHERE codigo='E.6'), (SELECT id_asignatura FROM asignatura WHERE codigo='4'),  'rendir', 'aprobada');

-- Proyecto Final (36): caso especial. Todo bajo tipo='cursar' — no
-- tiene correlatividades "para rendir" porque es una materia
-- integradora sin examen final tradicional.
INSERT INTO correlatividad (id_asignatura, id_requisito, tipo, estado_requerido) VALUES
((SELECT id_asignatura FROM asignatura WHERE codigo='36'), (SELECT id_asignatura FROM asignatura WHERE codigo='25'), 'cursar', 'regular'),
((SELECT id_asignatura FROM asignatura WHERE codigo='36'), (SELECT id_asignatura FROM asignatura WHERE codigo='26'), 'cursar', 'regular'),
((SELECT id_asignatura FROM asignatura WHERE codigo='36'), (SELECT id_asignatura FROM asignatura WHERE codigo='30'), 'cursar', 'regular'),
((SELECT id_asignatura FROM asignatura WHERE codigo='36'), (SELECT id_asignatura FROM asignatura WHERE codigo='12'), 'cursar', 'aprobada'),
((SELECT id_asignatura FROM asignatura WHERE codigo='36'), (SELECT id_asignatura FROM asignatura WHERE codigo='20'), 'cursar', 'aprobada'),
((SELECT id_asignatura FROM asignatura WHERE codigo='36'), (SELECT id_asignatura FROM asignatura WHERE codigo='23'), 'cursar', 'aprobada');

-- =====================================================================
-- DATOS: Caso de Martín (estudiante de prueba obligatorio)
-- =====================================================================
INSERT INTO estudiante (nombre) VALUES ('Martín');
SET @martin := LAST_INSERT_ID();

-- Algoritmo y Estructura de Datos: NO regularizada -> debe recursarla
INSERT INTO situacion_academica (id_estudiante, id_asignatura, estado) VALUES
(@martin, (SELECT id_asignatura FROM asignatura WHERE codigo='6'), 'no_regularizada');

-- Análisis Matemático I: Regular, final pendiente
INSERT INTO situacion_academica (id_estudiante, id_asignatura, estado) VALUES
(@martin, (SELECT id_asignatura FROM asignatura WHERE codigo='1'), 'regular');

-- Física I: Regular, final pendiente
INSERT INTO situacion_academica (id_estudiante, id_asignatura, estado) VALUES
(@martin, (SELECT id_asignatura FROM asignatura WHERE codigo='3'), 'regular');

-- Resto de Primer Nivel: Aprobadas
INSERT INTO situacion_academica (id_estudiante, id_asignatura, estado) VALUES
(@martin, (SELECT id_asignatura FROM asignatura WHERE codigo='2'),   'aprobada'),
(@martin, (SELECT id_asignatura FROM asignatura WHERE codigo='5'),   'aprobada'),
(@martin, (SELECT id_asignatura FROM asignatura WHERE codigo='7'),   'aprobada'),
(@martin, (SELECT id_asignatura FROM asignatura WHERE codigo='8'),   'aprobada'),
(@martin, (SELECT id_asignatura FROM asignatura WHERE codigo='O.1'), 'aprobada');

-- El resto de las asignaturas (Nivel 2 en adelante) quedan implícitamente
-- en estado 'no_cursada' (no se insertan filas para ellas).
