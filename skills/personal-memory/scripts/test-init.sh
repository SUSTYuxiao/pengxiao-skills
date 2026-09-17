#!/bin/sh
# ============================================================
# init.sh 行为测试 — 全程在临时 HOME 中运行，不触碰真实 HOME
# 覆盖：干净首次 / 重复幂等 / 既有内容保留 / 路径冲突 / 软链接入 /
#       悬空软链 / 外部软链 / 文件槽位为目录 / 子目录软链与文件冲突 /
#       并行竞争；每个场景后校验无临时文件残留
# 用法：sh test-init.sh
# ============================================================
set -eu

HERE=$(cd "$(dirname "$0")" && pwd)
TMP=$(mktemp -d /tmp/pm-init-test.XXXXXX)
trap 'rm -rf "$TMP"' EXIT

pass() { echo "PASS: $1"; }
fail_test() { echo "FAIL: $1" >&2; exit 1; }

N=0
new_home() {
    N=$((N + 1))
    HOME="$TMP/home-$N"
    mkdir -p "$HOME"
    export HOME
}

root() { printf '%s/.personal-memory' "$HOME"; }

# 数据根内不得残留 init 临时目录/文件
no_temp_leftover() {
    if ls -d "$(root)"/.init.* >/dev/null 2>&1; then
        fail_test "发现临时目录残留：$(root)"
    fi
}

# ---------- 1. 干净首次 init ----------
new_home
sh "$HERE/init.sh" > /dev/null || fail_test "首次 init 非零退出"
for f in raw wiki INDEX.md inbox.md; do
    [ -e "$(root)/$f" ] || fail_test "首次 init 缺 $f"
done
[ -f "$(root)/INDEX.md" ] && [ ! -L "$(root)/INDEX.md" ] || fail_test "INDEX 不是普通文件"
grep -q "INDEX — 按需导航" "$(root)/INDEX.md" || fail_test "INDEX 内容不完整"
no_temp_leftover
pass "干净首次 init 建全骨架"

# ---------- 2. 重复 init 幂等 ----------
BEFORE=$(shasum -a 256 "$(root)/INDEX.md" "$(root)/inbox.md")
sh "$HERE/init.sh" > /dev/null || fail_test "重复 init 非零退出"
AFTER=$(shasum -a 256 "$(root)/INDEX.md" "$(root)/inbox.md")
[ "$BEFORE" = "$AFTER" ] || fail_test "重复 init 改动了已有文件"
no_temp_leftover
pass "重复 init 幂等"

# ---------- 3. 既有内容全保留 ----------
echo "NAV MINE" > "$(root)/INDEX.md"
echo "MY RULE" > "$(root)/wiki/mine.md"
echo "RAW KEEP" > "$(root)/raw/keep.md"
sh "$HERE/init.sh" > /dev/null || fail_test "已有内容场景 init 非零退出"
grep -q "NAV MINE" "$(root)/INDEX.md" || fail_test "已有 INDEX 被覆盖"
grep -q "MY RULE" "$(root)/wiki/mine.md" || fail_test "已有 wiki 文件被改动"
grep -q "RAW KEEP" "$(root)/raw/keep.md" || fail_test "已有 raw 文件被改动"
no_temp_leftover
pass "既有内容（INDEX/wiki/raw）全保留"

# ---------- 4. 路径冲突（普通文件占用数据根位置） ----------
new_home
echo "not a dir" > "$(root)"
if sh "$HERE/init.sh" > /dev/null 2>&1; then
    fail_test "路径冲突未停止"
fi
[ "$(cat "$(root)")" = "not a dir" ] || fail_test "冲突文件被改动"
pass "路径冲突停止且现场未动"

# ---------- 5. 软链接入（既有目录无损接入 + 缺失补齐） ----------
new_home
SRC="$TMP/existing-memory"
mkdir -p "$SRC/wiki"
echo "KEEP ME" > "$SRC/wiki/keep.md"
ln -s "$SRC" "$(root)"
sh "$HERE/init.sh" > /dev/null || fail_test "软链 init 非零退出"
[ -L "$(root)" ] || fail_test "软链被替换成实体目录"
[ -e "$SRC/INDEX.md" ] || fail_test "软链目标未补齐 INDEX"
grep -q "KEEP ME" "$SRC/wiki/keep.md" || fail_test "软链目标既有文件被改动"
no_temp_leftover
pass "软链接入：既有数据无损 + 缺失补齐"

