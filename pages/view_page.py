# view_page.txt
import flet as ft
from utils.button_utils import create_button

class ViewPage:
    def __init__(self, page, background_image, db):
        self.page = page
        self.navigate = None
        self.background_image = background_image

    def set_navigate(self, navigate):
        self.navigate = navigate

    def get_content(self):
        title = ft.Text(
            "عرض البيانات",
            size=40,
            weight=ft.FontWeight.BOLD,
            color="white",
            text_align=ft.TextAlign.CENTER,
            font_family="DancingScript",
        )

        # زر عرض المتبقيات
        btn_view_remaining = create_button(
            "عرض المتبقيات",
            lambda e: self.navigate("show_purchases"),
            bgcolor=ft.colors.GREEN
        )

        # زر عرض النثريات
        btn_view_expenses = create_button(
            "عرض النثريات",
            lambda e: self.navigate("show_over"),
            bgcolor=ft.colors.GREEN
        )

        # زر عرض بيانات المشتركين
        btn_view_members = create_button(
            "عرض بيانات المشتركين",
            lambda e: self.navigate("show_subscribers"),
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
                    ft.Container(height=40),
                    title,
                    ft.Container(height=30),
                    btn_view_remaining,
                    ft.Container(height=20),
                    btn_view_expenses,
                    ft.Container(height=20),
                    btn_view_members,
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
