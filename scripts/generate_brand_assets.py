#!/usr/bin/env python3
"""Regenerate the site's favicon, touch icon and 1200 x 630 sharing card.

Authoring dependencies: Python 3, ReportLab, Pillow and Poppler (pdftoppm).
The website serves the finished assets without a build step or dependencies.
"""

from pathlib import Path
import subprocess
import tempfile

from PIL import Image
import reportlab
from reportlab.lib import colors
from reportlab.pdfbase.pdfmetrics import registerFont, stringWidth
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / 'assets'
NAVY = '#173e76'
RED = '#c92e38'
SIGN_RED = '#eb250f'
PAPER = '#fffcf3'
CARD_WIDTH, CARD_HEIGHT = 1200, 630
FONTS = Path(reportlab.__file__).resolve().parent / 'fonts'
registerFont(TTFont('BrandSans', str(FONTS / 'Vera.ttf')))
registerFont(TTFont('BrandSans-Bold', str(FONTS / 'VeraBd.ttf')))

# A small-size drawing of the existing Ellenfoot sign's double arrow.
# The horizontal bars align to whole pixels at both 16 px and 32 px.
# Keep the mark wide, with an opaque red field for light and dark browser chrome.
ICON_POINTS = (
    (8, 8), (14, 8), (22, 12), (29, 12), (29, 14),
    (22, 14), (15, 18), (29, 18), (29, 20), (15, 20),
    (24, 24), (18, 24), (10, 20), (3, 20), (3, 18),
    (10, 18), (17, 14), (3, 14), (3, 12), (17, 12),
)


def write_svg():
    path = 'M' + ' L'.join(f'{x} {y}' for x, y in ICON_POINTS) + ' Z'
    svg = (
        '<svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 32 32">\n'
        '  <title>Ellenfoot double arrow</title>\n'
        f'  <rect width="32" height="32" fill="{SIGN_RED}"/>\n'
        f'  <path d="{path}" fill="#ffffff"/>\n'
        '</svg>\n'
    )
    (ASSETS / 'favicon.svg').write_text(svg, encoding='utf-8')


def draw_icon(pdf):
    pdf.setFillColor(colors.HexColor(SIGN_RED))
    pdf.rect(0, 0, 32, 32, fill=1, stroke=0)
    mark = pdf.beginPath()
    for index, (x, y) in enumerate(ICON_POINTS):
        operation = mark.moveTo if index == 0 else mark.lineTo
        operation(x, 32 - y)
    mark.close()
    pdf.setFillColor(colors.white)
    pdf.drawPath(mark, fill=1, stroke=0)


def draw_card(pdf):
    def rectangle(left, top, width, height, colour):
        pdf.setFillColor(colors.HexColor(colour))
        pdf.rect(left, CARD_HEIGHT - top - height, width, height, fill=1, stroke=0)

    def text(left, baseline, value, size, face='BrandSans', colour=PAPER, max_width=None):
        if max_width is not None and stringWidth(value, face, size) > max_width:
            raise ValueError(f'Sharing-card text exceeds its allotted width: {value}')
        pdf.setFillColor(colors.HexColor(colour))
        pdf.setFont(face, size)
        pdf.drawString(left, CARD_HEIGHT - baseline, value)

    rectangle(0, 0, CARD_WIDTH, CARD_HEIGHT, PAPER)
    rectangle(0, 0, CARD_WIDTH, 470, NAVY)
    rectangle(0, 470, CARD_WIDTH, 8, RED)

    text(64, 88, 'ONLINE DESTINATIONS', 22, 'BrandSans-Bold')
    text(64, 202, 'Cumbrian', 76, 'BrandSans-Bold', max_width=760)
    text(64, 294, 'Railway Modeller', 76, 'BrandSans-Bold', max_width=760)
    text(64, 367, 'Model railways, practical making', 27, max_width=760)
    text(64, 409, 'and open-source engineering.', 27, max_width=760)

    # Place the original sign as a complete square, preserving its lettering,
    # border and fasteners. Only the separate favicon simplifies that artwork.
    sign_left, sign_top, sign_size = 892, 142, 244
    rectangle(sign_left - 4, sign_top - 4, sign_size + 8, sign_size + 8, PAPER)
    pdf.drawImage(str(ASSETS / 'ellenfoot-br-sign.png'),
                  sign_left, CARD_HEIGHT - sign_top - sign_size,
                  width=sign_size, height=sign_size, mask='auto')

    text(64, 568, 'Blog / Facebook / GitHub / TrackTemplate',
         31, 'BrandSans-Bold', NAVY, max_width=1072)


def make_pdf(path, dimensions, draw):
    pdf = canvas.Canvas(str(path), pagesize=dimensions, pageCompression=1, invariant=1)
    pdf.setAuthor('Cumbrian Railway Modeller')
    draw(pdf)
    pdf.showPage()
    pdf.save()


def rasterise(pdf, prefix, width, height):
    subprocess.run([
        'pdftoppm', '-png', '-singlefile', '-scale-to-x', str(width),
        '-scale-to-y', str(height), str(pdf), str(prefix),
    ], check=True)
    return prefix.with_suffix('.png')


def main():
    write_svg()
    with tempfile.TemporaryDirectory(prefix='ellenfoot-brand-') as temporary:
        temporary = Path(temporary)
        icon_pdf = temporary / 'icon.pdf'
        make_pdf(icon_pdf, (32, 32), draw_icon)
        frames = []
        for size in (16, 32, 48):
            path = rasterise(icon_pdf, temporary / f'icon-{size}', size, size)
            with Image.open(path) as frame:
                frames.append(frame.convert('RGBA'))
        # Use each directly rendered frame, without downsampling a larger icon.
        frames[-1].save(ASSETS / 'favicon.ico', format='ICO',
                        sizes=[(16, 16), (32, 32), (48, 48)],
                        append_images=frames[:-1])

        touch = rasterise(icon_pdf, temporary / 'touch-icon', 180, 180)
        with Image.open(touch) as image:
            image.convert('RGB').save(ASSETS / 'apple-touch-icon.png', optimize=True)

        card_pdf = temporary / 'social-card.pdf'
        make_pdf(card_pdf, (CARD_WIDTH, CARD_HEIGHT), draw_card)
        card = rasterise(card_pdf, temporary / 'social-card', CARD_WIDTH, CARD_HEIGHT)
        with Image.open(card) as image:
            image.convert('RGB').save(ASSETS / 'social-card.png', optimize=True)

    print('Created favicon.svg, favicon.ico (16/32/48 px), apple-touch-icon.png (180 px)')
    print(f'and social-card.png ({CARD_WIDTH} x {CARD_HEIGHT}).')


if __name__ == '__main__':
    main()
