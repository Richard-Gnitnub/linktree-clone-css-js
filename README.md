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

The Take a ticket section offers a PNG for sharing and an A4 PDF with three
160 x 70 mm tickets and cutting marks. Both files include the Ellenfoot sign,
a readable website address and a QR code pointing to the published website.
The downloads work without JavaScript or an external QR-code service.

The single source for the ticket destination is the canonical link in
`index.html`. The generator never takes the address from a preview or the
visitor's current browser URL. If the published address or artwork changes,
regenerate both files and scan-check their QR codes before committing:

```sh
python3 scripts/generate_ticket.py
```

Regeneration requires ReportLab, Pillow and Poppler (`pdftoppm`). These are
authoring tools only; the website still needs no build step or dependencies.
Install the Python packages in a virtual environment with
`python3 -m pip install reportlab Pillow`, and install Poppler using your
system package manager. Print the PDF at 100% or Actual size.

## Feature requests

Use **New issue > Feature request** to describe the visitor benefit, proposed
behaviour, acceptance criteria and any content needed. The reusable form lives
in `.github/ISSUE_TEMPLATE/feature_request.yml` and applies the `enhancement`
label. Backlog suggestions are proposals; they do not set a delivery date.
