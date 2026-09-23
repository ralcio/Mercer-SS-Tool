import os
import platform
import subprocess
import json
import re
from pathlib import Path
from zipfile import ZipFile
from datetime import datetime

RESET = "\033[0m"
WHITE = "\033[97m"

HEADER = r"""
███╗   ███╗███████╗██████╗  ██████╗███████╗██████╗     ████████╗ ██████╗  ██████╗ ██╗     
████╗ ████║██╔════╝██╔══██╗██╔════╝██╔════╝██╔══██╗    ╚══██╔══╝██╔═══██╗██╔═══██╗██║     
██╔████╔██║█████╗  ██████╔╝██║     █████╗  ██████╔╝       ██║   ██║   ██║██║   ██║██║     
██║╚██╔╝██║██╔══╝  ██╔══██╗██║     ██╔══╝  ██╔══██╗       ██║   ██║   ██║██║   ██║██║     
██║ ╚═╝ ██║███████╗██║  ██║╚██████╗███████╗██║  ██║       ██║   ╚██████╔╝╚██████╔╝███████╗
╚═╝     ╚═╝╚══════╝╚═╝  ╚═╝ ╚═════╝╚══════╝╚═╝  ╚═╝       ╚═╝    ╚═════╝  ╚═════╝╚══════╝
"""

CLIENT_LOCATIONS = {
    "NoRisk Client": [
        Path.home() / "AppData/Roaming/NoRiskClient",
        Path.home() / "AppData/Roaming/.noriskclient",
    ],
    "Lunar Client": [
        Path.home() / "AppData/Roaming/.lunarclient",
        Path.home() / "AppData/Roaming/.lunarclient/offline",
    ],
    "Badlion Client": [
        Path.home() / "AppData/Roaming/Badlion Client",
        Path.home() / "AppData/Roaming/.badlion",
    ],
    "Feather Client": [
        Path.home() / "AppData/Roaming/feather",
        Path.home() / "AppData/Roaming/.feather",
    ],
    "LabyMod": [
        Path.home() / "AppData/Roaming/LabyMod",
        Path.home() / "AppData/Roaming/.labymod",
    ],
    "Prism Launcher": [
        Path.home() / "AppData/Roaming/PrismLauncher",
        Path.home() / ".local/share/PrismLauncher",
    ],
    "Modrinth App": [
        Path.home() / "AppData/Roaming/ModrinthApp",
        Path.home() / "AppData/Roaming/com.modrinth.theseus",
    ],
    "CurseForge": [
        Path.home() / "Documents/CurseForge",
        Path.home() / "AppData/Roaming/CurseForge",
    ],
}


def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")


def find_minecraft():
    candidates = []

    if os.name == "nt":
        appdata = os.getenv("APPDATA")
        if appdata:
            candidates.append(Path(appdata) / ".minecraft")
    elif platform.system() == "Darwin":
        candidates.append(Path.home() / "Library/Application Support/minecraft")
    else:
        candidates.append(Path.home() / ".minecraft")

    for path in candidates:
        if path.exists():
            return path

    return None


def find_jars(folder, recursive=False):
    if not folder or not folder.exists():
        return []

    try:
        if recursive:
            return list(folder.rglob("*.jar"))
        return list(folder.glob("*.jar"))
    except (PermissionError, OSError):
        return []


def read_mod_info(jar_path):
    result = {
        "file": jar_path.name,
        "path": str(jar_path),
        "loader": "Unknown",
        "id": "",
        "name": jar_path.stem,
        "version": "",
    }

    try:
        with ZipFile(jar_path, "r") as jar:
            names = set(jar.namelist())

            if "fabric.mod.json" in names:
                data = json.loads(
                    jar.read("fabric.mod.json").decode(
                        "utf-8", errors="replace"
                    )
                )

                result["loader"] = "Fabric"
                result["id"] = str(data.get("id", ""))
                result["name"] = str(
                    data.get("name", result["id"] or jar_path.stem)
                )
                result["version"] = str(data.get("version", ""))

            elif "META-INF/mods.toml" in names:
                text = jar.read("META-INF/mods.toml").decode(
                    "utf-8", errors="replace"
                )

                result["loader"] = "Forge/NeoForge"

                mod_id = re.search(
                    r'modId\s*=\s*"([^"]+)"',
                    text
                )
                version = re.search(
                    r'version\s*=\s*"([^"]+)"',
                    text
                )
                display = re.search(
                    r'displayName\s*=\s*"([^"]+)"',
                    text
                )

                if mod_id:
                    result["id"] = mod_id.group(1)
                    result["name"] = result["id"]

                if version:
                    result["version"] = version.group(1)

                if display:
                    result["name"] = display.group(1)

    except Exception:
        pass

    return result


