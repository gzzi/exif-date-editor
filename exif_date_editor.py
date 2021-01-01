#!/usr/bin/env python3
# Graphic application to edit exif date of multiple images files
import PySimpleGUI as sg
from pathlib import Path
import sys
from exif import Image, DATETIME_STR_FORMAT
import logging
from datetime import datetime
import re


def init_logger(level=logging.DEBUG, to_file=True):
    if to_file:
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


def guess_date_from_string(txt: str, date_patterns: str = DATE_DEFAULT_PATTERN) -> datetime:
    date_patterns = date_patterns.split('\n')

    def test_all_pattern(input_txt: str):
        logging.debug('will search on ' + input_txt)
        for pattern in date_patterns:
            try:
                return datetime.strptime(input_txt, pattern)
            except ValueError:
                continue
        raise ValueError('no default datetime found for ' + txt)

    if not txt:
        raise ValueError('empty string')

    try:
        return test_all_pattern(txt)
    except ValueError:
        pass

    # look for biggest string with one delimiter start/ending with digit
    m = re.findall(r"(?:\d+.?)+\d", txt)
    if m:
        txt = max(m, key=len)
        try:
            return test_all_pattern(txt)
        except ValueError:
            pass

    logging.debug('no default datetime found for ' + txt)
    raise ValueError('no default datetime found for ' + txt)


def write_new_date(filename: Path, new_date: datetime):
    logging.info('update file ' + str(filename) + ' with ' + str(new_date))
    with open(filename, 'rb') as image_file:
        image = Image(image_file)

    new_date_str = new_date.strftime(DATETIME_STR_FORMAT)

    image.datetime_original = new_date_str
    image.datetime = new_date_str

    with open(filename, 'wb') as new_image_file:
        new_image_file.write(image.get_file())


def get_img_file_in_folder(folder: Path) -> list:
    return [f
            for f in folder.iterdir()
            if f.is_file()
            and f.suffix.lower() in [".jpg", ".jpeg"]
            ]


def init_window() -> sg.Window:
    sg.theme('SystemDefault1')

    WINDOW_LEFT_COLUMN = [
        [sg.Text("Image Folder"),
         sg.In(size=(25, 1), enable_events=True, key="-FOLDER-"),
         sg.FolderBrowse(),
        ],
        [sg.Listbox(values=[], enable_events=True, size=(40, 20), key="-FILE LIST-",
                    select_mode=sg.LISTBOX_SELECT_MODE_EXTENDED )
        ],
        [sg.Text("Datetime guess format strings")],
        [sg.Multiline(default_text=DATE_DEFAULT_PATTERN, size=(40, 20), key="-DATE_PATTERN-")],
    ]

    WINDOW_RIGHT_COLUMN = [
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

    WINDOW_LAYOUT = [
        [
            sg.Column(WINDOW_LEFT_COLUMN),
            sg.VSeperator(),
            sg.Column(WINDOW_RIGHT_COLUMN),
        ],
    ]
    return sg.Window("Exif date editor", WINDOW_LAYOUT)


def handle_events(window: sg.Window):
    while True:
        event, values = window.read()
        window["-PROGRESS-"].Update(0, 0, False)
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

            elif event == '-BUPDATE-':
                new_date = values["-TNEW_DATE-"]
                new_date = guess_date_from_string(new_date, values['-DATE_PATTERN-'])

                filename = Path(values["-FOLDER-"]) / values["-FILE LIST-"][0]
                write_new_date(filename, new_date)
                status = 'Success'

            elif event == '-BUPDATE_ALL_DIR-':
                new_date = values["-TNEW_DATE-"]
                new_date = guess_date_from_string(new_date, values['-DATE_PATTERN-'])

                files = get_img_file_in_folder(Path(values["-FOLDER-"]))
                progress_bar: sg.ProgressBar = window["-PROGRESS-"]
                curr_progress = 0
                progress_bar.Update(curr_progress, len(files), True)
                for filepath in files:
                    write_new_date(filepath, new_date)
                    curr_progress = curr_progress + 1
                    progress_bar.UpdateBar(curr_progress)
                status = 'Success'

            elif event == '-BUPDATE_ALL_SELECTED-':
                new_date = values["-TNEW_DATE-"]
                new_date = guess_date_from_string(new_date, values['-DATE_PATTERN-'])

                files = [Path(values["-FOLDER-"]) / f for f in values["-FILE LIST-"]]
                progress_bar: sg.ProgressBar = window["-PROGRESS-"]
                curr_progress = 0
                progress_bar.Update(curr_progress, len(files), True)
                for filepath in files:
                    write_new_date(filepath, new_date)
                    curr_progress = curr_progress + 1
                    progress_bar.UpdateBar(curr_progress)
                status = 'Success'

            if event == "-FILE LIST-" or event.startswith('-BUPDATE'):
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

        except Exception as e:
            logging.warning('Got Exception: ' + str(e))
            window["-STATUS-"].update('Error: ' + str(e))
            pass
        else:
            window["-STATUS-"].update(status)


if __name__ == "__main__":
    init_logger()
    logging.info('Starting...')
    window = init_window()
    handle_events(window)
    window.close()
