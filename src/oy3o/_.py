from typing import (
    get_type_hints,
    overload,
    TypeVar,
    Generic,
    Iterable,
    Callable,
    Mapping,
    List,
    Tuple,
    Optional,
)
from typing_extensions import Annotated
from inspect import signature, isawaitable
from copy import deepcopy
from numba import (
    jit,
    njit,
    byte,
    uint32 as u32,
    uint64 as u64,
    char,
    int32 as i32,
    int64 as i64,
    uintp as pointer,
    float32 as f32,
    float64 as f64,
)
from dataclasses import dataclass
from functools import wraps, cache, lru_cache, partial as bind
from deco import concurrent, synchronized
from abc import ABC as Interface, abstractmethod
from collections.abc import MutableSequence, MutableSet, MutableMapping
from time import time, sleep
import asyncio
import threading
import queue

T = TypeVar("T")
bytes = type(byte([]))
byte = type(byte(0))
u32 = type(u32(0))
u64 = type(u64(0))
char = type(char(0))
i32 = type(i32(0))
i64 = type(i64(0))
pointer = type(pointer(0))
f32 = type(f32(0))
f64 = type(f64(0))


class undefined:
    def __bool__(self):
        return False


def setdefault(o: object, name, default):
    value = getattr(o, name, undefined)
    if value == undefined:
        object.__setattr__(o, name, default)
        return default
    return value


def isIterable(o):
    return isinstance(o, Iterable)


def isMapping(o):
    return isinstance(o, Mapping)


def isCallable(o):
    return isinstance(o, Callable)


def isAsync(func):
    return asyncio.iscoroutinefunction(func)


class Task:
    """
    A wrapper class for a function that can be executed synchronously or asynchronously.

    :param func: a callable object
    :param args: a tuple of positional arguments to pass to the function
    :param kwargs: a dictionary of keyword arguments to pass to the function
    :param asyncrun: a boolean indicating whether force to run the function asynchronously or not
    """

    def __init__(self, func: Callable, args=None, kwargs=None, asyncrun=False):
        if not callable(func):
            raise ValueError("Invalid function not callable")
        self.func = func
        self.args = args or ()
        self.kwargs = kwargs or {}
        self.is_async = asyncrun or isAsync(func)

    def do(self):
        """
        Execute the function and return its result.

        :return: the return value of the function call
        """
        if self.is_async:
            return asyncio.run(self.func(*self.args, **self.kwargs))
        else:
            return self.func(*self.args, **self.kwargs)

    def catch(self, func=lambda e: None):
        """
        Execute the function and handle any exception with another function.

        :param func: a callable object that takes an exception as an argument and returns a value
        :return: the return value of the function call or the exception handler
        """
        try:
            return self.do()
        except Exception as e:
            return func(e)

    def threading(self):
        """
        Return a threading.Thread object that executes the function.

        :return: a threading.Thread object
        """
        return threading.Thread(target=self.do)


class TaskID:
    pass


class Timer(threading.Timer):
    """
    Timer class is a timer class that can repeatedly execute a function at a specified time once and update the function's parameters at runtime.

    :param once: a bool, when false means the startup interval occurs only once, otherwise, the interval continuously recur.
    :param interval: a float, representing the time once in seconds.
    :param function: a callable object, representing the function to execute.
    :param args: a variable argument list, representing the positional arguments to pass to the function.
    :param kwargs: a variable argument dictionary, representing the keyword arguments to pass to the function.

    usage:
    ```
    # Define a function that prints a message
    def print_message(message):
        print(message)

    # Create an Timer object that prints "Hello" every 5 seconds
    timer = Timer(False, 5, print_message, "Hello")
    timer.start()

    time.sleep(10)
    timer.update("World")
    time.sleep(10)
    timer.cancel()
    """

    def __init__(self, once: bool, interval: int, function: Callable, *args, **kwargs):
        super().__init__(interval, function, args, kwargs)
        self.run_time = time() + interval
        self.once = once

    # Define update method, receive *args, **kwargs parameters
    def update(self, *args, **kwargs):
        """
        This method will update the function's parameters and  set the next execution time to the current time plus the interval.
        :param *args: a variable argument list, representing the positional arguments to update.
        :param **kwargs: a variable argument dictionary, representing the keyword arguments to update.
        """
        self.args = args
        self.kwargs = kwargs
        self.run_time = time() + self.interval

    def run(self):
        while not self.finished.is_set():
            wait_time = self.run_time - time()
            if wait_time <= 0:
                if self.once:
                    self.finished.set()
                self.function(*self.args, **self.kwargs)
                self.run_time = time() + self.interval
            else:
                self.finished.wait(wait_time)


