from flask import Flask
from .views import bp
from .scheduler import start_scheduler
from .models import Base
from .database import engine

app = Flask(__name__)

# Crear tablas en la base de datos
Base.metadata.create_all(bind=engine)

# Registrar rutas
app.register_blueprint(bp)

# Iniciar tareas periódicas
start_scheduler()