import wcwidth

def width(str):
    """
    Return the width of a string in terminal columns.
    """
    if not str:
        return 0
    return wcwidth.wcswidth(str)

def truncate(str, _width):
    """
    Return a truncated version of a string that fits in a given width.
    """
    if width(str) > _width:
        return lineview(str, _width - 3)[0] + "..."
    return str

def lineview(line: str, width: int):
    """
    Split a string into a list of substrings that have the same or less width.
    """
    list = []
    chunk = ""
    count = 0
    for c in line:
        cw = wcwidth.wcwidth(c)
        if count + cw > width:
            list.append(chunk)
            chunk = c
            count = cw
        else:
            chunk += c
            count += cw
    if chunk:
        list.append(chunk)
    if not list or count == width:
        list.append("")
    return list

def linesview(lines: list[str], width: int, start: int = None, end: int = None):
    """
    Split a list of strings into a list of tuples containing substrings, line index and fragment index.
    """
    result = []
    start = 0 if start == None else max(0, min(start, len(lines)))
    end = len(lines) if end == None else min(end, len(lines))
    for i in range(start, end):
        line = lines[i]
        fragments = lineview(line, width)
        for j in range(len(fragments)):
            str = fragments[j]
            result.append((str, i, j))
    return result