class template(Generic[T]):
    """
    A decorator that implements a template pattern for a generic function.
        :param declare: a function that declares the generic type

    usage:
    ```
    @overload def a():...
    @overload def a(int:i):...

    a = template(a) # for type hints

    @a.register def _():...
    @a.register def _(int:i):...
    """

    def __init__(self, declare: T = lambda *args: None):
        self.declare = declare
        self.registry = {}

    def register(self, func: Callable):
        sig = signature(func)
        hints = get_type_hints(func)
        hints.pop("return", None)
        if len(hints) != len(sig.parameters):
            raise TypeError(f"template function must have explicit type")
        self.registry[sig] = func

    @wraps(T)
    def __call__(self, *args, **kwds):
        for sig, func in self.registry.items():
            try:
                sig.bind(*args, **kwds)
                return func(*args, **kwds)
            except TypeError:
                pass
        raise NotImplementedError(
            f'No matching implementation of arguments types ({", ".join(map(str, map(type, args)))})'
        )


class members(Generic[T]):
    """
    A decorator that adds default values to a class's attributes.
    :param args: a list of tuples that contain the attribute name and the default value
    usage:
    ```
    @members(("name", ""), ("age", 0), ("friends", set()))
    class Person: # add default values for name, age and friends attributes
        def __init__(self, name):
            self.name = name
    """

    def __init__(self, *args):
        self.members = args

    def __call__(self, klass: T) -> T:
        if not isinstance(klass, type):
            raise TypeError("members can only decorate classes")
        members = self.members

        class WithMembers(klass):
            @wraps(klass.__init__)
            def __init__(self, *args, **kwds):
                super().__init__(*args, **kwds)
                for member, default in members:
                    klass_member = getattr(self, member, None)
                    if isinstance(klass_member, type(default)):
                        if isinstance(klass_member, MutableSet):
                            klass_member = deepcopy(default).union(klass_member)
                        elif isinstance(klass_member, MutableMapping):
                            klass_member = {**deepcopy(default), **klass_member}
                        elif isinstance(klass_member, MutableSequence):
                            klass_member = [*deepcopy(default), *klass_member]
                    if klass_member == None:
                        klass_member = deepcopy(default)
                    setattr(self, member, klass_member)

        WithMembers.__name__ = (
            klass.__name__ + f'({" ".join([name for (name,_) in self.members])})'
        )
        return WithMembers


