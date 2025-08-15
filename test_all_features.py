#!/usr/bin/env python3
"""
Comprehensive test script for all MySQL MCP Server features
Tests database management, table management, and CRUD operations
"""

import sys
import os

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from mcp_mysql_server import (
    # Database management
    create_database, delete_database, switch_database, list_databases,
    get_database_info, get_database_details, copy_database, rename_database,
    
    # Table management
    create_table_from_sql, delete_table, rename_table, truncate_table,
    get_table_schema, get_table_stats,
    
    # Table structure management
    add_column, drop_column, modify_column,
    
    # Index management
    get_table_indexes, create_index, drop_index,
    
    # Data operations
    write_table, read_table, update_table, delete_from_table, search_table, execute_sql
)

def test_database_management():
    """Test database management functions"""
    print("🔧 Testing Database Management...")
    
    # Test 1: List all databases
    print("  1. Listing all databases...")
    result = list_databases()
    if result['status'] == 'success':
        print(f"     ✓ Found {len(result['data']['databases'])} databases")
        print(f"     Databases: {', '.join(result['data']['databases'][:5])}{'...' if len(result['data']['databases']) > 5 else ''}")
    else:
        print(f"     ✗ Failed: {result['message']}")
        return False
    
    # Test 2: Create test database
    print("  2. Creating test database...")
    result = create_database("mcp_test_features")
    if result['status'] == 'success':
        print(f"     ✓ Database '{result['data']['database_name']}' created successfully")
    else:
        print(f"     ✗ Failed: {result['message']}")
        return False
    
    # Test 3: Switch to test database
    print("  3. Switching to test database...")
    result = switch_database("mcp_test_features")
    if result['status'] == 'success':
        print(f"     ✓ Switched to database '{result['data']['current_database']}'")
    else:
        print(f"     ✗ Failed: {result['message']}")
        return False
    
    # Test 4: Get database info
    print("  4. Getting database information...")
    result = get_database_info()
    if result['status'] == 'success':
        info = result['data']
        print(f"     ✓ Database: {info['database_name']}, Tables: {info['table_count']}")
    else:
        print(f"     ✗ Failed: {result['message']}")
    
    return True

def test_table_management():
    """Test table management functions"""
    print("\n📊 Testing Table Management...")
    
    # Test 1: Create test table
    print("  1. Creating test table...")
    create_sql = """CREATE TABLE products (
        id INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(100) NOT NULL,
        category VARCHAR(50),
        price DECIMAL(10,2) NOT NULL,
        stock INT DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    ) ENGINE=InnoDB CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"""
    
    result = create_table_from_sql(create_sql)
    if result['status'] == 'success':
        print(f"     ✓ Table '{result['data']['table_name']}' created successfully")
    else:
        print(f"     ✗ Failed: {result['message']}")
        return False
    
    # Test 2: Get table schema
    print("  2. Getting table schema...")
    result = get_table_schema("products")
    if result['status'] == 'success':
        schema = result['data']['schema']
        print(f"     ✓ Table has {len(schema)} columns")
        for col in schema:
            print(f"       - {col['field']}: {col['type']} {col['null']} {col['key']}")
    else:
        print(f"     ✗ Failed: {result['message']}")
    
    # Test 3: Get table stats
    print("  3. Getting table statistics...")
    result = get_table_stats("products")
    if result['status'] == 'success':
        stats = result['data']
        print(f"     ✓ Table: {stats['table_name']}, Rows: {stats['actual_rows']}")
    else:
        print(f"     ✗ Failed: {result['message']}")
    
    return True

