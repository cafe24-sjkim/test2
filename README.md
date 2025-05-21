# FastAPI 게시판 API

## 프로젝트 소개
이 프로젝트는 FastAPI를 사용하여 간단한 게시판 API를 구현합니다. SQLite 데이터베이스를 사용하여 게시글 및 사용자 데이터를 저장하며, 사용자 인증 (JWT) 및 게시글 CRUD (생성, 읽기, 수정, 삭제) 기능을 제공합니다.

## 설치 방법
1. 저장소를 복제합니다:
   ```bash
   git clone <repository_url>
   ```
2. 프로젝트 디렉토리로 이동합니다:
   ```bash
   cd <project_directory>
   ```
3. 필요한 라이브러리를 설치합니다:
   ```bash
   pip install -r requirements.txt
   ```
   (`requirements.txt` 파일에는 `fastapi`, `uvicorn`, `sqlalchemy`, `pydantic`, `python-jose[cryptography]`, `passlib[bcrypt]` 등 실행에 필요한 모든 라이브러리가 포함되어 있습니다.)

## 실행 방법
1. FastAPI 애플리케이션을 실행합니다:
   ```bash
   uvicorn main:app --reload
   ```
   애플리케이션 실행 전에 `database/setup.py`를 실행하여 데이터베이스와 테이블이 생성되었는지 확인할 수 있습니다 (main.py에서도 자동으로 호출됩니다).
   ```bash
   python database/setup.py 
   ```
2. 브라우저 또는 API 클라이언트를 사용하여 다음 URL에 접속합니다:
   - 기본 접속 URL: `http://127.0.0.1:8000`
   - API 자동 문서 (Swagger UI): `http://127.0.0.1:8000/docs`
   - 대체 API 문서 (ReDoc): `http://127.0.0.1:8000/redoc`

## API 엔드포인트 설명

### 사용자 및 인증

#### 사용자 회원가입
- **엔드포인트**: `POST /users/signup`
- **설명**: 새로운 사용자를 시스템에 등록합니다.
- **요청 본문 예시** (`application/json`):
  ```json
  {
    "username": "newuser",
    "password": "securepassword123"
  }
  ```
- **성공 응답 (201 Created)**:
  ```json
  {
    "id": 1,
    "username": "newuser",
    "is_active": true
  }
  ```
- **실패 응답 (400 Bad Request)**: 사용자 이름이 이미 존재할 경우.

#### 로그인 (토큰 발급)
- **엔드포인트**: `POST /token`
- **설명**: 사용자 이름과 비밀번호를 제공하여 JWT 액세스 토큰을 발급받습니다.
- **요청 본문 형식**: `application/x-www-form-urlencoded`
  - `username`: (사용자 이름)
  - `password`: (비밀번호)
- **성공 응답 (200 OK)**:
  ```json
  {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer"
  }
  ```
- **실패 응답 (401 Unauthorized)**: 사용자 이름 또는 비밀번호가 잘못된 경우.

### 게시글 (Posts)
**참고**: **모든 게시글 관련 API (생성, 전체 조회, 특정 조회, 수정, 삭제)는 이제 인증이 필요합니다.** API 요청 시 `Authorization` 헤더에 `Bearer <발급받은_토큰>` 형태로 토큰을 포함해야 합니다.

#### 게시글 생성
- **엔드포인트**: `POST /posts`
- **인증**: 필요 (Bearer 토큰)
- **설명**: 새로운 게시글을 생성합니다.
- **요청 본문 예시** (`application/json`):
  ```json
  {
    "title": "새 게시글 제목",
    "content": "게시글 내용입니다."
  }
  ```
- **성공 응답 (201 Created)**:
  ```json
  {
    "id": 1,
    "title": "새 게시글 제목",
    "content": "게시글 내용입니다."
  }
  ```

#### 전체 게시글 목록 조회
- **엔드포인트**: `GET /posts`
- **인증**: 필요 (Bearer 토큰)
- **설명**: 모든 게시글 목록을 조회합니다. (인증된 사용자만 접근 가능)
- **성공 응답 (200 OK)**:
  ```json
  [
    {"id": 1, "title": "첫 번째 게시글", "content": "내용1"},
    {"id": 2, "title": "두 번째 게시글", "content": "내용2"}
  ]
  ```

#### 특정 게시글 조회
- **엔드포인트**: `GET /posts/{post_id}`
- **인증**: 필요 (Bearer 토큰)
- **설명**: 지정된 ID의 게시글을 조회합니다. (인증된 사용자만 접근 가능)
- **성공 응답 (200 OK)**:
  ```json
  {
    "id": 1,
    "title": "첫 번째 게시글",
    "content": "내용1"
  }
  ```
- **실패 응답 (404 Not Found)**: 해당 ID의 게시글을 찾을 수 없을 때 반환됩니다.

#### 게시글 수정
- **엔드포인트**: `PUT /posts/{post_id}`
- **인증**: 필요 (Bearer 토큰)
- **설명**: 지정된 ID의 게시글을 수정합니다.
- **요청 본문 예시** (`application/json`):
  ```json
  {
    "title": "수정된 제목",
    "content": "수정된 내용입니다."
  }
  ```
- **성공 응답 (200 OK)**:
  ```json
  {
    "id": 1,
    "title": "수정된 제목",
    "content": "수정된 내용입니다."
  }
  ```
- **실패 응답 (404 Not Found)**: 해당 ID의 게시글을 찾을 수 없을 때 반환됩니다.

#### 게시글 삭제
- **엔드포인트**: `DELETE /posts/{post_id}`
- **인증**: 필요 (Bearer 토큰)
- **설명**: 지정된 ID의 게시글을 삭제합니다.
- **성공 응답 (204 No Content)**: 게시글이 성공적으로 삭제되면 내용 없이 반환됩니다.
- **실패 응답 (404 Not Found)**: 해당 ID의 게시글을 찾을 수 없을 때 반환됩니다.

## API 테스트 방법
FastAPI의 자동 문서 (`http://127.0.0.1:8000/docs`)를 사용하면 API를 쉽게 테스트할 수 있습니다.
1. `/users/signup`을 통해 사용자를 생성합니다.
2. `/token` 엔드포인트에서 생성한 사용자의 정보로 로그인하여 `access_token`을 발급받습니다. (Swagger UI 우측 상단의 "Authorize" 버튼을 클릭하고, 발급받은 토큰을 `Bearer <token>` 형식으로 입력)
3. 인증이 필요한 API (예: `POST /posts`)를 테스트할 때, Swagger UI는 자동으로 `Authorization` 헤더에 토큰을 포함하여 요청합니다.

**`curl` 사용 예시:**
1. 사용자 생성:
   ```bash
   curl -X POST "http://127.0.0.1:8000/users/signup" \
        -H "Content-Type: application/json" \
        -d '{"username": "testuser", "password": "testpassword"}'
   ```
2. 로그인 및 토큰 발급 (jq가 설치되어 있다면 토큰만 추출 가능):
   ```bash
   ACCESS_TOKEN=$(curl -X POST "http://127.0.0.1:8000/token" \
                       -H "Content-Type: application/x-www-form-urlencoded" \
                       -d "username=testuser&password=testpassword" | jq -r .access_token)
   echo $ACCESS_TOKEN 
   ```
3. 토큰을 사용하여 게시글 생성:
   ```bash
   curl -X POST "http://127.0.0.1:8000/posts" \
        -H "Authorization: Bearer $ACCESS_TOKEN" \
        -H "Content-Type: application/json" \
        -d '{"title": "인증된 게시글", "content": "토큰으로 작성된 내용입니다."}'
   ```
