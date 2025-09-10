# Barrel Monitor API - Automatizovaná testovací sada

Automatizované testy pro Barrel Monitor API sloužící ke správě měření nečistot v barelech s použitým kuchyňským olejem (UCO).

## Přehled

Tato testovací sada implementuje **enterprise-grade testování** pro Barrel Monitor API s pokročilými performance a load testing capabilities. Testy pokrývají:

- **Základní API operace**: CRUD operace pro barrels a measurements
- **Validace dat**: Kontrola povinných polí a datových typů
- **Hraniční případy**: Nevalidní data, neexistující ID, prázdné requesty
- **Integrační testy**: End-to-end workflow a konzistence dat
- **Výkonnostní testování**: Souběžnost, propustnost, analýza doby odezvy
- **Zátěžové testování**: Testování vysokého objemu, DDOS ochrana, rate limiting
- **Dávkové operace**: Testování s velkým množstvím dat (konfigurovatelné)
- **Pokročilé reportování**: HTML dashboardy, JSON reporty, benchmarking

## Struktura projektu

```
├── docker-compose.yml          # Docker orchestrace
├── Dockerfile                  # Python testovací prostředí
├── requirements.txt            # Python závislosti (including performance tools)
├── .python-version            # Python verze specifikace (3.11.13+)
├── .env.example               # Příklad konfigurace
├── config/                    # YAML konfigurace
│   ├── performance.yaml      # Nastavení výkonnostních testů
│   └── load_testing.yaml     # Scénáře zátěžových testů
├── tests/
│   ├── conftest.py           # Pytest konfigurace a fixtures
│   ├── test_barrels.py       # Základní barrel endpointy
│   ├── test_measurements.py  # Základní measurement endpointy
│   ├── test_integration.py   # Integrační testy
│   ├── performance/          # Výkonnostní testování
│   │   ├── test_concurrency.py      # Testování souběžných uživatelů
│   │   └── test_batch_operations.py # Dávkové operace
│   ├── load/                 # Zátěžové testování
│   │   └── test_rate_limiting.py    # DDOS/rate limiting testy
│   └── utils/
│       ├── api_client.py            # HTTP client wrapper
│       ├── test_data.py             # Factory pro testovací data
│       ├── config_loader.py         # YAML config loader
│       ├── performance_metrics.py   # Sběrač výkonnostních metrik
│       ├── performance_reporter.py  # Pokročilé reportování
│       └── benchmark_generator.py   # Generátor benchmark reportů
└── reports/                   # Výstupy testů (generované automaticky)
    ├── report.html           # Hlavní HTML report
    ├── report.json           # JSON report
    ├── assets/               # CSS styly pro HTML report
    ├── performance/          # Výkonnostní HTML/JSON reporty
    └── benchmarks/           # Benchmark comparison reporty
```

## Rychlé spuštění

### Docker (doporučeno)

1. **Kopírování konfigurace:**
   ```bash
   cp .env.example .env
   ```

2. **Spuštění všech testů:**
   ```bash
   docker-compose up api-tester
   ```

3. **Interaktivní spuštění:**
   ```bash
   docker-compose run --rm api-tester bash
   # V kontejneru pak:
   pytest -v
   ```

### Lokální spuštění

1. **Instalace závislostí:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Konfigurace prostředí:**
   ```bash
   export API_BASE_URL=https://to-barrel-monitor.azurewebsites.net
   ```

3. **Spuštění testů:**
   ```bash
   pytest -v --html=reports/report.html --json-report --json-report-file=reports/report.json
   ```

## Konfigurace

### YAML Konfigurace (doporučeno)

Projekt podporuje pokročilou YAML konfiguraci pro různé testovací scénáře:

```yaml
# config/performance.yaml
performance:
  batch_sizes: [1, 5, 10, 25, 50, 100]    # Kolik barelů vytvořit najednou
  concurrent_users: [1, 3, 5, 10, 20]     # Počet současných requestů
  test_duration: 300                       # Celková doba testování (sekundy)
  
# config/load_testing.yaml
ddos_protection:
  rate_limit_tests:
    - name: "burst_test"
      requests_per_second: 100
      duration: 10
```

