import pandas as pd

from riskmodeler.project_store import (
    append_or_replace_node,
    build_node_record,
    build_project_record,
    empty_project_detail,
)


def test_append_or_replace_project_node():
    project_detail = empty_project_detail()
    project_detail = append_or_replace_node(
        project_detail,
        build_project_record("demo", "/tmp/demo.project"),
    )

    assert len(project_detail) == 1
    assert project_detail.iloc[0]["模块类型"] == "project"
    assert project_detail.iloc[0]["模块名字"] == "demo"


def test_append_or_replace_keeps_latest_node_by_name():
    project_detail = pd.DataFrame(
        [
            {
                "模块类型": "DATA",
                "模块名字": "train_data",
                "引用模块": [],
                "保存地址": "/tmp/old.dataset",
                "状态": "Good",
                "创建时间": "2026-05-31 10:00:00",
            }
        ]
    )

    node_setting = {
        "node_type": "DATA",
        "node_name": "train_data",
        "use_node": [],
        "node_save_path": "/tmp/new.dataset",
        "time": "2026-05-31 11:00:00",
    }

    updated = append_or_replace_node(project_detail, build_node_record(node_setting))

    assert len(updated) == 1
    assert updated.iloc[0]["保存地址"] == "/tmp/new.dataset"
    assert updated.iloc[0]["创建时间"] == "2026-05-31 11:00:00"
