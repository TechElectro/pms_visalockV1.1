# 🏨 Interfaz PMS Vislaock

Este proyecto es una interfaz web (frontend) y un servidor (backend) para interactuar con un sistema de gestión de propiedades (PMS) y crear tarjetas de huésped, basándose en la documentación de la API TCP/IP.

## ✨ Características

* **Check-in:** Crea nuevas tarjetas de huésped (Comando `G`).
* **Check-out:** Da de baja a un huésped de la base de datos y/o cancela su tarjeta (Comando `B`).
* **Lectura:** Verifica la información de una tarjeta (Comando `E`).

---

## 🛠️ Tecnologías Utilizadas

* **Backend:** Python
    * Flask (para el servidor web/API)
    * Flask-CORS
* **Frontend:**
    * HTML
    * CSS
    * JavaScript (Fetch API)

---

## 🚀 Instalación y Uso

Sigue estos pasos para ejecutar el proyecto.

### 1. Backend (Servidor)

Navega a la carpeta del backend y activa el entorno virtual.

```bash
# 1. Ve a la carpeta del backend
cd backend

# 2. (Si no lo has hecho) Crea un entorno virtual
python -m venv venv

# 3. Activa el entorno (Windows)
.\venv\Scripts\activate
# (macOS/Linux: source venv/bin/activate)

# 4. Instala las dependencias
pip install -r requirements.txt

# 5. Ejecuta el servidor Flask
python app.py