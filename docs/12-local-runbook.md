# DUO MIND - Local Runbook

## 1. Muc tieu

File nay ghi lai cach chay local o trang thai hien tai de tranh lap lai tinh trang:
- frontend len process nhung tra `500`
- `next dev` fail voi loi `spawn EPERM`
- app build duoc nhung local runtime bi vo do `.next` stale

## 2. Trang thai hien tai

### Frontend
- Tech: `Next.js 14`
- Port mac dinh: `3001`
- Script hien tai:
  - `npm run dev` -> `next start -p 3001`
  - `npm run dev:rebuild` -> `clean .next -> next build -> next start -p 3001`

### Backend
- Tech: `FastAPI`
- Port mac dinh: `8000`
- Health check: `GET /health`

## 3. Cach chay

### Cach nhanh nhat
Tu root project, co the dung script co san:

```bash
scripts\start-duomind-local.cmd
```

Neu chi can frontend:

```bash
scripts\start-frontend.cmd
```

Neu vua sua code va can build lai frontend:

```bash
scripts\start-frontend-rebuild.cmd
```

Neu can backend rieng:

```bash
scripts\start-backend.cmd
```

### Frontend
Chay:

```bash
npm run dev
```

Y nghia:
- Dung lai ban build gan nhat, on dinh hon cho demo
- Phu hop khi code da build pass va can mo app nhanh

Neu vua co thay doi code va can rebuild lai ban local:

```bash
npm run dev:rebuild
```

Neu muon thu lai hot-reload:

```bash
npm run dev:hot
```

Luu y:
- Script nay co the fail lai voi `spawn EPERM`
- Chi dung khi da xac minh moi truong co the fork process binh thuong

### Backend
Backend hien tai van dung `http://localhost:8000`

Kiem tra nhanh:

```bash
curl http://localhost:8000/health
```

Ky vong:

```json
{"status":"healthy","app":"DUO MIND API"}
```

## 4. Cach kiem tra frontend da len dung

Kiem tra:

```bash
curl -I http://localhost:3001
```

Ky vong:
- Tra ve `HTTP/1.1 200 OK`

Neu tra ve `500` va stack co dang:
- `Cannot find module './xxx.js'`
- `Require stack: .next/server/...`

thi kha nang cao la `.next` dang stale.

## 5. Nguyen nhan da gap

Frontend local da tung bi:
- `next dev` fail voi `spawn EPERM`
- process cu van giu cong `3001`
- process do doc `.next` dang stale va tra `500`

Huong xu ly da chot:
- khong dua vao `next dev` lam duong chay chinh nua
- dung `next start` de chay ban build on dinh
- chi rebuild khi thuc su can

## 6. Checklist khi bao "web khong chay"

1. Check backend:
   - `curl http://localhost:8000/health`
2. Check frontend:
   - `curl -I http://localhost:3001`
3. Neu frontend `500`:
   - nghi ngay toi `.next` stale hoac process cu
4. Neu frontend khong len:
   - neu da co build moi: chay lai `npm run dev`
   - neu vua sua code: chay `npm run dev:rebuild`
5. Neu khong muon mo tung terminal thu cong:
   - chay `scripts\start-duomind-local.cmd`

## 7. Ghi chu

Runbook nay uu tien:
- on dinh de demo
- de test nhanh
- phu hop voi boi canh con it thoi gian

Neu sau cuoc demo can quay lai che do phat trien day du, co the toi uu tiep theo huong:
- tim cach bat `next dev` chay on dinh tren may nay
- tach script `demo` va `dev` ro hon
