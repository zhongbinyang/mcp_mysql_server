# MySQL MCP Server - 完整的增删改查功能

## 概述

MySQL MCP Server 提供了完整的数据库和表管理功能，包括增删改查（CRUD）操作。本文档详细介绍了所有可用的功能。

## 功能总览

### 🗄️ 数据库管理
- ✅ 创建数据库
- ✅ 删除数据库
- ✅ 切换数据库
- ✅ 列出所有数据库
- ✅ 获取数据库信息
- ✅ 复制数据库
- ✅ 重命名数据库

### 📊 表管理
- ✅ 创建表
- ✅ 删除表
- ✅ 重命名表
- ✅ 清空表
- ✅ 获取表结构
- ✅ 获取表统计信息
- ✅ 获取表索引信息

### 🔧 表结构管理
- ✅ 添加列
- ✅ 删除列
- ✅ 修改列
- ✅ 创建索引
- ✅ 删除索引

### 📝 数据操作
- ✅ 插入数据
- ✅ 查询数据
- ✅ 更新数据
- ✅ 删除数据
- ✅ 搜索数据
- ✅ 执行SQL查询

## 详细功能说明

### 1. 数据库管理

#### 1.1 创建数据库
```python
create_database(database_name: str, charset: str = None, collation: str = None)
```
**功能**: 创建新的数据库
**参数**:
- `database_name`: 数据库名称
- `charset`: 字符集（可选，默认utf8mb4）
- `collation`: 排序规则（可选，默认utf8mb4_unicode_ci）

**示例**:
```python
result = create_database("my_database")
if result['status'] == 'success':
    print(f"数据库 '{result['data']['database_name']}' 创建成功")
```

#### 1.2 删除数据库
```python
delete_database(database_name: str, force: bool = False)
```
**功能**: 删除指定的数据库
**参数**:
- `database_name`: 数据库名称
- `force`: 是否强制删除（如果不存在也删除）

**示例**:
```python
result = delete_database("old_database", force=True)
if result['status'] == 'success':
    print(f"数据库 '{result['data']['database_name']}' 删除成功")
```

#### 1.3 切换数据库
```python
switch_database(database_name: str)
```
**功能**: 切换到指定的数据库
**参数**:
- `database_name`: 目标数据库名称

**示例**:
```python
result = switch_database("my_database")
if result['status'] == 'success':
    print(f"已切换到数据库: {result['data']['current_database']}")
```

#### 1.4 列出所有数据库
```python
list_databases()
```
**功能**: 列出MySQL服务器上的所有数据库
**返回**: 数据库名称列表

**示例**:
```python
result = list_databases()
if result['status'] == 'success':
    databases = result['data']['databases']
    print(f"找到 {len(databases)} 个数据库: {databases}")
```

#### 1.5 获取数据库信息
```python
get_database_info()
get_database_details(database_name: str = None)
```
**功能**: 获取数据库的详细信息（表数量、大小等）
**参数**:
- `database_name`: 数据库名称（可选，默认当前数据库）

**示例**:
```python
result = get_database_info()
if result['status'] == 'success':
    info = result['data']
    print(f"数据库: {info['database_name']}")
    print(f"表数量: {info['table_count']}")
    print(f"总大小: {info['total_size_bytes']} 字节")
```

### 2. 表管理

#### 2.1 创建表
```python
# 方法1: 结构化方式
create_table(table_name: str, columns: List[Dict], options: Dict = None)

# 方法2: SQL方式
create_table_from_sql(create_table_sql: str)
```

**功能**: 创建新表
**参数**:
- `table_name`: 表名
- `columns`: 列定义列表
- `options`: 表选项（引擎、字符集等）
- `create_table_sql`: 完整的CREATE TABLE SQL语句

**示例**:
```python
# 结构化方式
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
    }
]

result = create_table("products", columns, {"engine": "InnoDB"})

# SQL方式
create_sql = """CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)"""

result = create_table_from_sql(create_sql)
```

#### 2.2 删除表
```python
delete_table(table_name: str, force: bool = False)
```
**功能**: 删除指定的表
**参数**:
- `table_name`: 表名
- `force`: 是否强制删除（如果不存在也删除）

**示例**:
```python
result = delete_table("old_table", force=True)
if result['status'] == 'success':
    print(f"表 '{result['data']['table_name']}' 删除成功")
```

#### 2.3 重命名表
```python
rename_table(old_table_name: str, new_table_name: str)
```
**功能**: 重命名表
**参数**:
- `old_table_name`: 原表名
- `new_table_name`: 新表名

**示例**:
```python
result = rename_table("old_name", "new_name")
if result['status'] == 'success':
    print(f"表重命名成功: {result['data']['old_table_name']} -> {result['data']['new_table_name']}")
```

#### 2.4 清空表
```python
truncate_table(table_name: str)
```
**功能**: 清空表数据但保留表结构
**参数**:
- `table_name`: 表名

**示例**:
```python
result = truncate_table("temp_data")
if result['status'] == 'success':
    print(f"表清空成功，删除了 {result['data']['rows_removed']} 行数据")
```

