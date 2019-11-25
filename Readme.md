# BlenderUpdaterCLI
## Python 3 command line tool to update Blender to the latest buildbot version
If you want to support me, feel free to donate on Ko-Fi!

<a href="https://ko-fi.com/tobkum"><img src="https://az743702.vo.msecnd.net/cdn/kofi1.png?v=2" width="150"></a>
## Usage
### Minimal example:
```python BlenderUpdaterCLI.py -b 281 -p PATH```

#### Required flags:
* ```-p``` PATH (add a valid path where you want the downloaded archive to be extracted to)
* ```-b``` BLENDER (Desired Blender version - for example ```-b 2.82```)

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
```python BlenderUpdaterCLI.py -p C:\Tools\Blender -b 281 -o windows -a x64```

This will download the latest build of Blender 2.8 for 64bit Windows and copy it to C:\Tools\Blender

## Screenshot
![Screenshot](https://raw.githubusercontent.com/overmindstudios/BlenderUpdaterCLI/master/screenshot.png)
