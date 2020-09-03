#!/usr/bin/env python3
import os
import sys
import difflib
import smtplib
import argparse
import psycopg2
from pathlib import Path
from termcolor import colored
from email.message import EmailMessage
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

parser = argparse.ArgumentParser(description="Check if new subdomains have been added")
parser.add_argument("-e", "--email", type=str, help="Your Gmail", required=True)
parser.add_argument("-p", "--password", type=str, help="Your Gmail password", required=True)
parser.add_argument("-r", "--recipient", type=str, help="Email you're sending to (Can be the same as your Gmail)", required=True)
parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose mode")
parser.add_argument("-d", "--domain", type=str, help="Domain to check", required=True)

args = parser.parse_args()
port      = 465
email     = args.email
passw     = args.password
domain    = args.domain
verbose   = args.verbose
recipient = args.recipient
home      = str(Path.home()) + f"/.subcheck/{domain}/"

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
        cur.execute(f"SELECT ci.NAME_VALUE NAME_VALUE FROM certificate_identity ci WHERE ci.NAME_TYPE = 'dNSName' AND reverse(lower(ci.NAME_VALUE)) LIKE reverse(lower('%.{domain}'));")
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
    old        = []
    new        = []
    domains    = []
    msg_buffer = []

    if not os.path.exists(home + "old.txt"):
        os.makedirs(home)
        print(colored("[+] Initial run detected...", "green"))
        print(colored("[+] Creating files...", "green"))
        print(colored("[+] Done...", "green"))
        print(colored("[+] We'll notify you when a new subdomain is detected...", "green"))
        new = connect()
        with open(home + "old.txt", "w") as f:
            for x in new:
                for y in x:
                    f.write(f"{y}\n")
    else:
        print(colored("[+] `old.txt` detected...", "green"))
        print(colored("[+] Checking for new subdomains...", "green"))
        domains = connect()
        for x in domains:
            for y in x:
                new.append(y)

        with open(home + "old.txt", "r") as f:
            for x in f:
                old.append(x.strip())

            diff = difflib.unified_diff(
                old,
                new,
                fromfile='old.txt',
                tofile='new.txt',
                lineterm=''
            )

            # Check for new subdomains
            for dom in diff:
                if dom.startswith("+++ new.txt"):
                    continue
                elif dom.startswith("+"):
                    print(colored("[+] New domain detected:", "blue") + colored(f" {dom[1:]}", "yellow"))
                    msg_buffer.append(dom[1:])

            # Send email if msg_buffer is not empty
            if not msg_buffer:
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
                                   <h2>
                                   <ul>
                                   """)
                        for dom in msg_buffer:
                            html.write(f"""
                                       <li>{dom}</li>
                                       """)
                        html.write("""
                                   </ul>
                                   </h2>
                                   </div>
                                   </body>
                                   </html>
                                   """)
                    with open(home + "email.html", "r") as f:
                        print(colored("[+] New domain(s) detected...", "yellow"))
                        print(colored("[+] Sending email...", "yellow"))
                        html = f.read()
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
                except smtplib.SMTPAuthenticationError:
                    print(colored("[!] Failed to login...", "red"))
                    print(colored("[!] Please check your email and credentials...", "red"))
                    sys.exit(1)

    return 0

if __name__ == "__main__":
    main()
