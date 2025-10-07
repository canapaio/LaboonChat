# 🔄 SISTEMA VERSIONAMENTO E BACKUP - LABOON CHAT 2

*Sistema completo di gestione versioni, backup e controllo qualità*

**Data Creazione:** 27 Gennaio 2025  
**Versione Sistema:** 2.0.0  
**Stato:** Sistema Attivo ✅

---

## 📋 PANORAMICA SISTEMA

### 🎯 Obiettivi Principali
- **Versionamento Semantico**: Gestione versioni secondo SemVer 2.0
- **Backup Automatizzato**: Protezione dati e codice
- **Controllo Qualità**: Validazione automatica pre-commit
- **Rollback Sicuro**: Ripristino rapido versioni precedenti
- **Distribuzione Controllata**: Release management professionale

### 🏗️ Architettura Sistema
```
Sistema Versionamento
├── 📦 Git Repository Management
│   ├── Branch Strategy (GitFlow)
│   ├── Tag Management (SemVer)
│   ├── Commit Conventions
│   └── Merge Policies
├── 🔄 Backup System
│   ├── Local Backups
│   ├── Remote Repositories
│   ├── Archive Management
│   └── Recovery Procedures
├── 🛡️ Quality Gates
│   ├── Pre-commit Hooks
│   ├── CI/CD Pipeline
│   ├── Automated Testing
│   └── Code Quality Checks
└── 📊 Release Management
    ├── Version Bumping
    ├── Changelog Generation
    ├── Distribution Packages
    └── Deployment Automation
```

---

## 🏷️ SCHEMA VERSIONAMENTO

### 📊 Semantic Versioning (SemVer 2.0)

#### Formato Versione
```
MAJOR.MINOR.PATCH[-PRERELEASE][+BUILD]

Esempi:
- 2.0.0          # Release stabile
- 2.1.0-alpha.1  # Pre-release alpha
- 2.1.0-beta.2   # Pre-release beta
- 2.1.0-rc.1     # Release candidate
- 2.1.0+20250127 # Build metadata
```

#### Regole Incremento
| Tipo | Incremento | Quando | Esempio |
|------|------------|--------|---------|
| **MAJOR** | X.0.0 | Breaking changes | 1.5.2 → 2.0.0 |
| **MINOR** | X.Y.0 | Nuove funzionalità | 2.1.3 → 2.2.0 |
| **PATCH** | X.Y.Z | Bug fixes | 2.1.3 → 2.1.4 |

### 🎯 Versioni Correnti

#### LaboonChat2 Core
- **Versione Attuale**: `2.0.0`
- **Prossima Minor**: `2.1.0` (Plugin Marketplace)
- **Prossima Major**: `3.0.0` (Federation Support)

#### Plugin System
- **Core Plugins**: `2.0.0`
- **Secondary Plugins**: `1.0.0`
- **Plugin API**: `2.0.0`

---

## 🌳 STRATEGIA BRANCHING

### 🔄 GitFlow Workflow

#### Branch Principali
```
main (production)
├── develop (integration)
├── feature/* (nuove funzionalità)
├── release/* (preparazione release)
├── hotfix/* (fix urgenti)
└── support/* (manutenzione versioni)
```

#### Convenzioni Naming
| Tipo | Pattern | Esempio | Scopo |
|------|---------|---------|-------|
| **Feature** | `feature/ISSUE-description` | `feature/LC2-123-plugin-marketplace` | Nuove funzionalità |
| **Release** | `release/vX.Y.Z` | `release/v2.1.0` | Preparazione release |
| **Hotfix** | `hotfix/vX.Y.Z` | `hotfix/v2.0.1` | Fix critici |
| **Support** | `support/vX.Y` | `support/v2.0` | Manutenzione LTS |

### 🔀 Merge Policies

#### Protezione Branch
```yaml
main:
  - Require pull request reviews: 2
  - Require status checks: true
  - Require up-to-date branches: true
  - Include administrators: true

develop:
  - Require pull request reviews: 1
  - Require status checks: true
  - Allow force pushes: false
```

