from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta
from pytz import timezone, UTC

class ChamCongChiTiet(models.Model):
    _name = 'cham_cong_chi_tiet'
    _description = 'Chấm công chi tiết'
    _rec_name = 'nhan_vien_id'
    _order = 'ngay_cham_cong desc'

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
    
    trang_thai_vao_ca = fields.Selection([('Đúng giờ', "Đúng giờ"), ('Đi muộn', "Đi muộn"), ('Chưa chấm vào', "Chưa chấm vào")], string="Trạng thái vào ca", compute="_compute_vao_ca", store=True)
    trang_thai_ra_giua_ca = fields.Selection([('Đúng giờ', "Đúng giờ"), ('Về sớm', "Về sớm"), ('Chưa chấm ra', "Chưa chấm ra")], string="Trạng thái ra giữa ca", compute="_compute_ra_giua_ca", store=True)
    trang_thai_vao_giua_ca = fields.Selection([('Đúng giờ', "Đúng giờ"), ('Đi muộn', "Đi muộn"), ('Chưa chấm vào', "Chưa chấm vào")], string="Trạng thái vào giữa ca", compute="_compute_vao_giua_ca", store=True)
    trang_thai_ra_ca = fields.Selection([('Đúng giờ', "Đúng giờ"), ('Về sớm', "Về sớm"), ('Chưa chấm ra', "Chưa chấm ra")], string="Trạng thái ra ca", compute="_compute_ra_ca", store=True)
    
    trang_thai_cham_cong = fields.Selection([
        ('Đúng giờ', "Đúng giờ"),
        ('Đi muộn', "Đi muộn"),
        ('Về sớm', "Về sớm"),
        ('Đi muộn về sớm', "Đi muộn về sớm"),
        ('Chưa chấm công đủ', "Chưa chấm công đủ"),
        ('Nghỉ', "Nghỉ"),
    ], string="Trạng thái chấm công", store=True)

    so_phut_di_muon = fields.Integer(string="Số phút đi muộn")
    so_phut_ve_som = fields.Integer(string="Số phút về sớm")
    so_gio_lam_them = fields.Float(string="Số giờ làm thêm")
    tong_gio_lam = fields.Float(string="Tổng giờ làm")
    so_gio_cong = fields.Float(string="Số giờ công")

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
                if ngay and ngay.date() != record.ngay_cham_cong:
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
    
    @api.depends('cham_vao_ca', 'ca_lam_id.gio_vao_ca')
    def _compute_vao_ca(self):
        for record in self:
            if not record.ca_lam_id:
                record.trang_thai_vao_ca = "Chưa chấm vào"
                record.so_phut_di_muon_dau_ca = 0
                continue
            
            ngay = record.ngay_cham_cong
            gio_vao_ca = self._convert_time_to_datetime(ngay, record.ca_lam_id.gio_vao_ca)
            if not record.cham_vao_ca:
                record.trang_thai_vao_ca = "Chưa chấm vào"
                record.so_phut_di_muon_dau_ca = 0
            else:
                so_phut_di_muon = max(0, int((record.cham_vao_ca - gio_vao_ca).total_seconds() // 60))
                record.trang_thai_vao_ca = "Đi muộn" if so_phut_di_muon > 0 else "Đúng giờ"
                record.so_phut_di_muon_dau_ca = so_phut_di_muon

    @api.depends('cham_ra_giua_ca', 'ca_lam_id.gio_bat_dau_nghi_giua_ca')
    def _compute_ra_giua_ca(self):
        for record in self:
            if not record.ca_lam_id:
                record.trang_thai_ra_giua_ca = "Chưa chấm ra"
                record.so_phut_ve_som_giua_ca = 0
                continue
            
            ngay = record.ngay_cham_cong
            gio_bat_dau_nghi = self._convert_time_to_datetime(ngay, record.ca_lam_id.gio_bat_dau_nghi_giua_ca)

            if not record.cham_ra_giua_ca:
                record.trang_thai_ra_giua_ca = "Chưa chấm ra"
                record.so_phut_ve_som_giua_ca = 0
            else:
                so_phut_ve_som = max(0, int((gio_bat_dau_nghi - record.cham_ra_giua_ca).total_seconds() // 60))
                record.trang_thai_ra_giua_ca = "Về sớm" if so_phut_ve_som > 0 else "Đúng giờ"
                record.so_phut_ve_som_giua_ca = so_phut_ve_som

    @api.depends('cham_vao_giua_ca', 'ca_lam_id.gio_ket_thuc_nghi_giua_ca')
    def _compute_vao_giua_ca(self):
        for record in self:
            if not record.ca_lam_id:
                record.trang_thai_vao_giua_ca = "Chưa chấm vào"
                record.so_phut_di_muon_giua_ca = 0
                continue

            ngay = record.ngay_cham_cong
            gio_ket_thuc_nghi = self._convert_time_to_datetime(ngay, record.ca_lam_id.gio_ket_thuc_nghi_giua_ca)

            if not record.cham_vao_giua_ca:
                record.trang_thai_vao_giua_ca = "Chưa chấm vào"
                record.so_phut_di_muon_giua_ca = 0
            else:
                so_phut_di_muon = max(0, int((record.cham_vao_giua_ca - gio_ket_thuc_nghi).total_seconds() // 60))
                record.trang_thai_vao_giua_ca = "Đi muộn" if so_phut_di_muon > 0 else "Đúng giờ"
                record.so_phut_di_muon_giua_ca = so_phut_di_muon

    @api.depends('cham_ra_ca', 'ca_lam_id.gio_ra_ca')
    def _compute_ra_ca(self):
        for record in self:
            if not record.ca_lam_id:
                record.trang_thai_ra_ca = "Chưa chấm ra"
                record.so_phut_ve_som_cuoi_ca = 0
                continue

            ngay = record.ngay_cham_cong
            gio_ra_ca = self._convert_time_to_datetime(ngay, record.ca_lam_id.gio_ra_ca)

            if not record.cham_ra_ca:
                record.trang_thai_ra_ca = "Chưa chấm ra"
                record.so_phut_ve_som_cuoi_ca = 0
            else:
                so_phut_ve_som = max(0, int((gio_ra_ca - record.cham_ra_ca).total_seconds() // 60))
                record.trang_thai_ra_ca = "Về sớm" if so_phut_ve_som > 0 else "Đúng giờ"
                record.so_phut_ve_som_cuoi_ca = so_phut_ve_som

    @api.onchange('cham_vao_ca')
    def _onchange_cham_vao_ca(self):
        self._compute_vao_ca()

    @api.onchange('cham_ra_giua_ca')
    def _onchange_cham_ra_giua_ca(self):
        self._compute_ra_giua_ca()

    @api.onchange('cham_vao_giua_ca')
    def _onchange_cham_vao_giua_ca(self):
        self._compute_vao_giua_ca()

    @api.onchange('cham_ra_ca')
    def _onchange_cham_ra_ca(self):
        self._compute_ra_ca()