def scan_mod_folder(mods_folder):
    mods = []

    for jar in find_jars(mods_folder):
        mods.append(read_mod_info(jar))

    return mods


def detect_loader(minecraft):
    if not minecraft:
        return []

    detected = []

    checks = {
        "Fabric": minecraft / "fabric-loader",
        "Forge": minecraft / "libraries/net/minecraftforge",
        "NeoForge": minecraft / "libraries/net/neoforged",
        "Quilt": minecraft / "quilt-loader",
    }

    for name, path in checks.items():
        if path.exists():
            detected.append(name)

    if (minecraft / "mods").exists():
        for jar in find_jars(minecraft / "mods"):
            info = read_mod_info(jar)

            if (
                info["loader"] not in detected
                and info["loader"] != "Unknown"
            ):
                detected.append(info["loader"])

    return detected


def get_versions(minecraft):
    if not minecraft:
        return []

    versions = minecraft / "versions"

    if not versions.exists():
        return []

    try:
        return sorted(
            [
                p.name
                for p in versions.iterdir()
                if p.is_dir()
            ],
            key=str.lower
        )
    except (PermissionError, OSError):
        return []


def detect_clients():
    found = {}

    for client, paths in CLIENT_LOCATIONS.items():
        matches = [
            str(path)
            for path in paths
            if path.exists()
        ]

        if matches:
            found[client] = matches

    return found


def get_client_jars(client_paths):
    result = []

    for path_text in client_paths:
        path = Path(path_text)

        if not path.exists():
            continue

        for jar in find_jars(path, recursive=True):
            result.append(str(jar))

    return result[:1000]


def scan_instances():
    home = Path.home()

    locations = [
        home / "AppData/Roaming/PrismLauncher/instances",
        home / "AppData/Roaming/ModrinthApp/profiles",
        home / "AppData/Roaming/com.modrinth.theseus/profiles",
        home / "Documents/CurseForge/Minecraft/Instances",
        home / "AppData/Roaming/CurseForge/Minecraft/Instances",
    ]

    return [
        path
        for path in locations
        if path.exists()
    ]


def detect_instances():
    data = []

    for base in scan_instances():
        try:
            for instance in base.iterdir():
                if instance.is_dir():
                    mods = instance / "mods"

                    data.append({
                        "instance": instance.name,
                        "path": str(instance),
                        "mods": len(find_jars(mods)),
                    })

        except (PermissionError, OSError):
            pass

    return data


def get_launcher_profiles(minecraft):
    if not minecraft:
        return []

    file = minecraft / "launcher_profiles.json"

    if not file.exists():
        return []

    try:
        data = json.loads(
            file.read_text(
                encoding="utf-8",
                errors="replace"
            )
        )
    except Exception:
        return []

    profiles = []

    for profile_id, profile in data.get(
        "profiles",
        {}
    ).items():

        profiles.append({
            "id": profile_id,
            "name": profile.get("name", ""),
            "lastVersionId": profile.get(
                "lastVersionId",
                ""
            ),
            "type": profile.get(
                "type",
                ""
            ),
        })

    return profiles


def get_java_details():
    result = {
        "installed": False,
        "version": "",
        "vendor": "",
        "arch": "",
        "home": "",
    }

    try:
        process = subprocess.run(
            [
                "java",
                "-XshowSettings:properties",
                "-version",
            ],
            capture_output=True,
            text=True,
            timeout=10,
        )

        output = (
            process.stdout or ""
        ) + "\n" + (
            process.stderr or ""
        )

        result["installed"] = True

        patterns = {
            "version": r"java\.version\s*=\s*(.+)",
            "vendor": r"java\.vendor\s*=\s*(.+)",
            "arch": r"os\.arch\s*=\s*(.+)",
            "home": r"java\.home\s*=\s*(.+)",
        }

        for key, pattern in patterns.items():
            match = re.search(
                pattern,
                output
            )

            if match:
                result[key] = match.group(1).strip()

    except (
        FileNotFoundError,
        subprocess.SubprocessError,
        OSError,
    ):
        pass

    return result


