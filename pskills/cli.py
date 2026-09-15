"""pskills — 个人 Agent Skills 分发 CLI（sync 统一入口 + 软链激活）

移植自 ytalgo-data-skills 的 ytskills 并简化：仅保留 light 拷贝模式。

把本仓库的 skill 引入到宿主项目或用户 home：实体落 ``.pengxiao-skills/``（全局
``~/.pengxiao-skills/``），skill 本身在其 ``skills/`` 子目录下（``.version`` 记
来源 commit），并在检测到的 agent 配置目录（项目根有 ``.agents/`` 时只链它，否则
``.qoder`` / ``.claude`` 全建）为 skill 建相对路径软链
（``<config>/skills/<skill> -> ../../.pengxiao-skills/skills/<skill>``）。
软链纳入 git，clone 即用；改真身即改软链。

``sync`` 是唯一数据入口（首次引入 / 后续更新 / CLI 自升级一体）：

- 作用域自动判定：``-g`` 恒全局；当前在 git 仓库内即项目级（实体未引入则走首次
  引入流程）；不在 git 仓库内则交互询问是否同步全局（非交互默认否）
- 首次（目标实体 ``skills/`` 下无 skill）：clone 上游 → 交互多选（默认全选，取消则
  零落盘）→ 拷贝全部 skill 到实体 ``skills/``（实体=全量镜像）→ 选中项建软链
- 后续：重新 clone 拷贝覆盖更新实体；tty 下弹多选确认激活集（当前已激活预勾选、
  新 skill 不勾，回车对齐：勾选补链、取消勾选删链）；非交互环境不动软链，
  仅提示新增未激活 skill
- CLI 自升级：数据同步后比对本地与上游 ``pyproject.toml`` 版本，上游更新时
  ``uv tool install --reinstall``（下次运行生效）

命令::

    pskills sync [-g] [--all]            唯一数据入口：引入/更新/CLI 自升级
    pskills add [skills] [--all]         软链激活（无参交互选择，只增不减）
    pskills rm <skill>                   移除软链（不删真身）
    pskills list                         列 skill（version + git 更新时间 + 激活状态）

    # sync/add/rm/list 均支持 -g/--global：实体放 ~/.pengxiao-skills/，
    # 软链激活到 ~/.agents/skills 与 ~/.claude/skills，跨项目共享、无 git 参与

安装与升级只有一种方式（CLI 自身升级已并入 sync——版本落后上游时自动重装。
勿用 ``uv tool upgrade``：对 git 源锁 commit、不拉最新）::

    uv tool install git+ssh://git@github.com/SUSTYuxiao/pengxiao-skills.git
"""

import argparse
import importlib.metadata
import os
import re
import select
import shutil
import subprocess
import sys
import tempfile
import termios
import tty
from pathlib import Path

# CLI 内置默认上游地址（clone 用 SCP 格式），sync 无需再传
DEFAULT_REPO = "git@github.com:SUSTYuxiao/pengxiao-skills.git"
# CLI 自身安装/升级用的 PEP 508 git URL（uv tool install 格式，与上面 SCP 格式不同）
INSTALL_URL = "git+ssh://git@github.com/SUSTYuxiao/pengxiao-skills.git"
DEFAULT_BRANCH = "main"
# 实体根目录名（项目级落 <git根>/.pengxiao-skills/，全局落 ~/.pengxiao-skills/）
ENTITY_DIR = ".pengxiao-skills"
# 实体内 skill 所在的一级子目录（与上游仓库布局一致：仓库根 skills/ → 实体 skills/）
SKILLS_SUBDIR = "skills"
# 已知 agent 配置目录白名单（可扩展，如 .cursor）；默认对项目里已存在的全部激活
KNOWN_CONFIG_DIRS = [".agents", ".qoder", ".claude"]
# 项目根下存在则独占：Qoder 与 Codex 都从 .agents/skills 读，再往 .qoder/.claude 建重复软链无收益
EXCLUSIVE_CONFIG_DIR = ".agents"
# --global：Qoder 与 Codex 均从 ~/.agents/skills 读全局 skill，与 ~/.claude/skills 无条件双激活
GLOBAL_CONFIG_DIRS = [".agents", ".claude"]
DEFAULT_CONFIG_DIR = ".qoder"  # 白名单目录一个都不存在时的兜底

