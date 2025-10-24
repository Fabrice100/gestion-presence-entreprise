"""
Tests pour la sécurité avancée de PresencePro.

Ce module teste :
- Authentification à deux facteurs (2FA)
- Chiffrement des données sensibles
- Audit trail complet
- Détection d'intrusion et d'anomalies
- Gestion des sessions sécurisées

Auteur: Système de Gestion de Présence
Date: 23 octobre 2025
"""

import time
import base64
from django.test import TestCase, RequestFactory
from django.contrib.auth.models import User
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta

from common.two_factor_auth import (
    TwoFactorAuthService, SecureSessionManager,
    two_factor_service, secure_session_manager
)
from common.encryption_service import (
    EncryptionService, PasswordHashingService, SensitiveDataManager,
    encryption_service, password_hashing_service, sensitive_data_manager
)
from common.audit_trail import (
    AuditTrailService, AuditEventType, AuditSeverity,
    audit_trail_service
)
from common.intrusion_detection import (
    IntrusionDetectionService, ThreatLevel, AnomalyType,
    intrusion_detection_service
)


class TwoFactorAuthTestCase(TestCase):
    """Tests pour l'authentification à deux facteurs."""
    
    def setUp(self):
        """Configuration des tests."""
        self.two_factor = TwoFactorAuthService()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_generate_secret_key(self):
        """Test génération de clé secrète."""
        secret_key = self.two_factor.generate_secret_key(self.user)
        
        self.assertIsNotNone(secret_key)
        self.assertIsInstance(secret_key, str)
        self.assertGreater(len(secret_key), 20)
    
    def test_generate_qr_code(self):
        """Test génération de QR code."""
        secret_key = self.two_factor.generate_secret_key(self.user)
        qr_code = self.two_factor.generate_qr_code(self.user, secret_key)
        
        self.assertIsNotNone(qr_code)
        self.assertIsInstance(qr_code, str)
        # Vérification que c'est un base64 valide
        try:
            base64.b64decode(qr_code)
        except Exception:
            self.fail("QR code n'est pas un base64 valide")
    
    def test_generate_backup_codes(self):
        """Test génération de codes de sauvegarde."""
        backup_codes = self.two_factor.generate_backup_codes(self.user)
        
        self.assertIsInstance(backup_codes, list)
        self.assertEqual(len(backup_codes), 10)
        
        # Vérification que tous les codes sont uniques
        self.assertEqual(len(set(backup_codes)), len(backup_codes))
        
        # Vérification de la longueur des codes
        for code in backup_codes:
            self.assertEqual(len(code), 16)  # 8 bytes * 2 (hex)
    
    def test_verify_totp_code(self):
        """Test vérification de code TOTP."""
        secret_key = self.two_factor.generate_secret_key(self.user)
        
        # Test avec un code valide (simulation)
        with patch('pyotp.TOTP.verify') as mock_verify:
            mock_verify.return_value = True
            
            result = self.two_factor.verify_totp_code(self.user, '123456', secret_key)
            self.assertTrue(result)
            mock_verify.assert_called_once_with('123456', valid_window=1)
    
    def test_verify_backup_code(self):
        """Test vérification de code de sauvegarde."""
        backup_codes = self.two_factor.generate_backup_codes(self.user)
        test_code = backup_codes[0]
        
        # Test avec un code valide
        result = self.two_factor.verify_backup_code(self.user, test_code)
        self.assertTrue(result)
        
        # Test avec un code invalide
        result = self.two_factor.verify_backup_code(self.user, 'INVALID')
        self.assertFalse(result)
    
    def test_enable_disable_2fa(self):
        """Test activation/désactivation de la 2FA."""
        secret_key = self.two_factor.generate_secret_key(self.user)
        
        # Test activation
        result = self.two_factor.enable_2fa(self.user, secret_key)
        self.assertTrue(result)
        self.assertTrue(self.two_factor.is_2fa_enabled(self.user))
        
        # Test désactivation
        result = self.two_factor.disable_2fa(self.user)
        self.assertTrue(result)
        self.assertFalse(self.two_factor.is_2fa_enabled(self.user))


