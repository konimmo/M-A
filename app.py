import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session, g
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'change_this_secret'
DATABASE = 'database.db'

# DB helpers

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(exception=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()

def init_db():
    db = get_db()
    with app.open_resource('schema.sql') as f:
        db.executescript(f.read().decode('utf8'))
    db.commit()

# Routes
@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('home.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        db = get_db()
        user = db.execute('SELECT * FROM user WHERE email = ?', (request.form['email'],)).fetchone()
        if user and check_password_hash(user['password'], request.form['password']):
            session['user_id'] = user['id']
            return redirect(url_for('index'))
        error = 'Credenziali non valide'
    return render_template('login.html', error=error)

@app.route('/register', methods=['GET', 'POST'])
def register():
    error = None
    if request.method == 'POST':
        db = get_db()
        if db.execute('SELECT id FROM user WHERE email = ?', (request.form['email'],)).fetchone():
            error = 'Email già registrata'
        else:
            db.execute('INSERT INTO user (name, email, password) VALUES (?,?,?)',
                       (request.form['name'], request.form['email'], generate_password_hash(request.form['password'])))
            db.commit()
            return redirect(url_for('login'))
    return render_template('register.html', error=error)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/prenotazione', methods=['GET', 'POST'])
def prenotazione():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    db = get_db()
    if request.method == 'POST':
        service = request.form['service']
        stylist = request.form['stylist']
        date = request.form['date']
        time = request.form['time']
        db.execute('INSERT INTO booking (user_id, service, stylist, date, time) VALUES (?,?,?,?,?)',
                   (session['user_id'], service, stylist, date, time))
        db.commit()
        return redirect(url_for('notifiche'))
    return render_template('prenotazione.html')

@app.route('/notifiche')
def notifiche():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    db = get_db()
    bookings = db.execute('SELECT * FROM booking WHERE user_id = ?', (session['user_id'],)).fetchall()
    return render_template('notifiche.html', bookings=bookings)

@app.route('/profilo')
def profilo():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    db = get_db()
    user = db.execute('SELECT * FROM user WHERE id = ?', (session['user_id'],)).fetchone()
    bookings = db.execute('SELECT * FROM booking WHERE user_id = ? ORDER BY date DESC', (session['user_id'],)).fetchall()
    return render_template('profilo.html', user=user, bookings=bookings)

@app.route('/contatti')
def contatti():
    return render_template('contatti.html')

if __name__ == '__main__':
    import os
    if not os.path.exists(DATABASE):
        with app.app_context():
            init_db()
    app.run(debug=True)
