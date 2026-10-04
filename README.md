# ServerEye

لوحة مراقبة عربية لخوادم Linux وWindows Server. وكيل خفيف يرسل قراءات المعالج والذاكرة والقرص وزمن الاستجابة، واللوحة تنبّه عند تجاوز العتبات أو عند انحراف إحصائي، وتصدر تقريراً يومياً أو أسبوعياً بصيغة PDF.

## 1. ما هو المشروع

ServerEye تطبيق Flask بلوحة عربية. المسؤول يسجّل الدخول، يضيف خادماً، وينسخ مفتاح الوكيل إلى الجهاز المراد مراقبته. الوكيل `agent/servereye_agent.py` يقرأ المقاييس عبر `psutil` ويرسلها إلى `POST /api/metrics`. الخادم يحفظ القراءة، يقارنها بالعتبات، ويشغّل فحص انحراف، ثم يعرض الحالة في لوحة ورسوم.

## 2. لماذا يوجد هذا المشروع

الجداول والأدوار والنصوص تربط المنتج بمراقبة تشغيل الخوادم من داخل مركز عمليات: أدوار `admin` و`soc_analyst` و`it_manager`، تنبيهات بدرجات عربية، وتقارير PDF. الكشف يجمع عتبات ثابتة مع درجة Z ونموذج Isolation Forest من `scikit-learn` بعد اكتمال خط أساس.

## 3. من يستخدمه

| الدور | الاسم العربي في `config.py` | الصلاحيات |
| --- | --- | --- |
| `admin` | مسؤول النظام | لوحة، عرض الخوادم وإدارتها، التنبيهات وحلّها، التقارير، المستخدمون، الإعدادات |
| `soc_analyst` | محلل مركز العمليات الأمنية | لوحة، عرض الخوادم، التنبيهات وحلّها، التقارير |
| `it_manager` | مدير تقنية المعلومات | لوحة، عرض الخوادم، عرض التنبيهات، التقارير |

الوكيل عملية على الخادم المراقب وليست حساباً بشرياً. يصادق بترويسة `X-Agent-Token`.

عند أول إنشاء لقاعدة فارغة يُدرج ثلاثة مستخدمين بهذه الأسماء: `admin` و`soc_analyst` و`it_manager`. كلمات المرور الأولية مكتوبة داخل `database/db.py` وتُخزَّن بعد تجزئة bcrypt. هذا الملف لا يعيد كتابتها.

## 4. ماذا يستطيع النظام أن يفعل

- تسجيل الدخول والخروج مع حد لمحاولات الفشل.
- إضافة خادم باسم ونوع نظام (`Linux` أو `Windows Server`) وعنوان ووصف، وتوليد `agent_token`.
- عرض قائمة الخوادم وصفحة تفاصيل مع آخر القراءات.
- استقبال المقاييس من الوكيل وحفظها.
- إنشاء تنبيه عند تجاوز عتبات CPU أو RAM أو القرص أو زمن الاستجابة.
- فحص خط الأساس: أقل من 50 قراءة خلال 24 ساعة يبقي الخادم في وضع الخط الأساسي.
- بعد الخط الأساسي: درجة Z على نافذة 100 قراءة بحد 3.0، ونموذج Isolation Forest يُدرَّب ويُعاد تدريبه.
- حل التنبيه وتسجيل من حلّه.
- تقارير يومية وأسبوعية وتصدير PDF بخط IBM Plex Sans Arabic.
- إدارة المستخدمين والأدوار من حساب المسؤول.
- تعديل العتبات من صفحة الإعدادات.
- بريد تنبيه حرج عبر SMTP عندما يكون الإشعار مفعّلاً.

## 5. كيف يعمل النظام

```
الوكيل كل interval_seconds
  -> psutil
  -> POST /api/metrics + X-Agent-Token
  -> إدراج metrics وتحديث last_seen_at
  -> عتبات + انحراف
  -> صف في alerts عند اللزوم
  -> لوحة المستخدم تقرأ الخوادم والتنبيهات
```

خيط خلفي كل 60 ثانية يفحص انقطاع الوكلاء، وكل 3600 ثانية يعيد تدريب النماذج.

## 6. أمثلة واقعية

