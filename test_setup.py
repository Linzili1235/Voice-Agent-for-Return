#!/usr/bin/env python3
# 项目设置验证脚本 - 检查项目结构和依赖是否正确安装
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

def check_project_structure():
    """检查项目结构是否完整"""
    print("\n检查项目结构...")
    
    required_files = [
        'main.py',
        'requirements.txt',
        '.env.example',
        'README.md',
        'Dockerfile',
        'pytest.ini',
        'app/__init__.py',
        'app/config/settings.py',
        'app/schemas/base.py',
        'app/schemas/vapi.py',
        'app/schemas/mcp.py',
        'app/utils/logging.py',
        'app/utils/security.py',
        'app/utils/cache.py',
        'app/services/vapi_service.py',
        'app/services/mcp_service.py',
        'app/routers/health.py',
        'app/routers/metrics.py',
        'app/routers/vapi.py',
        'app/routers/mcp.py',
        'tests/conftest.py',
        'tests/test_health.py',
        'tests/test_metrics.py',
        'tests/test_vapi.py',
        'tests/test_mcp.py',
        'tests/test_utils.py'
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
    
    app_modules = [
        'app.config.settings',
        'app.schemas.base',
        'app.schemas.vapi',
        'app.schemas.mcp',
        'app.utils.logging',
        'app.utils.security',
        'app.utils.cache',
        'app.services.vapi_service',
        'app.services.mcp_service',
        'app.routers.health',
        'app.routers.metrics',
        'app.routers.vapi',
        'app.routers.mcp'
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

def main():
    """主函数"""
    print("Vapi Agent API 项目设置验证")
    print("=" * 50)
    
    # 检查 Python 依赖
    failed_deps = check_imports()
    
    # 检查项目结构
    missing_files = check_project_structure()
    
    # 检查应用模块导入
    failed_app_imports = check_app_imports()
    
    # 总结
    print("\n" + "=" * 50)
    print("验证结果总结:")
    
    if not failed_deps and not missing_files and not failed_app_imports:
        print("✓ 所有检查都通过了！项目设置正确。")
        print("\n下一步:")
        print("1. 复制 .env.example 到 .env 并配置环境变量")
        print("2. 运行 'python run.py' 启动开发服务器")
        print("3. 运行 'pytest' 执行测试")
        return 0
    else:
        print("✗ 发现以下问题:")
        
        if failed_deps:
            print(f"  - 缺少依赖: {', '.join(failed_deps)}")
            print("    运行: pip install -r requirements.txt")
        
        if missing_files:
            print(f"  - 缺少文件: {', '.join(missing_files)}")
        
        if failed_app_imports:
            print(f"  - 模块导入失败: {', '.join(failed_app_imports)}")
        
        return 1

if __name__ == "__main__":
    sys.exit(main())
