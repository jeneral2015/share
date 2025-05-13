import flet as ft
from datetime import datetime
import logging

class ClearData:
    def __init__(self, page, db):
        self.page = page
        self.db = db
        self.checkboxes = {
            "members": ft.Checkbox(label="سجل المشتركين", label_position=ft.LabelPosition.LEFT),
            "expenses": ft.Checkbox(label="سجل المشتروات", label_position=ft.LabelPosition.LEFT),
            "meals": ft.Checkbox(label="سجل الوجبات", label_position=ft.LabelPosition.LEFT),
            "drinks": ft.Checkbox(label="سجل المشروبات", label_position=ft.LabelPosition.LEFT),
            "misc": ft.Checkbox(label="سجل المصروفات الاخرى", label_position=ft.LabelPosition.LEFT),
            "select_all": ft.Checkbox(label="الكل", label_position=ft.LabelPosition.LEFT),
        }
        self.setup_checkboxes()

    def setup_checkboxes(self):
        def update_select_all(e):
            all_checked = all(cb.value for key, cb in self.checkboxes.items() if key != "select_all")
            self.checkboxes["select_all"].value = all_checked
            self.page.update()

        def select_all_changed(e):
            is_checked = self.checkboxes["select_all"].value
            for key in ["members", "expenses", "meals", "drinks", "misc"]:
                self.checkboxes[key].value = is_checked
            self.page.update()

        self.checkboxes["select_all"].on_change = select_all_changed
        for key in ["members", "expenses", "meals", "drinks", "misc"]:
            self.checkboxes[key].on_change = update_select_all

    def show_confirmation(self):
        content = ft.Column([
            ft.Row([self.checkboxes["select_all"]], alignment=ft.MainAxisAlignment.END),
            *[ft.Row([self.checkboxes[key]], alignment=ft.MainAxisAlignment.END) for key in ["members", "expenses", "meals", "drinks", "misc"]],
        ], scroll=ft.ScrollMode.AUTO)

        def on_confirm(e):
            self.page.dialog.open = False
            self.page.update()
            self._confirm_clear()

        confirm_dialog = ft.AlertDialog(
            title=ft.Text("مسح البيانات"),
            content=content,
            actions=[
                ft.TextButton("نعم", on_click=on_confirm),
                ft.TextButton("لا", on_click=self.close_dialog),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self.page.dialog = confirm_dialog
        confirm_dialog.open = True
        self.page.update()

    def _confirm_clear(self):
        try:
            tables = []
            if self.checkboxes["members"].value:
                tables.append("members")
            if self.checkboxes["expenses"].value:
                tables.append("expenses")
            if self.checkboxes["meals"].value:
                tables.append("meal_records")
            if self.checkboxes["drinks"].value:
                tables.append("drink_records")
            if self.checkboxes["misc"].value:
                tables.append("miscellaneous_expenses")
            if not tables:
                self.show_snackbar("لم يتم اختيار أي جداول!")
                return

            with self.db.conn:
                cursor = self.db.conn.cursor()
                for table in tables:
                    cursor.execute(f"DELETE FROM {table}")

            self.show_snackbar("تم المسح بنجاح!")
            # إذا كان هناك نقل إلى صفحة معينة بعد المسح:
            # self.navigate("main_page")

        except Exception as e:
            logging.error(f"Error clearing data: {str(e)}")
            self.show_snackbar(f"خطأ: {str(e)}")

    def show_snackbar(self, message):
        self.page.snack_bar = ft.SnackBar(ft.Text(message))
        self.page.snack_bar.open = True
        self.page.update()

    def close_dialog(self, e=None):
        if self.page.dialog:
            self.page.dialog.open = False
            self.page.update()
