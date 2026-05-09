{
    "name": "Training Academy",
    "version": "1.0",
    "license": "LGPL-3",
    "depends": ["base"],
    "data": [
        "security/training_security.xml",
        "security/ir.model.access.csv",
        "data/sequence.xml",
        "views/training_course.xml",
        "views/training_trainer_views.xml",
        "views/training_student_views.xml",
        "views/training_enrollment_views.xml",
    ],
    "installable": True,
    "application": True,
}
