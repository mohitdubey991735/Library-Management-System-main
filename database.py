import mysql.connector
import streamlit as st
import os


def mysql_config():
    config = {}
    try:
        config = dict(st.secrets["mysql"])
    except Exception:
        pass

    return {
        "host": config.get("host") or os.getenv("MYSQL_HOST", "localhost"),
        "port": int(config.get("port") or os.getenv("MYSQL_PORT", "3306")),
        "user": config.get("user") or os.getenv("MYSQL_USER", "root"),
        "password": config.get("password")
        or os.getenv("MYSQL_PASSWORD")
        or "8962",
    }


def get_connection():
    config = mysql_config()
    return mysql.connector.connect(
        host=config["host"],
        port=config["port"],
        user=config["user"],
        password=config["password"],
        database="Library",
    )


def initialize_database():
    try:
        config = mysql_config()
        connection = mysql.connector.connect(
            host=config["host"],
            port=config["port"],
            user=config["user"],
            password=config["password"],
        )
        cursor = connection.cursor()
        cursor.execute("CREATE DATABASE IF NOT EXISTS Library")
        cursor.execute("USE Library")

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS BookRecord (
                BookID VARCHAR(10) PRIMARY KEY,
                BookName VARCHAR(35),
                Author VARCHAR(30),
                Publisher VARCHAR(30)
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS UserRecord (
                UserID VARCHAR(10) PRIMARY KEY,
                UserName VARCHAR(20),
                Password VARCHAR(20),
                BookID VARCHAR(10),
                FOREIGN KEY (BookID) REFERENCES BookRecord(BookID)
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS AdminRecord (
                AdminID VARCHAR(10) PRIMARY KEY,
                Password VARCHAR(20)
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS Feedback (
                Feedback VARCHAR(100) PRIMARY KEY,
                Rating VARCHAR(10)
            )
            """
        )

        cursor.execute("SELECT COUNT(*) FROM AdminRecord")
        if cursor.fetchone()[0] == 0:
            cursor.executemany(
                "INSERT INTO AdminRecord VALUES (%s, %s)",
                [
                    ("Kunal1020", "123"),
                    ("Siddesh510", "786"),
                    ("Vishal305", "675"),
                ],
            )

        cursor.execute("SELECT COUNT(*) FROM UserRecord")
        if cursor.fetchone()[0] == 0:
            cursor.executemany(
                "INSERT INTO UserRecord VALUES (%s, %s, %s, %s)",
                [
                    ("101", "Kunal", "1234", None),
                    ("102", "Vishal", "3050", None),
                    ("103", "Siddhesh", "5010", None),
                ],
            )

        connection.commit()
        cursor.close()
        connection.close()
        return None
    except Exception as exc:
        return str(exc)
