# Library Management System

A Streamlit web application for managing books, users, administrators, issued books, and feedback using MySQL.

## Requirements

- Python 3.10 or newer
- MySQL Server

## Run

Install dependencies:

```powershell
python -m pip install -r requirements.txt
```

Configure MySQL credentials in `.streamlit/secrets.toml`:

```toml
[mysql]
host = "localhost"
port = 3306
user = "root"
password = "YOUR_MYSQL_PASSWORD"
```

Start the application:

```powershell
python -m streamlit run app.py
```
