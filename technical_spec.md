# SaaS-platforma monitoringa i PR-analitiki

## 1. Cel produkta

Razrabotat oblachnuyu SaaS-platformu dlya monitoringa, analiza i ocenki publikaciy v onlayn-SMI, socialnyh setyah, Telegram-kanalah, novostnyh portalax, blogah, forumah i otzovikah.

Sistema prednaznachena dlya PR-otdelov, marketologov, SMM-specialistov, press-sluzhb i analitikov, kotorym nuzhno:

- otslezhivat upominaniya kompaniy, brendov, person, konkurentov i klyuchevyh slov;
- analizirovat tonalnost, ohvat, dinamiku, geografiyu i vovlechennost;
- ocenivat effektivnost PR-aktivnostey i infopovodov;
- formirovat otchety, dashbordy i avtomaticheskie uvelomleniya.

## 2. Rynochniy orientir

V kachestve funkcionalnogo orientira rassmatrivaetsya klass sistem, podobnyh Medialogii: monitoring SMI i socsetey, real-time analitika, ocenki effektivnosti kommunikaciy, indeksi citiruemosti, uvelomleniya i otchetnost.

Na sayte Medialogii ukazany sleduyushchie znachimye benchmarki:

- monitoring SMI i socialnyh setey dlya ocenki effektivnosti kommunikaciy;
- produkty dlya PR, SM, analiza citiruemosti i reagirovaniya v socmedia;
- pokrytie bolee 110 000 SMI;
- obrabotka do 100 mln soobshcheniy v sutki;
- metriky: vliyatelnost SMI, tonalnost, citiruemost, glavnaia rol, perepechatki, zametnost, vovlechennost, potencialniy ohvat;
- real-time analitika i uvelomleniya v Telegram, email, push.

Istochniki:

- https://www.mlg.ru/
- https://www.mlg.ru/products/pr/
- https://www.mlg.ru/about/

## 3. Polzovateli i roli

### Administrator

- upravlyaet organizaciyami, polzovatelyami, rolyami i tarifami;
- nastroyivaet istochniki, prioritety, slovari, integracii i limity;
- vidit sistemnye metriky i zhurnal oshibok.

### Analitik

- sozdaet i nastroyivaet proekty monitoringa;
- rabotaet s lentoy upominaniy, filtrami, razmetkoy tonalnosti;
- sobiraet dashbordy i otchety;
- korrektiruet klassifikaciyu i tonalnost dlya doobucheniya modeley.

### Nablyudatel

- prosmatrivaet dashbordy, lenty i gotovye otchety;
- poluchaet uvelomleniya;
- ne mozhet menyat istochniki, modeli i kriticheskie nastroiki.

## 4. Osnovnye moduli

### 4.1. Sbor dannyh

Sistema dolzhna podderzhivat sbor iz istochnikov:

- novostnye sayty i RSS;
- onlayn-SMI;
- VK;
- Telegram-kanaly;
- X / Twitter API;
- YouTube;
- forumi;
- blogi;
- otzoviki;
- ruchno dobavlennye URL.

Funkcii:

- raspisanie parsinga: 15-30 minut dlya vysokogo prioriteta, 1-6 chasov dlya srednego, 12-24 chasa dlya nizkogo;
- ochered zadaniy s prioritetami istochnikov;
- hranenie syrogo HTML / JSON otveta;
- hranenie strukturirovannogo kontenta: zagolovok, tekst, data, avtor, istochnik, ssylka, media, layki, reposty, kommentarii, prosmotry;
- deduplikaciya na etape sbora;
- ruchnoe dobavlenie istochnika po URL;
- monitoring statusa istochnikov: posledniy uspeh, oshibki, chastota, srednee vremya otveta.

Vazhno: trebovanie "obhod kapchi" nuzhno oformit bez narusheniya pravil istochnikov. Rekomenduemaya realizaciya:

- v pervuyu ochered ispolzovat oficialnye API, RSS, dogovornye feedy i razreshennye metody dostupa;
- pri kapche stavit istochnik v ochered proveryki ili zaprashivat ruchnoe podtverzhdenie;
- rotaciyu User-Agent ispolzovat dlya sovmestimosti i ustoychivosti, s soblyudeniem robots.txt, ToS i chastotnyh limitov;
- vesty audit dostupov i blokirovok.

### 4.2. Normalizaciya i obogashchenie

Pipeline obrabotki publikacii:

1. Izvlechenie teksta iz HTML / API-otveta.
2. Ochistka boilerplate-blokov, menyu, reklamnyh fragmentov.
3. Opredelenie yazyka.
4. Tokenizaciya, lemmatizaciya / stemming.
5. Izvlechenie imenovannyh sushchnostey:
   - ORG: organizacii;
   - PER: persony;
   - LOC: lokacii.
