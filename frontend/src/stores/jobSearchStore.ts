import axios from 'axios'
import { create } from 'zustand'
import { persist } from 'zustand/middleware'

import { jobSearchApi } from '../services/api'
import type {
  JobSearchQuery,
  JobSearchResponse,
  JobSource,
  JobSortBy,
  JobSortOrder,
  JobMatchMode,
  UnifiedJobItem,
} from '../types'

const ALL_SOURCES: JobSource[] = ['boss', 'zhaopin', 'yupao']

export const defaultJobSearchQuery = (): JobSearchQuery => ({
  keyword: '',
  company_keyword: '',
  match_mode: 'fuzzy',
  city: undefined,
  salary_min: undefined,
  salary_max: undefined,
  experience: undefined,
  sources: [...ALL_SOURCES],
  sort_by: 'published_at',
  sort_order: 'desc',
  page: 1,
  page_size: 15,
})

function isCanceled(err: unknown): boolean {
  if (axios.isAxiosError(err)) {
    return err.code === 'ERR_CANCELED' || axios.isCancel(err)
  }
  return false
}

function buildQuery(state: JobSearchStore): JobSearchQuery {
  return {
    keyword: state.keyword,
    company_keyword: state.company_keyword,
    match_mode: state.match_mode,
    city: state.city || undefined,
    salary_min: state.salary_min ?? undefined,
    salary_max: state.salary_max ?? undefined,
    experience: state.experience || undefined,
    sources: state.sources.length ? state.sources : [...ALL_SOURCES],
    sort_by: state.sort_by,
    sort_order: state.sort_order,
    page: state.page,
    page_size: state.page_size,
  }
}

export interface JobSearchHistoryEntry {
  label: string
  query: JobSearchQuery
  savedAt: string
}

interface JobSearchStore {
  keyword: string
  company_keyword: string
  match_mode: JobMatchMode
  city: string
  salary_min: number | undefined
  salary_max: number | undefined
  experience: string
  sources: JobSource[]
  sort_by: JobSortBy
  sort_order: JobSortOrder
  page: number
  page_size: number

  items: UnifiedJobItem[]
  total: number
  sources_used: string[]
  cached: boolean
  warning: string | undefined
  loading: boolean
  lastError: string | undefined

  liveSearch: boolean
  history: JobSearchHistoryEntry[]

  setKeyword: (v: string) => void
  setCompanyKeyword: (v: string) => void
  setMatchMode: (v: JobMatchMode) => void
  setCity: (v: string) => void
  setSalaryMin: (v: number | undefined) => void
  setSalaryMax: (v: number | undefined) => void
  setExperience: (v: string) => void
  setSources: (v: JobSource[]) => void
  setSortBy: (v: JobSortBy) => void
  setSortOrder: (v: JobSortOrder) => void
  setPage: (v: number) => void
  setPageSize: (v: number) => void
  setLiveSearch: (v: boolean) => void

  runSearch: (options?: { saveHistory?: boolean }) => Promise<void>
  applyHistoryEntry: (entry: JobSearchHistoryEntry) => void
  pushHistoryFromCurrent: () => void
  resetFilters: () => void
}

let searchAbort: AbortController | null = null

export const useJobSearchStore = create<JobSearchStore>()(
  persist(
    (set, get) => ({
      keyword: '',
      company_keyword: '',
      match_mode: 'fuzzy',
      city: '',
      salary_min: undefined,
      salary_max: undefined,
      experience: '',
      sources: [...ALL_SOURCES],
      sort_by: 'published_at',
      sort_order: 'desc',
      page: 1,
      page_size: 15,

      items: [],
      total: 0,
      sources_used: [],
      cached: false,
      warning: undefined,
      loading: false,
      lastError: undefined,

      liveSearch: false,
      history: [],

      setKeyword: (keyword) => set({ keyword }),
      setCompanyKeyword: (company_keyword) => set({ company_keyword }),
      setMatchMode: (match_mode) => set({ match_mode }),
      setCity: (city) => set({ city }),
      setSalaryMin: (salary_min) => set({ salary_min }),
      setSalaryMax: (salary_max) => set({ salary_max }),
      setExperience: (experience) => set({ experience }),
      setSources: (sources) => set({ sources }),
      setSortBy: (sort_by) => set({ sort_by }),
      setSortOrder: (sort_order) => set({ sort_order }),
      setPage: (page) => set({ page }),
      setPageSize: (page_size) => set({ page_size }),
      setLiveSearch: (liveSearch) => set({ liveSearch }),

      resetFilters: () => {
        const d = defaultJobSearchQuery()
        set({
          keyword: d.keyword,
          company_keyword: d.company_keyword,
          match_mode: d.match_mode,
          city: d.city ?? '',
          salary_min: d.salary_min ?? undefined,
          salary_max: d.salary_max ?? undefined,
          experience: d.experience ?? '',
          sources: d.sources,
          sort_by: d.sort_by,
          sort_order: d.sort_order,
          page: 1,
          page_size: d.page_size,
        })
      },

      applyHistoryEntry: (entry) => {
        const q = entry.query
        set({
          keyword: q.keyword,
          company_keyword: q.company_keyword,
          match_mode: q.match_mode,
          city: q.city ?? '',
          salary_min: q.salary_min ?? undefined,
          salary_max: q.salary_max ?? undefined,
          experience: q.experience ?? '',
          sources: q.sources?.length ? q.sources : [...ALL_SOURCES],
          sort_by: q.sort_by,
          sort_order: q.sort_order,
          page: q.page,
          page_size: q.page_size,
        })
        void get().runSearch({ saveHistory: true })
      },

      pushHistoryFromCurrent: () => {
        const q = buildQuery(get())
        const label = [q.keyword, q.company_keyword, q.city].filter(Boolean).join(' · ') || '（空条件）'
        const entry: JobSearchHistoryEntry = {
          label,
          query: { ...q },
          savedAt: new Date().toISOString(),
        }
        set((s) => {
          const rest = s.history.filter(
            (h) => JSON.stringify(h.query) !== JSON.stringify(entry.query)
          )
          return { history: [entry, ...rest].slice(0, 10) }
        })
      },

      runSearch: async (options?: { saveHistory?: boolean }) => {
        searchAbort?.abort()
        searchAbort = new AbortController()
        set({ loading: true, lastError: undefined })
        const q = buildQuery(get())
        try {
          const res = await jobSearchApi.search(q, { signal: searchAbort.signal })
          if (!res.success || !res.data) {
            set({ loading: false, lastError: res.message || '搜索失败' })
            return
          }
          const data = res.data as JobSearchResponse
          set({
            loading: false,
            items: data.items,
            total: data.total,
            sources_used: data.sources_used,
            cached: data.cached,
            warning: data.warning ?? undefined,
          })
          if (options?.saveHistory) {
            get().pushHistoryFromCurrent()
          }
        } catch (err: unknown) {
          if (isCanceled(err)) {
            set({ loading: false })
            return
          }
          const msg = err instanceof Error ? err.message : '搜索失败'
          set({ loading: false, lastError: msg })
        }
      },
    }),
    {
      name: 'job-search-storage',
      partialize: (s) => ({ history: s.history }),
    }
  )
)
