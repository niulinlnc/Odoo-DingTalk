# -*- coding: utf-8 -*-
import logging

from odoo import api, fields, models, _
from odoo.addons.ali_dindin.dingtalk.main import get_client
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


# 继承联系人标签模型，增加钉钉返回的id、颜色字段
class ResPartnerCategory(models.Model):
    _inherit = 'res.partner.category'

    din_id = fields.Char(string='钉钉标签ID')
    din_color = fields.Char(string='钉钉标签颜色')
    din_category_type = fields.Char(string='标签分类名')


# 继承联系人模型，增加钉钉返回的userid等字段
class ResPartner(models.Model):
    _inherit = 'res.partner'

    din_userid = fields.Char(string='钉钉联系人ID', help="用于存储在钉钉系统中返回的联系人id")
    din_company_name = fields.Char(
        string='钉钉联系人公司', help="用于存储在钉钉系统中返回的联系人所在公司")
    din_sy_state = fields.Boolean(
        string='钉钉同步标识', default=False, help="避免使用同步时,会执行创建、修改上传钉钉方法")
    din_employee_id = fields.Many2one(
        comodel_name='hr.employee', string='负责人', ondelete='cascade')
    din_share_department_ids = fields.Many2many(
        'hr.department', 'partner_department_rel', 'partner_id', 'department_id', string='共享范围')
    din_share_employee_ids = fields.Many2many(
        'hr.employee', 'partner_shar_employee_rel', 'partner_id', 'emp_id', string='共享给员工')

    @api.multi
    def create_ding_partner(self):
        """
        添加外部联系人

        :param name: 名称
        :param follower_user_id: 负责人userId
        :param state_code: 手机号国家码
        :param mobile: 手机号
        :param label_ids: 标签列表
        :param title: 职位
        :param share_dept_ids: 共享给的部门ID
        :param remark: 备注
        :param address: 地址
        :param company_name: 企业名
        :param share_user_ids: 共享给的员工userId列表
        :return:
        """
        client = get_client(self)
        for res in self:
            if res.din_userid:
                raise UserError(_('钉钉中已存在该联系人,请不要重复上传或使用更新联系人功能！'))
            # 获取标签
            label_ids = list()
            if res.category_id:
                for category in res.category_id:
                    label_ids.append(category.din_id)
                label_ids = list(map(int, label_ids))
            else:
                raise UserError(_('请选择联系人标签，若不存在标签，请先使用手动同步联系人标签功能！'))
            if not res.din_employee_id:
                raise UserError(_("请选择联系人对应的负责人!"))

            name = res.name  # 联系人名称
            title = res.function if res.function else ''  # 职位
            address = res.street if res.street else ''  # 地址
            remark = res.comment if res.comment else ''  # 备注
            follower_user_id = res.din_employee_id.din_id  # 负责人userid
            state_code = '86'  # 手机号国家码
            company_name = res.din_company_name if res.din_company_name else ''  # 钉钉企业公司名称
            mobile = res.mobile if res.mobile else res.phone  # 手机

            share_deptlist = list()
            if res.din_share_department_ids:
                share_deptlist = res.din_share_department_ids.mapped('din_id')
                share_deptlist = list(map(int, share_deptlist))
            share_dept_ids = share_deptlist
            share_emplist = list()
            if res.din_share_employee_ids:
                share_emplist = res.din_share_employee_ids.mapped('din_id')
            share_user_ids = share_emplist

            try:
                result = client.extcontact.create(name, follower_user_id, label_ids, mobile, state_code,
                                                  title=title, share_dept_ids=share_dept_ids, remark=remark, address=address,
                                                  company_name=company_name,
                                                  share_user_ids=share_user_ids
                                                  )
                logging.info("创建联系人返回结果:%s", result)
                res.write({'din_userid': result})
                res.message_post(body=_("钉钉消息：联系人信息已上传至钉钉"),
                                 message_type='notification')
            except Exception as e:
                raise UserError(e)

    @api.multi
    def update_ding_partner(self):
        """
        更新外部联系人

        :param user_id: 该外部联系人的userId
        :param name: 名称
        :param follower_user_id: 负责人userId
        :param state_code: 手机号国家码
        :param mobile: 手机号
        :param label_ids: 标签列表
        :param title: 职位
        :param share_dept_ids: 共享给的部门ID
        :param remark: 备注
        :param address: 地址
        :param company_name: 企业名
        :param share_user_ids: 共享给的员工userId列表
        :return:
        """
        client = get_client(self)
        for res in self:
            # 获取标签
            label_list = list()
            if res.category_id:
                for label in res.category_id:
                    label_list.append(label.din_id)
                label_list = list(map(int, label_list))  # 将列表里的字符串转成数字
            else:
                raise UserError('请选择联系人标签，若不存在标签，请先使用手动同步联系人标签功能！')

            user_id = res.din_userid  # 联系人钉钉id
            name = res.name  # 联系人名称
            follower_user_id = res.din_employee_id.din_id  # 负责人userid
            label_ids = label_list  # 标签列表
            mobile = res.mobile if res.mobile else res.phone  # 手机
            title = res.function if res.function else ''  # 职位
            address = res.street if res.street else ''  # 地址
            remark = res.comment if res.comment else ''  # 备注
            company_name = res.din_company_name if res.din_company_name else ''  # 钉钉企业公司名称

            share_deptlist = res.din_share_department_ids.mapped('din_id')
            share_deptlist = list(map(int, share_deptlist))
            share_dept_ids = share_deptlist if share_deptlist else ()
            share_emplist = res.din_share_employee_ids.mapped('din_id')
            share_user_ids = share_emplist if share_emplist else ()

            try:
                result = client.extcontact.update(user_id, name, follower_user_id, label_ids, mobile, state_code='86',
                                                  title=title, share_dept_ids=share_dept_ids, remark=remark, address=address, company_name=company_name, share_user_ids=share_user_ids)
                logging.info("更新联系人返回结果:%s", result)
                res.message_post(body="钉钉消息：联系人信息已更新至钉钉",
                                 message_type='notification')
            except Exception as e:
                raise UserError(e)

    # 重写删除方法
    @api.multi
    def unlink(self):
        for res in self:
            din_userid = res.din_userid
            super(ResPartner, self).unlink()
            if self.env['ir.config_parameter'].sudo().get_param('ali_dindin.din_delete_extcontact') and din_userid:
                self.delete_din_extcontact(din_userid)
            return True

    @api.model
    def delete_din_extcontact(self, din_userid):
        """删除钉钉联系人"""
        client = get_client(self)
        try:
            result = client.extcontact.delete(din_userid)
            logging.info("删除钉钉联系人结果:%s", result)
        except Exception as e:
            raise UserError(e)

    @api.multi
    def get_dingding_partner(self):
        """
        外部联系人详情
        获取企业外部联系人详情
        :param user_id: userId
        返回数据结构：
        {'ding_open_errcode': 0,
        'result': {
            'address': 'xxxx',
            'company_name': 'xxxx',
            'follower_user_id': '01454209',
            'label_ids': {'number': [1362340, 1362317, 136229]},
            'mobile': '189****',
            'name': '曾**',
            'remark': '电xxxx',
            'share_dept_ids': {'number': [108280604]},
            'share_user_ids': {},
            'state_code': '86',
            'title': '总经理',
            'userid': '014711'},
        'success': True}

        """
        client = get_client(self)
        for partner in self:
            userid = partner.din_userid
            try:
                result = client.extcontact.get(userid)
                logging.info(">>>获取外部联系人返回结果:%s", result)
                if result.get('ding_open_errcode') == 0:
                    result = result['result']
                    # 获取标签
                    label_list = list()
                    for label in result['label_ids']['number']:
                        category = self.env['res.partner.category'].sudo().search(
                            [('din_id', '=', str(label))])
                        if category:
                            label_list.append(category[0].id)
                    data = {
                        'name': result.get('name'),
                        'function': result.get('title'),
                        'category_id': [(6, 0, label_list)],  # 标签
                        'comment': result.get('remark'),  # 备注
                        'street': result.get('address'),  # 地址
                        'mobile': result.get('mobile'),  # 手机
                        'phone': result.get('mobile'),  # 电话
                        # 钉钉公司名称
                        'din_company_name': result.get('company_name'),
                    }
                    # 获取负责人
                    if result.get('follower_user_id'):
                        follower_user = self.env['hr.employee'].sudo().search(
                            [('din_id', '=', result.get('follower_user_id'))])
                        data.update(
                            {'din_employee_id': follower_user[0].id if follower_user else ''})
                    # 获取共享范围
                    if result.get('share_dept_ids'):
                        dep_din_ids = result['share_dept_ids']['number']
                        dep_din_ids = [str(i) for i in dep_din_ids]
                        dep_list = self.env['hr.department'].sudo().search(
                            [('din_id', 'in', dep_din_ids)])
                        data.update({'din_share_department_ids': [
                                    (6, 0, dep_list.ids)] if dep_list else ''})
                    # 获取共享员工
                    if result.get('share_user_ids'):
                        emp_din_ids = result['share_user_ids']['string']
                        emp_list = self.env['hr.employee'].sudo().search(
                            [('din_id', 'in', emp_din_ids)])
                        data.update({'din_share_employee_ids': [
                                    (6, 0, emp_list.ids)] if emp_list else ''})
                    partner.sudo().write(data)
                    partner.message_post(
                        body="钉钉消息：已从钉钉同步联系人信息", message_type='notification')
                else:
                    _logger.info("从钉钉同步联系人时发生意外，原因为:%s", result.get('errmsg'))
                    partner.message_post(body="从钉钉同步联系人失败:{}".format(
                        result.get('errmsg')), message_type='notification')
            except Exception as e:
                raise UserError(e)
