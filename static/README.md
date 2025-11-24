# Kripaa - Static Files

This directory contains the input files for the exam generation pipeline.

## Structure

```
static/
├── py/
│   ├── 2023.pdf    # Past question paper from 2023
│   ├── 2022.pdf    # Past question paper from 2022
│   └── ...         # Other years
└── syllabus/
    └── syllabus.pdf # Course syllabus PDF
```

## Usage

1. Place all past question paper PDFs in `static/pyq/`
2. Place the course syllabus PDF in `static/syllabus/`
3. Run the pipeline:

```bash
python -m src.cli --target-year 2025
```

The pipeline will automatically process all PDFs in these directories.
