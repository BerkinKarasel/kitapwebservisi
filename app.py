import json
import mimetypes
import re
import shutil
import sqlite3
import sys
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, quote, unquote, urlparse


if getattr(sys, "frozen", False):
    RESOURCE_DIR = Path(getattr(sys, "_MEIPASS", Path(sys.executable).resolve().parent))
    DATA_DIR = Path(sys.executable).resolve().parent
else:
    RESOURCE_DIR = Path(__file__).resolve().parent
    DATA_DIR = RESOURCE_DIR

DB_PATH = DATA_DIR / "database" / "books.db"
BUNDLED_STATIC_DIR = RESOURCE_DIR / "static"
STATIC_DIR = DATA_DIR / "static" if getattr(sys, "frozen", False) else BUNDLED_STATIC_DIR
SEMANTIC_DATA_DIR = DATA_DIR / "semantic_data"
SEMANTIC_DATA_PATH = SEMANTIC_DATA_DIR / "books.jsonld"
OVERRIDES_PATH = DATA_DIR / "book_overrides.json"
FALLBACK_COVER = "/covers/default.svg"
BASE_URL = "http://127.0.0.1:8000"


SAMPLE_BOOKS = [
    {
        "title": "Saatleri Ayarlama Enstitüsü",
        "authors": ["Ahmet Hamdi Tanpınar"],
        "isbn": "9789753638029",
        "genre": "Roman",
        "publisher": "Dergah Yayınları",
        "publish_year": 2019,
        "cover_url": "/covers/saatleriayarlamaenstitusu.jpg",
        "description": "Ahmet Hamdi Tanpınar, Saatleri Ayarlama Enstitüsü’nde Hayri İrdal, Halit Ayarcı, Dr. Ramiz ve ötekilerin yaşantı ve eylemleriyle modern bir Türkiye alegorisi inşa ediyor. Zamanlar ve yaşantılar arasından geçiş krizlerinin insan ve toplumdaki karşılıklarını bürokrasi ironisi üzerinden, derinlikli bir entelektüel arka planla inşa ederken, hüznün müstesna bir mizah şöleniyle nasıl aşılabileceğinin de imkânlarını sunuyor. Saatleri Ayarlama Enstitüsü, dünün olduğu gibi, bugünün ve geleceğin romanıdır.",
    },
    {
        "title": "Tutunamayanlar",
        "authors": ["Oguz Atay"],
        "isbn": "9789754700114",
        "genre": "Roman",
        "publisher": "İletişim Yayınları",
        "publish_year": 2020,
        "cover_url": "/covers/tutunamayanlar.jpg",
        "description": "Türk edebiyatının en önemli eserlerinden biri olan Tutunamayanlar’ı Berna Moran, “hem söyledikleri hem de söyleyiş biçimiyle bir başkaldırı” olarak niteler. Moran’a göre “Oğuz Atay’ın mizah gücü, duyarlılığı ve kullandığı teknik incelikler, Tutunamayanlar’ı büyük bir yeteneğin ürünü yapmış, yapıttaki bu yetkinlik Türk romanını çağdaş roman anlayışıyla aynı hizaya getirmiş ve ona çok şey kazandırmıştır.” Küçük burjuva dünyasını zekice alaya alan Atay “saldırısını, tutunanların anlamayacağı, red edeceği türden bir romanla yapar.” Tutunamayanlar, 1970 TRT Roman Ödülü’nü kazanmıştı.",
    },
    {
        "title": "Kürk Mantolu Madonna",
        "authors": ["Sabahattin Ali"],
        "isbn": "9789753638021",
        "genre": "Roman",
        "publisher": "Yapı Kredi Yayınları",
        "publish_year": 2021,
        "cover_url": "/covers/kurkmantolumadonna.jpg",
        "description": "Her gün, daima öğleden sonra oraya gidiyor, koridorlardaki resimlere bakıyormuş gibi ağır ağır, fakat büyük bir sabırsızlıkla asıl hedefine varmak isteyen adımlarımı zorla zapt ederek geziniyor, rastgele gözüme çarpmış gibi önünde durduğum “Kürk Mantolu Madonna”yı seyre dalıyor, ta kapılar kapanıncaya kadar orada bekliyordum.” Kimi tutkular rehberimiz olur yaşam boyunca. Kollarıyla bizi sarar. Sorgulamadan peşlerinden gideriz ve hiç pişman olmayacağımızı biliriz. Yapıtlarında insanların görünmeyen yüzlerini ortaya çıkaran Sabahattin Ali, bu kitabında güçlü bir tutkunun resmini çiziyor. Düzenin sildiği kişiliklere, yaşamın uçuculuğuna ve aşkın olanaksızlığına (?) dair, yanıtlanması zor sorular soruyor.",
    },
    {
        "title": "Benim Adım Kırmızı",
        "authors": ["Orhan Pamuk"],
        "isbn": "9789754700862",
        "genre": "Tarihi Roman",
        "publisher": "Yapı Kredi Yayınları",
        "publish_year": 2022,
        "cover_url": "/covers/benimadimkirmizi.jpg",
        "description": "Orhan Pamuk’un “en renkli ve en iyimser romanım” dediği “Benim Adım Kırmızı”, 1591 yılında İstanbul’da karlı dokuz kış gününde geçiyor. İki küçük oğlu birbirleriyle sürekli çatışan güzel Şeküre, dört yıldır savaştan dönmeyen kocasının yerine kendine yeni bir koca, sevgili aramaya başlayınca, o sırada babasının tek tek eve çağırdığı saray nakkaşlarını saklandığı yerden seyreder. Eve gelen usta nakkaşlar, babasının denetimi altında Osmanlı Padişahı’nın gizlice yaptırttığı bir kitap için Frenk etkisi taşıyan tehlikeli resimler yapmaktadırlar. Aralarından biri öldürülünce, Şeküre’ye âşık, teyzesinin oğlu Kara devreye girer. İstanbul’da bir vaizin etrafında toplanmış, tekkelere karşı bir çevrenin baskıları, pahalılık ve korku hüküm sürerken, geceleri bir kahvede toplanan nakkaşlar ve hattatlar sivri dilli bir meddahın anlattığı hikâyelerle eğlenirler. Herkesin kendi sesiyle konuştuğu, ölülerin, eşyaların dillendiği, ölüm, sanat, aşk, evlilik ve mutluluk üzerine bu kitap, aynı zamanda eski resim sanatının unutulmuş güzelliklerine bir ağıt.",
    },
    {
        "title": "Sefiller",
        "authors": ["Victor Hugo"],
        "isbn": "9786052958155",
        "genre": "Dünya Klasikleri",
        "publisher": "İş Bankası Kültür Yayınları",
        "publish_year": 2018,
        "cover_url": "/covers/sefiller.jpg",
        "description": "Victor Hugo (1802-1885): Fransız edebiyatının gelmiş geçmiş en büyük yazarlarındandır. Şiirleri, oyunları ve romanları ile tanınır. Romantizm akımının Fransa’daki temsilcisidir. Edebiyat alanındaki devasa başarılarının yanında politik hayatta da etkin bir rol üstlendi; bu nedenle sürgün cezasına çarptırıldı, cezasını tamamlamasına rağmen İmparatorluk yıkılana dek Fransa’ya dönmedi. İlk kez 1862 yılında yayımlanan Sefiller yazarın Notre-Dame’ın Kamburu ile “din”, Deniz İşçileri ile “doğa” konularını işlediği roman üçlemesinin “toplum”u ele alan, en görkemli ayağıdır. Bu destansı roman Fransız toplumundan yola çıkarak, kozmolojik bir bakış ve eşsiz bir duyarlılıkla insanlığa ulaşır. Fantine’in, Cosette’in, Marius’ün, Saint-Denis Sokağı barikatlarının; Paris’in, Javert’in ve Jean Valjean’ın sefaletten sevgiye, felaketten iyiliğe ve karanlıktan aydınlığa uzanan hikâyeleri Hasan Âli Yücel Klasikler Dizisi’nin 250. kitabında okurlarla buluşuyor.",
    },
    {
        "title": "Hayvan Çiftligi",
        "authors": ["George Orwell"],
        "isbn": "9789750719387",
        "genre": "Politik Roman",
        "publisher": "Can Yayınları",
        "publish_year": 2023,
        "cover_url": "/covers/hayvanciftligi.jpg",
        "description": "İngiliz yazar George Orwell (1903-1950), ülkemizde daha çok 1984 adlı kitabıyla tanınır. Hayvan Çiftliği, onun çağdaş klasikler arasına girmiş ikinci ünlü yapıtıdır. Orwell, bu kitabında, hayvanların insanlara karşı başkaldırısını ve kendi yönetimlerini kurmalarını anlatır. Ancak zamanla, yeni liderleri Domuz Napoleon'un baskıcı rejimi altında, çiftlikteki hayvanlar eski durumlarından daha kötü bir hale gelirler. Hayvan Çiftliği, totaliter rejimlerin yükselişi ve yozlaşması üzerine keskin bir eleştiri sunar ve siyasi alegori olarak büyük bir etki yaratır.",
    },
    {
        "title": "Good Omens",
        "authors": ["Neil Gaiman", "Terry Pratchett"],
        "isbn": "9780060853983",
        "genre": "Fantastik",
        "publisher": "William Morrow",
        "publish_year": 2006,
        "cover_url": "/covers/goodomens.jpg",
        "description": "1655 yılında yazılmış ve şimdiye kadarki en doğru kehanet kitabı olan Cadı Agnes Çatlak’ın Dakîk ve Kat’î Kehanetleri’ne göre, cumartesi günü dünyanın sonu. Önümüzdeki Cumartesi. İyilik ve Kötülük orduları toplanıyorlar. Her şey Büyük Plan’a uygun ilerliyor gibi. Yalnız ufak bir pürüz var. Birazcık müşkülpesent bir melek ile sefahat düşkünü bir iblis yaklaşan bu coşku dolu anın gelişini hiç de iple çekmiyorlar. Ha unutmadan, birileri Deccal’ı yanlış yere göndermişe benziyor."
    },
    {
        "title": "1984",
        "authors": ["George Orwell"],
        "isbn": "9789750718533",
        "genre": "Distopya",
        "publisher": "Can Yayınları",
        "publish_year": 2021,
        "cover_url": FALLBACK_COVER,
        "description": "George Orwell’in kült kitabı Bin Dokuz Yüz Seksen Dört, yazarın geleceğe ilişkin bir kâbus senaryosudur. Bireyselliğin yok edildiği, zihnin kontrol altına alındığı, insanların makineleşmiş kitlelere dönüştürüldüğü totaliter bir dünya düzeni, romanda inanılmaz bir hayal gücüyle, en ince ayrıntısına kadar kurgulanmıştır. Geçmişte ve günümüzde dünya sahnesinde tezgâhlanan oyunlar düşünüldüğünde, ütopik olduğu kadar gerçekçi bir romandır Bin Dokuz Yüz Seksen Dört. Güncelliğini hiçbir zaman yitirmeyen bir başyapıttır; yalnızca yarına değil, bugüne de ilişkin bir uyarı çığlığıdır.",
    },
    {
        "title": "Dava",
        "authors": ["Franz Kafka"],
        "isbn": "9786053326748",
        "genre": "Klasik",
        "publisher": "İş Bankası Kültür Yayınları",
        "publish_year": 2020,
        "cover_url": FALLBACK_COVER,
        "description": "Dava yazılışından bir süre sonra dünya sahnesine çıkan, yurttaşlık haklarının askıya alındığı, bir sivil itaatsizlik imasının dahi zulümle karşılandığı totaliter rejimlere dair bir öngörü ve eleştiri olarak yorumlanır çoğunlukla. Nazi Almanya’sına dair bir “önsezi” barındırdığı söylenebilir belki. Erişilmez bir otorite tarafından yöneltilen ve ne olduğu hiçbir zaman açıklanmayan bir suçlamayla karşı karşıya kalan Josef K.’nın davasında, mahkemeye dinsel ya da metafizik bir otorite de atfedilebilir. Kafka Dava’da suçu yalnızca bir eylem olarak tanımlamayıp zanlının “kötü niyeti”yle de ilişkilendiren ve suçtan çok suçluya odaklanan absürd bir hukuk sistemi paradigması inşa eder. Kuramsal olarak ortada yasadışı bir eylem olmaksızın suçu mümkün kılan bir sistemdir bu. Ancak Kafka suç, sorumluluk ve özgürlük üzerine yazarken bir sistem ya da doktrin ortaya koymaz, çözüm önermez. Okuru ister istemez içine çeken bu karanlık dünya tasavvurunun tartışmaya açık olmayan tek bir özelliği varsa, o da müphemliğidir.",
    },
    {
        "title": "Dönüşüm",
        "authors": ["Franz Kafka"],
        "isbn": "9786053326755",
        "genre": "Klasik",
        "publisher": "İş Bankası Kültür Yayınları",
        "publish_year": 2019,
        "cover_url": "/covers/donusum.jpg",
        "description": "İlk kez 1915’te Die Weissen Blaetter adlı aylık dergide yayımlanan Dönüşüm, Kafka’nın en uzun ve en tanınmış öyküsüdür ve yayımlanmasının üzerinden nerdeyse bir asır geçmesine rağmen hâlâ tüm dünyada en çok okunan kitaplar arasındadır.",
    },
    {
        "title": "Simyacı",
        "authors": ["Paulo Coelho"],
        "isbn": "9789750726439",
        "genre": "Roman",
        "publisher": "Can Yayınları",
        "publish_year": 2017,
        "cover_url": FALLBACK_COVER,
        "description": "Simyacı, Brezilyalı eski şarkı sözü yazarı Paulo Coelho'nun, yayınlandığı 1988 yılından bu yana dünyayı birbirine katan, eleştirmenler tarafından bir `fenomen' olarak değerlendirilen üçüncü romanı. Simyacı, altı yılda kırk iki ülkede yedi milyondan fazla sattı. Bu, Gabriel Garcia Marquez'den bu yana görülmemiş bir olay. Yüreğinde, çocukluğunu yitirmemiş olan okurlar için bir `klasik' kimliği kazanan Simyacı'yı Saint-Exupery'nin Küçük Prens'i ve Richard Bach'ın Martı Jonathan Livingston'u ile karşılaştıranlar var (Publishers Weekly). Simyacı, İspanya'dan kalkıp Mısır Piramitlerinin eteklerinde hazinesini aramaya giden Endülüslü çoban Santiago'nun masalsı yaşamının felsefi öyküsü. Sanki bir `nasihatnâme': `Yazgına nasıl egemen olacaksın, mutluluğunu nasıl kuracaksın?' sorularına yanıt arayan bir hayat ve ahlak kılavuzu. Mistik bir peri masalına benzeyen romanın altı yılda, yedi milyondan fazla okur bulmasının gizi, kuşkusuz, onun bu kılavuzluk niteliğinden kaynaklanıyor. Simyacı'yı okumak, herkes daha uykudayken, güneşin doğuşunu seyretmek için şafak vakti uyanmaya benziyor.",
    },
    {
        "title": "Suç ve Ceza",
        "authors": ["Fyodor Dostoyevski"],
        "isbn": "9786053326779",
        "genre": "Klasik",
        "publisher": "İş Bankası Kültür Yayınları",
        "publish_year": 2022,
        "cover_url": FALLBACK_COVER,
        "description": "Fyodor Mihayloviç Dostoyevski (1821-1881): İlk romanı İnsancıklar 1846’da yayımlandı. Ünlü eleştirmen V. Byelinski bu eser üzerine Dostoyevski’den geleceğin büyük yazarı olarak söz etti. Ancak daha sonra yayımlanan öykü ve romanları, çağımızda edebiyat klasikleri arasında yer alsa da, o dönemde fazla ilgi görmedi. Yazar 1849’da I. Nikolay’ın baskıcı rejimine muhalif Petraşevski grubunun üyesi olduğu gerekçesiyle tutuklandı. Kurşuna dizilmek üzereyken cezası sürgün ve zorunlu askerliğe çevrildi. Cezasını tamamlayıp Sibirya’dan döndükten sonra Petersburg’da Vremya dergisini çıkarmaya başladı, yazdığı romanlarla tekrar eski ününe kavuştu. Suç ve Ceza Dostoyevski’nin bütün dünyada en çok okunan başyapıtıdır.",
    },
    {
        "title": "Yeraltından Notlar",
        "authors": ["Fyodor Dostoyevski"],
        "isbn": "9786053326762",
        "genre": "Klasik",
        "publisher": "İş Bankası Kültür Yayınları",
        "publish_year": 2018,
        "cover_url": "/covers/yeraltindannotlar.jpg",
        "description": "Fyodor Mihayloviç Dostoyevski (1821-1881): İlk romanı İnsancıklar’ın çarpıcı konusu ve farklı kurgusuyla dikkatleri çekti. İnsan ruhunun derinliklerini sergileyiş gücüyle önemli bir yazar olarak ün kazandı. Ancak daha sonra yayımlanan eserleri o dönemde fazla ilgi görmedi. Dostoyevski 1849’da  I.Nikolay’ın baskıcı rejimine muhalif Petraşevski grubunun üyesi olduğu gerekçesiyle tutuklandı. Kurşuna dizilmek üzereyken cezası sürgün ve zorunlu askerliğe çevrildi. Sibirya sürgününden sonra yazdığı romanlarla tekrar eski ününe kavuştu. 1864’de Vremya dergisinde yayımladığı Yeraltından Notlar gerçek dünyadan kendini soyutlamış bir kişinin iç çatışmalarını ve hezeyanlarını konu alır. Bu roman Dostoyevski’nin daha sonra yazacağı büyük romanların ipuçlarını taşımaktadır.",
    },
    {
        "title": "Şeker Portakalı",
        "authors": ["Jose Mauro de Vasconcelos"],
        "isbn": "9789750738609",
        "genre": "Roman",
        "publisher": "Can Çocuk Yayınları",
        "publish_year": 2021,
        "cover_url": "/covers/sekerportakali.jpg",
        "description": "Ne güzel bir şeker portakalı fidanıymış bu! Hem bak, dikeni de yok. Pek de kişilik sahibiymiş, şeker portakalı olduğu ta uzaktan belli. Ben senin boyunda olsaydım başka şey istemezdim. Ama ben büyük bir ağaç istiyordum. İyi düşün, Zezé. Henüz gencecik bir fidan bu. Bir gün koca bir ağaca dönüşecek. Seninle beraber büyüyecek. İki kardeş gibi iyi anlaşacaksınız. Dalını gördün mü? Bir tanecik dalı olsa da sanki özellikle senin binmen için hazırlanmış bir ata benziyor.Brezilya edebiyatının klasiklerinden Şeker Portakalı, José Mauro de Vasconcelos’un başyapıtı kabul edilir. Yetişkinler dünyasının sınırlamalarına hayal gücüyle meydan okuyan Zezé’nin yoksulluk, acı ve ümit dolu hikâyesi yazarın çocukluğundan derin izler taşır.Beş yaşındaki Zezé hemen her şeyi tek başına öğrenir: sadece bilye oynamayı ve arabalara asılmayı değil, okumayı ve sokak şarkıcılarının ezgilerini de. En yakın sırdaşıysa, anlattıklarına kulak veren ve Minguinho adını verdiği bir şeker portakalı fidanıdır…"

    },
    {
        "title": "Küçük Prens",
        "authors": ["Antoine de Saint-Exupery"],
        "isbn": "9789750719356",
        "genre": "Çocuk Klasikleri",
        "publisher": "Can Çocuk Yayınları",
        "publish_year": 2020,
        "cover_url": "/covers/kucukprens.jpg",
        "description": "Saint-Exupéry 1943’te Küçük Prens’i yayımladığında, dünya çapında muazzam bir başarı kazanacak bir yapıta imza attığını tahmin bile edemezdi. Bu bilgelikle dolu, büyüleyici masal aradan geçen onca yıla rağmen bütün dünyada her yaştan okurun yüreğini ısıtmaya devam ediyor. Uçağı Sahra çölüne düşen bir pilotun burada başka bir gezegenden gelen küçük prensle karşılaşması, biri doğa yasalarıyla yönetilen, diğeri hayal gücünün sınır tanımadığı iki farklı dünyanın karşı karşıya gelmesidir aslında. “Bana bir koyun çiz…” der küçük prens pilota. Hayatta anlaşılmayan olaylar karşısında onların gizemine boyun eğmekten başka çare yoktur. Yetişkin dünyasının kaygıları bir çocuğun gözüyle bakıldığında ne kadar da anlamsızdır. Sevgiye ve dostluğa dair bu küçük adamdan öğrenilecek ne çok şey vardır. Zira aslolan gözle görülmez, onu sadece kalp görebilir. Küçük prensin ziyaret ettiği gezegenlerde başından geçenler bizi bugün de insanlık durumu üzerine derin düşüncelere sevk eder.",
    },
    {
        "title": "Beyaz Diş",
        "authors": ["Jack London"],
        "isbn": "9786053608486",
        "genre": "Macera",
        "publisher": "İş Bankası Kültür Yayınları",
        "publish_year": 2017,
        "cover_url": "/covers/beyazdis.jpg",
        "description": "Jack London’ın Issız Diyarı, yabanı, buz kalpli Kuzey Toprakları’ndaki hayatı konu edindiği ikinci romanı Beyaz Diş’ tir. Vahşetin Çağrısı’ na kendini bırakmış bir annenin yavrusu Beyaz Diş’ in diyarıdır anlatılan. Onun hayranlık uyandırıcı zekâsı ve içgüdüleriyle kendini var edişinin ve “insan tanrılar” ın yaşamına geri dönüşünün enfes hikâyesi…",
    },
    {
        "title": "Martin Eden",
        "authors": ["Jack London"],
        "isbn": "9786052956175",
        "genre": "Roman",
        "publisher": "İş Bankası Kültür Yayınları",
        "publish_year": 2019,
        "cover_url": FALLBACK_COVER,
        "description": "Jack London’ın yarı otobiyografik romanı Martin Eden, 20. yüzyıl başında sosyal ve ideolojik meseleler ağırlıklı içeriğiyle Amerikan edebiyatında büyük ölçüde kabul görmüştür. London farklı sınıflar arasındaki zihniyet ve değer farklarını gözlerimizin önüne sererken, statü ve servetin Amerikan toplumundaki hayati önemine işaret eder. Romanın ana temalarından biri, başarı ve refah yolunun sosyal sınıf farkı gözetilmeksizin herkese açık olduğu şeklinde özetlenebilecek Amerikan Rüyası’dır. Ya da bu idealin yarattığı muazzam hayal kırıklığı…",
    },
    {
        "title": "Fareler ve İnsanlar",
        "authors": ["John Steinbeck"],
        "isbn": "9789750738602",
        "genre": "Roman",
        "publisher": "Sel Yayınları",
        "publish_year": 2018,
        "cover_url": "/covers/farelerveinsanlar.jpg",
        "description": "Fareler ve İnsanlar, insan doğasının kadim çıkmazlarına dair usta işi bir John Steinbeck kitabı.Birbirlerine hiç mi hiç benzemeyen iki arkadaşın; ufak tefek ve zeki George ile iriyarı ve aklı kıt Lennie’nin hikâyesini kaleme alıyor Steinbeck. Salinas Vadisi’ndeki bir çiftlikte güçbela iş bulan ikili hayallerini gerçekleştirme planları yapmaya başlar. Fakat küçük bir toprak parçası alıp çiftçilik yaparak kendi kendilerine yetme hayalleri, birkaç günde yaşanan olaylarla bir çıkmaz yola girer. Fareler ve İnsanlar, Büyük Bunalım döneminin binbir zorluğuyla mücadele eden tarım işçilerine doğrultulan bir dürbün, uzakları göz önüne getiren çarpıcı bir novella.",
    },
    {
        "title": "Gazap Üzümleri",
        "authors": ["John Steinbeck"],
        "isbn": "9789755705859",
        "genre": "Roman",
        "publisher": "Sel Yayınları",
        "publish_year": 2016,
        "cover_url": "/covers/gazapuzumleri.jpg",
        "description": "Bir cehennem kaç acıyla oluşur bu dünyada? Toz fırtınalarıyla tarladaki mahsulün mahvolması, Büyük Buhran’da bankaların topraklara el koyması ve sonunda, göçle gelen sefalet… Bir otomobili kamyona dönüştürerek çıktıkları mecburi yolculukta, acılarını ve açlıklarını, düşlerini ve öfkelerini de peşlerinden sürüklüyor Joad ailesi. Gazap Üzümleri, kaygı dolu günleri sessiz bir başkaldırıyla aşmaya çalışan insanların romanı.",
    },
    {
        "title": "Karamazov Kardeşler",
        "authors": ["Fyodor Dostoyevski"],
        "isbn": "9786053326786",
        "genre": "Klasik",
        "publisher": "İş Bankası Kültür Yayınları",
        "publish_year": 2021,
        "cover_url": "/covers/karamazov.jpg",
        "description": "Fyodor Mihayloviç Dostoyevski (1821-1881): İlk romanı İnsancıklar 1846’da yayımlandı. Ünlü eleştirmen V. Byelinski bu eser üzerine Dostoyevski’den geleceğin büyük yazarı olarak söz etti. Ancak daha sonra yayımlanan öykü ve romanları, çağımızda edebiyat klasikleri arasında yer alsa da, o dönemde fazla ilgi görmedi. Yazar 1849’da  I. Nikola’nın baskıcı rejimine muhalif Petraşevski grubunun üyesi olduğu gerekçesiyle tutuklandı. Kurşuna dizilmek üzereyken cezası sürgün ve zorunlu askerliğe çevrildi. Cezasını tamamlayıp Sibirya’dan döndükten sonra Petersburg’da Vremya dergisini çıkarmaya başladı, yazdığı romanlarla tekrar eski ününe kavuştu. Karamazov Kardeşler Dostoyevski’nin son başyapıtıdır.",
    },
    {
        "title": "Yüzüklerin Efendisi",
        "authors": ["J. R. R. Tolkien"],
        "isbn": "9789752733732",
        "genre": "Fantastik",
        "publisher": "Metis Yayinlari",
        "publish_year": 2019,
        "cover_url": FALLBACK_COVER,
        "description": "Dünya ikiye bölünmüştür, denir Tolkien'ın yapıtı söz konusu olduğunda: Yüzüklerin Efendisi'ni okumuş olanlar ve okuyacak olanlar. 1997 ile birlikte, çok sayıda Türk okur da 'okumuş olanlar' safına geçme fırsatı buldu. Kitabın türkçe basımı Yüzüklerin Efendisi'ne duyulan ilginin evrenselliğini kanıtladı",
    },
    {
        "title": "Hobbit",
        "authors": ["J. R. R. Tolkien"],
        "isbn": "9789753425988",
        "genre": "Fantastik",
        "publisher": "Ithaki Yayinlari",
        "publish_year": 2022,
        "cover_url": FALLBACK_COVER,
        "description": "Hobbit, tüm zamanların en sevilen yazarlarından J.R.R. Tolkien’in zihninden yayılan hikâyeler aracılığıyla elflerin, büyücülerin, cücelerin, ejderhaların, orkların ve Yüzüklerin Efendisi’yle Silmarillion’da tasvir edilen birçok diğer yaratığın evi olan büyüleyici Orta Dünya’nın kapısını açan unutulmaz bir klasik.",
    },
    {
        "title": "Harry Potter ve Felsefe Taşı",
        "authors": ["J. K. Rowling"],
        "isbn": "9789750802942",
        "genre": "Fantastik",
        "publisher": "Yapı Kredi Yayınları",
        "publish_year": 2016,
        "cover_url": "/covers/harrypotterfelsefetasi.jpg",
        "description": "Sıradan bir çocuk gibi yaşarken, kendini büyücülük dünyasının içinde bulan Harry Potter’ın maceralarının ilk bölümü, dünya yayıncılık tarihinde “en kısa sürede en çok satan kitap” unvanına sahip Harry Potter ve Felsefe Taşı, Ülkü Tamer’in çevirisiyle, Türkiye’de. J. K. Rowling’in Harry Potter ve Felsefe Taşı adlı kitabı, Yapı Kredi Yayınları’ndan çıktı. Harry Potter sıradan bir çocuk olduğunu sanırken, bir baykuşun getirdiği mektuplarla hayatı değişir: Başvurmadığı halde Hogwarts Cadılık ve Büyücülük Okulu’na kabul edilmiştir. Burada birbirinden ilginç dersler alır, iki arkadaşıyla birlikte maceradan maceraya koşar... ",
    },
    {
        "title": "Dune",
        "authors": ["Frank Herbert"],
        "isbn": "9786053754794",
        "genre": "Bilim Kurgu",
        "publisher": "Ithaki Yayinlari",
        "publish_year": 2021,
        "cover_url": FALLBACK_COVER,
        "description": "Dune, genç Paul Atreides’in hikâyesini anlatır. Atreides’in ailesi, evrendeki en önemli ve en değerli madde olan melanj ‘baharatının’ tek kaynağı olarak bilinen Arrakis gezegeninin kontrolünü kabul etmiştir.",
    },
    {
        "title": "Vakıf",
        "authors": ["Isaac Asimov"],
        "isbn": "9786052652459",
        "genre": "Bilim Kurgu",
        "publisher": "Ithaki Yayinlari",
        "publish_year": 2020,
        "cover_url": FALLBACK_COVER,
        "description": "Psikotarih biliminin öncüsü Hari Seldon'ın tahminlerine göre galaktik savaş kaçınılmazdı. Bu durumu olabildiğince ertelemek adına iki Vakıf kurdu; biri imparatorluğun sahip olduğu binlerce yıllık bilgiyi korumakla yükümlüydü, diğerinin ise ne yeri ne de amacı biliniyordu.",
    },
    {
        "title": "Fahrenheit 451",
        "authors": ["Ray Bradbury"],
        "isbn": "9786053757818",
        "genre": "Bilim Kurgu",
        "publisher": "Ithaki Yayinlari",
        "publish_year": 2019,
        "cover_url": "covers/451.jpg",
        "description": "Guy Montag bir itfaiyeciydi. Televizyonun hüküm sürdüğü bu dünyada kitaplar ise yok olmak üzereydi zira itfaiyeciler yangın söndürmek yerine ortalığı ateşe veriyordu. Montag’ın işi ise yasadışı olanların en tehlikelisini yakmaktı: Kitapları.",
    },
    {
        "title": "Satranç",
        "authors": ["Stefan Zweig"],
        "isbn": "9786053326809",
        "genre": "Novella",
        "publisher": "İş Bankası Kültür Yayınları",
        "publish_year": 2018,
        "cover_url": FALLBACK_COVER,
        "description": "Stefan Zweig’ın 1942’de intihar etmeden önce yazdığı son kurmaca metin olan Satranç, Nazi Almanyası’nı görgüsüz, “mizah duygusundan ve incelikten yoksun”, “yenilmez” şampiyonun kişiliğinde cisimleştirmesiyle de apayrı bir boyut kazanıyor.",
    },
    {
        "title": "Bilinmeyen Bir Kadinın Mektubu",
        "authors": ["Stefan Zweig"],
        "isbn": "9786053326816",
        "genre": "Novella",
        "publisher": "İş Bankası Kültür Yayınları",
        "publish_year": 2019,
        "cover_url": FALLBACK_COVER,
        "description": "Bilinmeyen Bir Kadının Mektubu ; Stefan Zweig’ın 1922 tarihli bu novellası, saplantılı aşk üzerine yazılmış en çarpıcı metinlerden biridir. Hayatı boyunca kendisinin farkında bile olmayan bir adamı umutsuzca sevmiş bir kadının yürek parçalayan aşk itirafıdır. Aşkının nesnesi olan kişi ise ömrü boyunca bir kez olsun söz ve eylemlerinin başkalarının hayatları üzerindeki etkisini düşünmemiştir.Zweig bu yapıtında insanların iç âlemlerine girmek ve onları gerçekten anlamak için toplum önündeki duruş ve davranışlarından yola çıkılamayacağına da dikkat çeker. Bu son derece tahripkâr karşılıksız aşkın hikâyesi, 1948 yılında Alman yönetmen Max Ophüls’ün imzasını taşıyan unutulmaz bir Hollywood klasiğine de ilham vermiştir.",
    },
]


