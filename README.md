# Book Inventory FastAPI

### User Module
1. Register User
2. Login User with JWT Authentication


### Book Module
1. CRUD Book by Admin only
2. Borrow Book
3. Return Book 
4. Book History/User History by Admin only



### Build and run the Project
``docker-compose up --build``



### Generate migrations
``alembic revision --autogenerate -m "description about migration"``


### Apply migrations on Database schema
``alembic upgrade head``