1. المسؤول يفتح `/login` ويدخل بحسابه.
2. من `/servers` يضيف خادماً. النظام يحفظ صفاً ومفتاح وكيل فريداً.
3. على الجهاز المراقب يُنسخ `agent_config.example.json` إلى `agent_config.json` ويوضع عنوان اللوحة والمفتاح.
4. الوكيل يرسل نسب المعالج والذاكرة والقرص وزمن فتح منفذ محلي.
5. إن تجاوزت نسبة المعالج العتبة `cpu_critical` (الافتراضي 90) يُنشأ تنبيه شدته `حرجة`.
6. المحلل يفتح `/alerts` ويعلّم التنبيه محلولاً.
7. من `/reports` يختار فترة `daily` أو `weekly` وينزّل PDF.

## 7. رحلة المستخدم

1. `/` يحوّل غير المسجّل إلى `/login` والمسجّل إلى `/dashboard`.
2. بعد الدخول تُحفظ الجلسة 60 دقيقة.
3. القائمة تعتمد على صلاحيات الدور المحقونة في القالب.
4. اختيار الخوادم أو التنبيهات أو التقارير أو المستخدمين أو الإعدادات.
5. النماذج التي تغيّر البيانات ترسل رمز CSRF.
6. الخروج عبر `/logout`.

الواجهة البرمجية للمقاييس لا تمر بجلسة المستخدم.

## 8. الوحدات والأقسام

| الوحدة | الملفات | ماذا يفعل المستخدم |
| --- | --- | --- |
| الدخول | `routes/auth_routes.py` | دخول وخروج |
| اللوحة | `routes/dashboard_routes.py` و`templates/dashboard.html` و`static/js/dashboard.js` | بطاقات الحالة وتحديث حي `/api/dashboard/live` |
| الخوادم | `routes/server_routes.py` و`models/server_model.py` | إضافة وعرض وحذف وقراءات `/api/servers/<id>/metrics` |
| التنبيهات | `routes/alert_routes.py` و`services/alert_service.py` | عرض وحل وتحديث `/api/alerts/live` |
| التقارير | `routes/report_routes.py` و`services/report_service.py` | عرض وتصدير PDF |
| المستخدمون | `routes/user_routes.py` و`models/user_model.py` | إنشاء وحذف وتعديل الدور |
| الإعدادات | `routes/settings_routes.py` | عتبات الإشعار |
| الوكيل | `agent/servereye_agent.py` | جمع وإرسال |
| الكشف | `services/anomaly_detection.py` | خط أساس وZ وIsolation Forest |
| البريد | `services/email_service.py` | رسالة حرجة |
| الجدولة | `services/scheduler_service.py` | مهلة الوكيل وإعادة التدريب |
| الوقت | `utils/datetime_fmt.py` | عرض `YYYY/M/Dم H:MMص` أو `م` |
| الأمان | `utils/security.py` | CSRF والجلسة وحد الدخول |

## 9. الشركات والكيانات

«غير موجود في الملفات الحالية». الكيان التشغيلي هو صف في جدول `servers`.

## 10. الصلاحيات

الصلاحيات مجموعة نصية في `ROLE_PERMISSIONS` وتُفحص بـ `role_required`. المسؤول وحده يملك `users_manage` و`settings` و`servers_manage`. محلل المركز يحل التنبيهات ولا يدير المستخدمين. مدير التقنية يعرض التنبيهات ولا يحلّها حسب المجموعة `it_manager`.

مفتاح الوكيل يمنح كتابة المقاييس لخادم واحد فقط عبر `ServerModel.get_by_token`.

## 11. الأتمتة ومسارات العمل

| الآلية | السلوك |
| --- | --- |
| وكيل | حلقة إرسال، والفاصل لا يقل عن 10 ثوانٍ في الكود حتى لو كان الإعداد أصغر |
| جدولة | خيط `servereye-scheduler` كل 60 ثانية |
| مهلة الوكيل | `check_agent_timeouts` يعلّم الخادم إن انقطع الإرسال |
| إعادة التدريب | كل ساعة عندما تمضي 3600 ثانية |
| بريد | عند تنبيه حرج وإذا `email_notify_enabled` مفعّل وSMTP مكتمل |

طوابير رسائل خارجية: «غير موجود في الملفات الحالية».

## 12. التكامل بين الوحدات

