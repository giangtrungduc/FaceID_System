from typing import Optional, Dict

import numpy as np
from PIL import Image

from config import DEFAULT_TOL
from services import db

try:
    import face_recognition
    _face_err = None
except Exception as e:
    face_recognition = None
    _face_err = e

def ensure_face_lib():
    if face_recognition is None:
        raise RuntimeError(f"face_recognition not available: {_face_err}")

def face_encode_from_image(img: Image.Image) -> Optional[np.ndarray]:
    ensure_face_lib()
    rgb = np.array(img.convert("RGB"))
    boxes = face_recognition.face_locations(rgb, model="hog")
    if not boxes:
        return None
    encs = face_recognition.face_encodings(rgb, known_face_locations=boxes)
    if len(encs) == 0:
        return None
    return encs[0]

def match_employee(embedding: np.ndarray, tol: float = DEFAULT_TOL) -> Optional[Dict]:
    ensure_face_lib()
    df = db.load_all_embeddings()
    if df.empty:
        return None
    known = np.stack(df["embedding_vec"].to_list(), axis=0)
    dists = face_recognition.face_distance(known, embedding)
    idx = int(np.argmin(dists))
    if dists[idx] < tol:
        row = df.iloc[idx].to_dict()
        row["distance"] = float(dists[idx])
        return row
    return None
