import psycopg2

# ------------------------------
# DATABASE CONNECTION
# ------------------------------
conn = psycopg2.connect(
    user="postgres",
    password="123456",
    host="localhost",
    port="5432",
    database="myduka_app"
)
cur = conn.cursor()

# ------------------------------
# HELPER FUNCTION TO EXECUTE QUERIES
# ------------------------------
def execute_query(query, values=None, fetch=False):
    try:
        if values:
            cur.execute(query, values)
        else:
            cur.execute(query)
        conn.commit()
        if fetch:
            return cur.fetchall()
    except psycopg2.Error as e:
        print("SQL Error:", e)
        conn.rollback()
        return None

# ------------------------------
# FETCH FUNCTIONS
# ------------------------------
def fetch_products():
    """Fetch all products with category name"""
    query = """
        SELECT p.id, p.name, p.buying_price, p.selling_price, c.name AS category_name
        FROM products p
        LEFT JOIN categories c ON p.category_id = c.id
        ORDER BY p.id
    """
    return execute_query(query, fetch=True)

def fetch_sales():
    return execute_query("SELECT * FROM sales", fetch=True)

def fetch_stock():
    return execute_query("SELECT * FROM stock", fetch=True)

def fetch_categories():
    return execute_query("SELECT id, name FROM categories ORDER BY id", fetch=True)

def fetch_products_by_category(category_id):
    return execute_query("""
        SELECT id, name, buying_price, selling_price, category_id
        FROM products
        WHERE category_id = %s
    """, (category_id,), fetch=True)

def get_data(table):
    return execute_query(f"SELECT * FROM {table}", fetch=True)

def fetch_users():
    return execute_query("SELECT id, name FROM users", fetch=True)


# ------------------------------
# INSERT FUNCTIONS
# ------------------------------
def insert_products(product_values):
    query = """
        INSERT INTO products (name, buying_price, selling_price, category_id)
        VALUES (%s, %s, %s, %s)
    """
    execute_query(query, product_values)

def insert_sales(sale_values):
    query = """
        INSERT INTO sales (product_id, user_id, quantity, total_price)
        VALUES (%s, %s, %s, %s)
    """
    execute_query(query, sale_values)

def insert_stock(stock_values):
    query = """
        INSERT INTO stock (product_id, quantity)
        VALUES (%s, %s)
    """
    execute_query(query, stock_values)

def insert_user(user_details):
    query = """
        INSERT INTO users (name, email, password, phone_number)
        VALUES (%s, %s, %s, %s)
    """
    execute_query(query, user_details)

# ------------------------------
# STOCK CHECK
# ------------------------------
def available_stock(product_id):
    total_stock = execute_query(
        "SELECT COALESCE(SUM(quantity),0) FROM stock WHERE product_id=%s",
        (product_id,), fetch=True
    )[0][0]

    total_sales = execute_query(
        "SELECT COALESCE(SUM(quantity),0) FROM sales WHERE product_id=%s",
        (product_id,), fetch=True
    )[0][0]

    return total_stock - total_sales

# ------------------------------
# REPORT FUNCTIONS
# ------------------------------
def sales_per_product():
    return execute_query("""
        SELECT p.name, SUM(p.selling_price * s.quantity) AS total_sales
        FROM products p
        INNER JOIN sales s ON s.product_id = p.id
        GROUP BY p.name
    """, fetch=True)

def sales_per_day():
    return execute_query("""
        SELECT DATE(s.created_at) AS date, SUM(p.selling_price * s.quantity) AS total_sales
        FROM products p
        INNER JOIN sales s ON s.product_id = p.id
        GROUP BY DATE(s.created_at)
    """, fetch=True)

def profit_per_product():
    return execute_query("""
        SELECT p.name, SUM((p.selling_price - p.buying_price) * s.quantity) AS profit
        FROM products p
        INNER JOIN sales s ON s.product_id = p.id
        GROUP BY p.name
    """, fetch=True)

def profit_per_day():
    return execute_query("""
        SELECT DATE(s.created_at) AS date,
               SUM((p.selling_price - p.buying_price) * s.quantity) AS profit
        FROM products p
        INNER JOIN sales s ON s.product_id = p.id
        GROUP BY DATE(s.created_at)
    """, fetch=True)

# ------------------------------
# USER FUNCTIONS
# ------------------------------
def check_user(email):
    result = execute_query(
        "SELECT * FROM users WHERE email=%s",
        (email,), fetch=True
    )
    return result[0] if result else None