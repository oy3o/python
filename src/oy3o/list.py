from ._ import *
from ._ import List as TypingList

_T = TypeVar('_T')

@subscribe(["empty", "full", "append", "pop", "change", "update"])
class List(UserList):
    """
    A list subclass that triggers events on modifications.
    Can be configured with a max size and rolling behavior.
    """

    def __init__(self, data: Iterable[_T] = None, size: int = None, roll: bool = True):
        # Initialize with data, respecting the initial size limit
        initial_data = list(data) if data is not None else []
        if size is not None:
            # Ensure initial data doesn't exceed size
            if len(initial_data) > size:
                if roll:
                    # If rolling, take the last 'size' elements
                    initial_data = initial_data[-size:]
                else:
                    # If not rolling, truncate to 'size' elements from the beginning
                     initial_data = initial_data[:size]

        super().__init__(initial_data)

        self.size = size
        self.roll = roll

    def __setitem__(self, index: SupportsIndex | slice, item: _T | Iterable[_T]):
        """Change item(s) at index or slice, trigger events."""
        # UserList's __setitem__ handles index/slice correctly on self.data
        # We need to capture the old value(s) *before* the change
        if isinstance(index, slice):
            # A robust way to get old items for slice might be more complex depending on desired 'change' event detail.
            # For simplicity, let's trigger update for slices after calling super.
            super().__setitem__(index, item)
            # Trigger a general update event for slice changes
            self.trigger("update", self)
            return

        # Single item assignment
        idx = index.__index__()
        if not 0 <= idx < len(self.data):
            raise IndexError("list assignment index out of range")

        old_item = self.data[idx] # Get old item from internal list
        super().__setitem__(idx, item) # UserList's __setitem__ sets self.data[idx] = item

        # Trigger change event specific to single item replacement
        self.trigger("change", idx, item, old_item)
        self.trigger("update", self) # General update event

    def __delitem__(self, index: SupportsIndex | slice):
         """Delete item(s) at index or slice, trigger events."""
         # Similar logic to __setitem__ for capturing deleted items and triggering events
         if isinstance(index, slice):
             # For slice deletion, trigger a general update event
             # Capturing all deleted items for a detailed event is complex but possible
             super().__delitem__(index)
             self.trigger("update", self)
             if len(self.data) == 0:
                 self.trigger("empty", self)

         else:
             # Single item deletion
             idx = index.__index__()
             if not 0 <= idx < len(self.data):
                 raise IndexError("list assignment index out of range")

             # Get the item before deleting
             item = self.data[idx]

             # Perform deletion using super()
             super().__delitem__(index) # UserList's __delitem__ operates on self.data

             # Trigger events - similar to pop, but the 'pop' event name is used for removal
             self.trigger("pop", idx, item) # Use 'pop' event name for deletion? Or 'delete'? Original used 'pop'.
             self.trigger("update", self)

             if len(self.data) == 0:
                 self.trigger("empty", self)

    def insert(self, index: SupportsIndex, item: _T, /) -> None:
        """Insert item before index, handling size/roll."""
        idx = index.__index__()

        # Not full yet or no size limit
        if self.size is None or len(self) < self.size:
            super().insert(idx, item)

            self.trigger("append", idx, item)
            self.trigger("update", self)
            if self.size is not None and len(self) == self.size:
                self.trigger("full", self)
            return

        # List is full
        if self.roll:
            self.pop(0)
            super().insert(idx, item)

            self.trigger("append", idx, item)
            self.trigger("update", self)
            self.trigger("full", self)

    def append(self, item: _T) -> None:
        """Append item to the list, handling max size and rolling."""
        self.insert(len(self), item)

    def pop(self, index: int = -1) -> _T:
        """Remove and return item at index, trigger events."""
        if index < 0:
            index += len(self)

        if not 0 <= index < len(self):
            raise IndexError("list index out of range")

        item = super().pop(index)
        self.trigger("pop", index, item)
        self.trigger("update", self)
        if len(self) == 0:
            self.trigger("empty", self)
        return item

    def remove(self, value: _T, /) -> None:
        """Remove first occurrence of value, trigger events."""
        index = self.index(value)
        self.pop(index)

    def pick(self, index: SupportsIndex) -> _T:
        """Return item at index (alias for __getitem__)."""
        return super().__getitem__(index.__index__())

    def last(self, n: int) -> TypingList[_T]:
        """Return the last n items."""
        if n <= 0:
            return []
        return super().__getitem__(slice(-n, None))

    def clear(self) -> None:
        """Remove all items, trigger events for each removal."""
        while len(self) > 0:
            self.pop(-1)

    def extend(self, iterable: Iterable[_T], /) -> None:
        """Extend list by appending elements from the iterable, handling size/roll."""
        for item in iterable:
            self.append(item)

    def sort(self, *args, **kwargs):
        """Sort the list in place, trigger update event."""
        super().sort(*args, **kwargs)
        self.trigger("update", self)

    def reverse(self):
        """Reverse the list in place, trigger update event."""
        super().reverse()
        self.trigger("update", self)
