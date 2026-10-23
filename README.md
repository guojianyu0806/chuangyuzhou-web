# 创宇宙 · Web工作台

让每个人搭建自己的工作台。使用模块、空间和自定义方块组织资料、任务与日程，由AI伙伴查询、生成和修订方案，在审核确认后执行。

本仓库专门维护第九届传智杯 **AI WEB网页开发挑战赛（10037）** 的创宇宙Web版。A组（211组），成员位次：**1 郭剑宇；2 单汝巨；3 栾健**；已报名。

## 使用入口

- [Web源码与完整运行指南](web-track/chuangyuzhou/README.md)
- [Web部署配置](web-track/chuangyuzhou/web-deployment/README.md)
- [15页技术PDF及可编辑源稿](web-track/materials/2026-10-23_创宇宙Web技术文档_v1/README.md)
- [Web材料清单](web-track/materials/README.md)
- [独立仓库与Git迁移记录](web-track/evidence/WEB-007.md)

安装Node.js ≥22.13，在仓库根目录运行：

```powershell
cd web-track/chuangyuzhou
node tools/verify-source.mjs
node tools/start.mjs --check
node tools/start.mjs
```

默认访问 `http://127.0.0.1:4396/`，基础应用不需要npm安装或前端构建。首次按应用指南初始化自己的账号。真实模型Key只在本实例运行环境配置，不放入Git。网站模式需同机HTTPS代理，当前没有完成公网部署。

## 源码、测试与材料

当前应用对应WEB-004，312个源码文件校验清单随目录保留；独立仓库整理不改应用文件和技术PDF原件。最新迁移回归见WEB-007；此前WEB-004为917项、914通过、0失败、3跳过。真实模型、浏览器与历史测试保留发生日期和环境，不混作本轮结果。

`web-track/`包含应用、技术PDF、Web阶段证据和维护工具。本仓库不携带作者账号、数据库、附件、初始化口令或Key，也不复制旧工作区未提交的材料。

## 完整Git记录

原主线203个提交以原SHA、作者、日期和父子关系保留，随后按真实时间追加Web独立整理提交。`codex/web-separation-baseline`固定在迁移前的`c0ac056`；`codex/yuzhou-historical-snapshots`保留25个早期版本快照提交，其补录性质和时间不改写。

完整历史中的旧目录可以从上述基准分支查看，当前`main`只维护Web版。历史开发证据可查看[三条Prompt链](https://github.com/guojianyu0806/chuangyuzhou-web/tree/c0ac0564c5e93ea0ba9a7af001dc5e12b685754e/evidence/prompt-chains)。应用版本内说明及PDF v1中的原仓库地址属于编制时的历史引用，原件保持不变；当前仓库地址以本页为准，同一提交在本仓库的Git历史中仍可定位。

后续Web开发使用本仓库和独立本地目录，原仓库不随本仓库同步更新。
