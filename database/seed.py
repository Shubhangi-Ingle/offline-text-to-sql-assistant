import os
import random
from datetime import date, timedelta

import psycopg2
from dotenv import load_dotenv
from faker import Faker

load_dotenv()
fake = Faker("en_IN")
Faker.seed(42)
random.seed(42)

NUM_CUSTOMERS = 200
NUM_ORDERS = 1500
START_DATE = date(2023, 1, 1)
END_DATE = date(2026, 9, 30)

CATALOG = {
    "Electronics": [
        ("Wireless Earbuds", 1999), ("Bluetooth Speaker", 2499),
        ("Smart Watch", 4999), ("Power Bank 20000mAh", 1799),
        ("USB-C Charger", 899), ("Webcam HD", 2199),
        ("Wireless Mouse", 699), ("Mechanical Keyboard", 3499),
    ],
    "Home & Kitchen": [
        ("Air Fryer", 5499), ("Mixer Grinder", 3299),
        ("Electric Kettle", 1199), ("Non-stick Cookware Set", 2799),
        ("Water Purifier", 11999), ("Vacuum Flask", 799),
        ("Dinner Set 24pc", 2599), ("Induction Cooktop", 2999),
    ],
    "Fashion": [
        ("Cotton T-Shirt", 499), ("Denim Jeans", 1499),
        ("Running Shoes", 2499), ("Leather Wallet", 699),
        ("Formal Shirt", 1199), ("Backpack 30L", 1299),
        ("Sunglasses", 999), ("Hoodie", 1599),
    ],
    "Books": [
        ("Python Crash Course", 699), ("Atomic Habits", 499),
        ("Data Structures Handbook", 599), ("Deep Learning Basics", 899),
        ("The Psychology of Money", 399), ("Clean Code", 749),
        ("SQL Cookbook", 649), ("Ikigai", 299),
    ],
    "Sports": [
        ("Yoga Mat", 799), ("Dumbbell Set 10kg", 1899),
        ("Cricket Bat", 2199), ("Badminton Racket", 1299),
        ("Football", 899), ("Skipping Rope", 249),
        ("Resistance Bands", 599), ("Fitness Tracker", 2999),
    ],
    "Beauty": [
        ("Face Wash", 249), ("Sunscreen SPF 50", 449),
        ("Hair Dryer", 1499), ("Beard Trimmer", 1299),
        ("Moisturizer", 399), ("Perfume 100ml", 1199),
        ("Shampoo 500ml", 349), ("Lip Balm Pack", 199),
    ],
}

LOCATIONS = [
    ("Mumbai", "Maharashtra"), ("Pune", "Maharashtra"), ("Nagpur", "Maharashtra"),
    ("Akola", "Maharashtra"), ("Bengaluru", "Karnataka"), ("Hyderabad", "Telangana"),
    ("Chennai", "Tamil Nadu"), ("Delhi", "Delhi"), ("Ahmedabad", "Gujarat"),
    ("Jaipur", "Rajasthan"), ("Kolkata", "West Bengal"), ("Indore", "Madhya Pradesh"),
]

STATUSES = ["delivered", "shipped", "pending", "cancelled", "returned"]
STATUS_WEIGHTS = [70, 8, 7, 8, 7]
METHODS = ["card", "upi", "netbanking", "cash_on_delivery"]
METHOD_WEIGHTS = [25, 45, 15, 15]


def random_date(start, end):
    return start + timedelta(days=random.randint(0, (end - start).days))


conn = psycopg2.connect(
    host=os.getenv("DB_HOST", "localhost"),
    port=os.getenv("DB_PORT", "5432"),
    dbname=os.getenv("DB_NAME"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
)
cur = conn.cursor()

cur.execute(
    "TRUNCATE payments, order_items, orders, products, categories, customers "
    "RESTART IDENTITY CASCADE"
)

# Categories and products
product_prices = {}
for cat_name, items in CATALOG.items():
    cur.execute(
        "INSERT INTO categories (category_name) VALUES (%s) RETURNING category_id",
        (cat_name,),
    )
    cat_id = cur.fetchone()[0]
    for name, base_price in items:
        price = round(base_price * random.uniform(0.95, 1.05), 2)
        cur.execute(
            "INSERT INTO products (product_name, category_id, price, stock_quantity) "
            "VALUES (%s, %s, %s, %s) RETURNING product_id",
            (name, cat_id, price, random.randint(0, 300)),
        )
        product_prices[cur.fetchone()[0]] = price

# Customers
customers = []
for _ in range(NUM_CUSTOMERS):
    city, state = random.choice(LOCATIONS)
    signup = random_date(START_DATE, date(2025, 12, 31))
    cur.execute(
        "INSERT INTO customers (full_name, email, city, state, signup_date) "
        "VALUES (%s, %s, %s, %s, %s) RETURNING customer_id",
        (fake.name(), fake.unique.email(), city, state, signup),
    )
    customers.append((cur.fetchone()[0], signup))

# Orders, order items, payments
product_ids = list(product_prices.keys())
for _ in range(NUM_ORDERS):
    customer_id, signup = random.choice(customers)
    order_date = random_date(signup, END_DATE)
    status = random.choices(STATUSES, STATUS_WEIGHTS)[0]

    cur.execute(
        "INSERT INTO orders (customer_id, order_date, status) "
        "VALUES (%s, %s, %s) RETURNING order_id",
        (customer_id, order_date, status),
    )
    order_id = cur.fetchone()[0]

    total = 0
    for pid in random.sample(product_ids, random.randint(1, 4)):
        qty = random.randint(1, 3)
        unit_price = product_prices[pid]
        total += qty * unit_price
        cur.execute(
            "INSERT INTO order_items (order_id, product_id, quantity, unit_price) "
            "VALUES (%s, %s, %s, %s)",
            (order_id, pid, qty, unit_price),
        )

    # Pending orders have no payment yet
    if status == "pending":
        continue

    if status in ("delivered", "shipped"):
        pay_status = "paid"
    elif status == "returned":
        pay_status = "refunded"
    else:  # cancelled
        pay_status = random.choices(["refunded", "failed"], [70, 30])[0]

    cur.execute(
        "INSERT INTO payments (order_id, amount, payment_method, payment_status, payment_date) "
        "VALUES (%s, %s, %s, %s, %s)",
        (
            order_id,
            round(total, 2),
            random.choices(METHODS, METHOD_WEIGHTS)[0],
            pay_status,
            order_date + timedelta(days=random.randint(0, 2)),
        ),
    )

conn.commit()

for table in ["customers", "categories", "products", "orders", "order_items", "payments"]:
    cur.execute(f"SELECT COUNT(*) FROM {table}")
    print(f"{table}: {cur.fetchone()[0]} rows")

cur.close()
conn.close()