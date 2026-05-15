"use client";

import { useEffect, useState } from "react";
import Link from "next/link";

import { api, clearToken, type Report, type User } from "@/lib/api";
import { formatDateVN, formatVnd } from "@/lib/utils";

export default function DashboardPage() {
  const [me, setMe] = useState<User | null>(null);
  const [reports, setReports] = useState<Report[]>([]);
  const [balance, setBalance] = useState<string>("—");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      api.get<User>("/v1/auth/me"),
      api.get<Report[]>("/v1/reports"),
      api.get<{ credit_balance: string }>("/v1/billing/balance"),
    ])
      .then(([m, r, b]) => {
        setMe(m.data);
        setReports(r.data);
        setBalance(b.data.credit_balance);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  function logout() {
    clearToken();
    window.location.href = "/login";
  }

  return (
    <main className="min-h-screen bg-stone-50">
      <header className="border-b border-stone-200 bg-white">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
          <div className="flex items-center gap-6">
            <Link href="/dashboard" className="text-lg font-bold text-primary-700">
              Phong Thủy BĐS
            </Link>
            <nav className="flex gap-4 text-sm">
              <Link href="/dashboard" className="text-primary-700">Báo cáo</Link>
              <Link href="/reports/new" className="text-stone-600 hover:text-primary-700">
                Tạo mới
              </Link>
            </nav>
          </div>
          <div className="flex items-center gap-4 text-sm">
            <span className="text-stone-500">
              Tín dụng: <strong className="text-primary-700">{balance}</strong>
            </span>
            <span className="text-stone-700">{me?.full_name}</span>
            <button onClick={logout} className="text-stone-500 hover:underline">
              Đăng xuất
            </button>
          </div>
        </div>
      </header>

      <section className="mx-auto max-w-6xl px-6 py-8">
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-bold">Báo cáo gần đây</h1>
          <Link href="/reports/new" className="btn-primary">
            + Tạo báo cáo mới
          </Link>
        </div>

        <div className="mt-6 overflow-hidden rounded-lg border border-stone-200 bg-white">
          {loading ? (
            <div className="p-8 text-center text-stone-500">Đang tải…</div>
          ) : reports.length === 0 ? (
            <div className="p-12 text-center">
              <p className="text-stone-500">Chưa có báo cáo nào.</p>
              <Link href="/reports/new" className="btn-primary mt-4 inline-flex">
                Tạo báo cáo đầu tiên
              </Link>
            </div>
          ) : (
            <table className="w-full text-sm">
              <thead className="border-b border-stone-200 bg-stone-50 text-left">
                <tr>
                  <th className="px-4 py-3">Ngày tạo</th>
                  <th className="px-4 py-3">Trạng thái</th>
                  <th className="px-4 py-3">Mục đích</th>
                  <th className="px-4 py-3">Tín dụng</th>
                  <th className="px-4 py-3 text-right">Hành động</th>
                </tr>
              </thead>
              <tbody>
                {reports.map((r) => (
                  <tr key={r.id} className="border-b border-stone-100">
                    <td className="px-4 py-3">{formatDateVN(r.created_at)}</td>
                    <td className="px-4 py-3">
                      <StatusBadge status={r.status} />
                    </td>
                    <td className="px-4 py-3 text-stone-600">
                      {r.purposes.join(", ")}
                    </td>
                    <td className="px-4 py-3">{formatVnd(r.credit_cost)}</td>
                    <td className="px-4 py-3 text-right">
                      <Link
                        href={{ pathname: `/reports/${r.id}` } as never}
                        className="text-primary-700 hover:underline"
                      >
                        Xem
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </section>
    </main>
  );
}

function StatusBadge({ status }: { status: string }) {
  const map: Record<string, string> = {
    ready: "bg-green-100 text-green-700",
    pending: "bg-amber-100 text-amber-700",
    computing: "bg-amber-100 text-amber-700",
    failed: "bg-red-100 text-red-700",
  };
  const labelMap: Record<string, string> = {
    ready: "Hoàn thành",
    pending: "Đang xử lý",
    computing: "Đang tính",
    failed: "Lỗi",
  };
  return (
    <span
      className={`rounded-full px-2 py-0.5 text-xs ${
        map[status] ?? "bg-stone-100 text-stone-700"
      }`}
    >
      {labelMap[status] ?? status}
    </span>
  );
}
