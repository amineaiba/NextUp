from fastapi import FastAPI

app = FastAPI(title="Virtual Queue")


@app.get("/health")
async def health():
    return {"status": "ok"}
