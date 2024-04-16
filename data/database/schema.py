from datetime import datetime
from typing import Optional
from tortoise import fields
from tortoise.models import Model


class DbBarData(Model):
    """K线数据表映射对象"""

    id: int = fields.IntField(pk=True)

    symbol: str = fields.CharField(max_length=64)
    exchange: str = fields.CharField(max_length=64)
    datetime: datetime = fields.DatetimeField()
    interval: str = fields.CharField(max_length=16)

    volume: float = fields.FloatField()
    turnover: float = fields.FloatField()
    open_interest: float = fields.FloatField()
    open_price: float = fields.FloatField()
    high_price: float = fields.FloatField()
    low_price: float = fields.FloatField()
    close_price: float = fields.FloatField()

    class Meta:
        table: str = "db_bar_data"
        indexes: list = [(("symbol", "exchange", "interval", "datetime"), True)]


class DbTickData(Model):
    """TICK数据表映射对象"""

    id = fields.IntField(pk=True)

    symbol: str = fields.CharField(max_length=64)
    exchange: str = fields.CharField(max_length=64)
    datetime: datetime = fields.DatetimeField()

    name: str = fields.CharField(max_length=128)
    volume: float = fields.FloatField()
    turnover: float = fields.FloatField()
    open_interest: float = fields.FloatField()
    last_price: float = fields.FloatField()
    last_volume: float = fields.FloatField()
    limit_up: float = fields.FloatField()
    limit_down: float = fields.FloatField()

    open_price: float = fields.FloatField()
    high_price: float = fields.FloatField()
    low_price: float = fields.FloatField()
    pre_close: float = fields.FloatField()

    bid_price_1: float = fields.FloatField()
    bid_price_2: Optional[float] = fields.FloatField(null=True)
    bid_price_3: Optional[float] = fields.FloatField(null=True)
    bid_price_4: Optional[float] = fields.FloatField(null=True)
    bid_price_5: Optional[float] = fields.FloatField(null=True)

    ask_price_1: float = fields.FloatField()
    ask_price_2: Optional[float] = fields.FloatField(null=True)
    ask_price_3: Optional[float] = fields.FloatField(null=True)
    ask_price_4: Optional[float] = fields.FloatField(null=True)
    ask_price_5: Optional[float] = fields.FloatField(null=True)

    bid_volume_1: float = fields.FloatField()
    bid_volume_2: Optional[float] = fields.FloatField(null=True)
    bid_volume_3: Optional[float] = fields.FloatField(null=True)
    bid_volume_4: Optional[float] = fields.FloatField(null=True)
    bid_volume_5: Optional[float] = fields.FloatField(null=True)

    ask_volume_1: float = fields.FloatField()
    ask_volume_2: Optional[float] = fields.FloatField(null=True)
    ask_volume_3: Optional[float] = fields.FloatField(null=True)
    ask_volume_4: Optional[float] = fields.FloatField(null=True)
    ask_volume_5: Optional[float] = fields.FloatField(null=True)

    localtime: Optional[datetime] = fields.DatetimeField(null=True)

    class Meta:
        table: str = "db_tick_data"
        indexes: list = [(("symbol", "exchange", "datetime"), True)]


class DbBarOverview(Model):
    """K线汇总数据表映射对象"""

    id: int = fields.IntField(pk=True)

    symbol: str = fields.CharField(max_length=64)
    exchange: str = fields.CharField(max_length=64)
    interval: str = fields.CharField(max_length=16)
    count: int = fields.IntField()
    start: datetime = fields.DatetimeField()
    end: datetime = fields.DatetimeField()

    class Meta:
        table: str = "db_bar_overview"
        indexes: list = [(("symbol", "exchange", "interval"), True)]


class DbTickOverview(Model):
    """Tick汇总数据表映射对象"""

    id: int = fields.IntField(pk=True)

    symbol: str = fields.CharField(max_length=64)
    exchange: str = fields.CharField(max_length=64)
    count: int = fields.IntField()
    start: datetime = fields.DatetimeField()
    end: datetime = fields.DatetimeField()

    class Meta:
        table: str = "db_tick_overview"
        indexes: list = [(("symbol", "exchange"), True)]
