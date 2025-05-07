from .._ import *
from .. import input
from ..terminal import curses
from ..list import List
from .flow import View

def run_flow():
    """Main function to set up and run the curses flow view."""
    data = List()

    if not sys.stdin.isatty():
        try:
            for line in sys.stdin:
                data.append(line.rstrip('\n')) # Remove trailing newline
        except BrokenPipeError:
            # Handle cases where the pipe is closed by the reading end
            pass
        except Exception as e:
            print(f"Error reading input: {e}")
            return
    else:
        print("Error: No input provided via pipe or redirection.\nUsage: cat file.txt | python -m oy3o.flow")
        return # Exit as no input was provided

    # If no data was read (e.g., empty file or immediate pipe close)
    if not data:
        print("No data received from input.")
        return

    original_stdin = sys.stdin
    original_stdin_fd = os.dup(original_stdin.fileno())
    tty_fd = os.open('/dev/tty', os.O_RDWR)
    os.dup2(tty_fd, original_stdin.fileno())

    stdscr = curses.initscr()
    curses.savetty()
    curses.curs_set(0)
    curses.noecho()
    curses.cbreak()
    stdscr.keypad(True)
    stdscr.clear()
    stdscr.refresh()

    def clean():
        stdscr.clear()
        stdscr.refresh()
        curses.resetty()
        curses.endwin()

    # Get screen dimensions for the View
    max_y, max_x = stdscr.getmaxyx()

    # --- Create and manage the View ---
    # The View should use the main stdscr window and its full dimensions.
    # auto_scroll=True ensures it shows the bottom of the loaded content initially.
    try:
        with View(
            data=data,
            window=stdscr, # Pass the standard screen window
            height=max_y,
            width=max_x,
            offset=0, # Initial offset; auto_scroll will change this immediately
            auto_scroll=True
        ) as view:

            # Quit handler: stop the input loop
            def handle_quit(key):
                input.stop()

            input.onchar('q', handle_quit)         # Quit on 'q' key
            input.onkey(input.ESC, handle_quit) # Quit on ESC key

            def handle_page_up(key):
                view.curs_up(view.height) # Scroll up by view height (a page)
                view.render()

            def handle_page_down(key):
                view.curs_down(view.height) # Scroll down by view height (a page)
                view.render()

            def handle_home(key):
                view.curs_to(0) # Scroll to the very top
                view.render()

            def handle_end(key):
                # Scroll to the very bottom (curs_to handles clamping)
                view.curs_to(len(data))
                view.render()

            # Use standard curses constants for PageUp/Down, Home/End
            # Assume these are available via the imported `curses` object from terminal.py
            input.onkey(curses.KEY_PPAGE, handle_page_up)
            input.onkey(curses.KEY_NPAGE, handle_page_down)
            input.onkey(curses.KEY_HOME, handle_home)
            input.onkey(curses.KEY_END, handle_end)
            input.onchar('g', handle_home) # less/vim Home (go to top)
            input.onchar('G', handle_end)  # less/vim End (go to bottom)
            input.onchar(' ', handle_page_down) # Spacebar for page down like `less`

            for wc in input.listen():
                continue

    except Exception as e:
            print(f"An error occurred: {e}", file=sys.stderr)

    finally:
        clean()

# Standard Python entry point for -m execution
if __name__ == "__main__":
    # Run the main application logic
    run_flow()
    # Exit explicitly with a status code (optional but good practice)
    sys.exit(0)
