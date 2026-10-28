# 创宇宙 · AI WEB网页开发挑战赛

创宇宙是一款 AI 驱动的可搭建个人 Web 工作台。用户可用模块、空间和自定义方块组织资料、任务与日程，通过 AI 伙伴查询内容、生成方案和持续修订，并在审核确认后执行。

本目录用于第九届传智杯 **AI WEB网页开发挑战赛（10037）** 的独立开发、配置、测试和材料整理。创建日期：2026-10-23。当前使用创宇宙Web独立仓库，并完整保留真实Git历史。

## 参赛信息

组别：**A组（211组）**。报名状态：**已报名**。

| 位次 | 成员 |
| --- | --- |
| 1 | 郭剑宇 |
| 2 | 单汝巨 |
| 3 | 栾健 |

成员顺序按本赛道报名位次保留。指导老师信息尚未提供。

## 入口

- [应用源码与运行说明](chuangyuzhou/README.md)
- [Web服务配置与部署示例](chuangyuzhou/web-deployment/README.md)、[Web转换记录](evidence/WEB-004.md)
- [本目录工作规则](AGENTS.md)
- [当前团队与仓库更新记录](evidence/WEB-003.md)、[模型配置记录](evidence/WEB-002.md)与[独立目录建立记录](evidence/WEB-001.md)
- [材料整理清单](materials/README.md)
- [最新18页技术PDF v3与配套源稿](materials/2026-10-28_创宇宙Web技术文档_v3/README.md)、[保留的v2](materials/2026-10-28_创宇宙Web技术文档_v2/README.md)、[保留的v1](materials/2026-10-23_创宇宙Web技术文档_v1/README.md)、[独立仓库记录](evidence/WEB-007.md)
- [Web真实AI验收与撤销修复](evidence/WEB-008.md)
- [技术PDF v2与公开同步](evidence/WEB-009.md)
- [运行指南及AI论证修正](evidence/WEB-010.md)
- [历史开发对话链](https://github.com/guojianyu0806/chuangyuzhou-web/tree/c0ac0564c5e93ea0ba9a7af001dc5e12b685754e/evidence/prompt-chains)
- 代码仓库：<https://github.com/guojianyu0806/chuangyuzhou-web>
- 赛道官方详情：<https://www.boxuegu.com/matchTrack/detail/?id=10037>

## 本机运行

在仓库根目录执行：

```powershell
cd "web-track/chuangyuzhou"
node tools/verify-source.mjs
node tools/start.mjs --check
node tools/start.mjs
```

需要 Node.js ≥22.13。基础应用无需 `npm install` 或前端构建。默认地址为 **http://127.0.0.1:4396/**；也可运行本目录的 `启动Web赛道创宇宙.cmd`。

源码为普通物理文件，运行数据保存在应用自己的 `yuzhou/.cu-runtime/`。本入口使用独立端口和登录 Cookie；初始化账号由使用者在新环境自行建立。当前目录不携带其他环境的账号、业务数据、模型配置或 Key。

## 当前阶段

已建立源码工作目录、运行隔离、文件校验和独立启动入口，补齐模型环境变量，完成团队及公开仓库信息。WEB-004增加local/web两种运行模式：本机使用保持兼容；Web模式通过固定HTTPS原点与同源反向代理运行，使用安全登录Cookie。浏览器启动检查和服务端同步相关提示已适配，原有业务功能保留。配置见[应用说明](chuangyuzhou/README.md#3-环境变量模板)及[Web服务指南](chuangyuzhou/web-deployment/README.md)。

现有工程测试、真实模型记录和演示材料保留各自日期及版本。WEB-007建立独立仓库；WEB-008完成本机Web真实AI及修复后撤销回放，4次请求共48,730 token；全量920项、917通过、0失败、3跳过。WEB-010统一当前运行指南并另存18页PDF v3，补AI选型与优化依据、两类创新及案例矩阵，业务代码未改。v1/v2及旧视频原件保留，不重剪旧视频。真实域名TLS及官网最终提交仍按实际办理情况记录。

核心AI证据、当前运行指南和PDF v3已经具备；旧视频按用户确认沿用。官网上传字段、准确文件/视频链接及最终提交回执仍按实际核对。公网演示属于可选加分项，如选择提供，再验证目标域名TLS、服务可用性和专用体验账号。本版不声称已完成独立环境复现。

## Git 与材料

当前使用新独立仓库根目录的.git，本目录没有嵌套仓库。原主线203个提交与25个早期快照提交保留SHA、作者和时间，当前main只维护Web版；旧目录可在codex/web-separation-baseline中查看。源版本文件记录为evidence/WEB-001/baseline-files.json，当前清单为chuangyuzhou/SOURCE-MANIFEST.json。

原仓库、旧源码、成品及用户另改文件保持原样。WEB-003/005曾将对应阶段推送至原仓库，WEB-006新增技术PDF；这些记录保留历史事实。WEB-007以后Web开发使用本独立仓库，不向原仓库回写。PDF v1保留编制时的固定链接，可在本新仓库相同提交中定位来源。
