# Logscorecard

一个基于 Python 与 Tkinter 的图形化评分卡建模工具，面向信用风险分析、评分卡训练与打分应用场景。项目将传统评分卡流程拆成可复用的节点，包括数据导入、样本处理、交互分组、逻辑回归建模、评分卡生成与结果应用。

## 项目亮点

- 图形化工作流：适合按步骤完成评分卡建模，不依赖命令行操作
- 完整建模链路：覆盖数据导入、分箱、建模、评分和规则配置
- 交互式分组：支持分组结果查看、调整与刷新
- 项目化管理：通过节点文件保存过程结果，方便回看与复用
- 本地可运行：无服务端依赖，适合研究、教学与内部原型验证

## 当前状态

- 已完成一轮基础重构，拆出了项目存储与部分建模公共逻辑
- 已补充最小测试集，覆盖项目存储和核心建模 helper
- 已优化启动页与数据导入页的 Tkinter 交互样式

## 功能概览

- 数据导入：导入训练集、拒绝样本、时间外样本、打分样本
- 样本处理：分区、抽样与节点复用
- 特征分组：自动分箱、交互式分组、特殊值处理
- 特征工程：WOE 转换、变量聚类
- 模型训练：逻辑回归、逐步回归、分组逻辑回归
- 评分卡应用：模型打分、评分结果输出
- 规则集管理：支持业务规则配置与衍生使用

## 快速开始

### 1. 创建虚拟环境

```bash
python -m venv myenv
source myenv/bin/activate
```

Windows:

```bash
myenv\Scripts\activate
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 启动项目

```bash
python start.py
```

也可以在 Python 中直接启动：

```python
import riskmodeler as rm

rm.scorecard()
```

## 使用流程

1. 创建新项目或导入已有 `.project` 文件
2. 导入训练数据集并设置变量角色
3. 进行样本分区或抽样
4. 创建交互分组节点，完成分箱与变量筛选
5. 创建评分卡模型节点，训练逻辑回归模型
6. 生成评分卡并对新数据执行打分

## 目录结构

```text
scorecard/
├── riskmodeler/
│   ├── __init__.py
│   ├── start.py
│   ├── ui.py
│   ├── project_store.py
│   ├── inputdata.py
│   ├── interactive_grouping.py
│   ├── model.py
│   ├── model_ui.py
│   ├── score_ui.py
│   ├── split.py
│   ├── sampling.py
│   ├── policy.py
│   └── ...
├── tests/
│   ├── conftest.py
│   ├── test_model_helpers.py
│   └── test_project_store.py
├── requirements.txt
├── start.py
└── README.md
```

## 核心模块

- `riskmodeler/start.py`：主程序入口与项目工作台
- `riskmodeler/inputdata.py`：数据集导入、预览与变量角色设置
- `riskmodeler/interactive_grouping.py`：交互式分组与分箱调整
- `riskmodeler/model.py`：评分卡建模核心逻辑
- `riskmodeler/model_ui.py`：模型参数配置与结果展示入口
- `riskmodeler/score_ui.py`：模型打分与结果输出
- `riskmodeler/project_store.py`：项目文件和节点清单的存储辅助
- `riskmodeler/ui.py`：Tkinter 样式与界面布局辅助

## 运行测试

```bash
pytest tests/test_project_store.py tests/test_model_helpers.py
```

## 依赖说明

项目主要依赖：

- `pandas`
- `numpy`
- `statsmodels`
- `scikit-learn`
- `joblib`
- `matplotlib`
- `plotly`
- `pandastable`

## 注意事项

- 项目大量使用本地文件和 `pickle` 保存节点数据，跨 Python 版本时需要关注兼容性
- 建议使用虚拟环境运行，避免依赖污染
- Tkinter 图形界面依赖本机桌面环境，不适合纯无头服务器
- 大样本数据建议先使用抽样或分区节点，减少交互等待时间

## 后续可优化方向

- 继续统一其余 Tkinter 页面交互风格
- 为核心建模流程补充更多自动化测试
- 进一步拆分 `model_ui.py` 和交互分组相关超长模块
- 增加导出模板、项目示例与操作截图

## License

本项目当前仅供学习、研究与内部原型验证使用。
