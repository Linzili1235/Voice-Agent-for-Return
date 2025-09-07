#!/usr/bin/env python3
# 服务器设置验证脚本 - 检查 FastAPI HTTP Tools 服务器设置
import sys
import os
import importlib

def check_imports():
    """检查所有必要的模块是否可以正确导入"""
    modules_to_check = [
        'fastapi',
        'uvicorn',
        'pydantic',
        'pydantic_settings',
        'httpx',
        'structlog',
        'prometheus_client',
        'redis',
        'pytest',
        'pytest_asyncio'
    ]
    
    print("检查 Python 依赖...")
    failed_imports = []
    
    for module in modules_to_check:
        try:
            importlib.import_module(module)
            print(f"✓ {module}")
        except ImportError as e:
            print(f"✗ {module}: {e}")
            failed_imports.append(module)
    
    return failed_imports

def check_server_structure():
    """检查服务器项目结构是否完整"""
    print("\n检查服务器项目结构...")
    
    required_files = [
        'server/requirements.txt',
        'server/.env.example',
        'server/app/config.py',
        'server/app/schemas.py',
        'server/app/vendors.py',
        'server/app/utils.py',
        'server/app/main.py',
        'server/app/services/email_service.py',
        'server/app/services/sms_service.py',
        'server/app/services/kb_service.py',
        'server/app/routers/tools_email.py',
        'server/app/routers/tools_misc.py',
        'server/app/routers/meta.py',
        'tests/test_make_rma_email.py',
        'README.md'
    ]
    
    missing_files = []
    
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"✓ {file_path}")
        else:
            print(f"✗ {file_path}")
            missing_files.append(file_path)
    
    return missing_files

def check_app_imports():
    """检查应用模块是否可以正确导入"""
    print("\n检查应用模块导入...")
    
    # Add server directory to path
    server_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'server')
    sys.path.insert(0, server_dir)
    
    app_modules = [
        'app.config',
        'app.schemas',
        'app.vendors',
        'app.utils',
        'app.services.email_service',
        'app.services.sms_service',
        'app.services.kb_service',
        'app.routers.tools_email',
        'app.routers.tools_misc',
        'app.routers.meta',
        'app.main'
    ]
    
    failed_imports = []
    
    for module in app_modules:
        try:
            importlib.import_module(module)
            print(f"✓ {module}")
        except ImportError as e:
            print(f"✗ {module}: {e}")
            failed_imports.append(module)
    
    return failed_imports

def test_basic_functionality():
    """测试基本功能"""
    print("\n测试基本功能...")
    
    try:
        # Add server directory to path
        server_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'server')
        sys.path.insert(0, server_dir)
        
        # Test vendor configuration
        from app.vendors import get_vendor_config, format_rma_email
        
        vendor_config = get_vendor_config("amazon")
        print(f"✓ 供应商配置: {vendor_config.name}")
        
        # Test RMA email generation
        subject, body = format_rma_email(
            vendor_config=vendor_config,
            order_id="TEST-123",
            item_sku="SKU-456",
            intent="return",
            reason="damaged",
            evidence_urls=["https://example.com/photo.jpg"],
            contact_email="test@example.com"
        )
        
        print(f"✓ RMA 邮件生成: {len(subject)} 字符主题, {len(body)} 字符正文")
        
        # Test schemas
        from app.schemas import MakeRMAEmailRequest
        
        request = MakeRMAEmailRequest(
            vendor="amazon",
            order_id="TEST-123",
            item_sku="SKU-456",
            intent="return",
            reason="damaged",
            evidence_urls=["https://example.com/photo.jpg"]
        )
        
        print(f"✓ 数据模式验证: {request.vendor}")
        
        return True
        
    except Exception as e:
        print(f"✗ 基本功能测试失败: {e}")
        return False

def main():
    """主函数"""
    print("FastAPI HTTP Tools 服务器设置验证")
    print("=" * 50)
    
    # 检查 Python 依赖
    failed_deps = check_imports()
    
    # 检查项目结构
    missing_files = check_server_structure()
    
    # 检查应用模块导入
    failed_app_imports = check_app_imports()
    
    # 测试基本功能
    basic_test_passed = test_basic_functionality()
    
    # 总结
    print("\n" + "=" * 50)
    print("验证结果总结:")
    
    if not failed_deps and not missing_files and not failed_app_imports and basic_test_passed:
        print("✓ 所有检查都通过了！服务器设置正确。")
        print("\n下一步:")
        print("1. 复制 server/.env.example 到 server/.env 并配置环境变量")
        print("2. 运行 'python run_server.py' 启动服务器")
        print("3. 运行 'pytest tests/test_make_rma_email.py' 执行测试")
        print("4. 访问 http://localhost:8787/docs 查看 API 文档")
        return 0
    else:
        print("✗ 发现以下问题:")
        
        if failed_deps:
            print(f"  - 缺少依赖: {', '.join(failed_deps)}")
            print("    运行: pip install -r server/requirements.txt")
        
        if missing_files:
            print(f"  - 缺少文件: {', '.join(missing_files)}")
        
        if failed_app_imports:
            print(f"  - 模块导入失败: {', '.join(failed_app_imports)}")
        
        if not basic_test_passed:
            print("  - 基本功能测试失败")
        
        return 1

if __name__ == "__main__":
    sys.exit(main())

