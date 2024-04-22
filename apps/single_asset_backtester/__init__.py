from pathlib import Path
from apps.baseapp import BaseApp
from .engine import BacktesterEngine, APP_NAME


class SingleAssetBacktesterApp(BaseApp):
    """"""

    app_name: str = APP_NAME
    app_module: str = "apps.single_asset_backtester"
    app_path: Path = Path(__file__).parent
    display_name: str = "单资产回测"
    engine_class: BacktesterEngine = BacktesterEngine
    widget_name: str = "BacktesterManager"
    icon_name: str = str(app_path.joinpath("ui", "backtester.ico"))