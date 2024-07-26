Paso 1: Instalar las dependencias geoespaciales
En un sistema basado en Debian/Ubuntu:

bash
Copy code
sudo apt-get update
sudo apt-get install binutils libproj-dev gdal-bin
En macOS usando Homebrew:

bash
Copy code
brew install gdal
Paso 2: Crear un entorno virtual y activar
bash
Copy code
python3 -m venv my_geodjango_env
source my_geodjango_env/bin/activate  # En Windows usa my_geodjango_env\Scripts\activate
Paso 3: Instalar Django y GeoDjango
bash
Copy code
pip install django
pip install psycopg2-binary  # Conector de PostgreSQL para Python
Paso 4: Crear un proyecto Django
bash
Copy code
django-admin startproject my_geodjango_project
cd my_geodjango_project
Paso 5: Configurar la base de datos PostgreSQL con PostGIS
Asegúrate de tener PostgreSQL y PostGIS instalados. Luego, crea una base de datos y habilita PostGIS:

sql
Copy code
CREATE DATABASE my_geodjango_db;
\c my_geodjango_db;
CREATE EXTENSION postgis;
Actualiza el archivo settings.py de tu proyecto Django para usar PostgreSQL:

python
Copy code
DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': 'my_geodjango_db',
        'USER': 'tu_usuario',
        'PASSWORD': 'tu_contraseña',
        'HOST': 'localhost',
        'PORT': '',
    }
}
Paso 6: Crear una aplicación Django
bash
Copy code
python manage.py startapp my_geodjango_app
Paso 7: Configurar la aplicación para usar GeoDjango
En settings.py, añade 'django.contrib.gis' y tu nueva aplicación a la lista INSTALLED_APPS:

python
Copy code
INSTALLED_APPS = [
    ...
    'django.contrib.gis',
    'my_geodjango_app',
]
Paso 8: Crear un modelo geoespacial
En my_geodjango_app/models.py, define un modelo geoespacial:

python
Copy code
from django.contrib.gis.db import models

class Location(models.Model):
    name = models.CharField(max_length=100)
    point = models.PointField()

    def __str__(self):
        return self.name
Paso 9: Migrar la base de datos
bash
Copy code
python manage.py makemigrations
python manage.py migrate
Paso 10: Probar el proyecto
Crea un superusuario para acceder al administrador de Django:

bash
Copy code
python manage.py createsuperuser
Ejecuta el servidor de desarrollo:

bash
Copy code
python manage.py runserver
Ahora puedes acceder al administrador de Django en http://127.0.0.1:8000/admin, donde podrás agregar y visualizar datos geoespaciales.