class subscribe(Generic[T]):
    """
    A decorator that adds event-driven features to a class.
    :param events: a list of strings that represent the allowed events
    :param single: a boolean that indicates whether to use a single event hub for all instances
    usage:
    ```
    @subscribe(["click"]) # only allow click and hover events
    class Button: text: str

    b = Button("OK")
    b.subscribe("click", lambda e: print(f"Clicked {e['text']}")) # register a listener for click event
    b.trigger("click", {"text": b.text}) # trigger the click event and print "Clicked OK"

    @subscribe() # allow all events
    class Unknow: ...
    """

    def __init__(self, events: list[str] = [], single: bool = False):
        self.events = events
        self.single = single

    def __call__(self, klass: T) -> T:
        if not isinstance(klass, type):
            raise TypeError("subscribe can only decorate classes")
        eventshub = {}
        events = self.events
        single = self.single

        class EventsHub(klass):
            @wraps(klass.__init__)
            def __init__(self, *args, **kwds):
                super().__init__(*args, **kwds)
                self.eventshub = getattr(self, "eventshub", eventshub if single else {})

            def trigger(self, event: str, *args):
                """
                A method that triggers an event and calls the registered listeners with the given arguments.
                :param event: a string that represents the event name
                :param args: any arguments to be passed to the listeners
                """
                if (not events) or (event in events):
                    listeners = self.eventshub.get(event, [])
                    if (len(args) == 1) and isMapping(args[0]):
                        e = args[0]
                        e.update({"event": event})
                        for listener in listeners:
                            listener(e)
                    else:
                        for listener in listeners:
                            listener(*args)
                else:
                    raise ValueError("Invalid event")

            def subscribe(self, event: str, listener: Callable):
                """
                A method that registers a listener for an event.
                :param event: a string that represents the event name
                :param listener: a callable object that handles the event
                """
                if callable(listener) and ((not events) or (event in events)):
                    self.eventshub.setdefault(event, []).append(listener)
                else:
                    raise ValueError("Invalid event or listener")

            def unsubscribe(self, event: str, listener: Callable):
                """
                A method that unregisters a listener for an event.
                :param event: a string that represents the event name
                :param listener: a callable object that handles the event
                """
                if callable(listener) and ((not events) or (event in events)):
                    if listener in self.eventshub.get(event, []):
                        self.eventshub[event].remove(listener)
                    else:
                        raise ValueError("Invalid event")

        EventsHub.__name__ = klass.__name__ + "(subscribe)"
        return EventsHub


class Proxy(Generic[T]):
    """
    A class that wraps a target object and delegates attribute access to a handler object.
    :param target: the object to be wrapped
    :param handler: the class that defines the custom attribute access methods
    if the handler does not define these methods, the Proxy class will use the methods or properties of the target itself.
    usage:
    ```
    class handler:
        getattr(target, name) -> Any: # defines the behavior when accessing the target's attributes
        setattr(target, name, value) -> None: # defines the behavior when setting the attribute of target
        delattr(target, name) -> None: # defines the behavior when deleting the attribute of target
        getitem(target, key) -> Any: # defines the behavior when accessing the element of target
        setitem(target, key, value) -> None: # defines the behavior when setting the target element
        len(target) -> int: # define the behavior when getting the length of target
        iter(target) -> Iterator: # defines the behavior when iterating target
        keys(target) -> Iterable: # defines the behavior when getting the key set of target

    o = Proxy(object(), handler)
    """

    def __init__(self, target: T, handler: type) -> None:
        self.target = target
        self.handler = handler

    @property
    def __dict__(self):
        return object.__getattribute__(self, "target").__dict__

    def __dir__(self):
        return object.__getattribute__(self, "target").__dir__

    def __getattribute__(self, name):
        target = object.__getattribute__(self, "target")
        func = getattr(object.__getattribute__(self, "handler"), "getattr", undefined)
        if func == undefined:
            return object.__getattribute__(target, name)
        return func(target, name)

    def __setattribute__(self, name, value):
        target = object.__getattribute__(self, "target")
        func = getattr(object.__getattribute__(self, "handler"), "setattr", undefined)
        if func == undefined:
            return object.__setattribute__(target, name, value)
        return func(target, name, value)

    def __delattribute__(self, name):
        target = object.__getattribute__(self, "target")
        func = getattr(object.__getattribute__(self, "handler"), "delattr", undefined)
        if func == undefined:
            return object.__delattribute__(target, name)
        return func(target, name)

    def __getitem__(self, key):
        target = object.__getattribute__(self, "target")
        func = getattr(object.__getattribute__(self, "handler"), "getitem", undefined)
        if func == undefined:
            return target.__getitem__(key)
        return func(target, key)

    def __setitem__(self, key, value):
        target = object.__getattribute__(self, "target")
        func = getattr(object.__getattribute__(self, "handler"), "setitem", undefined)
        if func == undefined:
            return target.__setitem__(key, value)
        return func(target, key, value)

    def __len__(self):
        target = object.__getattribute__(self, "target")
        func = getattr(object.__getattribute__(self, "handler"), "len", undefined)
        if func == undefined:
            return len(target) if isIterable(target) else True
        return func(target)

    def __iter__(self):
        target = object.__getattribute__(self, "target")
        func = getattr(object.__getattribute__(self, "handler"), "iter", undefined)
        if func == undefined:
            return iter(target)
        return func(target)

    def __keys__(self):
        target = object.__getattribute__(self, "target")
        func = getattr(object.__getattribute__(self, "handler"), "keys", undefined)
        if func == undefined:
            return target.__keys__()
        return func(target)


