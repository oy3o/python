# oy3o

[![PyPI version](https://badge.fury.io/py/oy3o.svg)](https://badge.fury.io/py/oy3o)
[English README (英文版 README)](README.md)

一个用于构建文本用户界面 (TUI) 的 Python 库，提供基于 `curses` 的交互式组件（例如多行文本编辑器、可滚动列表视图）和灵活的输入处理。

**注意:** 这个库依赖于 Python 的 `curses` 模块，该模块在类 Unix 系统 (Linux, macOS) 上通常是标准库的一部分，但在 Windows 上默认不可用。Windows 用户可能需要安装 `windows-curses` 包 (`pip install windows-curses`)，但兼容性可能需要进一步测试。

## 特性 (Features)

*   **交互式组件:**
    *   基于 `curses` 的可编辑文本框/编辑器 (`oy3o.editor.Editor`)。
        *   支持基本的文本导航 (上下左右，行首行尾)。
        *   支持文本换行和视图滚动。
    *   可滚动的列表视图 (`oy3o.flow.View`)。
        *   显示 `oy3o.list.List` 的内容。
        *   支持键盘和鼠标滚轮滚动。
        *   自动滚动到新添加的条目。
*   **高级输入处理 (`oy3o.input`):**
    *   监听并响应单个按键，包括修饰键 (Ctrl)。
    *   处理特殊键（方向键、回车、退格等）。
    *   捕获鼠标事件：点击、滚动（向上/向下）和移动（包括坐标和修饰键状态，如 Ctrl+Alt+Move）。
    *   通过 `onkey`, `onmouse`, `onchar` 将函数绑定到特定的按键、鼠标或字符事件。
    *   提供主输入循环 (`listen()`) 来处理事件流。
    *   **注意:** `input.ALT` 目前主要用于鼠标事件，因为 Alt + 字母键 通常会被操作系统或终端拦截。
*   **数据结构 (`oy3o.list`):**
    *   `List`: 一个可观察的列表，当其内容更改时可以触发事件，与 `Flow` 和 `View` 等组件集成。
*   **宽字符支持:** 集成了 `wcwidth` 以正确处理宽字符（例如 CJK 字符）。
*   **实用工具 (`oy3o._`):** 包含一些实用的工具和装饰器，如事件订阅 (`@subscribe`)、节流 (`@throttle`)、防抖 (`@debounce`)、任务管理 (`Task`, `Timer`)、元编程助手 (`@members`, `@template`, `Proxy`) 等。(详见下文)。
*   **Token 计数:** 集成了 `tiktoken` 用于 token 计数。
*   **系统剪贴板:** 支持通过 `pyperclip` 进行系统剪贴板的复制/粘贴操作。

## 安装 (Installation)

你可以通过 pip 从 PyPI 安装 `oy3o`：

```bash
pip install oy3o
```

## 模块化运行 (Command-Line Piping)

`oy3o` 的一些模块可以直接通过 `python -m` 从命令行运行，并支持从标准输入管道输入内容：

*   **编辑器 (`oy3o.editor`):**
    ```bash
    cat some_file.txt | python -m oy3o.editor
    ```
    这会将 `some_file.txt` 的内容加载到编辑器中。编辑完成后，按 `Ctrl+D` 保存并退出，内容将打印到标准输出；按 `Esc` 取消。

*   **流视图 (`oy3o.flow`):**
    ```bash
    cat some_file.txt | python -m oy3o.flow
    ```
    这会将 `some_file.txt` 的每一行作为列表项显示在可滚动的流视图中。按 `q` 退出。

## 基本用法 - 编辑器 (`oy3o.editor`)

下面是一个简单的例子，演示如何在终端中启动一个基本的 `oy3o` 编辑器：

```python
import curses
from oy3o.editor import Editor

def main(stdscr):
    # 创建 Editor 实例
    # Editor 在给定的 window 内根据 top/bottom/left/right 绘制和管理其区域
    editor = Editor(
        window=stdscr,       # 指定父窗口为 stdscr
        top=1,               # 编辑器区域顶部边距 (从 stdscr 第 1 行开始)
        bottom=1,            # 编辑器区域底部边距 (距离 stdscr 底部 1 行)
        left=1,              # 编辑器区域左侧边距 (从 stdscr 第 1 列开始)
        right=1,             # 编辑器区域右侧边距 (距离 stdscr 右侧 1 列)
        text="你好，世界！\n这是 oy3o 编辑器。\n按 Ctrl+D 保存并退出。\n按 Esc 取消。", # 初始文本
        editable=True        # 允许编辑
    )

    # (可选) 在编辑器外部添加一些提示信息
    stdscr.addstr(0, 1, "oy3o 编辑器示例 - Ctrl+D 退出 / Esc 取消")
    stdscr.refresh() # 刷新父窗口以显示提示

    # 启动编辑器的主循环
    # edit() 方法会接管输入，直到用户退出 (例如按 Ctrl+D 或 Esc)
    final_text = editor.edit()

    # curses.wrapper 会自动处理 curses.endwin() 来恢复终端

    # 返回结果，以便在 curses 环境结束后打印
    return final_text

if __name__ == "__main__":
    # 使用 curses.wrapper 来安全地初始化和清理 curses 环境
    result = curses.wrapper(main)

    # 在 curses 环境关闭后打印结果
    print("\n--- 编辑器会话结束 ---")
    if result is not None:
        # 根据你的 editor.edit() 实现，确认返回的是最终文本还是其他
        print("提交的内容:")
        print(result)
    else:
        # 这取决于 edit() 在取消时返回什么，可能返回 None 或原始文本
        print("编辑已取消。")

```

## 基本用法 - 流视图 (`oy3o.flow`)

`oy3o.flow.View` 类可以将 `oy3o.list.List` 的内容显示在一个可滚动的 `curses` 窗口中。

```python
import curses
from oy3o import input
from oy3o.list import List
from oy3o.flow import View
import time # 用于演示动态添加内容

def main(stdscr):
    curses.curs_set(0) # 隐藏光标
    stdscr.nodelay(True) # 非阻塞输入

    # 创建一个 List 实例
    data_list = List([f"初始行 {i}" for i in range(20)])

    # 在 stdscr 中创建一个 View
    # y, x, height, width 定义了 View 在 stdscr 内的区域
    # 使用 with 语句确保资源被正确清理
    with View(data_list, stdscr, y=1, x=1, height=curses.LINES - 2, width=curses.COLS - 2) as view:
        stdscr.addstr(0, 1, "oy3o 流视图示例 - 按 'q' 退出, 'a' 添加行, 滚轮滚动")
        stdscr.refresh()

        # 启动输入监听
        # view.listen() 会处理鼠标滚动等内部事件
        # input.listen() 是外部事件循环
        counter = 20
        for wc in input.listen(stdscr, delay=0.05): # delay 减少 CPU 占用
            if wc == 'q':
                input.stop() # 停止 input.listen() 循环
                break
            elif wc == 'a':
                data_list.append(f"新添加的行 {counter}")
                counter += 1
            # view.render() 会在 data_list 更新时自动调用 (通过订阅)
            # 如果需要手动刷新或处理其他逻辑，可以在这里添加

            # 模拟外部数据更新
            # if time.time() % 5 < 0.05: # 大约每5秒添加一次
            #     data_list.append(f"定时添加的行 {counter}")
            #     counter += 1
    
    # curses.wrapper 会处理 curses.endwin()

if __name__ == "__main__":
    curses.wrapper(main)
    print("流视图已关闭。")
```

## 进阶用法 - 输入处理 (`oy3o.input`)

`oy3o.input` 模块提供了更底层的接口来处理键盘和鼠标输入。

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

`input.ALT` 是仅鼠标可用的, 因为 `ALT + Key` 总是会响应系统快捷键.
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

## 实用工具 (`oy3o`)

`oy3o` 模块提供了一系列可重用的实用程序类、装饰器和辅助函数，它们在 `oy3o` 库内部使用，也可供直接使用。

```python
from oy3o import Task, Timer, throttle, debounce, subscribe, members, template # 等等
```

主要组件包括：

### 装饰器 (Decorators)

*   **`@throttle(interval: int, exit: bool = True)`**: 限制函数调用频率（速率限制）。确保函数每 `interval` 秒最多执行一次。`exit=True` 会将最后一次调用的参数排队，在间隔结束后执行。请参阅 `_.py` 中的代码示例。
*   **`@debounce(interval: int, enter: bool = False, exit: bool = True)`**: 延迟函数执行，直到自上次调用以来经过了 `interval` 秒且没有新的调用。适用于在活动暂停后执行的操作（例如，停止输入后进行搜索）。`enter=True` 在首次调用时执行，`exit=True` 在暂停后执行。请参阅 `_.py` 中的代码示例。
*   **`@members(*args)`**: 向类添加默认属性（例如 `("name", default_value)`），并通过 `deepcopy` 正确处理可变类型默认值。请参阅 `_.py` 中的代码示例。
*   **`@subscribe(events: list[str] = [], single: bool = False)`**: 向类添加简单的发布/订阅事件系统（`trigger`, `subscribe`, `unsubscribe` 方法）。`events` 限制允许的事件名称。`single=True` 使所有实例共享同一个事件中心。请参阅 `_.py` 中的代码示例。
*   **`@template(declare: T)`**: 基于签名和类型提示实现泛型函数（模板），类似于 `functools.singledispatch` 但匹配完整签名。需要使用 `@template_instance.register` 注册具体实现。请参阅 `_.py` 中的代码示例。
*   **`@commands(commands: list)`**: 包装一个类，将外部访问限制为 `commands` 列表中指定的方法。请参阅 `_.py` 中的代码示例。

### 实用类 (Utility Classes)

*   **`Task(func: Callable, ...)`**: 包装函数调用，以支持同步 (`.do()`)、线程 (`.threading()`) 或异常处理 (`.catch()`) 执行。通过 `.do()` 中的 `asyncio.run` 处理异步函数。请参阅 `_.py` 中的代码示例。
*   **`Timer(once: bool, interval: int, function: Callable, ...)`**: 增强版的 `threading.Timer`，支持重复执行 (`once=False`) 并在不重启的情况下更新参数 (`.update()`)。请参阅 `_.py` 中的代码示例。
*   **`Proxy(target: T, handler: type)`**: 实现代理模式，将属性/项的访问委托给 `handler` 类。请参阅 `_.py` 中的代码示例。
*   **`List(list)`**: `oy3o.list.List` 是一个可观察的列表。当其内容通过 `append`, `extend`, `insert`, `pop`, `remove`, `clear`, `__setitem__`, `__delitem__` 等方法更改时，它会触发 "update" 事件。`Flow` 和 `View` 组件订阅此事件以自动刷新其显示。

### 辅助函数与常量 (Helper Functions & Constants)

*   包括类型检查器 (`isIterable`, `isAsync` 等)、一个唯一的 `undefined` 哨兵对象，以及 Numba 类型别名。

*(有关详细实现和文档字符串，请参阅 `src/oy3o/_.py` 和 `src/oy3o/list.py` 中的源代码。)*

## 许可证 (License)

本项目采用 MIT 许可证。详情请参阅 [LICENSE](LICENSE) 文件。

## 贡献 (Contributing)

欢迎贡献！请随时提出问题 (Issues) 或提交拉取请求 (Pull Requests)。

## 致谢 (Acknowledgements)

*   感谢 `curses` 库提供强大的终端控制能力。
*   感谢 `wcwidth` 库帮助正确处理字符宽度。
