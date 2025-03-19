from odoo import models, fields, api

class TongHopChamCong(models.Model):
    _name = 'tong_hop_cham_cong'
    _description = 'Tổng hợp chấm công theo tháng'
    _rec_name = 'nhan_vien_id'

    nhan_vien_id = fields.Many2one('nhan_vien', string="Nhân viên", required=True)
    phong_ban_id = fields.Many2one('phong_ban', string="Phòng ban", related="nhan_vien_id.phong_ban_id", store=True)
    nam = fields.Integer(string="Năm", required=True)
    thang = fields.Integer(string="Tháng", required=True)

    so_lan_di_muon = fields.Integer(string="Số lần đi muộn")
    so_lan_ve_som = fields.Integer(string="Số lần về sớm")
    so_lan_xin_nghi = fields.Integer(string="Số lần xin nghỉ")
    so_lan_nghi_khong_phep = fields.Integer(string="Số lần nghỉ không phép")