---

## 💾 SISTEMA BACKUP

### 🏠 Backup Locali

#### Struttura Directory
```
backups/
├── daily/           # Backup giornalieri (7 giorni)
├── weekly/          # Backup settimanali (4 settimane)
├── monthly/         # Backup mensili (12 mesi)
├── releases/        # Backup release (permanenti)
└── emergency/       # Backup emergenza (manuali)
```

#### Script Backup Automatico
```bash
#!/bin/bash
# backup_laboon_chat2.sh

BACKUP_DIR="/backups/laboon_chat2"
PROJECT_DIR="/path/to/LaboonChat2"
DATE=$(date +%Y%m%d_%H%M%S)

# Backup completo
tar -czf "$BACKUP_DIR/daily/laboon_chat2_$DATE.tar.gz" \
    --exclude='.git' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='node_modules' \
    "$PROJECT_DIR"

# Cleanup backup vecchi (>7 giorni)
find "$BACKUP_DIR/daily" -name "*.tar.gz" -mtime +7 -delete

echo "Backup completato: laboon_chat2_$DATE.tar.gz"
```

### ☁️ Backup Remoti

#### Repository Mirror
```yaml
# .github/workflows/mirror.yml
name: Repository Mirror
on:
  push:
    branches: [main, develop]
  schedule:
    - cron: '0 2 * * *'  # Daily at 2 AM

jobs:
  mirror:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - name: Mirror to GitLab
        run: |
          git remote add gitlab https://gitlab.com/laboonchat/LaboonChat2.git
          git push gitlab --all
          git push gitlab --tags
```

#### Cloud Storage Sync
```python
# scripts/cloud_backup.py
import boto3
import os
from datetime import datetime

def sync_to_s3():
    """Sincronizza backup su AWS S3"""
    s3 = boto3.client('s3')
    bucket = 'laboonchat2-backups'
    
    for root, dirs, files in os.walk('/backups/laboon_chat2'):
        for file in files:
            local_path = os.path.join(root, file)
            s3_path = f"backups/{datetime.now().strftime('%Y/%m')}/{file}"
            
            s3.upload_file(local_path, bucket, s3_path)
            print(f"Uploaded: {s3_path}")

if __name__ == "__main__":
    sync_to_s3()
```

---

## 🛡️ QUALITY GATES

### 🔍 Pre-commit Hooks

#### Configurazione `.pre-commit-config.yaml`
```yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-json
      - id: check-merge-conflict
      - id: check-added-large-files

  - repo: https://github.com/psf/black
    rev: 23.12.1
    hooks:
      - id: black
        language_version: python3.9

  - repo: https://github.com/pycqa/isort
    rev: 5.13.2
    hooks:
      - id: isort

  - repo: https://github.com/pycqa/flake8
    rev: 7.0.0
    hooks:
      - id: flake8

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.8.0
    hooks:
      - id: mypy
        additional_dependencies: [types-all]

  - repo: local
    hooks:
      - id: pytest
        name: pytest
        entry: pytest
        language: system
        pass_filenames: false
        always_run: true
```

### 🚀 CI/CD Pipeline

#### GitHub Actions Workflow
```yaml
# .github/workflows/ci.yml
name: CI/CD Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.9, 3.10, 3.11, 3.12]

    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -e .[dev,test]
    
    - name: Lint with flake8
      run: flake8 src tests
    
    - name: Type check with mypy
      run: mypy src
    
    - name: Test with pytest
      run: |
        pytest --cov=laboon_chat2 --cov-report=xml
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3

  security:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4
    
    - name: Security scan with bandit
      run: |
        pip install bandit
        bandit -r src/
    
    - name: Dependency check
      run: |
        pip install safety
        safety check

  build:
    needs: [test, security]
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Build package
      run: |
        python -m pip install build
        python -m build
    
    - name: Upload artifacts
      uses: actions/upload-artifact@v3
      with:
        name: dist
        path: dist/
```

---

## 📦 RELEASE MANAGEMENT

