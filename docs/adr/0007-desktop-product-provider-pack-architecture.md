# ADR 0007: 桌面客户端产品架构 — Provider Pack 与可插拔调度

## Status

Proposed（2026-09-18，桌面产品架构讨论定稿；实施尚未开始）

延续 [ADR 0005](0005-isolate-providers-by-runtime.md)（provider 运行时隔离）与
[ADR 0006](0006-extract-core-as-embeddable-dual-layer-sdk.md)（核心抽为可嵌入
双层 SDK）。

## 背景：要解决什么问题

计划基于 MinerU、docling 等解析引擎开发**面向终端用户的桌面客户端产品**
（Electron），在其上构建高级文档服务（预览、块级交互、表格工作流等）。由此
引出一组相互牵制的问题：

1. **商业约束**：前期投入必须足够小。目标是先免费赚口碑、后收费；不能在
   有收入之前先投入大笔 GPU/服务器硬件成本。
2. **用户硬件异构**：一部分用户本地硬件足够跑高质量解析，一部分不够。
   两种用户都要能服务，且弱硬件用户不能拖垮产品体验。
3. **MinerU 4.0 破坏了现有集成**：当前 `MinerUAdapter` 以 subprocess 方式调
   `mineru` CLI（3.4.0，`-b pipeline`），4.0 更换了命令入口、移除了
   backend 概念（改为 flash/basic/standard/advanced 质量档位）、输出契约
   变更为带 `schema` 标识（2.0）的新格式，旧 JSON 不保证可读。CLI 参数和
   输出目录结构从来不是稳定 API，每次大版本都会被打断。
4. **MinerU 表格输出没有 cell 级 bbox**（已核实本仓库存储的 3.4.0 产物与
   官方输出文档）：表格几何只到整表级，单元格结构是纯 HTML。块级定位类
   产品功能需要 cell 坐标时要走 docling 路径（其 normalizer 已在消费
   cell bbox）或自行补一步 cell 检测。
5. **多 provider 依赖冲突在桌面怎么办**：服务端用"每 provider 一个容器 +
   独立 queue"解决（ADR 0005）；桌面端没有 Docker，需要等价的隔离手段。
6. **多部署形态的复用**：明确的产品路线是"桌面 + 线上服务 + 云端解析"
   三种形态并存。希望三者的代码与产物最大限度统一，避免每加一种部署就
   多一套打包和调用方式。

## 决策

### 总览

整个系统收敛为三种零件：

| 零件 | 内容 | 说明 |
| --- | --- | --- |
| **主服务** | `DocumentService` + `build_api_router`（ADR 0006） | 业务逻辑、数据库、存储、provider 路由。所有部署同一份代码 |
| **Dispatcher 端口** | `TaskDispatcher` 的两个后端：`LocalDispatcher` / `CeleryDispatcher` | 派活与盯梢的唯一分叉点，按部署配置选择 |
| **Provider Pack** | 解析引擎 + 全部依赖 + HTTP 壳，一体的自包含交付物 | 桌面是子进程目录，线上是容器内容物，云端是服务 URL |

```
renderer / 客户端
      │  统一 HTTP API（本地 127.0.0.1 或线上域名，只差 base URL）
┌─────▼──────────────────────────┐
│ 主服务                          │
│  ├ DB + 存储                    │
│  └ Dispatcher（端口，可插拔）    │
│     ├ LocalDispatcher           │ ← 桌面 / 线上早期
│     │    └─► Pack 的 HTTP       │
│     └ CeleryDispatcher          │ ← 线上扩容后（期权，非现状依赖）
│          └ broker → worker      │
│               └─► Pack 的 HTTP  │ ← 调用方式与左侧完全相同
└────────────────────────────────┘
```

### D1：Electron 三进程模型

Electron main（壳：进程守护、更新、托盘）→ 本地 sidecar（主服务，嵌入
docalchemy-core，uvicorn 跑在 `127.0.0.1` 随机端口 + Bearer token）→
解析 worker（Provider Pack 子进程）。

- sidecar 与解析分离的原因：torch/OpenCV 段错误不应带走 API；模型常驻内存
  与 UI 进程隔离；解析进程可独立重启。
