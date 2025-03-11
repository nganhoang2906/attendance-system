from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import date, datetime
import calendar

class DotDangKyCaLam(models.Model):
    _name = 'dot_dang_ky_ca_lam'
    _description = "Bảng chứa thông tin đợt đăng ký"
    _rec_name = 'ten_dot'
    _order = 'ten_dot desc'
    _sql_constraints = [
        ('unique_ma_dot', 'unique(ma_dot)', 'Đã tồn tại mã đợt!'),
        ('unique_nam_thang', 'unique(nam_dang_ky, thang_dang_ky)', 'Đã tồn tại đợt đăng ký của tháng này!')
    ]

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
    
    @api.constrains('nam_dang_ky')
    def _check_nam_dang_ky(self):
        for record in self:
            if not record.nam_dang_ky.isdigit() or int(record.nam_dang_ky) < 2000 or int(record.nam_dang_ky) > datetime.today().year + 10:
                raise ValidationError("Năm không hợp lệ. Vui lòng nhập năm từ 2000 trở đi và trong vòng 10 năm tới.")
    
    @api.depends('thang_dang_ky', 'nam_dang_ky')
    def _compute_ten_dot(self):
        for record in self:
            if record.thang_dang_ky and record.nam_dang_ky:
                record.ten_dot = f"Tháng {record.thang_dang_ky}/{record.nam_dang_ky}"
            else:
                record.ten_dot = False
    
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
                            
    @api.constrains('han_dang_ky', 'ngay_bat_dau')
    def _check_han_dang_ky(self):
        for record in self:
            if record.han_dang_ky and record.ngay_bat_dau:
                if record.han_dang_ky >= record.ngay_bat_dau:
                    raise ValidationError("Hạn đăng ký phải trước ngày bắt đầu đợt đăng ký!")
                  
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
    
    
    
    