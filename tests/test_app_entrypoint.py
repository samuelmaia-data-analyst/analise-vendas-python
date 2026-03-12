from pathlib import Path


def test_app_entrypoint_points_to_streamlit_app():
    app_file = Path(__file__).resolve().parents[1] / "app.py"
    content = app_file.read_text(encoding="utf-8")
    assert "run_streamlit_app" in content
    assert "src.sales_analytics.app_runner" in content


def test_cli_wrapper_uses_official_package_entrypoint():
    script_file = Path(__file__).resolve().parents[1] / "scripts" / "analise_crescimento.py"
    content = script_file.read_text(encoding="utf-8")
    assert "src.sales_analytics.cli" in content
    assert "SystemExit(main())" in content
