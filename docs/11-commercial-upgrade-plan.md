# DUO MIND - 3 Day Commercial Upgrade Plan

## 1. Muc tieu tai dinh vi san pham

### Dinh vi moi
`DUO MIND = AI mentor va learning planner giup sinh vien va nguoi di lam tre xac dinh skill gap, chon muc tieu nghe nghiep, hoc theo lo trinh ro rang va theo doi tien do.`

### Ly do phai thu hep
- San pham hien tai co nhieu tinh nang tot, nhung dang qua rong: explore chung, analyze chung, mentor, history, quiz.
- Neu tiep tuc theo huong "AI hoc moi thu", rat kho thuyet phuc nguoi dung tra tien.
- Huong co gia tri thuong mai ro nhat hien nay la: `career learning companion`.

### Muc tieu 3 ngay
- Chot lai truc gia tri xoay quanh `muc tieu nghe nghiep`.
- Them lop du lieu `target_role` xuyen suot onboarding -> profile -> dashboard -> mentor.
- Bien dashboard thanh noi dieu phoi hoc tap, khong chi la trang link tinh nang.
- Tao 1 ke hoach trien khai co the demo, test va pitch duoc ngay.

## 2. Boi canh ky thuat hien tai

### Frontend
- `Next.js 14 App Router`
- `TypeScript`
- `Tailwind CSS`
- `shadcn/ui`
- `Framer Motion`
- `@tanstack/react-query`
- `Zustand`

### Backend
- `FastAPI`
- `Pydantic`
- `Supabase Python client`
- `Gemini`
- `httpx`

### Database
- `Supabase Postgres`
- Cac bang chinh da co:
  - `profiles`
  - `user_onboarding`
  - `learning_sessions`
  - `quiz_questions`
  - `quiz_attempts`
  - `open_question_responses`
  - `knowledge_analytics`
  - `mentor_threads`
  - `mentor_messages`
  - `mentor_memory`
  - `job_market_signals`

## 3. Danh gia san pham hien tai

### Gia tri dang co
- Onboarding 4 buoc da tao du lieu ca nhan hoa tot.
- Mentor AI da co context tu profile, lich su hoc va memory.
- Analyze va Explore da tao duoc vong lap hoc tap co output ro.
- History, quiz va report da giup giu session va ket qua hoc tap.

### Van de can xu ly ngay
- Chua co bien trung tam de goi la san pham nghe nghiep hoc tap.
- Chua co "next best action" ro rang cho nguoi dung sau onboarding.
- Dashboard dang la trang tong hop chuc nang, chua la bo dieu huong gia tri.
- Mentor dang manh ve tra loi, nhung chua bam mot muc tieu nghe nghiep xuyen suot.

## 4. Keep / Add / De-emphasize

### Keep
- `Onboarding AI`
- `Mentor AI`
- `Analyze`
- `Quiz`
- `History`
- `AI persona`

### Add ngay trong dot 3 ngay
- `target_role`: muc tieu nghe nghiep chinh
- `career_direction_summary`: thong diep ngan de dashboard bam vao
- `next_best_action`: thong diep hanh dong tiep theo tren dashboard
- `mentor suggested questions` moi dua tren target role
- `dashboard hero` moi bam muc tieu thay vi noi chung chung

### De-emphasize trong giao dien va pitch
- `Explore` theo kieu hoc moi chu de bat ky
- `Mind map` nhu diem ban hang chinh
- `Export Word/Markdown` nhu feature noi bat

### De roadmap, khong lam trong 3 ngay
- `Skill Gap Map` day du
- `Learning Roadmap` day du theo milestone
- `JD Analyzer`
- `CV Analyzer`
- `Weekly Coach Report`
- `Institution dashboard`

## 5. Pham vi thuc thi 3 ngay

## P0 - Bat buoc xong
- Them truong `target_role` vao `user_onboarding`
- Cap nhat type frontend va model backend
- Sua onboarding step 3 de thu duoc `target_role`
- Sua profile editor de cho phep cap nhat `target_role`
- Sua dashboard hero + learning path de dua tren `target_role`
- Sua mentor suggestion va mentor context de dung `target_role`
- Tao migration SQL ro rang

