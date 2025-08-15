import mysql.connector
from mysql.connector import Error
import sys
import logging
import re
from datetime import datetime
from typing import Dict, List, Any, Optional, Union
from contextlib import contextmanager
from mcp.server.fastmcp import FastMCP
from config import DB_CONFIG, SERVER_CONFIG, LOGGING_CONFIG, SECURITY_CONFIG, DB_MANAGEMENT_CONFIG

# Global variable to track current database
CURRENT_DATABASE: Optional[str] = None

# Configure logging
logger = logging.getLogger()
logger.setLevel(getattr(logging, LOGGING_CONFIG['level']))

# File handler
file_handler = logging.FileHandler(LOGGING_CONFIG['file_path'])
file_handler.setFormatter(logging.Formatter(LOGGING_CONFIG['format']))

# Console handler
# console_handler = logging.StreamHandler()
# console_handler.setFormatter(logging.Formatter(LOGGING_CONFIG['format']))

logger.addHandler(file_handler)
# logger.addHandler(console_handler)

def configure_mcp_logging():
    """Configure MCP framework logging levels"""
    mcp_log_level = getattr(logging, LOGGING_CONFIG['mcp_framework_log_level'])
    
    # Control all MCP-related loggers
    mcp_loggers = [
        'mcp',
        'mcp.server', 
        'mcp.server.fastmcp',
        'mcp.server.models',
        'mcp.server.stdio',
        'mcp.server.http'
    ]
    
    for logger_name in mcp_loggers:
        mcp_logger = logging.getLogger(logger_name)
        mcp_logger.setLevel(mcp_log_level)
        # Prevent propagation to avoid duplicate logs
        mcp_logger.propagate = False

# Configure MCP framework logging
configure_mcp_logging()

def log_sql_execution(func):
    """Decorator to log SQL execution"""
    def wrapper(*args, **kwargs):
        # Get the function name for logging
        func_name = func.__name__
        
        # Log the function call
        logger.info(f"[SQL EXECUTION] {func_name} called")
        
        try:
            result = func(*args, **kwargs)
            logger.info(f"[SQL EXECUTION] {func_name} completed successfully")
            return result
        except Exception as e:
            logger.error(f"[SQL EXECUTION] {func_name} failed with error: {e}")
            raise
    return wrapper

# Initialize MCP server
if SERVER_CONFIG['transport'] == 'stdio':
    mcp = FastMCP(SERVER_CONFIG['name'])
else:
    mcp = FastMCP(SERVER_CONFIG['name'], port=SERVER_CONFIG['port'], host=SERVER_CONFIG['host'])

def log_client_call(func):
    """Decorator to log client function calls"""
    def wrapper(*args, **kwargs):
        logger.info(f"[CLIENT CALL] {func.__name__} called with args={args}, kwargs={kwargs}")
        try:
            result = func(*args, **kwargs)
            logger.info(f"[CLIENT CALL] {func.__name__} completed successfully")
            return result
        except Exception as e:
            logger.error(f"[CLIENT CALL] {func.__name__} failed with error: {e}")
            raise
    return wrapper

@contextmanager
def get_mysql_connection():
    """Context manager for MySQL connections with automatic cleanup and SQL logging"""
    connection = None
    try:
        # Create connection config based on current database
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
        
        # Only add database if one is currently selected
        if CURRENT_DATABASE:
            connection_config['database'] = CURRENT_DATABASE
        
        connection = mysql.connector.connect(**connection_config)
        if connection.is_connected():
            logger.debug(f"MySQL connection established{' to database ' + CURRENT_DATABASE if CURRENT_DATABASE else ' (no database)'}")
            
            # Create a custom cursor class that logs SQL statements
            class LoggingCursor:
                def __init__(self, cursor):
                    self.cursor = cursor
                
                def execute(self, query, params=None):
                    if params:
                        logger.info(f"[SQL] {query} with params: {params}")
                    else:
                        logger.info(f"[SQL] {query}")
                    return self.cursor.execute(query, params)
                
                def fetchall(self):
                    return self.cursor.fetchall()
                
                def fetchone(self):
                    return self.cursor.fetchone()
                
                def close(self):
                    return self.cursor.close()
                
                @property
                def rowcount(self):
                    return self.cursor.rowcount
                
                @property
                def lastrowid(self):
                    return self.cursor.lastrowid
            
            # Monkey patch the connection's cursor method
            original_cursor = connection.cursor
            
            def logging_cursor(*args, **kwargs):
                cursor = original_cursor(*args, **kwargs)
                return LoggingCursor(cursor)
            
            connection.cursor = logging_cursor
            
            yield connection
        else:
            raise Error("Failed to establish MySQL connection")
    except Error as e:
        logger.error(f"MySQL connection error: {e}")
        raise
    finally:
        if connection and connection.is_connected():
            connection.close()
            logger.debug("MySQL connection closed")

