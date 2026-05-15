"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";

import { api, setToken, type TokenResponse } from "@/lib/api";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const { data } = await api.post<TokenResponse>("/v1/auth/login", {
        email,
        password,
      });
      setToken(data.access_token, data.refresh_token);
      router.push("/dashboard");
    } catch (err: unknown) {
      const msg =
        // @ts-expect-error axios error shape
        err?.response?.data?.detail ?? "Đăng nhập thất bại — kiểm tra lại email/mật khẩu";
      setError(String(msg));
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="min-h-screen bg-stone-50 grid place-items-center px-4">
      <form onSubmit={onSubmit} className="card w-full max-w-md space-y-4">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-primary-700">Đăng nhập</h1>
          <p className="mt-1 text-sm text-stone-500">
            Tài khoản môi giới Phong Thủy BĐS
          </p>
        </div>

        <div>
          <label className="label" htmlFor="email">Email</label>
          <input
            id="email"
            type="email"
            required
            autoFocus
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="input"
            placeholder="moigioi@example.com"
          />
        </div>

        <div>
          <label className="label" htmlFor="password">Mật khẩu</label>
          <input
            id="password"
            type="password"
            required
            minLength={8}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="input"
          />
        </div>

        {error && (
          <div className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">
            {error}
          </div>
        )}

        <button type="submit" className="btn-primary w-full" disabled={loading}>
          {loading ? "Đang đăng nhập…" : "Đăng nhập"}
        </button>

        <div className="text-center text-sm text-stone-500">
          Chưa có tài khoản?{" "}
          <Link href="/register" className="text-primary-700 hover:underline">
            Đăng ký sàn mới
          </Link>
        </div>
      </form>
    </main>
  );
}
