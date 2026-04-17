# gh0stfind3r
Automated bug bounty hunting framework with 35+ modules, CVE fingerprinting, and OWASP coverage.

# 👻 gh0stfind3r

**Automated Bug Bounty & Ethical Hacking Framework**  
*35+ modules | 37 CVE fingerprints | 93 CWE checks | OWASP Top 10 coverage*

![Version](https://img.shields.io/badge/version-1.0-red)
![License](https://img.shields.io/badge/license-MIT-blue)
![Platform](https://img.shields.io/badge/platform-Linux%20%7C%20macOS-lightgrey)
![Python](https://img.shields.io/badge/python-3.6%2B-blue)

---

## ⚡ Features

- **Reconnaissance**: WHOIS, DNS enumeration, subdomain discovery (passive/active), port scanning, technology fingerprinting
- **Vulnerability Scanning**: SQLi, XSS, LFI, XXE, SSRF, SSTI, NoSQLi, Command Injection, CRLF, Prototype Pollution, Deserialization
- **CVE Fingerprinting**: 37+ known CVEs (Log4Shell, Spring4Shell, Shellshock, Apache Struts, Drupalgeddon, ProxyLogon, Confluence, Jenkins, GitLab, Grafana, etc.)
- **API Security**: Full OWASP API Top 10 checks (BOLA, BFLA, rate limiting, excessive data exposure)
- **JWT Attacks**: Algorithm confusion, weak secret brute‑force, `kid` injection, claim tampering
- **AI Advisor**: Heuristic attack path suggestions based on discovered services and vulnerabilities
- **Reporting**: CWE‑mapped findings, OWASP Top 10 coverage summary, plain‑text and log output

---

## 🚀 Quick Start

```bash
# Clone the repository
git clone https://github.com/h11ghostberok-jpg/gh0stfind3r.git
cd gh0stfind3r

# Run the installer (installs dependencies automatically)
chmod +x install.sh
./install.sh

# Start a full scan
python3 gh0stfind3r.py -u https://target.com --full
