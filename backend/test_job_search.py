"""职位搜索：normalize / aggregator 单元测试（mock 外呼）。"""

from app.models.job_search_schemas import JobSearchQuery, JobSource, MatchMode, SortBy, SortOrder
from app.services.job_search.aggregator import aggregate_jobs
from app.services.job_search.normalize import raw_row_to_unified
from app.services.job_search.types import RawJobRow


def test_raw_row_to_unified_maps_source():
    row = RawJobRow(
        title=" 工程师 ",
        company_name="ACME",
        salary_text="20-30K",
        location="北京",
        published_at="1700000000000",
        experience_text="3-5年",
        education_text="本科",
        detail_url="https://example.com/j/1",
        raw_snippet=None,
    )
    u = raw_row_to_unified(row, JobSource.BOSS)
    assert u.title == "工程师"
    assert u.source == JobSource.BOSS
    assert u.detail_url == "https://example.com/j/1"


def test_aggregate_dedupes_by_detail_url(monkeypatch):
    from app.services.job_search import aggregator as agg

    def fake_boss(*args, **kwargs):
        return (
            [
                RawJobRow(
                    title="A",
                    company_name="X",
                    salary_text="",
                    location="",
                    published_at="1",
                    experience_text="",
                    education_text="",
                    detail_url="https://same",
                )
            ],
            1,
        )

    def fake_zhi(*args, **kwargs):
        return (
            [
                RawJobRow(
                    title="B",
                    company_name="Y",
                    salary_text="",
                    location="",
                    published_at="2",
                    experience_text="",
                    education_text="",
                    detail_url="https://same",
                )
            ],
            1,
        )

    def fake_yu(*args, **kwargs):
        return ([], None)

    monkeypatch.setattr(agg, "search_boss_jobs", fake_boss)
    monkeypatch.setattr(agg, "search_zhaopin_jobs", fake_zhi)
    monkeypatch.setattr(agg, "search_yupao_jobs", fake_yu)

    q = JobSearchQuery(
        keyword="test",
        sources=[JobSource.BOSS, JobSource.ZHAOPIN],
        page=1,
        page_size=10,
        match_mode=MatchMode.FUZZY,
        sort_by=SortBy.PUBLISHED_AT,
        sort_order=SortOrder.DESC,
    )
    items, total, used, _warn = aggregate_jobs(q)
    assert total == 1
    assert len(items) == 1
    assert "boss" in used and "zhaopin" in used


def test_aggregate_global_pagination(monkeypatch):
    from app.services.job_search import aggregator as agg

    def fake_boss(*args, **kwargs):
        rows = []
        for i in range(5):
            rows.append(
                RawJobRow(
                    title=f"T{i}",
                    company_name="C",
                    salary_text="10K",
                    location="",
                    published_at=str(1000 + i),
                    experience_text="",
                    education_text="",
                    detail_url=f"https://ex.com/{i}",
                )
            )
        return rows, 5

    monkeypatch.setattr(agg, "search_boss_jobs", fake_boss)
    monkeypatch.setattr(agg, "search_zhaopin_jobs", lambda *a, **k: ([], None))
    monkeypatch.setattr(agg, "search_yupao_jobs", lambda *a, **k: ([], None))

    q = JobSearchQuery(
        keyword="x",
        sources=[JobSource.BOSS],
        page=2,
        page_size=2,
        match_mode=MatchMode.FUZZY,
        sort_by=SortBy.PUBLISHED_AT,
        sort_order=SortOrder.DESC,
    )
    items, total, _, _ = aggregate_jobs(q)
    assert total == 5
    assert len(items) == 2
    assert items[0].title == "T2"


def test_cache_key_stable():
    """原始 cache_key 对 JSON 键顺序敏感；规范化 sources 后同义查询应对应同一 key。"""
    from app.services.job_search.cache import cache_key

    a = cache_key({"sources": ["boss", "zhaopin"], "keyword": "a"})
    b = cache_key({"keyword": "a", "sources": ["zhaopin", "boss"]})
    assert a != b

    def normalize_payload(q: JobSearchQuery) -> dict:
        d = q.model_dump(mode="json", exclude_none=True)
        if "sources" in d and isinstance(d["sources"], list):
            d["sources"] = sorted(d["sources"])
        return d

    q1 = JobSearchQuery(keyword="a", sources=[JobSource.ZHAOPIN, JobSource.BOSS])
    q2 = JobSearchQuery(keyword="a", sources=[JobSource.BOSS, JobSource.ZHAOPIN])
    assert cache_key(normalize_payload(q1)) == cache_key(normalize_payload(q2))
