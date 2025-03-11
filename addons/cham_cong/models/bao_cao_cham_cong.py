from odoo import models, fields, api

class BaoCaoChamCong(models.Model):
    _name = 'bao_cao_cham_cong'
    _description = 'Báo cáo chấm công theo tháng'

    name = fields.Char(string='Tên báo cáo', compute="_compute_name", store=True)
    dot_dang_ky_id = fields.Many2one('dot_dang_ky', string="Đợt đăng ký", required=True)
    thang = fields.Selection(
        [(str(i), f'Tháng {i}') for i in range(1, 13)],
        string="Tháng đăng ký",
        related="dot_dang_ky_id.thang_dang_ky",
        store=True
    )
    nam = fields.Char("Năm đăng ký", related="dot_dang_ky_id.nam_dang_ky", store=True)
    so_nhan_vien_di_muon = fields.Integer(string='Số nhân viên đi muộn', store=True)
    so_nhan_vien_ve_som = fields.Integer(string='Số nhân viên về sớm', store=True)
    so_nhan_vien_nghi = fields.Integer(string='Số nhân viên nghỉ', store=True)
