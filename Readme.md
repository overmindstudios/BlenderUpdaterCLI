# BlenderUpdaterCLI
## Python 3 command line tool to update Blender to the latest buildbot version
[![Coffee](https://www.buymeacoffee.com/assets/img/custom_images/black_img.png)](https://www.buymeacoffee.com/tobkum)
## Usage
### Minimal example:
```python BlenderUpdaterCLI.py -p PATH```

#### Additional flags:
* ```-o``` OPERATINGSYSTEM (```windows```, ```linux``` or ```osx```) 
* ```-a``` ARCHITECTURE (```x86``` for 32bit or ```x64``` for 64bit). 

If those two flags above are omitted, the script autodetects the OS and architecture it's currently running on.

#### Optional flags:
* ```-r``` runs Blender after finishing
* ```-y``` installs even when version on server matches last installed version
* ```-n``` exits if last installed version matches version to be downloaded
* ```-k``` keeps temporary archive download. 
* ```-h``` shows help text
* ```-v``` shows version of the tool

### Verbose example:
```python BlenderUpdaterCLI.py -p C:\Tools\Blender -o windows -a x64```

This will download the latest build of Blender 2.8 for 64bit Windows and copy it to C:\Tools\Blender

## Screenshot
![Screenshot](https://raw.githubusercontent.com/overmindstudios/BlenderUpdaterCLI/master/screenshot.png)
