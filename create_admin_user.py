from main import User, get_db

def create_admin_user():
    """
    To create the admin user
    :return: admin user
    """
    session = get_db()  # Get the database session

    # Create the admin user
    admin_user = User(
        name="admin",
        email="admin@gmail.com",
        password="admin",
        is_admin=True
    )

    session.add(admin_user)  # Add the admin user to the session
    session.commit()  # Commit the changes to the database
    session.close()  # Close the session

    print("Admin user created successfully.")
    return admin_user

# Call the function to create the admin user
create_admin_user()