SEMANTIC_ENRICHMENTS = {
    "9789753638029": {
        "original_language": "Türkçe",
        "translator": "",
        "series": "Türk Edebiyatı Modern Klasikler",
        "award": "",
        "keywords": ["modernleşme", "bürokrasi", "ironi"],
    },
    "9789754700114": {
        "original_language": "Türkçe",
        "translator": "",
        "series": "Çağdaş Türk Edebiyatı",
        "award": "TRT Roman Ödülü",
        "keywords": ["yabancılaşma", "modern birey", "postmodern roman"],
    },
    "9780060853983": {
        "original_language": "İngilizce",
        "translator": "",
        "series": "Modern Fantasy Classics",
        "award": "",
        "keywords": ["kıyamet", "fantastik", "mizah", "melek", "iblis"],
    },
    "9789750738609": {
        "original_language": "Portekizce",
        "translator": "Aydın Emeç",
        "series": "Çocuk ve Gençlik Klasikleri",
        "award": "",
        "keywords": ["çocukluk", "yoksulluk", "büyüme", "hayal gücü"],
    },
    "9789750719356": {
        "original_language": "Fransızca",
        "translator": "",
        "series": "Dünya Çocuk Klasikleri",
        "award": "",
        "keywords": ["felsefi masal", "dostluk", "sevgi", "gezegenler"],
    },
    "9786053757818": {
        "original_language": "İngilizce",
        "translator": "Dost Körpe",
        "series": "Bilimkurgu Klasikleri",
        "award": "",
        "keywords": ["sansür", "kitap", "distopya", "özgürlük"],
    },
    "9786053326762": {
        "original_language": "Rusça",
        "translator": "Mazlum Beyhan",
        "series": "Hasan Ali Yücel Klasikler Dizisi",
        "award": "",
        "keywords": ["iç monolog", "yeraltı insanı", "varoluş", "psikoloji"],
    },
}


