from flask import Flask, render_template, request, redirect, url_for, send_from_directory
import sqlite3
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['DATABASE'] = 'trading_log.db'

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def get_db_connection():
    conn = sqlite3.connect(app.config['DATABASE'])
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    conn = get_db_connection()
    trades = conn.execute("""
        SELECT *,
            quantity * buy_price AS entry_value,
            quantity * sell_price AS exit_value,
            (quantity * sell_price) - (quantity * buy_price) AS pnl
        FROM trading_log
        ORDER BY date
    """).fetchall()
    conn.close()

    # Calculate cumulative PnL
    cumulative = 0
    trade_list = []
    for trade in trades:
        entry = dict(trade)
        entry['cumulative_pnl'] = cumulative + entry['pnl']
        cumulative = entry['cumulative_pnl']
        trade_list.append(entry)

    return render_template('index.html', trades=trade_list)

@app.route('/add', methods=['GET', 'POST'])
def add_trade():
    if request.method == 'POST':
        date = request.form['date']
        stock = request.form['stock']
        quantity = int(request.form['quantity'])
        buy_price = float(request.form['buy_price'])
        sell_price = float(request.form['sell_price'])
        screenshot = request.files['screenshot']

        filename = None
        if screenshot and screenshot.filename != '':
            filename = secure_filename(screenshot.filename)
            screenshot.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        conn = get_db_connection()
        conn.execute('INSERT INTO trading_log (date, stock, quantity, buy_price, sell_price, screenshot) VALUES (?, ?, ?, ?, ?, ?)',
                     (date, stock, quantity, buy_price, sell_price, filename))
        conn.commit()
        conn.close()
        return redirect(url_for('index'))
    return render_template('add.html')

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

