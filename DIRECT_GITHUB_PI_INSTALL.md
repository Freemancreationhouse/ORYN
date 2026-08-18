# ORYN — Direct GitHub + Raspberry Pi Installation

## A. Upload ORYN to GitHub

Create a GitHub repository:

https://github.com/Freemancreationhouse/ORYN

### Easiest upload from Windows using GitHub Desktop
1. Extract the ORYN ZIP to a normal folder.
2. Open GitHub Desktop.
3. File → Add Local Repository.
4. Select the extracted ORYN folder.
5. If asked, choose "create a repository here".
6. Repository name: ORYN
7. Publish repository.
8. Ensure the GitHub repository root directly contains:
   - setup-pi.sh
   - install-oryn-from-github.sh
   - main.py
   - modules/
   - patterns/
   - static/
   - frontend/

Do NOT upload only the ZIP as one file.

### Command-line upload alternative

Open PowerShell inside the extracted ORYN folder:

git init
git branch -M main
git add .
git commit -m "ORYN initial release"
git remote add origin https://github.com/Freemancreationhouse/ORYN.git
git push -u origin main

If the repository already exists locally, do not run `git init` again.

---

## B. Prepare Raspberry Pi Zero 2 W

Use Raspberry Pi Imager.

Recommended:
- Raspberry Pi Zero 2 W
- Raspberry Pi OS Lite (64-bit)
- hostname: oryn
- configure Wi-Fi
- enable SSH
- set username/password

Boot the Pi.

From Windows PowerShell:

ssh YOUR_PI_USERNAME@oryn.local

If that does not resolve, use the Pi IP address:

ssh YOUR_PI_USERNAME@192.168.x.x

---

## C. Install ORYN directly from GitHub

Recommended USB-controller installation:

curl -fsSL https://raw.githubusercontent.com/Freemancreationhouse/ORYN/main/install-oryn-from-github.sh | bash

The installer clones ORYN into:

~/oryn

and runs the included Raspberry Pi setup.

If a reboot is requested:

sudo reboot

---

## D. Open ORYN

After the Pi restarts, try:

http://oryn.local

If that does not resolve, use:

http://PI_IP_ADDRESS

---

## E. Update ORYN later

Push your new software version to GitHub from the development computer.

Then on the Pi run:

oryn update

Useful commands:

oryn status
oryn logs
oryn restart
oryn stop
oryn start
oryn update
oryn wifi help

---

## F. UART option

For initial testing, use USB between the controller and Pi.

If you later intentionally want Pi GPIO UART, run the normal setup with its
UART option documented by `setup-pi.sh --help`.
