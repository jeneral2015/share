# input_page.txt
import flet as ft
from utils.button_utils import create_button

class InputPage:
    def __init__(self, page, background_image, db):
        self.page = page
        self.navigate = None
        self.background_image = background_image

    def set_navigate(self, navigate):
        self.navigate = navigate

    def get_content(self):
        title = ft.Text(
            "إدخال البيانات",
            size=40,
            weight=ft.FontWeight.BOLD,
            color="white",
            text_align=ft.TextAlign.CENTER,
            font_family="DancingScript",
        )

        # زر إدخال بيانات المشتركين
        btn_members = create_button(
            "إدخال بيانات المشتركين",
            lambda e: self.navigate("input_subscribers"),
            bgcolor=ft.colors.GREEN
        )

        # زر إدخال المشتروات
        btn_expenses = create_button(
            "إدخال المشتروات",
            lambda e: self.navigate("input_purchases"),
            bgcolor=ft.colors.GREEN
        )

        # زر الرجوع
        btn_back = create_button(
            "رجوع",
            lambda e: self.navigate("main_page"),
            bgcolor=ft.colors.RED
        )

        content = ft.Container(
            content=ft.Column(
                [
                    ft.Container(height=50),
                    title,
                    ft.Container(height=50),
                    btn_members,
                    ft.Container(height=20),
                    btn_expenses,
                    ft.Container(height=20),
                    btn_back,
                ],
                alignment=ft.MainAxisAlignment.START,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            image_src=self.background_image.src,  # استخدام الخلفية المشتركة
            image_fit=ft.ImageFit.COVER,  # الصورة تغطي الخلفية بالكامل
            expand=True,  # جعل العنصر يتكيف مع حجم النافذة
        )

        return content
