# DUO MIND - Hồ Sơ Dự Thi Khởi Nghiệp

## 1. Thông tin khái quát dự án

- Tên sản phẩm: **DUO MIND**
- Loại hình: Nền tảng hỗ trợ học tập cá nhân hóa ứng dụng AI
- Trạng thái: **MVP web app đang hiện thực trong codebase**
- Đối tượng chính:
  - sinh viên đại học,
  - người tự học định hướng nghề nghiệp,
  - người cần hệ thống học và kiểm chứng kiến thức thay vì chỉ hỏi đáp đơn lẻ.

## 2. Bối cảnh và vấn đề thực tiễn

### 2.1. Bối cảnh

Trong môi trường học tập hiện nay, người học tiếp cận lượng lớn nội dung từ nhiều kênh khác nhau: tài liệu số, video, bài viết, khóa học online và các công cụ AI. Tuy nhiên, phần lớn người học vẫn gặp khó khăn trong việc:

- xác định đâu là nội dung cốt lõi,
- hiểu đúng bản chất của kiến thức,
- biết mình đang thiếu gì so với mục tiêu nghề nghiệp,
- lựa chọn bước học tiếp theo một cách có hệ thống.

### 2.2. Vấn đề cốt lõi

Qua quan sát hành vi học tập hiện đại, có thể tóm tắt vấn đề bằng ba điểm:

1. **Người học bị quá tải thông tin nhưng thiếu định hướng.**
2. **Công cụ AI hiện tại trả lời nhanh nhưng chưa đủ tính sư phạm và chưa gắn với hồ sơ người học.**
3. **Quá trình học bị rời rạc giữa khám phá kiến thức, kiểm chứng nội dung, ôn tập và định hướng nghề nghiệp.**

Điều này dẫn tới hệ quả:

- học lan man,
- dễ tin vào nội dung chưa được kiểm chứng,
- khó chuyển kiến thức thành năng lực,
- khó duy trì động lực học dài hạn.

## 3. Giải pháp của DUO MIND

DUO MIND là nền tảng AI hỗ trợ người học theo một vòng khép kín:

1. hiểu người học,
2. hỗ trợ học kiến thức,
3. kiểm chứng kiến thức,
4. định hướng bước tiếp theo,
5. lưu lại tiến trình học.

## 4. Cấu trúc sản phẩm MVP hiện tại

### 4.1. Onboarding và hồ sơ học tập

Hệ thống thu thập và quản lý các tín hiệu quan trọng của người học:

- vai trò mục tiêu,
- trọng tâm hiện tại,
- khó khăn hiện tại,
- đầu ra mong muốn,
- ràng buộc học tập,
- thời lượng học mỗi ngày,
- mối quan tâm học tập.

Người dùng có thể vào trang hồ sơ để xem và điều chỉnh lại các thông tin này.

### 4.2. Dashboard tổng quan

Dashboard đóng vai trò trung tâm điều phối, hiển thị:

- hướng tập trung hiện tại,
- hành động nên làm ngay,
- mức độ sẵn sàng của hồ sơ,
- bối cảnh học tập,
- gợi ý điều hướng sang Mentor, Explore, Analyze và Roadmap.

### 4.3. Mentor AI

Mentor AI hỗ trợ:

- xác định kỹ năng còn thiếu,
- gợi ý vai trò nghề nghiệp phù hợp,
- đề xuất bước học tiếp theo,
- đưa ra các câu hỏi tiếp theo để đào sâu,
- lưu bộ nhớ mentor nhằm duy trì ngữ cảnh giữa nhiều phiên.

### 4.4. Roadmap

Roadmap tổng hợp dữ liệu hồ sơ, lịch sử học và analytics để:

- xác định khoảng trống kỹ năng,
- ưu tiên chủ đề cần học,
- gợi ý hướng hành động trong ngắn hạn,
- neo việc học vào mục tiêu nghề nghiệp cụ thể.

### 4.5. Explore

Explore phục vụ nhu cầu tìm hiểu một chủ đề mới. Đầu ra hiện tại của MVP gồm:

- tổng quan chủ đề,
- tóm tắt lý thuyết cốt lõi,
- phân tích chi tiết kiến thức,
- nguồn tham khảo,
- mind map,
- quiz ôn tập,
- xuất kết quả ra file Word.

### 4.6. Analyze

Analyze phục vụ nhu cầu kiểm tra lại nội dung người dùng đang học hoặc tự ghi chép. Chức năng hiện tại gồm:

- đánh giá độ chính xác,
- chỉ ra điểm cần đính chính,
- trình bày lại kiến thức đúng cần nắm,
- mind map,
- quiz ôn tập,
- nguồn tham khảo xác minh.

### 4.7. History và Báo cáo AI

Mỗi phiên học được lưu lại trong lịch sử. Từ dữ liệu đó, hệ thống có thể:

- lọc theo loại phiên,
- xem lại nội dung đã học,
- xóa hoặc quản lý phiên,
- sinh báo cáo AI về nhịp học, độ sâu kiến thức và gợi ý bước tiếp theo.

## 5. Công nghệ áp dụng

### 5.1. Kiến trúc hệ thống

- Frontend: Next.js 14, TypeScript, Tailwind CSS, shadcn/ui
- Backend: FastAPI
- Database và xác thực: Supabase PostgreSQL + Supabase Auth
- AI: Gemini API
- Mind map: React Flow
- Quản lý trạng thái và data fetching: Zustand, TanStack Query

