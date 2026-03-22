"""
Job Scraper Service - 岗位信息爬取服务

爬取 Boss直聘等招聘网站的岗位信息。

⚠️ 注意：本模块仅用于学习目的，请遵守网站的 robots.txt 规则。
"""

import json
import re
import time
from html import unescape
from typing import Any, Dict, List, Optional
from urllib.parse import parse_qs, urlparse

import requests
from bs4 import BeautifulSoup

from app.core.exceptions import ExternalServiceException
from app.models.schemas import JobRequirements


class JobScraper:
    """
    岗位信息爬取器

    支持从 Boss直聘 等招聘网站爬取岗位详情。

    ⚠️ 仅用于学习目的，请遵守网站 robots.txt 规则。
    """

    # 请求头，模拟浏览器（Boss 会校验 Referer / Accept）
    DEFAULT_HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Cache-Control": "no-cache",
    }

    REQUEST_DELAY = 2

    BOSS_WAPI_DETAIL = "https://www.zhipin.com/wapi/zpgeek/job/detail.json"

    def __init__(self, headers: Optional[Dict[str, str]] = None):
        self.headers = headers or self.DEFAULT_HEADERS
        self.session = requests.Session()
        self.session.headers.update(self.headers)

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
        try:
            response = self.session.get(url, timeout=20)
            response.raise_for_status()
            html = response.text
        except requests.RequestException as e:
            raise ExternalServiceException(
                f"Failed to fetch Boss直聘 page: {str(e)}",
                service_name="Boss直聘",
                original_error=str(e),
            )

        # 1) 优先：官方 WAPI JSON（页面内请求同源接口，携带 securityId / encryptJobId）
        wapi_data = self._try_boss_wapi(url)
        req_from_api: Optional[JobRequirements] = None
        if wapi_data:
            req_from_api = self._job_dict_to_requirements_from_wapi(wapi_data)

        # 2) 从整页 HTML 中正则提取内嵌 JSON 字段（SSR / 脚本中的职位数据）
        regex_fields = self._extract_boss_json_string_fields(html)

        # 3) BeautifulSoup 选择器兜底
        soup = BeautifulSoup(html, "lxml")
        soup_fields = self._extract_boss_dom_fields(soup)

        merged = self._merge_boss_sources(req_from_api, regex_fields, soup_fields, html)
        if merged.title and merged.title != "未知岗位":
            return merged

        # 4) 仍无标题时走通用正文解析
        generic = self._scrape_generic_from_html(html, url)
        return self._merge_boss_sources(
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

    def _try_boss_wapi(self, job_url: str) -> Optional[Dict[str, Any]]:
        parsed = urlparse(job_url)
        qs = parse_qs(parsed.query)
        security_id = (qs.get("securityId") or [None])[0]
        lid = (qs.get("lid") or [None])[0]
        m = re.search(r"/job_detail/([^/]+)\.html", job_url, re.I)
        encrypt_job_id = m.group(1) if m else None

        header_extra = {
            **self.headers,
            "Referer": job_url,
            "Origin": f"{parsed.scheme}://{parsed.netloc}",
            "Accept": "application/json, text/plain, */*",
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

        for params in attempts:
            try:
                r = self.session.get(
                    self.BOSS_WAPI_DETAIL,
                    params=params,
                    headers=header_extra,
                    timeout=18,
                )
                if r.status_code != 200:
                    continue
                data = r.json()
                if data.get("code") != 0:
                    continue
                zp = data.get("zpData")
                if isinstance(zp, dict):
                    for key in ("jobInfo", "jobDetail", "detail", "job"):
                        j = zp.get(key)
                        if isinstance(j, dict) and j.get("jobName"):
                            return j
                job = self._find_boss_job_dict(data)
                if job:
                    return job
            except (requests.RequestException, ValueError, json.JSONDecodeError):
                continue
        return None

    @staticmethod
    def _find_boss_job_dict(obj: Any) -> Optional[Dict[str, Any]]:
        """在 WAPI 或页面 JSON 中递归查找含 jobName 的职位对象。"""

        def walk(o: Any) -> Optional[Dict[str, Any]]:
            if isinstance(o, dict):
                if "jobName" in o and o.get("jobName"):
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
        title = (job.get("jobName") or "").strip() or "未知岗位"
        company = job.get("brandName") or job.get("companyName")
        salary = job.get("salaryDesc")
        location = job.get("locationName") or job.get("cityName")
        industry = job.get("brandIndustry")
        company_scale = job.get("brandScaleName")
        financing_stage = job.get("financeStage") or job.get("financeStageName")

        exp = job.get("jobExperience") or job.get("experienceName")
        edu = job.get("jobDegree") or job.get("degreeName")

        raw_html = job.get("postDescription") or job.get("jobDesc") or ""
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
        try:
            response = self.session.get(url, timeout=20)
            response.raise_for_status()
            return self._scrape_generic_from_html(response.text, url)
        except requests.RequestException as e:
            raise ExternalServiceException(
                f"Failed to fetch job page: {str(e)}",
                service_name="Generic Scraper",
                original_error=str(e),
            )

    def _scrape_generic_from_html(self, html: str, url: str) -> JobRequirements:
        soup = BeautifulSoup(html, "lxml")
        title = ""
        h1 = soup.find("h1")
        if h1:
            title = h1.get_text(strip=True)
        elif soup.title:
            title = soup.title.get_text(strip=True)
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
