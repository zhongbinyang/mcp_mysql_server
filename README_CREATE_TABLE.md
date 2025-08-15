# MySQL MCP Server - 表创建功能

## 概述

MySQL MCP Server 现在支持创建表的功能，提供了两种方式来创建表：

1. **结构化方式** (`create_table`) - 使用列定义对象
2. **SQL方式** (`create_table_from_sql`) - 使用原始SQL语句

## 功能特性

### 1. 结构化表创建 (`create_table`)

使用预定义的列结构来创建表，更安全且易于使用。

**参数：**
- `table_name`: 表名
- `columns`: 列定义列表
- `options`: 表选项（可选）

**列定义格式：**
```python
{
    "name": "列名",
    "type": "数据类型",
    "constraints": ["约束1", "约束2"],  # 可选
    "default": "默认值"  # 可选
}
```

**示例：**
```python
columns = [
    {
        "name": "id",
        "type": "INT",
        "constraints": ["AUTO_INCREMENT", "PRIMARY KEY"]
    },
    {
        "name": "name",
        "type": "VARCHAR(100)",
        "constraints": ["NOT NULL"]
    },
    {
        "name": "price",
        "type": "DECIMAL(10,2)",
        "constraints": []
    },
    {
        "name": "created_at",
        "type": "TIMESTAMP",
        "constraints": ["DEFAULT CURRENT_TIMESTAMP"]
    }
]

options = {
    "engine": "InnoDB",
    "charset": "utf8mb4",
    "collation": "utf8mb4_unicode_ci"
}

result = create_table("products", columns, options)
```

### 2. SQL方式表创建 (`create_table_from_sql`)

直接使用CREATE TABLE SQL语句创建表，提供最大的灵活性。

**参数：**
- `create_table_sql`: 完整的CREATE TABLE SQL语句

**示例：**
```python
create_sql = """CREATE TABLE products (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    category VARCHAR(50),
    price DECIMAL(10,2),
    stock INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"""

result = create_table_from_sql(create_sql)
```

## 安全特性

### 输入验证
- 表名和列名验证（防止SQL注入）
- SQL语句长度限制
- 危险关键字检测

### 权限控制
- 需要先选择数据库
- 只允许CREATE TABLE语句
- 禁止危险操作（DROP, DELETE, UPDATE等）

## 使用流程

### 1. 选择数据库
在创建表之前，必须先选择一个数据库：

```python
# 切换到现有数据库
switch_database("your_database_name")

# 或创建新数据库
create_database("new_database_name")
switch_database("new_database_name")
```

### 2. 创建表
选择数据库后，可以使用任一方法创建表：

```python
# 方法1：结构化方式
result = create_table("table_name", columns, options)

# 方法2：SQL方式
result = create_table_from_sql(create_table_sql)
```

### 3. 检查结果
```python
if result['status'] == 'success':
    print(f"表创建成功: {result['message']}")
    print(f"表名: {result['data']['table_name']}")
    print(f"列数: {result['data']['columns']}")
else:
    print(f"表创建失败: {result['message']}")
    print(f"错误: {result['error']}")
```

## 完整示例

### 创建产品表
```python
# 1. 创建测试数据库
create_database("mcp_test")

# 2. 切换到新数据库
switch_database("mcp_test")

# 3. 创建产品表
create_sql = """CREATE TABLE products (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    category VARCHAR(50),
    price DECIMAL(10,2),
    stock INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"""

result = create_table_from_sql(create_sql)

if result['status'] == 'success':
    print("产品表创建成功！")
    print(f"表名: {result['data']['table_name']}")
    print(f"数据库: {result['data']['database']}")
else:
    print(f"创建失败: {result['message']}")
```

## 错误处理

### 常见错误及解决方案

1. **"No database selected"**
   - 解决方案：使用 `switch_database()` 选择数据库

2. **"Invalid table name"**
   - 解决方案：检查表名是否包含特殊字符

3. **"Only CREATE TABLE statements are allowed"**
   - 解决方案：确保SQL语句以 "CREATE TABLE" 开头

4. **"SQL statement contains forbidden keyword"**
   - 解决方案：移除SQL中的危险关键字

## 注意事项

1. **数据库选择**：创建表前必须先选择数据库
2. **权限要求**：用户需要有创建表的权限
3. **表名唯一性**：在同一数据库中表名必须唯一
4. **字符集**：建议使用utf8mb4字符集以支持完整的Unicode字符

## 测试

运行测试脚本验证功能：

```bash
# 测试数据库和表创建
python3 test_create_db.py

# 测试结构化表创建
python3 test_create_table.py

# 测试简单表创建
python3 test_simple_create.py
```

## 总结

新的表创建功能提供了安全、灵活的方式来创建MySQL表，支持：

- ✅ 结构化列定义
- ✅ 原始SQL语句
- ✅ 完整的输入验证
- ✅ 安全限制
- ✅ 详细的错误信息
- ✅ 自动数据库管理

这些功能使得MySQL MCP Server更加完整和易用。