### 5.2. Công nghệ AI trong sản phẩm

AI được áp dụng theo nhiều lớp:

- sinh và tái cấu trúc nội dung học,
- xây dựng content blueprint trước khi viết nội dung,
- phân tích đúng/sai của kiến thức,
- tạo quiz ôn tập,
- sinh mind map,
- tạo báo cáo AI từ lịch sử học,
- cá nhân hóa tư vấn nhờ dữ liệu hồ sơ và bộ nhớ mentor.

Điểm đáng chú ý là AI trong DUO MIND không chỉ "trả lời", mà được đặt trong một pipeline có:

- prompt theo vai trò rõ ràng,
- content planning,
- source-aware output,
- validation để giảm nội dung chung chung hoặc trùng ý.

## 6. Giá trị của sản phẩm

### 6.1. Giá trị đối với người học

- học đúng trọng tâm thay vì học lan man,
- hiểu sâu hơn nhờ cấu trúc kiến thức rõ ràng,
- kiểm tra lại được nội dung mình đang học,
- có hướng đi tiếp theo gắn với nghề nghiệp,
- tích lũy lịch sử học và báo cáo tiến bộ.

### 6.2. Giá trị đối với nhà trường và giáo dục

- tăng năng lực tự học của sinh viên,
- hỗ trợ cá nhân hóa học tập,
- tăng liên kết giữa học thuật và định hướng nghề nghiệp,
- tạo tiền đề cho mô hình trợ lý học tập số trong môi trường đào tạo.

### 6.3. Giá trị đối với thị trường

DUO MIND có tiềm năng phát triển theo hướng:

- công cụ học tập cá nhân hóa cho người học cá nhân,
- nền tảng đồng hành học tập cho trung tâm đào tạo,
- giải pháp EdTech hỗ trợ sinh viên trong trường đại học.

## 7. Tính mới và sáng tạo của ý tưởng

Tính mới của DUO MIND nằm ở việc kết hợp nhiều lớp giá trị trong cùng một sản phẩm:

- cá nhân hóa dựa trên hồ sơ học tập,
- học một chủ đề theo cấu trúc sư phạm,
- kiểm chứng độ chính xác của nội dung,
- định hướng nghề nghiệp bằng mentor AI,
- duy trì trí nhớ học tập qua lịch sử và mentor memory.

Khác với chatbot học tập thông thường, DUO MIND được thiết kế như một **vòng lặp học tập thông minh**:

**Hồ sơ -> Khám phá -> Phân tích -> Ôn tập -> Báo cáo -> Điều chỉnh hướng đi**

Đây là điểm khác biệt quan trọng về mặt ý tưởng và thiết kế sản phẩm.

## 8. Tính khả thi

### 8.1. Khả thi về kỹ thuật

MVP đã được xây dựng trên stack hiện đại, phổ biến và dễ mở rộng.

Các thành phần chính đều đã có trong code:

- giao diện người dùng,
- hệ thống auth,
- backend API,
- data model,
- AI integration,
- history,
- memory,
- report.

### 8.2. Khả thi về vận hành

Sản phẩm có thể triển khai theo mô hình web app, dễ tiếp cận, dễ demo và dễ mở rộng theo nhóm người dùng.

### 8.3. Khả thi về phát triển kinh doanh

Trong giai đoạn sau MVP, có thể phát triển theo các hướng:

- gói cá nhân cho người học,
- gói cho trung tâm đào tạo,
- gói trường học hoặc khoa đào tạo,
- tích hợp học liệu và dashboard quản trị.

## 9. Tính phù hợp với nhu cầu thị trường và ngành giáo dục

DUO MIND phù hợp với:

- xu hướng AI trong giáo dục,
- nhu cầu cá nhân hóa học tập,
- nhu cầu tự học có định hướng,
- nhu cầu gắn học tập với kỹ năng nghề nghiệp.

Đặc biệt với sinh viên, sản phẩm giải quyết một khoảng trống rất rõ:

- không chỉ học "để biết",
- mà học để hiểu đúng, học đúng và đi đúng hướng.

## 10. Hình thức thể hiện và lợi thế khi trình bày

DUO MIND có lợi thế lớn khi mang đi dự thi vì có thể minh họa trực tiếp bằng demo:

- từ onboarding đến dashboard,
- từ mentor đến roadmap,
- từ explore đến analyze,
- từ history đến AI report.

Điều này giúp hội đồng không chỉ nghe mô tả ý tưởng, mà còn nhìn thấy luồng sử dụng thật và tính logic của toàn bộ hệ thống.

## 11. Kết luận

DUO MIND là một sản phẩm EdTech AI có định hướng rõ ràng, giải quyết một vấn đề thực của người học hiện đại: học quá nhiều nhưng thiếu định hướng, thiếu kiểm chứng và thiếu liên kết với mục tiêu nghề nghiệp.

Trong trạng thái MVP hiện tại, sản phẩm đã có đủ cấu trúc để chứng minh:

- ý tưởng có tính mới,
- giải pháp có tính logic,
- công nghệ có tính khả thi,
- và giá trị ứng dụng có thể phát triển rộng hơn trong giáo dục.

DUO MIND không chỉ là công cụ hỏi đáp AI, mà là nền tảng đồng hành học tập thông minh, cá nhân hóa và có khả năng mở rộng trong bối cảnh giáo dục số.
