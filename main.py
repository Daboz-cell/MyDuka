from flask import Flask, render_template, request, redirect, url_for, flash, session
from database import (
    fetch_products, fetch_sales, fetch_stock,
    insert_products, insert_sales, insert_stock,
    available_stock, sales_per_day, sales_per_product,
    profit_per_day, profit_per_product,
    insert_user, check_user, fetch_categories, fetch_users,cur,fetch_top_product,fetch_products_by_category,get_db_connection
)
from flask_bcrypt import Bcrypt
from functools import wraps

# ------------------------------
# FLASK SETUP
# ------------------------------
app = Flask(__name__)
bcrypt = Bcrypt(app)
app.secret_key = "dgdhidhds"  # Replace with a secure key or env variable

# ------------------------------
# LOGIN REQUIRED DECORATOR
# ------------------------------
def login_required(f):
    @wraps(f)
    def protected(*args, **kwargs):
        if 'email' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return protected

# ------------------------------
# ROUTES
# ------------------------------

@app.route('/')
@login_required
def home():
    categories = fetch_categories()
    return render_template('index.html', categories=categories)

# ------------------------------
# PRODUCTS
# ------------------------------
@app.route('/products')
@login_required
def products():
    category_id = request.args.get('category_id')

    if category_id:
        products = fetch_products_by_category(category_id)
    else:
        products = fetch_products()

    categories = fetch_categories()

    # ---- stats ----
    total_products = len(products)
    total_categories = len(categories)
    if total_products > 0:
        avg_markup = (
            (sum([p[3] for p in products]) / sum([p[2] for p in products])) * 100 - 100
        )
    else:
        avg_markup = 0

    return render_template(
        'products.html',
        products=products,
        categories=categories,
        total_products=total_products,
        total_categories=total_categories,
        avg_markup=round(avg_markup, 1)
    )


@app.route('/add_products', methods=['GET', 'POST'])
def add_product():
    if request.method == 'POST':
        product_name = request.form['product']
        buying_price = request.form['buying_price']
        selling_price = request.form['selling_price']
        category_id = request.form['category_id']
        insert_products((product_name, buying_price, selling_price, category_id))
        flash("Product added successfully", "success")
        return redirect(url_for('products'))
    return render_template('products.html')

@app.route('/edit_product/<int:product_id>', methods=['GET', 'POST'])
@login_required
def edit_product(product_id):
    conn = get_db_connection()
    cur = conn.cursor()

    if request.method == 'POST':
        name = request.form['name']
        buying_price = request.form['buying_price']
        selling_price = request.form['selling_price']
        category_id = request.form['category_id']

        cur.execute("""
            UPDATE products
            SET name=%s, buying_price=%s, selling_price=%s, category_id=%s
            WHERE id=%s
        """, (name, buying_price, selling_price, category_id, product_id))
        conn.commit()
        cur.close()
        conn.close()
        flash('Product updated successfully!', 'success')
        return redirect(url_for('products'))

    cur.execute("SELECT id, name, buying_price, selling_price, category_id FROM products WHERE id=%s", (product_id,))
    product = cur.fetchone()
    cur.close()
    conn.close()

    categories = fetch_categories()
    return render_template('edit_product.html', product=product, categories=categories)


