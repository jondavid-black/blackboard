import flet as ft
import flet.canvas as cv


def main(page: ft.Page):
    page.bgcolor = ft.Colors.WHITE

    cp = cv.Canvas(
        shapes=[
            cv.Path(
                [
                    cv.Path.MoveTo(50, 50),
                    cv.Path.LineTo(250, 50),
                    cv.Path.LineTo(250, 250),
                    cv.Path.LineTo(50, 250),
                    cv.Path.Close(),
                ],
                paint=ft.Paint(
                    stroke_width=20,
                    style=ft.PaintingStyle.STROKE,
                    stroke_join=ft.StrokeJoin.ROUND,
                    color=ft.Colors.RED,
                ),
            ),
            cv.Path(
                [
                    cv.Path.MoveTo(300, 50),
                    cv.Path.LineTo(500, 50),
                    cv.Path.LineTo(500, 250),
                    cv.Path.LineTo(300, 250),
                    cv.Path.Close(),
                ],
                paint=ft.Paint(
                    stroke_width=20,
                    style=ft.PaintingStyle.STROKE,
                    stroke_join=ft.StrokeJoin.BEVEL,
                    color=ft.Colors.BLUE,
                ),
            ),
        ],
        width=float("inf"),
        expand=True,
    )

    page.add(cp)


ft.app(target=main)
