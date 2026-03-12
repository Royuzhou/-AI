"""
合同修订智能体 - 主入口文件
提供交互式命令行接口处理合同文件
"""

import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.agent import ContractRevisionAgent
from config import CONFIG


def list_contracts(contracts_dir):
    """列出data/contracts目录中的所有合同文件"""
    if not os.path.exists(contracts_dir):
        return []
    
    contracts = []
    for file in os.listdir(contracts_dir):
        if file.lower().endswith(('.docx', '.pdf')):
            contracts.append(file)
    
    return sorted(contracts)


def get_output_filename(input_filename):
    """生成输出文件名：输入文件名加上(revised)，格式为.txt"""
    name, ext = os.path.splitext(input_filename)
    return f"{name}(revised).txt"


def main():
    """主函数"""
    contracts_dir = "data/contracts"
    output_dir = "data/outputs"
    
    print("=" * 80)
    print("合同修订智能体")
    print("=" * 80)
    
    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)
    
    # 列出可用的合同文件
    contracts = list_contracts(contracts_dir)
    
    if not contracts:
        print(f"\n在 '{contracts_dir}' 目录中没有找到合同文件")
        print(f"请将 .docx 或 .pdf 格式的合同文件放入该目录")
        sys.exit(1)
    
    print(f"\n在 '{contracts_dir}' 目录中找到以下合同文件：\n")
    for i, contract in enumerate(contracts, 1):
        print(f"  {i}. {contract}")
    
    # 用户选择文件
    while True:
        try:
            choice = input(f"\n请输入要处理的合同文件编号 (1-{len(contracts)}) 或文件名: ").strip()
            
            # 尝试解析为编号
            try:
                index = int(choice) - 1
                if 0 <= index < len(contracts):
                    selected_file = contracts[index]
                    break
                else:
                    print(f"错误: 请输入 1 到 {len(contracts)} 之间的数字")
                    continue
            except ValueError:
                # 不是数字，尝试作为文件名
                if choice in contracts:
                    selected_file = choice
                    break
                elif choice.lower().endswith(('.docx', '.pdf')):
                    # 检查是否是完整路径
                    if os.path.exists(choice):
                        selected_file = os.path.basename(choice)
                        # 如果文件不在contracts目录，复制过去
                        if os.path.dirname(choice) != contracts_dir:
                            import shutil
                            dest_path = os.path.join(contracts_dir, selected_file)
                            shutil.copy2(choice, dest_path)
                            print(f"已将文件复制到 {contracts_dir}")
                        break
                    else:
                        print(f"错误: 找不到文件 '{choice}'")
                else:
                    print("错误: 请输入有效的编号或文件名")
                    
        except KeyboardInterrupt:
            print("\n\n用户中断")
            sys.exit(0)
    
    input_file_path = os.path.join(contracts_dir, selected_file)
    
    # 生成输出文件名
    output_filename = get_output_filename(selected_file)
    output_file_path = os.path.join(output_dir, output_filename)
    
    print(f"\n" + "-" * 80)
    print(f"输入文件: {input_file_path}")
    print(f"文件大小: {os.path.getsize(input_file_path)} 字节")
    print(f"输出文件: {output_file_path}")
    print("-" * 80)
    
    # 确认处理
    confirm = input("\n确认处理此合同? (y/n): ").strip().lower()
    if confirm != 'y':
        print("已取消处理")
        sys.exit(0)
    
    # 初始化智能体
    print("\n正在初始化智能体...")
    try:
        agent = ContractRevisionAgent(CONFIG)
        print("✓ 智能体初始化成功")
    except Exception as e:
        print(f"✗ 智能体初始化失败: {e}")
        sys.exit(1)
    
    # 处理合同
    try:
        print("\n正在处理合同...")
        result = agent.process_contract(
            input_file_path,
            output_dir=output_dir,
            output_file=output_filename
        )
        
        if result:
            print("\n" + "=" * 80)
            print("✓ 处理完成！")
            print("=" * 80)
            print(f"\n修订后的合同已保存到: {output_file_path}")
        else:
            print("\n" + "=" * 80)
            print("✗ 处理失败")
            print("=" * 80)
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n\n用户中断")
        sys.exit(0)
    except Exception as e:
        print(f"\n✗ 处理过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