### 🏷️ Tag Management

#### Convenzioni Tag
```bash
# Release tags
v2.0.0          # Release stabile
v2.1.0-alpha.1  # Pre-release
v2.1.0-beta.1   # Beta release
v2.1.0-rc.1     # Release candidate

# Special tags
latest          # Ultima release stabile
stable          # Release LTS
experimental    # Branch sperimentale
```

#### Script Tagging Automatico
```bash
#!/bin/bash
# scripts/create_release.sh

VERSION=$1
TYPE=${2:-patch}  # major, minor, patch

if [ -z "$VERSION" ]; then
    echo "Usage: $0 <version> [type]"
    exit 1
fi

# Validazione formato SemVer
if ! [[ $VERSION =~ ^[0-9]+\.[0-9]+\.[0-9]+(-[a-zA-Z0-9.-]+)?(\+[a-zA-Z0-9.-]+)?$ ]]; then
    echo "Error: Invalid SemVer format"
    exit 1
fi

# Update version in files
sed -i "s/version = \".*\"/version = \"$VERSION\"/" pyproject.toml
sed -i "s/__version__ = \".*\"/__version__ = \"$VERSION\"/" src/laboon_chat2/__init__.py

# Commit changes
git add pyproject.toml src/laboon_chat2/__init__.py
git commit -m "chore: bump version to $VERSION"

# Create tag
git tag -a "v$VERSION" -m "Release version $VERSION"

echo "Created release tag: v$VERSION"
```

### 📝 Changelog Generation

#### Formato Changelog
```markdown
# Changelog

All notable changes to LaboonChat2 will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- New features in development

### Changed
- Changes in existing functionality

### Deprecated
- Soon-to-be removed features

### Removed
- Now removed features

### Fixed
- Any bug fixes

### Security
- Vulnerability fixes

## [2.0.0] - 2025-01-27

### Added
- Complete modular architecture
- Plugin system with core and secondary plugins
- Advanced security with post-quantum cryptography
- P2P networking with hybrid topology
- Comprehensive test suite
- Production-ready deployment options

### Changed
- Complete rewrite from LaboonChat v1
- New plugin-based architecture
- Enhanced security model

## [1.0.0] - 2024-12-01

### Added
- Initial release of LaboonChat
- Basic P2P messaging
- Simple encryption
```

#### Script Generazione Automatica
```python
# scripts/generate_changelog.py
import re
import subprocess
from datetime import datetime

def get_commits_since_tag(tag):
    """Ottiene commit dal tag specificato"""
    cmd = f"git log {tag}..HEAD --oneline --no-merges"
    result = subprocess.run(cmd.split(), capture_output=True, text=True)
    return result.stdout.strip().split('\n') if result.stdout else []

def categorize_commit(commit_msg):
    """Categorizza commit per tipo"""
    patterns = {
        'Added': [r'^feat:', r'^add:', r'^new:'],
        'Changed': [r'^change:', r'^update:', r'^modify:'],
        'Fixed': [r'^fix:', r'^bug:', r'^patch:'],
        'Security': [r'^security:', r'^sec:', r'^vuln:'],
        'Deprecated': [r'^deprecate:', r'^dep:'],
        'Removed': [r'^remove:', r'^delete:', r'^rm:']
    }
    
    for category, patterns_list in patterns.items():
        for pattern in patterns_list:
            if re.match(pattern, commit_msg, re.IGNORECASE):
                return category
    
    return 'Changed'  # Default category

def generate_changelog_entry(version, commits):
    """Genera entry changelog per versione"""
    date = datetime.now().strftime('%Y-%m-%d')
    entry = f"\n## [{version}] - {date}\n\n"
    
    categories = {}
    for commit in commits:
        if commit:
            category = categorize_commit(commit)
            if category not in categories:
                categories[category] = []
            # Remove commit hash and clean message
            msg = re.sub(r'^[a-f0-9]+\s+', '', commit)
            categories[category].append(msg)
    
    for category in ['Added', 'Changed', 'Deprecated', 'Removed', 'Fixed', 'Security']:
        if category in categories:
            entry += f"### {category}\n"
            for msg in categories[category]:
                entry += f"- {msg}\n"
            entry += "\n"
    
    return entry

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("Usage: python generate_changelog.py <version>")
        sys.exit(1)
    
    version = sys.argv[1]
    last_tag = subprocess.run(
        ["git", "describe", "--tags", "--abbrev=0"], 
        capture_output=True, text=True
    ).stdout.strip()
    
    commits = get_commits_since_tag(last_tag)
    entry = generate_changelog_entry(version, commits)
    
    print(f"Changelog entry for {version}:")
    print(entry)
```

