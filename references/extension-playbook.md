# 扩展操作手册

**改这个包**的时候读这份文件：新增能力、新增资源、新增模块各要走哪些步骤、改完跑什么验证。

**规则**（命名空间、版本、状态流转、匹配优先级、`extends` 语义、加载上限）在 [扩展协议](extension-protocol.md)；本文件只讲**操作顺序**，不重复那些规则。

---

## 0. 改完统一跑这个

```powershell
python -B -X utf8 "<pm-kit 根目录>/tests/test_evals_schema.py"
python -B -X utf8 "<pm-kit 根目录>/tests/test_record_contract.py"
python -B -X utf8 "<pm-kit 根目录>/tests/test_catalog_manager.py"
python -B -X utf8 "<pm-kit 根目录>/tests/test_html_prd_scripts.py"
python -B -X utf8 "<pm-kit 根目录>/tests/test_validate_records.py"
python -B -X utf8 "<pm-kit 根目录>/tests/test_single_file_review_pipeline.py"
python -B -X utf8 "<pm-kit 根目录>/tests/test_flowchart_diagram_scripts.py"
```

上述测试均应输出 `OK`。加 `-B` 是为了不把 `.pyc` 写回包里。需要 Python 包 `jsonschema`（4.18 以上）。有禁止自动删除的工作区约定时，保留测试临时目录，并用保留夹具的方式验证缺文件场景。

---

## 1. 新增一种能力

**适用**：想让运行中的 Agent 多一种可调度的流程能力（例如「竞品分析」「数据分析」）。**不需要写代码。**

`capabilities/registry.json` 是能力的唯一登记处，字段含义：

| 字段 | 说明 |
| --- | --- |
| `id` | 调度标识，kebab-case，稳定、不复用 |
| `kind` | **只是分类标签**，不驱动加载。所以新增一种类型不需要改任何 schema 或入口正文 |
| `resource_base` | 该能力提到的 `assets/`、`references/`、`design-specs/`、`scripts/` 相对哪个目录解析；包根能力写 `"."` |
| `instruction` | 要读取的说明文件，**相对包根**解析 |
| `when` | 适用条件，Agent 靠它选能力 |
| `accepts` / `produces` | 阶段交接约定 |

**步骤**

1. 写说明文件：放 `references/`；如果它是一整套流程，考虑做成模块（见第 3 节）。
2. 在 `capabilities/registry.json` 里追加一条，七个字段都要有。
3. **要让它被自动路由到**（而不只是能被点名调用），再补三处给人看的索引：
   - `workflows/recipes.md`：某类目标走这条路径
   - `references/task-modes.md`：它属于哪个任务模式的常用能力
   - `使用说明与扩展指南.md` §4.1 的能力摘要表
4. 验证：`tests/test_catalog_manager.py` 会校验 registry 是否符合 `catalog/_schemas/capability.schema.json`，并确认每个 `instruction` 和 `resource_base` 真实存在、`id` 不重复。

**注意**：`SKILL.md` 的正文不需要改——它只讲规则，不列能力。但步骤 3 那三处索引不补，Agent 就不会自动想到用它。

---

## 2. 新增一个资源包

**适用**：沉淀行业做法、组件规范、交付模板或脱敏案例。四类的定义见 [扩展协议](extension-protocol.md) §2。

**步骤**

1. 用脚手架建骨架，不要手写目录：
   ```powershell
   python -X utf8 "<pm-kit 根目录>/scripts/catalog_manager.py" scaffold scenario store-inspection --name "门店巡检"
   ```
   四类的容器目录与脚手架文件由脚本定义；场景包会生成 `overview / roles / workflow / states / risks / validation` 六个文件。
2. 填内容。每类建议补什么，见 `使用说明与扩展指南.md` §8.3。
3. 校验并重建索引：
   ```powershell
   python -X utf8 "<pm-kit 根目录>/scripts/catalog_manager.py" validate
   python -X utf8 "<pm-kit 根目录>/scripts/catalog_manager.py" rebuild-index
   ```
   `validate` 通过后才是合格资源；`rebuild-index` 让 `catalog/index.json` 反映最新状态。
4. 经一次真实复用验证后，把 `status` 从 `draft` 提到 `active`。

**三条硬规则**（校验脚本会拦，文档也写在 `使用说明` §8.4）：

- `draft` 允许必填项留空；`reviewed` / `active` 不允许任何必填项为空。
- `id` 必须与目录位置一致：`catalog/<命名空间>/<容器>/<slug>/` 对应 `<命名空间>:<slug>`。
- `triggers` 在任何状态下都不能为空——它是资源被匹配到的唯一入口。

