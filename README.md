# 釣魚自動化

基於 Python 的 スタレゾ 釣魚自動化工具

## 開發方向?

目前還在早期開發階段

參數與檢測圖片都相當隨意，單純為了能夠在最短的時間內做出可運作的最小實現

工具是在 1920x1080 解析度下開發的，沒確認過其他 16:9 環境下是不是能正常運作
非16:9的解析度猜測大概率是有問題不運作的

## 結構

```
StarResonanceFishing/
├── src/
│   ├── __init__.py                  # 模組初始化
│   ├── fishing_bot.py               # 釣魚機器人主邏輯
│   ├── config_manager.py            # 配置管理
│   ├── logger.py                    # 日誌模組
│   ├── window_manager.py            # 視窗管理
│   ├── input_controller.py          # 輸入控制（PyAutoGUI）
│   ├── input_controller_winapi.py   # 輸入控制（Windows API）
│   └── image_detector.py            # 圖像檢測
├── templates/                       # 存放模板圖片（用於圖像識別）
├── config.yaml                      # 配置檔案
├── requirements.txt                 # 相依套件列表
├── main.py                          # 主程式入口
├── debug_detection_area.py          # 測試檢測區域
└── README.md                        # 說明檔案
```

## 安裝步驟

1. 確保已安裝 Python 3.8 或更高版本

2. 安裝相依套件：
```bash
pip install -r requirements.txt
```

## 配置說明

在運行程式前，請根據實際遊戲修改 `config.yaml` 檔案：

## 使用方法

### 基礎使用

```bash
python main.py
```

## License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.
