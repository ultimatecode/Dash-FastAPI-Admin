import dash
import time
import uuid
from dash import dcc
from dash.dependencies import Input, Output, State, ALL
from dash.exceptions import PreventUpdate
import feffery_utils_components as fuc

from server import app
from api.dict import get_dict_data_list_api, get_dict_data_detail_api, add_dict_data_api, edit_dict_data_api, delete_dict_data_api, export_dict_data_list_api


@app.callback(
    output=dict(
        dict_data_table_data=Output('dict_data-list-table', 'data', allow_duplicate=True),
        dict_data_table_pagination=Output('dict_data-list-table', 'pagination', allow_duplicate=True),
        dict_data_table_key=Output('dict_data-list-table', 'key'),
        dict_data_table_selectedrowkeys=Output('dict_data-list-table', 'selectedRowKeys'),
        api_check_token_trigger=Output('api-check-token', 'data', allow_duplicate=True)
    ),
    inputs=dict(
        search_click=Input('dict_data-search', 'nClicks'),
        refresh_click=Input('dict_data-refresh', 'nClicks'),
        pagination=Input('dict_data-list-table', 'pagination'),
        operations=Input('dict_data-operations-store', 'data')
    ),
    state=dict(
        dict_type=State('dict_data-dict_type-select', 'value'),
        dict_label=State('dict_data-dict_label-input', 'value'),
        status_select=State('dict_data-status-select', 'value'),
        button_perms=State('dict_data-button-perms-container', 'data')
    ),
    prevent_initial_call=True
)
def get_dict_data_table_data(search_click, refresh_click, pagination, operations, dict_type, dict_label, status_select, button_perms):
    """
    获取字典数据表格数据回调（进行表格相关增删查改操作后均会触发此回调）
    """

    query_params = dict(
        dict_type=dict_type,
        dict_label=dict_label,
        status=status_select,
        page_num=1,
        page_size=10
    )
    triggered_id = dash.ctx.triggered_id
    if triggered_id == 'dict_data-list-table':
        query_params = dict(
            dict_type=dict_type,
            dict_label=dict_label,
            status=status_select,
            page_num=pagination['current'],
            page_size=pagination['pageSize']
        )
    if search_click or refresh_click or pagination or operations:
        table_info = get_dict_data_list_api(query_params)
        if table_info['code'] == 200:
            table_data = table_info['data']['rows']
            table_pagination = dict(
                pageSize=table_info['data']['page_size'],
                current=table_info['data']['page_num'],
                showSizeChanger=True,
                pageSizeOptions=[10, 30, 50, 100],
                showQuickJumper=True,
                total=table_info['data']['total']
            )
            for item in table_data:
                if item['status'] == '0':
                    item['status'] = dict(tag='正常', color='blue')
                else:
                    item['status'] = dict(tag='停用', color='volcano')
                item['key'] = str(item['dict_code'])
                item['operation'] = [
                    {
                        'content': '修改',
                        'type': 'link',
                        'icon': 'antd-edit'
                    } if 'system:dict:edit' in button_perms else {},
                    {
                        'content': '删除',
                        'type': 'link',
                        'icon': 'antd-delete'
                    } if 'system:dict:remove' in button_perms else {},
                ]

            return dict(
                dict_data_table_data=table_data,
                dict_data_table_pagination=table_pagination,
                dict_data_table_key=str(uuid.uuid4()),
                dict_data_table_selectedrowkeys=None,
                api_check_token_trigger={'timestamp': time.time()}
            )

        return dict(
            dict_data_table_data=dash.no_update,
            dict_data_table_pagination=dash.no_update,
            dict_data_table_key=dash.no_update,
            dict_data_table_selectedrowkeys=dash.no_update,
            api_check_token_trigger={'timestamp': time.time()}
        )

    raise PreventUpdate


# 重置字典数据搜索表单数据回调
app.clientside_callback(
    '''
    (reset_click) => {
        if (reset_click) {
            return [null, null, {'type': 'reset'}]
        }
        return window.dash_clientside.no_update;
    }
    ''',
    [Output('dict_data-dict_label-input', 'value'),
     Output('dict_data-status-select', 'value'),
     Output('dict_data-operations-store', 'data')],
    Input('dict_data-reset', 'nClicks'),
    prevent_initial_call=True
)