6. Izvlechenie klyuchevyh fraz i hashtagov.
7. Opredelenie geografi publikacii po istochniku, tekstu i metadannym.
8. Privozka k teme monitoringa.
9. Raschet metrik.

### 4.3. Klassifikaciya i analiz

Sistema dolzhna vypolnyat:

- sentiment-analiz: pozitivnyy, negativnyy, neytralnyy;
- ruchnuyu korrektirovku tonalnosti s zapisyu v training dataset;
- tematicheskuyu klassifikaciyu: tehnologii, finansy, sport, politika, ekonomika, kultura, kriza, reputaciya i drugie rubriki;
- poisk dublikatov i pohozhih publikaciy;
- vydelenie pervoistochnika i perepechatok;
- opredelenie glavnosti upominaniya: glavnaya rol ili epizod;
- opredelenie nalichiya pryamoy rechi;
- opredelenie informpovodov i ih dinamiki.

### 4.4. Metriki publikacii

Dlya kazhdoy publikacii rasschityvat:

- IC: indeks citirovaniya istochnika;
- PO: potencialnyy ohvat;
- TIC / PageRank istochnika;
- vovlechennost: layki, reposty, kommentarii, prosmotry, dinamika;
- tonalnost;
- ves istochnika;
- tip istochnika;
- geografia;
- zametnost materiala;
- koefficient perepechatok;
- rol obekta v publikacii;
- svyaz s PR-aktivnostyu ili infopovodom.

### 4.5. Dashbord

Glavnyy ekran dolzhen soderzhat:

- grafik upominaniy po vremeni;
- raspredelenie tonalnosti;
- dinamiku negativnyh upominaniy;
- top istochnikov;
- top avtorov;
- top tem i infopovodov;
- karta geografii;
- lenta poslednih upominaniy;
- blok alertov: vspysk negativa, novyy viralnyy material, upominanie VIP-persony;
- sravnenie s konkurentami;
- summary po periodu: vsego upominaniy, ohvat, dolya negativa, vovlechennost, Media Score.

### 4.6. Poisk i monitoring

Funkcii:

- gibkiy poisk po publikaciyam;
- filtry: period, tonalnost, istochnik, tip istochnika, geografia, avtor, IC, PO, tema, proekt, yazyk, teg;
- sohranennye poiski;
- lenta upominaniy v realnom vremeni;
- eksporter vybrannyh publikaciy.

Yazyk zaprosov dlya tem monitoringa:

- AND / I;
- OR / ILI;
- NOT / NET;
- kavichki dlya tochnoy frazy;
- gruppirovka skobkami;
- minus-slova;
- sinonimy i aliasy brenda;
- otdelnye slovari dlya konkurentov, produktov, person i kampaniy.

Primer:

```text
("Brand X" OR "Brend Iks" OR brandx) AND (zapusk OR reliz OR prezentaciya) NOT vakansiya
```

### 4.7. Otchetnost

Sistema dolzhna podderzhivat:

- shablony: ezhednevnyy, ezhenedelnyy, ezhemesyachnyy, kampaniynyy, krizisnyy;
- eksport v PDF, PPTX, XLSX / CSV;
- avtomaticheskuyu otpravku na email po raspisaniyu;
- podderzhku logotipa klienta i firmennogo stilya;
- nastroiku sostava blokov otcheta.

Na osnove primerov otchetov nuzhno razdelit otchetnost na 2 urovnya:

- executive dashboard: pervyy ekran dlya rukovoditelya s KPI, vyvodami, riskami i rekomendaciyami;
- analytical appendix: detalnye tablitsy po dinamike, tonalnosti, istochnikam, regionam, avtoram, slovam i infopovodam.

Uluchshennyy otchet dolzhen ne prosto vygruzhat tablitsy, a otvechat na voprosy:

- chto proizoshlo za period;
- kakoy obekt lideriruet po obemu i MediaIndex;
- gde est pozitiv / negativ / otsutstvie prisutstviya;
- kakoy infopovod stal glavnoy prichinoy dinamiki;
- kakie istochniki i avtory dali naibolshiy vklad;
- kakie deystviya rekomendovany PR-komande.

Primer struktury ezhenedelnogo PR-otcheta:

1. Executive summary.
2. Kluchyevye vyvody.
3. Dinamika upominaniy.
4. Tonalnost po dnyam.
5. Top infopovodov.
6. Top istochnikov i avtorov.
7. Geografiya upominaniy.
8. Sravnenie s konkurentami.
9. Negativnye publikacii i rekomendacii po reagirovaniyu.
10. Effektivnost PR-aktivnostey.
11. Prilozhenie: spisok publikaciy.

