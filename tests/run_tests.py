"""
Test Runner per LaboonChat2

Esegue tutti i test della suite con opzioni di configurazione e reporting.
"""

import sys
import os
import pytest
import argparse
from pathlib import Path
import time
import json
from typing import List, Dict, Any

# Aggiungi percorsi per import
current_dir = Path(__file__).parent
project_root = current_dir.parent
sys.path.insert(0, str(project_root / "src"))
sys.path.insert(0, str(project_root / "plugins" / "core" / "security"))
sys.path.insert(0, str(project_root / "plugins" / "core" / "messaging"))
sys.path.insert(0, str(project_root / "plugins" / "core" / "interface"))


def get_test_files() -> List[str]:
    """Recupera tutti i file di test disponibili"""
    test_dir = Path(__file__).parent
    test_files = []
    
    for test_file in test_dir.glob("test_*.py"):
        if test_file.name != "run_tests.py":
            test_files.append(str(test_file))
    
    return sorted(test_files)


def run_test_suite(
    test_files: List[str] = None,
    verbose: bool = True,
    coverage: bool = False,
    html_report: bool = False,
    xml_report: bool = False,
    parallel: bool = False,
    markers: str = None,
    output_dir: str = None
) -> Dict[str, Any]:
    """
    Esegue la suite di test con le opzioni specificate
    
    Args:
        test_files: Lista di file di test da eseguire (None per tutti)
        verbose: Modalità verbose
        coverage: Abilita report di copertura
        html_report: Genera report HTML
        xml_report: Genera report XML
        parallel: Esegue test in parallelo
        markers: Filtri per marker pytest
        output_dir: Directory per i report
    
    Returns:
        Dizionario con risultati dell'esecuzione
    """
    if test_files is None:
        test_files = get_test_files()
    
    if output_dir is None:
        output_dir = Path(__file__).parent / "reports"
    else:
        output_dir = Path(output_dir)
    
    output_dir.mkdir(exist_ok=True)
    
    # Costruisci argomenti pytest
    pytest_args = []
    
    # Aggiungi file di test
    pytest_args.extend(test_files)
    
    # Opzioni di base
    if verbose:
        pytest_args.append("-v")
    
    # Markers
    if markers:
        pytest_args.extend(["-m", markers])
    
    # Coverage
    if coverage:
        pytest_args.extend([
            "--cov=laboon_chat2",
            "--cov=plugins",
            f"--cov-report=html:{output_dir}/coverage_html",
            f"--cov-report=term-missing"
        ])
    
    # Report HTML
    if html_report:
        pytest_args.extend([
            f"--html={output_dir}/report.html",
            "--self-contained-html"
        ])
    
    # Report XML (JUnit)
    if xml_report:
        pytest_args.extend([
            f"--junit-xml={output_dir}/junit.xml"
        ])
    
    # Esecuzione parallela
    if parallel:
        pytest_args.extend(["-n", "auto"])
    
    # Aggiungi opzioni per output più pulito
    pytest_args.extend([
        "--tb=short",
        "--strict-markers",
        "--disable-warnings"
    ])
    
    print(f"Esecuzione test con argomenti: {' '.join(pytest_args)}")
    print(f"Report salvati in: {output_dir}")
    print("-" * 60)
    
    start_time = time.time()
    
    # Esegui pytest
    exit_code = pytest.main(pytest_args)
    
    end_time = time.time()
    execution_time = end_time - start_time
    
    # Risultati
    results = {
        "exit_code": exit_code,
        "execution_time": execution_time,
        "test_files": test_files,
        "output_dir": str(output_dir),
        "success": exit_code == 0
    }
    
    # Salva risultati
    results_file = output_dir / "test_results.json"
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    return results


