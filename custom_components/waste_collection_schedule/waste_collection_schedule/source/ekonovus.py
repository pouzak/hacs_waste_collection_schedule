import datetime
import requests
from waste_collection_schedule import Collection
#from collection import Collection


TITLE = "Ekonovus"
DESCRIPTION = 'Source for UAB "Ekonovus"'
URL = "https://www.ekonovus.lt/aptarnavimo-grafikai/"
TEST_CASES = {
    "Vilniaus r. sav., Vilniaus m., Fabijoniškių g. 24-1": {
        "region": "Vilniaus r. sav.",
        "district":"Vilniaus m.",
        "street": "Fabijoniškių g.",
        "house_number": "24-1",
    },
     "Klaipėdos r. sav., Klemiškės II k., Pumpurų g. 5": {
        "region": "Klaipėdos r. sav.",
        "district":"Klemiškės II k.",
        "street": "Pumpurų g.",
        "house_number": "5",
        "waste_object_ids": ["55-L-39605", "55-P-29313"]
    },
}

ICON_MAP = {
    "Komunalinės": "mdi:trash-can",
    "Pakuotė": "mdi:recycle",
    "Stiklas": "mdi:glass-fragile",
    "Žaliųjų atliekų": "mdi:leaf",
}

class Source:
    API_URL = "https://wabi-west-europe-d-primary-api.analysis.windows.net/public/reports/querydata?synchronous=true"

    def __init__(
        self, region, district, street, house_number, waste_object_ids=None, powerbi_resource_key=None
    ):
        if waste_object_ids is None:
            waste_object_ids = []
        self._region = region
        self._district = district
        self._street = street
        self._house_number = str(house_number)
        self._waste_object_ids = waste_object_ids
        self._valid_waste_object_ids = []
        self._powerbi_resource_key = powerbi_resource_key if powerbi_resource_key != None else "d86dc3d4-e915-4460-b12e-c925d3ae6c75"

    def fetch(self):
        headers = {"X-PowerBI-ResourceKey": self._powerbi_resource_key}
        
        r = requests.post(
            self.API_URL,
            json=self.get_waste_object_ids(),
            headers=headers
        )

        data = r.json()
        self.check_for_error_status(data)

        for i in data['results'][0]['result']['data']['dsr']['DS'][0]['PH'][0]['DM0']:
            if len(self._waste_object_ids) == 0:
                self._valid_waste_object_ids.append(i['G0'])
            else:
                id = i['G0'].split(" ")[0]
                if id in self._waste_object_ids:
                    self._valid_waste_object_ids.append(i['G0'])

        entries = []
        for collection in self._valid_waste_object_ids:
            type =  collection[collection.find("(")+1:collection.find(")")]
            id = collection.split(" ")[0]
            r = requests.post(
                self.API_URL,
                json=self.get_waste_object_data(collection),
                headers=headers
            )
            data = r.json()
            self.check_for_error_status(data)
            date_arr = data['results'][0]['result']['data']['dsr']['DS'][0]['PH'][0]['DM0'][0]['M0'].replace(".","").split(",")
            for date in date_arr:
                split = date.split('-')
                entries.append(
                    Collection(
                        date=datetime.datetime(int(split[0]), int(split[1]), int(split[2])).date(),
                        t=type,
                        icon=ICON_MAP.get(type),
                    )
                )
        return entries


    def check_for_error_status(self, collection):
        if "error" in collection:
            raise Exception(
                "Error: failed to fetch get data, got status: {}".format(
                    collection["error"]["message"]
                )
            )
    def get_waste_object_data(self, waste_object):
        return {
            "version": "1.0.0",
            "queries": [
                {
                    "Query": {
                        "Commands": [
                            {
                                "SemanticQueryDataShapeCommand": {
                                    "Query": {
                                        "Version": 2,
                                        "From": [
                                            {
                                                "Name": "s",
                                                "Entity": "ScheduleDates",
                                                "Type": 0
                                            },
                                            {
                                                "Name": "w",
                                                "Entity": "WasteObject",
                                                "Type": 0
                                            },
                                            {
                                                "Name": "a",
                                                "Entity": "AllAddresses",
                                                "Type": 0
                                            },
                                            {
                                                "Name": "t",
                                                "Entity": "Teritorijos konteinerių tvarkaraščiams",
                                                "Type": 0
                                            },
                                            {
                                                "Name": "s1",
                                                "Entity": "Schedule",
                                                "Type": 0
                                            }
                                        ],
                                        "Select": [
                                            {
                                                "Measure": {
                                                    "Expression": {
                                                        "SourceRef": {
                                                            "Source": "s"
                                                        }
                                                    },
                                                    "Property": "Datos"
                                                },
                                                "Name": "ScheduleDates.Datos"
                                            }
                                        ],
                                        "Where": [
                                            {
                                                "Condition": {
                                                    "In": {
                                                        "Expressions": [
                                                            {
                                                                "Column": {
                                                                    "Expression": {
                                                                        "SourceRef": {
                                                                            "Source": "w"
                                                                        }
                                                                    },
                                                                    "Property": "Adresas"
                                                                }
                                                            }
                                                        ],
                                                        "Values": [
                                                            [
                                                                {
                                                                    "Literal": {
                                                                        "Value": f"'{self._district} {self._street} {self._house_number}'"
                                                                    }
                                                                }
                                                            ]
                                                        ]
                                                    }
                                                }
                                            },
                                            {
                                                "Condition": {
                                                    "In": {
                                                        "Expressions": [
                                                            {
                                                                "Column": {
                                                                    "Expression": {
                                                                        "SourceRef": {
                                                                            "Source": "w"
                                                                        }
                                                                    },
                                                                    "Property": "Inventorinis nr."
                                                                }
                                                            }
                                                        ],
                                                        "Values": [
                                                            [
                                                                {
                                                                    "Literal": {
                                                                        "Value": f"'{waste_object}'"
                                                                    }
                                                                }
                                                            ]
                                                        ]
                                                    }
                                                }
                                            },
                                            {
                                                "Condition": {
                                                    "In": {
                                                        "Expressions": [
                                                            {
                                                                "Column": {
                                                                    "Expression": {
                                                                        "SourceRef": {
                                                                            "Source": "a"
                                                                        }
                                                                    },
                                                                    "Property": "District"
                                                                }
                                                            }
                                                        ],
                                                        "Values": [
                                                            [
                                                                {
                                                                    "Literal": {
                                                                        "Value": f"'{self._region}'"
                                                                    }
                                                                }
                                                            ]
                                                        ]
                                                    }
                                                }
                                            },
                                            {
                                                "Condition": {
                                                    "In": {
                                                        "Expressions": [
                                                            {
                                                                "Column": {
                                                                    "Expression": {
                                                                        "SourceRef": {
                                                                            "Source": "s"
                                                                        }
                                                                    },
                                                                    "Property": "Future"
                                                                }
                                                            }
                                                        ],
                                                        "Values": [
                                                            [
                                                                {
                                                                    "Literal": {
                                                                        "Value": "'true'"
                                                                    }
                                                                }
                                                            ]
                                                        ]
                                                    }
                                                }
                                            },
                                            {
                                                "Condition": {
                                                    "In": {
                                                        "Expressions": [
                                                            {
                                                                "Column": {
                                                                    "Expression": {
                                                                        "SourceRef": {
                                                                            "Source": "t"
                                                                        }
                                                                    },
                                                                    "Property": "Rodomas tvarkaraštis"
                                                                }
                                                            }
                                                        ],
                                                        "Values": [
                                                            [
                                                                {
                                                                    "Literal": {
                                                                        "Value": "'1'"
                                                                    }
                                                                }
                                                            ]
                                                        ]
                                                    }
                                                }
                                            },
                                            {
                                                "Condition": {
                                                    "In": {
                                                        "Expressions": [
                                                            {
                                                                "Column": {
                                                                    "Expression": {
                                                                        "SourceRef": {
                                                                            "Source": "s"
                                                                        }
                                                                    },
                                                                    "Property": "OverNextRun"
                                                                }
                                                            }
                                                        ],
                                                        "Values": [
                                                            [
                                                                {
                                                                    "Literal": {
                                                                        "Value": "true"
                                                                    }
                                                                }
                                                            ]
                                                        ]
                                                    }
                                                }
                                            },
                                            {
                                                "Condition": {
                                                    "Not": {
                                                        "Expression": {
                                                            "In": {
                                                                "Expressions": [
                                                                    {
                                                                        "Column": {
                                                                            "Expression": {
                                                                                "SourceRef": {
                                                                                    "Source": "s1"
                                                                                }
                                                                            },
                                                                            "Property": "ScheduleId"
                                                                        }
                                                                    }
                                                                ],
                                                                "Values": [
                                                                    [
                                                                        {
                                                                            "Literal": {
                                                                                "Value": "7127L"
                                                                            }
                                                                        }
                                                                    ],
                                                                    [
                                                                        {
                                                                            "Literal": {
                                                                                "Value": "7128L"
                                                                            }
                                                                        }
                                                                    ],
                                                                    [
                                                                        {
                                                                            "Literal": {
                                                                                "Value": "7129L"
                                                                            }
                                                                        }
                                                                    ],
                                                                    [
                                                                        {
                                                                            "Literal": {
                                                                                "Value": "7131L"
                                                                            }
                                                                        }
                                                                    ],
                                                                    [
                                                                        {
                                                                            "Literal": {
                                                                                "Value": "7132L"
                                                                            }
                                                                        }
                                                                    ],
                                                                    [
                                                                        {
                                                                            "Literal": {
                                                                                "Value": "7133L"
                                                                            }
                                                                        }
                                                                    ],
                                                                    [
                                                                        {
                                                                            "Literal": {
                                                                                "Value": "7134L"
                                                                            }
                                                                        }
                                                                    ],
                                                                    [
                                                                        {
                                                                            "Literal": {
                                                                                "Value": "7135L"
                                                                            }
                                                                        }
                                                                    ],
                                                                    [
                                                                        {
                                                                            "Literal": {
                                                                                "Value": "7136L"
                                                                            }
                                                                        }
                                                                    ],
                                                                    [
                                                                        {
                                                                            "Literal": {
                                                                                "Value": "7137L"
                                                                            }
                                                                        }
                                                                    ],
                                                                    [
                                                                        {
                                                                            "Literal": {
                                                                                "Value": "7138L"
                                                                            }
                                                                        }
                                                                    ],
                                                                    [
                                                                        {
                                                                            "Literal": {
                                                                                "Value": "7139L"
                                                                            }
                                                                        }
                                                                    ],
                                                                    [
                                                                        {
                                                                            "Literal": {
                                                                                "Value": "7140L"
                                                                            }
                                                                        }
                                                                    ],
                                                                    [
                                                                        {
                                                                            "Literal": {
                                                                                "Value": "7141L"
                                                                            }
                                                                        }
                                                                    ]
                                                                ]
                                                            }
                                                        }
                                                    }
                                                }
                                            },
                                            {
                                                "Condition": {
                                                    "And": {
                                                        "Left": {
                                                            "Not": {
                                                                "Expression": {
                                                                    "Contains": {
                                                                        "Left": {
                                                                            "Column": {
                                                                                "Expression": {
                                                                                    "SourceRef": {
                                                                                        "Source": "w"
                                                                                    }
                                                                                },
                                                                                "Property": "Inventorinis nr."
                                                                            }
                                                                        },
                                                                        "Right": {
                                                                            "Literal": {
                                                                                "Value": "'siuk'"
                                                                            }
                                                                        }
                                                                    }
                                                                }
                                                            }
                                                        },
                                                        "Right": {
                                                            "Not": {
                                                                "Expression": {
                                                                    "Contains": {
                                                                        "Left": {
                                                                            "Column": {
                                                                                "Expression": {
                                                                                    "SourceRef": {
                                                                                        "Source": "w"
                                                                                    }
                                                                                },
                                                                                "Property": "Inventorinis nr."
                                                                            }
                                                                        },
                                                                        "Right": {
                                                                            "Literal": {
                                                                                "Value": "'šiuk'"
                                                                            }
                                                                        }
                                                                    }
                                                                }
                                                            }
                                                        }
                                                    }
                                                }
                                            }
                                        ]
                                    },
                                    "Binding": {
                                        "Primary": {
                                            "Groupings": [
                                                {
                                                    "Projections": [
                                                        0
                                                    ]
                                                }
                                            ]
                                        },
                                        "DataReduction": {
                                            "DataVolume": 3,
                                            "Primary": {
                                                "Top": {}
                                            }
                                        },
                                        "Version": 1
                                    },
                                    "ExecutionMetricsKind": 1
                                }
                            }
                        ]
                    },
                    "QueryId": "",
                    "ApplicationContext": {
                        "DatasetId": "90015897-045e-4f68-8f83-c40d1fc3bfc2",
                        "Sources": [
                            {
                                "ReportId": "06fc8043-9afa-43d6-88cc-3a1e73aaf964",
                                "VisualId": "161c6ed98b10564c91b7"
                            }
                        ]
                    }
                }
            ],
            "cancelQueries": [],
            "modelId": 1026609
        }
    
    def get_waste_object_ids(self):
        return {
                "version": "1.0.0",
                "queries": [
                    {
                        "Query": {
                            "Commands": [
                                {
                                    "SemanticQueryDataShapeCommand": {
                                        "Query": {
                                            "Version": 2,
                                            "From": [
                                                {
                                                    "Name": "w",
                                                    "Entity": "WasteObject",
                                                    "Type": 0
                                                },
                                                {
                                                    "Name": "a",
                                                    "Entity": "AllAddresses",
                                                    "Type": 0
                                                },
                                                {
                                                    "Name": "s",
                                                    "Entity": "ScheduleDates",
                                                    "Type": 0
                                                },
                                                {
                                                    "Name": "t",
                                                    "Entity": "Teritorijos konteinerių tvarkaraščiams",
                                                    "Type": 0
                                                },
                                                {
                                                    "Name": "s1",
                                                    "Entity": "Schedule",
                                                    "Type": 0
                                                }
                                            ],
                                            "Select": [
                                                {
                                                    "Column": {
                                                        "Expression": {
                                                            "SourceRef": {
                                                                "Source": "w"
                                                            }
                                                        },
                                                        "Property": "Inventorinis nr."
                                                    },
                                                    "Name": "WasteObject.reikia"
                                                }
                                            ],
                                            "Where": [
                                                {
                                                    "Condition": {
                                                        "In": {
                                                            "Expressions": [
                                                                {
                                                                    "Column": {
                                                                        "Expression": {
                                                                            "SourceRef": {
                                                                                "Source": "w"
                                                                            }
                                                                        },
                                                                        "Property": "Adresas"
                                                                    }
                                                                }
                                                            ],
                                                            "Values": [
                                                                [
                                                                    {
                                                                        "Literal": {
                                                                            # "Value": "'Radikių k. Lėtos g. 13'"
                                                                            "Value": f"'{self._district} {self._street} {self._house_number}'"
                                                                        }
                                                                    }
                                                                ]
                                                            ]
                                                        }
                                                    }
                                                },
                                                {
                                                    "Condition": {
                                                        "In": {
                                                            "Expressions": [
                                                                {
                                                                    "Column": {
                                                                        "Expression": {
                                                                            "SourceRef": {
                                                                                "Source": "a"
                                                                            }
                                                                        },
                                                                        "Property": "District"
                                                                    }
                                                                }
                                                            ],
                                                            "Values": [
                                                                [
                                                                    {
                                                                        "Literal": {
                                                                             "Value":f"'{self._region}'"
                                                                            # # "Value": "'Kauno r. sav.'"
                                                                        }
                                                                    }
                                                                ]
                                                            ]
                                                        }
                                                    }
                                                },
                                                {
                                                    "Condition": {
                                                        "In": {
                                                            "Expressions": [
                                                                {
                                                                    "Column": {
                                                                        "Expression": {
                                                                            "SourceRef": {
                                                                                "Source": "s"
                                                                            }
                                                                        },
                                                                        "Property": "Future"
                                                                    }
                                                                }
                                                            ],
                                                            "Values": [
                                                                [
                                                                    {
                                                                        "Literal": {
                                                                            "Value": "'true'"
                                                                        }
                                                                    }
                                                                ]
                                                            ]
                                                        }
                                                    }
                                                },
                                                {
                                                    "Condition": {
                                                        "In": {
                                                            "Expressions": [
                                                                {
                                                                    "Column": {
                                                                        "Expression": {
                                                                            "SourceRef": {
                                                                                "Source": "t"
                                                                            }
                                                                        },
                                                                        "Property": "Rodomas tvarkaraštis"
                                                                    }
                                                                }
                                                            ],
                                                            "Values": [
                                                                [
                                                                    {
                                                                        "Literal": {
                                                                            "Value": "'1'"
                                                                        }
                                                                    }
                                                                ]
                                                            ]
                                                        }
                                                    }
                                                },
                                                {
                                                    "Condition": {
                                                        "In": {
                                                            "Expressions": [
                                                                {
                                                                    "Column": {
                                                                        "Expression": {
                                                                            "SourceRef": {
                                                                                "Source": "s"
                                                                            }
                                                                        },
                                                                        "Property": "OverNextRun"
                                                                    }
                                                                }
                                                            ],
                                                            "Values": [
                                                                [
                                                                    {
                                                                        "Literal": {
                                                                            "Value": "true"
                                                                        }
                                                                    }
                                                                ]
                                                            ]
                                                        }
                                                    }
                                                },
                                                {
                                                    "Condition": {
                                                        "Not": {
                                                            "Expression": {
                                                                "In": {
                                                                    "Expressions": [
                                                                        {
                                                                            "Column": {
                                                                                "Expression": {
                                                                                    "SourceRef": {
                                                                                        "Source": "s1"
                                                                                    }
                                                                                },
                                                                                "Property": "ScheduleId"
                                                                            }
                                                                        }
                                                                    ],
                                                                    "Values": [
                                                                        [
                                                                            {
                                                                                "Literal": {
                                                                                    "Value": "7127L"
                                                                                }
                                                                            }
                                                                        ],
                                                                        [
                                                                            {
                                                                                "Literal": {
                                                                                    "Value": "7128L"
                                                                                }
                                                                            }
                                                                        ],
                                                                        [
                                                                            {
                                                                                "Literal": {
                                                                                    "Value": "7129L"
                                                                                }
                                                                            }
                                                                        ],
                                                                        [
                                                                            {
                                                                                "Literal": {
                                                                                    "Value": "7131L"
                                                                                }
                                                                            }
                                                                        ],
                                                                        [
                                                                            {
                                                                                "Literal": {
                                                                                    "Value": "7132L"
                                                                                }
                                                                            }
                                                                        ],
                                                                        [
                                                                            {
                                                                                "Literal": {
                                                                                    "Value": "7133L"
                                                                                }
                                                                            }
                                                                        ],
                                                                        [
                                                                            {
                                                                                "Literal": {
                                                                                    "Value": "7134L"
                                                                                }
                                                                            }
                                                                        ],
                                                                        [
                                                                            {
                                                                                "Literal": {
                                                                                    "Value": "7135L"
                                                                                }
                                                                            }
                                                                        ],
                                                                        [
                                                                            {
                                                                                "Literal": {
                                                                                    "Value": "7136L"
                                                                                }
                                                                            }
                                                                        ],
                                                                        [
                                                                            {
                                                                                "Literal": {
                                                                                    "Value": "7137L"
                                                                                }
                                                                            }
                                                                        ],
                                                                        [
                                                                            {
                                                                                "Literal": {
                                                                                    "Value": "7138L"
                                                                                }
                                                                            }
                                                                        ],
                                                                        [
                                                                            {
                                                                                "Literal": {
                                                                                    "Value": "7139L"
                                                                                }
                                                                            }
                                                                        ],
                                                                        [
                                                                            {
                                                                                "Literal": {
                                                                                    "Value": "7140L"
                                                                                }
                                                                            }
                                                                        ],
                                                                        [
                                                                            {
                                                                                "Literal": {
                                                                                    "Value": "7141L"
                                                                                }
                                                                            }
                                                                        ]
                                                                    ]
                                                                }
                                                            }
                                                        }
                                                    }
                                                },
                                                {
                                                    "Condition": {
                                                        "And": {
                                                            "Left": {
                                                                "Not": {
                                                                    "Expression": {
                                                                        "Contains": {
                                                                            "Left": {
                                                                                "Column": {
                                                                                    "Expression": {
                                                                                        "SourceRef": {
                                                                                            "Source": "w"
                                                                                        }
                                                                                    },
                                                                                    "Property": "Inventorinis nr."
                                                                                }
                                                                            },
                                                                            "Right": {
                                                                                "Literal": {
                                                                                    "Value": "'siuk'"
                                                                                }
                                                                            }
                                                                        }
                                                                    }
                                                                }
                                                            },
                                                            "Right": {
                                                                "Not": {
                                                                    "Expression": {
                                                                        "Contains": {
                                                                            "Left": {
                                                                                "Column": {
                                                                                    "Expression": {
                                                                                        "SourceRef": {
                                                                                            "Source": "w"
                                                                                        }
                                                                                    },
                                                                                    "Property": "Inventorinis nr."
                                                                                }
                                                                            },
                                                                            "Right": {
                                                                                "Literal": {
                                                                                    "Value": "'šiuk'"
                                                                                }
                                                                            }
                                                                        }
                                                                    }
                                                                }
                                                            }
                                                        }
                                                    }
                                                }
                                            ]
                                        },
                                        "Binding": {
                                            "Primary": {
                                                "Groupings": [
                                                    {
                                                        "Projections": [
                                                            0
                                                        ]
                                                    }
                                                ]
                                            },
                                            "DataReduction": {
                                                "DataVolume": 3,
                                                "Primary": {
                                                    "Window": {}
                                                }
                                            },
                                            "IncludeEmptyGroups": True,
                                            "Version": 1
                                        },
                                        "ExecutionMetricsKind": 1
                                    }
                                }
                            ]
                        },
                        "QueryId": "",
                        "ApplicationContext": {
                            "DatasetId": "90015897-045e-4f68-8f83-c40d1fc3bfc2",
                            "Sources": [
                                {
                                    "ReportId": "06fc8043-9afa-43d6-88cc-3a1e73aaf964",
                                    "VisualId": "cfba850d0ce48eb9e44d"
                                }
                            ]
                        }
                    }
                ],
                "cancelQueries": [],
                "modelId": 1026609
            }