def folder_statistics(minecraft):
    folders = [
        "mods",
        "config",
        "resourcepacks",
        "shaderpacks",
        "saves",
        "screenshots",
        "versions",
        "logs",
        "crash-reports",
    ]

    result = {}

    for folder_name in folders:
        folder = minecraft / folder_name
        files = 0
        total_size = 0

        if folder.exists():
            try:
                for item in folder.rglob("*"):
                    if item.is_file():
                        files += 1

                        try:
                            total_size += item.stat().st_size
                        except OSError:
                            pass

            except (
                PermissionError,
                OSError,
            ):
                pass

        result[folder_name] = {
            "files": files,
            "size_mb": round(
                total_size / (1024 * 1024),
                2,
            ),
        }

    return result


def get_system_info():
    return {
        "os": platform.system(),
        "os_version": platform.version(),
        "architecture": platform.machine(),
        "python": platform.python_version(),
    }


def create_json_report(report):
    report_path = (
        Path.cwd() /
        "screenshare_report.json"
    )

    with report_path.open(
        "w",
        encoding="utf-8"
    ) as file:
        json.dump(
            report,
            file,
            indent=4,
            ensure_ascii=False,
        )

    return report_path


def create_txt_report(report):
    report_path = (
        Path.cwd() /
        "screenshare_report.txt"
    )

    lines = []

    lines.append(
        "MINECRAFT SCREENSHARE REPORT"
    )
    lines.append("=" * 60)
    lines.append(
        f"Created: {report['created_at']}"
    )
    lines.append("")

    lines.append("SYSTEM")
    lines.append("-" * 60)

    for key, value in report[
        "system"
    ].items():
        lines.append(
            f"{key}: {value}"
        )

    lines.append("")

    lines.append("MINECRAFT")
    lines.append("-" * 60)

    lines.append(
        f"Path: {report['minecraft']['path']}"
    )

    lines.append(
        "Loaders: "
        + (
            ", ".join(
                report["minecraft"]["loaders"]
            )
            or "None"
        )
    )

    lines.append(
        "Versions: "
        + (
            ", ".join(
                report["minecraft"]["versions"]
            )
            or "None"
        )
    )

    lines.append("")

    lines.append("MODS")
    lines.append("-" * 60)

    for mod in report["mods"]:
        lines.append(
            f"{mod['name']} | "
            f"ID: {mod['id']} | "
            f"Version: {mod['version']} | "
            f"Loader: {mod['loader']} | "
            f"File: {mod['file']}"
        )

    lines.append("")

    lines.append("CLIENTS")
    lines.append("-" * 60)

    for client, client_paths in report[
        "clients"
    ].items():

        lines.append(client)

        for client_path in client_paths:
            lines.append(
                f"  {client_path}"
            )

    lines.append("")

    lines.append("INSTANCES")
    lines.append("-" * 60)

    for instance in report[
        "instances"
    ]:
        lines.append(
            f"{instance['instance']} | "
            f"Mods: {instance['mods']} | "
            f"Path: {instance['path']}"
        )

    lines.append("")

    lines.append(
        "LAUNCHER PROFILES"
    )
    lines.append("-" * 60)

    for profile in report[
        "launcher_profiles"
    ]:
        lines.append(
            f"{profile['name']} | "
            f"Version: {profile['lastVersionId']} | "
            f"Type: {profile['type']}"
        )

    lines.append("")

    lines.append("JAVA")
    lines.append("-" * 60)

    for key, value in report[
        "java"
    ].items():
        lines.append(
            f"{key}: {value}"
        )

    lines.append("")

    lines.append(
        "MINECRAFT FOLDER STATISTICS"
    )
    lines.append("-" * 60)

    for folder, stats in report[
        "folder_statistics"
    ].items():

        lines.append(
            f"{folder}: "
            f"{stats['files']} files | "
            f"{stats['size_mb']} MB"
        )

    lines.append("")

    lines.append("SUMMARY")
    lines.append("-" * 60)

    lines.append(
        f"Mods: {len(report['mods'])}"
    )

    lines.append(
        f"Clients: {len(report['clients'])}"
    )

    lines.append(
        f"Instances: {len(report['instances'])}"
    )

    lines.append(
        "Launcher profiles: "
        f"{len(report['launcher_profiles'])}"
    )

    report_path.write_text(
        "\n".join(lines),
        encoding="utf-8",
    )

    return report_path


