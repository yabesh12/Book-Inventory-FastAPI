"""
Note: to create a admin user
1. docker-compose run book_inventory bash
2. python
3.
from api.account.utils import get_password_hash
from models import User
from settings import get_db
session = get_db()
hashed_password = get_password_hash("admin")
admin_user = User(name="admin", email="admin@gmail.com", password=hashed_password, is_admin=True)
session.add(admin_user)
session.commit()
session.close()
"""

from api.account.utils import get_password_hash
from models import User
from settings import get_db


def create_admin_user():
    """
    To create the admin user
    :return: admin user
    """
    session = get_db()  # Get the database session

    # Create the admin user
    hashed_password = get_password_hash("admin")
    admin_user = User(name="admin", email="admin@gmail.com", password=hashed_password, is_admin=True)

    session.add(admin_user)  # Add the admin user to the session
    session.commit()  # Commit the changes to the database
    session.close()  # Close the session

    print("Admin user created successfully.")
    return admin_user


# Call the function to create the admin user
create_admin_user()


