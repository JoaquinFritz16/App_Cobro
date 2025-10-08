import os
from flask import Blueprint, render_template, request, jsonify, url_for
from app.models import Order, Payment
from app import db
import mercadopago
from dotenv import load_dotenv
from flask_login import login_required, current_user

load_dotenv()

# Blueprint
payments_bp = Blueprint('payments', __name__, url_prefix='/payments', template_folder='templates')

# SDK de Mercado Pago
sdk = mercadopago.SDK(os.getenv("MP_ACCESS_TOKEN"))
print("Access token usado:", os.getenv("MP_ACCESS_TOKEN"))


# 🧩 Función auxiliar para obtener el título del producto
def prod_title(order_item):
    try:
        return order_item.product.title
    except Exception:
        return 'Producto'

# 💳 Crear preferencia de pago
@payments_bp.route('/create_preference/<int:order_id>', methods=['GET'])
@login_required
def create_preference(order_id):
    order = Order.query.get_or_404(order_id)

    # Construir la lista de ítems
    items = []
    for it in order.items:
        items.append({
            "title": prod_title(it),
            "quantity": int(it.quantity),
            "currency_id": "ARS",
            "unit_price": float(it.price)
        })

    # Datos de preferencia
    preference_data = {
        "items": items,
        "back_urls": {
            "success": url_for('payments.success', order_id=order.id, _external=True),
            "failure": url_for('payments.failure', order_id=order.id, _external=True),
            "pending": url_for('payments.pending', order_id=order.id, _external=True)
        },
        "auto_return": "approved",
        "external_reference": str(order.id)
    }

    # Crear preferencia en Mercado Pago
    preference_response = sdk.preference().create(preference_data)
    preference = preference_response["response"]

    # Registrar el pago en BD (estado inicial)
    pay = Payment(
        order_id=order.id,
        status='created',
        mercadopago_payment_id=preference.get('id'),
        raw_response=str(preference)
    )
    db.session.add(pay)
    db.session.commit()
    result = sdk.preference().create(preference_data)
    preference = result["response"]

    if "id" not in preference:
        print("⚠️ Error creando preferencia:", result)

    # Renderizar el checkout
    print("Preferencia creada:", preference.get("id")),
    return render_template(
        "checkout.html",
        preference=preference,
        mp_public_key=os.getenv("MP_PUBLIC_KEY"),
        items=items  # ✅ pasamos la lista de ítems iterable
    )

# ✅ Rutas de resultado
@payments_bp.route('/success/<int:order_id>')
@login_required
def success(order_id):
    order = Order.query.get_or_404(order_id)
    order.status = 'paid'
    db.session.commit()
    return render_template("success.html", order=order)

@payments_bp.route('/failure/<int:order_id>')
@login_required
def failure(order_id):
    order = Order.query.get_or_404(order_id)
    order.status = 'failed'
    db.session.commit()
    return render_template("failure.html", order=order)

@payments_bp.route('/pending/<int:order_id>')
@login_required
def pending(order_id):
    order = Order.query.get_or_404(order_id)
    order.status = 'pending'
    db.session.commit()
    return render_template("pending.html", order=order)

# 📩 Webhook (notificaciones de Mercado Pago)
@payments_bp.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json() or request.form.to_dict()
    print("Webhook recibido:", data)

    if data and "data" in data and "id" in data["data"]:
        payment_id = data["data"]["id"]
        payment_info = sdk.payment().get(payment_id)
        info = payment_info["response"]

        order_id = int(info.get("external_reference", 0))
        order = Order.query.get(order_id)

        if order:
            status = info.get("status", "unknown")
            payment = Payment(
                order_id=order.id,
                status=status,
                mercadopago_payment_id=str(payment_id),
                raw_response=str(info)
            )
            order.status = status
            db.session.add(payment)
            db.session.commit()

    return jsonify({"status": "ok"}), 200

@payments_bp.route('/payment/success')
def payment_success():
    return "✅ Pago aprobado con éxito."

@payments_bp.route('/payment/failure')
def payment_failure():
    return "❌ El pago falló o fue cancelado."

@payments_bp.route('/payment/pending')
def payment_pending():
    return "⏳ El pago está pendiente de aprobación."

