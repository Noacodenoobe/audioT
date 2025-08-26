from fastapi import FastAPI

app = FastAPI()

@app.get('/health')
def health() -> dict:
    """Simple health check endpoint."""
    return {'status': 'ok'}