**`files` 的解析基准**：相对该资源 `manifest.json` 所在目录。可以指向资源包之外（内置资源就指向 `references/`），但必须落在本包内且文件真实存在。

**想叠加多个维度时不要堆 `extends`**。`extends` 是一对一的精化（最多一个父、必须同类）。"行业 + 端 + 合规 + 团队"应当**拆到不同的资源位**分别加载——组合发生在任务运行时，规则见 [扩展协议](extension-protocol.md) §4.1 与 §7.1。

---

## 3. 新增一个专项模块

**适用**：带多份参考或专用脚本的完整流程，例如六步 PRD、多页面原型、HTML 反向 PRD、流程图导出。确认节奏由模块自行声明，不要求每个模块都有多轮确认。

**目录结构**

```text
modules/<能力 ID>/
├── procedure.md     必需：执行说明（Agent 读它来干活）
├── README.md        必需：给人看的说明
├── assets/          可选：交付模板、骨架文件
├── references/      可选：按需读取的细则
├── design-specs/    可选：该模块自己的规范库
├── scripts/         可选：可执行的检查或生成工具
└── evals/
    ├── evals.json   可选但强烈建议：评测用例
    └── files/       可选：评测用到的 fixture
```

**可选的层级按需要挑**，不要照抄某一个模块——现有三个模块的可选部分**各不相同**：

| 模块 | assets | references | design-specs | scripts | evals/files |
| --- | --- | --- | --- | --- | --- |
| `make-prd` | 有 | 有（28 个文件） | — | — | 有 |
| `prd-html` | 有 | 有 | **有** | — | — |
| `html-prd` | 有 | 有 | — | **有**（3 个） | 有 |
| `flowchart-diagram` | — | 有 | — | **有**（2 个） | —（示例在 EXAMPLES.md） |

**确认节奏由模块自己声明，允许不同**：`prd-html` 每批生成 1–2 页，`html-prd` 每次只处理一页——这是各自流程的选择（前者页多而薄，后者页重），不是冲突，也不要拿一个模块的节奏去改另一个。新增模块时把节奏写在自己的 `procedure.md` 里。

**步骤**

1. 建目录，写 `procedure.md` 和 `README.md`。
2. 在 `capabilities/registry.json` 里登记：`kind` 写 `"bundled-module"`，`resource_base` 写 `"modules/<能力 ID>"`，`instruction` 写 `"modules/<能力 ID>/procedure.md"`。
3. 在 `SKILL.md` 的「能力选择与交接」补一句它的适用条件——模块靠这句话被正确路由（这一点和普通能力不同：模块是重武器，入口要说明什么时候该用它）。
4. 写 `evals/evals.json`，格式见 `catalog/_schemas/evals.schema.json`；`files` 里的路径相对**该模块目录**。
5. 验证：
   - `tests/test_catalog_manager.py` 检查 `procedure.md` / `README.md` 存在，且 `instruction` 指向 `procedure.md`
   - `tests/test_evals_schema.py` 自动发现模块的 `evals/evals.json` 并检查评测格式（id 从 1 开始、每条至少 3 条断言、引用的 fixture 存在）

---

## 4. 三条纪律

1. **不要动 `catalog/local/`**——那是使用者自己的资源，技能升级不得覆盖（见 [扩展协议](extension-protocol.md) §1）。
2. **改了 schema 就要跑测试**。包里有几处"同一句话写两遍"的地方，靠测试钉住同步；最典型的范式是 `tests/test_catalog_manager.py` 的 `DocumentedLimitsMatchSchemaTest`——它解析 `SKILL.md` 里的加载上限数字，和 `workflow-plan.schema.json` 的 `maxItems` 逐个比对。
3. **新增的多副本要配测试**。同一规则出现在多处时，选一处做权威，其余写成引用；确实必须重复的（比如给人看的摘要），补一条像上面那样的测试。目前只有"加载上限"这一组被机器同步，其余仍是人工维护。

---

## 5. 相关文件

| 想知道 | 看哪里 |
| --- | --- |
| 能力的适用条件、字段格式 | `capabilities/registry.json` + `catalog/_schemas/capability.schema.json` |
| 资源的命名、版本、状态、匹配、继承规则 | `references/extension-protocol.md` |
| 资源包各类要补什么内容 | `使用说明与扩展指南.md` §8 |
| 跨轮记录格式 | `references/record-contract.md` |
| 评测用例格式 | `catalog/_schemas/evals.schema.json` |
| 各部分从哪来 | `references/source-map.md` |
