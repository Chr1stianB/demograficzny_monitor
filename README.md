# Demograficzny Monitor

Aplikacja Flask demonstrująca przetwarzanie danych demograficznych z plików CSV i bazy MySQL. Umożliwia rejestrację, logowanie, przeglądanie statystyk populacyjnych, dokonywanie prostych porównań oraz posiada panel administracyjny.

## Spis treści
1. [Wymagania](#wymagania)
2. [Struktura projektu](#struktura-projektu)
3. [Opis plików](#opis-plików)
4. [Instrukcja uruchomienia](#instrukcja-uruchomienia)
5. [Zatrzymywanie i czyszczenie środowiska](#zatrzymywanie-i-czyszczenie-środowiska)
6. [Konfiguracja](#konfiguracja)
7. [Funkcjonalności aplikacji](#funkcjonalności-aplikacji)
8. [Pobieranie danych z Kaggle (data_download.py)](#pobieranie-danych-z-kaggle-datadownloadpy)
9. [Autor / Kontakt](#autor--kontakt)

---

## Wymagania
- **Docker** w wersji co najmniej 19+
- **Docker Compose** w wersji 1.29+ (lub wbudowany w Docker Desktop)
- Opcjonalnie: Git do klonowania/zarządzania repozytorium

---

## Struktura projektu

```
demograficzny_monitor/
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── app/
│   ├── app.py
│   ├── data/
│   │   ├── demografia.csv
│   │   ├── population_by_region_combined_en.csv
│   │   └── population_data.db
│   ├── data_download.py
│   ├── kaggle.json
│   ├── static/
│   │   ├── css/
│   │   │   └── styles.css
│   │   └── js/
│   │       └── scripts.js
│   └── templates/
│       ├── admin.html
│       ├── compare.html
│       ├── index.html
│       ├── layout.html
│       ├── ranking.html
│       └── stats.html
└── README.md
```

---

## Opis plików

### Główne pliki aplikacji

- **Dockerfile**  
  - Buduje obraz Dockera zawierający środowisko Python (3.11-slim), instaluje zależności z `requirements.txt` i kopiuje kod do `/app`.

- **docker-compose.yml**  
  - Definiuje dwa kontenery:  
    1. `db` (MySQL, port hosta 3307)  
    2. `app` (Aplikacja Flask, port hosta 5001)  
  - Uruchamiane przez `docker-compose up --build`.

- **requirements.txt**  
  - Lista zależności Python (Flask, PyMySQL, Plotly, Pandas, itp.).

### Katalog `app/`
- **app.py**  
  - Główny plik aplikacji Flask, zawierający:
    - Konfigurację bazy MySQL
    - Trasy (routes) do: `/` (główna), `/stats`, `/compare`, `/ranking`, `/admin`
    - Obsługę rejestracji, logowania i wylogowania
    - Generowanie wykresów w Plotly z danych z CSV
    - Panel Administratora

- **data/**  
  - Przechowuje różne pliki danych, m.in.:
    - `demografia.csv` – główny plik z danymi demograficznymi wykorzystywany w aplikacji
    - `population_data.db` (przykładowa baza SQLite, używana przez skrypt `data_download.py`)
    - `population_by_region_combined_en.csv` (opcjonalny plik z danymi w jęz. angielskim)

- **data_download.py**  
  - Skrypt demonstracyjny pokazujący, jak pobierać i prezentować dane z bazy SQLite (`population_data.db`).
  - Uruchamia wewnętrzny serwer Flask, pozwala wizualizować dane z kolumn `province`, `year`, `overall_overall` itp.
  - Zawiera przykłady tras: `/` (wykres) i `/province/<province_name>` (szczegółowe dane dla województwa).

- **kaggle.json**  
  - Plik z kluczem API do pobierania danych z serwisu Kaggle (format: JSON).  
  - **Należy w nim umieścić własne dane autoryzacyjne**: `"username"` i `"key"`.  
  - Jeśli planujesz pobierać dane z Kaggle (np. w `data_download.py` lub innym skrypcie), musisz:
    1. Zarejestrować się w Kaggle
    2. Wygenerować klucz API
    3. Skopiować zawartość klucza do `kaggle.json`

- **static/**  
  - Zasoby statyczne (CSS, JS) dla aplikacji:
    - `css/styles.css` – Style ogólne
    - `js/scripts.js` – Skrypt JavaScript (m.in. do własnych efektów czy obsługi formularzy)

- **templates/**  
  - Szablony HTML (Jinja2) używane przez Flask:
    - `layout.html` – bazowy layout z paskiem nawigacji, modalami do logowania/rejestracji, Bootstrap 5  
    - `index.html` – strona główna
    - `stats.html` – strona statystyk (wykresy)
    - `compare.html` – porównanie województw
    - `admin.html` – panel administracyjny
    - `ranking.html` – ranking województw

---

## Instrukcja uruchomienia

1. **Klonowanie repozytorium (opcjonalne)**  
   ```bash
   git clone https://github.com/twoj-user/demograficzny_monitor.git
   cd demograficzny_monitor
   ```

2. **Uruchamianie przez Docker Compose**  
   - Aby zbudować i uruchomić wszystkie kontenery, wykonaj w katalogu głównym:
     ```bash
     docker-compose up --build
     ```
   - Po poprawnym uruchomieniu:
     - Aplikacja będzie dostępna pod adresem [http://localhost:5001](http://localhost:5001)
     - Baza MySQL jest dostępna z hosta na porcie `3307` (login: `demouser`, hasło: `demopass`).

3. **Sprawdzenie działania**  
   - Otwórz przeglądarkę na [http://localhost:5001](http://localhost:5001).
   - Powinna załadować się strona główna aplikacji.  
   - Możesz się zarejestrować, zalogować i przeglądać statystyki.

---

## Zatrzymywanie i czyszczenie środowiska

- **Zatrzymanie kontenerów** (bez usuwania danych):
  ```bash
  docker-compose down
  ```
  Wolumen `db_data` z bazą MySQL zostaje zachowany.

- **Całkowite usunięcie kontenerów i wolumenów**:
  ```bash
  docker-compose down -v
  ```
  Usuwa również wolumen `db_data`, czyli całą zawartość bazy.

---

## Konfiguracja

- **Zmienne środowiskowe** (w `docker-compose.yml`):
  ```yaml
  environment:
    DB_HOST: db
    DB_PORT: 3306
    DB_USER: demouser
    DB_PASS: demopass
    DB_NAME: demografia_db
  ```
  - `DB_HOST=db` oznacza nazwę usługi w sieci Docker
  - `DB_PORT=3306` to domyślny port MySQL wewnątrz kontenera (mapowany na 3307 na hoście)

- **Zmiana CSV**:  
  W pliku `app.py` zdefiniowana jest ścieżka do pliku `demografia.csv`. Możesz podmienić go na własny, jeśli dane mają podobną strukturę kolumn.

- **Zależności**:  
  Przy uruchamianiu przez Docker Compose wszystkie wymagane pakiety z `requirements.txt` są instalowane w kontenerze.

---

## Funkcjonalności aplikacji

1. **Strona główna** (`/`):
   - Podstawowe informacje, przyciski do statystyk i porównań.
   - Możliwość logowania / rejestracji (modale Bootstrap).

2. **Rejestracja i logowanie**:
   - Hasła przechowywane jako hash (Funkcja `generate_password_hash`).
   - Po zalogowaniu użytkownik może przeglądać dane i zapisywać w historii zapytań wybrane województwa.

3. **Statystyki** (`/stats`):
   - Wybór województwa z listy rozwijanej.
   - Wykresy generowane w Plotly: populacja w czasie + regresja liniowa, podział mężczyźni/kobiety, struktura wiekowa.

4. **Porównanie** (`/compare`):
   - Prosty wykres słupkowy z liczbą ludności w ostatnim roku.

5. **Panel Administratora** (`/admin`):
   - Wyświetla listę użytkowników i ostatnie zapytania (z tabeli `search_history`).
   - Dostęp tylko dla konta z rolą `admin`.

6. **Ranking** (`/ranking`):
   - Przykładowe rozszerzenie wyświetlające TOP 5 województw o największej populacji.

---

## Pobieranie danych z Kaggle (`data_download.py`)

- Plik `app/data_download.py` to **dodatkowy** skrypt Flask, który może działać niezależnie (np. poza kontenerem) i pokazuje przykładowe pobieranie oraz wizualizację danych z bazy SQLite (`population_data.db`).  
- Aby pobrać dane z Kaggle, potrzebny jest plik `kaggle.json` z Twoimi **danymi autoryzacyjnymi**:
  ```json
  {
    "username": "twoja_nazwa_kaggle",
    "key": "twoj_klucz_api_kaggle"
  }
  ```
- **Krok po kroku**:
  1. Zarejestruj się w [Kaggle](https://www.kaggle.com) (jeśli jeszcze nie masz konta).
  2. Wygeneruj klucz API (sekcja: *Account -> API -> Create New API Token*).
  3. Zapisz ten klucz do pliku `kaggle.json` w katalogu `app/`.
  4. Skrypt `data_download.py` może być rozbudowany o komendy `kaggle datasets download ...` lub inne funkcje, by pobierać dane i zapisywać do `population_data.db`.
  5. Aby uruchomić ten skrypt (np. lokalnie), wykonaj:
     ```bash
     cd app
     python data_download.py
     ```
     i wejdź na [http://localhost:5001](http://localhost:5001).  
     Skrypt pokazuje przykładowy wykres słupkowy (`/`) i trasę `/province/<province_name>` dla szczegółowych danych.

> **Uwaga:** `data_download.py` nie jest zintegrowany z główną aplikacją demograficzną; pełni raczej rolę demo do pobierania/przetwarzania innych danych.
