
# 风险评分卡建模工具

一个基于 Python 和 Tkinter 的图形化风险评分卡建模工具，用于信用风险分析和风控建模。

## 功能特性

- **数据导入**：支持多种数据格式导入
- **数据集处理**：数据集分割、抽样等预处理功能
- **特征分箱**：自动分箱与交互式分箱
- **特征工程**：WOE 转换、变量聚类等
- **模型训练**：逻辑回归建模，支持逐步回归
- **评分卡生成**：自动生成评分卡
- **模型评估**：提供模型评估指标和可视化
- **规则集管理**：支持业务规则配置

## 安装

### 环境要求

- Python 3.7+
- 虚拟环境（推荐）

### 安装步骤

1. 克隆项目
```bash
cd scorecard
```

2. 创建并激活虚拟环境
```bash
python -m venv myenv
# Windows
myenv\Scripts\activate
# macOS/Linux
source myenv/bin/activate
```

3. 安装依赖
```bash
pip install -r requirements.txt
```

## 快速开始

### 启动应用

```python
import riskmodeler as rm
rm.scorecard()
```

或者直接运行项目根目录的 `start.py`：
```bash
python start.py
```

### 基本使用流程

1. **创建新项目**：设置项目名称和保存路径
2. **导入数据**：加载训练数据集
3. **数据预处理**：进行数据集分割或抽样
4. **特征分箱**：对变量进行分箱处理
5. **模型训练**：训练评分卡模型
6. **应用评分**：对新数据进行评分

## 项目结构

```
scorecard/
├── myenv/                  # 虚拟环境目录
├── riskmodeler/            # 核心代码包
│   ├── __init__.py        # 包初始化
│   ├── start.py           # 主程序入口
│   ├── base.py            # 基础功能模块
│   ├── func.py            # 分箱函数
│   ├── inputdata.py       # 数据导入模块
│   ├── split.py           # 数据分割模块
│   ├── sampling.py        # 抽样模块
│   ├── interactive_grouping.py  # 交互式分箱
│   ├── model.py           # 建模核心模块
│   ├── model_ui.py        # 建模界面
│   ├── score_ui.py        # 评分界面
│   ├── policy.py          # 规则集模块
│   └── load_node.py       # 节点加载
├── start.py               # 项目启动脚本
├── requirements.txt       # 项目依赖
└── README.md              # 项目说明文档
```

## 核心模块说明

### 1. 数据导入 (inputdata.py)

负责数据加载、预览和基本变量设置。

### 2. 特征分箱 (func.py, base.py)

提供自动分箱、先验分箱和自定义分箱功能，支持 WOE 和 IV 计算。

### 3. 模型训练 (model.py)

实现逻辑回归建模，支持：
- 前向逐步回归
- 双向逐步回归
- 变量筛选
- 模型评估

### 4. 评分应用 (score_ui.py)

将训练好的模型应用到新数据集，生成评分结果。

## 依赖库

- **pandas**: 数据处理
- **numpy**: 数值计算
- **statsmodels**: 统计建模
- **scikit-learn**: 机器学习工具
- **matplotlib**: 数据可视化
- **plotly**: 交互式图表
- **joblib**: 并行计算
- **pandastable**: 表格组件

## 技术特点

- 图形化界面，操作简单
- 完整的建模流程
- 支持交互式分箱调整
- 并行计算优化
- 项目管理和版本保存

## 注意事项

- 本项目使用 pickle 进行数据持久化，请注意版本兼容性
- 建议使用虚拟环境隔离依赖
- 大数据集建议使用抽样功能提高效率

## 更新日志

### v1.0.0
- 初始版本发布
- 基础评分卡建模功能
- 图形化操作界面

## 许可证

本项目仅供学习和研究使用。

## 联系方式

如有问题或建议，请联系项目维护者。