## P1 - Nen xong neu con thoi gian
- Them block `Huong muc tieu` tren dashboard
- Them `next step` text ro rang dua tren target role + daily_study_minutes
- Lam moi wording cua onboarding va profile de khop dinh vi thuong mai
- Tao route `roadmap` toi gian de gom skill gap, tien do va lo trinh 14 ngay

## P2 - Khong lam trong dot nay
- Skill gap page rieng o muc do sau hon
- Dashboard analytics moi
- Billing / pricing UI

## 6. Chi tiet tung phan can nang cap

### 6.1 Database
Can bo sung vao `user_onboarding`:
- `target_role TEXT`

Yeu cau:
- Chap nhan `NULL` de an toan voi user cu
- Co script migration rieng de deploy nhanh
- Cap nhat `supabase/schema.sql` de source of truth khong bi lech

### 6.2 Backend
Can sua:
- `backend/app/models/user.py`
- `backend/app/routers/onboarding.py`
- `backend/app/services/mentor_service.py`
- `backend/app/utils/helpers.py`

Can dat duoc:
- `OnboardingData` nhan duoc `target_role`
- Prompt onboarding doc duoc `target_role`
- Fallback onboarding co mo ta persona bam muc tieu nghe nghiep
- Mentor suggestion uu tien cau hoi theo `target_role`
- Mentor track / context digest nhin thay `target_role`

### 6.3 Frontend
Can sua:
- `frontend/types/index.ts`
- `frontend/components/onboarding/options.ts`
- `frontend/components/onboarding/steps/Step3Goals.tsx`
- `frontend/components/onboarding/OnboardingWizard.tsx`
- `frontend/components/profile/ProfileEditor.tsx`
- `frontend/app/(app)/dashboard/page.tsx`

Can dat duoc:
- Step 3 thu duoc `target_role`
- Payload gui len API khong lech schema
- Profile cho sua `target_role`
- Dashboard hien duoc muc tieu nghe nghiep va hanh dong tiep theo

## 7. Trinh tu trien khai de tranh vo flow

### Buoc 1
Sua schema va migration truoc.

### Buoc 2
Sua type/model chung:
- `frontend/types/index.ts`
- `backend/app/models/user.py`

### Buoc 3
Sua onboarding flow:
- options
- step 3
- validation
- submit payload

### Buoc 4
Sua profile editor:
- initial state
- form field
- validation
- build payload

### Buoc 5
Sua dashboard:
- hero copy
- learning path
- next action

### Buoc 6
Sua mentor:
- suggested questions
- context digest
- role detection logic

### Buoc 7
Smoke test end-to-end:
- onboarding moi
- sua profile
- vao dashboard
- mo mentor

## 8. Ke hoach 3 ngay

## Day 1 - Data model + onboarding + profile

### Muc tieu
Lam xong duong du lieu `target_role` tu database toi UI.

### Cong viec
1. Tao migration SQL them `target_role`.
2. Cap nhat `supabase/schema.sql`.
3. Cap nhat `OnboardingData` backend va frontend.
4. Them `TARGET_ROLE_OPTIONS`.
5. Sua `Step3Goals` de co section `Muc tieu nghe nghiep`.
6. Cap nhat validation va payload onboarding.
7. Sua `ProfileEditor` de xem/sua `target_role`.

### Acceptance criteria
- User moi co the chon `target_role` trong onboarding.
- Sau khi submit, Supabase luu duoc `target_role`.
- Vao profile thay duoc va sua duoc `target_role`.

## Day 2 - Dashboard + mentor

### Muc tieu
Lam ro gia tri thuong mai tren giao dien sau onboarding.

