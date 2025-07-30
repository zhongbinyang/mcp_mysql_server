# MySQL MCP Server

一个功能完善的MySQL数据库MCP (Model Context Protocol) 服务器，提供了丰富的数据库操作工具。

## 功能特性

### 🔧 核心功能
- **数据库连接管理**: 自动连接池和连接清理
- **表操作**: 读取、写入、更新、删除数据
- **模式管理**: 获取表结构和统计信息
- **搜索功能**: 支持模糊搜索和条件查询
- **安全防护**: SQL注入防护和输入验证

### 🛠️ 可用工具

#### 1. 连接测试
- `test_connection()`: 测试数据库连接并返回服务器信息

#### 2. 数据库管理
- `list_databases()`: 列出所有数据库
- `get_current_database()`: 获取当前数据库名称
- `create_database(database_name, charset, collation)`: 创建新数据库
- `delete_database(database_name, force)`: 删除数据库
- `switch_database(database_name)`: 切换数据库
- `get_database_details(database_name)`: 获取数据库详细信息
- `copy_database(source_database, target_database)`: 复制数据库
- `rename_database(old_name, new_name)`: 重命名数据库

#### 3. 表管理
- `list_tables()`: 列出所有表
- `get_table_schema(table_name)`: 获取表结构
- `get_table_stats(table_name)`: 获取表统计信息

#### 4. 数据操作
- `read_table(table_name, limit, offset)`: 读取表数据（支持分页）
- `write_table(table_name, data)`: 插入新数据
- `update_table(table_name, data, where_conditions)`: 更新数据
- `delete_from_table(table_name, where_conditions)`: 删除数据

#### 5. 搜索和查询
- `search_table(table_name, search_column, search_value, limit)`: 模糊搜索
- `execute_sql(query)`: 执行自定义SQL查询（仅限SELECT）

## 安装和配置

### 1. 安装依赖
```bash
pip install mysql-connector-python mcp-server-fastmcp
```

### 2. 环境变量配置
```bash
# 数据库配置
export MYSQL_HOST=127.0.0.1
export MYSQL_PORT=3306
export MYSQL_USER=root
export MYSQL_PASSWORD=123456
export MYSQL_DATABASE=mcp

# 服务器配置
export MCP_PORT=8002
export MCP_HOST=0.0.0.0

# 日志配置
export LOG_LEVEL=INFO
export LOG_FILE=/path/to/application.log
```

### 3. 启动服务器
```bash
python mcp-mysql-server.py
```

## 配置选项

### 数据库配置
- `MYSQL_HOST` - 数据库主机地址
- `MYSQL_PORT` - 数据库端口
- `MYSQL_USER` - 数据库用户名
- `MYSQL_PASSWORD` - 数据库密码
- `MYSQL_DATABASE` - 数据库名称

### 服务器配置
- `MCP_PORT` - MCP服务器端口
- `MCP_HOST` - MCP服务器主机地址

### 日志配置
- `LOG_LEVEL` - 日志级别（DEBUG, INFO, WARNING, ERROR）
- `LOG_FILE` - 日志文件路径

### 数据库管理配置
- `default_charset` - 默认字符集（默认：utf8mb4）
- `default_collation` - 默认排序规则（默认：utf8mb4_unicode_ci）
- `allow_system_db_operations` - 是否允许操作系统数据库（默认：False）
- `max_database_name_length` - 数据库名称最大长度（默认：64）
- `backup_before_delete` - 删除前是否自动备份（默认：True）
- `auto_switch_on_create` - 创建数据库后是否自动切换（默认：False）

## 使用示例

### 测试连接
```python
# 测试数据库连接
result = test_connection()
print(result)
```

### 数据库管理
```python
# 列出所有数据库
databases = list_databases()
print(databases)

# 获取当前数据库
current_db = get_current_database()
print(current_db)

# 创建新数据库
result = create_database("new_database", charset="utf8mb4", collation="utf8mb4_unicode_ci")
print(result)

# 切换数据库
result = switch_database("new_database")
print(result)

# 获取数据库详细信息
details = get_database_details("new_database")
print(details)

# 复制数据库
result = copy_database("source_db", "target_db")
print(result)

# 重命名数据库
result = rename_database("old_name", "new_name")
print(result)

# 删除数据库
result = delete_database("unused_database", force=True)
print(result)
```

### 表操作
```python
# 列出所有表
tables = list_tables()
print(tables)

# 获取表结构
schema = get_table_schema("users")
print(schema)

# 读取表数据（前10行）
data = read_table("users", limit=10)
print(data)
```

### 数据操作
```python
# 插入数据
new_user = {
    "name": "John Doe",
    "email": "john@example.com",
    "age": 30
}
result = write_table("users", new_user)
print(result)

# 更新数据
update_data = {"age": 31}
where_conditions = {"email": "john@example.com"}
result = update_table("users", update_data, where_conditions)
print(result)

# 删除数据
where_conditions = {"email": "john@example.com"}
result = delete_from_table("users", where_conditions)
print(result)
```

### 搜索功能
```python
# 搜索用户
results = search_table("users", "name", "John", limit=10)
print(results)
```

## 安全特性

### 1. SQL注入防护
- 表名和列名验证
- 参数化查询
- 危险操作限制

### 2. 输入验证
- 数据类型检查
- 长度限制
- 格式验证

### 3. 操作限制
- 仅允许SELECT查询的自定义SQL
- 结果数量限制
- 查询长度限制

### 4. 数据库管理安全
- 系统数据库保护（mysql, information_schema等）
- 数据库名称长度限制
- 删除前自动备份（可配置）
- 系统数据库操作权限控制

## 错误处理

所有工具函数都返回标准化的响应格式：

### 成功响应
```json
{
    "status": "success",
    "message": "Operation completed successfully",
    "data": {...},
    "timestamp": "2024-01-01T12:00:00"
}
```

### 错误响应
```json
{
    "status": "error",
    "message": "Error description",
    "error": "Detailed error message",
    "timestamp": "2024-01-01T12:00:00"
}
```

## 日志记录

服务器提供详细的日志记录：
- 客户端调用日志
- SQL执行日志
- 错误和异常日志
- 连接状态日志

日志文件位置：`/Users/zbyang/mcp_getting_started/log/application.log`

## 性能优化

### 1. 连接管理
- 使用上下文管理器自动管理连接
- 连接池优化
- 自动连接清理

### 2. 查询优化
- 分页支持
- 结果限制
- 索引友好查询

### 3. 内存管理
- 及时释放资源
- 游标自动关闭
- 连接自动关闭

## 扩展功能

### 添加新工具
```python
@log_client_call
@mcp.tool()
def your_custom_tool(param1: str, param2: int) -> Dict[str, Any]:
    """
    Your custom tool description.
    
    Args:
        param1: Description of param1
        param2: Description of param2
        
    Returns:
        Dict containing operation results
    """
    try:
        # Your implementation here
        return format_result(data, "Success message")
    except Exception as e:
        return format_error(e, "Error message")
```

## 故障排除

### 常见问题

1. **连接失败**
   - 检查数据库服务是否运行
   - 验证连接参数
   - 检查网络连接

2. **权限错误**
   - 确认数据库用户权限
   - 检查表访问权限

3. **性能问题**
   - 检查索引使用情况
   - 优化查询语句
   - 调整连接池设置

## 贡献

欢迎提交Issue和Pull Request来改进这个项目。

## 许可证

MIT License