# 隐藏/显示字典数据搜索表单回调
app.clientside_callback(
    '''
    (hidden_click, hidden_status) => {
        if (hidden_click) {
            return [
                !hidden_status,
                hidden_status ? '隐藏搜索' : '显示搜索'
            ]
        }
        return window.dash_clientside.no_update;
    }
    ''',
    [Output('dict_data-search-form-container', 'hidden'),
     Output('dict_data-hidden-tooltip', 'title')],
    Input('dict_data-hidden', 'nClicks'),
    State('dict_data-search-form-container', 'hidden'),
    prevent_initial_call=True
)


@app.callback(
    Output({'type': 'dict_data-operation-button', 'index': 'edit'}, 'disabled'),
    Input('dict_data-list-table', 'selectedRowKeys'),
    prevent_initial_call=True
)
def change_dict_data_edit_button_status(table_rows_selected):
    """
    根据选择的表格数据行数控制编辑按钮状态回调
    """
    outputs_list = dash.ctx.outputs_list
    if outputs_list:
        if table_rows_selected:
            if len(table_rows_selected) > 1:
                return True

            return False

        return True

    raise PreventUpdate


@app.callback(
    Output({'type': 'dict_data-operation-button', 'index': 'delete'}, 'disabled'),
    Input('dict_data-list-table', 'selectedRowKeys'),
    prevent_initial_call=True
)
def change_dict_data_delete_button_status(table_rows_selected):
    """
    根据选择的表格数据行数控制删除按钮状态回调
    """
    outputs_list = dash.ctx.outputs_list
    if outputs_list:
        if table_rows_selected:

            return False

        return True

    raise PreventUpdate


@app.callback(
    output=dict(
        modal_visible=Output('dict_data-modal', 'visible', allow_duplicate=True),
        modal_title=Output('dict_data-modal', 'title'),
        form_value=Output({'type': 'dict_data-form-value', 'index': ALL}, 'value'),
        form_label_validate_status=Output({'type': 'dict_data-form-label', 'index': ALL, 'required': True}, 'validateStatus', allow_duplicate=True),
        form_label_validate_info=Output({'type': 'dict_data-form-label', 'index': ALL, 'required': True}, 'help', allow_duplicate=True),
        api_check_token_trigger=Output('api-check-token', 'data', allow_duplicate=True),
        edit_row_info=Output('dict_data-edit-id-store', 'data'),
        modal_type=Output('dict_data-operations-store-bk', 'data')
    ),
    inputs=dict(
        operation_click=Input({'type': 'dict_data-operation-button', 'index': ALL}, 'nClicks'),
        button_click=Input('dict_data-list-table', 'nClicksButton')
    ),
    state=dict(
        selected_row_keys=State('dict_data-list-table', 'selectedRowKeys'),
        clicked_content=State('dict_data-list-table', 'clickedContent'),
        recently_button_clicked_row=State('dict_data-list-table', 'recentlyButtonClickedRow'),
        dict_type_select=State('dict_data-dict_type-select', 'value')
    ),
    prevent_initial_call=True
)
def add_edit_dict_data_modal(operation_click, button_click, selected_row_keys, clicked_content,
                        recently_button_clicked_row, dict_type_select):
    """
    显示新增或编辑字典数据弹窗回调
    """
    trigger_id = dash.ctx.triggered_id
    if trigger_id == {'index': 'add', 'type': 'dict_data-operation-button'} \
            or trigger_id == {'index': 'edit', 'type': 'dict_data-operation-button'} \
            or (trigger_id == 'dict_data-list-table' and clicked_content == '修改'):
        # 获取所有输出表单项对应value的index
        form_value_list = [x['id']['index'] for x in dash.ctx.outputs_list[2]]
        # 获取所有输出表单项对应label的index
        form_label_list = [x['id']['index'] for x in dash.ctx.outputs_list[3]]
        if trigger_id == {'index': 'add', 'type': 'dict_data-operation-button'}:
            dict_data_info = dict(
                dict_type=dict_type_select,
                dict_label=None,
                dict_value=None,
                css_class=None,
                dict_sort=0,
                list_class='default',
                status='0',
                remark=None
            )
            return dict(
                modal_visible=True,
                modal_title='新增字典数据',
                form_value=[dict_data_info.get(k) for k in form_value_list],
                form_label_validate_status=[None] * len(form_label_list),
                form_label_validate_info=[None] * len(form_label_list),
                api_check_token_trigger=dash.no_update,
                edit_row_info=None,
                modal_type={'type': 'add'}
            )
        elif trigger_id == {'index': 'edit', 'type': 'dict_data-operation-button'} or (trigger_id == 'dict_data-list-table' and clicked_content == '修改'):
            if trigger_id == {'index': 'edit', 'type': 'dict_data-operation-button'}:
                dict_code = int(','.join(selected_row_keys))
            else:
                dict_code = int(recently_button_clicked_row['key'])
            dict_data_info_res = get_dict_data_detail_api(dict_code=dict_code)
            if dict_data_info_res['code'] == 200:
                dict_data_info = dict_data_info_res['data']
                return dict(
                    modal_visible=True,
                    modal_title='编辑字典数据',
                    form_value=[dict_data_info.get(k) for k in form_value_list],
                    form_label_validate_status=[None] * len(form_label_list),
                    form_label_validate_info=[None] * len(form_label_list),
                    api_check_token_trigger={'timestamp': time.time()},
                    edit_row_info=dict_data_info if dict_data_info else None,
                    modal_type={'type': 'edit'}
                )

        return dict(
            modal_visible=dash.no_update,
            modal_title=dash.no_update,
            form_value=[dash.no_update] * len(form_value_list),
            form_label_validate_status=[dash.no_update] * len(form_label_list),
            form_label_validate_info=[dash.no_update] * len(form_label_list),
            api_check_token_trigger={'timestamp': time.time()},
            edit_row_info=None,
            modal_type=None
        )

    raise PreventUpdate


