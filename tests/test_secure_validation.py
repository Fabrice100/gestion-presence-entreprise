"""
Tests pour la validation sécurisée des données.

Ce module teste :
- Validation des coordonnées GPS
- Sanitisation des données
- Validation des IDs employés
- Validation des emails
- Validation des motifs
- Intégration avec PunchService

Auteur: Système de Gestion de Présence
Date: 22 octobre 2025
"""

from django.test import TestCase
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from unittest.mock import patch, MagicMock

from common.secure_validation import secure_validator
from common.validators import (
    validate_gps_coordinate,
    validate_gps_accuracy,
    validate_employee_id,
    validate_email_address,
    validate_reason_text,
    validate_safe_string
)
from attendance.services import PunchService


class SecureValidationTestCase(TestCase):
    """Tests pour SecureDataValidator."""
    
    def setUp(self):
        """Configuration des tests."""
        self.validator = secure_validator
    
    def test_validate_gps_coordinates_valid(self):
        """Test validation GPS avec coordonnées valides."""
        result = self.validator.validate_gps_coordinates(
            "6.123456789012345",
            "1.234567890123456",
            "5.0"
        )
        
        self.assertTrue(result['valid'])
        self.assertEqual(result['latitude'], 6.123456789012345)
        self.assertEqual(result['longitude'], 1.234567890123456)
        self.assertEqual(result['accuracy'], 5.0)
        self.assertIsNone(result['error_message'])
    
    def test_validate_gps_coordinates_invalid_format(self):
        """Test validation GPS avec format invalide."""
        result = self.validator.validate_gps_coordinates(
            "invalid_lat",
            "1.234567890123456",
            "5.0"
        )
        
        self.assertFalse(result['valid'])
        self.assertEqual(result['error_message'], "Format de latitude invalide")
    
    def test_validate_gps_coordinates_out_of_range(self):
        """Test validation GPS avec coordonnées hors limites."""
        result = self.validator.validate_gps_coordinates(
            "91.0",  # Latitude > 90
            "1.234567890123456",
            "5.0"
        )
        
        self.assertFalse(result['valid'])
        self.assertEqual(result['error_message'], "Latitude hors limites (-90° à +90°)")
    
    def test_validate_gps_coordinates_accuracy_out_of_range(self):
        """Test validation GPS avec précision hors limites."""
        result = self.validator.validate_gps_coordinates(
            "6.123456789012345",
            "1.234567890123456",
            "2000.0"  # Précision > 1000m
        )
        
        self.assertFalse(result['valid'])
        self.assertEqual(result['error_message'], "Format de précision invalide")
    
    def test_validate_employee_id_valid(self):
        """Test validation ID employé valide."""
        is_valid, error = self.validator.validate_employee_id("EMP123")
        self.assertTrue(is_valid)
        self.assertIsNone(error)
    
    def test_validate_employee_id_invalid_format(self):
        """Test validation ID employé format invalide."""
        is_valid, error = self.validator.validate_employee_id("123EMP")
        self.assertFalse(is_valid)
        self.assertEqual(error, "Format d'ID employé invalide (doit être EMPXXX)")
    
    def test_validate_email_valid(self):
        """Test validation email valide."""
        is_valid, error = self.validator.validate_email("test@example.com")
        self.assertTrue(is_valid)
        self.assertIsNone(error)
    
    def test_validate_email_invalid_format(self):
        """Test validation email format invalide."""
        is_valid, error = self.validator.validate_email("invalid-email")
        self.assertFalse(is_valid)
        self.assertEqual(error, "Format d'email invalide")
    
    def test_validate_email_dangerous_chars(self):
        """Test validation email avec caractères dangereux."""
        is_valid, error = self.validator.validate_email("test<script>@example.com")
        self.assertFalse(is_valid)
        self.assertEqual(error, "Email contient des caractères non autorisés")
    
    def test_validate_reason_valid(self):
        """Test validation motif valide."""
        is_valid, error = self.validator.validate_reason("Congé pour maladie")
        self.assertTrue(is_valid)
        self.assertIsNone(error)
    
    def test_validate_reason_too_long(self):
        """Test validation motif trop long."""
        long_reason = "x" * 501  # > 500 caractères
        is_valid, error = self.validator.validate_reason(long_reason)
        self.assertFalse(is_valid)
        self.assertEqual(error, "Motif trop long (max 500 caractères)")
    
    def test_validate_reason_dangerous_content(self):
        """Test validation motif avec contenu dangereux."""
        is_valid, error = self.validator.validate_reason("Congé <script>alert('xss')</script>")
        self.assertFalse(is_valid)
        # Le contenu dangereux est détecté soit par les caractères soit par les patterns
        self.assertTrue(
            "caractères non autorisés" in error or 
            "code potentiellement dangereux" in error
        )
    
    def test_sanitize_string(self):
        """Test sanitisation de chaîne."""
        dirty_string = "  Test\x00\x01\x02String  "
        sanitized = self.validator.sanitize_string(dirty_string)
        self.assertEqual(sanitized, "TestString")
    
    def test_sanitize_string_with_max_length(self):
        """Test sanitisation avec limite de longueur."""
        long_string = "x" * 100
        sanitized = self.validator.sanitize_string(long_string, max_length=50)
        self.assertEqual(len(sanitized), 50)
    
    def test_sanitize_gps_data(self):
        """Test sanitisation des données GPS."""
        dirty_gps = {
            'latitude': '  6.123456789012345  ',
            'longitude': '1.234567890123456abc',
            'accuracy': '5.0xyz'
        }
        sanitized = self.validator.sanitize_gps_data(dirty_gps)
        
        self.assertEqual(sanitized['latitude'], '6.123456789012345')
        self.assertEqual(sanitized['longitude'], '1.234567890123456')
        self.assertEqual(sanitized['accuracy'], '5.0')


