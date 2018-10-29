# BlenderUpdaterCLI
## Python 3 command line tool to update Blender to the latest buildbot version
## Usage
### Minimal example:
```python BlenderUpdaterCLI.py -b BLENDERVERSION -p PATH```

where BLENDERVERSION is either ```279``` or ```28``` and PATH is an existing directory on your hard drive

#### Additional flags:
* ```-o``` OPERATINGSYSTEM (```windows```, ```linux``` or ```osx```) 
* ```-a``` ARCHITECTURE (```x86``` for 32bit or ```x64``` for 64bit). 

If those two flags above are omitted, the script autodetects the OS and architecture it's currently running on.
* ```-r``` runs Blender after finishing
* ```-h``` shows help text
* ```-v``` shows version of the tool

### Verbose example:
```python BlenderUpdaterCLI.py -b 28 -p C:\Tools\Blender -o windows -a x64```

This will download the latest build of Blender 2.8 for 64bit Windows and copy it to C:\Tools\Blender

## Screenshot
![Screenshot](https://raw.githubusercontent.com/overmindstudios/BlenderUpdaterCLI/master/screenshot.png)