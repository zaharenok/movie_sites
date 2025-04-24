# Movie Sites Scraper

A Python-based web scraper that discovers and catalogs free online streaming sites (movies, series, anime, etc.) by querying search engines and filtering results. Designed as a hands-on portfolio project demonstrating:

- **Asynchronous browsing** with [Playwright](https://playwright.dev/python/)  
- **Proxy/VPN integration** via SOCKS5 (Outline VPN & PySocks)  
- **Domain validation** and filtering logic for streaming vs. excluded/adult sites  
- **Data persistence** in JSON & CSV formats  
- **Resource management**: automatic closing of idle browser tabs  

---

## 🚀 Features

- **Multi-regional search**  
  Queries Google, Bing, Yahoo and more with geolocation set to India by default.

- **Dynamic tab management**  
  Limits simultaneous tabs, auto-closes oldest or idle tabs to conserve resources.

- **Custom query list**  
  Generates localized queries (English, Hindi, Spanish, Portuguese, etc.) and “similar to” searches for known target domains.

- **Filtering pipeline**  
  - Excludes common sites (Google, YouTube, social networks, big streaming platforms)  
  - Detects adult/porn domains via keyword matching  
  - Validates potential streaming sites via keyword heuristics and TLD checks

- **Resilient scraping**  
  - Retries on network timeouts  
  - Graceful shutdown on `KeyboardInterrupt`, saving current results

- **Output**  
  - `movie_sites.json`: list of discovered domains  
  - `movie_sites.csv`: with discovery date & category for easy import into analytics tools  

---

## 📋 Prerequisites

- **Ubuntu / Debian** server (or similar Linux) with Python 3.8  
- Installed system packages:
  ```bash
  sudo apt update
  sudo apt install python3.8 python3.8-venv python3.8-distutils git
  ```
- (Optional) Docker, if you prefer containerized deployment  

---

## 🔧 Installation & Setup

1. **Clone the repo**  
   ```bash
   git clone https://github.com/your-username/movie_sites.git
   cd movie_sites
   ```

2. **Create & activate a virtual environment**  
   ```bash
   python3.8 -m venv venv
   source venv/bin/activate
   ```

3. **Install Python dependencies**  
   ```bash
   pip install --upgrade pip setuptools wheel
   pip install -r requirements.txt
   ```

4. **Outline VPN (SOCKS5) configuration**  
   - Edit the `outline_vpn` dictionary in `movie_sites_scraper_v2.py` with your server, port, method and password.  
   - Run:
     ```bash
     python -c "import socks; print('PySocks imported OK')"
     ```

---

## ▶️ Usage

Start the scraper with:

```bash
python movie_sites_scraper_v2.py
```

By default, it will:

1. Wait 10 seconds (`initial_delay`)  
2. Launch a visible Chromium browser  
3. Loop through all search queries (shuffled) for the “India” region  
4. Save new domains to `movie_sites.json` and `movie_sites.csv` after each discovery  
5. Close and report stats on exit (Ctrl+C)

---

## ⚙️ Configuration

All core settings live in the `MovieSitesScraper.__init__`:

- **`max_results`**: stop after N domains found  
- **`max_tabs`** / **`tab_timeout`**: control tab concurrency & idle cleanup  
- **`search_queries`**: list of search terms (add/remove locales or sites)  
- **`excluded_domains`**: domains to skip (e.g. Google, YouTube)  
- **`target_domains`**: seeds for “similar to” searches  
- **`search_engines`**: list of base URLs to rotate  

---

## 🗂️ Output Files

- **`movie_sites.json`**  
  ```json
  [
    "site1.example.com",
    "site2.example.org",
    ...
  ]
  ```
- **`movie_sites.csv`**  
  | domain               | date_found | category  |
  |----------------------|------------|-----------|
  | site1.example.com    | 2025-04-24 | streaming |
  | site2.example.org    | 2025-04-24 | streaming |
  | …                    | …          | …         |

---

## 💡 Extending & Deployment

- **Systemd service**: configure `/etc/systemd/system/movie_sites.service` for auto-restart  
- **Docker**: add a `Dockerfile` wrapping Python 3.8 & Playwright, build & run on any host  
- **Scheduling**: use cron or an automation tool to run daily/weekly and accumulate new findings  

---

## 📜 License & Contact

This project is released under the MIT License.  
Questions or feedback? Feel free to open an issue or contact `olegzakharchenko@gmail.com`.  
