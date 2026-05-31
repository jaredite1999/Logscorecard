"""
风险评分卡建模工具包

这个包提供了一个完整的图形化风险评分卡建模解决方案，
包括数据导入、特征分箱、模型训练和评分应用等功能。

主要模块：
- start: 主程序入口，提供图形化界面
- inputdata: 数据导入和处理
- func: 特征分箱函数
- model: 模型训练核心逻辑
"""

from .start import scorecard
from .project_store import PROJECT_COLUMNS

__version__ = "1.0.0"
__all__ = ["scorecard", "PROJECT_COLUMNS"]