- renderer 永远只说 HTTP API 一种协议。**解析在哪执行是服务端的实现细节**
  ——这是"桌面版与云端版是同一个产品两种部署"的基础：换 base URL 即切换。

**拒绝的备选**：
- Docker 桌面端部署——要求用户安装 Docker Desktop（商业授权、WSL2、常驻
  虚拟机 2–4 GB 内存），对消费级桌面产品不可行。Docker 保留在服务端。
- 解析进程内嵌进 renderer/main——无隔离，重负载崩溃即整个应用崩溃。

### D2：Provider Pack — provider 与 HTTP 壳绑定为一体

每个 provider 打包为**自包含目录**（PyInstaller onedir：自带解释器与全部
依赖），附带 manifest：

```json
{
  "provider_id": "mineru",
  "version": "4.0.1",
  "capabilities": {"ocr": true, "table": true},
  "supported_mime_types": ["application/pdf"],
  "entry": "bin/serve",
  "endpoint": null,
  "min_hardware": {"ram_gb": 4}
}
```

- 主服务扫描 manifest 注册进 `ProviderRegistry`（对齐 ADR 0006 的
  `ProviderSpec`，增加 `endpoint` 字段后**本地 Pack 与远程解析服务是同一
  种东西**）。
- 构建期复用现有 `docker/requirements/*.txt` lockfile（`uv pip compile
  --extra <provider>`）——Pack 是"每 provider 一个容器镜像"的桌面等价物。
- **用户机器上永远不做依赖解析**：要么是构建期打包好的产物，要么是一个
  URL。依赖冲突在物理上到不了用户面前。
- 生命周期：按需拉起（首用加载模型）、空闲回收、崩溃自动重启；每 provider
  并发 1（与服务端 `-c 1` 一致，单机 GPU/CPU 下并发无收益）。

**为什么 provider 要"包一层 HTTP"**——这是讨论中反复澄清的核心点：

1. 依赖隔离要求 provider 跑在独立进程，独立进程必须有通信协议。HTTP 壳
   就是那个协议的选型，**壳本身没有业务逻辑**（run/progress/cancel/health
   四个端点包住 adapter）。
2. 选 HTTP 而非 stdio 自定义协议：进度流、取消、健康检查都是现成语义，
   不必手写小型 RPC 框架；且桌面子进程、线上容器、云端服务**用同一种
   语言**，调用方一份代码通吃。
3. 例外：依赖与主服务兼容的轻 provider（如 docling）**不包壳**，直接
  进程内调用——壳的唯一意义是跨进程通信，不跨进程就不需要。

**壳的内部执行模型与性能边界**：

- 壳与执行者**同进程**：HTTP handler → `adapter.execute()` → MinerU SDK →
  normalizer 全部是普通函数调用。全链路只有**一条**进程边界，就是那层
  HTTP；门里所有东西同居一室。引擎内部若自己 spawn 子进程，是 Pack 的
  私事，对外契约不变。
- HTTP 不在热路径上：契约是**粗粒度**的（一份文档一个 job），全部流量
  = 一次 `POST /run` + 每秒一次进度轮询 + 取一次结果。localhost 往返
  ~1 ms，摊在分钟级解析任务上 < 0.01%。吞吐瓶颈永远是模型推理。
- **只传存储键，不传字节**：PDF 本体与产物（markdown/json/图片）走共享
  存储（桌面同一个 `STORAGE_ROOT_PATH`，线上同一个 volume），HTTP body
  里过的是钥匙不是货。把几百 MB 文件塞进 body 是被禁止的反模式。
- 硬红线与固定写法：这个 HTTP server 是控制面门面（唯一客户是
  dispatcher，并发 1），性能要求趋近于零，**唯一必须守住的是
  health/cancel 不被解析饿死**。因此解析一律跑在工作线程/子进程
  （`run_in_executor`；torch/onnx 推理期间大量释放 GIL，事件循环可保持
  响应；纯 Python 重计算再升级为子进程）。此写法进 Pack 规范。
- 内部升级期权：必要时 Pack 可拆为"门面进程 + 执行子进程"两进程，外部
  契约完全不变（边界以里是 Pack 的私事），属于纯内部优化，随时可加。

**拒绝的备选**：
- 运行时在用户机器上创建 venv——首次运行要联网解析依赖，不可复现，恰是
  服务端用 lockfile 镜像规避掉的问题。运行时 venv 仅留作将来"企业自定义
  provider 插件"的进阶机制。
