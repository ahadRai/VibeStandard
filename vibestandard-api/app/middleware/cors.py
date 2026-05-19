from fastapi.middleware.cors import CORSMiddleware


def add_cors_middleware(app, settings):
    origins = [o.strip() for o in settings.cors_origins.split(",")]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=False,
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type", "Accept"],
        max_age=600,
    )
