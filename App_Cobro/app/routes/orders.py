from flask import Blueprint, render_template, redirect, url_for, flash, request
from ..models import Order, OrderItem, Product
from .. import db
from flask_login import login_required, current_user


orders_bp = Blueprint('orders', __name__, url_prefix='/orders', template_folder='templates')


@orders_bp.route('/create/<int:product_id>')
@login_required
def create_order(product_id):
    product = Product.query.get_or_404(product_id)
    order = Order(user_id=current_user.id, total=product.price)
    db.session.add(order)
    db.session.commit()
    item = OrderItem(order_id=order.id, product_id=product.id, quantity=1, price=product.price)
    db.session.add(item)
    db.session.commit()
    return redirect(url_for('payments.create_preference', order_id=order.id))


@orders_bp.route('/<int:id>')
@login_required
def view_order(id):
    order = Order.query.get_or_404(id)
    return render_template('order.html', order=order)

@orders_bp.route('/')
@login_required
def list_orders():
    orders = Order.query.filter_by(user_id=current_user.id).all()
    return render_template('orders.html', orders=orders)