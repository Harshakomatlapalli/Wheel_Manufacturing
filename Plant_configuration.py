import random
wheel_config = {
"Family_A" : {
    "probability" : 0.50,
    "Casting_time" : lambda: random.lognormvariate(mu = 1.6044 , sigma = 0.0997), #dynamic evaluation new random sample for every single wheel #real mean is 5 min and std is 30 sec
    "NDT_time" : lambda: random.uniform(0.50,1),
    "machining_time" : lambda: random.weibullvariate(alpha = 6.0, beta = 4.0), 
    "ht_slot" : 1,
    "Airleak_time" : lambda: 1,
    "Sandblasting_time" : lambda:1,
    "Paintline_pretreatment" : lambda: random.gauss(30,2),
    "Paintline_primer": lambda: random.gauss(40,3),
    "Paintline_color" : lambda: random.gauss(30,2),
    "PL_QC": lambda: random.triangular(0.5, 2.0, 1.0),
    "ndt_scrap_rate": 0.02,
    "air_leak_scrap_rate" : 0.01,
    "paint_line_scrap_rate" : 0.05
},
"Family_B" :{
    "probability" : 0.35,
    "Casting_time" : lambda: random.lognormvariate(mu = 1.9434 , sigma = 0.0713), # Real parameters inverse of natural log mean is 7 min and std is 30 sec
    "NDT_time" : lambda: random.uniform(0.75,1),
    "machining_time" : lambda : random.weibullvariate(alpha = 6.0, beta = 5.5), 
    "ht_slot" : 1.5,
    "Airleak_time": lambda:1,
    "Sandblasting_time": lambda: 1,
    "Paintline_pretreatment" : lambda: random.gauss(30,2),
    "Paintline_primer": lambda: random.gauss(40,3),
    "Paintline_color" : lambda: random.gauss(30,2),
    "PL_QC": lambda: random.triangular(1.0, 2.5, 1.5),
    "ndt_scrap_rate": 0.05,
    "air_leak_scrap_rate" : 0.01,
    "paint_line_scrap_rate" : 0.08,
},
"Family_C" :
{
    "probability" : 0.15,
    "Casting_time" : lambda: random.lognormvariate(mu = 2.3013 , sigma = 0.05), # Real parameters mean is 10 min and std is 30 sec
    "NDT_time" : lambda: random.uniform(0.85,1),
    "machining_time" : lambda: random.weibullvariate(alpha = 6.0, beta = 7), 
    "ht_slot" : 2,
    "Airleak_time" : lambda: 1,
    "Sandblasting_time" : lambda: 1,
    "Paintline_pretreatment" : lambda: random.gauss(30,2),
    "Paintline_primer": lambda: random.gauss(40,3),
    "Paintline_color" : lambda: random.gauss(30,2),
    "PL_QC": lambda: random.triangular(2.0, 3.0, 2.5),
    "ndt_scrap_rate": 0.09,
    "air_leak_scrap_rate" : 0.02,
    "paint_line_scrap_rate" : 0.10,
}
}

Family = list(wheel_config.keys())
Family_probability = [data["probability"] for data in wheel_config.values() if "probability" in data]
