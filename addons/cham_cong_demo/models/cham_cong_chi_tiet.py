from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import date, datetime, timedelta
from pytz import timezone, UTC

class ChamCongChiTiet(models.Model):
    _name = 'cham_cong_chi_tiet'
    _description = 'Chấm công chi tiết'
    _rec_name = 'nhan_vien_id'
    _order = 'ngay_cham_cong desc'
    _sql_constraints = [
        ('unique_cham_cong_chi_tiet', 'unique(nhan_vien_id, ngay_cham_cong)', 'Nhân viên này đã có chấm công chi tiết vào ngày này!'),
    ]
    
    nhan_vien_id = fields.Many2one('nhan_vien', string="Nhân viên", required=True)
    ngay_cham_cong = fields.Date(string="Ngày chấm công", required=True)
    ngay_lam_viec = fields.Selection(
        [
            ('Ngày thường', "Ngày thường"),
            ('Ngày nghỉ', "Ngày nghỉ"),
            ('Ngày lễ', "Ngày lễ"),
        ],
        string="Ngày làm việc", compute="_compute_ngay_lam_viec", store=True
    )
    ca_lam_id = fields.Many2one('ca_lam', string="Ca làm", compute="_compute_ca_lam_id", store=True)

    gio_vao_ca = fields.Selection(related='ca_lam_id.gio_vao_ca', string="Giờ vào ca", store=True)
    gio_ra_ca = fields.Selection(related='ca_lam_id.gio_ra_ca', string="Giờ ra ca", store=True)
    nghi_giua_ca = fields.Boolean(related='ca_lam_id.nghi_giua_ca', string="Nghỉ giữa ca", store=True)
    gio_bat_dau_nghi_giua_ca = fields.Selection(related='ca_lam_id.gio_bat_dau_nghi_giua_ca', string="Giờ bắt đầu nghỉ giữa ca", store=True)
    gio_ket_thuc_nghi_giua_ca = fields.Selection(related='ca_lam_id.gio_ket_thuc_nghi_giua_ca', string="Giờ kết thúc nghỉ giữa ca", store=True)

    cham_vao_ca = fields.Datetime(string="Chấm vào")
    cham_ra_giua_ca = fields.Datetime(string="Chấm ra giữa ca")
    cham_vao_giua_ca = fields.Datetime(string="Chấm vào giữa ca")
    cham_ra_ca = fields.Datetime(string="Chấm ra")
    
    so_phut_di_muon_dau_ca = fields.Integer(string="Số phút đi muộn đầu ca", compute="_compute_vao_ca", store=True)
    so_phut_ve_som_giua_ca = fields.Integer(string="Số phút về sớm giữa ca", compute="_compute_ra_giua_ca", store=True)
    so_phut_di_muon_giua_ca = fields.Integer(string="Số phút đi muộn giữa ca", compute="_compute_vao_giua_ca", store=True)
    so_phut_ve_som_cuoi_ca = fields.Integer(string="Số phút về sớm cuối ca", compute="_compute_ra_ca", store=True)
    
    trang_thai_vao_ca = fields.Selection([('Đúng giờ', "Đúng giờ"), ('Đi muộn', "Đi muộn"), ('Chưa chấm vào', "Chưa chấm vào"), ('Nghỉ buổi sáng', "Nghỉ buổi sáng"), ('Nghỉ', "Nghỉ")], string="Trạng thái vào ca", compute="_compute_vao_ca", store=True)
    trang_thai_ra_giua_ca = fields.Selection([('Đúng giờ', "Đúng giờ"), ('Về sớm', "Về sớm"), ('Chưa chấm ra', "Chưa chấm ra"), ('Nghỉ buổi sáng', "Nghỉ buổi sáng"), ('Nghỉ', "Nghỉ")], string="Trạng thái ra giữa ca", compute="_compute_ra_giua_ca", store=True)
    trang_thai_vao_giua_ca = fields.Selection([('Đúng giờ', "Đúng giờ"), ('Đi muộn', "Đi muộn"), ('Chưa chấm vào', "Chưa chấm vào"), ('Nghỉ buổi chiều', "Nghỉ buổi chiều"), ('Nghỉ', "Nghỉ")], string="Trạng thái vào giữa ca", compute="_compute_vao_giua_ca", store=True)
    trang_thai_ra_ca = fields.Selection([('Đúng giờ', "Đúng giờ"), ('Về sớm', "Về sớm"), ('Chưa chấm ra', "Chưa chấm ra"), ('Nghỉ buổi chiều', "Nghỉ buổi chiều"), ('Nghỉ', "Nghỉ")], string="Trạng thái ra ca", compute="_compute_ra_ca", store=True)
    
    trang_thai_cham_cong = fields.Selection([
        ('Đúng giờ', "Đúng giờ"),
        ('Đi muộn', "Đi muộn"),
        ('Về sớm', "Về sớm"),
        ('Đi muộn về sớm', "Đi muộn về sớm"),
        ('Chưa chấm công đủ', "Chưa chấm công đủ"),
        ('Nghỉ', "Nghỉ"),
        ('Nghỉ không phép', "Nghỉ không phép"),
    ], string="Trạng thái chấm công", compute="_compute_trang_thai_cham_cong", store=True)

    so_phut_di_muon = fields.Integer(string="Số phút đi muộn", compute="_compute_ket_qua_cham_cong", store=True)
    so_phut_ve_som = fields.Integer(string="Số phút về sớm", compute="_compute_ket_qua_cham_cong", store=True)
    so_gio_lam_them = fields.Float(string="Số giờ làm thêm", compute="_compute_ket_qua_cham_cong", store=True)
    tong_gio_lam = fields.Float(string="Tổng giờ làm", compute="_compute_ket_qua_cham_cong", store=True)
    so_gio_cong = fields.Float(string="Số giờ công", compute="_compute_ket_qua_cham_cong", store=True)

    don_xin_nghi_id = fields.Many2one('don_xin_nghi', string="Đơn xin nghỉ", compute="_compute_don_xin_nghi_id", store=True)
    don_xin_di_muon_ve_som_id = fields.Many2one('don_xin_di_muon_ve_som', string="Đơn xin đi muộn về sớm", compute="_compute_don_xin_di_muon_ve_som_id", store=True)
    don_dang_ky_lam_them_gio_id = fields.Many2one('don_dang_ky_lam_them_gio', string="Đơn đăng ký làm thêm giờ", compute="_compute_don_dang_ky_lam_them_gio_id", store=True)
    
    trang_thai = fields.Selection(
        [
            ('Chưa chốt công', "Chưa chốt công"),
            ('Đã chốt công', "Đã chốt công"),
        ],
        string="Trạng thái", default="Chưa chốt công", required=True
    )
    
    @api.depends('ngay_cham_cong')
    def _compute_ngay_lam_viec(self):
        for record in self:
            if not record.ngay_cham_cong:
                record.ngay_lam_viec = False
                continue
            
            ngay_le = self.env['lich_nghi_le'].search([
                ('ngay_bat_dau', '<=', record.ngay_cham_cong),
                ('ngay_ket_thuc', '>=', record.ngay_cham_cong)
            ], limit=1)

            if ngay_le:
                record.ngay_lam_viec = 'Ngày lễ'
            elif record.ngay_cham_cong.weekday() == 6:
                record.ngay_lam_viec = 'Ngày nghỉ'
            else:
                record.ngay_lam_viec = 'Ngày thường'
    
    @api.depends('ngay_cham_cong', 'nhan_vien_id', 'ngay_lam_viec')
    def _compute_ca_lam_id(self):
        for record in self:
            if not record.nhan_vien_id or not record.ngay_cham_cong:
                record.ca_lam_id = False
                continue

            ca_lam = False

            if record.ngay_lam_viec == 'Ngày thường':
                dang_ky_ca = self.env['dang_ky_ca_lam'].search([
                    ('nhan_vien_id', '=', record.nhan_vien_id.id),
                    ('ngay_dang_ky', '=', record.ngay_cham_cong)
                ], limit=1)
                if dang_ky_ca:
                    ca_lam = dang_ky_ca.ca_lam_id

            elif record.ngay_lam_viec in ['Ngày nghỉ', 'Ngày lễ']:
                don_lam_them = self.env['don_dang_ky_lam_them_gio'].search([
                    ('nhan_vien_id', '=', record.nhan_vien_id.id),
                    ('ngay_ap_dung', '=', record.ngay_cham_cong)
                ], limit=1)
                if don_lam_them:
                    ca_lam = don_lam_them.ca_lam_id

            record.ca_lam_id = ca_lam.id if ca_lam else False

    @api.constrains('ngay_cham_cong', 'ca_lam_id')
    def _check_ca_lam(self):
        for record in self:
            if record.ngay_cham_cong and not record.ca_lam_id:
                raise ValidationError(f"Nhân viên không làm việc vào ngày {record.ngay_cham_cong.strftime('%d/%m/%Y')}")
    
    @api.constrains('cham_vao_ca', 'cham_ra_giua_ca', 'cham_vao_giua_ca', 'cham_ra_ca', 'ngay_cham_cong')
    def _check_cham_cong_ngay(self):
        for record in self:
            if not record.ngay_cham_cong:
                continue
            
            for field_name in ['cham_vao_ca', 'cham_ra_giua_ca', 'cham_vao_giua_ca', 'cham_ra_ca']:
                ngay = getattr(record, field_name)
                if ngay:
                    # Chuyển datetime về UTC+7
                    ngay_utc7 = ngay + timedelta(hours=7)
                    
                    if ngay_utc7.date() != record.ngay_cham_cong:
                        raise ValidationError(f"Thời gian chấm công không thuộc ngày {record.ngay_cham_cong.strftime('%d/%m/%Y')}")

    @api.onchange('ngay_cham_cong')
    def _onchange_ngay_cham_cong(self):
        self.cham_vao_ca = False
        self.cham_ra_giua_ca = False
        self.cham_vao_giua_ca = False
        self.cham_ra_ca = False

    @api.constrains('cham_vao_ca', 'cham_ra_giua_ca', 'cham_vao_giua_ca', 'cham_ra_ca', 'nghi_giua_ca')
    def _check_thoi_gian_cham_cong(self):
        for record in self:
            cham_vao_ca = record.cham_vao_ca
            cham_ra_giua_ca = record.cham_ra_giua_ca
            cham_vao_giua_ca = record.cham_vao_giua_ca
            cham_ra_ca = record.cham_ra_ca
            nghi_giua_ca = record.nghi_giua_ca

            if not cham_vao_ca or not cham_ra_ca:
                continue
            
            if cham_vao_ca and cham_ra_ca and cham_vao_ca >= cham_ra_ca:
                raise ValidationError("Giờ vào ca phải trước giờ ra ca!")

            if nghi_giua_ca:
                if not cham_ra_giua_ca or not cham_vao_giua_ca:
                    continue

                if cham_ra_giua_ca <= cham_vao_ca or cham_ra_giua_ca >= cham_ra_ca:
                    raise ValidationError("Giờ ra ca giữa ca phải sau giờ vào ca và trước giờ ra ca!")

                if cham_vao_giua_ca <= cham_vao_ca or cham_vao_giua_ca >= cham_ra_ca:
                    raise ValidationError("Giờ vào ca giữa ca phải sau giờ vào ca và trước giờ ra ca!")

                if cham_vao_giua_ca <= cham_ra_giua_ca:
                    raise ValidationError("Giờ vào ca giữa ca phải sau giờ ra ca giữa ca!")

    @api.depends('nhan_vien_id', 'ngay_cham_cong')
    def _compute_don_xin_nghi_id(self):
        for record in self:
            don_xin_nghi = self.env['don_xin_nghi'].search([
                ('nhan_vien_id', '=', record.nhan_vien_id.id),
                ('trang_thai', '=', 'Đã duyệt'),
                ('ngay_bat_dau_nghi', '<=', record.ngay_cham_cong),
                ('ngay_ket_thuc_nghi', '>=', record.ngay_cham_cong),
            ], limit=1)
            
            record.don_xin_nghi_id = don_xin_nghi.id if don_xin_nghi else False
            
    @api.depends('nhan_vien_id', 'ngay_cham_cong')
    def _compute_don_xin_di_muon_ve_som_id(self):
        for record in self:
            don_xin_di_muon_ve_som = self.env['don_xin_di_muon_ve_som'].search([
                ('nhan_vien_id', '=', record.nhan_vien_id.id),
                ('trang_thai', '=', 'Đã duyệt'),
                ('ngay_ap_dung', '=', record.ngay_cham_cong),
            ], limit=1)
            record.don_xin_di_muon_ve_som_id = don_xin_di_muon_ve_som.id if don_xin_di_muon_ve_som else False

    @api.depends('nhan_vien_id', 'ngay_cham_cong')
    def _compute_don_dang_ky_lam_them_gio_id(self):
        for record in self:
            don_dang_ky_lam_them_gio = self.env['don_dang_ky_lam_them_gio'].search([
                ('nhan_vien_id', '=', record.nhan_vien_id.id),
                ('trang_thai', '=', 'Đã duyệt'),
                ('ngay_ap_dung', '=', record.ngay_cham_cong),
            ], limit=1)
            record.don_dang_ky_lam_them_gio_id = don_dang_ky_lam_them_gio.id if don_dang_ky_lam_them_gio else False
    
    def _convert_time_to_datetime(self, ngay, gio_str):
        user_tz = self.env.user.tz or 'UTC'
        tz = timezone(user_tz)
        if not ngay or not gio_str:
            return None
        h, m, s = map(int, gio_str.split(':'))
        dt = datetime.combine(ngay, datetime.min.time()) + timedelta(hours=h, minutes=m, seconds=s)
        return tz.localize(dt).astimezone(UTC).replace(tzinfo=None)
    
    @api.depends('cham_vao_ca', 'ca_lam_id.gio_vao_ca', 'don_xin_nghi_id', 'don_xin_di_muon_ve_som_id', 'don_dang_ky_lam_them_gio_id')
    def _compute_vao_ca(self):
        for record in self:
            if not record.ca_lam_id:
                record.trang_thai_vao_ca = False
                record.so_phut_di_muon_dau_ca = 0
                continue

            ngay = record.ngay_cham_cong
            gio_vao_ca = self._convert_time_to_datetime(ngay, record.ca_lam_id.gio_vao_ca)

            if record.don_xin_nghi_id:
                don_xin_nghi = record.don_xin_nghi_id
                if don_xin_nghi.nghi_nua_ngay:
                    if record.ca_lam_id.ten_ca == "Cả ngày" and don_xin_nghi.buoi_nghi == "Sáng":
                        record.trang_thai_vao_ca = "Nghỉ buổi sáng"
                        record.so_phut_di_muon_dau_ca = 0
                        continue
                else:
                    record.trang_thai_vao_ca = "Nghỉ"
                    record.so_phut_di_muon_dau_ca = 0
                    continue

            # Không nghỉ, chưa chấm công
            if not record.cham_vao_ca:
                record.trang_thai_vao_ca = "Chưa chấm vào"
                record.so_phut_di_muon_dau_ca = 0
            else:
                so_phut_di_muon = max(0, int((record.cham_vao_ca - gio_vao_ca).total_seconds() // 60))

                if record.don_xin_di_muon_ve_som_id:
                    don_xin_di_muon = record.don_xin_di_muon_ve_som_id
                    if don_xin_di_muon.so_phut_xin_di_muon_dau_ca > 0:
                        so_phut_di_muon = max(0, so_phut_di_muon - don_xin_di_muon.so_phut_xin_di_muon_dau_ca)
                        record.trang_thai_vao_ca = "Đi muộn" if so_phut_di_muon > 0 else "Đúng giờ"
                        record.so_phut_di_muon_dau_ca = so_phut_di_muon
                        continue
                
                if record.don_dang_ky_lam_them_gio_id:
                    don_lam_them = record.don_dang_ky_lam_them_gio_id
                    if don_lam_them.thoi_diem_lam_them != "Sau ca" and don_lam_them.lam_ngoai_ca_tu:
                        lam_ngoai_ca_tu = self._convert_time_to_datetime(ngay, don_lam_them.lam_ngoai_ca_tu)
                        so_phut_di_muon = max(0, int((record.cham_vao_ca - lam_ngoai_ca_tu).total_seconds() // 60))
                        record.trang_thai_vao_ca = "Đi muộn" if so_phut_di_muon > 0 else "Đúng giờ"
                        record.so_phut_di_muon_dau_ca = so_phut_di_muon

                record.trang_thai_vao_ca = "Đi muộn" if so_phut_di_muon > 0 else "Đúng giờ"
                record.so_phut_di_muon_dau_ca = so_phut_di_muon
                
    @api.depends('cham_ra_giua_ca', 'ca_lam_id.gio_bat_dau_nghi_giua_ca', 'don_xin_nghi_id', 'don_xin_di_muon_ve_som_id')
    def _compute_ra_giua_ca(self):
        for record in self:
            if not record.ca_lam_id:
                record.trang_thai_ra_giua_ca = False
                record.so_phut_ve_som_giua_ca = 0
                continue
            if record.nghi_giua_ca == False:
                record.trang_thai_ra_giua_ca = False
                record.so_phut_ve_som_giua_ca = 0
                continue

            ngay = record.ngay_cham_cong
            gio_bat_dau_nghi_giua_ca = self._convert_time_to_datetime(ngay, record.ca_lam_id.gio_bat_dau_nghi_giua_ca)

            if record.don_xin_nghi_id:
                don_xin_nghi = record.don_xin_nghi_id
                if don_xin_nghi.nghi_nua_ngay:
                    if record.ca_lam_id.ten_ca == "Cả ngày" and don_xin_nghi.buoi_nghi == "Sáng":
                        record.trang_thai_ra_giua_ca = "Nghỉ buổi sáng"
                        record.so_phut_ve_som_giua_ca = 0
                        continue
                else:
                    record.trang_thai_ra_giua_ca = "Nghỉ"
                    record.so_phut_ve_som_giua_ca = 0
                    continue

            # Không nghỉ, chưa chấm công
            if not record.cham_ra_giua_ca:
                record.trang_thai_ra_giua_ca = "Chưa chấm ra"
                record.so_phut_ve_som_giua_ca = 0
            else:
                so_phut_ve_som = max(0, int((gio_bat_dau_nghi_giua_ca - record.cham_ra_giua_ca).total_seconds() // 60))

                if record.don_xin_di_muon_ve_som_id:
                    don_xin_ve_som = record.don_xin_di_muon_ve_som_id
                    if don_xin_ve_som.so_phut_xin_ve_som_giua_ca > 0:
                        so_phut_ve_som = max(0, so_phut_ve_som - don_xin_ve_som.so_phut_xin_ve_som_giua_ca)
                        record.trang_thai_ra_giua_ca = "Về sớm" if so_phut_ve_som > 0 else "Đúng giờ"
                        record.so_phut_ve_som_giua_ca = so_phut_ve_som
                        continue

                record.trang_thai_ra_giua_ca = "Về sớm" if so_phut_ve_som > 0 else "Đúng giờ"
                record.so_phut_ve_som_giua_ca = so_phut_ve_som


    @api.depends('cham_vao_giua_ca', 'ca_lam_id.gio_ket_thuc_nghi_giua_ca', 'don_xin_nghi_id', 'don_xin_di_muon_ve_som_id')
    def _compute_vao_giua_ca(self):
        for record in self:
            if not record.ca_lam_id:
                record.trang_thai_vao_giua_ca = False
                record.so_phut_di_muon_giua_ca = 0
                continue
            
            if record.nghi_giua_ca == False:
                record.trang_thai_vao_giua_ca = False
                record.so_phut_di_muon_giua_ca = 0
                continue
            
            ngay = record.ngay_cham_cong
            gio_ket_thuc_nghi_giua_ca = self._convert_time_to_datetime(ngay, record.ca_lam_id.gio_ket_thuc_nghi_giua_ca)

            if record.don_xin_nghi_id:
                don_xin_nghi = record.don_xin_nghi_id
                if don_xin_nghi.nghi_nua_ngay:
                    if record.ca_lam_id.ten_ca == "Cả ngày" and don_xin_nghi.buoi_nghi == "Chiều":
                        record.trang_thai_vao_giua_ca = "Nghỉ buổi chiều"
                        record.so_phut_di_muon_giua_ca = 0
                        continue
                else:
                    record.trang_thai_vao_giua_ca = "Nghỉ"
                    record.so_phut_di_muon_giua_ca = 0
                    continue

            # Không nghỉ, chưa chấm công
            if not record.cham_vao_giua_ca:
                record.trang_thai_vao_giua_ca = "Chưa chấm vào"
                record.so_phut_di_muon_giua_ca = 0
            else:
                so_phut_di_muon = max(0, int((record.cham_vao_giua_ca - gio_ket_thuc_nghi_giua_ca).total_seconds() // 60))

                if record.don_xin_di_muon_ve_som_id:
                    don_xin_di_muon = record.don_xin_di_muon_ve_som_id
                    if don_xin_di_muon.so_phut_xin_di_muon_giua_ca > 0:
                        so_phut_di_muon = max(0, so_phut_di_muon - don_xin_di_muon.so_phut_xin_di_muon_giua_ca)
                        record.trang_thai_vao_giua_ca = "Đi muộn" if so_phut_di_muon > 0 else "Đúng giờ"
                        record.so_phut_di_muon_giua_ca = so_phut_di_muon
                        continue

                record.trang_thai_vao_giua_ca = "Đi muộn" if so_phut_di_muon > 0 else "Đúng giờ"
                record.so_phut_di_muon_giua_ca = so_phut_di_muon

    @api.depends('cham_ra_ca', 'ca_lam_id.gio_ra_ca', 'don_xin_nghi_id', 'don_xin_di_muon_ve_som_id', 'don_dang_ky_lam_them_gio_id')
    def _compute_ra_ca(self):
        for record in self:
            if not record.ca_lam_id:
                record.trang_thai_ra_ca = False
                record.so_phut_ve_som_cuoi_ca = 0
                continue

            ngay = record.ngay_cham_cong
            gio_ra_ca = self._convert_time_to_datetime(ngay, record.ca_lam_id.gio_ra_ca)

            if record.don_xin_nghi_id:
                don_xin_nghi = record.don_xin_nghi_id
                if don_xin_nghi.nghi_nua_ngay:
                    if record.ca_lam_id.ten_ca == "Cả ngày" and don_xin_nghi.buoi_nghi == "Chiều":
                        record.trang_thai_ra_ca = "Nghỉ buổi chiều"
                        record.so_phut_ve_som_cuoi_ca = 0
                        continue
                else:
                    record.trang_thai_ra_ca = "Nghỉ"
                    record.so_phut_ve_som_cuoi_ca = 0
                    continue

            # Không nghỉ, chưa chấm công
            if not record.cham_ra_ca:
                record.trang_thai_ra_ca = "Chưa chấm ra"
                record.so_phut_ve_som_cuoi_ca = 0
            else:
                so_phut_ve_som = max(0, int((gio_ra_ca - record.cham_ra_ca).total_seconds() // 60))

                if record.don_xin_di_muon_ve_som_id:
                    don_xin_ve_som = record.don_xin_di_muon_ve_som_id
                    if don_xin_ve_som.so_phut_xin_ve_som_cuoi_ca > 0:
                        so_phut_ve_som = max(0, so_phut_ve_som - don_xin_ve_som.so_phut_xin_ve_som_cuoi_ca)
                        record.trang_thai_ra_ca = "Về sớm" if so_phut_ve_som > 0 else "Đúng giờ"
                        record.so_phut_ve_som_cuoi_ca = so_phut_ve_som
                        continue

                if record.don_dang_ky_lam_them_gio_id:
                    don_lam_them = record.don_dang_ky_lam_them_gio_id
                    if don_lam_them.thoi_diem_lam_them != "Trước ca" and don_lam_them.lam_ngoai_ca_den:
                        lam_ngoai_ca_den = self._convert_time_to_datetime(ngay, don_lam_them.lam_ngoai_ca_den)
                        so_phut_ve_som = max(0, int((lam_ngoai_ca_den - record.cham_ra_ca).total_seconds() // 60))
                        record.trang_thai_ra_ca = "Về sớm" if so_phut_ve_som > 0 else "Đúng giờ"
                        record.so_phut_ve_som_cuoi_ca = so_phut_ve_som

                record.trang_thai_ra_ca = "Về sớm" if so_phut_ve_som > 0 else "Đúng giờ"
                record.so_phut_ve_som_cuoi_ca = so_phut_ve_som

    @api.onchange('cham_vao_ca')
    def _onchange_cham_vao_ca(self):
        self._compute_vao_ca()
        self._compute_ket_qua_cham_cong()

    @api.onchange('cham_ra_giua_ca')
    def _onchange_cham_ra_giua_ca(self):
        self._compute_ra_giua_ca()
        self._compute_ket_qua_cham_cong()

    @api.onchange('cham_vao_giua_ca')
    def _onchange_cham_vao_giua_ca(self):
        self._compute_vao_giua_ca()
        self._compute_ket_qua_cham_cong()

    @api.onchange('cham_ra_ca')
    def _onchange_cham_ra_ca(self):
        self._compute_ra_ca()
        self._compute_ket_qua_cham_cong()
    
    @api.depends(
        'so_phut_di_muon_dau_ca', 'so_phut_ve_som_giua_ca', 'so_phut_di_muon_giua_ca', 'so_phut_ve_som_cuoi_ca',
        'trang_thai_vao_ca', 'trang_thai_ra_ca', 'trang_thai_vao_giua_ca', 'trang_thai_ra_giua_ca',
        'cham_vao_ca', 'cham_ra_ca', 'ca_lam_id', 'don_dang_ky_lam_them_gio_id', 'don_xin_nghi_id', 'don_xin_di_muon_ve_som_id'
    )
    def _compute_ket_qua_cham_cong(self):
        for record in self:
            ngay = record.ngay_cham_cong
            gio_ra_ca = self._convert_time_to_datetime(ngay, record.ca_lam_id.gio_ra_ca)
            gio_vao_ca = self._convert_time_to_datetime(ngay, record.ca_lam_id.gio_vao_ca)

            record.so_phut_di_muon = record.so_phut_di_muon_dau_ca + record.so_phut_di_muon_giua_ca
            record.so_phut_ve_som = record.so_phut_ve_som_giua_ca + record.so_phut_ve_som_cuoi_ca

            thoi_gian_lam_them = 0
            thoi_gian_lam = record.ca_lam_id.tong_thoi_gian - (record.so_phut_di_muon + record.so_phut_ve_som) / 60

            if record.don_xin_nghi_id:
                if record.don_xin_nghi_id.loai_nghi in ["Nghỉ không lương", "Nghỉ hưởng chế độ BHXH"]:
                    if record.don_xin_nghi_id.nghi_nua_ngay == False:
                        record.so_gio_cong = 0
                        record.tong_gio_lam = 0
                        record.so_gio_lam_them = 0
                        continue
                    else:
                        record.so_gio_lam_them = 0
                        record.tong_gio_lam = record.ca_lam_id.tong_thoi_gian / 2 - (record.so_phut_di_muon + record.so_phut_ve_som) / 60
                        record.so_gio_cong = record.tong_gio_lam
                        continue
                
                else:
                    if record.don_xin_nghi_id.nghi_nua_ngay:
                        record.so_gio_lam_them = 0
                        record.tong_gio_lam = record.ca_lam_id.tong_thoi_gian / 2 - (record.so_phut_di_muon + record.so_phut_ve_som) / 60
                        record.so_gio_cong = record.tong_gio_lam + record.ca_lam_id.tong_thoi_gian / 2
                        continue
                    else: 
                        record.so_gio_cong = record.ca_lam_id.tong_thoi_gian
                        record.so_gio_lam_them = 0
                        record.tong_gio_lam = 0
                        continue
            
            if record.trang_thai_cham_cong not in ["Chưa chấm công đủ", "Nghỉ không phép"]:
                don_lam_them = record.don_dang_ky_lam_them_gio_id
                ngay = record.ngay_cham_cong
                lam_ngoai_ca_tu = self._convert_time_to_datetime(ngay, don_lam_them.lam_ngoai_ca_tu)
                lam_ngoai_ca_den = self._convert_time_to_datetime(ngay, don_lam_them.lam_ngoai_ca_den)
                
                if don_lam_them.thoi_diem_lam_them == "Trước ca":
                    thoi_gian_lam_them = max((gio_vao_ca - max(record.cham_vao_ca, lam_ngoai_ca_tu)).total_seconds() / 3600, 0)
                    
                elif don_lam_them.thoi_diem_lam_them == "Sau ca":
                    thoi_gian_lam_them = max((min(record.cham_ra_ca, lam_ngoai_ca_den) - gio_ra_ca).total_seconds() / 3600, 0)
                
                elif don_lam_them.thoi_diem_lam_them in ["Ngày nghỉ", "Ngày lễ"]:
                    if don_lam_them.lam_ngoai_ca_tu == record.ca_lam_id.gio_ra_ca:
                        thoi_gian_lam_them = max((min(record.cham_ra_ca, lam_ngoai_ca_den) - gio_ra_ca).total_seconds() / 3600, 0)

                    elif don_lam_them.lam_ngoai_ca_den == record.ca_lam_id.gio_vao_ca:
                        thoi_gian_lam_them = max((gio_vao_ca - max(record.cham_vao_ca, lam_ngoai_ca_tu)).total_seconds() / 3600, 0)

                record.so_gio_lam_them = thoi_gian_lam_them    
                
                if don_lam_them.loai_ngay == "Ngày làm việc":
                    record.so_gio_cong = thoi_gian_lam + thoi_gian_lam_them * 1.5
                elif don_lam_them.loai_ngay == "Ngày nghỉ":
                    record.so_gio_cong = (thoi_gian_lam + thoi_gian_lam_them) * 2
                elif don_lam_them.loai_ngay == "Ngày lễ":
                    record.so_gio_cong = (thoi_gian_lam + thoi_gian_lam_them) * 3
                    if record.ngay_cham_cong.weekday() == 6:  # Nếu ngày lễ trùng với Chủ nhật
                        record.so_gio_cong = (thoi_gian_lam + thoi_gian_lam_them) * 4

            if record.trang_thai_cham_cong not in ["Chưa chấm công đủ", "Nghỉ không phép"]:
                record.tong_gio_lam = thoi_gian_lam
            else:
                record.tong_gio_lam = 0

    @api.depends('trang_thai_vao_ca', 'trang_thai_ra_ca', 'trang_thai_vao_giua_ca', 'trang_thai_ra_giua_ca', 'nghi_giua_ca')
    def _compute_trang_thai_cham_cong(self):
        for record in self:
            
            trang_thai = "Đúng giờ"

            if record.ngay_cham_cong and record.ngay_cham_cong < date.today():
                # Trường hợp không nghỉ giữa ca, nhưng chưa chấm vào/ra => Nghỉ không phép
                if not record.nghi_giua_ca and record.trang_thai_vao_ca == "Chưa chấm vào" and record.trang_thai_ra_ca == "Chưa chấm ra":
                    record.trang_thai_cham_cong = "Nghỉ không phép"
                    continue

                # Trường hợp có nghỉ giữa ca, nhưng tất cả các trạng thái vào/ra đều chưa chấm => Nghỉ không phép
                if (
                    record.nghi_giua_ca and
                    all(trang_thai == "Chưa chấm vào" for trang_thai in [record.trang_thai_vao_ca, record.trang_thai_vao_giua_ca]) and
                    all(trang_thai == "Chưa chấm ra" for trang_thai in [record.trang_thai_ra_ca, record.trang_thai_ra_giua_ca])
                ):
                    record.trang_thai_cham_cong = "Nghỉ không phép"
                    continue
                
            if any(trang_thai == "Nghỉ" for trang_thai in [record.trang_thai_vao_ca, record.trang_thai_ra_ca, record.trang_thai_vao_giua_ca, record.trang_thai_ra_giua_ca]):
                record.trang_thai_cham_cong = "Nghỉ"
                continue

            if  record.trang_thai_vao_ca == "Chưa chấm vào" or record.trang_thai_ra_ca == "Chưa chấm ra":
                record.trang_thai_cham_cong = "Chưa chấm công đủ"
                continue

            if record.nghi_giua_ca and (record.trang_thai_vao_giua_ca == "Chưa chấm vào" or record.trang_thai_ra_giua_ca == "Chưa chấm ra"):
                record.trang_thai_cham_cong = "Chưa chấm công đủ"
                continue
            
            so_lan_di_muon = sum(trang_thai == "Đi muộn" for trang_thai in [record.trang_thai_vao_ca, record.trang_thai_vao_giua_ca])
            so_lan_ve_som = sum(trang_thai == "Về sớm" for trang_thai in [record.trang_thai_ra_ca, record.trang_thai_ra_giua_ca])

            if so_lan_di_muon > 0 and so_lan_ve_som > 0:
                trang_thai = "Đi muộn về sớm"
            elif so_lan_di_muon > 0:
                trang_thai = "Đi muộn"
            elif so_lan_ve_som > 0:
                trang_thai = "Về sớm"

            record.trang_thai_cham_cong = trang_thai
                
    def action_chot_cong(self):
        for record in self:
            if record.trang_thai_cham_cong == "Chưa chấm công đủ" and record.trang_thai == 'Chưa chốt công':
                raise ValidationError("Chưa chấm công đủ!")

            ngay = record.ngay_cham_cong
            nam = str(ngay.year)
            thang = str(ngay.month)
            ngay_str = str(ngay.day)
            tuan = ngay.isocalendar()[1]

            tong_hop = self.env['tong_hop_cham_cong'].search([
                ('nhan_vien_id', '=', record.nhan_vien_id.id),
                ('nam', '=', nam),
                ('thang', '=', thang),
                ('ngay', '=', ngay_str)
            ], limit=1)

            if tong_hop:
                tong_hop.write({
                    'so_lan_di_muon': tong_hop.so_lan_di_muon + (1 if record.trang_thai_cham_cong == "Đi muộn" else 0),
                    'so_lan_ve_som': tong_hop.so_lan_ve_som + (1 if record.trang_thai_cham_cong == "Về sớm" else 0),
                    'so_lan_nghi': tong_hop.so_lan_nghi + (1 if record.trang_thai_cham_cong == "Nghỉ không phép" else 0),
                    'trang_thai_cham_cong': record.trang_thai_cham_cong,
                })
            else:
                self.env['tong_hop_cham_cong'].create({
                    'nhan_vien_id': record.nhan_vien_id.id,
                    'nam': nam,
                    'thang': thang,
                    'ngay': ngay_str,
                    'tuan': tuan,
                    'so_lan_di_muon': 1 if record.trang_thai_cham_cong == "Đi muộn" else 0,
                    'so_lan_ve_som': 1 if record.trang_thai_cham_cong == "Về sớm" else 0,
                    'so_lan_nghi': 1 if record.trang_thai_cham_cong == "Nghỉ không phép" else 0,
                    'trang_thai_cham_cong': record.trang_thai_cham_cong,
                })

            record.write({'trang_thai': 'Đã chốt công'})

    def action_huy(self):
        """ Hủy chốt công: Xóa dữ liệu trong `tong_hop_cham_cong` """
        for record in self:
            if record.trang_thai == 'Đã chốt công':
                ngay = record.ngay_cham_cong
                nam = str(ngay.year)
                thang = str(ngay.month)
                ngay_str = str(ngay.day)

                tong_hop = self.env['tong_hop_cham_cong'].search([
                    ('nhan_vien_id', '=', record.nhan_vien_id.id),
                    ('nam', '=', nam),
                    ('thang', '=', thang),
                    ('ngay', '=', ngay_str)
                ], limit=1)

                if tong_hop:
                    tong_hop.unlink()

                record.write({'trang_thai': 'Chưa chốt công'})

    def write(self, vals):
        for record in self:
            if record.trang_thai != 'Chưa chốt công':
                allowed_fields = {'trang_thai'}
                if any(field not in allowed_fields for field in vals.keys()):
                    raise ValidationError("Chỉ có thể cập nhật khi chưa chốt công!")

            if 'nhan_vien_id' in vals:
                raise ValidationError("Không thể chỉnh sửa nhân viên sau khi chấm công!")

            if 'ngay_cham_cong' in vals:
                raise ValidationError("Không thể chỉnh sửa ngày chấm công sau khi chấm công!")
            
        return super(ChamCongChiTiet, self).write(vals)