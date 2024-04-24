# MFE5210_Project
MFE5210_Group_Project

源自vnpy的事件驱动回测框架

目前具有以下功能：

1.数据管理
  源自vnpy_datamanager, 是包括数据获取、数据存储与查询、数据导入导出功能的数据管理器。
  其中，数据获取依赖于datafeed模块, 即数据服务。目前基于datafeed的基类开发了聚宽数据得接口，支持获取股票、基金的bar数据
  数据存储与查询依赖于database模块，即数据库。目前，本项目支持sqlite数据库，以及基于database基类，用Tortoise-orm管理，支持异步操作的mysql数据库。
  目前，数据管理支持读取csv文件并存储入数据库，以及从数据库中查询数据并导出为csv文件。

2.单资产回测
  源自vnpy_ctabacktester以及vnpy_ctastrategy。
  支持用户基于CtaTemplate编写基于事件驱动的交易策略，进行回测，汇报策略的回测结果，以及进行参数优化。
  
