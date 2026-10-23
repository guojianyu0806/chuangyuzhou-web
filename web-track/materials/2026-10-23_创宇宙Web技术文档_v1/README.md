# 创宇宙 · Web赛道技术文档 v1

编制日期：2026-10-23。赛道：10037，AI WEB网页开发挑战赛。A组（211组）；成员顺序为郭剑宇、单汝巨、栾健。

- `创宇宙_Web赛道技术文档_v1.pdf`：15页A4技术文档，覆盖需求、架构、AI、核心实现、测试、运行部署与总结。
- `创宇宙_Web赛道技术文档_正文_v1.md`：可编辑正文；`<!-- PAGE -->`控制分页，`:::diagram`绘制架构与流程图，`:::image`引用公开合成截图。
- `build_pdf.py`：使用ReportLab生成PDF，需要ReportLab、Pillow和Windows等线字体。字体读取系统文件并子集嵌入PDF，不复制字体原件。
- `SHA256SUMS.txt`：本目录交付文件的SHA-256；不包含校验和文件自身。

应用对应提交：`2ac61cbbf7dcbcdf8e173d2ab0977667497fa4ca`；后续`cd2c6f8`只补充公开同步与待办记录。源码目录为`web-track/chuangyuzhou`，默认端口4396，应用版本为`2026-10-23-web-dev-004`。

文档采用WEB-004既有全量结果917项、914通过、0失败、3跳过，明确说明本轮未配置独立解析器、真实TLS、当前Web真实AI全链和设备覆盖的边界。历史DEV-027/028真实模型案例保留发生日期及版本归属。

从本目录运行`python build_pdf.py`可在输出不存在时生成PDF；默认拒绝覆盖。`--rebuild`只供同一未交付草稿的排版迭代使用。后续要求新版本时应复制或另建版本目录，保留本版。

验收记录为`../../evidence/WEB-006.md`和`../../evidence/WEB-006/pdf-check.json`；可从仓库根运行`python web-track/tools/verify-web-pdf.py`复查正文、PDF、引用证据及旧材料哈希。需要pypdf、pdfplumber。逐页PNG检查图保存在被忽略的Web临时目录，不进入正式材料。

本次仅新增本目录、Web文档核验工具和WEB-006记录。旧PDF、旧源稿、视频、源码ZIP、原应用及已有材料索引均保持原样。没有覆盖旧成品、部署网站或提交比赛。
