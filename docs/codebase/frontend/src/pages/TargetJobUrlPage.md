# 概要：`frontend/src/pages/TargetJobUrlPage.tsx`

**对应源码**：[../../../../../frontend/src/pages/TargetJobUrlPage.tsx](../../../../../frontend/src/pages/TargetJobUrlPage.tsx)

## 路径与角色

粘贴岗位详情 URL → `jobScrapeApi.scrapeAndSave` → 展示爬取快照与保存结果。

## 对外接口

默认导出页面组件。

## 关键依赖

[jobScrapeApi](../services/api.md)；长超时配置在后端/axios。

## 数据流 / 副作用

慢请求；写入 `saved_jobs`。

## 与前端/其它模块的衔接

[jobs.md](../../../backend/app/api/jobs.md) `scrape-url`；可链到简历优化带 `targetJobUrl`。

## 注意点

用户等待体验（Loading）；失败错误文案。
