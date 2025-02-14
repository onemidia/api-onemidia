import os
import csv
from flask import Blueprint, request, jsonify, flash, redirect, url_for, render_template
from flask_caching import Cache
from werkzeug.utils import secure_filename
from sqlalchemy import text
from models import Produto
from database import get_db

routes = Blueprint("routes", __name__)

# ... (Funções auxiliares: allowed_file, formatar_numero)

@routes.route('/', methods=['GET', 'POST'])
def index():
    # ... (Código para upload e processamento do arquivo TXT com as atualizações)

@routes.route('/produtos', methods=['GET'])
@cache.cached(timeout=60, key_prefix='produtos_cache')
def get_produtos():
    # ... (Código para listar produtos com paginação)