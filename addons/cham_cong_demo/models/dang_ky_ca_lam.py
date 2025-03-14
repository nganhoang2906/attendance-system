from odoo import models, fields, api
from odoo.exceptions import ValidationError

class DangKyCaLam(models.Model):
    _name = 'dang_ky_ca_lam'
    _description = 'Bảng chứa thông tin đăng ký ca làm'
    _rec_name = 'nhan_vien_id'
    _order = 'ngay_dang_ky desc'
    _sql_constraints = [
        ('unique_dang_ky', 'unique(nhan_vien_id, ngay_dang_ky)', 'Nhân viên này đã đăng ký ca làm vào ngày này!'),
    ]

    nhan_vien_id = fields.Many2one('nhan_vien', string="Nhân viên", required=True)
    dot_dang_ky_id = fields.Many2one('dot_dang_ky_ca_lam', string="Đợt đăng ký", required=True)
    ngay_dang_ky = fields.Date("Ngày đăng ký", required=True)
    ca_lam_id = fields.Many2one('ca_lam', string="Ca làm")
    trang_thai = fields.Selection(
        [
            ('Chờ duyệt', "Chờ duyệt"),
            ('Đã duyệt', "Đã duyệt"),
            ('Đã từ chối', "Đã từ chối"),
            ('Đã hủy', "Đã hủy")
        ],
        string="Trạng thái", default="Chờ duyệt", required=True
    )

    @api.constrains('ngay_dang_ky', 'dot_dang_ky_id')
    def _check_ngay_dang_ky_trong_dot(self):
        for record in self:
            if record.dot_dang_ky_id:
                ngay_bat_dau = record.dot_dang_ky_id.ngay_bat_dau
                ngay_ket_thuc = record.dot_dang_ky_id.ngay_ket_thuc
                if not (ngay_bat_dau <= record.ngay_dang_ky <= ngay_ket_thuc):
                    raise ValidationError(
                        f"Ngày đăng ký {record.ngay_dang_ky} không nằm trong đợt đăng ký đã chọn!"
                    )

    @api.constrains('nhan_vien_id', 'dot_dang_ky_id')
    def _check_nhan_vien_in_dot_dang_ky(self):
        for record in self:
            if record.nhan_vien_id not in record.dot_dang_ky_id.nhan_vien_ids:
                raise ValidationError(f'Nhân viên {record.nhan_vien_id.ho_va_ten} không thuộc đợt đăng ký này!')

    @api.constrains('dot_dang_ky_id')
    def _check_trang_thai_dot_dang_ky(self):
        for record in self:
            if record.dot_dang_ky_id.trang_thai_dang_ky != "Đang mở":
                raise ValidationError(f"Đợt đăng ký '{record.dot_dang_ky_id.ten_dot}' đã hết hạn đăng ký!")
    
    @api.constrains('ngay_dang_ky')
    def _check_ngay_dang_ky(self):
        for record in self:
            if record.ngay_dang_ky and record.ngay_dang_ky.weekday() == 6:
                raise ValidationError("Không thể đăng ký ca làm vào ngày Chủ nhật!")
                    
    def action_duyet(self):
        for record in self:
            if not record.ca_lam_id:
                raise ValidationError("Chưa chọn ca làm!")
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
                
    def write(self, vals):
        for record in self:
            if record.trang_thai != 'Chờ duyệt':
                allowed_fields = {'trang_thai'}
                if any(field not in allowed_fields for field in vals.keys()):
                    raise ValidationError("Chỉ có thể cập nhật ở trạng thái 'Chờ duyệt'!")

            if 'nhan_vien_id' in vals:
                raise ValidationError("Không thể chỉnh sửa nhân viên sau khi đăng ký!")

        return super(DangKyCaLam, self).write(vals)