# prac-profile-board

FastAPI와 jQuery를 활용한 프로필 관리 사이트입니다.

사용자는 회원가입 및 로그인을 통해 프로필 정보를 관리할 수 있으며, 프로필 이미지 업로드 기능을 제공합니다.

## 프로젝트 개요

개인별 프로필 정보와 이미지를 등록하고 관리할 수 있는 웹 서비스입니다.

### 주요 기능

* 회원가입
* 로그인 (JWT 인증)
* 내 정보 조회
* 사용자 목록 조회
* 사용자 상세 조회
* 사용자 정보 수정
* 사용자 삭제
* 프로필 이미지 업로드
* 프로필 이미지 조회

---

## 기술 스택

### Frontend

* HTML5
* CSS3
* JavaScript
* jQuery
* Ajax

### Backend

* FastAPI
* SQLite
* aiosqlite
* bcrypt
* JWT
* aiofiles

---

## 프로젝트 구조

```text
prac-profile-board
│
├── frontend
│   ├── css
│   │   └── style.css
│   ├── js
│   │   ├── api.js
│   │   ├── auth.js
│   │   ├── users.js
│   │   └── detail.js
│   ├── login.html
│   ├── register.html
│   ├── index.html
│   └── detail.html
│
├── backend
│
└── README.md
```

---

## 화면 구성

### 로그인

* 이메일 로그인
* JWT 토큰 발급

### 회원가입

* 사용자 등록
* 이메일 중복 검사

### 사용자 목록

* 전체 사용자 조회
* 프로필 이미지 표시

### 사용자 상세

* 사용자 정보 조회
* 사용자 정보 수정
* 사용자 삭제
* 프로필 이미지 업로드

---

## API

### 인증

| Method | URL       | Description |
| ------ | --------- | ----------- |
| POST   | /register | 회원가입        |
| POST   | /login    | 로그인         |

### 사용자

| Method | URL         | Description |
| ------ | ----------- | ----------- |
| GET    | /me         | 내 정보 조회     |
| GET    | /users      | 사용자 목록 조회   |
| GET    | /users/{id} | 사용자 상세 조회   |
| PUT    | /users/{id} | 사용자 정보 수정   |
| DELETE | /users/{id} | 사용자 삭제      |

### 프로필 이미지

| Method | URL                       | Description |
| ------ | ------------------------- | ----------- |
| POST   | /users/{id}/profile-image | 이미지 업로드     |
| GET    | /users/{id}/profile-image | 이미지 정보 조회   |

---

## 실행 방법

### Frontend

Live Server 또는 정적 웹 서버 실행

```bash
frontend 폴더 실행
```

### Backend

```bash
pip install -r requirements.txt

uvicorn profile_backend:app --reload --host 0.0.0.0 --port 8000
```

---

## 팀 구성

### Frontend

* UI 구현
* Ajax API 연동
* 사용자 화면 개발

### Backend

* FastAPI API 개발
* JWT 인증 구현
* SQLite 데이터 관리
* 이미지 업로드 처리

---

## 개발 목적

* FastAPI 기반 REST API 학습
* JWT 인증 방식 이해
* SQLite 비동기 처리 경험
* 프론트엔드와 백엔드 협업 경험
* GitHub 브랜치 기반 협업 경험

---

## Branch Strategy

```text
main
├── fe
└── be
```

* fe : Frontend 개발 브랜치
* be : Backend 개발 브랜치
* main : 최종 통합 브랜치

```
```
