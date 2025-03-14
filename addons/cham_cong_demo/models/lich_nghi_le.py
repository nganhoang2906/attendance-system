from odoo import models, fields, api
from odoo.exceptions import ValidationError

class LichNghiLe(models.Model):
    _name = 'lich_nghi_le'
    _description = 'Lịch nghỉ lễ'
    _rec_name = 'ten_ngay_le'
    _order = "nam DESC, ngay_bat_dau ASC"
    
    ten_ngay_le = fields.Char(string='Tên ngày nghỉ', required=True)
    nam = fields.Char("Năm", compute="_compute_nam", store=True)
    ngay_bat_dau = fields.Date(string='Ngày bắt đầu', required=True)
    ngay_ket_thuc = fields.Date(string='Ngày kết thúc', required=True)
    so_ngay_le = fields.Integer(string='Số ngày nghỉ', compute='_compute_so_ngay_le', store=True)
    ghi_chu = fields.Text(string='Ghi chú')

    @api.constrains('ngay_bat_dau_nghi', 'ngay_ket_thuc_nghi')
    def _check_ngay_nghi(self):
        for record in self:
            if record.ngay_bat_dau_nghi > record.ngay_ket_thuc_nghi:
                raise ValidationError("Ngày bắt đầu phải trước hoặc bằng ngày kết thúc!")
            
    @api.depends('ngay_bat_dau', 'ngay_ket_thuc')
    def _compute_so_ngay_le(self):
        for record in self:
            if record.ngay_bat_dau and record.ngay_ket_thuc:
                record.so_ngay_le = (record.ngay_ket_thuc - record.ngay_bat_dau).days + 1
            else:
                record.so_ngay_le = 0
                
    @api.depends('ngay_bat_dau')
    def _compute_nam(self):
        for record in self:
            record.nam = record.ngay_bat_dau.year if record.ngay_bat_dau else 0
