import pandas as pd
import streamlit as st

from database import get_connection, initialize_database


st.set_page_config(
    page_title="Library Management System",
    page_icon="",
    layout="wide",
)

st.markdown(
    """
    <style>
    .main { background-color: #f7f9fc; }
    .block-container { padding-top: 2rem; }
    div[data-testid="stMetric"] {
        background-color: black;
        border: 1px solid #e6eaf0;
        border-radius: 12px;
        padding: 16px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data(ttl=2)
def fetch_query(query, params=None):
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    cursor.execute(query, params or ())
    rows = cursor.fetchall()
    cursor.close()
    connection.close()
    return pd.DataFrame(rows)


def execute_query(query, params=None):
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute(query, params or ())
    connection.commit()
    cursor.close()
    connection.close()
    fetch_query.clear()


def logout():
    st.session_state.logged_in = False
    st.session_state.role = None
    st.session_state.user_id = None
    st.session_state.admin_id = None
    st.rerun()


if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.role = None

initialization_error = initialize_database()
if initialization_error:
    st.error("Unable to connect to MySQL.")
    st.code(initialization_error)
    st.stop()


def login_page():
    st.title("Library Management System")
    st.caption("Manage books, users, issuing, returns, and feedback")

    tab_admin, tab_user = st.tabs(["Administrator Login", "User Login"])

    with tab_admin:
        with st.form("admin_login"):
            admin_id = st.text_input("Admin ID")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Login", use_container_width=True)

        if submitted:
            connection = get_connection()
            cursor = connection.cursor(dictionary=True)
            cursor.execute(
                "SELECT * FROM AdminRecord WHERE AdminID = %s AND Password = %s",
                (admin_id, password),
            )
            account = cursor.fetchone()
            cursor.close()
            connection.close()
            if account:
                st.session_state.logged_in = True
                st.session_state.role = "admin"
                st.session_state.admin_id = admin_id
                st.rerun()
            else:
                st.error("Invalid Admin ID or password.")

    with tab_user:
        create_tab, login_tab = st.tabs(["Create Account", "Login"])
        with create_tab:
            with st.form("create_user"):
                user_id = st.text_input("User ID")
                name = st.text_input("Name")
                password = st.text_input("Password", type="password")
                submitted = st.form_submit_button("Create Account", use_container_width=True)

            if submitted:
                if not user_id or not name or not password:
                    st.error("All fields are required.")
                else:
                    try:
                        execute_query(
                            "INSERT INTO UserRecord (UserID, UserName, Password, BookID) VALUES (%s, %s, %s, NULL)",
                            (user_id, name, password),
                        )
                        st.success("Account created successfully.")
                    except Exception:
                        st.error("User ID already exists.")

        with login_tab:
            with st.form("user_login"):
                user_id = st.text_input("User ID")
                password = st.text_input("Password", type="password")
                submitted = st.form_submit_button("Login", use_container_width=True)

            if submitted:
                connection = get_connection()
                cursor = connection.cursor(dictionary=True)
                cursor.execute(
                    "SELECT * FROM UserRecord WHERE UserID = %s AND Password = %s",
                    (user_id, password),
                )
                account = cursor.fetchone()
                cursor.close()
                connection.close()
                if account:
                    st.session_state.logged_in = True
                    st.session_state.role = "user"
                    st.session_state.user_id = user_id
                    st.rerun()
                else:
                    st.error("Invalid User ID or password.")


def overview_metrics():
    books = fetch_query("SELECT COUNT(*) AS total FROM BookRecord").iloc[0]["total"]
    users = fetch_query("SELECT COUNT(*) AS total FROM UserRecord").iloc[0]["total"]
    issued = fetch_query(
        "SELECT COUNT(*) AS total FROM UserRecord WHERE BookID IS NOT NULL"
    ).iloc[0]["total"]
    feedback = fetch_query("SELECT COUNT(*) AS total FROM Feedback").iloc[0]["total"]

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Books", int(books))
    col2.metric("Users", int(users))
    col3.metric("Issued Books", int(issued))
    col4.metric("Feedback Entries", int(feedback))


def admin_dashboard():
    st.sidebar.success(f"Admin: {st.session_state.admin_id}")
    if st.sidebar.button("Logout", use_container_width=True):
        logout()

    page = st.sidebar.radio(
        "Navigation",
        ["Overview", "Books", "Users", "Administrators", "Feedback"],
    )

    st.title(page)

    if page == "Overview":
        overview_metrics()
        st.subheader("Issued Book Records")
        issued = fetch_query(
            """
            SELECT u.UserID, u.UserName, b.BookID, b.BookName, b.Author, b.Publisher
            FROM UserRecord u
            JOIN BookRecord b ON u.BookID = b.BookID
            ORDER BY u.UserID
            """
        )
        st.dataframe(issued if not issued.empty else pd.DataFrame(), use_container_width=True)

        st.subheader("Availability")
        availability = fetch_query(
            """
            SELECT
                COUNT(*) AS TotalBooks,
                SUM(CASE WHEN u.BookID IS NULL THEN 1 ELSE 0 END) AS AvailableBooks
            FROM BookRecord b
            LEFT JOIN UserRecord u ON b.BookID = u.BookID
            """
        )
        if availability.empty:
            st.info("No data available.")
        else:
            st.dataframe(availability, use_container_width=True)

    elif page == "Books":
        action = st.tabs(["View & Search", "Add", "Update", "Delete"])

        with action[0]:
            books = fetch_query(
                """
                SELECT b.*, u.UserID AS IssuedTo
                FROM BookRecord b
                LEFT JOIN UserRecord u ON b.BookID = u.BookID
                ORDER BY b.BookID
                """
            )
            search = st.text_input("Search by ID, title, author, or publisher")
            if search:
                mask = books.astype(str).apply(
                    lambda column: column.str.contains(search, case=False, na=False)
                ).any(axis=1)
                books = books[mask]
            st.dataframe(books, use_container_width=True)

        with action[1]:
            with st.form("add_book"):
                book_id = st.text_input("Book ID")
                title = st.text_input("Book Name")
                author = st.text_input("Author")
                publisher = st.text_input("Publisher")
                submitted = st.form_submit_button("Add Book")
            if submitted:
                if not all([book_id, title, author, publisher]):
                    st.error("All fields are required.")
                else:
                    try:
                        execute_query(
                            "INSERT INTO BookRecord VALUES (%s, %s, %s, %s)",
                            (book_id, title, author, publisher),
                        )
                        st.success("Book added.")
                        st.rerun()
                    except Exception:
                        st.error("Book ID already exists.")

        with action[2]:
            books = fetch_query("SELECT * FROM BookRecord")
            if books.empty:
                st.info("No books available.")
            else:
                book_id = st.selectbox("Book", books["BookID"].tolist())
                selected = books.loc[books["BookID"] == book_id].iloc[0]
                with st.form("update_book"):
                    title = st.text_input("Book Name", selected["BookName"])
                    author = st.text_input("Author", selected["Author"])
                    publisher = st.text_input("Publisher", selected["Publisher"])
                    submitted = st.form_submit_button("Update Book")
                if submitted:
                    execute_query(
                        "UPDATE BookRecord SET BookName=%s, Author=%s, Publisher=%s WHERE BookID=%s",
                        (title, author, publisher, book_id),
                    )
                    st.success("Book updated.")
                    st.rerun()

        with action[3]:
            books = fetch_query("SELECT BookID, BookName FROM BookRecord")
            if books.empty:
                st.info("No books available.")
            else:
                book_id = st.selectbox("Select Book", books["BookID"].tolist(), key="delete_book")
                if st.button("Delete Book", type="primary"):
                    execute_query("UPDATE UserRecord SET BookID=NULL WHERE BookID=%s", (book_id,))
                    execute_query("DELETE FROM BookRecord WHERE BookID=%s", (book_id,))
                    st.success("Book deleted.")
                    st.rerun()

    elif page == "Users":
        action = st.tabs(["View & Search", "Add", "Update", "Delete"])
        with action[0]:
            users = fetch_query(
                """
                SELECT u.UserID, u.UserName, u.Password, u.BookID,
                       b.BookName
                FROM UserRecord u
                LEFT JOIN BookRecord b ON u.BookID = b.BookID
                ORDER BY u.UserID
                """
            )
            search = st.text_input("Search user")
            if search:
                mask = users.astype(str).apply(
                    lambda column: column.str.contains(search, case=False, na=False)
                ).any(axis=1)
                users = users[mask]
            st.dataframe(users, use_container_width=True)

        with action[1]:
            with st.form("add_user"):
                user_id = st.text_input("User ID")
                name = st.text_input("Name")
                password = st.text_input("Password", type="password")
                submitted = st.form_submit_button("Add User")
            if submitted:
                try:
                    execute_query(
                        "INSERT INTO UserRecord VALUES (%s, %s, %s, NULL)",
                        (user_id, name, password),
                    )
                    st.success("User added.")
                    st.rerun()
                except Exception:
                    st.error("User ID already exists or fields are invalid.")

        with action[2]:
            users = fetch_query("SELECT * FROM UserRecord")
            if users.empty:
                st.info("No users available.")
            else:
                user_id = st.selectbox("User", users["UserID"].tolist())
                selected = users.loc[users["UserID"] == user_id].iloc[0]
                with st.form("update_user"):
                    name = st.text_input("Name", selected["UserName"])
                    password = st.text_input("Password", selected["Password"], type="password")
                    submitted = st.form_submit_button("Update User")
                if submitted:
                    execute_query(
                        "UPDATE UserRecord SET UserName=%s, Password=%s WHERE UserID=%s",
                        (name, password, user_id),
                    )
                    st.success("User updated.")
                    st.rerun()

        with action[3]:
            users = fetch_query("SELECT UserID, UserName FROM UserRecord")
            if not users.empty:
                user_id = st.selectbox("Select User", users["UserID"].tolist(), key="delete_user")
                if st.button("Delete User", type="primary"):
                    execute_query("DELETE FROM UserRecord WHERE UserID=%s", (user_id,))
                    st.success("User deleted.")
                    st.rerun()

    elif page == "Administrators":
        admins = fetch_query("SELECT * FROM AdminRecord")
        st.dataframe(admins, use_container_width=True)
        tab_add, tab_update, tab_delete = st.tabs(["Add", "Update", "Delete"])
        with tab_add:
            with st.form("add_admin"):
                admin_id = st.text_input("Admin ID")
                password = st.text_input("Password", type="password")
                submitted = st.form_submit_button("Add Admin")
            if submitted:
                try:
                    execute_query(
                        "INSERT INTO AdminRecord VALUES (%s, %s)",
                        (admin_id, password),
                    )
                    st.success("Admin added.")
                    st.rerun()
                except Exception:
                    st.error("Admin ID already exists.")
        with tab_update:
            if not admins.empty:
                admin_id = st.selectbox("Admin", admins["AdminID"].tolist())
                password = st.text_input("New Password", type="password")
                if st.button("Update Password"):
                    execute_query(
                        "UPDATE AdminRecord SET Password=%s WHERE AdminID=%s",
                        (password, admin_id),
                    )
                    st.success("Password updated.")
                    st.rerun()
        with tab_delete:
            if not admins.empty:
                admin_id = st.selectbox("Admin to Delete", admins["AdminID"].tolist(), key="delete_admin")
                if st.button("Delete Admin", type="primary"):
                    execute_query("DELETE FROM AdminRecord WHERE AdminID=%s", (admin_id,))
                    st.success("Admin deleted.")
                    st.rerun()

    elif page == "Feedback":
        feedback = fetch_query("SELECT * FROM Feedback")
        st.dataframe(feedback if not feedback.empty else pd.DataFrame(), use_container_width=True)
        if not feedback.empty:
            st.subheader("Rating Summary")
            ratings = feedback.copy()
            ratings["Rating"] = pd.to_numeric(ratings["Rating"], errors="coerce")
            st.bar_chart(ratings.set_index("Feedback")["Rating"])


def user_dashboard():
    st.sidebar.success(f"User: {st.session_state.user_id}")
    if st.sidebar.button("Logout", use_container_width=True):
        logout()

    page = st.sidebar.radio("Navigation", ["Dashboard", "Issue / Return", "Feedback"])
    st.title(page)

    if page == "Dashboard":
        overview_metrics()
        st.subheader("Book Catalogue")
        books = fetch_query(
            """
            SELECT b.BookID, b.BookName, b.Author, b.Publisher,
                   CASE WHEN u.UserID IS NULL THEN 'Available' ELSE 'Issued' END AS Status
            FROM BookRecord b
            LEFT JOIN UserRecord u ON b.BookID = u.BookID
            ORDER BY b.BookID
            """
        )
        search = st.text_input("Search catalogue")
        if search:
            books = books[
                books.astype(str).apply(
                    lambda column: column.str.contains(search, case=False, na=False)
                ).any(axis=1)
            ]
        st.dataframe(books if not books.empty else pd.DataFrame(), use_container_width=True)

    elif page == "Issue / Return":
        user_id = st.session_state.user_id
        issued = fetch_query(
            """
            SELECT b.BookID, b.BookName, b.Author, b.Publisher
            FROM UserRecord u
            JOIN BookRecord b ON u.BookID = b.BookID
            WHERE u.UserID = %s
            """,
            (user_id,),
        )

        if issued.empty:
            st.info("You do not have an issued book.")
            available = fetch_query(
                """
                SELECT b.*
                FROM BookRecord b
                LEFT JOIN UserRecord u ON b.BookID = u.BookID
                WHERE u.UserID IS NULL
                ORDER BY b.BookID
                """
            )
            if available.empty:
                st.warning("No books are currently available.")
            else:
                book_id = st.selectbox(
                    "Available Book",
                    available["BookID"].tolist(),
                    format_func=lambda value: (
                        f"{value} - {available.loc[available['BookID'] == value, 'BookName'].iloc[0]}"
                    ),
                )
                if st.button("Issue Book", type="primary"):
                    execute_query(
                        "UPDATE UserRecord SET BookID=%s WHERE UserID=%s",
                        (book_id, user_id),
                    )
                    st.success("Book issued successfully.")
                    st.rerun()
        else:
            record = issued.iloc[0]
            st.success(f"Issued: {record['BookName']}")
            st.write(f"**Author:** {record['Author']}")
            st.write(f"**Publisher:** {record['Publisher']}")
            if st.button("Return Book", type="primary"):
                execute_query(
                    "UPDATE UserRecord SET BookID=NULL WHERE UserID=%s",
                    (user_id,),
                )
                st.success("Book returned successfully.")
                st.rerun()

    elif page == "Feedback":
        with st.form("feedback"):
            feedback = st.text_area("Your Feedback")
            rating = st.slider("Rating", 1, 10, 8)
            submitted = st.form_submit_button("Submit")
        if submitted:
            if not feedback.strip():
                st.error("Feedback cannot be empty.")
            else:
                try:
                    execute_query(
                        "INSERT INTO Feedback (Feedback, Rating) VALUES (%s, %s)",
                        (feedback.strip(), str(rating)),
                    )
                    st.success("Thank you for your feedback.")
                    st.rerun()
                except Exception:
                    st.error("This feedback already exists.")


if not st.session_state.logged_in:
    login_page()
elif st.session_state.role == "admin":
    admin_dashboard()
elif st.session_state.role == "user":
    user_dashboard()
