# A4 切片独立同行评审（只看 diff 与测试）

评审人：独立评审者（未参与编写，未阅读作者的解释性文档 `slice-notes.md` / `edge-cases.md` / `task-contract.md` / `rollback.md`）
评审对象：`A4/work/UCAS-course-planner` 上 `upstream/main..a4-slice` 的唯一提交 **`7e17a215564feeb3f5d0199941d51ddc21ab4324`**（`slice: advise the order to register in, from the plan's own data`）
评审日期：2026-10-05

## 0. 取证方式（可复现）

```bash
cd "…/A4/work/UCAS-course-planner"
git log --oneline upstream/main..7e17a21
# 7e17a21 slice: advise the order to register in, from the plan's own data

git diff --stat upstream/main 7e17a21
#  .gitignore              |   3 +
#  app/page.tsx            |  58 ++++++++++++++++
#  lib/priority-mapping.ts |  45 ++++++++++++
#  lib/priority.ts         | 140 +++++++++++++++++++++++++++++++++++++
#  tests/priority.test.ts  | 178 ++++++++++++++++++++++++++++++++++++++++++++++++
#  tsconfig.json           |   1 +
#  6 files changed, 425 insertions(+)

git rev-parse upstream/main
# 68e7080503084a41f42db6e0e9ff94c0e9ef2f19
```

仓库工作树的 HEAD 在评审过程中被外部切过两次（我先看到 `7e17a21`，随后是 `rollback-test`（该提交是这 425 行的完整 revert），最后又是 `a4-slice`）。为不受影响，全部结论钉在不可变提交 `7e17a21` 上，用只读方式取树后**在 /tmp 里**跑测试与构建：

```bash
git archive 7e17a21 | tar -x -C /tmp/a4slice
ln -s "<repo>/node_modules" /tmp/a4slice/node_modules
git archive 68e7080  | tar -x -C /tmp/a4base && ln -s "<repo>/node_modules" /tmp/a4base/node_modules
```

评审结束时 `git status --short` 为空，我没有修改仓库任何文件，也没有执行任何 git 写操作；下面所有探针都写在 `/tmp/probe*.ts`。

基线绿色检查（切片 vs `upstream/main`，两侧都跑）：

```bash
# /tmp/a4slice（含本切片）
node --experimental-strip-types --test tests/priority.test.ts
# # tests 20 / # pass 20 / # fail 0
npx tsc --noEmit          # exit 0（无输出）
npm run build             # ✓ built in 3.12s … [5/5] … 112 modules transformed. exit 0
npm run lint              # Found 0 warnings and 0 errors. Finished in 1.7s on 8 files

# /tmp/a4base（upstream/main）
npx tsc --noEmit          # exit 0
npm run build             # ✓ built in 3.19s … 110 modules transformed. exit 0
```

结论先行：**构建/类型/测试三条线全绿，切片边界干净；但它的核心输出在自家数据上不成立，且有一处会误导用户的语义冲突。可以合入，但不应当作"已交付价值"来宣称。**

---

## 1. 正确性

### 1.1 实现与它自称的规则一致 —— 这条我反证失败，是正面的

`lib/priority.ts:88-94` 写明了 5 级排序键。我按文档**独立重写**了一遍排序键（`/tmp/probe5.ts`），对 5000 个随机方案做差分：

```bash
node --experimental-strip-types /tmp/probe5.ts
# trials: 5000 | orders differing from the documented rule: 0 | calls that mutated their input: 0
```

即：文档 ↔ 实现一致，且 `rankPlan` 不修改调用方数组（`:101-104` 的 `filter`/`map` 产生新数组，`sort` 只作用于新数组）。这条我没有找到反例。

### 1.2 `selected` 被当作权威的实时报名数（**我认为这是最严重的问题**）

- 规则的前提写在 `lib/priority.ts:11-13`：*"what matters first is **how much room is left** (risk of losing the section)"*。
- `placesLeft` = `limit - enrolled`（`lib/priority.ts:59-62`），`enrolled` 来自行数据的 `selected`（`lib/priority-mapping.ts:26-32`），页面从计划里读这两个字段（`app/page.tsx:695-696`）。
- 但 `public/data/courses.json` 里的 `selected` 是一份**基本为空的快照**：