# ---------- 6. INDEX 为悬空软链：拒绝且不写穿 ----------
new_home
mkdir -p "$(root)"
ln -s "$TMP/no-such-target-$$" "$(root)/INDEX.md"
if sh "$HERE/init.sh" > /dev/null 2>&1; then
    fail_test "悬空软链未拒绝"
fi
[ -L "$(root)/INDEX.md" ] || fail_test "悬空软链被改动"
[ ! -e "$(root)/inbox.md" ] || fail_test "拒绝后仍创建了其他骨架"
no_temp_leftover
pass "INDEX 悬空软链拒绝，不写穿不部分创建"

# ---------- 7. INDEX 为外部软链：拒绝且目标不被截断 ----------
new_home
EXT="$TMP/external-$$"
echo "SECRET" > "$EXT"
mkdir -p "$(root)"
ln -s "$EXT" "$(root)/INDEX.md"
if sh "$HERE/init.sh" > /dev/null 2>&1; then
    fail_test "外部软链未拒绝"
fi
[ "$(cat "$EXT")" = "SECRET" ] || fail_test "外部软链目标被写入"
no_temp_leftover
pass "INDEX 外部软链拒绝，目标未被写穿"

# ---------- 8. INDEX 为目录：拒绝 ----------
new_home
mkdir -p "$(root)/INDEX.md"
if sh "$HERE/init.sh" > /dev/null 2>&1; then
    fail_test "INDEX 为目录未拒绝"
fi
[ -d "$(root)/INDEX.md" ] && [ ! -e "$(root)/INDEX.md/INDEX.md" ] || fail_test "目录槽位被改动"
pass "INDEX 为目录拒绝"

# ---------- 9. raw 为外部软链：拒绝且外部目录不被写入 ----------
new_home
EXTD="$TMP/external-dir-$$"
mkdir -p "$EXTD" "$(root)"
ln -s "$EXTD" "$(root)/raw"
if sh "$HERE/init.sh" > /dev/null 2>&1; then
    fail_test "raw 外部软链未拒绝"
fi
[ -z "$(ls -A "$EXTD")" ] || fail_test "外部软链目录被写入"
pass "raw 子路径软链拒绝，外逃目录未被写入"

# ---------- 10. raw 为普通文件：拒绝 ----------
new_home
mkdir -p "$(root)"
echo "i am a file" > "$(root)/raw"
if sh "$HERE/init.sh" > /dev/null 2>&1; then
    fail_test "raw 为普通文件未拒绝"
fi
[ "$(cat "$(root)/raw")" = "i am a file" ] || fail_test "raw 文件被改动"
pass "raw 为普通文件拒绝且未覆盖"

# ---------- 11. inbox 为外部软链：拒绝 ----------
new_home
EXTI="$TMP/external-inbox-$$"
echo "INBOX SECRET" > "$EXTI"
mkdir -p "$(root)"
ln -s "$EXTI" "$(root)/inbox.md"
if sh "$HERE/init.sh" > /dev/null 2>&1; then
    fail_test "inbox 外部软链未拒绝"
fi
[ "$(cat "$EXTI")" = "INBOX SECRET" ] || fail_test "inbox 外部目标被写入"
pass "inbox 外部软链拒绝"

# ---------- 12. 并行竞争：双实例同时 init，内容完整无残留 ----------
new_home
sh "$HERE/init.sh" > "$TMP/p1.log" 2>&1 & P1=$!
sh "$HERE/init.sh" > "$TMP/p2.log" 2>&1 & P2=$!
wait "$P1" || fail_test "并行实例1 失败"
wait "$P2" || fail_test "并行实例2 失败"
grep -q "INDEX — 按需导航" "$(root)/INDEX.md" || fail_test "并行后 INDEX 内容不完整"
grep -q "上浮签收清单" "$(root)/inbox.md" || fail_test "并行后 inbox 内容不完整"
no_temp_leftover
pass "并行竞争：原子发布无损坏无残留"

echo "全部通过（临时目录已清理：${TMP}）"
