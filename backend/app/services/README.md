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

## 注意事项
- 爬虫功能需添加请求延迟（time.sleep(2)）
- 爬虫仅用于学习目的，需遵守网站 robots.txt
- 音频处理需处理文件格式转换
- 所有服务函数需添加完善的错误处理