```bash
node --experimental-strip-types /tmp/probe3.ts
# rows with capacity>0: 1978 | of those selected===0: 1968 (94.8% of all 2077 rows)
# rows with capacity===0 (sentinel): 99
```

`selected>0` 的只有 10 行，其中 5 行是 `118`（马院公共课）。于是 `placesLeft` 在 94.8% 的行上**恒等于 `capacity`**：排序实际排的是"班级容量大小"，不是"抢课风险"。

- 更尖锐的一点：映射层对邻字段的处理是不对称的。`capacity===0` 被郑重地当作哨兵映射成 `unknown`，并在 `lib/priority-mapping.ts:25-30` 与注释 `:1-10` 里反复论证"不能让 0 变成满员，否则会**发明一场危机**"；而同样"基本没填"的 `selected===0` 却没有任何等价的怀疑，`caveats`（`lib/priority.ts:127-137`）和面板硬编码的 bullet（`app/page.tsx:1299-1301`）都只说"没有开课学期字段"。**同一份数据、相邻两个字段，一个被诚实降级，一个被当权威用**。这恰恰是它自己批评的那种错误方向的反面版本：不是发明危机，而是发明安心。

真实方案上的输出（`/tmp/probe3.ts`，5 门真实课程，渲染逻辑照抄 `app/page.tsx:1284-1301`）：

```
--- 抢课顺序建议 (what the user sees) ---
  1. [无法判断] 带稿同传-I 180089055102M3001H — 该班次没有容量数据，依据现有数据无法判断抢课风险
  2. [从容] 抽象代数II 180080070100M1004H — 剩余 35 个名额
  3. [从容] 自然辩证法概论 180213010108MB001H-14 — 剩余 192 个名额
  4. [从容] 固体物理（材料与化工） 180092085601P2003H — 剩余 199 个名额
  5. [从容] 现代数字信号处理I一班 180093081000P1001H-1 — 剩余 212 个名额
--- raw capacity/selected behind those reasons ---
  180080070100M1004H capacity=35 selected=0
  180089055102M3001H capacity=0 selected=0
  180213010108MB001H-14 capacity=310 selected=118
  180093081000P1001H-1 capacity=214 selected=2
  180092085601P2003H capacity=200 selected=1
```

"剩余 199 个名额"是对一个尚未/尚未更新报名的字段的断言，且**没有任何 caveat 提示这一点**。这是面向用户的错误陈述，不只是代码问题。

### 1.3 `critical`（"优先抢"）在出厂数据下不可达

`critical` 只有两条路径（`lib/priority.ts:70-76`）：`left<=0`，或 `required && autumnOnly && left<=10`。

```bash
node --experimental-strip-types /tmp/probe3.ts
# urgency reachable from the shipped catalog: {"normal":1976,"high":2,"unknown":99}
# （critical 0；另：selected>=capacity(>0) 的行数为 0）
```

- `left<=0` 需要 `selected>=capacity`：全表 0 行。
- `required && autumnOnly` 需要 `autumnOnly`：页面**从不传**这个字段（`app/page.tsx:689-700` 的映射里没有 `autumnOnly`；`lib/priority-mapping.ts:42` 只会得到 `undefined`），面板自己也在 `app/page.tsx:1299-1301` 声明"本数据没有开课学期字段"。

所以 `app/page.tsx:27-32` 的 `URGENCY_LABEL['critical'] = '优先抢'` 在产品里永远不会出现，`high` 也只有 2 行可达。四档词汇实际退化成两档（`无法判断` / `从容`）。

### 1.4 排序键第 1 档把"无法判断"放在"快满"之前，与面板自己的标题冲突

```bash
node --experimental-strip-types /tmp/probe1.ts
# --- P2: unknown vs critically-full, relative position ---
# 1.FULL[critical] 2.MYSTERY[unknown] 3.TIGHT[high]
```

