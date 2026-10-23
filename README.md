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
