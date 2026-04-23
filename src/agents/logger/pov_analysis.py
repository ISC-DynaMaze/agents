from pathlib import Path

import cv2
import numpy as np
from spade.behaviour import OneShotBehaviour


class AnalysePOVBehaviour(OneShotBehaviour):
    def __init__(self, img: np.ndarray):
        super().__init__()
        self.img : np.ndarray = img
        self.tmp_dir: Path = Path("tmp")
        self.tmp_dir.mkdir(parents=True, exist_ok=True)
    
    async def run(self):
        img = cv2.GaussianBlur(self.img, (11, 11), 5)
        lab_img = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)

        l_bin = np.where(lab_img[..., 0] > 50, 255, 0).astype(np.uint8)
        a_bin = np.where(lab_img[..., 1] > 150, 255, 0).astype(np.uint8)
        b_bin = np.where(lab_img[..., 2] > 125, 255, 0).astype(np.uint8)

        l, a, b = cv2.split(lab_img)
        #l_bin = cv2.adaptiveThreshold(l, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY+cv2.THRESH_OTSU, 11, 5)
        #a_bin = cv2.adaptiveThreshold(a, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY+cv2.THRESH_OTSU, 11, 5)
        #b_bin = cv2.adaptiveThreshold(b, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY+cv2.THRESH_OTSU, 11, 5)
        _, l_bin = cv2.threshold(l, 0, 255, cv2.THRESH_BINARY|cv2.THRESH_OTSU)
        _, a_bin = cv2.threshold(a, 0, 255, cv2.THRESH_BINARY|cv2.THRESH_OTSU)
        _, b_bin = cv2.threshold(b, 0, 255, cv2.THRESH_BINARY|cv2.THRESH_OTSU)
        cv2.imwrite(self.tmp_dir / "l_bin.png", l_bin.astype(np.uint8))
        cv2.imwrite(self.tmp_dir / "a_bin.png", a_bin.astype(np.uint8))
        cv2.imwrite(self.tmp_dir / "b_bin.png", b_bin.astype(np.uint8))

        cnts, hrcy = cv2.findContours(l_bin, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        with_cnts = self.img.copy()
        cv2.drawContours(with_cnts, cnts, -1, (0, 0, 255), 2)
        img_area = img.shape[0] * img.shape[1]

        for cnt in cnts:
            rect = cv2.minAreaRect(cnt)
            box = cv2.boxPoints(rect)
            area = cv2.contourArea(box)
            v1 = box[1] - box[0]
            v2 = box[3] - box[0]
            l1 = np.linalg.norm(v1)
            l2 = np.linalg.norm(v2)
            a, b = (l1, l2) if l1 < l2 else (l2, l1)
            box = np.intp(box)
            cv2.drawContours(with_cnts, [box], 0, (0,255, 255), 1)
            ratio = b / a
            if ratio < 1 or ratio > 6:
                print(ratio)
                continue
            area_ratio = area / img_area
            
            if area_ratio < 0.003 or area_ratio > 0.02:
                continue
            cv2.drawContours(with_cnts, [box], 0, (0,255, 0), 2)

        self.detect_plinth(self.img)

        cv2.imwrite(self.tmp_dir / "contours.png", with_cnts)
    
    def detect_plinth(self, img: np.ndarray):
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 11, 5)
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (11, 11))
        #dilated = cv2.dilate(thresh, kernel)
        linesP = cv2.HoughLinesP(
            image=thresh,
            rho=1,
            theta=np.pi / 180,
            threshold=150,
            minLineLength=50,
            maxLineGap=50
        )
        
        with_lines = img.copy()
        if linesP is not None:
            for i in range(0, len(linesP)):
                l = linesP[i][0]
                cv2.line(with_lines, (l[0], l[1]), (l[2], l[3]), (0,0,255), 3, cv2.LINE_AA)
        cv2.imwrite(self.tmp_dir / "lines.png", with_lines)