`WEIGHT`（`lib/priority.ts:83`）= `{critical:0, unknown:1, high:2, normal:3}`，即"没有数据"的课排在"只剩 5 个名额"的课**前面**。文档 `:88-90` 承认这是刻意的（"not knowing is closer to a risk than to a reassurance"），理由我可以接受；**但它落在 UI 上就成了矛盾**：面板标题与空态文案是"按名额风险给出先抢哪一门"（`app/page.tsx:1282, 1296`），而 `<ol>` 的第 1 项恰恰是 `[无法判断] …`（见 1.2 的真实输出）。一个自称"无法判断"的条目占据"抢课顺序"第一位，是在给一条确定指令。建议：`unknown` 条目移出 `<ol>`，或把标签改成"请自行核实"这类不构成指令的措辞。

### 1.5 `FEW_PLACES` 边界是一个断崖（当前不可达，但一填数据就生效）

```bash
node --experimental-strip-types /tmp/probe1.ts
# --- P1: required+autumnOnly, 10 vs 11 places left (cliff at FEW_PLACES=10) ---
# 10 left: {"level":"critical","reason":"学位必修且仅秋季开课，只剩 10 个名额"}
# 11 left: {"level":"normal","reason":"剩余 11 个名额"}
```

差一个座位，从第 1 档掉到**最后一档**（跳过 `unknown` 和 `high`）。今天因为 `autumnOnly` 恒为 `false` 不可达；一旦数据补上学季字段（这正是缺口①的修复方向），这条断崖会立刻对用户生效。没有任何测试断言 10/11 这个边界（见第 3 节）。

### 1.6 损坏/负容量会被提升为最高优先级，并给出无意义文案

`left<=0` 分支对任何非正 `left` 都成立（`lib/priority.ts:70-73`），且 `Capacity` 类型不变量为空（`:16`）：

```bash
node --experimental-strip-types /tmp/probe1.ts
# --- P4 ---
# known(10,12): {"level":"critical","reason":"该班次已满（12/10）"}
# mapping capacity:-5 -> {"kind":"unknown"}
# direct KNOWN capacity(-5,0) -> {"level":"critical","reason":"该班次已满（0/-5）"}
# rank order: 1.CORRUPT[critical] 该班次已满（0/-5） | 2.REALFULL[critical] 该班次已满（265/265）
```

行数据这一路被 `lib/priority-mapping.ts:30`（`limit <= 0 → unknown`）挡住了，所以**不构成当前可达缺陷**；但 `placesLeft` / `urgencyOf` / `rankPlan` 都是 `export` 的公共函数面（文件头 `:4-6` 明确说这是"可抽取的核心"），契约只存在于注释里。损坏数据不但不降级为 `unknown`，反而插到真·满员课前面，文案 `已满（0/-5）` 会原样进 UI。建议在 `placesLeft` 层就把 `limit<0 || enrolled<0` 归为 `unknown`。

### 1.7 措辞精度

`known(10,12)` → `该班次已满（12/10）`。12/10 不是"已满"而是"超额"；`lib/priority.ts:34` 的注释自己写的是 `full, or over-subscribed`，文案没跟上。

### 1.8 已被测试钉住、我反证失败的其余路径（记录在案）

- **并列确定性**：`/tmp/probe1.ts` P3，把 3 门完全并列的课洗牌 200 次 → 只有一种输出 `A,B,C`；测试 `tests/priority.test.ts:100-106` 覆盖。重复 code（比较器返回 0）依赖 V8 稳定排序，P9 输出 `1.DUP 2.DUP`，不崩不乱；code 唯一即无问题。
- **排列不变性**（不丢不重）：`tests/priority.test.ts:125-136`。
- **容量缺失 vs 已知安全的相对位置**：`tests/priority.test.ts:64-72` 断言 `MYSTERY` 先于 `SAFE`，实测通过。
- **`credits` 缺失**：`/tmp/probe1.ts` P5，`credit` 缺失 → 回填 `0`。**但 `credit` 从头到尾没被任何逻辑使用**（`RankedCourse` 的键只有 `rank,code,name,urgency,placesLeft`），所以这既不是 bug 也不是测试漏洞，而是死字段（见 4.3）。
- **`selected > capacity`**：见 1.7（判为 critical，方向正确、措辞不准）。
- **比较器里两行死代码**：`lib/priority.ts:113-114` 看起来在"同一个档位内按有无名额混排"，但 `urgencyOf` 保证 `level==='unknown' ⟺ placesLeft===null`，所以同一档位内 null-ness 必然一致：

