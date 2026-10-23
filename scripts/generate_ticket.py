#!/usr/bin/env python3
"""Regenerate the sharing ticket PNG and A4 PDF from the site's canonical URL.

Authoring dependencies: Python 3, ReportLab, Pillow and Poppler (pdftoppm).
The website serves the finished files and needs none of these at runtime.
"""

from html.parser import HTMLParser
from pathlib import Path
import subprocess
import tempfile
from urllib.parse import urlsplit

from PIL import Image
import reportlab
from reportlab.graphics import renderPDF
from reportlab.graphics.barcode.qr import QrCodeWidget
from reportlab.graphics.shapes import Drawing
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfbase.pdfmetrics import registerFont, stringWidth
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas


ROOT = Path(__file__).resolve().parents[1]
WIDTH_MM, HEIGHT_MM = 160, 70
PNG_WIDTH, PNG_HEIGHT = 1920, 840
BLUE = colors.HexColor('#173e76')
RED = colors.HexColor('#c92e38')
PAPER = colors.HexColor('#fffcf3')
INK = colors.HexColor('#172c45')
MUTED = colors.HexColor('#526073')
STUB = colors.HexColor('#f1eddf')
FONTS = Path(reportlab.__file__).resolve().parent / 'fonts'
registerFont(TTFont('TicketSans', str(FONTS / 'Vera.ttf')))
registerFont(TTFont('TicketSans-Bold', str(FONTS / 'VeraBd.ttf')))


class CanonicalParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.urls = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'link' and 'canonical' in attrs.get('rel', '').split():
            self.urls.append(attrs.get('href', ''))


def canonical_url():
    parser = CanonicalParser()
    parser.feed((ROOT / 'index.html').read_text(encoding='utf-8'))
    if len(parser.urls) != 1:
        raise ValueError('index.html must have exactly one canonical URL.')
    url = parser.urls[0]
    parts = urlsplit(url)
    if parts.scheme != 'https' or not parts.hostname or parts.query or parts.fragment:
        raise ValueError('Use the published HTTPS URL without a query or fragment.')
    if parts.username or parts.password or parts.hostname in {'localhost', '127.0.0.1', 'htmlpreview.github.io'}:
        raise ValueError('The ticket must link to the published website, not a preview.')
    return url


def draw_ticket(pdf, x, y, url):
    """Draw one 160 x 70 mm ticket at a PDF point coordinate."""
    pdf.saveState()
    pdf.translate(x, y)

    def rectangle(left, top, width, height, colour):
        pdf.setFillColor(colour)
        pdf.rect(left * mm, (HEIGHT_MM - top - height) * mm,
                 width * mm, height * mm, stroke=0, fill=1)

    def text(left, baseline, value, size, face='TicketSans', colour=INK, centred=False):
        pdf.setFillColor(colour)
        pdf.setFont(face, size)
        draw = pdf.drawCentredString if centred else pdf.drawString
        draw(left * mm, (HEIGHT_MM - baseline) * mm, value)

    rectangle(0, 0, WIDTH_MM, HEIGHT_MM, PAPER)
    rectangle(112, 13.2, 48, HEIGHT_MM - 13.2, STUB)
    rectangle(0, 0, WIDTH_MM, 12, BLUE)
    rectangle(0, 12, WIDTH_MM, 1.2, RED)
    text(6, 7.9, 'ELLENFOOT / ONLINE DESTINATIONS', 9.0, 'TicketSans-Bold', colors.white)
    text(136, 7.9, 'SCAN TO VISIT', 8.5, 'TicketSans-Bold', colors.white, centred=True)

    pdf.drawImage(str(ROOT / 'assets/ellenfoot-br-sign.png'),
                  6 * mm, (HEIGHT_MM - 19 - 26) * mm,
                  width=26 * mm, height=26 * mm, mask='auto')
    text(38, 27.5, 'Cumbrian', 21, 'TicketSans-Bold')
    text(38, 36.0, 'Railway Modeller', 17.5, 'TicketSans-Bold')
    text(38, 43.0, 'Model railways / making / open source', 7.2, colour=MUTED)

    pdf.setStrokeColor(colors.HexColor('#b8bdc2'))
    pdf.setLineWidth(0.2 * mm)
    pdf.line(6 * mm, (HEIGHT_MM - 50) * mm, 105 * mm, (HEIGHT_MM - 50) * mm)
    text(6, 55.2, 'YOUR CONNECTION TO THE WORKBENCH', 7.5, 'TicketSans-Bold', BLUE)
    parts = urlsplit(url)
    address_lines = [parts.netloc + '/', parts.path.lstrip('/')]
    for index, line in enumerate(address_lines):
        if stringWidth(line, 'TicketSans', 8.4) > 99 * mm:
            raise ValueError('The printed address needs a wider layout before regeneration.')
        text(6, 60.8 + index * 4.2, line, 8.4)

    # Keep the QR square, high contrast and clear of the ticket's decorative rule.
    # DENSO WAVE specifies a quiet zone of four modules on all four sides:
    # https://www.qrcode.com/en/howto/code.html
    qr_size = 39 * mm
    qr = QrCodeWidget(url, barLevel='M', barBorder=4,
                     barWidth=qr_size, barHeight=qr_size,
                     barFillColor=colors.black)
    drawing = Drawing(qr_size, qr_size)
    drawing.add(qr)
    rectangle(116.5, 18, 39, 39, colors.white)
    renderPDF.draw(drawing, pdf, 116.5 * mm, (HEIGHT_MM - 18 - 39) * mm)
    text(136, 62.0, 'KEEP FOR YOUR NEXT VISIT', 6.5, 'TicketSans-Bold', BLUE, centred=True)
    text(136, 66.3, 'WEBSITE SHARING TICKET', 5.7, colour=MUTED, centred=True)

    pdf.setStrokeColor(colors.HexColor('#aeb4b9'))
    pdf.setLineWidth(0.25 * mm)
    pdf.setDash(1.2 * mm, 1.1 * mm)
    pdf.line(112 * mm, 2 * mm, 112 * mm, (HEIGHT_MM - 14.8) * mm)
    pdf.setDash()
    pdf.setStrokeColor(BLUE)
    pdf.setLineWidth(0.3 * mm)
    pdf.rect(0.15 * mm, 0.15 * mm, (WIDTH_MM - 0.3) * mm,
             (HEIGHT_MM - 0.3) * mm, stroke=1, fill=0)
    pdf.linkURL(url, (0, 0, WIDTH_MM * mm, HEIGHT_MM * mm), relative=1, thickness=0)
    pdf.restoreState()


