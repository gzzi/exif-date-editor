import PySimpleGUI as sg
from pathlib import Path
import sys
from exif import Image, DATETIME_STR_FORMAT
import logging
from datetime import datetime
import re


def setup_logger(level=logging.DEBUG):
    logfile = 'log_' + datetime.now().strftime('%y%m%d_%H%M%S') + '.txt'
    logging.basicConfig(filename=logfile, level=level)
    root = logging.getLogger()
    root.setLevel(level)
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter()
    handler.setFormatter(formatter)
    handler.setLevel(level)
    root.addHandler(handler)


DATE_DEFAULT_PATTERN = """%Y-%m-%d %H:%M:%S
%Y-%m-%d %H.%M.%S
%Y_%m_%d_%H_%M_%S
%Y_%m_%d_%H.%M.%S
%Y%m%d_%H%M%S
%Y%m%d %H%M%S
%Y-%m-%d
%Y_%m_%d
%Y.%m.%d
%Y%m%d
%Y-%m
%Y_%m
%Y.%m
%Y%m
%Y"""


def guess_date_from_string(txt: str, date_patterns: str) -> datetime:
    input_txt = [txt]
    date_patterns = date_patterns.split('\n')
    if txt and not txt[0].isdigit():
        m = re.search(r"\d", txt)
        if m:
            input_txt.append(txt[m.start():])

    if txt and not txt[-1].isdigit():
        m = re.search(r".*\d", txt)
        if m:
            input_txt.append(txt[:m.end()])

    logging.debug('will search on ' + str(input_txt))
    logging.debug('using patterns: ' + str(date_patterns))
    for el in input_txt:
        for pattern in date_patterns:
            try:
                return datetime.strptime(el, pattern)
            except:
                continue
    logging.debug('no default datetime found for ' + txt)
    raise ValueError('no default datetime found for ' + txt)


def write_new_date(filename: Path, new_date: datetime):
    logging.info('will update selected file ' + str(filename) + ' with ' + str(new_date))

    with open(filename, 'rb') as image_file:
        image = Image(image_file)

    image.datetime_original = new_date.strftime(DATETIME_STR_FORMAT)
    image.datetime = image.datetime_original

    with open(filename, 'wb') as new_image_file:
        new_image_file.write(image.get_file())
    logging.info(status + 'complete')


def has_exif(filename: Path):
    with open(filename, 'rb') as image_file:
        my_image = Image(image_file)
        return my_image.has_exif


def get_img_file_in_folder(folder: Path):
    return [f
            for f in folder.iterdir()
            if f.is_file()
            and f.suffix.lower() in [".jpg", ".jpeg", ".png", ".tiff"]
            and has_exif(f)
            ]


setup_logger()

# First the window layout in 2 columns
file_list_column = [
    [
        sg.Text("Image Folder"),
        sg.In(size=(25, 1), enable_events=True, key="-FOLDER-"),
        sg.FolderBrowse(),
    ],
    [
        sg.Listbox(
            values=[], enable_events=True, size=(40, 20), key="-FILE LIST-", select_mode=sg.LISTBOX_SELECT_MODE_EXTENDED
        )
    ],
    [sg.Text("Datetime guess format strings")],
    [
        sg.Multiline(default_text=DATE_DEFAULT_PATTERN, size=(40, 20), key="-DATE_PATTERN-")
    ],
]

# For now will only show the name of the file that was chosen
image_viewer_column = [
    [sg.Text("File"),
     sg.Text(size=(60, 1), key="-TFILEPATH-")],
    [sg.HSeparator()],  # =====================================
    [sg.Text("Exif date", size=(20, 1)),
     sg.Text(size=(40, 1), key="-TEXIF_DATE-")],
    [sg.Text("Exif date original", size=(20, 1)),
     sg.Text(size=(40, 1), key="-TEXIF_DATE_ORIGINAL-")],
    [sg.Text("Exif date digitalized", size=(20, 1)),
     sg.Text(size=(40, 1), key="-TEXIF_DATE_DIGITALIZED-")],
    [sg.HSeparator()],  # =====================================
    [sg.Text("New original date", size=(20, 1)),
     sg.In(size=(20, 1), key="-TNEW_DATE-"),
     sg.CalendarButton("Edit")
    ],
    [sg.Button("Update", key="-BUPDATE-"),
     sg.Button("Update selected files", key="-BUPDATE_ALL_SELECTED-"),
     sg.Button("Update all files in directory", key="-BUPDATE_ALL_DIR-"),],
    [sg.ProgressBar(10, size=(60, 10), key="-PROGRESS-", visible=False)],
    [sg.Text(size=(60, 1), key="-STATUS-")],
]

