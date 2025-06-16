"""
Overmind Studios BlenderUpdaterCLI - update Blender to latest buildbot version
Copyright (C) 2018-2022 by Tobias Kummer for Overmind Studios

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

from colorama import init, Fore
from progress.bar import IncrementalBar
from packaging import version
import json
import argparse
import configparser
import os
import platform
import re
import requests
import shutil
import subprocess
import sys
import threading
import time


appversion = "v1.7.1"
url = "https://builder.blender.org/download/daily/"
updateurl = (
    "https://api.github.com/repos/overmindstudios/BlenderUpdaterCLI/releases/latest"
)
DEFAULT_TEMP_DIR = "./blendertemp/"
CONFIG_FILE_NAME = "config.ini"

OS_WINDOWS = "windows"
OS_LINUX = "linux"
EXT_ZIP = "zip"
EXT_TAR_XZ = "tar.xz"

init(autoreset=True)  # enable Colorama autoreset
failed = False
config = configparser.ConfigParser()
tempDir = DEFAULT_TEMP_DIR


class Spinner:
    busy = False
    delay = 0.1

    @staticmethod
    def spinning_cursor():
        while True:
            for cursor in "|/-\\":
                yield cursor

    def __init__(self, title, delay=None):
        self.spinner_generator = self.spinning_cursor()
        if delay is not None:
            try:
                parsed_delay = float(delay)
                if parsed_delay > 0:
                    self.delay = parsed_delay
            except ValueError:
                pass  # Use default delay if parsing fails
        self.title = title

    def spinner_task(self):
        while self.busy:
            sys.stdout.write(self.title + next(self.spinner_generator))
            sys.stdout.flush()
            time.sleep(self.delay)
            sys.stdout.write("\b" * (len(self.title) + 1))
            sys.stdout.flush()

    def start(self):
        self.busy = True
        threading.Thread(target=self.spinner_task).start()

    def stop(self):
        self.busy = False
        time.sleep(self.delay)


parser = argparse.ArgumentParser(
    description="Update Blender to latest nightly build. (c) 2018-2021 by Tobias Kummer/Overmind Studios.",
    epilog="example usage: BlenderUpdaterCLI -b 2.93.2 -p C:\\Blender",
)
parser.add_argument("-p", "--path", help="Destination path", required=True, type=str)
parser.add_argument(
    "-o",
    "--operatingsystem",
    help="Operating system. 'linux' or 'windows'. If omitted, it will try to autodetect current OS.",
    type=str,
)
parser.add_argument(
    "-y", "--yes", help="Install even if version already installed", action="store_true"
)
parser.add_argument(
    "-n", "--no", help="Don't install if version already installed", action="store_true"
)
parser.add_argument(
    "-k", "--keep", help="Keep temporary downloaded archive file", action="store_true"
)
parser.add_argument(
    "-t", "--temp", help="Temporary file path", required=False, type=str
)
parser.add_argument(
    "-b",
    "--blender",
    help="Desired Blender version - for example '-b 2.93.2'",
    required=True,
    type=str,
)
parser.add_argument(
    "-r",
    "--run",
    help="Run downloaded Blender version when finished",
    action="store_true",
)
parser.add_argument(
    "-v",
    "--version",
    action="version",
    version=appversion,
    help="Print program version",
)
args = parser.parse_args()


# Check for updates for BlenderUpdaterCLI
try:
    appupdate = requests.get(
        "https://api.github.com/repos/overmindstudios/BlenderUpdaterCLI/releases/latest"
    ).text
    UpdateData = json.loads(appupdate)
    applatestversion = UpdateData["tag_name"]
    if version.parse(applatestversion) > version.parse(appversion):
        print(" ERROR ".center(80, "-"))
        print(f"{Fore.RED}Updated version of BlenderUpdaterCLI found.")
        print(f"{Fore.RED}The current version might not work properly anymore.")
        print(
            f"{Fore.RED}Please visit https://github.com/overmindstudios/BlenderUpdaterCLI/releases"
        )
        print(f"{Fore.RED}to download the latest version.")
        print(f"{Fore.RED}Current: {appversion} - Latest: {applatestversion}")
        sys.exit(1)
except Exception:
    print(" NOTICE ".center(80, "-"))
    print("Cannot check for updates.")
    raise Exception


# Start update process

print(" SETTINGS ".center(80, "-"))

# check for path validity
if os.path.isdir(args.path):
    destination_path = args.path
    print(f"Destination path: {Fore.GREEN}{args.path}")
else:
    print(Fore.RED + f"'{args.path}' is an invalid path, make sure directory exists")
    failed = True

if args.temp:
    tempDir = args.temp
print(f"Temporary path: {Fore.GREEN}{tempDir}")

# check for desired blender version
blender = args.blender

# check for desired operating system or autodetect when empty
opsys_map = {
    "Windows": (OS_WINDOWS, EXT_ZIP),
    "Linux": (OS_LINUX, EXT_TAR_XZ),
}
autodetected_os_msg = ""
opsys = None
extension = None

if args.operatingsystem:
    user_os_key = args.operatingsystem.lower()
    if user_os_key == OS_WINDOWS:
        opsys, extension = OS_WINDOWS, EXT_ZIP
    elif user_os_key == OS_LINUX:
        opsys, extension = OS_LINUX, EXT_TAR_XZ
    else:
        print(f"{Fore.RED}Syntax error - use '-o {OS_WINDOWS}' or '-o {OS_LINUX}'")
        failed = True
else:  # Autodetect
    current_platform_system = platform.system()
    if current_platform_system in opsys_map:
        opsys, extension = opsys_map[current_platform_system]
        autodetected_os_msg = f"{Fore.CYAN} (autodetected)"
    else:
        print(
            f"{Fore.RED}Unsupported operating system auto-detected: {current_platform_system}"
        )
        failed = True

if not failed and opsys:
    print(f"Operating system: {Fore.GREEN}{opsys}{autodetected_os_msg}")

# Only 64bit supported for all OS in experimental builds
arch = "64"

# check for --keep flag
keep_temp = args.keep
print(
    f"{Fore.MAGENTA}Will keep temporary archive file"
    if keep_temp
    else f"{Fore.MAGENTA}Will NOT keep temporary archive file"
)

# check for --run flag
if args.run:
    print(f"{Fore.MAGENTA}Will run Blender when finished")
    will_run = True
else:
    print(f"{Fore.MAGENTA}Will NOT run Blender when finished")
    will_run = False

print("-".center(80, "-"))

if args.yes and args.no:
    print("You cannot pass both -y and -n flags at the same time!")
    failed = True

# Abort if any error occured during parsing
if failed:
    print(f"{Fore.RED}Input errors detected, aborted (check above for details)")
    sys.exit(1)
else:
    try:
        req = requests.get(url)
        req.raise_for_status()  # Raise an exception for HTTP errors
    except requests.exceptions.RequestException as e:
        print(f"{Fore.RED}Error connecting to {url}: {e}")
        sys.exit(1)

    # Ensure opsys and extension are valid before using in regex
    if not opsys or not extension:
        print(f"{Fore.RED}Operating system details not determined. Cannot proceed.")
        sys.exit(1)

    regex_pattern_str = f"blender-{blender}[^\\s]+{opsys}[^\\s]+{extension}"
    try:
        found_files = re.findall(regex_pattern_str, req.text)
    except Exception as e:  # Should be rare if req.text is valid
        print(f"{Fore.RED}Error parsing download page content: {e}")
        sys.exit(1)

    if not found_files:
        print(
            f"{Fore.RED}No matching Blender build found for version '{args.blender}', OS '{opsys}', extension '{extension}'."
        )
        print(f"{Fore.RED}Please check {url} for available builds.")
        sys.exit(1)

    target_filename = found_files[0]

    if os.path.isfile(CONFIG_FILE_NAME):
        config.read(CONFIG_FILE_NAME)
        lastversion = ""
        try:
            lastversion = config.get("main", "version")
        except (configparser.NoSectionError, configparser.NoOptionError):
            pass  # It's okay if the version is not in the config yet
        except configparser.Error as e:
            print(f"{Fore.YELLOW}Warning: Could not read last version from config: {e}")

        if lastversion == target_filename:
            if args.no:
                print(
                    "This version is already installed. -n option present, exiting..."
                )
                sys.exit(0)
            if not args.yes:  # Prompt only if not -y and not -n
                while True:  # Loop until valid input y/n
                    anyway = input(
                        "This version is already installed. Continue anyways? [Y]es or [N]o: "
                    ).lower()
                    if anyway == "n":
                        sys.exit(0)
                    elif anyway == "y":
                        break
                    print("Invalid choice, try again!")
    else:
        config.read(CONFIG_FILE_NAME)  # Read (empty) config
        config.add_section("main")
        with open(CONFIG_FILE_NAME, "w") as f:
            config.write(f)

    if not keep_temp:
        if os.path.isdir(tempDir):
            shutil.rmtree(tempDir)
    os.makedirs(tempDir, exist_ok=True)

    print(f"{Fore.GREEN}All settings valid, proceeding...")
    print(f"Downloading {target_filename}")
    chunkSize = 10240
    download_file_path = os.path.join(tempDir, target_filename)
    try:
        r = requests.get(url + target_filename, stream=True)
        r.raise_for_status()
        with open(download_file_path, "wb") as f:
            pbar = IncrementalBar(
                "Downloading",
                max=int(r.headers["Content-Length"]) / chunkSize,
                suffix="%(percent)d%%",
            )
            for chunk in r.iter_content(chunk_size=chunkSize):
                if chunk:  # filter out keep-alive new chunks
                    pbar.next()
                    f.write(chunk)
            pbar.finish()
    except requests.exceptions.RequestException as e:
        print(f"Download {Fore.RED}failed: {e}. Exiting.")
        sys.exit(1)
    except IOError as e:
        print(f"Download {Fore.RED}failed (file error): {e}. Exiting.")
        sys.exit(1)
    print(f"Download {Fore.GREEN}done")

    # Extraction
    spinnerExtract = Spinner("Extracting... ")
    spinnerExtract.start()
    try:
        shutil.unpack_archive(download_file_path, tempDir)
    except Exception as e:
        spinnerExtract.stop()
        print(f"Extraction {Fore.RED}failed: {e}. Exiting.")
        sys.exit(1)
    spinnerExtract.stop()
    print(f"Extraction {Fore.GREEN}done")

    # Copying
    source = next(os.walk(tempDir))[1]
    spinnerCopy = Spinner("Copying... ")
    spinnerCopy.start()
    shutil.copytree(
        os.path.join(tempDir, source[0]), destination_path, dirs_exist_ok=True
    )
    spinnerCopy.stop()
    print(f"Copying {Fore.GREEN}done")

    # Cleanup
    spinnerCleanup = Spinner("Cleanup... ")
    spinnerCleanup.start()
    if keep_temp:
        # just remove the extracted files
        shutil.rmtree(os.path.join(tempDir, source[0]))
    else:
        shutil.rmtree(tempDir)

    spinnerCleanup.stop()
    print(f"Cleanup {Fore.GREEN}done")

    # Finished
    print("-".center(80, "-"))
    print(f"{Fore.GREEN}All tasks finished")

    # write configuration file
    config.read(
        CONFIG_FILE_NAME
    )  # Re-read in case of external changes, though unlikely here
    if not config.has_section("main"):  # Ensure section exists
        config.add_section("main")
    config.set("main", "version", target_filename)
    with open(CONFIG_FILE_NAME, "w") as f:
        config.write(f)

    # run Blender if -r flag present
    if args.run:
        executable_path = ""
        # Use the 'opsys' determined for download, not the current platform.system()
        if opsys == OS_WINDOWS:
            executable_path = os.path.join(destination_path, "blender.exe")
        elif opsys == OS_LINUX:
            executable_path = os.path.join(destination_path, "blender")

        if executable_path and os.path.isfile(executable_path):
            print(f"{Fore.MAGENTA}Starting up Blender from {executable_path}...")
            try:
                subprocess.Popen([executable_path])
            except OSError as e:
                print(f"{Fore.RED}Failed to start Blender: {e}")
        elif executable_path:
            print(f"{Fore.RED}Blender executable not found at {executable_path}")
        else:
            print(f"{Fore.RED}Cannot determine Blender executable for OS '{opsys}'")
