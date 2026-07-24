"""修订输出格式校验 — §CHANGE...§END 标签格式"""
import re, sys


class FormatError(ValueError):
    def __init__(self, errors: list[str]):
        self.errors = errors
        super().__init__("; ".join(errors))


def validate_revision_format(revised_content: str) -> tuple[bool, list[str]]:
    errors = []

    if "【修订后的完整合同】" not in revised_content:
        errors.append("缺少'【修订后的完整合同】'标题")

    if "【修改建议清单】" not in revised_content:
        errors.append("缺少'【修改建议清单】'标题")

    if "§CHANGE" not in revised_content:
        errors.append("缺少 §CHANGE 标签——每条修改须以 §CHANGE 开头")

    # 检查 4 个必要子标签
    for tag in ["§ORIGINAL", "§LAW", "§SUGGESTION", "§REVISED", "§END"]:
        if tag not in revised_content:
            errors.append(f"缺少 {tag} 标签")

    if not re.search(r'《[^》]+》\s*第[\d一二三四五六七八九十百千]+条', revised_content):
        errors.append("修改建议中未检测到法条引用（如'《民法典》第585条'）")

    return len(errors) == 0, errors


def _main():
    if len(sys.argv) > 1:
        content = sys.argv[1]
    else:
        content = sys.stdin.read()
    valid, errors = validate_revision_format(content)
    if valid:
        print("格式校验通过")
        return 0
    else:
        print("格式校验失败:")
        for e in errors:
            print(f"  - {e}")
        return 1


if __name__ == "__main__":
    sys.exit(_main())
