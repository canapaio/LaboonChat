#!/usr/bin/env python3
"""
Script per eseguire tutti i test di integrazione end-to-end di LaboonChat2

Questo script esegue una suite completa di test di integrazione,
generando report dettagliati e verificando la copertura del codice.
"""

import os
import sys
import subprocess
import argparse
import json
import time
from pathlib import Path
from typing import Dict, List, Any, Optional


def setup_test_environment():
    """Configura l'ambiente di test"""
    
    # Aggiungi percorsi al PYTHONPATH
    project_root = Path(__file__).parent.parent
    src_path = project_root / "src"
    plugins_path = project_root / "plugins"
    
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))
    if str(plugins_path) not in sys.path:
        sys.path.insert(0, str(plugins_path))
    
    # Configura variabili ambiente per test
    os.environ["LABOON_TEST_MODE"] = "true"
    os.environ["LABOON_LOG_LEVEL"] = "DEBUG"
    os.environ["LABOON_DISABLE_NETWORK"] = "false"  # Abilita test di rete
    
    print("✓ Ambiente di test configurato")


def run_pytest_command(test_files: List[str], extra_args: List[str] = None) -> Dict[str, Any]:
    """Esegue comando pytest e restituisce risultati"""
    
    if extra_args is None:
        extra_args = []
    
    # Comando base pytest
    cmd = [
        sys.executable, "-m", "pytest",
        "--tb=short",
        "--strict-markers",
        "--strict-config",
        "-v"
    ] + test_files + extra_args
    
    print(f"Eseguendo: {' '.join(cmd)}")
    
    start_time = time.time()
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent
        )
        
        end_time = time.time()
        duration = end_time - start_time
        
        return {
            "success": result.returncode == 0,
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "duration": duration,
            "command": " ".join(cmd)
        }
        
    except Exception as e:
        return {
            "success": False,
            "returncode": -1,
            "stdout": "",
            "stderr": str(e),
            "duration": 0,
            "command": " ".join(cmd)
        }


def run_basic_integration_tests() -> Dict[str, Any]:
    """Esegue test di integrazione base"""
    
    print("\n" + "="*60)
    print("ESECUZIONE TEST DI INTEGRAZIONE BASE")
    print("="*60)
    
    test_files = [
        "tests/test_integration_e2e.py::TestE2EBasicFlow",
        "tests/test_integration_e2e.py::TestE2EMessagingFlow",
        "tests/test_integration_e2e.py::TestE2EInterfaceFlow"
    ]
    
    extra_args = [
        "--maxfail=5",  # Ferma dopo 5 fallimenti
        "-x"  # Ferma al primo fallimento
    ]
    
    return run_pytest_command(test_files, extra_args)


def run_security_integration_tests() -> Dict[str, Any]:
    """Esegue test di integrazione sicurezza"""
    
    print("\n" + "="*60)
    print("ESECUZIONE TEST DI INTEGRAZIONE SICUREZZA")
    print("="*60)
    
    test_files = [
        "tests/test_integration_e2e.py::TestE2ESecurityFlow",
        "tests/test_real_world_scenarios.py::TestRealWorldSecurityScenarios"
    ]
    
    extra_args = [
        "-m", "security or crypto",
        "--maxfail=3"
    ]
    
    return run_pytest_command(test_files, extra_args)


def run_file_transfer_integration_tests() -> Dict[str, Any]:
    """Esegue test di integrazione trasferimento file"""
    
    print("\n" + "="*60)
    print("ESECUZIONE TEST DI INTEGRAZIONE TRASFERIMENTO FILE")
    print("="*60)
    
    test_files = [
        "tests/test_integration_e2e.py::TestE2EFileTransferFlow",
        "tests/test_real_world_scenarios.py::TestRealWorldFileTransferScenarios"
    ]
    
    extra_args = [
        "-m", "file_io",
        "--maxfail=3"
    ]
    
    return run_pytest_command(test_files, extra_args)