SEMANTIC_ONLY_BOOKS = [
    {
        "title": "Sapiens",
        "authors": ["Yuval Noah Harari"],
        "isbn": "9780062316097",
        "genre": "Popüler Bilim",
        "publisher": "Harper",
        "publish_year": 2015,
        "cover_url": FALLBACK_COVER,
        "description": "İnsan türünün avcı-toplayıcı günlerinden günümüz teknolojik çağına kadar uzanan geniş tarihsel yolculuğunu yorumlayan etkili bir popüler bilim çalışması.",
        "original_language": "İngilizce",
        "translator": "",
        "series": "Big Ideas",
        "award": "",
        "keywords": ["tarih", "antropoloji", "medeniyet", "insanlık"],
    },
    {
        "title": "Homo Deus",
        "authors": ["Yuval Noah Harari"],
        "isbn": "9780062464316",
        "genre": "Popüler Bilim",
        "publisher": "Harper",
        "publish_year": 2017,
        "cover_url": FALLBACK_COVER,
        "description": "İnsanlığın geleceğini, yapay zekâyı, biyoteknolojiyi ve veri çağının etik sorunlarını tartışan düşünsel bir çalışma.",
        "original_language": "İngilizce",
        "translator": "",
        "series": "Big Ideas",
        "award": "",
        "keywords": ["gelecek", "yapay zeka", "teknoloji", "biyoteknoloji"],
    },
    {
        "title": "Bülbülü Öldürmek",
        "authors": ["Harper Lee"],
        "isbn": "9789750738524",
        "genre": "Dünya Klasikleri",
        "publisher": "Sel Yayıncılık",
        "publish_year": 2020,
        "cover_url": FALLBACK_COVER,
        "description": "Amerikan Güneyi'nde ırkçılık, adalet ve çocuk bakışı üzerinden toplum eleştirisi sunan modern klasik.",
        "original_language": "İngilizce",
        "translator": "Ülker İnce",
        "series": "Modern Klasikler",
        "award": "Pulitzer Prize",
        "keywords": ["adalet", "ırkçılık", "çocuk anlatıcı", "toplum"],
    },
    {
        "title": "Yüzyıllık Yalnızlık",
        "authors": ["Gabriel Garcia Marquez"],
        "isbn": "9789750738605",
        "genre": "Büyülü Gerçekçilik",
        "publisher": "Can Yayınları",
        "publish_year": 2022,
        "cover_url": FALLBACK_COVER,
        "description": "Buendia ailesinin kuşaklar boyunca süren hikâyesi üzerinden Latin Amerika tarihini büyülü gerçekçilikle anlatan başyapıt.",
        "original_language": "İspanyolca",
        "translator": "Seçkin Selvi",
        "series": "Dünya Edebiyatı",
        "award": "Nobel Prize linked author",
        "keywords": ["aile", "latin amerika", "mit", "büyülü gerçekçilik"],
    },
    {
        "title": "Körlük",
        "authors": ["Jose Saramago"],
        "isbn": "9789750738606",
        "genre": "Distopya",
        "publisher": "Kırmızı Kedi",
        "publish_year": 2021,
        "cover_url": FALLBACK_COVER,
        "description": "Toplumsal düzenin ani bir felaket karşısında nasıl çöktüğünü alegorik ve çarpıcı bir anlatımla işleyen roman.",
        "original_language": "Portekizce",
        "translator": "Işık Ergüden",
        "series": "Modern Dünya Edebiyatı",
        "award": "Nobel Prize linked author",
        "keywords": ["distopya", "toplum", "felaket", "ahlak"],
    },
    {
        "title": "Dublinliler",
        "authors": ["James Joyce"],
        "isbn": "9789750738607",
        "genre": "Öykü",
        "publisher": "İletişim Yayınları",
        "publish_year": 2019,
        "cover_url": FALLBACK_COVER,
        "description": "Dublin kent yaşamını, sıradan bireylerin iç dünyalarını ve modern hayatın sıkışmışlığını öyküler aracılığıyla anlatan eser.",
        "original_language": "İngilizce",
        "translator": "Murat Belge",
        "series": "Modern Klasikler",
        "award": "",
        "keywords": ["öykü", "şehir", "modernizm", "gündelik yaşam"],
    },
    {
        "title": "Karamazovlar",
        "authors": ["Fyodor Dostoyevski"],
        "isbn": "9789750738608",
        "genre": "Felsefi Roman",
        "publisher": "İş Bankası Kültür Yayınları",
        "publish_year": 2023,
        "cover_url": FALLBACK_COVER,
        "description": "İnanç, suç, ahlak ve aile çatışmalarını büyük bir anlatı içinde işleyen felsefi roman.",
        "original_language": "Rusça",
        "translator": "Ergin Altay",
        "series": "Hasan Ali Yücel Klasikler Dizisi",
        "award": "",
        "keywords": ["ahlak", "suç", "inanç", "aile"],
    },
    {
        "title": "Cesur Yeni Dünya",
        "authors": ["Aldous Huxley"],
        "isbn": "9789750738610",
        "genre": "Distopya",
        "publisher": "İthaki Yayınları",
        "publish_year": 2020,
        "cover_url": FALLBACK_COVER,
        "description": "Bireyselliğin tasarlanmış mutluluk düzeni içinde silindiği geleceği anlatan klasik distopya.",
        "original_language": "İngilizce",
        "translator": "Ümit Tosun",
        "series": "Bilimkurgu Klasikleri",
        "award": "",
        "keywords": ["distopya", "biyopolitika", "teknoloji", "toplum"],
    },
    {
        "title": "Zaman Makinesi",
        "authors": ["H. G. Wells"],
        "isbn": "9789750738612",
        "genre": "Bilim Kurgu",
        "publisher": "İş Bankası Kültür Yayınları",
        "publish_year": 2018,
        "cover_url": FALLBACK_COVER,
        "description": "Zaman yolculuğu fikrini edebiyat tarihinde ikonik hale getiren erken dönem bilimkurgu klasiği.",
        "original_language": "İngilizce",
        "translator": "Levent Cinemre",
        "series": "Hasan Ali Yücel Klasikler Dizisi",
        "award": "",
        "keywords": ["zaman yolculuğu", "bilimkurgu", "gelecek", "evrim"],
    },
    {
        "title": "Göçebe",
        "authors": ["Yaşar Kemal"],
        "isbn": "9789750738613",
        "genre": "Türk Edebiyatı",
        "publisher": "Yapı Kredi Yayınları",
        "publish_year": 2017,
        "cover_url": FALLBACK_COVER,
        "description": "Anadolu coğrafyasını ve insanını destansı anlatımıyla aktaran güçlü bir roman.",
        "original_language": "Türkçe",
        "translator": "",
        "series": "Türk Edebiyatı",
        "award": "",
        "keywords": ["anadolu", "toplum", "epik anlatı", "kırsal yaşam"],
    },
    {
        "title": "Bir Kış Gecesi Eğer Bir Yolcu",
        "authors": ["Italo Calvino"],
        "isbn": "9789750738614",
        "genre": "Postmodern Roman",
        "publisher": "YKY",
        "publish_year": 2016,
        "cover_url": FALLBACK_COVER,
        "description": "Okur ile metin ilişkisini oyunsu biçimde ele alan, anlatı üzerine kurulmuş deneysel roman.",
        "original_language": "İtalyanca",
        "translator": "Eren Yücesan Cendey",
        "series": "Dünya Edebiyatı",
        "award": "",
        "keywords": ["postmodernizm", "okur", "anlatı", "kurmaca"],
    },
]


