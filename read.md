# Cập nhật bộ lọc LI theo giao diện Aging

Áp dụng cho đúng project LI\_APP\_Without\_CLI(1).zip đã gửi.

## Cài đặt

1. Đóng ứng dụng LI.
2. Giải nén gói này, chép các thư mục controllers, repositories, services, ui, workers và tests vào thư mục LI\_APP đang dùng. Đồng ý ghi đè các file trùng tên; giữ các file khác.
3. Chép read.md và change log.txt vào gốc project nếu muốn lưu hướng dẫn.
4. Chạy main.py như trước. Không cần tạo lại hoặc xóa database, không thêm thư viện.

## File chỉnh sửa

* controllers/prime\_controller.py: điều phối nạp lựa chọn bằng worker sau khởi tạo database và sau PRIME/CUM; dùng cùng vòng đời worker để không chồng tác vụ và đóng cửa sổ an toàn.
* ui/pages/prime\_page.py: gắn bộ lọc Aging vào trang LI, nối hai nút import hiện có, lưu và phát điều kiện SEARCH. Có vùng cuộn khi cửa sổ nhỏ.
* tests/test\_gui.py: cập nhật kiểm thử giao diện từ hai nút sang bộ lọc mới.

## File thêm

* ui/widgets/**init**.py
* ui/widgets/filter\_panel.py: giao diện và hành vi bộ lọc lấy từ Aging, đổi Chamber thành SLOT, hiển thị cả hai nút import.
* repositories/filter\_option\_repository.py: truy vấn các giá trị phân biệt, không ghi dữ liệu.
* workers/filter\_option\_worker.py: nạp lựa chọn ngoài luồng giao diện.
* services/scrap\_code\_config.py: danh sách mã ưu tiên giống Aging.
* tests/test\_filters.py: kiểm thử nguồn lựa chọn và thao tác bộ lọc.

## Quy tắc lựa chọn

|Trường|Nguồn / hành vi|
|-|-|
|From, To|Mặc định hôm nay, lịch popup, hiển thị yyyy-MM-dd; tự điều chỉnh để From không vượt To; điều kiện xuất ra yyyyMMdd.|
|EQP|DISTINCT EQP trong prime\_data; chưa chọn nghĩa là không giới hạn máy.|
|SLOT|DISTINCT SLOT trong prime\_data, sắp theo số; chưa chọn nghĩa là không giới hạn slot. Không sinh cứng danh sách 1–48.|
|Tier|TIER khác NULL từ prime\_data và cum\_data, giống Aging; checkbox và Select All, mặc định chọn tất cả.|
|Model|MODEL từ prime\_data, giống Aging; checkbox và Select All, mặc định chọn tất cả.|
|Scrap Code|Mã 4 chữ số từ prime\_data.SCRAPCODE và cum\_scrap\_detail.scrap\_code; checkbox, Select All, mặc định chưa chọn. Mã 3212, 3308, 3329, 3346, 3382 được ưu tiên và tô đỏ khi có trong dữ liệu.|

Danh sách là toàn bộ lựa chọn hiện có, không phụ thuộc khoảng ngày hoặc EQP đang chọn, giống bộ lọc Aging. Sau import, danh sách được đọc lại và lựa chọn trở về mặc định giống Aging. Ngày From/To được giữ nguyên.

Tier NULL không xuất hiện trong danh sách, giống Aging. Nếu PRIME chưa được ghép Tier từ CUM, danh sách Tier có thể trống. Bản này không thay đổi cách tính Tier.

## Phạm vi SEARCH và bước phát triển tiếp

Project LI đầu vào mới có chức năng import, chưa có bảng Summary/Yield Slot hoặc biểu đồ. Bản cập nhật này hoàn thành giao diện, nạp lựa chọn thật từ database, kiểm soát lựa chọn và phát điều kiện khi bấm SEARCH; chưa tạo các màn hình phân tích hoặc truy vấn kết quả cho chúng.

SEARCH lưu FilterCriteria tại prime\_page.current\_criteria và phát prime\_page.filter\_applied(criteria). Các trường là date\_from, date\_to, selected\_date=None, eqp, slot, tiers, models, scrap\_codes. Dòng dưới bộ lọc xác nhận điều kiện vừa chọn; không phải thống kê kết quả trong database.

Giữ ý nghĩa Scrap Code của Aging: chọn chuỗi lỗi cho biểu đồ, không dùng để loại các dòng PASS khỏi mẫu số tính Yield. Khi nối màn hình phân tích ở bước sau, áp dụng From/To/EQP/SLOT/Tier/Model vào truy vấn; Tier hoặc Model bỏ chọn hết phải cho kết quả rỗng như Aging. Không nối vào dữ liệu alarm hoặc thay đổi thuật toán Yield trong bản này.

## Nạp dữ liệu và hiệu năng

Dùng một connection riêng và một read transaction trong worker để lấy snapshot nhất quán. Chỉ đọc danh sách lúc khởi tạo xong và sau import; không truy vấn database khi tick từng checkbox. Bản này dùng DISTINCT trực tiếp, chưa bổ sung bảng cache/migration như Aging. Database lớn có thể mất thời gian nạp nhưng UI không bị chặn bởi truy vấn.

## Kiểm tra

Đã chạy 7 kiểm thử bằng PyQt5 ở chế độ offscreen trên Linux: nguồn lựa chọn PRIME/CUM, lọc mã lỗi đúng 4 chữ số, không sửa dữ liệu khi đọc, ngày From/To, Select All và điều kiện SEARCH, startup, import/reimport, hủy lựa chọn, đóng cửa sổ. Đã mở và kiểm tra ảnh giao diện 1366×768. Chưa chạy trực tiếp trên Windows hoặc database sản xuất của bạn.

Chạy lại: python -m unittest discover -s tests -v



\---

# \[2026-09-13 22:24:28] CẬP NHẬT — CUM YIELD LI SUMMARY

Thời gian ghi: giờ Việt Nam (UTC+7). Áp dụng cho LI\_APP(6).zip.
Nội dung phía trên là lịch sử được giữ nguyên. Phần cập nhật này thay thế mô tả cũ rằng SEARCH chưa có bảng/biểu đồ; riêng CUM Summary áp dụng phạm vi lọc dưới đây.

## \[2026-09-13 22:24:28] Cài đặt

1. Đóng LI App.
2. Giải nén gói LI\_APP\_Summary\_patch.zip và chép toàn bộ nội dung bên trong vào thư mục LI\_APP có main.py; đồng ý ghi đè các file trùng tên.
3. Trong môi trường Python đang chạy LI, thực hiện `python -m pip install -r requirements.txt` để bổ sung Matplotlib.
4. Chạy `python main.py`, chọn From/To, Tier và Model rồi bấm SEARCH.
5. Không xóa hoặc tạo lại database. Gói chỉ chứa file thêm/sửa, không chứa database hay toàn bộ project.

File nhật ký mới có tên `changelog.txt` theo yêu cầu lần này. Toàn bộ lịch sử trong `change log.txt` cũ đã được chép nguyên vẹn vào đầu file này rồi nối thêm lần cập nhật mới. Từ lần này tiếp tục nối vào `changelog.txt`; file `change log.txt` cũ có thể lưu làm bản lịch sử, không cần dùng để ghi tiếp. Không tự đặt ngày giờ cho các mục cũ vì file nguồn không có thông tin đó.

## \[2026-09-13 22:24:28] Giao diện và tính dữ liệu

* Tab Summary có tiêu đề Cum Yield LI Summary, bảng bên trái và biểu đồ bên phải.
* Bảng gồm EQPID, In Qty, Out Qty, Fail Qty, Fail PPM, Yield; dòng Total in đậm nền xám, tiêu đề cột xanh nhạt như Aging.
* Nguồn là cum\_data, GROUP BY EQPID, ORDER BY EQPID.
* In Qty = SUM(INQTY); Out Qty = SUM(OUTQTY); Fail Qty = In Qty − Out Qty.
* Fail PPM = Fail Qty / In Qty × 1.000.000; Yield = Out Qty / In Qty × 100.
* Không dùng cột FAILQTY/YIELD đã lưu để tính Summary. Total tính lại tỷ lệ từ tổng In/Out, không lấy trung bình tỷ lệ từng máy.
* In Qty <= 0: bảng hiện dấu — cho PPM/Yield. Biểu đồ giữ cách xử lý Aging: giá trị không có tỷ lệ được vẽ bằng 0.
* Bảng hiển thị PPM không có số lẻ, Yield hai chữ số thập phân; biểu đồ dùng số liệu chưa làm tròn.
* Không có dữ liệu: bảng chỉ còn Total với Qty = 0, tỷ lệ = —; biểu đồ hiện thông báo rỗng, xóa cột/đường/chú thích cũ.
* Biểu đồ giữ mã vẽ của Aging: cột Fail PPM vàng, đường Yield xanh, hai trục Y, nhãn Yield, lưới và chú thích. Đổi tiêu đề Aging thành LI. Giữ kích thước 1300 × 536 của Aging; vùng Summary có thanh cuộn cho màn hình nhỏ.

## \[2026-09-13 22:24:28] Quy tắc bộ lọc

|Trường|Tác động tới CUM Summary|
|-|-|
|From, To|DATE BETWEEN From AND To, gồm cả hai ngày đầu/cuối.|
|Tier|Chỉ lấy các TIER được chọn. Bỏ chọn hết: dữ liệu rỗng.|
|Model|Chỉ lấy các MODEL được chọn. Bỏ chọn hết: dữ liệu rỗng.|
|EQP, SLOT|Không giới hạn khối Summary toàn bộ máy, theo cách triển khai Aging.|
|Scrap Code|Không lọc Summary và không thay đổi mẫu số Yield, theo Aging.|

Nguồn lựa chọn Model vẫn là prime\_data như bộ lọc hiện tại/Aging. Model chỉ có trong CUM mà chưa có trong PRIME chưa xuất hiện trong danh sách chọn; không thay đổi nguồn lựa chọn ở lần này.

## \[2026-09-13 22:24:28] Tổ chức và hiệu năng

Luồng: SEARCH → PrimeController → SummaryWorker → SummaryRepository → cum\_data → SummaryPage/CumEqpChart.
Repository chỉ đọc dữ liệu, tính tỷ lệ theo Aging. Worker mở/đóng kết nối trong luồng của nó. Controller dùng chung cơ chế điều phối tác vụ hiện có để không chạy chồng import và Summary; UI chỉ dựng bảng/biểu đồ trên luồng chính.

Chỉ truy vấn sau SEARCH; Matplotlib được nạp và chart được tạo ở SEARCH đầu tiên. Khi From/To/Tier/Model không đổi, giữ kết quả đã hiển thị, không query/vẽ lại. Đổi riêng EQP/SLOT/Scrap Code không làm mất cache Summary. Sau luồng import/khởi tạo và nạp lại bộ lọc, xóa cache và kết quả cũ; bấm SEARCH để lấy dữ liệu mới. Khi lỗi đọc/vẽ, hiện thông báo và cho phép thử lại. Khi đóng cửa sổ đang đọc, đợi worker kết thúc trước khi đóng.

## \[2026-09-13 22:24:28] Danh sách file

File sửa:

* controllers/prime\_controller.py: điều phối SEARCH, cache, lỗi và vòng đời worker.
* ui/pages/prime\_page.py: bổ sung QTabWidget và trang Summary.
* requirements.txt: thêm Matplotlib.
* read.md: giữ nội dung cũ và nối hướng dẫn lần này.

File thêm:

* domain/summary.py: kiểu dữ liệu dòng/tổng Summary.
* repositories/data\_filter.py: quy tắc Tier/Model lấy từ Aging.
* repositories/summary\_repository.py: SQL tổng hợp và công thức.
* workers/summary\_worker.py: đọc Summary bằng worker.
* ui/pages/summary\_page.py: bảng và vùng biểu đồ.
* ui/charts/**init**.py, ui/charts/cum\_eqp\_chart.py: biểu đồ lấy từ Aging.
* tests/test\_summary.py: kiểm thử tính toán và luồng Summary.
* changelog.txt: toàn bộ lịch sử cũ và mục mới có ngày giờ.

## \[2026-09-13 22:24:28] Kiểm tra

Đã chạy 9 kiểm thử thành công: 7 kiểm thử hiện có và 2 kiểm thử Summary. Kiểm tra cộng gộp nhiều ngày, Total có trọng số, bỏ qua FAILQTY/YIELD lưu sẵn, lọc ngày/Tier/Model, In = 0, lựa chọn rỗng, số liệu bảng/biểu đồ, cache, làm mới sau luồng nạp bộ lọc, lỗi truy vấn và thử lại, xóa biểu đồ cũ, đóng cửa sổ khi worker chạy. Đã xem ảnh giao diện với dữ liệu giả lập ở 1920 × 900. Chưa chạy trực tiếp trên Windows hoặc dữ liệu sản xuất.

Chạy lại: `python -m unittest discover -s tests -v` tại gốc LI\_APP.



\---

# \[2026-09-13 22:48:31] SỬA BỘ LỌC MODEL BỎ SÓT CUM (UTC+7)

Nguyên nhân: danh sách Model trước đây chỉ lấy từ prime\_data, trong khi Summary truy vấn cum\_data theo các Model đã chọn. Vì vậy Select All chỉ chọn các Model đang xuất hiện trong danh sách; các Model chỉ có ở CUM bị loại khỏi kết quả. Trong dữ liệu và ảnh đã gửi, Model đang chọn khác MZWL6/MZWLR của các dòng CUM.

Thay đổi: lấy hợp danh sách MODEL của prime\_data và cum\_data bằng UNION, loại trùng và sắp xếp. Nội dung này thay thế quy tắc nguồn Model chỉ từ PRIME trong các phần lịch sử phía trên. Giữ nguyên công thức CUM Summary và quy tắc bỏ chọn hết Model thì kết quả rỗng.

Cài đặt: đóng app, giải nén LI\_Model\_Filter\_fix.zip, chép các file vào gốc LI\_Tool có main.py và đồng ý ghi đè. Mở lại app để nạp danh sách Model mới; chọn khoảng ngày chứa dữ liệu, Select All ở Tier/Model rồi bấm SEARCH. Không cần import lại dữ liệu hoặc xóa database.

File sửa: repositories/filter\_option\_repository.py, tests/test\_filters.py, read.md, changelog.txt. Chỉ file repository ảnh hưởng hành vi chạy; file test cập nhật kiểm tra nguồn lựa chọn và xác nhận CUM vẫn được thống kê khi PRIME rỗng.

Kiểm tra: 9 kiểm thử thành công trên môi trường Linux/offscreen; có kiểm tra Model riêng của CUM xuất hiện, được chọn mặc định và trả về Summary. Chưa chạy trực tiếp trên Windows hoặc database thực tế của bạn.



\---

# \[2026-09-13 22:56:57] SỬA ĐÓNG APP BẰNG MỘT LẦN CLICK (UTC+7)

Nguyên nhân: khi app rảnh, closeEvent bỏ qua sự kiện ban đầu rồi phát close\_requested. Controller gọi finish\_close ngay, nhưng finish\_close gọi self.close() trong lúc closeEvent đầu tiên vẫn đang chạy. Qt bỏ qua yêu cầu đóng lồng nhau, khiến phải bấm lần hai.

Sửa ui/main\_window.py: finish\_close đánh dấu được phép đóng và dùng QTimer.singleShot(0, self.close) để đóng ở lượt xử lý sự kiện tiếp theo. Không gọi close lồng trong closeEvent. Khi app rảnh chỉ cần bấm Close một lần; khi đang có worker, controller vẫn hủy import nếu có và đợi worker kết thúc rồi tự đóng, không cần bấm thêm.

Cài đặt: đóng ứng dụng, giải nén LI\_Close\_Once\_fix.zip, chép các file vào gốc LI\_Tool chứa main.py và đồng ý ghi đè. Chạy lại app. Không cần cài thêm thư viện hay thay đổi database.

File trong gói: ui/main\_window.py, tests/test\_gui.py, read.md, changelog.txt. Đây là bản vá tiếp theo sau bản sửa Model; không chứa lại các file của bản vá Model.

Kiểm tra: đã tái hiện lỗi trên code cũ bằng kiểm thử một lần close khi app rảnh (thất bại trước sửa); sau sửa toàn bộ 10 kiểm thử thành công, gồm một lần close khi rảnh và đóng khi worker đang chạy. Kiểm tra trên Linux/offscreen, chưa chạy trực tiếp trên Windows. Nội dung tài liệu và nhật ký các lần trước được giữ nguyên.



\---

# \[2026-09-13 23:23:59] CẬP NHẬT — TỐI ƯU INDEX VÀ LOADING DIALOG (UTC+7)

Áp dụng tiếp trên project LI\_Tool hiện tại. Không cần xóa database cũ. Khi mở app, database schema 2 đang dùng sẽ tự bổ sung các index còn thiếu bằng `CREATE INDEX IF NOT EXISTS`.

## Đánh giá index hiện tại

Các index cũ đã phù hợp cho những phần sau:

|Index cũ|Truy vấn được hỗ trợ|Đánh giá|
|-|-|-|
|`idx\\\_prime\\\_date`|Xóa/thay PRIME theo `DATE`; cập nhật PRIME theo ngày khi đồng bộ Tier|Phù hợp|
|`idx\\\_prime\\\_eqp\\\_date`|Lấy danh sách EQP; truy vấn PRIME theo EQP/ngày về sau|Phù hợp|
|`idx\\\_prime\\\_slot\\\_time`|Truy vấn PRIME theo EQP + SLOT + DATE + TIME|Phù hợp nếu truy vấn có EQP|
|`idx\\\_cum\\\_date`|Xóa/thay CUM theo ngày|Phù hợp|
|`idx\\\_cum\\\_lot\\\_date\\\_tier`|Đồng bộ `prime\\\_data.TIER` từ CUM theo `LOTID` và cửa sổ ngày|Rất cần, giữ nguyên|
|`idx\\\_cum\\\_eqp\\\_date`|Truy vấn CUM theo EQP/ngày về sau|Phù hợp|
|`idx\\\_cum\\\_scrap\\\_code`|Lấy/lọc mã scrap từ bảng chi tiết CUM|Phù hợp|

Các điểm còn thiếu:

|Truy vấn|Vấn đề cũ|Index bổ sung|
|-|-|-|
|`SELECT DISTINCT SLOT FROM prime\\\_data ORDER BY SLOT`|`idx\\\_prime\\\_slot\\\_time` bắt đầu bằng EQP nên không tối ưu cho riêng SLOT|`idx\\\_prime\\\_slot`|
|`MODEL` từ `prime\\\_data`|Chưa có index dẫn đầu bằng MODEL|`idx\\\_prime\\\_model`|
|`TIER` + `MODEL` trên PRIME|Chưa có index ghép cho bộ lọc Tier/Model|`idx\\\_prime\\\_tier\\\_model`|
|`SCRAPCODE` từ PRIME|Chưa có index riêng cho mã lỗi PRIME|`idx\\\_prime\\\_scrapcode`|
|`MODEL` từ `cum\\\_data`|Chưa có index dẫn đầu bằng MODEL|`idx\\\_cum\\\_model`|
|Summary CUM `WHERE TIER IN (...) AND MODEL IN (...) AND DATE BETWEEN ... GROUP BY EQPID`|Chỉ có `idx\\\_cum\\\_date`, chưa tận dụng tốt Tier/Model|`idx\\\_cum\\\_tier\\\_model\\\_date\\\_eqp`|

Không thêm index cho tất cả tổ hợp EQP/SLOT/Scrap Code vì hiện tại Summary chưa dùng các trường này để lọc dữ liệu. Thêm quá nhiều index sẽ làm import PRIME/CUM chậm hơn do mỗi lần ghi phải cập nhật thêm index.

## Thay đổi giao diện loading

* SEARCH dùng `LoadingDialog` giống Aging, hiển thị hộp thoại `Please Wait / Loading ...` trong khi worker Summary chạy.
* Import PRIME và Import CUM cũng dùng cùng `LoadingDialog`, thay cho `QProgressDialog` cũ.
* Bỏ chữ `(đang tải...)` trong tiêu đề `Cum Yield LI Summary`; trạng thái loading chỉ hiển thị bằng dialog.
* Vẫn chạy tác vụ bằng worker/QThread, không khóa UI bằng truy vấn trực tiếp.

## File liên quan theo từng chức năng

|Chức năng|File liên quan|Trạng thái trong lần này|
|-|-|-|
|Khởi tạo database và tối ưu index|`database/schema.py`|Sửa|
|Import PRIME|`controllers/prime\\\_controller.py`, `ui/dialogs/import\\\_dialogs.py`, `ui/widgets/loading\\\_dialog.py`, `workers/prime\\\_import\\\_worker.py`, `repositories/prime\\\_repository.py`, `services/prime\\\_import\\\_service.py`, `services/prime\\\_log\\\_reader.py`, `domain/prime.py`|Sửa controller/dialog; thêm loading dialog|
|Import CUM|`controllers/prime\\\_controller.py`, `ui/dialogs/import\\\_dialogs.py`, `ui/widgets/loading\\\_dialog.py`, `workers/cum\\\_import\\\_worker.py`, `repositories/cum\\\_repository.py`, `services/cum\\\_import\\\_service.py`, `services/cum\\\_excel\\\_reader.py`, `domain/cum.py`|Sửa controller/dialog; thêm loading dialog|
|SEARCH / CUM Summary|`controllers/prime\\\_controller.py`, `workers/summary\\\_worker.py`, `repositories/summary\\\_repository.py`, `repositories/data\\\_filter.py`, `ui/pages/summary\\\_page.py`, `ui/charts/cum\\\_eqp\\\_chart.py`, `domain/summary.py`, `ui/widgets/loading\\\_dialog.py`|Sửa controller/summary page; thêm loading dialog|
|Bộ lọc From/To/EQP/SLOT/Model/Scrap/Tier|`ui/widgets/filter\\\_panel.py`, `ui/pages/prime\\\_page.py`, `repositories/filter\\\_option\\\_repository.py`, `workers/filter\\\_option\\\_worker.py`, `services/scrap\\\_code\\\_config.py`|Không đổi logic lần này|
|Đóng app một lần click|`ui/main\\\_window.py`, `controllers/prime\\\_controller.py`|Không đổi lần này, giữ bản vá cũ|
|Kiểm thử|`tests/test\\\_filters.py`, `tests/test\\\_gui.py`, `tests/test\\\_summary.py`|Sửa `tests/test\\\_filters.py` để kiểm tra index|
|Tài liệu bàn giao|`read.md`, `changelog.txt`|Sửa|

## File sửa / thêm trong gói lần này

File sửa:

* `database/schema.py`
* `controllers/prime\\\_controller.py`
* `ui/dialogs/import\\\_dialogs.py`
* `ui/pages/summary\\\_page.py`
* `tests/test\\\_filters.py`
* `read.md`
* `changelog.txt`

File thêm:

* `ui/widgets/loading\\\_dialog.py`

## Kiểm tra

Đã chạy `python -m unittest discover -s tests -v`: 11 kiểm thử thành công. Bổ sung kiểm thử xác nhận các index mới được tạo khi khởi tạo database. Chưa chạy trực tiếp trên Windows hoặc database sản xuất của bạn.

# Cập nhật LI — Cum/Prime Yield Daily theo Scrap Code (PPM)

Áp dụng cho đúng bản nguồn `LI\\\_App\\\_v1.1-master.zip` đã gửi trong cuộc trao đổi này. Đối chiếu cách tính và hiển thị với `Aging\\\_Tool\\\_v1.0.21-master(8).zip`.

## Cài cập nhật

1. Đóng LI, giải nén gói cập nhật.
2. Chép các thư mục bên trong vào thư mục project chứa `main.py`, ghi đè các file trùng tên. Các file mới phải giữ đúng đường dẫn.
3. Chạy `python main.py`. Nếu đang dùng EXE, cần build lại từ mã nguồn đã cập nhật.
4. Giữ database LI schema 2 hiện tại. App tự bổ sung index còn thiếu trong worker khởi tạo sau khi cửa sổ hiển thị. Không xóa database, không import lại chỉ để dùng tính năng này.

Gói chỉ gồm file thêm/sửa và tài liệu, không phải toàn bộ project. Thư mục tests phục vụ kiểm thử, không cần gọi khi chạy app thông thường. Không bổ sung thư viện ứng dụng ngoài requirements đang có.

## Sử dụng

Chọn From/To, một EQP, Tier, Model; tick Scrap Code và bấm SEARCH. Cuộn xuống bên dưới Cum Yield LI Summary để xem lần lượt:

* Cum Yield LI Daily: bảng theo ngày và biểu đồ ngay dưới.
* Prime Yield LI Daily: bảng theo ngày và biểu đồ ngay dưới.

Giống Aging, Daily là thống kê **toàn máy EQP**, không phụ thuộc SLOT. CUM dùng `EQPID`, PRIME dùng `EQP` để khớp EQP đã chọn. Không chọn EQP thì xóa kết quả Daily cũ và nhắc chọn EQP; bảng Summary theo các máy vẫn hoạt động.

Bảng Daily hiển thị toàn bộ mã lỗi phát sinh theo EQP/Date/Tier/Model. Scrap Code được tick chỉ quyết định cột chồng trên biểu đồ, không lọc mẫu số hay thay đổi In/Pass/Fail/Yield. Không chọn Tier hoặc Model thì không có dữ liệu, đúng bộ lọc hiện tại. Không chọn mã lỗi hoặc mã chọn không phát sinh thì hiện thông báo thay biểu đồ, đúng Aging.

## Dữ liệu và công thức

|Nội dung|CUM|PRIME|
|-|-|-|
|Ngày thống kê|DATE trong cum\_data|DATE trong prime\_data|
|In Qty|SUM(INQTY)|SUM(QTY)|
|Pass|SUM(OUTQTY)|SUM(QTY) với RESULT='PASS'|
|Fail Qty|In Qty − Pass; không lấy cột FAILQTY có sẵn|In Qty − Pass|
|Fail PPM|Fail Qty / In Qty × 1.000.000|Cùng công thức|
|Yield|Pass / In Qty × 100|Cùng công thức|
|Số lượng từng mã lỗi|SUM(cum\_scrap\_detail.qty), join bằng cum\_data\_id|SUM(QTY), chỉ RESULT='FAIL' và SCRAPCODE không rỗng|
|PPM từng mã lỗi|Số lượng mã lỗi / In Qty của ngày × 1.000.000|Cùng công thức|

Có đủ mọi ngày từ From đến To, kể cả hai đầu. Ngày không có dữ liệu có In/Pass/Fail bằng 0; PPM/Yield để trống. Ô Scrap Code không phát sinh để trống. PPM làm tròn số nguyên khi hiển thị, Yield hai chữ số thập phân. Không lấy trung bình Yield hay cộng PPM giữa các ngày. Fail không có Scrap Code vẫn được tính vào Fail Qty/Fail PPM, vì vậy tổng các cột Scrap PPM không nhất thiết bằng Fail PPM.

## Bảng và biểu đồ

Tái sử dụng các phương thức bảng Daily và lớp `CumDailyStackedChart` từ Aging, đổi tên hiển thị thành LI: header xanh nhạt, dòng xen kẽ, cao dòng 24 px, các cột Date/In Qty/Pass/Fail Qty/Fail PPM/Yield rồi đến mã lỗi. Bảng co theo nội dung, cuộn theo trang Summary.

Biểu đồ giữ thiết kế Aging: rộng 1550 px, cột chồng từng mã lỗi trên trục Scrap PPM bên trái; đường Yield, marker và nhãn trên trục phần trăm bên phải; chú giải phía dưới. Màn hình hẹp sử dụng thanh cuộn ngang của trang.

## Index và tải thư viện

* Giữ `idx\\\_cum\\\_eqp\\\_date(EQPID, DATE)` và `idx\\\_prime\\\_eqp\\\_date(EQP, DATE)` cho tra cứu một máy theo khoảng ngày; không tạo thêm index trùng tiền tố chỉ để đổi tên.
* CUM join chi tiết tận dụng unique index sẵn có `(cum\\\_data\\\_id, scrap\\\_code)`; giữ các index phục vụ Summary, filter và import.
* Thêm `idx\\\_prime\\\_daily\\\_fail(EQP, DATE, TIER, MODEL, SCRAPCODE, QTY)` với điều kiện `RESULT='FAIL' AND COALESCE(SCRAPCODE, '') <> ''`. Đây là partial index dành cho truy vấn mã lỗi PRIME, nhỏ hơn index tương tự trên toàn bộ bản ghi khi PASS chiếm đa số.
* Kiểm tra EXPLAIN QUERY PLAN trên dữ liệu kiểm thử xác nhận truy vấn mã lỗi PRIME dùng index mới. Chưa đo tốc độ trên database sản xuất hoặc ổ mạng của bạn; thời gian tạo index lần đầu phụ thuộc lượng dữ liệu.
* SQL GROUP BY thực hiện trong worker; UI chỉ nhận kết quả đã tổng hợp. Summary và hai Daily dùng cùng một connection và read transaction để dữ liệu nhất quán trong một lần SEARCH. Kết thúc đọc thì đóng connection trước khi nạp thư viện vẽ.
* Cache theo From/To/Tier/Model/EQP. Đổi mã lỗi chỉ vẽ lại từ cache khi bấm SEARCH. Import/refresh xóa cache; đổi EQP hoặc các điều kiện dữ liệu sẽ truy vấn lại.
* Matplotlib và backend Qt được import trong SummaryWorker khi SEARCH lần đầu, sau khi cửa sổ đã mở. Canvas chỉ được tạo trên luồng UI. Loading dialog giữ đến khi đã gắn kết quả vào giao diện.
* Không preload thư viện nặng trong main hoặc constructor cửa sổ. Cơ chế import pandas/openpyxl khi cần import CUM được giữ nguyên. Đã kiểm tra trước show: matplotlib, numpy, pandas, openpyxl đều chưa nằm trong sys.modules.

## File liên quan theo chức năng

|Chức năng|File thêm|File sửa|File liên quan giữ nguyên|
|-|-|-|-|
|Tính Cum/Prime Daily|domain/daily\_summary.py; repositories/daily\_summary\_repository.py|domain/summary.py; workers/summary\_worker.py; repositories/summary\_repository.py|repositories/data\_filter.py; database/connection.py|
|Bảng Daily|ui/widgets/daily\_summary\_widget.py|ui/pages/summary\_page.py|ui/pages/prime\_page.py|
|Biểu đồ PPM/Yield|ui/charts/cum\_daily\_chart.py|workers/summary\_worker.py; ui/pages/summary\_page.py|ui/charts/cum\_eqp\_chart.py|
|SEARCH/cache/loading|ui/widgets/daily\_summary\_widget.py|controllers/prime\_controller.py; workers/summary\_worker.py|ui/widgets/filter\_panel.py; ui/dialogs/import\_dialogs.py; ui/widgets/loading\_dialog.py|
|Index tự bổ sung vào DB cũ|—|database/schema.py|workers/database\_init\_worker.py; database/connection.py|
|Trì hoãn thư viện nặng|—|workers/summary\_worker.py|main.py; workers/cum\_import\_worker.py; services/cum\_excel\_reader.py|
|Kiểm thử|tests/test\_daily\_summary.py; tests/test\_daily\_gui.py|tests/test\_summary.py|tests/test\_filters.py; tests/test\_gui.py|

## Danh sách file trong bản vá

|Thao tác|Đường dẫn|
|-|-|
|Sửa|controllers/prime\_controller.py|
|Sửa|database/schema.py|
|Thêm|domain/daily\_summary.py|
|Sửa|domain/summary.py|
|Thêm|repositories/daily\_summary\_repository.py|
|Sửa|repositories/summary\_repository.py|
|Thêm|tests/test\_daily\_gui.py|
|Thêm|tests/test\_daily\_summary.py|
|Sửa|tests/test\_summary.py|
|Thêm|ui/charts/cum\_daily\_chart.py|
|Sửa|ui/pages/summary\_page.py|
|Thêm|ui/widgets/daily\_summary\_widget.py|
|Sửa|workers/summary\_worker.py|

## Kiểm chứng

Đã chạy 15 kiểm thử thành công, gồm tính CUM/PRIME, ngày rỗng, lọc dữ liệu, upgrade index không mất dữ liệu, SEARCH/cache, hai biểu đồ, đổi/bỏ EQP, import lại và đóng app. Đã render và kiểm tra hình hai khối Daily bằng Qt offscreen với dữ liệu mẫu. Chưa kiểm thử EXE trên Windows hoặc kết nối database sản xuất.

Chạy lại từ thư mục chứa main.py:

```bash
python -m unittest discover -s tests -v
```



\---

## \[2026-09-14 14:14:42 UTC+7] Cập nhật Prime Yield LI Daily — chỉ tính TEST\_COUNT = 1

Mục này bổ sung và thay thế phạm vi lấy dữ liệu PRIME Daily mô tả ở các mục trước: chỉ các dòng có `TEST\\\_COUNT = 1` được dùng để tính thống kê. Toàn bộ lịch sử tài liệu phía trên được giữ nguyên.

* Thêm `AND TEST\\\_COUNT = 1` vào cả hai truy vấn của `get\\\_prime\\\_daily\\\_summary`: truy vấn In/Pass và truy vấn số lỗi theo Scrap Code.
* In Qty, Pass, Fail Qty, Fail PPM, Yield và PPM từng Scrap Code đều tính trên tập bản ghi test lần 1. Biểu đồ Prime Daily dùng cùng kết quả với bảng nên áp dụng điều kiện này tự động.
* Các dòng có TEST\_COUNT khác 1 không tham gia kết quả. Ngày chỉ có các dòng này vẫn hiển thị trong khoảng ngày chọn với In/Pass/Fail bằng 0, PPM/Yield để trống.
* CUM Daily, CUM Summary, cơ chế import, cache và nạp thư viện giữ nguyên. Không xóa bản ghi test lại trong database, không sửa schema/index, không cần import lại.

### File liên quan đến chức năng lần này

|Vai trò|File|Trạng thái|
|-|-|-|
|Lọc TEST\_COUNT trong hai truy vấn PRIME Daily|repositories/daily\_summary\_repository.py|Sửa|
|Nhận kết quả truy vấn và đưa lên UI|workers/summary\_worker.py|Liên quan, không sửa|
|Hiển thị bảng và chuyển dữ liệu sang biểu đồ|ui/widgets/daily\_summary\_widget.py|Liên quan, không sửa|
|Vẽ biểu đồ Prime Daily|ui/charts/cum\_daily\_chart.py|Liên quan, không sửa|
|Hướng dẫn cập nhật|read.md|Nối nội dung mới vào cuối|
|Lịch sử thay đổi có ngày giờ Việt Nam|changelog.txt|Nối nội dung mới vào cuối|

Không thêm file mã nguồn. Gói bàn giao lần này chỉ gồm ba file có thay đổi: `repositories/daily\\\_summary\\\_repository.py`, `read.md`, `changelog.txt`.

### Áp dụng và kiểm chứng

Đóng app, chép đè ba file theo đúng đường dẫn vào project chứa `main.py`, mở lại và bấm SEARCH. Nếu sử dụng EXE thì build lại từ mã nguồn đã cập nhật.

Đã kiểm tra dữ liệu mẫu trộn TEST\_COUNT 1, 2, 3, 5: các lần test lại không làm tăng In/Pass/Fail và Scrap PPM; mã lỗi chỉ xuất hiện ở lần test lại không vào kết quả; ngày chỉ có test lại trở thành ngày không có dữ liệu lần 1. Đã xác nhận CUM không đổi và không mất bản ghi database. Chưa kiểm thử EXE trên Windows.



\[2026-09-14 14:37:40 UTC+7] Prime Yield by Slot — tab Yield Slot
Sử dụng và phạm vi thống kê
Chọn From/To, một EQP, Tier và Model; mở tab Yield Slot rồi bấm SEARCH.
Bảng có 48 cột slot (1–48), cuộn ngang để xem các cột còn lại; bên dưới là biểu đồ 48 cột đỏ Prime FAIL có nhãn số lượng.
Tiêu đề hiển thị khoảng ngày và EQP đã truy vấn.
Chỉ lấy `prime\\\_data.TEST\\\_COUNT = 1`; các lần test khác vẫn lưu trong database nhưng không tham gia thống kê.
Lọc theo `DATE BETWEEN From AND To` (bao gồm hai ngày biên), EQP, Tier và Model giống Summary/Daily.
In = SUM(QTY); PASS = SUM(QTY của RESULT='PASS'); Prime FAIL = In − PASS.
Prime Yield = PASS / In × 100; Fail PPM = Prime FAIL / In × 1.000.000.
Tính tỷ lệ từ tổng số lượng toàn khoảng ngày, không lấy trung bình tỷ lệ từng ngày.
Slot không có dữ liệu lần test đầu: In/PASS/FAIL = 0; Yield và PPM để trống.
Chưa chọn EQP: yêu cầu chọn máy, không cộng gộp nhiều máy.
Không chọn Tier hoặc Model: không trả dữ liệu, theo quy tắc bộ lọc hiện có.
SLOT và Scrap Code không thu hẹp chức năng này: luôn thống kê đủ 48 slot và toàn bộ Prime FAIL.
Yield hiển thị 2 số thập phân; PPM làm tròn để hiển thị số nguyên, biểu đồ lấy số FAIL nguyên từ cùng kết quả bảng.
Màu Yield: xanh từ 99,8%; vàng từ 95% đến dưới 99,8%; đỏ dưới 95%. Đây là màu hiển thị, không thay đổi phép tính.
Luồng chạy và tối ưu
SEARCH → controller xác định tab đang mở → worker riêng → repository SQL GROUP BY SLOT → trả tối đa 48 dòng → cập nhật bảng → vẽ biểu đồ.
Summary chỉ chạy khi đang mở Summary; Yield Slot chỉ chạy khi đang mở Yield Slot. Chuyển tab đơn thuần không query; bấm SEARCH để áp dụng bộ lọc cho tab đó.
Cache riêng mỗi tab theo From/To/Tier/Model/EQP. Search lại cùng điều kiện dùng kết quả đã hiển thị; thay riêng SLOT/Scrap Code không query Yield Slot lại.
Sau import/refresh filter, xóa cache và kết quả của cả hai tab để lần SEARCH tiếp theo lấy dữ liệu mới.
SQL chạy trên QThread với kết nối SQLite riêng; không đưa log thô lên UI, không dùng pandas cho thống kê slot.
Matplotlib chỉ import trong worker khi SEARCH sau khi cửa sổ đã mở; canvas tạo ở UI thread khi có kết quả. Khởi tạo cửa sổ không nạp matplotlib/pandas/numpy/openpyxl.
Dùng LoadingDialog hiện có, giữ đến khi cập nhật kết quả; khóa chuyển tab trong lúc worker chạy để kết quả không vẽ vào tab vừa bị ẩn. Khi lỗi, đóng loading và cho phép SEARCH lại.
Bổ sung index `idx\\\_prime\\\_first\\\_slot`:

```sql
CREATE INDEX IF NOT EXISTS idx\\\_prime\\\_first\\\_slot
ON prime\\\_data(EQP, DATE, TIER, MODEL, SLOT, RESULT, QTY)
WHERE TEST\\\_COUNT = 1;
```

EQP trước DATE phục vụ điều kiện máy bằng giá trị và khoảng ngày; các cột còn lại phục vụ lọc/tổng hợp. Partial index chỉ chứa test đầu, tránh đưa test lại vào index này.
SQLite có thể dùng bảng tạm nhỏ để GROUP BY SLOT; không ép INDEXED BY. Đã kiểm tra EXPLAIN QUERY PLAN chọn index mới trên dữ liệu kiểm thử.
Database schema 2 cũ được tự bổ sung index trong DatabaseInitWorker; database mới có sẵn index. Không xóa bảng, không yêu cầu import lại. Lần đầu mở database lớn có thể cần thêm thời gian tạo index ở worker nền.
File liên quan lần cập nhật này
Chức năng	File	Thay đổi
Cấu trúc kết quả slot	domain/slot\_summary.py	Thêm
Truy vấn tổng hợp slot	repositories/slot\_summary\_repository.py	Thêm
Worker nền, nạp thư viện chart	workers/slot\_summary\_worker.py	Thêm
Bảng 48 slot và vùng biểu đồ	ui/pages/yield\_slot\_page.py	Thêm
Biểu đồ số lượng Prime Fail	ui/charts/slot\_fail\_chart.py	Thêm
Thêm tab Yield Slot	ui/pages/prime\_page.py	Sửa
Search tab hiện tại, cache, loading	controllers/prime\_controller.py	Sửa
Index cho database cũ/mới	database/schema.py	Sửa
Kiểm thử dữ liệu/index	tests/test\_slot\_summary.py	Thêm
Kiểm thử UI/cache/tab/lỗi	tests/test\_slot\_gui.py	Thêm
Tài liệu	read.md	Nối thêm, giữ nguyên toàn bộ nội dung cũ
Nhật ký có ngày giờ Việt Nam	changelog.txt	Nối thêm, giữ nguyên toàn bộ nội dung cũ
Giữ tên `changelog.txt` đúng theo project gốc (không tạo thêm file trùng nội dung tên `changlog.txt`).
Áp dụng
Đóng app, giải nén gói cập nhật và chép các file/thư mục vào thư mục chứa main.py, chấp nhận ghi đè file cùng tên. Không xóa database. Nếu dùng EXE, build lại sau khi cập nhật mã nguồn.
Gói chỉ chứa 12 file mới/sửa nêu trên, không chứa toàn bộ project hoặc database.
Kiểm chứng
4 kiểm thử mới đều đạt: công thức và 48 slot; loại TEST\_COUNT 2/3/5; lọc ngày biên/EQP/Tier/Model; slot 48; dữ liệu rỗng; tạo lại index không đổi dữ liệu; query plan; Search không query tab ẩn; cache; reset sau refresh; lỗi truy vấn và thử lại; bảng/biểu đồ dùng cùng số FAIL.
Đã chạy kiểm thử hồi quy hiện có: có một lỗi cũ `test\\\_ui\\\_criteria\\\_and\\\_select\\\_all` về thứ tự Scrap Code (mong 3212, thực tế 9999), tái hiện trên bản gốc chưa chỉnh sửa. Không sửa logic bộ lọc ngoài phạm vi yêu cầu.
Đã xem ảnh render Qt offscreen và kiểm tra không nạp thư viện nặng khi tạo cửa sổ. Chưa kiểm thử EXE Windows hoặc hiệu năng trên database sản xuất/ổ mạng thực tế.

\[2026-09-14 17:17:24 UTC+7] Chỉnh giao diện Yield Slot và tự tải khi chuyển tab
Nội dung thay đổi
Biểu đồ Slot Fail Prime có lưới ngang/dọc màu xám nhạt và khung bốn cạnh giống phong cách biểu đồ CUM. Bỏ vạch tick bên trái và phía dưới, giữ số nhãn trục.
Giới hạn trên trục Y bằng đúng số Prime FAIL lớn nhất, không nhân thêm 1,2. Ví dụ lớn nhất bằng 1 thì trục Y dừng ở 1. Nếu toàn bộ bằng 0, dùng thang 0–1 để trục hợp lệ.
Nhãn số lượng trên đỉnh cột vẫn hiển thị kể cả khi cột chạm khung trên. Với số lượng tối đa nhỏ (0–2), thêm lưới ngang phụ để nền vẫn có các ô; nhãn số lượng trục Y vẫn là số nguyên.
Bỏ dòng “Áp dụng From/To...” phía trên bảng.
Ô góc trên In có nhãn Slot, nền xanh cùng tiêu đề bảng; cố định khi cuộn ngang.
Thu hẹp cột theo kích thước chữ thực tế, đủ cho PPM `1000000` và Yield `100.00%`; khoảng 59 px với font trong môi trường kiểm thử, tự mở rộng nếu số lượng có nhiều chữ số hơn. Không cắt giá trị hoặc giảm độ chính xác thống kê.
Chuyển tab và bộ lọc
Mục này cập nhật hành vi mô tả ở phần trước: chuyển tab sẽ tự áp dụng bộ lọc hiện tại, không cần bấm SEARCH ở tab mới.
`QTabWidget.currentChanged` → `PrimePage.\\\_on\\\_tab\\\_changed` → đọc `FilterPanel.get\\\_filter\\\_criteria()` → phát filter\_applied → controller chọn worker của tab đang mở.
Đọc trực tiếp From/To, EQP, SLOT, Tier, Model và Scrap Code từ các điều khiển, bao gồm thay đổi chưa bấm SEARCH. Mỗi tab vẫn áp dụng các trường thuộc phạm vi thống kê của nó.
Chỉ query/render tab mới hiện ra; không tải đồng thời tab ẩn. Dùng cache riêng từng tab theo cơ chế đang có.
Điều kiện không đổi thì dùng cache; thay riêng Scrap Code vẫn vẽ lại Summary theo logic hiện có mà không query lại số lượng.
Tab chuyển trong lúc khởi tạo/chưa sẵn sàng không khởi chạy truy vấn. Trong lúc worker chạy vẫn khóa tab và dùng LoadingDialog hiện có.
Bấm SEARCH vẫn áp dụng bộ lọc cho tab hiện tại như trước. Thay từng điều khiển khi đang ở một tab chưa tự query ngay; query diễn ra khi SEARCH hoặc chuyển tab.
Không thay đổi SQL, index, công thức, điều kiện `TEST\\\_COUNT = 1`, import hoặc dữ liệu database. Matplotlib vẫn chỉ nạp sau khi giao diện mở, khi lần đầu thực sự tải biểu đồ (SEARCH hoặc chuyển tab).
Các file liên quan
Chức năng	File	Trạng thái
Lưới, khung, tick và giới hạn trục Y	ui/charts/slot\_fail\_chart.py	Sửa
Nhãn Slot, bỏ chú thích, co cột bảng	ui/pages/yield\_slot\_page.py	Sửa
Tự áp dụng bộ lọc khi chuyển tab	ui/pages/prime\_page.py	Sửa
Đọc bộ lọc hiện tại dùng chung với SEARCH	ui/widgets/filter\_panel.py	Sửa
Kiểm thử chuyển tab, cache, bảng và chart	tests/test\_slot\_tab\_refresh.py	Thêm
Hướng dẫn	read.md	Nối thêm
Nhật ký có ngày giờ Việt Nam	changelog.txt	Nối thêm
Controller/worker/repository/schema liên quan được giữ nguyên. Giữ tên `changelog.txt` đang có trong project, không tạo thêm file `changlog.txt` trùng nội dung.
Áp dụng và kiểm chứng
Gói cập nhật chỉ chứa 7 file mới/sửa ở trên. Đóng app, chép file theo đúng đường dẫn vào thư mục chứa main.py, chấp nhận ghi đè. Không xóa database. Nếu dùng EXE thì build lại.
Đã kiểm tra trực quan Qt offscreen: lưới/khung, Slot nền xanh, bỏ chú thích, PPM không bị cắt và nhãn trên đỉnh cột. 5 kiểm thử nhóm Slot và 2 kiểm thử Summary đều đạt, bao gồm thay ngày không SEARCH rồi chuyển tab, cả hai hướng chuyển tab, không query tab ẩn, cache và bỏ chọn EQP. Kiểm tra riêng giới hạn Y với cực đại 0/1/2/7/37 đều đạt; tạo cửa sổ không import Matplotlib. Chưa kiểm thử EXE trên Windows.

\[2026-09-14 18:06:07 UTC+07:00] Daily Prime Yield by Slot
Chức năng và cách dùng
Chọn From/To, một EQP, một SLOT, Tier và Model; mở tab Yield Slot hoặc bấm SEARCH.
Khối mới nằm dưới biểu đồ Slot Fail Prime: bảng bên trái, biểu đồ bên phải (1300 × 536 px giống Cum Yield LI Summary). Trang dùng thanh cuộn chung.
Bảng gồm Day, Input, Output, Prime Fail, Prime Yield; một dòng cho từng ngày trong khoảng được chọn, cuối bảng là Total.
Input = SUM(QTY), Output = SUM(QTY của RESULT='PASS'), Prime Fail = Input - Output. Chỉ lấy TEST\_COUNT = 1.
Yield ngày = Output / Input × 100. Total cộng số lượng tất cả ngày; Total Yield = tổng Output / tổng Input × 100, không trung bình Yield ngày.
Ngày không có dữ liệu: số lượng 0, Yield “—”, đường Yield ngắt tại ngày đó. Total Input=0 thì Total Yield “—”.
Biểu đồ cột đỏ Prime Fail, đường xanh Prime Yield, không vẽ Total. Có lưới/khung, bỏ vạch tick; trục Fail kết thúc đúng giá trị lớn nhất (dùng 1 nếu toàn 0). Trục Yield 0–120% theo mẫu.
Dùng ngưỡng màu Yield hiện có của Yield Slot: >=99.8% xanh, >=95% vàng, còn lại đỏ; Total nền xanh nhạt.
Chưa chọn SLOT chỉ xóa khối Daily; bảng/biểu đồ tổng hợp 48 slot vẫn hoạt động. Scrapcode không lọc mẫu số yield, giống thống kê slot hiện có.
Triển khai và tối ưu
SQL GROUP BY DATE trực tiếp trong SQLite, chỉ trả dữ liệu tổng hợp theo ngày; không tải từng bản ghi và không cần pandas.
Thêm partial index idx\_prime\_first\_slot\_daily trên (EQP, SLOT, DATE, TIER, MODEL, RESULT, QTY) WHERE TEST\_COUNT = 1. Hai khóa EQP/SLOT đứng trước khoảng ngày; query plan đã xác nhận dùng index, không cần TEMP B-TREE cho GROUP BY/ORDER BY ngày.
Index tự bổ sung khi mở database hiện có; không xóa hoặc tạo lại database, không đổi schema version.
Tiếp tục dùng SlotSummaryWorker/QThread, connection riêng, dialog loading, cache tab và cơ chế làm mới sau import. SLOT được thêm vào khóa cache Yield Slot, Summary không bị ảnh hưởng.
Mỗi lần khóa cache đổi, worker tổng hợp 48 slot và (nếu chọn SLOT) query thêm thống kê ngày. Cache trùng thì không query lại.
Widget tạo nhẹ khi mở app; canvas chỉ tạo khi có kết quả, Matplotlib vẫn được nạp muộn trong worker hiện có. Bảng và biểu đồ dùng chung một kết quả.
Nhãn ngày/nhãn phần trăm được giảm mật độ khi trên 31 ngày; dữ liệu các ngày vẫn giữ đầy đủ.
File liên quan
Sửa domain/slot\_summary.py: DTO cho dòng ngày và Total, kết quả Daily tùy chọn.
Sửa repositories/slot\_summary\_repository.py: query ngày và tính tổng có trọng số.
Sửa database/schema.py: bổ sung index cho DB mới và hiện có.
Sửa controllers/prime\_controller.py: khóa cache có SLOT.
Sửa ui/pages/yield\_slot\_page.py: tích hợp khối mới dưới chart Slot Fail.
Thêm ui/widgets/slot\_daily\_widget.py: bảng ngày, Total, bố cục ngang và lazy canvas.
Thêm ui/charts/slot\_daily\_chart.py: chart Prime Fail/Prime Yield theo ngày.
Thêm tests/test\_slot\_daily.py; sửa tests/test\_slot\_gui.py: kiểm thử số liệu, index và thay đổi SLOT/cache.
Nối thêm read.md và changelog.txt, giữ nguyên toàn bộ nội dung cũ.
Kiểm tra và cài đặt
Đạt 7 kiểm thử liên quan slot: retest, ngày trống, tổng có trọng số, EQP/SLOT/Tier/Model, index DB hiện có, cache, chuyển tab, xử lý lỗi và phục hồi.
Đã kiểm tra UI Qt offscreen; chưa chạy trên Windows/database mạng thực tế.
Giải nén gói cập nhật và chép các thư mục/file vào thư mục project chứa main.py, thay thế file trùng tên; khởi động lại app. Gói chỉ chứa file thêm/sửa, không chứa database, build hoặc toàn project.

2026-09-15 09:31:00 (UTC+07:00) — Cum Yield by Model
Vị trí và sử dụng
Thêm khối Cum Yield by Model trong tab Summary, ngay dưới khối Cum Yield LI Summary và trước các bảng Daily hiện có.
Chọn bộ lọc rồi bấm SEARCH. Khi quay lại Summary, khối này tự áp dụng bộ lọc hiện tại theo cơ chế chuyển tab của project.
Bảng phía trên gồm Model, In, Out, Fail, Yield và toàn bộ scrapcode phát sinh trong dữ liệu CUM thỏa bộ lọc Date/EQP/Tier/Model. Không giới hạn bằng danh sách mã ưu tiên và không lọc bảng theo lựa chọn Scrap Code.
Dòng cuối gộp 5 ô đầu thành Total; mỗi cột scrap là tổng số lượng mã đó của tất cả Model trong bảng. Không đưa Total lên biểu đồ.
Ô scrap không phát sinh để trống. In = 0 hiển thị Yield là “—” và không vẽ điểm Yield giả bằng 0.
Bấm Copy All, Ctrl+C khi bảng có focus hoặc chuột phải → Copy All để sao chép toàn bộ header, các Model, mọi cột scrap và Total, kể cả phần đang khuất do cuộn. Clipboard là TSV, dán trực tiếp được vào Excel. Ctrl+C ở bảng này luôn copy toàn bộ bảng.
Biểu đồ nằm ngay dưới bảng: cột chồng số lượng scrap theo Model, đường Yield và nhãn phần trăm trên trục phải. Có nền gạch chéo, lưới và khung; không có vạch tick nhô ra ở trục.
Chọn một/nhiều Scrap Code rồi SEARCH: chỉ vẽ các mã được chọn. Mã được chọn nhưng không phát sinh trong kết quả có cột bằng 0. Không chọn mã nào: hiện lời nhắc chọn mã; bảng vẫn giữ đầy đủ.
Quy tắc bộ lọc
Bộ lọc	Bảng Cum theo Model	Biểu đồ bên dưới
From / To	Có, bao gồm cả hai ngày	Dùng cùng kết quả
EQP	Có; bỏ chọn EQP thì tổng hợp tất cả máy	Dùng cùng kết quả
Tier / Model	Có; không chọn Tier hoặc Model thì không trả dữ liệu	Dùng cùng kết quả
SLOT	Không áp dụng: cum\_data không có cột SLOT	Không áp dụng
Scrap Code	Không áp dụng	Chỉ vẽ mã được chọn
Công thức và dữ liệu nguồn
In = SUM(cum\_data.INQTY), Out = SUM(cum\_data.OUTQTY), GROUP BY MODEL.
Fail = In - Out, đồng nhất với các bảng CUM trước đó. Không lấy tổng FAILQTY có thể khác công thức đang dùng.
Yield = Out / In × 100 từ tổng sản lượng, không trung bình cộng YIELD của từng dòng.
Số lượng scrap = SUM(cum\_scrap\_detail.qty), JOIN cum\_data bằng cum\_data\_id = id và GROUP BY MODEL, scrap\_code. Đây là số lượng, không phải PPM hoặc số bản ghi.
cum\_scrap\_detail được importer hiện có cập nhật từ cum\_data.SCRAP. Không phân tích lại chuỗi SCRAP lúc SEARCH; nếu sửa SCRAP thủ công ngoài app thì cần cập nhật detail tương ứng hoặc import lại CUM qua app.
Tổng scrap không bị ép bằng Fail: giữ nguyên số lượng từng mã nguồn, không suy diễn các mã chưa có dữ liệu.
Tối ưu kỹ thuật
Chỉ thêm 2 truy vấn tổng hợp cho khối Model: sản lượng và scrap. Không query từng Model, từng mã hoặc từng ô.
Tách truy vấn sản lượng khỏi JOIN scrap để không nhân In/Out khi một dòng CUM có nhiều mã lỗi.
Các câu SELECT dùng chung connection và transaction đọc BEGIN của SummaryWorker với các bảng Summary/Daily, giúp dữ liệu đồng nhất trong một lần tải. Worker có connection riêng, không truyền connection SQLite sang GUI.
Tái sử dụng index idx\_cum\_tier\_model\_date\_eqp(TIER, MODEL, DATE, EQPID) để lọc và UNIQUE index (cum\_data\_id, scrap\_code) để JOIN detail. EXPLAIN QUERY PLAN trên fixture xác nhận cả hai được sử dụng; không thêm index trùng, không thay schema và không cần xóa database. Tốc độ thực tế còn phụ thuộc dung lượng dữ liệu và mạng.
Cache dùng key Summary hiện có: From, To, Tier, Model, EQP. SLOT và Scrap Code không nằm trong key. Khi chỉ đổi scrapcode, vẽ lại từ kết quả đã có; không query lại, không reset bảng Model.
Import PRIME/CUM hoặc refresh bộ lọc xóa cache và kết quả Model cùng các bảng Summary. Lỗi tải không giữ số liệu/biểu đồ cũ gây nhầm lẫn.
Bảng dùng QTableView + QAbstractTableModel: không tạo QTableWidgetItem cho từng ô; một lần beginResetModel/endResetModel khi nhận kết quả mới. Chiều cao giới hạn 440px, chiều rộng giới hạn 1300px, có thanh cuộn khi vượt giới hạn. Copy All vẫn chứa toàn bộ dữ liệu.
Matplotlib chỉ import sau khi SEARCH trong worker như cơ chế trước; CumModelChart chỉ được import/tạo khi nhận kết quả. Khởi tạo MainWindow không load pandas/Matplotlib.
Tái sử dụng canvas và hai trục, xóa artist/legend cũ và draw\_idle; số cột legend/chiều cao thích ứng số mã, xoay tên Model khi nhiều Model. Không áp giới hạn cố định số scrapcode được thống kê.
File liên quan trong gói cập nhật
File	Loại	Chức năng
domain/model\_summary.py	Thêm	Kiểu dữ liệu Model, số lượng scrap và Total
repositories/model\_summary\_repository.py	Thêm	Hai truy vấn tổng hợp theo Model với bộ lọc chung
ui/widgets/model\_summary\_widget.py	Thêm	Bảng động, Total, Copy All và cache biểu đồ
ui/charts/cum\_model\_chart.py	Thêm	Biểu đồ cột chồng scrap và đường Yield
domain/summary.py	Sửa	Bổ sung cum\_model vào kết quả Summary
workers/summary\_worker.py	Sửa	Nạp thống kê Model trong transaction Summary hiện có
ui/pages/summary\_page.py	Sửa	Gắn khối mới, nhận kết quả, reset và cập nhật scrap
tests/test\_model\_summary.py	Thêm	Kiểm thử dữ liệu, query plan, UI/cache/copy và chuyển tab
read.md	Nối tiếp	Hướng dẫn và mô tả kỹ thuật lần cập nhật này
changelog.txt	Nối tiếp	Nhật ký thay đổi có ngày giờ
Kiểm tra và phạm vi xác minh
4 kiểm thử mới: tổng hợp/filters/mã động; index qua EXPLAIN QUERY PLAN; SEARCH qua worker, clipboard và đổi scrap từ cache; quay lại Summary lấy ngày vừa sửa không cần SEARCH.
3 kiểm thử hồi quy Summary và Daily GUI chạy thành công cùng 4 kiểm thử mới (7/7).
Kiểm tra riêng startup: MainWindow chưa import pandas hoặc Matplotlib.
Đã dựng và xem ảnh UI bằng Qt offscreen với 8 Model/4 scrapcode theo mẫu. Đây là dữ liệu minh họa; các số sản lượng thực lấy theo database, không hardcode bảng mẫu.
Kiểm thử cũ test\_slot\_tab\_refresh thất bại ở yêu cầu độ rộng cột <64 (thực tế 80) trên cả ZIP gốc và bản sửa; không phải lỗi phát sinh từ cập nhật Model. Giữ nguyên file/chức năng Yield Slot ngoài phạm vi yêu cầu. Luồng chuyển tab của khối Model được kiểm tra riêng và đạt.
Kiểm thử chạy trên Linux/Qt offscreen, chưa chạy EXE Windows hoặc đo tốc độ trên database mạng thực tế của người dùng.
Cài cập nhật
Đóng app, giải nén gói vào thư mục gốc LI\_App\_v1.3-master (cạnh main.py), chép đè các file cùng đường dẫn và thêm các file mới. Gói chỉ chứa file thêm/sửa, không có database hoặc toàn bộ project. read.md và changelog.txt đã giữ nguyên nội dung cũ và nối thêm mục này ở cuối. Mở main.py như trước; không cần cài thêm dependency so với requirements.txt hiện có và không cần tạo lại database.

2026-09-15 10:11:45 (UTC+07:00) — Chuyển Cum theo Model sang Yield Slot, sửa legend và bố cục
Mục này thay thế hướng dẫn vị trí/bố cục của Cum Yield by Model trong lần cập nhật trước.
Thay đổi sử dụng
Cum Yield by Model nằm cuối tab Yield Slot, dưới toàn bộ bảng và biểu đồ Slot Daily. Bảng Model ở trên, biểu đồ Model ngay bên dưới; không còn xuất hiện trong Summary.
Legend chỉ hiển thị scrapcode vừa được chọn vừa có số lượng > 0 trong dữ liệu CUM hiện tại. Không tạo cột/legend cho mã không phát sinh và không tạo Rectangle cho ô số lượng bằng 0.
Nếu tất cả mã đang chọn đều không phát sinh: xóa biểu đồ/legend cũ và hiện thông báo. Không chọn Scrap Code: hiện hướng dẫn chọn mã. Bảng vẫn có tất cả scrapcode và Copy All hoạt động như trước.
Biểu đồ lấy trực tiếp bảng màu CODE\_COLORS của CumDailyStackedChart; màu mỗi mã theo thứ tự mã trong kết quả đầy đủ, giữ ổn định khi chỉ đổi lựa chọn scrap. Đường Yield dùng #4472C4.
Legend giống cấu hình Cum Daily LI: tối đa 15 mục/hàng (bao gồm Yield), fontsize=8, handlelength=1.8, columnspacing=1.2, nằm giữa dưới biểu đồ. Khoảng đáy tính theo số hàng legend như Daily.
Canvas 1550 × 550 px giống Cum Daily LI; tiêu đề biểu đồ không in đậm. Giữ cách tính số lượng scrap, Yield, nền và lưới của biểu đồ Model.
Khung bảng giãn hết chiều ngang khả dụng của tab, bỏ giới hạn chiều rộng 1300px. Mỗi cột co theo chữ/số thực tế cộng 14px khoảng đệm; cột scrap vừa mã lỗi hoặc số lượng Total nếu số đó dài hơn. Không kéo giãn cột scrap khi ít mã; phần ngang còn dư của khung để trống. Có cuộn ngang nếu nhiều mã; Copy All vẫn chứa mọi dòng/cột.
Bộ lọc, worker và cache
Giữ bộ lọc CUM theo From/To, Tier, Model, EQP. SLOT không áp dụng cho CUM; Scrap Code chỉ áp dụng biểu đồ.
Khi chưa chọn EQP, phần PRIME Slot phía trên yêu cầu chọn máy như trước; phần CUM Model cuối tab vẫn tổng hợp tất cả máy.
SlotSummaryWorker tải cả kết quả Slot và CUM Model; SummaryWorker không query CUM Model nữa. ModelSummaryRepository vẫn dùng hai câu tổng hợp và index sẵn có, không thay dữ liệu hoặc schema.
Cache CUM theo 5 thành phần From/To/Tier/Model/EQP. Chỉ đổi SLOT: Slot worker tái sử dụng đối tượng kết quả CUM đã có, không query lại CUM. Chỉ đổi Scrap Code: không khởi động worker/query, chỉ cập nhật biểu đồ.
Chuyển sang Yield Slot tự áp dụng các giá trị bộ lọc hiện tại; import hoặc refresh filter vẫn xóa cả cache lẫn kết quả. Giữ dialog loading và lazy import Matplotlib sau khi giao diện đã mở.
Truy vấn CUM dùng transaction đọc riêng của ModelSummaryRepository trong Slot worker; truy vấn PRIME Slot giữ cơ chế kết nối hiện có. Không thay đổi cơ chế import/ghi dữ liệu.
File chỉnh sửa
File	Nội dung
controllers/prime\_controller.py	Chuyển lựa chọn Scrap Code cho Yield Slot, cache CUM khi chỉ đổi SLOT, cho phép tải CUM khi không chọn EQP
domain/slot\_summary.py	Thêm cum\_model vào kết quả Slot
domain/summary.py	Bỏ cum\_model khỏi kết quả Summary
workers/slot\_summary\_worker.py	Tải hoặc tái sử dụng CUM Model cùng tác vụ Slot
workers/summary\_worker.py	Bỏ truy vấn CUM Model ở Summary
ui/pages/summary\_page.py	Bỏ khối Model khỏi Summary
ui/pages/yield\_slot\_page.py	Đặt khối Model cuối tab, nhận dữ liệu/scrap và xóa cache khi refresh
ui/widgets/model\_summary\_widget.py	Khung bảng toàn chiều ngang, cột gọn theo nội dung, canh trái biểu đồ
ui/charts/cum\_model\_chart.py	Legend thực phát sinh, màu/số mục/chiều rộng giống Daily, title không đậm
tests/test\_model\_summary.py	Cập nhật kiểm thử vị trí mới và thêm kiểm tra legend/cache SLOT
read.md	Nối tiếp hướng dẫn lần này
changelog.txt	Nối tiếp nhật ký có ngày giờ
Xác minh và cài đặt
8/8 kiểm thử liên quan đạt: tổng hợp/filters/index, copy/cache, chuyển tab, legend/chiều rộng/title/cache khi đổi SLOT và hồi quy Summary/Daily.
Startup được kiểm tra riêng: tạo MainWindow chưa import pandas hoặc Matplotlib.
Đã dựng và xem giao diện Qt offscreen. Chưa chạy bản EXE Windows hoặc database mạng thực tế.
Đóng app, giải nén gói cập nhật vào thư mục cạnh main.py, chép đè đúng đường dẫn. Chỉ có file sửa so với LIApp (6).zip. Không cần xóa/tạo lại database. Nội dung read.md và changelog.txt cũ được giữ nguyên phía trước mục mới này.

2026-09-15 10:54:25 (UTC+07:00) — Cum Yield by Model chỉ lọc From / To / Tier
Mục này thay thế quy tắc EQP/Model và cache của Cum Yield by Model ở các mục trước. Khối vẫn ở cuối tab Yield Slot.
Bộ lọc	Bảng Cum Yield by Model	Biểu đồ Cum Yield by Model
From / To	Có, gồm cả hai ngày	Dùng cùng dữ liệu bảng
Tier	Có; không chọn Tier thì bảng rỗng	Dùng cùng dữ liệu bảng
EQP	Không; luôn tổng hợp mọi EQP	Không
Model	Không; luôn thống kê mọi Model trong khoảng ngày/Tier, kể cả khi bỏ chọn toàn bộ Model	Không
SLOT	Không	Không
Scrap Code	Không; bảng vẫn chứa tất cả mã phát sinh	Chỉ vẽ mã được chọn có số lượng > 0
Triển khai
ModelSummaryRepository.load chỉ nhận From, To, Tier và connection tùy chọn; không nhận EQP/Model. WHERE của cả hai truy vấn chỉ có DATE BETWEEN và TIER IN, không gọi bộ lọc chung build\_data\_filter vốn yêu cầu Model.
Giữ nguyên SUM(INQTY), SUM(OUTQTY), Fail = In - Out, Yield = Out/In × 100; scrap lấy SUM(qty) từ cum\_scrap\_detail. Dòng Total và Copy All không đổi.
SlotSummaryWorker chỉ chuyển 3 giá trị From/To/Tier cho repository CUM. Phần PRIME Slot vẫn nhận đầy đủ bộ lọc cũ.
Cache CUM so sánh 3 giá trị From/To/Tier. Đổi EQP, Model hoặc SLOT chỉ làm tải lại phần Slot theo cơ chế cũ, tái sử dụng dữ liệu CUM đã có; không query lại CUM. Đổi Scrap Code vẫn chỉ vẽ lại biểu đồ.
Đổi ngày/Tier hoặc import/refresh sẽ tải lại CUM. Chuyển tab tự áp dụng bộ lọc như trước. Không thay bộ lọc hay cách tính của Summary, Daily hoặc PRIME Slot.
Thêm index idx\_cum\_tier\_date\_model(TIER, DATE, MODEL) cho database mới và database hiện có qua ensure\_performance\_indexes. Không đổi schema version, không xóa dữ liệu, không cần tạo lại database. Giữ index cũ vì các chức năng khác vẫn cần lọc Model.
EXPLAIN QUERY PLAN trên fixture xác nhận truy vấn sản lượng dùng index Tier/Date mới; truy vấn scrap dùng index CUM và UNIQUE index detail để JOIN. SQLite tự chọn index theo từng truy vấn, không ép INDEXED BY.
File chỉnh sửa
File	Nội dung
repositories/model\_summary\_repository.py	Chỉ lọc ngày và Tier, bỏ phụ thuộc EQP/Model
workers/slot\_summary\_worker.py	Chỉ chuyển From/To/Tier vào truy vấn CUM
controllers/prime\_controller.py	Cache CUM độc lập EQP/Model/SLOT
database/schema.py	Tự bổ sung index Tier/Date/Model cho DB mới và đang dùng
tests/test\_model\_summary.py	Kiểm tra mọi Model/máy, cache khi đổi EQP/Model/SLOT, đổi Tier/ngày và bổ sung index không mất dữ liệu
read.md	Nối tiếp hướng dẫn này
changelog.txt	Nối tiếp nhật ký có ngày giờ
Xác minh và cài đặt
8/8 kiểm thử liên quan đạt trên Qt offscreen: tổng hợp, index, cập nhật index lặp lại trên database có dữ liệu, bộ lọc/cache, copy/legend/chuyển tab và hồi quy Summary/Daily. Chưa chạy EXE Windows hoặc database mạng thực tế.
Đóng app, giải nén gói vào thư mục cạnh main.py và chép đè đúng đường dẫn. Gói chỉ gồm file sửa so với LIApp (7).zip; không chứa database. Khi mở app, index mới được bổ sung tự động. read.md và changelog.txt giữ nguyên nội dung cũ và nối mục mới này ở cuối.



\[2026-09-15 11:10:24 (UTC+07:00)] File Management giống Aging
Cài đặt bản cập nhật
Giải nén gói cập nhật vào đúng thư mục LIApp đang chứa main.py và chép đè theo đường dẫn tương đối bên dưới. Không chép vào thư mục `New folder` trong project.
Gói chỉ gồm file thêm/sửa và tài liệu nối tiếp; không chứa database hay toàn bộ project.
Không cần xóa database. App bổ sung bảng cấu hình `auto\\\_import\\\_scheduler` với id=1; mặc định Auto Import tắt, giờ 03:00, thư mục trống. Schema dữ liệu LI vẫn là phiên bản 2.
Không cần thêm thư viện: dùng PyQt5 và openpyxl đã có trong requirements.txt.
Hành vi và giao diện
Bố cục: Prime Data List bên trái, Cum Data List ở giữa, Auto Import Prime Log bên phải. Hai bảng cùng chiều rộng; khối cấu hình rộng 440 px, căn trên; hàng cao 30 px, nền xen kẽ và khung giống Aging.
Bộ lọc thống kê chung được ẩn ở tab này. Danh sách không phụ thuộc From/To/EQP/SLOT/Model/Tier/Scrap Code.
Mỗi DATE thực tế chỉ hiển thị một dòng, sắp xếp giảm dần; Month lấy 6 ký tự đầu DATE. Load time lấy `data\\\_import\\\_status.imported\\\_at`, chuyển UTC sang giờ máy và hiển thị `yyyy-MM-dd HH:mm:ss`. Ngày cũ thiếu metadata hiện dấu —, không tự tạo thời gian giả.
Filter Month/Filter Date độc lập cho từng bảng. Date chỉ liệt kê các ngày thuộc Month đang chọn. Đổi Month mặc định chọn tất cả Date của tháng đó; các ô chọn xuất được bỏ tích khi lọc hoặc tải lại như Aging.
PRIME có Select All và checkbox từng ngày. Select All chỉ tác động các dòng đang hiển thị. CUM không có checkbox hoặc Export.
Export Prime xuất tất cả cột và tất cả dòng của ngày được tích, bao gồm TEST\_COUNT khác 1 và TIER trống. Không áp dụng bộ lọc thống kê.
Export chạy QThread, đọc batch 10.000 dòng, openpyxl write-only, tối đa 1.048.575 dòng dữ liệu/sheet. Ghi file tạm rồi thay file đích sau khi hoàn tất.
Tải danh sách và Export dùng loading dialog. Tab tạo lần đầu sau khi DB sẵn sàng, không tải openpyxl khi khởi động; tải lại khi quay lại tab để thấy dữ liệu do auto import/người khác cập nhật. Đóng cửa sổ đợi worker hoàn tất, không cần bấm Close lần hai.
Dùng index DATE hiện có; metadata có khóa chính (data\_type, DATE), không tạo index trùng.
Auto Import và Task Scheduler
Enable, Import Time (HH:mm), Select Folder và Save giống Aging. Save chỉ lưu cấu hình trong DB; không tự tạo Windows Task Scheduler và không tạo bộ hẹn giờ trong GUI.
`auto\\\_import\\\_main.py` là tác vụ chạy độc lập giống entry point của Aging, cần thiết để chạy khi GUI đã đóng. Tác vụ chỉ import ngày hôm trước sau giờ cấu hình, bỏ qua khi tắt hoặc ngày đó đã auto import thành công.
Dùng đúng PrimeImportService của LI: parser LI, staging, khóa import dùng chung, thay dữ liệu theo các ngày thực tế trong staging, đồng bộ TIER. Không dùng parser/chamber của Aging. Không thay cơ chế import thủ công.
Chỉ ghi last\_import\_date sau khi service thành công; khi lỗi giữ mốc cũ để lần chạy sau thử lại. Thời điểm chạy theo đồng hồ Windows. Log nối tiếp ở `log/auto\\\_import\\\_log.txt` cạnh project/EXE.
Cấu hình Task Scheduler trên một máy phụ trách: Program là đường dẫn đầy đủ python.exe; Arguments là `"D:\\\\LIApp\\\\auto\\\_import\\\_main.py" --database "D:\\\\LIApp\\\\database\\\\li\\\_app.db"`; Start in là `D:\\\\LIApp`. Thay các đường dẫn ví dụ bằng đường dẫn thực tế; --database phải trỏ cùng DB mà GUI dùng.
Đặt trigger lặp mỗi 5 phút, thời hạn Indefinitely; chọn “Do not start a new instance”. Script tự kiểm tra Import Time và ngày đã hoàn thành. Tài khoản chạy task cần đọc được folder log và ghi được database. Chưa tạo task hoặc chạy thử trên máy Windows của người dùng.
Nếu không truyền --database: dùng LI\_DB\_PATH nếu có, nếu không dùng DATABASE\_PATH trong config/paths.py. Không thêm JSON cấu hình startup.
File liên quan
File	Thao tác	Chức năng
`auto\\\_import\\\_main.py`	Thêm	Entry point cho Task Scheduler: đọc cấu hình, import log hôm qua, ghi log và đánh dấu thành công.
`controllers/prime\\\_controller.py`	Sửa	Tải tab sau khởi tạo DB; làm mới sau import; đợi worker khi đóng cửa sổ.
`database/connection.py`	Sửa	Bổ sung hàm tạo kết nối cho các repository/worker; giữ timeout và PRAGMA của LI.
`database/schema.py`	Sửa	Tạo bổ sung auto\_import\_scheduler cho DB LI mới/cũ, giữ nguyên dữ liệu schema 2.
`repositories/auto\\\_import\\\_scheduler\\\_repository.py`	Thêm	Đọc/lưu Enable, Import Time, Log Folder và last\_import\_date.
`repositories/database\\\_management\\\_repository.py`	Thêm	Danh sách DATE thực tế qua index và LEFT JOIN metadata import LI.
`services/prime\\\_export\\\_service.py`	Thêm	Xuất toàn bộ cột PRIME bằng fetchmany và openpyxl write-only, chia sheet.
`tests/test\\\_file\\\_management.py`	Thêm	Kiểm thử database cũ, export, scheduler và vòng đời GUI.
`ui/filter\\\_value\\\_dialog.py`	Thêm	Popup lọc tháng/ngày có Search, Select All, OK/Cancel giống Aging.
`ui/pages/file\\\_management\\\_page.py`	Thêm	Hai bảng ngày, lọc độc lập, chọn PRIME, export và loading dialog.
`ui/pages/prime\\\_page.py`	Sửa	Thêm tab File Management, ẩn bộ lọc thống kê khi mở tab, lazy-create UI.
`ui/widgets/auto\\\_import\\\_scheduler\\\_panel.py`	Thêm	Khối Auto Import Prime Log bên phải giống Aging.
`workers/database\\\_management\\\_worker.py`	Thêm	Worker tải danh sách và xuất Excel ngoài UI thread.
`read.md`	Sửa, nối tiếp	Hướng dẫn chức năng, file liên quan, cài đặt và kiểm thử.
`changelog.txt`	Sửa, nối tiếp	Lịch sử thay đổi có ngày giờ.
Kiểm thử và giới hạn xác nhận
4 kiểm thử File Management đạt: bổ sung cấu hình trên DB đã có dữ liệu và chạy lặp; danh sách/metadata; Excel chọn ngày và chia sheet vẫn giữ TEST\_COUNT; scheduler tắt/thành công/lỗi/chạy lặp; tải tab, lọc/chọn, export QThread và đóng cửa sổ lúc worker đang chạy. Chạy: `python -m unittest discover -s tests -p "test\\\_file\\\_management.py" -v`.
5 kiểm thử GUI có sẵn đạt: import/re-import, hủy chọn, ngày, đóng một lần, đóng khi đang chạy tác vụ.
Hai kiểm tra cũ không đạt ở cả bản ZIP gốc và bản cập nhật trong môi trường Qt offscreen: số QPushButton thực tế 4 thay vì 3; chiều rộng cột Slot 80 thay vì <64. Không sửa các kiểm tra hay giao diện thống kê không liên quan.
Đã kiểm tra ảnh giao diện Qt offscreen; font/emoji thực tế có thể khác theo Windows và DPI. Chưa kiểm thử trực tiếp UNC/Task Scheduler trên máy sản xuất.

\[2026-09-15 11:20:49 (UTC+07:00)] Sửa File Management ẩn bộ lọc
Bỏ logic ẩn filter\_panel/filter\_status và đổi lề về 0 khi mở File Management. Bộ lọc và lề 24 px được giữ như các tab khác; File Management nằm trong vùng tab bên dưới.
Nội dung cập nhật này thay thế mô tả “Bộ lọc thống kê chung được ẩn ở tab này” trong lần bàn giao trước.
Giữ nguyên truy vấn, export, cấu hình Auto Import và bộ lọc Month/Date riêng của File Management.
File sửa: `ui/pages/prime\\\_page.py` (bố cục khi chuyển tab); `tests/test\\\_file\\\_management.py` (đổi kiểm tra sang yêu cầu bộ lọc vẫn hiển thị); `read.md` và `changelog.txt` (nối tiếp).
Chép đè các file theo đúng thư mục trong gói vào thư mục LIApp chứa main.py rồi mở lại app. Không cần thay đổi database.
Đã chạy 4 kiểm thử File Management thành công, gồm kiểm tra bộ lọc hiển thị khi mở tab bằng Qt offscreen.

\[2026-09-15 12:47:53 (UTC+07:00)] Auto Import bỏ qua ngày chưa có file
Khi `PrimeImportService` trả đúng lỗi `Không tìm thấy file .txt trong các folder ngày được chọn`, `auto\\\_import\\\_main.py` ghi một dòng `SKIPPED` rồi kết thúc với mã `0`. Vì vậy Task Scheduler không còn nhận trạng thái lỗi và log không có `ERROR` hoặc `TRACEBACK` cho trường hợp này.
Không cập nhật `last\\\_import\\\_date` khi chưa có file. Nếu Task Scheduler chạy lặp, lần chạy sau vẫn kiểm tra lại ngày hôm trước và sẽ import khi file xuất hiện.
Chỉ trường hợp không có file được bỏ qua. Folder không truy cập được, file sai cấu trúc, file rỗng/không có sản phẩm hợp lệ, dữ liệu sai hoặc lỗi database vẫn được chuyển tới `main()` để ghi `ERROR` và `TRACEBACK` như trước.
Import PRIME thủ công không thay đổi: khi người dùng chọn ngày không có file, giao diện vẫn có thể báo không tìm thấy file để người dùng biết lựa chọn không có dữ liệu.
File sửa: `auto\\\_import\\\_main.py`; `tests/test\\\_file\\\_management.py`; `read.md`; `changelog.txt`.
Đã kiểm tra: ngày không có file trả mã `0`, ghi `SKIPPED`, giữ `last\\\_import\\\_date` rỗng; file `.txt` sai nội dung vẫn phát sinh `ValidationError`.

\[2026-09-15 13:12:28 (UTC+07:00)] Auto Import PRIME ngày hiện tại
Cơ chế hoạt động
Thêm entry point `auto\\\_import\\\_today\\\_main.py` dành riêng cho Task Scheduler. Mỗi lần được gọi, file lấy ngày hiện tại theo đồng hồ Windows và truyền ngày đó vào chính `PrimeImportService` mà nút Import PRIME đang dùng.
Cơ chế ghi đè không được viết lại riêng: service đọc và kiểm tra toàn bộ file vào SQLite staging trước; khi staging hợp lệ, `PrimeRepository.replace\\\_from\\\_staging()` mở transaction, xóa dữ liệu PRIME của ngày trong staging, ghi toàn bộ bản mới, đồng bộ TIER rồi commit. Nếu đọc/kiểm tra lỗi, dữ liệu đang có không bị xóa.
Không kiểm tra và không cập nhật `last\\\_import\\\_date`. Vì vậy Task Scheduler có thể gọi nhiều lần trong ngày và lần nào cũng thay lại dữ liệu hôm nay. File `auto\\\_import\\\_main.py` vẫn có thể import chốt ngày hôm qua vào ngày kế tiếp.
Dùng chung `Enable Auto Import Prime Log`, `Import Time` và `Log Folder` đã lưu tại tab File Management. Nếu Auto Import tắt hoặc chưa đến Import Time thì ghi `SKIPPED` và kết thúc bình thường.
Nếu hôm nay chưa có file `.txt`, ghi `SKIPPED`, không ghi `ERROR/TRACEBACK`, không xóa dữ liệu đang có và chờ lần chạy sau. Các lỗi truy cập folder, cấu trúc log, dữ liệu và database vẫn ghi `ERROR/TRACEBACK`.
Tất cả trạng thái INFO/SUCCESS/SKIPPED/ERROR được nối vào cùng file `log/auto\\\_import\\\_log.txt` mà `auto\\\_import\\\_main.py` đang sử dụng. Nội dung log có chữ `TODAY` để phân biệt hai tác vụ.
Dùng khóa import chung của LI. Nếu Import PRIME/CUM hoặc một auto task khác đang ghi database, tác vụ không chạy chồng lên transaction hiện tại.
Cài Task Scheduler cho Today
Program/script: đường dẫn đầy đủ tới `python.exe` đang chạy LI App.
Add arguments: `"D:\\\\LIApp\\\\auto\\\_import\\\_today\\\_main.py" --database "D:\\\\LIApp\\\\database\\\\li\\\_app.db"`.
Start in: `D:\\\\LIApp` (thư mục chứa `main.py` và `auto\\\_import\\\_today\\\_main.py`). Thay đường dẫn ví dụ bằng đường dẫn thực tế; database phải giống `DATABASE\\\_PATH` của GUI.
Trigger đề xuất: chạy mỗi 1 giờ trong ngày. Chọn `Do not start a new instance` cho task Today. Nên tránh đặt task Today và task Yesterday chạy đúng cùng phút vì hai tác vụ dùng chung khóa import.
Nếu đóng gói thành EXE riêng, dùng `auto\\\_import\\\_today\\\_main.py` làm entry point và đặt EXE cùng thư mục ứng dụng; Task Scheduler gọi EXE với `--database` tương tự.
File bàn giao và kiểm thử
`auto\\\_import\\\_today\\\_main.py`: file mới để import/ghi đè log hôm nay.
`tests/test\\\_auto\\\_import\\\_today.py`: kiểm tra chạy lại thay dữ liệu và thiếu file không xóa dữ liệu cũ.
`read.md`, `changelog.txt`: nối tiếp nội dung hiện tại.
Đã chạy `python -m unittest tests.test\\\_auto\\\_import\\\_today -v`: 2/2 kiểm thử đạt. Kết quả xác nhận lần chạy thứ hai xóa một bản ghi cũ, chỉ giữ bản ghi mới; `last\\\_import\\\_date` không đổi; ngày chưa có file trả `SKIPPED` và giữ dữ liệu cũ.

\[2026-09-15 14:47:10 (UTC+07:00)] Tab Send Mail theo giao diện Aging
Phạm vi chức năng
Sender: Add/Delete, User ID và Name bắt buộc, không trùng User ID; che mật khẩu trên bảng; Enable tối đa một Sender. Đổi Enable chạy trong transaction BEGIN IMMEDIATE và có unique index bảo vệ.
Receiver / CC: Add/Delete; đổi Receiver/CC/None ngay tại bảng. Tải lại cả danh sách và bảng sau khi đổi loại để thứ tự dòng và ID xóa luôn khớp nhau.
Auto Send Mail: giữ giao diện Enable Auto Send Mail, Send Time HH:mm và Save như Aging. Chỉ lưu cấu hình SQLite; KHÔNG tạo Task Scheduler, không chạy timer gửi mail, không gửi tự động dù Enable đã được lưu.
Test Login: kiểm tra Sender đang Enable qua cùng endpoint đăng nhập của Aging. Chạy QThread, chỉ nạp requests trong worker khi bấm nút. Luôn đóng session, xử lý lỗi và dọn thread. Đóng app khi đang đăng nhập sẽ chờ worker kết thúc, không cần bấm Close lần thứ hai.
Customize Email: vẫn hiển thị tại vị trí cũ nhưng tạm vô hiệu hóa. Chưa đưa luồng tạo nội dung hoặc gửi email vào LI. Nút gửi thủ công không hiển thị như bản Aging nguồn/ảnh mẫu.
MAIL HISTORY: giữ 8 cột ID, Alarm Date, Send Time, Sender, Receiver, CC, Result, Detail. Hiển thị tối đa 500 lịch sử mới nhất; click để xem snapshot HTML và thông tin mail. Database mới chưa có mail nên bảng trống, không tạo lịch sử giả.
Tab và hộp thoại giữ bố cục, màu, kích thước cột, hàng và các điều khiển của Aging. Giữ bộ lọc chung của LI ở trên tab theo bố cục hiện tại; dữ liệu mail độc lập mọi bộ lọc thống kê.
Database và tích hợp
Khởi tạo tự bổ sung mail\_sender, mail\_recipient, auto\_send\_mail\_scheduler và mail\_send\_history cho database mới hoặc LI schema 2 hiện tại; không cần xóa/tạo lại database.
Bổ sung schema theo savepoint để lỗi có thể rollback toàn bộ phần tạo bảng mail. Giữ schema 2 và toàn bộ dữ liệu PRIME/CUM, File Management, lịch sử cấu hình đã lưu. Chưa tạo bảng Slot Fail hay lịch sử slot đã gửi.
Tái sử dụng kết nối LI: journal\_mode DELETE, busy\_timeout 60 giây, kết nối riêng cho tác vụ. Giao diện tạo tab lần đầu sau khi database sẵn sàng và nạp lại khi quay về tab.
Test Login dùng URL của Aging: http://107.11.192.45/DATA/Ajax\_UserLoginGet.asp. Cần chạy trong mạng nội bộ có thể truy cập hệ thống này.
Mật khẩu được lưu theo cơ chế database của Aging; ký tự che chỉ áp dụng trên giao diện.
File thêm/sửa theo chức năng
File	Loại	Vai trò
ui/pages/prime\_page.py	Sửa	Thêm tab Send Mail và tín hiệu mở tab, nạp giao diện khi cần.
controllers/prime\_controller.py	Sửa	Mở tab sau khi DB sẵn sàng, Search độc lập bộ lọc, chờ login khi đóng app.
database/schema.py	Sửa	Gọi bổ sung schema mail khi mở database.
database/mail\_schema.py	Thêm	Bốn bảng mail và index; khởi tạo lại không ghi đè cấu hình.
ui/pages/send\_mail\_page.py	Thêm	Giao diện Send Mail, thao tác cấu hình, lịch sử, Test Login.
ui/mail\_party\_dialogs.py	Thêm	Form Add Sender và Add Receiver/CC.
ui/mail\_history\_dialog.py	Thêm	Xem nội dung mail và thông tin lịch sử.
ui/widgets/auto\_send\_mail\_scheduler\_panel.py	Thêm	Checkbox, giờ gửi và Save.
repositories/mail\_configuration\_repository.py	Thêm	Đọc/ghi Sender và người nhận; transaction và kiểm tra dữ liệu.
repositories/auto\_send\_mail\_scheduler\_repository.py	Thêm	Đọc/ghi và kiểm tra cấu hình giờ gửi.
repositories/mail\_send\_repository.py	Thêm	Chỉ đọc danh sách/chi tiết lịch sử; không gửi mail.
services/mail\_service.py	Thêm	Chỉ đăng nhập hệ thống mail và đóng session.
workers/mail\_login\_worker.py	Thêm	Chạy login ngoài UI thread, trả kết quả/lỗi và tín hiệu hoàn tất.
requirements.txt	Sửa	Bổ sung requests cho Test Login.
read.md, changelog.txt	Sửa	Nối tiếp mô tả triển khai và lịch sử thay đổi.
Cách áp dụng
Đóng ứng dụng LI.
Giải nén gói và chép các file theo đúng đường dẫn tương đối vào thư mục LIApp đang chứa main.py. Chấp nhận ghi đè các file cùng tên. Gói không chứa database, không chứa toàn bộ project.
Chạy `python -m pip install -r requirements.txt` bằng môi trường Python dùng để chạy LI.
Mở lại app, vào tab Send Mail, Add Sender và Receiver/CC. Chọn một Sender Enable rồi bấm Test Login.
Customize Email và gửi mail sẽ triển khai sau khi có chức năng Slot Fail. Việc lưu Auto Send Mail hiện tại chưa làm phát sinh email.
Kiểm tra đã thực hiện
Kiểm tra cú pháp Python của project; chạy GUI Qt offscreen và kiểm tra ảnh tab Send Mail.
Tạo DB mới, mở lại nhiều lần; bổ sung bảng trên bản sao database đính kèm và đối chiếu toàn bộ dòng PRIME/CUM trước/sau không đổi.
Thêm Sender trùng bị từ chối và rollback, chỉ một Sender được Enable; thêm/xóa người nhận, đổi loại làm thay thứ tự rồi xóa vẫn đúng ID.
Lưu cấu hình và giữ nguyên khi khởi tạo lại; từ chối giờ sai; hiển thị lịch sử và đọc snapshot HTML.
Xác nhận requests chưa được nạp khi chỉ mở tab; Test Login success/failure với phản hồi mô phỏng; Customize Email vẫn khóa; đóng app một lần khi login đang chạy.



\[2026-09-16 13:52:12 (UTC+07:00)] Tab Machine Slot Yield
Chức năng và giao diện
Tab `🧪 Machine Slot Yield` nằm ngay sau Yield Slot. Nội dung gồm tiêu đề Machine Slot Yield, Log Folder, Target 15, Target 30, Continuous Fail và nút Save Target. Bộ lọc chung phía trên vẫn được giữ theo bố cục hiện tại của LI App nhưng không ảnh hưởng dữ liệu cấu hình trong tab này.
Target 15 mặc định 70.00%, Target 30 mặc định 75.00%; hai ô dùng phần trăm, cho phép 0–100 và bước chỉnh 0.1. Continuous Fail mặc định 3, chỉ nhận số nguyên từ 1 đến 9.999. Đây là số bản ghi FAIL liên tiếp dự kiến dùng làm điều kiện tạo Alarm ở bước tiếp theo; lần cập nhật này chỉ chuẩn bị và lưu cấu hình, chưa tạo Alarm.
Log Folder có thể chỉnh sửa trực tiếp. Trong lần đầu chưa có giá trị riêng, tab hiển thị Log Folder đã lưu tại Auto Import Prime Log nếu có. Khi bấm Save Target, giá trị đang hiển thị được lưu riêng cho Machine Slot Yield.
Database và cơ chế lưu
Bảng `machine\\\_slot\\\_yield\\\_config` có đúng một dòng `id=1`, gồm `log\\\_folder`, `target\\\_15`, `target\\\_30`, `continuous\\\_fail\\\_count`, `updated\\\_at`. Database mới và database LI schema 2 hiện có đều được tự động bổ sung bảng/dòng mặc định khi mở app; không tăng schema version và không cần tạo lại database.
Repository kiểm tra Target trong khoảng 0–100 và Continuous Fail từ 1 trở lên. Nút Save lưu đồng thời bốn cấu hình bằng `BEGIN IMMEDIATE`; nếu có lỗi thì rollback, không để trạng thái lưu dở. Chức năng Alarm tiếp theo có thể đọc trực tiếp cấu hình qua `MachineSlotYieldRepository.get\\\_config()`.
Tab được lazy-load sau khi database sẵn sàng nên không thêm thư viện nặng hoặc truy vấn lúc màn hình chính vừa xuất hiện. Chuyển sang tab lần đầu mới tạo giao diện và đọc cấu hình.
File bàn giao
File	Loại	Vai trò
`database/schema.py`	Sửa	Tự bổ sung bảng/dòng cấu hình Machine Slot Yield cho DB mới và DB schema 2 đang dùng.
`repositories/machine\\\_slot\\\_yield\\\_repository.py`	Thêm	Đọc, kiểm tra và lưu nguyên tử cấu hình; lấy Log Folder Auto Import làm giá trị ban đầu khi cần.
`ui/pages/machine\\\_slot\\\_yield\\\_page.py`	Thêm	Giao diện Log Folder, Target 15/30, Continuous Fail và Save Target.
`ui/pages/prime\\\_page.py`	Sửa	Đăng ký tab, tín hiệu mở tab và lazy-create trang cấu hình.
`controllers/prime\\\_controller.py`	Sửa	Chỉ cho mở/tải tab sau khi database đã sẵn sàng; tách khỏi bộ lọc thống kê.
`tests/test\\\_machine\\\_slot\\\_yield.py`	Thêm	Kiểm tra mặc định, lưu bền vững, singleton và thao tác tab/nút Save.
`read.md`, `changelog.txt`	Sửa, nối tiếp	Hướng dẫn và lịch sử thay đổi có thời gian.
Cách áp dụng và xác minh
Đóng LI App, giải nén gói cập nhật vào thư mục đang chứa `main.py`, rồi chép đè đúng các đường dẫn tương đối. Không xóa database. Mở app và chuyển sang Machine Slot Yield; chỉnh cấu hình rồi bấm Save Target. Đóng/mở lại app để kiểm tra giá trị được giữ.
Đã kiểm tra cú pháp toàn bộ project và kiểm tra tích hợp SQLite: tạo DB, mặc định 70/75/3, lưu lại 71.25/76.5/5, khởi tạo lặp vẫn giữ đúng dữ liệu, bảng luôn có một dòng và schema chính vẫn là version 2. Đã chạy `python -m unittest tests.test\\\_machine\\\_slot\\\_yield -v`: 2/2 kiểm thử đạt, gồm repository/schema và thao tác tab/nút Save trên Qt offscreen.

\[2026-09-16 15:50:48 (UTC+07:00)] Tab Alarm LI — tạo sau import PRIME
Cách cập nhật
Đóng LI App và các tác vụ auto import đang chạy trước khi chép file.
Giải nén LI\_Alarm\_Update.zip vào thư mục LIApp đang chứa main.py, chép đè đúng đường dẫn tương đối. Gói chỉ chứa 14 file mới/sửa, không chứa database hay toàn bộ project.
Mở lại app. Bảng slot\_fail\_alarm được tự động bổ sung; giữ schema chính version 2, không phải xóa/tạo lại database, không có thư viện mới cần cài.
Vào Machine Slot Yield, chỉnh Target 15, Target 30, Continuous Fail và bấm Save Target.
Import PRIME ngày cần xét, sau đó chọn From/To và mở tab Alarm. Với dữ liệu đã có từ trước khi cài bản này, cần import lại ngày muốn tạo Alarm; mở tab/Search chỉ đọc alarm đã lưu.
Nếu dùng bản EXE, cần build lại từ source đã cập nhật. Chép các file .py này không thay đổi một EXE đã đóng gói.
Quy tắc và nguồn dữ liệu
Lấy trực tiếp prime\_data, tất cả TEST\_COUNT; mỗi dòng là một test, không nhân với TEST\_COUNT, không loại retest theo SERIAL và không phụ thuộc Tier/CUM.
Xét riêng EQP/SLOT cho từng ngày có trong staging. Chỉ lấy test có DATE <= ngày đó; dữ liệu các ngày trước phải tồn tại trong database để dùng làm lịch sử.
Quy tắc 1: FAIL liên tiếp cùng MODEL và SCRAPCODE đạt continuous\_fail\_count; PASS, đổi Model hoặc đổi Scrapcode ngắt chuỗi. Chuỗi nối xuyên ngày, kéo dài tới cuối chuỗi và phải có ít nhất một test thuộc Alarm Date. Nhiều chuỗi đạt điều kiện vẫn gộp một dòng; các Scrapcode loại trùng, nối dấu phẩy.
Quy tắc 2/3: cửa sổ trượt 15/30 test cùng Model, bỏ qua Model khác. Duyệt từ mới về cũ, lấy cửa sổ đầu tiên có Yield < Target cho từng quy tắc. Nếu nhiều Model có cửa sổ vi phạm, lấy cửa sổ có điểm kết thúc mới nhất (TIME rồi id phân định khi trùng giây). Endpoint phải thuộc Alarm Date, phần đầu được lấy từ ngày trước. Không lấy vi phạm chỉ xảy ra hoàn toàn ở ngày trước.
Yield = PASS / 15 hoặc PASS / 30 \* 100; so sánh trước khi làm tròn. Thiếu mẫu hoặc không có cửa sổ vi phạm thì Yield tương ứng để trống. Giao diện hiển thị 2 chữ số thập phân.
Quy tắc 2/3 không đưa Scrapcode vào cột Scrap code. LOTID/Model lấy từ các chuỗi/cửa sổ gây alarm, loại trùng và nối dấu phẩy.
Fail comment gộp các quy tắc bằng dấu ' / '. Start/End lấy nguyên một cặp theo ưu tiên 1,2,3. Nếu có nhiều chuỗi quy tắc 1, lấy chuỗi vi phạm gần nhất. Không lấy min/max của cả ba quy tắc.
DATE/TIME đang lấy từ ENDTIME của log LI, do đó Start time là thời gian bản ghi đầu của chuỗi/cửa sổ đã chọn, không phải giờ bắt đầu chạy vật lý của máy.
Khóa duy nhất: Alarm Date + EQP + Slot. Ngày 16 nhập lại dữ liệu ngày 15 thì Alarm Date vẫn là ngày 15.
Import lại và bảo toàn thông tin
Sau khi thay PRIME, tính lại các điều kiện theo cấu hình đã Save trong cùng connection/transaction.
Đã có alarm cùng khóa và vẫn vi phạm bất kỳ quy tắc nào: giữ NGUYÊN TOÀN BỘ dòng, kể cả ID, Fail comment, Yield, Target, thời gian và toàn bộ thông tin người dùng. Không UPSERT/cập nhật dòng này. Vì vậy các trường máy phản ánh lúc alarm được tạo, không nhất thiết phản ánh lần nhập lại gần nhất.
Đã có alarm nhưng không còn vi phạm: xóa dòng, gồm cả ghi chú và trạng thái. Slot biến mất khỏi dữ liệu mới của ngày đó cũng bị xóa alarm. Nếu lần nhập sau lại vi phạm thì tạo alarm mới với trạng thái mặc định.
Chưa có alarm và vi phạm: tạo mới, Status='Chưa tiến hành'. Không dùng is\_active.
Chỉ đồng bộ Alarm Date của các ngày thực sự được thay trong staging. Sửa ngày trước không tự tính lại alarm ngày sau; muốn đánh giá lại ngày sau thì import lại ngày đó. Không thay đổi hành vi importer với staging rỗng/không tìm thấy file: dữ liệu cũ được giữ.
Lưu cấu hình không tự tính lại lịch sử. Lần import kế tiếp dùng cấu hình đã lưu tại lúc bắt đầu transaction ghi.
Nút Import PRIME, auto\_import\_main.py và auto\_import\_today\_main.py dùng cùng PrimeImportService/PrimeRepository nên cùng tạo alarm. Auto hôm qua bỏ qua ngày đã import thì không tính lại; Auto hôm nay mỗi lần ghi đè đều tính lại. Không cần sửa hai file auto import.
PRIME, Tier, Alarm và metadata import commit cùng nhau. Lỗi hoặc hủy trước commit sẽ rollback toàn bộ; khóa import hiện có vẫn được giữ đến khi kết thúc.
Giao diện và lưu kết quả
Thứ tự: No, Alarm Date, EQP, Slot, Fail comment, Start time, End time, Yield 15, Target 15, Yield 30, Target 30, Scrap code, LOTID, Model, Status, Date complete, Quick check result, Cal check result, Engineer action, Monitor day 1/2/3, Comment.
Alarm chỉ dùng From/To của bộ lọc chung. EQP, Slot, Model, Scrapcode và các cột khác lọc trực tiếp qua tiêu đề cột; không phụ thuộc Tier/Model/Scrapcode của tab thống kê.
Click tiêu đề cột để mở popup lựa chọn, áp dụng ngay, Close để đóng. Dấu chấm trên tiêu đề cho biết có điều kiện lọc. Clear column filters bỏ điều kiện. No đánh số theo các dòng đang hiển thị.
Nhấp đúp ô Status để chọn Chưa tiến hành (đỏ nhạt), Đang thực hiện (vàng), Đã hoàn thành (xanh). Chuyển sang hoàn thành tự ghi Date complete; chọn lại cùng trạng thái không đổi giờ; chuyển sang trạng thái khác xóa Date complete.
Nhấp đúp hoặc F2 tại các ô kết quả xử lý/Comment để nhập; Enter hoặc kết thúc chỉnh sửa để lưu. Các trường máy và Date complete không sửa trực tiếp. Nội dung dài xem đầy đủ bằng tooltip.
Chỉ cập nhật giá trị hiển thị sau khi commit. Nếu người khác đã thay đổi row\_version, tải dòng mới nhất và báo thay đổi của bạn chưa lưu. Database đang bị ghi thì báo chưa lưu để thử lại, không tự ghi đè hoặc retry.
Search/chuyển vào tab luôn đọc lại database để nhận cập nhật từ auto import hoặc máy khác. Import trong app xong, nếu đang ở Alarm thì tự tải lại sau khi bộ lọc sẵn sàng. Đóng app đợi worker đang lưu hoàn tất.
Kiến trúc và hiệu năng
Engine Python thuần; không thêm pandas/matplotlib vào startup hoặc vào thuật toán Alarm.
Truy vấn từng slot dùng index idx\_prime\_slot\_time(EQP,SLOT,DATE,TIME) có sẵn; EXPLAIN QUERY PLAN xác nhận dùng index, không thêm index trùng lặp. Index UNIQUE của bảng alarm cũng phục vụ lọc theo khoảng Alarm Date.
Duyệt cursor lịch sử giảm dần, giữ tối đa 30 test cho mỗi Model xuất hiện ngày đích, dừng khi đã xét hết cửa sổ có endpoint ngày đích và đã đóng chuỗi FAIL nối sang ngày trước. Nếu Model thiếu mẫu thì có thể phải đọc hết lịch sử sẵn có.
evidence\_json lưu bằng chứng các chuỗi/cửa sổ được chọn trong dòng mới để tra cứu; không phụ thuộc khóa ngoại prime\_data.id vốn thay đổi khi import lại.
row\_version và ID AUTOINCREMENT ngăn editor cũ ghi lên alarm đã bị xóa rồi tạo mới.
File liên quan (gói cập nhật)
`domain/alarm.py` — Thêm: định nghĩa 23 cột, trạng thái và các trường được chỉnh sửa.
`database/alarm\\\_schema.py` — Thêm: bảng slot\_fail\_alarm, khóa duy nhất ngày/máy/slot, version chống ghi đè.
`database/schema.py` — Sửa: bổ sung bảng Alarm cho database LI schema 2 mới/cũ.
`services/alarm\\\_builder.py` — Thêm: xét ba quy tắc xuyên ngày, cửa sổ cùng Model và chọn bằng chứng đầu tiên từ mới về cũ.
`repositories/alarm\\\_repository.py` — Thêm: đồng bộ alarm cùng transaction PRIME, truy vấn theo ngày và lưu kết quả xử lý.
`repositories/prime\\\_repository.py` — Sửa: giữ thứ tự staging ổn định, tính Alarm trước commit trong mọi đường import PRIME.
`workers/alarm\\\_worker.py` — Thêm: đọc/lưu Alarm trong QThread do controller quản lý.
`ui/pages/alarm\\\_page.py` — Thêm: bảng 23 cột, lọc từng cột, dropdown Status và nhập kết quả xử lý.
`ui/pages/prime\\\_page.py` — Sửa: đăng ký tab Alarm ngay sau Machine Slot Yield, tạo giao diện khi mở.
`controllers/prime\\\_controller.py` — Sửa: định tuyến Search/chuyển tab, tải sau import, lưu bằng worker và đóng app an toàn.
`tests/test\\\_alarm.py` — Thêm: 14 kiểm thử quy tắc và transaction import trên SQLite.
`tests/test\\\_alarm\\\_gui.py` — Thêm: 2 kiểm thử GUI/worker/chỉnh sửa/đóng app trên Qt offscreen.
`read.md`, `changelog.txt` — nối nội dung mới và thời gian, giữ nguyên nội dung cũ.
Kiểm tra đã thực hiện
`QT\\\_QPA\\\_PLATFORM=offscreen PYTHONPATH=.:tests python -m unittest tests.test\\\_alarm tests.test\\\_alarm\\\_gui tests.test\\\_auto\\\_import\\\_today tests.test\\\_machine\\\_slot\\\_yield -v`: 20/20 đạt.
Bao gồm retest, cửa sổ xuyên ngày, Model xen kẽ, cửa sổ đầu tiên thay vì thấp nhất, không dùng tương lai, ưu tiên thời gian, gộp ba quy tắc, bảo toàn nguyên dòng, xóa/tạo lại, slot biến mất, rollback sau bước Alarm, database bận, xung đột hai người sửa, Date complete, lọc và lưu đúng ID trên GUI, đóng app trong lúc lưu.
Kiểm tra cú pháp các file mới/sửa và quan sát ảnh giao diện Qt offscreen. Mở bản sao database đi kèm để bổ sung schema thành công (database đi kèm không có dòng PRIME/CUM); kiểm thử riêng database có dữ liệu xác nhận khởi tạo lặp không mất alarm.
Một kiểm thử cũ `tests.test\\\_slot\\\_tab\\\_refresh` báo độ rộng cột Yield Slot 80 >= 64; chạy trên cả source gốc và source cập nhật đều cùng lỗi, không sửa chức năng ngoài phạm vi Alarm.
Môi trường kiểm tra Python 3.12 + PyQt5 trên Linux/offscreen; chưa chạy EXE Windows hoặc đo hiệu năng trực tiếp trên mạng nội bộ của nhà máy.

\[2026-09-16 17:47:56 (UTC+07:00)] Cập nhật lại các trường máy của Alarm còn vi phạm khi import lại
Quy định mới thay thế hướng dẫn trước đây về "giữ nguyên toàn bộ dòng":
Import lại ngày D: tính lại từ PRIME theo cấu hình Machine Slot Yield đã Save; quy tắc tìm chuỗi/cửa sổ không đổi.
Alarm đã có, còn vi phạm: UPDATE chính dòng đó, giữ ID; cập nhật Fail comment, Start time, End time, Yield 15, Target 15, Yield 30, Target 30, Scrap code, LOTID, Model theo kết quả mới. Cửa sổ không vi phạm được xóa Yield cũ về NULL (hiển thị trống).
Alarm Date, EQP, Slot là khóa nhận diện dòng và không đổi; No là số thứ tự giao diện.
Từ Status trở đi giữ nguyên tuyệt đối: Status, Date complete, Quick check result, Cal check result, Engineer action, Monitor day 1/2/3, Comment.
Đồng bộ bằng chứng evidence\_json và ngưỡng continuous\_fail\_count\_used; cập nhật updated\_at, tăng row\_version để ngăn một editor cũ ghi đè dòng vừa được tính lại. created\_at giữ nguyên.
Alarm không còn vi phạm bất kỳ quy tắc nào: xóa. Chưa có alarm và có vi phạm: tạo mới. Tất cả nằm cùng transaction import PRIME; có lỗi rollback cả PRIME và alarm.
Không tự tính lại chỉ khi bấm Save Target. Cần import lại ngày muốn cập nhật. Không thay đổi các ngày không được import.
Ví dụ đã xác minh trên bản sao database LIApp (12): AI-H911 / Slot 47 / 08-09-2026 sau import lại với Target 50/70 có Yield 15 trống, Yield 30=66.67%, Fail comment='Yield 30 < 70.00%', Start=2026-09-07 21:23:48, End=2026-09-08 11:57:00. Toàn bộ trường xử lý của 14 alarm giữ nguyên.
File thay đổi:
repositories/alarm\_repository.py: thay nhánh giữ nguyên bằng UPDATE danh sách trường máy tường minh; không đụng các cột xử lý.
tests/test\_alarm.py: cập nhật kiểm thử bảo toàn trường xử lý; thêm kiểm thử target mới, xóa Yield cũ, đổi Model/LOTID, phát hiện editor cũ sau import.
read.md, changelog.txt: nối nội dung và thời gian, không bỏ nội dung cũ.
Cách áp dụng: đóng ứng dụng và tác vụ import, chép đè các file trong ZIP vào thư mục chứa main.py. Không xóa database. Mở lại, Save Target và import lại ngày cần cập nhật; nếu dùng EXE thì build lại.
Kiểm tra: 15 kiểm thử nghiệp vụ/import SQLite đạt; chạy import thực tế trên bản sao 42.709 dòng PRIME xác nhận 14 alarm giữ nguyên ID và toàn bộ trường xử lý. Kiểm tra cú pháp file sửa. Không sửa database gốc; chưa chạy lại kiểm thử GUI vì môi trường hiện tại không có PyQt5; không thay đổi file GUI trong bản này.

\[2026-09-16 18:41:52 (UTC+07:00)] Customize Email — preview Alarm LI
Cách cập nhật và sử dụng
Chép các file trong gói vào đúng đường dẫn tương đối của project LIApp (14), cho phép ghi đè file trùng tên.
Mở lại ứng dụng. Bảng mail\_template được bổ sung tự động, không cần xóa database.
Vào Send Mail > Customize Email. Dialog theo mẫu Aging gồm Subject, Heading, Body Preview (chỉ đọc), Closing, Close và Save.
Save chỉ lưu Subject/Heading/Closing vào database; Subject không được trống. Đóng không lưu các chỉnh sửa chưa bấm Save.
Mỗi lần mở lại, preview đọc dữ liệu mới từ database, chạy ở worker để tránh chặn giao diện khi đọc alarm.
Quy tắc nội dung
Lấy alarm theo alarm\_date của ngày hiện tại và ngày trước đó theo ngày máy chạy ứng dụng, không theo bộ lọc đang chọn. Ví dụ ngày 16 lấy Alarm Date 16 và 15. Không lọc Status, Model, EQP, Tier hay lịch sử gửi.
Nhóm ngày mới trước với dòng `Alarm ngày: dd/mm/yyyy`; ngày không có dữ liệu hiện `Không có alarm.`
Mỗi nhóm slot hiện EQP, Slot và Alarm Type. Không có Chamber.
FAIL liên tiếp: dùng ngưỡng continuous\_fail\_count\_used lưu trong alarm (mặc định 3); bảng gồm File Date, Date time, Model, Lot ID, Scrap code, Fail qty. Lấy từng chuỗi bằng chứng với đúng Model/Scrapcode, kể cả log xuyên ngày; không lấy FAIL ở khoảng trống giữa các chuỗi.
Yield 15 hoặc Yield 30 hoặc cả hai: giữ Model, Lot ID, thời gian cửa sổ và đủ bốn cột Yield 15, Target 15, Yield 30, Target 30. Dùng yield/target đã lưu trong alarm, không tự tính lại bằng cấu hình mới.
Nếu cả hai cửa sổ vi phạm, mỗi cửa sổ có một dòng riêng để thể hiện đúng Model/thời điểm (chúng có thể khác nhau). Ô Yield không thuộc cửa sổ đó hiển thị —; không coi là 0%.
Nếu có cả chuỗi FAIL và Yield, hiển thị đầy đủ hai phần trong cùng nhóm slot.
Body tự tạo từ alarm và evidence\_json; không thay đổi alarm, trường theo dõi hay dữ liệu PRIME. Chức năng gửi mail chưa được triển khai trong thay đổi này.
Chỉ có ảnh cửa sổ Aging trong đầu vào; bảng Yield được dựng theo mô tả bốn cột và Model.
File liên quan
File	Thay đổi / chức năng
database/mail\_schema.py	Sửa: bổ sung bảng mail\_template và mẫu mặc định LI, không ghi đè mẫu đã lưu
ui/pages/send\_mail\_page.py	Sửa: kích hoạt Customize Email và quản lý vòng đời dialog
ui/mail\_template\_dialog.py	Thêm: giao diện Aging, lưu mẫu, bảo vệ QThread khi Close/X/Escape
workers/mail\_template\_preview\_worker.py	Thêm: đọc mẫu và alarm hôm nay/hôm qua ở nền
repositories/mail\_template\_repository.py	Thêm: đọc/lưu mẫu, truy vấn alarm và chi tiết chuỗi FAIL
services/mail\_content\_builder.py	Thêm: HTML theo ngày, slot, loại alarm; escape nội dung log
tests/test\_mail\_template.py	Thêm: kiểm thử SQLite và nội dung HTML
read.md, changelog.txt	Nối nội dung cập nhật vào tài liệu cũ
Kiểm tra
Chạy `python -m unittest tests.test\\\_mail\\\_template -v` tại thư mục gốc project: 4 test methods thành công (bao gồm các subtest Yield riêng, cả hai, kết hợp FAIL).
Kiểm tra biên dịch Python của toàn bộ file chức năng thay đổi thành công.
Chưa chạy kiểm tra trực quan Qt/Windows do môi trường kiểm tra không có PyQt5; chưa kết nối hay gửi email thật.



2026-09-17 09:53:35 (UTC+07:00) — Gửi mail tự động LI bằng Task Scheduler
Cơ chế
Thêm entry point `auto\\\_send\\\_mail\\\_main.py`, chạy độc lập, không mở PyQt5 và không tải pandas/matplotlib.
Đọc Enable và Send Time đã lưu ở tab Send Mail. OFF hoặc chưa đến giờ: ghi SKIP và thoát mã 0. Đến giờ: kiểm tra alarm hôm nay và 3 ngày trước, giống bản Aging đính kèm. Ví dụ 17/09 kiểm tra 17, 16, 15, 14/09.
Đọc `slot\\\_fail\\\_alarm` đã lưu, không tự import PRIME hoặc tính lại alarm. Nên đặt task gửi sau task import. Không phụ thuộc bộ lọc GUI, không lọc mã scrap ưu tiên hoặc Status.
Chống gửi trùng theo `(alarm\\\_date, eqp, slot)` trong `mail\\\_slot\\\_send\\\_history`. Cùng slot nhưng ngày khác hoặc EQP khác là khóa khác. Slot đã gửi trong cùng ngày vẫn bị bỏ qua dù Model, target hoặc loại alarm thay đổi, đúng cơ chế Aging.
Gộp các slot chưa gửi thành một mail, nhóm theo ngày. Subject/Heading/Closing lấy từ Customize Email. Body dùng mẫu LI hiện có: không Chamber, giữ Model, bằng chứng FAIL và Yield/Target 15/30.
Sender được Enable, Receiver và CC lấy từ database. Đăng nhập/gửi qua giao thức mail nội bộ giống Aging; không ghi mật khẩu vào log.
Khóa `mail\\\_send\\\_lock` trên database chung chặn các task chạy đồng thời; tự hết hạn sau 5 phút nếu tiến trình dừng bất thường. Kiểm tra token và gia hạn ngay trước khi gửi để tránh dùng khóa cũ sau bước dựng nội dung lâu.
Chỉ khi hệ thống mail trả thành công mới lưu snapshot email và khóa slot trong cùng transaction. Mail History hiện có xem được lịch sử này. Lỗi: không ghi lịch sử Success, mã thoát 1, ghi ERROR/TRACEBACK.
Ghi nối tiếp `log/auto\\\_send\\\_mail\\\_log.txt` cạnh file chạy hoặc EXE: START, CONFIG, ngày kiểm tra, slot bỏ qua, đăng nhập, kết quả gửi, lỗi và END. Không có alarm hoặc tất cả đã gửi: SKIP, mã 0.
Preview Customize Email vẫn là hôm nay + hôm qua. Nút Send Mail thủ công vẫn giữ trạng thái hiện tại; đợt này triển khai tác vụ tự động riêng.
File bàn giao
File	Loại	Chức năng
auto\_send\_mail\_main.py	Thêm	Entry point, Enable/giờ gửi, đường dẫn DB, log và exit code
services/mail\_send\_job\_service.py	Thêm	Kiểm tra alarm 4 ngày, lọc trùng, dựng mail, gọi gửi, lưu lịch sử
services/mail\_service.py	Sửa	Bổ sung gửi TO/CC qua session, dùng giao thức Aging
repositories/mail\_send\_repository.py	Sửa	Khóa gửi, lọc slot đã gửi, lưu lịch sử nguyên tử; giữ hàm đọc Mail History
database/mail\_schema.py	Sửa	Thêm mail\_slot\_send\_history (slot 1–48) và mail\_send\_lock, không xóa dữ liệu
ui/widgets/auto\_send\_mail\_scheduler\_panel.py	Sửa	Thông báo lưu cấu hình khớp tác vụ tự động mới
Auto\_Send\_Mail.spec	Thêm	Build EXE riêng LI\_Auto\_Send\_Mail
read.md, changelog.txt	Sửa	Nối tiếp nội dung cũ và ngày giờ cập nhật
Cài đặt
Chép các file vào đúng đường dẫn tương đối trong project LI, ghi đè file cũ tương ứng. Không cần xóa hay tạo lại DB. Lần mở app/chạy task sẽ bổ sung hai bảng mới.
Trong tab Send Mail: cấu hình một Sender được Enable và mật khẩu, chọn Receiver/CC; lưu mẫu Customize Email; bật Auto Send Mail, chọn giờ và Save.
Task Scheduler dùng đúng Python có thư viện `requests` của ứng dụng:
Program/script: đường dẫn đầy đủ tới `python.exe`.
Add arguments (ví dụ): `"D:\\\\LIApp\\\\auto\\\_send\\\_mail\\\_main.py" --database "D:\\\\LIApp\\\\database\\\\li\\\_app.db"`
Start in: `D:\\\\LIApp` (đổi tất cả đường dẫn theo máy).
Trigger theo lịch cần dùng. Nếu muốn lấy thêm alarm mới trong ngày, cho task lặp lại; những lần sau giờ cấu hình vẫn chạy và chỉ gửi slot chưa gửi.
Trong Settings chọn không tạo instance mới nếu task đang chạy. Tài khoản chạy task phải truy cập được DB, thư mục ghi log và hệ thống mail nội bộ.
Với DB dùng chung, truyền đường dẫn UNC thực tế qua `--database`, giống DB mà GUI đang dùng. Không dựa vào ổ mạng đã map ở phiên đăng nhập khác.
Thứ tự đường dẫn DB: `--database` > biến môi trường `LI\\\_DB\\\_PATH` > `config.paths.DATABASE\\\_PATH`. Không tìm thấy file DB thì báo lỗi, không tạo DB rỗng do gõ sai đường dẫn. Ngày/giờ theo máy chạy task.
Build tùy chọn tại thư mục gốc project: `pyinstaller --clean Auto\\\_Send\\\_Mail.spec`. Dùng `dist\\\\LI\\\_Auto\\\_Send\\\_Mail.exe` làm Program/script, arguments `--database "đường dẫn DB LI"`. EXE riêng không cần mở GUI. Nếu không truyền DB, cần bố trí DB/config đúng vị trí cạnh EXE; nên truyền rõ `--database`.
Kết quả task: 0 = gửi thành công hoặc bỏ qua bình thường; 1 = lỗi. Xem log để phân biệt. Lưu Enable/giờ trong GUI không tự tạo Windows Task Scheduler.
Kiểm chứng và giới hạn
Đạt 11 kiểm thử với SQLite tạm: 4 ngày, trùng/ngày khác/slot mới, không alarm, lỗi login/gửi, khóa, mất khóa, rollback lịch sử, nâng cấp schema, Enable/giờ gửi và exit code.
Kiểm tra payload tiếng Việt TO/CC và phản hồi lỗi/timeout bằng HTTP giả lập; không gọi hệ thống mail thật. Kiểm tra biên dịch các file Python bàn giao.
Chưa chạy GUI Windows, chưa build EXE hoặc gửi mail thật trong mạng nội bộ.
Giống Aging, HTTP gửi mail và SQLite không cùng một transaction: nếu server đã nhận nhưng timeout/mất điện, hoặc đã gửi thành công mà lưu lịch sử lỗi, lần sau có thể gửi lại. Trường hợp lưu lịch sử lỗi có log CRITICAL để đối chiếu mail thực tế trước lần chạy tiếp theo. Cơ chế này không bảo đảm exactly-once khi sự cố xảy ra giữa gửi và lưu lịch sử.

2026-09-17 11:06:47 (UTC+07:00) — Điều chỉnh nội dung email alarm
Ẩn toàn bộ nhóm ngày không có alarm, gồm tiêu đề Alarm ngày và dòng Không có alarm.
Đổi tên Yield 15 thành “Fail hiệu suất thấp 15 lần liên tục”; Yield 30 thành “Fail hiệu suất thấp 30 lần liên tục”. Nếu vi phạm cả hai, hiển thị cả hai tên nối bằng “và”.
Bảng hiệu suất bỏ cột Quy tắc và Lot ID, còn Start time, End time, Model, Yield 15, Target 15, Yield 30, Target 30. Giữ dòng riêng cho mỗi cửa sổ bằng chứng.
Áp dụng chung cho Customize Email và mail tự động; không đổi ngưỡng/cách tính alarm, chống trùng, hoặc bảng chi tiết FAIL liên tiếp.
File sửa: services/mail\_content\_builder.py. Tài liệu nối tiếp: read.md, changelog.txt.

2026-09-17 11:23:03 (UTC+07:00) — Export danh sách Alarm đang hiển thị ra Excel
Thêm nút `Export Excel` bên phải `Clear column filters` trong tab Alarm, giao diện và cách chọn nơi lưu giống Aging.
File Excel chỉ chứa các dòng đang hiển thị sau khi áp dụng tất cả bộ lọc cột. Cột No được đánh lại theo thứ tự hiện tại của bảng.
Xuất đủ 23 cột theo đúng thứ tự bảng Alarm LI; tiêu đề Excel không chứa ký hiệu bộ lọc `▾` hoặc `●`.
Tên mặc định: `List of Alarm from <ngày đầu> - <ngày cuối>.xlsx`; tự thêm đuôi `.xlsx` khi thiếu.
Sheet `List of Alarm` có tiêu đề in đậm, nền xám, Auto Filter, cố định dòng đầu và chiều rộng theo nội dung từng cột.
Snapshot dữ liệu được chụp trước khi chọn nơi lưu; worker nền ghi file nên không chặn giao diện. `openpyxl` chỉ được tải khi người dùng bấm Export.
Nút Export bị khóa khi đang tải/lưu dữ liệu, đang xuất hoặc bảng không có dòng; sau khi hoàn tất sẽ báo đường dẫn file hoặc lỗi.
Chuỗi bắt đầu bằng dấu `=` được lưu dưới dạng text để không bị Excel hiểu thành công thức.
File ứng dụng cần sửa: `ui/pages/alarm\\\_page.py`. Tài liệu nối tiếp: `read.md`, `changelog.txt`.
Kiểm tra worker tạo workbook thành công và mã Python biên dịch thành công. Môi trường kiểm tra hiện tại không có PyQt5 nên chưa chạy tự động toàn bộ GUI test.

2026-09-17 11:29:03 (UTC+07:00) — Điều chỉnh cột hiển thị tab Alarm
Ẩn cột `Yield 15` và `Yield 30` khỏi bảng Alarm. Dữ liệu vẫn được lưu trong database và vẫn dùng cho nội dung email; không thay đổi schema hoặc logic tính alarm.
Thu hẹp `Start time`, `End time`, `Target 15`, `Target 30`, `Model` và `Status`; vẫn bảo đảm tiêu đề và thời gian hiển thị đủ.
Căn giữa nội dung của toàn bộ cột trong bảng Alarm.
Export Excel chỉ lấy các cột đang hiển thị nên cũng bỏ `Yield 15` và `Yield 30`; các ô dữ liệu trong Excel được căn giữa.
Giữ nguyên chỉ số cột nội bộ để delegate Status, bộ lọc và lưu dữ liệu không bị lệch.
File ứng dụng cần sửa: `ui/pages/alarm\\\_page.py`. Tài liệu nối tiếp: `read.md`, `changelog.txt`.
Kiểm tra tạo workbook, danh sách cột hiển thị và biên dịch Python thành công. Môi trường hiện tại không có PyQt5 nên chưa chạy toàn bộ GUI test tự động.

2026-09-17 12:37:55 (UTC+07:00) — Đổi cột Yield/Target hiển thị trong tab Alarm
Hiện lại `Yield 15` và `Yield 30` trong bảng Alarm.
Ẩn `Target 15` và `Target 30` khỏi bảng Alarm. Dữ liệu Target vẫn giữ trong database và tiếp tục dùng cho nội dung email.
Export Excel đi theo cột đang hiển thị: có Yield 15/30 và không có Target 15/30.
Giữ nguyên căn giữa, độ rộng các cột khác, bộ lọc, Status và logic lưu alarm.
File ứng dụng cần sửa: `ui/pages/alarm\\\_page.py`. Tài liệu nối tiếp: `read.md`, `changelog.txt`.
Kiểm tra biên dịch Python và cấu hình chỉ số cột thành công.

2026-09-17 12:46:18 (UTC+07:00) — Lựa chọn PASS/FAIL và khóa Monitor trong tab Alarm
`Quick check result` và `Cal check result` dùng combobox không cho nhập chữ, chỉ có hai lựa chọn `PASS` và `FAIL`.
Ô `PASS` có nền xanh nhạt; ô `FAIL` có nền đỏ nhạt. Dòng chưa có kết quả vẫn để trống và không tô màu.
Repository kiểm tra lại giá trị trước khi ghi database; giá trị ngoài PASS/FAIL bị từ chối ngay cả khi gọi ngoài giao diện.
`Monitor day 1`, `Monitor day 2`, `Monitor day 3` được thu hẹp từ 180 px xuống 115 px và chuyển thành chỉ đọc, không thể double-click hoặc gõ để sửa.
Dữ liệu Monitor đã có trong database vẫn được hiển thị, lọc, export và bảo toàn khi import lại. Không thay đổi schema hoặc xóa dữ liệu cũ.
`Engineer action` và `Comment` vẫn cho nhập nội dung; `Status` vẫn dùng ba lựa chọn hiện tại.
File ứng dụng sửa: `domain/alarm.py`, `repositories/alarm\\\_repository.py`, `ui/pages/alarm\\\_page.py`. Tài liệu nối tiếp: `read.md`, `changelog.txt`.
Đã chạy thành công 15 kiểm thử nghiệp vụ Alarm và kiểm tra biên dịch Python. Môi trường hiện tại không có PyQt5 nên chưa chạy toàn bộ GUI test tự động.



2026-09-17 13:00:00 (UTC+07:00) — Launcher tự cập nhật LI Yield
Cơ chế hoạt động
Người dùng luôn mở `LI\\\_Yield\\\_Launcher.exe` tại thư mục dùng chung. Launcher không chạy chương trình trực tiếp qua mạng.
Launcher đọc `package/version.txt` và so sánh với `%LOCALAPPDATA%\\\\\\\\LI\\\_Yield\\\\\\\\App\\\\\\\\version.txt`.
Khi version khác, chưa có bản local hoặc package local thiếu EXE/`\\\_internal`, Launcher dùng Robocopy tải toàn bộ `package` vào `App.new`.
Chỉ sau khi kiểm tra đủ `LI\\\_Yield.exe`, `\\\_internal` và version khớp, `App.new` mới được thay thành `App`. Bản cũ được giữ tạm ở `App.backup` và được phục hồi nếu đổi package lỗi.
Khi không có cập nhật, Launcher mở ngay bản local để giảm thời gian tải thư viện qua mạng.
Launcher truyền biến `LI\\\_DB\\\_PATH` cho chương trình local, vì vậy toàn bộ người dùng vẫn đọc/ghi chung file `database\\\\\\\\li\\\_app.db` trên server; database không bị copy xuống máy.
Mỗi máy chỉ chạy một tiến trình Launcher tại một thời điểm. Nếu `LI\\\_Yield.exe` đang mở, Launcher không cập nhật đè lên file đang dùng.
LI không dùng `allow\\\_create\\\_database.flag`. Nếu `database\\\\\\\\li\\\_app.db` không tồn tại hoặc mất kết nối, Launcher dừng và báo lỗi để tránh tạo nhầm database rỗng.
Cấu trúc thư mục triển khai trên server

```text
LI Yield Deploy\\\\\\\\
├── LI\\\_Yield\\\_Launcher.exe
├── database\\\\\\\\
│   └── li\\\_app.db
└── package\\\\\\\\
    ├── LI\\\_Yield.exe
    ├── version.txt
    └── \\\_internal\\\\\\\\
```

Build và phát hành
Tại thư mục project, chạy `pyinstaller --clean LI\\\_Yield.spec` để tạo `dist\\\\\\\\LI\\\_Yield`.
Chép toàn bộ nội dung trong `dist\\\\\\\\LI\\\_Yield` vào thư mục `package` trên server.
Chép `version.txt` vào `package` và tăng nội dung version ở mỗi lần phát hành, ví dụ `1.0.0` thành `1.0.1`.
Chạy `pyinstaller --clean LI\\\_Yield\\\_Launcher.spec` để tạo `dist\\\\\\\\LI\\\_Yield\\\_Launcher.exe`, rồi đặt EXE này ở thư mục gốc như sơ đồ trên.
Tạo shortcut cho người dùng trỏ tới `LI\\\_Yield\\\_Launcher.exe`. Không tạo shortcut trực tiếp tới EXE trong `package`.
File và trách nhiệm
File	Loại	Chức năng
`launcher\\\_main.py`	Thêm	So sánh version, tải package an toàn, truyền DB server và mở bản local
`LI\\\_Yield\\\_Launcher.spec`	Thêm	Build Launcher dạng một EXE không có console
`LI\\\_Yield.spec`	Thêm	Build ứng dụng dạng onedir để Launcher copy xuống máy
`version.txt`	Thêm	Version mẫu; phải đặt trong `package` và tăng khi phát hành
`config/paths.py`	Sửa	Ưu tiên DB từ `LI\\\_DB\\\_PATH`, vẫn giữ đường dẫn mặc định khi chạy source
`main.py`	Sửa	Đặt application/organization name là LI Yield
`ui/main\\\_window.py`	Sửa	Đổi tiêu đề cửa sổ thành LI Yield
Kiểm tra và xử lý lỗi
Log Launcher nằm tại `%LOCALAPPDATA%\\\\\\\\LI\\\_Yield\\\\\\\\logs\\\\\\\\launcher.log`.
Robocopy trả mã 0–7 được coi là thành công; mã từ 8 trở lên dừng cập nhật và giữ bản hiện tại.
Nếu mất mạng, thiếu database, thiếu file package hoặc `version.txt` rỗng, Launcher báo lỗi và không mở ứng dụng với dữ liệu sai.
Thư mục `App.new` chỉ là bản đang tải; `App.backup` là bản cũ trong lúc thay version. Launcher tự dọn sau khi cập nhật thành công.



Bổ sung 17/09/2026 — Slot Fail History từ bảng Alarm
Cài đặt bản bổ sung
Đóng LI App và các tiến trình auto import đang dùng bộ code cần cập nhật.
Giải nén gói `LIApp\\\_20\\\_SlotFailHistory\\\_Patch.zip`, chép các file trong thư mục `LIApp` vào thư mục ứng dụng tương ứng, giữ đúng đường dẫn con. Gói chỉ chứa file thay đổi/file mới; không có database, log hoặc cấu hình đường dẫn.
Mở lại app. Index mới được tạo tự động bằng `CREATE INDEX IF NOT EXISTS`; không cần xóa database hay chạy SQL thủ công. Lần khởi động đầu có thể lâu hơn do tạo index.
Vào Alarm, chọn ngày và Search. Click một ô từ No đến Model để mở lịch sử. Click Yield 15 hoặc Yield 30 sẽ chọn sẵn quy tắc tương ứng nếu alarm có bằng chứng quy tắc đó.
Alarm được import sau bản cập nhật sẽ có snapshot đầy đủ. Với alarm cũ, xem thông báo nguồn dữ liệu trong cửa sổ. Nếu thiếu/mất dữ liệu đối chiếu, import lại ngày alarm từ log gốc rồi Search lại. Việc import lại vẫn cập nhật alarm theo cơ chế hiện có, không phải thao tác chỉ bổ sung lịch sử.
Giao diện và cột dữ liệu
Tiêu đề: `Slot Fail History: EQP: <EQP> SLOT: <slot>`, không có Chamber.
Cột cửa sổ	Nguồn PRIME	Ghi chú
Date	DATE	Giữ định dạng YYYYMMDD
Time	TIME	HH:mm:ss
Model	MODEL	Model của từng test
Lot ID	LOTNO	Không lấy chuỗi LOTID tổng hợp trên dòng alarm
Result	RESULT	PASS màu xanh, FAIL màu đỏ
Scrapcode	SCRAPCODE	NULL hiển thị trống
Test count	TEST\_COUNT	Giữ nguyên, kể cả 0; không cộng 1 và không lọc chỉ test đầu
Fail qty (QTY)	QTY	Giá trị QTY gốc của từng dòng, kể cả dòng PASS
Bộ đếm trên bảng phân biệt tổng test, số dòng FAIL và tổng QTY của các dòng FAIL. Cột QTY hiển thị giá trị gốc; tổng FAIL QTY chỉ cộng RESULT='FAIL'. Bảng chỉ đọc, thứ tự mới về cũ theo DATE, TIME, id; không gộp các dòng trùng giây.
Các cột Status, Date complete, Quick check result, Cal check result, Engineer action, Monitor day 1/2/3 và Comment không mở lịch sử khi click. Cơ chế sửa tay hiện có được giữ nguyên. Click được map từ proxy về source model, nên sau lọc hoặc sắp xếp vẫn đọc đúng ID alarm.
Cách xác định chuỗi và giới hạn nghiệp vụ
Không chạy lại quy tắc bằng cấu hình hiện tại khi click. Cửa sổ đọc `slot\\\_fail\\\_alarm.evidence\\\_json` của đúng ID và row\_version đã chọn.
Quy tắc FAIL liên tiếp: dùng `continuous\\\_fail\\\_count\\\_used` đã lưu khi tạo alarm, mặc định 3; chỉ các test FAIL liên tiếp cùng model và scrapcode. Mỗi đoạn vi phạm có một lựa chọn riêng nếu alarm chứa nhiều đoạn.
Giữ nguyên engine của LIApp (20): engine duyệt mới về cũ và lưu cả đoạn FAIL đủ ngưỡng. Bản này không đổi thuật toán phát hiện, Start/End time tổng, thứ tự ưu tiên hoặc số alarm. Đoạn dài hơn ngưỡng N được hiển thị bằng N test liên tiếp mới nhất kết thúc tại End time của đoạn đó; cửa sổ ghi rõ tổng chiều dài đoạn gốc. Đây không phải N test đầu tiên theo chiều thời gian tăng dần. Ví dụ đoạn 10 FAIL liên tiếp, ngưỡng 3: hiển thị test 10, 9, 8 và chú thích đoạn gốc 10 test. Start time trên dòng alarm vẫn là đầu đoạn gốc.
Yield 15/30: hiển thị nguyên cửa sổ 15/30 test được engine lưu, gồm PASS và FAIL. Không lọc riêng FAIL vì như vậy sẽ làm sai mẫu số. Giữ nguyên quy tắc cùng model, có thể nối xuyên ngày và bỏ qua model khác như engine hiện có.
Một alarm có nhiều quy tắc: dropdown cho phép xem từng quy tắc/đoạn riêng, không trộn chuỗi hoặc bỏ bớt dòng trùng giữa các quy tắc.
Snapshot mới lưu id, DATE, TIME, MODEL, LOTNO, RESULT, SCRAPCODE, TEST\_COUNT, SERIAL, QTY từ PRIME. ID và SERIAL chỉ dùng xác định thứ tự/đối chiếu; không hiển thị thêm cột.
Snapshot được ghi trong chính transaction import PRIME/Alarm. Import lỗi thì rollback cùng nhau. Nếu chỉ dữ liệu PRIME thay đổi mà alarm chưa được tính lại, snapshot vẫn thể hiện bằng chứng của alarm đã lưu. Khi import tính lại alarm, snapshot cũng cập nhật theo alarm, không phải kho lưu mọi phiên bản alarm trong quá khứ.
Tương thích alarm cũ
Không sửa hoặc dựng lại tất cả alarm khi khởi động app.
Rule 1 cũ chưa có tests: truy vấn PRIME theo EQP, SLOT và khoảng DATE/TIME đã lưu của từng đoạn, ORDER BY DATE DESC, TIME DESC, id DESC, LIMIT N. Kiểm tra số lượng, model, scrapcode, RESULT và mốc kết thúc trước khi hiển thị. Có thông báo đây là dữ liệu dựng từ PRIME hiện tại. Bản cũ không lưu ID từng test nên không thể bảo đảm phục hồi tuyệt đối phiên bản lịch sử nếu PRIME đã bị thay đổi; import lại ngày alarm để có snapshot mới.
Rule 15/30 cũ đã có tests nhưng thiếu QTY/id: một truy vấn batch CTE VALUES đối chiếu tối đa 30 mốc. So khớp DATE, TIME, MODEL, LOTNO, RESULT, SCRAPCODE, TEST\_COUNT, SERIAL; mỗi test phải có đúng một dòng tương ứng. QTY lấy từ PRIME, không tự điền 1.
Nếu dữ liệu không đủ hoặc không xác định duy nhất: hiển thị lỗi ngay ở quy tắc đó, để bảng rỗng và yêu cầu import lại; không tìm một chuỗi mới thay thế. Các quy tắc khác còn bằng chứng vẫn xem được.
Nếu alarm bị xóa hoặc row\_version đã thay đổi từ lúc tải danh sách: yêu cầu Search lại để tránh mở nhầm phiên bản.
Tối ưu truy vấn và index
Worker tải danh sách Alarm dùng `include\\\_evidence=False`: SELECT các cột hiển thị cùng id/row\_version, không tải JSON cho tất cả alarm. API `AlarmRepository.load()` mặc định vẫn trả đầy đủ để tương thích các caller khác.
Click chỉ đọc một alarm bằng `WHERE id=?`, sử dụng INTEGER PRIMARY KEY. Snapshot mới không cần scan/join lại PRIME.
Thêm index `idx\\\_alarm\\\_history\\\_list(alarm\\\_date DESC, end\\\_datetime DESC, eqp, slot)` phục vụ lọc ngày và ORDER BY danh sách, tránh sort tạm.
Tái sử dụng `idx\\\_prime\\\_slot\\\_time(EQP, SLOT, DATE, TIME)` hiện có cho alarm cũ. SQLite index này chứa rowid (=id) làm khóa phụ, đáp ứng thứ tự DATE/TIME/id giảm dần. Không tạo thêm index PRIME trùng chức năng hoặc index riêng theo TEST\_COUNT.
Phạm vi lịch sử cũ dùng so sánh tuple `(DATE,TIME)`; không bọc cột bằng hàm ghép chuỗi/ngày. Batch đối chiếu dùng EQP/SLOT/DATE/TIME để tìm theo index.
Tải trên QThread với connection SQLite riêng và read transaction; UI không thực hiện SQL. Busy timeout của tác vụ lịch sử là 5 giây. Dùng lifecycle worker hiện có để khóa click lặp, báo lỗi và đợi thread khi đóng app.
Đổi lựa chọn quy tắc trong cửa sổ dùng dữ liệu đã tải, không truy vấn DB thêm.
File liên quan trong gói cập nhật
File	Thay đổi
`database/alarm\\\_schema.py`	Tạo index danh sách alarm, idempotent
`services/alarm\\\_builder.py`	Lưu snapshot N/15/30 test, giữ nguyên phát hiện alarm
`repositories/alarm\\\_repository.py`	Đọc thêm QTY cho snapshot; tùy chọn tải danh sách nhẹ
`repositories/alarm\\\_history\\\_repository.py`	Mới: đọc bằng chứng, kiểm tra phiên bản, hỗ trợ dữ liệu cũ
`workers/alarm\\\_worker.py`	Thêm tác vụ history chạy nền
`controllers/prime\\\_controller.py`	Điều phối worker, loading, lỗi, mở dialog, đóng app an toàn
`ui/pages/prime\\\_page.py`	Chuyển tiếp signal mở history
`ui/pages/alarm\\\_page.py`	Click ô, loại trừ nhóm cột xử lý, map proxy và chọn quy tắc
`ui/dialogs/slot\\\_fail\\\_history\\\_dialog.py`	Mới: dialog tám cột, dropdown, bộ đếm, thông báo
`tests/test\\\_alarm\\\_history.py`	Mới: kiểm thử repository, index và Qt offscreen
`changelog.txt`	Thêm mục cập nhật, giữ lịch sử cũ
`read.md`	Thêm mục tài liệu này vào cuối file, giữ nội dung trước đó
Kết quả kiểm tra
`python -m compileall -q .`: kiểm tra cú pháp thành công.
Từ thư mục ứng dụng: `python -m unittest tests.test\\\_alarm\\\_history -v`. Trong môi trường Linux không có màn hình, đặt `QT\\\_QPA\\\_PLATFORM=offscreen`. 12/12 test mới đạt: chuỗi 3/15/30, xuyên ngày, PASS/FAIL, TEST\_COUNT=0, trùng giây, snapshot khi PRIME đổi, dữ liệu cũ thiếu, version conflict, query plan, click sau lọc, loại trừ cột sửa tay, đổi quy tắc, chỉ đọc, đóng app khi worker đang chạy.
`EXPLAIN QUERY PLAN`: lookup alarm dùng INTEGER PRIMARY KEY; đọc lịch sử cũ dùng idx\_prime\_slot\_time; danh sách dùng idx\_alarm\_history\_list; không TEMP B-TREE ở các truy vấn thứ tự đã kiểm tra.
Chạy đọc thử DB đính kèm (42.709 dòng PRIME, 2 alarm được lấy mẫu): tải lịch sử khoảng 1,00–1,46 ms/lần tại máy kiểm thử local, không nhóm lỗi. Số này chỉ đo repository trên mẫu nhỏ, không phải cam kết độ trễ mạng/UNC hay thời gian vẽ UI.
Đã render và xem trực tiếp ảnh cửa sổ Qt offscreen để kiểm tra đủ tám cột, màu PASS/FAIL và nút Close. Chưa chạy GUI trực tiếp trên Windows/mạng nội bộ của người dùng.
Bộ test cũ `tests.test\\\_alarm` + `tests.test\\\_alarm\\\_gui` có 17 test: 14 đạt, 3 lỗi tồn tại giống hệt trên bản ZIP gốc và bản cập nhật. Cụ thể: test mong dấu phân cách `/` trong fail\_comment trong khi code dùng `|`; test nhập nội dung tự do vào Quick/Cal trong khi code chỉ chấp nhận PASS/FAIL; test Auto Today kỳ vọng tạo alarm từ log mẫu nhưng bản gốc cũng không tạo. Không thay đổi các nghiệp vụ này trong bản bổ sung lịch sử.

Cập nhật 2026-09-17 — Bốn ngưỡng Alarm và kiểm tra phục hồi 6/10 test
Phần này thay thế các mô tả trước đây về việc luôn tìm lại cửa sổ Yield lỗi
khi các test mới nhất của slot đã phục hồi 100%.
Cấu hình Machine Slot Yield
Giữ Target 15, Target 30.
Đổi tên ô cũ thành Số lần fail liên tục cùng scrapcode; dùng nguyên
`continuous\\\_fail\\\_count` và giữ giá trị đang lưu (ví dụ 1000).
Thêm Số lần fail liên tục khác Scrap code, lưu vào
`machine\\\_slot\\\_yield\\\_config.different\\\_scrap\\\_fail\\\_count`.
Giá trị mặc định khi thêm cột: 3; giao diện nhận 2–9999.
Save Target lưu cả bốn ngưỡng và Log Folder trong cùng transaction.
Bố trí ô mới ở hàng thứ hai để nhãn không bị ép ngắn.
Database mới/cũ đều tự thêm cột qua bước khởi tạo hiện có. Không cần xóa DB.
Bảng `slot\\\_fail\\\_alarm` thêm `different\\\_scrap\\\_fail\\\_count\\\_used` để giữ ngưỡng
tại thời điểm tạo alarm; alarm cũ có giá trị NULL cho tới khi import lại.
Quy tắc FAIL khác Scrap code
Cùng EQP/Slot và cùng Model; chuỗi N test đều FAIL, có Scrap code hợp lệ,
trong đúng N test có ít nhất hai Scrap code khác nhau.
Ví dụ N=3: A,A,B hoặc A,B,A đều đạt; A,A,A chỉ thuộc quy tắc cùng Scrap code.
Không bắt buộc từng cặp liền nhau phải khác mã, cũng không bắt buộc N mã khác nhau.
PASS, đổi Model hoặc thiếu Scrap code ngắt chuỗi. Có thể nối qua ngày.
Duyệt từ mới về cũ, lấy cửa sổ N test hợp lệ đầu tiên trong mỗi chuỗi FAIL
cùng Model; cửa sổ phải kết thúc trong ngày alarm đang tính.
Lưu snapshot đúng N test, thời gian, Model, Lot và Scrap code trong
`evidence\\\_json.different\\\_scrap`. Lịch sử khi click alarm và phần nội dung mail
đều đọc được quy tắc này. Lịch sử dùng ngưỡng đã lưu, không dùng ngưỡng mới sửa.
Quy tắc cùng Scrap code hiện có vẫn hoạt động độc lập; có thể cùng thỏa
trong một dòng alarm của EQP/Slot/ngày.
Bỏ qua alarm hiệu suất khi slot đã phục hồi
Quy tắc	Kiểm tra trước khi xét cửa sổ hiệu suất	Kết quả
Yield 15	Đủ 6 test mới nhất của slot, cả 6 đều PASS	Bỏ toàn bộ Yield 15, không tìm cửa sổ lỗi cũ
Yield 30	Đủ 10 test mới nhất của slot, cả 10 đều PASS	Bỏ toàn bộ Yield 30, không tìm cửa sổ lỗi cũ
“Mới nhất” theo thời gian log `DATE DESC, TIME DESC, id DESC`, từ test mới
nhất trong dữ liệu sau import ngược về trước, không theo thứ tự đọc file.
Xét toàn bộ test của EQP/Slot, kể cả khác Model, retest và ngày trước đó.
Giữ nguyên TEST\_COUNT trong log, gồm cả 0; không đổi 0 thành 1.
Mỗi ngày alarm chỉ dùng dữ liệu đến hết ngày đó; không lấy test tương lai
để làm mất alarm lịch sử khi import nhiều ngày cùng lúc.
Chỉ có 5 PASS mới nhất: chưa được bỏ Yield 15. Có 6–9 PASS mới nhất:
bỏ Yield 15 nhưng vẫn xét Yield 30. Có 10 PASS mới nhất: bỏ cả hai.
Có FAIL trong nhóm gần nhất, hoặc thiếu số mẫu 6/10: không được miễn xét.
Bước tính Yield vẫn yêu cầu đủ 15/30 mẫu như trước, giữ cách gom cùng Model
và so sánh `< Target` hiện có.
Điều kiện phục hồi chỉ bỏ alarm hiệu suất; không bỏ quy tắc FAIL liên tục
cùng/khác Scrap code đã đủ điều kiện trong ngày.
Import lại tính lại các ngày được import. Nếu còn vi phạm, cập nhật trường
máy và bằng chứng nhưng giữ ID/trạng thái/nội dung xử lý. Nếu không còn quy
tắc nào vi phạm, alarm của ngày đó bị xóa theo cơ chế hiện có.
Chỉ bấm Save Target chưa tính lại alarm cũ; cần import lại ngày cần cập nhật.
Cách thay file
Đóng ứng dụng và các tác vụ auto import đang chạy; sao lưu database hiện tại.
Giải nén bản patch, chép nội dung thư mục `LIApp` đè vào thư mục project
cùng tên, giữ đúng các thư mục con. Bản patch chỉ chứa file mới/sửa.
Mở ứng dụng để tự bổ sung hai cột DB. Kiểm tra bốn ngưỡng trong Machine
Slot Yield, chọn giá trị cho ô mới rồi bấm Save Target.
Import lại ngày cần áp dụng quy tắc mới và kiểm tra lịch sử của dòng alarm.
Kiểm thử bản sửa
`python -m unittest tests.test\\\_alarm tests.test\\\_alarm\\\_recovery -q`: 28/28 đạt.
Bao gồm biên 5/6/9/10 PASS, một FAIL gần nhất, xuyên ngày/Model,
chuỗi mã A,A,B; ngắt chuỗi; thiếu mẫu; snapshot lịch sử; nội dung mail;
migration DB cũ; save/reopen; import lại; bảo toàn trường xử lý; rollback.
Đã biên dịch kiểm tra cú pháp các module sửa.
Đã bổ sung kiểm thử lưu ô mới vào `tests/test\\\_machine\\\_slot\\\_yield.py`,
nhưng chưa chạy GUI PyQt5 trong môi trường bàn giao vì không có PyQt5.

21.09

* services/alarm\_builder.py: chỉ đưa TEST\_COUNT = 0 vào hai bộ xét fail liên tiếp cùng/khác Scrap Code; bỏ qua retest, giữ nguyên Yield 15/30 và phục hồi 6/10.
* repositories/alarm\_history\_repository.py: lọc TEST\_COUNT = 0 ở lịch sử legacy; từ chối bằng chứng liên tiếp cũ có TEST\_COUNT khác 0 và hướng dẫn import lại ngày alarm.
* read.md: thêm hướng dẫn thay hai file, tính lại alarm cũ, ví dụ hai ảnh và phạm vi kiểm thử; giữ lịch sử tài liệu cũ.
* Xác minh: 8 kiểm thử tập trung đều PASS; chưa chạy GUI Windows/database sản xuất.

21.09
LI App — sửa khởi động chậm
Nguyên nhân xác định từ source
main.py gọi initialize\_database sau show, nhưng controller cũ dùng cùng worker cho init, bộ lọc, import và query. \_start khóa Import, Search và cả tab bar, kể cả khi chỉ tải bộ lọc. Đây là trạng thái bị vô hiệu hóa có chủ đích, không đủ bằng chứng kết luận Qt event loop bị treo.
initialize\_database cũ luôn chạy CREATE IF NOT EXISTS, kiểm tra cột và INSERT OR IGNORE cho cấu hình. Các lệnh ghi vẫn cần khóa SQLite kể cả không thêm dòng; connection mặc định có thể chờ 60 giây. Database trên server hoặc đang có auto-import có thể làm chờ lâu.
Bộ lọc cũ DISTINCT/UNION trên nhiều dòng dữ liệu. Thời gian tăng theo lượng test.
Source hiện tại vốn chưa import Matplotlib/openpyxl/pandas lúc dựng cửa sổ. Matplotlib được nạp ở worker khi SEARCH đầu tiên. Không có bằng chứng thư viện là nguyên nhân chính của ảnh chụp.
Aging có worker riêng tải bộ lọc và preload chart sau show 500 ms. LI áp dụng cách tách này. Aging vẫn khởi tạo database trước show; không sao chép phần đó.
Launcher LI đã chạy EXE local, chỉ copy package khi version thay đổi/thiếu file. Không thay launcher hoặc chương trình auto-import/auto-mail.
Hành vi sau sửa
Dựng cửa sổ bằng các module nhẹ. Không nạp thư viện biểu đồ/Excel nặng trước khi cửa sổ xuất hiện.
Sau show: kiểm tra DB trên worker; sau 500 ms nạp các module biểu đồ trên worker riêng. Không tạo QWidget/FigureCanvas trong worker.
Database đầy đủ: chỉ đọc metadata/cấu hình cần kiểm tra, không ghi schema mỗi lần mở. Nếu thiếu schema/index/cấu hình vẫn chạy bổ sung theo cơ chế hiện tại. Giới hạn chờ khóa SQL lúc khởi tạo giảm còn 5 giây; không giới hạn thời gian dựng index hay chờ hệ điều hành truy cập mạng.
Tải bộ lọc trên worker riêng, dùng index seek theo từng giá trị khác nhau. Giữ nguyên nguồn PRIME/CUM và quy tắc lọc Scrap Code.
Import và thanh tab không bị khóa bởi tải bộ lọc. Search trước khi có bộ lọc được ghi nhận và thực hiện khi sẵn sàng. Import bấm khi DB đang khởi tạo được ghi nhận; sau khi DB sẵn sàng mới mở hộp chọn nguồn.
Lỗi bộ lọc hiển thị ở status bar; Search thử tải lại. Không có popup chặn chỉ vì preload thất bại; SEARCH sẽ thử nạp và báo lỗi nếu cần.
Khi người dùng chủ động import/query, vẫn bảo vệ thao tác không được chạy chồng như trước. Không tự import log/Excel, không tự SEARCH khi chưa có yêu cầu. Các quy tắc alarm và TEST\_COUNT không đổi.
Đóng app chờ worker kết thúc an toàn; tải bộ lọc có cờ hủy.
File cần thay/thêm
Thay 7 file:
main.py
controllers/prime\_controller.py
database/schema.py
repositories/filter\_option\_repository.py
workers/filter\_option\_worker.py
workers/summary\_worker.py
workers/slot\_summary\_worker.py
Thêm:
workers/chart\_preload\_worker.py
tests/test\_startup\_responsiveness.py (kiểm thử, không bắt buộc khi chạy EXE)
Đóng app, sao lưu source, chép các file trên vào đúng đường dẫn. KHÔNG chép đè database/li\_app.db đang dùng từ bản source ZIP; database đính kèm chỉ là dữ liệu gốc do bạn gửi. Không cần xóa database hoặc import lại. Nếu dùng EXE, build lại core app theo quy trình hiện tại; nếu dùng Launcher, phát hành package và tăng version theo quy trình đang có để launcher lấy được bản mới.
Kiểm chứng
11 kiểm thử mới cho: không import thư viện nặng trước show; bộ lọc chậm không khóa nút và timer Qt vẫn chạy; ghi nhận Search; ghi nhận Import trong init; lỗi bộ lọc và thử lại; DB đủ schema khởi động dưới RESERVED write lock; schema thiếu vẫn bổ sung; đóng app khi tải bộ lọc/preload; preload không tạo biểu đồ; SEARCH thật sau khi tải nền.
Hai kiểm thử database của test\_filters.py đạt (nguồn dữ liệu/không sửa dữ liệu, tạo index).
Với database gốc 42.709 dòng PRIME, 531 dòng CUM, 193 dòng scrap detail: 5 danh sách bộ lọc cũ/mới trùng khớp. Trung vị 7 lượt trên máy kiểm tra: 0,00922 giây → 0,000643 giây. Đây là thời gian query cục bộ, không phải cam kết thời gian mở app Windows.
EXPLAIN QUERY PLAN xác nhận MIN(SCRAPCODE) dùng covering index.
Toàn bộ mã Python kiểm tra cú pháp thành công.
Không tuyên bố toàn bộ bộ test cũ đạt: test\_filters UI có kỳ vọng thứ tự Scrap Code không khớp code giao diện gốc; test\_slot\_tab\_refresh cũ đợi controller.busy (nay chỉ là tác vụ chính), cần đợi riêng worker bộ lọc trước khi đọc các item. Các test mới kiểm tra trực tiếp cơ chế tải nền thay thế.
Chưa đo trên Windows/ổ mạng thực tế hoặc EXE PyInstaller. Không thay logic đọc log, alarm, mail, tính yield.
Chạy bộ kiểm thử mới từ thư mục LI\_APP:
python -m unittest discover -s tests -p test\_startup\_responsiveness.py -v

LI App — Cập nhật khởi động và tải dữ liệu sau Import PRIME
Ngày cập nhật: 21/09/2026.
Tài liệu mô tả bản sửa khởi động đã bàn giao và kết quả kiểm tra lại source `LI\\\_APP (3).zip`. Lần kiểm tra bổ sung này không thay đổi thêm mã nguồn.

1. Vấn đề ở phiên bản cũ
Khi mở ứng dụng
Khởi tạo database, tải bộ lọc, import và truy vấn dùng chung worker trong `PrimeController`.
Mỗi lần worker chạy, controller khóa Import PRIME, Import CUM, Search và thanh tab. Vì vậy giao diện đã hiện nhưng chưa thao tác được.
Khởi tạo database luôn chạy các lệnh bổ sung schema và ghi cấu hình. Ngay cả `INSERT OR IGNORE` cũng cần quyền ghi; có thể phải chờ khóa SQLite tới 60 giây theo cấu hình kết nối cũ.
Các truy vấn DISTINCT/UNION của bộ lọc đọc nhiều dòng test, nên thời gian tăng theo lượng dữ liệu.
Source cũ đã trì hoãn nạp Matplotlib tới SEARCH. Không có bằng chứng thư viện nặng là nguyên nhân chính của trạng thái nút bị khóa trong ảnh.
Sau khi Import PRIME thành công
Bản cũ tự chạy tiếp chuỗi sau:
Import PRIME kết thúc và hiển thị thông báo thành công.
Tải lại bộ lọc bằng worker chung, tiếp tục khóa nút.
Nếu đang mở tab Alarm, tự gọi `load\\\_alarm()` sau khi bộ lọc tải xong, dù người dùng chưa bấm Search; bước này lại dùng worker khóa nút.
Do đó, việc dữ liệu đã ghi xong nhưng các nút tiếp tục bị khóa một lúc là có thể giải thích trực tiếp từ luồng điều khiển cũ.
2. Các thay đổi đã thực hiện
Thành phần	Thay đổi
Tải bộ lọc	Chạy bằng QThread riêng, không dùng worker import/query và không khóa các nút chính hoặc thanh tab.
Truy vấn bộ lọc	Dùng index để lấy từng giá trị phân biệt; giữ nguồn PRIME/CUM và quy tắc Scrap Code hiện có.
Kiểm tra database	Nếu schema/index/cấu hình đã đầy đủ, chỉ đọc thông tin kiểm tra, bỏ các lệnh ghi không cần thiết mỗi lần mở.
Database thiếu thành phần	Vẫn bổ sung schema/index/cấu hình theo cơ chế hiện có.
Chờ khóa lúc khởi tạo	Giảm timeout khóa SQLite xuống 5 giây. Đây không phải giới hạn tổng thời gian mở app hay thời gian truy cập ổ mạng.
Thư viện biểu đồ	Nạp trên worker riêng sau khi cửa sổ hiển thị, hẹn bắt đầu sau 500 ms, tham khảo Aging. Không tạo QWidget/FigureCanvas trong worker.
Search khi bộ lọc chưa sẵn sàng	Ghi nhận yêu cầu và thực hiện khi tải xong.
Import khi database đang khởi tạo	Ghi nhận yêu cầu; mở hộp chọn nguồn khi database sẵn sàng.
Sau Import PRIME/CUM	Tải lại bộ lọc ở nền. Không tự tải Alarm chỉ vì đang ở tab Alarm.
Lỗi tải bộ lọc	Báo trên thanh trạng thái; bấm Search để thử lại.
Đóng app	Hủy tải bộ lọc khi cần và chờ worker kết thúc an toàn.
Ứng dụng vẫn khóa các thao tác liên quan khi người dùng đang thực hiện import/query thực sự để tránh chạy chồng. Hộp thông báo Import thành công là hộp thoại modal: cần bấm OK để trở lại cửa sổ chính.
3. Phân biệt ghi dòng dữ liệu và hoàn tất import
Thông báo `Đang ghi database: ... dòng (chưa commit)` chưa có nghĩa toàn bộ import đã kết thúc.
Luồng xử lý PRIME vẫn gồm:
Đọc và kiểm tra log vào staging.
Thay dữ liệu các ngày được import trong transaction.
Đồng bộ TIER.
Tính/cập nhật Alarm cho các ngày import.
Cập nhật trạng thái import và commit transaction.
Dọn staging, giải phóng khóa import, kết thúc worker.
Hiển thị kết quả và tải lại bộ lọc ở nền.
Bước tính/cập nhật Alarm trong transaction vẫn được giữ để dữ liệu PRIME và Alarm đồng bộ. Bản sửa bỏ việc tự truy vấn lại bảng Alarm sau import; không bỏ tính Alarm trong quá trình import.
Sau import, bảng Alarm đang hiển thị có thể vẫn là kết quả cũ. Bấm Search để đọc lại dữ liệu mới. Nếu trước đó đã bấm Search lúc bộ lọc chưa sẵn sàng, yêu cầu đã ghi nhận có thể được thực hiện sau khi bộ lọc tải xong.
4. Danh sách file đã thay đổi
File	Nội dung
`main.py`	Gọi preload biểu đồ sau khi cửa sổ hiện lên.
`controllers/prime\\\_controller.py`	Tách worker bộ lọc/preload; quản lý yêu cầu chờ và đóng app; bỏ tự tải Alarm sau bộ lọc.
`database/schema.py`	Kiểm tra schema hiện có trước khi chạy bổ sung; giảm timeout khởi tạo.
`repositories/filter\\\_option\\\_repository.py`	Tối ưu truy vấn các lựa chọn bằng index.
`workers/filter\\\_option\\\_worker.py`	Hỗ trợ hủy tải bộ lọc.
`workers/summary\\\_worker.py`	Nạp module biểu đồ trên worker trước khi trả kết quả.
`workers/slot\\\_summary\\\_worker.py`	Nạp module biểu đồ trên worker trước khi trả kết quả.
`workers/chart\\\_preload\\\_worker.py`	File mới: nạp các module biểu đồ ở nền.
`tests/test\\\_startup\\\_responsiveness.py`	File kiểm thử mới cho khởi động và thao tác trong lúc tải nền.
Tổng cộng: 7 file mã thay thế, 1 file mã mới và 1 file kiểm thử mới.
5. Cách áp dụng
Đóng ứng dụng và sao lưu source hiện tại.
Thay/thêm đúng các file ở mục 4 từ gói sửa đã bàn giao. Source `LI\\\_APP (3).zip` đã có phần sửa controller được kiểm tra trong tài liệu này.
Giữ database đang sử dụng; không chép đè `database/li\\\_app.db` từ gói source.
Không cần xóa database hoặc import lại vì bản cập nhật này.
Nếu chạy Python, mở `main.py` như trước. Nếu chạy EXE, build lại core app. Nếu phân phối qua Launcher, cập nhật package/version theo quy trình đang dùng.
6. Kết quả kiểm tra
Bản sửa trước: 11 kiểm thử khởi động đạt; kiểm tra cú pháp toàn bộ source thành công.
Năm danh sách bộ lọc cũ/mới trùng khớp trên database đính kèm: 42.709 dòng PRIME, 531 dòng CUM và 193 dòng scrap detail.
Trung vị 7 lượt truy vấn bộ lọc trên môi trường kiểm tra: khoảng 9,22 ms trước sửa và 0,643 ms sau sửa. Đây là số đo query cục bộ, không phải thời gian mở app trên máy người dùng.
Kiểm tra bổ sung trên `LI\\\_APP (3).zip`: thực hiện import PRIME thật vào database tạm khi đang ở tab Alarm, cố ý trì hoãn tải bộ lọc sau import. Dữ liệu đã commit; Import PRIME, Import CUM, Search và thanh tab vẫn bật trong lúc bộ lọc đang chờ.
Xác nhận không tự gọi `load\\\_alarm()` sau khi bộ lọc tải xong trong tình huống trên.
Không tuyên bố toàn bộ bộ kiểm thử cũ đều đạt. Một số kiểm thử giao diện cũ có kỳ vọng lỗi thời về thứ tự item hoặc chỉ đợi worker chính thay vì đợi riêng worker bộ lọc.
Chưa đo trên Windows/ổ mạng thực tế hoặc bản EXE của người dùng. Nếu bản mới vẫn chậm, cần phân biệt đang tính Alarm/chưa commit, đang dọn import hay đã hoàn tất nhưng còn tác vụ khác.
Lệnh chạy bộ kiểm thử khởi động từ thư mục project:

```bash
python -m unittest discover -s tests -p test\\\_startup\\\_responsiveness.py -v
```

7. Phạm vi dữ liệu
Bản cập nhật này không thay quy tắc đọc log, TEST\_COUNT, tính Yield hoặc điều kiện tạo Alarm. Không tự import log/Excel khi mở giao diện. Thư viện nặng được nạp sau khi cửa sổ xuất hiện; database dùng chung và cơ chế khóa import vẫn được giữ.

Sửa tải lại khi mở File Management — 21/09/2026
Nguyên nhân
PrimePage.open\_file\_management() luôn gọi load\_if\_needed(force=True).
force=True đánh dấu cả PRIME/CUM cần tải lại; truy vấn danh sách và hộp Loading chạy mỗi lần quay lại tab.
DataListPanel.set\_records() đặt lại lựa chọn tháng/ngày mỗi lần nhận danh sách.
Truy vấn SELECT DISTINCT DATE cũ vẫn duyệt các mục trong index theo số dòng test.
Kiểm tra các kết nối currentChanged, filter\_applied, refresh\_filter\_options và worker trong project: chuyển vào File Management không trực tiếp gọi tải bộ lọc thống kê chung. Thông báo tải bộ lọc chung có thể thuộc tác vụ nền sau khởi tạo/import.
Đã sửa
ui/pages/prime\_page.py: bỏ force=True khi mở tab. Giữ danh sách và lựa chọn hiện tại khi không có thay đổi.
ui/pages/file\_management\_page.py: thêm REFRESH DATA LIST để chủ động đọc lại PRIME/CUM, độc lập bộ lọc thống kê. Giữ cơ chế đánh dấu đúng loại dữ liệu sau import; tab ẩn tải khi mở lại. Chờ slot kết thúc dọn thread trước khi tạo worker tiếp, giữ yêu cầu cập nhật đến trong lúc đang tải.
repositories/database\_management\_repository.py: dùng recursive index seek để tìm từng DATE khác nhau thay vì quét DISTINCT trên toàn bộ các dòng. Vẫn lấy ngày từ bảng dữ liệu thực và LEFT JOIN thời gian import; dữ liệu cũ thiếu metadata vẫn hiển thị.
tests/test\_file\_tab\_cache.py: 6 kiểm tra hồi quy mới.
Cách áp dụng
Đóng app; giải nén gói patch rồi chép 3 file .py ở ui/ và repositories/ vào đúng đường dẫn trong project, ghi đè file cũ.
tests/ là kiểm tra tự động, không bắt buộc để chạy app.
Không cần xóa hay tạo lại database. Nếu dùng bản .exe, build lại sau khi thay source.
Lần đầu mở File Management vẫn tải danh sách. Các lần mở sau dùng lại danh sách đã tải.
Import trong app cập nhật danh sách tương ứng. Nếu auto-import, app khác hoặc người khác cập nhật database, bấm REFRESH DATA LIST để lấy danh sách mới.
Khi thực sự tải lại (import/REFRESH), bộ lọc tháng/ngày trong danh sách vẫn theo hành vi cũ: chọn toàn bộ. Chuyển tab thông thường giữ nguyên lựa chọn.
Kiểm tra
Môi trường Python/PyQt5 Linux, GUI offscreen, database tạm; chưa đo tốc độ trên PC Windows/database sản xuất.
test\_file\_tab\_cache.py: 6/6 PASS (chuyển tab/SEARCH không query lại; giữ lựa chọn; import PRIME/CUM; refresh riêng; lỗi có thể thử lại; thay đổi trong lúc tải không mất).
test\_file\_management.py: 5/5 PASS.
test\_startup\_responsiveness.py: 11/11 PASS.
Toàn bộ test bản gốc: 103 tests, 11 failures + 23 errors.
Toàn bộ test sau sửa: 109 tests, cùng 11 failures + 23 errors, cùng danh sách test lỗi; 6 test mới đều PASS. Không có test lỗi mới trong lần chạy đối chiếu này.
Các lỗi có sẵn chưa được sửa trong patch này; không thể kết luận toàn project đã sạch lỗi.
Test có sẵn chưa đạt (giống bản gốc)
test\_conflict\_busy\_and\_completion (test\_alarm.AlarmImportTests.test\_conflict\_busy\_and\_completion)
test\_reimport\_updates\_machine\_fields\_preserves\_tracking\_then\_deletes (test\_alarm.AlarmImportTests.test\_reimport\_updates\_machine\_fields\_preserves\_tracking\_then\_deletes)
test\_delegate\_commit\_and\_close\_with\_worker (test\_alarm\_gui.AlarmGuiTests.test\_delegate\_commit\_and\_close\_with\_worker)
test\_tab\_filters\_save\_status\_text\_and\_refresh\_external (test\_alarm\_gui.AlarmGuiTests.test\_tab\_filters\_save\_status\_text\_and\_refresh\_external)
test\_close\_app\_while\_loading (test\_alarm\_history.HistoryGuiTests.test\_close\_app\_while\_loading)
test\_real\_click\_after\_filter\_and\_edit\_columns\_excluded (test\_alarm\_history.HistoryGuiTests.test\_real\_click\_after\_filter\_and\_edit\_columns\_excluded)
test\_index\_plans\_and\_repeat\_init (test\_alarm\_history.HistoryTests.test\_index\_plans\_and\_repeat\_init)
test\_list\_omits\_evidence\_only\_when\_requested (test\_alarm\_history.HistoryTests.test\_list\_omits\_evidence\_only\_when\_requested)
test\_snapshot\_survives\_prime\_changes (test\_alarm\_history.HistoryTests.test\_snapshot\_survives\_prime\_changes)
test\_tied\_timestamp\_stable\_by\_id (test\_alarm\_history.HistoryTests.test\_tied\_timestamp\_stable\_by\_id)
test\_version\_and\_deleted\_alarm (test\_alarm\_history.HistoryTests.test\_version\_and\_deleted\_alarm)
test\_import\_history\_mail\_and\_tracking (test\_alarm\_recovery.PersistenceTests.test\_import\_history\_mail\_and\_tracking)
test\_migration\_existing\_db\_and\_round\_trip (test\_alarm\_recovery.PersistenceTests.test\_migration\_existing\_db\_and\_round\_trip)
test\_mixed\_accepts\_repeated\_codes\_and\_preserves\_test\_count (test\_alarm\_recovery.RecoveryRulesTests.test\_mixed\_accepts\_repeated\_codes\_and\_preserves\_test\_count)
test\_mixed\_and\_same\_can\_coexist (test\_alarm\_recovery.RecoveryRulesTests.test\_mixed\_and\_same\_can\_coexist)
test\_mixed\_cross\_day\_and\_latest\_qualifying\_window (test\_alarm\_recovery.RecoveryRulesTests.test\_mixed\_cross\_day\_and\_latest\_qualifying\_window)
test\_recovery\_keeps\_same\_scrap\_alarm (test\_alarm\_recovery.RecoveryRulesTests.test\_recovery\_keeps\_same\_scrap\_alarm)
test\_button\_import\_reimport (test\_gui.GuiTests.test\_button\_import\_reimport)
test\_tab\_lazy\_load\_and\_save\_button (test\_machine\_slot\_yield.MachineSlotYieldTests.test\_tab\_lazy\_load\_and\_save\_button)
test\_legend\_style\_and\_slot\_only\_cache (test\_model\_summary.ModelSummaryTests.test\_legend\_style\_and\_slot\_only\_cache)
test\_tab\_switch\_applies\_current\_controls\_to\_model\_summary (test\_model\_summary.ModelSummaryTests.test\_tab\_switch\_applies\_current\_controls\_to\_model\_summary)
test\_active\_tab\_cache\_clear\_and\_recovery (test\_slot\_gui.SlotGuiTests.test\_active\_tab\_cache\_clear\_and\_recovery)
test\_tab\_switch\_reads\_unsubmitted\_filters\_and\_uses\_cache (test\_slot\_tab\_refresh.SlotTabRefreshTests.test\_tab\_switch\_reads\_unsubmitted\_filters\_and\_uses\_cache)
test\_new\_slot\_removed\_slot\_and\_other\_alarm\_date (test\_alarm.AlarmImportTests.test\_new\_slot\_removed\_slot\_and\_other\_alarm\_date)
test\_rule1\_cross\_day\_full\_run\_priority\_and\_scraps (test\_alarm.AlarmRulesTests.test\_rule1\_cross\_day\_full\_run\_priority\_and\_scraps)
test\_legacy\_all\_rules\_and\_missing\_prime (test\_alarm\_history.HistoryTests.test\_legacy\_all\_rules\_and\_missing\_prime)
test\_long\_run\_bounded\_snapshot\_and\_multiple\_rules (test\_alarm\_history.HistoryTests.test\_long\_run\_bounded\_snapshot\_and\_multiple\_rules)
test\_replaces\_current\_day\_every\_run\_and\_keeps\_last\_date (test\_auto\_import\_today.AutoImportTodayTests.test\_replaces\_current\_day\_every\_run\_and\_keeps\_last\_date)
test\_daily\_charts\_cache\_and\_reset (test\_daily\_gui.DailyGuiTests.test\_daily\_charts\_cache\_and\_reset)
test\_ui\_criteria\_and\_select\_all (test\_filters.FilterTests.test\_ui\_criteria\_and\_select\_all)
test\_close\_idle\_once (test\_gui.GuiTests.test\_close\_idle\_once)
test\_startup\_import\_buttons\_and\_maximized (test\_gui.GuiTests.test\_startup\_import\_buttons\_and\_maximized)
test\_search\_copy\_chart\_cache\_and\_invalidation (test\_model\_summary.ModelSummaryTests.test\_search\_copy\_chart\_cache\_and\_invalidation)
test\_search\_cache\_error\_and\_refresh (test\_summary.SummaryTests.test\_search\_cache\_error\_and\_refresh)



## \[2026-09-21 23:00:54 UTC+7] Hoàn thiện Report — Soạn báo cáo

### Chức năng và file liên quan

* Sửa `ui/pages/report\\\_page.py`: nối bộ soạn vào Report, thêm hai tab con Dữ liệu / Chi tiết và Soạn báo cáo; thêm dòng đang chọn, tải lại dữ liệu, đặt giờ trọn ngày. Khóa nguồn cũ ngay khi đổi bộ lọc để không thêm nhầm trong lúc chờ truy vấn.
* Sửa `ui/widgets/report\\\_builder.py`: cây nguồn có checkbox ngày → EQP → SLOT, chọn theo thứ tự tick, kéo nhóm vào cây báo cáo, sắp xếp cùng cấp, xóa nhóm/dòng, xem trước bảng gộp ô và đường viền đen.
* Thêm `tests/test\\\_report\\\_integration.py`: kiểm thử SQLite tạm, kết nối GUI, thứ tự chọn, copy, kéo từ nguồn, giữ bản soạn khi đổi bộ lọc.
* Tái sử dụng nguyên trạng `repositories/report\\\_repository.py`, `workers/report\\\_worker.py`, `services/report\\\_export.py`, `tests/test\\\_report\\\_builder.py`; các file này đã có trong LIapp.zip nên không kèm lại trong patch.
* `read.md`, `changelog.txt`: nối thêm hướng dẫn/lịch sử, giữ nguyên toàn bộ nội dung trước đó.

### Áp dụng

1. Đóng LI Yield. Giải nén patch và chép các file vào đúng thư mục tương ứng trong project LIapp, ghi đè file cũ.
2. Không cần xóa database, tạo database hoặc migration. Không thay đổi dữ liệu sản xuất.
3. Chạy `python main.py`. Nếu sử dụng bản exe, build lại bằng `pyinstaller --clean LI\\\_Yield.spec`, rồi phát hành cả thư mục dist/LI\_Yield theo quy trình launcher hiện có. Patch không chứa exe đã build.
4. PyQt5 và openpyxl đã có trong requirements.txt; không thêm thư viện mới. tests/ chỉ phục vụ kiểm thử.

### Ví dụ chọn ngày 09/09/2026, AI-H911, SLOT 47 rồi 46

1. Trong Report, đặt From và To cùng ngày 09/09/2026. Bấm Trọn ngày để lấy 00:00:00 đến 23:59:59; có thể chỉnh giờ riêng nếu cần.
2. Chọn EQP AI-H911. Trong bộ lọc SLOT, bỏ Select All rồi tick 47 trước, 46 sau. Chờ dữ liệu tải xong.
3. Mở Soạn báo cáo. Ở cây nguồn bên trái, tick SLOT 47 rồi 46 và bấm Thêm mục đã tick. Có thể tick cả ngày/máy để thêm toàn bộ SLOT con theo thứ tự hiển thị, hoặc kéo ngày/máy/SLOT từ cây nguồn sang cây Thứ tự báo cáo.
4. Bảng bên phải hiển thị đúng 8 cột Date, EQP, SLOT, IN, OutQty, FailQty, Scrap Code, YLD; gộp Date/EQP, Scrap Code đỏ và nhiều dòng, YLD có màu.
5. Đổi khoảng ngày hoặc EQP/SLOT và tiếp tục thêm để ghép báo cáo nhiều ngày/nhiều máy. Những dòng đã thêm được giữ lại khi lọc hoặc tải lại nguồn.
6. Kéo các mục cùng cấp trong cây Thứ tự báo cáo hoặc dùng Lên/Xuống: ngày đổi thứ tự với ngày; EQP đổi thứ tự trong cùng ngày; SLOT đổi thứ tự trong cùng EQP. Có thể xóa SLOT, cả máy hoặc cả ngày.
7. Ngoài ra, chọn các dòng/ô trong tab Dữ liệu rồi bấm Thêm dòng chọn vào báo cáo. Cách này lấy thứ tự hiện có trong bảng nguồn; muốn điều khiển thứ tự từng lần tick, dùng cây nguồn ở Soạn báo cáo.

### Copy và xuất Excel

* Copy báo cáo hoặc Ctrl+C khi bảng xem trước có focus: copy toàn bộ báo cáo kèm tiêu đề bằng TSV. Dán Excel giữ số 0; Scrap Code nhiều dòng được nối bằng `/` để không tách thành hàng khác. Copy không giữ ô gộp/màu.
* Xuất Excel: lưu .xlsx có ô gộp, viền, căn giữa, Scrap Code đỏ/xuống dòng, số lượng dạng số và YLD dạng phần trăm. Ngày hiển thị dd/MM/yyyy. Màu YLD: >=100% xanh, >=95% vàng, <95% cam; theo bộ xuất sẵn có.
* Hàng không có dữ liệu giữ trống các số lượng/YLD; không đổi thành 0. Có thể xóa các hàng này khỏi báo cáo.
* Thêm lại cùng ngày–EQP–SLOT cập nhật số liệu tại vị trí cũ, không tạo trùng. Nếu dùng khoảng giờ khác, dòng được thêm lại thay thế dòng cũ; không cộng dồn hai khoảng giờ.
* Bản soạn giữ số liệu tại thời điểm thêm. Sau khi import hoặc dữ liệu thay đổi, tải lại nguồn rồi thêm lại các nhóm cần cập nhật. Bản soạn hiện chỉ giữ trong phiên mở app; xuất Excel trước khi đóng nếu cần lưu lâu dài.

### Cách tính và kiểm chứng

* Không sửa truy vấn: chỉ TEST\_COUNT = 0; IN = COUNT(\*), OUT = số bản ghi PASS, FAIL = số bản ghi FAIL; YLD = OUT/IN × 100. Tổng hợp theo ngày–EQP–SLOT trong khoảng thời gian đang chọn.
* 10/10 kiểm thử Report đạt trên Python 3.12/PyQt5 5.15.11, GUI offscreen Linux, SQLite tạm: 4 test sẵn có + 6 test tích hợp mới.
* Dữ liệu mẫu kiểm tra: SLOT 47 có IN=79, OUT=79, FAIL=0, YLD=100%; SLOT 46 có IN=83, OUT=78, FAIL=5, Scrap 4541*4 / 4593*1, YLD=93.98%. Các bản ghi TEST\_COUNT=1 bị loại; bao gồm đúng bản ghi lúc 00:00:00 và 23:59:59.
* Đã kiểm tra file Excel xuất bằng openpyxl: gộp ô, số 0, phần trăm, màu và ô trống; đã xem ảnh chụp GUI mẫu. Chưa kiểm tra thao tác chuột kéo thả thực tế, dán Excel trên Windows, bản exe hoặc database sản xuất.
* Lệnh kiểm thử từ thư mục project: `python -m unittest discover -s tests -p "test\\\_report\\\*.py" -v`.



\#22.09 Thay đổi lần này – Daily và Report

## Cài đặt

Đóng app, chép 4 file trong gói vào đúng đường dẫn tương ứng của project LIapp đã gửi, đồng ý thay thế. Mở lại app và Search để lấy kết quả mới. Không cần tạo lại database.

## Các file sửa

* repositories/report\_repository.py: bỏ giới hạn TEST\_COUNT = 0 ở danh sách Machine/Slot, tổng hợp Report và cửa sổ chi tiết; tính tất cả lần test, gồm retest. Áp dụng cho cả Tra cứu SLOT và Báo cáo Slot dùng chung repository. IN = số bản ghi, Out = số PASS, Fail = số FAIL, Yield = PASS / tổng số lần × 100; không cộng QTY. Scrap Code và Model lấy từ cùng tập dữ liệu mới.
* services/slot\_report\_service.py: cập nhật mô tả chính sách tính Report theo mọi Test Count.
* ui/widgets/slot\_report\_builder.py: sửa thông báo hướng dẫn thành “Lấy tất cả Test Count”.
* ui/widgets/machine\_slot\_summary.py: Daily đổi thứ tự No, Date, Machine, Slot, Total Test, Pass, Fail, Yield; tăng chữ cả Summary và Daily từ 11px lên 13px, tăng chiều cao tiêu đề/dòng. Cột giữ chiều rộng tối thiểu để ngày và Yield không bị cắt; cửa sổ hẹp có thể xuất hiện thanh cuộn ngang.

## Xác nhận Daily

Trong source LIapp.zip lần này, truy vấn Daily đã dùng COUNT(\*) và không lọc TEST\_COUNT. Không cần sửa repository Daily. Đã kiểm tra với ba lần test có Test Count 0, 1, 2: tổng 3, PASS 2, FAIL 1, Yield 66.67%. QTY mỗi bản ghi là 99 vẫn chỉ tính một lần test.

## Kiểm tra lần này

Đã kiểm tra Daily, tổng hợp Report, chi tiết Report, danh sách máy/slot chỉ có retest, dữ liệu Báo cáo Slot, thứ tự cột Daily, cỡ chữ 13px và cú pháp các file bàn giao. Dữ liệu thử nghiệm dùng SQLite và giao diện Qt offscreen; chưa chạy trên database thực tế của bạn.



23.09
Machine Slot Yield – thay đổi lần này
Cài đặt
Đóng ứng dụng. Chép 3 file trong gói vào đúng thư mục của source LI\_App\_v1.12-master đã gửi:
controllers/prime\_controller.py
repositories/machine\_slot\_summary\_repository.py
ui/widgets/machine\_slot\_summary.py
Mở app, vào Machine Slot Yield, chọn From/To trên bộ lọc chung và bấm Search. Không cần tạo lại database.
Phạm vi ngày và cập nhật
Summary và Daily dùng From–To đã bấm Search, bao gồm toàn bộ hai ngày đầu/cuối, không còn cửa sổ 30 ngày.
Chưa Search thì hai bảng để trống. Đổi ngày nhưng chưa Search không thay kết quả, kể cả lúc tự cập nhật.
Lần 1–10 chỉ lấy các lần test mới nhất trong khoảng ngày đã áp dụng.
Cả hai bảng đếm mọi Test Count; mỗi bản ghi là một lần test, không cộng QTY.
Tự cập nhật mỗi 10 phút khi tab đang hiển thị; dùng lại khoảng ngày đã Search. Chuyển lại tab và import hoàn tất cũng làm mới khoảng đã áp dụng.
Đủ slot và Alarm
Theo schema hiện tại của LI App: mỗi máy có slot 1–48. Danh sách máy lấy từ prime\_data và bảng Alarm đã lưu, kể cả máy không có test trong khoảng chọn.
Summary có đủ 48 slot/máy. Daily có đủ mỗi ngày × máy × 48 slot, ngày mới nhất trước.
Dòng không có test: Total Test, PASS, FAIL bằng 0; Yield và kết quả gần nhất để trống.
Chỉ hiện Alarm lọc Summary theo các cặp máy/slot có trong toàn bộ slot\_fail\_alarm, không giới hạn ngày Alarm; giữ nền đỏ nhạt. Bộ lọc Machine/Slot riêng tiếp tục áp dụng cho Summary. Daily không chịu các bộ lọc riêng này.
Chỉ có thể nhận biết Alarm còn được lưu; Alarm đã xóa khỏi bảng không thể truy hồi bằng truy vấn này.
Lịch sử khi click dòng
Click một dòng ở bất kỳ bảng nào để mở lịch sử toàn khoảng From–To đã tạo ra dữ liệu đang hiển thị, kể cả khi click dòng Daily. Không chỉ giới hạn ở ngày của dòng Daily.
Đúng máy/slot được click, lấy mọi Test Count. Slot không có test mở bảng lịch sử rỗng.
Các cột: DATE, TIME, PARTNO, LOTNO, SERIAL, RESULT, SCRAPCODE, QTY, EQP, TEST\_COUNT, Slot, MODEL, TIER. Có Ctrl+C để sao chép.
Truy vấn lịch sử chạy nền; đóng cửa sổ trong khi tải sẽ yêu cầu hủy và chờ thread kết thúc an toàn.
Kiểm tra
Kiểm tra bằng SQLite giả lập và Qt offscreen: biên ngày, mọi Test Count, đủ slot và dòng Daily bằng 0, Alarm ngoài khoảng chọn, lịch sử có/không dữ liệu, Search, cập nhật liên tiếp và chu kỳ 10 phút. Chưa đo tốc độ trên database/ổ mạng thực tế; khoảng ngày dài tạo nhiều dòng Daily hơn.

Điều chỉnh bố cục Machine Slot Yield
Áp dụng
Đóng LI App, thay `ui/widgets/machine\\\_slot\\\_summary.py` trong project LI-APP bằng file cùng đường dẫn trong gói này. Mở lại ứng dụng. Không cần thay đổi database.
Nội dung lần này
Chia lại chiều ngang: bảng Machine / Slot Summary khoảng 63%, Daily Machine / Slot khoảng 37%; Daily được rộng hơn để hiện các tiêu đề, hai bảng vẫn cùng hàng. Có thể kéo vạch chia giữa hai bảng.
Giữ độ rộng tối thiểu cho tiêu đề và dữ liệu. Khi cửa sổ quá hẹp, bảng có thể cuộn ngang để không cắt mất giá trị.
Header bộ lọc Daily dùng nền xanh đậm giống Summary, chữ và biểu tượng mũi tên/phễu trắng; cột đang lọc có nền xanh đậm hơn và vạch trắng dưới tiêu đề.
Popup lọc của riêng bảng Daily tự chọn chiều ngang khoảng 190–250px theo giá trị, thay vì cố định 300px. Các popup ở tab khác không bị thay đổi.
Cả hai History tự tính chiều ngang theo 13 cột sau khi tải dữ liệu, thêm chỗ cho thanh cuộn và viền; giới hạn tối đa 90% chiều rộng màn hình. Trước khi tải xong, cửa sổ khởi tạo 980px thay cho 1250px. Trên màn hình hẹp, bảng History vẫn cuộn ngang.
Kiểm tra
Đã chạy giao diện Qt offscreen tại kích thước 1900×650 với dữ liệu SQLite giả lập: hai bảng chia đúng tỷ lệ, Daily hiển thị tiêu đề và biểu tượng trắng; bộ lọc Daily, lịch sử Summary/Daily, PASS/FAIL và nút Close còn hoạt động. Chưa kiểm tra trực tiếp trên màn hình Windows và dữ liệu thực tế của bạn.



## 2026-09-23 — Slot Summary alarm và Export Excel

### File thay đổi / thêm mới

* `repositories/machine\\\_slot\\\_summary\\\_repository.py`: chỉ lấy alarm có alarm\_date từ From đến To (bao gồm hai ngày); bỏ slot Total Test = 0 khỏi Summary. Giữ nguyên dữ liệu Daily, kể cả các dòng 0.
* `ui/widgets/machine\\\_slot\\\_summary.py`: nền đỏ nhạt cho mọi dòng alarm, không phụ thuộc checkbox; sửa mô tả khoảng ngày; thêm Export Excel chạy QThread, có xử lý lỗi và hủy khi đóng ứng dụng.
* `services/machine\\\_slot\\\_export.py` (mới): tạo Excel 3 sheet, đọc database ở chế độ read-only, ghi file tạm rồi thay thế file đích khi hoàn tất.
* `tests/test\\\_machine\\\_slot\\\_export.py` (mới): kiểm tra khoảng ngày, dòng 0, yield thiếu mẫu, cửa sổ 15/30, chuỗi fail, bỏ retest và nội dung Excel.
* `read.md`, `changelog.txt`: bổ sung nội dung lần này, giữ các ghi chú cũ.

### Cách dùng

1. Chép đè các file trong gói vào đúng thư mục project hiện tại. Hai file mới phải được thêm vào project.
2. Khởi động lại app. Chọn From/To, bấm Search, chọn Machine/Slot và Chỉ hiện Alarm nếu cần.
3. Bấm Export Excel và chọn nơi lưu `.xlsx`. Đóng file Excel đích trước khi xuất đè.
4. Thư viện openpyxl đã có trong requirements.txt. Nếu đóng gói exe, build lại để có chức năng mới.

### Quy tắc dữ liệu

* `slot summary`: xuất những dòng đang hiển thị sau bộ lọc Machine/Slot/Alarm, đủ các cột Summary và thêm Last 15 Yield, Target 15, Last 30 Yield, Target 30, Fail Consecutive, Same Scrapcode Fail, Alarm 15, Alarm 30, ALARM.
* Last 15/30 Yield: lấy tối đa 15/30 lần test mới nhất của EQP–Slot trong khoảng ngày đang hiển thị, thứ tự DATE/TIME/id giảm dần, mọi TEST\_COUNT. Nếu thiếu mẫu vẫn tính PASS/(PASS+FAIL) trên số lần hiện có. Không dùng PASS/FAIL vì đây không phải công thức hiệu suất và có thể chia cho 0.
* Target 15/30 đọc từ machine\_slot\_yield\_config đã lưu trong DB lúc export; giá trị 50 nghĩa là 50%.
* Fail Consecutive: YES khi có chuỗi fail cùng model đủ ngưỡng cùng/khác scrapcode trong khoảng ngày. Dùng ngưỡng đã lưu continuous\_fail\_count và different\_scrap\_fail\_count (ví dụ 3 và 4). Chỉ xét TEST\_COUNT=0, bỏ qua các retest như quy tắc hiện tại. Không nối sang ngày ngoài From/To.
* Same Scrapcode Fail: YES nếu tồn tại chuỗi đủ ngưỡng cùng scrapcode; NO nếu chỉ có chuỗi khác scrapcode hoặc không có chuỗi. Nếu có cả hai loại, ưu tiên YES.
* Alarm 15/30: YES khi Last 15/30 Yield thấp hơn target tương ứng; đây là phép so sánh của báo cáo.
* ALARM: lấy alarm thực tế đã lưu có alarm\_date thuộc From/To; PASS nếu không có. Không tự tạo/xóa alarm khi export. Alarm thực tế có quy tắc phục hồi và cửa sổ lịch sử riêng, nên không nhất thiết bằng phép so sánh Alarm 15/30 của báo cáo.
* `Daily`: tất cả các cột và dòng đang hiển thị trong bảng Daily, có áp dụng bộ lọc riêng ở tiêu đề, vẫn giữ dòng Total Test = 0. Bộ lọc bên trái không thay đổi bảng Daily.
* `test history`: mọi lần test (mọi TEST\_COUNT) trong From/To của các EQP–Slot được xuất ở Summary; nhóm theo thứ tự Summary, mỗi slot mới nhất trước. Các cột Machine, Date, Time, Slot, Result, Part No, Lot No, Interface, Scrap Code, File, Serial, Qty, Test Count, Model, Tier.
* Database hiện tại không có Interface và File nên hai cột đó để trống, không suy đoán dữ liệu. Các trường còn lại lấy từ prime\_data.
* Excel có filter, freeze panes, xuống dòng ở 10 lần test gần nhất, tỷ lệ là số định dạng %, alarm nền đỏ nhạt. Chuỗi log/serial luôn là text để không trở thành công thức Excel.
* Khi số test/pass/fail thay đổi giữa lúc hiển thị và export, yêu cầu Search lại để tránh xuất lệch với bảng. Nếu vượt giới hạn dòng Excel, yêu cầu thu hẹp bộ lọc; không cắt bỏ dữ liệu âm thầm.

### Kiểm tra

* 2 bài unittest mới chạy thành công, bao gồm kiểm tra lại workbook bằng openpyxl.
* Kiểm tra biên dịch Python cho 3 module thay đổi thành công.
* Môi trường kiểm tra không có PyQt5 nên chưa chạy giao diện thực tế. Cần kiểm tra nút Export Excel và màu dòng trên máy Windows chạy app.



# Cập nhật Monitor Day 1–3 cho Alarm LI

## Cài đặt

Đóng ứng dụng, sao lưu các file cần thay rồi chép 3 file sau vào đúng thư mục project:

* repositories/alarm\_repository.py
* workers/alarm\_worker.py
* ui/pages/alarm\_page.py

tests/test\_alarm\_monitor.py là file kiểm thử bổ sung, không bắt buộc để chạy app.
Không cần tạo lại database. Nếu đang dùng EXE, build lại bằng quy trình hiện tại.
read.md và changelog.txt trong gói chỉ chứa nội dung cập nhật lần này; có thể nối vào tài liệu cũ.

## Cách hoạt động

* Bấm Search tại tab Alarm để tính và lưu Monitor, sau đó tải bảng. Luồng tải Alarm khi chuyển tab/ở Dashboard cũng cập nhật Monitor.
* Xét tất cả alarm có Status = Đã hoàn thành, theo EQP + Slot và Date complete của từng alarm.
* Bỏ toàn bộ ngày hoàn thành. Lấy 3 ngày có dữ liệu test đầu tiên sau ngày đó, theo thứ tự tăng dần; ngày không chạy không tính.
* Tính trên tất cả lượt test, mọi TEST\_COUNT và Model của slot; không giới hạn theo Model, Tier, Scrapcode hoặc khoảng ngày đang lọc bảng Alarm.
* Tất cả test trong ngày PASS → PASS. Có test không PASS → FAIL.
* Chưa đủ 3 ngày thì các cột còn thiếu để trống. Có sẵn 3 ngày thì điền cả 3 ngay trong một lần Search. Không xét ngày thứ 4.
* Ví dụ hoàn thành 21/09, chạy ngày 22, 25 và 28: Day 1 = 22/09, Day 2 = 25/09, Day 3 = 28/09.
* Dữ liệu tính đến ngày hiện tại trên máy chạy app. Nếu lấy ngày hôm nay, kết quả theo log đã nhập tại thời điểm Search; có thể thay đổi khi nhập thêm log.
* Search tính lại 3 ngày đầu để phản ánh nhập bổ sung/nhập lại log. Không đóng băng kết quả cũ.
* Kết quả lưu trong database; PASS màu xanh, FAIL màu đỏ, các cột Monitor vẫn chỉ đọc.
* Đổi Status sẽ xóa Monitor cũ. Hoàn thành lại bắt đầu theo Date complete mới.
* Date complete trống/sai định dạng sẽ để trống Monitor, không đoán ngày.
* Bảo toàn các thông tin xử lý khác. Cập nhật có transaction và row\_version; database bận sẽ báo lỗi và yêu cầu Search lại.

## Kiểm thử

Chạy: python -m unittest tests.test\_alarm\_monitor -v
4 bài kiểm thử mới đều đạt: ngày không liên tiếp, loại ngày hoàn thành, đủ/thiếu 3 ngày, khác EQP/Slot, mọi test count/model, nhập lại log, version conflict, đổi Status, ngày lỗi/tương lai và database bận.
Kiểm tra cú pháp cả 3 file ứng dụng đạt.
Bộ test\_alarm cũ: 15 bài, 4 lỗi giống nhau ở bản gốc và bản sửa (2 failures, 2 errors).
Chưa chạy giao diện Windows/PyQt5 hoặc build EXE trong môi trường này.







# LI App v1.14 — Tooltip cho tất cả biểu đồ

## Cài đặt

1. Đóng LI App. Sao lưu thư mục `ui/charts` hiện tại.
2. Giải nén gói cập nhật. Chép thư mục `ui` vào thư mục project có `main.py`, chọn ghi đè các file trùng tên. Không chép vào thư mục cha bên ngoài project.
3. Chạy lại `main.py`. Nếu sử dụng bản EXE, cần build lại bằng quy trình PyInstaller hiện tại rồi phân phối bản mới; chép file Python cạnh EXE không cập nhật code đã đóng gói.

Gói chỉ chứa 6 file Python cần thêm/thay thế, cùng read.md và changelog.md. Không cần sửa database hay cài thư viện mới trên máy đã chạy được app.

## Cách sử dụng

Rê chuột vào phần màu của cột hoặc gần điểm trên đường Yield. Ô thông tin xuất hiện cạnh con trỏ, tự ẩn khi rời vùng dữ liệu, chuyển tab hoặc cập nhật biểu đồ. Không cần bấm chuột.

|Biểu đồ|Nội dung tooltip|
|-|-|
|Cum Yield LI theo EQP|EQP, In, Out, Fail, Fail PPM tổng, Yield|
|Cum Yield LI Daily / Prime Yield LI Daily|EQP, ngày đầy đủ, Scrap Code và Scrap PPM của phần cột đang trỏ, In, Out, Fail, Fail PPM tổng, Yield|
|Cum Yield by Model|Model, Scrap Code, Scrap Qty, In, Out, Fail, Fail PPM tổng, Yield|
|Slot Fail Prime|EQP, Slot, In, Pass, Fail, Fail PPM tổng, Yield|
|Yield slot theo ngày|EQP, Slot, ngày đầy đủ, In, Pass, Fail, Fail PPM tổng, Yield|

* Điểm Yield hiển thị thông số tổng hợp của dòng tương ứng; không gán điểm Yield cho một Scrap Code.
* Cột chồng hiển thị đúng phần màu đang trỏ, không lấy chiều cao cộng dồn làm PPM của mã lỗi.
* Với cột Fail bằng 0, trỏ sát chân cột. Phần Scrap Code có PPM/Qty bằng 0 không được biểu đồ tạo cột nên không có phần màu để trỏ.
* Nếu điểm Yield trùng vị trí cột, tooltip ưu tiên điểm Yield. Di chuyển xuống phần màu để xem mã lỗi.
* Dữ liệu không có mẫu số hoặc Yield chưa xác định hiển thị N/A; không hiểu nhầm là Yield thực tế bằng 0%.
* Fail PPM tổng lấy trực tiếp từ dòng thống kê; nếu dòng không có trường này thì tính Fail / In × 1.000.000 khi In > 0. Không suy ngược Scrap Qty từ PPM đã làm tròn.
* Số liệu dùng đúng kết quả đang vẽ theo bộ lọc hiện tại. Không truy vấn database mỗi lần di chuột.

## Danh sách file

* Mới: `ui/charts/chart\\\\\\\_hover.py` — xử lý tooltip và định dạng dữ liệu dùng chung.
* Thay thế: `ui/charts/cum\\\\\\\_daily\\\\\\\_chart.py`.
* Thay thế: `ui/charts/cum\\\\\\\_eqp\\\\\\\_chart.py`.
* Thay thế: `ui/charts/cum\\\\\\\_model\\\\\\\_chart.py`.
* Thay thế: `ui/charts/slot\\\\\\\_daily\\\\\\\_chart.py`.
* Thay thế: `ui/charts/slot\\\\\\\_fail\\\\\\\_chart.py`.

## Kiểm tra

Đã kiểm tra cú pháp 6 file và chạy kiểm tra tọa độ với Matplotlib Agg thực, phần Qt được giả lập: cả 5 lớp biểu đồ, phần cột chồng, hai trục, điểm Yield sát biên, cột 0, đổi lựa chọn Scrap Code trên dữ liệu được cache, trạng thái rỗng, N/A và số callback không tăng khi cập nhật.

Chưa chạy giao diện PyQt5/Windows thực vì môi trường kiểm tra không có PyQt5 và không tải được gói cài. Sau khi cập nhật, kiểm tra rê chuột trên các biểu đồ, đổi ngày/EQP/Scrap Code, chuyển tab và Copy chart trên máy chạy app.





# Dashboard – bố cục gọn và 3 biểu đồ

Áp dụng cho project trong LI-update0.zip.

## Cài đặt

1. Đóng ứng dụng và sao lưu ui/pages/dashboard\_page.py.
2. Thay ui/pages/dashboard\_page.py bằng file cùng đường dẫn trong gói.
3. Thêm ui/charts/dashboard\_bar\_chart.py vào project.
4. Chạy lại main.py. Chọn From/To, Search, mở Dashboard. Nếu dùng exe, build lại từ source đã cập nhật.

Không cần thay database hoặc import lại dữ liệu. Dùng PyQt5, matplotlib, chart\_hover.py và clipboard\_utils.py đã có trong project; không cần thêm thư viện mới.

## Bố cục

* 10 ô tổng cao 64 px (trước đây 92 px).
* Phần dưới: bảng khoảng 25%, alarm theo ngày 30%, trạng thái action 15%, effectiveness theo ngày 30% chiều rộng khả dụng.
* Bảng giữ đủ 11 cột, chữ và hàng gọn hơn. Kéo thanh cuộn ngang dưới bảng để xem các cột bên phải; có thể kéo mép cột để đổi độ rộng.
* Tiêu đề bảng cùng nền trung tính. Chỉ các ô giá trị Đã hoàn thành và Action Effectiveness có nền xanh.

## Biểu đồ

1. Alarm phát sinh theo ngày: X là từng ngày trong From/To, Y là số dòng alarm của ngày đó.
2. Trạng thái action: đúng 3 cột theo thứ tự Đã hoàn thành, Đang tiến hành, Chưa tiến hành; số lượng cộng trong khoảng ngày.
3. Action Effectiveness theo ngày: số hoàn thành / số phát sinh của ngày × 100%; Y từ 0% đến 100%.

Tất cả là cột xanh #4472C4, nền trắng, khung xám và lưới giống phong cách biểu đồ Summary/Yield Slot; có nhãn giá trị, tooltip và chức năng copy ảnh theo tiện ích biểu đồ hiện có. Khoảng nhiều ngày có thanh cuộn ngang riêng để giữ đủ nhãn ngày.

Ngày không có alarm vẫn xuất hiện, số lượng và effectiveness bằng 0. Tỷ lệ tổng trên ô phía trên vẫn bằng tổng hoàn thành / Total Alarm, không lấy trung bình tỷ lệ các ngày.

Giữ nguyên nguồn dữ liệu bản gốc: snapshot các dòng đang hiển thị ở tab Alarm, gồm bộ lọc cột của tab Alarm. Muốn thống kê tất cả alarm trong khoảng ngày, bỏ bộ lọc cột tại tab Alarm. Bảng và 3 biểu đồ cùng cập nhật khi nhận snapshot mới.

## Kiểm tra

Đã chạy PyQt5 offscreen với dữ liệu mẫu: số cột, số lượng, tỷ lệ, trạng thái tương đương, ngày trống, đổi khoảng ngày, xóa dữ liệu cũ, tỷ lệ chiều rộng và cuộn ngang 30 ngày. Đã xem giao diện ở chiều rộng 1366 và 1900 px. Chưa chạy trực tiếp trên Windows/database sản xuất.



Monitor cập nhật khi import ngày quá khứ
Cài đặt
Áp dụng cho LI-lastest.zip đã gửi, kể cả đã áp dụng LI_Alarm_Search_Busy_Fix.zip.
Đóng app, sao lưu và thay đủ 4 file theo đúng đường dẫn:
repositories/alarm_repository.py
repositories/prime_repository.py
workers/alarm_worker.py
controllers/prime_controller.py
Nếu chạy EXE, build lại app và các EXE import dùng những module này, đặc biệt Auto Import Yesterday. Bản Today mới vẫn giữ hành vi cũ. Cập nhật gói phát hành launcher nếu dùng launcher.
Không cần tạo lại database hoặc đổi schema. tests là kiểm thử, không bắt buộc để chạy app.
Bản này thay thế luồng xử lý khóa Monitor trong gói sửa trước.
Luồng mới
Search/mở Alarm hoặc Dashboard: chỉ đọc kết quả đã lưu; không tính, không ghi và không xin khóa ghi để cập nhật Monitor.
Auto Import Yesterday: tính Monitor sau khi thay log và đồng bộ Alarm, trước commit. PRIME, Alarm và Monitor cùng transaction; nếu tính Monitor lỗi thì rollback toàn bộ lần import.
Import PRIME thủ công cho ngày quá khứ, kể cả nhập lại nhiều ngày: tính lại các Alarm đã hoàn thành thuộc EQP/Slot bị ảnh hưởng bởi những ngày đó. Bao gồm slot có trong dữ liệu cũ nhưng biến mất khỏi dữ liệu mới.
Chỉ UPDATE Monitor khi kết quả thay đổi; giữ nguyên Status, Engineer, Date complete, Comment và các trường xử lý khác. row_version tăng khi Monitor đổi để tránh ghi đè từ giao diện cũ.
Import Today vẫn thay log, tính Alarm, đồng bộ TIER như cũ; không tính/ghi Monitor. Không sửa auto_import_today_main.py.
Dữ liệu ngày hôm nay không được tính vào Monitor khi import một ngày quá khứ. Ngày hiện tại lấy theo đồng hồ máy chạy import.
Quy tắc Monitor giữ nguyên
Lấy 3 ngày có test đầu tiên sau ngày Date complete cho đúng EQP/Slot, bỏ qua ngày không có test; dùng tất cả test count và Model. Mỗi ngày chỉ PASS nếu toàn bộ test PASS, có FAIL thì FAIL. Chưa có đủ 3 ngày thì các ô còn lại trống. Không tính lại Alarm chưa ở trạng thái Đã hoàn thành hoặc Date complete không hợp lệ.
Nhập lại một ngày có thể thay đổi thứ tự Day 1/2/3 nếu ngày đó thêm hoặc mất dữ liệu, nên tính lại bộ 3 ngày liên quan.
Lưu ý sử dụng
Auto Import Yesterday vẫn bỏ qua ngày đã được đánh dấu import thành công như trước. Cần nhập lại thì dùng nút Import PRIME chọn ngày đó.
Kết quả Monitor đã lưu được giữ tới lần import ngày quá khứ liên quan tiếp theo. Search không tự bổ sung kết quả còn thiếu; có thể Import PRIME lại các ngày cần theo dõi để cập nhật.
Đổi Status vẫn đặt/xóa Date complete và xóa Monitor theo quy tắc cũ; kết quả được bổ sung ở lần import ngày quá khứ liên quan tiếp theo.
Kiểm thử
7 kiểm thử đạt trên SQLite tạm, gồm: import/re-import, không ghi lại khi kết quả không đổi, slot biến mất và sắp lại ngày, cô lập Today/slot khác, Search khi có khóa ghi, rollback khi tính Monitor lỗi, luồng Task Scheduler Yesterday và Today thật với log TCP.
Chưa kiểm thử trên ổ mạng Windows thực tế.
Chạy từ thư mục project: python -m unittest tests.test_monitor_import_flow -v
Các test_monitor cũ kiểm tra refresh_monitors khi Search đã không còn phù hợp với luồng mới.

25.09
LI v1.15 — Sửa khóa database, snapshot log và chẩn đoán (25/09/2026)
Gói này chỉ chứa file mới/file thay đổi so với `LI_App_v1.15-master(1).zip`.
1. Cài đặt
Dừng các lượt auto import/auto mail đang chạy và đóng app trước khi thay EXE. Giữ bản sao source/EXE cũ để quay lại nếu cần.
Giải nén gói, chép đè đúng các đường dẫn tương đối vào thư mục project có `main.py`. Hai file mới trong `database/` là bắt buộc.
Không cần tạo lại database, không xóa `import_lock` thủ công. Bản sửa không đổi schema dữ liệu.
Nếu chạy EXE, phải build và thay cả app chính, Auto Import, Auto Import Today và Auto Send Mail. Chỉ thay `.py` không cập nhật EXE cũ:
```bat
python -m PyInstaller --noconfirm --clean LI_Yield.spec
python -m PyInstaller --noconfirm --clean Auto_Import_Log.spec
python -m PyInstaller --noconfirm --clean Auto_Import_Log_Today.spec
python -m PyInstaller --noconfirm --clean Auto_Send_Mail.spec
```
Dùng lại các tham số đường dẫn database trong Task Scheduler. Triển khai app đã build tới các máy đang dùng database chung để thu đủ log của bên đọc lẫn bên ghi. Launcher không đổi source; nếu dùng cơ chế phát hành qua launcher, cập nhật bộ EXE mà launcher phân phối theo cách đang sử dụng.
2. Cơ chế khóa
Tạo khóa import: chờ SQLite tối đa 60 giây cho mỗi thao tác bị tranh chấp, thay cho 0,25 giây; giống timeout của Aging. SQLite tự chờ/thử lại theo busy timeout, không mở thêm lượt import hay tự chạy lại toàn bộ job.
Refresh/release khóa: timeout 60 giây thay cho 1 giây.
Kiểm tra/khởi tạo schema: timeout 60 giây thay cho 5 giây.
Heartbeat mỗi 60 giây như Aging, lease vẫn 15 phút. Dừng heartbeat chờ tối đa 5 giây mỗi lần gọi. Nếu nó chưa dừng ở trước bước thay dữ liệu, import dừng có lỗi thay vì cho hai luồng cùng đi tiếp vào giai đoạn ghi.
Vẫn kiểm tra đúng batch sở hữu khóa. Không cưỡng bức xóa khóa của job khác, không bỏ khóa SQLite, không bật WAL trên database dùng chung qua mạng.
Giữ transaction thay PRIME/TIER/Alarm/Monitor nguyên tử. Không chia nhỏ commit dữ liệu khiến người dùng nhìn thấy trạng thái nửa chừng.
Vẫn giữ autocommit nền `isolation_level=None` của LI; không sao chép nguyên connection của Aging vì các hàm LI đang phụ thuộc cơ chế này. Thao tác sửa Alarm thủ công vẫn phản hồi nhanh khi bận; không bắt UI đợi 60 giây.
60 giây là busy timeout của SQLite theo thao tác, không phải hạn tổng của toàn job và không giới hạn được mọi I/O mạng ở cấp hệ điều hành. Khóa dài hơn vẫn có thể gây lỗi; đây không phải cam kết hết mọi lỗi khóa.
3. Rút ngắn khóa đọc
Machine/Slot Summary: đọc dữ liệu nhất quán, đóng kết nối rồi mới dựng bảng và các dòng Daily.
Chuẩn bị mail: giữ snapshot nhất quán; lấy chi tiết các chuỗi fail bằng một truy vấn theo bảng phạm vi TEMP. Đóng kết nối trước khi nhóm, lọc và dựng kết quả. Giữ nguyên phạm vi ngày/giờ, model, scrap code và thứ tự chi tiết.
Export Machine Slot: chép cấu hình, alarm và dữ liệu PRIME của khoảng ngày cần xuất vào SQLite tạm cục bộ. Nhả kết nối database chung trước khi tính chỉ số, tạo/định dạng Excel. Cần dung lượng tạm tương ứng dữ liệu trong khoảng ngày chọn; file tạm được dọn sau khi hoàn tất/lỗi.
Snapshot vẫn cần khóa đọc trong lúc lấy dữ liệu. Không giữ khóa của database chung trong suốt phần định dạng Excel nữa.
4. File log đang được cập nhật
Mỗi file được mở nhị phân, chốt số byte lúc mở, đọc tối đa số byte đó vào bộ nhớ rồi đóng file.
Parse/ghi staging từ các byte đã đọc. Không kiểm tra lại kích thước, mtime hay danh sách file ở cuối import. File thay đổi sau khi đọc không làm hủy dữ liệu đã đọc.
Các file được chụp lần lượt, không phải snapshot đồng thời của tất cả máy. File mới xuất hiện sau khi quét, và phần được ghi thêm sau mốc chụp, sẽ được lấy ở lần import kế tiếp.
Chỉ lấy các dòng đã có ký tự kết thúc dòng. Dòng cuối chưa có xuống dòng được để lại cho lần sau; áp dụng UTF-8/ANSI và UTF-16, tránh import serial/trường dữ liệu bị cắt giữa chừng. File tĩnh không có xuống dòng cuối phải được thêm xuống dòng để lấy dòng cuối đó.
Vẫn báo lỗi nếu dòng hoàn chỉnh có dữ liệu không hợp lệ, không đọc được file hoặc staging không có sản phẩm; không xóa dữ liệu cũ trong các trường hợp này.
Không bảo đảm snapshot nhất quán nếu bên tạo log sửa đè ngay các byte đang đọc. Cách này dành cho log ghi nối tiếp; không thực hiện khóa file của máy test.
5. Log cần lấy khi sự cố xuất hiện
Log tổng hiện có
Các file log import/mail cũ vẫn ở vị trí đang dùng. Mỗi thông báo có thêm `[PID=...]` để ghép với log chẩn đoán.
Log chẩn đoán mới
Trên Windows, mở Run và nhập:
```text
%LOCALAPPDATA%\LI_App\logs
```
Đây là thư mục của tài khoản chạy tác vụ. Task Scheduler dùng tài khoản khác thì log nằm trong profile của tài khoản đó. Nếu biến LOCALAPPDATA không có, dùng thư mục tạm của tài khoản rồi `LI_App/logs`.
`li_diagnostic_<PID>_<run>.jsonl`: log riêng từng tiến trình; mỗi dòng là JSON. Tự xoay khi đạt 5 MiB, giữ tối đa 3 bản `.1`/`.2`/`.3` cho file đó. Các lượt chạy khác tạo file riêng; có thể dọn các lượt cũ sau khi đã đối chiếu xong.
`li_diagnostic_<PID>_<run>.stacks.log`: auto import/auto mail chụp stack các thread mỗi 120 giây nếu tiến trình còn hoạt động. Đây là ảnh chụp theo chu kỳ, không tự kết luận job bị treo và không tự kill tiến trình.
Nếu thư mục log không ghi được, việc ghi chẩn đoán không được phép làm hỏng import. Kiểm tra quyền ghi nếu không thấy file mới.
Thông tin có trong log: máy chạy, PID/PPID, run ID, thread, connection ID, đường dẫn database, timeout, nơi gọi trong source, loại SQL/bảng, thời gian thực hiện, trạng thái transaction, mã lỗi SQLite; batch và chủ sở hữu khóa import; các mốc đọc file, số byte, staging/TIER/Alarm/commit/cleanup.
Không ghi SQL parameters, mật khẩu hay nội dung mail vào log chẩn đoán. Đường dẫn database và log nguồn có được ghi để phân biệt các tác vụ.
Các mốc quan trọng:
Mốc	Cách đọc
`DB_OPEN_BEGIN` không có `DB_OPENED`	Có thể đang mắc khi mở database/truy cập đường dẫn; đối chiếu stack
`DB_BEGIN`/`DB_END`	Bắt đầu/kết thúc một lời gọi SQLite; SELECT có thể còn fetch dữ liệu sau DB_END
`DB_ERROR`, operation `COMMIT`	Không hoàn tất commit; có thể chờ bên đọc, không mặc nhiên là có người ghi
`DB_CLOSE_BEGIN`/`DB_CLOSED`	Thời gian sống connection; transaction đọc mở được rollback khi đóng
`IMPORT_LOCK_BUSY_OWNER`	Chủ sở hữu khóa phiên khác: máy/PID/batch/expiry; không phải kết quả tìm chủ khóa đọc SQLite
`READ_SNAPSHOT_MAIN_CLOSED`	Export đã nhả database chung và chuyển sang dữ liệu tạm
`FILE_TAIL_DEFERRED`	Dòng cuối chưa hoàn chỉnh, để lần import sau
`PROCESS_EXIT_REQUEST`	Main đã trả về; chưa chứng minh EXE đã biến mất khỏi Task Manager
`PROCESS_PYTHON_SHUTDOWN`	Đã đi đến callback kết thúc Python; chưa chứng minh bootloader/Windows đã kết thúc
Khi còn lỗi: giữ log tổng, toàn bộ jsonl (kể cả file xoay) và stacks của đúng PID, giờ sự cố, PID trong Task Manager, đường dẫn EXE; thu log của app chính/auto mail ở các máy cùng dùng DB trong cùng thời điểm. SQLite không cung cấp PID của mọi reader đang giữ khóa, nên log một tiến trình import riêng không đủ xác định bên chặn nó.
6. Kiểm chứng
24 test parser/import và hồi quy mới đã pass: reader contention >0,25 giây, partial tail UTF-8/UTF-16, file đổi sau khi đọc, lỗi validation giữ dữ liệu cũ/nhả khóa, snapshot export không giữ DB chung, mail evidence, log không ghi parameters, stop heartbeat, bảo vệ khóa phiên khác và Report chỉ đọc.
Đối chiếu trực tiếp source gốc và source sửa trên dữ liệu mẫu: kết quả Machine Slot Summary, bằng chứng mail và dữ liệu/định dạng 3 sheet Excel trùng khớp.
Chưa chạy/build EXE Windows hoặc kiểm thử trên SMB thực tế. Môi trường kiểm tra không có PyQt5 nên chưa kiểm thử GUI.
Một số test cũ trong project đã lỗi trên source gốc (Machine Slot Summary còn kỳ vọng dòng trống, Alarm Monitor gọi hàm cũ không còn tồn tại). Không sửa logic ứng dụng chỉ để đáp ứng các test cũ này.
Chạy nhóm test dành cho bản sửa từ thư mục project:
```bat
python -m unittest tests.test_tcp_import tests.test_lock_snapshot_diagnostics -v
```



LI — cập nhật Alarm và Machine Slot Yield (30/09/2026)
Cài đặt
Đóng ứng dụng LI; chờ các tác vụ đang chạy hoàn tất.
Giải nén và chép các thư mục repositories, services, ui đè vào thư mục project chứa main.py, giữ nguyên cấu trúc đường dẫn.
Mở lại app. Nếu dùng bản EXE, build lại từ source đã cập nhật.
Nội dung thay đổi
Thêm cột No ở đầu bảng trong dialog Slot Fail History của Alarm và dialog Test History mở từ Summary/Daily của Machine Slot Yield. Đánh số từ 1 theo thứ tự hiển thị; khi đổi chuỗi alarm, đánh số lại từ 1. Giữ màu PASS/FAIL đúng cột Result.
Thêm Fail comment giữa YIELD và Lần 1 ở Machine / Slot Summary. Lấy nguyên nội dung fail_comment trong bảng slot_fail_alarm, cùng nguồn với tab Alarm; chỉ lấy alarm_date trong From–To đang chọn. Nếu có nhiều ngày alarm, gộp các nội dung khác nhau, ngày mới trước; không lặp nội dung giống nhau. Slot không có alarm trong khoảng này để trống.
Cột Fail comment có chiều ngang gọn; rê chuột để đọc đầy đủ. Bấm slot ở Summary để xem đầy đủ nội dung trong dialog lịch sử.
Bấm slot ở Daily: lịch sử vẫn chỉ lấy đúng ngày đó; Fail comment chỉ lấy alarm của chính slot và ngày đó. Dialog Alarm cũng hiển thị Fail comment của alarm đang mở.
Thu gọn vùng Daily và chiều ngang các cột, dành thêm chỗ cho Summary; vẫn giữ bộ lọc Daily và khả năng kéo thanh chia hai bảng.
Export Excel của Slot Summary có thêm Fail comment cùng vị trí với bảng; dịch đúng các cột và định dạng phần trăm tương ứng. Không thay cách tính các chỉ số export.
Bộ lọc chung lúc mở app: To = ngày hiện tại trên máy chạy ứng dụng; From = To trừ 14 ngày. Ví dụ 30/09/2026 → From 16/09/2026, To 30/09/2026. Khoảng truy vấn vẫn bao gồm cả hai đầu ngày như trước.
Alarm hiệu suất 15 và 30: giữ điều kiện Yield thấp hơn target hiện có, nhưng cùng dùng 8 test mới nhất của slot làm điều kiện phục hồi (thay 6 cho Yield 15 và 10 cho Yield 30). Nếu 8 test đều PASS, bỏ qua cả hai alarm hiệu suất; nếu có FAIL trong 8 test, vẫn xét Yield/target theo logic hiện có. Đây là quy tắc hiệu suất, không yêu cầu 15 hoặc 30 test đều FAIL.
Giữ cách chọn chuỗi/model, phạm vi lịch sử và TEST_COUNT của các quy tắc. Điều kiện 8 test vẫn xét toàn slot như cơ chế cũ. Hai quy tắc fail liên tiếp cùng/khác scrapcode không đổi.
Dữ liệu alarm đã lưu
Quy tắc mới áp dụng khi chạy tính alarm trong luồng import. Alarm cũ không tự tính lại khi Search hoặc chỉ mở app. Muốn cập nhật ngày đã lưu, import lại PRIME cho ngày tương ứng, sau đó Search lại. Không thay schema, cơ chế transaction/khóa DB hoặc thao tác theo dõi alarm trong bản vá này.
Kiểm tra đã thực hiện
Biên 5/6/7/8/9/10 test PASS gần nhất; 7 PASS chưa bỏ alarm, 8 PASS bỏ cả hai alarm hiệu suất khi không có quy tắc khác vi phạm.
Một FAIL tại từng vị trí trong 8 test mới nhất đều cho phép xét tiếp Yield 15/30.
DB SQLite tạm: import/tính alarm, đọc Fail comment sang Summary/Daily và dialog Alarm.
GUI Qt offscreen: đánh số đầu/cuối bảng, cột Result và màu PASS/FAIL, vị trí 10 kết quả gần nhất, khoảng ngày mặc định; xem ảnh render của bảng và dialog.
Export Excel: Fail comment, vị trí các cột và định dạng Yield sau khi thêm cột.
Biên dịch cú pháp toàn bộ source. Chưa chạy trên máy Windows sản xuất hoặc database thực tế của người dùng.
File source cần thay
repositories/machine_slot_summary_repository.py
repositories/alarm_history_repository.py
services/alarm_builder.py
services/machine_slot_export.py
ui/dialogs/slot_fail_history_dialog.py
ui/widgets/machine_slot_summary.py
ui/widgets/filter_panel.py



LI — cache chuyển tab và cập nhật Machine Slot Yield (30/09/2026)
Áp dụng trên source LI_LATEST (2).zip do người dùng cung cấp.
Cài đặt
Đóng app LI, chờ các tác vụ đang chạy hoàn tất.
Giải nén gói và chép đè các file source vào thư mục chứa main.py, đúng cấu trúc thư mục.
Mở lại app. Nếu sử dụng EXE, build lại từ source đã cập nhật.
1. Chuyển tab và Search
Tách sự kiện chuyển tab khỏi nút Search.
Alarm và Dashboard dùng chung kết quả Alarm đã tải cho From–To. Qua lại hai tab hoặc quay lại từ tab khác không chạy truy vấn lại nếu khoảng ngày không đổi và dữ liệu chưa bị đánh dấu thay đổi.
Machine Slot Yield giữ kết quả của khoảng ngày đã tải. Quay lại cùng khoảng ngày không khởi chạy worker mới.
Khi đổi From–To rồi Search ở tab khác, Machine Slot Yield đọc ngày trên bộ lọc lúc được mở và cập nhật nếu chưa có kết quả đúng khoảng đó. Alarm/Dashboard cũng kiểm tra khoảng ngày khi mở.
Nếu đổi From–To nhưng chưa Search, khi chuyển sang tab thống kê khác, tab đó vẫn áp dụng ngày đang hiển thị trên bộ lọc như hành vi hiện có.
Bấm Search chủ động ở Alarm/Dashboard vẫn đọc lại Alarm để có thể lấy dữ liệu mới từ tiến trình import khác. Bấm Search ở Machine Slot Yield kiểm tra phiên bản dữ liệu và dùng cache để giảm phần phải đọc lại.
Các tab này vốn truy vấn theo From–To; bản sửa giữ nguyên phạm vi các bộ lọc hiện có. Lọc Machine/Slot/Chỉ hiện Alarm và lọc cột vẫn hoạt động trên kết quả hiện tại.
Import PRIME thành công trong app làm mất hiệu lực kết quả Alarm; Machine Slot Yield được đánh dấu cần cập nhật cả khi đang ẩn. Khi quay lại sẽ cập nhật đúng dữ liệu.
2. Cache Machine Slot Yield trong phiên mở app
Lưu theo ngày: tổng số test, Pass/Fail theo Machine–Slot và tối đa 10 test mới nhất của mỗi slot trong ngày. Không giữ toàn bộ log hoặc toàn bộ lịch sử test chi tiết trong RAM.
Lần đầu đọc đầy đủ khoảng ngày được chọn.
Lần Search hoặc tự cập nhật sau đó: kiểm tra imported_at, batch_id và row_count trong data_import_status của PRIME. Ngày đã tải và không đổi được dùng lại; chỉ truy vấn lại ngày mới hoặc ngày đã import lại.
PRIME đang thay thế dữ liệu nguyên ngày khi import. Vì vậy bản sửa đọc lại trọn ngày bị thay đổi, không chỉ nối các dòng có thời gian mới hơn. Cách này xử lý đúng dữ liệu bị sửa/xóa, slot biến mất hoặc số test giảm khi import lại ngày cũ, tránh đếm trùng.
Nếu mở rộng khoảng ngày, dùng lại phần giao nhau và đọc phần mới; nếu thu hẹp, chỉ ghép những ngày nằm trong khoảng mới. Các ngày đã xem vẫn có thể dùng lại khi quay lại khoảng cũ, sau khi kiểm tra phiên bản import.
Ghép lại tổng, Daily và 10 kết quả mới nhất đúng thứ tự DATE/TIME/id. Fail comment được đọc lại từ bảng alarm trong cùng read transaction.
Ngày có dữ liệu cũ nhưng không có metadata import được đọc lại để bảo đảm đúng; ngày trống được kiểm tra xem đã có dữ liệu hay chưa.
Không đổi schema, không ghi thêm dữ liệu cache vào database và không sửa cơ chế khóa/transaction ghi hiện có.
Cache chỉ tồn tại trong RAM khi app mở. Đóng app thì cache mất; lần mở sau tải lại lần đầu. Lịch sử chi tiết khi click slot và export vẫn theo luồng truy vấn hiện có.
Bộ hẹn giờ vẫn là 10 phút, chạy khi Machine Slot Yield đang hiển thị như bản gốc. Bộ lọc To không tự chuyển sang ngày mới; muốn xem ngày mới sau nửa đêm cần đổi To.
Cache dựa trên metadata được các luồng import PRIME hiện tại ghi cùng transaction. Chỉnh SQL trực tiếp ở ngoài app mà không cập nhật metadata không thuộc cơ chế phát hiện thay đổi này; trường hợp đó cần mở lại app để xóa cache.
3. Loading và vòng đời tác vụ
Bấm Search tại Machine Slot Yield hiển thị LoadingDialog/spinner sẵn có của app.
Tự cập nhật định kỳ vẫn chạy nền, không mở dialog loading chặn thao tác.
Nếu có yêu cầu mới trong lúc worker đang chạy, gộp yêu cầu và xử lý khoảng ngày mới nhất; loading đóng khi yêu cầu cuối hoàn tất.
Khi lỗi, giữ kết quả/cache thành công trước đó và thông báo dữ liệu có thể cũ; lần sau được phép thử lại. Khi đóng app, hủy/đợi worker theo cơ chế hiện có và dọn loading.
Kiểm tra
Đối chiếu Summary, Daily, 10 kết quả mới nhất và Fail comment với repository gốc trên cùng SQLite tạm.
Xác nhận không đọc lại thống kê ngày không đổi; kiểm tra mở rộng/thu hẹp/quay lại khoảng ngày, thêm ngày mới và thay thế ngày cũ làm giảm số test/mất slot.
Kiểm tra dữ liệu không có metadata, ngày trống có dữ liệu mới, lỗi và hủy giữa chừng không làm hỏng cache cũ.
GUI Qt offscreen: qua lại Alarm/Dashboard/Machine Slot Yield, Search ở một tab rồi sang tab khác, đổi ngày chưa Search, loading khi Search, cập nhật định kỳ, import lúc tab ẩn, lỗi rồi thử lại.
Kiểm tra yêu cầu Search mới trong lúc worker chạy và đóng app khi worker chưa hoàn tất; kiểm tra cú pháp source.
Test hồi quy test_slot_tab_refresh có kiểm tra cũ về chiều rộng cột (80 < 64) thất bại giống nhau trên source gốc và source sửa; không sửa UI ngoài phạm vi để đáp ứng kiểm tra này. Test cũ cũng cần đợi worker bộ lọc tải xong trước khi đọc danh sách.
Chưa đo tốc độ trên database sản xuất hoặc chạy trực tiếp trên máy Windows của người dùng; mức giảm thời gian phụ thuộc lượng ngày được dùng lại.
File cần thay
repositories/machine_slot_summary_repository.py
controllers/prime_controller.py
ui/widgets/machine_slot_summary.py
ui/pages/prime_page.py



LI — Chỉ hiện Alarm còn thỏa điều kiện trong 3 ngày gần nhất
Áp dụng trên LI_LATEST (3).zip — 30/09/2026.
Cài đặt
Đóng app, giải nén và chép đè các file đúng cấu trúc thư mục vào project chứa main.py. Mở lại app; nếu dùng EXE thì build lại source.
Cách hoạt động
Khi tích “Chỉ hiện Alarm” ở Machine Slot Yield, chỉ giữ slot đồng thời thỏa cả hai điều kiện:
Slot đã là alarm trong khoảng From–To đang hiển thị (cùng nguồn bảng slot_fail_alarm của tab Alarm).
Kiểm tra lại dữ liệu test của slot trong 3 ngày gần nhất và còn thỏa ít nhất một quy tắc alarm hiện có.
Ba ngày là hôm nay và 2 ngày trước, theo ngày trên máy chạy app; bao gồm cả hai đầu. Ví dụ hôm nay 30/09/2026 thì chỉ xét test ngày 28, 29, 30/09/2026.
Cửa sổ kiểm tra 3 ngày độc lập với From–To của bảng. Tổng Test/Pass/Fail/Yield, Daily và 10 kết quả gần nhất vẫn thuộc khoảng From–To đã chọn.
Chỉ các dòng đạt hai điều kiện trên được hiển thị và giữ nền đỏ. Không tạo thêm dòng cho slot không có dữ liệu trong bảng Summary của From–To hiện tại.
Bỏ tích: trở lại cách hiển thị/tô đỏ cũ theo alarm trong From–To.
Quy tắc được kiểm tra lại
Dùng chung bộ tính alarm hiện có; thêm phạm vi cho phép chuỗi/cửa sổ kết thúc tại bất kỳ ngày nào trong 3 ngày xét.
Yield 15: phải đủ 15 test theo model, Yield thấp hơn Target 15 đang lưu.
Yield 30: phải đủ 30 test theo model, Yield thấp hơn Target 30 đang lưu.
Hai quy tắc Yield dùng mọi TEST_COUNT. Nếu 8 test mới nhất của toàn slot trong phạm vi xét đều PASS thì bỏ qua cả hai quy tắc Yield.
Fail liên tiếp cùng Scrapcode: dùng ngưỡng đang cấu hình (ví dụ 3), cùng model, chỉ TEST_COUNT = 0.
Fail liên tiếp khác Scrapcode: dùng ngưỡng đang cấu hình (ví dụ 4), cùng model và có ít nhất 2 Scrapcode khác nhau trong chuỗi, chỉ TEST_COUNT = 0.
Tất cả test tham gia phải nằm trong 3 ngày; không lấy test trước đó để bù đủ 15/30 hoặc nối dài chuỗi fail.
Không đủ số test/chuỗi trong 3 ngày thì không đạt quy tắc tương ứng. Chỉ cần một trong bốn quy tắc đạt là giữ slot.
Giữ cách tìm chuỗi của quy tắc hiện tại: một chuỗi fail hợp lệ xuất hiện trong 3 ngày vẫn có thể đạt quy tắc fail liên tiếp, kể cả có test PASS sau chuỗi. Không thêm điều kiện phục hồi mới cho hai quy tắc Scrapcode. Điều kiện 8 PASS chỉ áp dụng cho Yield 15/30.
Cập nhật và cache
Khi tích checkbox, chạy kiểm tra trên worker và hiển thị loading, tránh dùng kết quả cũ sau khi ngày/import/config thay đổi.
Kết quả kiểm tra 3 ngày được cache theo ngày hiện tại, danh sách slot alarm, metadata import và ngưỡng cấu hình. Không đổi dữ liệu thì dùng lại kết quả.
Import lại dữ liệu 3 ngày, thay đổi ngưỡng hoặc đổi ngày hiện tại sẽ làm tính lại ở lần tải tiếp theo. Dữ liệu không có metadata import được kiểm tra lại để tránh tin vào cache không xác định.
Giữ cache thống kê theo ngày và timer 10 phút khi tab đang hiển thị. Khi đang tích checkbox, quay lại tab sau khi qua ngày mới sẽ kiểm tra lại cửa sổ 3 ngày.
Fail comment hiện có vẫn lấy từ alarm đã lưu, không ghi đè bằng kết quả kiểm tra tạm.
Chỉ lọc giao diện Machine Slot Yield. Không tạo/xóa/sửa alarm trong database, không thay điều kiện tính alarm khi import, không thay bộ lọc Daily hoặc cách tính export. Export Summary tiếp tục lấy các dòng đang hiển thị.
Kiểm tra đã thực hiện
Đủ/thiếu chuỗi cùng/khác Scrapcode; tách model; loại TEST_COUNT khác 0 ở quy tắc liên tiếp.
Yield 15/30, thiếu 15 test, 7/8 test PASS gần nhất, phục hồi xuyên model và chuỗi xuyên ngày trong phạm vi 3 ngày.
Slot có alarm cũ nhưng không đủ điều kiện mới bị loại; slot đủ điều kiện nhưng chưa là alarm trong From–To không được thêm.
Loại test ngày thứ tư; không lấy lịch sử ngoài phạm vi để bù chuỗi; kiểm tra cửa sổ khi qua ngày mới.
Cache được dùng lại, thay đổi config/import làm tính lại.
GUI Qt offscreen: loading khi tích, đúng danh sách, nền đỏ, bỏ tích khôi phục danh sách cũ.
So sánh bộ tính alarm một ngày trước/sau sửa trên 100 bộ dữ liệu ngẫu nhiên: kết quả giống nhau. Kiểm tra cú pháp source.
Chưa chạy trên database sản xuất hoặc máy Windows thực tế.
File source thay đổi
repositories/machine_slot_summary_repository.py
services/alarm_builder.py
ui/widgets/machine_slot_summary.py


LI v1.16 — Tự phục hồi giao diện khi database đang cập nhật
Áp dụng trên source LI_App_v1.16-master(1).zip được gửi ngày 01/10/2026.
Gói này chỉ chứa các file thêm/sửa cho yêu cầu chờ database của giao diện.
Hành vi mới
Mở app lúc database bị khóa
Giao diện vẫn hiển thị. Nếu không đọc được database/bộ lọc do SQLITE_BUSY hoặc SQLITE_LOCKED, hiển thị đúng thông báo:
Database đang cập nhật, vui lòng thử lại sau 2 phút
Dialog có nút Đóng và nút X. Đóng dialog không đóng app, không hủy tác vụ chờ.
Tạm vô hiệu hóa bộ lọc, Search và các điều khiển liên quan khi đang chờ để không thay đổi yêu cầu.
Tự thử lại cùng tác vụ ở worker nền sau mỗi 5 giây; mỗi thao tác SQLite của luồng đọc GUI chờ khóa tối đa 1 giây. Đây là thời gian chờ khóa, không phải giới hạn tổng thời gian truy vấn.
Khi database đọc được, tự hoàn tất khởi tạo và tải bộ lọc. Dialog còn mở sẽ tự đóng; người dùng không cần bấm Import PRIME hay mở lại app.
Search khi app đã mở
Giữ điều kiện của yêu cầu Search trong worker hiện tại, không tạo nhiều worker chồng nhau.
Khi truy vấn gặp khóa, đóng loading chặn giao diện và chuyển sang dialog thông báo có thể đóng.
Kết quả đã hiển thị ở các bảng chính/Tra cứu SLOT được giữ trong lúc chờ; kết quả cũ không phải kết quả của bộ lọc mới. Tiêu đề Summary/Yield Slot/Alarm đổi khi nhận được kết quả mới.
Sau khi database đọc được, tự chạy lại truy vấn với tham số đã giữ, hiển thị kết quả và khôi phục các điều khiển.
Không bật lại dialog sau mỗi lần thử. Người dùng đã đóng dialog thì app tiếp tục chờ âm thầm trong đợt đó.
Áp dụng cho Summary, Yield Slot, Alarm/Dashboard, Machine Slot Yield và các worker đọc Report. Đọc cấu hình Machine Slot Yield lần đầu gặp khóa cũng chuyển sang worker nền.
Nếu import chỉ đang đọc log/staging và database vẫn đọc được, giao diện hoạt động bình thường. Không chặn Search chỉ vì có bản ghi import_lock hoặc tiến trình auto import.
“2 phút” chỉ là lời nhắc; không đợi cố định 2 phút và không dừng thử lại ở phút thứ 2.
Đóng app và lỗi khác
Đóng app sẽ hủy vòng chờ và đợi worker dọn kết nối an toàn. Không dùng terminate để cưỡng ép thread.
Chỉ thử lại lỗi SQLite BUSY/LOCKED. Lỗi schema, đường dẫn, SQL hoặc lỗi khác vẫn đi theo luồng báo lỗi hiện có.
Không tự thử lại thao tác lưu Alarm hay thao tác import.
Cài đặt
Đóng các cửa sổ LI đang chạy trước khi thay source. Chọn lúc không có tiến trình dùng source đang cập nhật.
Giải nén gói patch. Chép các thư mục `controllers`, `database`, `ui`, `workers`, `tests` cùng `read.md`, `changelog.txt` vào thư mục gốc project v1.16, giữ đúng đường dẫn và ghi đè các file trùng tên.
Không xóa các file khác của project. Gói này không phải toàn bộ project.
Chạy `main.py` như trước. Nếu dùng EXE, build lại ứng dụng LI từ source đã cập nhật theo cấu hình build hiện tại.
Không cần thay schema, tạo database mới, tạo bản đọc riêng hoặc cài thêm thư viện.
Các file thêm/sửa
File	Thay đổi
`database/read_wait.py` (mới)	Nhận diện đúng lỗi SQLite BUSY/LOCKED và ngữ cảnh timeout riêng cho GUI.
`database/connection.py`	Áp dụng timeout ngắn chỉ khi kết nối được mở trong tác vụ đọc GUI; ngoài ngữ cảnh này giữ nguyên timeout.
`workers/database_read_task.py` (mới)	Thử lại tác vụ đọc, chờ 5 giây có thể hủy, chỉ phát finished một lần.
`ui/database_wait.py` (mới)	Quản lý một dialog có thể đóng, khóa/khôi phục điều khiển và hủy chờ khi đóng app.
`controllers/prime_controller.py`	Gắn cơ chế chờ vào khởi tạo/bộ lọc/Search, giữ kết quả khi bận và dọn worker khi đóng.
`workers/database_init_worker.py`	Khởi tạo lại tự động khi gặp khóa.
`workers/filter_option_worker.py`	Tải lại bộ lọc tự động khi gặp khóa.
`workers/summary_worker.py`	Search Summary tự phục hồi.
`workers/slot_summary_worker.py`	Search Yield Slot tự phục hồi.
`workers/alarm_worker.py`	Đọc Alarm/lịch sử tự phục hồi; lưu Alarm không tự thử lại.
`workers/report_worker.py`	Đọc lựa chọn/kết quả/chi tiết Report tự phục hồi và kết thúc được khi hủy chờ.
`workers/slot_report_worker.py`	Worker đọc dữ liệu báo cáo Slot tự phục hồi.
`workers/machine_slot_config_worker.py` (mới)	Đọc cấu hình Machine Slot Yield ở nền khi database bận.
`ui/widgets/machine_slot_summary.py`	Truy vấn Machine Slot Yield tự phục hồi; bỏ loading chặn giao diện khi chờ.
`ui/pages/machine_slot_yield_page.py`	Chuyển đọc cấu hình đang bận sang worker; không thay logic Save Target.
`ui/pages/report_page.py`	Gắn dialog chờ và giữ bảng tra cứu cũ khi Search chưa thành công.
`ui/widgets/slot_report_builder.py`	Gắn worker Report với dialog chờ và xử lý hủy khi đóng.
`ui/report_detail_dialog.py`	Đồng bộ kết thúc/hủy chờ với ReportWorker và đóng cửa sổ an toàn.
`tests/test_database_wait_recovery.py` (mới)	Kiểm thử khóa SQLite thật, tự phục hồi GUI và hủy chờ.
Phạm vi được giữ nguyên
Không thay các service/repository import PRIME/CUM, parser log, staging, transaction ghi, khóa import, lịch auto import, quy tắc Alarm, Monitor, TIER, công thức thống kê hoặc schema database.
Không tối ưu tốc độ đọc log, không đổi journal_mode=DELETE. Timeout mặc định của kết nối import vẫn 60 giây; timeout riêng của thao tác lưu Alarm vẫn như trước.
Kiểm thử
15 kiểm thử mới cho yêu cầu này: mở app khi khóa (giữ/đóng dialog), khóa lúc tải bộ lọc, Summary/Yield Slot/Alarm/Report/Machine Slot Yield tự phục hồi, mở Report rồi đóng app khi đang khóa, đóng app an toàn, import đang staging vẫn đọc được, lỗi không phải khóa không bị retry, thao tác ghi không bị retry, timeout import không đổi.
11 kiểm thử startup hiện có đã chạy đạt.
Chạy đối chiếu 45 kiểm thử hiện có trên bản gốc và bản sửa: cùng 32 đạt, 6 failure và 7 error ở cùng các test. Các lỗi có sẵn liên quan fixture log/ngày, kỳ vọng UI cũ, chờ bộ lọc nền và quy tắc báo cáo cũ được giữ nguyên phạm vi; không sửa để làm xanh các test không liên quan.
Kiểm tra bằng SQLite thật và Qt offscreen trên Linux. Chưa chạy EXE trên Windows hoặc đường dẫn SMB thực tế của nhà máy; cần kiểm tra vận hành trên môi trường đó.
Chạy lại các kiểm thử mới từ gốc project:
```bash
python -m unittest discover -s tests -p "test_database_wait_recovery.py" -v
```
Kiểm tra tại máy sử dụng
Trong lúc auto import đang ghi, mở LI: giao diện xuất hiện và hiện thông báo nếu database chặn đọc. Giữ nguyên dialog, đợi import xong: dialog tự đóng và bộ lọc được tải.
Lặp lại nhưng đóng dialog bằng nút Đóng/X: bộ lọc vẫn tự tải khi database sẵn sàng.
Với app đã mở, chọn bộ lọc và Search lúc đang ghi: Search/bộ lọc bị vô hiệu hóa tạm thời. Đợi nhả khóa: kết quả tự tải đúng điều kiện, điều khiển bật lại.
Lặp lại bước 3 với dialog đã đóng; không cần bấm Search lần nữa.
Trong giai đoạn chỉ đọc log/staging, kiểm tra Search vẫn dùng được nếu database chưa khóa đọc.