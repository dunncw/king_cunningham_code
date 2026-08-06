# File: web_automation/path_validator.py

import os

# pyautogui.write() can only type printable ASCII. Anything outside this range
# raises OSError: [Errno 22] Invalid argument when the save path is typed into
# the browser's Save-As dialog.
TYPEABLE_MIN = 32
TYPEABLE_MAX = 126

WINDOWS_ILLEGAL_CHARS = '<>:"/\\|?*'

WINDOWS_RESERVED_NAMES = {
    "CON", "PRN", "AUX", "NUL",
    "COM1", "COM2", "COM3", "COM4", "COM5", "COM6", "COM7", "COM8", "COM9",
    "LPT1", "LPT2", "LPT3", "LPT4", "LPT5", "LPT6", "LPT7", "LPT8", "LPT9",
}

# Windows MAX_PATH. Leave room for the filename appended to the save directory.
MAX_PATH = 260
FILENAME_HEADROOM = 80


def describe_char(ch):
    """Human-readable name for a character that cannot be typed"""
    names = {
        ' ': "non-breaking space",
        '‘': "curly quote", '’': "curly apostrophe",
        '“': "curly double quote", '”': "curly double quote",
        '–': "en dash", '—': "em dash",
        '…': "ellipsis", '°': "degree sign",
        '\t': "tab",
    }
    if ch in names:
        return f"{names[ch]} (U+{ord(ch):04X})"
    if ord(ch) < 32:
        return f"control character (U+{ord(ch):04X})"
    return f"'{ch}' (U+{ord(ch):04X})"


def find_untypeable_chars(text):
    """
    Return list of (index, char) for characters pyautogui cannot type.

    Returns:
        list: [(position, character), ...] - empty if all characters are typeable
    """
    return [
        (i, ch) for i, ch in enumerate(text)
        if ord(ch) < TYPEABLE_MIN or ord(ch) > TYPEABLE_MAX
    ]


def validate_save_location(save_location):
    """
    Validate the output folder before starting a batch.

    Checks that the folder is a real, writable directory whose path can be typed
    into the browser Save-As dialog.

    Args:
        save_location (str): Folder path chosen by the user

    Returns:
        tuple: (is_valid: bool, error_message: str) - message is "" when valid
    """
    if not save_location or not save_location.strip():
        return False, "No save location selected. Choose an output folder."

    if save_location != save_location.strip():
        return False, (
            "Save location has leading or trailing spaces, which Windows cannot open.\n"
            f"Path: '{save_location}'\n"
            "Fix: re-pick the folder using the '...' button instead of typing it."
        )

    bad_chars = find_untypeable_chars(save_location)
    if bad_chars:
        details = ", ".join(describe_char(ch) for _, ch in bad_chars[:5])
        return False, (
            "Save location contains characters that cannot be typed into the "
            "browser's save dialog.\n"
            f"Path: {save_location}\n"
            f"Problem characters: {details}\n"
            "Fix: choose a folder whose full path uses only plain English letters, "
            "numbers, spaces, dashes and underscores."
        )

    if len(save_location) > MAX_PATH - FILENAME_HEADROOM:
        return False, (
            f"Save location path is too long ({len(save_location)} characters).\n"
            f"Path: {save_location}\n"
            f"Fix: use a folder with a shorter path (under "
            f"{MAX_PATH - FILENAME_HEADROOM} characters) so the PDF names still fit."
        )

    if not os.path.exists(save_location):
        return False, (
            f"Save location does not exist: {save_location}\n"
            "Fix: pick the folder again with the '...' button. If it is a network "
            "drive, confirm you are connected to it."
        )

    if not os.path.isdir(save_location):
        return False, (
            f"Save location is a file, not a folder: {save_location}\n"
            "Fix: choose the folder that should hold the PDFs."
        )

    if not os.access(save_location, os.W_OK):
        return False, (
            f"Cannot write to save location: {save_location}\n"
            "Fix: choose a folder you have permission to write to, such as one "
            "inside your Documents folder."
        )

    probe_path = os.path.join(save_location, ".pt61_write_test.tmp")
    try:
        with open(probe_path, "w") as probe:
            probe.write("")
    except OSError as e:
        return False, (
            f"Cannot write to save location: {save_location}\n"
            f"Windows reported: {e.strerror or str(e)}\n"
            "Fix: choose a different folder, or close any program locking this one."
        )
    finally:
        try:
            os.remove(probe_path)
        except OSError:
            pass

    return True, ""


def sanitize_filename(filename, fallback="PT61_record.pdf"):
    """
    Make a filename safe to type into the Save-As dialog.

    Strips Windows-illegal characters and anything pyautogui cannot type, so
    Excel data containing curly apostrophes or accented letters cannot crash the
    save step.

    Args:
        filename (str): Proposed filename built from Excel data
        fallback (str): Name to use if nothing usable survives

    Returns:
        str: Safe filename
    """
    cleaned = "".join(
        ch if TYPEABLE_MIN <= ord(ch) <= TYPEABLE_MAX else "_"
        for ch in filename
    )

    for ch in WINDOWS_ILLEGAL_CHARS:
        cleaned = cleaned.replace(ch, "_")

    # Windows silently drops trailing dots and spaces, producing a name that
    # does not match what we later look for when stacking PDFs.
    cleaned = cleaned.strip(" .")

    # A name like ".pdf" has no stem; splitext reads it as a dotfile, so check
    # for a usable stem before trusting the split.
    stem, ext = os.path.splitext(cleaned)
    if not ext or not stem:
        return fallback

    if stem.upper() in WINDOWS_RESERVED_NAMES:
        cleaned = f"{stem}_file{ext}"

    return cleaned


def validate_output_path(save_location, filename):
    """
    Validate the full path a PDF will be saved to.

    Args:
        save_location (str): Validated output folder
        filename (str): Sanitized filename

    Returns:
        tuple: (is_valid: bool, error_message: str)
    """
    full_path = os.path.normpath(os.path.join(save_location, filename))

    if len(full_path) > MAX_PATH:
        return False, (
            f"The PDF path is too long for Windows ({len(full_path)} characters, "
            f"limit is {MAX_PATH}):\n{full_path}\n"
            "Fix: choose an output folder with a shorter path."
        )

    bad_chars = find_untypeable_chars(full_path)
    if bad_chars:
        details = ", ".join(describe_char(ch) for _, ch in bad_chars[:5])
        return False, (
            f"The PDF path contains characters that cannot be typed:\n{full_path}\n"
            f"Problem characters: {details}"
        )

    return True, ""
