import flet as ft
from utils.button_utils import create_button

class EndMonthPage:
    def __init__(self, page, background_image, db):
        self.page = page
        self.navigate = None
        self.background_image = background_image
        self.db = db
        self.file_picker = ft.FilePicker()
        self.page.overlay.append(self.file_picker)
        self.page.update()

    def set_navigate(self, navigate):
        self.navigate = navigate

    def get_content(self):
        title = ft.Text(
            "تقفيل الشهر",
            size=40,
            weight=ft.FontWeight.BOLD,
            color="white",
            text_align=ft.TextAlign.CENTER,
            font_family="DancingScript",
        )
        buttons_row = ft.Row(
            [
                create_button("توزيع النثريات", self.distribute_miscellaneous, bgcolor=ft.colors.BLUE),
                create_button("مسح البيانات", self.clear_all_data, bgcolor=ft.colors.ORANGE),
                create_button("تقفيل الشهر", self.end_month_process, bgcolor=ft.colors.GREEN),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=20,
        )
        return ft.Container(
            content=ft.Column(
                [
                    ft.Container(height=20),
                    title,
                    ft.Container(height=150),
                    buttons_row,
                    ft.Container(height=50),
                    create_button("رجوع", lambda e: self.navigate("main_page"), bgcolor=ft.colors.RED),
                ],
                alignment=ft.MainAxisAlignment.START,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            image_src=self.background_image.src,
            image_fit=ft.ImageFit.COVER,
            expand=True,
        )

    def distribute_miscellaneous(self, e):
        from pages.distribute_miscellaneous import DistributeMiscellaneous
        DistributeMiscellaneous(self.page, self.db).show_confirmation()

    def clear_all_data(self, e):
        from pages.clear_data import ClearData
        ClearData(self.page, self.db).show_confirmation()

    def end_month_process(self, e):
        from pages.finalize_month import FinalizeMonth
        FinalizeMonth(self.page, self.db).start_process()
