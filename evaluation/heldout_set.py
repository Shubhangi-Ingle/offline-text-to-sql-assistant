# Held-out test set: questions the prompt has NOT been tuned on.
# Ids 101-106 are easy, 107-114 medium, 115-120 hard.

HELDOUT_CASES = [
    # ---------------- EASY ----------------
    {"id": 101, "difficulty": "easy",
     "question": "How many orders are pending?",
     "gold_sql": "SELECT COUNT(*) FROM orders WHERE status = 'pending'"},

    {"id": 102, "difficulty": "easy",
     "question": "How many customers are from Delhi?",
     "gold_sql": "SELECT COUNT(*) FROM customers WHERE city = 'Delhi'"},

    {"id": 103, "difficulty": "easy",
     "question": "What is the price of the cheapest product?",
     "gold_sql": "SELECT MIN(price) FROM products"},

    {"id": 104, "difficulty": "easy",
     "question": "How many payments failed?",
     "gold_sql": "SELECT COUNT(*) FROM payments WHERE payment_status = 'failed'"},

    {"id": 105, "difficulty": "easy",
     "question": "How many products are in the Books category?",
     "gold_sql": "SELECT COUNT(*) FROM products p JOIN categories c ON c.category_id = p.category_id WHERE c.category_name = 'Books'"},

    {"id": 106, "difficulty": "easy",
     "question": "How many orders were shipped?",
     "gold_sql": "SELECT COUNT(*) FROM orders WHERE status = 'shipped'"},

    # ---------------- MEDIUM ----------------
    {"id": 107, "difficulty": "medium",
     "question": "What is the total refunded amount?",
     "gold_sql": "SELECT SUM(amount) FROM payments WHERE payment_status = 'refunded'"},

    {"id": 108, "difficulty": "medium",
     "question": "How many orders were placed by customers from Pune?",
     "gold_sql": "SELECT COUNT(*) FROM orders o JOIN customers c ON c.customer_id = o.customer_id WHERE c.city = 'Pune'"},

    {"id": 109, "difficulty": "medium",
     "question": "What is the average price of products in the Fashion category?",
     "gold_sql": "SELECT AVG(p.price) FROM products p JOIN categories c ON c.category_id = p.category_id WHERE c.category_name = 'Fashion'"},

    {"id": 110, "difficulty": "medium",
     "question": "Which city generates the highest revenue?",
     "gold_sql": "SELECT c.city FROM payments p JOIN orders o ON o.order_id = p.order_id JOIN customers c ON c.customer_id = o.customer_id WHERE p.payment_status = 'paid' GROUP BY c.city ORDER BY SUM(p.amount) DESC LIMIT 1"},

    {"id": 111, "difficulty": "medium",
     "question": "What is the total stock quantity across all products?",
     "gold_sql": "SELECT SUM(stock_quantity) FROM products"},

    {"id": 112, "difficulty": "medium",
     "question": "How many orders were placed in the first quarter of 2025?",
     "gold_sql": "SELECT COUNT(*) FROM orders WHERE order_date >= '2025-01-01' AND order_date < '2025-04-01'"},

    {"id": 113, "difficulty": "medium",
     "question": "How many distinct customers have at least one payment using UPI?",
     "gold_sql": "SELECT COUNT(DISTINCT o.customer_id) FROM payments p JOIN orders o ON o.order_id = p.order_id WHERE p.payment_method = 'upi'"},

    {"id": 114, "difficulty": "medium",
     "question": "What is the revenue of each payment method?",
     "gold_sql": "SELECT payment_method, SUM(amount) FROM payments WHERE payment_status = 'paid' GROUP BY payment_method"},

    # ---------------- HARD ----------------
    {"id": 115, "difficulty": "hard",
     "question": "How many orders contain more than 2 different products?",
     "gold_sql": "SELECT COUNT(*) FROM (SELECT order_id FROM order_items GROUP BY order_id HAVING COUNT(DISTINCT product_id) > 2) t"},

    {"id": 116, "difficulty": "hard",
     "question": "How many customers from Maharashtra have spent more than 20000 in total?",
     "gold_sql": "SELECT COUNT(*) FROM (SELECT o.customer_id FROM payments p JOIN orders o ON o.order_id = p.order_id JOIN customers c ON c.customer_id = o.customer_id WHERE c.state = 'Maharashtra' AND p.payment_status = 'paid' GROUP BY o.customer_id HAVING SUM(p.amount) > 20000) t"},

    {"id": 117, "difficulty": "hard",
     "question": "How many customers have ordered products from at least 3 different categories?",
     "gold_sql": "SELECT COUNT(*) FROM (SELECT o.customer_id FROM orders o JOIN order_items oi ON oi.order_id = o.order_id JOIN products p ON p.product_id = oi.product_id GROUP BY o.customer_id HAVING COUNT(DISTINCT p.category_id) >= 3) t"},

    {"id": 118, "difficulty": "hard",
     "question": "What is the total revenue from customers in Karnataka?",
     "gold_sql": "SELECT SUM(p.amount) FROM payments p JOIN orders o ON o.order_id = p.order_id JOIN customers c ON c.customer_id = o.customer_id WHERE c.state = 'Karnataka' AND p.payment_status = 'paid'"},

    {"id": 119, "difficulty": "hard",
     "question": "How many customers placed orders in both 2024 and 2025?",
     "gold_sql": "SELECT COUNT(*) FROM (SELECT customer_id FROM orders WHERE order_date >= '2024-01-01' AND order_date < '2026-01-01' GROUP BY customer_id HAVING COUNT(DISTINCT EXTRACT(YEAR FROM order_date)) = 2) t"},

    {"id": 120, "difficulty": "hard",
     "question": "What is the total value of items in cancelled orders (quantity times unit price)?",
     "gold_sql": "SELECT SUM(oi.quantity * oi.unit_price) FROM order_items oi JOIN orders o ON o.order_id = oi.order_id WHERE o.status = 'cancelled'"},
]