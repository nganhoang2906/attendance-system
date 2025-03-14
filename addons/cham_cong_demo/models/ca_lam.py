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
        (f"{h:02}:{m:02}", f"{h:02}:{m:02}") for h in range(24) for m in (0, 30)
    ]

    ma_ca = fields.Char("Mã ca", required=True)
    ten_ca = fields.Char("Tên ca", required=True)
    gio_vao = fields.Selection(selection=GIO_SELECTION, string="Giờ vào", required=True)
    gio_ra = fields.Selection(selection=GIO_SELECTION, string="Giờ ra", required=True)
    nghi_giua_gio = fields.Boolean("Nghỉ giữa giờ", default=False)
    gio_bat_dau_nghi_giua_gio = fields.Selection(selection=GIO_SELECTION, string="Giờ bắt đầu nghỉ giữa giờ")
    gio_ket_thuc_nghi_giua_gio = fields.Selection(selection=GIO_SELECTION, string="Giờ kết thúc nghỉ giữa giờ")
    tong_thoi_gian = fields.Float("Tổng thời gian làm", compute="_compute_tong_thoi_gian", store=True)

    @api.onchange('nghi_giua_gio')
    def _onchange_nghi_giua_gio(self):
        if not self.nghi_giua_gio:
            self.gio_bat_dau_nghi_giua_gio = False
            self.gio_ket_thuc_nghi_giua_gio = False
    
    @api.depends('gio_vao', 'gio_ra', 'nghi_giua_gio', 'gio_bat_dau_nghi_giua_gio', 'gio_ket_thuc_nghi_giua_gio')
    def _compute_tong_thoi_gian(self):
        for record in self:
            if record.gio_vao and record.gio_ra:
                gio_vao = int(record.gio_vao[:2]) + int(record.gio_vao[3:]) / 60
                gio_ra = int(record.gio_ra[:2]) + int(record.gio_ra[3:]) / 60
                tong_thoi_gian = (gio_ra - gio_vao)

                if record.nghi_giua_gio and record.gio_bat_dau_nghi_giua_gio and record.gio_ket_thuc_nghi_giua_gio:
                    gio_bat_dau_nghi = int(record.gio_bat_dau_nghi_giua_gio[:2]) + int(record.gio_bat_dau_nghi_giua_gio[3:]) / 60
                    gio_ket_thuc_nghi = int(record.gio_ket_thuc_nghi_giua_gio[:2]) + int(record.gio_ket_thuc_nghi_giua_gio[3:]) / 60
                    tong_thoi_gian -= (gio_ket_thuc_nghi - gio_bat_dau_nghi)

                record.tong_thoi_gian = max(0, tong_thoi_gian)
            else:
                record.tong_thoi_gian = 0
    
    @api.constrains('tong_thoi_gian')
    def _check_tong_thoi_gian(self):
        for record in self:
            if record.tong_thoi_gian > 8:
                raise ValidationError("Thời gian làm việc không được quá 8 tiếng mỗi ngày!")
    
    @api.constrains('gio_vao', 'gio_ra', 'gio_bat_dau_nghi_giua_gio', 'gio_ket_thuc_nghi_giua_gio', 'nghi_giua_gio')
    def _check_gio_lam_viec(self):
        for record in self:
            def time_to_minutes(time_str):
                if time_str:
                    h, m = map(int, time_str.split(':'))
                    return h * 60 + m
                return None

            gio_vao = time_to_minutes(record.gio_vao)
            gio_ra = time_to_minutes(record.gio_ra)
            gio_bd_nghi = time_to_minutes(record.gio_bat_dau_nghi_giua_gio)
            gio_kt_nghi = time_to_minutes(record.gio_ket_thuc_nghi_giua_gio)

            if gio_vao and gio_ra and gio_vao >= gio_ra:
                raise ValidationError("Giờ vào phải trước giờ ra.")

            if record.nghi_giua_gio:
                if not gio_bd_nghi or not gio_kt_nghi:
                    raise ValidationError("Cần nhập giờ nghỉ giữa giờ nếu bật chế độ nghỉ giữa giờ.")
                if gio_bd_nghi <= gio_vao or gio_bd_nghi >= gio_ra:
                    raise ValidationError("Giờ bắt đầu nghỉ giữa giờ phải sau giờ vào và trước giờ ra.")
                if gio_kt_nghi <= gio_vao or gio_kt_nghi >= gio_ra:
                    raise ValidationError("Giờ kết thúc nghỉ giữa giờ phải sau giờ vào và trước giờ ra.")
                if gio_kt_nghi <= gio_bd_nghi:
                    raise ValidationError("Giờ kết thúc nghỉ giữa giờ phải sau giờ bắt đầu nghỉ giữa giờ.")