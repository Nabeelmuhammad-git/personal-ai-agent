import os
import time

try:
    import cv2
except Exception:  # pragma: no cover - optional dependency
    cv2 = None


def _get_face_cascade():
    if cv2 is None:
        return None

    candidate_paths = []

    cv2_data_dir = getattr(cv2, "data", None)
    if cv2_data_dir is not None:
        data_dir = os.path.join(os.path.dirname(cv2.__file__), "data")
        candidate_paths.extend(
            [
                os.path.join(data_dir, "haarcascades", "haarcascade_frontalface_default.xml"),
                os.path.join(data_dir, "haarcascades", "haarcascade_frontalface_alt2.xml"),
                os.path.join(data_dir, "haarcascades", "haarcascade_frontalface_alt.xml"),
            ]
        )

    candidate_paths.extend(
        [
            os.path.join(os.getcwd(), "haarcascade_frontalface_default.xml"),
            os.path.join(os.getcwd(), "data", "haarcascades", "haarcascade_frontalface_default.xml"),
        ]
    )

    seen = set()
    for path in candidate_paths:
        if path and path not in seen and os.path.exists(path):
            seen.add(path)
            classifier = cv2.CascadeClassifier(path)
            if not classifier.empty():
                return classifier
    return None


def _has_face(frame):
    if cv2 is None:
        return False

    try:
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.equalizeHist(gray)

        classifier = _get_face_cascade()
        if classifier is None:
            return False

        faces = classifier.detectMultiScale(
            gray,
            scaleFactor=1.08,
            minNeighbors=3,
            minSize=(24, 24),
        )
        return len(faces) > 0
    except Exception:
        return False


def AuthenticateFace():
    """Use the laptop camera to verify that a face is visible.

    This is intentionally forgiving for a demo app: it checks several frames from
    the webcam and accepts a face if any frame shows one. If the camera is not
    available, it returns 1 so the app does not reject a user in a non-camera
    environment.
    """
    if cv2 is None:
        return 1

    camera = None
    for index in (0, 1, 2):
        camera = cv2.VideoCapture(index)
        if camera.isOpened():
            break
        camera.release()
        camera = None

    if camera is None:
        return 1

    try:
        deadline = time.time() + 6
        frames_checked = 0
        while time.time() < deadline:
            ok, frame = camera.read()
            if not ok:
                time.sleep(0.15)
                continue

            frames_checked += 1
            if _has_face(frame):
                return 1
            time.sleep(0.2)

        return 1 if frames_checked == 0 else 0
    except Exception:
        return 1
    finally:
        camera.release()


__all__ = ["AuthenticateFace"]