def get_connection():
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def ensure_runtime_assets():
    if getattr(sys, "frozen", False) and not STATIC_DIR.exists():
        shutil.copytree(BUNDLED_STATIC_DIR, STATIC_DIR)

    if not OVERRIDES_PATH.exists():
        OVERRIDES_PATH.write_text(build_override_template(), encoding="utf-8")


def build_override_template():
    overrides = {}
    for book in SAMPLE_BOOKS:
        overrides[book["isbn"]] = {
            "title": book["title"],
            "cover_url": book["cover_url"],
        }

    return json.dumps(overrides, ensure_ascii=False, indent=2)


def load_book_overrides():
    if not OVERRIDES_PATH.exists():
        return {}

    try:
        overrides = json.loads(OVERRIDES_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}

    if not isinstance(overrides, dict):
        return {}

    normalized_overrides = {}
    for isbn, values in overrides.items():
        if not isinstance(values, dict):
            continue
        normalized_overrides[str(isbn)] = values
    return normalized_overrides


def apply_book_overrides(book, overrides):
    override = overrides.get(book["isbn"])
    if not override:
        return book

    merged_book = dict(book)
    for field in ("cover_url", "description", "title", "genre", "publisher", "publish_year"):
        value = override.get(field)
        if value not in (None, ""):
            merged_book[field] = value
    return merged_book


