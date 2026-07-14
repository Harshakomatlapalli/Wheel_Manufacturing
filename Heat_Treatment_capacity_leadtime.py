import simpy
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import random
from Plant_configuration import wheel_config, Family_probability, Family
from Equipment_state_Setup_change import calculate_machinesetup_time, plantAssetstate
from Metrics import cumulative_busy_time, log_stage_metrics, metrics_log

def casting_stage_process(env,wheel_data, resources):
    cfg = wheel_config[wheel_data["family"]]

    # Casting Process & NDT Process
    t_casting_arrival = env.now

    with resources["casting"].request() as req:
        yield req

        t_casting_start = env.now

        casting_id = next((i for i, avail in plant_state.casting_machine_available.items() if avail), None) # 1, 2, 3.....
        if casting_id is not None:
            plant_state.casting_machine_available[casting_id] = False
            prev_family = plant_state.last_family_casting_machine[casting_id]
            if prev_family is not None and prev_family != wheel_data["family"]:
                setup_delay = random.lognormvariate(mu= 5.46 , sigma = 0.2) # realtime mean = 240 min & std = 45 min
                yield env.timeout(setup_delay)
        plant_state.last_family_casting_machine[casting_id] = wheel_data["family"]
        yield env.timeout(cfg["Casting_time"]()) #variation for every wheel
        plant_state.casting_machine_available[casting_id] = True

        wheel_casted =  env.now

        log_stage_metrics(env = env, wheel_data = wheel_data ,wheel_casted = wheel_casted,stage_name = "Casting", start_queue_time = t_casting_arrival, start_proc_time = t_casting_start, resource_obj = resources["casting"], status = "Casted")

    # NDT process
    t_ndt_arrival = env.now
    with resources["NDT"].request() as req:
        yield req
        t_ndt_start = env.now
        yield env.timeout(cfg["NDT_time"]()) #variation for every wheel otherwise it is just int

        if random.random() < cfg["ndt_scrap_rate"]:  # Wheel vanishies from the system- In relaity these are collected and looped back
            log_stage_metrics(env = env,wheel_data = wheel_data, wheel_casted = wheel_casted, stage_name = "NDT", start_queue_time = t_ndt_arrival, start_proc_time = t_ndt_start, resource_obj = resources["NDT"], status = "Scrapped")
            return
        else:
            log_stage_metrics(env = env,wheel_data = wheel_data,wheel_casted = wheel_casted, stage_name = "NDT", start_queue_time = t_ndt_arrival, start_proc_time = t_ndt_start, resource_obj = resources["NDT"], status = "Passed")
            
        
    env.process(Ht_load.load_wheel(env, wheel_data, wheel_casted,resources))

#Machning and Air Leak process
def machining_process(env, wheel_data, wheel_casted, resources):
    cfg = wheel_config[wheel_data["family"]]
    t_machining_arrival = env.now

    with resources["Machining"].request() as req:
        yield req
        t_machining_start = env.now
        machine_id = next((i for i,avail in plant_state.machining_available.items() if avail),None)

        if machine_id is not None:
            plant_state.machining_available[machine_id] = False
            from_family = plant_state.last_family_on_machining[machine_id]
            to_family = wheel_data["family"]
            setup_time = calculate_machinesetup_time(from_family,to_family)
            yield env.timeout(setup_time)
            
        plant_state.last_family_on_machining[machine_id] = wheel_data["family"]

        #Machining cycle time
        yield env.timeout(cfg["machining_time"]())
        plant_state.machining_available[machine_id] = True

        log_stage_metrics(env = env, wheel_data = wheel_data,wheel_casted = wheel_casted, stage_name = "Machining", start_queue_time = t_machining_arrival, start_proc_time = t_machining_start, resource_obj = resources["Machining"], status = "Machined")

    #Air Leak process
    t_airleak_arrival = env.now

    with resources["Airleak"].request() as req:
        yield req
        t_airleak_start = env.now
        yield env.timeout(cfg["Airleak_time"]())

        if random.random() < cfg["air_leak_scrap_rate"]:
            log_stage_metrics( env = env, wheel_data = wheel_data,wheel_casted = wheel_casted, stage_name = "Airleak", start_queue_time = t_airleak_arrival, start_proc_time = t_airleak_start, resource_obj = resources["Airleak"], status = "Scrapped")
            return
        else:
            log_stage_metrics(env = env, wheel_data = wheel_data, wheel_casted = wheel_casted, stage_name = "Airleak", start_queue_time = t_airleak_arrival, start_proc_time = t_airleak_start, resource_obj = resources["Airleak"], status = "Passed")


    env.process(paintline(env, wheel_data,wheel_casted, resources))

