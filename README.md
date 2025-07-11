# xDork

Welcome to **xDork** – my personal, nonsense, CLI dorking tool for bug bounty, OSINT, and general web reconnaissance.

---

## What is this?

xDork is a multi-threaded, SQLite-backed search engine dorker. Feed it a list of Google/Bing dorks, and it’ll shotgun them across a bunch of TLDs, scraping and storing unique domains it finds. It’s fast, colorful, and logs everything for you.

---


## Quickstart

1. **Install dependencies**  
   You only need Python 3 and `requests`:
   ```bash
   pip install requests
   ```

2. **Prepare your dork list**  
   Make a `dorks.txt` file, one dork per line.  
   Example:
   ```
   inurl:admin
   intitle:index.of
   ext:sql | ext:db
   ```

3. **Run it**
   ```bash
   python x-dork.py
   ```

4. **Menu**
   ```
   [1] Dork Scanner      # Start scanning with your dork list
   [2] Export Results    # Dump all unique URLs to results/urls.txt
   [3] Clear Database    # Nuke the DB if you want to start fresh
   [4] Exit              # Self-explanatory
   ```

5. **Follow the prompts**
   - Enter your dork list file path.
   - Choose thread count (default is 50, which is plenty).
   - Watch the results roll in.

---

## Output

- **results/urls.txt**: All unique domains found (after you export).
- **logs/x-dork.log**: Every action, error, and result is logged here.

---

## Real Talk

- This is for legal, authorized testing only. Don’t be a jerk.
- If you hammer Bing/Google too hard, you’ll get CAPTCHAs or temp bans. Use responsibly.
- No warranty, no support, but PRs and issues are welcome.

---

## Menu Screen

```
╔════════════════════════════════════════════════════════════════════╗
║   xDork - Search Engine Dorking Tool v2.0  |  Release the Dragon!║
║                by @cediegreyhat                                  ║
╚════════════════════════════════════════════════════════════════════╝
[1] Dork Scanner
[2] Export Results
[3] Clear Database
[4] Exit
```

---

Happy hunting. 🕵️‍♂️
