# DUO MIND - Báo Cáo Mô Tả Sản Phẩm MVP

## 1. Mục đích tài liệu

Tài liệu này mô tả logic sản phẩm DUO MIND ở trạng thái MVP hiện tại trong codebase, phục vụ cho:

- báo cáo mô tả sản phẩm,
- giải thích cấu trúc hệ thống với hội đồng,
- làm nền cho hồ sơ dự thi và thuyết trình.

## 2. Tuyên bố giá trị sản phẩm

DUO MIND là nền tảng học tập AI cá nhân hóa giúp người học:

- hiểu rõ mình đang học để làm gì,
- học một chủ đề theo cấu trúc dễ hiểu,
- kiểm tra lại nội dung mình đang hiểu có chính xác không,
- xác định kỹ năng và bước tiếp theo phù hợp với mục tiêu nghề nghiệp.

## 3. Nhóm người dùng mục tiêu

### 3.1. Người dùng chính

- sinh viên đại học,
- người mới tự học để chuyển hướng nghề nghiệp,
- người học cần hệ thống vừa giải thích kiến thức vừa định hướng năng lực.

### 3.2. Bối cảnh sử dụng

- tự học ngoài giờ lên lớp,
- ôn tập kiến thức,
- rà soát note hoặc tài liệu tự học,
- xác định hướng phát triển nghề nghiệp,
- xây dựng kế hoạch học ngắn hạn.

## 4. Luồng sản phẩm tổng thể

DUO MIND vận hành theo một logic vòng lặp:

1. người dùng tạo hồ sơ học tập,
2. hệ thống hiểu bối cảnh và mục tiêu,
3. người dùng học bằng Explore hoặc kiểm chứng bằng Analyze,
4. người dùng nhận quiz, mind map và báo cáo,
5. mentor và roadmap dùng lại dữ liệu đó để gợi ý bước tiếp theo,
6. lịch sử học được lưu để tăng chất lượng phản hồi về sau.

Luồng này giúp sản phẩm không bị rơi vào tình trạng "mỗi phiên hỏi là một phiên rời rạc".

## 5. Các module hiện có trong MVP

## 5.1. Onboarding

Mục đích:

- thu thập tín hiệu ban đầu về người học,
- làm nền cho cá nhân hóa toàn bộ trải nghiệm.

Dữ liệu chính:

- trạng thái học tập/làm việc,
- ngành học hoặc lĩnh vực,
- vai trò mục tiêu,
- trọng tâm hiện tại,
- khó khăn,
- đầu ra mong muốn,
- ràng buộc,
- thời lượng học.

Giá trị:

- giúp hệ thống tránh phản hồi chung chung,
- tạo nền tảng cho mentor và roadmap.

## 5.2. Profile

Mục đích:

- cho phép người dùng xem lại và chỉnh sửa bối cảnh học tập.

Giá trị:

- cá nhân hóa không phải dữ liệu tĩnh,
- người dùng có quyền điều chỉnh định hướng theo thời gian.

## 5.3. Dashboard

Mục đích:

- làm trung tâm điều phối trải nghiệm.

Thông tin hiển thị:

- hướng tập trung hiện tại,
- hành động nên làm ngay,
- bối cảnh hiện tại,
- độ đầy hồ sơ,
- quick actions sang Mentor, Explore, Analyze, Roadmap, History.

Giá trị:

- giảm ma sát điều hướng,
- biến sản phẩm thành một hệ thống có định hướng, không chỉ là danh sách tính năng.

## 5.4. Mentor AI

Mục đích:

- đưa ra phản hồi định hướng mang tính hành động.

Khả năng hiện tại:

- gợi ý vai trò phù hợp,
- chỉ ra skill gaps,
- đề xuất bước học tiếp theo,
- hiển thị tín hiệu thị trường và nguồn tham khảo,
- lưu bộ nhớ mentor để dùng lại ngữ cảnh.

Giá trị:

- gắn việc học với mục tiêu nghề nghiệp,
- tăng cảm giác "được dẫn đường" thay vì chỉ "được trả lời".

## 5.5. Roadmap

Mục đích:

- gom dữ liệu từ hồ sơ, analytics và session history để tạo lộ trình hành động.

Khả năng hiện tại:

- hiển thị mức sẵn sàng,
- xác định khoảng trống kỹ năng,
- gợi ý trọng tâm 14 ngày,
- kết nối ngược sang Explore và Mentor.

Giá trị:

- chuyển dữ liệu học tập thành quyết định hành động.

## 5.6. Explore

Mục đích:

- giúp người dùng học một chủ đề mới theo cấu trúc có tính sư phạm.

Đầu ra hiện tại:

- tổng quan chủ đề,
- lý thuyết cốt lõi,
- chi tiết kiến thức,
- nguồn xác minh,
- mind map,
- quiz,
- tải file Word.

Logic AI:

- xây dựng content blueprint,
- tách section theo vai trò riêng,
- giảm trùng ý giữa các khối nội dung,
- ưu tiên nội dung có giá trị học thật.

Giá trị:

- giúp người học không chỉ biết "định nghĩa", mà còn hiểu cơ chế, ví dụ, ứng dụng và ngộ nhận.

