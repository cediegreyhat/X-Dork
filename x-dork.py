#!/usr/bin/env python3
import os
import re
import sys
import threading
import sqlite3
import requests
import signal
from queue import Queue
from urllib.parse import urlparse
from pathlib import Path
from datetime import datetime

# CLI Colors
COLORS = {
    'r': '\033[31m', 'g': '\033[32m', 'y': '\033[33m', 'b': '\033[34m',
    'm': '\033[35m', 'c': '\033[36m', 'w': '\033[37m', 'rr': '\033[39m'
}

DB_LOCK = threading.Lock()
LOG_FILE = "logs/x-dork.log"

def log(msg, level="INFO"):
    """Enhanced logging to file and terminal."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{now}] [{level}] {msg}"
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")
    # Print to terminal if not DEBUG
    if level != "DEBUG":
        print(line)

def print_banner():
    print(f"""{COLORS['c']}
      .---.        .-----------
     /     \\  __  /    ------
    / /     \\(  )/    -----
   //////   ' \\/ `   ---
  //// / // :    : ---
 // /   /  /`    '--
          //..\\
=========((====))=======================
//   \\\\   \\\\  //   \\\\
      {COLORS['y']}xDork v1.0 - Machine Spirit Awakened!{COLORS['c']}
            {COLORS['g']}by @cediegreyhat{COLORS['c']}
