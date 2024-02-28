"""
参考 VNPY的 Event-driven framework
"""

from typing import Any, Callable, List
from threading import Thread
from queue import Empty, Queue
from collections import defaultdict
import time
from trader.constant import EventType


class Event:
    """
    事件基类
    所有事件共有的属性包括：事件名称、事件数据
    """
    def __init__(self, event_type: str, data: Any = None) -> None:
        
        self.type: str = event_type
        self.data: Any = data


# 时间事件的类型
EVENT_TIMER = "eTimer"

# handler函数的注释类别； 为Callabel类别，接受参数为事件，返回None
HandlerType: callable = Callable[[Event], None]


class EventEngine:
    """
    Event engine distributes event object based on its type
    to those handlers registered.

    It also generates timer event by every interval seconds,
    which can be used for timing purpose.

    主线程：分发事件队列里的事件
    事件线程：往事件队列里添加事件事件

    """
    def __init__(self, interval: int = 1) -> None:
        """
        Timer event is generated every 1 second by default, if
        interval not specified.
        """
        self._active: bool = False
        self._queue: Queue = Queue()
        self._handlers: defaultdict = defaultdict(list)
        self._general_handlers: List = []
        self._thread: Thread = Thread(target=self._run)
        self._interval: int = interval
        self._timer: Thread = Thread(target=self._run_timer)

    def _run(self) -> None:
        """
        运行时，从事件队列不断事件，
        并通过_process分发给不同类型的处理器
        """
        while self._active:
            try:
                event: Event = self._queue.get(block=True, timeout=1)
                self._process(event)
            except Empty:
                pass

    def _process(self, event: Event) -> None:
        """
        First distribute event to those handlers registered listening
        to this type.

        Then distribute event to those general handlers which listens
        to all types.
        """
        if event.type in self._handlers:
            [handler(event) for handler in self._handlers[event.type]]

        if self._general_handlers:
            [handler(event) for handler in self._general_handlers]

    def _run_timer(self) -> None:
        """
        Sleep by interval second(s) and then generate a timer event.
        """
        while self._active:
            time.sleep(self._interval)
            event: Event = Event(EVENT_TIMER)
            self.put(event)

    def put(self, event: Event) -> None:
        """
        将事件加入事件队列
        """
        self._queue.put(event)

    def start(self) -> None:
        """
        开启事件引擎
        分发、处理事件
        生成时间事件
        """
        self._active = True
        self._thread.start()
        self._timer.start()

    def stop(self) -> None:
        """
        关闭事件引擎
        """
        self._active = False
        self._timer.join()
        self._thread.join()

    def register(self, event_type: str, handler: HandlerType) -> None:
        """
        依据事件类别，注册新的处理函数
        对于每一事件类别，同一处理函数仅能被注册一次
        """
        handler_lst: list = self._handlers[event_type]

        if handler not in handler_lst:
            handler_lst.append(handler)

    def unregister(self, event_type: str, handler: HandlerType) -> None:
        """
        注销某一处理函数
        """
        handler_lst: list = self._handlers[event_type]

        if handler in handler_lst:
            handler_lst.remove(handler)

        if not handler_lst:
            self._handlers.pop(event_type)

    def register_general(self, handler: HandlerType) -> None:

        if handler not in self._general_handlers:
            self._general_handlers.append(handler)

    def unregister_general(self, handler: HandlerType) -> None:

        if handler in self._general_handlers:
            self._general_handlers.remove(handler)