## 5.7. Analyze

Mục đích:

- giúp người dùng kiểm tra nội dung đang học hoặc tự ghi chép.

Đầu ra hiện tại:

- phần trăm/mức độ chính xác,
- điểm cần đính chính,
- kiến thức đúng cần nắm,
- nguồn tham khảo,
- mind map,
- quiz.

Logic AI:

- phân tích nội dung đầu vào,
- so sánh với nguồn và rule hậu kiểm,
- tái cấu trúc lại phần kiến thức đúng,
- tránh để người học chỉ nhận một phản hồi chung chung.

Giá trị:

- hỗ trợ "học đúng", không chỉ "học nhiều".

## 5.8. Quiz

Mục đích:

- chuyển nội dung vừa học thành bài ôn tập ngay trong cùng phiên.

Khả năng hiện tại:

- câu hỏi trắc nghiệm,
- câu hỏi mở,
- gợi ý lập luận,
- điểm số và phản hồi.

Giá trị:

- tăng khả năng ghi nhớ,
- giúp người học tự kiểm tra sau khi tiếp nhận kiến thức.

## 5.9. Mind Map

Mục đích:

- trực quan hóa cấu trúc kiến thức.

Khả năng hiện tại:

- dựng mind map trực tiếp từ kết quả AI,
- hiển thị trong Explore và Analyze.

Giá trị:

- hỗ trợ người học nhìn được toàn cảnh,
- phù hợp với người học thiên về trực quan.

## 5.10. History và Knowledge Report

Mục đích:

- lưu tiến trình học tập và tổng hợp tiến bộ.

Khả năng hiện tại:

- xem lại session,
- lọc theo loại phiên,
- mở báo cáo AI,
- tổng hợp nhịp học, độ sâu và khuyến nghị tiếp theo.

Giá trị:

- tạo chiều sâu dài hạn cho sản phẩm,
- giúp người học thấy được hành trình thay vì chỉ các tương tác đơn lẻ.

## 6. Công nghệ sản phẩm

### 6.1. Frontend

- Next.js 14
- TypeScript
- Tailwind CSS
- shadcn/ui
- Framer Motion
- React Flow
- Zustand
- TanStack Query

### 6.2. Backend

- FastAPI
- Pydantic
- async API architecture

### 6.3. Database và xác thực

- Supabase PostgreSQL
- Supabase Auth

### 6.4. AI

- Gemini API
- pipeline prompt nhiều lớp
- planning trước khi sinh nội dung
- hậu kiểm chất lượng nội dung

## 7. Điểm mạnh sản phẩm ở trạng thái MVP

### 7.1. Tính hệ thống

DUO MIND đã có đủ các mắt xích quan trọng của một hành trình học tập:

- hồ sơ,
- định hướng,
- học,
- kiểm chứng,
- ôn tập,
- báo cáo.

### 7.2. Tính cá nhân hóa

Sản phẩm không trả lời theo kiểu một-mẫu-cho-tất-cả, mà bám:

- mục tiêu nghề nghiệp,
- ràng buộc học tập,
- khó khăn hiện tại,
- dữ liệu lịch sử,
- bộ nhớ mentor.

### 7.3. Tính sư phạm

Các đầu ra AI được tổ chức thành:

- tổng quan,
- ý cốt lõi,
- giải thích chi tiết,
- ví dụ,
- ứng dụng,
- ngộ nhận,
- ôn tập.

Điều này phù hợp hơn với giáo dục so với mô hình chatbot thuần túy.

## 8. Giới hạn của MVP hiện tại

Để giữ đúng phạm vi trung thực với code hiện tại, cần lưu ý:

- MVP chủ yếu tập trung vào trải nghiệm cá nhân hóa cho từng người học,
- chưa phải nền tảng quản trị đầy đủ cho giảng viên hoặc nhà trường,
- chưa trình bày mô hình doanh thu hoàn chỉnh trong sản phẩm,
- cần thêm dữ liệu người dùng thực để đo sâu hơn về hiệu quả học tập.

Việc nêu rõ giới hạn này giúp dự án có tính học thuật và tính khả thi cao hơn khi bảo vệ trước hội đồng.

## 9. Tiềm năng phát triển sau MVP

Sau giai đoạn MVP, sản phẩm có thể mở rộng theo các hướng:

- dashboard cho giảng viên,
- theo dõi nhóm học,
- gợi ý học liệu theo chương trình đào tạo,
- phân tích năng lực theo chuẩn đầu ra,
- license cho trường học hoặc trung tâm đào tạo.

## 10. Kết luận

DUO MIND ở trạng thái MVP hiện tại đã hình thành được một logic sản phẩm rõ ràng:

- bắt đầu từ dữ liệu người học,
- tạo ra nội dung học có cấu trúc,
- kiểm chứng kiến thức,
- hỗ trợ hành động tiếp theo,
- và tích lũy tiến bộ lâu dài.

Điểm mạnh quan trọng nhất của DUO MIND là không xem AI như một công cụ trả lời tức thời, mà xem AI như một động cơ tổ chức lại hành trình học tập cho người dùng.
