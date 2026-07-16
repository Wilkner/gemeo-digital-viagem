from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
from datetime import datetime
import io
from typing import Optional, Tuple, Dict, Any

class MediaService:
    @staticmethod
    def _convert_to_degrees(value) -> float:
        """
        Converte as coordenadas GPS do formato EXIF (Graus, Minutos, Segundos)
        para o formato Decimal (float).
        """
        # Trata o formato de tuplas/frações do Pillow
        try:
            degrees = float(value[0])
            minutes = float(value[1])
            seconds = float(value[2])
            return degrees + (minutes / 60.0) + (seconds / 3600.0)
        except (TypeError, IndexError, ZeroDivisionError):
            return 0.0

    @classmethod
    def extract_exif(cls, image_bytes: bytes) -> Dict[str, Any]:
        """
        Recebe os bytes de uma imagem, extrai os metadados EXIF de data, hora e GPS.
        """
        metadata = {
            "taken_at": None,
            "latitude": None,
            "longitude": None
        }
        
        try:
            image = Image.open(io.BytesIO(image_bytes))
            exif_data = image._getexif()
            
            if not exif_data:
                return metadata
                
            gps_info = {}
            
            for tag_id, value in exif_data.items():
                tag_name = TAGS.get(tag_id, tag_id)
                
                # 1. Extrai Data e Hora Original
                if tag_name == "DateTimeOriginal":
                    try:
                        # O formato padrão EXIF é "YYYY:MM:DD HH:MM:SS"
                        # Vamos converter para ISO format para facilitar no JSON
                        dt = datetime.strptime(value, "%Y:%m:%d %H:%M:%S")
                        metadata["taken_at"] = dt.isoformat()
                    except ValueError:
                        metadata["taken_at"] = value
                        
                # 2. Extrai bloco de informações de GPS
                elif tag_name == "GPSInfo":
                    for gps_tag_id in value:
                        gps_tag_name = GPSTAGS.get(gps_tag_id, gps_tag_id)
                        gps_info[gps_tag_name] = value[gps_tag_id]
            
            # 3. Calcula Latitude e Longitude decimais se o bloco GPS existir
            if gps_info:
                lat_value = gps_info.get("GPSLatitude")
                lat_ref = gps_info.get("GPSLatitudeRef")  # 'N' ou 'S'
                lon_value = gps_info.get("GPSLongitude")
                lon_ref = gps_info.get("GPSLongitudeRef")  # 'E' ou 'W'
                
                if lat_value and lat_ref and lon_value and lon_ref:
                    lat = cls._convert_to_degrees(lat_value)
                    if lat_ref != "N":
                        lat = -lat
                        
                    lon = cls._convert_to_degrees(lon_value)
                    if lon_ref != "E":
                        lon = -lon
                        
                    metadata["latitude"] = round(lat, 6)
                    metadata["longitude"] = round(lon, 6)
                    
        except Exception as e:
            # Em produção, você logaria o erro. No MVP, retornamos o dict vazio para evitar quebras.
            print(f"Erro ao ler EXIF: {str(e)}")
            
        return metadata