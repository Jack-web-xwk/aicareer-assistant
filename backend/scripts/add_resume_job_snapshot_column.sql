-- 若本地 SQLite 数据库在引入 job_snapshot 字段前已创建，请执行一次：
-- sqlite3 your.db < add_resume_job_snapshot_column.sql
-- 或手动：ALTER TABLE resumes ADD COLUMN job_snapshot TEXT;

ALTER TABLE resumes ADD COLUMN job_snapshot TEXT;