#### 2.5 获取表结构
```python
get_table_schema(table_name: str)
```
**功能**: 获取表的详细结构信息
**参数**:
- `table_name`: 表名

**示例**:
```python
result = get_table_schema("products")
if result['status'] == 'success':
    schema = result['data']['schema']
    for column in schema:
        print(f"列: {column['field']}, 类型: {column['type']}, 约束: {column['key']}")
```

#### 2.6 获取表统计信息
```python
get_table_stats(table_name: str)
```
**功能**: 获取表的统计信息（行数、大小等）
**参数**:
- `table_name`: 表名

**示例**:
```python
result = get_table_stats("products")
if result['status'] == 'success':
    stats = result['data']
    print(f"表名: {stats['table_name']}")
    print(f"行数: {stats['actual_rows']}")
    print(f"总大小: {stats['total_size_bytes']} 字节")
```

### 3. 表结构管理

#### 3.1 添加列
```python
add_column(table_name: str, column_name: str, column_type: str, 
           constraints: List[str] = None, default_value: Any = None, 
           after_column: str = None)
```
**功能**: 向现有表添加新列
**参数**:
- `table_name`: 表名
- `column_name`: 新列名
- `column_type`: 列数据类型
- `constraints`: 列约束列表
- `default_value`: 默认值
- `after_column`: 在指定列后添加

**示例**:
```python
result = add_column("products", "description", "TEXT", 
                   constraints=["NULL"], 
                   after_column="price")
if result['status'] == 'success':
    print(f"列 '{result['data']['column_name']}' 添加成功")
```

#### 3.2 删除列
```python
drop_column(table_name: str, column_name: str)
```
**功能**: 从表中删除指定列
**参数**:
- `table_name`: 表名
- `column_name`: 要删除的列名

**示例**:
```python
result = drop_column("products", "old_column")
if result['status'] == 'success':
    print(f"列 '{result['data']['column_name']}' 删除成功")
```

#### 3.3 修改列
```python
modify_column(table_name: str, column_name: str, new_type: str, 
              new_constraints: List[str] = None, new_default: Any = None)
```
**功能**: 修改现有列的类型、约束或默认值
**参数**:
- `table_name`: 表名
- `column_name`: 列名
- `new_type`: 新的数据类型
- `new_constraints`: 新的约束列表
- `new_default`: 新的默认值

**示例**:
```python
result = modify_column("products", "price", "DECIMAL(12,2)", 
                      new_constraints=["NOT NULL"], 
                      new_default=0.00)
if result['status'] == 'success':
    print(f"列 '{result['data']['column_name']}' 修改成功")
```

### 4. 索引管理

#### 4.1 获取表索引
```python
get_table_indexes(table_name: str)
```
**功能**: 获取表的所有索引信息
**参数**:
- `table_name`: 表名

**示例**:
```python
result = get_table_indexes("products")
if result['status'] == 'success':
    indexes = result['data']['indexes']
    for index in indexes:
        print(f"索引: {index['name']}, 类型: {index['type']}")
        for col in index['columns']:
            print(f"  - 列: {col['column_name']}")
```

#### 4.2 创建索引
```python
create_index(table_name: str, index_name: str, columns: List[str], 
             index_type: str = "BTREE", unique: bool = False)
```
**功能**: 在表上创建索引
**参数**:
- `table_name`: 表名
- `index_name`: 索引名
- `columns`: 索引列列表
- `index_type`: 索引类型（BTREE、HASH等）
- `unique`: 是否唯一索引

**示例**:
```python
result = create_index("products", "idx_name", ["name"], 
                     index_type="BTREE", unique=False)
if result['status'] == 'success':
    print(f"索引 '{result['data']['index_name']}' 创建成功")
```

#### 4.3 删除索引
```python
drop_index(table_name: str, index_name: str)
```
**功能**: 删除表上的指定索引
**参数**:
- `table_name`: 表名
- `index_name`: 索引名

**示例**:
```python
result = drop_index("products", "idx_name")
if result['status'] == 'success':
    print(f"索引 '{result['data']['index_name']}' 删除成功")
```

### 5. 数据操作

#### 5.1 插入数据
```python
write_table(table_name: str, data: Dict[str, Any])
```
**功能**: 向表中插入一行数据
**参数**:
- `table_name`: 表名
- `data`: 要插入的数据字典（列名: 值）

**示例**:
```python
data = {
    "name": "iPhone 15",
    "category": "Electronics",
    "price": 999.99,
    "stock": 100
}

result = write_table("products", data)
if result['status'] == 'success':
    print(f"数据插入成功，ID: {result['data']['inserted_id']}")
```

#### 5.2 查询数据
```python
read_table(table_name: str, limit: Optional[int] = 100, offset: Optional[int] = 0)
```
**功能**: 从表中读取数据
**参数**:
- `table_name`: 表名
- `limit`: 最大返回行数（默认100）
- `offset`: 跳过的行数（默认0）

**示例**:
```python
result = read_table("products", limit=50, offset=0)
if result['status'] == 'success':
    data = result['data']['data']
    print(f"查询到 {len(data)} 行数据")
    for row in data:
        print(f"产品: {row['name']}, 价格: {row['price']}")
```

