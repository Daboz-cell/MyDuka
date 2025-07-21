import psycopg2

conn = psycopg2.connect(user="postgres",password='123456',host='localhost',port='5432',database='myduka_app')

cur = conn.cursor()

def fetch_products():
    cur.execute("Select * from products")
    products = cur.fetchall()
    return products

products= fetch_products()

def insert_products():
    cur.execute("insert into products(name,buying_price,selling_price)values('milk',40,60);")
    conn.commit()
 
insert_products()

print(products)