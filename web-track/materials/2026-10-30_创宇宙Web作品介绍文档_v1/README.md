# 创宇宙Web作品介绍文档 v1

日期：2026-10-30。适用于本轮提供的“6.作品介绍文档”七项要求。表单该项最多1个文件、100MB以内，直接上传本目录的`创宇宙_Web赛道作品介绍文档_v1.pdf`即可。本目录其余文件用于编辑、生成及核对，无需一并上传到第6项。

## 内容定位

| 表单要求 | PDF页码 |
| --- | --- |
| 项目详情及使用方式 | 2 |
| 项目亮点 | 3 |
| AI技术落地使用与测试概述 | 4 |
| 项目关键技术 | 5 |
| 项目相关图片 | 6-7 |
| 发表及获奖情况 | 8 |
| 项目基础与本版优化 | 8 |

第6项采用用户本轮确认事实：除GitHub源码公开外，没有正式发表或获奖；不由此推导其他赛事报名或提交状态。第7项说明同一作品持续迭代及本Web版具体优化，没有将既有功能表述为本阶段全部新增。

## 文件与生成

- `作品介绍正文.md`：可编辑正文。
- `build_pdf.py`：独立ReportLab生成器，输出存在时拒绝覆盖。
- `images/`：4份真实界面图；PDF仅做矩形裁切，没有改写界面文字。
- `SHA256SUMS.txt`：本包文件校验清单（清单自身除外）。

生成需要Python、ReportLab、Pillow、pypdf，以及Windows等线字体和Consolas。示例：

```powershell
python build_pdf.py --output 新的草稿路径.pdf
```

最终输出为8页，含嵌入字体、可选取文字、架构及流程图。按页面渲染检查，再完成文本、文件体积及哈希核验，详见`web-track/evidence/WEB-017.md`。

## 图片来源

| 本目录文件 | 原始来源 | 用途 |
| --- | --- | --- |
| images/workbench-demo.jpg | 项目演示视频第20秒，WEB-014只读检查导出的原帧 | 自由画布局部概览 |
| images/space-overview.png | web-track/evidence/WEB-008/09-linked-tasks.png | 空间概览及任务入口 |
| images/ai-proposal.png | web-track/evidence/WEB-008/04-corrected-proposal.png | 补充修订后的审核状态 |
| images/calendar-task.png | web-track/evidence/WEB-008/10-calendar-projection.png | 确认后关联待办 |

模型请求、工程回归均注明2026-10-24的阶段和范围；本轮只编制文档，不重新调用模型，不将文档检查计为业务回归。

本说明另存为新版。已有技术PDF、旧介绍文件、视频和网盘目录保持原样；本轮未修改应用源码、凭据或Git历史。
