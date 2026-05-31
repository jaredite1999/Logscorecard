"""
项目文件与节点清单的存储辅助工具。
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import datetime as dt
import pickle
from typing import Any

import pandas as pd


PROJECT_COLUMNS = ["模块类型", "模块名字", "引用模块", "保存地址", "状态", "创建时间"]


@dataclass(frozen=True)
class NodeRecord:
    node_type: str
    node_name: str
    use_node: list[Any]
    save_path: str
    created_at: str
    status: str = "Good"

    def to_dict(self) -> dict[str, Any]:
        return {
            "模块类型": self.node_type,
            "模块名字": self.node_name,
            "引用模块": self.use_node,
            "保存地址": self.save_path,
            "状态": self.status,
            "创建时间": self.created_at,
        }


def empty_project_detail() -> pd.DataFrame:
    return pd.DataFrame(columns=PROJECT_COLUMNS)


def build_project_record(project_name: str, project_path: str) -> NodeRecord:
    return NodeRecord(
        node_type="project",
        node_name=project_name,
        use_node=[],
        save_path=project_path,
        created_at=dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    )


def build_node_record(node_setting: dict[str, Any]) -> NodeRecord:
    return NodeRecord(
        node_type=node_setting["node_type"],
        node_name=node_setting["node_name"],
        use_node=node_setting["use_node"],
        save_path=node_setting["node_save_path"],
        created_at=node_setting["time"],
    )


def append_or_replace_node(project_detail: pd.DataFrame, record: NodeRecord) -> pd.DataFrame:
    filtered = project_detail[project_detail["模块名字"] != record.node_name].copy()
    row = pd.DataFrame([record.to_dict()], columns=PROJECT_COLUMNS)
    return pd.concat([filtered, row], ignore_index=True)


def mark_project_path(project_detail: pd.DataFrame, project_path: str) -> pd.DataFrame:
    result = project_detail.copy()
    mask = result["模块类型"] == "project"
    result.loc[mask, "保存地址"] = project_path
    return result


def load_project(project_path: str) -> pd.DataFrame:
    with open(project_path, "rb") as file_obj:
        data = pickle.load(file_obj)
    project_detail = pd.DataFrame(data).copy()
    for column in PROJECT_COLUMNS:
        if column not in project_detail.columns:
            project_detail[column] = None
    return project_detail[PROJECT_COLUMNS]


def save_project(project_detail: pd.DataFrame, project_path: str) -> None:
    path = Path(project_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "wb") as file_obj:
        pickle.dump(project_detail, file_obj, 1)


def load_pickle_file(file_path: str) -> Any:
    with open(file_path, "rb") as file_obj:
        return pickle.load(file_obj)