def run_network_integration_tests() -> Dict[str, Any]:
    """Esegue test di integrazione rete"""
    
    print("\n" + "="*60)
    print("ESECUZIONE TEST DI INTEGRAZIONE RETE")
    print("="*60)
    
    test_files = [
        "tests/test_real_world_scenarios.py::TestRealWorldNetworkScenarios",
        "tests/test_real_world_scenarios.py::TestRealWorldChatScenarios"
    ]
    
    extra_args = [
        "-m", "network",
        "--maxfail=3"
    ]
    
    return run_pytest_command(test_files, extra_args)


def run_performance_tests() -> Dict[str, Any]:
    """Esegue test di performance"""
    
    print("\n" + "="*60)
    print("ESECUZIONE TEST DI PERFORMANCE")
    print("="*60)
    
    test_files = [
        "tests/test_integration_e2e.py::TestE2EPerformance",
        "tests/test_real_world_scenarios.py::TestRealWorldStressScenarios"
    ]
    
    extra_args = [
        "-m", "performance or stress",
        "--maxfail=2",
        "--timeout=60"  # Timeout di 60 secondi per test performance
    ]
    
    return run_pytest_command(test_files, extra_args)


def run_error_handling_tests() -> Dict[str, Any]:
    """Esegue test di gestione errori"""
    
    print("\n" + "="*60)
    print("ESECUZIONE TEST DI GESTIONE ERRORI")
    print("="*60)
    
    test_files = [
        "tests/test_integration_e2e.py::TestE2EErrorHandling"
    ]
    
    extra_args = [
        "--maxfail=3"
    ]
    
    return run_pytest_command(test_files, extra_args)


def run_complete_scenarios_tests() -> Dict[str, Any]:
    """Esegue test di scenari completi"""
    
    print("\n" + "="*60)
    print("ESECUZIONE TEST SCENARI COMPLETI")
    print("="*60)
    
    test_files = [
        "tests/test_real_world_scenarios.py::TestRealWorldIntegrationScenarios"
    ]
    
    extra_args = [
        "--maxfail=2",
        "--timeout=120"  # Timeout più lungo per scenari completi
    ]
    
    return run_pytest_command(test_files, extra_args)


def run_coverage_analysis() -> Dict[str, Any]:
    """Esegue analisi copertura codice"""
    
    print("\n" + "="*60)
    print("ANALISI COPERTURA CODICE")
    print("="*60)
    
    # Installa pytest-cov se non presente
    try:
        import pytest_cov
    except ImportError:
        print("Installando pytest-cov...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pytest-cov"])
    
    test_files = [
        "tests/test_integration_e2e.py",
        "tests/test_real_world_scenarios.py"
    ]
    
    extra_args = [
        "--cov=src",
        "--cov=plugins",
        "--cov-report=html:coverage_html",
        "--cov-report=term-missing",
        "--cov-fail-under=70"  # Richiede almeno 70% di copertura
    ]
    
    return run_pytest_command(test_files, extra_args)


