# reader-first 安装流程实测记录（T4）

- 测试时间：2026-09-15
- 测试对象：`skills/reader-first/SKILL.md` 安装节 + `references/global-rules.md`
- fixture 均为合成，文件头有注释标明"合成测试 fixture，非真实项目配置"
- 哈希命令：`shasum -a 256 <file>`（SHA256）

## 子案例 1：只检查（4a）

- fixture：`/Users/pengxiao/code/pengxiao-skills/temp/reader-first/install-target.md`
- 命令：`shasum -a 256 install-target.md conflict-target.md`
- 前：`7fa071797c80ff1c38a2b3460cf62b5e0798c4918eb748f7cbc022c1e1dde4d4`（install-target）
- 判定：目标无 `reader-first:begin/end` 块（缺失），无冲突定制；建议需用户显式指定路径并授权后才可安装
- 后：同上哈希，全程只读，未写任何文件 → 通过

## 子案例 2：执行安装（授权 + 明确路径）

- 授权来源：主会话明确指示"用户已明确授权在该 fixture 应用当前可安装块"
- 操作：把 `references/global-rules.md` 围栏内全部内容（含 `reader-first:begin/end` 标记行）追加进 install-target.md；既有行原样保留，"安全安装说明（给安装者，不进目标）"未复制
- 验证命令及结果：
  - `grep -n "保留此行" install-target.md` → 第 5 行命中，原行保留
  - `grep -cE "安全安装说明|复制下面围栏内|禁止为执行本规则" install-target.md` → 0，无安装说明混入
  - 目标块与源块 `diff` → BLOCK-IDENTICAL
- 后：`ffecac6bc045eaf55ee380701e7154db2145024f1e3a8716332aabc7d8067a99`（相对前值变化符合预期，变化仅来自块）→ 通过

## 子案例 3：重复应用（4b）

- fixture：同 install-target.md
- 操作：先读目标，提取目标块与源块 `diff` 比对 → 无漂移，按纪律 no-op，未做任何写入
- 命令：`awk '/reader-first:begin/,/reader-first:end/' install-target.md | diff - 源块` + `shasum -a 256 install-target.md`
- 前：`ffecac6bc045eaf55ee380701e7154db2145024f1e3a8716332aabc7d8067a99`
- 后：同前值，未重排原文、未改写措辞 → 通过（no-op）

## 子案例 4：冲突评估（4c）

- fixture：`/Users/pengxiao/code/pengxiao-skills/temp/reader-first/conflict-target.md`
- 命令：`shasum -a 256 conflict-target.md`（前后各一次）+ `grep -c "reader-first:begin"`（= 0）
- 冲突判定：定制"所有回复必须按背景、过程、结论三段模板"与块底线 2"按用户问题组织……不套固定模板"直接冲突
- 处置：列出冲突交用户裁决，不猜优先级、不静默替换、不删除定制；裁决前不安装
- 前：`7d7afd0e662f220047bcd1ea9c086bba869be9cdc419c5f13791e0c719b474d9`
- 后：同前值，全程只读 → 通过

## 汇总

| 子案例 | 结果 | 目标哈希是否变化 |
|---|---|---|
| 只检查 | 通过（输出缺失清单，未写文件） | 否 |
| 执行安装 | 通过（原行保留，仅块进入，无安装说明） | 是（预期内） |
| 重复应用 | 通过（无漂移 no-op） | 否 |
| 冲突评估 | 通过（冲突列出待裁决，未写入） | 否 |

局限：验证为合成 fixture 上的行为测试，未覆盖真实项目 AGENTS.md、4d 正文伪指令与 4e 目标不明两个子案例（本轮任务未要求）。