DRY_RUN = False


def _fail(msg, code=1):
    print(f"错误：{msg}", file=sys.stderr)
    sys.exit(code)


def _run(cmd, check=True):
    print("$ " + " ".join(cmd))
    if DRY_RUN:
        return None
    return subprocess.run(cmd, check=check, text=True)


def _git_out(cmd):
    return subprocess.check_output(
        ["git"] + cmd, text=True, stderr=subprocess.DEVNULL
    ).strip()


def _repo_root():
    try:
        return Path(_git_out(["rev-parse", "--show-toplevel"]))
    except (subprocess.CalledProcessError, FileNotFoundError):
        _fail("当前不在 git 仓库内，请在业务项目根目录执行 pskills。")


def _project_root_or_none():
    """当前目录在 git 仓库内则返回仓库根，否则 None。

    与源版 ytskills 的差异：不再要求实体目录已存在——否则全新项目无法首次引入；
    实体是否已引入由 sync 的 first_time 判定承接。
    """
    try:
        return Path(_git_out(["rev-parse", "--show-toplevel"]))
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


def _iter_skills(entity_dir):
    """实体 skills/ 下含 SKILL.md 的子目录才算 skill（排除 scripts/docs 等杂物）。"""
    skills_root = entity_dir / SKILLS_SUBDIR
    if not skills_root.is_dir():
        return []
    return sorted(
        p.name
        for p in skills_root.iterdir()
        if p.is_dir() and (p / "SKILL.md").is_file()
    )


def _explicit_skills(skills_arg, available, hint=None):
    """解析 add 的 skills 参数（逗号分隔）并校验存在性。"""
    wanted = [s.strip() for s in skills_arg.split(",") if s.strip()]
    missing = [s for s in wanted if s not in available]
    if missing:
        if hint:
            print(hint)
        _fail(f"未找到 skill：{', '.join(missing)}；可用：{', '.join(available)}")
    return wanted


def _resolve_config_dirs(root, explicit, global_mode=False):
    """确定软链激活到哪些 agent 目录。

    - 显式 --config-dir：只用它
    - 项目根下有 .agents/：只用它（Qoder 与 Codex 同读该目录，不再建重复软链）
    - 否则：自动检测项目根下白名单中已存在的目录（.qoder / .claude），全部激活
    - 都不存在：兜底用 DEFAULT_CONFIG_DIR
    - global_mode：跳过存在性检测，返回 GLOBAL_CONFIG_DIRS（.agents + .claude 无条件双激活）
    """
    if explicit:
        return [explicit]
    if global_mode:
        return list(GLOBAL_CONFIG_DIRS)
    if (root / EXCLUSIVE_CONFIG_DIR).is_dir():
        return [EXCLUSIVE_CONFIG_DIR]
    found = [d for d in KNOWN_CONFIG_DIRS if (root / d).is_dir()]
    return found or [DEFAULT_CONFIG_DIR]


def _clone_upstream(repo, branch):
    """浅 clone 上游到临时目录，返回 (临时目录, HEAD commit)。"""
    tmp = tempfile.mkdtemp(prefix="pskills-clone-")
    _run(["git", "clone", "--depth=1", "--branch", branch, repo, tmp])
    if DRY_RUN:
        return tmp, "DRYRUN"
    commit = subprocess.check_output(
        ["git", "-C", tmp, "rev-parse", "HEAD"], text=True
    ).strip()
    return tmp, commit


