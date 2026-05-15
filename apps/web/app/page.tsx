import Link from "next/link";

export default function Home() {
  return (
    <main className="min-h-screen bg-gradient-to-br from-accent-50 to-white">
      <nav className="border-b border-accent-100 bg-white/80 backdrop-blur">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
          <div className="text-xl font-bold text-primary-700">
            Phong Thủy BĐS
          </div>
          <div className="flex gap-2">
            <Link href="/login" className="btn-secondary">
              Đăng nhập
            </Link>
            <Link href="/register" className="btn-primary">
              Dùng thử
            </Link>
          </div>
        </div>
      </nav>

      <section className="mx-auto max-w-5xl px-6 py-20 text-center">
        <h1 className="text-5xl font-bold leading-tight text-stone-900">
          Cây búa <span className="text-primary-700">chốt deal</span>
          <br />
          cho môi giới BĐS Việt Nam
        </h1>
        <p className="mx-auto mt-6 max-w-2xl text-lg text-stone-600">
          Nhập sổ đỏ + ngày sinh khách → trong 30 giây có ngay báo cáo PDF
          <strong> hợp tuổi, hướng nhà, ngày tốt động thổ / nhập trạch</strong>.
          Hết thời chép tay lịch giấy.
        </p>
        <div className="mt-10 flex justify-center gap-3">
          <Link href="/register" className="btn-primary text-base px-6 py-3">
            Tạo báo cáo đầu tiên (miễn phí 5 tín dụng)
          </Link>
          <Link href="#how" className="btn-secondary text-base px-6 py-3">
            Cách dùng
          </Link>
        </div>

        <div id="how" className="mt-24 grid gap-6 md:grid-cols-3 text-left">
          <div className="card">
            <div className="text-2xl">①</div>
            <h3 className="mt-2 font-semibold">Upload sổ đỏ</h3>
            <p className="mt-1 text-sm text-stone-600">
              Chụp ảnh hoặc tải PDF. Hệ thống nhận biết mẫu sổ TT 23/2014
              (cũ) và TT 10/2024 (mới), trích xuất địa chỉ, diện tích, mục
              đích sử dụng, người đứng tên.
            </p>
          </div>
          <div className="card">
            <div className="text-2xl">②</div>
            <h3 className="mt-2 font-semibold">Nhập ngày sinh khách</h3>
            <p className="mt-1 text-sm text-stone-600">
              Chỉ cần năm sinh + giới tính (có đồng thuận xử lý DLCN theo NĐ
              13/2023/NĐ-CP). Hệ thống tự tính cung mệnh, nhóm Đông/Tây tứ
              mệnh, ngũ hành nạp âm.
            </p>
          </div>
          <div className="card">
            <div className="text-2xl">③</div>
            <h3 className="mt-2 font-semibold">Tải báo cáo PDF</h3>
            <p className="mt-1 text-sm text-stone-600">
              PDF gồm bảng 8 hướng bát trạch, đánh giá hợp tuổi với hướng cụ
              thể của căn hộ, và top 5 ngày tốt động thổ/nhập trạch trong 90
              ngày tới — gửi thẳng khách.
            </p>
          </div>
        </div>
      </section>

      <footer className="border-t border-stone-200 bg-white">
        <div className="mx-auto max-w-6xl px-6 py-8 text-sm text-stone-500">
          © 2026 Phong Thủy BĐS · Tuân thủ NĐ 13/2023/NĐ-CP và Luật Đất đai
          2024. Báo cáo phong thủy mang tính tham khảo văn hóa, không thay thế
          tư vấn pháp lý hay đầu tư.
        </div>
      </footer>
    </main>
  );
}
