"""
檢測區域測試工具
運行此腳本可以預覽配置的檢測區域
"""

import sys
from pathlib import Path

import cv2
import numpy as np
import pyautogui
import pygetwindow as gw
import yaml


def load_config():
    """加載配置檔案"""
    config_path = Path("config.yaml")
    if not config_path.exists():
        print("錯誤: 找不到 config.yaml 檔案")
        sys.exit(1)

    with open(config_path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def find_game_window(window_title):
    """查找遊戲視窗"""
    windows = gw.getWindowsWithTitle(window_title)
    if not windows:
        print(f"錯誤: 未找到標題包含 '{window_title}' 的視窗")
        print("\n提示: 運行 get_window_title.py 查看所有視窗")
        return None
    return windows[0]


def draw_region_on_screen(window, region_config, color, label, offset_y=0):
    """在視窗截圖上繪製區域框"""
    x, y, w, h = window.left, window.top, window.width, window.height

    _, _ = x, y  # 未使用的變量，避免警告

    # 計算區域座標
    region_x = int(w * region_config["x"])
    region_y = int(h * region_config["y"])
    region_w = int(w * region_config["width"])
    region_h = int(h * region_config["height"])

    return {
        "rect": (region_x, region_y, region_w, region_h),
        "color": color,
        "label": label,
        "offset_y": offset_y,
    }


def main():
    print("=" * 60)
    print("檢測區域測試工具")
    print("=" * 60)

    # 加載配置
    config = load_config()
    window_title = config.get("game", {}).get("window_title", "")

    if not window_title:
        print("錯誤: config.yaml 中未設置 window_title")
        return

    # 查找視窗
    print(f"\n正在查找視窗: {window_title}")
    window = find_game_window(window_title)
    if not window:
        return

    print(f"找到視窗: {window.title}")
    print(f"視窗位置: ({window.left}, {window.top})")
    print(f"視窗大小: {window.width}x{window.height}")

    # 激活視窗
    if window.isMinimized:
        window.restore()
    window.activate()

    print("\n正在截取視窗...")
    import time

    time.sleep(0.5)  # 等待視窗激活

    # 截取視窗
    screenshot = pyautogui.screenshot(
        region=(window.left, window.top, window.width, window.height)
    )
    img = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)

    # 准备繪製的區域
    regions = []

    # 1. 咬勾檢測區域
    bite_region = config.get("detection", {}).get("region", {})
    if bite_region:
        regions.append(
            draw_region_on_screen(
                window, bite_region, (0, 0, 255), "bite_region", 0
            )
        )

    # 2. 魚追踪區域
    fish_splash_region = (
        config.get("detection", {}).get("fish_splash", {}).get("region", {})
    )
    center_threshold = (
        config.get("fishing", {})
        .get("fish_tracking", {})
        .get("center_threshold", 0.1)
    )
    if fish_splash_region:
        regions.append(
            draw_region_on_screen(
                window,
                fish_splash_region,
                (0, 255, 0),
                "fish_splash_region",
                30,
            )
        )

        # 繪製中心閾值線（左邊界和右邊界）
        splash_x = int(window.width * fish_splash_region["x"])
        splash_y = int(window.height * fish_splash_region["y"])
        splash_w = int(window.width * fish_splash_region["width"])
        splash_h = int(window.height * fish_splash_region["height"])

        # 計算閾值邊界
        threshold_pixels = int(window.width * center_threshold)
        center_offset = config.get("fishing.fish_tracking.center_offset", 0)
        center_x = window.width // 2 + center_offset  # 視窗中心X座標
        left_boundary = center_x - threshold_pixels
        right_boundary = center_x + threshold_pixels

        # 確保邊界在追踪區域内
        if left_boundary >= splash_x and left_boundary <= splash_x + splash_w:
            # 繪製左邊界線（相對於截圖座標）
            cv2.line(
                img,
                (left_boundary, splash_y),
                (left_boundary, splash_y + splash_h),
                (255, 255, 0),
                2,
            )
        if (
            right_boundary >= splash_x
            and right_boundary <= splash_x + splash_w
        ):
            # 繪製右邊界線
            cv2.line(
                img,
                (right_boundary, splash_y),
                (right_boundary, splash_y + splash_h),
                (255, 255, 0),
                2,
            )

        # 繪製中心線
        cv2.line(
            img,
            (center_x, splash_y),
            (center_x, splash_y + splash_h),
            (255, 128, 0),
            2,
        )

        # 添加標註
        cv2.putText(
            img,
            "Center",
            (center_x + 5, splash_y + 20),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (255, 128, 0),
            2,
        )
        cv2.putText(
            img,
            f"Threshold: {center_threshold:.1%}",
            (splash_x, splash_y + splash_h + 20),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (255, 255, 0),
            2,
        )

    # 3. 拉力計檢測區域
    tension_bar_region = (
        config.get("detection", {}).get("tension_bar", {}).get("region", {})
    )
    if tension_bar_region:
        regions.append(
            draw_region_on_screen(
                window,
                tension_bar_region,
                (0, 255, 255),
                "tension_bar_region",
                60,
            )
        )

    # 4. 紅色張力檢測區域
    red_tension_region = (
        config.get("detection", {}).get("red_tension", {}).get("region", {})
    )
    if red_tension_region:
        regions.append(
            draw_region_on_screen(
                window,
                red_tension_region,
                (0, 128, 255),
                "red_tension_region",
                90,
            )
        )

    # 5. "再來一次"按鈕檢測區域
    retry_button_region = (
        config.get("detection", {}).get("retry_button", {}).get("region", {})
    )
    if retry_button_region:
        regions.append(
            draw_region_on_screen(
                window,
                retry_button_region,
                (255, 0, 255),
                "retry_button_region",
                120,
            )
        )

    # 6. 魚竿耐久度檢測區域
    rod_durability_region = (
        config.get("detection", {}).get("rod_durability", {}).get("region", {})
    )
    if rod_durability_region:
        regions.append(
            draw_region_on_screen(
                window,
                rod_durability_region,
                (128, 0, 255),
                "rod_durability_region",
                150,
            )
        )

    # 點擊位置（如果使用點擊模式）
    if config.get("fishing", {}).get("cast_type") == "click":
        cast_pos = config.get("fishing", {}).get("cast_click_pos", {})
        if cast_pos:
            click_x = int(window.width * cast_pos["x"])
            click_y = int(window.height * cast_pos["y"])
            cv2.circle(img, (click_x, click_y), 10, (255, 0, 0), 2)
            cv2.putText(
                img,
                "抛竿點擊位置",
                (click_x + 15, click_y),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (255, 0, 0),
                2,
            )

    # 魚竿更換的點擊位置
    rod_config = config.get("detection", {}).get("rod_durability", {})
    first_click_pos = rod_config.get("first_click_pos", {})
    second_click_pos = rod_config.get("second_click_pos", {})

    if first_click_pos:
        first_x = int(window.width * first_click_pos["x"])
        first_y = int(window.height * first_click_pos["y"])
        # 繪製第一次點擊位置（綠色）
        cv2.circle(img, (first_x, first_y), 12, (0, 255, 0), -1)
        cv2.circle(img, (first_x, first_y), 15, (0, 255, 0), 2)
        cv2.putText(
            img,
            "Rod Replace 1st Click",
            (first_x + 20, first_y - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (0, 255, 0),
            2,
        )

    if second_click_pos:
        second_x = int(window.width * second_click_pos["x"])
        second_y = int(window.height * second_click_pos["y"])
        # 繪製第二次點擊位置（紅色）
        cv2.circle(img, (second_x, second_y), 12, (0, 0, 255), -1)
        cv2.circle(img, (second_x, second_y), 15, (0, 0, 255), 2)
        cv2.putText(
            img,
            "Rod Replace 2nd Click",
            (second_x + 20, second_y - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (0, 0, 255),
            2,
        )

    # 如果兩個點擊位置都存在，繪製連接線
    if first_click_pos and second_click_pos:
        first_x = int(window.width * first_click_pos["x"])
        first_y = int(window.height * first_click_pos["y"])
        second_x = int(window.width * second_click_pos["x"])
        second_y = int(window.height * second_click_pos["y"])
        cv2.arrowedLine(
            img,
            (first_x, first_y),
            (second_x, second_y),
            (255, 255, 0),
            2,
            tipLength=0.3,
        )

    # 繪製所有區域框
    for region_info in regions:
        rect = region_info["rect"]
        color = region_info["color"]
        label = region_info["label"]
        offset_y = region_info["offset_y"]

        x, y, w, h = rect
        # 繪製矩形框
        cv2.rectangle(img, (x, y), (x + w, y + h), color, 3)

        # 繪製標籤背景
        label_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)[
            0
        ]
        cv2.rectangle(
            img,
            (x, y - 30 - offset_y),
            (x + label_size[0] + 10, y - 5 - offset_y),
            color,
            -1,
        )

        # 繪製標籤文字
        cv2.putText(
            img,
            label,
            (x + 5, y - 10 - offset_y),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 255, 255),
            2,
        )

    # 添加說明文字
    info_text = [
        "檢測區域預覽",
        f"視窗大小: {window.width}x{window.height}",
        "",
        "區域說明:",
        "  紅色框 = 咬勾檢測區域",
        "  綠色框 = 魚追踪區域",
        "  黄色框 = 拉力計檢測區域",
        "  橙色框 = 紅色張力檢測區域",
        "  紫红框 = 再來一次按鈕區域",
        "  紫色框 = 魚竿耐久度檢測區域",
        "",
        "點擊位置:",
        "  橙色線 = 視窗中心",
        "  青色線 = 追踪閾值邊界",
        "  綠色圓 = 第一次點擊（更換魚竿）",
        "  紅色圓 = 第二次點擊（更換魚竿）",
        "  黄色箭头 = 點擊順序",
        "",
        "按鍵說明:",
        "  S - 保存截圖",
        "  Q - 退出",
        "  R - 刷新",
    ]

    y_offset = 30
    for text in info_text:
        cv2.putText(
            img,
            text,
            (10, y_offset),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (255, 255, 255),
            2,
        )
        # 添加黑色背景讓文字更清晰
        cv2.putText(
            img,
            text,
            (10, y_offset),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (0, 0, 0),
            1,
        )
        y_offset += 25

    # 保存到檔案
    output_file = "debug_detection_area.png"
    cv2.imwrite(output_file, img)
    print(f"\n✓ 截圖已保存: {output_file}")

    # 顯示圖片
    print("\n顯示預覽視窗...")
    print("提示: 按 'S' 保存截圖, 'Q' 退出, 'R' 刷新")

    cv2.namedWindow("Detection Area Preview", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("Detection Area Preview", 1280, 720)

    while True:
        cv2.imshow("Detection Area Preview", img)
        key = cv2.waitKey(1) & 0xFF

        if key == ord("q") or key == ord("Q") or key == 27:  # Q 或 ESC
            print("\n退出預覽")
            break
        elif key == ord("s") or key == ord("S"):
            output_file = f"debug_detection_area_{int(time.time())}.png"
            cv2.imwrite(output_file, img)
            print(f"✓ 截圖已保存: {output_file}")
        elif key == ord("r") or key == ord("R"):
            print("\n刷新截圖...")
            # 重新運行主函數
            cv2.destroyAllWindows()
            time.sleep(0.5)
            main()
            return

    cv2.destroyAllWindows()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n用戶中断")
    except Exception as e:
        print(f"\n錯誤: {e}")
        import traceback

        traceback.print_exc()