def paintline(env,wheel_data,wheel_casted, resources):
    cfg = wheel_config[wheel_data["family"]]
    t_sandblasting_arrival = env.now

    with resources["Sandblasting"].request() as req:
        yield req
        t_sandblasting_start = env.now
        yield env.timeout(cfg["Sandblasting_time"]())
    log_stage_metrics(env = env,wheel_data = wheel_data,wheel_casted = wheel_casted,  stage_name = "SandBlasting", start_queue_time = t_sandblasting_arrival, start_proc_time = t_sandblasting_start, resource_obj = resources["Sandblasting"], status = "SandBlasting")

# As there is single paintline, primer would take longer time, then followed by bake & clear
    # Wheels goes for Pre-Treatment & Chemical Prep
    t_paintline_ptarrival = env.now
    with resources["pretreatment"].request() as req:
        yield req
        t_paintline_ptstart = env.now
        yield env.timeout(cfg["Paintline_pretreatment"]())
    log_stage_metrics(env = env,wheel_data = wheel_data,wheel_casted = wheel_casted,  stage_name = "Paintline_Pretreatment", start_queue_time = t_paintline_ptarrival, start_proc_time = t_paintline_ptstart, resource_obj = resources["pretreatment"], status = "pretreament_completed")
    # Wheels goes for Primer Application & Bake
    t_paintline_primerarrival = env.now
    with resources["primer"].request() as req:
        yield req
        t_paintline_primerstart = env.now
        yield env.timeout(cfg["Paintline_primer"]())
    log_stage_metrics(env = env,wheel_data = wheel_data,wheel_casted = wheel_casted,  stage_name = "Paintline_Primer", start_queue_time = t_paintline_primerarrival, start_proc_time = t_paintline_primerstart, resource_obj = resources["primer"], status = "primer_completed")
    # Wheels goes for Base coat & liquid clear
    t_paintline_colorarrival = env.now
    with resources["color"].request() as req:
        yield req
        t_paintline_colorstart = env.now
        yield env.timeout(cfg["Paintline_color"]())
    log_stage_metrics(env = env,wheel_data = wheel_data, wheel_casted = wheel_casted,  stage_name = "Paintline_Color", start_queue_time = t_paintline_colorarrival, start_proc_time = t_paintline_colorstart, resource_obj = resources["color"], status = "painted")

    # Paint Line QC
    t_PLQC_arrival = env.now
    with resources["PL_QC"].request() as req:
        yield req
        t_PLQC_start = env.now
        yield env.timeout(cfg["PL_QC"]())

        if random.random() < cfg["paint_line_scrap_rate"]:
            log_stage_metrics(env = env,wheel_data = wheel_data,wheel_casted = wheel_casted,stage_name = "Paintline_QC", start_queue_time = t_PLQC_arrival, start_proc_time = t_PLQC_start, resource_obj = resources["PL_QC"], status = "Scrapped")
            return
        else:
            log_stage_metrics(env = env,wheel_data = wheel_data,wheel_casted = wheel_casted,stage_name = "Paintline_QC", start_queue_time = t_PLQC_arrival, start_proc_time = t_PLQC_start, resource_obj = resources["PL_QC"], status = "Passed")

    #Packing
    t_Packing_arrival = env.now
    with resources["packing"].request() as req:
        yield req
        t_Packing_start = env.now
        yield env.timeout(random.uniform(1.0, 2.5)) #Box Packing

        log_stage_metrics(env = env,wheel_data = wheel_data,wheel_casted = wheel_casted, start_queue_time = t_Packing_arrival, start_proc_time = t_Packing_start, resource_obj = resources["packing"], stage_name = "Packing", status = "Shipment_ready")


def wheel_arrival_generator(env, resources):
    wheel_id = 0
    while True:
        family = random.choices(Family, weights= Family_probability)[0]
        batch_processing = random.choice([1200,1600,2000])  # Production order 

        for _ in range(batch_processing):
            wheel_id += 1
            yield env.timeout(1)
            wheel_data = {
                "id" : wheel_id,
                "family" : family
            }
            env.process(casting_stage_process(env, wheel_data, resources))

#To Tackle Heat treament process and capacity restrictions

