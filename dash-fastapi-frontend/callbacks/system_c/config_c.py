import dash
import time
import uuid
from dash import dcc
from dash.dependencies import Input, Output, State, ALL
from dash.exceptions import PreventUpdate
import feffery_utils_components as fuc

from server import app
from api.config import get_config_list_api, get_config_detail_api, add_config_api, edit_config_api, delete_config_api, export_config_list_api, refresh_config_api


@app.callback(
    output=dict(
        config_table_data=Output('config-list-table', 'data', allow_duplicate=True),
        config_table_pagination=Output('config-list-table', 'pagination', allow_duplicate=True),
        config_table_key=Output('config-list-table', 'key'),
        config_table_selectedrowkeys=Output('config-list-table', 'selectedRowKeys'),
        api_check_token_trigger=Output('api-check-token', 'data', allow_duplicate=True)
    ),
    inputs=dict(
        search_click=Input('config-search', 'nClicks'),
        refresh_click=Input('config-refresh', 'nClicks'),
        pagination=Input('config-list-table', 'pagination'),
        operations=Input('config-operations-store', 'data')
    ),
    state=dict(
        config_name=State('config-config_name-input', 'value'),
        config_key=State('config-config_key-input', 'value'),
        config_type=State('config-config_type-select', 'value'),
        create_time_range=State('config-create_time-range', 'value'),
        button_perms=State('config-button-perms-container', 'data')
    ),
    prevent_initial_call=True
)
def get_config_table_data(search_click, refresh_click, pagination, operations, config_name, config_key, config_type, create_time_range, button_perms):
    """
    获取参数设置表格数据回调（进行表格相关增删查改操作后均会触发此回调）
    """
    create_time_start = None
    create_time_end = None
    if create_time_range:
        create_time_start = create_time_range[0]
        create_time_end = create_time_range[1]

    query_params = dict(
        config_name=config_name,
        config_key=config_key,
        config_type=config_type,
        create_time_start=create_time_start,
        create_time_end=create_time_end,
        page_num=1,
        page_size=10
    )
    triggered_id = dash.ctx.triggered_id
    if triggered_id == 'config-list-table':
        query_params = dict(
            config_name=config_name,
            config_key=config_key,
            config_type=config_type,
            create_time_start=create_time_start,
            create_time_end=create_time_end,
            page_num=pagination['current'],
            page_size=pagination['pageSize']
        )
    if search_click or refresh_click or pagination or operations:
        table_info = get_config_list_api(query_params)
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
                if item['config_type'] == 'Y':
                    item['config_type'] = dict(tag='是', color='blue')
                else:
                    item['config_type'] = dict(tag='否', color='volcano')
                item['key'] = str(item['config_id'])
                item['operation'] = [
                    {
                        'content': '修改',
                        'type': 'link',
                        'icon': 'antd-edit'
                    } if 'system:config:edit' in button_perms else {},
                    {
                        'content': '删除',
                        'type': 'link',
                        'icon': 'antd-delete'
                    } if 'system:config:remove' in button_perms else {},
                ]

            return dict(
                config_table_data=table_data,
                config_table_pagination=table_pagination,
                config_table_key=str(uuid.uuid4()),
                config_table_selectedrowkeys=None,
                api_check_token_trigger={'timestamp': time.time()}
            )

        return dict(
            config_table_data=dash.no_update,
            config_table_pagination=dash.no_update,
            config_table_key=dash.no_update,
            config_table_selectedrowkeys=dash.no_update,
            api_check_token_trigger={'timestamp': time.time()}
        )

    raise PreventUpdate


# 重置参数设置搜索表单数据回调
app.clientside_callback(
    '''
    (reset_click) => {
        if (reset_click) {
            return [null, null, null, null, {'type': 'reset'}]
        }
        return window.dash_clientside.no_update;
    }
    ''',
    [Output('config-config_name-input', 'value'),
     Output('config-config_key-input', 'value'),
     Output('config-config_type-select', 'value'),
     Output('config-create_time-range', 'value'),
     Output('config-operations-store', 'data')],
    Input('config-reset', 'nClicks'),
    prevent_initial_call=True
)


# 隐藏/显示参数设置搜索表单回调
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
    [Output('config-search-form-container', 'hidden'),
     Output('config-hidden-tooltip', 'title')],
    Input('config-hidden', 'nClicks'),
    State('config-search-form-container', 'hidden'),
    prevent_initial_call=True
)


