import flet as ft
from database import DatabaseManager
from utils.button_utils import create_button
from datetime import datetime  # لإضافة التاريخ

class InputPurchasesPage:
    def __init__(self, page, background_image, db):
        self.page = page
        self.navigate = None
        self.background_image = background_image
        self.db = db

        self.item_name_dropdown = ft.Dropdown(
            options=self.get_expense_options(),
            label="اسم الصنف",
            width=300,
            height=50,
            bgcolor="#f0f0f0",
        )

        self.quantity_field = ft.TextField(
            label="الكمية",
            width=300,
            height=50,
            bgcolor="#f0f0f0",
            keyboard_type=ft.KeyboardType.NUMBER,
        )

        self.total_price_field = ft.TextField(
            label="السعر الإجمالي",
            width=300,
            height=50,
            bgcolor="#f0f0f0",
            keyboard_type=ft.KeyboardType.NUMBER,
        )

        self.is_miscellaneous_check = ft.Checkbox(
            label="هل هي نثريات؟",
            value=False,
            label_style=ft.TextStyle(color="white", weight=ft.FontWeight.BOLD),
            label_position=ft.LabelPosition.LEFT,
        )

        self.is_drink_check = ft.Checkbox(
            label="هل هي مشروبات؟",
            value=False,
            label_style=ft.TextStyle(color="white", weight=ft.FontWeight.BOLD),
            label_position=ft.LabelPosition.LEFT,
        )

    def set_navigate(self, navigate):
        self.navigate = navigate

    def get_expense_options(self):
        cursor = self.db.conn.cursor()
        cursor.execute("SELECT DISTINCT item_name FROM expenses")
        return [ft.dropdown.Option(row[0]) for row in cursor.fetchall()]

    def open_add_item_dialog(self, e):
        self.new_item_name_field = ft.TextField(
            label="اسم الصنف الجديد",
            width=300,
            height=50,
            bgcolor="#f0f0f0",
            on_change=self.search_similar_items
        )
        self.similar_items_list = ft.Column()

        self.add_item_dialog = ft.AlertDialog(
            title=ft.Text("إضافة صنف جديد"),
            content=ft.Column(
                [
                    self.new_item_name_field,
                    ft.Container(height=10),
                    ft.Text("الأصناف المشابهة:", color="red", weight=ft.FontWeight.BOLD),
                    self.similar_items_list,
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                scroll=ft.ScrollMode.AUTO,
            ),
            actions=[
                create_button("إضافة", self.add_new_item),
                create_button("إلغاء", self.close_add_item_dialog, bgcolor=ft.colors.RED_700),
            ],
            actions_alignment=ft.MainAxisAlignment.CENTER,
            on_dismiss=lambda e: self.page.update()
        )

        self.page.dialog = self.add_item_dialog
        self.add_item_dialog.open = True
        self.page.update()

    def search_similar_items(self, e):
        search_query = self.new_item_name_field.value.strip().lower()
        if not search_query:
            self.similar_items_list.controls = []
            self.page.update()
            return

        similar_items = self.db.fetch_all(
            "SELECT item_name FROM expenses WHERE LOWER(item_name) LIKE ?",
            (f"%{search_query}%",)
        )
        similar_items = [item[0] for item in similar_items]
        self.similar_items_list.controls = [
            ft.TextButton(
                content=ft.Text(item, size=14, color="black"),
                on_click=lambda e, item=item: self.select_similar_item(item)
            ) for item in similar_items
        ]
        self.page.update()

    def select_similar_item(self, selected_item):
        print(f"Selected item: {selected_item}")
        item_name = selected_item[0] if isinstance(selected_item, tuple) else selected_item
        self.item_name_dropdown.options = self.get_expense_options()
        self.item_name_dropdown.value = item_name
        self.close_add_item_dialog()
        self.page.update()

    def add_new_item(self, e):
        new_item = self.new_item_name_field.value.strip()
        if not new_item:
            self.show_snackbar("يرجى إدخال اسم الصنف!")
            return

        if any(option.key == new_item for option in self.item_name_dropdown.options):
            self.show_snackbar("هذا الصنف موجود بالفعل!")
            return

        # إضافة التاريخ الحالي
        current_date = datetime.now().strftime("%Y-%m-%d")

        cursor = self.db.conn.cursor()
        cursor.execute(
            "INSERT INTO expenses (item_name, quantity, price, total_price, remaining, date) VALUES (?, 0, 0, 0, 0, ?)",
            (new_item, current_date)
        )
        self.db.conn.commit()

        self.item_name_dropdown.options = self.get_expense_options()
        self.item_name_dropdown.value = new_item
        self.close_add_item_dialog()
        self.page.update()

    def close_add_item_dialog(self, e=None):
        self.add_item_dialog.open = False
        self.page.update()

    def show_snackbar(self, message):
        snack_bar = ft.SnackBar(ft.Text(message))
        self.page.snack_bar = snack_bar
        snack_bar.open = True
        self.page.update()

    def save_expense(self, e):
        try:
            item_name = self.item_name_dropdown.value
            quantity = int(self.quantity_field.value)
            total_price = float(self.total_price_field.value)

            if not all([item_name, quantity > 0, total_price > 0]):
                self.show_snackbar("يرجى ملء جميع الحقول بشكل صحيح!")
                return

            # إضافة التاريخ الحالي
            current_date = datetime.now().strftime("%Y-%m-%d")

            cursor = self.db.conn.cursor()

            # Get existing item data
            cursor.execute("SELECT quantity, price, is_miscellaneous, is_drink FROM expenses WHERE item_name = ?", (item_name,))
            result = cursor.fetchone()

            if result:
                # Update existing item
                old_qty, old_price, old_is_miscellaneous, old_is_drink = result
                new_qty = old_qty + quantity
                new_total = (old_price * old_qty) + total_price
                new_price = new_total / new_qty
                new_is_miscellaneous = self.is_miscellaneous_check.value
                new_is_drink = self.is_drink_check.value

                cursor.execute(
                    "UPDATE expenses SET quantity=?, price=?, total_price=?, remaining=?, is_miscellaneous=?, is_drink=?, date=? WHERE item_name=?",
                    (new_qty, new_price, new_total, new_qty, new_is_miscellaneous, new_is_drink, current_date, item_name)
                )
            else:
                # Insert new item
                unit_price = total_price / quantity
                cursor.execute(
                    "INSERT INTO expenses (item_name, quantity, price, total_price, remaining, is_miscellaneous, is_drink, date) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (item_name, quantity, unit_price, total_price, quantity, self.is_miscellaneous_check.value, self.is_drink_check.value, current_date)
                )

            self.db.conn.commit()
            self.reset_form()
            self.show_snackbar("تم الحفظ بنجاح!")

        except ValueError:
            self.show_snackbar("خطأ في القيم المدخلة! يرجى التأكد من الأرقام")
        except Exception as ex:
            self.show_snackbar(f"خطأ غير متوقع: {str(ex)}")

    def reset_form(self):
        self.item_name_dropdown.value = None
        self.quantity_field.value = ""
        self.total_price_field.value = ""
        self.is_miscellaneous_check.value = False
        self.is_drink_check.value = False
        self.page.update()

    def handle_back_button(self, e):
        self.reset_form()
        if self.navigate:
            self.navigate("input_page")

    def get_content(self):
        return ft.Container(
            content=ft.Column(
                [
                    ft.Container(height=20),
                    ft.Text(
                        "إدخال المشتروات",
                        size=40,
                        weight=ft.FontWeight.BOLD,
                        color="white",
                        text_align=ft.TextAlign.CENTER,
                        font_family="DancingScript",
                    ),
                    ft.Container(height=20),
                    ft.Row(
                        [
                            self.item_name_dropdown,
                            create_button("➕ إضافة صنف", self.open_add_item_dialog, bgcolor=ft.colors.BLUE_700)
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                        spacing=20
                    ),
                    ft.Container(height=10),
                    self.quantity_field,
                    ft.Container(height=10),
                    self.total_price_field,
                    ft.Container(height=10),
                    ft.Row(
                        [
                            self.is_miscellaneous_check,
                            ft.Container(width=20),
                            self.is_drink_check
                        ],
                        alignment=ft.MainAxisAlignment.CENTER
                    ),
                    ft.Container(height=20),
                    ft.Row(
                        [
                            create_button("← رجوع", lambda e: self.handle_back_button(e), bgcolor=ft.colors.RED_700),
                            create_button("💾 حفظ", self.save_expense, bgcolor=ft.colors.GREEN_700)
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                        spacing=50
                    )
                ],
                alignment=ft.MainAxisAlignment.START,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                scroll=ft.ScrollMode.AUTO,
            ),
            image_src=self.background_image.src,
            image_fit=ft.ImageFit.COVER,
            expand=True,
            padding=ft.padding.all(5)
        )
