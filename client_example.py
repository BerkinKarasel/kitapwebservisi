import json
from urllib.parse import quote
from urllib.request import urlopen


BASE_URL = "http://127.0.0.1:8000"


def get_json(path):
    with urlopen(f"{BASE_URL}{path}") as response:
        return json.loads(response.read().decode("utf-8"))


def main():
    samples = {
        "isbn_ile_kitap": get_json("/api/books/by-isbn?isbn=9780060853983"),
        "yazara_gore_kitaplar": get_json(f"/api/books/by-author?author={quote('Oguz Atay')}"),
        "ture_gore_kitaplar": get_json(f"/api/books/by-genre?genre={quote('Roman')}"),
        "kitap_adi_ile_basimevi": get_json(f"/api/books/publisher-by-title?title={quote('Tutunamayanlar')}"),
    }

    print(json.dumps(samples, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
