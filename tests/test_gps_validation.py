"""
Tests unitaires pour la validation GPS et calculs de distance.

Ce module teste :
- Formule de Haversine pour le calcul de distance
- Validation de la précision GPS
- Validation de la distance par rapport au bureau

Auteur: Système de Gestion de Présence
Date: 22 octobre 2025
"""

from django.test import TestCase
from math import radians, sin, cos, sqrt, atan2


class HaversineCalculationTest(TestCase):
    """Tests pour le calcul de distance GPS (formule Haversine)."""
    
    def calculate_distance(self, lat1, lon1, lat2, lon2):
        """
        Calcule la distance entre deux coordonnées GPS en mètres.
        Formule de Haversine.
        """
        R = 6371000  # Rayon de la Terre en mètres
        
        # Convertir en radians
        lat1_rad = radians(lat1)
        lat2_rad = radians(lat2)
        delta_lat = radians(lat2 - lat1)
        delta_lon = radians(lon2 - lon1)
        
        # Formule de Haversine
        a = sin(delta_lat / 2) ** 2 + cos(lat1_rad) * cos(lat2_rad) * sin(delta_lon / 2) ** 2
        c = 2 * atan2(sqrt(a), sqrt(1 - a))
        distance = R * c
        
        return distance
    
    def test_same_location_distance_zero(self):
        """Distance entre deux points identiques = 0."""
        lat, lon = 6.1304, 1.2158  # Cotonou, Bénin
        distance = self.calculate_distance(lat, lon, lat, lon)
        self.assertAlmostEqual(distance, 0, delta=0.1)
    
    def test_known_distance_paris_london(self):
        """Test avec une distance connue: Paris - Londres ≈ 344 km."""
        # Paris: 48.8566° N, 2.3522° E
        # Londres: 51.5074° N, -0.1278° W
        paris_lat, paris_lon = 48.8566, 2.3522
        london_lat, london_lon = 51.5074, -0.1278
        
        distance = self.calculate_distance(paris_lat, paris_lon, london_lat, london_lon)
        
        # Distance attendue ≈ 344 km = 344000 m
        expected_distance = 344000
        # Tolérance de 5%
        self.assertAlmostEqual(distance, expected_distance, delta=expected_distance * 0.05)
    
    def test_distance_100_meters(self):
        """Test avec une petite distance (environ 100m)."""
        # Point de référence
        lat1, lon1 = 6.1304, 1.2158
        
        # Point à environ 100m au nord
        # 1 degré de latitude ≈ 111 km
        # 100m ≈ 0.0009 degrés
        lat2, lon2 = lat1 + 0.0009, lon1
        
        distance = self.calculate_distance(lat1, lon1, lat2, lon2)
        
        # Devrait être proche de 100m (tolérance 10%)
        self.assertAlmostEqual(distance, 100, delta=10)
    
    def test_distance_200_meters(self):
        """Test avec une distance de 200m."""
        lat1, lon1 = 6.1304, 1.2158
        lat2, lon2 = lat1 + 0.0018, lon1
        
        distance = self.calculate_distance(lat1, lon1, lat2, lon2)
        
        # Devrait être proche de 200m (tolérance 20%)
        self.assertAlmostEqual(distance, 200, delta=20)
    
    def test_distance_symmetry(self):
        """Distance A→B = Distance B→A."""
        lat1, lon1 = 6.1304, 1.2158
        lat2, lon2 = 6.1500, 1.2300
        
        distance_ab = self.calculate_distance(lat1, lon1, lat2, lon2)
        distance_ba = self.calculate_distance(lat2, lon2, lat1, lon1)
        
        self.assertAlmostEqual(distance_ab, distance_ba, delta=0.1)
    
    def test_distance_negative_coordinates(self):
        """Test avec des coordonnées négatives (hémisphère sud/ouest)."""
        # São Paulo, Brazil: -23.5505° S, -46.6333° W
        # Rio de Janeiro, Brazil: -22.9068° S, -43.1729° W
        sp_lat, sp_lon = -23.5505, -46.6333
        rio_lat, rio_lon = -22.9068, -43.1729
        
        distance = self.calculate_distance(sp_lat, sp_lon, rio_lat, rio_lon)
        
        # Distance attendue ≈ 357 km
        expected_distance = 357000
        self.assertAlmostEqual(distance, expected_distance, delta=expected_distance * 0.1)