```bash
node --experimental-strip-types /tmp/probe4.ts
# groups checked: 48005, groups mixing null and non-null placesLeft inside one urgency level: 0
```

这两行永远不会改变结果（意图其实由 `WEIGHT` 实现了）。不是缺陷，但说明写它时的排序模型与最终代码不同，留着会误导后来者。

### 1.9 `required` 的语义漂移（文档 vs 调用方）

`lib/priority.ts:25` 说 `required` = "required for the degree (**public required course**)"；页面传的却是 `degreeCodes.has(course.code)`（`app/page.tsx:697`），而 `degreeCodes` 是用户在卡片上可开关的"学位课标记"（`app/page.tsx:1240-1252` 的 toggle、`toggleDegree`）。用户关掉开关，一门公共必修课就不再享有"必修"权重。行为上可辩护（应用自称标记只是规划判断），但库里的措辞和调用方的语义不是一回事，属可维护性风险。

---

## 2. 越界与耦合

### 2.1 切片边界：干净（正面）

`git diff upstream/main 7e17a21` 里 `app/page.tsx` 的 58 行**全部**是一个 `useMemo`（`:685-703`）加一个 JSX 块（`:1280-1307`）：

- 没有新增 `useState`、没有改 `PLAN_STORAGE_KEY`（仍是 `ucas-graduate-course-planner-v3`，`app/page.tsx:123`）、没有改 localStorage 的写入（`:630-644`）或导入/导出（`:900+`）。
- 没有新 CSS 类，复用了既有的 `important-note` 与 `Info` 图标。
- `plan`、`degreeCodes`、`conflictCodes` 只被读。既没有回写计划，也没有把排序结果持久化。

唯一的越界是下面两条**配置类**改动（`.gitignore`、`tsconfig.json`），它们不在"纯函数层 + 一个面板"的自我声明里。

### 2.2 `tsconfig.json:15` 的 `allowImportingTsExtensions`：为了测试文件放宽了全仓库

这是**只被测试需要**的开关。把它删掉后：

```bash
# 在 /tmp/a4slice 里临时注释掉该行（只改 /tmp 的副本），再跑：
npx tsc --noEmit
# tests/priority.test.ts(11,66): error TS5097: An import path can only end with a '.ts' extension when 'allowImportingTsExtensions' is enabled.
# tests/priority.test.ts(12,73): error TS5097: error TS5097 …
# exit: 2
```

注意报错**只在测试文件**：`lib/priority-mapping.ts:12` 的 `import type ... from './priority.ts'` 因为 type-only 被擦除而不报错 —— 也就是说 `lib/` 侧根本不需要这个开关，是 `tests/` 的 `import ... from '../lib/priority.ts'`（`tests/priority.test.ts:11-12`）需要它，而 `tsconfig.json` 的 `include` 是 `"**/*.ts"`，把 `tests/` 一并扫进来了。

**它会不会影响仓库原有代码的构建/类型检查？我实际跑了，答案是不会：**

| 检查 | slice（含该 flag） | upstream/main（无该 flag） |
|---|---|---|
| `npx tsc --noEmit` | exit 0 | exit 0 |
| `npm run build`（vinext） | ✓ exit 0，112 modules | ✓ exit 0，110 modules |
| `npm run lint`（oxlint） | 0 error / 0 warning，8 files | （改动前同样通过） |

代价是两处耦合：(a) 全仓库从此允许 `import './x.ts'`，而这个写法只在"`noEmit` 或 `emitDeclarationOnly`"下合法 —— `tsconfig.json` 现在有 `noEmit: true`，所以合法，但一旦有人为了发 `.d.ts`/产物而关掉 `noEmit`，这个 flag 会变成硬错误，属于埋给未来的地雷；(b) 为一个测试文件改全局编译器选项，影响面大于需要。更小的等价做法：`tests/` 用独立 `tsconfig.test.json`，或把 `tests/**` 从主 `include` 里排除。

