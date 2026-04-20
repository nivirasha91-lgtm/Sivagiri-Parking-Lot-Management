import sqlite3

def get_connection():
    return sqlite3.connect("parking.db", check_same_thread=False)