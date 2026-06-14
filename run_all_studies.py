import subprocess
import sys


COMMANDS = [
    "run_backtest.py",
    "optimize_strategies.py",
    "run_walk_forward.py",
    "run_no_leverage_study.py",
    "run_qqq_voo_rotation_study.py",
    "run_mag7_study.py",
    "generate_master_report.py",
]


def main() -> None:
    for script in COMMANDS:
        print(f"\n=== {script} ===")
        subprocess.run([sys.executable, script], check=True)


if __name__ == "__main__":
    main()
