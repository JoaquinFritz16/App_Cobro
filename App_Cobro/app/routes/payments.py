import os
from flask import Blueprint, render_template, request, jsonify, url_for
from app.models import Order, Payment
from app import db
import mercadopago
from dotenv import load_dotenv
from flask_login import login_required, current_user

load_dotenv()

payments_bp = Blueprint('payments', __name__, url_prefix='/payments', template_folder='templates')

sdk = mercadopago.SDK(os.getenv("MP_ACCESS_TOKEN"))
print("Access token usado:", os.getenv("MP_ACCESS_TOKEN"))
def prod_title(order_item):
    try:
        return order_item.product.title
    except Exception:
        return 'Producto'


@payments_bp.route('/create_preference/<int:order_id>', methods=['GET'])
@login_required
def create_preference(order_id):
    order = Order.query.get_or_404(order_id)

    items = []
    for it in order.items:
        items.append({
            "title": prod_title(it),
            "quantity": int(it.quantity),
            "currency_id": "ARS",
            "unit_price": float(it.price)
        })

    preference_data = {
    "items": items,
    "auto_return": "approved",
    "back_urls": {
        "success": f"https://proleptically-pseudoallegoristic-monika.ngrok-free.app/payments/success/1",
        "failure": f"https://proleptically-pseudoallegoristic-monika.ngrok-free.app/payments/failure/1",
        "pending": f"https://proleptically-pseudoallegoristic-monika.ngrok-free.app/payments/pending/1"
    },
    "external_reference": str(order_id)
}


    preference_response = sdk.preference().create(preference_data)
    preference = preference_response["response"]

    if "id" not in preference:
        print("⚠️ Error creando preferencia:", preference_response)
        return "Error creando preferencia", 500

    pay = Payment(
        order_id=order.id,
        status='created',
        mercadopago_payment_id=preference.get('id'),
        raw_response=str(preference)
    )
    db.session.add(pay)
    db.session.commit()

    print("✅ Preferencia creada:", preference.get("id"))

    return render_template(
        "checkout.html",
        preference=preference,
        mp_public_key=os.getenv("MP_PUBLIC_KEY"),
        items=items,
        order=order 
    )


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
    return "Pago aprobado con éxito."

@payments_bp.route('/payment/failure')
def payment_failure():
    return "El pago falló o fue cancelado."

@payments_bp.route('/payment/pending')
def payment_pending():
    return "El pago está pendiente de aprobación."
@payments_bp.route('/pay_with_wallet/<int:order_id>', methods=['POST'])
@login_required
def pay_with_wallet(order_id):
    order = Order.query.get_or_404(order_id)
    if current_user.wallet_balance >= float(order.total):
        current_user.wallet_balance -= float(order.total)
        order.status = 'paid'
        db.session.commit()
        return render_template("success.html", order=order)
    else:
        return "Saldo insuficiente", 400

