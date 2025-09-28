from flask import Blueprint, render_template, redirect, url_for, flash, request
from ..models import Product
from .. import db
from ..forms import ProductForm
from flask_login import login_required


products_bp = Blueprint('products', __name__, url_prefix='/', template_folder='templates')


@products_bp.route('/')
def list_products():
    products = Product.query.all()
    return render_template('products.html', products=products)


@products_bp.route('/product/new', methods=['GET','POST'])
@login_required
def new_product():
    form = ProductForm()
    if form.validate_on_submit():
        p = Product(title=form.title.data, description=form.description.data, price=form.price.data, available=form.available.data)
        db.session.add(p)
        db.session.commit()
        flash('Producto creado')
        return redirect(url_for('products.list_products'))
    return render_template('product_form.html', form=form)


@products_bp.route('/product/<int:id>/edit', methods=['GET','POST'])
@login_required
def edit_product(id):
    p = Product.query.get_or_404(id)
    form = ProductForm(obj=p)
    if form.validate_on_submit():
        form.populate_obj(p)
        db.session.commit()
        flash('Producto actualizado')
        return redirect(url_for('products.list_products'))
    return render_template('product_form.html', form=form)


@products_bp.route('/product/<int:id>/delete', methods=['POST'])
@login_required
def delete_product(id):
    p = Product.query.get_or_404(id)
    db.session.delete(p)
    db.session.commit()
    flash('Producto eliminado')
    return redirect(url_for('products.list_products'))