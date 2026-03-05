from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import engine, Base
from routers import systems, datasets, evaluations, experiments

# Create all tables on startup
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="AI Evaluation & Benchmarking Platform",
    description="Automated evaluation framework for AI systems",
    version="1.0.0",
)

# CORS – allow the Vite dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(systems.router)
app.include_router(datasets.router)
app.include_router(evaluations.router)
app.include_router(experiments.router)


@app.get("/")
def root():
    return {"message": "AI Evaluation & Benchmarking Platform API", "version": "1.0.0"}
