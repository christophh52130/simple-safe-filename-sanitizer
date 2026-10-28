# simple-safe-filename-sanitizer

Replaces or removes characters invalid on Windows, macOS, and Linux to produce a portable filename string.

```python
from simple_safe_filename_sanitizer import sanitize_filename

safe = sanitize_filename('re:p/o?rt*.txt')
print(safe)  # re_p_o_rt_.txt
```

## Why

Saving user-supplied strings as filenames breaks the moment someone passes a colon on Windows, a NUL byte on Linux, or a trailing dot that the Win32 API silently strips. This library collapses all three platforms' rules into a single function so the output is a filename you can write to disk without a `ValueError` or a silent rename.

The function sanitizes a **basename only**. Forward and back slashes in the input are treated as forbidden characters and replaced — they never create path separators. If you need to sanitize a full path, split it into components and sanitize each one.

## Edge cases

Windows reserves names like `CON`, `PRN`, `AUX`, `NUL`, and `COM1`–`COM9` regardless of extension. The library prefixes these exact tokens with an underscore (`CON` → `_CON`) but does **not** treat `CON.txt` as reserved, because the reserved-word check applies to the whole name. This is the one interpretation worth stating plainly: if your input is `CON.txt`, it survives unchanged.

## Performance

The window keeps a bounded buffer, so `push` is constant time and memory does not
grow with the length of the stream. `peak` and `trough` are linear in the window
size, which is the trade that keeps `push` cheap.

## Limitations

Values are coerced to floats, so very large integers lose precision. If you need
exact integer aggregates over a window, this is the wrong tool.