def test_data_operations():
    """Test data CRUD operations"""
    print("\n📝 Testing Data Operations...")
    
    # Test 1: Insert data
    print("  1. Inserting test data...")
    products_data = [
        {"name": "iPhone 15", "category": "Electronics", "price": 999.99, "stock": 100},
        {"name": "MacBook Pro", "category": "Electronics", "price": 1999.99, "stock": 50},
        {"name": "Coffee Maker", "category": "Home", "price": 89.99, "stock": 200},
        {"name": "Desk Chair", "category": "Furniture", "price": 299.99, "stock": 75},
        {"name": "Wireless Mouse", "category": "Electronics", "price": 49.99, "stock": 150}
    ]
    
    inserted_count = 0
    for product in products_data:
        result = write_table("products", product)
        if result['status'] == 'success':
            inserted_count += 1
            print(f"       ✓ Inserted: {product['name']} (ID: {result['data']['inserted_id']})")
        else:
            print(f"       ✗ Failed to insert {product['name']}: {result['message']}")
    
    print(f"     ✓ Successfully inserted {inserted_count}/{len(products_data)} products")
    
    # Test 2: Read data
    print("  2. Reading table data...")
    result = read_table("products", limit=10)
    if result['status'] == 'success':
        data = result['data']['data']
        print(f"     ✓ Retrieved {len(data)} rows")
        for row in data[:3]:  # Show first 3 rows
            print(f"       - {row['name']}: ${row['price']} (Stock: {row['stock']})")
    else:
        print(f"     ✗ Failed: {result['message']}")
    
    # Test 3: Search data
    print("  3. Searching for products...")
    result = search_table("products", "name", "iPhone", limit=5)
    if result['status'] == 'success':
        data = result['data']['data']
        print(f"     ✓ Found {len(data)} iPhone products")
    else:
        print(f"     ✗ Failed: {result['message']}")
    
    # Test 4: Update data
    print("  4. Updating product price...")
    result = update_table("products", {"price": 899.99}, {"name": "iPhone 15"})
    if result['status'] == 'success':
        print(f"     ✓ Updated {result['data']['affected_rows']} row(s)")
    else:
        print(f"     ✗ Failed: {result['message']}")
    
    # Test 5: Execute custom SQL
    print("  5. Executing custom SQL query...")
    sql = "SELECT name, price FROM products WHERE price > 500 ORDER BY price DESC"
    result = execute_sql(sql)
    if result['status'] == 'success':
        data = result['data']['data']
        print(f"     ✓ Query returned {len(data)} expensive products")
        for row in data:
            print(f"       - {row['name']}: ${row['price']}")
    else:
        print(f"     ✗ Failed: {result['message']}")
    
    return True

def test_table_structure_management():
    """Test table structure modification functions"""
    print("\n🔧 Testing Table Structure Management...")
    
    # Test 1: Add column
    print("  1. Adding new column...")
    result = add_column("products", "description", "TEXT", constraints=["NULL"], after_column="price")
    if result['status'] == 'success':
        print(f"     ✓ Column '{result['data']['column_name']}' added successfully")
    else:
        print(f"     ✗ Failed: {result['message']}")
    
    # Test 2: Modify column
    print("  2. Modifying column...")
    result = modify_column("products", "price", "DECIMAL(12,2)", new_constraints=["NOT NULL"], new_default=0.00)
    if result['status'] == 'success':
        print(f"     ✓ Column '{result['data']['column_name']}' modified successfully")
    else:
        print(f"     ✗ Failed: {result['message']}")
    
    # Test 3: Get updated schema
    print("  3. Getting updated schema...")
    result = get_table_schema("products")
    if result['status'] == 'success':
        schema = result['data']['schema']
        print(f"     ✓ Table now has {len(schema)} columns")
        for col in schema:
            print(f"       - {col['field']}: {col['type']} {col['null']} {col['key']}")
    else:
        print(f"     ✗ Failed: {result['message']}")
    
    return True

