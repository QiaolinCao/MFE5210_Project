from event.engine import EventEngine
from trader.engine import MainEngine

from trader.ui import MainWindow, create_qapp

# 应用程序
from apps.datamanager import DataManagerApp
from apps.single_asset_backtester import  SingleAssetBacktesterApp


def main():

    qapp = create_qapp()

    event_engine = EventEngine()

    main_engine = MainEngine(event_engine)

    main_engine.add_app(DataManagerApp)
    main_engine.add_app(SingleAssetBacktesterApp)

    main_window = MainWindow(main_engine, event_engine)
    main_window.showMaximized()

    qapp.exec()


if __name__ == "__main__":
    main()
