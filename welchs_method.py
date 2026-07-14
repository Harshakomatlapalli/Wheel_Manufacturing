'''
Using  Welch's Graphical Procedure to calulcate warmup period required.
 - Perform Replications: Run n independent replications of the simulation (Law recommends a minimum of 3 to 5 runs, each of length m).
- Calculate the Averaged Process: At each simulated step i, calculate the average across all replications
- Apply a Moving Average: To smooth out the high-frequency random noise (which makes it hard to see the true trend), calculate a moving average with a window size w:
- Visual Inspection: Plot the smoothed moving average output against time. The point on the X-axis where the curve flattens out and begins oscillating around a stable, consistent mean is your Warm-Up Period l. All data before this point is deleted from your final KPIs.
- Rule of Thumb: post warm up run length >= 10x warm up period
'''
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


def welch_moving_average(averages, w):
    """
    Appends Averill Law's Welch's Moving Average formula.
    Adjusts dynamically at the boundaries to prevent data truncation.
    """
    M = len(averages)
    smoothed = np.zeros(M)
    for idx in range(M):
        i = idx + 1
        if i > w and idx < (M - w):
            window = averages[idx - w : idx + w + 1]
            smoothed[idx] = np.mean(window)
        elif i <= w:
            window = averages[0 : (2 * idx) + 1]
            smoothed[idx] = np.mean(window)
        else:
            dist_to_end = M - 1 - idx
            window = averages[idx - dist_to_end : idx + dist_to_end + 1]
            smoothed[idx] = np.mean(window)
    return smoothed

def process_simulation_warmup(all_replication_logs, time_bucket_size=60, window_size= 30):
    """
    Processes logs from multiple runs to execute Welch's method.
    
    Parameters:
    - all_replication_logs: List of DataFrames (one per independent simulation run).
    - time_bucket_size: The interval (e.g., 60 minutes) to bin timestamps.
    - window_size: Smoothing parameter 'w'. 30 buckets into past and 30 buckets into future
    """
    binned_replications = []
    max_bucket = 0
    
    for df_log in all_replication_logs:
        # I can see if casting machines are stabilized by observing the queue. Here I am intrested to system wide lead time from casting to packing
        df_filtered = df_log[df_log["Stage"] == "Heat_treatment"].dropna(subset=["Stage_arrival_Time", "Timestamp_Exit"]).copy()
        df_filtered["Total_Lead_time"] = df_filtered["Timestamp_Exit"] - df_filtered["Stage_arrival_Time"]

        # Create discrete time intervals based on the exit time
        df_filtered["Time_Bucket"] = (df_filtered["Timestamp_Exit"] // time_bucket_size).astype(int)
        
        # Calculate the mean of intrested KPI like queue wait time/ total stage time
        bucket_means = df_filtered.groupby("Time_Bucket")["Total_Lead_time"].mean()

        if not bucket_means.empty:
            max_bucket = max(max_bucket, bucket_means.index.max())

        binned_replications.append(bucket_means)

    #Step 2: Continuous Grid Reindexing
    master_timeline = pd.Index(range(0, max_bucket + 1), name="Time_Bucket")
    
    # Reindex and forward-fill quiet hours to keep continuous step-intervals
    aligned_replications = [
        series.reindex(master_timeline).ffill().fillna(0.0) 
        for series in binned_replications
    ]
    
    # Combine individual runs safely into a single data matrix
    df_matrix = pd.concat(aligned_replications, axis=1)    

    data_matrix = df_matrix.to_numpy().T  # Shape: (replications, time_steps)
    
    # Step 3: Compute Averages across rows
    averages = np.mean(data_matrix, axis=0)
    
    # Step 4: Apply Welch Smoothing
    smoothed_series = welch_moving_average(averages, w=window_size)
    
    # Step 5: Plot results
    time_indices = df_matrix.index * time_bucket_size
    
    plt.figure(figsize=(12, 6))
    
    # Plot individual run data to show system volatility
    for j in range(data_matrix.shape[0]):
        plt.plot(time_indices, data_matrix[j], color='lightgray', alpha=0.4, 
                 label='Individual Run' if j == 0 else "")
                 
    plt.plot(time_indices, averages, color='skyblue', alpha=0.7, label='Ensemble Average')
    plt.plot(time_indices, smoothed_series, color='crimson', linewidth=2.5, label=f'Welch Moving Average (w={window_size})')
    
    plt.title("Welch's Method: Lead time for Heat treatment", fontsize=12)
    plt.xlabel("Simulation Time (Minutes / Steps)", fontsize=10)
    plt.ylabel("Lead time (Minutes)", fontsize=10)
    plt.grid(True, linestyle=':', alpha=0.6)
    plt.legend()
    plt.tight_layout()
    plt.show()
     
def run_simulation():
    all_runs_data = []
    runs = 10
    for i in range(runs): 
        random.seed(50 + i)

        metrics_log.clear()

        env = simpy.Environment()

        resources = {
        "casting" : simpy.Resource(env, capacity = 20),
        "NDT" : simpy.Resource(env, capacity = 2),
        "Machining" : simpy.Resource(env, capacity = 7),
        "Airleak" : simpy.Resource(env,capacity =2),
        "Sandblasting" : simpy.Resource(env, capacity =2),
        "pretreatment" : simpy.Resource(env, capacity= 80),
        "primer" : simpy.Resource(env,capacity = 80 ),
        "color" : simpy.Resource(env, capacity= 80),
        "PL_QC" : simpy.Resource(env, capacity = 4),
        "packing" : simpy.Resource(env, capacity = 4)
        }
        
        global plant_state, Ht_load

        plant_state = plantAssetstate()
        env.process(wheel_arrival_generator(env, resources))
        Ht_load = HT(env, capacity= 500)
        
        env.run(until=20000)
        all_runs_data.append(pd.DataFrame(list(metrics_log)))
    process_simulation_warmup(all_runs_data, time_bucket_size=60, window_size=30)
    return all_runs_data

if __name__ == "__main__":
    data_set = run_simulation()
    print("Simulation run successful")