### 2.3 `.gitignore` 新增 `*.tsbuildinfo`（`.gitignore:39-40`）

与切片目标无关（属于仓库卫生），但**确实解决一个真实痛点**：`upstream/main` 的树里 `tsconfig.tsbuildinfo` 是未跟踪且未被忽略的（`git ls-files | grep tsbuildinfo` 为空；`.gitignore` 原本只忽略 `/.next/ /dist/ /.wrangler/` 等），跑一次 `tsc` 就会把工作树弄脏。建议收窄为锚定的 `/tsconfig.tsbuildinfo`，避免把任意子目录的 buildinfo 一起忽略。风险：无（没有已跟踪的 buildinfo 被掩蔽）。

### 2.4 页面里对被隐藏类型字段的读取（`app/page.tsx:695-696`）

`Course` 类型只有 `capacity?: number`（`app/page.tsx:80`），**没有 `selected`**；切片用 `(course as { selected?: number }).selected` 绕过类型系统。运行上是安全的（`normalizeCourse` 用 `...course` 扩散，`:236-260`；localStorage 往返同样保留该字段），但既然切片要求应用首次读取这两个字段，正确做法是给 `Course` 补 `capacity?/selected?`，而不是就地断言 —— 否则类型检查对未来 `normalizeCourse` 的改动没有任何保护能力。

---

## 3. 可测试性与遗漏

### 3.1 已有测试：质量高于平均

`tests/priority.test.ts` 20 条全绿（`node --experimental-strip-types --test tests/priority.test.ts` → `# pass 20 / # fail 0`）。选材是对的：`placesLeft` 不猜、满员/超额、缺数据判 unknown 而非 safe、unknown 排在 known-safe 之前、档次大小关系、same-level 的 required/autumnOnly 次序、并列回退到 code、冲突课排除、空方案、排列不变性、rank 连续。哨兵规则（`tests/priority.test.ts:156-160`）与"字符串容量不认"（`:162-167`）这两条尤其到位。

### 3.2 没覆盖的行为，以及是否与风险成比例

| 遗漏 | 风险 | 我的判断 |
|---|---|---|
| 面板层（`app/page.tsx:685-703` 的内联映射 + `:1280-1307` 渲染）零测试 | 中 | **可接受**：仓库没有任何前端测试基础设施（`package.json` 的 scripts 只有 `dev/build/start/lint/format`，无 `test`；`.github/` 下只有 issue 模板、**没有 CI workflow**），为一条薄壳面板引入 React 测试栈不成比例。但要记在账上：`autumnOnly` 缺失、`required=degreeCodes`、`selected` 强转这三件事**只发生在页面里**，纯函数测试永远照不到 |
| 映射里的负/损坏 capacity、超额容量的相对位置 | 中（公共函数面） | **该加没加**：5 行断言，覆盖 `lib/priority.ts:70-73` |
| `FEW_PLACES` 的 10/11 边界 | 中低（当前不可达，修缺口①后立刻可达） | **该加没加** |
| `credit` 回填 0 | 低（字段未被使用） | 可不加；但更该做的是删字段（4.3） |
| 换行/空串 code 进 UI 的 `key={item.code}` | 低（计划课程来自目录，必有 code） | 可不加 |

### 3.3 我建议"应该加但没加"的测试（附断言，已实测当前会红）

把下面两条放进 `tests/priority.test.ts` 即可，其中第一条**当前会 FAIL**（我跑过，见输出）：

