import PyInstaller.__main__

PyInstaller.__main__.run([
    'exif_date_editor.py',
    #'--paths', R'C:\Program Files (x86)\Python37-32',
    '--onefile',  # fix issue with python.dll
    '--noconfirm',  # will overwrite output exe
    '--windowed'
])