from module_admin.entity.vo.menu_vo import *
from module_admin.dao.menu_dao import *
from module_admin.entity.vo.user_vo import CurrentUserInfoServiceResponse


class MenuService:
    """
    菜单管理模块服务层
    """

    @classmethod
    def get_menu_tree_services(cls, result_db: Session, page_object: MenuTreeModel, current_user: Optional[CurrentUserInfoServiceResponse] = None):
        """
        获取菜单树信息service
        :param result_db: orm对象
        :param page_object: 查询参数对象
        :param current_user: 当前用户对象
        :return: 菜单树信息对象
        """
        menu_tree_option = []
        menu_list_result = get_menu_list_for_tree(result_db, MenuModel(**page_object.dict()), current_user.user.user_id, current_user.role)
        menu_tree_result = cls.get_menu_tree(0, MenuTree(menu_tree=menu_list_result))
        if page_object.type != 'role':
            menu_tree_option.append(dict(title='主类目', value='0', key='0', children=menu_tree_result))
        else:
            menu_tree_option = [menu_tree_result, menu_list_result]

        return menu_tree_option

    @classmethod
    def get_menu_tree_for_edit_option_services(cls, result_db: Session, page_object: MenuModel, current_user: Optional[CurrentUserInfoServiceResponse] = None):
        """
        获取菜单编辑菜单树信息service
        :param result_db: orm对象
        :param page_object: 查询参数对象
        :param current_user: 当前用户
        :return: 菜单树信息对象
        """
        menu_tree_option = []
        menu_list_result = get_menu_info_for_edit_option(result_db, page_object, current_user.user.user_id, current_user.role)
        menu_tree_result = cls.get_menu_tree(0, MenuTree(menu_tree=menu_list_result))
        menu_tree_option.append(dict(title='主类目', value='0', key='0', children=menu_tree_result))

        return menu_tree_option

    @classmethod
    def get_menu_list_services(cls, result_db: Session, page_object: MenuModel, current_user: Optional[CurrentUserInfoServiceResponse] = None):
        """
        获取菜单列表信息service
        :param result_db: orm对象
        :param page_object: 分页查询参数对象
        :param current_user: 当前用户对象
        :return: 菜单列表信息对象
        """
        menu_list_result = get_menu_list(result_db, page_object, current_user.user.user_id, current_user.role)

        return menu_list_result

    @classmethod
    def add_menu_services(cls, result_db: Session, page_object: MenuModel):
        """
        新增菜单信息service
        :param result_db: orm对象
        :param page_object: 新增菜单对象
        :return: 新增菜单校验结果
        """
        add_menu_result = add_menu_dao(result_db, page_object)

        return add_menu_result

    @classmethod
    def edit_menu_services(cls, result_db: Session, page_object: MenuModel):
        """
        编辑菜单信息service
        :param result_db: orm对象
        :param page_object: 编辑部门对象
        :return: 编辑菜单校验结果
        """
        edit_menu = page_object.dict(exclude_unset=True)
        edit_menu_result = edit_menu_dao(result_db, edit_menu)

        return edit_menu_result

    @classmethod
    def delete_menu_services(cls, result_db: Session, page_object: DeleteMenuModel):
        """
        删除菜单信息service
        :param result_db: orm对象
        :param page_object: 删除菜单对象
        :return: 删除菜单校验结果
        """
        if page_object.menu_ids.split(','):
            menu_id_list = page_object.menu_ids.split(',')
            for menu_id in menu_id_list:
                menu_id_dict = dict(menu_id=menu_id)
                delete_menu_dao(result_db, MenuModel(**menu_id_dict))
            result = dict(is_success=True, message='删除成功')
        else:
            result = dict(is_success=False, message='传入菜单id为空')
        return CrudMenuResponse(**result)

    @classmethod
    def detail_menu_services(cls, result_db: Session, menu_id: int):
        """
        获取菜单详细信息service
        :param result_db: orm对象
        :param menu_id: 菜单id
        :return: 菜单id对应的信息
        """
        menu = get_menu_detail_by_id(result_db, menu_id=menu_id)

        return menu

    @classmethod
    def get_menu_tree(cls, pid: int, permission_list: MenuTree):
        """
        工具方法：根据菜单信息生成树形嵌套数据
        :param pid: 菜单id
        :param permission_list: 菜单列表信息
        :return: 菜单树形嵌套数据
        """
        menu_list = []
        for permission in permission_list.menu_tree:
            if permission.parent_id == pid:
                children = cls.get_menu_tree(permission.menu_id, permission_list)
                menu_list_data = {}
                if children:
                    menu_list_data['title'] = permission.menu_name
                    menu_list_data['key'] = str(permission.menu_id)
                    menu_list_data['value'] = str(permission.menu_id)
                    menu_list_data['children'] = children
                else:
                    menu_list_data['title'] = permission.menu_name
                    menu_list_data['key'] = str(permission.menu_id)
                    menu_list_data['value'] = str(permission.menu_id)
                menu_list.append(menu_list_data)

        return menu_list
