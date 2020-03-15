from flask import Flask, render_template
from bs4 import BeautifulSoup
import requests
import sqlite3
from collections import deque

app = Flask(__name__)

TIKI_URL = 'https://tiki.vn'
conn = sqlite3.connect('tiki.db')
cur = conn.cursor()

def create_categories_table():
    query = """
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name VARCHAR(255),
            url TEXT, 
            parent_id INT, 
            create_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """
    try:
        cur.execute(query)
    except Exception as err:
        print('ERROR BY CREATE TABLE', err)
create_categories_table()


def select_all():
    return cur.execute('SELECT * FROM categories;').fetchall()

def delete_all():
    return cur.execute('DELETE FROM categories;')


class Category:
    def __init__(self, cat_id, name, url, parent_id):
        self.cat_id = cat_id
        self.name = name
        self.url = url
        self.parent_id = parent_id

    def __repr__(self):
        return "ID: {}, Name: {}, URL: {}, Parent_id: {}".format(self.cat_id, self.name, self.url, self.parent_id)

    def save_into_db(self):
        query = """
            INSERT INTO categories (name, url, parent_id)
            VALUES (?, ?, ?);
        """
        val = (self.name, self.url, self.parent_id)
        try:
            cur.execute(query, val)
            self.cat_id = cur.lastrowid
        except Exception as err:
            print('ERROR BY INSERT:', err)

def get_url(url):  
    try:
        response = requests.get(url).text
        response = BeautifulSoup(response, 'html.parser')
        return response
    except Exception as err:
            print('ERROR BY REQUEST:', err)


def get_main_categories(save_db=False):
    soup = get_url(TIKI_URL)

    result = []
    for a in soup.findAll('a', {'class':'MenuItem__MenuLink-tii3xq-1 efuIbv'}):
        cat_id = None
        name = a.find('span', {'class':'text'}).text
        url = a['href']
        parent_id = None

        cat = Category(cat_id, name, url, parent_id)
        if save_db:
            cat.save_into_db()
        result.append(cat)
    return result


main_categories = get_main_categories(save_db=True)


def get_sub_categories(category, save_db=False):
    name = category.name
    url = category.url
    result = []

    try:
        soup = get_url(url)
        div_containers = soup.findAll('div', {'class':'list-group-item is-child'})
        for div in div_containers:
            sub_id = None
            sub_name = div.a.text
            sub_url = 'http://tiki.vn' + div.a['href']
            sub_parent_id = category.cat_id

            sub = Category(sub_id, sub_name, sub_url, sub_parent_id)
            if save_db:
                sub.save_into_db()
            result.append(sub)
    except Exception as err:
        print('ERROR BY GET SUB CATEGORIES:', err)

    return result


def get_all_categories(main_categories):
    de = deque(main_categories)
    count = 0

    while de:
        parent_cat = de.popleft()
        sub_cats = get_sub_categories(parent_cat, save_db=True)
        print(sub_cats)
        de.extend(sub_cats)
        count += 1
get_all_categories(main_categories[0:2])

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
  app.run(host='127.0.0.1', port=8000, debug=True)
