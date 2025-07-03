from flask import Flask

app=Flask(__name__)

#Importa as rotas para registrar no app
from app import routes

from web_routes import register_web_routes  # ← LINHA NOVA

# Registrar rotas da interface web
register_web_routes(app)  # ← LINHA NOVA