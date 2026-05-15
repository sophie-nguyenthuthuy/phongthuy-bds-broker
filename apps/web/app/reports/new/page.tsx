"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";

import { api, type Customer, type OcrSoDoResponse, type Report } from "@/lib/api";

type Step = "customer" | "sodo" | "direction" | "submit";

const DIRECTIONS = [
  "Bắc", "Đông Bắc", "Đông", "Đông Nam",
  "Nam", "Tây Nam", "Tây", "Tây Bắc",
];

export default function NewReportPage() {
  const router = useRouter();
  const [step, setStep] = useState<Step>("customer");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  // Step 1 — customer
  const [fullName, setFullName] = useState("");
  const [phone, setPhone] = useState("");
  const [birthDate, setBirthDate] = useState("");
  const [gender, setGender] = useState<"nam" | "nu">("nam");
  const [consent, setConsent] = useState(false);
  const [customer, setCustomer] = useState<Customer | null>(null);

  // Step 2 — OCR sổ đỏ
  const [ocrResult, setOcrResult] = useState<OcrSoDoResponse | null>(null);

  // Step 3 — direction
  const [houseDirection, setHouseDirection] = useState<string>("");

  // Step 4 — submit
  const [purposes, setPurposes] = useState<string[]>(["nhap_trach"]);

  async function submitCustomer(e: React.FormEvent) {
    e.preventDefault();
    if (!consent) {
      setError("Cần đồng thuận DLCN trước khi lưu hồ sơ khách");
      return;
    }
    setError(null);
    setLoading(true);
    try {
      const { data } = await api.post<Customer>("/v1/customers", {
        full_name: fullName,
        phone: phone || null,
        birth_date: birthDate,
        gender,
        consent_given: true,
      });
      setCustomer(data);
      setStep("sodo");
    } catch (err: unknown) {
      // @ts-expect-error axios
      setError(err?.response?.data?.detail ?? "Tạo khách thất bại");
    } finally {
      setLoading(false);
    }
  }

  async function uploadSoDo(file: File) {
    setError(null);
    setLoading(true);
    try {
      const form = new FormData();
      form.append("file", file);
      const { data } = await api.post<OcrSoDoResponse>("/v1/ocr/sodo", form, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      setOcrResult(data);
      setStep("direction");
    } catch (err: unknown) {
      // @ts-expect-error axios
      setError(err?.response?.data?.detail ?? "OCR sổ đỏ thất bại");
    } finally {
      setLoading(false);
    }
  }

  async function setDirection() {
    if (!ocrResult || !houseDirection) return;
    setError(null);
    setLoading(true);
    try {
      await api.patch(
        `/v1/ocr/sodo/${ocrResult.land_title_id}/direction`,
        { house_direction: houseDirection },
      );
      setStep("submit");
    } catch (err: unknown) {
      // @ts-expect-error axios
      setError(err?.response?.data?.detail ?? "Cập nhật hướng nhà thất bại");
    } finally {
      setLoading(false);
    }
  }

  async function submitReport() {
    if (!customer || !ocrResult) return;
    setError(null);
    setLoading(true);
    try {
      const { data } = await api.post<Report>("/v1/reports", {
        customer_id: customer.id,
        land_title_id: ocrResult.land_title_id,
        purposes,
      });
      router.push(`/reports/${data.id}` as never);
    } catch (err: unknown) {
      // @ts-expect-error axios
      setError(err?.response?.data?.detail ?? "Tạo báo cáo thất bại");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="min-h-screen bg-stone-50 px-6 py-8">
      <div className="mx-auto max-w-3xl">
        <Link href="/dashboard" className="text-sm text-stone-500 hover:underline">
          ← Quay lại
        </Link>
        <h1 className="mt-2 text-2xl font-bold">Tạo báo cáo mới</h1>

        <Stepper current={step} />

        {error && (
          <div className="my-4 rounded-md bg-red-50 px-4 py-3 text-sm text-red-700">
            {error}
          </div>
        )}

        {step === "customer" && (
          <form onSubmit={submitCustomer} className="card mt-6 space-y-4">
            <h2 className="font-semibold">Bước 1 — Hồ sơ khách</h2>
            <div>
              <label className="label">Họ tên khách</label>
              <input
                required
                className="input"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
              />
            </div>
            <div className="grid gap-4 sm:grid-cols-2">
              <div>
                <label className="label">SĐT (tùy chọn)</label>
                <input
                  className="input"
                  value={phone}
                  onChange={(e) => setPhone(e.target.value)}
                  placeholder="0901234567"
                />
              </div>
              <div>
                <label className="label">Ngày sinh</label>
                <input
                  type="date"
                  required
                  className="input"
                  value={birthDate}
                  onChange={(e) => setBirthDate(e.target.value)}
                />
              </div>
            </div>
            <div>
              <label className="label">Giới tính</label>
              <div className="flex gap-4">
                <label className="flex items-center gap-2">
                  <input
                    type="radio"
                    checked={gender === "nam"}
                    onChange={() => setGender("nam")}
                  />
                  Nam
                </label>
                <label className="flex items-center gap-2">
                  <input
                    type="radio"
                    checked={gender === "nu"}
                    onChange={() => setGender("nu")}
                  />
                  Nữ
                </label>
              </div>
            </div>

            <div className="rounded-md bg-amber-50 p-3 text-sm text-amber-900">
              <label className="flex gap-2">
                <input
                  type="checkbox"
                  className="mt-1"
                  checked={consent}
                  onChange={(e) => setConsent(e.target.checked)}
                />
                <span>
                  Tôi xác nhận khách hàng đã <strong>đồng thuận</strong> cho phép
                  xử lý dữ liệu cá nhân (ngày sinh, SĐT) theo
                  NĐ 13/2023/NĐ-CP. Hồ sơ sẽ tự xóa sau 90 ngày.
                </span>
              </label>
            </div>

            <button type="submit" className="btn-primary" disabled={loading}>
              {loading ? "Đang lưu…" : "Tiếp tục →"}
            </button>
          </form>
        )}

        {step === "sodo" && (
          <div className="card mt-6 space-y-4">
            <h2 className="font-semibold">Bước 2 — Tải sổ đỏ</h2>
            <p className="text-sm text-stone-500">
              Chấp nhận JPG, PNG, PDF (≤ 10MB). Hỗ trợ cả mẫu cũ
              (TT 23/2014) và mẫu mới (TT 10/2024).
            </p>
            <input
              type="file"
              accept="image/jpeg,image/png,image/webp,application/pdf"
              disabled={loading}
              onChange={(e) => {
                const f = e.target.files?.[0];
                if (f) void uploadSoDo(f);
              }}
            />
            {loading && (
              <div className="text-sm text-stone-500">Đang OCR sổ đỏ…</div>
            )}
          </div>
        )}

        {step === "direction" && ocrResult && (
          <div className="card mt-6 space-y-4">
            <h2 className="font-semibold">Bước 3 — Chốt hướng nhà</h2>
            <div className="rounded-md bg-stone-50 p-3 text-sm">
              <div>
                <strong>Địa chỉ:</strong>{" "}
                {ocrResult.extracted.dia_chi ?? "—"}
              </div>
              <div>
                <strong>Diện tích:</strong>{" "}
                {ocrResult.extracted.dien_tich_m2 ?? "—"} m²
              </div>
              <div>
                <strong>Thửa/tờ bản đồ:</strong>{" "}
                {ocrResult.extracted.thua_dat_so}/{ocrResult.extracted.to_ban_do_so}
              </div>
              <div className="mt-1 text-xs text-stone-500">
                Confidence: {(ocrResult.confidence * 100).toFixed(0)}%
                {ocrResult.needs_review && " (cần xác nhận thủ công)"}
              </div>
            </div>
            <div>
              <label className="label">
                Hướng cửa chính nhà (đo bằng la bàn / Google Maps)
              </label>
              <select
                className="input"
                value={houseDirection}
                onChange={(e) => setHouseDirection(e.target.value)}
              >
                <option value="">— Chọn hướng —</option>
                {DIRECTIONS.map((d) => (
                  <option key={d} value={d}>{d}</option>
                ))}
              </select>
            </div>
            <button
              onClick={setDirection}
              className="btn-primary"
              disabled={loading || !houseDirection}
            >
              Tiếp tục →
            </button>
          </div>
        )}

        {step === "submit" && (
          <div className="card mt-6 space-y-4">
            <h2 className="font-semibold">Bước 4 — Mục đích & tạo báo cáo</h2>
            <div>
              <label className="label">Chọn các mục đích cần ngày tốt</label>
              <div className="space-y-2">
                {[
                  ["nhap_trach", "Nhập trạch (về nhà mới)"],
                  ["dong_tho", "Động thổ (khởi công xây)"],
                  ["dat_mong", "Đặt móng"],
                  ["khai_truong", "Khai trương cửa hàng"],
                ].map(([value, label]) => (
                  <label key={value} className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      checked={purposes.includes(value)}
                      onChange={(e) => {
                        if (e.target.checked) {
                          setPurposes([...purposes, value]);
                        } else {
                          setPurposes(purposes.filter((p) => p !== value));
                        }
                      }}
                    />
                    {label}
                  </label>
                ))}
              </div>
            </div>
            <div className="rounded-md bg-primary-50 p-3 text-sm text-primary-800">
              Tạo báo cáo này sẽ trừ <strong>1 tín dụng</strong> khỏi sàn của bạn.
            </div>
            <button
              onClick={submitReport}
              className="btn-primary"
              disabled={loading || purposes.length === 0}
            >
              {loading ? "Đang tạo báo cáo…" : "Tạo báo cáo"}
            </button>
          </div>
        )}
      </div>
    </main>
  );
}

function Stepper({ current }: { current: Step }) {
  const steps: { key: Step; label: string }[] = [
    { key: "customer", label: "Khách" },
    { key: "sodo", label: "Sổ đỏ" },
    { key: "direction", label: "Hướng" },
    { key: "submit", label: "Tạo" },
  ];
  const currentIdx = steps.findIndex((s) => s.key === current);
  return (
    <ol className="mt-6 flex gap-2 text-sm">
      {steps.map((s, i) => (
        <li
          key={s.key}
          className={`flex-1 rounded-md px-3 py-2 text-center ${
            i < currentIdx
              ? "bg-primary-100 text-primary-700"
              : i === currentIdx
                ? "bg-primary-700 text-white"
                : "bg-stone-100 text-stone-500"
          }`}
        >
          {i + 1}. {s.label}
        </li>
      ))}
    </ol>
  );
}
