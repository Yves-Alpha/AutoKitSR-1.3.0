"""Entrée Streamlit Cloud pour AutoKitSR."""

# Exécute le module principal (UI Streamlit) situé dans app/main.py
import runpy

runpy.run_module("app.main", run_name="__main__")
