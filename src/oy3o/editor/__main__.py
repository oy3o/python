from .editor import Editor
import curses
import os
import sys # Import sys to potentially write to stdout explicitly if needed

# Wrap the core editor logic in a function that accepts stdscr
def run_editor(stdscr):
    # --- Basic curses setup inside the wrapper ---
    # No need for curses.initscr() - wrapper handles it.
    # Set up modes if your Editor doesn't handle them all internally.
    curses.curs_set(1) # Show cursor (adjust as needed)
    # keypad(True) enables reading keys like arrows, F-keys etc.
    # stdscr is the window object provided by wrapper, enable keypad on it.
    stdscr.keypad(True)
    # If your editor uses mouse input:
    # curses.mousemask(curses.ALL_MOUSE_EVENTS | curses.REPORT_MOUSE_POSITION)
    # curses.mouseinterval(0)

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
        max_length=max_length, # Editor needs to use this to limit input/display if set
        outline=outline,
        editable=True,
        # Consider adding initial text or placeholder?
        # text="Enter text here, Ctrl+D to save..."
    )

    # --- Run the editor's main loop ---
    # This handles all the curses interaction within the wrapper
    final_text = editor.edit()

    # --- Return the final text ---
    # This will be the return value of curses.wrapper()
    return final_text

# Main execution block
def main():
    original_stdout_fd = -1
    temp_stdout_path = "/dev/tty" # Path to the controlling terminal

    try:
        # --- Save original stdout and potentially redirect ---
        # Check if stdout is a TTY (terminal)
        if sys.stdout.isatty():
            # If output is going to terminal, no need to redirect here.
            # Curses will use it directly.
            pass
        else:
            # stdout is redirected (e.g., to a file).
            # Save original stdout FD *before* curses potentially messes with it.
            original_stdout_fd = os.dup(sys.stdout.fileno())

            # Redirect Python's sys.stdout to the actual terminal so curses works.
            # This is crucial!
            try:
                # Open the controlling terminal for writing.
                # This might fail if not run from an interactive terminal.
                new_stdout = open(temp_stdout_path, 'w')
                os.dup2(new_stdout.fileno(), sys.stdout.fileno())
                # Note: We don't close new_stdout here because sys.stdout now owns it.
            except OSError as e:
                # Cannot open /dev/tty, maybe not interactive? Fallback needed.
                # Print error to stderr (which might still be the terminal or redirected)
                print(f"Error: Cannot redirect stdout to terminal ({temp_stdout_path}): {e}", file=sys.stderr)
                # Depending on requirements, either exit or try to proceed without UI
                return # Exit in this case

        # --- Run curses using wrapper ---
        final_output = curses.wrapper(run_editor)

    finally:
        # --- Restore original stdout if it was redirected ---
        # This block executes even if curses.wrapper raises an exception.
        if original_stdout_fd != -1:
            # Ensure terminal is somewhat restored before writing final output
            # curses.wrapper should have called endwin(), but add delay just in case.
            try:
                curses.napms(50) # Small delay
            except: pass # Ignore if curses isn't initialized anymore

            # Restore the original stdout file descriptor
            try:
                os.dup2(original_stdout_fd, sys.stdout.fileno())
                os.close(original_stdout_fd) # Close the saved duplicate
            except OSError as e:
                print(f"Error restoring stdout: {e}", file=sys.stderr)


    # --- Write final output to the *original* stdout ---
    if final_output is not None and original_stdout_fd != -1:
        # If we redirected stdout, write the result to the saved FD
        try:
            with os.fdopen(os.dup(sys.stdout.fileno()), 'w') as final_writer: # Use original stdout's FD
                final_writer.write(final_output)
                # No extra newline needed if final_output has one
        except OSError as e:
             print(f"Error writing final output: {e}", file=sys.stderr)

    elif final_output is not None and original_stdout_fd == -1:
        # If stdout was the TTY all along, just print normally
        print(final_output, end='')


if __name__ == "__main__":
    main()