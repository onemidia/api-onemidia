import os
import csv
from flask import Blueprint, request, jsonify, flash, redirect, url_for, render_template
from werkzeug.utils import secure_filename
from sqlalchemy import text, exc
from models import Produto
from database import get_db
from extensions import cache

# Configuração do upload
UPLOAD_FOLDER = './uploads'
ALLOWED_EXTENSIONS = {'txt'}

routes = Blueprint("routes", __name__)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[-1].lower() in ALLOWED_EXTENSIONS

def formatar_numero(valor):
    try:
        valor = valor.replace(',', '.')  # Substitui vírgula por ponto
        return "{:.2f}".format(float(valor))  # Formata com duas casas decimais
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
                produtos = []

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

                        id_produto = row[0].zfill(10)  # Corrigido
                        descricao = row[1]  # Corrigido
                        valor = formatar_numero(row[2])  # Corrigido
                        unidade = row[3]  # Corrigido

                        if valor is None:
                            flash(f'Erro: valor inválido {row}', 'error')
                            continue

                        produto_existente = db_session.query(Produto).filter_by(codigo=id_produto).first()
                        if produto_existente:
                            produto_existente.descricao = descricao
                            produto_existente.valor = valor
                            produto_existente.unidade = unidade
                        else:
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
                        cache.delete('produtos_cache')  # Agora funciona corretamente
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
            'valor': formatar_numero(str(produto.valor).replace('.', ',')),  # Formata o valor
            'unidade': produto.unidade
        } for produto in produtos
    ])