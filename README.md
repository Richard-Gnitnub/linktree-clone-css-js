# Cumbrian Railway Modeller links

A small, dependency-free personal link page, inspired by the graphic style of British Rail timetables of the 1970s. It uses original HTML/CSS rather than reproducing a period timetable or bundling a licensed Rail Alphabet font.

## Local preview

Open index.html in a browser. No build step or package installation is required. The page is deployed to GitHub Pages on pushes to main.

## Editing destinations

Edit each service-link href in index.html. The adjacent Copy link button automatically copies the address from that link, so the destination is defined only once.

The Blog button opens the Modelling Blog on Rich B Modeller, not the shop homepage. The original template's YouTube URL was an unrelated placeholder and has been omitted until a real channel address is supplied.

## Checks

Run these commands with Node.js 22 or later:

- node --check app.js
- node --test tests/*.test.mjs

GitHub Actions also runs these checks for pull requests.

## Railway sharing ticket

The Take a ticket section uses cream and red railway ticket styling with
live text, a QR code and download links. It offers a 1920 x 840 PNG for sharing
and an A4 PDF with three 160 x 70 mm landscape tickets and cutting marks.
The downloads match the section's colours and ruled panels, and include the
original Ellenfoot sign, a readable website address and a QR code pointing to
the published website. They work without JavaScript or an external QR service.

The single source for the ticket destination is the canonical link in
`index.html`. The generator never takes the address from a preview or the
visitor's current browser URL. If the published address or artwork changes,
regenerate the PNG, PDF and on-page QR SVG, then scan-check their QR codes
before committing:

```sh
python3 scripts/generate_ticket.py
```

The generator creates `assets/sharing-ticket-qr.svg` with the same QR generator
as the downloads, with a white background and a four-module quiet zone.

Regeneration requires ReportLab, Pillow and Poppler (`pdftoppm`). These are
authoring tools only; the website still needs no build step or dependencies.
Install the Python packages in a virtual environment with
`python3 -m pip install reportlab Pillow`, and install Poppler using your
system package manager. Print the PDF at 100% or Actual size.

## Parcels office

Platform 4 is a static catalogue of useful guides and finished downloads. Its
yellow and red sign uses a code-drawn Red Star parcels mark in
`assets/red-star-parcels.svg`, with live heading text and the site's existing
typefaces. The supplied signage sheet is a visual reference, not a bundled
site asset.

The initial catalogue links to Rich B Modeller's published
[FreeCAD bevel-gear guide](https://richbmodeller.com/blogs/news/freecad) and the
two sharing-ticket files described above. The guide opens its original page;
the PNG and PDF links download the local files. Source links lead to the ticket
generator. All entries work without JavaScript.

To add a resource, edit the `parcel-list` in `index.html`. Give it a clear name,
short description, format and any relevant printing, scale or software details.
Use a maintained file, release or guide URL, and label the action to match:
**Download PDF** for a file, **Read guide** or **View releases** for a page.
Only use the `download` attribute for local files. Include version, compatibility
and licence information when the source provides it; do not guess missing
details or list unfinished resources. The current resources have no supplied
version or explicit reuse licence, so no such claims appear in the catalogue.

## Browser identity and social sharing

A small code-drawn mark derived from the Ellenfoot sign supplies the SVG
favicon, the ICO's 16, 32 and 48 pixel sizes, and a 180 pixel Apple touch icon.
The 1200 x 630 sharing card uses the original sign artwork and the site's
colours without changing the source image.

Regenerate these assets with:

```sh
python3 scripts/generate_brand_assets.py
```

This uses the same ReportLab, Pillow and Poppler authoring tools as the ticket
generator. Check the small icons against light and dark browser backgrounds
and inspect the sharing card after regeneration.

The favicon links use relative paths for the GitHub Pages project directory.
Open Graph and social card metadata in `index.html` use the published HTTPS
page and image addresses, including descriptive image alternative text. If
the published address changes, update these addresses and the canonical link.

New sharing artwork becomes available at its published URL after merge and
GitHub Pages deployment. Social platforms manage their own preview caches,
so an existing preview may take time to refresh.

## Feature requests

Use **New issue > Feature request** to describe the visitor benefit, proposed
behaviour, acceptance criteria and any content needed. The reusable form lives
in `.github/ISSUE_TEMPLATE/feature_request.yml` and applies the `enhancement`
label. Backlog suggestions are proposals; they do not set a delivery date.
