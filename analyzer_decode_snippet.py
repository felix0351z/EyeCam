# Auf der Analyzer-Seite: Bytes zurück in 8x8-Arrays verwandeln (Python-Beispiel)
import numpy as np

def decode_sensor(p):
    dist   = np.frombuffer(p.distance_mm,    dtype="<i2").reshape(8, 8)
    status = np.frombuffer(p.target_status,  dtype="<u1").reshape(8, 8)
    sigma  = np.frombuffer(p.range_sigma_mm, dtype="<u2").reshape(8, 8)
    return dist, status, sigma
