import os
import requests
import json
import shutil
import urllib.parse
import flask
from flask import Flask, render_template, request, redirect, jsonify, flash, url_for, session
import psycopg2
from dotenv import load_dotenv
import hashlib
import uuid
from functools import wraps
from datetime import datetime
from difflib import SequenceMatcher

###############################################################
########################## SET UP #############################
###############################################################

app = Flask(__name__)
app.secret_key = 'logan'
load_dotenv()

DB_USERNAME = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PW') 
DB_PORT = os.getenv('DB_PORT')
DB_NAME = os.getenv('DB_NAME')
DB_ENDPOINT = os.getenv('DB_ENDPOINT')

try:
    db_conn = psycopg2.connect(
        database=DB_NAME,
        user=DB_USERNAME,
        password=DB_PASSWORD,
        host=DB_ENDPOINT,
        port=DB_PORT
    )
    print("Successful DB connection.")
except:
    print("DB connection failed")
    exit(1)

###############################################################
########################## HELPERS ############################
###############################################################

def insert_user(og_handle, ip):
    cur = db_conn.cursor()
    handle = og_handle.replace("'", "''")
    cur.execute(f'''
        INSERT INTO people (handle, ip) VALUES ('{handle}', '{ip}');
    ''')
    db_conn.commit()
    print(f'{og_handle} registered.')


def find_user(id, username=None):
    cur = db_conn.cursor()
    query = "SELECT * FROM people WHERE "

    if username:
        username = username.replace("'", "''")
        query += f"handle = '{username}';"
    else:
        query += f"id = {id};"

    cur.execute(query)
    return cur.fetchone()


def find_ip(ip):
    cur = db_conn.cursor()
    query = f"SELECT * FROM people WHERE ip = '{ip}';"
    cur.execute(query)
    return cur.fetchone()   


def get_pack(user_id, pack):
    cur = db_conn.cursor()
    query = f'''
        select json_agg(to_json(d)) from(select h.name, p.handle as created_by, c.sum, v2.direction
        from (select * from hangs where pack = '{pack}') h inner join 
        (select hang, sum(direction)
        from votes
        group by hang
        order by sum(direction) desc) c
        on h.id = c.hang
        inner join people p
        on h.created_by = p.id
        left join (select * from votes where voter = {user_id}) v2
        on h.id = v2.hang) d
        ;
    '''
    cur.execute(query)
    return cur.fetchall()[0][0]


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        print("Checking user...")
        if 'user' not in session:
            print("Not logged in.")
            res = find_ip(request.remote_addr)
            if res:
                print("IP Found.")
                id = res[0]
                session['user'] = res[1]
                return f(*args, **kwargs)

            return redirect(url_for('new'))

        # current_ip = find_ip(request.remote_addr)
        # if not current_ip:
        #     id = find_user(0, session['user'])[0]
        #     insert_machine_registration(request.remote_addr, id)

        return f(*args, **kwargs)
    return decorated_function

###############################################################
############################ API ##############################
###############################################################

# select h.name, p.handle as created_by, c.sum, v2.direction
# from (select * from hangs where pack = 'testpack') h inner join 
# (select hang, sum(direction)
# from votes
# group by hang
# order by sum(direction) desc) c
# on h.id = c.hang
# inner join people p
# on h.created_by = p.id
# left join (select * from votes where voter = 3) v2
# on h.id = v2.hang
# ;

@app.route('/', methods=['GET'])
@login_required
def home():
    user_id = find_user(0, session['user'])[0]
    pack = get_pack(user_id, 'testpack')
    return render_template('home.html', pack=pack)

@app.route('/new', methods=['GET', 'POST'])
def new():
    if request.method == 'POST':
        username = request.form['handle']

        user = find_user(0, username)
        if not user:
            ip = request.remote_addr
            insert_user(username, ip)
            session['user'] = username
            return redirect(url_for('home'))
        return render_template('new.html', message='Username already taken.')

    return render_template('new.html')


if __name__ == '__main__':
    app.run()