"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";

import { api, setToken, type TokenResponse } from "@/lib/api";

export default function RegisterPage() {
  const router = useRouter();
  const [form, setForm] = useState({
    tenant_name: "",
    full_name: "",
    email: "",
    phone: "",
    password: "",
  });
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const { data } = await api.post<TokenResponse>("/v1/auth/register", form);
      setToken(data.access_token, data.refresh_token);
      router.push("/dashboard");
    } catch (err: unknown) {
      // @ts-expect-error axios
      setError(err?.response?.data?.detail ?? "Đăng ký thất bại");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="min-h-screen bg-stone-50 grid place-items-center px-4 py-8">
      <form onSubmit={onSubmit} className="card w-full max-w-md space-y-4">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-primary-700">Đăng ký sàn mới</h1>
          <p className="mt-1 text-sm text-stone-500">5 tín dụng dùng thử miễn phí</p>
        </div>

        <Input label="Tên sàn môi giới" value={form.tenant_name}
          onChange={(v) => setForm({ ...form, tenant_name: v })} />
        <Input label="Họ tên chủ tài khoản" value={form.full_name}
          onChange={(v) => setForm({ ...form, full_name: v })} />
        <Input label="Email" type="email" value={form.email}
          onChange={(v) => setForm({ ...form, email: v })} />
        <Input label="SĐT (tùy chọn)" value={form.phone}
          onChange={(v) => setForm({ ...form, phone: v })}
          required={false} placeholder="0901234567" />
        <Input label="Mật khẩu (≥ 8 ký tự)" type="password" minLength={8}
          value={form.password}
          onChange={(v) => setForm({ ...form, password: v })} />

        {error && (
          <div className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">
            {error}
          </div>
        )}

        <button type="submit" className="btn-primary w-full" disabled={loading}>
          {loading ? "Đang tạo…" : "Tạo tài khoản"}
        </button>

        <div className="text-center text-sm text-stone-500">
          Đã có tài khoản?{" "}
          <Link href="/login" className="text-primary-700 hover:underline">
            Đăng nhập
          </Link>
        </div>
      </form>
    </main>
  );
}

function Input({
  label, value, onChange, type = "text", required = true, minLength, placeholder,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  type?: string;
  required?: boolean;
  minLength?: number;
  placeholder?: string;
}) {
  return (
    <div>
      <label className="label">{label}</label>
      <input
        type={type}
        required={required}
        minLength={minLength}
        placeholder={placeholder}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="input"
      />
    </div>
  );
}
