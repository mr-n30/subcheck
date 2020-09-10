#!/usr/bin/env python3
import os
import sys
import time
import difflib
import smtplib
import argparse
import psycopg2
from pathlib import Path
from termcolor import colored
from email.message import EmailMessage
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

print(r"""

      ███████╗██╗   ██╗██████╗ ██╗    ██╗ █████╗ ████████╗ ██████╗██╗  ██╗
      ██╔════╝██║   ██║██╔══██╗██║    ██║██╔══██╗╚══██╔══╝██╔════╝██║  ██║
      ███████╗██║   ██║██████╔╝██║ █╗ ██║███████║   ██║   ██║     ███████║
      ╚════██║██║   ██║██╔══██╗██║███╗██║██╔══██║   ██║   ██║     ██╔══██║
      ███████║╚██████╔╝██████╔╝╚███╔███╔╝██║  ██║   ██║   ╚██████╗██║  ██║
      ╚══════╝ ╚═════╝ ╚═════╝  ╚══╝╚══╝ ╚═╝  ╚═╝   ╚═╝    ╚═════╝╚═╝  ╚═╝

      """)

parser = argparse.ArgumentParser(description="Check if new subdomains have been added")
parser.add_argument("-e", "--email", type=str, help="Your Gmail", required=True)
parser.add_argument("-p", "--password", type=str, help="Your Gmail password", required=True)
parser.add_argument("-r", "--recipient", type=str, help="Email you're sending to (Can be the same as your Gmail)", required=True)
parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose mode")
parser.add_argument("-f", "--file", type=str, help="File containing domain(s) to check", required=True)

args = parser.parse_args()
file      = args.file
port      = 465
email     = args.email
passw     = args.password
verbose   = args.verbose
recipient = args.recipient

def connect():
    conn       = None
    old        = []
    new        = []
    domains    = []
    msg_buffer = []

    try:
        conn = psycopg2.connect(
            host="crt.sh",
            database="certwatch",
            user="guest",
            password=""
        )

        if verbose:
            print(colored("[+] Connecting to the database...", "magenta"))
        cur = conn.cursor()
        conn.set_session(readonly=True, autocommit=True)
        # START

        # Loop through entire file
        with open(file, "r") as f:
            for domain in f:
                home = str(Path.home()) + f"/.subwatch/{domain.strip()}/"
                # If old.txt is not present
                # create and write to it
                if not os.path.exists(home + "old.txt"):
                    try:
                        os.makedirs(home)
                    except FileExistsError:
                        pass
                    print(colored("[+] Initial run detected for: ", "green") + colored(f"{domain.strip()}", "yellow"))
                    print(colored("[+] Creating files...", "green"))
                    # Connect to PosgreSQL DB
                    # and write domains to file
                    with open(home + "old.txt", "w") as o:
                        cur.execute(f"SELECT ci.NAME_VALUE NAME_VALUE FROM certificate_identity ci WHERE ci.NAME_TYPE = 'dNSName' AND reverse(lower(ci.NAME_VALUE)) LIKE reverse(lower('%.{domain.strip()}'));")
                        for x in cur:
                            domains.append(x)
                        domains = list(dict.fromkeys(domains))
                        domains.sort()
                        for x in domains:
                            for y in x:
                                if "*" in y or "?" in y:
                                    pass
                                else:
                                    o.write(f"{y.lower()}\n")
                        # Clear out domains buffer
                        # when finished
                        domains = []
                        print(colored("[+] Done...", "green"))
                        print(colored("[+] We'll notify you when new subdomain(s) are detected...", "green"))
                else:
                    print(colored("[+] Checking for new subdomains: ", "green") + colored(f"{domain.strip()}", "yellow"))
                    cur.execute(f"SELECT ci.NAME_VALUE NAME_VALUE FROM certificate_identity ci WHERE ci.NAME_TYPE = 'dNSName' AND reverse(lower(ci.NAME_VALUE)) LIKE reverse(lower('%.{domain.strip()}'));")
                    for x in cur:
                        domains.append(x)
                    domains = list(dict.fromkeys(domains))
                    domains.sort()
                    # Load fresh set of domains from DB
                    for x in domains:
                        for y in x:
                            if "*" in y or "?" in y:
                                pass
                            else:
                                new.append(y.lower())
                    with open(home + "old.txt", "r") as o:
                        for x in o:
                            old.append(x.strip())
                    # Check for differences
                    diff = difflib.unified_diff(
                        old,
                        new,
                        fromfile='old.txt',
                        tofile='new.txt',
                        lineterm=''
                    )
                    for dom in diff:
                        if dom.startswith("+++ new.txt"):
                            continue
                        elif dom.startswith("+"):
                            print(colored("[+] New domain detected:", "blue") + colored(f" {dom[1:]}", "yellow"))
                            msg_buffer.append(dom[1:])
                    # Send email if msg_buffer is not empty
                    if not msg_buffer:
                        # Would be nice to put a time stamp here
                        print(colored("[+] No new domains...", "red"))
                    else:
                        try:
                            # Create the HTML file to be sent via email
                            with open(home + "email.html", "w") as html:
                                html.write("""
                                           <!DOCTYPE html>
                                           <html>
                                           <body>
                                           <div>
                                           <h3>
                                           <ul>
                                           """)
                                for dom in msg_buffer:
                                    html.write(f"""
                                               <li>{dom}</li>
                                               """)
                                html.write("""
                                           </ul>
                                           </h3>
                                           </div>
                                           </body>
                                           </html>
                                           """)
                            # Send email
                            with open(home + "email.html", "r") as e:
                                print(colored("[+] New domain(s) detected...", "yellow"))
                                print(colored("[+] Sending email...", "yellow"))
                                html = e.read()
                                msg  = MIMEMultipart("alternative")
                                msg["Subject"] = f"New subdomain(s) detected for: {domain}"
                                msg["From"]    = f"{email}"
                                msg["To"]      = f"{recipient}"
                                mime = MIMEText(html, "html")
                                msg.attach(mime)
                                with smtplib.SMTP_SSL("smtp.gmail.com", port) as server:
                                    server.ehlo()
                                    server.login(email, passw)
                                    server.send_message(msg)
                                    server.quit()
                                    print(colored("[+] Done...", "green"))
                                    # Write new subdomain(s) to old.txt
                                    with open(home + "old.txt", "w") as o:
                                        for x in new:
                                            o.write(f"{x.lower()}\n")
                        except smtplib.SMTPAuthenticationError:
                            print(colored("[!] Failed to login...", "red"))
                            print(colored("[!] Please check your email and credentials...", "red"))
                            sys.exit(1)
                    # No more domains
                    # to check
                    old        = []
                    new        = []
                    domains    = []
                    msg_buffer = []
        cur.close()

    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
        sys.exit(1)

    finally:
        if conn is not None:
            conn.close()
        if verbose:
            print(colored("[+] Database connection closed...", "magenta"))
        return domains

def main():
    connect()
    return 0

if __name__ == "__main__":
    main()
