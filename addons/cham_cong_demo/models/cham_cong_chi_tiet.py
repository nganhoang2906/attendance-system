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
        string="Trạng thái", compute="_compute_ngay_lam_viec", store=True
    )
    ca_lam_id = fields.Many2one('ca_lam', string="Ca làm", compute="_compute_ca_lam_id", store=True)

    gio_vao = fields.Selection(related='ca_lam_id.gio_vao', string="Giờ vào", store=True)
    gio_ra = fields.Selection(related='ca_lam_id.gio_ra', string="Giờ ra", store=True)
    nghi_giua_gio = fields.Boolean(related='ca_lam_id.nghi_giua_gio', string="Nghỉ giữa giờ", store=True)
    gio_bat_dau_nghi_giua_gio = fields.Selection(related='ca_lam_id.gio_bat_dau_nghi_giua_gio', string="Giờ bắt đầu nghỉ giữa giờ", store=True)
    gio_ket_thuc_nghi_giua_gio = fields.Selection(related='ca_lam_id.gio_ket_thuc_nghi_giua_gio', string="Giờ kết thúc nghỉ giữa giờ", store=True)

    cham_vao = fields.Float(string="Chấm vào", widget="float_time")
    cham_ra_giua_gio = fields.Char(string="Chấm ra giữa giờ")
    cham_vao_giua_gio = fields.Char(string="Chấm vào giữa giờ")
    cham_ra = fields.Float(string="Chấm ra", widget="float_time")

    so_phut_di_muon = fields.Integer(string="Số phút đi muộn")
    so_phut_ve_som = fields.Integer(string="Số phút về sớm")
    so_gio_lam_them = fields.Float(string="Số giờ làm thêm")
    tong_gio_lam = fields.Float(string="Tổng giờ làm")
    so_gio_cong = fields.Float(string="Số giờ công")

    trang_thai = fields.Selection(
        [
            ('Chờ duyệt', "Chờ duyệt"),
            ('Đã duyệt', "Đã duyệt"),
            ('Đã từ chối', "Đã từ chối"),
            ('Đã hủy', "Đã hủy")
        ],
        string="Trạng thái", default="Chờ duyệt", required=True
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
                raise ValidationError(f"Nhân viên không làm việc vào ngày {record.ngay_cham_cong.strftime('%d/%m/%Y')}. Vui lòng kiểm tra lại!")
    
    @api.constrains('cham_vao', 'cham_ra')
    def _check_valid_time(self):
        for record in self:
            if not (0 <= record.cham_vao < 24):
                raise ValidationError("Thời gian chấm vào phải trong khoảng 00:00 - 23:59!")
            if not (0 <= record.cham_ra < 24):
                raise ValidationError("Thời gian chấm ra phải trong khoảng 00:00 - 23:59!")