@app.callback(
    Output({'type': 'config-operation-button', 'index': 'edit'}, 'disabled'),
    Input('config-list-table', 'selectedRowKeys'),
    prevent_initial_call=True
)
def change_config_edit_button_status(table_rows_selected):
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
    Output({'type': 'config-operation-button', 'index': 'delete'}, 'disabled'),
    Input('config-list-table', 'selectedRowKeys'),
    prevent_initial_call=True
)
def change_config_delete_button_status(table_rows_selected):
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
        modal_visible=Output('config-modal', 'visible', allow_duplicate=True),
        modal_title=Output('config-modal', 'title'),
        form_value=Output({'type': 'config-form-value', 'index': ALL}, 'value'),
        form_label_validate_status=Output({'type': 'config-form-label', 'index': ALL, 'required': True}, 'validateStatus', allow_duplicate=True),
        form_label_validate_info=Output({'type': 'config-form-label', 'index': ALL, 'required': True}, 'help', allow_duplicate=True),
        api_check_token_trigger=Output('api-check-token', 'data', allow_duplicate=True),
        edit_row_info=Output('config-edit-id-store', 'data'),
        modal_type=Output('config-operations-store-bk', 'data')
    ),
    inputs=dict(
        operation_click=Input({'type': 'config-operation-button', 'index': ALL}, 'nClicks'),
        button_click=Input('config-list-table', 'nClicksButton')
    ),
    state=dict(
        selected_row_keys=State('config-list-table', 'selectedRowKeys'),
        clicked_content=State('config-list-table', 'clickedContent'),
        recently_button_clicked_row=State('config-list-table', 'recentlyButtonClickedRow')
    ),
    prevent_initial_call=True
)
def add_edit_config_modal(operation_click, button_click, selected_row_keys, clicked_content, recently_button_clicked_row):
    """
    显示新增或编辑参数设置弹窗回调
    """
    trigger_id = dash.ctx.triggered_id
    if trigger_id == {'index': 'add', 'type': 'config-operation-button'} \
            or trigger_id == {'index': 'edit', 'type': 'config-operation-button'} \
            or (trigger_id == 'config-list-table' and clicked_content == '修改'):
        # 获取所有输出表单项对应value的index
        form_value_list = [x['id']['index'] for x in dash.ctx.outputs_list[2]]
        # 获取所有输出表单项对应label的index
        form_label_list = [x['id']['index'] for x in dash.ctx.outputs_list[3]]
        if trigger_id == {'index': 'add', 'type': 'config-operation-button'}:
            config_info = dict(config_name=None, config_key=None, config_value=None, config_type='Y', remark=None)
            return dict(
                modal_visible=True,
                modal_title='新增参数',
                form_value=[config_info.get(k) for k in form_value_list],
                form_label_validate_status=[None] * len(form_label_list),
                form_label_validate_info=[None] * len(form_label_list),
                api_check_token_trigger=dash.no_update,
                edit_row_info=None,
                modal_type={'type': 'add'}
            )
        elif trigger_id == {'index': 'edit', 'type': 'config-operation-button'} or (trigger_id == 'config-list-table' and clicked_content == '修改'):
            if trigger_id == {'index': 'edit', 'type': 'config-operation-button'}:
                config_id = int(','.join(selected_row_keys))
            else:
                config_id = int(recently_button_clicked_row['key'])
            config_info_res = get_config_detail_api(config_id=config_id)
            if config_info_res['code'] == 200:
                config_info = config_info_res['data']
                return dict(
                    modal_visible=True,
                    modal_title='编辑参数',
                    form_value=[config_info.get(k) for k in form_value_list],
                    form_label_validate_status=[None] * len(form_label_list),
                    form_label_validate_info=[None] * len(form_label_list),
                    api_check_token_trigger={'timestamp': time.time()},
                    edit_row_info=config_info if config_info else None,
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
        form_label_validate_status=Output({'type': 'config-form-label', 'index': ALL, 'required': True}, 'validateStatus',
                                          allow_duplicate=True),
        form_label_validate_info=Output({'type': 'config-form-label', 'index': ALL, 'required': True}, 'help',
                                        allow_duplicate=True),
        modal_visible=Output('config-modal', 'visible'),
        operations=Output('config-operations-store', 'data', allow_duplicate=True),
        api_check_token_trigger=Output('api-check-token', 'data', allow_duplicate=True),
        global_message_container=Output('global-message-container', 'children', allow_duplicate=True)
    ),
    inputs=dict(
        confirm_trigger=Input('config-modal', 'okCounts')
    ),
    state=dict(
        modal_type=State('config-operations-store-bk', 'data'),
        edit_row_info=State('config-edit-id-store', 'data'),
        form_value=State({'type': 'config-form-value', 'index': ALL}, 'value'),
        form_label=State({'type': 'config-form-label', 'index': ALL, 'required': True}, 'label')
    ),
    prevent_initial_call=True
)
def dict_type_confirm(confirm_trigger, modal_type, edit_row_info, form_value, form_label):
    """
    新增或编辑参数设置弹窗确认回调，实现新增或编辑操作
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
            params_edit['config_id'] = edit_row_info.get('config_id') if edit_row_info else None
            api_res = {}
            modal_type = modal_type.get('type')
            if modal_type == 'add':
                api_res = add_config_api(params_add)
            if modal_type == 'edit':
                api_res = edit_config_api(params_edit)
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
    [Output('config-delete-text', 'children'),
     Output('config-delete-confirm-modal', 'visible'),
     Output('config-delete-ids-store', 'data')],
    [Input({'type': 'config-operation-button', 'index': ALL}, 'nClicks'),
     Input('config-list-table', 'nClicksButton')],
    [State('config-list-table', 'selectedRowKeys'),
     State('config-list-table', 'clickedContent'),
     State('config-list-table', 'recentlyButtonClickedRow')],
    prevent_initial_call=True
)
def config_delete_modal(operation_click, button_click,
                      selected_row_keys, clicked_content, recently_button_clicked_row):
    """
    显示删除参数设置二次确认弹窗回调
    """
    trigger_id = dash.ctx.triggered_id
    if trigger_id == {'index': 'delete', 'type': 'config-operation-button'} or (
            trigger_id == 'config-list-table' and clicked_content == '删除'):

        if trigger_id == {'index': 'delete', 'type': 'config-operation-button'}:
            config_ids = ','.join(selected_row_keys)
        else:
            if clicked_content == '删除':
                config_ids = recently_button_clicked_row['key']
            else:
                return dash.no_update

        return [
            f'是否确认删除参数编号为{config_ids}的参数设置？',
            True,
            {'config_ids': config_ids}
        ]

    raise PreventUpdate


@app.callback(
    [Output('config-operations-store', 'data', allow_duplicate=True),
     Output('api-check-token', 'data', allow_duplicate=True),
     Output('global-message-container', 'children', allow_duplicate=True)],
    Input('config-delete-confirm-modal', 'okCounts'),
    State('config-delete-ids-store', 'data'),
    prevent_initial_call=True
)
def config_delete_confirm(delete_confirm, config_ids_data):
    """
    删除参数设置弹窗确认回调，实现删除操作
    """
    if delete_confirm:

        params = config_ids_data
        delete_button_info = delete_config_api(params)
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
    [Output('config-export-container', 'data', allow_duplicate=True),
     Output('config-export-complete-judge-container', 'data'),
     Output('api-check-token', 'data', allow_duplicate=True),
     Output('global-message-container', 'children', allow_duplicate=True)],
    Input('config-export', 'nClicks'),
    prevent_initial_call=True
)
def export_config_list(export_click):
    """
    导出参数设置信息回调
    """
    if export_click:
        export_config_res = export_config_list_api({})
        if export_config_res.status_code == 200:
            export_config = export_config_res.content

            return [
                dcc.send_bytes(export_config, f'参数配置信息_{time.strftime("%Y%m%d%H%M%S", time.localtime())}.xlsx'),
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
    Output('config-export-container', 'data', allow_duplicate=True),
    Input('config-export-complete-judge-container', 'data'),
    prevent_initial_call=True
)
def reset_config_export_status(data):
    """
    导出完成后重置下载组件数据回调，防止重复下载文件
    """
    time.sleep(0.5)
    if data:

        return None

    raise PreventUpdate


@app.callback(
    [Output('api-check-token', 'data', allow_duplicate=True),
     Output('global-message-container', 'children', allow_duplicate=True)],
    Input('config-refresh-cache', 'nClicks'),
    prevent_initial_call=True
)
def refresh_config_cache(refresh_click):
    """
    刷新缓存回调
    """
    if refresh_click:
        refresh_info_res = refresh_config_api({})
        if refresh_info_res.get('code') == 200:
            return [
                {'timestamp': time.time()},
                fuc.FefferyFancyMessage('刷新成功', type='success')
            ]

        return [
            {'timestamp': time.time()},
            fuc.FefferyFancyMessage('刷新失败', type='error')
        ]

    raise PreventUpdate