@contextmanager
def get_mysql_connection_no_db():
    """Context manager for MySQL connections without database specification and SQL logging"""
    connection = None
    try:
        connection = mysql.connector.connect(
            host=DB_CONFIG['host'],
            port=DB_CONFIG['port'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password']
        )
        if connection.is_connected():
            logger.debug("MySQL connection established (no database)")
            
            # Create a custom cursor class that logs SQL statements
            class LoggingCursor:
                def __init__(self, cursor):
                    self.cursor = cursor
                
                def execute(self, query, params=None):
                    if params:
                        logger.info(f"[SQL] {query} with params: {params}")
                    else:
                        logger.info(f"[SQL] {query}")
                    return self.cursor.execute(query, params)
                
                def fetchall(self):
                    return self.cursor.fetchall()
                
                def fetchone(self):
                    return self.cursor.fetchone()
                
                def close(self):
                    return self.cursor.close()
                
                @property
                def rowcount(self):
                    return self.cursor.rowcount
                
                @property
                def lastrowid(self):
                    return self.cursor.lastrowid
            
            # Monkey patch the connection's cursor method
            original_cursor = connection.cursor
            
            def logging_cursor(*args, **kwargs):
                cursor = original_cursor(*args, **kwargs)
                return LoggingCursor(cursor)
            
            connection.cursor = logging_cursor
            
            yield connection
        else:
            raise Error("Failed to establish MySQL connection")
    except Error as e:
        logger.error(f"MySQL connection error: {e}")
        raise
    finally:
        if connection and connection.is_connected():
            connection.close()
            logger.debug("MySQL connection closed (no database)")

def validate_table_name(table_name: str) -> bool:
    """Validate table name to prevent SQL injection"""
    if not table_name or not isinstance(table_name, str):
        return False
    # Use pattern from config
    pattern = SECURITY_CONFIG['table_name_pattern']
    return bool(re.match(pattern, table_name))

def validate_sql_query(query: str) -> bool:
    """Basic SQL query validation"""
    if not query or not isinstance(query, str):
        return False
    
    # Only check if query is not empty
    if not query.strip():
        return False
    
    return True

def format_result(data: Any, message: str = "Success") -> Dict[str, Any]:
    """Standardize result format"""
    return {
        "status": "success",
        "message": message,
        "data": data,
        "timestamp": datetime.now().isoformat()
    }

def format_error(error: str, message: str = "Error occurred") -> Dict[str, Any]:
    """Standardize error format"""
    return {
        "status": "error",
        "message": message,
        "error": str(error),
        "timestamp": datetime.now().isoformat()
    }

# Tool: Test database connection
@log_client_call
@mcp.tool()
def test_connection() -> Dict[str, Any]:
    """
    Tests the database connection and returns server information.
    
    Returns:
        Dict containing connection status, server version, and database name
    """
    try:
        with get_mysql_connection() as connection:
            db_info = connection.get_server_info()
            cursor = connection.cursor()
            cursor.execute("SELECT DATABASE()")
            database_name = cursor.fetchone()[0]
            cursor.close()
            
            return format_result({
                "server_version": db_info,
                "database": database_name,
                "connection_id": connection.connection_id
            }, "Database connection successful")
    except Exception as e:
        logger.error(f"Connection test failed: {e}")
        return format_error(e, "Database connection failed")

# Tool: List all tables
@log_client_call
@mcp.tool()
def list_tables() -> Dict[str, Any]:
    """
    Lists all tables in the database.
    
    Returns:
        Dict containing list of table names
    """
    if not CURRENT_DATABASE:
        return format_error("No database selected", "Please use switch_database() to select a database first")
    
    try:
        with get_mysql_connection() as connection:
            cursor = connection.cursor()
            cursor.execute("SHOW TABLES")
            tables = [row[0] for row in cursor.fetchall()]
            cursor.close()
            
            return format_result({"tables": tables}, f"Found {len(tables)} tables in database '{CURRENT_DATABASE}'")
    except Exception as e:
        logger.error(f"Failed to list tables: {e}")
        return format_error(e, "Failed to list tables")

# Tool: Get table schema
@log_client_call
@mcp.tool()
def get_table_schema(table_name: str) -> Dict[str, Any]:
    """
    Fetches the schema of the specified table.
    
    Args:
        table_name: Name of the table to get schema for
        
    Returns:
        Dict containing table schema information
    """
    if not CURRENT_DATABASE:
        return format_error("No database selected", "Please use switch_database() to select a database first")
    
    if not validate_table_name(table_name):
        return format_error("Invalid table name", "Table name contains invalid characters")
    
    try:
        with get_mysql_connection() as connection:
            cursor = connection.cursor()
            cursor.execute(f"DESCRIBE {table_name}")
            rows = cursor.fetchall()
            cursor.close()
            
            schema = []
            for row in rows:
                schema.append({
                    "field": row[0],
                    "type": row[1],
                    "null": row[2],
                    "key": row[3],
                    "default": row[4],
                    "extra": row[5]
                })
            
            return format_result({"schema": schema}, f"Schema retrieved for table '{table_name}' in database '{CURRENT_DATABASE}'")
    except Exception as e:
        logger.error(f"Failed to get schema for table '{table_name}': {e}")
        return format_error(e, f"Failed to get schema for table '{table_name}'")

# Tool: Read data from table
@log_client_call
@mcp.tool()
def read_table(table_name: str, limit: int = 100, offset: int = 0) -> Dict[str, Any]:
    """
    Reads data from the specified table and returns it.
    
    Args:
        table_name: Name of the table to read from
        limit: Maximum number of rows to return (default: 100)
        offset: Number of rows to skip (default: 0)
        
    Returns:
        Dict containing table data
    """
    if not CURRENT_DATABASE:
        return format_error("No database selected", "Please use switch_database() to select a database first")
    
    if not validate_table_name(table_name):
        return format_error("Invalid table name", "Table name contains invalid characters")
    
    if limit < 0:
        return format_error("Invalid limit", "Limit must be a positive integer")
    
    if offset < 0:
        return format_error("Invalid offset", "Offset must be a positive integer")
    
    # Apply security limit
    if limit > SECURITY_CONFIG['max_results']:
        limit = SECURITY_CONFIG['max_results']
    
    try:
        with get_mysql_connection() as connection:
            cursor = connection.cursor(dictionary=True)
            
            # Build query with limit and offset
            query = f"SELECT * FROM {table_name} LIMIT {limit} OFFSET {offset}"
            
            cursor.execute(query)
            rows = cursor.fetchall()
            cursor.close()
            
            return format_result({
                "data": rows,
                "count": len(rows),
                "table": table_name,
                "database": CURRENT_DATABASE
            }, f"Retrieved {len(rows)} rows from table '{table_name}' in database '{CURRENT_DATABASE}'")
    except Exception as e:
        logger.error(f"Failed to read from table '{table_name}': {e}")
        return format_error(e, f"Failed to read from table '{table_name}'")

# Tool: Write data to table
@log_client_call
@mcp.tool()
def write_table(table_name: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Writes a row of data to the specified table.
    
    Args:
        table_name: Name of the table to write to
        data: Dictionary containing column names and values
        
    Returns:
        Dict containing operation status
    """
    if not CURRENT_DATABASE:
        return format_error("No database selected", "Please use switch_database() to select a database first")
    
    if not validate_table_name(table_name):
        return format_error("Invalid table name", "Table name contains invalid characters")
    
    if not data or not isinstance(data, dict):
        return format_error("Invalid data", "Data must be a non-empty dictionary")
    
    try:
        with get_mysql_connection() as connection:
            cursor = connection.cursor()
            
            # Generate SQL for INSERT
            columns = ', '.join(data.keys())
            values = ', '.join(['%s'] * len(data))
            query = f"INSERT INTO {table_name} ({columns}) VALUES ({values})"
            
            cursor.execute(query, tuple(data.values()))
            last_insert_id = cursor.lastrowid
            cursor.close()
            
            return format_result({
                "inserted_id": last_insert_id,
                "affected_rows": cursor.rowcount,
                "database": CURRENT_DATABASE
            }, f"Data inserted successfully into table '{table_name}' in database '{CURRENT_DATABASE}'")
    except Exception as e:
        logger.error(f"Failed to write to table '{table_name}': {e}")
        return format_error(e, f"Failed to write to table '{table_name}'")

# Tool: Update data in table
@log_client_call
@mcp.tool()
def update_table(table_name: str, data: Dict[str, Any], where_conditions: Dict[str, Any]) -> Dict[str, Any]:
    """
    Updates data in the specified table based on where conditions.
    
    Args:
        table_name: Name of the table to update
        data: Dictionary containing column names and new values
        where_conditions: Dictionary containing column names and values for WHERE clause
        
    Returns:
        Dict containing operation status
    """
    if not CURRENT_DATABASE:
        return format_error("No database selected", "Please use switch_database() to select a database first")
    
    if not validate_table_name(table_name):
        return format_error("Invalid table name", "Table name contains invalid characters")
    
    if not data or not isinstance(data, dict):
        return format_error("Invalid data", "Data must be a non-empty dictionary")
    
    if not where_conditions or not isinstance(where_conditions, dict):
        return format_error("Invalid where conditions", "Where conditions must be a non-empty dictionary")
    
    try:
        with get_mysql_connection() as connection:
            cursor = connection.cursor()
            
            # Build UPDATE query
            set_clause = ', '.join([f"{k} = %s" for k in data.keys()])
            where_clause = ' AND '.join([f"{k} = %s" for k in where_conditions.keys()])
            query = f"UPDATE {table_name} SET {set_clause} WHERE {where_clause}"
            
            # Combine values for execution
            values = tuple(data.values()) + tuple(where_conditions.values())
            
            cursor.execute(query, values)
            affected_rows = cursor.rowcount
            cursor.close()
            
            return format_result({
                "affected_rows": affected_rows,
                "database": CURRENT_DATABASE
            }, f"Updated {affected_rows} rows in table '{table_name}' in database '{CURRENT_DATABASE}'")
    except Exception as e:
        logger.error(f"Failed to update table '{table_name}': {e}")
        return format_error(e, f"Failed to update table '{table_name}'")

# Tool: Delete data from table
@log_client_call
@mcp.tool()
def delete_from_table(table_name: str, where_conditions: Dict[str, Any]) -> Dict[str, Any]:
    """
    Deletes data from the specified table based on where conditions.
    
    Args:
        table_name: Name of the table to delete from
        where_conditions: Dictionary containing column names and values for WHERE clause
        
    Returns:
        Dict containing operation status
    """
    if not CURRENT_DATABASE:
        return format_error("No database selected", "Please use switch_database() to select a database first")
    
    if not validate_table_name(table_name):
        return format_error("Invalid table name", "Table name contains invalid characters")
    
    if not where_conditions or not isinstance(where_conditions, dict):
        return format_error("Invalid where conditions", "Where conditions must be a non-empty dictionary")
    
    try:
        with get_mysql_connection() as connection:
            cursor = connection.cursor()
            
            # Build DELETE query
            where_clause = ' AND '.join([f"{k} = %s" for k in where_conditions.keys()])
            query = f"DELETE FROM {table_name} WHERE {where_clause}"
            
            cursor.execute(query, tuple(where_conditions.values()))
            affected_rows = cursor.rowcount
            cursor.close()
            
            return format_result({
                "affected_rows": affected_rows,
                "database": CURRENT_DATABASE
            }, f"Deleted {affected_rows} rows from table '{table_name}' in database '{CURRENT_DATABASE}'")
    except Exception as e:
        logger.error(f"Failed to delete from table '{table_name}': {e}")
        return format_error(e, f"Failed to delete from table '{table_name}'")

# Tool: Execute custom SQL query
@log_client_call
@mcp.tool()
def execute_sql(query: str) -> Dict[str, Any]:
    """
    Executes a custom SQL query and returns the result.
    
    Args:
        query: SQL query to execute (any valid SQL)
        
    Returns:
        Dict containing query results
    """
    if not CURRENT_DATABASE:
        return format_error("No database selected", "Please use switch_database() to select a database first")
    
    if not validate_sql_query(query):
        return format_error("Invalid query", "Query validation failed")
    
    try:
        with get_mysql_connection() as connection:
            cursor = connection.cursor(dictionary=True)
            
            cursor.execute(query)
            rows = cursor.fetchall()
            cursor.close()
            
            return format_result({
                "data": rows,
                "count": len(rows),
                "database": CURRENT_DATABASE
            }, f"Query executed successfully, returned {len(rows)} rows from database '{CURRENT_DATABASE}'")
    except Exception as e:
        logger.error(f"Failed to execute SQL query: {e}")
        return format_error(e, "Failed to execute SQL query")

# Tool: Create table
@log_client_call
@mcp.tool()
def create_table(table_name: str, columns: List[Dict[str, Any]], options: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Creates a new table with the specified columns and options.
    
    Args:
        table_name: Name of the table to create
        columns: List of column definitions, each containing:
                - name: Column name
                - type: Data type (e.g., 'INT', 'VARCHAR(100)', 'DECIMAL(10,2)')
                - constraints: List of constraints (e.g., ['NOT NULL', 'PRIMARY KEY', 'AUTO_INCREMENT'])
                - default: Default value (optional)
        options: Additional table options (e.g., engine, charset, collation)
        
    Returns:
        Dict containing operation status
    """
    if not CURRENT_DATABASE:
        return format_error("No database selected", "Please use switch_database() to select a database first")
    
    if not validate_table_name(table_name):
        return format_error("Invalid table name", "Table name contains invalid characters")
    
    if not columns or not isinstance(columns, list):
        return format_error("Invalid columns", "Columns must be a non-empty list")
    
    try:
        with get_mysql_connection() as connection:
            cursor = connection.cursor()
            
            # Build CREATE TABLE statement
            column_definitions = []
            for column in columns:
                if not isinstance(column, dict) or 'name' not in column or 'type' not in column:
                    return format_error("Invalid column definition", "Each column must have 'name' and 'type'")
                
                col_name = column['name']
                col_type = column['type']
                
                # Validate column name
                if not validate_table_name(col_name):
                    return format_error("Invalid column name", f"Column name '{col_name}' contains invalid characters")
                
                # Build column definition
                col_def = f"`{col_name}` {col_type}"
                
                # Add constraints
                if 'constraints' in column and isinstance(column['constraints'], list):
                    for constraint in column['constraints']:
                        if isinstance(constraint, str):
                            col_def += f" {constraint}"
                
                # Add default value
                if 'default' in column:
                    if column['default'] is None:
                        col_def += " DEFAULT NULL"
                    elif isinstance(column['default'], str):
                        col_def += f" DEFAULT '{column['default']}'"
                    else:
                        col_def += f" DEFAULT {column['default']}"
                
                column_definitions.append(col_def)
            
            # Build the complete CREATE TABLE statement
            create_sql = f"CREATE TABLE `{table_name}` (\n  "
            create_sql += ",\n  ".join(column_definitions)
            create_sql += "\n)"
            
            # Add table options
            if options:
                if 'engine' in options:
                    create_sql += f" ENGINE={options['engine']}"
                if 'charset' in options:
                    create_sql += f" CHARACTER SET {options['charset']}"
                if 'collation' in options:
                    create_sql += f" COLLATE {options['collation']}"
            
            # Execute the CREATE TABLE statement
            cursor.execute(create_sql)
            cursor.close()
            
            return format_result({
                "table_name": table_name,
                "columns": len(columns),
                "sql": create_sql,
                "database": CURRENT_DATABASE
            }, f"Table '{table_name}' created successfully in database '{CURRENT_DATABASE}'")
    except Exception as e:
        logger.error(f"Failed to create table '{table_name}': {e}")
        return format_error(e, f"Failed to create table '{table_name}'")

# Tool: Create table from SQL
@log_client_call
@mcp.tool()
def create_table_from_sql(create_table_sql: str) -> Dict[str, Any]:
    """
    Creates a table using a raw CREATE TABLE SQL statement.
    
    Args:
        create_table_sql: Complete CREATE TABLE SQL statement
        
    Returns:
        Dict containing operation status
    """
    if not CURRENT_DATABASE:
        return format_error("No database selected", "Please use switch_database() to select a database first")
    
    if not create_table_sql or not isinstance(create_table_sql, str):
        return format_error("Invalid SQL", "CREATE TABLE SQL statement must be a non-empty string")
    
    # Basic validation for CREATE TABLE statements
    sql_lower = create_table_sql.strip().lower()
    if not sql_lower.startswith('create table'):
        return format_error("Invalid SQL", "Only CREATE TABLE statements are allowed")
    
    # Check for potentially dangerous operations
    dangerous_keywords = ['drop', 'delete', 'update', 'insert', 'grant', 'revoke', 'execute']
    for keyword in dangerous_keywords:
        if keyword in sql_lower:
            return format_error("Invalid SQL", f"SQL statement contains forbidden keyword: {keyword}")
    
    try:
        with get_mysql_connection() as connection:
            cursor = connection.cursor()
            
            # Execute the CREATE TABLE statement
            cursor.execute(create_table_sql)
            cursor.close()
            
            # Extract table name from SQL for response
            # Simple extraction - look for table name after CREATE TABLE
            import re
            table_match = re.search(r'create\s+table\s+(?:if\s+not\s+exists\s+)?`?(\w+)`?', sql_lower)
            table_name = table_match.group(1) if table_match else "unknown"
            
            return format_result({
                "table_name": table_name,
                "sql": create_table_sql,
                "database": CURRENT_DATABASE
            }, f"Table '{table_name}' created successfully in database '{CURRENT_DATABASE}'")
    except Exception as e:
        logger.error(f"Failed to create table from SQL: {e}")
        return format_error(e, "Failed to create table from SQL")

# Tool: Get table statistics
@log_client_call
@mcp.tool()
def get_table_stats(table_name: str) -> Dict[str, Any]:
    """
    Gets statistics about the specified table.
    
    Args:
        table_name: Name of the table to get statistics for
        
    Returns:
        Dict containing table statistics
    """
    if not CURRENT_DATABASE:
        return format_error("No database selected", "Please use switch_database() to select a database first")
    
    if not validate_table_name(table_name):
        return format_error("Invalid table name", "Table name contains invalid characters")
    
    try:
        with get_mysql_connection() as connection:
            cursor = connection.cursor()
            
            # Get row count
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            row_count = cursor.fetchone()[0]
            
            # Get table size information
            cursor.execute(f"""
                SELECT 
                    table_name,
                    table_rows,
                    data_length,
                    index_length,
                    (data_length + index_length) as total_size
                FROM information_schema.tables 
                WHERE table_schema = DATABASE() AND table_name = %s
            """, (table_name,))
            
            table_info = cursor.fetchone()
            cursor.close()
            
            if table_info:
                stats = {
                    "table_name": table_info[0],
                    "estimated_rows": table_info[1],
                    "actual_rows": row_count,
                    "data_size_bytes": table_info[2],
                    "index_size_bytes": table_info[3],
                    "total_size_bytes": table_info[4],
                    "database": CURRENT_DATABASE
                }
            else:
                stats = {
                    "row_count": row_count,
                    "database": CURRENT_DATABASE
                }
            
            return format_result(stats, f"Statistics retrieved for table '{table_name}' in database '{CURRENT_DATABASE}'")
    except Exception as e:
        logger.error(f"Failed to get stats for table '{table_name}': {e}")
        return format_error(e, f"Failed to get stats for table '{table_name}'")

# Tool: Search data in table
@log_client_call
@mcp.tool()
def search_table(table_name: str, search_column: str, search_value: str, limit: int = 50) -> Dict[str, Any]:
    """
    Searches for data in a specific column of the table.
    
    Args:
        table_name: Name of the table to search in
        search_column: Name of the column to search in
        search_value: Value to search for
        limit: Maximum number of results to return (default: 50)
        
    Returns:
        Dict containing search results
    """
    if not CURRENT_DATABASE:
        return format_error("No database selected", "Please use switch_database() to select a database first")
    
    if not validate_table_name(table_name):
        return format_error("Invalid table name", "Table name contains invalid characters")
    
    if not validate_table_name(search_column):
        return format_error("Invalid column name", "Column name contains invalid characters")
    
    if limit < 0:
        return format_error("Invalid limit", "Limit must be a positive integer")
    
    # Apply security limit
    if limit > SECURITY_CONFIG['max_results']:
        limit = SECURITY_CONFIG['max_results']
    
    try:
        with get_mysql_connection() as connection:
            cursor = connection.cursor(dictionary=True)
            
            query = f"SELECT * FROM {table_name} WHERE {search_column} LIKE %s LIMIT {limit}"
            
            search_pattern = f"%{search_value}%"
            cursor.execute(query, (search_pattern,))
            rows = cursor.fetchall()
            cursor.close()
            
            return format_result({
                "data": rows,
                "count": len(rows),
                "search_column": search_column,
                "search_value": search_value,
                "database": CURRENT_DATABASE
            }, f"Found {len(rows)} matching rows in table '{table_name}' in database '{CURRENT_DATABASE}'")
    except Exception as e:
        logger.error(f"Failed to search table '{table_name}': {e}")
        return format_error(e, f"Failed to search table '{table_name}'")

# Tool: Get database information
@log_client_call
@mcp.tool()
def get_database_info() -> Dict[str, Any]:
    """
    Gets comprehensive information about the database.
    
    Returns:
        Dict containing database information
    """
    if not CURRENT_DATABASE:
        return format_error("No database selected", "Please use switch_database() to select a database first")
    
    try:
        with get_mysql_connection() as connection:
            cursor = connection.cursor()
            
            # Get database name
            cursor.execute("SELECT DATABASE()")
            database_name = cursor.fetchone()[0]
            
            # Get table count
            cursor.execute("SHOW TABLES")
            tables = cursor.fetchall()
            table_count = len(tables)
            
            # Get database size
            cursor.execute("""
                SELECT 
                    SUM(data_length + index_length) as total_size,
                    SUM(data_length) as data_size,
                    SUM(index_length) as index_size
                FROM information_schema.tables 
                WHERE table_schema = DATABASE()
            """)
            
            size_info = cursor.fetchone()
            cursor.close()
            
            info = {
                "database_name": database_name,
                "table_count": table_count,
                "total_size_bytes": size_info[0] if size_info[0] else 0,
                "data_size_bytes": size_info[1] if size_info[1] else 0,
                "index_size_bytes": size_info[2] if size_info[2] else 0
            }
            
            return format_result(info, f"Database information retrieved for '{database_name}'")
    except Exception as e:
        logger.error(f"Failed to get database info: {e}")
        return format_error(e, "Failed to get database information")

# Tool: List all databases
@log_client_call
@mcp.tool()
def list_databases() -> Dict[str, Any]:
    """
    Lists all databases on the MySQL server.
    
    Returns:
        Dict containing list of database names
    """
    try:
        # Connect without specifying database to get server-level access
        with get_mysql_connection_no_db() as connection:
            cursor = connection.cursor()
            cursor.execute("SHOW DATABASES")
            databases = [row[0] for row in cursor.fetchall()]
            cursor.close()
            
            return format_result({"databases": databases}, f"Found {len(databases)} databases")
    except Exception as e:
        logger.error(f"Failed to list databases: {e}")
        return format_error(e, "Failed to list databases")

# Tool: Create database
@log_client_call
@mcp.tool()
def create_database(database_name: str, charset: str = None, collation: str = None) -> Dict[str, Any]:
    """
    Creates a new database.
    
    Args:
        database_name: Name of the database to create
        charset: Character set for the database (default: from config)
        collation: Collation for the database (default: from config)
        
    Returns:
        Dict containing operation status
    """
    if not validate_table_name(database_name):  # Reuse table name validation for database names
        return format_error("Invalid database name", "Database name contains invalid characters")
    
    if len(database_name) > DB_MANAGEMENT_CONFIG['max_database_name_length']:
        return format_error("Database name too long", f"Database name must be {DB_MANAGEMENT_CONFIG['max_database_name_length']} characters or less")
    
    # Use default values from config if not provided
    charset = charset or DB_MANAGEMENT_CONFIG['default_charset']
    collation = collation or DB_MANAGEMENT_CONFIG['default_collation']
    
    try:
        # Connect without specifying database
        with get_mysql_connection_no_db() as connection:
            cursor = connection.cursor()
            
            # Create database with charset and collation
            query = f"CREATE DATABASE IF NOT EXISTS `{database_name}` CHARACTER SET {charset} COLLATE {collation}"
            cursor.execute(query)
            
            cursor.close()
            
            result_data = {
                "database_name": database_name,
                "charset": charset,
                "collation": collation
            }
            
            # Auto-switch to new database if configured
            if DB_MANAGEMENT_CONFIG['auto_switch_on_create']:
                switch_result = switch_database(database_name)
                if switch_result['status'] == 'success':
                    result_data['auto_switched'] = True
            
            return format_result(result_data, f"Database '{database_name}' created successfully")
    except Exception as e:
        logger.error(f"Failed to create database '{database_name}': {e}")
        return format_error(e, f"Failed to create database '{database_name}'")

# Tool: Delete database
@log_client_call
@mcp.tool()
def delete_database(database_name: str, force: bool = False) -> Dict[str, Any]:
    """
    Deletes a database.
    
    Args:
        database_name: Name of the database to delete
        force: If True, drops the database even if it doesn't exist (default: False)
        
    Returns:
        Dict containing operation status
    """
    if not validate_table_name(database_name):
        return format_error("Invalid database name", "Database name contains invalid characters")
    
    # Check if it's a protected database
    if database_name.lower() in SECURITY_CONFIG['protected_databases']:
        if not DB_MANAGEMENT_CONFIG['allow_system_db_operations']:
            return format_error("Cannot delete system database", f"Database '{database_name}' is a system database and cannot be deleted")
    
    try:
        # Create backup before deletion if configured
        backup_created = False
        if DB_MANAGEMENT_CONFIG['backup_before_delete'] and not force:
            backup_name = f"{database_name}_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            backup_result = copy_database(database_name, backup_name)
            if backup_result['status'] == 'success':
                backup_created = True
                logger.info(f"Backup created: {backup_name}")
        
        # Connect without specifying database
        with get_mysql_connection_no_db() as connection:
            cursor = connection.cursor()
            
            if force:
                query = f"DROP DATABASE IF EXISTS `{database_name}`"
            else:
                query = f"DROP DATABASE `{database_name}`"
            
            cursor.execute(query)
            
            cursor.close()
            
            result_data = {
                "database_name": database_name,
                "force": force
            }
            
            if backup_created:
                result_data['backup_created'] = True
            
            return format_result(result_data, f"Database '{database_name}' deleted successfully")
    except Exception as e:
        logger.error(f"Failed to delete database '{database_name}': {e}")
        return format_error(e, f"Failed to delete database '{database_name}'")

# Tool: Switch database
@log_client_call
@mcp.tool()
def switch_database(database_name: str) -> Dict[str, Any]:
    """
    Switches to a different database.
    
    Args:
        database_name: Name of the database to switch to
        
    Returns:
        Dict containing operation status
    """
    global CURRENT_DATABASE
    
    if not validate_table_name(database_name):
        return format_error("Invalid database name", "Database name contains invalid characters")
    
    try:
        # Test connection to the new database
        connection_config = {
            'host': DB_CONFIG['host'],
            'port': DB_CONFIG['port'],
            'user': DB_CONFIG['user'],
            'password': DB_CONFIG['password'],
            'database': database_name
        }
        
        test_connection = mysql.connector.connect(**connection_config)
        
        if test_connection.is_connected():
            # Create a custom cursor class that logs SQL statements
            class LoggingCursor:
                def __init__(self, cursor):
                    self.cursor = cursor
                
                def execute(self, query, params=None):
                    if params:
                        logger.info(f"[SQL] {query} with params: {params}")
                    else:
                        logger.info(f"[SQL] {query}")
                    return self.cursor.execute(query, params)
                
                def fetchall(self):
                    return self.cursor.fetchall()
                
                def fetchone(self):
                    return self.cursor.fetchone()
                
                def close(self):
                    return self.cursor.close()
            
            # Monkey patch the connection's cursor method
            original_cursor = test_connection.cursor
            
            def logging_cursor(*args, **kwargs):
                cursor = original_cursor(*args, **kwargs)
                return LoggingCursor(cursor)
            
            test_connection.cursor = logging_cursor
            
            cursor = test_connection.cursor()
            cursor.execute("SELECT DATABASE()")
            current_db = cursor.fetchone()[0]
            cursor.close()
            test_connection.close()
            
            # Update the global variable
            previous_database = CURRENT_DATABASE
            CURRENT_DATABASE = database_name
            
            return format_result({
                "previous_database": previous_database,
                "current_database": database_name
            }, f"Successfully switched to database '{database_name}'")
    except Exception as e:
        logger.error(f"Failed to switch to database '{database_name}': {e}")
        return format_error(e, f"Failed to switch to database '{database_name}'")

# Tool: Get database details
@log_client_call
@mcp.tool()
def get_database_details(database_name: str = None) -> Dict[str, Any]:
    """
    Gets detailed information about a specific database.
    
    Args:
        database_name: Name of the database (if None, uses current database)
        
    Returns:
        Dict containing database details
    """
    if database_name and not validate_table_name(database_name):
        return format_error("Invalid database name", "Database name contains invalid characters")
    
    try:
        # Connect to the specified database or current database
        if database_name:
            # Create a temporary connection to the specified database
            connection_config = DB_CONFIG.copy()
            connection_config['database'] = database_name
            
            connection = mysql.connector.connect(**connection_config)
            
            if connection.is_connected():
                # Create a custom cursor class that logs SQL statements
                class LoggingCursor:
                    def __init__(self, cursor):
                        self.cursor = cursor
                    
                    def execute(self, query, params=None):
                        if params:
                            logger.info(f"[SQL] {query} with params: {params}")
                        else:
                            logger.info(f"[SQL] {query}")
                        return self.cursor.execute(query, params)
                    
                    def fetchall(self):
                        return self.cursor.fetchall()
                    
                    def fetchone(self):
                        return self.cursor.fetchone()
                    
                    def close(self):
                        return self.cursor.close()
                
                # Monkey patch the connection's cursor method
                original_cursor = connection.cursor
                
                def logging_cursor(*args, **kwargs):
                    cursor = original_cursor(*args, **kwargs)
                    return LoggingCursor(cursor)
                
                connection.cursor = logging_cursor
                
                cursor = connection.cursor()
                
                # Get database name
                cursor.execute("SELECT DATABASE()")
                current_db = cursor.fetchone()[0]
                
                # Get table count
                cursor.execute("SHOW TABLES")
                tables = cursor.fetchall()
                table_count = len(tables)
                
                # Get database size and other details
                cursor.execute("""
                    SELECT 
                        table_schema,
                        SUM(data_length + index_length) as total_size,
                        SUM(data_length) as data_size,
                        SUM(index_length) as index_size,
                        COUNT(*) as table_count
                    FROM information_schema.tables 
                    WHERE table_schema = %s
                    GROUP BY table_schema
                """, (current_db,))
                
                db_info = cursor.fetchone()
                cursor.close()
                connection.close()
        else:
            # Use the standard connection manager for current database
            with get_mysql_connection() as connection:
                cursor = connection.cursor()
                
                # Get database name
                cursor.execute("SELECT DATABASE()")
                current_db = cursor.fetchone()[0]
                
                # Get table count
                cursor.execute("SHOW TABLES")
                tables = cursor.fetchall()
                table_count = len(tables)
                
                # Get database size and other details
                cursor.execute("""
                    SELECT 
                        table_schema,
                        SUM(data_length + index_length) as total_size,
                        SUM(data_length) as data_size,
                        SUM(index_length) as index_size,
                        COUNT(*) as table_count
                    FROM information_schema.tables 
                    WHERE table_schema = %s
                    GROUP BY table_schema
                """, (current_db,))
                
                db_info = cursor.fetchone()
                cursor.close()
        
        if db_info:
            details = {
                "database_name": db_info[0],
                "table_count": db_info[4],
                "total_size_bytes": db_info[1] if db_info[1] else 0,
                "data_size_bytes": db_info[2] if db_info[2] else 0,
                "index_size_bytes": db_info[3] if db_info[3] else 0,
                "tables": [table[0] for table in tables]
            }
        else:
            details = {
                "database_name": current_db,
                "table_count": table_count,
                "total_size_bytes": 0,
                "data_size_bytes": 0,
                "index_size_bytes": 0,
                "tables": [table[0] for table in tables]
            }
        
        return format_result(details, f"Database details retrieved for '{current_db}'")
    except Exception as e:
        logger.error(f"Failed to get database details for '{database_name}': {e}")
        return format_error(e, f"Failed to get database details for '{database_name}'")

# Tool: Copy database
@log_client_call
@mcp.tool()
def copy_database(source_database: str, target_database: str) -> Dict[str, Any]:
    """
    Creates a copy of an existing database.
    
    Args:
        source_database: Name of the source database
        target_database: Name of the target database
        
    Returns:
        Dict containing operation status
    """
    if not validate_table_name(source_database) or not validate_table_name(target_database):
        return format_error("Invalid database name", "Database name contains invalid characters")
    
    try:
        # Connect without specifying database
        with get_mysql_connection_no_db() as connection:
            cursor = connection.cursor()
            
            # Create target database
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{target_database}`")
            
            # Get all tables from source database
            cursor.execute(f"SHOW TABLES FROM `{source_database}`")
            tables = cursor.fetchall()
            
            copied_tables = []
            for table in tables:
                table_name = table[0]
                
                # Get table structure
                cursor.execute(f"SHOW CREATE TABLE `{source_database}`.`{table_name}`")
                create_table_sql = cursor.fetchone()[1]
                
                # Create table in target database
                create_table_sql = create_table_sql.replace(f"`{source_database}`.", "")
                cursor.execute(f"USE `{target_database}`")
                cursor.execute(create_table_sql)
                
                # Copy data
                cursor.execute(f"INSERT INTO `{target_database}`.`{table_name}` SELECT * FROM `{source_database}`.`{table_name}`")
                copied_tables.append(table_name)
            
            cursor.close()
            
            return format_result({
                "source_database": source_database,
                "target_database": target_database,
                "copied_tables": copied_tables,
                "table_count": len(copied_tables)
            }, f"Successfully copied database '{source_database}' to '{target_database}'")
    except Exception as e:
        logger.error(f"Failed to copy database '{source_database}' to '{target_database}': {e}")
        return format_error(e, f"Failed to copy database '{source_database}' to '{target_database}'")

# Tool: Rename database
@log_client_call
@mcp.tool()
def rename_database(old_name: str, new_name: str) -> Dict[str, Any]:
    """
    Renames a database by creating a copy and dropping the original.
    
    Args:
        old_name: Current name of the database
        new_name: New name for the database
        
    Returns:
        Dict containing operation status
    """
    if not validate_table_name(old_name) or not validate_table_name(new_name):
        return format_error("Invalid database name", "Database name contains invalid characters")
    
    try:
        # First copy the database
        copy_result = copy_database(old_name, new_name)
        if copy_result['status'] == 'error':
            return copy_result
        
        # Then delete the old database
        delete_result = delete_database(old_name, force=True)
        if delete_result['status'] == 'error':
            return delete_result
        
        return format_result({
            "old_name": old_name,
            "new_name": new_name
        }, f"Successfully renamed database '{old_name}' to '{new_name}'")
    except Exception as e:
        logger.error(f"Failed to rename database '{old_name}' to '{new_name}': {e}")
        return format_error(e, f"Failed to rename database '{old_name}' to '{new_name}'")

# Tool: Get current database
@log_client_call
@mcp.tool()
def get_current_database() -> Dict[str, Any]:
    """
    Gets the name of the currently selected database.
    
    Returns:
        Dict containing current database name
    """
    try:
        return format_result({
            "current_database": CURRENT_DATABASE
        }, f"Current database is '{CURRENT_DATABASE if CURRENT_DATABASE else 'None (no database selected)'}'")
    except Exception as e:
        logger.error(f"Failed to get current database: {e}")
        return format_error(e, "Failed to get current database")

# Tool: Delete table
@log_client_call
@mcp.tool()
def delete_table(table_name: str, force: bool = False) -> Dict[str, Any]:
    """
    Deletes a table from the current database.
    
    Args:
        table_name: Name of the table to delete
        force: If True, drops the table even if it doesn't exist (default: False)
        
    Returns:
        Dict containing operation status
    """
    if not CURRENT_DATABASE:
        return format_error("No database selected", "Please use switch_database() to select a database first")
    
    if not validate_table_name(table_name):
        return format_error("Invalid table name", "Table name contains invalid characters")
    
    try:
        with get_mysql_connection() as connection:
            cursor = connection.cursor()
            
            if force:
                query = f"DROP TABLE IF EXISTS `{table_name}`"
            else:
                query = f"DROP TABLE `{table_name}`"
            
            cursor.execute(query)
            cursor.close()
            
            return format_result({
                "table_name": table_name,
                "force": force,
                "database": CURRENT_DATABASE
            }, f"Table '{table_name}' deleted successfully from database '{CURRENT_DATABASE}'")
    except Exception as e:
        logger.error(f"Failed to delete table '{table_name}': {e}")
        return format_error(e, f"Failed to delete table '{table_name}'")

# Tool: Truncate table
@log_client_call
@mcp.tool()
def truncate_table(table_name: str) -> Dict[str, Any]:
    """
    Truncates a table (removes all data but keeps the structure).
    
    Args:
        table_name: Name of the table to truncate
        
    Returns:
        Dict containing operation status
    """
    if not CURRENT_DATABASE:
        return format_error("No database selected", "Please use switch_database() to select a database first")
    
    if not validate_table_name(table_name):
        return format_error("Invalid table name", "Table name contains invalid characters")
    
    try:
        with get_mysql_connection() as connection:
            cursor = connection.cursor()
            
            # Get row count before truncation
            cursor.execute(f"SELECT COUNT(*) FROM `{table_name}`")
            row_count = cursor.fetchone()[0]
            
            # Truncate the table
            cursor.execute(f"TRUNCATE TABLE `{table_name}`")
            cursor.close()
            
            return format_result({
                "table_name": table_name,
                "rows_removed": row_count,
                "database": CURRENT_DATABASE
            }, f"Table '{table_name}' truncated successfully, removed {row_count} rows from database '{CURRENT_DATABASE}'")
    except Exception as e:
        logger.error(f"Failed to truncate table '{table_name}': {e}")
        return format_error(e, f"Failed to truncate table '{table_name}'")

# Tool: Add column to table
@log_client_call
@mcp.tool()
def add_column(table_name: str, column_name: str, column_type: str, constraints: List[str] = None, default_value: Any = None, after_column: str = None) -> Dict[str, Any]:
    """
    Adds a new column to an existing table.
    
    Args:
        table_name: Name of the table to modify
        column_name: Name of the new column
        column_type: Data type of the new column
        constraints: List of constraints (e.g., ['NOT NULL', 'UNIQUE'])
        default_value: Default value for the column
        after_column: Name of the column to place the new column after (optional)
        
    Returns:
        Dict containing operation status
    """
    if not CURRENT_DATABASE:
        return format_error("No database selected", "Please use switch_database() to select a database first")
    
    if not validate_table_name(table_name):
        return format_error("Invalid table name", "Table name contains invalid characters")
    
    if not validate_table_name(column_name):
        return format_error("Invalid column name", "Column name contains invalid characters")
    
    try:
        with get_mysql_connection() as connection:
            cursor = connection.cursor()
            
            # Build ALTER TABLE statement
            alter_sql = f"ALTER TABLE `{table_name}` ADD COLUMN `{column_name}` {column_type}"
            
            # Add constraints
            if constraints and isinstance(constraints, list):
                for constraint in constraints:
                    if isinstance(constraint, str):
                        alter_sql += f" {constraint}"
            
            # Add default value
            if default_value is not None:
                if isinstance(default_value, str):
                    alter_sql += f" DEFAULT '{default_value}'"
                else:
                    alter_sql += f" DEFAULT {default_value}"
            
            # Add position
            if after_column and validate_table_name(after_column):
                alter_sql += f" AFTER `{after_column}`"
            
            cursor.execute(alter_sql)
            cursor.close()
            
            return format_result({
                "table_name": table_name,
                "column_name": column_name,
                "column_type": column_type,
                "constraints": constraints or [],
                "default_value": default_value,
                "after_column": after_column,
                "database": CURRENT_DATABASE
            }, f"Column '{column_name}' added successfully to table '{table_name}' in database '{CURRENT_DATABASE}'")
    except Exception as e:
        logger.error(f"Failed to add column '{column_name}' to table '{table_name}': {e}")
        return format_error(e, f"Failed to add column '{column_name}' to table '{table_name}'")

# Tool: Drop column from table
@log_client_call
@mcp.tool()
def drop_column(table_name: str, column_name: str) -> Dict[str, Any]:
    """
    Removes a column from an existing table.
    
    Args:
        table_name: Name of the table to modify
        column_name: Name of the column to remove
        
    Returns:
        Dict containing operation status
    """
    if not CURRENT_DATABASE:
        return format_error("No database selected", "Please use switch_database() to select a database first")
    
    if not validate_table_name(table_name):
        return format_error("Invalid table name", "Table name contains invalid characters")
    
    if not validate_table_name(column_name):
        return format_error("Invalid column name", "Column name contains invalid characters")
    
    try:
        with get_mysql_connection() as connection:
            cursor = connection.cursor()
            
            # Build ALTER TABLE statement
            alter_sql = f"ALTER TABLE `{table_name}` DROP COLUMN `{column_name}`"
            
            cursor.execute(alter_sql)
            cursor.close()
            
            return format_result({
                "table_name": table_name,
                "column_name": column_name,
                "database": CURRENT_DATABASE
            }, f"Column '{column_name}' dropped successfully from table '{table_name}' in database '{CURRENT_DATABASE}'")
    except Exception as e:
        logger.error(f"Failed to drop column '{column_name}' from table '{table_name}': {e}")
        return format_error(e, f"Failed to drop column '{column_name}' from table '{table_name}'")

# Tool: Modify column in table
@log_client_call
@mcp.tool()
def modify_column(table_name: str, column_name: str, new_type: str, new_constraints: List[str] = None, new_default: Any = None) -> Dict[str, Any]:
    """
    Modifies an existing column in a table.
    
    Args:
        table_name: Name of the table to modify
        column_name: Name of the column to modify
        new_type: New data type for the column
        new_constraints: New constraints for the column
        new_default: New default value for the column
        
    Returns:
        Dict containing operation status
    """
    if not CURRENT_DATABASE:
        return format_error("No database selected", "Please use switch_database() to select a database first")
    
    if not validate_table_name(table_name):
        return format_error("Invalid table name", "Table name contains invalid characters")
    
    if not validate_table_name(column_name):
        return format_error("Invalid column name", "Column name contains invalid characters")
    
    try:
        with get_mysql_connection() as connection:
            cursor = connection.cursor()
            
            # Build ALTER TABLE statement
            alter_sql = f"ALTER TABLE `{table_name}` MODIFY COLUMN `{column_name}` {new_type}"
            
            # Add constraints
            if new_constraints and isinstance(new_constraints, list):
                for constraint in new_constraints:
                    if isinstance(constraint, str):
                        alter_sql += f" {constraint}"
            
            # Add default value
            if new_default is not None:
                if isinstance(new_default, str):
                    alter_sql += f" DEFAULT '{new_default}'"
                else:
                    alter_sql += f" DEFAULT {new_default}"
            
            cursor.execute(alter_sql)
            cursor.close()
            
            return format_result({
                "table_name": table_name,
                "column_name": column_name,
                "new_type": new_type,
                "new_constraints": new_constraints or [],
                "new_default": new_default,
                "database": CURRENT_DATABASE
            }, f"Column '{column_name}' modified successfully in table '{table_name}' in database '{CURRENT_DATABASE}'")
    except Exception as e:
        logger.error(f"Failed to modify column '{column_name}' in table '{table_name}': {e}")
        return format_error(e, f"Failed to modify column '{column_name}' in table '{table_name}'")

# Tool: Rename table
@log_client_call
@mcp.tool()
def rename_table(old_table_name: str, new_table_name: str) -> Dict[str, Any]:
    """
    Renames a table in the current database.
    
    Args:
        old_table_name: Current name of the table
        new_table_name: New name for the table
        
    Returns:
        Dict containing operation status
    """
    if not CURRENT_DATABASE:
        return format_error("No database selected", "Please use switch_database() to select a database first")
    
    if not validate_table_name(old_table_name):
        return format_error("Invalid old table name", "Old table name contains invalid characters")
    
    if not validate_table_name(new_table_name):
        return format_error("Invalid new table name", "New table name contains invalid characters")
    
    try:
        with get_mysql_connection() as connection:
            cursor = connection.cursor()
            
            # Build RENAME TABLE statement
            rename_sql = f"RENAME TABLE `{old_table_name}` TO `{new_table_name}`"
            
            cursor.execute(rename_sql)
            cursor.close()
            
            return format_result({
                "old_table_name": old_table_name,
                "new_table_name": new_table_name,
                "database": CURRENT_DATABASE
            }, f"Table '{old_table_name}' renamed successfully to '{new_table_name}' in database '{CURRENT_DATABASE}'")
    except Exception as e:
        logger.error(f"Failed to rename table '{old_table_name}' to '{new_table_name}': {e}")
        return format_error(e, f"Failed to rename table '{old_table_name}' to '{new_table_name}'")

# Tool: Get table indexes
@log_client_call
@mcp.tool()
def get_table_indexes(table_name: str) -> Dict[str, Any]:
    """
    Gets information about indexes on the specified table.
    
    Args:
        table_name: Name of the table to get indexes for
        
    Returns:
        Dict containing index information
    """
    if not CURRENT_DATABASE:
        return format_error("No database selected", "Please use switch_database() to select a database first")
    
    if not validate_table_name(table_name):
        return format_error("Invalid table name", "Table name contains invalid characters")
    
    try:
        with get_mysql_connection() as connection:
            cursor = connection.cursor()
            
            # Get index information
            cursor.execute(f"SHOW INDEX FROM `{table_name}`")
            indexes = cursor.fetchall()
            cursor.close()
            
            # Process index information
            index_info = {}
            for row in indexes:
                index_name = row[2]
                if index_name not in index_info:
                    index_info[index_name] = {
                        "name": index_name,
                        "type": "UNIQUE" if row[1] == 0 else "NONUNIQUE",
                        "columns": []
                    }
                
                index_info[index_name]["columns"].append({
                    "column_name": row[4],
                    "seq_in_index": row[3],
                    "collation": row[5],
                    "cardinality": row[6],
                    "sub_part": row[7],
                    "packed": row[8],
                    "null": row[9],
                    "index_type": row[10]
                })
            
            return format_result({
                "table_name": table_name,
                "indexes": list(index_info.values()),
                "index_count": len(index_info),
                "database": CURRENT_DATABASE
            }, f"Retrieved {len(index_info)} indexes for table '{table_name}' in database '{CURRENT_DATABASE}'")
    except Exception as e:
        logger.error(f"Failed to get indexes for table '{table_name}': {e}")
        return format_error(e, f"Failed to get indexes for table '{table_name}'")

# Tool: Create index on table
@log_client_call
@mcp.tool()
def create_index(table_name: str, index_name: str, columns: List[str], index_type: str = "BTREE", unique: bool = False) -> Dict[str, Any]:
    """
    Creates an index on the specified table.
    
    Args:
        table_name: Name of the table to create index on
        index_name: Name of the index
        columns: List of column names to include in the index
        index_type: Type of index (e.g., 'BTREE', 'HASH')
        unique: Whether the index should be unique
        
    Returns:
        Dict containing operation status
    """
    if not CURRENT_DATABASE:
        return format_error("No database selected", "Please use switch_database() to select a database first")
    
    if not validate_table_name(table_name):
        return format_error("Invalid table name", "Table name contains invalid characters")
    
    if not validate_table_name(index_name):
        return format_error("Invalid index name", "Index name contains invalid characters")
    
    if not columns or not isinstance(columns, list):
        return format_error("Invalid columns", "Columns must be a non-empty list")
    
    # Validate column names
    for col in columns:
        if not validate_table_name(col):
            return format_error("Invalid column name", f"Column name '{col}' contains invalid characters")
    
    try:
        with get_mysql_connection() as connection:
            cursor = connection.cursor()
            
            # Build CREATE INDEX statement
            unique_clause = "UNIQUE" if unique else ""
            columns_clause = ", ".join([f"`{col}`" for col in columns])
            
            create_sql = f"CREATE {unique_clause} INDEX `{index_name}` ON `{table_name}` ({columns_clause}) USING {index_type}"
            
            cursor.execute(create_sql)
            cursor.close()
            
            return format_result({
                "table_name": table_name,
                "index_name": index_name,
                "columns": columns,
                "index_type": index_type,
                "unique": unique,
                "database": CURRENT_DATABASE
            }, f"Index '{index_name}' created successfully on table '{table_name}' in database '{CURRENT_DATABASE}'")
    except Exception as e:
        logger.error(f"Failed to create index '{index_name}' on table '{table_name}': {e}")
        return format_error(e, f"Failed to create index '{index_name}' on table '{table_name}'")

# Tool: Drop index from table
@log_client_call
@mcp.tool()
def drop_index(table_name: str, index_name: str) -> Dict[str, Any]:
    """
    Removes an index from the specified table.
    
    Args:
        table_name: Name of the table to remove index from
        index_name: Name of the index to remove
        
    Returns:
        Dict containing operation status
    """
    if not CURRENT_DATABASE:
        return format_error("No database selected", "Please use switch_database() to select a database first")
    
    if not validate_table_name(table_name):
        return format_error("Invalid table name", "Table name contains invalid characters")
    
    if not validate_table_name(index_name):
        return format_error("Invalid index name", "Index name contains invalid characters")
    
    try:
        with get_mysql_connection() as connection:
            cursor = connection.cursor()
            
            # Build DROP INDEX statement
            drop_sql = f"DROP INDEX `{index_name}` ON `{table_name}`"
            
            cursor.execute(drop_sql)
            cursor.close()
            
            return format_result({
                "table_name": table_name,
                "index_name": index_name,
                "database": CURRENT_DATABASE
            }, f"Index '{index_name}' dropped successfully from table '{table_name}' in database '{CURRENT_DATABASE}'")
    except Exception as e:
        logger.error(f"Failed to drop index '{index_name}' from table '{table_name}': {e}")
        return format_error(e, f"Failed to drop index '{index_name}' from table '{table_name}'")

# Start the MCP server
if __name__ == "__main__":
    if SERVER_CONFIG['transport'] == 'stdio':
        logger.info(f"Starting {SERVER_CONFIG['name']} with stdio transport")
    else:
        logger.info(f"Starting {SERVER_CONFIG['name']} on {SERVER_CONFIG['host']}:{SERVER_CONFIG['port']}")
    logger.info(f"Database: {DB_CONFIG['host']}:{DB_CONFIG['port']} (no default database)")
    mcp.run(transport=SERVER_CONFIG['transport'])
