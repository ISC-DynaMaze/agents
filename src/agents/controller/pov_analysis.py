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
        lab_img = cv2.cvtColor(self.img, cv2.COLOR_BGR2LAB)

        l_bin = cv2.threshold(lab_img[0], 50, 255, cv2.THRESH_BINARY)
        a_bin = cv2.threshold(lab_img[1], 150, 255, cv2.THRESH_BINARY)
        b_bin = cv2.threshold(lab_img[2], 125, 255, cv2.THRESH_BINARY)
        cv2.imwrite(self.tmp_dir / "l_bin.png", l_bin)
        cv2.imwrite(self.tmp_dir / "a_bin.png", a_bin)
        cv2.imwrite(self.tmp_dir / "b_bin.png", b_bin)
