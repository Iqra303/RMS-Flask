# from flask import Flask, render_template, request, redirect, url_for, flash,session
# import requests, json, os
# import sqlite3
# from werkzeug.security import generate_password_hash, check_password_hash

# app = Flask(__name__)
# app.secret_key = "supersecretkey" 


# def init_db():
#     conn = sqlite3.connect("users.db")
#     cursor = conn.cursor()
#     cursor.execute("""
#         CREATE TABLE IF NOT EXISTS users (
#             id INTEGER PRIMARY KEY AUTOINCREMENT,
#             email TEXT UNIQUE NOT NULL,
#             password TEXT NOT NULL
#         )
#     """)
#     conn.commit()
#     conn.close()

# init_db()

# @app.route("/")
# def home():
#     if "user_id" in session:
#         # User is logged in
#         email = session["email"]
#         return render_template("home.html", logged_in=True, email=email)
#     else:
#         # User is NOT logged in
#         return render_template("login.html", logged_in=False)

# @app.route("/menu")
# def Menu():
#     return render_template("Menu_Page.html")

# @app.route("/contact")
# def contact():
#     return render_template("contact.html")

# @app.route("/thanks")
# def thanks():
#     return render_template("Thank_You_Meal.html")

# @app.route("/signup", methods=["GET", "POST"])
# def signup():
#     if request.method == "POST":
#         email = request.form["email"]
#         password = request.form["password"]
#         confirm_password = request.form["cpassword"]

#         # Check if passwords match
#         if password != confirm_password:
#             flash("Passwords do not match!", "error")
#             return render_template("signup.html")

#         hashed_password = generate_password_hash(password)

#         try:
#             conn = sqlite3.connect("users.db")
#             cursor = conn.cursor()
#             cursor.execute(
#                 "INSERT INTO users (email, password) VALUES (?, ?)", 
#                 (email, hashed_password)
#             )
#             conn.commit()
#             conn.close()
#             flash("Sign Up Successful! You can now login.", "success")
#             return redirect(url_for("home"))
#         except sqlite3.IntegrityError:
#             flash("Email already registered!", "error")
    
#     return render_template("signup.html")


# @app.route("/login", methods=["GET", "POST"])
# def login():
#     if request.method == "POST":
#         email = request.form["email"]
#         password = request.form["password"]

#         conn = sqlite3.connect("users.db")
#         cursor = conn.cursor()
#         cursor.execute("SELECT * FROM users WHERE email=?", (email,))
#         user = cursor.fetchone()
#         conn.close()

#         if user:
#             stored_password = user[2]
#             if check_password_hash(stored_password, password):
#                 flash("Login Successful!", "success")
#                 return redirect(url_for("home"))
#             else:
#                 flash("Incorrect Password!", "error")
#         else:
#             flash("Email not registered!", "error")

#     return render_template("login.html")
    
# if __name__ == "__main__":
#     app.run(debug=True)
from flask import Flask, render_template, request, redirect, url_for, flash, session
import sqlite3
import os
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
app = Flask(__name__)
app.secret_key = "supersecretkey" 

# Initialize DB
def init_db():
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

init_db()