@app.callback(
    output=dict(
        form_label_validate_status=Output({'type': 'dict_data-form-label', 'index': ALL, 'required': True}, 'validateStatus',
                                          allow_duplicate=True),
        form_label_validate_info=Output({'type': 'dict_data-form-label', 'index': ALL, 'required': True}, 'help',
                                        allow_duplicate=True),
        modal_visible=Output('dict_data-modal', 'visible'),
        operations=Output('dict_data-operations-store', 'data', allow_duplicate=True),
        api_check_token_trigger=Output('api-check-token', 'data', allow_duplicate=True),
        global_message_container=Output('global-message-container', 'children', allow_duplicate=True)
    ),
    inputs=dict(
        confirm_trigger=Input('dict_data-modal', 'okCounts')
    ),
    state=dict(
        modal_type=State('dict_data-operations-store-bk', 'data'),
        edit_row_info=State('dict_data-edit-id-store', 'data'),
        form_value=State({'type': 'dict_data-form-value', 'index': ALL}, 'value'),
        form_label=State({'type': 'dict_data-form-label', 'index': ALL, 'required': True}, 'label')
    ),
    prevent_initial_call=True
)
def dict_data_confirm(confirm_trigger, modal_type, edit_row_info, form_value, form_label):
    """
    新增或编字典数据弹窗确认回调，实现新增或编辑操作
    """
    if confirm_trigger:
        # 获取所有输出表单项对应label的index
        form_label_output_list = [x['id']['index'] for x in dash.ctx.outputs_list[0]]
        # 获取所有输入表单项对应的value及label
        form_value_state = {x['id']['index']: x.get('value') for x in dash.ctx.states_list[-2]}
        form_label_state = {x['id']['index']: x.get('value') for x in dash.ctx.states_list[-1]}
        if all([form_value_state.get(k) for k in form_label_output_list]):
            params_add = form_value_state
            params_edit = params_add.copy()
            params_edit['dict_code'] = edit_row_info.get('dict_code') if edit_row_info else None
            api_res = {}
            modal_type = modal_type.get('type')
            if modal_type == 'add':
                api_res = add_dict_data_api(params_add)
            if modal_type == 'edit':
                api_res = edit_dict_data_api(params_edit)
            if api_res.get('code') == 200:
                if modal_type == 'add':
                    return dict(
                        form_label_validate_status=[None] * len(form_label_output_list),
                        form_label_validate_info=[None] * len(form_label_output_list),
                        modal_visible=False,
                        operations={'type': 'add'},
                        api_check_token_trigger={'timestamp': time.time()},
                        global_message_container=fuc.FefferyFancyMessage('新增成功', type='success')
                    )
                if modal_type == 'edit':
                    return dict(
                        form_label_validate_status=[None] * len(form_label_output_list),
                        form_label_validate_info=[None] * len(form_label_output_list),
                        modal_visible=False,
                        operations={'type': 'edit'},
                        api_check_token_trigger={'timestamp': time.time()},
                        global_message_container=fuc.FefferyFancyMessage('编辑成功', type='success')
                    )

            return dict(
                form_label_validate_status=[None] * len(form_label_output_list),
                form_label_validate_info=[None] * len(form_label_output_list),
                modal_visible=dash.no_update,
                operations=dash.no_update,
                api_check_token_trigger={'timestamp': time.time()},
                global_message_container=fuc.FefferyFancyMessage('处理失败', type='error')
            )

        return dict(
            form_label_validate_status=[None if form_value_state.get(k) else 'error' for k in form_label_output_list],
            form_label_validate_info=[None if form_value_state.get(k) else f'{form_label_state.get(k)}不能为空!' for k in form_label_output_list],
            modal_visible=dash.no_update,
            operations=dash.no_update,
            api_check_token_trigger={'timestamp': time.time()},
            global_message_container=fuc.FefferyFancyMessage('处理失败', type='error')
        )

    raise PreventUpdate