---

## 🔄 PROCEDURE OPERATIVE

### 🚀 Workflow Release

#### 1. Preparazione Release
```bash
# 1. Checkout develop branch
git checkout develop
git pull origin develop

# 2. Create release branch
git checkout -b release/v2.1.0

# 3. Update version numbers
./scripts/create_release.sh 2.1.0

# 4. Run full test suite
pytest --cov=laboon_chat2 --cov-report=html

# 5. Generate changelog
python scripts/generate_changelog.py 2.1.0

# 6. Commit release changes
git add .
git commit -m "chore: prepare release v2.1.0"
```

#### 2. Finalizzazione Release
```bash
# 1. Merge to main
git checkout main
git merge --no-ff release/v2.1.0

# 2. Create release tag
git tag -a v2.1.0 -m "Release version 2.1.0"

# 3. Merge back to develop
git checkout develop
git merge --no-ff release/v2.1.0

# 4. Push everything
git push origin main develop --tags

# 5. Delete release branch
git branch -d release/v2.1.0
git push origin --delete release/v2.1.0
```

### 🔧 Hotfix Workflow

#### Procedura Hotfix Urgente
```bash
# 1. Create hotfix from main
git checkout main
git checkout -b hotfix/v2.0.1

# 2. Fix the issue
# ... make necessary changes ...

# 3. Test the fix
pytest tests/test_security.py -v

# 4. Update version
./scripts/create_release.sh 2.0.1 patch

# 5. Commit fix
git add .
git commit -m "fix: critical security vulnerability"

# 6. Merge to main and develop
git checkout main
git merge --no-ff hotfix/v2.0.1
git tag -a v2.0.1 -m "Hotfix version 2.0.1"

git checkout develop
git merge --no-ff hotfix/v2.0.1

# 7. Push and cleanup
git push origin main develop --tags
git branch -d hotfix/v2.0.1
```

---

## 📊 MONITORING E METRICHE

### 📈 Metriche Repository

#### Git Statistics
```bash
# Script per statistiche repository
#!/bin/bash
# scripts/repo_stats.sh

echo "=== LaboonChat2 Repository Statistics ==="
echo "Date: $(date)"
echo

echo "📊 Commit Statistics:"
echo "Total commits: $(git rev-list --all --count)"
echo "Contributors: $(git shortlog -sn | wc -l)"
echo "Branches: $(git branch -a | wc -l)"
echo "Tags: $(git tag | wc -l)"
echo

echo "📁 Code Statistics:"
find src -name "*.py" | xargs wc -l | tail -1
echo "Test files: $(find tests -name "*.py" | wc -l)"
echo "Documentation files: $(find docs -name "*.md" | wc -l)"
echo

echo "🔄 Recent Activity:"
git log --oneline -10
```

