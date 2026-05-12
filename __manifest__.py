{
    "name": "Training Academy",
    "version": "1.0",
    "license": "LGPL-3",
    "depends": ["base", "web", "mail"],
    "data": [
        "security/training_security.xml",
        "security/ir.model.access.csv",
        "data/sequence.xml",
        "reports/certificate_template.xml",
        "reports/certificate_report.xml",
        "views/training_course.xml",
        "views/training_trainer_views.xml",
        "views/training_student_views.xml",
        "views/training_enrollment_views.xml",
        "views/training_dashboard_menu.xml",

        "reports/course_report_template.xml",
        "reports/enrollment_receipt_template.xml",
        "reports/report_action.xml",

        "data/cron.xml",
        "data/certificate_sequence.xml",
          

          
    
    ],
    "assets": {
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
