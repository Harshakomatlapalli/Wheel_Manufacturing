
cumulative_busy_time = {
    "Casting": 0.0,
    "NDT": 0.0,
    "Heat_treatment": 0.0,
    "Machining": 0.0,
    "Airleak": 0.0,
    "SandBlasting": 0.0,
    "Paintline_Pretreatment" :0.0,
    "Paintline_Primer": 0.0,
    "Paintline_Color":0.0,
    "Paintline_QC": 0.0,
    "Packing": 0.0
}
metrics_log = []
def log_stage_metrics(env, wheel_data,wheel_casted,stage_name, start_queue_time, start_proc_time, resource_obj, status="Passed"):
        # Calulcating exactly how long this wheel spent inside the machine
        processing_duration = env.now - start_proc_time

        if stage_name in cumulative_busy_time:
            cumulative_busy_time[stage_name] += processing_duration
        #Calculate true time-weighted utilization up to the current simulation time
        if env.now > 0:
            # Check if it's the custom Heat Treatment class or a standard SimPy resource
            if stage_name == "Heat_treatment":
                capacity = 640
                true_cumulative_utilization = None
            else:
                capacity = resource_obj.capacity if resource_obj else 1
            # Formula: Total Machine-Minutes Spent Working / Total Machine-Minutes Open
            total_available_capacity_time = capacity * env.now
            true_cumulative_utilization = (cumulative_busy_time[stage_name] / total_available_capacity_time) * 100
        else:
            true_cumulative_utilization = 0.0

        metrics_log.append({
        "ID": wheel_data["id"],
        "wheel_casted" : wheel_casted,
        "Family": wheel_data["family"],
        "Stage": stage_name,
        "Stage_arrival_Time" : start_proc_time,
        "Queue_Wait_Time": start_proc_time - start_queue_time,
        "Processing_Time": env.now - start_proc_time,
        "Total_Stage_Time": env.now - start_queue_time,
        "Queue_Length_At_Entry": len(resource_obj.queue) if resource_obj else 0,
        "Machine_Utilization %": true_cumulative_utilization, #(resource_obj.count / resource_obj.capacity) if (resource_obj and resource_obj.capacity > 0) else 0,
        "Status": status,  
        "Timestamp_Exit": env.now
    
    })
        
