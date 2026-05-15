import axios, { AxiosError, AxiosInstance } from "axios";

const API_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const TOKEN_KEY = "phongthuy_bds_token";
const REFRESH_KEY = "phongthuy_bds_refresh";

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(access: string, refresh: string): void {
  if (typeof window === "undefined") return;
  localStorage.setItem(TOKEN_KEY, access);
  localStorage.setItem(REFRESH_KEY, refresh);
}

export function clearToken(): void {
  if (typeof window === "undefined") return;
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(REFRESH_KEY);
}

export const api: AxiosInstance = axios.create({
  baseURL: API_URL,
  timeout: 30_000,
});

api.interceptors.request.use((config) => {
  const token = getToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (r) => r,
  (err: AxiosError) => {
    if (err.response?.status === 401 && typeof window !== "undefined") {
      clearToken();
      window.location.href = "/login";
    }
    return Promise.reject(err);
  },
);

// ─── Domain types (mirror Pydantic schemas) ───────────────────────
export type Gender = "nam" | "nu";

export type Purpose =
  | "dong_tho"
  | "nhap_trach"
  | "khai_truong"
  | "dat_mong";

export interface User {
  id: string;
  tenant_id: string;
  email: string;
  full_name: string;
  role: "owner" | "admin" | "broker" | "viewer";
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in_min: number;
}

export interface Customer {
  id: string;
  tenant_id: string;
  full_name: string;
  phone: string | null;
  birth_date: string;
  gender: Gender;
  delete_after: string;
  created_at: string;
}

export interface OcrSoDoResponse {
  land_title_id: string;
  template_version: string;
  extracted: {
    nguoi_su_dung: string | null;
    thua_dat_so: string | null;
    to_ban_do_so: string | null;
    dia_chi: string | null;
    dien_tich_m2: string | null;
    muc_dich_su_dung: string | null;
    thoi_han_su_dung: string | null;
    so_seri: string | null;
    so_vao_so: string | null;
  };
  confidence: number;
  needs_review: boolean;
  created_at: string;
}

export interface ReportResultData {
  cung_menh: {
    cung: string;
    nhom: string;
    ngu_hanh_cung: string;
    ngu_hanh_nap_am: string;
    can_chi: string;
    lunar_year: number;
    lac_thu_so: number;
    notes: string[];
  };
  bat_trach: {
    quality: string;
    direction: string;
    description: string;
    is_good: boolean;
  }[];
  house_match: {
    house_direction: string;
    matched_quality: string;
    is_good: boolean;
    advice: string;
  } | null;
  good_days: Record<string, {
    solar_date: string;
    lunar_date: string;
    can_chi_day: string;
    hoang_dao_than: string;
    is_hoang_dao: boolean;
    score: number;
    reasons_good: string[];
    reasons_bad: string[];
    is_recommended: boolean;
  }[]>;
  disclaimer: string;
}

export interface Report {
  id: string;
  tenant_id: string;
  customer_id: string;
  land_title_id: string;
  status: string;
  purposes: Purpose[];
  result_data: ReportResultData | Record<string, never>;
  pdf_url: string | null;
  credit_cost: string;
  created_at: string;
  error_message: string | null;
}
