from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import timedelta

class DonXinNghi(models.Model):
    _name = 'don_xin_nghi'
    _description = "Đơn xin nghỉ"
    _rec_name = "nhan_vien_id"

    nhan_vien_id = fields.Many2one('nhan_vien', string="Nhân viên", required=True)
    ngay_lam_don = fields.Date("Ngày làm đơn", required=True, default=fields.Date.today)
    ngay_bat_dau_nghi = fields.Date("Ngày bắt đầu nghỉ", required=True)
    ngay_ket_thuc_nghi = fields.Date("Ngày kết thúc nghỉ", required=True)
    so_ngay_nghi = fields.Float("Số ngày nghỉ", compute="_compute_so_ngay_nghi", store=True)
    ngay_phep_id = fields.Many2one('ngay_phep', string="Ngày phép", compute="_compute_ngay_phep", store=True, readonly=False)
    ly_do = fields.Text("Lý do")
    nghi_nua_ngay = fields.Boolean("Nghỉ nửa ngày")
    buoi_nghi = fields.Selection(
        [
            ('Sáng', 'Sáng'), 
            ('Chiều', 'Chiều')
        ],
        string="Buổi nghỉ", default='Sáng'
    )
    loai_nghi = fields.Selection(
        [
            ('Nghỉ phép', "Nghỉ phép"),
            ('Nghỉ không lương', "Nghỉ không lương"),
            ('Nghỉ kết hôn', "Nghỉ kết hôn"),
            ('Nghỉ con kết hôn', "Nghỉ con kết hôn"),
            ('Nghỉ thai sản', "Nghỉ thai sản"),
            ('Nghỉ ma chay', "Nghỉ ma chay"),
            ('Nghỉ hưởng chế độ BHXH', "Nghỉ hưởng chế độ BHXH"),
        ],
        string="Loại nghỉ", default="Nghỉ phép", required=True
    )
    trang_thai = fields.Selection(
        [
            ('Chờ duyệt', "Chờ duyệt"),
            ('Đã duyệt', "Đã duyệt"),
            ('Đã từ chối', "Đã từ chối"),
            ('Đã hủy', "Đã hủy")
        ], 
        string="Trạng thái", default="Chờ duyệt", required=True
    )

    @api.depends('nhan_vien_id', 'ngay_bat_dau_nghi')
    def _compute_ngay_phep(self):
        for record in self:
            if record.nhan_vien_id and record.ngay_bat_dau_nghi:
                nam = str(record.ngay_bat_dau_nghi.year)
                ngay_phep = self.env['ngay_phep'].search([
                    ('nhan_vien_id', '=', record.nhan_vien_id.id),
                    ('nam', '=', nam)
                ], limit=1)
                record.ngay_phep_id = ngay_phep if ngay_phep else False
            else:
                record.ngay_phep_id = False

    @api.constrains('trang_thai', 'ngay_bat_dau_nghi', 'ngay_ket_thuc_nghi', 'nhan_vien_id')
    def _check_don_da_duyet(self):
        for record in self:
            if record.trang_thai == 'Đã duyệt':
                don_da_duyet = self.env['don_xin_nghi'].search([
                    ('nhan_vien_id', '=', record.nhan_vien_id.id),
                    ('id', '!=', record.id),
                    ('trang_thai', '=', 'Đã duyệt'),
                    ('ngay_bat_dau_nghi', '<=', record.ngay_ket_thuc_nghi),
                    ('ngay_ket_thuc_nghi', '>=', record.ngay_bat_dau_nghi),
                ])
                if don_da_duyet:
                    raise ValidationError(
                        f"Nhân viên {record.nhan_vien_id.ho_va_ten} đã có đơn nghỉ được duyệt trong khoảng thời gian này!"
                    )

    @api.onchange('nghi_nua_ngay')
    def _onchange_nghi_nua_ngay(self):
        if not self.nghi_nua_ngay:
            self.buoi_nghi = False
        
        self._compute_so_ngay_nghi()


    @api.depends('ngay_bat_dau_nghi', 'ngay_ket_thuc_nghi', 'nhan_vien_id', 'nghi_nua_ngay', 'buoi_nghi')
    def _compute_so_ngay_nghi(self):
        for record in self:
            if not (record.ngay_bat_dau_nghi and record.ngay_ket_thuc_nghi and record.nhan_vien_id):
                record.so_ngay_nghi = 0
                continue

            so_ngay_lam_ca_ngay = 0
            so_ngay_lam_sang = 0
            so_ngay_lam_chieu = 0

            ngay_co_ca_lam = self.env['dang_ky_ca_lam'].search([
                ('nhan_vien_id', '=', record.nhan_vien_id.id),
                ('ngay_dang_ky', '>=', record.ngay_bat_dau_nghi),
                ('ngay_dang_ky', '<=', record.ngay_ket_thuc_nghi),
                ('trang_thai', '=', 'Đã duyệt')
            ])

            for dk in ngay_co_ca_lam:
                if dk.ca_lam_id.ten_ca == "Cả ngày":
                    so_ngay_lam_ca_ngay += 1
                elif dk.ca_lam_id.ten_ca == "Sáng":
                    so_ngay_lam_sang += 1
                elif dk.ca_lam_id.ten_ca == "Chiều":
                    so_ngay_lam_chieu += 1
            
            if record.nghi_nua_ngay:
                record.so_ngay_nghi = so_ngay_lam_ca_ngay * 0.5 + so_ngay_lam_sang + so_ngay_lam_chieu
            else:
                record.so_ngay_nghi = so_ngay_lam_ca_ngay + so_ngay_lam_sang + so_ngay_lam_chieu

    @api.constrains('nghi_nua_ngay', 'buoi_nghi')
    def _check_buoi_nghi(self):
        for record in self:
            if record.nghi_nua_ngay and not record.buoi_nghi:
                raise ValidationError("Bạn phải chọn buổi nghỉ khi đăng ký nghỉ nửa ngày!")

    @api.constrains('ngay_bat_dau_nghi', 'ngay_ket_thuc_nghi')
    def _check_ngay_nghi(self):
        for record in self:
            if record.ngay_bat_dau_nghi > record.ngay_ket_thuc_nghi:
                raise ValidationError("Ngày bắt đầu phải trước hoặc bằng ngày kết thúc!")
    
    @api.constrains('so_ngay_nghi', 'trang_thai', 'loai_nghi')
    def _check_han_muc_nghi(self):
        for record in self:
            if record.loai_nghi != 'Nghỉ không lương' and record.ngay_phep_id:
                if record.ngay_phep_id.so_ngay_con_lai < record.so_ngay_nghi:
                    raise ValidationError(
                        f"Nhân viên {record.nhan_vien_id.ho_va_ten} không đủ ngày phép để nghỉ! Số ngày phép còn lại: {record.ngay_phep_id.so_ngay_con_lai}"
                    )

    def action_duyet(self):
        for record in self:
            if record.trang_thai == 'Chờ duyệt':
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
        
            if 'trang_thai' in vals:
                new_state = vals['trang_thai']
                ngay_phep = record.ngay_phep_id.sudo()

                if not ngay_phep or record.loai_nghi == 'Nghỉ không lương':
                    continue  

                if record.trang_thai == 'Đã duyệt' and new_state == 'Đã hủy':
                    ngay_phep.write({
                        'so_ngay_da_su_dung': ngay_phep.so_ngay_da_su_dung - record.so_ngay_nghi
                    })

                elif record.trang_thai == 'Chờ duyệt' and new_state == 'Đã duyệt':
                    if ngay_phep.so_ngay_con_lai < record.so_ngay_nghi:
                        raise ValidationError(f"Nhân viên {record.nhan_vien_id.ho_va_ten} không đủ ngày phép để nghỉ!")
                    else:
                        ngay_phep.write({
                            'so_ngay_da_su_dung': ngay_phep.so_ngay_da_su_dung + record.so_ngay_nghi
                        })
                ngay_phep._compute_so_ngay_con_lai()

        return super(DonXinNghi, self).write(vals)