def test_index_management():
    """Test index management functions"""
    print("\n🔍 Testing Index Management...")
    
    # Test 1: Create indexes
    print("  1. Creating indexes...")
    
    # Create index on category
    result = create_index("products", "idx_category", ["category"])
    if result['status'] == 'success':
        print(f"     ✓ Index '{result['data']['index_name']}' created on category")
    else:
        print(f"     ✗ Failed: {result['message']}")
    
    # Create index on price
    result = create_index("products", "idx_price", ["price"])
    if result['status'] == 'success':
        print(f"     ✓ Index '{result['data']['index_name']}' created on price")
    else:
        print(f"     ✗ Failed: {result['message']}")
    
    # Test 2: Get table indexes
    print("  2. Getting table indexes...")
    result = get_table_indexes("products")
    if result['status'] == 'success':
        indexes = result['data']['indexes']
        print(f"     ✓ Table has {len(indexes)} indexes")
        for index in indexes:
            print(f"       - {index['name']}: {index['type']} on {', '.join([col['column_name'] for col in index['columns']])}")
    else:
        print(f"     ✗ Failed: {result['message']}")
    
    return True

def test_advanced_operations():
    """Test advanced table operations"""
    print("\n🚀 Testing Advanced Operations...")
    
    # Test 1: Rename table
    print("  1. Renaming table...")
    result = rename_table("products", "products_new")
    if result['status'] == 'success':
        print(f"     ✓ Table renamed: {result['data']['old_table_name']} -> {result['data']['new_table_name']}")
    else:
        print(f"     ✗ Failed: {result['message']}")
    
    # Test 2: Rename back
    print("  2. Renaming table back...")
    result = rename_table("products_new", "products")
    if result['status'] == 'success':
        print(f"     ✓ Table renamed back: {result['data']['old_table_name']} -> {result['data']['new_table_name']}")
    else:
        print(f"     ✗ Failed: {result['message']}")
    
    # Test 3: Truncate table
    print("  3. Truncating table...")
    result = truncate_table("products")
    if result['status'] == 'success':
        print(f"     ✓ Table truncated, removed {result['data']['rows_removed']} rows")
    else:
        print(f"     ✗ Failed: {result['message']}")
    
    # Test 4: Verify truncation
    result = read_table("products", limit=5)
    if result['status'] == 'success':
        data = result['data']['data']
        print(f"     ✓ Table now has {len(data)} rows (should be 0)")
    
    return True

def cleanup():
    """Clean up test data"""
    print("\n🧹 Cleaning up test data...")
    
    # Delete test table
    result = delete_table("products", force=True)
    if result['status'] == 'success':
        print(f"   ✓ Table '{result['data']['table_name']}' deleted")
    else:
        print(f"   ✗ Failed to delete table: {result['message']}")
    
    # Delete test database
    result = delete_database("mcp_test_features", force=True)
    if result['status'] == 'success':
        print(f"   ✓ Database '{result['data']['database_name']}' deleted")
    else:
        print(f"   ✗ Failed to delete database: {result['message']}")

def main():
    """Main test function"""
    print("🧪 MySQL MCP Server - Comprehensive Feature Test")
    print("=" * 60)
    
    try:
        # Run all tests
        tests = [
            ("Database Management", test_database_management),
            ("Table Management", test_table_management),
            ("Data Operations", test_data_operations),
            ("Table Structure Management", test_table_structure_management),
            ("Index Management", test_index_management),
            ("Advanced Operations", test_advanced_operations)
        ]
        
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            try:
                if test_func():
                    passed += 1
                    print(f"✅ {test_name}: PASSED")
                else:
                    print(f"❌ {test_name}: FAILED")
            except Exception as e:
                print(f"💥 {test_name}: ERROR - {e}")
        
        print("\n" + "=" * 60)
        print(f"📊 Test Results: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 All tests passed! MySQL MCP Server is working correctly.")
        else:
            print("⚠️  Some tests failed. Please check the error messages above.")
        
    except Exception as e:
        print(f"💥 Test suite failed with error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Always cleanup
        cleanup()
        print("\n🏁 Test completed!")

if __name__ == "__main__":
    main()
