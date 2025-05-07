# oy3o

[![PyPI version](https://badge.fury.io/py/oy3o.svg)](https://badge.fury.io/py/oy3o)
[中文版 README (Chinese README)](README.zh-CN.md)

A Python library for building Text User Interfaces (TUIs), providing `curses`-based interactive components (e.g., multi-line text editor, scrollable list view) and flexible input handling.

**Note:** This library depends on Python's `curses` module, which is typically part of the standard library on Unix-like systems (Linux, macOS), but is not available by default on Windows. Windows users may need to install the `windows-curses` package (`pip install windows-curses`), but compatibility may require further testing.

## Features

*   **Interactive Components:**
    *   `curses`-based editable textbox/editor (`oy3o.editor.Editor`).
        *   Supports basic text navigation (up, down, left, right, home, end).
        *   Supports text wrapping and view scrolling.
    *   Scrollable list view (`oy3o.flow.View`).
        *   Displays the content of `oy3o.list.List`.
        *   Supports keyboard and mouse wheel scrolling.
        *   Auto-scrolls to newly added entries.
*   **Advanced Input Handling (`oy3o.input`):**
    *   Listens and responds to individual key presses, including modifier keys (Ctrl).
    *   Handles special keys (arrow keys, enter, backspace, etc.).
    *   Captures mouse events: clicks, scrolling (up/down), and movement (including coordinates and modifier key states, e.g., Ctrl+Alt+Move).
    *   Binds functions to specific key, mouse, or character events via `onkey`, `onmouse`, `onchar`.
    *   Provides a main input loop (`listen()`) to process the event stream.
    *   **Note:** `input.ALT` is currently primarily for mouse events, as Alt + letter keys are often intercepted by the operating system or terminal.
*   **Data Structures (`oy3o.list`):**
    *   `List`: An observable list that can trigger events when its content changes, integrating with components like `Flow` and `View`.
*   **Wide Character Support:** Integrates `wcwidth` to correctly handle wide characters (e.g., CJK characters).
*   **Utilities (`oy3o._`):** Contains several utility tools and decorators such as event subscription (`@subscribe`), throttling (`@throttle`), debouncing (`@debounce`), task management (`Task`, `Timer`), metaprogramming helpers (`@members`, `@template`, `Proxy`), etc. (See details below).
*   **Token Counting:** Integrates `tiktoken` for token counting.
*   **System Clipboard:** Supports copy/paste operations with the system clipboard via `pyperclip`.

## Installation

You can install `oy3o` from PyPI using pip:

```bash
pip install oy3o
```

## Modular Running (Command-Line Piping)

Some `oy3o` modules can be run directly from the command line using `python -m` and support piping content from standard input:

*   **Editor (`oy3o.editor`):**
    ```bash
    cat some_file.txt | python -m oy3o.editor
    ```
    This will load the content of `some_file.txt` into the editor. After editing, press `Ctrl+D` to save and exit (content will be printed to standard output); press `Esc` to cancel.

*   **Flow View (`oy3o.flow`):**
    ```bash
    cat some_file.txt | python -m oy3o.flow
    ```
    This will display each line of `some_file.txt` as a list item in a scrollable flow view. Press `q` to quit.

## Basic Usage - Editor (`oy3o.editor`)

Here's a simple example demonstrating how to launch a basic `oy3o` editor in the terminal:

```python
import curses
from oy3o.editor import Editor

def main(stdscr):
    # Create an Editor instance
    # Editor draws and manages its area within the given window based on top/bottom/left/right
    editor = Editor(
        window=stdscr,       # Specify the parent window as stdscr
        top=1,               # Top margin of the editor area (starts from stdscr row 1)
        bottom=1,            # Bottom margin of the editor area (1 row from the bottom of stdscr)
        left=1,              # Left margin of the editor area (starts from stdscr column 1)
        right=1,             # Right margin of the editor area (1 column from the right of stdscr)
        text="Hello, world!\nThis is the oy3o editor.\nPress Ctrl+D to save and exit.\nPress Esc to cancel.", # Initial text
        editable=True        # Allow editing
    )

    # (Optional) Add some hint text outside the editor
    stdscr.addstr(0, 1, "oy3o Editor Example - Ctrl+D to Save & Exit / Esc to Cancel")
    stdscr.refresh() # Refresh the parent window to display the hint

    # Start the editor's main loop
    # The edit() method will take over input until the user exits (e.g., by pressing Ctrl+D or Esc)
    final_text = editor.edit()

    # curses.wrapper will automatically handle curses.endwin() to restore the terminal

    # Return the result so it can be printed after the curses environment ends
    return final_text

if __name__ == "__main__":
    # Use curses.wrapper to safely initialize and clean up the curses environment
    result = curses.wrapper(main)

    # Print the result after the curses environment is closed
    print("\n--- Editor session ended ---")
    if result is not None:
        # Depending on your editor.edit() implementation, confirm if it returns the final text or something else
        print("Submitted content:")
        print(result)
    else:
        # This depends on what edit() returns on cancellation, possibly None or the original text
        print("Editing was canceled.")

```

## Basic Usage - Flow View (`oy3o.flow`)

The `oy3o.flow.View` class can display the content of an `oy3o.list.List` in a scrollable `curses` window.

```python
import curses
from oy3o import input
from oy3o.list import List
from oy3o.flow import View
import time # For demonstrating dynamic content addition

def main(stdscr):
    curses.curs_set(0) # Hide the cursor
    stdscr.nodelay(True) # Non-blocking input

    # Create a List instance
    data_list = List([f"Initial line {i}" for i in range(20)])

    # Create a View in stdscr
    # y, x, height, width define the View's area within stdscr
    # Use a with statement to ensure resources are properly cleaned up
    with View(data_list, stdscr, y=1, x=1, height=curses.LINES - 2, width=curses.COLS - 2) as view:
        stdscr.addstr(0, 1, "oy3o Flow View Example - Press 'q' to quit, 'a' to add a line, scroll with wheel")
        stdscr.refresh()

        # Start input listening
        # view.listen() will handle internal events like mouse scrolling
        # input.listen() is the external event loop
        counter = 20
        for wc in input.listen(stdscr, delay=0.05): # delay reduces CPU usage
            if wc == 'q':
                input.stop() # Stop the input.listen() loop
                break
            elif wc == 'a':
                data_list.append(f"Newly added line {counter}")
                counter += 1
            # view.render() will be called automatically when data_list is updated (via subscription)
            # If manual refresh or other logic is needed, it can be added here

            # Simulate external data updates
            # if time.time() % 5 < 0.05: # Add approximately every 5 seconds
            #     data_list.append(f"Periodically added line {counter}")
            #     counter += 1
    
    # curses.wrapper will handle curses.endwin()

if __name__ == "__main__":
    curses.wrapper(main)
    print("Flow view closed.")
```

## Advanced Usage - Input Handling (`oy3o.input`)

The `oy3o.input` module provides a lower-level interface for handling keyboard and mouse input.

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

for wc in input.listen(move=0): # Set move=0 if you don't need mouse move events with no buttons pressed
    if wc == 'q':
        input.stop()
    print(wc)
```

`input.ALT` is mainly for mouse events, as `ALT + Key` is often intercepted by the OS/terminal.
```python
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

The `oy3o` module (often from `oy3o._`) provides a collection of reusable utility classes, decorators, and helper functions, used internally within the `oy3o` library and also available for direct use.

```python
from oy3o import Task, Timer, throttle, debounce, subscribe, members, template # and more
```

Key components include:

### Decorators

*   **`@throttle(interval: int, exit: bool = True)`**: Limits function call frequency (rate limiting). Ensures the function is executed at most once per `interval` seconds. `exit=True` queues the arguments of the last call to be executed after the interval. See code examples in `_.py`.
*   **`@debounce(interval: int, enter: bool = False, exit: bool = True)`**: Delays function execution until `interval` seconds have passed without a new call since the last call. Useful for actions performed after activity has paused (e.g., searching after typing stops). `enter=True` executes on the first call, `exit=True` executes after the pause. See code examples in `_.py`.
*   **`@members(*args)`**: Adds default attributes (e.g., `("name", default_value)`) to a class, correctly handling mutable default values via `deepcopy`. See code examples in `_.py`.
*   **`@subscribe(events: list[str] = [], single: bool = False)`**: Adds a simple publish/subscribe event system (`trigger`, `subscribe`, `unsubscribe` methods) to a class. `events` limits allowed event names. `single=True` makes all instances share the same event hub. See code examples in `_.py`.
*   **`@template(declare: T)`**: Implements generic functions (templates) based on signatures and type hints, similar to `functools.singledispatch` but matches the full signature. Requires registering concrete implementations with `@template_instance.register`. See code examples in `_.py`.
*   **`@commands(commands: list)`**: Wraps a class to restrict external access to methods specified in the `commands` list. See code examples in `_.py`.

### Utility Classes

*   **`Task(func: Callable, ...)`**: Wraps a function call to support synchronous (`.do()`), threaded (`.threading()`), or exception-handled (`.catch()`) execution. Handles async functions via `asyncio.run` in `.do()`. See code examples in `_.py`.
*   **`Timer(once: bool, interval: int, function: Callable, ...)`**: An enhanced version of `threading.Timer` that supports repeated execution (`once=False`) and updating parameters (`.update()`) without restarting. See code examples in `_.py`.
*   **`Proxy(target: T, handler: type)`**: Implements the Proxy pattern, delegating attribute/item access to a `handler` class. See code examples in `_.py`.
*   **`List(list)`**: `oy3o.list.List` is an observable list. It triggers an "update" event when its content is changed via methods like `append`, `extend`, `insert`, `pop`, `remove`, `clear`, `__setitem__`, `__delitem__`, etc. `Flow` and `View` components subscribe to this event to automatically refresh their display.

### Helper Functions & Constants

*   Includes type checkers (`isIterable`, `isAsync`, etc.), a unique `undefined` sentinel object, and Numba type aliases.

*(For detailed implementations and docstrings, please refer to the source code in `src/oy3o/_.py` and `src/oy3o/list.py`.)*

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please feel free to raise Issues or submit Pull Requests.

## Acknowledgements

*   Thanks to the `curses` library for providing powerful terminal control capabilities.
*   Thanks to the `wcwidth` library for helping to correctly handle character widths.
