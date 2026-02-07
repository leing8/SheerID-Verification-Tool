# 🤖 Google One (Gemini) Verification Tool

Python tool for Google One AI Premium student discount via SheerID.

---

## 📋 Requirements

- Python 3.8+
- `curl_cffi` - TLS 指纹伪装（必需，用于绕过反欺诈检测）
- `Pillow` - 图像生成
- `numpy` - 人类行为模拟

---

## 🚀 Quick Start

### 1. Clone Repository

```bash
git clone https://github.com/ThanhNguyxn/SheerID-Verification-Tool.git
```

### 2. Go to Tool Directory

```bash
cd SheerID-Verification-Tool/one-verify-tool
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

> ⚠️ **高通过率模式**: 所有依赖均为必需，缺少任何依赖将导致程序报错退出。

### 4. Run Tool

```bash
python main.py "https://services.sheerid.com/verify/xxx?verificationId=abc123"
```

**With proxy (recommended to avoid fraud detection):**
```bash
python main.py "URL" --proxy 123.45.67.89:8080
python main.py "URL" --proxy http://user:pass@proxy.example.com:8080
```

---

## 🛡️ Avoiding Fraud Detection (`fraudRulesReject`)

If you encounter `fraudRulesReject` error, try:

| Solution | Description |
|----------|-------------|
| **Residential Proxy** | Use `--proxy` flag with residential IP (not datacenter) |
| **Wait Between Attempts** | 5-10 minutes between verifications |
| **Different University** | Tool uses weighted selection for higher success |
| **Fresh Verification Link** | Get a new link if previous one failed |

## ⚙️ How It Works

```
1. Parse verificationId
2. Check link state
3. Generate student identity
4. Generate student ID card
5. Submit → collectStudentPersonalInfo
6. Skip SSO → DELETE /step/sso
7. Upload document → S3
8. Complete → completeDocUpload
```

---

## 🎁 Benefits After Verification

Once verified, you get:

| Benefit | Description |
|---------|-------------|
| **Gemini Advanced** | Most powerful AI model |
| **2TB Google Drive** | Cloud storage |
| **NotebookLM Pro** | AI-powered notes |
| **AI Video Credits** | Veo video generation |

---

## 🧠 Intelligent Strategy: University Student

Optimized for Google One (Gemini Advanced) verification:

### 1. Weighted University Selection
-   **Database**: 45+ Universities (Global).
-   **Smart Weighting**: Selects high-success institutions.

### 2. The "Waterfall" Flow
1.  **Submission**: Submits PII.
2.  **SSO Bypass**: Skips school portal login (`DELETE /step/sso`).
3.  **Document Gen**: Creates realistic Student ID cards.
4.  **Completion**: Finalizes upload via `completeDocUpload`.

### 3. Success Factors
-   **Age Targeting**: 18-24 demographic.
-   **Clean Images**: Optimized for OCR.

---

## 🔐 统一设备档案 (DeviceProfile)

### 为什么需要统一设备档案？

SheerID 等反欺诈系统会检测**指纹属性之间的逻辑矛盾**。如果各指纹组件独立生成，可能出现：

| 矛盾情况 | 检测风险 |
|----------|----------|
| GPU 声称是 RTX 4090，但 WebGL max_texture_size 只有 8192 | 🚨 高 |
| 操作系统是 Windows，但字体列表包含 macOS 专有字体 | 🚨 高 |
| 声称 16 核 CPU，但 deviceMemory 只有 4GB | ⚠️ 中 |
| 时区是美国东部，但语言是 zh-CN | ⚠️ 中 |

### DeviceProfile 如何解决？

`DeviceProfile` 作为统一的设备配置中心，确保所有指纹组件使用**同一套逻辑一致的设备参数**：

```
┌─────────────────────────────────────────────────────────────┐
│                    DeviceProfile (统一档案)                   │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐            │
│  │ os_type     │ │ gpu         │ │ cpu_cores   │            │
│  │ platform    │ │ renderer    │ │ device_memory│           │
│  │ screen_w/h  │ │ max_texture │ │ timezone    │            │
│  └──────┬──────┘ └──────┬──────┘ └──────┬──────┘            │
└─────────┼───────────────┼───────────────┼───────────────────┘
          │               │               │
          ▼               ▼               ▼
    ┌──────────┐   ┌──────────┐   ┌──────────┐
    │ Canvas   │   │ WebGL    │   │Navigator │
    │ 指纹      │   │ 指纹      │   │ 指纹      │
    └──────────┘   └──────────┘   └──────────┘
          │               │               │
          └───────────────┼───────────────┘
                          ▼
                  🔐 一致的 deviceFingerprintHash
```

### 关键特性

| 特性 | 说明 |
|------|------|
| **GPU 参数精确匹配** | RTX 4090 对应 max_texture_size=32768，Intel UHD 对应 16384 |
| **操作系统一致性** | Windows 使用 Windows 字体，macOS 使用 macOS 字体 |
| **美国地区优化** | 自动选择美国时区 (EST/CST/MST/PST) 和英语语言 |
| **确定性生成** | 使用 verificationId 作为种子，同一会话中配置保持一致 |

