"""
Configuration file for MySQL MCP Server
"""

import os
from typing import Dict, Any

# Database configuration
DB_CONFIG: Dict[str, Any] = {
    'host': os.getenv('MYSQL_HOST', '127.0.0.1'),
    'port': int(os.getenv('MYSQL_PORT', '3306')),
    'user': os.getenv('MYSQL_USER', 'root'),
    'password': os.getenv('MYSQL_PASSWORD', 'zhongbin'),
    # 'database': os.getenv('MYSQL_DATABASE', 'mcp'),  # 移除默认数据库，让系统不指定数据库
    'autocommit': True,
    'charset': 'utf8mb4',
    'collation': 'utf8mb4_unicode_ci',
    'connect_timeout': 10,
    'read_timeout': 30,
    'write_timeout': 30
}

# Server configuration
SERVER_CONFIG: Dict[str, Any] = {
    'name': 'MySQL MCP Server',
    'port': int(os.getenv('MCP_PORT', '8002')),
    'host': os.getenv('MCP_HOST', '0.0.0.0'),
    'transport': 'stdio'
}

# Logging configuration
LOGGING_CONFIG: Dict[str, Any] = {
    'level': os.getenv('LOG_LEVEL', 'INFO'),
    'file_path': os.getenv('LOG_FILE', '/Users/zbyang/git/mcp_mysql_server/log/application.log'),
    'format': '%(asctime)s - %(levelname)s - %(message)s',
    'mcp_framework_log_level': os.getenv('MCP_LOG_LEVEL', 'WARNING'),  # Control MCP framework logging
    'enable_mcp_request_logs': os.getenv('ENABLE_MCP_REQUEST_LOGS', 'false').lower() == 'true'  # Enable/disable MCP request logs
}

# Security configuration
SECURITY_CONFIG: Dict[str, Any] = {
    'max_query_length': 10000,  # Maximum SQL query length
    'allowed_operations': ['SELECT'],  # Only allow SELECT operations for custom SQL
    'table_name_pattern': r'^[a-zA-Z0-9_-]+$',  # Regex pattern for valid table names
    'max_results': 1000,  # Maximum number of results to return
    'protected_databases': ['mysql', 'information_schema', 'performance_schema', 'sys']  # System databases that cannot be deleted
}

# Database management configuration
DB_MANAGEMENT_CONFIG: Dict[str, Any] = {
    'default_charset': 'utf8mb4',
    'default_collation': 'utf8mb4_unicode_ci',
    'allow_system_db_operations': False,  # Whether to allow operations on system databases
    'max_database_name_length': 64,  # Maximum length for database names
    'backup_before_delete': True,  # Whether to create backup before deleting database
    'auto_switch_on_create': True  # Whether to automatically switch to newly created database
} 