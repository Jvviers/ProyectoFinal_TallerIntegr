from io import BytesIO
from typing import Tuple

import pandas as pd

# Columnas exactas que espera el model_pipeline.pkl (verificado desde feature_names_in_)
FEATURE_COLUMNS = [
    "acc_chest_X", "acc_chest_Y", "acc_chest_Z",
    "ecg_lead_1", "ecg_lead_2",
    "acc_ankle_X", "acc_ankle_Y", "acc_ankle_Z",
    "gyro_ankle_X", "gyro_ankle_Y", "gyro_ankle_Z",
    "mag_ankle_X", "mag_ankle_Y", "mag_ankle_Z",
    "acc_arm_X", "acc_arm_Y", "acc_arm_Z",
    "gyro_arm_X", "gyro_arm_Y", "gyro_arm_Z",
    "mag_arm_X", "mag_arm_Y", "mag_arm_Z",
]

EXPECTED_FEATURES = len(FEATURE_COLUMNS)  # 23 columnas
LABEL_VALUE_RANGE = set(range(0, 30))  # rango tipico de etiquetas/subject en MHealth


def _decode_preview(file_bytes: bytes, sample_size: int = 2000) -> str:
    if not file_bytes:
        raise ValueError("El archivo esta vacio.")

    for encoding in ("utf-8", "latin-1"):
        try:
            return file_bytes[:sample_size].decode(encoding)
        except UnicodeDecodeError:
            continue

    raise ValueError("No se pudo decodificar el archivo. Usa UTF-8 o Latin-1.")


def _detect_separator(preview: str) -> str:
    first_line = next((line for line in preview.splitlines() if line.strip()), "")
    if not first_line:
        raise ValueError("El archivo no contiene filas con datos.")

    if "\t" in first_line:
        return "\t"  # tabulacion estandar del dataset original

    if " " in first_line:
        return r"\s+"  # espacios multiples

    raise ValueError(
        "No se pudo detectar el separador. Usa tabulaciones '\\t' o espacios."
    )


def _is_integer_series(series: pd.Series) -> bool:
    if not pd.api.types.is_numeric_dtype(series):
        return False

    cleaned = series.dropna()
    if cleaned.empty:
        return False

    return bool(((cleaned % 1) == 0).all())


def _looks_like_label(series: pd.Series) -> bool:
    if not _is_integer_series(series):
        return False

    values = series.dropna().astype(int)
    if values.empty:
        return False

    unique_values = set(values.unique().tolist())
    if unique_values <= LABEL_VALUE_RANGE:
        return True

    return len(unique_values) < 30


def process_log_file(file_bytes: bytes) -> Tuple[pd.DataFrame, dict]:
    """
    Lee un archivo .log de MHealth, detecta separador y columnas, valida formato,
    y devuelve un DataFrame listo para el pipeline (solo 23 columnas de senales)
    mas metadatos de la deteccion.
    """
    preview = _decode_preview(file_bytes)
    separator = _detect_separator(preview)

    try:
        df = pd.read_csv(BytesIO(file_bytes), sep=separator, header=None, engine="python")
    except Exception as exc:
        raise ValueError(f"No se pudo leer el archivo .log: {exc}") from exc

    if df.empty:
        raise ValueError("El archivo no contiene datos.")

    col_count = df.shape[1]
    label_detected = None  # None: no existe; "Label": era label; "Subject": id/subject

    if col_count == EXPECTED_FEATURES:
        df.columns = FEATURE_COLUMNS
    elif col_count == EXPECTED_FEATURES + 1:
        df.columns = FEATURE_COLUMNS + ["_extra"]
        extra_col = df.columns[-1]
        extra_series = df[extra_col]

        if _looks_like_label(extra_series):
            label_detected = "Label"
        elif _is_integer_series(extra_series) and extra_series.nunique() == 1:
            label_detected = "Subject"
        else:
            raise ValueError(
                "La ultima columna no parece ser la etiqueta ni un identificador "
                "numerico. Se esperaban 23 columnas de sensores (+ Label/Subject opcional al final)."
            )

        df = df.drop(columns=[extra_col])
    else:
        raise ValueError(
            f"Formato invalido: se detectaron {col_count} columnas usando separador "
            f"'{separator}'. El pipeline requiere 23 columnas de sensores "
            f"(mas una columna Label/Subject opcional al final)."
        )

    info = {
        "separator": "\\t" if separator == "\t" else "espacios",
        "columns_detected": col_count,
        "label_column": label_detected,
    }

    return df[FEATURE_COLUMNS], info