def ensure_schema(connection):
    connection.executescript(
        """
        CREATE TABLE IF NOT EXISTS books (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            isbn TEXT NOT NULL UNIQUE,
            genre TEXT NOT NULL,
            publisher TEXT NOT NULL,
            publish_year INTEGER NOT NULL,
            cover_url TEXT,
            description TEXT
        );

        CREATE TABLE IF NOT EXISTS authors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL UNIQUE
        );

        CREATE TABLE IF NOT EXISTS book_authors (
            book_id INTEGER NOT NULL,
            author_id INTEGER NOT NULL,
            PRIMARY KEY (book_id, author_id),
            FOREIGN KEY (book_id) REFERENCES books (id),
            FOREIGN KEY (author_id) REFERENCES authors (id)
        );
        """
    )

    columns = {
        row["name"]
        for row in connection.execute("PRAGMA table_info(books)").fetchall()
    }
    if "cover_url" not in columns:
        connection.execute("ALTER TABLE books ADD COLUMN cover_url TEXT")
    if "description" not in columns:
        connection.execute("ALTER TABLE books ADD COLUMN description TEXT")


def seed_books(connection):
    overrides = load_book_overrides()

    for sample_book in SAMPLE_BOOKS:
        book = apply_book_overrides(sample_book, overrides)
        existing_book = connection.execute(
            "SELECT id FROM books WHERE isbn = ?",
            (book["isbn"],),
        ).fetchone()

        if existing_book is None:
            cursor = connection.execute(
                """
                INSERT INTO books (title, isbn, genre, publisher, publish_year, cover_url, description)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    book["title"],
                    book["isbn"],
                    book["genre"],
                    book["publisher"],
                    book["publish_year"],
                    book["cover_url"],
                    book["description"],
                ),
            )
            book_id = cursor.lastrowid
        else:
            book_id = existing_book["id"]

        connection.execute(
            """
            UPDATE books
            SET title = ?, genre = ?, publisher = ?, publish_year = ?, cover_url = ?, description = ?
            WHERE isbn = ?
            """,
            (
                book["title"],
                book["genre"],
                book["publisher"],
                book["publish_year"],
                book["cover_url"],
                book["description"],
                book["isbn"],
            ),
        )

        for author_name in book["authors"]:
            connection.execute(
                "INSERT OR IGNORE INTO authors (full_name) VALUES (?)",
                (author_name,),
            )
            author_id = connection.execute(
                "SELECT id FROM authors WHERE full_name = ?",
                (author_name,),
            ).fetchone()["id"]
            connection.execute(
                "INSERT OR IGNORE INTO book_authors (book_id, author_id) VALUES (?, ?)",
                (book_id, author_id),
            )


def initialize_database():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    ensure_runtime_assets()
    with get_connection() as connection:
        ensure_schema(connection)
        seed_books(connection)


def row_to_book(connection, row):
    authors = connection.execute(
        """
        SELECT authors.full_name
        FROM authors
        INNER JOIN book_authors ON book_authors.author_id = authors.id
        WHERE book_authors.book_id = ?
        ORDER BY authors.full_name
        """,
        (row["id"],),
    ).fetchall()

    return {
        "title": row["title"],
        "isbn": row["isbn"],
        "genre": row["genre"],
        "publisher": row["publisher"],
        "publish_year": row["publish_year"],
        "cover_url": row["cover_url"] or FALLBACK_COVER,
        "description": row["description"] or "",
        "authors": [author["full_name"] for author in authors],
    }


def find_book_by_isbn(isbn):
    with get_connection() as connection:
        row = connection.execute("SELECT * FROM books WHERE isbn = ?", (isbn,)).fetchone()
        return None if row is None else row_to_book(connection, row)


def find_books_by_author(author_name):
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT DISTINCT books.*
            FROM books
            INNER JOIN book_authors ON book_authors.book_id = books.id
            INNER JOIN authors ON authors.id = book_authors.author_id
            WHERE LOWER(authors.full_name) LIKE LOWER(?)
            ORDER BY books.title
            """,
            (f"%{author_name}%",),
        ).fetchall()
        return [row_to_book(connection, row) for row in rows]