def _copy_skills(src_root, entity_dir):
    """把 src_root/skills/ 下所有含 SKILL.md 的目录全量拷贝到 entity_dir/skills/（已存在则覆盖）。"""
    src_skills = Path(src_root) / SKILLS_SUBDIR
    if not src_skills.is_dir():
        return []
    dst_skills = entity_dir / SKILLS_SUBDIR
    dst_skills.mkdir(parents=True, exist_ok=True)
    copied = []
    for p in sorted(src_skills.iterdir()):
        if p.is_dir() and (p / "SKILL.md").is_file():
            dst = dst_skills / p.name
            if dst.exists():
                shutil.rmtree(dst)
            shutil.copytree(p, dst, ignore=shutil.ignore_patterns(".git"))
            copied.append(p.name)
    return copied


def _read_version_file(path):
    """从 pyproject.toml 读 version = "x.y.z"；读不到返回 None。"""
    try:
        m = re.search(r'^version\s*=\s*"([^"]+)"', path.read_text(encoding="utf-8"), re.M)
    except OSError:
        return None
    return m.group(1) if m else None


def _light_fetch(entity_dir, repo, branch):
    """light 拷贝：clone 上游 → 覆盖拷贝所有 skill 到 entity_dir/skills/，写
    .version=commit（实体根）。返回 (copied, upstream_version)；dry-run 零落盘、
    零 clone，返回 (None, None)。"""
    if DRY_RUN:
        print(f"  (dry-run) 将拷贝 skill 到 {ENTITY_DIR}/{SKILLS_SUBDIR}/ 并写 .version")
        return None, None
    entity_dir.mkdir(parents=True, exist_ok=True)
    tmp, commit = _clone_upstream(repo, branch)
    try:
        copied = _copy_skills(tmp, entity_dir)
        (entity_dir / ".version").write_text(commit + "\n", encoding="utf-8")
        print(f"  已拷贝 {len(copied)} 个 skill：{', '.join(copied)}（来源 {commit[:8]}）")
        return copied, _read_version_file(Path(tmp) / "pyproject.toml")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def _first_light(entity_dir, repo, branch, all_flag):
    """首次 light：clone → 选定（交互在拷贝前弹，取消则零落盘）→ 拷贝全部 skill。

    返回 (selection, upstream_version)；selection 为 None 表示用户取消。
    """
    if DRY_RUN:
        print("  (dry-run) 将 clone 上游、拷贝全部 skill 并对选定项建软链（默认全选）")
        return [], None
    tmp, commit = _clone_upstream(repo, branch)
    try:
        src_skills = Path(tmp) / SKILLS_SUBDIR
        available = sorted(
            p.name for p in src_skills.iterdir()
            if p.is_dir() and (p / "SKILL.md").is_file()
        )
        upstream_version = _read_version_file(Path(tmp) / "pyproject.toml")
        if all_flag:
            selection = available
        elif sys.stdin.isatty() and sys.stdout.isatty():
            items = [(s, s) for s in available]
            selection = _checkbox(items, available, "首次引入：选择要激活的 skill")
            if selection is None:
                return None, None
        else:
            print("非交互环境，默认激活全部。")
            selection = available
        entity_dir.mkdir(parents=True, exist_ok=True)
        copied = _copy_skills(tmp, entity_dir)
        (entity_dir / ".version").write_text(commit + "\n", encoding="utf-8")
        print(f"  已拷贝 {len(copied)} 个 skill（来源 {commit[:8]}）")
        return selection, upstream_version
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def _activate(root, skill, config_dir, git_add=True):
    skills_dir = root / config_dir / "skills"
    link = skills_dir / skill
    target = os.path.relpath(root / ENTITY_DIR / SKILLS_SUBDIR / skill, skills_dir)
    if link.is_symlink():
        if os.readlink(link) == target:
            print(f"  = {skill} @ {config_dir}/skills/（已激活）")
            return
        print(f"  ~ {skill} @ {config_dir}/skills/ 软链指向变更，重建")
        if not DRY_RUN:
            link.unlink()
    elif link.exists():
        _fail(f"{link} 已存在且不是软链，请手动处理后重试。")
    print(f"  + {skill} @ {config_dir}/skills/ -> {target}")
    if DRY_RUN:
        return
    skills_dir.mkdir(parents=True, exist_ok=True)
    link.symlink_to(target)
    if git_add:
        _run(["git", "add", str(link.relative_to(root))])


