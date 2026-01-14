"""
圖像檢測模組
"""
import cv2
import numpy as np
import pyautogui
import logging
from typing import Optional, Tuple
from pathlib import Path


class ImageDetector:
    """圖像檢測器"""
    
    def __init__(self, threshold: float = 0.8):
        """
        初始化圖像檢測器
        
        Args:
            threshold: 匹配閾值
        """
        self.threshold = threshold
        self.logger = logging.getLogger("FishingBot.ImageDetector")
    
    def capture_screen(self, region: Optional[Tuple[int, int, int, int]] = None) -> np.ndarray:
        """
        截取螢幕
        
        Args:
            region: 截取區域 (x, y, width, height)
            
        Returns:
            截圖的 numpy 陣列
        """
        try:
            screenshot = pyautogui.screenshot(region=region)
            return cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
        except Exception as e:
            self.logger.error(f"截屏失敗: {e}")
            return None
    
    def find_template(self, screen: np.ndarray, template_path: str, threshold: Optional[float] = None) -> Optional[Tuple[int, int]]:
        """
        在螢幕截圖中查找模板圖像
        
        Args:
            screen: 螢幕截圖
            template_path: 模板圖像路徑
            threshold: 匹配閾值（可選，預設使用初始化時的閾值）
            
        Returns:
            匹配位置的中心座標 (x, y)，未找到返回 None
        """
        if screen is None:
            return None
        
        # 使用傳入的閾值，如果沒有則使用預設閾值
        match_threshold = threshold if threshold is not None else self.threshold
        
        template_file = Path(template_path)
        if not template_file.exists():
            self.logger.warning(f"模板檔案不存在: {template_path}")
            return None
        
        try:
            template = cv2.imread(str(template_file))
            if template is None:
                self.logger.error(f"無法加載模板圖像: {template_path}")
                return None
            
            # 檢查尺寸：搜索區域必須 >= 模板圖片
            screen_h, screen_w = screen.shape[:2]
            template_h, template_w = template.shape[:2]
            
            if screen_h < template_h or screen_w < template_w:
                self.logger.warning(
                    f"搜索區域 ({screen_w}x{screen_h}) 小於模板 ({template_w}x{template_h})，"
                    f"請調整遊戲窗口大小或使用更小的模板圖片"
                )
                return None
            
            result = cv2.matchTemplate(screen, template, cv2.TM_CCOEFF_NORMED)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
            
            if max_val >= match_threshold:
                # 返回匹配區域的中心點
                h, w = template.shape[:2]
                center_x = max_loc[0] + w // 2
                center_y = max_loc[1] + h // 2
                self.logger.debug(f"找到模板，匹配度: {max_val:.2f}，位置: ({center_x}, {center_y})")
                return (center_x, center_y)
            else:
                self.logger.debug(f"未找到模板，最高匹配度: {max_val:.2f}")
                return None
                
        except Exception as e:
            self.logger.error(f"模板匹配失敗: {e}")
            return None
    
    def detect_red_ratio(self, screen: np.ndarray, lower_red1: Tuple[int, int, int] = (0, 50, 50),
                        upper_red1: Tuple[int, int, int] = (10, 255, 255),
                        lower_red2: Tuple[int, int, int] = (170, 50, 50),
                        upper_red2: Tuple[int, int, int] = (180, 255, 255)) -> float:
        """
        檢測圖像中紅色像素的比例
        
        Args:
            screen: 輸入圖像（BGR格式）
            lower_red1: 紅色HSV範圍1的下界
            upper_red1: 紅色HSV範圍1的上界
            lower_red2: 紅色HSV範圍2的下界（紅色在HSV中跨越180度）
            upper_red2: 紅色HSV範圍2的上界
            
        Returns:
            紅色像素占總像素的比例 (0.0 - 1.0)
        """
        if screen is None:
            return 0.0
        
        try:
            # 轉換為HSV色彩空間
            hsv = cv2.cvtColor(screen, cv2.COLOR_BGR2HSV)
            
            # 創建紅色掩码（紅色在HSV中跨越0和180度，需要兩個範圍）
            mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
            mask2 = cv2.inRange(hsv, lower_red2, upper_red2)
            red_mask = cv2.bitwise_or(mask1, mask2)
            
            # 計算紅色像素数量
            red_pixels = cv2.countNonZero(red_mask)
            total_pixels = screen.shape[0] * screen.shape[1]
            
            ratio = red_pixels / total_pixels if total_pixels > 0 else 0.0
            return ratio
        except Exception as e:
            self.logger.error(f"紅色檢測失敗: {e}")
            return 0.0
    
    def detect_color_change(self, region: Tuple[int, int, int, int], 
                           target_color: Tuple[int, int, int],
                           tolerance: int = 30) -> bool:
        """
        檢測指定區域的顏色變化
        
        Args:
            region: 檢測區域 (x, y, width, height)
            target_color: 目標顏色 (B, G, R)
            tolerance: 顏色容差
            
        Returns:
            是否檢測到目標顏色
        """
        screen = self.capture_screen(region)
        if screen is None:
            return False
        
        try:
            # 計算平均顏色
            avg_color = cv2.mean(screen)[:3]
            
            # 檢查顏色是否在容差範圍内
            color_diff = sum(abs(avg_color[i] - target_color[i]) for i in range(3))
            
            if color_diff <= tolerance * 3:
                self.logger.debug(f"檢測到顏色變化，平均顏色: {avg_color}")
                return True
            return False
            
        except Exception as e:
            self.logger.error(f"顏色檢測失敗: {e}")
            return False
    
    def save_screenshot(self, filename: str, region: Optional[Tuple[int, int, int, int]] = None):
        """
        保存截圖（用於測試）
        
        Args:
            filename: 保存的檔案名稱
            region: 截取區域
        """
        screen = self.capture_screen(region)
        if screen is not None:
            cv2.imwrite(filename, screen)
            self.logger.info(f"截圖已保存: {filename}")
    
    def find_white_splash(self, region: Tuple[int, int, int, int], 
                         white_threshold: int = 200,
                         min_area: int = 50) -> Optional[Tuple[int, int]]:
        """
        檢測白色水花的位置
        
        Args:
            region: 檢測區域 (x, y, width, height)
            white_threshold: 白色閾值 (0-255)
            min_area: 最小面積（過濾噪点）
            
        Returns:
            白色水花的中心位置 (x, y)，相對於整個螢幕，未找到返回 None
        """
        screen = self.capture_screen(region)
        if screen is None:
            return None
        
        try:
            # 轉換為灰度圖
            gray = cv2.cvtColor(screen, cv2.COLOR_BGR2GRAY)
            
            # 二值化：提取白色區域
            _, binary = cv2.threshold(gray, white_threshold, 255, cv2.THRESH_BINARY)
            
            # 查找輪廓
            contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            if not contours:
                return None
            
            # 找到面積最大的輪廓（假設為水花）
            valid_contours = [c for c in contours if cv2.contourArea(c) >= min_area]
            if not valid_contours:
                return None
            
            largest_contour = max(valid_contours, key=cv2.contourArea)
            
            # 計算輪廓的中心點
            M = cv2.moments(largest_contour)
            if M["m00"] == 0:
                return None
            
            # 相對於檢測區域的座標
            cx = int(M["m10"] / M["m00"])
            cy = int(M["m01"] / M["m00"])
            
            # 轉換為絕對螢幕座標
            abs_x = region[0] + cx
            abs_y = region[1] + cy
            
            self.logger.debug(f"檢測到白色水花: ({abs_x}, {abs_y}), 面積: {cv2.contourArea(largest_contour):.0f}")
            return (abs_x, abs_y)
            
        except Exception as e:
            self.logger.error(f"白色水花檢測失敗: {e}")
            return None