### Cong viec
1. Sua dashboard hero de goi ten muc tieu nghe nghiep.
2. Tao helper tao `next best action`.
3. Sua `buildMentorLearningPath` dua tren `target_role`.
4. Sua mentor suggested questions bam muc tieu nghe nghiep.
5. Dua `target_role` vao profile digest va role detection.

### Acceptance criteria
- Dashboard khong con noi chung chung.
- Mentor de xuat cau hoi lien quan den role muc tieu.
- Role muc tieu anh huong duoc output learning path.
- Co them duong dan ro rang tu dashboard, sidebar va mentor sang roadmap.

## Day 3 - polish + test + demo readiness

### Muc tieu
Dong goi thay doi de co the demo, pitch va ban tiep.

### Cong viec
1. Soat lai wording tren onboarding, profile, dashboard.
2. Soat lai route `roadmap` de gom `skill gap + 14 day flow + mentor prompts`.
3. Smoke test full flow.
4. Fix loi typing / validation / rendering.
5. Chot checklist demo.
6. Cap nhat tai lieu neu can.

### Acceptance criteria
- Flow end-to-end chay on dinh.
- UI wording dong nhat voi dinh vi moi.
- Co the demo onboarding -> dashboard -> roadmap -> mentor trong 2-3 phut.

## 9. Test plan

### 9.1 Database test
- Chay migration them `target_role`.
- Kiem tra user cu khong loi vi truong moi la nullable.
- Kiem tra record moi co luu `target_role`.

### 9.2 API test
- `POST /api/onboarding/submit` voi `target_role`
- `GET /api/onboarding/me` tra ve `target_role`
- `GET /api/mentor/suggested-questions` thay doi theo `target_role`
- `POST /api/mentor/chat` van chay voi onboarding moi

### 9.3 Frontend manual test
- Dang nhap user moi -> onboarding -> dashboard
- Chon role trong onboarding, submit thanh cong
- Vao profile thay role da luu
- Sua role trong profile, refresh thay du lieu moi
- Vao dashboard thay hero va next action doi theo role
- Vao mentor thay question goi y doi theo role

### 9.4 Regression check
- Analyze van hoat dong
- Explore van hoat dong
- History van doc session cu
- Khong vo typing o cac component dang dung `OnboardingData`

## 10. Danh sach file du kien sua

### Database
- `supabase/schema.sql`
- `supabase/2026-03-20-add-target-role.sql` or equivalent migration file

### Backend
- `backend/app/models/user.py`
- `backend/app/routers/onboarding.py`
- `backend/app/services/mentor_service.py`
- `backend/app/utils/helpers.py`

### Frontend
- `frontend/types/index.ts`
- `frontend/components/onboarding/options.ts`
- `frontend/components/onboarding/steps/Step3Goals.tsx`
- `frontend/components/onboarding/OnboardingWizard.tsx`
- `frontend/components/profile/ProfileEditor.tsx`
- `frontend/app/(app)/dashboard/page.tsx`

## 11. Muc tieu demo sau nang cap

Pitch flow nen di theo:
1. User chon `target_role` khi onboarding.
2. Dashboard hien ngay san pham dang dan nguoi dung den role nao.
3. Mentor de xuat cau hoi, skill gap va huong hoc bam muc tieu do.
4. Analyze va Explore tro thanh cong cu hoc trong mot hanh trinh co muc tieu.

## 12. Nhung viec khong duoc lam trong 3 ngay

- Khong mo rong them qua nhieu feature moi.
- Khong tách them nhieu page neu chua can.
- Khong doi kien truc.
- Khong viet lai onboarding hoac mentor tu dau.

## 13. Ket luan thuc thi

Neu chi co 3 ngay, huong nang cap dung la:
- `khong build them qua nhieu`
- `lam ro gia tri bang target_role`
- `day target_role xuyen suot toan bo flow`
- `bien dashboard va mentor thanh bang chung thuong mai hoa`

Sau dot nay, DUO MIND se chuyen tu:
- `AI hoc tap co nhieu tinh nang`

thanh:
- `AI mentor va learning planner co muc tieu nghe nghiep ro rang`
