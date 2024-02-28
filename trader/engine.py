"""
参考vnpy
"""
from event.engine import Event, EventEngine
from typing import Dict
from gateway import BaseGateway


class MainEngine:
    """
    交易平台的核心
    """
    def __init__(self, event_engine: EventEngine) -> None:
        # 挂载、启动事件引擎
        if event_engine:
            self.event_engine: EventEngine = event_engine
        else:
            self.event_engine = EventEngine()
        self.event_engine.start()

        # 挂载接口
        self.gateways: Dict[str, BaseGateway]

        """
        未完成
        """
        pass

