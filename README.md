# Resume Builder

Generates a PDF resume from `data.json` using a LaTeX template.

## Setup (one-time)

```
brew install tectonic
```

## Usage

Edit `data.json` with your content, then run:

```
python3 builder.py
```

This writes `output/akash_kumar.tex` and `output/akash_kumar.pdf` every time.

Other options:

```
python3 builder.py --no-pdf         # only generate the .tex file, skip PDF compilation
python3 builder.py -i other.json    # use a different data file
python3 builder.py -o out/cv.tex    # customize the output path
```
# resume-template