#### 5.3 更新数据
```python
update_table(table_name: str, data: Dict[str, Any], where_conditions: Dict[str, Any])
```
**功能**: 更新表中的数据
**参数**:
- `table_name`: 表名
- `data`: 要更新的数据字典
- `where_conditions`: WHERE条件字典

**示例**:
```python
# 更新产品价格
update_data = {"price": 899.99}
where_conditions = {"name": "iPhone 15"}

result = update_table("products", update_data, where_conditions)
if result['status'] == 'success':
    print(f"更新成功，影响行数: {result['data']['affected_rows']}")
```

#### 5.4 删除数据
```python
delete_from_table(table_name: str, where_conditions: Dict[str, Any])
```
**功能**: 从表中删除数据
**参数**:
- `table_name`: 表名
- `where_conditions`: WHERE条件字典

**示例**:
```python
# 删除库存为0的产品
where_conditions = {"stock": 0}

result = delete_from_table("products", where_conditions)
if result['status'] == 'success':
    print(f"删除成功，影响行数: {result['data']['affected_rows']}")
```

#### 5.5 搜索数据
```python
search_table(table_name: str, search_column: str, search_value: str, limit: Optional[int] = 50)
```
**功能**: 在指定列中搜索数据
**参数**:
- `table_name`: 表名
- `search_column`: 搜索列名
- `search_value`: 搜索值
- `limit`: 最大返回结果数

**示例**:
```python
result = search_table("products", "name", "iPhone", limit=20)
if result['status'] == 'success':
    data = result['data']['data']
    print(f"找到 {len(data)} 个匹配的产品")
    for row in data:
        print(f"产品: {row['name']}")
```

#### 5.6 执行SQL查询
```python
execute_sql(query: str)
```
**功能**: 执行自定义SQL查询（仅限SELECT语句）
**参数**:
- `query`: SQL查询语句

**示例**:
```python
sql = "SELECT name, price FROM products WHERE price > 500 ORDER BY price DESC"
result = execute_sql(sql)
if result['status'] == 'success':
    data = result['data']['data']
    print(f"查询结果: {len(data)} 行")
    for row in data:
        print(f"{row['name']}: ${row['price']}")
```

## 使用流程示例

### 完整的数据库和表管理流程

```python
# 1. 创建新数据库
create_database("ecommerce")

# 2. 切换到新数据库
switch_database("ecommerce")

# 3. 创建产品表
create_sql = """CREATE TABLE products (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    category VARCHAR(50),
    price DECIMAL(10,2) NOT NULL,
    stock INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"""

create_table_from_sql(create_sql)

# 4. 添加一些测试数据
products_data = [
    {"name": "iPhone 15", "category": "Electronics", "price": 999.99, "stock": 100},
    {"name": "MacBook Pro", "category": "Electronics", "price": 1999.99, "stock": 50},
    {"name": "Coffee Maker", "category": "Home", "price": 89.99, "stock": 200}
]

for product in products_data:
    write_table("products", product)

# 5. 查询数据
result = read_table("products", limit=10)
print(f"产品数量: {result['data']['count']}")

# 6. 搜索特定产品
search_result = search_table("products", "name", "iPhone")
print(f"iPhone产品数量: {search_result['data']['count']}")

# 7. 更新产品价格
update_table("products", {"price": 899.99}, {"name": "iPhone 15"})

# 8. 添加新列
add_column("products", "description", "TEXT", constraints=["NULL"])

# 9. 创建索引
create_index("products", "idx_category", ["category"])
create_index("products", "idx_price", ["price"])

# 10. 获取表统计信息
stats = get_table_stats("products")
print(f"表大小: {stats['data']['total_size_bytes']} 字节")
```

## 安全特性

### 输入验证
- ✅ 表名和列名验证
- ✅ SQL注入防护
- ✅ 危险关键字检测
- ✅ 长度限制

### 权限控制
- ✅ 数据库选择验证
- ✅ 只读查询限制
- ✅ 系统数据库保护

### 操作限制
- ✅ 最大结果数限制
- ✅ 危险操作禁止
- ✅ 备份保护

## 错误处理

所有函数都返回统一的结果格式：

```python
{
    "status": "success" | "error",
    "message": "操作描述",
    "data": {...},  # 成功时的数据
    "error": "错误信息",  # 失败时的错误
    "timestamp": "时间戳"
}
```

## 总结

MySQL MCP Server 现在提供了完整的数据库和表管理功能：

### 🎯 核心功能
- **数据库**: 创建、删除、切换、复制、重命名
- **表**: 创建、删除、重命名、清空、结构管理
- **列**: 添加、删除、修改
- **索引**: 创建、删除、查看
- **数据**: 增删改查、搜索、统计

### 🛡️ 安全特性
- 完整的输入验证
- SQL注入防护
- 权限控制
- 操作限制

### 📊 管理功能
- 详细的统计信息
- 完整的元数据
- 灵活的查询选项
- 统一的错误处理

这些功能使得MySQL MCP Server成为一个功能完整、安全可靠的数据库管理工具。