class commands(Generic[T]):
    """
    A decorator that restricts the access to a class's methods to a given list of commands.
    :param commands: a list of strings that represent the allowed methods

    usage:
    ```
    @commands(["add", "sub"]) # only expose the add and sub methods
    class Calculator:
        def add(self, x, y): return x + y
        def sub(self, x, y): return x - y
        def mul(self, x, y): return x * y

    calculator.mul(1, 1) # invalid access Calculator.mul not exposed by commands
    """

    def __init__(self, commands: list) -> None:
        self.commands = commands

    def __call__(self, klass: T) -> T:
        if not isinstance(klass, type):
            raise TypeError("members can only decorate classes")
        commands = self.commands

        class app:
            @wraps(klass.__init__)
            def __init__(self, *args, **kwds):
                self.instance = klass(*args, **kwds)

            def __getattribute__(self, name):
                if name in commands:
                    return getattr(object.__getattribute__(self, "instance"), name)
                else:
                    raise AttributeError(
                        f"invalid access, {name} not exposed by commands"
                    )

        app.__name__ = f'app(${klass.__name__})[{" ".join(self.commands)}]'
        return app


def throttle(interval: int, exit: bool = True):
    """
    A decorator that limits the execution frequency of a function.
    :param interval: the minimum time interval between two executions in seconds
    :param exit: whether to execute the function at the exit of the interval
    """

    def decorator(func: T) -> T:
        timer: Timer = None
        last_time = 0
        now = 0

        @wraps(func)
        def wrapper(*args, immediate=False, **kwds):
            nonlocal last_time
            nonlocal timer
            nonlocal now
            now = time()
            if exit:
                if timer:
                    timer.update(args, kwds)
                else:

                    def inner(args, kwds):
                        nonlocal last_time
                        nonlocal timer
                        timer = None
                        if last_time != now:
                            last_time = now
                            func(*args, **kwds)

                    timer = Timer(True, interval, inner, args, kwds)
                    timer.setDaemon(True)
                    timer.start()

            if immediate or (now - last_time > interval):
                last_time = now
                return func(*args, **kwds)

        return wrapper

    return decorator


def debounce(interval: int, enter: bool = False, exit: bool = True):
    """
    A decorator that delays the execution of a function until it stops being called.
    :param interval: the interval time in seconds
    :param enter: whether to execute the function at the first call
    :param exit: whether to execute the function at the last call
    """
    exit |= not enter

    def decorator(func: T) -> T:
        timer: Timer = None

        @wraps(func)
        def wrapper(*args, immediate=False, **kwds):
            nonlocal timer
            called = immediate or (enter and not timer)

            if timer:
                timer.update(args, kwds)
            else:

                def inner(args, kwds):
                    nonlocal timer
                    timer = None
                    if exit and not called:
                        func(*args, **kwds)

                timer = Timer(True, interval, inner, args, kwds)
                timer.setDaemon(True)
                timer.start()

            if called:
                return func(*args, **kwds)

        return wrapper

    return decorator
