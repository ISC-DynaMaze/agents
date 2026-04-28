import base64
import datetime
from typing import Literal

import aiofiles
import numpy as np

from common.models.base import RequestBase, ResponseBase


class CameraRequest(RequestBase):
    type: Literal["cam-req"] = "cam-req"  # type: ignore


class CameraResponse(ResponseBase):
    type: Literal["cam-res"] = "cam-res"  # type: ignore
    img: str

    async def decode_img(self, img, save_dir):
        import cv2
        print("Received photo message.")
        img_data = base64.b64decode(img)

        # Generate filename with timestamp
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"photo_{timestamp}.jpg"
        filepath = save_dir / filename

        # Save the received image
        async with aiofiles.open(filepath, "wb") as img_file:
            await img_file.write(img_data)

        print(f"Photo saved as '{filepath}'.")
        img: np.ndarray = cv2.imread(str(filepath))  # type: ignore

        return img, filepath
