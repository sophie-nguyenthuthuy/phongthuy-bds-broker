"use client";

import { useEffect, useState } from "react";
import Link from "next/link";

import { api, type Report, type ReportResultData } from "@/lib/api";

const PURPOSE_LABEL: Record<string, string> = {
  dong_tho: "Động thổ",
  dat_mong: "Đặt móng",
  nhap_trach: "Nhập trạch",
  khai_truong: "Khai trương",
};

export default function ReportDetailPage({
  params,
}: {
  params: { id: string };
}) {
  const [report, setReport] = useState<Report | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api
      .get<Report>(`/v1/reports/${params.id}`)
      .then((r) => setReport(r.data))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [params.id]);

  if (loading) {
    return (
      <main className="min-h-screen grid place-items-center text-stone-500">
        Đang tải…
      </main>
    );
  }

  if (!report) {
    return (
      <main className="min-h-screen grid place-items-center text-stone-500">
        Không tìm thấy báo cáo.
      </main>
    );
  }

  const result = report.result_data as ReportResultData;
  const hasResult = "cung_menh" in result;

  return (
    <main className="min-h-screen bg-stone-50 px-6 py-8">
      <div className="mx-auto max-w-4xl">
        <Link href="/dashboard" className="text-sm text-stone-500 hover:underline">
          ← Dashboard
        </Link>

        <div className="mt-4 flex items-start justify-between">
          <div>
            <h1 className="text-2xl font-bold">Báo cáo phong thủy</h1>
            <p className="text-sm text-stone-500">Mã: {report.id}</p>
          </div>
          {report.pdf_url && (
            <a
              href={`${process.env.NEXT_PUBLIC_API_URL ?? ""}/v1/reports/${report.id}/pdf`}
              target="_blank"
              rel="noreferrer"
              className="btn-primary"
            >
              Tải PDF
            </a>
          )}
        </div>

        {!hasResult ? (
          <div className="card mt-6 text-stone-500">
            Trạng thái: <strong>{report.status}</strong>
            {report.error_message && (
              <div className="mt-2 text-red-700">{report.error_message}</div>
            )}
          </div>
        ) : (
          <>
            <Section title="Cung mệnh">
              <Kv k="Cung" v={result.cung_menh.cung} highlight />
              <Kv k="Nhóm" v={result.cung_menh.nhom} />
              <Kv k="Ngũ hành cung" v={result.cung_menh.ngu_hanh_cung} />
              <Kv k="Năm âm lịch" v={`${result.cung_menh.lunar_year} (${result.cung_menh.can_chi})`} />
              <Kv k="Nạp âm" v={result.cung_menh.ngu_hanh_nap_am} />
            </Section>

            {result.house_match && (
              <Section title="Hợp tuổi với hướng nhà">
                <div
                  className={`rounded-md border-2 p-4 ${
                    result.house_match.is_good
                      ? "border-green-300 bg-green-50"
                      : "border-red-300 bg-red-50"
                  }`}
                >
                  <div className="text-lg font-semibold">
                    Hướng {result.house_match.house_direction} →{" "}
                    {result.house_match.matched_quality}{" "}
                    {result.house_match.is_good ? "✓ TỐT" : "✗ XẤU"}
                  </div>
                  <p className="mt-2 text-sm">{result.house_match.advice}</p>
                </div>
              </Section>
            )}

            <Section title="8 hướng theo bát trạch">
              <table className="w-full text-sm">
                <thead className="bg-stone-100 text-left">
                  <tr>
                    <th className="px-3 py-2">Sao</th>
                    <th className="px-3 py-2">Hướng</th>
                    <th className="px-3 py-2">Đánh giá</th>
                  </tr>
                </thead>
                <tbody>
                  {result.bat_trach.map((d) => (
                    <tr
                      key={d.quality}
                      className={`border-b ${d.is_good ? "bg-green-50" : "bg-red-50"}`}
                    >
                      <td className="px-3 py-2 font-medium">{d.quality}</td>
                      <td className="px-3 py-2">{d.direction}</td>
                      <td className="px-3 py-2">
                        {d.is_good ? "Tốt" : "Xấu"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </Section>

            {Object.entries(result.good_days).map(([purpose, days]) => (
              <Section
                key={purpose}
                title={`Ngày tốt — ${PURPOSE_LABEL[purpose] ?? purpose}`}
              >
                {days.length === 0 ? (
                  <p className="text-stone-500">
                    Không có ngày tốt phù hợp — mở rộng khoảng thời gian.
                  </p>
                ) : (
                  <ul className="space-y-2">
                    {days.map((d) => (
                      <li
                        key={d.solar_date}
                        className="rounded-md border-l-4 border-primary-700 bg-white px-4 py-3 shadow-sm"
                      >
                        <div className="flex items-center gap-2">
                          <span className="text-lg font-semibold text-primary-700">
                            {d.solar_date}
                          </span>
                          <span className="rounded bg-stone-100 px-2 py-0.5 text-xs">
                            Âm: {d.lunar_date}
                          </span>
                          <span className="rounded bg-stone-100 px-2 py-0.5 text-xs">
                            {d.can_chi_day}
                          </span>
                          <span className="rounded bg-stone-100 px-2 py-0.5 text-xs">
                            {d.hoang_dao_than}
                          </span>
                        </div>
                        {d.reasons_good.length > 0 && (
                          <div className="mt-1 text-sm text-green-700">
                            ✓ {d.reasons_good.join("; ")}
                          </div>
                        )}
                        {d.reasons_bad.length > 0 && (
                          <div className="mt-1 text-sm text-amber-700">
                            ⚠ {d.reasons_bad.join("; ")}
                          </div>
                        )}
                      </li>
                    ))}
                  </ul>
                )}
              </Section>
            ))}

            <div className="mt-6 rounded-md bg-stone-100 p-4 text-xs text-stone-500">
              {result.disclaimer}
            </div>
          </>
        )}
      </div>
    </main>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="mt-6">
      <h2 className="mb-2 text-lg font-semibold text-primary-700">{title}</h2>
      <div className="card overflow-hidden">{children}</div>
    </section>
  );
}

function Kv({ k, v, highlight }: { k: string; v: string; highlight?: boolean }) {
  return (
    <div className="flex justify-between border-b border-stone-100 py-1.5 last:border-0">
      <span className="text-sm text-stone-500">{k}</span>
      <span className={`text-sm ${highlight ? "font-semibold text-primary-700" : ""}`}>
        {v}
      </span>
    </div>
  );
}
