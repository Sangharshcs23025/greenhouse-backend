"""
Maps predicted tomato disease classes to farmer-facing advice.
Order MUST match class_names.json exactly, since the model predicts
by index, not by name.
"""

DISEASE_TREATMENTS = {
    "Bacterial Spot": {
        "description": "Bacterial infection causing small dark, water-soaked spots with yellow halos on leaves and fruit.",
        "treatment": "Apply a copper-based bactericide (e.g. copper oxychloride) every 7-10 days. Remove and destroy severely infected leaves.",
        "prevention": "Avoid overhead watering and handling wet plants. Disinfect tools between plants. Use disease-free seeds/transplants.",
    },
    "Early Blight": {
        "description": "Fungal disease causing dark concentric ring spots, usually starting on lower/older leaves.",
        "treatment": "Remove and destroy infected leaves immediately. Apply a fungicide containing chlorothalonil or copper every 7-10 days.",
        "prevention": "Ensure good air circulation between plants, avoid overhead watering, mulch to prevent soil splash onto leaves, rotate crops yearly.",
    },
    "Healthy": {
        "description": "No disease detected — plant appears healthy.",
        "treatment": "No action needed.",
        "prevention": "Continue current care routine and monitor regularly.",
    },
    "Late Blight": {
        "description": "Aggressive, fast-spreading fungal-like disease (Phytophthora) causing water-soaked lesions; can destroy a crop within days in humid conditions.",
        "treatment": "Remove and destroy infected plants immediately to prevent spread — this disease spreads very fast. Apply a fungicide containing mancozeb or copper hydroxide preventively on remaining plants.",
        "prevention": "Avoid overhead irrigation, ensure good drainage, monitor humidity closely (this disease thrives above 90% humidity with cool temperatures).",
    },
    "Septoria Leaf Spot": {
        "description": "Fungal disease causing many small circular spots with dark borders and gray/tan centers, typically starting on lower leaves.",
        "treatment": "Remove infected lower leaves. Apply a fungicide containing chlorothalonil or copper every 7-10 days, especially during wet weather.",
        "prevention": "Avoid overhead watering, stake/prune plants for airflow, remove plant debris at end of season, rotate crops.",
    },
    "Yellow Leaf Curl Virus": {
        "description": "Viral disease transmitted by whiteflies, causing upward leaf curling, yellowing, and stunted growth.",
        "treatment": "No cure once infected — remove and destroy infected plants to prevent spread to healthy ones. Control whitefly populations urgently (see prevention).",
        "prevention": "Control whiteflies using yellow sticky traps and/or insecticidal soap/neem oil. Use virus-resistant tomato varieties if available. Use insect netting in the greenhouse.",
    },
}


def get_treatment(disease_class: str):
    return DISEASE_TREATMENTS.get(
        disease_class,
        {
            "description": "Unrecognized condition.",
            "treatment": "Consult a local agricultural expert for accurate diagnosis.",
            "prevention": "N/A",
        },
    )