import argparse
from colorama import init, Fore
import platform
from os import path
import tqdm

init(autoreset=True)    # enable Colorama autoreset
failed = False

parser = argparse.ArgumentParser(description="Update Blender to latest nightly build.", epilog="example usage: BlenderUpdaterCLI -p C:\\Blender -b 28")
parser.add_argument('-p','--path', help="Destination path", required=True, type=str)
parser.add_argument('-b', '--blender', help="Desired Blender version, either 279 or 28", required=True, type=str)
parser.add_argument('-a','--architecture', help="Architecture ('x86' or 'x64'). If omitted, it will autodetect current architecture.", required=False, type=str)
parser.add_argument('-o','--operatingsystem', help="Operating system. 'osx', 'linux' or 'windows'. If omitted, it will autodetect current OS.", type=str)
parser.add_argument('-v', '--version', action='version', version='0.1', help="Print program version")
args = parser.parse_args()

print(" SETTINGS ".center(80, "-"))

# check for path validity
if path.isdir(args.path):
    print("Destination path: " + Fore.GREEN + args.path)
else:
    print(Fore.RED + "'" + args.path + "'" + " is an invalid path, please make sure directory exists")
    failed = True

# check for desired blender version
if args.blender == "28":
    blender = "2.8"
    print("Blender version: " + Fore.GREEN + blender)
elif args.blender == "279":
    blender = "2.79"
    print("Blender version: " + Fore.GREEN + blender)
else:
    print(Fore.RED + "Syntax error - please use '-b 279' for Blender 2.79 or '-b 28' for Blender 2.8")
    failed = True

# check for desired operating system or autodetect when empty
if args.operatingsystem == "windows":
    print("Operating system: " + Fore.GREEN + "Windows")
elif args.operatingsystem == "osx":
    print("Operating system: " + Fore.GREEN + "OSX")
elif args.operatingsystem == "linux":
    print("Operating system: " + Fore.GREEN + "Linux")
elif not args.operatingsystem:
    if platform.system() == "Windows":
        print("Operating system: " + Fore.GREEN + "Windows " + Fore.CYAN + "(autodetected)")
    elif platform.system() == "Linux":
        print("Operating system: " + Fore.GREEN + "Linux " + Fore.CYAN + "(autodetected)")
    elif platform.system() == "Darwin":
        print("Operating system: " + Fore.GREEN + "OSX " + Fore.CYAN + "(autodetected)")
else:
    print(Fore.RED + "Syntax error - please use '-o windows', '-o linux' or '-o osx'")
    failed = True


# check for desired architecture or autodetect when empty
if args.architecture == "x86":
    if args.operatingsystem == "osx":
        print(Fore.RED + "Error - no 32bit build for OSX")
        failed = True
    else:
        print("Architecture: " + Fore.GREEN + "32bit")
elif args.architecture == "x64":
    print("Architecture: " + Fore.GREEN + "64bit")
elif not args.architecture:
    if "32" in platform.machine():
        print("Architecture: " + Fore.GREEN + "32bit " + Fore.CYAN + "(autodetected)")
    elif "64" in platform.machine():
        print("Architecture: " + Fore.GREEN + "64bit " + Fore.CYAN + "(autodetected)")
else:
    print(Fore.RED + "Syntax error - please use '-a x86' for 32bit or '-a x64' for 64bit")
    failed = True

print("-".center(80, "-"))

if failed == True:
    print(Fore.RED + "Input errors detected, aborted (check above for details)")
    quit()
else:
    print(Fore.GREEN + "All settings valid, proceeding...")