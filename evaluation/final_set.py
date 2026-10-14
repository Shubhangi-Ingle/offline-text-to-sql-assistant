# Final test set: written AFTER tuning was finished. Run once per model. Do not tune on it.
# Ids 201-206 are easy, 207-214 medium, 215-220 hard.

FINAL_CASES = [
    # ---------------- EASY ----------------
    {"id": 201, "difficulty": "easy",
     "question": "How many customers signed up before 2024?",
     "gold_sql": "SELECT COUNT(*) FROM customers WHERE signup_date < '2024-01-01'"},

    {"id": 202, "difficulty": "easy",
     "question": "What is the most expensive product?",
     "gold_sql": "SELECT product_name, price FROM products ORDER BY price DESC LIMIT 1"},

    {"id": 203, "difficulty": "easy",
     "question": "How many products belong to the Home & Kitchen category?",
     "gold_sql": "SELECT COUNT(*) FROM products p JOIN categories c ON c.category_id = p.category_id WHERE c.category_name = 'Home & Kitchen'"},

    {"id": 204, "difficulty": "easy",
     "question": "How many orders are there in total?",
     "gold_sql": "SELECT COUNT(*) FROM orders"},

    {"id": 205, "difficulty": "easy",
     "question": "How many customers live in Bengaluru?",
     "gold_sql": "SELECT COUNT(*) FROM customers WHERE city = 'Bengaluru'"},

    {"id": 206, "difficulty": "easy",
     "question": "What is the lowest stock quantity among all products?",
     "gold_sql": "SELECT MIN(stock_quantity) FROM products"},

    # ---------------- MEDIUM ----------------
    {"id": 207, "difficulty": "medium",
     "question": "How many orders were delivered in 2026?",
     "gold_sql": "SELECT COUNT(*) FROM orders WHERE status = 'delivered' AND order_date >= '2026-01-01' AND order_date < '2027-01-01'"},

    {"id": 208, "difficulty": "medium",
     "question": "What is the average amount of paid card payments?",
     "gold_sql": "SELECT AVG(amount) FROM payments WHERE payment_method = 'card' AND payment_status = 'paid'"},

    {"id": 209, "difficulty": "medium",
     "question": "How many customers from Gujarat have placed at least one order?",
     "gold_sql": "SELECT COUNT(DISTINCT o.customer_id) FROM orders o JOIN customers c ON c.customer_id = o.customer_id WHERE c.state = 'Gujarat'"},

    {"id": 210, "difficulty": "medium",
     "question": "What is the total amount of failed payments?",
     "gold_sql": "SELECT SUM(amount) FROM payments WHERE payment_status = 'failed'"},

    {"id": 211, "difficulty": "medium",
     "question": "How many orders were placed in December 2025?",
     "gold_sql": "SELECT COUNT(*) FROM orders WHERE order_date >= '2025-12-01' AND order_date < '2026-01-01'"},

    {"id": 212, "difficulty": "medium",
     "question": "How many products cost more than 2000?",
     "gold_sql": "SELECT COUNT(*) FROM products WHERE price > 2000"},

    {"id": 213, "difficulty": "medium",
     "question": "How many payments were made via cash on delivery?",
     "gold_sql": "SELECT COUNT(*) FROM payments WHERE payment_method = 'cash_on_delivery'"},

    {"id": 214, "difficulty": "medium",
     "question": "What is the total revenue from paid card payments made in 2024?",
     "gold_sql": "SELECT SUM(amount) FROM payments WHERE payment_status = 'paid' AND payment_method = 'card' AND payment_date >= '2024-01-01' AND payment_date < '2025-01-01'"},

    # ---------------- HARD ----------------
    {"id": 215, "difficulty": "hard",
     "question": "How many customers placed more than 10 orders?",
     "gold_sql": "SELECT COUNT(*) FROM (SELECT customer_id FROM orders GROUP BY customer_id HAVING COUNT(*) > 10) t"},

    {"id": 216, "difficulty": "hard",
     "question": "Which state has the highest revenue?",
     "gold_sql": "SELECT c.state FROM payments p JOIN orders o ON o.order_id = p.order_id JOIN customers c ON c.customer_id = o.customer_id WHERE p.payment_status = 'paid' GROUP BY c.state ORDER BY SUM(p.amount) DESC LIMIT 1"},

    {"id": 217, "difficulty": "hard",
     "question": "How many customers have had both a cancelled order and a delivered order?",
     "gold_sql": "SELECT COUNT(*) FROM (SELECT customer_id FROM orders WHERE status IN ('cancelled', 'delivered') GROUP BY customer_id HAVING COUNT(DISTINCT status) = 2) t"},

    {"id": 218, "difficulty": "hard",
     "question": "Which payment method has the highest total paid amount?",
     "gold_sql": "SELECT payment_method FROM payments WHERE payment_status = 'paid' GROUP BY payment_method ORDER BY SUM(amount) DESC LIMIT 1"},

    {"id": 219, "difficulty": "hard",
     "question": "How many customers have not placed any order in 2025?",
     "gold_sql": "SELECT COUNT(*) FROM customers c WHERE NOT EXISTS (SELECT 1 FROM orders o WHERE o.customer_id = c.customer_id AND o.order_date >= '2025-01-01' AND o.order_date < '2026-01-01')"},

    {"id": 220, "difficulty": "hard",
     "question": "What is the total revenue from Electronics products?",
     "gold_sql": "SELECT SUM(oi.quantity * oi.unit_price) FROM order_items oi JOIN orders o ON o.order_id = oi.order_id JOIN products pr ON pr.product_id = oi.product_id JOIN categories cat ON cat.category_id = pr.category_id WHERE cat.category_name = 'Electronics' AND o.status IN ('delivered', 'shipped')"},
]