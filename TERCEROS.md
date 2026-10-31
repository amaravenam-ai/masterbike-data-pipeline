# Dependencias y datos

Las dependencias se declaran en requirements.txt: FastAPI, Uvicorn, SQLAlchemy, psycopg2, Pydantic, python-dotenv, psutil y pytest. Se instalan desde su registro; no se incluyen sus fuentes o binarios como material propio. Conservar sus licencias al distribuir instalaciones o imágenes.
El dashboard usa HTML/CSS/JavaScript del proyecto, SVG y emojis del sistema. Se retiraron las fuentes remotas de Google Fonts; utiliza fuentes disponibles en el equipo. No se incluyen librerías minificadas descargadas. Swagger UI/Redoc servidos por FastAPI pueden solicitar sus recursos CDN al abrir la documentación interactiva; el dashboard no depende de ellos.
Los seis JSON son ejemplos del proyecto con contactos sustituidos por example.invalid y direcciones ficticias. No representan operaciones de una empresa real.

Las versiones y los metadatos de licencia/procedencia de los 26 paquetes presentes en la imagen de prueba se registran en evidencia/dependencias-python.json; el entorno está en evidencia/entorno-python-linux.txt. Se incluyen herramientas de instalación además de las dependencias de la aplicación. Estos registros no incorporan sus fuentes ni binarios al repositorio ni sustituyen sus textos de licencia.