#### Quality Metrics
```python
# scripts/quality_metrics.py
import subprocess
import json
from pathlib import Path

def get_test_coverage():
    """Ottiene coverage dei test"""
    result = subprocess.run(
        ["pytest", "--cov=laboon_chat2", "--cov-report=json"],
        capture_output=True, text=True
    )
    
    if Path("coverage.json").exists():
        with open("coverage.json") as f:
            data = json.load(f)
            return data["totals"]["percent_covered"]
    return 0

def get_code_quality():
    """Ottiene metriche qualità codice"""
    # Flake8 violations
    flake8_result = subprocess.run(
        ["flake8", "src", "--count"],
        capture_output=True, text=True
    )
    
    # MyPy errors
    mypy_result = subprocess.run(
        ["mypy", "src", "--error-format=json"],
        capture_output=True, text=True
    )
    
    return {
        "flake8_violations": int(flake8_result.stdout.strip() or 0),
        "mypy_errors": len(mypy_result.stdout.strip().split('\n')) if mypy_result.stdout else 0,
        "test_coverage": get_test_coverage()
    }

if __name__ == "__main__":
    metrics = get_code_quality()
    print(f"📊 Quality Metrics:")
    print(f"Test Coverage: {metrics['test_coverage']:.1f}%")
    print(f"Flake8 Violations: {metrics['flake8_violations']}")
    print(f"MyPy Errors: {metrics['mypy_errors']}")
```

### 🔔 Alerting System

#### Webhook Notifications
```python
# scripts/notify_release.py
import requests
import json
import sys

def notify_discord(version, changelog):
    """Notifica release su Discord"""
    webhook_url = "YOUR_DISCORD_WEBHOOK_URL"
    
    embed = {
        "title": f"🚀 LaboonChat2 v{version} Released!",
        "description": f"New version available: {version}",
        "color": 0x00ff00,
        "fields": [
            {
                "name": "📝 Changelog",
                "value": changelog[:1000] + "..." if len(changelog) > 1000 else changelog,
                "inline": False
            }
        ],
        "timestamp": datetime.utcnow().isoformat()
    }
    
    payload = {
        "embeds": [embed]
    }
    
    response = requests.post(webhook_url, json=payload)
    return response.status_code == 204

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python notify_release.py <version> <changelog>")
        sys.exit(1)
    
    version = sys.argv[1]
    changelog = sys.argv[2]
    
    if notify_discord(version, changelog):
        print("✅ Release notification sent successfully")
    else:
        print("❌ Failed to send notification")
```

---

## 🛠️ STRUMENTI E AUTOMAZIONE

### 📋 Checklist Release

#### Pre-Release Checklist
- [ ] **Code Quality**
  - [ ] All tests passing (100%)
  - [ ] Code coverage > 95%
  - [ ] No flake8 violations
  - [ ] No mypy errors
  - [ ] Security scan passed

- [ ] **Documentation**
  - [ ] README updated
  - [ ] CHANGELOG updated
  - [ ] API documentation current
  - [ ] User guide reviewed

- [ ] **Version Management**
  - [ ] Version bumped correctly
  - [ ] All version references updated
  - [ ] Migration scripts ready (if needed)

- [ ] **Testing**
  - [ ] Unit tests passing
  - [ ] Integration tests passing
  - [ ] E2E tests passing
  - [ ] Performance tests acceptable

- [ ] **Security**
  - [ ] Dependency vulnerabilities checked
  - [ ] Security audit completed
  - [ ] Secrets not exposed

#### Post-Release Checklist
- [ ] **Distribution**
  - [ ] PyPI package published
  - [ ] Docker images built
  - [ ] GitHub release created
  - [ ] Documentation deployed

- [ ] **Communication**
  - [ ] Release notes published
  - [ ] Community notified
  - [ ] Social media updated
  - [ ] Blog post published (major releases)

- [ ] **Monitoring**
  - [ ] Release metrics tracked
  - [ ] Error monitoring active
  - [ ] Performance monitoring active
  - [ ] User feedback collected

### 🤖 Automation Scripts

