# Mercer SS Tool

Mercer SS Tool is a local Minecraft scanner that lets you quickly scan Minecraft installations, mods, clients, launchers, versions, and Java information.

## What can it scan?

* Minecraft versions
* Fabric / Forge / NeoForge / Quilt
* Installed mods
* Mod names, versions, and loaders
* Minecraft clients
* Minecraft instances
* Launcher profiles
* Java version, architecture, and Java path
* Minecraft folder statistics

## Supported Clients

* NoRisk Client
* Lunar Client
* Badlion Client
* Feather Client
* LabyMod
* Prism Launcher
* Modrinth App
* CurseForge

## Reports

After the scan, the tool automatically creates:

* `screenshare_report.txt`
* `screenshare_report.json`

## Start the Scanner

You can run the scanner directly from the terminal without manually downloading the file:

```text
python -c "import urllib.request; exec(urllib.request.urlopen('https://raw.githubusercontent.com/ralcio/Mercer-SS-Tool/refs/heads/main/screenshare.py').read())"
```

Just paste the command into your terminal and press Enter to start the scan.

## Privacy

Mercer SS Tool runs locally on the computer being scanned. It only checks relevant Minecraft/client files and non-sensitive technical information. No scan results are uploaded to an external server.
