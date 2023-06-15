from fastapi import FastAPI

from api.account import account_api_endpoints

# Dependency: Get DB Session


# FastAPI App
from api.book import book_api_endpoints

app = FastAPI()

# Include routers for account-related API endpoints
app.include_router(account_api_endpoints.router)

# Include routers for book-related API endpoints
app.include_router(book_api_endpoints.router)