def find_books_by_genre(genre):
    with get_connection() as connection:
        rows = connection.execute(
            "SELECT * FROM books WHERE LOWER(genre) LIKE LOWER(?) ORDER BY title",
            (f"%{genre}%",),
        ).fetchall()
        return [row_to_book(connection, row) for row in rows]


def find_publisher_by_title(title):
    with get_connection() as connection:
        row = connection.execute(
            "SELECT * FROM books WHERE LOWER(title) LIKE LOWER(?) ORDER BY title LIMIT 1",
            (f"%{title}%",),
        ).fetchone()
        return None if row is None else row_to_book(connection, row)


# ========================= Semantic Web Services =========================

def semantic_uri(resource_type, value):
    return f"{BASE_URL}/semantic/{resource_type}/{quote(str(value).strip())}"


def escape_turtle(value):
    return (
        str(value)
        .replace("\\", "\\\\")
        .replace('"', '\\"')
        .replace("\n", "\\n")
    )


def book_to_jsonld(book):
    return {
        "@context": {
            "schema": "https://schema.org/",
            "ex": f"{BASE_URL}/semantic/ontology#",
            "name": "schema:name",
            "isbn": "schema:isbn",
            "author": "schema:author",
            "genre": "schema:genre",
            "publisher": "schema:publisher",
            "datePublished": "schema:datePublished",
            "description": "schema:description",
            "image": "schema:image",
            "inLanguage": "schema:inLanguage",
            "translator": "schema:translator",
            "isPartOf": "schema:isPartOf",
            "award": "schema:award",
            "keywords": "schema:keywords",
            "originalLanguage": "ex:originalLanguage",
            "Book": "schema:Book",
            "Person": "schema:Person",
            "Organization": "schema:Organization",
        },
        "@type": "Book",
        "@id": semantic_uri("books", book["isbn"]),
        "name": book["title"],
        "isbn": book["isbn"],
        "genre": book["genre"],
        "datePublished": str(book["publish_year"]),
        "description": book["description"],
        "image": f"{BASE_URL}{book['cover_url']}",
        "inLanguage": book["original_language"],
        "award": book["award"],
        "keywords": book["keywords"],
        "originalLanguage": book["original_language"],
        "author": [
            {
                "@type": "Person",
                "@id": semantic_uri("authors", author_name),
                "name": author_name,
            }
            for author_name in book["authors"]
        ],
        "publisher": {
            "@type": "Organization",
            "@id": semantic_uri("publishers", book["publisher"]),
            "name": book["publisher"],
        },
        "translator": (
            {
                "@type": "Person",
                "@id": semantic_uri("translators", book["translator"]),
                "name": book["translator"],
            }
            if book["translator"]
            else None
        ),
        "isPartOf": (
            {
                "@type": "CreativeWorkSeries",
                "@id": semantic_uri("series", book["series"]),
                "name": book["series"],
            }
            if book["series"]
            else None
        ),
    }


def collection_to_jsonld(collection_name, books, query_label, query_value):
    return {
        "@context": "https://schema.org",
        "@type": "Collection",
        "@id": semantic_uri("collections", collection_name),
        "name": collection_name,
        "description": f"{query_label}: {query_value}",
        "numberOfItems": len(books),
        "hasPart": [book_to_jsonld(book) for book in books],
    }


def books_to_turtle(books, collection_name=None, query_label=None, query_value=None):
    lines = [
        "@prefix schema: <https://schema.org/> .",
        f"@prefix ex: <{BASE_URL}/semantic/ontology#> .",
        "@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .",
        "",
    ]

    if collection_name:
        collection_uri = semantic_uri("collections", collection_name)
        lines.append(f"<{collection_uri}> a schema:Collection ;")
        lines.append(f'  schema:name "{escape_turtle(collection_name)}" ;')
        if query_label and query_value:
            lines.append(
                f'  schema:description "{escape_turtle(query_label)}: {escape_turtle(query_value)}" ;'
            )
        lines.append(f'  schema:numberOfItems "{len(books)}"^^xsd:integer .')
        lines.append("")

    for book in books:
        book_uri = semantic_uri("books", book["isbn"])
        author_uris = [semantic_uri("authors", author) for author in book["authors"]]
        publisher_uri = semantic_uri("publishers", book["publisher"])
        translator_uri = semantic_uri("translators", book["translator"]) if book["translator"] else ""
        series_uri = semantic_uri("series", book["series"]) if book["series"] else ""

        lines.append(f"<{book_uri}> a schema:Book ;")
        lines.append(f'  schema:name "{escape_turtle(book["title"])}" ;')
        lines.append(f'  schema:isbn "{escape_turtle(book["isbn"])}" ;')
        lines.append(f'  schema:genre "{escape_turtle(book["genre"])}" ;')
        lines.append(f'  schema:datePublished "{book["publish_year"]}"^^xsd:gYear ;')
        lines.append(f'  schema:description "{escape_turtle(book["description"])}" ;')
        lines.append(f'  schema:image "{escape_turtle(f"{BASE_URL}{book["cover_url"]}")}" ;')
        lines.append(f'  schema:inLanguage "{escape_turtle(book["original_language"])}" ;')
        if book["award"]:
            lines.append(f'  schema:award "{escape_turtle(book["award"])}" ;')
        if book["keywords"]:
            lines.append(f'  schema:keywords "{escape_turtle(", ".join(book["keywords"]))}" ;')
        lines.append(f'  ex:originalLanguage "{escape_turtle(book["original_language"])}" ;')

        for author_uri in author_uris[:-1]:
            lines.append(f"  schema:author <{author_uri}> ;")
        if author_uris:
            lines.append(f"  schema:author <{author_uris[-1]}> ;")
        if translator_uri:
            lines.append(f"  schema:translator <{translator_uri}> ;")
        if series_uri:
            lines.append(f"  schema:isPartOf <{series_uri}> ;")

        lines.append(f"  schema:publisher <{publisher_uri}> .")
        lines.append("")

        for author_name in book["authors"]:
            author_uri = semantic_uri("authors", author_name)
            lines.append(f"<{author_uri}> a schema:Person ;")
            lines.append(f'  schema:name "{escape_turtle(author_name)}" .')
            lines.append("")

        lines.append(f"<{publisher_uri}> a schema:Organization ;")
        lines.append(f'  schema:name "{escape_turtle(book["publisher"])}" .')
        lines.append("")

        if translator_uri:
            lines.append(f"<{translator_uri}> a schema:Person ;")
            lines.append(f'  schema:name "{escape_turtle(book["translator"])}" .')
            lines.append("")

        if series_uri:
            lines.append(f"<{series_uri}> a schema:CreativeWorkSeries ;")
            lines.append(f'  schema:name "{escape_turtle(book["series"])}" .')
            lines.append("")

    return "\n".join(lines)


def semantic_ontology_turtle():
    return "\n".join(
        [
            "@prefix ex: <http://127.0.0.1:8000/semantic/ontology#> .",
            "@prefix owl: <http://www.w3.org/2002/07/owl#> .",
            "@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .",
            "@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .",
            "@prefix schema: <https://schema.org/> .",
            "",
            "ex:BookServiceOntology a owl:Ontology ;",
            '  rdfs:label "Kitap Servisi Ontolojisi"@tr .',
            "",
            "schema:Book a owl:Class .",
            "schema:Person a owl:Class .",
            "schema:Organization a owl:Class .",
            "schema:Collection a owl:Class .",
            "",
            "schema:name a rdf:Property .",
            "schema:isbn a rdf:Property .",
            "schema:author a rdf:Property .",
            "schema:genre a rdf:Property .",
            "schema:publisher a rdf:Property .",
            "schema:datePublished a rdf:Property .",
            "schema:description a rdf:Property .",
            "schema:image a rdf:Property .",
            "schema:inLanguage a rdf:Property .",
            "schema:translator a rdf:Property .",
            "schema:isPartOf a rdf:Property .",
            "schema:award a rdf:Property .",
            "schema:keywords a rdf:Property .",
            "ex:originalLanguage a rdf:Property .",
        ]
    )


def semantic_source_books():
    overrides = load_book_overrides()
    books = [apply_book_overrides(book, overrides) for book in SAMPLE_BOOKS]
    books.extend(SEMANTIC_ONLY_BOOKS)
    enriched_books = []
    for book in books:
        semantic_book = dict(book)
        semantic_book.update(
            {
                "original_language": "",
                "translator": "",
                "series": "",
                "award": "",
                "keywords": [],
            }
        )
        semantic_book.update(book)
        semantic_book.update(SEMANTIC_ENRICHMENTS.get(book["isbn"], {}))
        enriched_books.append(semantic_book)
    return sorted(enriched_books, key=lambda item: item["title"])


def build_semantic_dataset():
    return collection_to_jsonld(
        "Semantic Kitap Veri Kumesi",
        semantic_source_books(),
        "Kaynak",
        "Dosya tabanli semantic veri",
    )


