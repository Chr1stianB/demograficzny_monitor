"""
Skrypt do jednorazowego pobierania danych demograficznych z Kaggle.
Nie uruchamia serwera Flask ani nie zajmuje portu.
Zakłada, że w katalogu głównym znajduje się kaggle.json
lub zmienna KAGGLE_CONFIG_DIR poprawnie wskazuje jego lokalizację.
"""

import os
import subprocess

def download_data():
    """
    Pobiera zestaw danych z Kaggle (np. plik CSV) i zapisuje go
    w katalogu 'app/data/' pod nazwą 'demografia.csv'.
    """
    # Przykład pobierania z Kaggle CLI:
    # Tutaj wstaw własną nazwę datasetu:
    dataset = "worldbank/population"
    target_dir = "app/data"
    file_name = "demografia.csv"

    # Upewnij się, że katalog docelowy istnieje
    if not os.path.exists(target_dir):
        os.makedirs(target_dir, exist_ok=True)

    print(f"[INFO] Pobieram dane z Kaggle: {dataset}")

    # Pobranie całego datasetu do tymczasowego folderu
    subprocess.run(["kaggle", "datasets", "download", "-d", dataset, "-p", target_dir, "--unzip"], check=True)

    # Jeżeli Kaggle ściąga wiele plików, trzeba je odpowiednio przenieść/zmienić nazwę.
    # Na przykład, jeśli w dataset jest plik "population.csv", można zrobić:
    original_file_path = os.path.join(target_dir, "population.csv")  # zmodyfikuj zgodnie z nazwą w paczce
    new_file_path = os.path.join(target_dir, file_name)

    if os.path.exists(original_file_path):
        os.rename(original_file_path, new_file_path)
        print(f"[INFO] Plik został zapisany jako {new_file_path}")
    else:
        print("[WARNING] Nie znaleziono oczekiwanego pliku 'population.csv'. Sprawdź nazwę w dataset.")

def main():
    try:
        download_data()
        print("[INFO] Pobieranie zakończone sukcesem.")
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Błąd podczas pobierania danych z Kaggle: {e}")
    except Exception as e:
        print(f"[ERROR] Inny błąd: {e}")

if __name__ == "__main__":
    main()