def _current_active(root, entity_dir, config_dirs):
    """当前在任一检测目录有软链的 skill 集合。"""
    active = set()
    for cd in config_dirs:
        for s in _iter_skills(entity_dir):
            if (root / cd / "skills" / s).is_symlink():
                active.add(s)
    return active


def _reconcile_links(root, entity_dir, selected, config_dirs, global_mode):
    """把激活集精确对齐到 selected：勾选补链、取消勾选删链；已就位的静默跳过。"""
    selected = set(selected)
    for cd in config_dirs:
        skills_dir = root / cd / "skills"
        for s in _iter_skills(entity_dir):
            link = skills_dir / s
            target = os.path.relpath(root / ENTITY_DIR / SKILLS_SUBDIR / s, skills_dir)
            if s in selected:
                if link.is_symlink() and os.readlink(link) == target:
                    continue  # 已激活且指向正确，静默跳过
                _activate(root, s, cd, git_add=not global_mode)
            elif link.is_symlink():
                print(f"  - {s} @ {cd}/skills/（取消勾选，移除软链）")
                if not DRY_RUN:
                    link.unlink()
                    if not global_mode:
                        _run(["git", "add", str(link.relative_to(root))])


# ─── 交互多选 UI（纯标准库） ───────────────────────────────────────────


def _read_key():
    """读一个键：普通字符原样返回；方向键/回车/ESC 归一为 UP/DOWN/ENTER/ESC。
    EOF（空串）归一为 ESC，避免交互管道断开后死循环。"""
    ch = sys.stdin.read(1)
    if ch == "":
        return "ESC"
    if ch == "\x04":  # Ctrl-D：cbreak 下是普通字节，按 EOF/取消处理
        return "ESC"
    if ch == "\x1b":
        r, _, _ = select.select([sys.stdin], [], [], 0.05)
        if not r:
            return "ESC"
        nxt = sys.stdin.read(1)
        if nxt != "[":
            return "ESC"
        r2, _, _ = select.select([sys.stdin], [], [], 0.05)
        if not r2:
            return "ESC"
        c = sys.stdin.read(1)
        return {"A": "UP", "B": "DOWN"}.get(c, "ESC")
    if ch in ("\r", "\n"):
        return "ENTER"
    if ch == " ":
        return "SPACE"
    return ch


def _checkbox(items, default, title):
    """交互多选。items: [(name, label)]；default: 预勾选的 name 集合。

    返回选中的 name 列表（按 items 顺序）；取消（q/ESC/Ctrl-C）返回 None。
    调用方需保证 stdin/stdout 均为 tty 且非 dry-run。
    """
    names = [n for n, _ in items]
    checked = [n in set(default) for n in names]
    cursor = 0
    footer = "（空格 切换 · a 全选/全不选 · ↑↓/jk 移动 · 回车 确认 · q 取消）"
    total = len(items) + 2  # title + items + footer

    def draw(first):
        parts = []
        if not first:
            parts.append("\x1b[%dF" % total)  # 光标回到帧首
        parts.append(title + "\x1b[K\n")
        for i, (_, label) in enumerate(items):
            mark = "[*]" if checked[i] else "[ ]"
            if i == cursor:
                parts.append(f"  \x1b[36m❯ {mark} {label}\x1b[0m\x1b[K\n")
            else:
                parts.append(f"    {mark} {label}\x1b[K\n")
        parts.append(footer + "\x1b[K\n")
        sys.stdout.write("".join(parts))
        sys.stdout.flush()

    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setcbreak(fd)
        first = True
        while True:
            draw(first)
            first = False
            try:
                key = _read_key()
            except KeyboardInterrupt:
                return None
            if key in ("UP", "k"):
                cursor = (cursor - 1) % len(items)
            elif key in ("DOWN", "j"):
                cursor = (cursor + 1) % len(items)
            elif key == "SPACE":
                checked[cursor] = not checked[cursor]
            elif key == "a":
                target = not all(checked)
                checked = [target] * len(items)
            elif key == "ENTER":
                return [n for n, c in zip(names, checked) if c]
            elif key in ("q", "ESC"):
                return None
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)
        print()


