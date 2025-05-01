# oy3o

[![PyPI version](https://badge.fury.io/py/oy3o.svg)](https://badge.fury.io/py/oy3o) <!-- Replace with your PyPI link after publishing -->
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
from oy3o.editor import Editor # Assuming __init__ exposes Editor

def main(stdscr):
    # Basic curses setup
    curses.curs_set(1) # Show cursor
    stdscr.keypad(True) # Enable special keys (like arrows)
    curses.mousemask(curses.ALL_MOUSE_EVENTS | curses.REPORT_MOUSE_POSITION) # Enable mouse events
    curses.mouseinterval(0) # Report mouse events immediately
    stdscr.clear()     # Clear screen

    # Get screen dimensions
    height, width = stdscr.getmaxyx()

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
import curses
from oy3o import input as oy3o_input # Import the input module

def main(stdscr):
    # --- Crucial Curses Setup for input module ---
    curses.curs_set(0)  # Usually hide cursor unless needed
    stdscr.keypad(True) # MUST be enabled for special keys (Arrows, F*, etc.)
    curses.noecho()     # Prevent keys from echoing automatically
    curses.cbreak()     # Get keys immediately, without waiting for Enter
    # If mouse events are needed:
    curses.mousemask(curses.ALL_MOUSE_EVENTS | curses.REPORT_MOUSE_POSITION)
    curses.mouseinterval(0) # Report mouse events immediately
    # Enable Xterm mouse move reporting (if terminal supports it)
    print('\033[?1003h', end='')
    stdscr.refresh() # Ensure the escape code is sent

    stdscr.clear()
    stdscr.addstr(1, 0, "oy3o Input Demo. Press 'q' to quit.")
    stdscr.addstr(2, 0, "Try pressing Ctrl+A, Arrow Keys, Enter, Backspace.")
    stdscr.addstr(3, 0, "Try scrolling or moving the mouse (with/without Ctrl+Alt).")
    stdscr.addstr(4, 0, "Try typing 😊 or 💕.")
    stdscr.refresh()

    # --- Event Bindings ---
    oy3o_input.onkey(oy3o_input.CTRL + 'a', lambda _: stdscr.addstr(6, 0, "Detected: CTRL + A ".ljust(30)))
    oy3o_input.onkey(oy3o_input.DOWN, lambda _: stdscr.addstr(7, 0, "Detected: ARROW DOWN ".ljust(30)))
    oy3o_input.onkey(oy3o_input.UP, lambda _: stdscr.addstr(8, 0, "Detected: ARROW UP   ".ljust(30)))
    oy3o_input.onkey(oy3o_input.LEFT, lambda _: stdscr.addstr(9, 0, "Detected: ARROW LEFT ".ljust(30)))
    oy3o_input.onkey(oy3o_input.RIGHT, lambda _: stdscr.addstr(10, 0, "Detected: ARROW RIGHT".ljust(30)))
    oy3o_input.onkey(oy3o_input.ENTER, lambda _: stdscr.addstr(11, 0, "Detected: ENTER      ".ljust(30)))
    oy3o_input.onkey(oy3o_input.BACKSPACE, lambda _: stdscr.addstr(12, 0, "Detected: BACKSPACE  ".ljust(30)))

    oy3o_input.onmouse(oy3o_input.SCROLL_DOWN, lambda *_: stdscr.addstr(13, 0, "Detected: SCROLL DOWN".ljust(30)))
    oy3o_input.onmouse(oy3o_input.SCROLL_UP, lambda *_: stdscr.addstr(14, 0, "Detected: SCROLL UP  ".ljust(30)))

    def show_mouse_pos(y, x, type_key):
        type_str = f"Type: {type_key!r}" # Display the internal key representation
        stdscr.addstr(15, 0, f"Mouse Move: ({y},{x}) {type_str}".ljust(40))
        stdscr.refresh()

    # Normal move
    oy3o_input.onmouse(oy3o_input.MOVE, show_mouse_pos)
    # Move with modifiers (Ctrl+Alt)
    oy3o_input.onmouse(oy3o_input.CTRL + oy3o_input.ALT + oy3o_input.MOVE, show_mouse_pos)

    # Handle specific characters (like Emoji)
    oy3o_input.onchar('😊', lambda _: stdscr.addstr(16, 0, "Detected: :smile:     ".ljust(30)))
    oy3o_input.onchar('💕', lambda _: stdscr.addstr(17, 0, "Detected: :love:      ".ljust(30)))

    # --- Main Event Loop ---
    # listen() blocks and yields key/mouse events
    # `move=1` (default) includes MOVE events. `move=0` excludes them.
    # Pass stdscr so `listen` can use its getch method.
    for event in oy3o_input.listen(stdscr, move=1):
        # You can handle events here not caught by onkey/onmouse/onchar
        # event can be a character, special key constant, or mouse tuple/constant
        stdscr.addstr(19, 0, f"Raw Event: {event!r}".ljust(40))
        stdscr.refresh()

        if event == 'q':
            oy3o_input.stop() # Stop the listen() loop

    # --- Cleanup (before wrapper exits) ---
    # Disable Xterm mouse reporting
    print('\033[?1003l', end='')
    # Optional: short sleep allows terminal to process escape code before restoring
    curses.napms(50)

if __name__ == "__main__":
    curses.wrapper(main)
    print("\nInput demo finished.")
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

*   Includes type checkers (`isIterable`, `isAsync`, etc.), `setdefault`, a unique `undefined` sentinel, and Numba type aliases.

*(Refer to the source code in `src/oy3o/_.py` for detailed implementations and docstrings.)*

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

## Acknowledgements

*   Thanks to the `curses` library for providing powerful terminal control capabilities.
*   Thanks to the `wcwidth` library for helping handle character widths correctly.
