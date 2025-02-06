# app.py
"""
Aplikacja Flask monitorująca dane demograficzne z pliku CSV
i bazy MySQL. Zawiera rejestrację, logowanie, panele statystyk,
porównań i prosty panel administratora.
"""

import os
from time import sleep
import pymysql
from flask import Flask, render_template, request, redirect, url_for, flash, session, g
from werkzeug.security import generate_password_hash, check_password_hash
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from sklearn.linear_model import LinearRegression

###############################################################################
# Inicjalizacja aplikacji
###############################################################################

app = Flask(__name__)
app.config['SECRET_KEY'] = "super_tajny_klucz"

# Pobranie danych do łączenia z MySQL z zmiennych środowiskowych
DB_HOST = os.environ.get('DB_HOST', 'db')
DB_PORT = int(os.environ.get('DB_PORT', '3306'))
DB_USER = os.environ.get('DB_USER', 'demouser')
DB_PASS = os.environ.get('DB_PASS', 'demopass')
DB_NAME = os.environ.get('DB_NAME', 'demografia_db')

# Ścieżka do głównego pliku CSV z danymi demograficznymi
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(BASE_DIR, 'data', 'demografia.csv')

###############################################################################
# Funkcje pomocnicze: łączenie z bazą MySQL i inicjalizacja tabel
###############################################################################

def get_db():
    """
    Zwraca połączenie do bazy MySQL (lub None, jeśli błąd).
    Połączenie cache'owane w obiekcie `g` dla danego requestu.
    """
    if 'db_conn' not in g:
        try:
            g.db_conn = pymysql.connect(
                host=DB_HOST,
                port=DB_PORT,
                user=DB_USER,
                password=DB_PASS,
                database=DB_NAME,
                charset='utf8mb4',
                autocommit=True,
                cursorclass=pymysql.cursors.DictCursor
            )
        except pymysql.MySQLError as e:
            print(f"[ERROR] Błąd połączenia z bazą MySQL: {e}")
            g.db_conn = None
    return g.db_conn

@app.teardown_appcontext
def close_db(error):
    """
    Zamknięcie połączenia z MySQL po zakończeniu obsługi requestu,
    jeśli połączenie zostało nawiązane.
    """
    db_conn = g.pop('db_conn', None)
    if db_conn:
        db_conn.close()

