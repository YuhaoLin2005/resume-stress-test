#!/usr/bin/env python3
"""从 prompts/00-总控调度器.md 抽取 01/02/03 三个独立文件。

这个包的核心设计是「单源维护」：三个角色的完整提示词只写在 00 里，
01/02/03 是从 00 机械抽取的副本，供多窗口模式单独粘贴。

单源维护最大的风险是「改了 00，忘了同步」——而模式B 的用户只读 01/02/03，
漂移不会自己暴露。这个脚本把那件事从「靠自觉」变成「靠检查」。

用法：
    python scripts/sync-modules.py           # 重新抽取，覆盖 01/02/03
    python scripts/sync-modules.py --check   # 只检查是否漂移，不写文件
                                             # 漂移则 exit 1

使用者不需要运行这个脚本——直接读 prompts/ 下的文件即可。
这是给维护者用的。
"""

import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROMPTS = os.path.join(ROOT, "prompts")
MASTER = os.path.join(PROMPTS, "00-总控调度器.md")

# 编号 → (输出文件名, 标题, 需粘贴说明)
SPEC = {
    "1": (
        "01-HR风控层.md",
        "角色1 · HR 风控筛查层（攻 · 真实性）",
        "岗位 JD + 简历 + 候选人身份",
    ),
    "2": (
        "02-业务终审层.md",
        "角色2 · 业务负责人终审层（攻 · 落地能力）",
        "岗位 JD + 原始简历 + 交接文档1",
    ),
    "3": (
        "03-初答回归层.md",
        "角色3 · HR 初答回归层（守 · 可读性）",
        "岗位 JD + 修订版简历（仅此两样，不放任何风险清单）",
    ),
}

HEADER = """# {title}

> **本文件用途**：多窗口模式（模式B）下单独粘贴的启动指令。
> **需粘贴**：{inputs}
> ⚠️ 本文件是从 `00-总控调度器.md` **机械抽取**的，**不要手动编辑**。
> 改内容请改 `00`，然后跑 `python scripts/sync-modules.py` 重新抽取。

---

{body}
"""


def extract(master_text, n):
    m = re.search(rf"MODULE-{n}【.*?\[/MODULE-{n}\]", master_text, re.S)
    if not m:
        raise SystemExit(f"SYNC:ERROR: 在 00 里找不到 MODULE-{n} 的标记对")
    return m.group(0)


def build(master_text):
    out = {}
    for n, (fname, title, inputs) in SPEC.items():
        out[fname] = HEADER.format(title=title, inputs=inputs, body=extract(master_text, n))
    return out


def main():
    check = "--check" in sys.argv

    if not os.path.exists(MASTER):
        raise SystemExit(f"SYNC:ERROR: 找不到 {MASTER}")

    with open(MASTER, encoding="utf-8") as f:
        master_text = f.read()

    expected = build(master_text)
    drifted = []

    for fname, content in expected.items():
        path = os.path.join(PROMPTS, fname)
        if check:
            actual = None
            if os.path.exists(path):
                with open(path, encoding="utf-8") as f:
                    actual = f.read()
            if actual != content:
                drifted.append(fname)
        else:
            with open(path, "w", encoding="utf-8", newline="\n") as f:
                f.write(content)
            print(f"SYNC:WROTE: {fname} ({len(content.encode('utf-8'))} bytes)")

    if check:
        if drifted:
            print("SYNC:DRIFT: 以下文件与 00 不一致 ——")
            for d in drifted:
                print(f"  - {d}")
            print("修复：python scripts/sync-modules.py")
            sys.exit(1)
        print(f"SYNC:OK: 01/02/03 与 00 一致（{len(expected)} 个文件）")

    sys.exit(0)


if __name__ == "__main__":
    main()
