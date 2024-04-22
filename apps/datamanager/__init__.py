"""
源自vnpy
"""

from pathlib import Path


from apps.baseapp import BaseApp

from .engine import APP_NAME, ManagerEngine


class DataManagerApp(BaseApp):
    """"""

    app_name: str = APP_NAME
    app_module: str = "apps.datamanager"
    app_path: Path = Path(__file__).parent
    display_name: str = "数据管理"
    engine_class: ManagerEngine = ManagerEngine
    widget_name: str = "ManagerWidget"
    icon_name: str = str(app_path.joinpath("ui", "manager.ico"))
