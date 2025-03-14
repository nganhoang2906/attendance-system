from odoo import models, fields, api
from odoo.exceptions import ValidationError

class DonXinDiMuonVeSom(models.Model):
    _name = 'don_xin_di_muon_ve_som'
    _description = "Đơn xin đi muộn về sớm"
    _rec_name = "nhan_vien_id"

    nhan_vien_id = fields.Many2one('nhan_vien', string="Nhân viên", required=True)
    ngay_lam_don = fields.Date("Ngày làm đơn", required=True, default=fields.Date.today)
    ngay_ap_dung = fields.Date("Ngày áp dụng", required=True, default=fields.Date.today)
    ca_lam_id = fields.Many2one('ca_lam', string="Ca làm", readonly=True, compute="_compute_ca_lam", store=True)
    so_phut_xin_di_muon_dau_ca = fields.Integer("Đi muộn đầu ca (phút)", default=0)
    so_phut_xin_ve_som_giua_ca = fields.Integer("Về sớm giữa ca (phút)", default=0)
    so_phut_xin_di_muon_giua_ca = fields.Integer("Đi muộn giữa ca (phút)", default=0)
    so_phut_xin_ve_som_cuoi_ca = fields.Integer("Về sớm cuối ca (phút)", default=0)
    tong_thoi_gian_xin = fields.Float("Tổng thời gian xin (giờ)", compute="_compute_tong_thoi_gian_xin", store=True)
    su_dung_phep = fields.Boolean("Sử dụng phép", default=False)
    ngay_phep_id = fields.Many2one('ngay_phep', string="Ngày phép", compute="_compute_ngay_phep", store=True, readonly=False)
    so_ngay_phep_bi_tru = fields.Float("Số ngày phép bị trừ", compute="_compute_so_ngay_phep_bi_tru", store=True)
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

    @api.depends('so_phut_xin_di_muon_dau_ca', 'so_phut_xin_ve_som_giua_ca', 'so_phut_xin_di_muon_giua_ca', 'so_phut_xin_ve_som_cuoi_ca')
    def _compute_tong_thoi_gian_xin(self):
        for record in self:
            tong_phut = sum([
                record.so_phut_xin_di_muon_dau_ca,
                record.so_phut_xin_ve_som_giua_ca,
                record.so_phut_xin_di_muon_giua_ca,
                record.so_phut_xin_ve_som_cuoi_ca
            ])
            record.tong_thoi_gian_xin = round(tong_phut / 60, 2)
    
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
                if so_phut < 0 or so_phut > 120:
                    raise ValidationError("Số phút đi muộn/về sớm chỉ được nằm trong khoảng 0-120 phút!")

            if not record.ca_lam_id:
                raise ValidationError("Nhân viên chưa đăng ký ca làm vào ngày này!")

            if record.ca_lam_id.ten_ca == "Cả ngày":
                gioi_han = 2 
            else:
                gioi_han = 1

            if record.tong_thoi_gian_xin > gioi_han:
                raise ValidationError(f"Tổng thời gian xin đi muộn, về sớm không được vượt quá {gioi_han} giờ!")

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

    @api.depends('nhan_vien_id', 'ngay_ap_dung')
    def _compute_ngay_phep(self):
        for record in self:
            if record.nhan_vien_id and record.ngay_ap_dung:
                nam = str(record.ngay_ap_dung.year)
                ngay_phep = self.env['ngay_phep'].search([
                    ('nhan_vien_id', '=', record.nhan_vien_id.id),
                    ('nam', '=', nam)
                ], limit=1)
                record.ngay_phep_id = ngay_phep if ngay_phep else False
            else:
                record.ngay_phep_id = False
    
    @api.onchange('su_dung_phep')
    def _onchange_su_dung_phep(self):
        if not self.su_dung_phep:
            self.so_ngay_phep_bi_tru = 0
        self._compute_so_ngay_phep_bi_tru()
    
    @api.depends('tong_thoi_gian_xin')
    def _compute_so_ngay_phep_bi_tru(self):
        for record in self:
            record.so_ngay_phep_bi_tru = round(record.tong_thoi_gian_xin / 8, 2)
    
    @api.constrains('su_dung_phep', 'tong_thoi_gian_xin')
    def _check_su_dung_phep(self):
        for record in self:
            if record.su_dung_phep and record.tong_thoi_gian_xin <= 1:
                raise ValidationError("Tổng thời gian xin đi muộn về sớm phải lớn hơn 1 giờ mới được sử dụng phép!")
                        
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
                so_ngay_su_dung = record.so_ngay_phep_bi_tru

                if record.su_dung_phep and ngay_phep:
                    if record.trang_thai == 'Đã duyệt' and new_state == 'Đã hủy':
                        ngay_phep.write({
                            'so_ngay_da_su_dung': ngay_phep.so_ngay_da_su_dung - so_ngay_su_dung
                        })
                    elif record.trang_thai in ['Chờ duyệt', 'Đã hủy'] and new_state == 'Đã duyệt':
                        if ngay_phep.so_ngay_con_lai < so_ngay_su_dung:
                            raise ValidationError(f"Nhân viên {record.nhan_vien_id.ho_va_ten} không đủ ngày phép để nghỉ!")
                        else:
                            ngay_phep.write({
                                'so_ngay_da_su_dung': ngay_phep.so_ngay_da_su_dung + so_ngay_su_dung
                            })
                    ngay_phep._compute_so_ngay_con_lai()

        return super(DonXinDiMuonVeSom, self).write(vals)