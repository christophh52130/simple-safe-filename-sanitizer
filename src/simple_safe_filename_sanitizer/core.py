from __future__ import annotations

import re
import unicodedata

# Characters forbidden on Windows. These are illegal regardless of position
# in the filename and cannot be escaped or quoted.
_WIN_FORBIDDEN = set('<>:"/\\|?*')

# Windows reserves these exact names (case-insensitive) in every directory.
# They are commonly produced by audio rippers and device-naming tools, so we
# must handle them even though they contain only "valid" characters.
_WIN_RESERVED = {
    "CON",
    "PRN",
    "AUX",
    "NUL",
    *(f"COM{i}" for i in range(1, 10)),
    *(f"LPT{i}" for i in range(1, 10)),
}

# Filenames consisting only of dots are directory-navigation tokens on
# Windows (".", "..") or rejected outright on Linux. We collapse them.
_DOTS_ONLY = re.compile(r"^\.+$")

# After substitution, runs of spaces carry no information and can collide
# visually. Collapse them to a single space for readability.
_RUN = re.compile(r" +")

# Trailing dots and spaces are silently stripped by the Windows shell and
# the Win32 API, which means "file.txt   ." and "file.txt" collide. We must
# remove them ourselves so the sanitized name is stable.
_TRAILING = re.compile(r"[. ]+$")

# Leading spaces have no meaning on any platform but can survive round-trips
# through archives. Strip them.
_LEADING = re.compile(r"^ +")

_MAX_LEN = 200
_FALLBACK = "untitled"


def _sanitize_replacement(replacement: str) -> str:
    """Sanitize the replacement string without recursing."""
    if replacement == "":
        return ""
    rep_chars: list[str] = []
    for ch in unicodedata.normalize("NFC", replacement):
        if ch == "/" or ch == "\\":
            rep_chars.append("_")
        elif ch in _WIN_FORBIDDEN:
            rep_chars.append("_")
        elif ch in "\x00\n\r\t":
            rep_chars.append("_")
        else:
            rep_chars.append(ch)
    rep = "".join(rep_chars)
    if rep == "":
        rep = "_"
    return rep


def sanitize_filename(name: str, replacement: str = "_") -> str:
    """Return a portable, single-component filename derived from *name*.

    The function replaces every character that is illegal on Windows,
    macOS, or Linux, normalizes Unicode to NFC form, trims whitespace that
    the Windows shell silently discards (leading spaces, trailing dots and
    spaces), collapses runs of separators, shortens over-long names, and
    guarantees a non-empty result that is not a Windows reserved name.

    Parameters
    ----------
    name:
        The candidate filename. May be an empty string or contain any
        Unicode characters.
    replacement:
        String substituted for each forbidden character. Must itself be a
        legal filename fragment; it is passed through the sanitizer if it is
        not, so you cannot smuggle illegal characters in through it.

    Returns
    -------
    str
        A filename safe for use on Windows, macOS, and Linux. Never empty.

    Notes
    -----
    Only the *basename* is considered. A forward slash or backslash in the
    input is treated as an illegal character and replaced; it does **not**
    create a path separator. If you need to sanitize an entire path, split
    it yourself and sanitize each component.
    """
    if not isinstance(name, str):
        raise TypeError("name must be a str")
    if not isinstance(replacement, str):
        raise TypeError("replacement must be a str")

    # Normalize first so that combining sequences collapse before we scan for
    # forbidden characters — otherwise a combining mark could survive attached
    # to the replacement.
    text = unicodedata.normalize("NFC", name)

    rep = _sanitize_replacement(replacement)

    out_chars: list[str] = []
    for ch in text:
        if ch == "/" or ch == "\\":
            out_chars.append(rep)
        elif ch in _WIN_FORBIDDEN:
            out_chars.append(rep)
        elif ch in "\x00\n\r\t":
            # NUL is illegal on Linux; the control characters \n, \r, \t are
            # legal on POSIX but break shells and scripts. Treat them as
            # forbidden for portability.
            out_chars.append(rep)
        else:
            out_chars.append(ch)
    text = "".join(out_chars)

    text = _RUN.sub(" ", text)
    text = _LEADING.sub("", text)
    text = _TRAILING.sub("", text)

    if _DOTS_ONLY.match(text):
        text = ""

    if text.upper() in _WIN_RESERVED:
        text = "_" + text

    if len(text) > _MAX_LEN:
        text = text[:_MAX_LEN].rstrip()
        text = _TRAILING.sub("", text)

    if text == "":
        text = _FALLBACK

    # Edge case: a name that was *only* forbidden characters becomes only
    # the replacement, which might itself be dots-only (e.g. rep="."). Guard
    # a second time so we never return a dots-only or empty string.
    if _DOTS_ONLY.match(text) or text.upper() in _WIN_RESERVED or text == "":
        text = _FALLBACK

    return text
