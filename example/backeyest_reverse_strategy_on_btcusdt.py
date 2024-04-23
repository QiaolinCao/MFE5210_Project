from datetime import datetime
from logging import INFO
import pandas as pd

from event.engine import EventEngine, Event
from trader.engine import MainEngine
from apps.single_asset_backtester.engine import (
    BacktesterEngine,
    EVENT_BACKTESTER_LOG,
    EVENT_BACKTESTER_BACKTESTING_FINISHED,
)
from apps.datamanager.engine import ManagerEngine
from trader.constant import Interval, Exchange


from trader.setting import SETTINGS


SETTINGS["log.active"] = True
SETTINGS["log.level"] = INFO
SETTINGS["log.console"] = True

# 创建事件引擎与主引擎
event_engine = EventEngine()
main_engine = MainEngine(event_engine)
main_engine.write_log("主引擎创建成功")

# 添加数据管理与回测引擎
main_engine.add_engine(ManagerEngine)
main_engine.add_engine(BacktesterEngine)

log_engine = main_engine.get_engine("log")
dm_engine = main_engine.get_engine("DataManager")
bt_engine = main_engine.get_engine("SingleAssetBacktester")


# 注册事件

def show_result(bt_finished: Event):
    KEY_NAME_MAP: dict = {
        "start_date": "首个交易日",
        "end_date": "最后交易日",

        "total_days": "总交易日",
        "profit_days": "盈利交易日",
        "loss_days": "亏损交易日",

        "capital": "起始资金",
        "end_balance": "结束资金",

        "total_return": "总收益率%",
        "annual_return": "年化收益%",
        "max_drawdown": "最大回撤",
        "max_ddpercent": "百分比最大回撤%",

        "total_net_pnl": "总盈亏",
        "total_commission": "总手续费",
        "total_slippage": "总滑点",
        "total_turnover": "总成交额",
        "total_trade_count": "总成交笔数",

        "daily_net_pnl": "日均盈亏",
        "daily_commission": "日均手续费",
        "daily_slippage": "日均滑点",
        "daily_turnover": "日均成交额",
        "daily_trade_count": "日均成交笔数",

        "daily_return": "日均收益率%",
        "return_std": "收益标准差",
        "sharpe_ratio": "夏普比率",
        "return_drawdown_ratio": "收益回撤比"
    }
    statistics = bt_engine.get_result_statistics()
    df = pd.DataFrame(statistics, index=["数值"])
    df.rename(columns=KEY_NAME_MAP, inplace=True)
    print(df.T)
    bt_engine.backtesting_engine.show_chart()


event_engine.register(EVENT_BACKTESTER_LOG, log_engine.process_log_event)
event_engine.register(EVENT_BACKTESTER_BACKTESTING_FINISHED, show_result)
main_engine.write_log("事件注册完成")

# 初始化回测引擎
bt_engine.init_engine()
bt_engine.write_log("回测引擎初始化成功")
bt_engine.init_datafeed()
bt_engine.load_strategy_class()


# 导入数据
overviews = dm_engine.get_bar_overview()

import_data = True
for overview in overviews:
    if overview.symbol == "btcusdt":
        import_data = False

file_path = "btcusdt_1m.csv"
symbol = "btcusdt"
exchange = Exchange.BINANCE
interval = Interval.MINUTE
tz_name = "Asia/Shanghai"
datetime_head = "datetime"
open_head = "open"
high_head = "high"
low_head = "low"
close_head = "close"
volume_head = "volume"
turnover_head = "turnover"
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
    main_engine.write_log("已有数据：cusdt")


# 回测设置
Reversal_setting = {
    "boll_window": 360,
    "boll_dev": 2
}

bt_engine.start_backtesting(
    class_name="Reversal",
    vt_symbol="btcusdt.BINANCE",
    interval=Interval.MINUTE.value,
    start=datetime(2022,1,1),
    end=datetime(2024,3,1),
    rate=0.00075,     
    slippage=0.0002,  # 平均滑点0.02%，见https://www.wwsww.cn/jiaoyisuo/8317.html
    size=1,
    pricetick=0.1,    # 最小价格变动
    capital=1000000,
    setting=Reversal_setting
)

