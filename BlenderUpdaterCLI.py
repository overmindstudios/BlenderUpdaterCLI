'''
    Overmind Studios BlenderUpdaterCLI - update Blender to latest buildbot version
    Copyright (C) 2018 by Tobias Kummer for Overmind Studios

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
'''

from colorama import init, Fore
from distutils.dir_util import copy_tree # pylint: disable=no-name-in-module,import-error
from progress.bar import IncrementalBar
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


init(autoreset=True)    # enable Colorama autoreset
failed = False
url = 'https://builder.blender.org/download/'
config = configparser.ConfigParser()
class Spinner:
    busy = False
    delay = 0.1

    @staticmethod
    def spinning_cursor():
        while 1: 
            for cursor in '|/-\\': yield cursor

    def __init__(self, title, delay=None):
        self.spinner_generator = self.spinning_cursor()
        if delay and float(delay): self.delay = delay
        self.title = title

    def spinner_task(self):
        while self.busy:
            sys.stdout.write(self.title + next(self.spinner_generator))
            sys.stdout.flush()
            time.sleep(self.delay)
            sys.stdout.write('\b' * (len(self.title) + 1))
            sys.stdout.flush()

    def start(self):
        self.busy = True
        threading.Thread(target=self.spinner_task).start()

    def stop(self):
        self.busy = False
        time.sleep(self.delay)

parser = argparse.ArgumentParser(description="Update Blender to latest nightly build. (c) 2018 by Tobias Kummer/Overmind Studios.", epilog="example usage: BlenderUpdaterCLI -p C:\\Blender -b 28")
parser.add_argument('-p', '--path', help="Destination path", required=True, type=str)
parser.add_argument('-b', '--blender', help="Desired Blender version, either '-b 279' or '-b 28'", required=True, type=str)
parser.add_argument('-a', '--architecture', help="Architecture ('x86' or 'x64'). If omitted, it will autodetect current architecture.", type=str)
parser.add_argument('-o', '--operatingsystem', help="Operating system. 'osx', 'linux' or 'windows'. If omitted, it will autodetect current OS.", type=str)
parser.add_argument('-y', '--yes', help="Install even if version already installed", action="store_true")
parser.add_argument('-n', '--no', help="Don't install if version already installed", action="store_true")
parser.add_argument('-k', '--keep', help="Keep temporary downloaded archive file", action="store_true")
parser.add_argument('-r', '--run', help="Run downloaded Blender version when finished", action="store_true")
parser.add_argument('-v', '--version', action='version', version='1.1', help="Print program version")
args = parser.parse_args()

print(" SETTINGS ".center(80, "-"))

# check for path validity
if os.path.isdir(args.path):
    dir_ = args.path
    print("Destination path: " + Fore.GREEN + args.path)
else:
    print(Fore.RED + "'" + args.path + "'" + " is an invalid path, make sure directory exists")
    failed = True

# check for desired blender version
if args.blender == "28":
    blender = "2.80"
    print("Blender version: " + Fore.GREEN + "2.8")
elif args.blender == "279":
    blender = "2.79"
    print("Blender version: " + Fore.GREEN + "2.79")
else:
    print(Fore.RED + "Syntax error - use '-b 279' for Blender 2.79 or '-b 28' for Blender 2.8")
    failed = True

# check for desired operating system or autodetect when empty
if args.operatingsystem == "windows":
    opsys = "win"
    extension = "zip"
    print("Operating system: " + Fore.GREEN + "Windows")
elif args.operatingsystem == "osx":
    opsys = "OSX"
    extension = "zip"
    print("Operating system: " + Fore.GREEN + "OSX")
elif args.operatingsystem == "linux":
    opsys = "linux"
    extension = "tar.bz2"
    print("Operating system: " + Fore.GREEN + "Linux")
elif not args.operatingsystem:
    if platform.system() == "Windows":
        opsys = "win"
        extension = "zip"
        print("Operating system: " + Fore.GREEN + "Windows" + Fore.CYAN + " (autodetected)")
    elif platform.system() == "Linux":
        opsys = "linux"
        extension = "tar.bz2"
        print("Operating system: " + Fore.GREEN + "Linux" + Fore.CYAN + " (autodetected)")
    elif platform.system() == "Darwin":
        opsys = "OSX"
        extension = "zip"
        print("Operating system: " + Fore.GREEN + "OSX" + Fore.CYAN + " (autodetected)")
else:
    print(Fore.RED + "Syntax error - use '-o windows', '-o linux' or '-o osx'")
    failed = True

# check for desired architecture or autodetect when empty
if args.architecture == "x86":
    if opsys == "OSX":
        print(Fore.RED + "Error - no 32bit build for OSX")
        failed = True
    elif opsys == "linux":
        arch = "686"
    else:
        arch = "32"
        print("Architecture: " + Fore.GREEN + "32bit")
elif args.architecture == "x64":
    arch = "64"
    print("Architecture: " + Fore.GREEN + "64bit")
elif not args.architecture:
    if "32" in platform.machine():
        if opsys == "OSX":
            print(Fore.RED + "Error - no 32bit build for OSX")
            failed = True
        else:
            arch = "32"
            print("Architecture: " + Fore.GREEN + "32bit" + Fore.CYAN + " (autodetected)")
    elif "64" in platform.machine():
        arch = "64"
        print("Architecture: " + Fore.GREEN + "64bit" + Fore.CYAN + " (autodetected)")
