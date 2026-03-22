"""
Job Scraper Service - 岗位信息爬取服务

爬取 Boss直聘等招聘网站的岗位信息。

参考阅读（通用「链接 → 正文」提取思路：Jina / Scrapling / 保底 fetch 分层调度，
与本仓库内 Boss WAPI 专用逻辑不同，可作扩展设计参考）：
https://mp.weixin.qq.com/s/ljMffydOigAl1muyLFhQhw

⚠️ 注意：本模块仅用于学习目的，请遵守网站的 robots.txt 规则。
"""

import json
import re
import time
from html import unescape
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import parse_qs, urlparse

import requests
from bs4 import BeautifulSoup

from app.core.config import settings
from app.core.exceptions import ExternalServiceException
from app.models.schemas import JobRequirements
from app.utils.logger import get_logger

logger = get_logger(__name__)


class JobScraper:
    """
    岗位信息爬取器

    支持从 Boss直聘 等招聘网站爬取岗位详情。

    ⚠️ 仅用于学习目的，请遵守网站 robots.txt 规则。
    """

    # 请求头，尽量贴近真实浏览器（Boss 校验 Referer / Accept / Sec-Fetch 等）
    DEFAULT_HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
        ),
        "Accept": (
            "text/html,application/xhtml+xml,application/xml;q=0.9,"
            "image/avif,image/webp,image/apng,*/*;q=0.8"
        ),
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Cache-Control": "no-cache",
        "Sec-Ch-Ua": '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
        "Sec-Ch-Ua-Mobile": "?0",
        "Sec-Ch-Ua-Platform": '"Windows"',
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Upgrade-Insecure-Requests": "1",
    }

    # 命中则说明拿到的是登录门页/挑战页而非职位 HTML
    _BOSS_GATE_HTML_MARKERS = (
        "BOSS直聘注册登录",
        "boss直聘在线注册登录",
        "安全验证",
        "访问验证",
        "请完成验证后继续",
        "请稍候",
        "正在加载",
        "security-check",
        "boss-loading",
    )

    # 仅含此类文案的 <title> 视为拦截/加载页，不能当职位名
    _INTERSTITIAL_TITLE_SUBSTR = (
        "请稍候",
        "正在加载",
        "安全验证",
    )

    REQUEST_DELAY = 2

    BOSS_WAPI_DETAIL = "https://www.zhipin.com/wapi/zpgeek/job/detail.json"

    def __init__(self, headers: Optional[Dict[str, str]] = None):
        self.headers = headers or self.DEFAULT_HEADERS
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        self._apply_boss_extra_cookies_from_config()

    def _apply_boss_extra_cookies_from_config(self) -> None:
        raw = (getattr(settings, "BOSS_ZHIPIN_EXTRA_COOKIES", None) or "").strip()
        if raw:
            self.session.headers["Cookie"] = raw

    def _bootstrap_boss_session(self) -> None:
        """先访问首页与求职页，尽量拿到基础 Cookie（对无浏览器 Cookie 的环境帮助有限）。"""
        try:
            self.session.get("https://www.zhipin.com/", timeout=15)
            time.sleep(0.35)
            h = {
                **self.session.headers,
                "Referer": "https://www.zhipin.com/",
                "Sec-Fetch-Site": "same-origin",
            }
            self.session.get("https://www.zhipin.com/web/geek/job", headers=h, timeout=15)
            time.sleep(0.25)
        except requests.RequestException:
            pass

    @classmethod
    def _is_boss_gateway_html(cls, html: str) -> bool:
        if not html or len(html) < 200:
            return True
        return any(m in html for m in cls._BOSS_GATE_HTML_MARKERS)

    @classmethod
    def _is_interstitial_title(cls, title: Optional[str]) -> bool:
        t = (title or "").strip()
        if not t:
            return False
        return any(s in t for s in cls._INTERSTITIAL_TITLE_SUBSTR)

    @classmethod
    def _html_looks_like_zhipin_interstitial(cls, html: str) -> bool:
        """安全校验页 / 加载壳，非职位详情 HTML。"""
        if not html or len(html) < 80:
            return True
        if "security-check" in html or "common/security-check" in html:
            return True
        if "请稍候" in html and "boss-loading" in html:
            return True
        return False

    @staticmethod
    def _boss_result_is_empty(req: JobRequirements) -> bool:
        if JobScraper._is_interstitial_title(req.title):
            return True
        if req.title and req.title.strip() and req.title != "未知岗位":
            return False
        if req.company or req.salary or req.location:
            return False
        if req.responsibilities or req.required_skills:
            return False
        return True

    @staticmethod
    def _generic_result_is_empty(req: JobRequirements) -> bool:
        """通用页解析是否几乎无有效信息（用于决定是否再试 Jina）。"""
        if JobScraper._is_interstitial_title(req.title):
            return True
        if req.title and req.title.strip() and req.title != "未知岗位":
            return False
        if req.responsibilities or req.required_skills or req.preferred_skills:
            return False
        return True

    def _fetch_jina_reader_markdown(self, target_url: str) -> str:
        """通过 Jina Reader 将 URL 转为正文（Markdown/纯文本）。参见文档分层思路。"""
        base = (getattr(settings, "JINA_READER_BASE_URL", None) or "https://r.jina.ai").rstrip(
            "/"
        )
        jina_url = f"{base}/{target_url}"
        headers: Dict[str, str] = {
            "Accept": "text/plain",
            "User-Agent": self.DEFAULT_HEADERS["User-Agent"],
        }
        key = (getattr(settings, "JINA_API_KEY", None) or "").strip()
        if key:
            headers["Authorization"] = f"Bearer {key}"
        r = self.session.get(jina_url, timeout=45, headers=headers)
        r.raise_for_status()
        text = r.text or ""
        if len(text.strip()) < 80:
            raise ValueError("Jina Reader 返回内容过短")
        return text

    def _requirements_from_markdown_or_plain(self, text: str, source_url: str) -> JobRequirements:
        """将 Jina 返回的 Markdown/纯文本解析为 JobRequirements。"""
        raw = text.strip()
        lines = [ln.strip() for ln in raw.splitlines() if ln.strip()]
        title = "未知岗位"
        body = raw
        if lines:
            first = lines[0]
            if first.startswith("#"):
                title = first.lstrip("#").strip() or title
                body = "\n".join(lines[1:]) if len(lines) > 1 else raw
            elif len(first) < 200 and not first.startswith("|"):
                title = first
                body = "\n".join(lines[1:]) if len(lines) > 1 else raw
        responsibilities, required_skills, preferred_skills = self._parse_job_description(body)
        return JobRequirements(
            title=title or "未知岗位",
            company=None,
            responsibilities=responsibilities,
            required_skills=required_skills,
            preferred_skills=preferred_skills,
            experience_years=None,
            education_requirement=None,
        )

    def _maybe_jina_fallback(self, target_url: str) -> Optional[JobRequirements]:
        """Boss/通用爬取失败时的可选兜底；关闭或异常时返回 None。"""
        if not getattr(settings, "JOB_SCRAPE_JINA_READER_FALLBACK", True):
            return None
        try:
            md = self._fetch_jina_reader_markdown(target_url)
            req = self._requirements_from_markdown_or_plain(md, target_url)
            if self._generic_result_is_empty(req):
                return None
            return req
        except (requests.RequestException, ValueError, OSError):
            return None

    def _maybe_scrapling_fallback(self, target_url: str) -> Optional[JobRequirements]:
        """
        使用 Scrapling Fetcher（curl_cffi 指纹）拉取 HTML 再走通用解析。
        需安装: pip install "scrapling[fetchers]"
        """
        if not getattr(settings, "JOB_SCRAPE_SCRAPLING_FALLBACK", False):
            return None
        try:
            from scrapling.fetchers import Fetcher
        except ImportError:
            logger.debug(
                "已开启 JOB_SCRAPE_SCRAPLING_FALLBACK 但未安装 scrapling，跳过（pip install \"scrapling[fetchers]\"）"
            )
            return None
        verify = bool(getattr(settings, "JOB_SCRAPE_SCRAPLING_VERIFY_SSL", True))
        try:
            page = Fetcher.get(target_url, timeout=45, verify=verify)
            html = page.body.decode("utf-8", errors="replace")
            if len(html.strip()) < 200:
                return None
            req = self._scrape_generic_from_html(html, target_url)
            if self._generic_result_is_empty(req):
                return None
            return req
        except Exception:
            return None

    def _fallback_chain(self, target_url: str) -> Optional[JobRequirements]:
        """Jina Reader →（可选）Scrapling，任一成功即返回。"""
        j = self._maybe_jina_fallback(target_url)
        if j is not None:
            return j
        return self._maybe_scrapling_fallback(target_url)

    def scrape(self, job_url: str) -> JobRequirements:
        try:
            parsed_url = urlparse(job_url)
            domain = parsed_url.netloc.lower()
            time.sleep(self.REQUEST_DELAY)

            if "zhipin.com" in domain or "boss" in domain:
                return self._scrape_boss_zhipin(job_url)
            if "lagou.com" in domain:
                return self._scrape_lagou(job_url)
            if "liepin.com" in domain:
                return self._scrape_liepin(job_url)
            return self._scrape_generic(job_url)

        except ExternalServiceException:
            raise
        except Exception as e:
            raise ExternalServiceException(
                f"Failed to scrape job info: {str(e)}",
                service_name="JobScraper",
                original_error=str(e),
            )

    # ---------- Boss 直聘 ----------

    def _scrape_boss_zhipin(self, url: str) -> JobRequirements:
        self._bootstrap_boss_session()
        try:
            nav_headers = {
                **self.headers,
                "Referer": "https://www.zhipin.com/web/geek/job",
                "Sec-Fetch-Site": "same-origin",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Dest": "document",
            }
            response = self.session.get(url, timeout=25, headers=nav_headers)
            response.raise_for_status()
            if not response.encoding or response.encoding.lower() == "iso-8859-1":
                response.encoding = response.apparent_encoding or "utf-8"
            html = response.text
        except requests.RequestException as e:
            raise ExternalServiceException(
                f"Failed to fetch Boss直聘 page: {str(e)}",
                service_name="Boss直聘",
                original_error=str(e),
            )

        wapi_job, wapi_code, wapi_msg = self._try_boss_wapi(url)
        req_from_api: Optional[JobRequirements] = None
        if wapi_job:
            req_from_api = self._job_dict_to_requirements_from_wapi(wapi_job)

        regex_fields = self._extract_boss_json_string_fields(html)
        soup = BeautifulSoup(html, "lxml")
        soup_fields = self._extract_boss_dom_fields(soup)

        merged = self._merge_boss_sources(req_from_api, regex_fields, soup_fields, html)

        def _fail_boss_blocked() -> None:
            hint = (
                "Boss直聘未返回职位正文：页面被导向登录/验证，或接口拒绝访问。"
                " 常见原因：服务器/数据中心 IP 被判定异常（WAPI code=35/37 等）。"
                " 请在运行环境设置 BOSS_ZHIPIN_EXTRA_COOKIES（从本机浏览器已登录 zhipin.com 时"
                " 复制完整 Cookie 一行写入 .env，勿提交仓库），"
                " 或在家庭宽带/本机运行后端后再试；亦可改用「上传截图识别」保存岗位。"
            )
            detail = []
            if wapi_code is not None:
                detail.append(f"wapi_code={wapi_code}")
            if wapi_msg:
                detail.append(f"wapi_message={wapi_msg}")
            if detail:
                hint += " [" + "; ".join(detail) + "]"
            raise ExternalServiceException(
                hint,
                service_name="Boss直聘",
                original_error=wapi_msg or str(wapi_code),
            )

        # 门页上的 <title> 等会被通用解析误当成职位名，必须在无 WAPI 数据时直接失败
        if self._is_boss_gateway_html(html) and not wapi_job:
            fb = self._fallback_chain(url)
            if fb is not None:
                return fb
            _fail_boss_blocked()

        if (
            merged.title
            and merged.title != "未知岗位"
            and not self._is_interstitial_title(merged.title)
        ):
            return merged

        generic = self._scrape_generic_from_html(html, url)
        merged = self._merge_boss_sources(
            JobRequirements(
                title=generic.title,
                company=generic.company,
                responsibilities=generic.responsibilities,
                required_skills=generic.required_skills,
                preferred_skills=generic.preferred_skills,
            ),
            regex_fields,
            soup_fields,
            html,
        )

        if self._boss_result_is_empty(merged) and (
            self._is_boss_gateway_html(html)
            or (wapi_code is not None and wapi_code != 0)
        ):
            fb = self._fallback_chain(url)
            if fb is not None:
                return fb
            _fail_boss_blocked()

        return merged

    def _extract_job_from_wapi_payload(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """从 WAPI 根 JSON 中解析职位 dict（兼容多种 zpData 嵌套）。"""
        zp = data.get("zpData")
        if isinstance(zp, dict):
            if zp.get("jobName") or zp.get("title"):
                return zp
            for key in ("jobInfo", "jobDetail", "detail", "job", "jobCard"):
                j = zp.get(key)
                if isinstance(j, dict) and (j.get("jobName") or j.get("title")):
                    return j
            found = self._find_boss_job_dict(zp)
            if found:
                return found
        return self._find_boss_job_dict(data)

    def _try_boss_wapi(self, job_url: str) -> Tuple[Optional[Dict[str, Any]], Optional[int], Optional[str]]:
        """
        调用官方 detail.json。返回 (job_dict, api_code, api_message)。
        api_code 非 0 时表示风控/登录等，供上层提示。
        """
        parsed = urlparse(job_url)
        qs = parse_qs(parsed.query)
        security_id = (qs.get("securityId") or [None])[0]
        lid = (qs.get("lid") or [None])[0]
        m = re.search(r"/job_detail/([^/]+)\.html", job_url, re.I)
        encrypt_job_id = m.group(1) if m else None

        header_extra = {
            **self.session.headers,
            "Referer": job_url,
            "Origin": f"{parsed.scheme}://{parsed.netloc}",
            "Accept": "application/json, text/plain, */*",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
        }

        attempts: List[Dict[str, str]] = []
        if security_id and encrypt_job_id and lid:
            attempts.append(
                {"securityId": security_id, "encryptJobId": encrypt_job_id, "lid": lid}
            )
        if security_id and encrypt_job_id:
            attempts.append({"securityId": security_id, "encryptJobId": encrypt_job_id})
        if security_id:
            attempts.append({"securityId": security_id})
        if encrypt_job_id:
            attempts.append({"encryptJobId": encrypt_job_id})

        last_code: Optional[int] = None
        last_msg: Optional[str] = None

        for params in attempts:
            try:
                r = self.session.get(
                    self.BOSS_WAPI_DETAIL,
                    params=params,
                    headers=header_extra,
                    timeout=22,
                )
                if r.status_code != 200:
                    continue
                data = r.json()
                if not isinstance(data, dict):
                    continue
                code = data.get("code")
                msg = data.get("message") or data.get("msg") or ""
                if isinstance(code, int):
                    last_code = code
                if msg:
                    last_msg = str(msg)

                if code != 0:
                    continue

                job = self._extract_job_from_wapi_payload(data)
                if job:
                    return job, 0, None
            except (requests.RequestException, ValueError, json.JSONDecodeError):
                continue

        return None, last_code, last_msg

    @staticmethod
    def _find_boss_job_dict(obj: Any) -> Optional[Dict[str, Any]]:
        """在 WAPI 或页面 JSON 中递归查找含 jobName 的职位对象。"""

        def walk(o: Any) -> Optional[Dict[str, Any]]:
            if isinstance(o, dict):
                if o.get("jobName") or (
                    o.get("title") and (o.get("salaryDesc") or o.get("encryptJobId"))
                ):
                    return o
                for v in o.values():
                    r = walk(v)
                    if r:
                        return r
            elif isinstance(o, list):
                for it in o:
                    r = walk(it)
                    if r:
                        return r
            return None

        return walk(obj)

    def _job_dict_to_requirements_from_wapi(self, job: Dict[str, Any]) -> JobRequirements:
        title = (job.get("jobName") or job.get("title") or "").strip() or "未知岗位"
        company = job.get("brandName") or job.get("companyName")
        salary = job.get("salaryDesc")
        location = job.get("locationName") or job.get("cityName") or job.get("areaDistrict")
        industry = job.get("brandIndustry")
        company_scale = job.get("brandScaleName")
        financing_stage = (
            job.get("financeStage")
            or job.get("financeStageName")
            or job.get("brandStageName")
        )

        exp = job.get("jobExperience") or job.get("experienceName")
        edu = job.get("jobDegree") or job.get("degreeName")

        raw_html = (
            job.get("postDescription")
            or job.get("jobDesc")
            or job.get("detailDescription")
            or job.get("positionDetail")
            or ""
        )
        description = self._html_to_text(raw_html) if raw_html else ""

        skills = self._normalize_skill_list(job.get("skills"))
        skills = skills or self._normalize_skill_list(job.get("skillsLabels"))

        responsibilities, req_skills, pref_skills = self._parse_job_description(description)
        if not req_skills and skills:
            req_skills = skills[:40]

        if not responsibilities and description:
            responsibilities = [line.strip() for line in description.split("\n") if line.strip()][:50]

        return JobRequirements(
            title=title,
            company=company,
            salary=salary,
            location=location,
            industry=industry,
            company_scale=company_scale,
            financing_stage=financing_stage,
            responsibilities=responsibilities,
            required_skills=req_skills,
            preferred_skills=pref_skills,
            experience_years=exp,
            education_requirement=edu,
        )

    @staticmethod
    def _normalize_skill_list(raw: Any) -> List[str]:
        if not raw:
            return []
        if isinstance(raw, str):
            return [raw]
        out: List[str] = []
        if isinstance(raw, list):
            for it in raw:
                if isinstance(it, str):
                    out.append(it)
                elif isinstance(it, dict):
                    name = it.get("name") or it.get("skillName")
                    if name:
                        out.append(str(name))
        return out

    @staticmethod
    def _html_to_text(html: str) -> str:
        if not html or not html.strip():
            return ""
        soup = BeautifulSoup(html, "lxml")
        return soup.get_text(separator="\n", strip=True)

    def _extract_boss_json_string_fields(self, html: str) -> Dict[str, Optional[str]]:
        """
        从页面 HTML 中直接匹配 JSON 字符串字段（Boss 常在 script 中嵌入大段 JSON）。
        """
        keys = [
            "jobName",
            "brandName",
            "salaryDesc",
            "locationName",
            "cityName",
            "jobExperience",
            "jobDegree",
            "brandIndustry",
            "brandScaleName",
            "financeStage",
            "financeStageName",
        ]
        out: Dict[str, Optional[str]] = {}
        for key in keys:
            val = self._read_json_string_value(html, key)
            if val:
                out[key] = val
        return out

    @staticmethod
    def _read_json_string_value(html: str, key: str) -> Optional[str]:
        # 匹配 "key":"..." 支持 \" 与 \uXXXX
        pat = rf'"{re.escape(key)}"\s*:\s*"((?:[^"\\]|\\.)*)"'
        m = re.search(pat, html)
        if not m:
            return None
        raw = '"' + m.group(1) + '"'
        try:
            return str(json.loads(raw))
        except json.JSONDecodeError:
            return unescape(m.group(1).replace(r"\\", "\\"))

    def _extract_boss_dom_fields(self, soup: BeautifulSoup) -> Dict[str, Optional[str]]:
        """
        从 DOM 提取信息（兼容不同版本 class）。
        """
        title = None
        for sel in ["h1.name", ".job-name", "h1.job-name", "div.job-title h1", "h1"]:
            el = soup.select_one(sel)
            if el and el.get_text(strip=True):
                title = el.get_text(strip=True)
                break

        salary = None
        for sel in [".salary", ".job-limit .red", "span.salary", ".info-primary .salary"]:
            el = soup.select_one(sel)
            if el and el.get_text(strip=True):
                salary = el.get_text(strip=True)
                break

        company = None
        for sel in [
            "a.company-name",
            ".company-name",
            "a[ka='job-detail-company-name']",
            ".company-info .name",
            "div.company-info a",
        ]:
            el = soup.select_one(sel)
            if el and el.get_text(strip=True):
                company = el.get_text(strip=True)
                break

        location = None
        for sel in [".job-location", ".location-address", ".location"]:
            el = soup.select_one(sel)
            if el and el.get_text(strip=True):
                t = el.get_text(strip=True)
                if "市" in t or "省" in t or "区" in t or "·" in t:
                    location = t
                    break

        if not location:
            info = soup.select_one(".job-limit") or soup.select_one(".info-primary")
            if info:
                txt = info.get_text(" ", strip=True)
                if txt:
                    location = txt

        desc_el = soup.select_one(".job-sec-text") or soup.select_one(
            ".job-detail"
        ) or soup.select_one(".job-detail-section")
        description = desc_el.get_text("\n", strip=True) if desc_el else None

        return {
            "title": title,
            "salary": salary,
            "company": company,
            "location": location,
            "description": description,
        }

    def _merge_boss_sources(
        self,
        api_req: Optional[JobRequirements],
        regex_fields: Dict[str, Optional[str]],
        soup_fields: Dict[str, Optional[str]],
        page_html: str,
        fallback_description: Optional[str] = None,
    ) -> JobRequirements:
        title = (
            (api_req.title if api_req and api_req.title != "未知岗位" else None)
            or regex_fields.get("jobName")
            or soup_fields.get("title")
            or "未知岗位"
        )

        company = (
            (api_req.company if api_req else None)
            or regex_fields.get("brandName")
            or soup_fields.get("company")
        )

        salary = (api_req.salary if api_req else None) or regex_fields.get(
            "salaryDesc"
        ) or soup_fields.get("salary")

        location = (
            (api_req.location if api_req else None)
            or regex_fields.get("locationName")
            or regex_fields.get("cityName")
            or soup_fields.get("location")
        )

        industry = (api_req.industry if api_req else None) or regex_fields.get(
            "brandIndustry"
        )
        company_scale = (api_req.company_scale if api_req else None) or regex_fields.get(
            "brandScaleName"
        )
        financing_stage = (api_req.financing_stage if api_req else None) or regex_fields.get(
            "financeStage"
        ) or regex_fields.get("financeStageName")

        exp = (
            (api_req.experience_years if api_req else None)
            or regex_fields.get("jobExperience")
        )
        edu = (
            (api_req.education_requirement if api_req else None)
            or regex_fields.get("jobDegree")
        )

        if api_req:
            responsibilities = list(api_req.responsibilities)
            required_skills = list(api_req.required_skills)
            preferred_skills = list(api_req.preferred_skills)
        else:
            responsibilities = []
            required_skills = []
            preferred_skills = []

        desc_text = soup_fields.get("description") or ""
        if not desc_text and fallback_description:
            desc_text = fallback_description
        if not desc_text:
            # 再尝试从页面正则拉 postDescription
            post_desc = self._read_json_string_value(page_html, "postDescription")
            if post_desc:
                desc_text = self._html_to_text(post_desc)

        if desc_text:
            r2, req2, pref2 = self._parse_job_description(desc_text)
            if not responsibilities:
                responsibilities = r2
            if not required_skills:
                required_skills = req2
            if not preferred_skills:
                preferred_skills = pref2
            if not responsibilities:
                responsibilities = [
                    line.strip() for line in desc_text.split("\n") if line.strip()
                ][:50]

        return JobRequirements(
            title=title,
            company=company,
            salary=salary,
            location=location,
            industry=industry,
            company_scale=company_scale,
            financing_stage=financing_stage,
            responsibilities=responsibilities,
            required_skills=required_skills,
            preferred_skills=preferred_skills,
            experience_years=exp,
            education_requirement=edu,
        )

    def _scrape_lagou(self, url: str) -> JobRequirements:
        return self._scrape_generic(url)

    def _scrape_liepin(self, url: str) -> JobRequirements:
        return self._scrape_generic(url)

    def _scrape_generic(self, url: str) -> JobRequirements:
        last_exc: Optional[requests.RequestException] = None
        try:
            response = self.session.get(url, timeout=20)
            response.raise_for_status()
            req = self._scrape_generic_from_html(response.text, url)
            if not self._generic_result_is_empty(req):
                return req
        except requests.RequestException as e:
            last_exc = e

        fb = self._fallback_chain(url)
        if fb is not None:
            return fb

        if last_exc is not None:
            raise ExternalServiceException(
                f"Failed to fetch job page: {str(last_exc)}",
                service_name="Generic Scraper",
                original_error=str(last_exc),
            )
        raise ExternalServiceException(
            "无法从页面解析有效岗位信息，且 Jina / Scrapling 兜底未返回内容",
            service_name="Generic Scraper",
            original_error="empty",
        )

    def _scrape_generic_from_html(self, html: str, url: str) -> JobRequirements:
        if self._html_looks_like_zhipin_interstitial(html):
            return JobRequirements(
                title="未知岗位",
                responsibilities=[],
                required_skills=[],
                preferred_skills=[],
            )
        soup = BeautifulSoup(html, "lxml")
        title = ""
        h1 = soup.find("h1")
        if h1:
            title = h1.get_text(strip=True)
        elif soup.title:
            title = soup.title.get_text(strip=True)
        if self._is_interstitial_title(title):
            title = "未知岗位"
        for script in soup(["script", "style"]):
            script.decompose()
        text = soup.get_text(separator="\n", strip=True)
        responsibilities, required_skills, preferred_skills = self._parse_job_description(text)
        return JobRequirements(
            title=title or "未知岗位",
            company=None,
            responsibilities=responsibilities,
            required_skills=required_skills,
            preferred_skills=preferred_skills,
            experience_years=None,
            education_requirement=None,
        )

    def _parse_job_description(
        self,
        description: str,
    ) -> tuple[list[str], list[str], list[str]]:
        responsibilities = []
        required_skills = []
        preferred_skills = []
        lines = description.split("\n")
        current_section = None

        for line in lines:
            line = line.strip()
            if not line:
                continue
            lower_line = line.lower()

            if any(
                kw in lower_line for kw in ["职责", "工作内容", "负责", "duties", "responsibilities"]
            ):
                current_section = "responsibilities"
                continue
            if any(
                kw in lower_line
                for kw in ["要求", "必备", "任职", "qualifications", "requirements"]
            ):
                current_section = "required"
                continue
            if any(kw in lower_line for kw in ["加分", "优先", "preferred", "nice to have"]):
                current_section = "preferred"
                continue

            if re.match(r"^[\d\.\-\•\*\·]+\s*", line):
                cleaned = re.sub(r"^[\d\.\-\•\*\·]+\s*", "", line).strip()
                if cleaned:
                    if current_section == "responsibilities":
                        responsibilities.append(cleaned)
                    elif current_section == "required":
                        required_skills.append(cleaned)
                    elif current_section == "preferred":
                        preferred_skills.append(cleaned)
            elif current_section and len(line) < 200:
                if current_section == "responsibilities":
                    responsibilities.append(line)
                elif current_section == "required":
                    required_skills.append(line)
                elif current_section == "preferred":
                    preferred_skills.append(line)

        return responsibilities, required_skills, preferred_skills


def scrape_job_info(job_url: str) -> JobRequirements:
    """
    爬取岗位信息的便捷函数

    ⚠️ 仅用于学习目的，请遵守网站 robots.txt 规则。
    """
    scraper = JobScraper()
    return scraper.scrape(job_url)
