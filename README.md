# StarResonanceFishing - 釣魚自動化

基於 Python 的 スタレゾ（Star Resonance）釣魚自動化工具

## ⚠️ 開發狀態

目前還在早期開發階段

參數與檢測圖片都相當隨意，單純為了能夠在最短的時間內做出可運作的最小實現。

### 系統需求
- Python 3.14 或更高版本
- Windows 作業系統（使用 Windows API）
- 螢幕解析度：1920x1080（16:9）
  - 工具在 1920x1080 解析度下開發
  - 其他 16:9 解析度未經測試，可能需要調整配置
  - 非 16:9 的解析度可能無法正常運作

## 📂 專案結構

```
StarResonanceFishing/
├── scripts/                         # 各種腳本
│   ├── check.py                     # 代碼檢查腳本（使用 Ruff）
│   └── pack.py                      # 打包腳本（PyInstaller）
├── src/                             # 源代碼目錄
│   ├── __init__.py                  # 模組初始化
│   ├── fishing_bot.py               # 釣魚機器人主邏輯
│   ├── config_manager.py            # 配置管理
│   ├── logger.py                    # 日誌模組
│   ├── window_manager.py            # 視窗管理
│   ├── input_controller.py          # 輸入控制（PyAutoGUI）
│   ├── input_controller_winapi.py   # 輸入控制（Windows API）
│   ├── image_detector.py            # 圖像檢測
│   ├── utils.py                     # 工具函數
│   └── phases/                      # 釣魚階段模組
│       ├── preparation_phase.py     # 準備階段
│       ├── casting_phase.py         # 拋竿階段
│       ├── waiting_phase.py         # 等待咬鉤階段
│       ├── tension_phase.py         # 拉力階段
│       └── completion_phase.py      # 完成階段
├── templates/                       # 存放模板圖片（用於圖像識別）
│   ├── bite_indicator.png           # 咬鉤指示器
│   ├── red_tension.png              # 紅色張力指示
│   ├── retry_button.png             # 重試按鈕
│   ├── rod_depleted.png             # 魚竿耐久耗盡
│   └── tension_bar.png              # 拉力計
├── config.yaml                      # 配置檔案
├── pyproject.toml                   # 專案設定檔
├── requirements.txt                 # 生產環境相依套件
├── requirements-dev.txt             # 開發環境相依套件
├── main.py                          # 主程式入口
├── debug_detection_area.py          # 測試檢測區域的調試工具
├── get_window_title.py              # 獲取視窗標題的工具
└── README.md                        # 說明檔案
```

## 🚀 安裝步驟

### 1. 前置要求
- 確保已安裝 Python 3.14 或更高版本
- Windows 作業系統

### 2. 克隆或下載專案
```bash
git clone https://github.com/walnut-almonds/StarResonanceFishing.git
cd StarResonanceFishing
```

### 3. 安裝相依套件

#### 開發環境（包含開發工具）
```bash
pip install -r requirements-dev.txt
```

#### 生產環境（僅運行所需）
```bash
pip install -r requirements.txt
```

### 4. 配置遊戲視窗標題
運行以下工具來獲取遊戲視窗的正確標題：
```bash
python get_window_title.py
```
然後將獲得的視窗標題填入 [config.yaml](config.yaml) 的 `game.window_title` 欄位。

## ⚙️ 配置說明

在運行程式前，請根據實際遊戲情況修改 [config.yaml](config.yaml) 檔案：

## 📖 使用方法

### 基本運行

1. 確保遊戲已經啟動並處於可釣魚狀態
2. 確認 [config.yaml](config.yaml) 中的配置正確
3. 運行主程式：

```bash
python main.py
```

4. 程式會自動尋找遊戲視窗並開始釣魚循環
5. 按 `Ctrl+C` 可以隨時中斷程式

### 調試工具

#### 查看遊戲視窗標題
```bash
python get_window_title.py
```
列出所有開啟的視窗標題，用於配置 `game.window_title`。

#### 調試檢測區域
```bash
python debug_detection_area.py
```
視覺化顯示圖像檢測區域，用於調整 `config.yaml` 中的 `detection.region` 配置。

### 開發工具

#### 代碼檢查
```bash
python scripts/check.py
```
使用 Ruff 進行代碼格式檢查和 linting。

#### 打包成執行檔
```bash
python scripts/pack.py
```
使用 PyInstaller 將專案打包成獨立執行檔。

## 🎣 運作流程

1. **準備階段** - 尋找並聚焦遊戲視窗
2. **拋竿階段** - 執行拋竿操作（按鍵或點擊）
3. **等待階段** - 等待魚咬鉤（圖像識別咬鉤指示器）
4. **拉力階段** - 追蹤魚的位置並控制張力
   - 根據魚的位置左右移動
   - 根據張力計調整收竿力度
5. **完成階段** - 處理釣魚結果，準備下一輪

## ⚠️ 注意事項

- 確保遊戲在前景執行並且視窗未被遮擋
- 建議在 1920x1080 解析度下使用
- 首次使用請先用 `debug_detection_area.py` 確認檢測區域是否正確
- 模板圖片需要根據實際遊戲畫面自行截取
- 使用前請確認遊戲的使用條款是否允許使用自動化工具

## 🐛 常見問題

### 找不到遊戲視窗
- 使用 `python get_window_title.py` 查看正確的視窗標題
- 檢查 `config.yaml` 中的 `game.window_title` 是否正確

### 無法識別咬鉤或拉力計
- 使用 `python debug_detection_area.py` 檢查檢測區域
- 調整 `config.yaml` 中的 `detection.region` 和 `detection.threshold`
- 重新截取 `templates/` 目錄下的模板圖片

### 魚追蹤不準確
- 調整 `fishing.fish_tracking` 中的參數
- 特別是 `center_offset`、`center_threshold_min` 和 `center_threshold_max`

## 📝 License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

## 🤝 貢獻

歡迎提交 Issue 和 Pull Request！

## ⚖️ 免責聲明

本工具僅供學習和研究使用。使用本工具可能違反遊戲的服務條款，請自行承擔使用風險。作者不對因使用本工具而導致的任何後果負責。