# ----- Full layout -----
layout = [
    [
        sg.Column(file_list_column),
        sg.VSeperator(),
        sg.Column(image_viewer_column),
    ],
]

logging.info('Starting...')
window = sg.Window("Image Viewer", layout)

# Run the Event Loop
while True:
    event, values = window.read()
    window["-PROGRESS-"].Update(0,0,False)
    status = ''
    if event == "Exit" or event == sg.WIN_CLOSED:
        break

    try:
        # Folder name was filled in, make a list of files in the folder
        if event == "-FOLDER-":
            folder = values["-FOLDER-"]
            if not folder:
                continue

            # Get list of files in folder
            logging.info('Folder selected:' + folder)
            folder = Path(folder)
            window["-FILE LIST-"].update([f.name for f in get_img_file_in_folder(folder)])

        elif event == "-FILE LIST-":  # A file was chosen from the listbox
            filename = Path(values["-FOLDER-"]) / values["-FILE LIST-"][0]
            logging.info('File selected: ' + str(filename))
            window["-TFILEPATH-"].update(filename)

            with open(filename, 'rb') as image_file:
                my_image = Image(image_file)
                window["-TEXIF_DATE-"].update(
                    datetime.strptime(my_image['datetime'], DATETIME_STR_FORMAT))
                window["-TEXIF_DATE_ORIGINAL-"].update(
                    datetime.strptime(my_image['datetime_original'], DATETIME_STR_FORMAT))
                window["-TEXIF_DATE_DIGITALIZED-"].update(
                    datetime.strptime(my_image['datetime_digitized'], DATETIME_STR_FORMAT))
            try:
                guess_date = guess_date_from_string(filename.stem, values['-DATE_PATTERN-'])
                window["-TNEW_DATE-"].update(guess_date)
            except ValueError:
                pass
        elif event == '-BUPDATE-':
            new_date = values["-TNEW_DATE-"]
            new_date = guess_date_from_string(new_date, values['-DATE_PATTERN-'])

            filename = Path(values["-FOLDER-"]) / values["-FILE LIST-"][0]
            write_new_date(filename, new_date)
            status = 'Success'

        elif event == '-BUPDATE_ALL_DIR-':
            new_date = values["-TNEW_DATE-"]
            new_date = guess_date_from_string(new_date, values['-DATE_PATTERN-'])

            filelist = get_img_file_in_folder(Path(values["-FOLDER-"]))
            progress_bar = window["-PROGRESS-"]
            currProgress = 0
            progress_bar.Update(currProgress, len(filelist), True)
            for filepath in filelist:
                write_new_date(filepath, new_date)
                currProgress = currProgress + 1
                progress_bar.UpdateBar(currProgress)
            status = 'Success'

        elif event == '-BUPDATE_ALL_SELECTED-':
            new_date = values["-TNEW_DATE-"]
            new_date = guess_date_from_string(new_date, values['-DATE_PATTERN-'])

            filelist = [Path(f) for f in values["-FILE LIST-"]]
            progress_bar = window["-PROGRESS-"]
            currProgress = 0
            progress_bar.Update(currProgress, len(filelist), True)
            for filepath in filelist:
                write_new_date(filepath, new_date)
                currProgress = currProgress + 1
                progress_bar.UpdateBar(currProgress)
            status = 'Success'

    except Exception as e:
        logging.warning('Got Exception: ' + str(e))
        window["-STATUS-"].update('Error: ' + str(e))
        pass
    else:
        window["-STATUS-"].update(status)

window.close()
