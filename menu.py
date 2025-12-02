import sqlite3
from flask import Flask, render_template
import os

app = Flask(__name__)

DB_PATH = os.path.join(os.path.dirname(__file__), "menu.db")

def get_categories():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, category, price, image, size FROM menu_items")
    items = cursor.fetchall()
    conn.close()

    categories = {}
    for item in items:
        category = item[2]
        if category not in categories:
            categories[category] = []
        categories[category].append(item)
    print("Fetched categories:", categories)  # Debug
    return categories

@app.route('/menu')
def menu_page():
    categories = get_categories()   # call the fetch function
    return render_template('Menu_Page.html', categories=categories)

if __name__ == "__main__":
    app.run(debug=True,port=8000)