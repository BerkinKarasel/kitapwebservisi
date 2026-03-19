# Kitap Web Servisi

Bu proje, yerel ortamda calisan SQLite tabanli bir kitap web servisidir. Hem JSON API hem de tarayicida kullanilabilen kucuk bir arayuz sunar.

## Ozellikler

- `kitap bul(isbn)`
- `kitaplarinin listesi bul(yazar adi soyadi)`
- `kitap listesi bul(tur)`
- SQLite veritabani ile kalici veri saklama
- Tarayicida calisan kucuk sorgu arayuzu
- Hazir ornek veriler ile ilk calistirmada otomatik kurulum

## Proje Yapisi

- `app.py`: HTTP sunucusu, API endpointleri ve veritabani baslatma kodu
- `database/books.db`: Uygulama calisinca otomatik olusan SQLite veritabani
- `static/index.html`: Kucuk arayuz
- `static/styles.css`: Arayuz tasarimi
- `static/app.js`: Arayuzun API ile haberlesmesi

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

## Gelistirme Fikirleri

- Kitap ekleme, guncelleme ve silme servisleri
- Ayri `authors` ve `publishers` yonetim ekranlari
- Filtreleme, sayfalama ve siralama
- Birim testleri ve entegrasyon testleri
- Docker ile paketleme

## Kod ile Cagirma Ornegi

Sunucu calisir durumdayken asagidaki komutla ornek istemciyi test edebilirsiniz:

```bash
python client_example.py
```
