# oy3o

[![PyPI version](https://badge.fury.io/py/oy3o.svg)](https://badge.fury.io/py/oy3o)
[中文版 README (Chinese README)](README.zh-CN.md)

A Python library for building Text User Interfaces (TUIs), providing interactive components based on `curses`, such as a multi-line text editor and flexible input handling.

**Note:** This library depends on Python's `curses` module, which is typically part of the standard library on Unix-like systems (Linux, macOS) but is not available by default on Windows. Windows users might need to install the `windows-curses` package (`pip install windows-curses`), but compatibility may require further testing.

## Features

*   **Interactive Components:**
    *   A `curses`-based editable text box/editor (`Editor`).
    *   Supports basic text navigation (up/down/left/right, home/end).
    *   Handles text wrapping and view scrolling.
*   **Advanced Input Handling (`oy3o.input`):**
    *   Listens for and responds to individual key presses, including modifier keys (Ctrl).
    *   Handles special keys (arrow keys, Enter, Backspace, etc.).
    *   Captures mouse events: clicks, scrolls (up/down), and movement (including coordinates and modifier states like Ctrl+Alt+Move).
    *   Bind functions to specific key, mouse, or character events using `onkey`, `onmouse`, `onchar`.
    *   Provides a main input loop (`listen()`) to process the event stream.
    *   **Note:** `input.ALT` is currently mainly intended for mouse events, as Alt + letter keys are often intercepted by the OS or terminal.
*   **Wide Character Support:** Integrates `wcwidth` for correct handling of wide characters (e.g., CJK characters).
*   **Utilities (`oy3o._`):** Includes helpful utilities and decorators like event subscription (`@subscribe`), throttling (`@throttle`), debouncing (`@debounce`), task management (`Task`, `Timer`), metaprogramming helpers (`@members`, `@template`, `Proxy`), and more. (See details below).
*   **Token Counting:** Integrates `tiktoken` for token counting.
*   **System Clipboard:** Supports copy/paste operations via `pyperclip`.

## Installation

You can install `oy3o` from PyPI using pip:

```bash
pip install oy3o
```

## Basic Usage - Editor (`oy3o.editor`)

Here's a simple example demonstrating how to start a basic `oy3o` editor in the terminal:

```python
import curses
from oy3o.editor import Editor

def main(stdscr):
    # Create Editor instance
    # Editor draws and manages its area within the given window
    # based on top/bottom/left/right margins.
    editor = Editor(
        window=stdscr,       # Parent window is stdscr
        top=1,               # Top margin (starts at row 1 of stdscr)
        bottom=1,            # Bottom margin (1 row from stdscr bottom)
        left=1,              # Left margin (starts at col 1 of stdscr)
        right=1,             # Right margin (1 col from stdscr right)
        text="Hello, World!\nThis is the oy3o editor.\nPress Ctrl+D to save and exit.\nPress Esc to cancel.", # Initial text
        editable=True        # Allow editing
    )

    # (Optional) Add some hint text outside the editor
    stdscr.addstr(0, 1, "oy3o Editor Example - Ctrl+D Exit / Esc Cancel")
    stdscr.refresh() # Refresh parent window to show hint

    # Start the editor's main loop
    # The edit() method takes control of input until the user exits (e.g., Ctrl+D or Esc)
    final_text = editor.edit()

    # curses.wrapper automatically handles curses.endwin() to restore the terminal

    # Return the result to be printed after curses has ended
    return final_text

if __name__ == "__main__":
    # Use curses.wrapper to safely initialize and clean up the curses environment
    result = curses.wrapper(main)

    # Print the result after curses environment is closed
    print("\n--- Editor session ended ---")
    if result is not None:
        # Check the return value based on your editor.edit() implementation
        print("Submitted content:")
        print(result)
    else:
        # Depends on what edit() returns on cancellation (e.g., None or original text)
        print("Editing cancelled.")
```

## Advanced Usage - Input Handling (`oy3o.input`)

The `oy3o.input` module provides lower-level access to handle keyboard and mouse input.

```python
from oy3o import input

input.onkey(input.CTRL + input.A, lambda _:print('CTRL + A'))

input.onkey(input.DOWN, lambda _:print('ARROW DOWN'))
input.onkey(input.UP, lambda _:print('ARROW UP'))
input.onkey(input.LEFT, lambda _:print('ARROW LEFT'))
input.onkey(input.RIGHT, lambda _:print('ARROW RIGHT'))

input.onkey(input.ENTER, lambda _:print('ENTER'))
input.onkey(input.BACKSPACE, lambda _:print('BACKSPACE'))

input.onmouse(input.SCROLL_DOWN, lambda *_:print('SCROLL DOWN'))
input.onmouse(input.SCROLL_UP, lambda *_:print('SCROLL UP'))

input.onchar('😊', lambda _:print(':smile:'))
input.onchar('💕', lambda _:print(':love:'))

for wc in input.listen(move=0):
    if wc == 'q':
        input.stop()
    print(wc)
```

`input.ALT` is mouse only, because `ALT + Key` always is system shortcut.
```py
from oy3o.terminal import curses
import oy3o.input as input

input.init()
screen = curses.stdscr

def pos(y,x,type):
    screen.addstr(0, 0, f'({y},{x})')
    screen.clrtoeol()
    screen.refresh()

input.onmouse(input.ALT + input.MOVE, pos)

for wc in input.listen(screen):
    if wc == 'q':
        input.stop()
```

## Utilities (`oy3o`)

The `oy3o` module provides a collection of reusable utility classes, decorators, and helper functions used throughout the `oy3o` library or available for direct use.

```python
from oy3o import Task, Timer, throttle, debounce, subscribe, members, template # etc.
```

Key components include:

### Decorators

*   **`@throttle(interval: int, exit: bool = True)`**: Limits function call frequency (rate-limiting). Ensures the function runs at most once per `interval`. `exit=True` queues the last call to run after the interval. See code example in `_.py`.
*   **`@debounce(interval: int, enter: bool = False, exit: bool = True)`**: Delays function execution until `interval` seconds have passed without new calls. Useful for actions after a pause (e.g., search after typing stops). `enter=True` runs on the first call, `exit=True` runs after the pause. See code example in `_.py`.
*   **`@members(*args)`**: Adds default attributes (e.g., `("name", default_value)`) to a class, handling mutable defaults correctly with `deepcopy`. See code example in `_.py`.
*   **`@subscribe(events: list[str] = [], single: bool = False)`**: Adds a simple pub/sub event system (`trigger`, `subscribe`, `unsubscribe`) to a class. `events` restricts allowed event names. `single=True` uses a shared event hub for all instances. See code example in `_.py`.
*   **`@template(declare: T)`**: Implements generic functions based on signature and type hints, similar to `singledispatch` but matching the full signature. Requires `@template_instance.register` for implementations. See code example in `_.py`.
*   **`@commands(commands: list)`**: Wraps a class to restrict external access to only the methods listed in `commands`. See code example in `_.py`.

### Utility Classes

*   **`Task(func: Callable, ...)`**: Wraps a function call for synchronous (`.do()`), threaded (`.threading()`), or exception-handled (`.catch()`) execution. Handles async functions via `asyncio.run` within `.do()`. See code example in `_.py`.
*   **`Timer(once: bool, interval: int, function: Callable, ...)`**: An enhanced `threading.Timer` supporting repeated execution (`once=False`) and argument updates (`.update()`) without restarting. See code example in `_.py`.
*   **`Proxy(target: T, handler: type)`**: Implements the Proxy pattern, delegating attribute/item access to a `handler` class. See code example in `_.py`.

### Helper Functions & Constants

*   Includes type checkers (`isIterable`, `isAsync`, etc.), a unique `undefined` sentinel, and Numba type aliases.

*(Refer to the source code in `src/oy3o/_.py` for detailed implementations and docstrings.)*

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

## Acknowledgements

*   Thanks to the `curses` library for providing powerful terminal control capabilities.
*   Thanks to the `wcwidth` library for helping handle character widths correctly.
