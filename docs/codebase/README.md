# 源码概要镜像（`docs/codebase`）

本目录结构与仓库源码**相对路径对应**：`backend/...` → `docs/codebase/backend/...`，`frontend/src/...` → `docs/codebase/frontend/src/...`，扩展名为 `.md`。

- **阅读顺序**：请先读 [../reading-roadmap.md](../reading-roadmap.md)。
- **系统总览**：[../ARCHITECTURE_SUMMARY.md](../ARCHITECTURE_SUMMARY.md)。
- **根脚本**：[`root/cli.md`](root/cli.md)、[`root/start-services.md`](root/start-services.md)。

每篇概要中的 **对应源码** 链接指向仓库中的真实文件。

## 演示（简历智能优化）

以下为「简历智能优化」流程的界面示意：上传简历 → 填写目标岗位链接 → LangGraph 节点执行与进度。截图仅作文档说明，界面以实际运行版本为准。**更完整的演示**（含各节点「看输出」侧栏与第四步结果页）见仓库根目录 [README.md](../../README.md)。

**第一步：上传或选择简历（PDF / Word）**

![简历优化：第一步上传简历](images/demo-resume-step1-upload.png)

**第二步：准备优化（目标岗位链接，可来自应用内搜索或粘贴招聘站链接）**

![简历优化：第二步目标岗位链接](images/demo-resume-step2-target-job.png)

**LangGraph 节点与进度（节点可展开查看结构化结果与「分析思路」）**

![简历优化：LangGraph 节点与进度](images/demo-resume-langgraph-nodes.png)