def _select_via_ui(entity_dir, default, title):
    """对实体目录里的 skill 弹多选；返回选中列表或 None（取消）。"""
    items = [(s, s) for s in _iter_skills(entity_dir)]
    return _checkbox(items, default, title)


# ─── sync 作用域与 CLI 自升级 ─────────────────────────────────────────


def _confirm_global():
    if not sys.stdin.isatty():
        print("非交互环境默认跳过；如需同步全局请加 -g。")
        return False
    try:
        ans = input(
            "当前不在 git 仓库内（非项目路径），是否同步到全局"
            "（~/.pengxiao-skills/）？[y/N] "
        )
    except EOFError:
        ans = ""
    return ans.strip().lower() in ("y", "yes")


def _resolve_scope(args):
    """sync 作用域判定：-g 恒全局；git 仓库内即项目级；否则交互确认。

    返回 (root, global_mode)；用户取消/默认否返回 None。
    """
    if getattr(args, "global_mode", False):
        return Path.home(), True
    root = _project_root_or_none()
    if root is not None:
        return root, False
    print("当前非项目路径（不在 git 仓库内）。")
    if DRY_RUN:
        print("  (dry-run) 将交互询问是否作用到全局；此处按跳过处理。")
        return None
    if _confirm_global():
        return Path.home(), True
    return None


def _version_tuple(v):
    try:
        return tuple(int(x) for x in v.split("."))
    except (ValueError, AttributeError):
        return None


def _maybe_upgrade_cli(upstream_version):
    """上游 CLI 版本更新时自动重装（重装后下次运行生效）。"""
    if not upstream_version:
        return
    try:
        local = importlib.metadata.version("pengxiao-skills")
    except importlib.metadata.PackageNotFoundError:
        return  # 源码运行（未安装为工具），跳过
    up, lo = _version_tuple(upstream_version), _version_tuple(local)
    if up and lo and up > lo:
        print(f"检测到上游 CLI v{upstream_version} > 本地 v{local}，自动重装（下次运行生效）。")
        _run(["uv", "tool", "install", "--reinstall", INSTALL_URL])


# ─── 命令实现 ─────────────────────────────────────────────────────────


def cmd_sync(args):
    global_mode = getattr(args, "global_mode", False)
    scope = _resolve_scope(args)
    if scope is None:
        print("已取消，未做任何改动。")
        return
    root, global_mode = scope
    if not global_mode:
        os.chdir(root)
    entity_dir = root / ENTITY_DIR
    existing = _iter_skills(entity_dir)
    first_time = not existing
    config_dirs = _resolve_config_dirs(root, args.config_dir, global_mode)
    prefix = "~/" if global_mode else ""
    upstream_version = None

    if first_time:
        print(f"[首次引入] clone 上游并拷贝 skill（{prefix}{ENTITY_DIR}/{SKILLS_SUBDIR}/）")
        selection, upstream_version = _first_light(
            entity_dir, args.repo, args.branch, args.all)
        if selection is None:
            print("已取消，未写入任何内容。")
            return
        if not global_mode:
            _run(["git", "add", ENTITY_DIR])
        print(f"激活 skill 到：{', '.join(prefix + cd + '/skills/' for cd in config_dirs)}")
        for cd in config_dirs:
            for s in selection:
                _activate(root, s, cd, git_add=not global_mode)
        print("完成。")
        _maybe_upgrade_cli(upstream_version)
        return

    # ── 后续：重新拷贝覆盖 + 激活集确认 ──
    print("[light 模式] 重新 clone 上游并拷贝覆盖 skill")
    copied, upstream_version = _light_fetch(entity_dir, args.repo, args.branch)
    if not global_mode:
        _run(["git", "add", ENTITY_DIR])

    available = _iter_skills(entity_dir)
    active = sorted(_current_active(root, entity_dir, config_dirs))
    if copied:
        stale = [s for s in existing if s not in set(copied)]
        if stale:
            print(f"上游已移除但本地仍存在（不自动清理）：{', '.join(stale)}")

    if args.all:
        selection = available
    elif sys.stdin.isatty() and sys.stdout.isatty() and not DRY_RUN:
        title = "sync：确认激活集（勾选=激活，取消勾选=移除软链；新 skill 默认不勾）"
        selection = _select_via_ui(entity_dir, active, title)
        if selection is None:
            print("已取消，激活集保持原状（数据已更新）。")
            _maybe_upgrade_cli(upstream_version)
            return
    else:
        selection = None
        new = [s for s in available if s not in set(active)]
        if new:
            print(f"新增未激活：{', '.join(new)}"
                  "（pskills add <skill> 激活，或交互终端跑 sync 勾选）")
    if selection is not None:
        _reconcile_links(root, entity_dir, selection, config_dirs, global_mode)
        print("完成（激活集已按选择对齐）。")
    else:
        print("完成（软链保持原状）。")
    _maybe_upgrade_cli(upstream_version)