- stdio JSONL 协议——功能可达但要自研协议；且与云端 provider（天然 HTTP）
  形成两种方言。

### D3：线上部署与 Celery 的关系

**队列拓扑不变**（`analysis.<provider>` 独立 queue、`-c 1`），变的只是
任务到达后 worker 做什么：

- 现在：worker 容器装 provider 依赖，adapter 进程内执行。
- 之后：容器内两个进程——celery 消费者（通用壳，不装 provider 依赖）+
  Provider Pack。`run_analysis` 变为**所有 provider 共用的通用任务**：
  POST 给 Pack → 轮询进度 → 写回 `analysis_run` → 搬产物。解析能力从
  celery worker 进程**搬进** Pack 进程（搬家的动机是桌面端没有 celery，
  解析逻辑留在 worker 里就无法复用）。

**分阶段取舍**：

| 阶段 | Dispatcher | Redis/Celery | 说明 |
| --- | --- | --- | --- |
| 桌面 | Local | 无 | 任务表 + 子进程守护 |
| 线上早期（单机） | **Local（同一个实现）** | **无** | 与桌面共用代码，系统总复杂度下降 |
| 线上扩容（多机/GPU 池） | 切 Celery | 有 | 配置切换，业务代码不动 |

砍掉 Celery 的准确理解：**Celery 买的不是"怎么调用 provider"而是"长任务的
生命周期管理"（排队、重试、崩溃恢复、持久化）**。HTTP 替换传输方式，替换
不了编排；单机并发有界时这些职责由 LocalDispatcher（任务表 + 信号量 +
超时监控，几百行）承担，且 `analysis_run` 状态行 + boot-janitor 已覆盖大
半。Celery 降级为**扩容期权**而非现状依赖——前提是业务代码永不直接
import celery（core 已做到，保持住）。

### D4：桌面端去服务器化

- SQLite（`sqlite+aiosqlite`）替代 Postgres——需先验证 core test suite
  对 SQLite 全绿（run 状态机的 CAS 更新是标准 SQL，风险点在是否有
  PG 专属类型/方言）。
- 无 Redis、无 Docker、无 broker。
- `MINERU_HOME`、`STORAGE_ROOT_PATH`、SQLite 全部指向应用数据目录，
  与安装目录分离，更新不碰用户数据。

### D5：能力分级 + 硬件探测 + 按需云端（商业模型与架构的对齐）

| 级别 | 引擎 | 跑在哪 | 边际成本 |
| --- | --- | --- | --- |
| L0 | docling（数字原生 PDF，含 cell bbox） | 用户本地 | 零 |
| L1 | MinerU flash/basic（onnx 路线，可不带 torch） | 用户本地 | 零 |
| L2 | MinerU standard/advanced（VLM） | 本地（硬件够）或云端 | 仅云端路径付费 |
| L3 | 大文档批处理 / 云端优先 | 云端 | 按量 |

- 桌面应用启动时探测硬件，自动落在用户机器能承受的最高一级。
- **GPU 账单与收入是同一条曲线**：本地能力免费送（边际成本为零），
  云端高质量解析按页/积分收费（成本为 serverless 按秒计费，定价含毛利）。
- 云端演进：Phase 1 用 MinerU 官方 API（零基础设施，**商用转售条款待核
  实**）→ Phase 2 量起来后换 serverless GPU（Modal/RunPod/国内按量，
  镜像即 worker 产物），官方 API 降为溢出通道。用户地域决定选型（国内
  客户文档传海外 GPU 平台有数据出境合规问题）。
- MinerU 4.0 的页码区间与库模式缓存/续跑协议支持**渐进解析**（先出前几
  页预览、后台全量），是桌面 UX 升级 4.0 的最大回报；注意 `mineru parse`
  默认只解析前 10 页，必须显式 `--pages all`。

### D6：MinerU 4.0 集成方式

- adapter 从"CLI subprocess + 临时目录捞文件"改为 **4.0 Python SDK 进程内
  调用**（Pack 内），CLI 的参数与输出目录结构从来不是稳定契约。