قراءة جديدة تحدّث `metrics` و`servers.last_seen_at` ثم `process_thresholds` و`evaluate_metric_reading` ثم `process_anomaly_result`. حالة البطاقة في اللوحة تأتي من `derive_server_status`. التقرير يقرأ الخوادم والمقاييس والتنبيهات لنفس الفترة. حذف الخادم يحذف المقاييس والتنبيهات بسبب `ON DELETE CASCADE`.

## 13. المصطلحات

| المصطلح | المعنى هنا |
| --- | --- |
| خط الأساس | أول 50 قراءة أو أول 24 ساعة، العلم `is_in_baseline` |
| درجة Z | انحراف القراءة عن نافذة سابقة بحد 3.0 |
| Isolation Forest | نموذج `scikit-learn` لكل خادم بعد الخط الأساسي |
| عتبة | مفاتيح `settings` مثل `cpu_critical` |
| شدة التنبيه | `منخفضة` أو `متوسطة` أو `حرجة` |
| مفتاح الوكيل | قيمة فريدة في `agent_token` |

## 14. الأسئلة الشائعة

**ما فترات التقرير؟** `daily` و`weekly` فقط. أي قيمة أخرى تُعاد إلى `daily`.

**هل يوجد تقرير شهري؟** «غير موجود في الملفات الحالية».

**أين تُخزَّن النماذج؟** دوال `train_isolation_forest` و`load_isolation_model` داخل `services/anomaly_detection.py`. مجلد نماذج ظاهر في شجرة الملفات غير مجلد `models` الخاص بجداول البيانات: «غير موجود في الملفات الحالية».

**هل الكوكي الآمن مفعّل؟** `SESSION_COOKIE_SECURE` مضبوط على `False` في `app.py`.

## 15. Architecture

```
+----------------+     HTTPS/HTTP      +----------------------+
| servereye_agent| ------------------> | POST /api/metrics    |
| psutil         |   X-Agent-Token     | Flask blueprints     |
+----------------+                     +----------+-----------+
                                                  |
                    +-----------------------------+------------------+
                    v                             v                  v
              SQLite servereye.db          alert_service      anomaly_detection
                    ^
                    |
              متصفح + جلسة + CSRF
              dashboard / servers / alerts / reports / users / settings
```

## 16. Tech Stack

| الطبقة | التقنية |
| --- | --- |
| لغة | Python |
| ويب | Flask 3.0.3 |
| قاعدة | SQLite عبر `sqlite3` |
| كلمات المرور | bcrypt 4.2.0 |
| بيئة | python-dotenv 1.0.1 |
| كشف | scikit-learn 1.5.2 وnumpy 1.26.4 |
| وكيل | psutil 6.0.0 |
| PDF | reportlab 4.2.5 مع arabic-reshaper وpython-bidi |
| واجهة | قوالب Jinja وCSS وJS وChart في `static/js/charts.js` |
| خط | IBM Plex Sans Arabic محلي في `fonts/` و`static/fonts/` |

## 17. Project Structure

```
ServerEye/
  app.py
  config.py
  requirements.txt
  .env.example
  agent/
  database/schema.sql
  database/db.py
  database/servereye.db
  models/
  routes/
  services/
  templates/
  static/
  utils/
  fonts/
```

## 18. Frontend

صفحات متعددة الاتجاه `rtl`. القوالب: `login.html` و`dashboard.html` و`servers.html` و`server_details.html` و`alerts.html` و`reports.html` و`users.html` و`settings.html` و`base.html`.

الشعار `static/images/logo.jpg`. أيقونة تبويب مستقلة: «غير موجود في الملفات الحالية».

البيانات الحية تُطلب من المتصفح إلى `/api/dashboard/live` و`/api/alerts/live` و`/api/servers/<id>/metrics`. الرسوم في `static/js/charts.js`.

## 19. Backend

Blueprints مسجّلة في `create_app`: `auth_bp` و`dashboard_bp` و`server_bp` و`metrics_bp` و`alert_bp` و`report_bp` و`user_bp` و`settings_bp`.

الوصول إلى القاعدة دوال في `models/*` و`database/db.py` باستعلامات بمعاملات `?`. لا طبقة PHP. التشغيل `host=0.0.0.0` والمنفذ 5000 و`use_reloader=False` حتى لا يتضاعف خيط الجدولة.

## 20. Request Flow

استقبال قياس:

```
الوكيل
  -> POST /api/metrics
  -> فحص X-Agent-Token
  -> clamp_percent على النسب
  -> MetricModel.insert
  -> process_thresholds
  -> evaluate_metric_reading
  -> JSON { ok: true }
```

