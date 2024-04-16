from datetime import datetime
from vnpy.event import EventEngine, Event
from vnpy.trader.engine import MainEngine
from vnpy_ctastrategy import CtaStrategyApp
from vnpy_ctabacktester import CtaBacktesterApp
from vnpy_ctabacktester.engine import (BacktesterEngine, EVENT_BACKTESTER_LOG, EVENT_BACKTESTER_BACKTESTING_FINISHED,
                                       EVENT_BACKTESTER_OPTIMIZATION_FINISHED)
from vnpy_datamanager import DataManagerApp
from vnpy.trader.constant import Interval, Exchange
import time

from logging import INFO
from vnpy.trader.setting import SETTINGS


SETTINGS["log.active"] = True
SETTINGS["log.level"] = INFO
SETTINGS["log.console"] = True

# 创建事件引擎与主引擎
event_engine = EventEngine()
main_engine = MainEngine(event_engine)
main_engine.write_log("主引擎创建成功")
main_engine.add_app(CtaStrategyApp)
main_engine.add_app(CtaBacktesterApp)
main_engine.add_app(DataManagerApp)


# 注册事件
def write_log(event: Event):
    main_engine.write_log(event.data)


def show_result(bt_finished: Event):
    print(bt_engine.result_statistics)
    bt_engine.backtesting_engine.show_chart()


event_engine.register(EVENT_BACKTESTER_LOG, write_log)
event_engine.register(EVENT_BACKTESTER_BACKTESTING_FINISHED, show_result)
main_engine.write_log("事件注册完成")

# 初始化回测引擎
bt_engine = main_engine.get_engine("CtaBacktester")
bt_engine.init_engine()
bt_engine.write_log("回测引擎初始化成功")
bt_engine.init_datafeed()
bt_engine.load_strategy_class()


# 导入数据
dm_engine = main_engine.engines["DataManager"]
overviews = dm_engine.get_bar_overview()

import_data = True
for overview in overviews:
    if overview.symbol == "A2307":
        import_data = False

file_path = "D:\\Documents\\cta_backtet_demo\\A2307_1m.DCE.csv"
symbol = "A2307"
exchange = Exchange.DCE
interval = Interval.MINUTE
tz_name = "Asia/Shanghai"
datetime_head = "datetime"
open_head = "open"
high_head = "high"
low_head = "low"
close_head = "close"
volume_head = "volume"
turnover_head = "total_turnover"
open_interest_head = "open_interest"
datetime_format = "%Y-%m-%d %H:%M:%S"

if import_data:
    start, end, count = dm_engine.import_data_from_csv(
        file_path,
        symbol,
        exchange,
        interval,
        tz_name,
        datetime_head,
        open_head,
        high_head,
        low_head,
        close_head,
        volume_head,
        turnover_head,
        open_interest_head,
        datetime_format,
    )

    msg: str = f"\
            CSV载入成功\n\
            代码：{symbol}\n\
            交易所：{exchange.value}\n\
            周期：{interval.value}\n\
            起始：{start}\n\
            结束：{end}\n\
            总数量：{count}\n\
            "
    main_engine.write_log(msg)
else:
    main_engine.write_log("已有数据：A2307")


# 回测设置
DoubleMa_setting = {
    "fast_window": 10,
    "slow_window": 60
}

result = bt_engine.start_backtesting(
    class_name="DoubleMaStrategy",
    vt_symbol="A2307.DCE",
    interval=Interval.MINUTE.value,
    start=datetime.strptime("2023-04-07", "%Y-%m-%d"),
    end=datetime.strptime("2023-06-12", "%Y-%m-%d"),
    rate=0.000025,
    slippage=0.2,
    size=10,
    pricetick=1,
    capital=1000000,
    setting=DoubleMa_setting
)

if result:
    print("回测成功")