Vizualizacii:

- line chart;
- bar chart;
- pie / donut chart;
- stacked chart po tonalnosti;
- heat map;
- tag cloud;
- karta regionov;
- tablitsy publikaciy;
- reytingi istochnikov.

### 4.8. Uvelomleniya

Kanaly:

- email;
- web-push;
- Telegram;
- webhook dlya CRM / BI / helpdesk.

Triggery:

- rezkiy rost negativa;
- upominanie klyuchevogo slova;
- upominanie persony;
- publikaciya v istochnike visokogo prioriteta;
- viralnyy rost vovlechennosti;
- padenie dostupnosti vazhnogo istochnika;
- novyy informpovod u konkurenta.

### 4.9. Administrirovanie

Funkcii:

- upravlenie polzovatelyami i rolyami;
- organizacii i multi-tenant dostupy;
- slovari: stop-slova, tonalnost, sinonimy, kategorii, geografia;
- upravlenie istochnikami;
- prioritety istochnikov;
- nastroyka kvot po tarifu;
- zhurnal deystviy;
- audit izmeneniy tonalnosti i klassifikacii;
- nastroyka integraciy.

## 5. Predlagaemaya arhitektura

### Frontend

- Web SPA: React / Next.js.
- UI: dashbordy, lenty, poisk, otchety, admin-panel.
- Grafiki: Apache ECharts, Recharts ili Highcharts.
- Real-time lenta: WebSocket / Server-Sent Events.

### Backend

- API Gateway.
- Auth service: organizacii, polzovateli, roli, JWT / OAuth2.
- Monitoring Projects service.
- Sources service.
- Crawling service.
- Parsing service.
- Enrichment / NLP service.
- Search service.
- Analytics service.
- Reports service.
- Notification service.
- Admin / Audit service.

### Data layer

- PostgreSQL: osnovnye biznes-sushchnosti.
- ClickHouse: sobytiya, metrika, agregacii, analitika po bolshim obemam.
- OpenSearch / Elasticsearch: polnotekstovyy poisk i filtry.
- S3-compatible storage: syroy HTML, JSON, media, gotovye PDF/PPTX.
- Redis: kesh, rate limits, loki, ocheredi malogo obema.
- Kafka / Redpanda: potok publikaciy i sobytiy obrabotki.

### ML / NLP

- Otelnyy service dlya inference.
- Model registry.
- Training dataset iz ruchnyh korrektirovok.
- Batch retraining po raspisaniyu.
- A/B sravnenie modeley.

## 6. Bazovaya model dannyh

### Organization

- id;
- name;
- plan;
- limits;
- created_at.

### User

- id;
- organization_id;
- name;
- email;
- role;
- status;
- last_login_at.

### MonitoringProject

- id;
- organization_id;
- name;
- query;
- dictionaries;
- competitors;
- status;
- created_by;
- created_at.

### Source

- id;
- name;
- url;
- type;
- priority;
- language;
- geography;
- crawl_interval;
- status;
- authority_score;
- audience;
- last_crawled_at.

### Publication

- id;
- source_id;
- original_url;
- canonical_url;
- title;
- text;
- published_at;
- collected_at;
- author;
- language;
- geography;
- raw_object_url;
- hash;
- duplicate_group_id;
- status.

### Mention

- id;
- publication_id;
- project_id;
- entity;
- entity_type;
- sentiment;
- sentiment_confidence;
- role;
- category;
- reach;
- citation_index;
- engagement_score;
- created_at.

### Report

- id;
- organization_id;
- project_id;
- template;
- period_from;
- period_to;
- status;
- file_url;
- scheduled_at;
- created_by.

## 7. API MVP

```http
POST /api/auth/login
GET  /api/me

GET  /api/projects
POST /api/projects
GET  /api/projects/{id}
PATCH /api/projects/{id}

GET  /api/sources
POST /api/sources
PATCH /api/sources/{id}

GET  /api/mentions
GET  /api/mentions/{id}
PATCH /api/mentions/{id}/sentiment

GET  /api/analytics/overview
GET  /api/analytics/timeseries
GET  /api/analytics/sentiment
GET  /api/analytics/sources
GET  /api/analytics/geography

POST /api/reports
GET  /api/reports
GET  /api/reports/{id}/download

GET  /api/notifications/rules
POST /api/notifications/rules
```

## 8. MVP

### Vhodit v pervuyu versiyu

