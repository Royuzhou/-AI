"""
批量更新 YAML 配置文件中的服务器路径为绝对路径
使用简单的字符串替换，避免正则表达式问题
"""

import os
from pathlib import Path


def update_yaml_paths(base_dir: str):
    """更新所有 YAML 文件中的服务器路径为绝对路径"""
    
    base_path = Path(base_dir)
    servers_dir = base_path / "UltraRAG" / "servers"
    
    # 获取所有服务器目录的绝对路径 (使用 forward slashes)
    server_paths = {}
    if servers_dir.exists():
        for server_folder in servers_dir.iterdir():
            if server_folder.is_dir():
                server_name = server_folder.name
                # 使用正斜杠，避免 YAML 转义问题
                abs_path = str(server_folder.resolve()).replace('\\', '/')
                server_paths[server_name] = abs_path
    
    print("=" * 80)
    print("找到的服务器目录:")
    print("=" * 80)
    for name, path in server_paths.items():
        print(f"{name}: {path}")
    
    # 查找所有 YAML 配置文件
    examples_dir = base_path / "UltraRAG" / "examples"
    yaml_files = list(examples_dir.glob("*.yaml"))
    server_yaml_files = list((examples_dir / "server").glob("*.yaml"))
    all_yaml_files = yaml_files + server_yaml_files
    
    print(f"\n需要更新的 YAML 文件数量：{len(all_yaml_files)}")
    print("=" * 80)
    
    updated_count = 0
    
    for yaml_file in all_yaml_files:
        try:
            # 读取 YAML 文件
            with open(yaml_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            new_lines = []
            file_updated = False
            
            # 逐行处理
            for line in lines:
                original_line = line
                
                # 检查是否是服务器定义行
                for server_name, abs_path in server_paths.items():
                    # 匹配模式：server_name: servers/server_name
                    pattern = f"{server_name}: servers/{server_name}"
                    replacement = f"{server_name}: {abs_path}"
                    
                    if pattern in line:
                        new_line = line.replace(pattern, replacement)
                        print(f"✓ 更新 {yaml_file.name}: {server_name}")
                        print(f"  原路径：{pattern}")
                        print(f"  新路径：{replacement}")
                        new_lines.append(new_line)
                        file_updated = True
                        updated_count += 1
                        break
                else:
                    new_lines.append(line)
            
            # 如果内容有变化，写回文件
            if file_updated:
                with open(yaml_file, 'w', encoding='utf-8') as f:
                    f.writelines(new_lines)
        
        except Exception as e:
            print(f"✗ 处理 {yaml_file.name} 失败：{e}")
    
    print("\n" + "=" * 80)
    print(f"更新完成！共更新了 {updated_count} 个服务器引用")
    print("=" * 80)

if __name__ == "__main__":
    # 获取项目根目录
    current_dir = Path.cwd()
    print(f"当前工作目录：{current_dir}")
    
    update_yaml_paths(str(current_dir))
    
    print("\n✅ 所有 YAML 配置文件中的服务器路径已更新为绝对路径")
