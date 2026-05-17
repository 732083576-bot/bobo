# 四川科瑞德HRV心率变异分析系统接口清单

## 基础信息
- **协议**: HTTP RESTful API
- **数据格式**: JSON (UTF-8)
- **认证方式**: OAuth2.0 (密码式/客户端模式)
- **Base URL**: `http://HRV一体机IP:8080`

---

## 接口清单

### 1. 鉴权Token获取
- **地址**: `/api/public/access-token`
- **请求方式**: GET/POST
- **认证方式**: 无需
- **请求参数**:
  - 密码式: `username`, `password`
  - 客户端模式: `client_id`, `client_secret`
- **返回**: 直接返回token字符串

### 2. 创建/同步患者
- **地址**: `/services/reporting/api/third-party/subscribe/sync-patients`
- **请求方式**: POST
- **请求头**: 
  ```
  Content-Type: application/json
  Authorization: Bearer {token}
  ```
- **必传参数**:
  ```json
  {
    "caseNo": "患者唯一标识(建议身份证号)",
    "姓名": "患者姓名",
    "性别": "性别",
    "出生日期": "出生日期",
    "身高": 身高(cm),
    "体重": 体重(kg),
    "运动等级": 运动等级
  }
  ```
- **逻辑**: 按caseNo校验，重复则更新患者信息

### 3. 获取检测记录列表
- **地址**: `/services/reporting/api/third-party/subscribe/measurement-record-list`
- **请求方式**: POST
- **请求头**: 同上
- **必传参数**: `{"excludeStatuses": ["CANCELED"]}`
- **功能**: 按关键字、状态、时间范围筛选检测记录，默认当天数据降序

### 4. 拉取检测结果参数
- **地址**: `/services/reporting/api/third-party/subscribe/parameters`
- **请求方式**: POST
- **请求头**: 同上
- **必传参数**:
  ```json
  {
    "caseNo": "患者唯一标识",
    "examType": "检查类型(HRV健康评估/自主功能评估等)"
  }
  ```
- **返回**: 心电、自主神经、HRV压力、脉搏波速度等指标数据+报告结论

### 5. 拉取检测报告(字节流)
- **地址**: `/services/reporting/api/third-party/subscribe/report-bytes`
- **请求方式**: POST
- **请求头**: 同上
- **必传参数**:
  ```json
  {
    "caseNo": "患者唯一标识",
    "reportType": "PDF/JPG"
  }
  ```
- **返回**: PDF/JPG文件流(JPG为zip压缩包)

### 6. 拉取检测报告(Base64)
- **地址**: `/services/reporting/api/third-party/subscribe/report-base64`
- **请求方式**: POST
- **请求头**: 同上
- **必传参数**:
  ```json
  {
    "caseNo": "患者唯一标识",
    "reportType": "PDF/JPG",
    "splitReport": false
  }
  ```
- **返回**: Base64编码字符串、文件名

### 7. 删除患者
- **地址**: `/services/reporting/api/third-party/subscribe/delete-patient`
- **请求方式**: POST
- **请求头**: 同上
- **必传参数**: `{"caseNo": "患者唯一标识"}`
- **说明**: 仅能删除无检测记录的同步患者

### 8. 获取患者列表
- **地址**: `/services/reporting/api/third-party/subscribe/patient-list`
- **请求方式**: POST
- **请求头**: 同上

### 9. 获取科室列表
- **地址**: `/services/reporting/api/third-party/subscribe/department-list`
- **请求方式**: POST
- **请求头**: 同上

---

## 错误码
- `400`: 请求参数非法/缺失
- `401`: token无效/过期（未授权）
- `403`: 无接口访问权限
- `500`: HRV服务器内部错误

---

## 使用说明

1. **配置**: 编辑 `config.json`，设置HRV一体机IP、认证信息
2. **HIS数据库**: 确保HIS数据库表结构与查询匹配
3. **运行**: 
   ```bash
   pip install -r requirements.txt
   python middleware.py
   ```
4. **功能**: 自动同步患者到HRV、拉取检测报告并保存到本地
