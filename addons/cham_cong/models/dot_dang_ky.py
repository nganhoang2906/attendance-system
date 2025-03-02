from odoo import models, fields, api
from datetime import datetime, date, timedelta
import calendar

class DotDangKy(models.Model):
    _name = 'dot_dang_ky'
    _description = "Bảng chứa thông tin đợt đăng ký"
    _rec_name = 'ten_dot'

    ma_dot = fields.Char("Mã đợt", required=True)
    ten_dot = fields.Char("Tên đợt", compute='_compute_ten_dot', store=True)
    nam_dang_ky = fields.Char("Năm đăng ký", required=True)
    thang_dang_ky = fields.Selection(
        [(str(i), f'Tháng {i}') for i in range(1, 13)],
        string="Tháng đăng ký",
        required=True
    )
    ngay_bat_dau = fields.Date("Thời gian bắt đầu", compute='_compute_thoi_gian', store=True)
    ngay_ket_thuc = fields.Date("Thời gian kết thúc", compute='_compute_thoi_gian', store=True)
    nhan_vien_ids = fields.Many2many('nhan_vien', string="Nhân viên đăng ký")
    han_dang_ky = fields.Date("Hạn đăng ký", required=True)
    trang_thai_dang_ky = fields.Selection(
        [
            ("Đang mở", "Đang mở"),
            ("Đã hết hạn", "Đã hết hạn"),
            ("Đã đóng", "Đã đóng")
        ],
        string="Trạng thái đăng ký",
        compute="_compute_trang_thai_dang_ky",
        store=True
    )
    trang_thai_ap_dung = fields.Selection(
        [
            ("Đang áp dụng", "Đang áp dụng"),
            ("Ngừng áp dụng", "Ngừng áp dụng"),
            ("Chưa áp dụng", "Chưa áp dụng")
        ],
        string="Trạng thái áp dụng",
        compute="_compute_trang_thai_ap_dung",
        store=True
    )
    dang_ky_ca_lam_theo_ngay_ids = fields.One2many('dang_ky_ca_lam_theo_ngay', inverse_name='dot_dang_ky_id', string="Đăng ký ca làm")

    def _compute_nhan_vien(self):
        for record in self:
            record.nhan_vien_ids = self.env['nhan_vien'].search([
                ('phong_ban_id', '!=', False),
                ('chuc_vu_id', '!=', False)
            ])
            
    @api.depends('han_dang_ky')
    def _compute_trang_thai_dang_ky(self):
        today = date.today()
        for record in self:
            if record.han_dang_ky and today > record.han_dang_ky:
                record.trang_thai_dang_ky = "Đã hết hạn"
            else:
                record.trang_thai_dang_ky = "Đang mở"
    
    @api.depends('ngay_bat_dau', 'ngay_ket_thuc')
    def _compute_trang_thai_ap_dung(self):
        today = date.today()
        for record in self:
            if record.ngay_ket_thuc and today > record.ngay_ket_thuc:
                record.trang_thai_ap_dung = "Ngừng áp dụng"
            elif record.ngay_bat_dau and today > record.ngay_bat_dau:
                record.trang_thai_ap_dung = "Đang áp dụng"
            else:
                record.trang_thai_ap_dung = "Chưa áp dụng"
    
    @api.depends('thang_dang_ky', 'nam_dang_ky')
    def _compute_thoi_gian(self):
        for record in self:
            if record.thang_dang_ky and record.nam_dang_ky:
                thang = int(record.thang_dang_ky)
                nam = int(record.nam_dang_ky)
                ngay_dau_thang = date(nam, thang, 1)
                ngay_cuoi_thang = date(nam, thang, calendar.monthrange(nam, thang)[1])
                record.ngay_bat_dau = ngay_dau_thang
                record.ngay_ket_thuc = ngay_cuoi_thang
            else:
                record.ngay_bat_dau = False
                record.ngay_ket_thuc = False
    
    @api.depends('thang_dang_ky', 'nam_dang_ky')
    def _compute_ten_dot(self):
        for record in self:
            if record.thang_dang_ky and record.nam_dang_ky:
                record.ten_dot = f"Tháng {record.thang_dang_ky}/{record.nam_dang_ky}"
            else:
                record.ten_dot = False

    def _sync_dang_ky_ca_lam(self):
        for record in self:
            self.env['dang_ky_ca_lam_theo_ngay'].search([
                ('dot_dang_ky_id', '=', record.id)
            ]).unlink()

            if not record.nhan_vien_ids or not record.ngay_bat_dau or not record.ngay_ket_thuc:
                continue

            records = []
            ngay_lam = record.ngay_bat_dau
            while ngay_lam <= record.ngay_ket_thuc:
                for nhan_vien in record.nhan_vien_ids:
                    records.append({
                        'dot_dang_ky_id': record.id,
                        'nhan_vien_id': nhan_vien.id,
                        'ngay_lam': ngay_lam,
                        'ca_lam': False
                    })
                ngay_lam += timedelta(days=1)

            if records:
                self.env['dang_ky_ca_lam_theo_ngay'].create(records)

    @api.model
    def create(self, vals):
        record = super(DotDangKy, self).create(vals)
        record._sync_dang_ky_ca_lam()
        return record

    def write(self, vals):
        res = super(DotDangKy, self).write(vals)
        self._sync_dang_ky_ca_lam()
        return res

    def unlink(self):
        for record in self:
            self.env['dang_ky_ca_lam_theo_ngay'].search([
                ('dot_dang_ky_id', '=', record.id)
            ]).unlink()
        return super(DotDangKy, self).unlink()