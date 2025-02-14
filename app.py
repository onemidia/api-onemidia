import os
from dotenv import load_dotenv
from flask import Flask
from database import init_db
from routes import routes
from extensions import cache  # Importando o cache corretamente

load_dotenv()

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URL", "").replace("postgres://", "postgresql://")
app.config['SECRET_KEY'] = os.getenv("SECRET_KEY", "default_secret_key")
app.config['CACHE_TYPE'] = 'simple'  # Pode mudar para 'redis' se necessário

cache.init_app(app)  # Agora o cache é inicializado corretamente

init_db()  # Inicializa o banco de dados

app.register_blueprint(routes)

if __name__ == "__main__":
    app.run(debug=False)  # Evita debug em produção
