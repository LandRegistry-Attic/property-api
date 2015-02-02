# coding=utf-8
import json
title = {
    "title_number": "TN1234567",
    "property_description" : {
        "template" : "The Freehold land shown edged with red on the plan of the above Title filed at the Registry and being *AD*",
        "full_text" : "The Freehold land shown edged with red on the plan of the above Title filed at the Registry and being 8 Miller Way, Plymouth, Devon, PL6 8UQ",
        "fields" : {"tenure": "freehold", "addresses" : [{"full_address": "8 Miller Way, Plymouth, Devon, PL6 8UQ", "house_no" : "8", "street_name" : "Miller Way", "town" : "Plymouth", "postal_county" : "Devon", "region_name" : "", "country" : "", "postcode":""}]},
        "deeds" : [],
        "notes" : []
    },

    "price_paid" : {
        "template" : "The price stated to have been paid on *DA* was *AM*.",
        "full_text" : "The price stated to have been paid on 15/11/2005 was £1000.",
        "fields" : {"date" : "15/11/2005", "amount" : "1000"},
        "deeds" : [],
        "notes" : []
    },

    "extent": {
        "crs": {
            "properties": {
                "name": "urn:ogc:def:crs:EPSG:27700"
            },
            "type": "name"
        },
        "geometry": {
            "coordinates": [
                [
                    [
                        [
                            530857.01,
                            181500
                        ],
                        [
                            530857,
                            181500
                        ],
                        [
                            530857,
                            181500
                        ],
                        [
                            530857,
                            181500
                        ],
                        [
                            530857.01,
                            181500
                        ]
                    ]
                ]
            ],
            "type": "MultiPolygon"
        },
        "properties": {},
        "type": "Feature"
    }
}

title1 = {
    "title_number": "TN7654321",
    "property_description" : {
        "template" : "The Freehold land shown edged with red on the plan of the above Title filed at the Registry and being *AD*",
        "full_text" : "The Freehold land shown edged with red on the plan of the above Title filed at the Registry and being 8 Miller Way, Plymouth, Devon, PL6 8UQ",
        "fields" : {"tenure": "freehold", "addresses" : [{"full_address": "10 Low St", "house_no" : "8", "street_name" : "Miller Way", "town" : "Plymouth", "postal_county" : "Devon", "region_name" : "", "country" : "", "postcode":""}]},
        "deeds" : [],
        "notes" : []
    },
    "price_paid" : {
        "template" : "The price stated to have been paid on *DA* was *AM*.",
        "full_text" : "The price stated to have been paid on 15/11/2005 was £1,000.",
        "fields" : {"date" :[ "15/11/2005"], "amount" : ["£1000"]},
        "deeds" : [],
        "notes" : []
    },

    "extent": {
        "crs": {
            "properties": {
                "name": "urn:ogc:def:crs:EPSG:27700"
            },
            "type": "name"
        },
        "geometry": {
            "coordinates": [
                [
                    [
                        [
                            530857.01,
                            181500
                        ],
                        [
                            530857,
                            181500
                        ],
                        [
                            530857,
                            181500
                        ],
                        [
                            530857,
                            181500
                        ],
                        [
                            530857.01,
                            181500
                        ]
                    ]
                ]
            ],
            "type": "MultiPolygon"
        },
        "properties": {},
        "type": "Feature"
    }
}

search_results = {"results" : [title]}
test_two_search_results = json.dumps({"results" : [title, title1]}, encoding='utf-8')
