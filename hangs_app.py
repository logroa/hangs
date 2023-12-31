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
from datetime import datetime, date


# NOTES
# i like a learn more link on the chat page that oepns a new window w just
# a simple google search

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
API_URL = os.getenv('API_URL')

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

def insert_user(og_handle, code):
    cur = db_conn.cursor()
    handle = og_handle.replace("'", "''")
    hashed_code = generate_password(code)
    cur.execute(f'''
        INSERT INTO people (handle, code, created_at, access_role) VALUES ('{handle}', '{hashed_code}', '{datetime.now()}', 2);
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


def get_users():
    cur = db_conn.cursor()
    query = '''
        select json_agg(to_json(d)) from (SELECT handle, created_at FROM people ORDER BY created_at) d
        ;
    '''
    cur.execute(query)
    return cur.fetchall()[0][0] 


def check_password(password, password_db_string):
    [algorithm, salt, password_hash] = password_db_string.split("$")
    hash_obj = hashlib.new(algorithm)
    password_salted = salt + password
    hash_obj.update(password_salted.encode('utf-8'))
    return hash_obj.hexdigest() == password_hash


def find_ip(ip):
    cur = db_conn.cursor()
    cur.execute(f"SELECT * FROM people WHERE ip = '{ip}';")
    return cur.fetchone()


def retreive_password(user_id):
    cur = db_conn.cursor()
    cur.execute(f"SELECT code FROM people WHERE id = {user_id}")
    return cur.fetchone()[0]


def get_pack_id(pack_name):
    cur = db_conn.cursor()
    clean_pack_name = pack_name.replace("'", "''")
    query = f'''
        select id from packs where name = '{clean_pack_name}';
    '''
    cur.execute(query)
    return cur.fetchone()[0]


def insert_hang(hang, pack, user):
    clean_hang = hang.replace("'", "''")
    cur = db_conn.cursor()
    cur.execute(f'''
                INSERT INTO hangs (name, created_by, created_at, pack)
                VALUES ('{clean_hang}', {user}, '{datetime.now()}', {pack});
                ''')
    db_conn.commit()


def update_hang(id, name):
    clean_name = name.replace("'", "''")
    cur = db_conn.cursor()
    cur.execute(f'''
                UPDATE hangs SET name = '{clean_name}'
                WHERE id = {id};
                ''')
    db_conn.commit()


def insert_pack(name, description, active):
    clean_name = name.replace("'", "''")
    clean_desc = description.replace("'", "''")
    cur = db_conn.cursor()
    cur.execute(
        f'''INSERT INTO packs (name, description, created_at, active)
        VALUES ('{clean_name}', '{clean_desc}', '{datetime.now()}', {active});
        '''
    )
    db_conn.commit()
    cur.execute(f'''SELECT id FROM packs WHERE name = '{clean_name}';''')
    return cur.fetchone()[0]


def update_pack(id, name, description, active):
    clean_name = name.replace("'", "''")
    clean_desc = description.replace("'", "''")
    cur = db_conn.cursor()
    cur.execute(f'''
                UPDATE packs SET name = '{clean_name}', description = '{clean_desc}', active = {active}
                WHERE id = {id};
                ''')
    db_conn.commit()


def get_pack(user_id, pack):
    print(user_id, pack)
    cur = db_conn.cursor()
    query = f'''
        select json_agg(to_json(d)) from (select h.id, h.name, h.packname, p.handle as created_by, c.sum, v2.direction
        from (select h1.*, p.name as packname from hangs h1
            inner join packs p on p.id = h1.pack
            where p.name = '{pack}') h left join 
        (select hang, sum(direction)
        from votes
        group by hang) c
        on h.id = c.hang
        inner join people p
        on h.created_by = p.id
        left join (select * from votes where voter = {user_id}) v2
        on h.id = v2.hang) d
        ;
    '''
    cur.execute(query)
    data = cur.fetchall()[0][0]
    if data:
        for d in data:
            d['search'] = d['name'].replace(" ", "+")
            if not d['sum']:
                d['sum'] = 0
        return sorted(data, key = lambda x: x['sum'], reverse=True)
    return []


def get_pack_info(pack_name):
    clean_name = pack_name.replace("'", "''")
    cur = db_conn.cursor()
    cur.execute(f'''
                SELECT * FROM packs WHERE name = '{clean_name}';
                ''')
    return cur.fetchone()


def get_packs(active = True):
    cur = db_conn.cursor()
    query = f'''
        select json_agg(to_json(d)) from (select * from packs where active = {active}) d;
    '''
    cur.execute(query)
    packs = cur.fetchall()[0][0]
    if not packs:
        return []
    return packs


def insert_vote(voter, hang, vote, existing):
    cur = db_conn.cursor()
    if existing > -2:
        print("updating")
        cur.execute(f'''
            UPDATE votes SET direction={vote}, created_at='{datetime.now()}' WHERE voter={voter} AND hang={hang};       
        ''')
    else:
        print("inserting")
        cur.execute(f'''
            INSERT INTO votes (voter, hang, direction, created_at) VALUES ({voter}, {hang}, {vote}, '{datetime.now()}');
        ''')
    db_conn.commit()


def get_chats(pack, offset=1):
    cur = db_conn.cursor()
    query = f'''
        select json_agg(to_json(d)) 
        from (select c.*, p.handle from chat c inner join people p on p.id = chatter 
        where c.about = {pack} order by c.created_at desc limit {15*offset}) d;
    '''
    cur.execute(query)
    chats = cur.fetchall()[0][0]
    if not chats:
        chats = []
    for c in chats:
        c['date'] = c['created_at'].split('T')[0]
    chats.reverse()
    return chats


def insert_chat(content, chatter, about):
    cur = db_conn.cursor()
    new_content = content.replace("'", "''")
    query = f'''INSERT INTO chat (chatter, about, content, created_at) VALUES ({chatter}, {about}, '{new_content}', '{datetime.now()}');'''
    cur.execute(query)
    db_conn.commit()


def generate_password(password):
    algorithm = 'sha512'
    salt = uuid.uuid4().hex
    hash_obj = hashlib.new(algorithm)
    password_salted = salt + password
    hash_obj.update(password_salted.encode('utf-8'))
    password_hash = hash_obj.hexdigest()
    password_db_string = "$".join([algorithm, salt, password_hash])
    return password_db_string


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        print("Checking user...")
        # session.clear()
        if 'user' not in session:
            return redirect(url_for('new'))

        # current_ip = find_ip(request.remote_addr)
        # if not current_ip:
        #     id = find_user(0, session['user'])[0]
        #     insert_machine_registration(request.remote_addr, id)


        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        print("Checking user...")
        # session.clear()
        if 'user' not in session:
            return redirect(url_for('new'))

        # current_ip = find_ip(request.remote_addr)
        # if not current_ip:
        #     id = find_user(0, session['user'])[0]
        #     insert_machine_registration(request.remote_addr, id)
     
        if session.get('user') != 1:
            return redirect(url_for('home'))

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
    packs = get_packs()
    return render_template('home.html', packs=packs, user=session['user'])


@app.route('/pack/<pack_name>', methods=['GET', 'POST'])
@login_required
def pack(pack_name):
    user_id = session['userid']
    pack = get_pack(user_id, pack_name)
    print(pack)
    packs = get_packs()
    print(packs)
    desc = ""
    chats = get_chats(get_pack_id(pack_name))
    for p in packs:
        if p['name'] == pack_name:
            desc = p['description']
    for c in chats:
        if c['handle'] == session['user']:
            c['mine'] = True
    return render_template('pack.html', api_url=API_URL, packname=pack_name, description=desc, pack=pack, packs=packs, chats=chats, user=session['user'])


@app.route('/chat', methods=['POST'])
@login_required
def chat():
    data = request.get_json()
    user_id = find_user(0, session['user'])[0]
    chat = data.get('chat')
    pack = data.get('pack')
    insert_chat(chat, user_id, get_pack_id(pack))
    return jsonify(**{
        "status": "success",
        "date": str(date.today())
    })


@app.route('/chat/<pack_name>/<page>', methods=['GET', 'POST'])
@login_required
def more_chats(pack_name, page):
    chats = get_chats(get_pack_id(pack_name), page)
    for c in chats:
        if c['handle'] == session['user']:
            c['mine'] = True
    return jsonify(**{
            "chats": chats
    })


@app.route('/new', methods=['GET', 'POST'])
def new():
    if request.method == 'POST':
        username = request.form['handle'].lower()
        code = request.form['code']
        user = find_user(0, username)
        if not user:
            insert_user(username, code)
            session['user'] = username
            session['userid'] = find_user(0, username)[0]
            return redirect(url_for('home'))
        return render_template('new.html', message='Username already taken.')

    return render_template('new.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        try:
            user = find_user(0, request.form['handle'].lower())
            password_db_string = retreive_password(user[0])
            if check_password(request.form['code'], password_db_string):
                session['user'] = user[1]
                session['userid'] = user[0]
                session.permanent = True
                return redirect(url_for('home'))
            return render_template('login.html', message="Incorrect login")
        except Exception as e:
            return render_template('login.html', message="Incorrect login")
    
    return render_template('login.html')


@app.route('/logout', methods=['POST'])
@login_required
def logout():
    print(f"Logging {session['user']} out.")
    session.clear()
    return redirect(url_for('new'))


@app.route('/vote', methods=['POST'])
def vote():
    try:
        data = request.get_json()
        user_id = session['userid']
        vote = data.get('vote')
        hang = data.get('hang')
        existing = data.get('existing')
        insert_vote(user_id, hang, vote, existing)
        return jsonify(**{
            "status": "success"
        })
    except Exception as e:
        return jsonify(**{
            "status": f"failure: {e}"
        })

###############################################################
######################### ADMIN API ###########################
###############################################################

@app.route('/admin', methods=['GET'])
@admin_required
def admin_panel():
    # list of users and each of the packs as well as link to create new pack
    active_packs = get_packs()
    inactive_packs = get_packs(False)
    users = get_users()
    return render_template('admin.html', active_packs=active_packs, inactive_packs=inactive_packs, users=users)


@app.route('/admin/new_pack', methods=['GET', 'POST'])
@admin_required
def new_pack():
    if request.method == 'POST':
        user_id = session['userid']
        title = request.form['title']
        description = request.form['description']
        active = request.form.get('activepack', "false")
        guys = []
        for i in range(1, 21):
            guys.append(request.form.get(f'hang{i}'))
        pack_id = insert_pack(title, description, active)
        for g in guys:
            if g:
                insert_hang(g, pack_id, user_id)
        return redirect(url_for('admin_panel'))

    # list of users and each of the packs as well as link to create new pack
    return render_template('new_pack.html', new=True)


@app.route('/admin/<pack_name>', methods=['GET', 'POST'])
@admin_required
def modify_pack(pack_name):
    user_id = session['userid']
    pack = [{ "name": h["name"], "id": h["id"] } for h in get_pack(user_id, pack_name)]
    pack_info = get_pack_info(pack_name)
    desc = pack_info[-2]
    active = pack_info[-1]

    if request.method == 'POST':
        
        new_title = request.form['title']
        new_description = request.form['description']
        new_active = request.form.get('activepack', "false")
        update_pack(pack_info[0], new_title, new_description, new_active)
        guys = []
        for i in range(len(pack)):
            new_hang = request.form[f'hang{pack[i]["id"]}']
            if pack[i]["name"] != new_hang:
                guys.append((pack[i]["id"], new_hang))
        for g in guys:
            update_hang(g[0], g[1])

        return redirect(url_for('admin_panel'))
    
    return render_template('new_pack.html', new=False, title=pack_name, pack=pack, description=desc, active=active)


if __name__ == '__main__':
    app.run()