```ts
void test('损坏的容量不得插到真·满员课前面', () => {
  const r = rankPlan([
    course({ code: 'CORRUPT', capacity: { kind: 'known', limit: -5, enrolled: 0 } }),
    course({ code: 'REALFULL', capacity: { kind: 'known', limit: 265, enrolled: 265 } }),
  ]);
  assert.equal(r.order[0].code, 'REALFULL');            // 今天拿到的是 CORRUPT
  assert.equal(r.unknownCodes.includes('CORRUPT'), true); // 或：至少不能被判 critical
});

void test('FEW_PLACES 边界：10 个名额是 critical，11 个是 normal', () => {
  assert.equal(urgencyOf(course({ code: 'A', capacity: known(20, 10), required: true, autumnOnly: true })).level, 'critical');
  assert.equal(urgencyOf(course({ code: 'A', capacity: known(20, 9),  required: true, autumnOnly: true })).level, 'normal');
});
```

```bash
node --experimental-strip-types --test /tmp/probe2.test.ts
# ok 1 - REVIEW T1: FEW_PLACES boundary — 10 left is critical, 11 left is normal (cliff)
# not ok 2 - REVIEW T2: a corrupt negative limit must not outrank a genuinely full section
#   error: 'corrupt row was ranked #1 (优先抢)'
#   #    observed order: 1.CORRUPT[critical] "该班次已满（0/-5）" | 2.REALFULL[critical] "该班次已满（265/265）"
# # tests 4 / # pass 3 / # fail 1
```

### 3.4 测试不会被自动跑

`.github/` 下没有 workflow（只有 `ISSUE_TEMPLATE/`），`package.json` 也没有 `test` 脚本 —— 唯一的运行方式是 `tests/priority.test.ts:4` 注释里那句手敲命令。也就是说这 178 行测试**只在人工记得跑的时候存在**。这不算切片的错（仓库本来就没有 CI），但既然切片是"用测试证明自己"的形态，建议顺手补 `"test": "node --experimental-strip-types --test tests/"`，否则"20/20 通过"是一次性证据。

---

## 4. 文档与可维护性

### 4.1 命名/文案与产品一致（正面，少数例外）

- "名额"是既有用语（既有文案 `app/page.tsx:1417`、`:1424`），切片没有生造词。
- 面板复用 `important-note` 容器、`Info` 图标，位置紧贴 `selected-list`（`:1280`），与"学位课请最终确认"那块并列 —— 视觉与既有模式一致。
- 例外：`优先抢 / 无法判断 / 尽快 / 从容` 是四个新词，且其中 `优先抢` 不可达（1.3）。建议收敛到真正可达的档位，或先修可达性再上文案。
- 例外：`app/page.tsx:1299-1301` 把内部编号写进面向用户的文案（"这是 A1 记录的缺口①"），而 `caveats` 里其它条目都不带编号。早期项目里可接受，但不应长期留在产品文案里。

### 4.2 `lib/` 下新增两个模块：合适，但可以更 KISS

- `lib/priority.ts` 是纯排序核心，放 `lib/`（目前只有 `utils.ts`）合理，且文件头注释把规则溯源到 A1/A2/A3，质量好。
- `lib/priority-mapping.ts` 只有 45 行、一个调用点（`app/page.tsx:690`）。它单独存在的唯一硬理由是"把 `capacity===0` 是哨兵这条数据规则用测试钉住"，这个理由我认为成立。
- 更简单的等价写法：`rankPlanRows(rows)` 直接吃 `capacity/selected` 并在内部处理哨兵，省掉 `Capacity` 联合类型与 `plan → RawCourseRow → PlanCourse → RankedCourse` 四层转换（UI 实际只用到 `name/code/urgency.label/urgency.reason/placesLeft`）。反论点也成立（这是 ADR-001 选定的纯函数边界），所以我把它列为"可讨论"，不是"错"。

### 4.3 `credit` 是死字段

`PlanCourse.credit` 存在（`lib/priority.ts:22`）、`planCoursesFromRows` 专门回填（`lib/priority-mapping.ts:39`）、页面专门传（`app/page.tsx:694`），但 `rankPlan`/`urgencyOf`/`RankedCourse` 全程不用它：

```bash
node --experimental-strip-types /tmp/probe1.ts
# --- P5 ---
# RankedCourse keys: rank,code,name,urgency,placesLeft
```

要么删掉（KISS），要么真的用它（"学位课学分够不够"是另一个真实痛点，比 `autumnOnly` 更可达）。

