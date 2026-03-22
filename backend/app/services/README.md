# services/

## 功能说明
业务服务层，实现核心业务逻辑，包括简历解析、岗位爬取、音频处理等功能。

## 开发状态
- [ ] 待开发
- [x] 开发中
- [ ] 已完成

## 依赖关系
- pdfplumber（PDF 解析）
- python-docx（Word 解析）
- requests, BeautifulSoup4（网页爬取）
- OpenAI SDK（语音处理）

## 文件说明
| 文件 | 说明 |
|------|------|
| __init__.py | 模块初始化 |
| resume_parser.py | 简历文件解析（PDF/Word） |
| job_scraper.py | 岗位信息爬取 |
| audio_processor.py | 语音转文字、文字转语音 |

## 参考：通用网页正文提取（与 Boss 专用爬取并列阅读）
- 思路说明（Jina Reader 清正文、Scrapling 应对反爬、分层优先级）：[可能是目前提取任何网页的终极方案](https://mp.weixin.qq.com/s/ljMffydOigAl1muyLFhQhw)
- 开源 Skill 示例：[shirenchuang/web-content-fetcher](https://github.com/shirenchuang/web-content-fetcher)（`pip install scrapling html2text` 等，按需自建）
- 本项目的 `job_scraper.py` 以 Boss 直聘 WAPI / HTML 为主；兜底顺序为 **直连 → Jina Reader →（可选）Scrapling**：
  - **Jina**（`JOB_SCRAPE_JINA_READER_FALLBACK`，默认 `true`）：`https://r.jina.ai/{目标URL}`；可选 `JINA_API_KEY`。
  - **Scrapling**（`JOB_SCRAPE_SCRAPLING_FALLBACK`，默认 `false`）：需 `pip install "scrapling[fetchers]"`，用 `Fetcher.get` 拉 HTML 再走通用解析；机房 SSL 异常时可设 `JOB_SCRAPE_SCRAPLING_VERIFY_SSL=false`（仅当你清楚风险）。

## 注意事项
- 爬虫功能需添加请求延迟（time.sleep(2)）
- Boss 直聘对机房/数据中心 IP 常返回 WAPI `code=35` 或登录门页；可在环境变量 `BOSS_ZHIPIN_EXTRA_COOKIES` 中配置从本机浏览器复制的 Cookie（勿提交仓库），详见 `app/core/config.py`
- 爬虫仅用于学习目的，需遵守网站 robots.txt
- 音频处理需处理文件格式转换
- 所有服务函数需添加完善的错误处理
