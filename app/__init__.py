from flask import Flask

app=Flask(__name__)

#Importa as rotas para registrar no app
from app import routes