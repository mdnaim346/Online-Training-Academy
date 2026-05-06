# -*- coding: utf-8 -*-
{
    'name' : 'Training Academy',
    'version' : '1.0',
    'sequence': 10,
    'summary': 'Simple Training Academy',
    'description': "",
    'depends': ['web'],
    'data': [
        'security/ir.model.access.csv',
        'views/training_course.xml',
       
        
    ],
    
    'installable': True,
    'application': True,
   
    'assets': {
       
        'web.assets_backend': [
            
            
        ],
        'web.assets_frontend': [
           
        ],
        
    },
    
}