class EncryptionServiceTestCase(TestCase):
    """Tests pour le service de chiffrement."""
    
    def setUp(self):
        """Configuration des tests."""
        self.encryption = EncryptionService()
        self.password_service = PasswordHashingService()
        self.data_manager = SensitiveDataManager()
    
    def test_encrypt_decrypt_data(self):
        """Test chiffrement/déchiffrement de données."""
        test_data = "Données sensibles à chiffrer"
        
        # Chiffrement
        encrypted = self.encryption.encrypt_data(test_data)
        self.assertIsNotNone(encrypted)
        self.assertNotEqual(encrypted, test_data)
        
        # Déchiffrement
        decrypted = self.encryption.decrypt_data(encrypted)
        self.assertEqual(decrypted, test_data)
    
    def test_encrypt_decrypt_bytes(self):
        """Test chiffrement/déchiffrement de bytes."""
        test_bytes = b"Donnees binaires sensibles"
        
        # Chiffrement
        encrypted = self.encryption.encrypt_data(test_bytes)
        self.assertIsNotNone(encrypted)
        
        # Déchiffrement
        decrypted = self.encryption.decrypt_data(encrypted)
        self.assertEqual(decrypted, test_bytes.decode('utf-8'))
    
    def test_encrypt_field(self):
        """Test chiffrement de champ de base de données."""
        test_value = "Valeur de champ sensible"
        
        encrypted = self.encryption.encrypt_field(test_value)
        self.assertIsNotNone(encrypted)
        
        decrypted = self.encryption.decrypt_field(encrypted)
        self.assertEqual(decrypted, test_value)
    
    def test_encrypt_field_none(self):
        """Test chiffrement de champ None."""
        encrypted = self.encryption.encrypt_field(None)
        self.assertIsNone(encrypted)
        
        decrypted = self.encryption.decrypt_field(None)
        self.assertIsNone(decrypted)
    
    def test_password_hashing(self):
        """Test hachage de mot de passe."""
        password = "MotDePasseSecurise123!"
        
        # Hachage
        hash_result = self.password_service.hash_password(password)
        
        self.assertIn('hash', hash_result)
        self.assertIn('salt', hash_result)
        self.assertIn('algorithm', hash_result)
        self.assertIn('iterations', hash_result)
        
        # Vérification
        is_valid = self.password_service.verify_password(
            password, hash_result['hash'], hash_result['salt']
        )
        self.assertTrue(is_valid)
        
        # Test avec mauvais mot de passe
        is_invalid = self.password_service.verify_password(
            "MauvaisMotDePasse", hash_result['hash'], hash_result['salt']
        )
        self.assertFalse(is_invalid)
    
    def test_create_secure_token(self):
        """Test création de token sécurisé."""
        token = self.data_manager.create_secure_token()
        
        self.assertIsNotNone(token)
        self.assertIsInstance(token, str)
        self.assertGreater(len(token), 20)
    
    def test_create_secure_id(self):
        """Test création d'ID sécurisé."""
        secure_id = self.data_manager.create_secure_id("TEST_")
        
        self.assertIsNotNone(secure_id)
        self.assertTrue(secure_id.startswith("TEST_"))
        self.assertGreater(len(secure_id), 20)


