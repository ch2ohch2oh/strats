from src.master_reporting import save_master_report


if __name__ == "__main__":
    report = save_master_report()
    print(f"Master report: {report}")