def run_specific_tests(test_categories: List[str]) -> Dict[str, Any]:
    """
    Esegue categorie specifiche di test
    
    Args:
        test_categories: Lista di categorie (es. ['core', 'plugins', 'integration'])
    
    Returns:
        Dizionario con risultati dell'esecuzione
    """
    test_mapping = {
        'core': [
            'test_plugin_manager.py',
            'test_application.py',
            'test_config_loader.py',
            'test_logger.py',
            'test_crypto_utils.py'
        ],
        'plugins': [
            'test_security_plugins.py',
            'test_messaging_plugins.py',
            'test_interface_plugins.py'
        ],
        'integration': [
            # Test di integrazione verranno aggiunti qui
        ]
    }
    
    test_files = []
    test_dir = Path(__file__).parent
    
    for category in test_categories:
        if category in test_mapping:
            for test_file in test_mapping[category]:
                full_path = test_dir / test_file
                if full_path.exists():
                    test_files.append(str(full_path))
    
    if not test_files:
        print(f"Nessun test trovato per le categorie: {test_categories}")
        return {"success": False, "error": "No tests found"}
    
    return run_test_suite(test_files=test_files)


def main():
    """Funzione principale del test runner"""
    parser = argparse.ArgumentParser(description="LaboonChat2 Test Runner")
    
    parser.add_argument(
        "--files", "-f",
        nargs="+",
        help="File di test specifici da eseguire"
    )
    
    parser.add_argument(
        "--category", "-c",
        choices=["core", "plugins", "integration", "all"],
        default="all",
        help="Categoria di test da eseguire"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Output verbose"
    )
    
    parser.add_argument(
        "--coverage",
        action="store_true",
        help="Genera report di copertura"
    )
    
    parser.add_argument(
        "--html-report",
        action="store_true",
        help="Genera report HTML"
    )
    
    parser.add_argument(
        "--xml-report",
        action="store_true",
        help="Genera report XML (JUnit)"
    )
    
    parser.add_argument(
        "--parallel", "-p",
        action="store_true",
        help="Esegui test in parallelo"
    )
    
    parser.add_argument(
        "--markers", "-m",
        help="Filtri per marker pytest (es. 'not slow')"
    )
    
    parser.add_argument(
        "--output-dir", "-o",
        help="Directory per i report"
    )
    
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Esecuzione rapida (solo test essenziali)"
    )
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("LaboonChat2 Test Runner")
    print("=" * 60)
    
    # Determina file di test
    test_files = None
    
    if args.files:
        # File specifici
        test_dir = Path(__file__).parent
        test_files = []
        for file in args.files:
            if not file.startswith("test_"):
                file = f"test_{file}"
            if not file.endswith(".py"):
                file = f"{file}.py"
            
            full_path = test_dir / file
            if full_path.exists():
                test_files.append(str(full_path))
            else:
                print(f"Attenzione: File di test non trovato: {full_path}")
    
    elif args.category != "all":
        # Categoria specifica
        results = run_specific_tests([args.category])
        print_results(results)
        return results["exit_code"] if "exit_code" in results else 1
    
    # Markers per esecuzione rapida
    markers = args.markers
    if args.quick:
        markers = "not slow" if not markers else f"{markers} and not slow"
    
    # Esegui test
    results = run_test_suite(
        test_files=test_files,
        verbose=args.verbose,
        coverage=args.coverage,
        html_report=args.html_report,
        xml_report=args.xml_report,
        parallel=args.parallel,
        markers=markers,
        output_dir=args.output_dir
    )
    
    print_results(results)
    return results["exit_code"]


def print_results(results: Dict[str, Any]):
    """Stampa i risultati dell'esecuzione"""
    print("\n" + "=" * 60)
    print("RISULTATI TEST")
    print("=" * 60)
    
    if "error" in results:
        print(f"❌ Errore: {results['error']}")
        return
    
    success = results.get("success", False)
    execution_time = results.get("execution_time", 0)
    
    status_icon = "✅" if success else "❌"
    status_text = "SUCCESSO" if success else "FALLIMENTO"
    
    print(f"{status_icon} Stato: {status_text}")
    print(f"⏱️  Tempo di esecuzione: {execution_time:.2f} secondi")
    print(f"📁 Report salvati in: {results.get('output_dir', 'N/A')}")
    
    if "test_files" in results:
        print(f"📋 File di test eseguiti: {len(results['test_files'])}")
    
    print("=" * 60)


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)