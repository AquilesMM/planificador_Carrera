"""
Planificá tu Carrera
=====================
Punto de entrada de la aplicación.

Antes de ejecutar:
  1. Crear la base de datos:  mysql -u root -p < db/schema.sql
  2. Ajustar la conexión en app/database.py (DB_CONFIG) si hace falta.
  3. Instalar dependencias:   pip install -r requirements.txt
  4. Ejecutar:                python main.py
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "app"))

from app.gui import main  # noqa: E402

if __name__ == "__main__":
    main()
