import asyncio
from datetime import datetime
from typing import List
from trader.constant import Exchange, Interval
from trader.object import BarData, TickData
from data.database.database import (
    BaseDatabase,
    BarOverview,
    TickOverview,
    DB_TZ,
    convert_tz
)
from trader.setting import SETTINGS
from data.database.schemas import DbBarData, DbTickData, DbBarOverview, DbTickOverview
from tortoise import Tortoise, run_async
from tortoise.queryset import QuerySet

user = SETTINGS["database.user"]
password = SETTINGS["database.password"]
host = SETTINGS["database.host"]
port = SETTINGS["database.port"]
database = SETTINGS["database.database"]
db_url = f"mysql://{user}:{password}@{host}:{port}/{database}"


class MysqlDatabase(BaseDatabase):
    """Mysql数据库接口"""
    def __init__(self) -> None:
        """"""
        self.db_url: str = db_url
        self.db_name: str = database
        self.models: str = "data.database.schemas"
        self.loop = asyncio.get_event_loop()
        self.tortoise = Tortoise()

        run_async(self.connect())

    async def connect(self):
        await self.tortoise.init(
            db_url=self.db_url,
            modules={"models": [self.models]}
        )

        await Tortoise.generate_schemas(safe=True)

    async def disconnect(self):
        await self.tortoise.close_connections()

    def set_loop(self, loop) -> None:
        self.loop = loop

    def save_bar_data(self, bars: List[BarData], stream: bool = False) -> bool:
        """保存K线数据"""
        async def async_func():
            # 读取主键参数
            bar: BarData = bars[0]
            symbol: str = bar.symbol
            exchange: Exchange = bar.exchange
            interval: Interval = bar.interval

            # 将BarData数据转换为字典，并调整时区
            data: list = []

            for bar in bars:
                bar.datetime = convert_tz(bar.datetime)

                d: dict = bar.__dict__
                d["exchange"] = d["exchange"].value
                d["interval"] = d["interval"].value
                d.pop("gateway_name")
                d.pop("vt_symbol")
                data.append(d)

            # 使用bulk_create操作将数据更新到数据库中
            batch_size = 50
            for chunk in [data[i:i+batch_size] for i in range(0, len(data), batch_size)]:
                await DbBarData.bulk_create([DbBarData(**item) for item in chunk])

            # 更新K线汇总数据
            overview: DbBarOverview = await DbBarOverview.filter(
                symbol=symbol,
                exchange=exchange.value,
                interval=interval.value
            ).first()

            if not overview:
                overview: DbBarOverview = DbBarOverview(
                    symbol=symbol,
                    exchange=exchange.value,
                    interval=interval.value,
                    start=bars[0].datetime,
                    end=bars[-1].datetime,
                    count=len(bars)
                )
            elif stream:
                overview.end = bars[-1].datetime
                overview.count += len(bars)
            else:
                overview.start = min(bars[0].datetime, overview.start)
                overview.end = max(bars[-1].datetime, overview.end)

                count: int = await DbBarData.filter(
                    symbol=symbol,
                    exchange=exchange.value,
                    interval=interval.value
                ).count()
                overview.count = count

            await overview.save()
        run_async(async_func())
        return True

    def save_tick_data(self, ticks: List[TickData], stream: bool = False) -> bool:
        """保存TICK数据"""
        async def async_func():

            # 读取主键参数
            tick: TickData = ticks[0]
            symbol: str = tick.symbol
            exchange: Exchange = tick.exchange

            # 将TickData数据转换为字典，并调整时区
            data: list = []

            for tick in ticks:
                tick.datetime = convert_tz(tick.datetime)

                d: dict = tick.__dict__
                d["exchange"] = d["exchange"].value
                d.pop("gateway_name")
                d.pop("vt_symbol")
                data.append(d)

            # 使用bulk_create操作将数据更新到数据库中
            batch_size = 50
            for chunk in [data[i:i + batch_size] for i in range(0, len(data), batch_size)]:
                await DbTickData.bulk_create([DbTickData(**item) for item in chunk])

            # 更新Tick汇总数据
            overview: DbTickOverview = await DbTickOverview.filter(
                symbol=symbol,
                exchange=exchange.value
            ).first()

            if not overview:
                overview: DbTickOverview = DbTickOverview(
                    symbol=symbol,
                    exchange=exchange.value,
                    start=ticks[0].datetime,
                    end=ticks[-1].datetime,
                    count=len(ticks)
                )
            elif stream:
                overview.end = ticks[-1].datetime
                overview.count += len(ticks)
            else:
                overview.start = min(ticks[0].datetime, overview.start)
                overview.end = max(ticks[-1].datetime, overview.end)

                count: int = await DbTickData.filter(
                    symbol=symbol,
                    exchange=exchange.value
                ).count()
                overview.count = count

            await overview.save()

        run_async(async_func())
        return True

    def load_bar_data(
        self,
        symbol: str,
        exchange: Exchange,
        interval: Interval,
        start: datetime,
        end: datetime,
    ) -> List[BarData]:
        """"""
        async def async_func():

            queryset = await (
                DbBarData.filter(
                    symbol=symbol,
                    exchange=exchange.value,
                    interval=interval.value,
                    datetime__gte=start,
                    datetime__lte=end,
                ).order_by("datetime")
            )

            bars: List[BarData] = []
            for db_bar in queryset:
                bar: BarData = BarData(
                    symbol=db_bar.symbol,
                    exchange=Exchange(db_bar.exchange),
                    datetime=datetime.fromtimestamp(db_bar.datetime.timestamp(), DB_TZ),
                    interval=Interval(db_bar.interval),
                    volume=db_bar.volume,
                    turnover=db_bar.turnover,
                    open_interest=db_bar.open_interest,
                    open_price=db_bar.open_price,
                    high_price=db_bar.high_price,
                    low_price=db_bar.low_price,
                    close_price=db_bar.close_price,
                    gateway_name="DB"
                )
                bars.append(bar)

            return bars
        loop = self.loop
        future = asyncio.ensure_future(async_func(), loop=loop)
        loop.run_until_complete(future)
        return future.result()

    def load_tick_data(
        self,
        symbol: str,
        exchange: Exchange,
        start: datetime,
        end: datetime
    ) -> List[TickData]:
        """读取TICK数据"""
        async def async_func():

            queryset: QuerySet = (
                DbTickData.filter(
                    symbol=symbol,
                    exchange=exchange.value,
                    datetime__gte=start,
                    datetime__lte=end
                ).order_by("datetime")
            )

            ticks: List[TickData] = []
            async for db_tick in queryset:
                tick: TickData = TickData(
                    symbol=db_tick.symbol,
                    exchange=Exchange(db_tick.exchange),
                    datetime=datetime.fromtimestamp(db_tick.datetime.timestamp(), DB_TZ),
                    name=db_tick.name,
                    volume=db_tick.volume,
                    turnover=db_tick.turnover,
                    open_interest=db_tick.open_interest,
                    last_price=db_tick.last_price,
                    last_volume=db_tick.last_volume,
                    limit_up=db_tick.limit_up,
                    limit_down=db_tick.limit_down,
                    open_price=db_tick.open_price,
                    high_price=db_tick.high_price,
                    low_price=db_tick.low_price,
                    pre_close=db_tick.pre_close,
                    bid_price_1=db_tick.bid_price_1,
                    bid_price_2=db_tick.bid_price_2,
                    bid_price_3=db_tick.bid_price_3,
                    bid_price_4=db_tick.bid_price_4,
                    bid_price_5=db_tick.bid_price_5,
                    ask_price_1=db_tick.ask_price_1,
                    ask_price_2=db_tick.ask_price_2,
                    ask_price_3=db_tick.ask_price_3,
                    ask_price_4=db_tick.ask_price_4,
                    ask_price_5=db_tick.ask_price_5,
                    bid_volume_1=db_tick.bid_volume_1,
                    bid_volume_2=db_tick.bid_volume_2,
                    bid_volume_3=db_tick.bid_volume_3,
                    bid_volume_4=db_tick.bid_volume_4,
                    bid_volume_5=db_tick.bid_volume_5,
                    ask_volume_1=db_tick.ask_volume_1,
                    ask_volume_2=db_tick.ask_volume_2,
                    ask_volume_3=db_tick.ask_volume_3,
                    ask_volume_4=db_tick.ask_volume_4,
                    ask_volume_5=db_tick.ask_volume_5,
                    localtime=db_tick.localtime,
                    gateway_name="DB"
                )
                ticks.append(tick)

            return ticks

        loop = self.loop
        future = asyncio.ensure_future(async_func(), loop=loop)
        loop.run_until_complete(future)
        return future.result()

    def delete_bar_data(
        self,
        symbol: str,
        exchange: Exchange,
        interval: Interval
    ) -> int:
        """删除K线数据"""
        async def async_func():

            que1 = DbBarData.filter(
                symbol=symbol,
                exchange=exchange.value,
                interval=interval.value
            )

            count: int = await que1.count()

            await que1.delete()

            # 删除K线汇总数据
            que2: QuerySet = DbBarOverview.filter(
                symbol=symbol,
                exchange=exchange.value,
                interval=interval.value
            )

            await que2.delete()

            return count

        loop = self.loop
        future = asyncio.ensure_future(async_func(), loop=loop)
        loop.run_until_complete(future)
        return future.result()

    def delete_tick_data(
        self,
        symbol: str,
        exchange: Exchange
    ) -> int:
        """删除TICK数据"""
        async def async_func():

            que1: QuerySet = DbTickData.filter(
                symbol=symbol,
                exchange=exchange.value
            )

            count: int = await que1.count()
            await que1.delete()

            # 删除Tick汇总数据
            que2: QuerySet = DbTickOverview.filter(
                symbol=symbol,
                exchange=exchange.value
            )

            await que2.delete()

            return count

        loop = self.loop
        future = asyncio.ensure_future(async_func(), loop=loop)
        loop.run_until_complete(future)
        return future.result()

    def get_bar_overview(self) -> List[BarOverview]:
        """查询数据库中的K线汇总信息"""
        async def async_func():

            # 如果已有K线，但缺失汇总信息，则执行初始化
            data_count: int = await DbBarData.all().count()
            overview_count: int = await DbBarOverview.all().count()
            if data_count and not overview_count:
                await self.init_bar_overview()

            queryset: QuerySet = DbBarOverview.all()
            overviews: List[BarOverview] = []
            async for overview in queryset:
                overview.exchange = Exchange(overview.exchange)
                overview.interval = Interval(overview.interval)
                overviews.append(overview)
            return overviews

        loop = self.loop
        future = asyncio.ensure_future(async_func(), loop=loop)
        loop.run_until_complete(future)
        return future.result()

    def get_tick_overview(self) -> List[TickOverview]:
        async def async_func():

            """查询数据库中的Tick汇总信息"""
            queryset: QuerySet = DbTickOverview.all()
            overviews: list = []
            async for overview in queryset:
                overview.exchange = Exchange(overview.exchange)
                overviews.append(overview)
            return overviews

        loop = self.loop
        future = asyncio.ensure_future(async_func(), loop=loop)
        loop.run_until_complete(future)
        return future.result()

    def init_bar_overview(self) -> None:
        async def async_func():

            group_set = set(await DbBarData.all().values_list("symbol", "exchange", "interval"))
            for group in group_set:
                symbol, exchange, interval = group
                queryset: QuerySet = DbBarData.filter(symbol=symbol, exchange=exchange, interval=interval)
                count = await queryset.count()
                start: datetime = await queryset.order_by("datetime").first()
                end: datetime = await queryset.order_by("-datetime").first()
                await DbBarOverview.create(
                    symbol=symbol,
                    exchange=exchange,
                    interval=interval,
                    count=count,
                    start=start,
                    end=end
                )
        run_async(async_func())
