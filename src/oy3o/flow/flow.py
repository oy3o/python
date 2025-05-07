from .._ import *
from ..list import List
from .. import input, string

@subscribe(["update", "full"])
class Flow:
    """
    A view onto a List, managing the visible window (offset and height).
    Manages scrolling state, including auto-scrolling to the bottom.
    """

    def __init__(
        self, data: List, height: int, offset: int = 0, auto_scroll: bool = True
    ):
        """
        Initialize the Flow.

        Args:
            data: The List instance to view.
            height: The height of the view (number of items visible).
            offset: The initial vertical offset (index of the first visible item).
            auto_scroll: If True, the view will automatically scroll to the bottom
                         when new items are appended.
        """
        if not isinstance(data, List):
            # Basic type check
            raise TypeError("data must be an instance of List")

        self.data = data
        self.height = max(0, height)  # Ensure height is non-negative
        self.auto_scroll = auto_scroll  # Renamed for clarity

        self._offset = self._clamp_offset(offset)
        data.subscribe("update", self._handle_update)

    def _clamp_offset(self, offset: int) -> int:
        """Helper to clamp the offset within valid bounds."""
        max_offset = max(0, len(self.data) - self.height)
        return max(0, min(offset, max_offset))

    @property
    def offset(self) -> int:
        return self._offset

    @offset.setter
    def offset(self, value: int) -> None:
        new_offset = self._clamp_offset(value)
        if new_offset != self._offset:
            self._offset = new_offset

    def curs_up(self, n: int = 1) -> bool:
        """Scroll view up by n lines. Disables auto-scroll."""
        old_offset = self.offset
        self.offset -= n
        return self.offset < old_offset

    def curs_down(self, n: int = 1) -> bool:
        """Scroll view down by n lines. Enables auto-scroll if reaching the bottom."""
        old_offset = self.offset
        self.offset += n
        return self.offset > old_offset

    def curs_to(self, pos: int) -> None:
        """Set the view offset to a specific position."""
        self.offset = pos

    def window(self) -> List:
        """Return the list items currently visible in the view."""
        return self.data[self.offset : self.offset + self.height]

    def __len__(self) -> int:
        """Return the number of items potentially visible in the view."""
        return min(self.height, max(0, len(self.data) - self.offset))

    def _handle_update(self, data):
        if self.auto_scroll:
            self.offset = len(data)


@subscribe(["update"])
class View(Flow):
    def __init__(
        self,
        data: List,
        window: input.curses.window,
        y: int = 0,
        x: int = 0,
        height: int = None,
        width: int = None,
        offset=0,
        auto_scroll=True,
    ):
        """
        Initialize the Flow View.

        Args:
            data: The List instance to display.
            window: The curses window object to draw on.
            y, x: Top-left coordinates relative to the window parent.
            height, width: Dimensions of the view sub-window. Defaults to window max dimensions.
            offset: Initial scroll offset.
            auto_scroll: If True, automatically scroll to the bottom on new appends.
        """
        self.ymax, self.xmax = window.getmaxyx()
        self.height = height or self.ymax
        self.width = width or self.xmax
        self.view = window.derwin(self.height, self.width, y, x)
        self.ymin, self.xmin = self.view.getbegyx()

        super().__init__(data, self.height, offset, auto_scroll)

        self._stop = False
        self.render()

    def listen(self) -> None:
        """Start listening for relevant input events and List updates."""
        input.onmouse(input.SCROLL_DOWN, self.handle_mouse)
        input.onmouse(input.SCROLL_UP, self.handle_mouse)

        self.data.subscribe("update", self.render)
        self._stop = False

    def stop(self) -> None:
        """Stop listening for events."""
        input.offmouse(input.SCROLL_DOWN, self.handle_mouse)
        input.offmouse(input.SCROLL_UP, self.handle_mouse)
        self.data.unsubscribe("update", self.render)  # Unsubscribe render handler
        self._stop = True

    def render(self, *args) -> None:
        """Render the visible part of the List to the curses window."""
        if self._stop:
            return

        self.view.erase()
        for i, item in enumerate(self.window()):
            display_text = string.truncate(str(item), self.width - 1)
            self.view.addstr(i, 0, display_text)
            self.view.clrtoeol()
        self.view.refresh()
        self.trigger('update', self)

    def close(self) -> None:
        """Erase the window content and refresh."""
        self.view.erase()
        self.view.refresh()

    def handle_mouse(self, y: int, x: int, mouse_type: int) -> None:
        """Handle mouse scroll events within the app's window boundaries."""
        if self._stop:
            return

        if self.ymin <= y < self.ymax and self.xmin <= x < self.xmax:
            if mouse_type == input.SCROLL_DOWN:
                if self.curs_down():
                     self.render()
            elif mouse_type == input.SCROLL_UP:
                if self.curs_up():
                     self.render()

    def __enter__(self):
        """Context manager entry: start listening."""
        self.listen()
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> bool:
        """Context manager exit: stop listening and close the view."""
        self.stop()
        self.close()
        return False
