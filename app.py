from flask import Flask
from routes import routes
from database import init_db

app = Flask(__name__)
app.config.from_object('config')  # Arquivo de configuração (opcional)

app.register_blueprint(routes)

init_db()  # Inicializa o banco de dados

if __name__ == '__main__':
    app.run(debug=True)