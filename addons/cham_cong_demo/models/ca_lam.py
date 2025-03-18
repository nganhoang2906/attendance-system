from odoo import models, fields, api
from odoo.exceptions import ValidationError

class CaLam(models.Model):
    _name = 'ca_lam'
    _description = 'Bảng chứa thông tin ca Làm Việc'
    _rec_name = 'ten_ca'
    _sql_constraints = [
        ('unique_ma_ca', 'unique(ma_ca)', 'Đã tồn tại mã ca!')
    ]

    GIO_SELECTION = [
        (f"{h:02}:{m:02}:00", f"{h:02}:{m:02}:00") for h in range(24) for m in (0, 30)
    ]

    ma_ca = fields.Char("Mã ca", required=True)
    ten_ca = fields.Char("Tên ca", required=True)
    gio_vao_ca = fields.Selection(selection=GIO_SELECTION, string="Giờ vào ca", required=True)
    gio_ra_ca = fields.Selection(selection=GIO_SELECTION, string="Giờ ra ca", required=True)
    nghi_giua_ca = fields.Boolean("Nghỉ giữa ca", default=False)
    gio_bat_dau_nghi_giua_ca = fields.Selection(selection=GIO_SELECTION, string="Giờ bắt đầu nghỉ giữa ca")
    gio_ket_thuc_nghi_giua_ca = fields.Selection(selection=GIO_SELECTION, string="Giờ kết thúc nghỉ giữa ca")
    tong_thoi_gian = fields.Float("Tổng thời gian làm", compute="_compute_tong_thoi_gian", store=True)

    @api.onchange('nghi_giua_ca')
    def _onchange_nghi_giua_ca(self):
        if not self.nghi_giua_ca:
            self.gio_bat_dau_nghi_giua_ca = False
            self.gio_ket_thuc_nghi_giua_ca = False
    
    @api.depends('gio_vao_ca', 'gio_ra_ca', 'nghi_giua_ca', 'gio_bat_dau_nghi_giua_ca', 'gio_ket_thuc_nghi_giua_ca')
    def _compute_tong_thoi_gian(self):
        for record in self:
            if record.gio_vao_ca and record.gio_ra_ca:
                gio_vao_ca = int(record.gio_vao_ca[:2]) + int(record.gio_vao_ca[3:5]) / 60
                gio_ra_ca = int(record.gio_ra_ca[:2]) + int(record.gio_ra_ca[3:5]) / 60
                tong_thoi_gian = (gio_ra_ca - gio_vao_ca)

                if record.nghi_giua_ca and record.gio_bat_dau_nghi_giua_ca and record.gio_ket_thuc_nghi_giua_ca:
                    gio_bat_dau_nghi = int(record.gio_bat_dau_nghi_giua_ca[:2]) + int(record.gio_bat_dau_nghi_giua_ca[3:5]) / 60
                    gio_ket_thuc_nghi = int(record.gio_ket_thuc_nghi_giua_ca[:2]) + int(record.gio_ket_thuc_nghi_giua_ca[3:5]) / 60
                    tong_thoi_gian -= (gio_ket_thuc_nghi - gio_bat_dau_nghi)

                record.tong_thoi_gian = max(0, tong_thoi_gian)
            else:
                record.tong_thoi_gian = 0
    
    @api.constrains('tong_thoi_gian')
    def _check_tong_thoi_gian(self):
        for record in self:
            if record.tong_thoi_gian > 8 or record.tong_thoi_gian <= 0:
                raise ValidationError("Thời gian làm việc không được quá 8 tiếng mỗi ngày!")
    
    @api.constrains('gio_vao_ca', 'gio_ra_ca', 'gio_bat_dau_nghi_giua_ca', 'gio_ket_thuc_nghi_giua_ca', 'nghi_giua_ca')
    def _check_gio_lam_viec(self):
        for record in self:
            def time_to_minutes(time_str):
                if time_str:
                    h, m, s = map(int, time_str.split(':'))
                    return h * 60 + m
                return None

            gio_vao_ca = time_to_minutes(record.gio_vao_ca)
            gio_ra_ca = time_to_minutes(record.gio_ra_ca)
            gio_bd_nghi = time_to_minutes(record.gio_bat_dau_nghi_giua_ca)
            gio_kt_nghi = time_to_minutes(record.gio_ket_thuc_nghi_giua_ca)

            if gio_vao_ca and gio_ra_ca and gio_vao_ca >= gio_ra_ca:
                raise ValidationError("Giờ vào ca phải trước giờ ra ca!")

            if record.nghi_giua_ca:
                if not gio_bd_nghi or not gio_kt_nghi:
                    raise ValidationError("Cần nhập giờ nghỉ giữa ca nếu bật chế độ nghỉ giữa ca!")
                if gio_bd_nghi <= gio_vao_ca or gio_bd_nghi >= gio_ra_ca:
                    raise ValidationError("Giờ bắt đầu nghỉ giữa ca phải sau giờ vào ca và trước giờ ra ca!")
                if gio_kt_nghi <= gio_vao_ca or gio_kt_nghi >= gio_ra_ca:
                    raise ValidationError("Giờ kết thúc nghỉ giữa ca phải sau giờ vào ca và trước giờ ra ca!")
                if gio_kt_nghi <= gio_bd_nghi:
                    raise ValidationError("Giờ kết thúc nghỉ giữa ca phải sau giờ bắt đầu nghỉ giữa ca!")