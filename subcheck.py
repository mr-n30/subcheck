#!/usr/bin/env python3
import os
import sys
import difflib
import argparse
import psycopg2
from termcolor import colored

parser = argparse.ArgumentParser(description="Request a URL")
parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose mode")
parser.add_argument("-d", "--domain", type=str, help="Domain to check", required=True)
args = parser.parse_args()

domain = args.domain
verbose = args.verbose

def connect():
    conn      = None
    domains   = []
    try:
        conn = psycopg2.connect(
            host="crt.sh",
            database="certwatch",
            user="guest",
            password=""
        )

        if verbose:
            print(colored("[+] Connecting to the database...", "blue"))
        cur = conn.cursor()
        conn.set_session(readonly=True, autocommit=True)
        cur.execute("SELECT ci.NAME_VALUE NAME_VALUE FROM certificate_identity ci WHERE ci.NAME_TYPE = 'dNSName' AND reverse(lower(ci.NAME_VALUE)) LIKE reverse(lower('%.tesla.com'));")
        for x in cur:
            domains.append(x)
        domains = list(dict.fromkeys(domains))
        domains.sort()
        cur.close()

    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
        sys.exit(1)

    finally:
        if conn is not None:
            conn.close()
        if verbose:
            print(colored("[+] Database connection closed...", "blue"))
        return domains

def main():
    old = []
    new = []
    domains = []
    #if not os.path.exists(f"~/.subcheck/{domain}/old.txt"):
        #os.mkdir(f"~/.subcheck/{domain}/")
        # copy and paste code from bellow
    if not os.path.exists("test.txt"):
        print("File is not here")
        print(colored("[+] Initial run detected...", "green"))
        print(colored("[+] Creating files...", "green"))
        new = connect()
        #for x in domains:
        #    for y in x:
        #        print(y)
    else:
        print(colored("[+] Checking for new subdomains...", "red"))
        domains = connect()
        for x in domains:
            for y in x:
                new.append(y)

        with open("old.txt", "r") as f:
            for x in f:
                old.append(x.strip())

            diff = difflib.unified_diff(
                old,
                new,
                fromfile='old.txt',
                tofile='new.txt',
                lineterm=''
            )

            for domain in diff:
                if domain.startswith("+++ new.txt"):
                    continue
                elif domain.startswith("+"):
                    print(colored("[+] New domain detected:", "green") + colored(f" {domain[1:]}", "yellow"))

if __name__ == "__main__":
    main()
