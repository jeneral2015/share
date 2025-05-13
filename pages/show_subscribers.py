import flet as ft
from database import DatabaseManager
from utils.button_utils import create_button

class ShowSubscribersPage:
    def __init__(self, page, background_image, db):
        self.page = page
        self.navigate = None
        self.background_image = background_image
        self.db =  db

        # تهيئة المتغيرات لتتبع الصف المحدد
        self.selected_row = None
        self.selected_member_id = None
        self.selected_row_control = None

    def set_navigate(self, navigate):
        self.navigate = navigate

    def get_members_data(self):
        rows = self.db.fetch_all("SELECT member_id, rank, name, contribution, total_due FROM members")
        columns = ["member_id", "rank", "name", "contribution", "total_due"]
        return [dict(zip(columns, row)) for row in rows]

    def select_row(self, e, row):
        if self.selected_row_control is not None:
            self.selected_row_control.bgcolor = None  # إعادة لون الصف السابق

        self.selected_row = row
        self.selected_member_id = row['member_id']
        if e is not None:  # إذا تم النقر على الصف
            e.control.bgcolor = ft.colors.YELLOW  # تغيير لون الصف المحدد إلى أصفر
            self.selected_row_control = e.control
        self.page.update()

    def edit_member(self, e):
        if not hasattr(self, 'selected_row') or self.selected_row is None:
            self.show_snackbar("يرجى اختيار مشترك للتعديل.")
            return

        member_id = self.selected_row['member_id']

        # إنشاء الحقول النصية مع تقليل الارتفاع وحجم الخط
        fields = [
            ft.TextField(label="الرتبة", value=self.selected_row['rank'], height=40, text_size=12),
            ft.TextField(label="الاسم", value=self.selected_row['name'], height=40, text_size=12),
            ft.TextField(label="مبلغ المساهمة", value=str(self.selected_row['contribution']), height=40, text_size=12),
            ft.TextField(label="المبلغ المستحق", value=str(self.selected_row['total_due']), height=40, text_size=12),
        ]

        # إنشاء صف لأزرار الحفظ والإلغاء في السنتر
        actions_row = ft.Row(
            [
                ft.TextButton("حفظ", on_click=lambda e: self.save_edit(member_id, dialog)),
                ft.TextButton("إلغاء", on_click=lambda e: self.close_dialog(dialog)),
            ],
            alignment=ft.MainAxisAlignment.CENTER,  # جعل الأزرار في السنتر
            spacing=10,  # تقليل المسافة بين الأزرار
        )

        # إنشاء محتوى الحوار مع تقليل المسافات
        dialog_content = ft.Column(
            fields + [actions_row],
            spacing=5,  # تقليل المسافة بين الحقول
            scroll=True,  # الإبقاء على السكرول إذا لزم الأمر
        )

        # إنشاء الحوار
        dialog = ft.AlertDialog(
            title=ft.Text("تعديل بيانات المشترك"),
            content=dialog_content,
            content_padding=ft.Padding(10, 10, 10, 10),  # تقليل padding داخل الديالوج
        )
        self.page.dialog = dialog
        dialog.open = True
        self.page.update()

    def save_edit(self, member_id, dialog):
        controls = dialog.content.controls
        rank = controls[0].value
        name = controls[1].value
        contribution = float(controls[2].value)
        total_due = float(controls[3].value)

        if rank and name and contribution >= 0 and total_due >= 0:
            try:
                cursor = self.db.conn.cursor()
                cursor.execute("UPDATE members SET total_due=?, contribution=?, name=?, rank=? WHERE member_id=?",
                               (total_due, contribution, name, rank, member_id))
                self.db.conn.commit()
                self.show_snackbar("تم تعديل البيانات بنجاح!")
                self.close_dialog(dialog)
                self.update_table()
            except Exception as e:
                self.show_snackbar(f"حدث خطأ أثناء تعديل البيانات: {e}")
        else:
            self.show_snackbar("يرجى ملء جميع الحقول بشكل صحيح.")
        self.page.update()

    def delete_member(self, e):
        if not hasattr(self, 'selected_row'):
            self.show_snackbar("يرجى اختيار مشترك للحذف.")
            return

        member_id = self.selected_row['member_id']

        # رسالة تأكيد الحذف
        confirm_dialog = ft.AlertDialog(
            title=ft.Text("تأكيد الحذف"),
            content=ft.Text("هل أنت متأكد أنك تريد حذف هذا المشترك؟"),
            actions=[
                ft.TextButton("نعم", on_click=lambda e: self.confirm_delete(member_id, confirm_dialog)),
                ft.TextButton("لا", on_click=lambda e: self.close_dialog(confirm_dialog)),
            ],
        )
        self.page.dialog = confirm_dialog
        confirm_dialog.open = True
        self.page.update()

    def confirm_delete(self, member_id, dialog):
        try:
            cursor = self.db.conn.cursor()
            cursor.execute("DELETE FROM members WHERE member_id=?", (member_id,))
            self.db.conn.commit()
            self.show_snackbar("تم حذف المشترك بنجاح!")
            self.close_dialog(dialog)
            self.update_table()
        except Exception as e:
            self.show_snackbar(f"حدث خطأ أثناء الحذف: {e}")

    def update_table(self):
        # تحديث البيانات في الجدول
        self.rows = self.get_members_data()
        self.data_rows.clear()
        self.data_rows.extend([
            ft.Container(
                content=ft.Row(
                    [
                        ft.Container(
                            content=ft.Text(str(row[col])),
                            width=120,
                            alignment=ft.alignment.center,
                            padding=10,
                            bgcolor=None,
                        ) for col in ["total_due", "contribution", "name", "rank", "member_id"]
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                ),
                on_click=lambda e, row=row: self.select_row(e, row),
            ) for idx, row in enumerate(self.rows)
        ])
        self.scrollable_data.controls = self.data_rows
        self.page.update()

    def close_dialog(self, dialog):
        dialog.open = False
        self.page.update()

    def show_snackbar(self, message):
        snack_bar = ft.SnackBar(ft.Text(message))
        self.page.snack_bar = snack_bar
        snack_bar.open = True
        self.page.update()

    def get_content(self):
        # العنوان
        title = ft.Text(
            "عرض بيانات المشتركين",
            size=25,
            color=ft.colors.GREEN,
            weight=ft.FontWeight.BOLD,
            text_align=ft.TextAlign.CENTER,
        )

        # عناوين الأعمدة بالعربية
        columns = ["total_due", "contribution", "name", "rank", "member_id"]
        column_names = {
            "member_id": "ID",
            "rank": "الرتبة",
            "name": "الاسم",
            "contribution": "مبلغ المساهمة",
            "total_due": "المبلغ المستحق",
        }

        # صف العناوين الثابت
        self.header_row = ft.Container(
            content=ft.Row(
                [
                    ft.Container(
                        content=ft.Text(column_names[col], weight=ft.FontWeight.BOLD),
                        width=120,
                        alignment=ft.alignment.center,
                        padding=10,
                        bgcolor=ft.colors.GREEN,
                    ) for col in columns
                ],
                alignment=ft.MainAxisAlignment.CENTER,
            ),
            bgcolor=ft.colors.GREEN,
            shadow=ft.BoxShadow(blur_radius=30, color="green"),
            width=600,
        )

        # بيانات الجدول
        self.rows = self.get_members_data()
        self.data_rows = [
            ft.Container(
                content=ft.Row(
                    [
                        ft.Container(
                            content=ft.Text(str(row[col])),
                            width=120,
                            alignment=ft.alignment.center,
                            padding=10,
                            bgcolor=None,
                        ) for col in columns
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                ),
                on_click=lambda e, row=row: self.select_row(e, row),
            ) for idx, row in enumerate(self.rows)
        ]

        # الجدول مع سكرول بار
        self.scrollable_data = ft.ListView(
            self.data_rows,
            height=300,
            width=640,
            spacing=0,
            padding=0,
        )

        # تغليف ListView داخل Container
        scrollable_container = ft.Container(
            content=self.scrollable_data,
            bgcolor=ft.colors.LIGHT_GREEN,
            shadow=ft.BoxShadow(blur_radius=30, color="green"),
        )

        # وضع صف العناوين والبيانات في عمود
        self.table = ft.Column(
            [
                self.header_row,
                scrollable_container,
            ],
            spacing=0,
        )

        # وضع الأزرار في سطر واحد باستخدام الزر الموحد
        btn_edit = create_button("تعديل", lambda e: self.edit_member(e), bgcolor=ft.colors.AMBER)
        btn_delete = create_button("حذف", lambda e: self.delete_member(e), bgcolor=ft.colors.RED)
        btn_back = create_button("رجوع", lambda e: self.navigate("view_page"), bgcolor=ft.colors.RED)

        buttons_row = ft.Row(
            [btn_back, btn_delete, btn_edit],
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=20,
        )

        # العناصر الرئيسية
        content = ft.Container(
            content=ft.Column(
                [
                    ft.Container(height=5),
                    title,
                    ft.Container(height=5),
                    self.table,
                    ft.Container(height=10),
                    buttons_row,
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            image_src=self.background_image.src,
            image_fit=ft.ImageFit.COVER,
            expand=True,
        )

        return content