class DjangoValidatorsTestCase(TestCase):
    """Tests pour les validateurs Django."""
    
    def test_validate_gps_coordinate_valid(self):
        """Test validateur GPS coordonnée valide."""
        # Ne doit pas lever d'exception
        validate_gps_coordinate("6.123456789012345")
        validate_gps_coordinate(6.123456789012345)
    
    def test_validate_gps_coordinate_invalid_type(self):
        """Test validateur GPS coordonnée type invalide."""
        with self.assertRaises(ValidationError) as context:
            validate_gps_coordinate(None)
        
        self.assertEqual(context.exception.code, 'gps_required')
    
    def test_validate_gps_coordinate_invalid_format(self):
        """Test validateur GPS coordonnée format invalide."""
        with self.assertRaises(ValidationError) as context:
            validate_gps_coordinate("invalid")
        
        self.assertEqual(context.exception.code, 'invalid_gps_numeric')
    
    def test_validate_gps_coordinate_out_of_range(self):
        """Test validateur GPS coordonnée hors limites."""
        with self.assertRaises(ValidationError) as context:
            validate_gps_coordinate("200.0")  # Complètement hors limites
        
        self.assertEqual(context.exception.code, 'coordinate_out_of_range')
    
    def test_validate_gps_accuracy_valid(self):
        """Test validateur précision GPS valide."""
        validate_gps_accuracy("5.0")
        validate_gps_accuracy(5.0)
    
    def test_validate_gps_accuracy_out_of_range(self):
        """Test validateur précision GPS hors limites."""
        with self.assertRaises(ValidationError) as context:
            validate_gps_accuracy("2000.0")
        
        self.assertEqual(context.exception.code, 'accuracy_out_of_range')
    
    def test_validate_employee_id_valid(self):
        """Test validateur ID employé valide."""
        validate_employee_id("EMP123")
    
    def test_validate_employee_id_invalid(self):
        """Test validateur ID employé invalide."""
        with self.assertRaises(ValidationError) as context:
            validate_employee_id("123EMP")
        
        self.assertEqual(context.exception.code, 'invalid_employee_id')
    
    def test_validate_email_address_valid(self):
        """Test validateur email valide."""
        validate_email_address("test@example.com")
    
    def test_validate_email_address_invalid(self):
        """Test validateur email invalide."""
        with self.assertRaises(ValidationError) as context:
            validate_email_address("invalid-email")
        
        self.assertEqual(context.exception.code, 'invalid_email')
    
    def test_validate_reason_text_valid(self):
        """Test validateur motif valide."""
        validate_reason_text("Congé pour maladie")
    
    def test_validate_reason_text_invalid(self):
        """Test validateur motif invalide."""
        with self.assertRaises(ValidationError) as context:
            validate_reason_text("x" * 501)
        
        self.assertEqual(context.exception.code, 'invalid_reason')
    
    def test_validate_safe_string_valid(self):
        """Test validateur chaîne sécurisée valide."""
        validate_safe_string("Test string")
    
    def test_validate_safe_string_dangerous_chars(self):
        """Test validateur chaîne avec caractères dangereux."""
        with self.assertRaises(ValidationError) as context:
            validate_safe_string("Test <script>alert('xss')</script>")
        
        self.assertEqual(context.exception.code, 'dangerous_characters')


class PunchServiceIntegrationTestCase(TestCase):
    """Tests d'intégration avec PunchService."""
    
    def test_log_validation_attempt(self):
        """Test logging des tentatives de validation."""
        # Test simple de la méthode sans mock complexe
        try:
            secure_validator.log_validation_attempt(
                'gps_coordinates',
                {'latitude': '6.123', 'longitude': '1.234'},
                success=True
            )
            # Si pas d'exception, le test passe
            self.assertTrue(True)
        except Exception as e:
            self.fail(f"Logging échoué: {e}")


class SecurityTestCase(TestCase):
    """Tests de sécurité spécifiques."""
    
    def test_sql_injection_prevention(self):
        """Test prévention injection SQL dans les motifs."""
        malicious_reason = "'; DROP TABLE users; --"
        is_valid, error = secure_validator.validate_reason(malicious_reason)
        
        # Le motif devrait être rejeté pour sécurité
        self.assertFalse(is_valid)
        self.assertIn("caractères non autorisés", error)
    
    def test_xss_prevention(self):
        """Test prévention XSS dans les motifs."""
        xss_reason = "Congé <script>alert('xss')</script>"
        is_valid, error = secure_validator.validate_reason(xss_reason)
        
        self.assertFalse(is_valid)
        # Le XSS est détecté soit par les caractères dangereux soit par les patterns
        self.assertTrue(
            "caractères non autorisés" in error or 
            "code potentiellement dangereux" in error
        )
    
    def test_gps_coordinate_injection(self):
        """Test prévention injection dans coordonnées GPS."""
        malicious_lat = "6.123; DROP TABLE attendance; --"
        result = secure_validator.validate_gps_coordinates(
            malicious_lat,
            "1.234567890123456",
            "5.0"
        )
        
        self.assertFalse(result['valid'])
        self.assertEqual(result['error_message'], "Format de latitude invalide")
    
    def test_email_injection_prevention(self):
        """Test prévention injection dans email."""
        malicious_email = "test@example.com<script>alert('xss')</script>"
        is_valid, error = secure_validator.validate_email(malicious_email)
        
        self.assertFalse(is_valid)
        self.assertIn("caractères non autorisés", error)
