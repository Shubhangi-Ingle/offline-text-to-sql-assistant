DROP TABLE IF EXISTS payments, order_items, orders, products, categories, customers CASCADE;

CREATE TABLE customers (
    customer_id  SERIAL PRIMARY KEY,
    full_name    VARCHAR(100) NOT NULL,
    email        VARCHAR(150) UNIQUE NOT NULL,
    city         VARCHAR(80),
    state        VARCHAR(80),
    signup_date  DATE NOT NULL
);

CREATE TABLE categories (
    category_id    SERIAL PRIMARY KEY,
    category_name  VARCHAR(80) UNIQUE NOT NULL
);

CREATE TABLE products (
    product_id      SERIAL PRIMARY KEY,
    product_name    VARCHAR(150) NOT NULL,
    category_id     INT NOT NULL REFERENCES categories(category_id),
    price           NUMERIC(10,2) NOT NULL CHECK (price >= 0),
    stock_quantity  INT NOT NULL DEFAULT 0
);

CREATE TABLE orders (
    order_id     SERIAL PRIMARY KEY,
    customer_id  INT NOT NULL REFERENCES customers(customer_id),
    order_date   DATE NOT NULL,
    status       VARCHAR(20) NOT NULL
                 CHECK (status IN ('pending','shipped','delivered','cancelled','returned'))
);

CREATE TABLE order_items (
    order_item_id  SERIAL PRIMARY KEY,
    order_id       INT NOT NULL REFERENCES orders(order_id),
    product_id     INT NOT NULL REFERENCES products(product_id),
    quantity       INT NOT NULL CHECK (quantity > 0),
    unit_price     NUMERIC(10,2) NOT NULL
);

CREATE TABLE payments (
    payment_id      SERIAL PRIMARY KEY,
    order_id        INT NOT NULL REFERENCES orders(order_id),
    amount          NUMERIC(10,2) NOT NULL,
    payment_method  VARCHAR(20) NOT NULL
                    CHECK (payment_method IN ('card','upi','netbanking','cash_on_delivery')),
    payment_status  VARCHAR(20) NOT NULL
                    CHECK (payment_status IN ('paid','failed','refunded')),
    payment_date    DATE NOT NULL
);