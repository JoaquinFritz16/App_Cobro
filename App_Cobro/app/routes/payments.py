from flask import Blueprint, render_template, redirect, url_for, request, jsonify
from ..models import Order, Payment
from .. import db
import os
import mercadopago

payments_bp = Blueprint('payments', __name__, url_prefix='/payments', template_folder='templates')


def prod_title(order_item):
    try:
        return order_item.product.title
    except Exception:
        return 'Producto'


@payments_bp.route('/create_preference/<int:order_id>')
def create_preference(order_id):
    order = Order.query.get_or_404(order_id)
    sdk = mercadopago.SDK(os.getenv('MP_ACCESS_TOKEN'))

    items = []
    for it in order.items:
        items.append({
            'title': prod_title(it),
            'quantity': int(it.quantity),
            'unit_price': float(it.price)
        })

    preference_data = {
        'items': items,
        'back_urls': {
            'success': url_for('payments.success', order_id=order.id, _external=True),
            'failure': url_for('payments.failure', order_id=order.id, _external=True),
            'pending': url_for('payments.pending', order_id=order.id, _external=True)
        },
        'auto_return': 'approved'
    }

    # Crear preferencia en MercadoPago
    preference_response = sdk.preference().create(preference_data)
    preference = preference_response['response']

    # Guardar registro de pago
    pay = Payment(
        order_id=order.id,
        status='created',
        mercadopago_payment_id=preference.get('id'),
        raw_response=str(preference)
    )
    db.session.add(pay)
    db.session.commit()

    # Renderizar checkout
    return render_template(
    'checkout.html',
    preference=preference,
    mp_public_key=os.getenv('MP_PUBLIC_KEY'),
    items=items  # <-- PASAMOS la lista de items que sí es iterable
)



@payments_bp.route('/success')
def success():
    order_id = request.args.get('order_id')
    order = Order.query.get_or_404(order_id)
    order.status = 'paid'
    db.session.commit()
    return render_template('payment_success.html', order=order)


@payments_bp.route('/failure')
def failure():
    order_id = request.args.get('order_id')
    order = Order.query.get_or_404(order_id)
    order.status = 'failed'
    db.session.commit()
    return render_template('payment_failure.html', order=order)


@payments_bp.route('/pending')
def pending():
    order_id = request.args.get('order_id')
    order = Order.query.get_or_404(order_id)
    order.status = 'pending'
    db.session.commit()
    return render_template('payment_pending.html', order=order)


@payments_bp.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json() or request.form.to_dict()
    # Aquí podrías procesar el webhook real
    return jsonify({'status': 'ok'})
