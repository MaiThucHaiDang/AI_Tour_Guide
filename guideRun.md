# GUIDE RUN
## tạo file .venv trước khi chạy các cái sau
pip thư viện trong requirement.txt của part4 và src
npm install // để chạy frontend được

1. tạo file .env ở cấu trúc bên ngoài với form như sau:
LLM_PROVIDER_ORDER= gemini,groq
GEMINI_API_KEY= 
GROQ_API_KEY= 
SQL_SERVER = localhost
SQL_DATABASE = AI_Tour_Guide
SQL_DRIVER = ODBC Driver 18 for SQL Server
SQL_TRUSTED_CONNECTION = true
SQL_ENCRYPT = yes
SQL_TRUST_SERVER_CERT = yes
ENVIRONMENT=development
LOG_LEVEL=INFO
# If SQL_TRUSTED_CONNECTION is false, set SQL_USERNAME and SQL_PASSWORD.

// tách thành 3 terminal
2. chạy backend của model hình ảnh
cd src/backend
python -m uvicorn main:app --reload --port 8000
3. chạy backend của model âm thanh
cd part4/backend
python -m uvicorn main:app --reload --port 8001
4. chạy frontend của app
npm run dev