def init_db():
    """
    Tworzy wymagane tabele (users, search_history) w bazie
    oraz w razie potrzeby dodaje konto 'admin'.
    """
    db = get_db()
    if not db:
        return
    try:
        with db.cursor() as cur:
            # Tabela użytkowników
            cur.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    username VARCHAR(50) NOT NULL UNIQUE,
                    password VARCHAR(255) NOT NULL,
                    role VARCHAR(20) NOT NULL DEFAULT 'user'
                )
            """)

            # Tabela historii zapytań
            cur.execute("""
                CREATE TABLE IF NOT EXISTS search_history (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT,
                    wojewodztwo VARCHAR(100),
                    search_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            """)
            db.commit()

            # Dodanie konta admin, jeśli nie istnieje
            cur.execute("SELECT * FROM users WHERE username='admin'")
            admin = cur.fetchone()
            if not admin:
                passhash = generate_password_hash("admin")
                cur.execute(
                    "INSERT INTO users (username, password, role) VALUES (%s, %s, %s)",
                    ('admin', passhash, 'admin')
                )
                db.commit()
    except pymysql.MySQLError as e:
        print(f"[ERROR] Błąd inicjalizacji bazy: {e}")

@app.before_first_request
def before_first_request():
    """
    Próbuje nawiązać połączenie z bazą danych przy pierwszym zapytaniu,
    ponawiając próbę kilkukrotnie (np. gdy kontener MySQL jeszcze nie wstał).
    """
    attempts = 5
    for i in range(attempts):
        db = get_db()
        if db:
            init_db()
            break
        else:
            print("[INIT] Baza danych nie jest gotowa. Próba ponownego połączenia za 5 sek...")
            sleep(5)
    else:
        print("[INIT] Nie udało się połączyć z bazą danych po kilku próbach.")

###############################################################################
# Funkcje pomocnicze: rejestracja/logowanie, zapisywanie historii
###############################################################################

@app.route('/register', methods=['POST'])
def register():
    """
    Rejestracja nowego użytkownika. Tworzy rekord w tabeli `users`,
    o ile nazwa nie jest zajęta. Hasło jest haszowane.
    """
    db = get_db()
    if not db:
        flash("Błąd połączenia z bazą.", "danger")
        return redirect(url_for('index'))

    username = request.form.get('username', '').strip()
    password = request.form.get('password', '').strip()

    if not username or not password:
        flash("Wypełnij pola nazwy użytkownika i hasła.", "warning")
        return redirect(url_for('index'))

    try:
        with db.cursor() as cur:
            cur.execute("SELECT * FROM users WHERE username=%s", (username,))
            row = cur.fetchone()
            if row:
                flash("Taki użytkownik już istnieje.", "warning")
                return redirect(url_for('index'))

            pass_hash = generate_password_hash(password)
            cur.execute(
                "INSERT INTO users (username, password, role) VALUES (%s, %s, %s)",
                (username, pass_hash, 'user')
            )
            db.commit()
        flash("Pomyślnie zarejestrowano! Możesz się zalogować.", "success")
        return redirect(url_for('index'))
    except pymysql.MySQLError as e:
        flash(f"Błąd rejestracji: {e}", "danger")
        return redirect(url_for('index'))

@app.route('/login', methods=['POST'])
def login():
    """
    Logowanie istniejącego użytkownika. Sprawdza hasło i rolę,
    zapisuje dane w sesji.
    """
    db = get_db()
    if not db:
        flash("Błąd połączenia z bazą.", "danger")
        return redirect(url_for('index'))

    username = request.form.get('username', '').strip()
    password = request.form.get('password', '').strip()

    if not username or not password:
        flash("Podaj poprawną nazwę użytkownika i hasło.", "warning")
        return redirect(url_for('index'))

    try:
        with db.cursor() as cur:
            cur.execute("SELECT * FROM users WHERE username=%s", (username,))
            user = cur.fetchone()
            if user and check_password_hash(user['password'], password):
                session['user_id'] = user['id']
                session['username'] = user['username']
                session['role'] = user['role']
                flash("Zalogowano pomyślnie!", "success")
            else:
                flash("Błędne dane logowania.", "danger")
    except pymysql.MySQLError as e:
        flash(f"Błąd logowania: {e}", "danger")

    return redirect(url_for('index'))

@app.route('/logout')
def logout():
    """
    Wylogowuje użytkownika, czyszcząc sesję.
    """
    session.clear()
    flash("Wylogowano.", "info")
    return redirect(url_for('index'))

def save_search_history(woj):
    """
    Zapisuje do bazy historii zapytań, jeśli użytkownik jest zalogowany.
    Argument:
        woj (str): nazwa województwa.
    """
    db = get_db()
    if not db or 'user_id' not in session:
        return
    user_id = session['user_id']
    try:
        with db.cursor() as cur:
            cur.execute(
                "INSERT INTO search_history (user_id, wojewodztwo) VALUES (%s, %s)",
                (user_id, woj)
            )
            db.commit()
    except pymysql.MySQLError as e:
        print(f"[ERROR] Błąd zapisu historii: {e}")

###############################################################################
# Strony główne: index, admin, statystyki, porównanie
###############################################################################

@app.route('/')
def index():
    """
    Strona główna. Prezentuje podstawowe opcje: Statystyki, Porównania,
    logowanie i rejestracja.
    """
    return render_template('index.html')

@app.route('/admin')
def admin_panel():
    """
    Panel administracyjny dostępny wyłącznie dla użytkowników z rolą 'admin'.
    Wyświetla listę użytkowników i ostatnie wpisy w historii zapytań.
    """
    if 'role' not in session or session['role'] != 'admin':
        flash("Brak uprawnień.", "danger")
        return redirect(url_for('index'))

    db = get_db()
    if not db:
        flash("Błąd połączenia z bazą.", "danger")
        return redirect(url_for('index'))

    users_data = []
    history_data = []
    try:
        with db.cursor() as cur:
            cur.execute("SELECT id, username, role FROM users ORDER BY id ASC")
            users_data = cur.fetchall()

            cur.execute("""
                SELECT h.id, h.user_id, u.username, h.wojewodztwo, h.search_time
                FROM search_history h
                JOIN users u ON u.id = h.user_id
                ORDER BY h.search_time DESC
                LIMIT 30
            """)
            history_data = cur.fetchall()
    except pymysql.MySQLError as e:
        flash(f"Błąd zapytania: {e}", "danger")

    return render_template('admin.html', users=users_data, history=history_data)

@app.route('/stats', methods=['GET', 'POST'])
def stats():
    """
    Strona prezentująca statystyki demograficzne wybranego województwa:
    - Wykres liczby ludności w czasie + regresja liniowa
    - Porównanie mężczyzn i kobiet
    - Struktura wiekowa w najnowszym roku
    """
    # Wczytanie CSV z danymi
    try:
        df = pd.read_csv(CSV_PATH, delimiter=',')
    except Exception as e:
        return f"Błąd wczytywania CSV: {e}"

    woj_list = sorted(df['Wojewodztwo'].unique())
    if request.method == 'POST':
        wybrane_woj = request.form.get('wojewodztwo')
    else:
        wybrane_woj = woj_list[0] if woj_list else None

    if not wybrane_woj:
        return "Brak danych o województwach w pliku CSV."

    # Zapis w historii zapytań, jeśli zalogowany
    save_search_history(wybrane_woj)

    # Filtrowanie danych dla wybranego województwa
    df_woj = df[df['Wojewodztwo'] == wybrane_woj].copy()
    if df_woj.empty:
        return f"Brak rekordów dla woj. {wybrane_woj}"

    # WYKRES 1: Populacja w czasie + prognoza
    df_agg = df_woj.groupby('Rok', as_index=False)['ogółem ogółem'].sum()
    fig1 = px.line(df_agg, x='Rok', y='ogółem ogółem',
                   title=f"Liczba ludności w {wybrane_woj} (lata)")

    # Regresja liniowa dla prognozy
    X = df_agg[['Rok']]
    y = df_agg['ogółem ogółem']
    model = LinearRegression()
    model.fit(X, y)
    last_year = int(df_agg['Rok'].max())
    forecast_horizon = 5
    future_years = np.arange(last_year+1, last_year+1+forecast_horizon).reshape(-1, 1)
    preds = model.predict(future_years)
    fig1.add_trace(go.Scatter(
        x=future_years.flatten(),
        y=preds,
        mode='lines+markers',
        name='Prognoza (LR)'
    ))
    graph1_html = fig1.to_html(full_html=False)

    # WYKRES 2: Mężczyźni vs kobiety
    df_mk = df_woj.groupby('Rok', as_index=False)[['ogółem mężczyźni', 'ogółem kobiety']].sum()
    fig2 = px.bar(df_mk, x='Rok', y=['ogółem mężczyźni', 'ogółem kobiety'],
                  barmode='group',
                  title=f"Mężczyźni vs Kobiety w {wybrane_woj}")
    graph2_html = fig2.to_html(full_html=False)

    # WYKRES 3: Struktura wiekowa w najnowszym roku
    newest_year = df_woj['Rok'].max()
    df_latest = df_woj[df_woj['Rok'] == newest_year].copy()
    age_cols = [c for c in df.columns if 'ogółem' in c and '-' in c]
    if age_cols:
        df_age_sum = df_latest[age_cols].sum()
        df_age = pd.DataFrame({'Grupa': age_cols, 'Liczba': df_age_sum.values})
        fig3 = px.bar(df_age, x='Grupa', y='Liczba',
                      title=f"Struktura wiekowa ({newest_year}) w {wybrane_woj}")
        graph3_html = fig3.to_html(full_html=False)
    else:
        graph3_html = "<p>Brak szczegółowych danych o grupach wiekowych.</p>"

    return render_template('stats.html',
                           woj_list=woj_list,
                           wybrane_woj=wybrane_woj,
                           graph1=graph1_html,
                           graph2=graph2_html,
                           graph3=graph3_html,
                           forecast_horizon=forecast_horizon)

@app.route('/compare')
def compare():
    """
    Strona z prostym porównaniem województw dla ostatniego roku,
    wyświetlana jako wykres słupkowy.
    """
    try:
        df = pd.read_csv(CSV_PATH, delimiter=',')
    except Exception as e:
        return f"Błąd wczytywania CSV: {e}"

    last_year = df['Rok'].max()
    df_last = df[df['Rok'] == last_year].copy()
    df_comp = df_last.groupby('Wojewodztwo', as_index=False)['ogółem ogółem'].sum()
    fig = px.bar(df_comp, x='Wojewodztwo', y='ogółem ogółem',
                 title=f"Porównanie województw (rok {last_year})",
                 color='Wojewodztwo')
    fig_html = fig.to_html(full_html=False)
    return render_template('compare.html', fig_html=fig_html)

###############################################################################
# Ranking najludniejszych województw
###############################################################################

@app.route('/ranking')
def ranking():
    """
    Nowa trasa pokazująca tabelę 5 najludniejszych województw
    w ostatnim dostępnym roku.
    """
    try:
        df = pd.read_csv(CSV_PATH, delimiter=',')
    except Exception as e:
        return f"Błąd wczytywania CSV: {e}"

    last_year = df['Rok'].max()
    df_last = df[df['Rok'] == last_year].copy()
    grouped = df_last.groupby('Wojewodztwo', as_index=False)['ogółem ogółem'].sum()
    ranking_df = grouped.sort_values('ogółem ogółem', ascending=False).head(5)
    # Prosty DataFrame do przekazania do templatu
    ranking_list = ranking_df.to_dict(orient='records')

    return render_template('ranking.html', ranking=ranking_list, rok=last_year)

###############################################################################
# Uruchomienie aplikacji
###############################################################################

if __name__ == '__main__':
    # Aplikacja uruchamiana na porcie 5001, widoczna dla pozostałych kontenerów (0.0.0.0)
    app.run(host='0.0.0.0', port=5001, debug=True)