class AuditTrailTestCase(TestCase):
    """Tests pour l'audit trail."""
    
    def setUp(self):
        """Configuration des tests."""
        self.audit_service = AuditTrailService()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_log_event(self):
        """Test enregistrement d'événement d'audit."""
        details = {
            'action': 'test_action',
            'resource': 'test_resource',
            'metadata': {'key': 'value'}
        }
        
        event_id = self.audit_service.log_event(
            event_type=AuditEventType.LOGIN_SUCCESS,
            user=self.user,
            details=details,
            severity=AuditSeverity.MEDIUM,
            ip_address='192.168.1.1'
        )
        
        self.assertIsNotNone(event_id)
        self.assertIsInstance(event_id, str)
    
    def test_log_authentication_event(self):
        """Test enregistrement d'événement d'authentification."""
        details = {
            'login_method': 'password',
            'success': True
        }
        
        event_id = self.audit_service.log_authentication_event(
            event_type=AuditEventType.LOGIN_SUCCESS,
            user=self.user,
            success=True,
            details=details,
            ip_address='192.168.1.1'
        )
        
        self.assertIsNotNone(event_id)
    
    def test_log_data_access_event(self):
        """Test enregistrement d'événement d'accès aux données."""
        details = {
            'operation': 'read',
            'record_count': 10
        }
        
        event_id = self.audit_service.log_data_access_event(
            event_type=AuditEventType.DATA_CREATE,
            user=self.user,
            model_name='TestModel',
            object_id='123',
            details=details,
            ip_address='192.168.1.1'
        )
        
        self.assertIsNotNone(event_id)
    
    def test_log_security_event(self):
        """Test enregistrement d'événement de sécurité."""
        details = {
            'threat_type': 'brute_force',
            'attempt_count': 5
        }
        
        event_id = self.audit_service.log_security_event(
            event_type=AuditEventType.SUSPICIOUS_ACTIVITY,
            user=self.user,
            details=details,
            severity=AuditSeverity.HIGH,
            ip_address='192.168.1.1'
        )
        
        self.assertIsNotNone(event_id)
    
    def test_get_audit_events(self):
        """Test récupération des événements d'audit."""
        events = self.audit_service.get_audit_events(
            user=self.user,
            limit=10
        )
        
        self.assertIsInstance(events, list)
    
    def test_generate_audit_report(self):
        """Test génération de rapport d'audit."""
        start_date = "2024-01-01"
        end_date = "2024-01-31"
        
        report = self.audit_service.generate_audit_report(
            start_date=start_date,
            end_date=end_date,
            report_type='summary'
        )
        
        self.assertIsInstance(report, dict)
        self.assertIn('period', report)
        self.assertIn('total_events', report)


class IntrusionDetectionTestCase(TestCase):
    """Tests pour la détection d'intrusion."""
    
    def setUp(self):
        """Configuration des tests."""
        self.intrusion_service = IntrusionDetectionService()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_analyze_login_attempt_success(self):
        """Test analyse de tentative de connexion réussie."""
        result = self.intrusion_service.analyze_login_attempt(
            username='testuser',
            ip_address='192.168.1.1',
            success=True,
            user_agent='Mozilla/5.0'
        )
        
        self.assertIsInstance(result, dict)
        self.assertIn('anomalies_detected', result)
        self.assertIn('threat_level', result)
        self.assertIn('action_required', result)
        self.assertIsInstance(result['anomalies_detected'], list)
    
    def test_analyze_login_attempt_failure(self):
        """Test analyse de tentative de connexion échouée."""
        result = self.intrusion_service.analyze_login_attempt(
            username='testuser',
            ip_address='192.168.1.1',
            success=False,
            user_agent='Mozilla/5.0'
        )
        
        self.assertIsInstance(result, dict)
        self.assertIn('anomalies_detected', result)
        self.assertIn('threat_level', result)
        self.assertIn('action_required', result)
    
    def test_analyze_data_access(self):
        """Test analyse d'accès aux données."""
        result = self.intrusion_service.analyze_data_access(
            user=self.user,
            model_name='TestModel',
            object_count=50,
            ip_address='192.168.1.1'
        )
        
        self.assertIsInstance(result, dict)
        self.assertIn('anomalies_detected', result)
        self.assertIn('threat_level', result)
        self.assertIn('action_required', result)
    
    def test_analyze_request_pattern(self):
        """Test analyse de pattern de requêtes."""
        result = self.intrusion_service.analyze_request_pattern(
            ip_address='192.168.1.1',
            endpoint='/test/',
            user=self.user
        )
        
        self.assertIsInstance(result, dict)
        self.assertIn('anomalies_detected', result)
        self.assertIn('threat_level', result)
        self.assertIn('action_required', result)
    
    def test_detect_brute_force(self):
        """Test détection de force brute."""
        username = 'testuser'
        ip_address = '192.168.1.1'
        
        # Simulation de plusieurs tentatives
        for i in range(3):
            result = self.intrusion_service._detect_brute_force(username, ip_address)
            self.assertIsInstance(result, dict)
            self.assertIn('detected', result)
            self.assertIn('attempt_count', result)
    
    def test_detect_unusual_login_time(self):
        """Test détection d'heure de connexion inhabituelle."""
        result = self.intrusion_service._detect_unusual_login_time()
        
        self.assertIsInstance(result, dict)
        self.assertIn('detected', result)
    
    def test_detect_suspicious_pattern(self):
        """Test détection de pattern suspect."""
        result = self.intrusion_service._detect_suspicious_pattern(
            username='testuser',
            ip_address='192.168.1.1',
            user_agent='bot'
        )
        
        self.assertIsInstance(result, dict)
        self.assertIn('detected', result)


