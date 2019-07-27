# -*- coding: utf-8 -*-
import base64
import logging

import requests

from odoo import api, fields, models, tools
from odoo.addons.ali_dindin.dingtalk.main import client, stamp_to_time
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class DingDingSynchronous(models.TransientModel):
    _name = 'dingding.bash.data.synchronous'
    _description = "基础数据同步"
    _rec_name = 'employee'

    department = fields.Boolean(string='同步钉钉部门', default=True)
    employee = fields.Boolean(string='同步钉钉员工', default=True)
    employee_avatar = fields.Boolean(string='是否替换为钉钉员工头像', default=False)
    partner = fields.Boolean(string='同步钉钉联系人', default=True)

    
    def start_synchronous_data(self):
        """
        基础数据同步
        :return:
        """
        for res in self:
            if res.department:
                self.synchronous_dingding_department()
                self.synchronous_dingding_department()
            if res.employee:
                self.synchronous_dingding_employee(
                    s_avatar=res.employee_avatar)
            if res.partner:
                self.synchronous_dingding_category()
                self.synchronous_dingding_partner()

    @api.model
    def synchronous_dingding_department(self):
        """
        同步钉钉部门
        :return:
        """
        
        try:
            result = client.department.list(fetch_child=True)
            for res in result:
                data = {
                    'name': res.get('name'),
                    'din_id': res.get('id'),
                }
                if res.get('parentid') != 1:
                    partner_department = self.env['hr.department'].search(
                        [('din_id', '=', res.get('parentid'))])
                    if partner_department:
                        data.update({'parent_id': partner_department[0].id})
                h_department = self.env['hr.department'].search(
                    ['|', ('din_id', '=', res.get('id')), ('name', '=', res.get('name'))])
                if h_department:
                    h_department.sudo().write(data)
                else:
                    dep = client.department.get(res.get('id'))
                    not_get_hiding_dep = self.env['ir.config_parameter'].sudo(
                    ).get_param('ali_dindin.din_not_get_hidden_department')
                    is_hiding_dep = dep.get('deptHiding')
                    if not_get_hiding_dep and is_hiding_dep:
                        pass  # 不创建钉钉通讯录中隐藏的部门
                    else:
                        self.env['hr.department'].create(data)
            return True
        except Exception as e:
            raise UserError(e)

    @api.model
    def synchronous_dingding_employee(self, s_avatar=None):
        """
        同步钉钉部门员工列表
        :return:
        """
        departments = self.env['hr.department'].sudo().search(
            [('din_id', '!=', '')])
        for department in departments:
            emp_offset = 0
            emp_size = 100
            while True:
                logging.info(">>>开始获取%s部门的员工", department.name)
                offset = emp_offset
                size = emp_size
                result_state = self.get_dingding_employees(
                    department, offset, size, s_avatar=s_avatar)
                if result_state:
                    emp_offset = emp_offset + 1
                else:
                    break
        return True

    @api.model
    def get_dingding_employees(self, department, offset=0, size=100, s_avatar=None):
        """
        获取部门成员（详情）

        :param department: 获取的部门id
        :param offset: 偏移量
        :param size: 表分页大小，最大100
        :param order: 排序规则
                      entry_asc     代表按照进入部门的时间升序
                      entry_desc    代表按照进入部门的时间降序
                      modify_asc    代表按照部门信息修改时间升序
                      modify_desc   代表按照部门信息修改时间降序
                      custom        代表用户定义排序
        :param lang: 通讯录语言(默认zh_CN另外支持en_US)
        :param s_avatar: 是否获取钉钉头像
        :return:
        """
        
        try:
            result = client.user.list(
                department[0].din_id, offset, size, order='custom')
            for user in result.get('userlist'):
                data = {
                    'name': user.get('name'),  # 员工名称
                    'din_id': user.get('userid'),  # 钉钉用户Id
                    'din_unionid': user.get('unionid'),  # 钉钉唯一标识
                    'mobile_phone': user.get('mobile'),  # 手机号
                    'work_phone': user.get('tel'),  # 分机号
                    'work_location': user.get('workPlace'),  # 办公地址
                    'notes': user.get('remark'),  # 备注
                    'job_title': user.get('position'),  # 职位
                    'work_email': user.get('email'),  # email
                    'din_jobnumber': user.get('jobnumber'),  # 工号
                    'department_id': department[0].id,  # 部门
                    # 钉钉头像url
                    'din_avatar': user.get('avatar') if user.get('avatar') else '',
                    'din_isSenior': user.get('isSenior'),  # 高管模式
                    'din_isAdmin': user.get('isAdmin'),  # 是管理员
                    'din_isBoss': user.get('isBoss'),  # 是老板
                    'din_isLeader': user.get('isLeader'),  # 是部门主管
                    'din_isHide': user.get('isHide'),  # 隐藏手机号
                    'din_active': user.get('active'),  # 是否激活
                    # 是否为部门主管
                    'din_isLeaderInDepts': user.get('isLeaderInDepts'),
                    'din_orderInDepts': user.get('orderInDepts'),  # 所在部门序位
                }
                # 支持显示国际手机号
                if user.get('stateCode') != '86':
                    data.update({
                        'mobile_phone': '+{}-{}'.format(user.get('stateCode'), user.get('mobile')),
                    })
                if user.get('hiredDate'):
                    time_stamp = stamp_to_time(user.get('hiredDate'))
                    data.update({
                        'din_hiredDate': time_stamp,
                    })
                if s_avatar and user.get('avatar'):
                    try:
                        binary_data = tools.image_resize_image_big(
                            base64.b64encode(requests.get(user.get('avatar')).content))
                        data.update({'image': binary_data})
                    except Exception as e:
                        logging.info(">>>--------------------------------")
                        logging.info(">>>SSL异常:%s", e)
                        logging.info(">>>--------------------------------")
                if user.get('department'):
                    dep_din_ids = user.get('department')
                    dep_list = self.env['hr.department'].sudo().search(
                        [('din_id', 'in', dep_din_ids)])
                    data.update({'department_ids': [(6, 0, dep_list.ids)]})
                employee = self.env['hr.employee'].search(['|', ('din_id', '=', user.get(
                    'userid')), ('mobile_phone', '=', user.get('mobile'))])
                if employee:
                    employee.sudo().write(data)
                else:
                    self.env['hr.employee'].sudo().create(data)
            return result.get('hasMore')
        except Exception as e:
            raise UserError(e)

    @api.model
    def synchronous_dingding_category(self):
        """
        同步钉钉联系人标签
        :return:
        """
        
        logging.info(">>>同步钉钉联系人标签")
        try:
            result = client.ext.listlabelgroups(offset=0, size=100)
            logging.info(result)
            category_list = list()
            for res in result:
                for labels in res.get('labels'):
                    category_list.append({
                        'name': labels.get('name'),
                        'din_id': labels.get('id'),
                        'din_color': res.get('color'),
                        'din_category_type': res.get('name'),
                    })
            for category in category_list:
                res_category = self.env['res.partner.category'].sudo().search(
                    [('din_id', '=', category.get('din_id'))])
                if res_category:
                    res_category.sudo().write(category)
                else:
                    self.env['res.partner.category'].sudo().create(category)
            return True
        except Exception as e:
            raise UserError(e)

    @api.model
    def synchronous_dingding_partner(self):
        """
        同步钉钉联系人列表
        :return:
        """
        
        logging.info(">>>同步钉钉联系人列表start")
        try:
            result = client.ext.list(offset=0, size=100)
            logging.info(result)
            for res in result:
                # 获取标签
                label_list = list()
                for label in res.get('labelIds'):
                    category = self.env['res.partner.category'].sudo().search(
                        [('din_id', '=', label)])
                    if category:
                        label_list.append(category[0].id)
                data = {
                    'name': res.get('name'),
                    'function': res.get('title'),
                    'category_id': [(6, 0, label_list)],  # 标签
                    'din_userid': res.get('userId'),  # 钉钉用户id
                    'comment': res.get('remark'),  # 备注
                    'street': res.get('address'),  # 地址
                    'mobile': res.get('mobile'),  # 手机
                    'phone': res.get('mobile'),  # 电话
                    'din_company_name': res.get('companyName'),  # 钉钉公司名称
                }
                # 获取负责人
                if res.get('followerUserId'):
                    follower_user = self.env['hr.employee'].sudo().search(
                        [('din_id', '=', res.get('followerUserId'))])
                    data.update(
                        {'din_employee_id': follower_user[0].id if follower_user else ''})
                # 获取共享范围
                if res.get('shareDeptIds'):
                    dep_din_ids = res.get('shareDeptIds')
                    dep_list = self.env['hr.department'].sudo().search(
                        [('din_id', 'in', dep_din_ids)])
                    data.update({'din_share_department_ids': [
                                (6, 0, dep_list.ids)]if dep_list else ''})
                # 获取共享员工
                if res.get('shareUserIds'):
                    emp_din_ids = res.get('shareUserIds')
                    emp_list = self.env['hr.employee'].sudo().search(
                        [('din_id', 'in', emp_din_ids)])
                    data.update({'din_share_employee_ids': [
                                (6, 0, emp_list.ids)] if emp_list else ''})
                # 根据userid查询联系人是否存在
                partner = self.env['res.partner'].sudo().search(
                    ['|', ('din_userid', '=', res.get('userId')), ('name', '=', res.get('name'))])
                if partner:
                    partner.sudo().write(data)
                else:
                    self.env['res.partner'].sudo().create(data)
            return True
        except Exception as e:
            raise UserError(e)
