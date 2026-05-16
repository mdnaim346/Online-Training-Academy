{
    "name": "Training Academy",
    "version": "1.0",
    "license": "LGPL-3",
    "depends": ["base",
    "web",
    "mail",
    "website",
    "portal",],
    "data": [
        "security/training_security.xml",
        "security/ir.model.access.csv",
        "data/sequence.xml",
        "data/certificate_sequence.xml",
        "reports/certificate_template.xml",
        "reports/course_report_template.xml",
        "reports/enrollment_receipt_template.xml",
        "reports/payment_receipt_template.xml",
        "reports/certificate_report.xml",
        "reports/report_action.xml",
        "data/email_templates.xml",
        "views/training_course.xml",
        "views/training_trainer_views.xml",
        "views/training_attendance_views.xml",
        "views/training_student_views.xml",
        "views/training_enrollment_views.xml",
        "views/training_payment_views.xml",
        "views/training_payment_transaction_views.xml",
        "views/training_dashboard_menu.xml",
        "views/res_config_settings_views.xml",
        "views/website_traning_templates.xml",
        "views/portal_training_templates.xml",

        "data/cron.xml",
          

          
    
    ],
    "assets": {
        "web.assets_frontend": [
            "Training_academy_management_system/static/src/css/training_website.css",
        ],
        "web.assets_backend": [
             "https://cdn.jsdelivr.net/npm/chart.js",
            "Training_academy_management_system/static/src/css/training_dashboard.css",
            "Training_academy_management_system/static/src/js/training_dashboard.js",
            "Training_academy_management_system/static/src/xml/training_dashboard.xml",
        ],
    },
    "installable": True,
    "application": True,
}