class SecureSessionManagerTestCase(TestCase):
    """Tests pour le gestionnaire de sessions sécurisées."""
    
    def setUp(self):
        """Configuration des tests."""
        self.session_manager = SecureSessionManager()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.factory = RequestFactory()
    
    def test_create_secure_session(self):
        """Test création de session sécurisée."""
        request = self.factory.get('/test/')
        request.META['REMOTE_ADDR'] = '192.168.1.1'
        request.META['HTTP_USER_AGENT'] = 'Mozilla/5.0'
        
        session_token = self.session_manager.create_secure_session(self.user, request)
        
        self.assertIsNotNone(session_token)
        self.assertIsInstance(session_token, str)
        self.assertGreater(len(session_token), 20)
    
    def test_verify_session(self):
        """Test vérification de session."""
        request = self.factory.get('/test/')
        request.META['REMOTE_ADDR'] = '192.168.1.1'
        request.META['HTTP_USER_AGENT'] = 'Mozilla/5.0'
        
        # Création de session
        session_token = self.session_manager.create_secure_session(self.user, request)
        
        # Vérification de session
        session_data = self.session_manager.verify_session(session_token, request)
        
        self.assertIsNotNone(session_data)
        self.assertIn('user_id', session_data)
        self.assertEqual(session_data['user_id'], self.user.id)
    
    def test_invalidate_session(self):
        """Test invalidation de session."""
        request = self.factory.get('/test/')
        request.META['REMOTE_ADDR'] = '192.168.1.1'
        
        # Création de session
        session_token = self.session_manager.create_secure_session(self.user, request)
        
        # Invalidation de session
        result = self.session_manager.invalidate_session(session_token)
        self.assertTrue(result)
        
        # Vérification que la session est invalidée
        session_data = self.session_manager.verify_session(session_token, request)
        self.assertIsNone(session_data)


class SecurityIntegrationTestCase(TestCase):
    """Tests d'intégration pour la sécurité."""
    
    def setUp(self):
        """Configuration des tests."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_security_workflow_integration(self):
        """Test intégration du workflow de sécurité."""
        # Test du workflow complet de sécurité
        # 1. Chiffrement de données sensibles
        sensitive_data = "Données sensibles"
        encrypted = encryption_service.encrypt_data(sensitive_data)
        decrypted = encryption_service.decrypt_data(encrypted)
        self.assertEqual(decrypted, sensitive_data)
        
        # 2. Audit trail
        event_id = audit_trail_service.log_event(
            event_type=AuditEventType.LOGIN_SUCCESS,
            user=self.user,
            details={'test': 'integration'},
            severity=AuditSeverity.MEDIUM
        )
        self.assertIsNotNone(event_id)
        
        # 3. Détection d'intrusion
        result = intrusion_detection_service.analyze_login_attempt(
            username='testuser',
            ip_address='192.168.1.1',
            success=True
        )
        self.assertIsInstance(result, dict)
    
    def test_security_services_availability(self):
        """Test disponibilité des services de sécurité."""
        # Vérification que tous les services sont disponibles
        self.assertIsNotNone(two_factor_service)
        self.assertIsNotNone(encryption_service)
        self.assertIsNotNone(password_hashing_service)
        self.assertIsNotNone(sensitive_data_manager)
        self.assertIsNotNone(audit_trail_service)
        self.assertIsNotNone(intrusion_detection_service)
        self.assertIsNotNone(secure_session_manager)
    
    def test_security_configuration(self):
        """Test configuration de sécurité."""
        # Vérification des configurations de détection d'intrusion
        config = intrusion_detection_service.config
        
        self.assertIn('brute_force', config)
        self.assertIn('rapid_requests', config)
        self.assertIn('unusual_login', config)
        self.assertIn('data_access', config)
        
        # Vérification des seuils
        self.assertGreater(config['brute_force']['max_attempts'], 0)
        self.assertGreater(config['rapid_requests']['max_requests'], 0)
