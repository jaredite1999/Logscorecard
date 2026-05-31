"""
逻辑回归模型模块

提供评分卡建模功能，包括 WOE 逻辑回归、分组逻辑回归、
逐步回归等方法。
"""

import numpy as np
import pandas as pd
import math
import statsmodels.api as sm
import statsmodels.formula.api as smf
from joblib import Parallel, delayed

import joblib

from tkinter import *


class lrmodel():
    """
    逻辑回归模型类
    
    提供各种逻辑回归建模方法，用于构建评分卡模型。
    """
    def __init__(self,):


        pass

    def _build_design_matrix(self, df, variables, intercept):
        design_matrix = df[variables]
        if intercept:
            return sm.add_constant(design_matrix)
        return design_matrix

    def _build_logit_model(self, df, response, variables, intercept, weight_flag=False, weight_var=None):
        design_matrix = self._build_design_matrix(df, variables, intercept)
        if (weight_flag == True) and (weight_var != None):
            return sm.GLM(
                df[response],
                design_matrix,
                family=sm.families.Binomial(),
                freq_weights=np.asarray(df[weight_var]),
            )
        return sm.Logit(df[response], design_matrix)

    def _fit_logit_model(self, df, response, variables, intercept, weight_flag=False, weight_var=None):
        model = self._build_logit_model(
            df=df,
            response=response,
            variables=variables,
            intercept=intercept,
            weight_flag=weight_flag,
            weight_var=weight_var,
        )
        return model.fit(method='lbfgs', maxiter=100)

    def _criterion_score(self, result, criterion):
        score = getattr(result, criterion)
        if criterion == 'llr':
            return -score
        return score

    def _group_selected_variables(self, variable_df, selected):
        if selected != []:
            return variable_df[variable_df['variable'].isin(selected)]['list'].sum()
        return []

    def _group_remaining_variables(self, variables, remove_variables):
        return list(set(variables) - set(remove_variables))

    def _group_candidate_pvalue(self, result, candidate_variables):
        pvalue_df = pd.DataFrame(result.pvalues).reset_index()
        return pvalue_df[pvalue_df['index'].isin(candidate_variables)][0].min()

    def _fit_group_candidate(self, df, response, variable_df, selected, candidate, intercept, weight_flag=False, weight_var=None, remove_variables=None):
        group_variable_candidate = variable_df[variable_df['variable'].isin([candidate])]['list'].sum()
        group_variable_select = self._group_selected_variables(variable_df, selected)
        variables = group_variable_select + group_variable_candidate
        if remove_variables:
            variables = self._group_remaining_variables(variables, remove_variables)
        result = self._fit_logit_model(
            df=df,
            response=response,
            variables=variables,
            intercept=intercept,
            weight_flag=weight_flag,
            weight_var=weight_var,
        )
        return result, group_variable_candidate

    def _append_progress(self, mianframe, record_list, message):
        print(message)
        record_list.append(message)
        self.label_list = self.label_list + '\n' + message
        self.text.set(self.label_list)
        mianframe.update()

    def _format_criterion_message(self, action, variable_name, criterion, score):
        display_score = -score if criterion == 'llr' else score
        return '%s %s, %s = %.3f' % (action, variable_name, criterion, display_score)

    def _record_step_message(self, mianframe, record_list, action, variable_name, criterion, score):
        self._append_progress(
            mianframe,
            record_list,
            self._format_criterion_message(action, variable_name, criterion, score),
        )

    def _record_pvalue_message(self, mianframe, record_list, action, variable_name, pvalue):
        self._append_progress(
            mianframe,
            record_list,
            '%s %s, pvalue = %.5f' % (action, variable_name, pvalue),
        )

    def _record_model_summary(self, record_list, model):
        record_list.append(model.summary2())

    def _record_final_summary(self, record_list, selected_variables, stepwise_model):
        print('模型变量共', len(selected_variables), '个')
        record_list.append(['模型变量共', len(selected_variables), '个'])
        print('模型变量列表是：', selected_variables)
        record_list.append('模型变量列表是：')
        record_list.append(selected_variables)
        print('\n', stepwise_model.summary2())
        record_list.append(stepwise_model.summary2())

    def _build_group_variable_metadata(self, df, var):
        group_varlist = ['f_group_' + x for x in var]
        select_variable = []
        modelvar_match_df = pd.DataFrame()
        for varable in group_varlist:
            mm = len(df[varable].unique())
            grouplist = list(
                df[varable]
                .groupby(df[varable])
                .agg({'count'})
                .reset_index()
                .sort_values(by='count')[varable][0:mm - 1]
            )
            remind_group = list(
                df[varable]
                .groupby(df[varable])
                .agg({'count'})
                .reset_index()
                .sort_values(by='count')[varable][mm - 1:mm]
            )[0]
            variabellist = []
            for value in grouplist:
                model_var = '%s_%s' % (varable, int(value))
                df[model_var] = df[varable].apply(lambda x: 1 if x == value else 0)
                df[model_var] = df[model_var].astype('int8')
                variabellist.append(model_var)
                modelvar_match_df = pd.concat([
                    modelvar_match_df,
                    pd.DataFrame(
                        {
                            'ori_var': varable[8:],
                            'variable': varable,
                            'model_var': model_var,
                            'group': int(value),
                            'var_type': 'ori',
                        },
                        index=[1],
                    ),
                ])
            modelvar_match_df = pd.concat([
                modelvar_match_df,
                pd.DataFrame(
                    {
                        'ori_var': varable[8:],
                        'variable': varable,
                        'model_var': '%s_%s' % (varable, remind_group),
                        'group': remind_group,
                        'var_type': 'ori',
                    },
                    index=[1],
                ),
            ])
            select_variable.append({'variable': varable, 'list': variabellist, 'remind_group': remind_group})
        return group_varlist, pd.DataFrame(select_variable), modelvar_match_df

    def _restrict_candidate_variables(self, df, varlist, apply_restrict, record_list):
        if not apply_restrict:
            return varlist

        remove = []
        for p in range(len(varlist) - 1):
            if len(df[varlist[p]].unique()) < 2:
                remove = remove + [varlist[p]]
        var_clearn_t = list(set(varlist) - set(remove))
        corr_data = df[var_clearn_t].corr()
        for col in corr_data.columns:
            if len(corr_data[corr_data[col] > 0.99]) > 1:
                corr_data[corr_data.index == col] = 0
                remove = remove + [col]
        var_clearn = list(set(varlist) - set(remove))
        print('those varable will be not involve modeling because the high corr(>0.99) or zero performance', remove)
        record_list.append('those varable will be not involve modeling because the high corr(>0.99) or zero performance')
        record_list.append(remove)
        return var_clearn
    def woe_logistic_regression(self,mianframe, inditor_pct, inditor_sample, var, p_value_entry,p_value_stay, add_inditor,
                                intercept, criterion, df, response, direction, show_step, apply_restrict, n_job=None,
                                flag_IGN=True,weight_flag=False,weight_var=None):
        tip = Toplevel(mianframe)
        self.text = StringVar()
        self.label_list=''
        self.label_list=self.label_list+'start...'
        self.text.set(self.label_list)
        lb = Label(tip, textvariable=self.text)
        lb.pack()
        mianframe.update()
        record_list = []
        modelvar_match_df = pd.DataFrame()
        if n_job == None:
            n_job = joblib.cpu_count() - 1
        flag_next = True
        indicator_df = pd.DataFrame()
        if direction=='NO':
            add_inditor=False
        if flag_IGN == True:
            woe_varlist = ['woe_' + x for x in var]
            modelvar_match_df['ori_var'] = var
            modelvar_match_df['model_var'] = woe_varlist
            modelvar_match_df['var_type'] = 'ori'
        else:
            inditor_pct == False
            woe_varlist = var
        var_clearn = self._restrict_candidate_variables(df, woe_varlist, apply_restrict, record_list)
        # 检查可能添加的辅助变量
        if add_inditor == True:
            tlist = []
            for m in range(len(var_clearn)):
                for p in range(m + 1, len(var_clearn)):
                    vara = var[m]
                    varb = var[p]
                    listt = [vara, varb]
                    tlist.append(listt)
            lent = math.ceil(len(tlist) / n_job)

            def func(num):
                summary = pd.DataFrame()
                for l in range((num - 1) * lent, min(len(tlist), num * lent)):
                    pair = tlist[l]
                    vara = pair[0]
                    varb = pair[1]
                    target = response
                    var_a = df.groupby(['f_group_%s' % vara])[target].mean().reset_index().rename(
                        {target: 'badrate_vara'},
                        axis=1)
                    var_b = df.groupby(['f_group_%s' % varb])[target].mean().reset_index().rename(
                        {target: 'badrate_varb'},
                        axis=1)
                    tt = df.groupby(['f_group_%s' % vara, 'f_group_%s' % varb]).agg(
                        {target: ['mean', 'count']}).reset_index()
                    tt.columns = ['f_group_%s' % vara, 'f_group_%s' % varb, 'badrate', 'count']
                    tt = pd.merge(tt, var_a, how='left', on='f_group_%s' % vara)
                    tt = pd.merge(tt, var_b, how='left', on='f_group_%s' % varb)
                    tt['vara'] = vara
                    tt['varb'] = varb
                    tt = tt.rename({'f_group_%s' % vara: 'group_a', 'f_group_%s' % varb: 'group_b'}, axis=1)
                    summary = pd.concat([summary,tt])
                return summary
            scores_with_candidates = Parallel(n_jobs=n_job, max_nbytes=None, verbose=5)(
                delayed(func)(num) for num in range(1, 1 + n_job))
            score_df = pd.DataFrame()
            for tt in scores_with_candidates:
                sc = pd.DataFrame(tt)
                score_df = pd.concat([score_df,sc])
            score_df['model_var'] = score_df.apply(lambda x: 'ind_f_group_%s_%s_f_group_%s_%s'% (x['vara'], int(x['group_a']), x['varb'], int(x['group_b'])),axis=1)
            score_df['var_type'] = 'add'
            modelvar_match_df = pd.concat([modelvar_match_df,score_df])
            che = score_df[((score_df['badrate'] < score_df['badrate_vara']) & (score_df['badrate'] < score_df['badrate_varb'])) | ((score_df['badrate'] > score_df['badrate_vara']) & (score_df['badrate'] > score_df['badrate_varb']))]
            che['h'] = che.apply(lambda x: min(abs(x['badrate'] - max(x['badrate_vara'], x['badrate_varb'])),abs(x['badrate'] - min(x['badrate_vara'], x['badrate_varb']))), axis=1)
            che_fin = che[(che['h'] > inditor_pct) & (che['count'] > len(df) * inditor_sample)&(che['count'] > 800)]
            remaining_inditor = che_fin
            indicator_df = che_fin
        else:
            remaining_inditor=pd.DataFrame()
        # 向前回归
        if direction == 'forward':
            remaining_list = var_clearn
            selected = []
            best_score = np.inf
            if show_step:
                print('\nforward_stepwise starting:\n')
                record_list.append('\nforward_stepwise starting:\n')
                self.label_list = self.label_list + '\nforward_stepwise starting:\n'
                self.text.set(self.label_list)
                mianframe.update()
            # 当变量未剔除完，并且当前评分更新时进行循环
            while remaining_list != [] and flag_next == True:
                lent = math.ceil(len(remaining_list) / n_job)
                def func(num):
                    result_list = []
                    for i in range(num * lent, min((num + 1) * lent, len(remaining_list))):
                        candidate = remaining_list[i]
                        result = self._fit_logit_model(
                            df=df,
                            response=response,
                            variables=selected + [candidate],
                            intercept=intercept,
                            weight_flag=weight_flag,
                            weight_var=weight_var,
                        )
                        var = candidate
                        pvalue = result.pvalues[candidate]
                        score = self._criterion_score(result, criterion)
                        result_list.append({'var': var, 'pvalue': pvalue, 'score': score})
                    return result_list
                scores_with_candidates = Parallel(n_jobs=n_job, max_nbytes=None, verbose=5)(delayed(func)(num) for num
                                                                                            in range(n_job))

                score_df = pd.DataFrame()
                for tt in scores_with_candidates:
                    sc = pd.DataFrame(tt)
                    score_df = pd.concat([score_df,sc])
                # 这几个指标取最小值进行优化
                score_df = score_df[score_df['pvalue'] <= p_value_entry]
                score_df = score_df.sort_values(by='score', ascending=True)  # 对评分列表进行升序排序
                if len(score_df) > 0:
                    current_score = score_df.iloc[0]['score']
                    if current_score < best_score:
                        best_score = current_score
                        selected.append(score_df.iloc[0]['var'])
                        remaining_list.remove(score_df.iloc[0]['var'])
                        if (add_inditor == True) & (remaining_inditor.empty == False):
                            remaining_inditor['add'] = remaining_inditor.apply(
                                lambda x: 'Y' if ('woe_' + x['vara'] in selected) & (
                                        'woe_' + x['varb'] in selected) else 'N', axis=1)
                            add = remaining_inditor[remaining_inditor['add'] == 'Y']
                            remaining_inditor = remaining_inditor[remaining_inditor['add'] == 'N']

                            def add_indictor(vara, varb, groupa, groupb):
                                df['ind_f_group_%s_%s_f_group_%s_%s' % (vara, int(groupa), varb, int(groupb))] = df.apply(lambda x: 1 if (x['f_group_%s' % vara] == groupa) & (x['f_group_%s' % varb] == groupb) else 0, axis=1)
                                remaining_list.append('ind_f_group_%s_%s_f_group_%s_%s' % (vara, int(groupa), varb, int(groupb)))
                            if len(add) > 0:
                                add.apply(lambda x: add_indictor(vara=x['vara'], varb=x['varb'], groupa=x['group_a'],
                                                                 groupb=x['group_b']), axis=1)
                        flag_next = True
                        if show_step:  # 是否显示逐步回归过程
                            self._record_step_message(
                                mianframe,
                                record_list,
                                'Adding',
                                score_df.iloc[0]['var'],
                                criterion,
                                best_score,
                            )
                            model = self._fit_logit_model(
                                df=df,
                                response=response,
                                variables=selected,
                                intercept=intercept,
                                weight_flag=weight_flag,
                                weight_var=weight_var,
                            )
                            self._record_model_summary(record_list, model)
                    else:
                        flag_next = False
                else:
                    flag_next = False
            stepwise_model = self._fit_logit_model(
                df=df,
                response=response,
                variables=selected,
                intercept=intercept,
                weight_flag=weight_flag,
                weight_var=weight_var,
            )
            tip.destroy()
            if show_step:  # 是否显示逐步回归过程
                self._record_final_summary(record_list, selected, stepwise_model)
        # 逐步回归
        if direction == 'stepwise':
            remaining_list = var_clearn
            selected = []  # 初始化选入模型的变量列表
            # 初始化当前评分,最优新评分
            include_var = []
            flag_nonew = 0
            best_score = np.inf
            if show_step:
                print('\nstepwise starting:\n')
                record_list.append('\nstepwise starting:\n')
                self.label_list = self.label_list + '\nstepwise starting:\n'
                self.text.set(self.label_list)
                mianframe.update()
            # 当变量未剔除完，并且当前评分更新时进行循环
            while remaining_list != [] and flag_next == True:

                lent = math.ceil(len(remaining_list) / n_job)

                def func(num):
                    result_list = []
                    for i in range(num * lent, min((num + 1) * lent, len(remaining_list))):
                        candidate = remaining_list[i]
                        result = self._fit_logit_model(
                            df=df,
                            response=response,
                            variables=selected + [candidate],
                            intercept=intercept,
                            weight_flag=weight_flag,
                            weight_var=weight_var,
                        )
                        var = candidate
                        pvalue = result.pvalues[candidate]
                        score = self._criterion_score(result, criterion)
                        result_list.append({'var': var, 'pvalue': pvalue, 'score': score})
                    return result_list

                scores_with_candidates = Parallel(n_jobs=n_job, max_nbytes=None, verbose=5)(delayed(func)(num) for num
                                                                                            in range(n_job))
                score_df = pd.DataFrame()
                for tt in scores_with_candidates:
                    sc = pd.DataFrame(tt)
                    score_df = pd.concat([score_df,sc])
                # 这几个指标取最小值进行优化
                score_df = score_df[score_df['pvalue'] <= p_value_entry]
                score_df = score_df.sort_values(by='score', ascending=True)  # 对评分列表进行降序排序
                if len(score_df) > 0:
                    current_score = score_df.iloc[0]['score']
                    if current_score < best_score:
                        best_score = current_score
                        selected.append(score_df.iloc[0]['var'])
                        remaining_list.remove(score_df.iloc[0]['var'])
                        if score_df.iloc[0]['var'] in include_var:
                            flag_nonew = flag_nonew + 1
                            print('Limited steps')
                        else:
                            flag_nonew = 0
                            include_var.append(score_df.iloc[0]['var'])
                        if (add_inditor == True) & (remaining_inditor.empty == False):
                            remaining_inditor['add'] = remaining_inditor.apply(lambda x: 'Y' if (('woe_' + x['vara'] in selected) & ('woe_' + x['varb'] in selected)) else 'N', axis=1)
                            add = remaining_inditor[remaining_inditor['add'] == 'Y']
                            remaining_inditor = remaining_inditor[remaining_inditor['add'] == 'N']
                            def add_indictor(vara, varb, groupa, groupb):
                                df['ind_f_group_%s_%s_f_group_%s_%s' % (vara, int(groupa), varb, int(groupb))] = df.apply(lambda x: 1 if (x['f_group_%s' % vara] == groupa) & (x['f_group_%s' % varb] == groupb) else 0, axis=1)
                                remaining_list.append('ind_f_group_%s_%s_f_group_%s_%s' % (vara, int(groupa), varb, int(groupb)))
                            if len(add) > 0:
                                add.apply(lambda x: add_indictor(vara=x['vara'], varb=x['varb'], groupa=x['group_a'],groupb=x['group_b']), axis=1)
                        flag_next = True
                        if show_step:  # 是否显示逐步回归过程
                            self._record_step_message(
                                mianframe,
                                record_list,
                                'Adding',
                                score_df.iloc[0]['var'],
                                criterion,
                                best_score,
                            )
                            model = self._fit_logit_model(
                                df=df,
                                response=response,
                                variables=selected,
                                intercept=intercept,
                                weight_flag=weight_flag,
                                weight_var=weight_var,
                            )
                            self._record_model_summary(record_list, model)
                        flag_e = True
                        while (flag_e == True) and (len(selected)>1):
                            result_full = self._fit_logit_model(
                                df=df,
                                response=response,
                                variables=selected,
                                intercept=intercept,
                                weight_flag=weight_flag,
                                weight_var=weight_var,
                            )
                            #                 def func(num):
                            result_list = []
                            for i in range(0, len(selected)):
                                candidate = selected[i]
                                result = self._fit_logit_model(
                                    df=df,
                                    response=response,
                                    variables=list(set(selected) - set([candidate])),
                                    intercept=intercept,
                                    weight_flag=weight_flag,
                                    weight_var=weight_var,
                                )
                                var = candidate
                                pvalue = result_full.pvalues[candidate]
                                score = self._criterion_score(result, criterion)
                                result_list.append({'var': var, 'pvalue': pvalue, 'score': score})
                            score_df = pd.DataFrame(result_list)
                            # 这几个指标取最小值进行优化
                            score_df = score_df.sort_values(by='score', ascending=True)  # 对评分列表进行降序排序
                            if len(score_df) > 0:
                                current_score = score_df.iloc[0]['score']
                                if current_score < best_score:
                                    best_score = current_score
                                    selected.remove(score_df.iloc[0]['var'])
                                    remaining_list.append(score_df.iloc[0]['var'])
                                    flag_next = True
                                    if show_step:  # 是否显示逐步回归过程
                                        self._record_step_message(
                                            mianframe,
                                            record_list,
                                            'Delet',
                                            score_df.iloc[0]['var'],
                                            criterion,
                                            best_score,
                                        )
                                        model = self._fit_logit_model(
                                            df=df,
                                            response=response,
                                            variables=selected,
                                            intercept=intercept,
                                            weight_flag=weight_flag,
                                            weight_var=weight_var,
                                        )
                                        self._record_model_summary(record_list, model)

                                    flag_e = True
                                elif len(score_df[score_df['pvalue'] > p_value_stay]) > 0:
                                    score_df = score_df.sort_values(by='pvalue', ascending=False)
                                    best_score = score_df.iloc[0]['score']
                                    p_big = score_df.iloc[0]['pvalue']
                                    selected.remove(score_df.iloc[0]['var'])
                                    remaining_list.append(score_df.iloc[0]['var'])

                                    if show_step:  # 是否显示逐步回归过程
                                        self._record_pvalue_message(
                                            mianframe,
                                            record_list,
                                            'Delet',
                                            score_df.iloc[0]['var'],
                                            p_big,
                                        )
                                        model = self._fit_logit_model(
                                            df=df,
                                            response=response,
                                            variables=selected,
                                            intercept=intercept,
                                            weight_flag=weight_flag,
                                            weight_var=weight_var,
                                        )
                                        self._record_model_summary(record_list, model)
                                    flag_e = True
                                else:
                                    if flag_nonew >= 3:
                                        flag_next = False
                                    flag_e = False
                            else:
                                if flag_nonew >= 3:
                                    flag_next = False
                                flag_e = False
                        else:
                            pass
                    else:
                        flag_next = False
                else:
                    flag_next = False
            stepwise_model = self._fit_logit_model(
                df=df,
                response=response,
                variables=selected,
                intercept=intercept,
                weight_flag=weight_flag,
                weight_var=weight_var,
            )
            tip.destroy()
            if show_step:  # 是否显示逐步回归过程
                self._record_final_summary(record_list, selected, stepwise_model)
        if direction == 'NO':
            remaining_list = var_clearn
            selected = []
            if show_step:
                print('\nLR starting:\n')
                record_list.append('\nLR starting:\n')
                self.label_list = self.label_list + '\nLR starting:\n'
                self.text.set(self.label_list)
                mianframe.update()
            # 当变量未剔除完，并且当前评分更新时进行循环
            stepwise_model = self._fit_logit_model(
                df=df,
                response=response,
                variables=var_clearn,
                intercept=intercept,
                weight_flag=weight_flag,
                weight_var=weight_var,
            )
            tip.destroy()
            if show_step:  # 是否显示逐步回归过程
                self._record_final_summary(record_list, var_clearn, stepwise_model)
            tip.destroy()
        if direction == 'exist':
            remaining_list = var_clearn
            selected = []
            if show_step:
                print('\nLR starting:\n')
                record_list.append('\nLR starting:\n')
                self.label_list = self.label_list + '\nLR starting:\n'
                self.text.set(self.label_list)
                mianframe.update()
            # 当变量未剔除完，并且当前评分更新时进行循环
            stepwise_model = self._fit_logit_model(
                df=df,
                response=response,
                variables=var_clearn,
                intercept=intercept,
                weight_flag=weight_flag,
                weight_var=weight_var,
            )
            tip.destroy()
            if show_step:  # 是否显示逐步回归过程
                self._record_final_summary(record_list, var_clearn, stepwise_model)
            tip.destroy()

        return [record_list, stepwise_model, modelvar_match_df]

    def grp_logistic_regression(self, mianframe,var, p_value_entry,p_value_stay, intercept, criterion, df, response, direction, show_step,
                                apply_restrict, n_job=None,weight_flag = False,weight_var=None):
        tip = Toplevel(mianframe)
        self.text = StringVar()
        self.label_list=''
        self.label_list=self.label_list+'start...'
        self.text.set(self.label_list)
        lb = Label(tip, textvariable=self.text)
        lb.pack()
        mianframe.update()
        record_list = []
        modelvar_match_df = pd.DataFrame()
        if n_job == None:
            n_job = joblib.cpu_count() - 1
        flag_next = True
        group_varlist, variable_df, modelvar_match_df = self._build_group_variable_metadata(df, var)
        var_clearn = self._restrict_candidate_variables(df, group_varlist, apply_restrict, record_list)
        if direction == 'forward':
            print('\nforward_stepwise starting:\n')
            record_list.append('\nforward_stepwise starting:\n')
            self.label_list = self.label_list + '\nforward_stepwise starting:\n'
            self.text.set(self.label_list)
            mianframe.update()
            remaining_list = var_clearn
            selected = []  # 初始化选入模型的变量列表
            # 初始化当前评分,最优新评分
            best_score = np.inf
            if show_step:
                print('\nforward_stepwise starting:\n')
                record_list.append('\nforward_stepwise starting:\n')
            # 当变量未剔除完，并且当前评分更新时进行循环
            while remaining_list != [] and flag_next == True:
                lent = math.ceil(len(remaining_list) / n_job)

                def func(num):
                    result_list = []
                    for i in range(num * lent, min((num + 1) * lent, len(remaining_list))):
                        candidate = remaining_list[i]
                        result, group_variable_candidate = self._fit_group_candidate(
                            df=df,
                            response=response,
                            variable_df=variable_df,
                            selected=selected,
                            candidate=candidate,
                            intercept=intercept,
                            weight_flag=weight_flag,
                            weight_var=weight_var,
                        )
                        var = candidate
                        pvalue = self._group_candidate_pvalue(result, group_variable_candidate)
                        score = self._criterion_score(result, criterion)
                        result_list.append({'var': var, 'pvalue': pvalue, 'score': score})
                    return result_list

                scores_with_candidates = Parallel(n_jobs=n_job, max_nbytes=None, verbose=5)(delayed(func)(num) for num
                                                                                            in range(n_job))

                score_df = pd.DataFrame()
                for tt in scores_with_candidates:
                    sc = pd.DataFrame(tt)
                    score_df = pd.concat([score_df,sc])
                # 这几个指标取最小值进行优化
                score_df = score_df[score_df['pvalue'] <= p_value_entry]
                score_df = score_df.sort_values(by='score', ascending=True)  # 对评分列表进行升序排序
                if len(score_df) > 0:
                    current_score = score_df.iloc[0]['score']
                    if current_score < best_score:
                        best_score = current_score
                        selected.append(score_df.iloc[0]['var'])
                        remaining_list.remove(score_df.iloc[0]['var'])
                        flag_next = True
                        if show_step:  # 是否显示逐步回归过程
                            self._record_step_message(
                                mianframe,
                                record_list,
                                'Adding',
                                score_df.iloc[0]['var'],
                                criterion,
                                best_score,
                            )

                    else:
                        flag_next = False
                else:
                    flag_next = False
            group_variable_select = self._group_selected_variables(variable_df, selected)
            stepwise_model = self._fit_logit_model(
                df=df,
                response=response,
                variables=group_variable_select,
                intercept=intercept,
                weight_flag=weight_flag,
                weight_var=weight_var,
            )
            tip.destroy()
            if show_step:  # 是否显示逐步回归过程
                self._record_final_summary(record_list, group_variable_select, stepwise_model)
        if direction == 'stepwise':
            remaining_list = var_clearn
            selected = []  # 初始化选入模型的变量列表
            # 初始化当前评分,最优新评分
            include_var = []
            flag_nonew = 0
            best_score = np.inf
            if show_step:
                print('\nstepwise starting:\n')
                record_list.append('\nstepwise starting:\n')
            # 当变量未剔除完，并且当前评分更新时进行循环
            self.label_list = self.label_list +'\nstepwise starting:\n'
            self.text.set(self.label_list)
            mianframe.update()
            while remaining_list != [] and flag_next == True:
                lent = math.ceil(len(remaining_list) / n_job)
                def func(num):
                    result_list = []
                    for i in range(num * lent, min((num + 1) * lent, len(remaining_list))):
                        candidate = remaining_list[i]
                        result, group_variable_candidate = self._fit_group_candidate(
                            df=df,
                            response=response,
                            variable_df=variable_df,
                            selected=selected,
                            candidate=candidate,
                            intercept=intercept,
                            weight_flag=weight_flag,
                            weight_var=weight_var,
                        )
                        var = candidate
                        pvalue = self._group_candidate_pvalue(result, group_variable_candidate)
                        score = self._criterion_score(result, criterion)
                        result_list.append({'var': var, 'pvalue': pvalue, 'score': score})
                    return result_list
                scores_with_candidates = Parallel(n_jobs=n_job, max_nbytes=None, verbose=5)(delayed(func)(num) for num
                                                                                            in range(n_job))
                score_df = pd.DataFrame()
                for tt in scores_with_candidates:
                    sc = pd.DataFrame(tt)
                    score_df = pd.concat([score_df,sc])
                # 这几个指标取最小值进行优化
                score_df = score_df[score_df['pvalue'] <= p_value_entry]
                score_df = score_df.sort_values(by='score', ascending=True)  # 对评分列表进行降序排序
                if len(score_df) > 0:
                    current_score = score_df.iloc[0]['score']
                    if current_score < best_score:
                        best_score = current_score
                        selected.append(score_df.iloc[0]['var'])
                        remaining_list.remove(score_df.iloc[0]['var'])

                        if score_df.iloc[0]['var'] in include_var:
                            flag_nonew = flag_nonew + 1
                            print('Limited steps')
                        else:
                            flag_nonew = 0
                            include_var.append(score_df.iloc[0]['var'])

                        flag_next = True
                        if show_step:  # 是否显示逐步回归过程
                            self._record_step_message(
                                mianframe,
                                record_list,
                                'Adding',
                                score_df.iloc[0]['var'],
                                criterion,
                                best_score,
                            )
                        flag_e = True
                        while (flag_e == True) and (len(selected)>1):
                            group_variable_select = self._group_selected_variables(variable_df, selected)
                            result_full = self._fit_logit_model(
                                df=df,
                                response=response,
                                variables=group_variable_select,
                                intercept=intercept,
                                weight_flag=weight_flag,
                                weight_var=weight_var,
                            )
                            result_list = []
                            for i in range(0, len(selected)):
                                candidate = selected[i]
                                group_variable_candidate = variable_df[variable_df['variable'].isin([candidate])]['list'].sum()
                                result = self._fit_logit_model(
                                    df=df,
                                    response=response,
                                    variables=self._group_remaining_variables(group_variable_select, group_variable_candidate),
                                    intercept=intercept,
                                    weight_flag=weight_flag,
                                    weight_var=weight_var,
                                )
                                var = candidate
                                pvalue = self._group_candidate_pvalue(result_full, group_variable_candidate)
                                score = self._criterion_score(result, criterion)
                                result_list.append({'var': var, 'pvalue': pvalue, 'score': score})
                            score_df = pd.DataFrame(result_list)
                            score_df = score_df.sort_values(by='score', ascending=True)  # 对评分列表进行降序排序
                            if len(score_df) > 0:
                                current_score = score_df.iloc[0]['score']
                                if current_score < best_score:
                                    best_score = current_score
                                    selected.remove(score_df.iloc[0]['var'])
                                    remaining_list.append(score_df.iloc[0]['var'])
                                    flag_next = True
                                    flag_e = True
                                    if show_step:  # 是否显示逐步回归过程
                                        self._record_step_message(
                                            mianframe,
                                            record_list,
                                            'Delet',
                                            score_df.iloc[0]['var'],
                                            criterion,
                                            best_score,
                                        )
                                elif len(score_df[score_df['pvalue'] > p_value_stay]) > 0:
                                    score_df = score_df.sort_values(by='pvalue', ascending=False)
                                    best_score = score_df.iloc[0]['score']
                                    selected.remove(score_df.iloc[0]['var'])
                                    remaining_list.append(score_df.iloc[0]['var'])
                                    flag_e = True
                                    if show_step:  # 是否显示逐步回归过程
                                        self._record_step_message(
                                            mianframe,
                                            record_list,
                                            'Delet',
                                            score_df.iloc[0]['var'],
                                            criterion,
                                            best_score,
                                        )
                                else:
                                    if flag_nonew >= 3:
                                        flag_next = False
                                    flag_e = False
                            else:
                                if flag_nonew >= 3:
                                    flag_next = False
                                flag_e = False
                    else:
                        flag_next = False
                else:
                    flag_next = False
            group_variable_select = self._group_selected_variables(variable_df, selected)
            stepwise_model = self._fit_logit_model(
                df=df,
                response=response,
                variables=group_variable_select,
                intercept=intercept,
                weight_flag=weight_flag,
                weight_var=weight_var,
            )
            tip.destroy()
            if show_step:  # 是否显示逐步回归过程
                self._record_final_summary(record_list, group_variable_select, stepwise_model)
        if direction == 'NO':
            print('\nLR starting:\n')
            record_list.append('\nforward_stepwise starting:\n')
            self.label_list = self.label_list + '\nforward_stepwise starting:\n'
            self.text.set(self.label_list)
            mianframe.update()
            remaining_list = var_clearn
            selected = []  # 初始化选入模型的变量列表
            # 初始化当前评分,最优新评分
            if show_step:
                print('\nLR starting:\n')
                record_list.append('\nLR starting:\n')
            # 当变量未剔除完，并且当前评分更新时进行循环
            group_variable_select = self._group_selected_variables(variable_df, var_clearn)
            stepwise_model = self._fit_logit_model(
                df=df,
                response=response,
                variables=group_variable_select,
                intercept=intercept,
                weight_flag=weight_flag,
                weight_var=weight_var,
            )

            if show_step:  # 是否显示逐步回归过程
                self._record_final_summary(record_list, group_variable_select, stepwise_model)
            tip.destroy()
        return [record_list, stepwise_model, modelvar_match_df]
    def grp_ind_logistic_regression(self, mianframe,var, p_value_entry,p_value_stay, intercept, criterion, df, response, direction, show_step,
                                apply_restrict, n_job=None,weight_flag = False,weight_var=None):
        tip = Toplevel(mianframe)
        self.text = StringVar()
        self.label_list=''
        self.label_list=self.label_list+'start...'
        self.text.set(self.label_list)
        lb = Label(tip, textvariable=self.text)
        lb.pack()
        mianframe.update()
        record_list = []
        modelvar_match_df = pd.DataFrame()
        if n_job == None:
            n_job = joblib.cpu_count() - 1
        flag_next = True
        group_varlist, variable_df, modelvar_match_df = self._build_group_variable_metadata(df, var)
        var_clearn = self._restrict_candidate_variables(df, group_varlist, apply_restrict, record_list)
        if direction == 'forward':
            print('\nforward_stepwise starting:\n')
            record_list.append('\nforward_stepwise starting:\n')
            self.label_list = self.label_list + '\nforward_stepwise starting:\n'
            self.text.set(self.label_list)
            mianframe.update()
            remaining_list = var_clearn
            selected = []  # 初始化选入模型的变量列表
            # 初始化当前评分,最优新评分
            best_score = np.inf
            if show_step:
                print('\nforward_stepwise starting:\n')
                record_list.append('\nforward_stepwise starting:\n')
            # 当变量未剔除完，并且当前评分更新时进行循环
            while remaining_list != [] and flag_next == True:
                lent = math.ceil(len(remaining_list) / n_job)

                def func(num):
                    result_list = []
                    for i in range(num * lent, min((num + 1) * lent, len(remaining_list))):
                        candidate = remaining_list[i]
                        result, group_variable_candidate = self._fit_group_candidate(
                            df=df,
                            response=response,
                            variable_df=variable_df,
                            selected=selected,
                            candidate=candidate,
                            intercept=intercept,
                            weight_flag=weight_flag,
                            weight_var=weight_var,
                        )
                        var = candidate
                        pvalue = self._group_candidate_pvalue(result, group_variable_candidate)
                        score = self._criterion_score(result, criterion)
                        result_list.append({'var': var, 'pvalue': pvalue, 'score': score})
                    return result_list

                scores_with_candidates = Parallel(n_jobs=n_job, max_nbytes=None, verbose=5)(delayed(func)(num) for num
                                                                                            in range(n_job))

                score_df = pd.DataFrame()
                for tt in scores_with_candidates:
                    sc = pd.DataFrame(tt)
                    score_df = pd.concat([score_df , sc])
                # 这几个指标取最小值进行优化
                score_df = score_df[score_df['pvalue'] <= p_value_entry]
                score_df = score_df.sort_values(by='score', ascending=True)  # 对评分列表进行升序排序
                if len(score_df) > 0:
                    current_score = score_df.iloc[0]['score']
                    if current_score < best_score:
                        best_score = current_score
                        selected.append(score_df.iloc[0]['var'])
                        remaining_list.remove(score_df.iloc[0]['var'])
                        flag_next = True
                        if show_step:  # 是否显示逐步回归过程
                            self._record_step_message(
                                mianframe,
                                record_list,
                                'Adding',
                                score_df.iloc[0]['var'],
                                criterion,
                                best_score,
                            )
                    else:
                        flag_next = False
                else:
                    flag_next = False
            group_variable_select = self._group_selected_variables(variable_df, selected)
            stepwise_model = self._fit_logit_model(
                df=df,
                response=response,
                variables=group_variable_select,
                intercept=intercept,
                weight_flag=weight_flag,
                weight_var=weight_var,
            )
            tip.destroy()
            if show_step:  # 是否显示逐步回归过程
                self._record_final_summary(record_list, group_variable_select, stepwise_model)
        if direction == 'stepwise':
            remaining_list = var_clearn
            selected = []  # 初始化选入模型的变量列表
            # 初始化当前评分,最优新评分
            include_var = []
            remove_grp_variable=[]
            flag_nonew = 0
            best_score = np.inf
            if show_step:
                print('\nstepwise starting:\n')
                record_list.append('\nstepwise starting:\n')
            # 当变量未剔除完，并且当前评分更新时进行循环
            self.label_list = self.label_list +'\nstepwise starting:\n'
            self.text.set(self.label_list)
            mianframe.update()
            while remaining_list != [] and flag_next == True:
                lent = math.ceil(len(remaining_list) / n_job)
                def func(num):
                    result_list = []
                    for i in range(num * lent, min((num + 1) * lent, len(remaining_list))):
                        candidate = remaining_list[i]
                        result, group_variable_candidate = self._fit_group_candidate(
                            df=df,
                            response=response,
                            variable_df=variable_df,
                            selected=selected,
                            candidate=candidate,
                            intercept=intercept,
                            weight_flag=weight_flag,
                            weight_var=weight_var,
                            remove_variables=remove_grp_variable,
                        )
                        var = candidate
                        pvalue = self._group_candidate_pvalue(result, group_variable_candidate)
                        score = self._criterion_score(result, criterion)
                        result_list.append({'var': var, 'pvalue': pvalue, 'score': score})
                    return result_list
                scores_with_candidates = Parallel(n_jobs=n_job, max_nbytes=None, verbose=5)(delayed(func)(num) for num
                                                                                            in range(n_job))
                score_df = pd.DataFrame()
                for tt in scores_with_candidates:
                    sc = pd.DataFrame(tt)
                    score_df = pd.concat([score_df,sc])
                # 这几个指标取最小值进行优化
                score_df = score_df[score_df['pvalue'] <= p_value_entry]
                score_df = score_df.sort_values(by='score', ascending=True)  # 对评分列表进行降序排序
                if len(score_df) > 0:
                    current_score = score_df.iloc[0]['score']
                    if current_score < best_score:
                        best_score = current_score
                        selected.append(score_df.iloc[0]['var'])
                        remaining_list.remove(score_df.iloc[0]['var'])

                        if score_df.iloc[0]['var'] in include_var:
                            flag_nonew = flag_nonew + 1
                            print('Limited steps')
                        else:
                            flag_nonew = 0
                            include_var.append(score_df.iloc[0]['var'])

                        flag_next = True
                        if show_step:  # 是否显示逐步回归过程
                            self._record_step_message(
                                mianframe,
                                record_list,
                                'Adding',
                                score_df.iloc[0]['var'],
                                criterion,
                                best_score,
                            )
                        flag_e = True
                        while (flag_e == True) and (len(selected)>1):
                            group_variable_select = self._group_selected_variables(variable_df, selected)
                            active_variables = self._group_remaining_variables(group_variable_select, remove_grp_variable)
                            result_full = self._fit_logit_model(
                                df=df,
                                response=response,
                                variables=active_variables,
                                intercept=intercept,
                                weight_flag=weight_flag,
                                weight_var=weight_var,
                            )
                            result_list = []
                            for i in range(0, len(active_variables)):
                                candidate = active_variables[i]
                                result = self._fit_logit_model(
                                    df=df,
                                    response=response,
                                    variables=self._group_remaining_variables(active_variables, [candidate]),
                                    intercept=intercept,
                                    weight_flag=weight_flag,
                                    weight_var=weight_var,
                                )
                                var = candidate
                                pvalue =result_full.pvalues[candidate]
                                score = self._criterion_score(result, criterion)
                                result_list.append({'var': var, 'pvalue': pvalue, 'score': score})
                            score_df = pd.DataFrame(result_list)
                            score_df = score_df.sort_values(by='score', ascending=True)  # 对评分列表进行降序排序
                            if len(score_df) > 0:
                                current_score = score_df.iloc[0]['score']
                                if current_score < best_score:
                                    best_score = current_score
                                    remove_grp_variable.append(score_df.iloc[0]['var'])
                                    # selected.remove(score_df.iloc[0]['var'])
                                    # remaining_list.append(score_df.iloc[0]['var'])
                                    flag_next = True
                                    flag_e = True
                                    if show_step:  # 是否显示逐步回归过程
                                        self._record_step_message(
                                            mianframe,
                                            record_list,
                                            'Delet',
                                            score_df.iloc[0]['var'],
                                            criterion,
                                            best_score,
                                        )
                                elif len(score_df[score_df['pvalue'] > p_value_stay]) > 0:
                                    score_df = score_df.sort_values(by='pvalue', ascending=False)
                                    best_score = score_df.iloc[0]['score']
                                    remove_grp_variable.append(score_df.iloc[0]['var'])
                                    # selected.remove(score_df.iloc[0]['var'])
                                    # remaining_list.append(score_df.iloc[0]['var'])
                                    flag_e = True
                                    if show_step:  # 是否显示逐步回归过程
                                        self._record_step_message(
                                            mianframe,
                                            record_list,
                                            'Delet',
                                            score_df.iloc[0]['var'],
                                            criterion,
                                            best_score,
                                        )
                                else:
                                    if flag_nonew >= 3:
                                        flag_next = False
                                    flag_e = False
                            else:
                                if flag_nonew >= 3:
                                    flag_next = False
                                flag_e = False
                    else:
                        flag_next = False
                else:
                    flag_next = False
            group_variable_select = self._group_selected_variables(variable_df, selected)
            stepwise_model = self._fit_logit_model(
                df=df,
                response=response,
                variables=self._group_remaining_variables(group_variable_select, remove_grp_variable),
                intercept=intercept,
                weight_flag=weight_flag,
                weight_var=weight_var,
            )
            tip.destroy()
            if show_step:  # 是否显示逐步回归过程
                self._record_final_summary(record_list, group_variable_select, stepwise_model)
        if direction == 'NO':
            print('\nLR starting:\n')
            record_list.append('\nforward_stepwise starting:\n')
            self.label_list = self.label_list + '\nforward_stepwise starting:\n'
            self.text.set(self.label_list)
            mianframe.update()
            remaining_list = var_clearn
            selected = []  # 初始化选入模型的变量列表
            # 初始化当前评分,最优新评分
            if show_step:
                print('\nLR starting:\n')
                record_list.append('\nLR starting:\n')
            # 当变量未剔除完，并且当前评分更新时进行循环
            group_variable_select = self._group_selected_variables(variable_df, var_clearn)
            stepwise_model = self._fit_logit_model(
                df=df,
                response=response,
                variables=group_variable_select,
                intercept=intercept,
                weight_flag=weight_flag,
                weight_var=weight_var,
            )

            if show_step:  # 是否显示逐步回归过程
                self._record_final_summary(record_list, group_variable_select, stepwise_model)
            tip.destroy()
        return [record_list, stepwise_model, modelvar_match_df]
