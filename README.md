# Шаблон для проектирования сервисов на базе FastAPI

---

### Deploy:

1. ```pip install python3.12```
2. ```python3.12 -m venv venv```
3. ```source venv/bin/activate```
4. ```pip install --no-deps -r requirements.txt```
5. Если необходимы подписи
6. ```rpm -ivh libs/deploy/cprocsp-pki-cades-64-2.0.14530-1.amd64.rpm```
7. ```cp settings_example.py settings.py```
8. Change settings.py specified by LPU
9. ```python main.py```