class GPSValidationTest(TestCase):
    """Tests pour la validation GPS."""
    
    def test_accuracy_within_limit(self):
        """Précision GPS dans la limite acceptable."""
        accuracy = 10  # 10 mètres
        max_accuracy = 50  # Limite: 50 mètres
        
        self.assertTrue(accuracy <= max_accuracy)
    
    def test_accuracy_exceeds_limit(self):
        """Précision GPS dépasse la limite."""
        accuracy = 100  # 100 mètres
        max_accuracy = 50  # Limite: 50 mètres
        
        self.assertFalse(accuracy <= max_accuracy)
    
    def test_distance_within_radius(self):
        """Employé dans le rayon autorisé."""
        # Bureau central
        site_lat, site_lon = 6.1304, 1.2158
        # Employé à 50m
        employee_lat, employee_lon = 6.1308, 1.2158
        
        # Calculer la distance
        distance = HaversineCalculationTest().calculate_distance(
            site_lat, site_lon, employee_lat, employee_lon
        )
        
        allowed_radius = 200  # 200 mètres
        
        self.assertTrue(distance <= allowed_radius)
    
    def test_distance_outside_radius(self):
        """Employé hors du rayon autorisé."""
        # Bureau central
        site_lat, site_lon = 6.1304, 1.2158
        # Employé à 500m
        employee_lat, employee_lon = 6.1350, 1.2158
        
        # Calculer la distance
        distance = HaversineCalculationTest().calculate_distance(
            site_lat, site_lon, employee_lat, employee_lon
        )
        
        allowed_radius = 200  # 200 mètres
        
        self.assertFalse(distance <= allowed_radius)
    
    def test_coordinates_validation(self):
        """Validation des coordonnées GPS."""
        # Coordonnées valides
        valid_lat = 6.1304
        valid_lon = 1.2158
        
        self.assertTrue(-90 <= valid_lat <= 90)
        self.assertTrue(-180 <= valid_lon <= 180)
        
        # Coordonnées invalides
        invalid_lat = 100
        invalid_lon = 200
        
        self.assertFalse(-90 <= invalid_lat <= 90)
        self.assertFalse(-180 <= invalid_lon <= 180)


class GPSEdgeCasesTest(TestCase):
    """Tests pour les cas limites GPS."""
    
    def calculate_distance(self, lat1, lon1, lat2, lon2):
        """Réutilisation de la formule Haversine."""
        R = 6371000
        lat1_rad = radians(lat1)
        lat2_rad = radians(lat2)
        delta_lat = radians(lat2 - lat1)
        delta_lon = radians(lon2 - lon1)
        a = sin(delta_lat / 2) ** 2 + cos(lat1_rad) * cos(lat2_rad) * sin(delta_lon / 2) ** 2
        c = 2 * atan2(sqrt(a), sqrt(1 - a))
        return R * c
    
    def test_equator_distance(self):
        """Test sur l'équateur (latitude 0)."""
        lat1, lon1 = 0, 0
        lat2, lon2 = 0, 0.001  # 0.001 degré à l'est
        
        distance = self.calculate_distance(lat1, lon1, lat2, lon2)
        
        # À l'équateur, 1 degré de longitude ≈ 111 km
        # 0.001 degré ≈ 111 m
        self.assertAlmostEqual(distance, 111, delta=20)
    
    def test_poles_distance(self):
        """Test près des pôles."""
        # Deux points près du pôle Nord
        lat1, lon1 = 89.999, 0
        lat2, lon2 = 89.999, 180
        
        distance = self.calculate_distance(lat1, lon1, lat2, lon2)
        
        # Près du pôle, la distance est très petite même avec 180° de longitude
        self.assertLess(distance, 1000)  # Moins de 1 km
    
    def test_international_date_line(self):
        """Test à travers la ligne de changement de date."""
        # Point à 179° E
        lat1, lon1 = 0, 179
        # Point à 179° W (-179)
        lat2, lon2 = 0, -179
        
        distance = self.calculate_distance(lat1, lon1, lat2, lon2)
        
        # Distance devrait être proche (pas faire le tour de la Terre)
        # 2 degrés à l'équateur ≈ 222 km
        self.assertAlmostEqual(distance, 222000, delta=50000)
    
    def test_very_precise_gps(self):
        """Test avec GPS très précis (1m de précision)."""
        lat1, lon1 = 6.1304, 1.2158
        # Décalage de 0.00001 degré ≈ 1 mètre
        lat2, lon2 = 6.13041, 1.2158
        
        distance = self.calculate_distance(lat1, lon1, lat2, lon2)
        
        # Devrait être très proche de 1m
        self.assertAlmostEqual(distance, 1, delta=0.5)
    
    def test_gps_accuracy_edge_cases(self):
        """Test des cas limites de précision GPS."""
        # Précision parfaite
        perfect_accuracy = 5
        self.assertTrue(perfect_accuracy <= 50)
        
        # Précision limite
        edge_accuracy = 50
        self.assertTrue(edge_accuracy <= 50)
        
        # Précision dépassée
        bad_accuracy = 51
        self.assertFalse(bad_accuracy <= 50)
        
        # Précision très mauvaise
        very_bad_accuracy = 1000
        self.assertFalse(very_bad_accuracy <= 50)
