# 釣魚自動化

基於 Python 的 スタレゾ 釣魚自動化工具

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
├── config.yaml                      # 配置文件
├── requirements.txt                 # 依賴包列表
├── main.py                          # 主程式入口
├── debug_detection_area.py          # 測試檢測區域
└── README.md                        # 說明文件
```

## 安装步骤

1. 確保已安装 Python 3.8 或更高版本

2. 安装依賴包：
```bash
pip install -r requirements.txt
```

## 配置說明

在運行程式前，請根据實際遊戲修改 `config.yaml` 文件：

## 使用方法

### 基礎使用

```bash
python main.py
```