def generate_test_report(results: Dict[str, Dict[str, Any]]) -> str:
    """Genera report dettagliato dei test"""
    
    report_lines = []
    report_lines.append("REPORT TEST DI INTEGRAZIONE LABOON CHAT2")
    report_lines.append("=" * 60)
    report_lines.append(f"Data esecuzione: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    report_lines.append("")
    
    total_duration = 0
    total_tests = len(results)
    passed_tests = 0
    
    for test_name, result in results.items():
        total_duration += result["duration"]
        
        status = "✓ PASSATO" if result["success"] else "✗ FALLITO"
        duration_str = f"{result['duration']:.2f}s"
        
        report_lines.append(f"{test_name}: {status} ({duration_str})")
        
        if result["success"]:
            passed_tests += 1
        else:
            report_lines.append(f"  Codice uscita: {result['returncode']}")
            if result["stderr"]:
                report_lines.append(f"  Errore: {result['stderr'][:200]}...")
        
        report_lines.append("")
    
    # Riepilogo
    report_lines.append("RIEPILOGO")
    report_lines.append("-" * 30)
    report_lines.append(f"Test eseguiti: {total_tests}")
    report_lines.append(f"Test passati: {passed_tests}")
    report_lines.append(f"Test falliti: {total_tests - passed_tests}")
    report_lines.append(f"Tasso successo: {(passed_tests/total_tests)*100:.1f}%")
    report_lines.append(f"Durata totale: {total_duration:.2f}s")
    
    return "\n".join(report_lines)


def save_test_results(results: Dict[str, Dict[str, Any]], report: str):
    """Salva risultati test su file"""
    
    # Crea directory risultati
    results_dir = Path("test_results")
    results_dir.mkdir(exist_ok=True)
    
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    
    # Salva report testuale
    report_file = results_dir / f"integration_test_report_{timestamp}.txt"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
    
    # Salva risultati JSON
    json_file = results_dir / f"integration_test_results_{timestamp}.json"
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\n✓ Risultati salvati in:")
    print(f"  Report: {report_file}")
    print(f"  JSON: {json_file}")


def main():
    """Funzione principale"""
    
    parser = argparse.ArgumentParser(description="Esegue test di integrazione LaboonChat2")
    parser.add_argument("--quick", action="store_true", help="Esegue solo test base (veloce)")
    parser.add_argument("--no-coverage", action="store_true", help="Salta analisi copertura")
    parser.add_argument("--category", choices=[
        "basic", "security", "files", "network", "performance", "errors", "scenarios"
    ], help="Esegue solo una categoria di test")
    parser.add_argument("--save-results", action="store_true", help="Salva risultati su file")
    
    args = parser.parse_args()
    
    print("SUITE TEST DI INTEGRAZIONE LABOON CHAT2")
    print("=" * 60)
    
    # Configura ambiente
    setup_test_environment()
    
    # Definisci test da eseguire
    test_suites = {}
    
    if args.category:
        # Esegui solo categoria specifica
        if args.category == "basic":
            test_suites["Test Base"] = run_basic_integration_tests
        elif args.category == "security":
            test_suites["Test Sicurezza"] = run_security_integration_tests
        elif args.category == "files":
            test_suites["Test File Transfer"] = run_file_transfer_integration_tests
        elif args.category == "network":
            test_suites["Test Rete"] = run_network_integration_tests
        elif args.category == "performance":
            test_suites["Test Performance"] = run_performance_tests
        elif args.category == "errors":
            test_suites["Test Gestione Errori"] = run_error_handling_tests
        elif args.category == "scenarios":
            test_suites["Test Scenari Completi"] = run_complete_scenarios_tests
    
    elif args.quick:
        # Esegui solo test base
        test_suites["Test Base"] = run_basic_integration_tests
        test_suites["Test Gestione Errori"] = run_error_handling_tests
    
    else:
        # Esegui suite completa
        test_suites = {
            "Test Base": run_basic_integration_tests,
            "Test Sicurezza": run_security_integration_tests,
            "Test File Transfer": run_file_transfer_integration_tests,
            "Test Rete": run_network_integration_tests,
            "Test Performance": run_performance_tests,
            "Test Gestione Errori": run_error_handling_tests,
            "Test Scenari Completi": run_complete_scenarios_tests
        }
        
        if not args.no_coverage:
            test_suites["Analisi Copertura"] = run_coverage_analysis
    
    # Esegui test
    results = {}
    
    for test_name, test_function in test_suites.items():
        print(f"\n🚀 Avvio {test_name}...")
        
        try:
            result = test_function()
            results[test_name] = result
            
            if result["success"]:
                print(f"✓ {test_name} completato con successo")
            else:
                print(f"✗ {test_name} fallito")
                
        except Exception as e:
            print(f"✗ Errore durante {test_name}: {e}")
            results[test_name] = {
                "success": False,
                "returncode": -1,
                "stdout": "",
                "stderr": str(e),
                "duration": 0,
                "command": ""
            }
    
    # Genera report
    report = generate_test_report(results)
    print("\n" + report)
    
    # Salva risultati se richiesto
    if args.save_results:
        save_test_results(results, report)
    
    # Determina codice uscita
    all_passed = all(result["success"] for result in results.values())
    
    if all_passed:
        print("\n🎉 Tutti i test sono passati!")
        sys.exit(0)
    else:
        print("\n❌ Alcuni test sono falliti!")
        sys.exit(1)


if __name__ == "__main__":
    main()