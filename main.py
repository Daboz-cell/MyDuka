from flask import Flask, render_template, request, redirect, url_for, flash, session
from database import (
    fetch_products, fetch_sales, fetch_stock,
    insert_products, insert_sales, insert_stock,
    available_stock, sales_per_day, sales_per_product,
    profit_per_day, profit_per_product,
    insert_user, check_user, fetch_categories, fetch_users,cur
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
        cur.execute("SELECT * FROM products WHERE category_id = %s", (category_id,))
        products = cur.fetchall()
    else:
        products = fetch_products()
    categories = fetch_categories()
    return render_template('products.html', products=products, categories=categories)

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

# ------------------------------
# SALES
# ------------------------------
@app.route('/sales')
@login_required
def sales():
    sales_data = fetch_sales()
    products = fetch_products()
    users = fetch_users()
    return render_template('sales.html', sales=sales_data, products=products, users=users)

@app.route('/add_sales', methods=['GET', 'POST'])
@login_required
def add_sales():
    if request.method == 'POST':
        product_id = request.form['product_id']
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
        else:
            if bcrypt.check_password_hash(existing_user[2], password):
                session['email'] = email
                session['user_id'] = existing_user[0]
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