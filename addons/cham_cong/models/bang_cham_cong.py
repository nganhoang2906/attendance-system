from odoo import models, fields, api
from datetime import datetime
from odoo.exceptions import ValidationError

class BangChamCong(models.Model):
    _name = 'bang_cham_cong'
    _description = "Bảng chấm công"
    _rec_name = 'nhan_vien_id'

    nhan_vien_id = fields.Many2one('nhan_vien', string="Nhân viên", required=True)
    ngay_cham_cong = fields.Date("Ngày chấm công", required=True)
    thoi_gian_vao = fields.Datetime("Giờ vào")
    thoi_gian_ra = fields.Datetime("Giờ ra")
    thoi_gian_lam = fields.Float("Số giờ làm", compute="_compute_thoi_gian_lam", store=True)

    @api.depends('thoi_gian_vao', 'thoi_gian_ra')
    def _compute_thoi_gian_lam(self):
        for record in self:
            if record.thoi_gian_ra:
                delta = record.thoi_gian_ra - record.thoi_gian_vao
                record.thoi_gian_lam = delta.total_seconds() / 3600
            else:
                record.thoi_gian_lam = 0