### Environment proměnné

| Proměnná | Popis | Default |
|----------|-------|---------|
| `API_BASE_URL` | Base URL pro API | `https://to-barrel-monitor.azurewebsites.net` |
| `API_TIMEOUT` | Timeout pro HTTP requesty (s) | `30` |

### .env soubor

```bash
API_BASE_URL=https://to-barrel-monitor.azurewebsites.net
API_TIMEOUT=30
```

### Konfigurovatelné parametry

- **Batch sizes**: 1-100 barelů najednou
- **Concurrent users**: 1-50 současných uživatelů
- **Load testing**: Rate limiting, DDOS protection testy
- **Performance thresholds**: Configurable limits pro response time, error rate

## Testovací scénáře

### Základní API testy
- **POST /barrels** - Vytvoření barelu s validními/nevalidními daty
- **GET /barrels** - Získání seznamu barelů
- **GET /barrels/{id}** - Detail barelu, neexistující ID, nevalidní UUID
- **DELETE /barrels/{id}** - Smazání barelu, chybové případy
- **POST /measurements** - Vytvoření měření, validace dat, neexistující barrel
- **GET /measurements** - Seznam měření
- **GET /measurements/{id}** - Detail měření, chybové případy

### Výkonnostní testy
- **Testování souběžnosti** - 1-50 současných uživatelů
- **Dávkové operace** - 1-100 barelů najednou
- **Smíšené operace** - Kombinace create/read/delete operací
- **Trvalé zatížení** - Dlouhodobé zatížení

### Zátěžové testování a DDOS ochrana
- **Rate limiting** - Burst testy (100+ RPS)
- **Connection flooding** - Velké množství spojení
- **Detekce útočných vzorů** - Simulace útočných vzorů
- **Trvalé vysoké zatížení** - Dlouhodobé vysoké zatížení

### Integrační a dávkové testy
- **Kompletní životní cyklus** - End-to-end workflow
- **Dávkové vytváření barelů** - Hromadné vytváření barelů
- **Dávkové vytváření měření** - Hromadná měření
- **Smíšené dávkové operace** - Kombinované batch operace
- **Konzistence dat** - Konzistence při vysokém zatížení

## Generování benchmark reportů

Po spuštění výkonnostních testů můžete vygenerovat souhrnný benchmark report:

```bash
# V Docker kontejneru
docker-compose run --rm api-tester python -c "from tests.utils.benchmark_generator import BenchmarkGenerator; gen = BenchmarkGenerator(); gen.generate_benchmark_comparison()"
```

Tento příkaz:
- Načte všechny JSON reporty z `reports/performance/`
- Vytvoří souhrnné porovnání všech testů
- Vygeneruje HTML a JSON benchmark reporty v `reports/benchmarks/`
- Analyzuje trendy a identifikuje nejlepší/nejhorší výkonnost

## Výstupy testů a reporty

### Základní HTML/JSON reporty
- `reports/report.html` - Základní pytest HTML report s výsledky všech testů
- `reports/report.json` - JSON report pro CI/CD integrace
- `reports/assets/` - CSS styly a další zdroje pro HTML report

### Výkonnostní reporty
Pokročilé HTML a JSON reporty z výkonnostních testů:
- `reports/performance/rate_limiting_[test_name].html` - HTML dashboard pro rate limiting testy
- `reports/performance/rate_limiting_[test_name].json` - JSON data z rate limiting testů
- `reports/performance/batch_creation_report.html` - Report z batch testů (když běží)
- `reports/performance/concurrent_creation_[N]_users.html` - Report z concurrency testů
- Obsahuje: RPS grafy, analýzu doby odezvy, rozložení chyb, percentily

