from odoo import models, fields, api
from odoo.exceptions import ValidationError

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
    
    trang_thai_vao_ca = fields.Selection([('Đúng giờ', "Đúng giờ"), ('Đi muộn', "Đi muộn"), ('Chưa chấm vào', "Chưa chấm vào")], string="Trạng thái vào ca", store=True)
    so_phut_di_muon_dau_ca = fields.Integer(string="Số phút đi muộn đầu ca")
    
    trang_thai_ra_giua_ca = fields.Selection([('Đúng giờ', "Đúng giờ"), ('Về sớm', "Về sớm"), ('Chưa chấm ra', "Chưa chấm ra")], string="Trạng thái ra giữa ca", store=True)
    so_phut_ve_som_giua_ca = fields.Integer(string="Số phút về sớm giữa ca")
    
    trang_thai_vao_giua_ca = fields.Selection([('Đúng giờ', "Đúng giờ"), ('Đi muộn', "Đi muộn"), ('Chưa chấm vào', "Chưa chấm vào")], string="Trạng thái vào giữa ca", store=True)
    so_phut_di_muon_giua_ca = fields.Integer(string="Số phút đi muộn giữa ca")
    
    trang_thai_ra_ca = fields.Selection([('Đúng giờ', "Đúng giờ"), ('Về sớm', "Về sớm"), ('Chưa chấm ra', "Chưa chấm ra")], string="Trạng thái ra ca", store=True)
    so_phut_ve_som_cuoi_ca = fields.Integer(string="Số phút về sớm cuối ca")

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