from fastapi import FastAPI
from .api.routes import router  # The dot means "current package"

app = FastAPI(
    title="Timetable Generator",
    description="Deterministic timetable generation system",
    version="2.0.0",
)

app.include_router(router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)