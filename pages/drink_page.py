import flet as ft
from database import DatabaseManager
from utils.button_utils import create_button
from datetime import datetime
import sqlite3

class DrinkPage:
    def __init__(self, page, background_image, db):
        self.page = page
        self.navigate = None
        self.background_image = background_image
        self.db = db 
        self.selected_row = None
        self.selected_item_id = None
        self.selected_row_control = None
        self.page.on_close = self.close_connection

    def set_navigate(self, navigate):
        self.navigate = navigate

    def get_content(self):
        self.page.clean()
        title = ft.Text(
            "توزيع المشروبات",
            size=40,
            weight=ft.FontWeight.BOLD,
            color=ft.colors.WHITE,
            text_align=ft.TextAlign.CENTER,
        )
        self.date_var = ft.TextField(
            label="التاريخ", 
            value=datetime.now().strftime("%Y-%m-%d"),
            width=300,
            bgcolor=ft.colors.WHITE,
            label_style=ft.TextStyle(size=18, weight=ft.FontWeight.BOLD),
        )
        self.drink_var = ft.Dropdown(
            label="اختر المشروب",
            options=self.get_drink_options(),
            width=300,
            bgcolor=ft.colors.WHITE,
            label_style=ft.TextStyle(size=18, weight=ft.FontWeight.BOLD),
        )
        self.quantity_var = ft.TextField(
            label="العدد",
            value=None,
            width=300,
            bgcolor=ft.colors.WHITE,
            label_style=ft.TextStyle(size=18, weight=ft.FontWeight.BOLD),
        )
        self.member_var = ft.Dropdown(
            label="اختر الشخص",
            options=self.get_member_options(),
            width=300,
            bgcolor=ft.colors.WHITE,
            label_style=ft.TextStyle(size=18, weight=ft.FontWeight.BOLD),
        )
        btn_save = create_button("حفظ", lambda e: self.save_drink_distribution(e), bgcolor=ft.colors.GREEN)
        btn_back = create_button("رجوع", lambda e: self.navigate("distribute_expenses"), bgcolor=ft.colors.RED)
        content = ft.Column(
            [title, self.date_var, self.drink_var, self.quantity_var, self.member_var, ft.Row([btn_back, btn_save], alignment=ft.MainAxisAlignment.CENTER, spacing=20)],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=20,
        )
        container = ft.Container(
            content=content,
            image_src=self.background_image.src,
            image_fit=ft.ImageFit.COVER,
            expand=True,
        )
        return container

    def get_drink_options(self):
        cursor = self.db.conn.cursor()
        cursor.execute("SELECT item_name FROM expenses WHERE is_drink = 1")
        return [ft.dropdown.Option(row[0]) for row in cursor.fetchall()]

    def get_member_options(self):
        cursor = self.db.conn.cursor()
        cursor.execute("SELECT member_id, rank || ' ' || name FROM members")
        return [ft.dropdown.Option(f"{row[0]} - {row[1]}") for row in cursor.fetchall()]

    ### دالة جديدة لإعادة تعيين الحقول ###
    def reset_fields(self):
        self.date_var.value = datetime.now().strftime("%Y-%m-%d")  # إعادة تعيين التاريخ للتاريخ الحالي
        self.drink_var.value = None  # إعادة تعيين اختيار المشروب لقيمة فارغة
        self.quantity_var.value = None  # إعادة تعيين العدد لـ 0
        self.member_var.value = None  # إعادة تعيين اختيار الشخص لقيمة فارغة
        self.page.update()  # تحديث الصفحة لعرض التغييرات

    def save_drink_distribution(self, e):
        drink_name = self.drink_var.value
        quantity = int(self.quantity_var.value)
        member_info = self.member_var.value
        date = self.date_var.value

        if drink_name and quantity > 0 and member_info and date:
            try:
                cursor = self.db.conn.cursor()
                member_id = member_info.split(" - ")[0]
                cursor.execute("SELECT price, quantity, consumption FROM expenses WHERE item_name = ? AND is_drink = 1", (drink_name,))
                price_data = cursor.fetchone()

                if price_data:
                    unit_price, available_quantity, consumption = price_data
                    if quantity <= available_quantity:
                        total_cost = quantity * unit_price
                        cursor.execute("UPDATE members SET total_due = total_due + ? WHERE member_id = ?", (total_cost, member_id))
                        new_consumption = consumption + quantity
                        remaining_quantity = available_quantity - quantity
                        cursor.execute("UPDATE expenses SET consumption = ?, remaining = ? WHERE item_name = ?", (new_consumption, remaining_quantity, drink_name))
                        cursor.execute("INSERT INTO drink_records (date, drink_name, member_id, quantity, total_cost) VALUES (?, ?, ?, ?, ?)",
                                       (date, drink_name, member_id, quantity, total_cost))
                        self.db.conn.commit()
                        self.show_snackbar("تم توزيع المشروبات بنجاح!")
                        ### استدعاء دالة إعادة التعيين ###
                        self.reset_fields()
                    else:
                        self.show_snackbar("الكمية المطلوبة تتجاوز الكمية المتاحة.")
                else:
                    self.show_snackbar("المشروب غير موجود.")
            except sqlite3.Error as e:
                self.show_snackbar(f"حدث خطأ أثناء توزيع المشروبات: {e}")
        else:
            self.show_snackbar("يرجى ملء جميع الحقول بشكل صحيح.")

    def show_snackbar(self, message):
        snack_bar = ft.SnackBar(ft.Text(message))
        self.page.snack_bar = snack_bar
        snack_bar.open = True
        self.page.update()

    def close_connection(self, e):
        if self.db.conn:
            self.db.conn.close()