دخول مستخدم:

```
POST /login
  -> حد المحاولات
  -> التحقق من bcrypt
  -> جلسة
  -> تحويل إلى /dashboard
```

## 21. Database

| البند | القيمة |
| --- | --- |
| النوع | SQLite |
| الملف | `database/servereye.db` |
| المخطط | `database/schema.sql` يُنفَّذ عند الإقلاع |
| الاستعلامات | `sqlite3` بمعاملات |
| المفاتيح الأجنبية | `PRAGMA foreign_keys = ON` |

| الجدول | المفاتيح والعلاقات |
| --- | --- |
| `users` | `id`، اسم فريد، `password_hash`، دور ضمن الثلاثة |
| `servers` | `id`، `agent_token` فريد، `os_type` ضمن قيمتين، `is_in_baseline` |
| `metrics` | `server_id` يشير إلى `servers` مع حذف متسلسل، فهرس `(server_id, recorded_at)` |
| `alerts` | `server_id` و`resolved_by` يشيران إلى `users`، الشدة ثلاث قيم عربية |
| `settings` | مفتاح نصي أساسي |

بذور: عتبات `DEFAULT_THRESHOLDS` والمستخدمون الثلاثة إن لم يكونوا موجودين.

## 22. API

| Method | Path | الغرض | المصادقة |
| --- | --- | --- | --- |
| GET | `/` | تحويل | جلسة إن وُجدت |
| GET/POST | `/login` | الدخول | عام |
| GET | `/logout` | الخروج | جلسة |
| GET | `/dashboard` | اللوحة | `dashboard` |
| GET | `/api/dashboard/live` | أرقام حية | `dashboard` |
| GET/POST | `/servers` | قائمة وإضافة | عرض أو إدارة حسب الفعل |
| GET/POST/DELETE | `/servers/<id>` | تفاصيل وتعديل وحذف | حسب الصلاحية |
| GET | `/api/servers/<id>/metrics` | سلسلة قراءات | `servers_view` |
| POST | `/api/metrics` | إدخال قياس | ترويسة `X-Agent-Token` |
| GET/POST | `/alerts` | قائمة | `alerts_view` |
| POST | `/alerts/<id>/resolve` | حل | `alerts_resolve` |
| GET | `/api/alerts/live` | تنبيهات حية | `alerts_view` |
| GET | `/reports` | صفحة التقارير | `reports` |
| GET | `/reports/export` و`/reports/<period>/export` | PDF | `reports` |
| GET/POST/DELETE | `/users` | المستخدمون | `users_manage` |
| GET/POST | `/settings` | العتبات | `settings` |

أجسام الأخطاء للمقاييس رسائل عربية عامة: غير مصرح، بيانات غير صالحة، خطأ داخلي.

## 23. Authentication & Authorization

- الجلسة: `SECRET_KEY` إجباري، العمر 60 دقيقة، الكوكي `HttpOnly` و`SameSite=Lax`.
- كلمة المرور: bcrypt.
- CSRF: `ensure_csrf_token` و`require_csrf` على النماذج.
- حد الدخول: 5 محاولات ثم قفل 300 ثانية لكل معرّف، عبر `check_login_rate_limit`.
- التفويض: `login_required` و`role_required`.
- الوكيل: مفتاح في الترويسة وليس جلسة.

## 24. Security

الموجود: تجزئة كلمات المرور، استعلامات بمعاملات، CSRF، حد محاولات، رؤوس `X-Content-Type-Options` و`X-Frame-Options: SAMEORIGIN` و`Referrer-Policy: no-referrer`، إزالة `X-Powered-By`. رأس `Server` يُضبط إلى النص `ServerEye`.

`SESSION_COOKIE_SECURE` قيمته `False`. صفحة الإعدادات تحفظ العتبات. بيانات SMTP تُقرأ من البيئة. كلمات المرور الأولية موجودة في مصدر `database/db.py` قبل التجزئة.

سجل تدقيق عام منفصل عن حقول `resolved_by`: «غير موجود في الملفات الحالية».

## 25. Configuration

أسماء المتغيرات في `.env.example`:

