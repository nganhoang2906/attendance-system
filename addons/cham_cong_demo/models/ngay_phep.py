from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import datetime

class NgayPhep(models.Model):
    _name = 'ngay_phep'
    _description = 'Bảng quản lý ngày phép của nhân viên'
    _rec_name = 'nhan_vien_id'
    _order = 'nam desc'
    _sql_constraints = [
        ('unique_nhan_vien_nam', 'unique(nhan_vien_id, nam)', 'Đã có bảng ngày phép của nhân viên này trong năm!')
    ]

    nhan_vien_id = fields.Many2one('nhan_vien', string="Nhân viên", required=True)
    nam = fields.Char(string="Năm", required=True)
    so_ngay_phep_tieu_chuan = fields.Float(string="Số ngày phép tiêu chuẩn", default=12, required=True)
    so_ngay_phep_nam_truoc = fields.Float(string="Số ngày phép năm trước", default=0, required=True)
    so_ngay_phep_khac = fields.Float(string="Số ngày phép khác", default=0, required=True)
    tong_so_ngay_phep = fields.Float(string="Tổng số ngày phép", compute="_compute_tong_so_ngay_phep", store=True)
    so_ngay_da_su_dung = fields.Float(string="Số ngày phép đã sử dụng", default=0, required=True)
    so_ngay_con_lai = fields.Float(
        string="Số ngày phép còn lại", compute="_compute_so_ngay_con_lai", store=True, readonly=False
    )
    
    @api.constrains('nam')
    def _check_nam(self):
        for record in self:
            if not record.nam.isdigit() or int(record.nam) < 2000 or int(record.nam) > datetime.today().year + 10:
                raise ValidationError("Năm không hợp lệ. Vui lòng nhập năm từ 2000 trở đi và trong vòng 10 năm tới.")
            
    @api.depends('so_ngay_phep_tieu_chuan', 'so_ngay_phep_nam_truoc', 'so_ngay_phep_khac')
    def _compute_tong_so_ngay_phep(self):
        for record in self:
            record.tong_so_ngay_phep = record.so_ngay_phep_tieu_chuan + record.so_ngay_phep_nam_truoc + record.so_ngay_phep_khac
            
    @api.depends('tong_so_ngay_phep', 'so_ngay_da_su_dung')
    def _compute_so_ngay_con_lai(self):
        for record in self:
            record.so_ngay_con_lai = record.tong_so_ngay_phep - record.so_ngay_da_su_dung
            record.sudo().write({'so_ngay_con_lai': record.so_ngay_con_lai})
