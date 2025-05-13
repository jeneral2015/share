import flet as ft
from database import DatabaseManager
from utils.button_utils import create_button

class ShowPurchasesPage:
    def __init__(self, page, background_image, db):
        self.page = page
        self.navigate = None
        self.background_image = background_image
        self.db =  db

        # تهيئة المتغيرات لتتبع الصف المحدد
        self.selected_row = None
        self.selected_item_id = None
        self.selected_row_control = None

    def set_navigate(self, navigate):
        self.navigate = navigate

    def get_expenses_data(self):
        results = self.db.fetch_all(
               "SELECT expense_id, item_name, quantity, price, total_price, consumption, remaining, is_miscellaneous, is_drink FROM expenses WHERE is_miscellaneous = 0"
        )
        columns = ["expense_id", "item_name", "quantity", "price", "total_price", "consumption", "remaining", "is_miscellaneous", "is_drink"]
        return [dict(zip(columns, row)) for row in results]
        

    def select_row(self, e, row):
        if self.selected_row_control is not None:
            self.selected_row_control.bgcolor = None  # إعادة لون الصف السابق

        self.selected_row = row
        self.selected_item_id = row['expense_id']
        if e is not None:  # إذا تم النقر على الصف
            e.control.bgcolor = ft.colors.YELLOW  # تغيير لون الصف المحدد إلى أصفر
            self.selected_row_control = e.control
        self.page.update()

    def edit_item(self, e):
        if not hasattr(self, 'selected_row') or self.selected_row is None:
            self.show_snackbar("يرجى اختيار صنف للتعديل.")
            return

        item_id = self.selected_row['expense_id']

        # إنشاء الأزرار باستخدام Container لتحديد padding
        self.edit_is_miscellaneous = ft.Container(
            content=ft.ElevatedButton(
                text="نثريات: مفعل" if self.selected_row['is_miscellaneous'] == 1 else "نثريات: غير مفعل",
                width=120,  # تقليل العرض
                bgcolor=ft.colors.GREEN if self.selected_row['is_miscellaneous'] == 1 else ft.colors.RED,
                color=ft.colors.WHITE,
                on_click=lambda e: self.toggle_button(e, "is_miscellaneous"),
            ),
            shadow=ft.BoxShadow(blur_radius=10, color=ft.colors.GREEN if self.selected_row['is_miscellaneous'] == 1 else ft.colors.RED),
            padding=ft.Padding(1, 1, 1, 1),
        )

        self.edit_is_drink = ft.Container(
            content=ft.ElevatedButton(
                text="مشروبات: مفعل" if self.selected_row['is_drink'] == 1 else "مشروبات: غير مفعل",
                width=120,  # تقليل العرض
                bgcolor=ft.colors.GREEN if self.selected_row['is_drink'] == 1 else ft.colors.RED,
                color=ft.colors.WHITE,
                on_click=lambda e: self.toggle_button(e, "is_drink"),
            ),
            shadow=ft.BoxShadow(blur_radius=10, color=ft.colors.GREEN if self.selected_row['is_drink'] == 1 else ft.colors.RED),
            padding=ft.Padding(1, 1, 1, 1),
        )

        # إنشاء الحقول النصية مع تقليل الارتفاع وحجم الخط
        fields = [
            ft.TextField(label="اسم الصنف", value=self.selected_row['item_name'], height=40, text_size=12),
            ft.TextField(label="الكمية", value=str(self.selected_row['quantity']), height=40, text_size=12),
            ft.TextField(label="سعر الوحدة", value=str(self.selected_row['price']), height=40, text_size=12),
            ft.TextField(label="السعر الإجمالي", value=str(self.selected_row['total_price']), height=40, text_size=12),
            ft.TextField(label="الاستهلاك", value=str(self.selected_row['consumption']), height=40, text_size=12),
            ft.TextField(label="المتبقي", value=str(self.selected_row['remaining']), height=40, text_size=12),
        ]

        # إنشاء صف للأزرار مع تقليل المسافات
        buttons_row = ft.Row(
            [self.edit_is_miscellaneous, self.edit_is_drink],
            spacing=10,  # تقليل المسافة بين الأزرار
            alignment=ft.MainAxisAlignment.CENTER,
        )

        # إضافة مسافة صغيرة بين الأزرار وأزرار الحفظ والإلغاء
        padding_between_rows = ft.Container(height=5)  # تقليل المسافة إلى 5

        # إنشاء صف لأزرار الحفظ والإلغاء مع تقليل المسافات
        save_cancel_row = ft.Row(
            [
                ft.TextButton("حفظ", on_click=lambda e: self.save_edit(item_id, dialog)),
                ft.TextButton("إلغاء", on_click=lambda e: self.close_dialog(dialog)),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=10,  # تقليل المسافة بين الأزرار
        )

        # إنشاء محتوى الحوار مع تقليل المسافات
        dialog_content = ft.Column(
            fields + [buttons_row, padding_between_rows, save_cancel_row],
            spacing=5,  # تقليل المسافة بين الحقول إلى 5
            scroll=True,  # الإبقاء على السكرول إذا لزم الأمر
        )

        # إنشاء الحوار مع padding أقل
        dialog = ft.AlertDialog(
            title=ft.Text("تعديل بيانات الصنف"),
            content=dialog_content,
            content_padding=ft.Padding(10, 10, 10, 10),  # تقليل padding داخل الديالوج
        )
        self.page.dialog = dialog
        dialog.open = True
        self.page.update()

    def toggle_button(self, e, button_type):
        if button_type == "is_miscellaneous":
            self.selected_row['is_miscellaneous'] = 1 if self.selected_row['is_miscellaneous'] == 0 else 0
            e.control.text = "نثريات: مفعل" if self.selected_row['is_miscellaneous'] == 1 else "نثريات: غير مفعل"
            e.control.bgcolor = ft.colors.GREEN if self.selected_row['is_miscellaneous'] == 1 else ft.colors.RED
        elif button_type == "is_drink":
            self.selected_row['is_drink'] = 1 if self.selected_row['is_drink'] == 0 else 0
            e.control.text = "مشروبات: مفعل" if self.selected_row['is_drink'] == 1 else "مشروبات: غير مفعل"
            e.control.bgcolor = ft.colors.GREEN if self.selected_row['is_drink'] == 1 else ft.colors.RED
        self.page.update()

    def save_edit(self, item_id, dialog):
        controls = dialog.content.controls
        item_name = controls[0].value
        quantity = int(controls[1].value)
        price = float(controls[2].value)
        total_price = float(controls[3].value)
        consumption = int(controls[4].value)
        remaining = int(controls[5].value)

        # التحقق من التغييرات التلقائية
        if remaining != quantity - consumption:
            self.show_snackbar("سيتم تعديل المتبقيات تلقائيًا بناءً على الكمية والاستهلاك.")
            remaining = quantity - consumption

        if price != total_price / quantity:
            self.show_snackbar("سيتم تعديل سعر الوحدة تلقائيًا بناءً على السعر الإجمالي والكمية.")
            price = total_price / quantity

        if item_name and quantity >= 0 and price >= 0:
            try:
                cursor = self.db.conn.cursor()
                cursor.execute("""
                    UPDATE expenses 
                    SET item_name=?, quantity=?, price=?, total_price=?, consumption=?, remaining=?, is_miscellaneous=?, is_drink=? 
                    WHERE expense_id=?
                """, (item_name, quantity, price, total_price, consumption, remaining, self.selected_row['is_miscellaneous'], self.selected_row['is_drink'], item_id))
                self.db.conn.commit()
                self.show_snackbar("تم تعديل البيانات بنجاح!")
                self.close_dialog(dialog)
                self.update_table()
            except Exception as e:
                self.show_snackbar(f"حدث خطأ أثناء تعديل البيانات: {e}")
        else:
            self.show_snackbar("يرجى ملء جميع الحقول بشكل صحيح.")
        self.page.update()

    def delete_item(self, e):
        if not hasattr(self, 'selected_row'):
            self.show_snackbar("يرجى اختيار صنف للحذف.")
            return

        item_id = self.selected_row['expense_id']

        # رسالة تأكيد الحذف
        confirm_dialog = ft.AlertDialog(
            title=ft.Text("تأكيد الحذف"),
            content=ft.Text("هل أنت متأكد أنك تريد حذف هذا الصنف؟"),
            actions=[
                ft.TextButton("نعم", on_click=lambda e: self.confirm_delete(item_id, confirm_dialog)),
                ft.TextButton("لا", on_click=lambda e: self.close_dialog(confirm_dialog)),
            ],
        )
        self.page.overlay.append(confirm_dialog)
        confirm_dialog.open = True
        self.page.update()

    def confirm_delete(self, item_id, dialog):
        try:
            cursor = self.db.conn.cursor()
            cursor.execute("DELETE FROM expenses WHERE expense_id=?", (item_id,))
            self.db.conn.commit()
            self.show_snackbar("تم حذف الصنف بنجاح!")
            self.close_dialog(dialog)
            self.update_table()
        except Exception as e:
            self.show_snackbar(f"حدث خطأ أثناء الحذف: {e}")

    def update_table(self):
        # تحديث البيانات في الجدول
        self.rows = self.get_expenses_data()
        self.data_rows.clear()
        display_columns = ["remaining", "consumption", "total_price", "price", "quantity", "item_name", "expense_id"]
        self.data_rows.extend([
            ft.Container(
                content=ft.Row(
                    [
                        ft.Container(
                            content=ft.Text(str(row[col])),
                            width=80 if col == "expense_id" else 100,
                            alignment=ft.alignment.center,
                            padding=10,
                            bgcolor=None,
                        ) for col in display_columns
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                ),
                on_click=lambda e, row=row: self.select_row(e, row),
            ) for row in self.rows
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
        title = ft.Text(
            "عرض الأصناف المتبقية",
            size=40,
            weight=ft.FontWeight.BOLD,
            color=ft.colors.WHITE,
            text_align=ft.TextAlign.CENTER,
        )

        # عناوين الأعمدة بالعربية
        columns = ["remaining", "consumption", "total_price", "price", "quantity", "item_name", "expense_id"]
        column_names = {
            "expense_id": "ID",
            "item_name": "اسم الصنف",
            "quantity": "الكمية",
            "price": "سعر الوحدة",
            "total_price": "السعر الإجمالي",
            "consumption": "الاستهلاك",
            "remaining": "المتبقي",
        }

        # صف العناوين الثابت
        self.header_row = ft.Container(
            content=ft.Row(
                [
                    ft.Container(
                        content=ft.Text(column_names[col], weight=ft.FontWeight.BOLD),
                        width=80 if col == "expense_id" else 100,
                        alignment=ft.alignment.center,
                        padding=10,
                        bgcolor=ft.colors.GREEN,
                    ) for col in columns
                ],
                alignment=ft.MainAxisAlignment.CENTER,
            ),
            bgcolor=ft.colors.GREEN,
            shadow=ft.BoxShadow(blur_radius=30, color="green"),
            width=750,
        )

        # بيانات الجدول
        self.rows = self.get_expenses_data()
        self.data_rows = [
            ft.Container(
                content=ft.Row(
                    [
                        ft.Container(
                            content=ft.Text(str(row[col])),
                            width=80 if col == "expense_id" else 100,
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
            width=750,
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
        btn_edit = create_button("تعديل", lambda e: self.edit_item(e), bgcolor=ft.colors.AMBER)
        btn_delete = create_button("حذف", lambda e: self.delete_item(e), bgcolor=ft.colors.RED)
        btn_back = create_button("رجوع", lambda e: self.navigate("view_page"), bgcolor=ft.colors.RED)

        buttons_row = ft.Row(
            [btn_back, btn_delete, btn_edit],
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=20,
        )

        content = ft.Container(
            content=ft.Column(
                [
                    ft.Container(height=10),
                    title,
                    ft.Container(height=10),
                    self.table,
                    ft.Container(height=10),
                    buttons_row,
                ],
                alignment=ft.MainAxisAlignment.START,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            image_src=self.background_image.src,
            image_fit=ft.ImageFit.COVER,
            expand=True,
        )

        return content
