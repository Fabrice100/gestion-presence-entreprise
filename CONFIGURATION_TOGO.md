# Configuration Togo - Système de Gestion de Présence

## 📋 Vue d'ensemble

Ce système est **pré-configuré pour les PME togolaises** avec :
- 4 types de congés conformes au Code du Travail togolais
- 10 jours fériés nationaux et religieux (année 2025)
- Attribution automatique de 24 jours de congés payés par employé

---

## 🇹🇬 Types de congés inclus

### 1. Congés payés (CP)
- **Allocation** : 24 jours par an
- **Conformité** : Code du Travail togolais
- **Rémunéré** : Oui
- **Justification** : Non requise
- **Préavis** : 30 jours

### 2. Congé maladie (MAL)
- **Allocation** : 180 jours maximum
- **Type** : Sur demande
- **Rémunéré** : Oui
- **Certificat médical** : Obligatoire
- **Préavis** : Aucun (urgence)

### 3. Événements familiaux (EVT)
- **Allocation** : 15 jours maximum
- **Type** : Sur demande
- **Rémunéré** : Oui
- **Justification** : Requise (acte de mariage, naissance, décès, etc.)
- **Préavis** : 3 jours
- **Exemples** : Mariage, naissance, décès d'un proche

### 4. Congé sans solde (CSS)
- **Allocation** : 0 jours (sur accord)
- **Type** : Sur demande
- **Rémunéré** : Non
- **Justification** : Requise
- **Préavis** : 15 jours
- **Maximum consécutif** : 90 jours

---

## 🗓️ Jours fériés 2025 (10 jours)

### Jours fériés nationaux (récurrents)
1. **1er janvier** - Nouvel An
2. **27 avril** - Fête de l'Indépendance
3. **1er mai** - Fête du Travail
4. **21 juin** - Fête des Martyrs

### Jours fériés religieux (récurrents)
5. **15 août** - Assomption
6. **1er novembre** - Toussaint
7. **25 décembre** - Noël

### Jours fériés religieux 2025 (dates mobiles)
8. **21 avril 2025** - Lundi de Pâques
9. **29 mai 2025** - Ascension
10. **9 juin 2025** - Lundi de Pentecôte

### ⚠️ Note importante
**Les fêtes musulmanes** (Aïd el-Fitr, Aïd el-Adha/Tabaski) suivent le calendrier lunaire.  
➡️ Elles doivent être **ajoutées manuellement chaque année** via l'interface RH ou Django Admin.

---

## 🚀 Installation et utilisation

### Installation initiale

Pour une nouvelle installation :

```bash
python manage.py migrate
python manage.py init_togo_setup
```

Cette commande :
1. Charge les 4 types de congés
2. Charge les 10 jours fériés 2025
3. Crée automatiquement 24 jours de congés payés pour tous les employés existants

### Pour un nouvel employé

**Aucune action requise !** 🎉  
Lorsque le RH/DG crée un nouvel employé :
- Un signal Django se déclenche automatiquement
- 24 jours de congés payés sont créés pour l'année en cours

---

## 🔄 Gestion annuelle

### Mise à jour pour une nouvelle année

1. **Créer les jours fériés de la nouvelle année** :
   - Dupliquer `leave/fixtures/togo_holidays_2025.json`
   - Renommer en `togo_holidays_2026.json`
   - Mettre à jour les dates mobiles (Pâques, Ascension, Pentecôte)
   - Ajouter les dates des fêtes musulmanes

2. **Charger les nouveaux jours fériés** :
   ```bash
   python manage.py loaddata togo_holidays_2026.json
   ```

3. **Attribution des nouveaux soldes** :
   - Via Django Admin ou interface RH
   - Ou créer une commande management pour automatiser

### Ajout manuel de jours fériés

**Via Django Admin** :
1. Aller sur `/admin/leave/holiday/`
2. Cliquer "Ajouter un jour férié"
3. Remplir les champs :
   - Nom : Ex. "Aïd el-Fitr 2026"
   - Date : Date exacte
   - Type : "Fête religieuse"
   - Récurrent : Non (date variable)
   - Actif : Oui

---

## 📊 Avantages pour votre soutenance

### Différenciation vs systèmes génériques (OrangeHRM, BambooHRM)

| Critère | Systèmes génériques | Votre système |
|---------|---------------------|---------------|
| Configuration initiale | 2-3 heures | **5 minutes** ✅ |
| Adaptation locale | Manuelle | **Pré-configurée** ✅ |
| Types de congés | À créer | **4 types inclus** ✅ |
| Jours fériés | À saisir | **10 jours inclus** ✅ |
| Soldes employés | À initialiser | **Automatique** ✅ |
| Langue | Souvent anglais | **Français** ✅ |

### Arguments pour le jury

> "J'ai développé un système **adapté au contexte togolais**, contrairement aux solutions génériques :
> - ✅ Pré-configuré avec la législation togolaise (24 jours de congés payés)
> - ✅ Jours fériés nationaux et religieux intégrés
> - ✅ Allocation automatique des soldes
> - ✅ Une PME togolaise peut **démarrer en 5 minutes** sans formation
> - ✅ Pas de configuration complexe requise"

---

## 🛠️ Fichiers créés

### Fixtures (données initiales)
- `leave/fixtures/togo_leave_types.json` : 4 types de congés
- `leave/fixtures/togo_holidays_2025.json` : 10 jours fériés 2025

### Signals (automatisation)
- `leave/signals.py` : Auto-création soldes pour nouveaux employés
- `leave/apps.py` : Enregistrement du signal

### Commande management
- `leave/management/commands/init_togo_setup.py` : Initialisation complète

---

## 📞 Support et personnalisation

### Personnalisation pour une entreprise spécifique

Si une entreprise togolaise a des besoins spécifiques :

1. **Jours de l'entreprise** : Ajouter via Django Admin (type "Jour de l'entreprise")
2. **Types de congés supplémentaires** : Créer via interface RH
3. **Nombre de jours différent** : Modifier l'allocation dans le type de congé

### Extensibilité

Le système reste **100% extensible** :
- ✅ Nouveaux types de congés
- ✅ Jours fériés régionaux
- ✅ Règles métier spécifiques
- ✅ Bonification d'ancienneté (à implémenter si besoin)

---

## 📝 Licence et auteur

**Projet** : Système de Gestion de Présence en Entreprise  
**Contexte** : Projet de fin de cycle - Licence en Architecture Logicielle  
**Cible** : PME togolaises  
**Version** : 1.0  
**Date** : 2025

---

**✅ Votre système est maintenant prêt à l'emploi pour les PME togolaises !**


