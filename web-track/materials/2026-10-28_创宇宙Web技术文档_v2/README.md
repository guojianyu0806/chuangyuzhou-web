# 创宇宙 · Web赛道技术文档 v2

编制日期：2026-10-28。赛道10037，AI WEB网页开发挑战赛。团队“我不是软蛋”，编号42988，云南大学，A组（211组）；成员位次为郭剑宇、单汝巨、栾健。

- `创宇宙_Web赛道技术文档_v2.pdf`：15页A4技术文档，包含需求、架构、AI技术选型与集成、核心实现、测试与部署、创新特点及证据索引。
- `创宇宙_Web赛道技术文档_正文_v2.md`：本版可编辑正文，保留显式分页与图示定义。
- `build_pdf.py`：本版ReportLab构建脚本；默认拒绝覆盖现有PDF，`--rebuild`仅用于同一未交付草稿的排版迭代。字体读取Windows等线字体并嵌入子集，不附带系统字体文件。
- `SHA256SUMS.txt`：本目录其余5个文件的SHA-256，不包含校验和文件自身。

固定应用源码为`c71c0411245943198ce1db9d6276e211b4a28c94`，应用版本`2026-10-24-web-dev-008`。源码清单的`e5925b3`表示开发基线，不当作修复后的最终源码。公开入口为[独立Web仓库](https://github.com/guojianyu0806/chuangyuzhou-web)，[固定源码](https://github.com/guojianyu0806/chuangyuzhou-web/tree/c71c0411245943198ce1db9d6276e211b4a28c94/web-track/chuangyuzhou)。

本版采用WEB-008既有最终测试：920项、917通过、0失败、3跳过；27项目标回归和32项离线证据核对分别报告，不重复累计。真实AI共4次请求、48,730 token，保留首次修订漏改日期及后续补充修正。查询、生成、确认、刷新与日历关联使用真实模型；撤销修复后使用保存的真实状态进行离线浏览器回放，未新增模型调用。

PDF生成不等同重新运行应用测试、干净环境复现、真机或公网TLS验收。v1目录全部6个文件字节保持，旧视频按用户确认沿用，不重剪、不覆盖；本次没有再次验收视频完整内容或发布新视频链接。

结构、引用、字体、敏感信息和v1保护检查见`../../evidence/WEB-009/pdf-check.json`，15页PNG视觉复核另见`../../evidence/WEB-009/visual-check.json`。核验命令（仓库根目录）：

```text
python web-track/tools/verify-web-pdf-v2.py
node web-track/chuangyuzhou/tools/verify-source.mjs
```

文档过程见[WEB-009](../../evidence/WEB-009.md)。v1仍在其原版本目录，本版没有覆盖旧PDF、旧源稿、旧校验和或其他旧材料。
