from flask import Flask, render_template, request, redirect, url_for, flash, session
from database import (
    fetch_products, fetch_sales, fetch_stock,
    insert_products, insert_sales, insert_stock,
    available_stock, sales_per_day, sales_per_product,
    profit_per_day, profit_per_product,
    insert_user, check_user, fetch_categories
)
from flask_bcrypt import Bcrypt
from functools import wraps

app = Flask(__name__)
bcrypt = Bcrypt(app)
app.secret_key = "dgdhidhds"

def login_required(f):
    @wraps(f)
    def protected(*args, **kwargs):
        if 'email' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return protected

# ------------------------------
# HOME
# ------------------------------
@app.route('/')
@login_required
def home():
    return render_template('index.html')

# ------------------------------
# PRODUCTS
# ------------------------------
@app.route('/products')
@login_required
def products():
    products = fetch_products()
    categories = fetch_categories()
    return render_template('products.html', products=products, categories=categories)

@app.route('/add_products', methods=['POST'])
@login_required
def add_product():
    product_name = request.form['product']
    buying_price = float(request.form['buying_price'])
    selling_price = float(request.form['selling_price'])
    category_id = int(request.form.get('category_id', 1))  # default to 1 if not provided

    insert_products((product_name, buying_price, selling_price, category_id))
    flash("Product added successfully", "success")
    return redirect(url_for('products'))

# ------------------------------
# SALES
# ------------------------------
@app.route('/sales')
@login_required
def sales():
    sales_data = fetch_sales()
    products = fetch_products()
    stock = fetch_stock()
    return render_template('sales.html', sales=sales_data, products=products, stock=stock)

@app.route('/add_sales', methods=['POST'])
@login_required
def add_sales():
    pid = int(request.form['pid'])
    quantity = int(request.form['quantity'])
    user = check_user(session['email'])
    user_id = user[0] if user else 1  # default to 1 if user not found

    if available_stock(pid) < quantity:
        flash("Stock not available", "danger")
        return redirect(url_for('sales'))

    product = next((p for p in fetch_products() if p[0] == pid), None)
    if not product:
        flash("Product not found", "danger")
        return redirect(url_for('sales'))

    total_price = quantity * float(product[2])
    insert_sales((pid, user_id, quantity, total_price))
    flash("Sale added successfully", "success")
    return redirect(url_for('sales'))

# ------------------------------
# STOCK
# ------------------------------
@app.route('/stock')
@login_required
def stock():
    return render_template('stock.html', stock=fetch_stock(), products=fetch_products())

@app.route('/add_stock', methods=['POST'])
@login_required
def add_stock():
    pid = int(request.form['pid'])
    quantity = int(request.form['stock_quantity'])
    insert_stock((pid, quantity))
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

    return render_template(
        'dashboard.html',
        product_names=[i[0] for i in sales_product],
        sales_per_p=[float(i[1]) for i in sales_product],
        profit_per_p=[float(i[1]) for i in profit_product],
        days=[str(i[0]) for i in sales_day],
        sales_per_d=[float(i[1]) for i in sales_day],
        profit_per_d=[float(i[1]) for i in profit_day]
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

        if not check_user(email):
            hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
            insert_user((full_name, email, hashed_password, phone_number))
            flash("User registered successfully", "success")
            return redirect(url_for('login'))
        else:
            flash("User already exists, please login", "danger")

    return render_template("register.html")

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == "POST":
        email = request.form['email']
        password = request.form['password']
        user = check_user(email)
        if user and bcrypt.check_password_hash(user[3], password):
            session['email'] = email
            flash("Logged in successfully", "success")
            return redirect(url_for('home'))
        else:
            flash("Invalid email or password", "danger")
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    session.pop('email', None)
    flash("Logged out", "info")


# ------------------------------
# RUN APP
# ------------------------------
if __name__ == "__main__":
    app.run(debug=True)