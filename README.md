# Book Inventory FastAPI

### User Module
1. Register User
2. Login User with JWT Authentication enabled
3. Activating/Deactivating users by Admin only


### Book Module
1. CRUD Category by Admin only
2. CRUD Book by Admin only
3. Borrow Book
4. Return Book 
5. Book rating by borrowed users only
6. Book History/User History by Admin only
7. Book/Category Search

### Notes
All APIs (user except login and register) require JWT authorization token
in the request header for authentication.

------------------------


### Build and run the Project
``docker-compose up --build``

### Stop the project
``docker-compose down``


### Generate migrations
``alembic revision --autogenerate -m "description about migration"``


### Apply migrations on Database schema
``alembic upgrade head``

----------------