`SECRET_KEY` و`FLASK_DEBUG` و`SMTP_HOST` و`SMTP_PORT` و`SMTP_USER` و`SMTP_PASSWORD` و`SMTP_FROM` و`SMTP_USE_TLS` و`EMAIL_NOTIFY_ENABLED`.

غياب `SECRET_KEY` يوقف الإقلاع برسالة عربية.

ملف الوكيل `agent/agent_config.json` (يُنسخ من `agent_config.example.json`) مفاتيحه: `server_url` و`agent_token` و`interval_seconds` و`disk_path` و`probe_host` و`probe_port`.

ثوابت في `config.py`: عمر الجلسة، حد الدخول، عتبات الكشف، أدوار.

## 26. Integrations

| الخدمة | الحالة |
| --- | --- |
| SMTP | `send_critical_alert_email` عند اكتمال الإعداد وتفعيل الإشعار |
| بريد آخر أو SMS أو Cloudflare | «غير موجود في الملفات الحالية» |

## 27. Scheduled Jobs

خيط داخلي لا يعتمد cron خارجياً. كل 60 ثانية: مهلة الوكلاء. كل ساعة: `retrain_all_servers`. الوكيل نفسه حلقة نوم على الجهاز المراقب.

## 28. File Storage

قاعدة SQLite هي التخزين. خطوط TTF في `fonts/` و`static/fonts/` مع رخصة `OFL.txt`. مرفوعات مستخدمين: «غير موجود في الملفات الحالية».

## 29. Logging & Monitoring

المسجل `servereye` بمستوى INFO. أخطاء 400 و403 و404 و500 رسائل عربية قصيرة، والتفاصيل في السجل. المراقبة الوظيفية هي المقاييس والتنبيهات نفسها. نظام مراقبة خارجي: «غير موجود في الملفات الحالية».

## 30. Installation

1. Python مع `pip install -r requirements.txt`.
2. نسخ `.env.example` إلى `.env` وتعيين `SECRET_KEY`.
3. `python app.py`.
4. فتح `http://127.0.0.1:5000` وتسجيل الدخول. غيّر كلمات المرور الأولية من شاشة المستخدمين بعد أول دخول.
5. أضف خادماً، انسخ المفتاح، ثبّت `psutil` على الجهاز المراقب، وشغّل `python agent/servereye_agent.py`.

القاعدة تُنشأ تلقائياً من `schema.sql`.

## 31. Development Guide

صفحة جديدة: قالب يرث `base.html` وblueprint في `routes/` وتسجيله في `create_app` مع `role_required`. مسار API جديد يُضاف في blueprint المناسب. تغيير جدول يُعدّل `schema.sql`؛ لا أداة migrations، والجداول تُنشأ بـ `CREATE TABLE IF NOT EXISTS` فلا تُرحَّل الأعمدة القديمة تلقائياً. صلاحية جديدة تُضاف إلى `ROLE_PERMISSIONS`.

## 32. Deployment

التشغيل الموثق في الكود: `app.run(host='0.0.0.0', port=5000)`. ملفات gunicorn أو Docker أو systemd: «غير موجود في الملفات الحالية». الإنتاج يحتاج `FLASK_DEBUG` بقيمة لا تفعّل التصحيح، و`SECRET_KEY` من البيئة. خلف وكيل HTTPS يبقى ضبط `SESSION_COOKIE_SECURE` كما هو في المصدر إلى أن يُغيَّر.

## 33. Backup & Recovery

«غير موجود في الملفات الحالية». الملف العملي للنسخ هو `database/servereye.db`.

## 34. Troubleshooting

| العرض | السبب الظاهر من الكود |
| --- | --- |
| توقف عند الإقلاع عن `SECRET_KEY` | المتغير فارغ |
| الوكيل يخرج فوراً | `agent_config.json` غير موجود أو مفتاح ناقص |
| `psutil` غير مثبت | رسالة عربية ثم خروج |
| المقاييس 401 | المفتاح لا يطابق `agent_token` |
| الخادم يبقى في الخط الأساسي | القراءات أقل من 50 خلال 24 ساعة |
| PDF بلا عربية سليمة | خطوط `fonts/` أو مكتبتي reshaper وbidi |
| البريد لا يخرج | `EMAIL_NOTIFY_ENABLED` أو حقول SMTP فارغة |

## 35. Dependencies

