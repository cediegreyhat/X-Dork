#!/usr/bin/env python3
import os
import re
import sys
import time
import threading
import sqlite3
import requests
from tqdm import tqdm
from queue import Queue
from urllib.parse import urlparse
from pathlib import Path
from fake_useragent import UserAgent

DB_LOCK = threading.Lock()

class Dorker:
    def __init__(self):
        self.cls()
        Path('logs').mkdir(exist_ok=True)
        Path('results').mkdir(exist_ok=True)

        self.concurrent = 50
        self.ua = UserAgent()
        self.colors = {
            'r': '\033[31m', 'g': '\033[32m', 'y': '\033[33m', 'b': '\033[34m',
            'm': '\033[35m', 'c': '\033[36m', 'w': '\033[37m', 'rr': '\033[39m'
        }

        self.domains = self.load_domains()
        try:
            self.dork_file = input(f"{self.colors['r']}    [+]{self.colors['c']} Enter Dork List: {self.colors['y']}")
            with open(self.dork_file, 'r') as f:
                self.dorks = [line.strip() for line in f if line.strip()]
        except Exception as e:
            print(f"{self.colors['r']}[-] {self.colors['c']}Error reading file: {e}")
            sys.exit(1)

        self.q = Queue()
        for _ in range(self.concurrent):
            t = threading.Thread(target=self.do_work)
            t.daemon = True
            t.start()

        for dork in self.dorks:
            self.q.put(dork)

        self.q.join()
        
    def print_banner():
    	banner = r"""
	__  __  ____             _             
	\ \/ / |  _ \ ___   ___| | _____ _ __ 
	 \  /  | | | / _ \ / __| |/ / _ \ '__|
	 /  \  | |_| | (_) | (__|   <  __/ |   
	/_/\_\ |____/ \___/ \___|_|\_\___|_|   

	        created by @cediegreyhat
	    """
	    print(banner)

	print_banner()

    def cls(self):
        os.system('cls' if os.name == 'nt' else 'clear')

    def load_domains(self):
        try:
            with open('tlds.txt') as f:
                return [line.strip() for line in f if line.strip()]
        except FileNotFoundError:
            print("[!] tlds.txt not found.")
            sys.exit(1)

    def cur_execute(self, data, args=()):
        with DB_LOCK:
            with sqlite3.connect("Database.sqlite3") as connection:
                cur = connection.cursor()
                cur.execute(data, args)
                connection.commit()

    def do_work(self):
        while True:
            dork = self.q.get()
            for domain in self.domains:
                for start in range(0, 501, 10):
                    url = f"https://www.bing.com/search?q={dork}+site:{domain}&first={start}&FORM=PORE"
                    headers = {'User-Agent': self.ua.random}
                    try:
                        response = requests.get(url, headers=headers, timeout=10)
                        matches = re.findall(r'<h2><a href="((?:https://|http://)[^"\s>]+)', response.text)
                        for match in matches:
                            parsed = urlparse(match)
                            clean_url = parsed.netloc.replace('www.', '')
                            if not any(x in clean_url for x in ['go.microsoft.com', 'wordpress.', 'blogspot.']):
                                try:
                                    self.cur_execute("INSERT INTO dorker_db(url) VALUES(?)", (clean_url,))
                                    print(f"{self.colors['c']}[+]{self.colors['y']} {clean_url} {self.colors['g']}--> ADDED")
                                except sqlite3.IntegrityError:
                                    print(f"{self.colors['c']}[+]{self.colors['y']} {clean_url} {self.colors['r']}--> DUPLICATE")
                    except requests.RequestException as e:
                        print(f"{self.colors['r']}[!] Request failed: {e}")
                        continue
            self.q.task_done()


class RowDatabase:
    def __init__(self):
        colors = {'c': '\033[36m', 'y': '\033[33m', 'g': '\033[32m'}
        with sqlite3.connect("Database.sqlite3") as conn:
            cur = conn.cursor()
            cur.execute("SELECT url FROM dorker_db")
            rows = cur.fetchall()

            with open('results/urls.txt', 'w') as f:
                for row in tqdm(rows, desc="[+] Exporting URLs"):
                    f.write(f"{row[0]}\n")

        print(f"{colors['c']}[+]{colors['y']} URLs saved to {colors['g']}results/urls.txt")


class ClearDatabase:
    def __init__(self):
        colors = {'c': '\033[36m', 'y': '\033[33m'}
        with sqlite3.connect("Database.sqlite3") as conn:
            cur = conn.cursor()
            try:
                cur.execute("DELETE FROM dorker_db")
                conn.commit()
                print(f"{colors['c']}[+]{colors['y']} Database cleared successfully.")
            except Exception as e:
                print(f"{colors['c']}[!] Failed to clear DB: {e}")


class Main:
    def __init__(self):
        self.menu()

    def menu(self):
        print("""
\033[36m      xDork - Search Engine Dorking Tool
\033[33m      1) Start Dorker
      2) Export Results
      3) Clear Database
      4) Exit\033[0m
        """)
        while True:
            choice = input("    @> ").strip()
            if choice == '1':
                Dorker()
            elif choice == '2':
                RowDatabase()
            elif choice == '3':
                ClearDatabase()
            elif choice == '4':
                sys.exit(0)
            else:
                print("[!] Invalid option.")


if __name__ == '__main__':
    with sqlite3.connect("Database.sqlite3") as conn:
        c = conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS dorker_db (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT UNIQUE
            )
        """)
        conn.commit()
    Main()