- multi-tenant kabinet;
- roli: Admin, Analitik, Nablyudatel;
- sozdanie proektov monitoringa;
- bazovyy query builder s AND / OR / NOT;
- RSS i nabor web-istochnikov;
- Telegram-kanaly pri nalichii dopustimogo sposoba sbora;
- hranenie syrogo i strukturirovannogo kontenta;
- polnotekstovyy poisk;
- lenta upominaniy;
- tonalnost s ruchnoy korrektirovkoy;
- NER: organizacii, persony, lokacii;
- deduplikaciya;
- osnovnoy dashbord;
- PDF-otchet po shablonu;
- email-uvelomleniya.

### Ne vhodit v MVP, no nuzhno zaplanirovat

- polnyy ML retraining contour;
- slozhnye mediaindeksy i sobstvennye reytingi istochnikov;
- PPTX-generator;
- heat maps i prodvinutaya geografia;
- integracii s BI;
- avtomaticheskoe sravnenie PR-kampaniy;
- SSO;
- marketplace connectorov.

## 9. Kriticheskie nefunkcionalnye trebovaniya

- Masshtabiruemost: gorizontalnoe masshtabirovanie crawlerov, parsers i NLP-workerov.
- Nadezhnost: povtornye popytki, dead-letter queue, audit obrabotki.
- Proizvoditelnost: poisk po upominaniyam do 2 sekund na standartnyh filtrah.
- Aktualnost: vysokoprioritetnye istochniki obnovlyat s zaderzhkoy do 15-30 minut.
- Bezopasnost: razdelenie tenantov, RBAC, shifrovanie sekretov, audit deystviy.
- Sootvetstvie zakonodatelstvu: obrabotka personalnyh dannyh, hranenie soglasiy, soblyudenie pravil istochnikov.
- Nabliudaemost: metriky, logi, tracing, dashboard po pipeline.

## 10. Etapy razrabotki

### Etap 1. Discovery i proektirovanie

- utverdit Figma-makety;
- opisat use cases;
- soglasovat istochniki i prioritety;
- opisat metody sbora po kazhdomu tipu istochnika;
- sformirovat backlog MVP;
- utverdit metriky i formuly.

### Etap 2. Platform core

- auth, organizacii, roli;
- proekty monitoringa;
- istochniki;
- ochered zadaniy;
- hranenie publikaciy;
- audit.

### Etap 3. Collection pipeline

- RSS crawler;
- web parser;
- Telegram connector;
- normalizaciya kontenta;
- raw storage;
- statusy i oshibki istochnikov.

### Etap 4. Search and analytics

- full-text index;
- filtry;
- deduplikaciya;
- bazovye agregacii;
- dashbord.

### Etap 5. NLP

- language detection;
- lemmatizaciya;
- NER;
- sentiment;
- kategorii;
- ruchnaya korrektirovka.

### Etap 6. Reports and notifications

- PDF-generator;
- shablony;
- raspisanie otpravki;
- email / Telegram / web-push alerts.

### Etap 7. Hardening

- nagruzochnoe testirovanie;
- bezopasnost;
- monitoring;
- optimizaciya stoimosti hraneniya;
- dokumentaciya API i admin-processov.

## 11. Kriterii priemki MVP

- Polzovatel mozhet sozdat proekt monitoringa s logicheskim zaprosom.
- Sistema sobiraet publikacii iz nastroennyh istochnikov po raspisaniyu.
- Dlya kazhdoy publikacii hranitsya syroy original i strukturirovannaya versiya.
- Lenta upominaniy obnovlyaetsya bez ruchnogo importa.
- Poisk rabotaet po tekstu, periodu, istochniku, tonalnosti i proektu.
- Dashboard pokazyvaet dinamiku upominaniy, tonalnost, top istochnikov i poslednie publikacii.
- Analitik mozhet izmenit tonalnost i eto popadaet v audit.
- Sistema formiruet PDF-otchet za vybrannyy period.
- Sistema otpravlyaet uvelomlenie pri vspyske negativa.
- Dostupy razdeleny po rolyam i organizaciyam.

## 12. Otkrytye voprosy

- Kakoy planiruemyi obem dannyh na starte: publikaciy v sutki, istochnikov, organizaciy?
- Nuzhna li polnaya zamena Medialogii ili vnutrenniy instrument s chastyu funkcionala?
- Kakie istochniki yavlyayutsya kritichnymi dlya MVP?
- Budut li kupleny licenzii / API-dostupy k socialnym setyam i novostnym bazam?
- Kakie yazyki nuzhno podderzhivat v pervoy versii?
- Nuzhny li on-premise instalacii ili tolko cloud?
- Kakie tochnye formuly IC, PO, TIC i Media Score dolzhny ispolzovatsya?
- Nuzhen li import istoricheskih publikaciy?
- Kakoy format otchetov iz primerov Yandex.Disk yavlyaetsya osnovnym: PDF, PPTX ili Excel?
