from datetime import timedelta, datetime
from typing import Dict, List, Optional, Callable
from pandas import DataFrame

import jqdatasdk as jq

from trader.setting import SETTINGS
from trader.constant import Exchange, Interval
from trader.object import BarData, HistoryRequest
from data.datafeed.datafeed import BaseDatafeed
from trader.utility import ZoneInfo, round_to


CHINA_TZ = ZoneInfo("Asia/Shanghai")

Interval_tO_Jqfrequency: Dict[Interval, str] = {
    Interval.MINUTE: "1m",
    Interval.HOUR: "60m",
    Interval.DAILY: "1d",
    Interval.WEEKLY: "7d"
}


INTERVAL_ADJUSTMENT_MAP: dict[Interval, timedelta] = {
    Interval.MINUTE: timedelta(minutes=1),
    Interval.HOUR: timedelta(hours=1),
    Interval.DAILY: timedelta()         # no need to adjust for daily bar
}


class JqdataDatafeed(BaseDatafeed):
    """
    jqdatasdk数据服务接口
    聚宽的试用版支持股票、基金的日线与分钟线行情数据
    """

    def __init__(self) -> None:
        """"""
        self.username: str = SETTINGS["datafeed.username"]
        self.password: str = SETTINGS["datafeed.password"]

        self.inited: bool = False

    def init(self, output: Callable = print) -> bool:
        """初始化"""
        if self.inited:
            return True

        if not self.username:
            output("jqdata数据服务初始化失败，用户名为空！")
            return False

        if not self.password:
            output("jqdata数据服务初始化失败，密码为空！")
            return False

        try:
            jq.auth(self.username, self.password)
        except Exception as ex:
            output(f"发生未知异常：{ex}")

        if not jq.is_auth():
            output(f"jqdata数据服务初始化失败，用户不存在或密码错误, 或未开通调用权限")
            return False

        self.inited = jq.is_auth()
        return True

    def query_bar_history(self, req: HistoryRequest, output: Callable = print) -> Optional[List[BarData]]:
        """查询K线数据"""
        # 检查是否登录
        if not self.inited:
            self.init(output)

        jq_symbol: str = jq.normalize_code(req.symbol)
        exchange: Exchange = req.exchange
        start: datetime = req.start
        end: datetime = req.end
        interval: Interval = req.interval
        jq_frequency: str = Interval_tO_Jqfrequency.get(interval)

        if not jq_frequency:
            output(f"RQData查询K线数据失败：不支持的时间周期{req.interval.value}")
            return []

        df: DataFrame = jq.get_price(
            security=jq_symbol,
            start_date=start,
            end_date=end,
            frequency=jq_frequency,
            fq="post",           # 便于回测，采用后复权数据
            fill_paused=False,    # 使用NAN填充停牌的股票价格
            round=False
        )

        # 为了将聚宽时间戳（K线结束时点）转换为vnpy时间戳（K线开始时点）
        adjustment: timedelta = INTERVAL_ADJUSTMENT_MAP[interval]

        data: List[BarData] = []

        if df is not None:

            for row in df.itertuples():
                dt: datetime = row.Index.to_pydatetime() - adjustment
                dt: datetime = dt.replace(tzinfo=CHINA_TZ)

                if dt >= end:
                    break

                bar: BarData = BarData(
                    symbol=jq_symbol,
                    exchange=exchange,
                    interval=interval,
                    datetime=dt,
                    open_price=round_to(row.open, 0.000001),
                    high_price=round_to(row.high, 0.000001),
                    low_price=round_to(row.low, 0.000001),
                    close_price=round_to(row.close, 0.000001),
                    volume=row.volume,
                    turnover=row.money,
                    gateway_name="JQ"
                )

                data.append(bar)

        return data
