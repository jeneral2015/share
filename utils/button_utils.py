import flet as ft

def create_button(
    text,
    on_click,
    bgcolor=ft.colors.GREEN,
    color=ft.colors.WHITE,
    width=200,
    height=50,
    elevation=2,
    shadow_color=None,
    hover_bgcolor=None,
    icon=None,
    icon_color=None
):
    hover_bgcolor = hover_bgcolor or ft.colors.with_opacity(0.8, bgcolor)
    shadow_color = shadow_color or bgcolor

    def button_hover(e):
        btn = e.control.content
        btn.bgcolor = bgcolor if e.data == "true" else hover_bgcolor
        btn.scale = 1.05 if e.data == "true" else 1.0
        e.control.shadow.blur_radius = 15 if e.data == "true" else 10
        e.control.update()

    return ft.Container(
        width=width,
        height=height,
        content=ft.ElevatedButton(
            text=text,
            bgcolor=bgcolor,
            color=color,
            on_click=on_click,
            icon=icon,
            icon_color=icon_color,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=10),
                elevation={"pressed": 0, "": elevation}
            )
        ),
        shadow=ft.BoxShadow(
            blur_radius=10,
            color=shadow_color,
            spread_radius=2
        ),
        on_hover=button_hover,
        animate_scale=ft.animation.Animation(200, "easeInOut")
    )
