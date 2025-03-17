from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import timedelta

class DonDangKyLamThemGio(models.Model):
    _name = 'don_dang_ky_lam_them_gio'
    _description = 'Đơn đăng ký làm thêm giờ'
    _rec_name = 'nhan_vien_id'
    _order = 'ngay_ap_dung desc'
    
    GIO_SELECTION = [
        (f"{h:02}:{m:02}", f"{h:02}:{m:02}") for h in range(24) for m in (0, 30)
    ]
    
    nhan_vien_id = fields.Many2one('nhan_vien', string="Nhân viên", required=True)
    ngay_lam_don = fields.Date("Ngày làm đơn", required=True, default=fields.Date.today)
    ngay_ap_dung = fields.Date("Ngày áp dụng", required=True)
    loai_ngay = fields.Selection(
        [
            ('Ngày làm việc', 'Ngày làm việc'),
            ('Ngày nghỉ', 'Ngày nghỉ'),
            ('Ngày lễ', 'Ngày lễ')
        ],
        string="Loại ngày", compute="_compute_loai_ngay", store=True
    )
    ca_lam_id = fields.Many2one('ca_lam', string="Ca làm", compute='_compute_ca_lam', store=True)
    thoi_diem_lam_them = fields.Selection(
        [
            ('Trước ca', 'Trước ca'),
            ('Sau ca', 'Sau ca'),
            ('Ngày nghỉ', 'Ngày nghỉ'),
            ('Ngày lễ', 'Ngày lễ')
        ],
        string="Thời điểm làm thêm", required=True
    )
    lam_ngoai_ca_tu = fields.Selection(selection=GIO_SELECTION, string="Làm ngoài ca từ", required=True)
    lam_ngoai_ca_den = fields.Selection(selection=GIO_SELECTION, string="Làm ngoài ca đến", required=True)
    tong_thoi_gian_lam_them = fields.Float(string="Tổng thời gian làm thêm (giờ)", compute="_compute_tong_thoi_gian_lam_them", store=True)
    trang_thai = fields.Selection(
        [
            ('Chờ duyệt', "Chờ duyệt"), 
            ('Đã duyệt', "Đã duyệt"), 
            ('Đã từ chối', "Đã từ chối"), 
            ('Đã hủy', "Đã hủy")
        ],
        string="Trạng thái", default="Chờ duyệt", required=True
    )
    
    @api.constrains('ngay_lam_don', 'ngay_ap_dung')
    def _check_ngay_lam_don(self):
        for record in self:
            if record.ngay_lam_don and record.ngay_ap_dung:
                if record.ngay_lam_don > record.ngay_ap_dung + timedelta(days=3):
                    raise ValidationError("Ngày làm đơn không được sau quá 3 ngày từ ngày áp dụng!")
    
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
                don_dang_ky_lam_them_gio = self.env['don_dang_ky_lam_them_gio'].search([
                    ('id', '!=', record.id),
                    ('nhan_vien_id', '=', record.nhan_vien_id.id),
                    ('trang_thai', '=', 'Đã duyệt'),
                    ('ngay_ap_dung', '=', record.ngay_ap_dung),
                ])
                if don_dang_ky_lam_them_gio:
                    raise ValidationError("Nhân viên đã có đơn đăng ký làm thêm giờ vào ngày này!") 
            
    @api.depends('ngay_ap_dung')
    def _compute_loai_ngay(self):
        for record in self:
            if not record.ngay_ap_dung:
                record.loai_ngay = False
                continue
            
            ngay_le = self.env['lich_nghi_le'].search([
                ('ngay_bat_dau', '<=', record.ngay_ap_dung),
                ('ngay_ket_thuc', '>=', record.ngay_ap_dung)
            ], limit=1)

            if ngay_le:
                record.loai_ngay = 'Ngày lễ'
            elif record.ngay_ap_dung.weekday() == 6:
                record.loai_ngay = 'Ngày nghỉ'
            else:
                record.loai_ngay = 'Ngày làm việc'

    @api.depends('nhan_vien_id', 'ngay_ap_dung', 'loai_ngay')
    def _compute_ca_lam(self):
        for record in self:
            if record.loai_ngay == 'Ngày làm việc':
                dang_ky_ca_lam = self.env['dang_ky_ca_lam'].search([
                    ('nhan_vien_id', '=', record.nhan_vien_id.id),
                    ('ngay_dang_ky', '=', record.ngay_ap_dung),
                    ('trang_thai', '=', 'Đã duyệt')
                ], limit=1)

                record.ca_lam_id = dang_ky_ca_lam.ca_lam_id if dang_ky_ca_lam else False
            else:
                record.ca_lam_id = False

    @api.onchange('ngay_ap_dung')
    def _onchange_ngay_ap_dung(self):
        for record in self:
            record._compute_loai_ngay()
            record._compute_ca_lam()

    @api.onchange('loai_ngay', 'ca_lam_id')
    def _check_dang_ky_ca_lam(self):
        for record in self:
            if record.loai_ngay == 'Ngày làm việc' and not record.ca_lam_id:
                raise ValidationError("Nhân viên chưa đăng ký ca làm!")
    
    @api.constrains('loai_ngay', 'thoi_diem_lam_them')
    def _check_thoi_diem_lam_them(self):
        for record in self:
            if record.loai_ngay == 'Ngày làm việc' and record.thoi_diem_lam_them not in ['Trước ca', 'Sau ca']:
                raise ValidationError("Nếu là 'Ngày làm việc', chỉ được chọn 'Trước ca' hoặc 'Sau ca' cho thời điểm làm thêm!")
            
            if record.loai_ngay == 'Ngày nghỉ' and record.thoi_diem_lam_them != 'Ngày nghỉ':
                raise ValidationError("Nếu là 'Ngày nghỉ', chỉ được chọn 'Ngày nghỉ' cho thời điểm làm thêm!")
            
            if record.loai_ngay == 'Ngày lễ' and record.thoi_diem_lam_them != 'Ngày lễ':
                raise ValidationError("Nếu là 'Ngày lễ', chỉ được chọn 'Ngày lễ' cho thời điểm làm thêm!")

    @api.constrains('lam_ngoai_ca_tu', 'lam_ngoai_ca_den', 'ca_lam_id')
    def _check_lam_ngoai_ca(self):
        for record in self:
            if not record.ca_lam_id:
                raise ValidationError("Chưa có ca làm!")

            gio_vao = record.ca_lam_id.gio_vao
            gio_ra = record.ca_lam_id.gio_ra

            if record.lam_ngoai_ca_tu and record.lam_ngoai_ca_den:
                if record.lam_ngoai_ca_tu >= record.lam_ngoai_ca_den:
                    raise ValidationError("Thời gian bắt đầu làm ngoài ca phải trước thời gian kết thúc làm ngoài ca!")

                if not (record.lam_ngoai_ca_den == gio_vao or record.lam_ngoai_ca_tu == gio_ra):
                    raise ValidationError("Thời gian làm thêm phải ngay trước hoặc ngay sau ca làm!")
        
    @api.depends('thoi_diem_lam_them', 'lam_ngoai_ca_tu', 'lam_ngoai_ca_den', 'ca_lam_id', 'loai_ngay')
    def _compute_tong_thoi_gian_lam_them(self):
        for record in self:
            if record.thoi_diem_lam_them == 'Sau ca' and record.ca_lam_id:
                record.lam_ngoai_ca_tu = record.ca_lam_id.gio_ra
            
            elif record.thoi_diem_lam_them == 'Trước ca' and record.ca_lam_id:
                record.lam_ngoai_ca_den = record.ca_lam_id.gio_vao
            
            if record.lam_ngoai_ca_tu and record.lam_ngoai_ca_den:
                gio_bd = int(record.lam_ngoai_ca_tu[:2]) + int(record.lam_ngoai_ca_tu[3:]) / 60
                gio_kt = int(record.lam_ngoai_ca_den[:2]) + int(record.lam_ngoai_ca_den[3:]) / 60
                
                if gio_kt > gio_bd:
                    thoi_gian_lam_them = gio_kt - gio_bd
                else:
                    thoi_gian_lam_them = 0

                if record.loai_ngay in ['Ngày nghỉ', 'Ngày lễ'] and record.ca_lam_id:
                    thoi_gian_lam_them += record.ca_lam_id.tong_thoi_gian

                record.tong_thoi_gian_lam_them = thoi_gian_lam_them
    
    @api.constrains('tong_thoi_gian_lam_them', 'ca_lam_id', 'loai_ngay')
    def _check_tong_thoi_gian_lam_them(self):
        for record in self:
            if record.tong_thoi_gian_lam_them < 0.5:
                raise ValidationError("Phải làm thêm tối thiểu 0.5 giờ!")

            if record.ca_lam_id and record.loai_ngay == 'Ngày làm việc' and record.tong_thoi_gian_lam_them > (record.ca_lam_id.tong_thoi_gian / 2):
                raise ValidationError("Không thể làm thêm quá 50% thời gian ca làm!")

            if record.loai_ngay in ['Ngày nghỉ', 'Ngày lễ'] and record.tong_thoi_gian_lam_them > 12:
                raise ValidationError("Không thể làm thêm quá 12 giờ trong ngày nghỉ/lễ!")

    def action_duyet(self):
        for record in self:
            if record.trang_thai in ['Chờ duyệt', 'Đã hủy']:
                record.write({'trang_thai': 'Đã duyệt'})

    def action_tu_choi(self):
        for record in self:
            if record.trang_thai == 'Chờ duyệt':
                record.write({'trang_thai': 'Đã từ chối'})

    def action_huy(self):
        for record in self:
            if record.trang_thai == 'Đã duyệt':
                record.write({'trang_thai': 'Đã hủy'})