- normalizer 按 `schema` 字段分发 + 版本门禁，按 schema 2.0 契约重写；
  避免再次被大版本格式变更打中。
- 数字原生 PDF 的 cell 级定位走 docling；MinerU 路径需要 cell bbox 时，
  用整表 bbox + HTML 网格近似（不规则表格误差大）或对其 `img_path`
  表格裁剪图补一步 cell 检测。
- 升级验收基线：一个原生文档 + 一个带文字层 PDF，比对 pages/Markdown/
  JSON/assets（迁移指南给的最小验证集）。AMD/厂商加速卡场景官方留在
  `mineru<4`，部署目标含非 NVIDIA 硬件时先确认。

### D7：免费期（Phase 0）的配套边界

**要做的**（运营基础设施，无论将来走哪条路都必须有）：

- 遥测（opt-in、匿名）：页数分布、解析时长、失败率、provider 占比——
  "何时上云、按页怎么定价"的全部依据
- 自动更新（electron-updater）与崩溃/错误上报——解析类产品缺陷修复频繁
- 产物 schema 版本门禁（见 D6）——升级不破坏用户已存数据
- "免费"边界提前公示：本地能力永久免费，云端 VLM 档标注"付费功能 · 即将
  推出"——将来收费不算背叛用户

**不做的**（服务基础设施，等收入信号出现再建）：账号、计费、支付、云解析
网关、多文档云端队列、协作同步。

**触发条件（现在写下来）**：遥测显示本地失败/超时占比超阈值、高质量档
需求在反馈中持续占一定比例、付费用户主动要批量/队列——满足其一启动
Phase 1。

## 好处（为什么值得这么做）

1. **一套代码三种部署**：桌面/线上/云端的差异收敛为配置（数据库、
   dispatcher 后端、Pack 运行位置），没有一种形态需要 fork。
2. **一个 Pack 产物全平台搬运**：桌面目录 = 线上容器内容物 = 云端服务。
   provider 新增或升级只产出一个 artifact。
3. **一份调用代码**：所有 provider（本地的、远程的）都是"带 token 的
   HTTP endpoint"，dispatcher 不区分方言。
4. **前期投入结构性趋零**：免费期全部解析发生在用户机器上，云端零部署；
   GPU 成本与收入同步发生，不存在"先赔硬件钱等收入"。
5. **对上游变化免疫**：MinerU 4/5、docling 大版本的变更被 Pack 边界和
   schema 门禁挡在 normalizer 一层，产品功能层零改动。
6. ** Celery/Redis 成为期权而非依赖**：单机阶段少两个常驻进程和一套
   broker 排障面；扩容需求出现时配置切换回来。

## 实施路径（建议顺序）

1. **桌面 MVP（用现有架构）**：Electron 骨架 + sidecar（`DocumentKit.
   from_env()` + uvicorn）+ docling 进程内直调跑通全链路。不依赖 MinerU
   4.0 的任何东西，产品验证与引擎升级解耦。
2. **Pack 规范**：manifest 字段、HTTP 契约（run/progress/cancel/health）、
   打包脚本（复用 lockfile）。设计在 MVP 期间同步起草。
3. **LocalDispatcher**：任务表 + 进程守护 + 通用 HTTP 客户端——唯一需要
   新写的核心件。
4. **MinerU Pack**（4.0 SDK adapter + normalizer schema 2.0 重写）+
   线上容器切换为"通用 worker + Pack"双进程形态。
5. **打包链**：PyInstaller → electron-builder → 首启模型下载 UX。
6. **云端路径**：触发条件满足后再建（账号计费小服务 + 按页云解析）。

## 待核实事项（设计前必须回答）

- [ ] MinerU 官方 API 的商用转售条款与当前定价/额度
- [ ] MinerU 4.0 Python SDK 与 V1 HTTP API 的完整规范（并发/排队语义、
      进度回调、取消）——本 ADR 只依据迁移指南，SDK 细节未读原文
- [ ] 4.0 输出契约（schema 2.0）是否包含 cell 级几何（"new geometry
      data" 的确切范围）
- [ ] core test suite 对 SQLite 的兼容性（D4 的前提）
- [ ] serverless GPU / 国内按量 GPU 的当前价格，每页真实成本测算
- [ ] 用户地域分布与数据合规约束（决定 Phase 2 云端选型）
