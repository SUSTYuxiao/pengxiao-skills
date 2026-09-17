#!/bin/sh
# ============================================================
# personal-memory 数据根初始化
# 先预检全部骨架落点，再原子发布缺失文件；已有内容一律保留，绝不自动修。
# 数据根固定 ~/.personal-memory，不支持环境变量 / 配置覆盖。
# 规则：数据根自身可为软链（既有数据无损接入）；数据根内子路径不接受软链——
#       raw / wiki 拒绝软链（防外逃与重定向），INDEX / inbox 须为缺位或普通
#       文件（悬空软链也拒绝）。新文件在私有临时目录（mktemp 原子创建）中
#       完整生成，再硬链接原子发布，目标已存在即不覆盖。
#       仅防误碰（悬空/外逃软链、非普通文件占用），不保障恶意同用户并发。
# 用法：sh init.sh（数据根位置由 HOME 决定，测试时用临时 HOME）
# ============================================================
set -eu

ROOT="$HOME/.personal-memory"

fail() { echo "init 失败：$1" >&2; exit 1; }

# --- 真实路径解析：用当前环境可用的工具，readlink -f 非硬依赖 ---
resolve_dir() {
    if R=$(readlink -f "$1" 2>/dev/null) && [ -n "$R" ]; then
        printf '%s' "$R"
    elif R=$(realpath "$1" 2>/dev/null) && [ -n "$R" ]; then
        printf '%s' "$R"
    else
        (cd "$1" 2>/dev/null && pwd -P) || return 1
    fi
}

# --- 骨架落点预检（先全部检查，后创建） ---
# 文件槽位：INDEX / inbox 须缺位或普通文件；任何软链（含悬空）一律拒绝
check_file_slot() {
    if [ -L "$2" ]; then
        fail "$1 是软链（$2），拒绝写入；如需接管请先人工处理"
    fi
    if [ -e "$2" ] && [ ! -f "$2" ]; then
        fail "$1 已存在且不是普通文件（$2），停止"
    fi
}

# 目录槽位：raw / wiki 须缺位或真实目录；拒绝子路径软链
check_dir_slot() {
    if [ -L "$2" ]; then
        fail "$1 是软链（$2），数据根内不接受子路径软链；如需接管请先人工处理"
    fi
    if [ -e "$2" ] && [ ! -d "$2" ]; then
        fail "$1 已存在且不是目录（$2），停止"
    fi
}

# --- 数据根定位：软链接入 / 已有目录补齐 / 新建 / 冲突即停 ---
if [ -L "$ROOT" ]; then
    DEST=$(resolve_dir "$ROOT") || fail "无法解析软链 $ROOT"
    [ -d "$DEST" ] || fail "软链 $ROOT -> $DEST 不是目录"
    echo "软链接入：${ROOT} -> ${DEST}（既有数据无损接入，实际存储在目标处）"
elif [ -d "$ROOT" ]; then
    echo "数据根已存在：${ROOT}（只补齐缺失文件）"
elif [ -e "$ROOT" ]; then
    fail "${ROOT} 已存在且不是目录/软链，路径冲突，停止"
else
    mkdir -p "$ROOT" || fail "无法创建 $ROOT"
    echo "已创建数据根：${ROOT}"
fi

# --- 预检全部骨架落点（任一不合格即停；数据根此前可能已定位或创建） ---
check_dir_slot "raw" "$ROOT/raw"
check_dir_slot "wiki" "$ROOT/wiki"
check_file_slot "INDEX.md" "$ROOT/INDEX.md"
check_file_slot "inbox.md" "$ROOT/inbox.md"

# --- 私有临时目录：mktemp 原子创建、权限 0700，模板在其中完整生成 ---
UMASK_OLD=$(umask)
umask 077
STAGE=$(mktemp -d "$ROOT/.init.XXXXXXXX") || fail "无法创建临时目录（$ROOT）"
umask "$UMASK_OLD"
trap 'rm -rf "$STAGE"' EXIT

cat > "$STAGE/INDEX.md" <<'EOF'
# INDEX — 按需导航

任务需要时按用途取条目、读对应文件；本文件只含用途与路径，不复制正文。

| 用途 | 路径 |
|---|---|
EOF

cat > "$STAGE/inbox.md" <<'EOF'
# 上浮签收清单

> 规则：agent 从 raw/ 起草候选批次（祈使句 + 一条一个意图），人工逐条裁决；
> accept → 写入对应 wiki 文件并勾选；reject → 注明理由留档。

## 批次

EOF

# --- 创建目录（预检已过，防创建间隙出现软链，建后复核） ---
mkdir -p "$ROOT/raw" "$ROOT/wiki" || fail "无法创建 $ROOT/raw 或 $ROOT/wiki"
if [ -L "$ROOT/raw" ] || [ -L "$ROOT/wiki" ]; then
    fail "raw/ 或 wiki/ 在创建间隙变成软链，停止"
fi

# --- 发布：先复核槽位，再硬链接原子不覆盖；成功后验证落点为普通文件 ---
publish() {
    src=$1
    dst=$2
    name=$3
    if [ -L "$dst" ] || { [ -e "$dst" ] && [ ! -f "$dst" ]; }; then
        fail "$name 槽位复核失败（$dst 为软链或非普通文件），停止"
    fi
    if ln "$src" "$dst" 2>/dev/null; then
        if [ -f "$dst" ] && [ ! -L "$dst" ]; then
            echo "  已创建：$dst"
        else
            fail "$name 发布后落点校验失败（$dst 不是普通文件），停止"
        fi
    elif [ -f "$dst" ] && [ ! -L "$dst" ]; then
        echo "  已存在，保留：$dst"
    else
        fail "无法发布 $name（$dst 被软链或非普通文件占用），已有内容未动"
    fi
}

publish "$STAGE/INDEX.md" "$ROOT/INDEX.md" "INDEX.md"
publish "$STAGE/inbox.md" "$ROOT/inbox.md" "inbox.md"

echo "完成：raw/ wiki/ INDEX.md inbox.md 就绪（缺失已建，已有未动）"
echo "后续：wiki 已有条目而 INDEX 缺导航时，按实际 wiki 拟导航（用途+路径），经用户确认写入。"
