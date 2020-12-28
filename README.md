
# Exif From Path

This tool allows modifying exif original date of picture. Goal was to fix scanned images incorrect date. Once date is 
correct, it fix sorting issues on Google Photos.

The tool try to guess date from file name and already fill edit box with the value if it found something that match one
of the python datetime format strings given in lower left edit filed (see [python doc](https://docs.python.org/3.7/library/datetime.html#strftime-and-strptime-behavior)).
Note that first match is taken so order matter.

Note if the file doesn't have exif data, it will not be possible to edit it and the file will not be shown.

**Warning** Use at Your Own Risk

![Screen shot](doc\screenshot.png)