#### Master Release Script
```bash
#!/bin/bash
# scripts/release.sh - Master release automation

set -e

VERSION=$1
TYPE=${2:-minor}

if [ -z "$VERSION" ]; then
    echo "Usage: $0 <version> [type]"
    exit 1
fi

echo "🚀 Starting release process for v$VERSION"

# 1. Pre-release checks
echo "📋 Running pre-release checks..."
./scripts/pre_release_check.sh

# 2. Create release branch
echo "🌿 Creating release branch..."
git checkout develop
git pull origin develop
git checkout -b "release/v$VERSION"

# 3. Update version
echo "🏷️ Updating version..."
./scripts/create_release.sh "$VERSION" "$TYPE"

# 4. Run tests
echo "🧪 Running test suite..."
pytest --cov=laboon_chat2 --cov-report=html

# 5. Generate changelog
echo "📝 Generating changelog..."
python scripts/generate_changelog.py "$VERSION"

# 6. Build package
echo "📦 Building package..."
python -m build

# 7. Security scan
echo "🛡️ Running security scan..."
bandit -r src/
safety check

# 8. Finalize release
echo "✅ Finalizing release..."
git add .
git commit -m "chore: prepare release v$VERSION"

# 9. Merge to main
git checkout main
git merge --no-ff "release/v$VERSION"
git tag -a "v$VERSION" -m "Release version $VERSION"

# 10. Merge back to develop
git checkout develop
git merge --no-ff "release/v$VERSION"

# 11. Push everything
git push origin main develop --tags

# 12. Cleanup
git branch -d "release/v$VERSION"

# 13. Notify
python scripts/notify_release.py "$VERSION" "$(cat CHANGELOG.md | head -20)"

echo "🎉 Release v$VERSION completed successfully!"
```

---

## 🔮 ROADMAP SISTEMA

### 📅 Prossimi Sviluppi

#### Q1 2025
- [ ] **Automated Dependency Updates**
  - Dependabot configuration
  - Automated security patches
  - Compatibility testing

- [ ] **Enhanced CI/CD**
  - Multi-platform builds
  - Automated performance testing
  - Deployment automation

#### Q2 2025
- [ ] **Advanced Monitoring**
  - Release health monitoring
  - User adoption metrics
  - Performance regression detection

- [ ] **Quality Improvements**
  - Mutation testing
  - Chaos engineering
  - Load testing automation

#### Q3 2025
- [ ] **Enterprise Features**
  - Enterprise release channels
  - Long-term support (LTS)
  - Professional support tiers

### 🎯 Obiettivi Qualità

#### Metriche Target 2025
| Metrica | Q1 | Q2 | Q3 | Q4 |
|---------|----|----|----|----|
| **Test Coverage** | 95% | 97% | 98% | 99% |
| **Release Frequency** | Monthly | Bi-weekly | Weekly | On-demand |
| **Time to Release** | 2 hours | 1 hour | 30 min | 15 min |
| **Rollback Time** | 10 min | 5 min | 2 min | 1 min |

---

## 📚 RISORSE E RIFERIMENTI

### 🔗 Collegamenti Utili

#### Documentazione Standard
- [Semantic Versioning](https://semver.org/)
- [Keep a Changelog](https://keepachangelog.com/)
- [GitFlow Workflow](https://nvie.com/posts/a-successful-git-branching-model/)
- [Conventional Commits](https://www.conventionalcommits.org/)

#### Strumenti Consigliati
- [Pre-commit](https://pre-commit.com/) - Git hooks
- [Bump2version](https://github.com/c4urself/bump2version) - Version management
- [Release-drafter](https://github.com/release-drafter/release-drafter) - Automated releases
- [Semantic-release](https://github.com/semantic-release/semantic-release) - Automated versioning

### 📖 Best Practices

#### Commit Messages
```
<type>(<scope>): <subject>

<body>

<footer>

Types: feat, fix, docs, style, refactor, test, chore
Scopes: core, plugin, security, network, ui, test, docs
```

#### Branch Naming
```
feature/LC2-123-short-description
bugfix/LC2-456-fix-security-issue
hotfix/v2.0.1-critical-patch
release/v2.1.0
```

---

*🐋 "Come Laboon che custodisce i ricordi dell'oceano,  
il nostro sistema di versionamento preserva ogni momento del viaggio." 🌊*

---

**Documento creato**: 27 Gennaio 2025  
**Versione**: 1.0  
**Stato**: Sistema Attivo ✅  
**Prossimo aggiornamento**: Implementazione automazioni Q1 2025