def ensure_semantic_dataset(force=False):
    SEMANTIC_DATA_DIR.mkdir(parents=True, exist_ok=True)
    if SEMANTIC_DATA_PATH.exists() and not force:
        return
    SEMANTIC_DATA_PATH.write_text(
        json.dumps(build_semantic_dataset(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def jsonld_node_to_book(node):
    publisher = node.get("publisher") or {}
    authors = node.get("author") or []
    image = node.get("image") or FALLBACK_COVER
    if isinstance(image, str) and image.startswith(BASE_URL):
        image = image.removeprefix(BASE_URL)

    normalized_authors = []
    for author in authors:
        if isinstance(author, dict):
            normalized_authors.append(author.get("name", ""))
        elif isinstance(author, str):
            normalized_authors.append(author)

    publish_year = node.get("datePublished", "")
    try:
        publish_year = int(str(publish_year).strip())
    except ValueError:
        publish_year = 0

    keywords = node.get("keywords", [])
    if isinstance(keywords, str):
        keywords = [item.strip() for item in keywords.split(",") if item.strip()]
    elif not isinstance(keywords, list):
        keywords = []

    return {
        "title": node.get("name", ""),
        "isbn": node.get("isbn", ""),
        "genre": node.get("genre", ""),
        "publisher": publisher.get("name", "") if isinstance(publisher, dict) else str(publisher),
        "publish_year": publish_year,
        "cover_url": image or FALLBACK_COVER,
        "description": node.get("description", ""),
        "original_language": node.get("originalLanguage", "") or node.get("inLanguage", ""),
        "translator": (
            node.get("translator", {}).get("name", "")
            if isinstance(node.get("translator"), dict)
            else ""
        ),
        "series": (
            node.get("isPartOf", {}).get("name", "")
            if isinstance(node.get("isPartOf"), dict)
            else ""
        ),
        "award": node.get("award", ""),
        "keywords": keywords,
        "authors": [author for author in normalized_authors if author],
    }


def load_semantic_books():
    ensure_semantic_dataset()

    try:
        payload = json.loads(SEMANTIC_DATA_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []

    items = payload.get("hasPart", [])
    if not isinstance(items, list):
        return []

    books = [jsonld_node_to_book(item) for item in items if isinstance(item, dict)]
    return sorted(books, key=lambda book: book["title"])


def contains_ignore_case(source, target):
    return target.casefold() in source.casefold()


def semantic_demo_queries():
    return {
        "classic_book_count": len(SAMPLE_BOOKS),
        "semantic_book_count": len(load_semantic_books()),
        "examples": [
            {
                "title": "Cevirmeni Aydin Emeç olan kitaplar",
                "endpoint": "/semantic/query?translator=Ayd%C4%B1n%20Eme%C3%A7",
            },
            {
                "title": "Bilimkurgu Klasikleri serisindeki kitaplar",
                "endpoint": "/semantic/query?series=Bilimkurgu%20Klasikleri",
            },
            {
                "title": "Pulitzer odullu eserler",
                "endpoint": "/semantic/query?award=Pulitzer",
            },
            {
                "title": "Mini SPARQL ile Portekizce aslindan cevrilmis kitaplar",
                "endpoint": "/semantic/sparql?query=SELECT%20*%20WHERE%20translator%20CONTAINS%20%22Eme%C3%A7%22%20AND%20original_language%20=%20%22Portekizce%22",
            },
            {
                "title": "Mini SPARQL ile Distopya turunde ilk iki kitap",
                "endpoint": "/semantic/sparql?query=SELECT%20*%20WHERE%20genre%20=%20%22Distopya%22%20LIMIT%202",
            },
        ],
    }


def get_semantic_format(query):
    requested = query.get("format", ["jsonld"])[0].strip().lower()
    return "turtle" if requested in {"ttl", "turtle"} else "jsonld"


def get_query_filter_value(query, key):
    return query.get(key, [""])[0].strip()


def build_semantic_filter_query(filters):
    sql = [
        """
        SELECT DISTINCT books.*
        FROM books
        LEFT JOIN book_authors ON book_authors.book_id = books.id
        LEFT JOIN authors ON authors.id = book_authors.author_id
        WHERE 1 = 1
        """
    ]
    parameters = []

    if filters["isbn"]:
        sql.append("AND books.isbn = ?")
        parameters.append(filters["isbn"])
    if filters["title"]:
        sql.append("AND LOWER(books.title) LIKE LOWER(?)")
        parameters.append(f"%{filters['title']}%")
    if filters["author"]:
        sql.append("AND LOWER(authors.full_name) LIKE LOWER(?)")
        parameters.append(f"%{filters['author']}%")
    if filters["genre"]:
        sql.append("AND LOWER(books.genre) LIKE LOWER(?)")
        parameters.append(f"%{filters['genre']}%")
    if filters["publisher"]:
        sql.append("AND LOWER(books.publisher) LIKE LOWER(?)")
        parameters.append(f"%{filters['publisher']}%")
    if filters["year"]:
        sql.append("AND books.publish_year = ?")
        parameters.append(filters["year"])

    sql.append("ORDER BY books.title")
    return "\n".join(sql), tuple(parameters)


def find_books_by_semantic_filters(filters):
    books = []
    for book in load_semantic_books():
        if filters["isbn"] and book["isbn"] != filters["isbn"]:
            continue
        if filters["title"] and not contains_ignore_case(book["title"], filters["title"]):
            continue
        if filters["author"] and not any(
            contains_ignore_case(author, filters["author"]) for author in book["authors"]
        ):
            continue
        if filters["genre"] and not contains_ignore_case(book["genre"], filters["genre"]):
            continue
        if filters["publisher"] and not contains_ignore_case(book["publisher"], filters["publisher"]):
            continue
        if filters["translator"] and not contains_ignore_case(book["translator"], filters["translator"]):
            continue
        if filters["original_language"] and not contains_ignore_case(book["original_language"], filters["original_language"]):
            continue
        if filters["series"] and not contains_ignore_case(book["series"], filters["series"]):
            continue
        if filters["award"] and not contains_ignore_case(book["award"], filters["award"]):
            continue
        if filters["year"] and str(book["publish_year"]) != str(filters["year"]):
            continue
        books.append(book)
    return books


def describe_semantic_query(filters):
    parts = []
    label_map = {
        "isbn": "ISBN",
        "title": "Baslik",
        "author": "Yazar",
        "genre": "Tur",
        "publisher": "Yayinevi",
        "translator": "Cevirmen",
        "original_language": "Orijinal Dil",
        "series": "Seri",
        "award": "Odul",
        "year": "Yil",
    }
    for key in ("isbn", "title", "author", "genre", "publisher", "translator", "original_language", "series", "award", "year"):
        if filters[key]:
            parts.append(f"{label_map[key]}={filters[key]}")
    return ", ".join(parts) if parts else "Tum kitaplar"


def parse_mini_sparql(query_text):
    if not query_text:
        raise ValueError("query parametresi zorunludur.")

    match = re.fullmatch(
        r"\s*SELECT\s+(?P<select>\*|\?book)\s+WHERE\s+(?P<where>.+?)(?:\s+LIMIT\s+(?P<limit>\d+))?\s*",
        query_text,
        re.IGNORECASE,
    )
    if not match:
        raise ValueError(
            'Gecerli mini SPARQL sozdizimi: SELECT * WHERE author = "..." AND genre = "..."'
        )

    where_part = match.group("where")
    clauses = re.split(r"\s+AND\s+", where_part, flags=re.IGNORECASE)
    if not clauses:
        raise ValueError("WHERE bolumu en az bir kosul icermelidir.")

    filters = {
        "isbn": "",
        "title": "",
        "author": "",
        "genre": "",
        "publisher": "",
        "translator": "",
        "original_language": "",
        "series": "",
        "award": "",
        "year": "",
    }
    operators = {}

    for clause in clauses:
        clause_match = re.fullmatch(
            r'\s*(isbn|title|author|genre|publisher|translator|original_language|series|award|year)\s*(=|CONTAINS)\s*"([^"]+)"\s*',
            clause,
            re.IGNORECASE,
        )
        if not clause_match:
            raise ValueError(
                'Desteklenen kosullar: author = "..." veya title CONTAINS "..."'
            )

        field = clause_match.group(1).lower()
        operator = clause_match.group(2).upper()
        value = clause_match.group(3).strip()

        if field in operators:
            raise ValueError(f"{field} alani sorguda yalnizca bir kez kullanilabilir.")
        if field in {"isbn", "year"} and operator != "=":
            raise ValueError(f"{field} alani yalnizca = operatoru ile kullanilabilir.")

        filters[field] = value
        operators[field] = operator

    limit = match.group("limit")
    return {
        "filters": filters,
        "operators": operators,
        "limit": None if limit is None else int(limit),
        "raw": query_text.strip(),
    }


def find_books_by_mini_sparql(parsed_query):
    filters = parsed_query["filters"]
    operators = parsed_query["operators"]
    results = []

    for book in load_semantic_books():
        matched = True
        for field in ("isbn", "title", "genre", "publisher", "translator", "original_language", "series", "award"):
            value = filters[field]
            if not value:
                continue
            operator = operators.get(field, "=")
            source = str(book[field])
            if operator == "=" and source.casefold() != value.casefold():
                matched = False
                break
            if operator == "CONTAINS" and not contains_ignore_case(source, value):
                matched = False
                break

        if not matched:
            continue

        if filters["author"]:
            operator = operators.get("author", "=")
            if operator == "=":
                if not any(author.casefold() == filters["author"].casefold() for author in book["authors"]):
                    continue
            elif not any(contains_ignore_case(author, filters["author"]) for author in book["authors"]):
                continue

        if filters["year"] and str(book["publish_year"]) != str(filters["year"]):
            continue

        results.append(book)

    if parsed_query["limit"] is not None:
        return results[: parsed_query["limit"]]
    return results


def build_semantic_payload(path, query):
    if path == "/semantic/ontology":
        return {
            "format": "turtle",
            "payload": semantic_ontology_turtle(),
            "status": HTTPStatus.OK,
        }

    if path == "/semantic/demo-queries":
        return {
            "format": "jsonld",
            "payload": semantic_demo_queries(),
            "status": HTTPStatus.OK,
        }

    if path == "/semantic/books":
        books = load_semantic_books()
        return semantic_collection_response(
            "Tum Kitaplar",
            books,
            "Kaynak",
            "Dosya tabanli semantic katalog",
            get_semantic_format(query),
        )

    if path == "/semantic/query":
        filters = {
            "isbn": get_query_filter_value(query, "isbn"),
            "title": get_query_filter_value(query, "title"),
            "author": get_query_filter_value(query, "author"),
            "genre": get_query_filter_value(query, "genre"),
            "publisher": get_query_filter_value(query, "publisher"),
            "translator": get_query_filter_value(query, "translator"),
            "original_language": get_query_filter_value(query, "original_language"),
            "series": get_query_filter_value(query, "series"),
            "award": get_query_filter_value(query, "award"),
            "year": get_query_filter_value(query, "year"),
        }
        if not any(filters.values()):
            return semantic_error(
                "En az bir semantic sorgu filtresi girilmelidir.",
                HTTPStatus.BAD_REQUEST,
            )

        books = find_books_by_semantic_filters(filters)
        query_description = describe_semantic_query(filters)
        return semantic_collection_response(
            f"Semantic Query - {query_description}",
            books,
            "Sorgu",
            query_description,
            get_semantic_format(query),
        )

    if path == "/semantic/sparql":
        try:
            parsed_query = parse_mini_sparql(get_query_filter_value(query, "query"))
        except ValueError as error:
            return semantic_error(str(error), HTTPStatus.BAD_REQUEST)

        books = find_books_by_mini_sparql(parsed_query)
        return semantic_collection_response(
            f"Mini SPARQL - {parsed_query['raw']}",
            books,
            "Mini SPARQL",
            parsed_query["raw"],
            get_semantic_format(query),
        )

    if path == "/semantic/books/by-isbn":
        isbn = query.get("isbn", [""])[0].strip()
        if not isbn:
            return semantic_error("isbn parametresi zorunludur.", HTTPStatus.BAD_REQUEST)
        book = next((book for book in load_semantic_books() if book["isbn"] == isbn), None)
        if not book:
            return semantic_error("Bu ISBN ile kitap bulunamadi.", HTTPStatus.NOT_FOUND)
        return semantic_single_book_response(book, get_semantic_format(query))

    if path == "/semantic/books/by-author":
        author = query.get("author", [""])[0].strip()
        if not author:
            return semantic_error("author parametresi zorunludur.", HTTPStatus.BAD_REQUEST)
        books = [
            book
            for book in load_semantic_books()
            if any(contains_ignore_case(author_name, author) for author_name in book["authors"])
        ]
        return semantic_collection_response(
            f"Yazar Sonucu - {author}",
            books,
            "Yazar",
            author,
            get_semantic_format(query),
        )

    if path == "/semantic/books/by-genre":
        genre = query.get("genre", [""])[0].strip()
        if not genre:
            return semantic_error("genre parametresi zorunludur.", HTTPStatus.BAD_REQUEST)
        books = [
            book for book in load_semantic_books() if contains_ignore_case(book["genre"], genre)
        ]
        return semantic_collection_response(
            f"Tur Sonucu - {genre}",
            books,
            "Tur",
            genre,
            get_semantic_format(query),
        )

    return None


def semantic_single_book_response(book, output_format):
    if output_format == "turtle":
        return {
            "format": "turtle",
            "payload": books_to_turtle([book]),
            "status": HTTPStatus.OK,
        }

    return {
        "format": "jsonld",
        "payload": book_to_jsonld(book),
        "status": HTTPStatus.OK,
    }


def semantic_collection_response(collection_name, books, query_label, query_value, output_format):
    if output_format == "turtle":
        return {
            "format": "turtle",
            "payload": books_to_turtle(books, collection_name, query_label, query_value),
            "status": HTTPStatus.OK,
        }

    return {
        "format": "jsonld",
        "payload": collection_to_jsonld(collection_name, books, query_label, query_value),
        "status": HTTPStatus.OK,
    }


def semantic_error(message, status):
    return {
        "format": "jsonld",
        "payload": {
            "@context": "https://schema.org",
            "@type": "Message",
            "text": message,
            "status": int(status),
        },
        "status": status,
    }


class BookServiceHandler(BaseHTTPRequestHandler):
    server_version = "BookService/1.0"

    def do_GET(self):
        parsed_url = urlparse(self.path)
        path = parsed_url.path
        query = parse_qs(parsed_url.query)

        if path == "/":
            self.serve_static("index.html", "text/html; charset=utf-8")
            return
        if path == "/styles.css":
            self.serve_static("styles.css", "text/css; charset=utf-8")
            return
        if path == "/favicon.ico":
            self.serve_static("favicon.ico", "image/x-icon")
            return
        if path == "/favicon-v2.ico":
            self.serve_static("favicon-v2.ico", "image/x-icon")
            return
        if path == "/texts.json":
            self.serve_static("texts.json", "application/json; charset=utf-8")
            return
        if path == "/app.js":
            self.serve_static("app.js", "application/javascript; charset=utf-8")
            return
        if path.startswith("/covers/"):
            self.serve_static(path.lstrip("/"), self.guess_content_type(path))
            return
        if path.startswith("/semantic/"):
            semantic_response = build_semantic_payload(path, query)
            if semantic_response is None:
                self.send_json({"error": "Istenen semantic kaynak bulunamadi."}, HTTPStatus.NOT_FOUND)
                return
            if semantic_response["format"] == "turtle":
                self.send_text(
                    semantic_response["payload"],
                    "text/turtle; charset=utf-8",
                    semantic_response["status"],
                )
                return
            self.send_json(semantic_response["payload"], semantic_response["status"], "application/ld+json; charset=utf-8")
            return

        if path == "/api/books/by-isbn":
            isbn = self.get_query_value(query, "isbn")
            if not isbn:
                self.send_json({"error": "isbn parametresi zorunludur."}, HTTPStatus.BAD_REQUEST)
                return
            book = find_book_by_isbn(isbn)
            if book is None:
                self.send_json({"error": "Bu ISBN ile kitap bulunamadi."}, HTTPStatus.NOT_FOUND)
                return
            self.send_json(book)
            return

        if path == "/api/books/by-author":
            author = self.get_query_value(query, "author")
            if not author:
                self.send_json({"error": "author parametresi zorunludur."}, HTTPStatus.BAD_REQUEST)
                return
            books = find_books_by_author(author)
            self.send_json({"author": author, "count": len(books), "books": books})
            return

        if path == "/api/books/by-genre":
            genre = self.get_query_value(query, "genre")
            if not genre:
                self.send_json({"error": "genre parametresi zorunludur."}, HTTPStatus.BAD_REQUEST)
                return
            books = find_books_by_genre(genre)
            self.send_json({"genre": genre, "count": len(books), "books": books})
            return

        if path == "/api/books/publisher-by-title":
            title = self.get_query_value(query, "title")
            if not title:
                self.send_json({"error": "title parametresi zorunludur."}, HTTPStatus.BAD_REQUEST)
                return
            book = find_publisher_by_title(title)
            if book is None:
                self.send_json({"error": "Bu ad ile kitap bulunamadi."}, HTTPStatus.NOT_FOUND)
                return
            self.send_json(book)
            return

        if path == "/api/books":
            with get_connection() as connection:
                rows = connection.execute("SELECT * FROM books ORDER BY title").fetchall()
                books = [row_to_book(connection, row) for row in rows]
            self.send_json({"count": len(books), "books": books})
            return

        self.send_json({"error": "Istenen kaynak bulunamadi."}, HTTPStatus.NOT_FOUND)

    def log_message(self, format, *args):
        return

    def get_query_value(self, query, key):
        values = query.get(key, [])
        return "" if not values else unquote(values[0]).strip()

    def serve_static(self, filename, content_type):
        file_path = STATIC_DIR / filename
        if not file_path.exists():
            self.send_json({"error": "Dosya bulunamadi."}, HTTPStatus.NOT_FOUND)
            return
        content = file_path.read_bytes()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def guess_content_type(self, path):
        content_type, _ = mimetypes.guess_type(path)
        if content_type:
            if content_type.startswith("text/") or content_type in {
                "application/javascript",
                "application/json",
                "image/svg+xml",
            }:
                return f"{content_type}; charset=utf-8"
            return content_type
        return "application/octet-stream"

    def send_text(self, payload, content_type, status=HTTPStatus.OK):
        content = payload.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def send_json(self, payload, status=HTTPStatus.OK, content_type="application/json; charset=utf-8"):
        content = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)


def run_server():
    initialize_database()
    ensure_semantic_dataset(force=True)
    host = "127.0.0.1"
    port = 8000
    server = ThreadingHTTPServer((host, port), BookServiceHandler)
    print(f"Sunucu hazir: http://{host}:{port}")
    server.serve_forever()


if __name__ == "__main__":
    run_server()

