"""
Job Scraper Service - 岗位信息爬取服务

爬取 Boss直聘等招聘网站的岗位信息。

⚠️ 注意：本模块仅用于学习目的，请遵守网站的 robots.txt 规则。
"""

import re
import time
from typing import Dict, Optional
from urllib.parse import urlparse

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
    
    # 请求头，模拟浏览器
    DEFAULT_HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    }
    
    # 请求延迟（秒），避免对服务器造成压力
    REQUEST_DELAY = 2
    
    def __init__(self, headers: Optional[Dict[str, str]] = None):
        """
        初始化爬取器
        
        Args:
            headers: 自定义请求头
        """
        self.headers = headers or self.DEFAULT_HEADERS
        self.session = requests.Session()
        self.session.headers.update(self.headers)
    
    def scrape(self, job_url: str) -> JobRequirements:
        """
        爬取岗位信息
        
        Args:
            job_url: 岗位详情页链接
        
        Returns:
            JobRequirements: 解析后的岗位需求信息
        
        Raises:
            ExternalServiceException: 爬取失败
        """
        try:
            # 解析 URL，判断是哪个招聘网站
            parsed_url = urlparse(job_url)
            domain = parsed_url.netloc.lower()
            
            # 添加请求延迟，避免对服务器造成压力
            # ⚠️ 仅用于学习目的，请遵守网站 robots.txt 规则
            time.sleep(self.REQUEST_DELAY)
            
            if "zhipin.com" in domain or "boss" in domain:
                return self._scrape_boss_zhipin(job_url)
            elif "lagou.com" in domain:
                return self._scrape_lagou(job_url)
            elif "liepin.com" in domain:
                return self._scrape_liepin(job_url)
            else:
                # 通用解析
                return self._scrape_generic(job_url)
        
        except ExternalServiceException:
            raise
        except Exception as e:
            raise ExternalServiceException(
                f"Failed to scrape job info: {str(e)}",
                service_name="JobScraper",
                original_error=str(e),
            )
    
    def _scrape_boss_zhipin(self, url: str) -> JobRequirements:
        """
        爬取 Boss直聘 岗位信息
        
        ⚠️ 仅用于学习目的，请遵守网站 robots.txt 规则。
        由于 Boss直聘 有反爬机制，实际使用可能需要其他方式获取数据。
        """
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, "lxml")
            
            # 提取岗位标题
            title_elem = soup.find("h1", class_="name") or soup.find("div", class_="job-name")
            title = title_elem.get_text(strip=True) if title_elem else "未知岗位"
            
            # 提取公司名称
            company_elem = soup.find("a", class_="company-name") or soup.find("div", class_="company-info")
            company = company_elem.get_text(strip=True) if company_elem else None
            
            # 提取岗位描述
            desc_elem = soup.find("div", class_="job-detail") or soup.find("div", class_="job-sec-text")
            description = desc_elem.get_text(strip=True) if desc_elem else ""
            
            # 从描述中提取职责和要求
            responsibilities, required_skills, preferred_skills = self._parse_job_description(description)
            
            # 提取经验和学历要求
            experience_years = None
            education_requirement = None
            
            # 查找标签信息
            tags = soup.find_all("span", class_="tag-item") or soup.find_all("span", class_="text-des")
            for tag in tags:
                text = tag.get_text(strip=True)
                if "经验" in text or "年" in text:
                    experience_years = text
                elif any(edu in text for edu in ["本科", "硕士", "博士", "大专", "学历"]):
                    education_requirement = text
            
            return JobRequirements(
                title=title,
                company=company,
                responsibilities=responsibilities,
                required_skills=required_skills,
                preferred_skills=preferred_skills,
                experience_years=experience_years,
                education_requirement=education_requirement,
            )
        
        except requests.RequestException as e:
            raise ExternalServiceException(
                f"Failed to fetch Boss直聘 page: {str(e)}",
                service_name="Boss直聘",
                original_error=str(e),
            )
    
    def _scrape_lagou(self, url: str) -> JobRequirements:
        """爬取拉勾网岗位信息"""
        # 拉勾网爬取逻辑，结构类似
        return self._scrape_generic(url)
    
    def _scrape_liepin(self, url: str) -> JobRequirements:
        """爬取猎聘网岗位信息"""
        # 猎聘网爬取逻辑
        return self._scrape_generic(url)
    
    def _scrape_generic(self, url: str) -> JobRequirements:
        """
        通用网页爬取
        
        适用于未适配的招聘网站。
        """
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, "lxml")
            
            # 尝试提取标题（通常在 h1 或 title 标签）
            title = ""
            h1 = soup.find("h1")
            if h1:
                title = h1.get_text(strip=True)
            elif soup.title:
                title = soup.title.get_text(strip=True)
            
            # 提取页面主要文本内容
            # 移除脚本和样式
            for script in soup(["script", "style"]):
                script.decompose()
            
            text = soup.get_text(separator="\n", strip=True)
            
            # 解析职责和技能要求
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
        
        except requests.RequestException as e:
            raise ExternalServiceException(
                f"Failed to fetch job page: {str(e)}",
                service_name="Generic Scraper",
                original_error=str(e),
            )
    
    def _parse_job_description(
        self,
        description: str,
    ) -> tuple[list[str], list[str], list[str]]:
        """
        解析岗位描述，提取职责和技能要求
        
        Args:
            description: 岗位描述文本
        
        Returns:
            (responsibilities, required_skills, preferred_skills)
        """
        responsibilities = []
        required_skills = []
        preferred_skills = []
        
        # 按行分割
        lines = description.split("\n")
        
        # 状态机：当前正在解析的部分
        current_section = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # 判断段落类型
            lower_line = line.lower()
            
            if any(kw in lower_line for kw in ["职责", "工作内容", "负责", "duties", "responsibilities"]):
                current_section = "responsibilities"
                continue
            elif any(kw in lower_line for kw in ["要求", "必备", "任职", "qualifications", "requirements"]):
                current_section = "required"
                continue
            elif any(kw in lower_line for kw in ["加分", "优先", "preferred", "nice to have"]):
                current_section = "preferred"
                continue
            
            # 提取列表项（以数字、点号、短横线开头的行）
            if re.match(r"^[\d\.\-\•\*\·]+\s*", line):
                cleaned = re.sub(r"^[\d\.\-\•\*\·]+\s*", "", line).strip()
                if cleaned:
                    if current_section == "responsibilities":
                        responsibilities.append(cleaned)
                    elif current_section == "required":
                        required_skills.append(cleaned)
                    elif current_section == "preferred":
                        preferred_skills.append(cleaned)
            elif current_section and len(line) < 200:  # 避免太长的段落
                if current_section == "responsibilities":
                    responsibilities.append(line)
                elif current_section == "required":
                    required_skills.append(line)
                elif current_section == "preferred":
                    preferred_skills.append(line)
        
        return responsibilities, required_skills, preferred_skills


# 便捷函数
def scrape_job_info(job_url: str) -> JobRequirements:
    """
    爬取岗位信息的便捷函数
    
    Args:
        job_url: 岗位详情页链接
    
    Returns:
        JobRequirements: 解析后的岗位需求信息
    
    ⚠️ 仅用于学习目的，请遵守网站 robots.txt 规则。
    """
    scraper = JobScraper()
    return scraper.scrape(job_url)
