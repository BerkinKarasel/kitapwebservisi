# Kitap Web Servisi

Bu proje, yerel ortamda calisan SQLite tabanli bir kitap web servisidir. Hem JSON API hem de tarayicida kullanilabilen kucuk bir arayuz sunar.

## Ozellikler

- `kitap bul(isbn)`
- `kitaplarinin listesi bul(yazar adi soyadi)`
- `kitap listesi bul(tur)`
- SQLite veritabani ile kalici veri saklama
- Tarayicida calisan kucuk sorgu arayuzu
- Hazir ornek veriler ile ilk calistirmada otomatik kurulum
- JSON-LD ve Turtle cikti ureten semantic web servisleri

## Proje Yapisi

- `app.py`: HTTP sunucusu, API endpointleri ve veritabani baslatma kodu
- `database/books.db`: Uygulama calisinca otomatik olusan SQLite veritabani
- `static/index.html`: Kucuk arayuz
- `static/styles.css`: Arayuz tasarimi
- `static/app.js`: Arayuzun API ile haberlesmesi
- `app.py` icindeki `Semantic Web Services` blogu: semantic endpointler ve RDF donusumleri
- `semantic_data/books.jsonld`: Veritabanindan bagimsiz semantic veri kaynagi

## Calistirma

1. Proje klasorunde terminal acin.
2. Su komutu calistirin:

```bash
python app.py
```

3. Tarayicida su adresi acin:

```text
http://127.0.0.1:8000
```

## Tek Tikla Acilis

Uygulamayi cift tiklayarak acmak icin su dosyayi kullanabilirsiniz:

```text
start_app.bat
```

Bu dosya sunucuyu baslatir ve uygulamayi varsayilan tarayicida otomatik acar. Sunucu zaten aciksa sadece tarayiciyi acar.

## API Uclari

### 1. ISBN ile kitap bul

```text
GET /api/books/by-isbn?isbn=9780060853983
```

### 2. Yazar adina gore kitaplarini bul

```text
GET /api/books/by-author?author=Oguz%20Atay
```

### 3. Ture gore kitap listesini bul

```text
GET /api/books/by-genre?genre=Roman
```

### 4. Kitap adina gore basimevini bul

```text
GET /api/books/publisher-by-title?title=Tutunamayanlar
```

### 5. Tum kitaplari listele

```text
GET /api/books
```

## Semantic Web Servisleri

Bu projede semantic servisler `app.py` dosyasinda ayri bir `Semantic Web Services` blogu icinde toplanmistir.
Bu servisler SQLite yerine `semantic_data/books.jsonld` dosyasini veri kaynagi olarak kullanir.
Klasik servislerde `28` kitap varken semantic veri kumesinde `39` kitap ve daha zengin alanlar bulunur.

Semantic tarafa ozel zengin alanlar:

- `translator`
- `original_language`
- `series`
- `award`
- `keywords`

### 1. JSON-LD olarak tum kitaplar

```text
GET /semantic/books
```

### 2. JSON-LD olarak ISBN ile kitap

```text
GET /semantic/books/by-isbn?isbn=9780060853983
```

### 3. JSON-LD olarak yazara gore kitaplar

```text
GET /semantic/books/by-author?author=Sabahattin%20Ali
```

### 4. JSON-LD olarak ture gore kitaplar

```text
GET /semantic/books/by-genre?genre=Roman
```

### 5. Turtle olarak semantic cikti

```text
GET /semantic/books/by-isbn?isbn=9780060853983&format=turtle
```

### 6. Ontoloji tanimi

```text
GET /semantic/ontology
```

### 7. Hazir demo sorgulari

```text
GET /semantic/demo-queries
```

### 8. Semantic filtre sorgu endpointi

Bu endpoint birden fazla filtreyi tek semantic sorguda birlestirir.

```text
GET /semantic/query?author=Sabahattin%20Ali&genre=Roman
GET /semantic/query?publisher=Can%20Cocuk%20Yayinlari&year=2021
GET /semantic/query?title=Kucuk%20Prens&format=turtle
GET /semantic/query?translator=Aydin%20Eme%C3%A7
GET /semantic/query?series=Bilimkurgu%20Klasikleri
GET /semantic/query?award=Pulitzer
```

### 9. Mini SPARQL sozdizimi

Bu endpoint kontrollu bir mini SPARQL yapisi kullanir.

Desteklenen kalip:

```text
SELECT * WHERE author = "Sabahattin Ali" AND genre = "Roman"
SELECT * WHERE title CONTAINS "Prens" LIMIT 1
SELECT ?book WHERE publisher = "Can Cocuk Yayinlari"
```

Desteklenen alanlar:

- `isbn`
- `title`
- `author`
- `genre`
- `publisher`
- `translator`
- `original_language`
- `series`
- `award`
- `year`

Desteklenen operatorler:

- `=`
- `CONTAINS`

Not:
- `isbn` ve `year` sadece `=` ile kullanilabilir.
- Cikti varsayilan olarak `JSON-LD` doner.
- `format=turtle` ile Turtle cikti alinabilir.

Ornekler:

```text
GET /semantic/sparql?query=SELECT%20*%20WHERE%20author%20=%20%22Sabahattin%20Ali%22%20AND%20genre%20=%20%22Roman%22
GET /semantic/sparql?query=SELECT%20*%20WHERE%20title%20CONTAINS%20%22Prens%22%20LIMIT%201&format=turtle
GET /semantic/sparql?query=SELECT%20*%20WHERE%20translator%20CONTAINS%20%22Eme%C3%A7%22%20AND%20original_language%20=%20%22Portekizce%22
GET /semantic/sparql?query=SELECT%20*%20WHERE%20award%20CONTAINS%20%22Pulitzer%22
```

## Ornek JSON Sonucu

```json
{
  "title": "Good Omens",
  "isbn": "9780060853983",
  "genre": "Fantastik",
  "publisher": "William Morrow",
  "publish_year": 2006,
  "authors": [
    "Neil Gaiman",
    "Terry Pratchett"
  ]
}
```

## Kod ile Cagirma Ornegi

Sunucu calisir durumdayken asagidaki komutla ornek istemciyi test edebilirsiniz:

```bash
python client_example.py
```
