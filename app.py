import os
import streamlit as st
from src.db import init_db
from src.users_repo import get_user_by_email, create_user
from src.rbac import ROLE_ADMIN

def seed_admin():
    admin_email = os.getenv("ADMIN_EMAIL")
    admin_pass = os.getenv("ADMIN_PASSWORD")

    if not admin_email or not admin_pass:
        return

    existing = get_user_by_email(admin_email)
    if existing is None:
        create_user(admin_email, admin_pass, ROLE_ADMIN, active=True)

def main():
    init_db()
    seed_admin()
    st.title("PlaygroundHub")
    st.write("Use o menu lateral para navegar.")

if __name__ == "__main__":
    main()
