"""
@author: XuYangtao
"""
import numpy as np
from decimal import Decimal

from strategies.template import CtaTemplate
from trader.object import (TickData, BarData, TradeData, OrderData, StopOrder)
from trader.utility import BarGenerator, ArrayManager


class Reversal(CtaTemplate):
    author = "Xu Yangtao"

    boll_window = 360
    boll_dev = 2
    positive_limit = 0.00029
    negative_limit = -0.00018
    weights = np.arange(1, 361)
    weights = weights / sum(weights)

    buy_price = 0
    short_price = 0
    boll_up = 0
    boll_down = 0
    reversal = 0
    last_15_closes = 0
    PB = 0
    timer = 0
    sign_trade = 0

    parameters = ["boll_window", "boll_dev","positive_limit","negative_limit"]
    variables = ["boll_up", "boll_down", "reversal"]

    def __init__(self, cta_engine, strategy_name, vt_symbol, setting):
        """"""
        super().__init__(cta_engine, strategy_name, vt_symbol, setting)

        self.bg = BarGenerator(self.on_bar)
        self.am = ArrayManager(3000)

    def on_init(self):
        """
        Callback when strategy is inited.
        """
        self.write_log("策略初始化")
        self.load_bar(30)

    def on_start(self):
        """
        Callback when strategy is started.
        """
        self.write_log("策略启动")
        self.put_event()
        # self.timer = 100

    def on_stop(self):
        """
        Callback when strategy is stopped.
        """
        self.write_log("策略停止")

        self.put_event()

    def on_tick(self, tick: TickData):
        """
        Callback of new tick data update.
        """
        self.bg.update_tick(tick)

    def on_bar(self, bar: BarData):
        """
        Callback of new bar data update.
        """

        self.timer += 1

        am = self.am
        am.update_bar(bar)
        if not am.inited:
            return

        self.boll_up, self.boll_down = am.boll(self.boll_window, self.boll_dev)
        self.PB = (am.close[-1] - self.boll_down) / (self.boll_up - self.boll_down)

        self.last_15_returns = am.close[-360:] / am.open[-360:] - 1  # get the last 15 close prices
        self.reversal = np.dot(self.last_15_returns, self.weights)



        if self.timer >= 240:
            if self.pos < 0:
                price = Decimal(am.close[-1])
                self.cover(price, abs(self.pos))
                self.sign_trade = 0

            if self.pos > 0:
                price = Decimal(am.close[-1])
                self.sell(price, abs(self.pos))
                self.sign_trade = 0


        if (am.close[-1] > self.boll_up or am.close[-1] < self.boll_down) and self.reversal > self.positive_limit:  #
            self.short_price = Decimal(am.close[-1])
            self.short(self.short_price, 1)
            self.sign_trade = "SHORT"
            self.timer = 0

        if (am.close[-1] > self.boll_up or am.close[-1] < self.boll_down) and self.reversal < self.negative_limit:  #
            self.buy_price = Decimal(am.close[-1])
            self.buy(self.buy_price, 1)
            self.sign_trade = "LONG"
            self.timer = 0

        self.put_event()

    def on_order(self, order: OrderData):
        """
        Callback of new order data update.
        """
        pass

    def on_trade(self, trade: TradeData):
        """
        Callback of new trade data update.
        """
        self.sign_trade = 0
        self.put_event()

    def on_stop_order(self, stop_order: StopOrder):
        """
        Callback of stop order update.
        """
        pass