@app.callback(
    [Output('dict_data-delete-text', 'children'),
     Output('dict_data-delete-confirm-modal', 'visible'),
     Output('dict_data-delete-ids-store', 'data')],
    [Input({'type': 'dict_data-operation-button', 'index': ALL}, 'nClicks'),
     Input('dict_data-list-table', 'nClicksButton')],
    [State('dict_data-list-table', 'selectedRowKeys'),
     State('dict_data-list-table', 'clickedContent'),
     State('dict_data-list-table', 'recentlyButtonClickedRow')],
    prevent_initial_call=True
)
def dict_data_delete_modal(operation_click, button_click,
                      selected_row_keys, clicked_content, recently_button_clicked_row):
    """
    显示删除字典数据二次确认弹窗回调
    """
    trigger_id = dash.ctx.triggered_id
    if trigger_id == {'index': 'delete', 'type': 'dict_data-operation-button'} or (
            trigger_id == 'dict_data-list-table' and clicked_content == '删除'):

        if trigger_id == {'index': 'delete', 'type': 'dict_data-operation-button'}:
            dict_codes = ','.join(selected_row_keys)
        else:
            if clicked_content == '删除':
                dict_codes = recently_button_clicked_row['key']
            else:
                return dash.no_update

        return [
            f'是否确认删除字典编码为{dict_codes}的数据？',
            True,
            {'dict_codes': dict_codes}
        ]

    raise PreventUpdate


@app.callback(
    [Output('dict_data-operations-store', 'data', allow_duplicate=True),
     Output('api-check-token', 'data', allow_duplicate=True),
     Output('global-message-container', 'children', allow_duplicate=True)],
    Input('dict_data-delete-confirm-modal', 'okCounts'),
    State('dict_data-delete-ids-store', 'data'),
    prevent_initial_call=True
)
def dict_data_delete_confirm(delete_confirm, dict_codes_data):
    """
    删除字典数据弹窗确认回调，实现删除操作
    """
    if delete_confirm:

        params = dict_codes_data
        delete_button_info = delete_dict_data_api(params)
        if delete_button_info['code'] == 200:
            return [
                {'type': 'delete'},
                {'timestamp': time.time()},
                fuc.FefferyFancyMessage('删除成功', type='success')
            ]

        return [
            dash.no_update,
            {'timestamp': time.time()},
            fuc.FefferyFancyMessage('删除失败', type='error')
        ]

    raise PreventUpdate


@app.callback(
    [Output('dict_data-export-container', 'data', allow_duplicate=True),
     Output('dict_data-export-complete-judge-container', 'data'),
     Output('api-check-token', 'data', allow_duplicate=True),
     Output('global-message-container', 'children', allow_duplicate=True)],
    Input('dict_data-export', 'nClicks'),
    State('dict_data-dict_type-select', 'value'),
    prevent_initial_call=True
)
def export_dict_data_list(export_click, dict_type):
    """
    导出字典数据信息回调
    """
    if export_click:
        export_dict_data_res = export_dict_data_list_api(dict(dict_type=dict_type))
        if export_dict_data_res.status_code == 200:
            export_dict_data = export_dict_data_res.content

            return [
                dcc.send_bytes(export_dict_data, f'字典数据信息_{time.strftime("%Y%m%d%H%M%S", time.localtime())}.xlsx'),
                {'timestamp': time.time()},
                {'timestamp': time.time()},
                fuc.FefferyFancyMessage('导出成功', type='success')
            ]

        return [
            dash.no_update,
            dash.no_update,
            {'timestamp': time.time()},
            fuc.FefferyFancyMessage('导出失败', type='error')
        ]

    raise PreventUpdate


@app.callback(
    Output('dict_data-export-container', 'data', allow_duplicate=True),
    Input('dict_data-export-complete-judge-container', 'data'),
    prevent_initial_call=True
)
def reset_dict_data_export_status(data):
    """
    导出完成后重置下载组件数据回调，防止重复下载文件
    """
    time.sleep(0.5)
    if data:

        return None

    raise PreventUpdate
