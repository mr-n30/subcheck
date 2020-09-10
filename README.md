# Subwatch
A program to check for newly added subdomains. Output is saved in `~/.subwatch/`

## Installation:
```bash
git clone https://github.com/mr-n30/subwatch.git
cd subcheck && pip3 install -r requirements.txt
./subwatch.py -h
```

## Usage:
```bash
$ cat domains.txt
example.com
exampledomain.com
...
$ subwatch -e "your_email@example.com" -p "YourPassword" -r "recipient_email@example.com" -f domains.txt 
```
