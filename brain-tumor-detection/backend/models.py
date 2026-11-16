"""
Data Models and Schema Definitions for BrainSight AI MongoDB Integration.
Represents the 6 core collections:
1. users
2. mri_scans
3. enhancement_results
4. detection_results
5. gradcam_results
6. reports
"""

import re
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List

EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
ALLOWED_FORMATS = {'JPG', 'JPEG', 'PNG', 'BMP', 'TIFF'}
ALLOWED_CLASSES = {'Glioma', 'Meningioma', 'Pituitary Tumor', 'No Tumor'}
ALLOWED_STATUSES = {'uploaded', 'enhanced', 'analyzed', 'completed', 'error'}

def current_iso_timestamp() -> str:
    """Returns ISO 8601 UTC timestamp."""
    return datetime.utcnow().isoformat() + 'Z'

class User:
    """User account document model."""
    def __init__(
        self,
        name: str,
        email: str,
        password_hash: str,
        user_id: Optional[str] = None,
        created_at: Optional[str] = None,
        role: str = 'clinician'
    ):
        self.user_id = user_id or f"USR-{uuid.uuid4().hex[:8].upper()}"
        self.name = (name or '').strip()
        self.email = (email or '').strip().lower()
        self.password_hash = password_hash
        self.created_at = created_at or current_iso_timestamp()
        self.role = role

    def validate(self) -> None:
        if not self.name or len(self.name) < 2:
            raise ValueError("User name must be at least 2 characters.")
        if not self.email or not EMAIL_REGEX.match(self.email):
            raise ValueError("Invalid email address format.")
        if not self.password_hash:
            raise ValueError("Password hash is required.")

    def to_dict(self, include_sensitive: bool = False) -> Dict[str, Any]:
        data = {
            "user_id": self.user_id,
            "name": self.name,
            "email": self.email,
            "role": self.role,
            "created_at": self.created_at
        }
        if include_sensitive:
            data["password_hash"] = self.password_hash
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'User':
        return cls(
            user_id=data.get('user_id'),
            name=data.get('name', ''),
            email=data.get('email', ''),
            password_hash=data.get('password_hash', ''),
            created_at=data.get('created_at'),
            role=data.get('role', 'clinician')
        )


class MRIScan:
    """MRI scan ingestion document model."""
    def __init__(
        self,
        scan_id: str,
        user_id: str,
        original_image_path: str,
        image_format: str,
        upload_date: Optional[str] = None,
        processing_status: str = 'uploaded',
        filename: Optional[str] = None,
        dimensions: Optional[str] = None,
        file_size: Optional[int] = None,
        patient_id: Optional[str] = None
    ):
        self.scan_id = scan_id
        self.user_id = user_id
        self.original_image_path = original_image_path
        self.image_format = (image_format or 'JPEG').upper()
        self.upload_date = upload_date or current_iso_timestamp()
        self.processing_status = processing_status
        self.filename = filename or scan_id
        self.dimensions = dimensions or "Unknown"
        self.file_size = file_size or 0
        self.patient_id = patient_id or f"P-{uuid.uuid4().hex[:5].upper()}"

    def validate(self) -> None:
        if not self.scan_id:
            raise ValueError("scan_id is required.")
        if not self.user_id:
            raise ValueError("user_id is required.")
        if not self.original_image_path:
            raise ValueError("original_image_path is required.")
        if self.image_format not in ALLOWED_FORMATS:
            raise ValueError(f"image_format must be one of {ALLOWED_FORMATS}")
        if self.processing_status not in ALLOWED_STATUSES:
            raise ValueError(f"processing_status must be one of {ALLOWED_STATUSES}")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "scan_id": self.scan_id,
            "user_id": self.user_id,
            "original_image_path": self.original_image_path,
            "upload_date": self.upload_date,
            "image_format": self.image_format,
            "processing_status": self.processing_status,
            "filename": self.filename,
            "dimensions": self.dimensions,
            "file_size": self.file_size,
            "patient_id": self.patient_id
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MRIScan':
        return cls(
            scan_id=data.get('scan_id'),
            user_id=data.get('user_id'),
            original_image_path=data.get('original_image_path'),
            upload_date=data.get('upload_date'),
            image_format=data.get('image_format', 'JPEG'),
            processing_status=data.get('processing_status', 'uploaded'),
            filename=data.get('filename'),
            dimensions=data.get('dimensions'),
            file_size=data.get('file_size'),
            patient_id=data.get('patient_id')
        )


class EnhancementResult:
    """Enhancement result document model (OpenCV CLAHE / Autoencoder)."""
    def __init__(
        self,
        scan_id: str,
        clahe_image_path: str,
        enhancement_method: str = 'OpenCV CLAHE + Bilateral Filtering',
        enhancement_id: Optional[str] = None,
        autoencoder_image_path: Optional[str] = None,
        parameters: Optional[Dict[str, Any]] = None,
        created_at: Optional[str] = None
    ):
        self.enhancement_id = enhancement_id or f"ENH-{uuid.uuid4().hex[:8].upper()}"
        self.scan_id = scan_id
        self.clahe_image_path = clahe_image_path
        self.autoencoder_image_path = autoencoder_image_path or ""
        self.enhancement_method = enhancement_method
        self.parameters = parameters or {}
        self.created_at = created_at or current_iso_timestamp()

    def validate(self) -> None:
        if not self.enhancement_id:
            raise ValueError("enhancement_id is required.")
        if not self.scan_id:
            raise ValueError("scan_id is required.")
        if not self.clahe_image_path:
            raise ValueError("clahe_image_path is required.")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "enhancement_id": self.enhancement_id,
            "scan_id": self.scan_id,
            "clahe_image_path": self.clahe_image_path,
            "autoencoder_image_path": self.autoencoder_image_path,
            "enhancement_method": self.enhancement_method,
            "parameters": self.parameters,
            "created_at": self.created_at
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EnhancementResult':
        return cls(
            enhancement_id=data.get('enhancement_id'),
            scan_id=data.get('scan_id'),
            clahe_image_path=data.get('clahe_image_path'),
            autoencoder_image_path=data.get('autoencoder_image_path'),
            enhancement_method=data.get('enhancement_method', 'OpenCV CLAHE'),
            parameters=data.get('parameters', {}),
            created_at=data.get('created_at')
        )