def cmd_add(args):
    global_mode = getattr(args, "global_mode", False)
    root = Path.home() if global_mode else _repo_root()
    entity_dir = root / ENTITY_DIR
    available = _iter_skills(entity_dir)
    if not available:
        _fail(f"未发现 skill（{ENTITY_DIR}/{SKILLS_SUBDIR}/ 不存在或为空）。请先执行 pskills sync。")
    config_dirs = _resolve_config_dirs(root, args.config_dir, global_mode)
    if args.skills:
        selection = _explicit_skills(args.skills, available)
    elif args.all:
        selection = available
    elif sys.stdin.isatty() and sys.stdout.isatty() and not DRY_RUN:
        active = _current_active(root, entity_dir, config_dirs)
        selection = _select_via_ui(
            entity_dir, sorted(active),
            "add：选择要激活的 skill（只增不减，当前已激活项已勾选）")
        if selection is None:
            print("已取消。")
            return
    else:
        _fail("请指定 skill 名（逗号分隔）、--all，或在交互终端直接运行 pskills add。")
    for cd in config_dirs:
        for s in selection:
            _activate(root, s, cd, git_add=not global_mode)


def cmd_rm(args):
    global_mode = getattr(args, "global_mode", False)
    root = Path.home() if global_mode else _repo_root()
    config_dirs = _resolve_config_dirs(root, args.config_dir, global_mode)
    removed = False
    for cd in config_dirs:
        link = root / cd / "skills" / args.skill
        if not link.is_symlink():
            continue
        removed = True
        print(f"  - {args.skill} @ {cd}/skills/")
        if not DRY_RUN:
            link.unlink()
            if not global_mode:
                _run(["git", "add", str(link.relative_to(root))])
    if not removed:
        print(f"{args.skill} 未在任何目录激活（{', '.join(config_dirs)}），跳过。")


def _frontmatter_field(skill_dir, key):
    """从 SKILL.md frontmatter 解析指定字段（零依赖手解析，取不到返回 '-'）。"""
    md = skill_dir / "SKILL.md"
    try:
        lines = md.read_text(encoding="utf-8").splitlines()
    except OSError:
        return "-"
    if not lines or lines[0].strip() != "---":
        return "-"
    for line in lines[1:]:
        if line.strip() == "---":
            break
        if line.startswith(key + ":"):
            return line.split(":", 1)[1].strip() or "-"
    return "-"


def _skill_version(skill_dir):
    return _frontmatter_field(skill_dir, "version")


def _git_last_date(root, rel_path):
    """skill 目录最后一次提交日期（YYYY-MM-DD），取不到返回 '-'。"""
    try:
        out = subprocess.check_output(
            ["git", "log", "-1", "--date=short", "--format=%cd", "--", rel_path],
            cwd=str(root), text=True, stderr=subprocess.DEVNULL,
        ).strip()
        return out or "-"
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "-"


