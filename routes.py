import os
import csv
from flask import Flask, Blueprint, request, jsonify, flash, redirect, url_for, render_template
from flask_caching import Cache
from werkzeug.serving import WSGIRequestHandler
from werkzeug.utils import secure_filename
from sqlalchemy import text, exc
from models import Produto
from database import get_db

# Configuração do Flask
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') # Configuração da SECRET_KEY
# Aumenta o timeout global para 60 segundos
WSGIRequestHandler.timeout = 60

# Configuração do cache
cache = Cache(config={'CACHE_TYPE': 'simple'})
cache.init_app(app)

# Configuração de uploads
UPLOAD_FOLDER = './uploads'
ALLOWED_EXTENSIONS = {'txt'}

# Criação do Blueprint
routes = Blueprint("routes", __name__)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1).lower() in ALLOWED_EXTENSIONS

def formatar_numero(valor):
    try:
        valor = valor.replace(',', '.')  # Substitui vírgula por ponto
        numero = float(valor)
        # Formata o número com duas casas decimais, preservando os zeros
        return "{:.2f}".format(numero)
    except ValueError:
        return None  # Retorna None para valores inválidos

@routes.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('Nenhum arquivo enviado', 'error')
            return redirect(url_for('routes.index'))

        arquivo = request.files['file']
        if arquivo.filename == '':
            flash('Nenhum arquivo selecionado', 'error')
            return redirect(url_for('routes.index'))

        if arquivo and allowed_file(arquivo.filename):
            filename = secure_filename(arquivo.filename)
            os.makedirs(UPLOAD_FOLDER, exist_ok=True)
            file_path = os.path.join(UPLOAD_FOLDER, filename)
            arquivo.save(file_path)

            with open(file_path, 'r', encoding='utf-8') as file:
                reader = csv.reader(file, delimiter=';')
                produtos =  # Inicializa a lista de produtos

                db_session = next(get_db())
                db_session.execute(text("SET statement_timeout TO 30000;"))
                try:
                    db_session.query(Produto).delete()
                    db_session.commit()
                except exc.SQLAlchemyError as e:
                    db_session.rollback()
                    flash(f'Erro ao limpar a tabela: {str(e)}', 'error')
                    return render_template('index.html')

                for row in reader:
                    try:
                        if len(row) < 4:
                            flash(f'Erro: linha inválida {row}', 'error')
                            continue

                        id_produto = row.zfill(10)  # Corrigido: row em vez de row
                        descricao = row  # Corrigido: row em vez de row
                        valor = formatar_numero(row)  # Corrigido: row em vez de row
                        unidade = row  # Corrigido: row em vez de row

                        if valor is None:
                            flash(f'Erro: valor inválido {row} na linha {row}', 'error')
                            continue

                        produto_existente = db_session.query(Produto).filter_by(codigo=id_produto).first()
                        if produto_existente:
                            produto_existente.descricao = descricao
                            produto_existente.valor = valor
                            produto_existente.unidade = unidade
                        else:
                            # Cria um novo produto se não existir
                            produto = Produto(id=int(id_produto), codigo=id_produto, descricao=descricao, valor=valor, unidade=unidade)
                            db_session.add(produto)
                        produtos.append(produto)
                    except (ValueError, IndexError, exc.SQLAlchemyError) as e:
                        db_session.rollback()
                        flash(f'Erro ao processar linha: {row} - {str(e)}', 'error')
                        continue

                try:
                    if produtos:
                        db_session.commit()
                        cache.delete('produtos_cache')
                        flash('Arquivo enviado e atualizado com sucesso!', 'success')
                    else:
                        flash('Nenhum produto processado. Verifique o arquivo.', 'warning')
                except exc.SQLAlchemyError as e:
                    db_session.rollback()
                    flash(f'Erro ao salvar dados: {str(e)}', 'error')

            return redirect(url_for('routes.index'))

    return render_template('index.html')

@routes.route('/produtos', methods=['GET'])
@cache.cached(timeout=60, key_prefix='produtos_cache')
def get_produtos():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)

    db_session = next(get_db())
    db_session.execute(text("SET statement_timeout TO 30000;"))
    produtos = db_session.query(Produto).limit(per_page).offset((page - 1) * per_page).all()

    return jsonify([
        {
            'id': produto.id,
            'codigo': produto.codigo,
            'descricao': produto.descricao,
            'valor': produto.valor,
            'unidade': produto.unidade
        } for produto in produtos
    ])

app.register_blueprint(routes)

if __name__ == '__main__':
    app.run(debug=True, threaded=True)