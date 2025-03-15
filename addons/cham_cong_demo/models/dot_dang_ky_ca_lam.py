from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import date, datetime, timedelta
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
    nam_dang_ky = fields.Selection(
        [(str(nam), f'Năm {nam}') for nam in range(datetime.today().year - 10, datetime.today().year + 10)],
        string="Năm đăng ký",
        required=True,
        default=str(datetime.today().year)
    )
    thang_dang_ky = fields.Selection(
        [(str(i), f'Tháng {i}') for i in range(1, 13)],
        string="Tháng đăng ký",
        required=True
    )
    ngay_bat_dau = fields.Date("Thời gian bắt đầu", compute='_compute_thoi_gian', store=True)
    ngay_ket_thuc = fields.Date("Thời gian kết thúc", compute='_compute_thoi_gian', store=True)
    nhan_vien_ids = fields.Many2many('nhan_vien', string="Nhân viên đăng ký", domain=[('trang_thai', '!=', 'Đã nghỉ việc')])
    han_dang_ky = fields.Date("Hạn đăng ký", required=True)
    trang_thai_dang_ky = fields.Selection(
        [
            ("Đang mở", "Đang mở"),
            ("Đã hết hạn", "Đã hết hạn")
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
    
    @api.constrains('nhan_vien_ids')
    def _check_nhan_vien(self):
        for record in self:
            for nhan_vien in record.nhan_vien_ids:
                if nhan_vien.trang_thai == 'Đã nghỉ việc':
                    raise ValidationError(f"Nhân viên {nhan_vien.name} đã nghỉ việc!")

    @api.model
    def default_get(self, fields_list):
        res = super(DotDangKyCaLam, self).default_get(fields_list)
        nhan_vien_dang_lam = self.env["nhan_vien"].search([("trang_thai", "!=", "Đã nghỉ việc")])
        res["nhan_vien_ids"] = [(6, 0, nhan_vien_dang_lam.ids)]
        return res

    @api.constrains('han_dang_ky', 'ngay_bat_dau')
    def _check_han_dang_ky(self):
        today = date.today()
        for record in self:
            if record.han_dang_ky and record.ngay_bat_dau:
                if record.han_dang_ky and today > record.han_dang_ky:
                    raise ValidationError("Đợt đăng ký đang tạo đã hết hạn đăng ký!")
                elif record.han_dang_ky >= record.ngay_bat_dau:
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
    
    def _get_ngay_le(self, ngay_bat_dau, ngay_ket_thuc):
        ngay_le_list = set()
        ngay_le_records = self.env['lich_nghi_le'].search([
            ('ngay_bat_dau', '<=', ngay_ket_thuc),
            ('ngay_ket_thuc', '>=', ngay_bat_dau)
        ])
        
        for ngay_le in ngay_le_records:
            ngay_hien_tai = ngay_le.ngay_bat_dau
            while ngay_hien_tai <= ngay_le.ngay_ket_thuc:
                ngay_le_list.add(ngay_hien_tai)
                ngay_hien_tai += timedelta(days=1)

        return ngay_le_list

    @api.model
    def create(self, vals):
        record = super(DotDangKyCaLam, self).create(vals)

        nhan_vien_ids = record.nhan_vien_ids
        ngay_bat_dau = record.ngay_bat_dau
        ngay_ket_thuc = record.ngay_ket_thuc

        if nhan_vien_ids and ngay_bat_dau and ngay_ket_thuc:
            ngay_le_list = self._get_ngay_le(ngay_bat_dau, ngay_ket_thuc)

            ngay_dang_ky = ngay_bat_dau
            while ngay_dang_ky <= ngay_ket_thuc:
                if ngay_dang_ky.weekday() != 6 and ngay_dang_ky not in ngay_le_list:
                    for nhan_vien in nhan_vien_ids:
                        self.env['dang_ky_ca_lam'].create({
                            'nhan_vien_id': nhan_vien.id,
                            'dot_dang_ky_id': record.id,
                            'ngay_dang_ky': ngay_dang_ky,
                            'ca_lam_id': False,
                            'trang_thai': 'Chờ duyệt'
                        })
                ngay_dang_ky += timedelta(days=1)

        return record
    
    def write(self, vals):
        for record in self:
            if record.trang_thai_ap_dung == "Ngừng áp dụng":
                raise ValidationError("Không thể chỉnh sửa đợt đăng ký đã Ngừng áp dụng!")

            nhan_vien_cu = set(record.nhan_vien_ids.ids)
            ngay_bat_dau_cu = record.ngay_bat_dau
            ngay_ket_thuc_cu = record.ngay_ket_thuc

            res = super(DotDangKyCaLam, self).write(vals)

            ngay_bat_dau_moi = record.ngay_bat_dau
            ngay_ket_thuc_moi = record.ngay_ket_thuc
            nhan_vien_moi = set(record.nhan_vien_ids.ids)

            if ngay_bat_dau_cu != ngay_bat_dau_moi or ngay_ket_thuc_cu != ngay_ket_thuc_moi:
                self.env['dang_ky_ca_lam'].search([
                    ('dot_dang_ky_id', '=', record.id),
                    '|', 
                    ('ngay_dang_ky', '<', ngay_bat_dau_moi),
                    ('ngay_dang_ky', '>', ngay_ket_thuc_moi)
                ]).unlink()

                ngay_le_list = self._get_ngay_le(ngay_bat_dau_moi, ngay_ket_thuc_moi)

                ngay_dang_ky = ngay_bat_dau_moi
                while ngay_dang_ky <= ngay_ket_thuc_moi:
                    if ngay_dang_ky.weekday() != 6 and ngay_dang_ky not in ngay_le_list:
                        for nhan_vien_id in nhan_vien_moi:
                            if not self.env['dang_ky_ca_lam'].search([
                                ('dot_dang_ky_id', '=', record.id),
                                ('nhan_vien_id', '=', nhan_vien_id),
                                ('ngay_dang_ky', '=', ngay_dang_ky)
                            ]):
                                self.env['dang_ky_ca_lam'].create({
                                    'nhan_vien_id': nhan_vien_id,
                                    'dot_dang_ky_id': record.id,
                                    'ngay_dang_ky': ngay_dang_ky,
                                    'ca_lam_id': False,
                                    'trang_thai': 'Chờ duyệt'
                                })
                    ngay_dang_ky += timedelta(days=1)

            if nhan_vien_cu != nhan_vien_moi:
                nhan_vien_xoa = nhan_vien_cu - nhan_vien_moi
                self.env['dang_ky_ca_lam'].search([
                    ('dot_dang_ky_id', '=', record.id),
                    ('nhan_vien_id', 'in', list(nhan_vien_xoa))
                ]).unlink()

                nhan_vien_them = nhan_vien_moi - nhan_vien_cu
                ngay_le_list = self._get_ngay_le(ngay_bat_dau_moi, ngay_ket_thuc_moi)

                for nhan_vien_id in nhan_vien_them:
                    ngay_dang_ky = ngay_bat_dau_moi
                    while ngay_dang_ky <= ngay_ket_thuc_moi:
                        if ngay_dang_ky.weekday() != 6 and ngay_dang_ky not in ngay_le_list:
                            self.env['dang_ky_ca_lam'].create({
                                'nhan_vien_id': nhan_vien_id,
                                'dot_dang_ky_id': record.id,
                                'ngay_dang_ky': ngay_dang_ky,
                                'ca_lam_id': False,
                                'trang_thai': 'Chờ duyệt'
                            })
                        ngay_dang_ky += timedelta(days=1)
        return res
    
    def unlink(self):
        for record in self:
            self.env['dang_ky_ca_lam'].search([('dot_dang_ky_id', '=', record.id)]).unlink()
        
        return super(DotDangKyCaLam, self).unlink()
        