### Benchmark reporty
Porovnání výkonnosti napříč různými testovacími běhy:
- `reports/benchmarks/benchmark_comparison_[timestamp].json` - JSON s kompletním porovnáním
- `reports/benchmarks/benchmark_comparison_[timestamp].html` - HTML dashboard s trendy
- Analýza nejlepší/nejhorší výkonnosti
- Sledování trendů (improving/stable/degrading)
- Historické porovnání posledních 10 běhů každého testu

### Výkonnostní metriky
Detailní metriky pro každý test:
- **Percentily doby odezvy** (50., 90., 95., 99.)
- **Propustnost** (požadavky za sekundu)
- **Míry chybovosti** a kategorizace
- **Výkonnost souběžných uživatelů**
- **Efektivita dávkových operací**

### Logování
- Logování HTTP požadavků/odpovědí
- Sledování výkonnostních metrik v reálném čase
- Korelace a analýza chyb

## API Endpointy

### Barrels
- `POST /barrels` - Vytvoření barelu
- `GET /barrels` - Seznam barelů
- `GET /barrels/{id}` - Detail barelu  
- `DELETE /barrels/{id}` - Smazání barelu

### Measurements
- `POST /measurements` - Vytvoření měření
- `GET /measurements` - Seznam měření
- `GET /measurements/{id}` - Detail měření

## Data schémata

### Barrel
```json
{
  "id": "uuid (auto-generated)",
  "qr": "string (required, minLength: 1)", 
  "rfid": "string (required, minLength: 1)",
  "nfc": "string (required, minLength: 1)"
}
```

### Measurement
```json
{
  "id": "uuid (auto-generated)",
  "barrelId": "uuid (required)",
  "dirtLevel": "number (required)",
  "weight": "number (required)"
}
```

## Technické detaily

### Systémové požadavky
- **Python 3.11.13+** (doporučeno)
- **Docker & Docker Compose** (pro containerized běh)
- **4GB RAM minimum** (pro performance testy)

### Závislosti
- **pytest**: Testovací framework
- **requests**: HTTP knihovna  
- **python-dotenv**: Environment konfigurace
- **pytest-html**: HTML reporting
- **pytest-json-report**: JSON reporting
- **pyyaml**: YAML konfigurace
- **aiohttp**: Async HTTP pro concurrency testy
- **pytest-benchmark**: Performance benchmarking
- **locust**: Load testing framework

### Docker service
- **api-tester**: Spuštění testů s automatickým generováním reportů

### Test fixtures
- **api_client**: Session-wide API client
- **cleanup_barrels**: Automatické mazání testovacích dat
- **sample_barrel_id**: Předpřipravený testovací barel

## Troubleshooting

### Časté problémy

1. **Connection timeout**
   ```bash
   # Zvýšit timeout v .env
   API_TIMEOUT=60
   ```

2. **SSL chyby**
   ```bash
   # Přidat do requestsu verify=False (pouze pro development)
   ```

3. **Docker build issues**
   ```bash
   # Rebuild bez cache
   docker-compose build --no-cache
   ```

4. **Spuštění různých typů testů**
   ```bash
   # Základní funkční testy
   docker-compose run --rm api-tester pytest tests/test_barrels.py tests/test_measurements.py -v
   
   # Performance testy
   docker-compose run --rm api-tester pytest tests/performance/ -v
   
   # Load testing (opatrně - vysoké zatížení!)
   docker-compose run --rm api-tester pytest tests/load/ -v -s
   
   # Konkrétní test s batch operacemi
   docker-compose run --rm api-tester pytest tests/performance/test_batch_operations.py::TestBatchOperations::test_batch_barrel_creation -v -s
   ```

### Debug režim
```bash
# Spuštění s verbose loggingem
pytest -v -s --log-cli-level=DEBUG
```

## Další informace

- **API dokumentace**: https://to-barrel-monitor.azurewebsites.net/swagger/index.html
- **OpenAPI spec**: [swagger.json](swagger.json)