class DetectionResult:
    """CNN classification and detection document model."""
    def __init__(
        self,
        scan_id: str,
        predicted_class: str,
        confidence_score: float,
        model_name: str = 'BrainSight CNN / EfficientNet-B0',
        model_version: str = 'v4.2',
        detection_id: Optional[str] = None,
        probabilities: Optional[Dict[str, float]] = None,
        created_at: Optional[str] = None
    ):
        self.detection_id = detection_id or f"DET-{uuid.uuid4().hex[:8].upper()}"
        self.scan_id = scan_id
        self.predicted_class = predicted_class
        self.confidence_score = round(float(confidence_score), 2)
        self.model_name = model_name
        self.model_version = model_version
        self.probabilities = probabilities or {}
        self.created_at = created_at or current_iso_timestamp()

    def validate(self) -> None:
        if not self.detection_id:
            raise ValueError("detection_id is required.")
        if not self.scan_id:
            raise ValueError("scan_id is required.")
        if self.predicted_class not in ALLOWED_CLASSES:
            raise ValueError(f"predicted_class must be one of {ALLOWED_CLASSES}")
        if not (0.0 <= self.confidence_score <= 100.0):
            raise ValueError("confidence_score must be between 0.0 and 100.0")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "detection_id": self.detection_id,
            "scan_id": self.scan_id,
            "predicted_class": self.predicted_class,
            "confidence_score": self.confidence_score,
            "model_name": self.model_name,
            "model_version": self.model_version,
            "probabilities": self.probabilities,
            "created_at": self.created_at
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DetectionResult':
        return cls(
            detection_id=data.get('detection_id'),
            scan_id=data.get('scan_id'),
            predicted_class=data.get('predicted_class'),
            confidence_score=data.get('confidence_score', 0.0),
            model_name=data.get('model_name', 'BrainSight CNN'),
            model_version=data.get('model_version', 'v4.2'),
            probabilities=data.get('probabilities', {}),
            created_at=data.get('created_at')
        )


class GradCAMResult:
    """Grad-CAM visual explainability document model."""
    def __init__(
        self,
        scan_id: str,
        heatmap_image_path: str,
        overlay_image_path: str,
        gradcam_id: Optional[str] = None,
        layer_name: str = 'top_conv_layer',
        created_at: Optional[str] = None
    ):
        self.gradcam_id = gradcam_id or f"GDC-{uuid.uuid4().hex[:8].upper()}"
        self.scan_id = scan_id
        self.heatmap_image_path = heatmap_image_path
        self.overlay_image_path = overlay_image_path
        self.layer_name = layer_name
        self.created_at = created_at or current_iso_timestamp()

    def validate(self) -> None:
        if not self.gradcam_id:
            raise ValueError("gradcam_id is required.")
        if not self.scan_id:
            raise ValueError("scan_id is required.")
        if not self.heatmap_image_path or not self.overlay_image_path:
            raise ValueError("heatmap_image_path and overlay_image_path are required.")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "gradcam_id": self.gradcam_id,
            "scan_id": self.scan_id,
            "heatmap_image_path": self.heatmap_image_path,
            "overlay_image_path": self.overlay_image_path,
            "layer_name": self.layer_name,
            "created_at": self.created_at
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'GradCAMResult':
        return cls(
            gradcam_id=data.get('gradcam_id'),
            scan_id=data.get('scan_id'),
            heatmap_image_path=data.get('heatmap_image_path'),
            overlay_image_path=data.get('overlay_image_path'),
            layer_name=data.get('layer_name', 'top_conv_layer'),
            created_at=data.get('created_at')
        )


class Report:
    """Diagnostic PDF report document model."""
    def __init__(
        self,
        scan_id: str,
        user_id: str,
        pdf_path: str,
        report_id: Optional[str] = None,
        summary: Optional[Dict[str, Any]] = None,
        generated_at: Optional[str] = None
    ):
        self.report_id = report_id or f"RPT-{uuid.uuid4().hex[:8].upper()}"
        self.scan_id = scan_id
        self.user_id = user_id
        self.pdf_path = pdf_path
        self.summary = summary or {}
        self.generated_at = generated_at or current_iso_timestamp()

    def validate(self) -> None:
        if not self.report_id:
            raise ValueError("report_id is required.")
        if not self.scan_id:
            raise ValueError("scan_id is required.")
        if not self.user_id:
            raise ValueError("user_id is required.")
        if not self.pdf_path:
            raise ValueError("pdf_path is required.")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "report_id": self.report_id,
            "scan_id": self.scan_id,
            "user_id": self.user_id,
            "pdf_path": self.pdf_path,
            "summary": self.summary,
            "generated_at": self.generated_at
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Report':
        return cls(
            report_id=data.get('report_id'),
            scan_id=data.get('scan_id'),
            user_id=data.get('user_id'),
            pdf_path=data.get('pdf_path'),
            summary=data.get('summary', {}),
            generated_at=data.get('generated_at')
        )
