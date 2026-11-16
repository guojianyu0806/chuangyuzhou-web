# 创宇宙 · Web 工作台

创宇宙把资料、任务和日程放进一张可以自己搭建的画布。以准备期末复习为例，可以把课程空间、章节进度和复习清单放到同一主题。常用的清单留在画布上，其余卡片可以拖进「课程复习」收纳盒。

第九届传智杯 AI WEB 网页开发挑战赛（10037）。云南大学「我不是软蛋」队，队号 42988，A 组（211 组）。成员按位次为郭剑宇、单汝巨、栾健。

## 从这里开始

- [作品介绍 PDF v4](web-track/materials/2026-11-16_创宇宙Web作品介绍文档_v4/创宇宙_Web赛道作品介绍文档_v4.pdf) 介绍如何搭建工作台、整理卡片，以及作品公开和优化的情况。
- [技术文档 PDF v7](web-track/materials/2026-11-16_创宇宙Web技术文档_v7/创宇宙_Web赛道技术文档_v7.pdf) 说明网页架构、数据保存、AI 审核和加载优化。第 12–13 页对应两条预指导意见。
- [验收导读](web-track/evidence/WEB-048/评审导读.md) 标出真实模型、模拟演示和性能测试各自的记录。完整证据见 v9 提交包内的 `04_AI开发过程与验收证据_v7.zip`。
- 演示使用 v8 版，播放地址以正式表单第 7 项为准。

## 在本机打开

安装 Node.js 22.13 或以上版本。在仓库根目录或源码 ZIP 解压后的 `chuangyuzhou-web` 目录执行：

```powershell
cd web-track/chuangyuzhou
node tools/verify-source.mjs
node tools/start.mjs --check
node tools/start.mjs
```

打开 `http://127.0.0.1:4396/`，按页面提示建立自己的工作台。基础功能无需安装 npm 依赖或配置模型。初始化口令的位置、环境变量和 HTTPS 代理配置见[应用运行指南](web-track/chuangyuzhou/README.md)。应用目录内的指南保留早期验收背景，正式提交版本以本页为准。当前评审方式为本地运行源码。

进入「按主题查看」后，可以勾选卡片、生成分类建议，改完再确认。主题名会显示在原卡片上。要腾出画布空间时，可手动把选中的卡片拖进收纳盒，也可以单独拖出来。

## 技术结构

浏览器端使用 HTML、CSS 和原生 JavaScript 模块实现画布与主题页。Node.js 负责登录、读写 SQLite 工作区和接入 DeepSeek。模型返回的建议在页面审核，用户确认后服务端才保存变更。运行依赖和可选文档解析依赖见[应用运行指南](web-track/chuangyuzhou/README.md)，环境变量见 [.env.example](web-track/chuangyuzhou/.env.example)。

## 测试记录

- [真实 AI 归类](web-track/evidence/WEB-021.md) 使用三张测试卡片调用 DeepSeek 一次。模型将「校园创作展筹备」和「布展前核对」分到一组，阅读卡分到另一组。之后在浏览器完成改分类、跳过、确认、刷新和撤销。视频的课程复习案例使用示例建议演示同一操作。
- [真实 AI 协同](web-track/evidence/WEB-008.md) 使用隔离工作区完成读书会的查询、修订、确认和保存。修复后的撤销用当次保存的状态离线验证。
- [首屏性能对照](web-track/evidence/WEB-026.md) 在模拟限速下交替测了 12 对样本。首开配对差值中位数提前 90.2 毫秒，最后一个 JS 文件加载完提前 98.3 毫秒。后续 Edge 验收另测了等待提示、超时重试和本机缓存恢复，记录见验收证据包。

正式提交包 v9 的应用源码固定在 [`a3d10a0`](https://github.com/guojianyu0806/chuangyuzhou-web/tree/a3d10a0b0d98ea390e62e28073efef1000b93dc0/web-track/chuangyuzhou)。该版本已有 951 项自动回归记录，其中 948 通过、3 跳过、0 失败。本次材料修订沿用这些记录，源码 ZIP 补入当前导读和文档。应用文件及 Git 源码历史保持原样。

## Git 历史

本仓库保留原主线 203 个提交的 SHA、作者、日期和父子关系，随后追加 Web 赛道开发记录。`codex/web-separation-baseline` 指向迁移基准 `c0ac056`，`codex/yuzhou-historical-snapshots` 保存 25 个有来源说明的早期快照。详见 [Web 仓库迁移记录](web-track/evidence/WEB-007.md)和[历史开发对话](https://github.com/guojianyu0806/chuangyuzhou-web/tree/c0ac0564c5e93ea0ba9a7af001dc5e12b685754e/evidence/prompt-chains)。