# Folder to save uploaded images
UPLOAD_FOLDER = 'static/images'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Create database if not exists
conn = sqlite3.connect("menu.db")
cursor = conn.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS menu_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    price REAL NOT NULL,
    image TEXT NOT NULL
);
""")
conn.commit()
conn.close()

conn = sqlite3.connect("order_user.db")
cursor = conn.cursor()

# Enable foreign keys
cursor.execute("PRAGMA foreign_keys = ON")

# Create orders table
cursor.execute("""
CREATE TABLE IF NOT EXISTS orders(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_name TEXT NOT NULL,
    phone TEXT NOT NULL,
    address TEXT NOT NULL,
    total REAL NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
""")

# Create order_items table
cursor.execute("""
CREATE TABLE IF NOT EXISTS order_items(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER NOT NULL,
    item_name TEXT NOT NULL,
    category TEXT NOT NULL,
    price REAL NOT NULL,
    quantity INTEGER NOT NULL,
    FOREIGN KEY(order_id) REFERENCES orders(id) ON DELETE CASCADE
);
""")

conn.commit()
conn.close()
print("Tables created successfully in order_user.db")



# ---------------- MENU ADMIN PANEL ---------------- #

# Show all menu items
@app.route("/admin/menu")
def admin_menu():
    conn = sqlite3.connect("menu.db")
    cur = conn.cursor()
    cur.execute("SELECT * FROM menu_items ORDER BY category, id")
    items = cur.fetchall()
    conn.close()

    # Group items by category
    categories = {}
    for item in items:
        cat = item[2]  # 0:id, 1:name, 2:category, 3:price, 4:image, 5:size (optional)
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(item)

    return render_template("Admin_Panel.html", categories=categories)



# Add new menu item
@app.route("/admin/menu/add", methods=["POST"])
def add_menu_item():
    name = request.form["name"]
    category = request.form["category"]
    price = request.form["price"]

    # Handle image upload
    file = request.files.get("image")
    if file and file.filename != "":
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    else:
        filename = "default.png"  # fallback image if none uploaded

    conn = sqlite3.connect("menu.db")
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO menu_items (name, category, price, image) VALUES (?, ?, ?, ?)",
        (name, category, price, filename)
    )
    conn.commit()
    conn.close()
    flash("Menu item added!", "success")
    return redirect(url_for("admin_menu"))


# Update menu item
@app.route("/admin/menu/update/<int:item_id>", methods=["POST"])
def update_menu_item(item_id):
    name = request.form["name"]
    category = request.form["category"]
    price = request.form["price"]

    conn = sqlite3.connect("menu.db")
    cursor = conn.cursor()

    # Check if a new image is uploaded
    file = request.files.get("image")
    if file and file.filename != "":
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        cursor.execute(
            "UPDATE menu_items SET name=?, category=?, price=?, image=? WHERE id=?",
            (name, category, price, filename, item_id)
        )
    else:
        cursor.execute(
            "UPDATE menu_items SET name=?, category=?, price=? WHERE id=?",
            (name, category, price, item_id)
        )

    conn.commit()
    conn.close()
    flash("Menu item updated!", "success")
    return redirect(url_for("admin_menu"))


# Delete menu item
@app.route("/admin/menu/delete/<int:item_id>")
def delete_menu_item(item_id):
    conn = sqlite3.connect("menu.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM menu_items WHERE id=?", (item_id,))
    conn.commit()
    conn.close()
    flash("Deleted successfully!", "success")
    return redirect(url_for("admin_menu"))

@app.route("/menu")
def menu_page():
    conn = sqlite3.connect("menu.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM menu_items")
    items = cursor.fetchall()
    conn.close()
    return render_template("Menu_Page.html", items=items)

@app.route("/add_to_order", methods=["POST"])
def add_to_order():
    item = {
        "id": request.form["id"],
        "name": request.form["name"],
        "category": request.form["category"],
        "price": float(request.form["price"]),
        "image": request.form["image"],
        "quantity": 1
    }

    if "order" not in session:
        session["order"] = []

    order = session["order"]
    # Increment quantity if item exists
    for existing_item in order:
        if existing_item["id"] == item["id"]:
            existing_item["quantity"] += 1
            session["order"] = order
            flash(f"{item['name']} quantity updated in cart!", "success")
            return redirect(url_for("menu_page"))

    order.append(item)
    session["order"] = order
    flash(f"{item['name']} added to cart!", "success")
    return redirect(url_for("menu_page"))


@app.route("/order")
def order_page():
    order = session.get("order", [])
    return render_template("Ordering.html", order=order)

@app.route("/remove_from_order/<int:index>")
def remove_from_order(index):
    order = session.get("order", [])
    if 0 <= index < len(order):
        removed_item = order.pop(index)
        session["order"] = order
        flash(f"{removed_item['name']} removed from order.", "success")
    return redirect(url_for("order_page"))

@app.route("/update_quantity", methods=["POST"])
def update_quantity():
    index = int(request.form["index"])
    delta = int(request.form["delta"])
    order = session.get("order", [])
    
    if 0 <= index < len(order):
        order[index]["quantity"] = max(1, order[index]["quantity"] + delta)
    
    session["order"] = order
    return redirect(url_for("order_page"))


@app.route("/confirm-order")
def confirm_order():
    order = session.get("order", [])
    
    total = sum(item["price"] * item["quantity"] for item in order)
    return render_template("Billing_Method.html", order=order, total=total)

@app.route("/menu")
def Menu():
    return render_template("Menu_Page.html")

@app.route("/contact")
def contact():
    return render_template("contact.html")

@app.route("/thanks")
def thanks():
    return render_template("Thank_You_Meal.html")

@app.route("/")
def home():
    if "user_id" in session:
        email = session["email"]
        return render_template("homepage.html", logged_in=True, email=email)
    else:
        flash("Please login first!", "error")
        return redirect(url_for("login"))


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        confirm_password = request.form["cpassword"]

        if password != confirm_password:
            flash("Passwords do not match!", "error")
            return render_template("signup.html")

        hashed_password = generate_password_hash(password)

        try:
            conn = sqlite3.connect("users.db")
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO users (email, password) VALUES (?, ?)", 
                (email, hashed_password)
            )
            conn.commit()
            user_id = cursor.lastrowid  # Get the new user's ID
            conn.close()

            # Store user in session automatically after signup
            session["user_id"] = user_id
            session["email"] = email

            flash("Sign Up Successful! You are now logged in.", "success")
            return redirect(url_for("home"))
        except sqlite3.IntegrityError:
            flash("Email already registered!", "error")
    
    return render_template("signup.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        conn = sqlite3.connect("users.db")
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email=?", (email,))
        user = cursor.fetchone()
        conn.close()

        if user:
            stored_password = user[2]
            if check_password_hash(stored_password, password):
                # Store user in session
                session["user_id"] = user[0]
                session["email"] = user[1]
                flash("Login Successful!", "success")
                return redirect(url_for("home"))
            else:
                flash("Incorrect Password!", "error")
        else:
            flash("Email not registered!", "error")

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully!", "success")
    return redirect(url_for("login"))

# @app.route("/bill")
# def billing():
#     return render_template("Billing_Method.html")

@app.route("/finalize_order", methods=["POST"])
def finalize_order():
    customer_name = request.form["customer_name"]
    phone = request.form["phone"]
    address = request.form["address"]
    order = session.get("order", [])

    total = sum(item["price"] * item["quantity"] for item in order)

    # Use single database
    conn = sqlite3.connect("order_user.db")
    cur = conn.cursor()

    # Enable foreign key constraints
    cur.execute("PRAGMA foreign_keys = ON")

    # Insert into orders table
    cur.execute("""
        INSERT INTO orders (customer_name, phone, address, total)
        VALUES (?, ?, ?, ?)
    """, (customer_name, phone, address, total))

    order_id = cur.lastrowid

    # Insert items into order_items table (same DB)
    for item in order:
        cur.execute("""
            INSERT INTO order_items (order_id, item_name, category, price, quantity)
            VALUES (?, ?, ?, ?, ?)
        """, (order_id, item["name"], item["category"], item["price"], item["quantity"]))

    conn.commit()
    conn.close()

    # Clear cart
    session["order"] = []

    return render_template("Thank_You_Meal.html", order_id=order_id)

# @app.route("/finalize_order", methods=["POST"])
# def finalize_order():
#     customer_name = request.form["customer_name"]
#     phone = request.form["phone"]
#     address = request.form["address"]
#     order = session.get("order", [])

#     total = sum(item["price"] * item["quantity"] for item in order)

#     # Use correct database file
#     conn = sqlite3.connect("order_user.db")
#     cur = conn.cursor()

#     # Insert into orders table
#     cur.execute("""
#         INSERT INTO orders (customer_name, phone, address, total)
#         VALUES (?, ?, ?, ?)
#     """, (customer_name, phone, address, total))

#     order_id = cur.lastrowid

#     # Insert items into order_items.db (or you can combine into one db)
#     conn_items = sqlite3.connect("items.db")
#     cur_items = conn_items.cursor()
#     for item in order:
#         cur_items.execute("""
#             INSERT INTO order_items (order_id, item_name, category, price, quantity)
#             VALUES (?, ?, ?, ?, ?)
#         """, (order_id, item["name"], item["category"], item["price"], item["quantity"]))
#     conn_items.commit()
#     conn_items.close()

#     conn.commit()
#     conn.close()

#     # Clear cart
#     session["order"] = []

#     return render_template("Thank_You_Meal.html", order_id=order_id)

# @app.route("/admin/orders")
# def admin_orders():
#     # Connect to orders database (orders and items can be separate)
#     conn_orders = sqlite3.connect("order_user.db")
#     cur_orders = conn_orders.cursor()

#     # Fetch all orders
#     cur_orders.execute("SELECT * FROM orders ORDER BY id DESC")
#     orders = cur_orders.fetchall()

#     # Connect to order_items database
#     conn_items = sqlite3.connect("items.db")
#     cur_items = conn_items.cursor()

#     orders_with_items = []
#     for order in orders:
#         order_id = order[0]
#         # Fetch items for this order
#         cur_items.execute("""
#             SELECT item_name, category, price, quantity
#             FROM order_items
#             WHERE order_id=?
#         """, (order_id,))
#         items = cur_items.fetchall()  # ✅ parentheses

#         orders_with_items.append({
#             "order_id": order_id,
#             "customer_name": order[1],
#             "phone": order[2],
#             "address": order[3],
#             "total": order[4],
#             "items": items
#         })

#     # Close connections
#     conn_orders.close()
#     conn_items.close()

#     return render_template("Admin_Orders.html", orders=orders_with_items)

@app.route("/admin/orders")
def admin_orders():
    import sqlite3

    conn = sqlite3.connect("order_user.db")
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # Fetch all orders
    cur.execute("SELECT * FROM orders ORDER BY id DESC")
    orders = cur.fetchall()

    orders_with_items = []
    for order in orders:
        order_id = order['id']
        # Fetch items for this order
        cur.execute("""
            SELECT item_name, category, price, quantity
            FROM order_items
            WHERE order_id=?
        """, (order_id,))
        items = cur.fetchall()  # ✅ same DB
        # Convert to list of tuples for template
        items_list = [(item['item_name'], item['category'], item['price'], item['quantity']) for item in items]

        orders_with_items.append({
            "order_id": order_id,
            "customer_name": order['customer_name'],
            "phone": order['phone'],
            "address": order['address'],
            "total": order['total'],
            "items": items_list
        })

    conn.close()
    return render_template("Admin_Orders.html", orders=orders_with_items)




@app.route("/admin-login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        # FIXED ADMIN CREDENTIALS
        if email == "admin@gmail.com" and password == "admin123":
            session["admin"] = True
            return redirect(url_for("admin_menu"))   # ← FIXED (added return)
        else:
            flash("Invalid email or password!", "error")
            return redirect("/admin-login")

    return render_template("admin_login.html")


@app.route("/admin/order/delete/<int:order_id>", methods=["POST"])
def delete_order(order_id):
    conn = sqlite3.connect("order_user.db")
    cur = conn.cursor()
    cur.execute("PRAGMA foreign_keys = ON")  # Enable foreign keys
    
    # Delete items first (if in a separate table)
    conn_items = sqlite3.connect("items.db")
    cur_items = conn_items.cursor()
    cur_items.execute("DELETE FROM order_items WHERE order_id=?", (order_id,))
    conn_items.commit()
    conn_items.close()
    
    # Then delete the order itself
    cur.execute("DELETE FROM orders WHERE id=?", (order_id,))
    conn.commit()
    conn.close()
    
    flash("Order deleted successfully!", "success")
    return redirect(url_for("admin_orders"))


if __name__ == "__main__":
    # Railway ya cloud deploy ke liye PORT environment variable use hota hai
    port = int(os.environ.get("PORT", 5000))
    # 0.0.0.0 host -> cloud / container ke liye zaruri
    app.run(host="0.0.0.0", port=port, debug=True)
# if __name__ == "__main__":
#     app.run(debug=True)
