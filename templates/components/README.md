# 🧩 Composants Réutilisables

Ce dossier contient des composants UI réutilisables pour éviter la duplication de code.

## 📦 Composants disponibles

### 1. `stat_card.html` - Carte Statistique
Affiche une statistique avec icône, titre, valeur et badge optionnel.

**Paramètres:**
- `icon` (requis) - Classe Bootstrap Icons (ex: `bi-calendar`)
- `title` (requis) - Titre de la statistique
- `value` (requis) - Valeur à afficher en gros
- `subtitle` (optionnel) - Texte sous la valeur
- `color` (optionnel, défaut: `blue`) - Couleur du thème
- `badge` (optionnel) - Badge à afficher en haut à droite
- `trend` (optionnel) - `up` ou `down` pour flèche de tendance
- `link_url` (optionnel) - URL du lien "Voir détails"
- `link_text` (optionnel, défaut: "Voir détails") - Texte du lien

**Exemple:**
```django
{% include 'components/stat_card.html' with 
    icon='bi-calendar' 
    title='Congés en attente' 
    value='15' 
    subtitle='Cette semaine'
    color='blue'
    badge='Nouveau'
    trend='up'
    link_url='/leave/requests/'
    link_text='Voir toutes les demandes'
%}
```

---

### 2. `action_button.html` - Bouton d'Action
Bouton stylisé avec icône et plusieurs variantes.

**Paramètres:**
- `text` (requis) - Texte du bouton
- `url` (optionnel) - URL Django (ex: `attendance:punch`) - transforme en lien
- `style` (optionnel, défaut: `primary`) - Variantes: `primary`, `success`, `danger`, `warning`, `secondary`, `outline`
- `icon` (optionnel) - Classe d'icône à gauche (ex: `bi-clock`)
- `icon_right` (optionnel) - Classe d'icône à droite
- `type` (optionnel, défaut: `button`) - Type de bouton: `button`, `submit`, `reset`
- `onclick` (optionnel) - Code JavaScript pour le clic
- `disabled` (optionnel) - `True` pour désactiver
- `full_width` (optionnel) - `True` pour largeur 100%
- `class` (optionnel) - Classes CSS supplémentaires
- `color` (optionnel) - Couleur pour style `outline`

**Exemples:**
```django
{# Bouton lien primaire #}
{% include 'components/action_button.html' with 
    text='Pointer' 
    icon='bi-clock' 
    url='attendance:punch' 
    style='primary'
%}

{# Bouton danger avec onclick #}
{% include 'components/action_button.html' with 
    text='Supprimer' 
    icon='bi-trash' 
    style='danger' 
    onclick='confirmDelete()'
%}

{# Bouton outline désactivé #}
{% include 'components/action_button.html' with 
    text='Enregistrer' 
    style='outline' 
    color='green'
    disabled=True
%}
```

---

### 3. `status_badge.html` - Badge de Statut
Badge coloré pour afficher un statut.

**Paramètres:**
- `status` (requis si pas `color`) - Statut prédéfini: `approved`, `rejected`, `pending`, `in_progress`, `completed`, `cancelled`
- `text` (requis) - Texte à afficher
- `color` (optionnel) - Couleur personnalisée (ex: `blue`, `green`)
- `icon` (optionnel) - Classe d'icône à gauche
- `class` (optionnel) - Classes CSS supplémentaires

**Exemples:**
```django
{# Badge avec statut prédéfini #}
{% include 'components/status_badge.html' with 
    status='approved_rh' 
    text='Approuvé'
%}

{# Badge avec couleur personnalisée #}
{% include 'components/status_badge.html' with 
    color='purple' 
    text='En cours'
    icon='bi-clock'
%}
```

---

### 4. `empty_state.html` - État Vide
Affichage élégant quand il n'y a pas de données.

**Paramètres:**
- `title` (optionnel, défaut: "Aucune donnée") - Titre principal
- `message` (optionnel) - Message explicatif
- `icon` (optionnel) - Classe Bootstrap Icons
- `icon_svg` (optionnel) - Code SVG complet pour icône personnalisée
- `action_url` (optionnel) - URL du bouton d'action
- `action_text` (optionnel, défaut: "Commencer") - Texte du bouton
- `action_icon` (optionnel) - Icône du bouton

**Exemples:**
```django
{# État vide simple #}
{% include 'components/empty_state.html' with 
    icon='bi-calendar-x' 
    title='Aucune demande de congé'
    message='Vous n\'avez pas encore créé de demande'
%}

{# État vide avec action #}
{% include 'components/empty_state.html' with 
    icon='bi-inbox' 
    title='Boîte vide'
    message='Toutes vos notifications ont été traitées'
    action_url='dashboard:main'
    action_text='Retour au tableau de bord'
    action_icon='bi-house'
%}
```

---

## 🎨 Bonnes Pratiques

### 1. **Cohérence Visuelle**
Utilisez toujours les mêmes composants pour les mêmes besoins :
- Statistiques → `stat_card.html`
- Boutons → `action_button.html`
- Statuts → `status_badge.html`
- Listes vides → `empty_state.html`

### 2. **Couleurs Standards**
- `blue` - Actions primaires, informations
- `green` - Succès, approuvé, validations
- `red` - Danger, refus, erreurs
- `yellow` - Avertissements, en attente
- `purple` - Fonctionnalités avancées
- `gray` - Neutre, désactivé

### 3. **Dark Mode**
Tous les composants supportent automatiquement le dark mode avec les classes `dark:*`.

### 4. **Responsivité**
Les composants s'adaptent automatiquement aux écrans mobiles.

---

## 🔄 Migration

### Avant (code dupliqué):
```django
<div class="bg-white rounded-xl p-6">
    <div class="flex items-center">
        <i class="bi-calendar text-blue-600"></i>
        <h3>Congés: 15</h3>
    </div>
</div>
```

### Après (composant réutilisable):
```django
{% include 'components/stat_card.html' with icon='bi-calendar' title='Congés' value='15' color='blue' %}
```

**Avantages:**
- ✅ Moins de code (1 ligne vs 6+)
- ✅ Consistance garantie
- ✅ Maintenance centralisée
- ✅ Dark mode inclus
- ✅ Responsive automatique

---

## 📝 Contribuer

Pour ajouter un nouveau composant:
1. Créer `templates/components/nom_composant.html`
2. Documenter les paramètres en commentaire en haut du fichier
3. Ajouter une section dans ce README
4. Tester avec dark mode et mobile

**Convention de nommage:**
- `snake_case.html` pour les fichiers
- Paramètres en `snake_case`
- Classes TailwindCSS standards
