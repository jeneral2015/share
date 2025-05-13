# distribute_expenses.txt
import flet as ft
from utils.button_utils import create_button

class DistributeExpensesPage:
    def __init__(self, page, background_image, db):
        self.page = page
        self.navigate = None
        self.background_image = background_image

    def set_navigate(self, navigate):
        self.navigate = navigate

    def get_content(self):
        title = ft.Text(
            "توزيع المصروفات",
            size=40,
            weight=ft.FontWeight.BOLD,
            color="white",
            text_align=ft.TextAlign.CENTER,
            font_family="DancingScript",
        )

        btn_drinks = create_button("المشروبات", lambda e: self.navigate("drink_page"), bgcolor=ft.colors.GREEN)
        btn_meals = create_button("الوجبات", lambda e: self.navigate("meal_page"), bgcolor=ft.colors.GREEN)
        btn_back = create_button("رجوع", lambda e: self.navigate("main_page"), bgcolor=ft.colors.RED)

        content = ft.Container(
            content=ft.Column(
                [
                    ft.Container(height=50),
                    title,
                    ft.Container(height=50),
                    btn_drinks,
                    ft.Container(height=20),
                    btn_meals,
                    ft.Container(height=20),
                    btn_back,
                ],
                alignment=ft.MainAxisAlignment.START,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            image_src=self.background_image.src,
            image_fit=ft.ImageFit.COVER,
            expand=True,
        )

        return content
