#!/usr/bin/env python3
"""Regenerate the sharing ticket PNG, A4 PDF and QR SVG from the canonical URL.

Authoring dependencies: Python 3, ReportLab, Pillow and Poppler (pdftoppm).
The website serves the finished files and needs none of these at runtime.
"""

from html.parser import HTMLParser
from pathlib import Path
import subprocess
import tempfile
from urllib.parse import urlsplit
from xml.etree import ElementTree

from PIL import Image
import reportlab
from reportlab.graphics import renderPDF, renderSVG
from reportlab.graphics.barcode.qr import QrCodeWidget
from reportlab.graphics.shapes import Drawing, Rect
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfbase.pdfmetrics import registerFont, stringWidth
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas


ROOT = Path(__file__).resolve().parents[1]
WIDTH_MM, HEIGHT_MM = 160, 70
PNG_WIDTH, PNG_HEIGHT = 1920, 840
RED = colors.HexColor('#ad302b')
PAPER = colors.HexColor('#fff8e4')
STAMP = colors.HexColor('#59456d')
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


def qr_drawing(url, size=39 * mm):
    """Use one square QR drawing for the downloads and live-page SVG."""
    drawing = Drawing(size, size)
    drawing.add(Rect(0, 0, size, size, fillColor=colors.white, strokeColor=None))
    # Keep a four-module quiet zone on all sides, as specified by DENSO WAVE:
    # https://www.qrcode.com/en/howto/code.html
    drawing.add(QrCodeWidget(url, barLevel='M', barBorder=4,
                            barWidth=size, barHeight=size,
                            barFillColor=colors.black))
    return drawing


def write_qr_svg(path, url):
    # ReportLab rounds its SVG viewBox and vertical transform to integers.
    # Integer drawing dimensions preserve the complete four-module quiet zone.
    namespace = 'http://www.w3.org/2000/svg'
    svg = ElementTree.fromstring(renderSVG.drawToString(qr_drawing(url, 256)))
    for tag, value in (
        ('title', 'Cumbrian Railway Modeller website QR code'),
        ('desc', 'Scan to visit ' + url),
    ):
        node = svg.find('{' + namespace + '}' + tag)
        if node is None:
            node = ElementTree.SubElement(svg, '{' + namespace + '}' + tag)
        node.text = value
    ElementTree.register_namespace('', namespace)
    path.write_bytes(ElementTree.tostring(svg, encoding='utf-8', xml_declaration=True))


def draw_ticket(pdf, x, y, url):
    """Draw one 160 x 70 mm ticket at a PDF point coordinate."""
    pdf.saveState()
    pdf.translate(x, y)

    def rectangle(left, top, width, height, colour):
        pdf.setFillColor(colour)
        pdf.rect(left * mm, (HEIGHT_MM - top - height) * mm,
                 width * mm, height * mm, stroke=0, fill=1)

    def text(left, baseline, value, size, face='TicketSans', colour=RED, centred=False):
        pdf.setFillColor(colour)
        pdf.setFont(face, size)
        draw = pdf.drawCentredString if centred else pdf.drawString
        draw(left * mm, (HEIGHT_MM - baseline) * mm, value)

    def rule(left, top, right, bottom):
        pdf.line(left * mm, (HEIGHT_MM - top) * mm,
                 right * mm, (HEIGHT_MM - bottom) * mm)

    rectangle(0, 0, WIDTH_MM, HEIGHT_MM, PAPER)
    rectangle(0, 0, WIDTH_MM, 13, RED)
    rectangle(0, 63, WIDTH_MM, 7, RED)
    text(6, 6.8, 'Cumbrian Railway Modeller', 12, 'TicketSans-Bold', PAPER)
    text(6, 11.0, 'Online destinations', 7.5, colour=PAPER)
    text(136, 8.4, 'SHARING TICKET', 8.3, 'TicketSans-Bold', PAPER, centred=True)

    text(6, 23.9, 'To', 10.5, 'TicketSans-Bold')
    text(20, 25.5, 'The workbench', 19.5, 'TicketSans-Bold')
    text(20, 31.1, 'Model railways / making / open source', 7.2, colour=STAMP)
    pdf.drawImage(str(ROOT / 'assets/ellenfoot-br-sign.png'),
                  89 * mm, (HEIGHT_MM - 16.5 - 16) * mm,
                  width=16 * mm, height=16 * mm, mask='auto')

    pdf.setStrokeColor(RED)
    pdf.setLineWidth(0.35 * mm)
    rule(112, 13, 112, 63)
    rule(0, 35, 112, 35)
    rule(0, 46.5, 112, 46.5)
    rule(41, 35, 41, 46.5)
    rule(85, 35, 85, 46.5)
    text(6, 39.3, 'From', 7.3)
    text(6, 44.1, 'ELLENFOOT', 9.5, 'TicketSans-Bold', STAMP)
    text(45, 39.3, 'Via', 7.3)
    text(45, 44.1, 'BLOG & PROJECTS', 8.2, 'TicketSans-Bold', STAMP)
    text(89, 39.3, 'Valid', 7.3)
    text(89, 44.1, 'EVERY VISIT', 7.6, 'TicketSans-Bold', STAMP)

    text(6, 51.0, 'Website', 7.3)
    parts = urlsplit(url)
    address_lines = [parts.netloc + '/', parts.path.lstrip('/')]
    for index, line in enumerate(address_lines):
        if stringWidth(line, 'TicketSans', 8.4) > 99 * mm:
            raise ValueError('The printed address needs a wider layout before regeneration.')
        text(6, 55.7 + index * 4.2, line, 8.4, colour=STAMP)

    renderPDF.draw(qr_drawing(url), pdf, 116.5 * mm, (HEIGHT_MM - 16.5 - 39) * mm)
    text(136, 60.1, 'SCAN TO VISIT', 7.1, 'TicketSans-Bold', centred=True)
    text(6, 67.8, 'Keep for your next visit', 8.2, colour=PAPER)
    text(136, 68.0, 'Return', 10.5, colour=PAPER, centred=True)

    pdf.setStrokeColor(RED)
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
    pdf.setStrokeColor(STAMP)
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
    svg_path = assets / 'sharing-ticket-qr.svg'
    write_qr_svg(svg_path, url)
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
    pdf.setFillColor(RED)
    pdf.drawString(25 * mm, 285 * mm, 'Cumbrian Railway Modeller / sharing tickets')
    pdf.setFont('TicketSans', 8)
    pdf.setFillColor(STAMP)
    pdf.drawString(25 * mm, 279 * mm, 'Print at 100% or Actual size. Each ticket is 160 x 70 mm. Cut at the corner marks.')
    for y_mm in (199, 116, 33):
        draw_ticket(pdf, 25 * mm, y_mm * mm, url)
        crop_marks(pdf, 25 * mm, y_mm * mm)
    pdf.setFont('TicketSans', 8)
    pdf.setFillColor(STAMP)
    pdf.drawString(25 * mm, 20 * mm, 'Scan the QR code or type the website address. All three tickets link to the same website.')
    pdf.showPage()
    pdf.save()
    print(f'Created {png_path.name} ({PNG_WIDTH} x {PNG_HEIGHT}), '
          f'{pdf_path.name} (A4, 3 tickets) and {svg_path.name}.')
    print(f'QR destination: {url}')


if __name__ == '__main__':
    main()
