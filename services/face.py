# services/face.py
"""
Module xử lý nhận diện khuôn mặt
"""

from typing import Optional, Dict
import numpy as np
from PIL import Image

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import DEFAULT_TOL, FACE_DETECTION_MODEL
from services import db

try:
    import face_recognition
    _face_err = None
except Exception as e:
    face_recognition = None
    _face_err = e

def ensure_face_lib():
    """Kiểm tra thư viện face_recognition có sẵn không"""
    if face_recognition is None:
        raise RuntimeError(f"face_recognition not available: {_face_err}")

def face_encode_from_image(img: Image.Image) -> Optional[np.ndarray]:
    """
    Trích xuất vector embedding từ ảnh khuôn mặt
    
    Args:
        img: PIL Image object
        
    Returns:
        numpy array (128-d vector) hoặc None nếu không tìm thấy khuôn mặt
    """
    ensure_face_lib()
    rgb = np.array(img.convert("RGB"))
    
    # Phát hiện khuôn mặt
    boxes = face_recognition.face_locations(rgb, model=FACE_DETECTION_MODEL)
    if not boxes:
        return None
    
    # Trích xuất encoding
    encs = face_recognition.face_encodings(rgb, known_face_locations=boxes)
    if len(encs) == 0:
        return None
        
    return encs[0]

def match_employee(embedding: np.ndarray, tol: float = DEFAULT_TOL) -> Optional[Dict]:
    """
    Tìm kiếm nhân viên khớp với embedding
    
    Args:
        embedding: Vector 128-d từ khuôn mặt
        tol: Ngưỡng chấp nhận (mặc định từ config)
        
    Returns:
        Dict thông tin nhân viên hoặc None nếu không khớp
    """
    ensure_face_lib()
    
    # Load tất cả nhân viên
    df = db.load_all_embeddings()
    if df.empty:
        return None
    
    # Tính khoảng cách với tất cả nhân viên
    known = np.stack(df["embedding_vec"].to_list(), axis=0)
    dists = face_recognition.face_distance(known, embedding)
    
    # Tìm người có khoảng cách nhỏ nhất
    idx = int(np.argmin(dists))
    
    if dists[idx] < tol:
        row = df.iloc[idx].to_dict()
        row["distance"] = float(dists[idx])
        return row
        
    return None