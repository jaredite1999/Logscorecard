import tkinter as tk
from tkinter import ttk
from tkinter import *

import pickle as pickle

from tkinter import filedialog
from .ui import set_window_ready, show_error
class import_node():
    def __init__(self, mainfram, project_info):
        self.root2=mainfram
        self.node_name = None
        self.node_type = None
        self.node_save_path = None
        self.node_current_save_path=None
        self.project_path = self._get_project_row(project_info, '模块类型', 'project')['保存地址']
        self.exist_data = list(project_info['模块名字'])
        self.exist_add = list(project_info['保存地址'])
        self.master = mainfram
        self.load_node()
        self.save = 'N'
    def _get_project_row(self, project_info, column, value):
        matched = project_info[project_info[column] == value]
        if matched.empty:
            raise ValueError(f'未找到 {column}={value} 对应的项目记录')
        return matched.iloc[0]

    def _refresh_form_state(self):
        has_path = bool(str(self.nodeimport_E1.get()).strip())
        has_name = bool(str(self.nodeimport_E2.get()).strip())
        is_duplicate_name = has_name and self.nodeimport_E2.get() in self.exist_data and self.nodeimport_E2.get() != self.node_name
        is_duplicate_path = has_path and self.nodeimport_E1.get() in self.exist_add

        can_import = has_path and has_name and not is_duplicate_name and not is_duplicate_path
        self.confirm_button.configure(state='normal' if can_import else 'disabled')

        if not has_path:
            self.status_var.set('请先选择需要导入的模块文件。')
        elif not has_name:
            self.status_var.set('请确认模块名称后再导入。')
        elif is_duplicate_name:
            self.status_var.set('当前模块名称已存在，请修改名称。')
        elif is_duplicate_path:
            self.status_var.set('该模块文件已在项目中导入，无需重复导入。')
        elif self.node_type:
            self.status_var.set(f'已识别模块类型：{self.node_type}，可以执行导入。')
        else:
            self.status_var.set('已选择文件，请确认模块信息。')

    def load_node(self):
            set_window_ready(self.root2, '导入模块', 560, 250, resizable=False)

            def selectExcelfile():
                sfname = filedialog.askopenfilename(title='选择模块文件', filetypes=[('IGN', '*.IGN'),('DATASET', '*.dataset'),('Sampling', '*.sample'),('Spliting', '*.spliting'),('Model','model')])
                if sfname == '':
                    return
                self.node_current_save_path=sfname
                self.nodeimport_E1.delete(0, 'end')
                self.nodeimport_E1.insert(INSERT, sfname)
                try:
                    with open(sfname, 'rb') as fr:
                        node_info = pickle.load(fr)
                    self.node_data = node_info
                    try:
                        self.node_name=node_info[0]['node_name']
                        self.node_type=node_info[0]['node_type']
                        self.use_node = node_info[0]['use_node']
                        self.node_time=node_info[0]['time']
                        self.node_save_path=node_info[0]['node_save_path']
                        self.nodeimport_E2.delete(0, 'end')
                        self.nodeimport_E2.insert(INSERT, self.node_name)
                        self.label_str.set(self.node_type)
                    except Exception as e:
                        show_error('模块文件解析失败，请确认文件格式正确', e)
                except Exception as e:
                    show_error('读取模块文件失败，请确认文件可用', e)
                self._refresh_form_state()
            L1 = Label(self.root2, text="模块路径")
            L1.grid(column=0, row=0, columnspan=2, sticky=(W))
            self.nodeimport_E1 = Entry(self.root2, width=50,  bd=1)
            self.nodeimport_E1.grid(column=1, row=0, sticky=(W))
            button1 = ttk.Button(self.root2, text='浏览', width=8, command=selectExcelfile)
            button1.grid(column=2, row=0, sticky=(W))

            L1 = Label(self.root2, text="模块名称")
            L1.grid(column=0, row=1, columnspan=2, sticky=(W))
            self.nodeimport_E2 = Entry(self.root2,  width=23, bd=1)
            self.nodeimport_E2.grid(column=1, row=1, sticky=(W))

            L3 = Label(self.root2, text="模块类型")
            L3.grid(column=0, row=2, sticky=(W))
            self.label_str = StringVar()
            warning = Label(self.root2, textvariable=self.label_str)
            warning.grid(column=1, row=2, sticky=(W))

            self.status_var = StringVar(value='请先选择需要导入的模块文件。')
            status_label = Label(self.root2, textvariable=self.status_var, justify=LEFT, wraplength=420, anchor='w')
            status_label.grid(column=0, row=3, columnspan=3, sticky=(W), padx=2, pady=(12, 8))

            self.confirm_button = ttk.Button(self.root2, text='确定')
            self.confirm_button.grid(column=1, row=5, sticky=(W))
            self.confirm_button.bind("<Button-1>", self.save_node)
            self.confirm_button.configure(state='disabled')
            self.nodeimport_E1.bind('<KeyRelease>', lambda event: self._refresh_form_state(), add='+')
            self.nodeimport_E2.bind('<KeyRelease>', lambda event: self._refresh_form_state(), add='+')

    def save_node(self,event):
        flag_error=0
        if self.nodeimport_E1.get()!=self.node_current_save_path:
            self.node_current_save_path=self.nodeimport_E1.get()
            try:
                with open(self.nodeimport_E1.get(), 'rb') as fr:
                    node_info = pickle.load(fr)
                self.node_data=node_info
                try:
                    self.node_name = node_info[0]['node_name']
                    self.node_type = node_info[0]['node_type']
                    self.use_node = node_info[0]['use_node']
                    self.node_time = node_info[0]['time']
                    # self.node_save_path = node_info[0]['node_save_path']
                    self.nodeimport_E2.delete(0, 'end')
                    self.nodeimport_E2.insert(INSERT, self.node_name)
                    self.label_str.set(self.node_type)
                except Exception as e:
                    flag_error = 1
                    show_error('模块文件解析失败，请确认文件格式正确', e)
            except Exception as e:
                flag_error = 1
                show_error('读取模块文件失败，请确认文件可用', e)
        if flag_error==0:
            if self.nodeimport_E2.get() in self.exist_data:
                show_error('该名称已经在项目中，请改名后再导入')
            elif self.node_current_save_path in self.exist_add:
                show_error('该地址已经在项目中，请勿重复导入')
            elif self.nodeimport_E2.get() != self.node_name:
                self.node_name= self.nodeimport_E2.get()
            else:
                self.node_setting={'node_type':self.node_type,'node_name':self.node_name,'use_node':self.use_node,'node_save_path':self.node_current_save_path,'time':self.node_time}
                self.save = 'Y'
                self.root2.destroy()
        self._refresh_form_state()
