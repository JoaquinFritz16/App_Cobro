from app import create_app, db
from app.models import Product

# 🔹 Crear la app
app = create_app()

# 🔹 Abrir un contexto de app
with app.app_context():
    # Crear un producto de prueba
    p = Product(title="Test", description="Producto de prueba", price=100.00)
    db.session.add(p)
    db.session.commit()

    # Consultar productos
    productos = Product.query.all()
    for prod in productos:
        print(prod.title, prod.price)
