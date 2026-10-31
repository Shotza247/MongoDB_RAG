from mongodb_vector_test_ui.core.config import get_settings, safe_diagnostics, validate_settings


def main() -> None:
    settings = get_settings()
    diagnostics = safe_diagnostics(settings)
    issues = validate_settings(settings)

    print("Environment diagnostics. Secrets are not printed.")
    for key, value in diagnostics.items():
        print(f"{key}: {value}")

    if issues:
        print("\nIssues:")
        for issue in issues:
            print(f"- {issue}")
        raise SystemExit(1)

    print("\nEnvironment check passed.")


if __name__ == "__main__":
    main()