========================================
{COLORS['rr']}""")

def graceful_exit(signum=None, frame=None):
    print(f"\n{COLORS['r']}[!] Exiting gracefully. Goodbye!{COLORS['rr']}")
    log("Graceful exit requested by user.", "INFO")
    sys.exit(0)

signal.signal(signal.SIGINT, graceful_exit)
signal.signal(signal.SIGTERM, graceful_exit)

class Dorker:
    def __init__(self):
        self.colors = COLORS
        self.cls()
        print_banner()
        Path('logs').mkdir(exist_ok=True)
        Path('results').mkdir(exist_ok=True)
        self.concurrent = self.ask_concurrent()
        self.q = Queue(self.concurrent * 2)
        self.domains = [
            'com', 'net', 'org', 'biz', 'gov', 'mil', 'edu', 'info', 'int', 'tel',
            'name', 'aero', 'asia', 'cat', 'coop', 'jobs', 'mobi', 'museum', 'pro', 'travel'
        ]
        self.header = {'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/117.0'}
        self.dorklist = self.ask_dorklist()
        self.results_count = 0
        self.threads = []

        for i in range(self.concurrent):
            t = threading.Thread(target=self.do_work, daemon=True)
            t.start()
            self.threads.append(t)

        try:
            with open(self.dorklist, 'r') as f:
                for dork in f:
                    if dork.strip():
                        self.q.put(dork.strip())
            self.q.join()
        except Exception as e:
            log(f"[!] Error reading dork list: {e}", "ERROR")
            print(self.colors['r'] + '[!] Error reading dork list: ' + str(e) + self.colors['rr'])
            sys.exit()

        print(f"\n{self.colors['g']}[+] Dorking complete! {self.results_count} unique URLs added.{self.colors['rr']}")
        log(f"Dorking complete! {self.results_count} unique URLs added.", "INFO")

    def ask_concurrent(self):
        while True:
            try:
                val = input(f"{self.colors['b']}    [+]{self.colors['c']} Threads (default 50): {self.colors['y']}")
                if not val.strip():
                    return 50
                val = int(val)
                if val < 1 or val > 200:
                    print(f"{self.colors['r']}[!] Please enter a value between 1 and 200.{self.colors['rr']}")
                    continue
                return val
            except ValueError:
                print(f"{self.colors['r']}[!] Invalid input. Please enter a number.{self.colors['rr']}")

    def ask_dorklist(self):
        while True:
            dorklist = input(self.colors['r'] + '    [+]' + self.colors['c'] + ' Enter Dork List: ' + self.colors['y'])
            if not dorklist.strip():
                print(self.colors['r'] + '[!] Please provide a dork list file.' + self.colors['rr'])
                continue
            if not os.path.isfile(dorklist):
                print(self.colors['r'] + '[!] File not found.' + self.colors['rr'])
                continue
            return dorklist

    def cls(self):
        os.system('cls' if os.name == 'nt' else 'clear')

    def cur_execute(self, data, args=()):
        with DB_LOCK:
            with sqlite3.connect("Database.sqlite3") as connection:
                cur = connection.cursor()
                cur.execute(data, args)
                connection.commit()

    def do_work(self):
        try:
            while True:
                dork = self.q.get()
                log(f"Scanning dork: {dork}", "INFO")
                found_any = False
                for domain in self.domains:
                    for start in range(0, 501, 10):
                        url = f"https://www.bing.com/search?q={dork} site:{domain}&first={start}&FORM=PORE"
                        try:
                            resp = requests.get(url, headers=self.header, timeout=10)
                            finder = re.findall(
                                r'<h2><a href="((?:https://|http://)[a-zA-Z0-9\-_.]+\.[a-zA-Z]{2,11}[^"\s>]*)',
                                resp.text)
                            if not finder:
                                continue
                            for found_url in finder:
                                clean_url = found_url
                                if clean_url.startswith('http://'):
                                    clean_url = clean_url.replace('http://', '')
                                elif clean_url.startswith('https://'):
                                    clean_url = clean_url.replace('https://', '')
                                if clean_url.startswith('www.'):
                                    clean_url = clean_url.replace('www.', '')
                                if any(x in clean_url for x in ['go.microsoft.com', '.wordpress.', '.blogspot.']):
                                    continue
                                try:
                                    self.cur_execute("INSERT INTO dorker_db(url) VALUES(?)", (clean_url,))
                                    msg = f"{clean_url} --> ADDED TO Database"
                                    print(self.colors['c'] + '       [' + self.colors['y'] + '+' + self.colors['c'] + '] ' +
                                          self.colors['y'] + clean_url + self.colors['g'] + ' --> ADDED TO Database' + self.colors['rr'])
                                    log(msg, "SUCCESS")
                                    self.results_count += 1
                                    found_any = True
                                except sqlite3.IntegrityError:
                                    msg = f"{clean_url} --> Was in Database"
                                    print(self.colors['c'] + '       [' + self.colors['y'] + '+' + colors['c'] + '] ' +
                                          self.colors['y'] + clean_url + self.colors['r'] + ' --> Was in Database' + self.colors['rr'])
                                    log(msg, "INFO")
                                    found_any = True
                        except Exception as e:
                            log(f"[!] Request failed: {e}", "ERROR")
                            print(self.colors['r'] + '[!] Request failed: ' + str(e) + self.colors['rr'])
                        # Give the terminal a chance to update and avoid hammering
                        import time
                        time.sleep(0.1)
                if not found_any:
                    msg = f"No results found for dork: {dork}"
                    print(self.colors['y'] + f"[!] No results found for dork: {dork}" + self.colors['rr'])
                    log(msg, "WARNING")
                self.q.task_done()
        except Exception as e:
            log(f"[!] Thread error: {e}", "ERROR")
            print(self.colors['r'] + '[!] Thread error: ' + str(e) + self.colors['rr'])

class RowDatabase:
    def __init__(self):
        colors = COLORS
        with sqlite3.connect("Database.sqlite3") as conn:
            cur = conn.cursor()
            cur.execute("SELECT url FROM dorker_db")
            rows = cur.fetchall()
            if not rows:
                print(colors['r'] + '[!] No URLs found in the database.' + colors['rr'])
                log("No URLs found in the database.", "WARNING")
                return
            Path('results').mkdir(exist_ok=True)
            with open('results/urls.txt', 'w') as f:
                for row in rows:
                    f.write(row[0] + '\n')
        print(colors['c'] + '       [' + colors['y'] + '+' + colors['c'] + '] ' +
              colors['y'] + 'Saved In' + colors['g'] + ' results/urls.txt' + colors['rr'])
        log("Exported URLs to results/urls.txt", "INFO")

class ClearDatabase:
    def __init__(self):
        colors = COLORS
        with sqlite3.connect("Database.sqlite3") as conn:
            cur = conn.cursor()
            try:
                cur.execute("DELETE FROM dorker_db")
                conn.commit()
                print(colors['c'] + '       [' + colors['y'] + '+' + colors['c'] + '] ' +
                      colors['y'] + 'Successfully Cleared DataBase!' + colors['rr'])
                log("Successfully Cleared DataBase!", "INFO")
            except Exception as e:
                print(colors['c'] + '       [' + colors['y'] + '+' + colors['c'] + '] ' +
                      colors['y'] + 'cant delete Rows! ' + str(e) + colors['rr'])
                log(f"Failed to clear database: {e}", "ERROR")
                sys.exit()

class Main:
    def __init__(self):
        self.colors = COLORS
        self.menu()

    def menu(self):
        while True:
            self.cls()
            print_banner()
            print(self.colors['y'] + '        [1] ' + self.colors['c'] + ' Dork Scanner')
            print(self.colors['y'] + '        [2] ' + self.colors['c'] + ' Export Results')
            print(self.colors['y'] + '        [3] ' + self.colors['c'] + ' Clear Database')
            print(self.colors['y'] + '        [4]' + self.colors['c'] + ' Exit')
            choice = input('    @> ').strip()
            if choice == '1':
                self.cls()
                print_banner()
                try:
                    Dorker()
                except KeyboardInterrupt:
                    graceful_exit()
                input(self.colors['b'] + '[Press Enter to return to menu]' + self.colors['rr'])
            elif choice == '2':
                self.cls()
                print_banner()
                RowDatabase()
                input(self.colors['b'] + '[Press Enter to return to menu]' + self.colors['rr'])
            elif choice == '3':
                self.cls()
                print_banner()
                ClearDatabase()
                input(self.colors['b'] + '[Press Enter to return to menu]' + self.colors['rr'])
            elif choice == '4':
                print(self.colors['c'] + '[+] Exiting. Have a nice day!' + self.colors['rr'])
                log("User exited the program.", "INFO")
                sys.exit(0)
            else:
                print(self.colors['c'] + '[' + self.colors['r'] + '-' + self.colors['c'] + '] ' +
                      self.colors['w'] + str(choice) + ' Command Not Found!' + self.colors['rr'])
                input(self.colors['b'] + '[Press Enter to try again]' + self.colors['rr'])

    def cls(self):
        os.system('cls' if os.name == 'nt' else 'clear')

if __name__ == '__main__':
    Path('logs').mkdir(exist_ok=True)
    with sqlite3.connect("Database.sqlite3") as conn:
        c = conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS dorker_db (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT UNIQUE
            )
        """)
        conn.commit()
    log("xDork started.", "INFO")
    Main()