def main():
    clear_screen()

    print(
        WHITE +
        HEADER +
        RESET
    )

    print(
        WHITE +
        "Local Minecraft Screenshare Scanner" +
        RESET
    )

    print(
        WHITE +
        "=" * 70 +
        RESET
    )

    print()

    minecraft = find_minecraft()

    if not minecraft:
        print(
            WHITE +
            "Minecraft wurde nicht gefunden." +
            RESET
        )

        input(
            "\nEnter zum Beenden..."
        )

        return

    mods_folder = minecraft / "mods"

    mods = scan_mod_folder(
        mods_folder
    )

    clients = detect_clients()
    instances = detect_instances()
    launcher_profiles = get_launcher_profiles(
        minecraft
    )

    java = get_java_details()
    stats = folder_statistics(
        minecraft
    )

    loaders = detect_loader(
        minecraft
    )

    versions = get_versions(
        minecraft
    )

    report = {
        "created_at": datetime.now().isoformat(
            timespec="seconds"
        ),

        "system": get_system_info(),

        "minecraft": {
            "path": str(minecraft),
            "loaders": loaders,
            "versions": versions,
        },

        "mods": mods,
        "clients": clients,
        "instances": instances,
        "launcher_profiles": launcher_profiles,
        "java": java,
        "folder_statistics": stats,
    }

    print(
        WHITE +
        "[ MINECRAFT ]" +
        RESET
    )

    print(
        f"Path: {minecraft}"
    )

    print(
        "Loaders: "
        + (
            ", ".join(loaders)
            if loaders
            else "None"
        )
    )

    print(
        f"Versions: {len(versions)}"
    )

    print()

    print(
        WHITE +
        "[ MODS ]" +
        RESET
    )

    if mods:
        for mod in mods:
            version = (
                mod["version"]
                or "?"
            )

            print(
                f"- {mod['name']} | "
                f"{version} | "
                f"{mod['loader']}"
            )

    else:
        print(
            "Keine .jar Mods gefunden."
        )

    print()

    print(
        WHITE +
        "[ CLIENTS / LAUNCHER ]" +
        RESET
    )

    if clients:
        for client, client_paths in clients.items():
            print(
                f"- {client}"
            )

            for client_path in client_paths:
                print(
                    f"  {client_path}"
                )

    else:
        print(
            "Keine bekannten Clients gefunden."
        )

    print()

    print(
        WHITE +
        "[ MINECRAFT INSTANCES ]" +
        RESET
    )

    if instances:
        for instance in instances:
            print(
                f"- {instance['instance']} | "
                f"{instance['mods']} Mods"
            )

    else:
        print(
            "Keine bekannten Instanzen gefunden."
        )

    print()

    print(
        WHITE +
        "[ LAUNCHER PROFILE ]" +
        RESET
    )

    if launcher_profiles:
        for profile in launcher_profiles:
            print(
                f"- {profile['name']} | "
                f"{profile['lastVersionId']} | "
                f"{profile['type']}"
            )

    else:
        print(
            "Keine Launcher-Profile gefunden."
        )

    print()

    print(
        WHITE +
        "[ JAVA ]" +
        RESET
    )

    if java["installed"]:
        print(
            f"Version: {java['version'] or '?'}"
        )

        print(
            f"Vendor: {java['vendor'] or '?'}"
        )

        print(
            f"Arch: {java['arch'] or '?'}"
        )

        print(
            f"Home: {java['home'] or '?'}"
        )

    else:
        print(
            "Java wurde nicht gefunden."
        )

    print()

    print(
        WHITE +
        "[ MINECRAFT ORDNER ]" +
        RESET
    )

    for folder, values in stats.items():
        print(
            f"- {folder}: "
            f"{values['files']} Dateien | "
            f"{values['size_mb']} MB"
        )

    print()

    print(
        WHITE +
        "[ SCAN SUMMARY ]" +
        RESET
    )

    print(
        f"Mods: {len(mods)}"
    )

    print(
        f"Clients: {len(clients)}"
    )

    print(
        f"Instances: {len(instances)}"
    )

    print(
        "Launcher profiles: "
        f"{len(launcher_profiles)}"
    )

    print()

    json_path = create_json_report(
        report
    )

    txt_path = create_txt_report(
        report
    )

    print(
        WHITE +
        "[ REPORTS ]" +
        RESET
    )

    print(
        f"JSON: {json_path}"
    )

    print(
        f"TXT : {txt_path}"
    )

    print()

    print(
        WHITE +
        "Scan abgeschlossen." +
        RESET
    )

    input(
        "\nEnter zum Beenden..."
    )


if __name__ == "__main__":
    main()
