from .._ import *
from ..input import curses
from .editor import Editor

# Wrap the core editor logic in a function that accepts stdscr
def edit(text):
    def run_editor(stdscr):
        h, w = stdscr.getmaxyx()

        # --- Your layout calculation logic ---
        # Use h, w from stdscr provided by the wrapper
        bottom = 0
        left = 0
        max_length = None
        outline = 1
        padding_x = 1
        padding_y = 0

        # Calculate desired editor height, ensuring it's positive
        # Note: Outline and padding apply twice (top/bottom or left/right)
        target_height = h - bottom - (padding_y * 2) - (outline * 2)
        target_height = max(1, target_height) # Ensure at least 1 row high

        # Calculate top margin based on desired height and bottom margin
        top = h - target_height - bottom - (padding_y * 2) - (outline * 2)
        top = max(0, top) # Ensure top margin isn't negative

        # Recalculate actual height based on clamped top margin
        height = h - top - bottom - (padding_y * 2) - (outline * 2)
        height = max(1, height) # Ensure height is still valid

        # Calculate width and right margin
        target_width = w - left - (padding_x * 2) - (outline * 2)
        if max_length is not None:
            target_width = min(target_width, max_length)
        target_width = max(1, target_width) # Ensure at least 1 column wide

        # Calculate right margin based on desired width and left margin
        right = w - left - target_width - (padding_x * 2) - (outline * 2)
        right = max(0, right) # Ensure right margin isn't negative

        # Final check if the screen is usable with these dimensions
        view_height = h - top - bottom
        view_width = w - left - right
        if view_height <= 0 or view_width <= 0:
            # Handle case where screen is too small
            # Clear screen first if possible
            try: stdscr.clear()
            except: pass
            message = "Screen too small!"
            try: stdscr.addstr(0, 0, message)
            except: pass # Ignore error if cannot even write error
            try: stdscr.refresh()
            except: pass
            curses.napms(2000) # Pause for 2 seconds
            return None # Indicate failure

        # --- Create the Editor instance ---
        # Pass the stdscr provided by curses.wrapper
        editor = Editor(
            window=stdscr,
            top=top,
            bottom=bottom,
            right=right,
            left=left,
            padding_y=padding_y,
            padding_x=padding_x,
            text=text,
            max_length=max_length, # Editor needs to use this to limit input/display if set
            outline=outline,
            editable=True,
            # Consider adding initial text or placeholder?
            # text="Enter text here, Ctrl+D to save..."
        )

        # --- Run the editor's main loop ---
        # This handles all the curses interaction within the wrapper
        result = editor.edit()

        # --- Return the final text ---
        # This will be the return value of curses.wrapper()
        return result
    return run_editor

# Main execution block
def main():
    original_stdin = sys.stdin
    original_stdout = sys.stdout
    original_stdin_fd = os.dup(original_stdin.fileno())
    original_stdout_fd = os.dup(original_stdout.fileno())
    stdin_fd = original_stdout_fd
    stdout_fd = original_stdout_fd
    pipedInput = []
    output = None

    try:
        if not original_stdin.isatty():
            try:
                for line in original_stdin:
                    pipedInput.append(line.rstrip('\n'))
            except BrokenPipeError:
                # Handle cases where the pipe is closed by the reading end
                pass
            except Exception as e:
                print(f"Error reading input: {e}")
                return
            stdin_fd = os.open('/dev/tty', os.O_RDWR)
            os.dup2(stdin_fd, original_stdin.fileno())

        if not original_stdout.isatty():
            stdout_fd = os.open('/dev/tty', os.O_WRONLY)
            os.dup2(stdout_fd, original_stdout.fileno())

        # edit update output
        output = curses.wrapper(edit('\n'.join(pipedInput)))

    except Exception as e:
        raise
    finally:
        if stdin_fd != original_stdin_fd:
            os.close(stdin_fd)
            os.dup2(original_stdin_fd, original_stdin.fileno())
        os.close(original_stdin_fd)

        if stdout_fd != original_stdout_fd:
            os.close(stdout_fd)
            os.dup2(original_stdout_fd, original_stdout.fileno())

    if output is not None and original_stdout_fd != -1:
        try:
            with os.fdopen(original_stdout_fd, 'w') as writer: # Use original stdout's FD
                writer.write(output)
        except OSError as e:
            print(f"Error writing final output: {e}", file=sys.stderr)
    elif output is not None and original_stdout_fd == -1:
        # If stdout was the TTY all along, just print normally
        print(output, end='')

if __name__ == "__main__":
    main()