```
Flask==3.0.3
bcrypt==4.2.0
python-dotenv==1.0.1
scikit-learn==1.5.2
psutil==6.0.0
reportlab==4.2.5
numpy==1.26.4
arabic-reshaper==3.0.0
python-bidi==0.6.3
```

## 36. Known Limitations

- فترتا تقرير فقط: يومي وأسبوعي.
- الكوكي غير موسوم `Secure`.
- كلمات مرور أولية ثابتة في المصدر حتى أول تغيير من الواجهة.
- لا ترحيل مخطط؛ التعديل اليدوي على قاعدة موجودة لا يطبقه `CREATE TABLE IF NOT EXISTS`.
- رأس `Server` يكشف اسم المنتج.
- الوكيل يقيس زمن منفذ محلي (الافتراضي 22) وليس زمن تطبيق بعيد بالضرورة.

## 37. Current System State

| الحالة | البنود |
| --- | --- |
| مكتمل في الكود | دخول، خوادم، مقاييس، تنبيهات، تقارير PDF، مستخدمون، إعدادات، وكيل، جدولة |
| موجود محلياً | `database/servereye.db` |
| غير مكتمل | نشر إنتاجي موثّق، تقرير شهري، علامة Secure على الكوكي |
| غير موثق | سياسة الاحتفاظ بالقراءات، جهة التشغيل |

## 38. Architecture Decisions

- SQLite ملف واحد يناسب تشغيلاً محلياً بلا خادم قاعدة منفصل.
- مفتاح وكيل لكل خادم بدل جلسة المستخدم على مسار المقاييس.
- العتبات في جدول `settings` حتى تُغيَّر من الواجهة دون إعادة نشر.
- Isolation Forest يبدأ بعد خط أساس حتى لا تُطلق تنبيهات على تاريخ قصير.
- `use_reloader=False` يمنع خيط جدولة مزدوج أثناء التطوير.

## 39. سجل التغييرات

«غير موجود في الملفات الحالية». لا ملف إصدارات. حقل الإصدار في مشروع Python: «غير موجود في الملفات الحالية».

## System Overview

```
[خادم مراقب + وكيل] --قياس--> [Flask :5000] --SQLite--> [users/servers/metrics/alerts/settings]
                                      |
                    [متصفح: لوحة، خوادم، تنبيهات، تقارير، مستخدمون، إعدادات]
                                      |
                                 [SMTP اختياري]
```

## Quick Reference

| الجزء | التقنية | الموقع | الوظيفة |
| --- | --- | --- | --- |
| تطبيق | Flask | `app.py` | التجميع والرؤوس |
| مخطط | SQL | `database/schema.sql` | الجداول |
| وكيل | psutil | `agent/servereye_agent.py` | الإرسال |
| كشف | scikit-learn | `services/anomaly_detection.py` | الانحراف |
| تنبيهات | Python | `services/alert_service.py` | العتبات والحالة |
| PDF | reportlab | `services/report_service.py` | التقارير |
| واجهة | Jinja/JS | `templates/` و`static/` | اللوحة |

## Quick Start

```
pip install -r requirements.txt
copy .env.example .env
python app.py
```

عيّن `SECRET_KEY` داخل `.env` قبل التشغيل. افتح `http://127.0.0.1:5000`.

## For Non-Technical Users

ServerEye شاشة متابعة للخوادم. بعد تسجيل الدخول ترى حالة كل خادم والتنبيهات، وتستطيع تنزيل تقرير يومي أو أسبوعي. إضافة خادم جديد تتم من صفحة الخوادم، ثم يثبّت فريق التقنية برنامجاً صغيراً على ذلك الخادم ليرسل الأرقام.

الأقسام: لوحة المعلومات، الخوادم، التنبيهات، التقارير، المستخدمون، الإعدادات. ما يظهر في القائمة يعتمد على دور حسابك.

## For Developers

- التقنيات: Flask وSQLite وbcrypt وscikit-learn وreportlab.
- المعمارية: blueprints وخدمات ونماذج دوال ووكيل منفصل.
- القاعدة: خمسة جداول في `schema.sql`.
- واجهة المقاييس: `POST /api/metrics` بمفتاح وكيل.
- أهم الملفات: `app.py` و`config.py` و`database/db.py` و`services/alert_service.py` و`services/anomaly_detection.py`.
- التطوير: صلاحية جديدة في `ROLE_PERMISSIONS`، واستعلامات بمعاملات فقط، والأسرار في `.env`.