else:
    print(Fore.RED + "Syntax error - please use '-a x86' for 32bit or '-a x64' for 64bit")
    failed = True

#check for --keep flag
if args.keep:
    print(Fore.MAGENTA + "Will keep temporary archive file")
    keep_temp = True
else:
    print(Fore.MAGENTA + "Will NOT keep temporary archive file")
    keep_temp = False

# check for --run flag
if args.run:
    print(Fore.MAGENTA + "Will run Blender when finished")
    will_run = True
else:
    print(Fore.MAGENTA + "Will NOT run Blender when finished")
    will_run = False

print("-".center(80, "-"))

if args.yes and args.no:
    print("You cannot pass both -y and -n flags at the same time!")
    failed = True

# Abort if any error occured during parsing
if failed == True:
    print(Fore.RED + "Input errors detected, aborted (check above for details)")
else:
    print(Fore.GREEN + "All settings valid, proceeding...")
    try:
        req = requests.get(url)
    except Exception:
        print(Fore.RED + "Error connecting to " + url + ", check your internet connection")
    
    filename = re.findall(r'blender-' + blender + r'-\w+-' + opsys + r'[0-9a-zA-Z-._]*' + arch + r'\.' + extension, req.text)

    if os.path.isfile('./config.ini'):
        config.read('config.ini')
        if '2.79' in str(filename[0]):
            try:
                lastversion = config.get('main', 'version279')
            except Exception:   # TODO: Handle errors a bit more gracefully
                lastversion = ''
        elif '2.80' in str(filename[0]):
            try:
                lastversion = config.get('main', 'version28')
            except Exception:
                lastversion = ''
        if lastversion == filename[0]:
            while True:
                if args.yes:
                    break
                elif args.no:
                    print("This version is already installed. -n option present, exiting...")
                    sys.exit()
                else:
                    anyway = str(input('This version is already installed. Continue anyways? [Y]es or [N]o: ')).lower()
                    if anyway == 'n':
                        sys.exit()
                    elif anyway == 'y':
                        break
                    print("Invalid choice, try again!")
            
    else:
        config.read('config.ini')
        config.add_section('main')
        with open('config.ini', 'w') as f:
            config.write(f)

    if(not keep_temp):
        if os.path.isdir('./blendertemp'):
            shutil.rmtree('./blendertemp')
    os.makedirs('./blendertemp', exist_ok=True)
    dir_ = os.path.join(args.path, '')
    print("Downloading " + filename[0])
    chunkSize = 10240
    try:
        r = requests.get(url + filename[0], stream=True)
        with open("./blendertemp/" + filename[0], 'wb') as f:
            pbar = IncrementalBar('Downloading', max=int(r.headers['Content-Length']) / chunkSize, suffix='%(percent)d%%')
            for chunk in r.iter_content(chunk_size=chunkSize): 
                if chunk: # filter out keep-alive new chunks
                    pbar.next()
                    f.write(chunk)
            pbar.finish()
    except Exception:
        print('Download' + Fore.RED + 'failed, please try again. Exiting.')
        sys.exit()
    print('Download ' + Fore.GREEN + 'done')

    # Extraction
    spinnerExtract = Spinner('Extracting... ')
    spinnerExtract.start()
    try:
        shutil.unpack_archive("./blendertemp/" + filename[0], './blendertemp/')
    except Exception:
        print('Extraction ' + Fore.RED + 'failed, please try again. Exiting.')
        sys.exit()
    spinnerExtract.stop()
    print('Extraction ' + Fore.GREEN + 'done')

    # Copying
    source = next(os.walk('./blendertemp/'))[1]
    spinnerCopy = Spinner('Copying... ')
    spinnerCopy.start()
    copy_tree(os.path.join('./blendertemp/', source[0]), dir_)
    spinnerCopy.stop()
    print('Copying ' + Fore.GREEN + 'done')
    
    if opsys == 'OSX':
        BlenderOSXPath = os.path.join('"' + dir_ + "blender.app/Contents/MacOS/blender" + '"')
        os.system("chmod +x " + BlenderOSXPath)

    # Cleanup
    spinnerCleanup = Spinner('Cleanup... ')
    spinnerCleanup.start()
    if(keep_temp):
        #just remove the extracted files
        shutil.rmtree(os.path.join('./blendertemp/', source[0]))        
    else:
        shutil.rmtree('./blendertemp')

    spinnerCleanup.stop()
    print('Cleanup ' + Fore.GREEN + 'done')

    # Finished
    print("-".center(80, "-"))
    print(Fore.GREEN + "All tasks finished")

    # write configuration file
    config.read('config.ini')
    if '2.80' in str(filename[0]):
        config.set('main', 'version28', filename[0])
    elif '2.79' in str(filename[0]):
        config.set('main', 'version279', filename[0])
    with open('config.ini', 'w') as f:
        config.write(f)

    # run Blender if -r flag present
    if args.run:
        print(Fore.MAGENTA + "Starting up Blender...")
        opsys = platform.system()
        if opsys == 'Windows':
            p = subprocess.Popen(os.path.join('"' + dir_ + "\\blender.exe" + '"'))
        elif opsys == 'OSX':
            p = subprocess.Popen(BlenderOSXPath)
        elif opsys == 'Linux':
            p = subprocess.Popen(os.path.join(dir_ + '/blender'))
        
