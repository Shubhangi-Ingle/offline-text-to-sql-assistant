# Each test case has an answer key (gold SQL). The evaluator runs both queries and compares results.
# Questions 1-10 are easy, 11-23 medium, 24-30 hard.

TEST_CASES = [
    # ---------------- EASY ----------------
    {"id": 1, "difficulty": "easy",
     "question": "How many customers are there?",
     "gold_sql": "SELECT COUNT(*) FROM customers"},

    {"id": 2, "difficulty": "easy",
     "question": "How many products are there in total?",
     "gold_sql": "SELECT COUNT(*) FROM products"},

    {"id": 3, "difficulty": "easy",
     "question": "How many orders were cancelled?",
     "gold_sql": "SELECT COUNT(*) FROM orders WHERE status = 'cancelled'"},

    {"id": 4, "difficulty": "easy",
     "question": "How many customers are from Maharashtra?",
     "gold_sql": "SELECT COUNT(*) FROM customers WHERE state = 'Maharashtra'"},

    {"id": 5, "difficulty": "easy",
     "question": "What is the price of the most expensive product?",
     "gold_sql": "SELECT MAX(price) FROM products"},

    {"id": 6, "difficulty": "easy",
     "question": "How many orders were placed in 2024?",
     "gold_sql": "SELECT COUNT(*) FROM orders WHERE order_date >= '2024-01-01' AND order_date < '2025-01-01'"},

    {"id": 7, "difficulty": "easy",
     "question": "How many payments use the UPI payment method?",
     "gold_sql": "SELECT COUNT(*) FROM payments WHERE payment_method = 'upi'"},

    {"id": 8, "difficulty": "easy",
     "question": "List all category names.",
     "gold_sql": "SELECT category_name FROM categories"},

    {"id": 9, "difficulty": "easy",
     "question": "How many products are in the Electronics category?",
     "gold_sql": "SELECT COUNT(*) FROM products p JOIN categories c ON c.category_id = p.category_id WHERE c.category_name = 'Electronics'"},

    {"id": 10, "difficulty": "easy",
     "question": "What is the average price of all products?",
     "gold_sql": "SELECT AVG(price) FROM products"},

    # ---------------- MEDIUM ----------------
    {"id": 11, "difficulty": "medium",
     "question": "What is the total revenue?",
     "gold_sql": "SELECT SUM(amount) FROM payments WHERE payment_status = 'paid'"},

    {"id": 12, "difficulty": "medium",
     "question": "What is the total revenue from net banking payments?",
     "gold_sql": "SELECT SUM(amount) FROM payments WHERE payment_status = 'paid' AND payment_method = 'netbanking'"},

    {"id": 13, "difficulty": "medium",
     "question": "How many units were sold in the Sports category?",
     "gold_sql": "SELECT SUM(oi.quantity) FROM order_items oi JOIN orders o ON o.order_id = oi.order_id JOIN products p ON p.product_id = oi.product_id JOIN categories c ON c.category_id = p.category_id WHERE c.category_name = 'Sports' AND o.status IN ('delivered', 'shipped')"},

    {"id": 14, "difficulty": "medium",
     "question": "Which 5 products have the highest price?",
     "gold_sql": "SELECT product_name, price FROM products ORDER BY price DESC LIMIT 5"},

    {"id": 15, "difficulty": "medium",
     "question": "How many customers have placed at least one order?",
     "gold_sql": "SELECT COUNT(DISTINCT customer_id) FROM orders"},

    {"id": 16, "difficulty": "medium",
     "question": "How many customers have never placed an order?",
     "gold_sql": "SELECT COUNT(*) FROM customers c WHERE NOT EXISTS (SELECT 1 FROM orders o WHERE o.customer_id = c.customer_id)"},

    {"id": 17, "difficulty": "medium",
     "question": "What is the average order value?",
     "gold_sql": "SELECT AVG(amount) FROM payments WHERE payment_status = 'paid'"},

    {"id": 18, "difficulty": "medium",
     "question": "How many orders were returned in 2025?",
     "gold_sql": "SELECT COUNT(*) FROM orders WHERE status = 'returned' AND order_date >= '2025-01-01' AND order_date < '2026-01-01'"},

    {"id": 19, "difficulty": "medium",
     "question": "What is the total revenue from payments made in 2025?",
     "gold_sql": "SELECT SUM(amount) FROM payments WHERE payment_status = 'paid' AND payment_date >= '2025-01-01' AND payment_date < '2026-01-01'"},

    {"id": 20, "difficulty": "medium",
     "question": "How many products have fewer than 50 items in stock?",
     "gold_sql": "SELECT COUNT(*) FROM products WHERE stock_quantity < 50"},

    {"id": 21, "difficulty": "medium",
     "question": "What is the total quantity of items in delivered orders?",
     "gold_sql": "SELECT SUM(oi.quantity) FROM order_items oi JOIN orders o ON o.order_id = oi.order_id WHERE o.status = 'delivered'"},

    {"id": 22, "difficulty": "medium",
     "question": "Which payment method has the most paid payments?",
     "gold_sql": "SELECT payment_method FROM payments WHERE payment_status = 'paid' GROUP BY payment_method ORDER BY COUNT(*) DESC LIMIT 1"},

    {"id": 23, "difficulty": "medium",
     "question": "Which state has the most customers?",
     "gold_sql": "SELECT state FROM customers GROUP BY state ORDER BY COUNT(*) DESC LIMIT 1"},

    # ---------------- HARD ----------------
    {"id": 24, "difficulty": "hard",
     "question": "Which category has the highest revenue?",
     "gold_sql": "SELECT cat.category_name FROM order_items oi JOIN orders o ON o.order_id = oi.order_id JOIN products pr ON pr.product_id = oi.product_id JOIN categories cat ON cat.category_id = pr.category_id WHERE o.status IN ('delivered', 'shipped') GROUP BY cat.category_name ORDER BY SUM(oi.quantity * oi.unit_price) DESC LIMIT 1"},

    {"id": 25, "difficulty": "hard",
     "question": "Show the 5 customers who spent the most money.",
     "gold_sql": "SELECT c.full_name, SUM(p.amount) FROM customers c JOIN orders o ON o.customer_id = c.customer_id JOIN payments p ON p.order_id = o.order_id WHERE p.payment_status = 'paid' GROUP BY c.customer_id, c.full_name ORDER BY SUM(p.amount) DESC LIMIT 5"},

    {"id": 26, "difficulty": "hard",
     "question": "How many customers from Maharashtra placed more than 5 orders?",
     "gold_sql": "SELECT COUNT(*) FROM (SELECT c.customer_id FROM customers c JOIN orders o ON o.customer_id = c.customer_id WHERE c.state = 'Maharashtra' GROUP BY c.customer_id HAVING COUNT(*) > 5) t"},

    {"id": 27, "difficulty": "hard",
     "question": "What is the revenue of each category?",
     "gold_sql": "SELECT cat.category_name, SUM(oi.quantity * oi.unit_price) FROM order_items oi JOIN orders o ON o.order_id = oi.order_id JOIN products pr ON pr.product_id = oi.product_id JOIN categories cat ON cat.category_id = pr.category_id WHERE o.status IN ('delivered', 'shipped') GROUP BY cat.category_name"},

    {"id": 28, "difficulty": "hard",
     "question": "Which product has the highest total units sold?",
     "gold_sql": "SELECT pr.product_name FROM order_items oi JOIN orders o ON o.order_id = oi.order_id JOIN products pr ON pr.product_id = oi.product_id WHERE o.status IN ('delivered', 'shipped') GROUP BY pr.product_id, pr.product_name ORDER BY SUM(oi.quantity) DESC LIMIT 1"},

    {"id": 29, "difficulty": "hard",
     "question": "How many customers have ordered products from more than one category?",
     "gold_sql": "SELECT COUNT(*) FROM (SELECT o.customer_id FROM orders o JOIN order_items oi ON oi.order_id = o.order_id JOIN products p ON p.product_id = oi.product_id GROUP BY o.customer_id HAVING COUNT(DISTINCT p.category_id) > 1) t"},

    {"id": 30, "difficulty": "hard",
     "question": "How many customers have spent more than 50000 in total?",
     "gold_sql": "SELECT COUNT(*) FROM (SELECT o.customer_id FROM payments p JOIN orders o ON o.order_id = p.order_id WHERE p.payment_status = 'paid' GROUP BY o.customer_id HAVING SUM(p.amount) > 50000) t"},
]