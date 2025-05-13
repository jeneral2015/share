import flet as ft
from database import DatabaseManager
from utils.button_utils import create_button
from datetime import datetime  # لإضافة التاريخ

class InputSubscribersPage:
    def __init__(self, page, background_image, db):
        self.page = page
        self.navigate = None
        self.background_image = background_image
        self.db = db

        self.rank_dropdown = ft.Dropdown(
            options=[
                ft.dropdown.Option("عميد"),
                ft.dropdown.Option("عقيد"),
                ft.dropdown.Option("مقدم"),
                ft.dropdown.Option("رائد"),
                ft.dropdown.Option("نقيب"),
                ft.dropdown.Option("ملازم أول"),
                ft.dropdown.Option("ملازم"),
            ],
            label="الرتبة",
            width=300,
            bgcolor="#f0f0f0",
        )

        self.name_field = ft.TextField(
            label="اسم المشترك",
            width=300,
            height=50,
            bgcolor="#f0f0f0",
            on_change=self.search_similar_names,
        )

        self.similar_names_list = ft.ListView(
            expand=True,
            spacing=5,
            padding=10,
            auto_scroll=True,
            height=100,
        )

        self.contribution_field = ft.TextField(
            label="مبلغ المساهمة",
            width=300,
            height=50,
            bgcolor="#f0f0f0",
            keyboard_type=ft.KeyboardType.NUMBER,
        )

    def set_navigate(self, navigate):
        self.navigate = navigate

    def search_similar_names(self, e):
        search_query = self.name_field.value.strip().lower()
        if not search_query:
            self.similar_names_list.controls = []
            self.page.update()
            return
        similar_names = self.db.fetch_all(
              "SELECT name FROM members WHERE LOWER(name) LIKE ?",(f"%{search_query}%",)
        )

        similar_names = [row[0] for row in similar_names]

        self.similar_names_list.controls = [
            ft.TextButton(
                content=ft.Text(name, size=14, color=ft.colors.WHITE, width=300),
                on_click=lambda e, n=name: self.select_similar_name(n)
            ) for name in similar_names
        ]
        self.page.update()

    def select_similar_name(self, selected_name):
        self.name_field.value = selected_name
        self.reset_form()
        self.show_snackbar("هذا الاسم موجود بالفعل!")
        self.page.update()

    def save_member(self, e):
        rank = self.rank_dropdown.value
        name = self.name_field.value.strip()
        contribution = self.contribution_field.value.strip()

        if not all([rank, name, contribution]):
            self.show_snackbar("يرجى ملء جميع الحقول بشكل صحيح.")
            return

        try:
            contribution = float(contribution)
            if contribution < 0:
                self.show_snackbar("مبلغ المساهمة يجب أن يكون رقمًا موجبًا.")
                return

            cursor = self.db.conn.cursor()

            # التحقق من عدم تكرار الاسم
            cursor.execute("SELECT COUNT(*) FROM members WHERE name = ?", (name,))
            if cursor.fetchone()[0] > 0:
                self.show_snackbar("هذا الاسم موجود بالفعل!")
                return

            # إضافة التاريخ الحالي
            current_date = datetime.now().strftime("%Y-%m-%d")

            # إدراج البيانات مع التاريخ
            cursor.execute(
                "INSERT INTO members (rank, name, contribution, date) VALUES (?, ?, ?, ?)",
                (rank, name, contribution, current_date)
            )
            self.db.conn.commit()
            self.reset_form()
            self.show_snackbar("تم حفظ البيانات بنجاح!")

        except ValueError:
            self.show_snackbar("مبلغ المساهمة يجب أن يكون رقمًا.")
        except Exception as ex:
            self.db.conn.rollback()
            self.show_snackbar(f"حدث خطأ أثناء حفظ البيانات: {str(ex)}")

    def reset_form(self):
        self.rank_dropdown.value = None
        self.name_field.value = ""
        self.similar_names_list.controls = []
        self.contribution_field.value = ""
        self.page.update()

    def handle_back(self, e):
        self.reset_form()
        self.navigate("input_page")

    def get_content(self):
        title = ft.Text(
            "إدخال بيانات المشتركين",
            size=25,
            color=ft.colors.WHITE,
            weight=ft.FontWeight.BOLD,
            text_align=ft.TextAlign.CENTER,
        )

        rank_field = ft.Container(
            content=self.rank_dropdown,
            alignment=ft.alignment.center,
        )

        name_section = ft.Column(
            [
                self.name_field,
                self.similar_names_list,
            ],
            alignment=ft.MainAxisAlignment.START,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )

        contribution_field = ft.Container(
            content=self.contribution_field,
            alignment=ft.alignment.center,
        )

        save_button = create_button(
            "حفظ",
            self.save_member,
            bgcolor=ft.colors.GREEN
        )

        back_button = create_button(
            "رجوع",
            self.handle_back,
            bgcolor=ft.colors.RED
        )

        buttons_row = ft.Row(
            [back_button, save_button],
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=20,
        )

        content = ft.Container(
            content=ft.Column(
                [
                    ft.Container(height=20),
                    title,
                    ft.Container(height=5),
                    rank_field,
                    ft.Container(height=5),
                    name_section,
                    ft.Container(height=1),
                    contribution_field,
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

    def show_snackbar(self, message):
        snack_bar = ft.SnackBar(ft.Text(message))
        self.page.snack_bar = snack_bar
        snack_bar.open = True
        self.page.update()
