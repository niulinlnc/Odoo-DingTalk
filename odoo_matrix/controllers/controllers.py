# -*- coding: utf-8 -*-
from odoo import http

# class .(http.Controller):
#     @http.route('/././', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/././objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('..listing', {
#             'root': '/./.',
#             'objects': http.request.env['...'].search([]),
#         })

#     @http.route('/././objects/<model("..."):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('..object', {
#             'object': obj
#         })