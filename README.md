# Library Management System

A web-based library management application built with **Streamlit** and **MySQL**. It provides separate administrator and user experiences for managing a book catalogue, library accounts, book issue and return activity, and feedback.

## Features

### Administrator

- View dashboard metrics for books, users, issued books, and feedback.
- Review current issued-book records and book availability.
- Add, search, update, and delete books.
- Add, search, update, and delete user accounts.
- Add, view, update, and delete administrator accounts.
- Review user feedback and view its rating summary.

### Library users

- Create an account and sign in.
- Browse and search the book catalogue, including availability.
- Issue an available book and return the currently issued book.
- Submit feedback with a rating from 1 to 10.

Each user record can be associated with one book at a time.

## Technology

- Python 3.10 or newer
- Streamlit
- MySQL
- pandas
- MySQL Connector/Python

## Getting started

### 1. Prerequisites

Install Python 3.10 or newer and start a MySQL server. The MySQL account used by the app must be able to create the `Library` database and its tables, and read and write records.

### 2. Install Python dependencies

From the project directory, run:

```powershell
python -m pip install -r requirements.txt
```

### 3. Configure MySQL

The recommended local configuration is a Streamlit secrets file. Create `.streamlit/secrets.toml` in the project directory:

```toml
[mysql]
host = "localhost"
port = 3306
user = "root"
password = "YOUR_MYSQL_PASSWORD"
```

Alternatively, set these environment variables before starting the application:

| Variable | Description | Default |
| --- | --- | --- |
| `MYSQL_HOST` | MySQL server hostname | `localhost` |
| `MYSQL_PORT` | MySQL server port | `3306` |
| `MYSQL_USER` | MySQL username | `root` |
| `MYSQL_PASSWORD` | MySQL password | The current source code has a fallback; see the security note below. |

If both Streamlit secrets and environment variables are configured, values in `[mysql]` secrets take precedence.

### 4. Run the application

```powershell
python -m streamlit run app.py
```

Streamlit prints a local URL in the terminal; open it in your browser. On startup, the application creates the `Library` database and required tables if they do not already exist. It also inserts built-in sample accounts when the administrator or user table is empty.

## Database tables

| Table | Purpose |
| --- | --- |
| `BookRecord` | Book ID, title, author, and publisher |
| `UserRecord` | User ID, name, password, and the ID of the book currently issued to the user |
| `AdminRecord` | Administrator IDs and passwords |
| `Feedback` | Feedback text and rating |

## Project files

- `app.py` — Streamlit interface, login flows, dashboards, and library operations.
- `database.py` — MySQL configuration, connection handling, and database/table initialization.
- `requirements.txt` — Python package dependencies.

## Security notice

This project is intended as a learning/demo application and is **not ready for production use**. The current source contains a fallback MySQL password and built-in sample login credentials, and account passwords are stored as plain text. Before deploying or publishing a public copy, remove the hard-coded credentials, change any exposed passwords, and implement secure password hashing and appropriate access controls. Never commit `.streamlit/secrets.toml` or other files containing real credentials.
