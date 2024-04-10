## HESK API

### Pre-install
```bash
cp .env.example .env
vim .env # Change variables
poetry install
```
### Run
```bash
poetry run uvicorn main:app
```
Go to http://localhost:8000/docs