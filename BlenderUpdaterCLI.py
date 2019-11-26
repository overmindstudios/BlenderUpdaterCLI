"""
    Overmind Studios BlenderUpdaterCLI - update Blender to latest buildbot version
    Copyright (C) 2018-2019 by Tobias Kummer for Overmind Studios

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
from distutils.dir_util import copy_tree
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


appversion = "v1.5"
init(autoreset=True)  # enable Colorama autoreset
failed = False
url = "https://builder.blender.org/download/"
config = configparser.ConfigParser()
updateurl = (
    "https://api.github.com/repos/overmindstudios/BlenderUpdaterCLI/releases/latest"
)


class Spinner:
    busy = False
    delay = 0.1

    @staticmethod
    def spinning_cursor():
        while 1:
            for cursor in "|/-\\":
                yield cursor

    def __init__(self, title, delay=None):
        self.spinner_generator = self.spinning_cursor()
        if delay and float(delay):
            self.delay = delay
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
    description="Update Blender to latest nightly build. (c) 2018-2019 by Tobias Kummer/Overmind Studios.",
    epilog="example usage: BlenderUpdaterCLI -b 2.82 -p C:\\Blender",
)
parser.add_argument("-p", "--path", help="Destination path", required=True, type=str)
parser.add_argument(
    "-o",
    "--operatingsystem",
    help="Operating system. 'osx', 'linux' or 'windows'. If omitted, it will try to autodetect current OS.",
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
    "-b",
    "--blender",
    help="Desired Blender version - for example '-b 2.82'",
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
        quit()
except Exception:
    print(" NOTICE ".center(80, "-"))
    print("Cannot check for updates.")
    raise Exception


# Start update process

print(" SETTINGS ".center(80, "-"))

# check for path validity
if os.path.isdir(args.path):
    dir_ = args.path
    print(f"Destination path: {Fore.GREEN}{args.path}")
else:
    print(Fore.RED + f"'{args.path}' is an invalid path, make sure directory exists")
    failed = True

# check for desired blender version
blender = args.blender

# check for desired operating system or autodetect when empty
if args.operatingsystem == "windows":
    opsys = "win"
    extension = "zip"
    print(f"Operating system: {Fore.GREEN}{opsys}")
elif args.operatingsystem == "osx":
    opsys = "OSX"
    extension = "zip"
    print(f"Operating system: {Fore.GREEN}{opsys}")
elif args.operatingsystem == "linux":
    opsys = "linux"
    extension = "tar.bz2"
    print(f"Operating system: {Fore.GREEN}{opsys}")

# autodetect OS
elif not args.operatingsystem:
    if platform.system() == "Windows":
        opsys = "win"
        extension = "zip"
    elif platform.system() == "Linux":
        opsys = "linux"
        extension = "tar.bz2"
    elif platform.system() == "Darwin":
        opsys = "OSX"
        extension = "zip"
    print(f"Operating system: {Fore.GREEN}{opsys}{Fore.CYAN} (autodetected)")

else:
    print(f"{Fore.RED}Syntax error - use '-o windows', '-o linux' or '-o osx'")
    failed = True

# Only 64bit supported for all OS in experimental builds
arch = "64"

# check for --keep flag
if args.keep:
    print(f"{Fore.MAGENTA}Will keep temporary archive file")
    keep_temp = True
else:
    print(f"{Fore.MAGENTA}Will NOT keep temporary archive file")
    keep_temp = False

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
if failed is True:
    print(f"{Fore.RED}Input errors detected, aborted (check above for details)")
else:
    try:
        req = requests.get(url)
    except Exception:
        print(f"{Fore.RED}Error connecting to {url}, check your internet connection")

    try:
        filename = re.findall(
            r"blender-"
            + blender
            + r"-\w+-"
            + opsys
            + r"[0-9a-zA-Z-._]*"
            + arch
            + r"\."
            + extension,
            req.text,
        )
    except Exception:
        print(
            f"{Fore.RED}No valid Blender version specified ({args.blender} not found)"
        )
        sys.exit()

    if os.path.isfile("./config.ini"):
        config.read("./config.ini")
        try:
            lastversion = config.get("main", "version")
        except Exception:  # TODO: Handle errors a bit more gracefully
            lastversion = ""

        try:
            if lastversion == filename[0]:
                while True:
                    if args.yes:
                        break
                    elif args.no:
                        print(
                            "This version is already installed. -n option present, exiting..."
                        )
                        sys.exit()
                    else:
                        anyway = str(
                            input(
                                "This version is already installed. Continue anyways? [Y]es or [N]o: "
                            )
                        ).lower()
                        if anyway == "n":
                            sys.exit()
                        elif anyway == "y":
                            break
                        print("Invalid choice, try again!")
        except Exception:
            print(
                f"{Fore.RED}No valid Blender version specified ({args.blender} not found)"
            )
            sys.exit()

    else:
        config.read("config.ini")
        config.add_section("main")
        with open("config.ini", "w") as f:
            config.write(f)

    if not keep_temp:
        if os.path.isdir("./blendertemp"):
            shutil.rmtree("./blendertemp")
    os.makedirs("./blendertemp", exist_ok=True)
    dir_ = os.path.join(args.path, "")
    print(f"{Fore.GREEN}All settings valid, proceeding...")
    print(f"Downloading {filename[0]}")
    chunkSize = 10240
    try:
        r = requests.get(url + filename[0], stream=True)
        with open("./blendertemp/" + filename[0], "wb") as f:
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
    except Exception:
        print(f"Download {Fore.RED}failed, please try again. Exiting.")
        sys.exit()
    print(f"Download {Fore.GREEN}done")

    # Extraction
    spinnerExtract = Spinner("Extracting... ")
    spinnerExtract.start()
    try:
        shutil.unpack_archive("./blendertemp/" + filename[0], "./blendertemp/")
    except Exception:
        print(f"Extraction {Fore.RED}failed, please try again. Exiting.")
        sys.exit()
    spinnerExtract.stop()
    print(f"Extraction {Fore.GREEN}done")

    # Copying
    source = next(os.walk("./blendertemp/"))[1]
    spinnerCopy = Spinner("Copying... ")
    spinnerCopy.start()
    copy_tree(os.path.join("./blendertemp/", source[0]), dir_)
    spinnerCopy.stop()
    print(f"Copying {Fore.GREEN}done")

    opsys = platform.system()
    if opsys == "darwin":
        BlenderOSXPath = os.path.join(
            '"' + dir_ + "\\blender.app/Contents/MacOS/blender" + '"'
        )
        os.system(f"chmod +x {BlenderOSXPath}")

    # Cleanup
    spinnerCleanup = Spinner("Cleanup... ")
    spinnerCleanup.start()
    if keep_temp:
        # just remove the extracted files
        shutil.rmtree(os.path.join("./blendertemp/", source[0]))
    else:
        shutil.rmtree("./blendertemp")

    spinnerCleanup.stop()
    print(f"Cleanup {Fore.GREEN}done")

    # Finished
    print("-".center(80, "-"))
    print(f"{Fore.GREEN}All tasks finished")

    # write configuration file
    config.read("config.ini")
    config.set("main", "version", filename[0])
    with open("config.ini", "w") as f:
        config.write(f)

    # run Blender if -r flag present
    if args.run:
        print(f"{Fore.MAGENTA}Starting up Blender...")
        if opsys == "Windows":
            p = subprocess.Popen(os.path.join('"' + dir_ + "\\blender.exe" + '"'))
        elif opsys == "darwin":
            p = subprocess.Popen(BlenderOSXPath)
        elif opsys == "Linux":
            p = subprocess.Popen(os.path.join(dir_ + "/blender"))