### 4.4 注释与实现的一处叙述矛盾

`lib/priority.ts:12-13` 写"没有容量数据的课… placed where **the evidence supports** placing it"，读起来像"不武断"；实测它落在第 2 档、排在"只剩 5 个名额"的课之前（1.4）。注释要么改成"刻意提前"，要么改 `WEIGHT`。文档里唯一让我觉得"说的话比做的事更谦虚"的地方。

---

## 5. verdict

**能安全合入上游：可以（不应回滚），但不应以"已交付价值"结项。**

三个理由：

1. **无回归风险（实测）**：`npx tsc --noEmit`、`npm run build`、`npm run lint` 在 slice 与 `upstream/main` 两侧均 exit 0；`app/page.tsx` 的 58 行只读不写，未触碰状态、持久化、既有 UI 结构或样式。
2. **可抽取核心的测试质量高于平均**：20/20 通过，覆盖哨兵、缺字段、冲突排除、排列不变性、并列确定性；实现与文档规则经 5000 次差分零偏差。
3. **但它的结论在自家数据上不成立**：`selected` 在 94.8% 的行上为 0，`placesLeft` 退化成 `capacity`，`critical` 不可达，面板第 1 条恰恰是"无法判断"。

**我认为最严重的一个问题**：`selected` 被当作权威的实时报名数使用（`lib/priority-mapping.ts:26-32` + `app/page.tsx:695-696`），于是把"班级容量"包装成"剩余 N 个名额 / 抢课风险"呈现给用户（`lib/priority.ts:80`、`app/page.tsx:1301`），而且**没有任何 caveat** —— 相比之下同一份数据里 `capacity===0` 被郑重地降级为 `unknown` 并写进 `caveats`（`lib/priority.ts:128-133`）。同一份数据、相邻两个字段，一个诚实、一个被当权威，输出的是面向用户的错误陈述。次严重的是 1.4：`无法判断` 的条目占据"抢课顺序建议"的第 1 位，与面板标题直接冲突。

### 我尝试过但没有推翻的路径

排序器实现与文档规则一致（5000 次差分）；并列确定（200 次洗牌）；输入不被修改；排列不丢不重；冲突课排除后仍以 caveat 形式交代；容量缺失不会被当作安全；`capacity===0` 哨兵处理正确且与数据普查吻合（99/2077，实测一致）；数字字符串不被误认成数字；`npx tsc --noEmit` / `npm run build` / `npm run lint` 无回归；`.gitignore` 与 `tsconfig.json` 的改动没有破坏既有构建。**这个切片的下限（不破坏、不撒谎地处理缺失数据）是达标的；它的上限（把 A1 痛点①②变成可执行建议）没有达标，原因主要在数据而不是在这 425 行代码**——但代码选择不把这件事说出来，才是评审要拦的那一点。

---

### 附：本文用到的命令一览

```bash
git log --oneline upstream/main..7e17a21
git diff --stat upstream/main 7e17a21
git archive 7e17a21 | tar -x -C /tmp/a4slice && ln -s "<repo>/node_modules" /tmp/a4slice/node_modules
git archive 68e7080  | tar -x -C /tmp/a4base  && ln -s "<repo>/node_modules" /tmp/a4base/node_modules
node --experimental-strip-types --test tests/priority.test.ts      # 20 pass / 0 fail
npx tsc --noEmit                                                   # exit 0（slice 与 base）
npm run build                                                      # exit 0（112 / 110 modules）
npm run lint                                                       # 0 error / 0 warning
node --experimental-strip-types /tmp/probe1.ts                     # 边界、措辞、损坏容量、credit、caveat
node --experimental-strip-types --test /tmp/probe2.test.ts         # 建议的测试：3 pass / 1 fail
node --experimental-strip-types /tmp/probe3.ts                     # selected 普查 + 真实方案的面板输出
node --experimental-strip-types /tmp/probe4.ts                     # 48,005 组，0 组混合 null-ness
node --experimental-strip-types /tmp/probe5.ts                     # 5,000 次差分：实现 vs 文档规则
```