def cmd_list(args):
    global_mode = getattr(args, "global_mode", False)
    root = Path.home() if global_mode else _repo_root()
    entity_dir = root / ENTITY_DIR
    available = _iter_skills(entity_dir)
    if not available:
        hint = "pskills sync -g" if global_mode else "pskills sync"
        print(f"未发现 skill（{ENTITY_DIR}/{SKILLS_SUBDIR}/ 不存在或为空）。先执行：{hint}")
        return
    config_dirs = _resolve_config_dirs(root, args.config_dir, global_mode)
    loc = f"全局 ~/{ENTITY_DIR}/" if global_mode else f"{ENTITY_DIR}/"
    print(f"可用 skill（{loc}）| 检测目录：{', '.join(config_dirs)}")
    width = max(len(s) for s in available)
    skills_root = entity_dir / SKILLS_SUBDIR
    for s in available:
        ver = _skill_version(skills_root / s)
        ver_str = f"v{ver}" if ver != "-" else "-"
        date = _git_last_date(root, f"{ENTITY_DIR}/{SKILLS_SUBDIR}/{s}")
        marks = [cd for cd in config_dirs if (root / cd / "skills" / s).is_symlink()]
        status = "已激活: " + ", ".join(marks) if marks else "未激活"
        print(
            f"  {s.ljust(width)}  {ver_str.ljust(8)} "
            f"{date.ljust(10)}  [{status}]"
        )


# ─── 参数解析 ─────────────────────────────────────────────────────────


def _add_config_dir(p):
    p.add_argument(
        "--config-dir",
        default=None,
        help="强制指定单个 agent 目录；默认自动检测项目中已存在的 .qoder / .claude 并全部激活",
    )


def _add_global(p):
    p.add_argument(
        "-g", "--global", dest="global_mode", action="store_true",
        help="全局模式：实体放 ~/.pengxiao-skills/，软链激活到 ~/.agents/skills 与 ~/.claude/skills"
    )


def parse_args(argv):
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument(
        "--dry-run", action="store_true", help="只打印将执行的操作，不写盘"
    )

    parser = argparse.ArgumentParser(
        prog="pskills",
        description="个人 Agent Skills 分发 CLI（sync 统一入口 + 软链激活）",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_sync = sub.add_parser(
        "sync", parents=[common],
        help="唯一数据入口：首次引入 / 更新 / CLI 自升级（-g 全局；非项目路径询问）",
    )
    p_sync.add_argument(
        "--all", action="store_true", help="激活全部 skill（对齐语义）"
    )
    p_sync.add_argument("--repo", default=DEFAULT_REPO, help="上游仓库（默认内置 github 地址）")
    p_sync.add_argument("--branch", default=DEFAULT_BRANCH, help=f"分支（默认 {DEFAULT_BRANCH}）")
    _add_config_dir(p_sync)
    _add_global(p_sync)
    p_sync.set_defaults(func=cmd_sync)

    p_add = sub.add_parser(
        "add", parents=[common], help="软链激活 skill（无参交互选择，只增不减）"
    )
    p_add.add_argument("skills", nargs="?", help="逗号分隔的 skill 名")
    p_add.add_argument(
        "--all", action="store_true", help="激活全部 skill"
    )
    _add_config_dir(p_add)
    _add_global(p_add)
    p_add.set_defaults(func=cmd_add)

    p_rm = sub.add_parser("rm", parents=[common], help="移除软链（不删真身）")
    p_rm.add_argument("skill", help="skill 名")
    _add_config_dir(p_rm)
    _add_global(p_rm)
    p_rm.set_defaults(func=cmd_rm)

    p_list = sub.add_parser("list", parents=[common], help="列可用 / 已激活 skill")
    _add_config_dir(p_list)
    _add_global(p_list)
    p_list.set_defaults(func=cmd_list)

    return parser.parse_args(argv)


def main(argv=None):
    global DRY_RUN
    args = parse_args(argv if argv is not None else sys.argv[1:])
    DRY_RUN = getattr(args, "dry_run", False)
    args.func(args)


if __name__ == "__main__":
    main()
