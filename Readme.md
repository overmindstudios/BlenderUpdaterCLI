[![GPL3 License](https://img.shields.io/badge/license-GPL3-blue.svg)](https://github.com/overmindstudios/BlenderUpdater/blob/master/LICENSE) 
[![Downloads](https://img.shields.io/github/downloads/overmindstudios/BlenderUpdaterCLI/total)](https://img.shields.io/github/downloads/overmindstudios/BlenderUpdaterCLI/total)
[![ko-fi](https://www.ko-fi.com/img/githubbutton_sm.svg)](https://ko-fi.com/G2G5149IX)

# BlenderUpdaterCLI
## Python 3 command line tool to update Blender to the latest buildbot version
If you want to support me, feel free to donate on Ko-Fi!

<a href="https://ko-fi.com/tobkum"><img src="https://az743702.vo.msecnd.net/cdn/kofi1.png?v=2" width="150"></a>
## Usage
### Minimal example:
```python BlenderUpdaterCLI.py -b 2.82 -p PATH```

#### Required flags:
* ```-p``` PATH (add a valid path where you want the downloaded archive to be extracted to)
* ```-b``` BLENDER (Desired Blender version - for example ```-b 2.82```)

#### Additional flag:
* ```-o``` OPERATINGSYSTEM (```windows```, ```linux``` or ```osx```) 

If this flag is omitted, the script autodetects the OS it's currently running on.

#### Optional flags:
* ```-r``` runs Blender after finishing
* ```-y``` installs even when version on server matches last installed version
* ```-n``` exits if last installed version matches version to be downloaded
* ```-k``` keeps temporary archive download.
* ```-t``` TEMP (Temporary file path. "./blendertemp" is the default. Unless -k specified it will be removed at the end of installation)
* ```-h``` shows help text
* ```-v``` shows version of the tool

### Verbose example:
```python BlenderUpdaterCLI.py -p C:\Tools\Blender -b 2.82 -o windows -a x64```

This will download the latest build of Blender 2.82 for 64bit Windows and copy it to C:\Tools\Blender

## Screenshot
![Screenshot](https://raw.githubusercontent.com/overmindstudios/BlenderUpdaterCLI/master/screenshot.png)
