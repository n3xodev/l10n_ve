{
    "name": "Venezuela — Consulta RIF SENIAT (captcha)",
    "summary": "Botón en contactos para consultar datos del contribuyente en el portal BuscaRif del SENIAT.",
    "version": "20.0.1.0.0",
    "category": "Localization",
    "author": "andyengit",
    "maintainer": "andyengit",
    "website": "https://github.com/OCA/l10n-venezuela",
    "license": "AGPL-3",
    "depends": ["contacts", "l10n_ve_seniat", "l10n_ve_withholding"],
    "data": [
        "views/res_partner_views.xml",
    ],
    "external_dependencies": {
        "python": ["requests", "Pillow", "pytesseract"],
        "bin": ["tesseract"],
    },
    "installable": True,
    "application": False,
}
