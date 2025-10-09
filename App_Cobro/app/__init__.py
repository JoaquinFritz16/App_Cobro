from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from dotenv import load_dotenv
import os
load_dotenv()


db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'




def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///db.sqlite3')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Inicializar extensiones
    db.init_app(app)
    login_manager.init_app(app)

    from . import models
    # Crear las tablas **antes de registrar cualquier blueprint**
    with app.app_context():
        db.create_all()

    # Registrar blueprints después de crear tablas
    from .routes.auth import auth_bp
    from .routes.products import products_bp
    from .routes.orders import orders_bp
    from .routes.payments import payments_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(products_bp)
    app.register_blueprint(orders_bp)
    app.register_blueprint(payments_bp)

    return app
