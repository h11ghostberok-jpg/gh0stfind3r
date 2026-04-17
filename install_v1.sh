#!/bin/bash
# gh0stfind3r v4.0 installer — GHOST BEROK
RED='\033[91m'; GREEN='\033[92m'; YELLOW='\033[93m'
CYAN='\033[96m'; BOLD='\033[1m'; RESET='\033[0m'
ok()   { echo -e "  ${GREEN}[✔]${RESET} $1"; }
warn() { echo -e "  ${YELLOW}[!]${RESET} $1"; }
info() { echo -e "  ${CYAN}[*]${RESET} $1"; }

echo -e "${RED}${BOLD}"
cat << 'ART'
 ██████╗ ██╗  ██╗ ██████╗ ███████╗████████╗
██╔════╝ ██║  ██║██╔═══██╗██╔════╝╚══██╔══╝
██║  ███╗███████║██║   ██║███████╗   ██║
██║   ██║██╔══██║██║   ██║╚════██║   ██║
╚██████╔╝██║  ██║╚██████╔╝███████║   ██║
 ╚═════╝ ╚═╝  ╚═╝ ╚═════╝ ╚══════╝   ╚═╝
  v4.0 — CVE/CWE/OWASP Edition
ART
echo -e "${RESET}"

command -v python3 &>/dev/null || sudo apt install python3 -y
ok "Python3 ready"

info "Installing APT tools..."
sudo apt update -qq 2>/dev/null
sudo apt install -y nmap whatweb nikto sqlmap wafw00f whois gobuster dirb \
    amass dnsmap testssl.sh curl wget git python3-pip hydra dnsutils \
    seclists 2>/dev/null
ok "APT tools done"

info "PIP tools..."
pip3 install wafw00f arjun --break-system-packages 2>/dev/null || \
pip3 install wafw00f arjun 2>/dev/null
ok "PIP tools done"

if command -v go &>/dev/null; then
    info "Go tools..."
    export PATH=$PATH:$HOME/go/bin
    go install github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest 2>/dev/null && ok "subfinder"
    go install github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest        2>/dev/null && ok "nuclei"
    go install github.com/projectdiscovery/httpx/cmd/httpx@latest             2>/dev/null && ok "httpx"
    go install github.com/hahwul/dalfox/v2@latest                             2>/dev/null && ok "dalfox"
    go install github.com/lc/gau/v2/cmd/gau@latest                            2>/dev/null && ok "gau"
    go install github.com/tomnomnom/waybackurls@latest                        2>/dev/null && ok "waybackurls"
    go install github.com/tomnomnom/assetfinder@latest                        2>/dev/null && ok "assetfinder"
    go install github.com/ffuf/ffuf/v2@latest                                 2>/dev/null && ok "ffuf"
    echo 'export PATH=$PATH:$HOME/go/bin' >> ~/.bashrc
    echo 'export PATH=$PATH:$HOME/go/bin' >> ~/.zshrc 2>/dev/null
    nuclei -update-templates -silent 2>/dev/null && ok "nuclei templates updated"
else
    warn "Go not found! sudo apt install golang-go -y  then rerun"
fi

info "Installing gh0stfind3r v4.0..."
sudo cp gh0stfind3r_v4.py /usr/local/bin/gh0stfind3r
sudo chmod +x /usr/local/bin/gh0stfind3r

echo ""
echo -e "${GREEN}${BOLD}gh0stfind3r v4.0 installed!${RESET}"
echo ""
echo -e "${CYAN}Usage:${RESET}"
echo "  gh0stfind3r -u https://target.com              # Auto full scan"
echo "  gh0stfind3r -u https://target.com --quick      # Fast scan"
echo "  gh0stfind3r -u https://target.com --full       # Deep scan (all 35 modules)"
echo "  gh0stfind3r -u https://target.com --exploit    # Exploit only"
echo "  gh0stfind3r -u https://target.com?id=1 --modules sqli,xss,ssti,jwt,cve"
echo "  gh0stfind3r --menu                             # Interactive menu"
echo "  gh0stfind3r --check-tools                      # Tool status"
echo ""
echo -e "${YELLOW}35 modules | 37 CVEs | 93 CWE checks | OWASP Top 10${RESET}"
echo -e "${RED}Use on authorized targets only — GHOST BEROK${RESET}"
