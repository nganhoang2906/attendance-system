from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import timedelta
import math

class DonXinDiMuonVeSom(models.Model):
    _name = 'don_xin_di_muon_ve_som'
    _description = "Đơn xin đi muộn về sớm"
    _rec_name = "nhan_vien_id"
    _order = 'ngay_ap_dung desc'

    nhan_vien_id = fields.Many2one('nhan_vien', string="Nhân viên", required=True)
    ngay_lam_don = fields.Date("Ngày làm đơn", required=True, default=fields.Date.today)
    ngay_ap_dung = fields.Date("Ngày áp dụng", required=True, default=fields.Date.today)
    ca_lam_id = fields.Many2one('ca_lam', string="Ca làm", readonly=True, compute="_compute_ca_lam", store=True)
    nghi_giua_ca = fields.Boolean(related='ca_lam_id.nghi_giua_ca', string="Nghỉ giữa ca", store=True)
    so_phut_xin_di_muon_dau_ca = fields.Integer("Đi muộn đầu ca (phút)", default=0)
    so_phut_xin_ve_som_giua_ca = fields.Integer("Về sớm giữa ca (phút)", default=0)
    so_phut_xin_di_muon_giua_ca = fields.Integer("Đi muộn giữa ca (phút)", default=0)
    so_phut_xin_ve_som_cuoi_ca = fields.Integer("Về sớm cuối ca (phút)", default=0)
    tong_thoi_gian_xin = fields.Float("Tổng thời gian xin (giờ)", compute="_compute_tong_thoi_gian_xin", store=True)
    ly_do = fields.Text("Lý do")
    giay_to = fields.Binary("Giấy tờ đính kèm")
    giay_to_filename = fields.Char("Tên file")
    trang_thai = fields.Selection(
        [
            ('Chờ duyệt', "Chờ duyệt"), 
            ('Đã duyệt', "Đã duyệt"), 
            ('Đã từ chối', "Đã từ chối"), 
            ('Đã hủy', "Đã hủy")
        ],
        string="Trạng thái", default="Chờ duyệt", required=True
    )

    @api.depends('nhan_vien_id', 'ngay_ap_dung')
    def _compute_ca_lam(self):
        for record in self:
            if record.nhan_vien_id and record.ngay_ap_dung:
                dkcl = self.env['dang_ky_ca_lam'].search([
                    ('nhan_vien_id', '=', record.nhan_vien_id.id),
                    ('ngay_dang_ky', '=', record.ngay_ap_dung),
                    ('trang_thai', '=', 'Đã duyệt')
                ], limit=1)

                record.ca_lam_id = dkcl.ca_lam_id if dkcl else False

    @api.constrains('ngay_lam_don', 'ngay_ap_dung')
    def _check_ngay_lam_don(self):
        for record in self:
            if record.ngay_lam_don and record.ngay_ap_dung:
                if record.ngay_lam_don > record.ngay_ap_dung + timedelta(days=3):
                    raise ValidationError("Ngày làm đơn không được sau quá 3 ngày từ ngày áp dụng!")
                
    @api.depends('so_phut_xin_di_muon_dau_ca', 'so_phut_xin_ve_som_giua_ca', 'so_phut_xin_di_muon_giua_ca', 'so_phut_xin_ve_som_cuoi_ca')
    def _compute_tong_thoi_gian_xin(self):
        for record in self:
            tong_phut = sum([
                max(record.so_phut_xin_di_muon_dau_ca, 0),
                max(record.so_phut_xin_ve_som_giua_ca, 0),
                max(record.so_phut_xin_di_muon_giua_ca, 0),
                max(record.so_phut_xin_ve_som_cuoi_ca, 0)
            ])
            record.tong_thoi_gian_xin = math.ceil(tong_phut / 60 * 100) / 100

    @api.onchange('ngay_ap_dung')
    def _onchange_ngay_ap_dung(self):
        for record in self:
            record.so_phut_xin_di_muon_dau_ca = 0
            record.so_phut_xin_ve_som_giua_ca = 0
            record.so_phut_xin_di_muon_giua_ca = 0
            record.so_phut_xin_ve_som_cuoi_ca = 0
    
    @api.constrains('so_phut_xin_di_muon_dau_ca', 'so_phut_xin_ve_som_giua_ca', 'so_phut_xin_di_muon_giua_ca', 'so_phut_xin_ve_som_cuoi_ca', 'tong_thoi_gian_xin')
    def _check_so_phut_hop_le(self):
        for record in self:
            so_phut_fields = [
                record.so_phut_xin_di_muon_dau_ca,
                record.so_phut_xin_ve_som_giua_ca,
                record.so_phut_xin_di_muon_giua_ca,
                record.so_phut_xin_ve_som_cuoi_ca
            ]

            for so_phut in so_phut_fields:
                if so_phut < 0:
                    raise ValidationError("Số phút đi muộn/về sớm không hợp lệ!")
                elif so_phut > 120:
                    raise ValidationError("Chỉ được đi muộn/về sớm tối đa 120 phút!")

            if not record.ca_lam_id:
                raise ValidationError("Nhân viên chưa đăng ký ca làm vào ngày này!")

            if record.tong_thoi_gian_xin <= 0:
                raise ValidationError("Chưa có thời gian xin đi muộn, về sớm!")
            
            gioi_han = record.ca_lam_id.tong_thoi_gian/4
            if record.tong_thoi_gian_xin > gioi_han:
                raise ValidationError(f"Tổng thời gian xin đi muộn, về sớm không được vượt quá {gioi_han} giờ!")

    @api.constrains('nhan_vien_id', 'ngay_ap_dung')
    def _check_ca_lam(self):
        for record in self:
            if not record.ca_lam_id:
                raise ValidationError("Nhân viên chưa đăng ký ca làm vào ngày này!")

    @api.constrains('ngay_ap_dung', 'nhan_vien_id')
    def _check_don_xin_nghi(self):
        for record in self:
            don_xin_nghi = self.env['don_xin_nghi'].search([
                ('nhan_vien_id', '=', record.nhan_vien_id.id),
                ('trang_thai', '=', 'Đã duyệt'),
                ('ngay_bat_dau_nghi', '<=', record.ngay_ap_dung),
                ('ngay_ket_thuc_nghi', '>=', record.ngay_ap_dung),
            ])
            if don_xin_nghi:
                raise ValidationError("Nhân viên đã có đơn xin nghỉ vào ngày này!")
    
    @api.constrains('ngay_ap_dung', 'nhan_vien_id', 'trang_thai')
    def _check_don_da_duyet(self):
        for record in self:
            if record.trang_thai == 'Đã duyệt':
                don_xin_di_muon_ve_som = self.env['don_xin_di_muon_ve_som'].search([
                    ('id', '!=', record.id),
                    ('nhan_vien_id', '=', record.nhan_vien_id.id),
                    ('trang_thai', '=', 'Đã duyệt'),
                    ('ngay_ap_dung', '=', record.ngay_ap_dung),
                ])
                if don_xin_di_muon_ve_som:
                    raise ValidationError("Nhân viên đã có đơn xin đi muộn về sớm vào ngày này!")        

    @api.constrains('nhan_vien_id', 'ngay_ap_dung')
    def _check_so_luong_don_trong_thang(self):
        for record in self:
            if record.nhan_vien_id and record.ngay_ap_dung:
                ngay_dau_thang = record.ngay_ap_dung.replace(day=1)
                ngay_cuoi_thang = (ngay_dau_thang + timedelta(days=32)).replace(day=1) - timedelta(days=1)

                so_don = self.env['don_xin_di_muon_ve_som'].search_count([
                    ('nhan_vien_id', '=', record.nhan_vien_id.id),
                    ('ngay_ap_dung', '>=', ngay_dau_thang),
                    ('ngay_ap_dung', '<=', ngay_cuoi_thang),
                    ('trang_thai', '=', 'Đã duyệt')
                ])

                if so_don > 3:
                    raise ValidationError(f"Nhân viên {record.nhan_vien_id.ho_va_ten} đã đạt giới hạn 3 đơn xin đi muộn về sớm trong tháng này!")
            
    def action_duyet(self):
        for record in self:
            if record.trang_thai in ['Chờ duyệt', 'Đã hủy']:
                ngay_dau_thang = record.ngay_ap_dung.replace(day=1)
                ngay_cuoi_thang = (ngay_dau_thang + timedelta(days=32)).replace(day=1) - timedelta(days=1)

                so_don = self.env['don_xin_di_muon_ve_som'].search_count([
                    ('nhan_vien_id', '=', record.nhan_vien_id.id),
                    ('ngay_ap_dung', '>=', ngay_dau_thang),
                    ('ngay_ap_dung', '<=', ngay_cuoi_thang),
                    ('trang_thai', '=', 'Đã duyệt')
                ])

                if so_don >= 3:
                    raise ValidationError(f"Nhân viên {record.nhan_vien_id.ho_va_ten} đã đạt giới hạn 3 đơn xin đi muộn về sớm trong tháng này!")
                
                record.write({'trang_thai': 'Đã duyệt'})

    def action_tu_choi(self):
        for record in self:
            if record.trang_thai == 'Chờ duyệt':
                record.write({'trang_thai': 'Đã từ chối'})

    def action_huy(self):
        for record in self:
            if record.trang_thai == 'Đã duyệt':
                record.write({'trang_thai': 'Đã hủy'})

    def write(self, vals):
        for record in self:
            if record.trang_thai != 'Chờ duyệt':
                allowed_fields = {'trang_thai'}
                if any(field not in allowed_fields for field in vals.keys()):
                    raise ValidationError("Chỉ có thể cập nhật khi đơn ở trạng thái 'Chờ duyệt'!")
            
            if 'nhan_vien_id' in vals:
                raise ValidationError("Không thể chỉnh sửa nhân viên sau khi tạo đơn!")

        return super(DonXinDiMuonVeSom, self).write(vals)