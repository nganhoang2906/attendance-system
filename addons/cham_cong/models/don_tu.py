from odoo import models, fields, api
from datetime import datetime

class DonTu(models.Model):
    _name = 'don_tu'
    _description = 'Đơn từ'
    _rec_name = 'nhan_vien_id'

    nhan_vien_id = fields.Many2one('nhan_vien', string="Nhân viên", required=True)
    ngay_lam_don = fields.Date("Ngày làm đơn", required=True, default=fields.Date.today)
    ngay_ap_dung = fields.Date("Ngày áp dụng", required=True)
    
    trang_thai_duyet = fields.Selection([
        ('Chờ duyệt', 'Chờ duyệt'),
        ('Đã duyệt', 'Đã duyệt'),
        ('Từ chối', 'Từ chối')
    ], string="Trạng thái phê duyệt", default='Chờ duyệt', required=True)

    loai_don = fields.Selection([
        ('Đơn xin nghỉ', 'Đơn xin nghỉ'),
        ('Đơn xin đi muộn', 'Đơn xin đi muộn'),
        ('Đơn xin về sớm', 'Đơn xin về sớm')
    ], string="Loại đơn", required=True)

    thoi_gian_xin = fields.Float("Thời gian xin (phút)")