class HT:
    def __init__(self, env , capacity):
        self.env = env
        self.max_slots = capacity
        self.queue = []  # queue for wheels waiting for HT
        
        # Physical chamber gatekeepers
        self.solution = simpy.Resource(env, capacity=1)
        self.quench = simpy.Resource(env, capacity=1)
        self.aging = simpy.Resource(env, capacity=1)
        
        self.env.process(self.furnace_manager())

    def load_wheel(self, env, wheel_data,wheel_casted, resources):
        t_HT_arrival = env.now
        wheel_done_event = env.event()
        true_ht_queue_at_entry = len(self.queue) + 1
        
        # Append the wheel to the queue and wait
        self.queue.append((wheel_data,wheel_casted, t_HT_arrival, wheel_done_event, true_ht_queue_at_entry))
        
        # Catch the index value passed from the pipeline to stagger downstream entry
        unload_index = yield wheel_done_event
        
        
        # Move to machining
        self.env.process(machining_process(self.env, wheel_data,wheel_casted, resources))

    def furnace_manager(self):
        while True:
            slots_waiting = sum(wheel_config[item[0]["family"]]["ht_slot"] for item in self.queue)
            #Check if the solution chamber is occupied instead of checking 'is_baking'
            if slots_waiting < self.max_slots or self.solution.count > 0:
                yield self.env.timeout(1)
                continue
            
            # Reset local tracking blocks for this specific batch
            wheels_in_batch = []
            current_slots_used = 0
            
            # Create a copy of the queue to iterate safely
            for item in list(self.queue):
                wheel_data,wheel_casted, t_HT_arrival, wheel_done_event, true_ht_queue_at_entry = item
                ht_slot = wheel_config[wheel_data["family"]]["ht_slot"]
                
                if current_slots_used + ht_slot <= self.max_slots:
                    current_slots_used += ht_slot
                    wheels_in_batch.append(item) 
                    self.queue.remove(item)  # Remove from waiting yard queue
                else:
                    continue

            if wheels_in_batch:
                self.env.process(self.move_batch_through_pipeline(wheels_in_batch))
            yield self.env.timeout(2)
            
   
            
    def move_batch_through_pipeline(self, batch):
        t_HT_start = self.env.now
        
        # CHAMBER 1: SOLUTION TREATMENT (120 Mins)
        sol_req = self.solution.request()
        yield sol_req
        yield self.env.timeout(120.0)
        


        # CHAMBER 2: QUENCH TANK (4 Mins) 
        quench_req = self.quench.request()
        yield quench_req
        self.solution.release(sol_req)
        yield self.env.timeout(4.0)
        

        # CHAMBER 3: AGING OVEN (180 Mins) 
        aging_req= self.aging.request()
        yield aging_req
        self.quench.release(quench_req)
        yield self.env.timeout(180.0)
        self.aging.release(aging_req)

        # Release the baked wheels
        for index, item in enumerate(batch):
            wheel_data, wheel_casted,t_HT_arrival, wheel_done_event, true_ht_queue_at_entry = item
            
            log_stage_metrics(
                env=self.env, 
                wheel_data=wheel_data,
                wheel_casted = wheel_casted, 
                stage_name="Heat_treatment", 
                start_queue_time=t_HT_arrival, 
                start_proc_time=t_HT_start, 
                resource_obj=None, 
                status="Heat_Treatment_completed"
            )
            metrics_log[-1]["Queue_Length_At_Entry"] = true_ht_queue_at_entry
            
          
            wheel_done_event.succeed(value=index)

def run_simulation():

    metrics_HT_cap = []

    capacity = [200,250,300,325,350,375,400,425,475,500,525]


    for cap in capacity:

        random.seed(50)

        metrics_log.clear()
        
        env = simpy.Environment()

        resources = {
            "casting" : simpy.Resource(env, capacity = 20),
            "NDT" : simpy.Resource(env, capacity = 2),
            "Machining" : simpy.Resource(env, capacity = 15),
            "Airleak" : simpy.Resource(env,capacity = 4),
            "Sandblasting" : simpy.Resource(env, capacity = 2),
            "pretreatment" : simpy.Resource(env, capacity= 80),
            "primer" : simpy.Resource(env,capacity = 80 ),
            "color" : simpy.Resource(env, capacity= 80),
            "PL_QC" : simpy.Resource(env, capacity = 4),
            "packing" : simpy.Resource(env, capacity = 4)
                }
        
        global plant_state,Ht_load

        plant_state = plantAssetstate()
        env.process(wheel_arrival_generator(env, resources))
        Ht_load = HT(env, cap)

        env.run(until = 43200)

        stats = pd.DataFrame(metrics_log)
        stats = stats[stats["wheel_casted"] > 3500]
        df_stage = stats[stats["Stage"] == "Heat_treatment"]
        df_stage["HeatTreatment_Capacity"] = cap
        df_stage["Leadtime_Heattreatment"] = df_stage["Timestamp_Exit"] - df_stage["Stage_arrival_Time"]    
        metrics_HT_cap.append(df_stage)

    final_df = pd.concat(metrics_HT_cap, ignore_index=True)         
    return final_df

if __name__ == "__main__":
    df_final = run_simulation()

max_leadtime = df_final.groupby(["HeatTreatment_Capacity"])[["Leadtime_Heattreatment"]].max().reset_index()
max_leadtime["HeatTreatment_Capacity"] = max_leadtime["HeatTreatment_Capacity"].apply(lambda x : f"Capacity-"+str(x))
fig,ax = plt.subplots(figsize = (10,6))
sns.lineplot(data = max_leadtime, x = "HeatTreatment_Capacity", y = "Leadtime_Heattreatment", marker= 'o',color = 'firebrick', ax = ax )
plt.xticks(rotation = 90)
ax.set_title("Determining Optimal HT Processing Capacity", fontweight = 'bold', fontsize = 14)
plt.ylabel("Process lead time in (minutes)")
plt.xlabel("Capacity/No of slots")
#plt.legend().remove()
plt.show()