def make_canvas(path, page_size, url):
    pdf = canvas.Canvas(str(path), pagesize=page_size, pageCompression=1, invariant=1)
    pdf.setTitle('Cumbrian Railway Modeller - railway sharing ticket')
    pdf.setAuthor('Cumbrian Railway Modeller')
    pdf.setSubject('Website sharing ticket: ' + url)
    return pdf


def crop_marks(pdf, x, y):
    pdf.saveState()
    pdf.setStrokeColor(MUTED)
    pdf.setLineWidth(0.2)
    for horizontal in (0, WIDTH_MM * mm):
        for vertical in (0, HEIGHT_MM * mm):
            dx = -1 if horizontal == 0 else 1
            dy = -1 if vertical == 0 else 1
            pdf.line(x + horizontal + dx * mm, y + vertical,
                     x + horizontal + dx * 3 * mm, y + vertical)
            pdf.line(x + horizontal, y + vertical + dy * mm,
                     x + horizontal, y + vertical + dy * 3 * mm)
    pdf.restoreState()


def main():
    url = canonical_url()
    assets = ROOT / 'assets'
    png_path = assets / 'sharing-ticket.png'
    pdf_path = assets / 'sharing-ticket.pdf'
    with tempfile.TemporaryDirectory(prefix='railway-ticket-') as temporary:
        temporary = Path(temporary)
        single_pdf = temporary / 'ticket.pdf'
        pdf = make_canvas(single_pdf, (WIDTH_MM * mm, HEIGHT_MM * mm), url)
        draw_ticket(pdf, 0, 0, url)
        pdf.showPage()
        pdf.save()
        subprocess.run([
            'pdftoppm', '-png', '-singlefile', '-scale-to-x', str(PNG_WIDTH),
            '-scale-to-y', str(PNG_HEIGHT), str(single_pdf), str(temporary / 'ticket'),
        ], check=True)
        # Retain the exact rendered pixels and record the intended print resolution.
        with Image.open(temporary / 'ticket.png') as image:
            image.save(png_path, optimize=True, dpi=(304.8, 304.8))

    pdf = make_canvas(pdf_path, A4, url)
    pdf.setFont('TicketSans-Bold', 12)
    pdf.setFillColor(BLUE)
    pdf.drawString(25 * mm, 285 * mm, 'Cumbrian Railway Modeller / sharing tickets')
    pdf.setFont('TicketSans', 8)
    pdf.setFillColor(MUTED)
    pdf.drawString(25 * mm, 279 * mm, 'Print at 100% or Actual size. Each ticket is 160 x 70 mm. Cut at the corner marks.')
    for y_mm in (199, 116, 33):
        draw_ticket(pdf, 25 * mm, y_mm * mm, url)
        crop_marks(pdf, 25 * mm, y_mm * mm)
    pdf.setFont('TicketSans', 8)
    pdf.setFillColor(MUTED)
    pdf.drawString(25 * mm, 20 * mm, 'Scan the QR code or type the website address. All three tickets link to the same website.')
    pdf.showPage()
    pdf.save()
    print(f'Created {png_path.name} ({PNG_WIDTH} x {PNG_HEIGHT}) and {pdf_path.name} (A4, 3 tickets).')
    print(f'QR destination: {url}')


if __name__ == '__main__':
    main()