@app.route('/delete_product/<int:product_id>')
@login_required
def delete_product(product_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM products WHERE id=%s", (product_id,))
    conn.commit()
    cur.close()
    conn.close()
    flash('Product deleted successfully!', 'danger')
    return redirect(url_for('products'))

# ------------------------------
# SALES
# ------------------------------
@app.route('/sales')
@login_required
def sales():
    sales_data = fetch_sales()
    products = fetch_products()
    users = fetch_users()
    top_product = fetch_top_product()   
    return render_template(
        'sales.html',
        sales=sales_data,
        products=products,
        users=users,
        top_product=top_product
    )


@app.route('/add_sales', methods=['GET', 'POST'])
@login_required
def add_sales():
    if request.method == 'POST':
        product_id = request.form['pid']
        user_id = request.form['user_id']
        quantity = int(request.form['quantity'])
        if available_stock(product_id) < quantity:
            flash("Stock not available", "danger")
            return redirect(url_for('sales'))
        cur.execute("SELECT selling_price FROM products WHERE id = %s", (product_id,))
        selling_price = cur.fetchone()[0]
        total_price = quantity * float(selling_price)
        new_sale = (product_id, user_id, quantity, total_price)
        insert_sales(new_sale)
        flash("Sale added successfully", "success")
        return redirect(url_for('sales'))
    return render_template('sales.html')

# ------------------------------
# STOCK
# ------------------------------
@app.route('/stock')
@login_required
def stock():
    stock_data = fetch_stock()
    products = fetch_products()
    return render_template('stock.html', stock=stock_data, products=products)

@app.route('/add_stock', methods=['POST'])
@login_required
def add_stock():
    pid = int(request.form["pid"])
    quantity = int(request.form["stock_quantity"])
    new_stock = (pid, quantity)
    insert_stock(new_stock)
    flash("Stock added successfully", "success")
    return redirect(url_for('stock'))

@app.route('/edit_stock/<int:stock_id>', methods=['GET', 'POST'])
@login_required
def edit_stock(stock_id):
    cur.execute("SELECT * FROM stock WHERE id=%s", (stock_id,))
    stock = cur.fetchone()

    products = fetch_products()

    if request.method == 'POST':
        product_id = request.form['product_id']
        quantity = request.form['quantity']

        cur.execute("""
            UPDATE stock
            SET product_id=%s, quantity=%s
            WHERE id=%s
        """, (product_id, quantity, stock_id))
        cur.connection.commit()

        flash("Stock updated successfully!", "success")
        return redirect(url_for('stock'))

    return render_template("edit_stock.html", stock=stock, products=products)


@app.route('/delete_stock/<int:stock_id>')
@login_required
def delete_stock(stock_id):
    cur.execute("DELETE FROM stock WHERE id=%s", (stock_id,))
    cur.connection.commit()
    flash("Stock deleted successfully!", "danger")
    return redirect(url_for('stock'))

# ------------------------------
# DASHBOARD
# ------------------------------
@app.route('/dashboard')
@login_required
def dashboard():
    sales_product = sales_per_product()
    profit_product = profit_per_product()
    sales_day = sales_per_day()
    profit_day = profit_per_day()

    product_names = [i[0] for i in sales_product]
    sales_per_p = [float(i[1]) for i in sales_product]
    profit_per_p = [float(i[1]) for i in profit_product]
    days = [str(i[0]) for i in sales_day]
    sales_per_d = [float(i[1]) for i in sales_day]
    profit_per_d = [float(i[1]) for i in profit_day]

    return render_template(
        'dashboard.html',
        product_names=product_names,
        sales_per_p=sales_per_p,
        profit_per_p=profit_per_p,
        days=days,
        sales_per_d=sales_per_d,
        profit_per_d=profit_per_d
    )

# ------------------------------
# USER AUTH
# ------------------------------
# ------------------------------
# USER AUTH
# ------------------------------
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == "POST":
        full_name = request.form['name']
        email = request.form['email']
        phone_number = request.form['phone_number']
        password = request.form['password']

        existing_user = check_user(email)
        if not existing_user:
            hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
            new_user = (full_name, email, hashed_password, phone_number)
            insert_user(new_user)
            flash("User registered successfully", "success")
            return redirect(url_for('login'))
        else:
            flash("User already exists, please login", "danger")

    return render_template("register.html")


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        existing_user = check_user(email)
        if not existing_user:
            flash("User does not exist, please register", "danger")
            return redirect(url_for('register'))

        user_id, name, email_db, stored_hash, phone_number = existing_user

        if bcrypt.check_password_hash(stored_hash, password):
            session['email'] = email_db
            session['user_id'] = user_id
            flash("Logged in successfully", "success")
            return redirect(url_for('home'))
        else:
            flash("Password incorrect, try again", "danger")

    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    session.pop('email', None)
    session.pop('user_id', None)
    flash("Logged out", "info")
    return redirect(url_for('login'))

# ------------------------------
# RUN APP
# ------------------------------
if __name__ == "__main__":
    app.run(debug=True)