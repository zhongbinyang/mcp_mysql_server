#!/usr/bin/env python3
"""
Test script to verify the MySQL MCP Server works without specifying a default database
"""

import mysql.connector
from mysql.connector import Error
import sys
import os

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import DB_CONFIG

def test_connection_without_db():
    """Test connecting to MySQL without specifying a database"""
    try:
        # Create connection config without database
        connection_config = {
            'host': DB_CONFIG['host'],
            'port': DB_CONFIG['port'],
            'user': DB_CONFIG['user'],
            'password': DB_CONFIG['password'],
            'autocommit': DB_CONFIG['autocommit'],
            'charset': DB_CONFIG['charset'],
            'collation': DB_CONFIG['collation'],
            'connect_timeout': DB_CONFIG['connect_timeout'],
            'read_timeout': DB_CONFIG['read_timeout'],
            'write_timeout': DB_CONFIG['write_timeout']
        }
        
        print("Testing connection without database...")
        connection = mysql.connector.connect(**connection_config)
        
        if connection.is_connected():
            print("✓ Successfully connected to MySQL without specifying database")
            
            # Test getting current database (should be None)
            cursor = connection.cursor()
            cursor.execute("SELECT DATABASE()")
            current_db = cursor.fetchone()[0]
            print(f"✓ Current database: {current_db}")
            
            # Test listing databases
            cursor.execute("SHOW DATABASES")
            databases = [row[0] for row in cursor.fetchall()]
            print(f"✓ Available databases: {databases}")
            
            cursor.close()
            connection.close()
            print("✓ Connection closed successfully")
            return True
        else:
            print("✗ Failed to connect to MySQL")
            return False
            
    except Error as e:
        print(f"✗ MySQL connection error: {e}")
        return False

def test_connection_with_db():
    """Test connecting to MySQL with a specific database"""
    try:
        # Test with 'mcp' database if it exists
        connection_config = {
            'host': DB_CONFIG['host'],
            'port': DB_CONFIG['port'],
            'user': DB_CONFIG['user'],
            'password': DB_CONFIG['password'],
            'database': 'mcp',  # Try to connect to 'mcp' database
            'autocommit': DB_CONFIG['autocommit'],
            'charset': DB_CONFIG['charset'],
            'collation': DB_CONFIG['collation'],
            'connect_timeout': DB_CONFIG['connect_timeout'],
            'read_timeout': DB_CONFIG['read_timeout'],
            'write_timeout': DB_CONFIG['write_timeout']
        }
        
        print("\nTesting connection with 'mcp' database...")
        connection = mysql.connector.connect(**connection_config)
        
        if connection.is_connected():
            print("✓ Successfully connected to MySQL with 'mcp' database")
            
            # Test getting current database
            cursor = connection.cursor()
            cursor.execute("SELECT DATABASE()")
            current_db = cursor.fetchone()[0]
            print(f"✓ Current database: {current_db}")
            
            # Test listing tables
            cursor.execute("SHOW TABLES")
            tables = [row[0] for row in cursor.fetchall()]
            print(f"✓ Tables in 'mcp' database: {tables}")
            
            cursor.close()
            connection.close()
            print("✓ Connection closed successfully")
            return True
        else:
            print("✗ Failed to connect to MySQL with 'mcp' database")
            return False
            
    except Error as e:
        print(f"✗ MySQL connection error with 'mcp' database: {e}")
        return False

if __name__ == "__main__":
    print("MySQL MCP Server - Database Connection Test")
    print("=" * 50)
    
    # Test connection without database
    success1 = test_connection_without_db()
    
    # Test connection with database
    success2 = test_connection_with_db()
    
    print("\n" + "=" * 50)
    if success1 and success2:
        print("✓ All tests passed! The server can work without specifying a default database.")
    else:
        print("✗ Some tests failed. Please check your MySQL configuration.") 