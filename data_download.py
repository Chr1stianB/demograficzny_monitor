# data_download.py
from flask import Flask, render_template, redirect, url_for
from sqlalchemy import create_engine
import pandas as pd
import plotly.express as px
import json
import plotly

app = Flask(__name__)

# Ścieżka do bazy danych
DATABASE_PATH = "/app/data/population_data.db"

# Tworzenie silnika SQLAlchemy
engine = create_engine(f'sqlite:///{DATABASE_PATH}')

@app.route('/')
def index():
    try:
        # Pobieranie danych z bazy
        query = "SELECT * FROM population"
        df = pd.read_sql(query, engine)

        # Usunięcie niepotrzebnej kolumny 'index.1' jeśli istnieje
        if 'index.1' in df.columns:
            df = df.drop(columns=['index.1'])

        # Debugowanie kolumn
        print("Kolumny w DataFrame:", df.columns)

        # Filtracja danych dla roku 2021
        df_2021 = df[df['year'] == 2021]

        # Użycie właściwej kolumny 'y'
        y_column = 'overall_overall' if 'overall_overall' in df_2021.columns else 'overall'

        # Sprawdzenie czy 'y_column' istnieje i czy df_2021 nie jest pusty
        if y_column not in df_2021.columns:
            raise ValueError(f"Column '{y_column}' does not exist in the DataFrame.")
        if df_2021.empty:
            raise ValueError("No data available for year 2021.")

        # Tworzenie wykresu
        fig = px.bar(
            df_2021, 
            x='province', 
            y=y_column, 
            title='Liczba Ludności w Województwach w 2021 Roku',
            labels={y_column: 'Liczba Ludności', 'province': 'Województwo'},
            color='province'
        )

        graphJSON = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

        # Przekazanie danych do szablonu
        return render_template('index.html', graphJSON=graphJSON, data=df)
    except Exception as e:
        print(f"Error in index route: {e}")
        return f"An error occurred while processing your request: {e}"

@app.route('/province/<province_name>')
def province_detail(province_name):
    try:
        # Pobieranie danych dla wybranego województwa
        query = f"SELECT * FROM population WHERE province = '{province_name}'"
        df = pd.read_sql(query, engine)

        # Usunięcie niepotrzebnej kolumny 'index.1' jeśli istnieje
        if 'index.1' in df.columns:
            df = df.drop(columns=['index.1'])

        if df.empty:
            return redirect(url_for('index'))

        # Debugowanie kolumn
        print("Kolumny w DataFrame:", df.columns)

        # Użycie właściwej kolumny 'y'
        y_column = 'overall_overall' if 'overall_overall' in df.columns else 'overall'

        # Sprawdzenie czy 'y_column' istnieje i czy df nie jest pusty
        if y_column not in df.columns:
            raise ValueError(f"Column '{y_column}' does not exist in the DataFrame.")
        if df.empty:
            raise ValueError("No data available for the selected province.")

        # Wizualizacja trendu ludności w czasie
        fig = px.line(
            df, 
            x='year', 
            y=y_column,  
            title=f'Trend Ludności w {province_name}',
            labels={y_column: 'Liczba Ludności', 'year': 'Rok'}
        )

        graphJSON = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

        return render_template('province.html', graphJSON=graphJSON, province_name=province_name)
    except Exception as e:
        print(f"Error in province_detail route: {e}")
        return f"An error occurred while processing your request: {e}"

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5001)
