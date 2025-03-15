from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import datetime

class LichNghiLe(models.Model):
    _name = 'lich_nghi_le'
    _description = 'Lịch nghỉ lễ'
    _rec_name = 'ten_ngay_le'
    _order = "nam DESC, ngay_bat_dau ASC"
    
    ten_ngay_le = fields.Char(string='Tên ngày nghỉ', required=True)
    nam = fields.Selection(
        [(str(nam), f'Năm {nam}') for nam in range(datetime.today().year - 10, datetime.today().year + 10)],
        string="Năm",
        required=True,
        default=str(datetime.today().year)
    )
    ngay_bat_dau = fields.Date(string='Ngày bắt đầu', required=True)
    ngay_ket_thuc = fields.Date(string='Ngày kết thúc', required=True)
    so_ngay_le = fields.Integer(string='Số ngày nghỉ', compute='_compute_so_ngay_le', store=True)
    ghi_chu = fields.Text(string='Ghi chú')

    @api.constrains('ngay_bat_dau', 'ngay_ket_thuc')
    def _check_ngay_nghi(self):
        for record in self:
            if record.ngay_bat_dau > record.ngay_ket_thuc:
                raise ValidationError("Ngày bắt đầu phải trước hoặc bằng ngày kết thúc!")
            
            nam_int = int(record.nam)
            if record.ngay_bat_dau.year != nam_int or record.ngay_ket_thuc.year != nam_int:
                    raise ValidationError("Ngày bắt đầu và ngày kết thúc phải thuộc năm đã chọn!")
                
    @api.depends('ngay_bat_dau', 'ngay_ket_thuc')
    def _compute_so_ngay_le(self):
        for record in self:
            if record.ngay_bat_dau and record.ngay_ket_thuc:
                record.so_ngay_le = (record.ngay_ket_thuc - record.ngay_bat_dau).days + 1
            else:
                record.so_ngay_le = 0
                
