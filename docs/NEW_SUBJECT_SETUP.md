# Quick Setup Guide - New Subject

## For Testing New Subject (e.g., Computer Networks)

### Option A: New Database (Recommended)

```bash
# 1. Create new database
createdb kripaa_networks

# 2. Update .env temporarily
DATABASE_URL=postgresql://user:pass@localhost/kripaa_networks

# 3. Initialize tables
python -c "from utils.db import init_db; import asyncio; asyncio.run(init_db())"

# 4. Add your PDFs to static/
#    - static/pyqs/ → networks PYQ PDFs
#    - static/syllabus/ → networks syllabus

# 5. Run pipeline
python -m src.cli --target-year 2025
```

### Option B: Same Database with Cleanup

```bash
# 1. Clean existing data (CAUTION!)
python tests/cleanup_database.py

# 2. Replace PDFs in static/
#    - Remove old PDFs
#    - Add new subject PDFs

# 3. Run pipeline
python -m src.cli --target-year 2025
```

## Pre-Test Checklist

- [ ] Database created/cleaned
- [ ] .env updated with correct DATABASE_URL
- [ ] GOOGLE_API_KEY set in .env
- [ ] PYQ PDFs in static/pyqs/
- [ ] Syllabus PDF in static/syllabus/
- [ ] output/ folder exists

## Run Tests

```bash
# Full pipeline test
python tests/test_e2e_pipeline.py

# Or run directly
python -m src.cli --target-year 2025
```

## Expected Output

```
output/
├── generated_paper.pdf       # 27 questions, 130 marks
├── generated_paper.md        # Markdown version
├── comprehensive_report.pdf  # Full analysis
└── comprehensive_report.md   # Report markdown
```

## Troubleshooting

### Issue: "No PYQ PDFs found"
**Fix**: Add PDFs to `static/pyqs/`

### Issue: "Database connection failed"
**Fix**: Check DATABASE_URL in .env, ensure PostgreSQL is running

### Issue: "GOOGLE_API_KEY not set"
**Fix**: Add key to .env file

### Issue: "No candidates generated"
**Fix**: Check if trend analysis completed, verify snapshot_id

## Database Commands

```bash
# List databases
psql -l

# Drop database
dropdb kripaa_old_subject

# Create database
createdb kripaa_new_subject

# Connect to database
psql kripaa_new_subject
```
