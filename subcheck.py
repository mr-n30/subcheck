#!/usr/bin/env python3
import argparse
import psycopg2

parser = argparse.ArgumentParser(description="Request a URL")
parser.add_argument("-d", "--domain", type=str, help="Domain to check", required=True)
args = parser.parse_args()

domain = args.domain

def connect():
  conn = None
  try:
    print("Test")
    conn = psycopg2.connect(
      host="crt.sh",
      database="certwatch",
      user="guest",
      password=""
    )

    print("[+] Connecting to the database...")
    cur = conn.cursor()
    conn.set_session(readonly=True, autocommit=True)

    print("PostgreSQL database version:")
    cur.execut("SELECT version();")
    #cursor.execute("SELECT ci.NAME_VALUE NAME_VALUE FROM certificate_identity ci WHERE ci.NAME_TYPE = 'dNSName' AND reverse(lower(ci.NAME_VALUE)) LIKE reverse(lower('%{}'));".format(domain))
    db_version = cur.fetchone()
    print(db_version)
    cur.close()
    
  except (Exception, psycopg2.DatabaseError) as error:
    print(error)
    
  finally:
    if conn is not None:
      conn.close()
      print("[+] Database connection closed...")

if __name__ == "__main__":
  connect()
